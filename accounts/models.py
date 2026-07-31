from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.core.validators import RegexValidator
from iranian_cities.models import Province, City


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(
            phone_number=phone_number,
            **extra_fields
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            phone_number=phone_number,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
    max_length=11,
    unique=True,
    validators=[
        RegexValidator(
            regex=r"^09\d{9}$",
            message="شماره موبایل معتبر نیست."
        )
    ]
)

    email = models.EmailField(
        blank=True,
        null=True
    )

    first_name = models.CharField(
        max_length=100,
        blank=True
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    address_name = models.CharField(
        max_length=100
    )

    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        verbose_name="استان"
    )

    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        verbose_name="شهر"
    )

    address = models.TextField(
        verbose_name="آدرس"
    )

    postal_code = models.CharField(
        max_length=10,
        verbose_name="کد پستی"
    )


    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.address_name} - {self.city}"