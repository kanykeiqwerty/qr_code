from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.send_email import send_confirmation_email
from qr_code import serializers
from .models import CustomUser, WaiterProfile, ClientProfile
from tips.models import Tip
from qr_code.serializers import WaiterProfileSerializer, ClientProfileSerializer, TipSerializer, RegisterSerializer, LoginSerializer, LogoutSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from io import BytesIO
import qrcode
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
import stripe


# from django.contrib.auth import get_user_model

# Устанавливаем секретный ключ для работы со Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY




class RegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = serializers.RegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            if user:
                send_confirmation_email(user)
            return Response(serializer.data, status=201)
        return Response(status=400)


class ActivationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, activation_code):
        try:
            user = CustomUser.objects.get(activation_code=activation_code)
            user.is_active = True
            user.activation_code = ''
            user.save()
            return Response({
                'msg': 'Successfully activated!'},
                status=200)
        except CustomUser.DoesNotExist:
            return Response(
                {'msg': 'Link expired!'},
                status=400
            )


class LoginApiView(TokenObtainPairView):
    serializer_class = serializers.LoginSerializer


class LogoutApiView(generics.GenericAPIView):
    serializer_class = serializers.LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('Successfully loged out', status=204)


class WaiterProfileView(generics.RetrieveUpdateAPIView):
    queryset = WaiterProfile.objects.all()
    serializer_class = WaiterProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        # Получаем идентификатор пользователя из запроса
        user_id = self.request.query_params.get('user_id')
        # Находим профиль официанта по идентификатору пользователя
        return get_object_or_404(WaiterProfile, user_id=user_id)

    def perform_update(self, serializer):
        # Сохраняем обновленный профиль официанта
        waiter = serializer.save()
        # Генерируем QR-код, который будет содержать ссылку на страницу чаевых
        qr_code_img = qrcode.make(f'https://your-site.com/tip/{waiter.id}/')
        buffer = BytesIO()
        qr_code_img.save(buffer)
        waiter.qr_code.save(f'qr_{waiter.id}.png', File(buffer), save=False)
        waiter.save()

class ClientProfileView(generics.RetrieveUpdateAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        # Получаем идентификатор пользователя из запроса
        user_id = self.request.query_params.get('user_id')
        # Находим профиль клиента по идентификатору пользователя
        return get_object_or_404(ClientProfile, user_id=user_id)

    def perform_update(self, serializer):
        # Сохраняем обновленный профиль клиента
        client = serializer.save()
        user = client.user
        # Если у пользователя еще нет идентификатора клиента Stripe, создаем его
        if not user.stripe_customer_id:
            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=user.username
            )
            user.stripe_customer_id = stripe_customer['id']
            user.save()

class AttachPaymentMethodView(APIView):
    def post(self, request):
        user = request.user
        payment_method_id = request.data.get('payment_method_id')

        try:
            stripe.PaymentMethod.attach(payment_method_id, customer=user.stripe_customer_id)
            user.payment_method_id = payment_method_id
            user.save()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@login_required
def make_tip(request, waiter_id):
    if request.method == 'POST':
        client = request.user.clientprofile
        waiter = get_object_or_404(WaiterProfile, user_id=waiter_id)
        amount = float(request.POST.get('amount'))

        try:
            # Создание платежного намерения
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='usd',
                payment_method=client.user.payment_method_id,
                customer=client.user.stripe_customer_id,
                confirm=True,
                transfer_data={
                    'destination': waiter.user.payment_method_id,
                },
            )
            # Создание записи о чаевых
            Tip.objects.create(
                waiter=waiter,
                client=client,
                amount=amount
            )
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


@login_required
def profile_view(request):
    user = request.user
    if user.user_type == 'waiter':
        profile = WaiterProfile.objects.get(user=user)
        data = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "workplace": profile.workplace,
            "qr_code": profile.qr_code.url if profile.qr_code else None
        }
    elif user.user_type == 'client':
        profile = ClientProfile.objects.get(user=user)
        data = {
            "nickname": profile.nickname,
            "payment_method_id": user.payment_method_id,
        }
    return JsonResponse(data)