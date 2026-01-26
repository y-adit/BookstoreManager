from flask import Flask, render_template, request, redirect, url_for, flash, session
import random
from faker import Faker

app = Flask(__name__)
app.secret_key = 'bookstore_secret_key'
fake = Faker()

# --- DATA STRUCTURES ---
users = {}
purchases = []
store_details = {}
catalog_books = []

def populate_data(count=50):
    catalog_books.clear()
    store_details.clear()
    for _ in range(count):
        title = fake.catch_phrase().title()
        author = fake.name()
        price_val = random.randint(200, 900)
        catalog_books.append({"title": title, "author": author, "price": f"₹{price_val}"})
        
        stores = []
        for _ in range(random.randint(2, 4)):
            stores.append({
                "name": f"{fake.company()} Books",
                "price": f"₹{price_val - random.randint(-40, 60)}",
                "delivery": random.choice(["Same Day", "2 Days", "5 Days"]),
                "type": random.choice(["Store Pickup", "Home Delivery"]),
                "stock": random.randint(0, 15)
            })
        store_details[title] = stores

populate_data(50)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users[request.form.get('username')] = request.form.get('password')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. Check if the user exists in the dictionary
        if username not in users:
            flash('Error: User does not exist. Please sign up first.', 'danger')
            return redirect(url_for('login'))
        
        # 2. If user exists, check if the password matches
        if users[username] == password:
            session['user'] = username
            return redirect(url_for('home', username=username))
        else:
            flash('Error: Invalid password. Please try again.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/home')
def home():
    u = request.args.get('username', 'Guest')
    user_p = [p for p in purchases if p['username'] == u]
    return render_template('home.html', username=u, books=catalog_books, user_purchases=user_p)

@app.route('/logout')
def logout():
    # This clears everything (User and Admin sessions)
    session.clear() 
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    # If it's a POST request, they are trying to log in
    if request.method == 'POST':
        admin_name = request.form.get('admin_name')
        admin_password = request.form.get('admin_password')
        
        if admin_name == "Admin_Aditya" and admin_password == "Admin@123":
            session['admin_logged_in'] = True # Set a specific admin flag
            return render_template('admin_dashboard.html', all_users=users, all_purchases=purchases, inventory=store_details)
        else:
            flash('Unauthorized Access: Invalid Admin Credentials', 'danger')
            return redirect(url_for('admin_login'))
            
    # If it's a GET request, check if the session flag exists
    if session.get('admin_logged_in'):
        return render_template('admin_dashboard.html', all_users=users, all_purchases=purchases, inventory=store_details)
    
    # Otherwise, show the login form (ensure you have an admin_login.html)
    return render_template('admin.html')
    
@app.route('/buy/<path:book_title>')
def buy_book(book_title):
    options = store_details.get(book_title, [])
    return render_template('availability.html', title=book_title, options=options)

@app.route('/lock_selection', methods=['POST'])
def lock_selection():
    bt, sn, pr = request.form.get('book_title'), request.form.get('store_name'), request.form.get('price')
    if bt in store_details:
        for i in range(len(store_details[bt])):
            if store_details[bt][i]['name'] == sn and store_details[bt][i]['stock'] > 0:
                store_details[bt][i]['stock'] -= 1
                purchases.append({"username": session.get('user'), "book": bt, "store": sn, "price": pr})
                break
    return redirect(url_for('home', username=session.get('user')))

@app.route('/admin/restock', methods=['POST'])
def restock():
    bt, sn = request.form.get('book_title'), request.form.get('store_name')
    amt = int(request.form.get('amount', 0))
    if bt in store_details:
        for s in store_details[bt]:
            if s['name'] == sn:
                s['stock'] += amt
                break
    return redirect(url_for('admin_login'))

# Fix BuildError for about/contact
@app.route('/about')
def about(): return render_template('about.html')
@app.route('/contact')
def contact(): return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)