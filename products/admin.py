from django.contrib import admin
from . import models
from django import forms
from django.utils.html import format_html


admin.site.register(models.Category)
admin.site.register(models.ProductImage)

class VariantInline(admin.TabularInline):
    model = models.ProductVariant
    extra = 0


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
            
            "name",
            "description",
            "created_at",
        )
    inlines=[VariantInline]

class ProductVariantAdminForm(forms.ModelForm):
    class Meta:
        model = models.ProductVariant
        fields = "__all__"
        widgets = {
            "price": forms.TextInput(attrs={
                "id": "id_price"
            })
        }


@admin.register(models.ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm

    class Media:
        js = ("js/price_format.js",)