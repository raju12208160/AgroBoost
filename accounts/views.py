from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import logout

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            logout(request)  # Log out before re-logging in
            login(request, user)  # Log in the new user
            
            # Explicitly check user type and redirect
            if user.user_type == 'SHG':
                return redirect('shg_dashboard')
            elif user.user_type == 'FPG':
                return redirect('fpg_dashboard')
            elif user.user_type == 'END':
                return redirect('enduser_dashboard')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



@login_required
def dashboard_view(request):
    if request.user.user_type == 'SHG':
        return redirect('shg_dashboard')
    elif request.user.user_type == 'FPG':
        return redirect('fpg_dashboard')
    elif request.user.user_type == 'END':
        return redirect('enduser_dashboard')
    return redirect('dashboard')


@login_required
def shg_dashboard_view(request):
    user = request.user
    if user.user_type == 'SHG':
        products = Product.objects.filter(shg=user)
        orders = Order.objects.filter(product__shg=user).order_by('-order_date')[:5]
        low_stock = products.filter(quantity__lte=5)
        pending_orders = Order.objects.filter(product__shg=user, status='pending')
        pending_products = pending_orders.count()
        earnings = sum(order.product.price * order.quantity for order in orders)
        total_sold = sum(order.quantity for order in orders)
        context = {
            'products': products,
            'orders': orders,
            'low_stock_count': low_stock.count(),
            'total_products': products.count(),
            'pending_products': pending_products,
            'earnings': earnings,
            'total_sold': total_sold,
        }
        return render(request, 'accounts/shg_dashboard.html', context)
    return redirect('fpg_dashboard')  # Redirect to FPG dashboard if not SHG





