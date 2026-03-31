import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
PRODUCTS = [
    ('Apple MacBook Pro 14" M3 Pro',
        'Supercharged by the M3 Pro chip with a 12-core CPU and 18-core GPU. Brilliant 14.2-inch Liquid Retina XDR display with ProMotion, up to 120 Hz. Up to 22 hours of battery life and MagSafe 3 charging. Thunderbolt 4 ports, HDMI 2.1, SDXC card slot. Available in Space Black and Silver.',
        1599.99, 1799.99, 'Electronics',
        'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80',
        35, 4.9, 4821, 'Best Seller'),
    ('Dell XPS 15 OLED — Intel Core i9',
        'Stunning 15.6-inch 3.5K OLED touch display with 100% DCI-P3 and DisplayHDR 500 True Black. Powered by Intel Core i9-13900H and NVIDIA RTX 4070. 32 GB DDR5 RAM, 1 TB PCIe NVMe SSD. Premium CNC-machined aluminium chassis weighing just 1.86 kg. Thunderbolt 4, Wi-Fi 6E and a best-in-class keyboard.',
        1849.99, 2099.99, 'Electronics',
        'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=800&q=80',
        22, 4.7, 2934, 'Hot'),
    ('Apple iPhone 15 Pro Max 256 GB',
        'Titanium design — the lightest Pro ever. A17 Pro chip with a 6-core GPU pushes the boundaries of what a smartphone can do. Pro camera system with 5x Telephoto, 48 MP Main and Ultra Wide. USB 3 speeds via USB-C. Action button. Up to 29 hours of video playback.',
        1199.99, 1299.99, 'Electronics',
        'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&q=80',
        64, 4.9, 9402, 'New'),
    ('Samsung Galaxy S24 Ultra 512 GB',
        'Galaxy AI is here. Embedded S Pen, 200 MP Adaptive Pixel sensor, Snapdragon 8 Gen 3 for Galaxy, 12 GB RAM. Titanium frame, Corning Gorilla Glass Armor. 5,000 mAh battery with 45 W fast charge.',
        1299.99, 1499.99, 'Electronics',
        'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&q=80',
        88, 4.8, 7155, 'Trending'),
    ('Sony WH-1000XM5 Wireless Headphones',
        'Industry-leading noise cancelling powered by two processors and 8 microphones. Up to 30 hours battery. Multipoint connection for two devices simultaneously. Hi-Res Audio certified.',
        279.99, 349.99, 'Audio',
        'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
        145, 4.9, 18632, 'Best Seller'),
    ('Apple AirPods Pro (2nd Gen) — USB-C',
        'Up to 2x more Active Noise Cancellation. Adaptive Audio seamlessly blends ANC and Transparency mode. Up to 30 hours total listening time. IP54 rated. USB-C and MagSafe charging.',
        249.99, 279.99, 'Audio',
        'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=800&q=80',
        210, 4.8, 14209, 'Choice'),
    ('Nike Air Max 270 React — Mens',
        'Nike first lifestyle Air unit is bigger than ever, offering maximum cushioning under the heel for all-day comfort. React foam midsole provides a smooth, springy ride.',
        129.99, 159.99, 'Footwear',
        'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80',
        320, 4.7, 11847, 'Trending'),
    ('Adidas Ultraboost 23 Running Shoes',
        'Every step returns energy. Responsive Boost midsole absorbs impact and returns it with each stride. Primeknit+ upper adapts to your foot for a sock-like fit.',
        179.99, 199.99, 'Footwear',
        'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&q=80',
        185, 4.6, 8743, 'Hot'),
    ('Apple Watch Series 9 GPS 45 mm',
        'The most capable Apple Watch yet. S9 SiP chip and 2x brighter display up to 2,000 nits. New Double Tap gesture. Blood oxygen, ECG sensors. Crash Detection. 18-hour battery life.',
        429.99, 469.99, 'Wearables',
        'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&q=80',
        72, 4.8, 6391, 'New'),
    ('Samsung Galaxy Watch 6 Classic 47 mm',
        'Iconic rotating bezel for intuitive navigation. 1.5-inch Super AMOLED display. Advanced health with BioActive sensor, sleep coaching, body composition monitoring. Up to 40 hours battery.',
        329.99, 399.99, 'Wearables',
        'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
        93, 4.7, 4872, 'Sale'),
    ('Bellroy Tokyo Totepack Premium',
        'A refined, functional pack that converts between a backpack and a carry-all tote in seconds. Padded 16 inch laptop sleeve. 20 L capacity. Certified B Corp.',
        219.99, 259.99, 'Fashion',
        'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&q=80',
        58, 4.6, 2108, 'Choice'),
    ('Louis Vuitton Neverfull MM Tote Bag',
        'The iconic Louis Vuitton Neverfull in Monogram coated canvas. Removable zipped pouch doubles as a clutch. Dimensions: 31x28x14 cm. Comes with dustbag and authenticity card.',
        1490.00, None, 'Fashion',
        'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800&q=80',
        12, 4.9, 3654, 'Luxury'),
    ('Logitech MX Keys S Wireless Keyboard',
        'Smart illuminated keys with Perfect Stroke. Type on up to 3 devices with Easy-Switch. USB-C rechargeable — one charge lasts up to 10 days with backlighting on.',
        109.99, 129.99, 'Peripherals',
        'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80',
        230, 4.7, 12541, 'Best Seller'),
    ('Keychron Q3 Pro QMK/VIA 80% Keyboard',
        'Full aluminium body with gasket mount. Hot-swappable PCB. RGB per-key backlight. Fully programmable via QMK/VIA firmware. Wired or Bluetooth 5.1.',
        179.99, 209.99, 'Peripherals',
        'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=800&q=80',
        67, 4.8, 5238, 'Hot'),
    ('Logitech MX Master 3S Wireless Mouse',
        'Ultra-fast MagSpeed electromagnetic scrolling. 8,000 DPI sensor tracks on any surface including glass. USB-C rechargeable — 70-day battery on a full charge.',
        99.99, 119.99, 'Peripherals',
        'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80',
        290, 4.8, 21047, 'Best Seller'),
    ('Razer DeathAdder V3 Pro Gaming Mouse',
        '90-hour battery life. Focus Pro 30K Optical Sensor with 30,000 DPI. HyperSpeed Wireless at 4 KHz polling. Ultralight ergonomic design at just 64 g.',
        149.99, 179.99, 'Peripherals',
        'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&q=80',
        112, 4.7, 8914, 'Choice'),
]

def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # create table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id       SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email    TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS orders (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER,
        product_id  INTEGER,
        quantity    INTEGER,
        total_price REAL,
        order_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''DROP TABLE IF EXISTS products''')
    cur.execute('''CREATE TABLE products (
        id             SERIAL PRIMARY KEY,
        name           TEXT    NOT NULL,
        description    TEXT    NOT NULL,
        price          REAL    NOT NULL,
        original_price REAL,
        category       TEXT    NOT NULL,
        image_url      TEXT    NOT NULL,
        stock          INTEGER DEFAULT 100,
        rating         REAL    DEFAULT 4.5,
        review_count   INTEGER DEFAULT 0,
        badge          TEXT
    )''')

    cur.executemany(
        '''INSERT INTO products
           (name, description, price, original_price, category,
            image_url, stock, rating, review_count, badge)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        PRODUCTS,
    )
    conn.commit()

    cur.execute('SELECT COUNT(*) FROM products')
    count = cur.fetchone()[0]
    print(f'✅ Seeded {count} products into Supabase!')
    conn.close()

if __name__ == '__main__':
    seed()
