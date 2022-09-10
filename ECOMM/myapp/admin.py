from django.contrib import admin

from myapp.models import Ad, Brand, Cart, CartTotal, Category, CheckoutCart, Contact, Product, Review, SiteReview, Slider, WishList

admin.site.register(Category)
admin.site.register(Slider)
admin.site.register(Ad)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Contact)
admin.site.register(SiteReview)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartTotal)
admin.site.register(CheckoutCart)
admin.site.register(WishList)
