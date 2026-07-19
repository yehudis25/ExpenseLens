# module to make and control the database
import sqlite3
import os
from utils.encryption import encrypt, decrypt, encrypt_bytes
import json

# for each seperate user
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(PROJECT_DIR, "expense_lens.db")
# folder for receipts
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, "uploads", "receipts")

# connect to dtbs
def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    """
    Create all database tables and update older databases if needed.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                store TEXT,
                date TEXT,
                total REAL,
                items TEXT,
                notes TEXT,
                image_path TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(receipts)"
            ).fetchall()
        }

        if "category" not in columns:
            cursor.execute(
                "ALTER TABLE receipts ADD COLUMN category TEXT"
            )

            cursor.execute(
                "UPDATE receipts SET category=? WHERE category IS NULL",
                (encrypt("Other"),)
            )

        conn.commit()

    finally:
        conn.close()


def save_image(image_input, user_id):
    """
    Save an encrypted receipt image and return its file path.
    """

    if isinstance(image_input, str):
        # already a file path
        return image_input

    # Streamlit UploadedFile
    filename = os.path.splitext(image_input.name)[0] + ".enc"

    save_path = os.path.join(
        UPLOAD_FOLDER,
        str(user_id)
    )
    os.makedirs(save_path, exist_ok=True)

    full_path = os.path.join(save_path, filename)

    # Read the uploaded image as bytes
    image_bytes = image_input.read()

    # Encrypt the bytes
    encrypted_bytes = encrypt_bytes(image_bytes)

     # Save encrypted file
    with open(full_path, "wb") as f:
        f.write(encrypted_bytes)

    return full_path

def save_receipt(data, image_path=None, user_id=None):
    """
    save a receipt with encrypted sensitive fields
    """
    if user_id is None:
        raise ValueError("User must be logged in")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO receipts
            (user_id, store, date, total, items, notes, image_path, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            (
                user_id,
                encrypt(data["store"]),
                encrypt(data["date"]),
                encrypt(str(data["total"])),
                encrypt(json.dumps(data["items"])),
                encrypt(data.get("notes", "")),
                image_path,
                encrypt(data.get("category", "Other")),
            ),
        )
        conn.commit()
        receipt_id = cursor.lastrowid  # get new row ID
        conn.close()
        return receipt_id
    except Exception as e:
        print("Receipt save error:", e)
        return False


def get_receipts(user_id=None):
    """
    get receipts and decrypt sensitive fields
    """
    conn = get_connection()
    if user_id:
        rows = conn.execute(
            """
            SELECT *
            FROM receipts
            WHERE user_id=?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM receipts
            ORDER BY created_at DESC
            """
        ).fetchall()
    conn.close()
    # decrypt the data
    decrypted_rows = []
    
    for row in rows:
        raw_category = row[9]

        if raw_category:
            try:
                category = decrypt(raw_category)
            except Exception:
                category = "Other"
        else:
            category = "Other"

        decrypted_rows.append(
            (
                row[0],                 # id
                row[1],                 # user_id
                decrypt(row[2]),        # store
                decrypt(row[3]),        # date
                float(decrypt(row[4])), # total
                json.loads(decrypt(row[5])),        # items
                decrypt(row[6]),        # notes
                row[7],                 # image_path
                category,        # category
                row[9]                  # created_at
            )
        )

    return decrypted_rows

# budget
def get_user_budget(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT budget FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else 500.0

def update_user_budget(user_id, new_budget):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET budget=? WHERE id=?",
        (new_budget, user_id)
    )
    conn.commit()
    conn.close()


def delete_receipt(receipt_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT image_path FROM receipts WHERE id=?", (receipt_id,))
        row = cursor.fetchone()

        if row and row[0]:
            try:
                os.remove(row[0])
            except:
                pass

        cursor.execute("DELETE FROM receipts WHERE id=?", (receipt_id,))
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(e)
        return False




def save_feedback(rating, comment):
    """
    save ratings and feedback
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO feedback
        (rating, comment)

        VALUES (?,?)
        """,
        (
            rating,
            comment
        )
    )

    conn.commit()
    conn.close()
