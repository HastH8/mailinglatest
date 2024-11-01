import os
import csv
import requests
import click 
import qrcode
import base64
import io
from io import BytesIO
from flask import send_file
from flask import Flask, render_template, request, session, redirect, url_for, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from functools import wraps
from flask import abort
from PIL import Image, ImageDraw, ImageFont 


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['DEFAULT_PROFILE_PIC'] = 'static/default-profile.png'
app.config['LOGIN_USERNAME'] = 'Kedi'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(150), nullable=True, default="static/default-profile.png")
    is_admin = db.Column(db.Boolean, default=False)  
    history = db.relationship("History", backref="user", cascade="all, delete-orphan", lazy=True)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.String(100))
    cost = db.Column(db.String(100))
    breakdown = db.Column(db.String(500))
    currency = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_path = os.path.join("static", "qr_codes", f"{data}.png")  
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)   
    img = qr.make_image(fill="black", back_color="white")
    img.save(qr_path) 
    return url_for("static", filename=f"qr_codes/{data}.png")

def convert_to_grams(mass, unit):
    conversion_factors = {"grams": 1, 
                          "kilograms": 1000, 
                          "ounces": 28.3495, 
                          "pounds": 453.592}
    return mass * conversion_factors.get(unit, 1)

def calculate_mail_cost(mass):
    breakdown = []
    if mass <= 30:
        cost = 40
        breakdown.append((f"{mass} grams at base cost", 40))
    elif mass <= 50:
        cost = 55
        breakdown.append((f"{mass} grams at base cost", 55))
    elif mass <= 100:
        cost = 70
        breakdown.append((f"{mass} grams at base cost", 70))
    else:
        base_cost = 70
        breakdown.append(("First 100 grams at base cost", base_cost))
        extra_weight = mass - 100
        additional_cost = ((extra_weight + 49) // 50) * 25
        cost = base_cost + additional_cost
        breakdown.append((f"{extra_weight} grams extra at additional cost", additional_cost))
    return cost, breakdown

def convert_currency(amount, target_currency):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/TRY")
        data = response.json()
        exchange_rate = data['rates'].get(target_currency.upper(), 1)
        return round(amount * exchange_rate, 2), exchange_rate
    except:
        return "Conversion error. Please try again."

# Routes
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    cost, message, breakdown_detail, converted_breakdown = None, None, [], []
    currency = "Sinas"
    qr_code = None
    
    if request.method == "POST":
        try:
            mass = float(request.form.get("mass"))
            unit = request.form.get("unit", "grams")
            currency = request.form.get("currency", "Sinas")
            
            if mass <= 0 or mass > 10000:
                message = "Please enter a weight between 1 and 10,000 grams."
            else:
                mass_in_grams = convert_to_grams(mass, unit)
                cost_in_try, breakdown_detail = calculate_mail_cost(mass_in_grams)
                converted_cost, exchange_rate = convert_currency(cost_in_try, currency)
                converted_breakdown = [(item[0], round(item[1] * exchange_rate, 2)) for item in breakdown_detail]
                
                # Save history
                cost = f"The cost to mail a {mass} {unit} package is {converted_cost} {currency.upper()}."
                history_entry = History(
                    weight=f"{mass} {unit}",
                    cost=f"{converted_cost} {currency.upper()}",
                    breakdown="; ".join([f"{item[0]}: {item[1]} {currency}" for item in converted_breakdown]),
                    currency=currency,
                    user_id=current_user.id
                )
                db.session.add(history_entry)
                db.session.commit()
                qr_data = f"Calculation cost: {cost}, Breakdown: {breakdown_detail}"
                qr_code = generate_qr_code(qr_data)
        except ValueError:
            message = "Invalid input. Please enter a numeric value for weight."

    history = History.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", cost=cost, message=message, history=history, breakdown=converted_breakdown, currency=currency, qr_code=qr_code)

@app.route("/download_breakdown")
def download_breakdown():
    breakdown_data = session.get("latest_qr_code", "No breakdown available")
    image = create_breakdown_image(breakdown_data)
    return send_file(image, as_attachment=True, download_name="cost_breakdown.png")

def create_breakdown_image(breakdown_text):
    font = ImageFont.load_default()
    image = Image.new("RGB", (400, 200), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), breakdown_text, font=font, fill=(0, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
@app.route("/clear_history", methods=["POST"])
@login_required
def clear_history():
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/export_csv")
@login_required
def export_csv():
    user_history = History.query.filter_by(user_id=current_user.id).all()
    if not user_history:
        return redirect(url_for("index"))

    output = [["Weight", "Cost", "Breakdown"]]
    for entry in user_history:
        output.append([entry.weight, entry.cost, entry.breakdown])

    response = make_response("\n".join([",".join(row) for row in output]))
    response.headers["Content-Disposition"] = "attachment; filename=calculation_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for("register"))
        new_user = User(username=username, password=generate_password_hash(password, method="pbkdf2:sha256"))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Login failed. Check your username and password.", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        username = request.form.get("username")
        profile_pic = request.files.get("profile_pic")
        
        if username:
            current_user.username = username

        if profile_pic and profile_pic.filename != '':
            filename = secure_filename(profile_pic.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(file_path)
            current_user.profile_pic = file_path

        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for("index"))
    
    return render_template("edit_profile.html")

@app.route("/update_password", methods=["GET", "POST"])
@login_required
def update_password():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        if not new_password:
            flash("Password cannot be empty.", "error")
            return redirect(url_for("edit_profile"))

        current_user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("index"))
    return render_template("update_password.html")

# Admin routes 
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin", methods=["GET"])
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    user_count = User.query.count()
    total_calculations = History.query.count()
    
    return render_template("admin_dashboard.html", users=users, user_count=user_count, total_calculations=total_calculations)

@app.route("/admin/user/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get("username")
    user.is_admin = request.form.get("is_admin") == "on"
    if username:
        user.username = username
    db.session.commit()
    flash("User updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.cli.command("grant-admin")
@click.argument("username")
def grant_admin(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {username} has been granted admin access.")
    else:
        print(f"User {username} not found.")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)
