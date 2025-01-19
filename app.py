from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import platform
import psutil
import os

app = Flask(__name__)

# Database configuration
DB_ENABLED = os.getenv("DB_ENABLED", "true").lower() == "true"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///:memory:"  # Use SQLite for fallback
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app) if DB_ENABLED else None

# In-memory storage for fallback
users = []

class User(db.Model if DB_ENABLED else object):
    """User model for MySQL database."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) if DB_ENABLED else None
    name = db.Column(db.String(100), nullable=False) if DB_ENABLED else None
    contact = db.Column(db.String(20), nullable=False) if DB_ENABLED else None

    def __init__(self, name, contact):
        self.name = name
        self.contact = contact

    def __repr__(self):
        return f"<User {self.name}>"

if DB_ENABLED:
    with app.app_context():
        db.create_all()  # Create tables

background_color = "white"

def get_memory_status():
    memory = psutil.virtual_memory()
    memory_percentage = memory.percent
    health_status = "Healthy" if memory_percentage < 70 else "Unhealthy"
    return memory_percentage, health_status

@app.route("/", methods=["GET", "POST"])
def home():
    global background_color

    if request.method == "POST":
        if "name" in request.form and "contact" in request.form:
            name = request.form.get("name").strip()
            contact = request.form.get("contact").strip()
            if name and contact:
                if DB_ENABLED:
                    new_user = User(name=name, contact=contact)
                    db.session.add(new_user)
                    db.session.commit()
                else:
                    users.append({"name": name, "contact": contact})

        if "color" in request.form:
            background_color = request.form.get("color")

    if DB_ENABLED:
        user_data = User.query.all()
    else:
        user_data = users

    hostname = platform.node()
    memory_percentage, health_status = get_memory_status()
    return render_template(
        "index.html",
        hostname=hostname,
        memory_percentage=memory_percentage,
        health_status=health_status,
        background_color=background_color,
        users=user_data,
    )

@app.route("/health")
def health():
    _, health_status = get_memory_status()
    return jsonify({"status": health_status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
