from django.contrib import admin
from django.urls import path, include, re_path
#from rest_framework_simplejwt import TokenVerifyView, TokenRefreshView, TokenObtainPairView

from tgbot.views import *
from rest_framework import routers

from xz.tgbot.views import BasketViewSet, ProductUpdate, ProductAPIDestroy, ProductAPIList

router = routers.DefaultRouter()
router.register(r'carts', BasketViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/drf-auth/',include('rest_framework.urls')),
    path('api/v1/product/', ProductAPIList.as_view()),
    path('api/v1/product/<int:pk>', ProductUpdate.as_view()),
    path('api/v1/productdelete/<int:pk>', ProductAPIDestroy.as_view()),
    path('api/v1/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls)),
    path('api/v1/basket/', BasketViewSet.as_view({'get': 'list', 'post': 'create'})),
    #path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]