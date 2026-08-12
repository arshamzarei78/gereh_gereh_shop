(function ($) {
    "use strict";

    $(window).on("load", function () {
        $("#cr-overlay").fadeOut("slow");
    });

    $(document).ready(function () {
        
        
        // وقتی کاربر گزینه‌ای را از لیست انتخاب می‌کند
    $('#variant-select').on('change', function() {
        // گرفتن گزینه‌ی انتخاب شده
        var selectedOption = $(this).find('option:selected');
        
        // خواندن موجودی و قیمت از data-attributes
        var newStock = selectedOption.attr('data-stock');
        var newPrice = selectedOption.attr('data-price');
        
        // ۱. به‌روزرسانی متن موجودی در لیست
        $('#dynamic-stock').text(newStock);
        
        // ۲. به‌روزرسانی متن قیمت
        $('#dynamic-price').text(newPrice + ' تومان');
        
        // ۳. به‌روزرسانی سقف انتخاب تعداد (max) برای دکمه‌های + و -
        var $qtyInput = $('#qty-input');
        $qtyInput.attr('max', newStock);
        
        // ۴. اگر تعدادی که کاربر قبلا انتخاب کرده بود، بیشتر از موجودی تنوع جدید بود، تعداد را روی 1 تنظیم کن
        var currentQty = parseInt($qtyInput.val());
        if (currentQty > newStock) {
            $qtyInput.val(newStock > 0 ? 1 : 0);
        }
    });



        /* -----------------------------------------------------------
         * ۱. مدیریت Ajax افزودن به سبد خرید و نمایش سایدبار
         * ----------------------------------------------------------- */
        $(document).on('submit', '#add-to-cart-form', function (e) {
            e.preventDefault();

            const form = $(this);
            const actionUrl = form.attr('action');
            const formData = form.serialize();
            const csrftoken = form.find('input[name="csrfmiddlewaretoken"]').val();

        $.ajax({
            url: actionUrl,
            type: 'POST',
            data: formData,
            headers: { 
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function (response) {
                if (response.status === 'success') {
                    // ۱. جایگزینی محتوای سایدبار
                    $('#cart-sidebar-inner').html(response.sidebar_html);

                    // ۲. به‌روزرسانی تعداد در هدر
                    $('.cart-badge, .header-cart-count').text(response.total_items);

                    // ۳. نمایش مستقیم نوتیفیکیشن موفقیت (بدون نیاز به رویداد کلیک مجدد)
                    $('.cr-wish-notify, .cr-compare-notify, .cr-cart-notify').remove();
                    $('footer').after('<div class="cr-cart-notify"><p class="compare-note">اضافه کردن محصول به <a href="cart.html">سبد خرید</a> موفقیت آمیز بود!</p></div>');
                    setTimeout(function () { $('.cr-cart-notify').fadeOut(); }, 2000);

                    // ۴. باز کردن سایدبار
                    $(".cr-cart-view").addClass("cr-cart-view-active");
                    $(".cr-cart-overlay").fadeIn();
                }
            },
            error: function (xhr) {
                const res = xhr.responseJSON;
                alert(res && res.message ? res.message : 'خطایی رخ داد.');
            }
        });
        });

        /* مدیریت باز و بستن سایدبار سبد خرید */
        $(document).on("click", ".Shopping-toggle", function (e) {
            e.preventDefault();
            $(".cr-cart-view").addClass("cr-cart-view-active");
            $(".cr-cart-overlay").fadeIn();
        });

        $(document).on("click", ".close-cart, .cr-cart-overlay", function (e) {
            e.preventDefault();
            $(".cr-cart-view").removeClass("cr-cart-view-active");
            $(".cr-cart-overlay").fadeOut();
        });

        /* -----------------------------------------------------------
         * ۲. تنظیمات عمومی و پلاگین‌ها
         * ----------------------------------------------------------- */
        if (typeof AOS !== 'undefined') {
            AOS.init({ once: true });
        }

        /* Product grid & column */
        $(".gridRow").on("click", function () {
            $(".col-100, .col-50").addClass("col-size");
        });

        $(".gridCol").on("click", function () {
            $(".col-100, .col-50").removeClass("col-size");
        });

        $(".cr-toggle a").on("click", function (e) {
            e.preventDefault();
            $(".cr-toggle a").removeClass("active-grid");
            $(this).addClass("active-grid");
        });

        /* Minus and Plus Quantity */
        $(document).on("click", ".minus", function (e) {
    e.preventDefault();
    var $input = $(this).parent().find('input');
    var count = parseInt($input.val()) - 1;
    count = count < 1 ? 1 : count;
    $input.val(count).change();
});

$(document).on("click", ".plus", function (e) {
    e.preventDefault();
    var $input = $(this).parent().find('input');
    var currentVal = parseInt($input.val());
    
    // دریافت سقف موجودی از خصیصه max (در صورت عدم وجود، پیش‌فرض ۱۰ قرار می‌گیرد)
    var maxStock = parseInt($input.attr('max'));
    if (isNaN(maxStock)) {
        maxStock = 10; 
    }

    var count = currentVal + 1;

    // چک کردن محدودیت موجودی انبار
    if (count <= maxStock) {
        $input.val(count).change();
    } else {
        alert("تعداد درخواستی بیشتر از موجودی انبار است. ");
    }
});

        /* Onclick Remove Products */
        $(document).on("click", ".cr-remove-product", function () {
            $(this).closest(".cr-product-box").remove();
            if ($(".cr-product-box").length === 0) {
                $('.section-wishlist').html('<p class="cr-wishlist-msg">لیست علاقه مندی شما خالی است!</p>');
                $('.section-compare').html('<p class="cr-wishlist-msg">لیست مقایسه شما خالی است!</p>');
            }
        });

        /* Sticky header on scroll */
        var doc = document.documentElement;
        var w = window;
        var crPrevScroll = w.scrollY || doc.scrollTop;
        var crCurScroll;
        var crDirection = 0;
        var crPrevDirection = 0;

        var checkScroll = function () {
            crCurScroll = w.scrollY || doc.scrollTop;
            if (crCurScroll > crPrevScroll) {
                crDirection = 2; // scrolled down
            } else if (crCurScroll < crPrevScroll) {
                crDirection = 1; // scrolled up
            }

            if (crDirection !== crPrevDirection) {
                toggleHeader(crDirection, crCurScroll);
            }
            crPrevScroll = crCurScroll;
        };

        var toggleHeader = function (crDirection, crCurScroll) {
            if (crDirection === 2 && crCurScroll > -46) {
                crPrevDirection = crDirection;
                $("#cr-main-menu-desk").addClass("menu_fixed_up");
            } else if (crDirection === 1) {
                crPrevDirection = crDirection;
                $("#cr-main-menu-desk").addClass("menu_fixed").removeClass("menu_fixed_up");
            }
        };

        $(window).on("scroll", function () {
            var $target = $('.next, .section-breadcrumb');
            if ($target.length) {
                var distance = $target.offset().top;
                if ($(window).scrollTop() <= distance + 5) {
                    $("#cr-main-menu-desk").removeClass("menu_fixed");
                } else {
                    checkScroll();
                }
            }
        });

        /* -----------------------------------------------------------
         * ۳. اسلایدرها (Swiper & Slick)
         * ----------------------------------------------------------- */
        if ($('.cr-service-slider').length) {
            new Swiper('.cr-service-slider', {
                loop: true,
                slidesPerView: 4,
                spaceBetween: 24,
                breakpoints: {
                    1399: { slidesPerView: 4, spaceBetween: 24 },
                    1028: { slidesPerView: 3, spaceBetween: 24 },
                    480: { slidesPerView: 2, spaceBetween: 24 },
                    0: { slidesPerView: 1, spaceBetween: 10 }
                }
            });
        }

        if ($('.cr-popular-product').length) {
            $('.cr-popular-product').slick({
                infinite: true,
                rtl: true,
                dots: false,
                arrows: false,
                slidesToShow: 5,
                slidesToScroll: 1,
                autoplay: true,
                autoplaySpeed: 3000,
                responsive: [
                    { breakpoint: 1400, settings: { slidesToShow: 4 } },
                    { breakpoint: 1200, settings: { slidesToShow: 3 } },
                    { breakpoint: 992, settings: { slidesToShow: 2 } },
                    { breakpoint: 481, settings: { slidesToShow: 1 } }
                ]
            });
        }

        if ($('.cr-blog-slider').length) {
            new Swiper('.cr-blog-slider', {
                loop: true,
                slidesPerView: 3,
                spaceBetween: 24,
                breakpoints: {
                    1600: { slidesPerView: 4, spaceBetween: 24 },
                    991: { slidesPerView: 3, spaceBetween: 24 },
                    576: { slidesPerView: 2, spaceBetween: 24 },
                    0: { slidesPerView: 1, spaceBetween: 10 }
                }
            });
        }

        if ($('.cr-testimonial-slider').length) {
            new Swiper('.cr-testimonial-slider', {
                loop: true,
                slidesPerView: 3,
                spaceBetween: 24,
                breakpoints: {
                    1028: { slidesPerView: 3, spaceBetween: 24 },
                    576: { slidesPerView: 2, spaceBetween: 24 },
                    0: { slidesPerView: 1, spaceBetween: 10 }
                }
            });
        }

        if ($('.cr-banner-slider').length) {
            new Swiper('.cr-banner-slider', {
                loop: true,
                slidesPerView: 2,
                spaceBetween: 24,
                autoplay: true,
                breakpoints: {
                    1200: { slidesPerView: 3, spaceBetween: 24 },
                    768: { slidesPerView: 2, spaceBetween: 24 },
                    0: { slidesPerView: 1, spaceBetween: 10 }
                }
            });
        }

        if ($('.cr-twocolumns-product').length) {
            $('.cr-twocolumns-product').slick({
                infinite: true,
                rtl: true,
                dots: false,
                arrows: false,
                slidesToShow: 3,
                slidesToScroll: 1,
                autoplay: true,
                autoplaySpeed: 3000,
                responsive: [
                    { breakpoint: 1400, settings: { slidesToShow: 2 } },
                    { breakpoint: 481, settings: { slidesToShow: 1 } }
                ]
            });
        }

        if ($('.tablist-swiper').length) {
            new Swiper('.tablist-swiper', {
                direction: 'vertical',
                slidesPerView: 6
            });
        }

        if ($('.cr-insta-slider').length) {
            new Swiper('.cr-insta-slider', {
                speed: 500,
                spaceBetween: 12,
                autoplay: false,
                disableOnInteraction: true,
                loop: true,
                slidesPerView: 4,
                allowTouchMove: true,
                breakpoints: {
                    576: { slidesPerView: 5 },
                    768: { slidesPerView: 6 },
                    992: { slidesPerView: 8 },
                    1200: { slidesPerView: 4 },
                    1400: { slidesPerView: 5 }
                }
            });
        }

        if ($('.cr-slider').length) {
            new Swiper('.cr-slider', {
                loop: true,
                centeredSlides: true,
                speed: 2000,
                effect: 'slide',
                parallax: true,
                autoplay: { delay: 10000, disableOnInteraction: false },
                pagination: { el: '.swiper-pagination', clickable: true },
                navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' }
            });
        }

        /* -----------------------------------------------------------
         * ۴. اعلان‌ها (Notifications)
         * ----------------------------------------------------------- */
        $(document).on("click", '.wishlist', function () {
            $('.cr-wish-notify, .cr-compare-notify, .cr-cart-notify').remove();
            var isWishlist = $(this).hasClass("active");
            if (isWishlist) {
                $(this).removeClass("active");
                $('footer').after('<div class="cr-wish-notify"><p class="wish-note">حذف محصول از <a href="wishlist.html">لیست علاقه مندی</a> موفقیت آمیز بود!</p></div>');
            } else {
                $(this).addClass("active");
                $('footer').after('<div class="cr-wish-notify"><p class="wish-note">اضافه کردن محصول به <a href="wishlist.html">لیست علاقه مندی</a> موفقیت آمیز بود!</p></div>');
            }
            setTimeout(function () { $('.cr-wish-notify').fadeOut(); }, 2000);
        });

        /* Product Image Zoom & Range Slider */
        if ($.fn.zoom && $('.zoom-image-hover').length) {
            $('.zoom-image-hover').zoom();
        }

        if ($.fn.slider && $("#slider-range").length) {
            $("#slider-range").slider({
                range: true,
                min: 20,
                max: 300,
                values: [0, 250],
                slide: function (event, ui) {
                    $("#amount").val(ui.values[0] + " تومان - " + ui.values[1] + " تومان ");
                }
            });
            $("#amount").val($("#slider-range").slider("values", 0) + " تومان - " + $("#slider-range").slider("values", 1) + " تومان ");
        }

        /* Tab to top */
        $(window).scroll(function () {
            if ($(this).scrollTop() > 50) {
                $(".back-to-top").fadeIn();
            } else {
                $(".back-to-top").fadeOut();
            }
        });

        /* Mobile Menu */
        $(".navbar-toggler").on("click", function () {
            $(".cr-sidebar-overlay").fadeIn();
            $(".cr-mobile-menu").addClass("cr-menu-open");
        });

        $(".cr-sidebar-overlay, .cr-close").on("click", function () {
            $(".cr-sidebar-overlay").fadeOut();
            $(".cr-mobile-menu").removeClass("cr-menu-open");
        });

        $(".drop-list > a").on("click", function () {
            $(".sub-menu").slideUp(600);
            if ($(this).parent().hasClass("active")) {
                $(".drop-list").removeClass("active");
            } else {
                $(".drop-list").removeClass("active");
                $(this).next(".sub-menu").slideDown(600);
                $(this).parent().addClass("active");
            }
        });

        /* Footer Toggle */
        $(".cr-footer-links").addClass("active-drop-footer");
        $('.cr-sub-title').append("<div class='cr-heading-res'><i class='ri-arrow-down-s-line' aria-hidden='true'></i></div>");
        $(".cr-sub-title .cr-heading-res").on("click", function () {
            var $this = $(this).closest('.footer-top .col-sm-12').find('.cr-footer-dropdown');
            $this.slideToggle('slow');
            $('.cr-footer-dropdown').not($this).slideUp('slow');
        });

        /* Product kg */
        $(".cr-kg ul li").on("click", function () {
            $(".cr-kg ul li").removeClass("active-color");
            $(this).addClass("active-color");
        });

        /* Counter */
        if ($('.elementor-counter-number').length) {
            $('.elementor-counter-number').each(function () {
                var size = $(this).text().split(".")[1] ? $(this).text().split(".")[1].length : 0;
                $(this).prop('Counter', 0).animate({
                    Counter: $(this).text()
                }, {
                    duration: 5000,
                    step: function (func) {
                        $(this).text(parseFloat(func).toFixed(size));
                    }
                });
            });
        }

        /* Deal Timer */
        function makeTimer() {
            var endTime = new Date("29 December 2024 9:56:00 GMT+01:00");
            endTime = (Date.parse(endTime) / 1000);
            var now = new Date();
            now = (Date.parse(now) / 1000);
            var timeLeft = endTime - now;
            var days = Math.floor(timeLeft / 86400);
            var hours = Math.floor((timeLeft - (days * 86400)) / 3600);
            var minutes = Math.floor((timeLeft - (days * 86400) - (hours * 3600)) / 60);
            var seconds = Math.floor((timeLeft - (days * 86400) - (hours * 3600) - (minutes * 60)));
            if (hours < "10") { hours = "0" + hours; }
            if (minutes < "10") { minutes = "0" + minutes; }
            if (seconds < "10") { seconds = "0" + seconds; }
            $("#days").html(days);
            $("#hours").html(hours);
            $("#minutes").html(minutes);
            $("#seconds").html(seconds);
        }
        if ($("#days").length) {
            setInterval(makeTimer, 1000);
        }

        /* Products-page model */
        $(".model-oraganic-product").on("click", function () {
            $(".cr-model-overlay, .cr-model").fadeIn();
        });

        $(".cr-close-model, .cr-model-overlay").on("click", function () {
            $(".cr-model-overlay, .cr-model").fadeOut();
        });

        /* Shop-side-view */
        $(".shop_side_view").on("click", function (e) {
            e.preventDefault();
            $(".cr-shop-leftside").addClass("cr-shop-leftside-active");
            $(".filter-sidebar-overlay").fadeIn();
        });

        $(".filter-sidebar-overlay, .close-shop-leftside").on("click", function () {
            $(".cr-shop-leftside").removeClass("cr-shop-leftside-active");
            $(".filter-sidebar-overlay").fadeOut();
        });

        /* Portfolio */
        $(".cr-product-tabs ul li").on("click", function () {
            $(".cr-product-tabs ul li").removeClass("active");
            $(this).addClass("active");
        });

        if ($.fn.mixItUp && $(".product-content").length) {
            $(".product-content").mixItUp();
        }

        /* Back to top button progress */
        var progressPath = document.querySelector('.back-to-top-wrap path');
        if (progressPath) {
            var pathLength = progressPath.getTotalLength();
            progressPath.style.transition = progressPath.style.WebkitTransition = 'none';
            progressPath.style.strokeDasharray = pathLength + ' ' + pathLength;
            progressPath.style.strokeDashoffset = pathLength;
            progressPath.getBoundingClientRect();
            progressPath.style.transition = progressPath.style.WebkitTransition = 'stroke-dashoffset 10ms linear';
            
            var updateProgress = function () {
                var scroll = $(window).scrollTop();
                var height = $(document).height() - $(window).height();
                var progress = pathLength - (scroll * pathLength / height);
                progressPath.style.strokeDashoffset = progress;
            };
            
            updateProgress();
            $(window).scroll(updateProgress);
            
            var offset = 50;
            var duration = 550;
            $(window).on('scroll', function () {
                if ($(this).scrollTop() > offset) {
                    $('.back-to-top-wrap').addClass('active-progress');
                } else {
                    $('.back-to-top-wrap').removeClass('active-progress');
                }
            });
            $('.back-to-top-wrap').on('click', function (event) {
                event.preventDefault();
                $('html, body').animate({ scrollTop: 0 }, duration);
                return false;
            });
        }

        /* Sidebar Tools & Color Switcher */
        $(".btn-cr-tool").on("click", function (e) {
            e.preventDefault();
            $(".cr-tool").addClass("cr-tool-active");
            $(".cr-tool-overlay").fadeIn();
            $(".btn-cr-tool").fadeOut();
        });

        $(".close-tools, .cr-tool-overlay").on("click", function () {
            $(".cr-tool").removeClass("cr-tool-active");
            $(".cr-tool-overlay").fadeOut();
            $(".btn-cr-tool").fadeIn();
        });

        $(".cr-color li").on("click", function () {
            $(".cr-color li").removeClass("active-colors");
            $(this).addClass("active-colors");
        });

        for (let i = 1; i <= 10; i++) {
            $(`.c${i}`).on("click", function () {
                $("#add_class").remove();
                if (i > 1) {
                    $("head").append(`<link rel="stylesheet" href="assets/css/color-${i-1}.css" id="add_class">`);
                }
            });
        }

        /* Dark Mode */
        $(".dark-mode li").on("click", function () {
            $(".dark-mode li").removeClass("active-dark-mode");
            $(this).addClass("active-dark-mode");
        });

        $(".dark").on("click", function () {
            $("#add_dark_mode").remove();
            $("head").append('<link rel="stylesheet" class="dark-link-mode" href="assets/css/dark.css" id="add_dark_mode">');
        });
        $(".white").on("click", function () {
            $("#add_dark_mode").remove();
        });

        /* Background switcher */
        $(".bg-panel li").on("click", function () {
            $(".bg-panel li").removeClass("active-bg-panel");
            $(this).addClass("active-bg-panel");
        });

        for (let i = 1; i <= 5; i++) {
            $(`.bg-${i}`).on("click", function () {
                $("#add_bg").remove();
                $("body").removeClass().addClass(`body-bg-${i}`);
                $("head").append(`<link rel="stylesheet" class="bg" href="assets/css/bg-${i}.css" id="add_bg">`);
            });
        }

        $(".bg-6").on("click", function () {
            $("#add_bg").remove();
            $("body").removeClass().addClass('body-bg-6');
        });

        /* Thumbnail Image Switcher */
        const bigImages = document.querySelectorAll(".slider-banner-image");
        const thumbs = document.querySelectorAll(".thumbnail-image");

        if (bigImages.length && thumbs.length) {
            bigImages[0].classList.add("active");
            thumbs[0].classList.add("active");

            thumbs.forEach((thumb, index) => {
                thumb.addEventListener("click", function () {
                    bigImages.forEach(img => img.classList.remove("active"));
                    thumbs.forEach(t => t.classList.remove("active"));

                    if (bigImages[index]) {
                        bigImages[index].classList.add("active");
                    }
                    thumb.classList.add("active");
                });
            });
        }

    });

})(jQuery);