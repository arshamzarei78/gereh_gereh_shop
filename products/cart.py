from .models import ProductVariant 
from django.shortcuts import get_object_or_404
CART_SESSION_ID = 'cart'

CART_SESSION_ID = "cart"


CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_ID, {})

    def save(self):
        self.session.modified = True

    def add(self, variant, quantity=1, override_quantity=False):
        """
        افزودن تنوع محصول به سبد خرید
        """
        variant_id = str(variant.id)

        # اگر آیتم جدید است، قیمت فعلی را ذخیره می‌کنیم
        if variant_id not in self.cart:
            self.cart[variant_id] = {
                "quantity": 0,
                "price": int(variant.final_price), # قیمت تخفیف خورده نهایی
            }

        item = self.cart[variant_id]

        # محاسبه تعداد جدید
        new_quantity = quantity if override_quantity else item["quantity"] + quantity

        # بررسی موجودی انبار (اختیاری ولی توصیه شده)
        if new_quantity > variant.stock:
            new_quantity = variant.stock

        item["quantity"] = new_quantity
        
        # اگر تعداد صفر شد، آیتم حذف شود
        if item["quantity"] <= 0:
            self.remove(variant)
        else:
            self.save()

    def remove(self, variant):
        """حذف یک تنوع محصول از سبد خرید"""
        variant_id = str(variant.id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def __iter__(self):
        """
        پیمایش روی آیتم‌های سبد خرید و دریافت اطلاعات از دیتابیس
        """
        variant_ids = self.cart.keys()

        # بهینه‌سازی کوئری: دریافت تنوع‌ها به همراه محصول و تصاویر مربوط به محصول
        variants = (
            ProductVariant.objects.filter(id__in=variant_ids)
            .select_related("product")
            .prefetch_related("product__images")
        )

        cart_copy = self.cart.copy()

        for variant in variants:
            item = cart_copy[str(variant.id)]
            
            # افزودن خود Object تنوع محصول جهت دسترسی به رنگ، سایز، تصویر و ...
            item["variant"] = variant
            item["total_price"] = item["price"] * item["quantity"]
            
            yield item

    def __len__(self):
        """تعداد کل کالاهای درون سبد خرید"""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """مجموع مبلغ کل سبد خرید (تومان)"""
        return sum(item["price"] * item["quantity"] for item in self.cart.values())

    def clear(self):
        """پاک کردن کامل سبد خرید از session"""
        del self.session[CART_SESSION_ID]
        self.save()