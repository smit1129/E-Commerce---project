import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shopzone-secret-key-2024'

# Supabase PostgreSQL URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres.ijgtygmmnsfuunycwbgz:Smitgamit@2025@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres')

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
        if user and check_password_hash(user['password'],password):
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

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)