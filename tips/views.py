from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, WaiterProfile, ClientProfile, Tip
from qr_code.serializers import WaiterProfileSerializer, ClientProfileSerializer, TipSerializer
from io import BytesIO
import qrcode
from django.core.files import File
import stripe

class TipView(generics.CreateAPIView):
    queryset = Tip.objects.all()
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Сохраняем данные о чаевых
        tip = serializer.save()
        waiter = tip.waiter
        client = tip.client
        amount = int(tip.amount * 100)  # переводим сумму в центы
        # Создаем платеж в Stripe, подтверждаем его и переводим деньги официанту
        stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method=client.payment_method,
            customer=client.user.stripe_customer_id,
            confirm=True,
            transfer_data={
                'destination': waiter.payment_method,
            },
        )

class WaiterTipHistoryView(generics.ListAPIView):
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем историю чаевых для конкретного официанта
        return Tip.objects.filter(waiter__user=self.request.user)

class ClientTipHistoryView(generics.ListAPIView):
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем историю чаевых для конкретного клиента
        return Tip.objects.filter(client__user=self.request.user)