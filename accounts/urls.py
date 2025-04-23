from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

        # Separate dashboards for each user type
    path('shg/dashboard/', views.shg_dashboard_view, name='shg_dashboard'),
    path('fpg/dashboard/', views.fpg_dashboard, name='fpg_dashboard'),
    path('enduser/dashboard/', views.enduser_dashboard_view, name='enduser_dashboard'),

    #shg urls
    path('shg/products/', views.shg_products_view, name='shg_products'),
    path('shg/products/add/', views.shg_add_product, name='shg_add_product'),
    path('shg/products/edit/<int:pk>/', views.shg_edit_product, name='shg_edit_product'),
    path('shg/products/delete/<int:pk>/', views.shg_delete_product, name='shg_delete_product'),

    path('inventory/', views.shg_inventory, name='shg_inventory'),
    path('orders/', views.shg_orders_received, name='shg_orders_received'),
    path('orders/update/<int:order_id>/', views.shg_order_status_update, name='shg_order_status_update'),


    #fpg urls
    path('fpg/products/', views.fpg_products_view, name='fpg_products'),
    path('fpg/add-product/', views.fpg_add_product, name='fpg_add_product'),
    path('fpg/products/edit/<int:pk>/', views.fpg_edit_product, name='fpg_edit_product'),
    path('fpg/products/delete/<int:pk>/', views.fpg_delete_product, name='fpg_delete_product'),

    
    path('fpg/inventory/', views.fpg_inventory, name='fpg_inventory'),
    path('fpg/orders/', views.fpg_orders_received, name='fpg_orders_received'),
    path('fpg/orders/status/<int:order_id>/', views.fpg_order_status_update, name='fpg_order_status_update'),

    path('shg/buy-fpg-products/', views.fpg_product_listing_for_shg, name='fpg_product_listing'), # Path for FPG products to buy
    path('shg/products/buy/<int:product_id>/', views.send_buy_request, name='buy_request'),  # Path to send buy request
    path('shg/cart/', views.shg_cart_page, name='shg_cart_page'),
    path('shg/cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/proceed/', views.proceed_to_buy, name='proceed_to_buy'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
]

