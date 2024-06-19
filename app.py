from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100))
    balance = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    complete = db.Column(db.Boolean, default=False)
    photo = db.Column(db.String)

@app.route("/")
def index():
    todo_list = Todo.query.all()
    total_todo = Todo.query.count()
    completed_todo = Todo.query.filter_by(complete=True).count()
    uncompleted_todo = total_todo - completed_todo
    return render_template("dashboard/index.html", **locals())

@app.route("/register")
def user_register():
    return render_template("dashboard/register.html")

@app.route("/products", methods=["POST"])
def add_products():
    if 'user' not in session or not session['user']['is_admin']:
        return "Unauthorized", 403
    
    name = request.form["name"]
    price = request.form["price"]
    image = request.files["image"]

    if image.filename == "":
        return "No selected file", 400

    filename = "".join(image.filename.split())
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        image.save(filepath)
    except Exception as e:
        return f"Failed to save image: {e}", 500

    product = Todo(name=name, price=price, photo=filename)
    db.session.add(product)
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/login")
def login_page():
    return render_template("dashboard/login.html")

@app.route('/login', methods=['POST'])
def login():
    name = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(name=name, password=password).first()
    if user:
        session['user'] = {'id': user.id, 'name': user.name, 'balance': user.balance, 'is_admin': user.is_admin}
        return redirect(url_for('index'))
    else:
        return 'Invalid username or password'

@app.route('/register', methods=['POST'])
def register():
    name = request.form['username']
    password = request.form['password']
    role = request.form["role"]

    existing_user = User.query.filter_by(name=name).first()
    if existing_user:
        return 'Username already exists!'

    new_user = User(name=name, password=password, is_admin=(role.lower() == 'admin'))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session or not session['user']['is_admin']:
        return "Unauthorized", 403

    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>')
def update(id):
    todo = Todo.query.get(id)
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/about")
def about():
    return render_template("dashboard/about.html")

@app.route("/cart")
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    user = User.query.get(user_id)
    cart_items = Todo.query.filter_by(complete=True).all()
    return render_template("dashboard/cart.html", cart_items=cart_items)

@app.route("/add_to_cart/<int:todo_id>")
def add_to_cart(todo_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    todo = Todo.query.get(todo_id)
    todo.complete = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/remove_from_cart/<int:todo_id>")
def remove_from_cart(todo_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    todo = Todo.query.get(todo_id)
    todo.complete = False
    db.session.commit()
    return redirect(url_for('cart'))

@app.route("/purchase", methods=['POST'])
def purchase():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']
    user = User.query.get(user_id)
    cart_items = Todo.query.filter_by(complete=True).all()
    total_cost = sum(item.price for item in cart_items)

    if user.balance < total_cost:
        return "Insufficient balance", 403
    
    user.balance -= total_cost
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    session['user']['balance'] = user.balance
    return redirect(url_for('index'))

@app.route("/add_balance")
def add_balance_page():
    return render_template("dashboard/add_balance.html")

@app.route("/add_balance", methods=['POST'])
def add_balance():
    if 'user' not in session:
        return redirect(url_for('login'))

    amount = int(request.form['amount'])
    user_id = session['user']['id']
    user = User.query.get(user_id)
    user.balance += amount
    db.session.commit()

    session['user']['balance'] = user.balance
    return redirect(url_for('index'))

@app.route('/edit_photo/<int:id>')
def edit_photo(id):
    if 'user' not in session or not session['user']['is_admin']:
        return "Unauthorized", 403

    product = Todo.query.get(id)
    return render_template("dashboard/edit_photo.html", product=product)

@app.route('/update_photo/<int:id>', methods=['POST'])
def update_photo(id):
    if 'user' not in session or not session['user']['is_admin']:
        return "Unauthorized", 403

    product = Todo.query.get(id)
    image = request.files["image"]

    if image.filename == "":
        return "No selected file", 400

    filename = "".join(image.filename.split())
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        image.save(filepath)
    except Exception as e:
        return f"Failed to save image: {e}", 500

    product.photo = filename
    db.session.commit()

    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
