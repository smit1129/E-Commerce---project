import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shopzone-secret-key-2024'

# Supabase PostgreSQL URL
DATABASE_URL = os.environ.get("DATABASE_URL")
def get_db():
    if 'db' not in g:
        conn = psycopg2.connect(DATABASE_URL)
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def query(sql, args=(), one=False):
    sql = sql.replace('?', '%s')
    cur = get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, args)
    rv = cur.fetchall()
    get_db().commit()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    sql = sql.replace('?', '%s')
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, args)
    db.commit()
    return cur.lastrowid

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' in session:
        return query('SELECT * FROM users WHERE id=?', [session['user_id']], one=True)
    return None

app.jinja_env.globals['current_user'] = current_user

def get_cart():
    return session.get('cart', {})

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

def cart_count():
    return sum(item['qty'] for item in get_cart().values())

def cart_total():
    return sum(item['price'] * item['qty'] for item in get_cart().values())

app.jinja_env.globals['cart_count'] = cart_count

def init_db():
    db = psycopg2.connect(DATABASE_URL)
    cur = db.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id       SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email    TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS products (
        id             SERIAL PRIMARY KEY,
        name           TEXT    NOT NULL,
        description    TEXT    NOT NULL,
        price          REAL    NOT NULL,
        original_price REAL,
        category       TEXT    NOT NULL,
        image_url      TEXT    NOT NULL,
        stock          INTEGER DEFAULT 100,
        rating         REAL    DEFAULT 4.0,
        review_count   INTEGER DEFAULT 0,
        badge          TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS admins (
        id       SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    db.commit()

    
    cur.execute('SELECT COUNT(*) FROM admins')
    if cur.fetchone()[0] == 0:
        hashed = generate_password_hash('smitt011', method='pbkdf2:sha256')
        cur.execute(
        'INSERT INTO admins (username, password) VALUES (%s, %s)',
        ['smit', hashed]
        )
    db.commit()
    print('✅ Default admin created!')

    cur.execute('''CREATE TABLE IF NOT EXISTS orders (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER,
        product_id  INTEGER,
        quantity    INTEGER,
        total_price REAL,
        order_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')


    db.commit()

    cur.execute('SELECT COUNT(*) FROM products')
    count = cur.fetchone()[0]

    if count == 0:
        try:
            from seed_db import PRODUCTS
            cur.executemany(
                '''INSERT INTO products
                   (name,description,price,original_price,category,
                    image_url,stock,rating,review_count,badge)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                PRODUCTS,
            )
            db.commit()
            print('✅ Products seeded!')
        except Exception as exc:
            print(f'⚠️ Could not seed: {exc}')
    db.close()
init_db()

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '').strip()
    if q and cat:
        products = query('SELECT * FROM products WHERE category=? AND (name LIKE ? OR description LIKE ?)',[cat,f'%{q}%',f'%{q}%'])
    elif q:
        products = query('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?',[f'%{q}%',f'%{q}%'])
    elif cat:
        products = query('SELECT * FROM products WHERE category=?',[cat])
    else:
        products = query('SELECT * FROM products')
    cats = [r['category'] for r in query('SELECT DISTINCT category FROM products')]
    return render_template('index.html', products=products, categories=cats, search_query=q, selected_category=cat)

@app.route('/product/<int:pid>')
def product_detail(pid):
    product = query('SELECT * FROM products WHERE id=?', [pid], one=True)
    if not product:
        flash('Product not found.','danger')
        return redirect(url_for('index'))
    related = query('SELECT * FROM products WHERE category=? AND id!=? LIMIT 4',[product['category'],pid])
    return render_template('product_detail.html', product=product, related=related)

@app.route('/add-to-cart/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    product = query('SELECT * FROM products WHERE id=?',[pid],one=True)
    if not product: return redirect(url_for('index'))
    qty = int(request.form.get('qty',1))
    cart = get_cart()
    key = str(pid)
    if key in cart: cart[key]['qty'] += qty
    else: cart[key] = {'name':product['name'],'price':product['price'],'image_url':product['image_url'],'qty':qty}
    save_cart(cart)
    flash(f'"{product["name"]}" added to cart!','success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def cart():
    cart_data = get_cart()
    items = [{'id':k,**v,'subtotal':v['price']*v['qty']} for k,v in cart_data.items()]
    return render_template('cart.html', products=items, total=cart_total())

@app.route('/update-cart/<pid>', methods=['POST'])
def update_cart(pid):
    cart = get_cart()
    qty = int(request.form.get('qty',1))
    if pid in cart:
        if qty<=0: del cart[pid]
        else: cart[pid]['qty'] = qty
    save_cart(cart)
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<pid>')
def remove_from_cart(pid):
    cart = get_cart()
    cart.pop(pid, None)
    save_cart(cart)
    flash('Item removed from cart.','info')
    return redirect(url_for('cart'))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("index"))

    conn = get_db()
    products = []
    total = 0

    for pid, item in cart.items():
        qty = item["qty"]
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM products WHERE id=%s", (pid,))
        p = cur.fetchone()

        if p:
            subtotal = float(p["price"]) * int(qty)
            total += subtotal
            products.append({
                "id":        p["id"],
                "name":      p["name"],
                "price":     float(p["price"]),
                "image_url": p["image_url"],
                "qty":       int(qty),
                "subtotal":  subtotal,
            })

    if request.method == "POST":
        user_id = session.get("user_id")
        cur = conn.cursor()
        for item in products:
            cur.execute(
                "INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                (user_id, item["id"], item["qty"], item["subtotal"])
            )
        conn.commit()
        session["cart"] = {}
        session.modified = True
        flash("Order placed successfully! 🎉", "success")
        return redirect(url_for("order_success"))

    return render_template("checkout.html", products=products, total=total)

@app.route('/order-success')
def order_success():
    return render_template('order_success.html')

@app.route("/my-orders")
@login_required
def my_orders():
    user_id = session.get("user_id")
    orders = query("""
        SELECT o.id, p.name, o.quantity, o.total_price, o.order_date
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id=?
        ORDER BY o.order_date DESC
    """, (user_id,))
    return render_template("orders.html", orders=orders)

@app.route('/register', methods=['GET','POST'])
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        if query('SELECT id FROM users WHERE email=?',[email],one=True):
            flash('Email already registered.','danger')
        elif query('SELECT id FROM users WHERE username=?',[username],one=True):
            flash('Username already taken.','danger')
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO users (username,email,password) VALUES (%s,%s,%s) RETURNING id',
                [username, email, generate_password_hash(password)]
            )
            uid = cur.fetchone()[0]
            db.commit()
            session['user_id'] = uid
            session['username'] = username
            session['email'] = email
            flash(f'Welcome, {username}! Account created.','success')
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = query('SELECT * FROM users WHERE email=?',[email],one=True)
        if user and check_password_hash(str(user['password']),password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash(f'Welcome back, {user["username"]}!','success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid email or password.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.','info')
    return redirect(url_for('index'))

@app.route('/deals')
def deals():
    products = query("""
        SELECT * FROM products
        WHERE original_price > price
        ORDER BY (original_price - price) DESC
    """)
    return render_template("deals.html", products=products)

# ══════════════════════════════════════════════════════
# ADMIN PANEL ROUTES
# ══════════════════════════════════════════════════════

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login as admin.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Admin Login ────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        admin = query('SELECT * FROM admins WHERE username=%s', [username], one=True)
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

# ── Admin Dashboard ────────────────────────────────────
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_products = query('SELECT COUNT(*) as c FROM products', one=True)['c']
    total_users    = query('SELECT COUNT(*) as c FROM users', one=True)['c']
    total_orders   = query('SELECT COUNT(*) as c FROM orders', one=True)['c']
    revenue_row    = query('SELECT SUM(total_price) as s FROM orders', one=True)
    revenue        = revenue_row['s'] if revenue_row['s'] else 0
    recent_orders  = query('''
        SELECT o.id, u.username, p.name as product_name,
               o.quantity, o.total_price, o.order_date
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN products p ON o.product_id = p.id
        ORDER BY o.order_date DESC LIMIT 8
    ''')
    return render_template('admin/dashboard.html',
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        revenue=revenue,
        recent_orders=recent_orders
    )

# ── Products ───────────────────────────────────────────
@app.route('/admin/products')
@admin_required
def admin_products():
    search = request.args.get('q', '').strip()
    if search:
        products = query(
            'SELECT * FROM products WHERE name ILIKE %s OR category ILIKE %s ORDER BY id DESC',
            [f'%{search}%', f'%{search}%']
        )
    else:
        products = query('SELECT * FROM products ORDER BY id DESC')
    return render_template('admin/products.html', products=products, search=search)

@app.route('/admin/add-product', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name           = request.form['name'].strip()
        description    = request.form['description'].strip()
        price          = float(request.form['price'])
        original_price = request.form.get('original_price', '').strip()
        original_price = float(original_price) if original_price else None
        category       = request.form['category']
        image_url      = request.form['image_url'].strip()
        stock          = int(request.form['stock'])
        rating         = float(request.form['rating'])
        badge          = request.form.get('badge', '').strip() or None

        if not all([name, description, price, category, image_url]):
            flash('Please fill all required fields!', 'danger')
            return render_template('admin/add_product.html')

        db = get_db()
        cur = db.cursor()
        cur.execute('''
            INSERT INTO products
            (name, description, price, original_price, category,
             image_url, stock, rating, badge)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', [name, description, price, original_price, category,
              image_url, stock, rating, badge])
        db.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html')

@app.route('/admin/edit-product/<int:pid>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(pid):
    product = query('SELECT * FROM products WHERE id=%s', [pid], one=True)
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        name           = request.form['name'].strip()
        description    = request.form['description'].strip()
        price          = float(request.form['price'])
        original_price = request.form.get('original_price', '').strip()
        original_price = float(original_price) if original_price else None
        category       = request.form['category']
        image_url      = request.form['image_url'].strip()
        stock          = int(request.form['stock'])
        rating         = float(request.form['rating'])
        badge          = request.form.get('badge', '').strip() or None

        db = get_db()
        cur = db.cursor()
        cur.execute('''
            UPDATE products SET
            name=%s, description=%s, price=%s, original_price=%s,
            category=%s, image_url=%s, stock=%s, rating=%s, badge=%s
            WHERE id=%s
        ''', [name, description, price, original_price, category,
              image_url, stock, rating, badge, pid])
        db.commit()
        flash(f'Product "{name}" updated!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete-product/<int:pid>')
@admin_required
def admin_delete_product(pid):
    product = query('SELECT name FROM products WHERE id=%s', [pid], one=True)
    if product:
        db = get_db()
        cur = db.cursor()
        cur.execute('DELETE FROM products WHERE id=%s', [pid])
        db.commit()
        flash(f'Product deleted!', 'success')
    return redirect(url_for('admin_products'))

# ── Orders ─────────────────────────────────────────────
@app.route('/admin/orders')
@admin_required
def admin_orders():
    search = request.args.get('q', '').strip()
    if search:
        orders = query('''
            SELECT o.id, u.username, u.email, p.name as product_name,
                   o.quantity, o.total_price, o.order_date
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE u.username ILIKE %s OR p.name ILIKE %s
            ORDER BY o.order_date DESC
        ''', [f'%{search}%', f'%{search}%'])
    else:
        orders = query('''
            SELECT o.id, u.username, u.email, p.name as product_name,
                   o.quantity, o.total_price, o.order_date
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.order_date DESC
        ''')
    return render_template('admin/orders.html', orders=orders, search=search)

# ── Users ──────────────────────────────────────────────
@app.route('/admin/users')
@admin_required
def admin_users():
    search = request.args.get('q', '').strip()
    if search:
        users = query(
            'SELECT * FROM users WHERE username ILIKE %s OR email ILIKE %s ORDER BY id DESC',
            [f'%{search}%', f'%{search}%']
        )
    else:
        users = query('SELECT * FROM users ORDER BY id DESC')
    return render_template('admin/users.html', users=users, search=search)

@app.route('/admin/delete-user/<int:uid>')
@admin_required
def admin_delete_user(uid):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM orders WHERE user_id=%s', [uid])
    cur.execute('DELETE FROM users WHERE id=%s', [uid])
    db.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)