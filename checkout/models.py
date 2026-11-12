from django.conf import settings
from django.db import models
from django.utils import timezone
from accounts.models import Address
from products.models import ProductVariant


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت شده (در حال پردازش)"
        SHIPPED = "shipped", "ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده"
        CANCELED = "canceled", "لغو شده"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="کاربر",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="آدرس انتخابی",
    )

    # اسنپ‌شات آدرس و اطلاعات گیرنده در لحظه ثبت سفارش
    full_name = models.CharField("نام تحویل‌گیرنده", max_length=200)
    phone_number = models.CharField("شماره تماس", max_length=11)
    address_text = models.TextField("آدرس کامل پستی در لحظه خرید")
    postal_code = models.CharField("کد پستی", max_length=10)

    # اطلاعات مالی تفکیک‌شده
    shipping_cost = models.PositiveBigIntegerField("هزینه ارسال (تومان)", default=0)
    discount_amount = models.PositiveBigIntegerField("مجموع تخفیف (تومان)", default=0)
    total_price = models.PositiveBigIntegerField("مبلغ کل قابل پرداخت (تومان)", default=0)

    status = models.CharField(
        "وضعیت سفارش",
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )

    is_paid = models.BooleanField("پرداخت شده؟", default=False)
    paid_at = models.DateTimeField("تاریخ و ساعت پرداخت", null=True, blank=True)
    authority = models.CharField("کد مرجع درگاه (Authority)", max_length=100, blank=True, default="")
    ref_id = models.CharField("کد رهگیری پرداخت (RefID)", max_length=100, blank=True, default="")
    tracking_code = models.CharField("کد رهگیری مرسوله پستی", max_length=100, blank=True, default="")
    order_note = models.TextField("یادداشت سفارش", blank=True, default="")

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["authority"]),
        ]

    def __str__(self):
        return f"سفارش #{self.id} | {self.full_name} ({self.get_status_display()})"

    def mark_as_paid(self, ref_id=""):
        """متد کمکی برای ثبت یکپارچه پرداخت موفق در ویوی بازگشت از درگاه"""
        self.is_paid = True
        self.status = self.StatusChoices.PAID
        self.paid_at = timezone.now()
        if ref_id:
            self.ref_id = str(ref_id)
        self.save(update_fields=["is_paid", "status", "paid_at", "ref_id", "updated_at"])

    @property
    def items_total_price(self):
        """جمع مبلغ کالاها بدون هزینه ارسال"""
        return max(0, self.total_price - self.shipping_cost)

    @property
    def total_price_display(self):
        return f"{self.total_price:,}"

    @property
    def shipping_cost_display(self):
        return f"{self.shipping_cost:,}" if self.shipping_cost else "رایگان"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="تنوع محصول",
    )

    # اسنپ‌شات مشخصات محصول در لحظه خرید
    product_name = models.CharField("نام محصول و تنوع", max_length=250)
    original_price = models.PositiveBigIntegerField(
        "قیمت واحد قبل از تخفیف (تومان)", default=0
    )
    price = models.PositiveBigIntegerField("قیمت واحد نهایی در لحظه خرید (تومان)")
    quantity = models.PositiveIntegerField("تعداد", default=1)

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.quantity} عدد {self.product_name} (سفارش #{self.order_id})"

    @property
    def cost(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity

    @property
    def price_display(self):
        return f"{self.price:,}" if self.price is not None else "0"

    @property
    def cost_display(self):
        return f"{self.cost:,}"

class ShippingSetting(models.Model):
    tehran_cost = models.PositiveBigIntegerField(
        "هزینه ارسال تهران (تومان)", default=50000
    )
    other_cities_cost = models.PositiveBigIntegerField(
        "هزینه ارسال شهرستان‌ها (تومان)", default=75000
    )
    free_shipping_threshold = models.PositiveBigIntegerField(
        "سقف خرید برای ارسال رایگان (تومان)",
        default=0,
        help_text="اگر ۰ باشد، ارسال رایگان غیرفعال است. در غیر این صورت، خریدهای بالای این مبلغ رایگان ارسال می‌شوند.",
    )

    class Meta:
        verbose_name = "تنظیمات هزینه ارسال"
        verbose_name_plural = "تنظیمات هزینه ارسال"

    def __str__(self):
        return f"تهران: {self.tehran_cost:,} تومان | شهرستان: {self.other_cities_cost:,} تومان"

    def save(self, *args, **kwargs):
        # تضمین اینکه همیشه فقط یک رکورد تنظیمات با pk=1 در دیتابیس وجود داشته باشد
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def calculate_cost(self, province_name, cart_total):
        """محاسبه هوشمند هزینه ارسال بر اساس نام استان و مبلغ سبد خرید"""
        if self.free_shipping_threshold > 0 and cart_total >= self.free_shipping_threshold:
            return 0
        if province_name and "تهران" in province_name:
            return self.tehran_cost
        return self.other_cities_cost