from django.shortcuts import render, get_object_or_404

from .models import *


def product_list(request, category_slug=None):
    category = None

    categories = Category.objects.all()
    # available -> 상품을 노출 할꺼냐 말꺼냐
    # is_order -> 상품을 주문할 수 있게할꺼냐 말꺼냐
    products = Product.objects.filter(available=True)

    if category_slug:
        print('if문')
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'shop/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
    })

from cart.forms import CartAddProductForm
def product_detail(request, id, product_slug=None):
    product = get_object_or_404(Product, id=id, slug=product_slug)
    # Todo : Cart Form 처리
    cart_form = CartAddProductForm()
    return render(request, 'shop/product/detail.html', {
        'product': product,
        'cart_form': cart_form
    })