from products.models import ProductVariant 
from django.shortcuts import get_object_or_404

CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart
        self._variants_cache = None

    def _format_price(self, amount):
        """متد کمکی برای ۳ رقم ۳ رقم کردن اعداد"""
        return f"{amount:,}"
    
    def _get_total_item_price(self, item):
        """متد کمکی برای محاسبه قیمت کل یک آیتم"""
        return item["price"] * item["quantity"]
    
    def _get_total_item_no_discount(self, item):
        """متد کمکی برای محاسبه قیمت کل یک آیتم"""
        return item["no_discount"] * item["quantity"]

    def save(self):
        self._variants_cache = None
        self.session.modified = True

    def add(self, variant, quantity=1, override_quantity=False):
        """افزودن تنوع محصول به سبد خرید"""
        variant_id = str(variant.id)

        if variant_id not in self.cart:
            self.cart[variant_id] = {
                "quantity": 0,
                "price": int(variant.final_price),
                "no_discount" : int(variant.price),
            }

        item = self.cart[variant_id]

        new_quantity = quantity if override_quantity else item["quantity"] + quantity

        if new_quantity > variant.stock:
            new_quantity = variant.stock

        item["quantity"] = new_quantity
        
        if item["quantity"] <= 0:
            self.remove(variant)
        else:
            self.cart[variant_id]["quantity"] = new_quantity
            self.cart[variant_id]["price"] = int(variant.final_price)
            self.cart[variant_id]["no_discount"] = int(variant.price)
            self.save()

    def remove(self, variant):
        """حذف یک تنوع محصول از سبد خرید"""
        variant_id = str(variant.id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def _get_variants(self):
        """واکشی بهینه محصولات از دیتابیس به همراه همگام‌سازی موجودی و قیمت"""
        if self._variants_cache is None:
            variant_ids = list(self.cart.keys())
            variants = (
                ProductVariant.objects.filter(id__in=variant_ids)
                .select_related("product")
                .prefetch_related("product__images")
            )
            
            valid_ids = set()
            session_changed = False

            for variant in variants:
                v_id = str(variant.id)
                valid_ids.add(v_id)
                item = self.cart[v_id]

                # ۱. اگر موجودی محصول در انبار تمام شده، از سبد حذف شود
                if variant.stock <= 0:
                    del self.cart[v_id]
                    session_changed = True
                    continue

                # ۲. اگر موجودی انبار کمتر از تعداد داخل سبد شده، تعداد سبد اصلاح شود
                if item["quantity"] > variant.stock:
                    item["quantity"] = variant.stock
                    session_changed = True

                # ۳. بروزرسانی قیمت‌های سشن با قیمت لحظه‌ای دیتابیس (جلوگیری از باگ قیمت قدیمی)
                current_price = int(variant.final_price)
                current_raw_price = int(variant.price)
                if item.get("price") != current_price or item.get("no_discount") != current_raw_price:
                    item["price"] = current_price
                    item["no_discount"] = current_raw_price
                    session_changed = True

            # ۴. حذف آیتم‌هایی که کلاً از دیتابیس پاک شده‌اند
            for v_id in variant_ids:
                if v_id not in valid_ids and v_id in self.cart:
                    del self.cart[v_id]
                    session_changed = True

            if session_changed:
                self.session.modified = True

            self._variants_cache = [v for v in variants if str(v.id) in self.cart]

        return self._variants_cache
    

    def __iter__(self):
        """پیمایش روی آیتم‌های سبد خرید"""
        variants = self._get_variants()

        # ✅ ساخت یک کپی عمیق از دیکشنری‌های داخلی برای جلوگیری از آلودگی Session
        cart_copy = {k: v.copy() for k, v in self.cart.items()}

        for variant in variants:
            item = cart_copy[str(variant.id)]
            item["variant"] = variant
            item["total_price"] = self._get_total_item_price(item)
            item["total_no_discount"] = item["no_discount"] * item["quantity"]
            item["total_discount"] = item["total_no_discount"] - item["total_price"]
            item["total_price_display"] = self._format_price(item["total_price"])
            item["total_no_discount_display"] = self._format_price(self._get_total_item_no_discount(item))
            yield item

    def __len__(self):
        """تعداد کل کالاهای درون سبد خرید"""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """مجموع مبلغ کل سبد خرید (تومان)"""
        self._get_variants()
        return sum(self._get_total_item_price(item) for item in self.cart.values())

    def get_total_price_display(self):
        """نمایش مجموع مبلغ کل با جداکننده ۳ رقم"""
        return self._format_price(self.get_total_price())
    
    def get_total_no_discount(self):
        """مجموع قیمت کل سبد خرید بدون اعمال هیچ تخفیفی (خروجی عدد)"""
        self._get_variants()
        return sum(self._get_total_item_no_discount(item) for item in self.cart.values())

    def get_total_no_discount_display(self):
        """نمایش مجموع مبلغ کل بدون تخفیف با جداکننده ۳ رقم"""
        return self._format_price(self.get_total_no_discount())

    def get_total_discount(self):
        """سود مشتری از این خرید (مجموع تخفیف‌ها)"""
        return self.get_total_no_discount() - self.get_total_price()

    def get_total_discount_display(self):
        return self._format_price(self.get_total_discount())
    
    def clear(self):
        """پاک کردن کامل سبد خرید از session"""
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
            self.save()