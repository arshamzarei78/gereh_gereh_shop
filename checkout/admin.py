from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "product_name", "price", "quantity", "cost_display")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "total_price_display",
        "status",
        "is_paid",
        "created_at",
    )
    list_filter = ("status", "is_paid", "created_at")
    search_fields = ("id", "full_name", "phone_number", "postal_code", "ref_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]
