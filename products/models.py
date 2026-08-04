from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    titel = models.CharField(max_length=30)
    created = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی ها"
    def __str__(self):
            return self.titel



class Product(models.Model):
    category = models.ManyToManyField(Category,related_name='product')
    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220,blank=True)

    description = models.TextField("توضیحات", blank=True)

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
            if not self.slug:
                self.slug = slugify(self.name, allow_unicode=True)
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
        return self.images.filter(is_main=True).first()

    @property
    def variant(self):
        variant = self.variants.first()
        return variant if variant else 0


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="محصول",
    )

    color = models.CharField("رنگ", max_length=50)
    size = models.CharField("سایز", max_length=20,null=True,blank=True)

    price = models.PositiveBigIntegerField("قیمت (تومان)")
    discount = models.PositiveIntegerField("درصد تخفیف",default=0)

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
        return f"{self.product.name} | {self.color} | {self.size}"

    @property
    def final_price(self):
        return int(self.price * (100 - self.discount) / 100)

    @property
    def price_display(self):
        """نمایش قیمت با کاما"""
        return f"{self.price:,}"

    @property
    def final_price_display(self):
        """نمایش قیمت نهایی با کاما"""
        return f"{self.final_price:,}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول"
    )

    image = models.ImageField(upload_to="products/",verbose_name="تصویر")

    is_main = models.BooleanField(default=False,verbose_name="تصویر اصلی")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"

    def __str__(self):
        return f"تصویر {self.product.name}"