import os
import csv
import io
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
@app.after_request
def prevent_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
app.secret_key = "road-safety-demo-key"

def get_db_connection():
    host = os.environ.get("DB_HOST", "localhost")

    config = {
        "host": host,
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "road_accident_db"),
        "port": int(os.environ.get("DB_PORT", 3306))
    }

    if host != "localhost":
        config["ssl_ca"] = os.path.join(os.path.dirname(__file__), "ca.pem")
        config["ssl_verify_cert"] = True

    return mysql.connector.connect(**config)


@app.route("/")
def home():
    return render_template("landing.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Demo account
        if email == "demo@roadsafety.com" and password == "road123":
            session["logged_in"] = True
            session["user_name"] = name or "Demo User"
            session["user_email"] = email

            return redirect(url_for("dashboard_page"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):
                session["logged_in"] = True
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]

                return redirect(url_for("dashboard_page"))

        finally:
            cursor.close()
            conn.close()

        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill all fields"
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must be at least 8 characters"
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                return render_template(
                    "register.html",
                    error="Email already registered. Please login."
                )

            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (name, email, password_hash)
            )

            conn.commit()

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    name = request.form.get("name")
    email = request.form.get("email")

    session["user_name"] = name
    session["user_email"] = email

    return redirect(url_for("dashboard_page"))
@app.route("/dashboard")
def dashboard_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    response = app.make_response(
        render_template(
            "index.html",
            user_name=session.get("user_name"),
            user_email=session.get("user_email")
        )
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.route("/logout")
def logout():
    session.clear()
    response = redirect(url_for("home"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/api/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    conn = None
    cursor = None

    try:
        year = int(request.args.get("year", ""))

        if year < 2011 or year > 2026:
            return jsonify({
                "error": "Please enter a year between 2011 and 2026."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Yearly summary
        cursor.execute("""
            SELECT
                COUNT(*) AS total_accidents,
                COALESCE(SUM(deaths), 0) AS total_deaths,
                COALESCE(SUM(injuries), 0) AS total_injuries,
                SUM(
                    CASE
                        WHEN location IS NULL
                          OR accident_time IS NULL
                          OR vehicle_type IS NULL
                          OR severity IS NULL
                        THEN 1 ELSE 0
                    END
                ) AS missing_records
            FROM accidents
            WHERE YEAR(accident_date) = %s
        """, (year,))

        summary = cursor.fetchone()

        # 2. Month-wise accident trends
        cursor.execute("""
            SELECT
                MONTHNAME(accident_date) AS month,
                COUNT(*) AS count
            FROM accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY MONTH(accident_date), MONTHNAME(accident_date)
            ORDER BY MONTH(accident_date)
        """, (year,))

        monthly = cursor.fetchall()

        # 3. Accidents by time of day
        cursor.execute("""
            SELECT
                CASE
                    WHEN accident_time IS NULL THEN 'Unknown'
                    WHEN HOUR(accident_time) < 6 THEN 'Night'
                    WHEN HOUR(accident_time) < 12 THEN 'Morning'
                    WHEN HOUR(accident_time) < 18 THEN 'Afternoon'
                    ELSE 'Evening'
                END AS period,
                COUNT(*) AS count
            FROM accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY period
            ORDER BY FIELD(
                period, 'Morning', 'Afternoon',
                'Evening', 'Night', 'Unknown'
            )
        """, (year,))

        time_of_day = cursor.fetchall()

        # 4. Locations with most accidents
        cursor.execute("""
            SELECT
                COALESCE(location, 'Unknown') AS location,
                COUNT(*) AS count
            FROM accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        """, (year,))

        locations = cursor.fetchall()

        # 5. Vehicle type comparison
        cursor.execute("""
            SELECT
                COALESCE(vehicle_type, 'Unknown') AS vehicle_type,
                COUNT(*) AS count
            FROM accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY vehicle_type
            ORDER BY count DESC
        """, (year,))

        vehicle_types = cursor.fetchall()

        # 6. Severity distribution
        cursor.execute("""
            SELECT
                COALESCE(severity, 'Unknown') AS severity,
                COUNT(*) AS count
            FROM accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY severity
            ORDER BY count DESC
        """, (year,))

        severity = cursor.fetchall()

        # 7. Accident records
        cursor.execute("""
            SELECT
                DATE_FORMAT(accident_date, '%Y-%m-%d') AS date,
                TIME_FORMAT(accident_time, '%H:%i') AS time,
                location,
                location AS region,
                road_name,
                vehicle_type,
                severity,
                weather
            FROM accidents
            WHERE YEAR(accident_date) = %s
            ORDER BY accident_date DESC, accident_time DESC
            LIMIT 1000
        """, (year,))

        records = cursor.fetchall()

        # 8. Filter options
        cursor.execute("""
            SELECT DISTINCT severity
            FROM accidents
            WHERE YEAR(accident_date) = %s
              AND severity IS NOT NULL
            ORDER BY severity
        """, (year,))

        severities = [
            row["severity"] for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT DISTINCT vehicle_type
            FROM accidents
            WHERE YEAR(accident_date) = %s
              AND vehicle_type IS NOT NULL
            ORDER BY vehicle_type
        """, (year,))

        vehicles = [
            row["vehicle_type"] for row in cursor.fetchall()
        ]

        return jsonify({
            "year": year,
            "summary": summary,
            "charts": {
                "monthly": monthly,
                "time_of_day": time_of_day,
                "locations": locations,
                "vehicle_types": vehicle_types,
                "severity": severity
            },
            "records": records,
            "filters": {
                "severities": severities,
                "vehicle_types": vehicles
            }
        })

    except ValueError:
        return jsonify({
            "error": "Please enter a valid year between 2011 and 2026."
        }), 400

    except Exception as e:
        app.logger.exception("Dashboard data loading failed")
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route("/download_records")
def download_records():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    year = request.args.get("year", "all")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if year == "all":
            cursor.execute("""
                SELECT accident_date, accident_time, location,
                       road_name, vehicle_type, severity,
                       weather, deaths, injuries
                FROM accidents
                ORDER BY accident_date DESC
            """)
        else:
            try:
                year = int(year)
            except ValueError:
                return "Invalid year", 400

            if year < 2011 or year > 2026:
                return "Year must be between 2011 and 2026", 400

            cursor.execute("""
                SELECT accident_date, accident_time, location,
                       road_name, vehicle_type, severity,
                       weather, deaths, injuries
                FROM accidents
                WHERE YEAR(accident_date) = %s
                ORDER BY accident_date DESC
            """, (year,))

        records = cursor.fetchall()

        output = io.StringIO()

        if records:
            writer = csv.DictWriter(
                output,
                fieldnames=records[0].keys()
            )
            writer.writeheader()
            writer.writerows(records)

        response = make_response(output.getvalue())

        response.headers["Content-Disposition"] = (
            f"attachment; filename=accident_records_{year}.csv"
        )

        response.headers["Content-Type"] = "text/csv; charset=utf-8"

        return response

    except Exception as e:
        return str(e), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=True)
