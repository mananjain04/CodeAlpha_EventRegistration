import os
import sqlite3

# Database file ka path
DB_PATH = os.path.join(os.path.dirname(__file__), "events.db")


def get_db_connection():
    """SQLite database se connection banata hai."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Events aur Registrations tables banata hai."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Events Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Registrations Table (Linked with events via event_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_email TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE,
            UNIQUE(event_id, user_email)
        );
    """)

    # 3. Sample Events
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO events (title, description, date, location, capacity)
            VALUES 
            ('AI & Web Innovation Summit', 'Explore generative AI and modern web architectures.', '2026-10-15', 'Convention Hall A', 50),
            ('Full-Stack Python Bootcamp', 'Deep dive into Flask, APIs and SQLite databases.', '2026-10-22', 'Online Zoom', 30),
            ('CodeAlpha Hackathon 2026', '24-hour national hackathon for top developers.', '2026-11-05', 'Main Auditorium', 100);
        """)

    conn.commit()
    conn.close()


# ---------------- DATABASE HELPER FUNCTIONS ---------------- #


def get_all_events():
    """Saare events fetch karta hai aur seats_left calculate karta hai."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, 
               (e.capacity - COUNT(r.id)) AS seats_left,
               COUNT(r.id) AS registered_count
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
        GROUP BY e.id
        ORDER BY e.date ASC;
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_event_by_id(event_id):
    """Kisi specific event ki details nikaalta hai."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def register_user(event_id, user_name, user_email):
    """User ko event mein register karta hai."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Capacity check karo
    cursor.execute(
        "SELECT capacity, (SELECT COUNT(*) FROM registrations WHERE event_id = ?) as booked FROM events WHERE id = ?",
        (event_id, event_id),
    )
    event = cursor.fetchone()
    if not event:
        conn.close()
        return False, "Event not found"

    if event["booked"] >= event["capacity"]:
        conn.close()
        return False, "Sorry, this event is already full!"

    # Registration insert karo
    try:
        cursor.execute(
            "INSERT INTO registrations (event_id, user_name, user_email) VALUES (?, ?, ?)",
            (event_id, user_name, user_email),
        )
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "You have already registered for this event!"


def get_user_registrations(user_email):
    """User ke booked events fetch karta hai (Using SQL JOIN)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.id AS reg_id, r.user_name, r.user_email, r.registered_at,
               e.id AS event_id, e.title, e.date, e.location
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.user_email = ?
        ORDER BY r.registered_at DESC;
    """,
        (user_email,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def cancel_registration(reg_id):
    """Registration cancel (DELETE) karta hai."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registrations WHERE id = ?", (reg_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


if __name__ == "__main__":
    init_db()
    print("Database ready!")