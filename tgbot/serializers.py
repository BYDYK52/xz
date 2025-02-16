from rest_framework import serializers

from .models import Product,Cart


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Product
        fields = ('__all__')

class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ("__all__")


class BasketProductsSerializer(serializers.HyperlinkedModelSerializer):
    products = ProductsSerializer(many=True)
    class Meta:
        model = BasketProducts
        fields = ('basket','products')

class BasketSerializer(serializers.HyperlinkedModelSerializer):
    basket_products = BsketProductsSerializer(many=True)
    class Meta:
        model = Basket
        fields = ('user' , 'basket_products ')

class UserSerializer(serializers.HyperlinkedModelSerializer):
    basket = BasketSerializer(many=True)
    class Meta:
        model = User
        fields = ('id', 'basket')