from django.contrib import admin
from .models import Product, WhoMade, Complexity,BasketProduct,About


admin.site.register(Complexity)
admin.site.register(Product)
admin.site.register(WhoMade)
admin.site.register(BasketProduct)
admin.site.register(About)