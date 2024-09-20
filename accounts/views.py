from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile,Stock,Transaction,Watchlist  # Import your Profile model
from .forms import ProfileForm,TransactionForm  # This form will handle profile updates



def homepage(request):
     if request.user.is_authenticated:
        return redirect('homepage')  # Redirect authenticated users to their dashboard or another view
     else:
        return render(request, 'home.html')

@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)  # Fetch the profile based on the logged-in user
    
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

