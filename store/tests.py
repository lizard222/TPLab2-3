from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from .models import Faction, Product, Cart, CartItem
from decimal import Decimal
from . import views

class ModelTests(TestCase):
    
    def setUp(self):
        """Создаем тестовые данные"""
        self.user = User.objects.create_user(
            username='testuser',
            password='123testpass123'
        )
        self.faction = Faction.objects.create(
            name='Space Marines',
            description='Элитные солдаты Империума'
        )
        self.product = Product.objects.create(
            name='Space Marine Tactical Squad',
            faction=self.faction,
            product_type='MINIATURE',
            description='Набор тактических десантников',
            price=Decimal('1500.00'),
            stock=10
        )
    
    def test_faction_creation(self):
        """Тест создания фракции"""
        self.assertEqual(self.faction.name, 'Space Marines')
        self.assertEqual(self.faction.description, 'Элитные солдаты Империума')
        self.assertEqual(str(self.faction), 'Space Marines')
    
    def test_product_creation(self):
        """Тест создания товара"""
        self.assertEqual(self.product.name, 'Space Marine Tactical Squad')
        self.assertEqual(self.product.faction, self.faction)
        self.assertEqual(self.product.product_type, 'MINIATURE')
        self.assertEqual(self.product.price, Decimal('1500.00'))
        self.assertEqual(self.product.stock, 10)
    
    def test_product_discounted_price(self):
        """Тест расчета цены со скидкой"""
        # Тест для обычного товара
        self.assertEqual(self.product.get_discounted_price(), Decimal('1500.00'))
        
        # Тест для стартового набора со скидкой 10%
        starter_set = Product.objects.create(
            name='Starter Set',
            faction=self.faction,
            product_type='STARTER_SET',
            description='Стартовый набор',
            price=Decimal('5000.00'),
            stock=5
        )
        self.assertEqual(starter_set.get_discounted_price(), Decimal('4500.00'))
    
    def test_cart_creation(self):
        """Тест создания корзины"""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(str(cart), f"Cart of {self.user.username}")
    
    def test_cart_item_creation(self):
        """Тест создания элемента корзины"""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        self.assertEqual(cart_item.cart, cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.total_price(), Decimal('3000.00'))
        self.assertEqual(str(cart_item), f"2 x {self.product.name}")
    

class ViewTests(TestCase):
    
    def setUp(self):
        """Создаем тестовые данные"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123testpass123'
        )
        self.faction = Faction.objects.create(
            name='Space Marines',
            description='Элитные солдаты Империума'
        )
        self.product1 = Product.objects.create(
            name='Space Marine Tactical Squad',
            faction=self.faction,
            product_type='MINIATURE',
            description='Набор тактических десантников',
            price=Decimal('1500.00'),
            stock=10
        )
        self.product2 = Product.objects.create(
            name='Starter Set',
            faction=self.faction,
            product_type='STARTER_SET',
            description='Стартовый набор',
            price=Decimal('5000.00'),
            stock=5
        )
    
    def test_product_list_view(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/faction_list.html')
        self.assertContains(response, 'Армии Warhammer')
    
    def test_product_list_with_faction_filter(self):
        """Тест фильтрации по фракции"""
        response = self.client.get(f'{reverse("product_list")}?faction={self.faction.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/faction_products.html')
        self.assertContains(response, 'Space Marines')
    
    def test_product_list_with_type_filter(self):
        """Тест фильтрации по типу товара"""
        response = self.client.get(f'{reverse("product_list")}?type=MINIATURE')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/product_list.html')
    
    def test_add_to_cart_authenticated(self):
        """Тест добавления в корзину для авторизованного пользователя"""
        self.client.login(username='testuser', password='123testpass123')
        
        response = self.client.post(reverse('add_to_cart', args=[self.product1.id]))
        self.assertEqual(response.status_code, 302)  # redirect
        self.assertRedirects(response, reverse('cart_detail'))
        
        # Проверяем, что товар добавился в корзину
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(cart_item.quantity, 1)
    
    def test_add_to_cart_unauthenticated(self):
        """Тест добавления в корзину для неавторизованного пользователя"""
        response = self.client.post(reverse('add_to_cart', args=[self.product1.id]))
        self.assertEqual(response.status_code, 302)  # redirect to login
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_cart_detail_authenticated(self):
        """Тест страницы корзины для авторизованного пользователя"""
        self.client.login(username='testuser', password='123testpass123')
        
        # Создаем корзину с товаром
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/cart.html')
        self.assertContains(response, 'Space Marine Tactical Squad')
        self.assertContains(response, '3000.00')  # 1500 * 2
    
    def test_remove_from_cart(self):
        """Тест удаления из корзины"""
        self.client.login(username='testuser', password='123testpass123')
        
        # Создаем корзину с товаром
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        
        response = self.client.post(reverse('remove_from_cart', args=[cart_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart_detail'))
        
        # Проверяем, что товар удалился
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
    
    def test_update_cart_quantity(self):
        """Тест обновления количества товара в корзине"""
        self.client.login(username='testuser', password='123testpass123')
        
        # Создаем корзину с товаром
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        
        response = self.client.post(
            reverse('update_cart_quantity', args=[cart_item.id]),
            {'quantity': '3'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart_detail'))
        
        # Проверяем, что количество обновилось
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)



class URLTests(TestCase):
    
    def test_product_list_url(self):
        """Тест URL главной страницы"""
        url = reverse('product_list')
        self.assertEqual(resolve(url).func, views.product_list)
    
    def test_add_to_cart_url(self):
        """Тест URL добавления в корзину"""
        url = reverse('add_to_cart', args=[1])
        self.assertEqual(resolve(url).func, views.add_to_cart)
    
    def test_remove_from_cart_url(self):
        """Тест URL удаления из корзины"""
        url = reverse('remove_from_cart', args=[1])
        self.assertEqual(resolve(url).func, views.remove_from_cart)
    
    def test_cart_detail_url(self):
        """Тест URL корзины"""
        url = reverse('cart_detail')
        self.assertEqual(resolve(url).func, views.cart_detail)