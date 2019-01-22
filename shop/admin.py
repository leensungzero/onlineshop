from django.contrib import admin

from .models import *

# 옵션 클래스 만들고 등록

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', ]
    prepopulated_fields = {'slug': ('name', )}

admin.site.register(Category, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'stock', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    prepopulated_fields = {'slug': ('name', )}
    list_editable = ['price', 'stock', 'available']

admin.site.register(Product, ProductAdmin)