@login_required
def enduser_dashboard_view(request):
    return render(request, 'accounts/enduser_dashboard.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

from .forms import ProductForm
from django.http import HttpResponseForbidden
from .models import Product

@login_required
def shg_add_product(request):
    if request.user.user_type != 'SHG':
        return HttpResponseForbidden("Only SHG users can add products.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shg = request.user  # ✅ Fixed: Assign current user directly
            product.save()

            # Add success message using messages framework
            messages.success(request, "Product added successfully.")

            return redirect('shg_products')  # redirect to 'your products' page
    else:
        form = ProductForm()

    return render(request, 'accounts/shg/add_products.html', {
        'form': form,
        'is_edit': False  # ✅ for template dynamic control
    })


from .models import Product  # if Product model is here; adjust import if it's elsewhere

def shg_products_view(request):
    products = Product.objects.filter(shg=request.user)
    return render(request, 'accounts/shg/shg_products.html', {'products': products})

@login_required
def shg_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, shg=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('shg_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'accounts/shg/add_products.html', {
        'form': form,
        'product': product,
        'is_edit': True  # ✅ edit mode flag
    })



@login_required
def shg_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, shg=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('shg_products')
    
    return render(request, 'accounts/shg/shg_confirm_delete.html', {'product': product})

from .models import Order
@login_required
def shg_inventory(request):
    products = Product.objects.filter(shg=request.user, is_available=True)  # Only available products
    return render(request, 'accounts/shg/shg_inventory.html', {'products': products})

@login_required
def shg_orders_received(request):
    user = request.user
    if user.user_type == 'SHG':
        orders = Order.objects.filter(product__shg=user).order_by('-order_date')
        return render(request, 'accounts/shg/shg_orders_received.html', {'orders': orders})
    # Redirect to another page, such as the dashboard, if user is not SHG
    return redirect('shg_dashboard')


@login_required
def shg_order_status_update(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Check if order belongs to the logged-in SHG
    if request.user != order.product.shg:
        messages.error(request, "You are not authorized to update this order.")
        return redirect('shg_orders_received')

    if request.method == "POST":
        new_status = request.POST.get('status')

        # Prevent changes if already in a final state
        if order.status in ['Delivered', 'Cancelled']:
            messages.warning(request, f"Order already {order.status}. Status can't be changed.")
            return redirect('shg_orders_received')

        # Handle Pending → Shipped
        if order.status == 'Pending' and new_status == 'Shipped':
            if order.product.quantity >= order.quantity:
                order.product.quantity -= order.quantity  # Deduct the quantity from stock
                if order.product.quantity == 0:
                    order.product.is_available = False  # Mark the product as unavailable if stock is zero
                order.product.save()
                order.status = new_status
                order.save()
                messages.success(request, "Order shipped and stock updated.")
            else:
                messages.error(request, "Not enough stock to ship this order.")
                return redirect('shg_orders_received')

        # Handle Shipped → Delivered
        elif order.status == 'Shipped' and new_status == 'Delivered':
            order.status = new_status
            order.save()
            messages.success(request, "Order marked as delivered.")

        # Handle Pending → Cancelled or any valid transition without stock change
        elif new_status in ['Cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")

        # Handle invalid status transition
        else:
            messages.warning(request, "Invalid status transition. Please select a valid status.")

        return redirect('shg_orders_received')

    return render(request, 'accounts/shg/shg_order_status_update.html', {'order': order})

#FPG


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Product, Order
from django.db.models import Sum, F, ExpressionWrapper, DecimalField


@login_required
def fpg_dashboard(request):
    user = request.user

    if user.user_type == 'FPG':
        # Fetch products and orders linked to FPG
        products = Product.objects.filter(fpg=user)
        orders = Order.objects.filter(fpg=request.user)

        total_products = products.count()
        total_orders = orders.count()
        fulfilled_orders = orders.filter(status='Delivered').count()
        pending_orders = orders.filter(fpg=request.user, status="Pending")


        # Calculate total revenue for delivered orders
        revenue_expr = ExpressionWrapper(
            F('product__price') * F('quantity'),
            output_field=DecimalField()
        )
        total_revenue = orders.filter(status='Delivered').aggregate(
            total=Sum(revenue_expr)
        )['total'] or 0

        low_stock = products.filter(quantity__lt=5).count()
        recent_orders = orders.order_by('-order_date')[:5]

        return render(request, 'accounts/fpg_dashboard.html', {
            'products': products,
            'orders': recent_orders,
            'total_products': total_products,
            'total_orders': total_orders,
            'fulfilled_orders': fulfilled_orders,
            'total_revenue': total_revenue,
            'pending': pending_orders.count(),
            'low_stock': low_stock,
        })

    return redirect('fpg_dashboard')






# views.py
@login_required
def fpg_add_product(request):
    
    if request.user.user_type != 'FPG':
        return HttpResponseForbidden("Only FPG users can add products.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.fpg = request.user  # ✅ Assign FPG owner
            product.save()

            messages.success(request, "FPG Product added successfully.")
            return redirect('fpg_products')
    else:
        form = ProductForm()

    return render(request, 'accounts/fpg/add_products.html', {
        'form': form,
        'is_edit': False
    })

@login_required
def fpg_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, fpg=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('fpg_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'accounts/fpg/add_products.html', {
        'form': form,
        'product': product,
        'is_edit': True  # edit mode flag
    })

@login_required
def fpg_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, fpg=request.user)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('fpg_products')

    return render(request, 'accounts/fpg/fpg_confirm_delete.html', {'product': product})



@login_required
def fpg_products_view(request):
    products = Product.objects.filter(fpg=request.user)  # Ensure the correct relation with the user
    return render(request, 'accounts/fpg/fpg_products.html', {'products': products})

from .models import Product

def fpg_inventory(request):
    # Fetch products for the FPG user
    products = Product.objects.filter(fpg=request.user)  # or your relevant filter logic

    return render(request, 'accounts/fpg/fpg_inventory.html', {'products': products})


@login_required
def fpg_orders_received(request):
    user = request.user
    if user.user_type == 'FPG':
        orders = Order.objects.filter(fpg=request.user).order_by('-order_date')  # Assuming the order has a date field 'ordered_at'
        return render(request, 'accounts/fpg/fpg_orders_received.html', {'orders': orders})
    # Redirect to another page, such as the dashboard, if user is not FPG
    return redirect('fpg_dashboard')

@login_required
def fpg_order_status_update(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Check if order belongs to the logged-in FPG
    if request.user != order.fpg:
        messages.error(request, "You are not authorized to update this order.")
        return redirect('fpg_orders_received')

    if request.method == "POST":
        new_status = request.POST.get('status')

        # Prevent changes if already in a final state
        if order.status in ['Delivered', 'Cancelled']:
            messages.warning(request, f"Order already {order.status}. Status can't be changed.")
            return redirect('fpg_orders_received')

        # Handle Pending → Shipped
        if order.status == 'Pending' and new_status == 'Shipped':
            if order.product.quantity >= order.quantity:
                order.product.quantity -= order.quantity  # Deduct the quantity from stock
                if order.product.quantity == 0:
                    order.product.is_available = False  # Mark the product as unavailable if stock is zero
                order.product.save()
                order.status = new_status
                order.save()
                messages.success(request, "Order shipped and stock updated.")
            else:
                messages.error(request, "Not enough stock to ship this order.")
                return redirect('fpg_orders_received')

        # Handle Shipped → Delivered
        elif order.status == 'Shipped' and new_status == 'Delivered':
            order.status = new_status
            order.save()
            messages.success(request, "Order marked as delivered.")

        # Handle Pending → Cancelled or any valid transition without stock change
        elif new_status in ['Cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")

        # Handle invalid status transition
        else:
            messages.warning(request, "Invalid status transition. Please select a valid status.")

        return redirect('fpg_orders_received')

    return render(request, 'accounts/fpg/fpg_order_status_update.html', {'order': order})




@login_required
def shg_buy_products(request):
    user = request.user
    if user.user_type == 'SHG':
        # Fetch all FPG products (products owned by FPG users)
        fpg_products = Product.objects.filter(fpg__isnull=False)  # Fetch products owned by FPG users

        return render(request, 'accounts/shg/fpg_product_listing.html', {
            'fpg_products': fpg_products
        })
    return redirect('shg_dashboard')  # Redirect if the user is not SHG

@login_required
def fpg_product_listing_for_shg(request):
    user = request.user

    if user.user_type == 'SHG':
        fpg_products = Product.objects.filter(fpg__isnull=False)  # Get FPG products available for SHG
        return render(request, 'accounts/shg/fpg_product_listing.html', {'fpg_products': fpg_products})
    
    return redirect('shg_dashboard')  


from .models import Product, BuyRequest

@login_required
def send_buy_request(request, product_id):
    user = request.user

    # Only SHG users can place buy requests
    if user.user_type != 'SHG':
        messages.error(request, "Only SHG users can place buy requests.")
        return redirect('shg_dashboard')

    product = get_object_or_404(Product, id=product_id)

    # Optional: Prevent SHG users from buying their own products
    if product.fpg == user:
        messages.error(request, "You cannot place an order for your own product.")
        return redirect('fpg_product_listing')

    # Validate quantity (it shouldn't go negative or zero)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0 or quantity > product.quantity:
        messages.error(request, f"Invalid quantity. Available stock: {product.quantity}.")
        return redirect('fpg_product_listing')

    # Ensure stock is updated after order is placed
    product.quantity -= quantity  # Decrease the stock of the product
    product.save()

    # Create the order and BuyRequest
    order = Order.objects.create(
        product=product,
        buyer=request.user,
        fpg=product.fpg,  # Ensure FPG is associated
        quantity=quantity,
        status='Pending'
    )

    BuyRequest.objects.create(
        shg=user,
        product=product,
        quantity=quantity,
        status='Pending'
    )

    messages.success(request, f"Buy request for '{product.name}' (x{quantity}) sent successfully.")
    return redirect('fpg_product_listing')

from .models import Product, CartItem

def add_to_cart(request, product_id):
    if request.user.is_authenticated and request.user.user_type == 'SHG':
        product = get_object_or_404(Product, id=product_id)

        # Check if already in cart
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            user_type='SHG',
            product=product
        )
        if not created:
            item.quantity += 1
            item.save()

        return redirect('shg_cart_page')  # Create this page in next step
    else:
        return redirect('login')


from .models import CartItem

def shg_cart_page(request):
    if request.user.is_authenticated and request.user.user_type == 'SHG':
        cart_items = CartItem.objects.filter(user=request.user, user_type='SHG')

        # Calculate total price and add item totals
        total = 0
        for item in cart_items:
            item.total_price = item.product.price * item.quantity
            total += item.total_price

        if request.method == 'POST':
            for item in cart_items:
                quantity = request.POST.get(f'quantity_{item.id}')
                if quantity and quantity.isdigit():
                    item.quantity = int(quantity)
                    item.save()
                    # Recalculate total price
                    item.total_price = item.product.price * item.quantity
                    item.save()
            return redirect('shg_cart_page')  # Redirect to the same page to refresh cart after update

        return render(request, 'accounts/shg/shg_cart.html', {'cart_items': cart_items, 'total': total})

    return redirect('login')

@login_required
def proceed_to_buy(request):
    user = request.user

    if user.user_type != 'SHG':
        messages.error(request, "Only SHG users can proceed with the purchase.")
        return redirect('shg_dashboard')

    cart_items = CartItem.objects.filter(user=user, user_type='SHG')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('shg_cart')

    errors = []
    success_count = 0

    for item in cart_items:
        product = item.product

        # Optional: Prevent SHG users from buying their own product
        if product.fpg == user:
            errors.append(f"Cannot buy your own product: '{product.name}'")
            continue

        # Get quantity from form
        quantity_str = request.POST.get(f'quantity_{item.id}')
        quantity = int(quantity_str) if quantity_str else item.quantity

        if quantity <= 0:
            errors.append(f"Invalid quantity for '{product.name}'")
            continue

        if quantity > product.quantity:
            errors.append(f"Not enough stock for '{product.name}'. Available: {product.quantity}")
            continue

        # Deduct stock
        product.quantity -= quantity
        product.save()

        # Create order
        Order.objects.create(
            product=product,
            buyer=user,
            fpg=product.fpg,
            quantity=quantity,
            status='Pending'
        )

        # Create buy request
        BuyRequest.objects.create(
            shg=user,
            product=product,
            quantity=quantity,
            status='Pending'
        )

        # Remove from cart
        item.delete()
        success_count += 1

    # Show messages
    if success_count > 0:
        messages.success(request, f"{success_count} buy request(s) sent successfully.")

    for err in errors:
        messages.error(request, err)

    return redirect('shg_dashboard')




@login_required
def remove_from_cart(request, cart_item_id):
    user = request.user

    # Ensure the user is an SHG user
    if user.user_type != 'SHG':
        messages.error(request, "Only SHG users can remove items from their cart.")
        return redirect('shg_cart_page')

    # Fetch the cart item to delete
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=user)

    # Remove the cart item
    cart_item.delete()

    messages.success(request, f"Item '{cart_item.product.name}' removed from your cart.")
    return redirect('shg_cart_page')


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CartItem

def update_cart_item(request):
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        action = request.POST.get('action')

        # Get the cart item
        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        # Update the quantity based on the action
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1

        # Save the updated cart item
        cart_item.save()

        # Recalculate the total price
        total_price = cart_item.quantity * cart_item.product.price
        total_cart_price = sum(item.quantity * item.product.price for item in CartItem.objects.filter(user=cart_item.user))

        # Return the updated values as JSON
        return JsonResponse({
            'quantity': cart_item.quantity,
            'total_amount': total_price,
            'total_price': total_cart_price,
        })
