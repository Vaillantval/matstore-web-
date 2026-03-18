from django.contrib import admin
from django.contrib import messages
from django.db import models as db_models
from django.utils.html import format_html
from django_ckeditor_5.widgets import CKEditor5Widget

from shop import models
from shop.models import (
    Slider,
    Collection,
    Category,
    Product,
    Image,
    Page,
    FAQ,
    ContactMessage,
    ExchangeRate,
    Order,
    OrderDetail,
    Method,
)
from shop.models.Carrier import Carrier
from shop.models.Setting import Setting


# Pour les sliders images
class SliderAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "display_image")
    list_display_links = ("id", "title")

    def display_image(self, obj):
        return format_html(
            '<img src="{}" width="100px" height="100px" />', obj.image.url
        )

    display_image.short_description = "image"


# pour les carriers
class CarrierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "price", "display_image")
    list_display_links = ("id", "name")
    formfield_overrides = {
        db_models.TextField: {"widget": CKEditor5Widget(config_name="default")},
    }

    def display_image(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" width="100px" height="100px" />', obj.image.url
        )

    display_image.short_description = "image"


# Pour les Pages
class PageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "page_type",
        "is_head",
        "is_foot",
        "is_checkout",
        "updated_at",
    )
    list_display_links = ("id", "name")
    list_editable = ("is_head", "is_foot", "page_type")
    list_filter = ("page_type", "is_head", "is_foot")
    search_fields = ("name", "content")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (
            "Informations principales",
            {"fields": ("name", "slug", "subtitle", "page_type", "image")},
        ),
        ("Contenu", {"fields": ("content",)}),
        (
            "Navigation",
            {"fields": ("is_head", "is_foot", "is_checkout"), "classes": ("collapse",)},
        ),
    )


# Pour les FAQs
class FAQAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "order", "is_active", "updated_at")
    list_display_links = ("id", "question")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")


# Pour les messages de contact
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "subject", "is_read", "created_at")
    list_display_links = ("id", "name")
    list_editable = ("is_read",)
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject")
    readonly_fields = ("name", "email", "subject", "message", "created_at")


# pour les Collection
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "display_image")
    list_display_links = ("id", "title")

    def display_image(self, obj):
        return format_html(
            '<img src="{}" width="100px" height="100px" />', obj.image.url
        )

    display_image.short_description = "image"


# pour les category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_mega", "display_image")
    list_display_links = ("id", "name")
    list_editable = ("is_mega",)

    def display_image(self, obj):
        return format_html(
            '<img src="{}" width="100px" height="100px" />', obj.image.url
        )

    display_image.short_description = "image"
    exclude = ("slug",)


# pour les produits
class ImageInline(admin.TabularInline):
    model = Image
    extra = 3


class ProductAdmin(admin.ModelAdmin):
    inlines = [ImageInline]
    list_display = (
        "id",
        "name",
        "solde_price",
        "regular_price",
        "is_available",
        "is_best_seller",
        "is_new_arrival",
        "display_image",
        "updated_at",
    )
    list_display_links = ("id", "name")
    list_editable = (
        "solde_price",
        "is_available",
        "is_best_seller",
        "is_new_arrival",
    )
    list_per_page = 10

    formfield_overrides = {
        db_models.TextField: {"widget": CKEditor5Widget(config_name="default")},
    }

    @staticmethod
    def display_image(obj):
        first_image = obj.images.first()
        if first_image:
            return format_html(
                '<img src="{}" width="100px" height="100px" />', first_image.image.url
            )
        return "Pas d'image"

    # display_image.short_description = 'image'
    exclude = ("slug",)


# pour les commandes
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_name",
        "billing_address",
        "shipping_address",
        "quantity",
        "taxe",
        "order_cost",
        "order_cost_ttc",
        "status",
        "is_paid",
        "carrier_name",
        "carrier_price",
    )
    list_display_links = ("client_name",)
    list_editable = ("status",)
    list_filter = ("is_paid", "created_at", "updated_at")
    search_fields = (
        "client_name",
        "billing_address",
        "shipping_address",
        "carrier_name",
        "payment_method",
    )


class OrderDetailAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_name",
        "quantity",
        "solde_price",
        "sub_total_ht",
        "sub_total_ttc",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "product_name",
        "quantity",
        "solde_price",
        "sub_total_ht",
        "sub_total_ttc",
    )


# pour les methodes de paiement
class MethodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "display_image", "is_available")
    list_display_links = ("name",)
    list_filter = ("is_available", "created_at", "updated_at")
    search_fields = (
        "name",
        "description",
    )

    def display_image(self, obj):
        if not obj.logo:
            return "—"
        return format_html('<img src="{}" height="40" width="100" />', obj.logo.url)

    display_image.short_description = "image"


# Pour les infos du site
class SettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "display_logo",
        "base_currency",
        "currency",
        "city",
    )
    list_display_links = (
        "id",
        "name",
    )
    list_editable = (
        "base_currency",
        "currency",
        "city",
    )
    fieldsets = (
        ("Informations générales", {"fields": ("name", "description", "logo")}),
        (
            "Devises & Taxes",
            {
                "fields": ("base_currency", "currency", "taxe_rate"),
                "description": (
                    "<strong>Devise de base :</strong> la devise dans laquelle vous saisissez les prix.<br>"
                    "<strong>Devise d'affichage :</strong> la devise montrée aux visiteurs (conversion automatique).<br>"
                    "Après changement, lancez <em>Actualiser les taux de change</em> depuis la liste."
                ),
            },
        ),
        (
            "Adresse & Contact",
            {"fields": ("street", "city", "state", "code_postal", "phone", "email")},
        ),
        ("Textes", {"fields": ("copyright",)}),
    )
    actions = ["refresh_exchange_rates"]

    def display_logo(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="60px" height="60px" style="border-radius:6px;" />',
                obj.logo.url,
            )
        return "—"

    display_logo.short_description = "Logo"

    def refresh_exchange_rates(self, request, queryset):
        from shop.management.commands.fetch_rates import fetch_rates_for_base

        obj = queryset.first()
        if not obj:
            self.message_user(
                request, "Sélectionnez un Setting.", level=messages.WARNING
            )
            return
        try:
            count = fetch_rates_for_base(obj.base_currency)
            self.message_user(
                request,
                f"✓ {count} taux actualisés pour {obj.base_currency} → depuis open.er-api.com",
                level=messages.SUCCESS,
            )
        except RuntimeError as e:
            self.message_user(request, f"Erreur : {e}", level=messages.ERROR)

    refresh_exchange_rates.short_description = "🔄 Actualiser les taux de change"


# Taux de change
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("base_currency", "target_currency", "rate", "updated_at")
    list_filter = ("base_currency",)
    search_fields = ("base_currency", "target_currency")
    readonly_fields = ("base_currency", "target_currency", "rate", "updated_at")

    def has_add_permission(self, request):
        return False  # Les taux sont gérés uniquement via l'API


admin.site.register(Slider, SliderAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)

admin.site.register(Order, OrderAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(OrderDetail, OrderDetailAdmin)
admin.site.register(Method, MethodAdmin)

#  .venv\Scripts\activate
# .\myenv\Scripts\activate
# python .\manage.py runserver
# python .\manage.py makemigrations; python .\manage.py migrate
