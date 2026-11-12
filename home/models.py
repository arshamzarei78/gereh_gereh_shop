from django.db import models
from django.core.validators import RegexValidator


class ContactMessage(models.Model):
    phone_regex = RegexValidator(
        regex=r"^09\d{9}$",
        message="شماره تلفن باید ۱۱ رقم بوده و با 09 شروع شود.",
    )

    full_name = models.CharField("نام و نام خانوادگی", max_length=150)
    email = models.EmailField("پست الکترونیک", blank=True, null=True)
    phone_number = models.CharField(
        "تلفن تماس", 
        max_length=11, 
        validators=[phone_regex]
    )
    message = models.TextField("متن پیام")
    is_read = models.BooleanField("بررسی شده؟", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "پیام تماس با ما"
        verbose_name_plural = "پیام‌های تماس با ما"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

class BannerAnimation(models.Model):
    image = models.ImageField(upload_to='banners/')
    h5 = models.CharField(max_length=30,verbose_name='عنوان کوچک',blank=True,null=True)
    span = models.CharField(max_length=25,verbose_name='قسمت رنگی عنوان کوچک',blank=True,null=True)
    title = models.CharField(max_length=50,verbose_name='عنوان اصلی')
    text = models.TextField(verbose_name='متن بنر')

    def __str__(self):
        return f"{self.h5}-{self.span}-{self.title}"

    class Meta:
        verbose_name_plural = "بخش انیمیشن بنر"


class SiteSetting(models.Model):
    """تنظیمات کلی سایت و اطلاعات فوتر"""
    about_footer = models.TextField(
        "متن معرفی کوتاه در فوتر",
        default="فروشگاه اینترنتی «گره گره»، ارائه‌دهنده انواع دست‌سازه‌های هنری مکرمه، دیوارکوب، آویز گلدان و محصولات بافتنی با بهترین الیاف طبیعی.",
    )
    address = models.CharField(
        "آدرس",
        max_length=300,
        default="تهران، کارگاه هنری گره گره (ارسال به سراسر کشور با پست پیشتاز)",
    )
    phone = models.CharField("شماره تماس", max_length=20, default="09365958252")
    email = models.EmailField("ایمیل", default="info@gereh-gereh.ir")
    
    # لینک شبکه‌های اجتماعی
    instagram_url = models.URLField("لینک اینستاگرام", blank=True, null=True)
    telegram_url = models.URLField("لینک تلگرام", blank=True, null=True)
    whatsapp_url = models.URLField("لینک واتساپ", blank=True, null=True)

    class Meta:
        verbose_name = "تنظیمات سایت و فوتر"
        verbose_name_plural = "تنظیمات سایت و فوتر"

    def __str__(self):
        return "تنظیمات اطلاعات فوتر گره گره"


class Newsletter(models.Model):
    """ذخیره شماره موبایل یا ایمیل کاربران در خبرنامه فوتر"""
    contact_info = models.CharField(
        "ایمیل یا شماره موبایل", 
        max_length=150, 
        unique=True
    )
    created_at = models.DateTimeField("تاریخ عضویت", auto_now_add=True)

    class Meta:
        verbose_name = "عضو خبرنامه"
        verbose_name_plural = "اعضای خبرنامه"
        ordering = ["-created_at"]

    def __str__(self):
        return self.contact_info