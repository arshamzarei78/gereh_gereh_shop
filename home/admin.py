from django.contrib import admin
from .models import ContactMessage,BannerAnimation,SiteSetting,Newsletter


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    list_editable = ("is_read",)
    search_fields = ("full_name", "phone_number", "message")
    readonly_fields = ("created_at",)

@admin.register(BannerAnimation)
class BannerAnimationAdmin(admin.ModelAdmin):
    list_display = ("image", "h5", "span","title")

from django.contrib import admin
from .models import ContactMessage, SiteSetting, Newsletter


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("phone", "email", "address")

    def has_add_permission(self, request):
        # جلوگیری از ساخت بیش از یک رکورد تنظیمات
        if SiteSetting.objects.exists():
            return False
        return True


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("contact_info", "created_at")
    search_fields = ("contact_info",)
    readonly_fields = ("created_at",)