from django.conf import settings
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
from django.core.files import File
import stripe

from django.contrib.auth import get_user_model

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
    permission_classes = [permissions.AllowAny]

    def post(self, request, user_id):
        # Находим пользователя по его идентификатору
        user = get_object_or_404(CustomUser, id=user_id)
        # Получаем идентификатор платежного метода из запроса
        payment_method_id = request.data.get('payment_method_id')

        # Привязываем платежный метод к клиенту Stripe
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=user.stripe_customer_id,
        )

        # Если пользователь является официантом, сохраняем платежный метод в его профиль
        if user.is_waiter:
            waiter_profile = WaiterProfile.objects.get(user=user)
            waiter_profile.payment_method = payment_method_id
            waiter_profile.save()
        # Если пользователь является клиентом, сохраняем платежный метод в его профиль
        else:
            client_profile = ClientProfile.objects.get(user=user)
            client_profile.payment_method = payment_method_id
            client_profile.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)