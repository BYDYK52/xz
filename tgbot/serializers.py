from rest_framework import serializers
from .models import Product, BasketProduct,  User

class ProductSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Product
        fields = ('__all__')

class BasketProductsSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)
    class Meta:
        model = BasketProduct
        fields = ('user','product')

class BasketSerializer(serializers.ModelSerializer):
    basket_product = BasketProductsSerializer(many=True)
    class Meta:
        model = BasketProduct
        fields = ('user', 'basket_product','quantity','product')

class UserSerializer(serializers.ModelSerializer):
    basket = BasketSerializer(many=True)
    class Meta:
        model = User
        fields = ('id', 'basket')


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate_product_id(self, value):
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist")
        return value

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        product = Product.objects.get(id=validated_data['product_id'])
        cart, created = Cart.objects.get_or_create(user=user)
        cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
        cart_product.quantity += validated_data['quantity']
        cart_product.save()
        return cart_product


