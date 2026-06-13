import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(fullname, username, email, password, role):

    conn = sqlite3.connect("neurodetect.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO users
        (fullname, username, email, password, role)
        VALUES (?, ?, ?, ?, ?)
        """, (
            fullname,
            username,
            email,
            hash_password(password),
            role
        ))

        conn.commit()
        return True, "Compte créé avec succès"

    except sqlite3.IntegrityError:
        return False, "Email ou username déjà utilisé"

    finally:
        conn.close()