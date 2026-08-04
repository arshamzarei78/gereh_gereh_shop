from django.contrib import admin
from . import models
from django import forms


admin.site.register(models.Category)
admin.site.register(models.Product)
admin.site.register(models.ProductImage)


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