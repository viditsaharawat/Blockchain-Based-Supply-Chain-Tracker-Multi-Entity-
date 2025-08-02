from flask import Flask, render_template, request, redirect, session, url_for, flash
from blockchain import Blockchain
from roles import CREDENTIALS, ROLES
from utils import generate_qr_code
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'
bc = Blockchain()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]
        if role in CREDENTIALS and username == CREDENTIALS[role]["username"] and password == CREDENTIALS[role]["password"]:
            session["role"] = role
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")
    return render_template("login.html", roles=ROLES)

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", role=session["role"])

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if "role" not in session:
        return redirect(url_for("login"))

    role = session["role"]

    if request.method == "POST":
        product_id = request.form["product_id"]
        details = request.form["description"]

        # Role-specific logic
        if role == "manufacturer":
            description = f"Manufactured Product: {details}"
        elif role == "distributor":
            description = f"Shipped from warehouse or in transit: {details}"
        elif role == "retailer":
            description = f"Received and marked for sale: {details}"
        else:
            description = details  # fallback (shouldn't happen)

        # Add to blockchain
        bc.add_block({
            "product_id": product_id,
            "description": description,
            "by": role
        })

        flash(f"{role.title()} update recorded for Product ID {product_id}.")
        return redirect(url_for("dashboard"))

    return render_template("product_form.html", role=role)

@app.route("/track", methods=["GET", "POST"])
def track():
    if "role" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        pid = request.form["product_id"]
        history = bc.get_product_history(pid)
        qr = generate_qr_code(f"Product ID: {pid}")
        return render_template("view_history.html", history=history, pid=pid, qr=qr)

    return render_template("track_product.html")

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime(format)
    return value

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
