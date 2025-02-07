from django.contrib import admin
from django.urls import path

from tgbot.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/productlist/', ProductAPIList.as_view()),
    path('api/v1/productdetail/<int:pk>', ProductUpdate.as_view())
    path('api/v1/product/<int:pk>', ProductUpdate.as_view())
]
