from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """نمایش آیتم‌های خریداری‌شده در پایین صفحه جزئیات همان سفارش"""
    model = OrderItem
    extra = 0  # جلوگیری از نمایش ردیف‌های خالی اضافی
    raw_id_fields = ("variant",)
    fields = ("variant", "product_name", "price", "quantity", "get_cost_display")
    readonly_fields = ("get_cost_display",)

    @admin.display(description="جمع این ردیف (تومان)")
    def get_cost_display(self, obj):
        return f"{obj.cost_display} تومان"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # ستون‌های نمایشی در لیست سفارشات
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "get_total_price",
        "is_paid",
        "status",
        "ref_id",
        "created_at",
    )
    
    # کلیدهای قابل کلیک برای ورود به جزئیات سفارش
    list_display_links = ("id", "full_name")

    # امکان تغییر مستقیم وضعیت سفارش از داخل لیست بدون باز کردن صفحه سفارش
    list_editable = ("status",)

    # فیلترهای سایدبار سمت چپ
    list_filter = ("status", "is_paid", "created_at")

    # قابلیت جستجو بر اساس شماره سفارش، نام، موبایل، کد پستی و کد رهگیری زرین‌پال
    search_fields = (
        "id",
        "full_name",
        "phone_number",
        "postal_code",
        "ref_id",
        "authority",
        "user__phone_number",
    )

    # بهینه‌سازی کوئری دیتابیس در صفحه لیست سفارشات
    list_select_related = ("user", "address")

    # فیلدهای فقط خواندنی (برای جلوگیری از دستکاری ناخواسته اطلاعات تراکنش بانکی)
    readonly_fields = ("created_at", "updated_at", "authority", "ref_id")

    # اتصال جدول آیتم‌های سفارش به صفحه ویرایش سفارش
    inlines = [OrderItemInline]

    # دسته‌بندی منظم فیلدها در صفحه جزئیات هر سفارش
    fieldsets = (
        (
            "وضعیت و اطلاعات مالی سفارش",
            {
                "fields": (
                    "user",
                    ("status", "is_paid"),
                    "total_price",
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
                "classes": ("collapse",),  # به صورت پیش‌فرض جمع‌شده برای خلوت‌تر شدن صفحه
                "fields": (
                    ("ref_id", "authority"),
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )

    # اکشن‌های گروهی برای تغییر وضعیت چند سفارش به صورت همزمان
    actions = ["make_shipped", "make_delivered"]

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