from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, get_user_model, authenticate
from rest_framework import status,viewsets
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import ProfileSerializer,UserDetailSerializer, UserLoginSerializer
from .models import CustomUser, Profile
from apps.accounts.models import Profile,Stock,Transaction,Watchlist  # Import your Profile model
from apps.accounts.forms import ProfileForm,TransactionForm  # This form will handle profile updates
from allauth.socialaccount.models import SocialApp
from allauth.account.views import LoginView
from django.urls import reverse
from rest_framework.views import APIView
import io
from apps.accounts.serializers import UserRegisterSerializer, UserLoginSerializer

User = get_user_model()

#class UserListCreateView(ListCreateAPIView):
 #   queryset = User.objects.all()
  #  serializer_class = UserDetailSerializer
   # permission_classes = [AllowAny]  # Modify according to your app requirements
   
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer   

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

            if user is not None and user.is_active:
                login(request, user)
                return Response({"message": "Login successful.", "user_id": user.id}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid username/email or password."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(login_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)

def homepage(request):
     if request.user.is_authenticated:
        return redirect('profile')  # Redirect authenticated users to their dashboard or another view
     else:
        return render(request, 'home.html')

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)  # Fetch the profile based on the logged-in user
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to profile page after saving
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})


def stock_list_view(request):
    stocks = Stock.objects.all()  # Fetch all stocks
    return render(request, 'stock_list.html', {'stocks': stocks})

def stock_detail_view(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)  # Fetch specific stock by ID
    return render(request, 'stock_detail.html', {'stock': stock})

@login_required
def create_transaction_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.profile = request.user.profile  # Assuming a user has one profile
            transaction.save()
            return redirect('transactions')  # Redirect to transaction history
    else:
        form = TransactionForm()

    return render(request, 'transaction_form.html', {'form': form})

@login_required
def add_to_watchlist_view(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    watchlist, created = Watchlist.objects.get_or_create(user=request.user, stock=stock)
    
    if created:
        watchlist.save()
    return redirect('watchlist')

@login_required
def watchlist_view(request):
    watchlist = Watchlist.objects.filter(user=request.user)
    return render(request, 'watchlist.html', {'watchlist': watchlist})


def check_social_app():
    try:
        social_app = SocialApp.objects.get(provider='google')  # Example for Google OAuth
        return social_app
    except SocialApp.DoesNotExist:
        raise Exception("Google SocialApp is not configured. Please configure it in the Django Admin.")