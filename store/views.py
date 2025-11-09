from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Product, Faction, Cart, CartItem

# def product_list(request):
#     faction_id = request.GET.get('faction')
#     product_type = request.GET.get('type')
    
#     products = Product.objects.all()
    
#     if faction_id:
#         products = products.filter(faction_id=faction_id)
#     if product_type:
#         products = products.filter(product_type=product_type)
    
#     factions = Faction.objects.all()
#     return render(request, 'store/product_list.html', {
#         'products': products,
#         'factions': factions
#     })
def product_list(request):
    faction_id = request.GET.get('faction')
    product_type = request.GET.get('type')
    
    products = Product.objects.all()
    factions = Faction.objects.all()
    
    # Если выбрана конкретная фракция - показываем ее товары
    selected_faction = None
    if faction_id:
        products = products.filter(faction_id=faction_id)
        selected_faction = get_object_or_404(Faction, id=faction_id)
        # Показываем страницу с товарами выбранной фракции
        return render(request, 'store/faction_products.html', {
            'products': products,
            'factions': factions,
            'selected_faction': selected_faction,
        })
    
    if product_type:
        products = products.filter(product_type=product_type)
        return render(request, 'store/product_list.html', {
            'products': products,
            'factions': factions,
        })
    
    # Если фракция не выбрана - показываем список всех фракций
    return render(request, 'store/faction_list.html', {
        'factions': factions,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(
        faction=product.faction
    ).exclude(id=product.id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Для миниатюр можно добавлять несколько одинаковых
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.cartitem_set.all()
    total_quantity = sum(item.quantity for item in cart_items)
    total_price = Decimal('0')
    for item in cart_items:
        total_price += item.total_price()
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'total_price': total_price
    })