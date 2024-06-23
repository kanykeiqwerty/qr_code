from django.urls import path
from .views import WaiterProfileView, ClientProfileView, AttachPaymentMethodView, LoginApiView, LogoutApiView, ActivationView

from main.views import UserRegistrationView
from tips.views import TipView, WaiterTipHistoryView, ClientTipHistoryView
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('activate/<str:activation_code>/', ActivationView.as_view(), name='activate'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
    path('waiter/profile/', WaiterProfileView.as_view(), name='waiter-profile'),
    path('client/profile/', ClientProfileView.as_view(), name='client-profile'),
    path('tip/', TipView.as_view(), name='tip'),
    path('waiter/tips/', WaiterTipHistoryView.as_view(), name='waiter-tips'),
    path('client/tips/', ClientTipHistoryView.as_view(), name='client-tips'),
    path('attach-payment-method/<uuid:user_id>/', AttachPaymentMethodView.as_view(), name='attach-payment-method'),
]
