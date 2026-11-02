
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector

app = Flask(__name__)
@app.after_request
def prevent_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
app.secret_key = "road-safety-demo-key"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hbindu@15",
        database="road_accident_db"
    )


@app.route("/")
def home():
    return render_template("landing.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if email == "demo@roadsafety.com" and password == "road123":
            session["logged_in"] = True
            session["user_name"] = name
            session["user_email"] = email

            return redirect(url_for("dashboard_page"))

        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    return render_template("login.html")


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


if __name__ == "__main__":
    app.run(debug=True)
