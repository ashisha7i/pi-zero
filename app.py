from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = 'shopping.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('PRAGMA foreign_keys = ON')

        # Create tables if they don't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                list_id INTEGER,
                name TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY(list_id) REFERENCES lists(id) ON DELETE CASCADE
            )
        ''')

        # Safely add missing columns to existing tables
        try:
            conn.execute('ALTER TABLE lists ADD COLUMN name TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute('ALTER TABLE items ADD COLUMN list_id INTEGER')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute('ALTER TABLE items ADD COLUMN sort_order INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/api/lists', methods=['GET', 'POST'])
def handle_lists():
    with sqlite3.connect(DB_FILE) as conn:
        if request.method == 'POST':
            data = request.get_json()
            if data and data.get('name'):
                conn.execute('INSERT INTO lists (name) VALUES (?)', (data['name'].strip(),))
            return jsonify({'status': 'success'})
        else:
            lists = conn.execute('SELECT id, name FROM lists').fetchall()
            return jsonify([{'id': row[0], 'name': row[1]} for row in lists])

@app.route('/api/lists/<int:list_id>', methods=['DELETE', 'PUT'])
def modify_list(list_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        if request.method == 'PUT':
            data = request.get_json()
            if data and data.get('name'):
                conn.execute('UPDATE lists SET name = ? WHERE id = ?', (data['name'].strip(), list_id))
            return jsonify({'status': 'success'})
        conn.execute('DELETE FROM items WHERE list_id = ?', (list_id,))
        conn.execute('DELETE FROM lists WHERE id = ?', (list_id,))
    return jsonify({'status': 'success'})

@app.route('/list/<int:list_id>')
def view_list(list_id):
    with sqlite3.connect(DB_FILE) as conn:
        lst = conn.execute('SELECT name FROM lists WHERE id = ?', (list_id,)).fetchone()
        if not lst:
            return "List not found", 404
        return render_template('list.html', list_id=list_id, list_name=lst[0])

@app.route('/api/items/<int:list_id>')
def get_items(list_id):
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute('SELECT id, name, done FROM items WHERE list_id = ? ORDER BY sort_order ASC, id ASC', (list_id,)).fetchall()
    return jsonify([{'id': int(row[0]), 'name': str(row[1]), 'done': int(row[2])} for row in items])

@app.route('/api/add/<int:list_id>', methods=['POST'])
def add_item(list_id):
    data = request.get_json()
    if data and data.get('item'):
        with sqlite3.connect(DB_FILE) as conn:
            max_order_row = conn.execute('SELECT MAX(sort_order) FROM items WHERE list_id = ?', (list_id,)).fetchone()
            max_order = 0 if max_order_row[0] is None else max_order_row[0] + 1
            conn.execute('INSERT INTO items (list_id, name, done, sort_order) VALUES (?, ?, 0, ?)', (list_id, data['item'].strip(), max_order))
    return jsonify({'status': 'success'})

@app.route('/toggle/<int:item_id>', methods=['POST'])
def toggle(item_id):
    with sqlite3.connect(DB_FILE) as conn:
        current = conn.execute('SELECT done FROM items WHERE id = ?', (item_id,)).fetchone()
        if current:
            new_status = 0 if current[0] == 1 else 1
            conn.execute('UPDATE items SET done = ? WHERE id = ?', (new_status, item_id))
    return jsonify({'status': 'success'})

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
    return jsonify({'status': 'success'})

@app.route('/edit/<int:item_id>', methods=['POST'])
def edit(item_id):
    data = request.get_json()
    if data and data.get('name'):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('UPDATE items SET name = ? WHERE id = ?', (data['name'].strip(), item_id))
    return jsonify({'status': 'success'})

@app.route('/reorder', methods=['POST'])
def reorder():
    data = request.get_json()
    if data and data.get('order'):
        with sqlite3.connect(DB_FILE) as conn:
            for index, item_id in enumerate(data['order']):
                conn.execute('UPDATE items SET sort_order = ? WHERE id = ?', (index, int(item_id)))
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
