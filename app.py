
from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hbindu@15",
        database="road_accident_db"
    )

@app.route("/", methods=["GET", "POST"])
def home():
    selected_year = request.values.get("year", "2026")
    data = {}
    weather_data = []
    error = None

    try:
        year = int(selected_year)
        if year < 2011 or year > 2026:
            raise ValueError("Year must be between 2011 and 2026.")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(deaths), 0),
                   COALESCE(SUM(injuries), 0)
            FROM Accidents
            WHERE YEAR(accident_date) = %s
        """, (year,))
        result = cursor.fetchone()

        data = {
            "total": result[0],
            "deaths": result[1],
            "injuries": result[2]
        }

        cursor.execute("""
            SELECT weather, COUNT(*)
            FROM Accidents
            WHERE YEAR(accident_date) = %s
            GROUP BY weather
            ORDER BY COUNT(*) DESC
        """, (year,))
        weather_data = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        error = str(e)

    return render_template(
        "index.html",
        selected_year=selected_year,
        data=data,
        weather_data=weather_data,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True)


