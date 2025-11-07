-- users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- items / catalog
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    buy_price REAL DEFAULT 0,
    sell_price REAL DEFAULT 0,
    qty INTEGER DEFAULT 0
);

-- purchases
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    total REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS purchase_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER,
    item_id INTEGER,
    qty INTEGER,
    buy_price REAL,
    sell_price REAL
);

-- sales
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    total REAL DEFAULT 0,
    payment_type TEXT DEFAULT 'cash'
);
CREATE TABLE IF NOT EXISTS sale_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    item_id INTEGER,
    qty INTEGER,
    price REAL
);
