from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=True)  # New field for subcategory
    stock = db.Column(db.Integer, default=0)
    colors = db.Column(db.Text, nullable=True)  # JSON string of available colors
    sizes = db.Column(db.Text, nullable=True)   # JSON string of available sizes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    advance_paid = db.Column(db.Float, default=0.0)  # New field for advance payment
    remaining_amount = db.Column(db.Float, nullable=False)  # New field for remaining amount
    status = db.Column(db.String(20), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    utr_number = db.Column(db.String(50), nullable=True)  # UTR number for payment
    payment_screenshot = db.Column(db.String(200), nullable=True)  # Payment screenshot filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with order items
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    selected_color = db.Column(db.String(50), nullable=True)  # Selected color
    selected_size = db.Column(db.String(20), nullable=True)   # Selected size
    
    # Relationship with product
    product = db.relationship('Product', backref='order_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions for colors and sizes
def parse_colors_sizes(colors_str, sizes_str):
    """Parse colors and sizes from form input strings"""
    colors = []
    sizes = []
    
    if colors_str:
        colors = [color.strip() for color in colors_str.split(',') if color.strip()]
    
    if sizes_str:
        sizes = [size.strip() for size in sizes_str.split(',') if size.strip()]
    
    return colors, sizes

def format_colors_sizes(colors, sizes):
    """Format colors and sizes for display"""
    colors_str = ', '.join(colors) if colors else 'N/A'
    sizes_str = ', '.join(sizes) if sizes else 'N/A'
    return colors_str, sizes_str

# Routes
@app.route('/')
def home():
    products = Product.query.all()
    # Format colors and sizes for display
    for product in products:
        if product.colors:
            product.colors_list = [color.strip() for color in product.colors.split(',') if color.strip()]
        else:
            product.colors_list = []
        
        if product.sizes:
            product.sizes_list = [size.strip() for size in product.sizes.split(',') if size.strip()]
        else:
            product.sizes_list = []
    
    return render_template('home.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Format colors and sizes for display
    if product.colors:
        product.colors_list = [color.strip() for color in product.colors.split(',') if color.strip()]
    else:
        product.colors_list = []
    
    if product.sizes:
        product.sizes_list = [size.strip() for size in product.sizes.split(',') if size.strip()]
    else:
        product.sizes_list = []
    
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    products = []
    total = 0
    
    if not cart_items:
        flash('Your cart is empty!', 'info')
        return render_template('cart.html', products=products, total=total)
    
    for product_id, item_data in cart_items.items():
        product = Product.query.get(int(product_id))
        if product:
            # Handle both old format (just quantity) and new format (dict with quantity, color, size)
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 1)
                selected_color = item_data.get('color', '')
                selected_size = item_data.get('size', '')
            else:
                quantity = item_data
                selected_color = ''
                selected_size = ''
            
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'image_url': product.image_url,
                'selected_color': selected_color,
                'selected_size': selected_size
            })
            total += product.price * quantity
    
    return render_template('cart.html', products=products, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if request.method == 'POST':
        try:
            # Get color and size from form
            selected_color = request.form.get('color', '')
            selected_size = request.form.get('size', '')
            quantity = int(request.form.get('quantity', 1))
            
            # Validate product exists
            product = Product.query.get(product_id)
            if not product:
                flash('Product not found!', 'error')
                return redirect(url_for('home'))
            
            cart = session.get('cart', {})
            product_key = str(product_id)
            
            if product_key in cart:
                # If product already exists, update quantity
                if isinstance(cart[product_key], dict):
                    cart[product_key]['quantity'] += quantity
                else:
                    # Convert old format to new format
                    cart[product_key] = {
                        'quantity': cart[product_key] + quantity,
                        'color': selected_color,
                        'size': selected_size
                    }
            else:
                # Add new product with color and size
                cart[product_key] = {
                    'quantity': quantity,
                    'color': selected_color,
                    'size': selected_size
                }
            
            session['cart'] = cart
            session.modified = True  # Ensure session is saved
            flash(f'{product.name} added to cart!', 'success')
            return redirect(url_for('cart'))
            
        except Exception as e:
            flash(f'Error adding product to cart: {str(e)}', 'error')
            return redirect(url_for('product_detail', product_id=product_id))
    
    # GET request - show product detail page
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash('Product removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please login to checkout!', 'error')
            return redirect(url_for('login'))
        
        cart_items = session.get('cart', {})
        if not cart_items:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('cart'))
        
        # Calculate total
        total = 0
        for product_id, item_data in cart_items.items():
            product = Product.query.get(int(product_id))
            if product:
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', 1)
                else:
                    quantity = item_data
                total += product.price * quantity
        
        # Calculate advance and remaining amount
        advance_amount = float(request.form.get('advance_paid', 100.0))  # Get advance amount from form
        if advance_amount < 100.0:
            advance_amount = 100.0  # Minimum advance payment of 100rs
        remaining_amount = total - advance_amount
        
        # Handle file upload for payment screenshot
        payment_screenshot = None
        if 'payment_screenshot' in request.files:
            file = request.files['payment_screenshot']
            if file and file.filename:
                # Generate unique filename
                filename = f"payment_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
                file_path = os.path.join(app.static_folder, 'images', 'payments', filename)
                
                # Create payments directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save the file
                file.save(file_path)
                payment_screenshot = filename
        
        # Create order
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total,
            advance_paid=advance_amount,
            remaining_amount=remaining_amount,
            shipping_address=request.form['address'],
            phone=request.form['phone'],
            utr_number=request.form.get('utr_number', ''),
            payment_screenshot=payment_screenshot
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for product_id, item_data in cart_items.items():
            product = Product.query.get(int(product_id))
            if product:
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', 1)
                    selected_color = item_data.get('color', '')
                    selected_size = item_data.get('size', '')
                else:
                    quantity = item_data
                    selected_color = ''
                    selected_size = ''
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price,
                    selected_color=selected_color,
                    selected_size=selected_size
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        # Clear cart
        session['cart'] = {}
        session.modified = True
        
        flash(f'Order placed successfully! Order number: {order_number}. Advance payment of ₹{advance_amount:.2f} received. Remaining amount: ₹{remaining_amount:.2f}', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    cart_items = session.get('cart', {})
    products = []
    total = 0
    
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))
    
    for product_id, item_data in cart_items.items():
        product = Product.query.get(int(product_id))
        if product:
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 1)
                selected_color = item_data.get('color', '')
                selected_size = item_data.get('size', '')
            else:
                quantity = item_data
                selected_color = ''
                selected_size = ''
            
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'image_url': product.image_url,
                'selected_color': selected_color,
                'selected_size': selected_size
            })
            total += product.price * quantity
    
    return render_template('checkout.html', products=products, total=total)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('order_confirmation.html', order=order, order_items=order_items)

# New route for user order history
@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# Debug route to check cart contents
@app.route('/debug/cart')
def debug_cart():
    cart_items = session.get('cart', {})
    return jsonify({
        'cart_items': cart_items,
        'cart_type': type(cart_items),
        'session_keys': list(session.keys())
    })

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         recent_orders=recent_orders)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        colors, sizes = parse_colors_sizes(request.form.get('colors', ''), request.form.get('sizes', ''))
        
        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            category=request.form['category'],
            subcategory=request.form.get('subcategory', ''),
            stock=int(request.form['stock']),
            image_url=request.form['image_url'],
            colors=','.join(colors),
            sizes=','.join(sizes)
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        colors, sizes = parse_colors_sizes(request.form.get('colors', ''), request.form.get('sizes', ''))
        
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.category = request.form['category']
        product.subcategory = request.form.get('subcategory', '')
        product.stock = int(request.form['stock'])
        product.image_url = request.form['image_url']
        product.colors = ','.join(colors)
        product.sizes = ','.join(sizes)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('admin/order_detail.html', order=order, order_items=order_items)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    flash('Order status updated successfully!', 'success')
    return redirect(url_for('admin_order_detail', order_id=order.id))

# Initialize database and create admin user
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
