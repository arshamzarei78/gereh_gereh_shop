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