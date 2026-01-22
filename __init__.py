from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------- Authentification ADMIN (déjà utilisée pour /lecture) --------

def est_authentifie():
    return session.get("authentifie")


@app.route("/")
def hello_world():
    return render_template("hello.html")


@app.route("/authentification", methods=["GET", "POST"])
def authentification():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = ? AND password = ? AND role = 'admin'",
            (username, password),
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["authentifie"] = True
            return redirect(url_for("lecture"))
        else:
            error = "Identifiants administrateur incorrects."

    return render_template("formulaire_authentification.html", error=error)


@app.route("/deconnexion_admin")
def deconnexion_admin():
    session.pop("authentifie", None)
    return redirect(url_for("hello_world"))


@app.route("/lecture")
def lecture():
    if not est_authentifie():
        return redirect(url_for("authentification"))
    return "Zone lecture réservée à l'administrateur."


# -------- Authentification USER pour /fiche_nom/ --------

def est_user_connecte():
    return session.get("user_auth")


@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    """
    Authentification pour accéder à /fiche_nom/ (user / 12345)
    """
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "user" and password == "12345":
            session["user_auth"] = True
            return redirect(url_for("fiche_nom"))
        else:
            error = "Identifiants utilisateur invalides (user / 12345)."

    return render_template("formulaire_user.html", error=error)


@app.route("/deconnexion_user")
def deconnexion_user():
    session.pop("user_auth", None)
    return redirect(url_for("hello_world"))


# -------- Exercice 1 + 2 : route /fiche_nom/ protégée --------

@app.route("/fiche_nom/", methods=["GET", "POST"])
def fiche_nom():
    """
    Recherche d'un client par nom (username) dans la table users
    Accès réservé à l'utilisateur simple (user / 12345)
    """
    if not est_user_connecte():
        return redirect(url_for("login_user"))

    client = None
    message = None

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()

        if nom:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username = ? AND role = 'user'",
                (nom,),
            )
            client = cur.fetchone()
            conn.close()

            if not client:
                message = "Aucun client trouvé pour ce nom."
        else:
            message = "Veuillez saisir un nom."

    return render_template("fiche_nom.html", client=client, message=message)

@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    """
    Enregistrement d'un livre dans la table books
    """
    message = None

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()

        if title and author:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO books (title, author, available) VALUES (?, ?, 1)",
                (title, author),
            )
            conn.commit()
            conn.close()
            message = "Livre enregistré avec succès."
        else:
            message = "Le titre et l'auteur sont obligatoires."

    return render_template("add_book.html", message=message)

@app.route("/books")
def list_books():
    """
    Liste tous les livres avec possibilité de suppression
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books ORDER BY id")
    books = cur.fetchall()
    conn.close()
    return render_template("read_data.html", books=books)


@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """
    Suppression d'un livre
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("list_books"))

@app.route("/books/search", methods=["GET", "POST"])
def search_books():
    """
    Recherche de livres disponibles (available = 1)
    par titre ou auteur (contient le texte saisi)
    """
    results = []
    query = ""
    message = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if query:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM books
                WHERE available = 1
                  AND (title LIKE ? OR author LIKE ?)
                ORDER BY title
                """,
                (f"%{query}%", f"%{query}%"),
            )
            results = cur.fetchall()
            conn.close()

            if not results:
                message = "Aucun livre disponible ne correspond à cette recherche."
        else:
            message = "Veuillez saisir un texte de recherche."

    return render_template(
        "search_books.html",
        query=query,
        results=results,
        message=message,
    )




# -------- Exemple : autres routes déjà présentes (si tu en as) --------
# Ici, tu peux garder tes routes existantes pour ajouter livres, lire données, etc.


# -------- Lancement local --------

if __name__ == "__main__":
    app.run(debug=True)
