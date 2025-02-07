from django.contrib import admin
from .models import Product, Whomade, Complexity


admin.site.register(Complexity)
admin.site.register(Product)
admin.site.register(Whomade)