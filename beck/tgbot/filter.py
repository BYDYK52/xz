from django_filters import rest_framework as filters
from .models import Product

class CharFilterInFilter(filters.BooleanFilter, filters.CharFilter):
    pass


class ProductFilter(filters.FilterSet):
    title =  CharFilterInFilter(field_name='title__name', lookup_expr='in')
    price = filters.RangeFilter()
    category = CharFilterInFilter(field_name='category__name', lookup_expr='in')
    who_made = CharFilterInFilter(field_name='who_made__name', lookup_expr='in')

    class Meta:
        model = Product
        fields = ['title', 'price', 'category', 'who_made']