from django.contrib import admin
from .models import BlogCategory, BlogTag, Post, BlogComment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "short_description", "content")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("author",)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user__phone_number", "post__title", "content")
    list_editable = ("is_approved",)