from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from .models import CustomUser, WaiterProfile, ClientProfile, Tip
from .forms import WaiterProfileForm, ClientProfileForm, PaymentMethodForm
from .serializers import RegisterSerializer, LoginSerializer
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class RegisterView(APIView):
    def get(self, request):
        role = request.GET.get('role', 'client')
        return render(request, 'register.html', {'role': role})

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user.user_type == 'waiter':
                request.session['user_id'] = str(user.id)
                return redirect('complete-waiter-profile')
            else:
                return redirect('edit-client-profile')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CompleteWaiterProfileView(APIView):
    @method_decorator(login_required)
    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user = get_object_or_404(CustomUser, id=user_id)
        profile, created = WaiterProfile.objects.get_or_create(user=user)
        form = WaiterProfileForm(instance=profile)
        return render(request, 'complete_waiter_profile.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user = get_object_or_404(CustomUser, id=user_id)
        profile = WaiterProfile.objects.get(user=user)
        form = WaiterProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('waiter-profile')
        return render(request, 'complete_waiter_profile.html', {'form': form})

class LoginApiView(TokenObtainPairView):
    serializer_class = LoginSerializer

@method_decorator(login_required, name='dispatch')
class ProfileView(APIView):
    def get(self, request):
        user = request.user
        if user.user_type == 'waiter':
            profile = WaiterProfile.objects.get(user=user)
            return render(request, 'waiter_profile.html', {'profile': profile})
        elif user.user_type == 'client':
            profile = ClientProfile.objects.get(user=user)
            return render(request, 'client_profile.html', {'profile': profile})
        return HttpResponse(status=404)

@method_decorator(login_required, name='dispatch')
class EditClientProfileView(APIView):
    def get(self, request):
        profile, created = ClientProfile.objects.get_or_create(user=request.user)
        form = ClientProfileForm(instance=profile)
        return render(request, 'edit_client_profile.html', {'form': form})

    def post(self, request):
        profile = ClientProfile.objects.get(user=request.user)
        form = ClientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            try:
                form.save()
                return redirect('profile')
            except IntegrityError:
                form.add_error('nickname', 'Этот никнейм уже используется.')
        return render(request, 'edit_client_profile.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class AttachPaymentMethodView(APIView):
    def get(self, request):
        form = PaymentMethodForm()
        return render(request, 'attach_payment_method.html', {'form': form})

    def post(self, request):
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            request.user.payment_method_id = form.cleaned_data['payment_method_id']
            request.user.save()
            return redirect('profile')
        return render(request, 'attach_payment_method.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class MakeTipView(APIView):
    def post(self, request, waiter_id):
        client = request.user.clientprofile
        waiter = get_object_or_404(WaiterProfile, user_id=waiter_id)
        amount = float(request.data.get('amount'))

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
