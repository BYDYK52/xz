import django_filters
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .models import Product, BasketProduct
from .serializers import ProductSerializer, BasketSerializer,BasketProductsSerializer,AddToCartSerializer
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from .filter import ProductFilter
from rest_framework import viewsets
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class ProductAPIList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter]
    search_fields = ['title', 'content', ]
    filterset_class = ProductFilter
class ProductUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class ProductAPIDestroy(generics.RetrieveDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAdminOrReadOnly)


# carts/views.py

class BasketViewSet(viewsets.ModelViewSet):
    queryset = BasketProduct.objects.all()
    serializer_class = BasketSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        product = Product.objects.get(id=serializer.validated_data['product'])
        cart, created = BasketProduct.objects.get_or_create(user=user)
        cart_product, created = BasketProduct.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_product.quantity += serializer.validated_data['quantity']
        else:
            cart_product.quantity = serializer.validated_data['quantity']
        cart_product.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Update the quantity of an existing cart item
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)



class AddToCartApi(APIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
