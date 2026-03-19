from django.contrib import admin
from dashboard.models.Adress import Adress


@admin.register(Adress)
class AdressAdmin(admin.ModelAdmin):
    list_display  = ('name', 'full_name', 'phone', 'city', 'country', 'adress_type', 'author', 'created_at')
    list_filter   = ('adress_type',)
    search_fields = ('name', 'full_name', 'phone', 'city', 'country', 'author__username')
    ordering      = ('-created_at',)
