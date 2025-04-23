# AgroBoost - Django Web Application

AgroBoost is a Django-based web application aimed at empowering SHGs (Self Help Groups) and FPGs (Farmer Producer Groups) by enabling them to manage their products, inventory, and orders efficiently. The application also includes a cart system for seamless buying between SHG and FPG users.

## 🔧 Features

### 🔹 User Types
- **SHG (Self Help Group)**
- **FPG (Farmer Producer Group)**
- *(Future: End Customer)*

### 🔹 SHG Dashboard
- Add/View/Edit/Delete products
- Inventory management with stock tracking
- View and manage received orders
- Place orders from FPG products

### 🔹 FPG Dashboard
- Add/View/Edit/Delete products
- Inventory and orders dashboard
- Manage order status with validations

### 🔹 Cart System
- Add products to cart
- Update quantity with dynamic total
- Remove items
- Proceed to Buy

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Django 3.x or 4.x
- SQLite (default) or PostgreSQL (optional)
- Git

### Setup Instructions

1. Clone the repository:


git clone https://github.com/raju12208160/agroboost.git
cd agroboost

2. Install dependencies:
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt 

3.Run migrations and create superuser:

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

4.Run the development server:
python manage.py runserver

Visit http://127.0.0.1:8000/accounts/login to get started.
