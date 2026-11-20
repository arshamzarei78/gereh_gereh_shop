from django.contrib import admin
from django import forms
from django.db import models as dj_models
from . import models


admin.site.register(models.Category)
admin.site.register(models.ProductImage)


class VariantInline(admin.TabularInline):
    model = models.ProductVariant
    extra = 0
    fields = ("color", "size", "extra_attributes", "price", "discount", "stock", "image")
    formfield_overrides = {
        dj_models.JSONField: {
            "widget": forms.Textarea(
                attrs={
                    "rows": 2,
                    "cols": 28,
                    "style": "direction: ltr; font-family: monospace; font-size: 12px;",
                    "placeholder": '{"ظرفیت": "20000mAh"}',
                }
            )
        }
    }


@admin.register(models.ProductComment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "rating",
        "content",
        "is_approved",
    )


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "created_at",
    )
    inlines = [VariantInline]


class ProductVariantAdminForm(forms.ModelForm):
    class Meta:
        model = models.ProductVariant
        fields = "__all__"
        widgets = {
            "price": forms.TextInput(attrs={"id": "id_price"}),
            "extra_attributes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "style": "direction: ltr; font-family: monospace; width: 420px;",
                    "placeholder": '{"حجم": "100 میل", "گارانتی": "۱۸ ماهه"}',
                }
            ),
        }


@admin.register(models.ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm
    list_display = (
        "product",
        "color",
        "size",
        "formatted_extra_attributes",
        "price_display",
        "discount",
        "stock",
    )
    list_filter = ("product",)
    search_fields = ("product__name", "color", "size")

    @admin.display(description="سایر ویژگی‌ها")
    def formatted_extra_attributes(self, obj):
        if not obj.extra_attributes:
            return "—"
        return " | ".join(f"{k}: {v}" for k, v in obj.extra_attributes.items())

    class Media:
        js = ("js/price_format.js",)