from django.shortcuts import render
from django.views.generic import DetailView,ListView
from .models import Product
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ProductVariant


class PtoductView(DetailView):
    model = Product

class ProductListView(ListView):
    model = Product
    template_name = 'products/products_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ارسال لیست رنگ‌ها و سایزهای یکتا (بدون تکرار) که موجودی دارند به قالب
        context['available_colors'] = (
            ProductVariant.objects.filter(stock__gt=0)
            .values_list('color', flat=True).distinct()
        )
        context['available_sizes'] = (
            ProductVariant.objects.filter(stock__gt=0, size__isnull=False)
            .exclude(size='')
            .values_list('size', flat=True).distinct()
        )
        
        # ارسال لیست گزینه‌های تیک‌خورده برای اینکه بعد از رفرش صفحه، تیک آن‌ها نپرد
        context['selected_categories'] = self.request.GET.getlist('category')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_sizes'] = self.request.GET.getlist('size')

        query_dict = self.request.GET.copy()
        
        # پارامتر page قبلی را از آن حذف می‌کنیم تا تکراری نشود
        if 'page' in query_dict:
            del query_dict['page']
            
        query_string = query_dict.urlencode()
        
        # اگر فیلتری وجود داشت، یک & به آخر آن اضافه می‌کنیم تا به شماره صفحه بچسبد
        if query_string:
            context['query_string'] = f"{query_string}&"
        else:
            context['query_string'] = ""
        
        return context


class SearchView(ProductListView):
    
    def get_queryset(self):
        queryset = Product.objects.all()
        
        # ۱. دریافت متن جستجو
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)
            
        # ۲. فیلتر دسته‌بندی (پشتیبانی از انتخاب چند دسته‌بندی همزمان با getlist)
        categories = [c for c in self.request.GET.getlist('category') if c.isdigit()]
        if categories:
            queryset = queryset.filter(category__id__in=categories)

        # ۳. فیلتر رنگ‌ها (از طریق ارتباط با جدول variants)
        colors = self.request.GET.getlist('color')
        if colors:
            queryset = queryset.filter(variants__color__in=colors)

        # ۴. فیلتر سایزها
        sizes = self.request.GET.getlist('size')
        if sizes:
            queryset = queryset.filter(variants__size__in=sizes)

        # ۵. فیلتر محدوده قیمت
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price and min_price.isdigit():
            queryset = queryset.filter(variants__price__gte=min_price)
        if max_price and max_price.isdigit():
            queryset = queryset.filter(variants__price__lte=max_price)
            
        # استفاده از distinct() بسیار مهم است تا اگر محصولی ۲ رنگ داشت، ۲ بار در نتایج تکرار نشود
        return queryset.distinct()
