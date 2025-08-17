# Flask E-Commerce Store

A complete e-commerce website built with Python Flask, featuring an admin dashboard, product management, order processing with advance payment system, and comprehensive order tracking.

## 🚀 Features

### Customer Features
- **Product Catalog**: Browse products with categories and images
- **Shopping Cart**: Add/remove items with session-based cart
- **User Authentication**: Register and login system
- **Advance Payment System**: ₹100 advance payment required for order confirmation
- **Order History**: View all your past orders with detailed information
- **Checkout Process**: Complete order placement with shipping details
- **Order Confirmation**: Detailed order summary with order number
- **Responsive Design**: Mobile-friendly interface

### Admin Features
- **Admin Dashboard**: Overview with statistics and recent orders
- **Product Management**: Add, edit, and delete products
- **Order Management**: View all orders and update status
- **Order Details**: Complete order information with customer details
- **Advance Payment Tracking**: Monitor advance payments and remaining amounts
- **User Information**: View customer details for each order
- **Role-based Access**: Secure admin-only routes

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5 + Font Awesome
- **Session Management**: Flask sessions
- **Password Security**: Werkzeug password hashing

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## 🚀 Quick Start

### 1. Clone or Download
Download all files to a folder on your computer.

### 2. Install Dependencies
```bash
pip install Flask==2.3.3 Flask-SQLAlchemy==3.0.5 Flask-Login==0.6.3 Werkzeug==2.3.7
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Website
Open your browser and go to: `http://localhost:5000`

## 👤 Default Admin Account

The application automatically creates an admin user:
- **Username**: `admin`
- **Password**: `admin123`

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── add_sample_products.py # Script to add sample products
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── home.html         # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── cart.html         # Shopping cart
│   ├── checkout.html     # Checkout page
│   ├── product_detail.html # Product detail page
│   ├── order_confirmation.html # Order confirmation
│   ├── my_orders.html    # User order history
│   └── admin/            # Admin templates
│       ├── dashboard.html # Admin dashboard
│       ├── products.html  # Product management
│       ├── add_product.html # Add product form
│       ├── edit_product.html # Edit product form
│       ├── orders.html   # Order list
│       └── order_detail.html # Order detail
└── ecommerce.db          # SQLite database (created automatically)
```

## 🎯 How to Use

### For Customers

1. **Browse Products**: Visit the home page to see all available products
2. **Register/Login**: Create an account or login to your existing account
3. **Add to Cart**: Click "Add to Cart" on any product
4. **View Cart**: Click the cart icon in the navigation
5. **Checkout**: Click "Proceed to Checkout" and fill in shipping details
6. **Advance Payment**: Pay ₹100 advance to confirm your order
7. **Order Confirmation**: View your order details and order number
8. **Order History**: Click "My Orders" to view all your past orders

### For Admins

1. **Login**: Use the admin credentials (admin/admin123)
2. **Dashboard**: View statistics and recent orders
3. **Add Products**: Go to Products → Add New Product
4. **Manage Products**: Edit or delete existing products
5. **View Orders**: See all customer orders with advance payment details
6. **Update Status**: Change order status (pending → processing → shipped → delivered)
7. **Customer Information**: View complete customer details for each order

## 💰 Payment System

### Advance Payment Structure
- **Advance Payment**: ₹100 (fixed amount for all orders)
- **Remaining Amount**: Total order value minus ₹100
- **Payment Method**: Cash on Delivery (COD)
- **Collection**: Advance paid online, remaining amount collected on delivery

### Payment Flow
1. Customer places order
2. ₹100 advance payment is automatically applied
3. Order is confirmed and processed
4. Remaining amount is collected when order is delivered

## 🛒 Product Management

### Adding Products
1. Login as admin
2. Go to "Manage Products"
3. Click "Add New Product"
4. Fill in:
   - Product name
   - Description
   - Price (in ₹)
   - Category
   - Stock quantity
   - Image URL (optional)

### Categories Available
- Electronics
- Clothing
- Books
- Home & Garden
- Sports
- Beauty
- Toys
- Other

## 📦 Order Management

### Order Status Flow
1. **Pending**: Order placed, waiting for processing
2. **Processing**: Order is being prepared
3. **Shipped**: Order has been shipped
4. **Delivered**: Order delivered to customer
5. **Cancelled**: Order cancelled

### Order Information
- Order number (auto-generated)
- Customer details (username, email)
- Shipping address
- Phone number
- Order items with quantities
- Total amount
- Advance paid amount
- Remaining amount to collect
- Order date and status

## 🔧 Customization

### Adding New Categories
Edit the `add_product.html` and `edit_product.html` templates to add new category options.

### Changing Styling
Modify the CSS in `base.html` or add custom stylesheets.

### Database Changes
The application uses SQLite by default. To use another database:
1. Update the `SQLALCHEMY_DATABASE_URI` in `app.py`
2. Install the appropriate database driver

## 🚨 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Admin-only route protection
- Input validation
- SQL injection protection (SQLAlchemy)
- Secure order confirmation

## 📱 Responsive Design

The website is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py` or kill the existing process
2. **Database errors**: Delete `ecommerce.db` and restart the application
3. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
4. **Order relationship errors**: Ensure the database is recreated after model changes

### Error Messages
- Check the console for Python error messages
- Ensure all required files are in the correct locations
- Verify Python version is 3.7 or higher

## 🔄 Recent Updates

### Version 2.0 Features
- ✅ **Advance Payment System**: ₹100 advance payment required
- ✅ **Order History**: Users can view their complete order history
- ✅ **Fixed Relationships**: Proper user-order relationships in admin panel
- ✅ **Enhanced Admin Dashboard**: Shows advance payment statistics
- ✅ **Improved Order Details**: Complete payment breakdown
- ✅ **Currency Update**: All prices now shown in ₹ (Indian Rupees)
- ✅ **Better User Experience**: Clear payment information throughout

## 🔄 Future Enhancements

Potential improvements:
- Email notifications for orders
- Payment gateway integration
- Product reviews and ratings
- Inventory management
- User profiles
- Product search and filtering
- Image upload functionality
- Multiple payment methods
- Order tracking system
- Customer support chat

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📞 Support

If you need help:
1. Check the troubleshooting section
2. Review the code comments
3. Ensure all dependencies are installed
4. Verify your Python version

---

**Happy Shopping! 🛍️**
