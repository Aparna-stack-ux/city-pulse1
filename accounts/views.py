from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from .forms import LoginForm, RegisterForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _('Your account has been created. You can log in now.'))
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Welcome back, %(username)s!') % {'username': user.username})
                return redirect(request.GET.get('next') or 'dashboard')
            messages.error(request, _('The username or password you entered is incorrect. Please try again.'))
        else:
            messages.error(request, _('Please check your login details and try again.'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')
