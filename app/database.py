"""
database.py  —  NeuroDetect SQLite layer
=========================================
Tables:
  users       — compte commun (identifiant, email, password_hash, salt, role)
  medecins    — infos spécifiques médecin
  etudiants   — infos spécifiques étudiant
  patients    — infos spécifiques patient
  analyses    — historique des analyses IRM (lié à users)
"""

import sqlite3
import hashlib
import os
import secrets
import re
from datetime import datetime
from pathlib import Path


# ══════════════════════════════════════════════
#  CHEMIN DB
# ══════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent.parent   # app/../  →  racine du projet
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH  = DATA_DIR / "neurodetect.db"


# ══════════════════════════════════════════════
#  HASH  (SHA-256 + salt aléatoire 32 bytes)
# ══════════════════════════════════════════════
def _generate_salt() -> str:
    """Génère un salt aléatoire unique (hex, 64 chars)."""
    return secrets.token_hex(32)


def _hash_password(password: str, salt: str) -> str:
    """SHA-256(password + salt) — retourne un hex string."""
    combined = (password + salt).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Vérifie si le mot de passe correspond au hash stocké."""
    return _hash_password(password, salt) == stored_hash


# ══════════════════════════════════════════════
#  CONNEXION
# ══════════════════════════════════════════════
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row          # accès par nom de colonne
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ══════════════════════════════════════════════
#  INITIALISATION DES TABLES
# ══════════════════════════════════════════════
def init_db():
    """Crée les tables si elles n'existent pas encore."""
    with _get_connection() as conn:
        conn.executescript("""
        -- ── TABLE USERS ──────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname      TEXT    NOT NULL,
            username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK(role IN ('Médecin','Étudiant','Patient')),
            created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            last_login    TEXT
        );

        -- ── TABLE MÉDECINS ───────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS medecins (
            id            INTEGER PRIMARY KEY,
            user_id       INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            specialite    TEXT,
            hopital       TEXT,
            experience    TEXT
        );

        -- ── TABLE ÉTUDIANTS ──────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS etudiants (
            id            INTEGER PRIMARY KEY,
            user_id       INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            type_ecole    TEXT,
            etablissement TEXT,
            filiere       TEXT,
            annee_etude   TEXT,
            cne           TEXT
        );

        -- ── TABLE PATIENTS ───────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS patients (
            id            INTEGER PRIMARY KEY,
            user_id       INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            age           TEXT,
            sexe          TEXT,
            ville         TEXT,
            groupe_sanguin TEXT,
            medecin_referent TEXT,
            statut_medical   TEXT
        );

        -- ── TABLE ANALYSES IRM ───────────────────────────────────────
        CREATE TABLE IF NOT EXISTS analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            medecin_id    INTEGER REFERENCES users(id),
            patient_nom   TEXT,
            patient_age   TEXT,
            date_analyse  TEXT    NOT NULL DEFAULT (datetime('now')),
            resultat      TEXT,
            type_tumeur   TEXT,
            localisation  TEXT,
            taille        TEXT,
            grade         TEXT,
            confiance     REAL,
            image_path    TEXT
        );
        """)
    print(f"[DB] Initialisee: {DB_PATH}")


