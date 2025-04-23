
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('SHG', 'Self Help Group'),
        ('FPG', 'Farmer Producer Group'),
        ('END', 'Customer'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    user_type = models.CharField(max_length=3, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    objects = UserManager()

    def __str__(self):
        return self.email



# accounts/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# models.py
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # stock = models.PositiveIntegerField(default=0)  # This ensures there is a stock attribute.

    image = models.ImageField(upload_to='product_images/', default='default.jpg')
    quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    shg = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shg_products', null=True, blank=True)
    fpg = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fpg_products', null=True, blank=True)

    def __str__(self):
        return self.name



class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_placed')
    fpg = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fpg_orders')
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.product.name} x {self.quantity}"
    
class BuyRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    shg = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'SHG'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='buy_requests')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BuyRequest by {self.shg.email} for {self.product.name} (x{self.quantity})"


from django.conf import settings

class CartItem(models.Model):
    USER_TYPE_CHOICES = (
        ('SHG', 'Self Help Group'),
        ('END', 'Customer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    product = models.ForeignKey('accounts.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.product.name} x {self.quantity}"
