from django.contrib import admin
from .models import Order, OrderItem,ShippingSetting


class OrderItemInline(admin.TabularInline):
    """نمایش آیتم‌های خریداری‌شده در پایین صفحه جزئیات همان سفارش"""
    model = OrderItem
    extra = 0  # جلوگیری از نمایش ردیف‌های خالی اضافی
    raw_id_fields = ("variant",)
    fields = (
        "variant",
        "product_name",
        "original_price",
        "price",
        "quantity",
        "get_cost_display",
    )
    readonly_fields = ("get_cost_display",)

    @admin.display(description="جمع این ردیف (تومان)")
    def get_cost_display(self, obj):
        if not obj.pk:
            return "-"
        return f"{obj.cost_display} تومان"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # ستون‌های نمایشی در لیست سفارشات (به همراه کد رهگیری پستی)
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "get_total_price",
        "is_paid",
        "status",
        "tracking_code",
        "ref_id",
        "created_at",
    )
    
    list_display_links = ("id", "full_name")

    list_editable = ("status", "tracking_code")

    list_filter = ("status", "is_paid", "created_at", "paid_at")

    search_fields = (
        "id",
        "full_name",
        "phone_number",
        "postal_code",
        "tracking_code",
        "ref_id",
        "authority",
        "user__phone_number",
    )

    readonly_fields = ("created_at", "updated_at", "paid_at", "authority", "ref_id")
    inlines = [OrderItemInline]
    fieldsets = (
        (
            "وضعیت، رهگیری پستی و اطلاعات مالی",
            {
                "fields": (
                    "user",
                    ("status", "is_paid"),
                    "tracking_code",
                    ("shipping_cost", "discount_amount", "total_price"),
                )
            },
        ),
        (
            "اطلاعات گیرنده و آدرس پستی",
            {
                "fields": (
                    ("full_name", "phone_number"),
                    "postal_code",
                    "address",
                    "address_text",
                    "order_note",
                )
            },
        ),
        (
            "اطلاعات درگاه زرین‌پال و زمان‌بندی",
            {
                "classes": ("collapse",),
                "fields": (
                    ("ref_id", "authority"),
                    "paid_at",
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )

    actions = ["make_shipped", "make_delivered"]

    def save_model(self, request, obj, form, change):
        """
        هوشمندسازی ادمین:
        اگر ادمین کد رهگیری پستی را وارد کرد و سفارش قبلاً در وضعیت «پرداخت شده» بود،
        وضعیت سفارش به صورت خودکار به «ارسال شده» (SHIPPED) تغییر کند.
        """
        if obj.tracking_code and obj.status == Order.StatusChoices.PAID:
            obj.status = Order.StatusChoices.SHIPPED
        super().save_model(request, obj, form, change)

    @admin.display(description="مبلغ کل", ordering="total_price")
    def get_total_price(self, obj):
        return f"{obj.total_price_display} تومان"

    @admin.action(description="تغییر وضعیت سفارش‌های انتخابی به «ارسال شده»")
    def make_shipped(self, request, queryset):
        updated = queryset.update(status=Order.StatusChoices.SHIPPED)
        self.message_user(request, f"وضعیت {updated} سفارش به «ارسال شده» تغییر یافت.")

    @admin.action(description="تغییر وضعیت سفارش‌های انتخابی به «تحویل داده شده»")
    def make_delivered(self, request, queryset):
        updated = queryset.update(status=Order.StatusChoices.DELIVERED)
        self.message_user(request, f"وضعیت {updated} سفارش به «تحویل داده شده» تغییر یافت.")

@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("tehran_cost", "other_cities_cost", "free_shipping_threshold")

    def has_add_permission(self, request):
        # اگر یک ردیف تنظیمات ساخته شده باشد، دکمه «افزودن» غیرفعال می‌شود تا رکورد تکراری ساخته نشود
        return not ShippingSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False