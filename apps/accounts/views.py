from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.models import Profile,Stock,Transaction,Watchlist  # Import your Profile model
from apps.accounts.forms import ProfileForm,TransactionForm  # This form will handle profile updates
from allauth.socialaccount.models import SocialApp
from allauth.account.views import LoginView
from django.urls import reverse


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