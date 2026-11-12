from django.shortcuts import render
from django.views.generic import DetailView,ListView
from .models import Product,ProductComment
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db.models.functions import Coalesce
from django.db.models import Min, Avg, Q, FloatField
from django.contrib import messages
from .models import ProductVariant


class PtoductView(DetailView):
    model = Product
    template_name = "products/product_detail.html" 
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.prefetch_related(
            "images",
            "variants__image",
            "category"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # نظرات تایید شده این محصول
        context["comments"] = self.object.comments.filter(is_approved=True).select_related("user")
        
        # محصولات مشابه (بر اساس دسته‌بندی‌های مشترک، به جز خود محصول فعلی)
        context["related_products"] = (
            Product.objects.filter(category__in=self.object.category.all())
            .exclude(id=self.object.id)
            .prefetch_related("images", "variants", "category")
            .distinct()[:6]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            messages.error(request, "برای ثبت نظر روی محصول ابتدا باید وارد حساب کاربری خود شوید.")
            return redirect(self.request.path_info)

        content = request.POST.get("content", "").strip()
        rating = request.POST.get("rating", 5)

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                rating = 5
        except ValueError:
            rating = 5

        if content:
            ProductComment.objects.create(
                product=self.object,
                user=request.user,
                rating=rating,
                content=content,
            )
            messages.success(request, "دیدگاه شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.")
        else:
            messages.error(request, "لطفاً متن نظر خود را بنویسید.")

        return redirect(f"{self.request.path_info}#review")

class ProductListView(ListView):
    model = Product
    template_name = 'products/products_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def apply_sorting(self, queryset):
        """متد مشترک برای مرتب‌سازی در لیست محصولات و صفحه سرچ"""
        queryset = queryset.annotate(
            min_variant_price=Min('variants__price'),
            avg_rating=Coalesce(
                Avg('comments__rating', filter=Q(comments__is_approved=True)),
                5.0,
                output_field=FloatField(),
            ),
        ).distinct()

        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'cheapest':
            return queryset.order_by('min_variant_price', '-id')
        elif sort_by == 'expensive':
            return queryset.order_by('-min_variant_price', '-id')
        elif sort_by == 'rating':
            return queryset.order_by('-avg_rating', '-id')
        return queryset.order_by('-id')  # پیش‌فرض: جدیدترین

    def get_queryset(self):
        queryset = Product.objects.prefetch_related('category', 'variants', 'images').all()
        return self.apply_sorting(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['available_colors'] = (
            ProductVariant.objects.filter(stock__gt=0)
            .values_list('color', flat=True).distinct()
        )
        context['available_sizes'] = (
            ProductVariant.objects.filter(stock__gt=0, size__isnull=False)
            .exclude(size='')
            .values_list('size', flat=True).distinct()
        )
        
        context['selected_categories'] = self.request.GET.getlist('category')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_sizes'] = self.request.GET.getlist('size')
        context['current_sort'] = self.request.GET.get('sort', 'newest')

        query_dict = self.request.GET.copy()
        if 'page' in query_dict:
            del query_dict['page']
            
        query_string = query_dict.urlencode()
        context['query_string'] = f"{query_string}&" if query_string else ""
        
        return context
class SearchView(ProductListView):
    
    def get_queryset(self):
        queryset = Product.objects.prefetch_related('category', 'variants', 'images').all()
        
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)
            
        categories = [c for c in self.request.GET.getlist('category') if c.isdigit()]
        if categories:
            queryset = queryset.filter(category__id__in=categories)

        colors = self.request.GET.getlist('color')
        if colors:
            queryset = queryset.filter(variants__color__in=colors)

        sizes = self.request.GET.getlist('size')
        if sizes:
            queryset = queryset.filter(variants__size__in=sizes)

        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price and min_price.isdigit():
            queryset = queryset.filter(variants__price__gte=min_price)
        if max_price and max_price.isdigit():
            queryset = queryset.filter(variants__price__lte=max_price)
            
        return self.apply_sorting(queryset)