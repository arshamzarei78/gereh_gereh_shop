from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User , Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):

    list_display = (
            "user",
            "get_user_full_name",
            "address_name",
            "province",
            "city",
            "postal_code",
            "is_default",
            "created_at",)

    list_filter = ("province","created_at")
    search_fields = (
        "user__phone_number",   # جستجو بر اساس شماره تلفن کاربر
        "user__first_name",     # جستجو بر اساس نام کاربر
        "user__last_name",      # جستجو بر اساس نام خانوادگی کاربر
        "postal_code",
        "address"
    )
    
    # برای بهینه‌سازی کوئری‌های دیتابیس در پنل ادمین
    list_select_related = ("user", "province", "city")

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()
    
    # تغییر عنوان این ستون در پنل ادمین
    get_user_full_name.short_description = "نام و نام خانوادگی"

    
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "email",
            "first_name",
            "last_name",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "phone_number",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = (
        "phone_number",
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("phone_number",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone_number",
                    "password",
                )
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "created_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "last_login",
    )