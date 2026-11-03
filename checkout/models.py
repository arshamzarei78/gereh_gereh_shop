from django.db import models
from django.conf import settings
from products.models import ProductVariant
from accounts.models import Address


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت شده (در حال پردازش)"
        SHIPPED = "shipped", "ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده"
        CANCELED = "canceled", "لغو شده"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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

    # اسنپ‌شات آدرس و اطلاعات گیرنده (برای اینکه با تغییر آدرس در آینده، فاکتور قبلی دست‌نخورده بماند)
    full_name = models.CharField("نام تحویل‌گیرنده", max_length=200)
    phone_number = models.CharField("شماره تماس", max_length=11)
    address_text = models.TextField("آدرس کامل پستی در لحظه خرید")
    postal_code = models.CharField("کد پستی", max_length=10)

    # اطلاعات مالی و وضعیت سفارش
    total_price = models.PositiveBigIntegerField("مبلغ کل قابل پرداخت (تومان)", default=0)
    status = models.CharField(
        "وضعیت سفارش",
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    is_paid = models.BooleanField("پرداخت شده؟", default=False)
    
    # اطلاعات درگاه بانکی و رهگیری
    authority = models.CharField("کد مرجع درگاه (Authority)", max_length=100, blank=True, null=True)
    ref_id = models.CharField("کد رهگیری پرداخت (RefID)", max_length=100, blank=True, null=True)
    
    order_note = models.TextField("یادداشت سفارش", blank=True, null=True)

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

    @property
    def total_price_display(self):
        """هماهنگ با فرمت نمایش قیمت در سایر مدل‌های شما"""
        return f"{self.total_price:,}"


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
        related_name="order_items",
        verbose_name="تنوع محصول",
    )

    # ذخیره نام و ویژگی‌ها به صورت متنی (در صورت حذف شدن محصول در آینده، فاکتور خراب نشود)
    product_name = models.CharField("نام محصول و تنوع", max_length=250)
    price = models.PositiveBigIntegerField("قیمت واحد در لحظه خرید (تومان)")
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
        return f"{self.price:,}"

    @property
    def cost_display(self):
        return f"{self.cost:,}"