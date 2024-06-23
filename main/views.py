# from django.contrib.auth.models import User
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from accounts.models import WaiterProfile, ClientProfile
# from tips.models import Tip
# from qr_code.serializers import WaiterProfileSerializer, ClientProfileSerializer, TipSerializer, UserSerializer
# import qrcode
# from django.core.files import File
# from io import BytesIO

# class UserRegistrationView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

#     def perform_create(self, serializer):
#         user = serializer.save()
#         if user.is_waiter:
#             WaiterProfile.objects.create(user=user)
#         else:
#             ClientProfile.objects.create(user=user)


# from django.contrib.auth import authenticate, login, logout
# from rest_framework.authtoken.models import Token
# from rest_framework.decorators import api_view
# from rest_framework.permissions import AllowAny

# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         username = request.data.get("username")
#         password = request.data.get("password")
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({"token": token.key})
#         else:
#             return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# class LogoutView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         request.user.auth_token.delete()
#         logout(request)
#         return Response(status=status.HTTP_200_OK)
