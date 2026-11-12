from django.contrib import messages
from django.db.models import Avg, ExpressionWrapper, F, FloatField, IntegerField, Min, Q
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView
from .models import Category, Product, ProductComment, ProductVariant


class PtoductView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.prefetch_related(
            "images",
            "variants__image",
            "category",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["comments"] = (
            self.object.comments.filter(is_approved=True)
            .select_related("user")
        )
        category_ids = [cat.id for cat in self.object.category.all()]
        
        context["related_products"] = (
            Product.objects.filter(category__id__in=category_ids)
            .exclude(id=self.object.id)
            .annotate(
                calculated_rating=Coalesce(
                    Avg("comments__rating", filter=Q(comments__is_approved=True)),
                    5.0,
                    output_field=FloatField(),
                )
            )
            .prefetch_related("images", "variants", "category")
            .distinct()
            .order_by("-created_at")[:6]
        )
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request, "برای ثبت نظر روی محصول ابتدا باید وارد حساب کاربری خود شوید."
            )
            return redirect(request.path_info)

        self.object = self.get_object()
        content = request.POST.get("content", "").strip()
        rating = request.POST.get("rating", 5)

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                rating = 5
        except (ValueError, TypeError):
            rating = 5

        if content:
            ProductComment.objects.create(
                product=self.object,
                user=request.user,
                rating=rating,
                content=content,
            )
            messages.success(
                request,
                "دیدگاه شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.",
            )
        else:
            messages.error(request, "لطفاً متن نظر خود را بنویسید.")

        return redirect(f"{request.path_info}#review")

class ProductListView(ListView):
    model = Product
    template_name = "products/products_list.html"
    context_object_name = "products"
    paginate_by = 12

    def apply_filters_and_sorting(self, queryset):
        """اعمال یکپارچه فیلترها و مرتب‌سازی با محاسبه دقیق قیمت پس از تخفیف"""
        
        # ۱. جستجوی متنی (در نام و توضیحات محصول)
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # ۲. فیلتر دسته‌بندی
        categories = [c for c in self.request.GET.getlist("category") if c.isdigit()]
        if categories:
            queryset = queryset.filter(category__id__in=categories)

        # ۳. تجمیع فیلترهای مربوط به Variant در یک دیکشنری واحد
        # (تا همه شرط‌ها روی یک تنوع واحد و موجود در انبار بررسی شوند)
        variant_filters = Q()
        colors = [c for c in self.request.GET.getlist("color") if c]
        sizes = [s for s in self.request.GET.getlist("size") if s]
        min_price = self.request.GET.get("min_price", "")
        max_price = self.request.GET.get("max_price", "")

        if colors:
            variant_filters &= Q(variants__color__in=colors)
        if sizes:
            variant_filters &= Q(variants__size__in=sizes)

        # فرمول قیمت نهایی (با احتساب تخفیف) در سطح دیتابیس
        discounted_price_expr = ExpressionWrapper(
            F("variants__price") * (100 - F("variants__discount")) / 100,
            output_field=IntegerField(),
        )

        queryset = queryset.annotate(
            min_variant_price=Min(discounted_price_expr),
            calculated_rating=Coalesce(
                Avg("comments__rating", filter=Q(comments__is_approved=True)),
                5.0,
                output_field=FloatField(),
            ),
        )

        if min_price.isdigit():
            variant_filters &= Q(min_variant_price__gte=int(min_price))
        if max_price.isdigit():
            variant_filters &= Q(min_variant_price__lte=int(max_price))

        if variant_filters:
            # اگر کاربر فیلتر رنگ/سایز/قیمت زده، فقط تنوع‌های موجود در انبار چک شوند
            queryset = queryset.filter(variant_filters, variants__stock__gt=0)

        queryset = queryset.distinct()

        # ۴. مرتب‌سازی
        sort_by = self.request.GET.get("sort", "newest")
        if sort_by == "cheapest":
            return queryset.order_by("min_variant_price", "-id")
        elif sort_by == "expensive":
            return queryset.order_by("-min_variant_price", "-id")
        elif sort_by == "rating":
            return queryset.order_by("-calculated_rating", "-id")
        return queryset.order_by("-id")

    def get_queryset(self):
        queryset = Product.objects.prefetch_related("category", "variants", "images")
        return self.apply_filters_and_sorting(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["available_colors"] = (
            ProductVariant.objects.filter(stock__gt=0)
            .exclude(color="")
            .values_list("color", flat=True)
            .distinct()
        )
        context["available_sizes"] = (
            ProductVariant.objects.filter(stock__gt=0)
            .exclude(size__isnull=True)
            .exclude(size="")
            .values_list("size", flat=True)
            .distinct()
        )

        context["selected_categories"] = self.request.GET.getlist("category")
        context["selected_colors"] = self.request.GET.getlist("color")
        context["selected_sizes"] = self.request.GET.getlist("size")
        context["current_sort"] = self.request.GET.get("sort", "newest")

        query_dict = self.request.GET.copy()
        query_dict.pop("page", None)

        query_string = query_dict.urlencode()
        context["query_string"] = f"{query_string}&" if query_string else ""

        return context


class SearchView(ProductListView):
    pass