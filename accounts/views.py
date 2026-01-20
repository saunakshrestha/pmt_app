from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def portal_login(request):
    """Login view for invoice portal"""
    # If user is already logged in, redirect to invoices home
    if request.user.is_authenticated:
        return redirect('invoices_home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '').strip()
        
        # If next_url is empty, use default
        if not next_url:
            next_url = 'invoices_home'
        
        # Since CustomUser uses email as USERNAME_FIELD, authenticate with email
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    
    # Get the 'next' parameter from GET request for redirect after login
    next_url = request.GET.get('next', '')
    
    return render(request, 'invoices/login.html', {'next': next_url})


def portal_logout(request):
    """Logout view for invoice portal"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('invoices_home')
