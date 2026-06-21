
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "expense_lens.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads", "receipts")


def get_connection():

    return sqlite3.connect(DB_PATH)

def create_tables():

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


# ---------------- SAVE IMAGE ----------------
def save_image(uploaded_file, user_id="guest"):

    try:
        folder = os.path.join(UPLOAD_FOLDER, user_id)
        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, uploaded_file.name)

        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return path

    except Exception as e:
        print("Image save error:", e)
        return None

def save_receipt(data, image_path=None, user_id="guest"):

    try:

        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute("""
        INSERT INTO receipts
        (user_id, store, date, total, items, notes, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data["store"],
            data["date"],
            data["total"],
            data["items"],
            data.get("notes", ""),
            image_path
        ))


        conn.commit()
        conn.close()


        return True


    except Exception as e:

        print("Receipt save error:", e)

        return False




def get_receipts():

    conn = get_connection()


    rows = conn.execute(
        """
        SELECT *
        FROM receipts
        ORDER BY created_at DESC
        """
    ).fetchall()


    conn.close()


    return rows




def delete_receipt(receipt_id):

    try:

        conn = get_connection()


        conn.execute(
            """
            DELETE FROM receipts
            WHERE id=?
            """,
            (receipt_id,)
        )


        conn.commit()
        conn.close()


        return True


    except Exception as e:

        print(e)

        return False




def save_feedback(rating, comment):

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
