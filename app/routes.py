from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Order
from .email_utils import send_admin_email, send_pin_email, send_order_email
from .automation import bot_automation
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/save', methods=['POST'])
def save():
    order_id = request.form['order_id']
    password = request.form['password']
    big_link = request.form['big_link']
    email = request.form.get('email', '')

    return render_template('index.html', order_id=order_id, password=password, big_link=big_link, email=email, show_email_popup=True)

@main_bp.route('/view_db')
def view_db():
    orders = Order.query.all()
    return render_template('view_db.html', orders=orders)

@main_bp.route('/send_email', methods=['POST'])
def send_email():
    order_id = request.form['order_id']
    password = request.form['password']
    big_link = request.form['big_link']
    email = request.form['email']

    # Save admin order into the Order table with role 'admin'
    new_order = Order(order_id=order_id, password=password, big_link=big_link, email=email, role='admin')
    db.session.add(new_order)
    db.session.commit()

    # Implement your email sending logic here
    success = send_order_email(email,order_id)
    if success:
        flash('Email sent successfully!')
    else:
        flash('Failed to send email.')

    return redirect(url_for('main.index'))  # Redirect to index after sending email



@main_bp.route('/customer', methods=['GET', 'POST'])
def customer():
    if request.method == 'POST':
        order_id = request.form['order_id']
        access_code = request.form.get('access_code')
        email = request.form['email']

        # Ensure that access_code is provided
        if not access_code:
            flash('Access code is required!')
            return redirect(url_for('main.customer'))

        # Save customer request into the Order table with role 'customer'
        new_request = Order(order_id=order_id, access_code=access_code, email=email, role='customer')
        db.session.add(new_request)
        db.session.commit()

        bot_automation(order_id)

        # Send email to the admin about the customer request
        if send_admin_email(order_id, access_code, email):
            flash('Request submitted successfully! and automation started')
        else:
            flash('Failed to send request email.')

        return redirect(url_for('main.customer'))

    return render_template('customer.html')

@main_bp.route('/print_orders')
def print_orders():
    all_orders = Order.query.all()

    # Format the result as a string
    orders_data = ""
    for order in all_orders:
        orders_data += f"ID: {order.id}, Order ID: {order.order_id}, Password: {order.password}, "
        orders_data += f"Big Link: {order.big_link}, Email: {order.email}, Role: {order.role}, Access Code: {order.access_code}\n"

    return f"<pre>{orders_data}</pre>"
