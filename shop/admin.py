from django.contrib import admin
from django.utils.html import format_html

from shop.models import Slider, Collection, Category, Product, Image


# Pour les sliders images
class SliderAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "display_image")
    list_display_links = ("id", "title")

    def display_image(self, obj):
        return format_html(
            '<img src="{}" width="100px" height="100px" />', obj.image.url
        )

    display_image.short_description = "image"


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
    list_display = ("id", "name", "display_image")
    list_display_links = ("id", "name")

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


admin.site.register(Slider, SliderAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)


#  .venv\Scripts\activate
# .\myenv\Scripts\activate
# python .\manage.py runserver
# python .\manage.py makemigrations; python .\manage.py migrate
