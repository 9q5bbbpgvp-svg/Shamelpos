from flask import Flask, render_template, request, redirect, url_for, session, g, flash, jsonify
import sqlite3, os, datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'pos.db')

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-random-key'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()

# Initialize DB if not exists
if not os.path.exists(DB_PATH):
    with app.app_context():
        init_db()
        # create default admin user
        db = get_db()
        db.execute('INSERT INTO users (username, password_hash) VALUES (?,?)',
                   ('admin', generate_password_hash('1234')))
        db.commit()

# Helpers
def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query('SELECT * FROM users WHERE username = ?', (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = username
            return redirect(url_for('index'))
        flash('بيانات الدخول غير صحيحة', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
@login_required
def index():
    today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('index.html', today=today, user=session.get('user'))

# Items / catalog
@app.route('/items')
@login_required
def items():
    cats = query('SELECT DISTINCT category FROM items')
    items = query('SELECT * FROM items')
    return render_template('items.html', categories=[c['category'] for c in cats], items=items)

@app.route('/items/add', methods=['POST'])
@login_required
def add_item():
    name = request.form['name']
    category = request.form['category']
    buy_price = float(request.form['buy_price'] or 0)
    sell_price = float(request.form['sell_price'] or 0)
    qty = int(request.form['qty'] or 0)
    execute('INSERT INTO items (name, category, buy_price, sell_price, qty) VALUES (?,?,?,?,?)',
            (name, category, buy_price, sell_price, qty))
    flash('تم إضافة الصنف', 'success')
    return redirect(url_for('items'))

@app.route('/items/update/<int:item_id>', methods=['POST'])
@login_required
def update_item(item_id):
    name = request.form['name']
    category = request.form['category']
    buy_price = float(request.form['buy_price'] or 0)
    sell_price = float(request.form['sell_price'] or 0)
    qty = int(request.form['qty'] or 0)
    execute('UPDATE items SET name=?, category=?, buy_price=?, sell_price=?, qty=? WHERE id=?',
            (name, category, buy_price, sell_price, qty, item_id))
    flash('تم تعديل الصنف', 'success')
    return redirect(url_for('items'))

@app.route('/items/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    execute('DELETE FROM items WHERE id=?', (item_id,))
    flash('تم حذف الصنف', 'warning')
    return redirect(url_for('items'))

# Purchases
@app.route('/purchases')
@login_required
def purchases():
    pur = query('SELECT * FROM purchases ORDER BY created_at DESC')
    return render_template('purchases.html', purchases=pur)

@app.route('/purchases/new', methods=['POST'])
@login_required
def new_purchase():
    data = request.get_json()
    items = data.get('items', [])
    total = 0
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pid = execute('INSERT INTO purchases (created_at, total) VALUES (?,?)', (created_at, 0))
    for it in items:
        item_id = int(it['id'])
        qty = int(it['qty'])
        buy_price = float(it['buy_price'])
        sell_price = float(it.get('sell_price', 0))
        line_total = qty * buy_price
        total += line_total
        execute('INSERT INTO purchase_details (purchase_id, item_id, qty, buy_price, sell_price) VALUES (?,?,?,?,?)',
                (pid, item_id, qty, buy_price, sell_price))
        # update item qty and possibly update buy/sell prices
        row = query('SELECT * FROM items WHERE id=?', (item_id,), one=True)
        if row:
            new_qty = row['qty'] + qty
            # optionally update buy price to latest and sell price if provided
            execute('UPDATE items SET qty=?, buy_price=?, sell_price=? WHERE id=?',
                    (new_qty, buy_price, sell_price or row['sell_price'], item_id))
    execute('UPDATE purchases SET total=? WHERE id=?', (total, pid))
    return jsonify({'status':'ok', 'purchase_id': pid})

# Sales
@app.route('/sales')
@login_required
def sales():
    s = query('SELECT * FROM sales ORDER BY created_at DESC')
    return render_template('sales.html', sales=s)

@app.route('/sales/new', methods=['POST'])
@login_required
def new_sale():
    data = request.get_json()
    items = data.get('items', [])
    payment_type = data.get('payment_type','cash')  # cash or credit
    total = 0
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sid = execute('INSERT INTO sales (created_at, total, payment_type) VALUES (?,?,?)', (created_at, 0, payment_type))
    for it in items:
        item_id = int(it['id'])
        qty = int(it['qty'])
        price = float(it['price'])
        line_total = qty * price
        total += line_total
        execute('INSERT INTO sale_details (sale_id, item_id, qty, price) VALUES (?,?,?,?)',
                (sid, item_id, qty, price))
        # decrease stock
        row = query('SELECT * FROM items WHERE id=?', (item_id,), one=True)
        if row:
            new_qty = max(0, row['qty'] - qty)
            execute('UPDATE items SET qty=? WHERE id=?', (new_qty, item_id))
    execute('UPDATE sales SET total=? WHERE id=?', (total, sid))
    return jsonify({'status':'ok', 'sale_id': sid})

# Reports
@app.route('/reports', methods=['GET','POST'])
@login_required
def reports():
    start = request.args.get('start')
    end = request.args.get('end')
    items = query('SELECT * FROM items')
    report = []
    if start and end:
        # convert to datetime strings inclusive
        s = start + ' 00:00:00'
        e = end + ' 23:59:59'
        # compute sold qty per item and profit based on purchase history
        for it in items:
            item_id = it['id']
            sold_rows = query('SELECT SUM(qty) as sold_qty, AVG(price) as avg_sell_price FROM sale_details sd JOIN sales s ON sd.sale_id=s.id WHERE sd.item_id=? AND s.created_at BETWEEN ? AND ?', (item_id, s, e), one=True)
            sold_qty = sold_rows['sold_qty'] or 0
            avg_price = sold_rows['avg_sell_price'] or 0
            # compute average buy price from purchase_details within period (or overall)
            buy_rows = query('SELECT SUM(qty) as bought_qty, SUM(qty*buy_price) as total_buy FROM purchase_details pd JOIN purchases p ON pd.purchase_id=p.id WHERE pd.item_id=? AND p.created_at BETWEEN ? AND ?', (item_id, s, e), one=True)
            bought_qty = buy_rows['bought_qty'] or 0
            total_buy = buy_rows['total_buy'] or 0
            avg_buy = (total_buy / bought_qty) if bought_qty else it['buy_price']
            profit = (avg_price - avg_buy) * sold_qty
            report.append({'id':item_id, 'name':it['name'], 'sold_qty': sold_qty, 'avg_sell': round(avg_price,2), 'avg_buy': round(avg_buy,2), 'profit': round(profit,2), 'remaining': it['qty']})
    return render_template('reports.html', report=report, items=items, start=start, end=end)

# Shift closing
@app.route('/shift')
@login_required
def shift():
    # summarize today's totals
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    s = today + ' 00:00:00'
    e = today + ' 23:59:59'
    cash = query('SELECT SUM(total) as sum FROM sales WHERE payment_type="cash" AND created_at BETWEEN ? AND ?', (s,e), one=True)['sum'] or 0
    credit = query('SELECT SUM(total) as sum FROM sales WHERE payment_type="credit" AND created_at BETWEEN ? AND ?', (s,e), one=True)['sum'] or 0
    return render_template('shift.html', cash=cash, credit=credit, today=today)

if __name__ == '__main__':
    app.run(debug=True)
