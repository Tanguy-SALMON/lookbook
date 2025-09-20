[38;2;216;222;233m-- Create products table with proper schema[0m
[38;2;216;222;233mDROP TABLE IF EXISTS products;[0m

[38;2;216;222;233mCREATE TABLE products ([0m
[38;2;216;222;233m    id INTEGER PRIMARY KEY AUTOINCREMENT,[0m
[38;2;216;222;233m    sku TEXT UNIQUE NOT NULL,[0m
[38;2;216;222;233m    title TEXT NOT NULL,[0m
[38;2;216;222;233m    price REAL NOT NULL,[0m
[38;2;216;222;233m    size_range TEXT DEFAULT '[]',[0m
[38;2;216;222;233m    image_key TEXT NOT NULL,[0m
[38;2;216;222;233m    attributes TEXT DEFAULT '{}',[0m
[38;2;216;222;233m    in_stock INTEGER DEFAULT 1,[0m
[38;2;216;222;233m    created_at TEXT DEFAULT CURRENT_TIMESTAMP,[0m
[38;2;216;222;233m    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,[0m
[38;2;216;222;233m    season TEXT,[0m
[38;2;216;222;233m    url_key TEXT UNIQUE,[0m
[38;2;216;222;233m    product_created_at TEXT,[0m
[38;2;216;222;233m    stock_qty INTEGER DEFAULT 0,[0m
[38;2;216;222;233m    category TEXT,[0m
[38;2;216;222;233m    color TEXT,[0m
[38;2;216;222;233m    material TEXT,[0m
[38;2;216;222;233m    pattern TEXT,[0m
[38;2;216;222;233m    occasion TEXT[0m
[38;2;216;222;233m);[0m

[38;2;216;222;233m-- Create indexes for performance[0m
[38;2;216;222;233mCREATE INDEX idx_products_sku ON products(sku);[0m
[38;2;216;222;233mCREATE INDEX idx_products_price ON products(price);[0m
[38;2;216;222;233mCREATE INDEX idx_products_in_stock ON products(in_stock);[0m
[38;2;216;222;233mCREATE INDEX idx_products_category ON products(category);[0m
[38;2;216;222;233mCREATE INDEX idx_products_color ON products(color);[0m
[38;2;216;222;233mCREATE INDEX idx_products_material ON products(material);[0m
[38;2;216;222;233mCREATE INDEX idx_products_season ON products(season);[0m
[38;2;216;222;233mCREATE INDEX idx_products_occasion ON products(occasion);[0m
[38;2;216;222;233mCREATE INDEX idx_products_url_key ON products(url_key);[0m
