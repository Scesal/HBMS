"""
models.py — Data Access Layer
Hotel Booking Management System
Handles all database interactions via raw SQL with sqlite3.
"""

import sqlite3
from datetime import date

DATABASE = "hbms.db"


def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row          # Rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialise the database from schema.sql."""
    with open("schema.sql", "r") as f:
        sql = f.read()
    conn = get_db()
    # Split on semicolons so we can execute each statement individually
    # (executescript commits automatically, which is fine for DDL/seeds)
    conn.executescript(sql)
    conn.close()


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def get_user_by_email(email: str):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM Users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id: int):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM Users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return user


def create_user(full_name: str, email: str, hashed_password: str, role: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO Users (full_name, email, password, role) VALUES (?, ?, ?, ?)",
        (full_name, email, hashed_password, role),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Hotel helpers
# ---------------------------------------------------------------------------

def get_all_hotels():
    conn = get_db()
    hotels = conn.execute("SELECT * FROM Hotel ORDER BY city, name").fetchall()
    conn.close()
    return hotels


def get_hotel_by_id(hotel_id: int):
    conn = get_db()
    hotel = conn.execute(
        "SELECT * FROM Hotel WHERE hotel_id = ?", (hotel_id,)
    ).fetchone()
    conn.close()
    return hotel


def search_hotels_by_city(city: str):
    conn = get_db()
    hotels = conn.execute(
        "SELECT * FROM Hotel WHERE city LIKE ? ORDER BY rating DESC",
        (f"%{city}%",),
    ).fetchall()
    conn.close()
    return hotels


def add_hotel(name, city, address, description, rating, image_url):
    conn = get_db()
    conn.execute(
        """INSERT INTO Hotel (name, city, address, description, rating, image_url)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, city, address, description, rating, image_url),
    )
    conn.commit()
    conn.close()


def update_hotel(hotel_id, name, city, address, description, rating, image_url):
    conn = get_db()
    conn.execute(
        """UPDATE Hotel
           SET name=?, city=?, address=?, description=?, rating=?, image_url=?
           WHERE hotel_id=?""",
        (name, city, address, description, rating, image_url, hotel_id),
    )
    conn.commit()
    conn.close()


def delete_hotel(hotel_id: int):
    conn = get_db()
    conn.execute("DELETE FROM Hotel WHERE hotel_id = ?", (hotel_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Room helpers
# ---------------------------------------------------------------------------

def get_rooms_by_hotel(hotel_id: int):
    conn = get_db()
    rooms = conn.execute(
        "SELECT * FROM RoomDetails WHERE hotel_id = ? ORDER BY room_number",
        (hotel_id,),
    ).fetchall()
    conn.close()
    return rooms


def get_room_by_id(room_id: int):
    conn = get_db()
    room = conn.execute(
        """SELECT r.*, h.name AS hotel_name, h.city
           FROM RoomDetails r
           JOIN Hotel h ON r.hotel_id = h.hotel_id
           WHERE r.room_id = ?""",
        (room_id,),
    ).fetchone()
    conn.close()
    return room


def get_available_rooms_by_hotel(hotel_id: int):
    conn = get_db()
    rooms = conn.execute(
        "SELECT * FROM RoomDetails WHERE hotel_id = ? AND is_available = 1",
        (hotel_id,),
    ).fetchall()
    conn.close()
    return rooms


def add_room(hotel_id, room_number, room_type, price_per_night, max_occupancy, amenities):
    conn = get_db()
    conn.execute(
        """INSERT INTO RoomDetails
           (hotel_id, room_number, room_type, price_per_night, max_occupancy, amenities)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (hotel_id, room_number, room_type, price_per_night, max_occupancy, amenities),
    )
    conn.commit()
    conn.close()


def update_room(room_id, room_number, room_type, price_per_night, max_occupancy, amenities, is_available):
    conn = get_db()
    conn.execute(
        """UPDATE RoomDetails
           SET room_number=?, room_type=?, price_per_night=?, max_occupancy=?,
               amenities=?, is_available=?
           WHERE room_id=?""",
        (room_number, room_type, price_per_night, max_occupancy,
         amenities, is_available, room_id),
    )
    conn.commit()
    conn.close()


def delete_room(room_id: int):
    conn = get_db()
    conn.execute("DELETE FROM RoomDetails WHERE room_id = ?", (room_id,))
    conn.commit()
    conn.close()


def set_room_availability(room_id: int, available: bool):
    conn = get_db()
    conn.execute(
        "UPDATE RoomDetails SET is_available = ? WHERE room_id = ?",
        (1 if available else 0, room_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Booking helpers
# ---------------------------------------------------------------------------

def create_booking(user_id, room_id, check_in, check_out, total_price):
    conn = get_db()
    conn.execute(
        """INSERT INTO BookingDetails
           (user_id, room_id, check_in_date, check_out_date, total_price)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, room_id, check_in, check_out, total_price),
    )
    set_room_availability(room_id, False)   # Mark room as unavailable
    conn.commit()
    conn.close()


def get_bookings_by_user(user_id: int):
    conn = get_db()
    bookings = conn.execute(
        """SELECT b.*, r.room_number, r.room_type, h.name AS hotel_name, h.city
           FROM BookingDetails b
           JOIN RoomDetails r ON b.room_id = r.room_id
           JOIN Hotel h ON r.hotel_id = h.hotel_id
           WHERE b.user_id = ?
           ORDER BY b.booked_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return bookings


def get_all_bookings():
    conn = get_db()
    bookings = conn.execute(
        """SELECT b.*, r.room_number, r.room_type,
                  h.name AS hotel_name, h.city,
                  u.full_name AS customer_name, u.email AS customer_email
           FROM BookingDetails b
           JOIN RoomDetails r ON b.room_id = r.room_id
           JOIN Hotel h ON r.hotel_id = h.hotel_id
           JOIN Users u ON b.user_id = u.user_id
           ORDER BY b.booked_at DESC"""
    ).fetchall()
    conn.close()
    return bookings


def get_booking_by_id(booking_id: int):
    conn = get_db()
    booking = conn.execute(
        """SELECT b.*, r.room_number, r.room_type,
                  h.name AS hotel_name, h.city,
                  u.full_name AS customer_name
           FROM BookingDetails b
           JOIN RoomDetails r ON b.room_id = r.room_id
           JOIN Hotel h ON r.hotel_id = h.hotel_id
           JOIN Users u ON b.user_id = u.user_id
           WHERE b.booking_id = ?""",
        (booking_id,),
    ).fetchone()
    conn.close()
    return booking


def cancel_booking(booking_id: int):
    conn = get_db()
    # Fetch the room_id before cancelling so we can free the room
    row = conn.execute(
        "SELECT room_id FROM BookingDetails WHERE booking_id = ?", (booking_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE BookingDetails SET status = 'Cancelled' WHERE booking_id = ?",
            (booking_id,),
        )
        conn.execute(
            "UPDATE RoomDetails SET is_available = 1 WHERE room_id = ?",
            (row["room_id"],),
        )
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Dashboard stats (Admin)
# ---------------------------------------------------------------------------

def get_dashboard_stats():
    conn = get_db()
    stats = {
        "total_hotels":   conn.execute("SELECT COUNT(*) FROM Hotel").fetchone()[0],
        "total_rooms":    conn.execute("SELECT COUNT(*) FROM RoomDetails").fetchone()[0],
        "total_bookings": conn.execute("SELECT COUNT(*) FROM BookingDetails").fetchone()[0],
        "total_customers":conn.execute(
            "SELECT COUNT(*) FROM Users WHERE role='Customer'"
        ).fetchone()[0],
    }
    conn.close()
    return stats
