from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

from dashboard.forms.UserAccountForm import UserAccountForm
from accounts.forms.ResetPasswordForm import ResetPasswordForm


@login_required(login_url='accounts:signin')
def index(request):
    user = request.user
    account_form = UserAccountForm(instance=user)
    reset_password_form = ResetPasswordForm()
    reset_password_form.user = user

    return render(request, 'dashboard/profile.html', {
        'account_form': account_form,
        'reset_password_form': reset_password_form,
    })


@login_required(login_url='accounts:signin')
def save_account(request):
    user = request.user
    if request.method == 'POST':
        account_form = UserAccountForm(request.POST, instance=user)
        if account_form.is_valid():
            account_form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
        else:
            messages.error(request, 'Erreur lors de la mise à jour du profil.')
    return redirect('dashboard:account')


@login_required(login_url='accounts:signin')
def reset_user_password(request):
    user = request.user
    if request.method == 'POST':
        reset_password_form = ResetPasswordForm(request.POST)
        reset_password_form.user = user
        if reset_password_form.is_valid():
            new_password = reset_password_form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe modifié avec succès.')
            return redirect('dashboard:account')
        else:
            account_form = UserAccountForm(instance=user)
            return render(request, 'dashboard/profile.html', {
                'account_form': account_form,
                'reset_password_form': reset_password_form,
                'open_password_tab': True,
            })
    return redirect('dashboard:account')