# ══════════════════════════════════════════════
#  VALIDATION
# ══════════════════════════════════════════════
def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _validate_password(password: str) -> tuple[bool, str]:
    """
    Règles :
      - min 8 caractères
      - au moins 1 majuscule
      - au moins 1 chiffre
      - au moins 1 caractère spécial
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, ""


# ══════════════════════════════════════════════
#  REGISTER
# ══════════════════════════════════════════════
def register_user(
    fullname:  str,
    username:  str,
    email:     str,
    password:  str,
    confirm:   str,
    role:      str,
    extra:     dict = None
) -> tuple[bool, str]:
    """
    Inscrit un nouvel utilisateur.
    Retourne (True, "") en cas de succès,
             (False, message_erreur) sinon.
    extra = dict avec les champs spécifiques au rôle.
    """

    # ── validations de base ──
    if not fullname.strip():
        return False, "Le nom complet est obligatoire."
    if not username.strip():
        return False, "L'identifiant est obligatoire."
    if len(username.strip()) < 3:
        return False, "L'identifiant doit contenir au moins 3 caractères."
    if not _validate_email(email.strip()):
        return False, "Adresse e-mail invalide."
    if password != confirm:
        return False, "Les mots de passe ne correspondent pas."

    pwd_ok, pwd_msg = _validate_password(password)
    if not pwd_ok:
        return False, pwd_msg

    if role not in ("Médecin", "Étudiant", "Patient"):
        return False, "Rôle invalide."

    # ── hash du mot de passe ──
    salt          = _generate_salt()
    password_hash = _hash_password(password, salt)

    try:
        with _get_connection() as conn:
            # insérer dans users
            cursor = conn.execute("""
                INSERT INTO users
                    (fullname, username, email, password_hash, salt, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fullname.strip(),
                username.strip().lower(),
                email.strip().lower(),
                password_hash,
                salt,
                role
            ))
            user_id = cursor.lastrowid

            # insérer dans la table spécifique au rôle
            extra = extra or {}
            if role == "Médecin":
                conn.execute("""
                    INSERT INTO medecins
                        (user_id, specialite, hopital, experience)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    extra.get("specialite", ""),
                    extra.get("hopital",    ""),
                    extra.get("experience", ""),
                ))

            elif role == "Étudiant":
                conn.execute("""
                    INSERT INTO etudiants
                        (user_id, type_ecole, etablissement,
                         filiere, annee_etude, cne)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    extra.get("type_ecole",    ""),
                    extra.get("etablissement", ""),
                    extra.get("filiere",       ""),
                    extra.get("annee_etude",   ""),
                    extra.get("cne",           ""),
                ))

            elif role == "Patient":
                conn.execute("""
                    INSERT INTO patients
                        (user_id, age, sexe, ville,
                         groupe_sanguin, medecin_referent, statut_medical)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    extra.get("age",              ""),
                    extra.get("sexe",             ""),
                    extra.get("ville",            ""),
                    extra.get("groupe_sanguin",   ""),
                    extra.get("medecin_referent", ""),
                    extra.get("statut_medical",   ""),
                ))

        return True, ""

    except sqlite3.IntegrityError as e:
        err = str(e)
        if "username" in err:
            return False, "Cet identifiant est déjà utilisé."
        if "email" in err:
            return False, "Cette adresse e-mail est déjà utilisée."
        return False, f"Erreur d'inscription : {err}"
    except Exception as e:
        return False, f"Erreur inattendue : {e}"


# ══════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════
def login_user(identifier: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Connecte un utilisateur par username OU email.
    Retourne:
      (True,  "",        user_dict)   — succès
      (False, "message", None)        — échec
    user_dict contient toutes les colonnes de users + les infos du rôle.
    """
    if not identifier.strip() or not password:
        return False, "Veuillez remplir tous les champs.", None

    try:
        with _get_connection() as conn:
            # chercher par username ou email
            row = conn.execute("""
                SELECT * FROM users
                WHERE username = ? OR email = ?
                LIMIT 1
            """, (
                identifier.strip().lower(),
                identifier.strip().lower()
            )).fetchone()

            if row is None:
                return False, "Identifiant ou mot de passe incorrect.", None

            # vérifier le mot de passe
            if not verify_password(password, row["salt"], row["password_hash"]):
                return False, "Identifiant ou mot de passe incorrect.", None

            # mettre à jour last_login
            conn.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now().isoformat(), row["id"]))

            # construire user_dict
            user = dict(row)

            # ajouter les infos du rôle
            role = row["role"]
            if role == "Médecin":
                extra = conn.execute(
                    "SELECT * FROM medecins WHERE user_id = ?", (row["id"],)
                ).fetchone()
            elif role == "Étudiant":
                extra = conn.execute(
                    "SELECT * FROM etudiants WHERE user_id = ?", (row["id"],)
                ).fetchone()
            elif role == "Patient":
                extra = conn.execute(
                    "SELECT * FROM patients WHERE user_id = ?", (row["id"],)
                ).fetchone()
            else:
                extra = None

            if extra:
                extra_dict = dict(extra)
                extra_dict.pop('id', None) 
                user.update(extra_dict)

            return True, "", user

    except Exception as e:
        return False, f"Erreur de connexion : {e}", None


# ══════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════
def get_user_by_id(user_id: int) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def username_exists(username: str) -> bool:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username.strip().lower(),)
        ).fetchone()
        return row is not None


def email_exists(email: str) -> bool:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return row is not None


def save_analyse(medecin_id: int, data: dict) -> int:
    """Sauvegarde une analyse IRM dans la DB. Retourne l'id de l'analyse."""
    with _get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO analyses
                (medecin_id, patient_nom, patient_age, resultat,
                 type_tumeur, localisation, taille, grade,
                 confiance, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            medecin_id,
            data.get("patient_nom",  ""),
            data.get("patient_age",  ""),
            data.get("resultat",     ""),
            data.get("type_tumeur",  ""),
            data.get("localisation", ""),
            data.get("taille",       ""),
            data.get("grade",        ""),
            data.get("confiance",    0.0),
            data.get("image_path",   ""),
        ))
        return cursor.lastrowid


def get_analyses_by_medecin(medecin_id: int) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM analyses
            WHERE medecin_id = ?
            ORDER BY date_analyse DESC
        """, (medecin_id,)).fetchall()
        return [dict(r) for r in rows]


# ══════════════════════════════════════════════
#  AUTO-INIT à l'import
# ══════════════════════════════════════════════
init_db()