from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
from sqlalchemy import text

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
    # Relationship with images
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)  # stored as "/static/images/products/<file>"
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

# Simple SQLite migration helpers
def ensure_sqlite_column(table_name, column_name, column_def_sql):
    """Add a column to a SQLite table if it doesn't exist.

    Parameters:
    - table_name: target table
    - column_name: name to check for existence
    - column_def_sql: full column definition used in ALTER TABLE (e.g., "subcategory VARCHAR(50)")
    """
    # Only run for SQLite
    if db.engine.dialect.name != 'sqlite':
        return
    
    try:
        existing_columns = []
        # Quote table names for PRAGMA calls to handle reserved keywords
        quoted_table = f'"{table_name}"' if table_name in ['order', 'user'] else table_name
        result = db.session.execute(text(f"PRAGMA table_info({quoted_table})"))
        for row in result:
            # row: (cid, name, type, notnull, dflt_value, pk)
            existing_columns.append(row[1])
        
        if column_name not in existing_columns:
            # Quote table names to handle reserved keywords like 'order'
            quoted_table = f'"{table_name}"' if table_name in ['order', 'user'] else table_name
            db.session.execute(text(f"ALTER TABLE {quoted_table} ADD COLUMN {column_def_sql}"))
            db.session.commit()
            print(f"Added column {column_name} to table {table_name}")
        else:
            print(f"Column {column_name} already exists in table {table_name}")
            
    except Exception as e:
        print(f"Error adding column {column_name} to table {table_name}: {str(e)}")
        db.session.rollback()

