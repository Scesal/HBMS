"""
app.py — Business Logic Layer
Hotel Booking Management System (HBMS)
Flask application with role-based routing and authentication.
"""

from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

import models

app = Flask(__name__)
app.secret_key = "hbms-super-secret-key-change-in-production"


# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

@app.before_request
def load_logged_in_user():
    """Inject the current user into Flask's `g` on every request."""
    user_id = session.get("user_id")
    g.user = models.get_user_by_id(user_id) if user_id else None


# ---------------------------------------------------------------------------
# Authentication decorators
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user is None:
                flash("Please log in.", "warning")
                return redirect(url_for("login"))
            if g.user["role"] not in roles:
                flash("Access denied: insufficient permissions.", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if g.user:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("home"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = models.get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email", "").strip()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")

        if not all([full_name, email, password, confirm]):
            flash("All fields are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif models.get_user_by_email(email):
            flash("An account with this email already exists.", "danger")
        else:
            hashed = generate_password_hash(password)
            models.create_user(full_name, email, hashed, "Customer")
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Shared home route — redirects based on role
# ---------------------------------------------------------------------------

@app.route("/home")
@login_required
def home():
    role = g.user["role"]
    if role == "Admin":
        stats = models.get_dashboard_stats()
        return render_template("admin/dashboard.html", stats=stats)
    elif role == "Employee":
        bookings = models.get_all_bookings()
        return render_template("employee/dashboard.html", bookings=bookings)
    else:
        hotels = models.get_all_hotels()
        return render_template("customer/home.html", hotels=hotels)


# ===========================================================================
# ADMIN ROUTES
# ===========================================================================

# --- Hotels -----------------------------------------------------------------

@app.route("/admin/hotels")
@role_required("Admin")
def admin_hotels():
    hotels = models.get_all_hotels()
    return render_template("admin/hotels.html", hotels=hotels)


@app.route("/admin/hotels/add", methods=["GET", "POST"])
@role_required("Admin")
def admin_add_hotel():
    if request.method == "POST":
        models.add_hotel(
            name        = request.form.get("name", "").strip(),
            city        = request.form.get("city", "").strip(),
            address     = request.form.get("address", "").strip(),
            description = request.form.get("description", "").strip(),
            rating      = float(request.form.get("rating", 0)),
            image_url   = request.form.get("image_url", "").strip(),
        )
        flash("Hotel added successfully.", "success")
        return redirect(url_for("admin_hotels"))
    return render_template("admin/hotel_form.html", hotel=None, action="Add")


@app.route("/admin/hotels/edit/<int:hotel_id>", methods=["GET", "POST"])
@role_required("Admin")
def admin_edit_hotel(hotel_id):
    hotel = models.get_hotel_by_id(hotel_id)
    if not hotel:
        flash("Hotel not found.", "danger")
        return redirect(url_for("admin_hotels"))

    if request.method == "POST":
        models.update_hotel(
            hotel_id    = hotel_id,
            name        = request.form.get("name", "").strip(),
            city        = request.form.get("city", "").strip(),
            address     = request.form.get("address", "").strip(),
            description = request.form.get("description", "").strip(),
            rating      = float(request.form.get("rating", 0)),
            image_url   = request.form.get("image_url", "").strip(),
        )
        flash("Hotel updated successfully.", "success")
        return redirect(url_for("admin_hotels"))

    return render_template("admin/hotel_form.html", hotel=hotel, action="Edit")


@app.route("/admin/hotels/delete/<int:hotel_id>", methods=["POST"])
@role_required("Admin")
def admin_delete_hotel(hotel_id):
    models.delete_hotel(hotel_id)
    flash("Hotel deleted.", "success")
    return redirect(url_for("admin_hotels"))


# --- Rooms ------------------------------------------------------------------

@app.route("/admin/hotels/<int:hotel_id>/rooms")
@role_required("Admin")
def admin_rooms(hotel_id):
    hotel = models.get_hotel_by_id(hotel_id)
    rooms = models.get_rooms_by_hotel(hotel_id)
    return render_template("admin/rooms.html", hotel=hotel, rooms=rooms)


@app.route("/admin/hotels/<int:hotel_id>/rooms/add", methods=["GET", "POST"])
@role_required("Admin")
def admin_add_room(hotel_id):
    hotel = models.get_hotel_by_id(hotel_id)
    if request.method == "POST":
        models.add_room(
            hotel_id        = hotel_id,
            room_number     = request.form.get("room_number", "").strip(),
            room_type       = request.form.get("room_type", "Single"),
            price_per_night = float(request.form.get("price_per_night", 0)),
            max_occupancy   = int(request.form.get("max_occupancy", 2)),
            amenities       = request.form.get("amenities", "").strip(),
        )
        flash("Room added successfully.", "success")
        return redirect(url_for("admin_rooms", hotel_id=hotel_id))
    return render_template("admin/room_form.html", hotel=hotel, room=None, action="Add")


@app.route("/admin/rooms/edit/<int:room_id>", methods=["GET", "POST"])
@role_required("Admin")
def admin_edit_room(room_id):
    room = models.get_room_by_id(room_id)
    if not room:
        flash("Room not found.", "danger")
        return redirect(url_for("admin_hotels"))

    hotel = models.get_hotel_by_id(room["hotel_id"])

    if request.method == "POST":
        models.update_room(
            room_id         = room_id,
            room_number     = request.form.get("room_number", "").strip(),
            room_type       = request.form.get("room_type", "Single"),
            price_per_night = float(request.form.get("price_per_night", 0)),
            max_occupancy   = int(request.form.get("max_occupancy", 2)),
            amenities       = request.form.get("amenities", "").strip(),
            is_available    = int(request.form.get("is_available", 1)),
        )
        flash("Room updated successfully.", "success")
        return redirect(url_for("admin_rooms", hotel_id=room["hotel_id"]))

    return render_template("admin/room_form.html", hotel=hotel, room=room, action="Edit")


@app.route("/admin/rooms/delete/<int:room_id>", methods=["POST"])
@role_required("Admin")
def admin_delete_room(room_id):
    room = models.get_room_by_id(room_id)
    models.delete_room(room_id)
    flash("Room deleted.", "success")
    return redirect(url_for("admin_rooms", hotel_id=room["hotel_id"]))


# ===========================================================================
# CUSTOMER ROUTES
# ===========================================================================

@app.route("/search")
@role_required("Customer")
def search_hotels():
    city   = request.args.get("city", "").strip()
    hotels = models.search_hotels_by_city(city) if city else []
    return render_template("customer/search.html", hotels=hotels, city=city)


@app.route("/hotels/<int:hotel_id>/rooms")
@role_required("Customer")
def view_rooms(hotel_id):
    hotel = models.get_hotel_by_id(hotel_id)
    rooms = models.get_available_rooms_by_hotel(hotel_id)
    return render_template("customer/rooms.html", hotel=hotel, rooms=rooms)


@app.route("/book/<int:room_id>", methods=["GET", "POST"])
@role_required("Customer")
def book_room(room_id):
    room = models.get_room_by_id(room_id)
    if not room or not room["is_available"]:
        flash("This room is no longer available.", "warning")
        return redirect(url_for("home"))

    if request.method == "POST":
        check_in_str  = request.form.get("check_in")
        check_out_str = request.form.get("check_out")

        try:
            check_in  = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Invalid date format.", "danger")
            return render_template("customer/book.html", room=room)

        if check_in < date.today():
            flash("Check-in date cannot be in the past.", "danger")
        elif check_out <= check_in:
            flash("Check-out must be after check-in.", "danger")
        else:
            nights      = (check_out - check_in).days
            total_price = nights * room["price_per_night"]
            models.create_booking(
                user_id     = g.user["user_id"],
                room_id     = room_id,
                check_in    = check_in_str,
                check_out   = check_out_str,
                total_price = total_price,
            )
            flash(
                f"Booking confirmed for {nights} night(s)! Total: ₹{total_price:,.2f}",
                "success"
            )
            return redirect(url_for("my_bookings"))

    return render_template("customer/book.html", room=room)


@app.route("/my-bookings")
@role_required("Customer")
def my_bookings():
    bookings = models.get_bookings_by_user(g.user["user_id"])
    return render_template("customer/my_bookings.html", bookings=bookings)


# ===========================================================================
# EMPLOYEE ROUTES
# ===========================================================================

@app.route("/employee/bookings")
@role_required("Employee")
def employee_bookings():
    bookings = models.get_all_bookings()
    return render_template("employee/bookings.html", bookings=bookings)


@app.route("/employee/bookings/cancel/<int:booking_id>", methods=["POST"])
@role_required("Employee")
def employee_cancel_booking(booking_id):
    booking = models.get_booking_by_id(booking_id)
    if not booking:
        flash("Booking not found.", "danger")
    elif booking["status"] == "Cancelled":
        flash("Booking is already cancelled.", "warning")
    else:
        models.cancel_booking(booking_id)
        flash(f"Booking #{booking_id} has been cancelled.", "success")
    return redirect(url_for("employee_bookings"))


# ===========================================================================
# Error handlers
# ===========================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    models.init_db()
    app.run(debug=True)
