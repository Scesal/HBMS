-- Hotel Booking Management System - Database Schema

PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS Users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('Admin', 'Customer', 'Employee')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Hotel Table
CREATE TABLE IF NOT EXISTS Hotel (
    hotel_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    city        TEXT    NOT NULL,
    address     TEXT    NOT NULL,
    description TEXT,
    rating      REAL    DEFAULT 0.0 CHECK(rating >= 0.0 AND rating <= 5.0),
    image_url   TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- RoomDetails Table
CREATE TABLE IF NOT EXISTS RoomDetails (
    room_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id        INTEGER NOT NULL,
    room_number     TEXT    NOT NULL,
    room_type       TEXT    NOT NULL CHECK(room_type IN ('Single', 'Double', 'Suite', 'Deluxe')),
    price_per_night REAL    NOT NULL CHECK(price_per_night > 0),
    max_occupancy   INTEGER NOT NULL DEFAULT 2,
    is_available    INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0, 1)),
    amenities       TEXT,
    FOREIGN KEY (hotel_id) REFERENCES Hotel(hotel_id) ON DELETE CASCADE,
    UNIQUE (hotel_id, room_number)
);

-- BookingDetails Table
CREATE TABLE IF NOT EXISTS BookingDetails (
    booking_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    room_id         INTEGER NOT NULL,
    check_in_date   TEXT    NOT NULL,
    check_out_date  TEXT    NOT NULL,
    total_price     REAL    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Confirmed'
                            CHECK(status IN ('Confirmed', 'Cancelled', 'Completed')),
    booked_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (room_id) REFERENCES RoomDetails(room_id)
);

-- Seed Data: Default Admin user (password: admin123)
INSERT OR IGNORE INTO Users (full_name, email, password, role)
VALUES ('System Admin', 'admin@hbms.com',
        'pbkdf2:sha256:600000$admin$placeholder', 'Admin');

INSERT OR IGNORE INTO Users (full_name, email, password, role)
VALUES ('Jane Employee', 'employee@hbms.com',
        'pbkdf2:sha256:600000$emp$placeholder', 'Employee');
