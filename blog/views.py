from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from .models import Post, BlogCategory, BlogTag, BlogComment
from django.contrib import messages
from django.shortcuts import redirect

class BlogSidebarMixin:
    """
    میکسین مشترک برای تامین اطلاعات سایدبار (دسته‌بندی‌ها، پست‌های اخیر و تگ‌ها)
    در هر دو صفحه لیست مقالات و جزئیات مقاله
    """
    def get_sidebar_context(self):
        return {
            # شمارش تعداد پست‌های منتشر شده در هر دسته‌بندی با یک کوئری بهینه
            "blog_categories": BlogCategory.objects.annotate(
                post_count=Count("posts", filter=Q(posts__status=Post.StatusChoices.PUBLISHED))
            ).filter(post_count__gt=0),
            
            # ۳ پست آخر برای بخش "پست اخیر" در سایدبار
            "recent_posts": Post.objects.filter(
                status=Post.StatusChoices.PUBLISHED
            ).only("id", "title", "slug", "main_image", "short_description", "created_at")[:3],
            
            # برچسب‌های محبوب
            "blog_tags": BlogTag.objects.filter(
                posts__status=Post.StatusChoices.PUBLISHED
            ).distinct()[:15],
        }


class PostListView(BlogSidebarMixin, ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 6  # نمایش ۶ مقاله در هر صفحه

    def get_queryset(self):
        # واکشی بهینه نویسنده و دسته‌بندی + شمارش نظرات تایید شده هر پست
        queryset = (
            Post.objects.filter(status=Post.StatusChoices.PUBLISHED)
            .select_related("author", "category")
            .annotate(
                approved_comments_count=Count(
                    "comments", filter=Q(comments__is_approved=True)
                )
            )
        )

        # ۱. فیلتر بر اساس جستجوی متنی (پارامتر q در سایدبار)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(short_description__icontains=q) | Q(content__icontains=q)
            )

        # ۲. فیلتر بر اساس دسته‌بندی بلاگ
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # ۳. فیلتر بر اساس برچسب (Tag)
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تزریق اطلاعات سایدبار به کانتکست
        context.update(self.get_sidebar_context())

        # حفظ فیلترها (جستجو، دسته‌بندی یا تگ) هنگام ورق زدن صفحات (Pagination)
        query_dict = self.request.GET.copy()
        if "page" in query_dict:
            del query_dict["page"]
        query_string = query_dict.urlencode()
        context["query_string"] = f"{query_string}&" if query_string else ""

        return context


class PostDetailView(BlogSidebarMixin, DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return (
            Post.objects.filter(status=Post.StatusChoices.PUBLISHED)
            .select_related("author", "category")
            .prefetch_related("tags")
            .annotate(
                approved_comments_count=Count(
                    "comments", filter=Q(comments__is_approved=True)
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تزریق اطلاعات سایدبار به صفحه جزئیات
        context.update(self.get_sidebar_context())
        # ارسال لیست نظرات تایید شده این مقاله
        context["comments"] = self.object.comments.filter(is_approved=True).select_related("user")
        return context

    def post(self, request, *args, **kwargs):
        # این متد فرم ارسال نظر که با متد POST ارسال می‌شود را هندل می‌کند
        self.object = self.get_object()

        # بررسی لاگین بودن کاربر (محض اطمینان برای جلوگیری از ارسال مستقیم ریکوئست)
        if not request.user.is_authenticated:
            messages.error(request, "برای ثبت نظر ابتدا باید وارد حساب کاربری خود شوید.")
            return redirect(self.request.path_info)

        content = request.POST.get('content', '').strip()
        if content:
            # ایجاد و ذخیره نظر جدید در دیتابیس
            # نیاز به ایمپورت BlogComment در بالای فایل دارید
            BlogComment.objects.create(
                post=self.object,
                user=request.user,
                content=content,
            )
            messages.success(request, "دیدگاه شما با موفقیت ثبت شد و پس از تایید مدیریت نمایش داده خواهد شد.")
        else:
            messages.error(request, "لطفاً متن نظر خود را وارد کنید.")

        # بازگشت به همان صفحه مقاله و اسکرول خودکار به بخش نظرات
        return redirect(f"{self.request.path_info}#comments-section")