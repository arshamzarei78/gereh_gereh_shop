from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


class Category(models.Model):
    title = models.CharField("عنوان دسته‌بندی", max_length=30)
    created = models.DateField(auto_now_add=True)
    image = models.ImageField(
        upload_to="category/", verbose_name="تصویر دسته‌بندی", blank=True, null=True
    )

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ManyToManyField(
        Category, related_name="products", verbose_name="دسته‌بندی‌ها"
    )
    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField(
        "اسلاگ", max_length=220, blank=True, allow_unicode=True, unique=True
    )
    description = models.TextField("توضیحات", blank=True)

    material = models.CharField(
        "جنس / متریال",
        max_length=150,
        blank=True,
        null=True,
        help_text="مثلاً: نخ مکرومه پنبه‌ای درجه یک و چوب طبیعی",
    )
    dimensions = models.CharField(
        "ابعاد تقریبی",
        max_length=100,
        blank=True,
        null=True,
        help_text="مثلاً: عرض ۴۰ در ارتفاع ۷۰ سانتی‌متر",
    )
    weight = models.CharField(
        "وزن", max_length=50, blank=True, null=True, help_text="مثلاً: ۳۵۰ گرم"
    )
    care_instructions = models.TextField(
        "نحوه شستشو و نگهداری",
        blank=True,
        null=True,
        help_text="توضیحات مربوط به نحوه نگهداری یا بسته‌بندی محصول",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        target_slug = self.slug if self.slug else self.name
        clean_slug = target_slug.replace("\u200c", " ")
        base_slug = slugify(clean_slug, allow_unicode=True)

        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "products:detail",
            kwargs={"pk": self.pk, "slug": self.slug},
        )

    @property
    def main_image(self):
        images = list(self.images.all())
        if not images:
            return None
        for img in images:
            if img.is_main:
                return img
        return images[0]

    @property
    def variant(self):
        variants = list(self.variants.all())
        return variants[0] if variants else None

    @property
    def available_colors(self):
        colors = dict.fromkeys(v.color for v in self.variants.all() if v.color)
        return "، ".join(colors.keys())

    @property
    def available_sizes(self):
        sizes = dict.fromkeys(v.size for v in self.variants.all() if v.size)
        return "، ".join(sizes.keys())

    @property
    def average_rating(self):
        if hasattr(self, "calculated_rating"):
            return round(self.calculated_rating, 1)
        avg = self.comments.filter(is_approved=True).aggregate(Avg("rating"))["rating__avg"]
        return round(avg, 1) if avg else 5.0

    @property
    def available_extra_attributes(self):
        """استخراج یکتای سایر ویژگی‌های تنوع‌ها برای نمایش در جدول مشخصات"""
        grouped = {}
        for v in self.variants.all():
            if isinstance(v.extra_attributes, dict):
                for k, val in v.extra_attributes.items():
                    grouped.setdefault(k, {})[val] = None
        return {k: "، ".join(vals.keys()) for k, vals in grouped.items()}


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
        verbose_name="تصویر اختصاصی این تنوع",
    )
    color = models.CharField(
        "رنگ", max_length=50, blank=True, null=True, db_index=True
    )
    size = models.CharField(
        "سایز", max_length=20, blank=True, null=True, db_index=True
    )
    extra_attributes = models.JSONField(
        "سایر ویژگی‌ها",
        default=dict,
        blank=True,
        help_text='به فرمت JSON وارد کنید. مثال: {"حجم": "100 میل", "گارانتی": "۱۸ ماهه"}',
    )
    price = models.PositiveBigIntegerField("قیمت (تومان)")
    discount = models.PositiveIntegerField(
        "درصد تخفیف",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    stock = models.PositiveIntegerField("موجودی", default=0)

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع محصولات"

    def clean(self):
        super().clean()

        # یکسان‌سازی مقادیر خالی به None
        self.color = self.color.strip() if self.color and self.color.strip() else None
        self.size = self.size.strip() if self.size and self.size.strip() else None

        # اطمینان از ساختار دیکشنری برای extra_attributes
        if self.extra_attributes in (None, ""):
            self.extra_attributes = {}
        elif not isinstance(self.extra_attributes, dict):
            raise ValidationError(
                {
                    "extra_attributes": 'مقدار باید به صورت کلید و مقدار (JSON Object) باشد؛ مثلاً {"حجم": "100 میل"}'
                }
            )
        else:
            cleaned_attrs = {}
            for k, v in self.extra_attributes.items():
                key = str(k).strip()
                val = str(v).strip()
                if key and val:
                    cleaned_attrs[key] = val
            self.extra_attributes = cleaned_attrs

        # جلوگیری از ثبت تنوع کاملاً تکراری برای یک محصول
        if self.product_id:
            same_base = ProductVariant.objects.filter(
                product_id=self.product_id,
                color=self.color,
                size=self.size,
            ).exclude(pk=self.pk)

            for variant in same_base:
                if (variant.extra_attributes or {}) == self.extra_attributes:
                    raise ValidationError(
                        "تنوعی با دقیقاً همین مشخصات (رنگ، سایز و سایر ویژگی‌ها) قبلاً برای این محصول ثبت شده است."
                    )

    @property
    def all_attributes(self):
        """ترکیب یکپارچه رنگ، سایز و سایر ویژگی‌های دلخواه"""
        attrs = {}
        if self.color:
            attrs["رنگ"] = self.color
        if self.size:
            attrs["سایز"] = self.size
        if isinstance(self.extra_attributes, dict):
            attrs.update(self.extra_attributes)
        return attrs

    def __str__(self):
        attrs_text = " | ".join(f"{k}: {v}" for k, v in self.all_attributes.items())
        return f"{self.product.name} ({attrs_text})" if attrs_text else self.product.name

    @property
    def final_price(self):
        if not self.discount:
            return self.price
        return int(self.price * (100 - self.discount) // 100)

    @property
    def price_display(self):
        return f"{self.price:,}"

    @property
    def final_price_display(self):
        return f"{self.final_price:,}"

    @property
    def display_image(self):
        return self.image or self.product.main_image


@receiver([post_save, post_delete], sender=ProductVariant)
def clear_product_variants_cache(sender, **kwargs):
    cache.delete_many(
        [
            "sidebar_available_colors",
            "sidebar_available_sizes",
            "home_products",
            "home_discounted_products",
        ]
    )


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول",
    )
    title = models.CharField(
        "عنوان عکس",
        max_length=100,
        blank=True,
        default="",
        help_text="مثلاً: نمای روبرو - رنگ قرمز (برای تشخیص راحت در پنل ادمین)",
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
        verbose_name="محصول",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_comments",
        verbose_name="کاربر",
    )
    rating = models.PositiveSmallIntegerField(
        "امتیاز (۱ تا ۵)",
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    content = models.TextField("متن نظر")
    is_approved = models.BooleanField("تایید شده؟", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "نظر محصول"
        verbose_name_plural = "نظرات محصولات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"نظر {self.user} برای {self.product.name}"