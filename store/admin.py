from django.contrib import admin
from .models import Product,Category,Order,Review,Wishlist

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(Wishlist)
# Register your models here.
