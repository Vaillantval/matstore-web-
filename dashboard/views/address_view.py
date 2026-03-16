from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from dashboard.models.Adress import Adress
from dashboard.forms.AdressForm import AdressForm


@login_required(login_url='accounts:signin')
def addresses(request):
    user_addresses = Adress.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'dashboard/addresses.html', {
        'addresses': user_addresses,
    })


@login_required(login_url='accounts:signin')
def address_create(request):
    if request.method == 'POST':
        form = AdressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.author = request.user
            address.save()
            messages.success(request, 'Adresse ajoutée avec succès.')
            return redirect('dashboard:addresses')
    else:
        form = AdressForm()
    return render(request, 'dashboard/address_form.html', {
        'form':      form,
        'form_mode': 'create',
    })


@login_required(login_url='accounts:signin')
def address_edit(request, pk):
    address = get_object_or_404(Adress, pk=pk, author=request.user)
    if request.method == 'POST':
        form = AdressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Adresse mise à jour.')
            return redirect('dashboard:addresses')
    else:
        form = AdressForm(instance=address)
    return render(request, 'dashboard/address_form.html', {
        'form':      form,
        'form_mode': 'edit',
        'address':   address,
    })


@login_required(login_url='accounts:signin')
def address_delete(request, pk):
    address = get_object_or_404(Adress, pk=pk, author=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Adresse supprimée.')
    return redirect('dashboard:addresses')