def check_database_health():
    """Check if all required columns exist in the database tables"""
    required_columns = {
        'product': ['id', 'name', 'description', 'price', 'image_url', 'category', 'subcategory', 'stock', 'colors', 'sizes', 'created_at'],
        'order': ['id', 'order_number', 'user_id', 'total_amount', 'advance_paid', 'remaining_amount', 'status', 'shipping_address', 'phone', 'utr_number', 'payment_screenshot', 'created_at'],
        'order_item': ['id', 'order_id', 'product_id', 'quantity', 'price', 'selected_color', 'selected_size'],
        'user': ['id', 'username', 'email', 'password_hash', 'is_admin', 'created_at']
    }
    
    missing_columns = []
    
    for table_name, columns in required_columns.items():
        try:
            quoted_table = f'"{table_name}"' if table_name in ['order', 'user'] else table_name
            result = db.session.execute(text(f"PRAGMA table_info({quoted_table})"))
            existing_columns = [row[1] for row in result]
            
            for column in columns:
                if column not in existing_columns:
                    missing_columns.append(f"{table_name}.{column}")
                    
        except Exception as e:
            print(f"Error checking table {table_name}: {str(e)}")
    
    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        return False
    else:
        print("Database schema is healthy - all required columns exist")
        return True

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

            # Support redirecting directly to checkout when requested
            next_dest = request.args.get('next') or request.form.get('next')
            if next_dest == 'checkout':
                return redirect(url_for('checkout'))
            return redirect(url_for('cart'))
            
        except Exception as e:
            flash(f'Error adding product to cart: {str(e)}', 'error')
            return redirect(url_for('product_detail', product_id=product_id))
    
    # GET request - add 1 item directly for products without variants, else go to detail
    product = Product.query.get(product_id)
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('home'))

    if (product.colors and product.colors.strip()) or (product.sizes and product.sizes.strip()):
        flash('Please select color/size before adding to cart.', 'info')
        return redirect(url_for('product_detail', product_id=product_id))

    cart = session.get('cart', {})
    product_key = str(product_id)
    if product_key in cart:
        if isinstance(cart[product_key], dict):
            cart[product_key]['quantity'] += 1
        else:
            cart[product_key] += 1
    else:
        cart[product_key] = {
            'quantity': 1,
            'color': '',
            'size': ''
        }
    session['cart'] = cart
    session.modified = True

    next_dest = request.args.get('next')
    if next_dest == 'checkout':
        return redirect(url_for('checkout'))
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('cart'))

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
    
    # Calculate total advance collected
    total_advance = db.session.query(db.func.sum(Order.advance_paid)).scalar() or 0.0
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    
    # Get low stock products (less than 10)
    low_stock_products = Product.query.filter(Product.stock < 10).count()
    
    # Get recent products
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         recent_orders=recent_orders,
                         total_advance=total_advance,
                         total_revenue=total_revenue,
                         low_stock_products=low_stock_products,
                         recent_products=recent_products)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    # Build query
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    if category:
        query = query.filter(Product.category == category)
    
    products = query.order_by(Product.created_at.desc()).all()
    
    # Process colors and sizes for display
    for product in products:
        if product.colors:
            product.colors_list = [color.strip() for color in product.colors.split(',') if color.strip()]
        else:
            product.colors_list = []
        
        if product.sizes:
            product.sizes_list = [size.strip() for size in product.sizes.split(',') if size.strip()]
        else:
            product.sizes_list = []
    
    # Get unique categories for filter
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin/products.html', 
                         products=products, 
                         search=search, 
                         category=category,
                         categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        colors, sizes = parse_colors_sizes(request.form.get('colors', ''), request.form.get('sizes', ''))

        # Determine primary image URL: from text field or from first uploaded file
        primary_image_url = request.form.get('image_url', '').strip()

        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            category=request.form['category'],
            subcategory=request.form.get('subcategory', ''),
            stock=int(request.form['stock']),
            image_url=primary_image_url,
            colors=','.join(colors),
            sizes=','.join(sizes)
        )
        db.session.add(product)
        db.session.flush()

        # Handle multiple image uploads
        try:
            upload_files = request.files.getlist('images') if 'images' in request.files else []
        except Exception:
            upload_files = []

        saved_any = False
        for file in upload_files:
            if file and file.filename:
                # Save file
                filename = f"{uuid.uuid4().hex}_{file.filename}"
                products_dir = os.path.join(app.static_folder, 'images', 'products')
                os.makedirs(products_dir, exist_ok=True)
                file_path = os.path.join(products_dir, filename)
                file.save(file_path)

                rel_path = f"/static/images/products/{filename}"
                db.session.add(ProductImage(product_id=product.id, image_path=rel_path))
                if not primary_image_url:
                    primary_image_url = rel_path
                    product.image_url = primary_image_url
                saved_any = True

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
        product.image_url = request.form.get('image_url', '').strip()
        product.colors = ','.join(colors)
        product.sizes = ','.join(sizes)

        # Handle any newly uploaded images
        try:
            upload_files = request.files.getlist('images') if 'images' in request.files else []
        except Exception:
            upload_files = []

        for file in upload_files:
            if file and file.filename:
                filename = f"{uuid.uuid4().hex}_{file.filename}"
                products_dir = os.path.join(app.static_folder, 'images', 'products')
                os.makedirs(products_dir, exist_ok=True)
                file_path = os.path.join(products_dir, filename)
                file.save(file_path)
                rel_path = f"/static/images/products/{filename}"
                db.session.add(ProductImage(product_id=product.id, image_path=rel_path))
                if not product.image_url:
                    product.image_url = rel_path

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('admin_products'))
    
    product = Product.query.get_or_404(product_id)
    
    # Check if product is referenced in any orders
    order_items = OrderItem.query.filter_by(product_id=product_id).first()
    if order_items:
        flash('Cannot delete product: It is referenced in existing orders. Consider marking it as out of stock instead.', 'error')
        return redirect(url_for('admin_products'))
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/products/bulk-delete', methods=['POST'])
@login_required
def admin_bulk_delete_products():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('admin_products'))
    
    product_ids = request.form.getlist('product_ids')
    
    if not product_ids:
        flash('No products selected for deletion.', 'error')
        return redirect(url_for('admin_products'))
    
    deleted_count = 0
    error_count = 0
    
    for product_id in product_ids:
        try:
            product = Product.query.get(product_id)
            if product:
                # Check if product is referenced in any orders
                order_items = OrderItem.query.filter_by(product_id=product_id).first()
                if order_items:
                    error_count += 1
                    continue
                
                db.session.delete(product)
                deleted_count += 1
        except Exception as e:
            error_count += 1
    
    try:
        db.session.commit()
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} products.', 'success')
        if error_count > 0:
            flash(f'Could not delete {error_count} products (referenced in orders).', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during bulk deletion: {str(e)}', 'error')
    
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

@app.route('/admin/orders/<int:order_id>/delete', methods=['POST'])
@login_required
def admin_delete_order(order_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    order = Order.query.get_or_404(order_id)

    try:
        # Delete payment screenshot file if exists
        if order.payment_screenshot:
            screenshot_path = os.path.join(app.static_folder, 'images', 'payments', order.payment_screenshot)
            try:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            except Exception:
                pass

        # Delete order items first
        OrderItem.query.filter_by(order_id=order.id).delete()
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting order: {str(e)}', 'error')
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/cleanup', methods=['POST'])
@login_required
def admin_cleanup_orders():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    try:
        # Remove payment screenshots
        for order in Order.query.all():
            if order.payment_screenshot:
                screenshot_path = os.path.join(app.static_folder, 'images', 'payments', order.payment_screenshot)
                try:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                except Exception:
                    pass
        # Delete order items then orders
        OrderItem.query.delete()
        Order.query.delete()
        db.session.commit()
        flash('All orders deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cleaning up orders: {str(e)}', 'error')
    return redirect(url_for('admin_orders'))

@app.route('/admin/products/<int:product_id>/images/<int:image_id>/delete', methods=['POST'])
@login_required
def admin_delete_product_image(product_id, image_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    image = ProductImage.query.get_or_404(image_id)
    if image.product_id != product_id:
        flash('Invalid image.', 'error')
        return redirect(url_for('admin_edit_product', product_id=product_id))

    try:
        # Delete file
        file_path = os.path.join(app.root_path, image.image_path.lstrip('/'))
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        db.session.delete(image)
        db.session.commit()
        flash('Product image deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    return redirect(url_for('admin_edit_product', product_id=product_id))

@app.route('/admin/products/cleanup', methods=['POST'])
@login_required
def admin_cleanup_products():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    try:
        # Delete product images from disk
        for img in ProductImage.query.all():
            file_path = os.path.join(app.root_path, img.image_path.lstrip('/'))
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        ProductImage.query.delete()
        # Delete products
        Product.query.delete()
        db.session.commit()
        flash('All products deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cleaning up products: {str(e)}', 'error')
    return redirect(url_for('admin_products'))

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
        # Minimal migrations for SQLite when schema has evolved
        # product.subcategory
        ensure_sqlite_column('product', 'subcategory', 'subcategory VARCHAR(50)')
        # product.colors and product.sizes existed before, but ensure for older DBs
        ensure_sqlite_column('product', 'colors', 'colors TEXT')
        ensure_sqlite_column('product', 'sizes', 'sizes TEXT')
        # order.advance_paid, order.remaining_amount, order.utr_number, order.payment_screenshot
        ensure_sqlite_column('order', 'advance_paid', 'advance_paid FLOAT DEFAULT 0.0')
        ensure_sqlite_column('order', 'remaining_amount', 'remaining_amount FLOAT DEFAULT 0.0')
        ensure_sqlite_column('order', 'utr_number', 'utr_number VARCHAR(50)')
        ensure_sqlite_column('order', 'payment_screenshot', 'payment_screenshot VARCHAR(200)')
        
        # order_item.selected_color and order_item.selected_size
        ensure_sqlite_column('order_item', 'selected_color', 'selected_color VARCHAR(50)')
        ensure_sqlite_column('order_item', 'selected_size', 'selected_size VARCHAR(20)')
        # ProductImage table will be created by create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('rosstech'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
