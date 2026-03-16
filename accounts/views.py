from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from accounts.forms.CustomUserRegisterForm import CustomUserRegisterForm
from accounts.forms.CustomLoginForm import CustomLoginForm


def signin(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # AuthenticationForm requiert request en premier argument
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Rediriger vers la page demandée ou le dashboard
            next_url = request.GET.get('next', 'dashboard:overview')
            return redirect(next_url)
        # Les erreurs du formulaire sont affichées dans le template
    else:
        form = CustomLoginForm(request)

    return render(request, 'accounts/signin.html', {'form': form})


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connexion automatique après inscription
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} ! Votre compte a été créé.')
            return redirect('dashboard:overview')
    else:
        form = CustomUserRegisterForm()

    return render(request, 'accounts/signup.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('home')
