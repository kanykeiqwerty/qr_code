from django.urls import path
from .views import RegisterView, LoginApiView, ProfileView, MakeTipView, CompleteWaiterProfileView, EditClientProfileView, AttachPaymentMethodView
# from django.urls import reverse
# app_name='accounts'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('make-tip/<uuid:waiter_id>/', MakeTipView.as_view(), name='make-tip'),
    path('complete-waiter-profile/', CompleteWaiterProfileView.as_view(), name='complete-waiter-profile'),
    path('edit-client-profile/', EditClientProfileView.as_view(), name='edit-client-profile'),
    path('attach-payment-method/', AttachPaymentMethodView.as_view(), name='attach-payment-method'),
    path('waiter-profile/', ProfileView.as_view(), name='waiter-profile'),
]
# print(reverse('accounts:waiter_profile'))