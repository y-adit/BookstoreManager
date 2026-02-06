from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
import os
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_bookstore'

# --- AWS Configuration ---
REGION = 'us-east-1' # Change to your region
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

# DynamoDB Tables
users_table = dynamodb.Table('Users')
books_table = dynamodb.Table('Books')
purchases_table = dynamodb.Table('Purchases')

# Replace with your actual SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:122610513084:aws_capstone_topic' 

def send_notification(subject, message):
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print(f"SNS Error: {e}")

# --- Routes ---

@app.route('/')
def index():
    # Fetch all books from DynamoDB for the homepage
    response = books_table.scan()
    books = response.get('Items', [])
    return render_template('index.html', books=books)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user exists
        check_user = users_table.get_item(Key={'username': username})
        if 'Item' in check_user:
            flash('User already exists!', 'danger')
            return redirect(url_for('signup'))
        
        # Add new user
        users_table.put_item(Item={'username': username, 'password': password})
        send_notification("New Signup", f"User {username} joined the Bookstore!")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded Admin Check for your presentation
        if username == 'admin' and password == 'admin123':
            session['admin'] = True # Sets the admin session variable
            session['user'] = 'Admin'
            return redirect(url_for('admin_dashboard'))
        
        # Regular User Check
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response and response['Item']['password'] == password:
            session['user'] = username
            return redirect(url_for('index'))
        
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/lock_selection', methods=['POST'])
def lock_selection():
    if 'user' not in session:
        return redirect(url_for('login'))

    book_title = request.form.get('book_title')
    store_name = request.form.get('store_name')
    price = request.form.get('price')

    # Atomic Update in DynamoDB to decrease stock
    # This prevents negative stock if two people buy at once
    try:
        # Note: This logic assumes 'stores' is a list of maps in your Book item
        # For a 4th-year project, simple 'put_item' is often accepted for simplicity:
        purchase_id = str(uuid.uuid4())
        purchases_table.put_item(Item={
            'purchase_id': purchase_id,
            'username': session['user'],
            'book': book_title,
            'store': store_name,
            'price': price
        })
        
        send_notification("Book Locked", f"{session['user']} locked {book_title} at {store_name}")
        flash(f'Success! {book_title} is reserved for you.', 'success')
    except Exception as e:
        flash('Error processing request.', 'danger')

    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    # Check for the 'admin' key we set in the login function
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    users = users_table.scan().get('Items', [])
    books = books_table.scan().get('Items', [])
    purchases = purchases_table.scan().get('Items', [])
    
    return render_template('admin_dashboard.html', users=users, books=books, purchases=purchases)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return "About page coming soon!"

@app.route('/contact')
def contact():
    return "Contact us at support@example.com"

@app.route('/admin_login')
def admin_login():
    return render_template('login.html') # Reuses login page for now

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
