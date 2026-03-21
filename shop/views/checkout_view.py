from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from shop.services.cart_service import CartService
from shop.models.Carrier import Carrier
from shop.forms.CheckoutAddressForm import CheckoutAddressForm
from django.contrib import messages
from accounts.forms.CustomLoginForm import CustomLoginForm
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from accounts.models.Customer import Customer
from django.contrib.auth.hashers import make_password
import random
import string
from django.db import transaction
from shop.models.Order import Order
from shop.models.Method import Method
from dashboard.models.Adress import Adress
from shop.models.OrderDetail import OrderDetail
from shop.services.payment_service import StripeService
from shop.services.moncash_service import MonCashService


def index(request):
    carrier_id = request.GET.get('carrier_id')
    new_shipping_address = request.GET.get('new_shipping_address', '')
    address_billing_id = request.GET.get('address_billing_id', '')
    if address_billing_id and address_billing_id != "":
        address_billing_id = int(address_billing_id)

    address_shipping_id = request.GET.get('address_shipping_id', address_billing_id)
    if address_shipping_id and address_shipping_id != "":
        address_shipping_id = int(address_shipping_id)

    ready_to_pay = False
    if new_shipping_address and new_shipping_address != 'false':
        ready_to_pay = bool(address_billing_id) and bool(address_shipping_id)
    else:
        ready_to_pay = bool(address_billing_id)

    if carrier_id and carrier_id != '':
        carrier = Carrier.objects.filter(id=carrier_id).first()
        if carrier:
            request.session['carrier'] = {
                'id': carrier.id,
                'name': carrier.name,
                'price': float(carrier.price),
            }
            # Sync avec la clé lue par cart_service.get_cart_details()
            request.session['carrier_id'] = carrier.id

    cart = CartService.get_cart_details(request)
    carriers = Carrier.objects.all()

    payment_service = StripeService()
    order_id = None
    if ready_to_pay:
        if new_shipping_address and new_shipping_address != 'false':
            billing_address = Adress.objects.filter(id=address_billing_id).first()
            shipping_address = Adress.objects.filter(id=address_shipping_id).first()
        else:
            billing_address = Adress.objects.filter(id=address_billing_id).first()
            shipping_address = None

        billing_address_str = billing_address.get_adress_as_string() if billing_address else ""
        shipping_address_str = shipping_address.get_adress_as_string() if shipping_address else None

        existing_order_id = request.session.get('pending_order_id')
        if existing_order_id:
            existing_order = Order.objects.filter(
                id=existing_order_id, is_paid=False
            ).first()
            if existing_order:
                existing_order.billing_address = billing_address_str
                existing_order.shipping_address = shipping_address_str or billing_address_str
                existing_order.save()
                order_id = existing_order.id

        if not order_id:
            order_id = create_order(
                request, billing_address_str, shipping_address_str
            )
            request.session['pending_order_id'] = order_id

    address_form = CheckoutAddressForm()
    login_form_instance = CustomLoginForm()

    # Méthodes de paiement disponibles (depuis Admin)
    payment_methods = Method.objects.filter(is_available=True)
    moncash_configured = MonCashService.is_configured()

    return render(request, 'shop/checkout.html', {
        'cart': cart,
        'carriers': carriers,
        'address_form': address_form,
        'login_form': login_form_instance,
        'ready_to_pay': ready_to_pay,
        'address_billing_id': address_billing_id,
        'address_shipping_id': address_shipping_id,
        'new_shipping_address': new_shipping_address,
        'public_key': payment_service.get_public_key(),
        'order_id': order_id,
        'payment_methods': payment_methods,
        'moncash_configured': moncash_configured,
    })


def add_address(request):
    user = request.user
    if request.method == 'POST':
        address_form = CheckoutAddressForm(request.POST)
        if not user.is_authenticated:
            email = request.POST.get('email')
            existing_user = Customer.objects.filter(email=email).first()

            if existing_user:
                login(request, existing_user)
                user = existing_user
            else:
                new_user = Customer()
                new_user.username = email
                new_user.email = email
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                new_user.password = make_password(password)
                new_user.save()
                login(request, new_user)
                user = new_user

        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.author = user
            address.save()
            messages.success(request, 'Address added successfully.')

    # Fix #6 : reverse() au lieu d'un chemin hardcodé '/checkout/'
    query_string = request.GET.urlencode()
    redirect_url = reverse('checkout')
    if query_string:
        redirect_url += f"?{query_string}"
    return redirect(redirect_url)


def login_form(request):
    if request.user.is_authenticated:
        return JsonResponse({"isSuccess": True, 'message': 'This user is already connected !'})

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"isSuccess": True, 'message': 'This user connected !'})
        else:
            return JsonResponse({"isSuccess": False,
                                 'message': 'Invalid credentials. Unable to connect.'})

    return JsonResponse({"isSuccess": False, 'message': 'Error, Invalid request method !'})


def create_order(request, billing_address, shipping_address=None, payment_method='pending'):
    cart = CartService.get_cart_details(request)
    user = request.user

    carrier_data = request.session.get('carrier')
    if carrier_data and isinstance(carrier_data, dict):
        carrier_name = carrier_data.get('name', '')
        carrier_price = carrier_data.get('price', 0)
    else:
        # Fallback sur carrier_id stocké par cart_view (select_carrier)
        session_carrier_id = request.session.get('carrier_id')
        fallback_carrier = (
            Carrier.objects.filter(id=session_carrier_id).first()
            if session_carrier_id
            else Carrier.objects.first()
        )
        carrier_name = fallback_carrier.name if fallback_carrier else ''
        carrier_price = float(fallback_carrier.price) if fallback_carrier else 0

    with transaction.atomic():
        order = Order()
        order.client_name = user.username
        order.author = user
        order.billing_address = billing_address
        order.shipping_address = shipping_address or billing_address
        order.carrier_name = carrier_name
        order.carrier_price = carrier_price
        order.quantity = cart['cart_count']
        order.order_cost = cart['sub_total_ht']
        order.taxe = cart['taxe_amount']
        order.order_cost_ttc = cart['sub_total_with_shipping']
        # Fix #7 : méthode de paiement dynamique, non hardcodée
        order.payment_method = payment_method
        order.save()

        for item in cart['items']:
            order_details = OrderDetail()
            order_details.product_name = item.get("product").get("name")
            order_details.product_description = item.get("product").get("description")
            order_details.solde_price = item.get("product").get("solde_price")
            order_details.regular_price = item.get("product").get("regular_price")
            order_details.quantity = item.get("quantity")
            order_details.taxe = item.get("taxe_amount")
            order_details.sub_total_ht = item.get("sub_total_ht")
            order_details.sub_total_ttc = item.get("sub_total_ttc")
            order_details.order = order
            order_details.save()

    return order.id
