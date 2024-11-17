from urllib.parse import urlencode
import jwt as jwt_lib
import requests
from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, get_user_model, authenticate
from django.urls import reverse
from rest_framework import status,viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ProfileSerializer, UserDetailSerializer, UserLoginSerializer, UserLogoutSerializer
from .models import CustomUser, Profile
from apps.accounts.models import Profile,Stock,Transaction,Watchlist  # Import your Profile model
from apps.accounts.forms import ProfileForm,TransactionForm  # This form will handle profile updates
from rest_framework.views import APIView
import io
from apps.accounts.serializers import UserRegisterSerializer, UserLoginSerializer

User = get_user_model()

   
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(User, id=self.request.user.id)

#class ProfileListCreateView(ListCreateAPIView):
 #   queryset = Profile.objects.all()
  #  serializer_class = ProfileSerializer
   # permission_classes = [IsAuthenticated]

    #def perform_create(self, serializer):
     #   serializer.save(user=self.request.user)
     
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

class ProfileDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

class UserRegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer

    def post(self, request):
        payload: dict = JSONParser().parse(stream=io.BytesIO(request.body))
        serializer = self.serializer_class(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        payload: dict = JSONParser().parse(stream=io.BytesIO(request.body))
        login_serializer = self.serializer_class(data=payload)

        if login_serializer.is_valid():
            # Authenticate the user with the LoginSerializer's data
            username_or_email = login_serializer.validated_data['username_or_email']
            password = login_serializer.validated_data['password']

            # Use the existing authenticate_user method from UserSerializer or create a new one in the LoginSerializer
            user = authenticate(username=username_or_email, password=password)
            if not user:
                # Try to authenticate with email
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    return Response({"error": "Invalid username/email or password."},
                                    status=status.HTTP_400_BAD_REQUEST)

            if user and user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Login successful.",
                    "user_id": user.id,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid username/email or password."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(login_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLogoutSerializer

    def post(self, request):
        try:
            payload: dict = JSONParser().parse(stream=io.BytesIO(request.body))
            logout_serializer = self.serializer_class(data=payload)
            if not logout_serializer.is_valid():
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the token
            token = RefreshToken(logout_serializer.validated_data['refresh'])
            # token.blacklist()

            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            raise e
            return Response({"error": "Invalid token or logout failed."}, status=status.HTTP_400_BAD_REQUEST)


class GoogleOAuthSettings:
    """Centralized Google OAuth settings management"""
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    @classmethod
    def get_redirect_uri(cls, request):
        """Generate the redirect URI dynamically based on the current domain"""
        # return request.build_absolute_uri(reverse('google-callback'))
        return settings.GOOGLE_REDIRECT_URI


class GoogleAuthRedirectView(APIView):
    """
    Initiates the Google OAuth2 flow by returning the authorization URL.
    The frontend should redirect the user to this URL.
    """

    def get(self, request, *args, **kwargs):
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": GoogleOAuthSettings.get_redirect_uri(request),
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",  # Request refresh token
            "state": self.generate_state_parameter(request),  # Add CSRF protection
            "prompt": "select_account"  # Always show account selector
        }

        auth_url = f"{GoogleOAuthSettings.GOOGLE_AUTH_URL}?{urlencode(params)}"
        return Response({"authorization_url": auth_url}, status=status.HTTP_200_OK)

    def generate_state_parameter(self, request):
        """Generate and store a state parameter for CSRF protection"""
        state = jwt_lib.encode(
            {"session_id": request.session.session_key},
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        return state


class GoogleCallbackView(APIView):
    """
    Handles the OAuth2 callback from Google and issues JWT tokens.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Validate the request
            self.validate_callback_request(request)

            # Exchange the authorization code for tokens
            token_data = self.exchange_code_for_tokens(request)

            # Get user info from Google
            user_info = self.get_google_user_info(token_data['access_token'])

            # Create or update user
            user = self.create_or_update_user(user_info)

            # Generate JWT tokens
            tokens = self.generate_jwt_tokens(user)

            # Prepare the response
            response_data = {
                "access": str(tokens['access']),
                "refresh": str(tokens['refresh']),
                "user": {
                    "email": user.email,
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise e
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def validate_callback_request(self, request):
        """Validate the callback request parameters"""
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        print("new_state: "+ state)

        if not code:
            raise ValidationError("Authorization code is missing")

        if not state:
            raise ValidationError("Invalid state parameter")


    def exchange_code_for_tokens(self, request):
        """Exchange the authorization code for Google tokens"""
        response = requests.post(
            GoogleOAuthSettings.GOOGLE_TOKEN_URL,
            data={
                "code": request.query_params.get("code"),
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": GoogleOAuthSettings.get_redirect_uri(request),
                "grant_type": "authorization_code",
            },
            timeout=10  # Add timeout for safety
        )

        if response.status_code != 200:
            raise ValidationError("Failed to exchange authorization code")

        return response.json()

    def get_google_user_info(self, access_token):
        """Fetch user information from Google"""
        response = requests.get(
            GoogleOAuthSettings.GOOGLE_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code != 200:
            raise ValidationError("Failed to fetch user info from Google")

        return response.json()

    def create_or_update_user(self, user_info):
        """Create or update user based on Google profile data"""
        email = user_info.get("email")
        if not email:
            raise ValidationError("Email not provided by Google")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "is_active": True,
                "is_verified": True,
                "is_social": True,
            }
        )

        if not created:
            # Update existing user info
            user.first_name = user_info.get("given_name", user.first_name)
            user.last_name = user_info.get("family_name", user.last_name)
            user.is_verified = True
            user.save()

        return user

    def generate_jwt_tokens(self, user):
        """Generate JWT access and refresh tokens"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': refresh,
            'access': refresh.access_token,
        }