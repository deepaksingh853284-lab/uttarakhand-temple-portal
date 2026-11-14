import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, g, redirect, render_template, request,
    session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "temples.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-this-development-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

SEED_TEMPLES = [
    ("Kedarnath Temple", "Rudraprayag", "Shiva", "Char Dham · Panch Kedar",
     "One of the most revered Shiva temples, set in the Garhwal Himalayas.",
     "Kedarnath is a major pilgrimage destination surrounded by high Himalayan peaks. The temple is traditionally associated with the Pandavas and Lord Shiva.",
     "May–October (seasonal; confirm before travel)", "Gaurikund, followed by a trek",
     "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=1200&q=85"),
    ("Badrinath Temple", "Chamoli", "Vishnu", "Char Dham",
     "A prominent Vishnu shrine on the banks of the Alaknanda River.",
     "Badrinath is one of the Char Dham pilgrimage sites. The colorful temple stands in the Himalayan town of Badrinath.",
     "Seasonal; check the official opening announcement", "Road access to Badrinath town",
     "https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=85"),
    ("Gangotri Temple", "Uttarkashi", "Ganga", "Char Dham",
     "A sacred temple associated with the origin of the River Ganga.",
     "Gangotri is an important pilgrimage site in the upper Bhagirathi valley. The surrounding area has mountain scenery and a strong religious tradition.",
     "Seasonal; check local updates before travelling", "Road access from Uttarkashi region",
     "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=85"),
    ("Yamunotri Temple", "Uttarkashi", "Goddess Yamuna", "Char Dham",
     "A Himalayan shrine dedicated to Goddess Yamuna.",
     "Yamunotri marks the traditional pilgrimage source region of the Yamuna. Visitors usually reach the trailhead at Janki Chatti and continue on foot.",
     "Seasonal; confirm weather and route conditions", "Janki Chatti, followed by a trek",
     "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=85"),
    ("Jageshwar Dham", "Almora", "Shiva", "Heritage",
     "A historic group of stone temples set among deodar trees.",
     "Jageshwar is known for its cluster of ancient stone temples and peaceful forest setting. It is an important heritage and pilgrimage destination in Kumaon.",
     "Check local temple timings before visiting", "Road access from Almora",
     "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=1200&q=85"),
    ("Neelkanth Mahadev Temple", "Pauri Garhwal", "Shiva", "Pilgrimage",
     "A well-known Shiva temple in the forested hills near Rishikesh.",
     "Neelkanth Mahadev is a popular pilgrimage destination in the hills near Rishikesh, associated with the legend of Shiva drinking the halahala poison.",
     "Check local timings and road conditions", "Road route from Rishikesh; verify current access",
     "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=85"),
    ("Chitai Golu Devta Temple", "Almora", "Golu Devta", "Kumaon",
     "A distinctive temple famous for bells and written petitions.",
     "Devotees visit Chitai Golu Devta Temple to offer prayers and petitions. Its many bells make it a recognizable landmark near Almora.",
     "Check locally for current timings", "Road access from Almora",
     "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?auto=format&fit=crop&w=1200&q=85"),
    ("Mansa Devi Temple", "Haridwar", "Goddess Mansa Devi", "Shakti Peeth tradition",
     "A hilltop temple overlooking Haridwar and the Ganges plain.",
     "Mansa Devi is one of Haridwar's best-known temples. Visitors can walk up or use the ropeway when operating.",
     "Confirm ropeway and temple timings locally", "Haridwar; walking route or ropeway when available",
     "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=85"),
    ("Tungnath Temple", "Rudraprayag", "Shiva", "Panch Kedar",
     "A high-altitude Shiva temple reached by a mountain trail.",
     "Tungnath is part of the Panch Kedar tradition. The trek offers broad Himalayan views, but weather and altitude should be considered carefully.",
     "Seasonal; verify trail and weather conditions", "Chopta, followed by a trek",
     "https://images.unsplash.com/photo-1464278533981-50106e6176b1?auto=format&fit=crop&w=1200&q=85"),
    ("Patal Bhuvaneshwar", "Pithoragarh", "Shiva", "Cave shrine",
     "A limestone cave shrine with religious and geological significance.",
     "Patal Bhuvaneshwar is known for its cave formations and sacred associations. Follow local guidance and safety instructions when visiting.",
     "Confirm access and visiting rules locally", "Road access in the Gangolihat region",
     "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1200&q=85"),
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""
        CREATE TABLE IF NOT EXISTS temples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            deity TEXT NOT NULL,
            category TEXT NOT NULL,
            short_description TEXT NOT NULL,
            history TEXT NOT NULL,
            timings TEXT NOT NULL,
            how_to_reach TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    count = db.execute("SELECT COUNT(*) FROM temples").fetchone()[0]
    if count == 0:
        db.executemany("""
            INSERT INTO temples
            (name, district, deity, category, short_description, history, timings, how_to_reach, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, SEED_TEMPLES)
    admin = db.execute("SELECT id FROM admins WHERE username = ?", ("admin",)).fetchone()
    if not admin:
        # Change the default password after first login.
        password = os.environ.get("TEMPLE_ADMIN_PASSWORD", "ChangeMe123!")
        db.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                   ("admin", generate_password_hash(password)))
    db.commit()
    db.close()

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to access the admin panel.", "warning")
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    db = get_db()
    featured = db.execute("SELECT * FROM temples ORDER BY id LIMIT 6").fetchall()
    total = db.execute("SELECT COUNT(*) FROM temples").fetchone()[0]
    districts = db.execute("SELECT COUNT(DISTINCT district) FROM temples").fetchone()[0]
    return render_template("index.html", featured=featured, total=total, districts=districts)


def temples():
    db = get_db()
    q = request.args.get("q", "").strip()
    district = request.args.get("district", "").strip()
    districts = db.execute("SELECT DISTINCT district FROM temples ORDER BY district").fetchall()
    sql = "SELECT * FROM temples WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR deity LIKE ? OR district LIKE ? OR category LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern])
    if district:
        sql += " AND district = ?"
        params.append(district)
    sql += " ORDER BY name"
    results = db.execute(sql, params).fetchall()
    return render_template("temples.html", temples=results, districts=districts, q=q, selected_district=district)

@app.route("/temple/<int:temple_id>")
def temple_detail(temple_id):
    temple = get_db().execute("SELECT * FROM temples WHERE id = ?", (temple_id,)).fetchone()
    if temple is None:
        abort(404)
    return render_template("temple_detail.html", temple=temple)
@app.route("/char-dham")
def char_dham():
    return render_template("char_dham.html")
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill in every field.", "danger")
        else:
            # Demo project: no email is sent; the message is acknowledged only.
            flash("Thank you! This demo form received your message locally.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = get_db().execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin"))
        flash("Invalid username or password.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    rows = get_db().execute("SELECT * FROM temples ORDER BY name").fetchall()
    return render_template("admin.html", temples=rows, edit_temple=None)

def form_temple_values():
    fields = ["name", "district", "deity", "category", "short_description", "history", "timings", "how_to_reach", "image_url"]
    values = [request.form.get(field, "").strip() for field in fields]
    if not all(values):
        return None
    return values

@app.route("/admin/add", methods=["POST"])
@admin_required
def add_temple():
    values = form_temple_values()
    if values is None:
        flash("Please complete all temple fields.", "danger")
    else:
        get_db().execute("""
            INSERT INTO temples (name, district, deity, category, short_description, history, timings, how_to_reach, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        get_db().commit()
        flash("Temple added successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/edit/<int:temple_id>", methods=["GET", "POST"])
@admin_required
def edit_temple(temple_id):
    db = get_db()
    temple = db.execute("SELECT * FROM temples WHERE id = ?", (temple_id,)).fetchone()
    if temple is None:
        abort(404)
    if request.method == "POST":
        values = form_temple_values()
        if values is None:
            flash("Please complete all temple fields.", "danger")
        else:
            db.execute("""
                UPDATE temples SET name=?, district=?, deity=?, category=?, short_description=?,
                history=?, timings=?, how_to_reach=?, image_url=? WHERE id=?
            """, (*values, temple_id))
            db.commit()
            flash("Temple updated successfully.", "success")
            return redirect(url_for("admin"))
    return render_template("admin.html", temples=db.execute("SELECT * FROM temples ORDER BY name").fetchall(), edit_temple=temple)

@app.route("/admin/delete/<int:temple_id>", methods=["POST"])
@admin_required
def delete_temple(temple_id):
    db = get_db()
    db.execute("DELETE FROM temples WHERE id = ?", (temple_id,))
    db.commit()
    flash("Temple deleted.", "success")
    return redirect(url_for("admin"))

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
