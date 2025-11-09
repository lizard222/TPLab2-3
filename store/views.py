from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Product, Faction, Cart, CartItem


def product_list(request):
    faction_id = request.GET.get('faction')
    product_type = request.GET.get('type')
    
    products = Product.objects.all()
    factions = Faction.objects.all()
    
    selected_faction = None
    
    # Применяем оба фильтра последовательно
    if faction_id:
        products = products.filter(faction_id=faction_id)
        selected_faction = get_object_or_404(Faction, id=faction_id)
    
    if product_type:
        products = products.filter(product_type=product_type)
    
    # Определяем какой шаблон использовать
    if selected_faction:
        # Показываем страницу с товарами выбранной фракции
        return render(request, 'store/faction_products.html', {
            'products': products,
            'factions': factions,
            'selected_faction': selected_faction,
            'current_product_type': product_type, 
        })
    elif faction_id is None and product_type is None:
        # Если нет фильтров - показываем список всех фракций
        return render(request, 'store/faction_list.html', {
            'factions': factions,
        })
    else:
        # Если есть только тип товара или другие фильтры - показываем общий список товаров
        return render(request, 'store/product_list.html', {
            'products': products,
            'factions': factions,
            'current_product_type': product_type,
        })

# def product_detail(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     related_products = Product.objects.filter(
#         faction=product.faction
#     ).exclude(id=product.id)[:4]
    
#     return render(request, 'store/product_detail.html', {
#         'product': product,
#         'related_products': related_products
#     })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Добавление нескольких одинаковых
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

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')

@login_required
def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        new_quantity = int(request.POST.get('quantity', 1))
        
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item.delete()
            
    return redirect('cart_detail')