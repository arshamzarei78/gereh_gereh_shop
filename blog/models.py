from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class BlogCategory(models.Model):
    title = models.CharField("عنوان دسته‌بندی", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, allow_unicode=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی بلاگ"
        verbose_name_plural = "دسته‌بندی‌های بلاگ"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class BlogTag(models.Model):
    name = models.CharField("نام برچسب", max_length=50)
    slug = models.SlugField("اسلاگ", max_length=70, unique=True, allow_unicode=True, blank=True)

    class Meta:
        verbose_name = "برچسب بلاگ"
        verbose_name_plural = "برچسب‌های بلاگ"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        PUBLISHED = "published", "منتشر شده"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        verbose_name="نویسنده",
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        verbose_name="دسته‌بندی",
    )
    tags = models.ManyToManyField(
        BlogTag,
        blank=True,
        related_name="posts",
        verbose_name="برچسب‌ها",
    )

    title = models.CharField("عنوان مقاله", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220, unique=True, allow_unicode=True, blank=True)
    main_image = models.ImageField("تصویر اصلی", upload_to="blog/posts/")
    
    short_description = models.TextField("خلاصه مقاله (نمایش در لیست)", max_length=400)
    content = models.TextField("متن اصلی مقاله (بخش اول)")

    # فیلدهای اختیاری منطبق با گرافیک صفحه جزئیات قالب شما (۲ تصویر وسط متن + باکس نقل‌قول)
    sub_image_1 = models.ImageField("تصویر فرعی ۱ (اختیاری)", upload_to="blog/sub/", blank=True, null=True)
    sub_image_1_caption = models.CharField("توضیح تصویر فرعی ۱", max_length=250, blank=True)
    
    sub_image_2 = models.ImageField("تصویر فرعی ۲ (اختیاری)", upload_to="blog/sub/", blank=True, null=True)
    sub_image_2_caption = models.CharField("توضیح تصویر فرعی ۲", max_length=250, blank=True)

    quote_text = models.TextField("متن نقل‌قول / پیام ویژه (اختیاری)", blank=True)
    quote_author = models.CharField("گوینده نقل‌قول", max_length=100, blank=True)

    extra_content = models.TextField("ادامه متن مقاله (بخش پایانی - اختیاری)", blank=True)

    status = models.CharField(
        "وضعیت انتشار",
        max_length=15,
        choices=StatusChoices.choices,
        default=StatusChoices.PUBLISHED,
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"pk": self.pk, "slug": self.slug})

    def __str__(self):
        return self.title


class BlogComment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="مقاله",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments",
        verbose_name="کاربر",
    )
    content = models.TextField("متن نظر")
    is_approved = models.BooleanField("تایید شده برای نمایش؟", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "نظر بلاگ"
        verbose_name_plural = "نظرات بلاگ"
        ordering = ["-created_at"]

    def __str__(self):
        return f"نظر {self.user} روی {self.post.title}"