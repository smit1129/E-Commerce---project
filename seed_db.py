import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), "ecommerce.db")

SCHEMA = """

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    total_price REAL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    original_price REAL,
    category TEXT NOT NULL,
    image_url TEXT NOT NULL,
    stock INTEGER DEFAULT 100,
    rating REAL DEFAULT 4.5,
    review_count INTEGER DEFAULT 0,
    badge TEXT
);
"""

# ── Product data ──────────────────────────────────────────────────────────────
# Columns: name, description, price, original_price,
#          category, image_url, stock, rating, review_count, badge

PRODUCTS = [

    # ── LAPTOP ────────────────────────────────────────────────────────────────
    (
        'Apple MacBook Pro 14" M3 Pro',
        (
            'Supercharged by the M3 Pro chip with a 12-core CPU and 18-core GPU. '
            'Brilliant 14.2-inch Liquid Retina XDR display with ProMotion, up to '
            '120 Hz. Up to 22 hours of battery life and MagSafe 3 charging. '
            'Thunderbolt 4 ports, HDMI 2.1, SDXC card slot. Available in Space '
            'Black and Silver.'
        ),
        1_599.99, 1_799.99,
        'Electronics',
        'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80',
        35, 4.9, 4_821, 'Best Seller',
    ),
    (
        'Dell XPS 15 OLED — Intel Core i9',
        (
            'Stunning 15.6-inch 3.5K OLED touch display with 100% DCI-P3 and '
            'DisplayHDR 500 True Black. Powered by Intel Core i9-13900H and '
            'NVIDIA RTX 4070. 32 GB DDR5 RAM, 1 TB PCIe NVMe SSD. '
            'Premium CNC-machined aluminium chassis weighing just 1.86 kg. '
            'Thunderbolt 4, Wi-Fi 6E and a best-in-class keyboard.'
        ),
        1_849.99, 2_099.99,
        'Electronics',
        'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=800&q=80',
        22, 4.7, 2_934, 'Hot',
    ),

    # ── PHONE ─────────────────────────────────────────────────────────────────
    (
        'Apple iPhone 15 Pro Max 256 GB',
        (
            'Titanium design — the lightest Pro ever. A17 Pro chip with a '
            '6-core GPU pushes the boundaries of what a smartphone can do. '
            'Pro camera system with 5× Telephoto, 48 MP Main and Ultra Wide. '
            'USB 3 speeds via USB-C. Action button. Up to 29 hours of video '
            'playback. Available in Natural Titanium, Blue Titanium & Black Titanium.'
        ),
        1_199.99, 1_299.99,
        'Electronics',
        'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&q=80',
        64, 4.9, 9_402, 'New',
    ),
    (
        'Samsung Galaxy S24 Ultra 512 GB',
        (
            'Galaxy AI is here. Embedded S Pen, 200 MP Adaptive Pixel sensor, '
            'Snapdragon 8 Gen 3 for Galaxy, 12 GB RAM. ProVisual Engine with '
            'Zoom Anyplace and AI-powered editing. Titanium frame, '
            'Corning Gorilla Glass Armor. 5,000 mAh battery with 45 W fast charge. '
            'Available in Titanium Gray, Titanium Black, Titanium Violet and Yellow.'
        ),
        1_299.99, 1_499.99,
        'Electronics',
        'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&q=80',
        88, 4.8, 7_155, 'Trending',
    ),

    # ── HEADPHONES ────────────────────────────────────────────────────────────
    (
        'Sony WH-1000XM5 Wireless Headphones',
        (
            'Industry-leading noise cancelling powered by two processors and '
            '8 microphones. Crystal-clear hands-free calling with beamforming mics. '
            'Up to 30 hours battery; 3-minute quick charge gives 3 hours playback. '
            'Multipoint connection for two devices simultaneously. '
            'Foldable design with soft-fit leather. Hi-Res Audio certified. '
            'Available in Black and Platinum Silver.'
        ),
        279.99, 349.99,
        'Audio',
        'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
        145, 4.9, 18_632, 'Best Seller',
    ),
    (
        'Apple AirPods Pro (2nd Gen) — USB-C',
        (
            'Up to 2× more Active Noise Cancellation than the previous generation. '
            'Adaptive Audio seamlessly blends ANC and Transparency mode. '
            'Personalised Spatial Audio with dynamic head tracking. '
            'Up to 30 hours total listening time with the MagSafe Charging Case. '
            'IP54 rated dust, sweat and water resistant. '
            'Find My network support. USB-C and MagSafe charging.'
        ),
        249.99, 279.99,
        'Audio',
        'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=800&q=80',
        210, 4.8, 14_209, 'Choice',
    ),

    # ── SHOES ─────────────────────────────────────────────────────────────────
    (
        'Nike Air Max 270 React — Men\'s',
        (
            'Nike\'s first lifestyle Air unit is bigger than ever, offering '
            'maximum cushioning under the heel for all-day comfort. '
            'React foam midsole provides a smooth, springy ride. '
            'Breathable mesh upper with TPU overlays for support and style. '
            'Available in sizes UK 6–13 and multiple colourways including '
            'Black/White, Triple White and Volt/Black.'
        ),
        129.99, 159.99,
        'Footwear',
        'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80',
        320, 4.7, 11_847, 'Trending',
    ),
    (
        'Adidas Ultraboost 23 Running Shoes',
        (
            'Every step returns energy. Responsive Boost midsole absorbs impact '
            'and returns it with each stride. Linear Energy Push system creates '
            'a propulsive toe-off. Primeknit+ upper adapts to your foot for a '
            'sock-like fit. Continental™ Rubber outsole for grip in wet and dry '
            'conditions. Available in 12 colourways.'
        ),
        179.99, 199.99,
        'Footwear',
        'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&q=80',
        185, 4.6, 8_743, 'Hot',
    ),

    # ── WATCH ─────────────────────────────────────────────────────────────────
    (
        'Apple Watch Series 9 GPS 45 mm',
        (
            'The most capable Apple Watch yet. S9 SiP chip and 2× brighter '
            'display up to 2,000 nits. New Double Tap gesture. Advanced health '
            'sensors: blood oxygen, ECG, high/low heart rate & irregular rhythm '
            'notifications. Crash Detection. Emergency SOS via satellite. '
            'Carbon neutral. All-day 18-hour battery life. WR50 water resistance.'
        ),
        429.99, 469.99,
        'Wearables',
        'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&q=80',
        72, 4.8, 6_391, 'New',
    ),
    (
        'Samsung Galaxy Watch 6 Classic 47 mm',
        (
            'Iconic rotating bezel for intuitive navigation. 1.5-inch Super '
            'AMOLED display with sapphire crystal glass. Advanced health with '
            'BioActive sensor, sleep coaching, body composition and blood pressure '
            'monitoring. 5 ATM + IP68 rating. Up to 40 hours battery. '
            'Works with Android 10+ and iPhone 11+. Available in Black and Silver.'
        ),
        329.99, 399.99,
        'Wearables',
        'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
        93, 4.7, 4_872, 'Sale',
    ),

    # ── BAG ───────────────────────────────────────────────────────────────────
    (
        'Bellroy Tokyo Totepack Premium',
        (
            'A refined, functional pack with a magnetic tote-carry system that '
            'converts between a backpack and a carry-all tote in seconds. '
            'Premium woven exterior with vegetable-tanned leather accents. '
            'Padded 16" laptop sleeve, hidden organisation pockets and magnetic '
            'clasps. 20 L capacity. Certified B Corp. Available in Black, '
            'Everglade and Stone.'
        ),
        219.99, 259.99,
        'Fashion',
        'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&q=80',
        58, 4.6, 2_108, 'Choice',
    ),
    (
        'Louis Vuitton Neverfull MM Tote Bag',
        (
            'The iconic Louis Vuitton Neverfull in Monogram coated canvas. '
            'Supple sides that cinch to change the bag\'s look and volume. '
            'Removable zipped pouch doubles as a clutch. Microfiber lining, '
            'flat base studs. Can be worn on the shoulder or carried in hand. '
            'Dimensions: 31 × 28 × 14 cm. Comes with dustbag and authenticity card.'
        ),
        1_490.00, None,
        'Fashion',
        'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800&q=80',
        12, 4.9, 3_654, 'Luxury',
    ),

    # ── KEYBOARD ──────────────────────────────────────────────────────────────
    (
        'Logitech MX Keys S Wireless Keyboard',
        (
            'Smart illuminated keys with Perfect Stroke that adjust backlight '
            'based on ambient light. Type on up to 3 devices with Easy-Switch '
            'and Bolt USB receiver or Bluetooth. USB-C rechargeable — one charge '
            'lasts up to 10 days with backlighting on. Flow cross-computer '
            'control. Quiet keys. Compatible with Windows, macOS, Linux, '
            'ChromeOS, iOS and Android.'
        ),
        109.99, 129.99,
        'Peripherals',
        'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80',
        230, 4.7, 12_541, 'Best Seller',
    ),
    (
        'Keychron Q3 Pro QMK/VIA 80% Keyboard',
        (
            'Full aluminium body with gasket mount for a premium typing feel. '
            'Hot-swappable PCB supports 3/5 pin MX switches. Pre-lubed Keychron '
            'K Pro Red switches included. RGB per-key backlight. '
            'Fully programmable via QMK/VIA firmware. Wired or Bluetooth 5.1 '
            '(3-device multipairing). Compatible with Windows, macOS and Linux. '
            'Weight: 1.65 kg.'
        ),
        179.99, 209.99,
        'Peripherals',
        'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=800&q=80',
        67, 4.8, 5_238, 'Hot',
    ),

    # ── MOUSE ─────────────────────────────────────────────────────────────────
    (
        'Logitech MX Master 3S Wireless Mouse',
        (
            'Ultra-fast MagSpeed electromagnetic scrolling — whisper-quiet and '
            '90× faster than a mechanical wheel. 8,000 DPI high-precision sensor '
            'tracks on any surface including glass. Quiet Click buttons. '
            'USB-C rechargeable — 70-day battery on a full charge. '
            'Connect to 3 devices via Bolt USB receiver or Bluetooth. '
            'Compatible with Windows, macOS, Linux, ChromeOS, iPadOS and Android.'
        ),
        99.99, 119.99,
        'Peripherals',
        'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80',
        290, 4.8, 21_047, 'Best Seller',
    ),
    (
        'Razer DeathAdder V3 Pro Gaming Mouse',
        (
            '90-hour battery life — the longest of any wireless gaming mouse. '
            'Focus Pro 30K Optical Sensor with 30,000 DPI, 750 IPS tracking '
            'speed and 70 G acceleration. 5 Razer Optical Mouse Switches rated '
            'for 90 million clicks. HyperSpeed Wireless at 4 KHz polling. '
            'Ultralight ergonomic design at just 64 g. RGB Chroma compatible. '
            'Available in Black and White.'
        ),
        149.99, 179.99,
        'Peripherals',
        'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&q=80',
        112, 4.7, 8_914, 'Choice',
    ),
]

# ── Seed ──────────────────────────────────────────────────────────────────────
def seed():
    conn = sqlite3.connect(DATABASE)
    conn.executescript(SCHEMA)
    conn.executemany(
        '''INSERT INTO products
           (name, description, price, original_price, category,
            image_url, stock, rating, review_count, badge)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        PRODUCTS,
    )
    conn.commit()

    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f'✅  Seeded {count} products into {DATABASE}')

    rows = conn.execute(
        'SELECT id, name, category, price FROM products ORDER BY category, id'
    ).fetchall()
    print()
    print(f'  {"ID":<4}  {"Category":<12}  {"Price":>8}  Name')
    print(f'  {"─"*4}  {"─"*12}  {"─"*8}  {"─"*40}')
    for r in rows:
        print(f'  {r[0]:<4}  {r[2]:<12}  ₹{r[3]:>7.2f}  {r[1]}')

    conn.close()

if __name__ == '__main__':
    seed()
