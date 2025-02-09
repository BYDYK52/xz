from django.contrib import admin
from .models import Product, WhoMade, Complexity,Cart


admin.site.register(Complexity)
admin.site.register(Product)
admin.site.register(WhoMade)