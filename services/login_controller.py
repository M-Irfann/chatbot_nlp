from flask import render_template, request, redirect, session
from connection import connection_db

def login_controller():


    if session.get("is_login"):
        return redirect("/dashboard")


    if request.method == "GET":
        return render_template("pages/login.html")

    email = request.form["email"]
    password = request.form["password"]

    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM users
        WHERE email = %s
        AND password = %s
    """

    values = (email, password)

    cursor.execute(query, values)
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return render_template(
            "pages/login.html",
            error="Email atau password salah"
        )

    session["is_login"] = True
    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["nama"] = user["nama"]

    return redirect("/dashboard")