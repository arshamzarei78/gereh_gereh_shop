from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import Avg


class Category(models.Model):
    titel = models.CharField(max_length=30)
    created = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی ها"

    def __str__(self):
        return self.titel


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='product', verbose_name="دسته‌بندی‌ها")
    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220, blank=True,allow_unicode=True,unique=True)
    description = models.TextField("توضیحات", blank=True)

    # فیلدهای تکمیلی متناسب با محصولات مکرمه و بافتنی دست‌ساز
    material = models.CharField("جنس نخ / متریال", max_length=150, blank=True, null=True, help_text="مثلاً: نخ مکرومه پنبه‌ای درجه یک و چوب طبیعی")
    dimensions = models.CharField("ابعاد تقریبی", max_length=100, blank=True, null=True, help_text="مثلاً: عرض ۴۰ در ارتفاع ۷۰ سانتی‌متر")
    weight = models.CharField("وزن", max_length=50, blank=True, null=True, help_text="مثلاً: ۳۵۰ گرم")
    care_instructions = models.TextField("نحوه شستشو و نگهداری", blank=True, null=True, help_text="توضیحات مربوط به نحوه شستشو و بسته‌بندی محصول")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # چه اسلاگ خالی باشد چه از قبل پر شده باشد، نیم‌فاصله‌ها را تمیز و استاندارد کن
        target_slug = self.slug if self.slug else self.name
        clean_slug = target_slug.replace('\u200c', ' ')
        self.slug = slugify(clean_slug, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "products:detail",
            kwargs={
                "pk": self.pk,
                "slug": self.slug,
            },
        )

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()

    @property
    def variant(self):
        variant = self.variants.first()
        return variant if variant else None

    @property
    def available_colors(self):
        """لیست رنگ‌های یکتای این محصول برای نمایش در جدول مشخصات"""
        return ", ".join(self.variants.values_list('color', flat=True).distinct())

    @property
    def available_sizes(self):
        """لیست سایزهای یکتای این محصول"""
        sizes = [s for s in self.variants.values_list('size', flat=True).distinct() if s]
        return ", ".join(sizes)

    @property
    def average_rating(self):
        avg = self.comments.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 5.0


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="محصول",
    )
    image = models.ForeignKey(
        "ProductImage", 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="variant_items",
        verbose_name="تصویر اختصاصی این رنگ/تنوع"
    )
    color = models.CharField("رنگ", max_length=50)
    size = models.CharField("سایز", max_length=20, null=True, blank=True)
    price = models.PositiveBigIntegerField("قیمت (تومان)")
    discount = models.PositiveIntegerField("درصد تخفیف", default=0)
    stock = models.PositiveIntegerField("موجودی", default=0)

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌ محصولات"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "size"],
                name="unique_product_variant",
            )
        ]

    def __str__(self):
        return f"{self.product.name} | {self.color} | {self.size or 'بدون سایز'}"

    @property
    def final_price(self):
        return int(self.price * (100 - self.discount) / 100)

    @property
    def price_display(self):
        return f"{self.price:,}"

    @property
    def final_price_display(self):
        return f"{self.final_price:,}"

    @property
    def display_image(self):
        if self.image:
            return self.image
        return self.product.main_image


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول"
    )
    title = models.CharField(
        "عنوان عکس", 
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="مثلاً: نمای روبرو - رنگ قرمز (برای تشخیص راحت در پنل ادمین)"
    )
    image = models.ImageField(upload_to="products/", verbose_name="تصویر")
    is_main = models.BooleanField(default=False, verbose_name="تصویر اصلی")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"

    def __str__(self):
        if self.title:
            return f"{self.product.name} | {self.title}"
        return f"تصویر {self.product.name}"


class ProductComment(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="محصول"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_comments",
        verbose_name="کاربر"
    )
    rating = models.PositiveSmallIntegerField("امتیاز (۱ تا ۵)", default=5)
    content = models.TextField("متن نظر")
    is_approved = models.BooleanField("تایید شده؟", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "نظر محصول"
        verbose_name_plural = "نظرات محصولات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"نظر {self.user} برای {self.product.name}"