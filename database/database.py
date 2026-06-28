# module to make and control the database
import sqlite3
import os
from utils.encryption import encrypt, decrypt
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
    make tables in dtbs
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        store TEXT,
        date TEXT,
        total REAL,
        items TEXT,
        notes TEXT,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_image(image_input, user_id):
    """
    save image
    """
    import os
    from PIL import Image
    import io

    if isinstance(image_input, str):
        # already a file path
        return image_input

    # Streamlit UploadedFile
    filename = image_input.name

    save_path = os.path.join("uploads", user_id)
    os.makedirs(save_path, exist_ok=True)

    full_path = os.path.join(save_path, filename)

    image = Image.open(image_input)
    image.save(full_path)

    return full_path

def save_receipt(data, image_path=None, user_id="guest"):
    """
    save a receipt with encrypted sensitive fields
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO receipts
        (user_id, store, date, total, items, notes, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            encrypt(data["store"]),
            encrypt(data["date"]),
            encrypt(str(data["total"])),
            encrypt(json.dumps(data["items"])),
            encrypt(data.get("notes", "")),
            image_path
        ))
        conn.commit()
        conn.close()
        return True
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
                row[8]                  # created_at
            )
        )

    return decrypted_rows




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
