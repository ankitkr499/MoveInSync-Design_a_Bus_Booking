from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from database import db, Bus, User, Admin, Seat
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

# Add this function to your database.py
def init_admin():
    with app.app_context():
        admin_exists = Admin.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = Admin(username='admin', password='password')
            db.session.add(admin)
            db.session.commit()


def init_users():
    # Function to initialize a demo user
    with app.app_context():
        demo_user_exists = User.query.filter_by(username='user').first()
        if not demo_user_exists:
            demo_user = User(username='user', password='password')
            db.session.add(demo_user)
            db.session.commit()            

with app.app_context():
    db.create_all()
    init_admin() 
    init_users()

# Decorators for authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        user = User.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        elif user:
            session['user'] = True
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/admin/add_bus', methods=['GET', 'POST'])
@admin_required
def add_bus():
    if request.method == 'POST':
        data = request.form
        bus = Bus(
            bus_name=data['bus_name'],
            total_seats=int(data['total_seats']),
            operation_days=data['operation_days'],
            source=data['source'],
            destination=data['destination'],
            distance=int(data['distance']),
            eta=data['eta']
        )
        db.session.add(bus)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_bus.html')

@app.route('/admin/update_bus/<int:bus_id>', methods=['GET', 'POST'])
@admin_required
def update_bus(bus_id):
    bus = Bus.query.get(bus_id)
    if not bus:
        return jsonify({"message": "Bus not found"}), 404

    if request.method == 'POST':
        data = request.form
        bus.bus_name = data['bus_name']
        bus.total_seats = int(data['total_seats'])
        bus.operation_days = data['operation_days']
        bus.source = data['source']
        bus.destination = data['destination']
        bus.distance = int(data['distance'])
        bus.eta = data['eta']
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('update_bus.html', bus=bus)

@app.route('/admin/delete_bus', methods=['GET', 'POST'])
@admin_required
def delete_bus():
    if request.method == 'POST':
        bus_id = int(request.form['bus_id'])
        bus = Bus.query.get(bus_id)
        if bus:
            db.session.delete(bus)
            db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('delete_bus.html')

@app.route('/user/browse_buses', methods=['GET', 'POST'])
@login_required
def browse_buses():
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        buses = Bus.query.filter_by(source=source, destination=destination).all()
        return render_template('browse_buses.html', buses=buses)
    return render_template('browse_buses.html')

@app.route('/user/check_seat_availability/<int:bus_id>', methods=['GET'])
@login_required
def check_seat_availability(bus_id):
    bus = Bus.query.get(bus_id)
    if bus:
        seat_plan = Seat.query.filter_by(bus_id=bus_id).all()
        seat_status = [
            {"seat_number": seat.seat_number, "status": "Booked" if seat.is_booked else "Available"} 
            for seat in seat_plan
        ]
        return render_template('check_seat_availability.html', seat_status=seat_status, bus_id=bus_id)
    return jsonify({"message": "Bus not found"}), 404

@app.route('/user/book_seat/<int:bus_id>', methods=['GET', 'POST'])
@login_required
def book_seat(bus_id):
    bus = Bus.query.get(bus_id)
    if not bus:
        return jsonify({"message": "Bus not found"}), 404

    if request.method == 'POST':
        seat_number = int(request.form['seat_number'])
        seat = Seat.query.filter_by(bus_id=bus_id, seat_number=seat_number).first()
        if seat and not seat.is_booked:
            seat.is_booked = True
            seat.user_id = session['user_id']
            bus.current_occupancy += 1
            db.session.commit()
            return redirect(url_for('user_dashboard'))
    return render_template('book_seat.html', bus_id=bus_id)

@app.route('/user/cancel_seat/<int:bus_id>', methods=['GET', 'POST'])
@login_required
def cancel_seat(bus_id):
    bus = Bus.query.get(bus_id)
    if not bus:
        return jsonify({"message": "Bus not found"}), 404

    if request.method == 'POST':
        seat_number = int(request.form['seat_number'])
        seat = Seat.query.filter_by(bus_id=bus_id, seat_number=seat_number).first()
        if seat and seat.is_booked and seat.user_id == session['user_id']:
            seat.is_booked = False
            seat.user_id = None
            bus.current_occupancy -= 1
            db.session.commit()
            return redirect(url_for('user_dashboard'))
    return render_template('cancel_seat.html', bus_id=bus_id)

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all tables
        init_admin()     # Initialize the admin account
    app.run(debug=True)

