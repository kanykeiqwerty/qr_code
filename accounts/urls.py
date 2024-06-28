from django.conf import settings
from django.urls import path
from .views import RegisterView, LoginApiView, ProfileView, MakeTipView, CompleteWaiterProfileView, EditClientProfileView, AttachPaymentMethodView
from django.conf.urls.static import static
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('make-tip/<int:waiter_id>/', MakeTipView.as_view(), name='make-tip'),
    path('complete-waiter-profile/', CompleteWaiterProfileView.as_view(), name='complete-waiter-profile'),
    path('edit-client-profile/', EditClientProfileView.as_view(), name='edit-client-profile'),
    path('attach-payment-method/', AttachPaymentMethodView.as_view(), name='attach-payment-method'),
    path('client-profile/<int:user_id>/', ProfileView.as_view(), name='client-profile'),
    path('waiter-profile/<int:user_id>/', ProfileView.as_view(), name='waiter-profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)