from flask import Flask, request, render_template_string, send_from_directory
from pathlib import Path
import sys
import pandas as pd
import matplotlib

matplotlib.use("Agg")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from db import connect_db
from dashboard_analysis import generate_charts

app = Flask(__name__)

CHART_DIR = BASE_DIR / "charts"
CHART_DIR.mkdir(exist_ok=True)


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Road Accident Analysis Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            color: #1e293b;
            margin: 0;
        }
        header {
            background: #17365d;
            color: white;
            text-align: center;
            padding: 25px;
        }
        .container {
            max-width: 1150px;
            margin: 25px auto;
            padding: 0 18px;
        }
        .filters, .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px #00000012;
            margin-bottom: 20px;
        }
        .filters form {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: end;
        }
        .filters label {
            display: block;
            margin-bottom: 7px;
            font-weight: bold;
        }
        select, button {
            padding: 10px;
            min-width: 150px;
            border: 1px solid #cbd5e1;
            border-radius: 5px;
        }
        button {
            background: #17365d;
            color: white;
            cursor: pointer;
        }
        .cards, .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 18px;
            margin-top: 20px;
        }
        .number {
            font-size: 32px;
            font-weight: bold;
            color: #17365d;
        }
        .charts img {
            width: 100%;
            height: auto;
        }
        .message {
            background: #fff7ed;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        footer {
            text-align: center;
            padding: 25px;
            color: #64748b;
        }
    </style>
</head>
<body>

<header>
    <h1>Road Accident Data Analysis System</h1>
    <p>Interactive accident statistics and visualization</p>
</header>

<div class="container">

    <section class="filters">
        <h2>Filter Accident Records</h2>
        <form method="GET" action="/">
            <div>
                <label for="year">Year</label>
                <select name="year" id="year">
                    <option value="">All Years</option>
                    {% for y in years %}
                    <option value="{{ y }}" {% if selected_year == y|string %}selected{% endif %}>
                        {{ y }}
                    </option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <label for="severity">Severity</label>
                <select name="severity" id="severity">
                    <option value="">All Severities</option>
                    {% for s in severities %}
                    <option value="{{ s }}" {% if selected_severity == s %}selected{% endif %}>
                        {{ s }}
                    </option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <label for="region">Region</label>
                <select name="region" id="region">
                    <option value="">All Regions</option>
                    {% for r in regions %}
                    <option value="{{ r }}" {% if selected_region == r %}selected{% endif %}>
                        {{ r }}
                    </option>
                    {% endfor %}
                </select>
            </div>

            <button type="submit">Apply Filters</button>
            <a href="/" style="padding: 10px; color: #17365d; text-decoration: none;">Reset</a>
        </form>
    </section>

    {% if error %}
        <div class="message">{{ error }}</div>
    {% else %}

        <h2>Accident Statistics</h2>
        <div class="cards">
            <div class="card">
                <h3>Total Accident Records</h3>
                <div class="number">{{ total }}</div>
            </div>
            <div class="card">
                <h3>Total Deaths</h3>
                <div class="number">{{ deaths }}</div>
            </div>
            <div class="card">
                <h3>Total Injuries</h3>
                <div class="number">{{ injuries }}</div>
            </div>
        </div>

        {% if total > 0 %}
            <h2>Accident Analysis Charts</h2>
            <div class="charts">
                {% for chart in charts %}
                <div class="card">
                    <h3>{{ chart.title }}</h3>
                    <img src="/charts/{{ chart.filename }}" alt="{{ chart.title }}">
                </div>
                {% endfor %}
            </div>

            <h2>Accident Records</h2>
            <div class="card" style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="background: #17365d; color: white;">
                            <th style="padding: 12px;">Accident ID</th>
                            <th style="padding: 12px;">Accident Date</th>
                            <th style="padding: 12px;">Vehicle Type</th>
                            <th style="padding: 12px;">Region</th>
                            <th style="padding: 12px;">Severity</th>
                            <th style="padding: 12px;">Deaths</th>
                            <th style="padding: 12px;">Injuries</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for record in records %}
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px;">{{ record.accident_id }}</td>
                            <td style="padding: 10px;">{{ record.accident_date }}</td>
                            <td style="padding: 10px;">{{ record.vehicle_type }}</td>
                            <td style="padding: 10px;">{{ record.region }}</td>
                            <td style="padding: 10px;">{{ record.severity }}</td>
                            <td style="padding: 10px;">{{ record.deaths }}</td>
                            <td style="padding: 10px;">{{ record.injuries }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                {% if not records %}
                    <p>No accident records match the selected filters.</p>
                {% endif %}

                <p style="margin-top: 15px;">
                    Showing {{ records|length }} records on this page.
                </p>
            </div>

        {% else %}
            <div class="message">
                No accident records match the selected filters.
            </div>
        {% endif %}

    {% endif %}

</div>

<footer>
    Road Accident Data Analysis System
    <br>
    Python | MySQL | Pandas | Matplotlib | Flask
    <br><br>
    This project uses synthetic sample data, not verified real-world accident records.
</footer>

</body>
</html>
"""


@app.route("/")
def dashboard():
    connection = connect_db()
    if connection is None:
        return "MySQL connection failed. Check db.py.", 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        # Retrieve available filter options
        cursor.execute("""
            SELECT DISTINCT YEAR(accident_date) AS year
            FROM accident
            WHERE accident_date IS NOT NULL
            ORDER BY year
        """)
        years = [row["year"] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT severity
            FROM accident
            WHERE severity IS NOT NULL
            ORDER BY severity
        """)
        severities = [row["severity"] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT region
            FROM location
            WHERE region IS NOT NULL
            ORDER BY region
        """)
        regions = [row["region"] for row in cursor.fetchall()]

        # Read filter values from the browser
        selected_year = request.args.get("year", "").strip()
        selected_severity = request.args.get("severity", "").strip()
        selected_region = request.args.get("region", "").strip()

        # Build parameterized SQL query
        sql = """
            SELECT
                a.accident_id,
                a.accident_date,
                a.vehicle_type,
                a.severity,
                a.deaths,
                a.injuries,
                l.region
            FROM accident a
            JOIN location l
              ON a.location_id = l.location_id
            WHERE 1 = 1
        """
        params = []

        if selected_year:
            try:
                year_number = int(selected_year)
                if year_number not in years:
                    raise ValueError
                sql += " AND YEAR(a.accident_date) = %s"
                params.append(year_number)
            except ValueError:
                return render_template_string(
                    HTML,
                    years=years,
                    severities=severities,
                    regions=regions,
                    selected_year="",
                    selected_severity="",
                    selected_region="",
                    error="Please select a valid year.",
                    charts=[],
                    records=[],
                    total=0,
                    deaths=0,
                    injuries=0
                ), 400

        if selected_severity:
            if selected_severity not in severities:
                return "Invalid severity filter.", 400
            sql += " AND a.severity = %s"
            params.append(selected_severity)

        if selected_region:
            if selected_region not in regions:
                return "Invalid region filter.", 400
            sql += " AND l.region = %s"
            params.append(selected_region)

        cursor.execute(sql, tuple(params))
        raw_records = cursor.fetchall()

        # Format records for table display and analysis
        df = pd.DataFrame(raw_records)
        table_records = []

        if not df.empty:
            df_display = df.copy()
            df_display["accident_date"] = (
                pd.to_datetime(df_display["accident_date"], errors="coerce")
                .dt.strftime("%Y-%m-%d")
                .fillna("")
            )
            df_display = df_display.astype(object).where(pd.notna(df_display), "")
            table_records = df_display.to_dict(orient="records")

            df["accident_date"] = pd.to_datetime(df["accident_date"], errors="coerce")
            df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
            df["injuries"] = pd.to_numeric(df["injuries"], errors="coerce").fillna(0)

            total = len(df)
            deaths = int(df["deaths"].sum())
            injuries = int(df["injuries"].sum())

            # Generate charts using filtered data
            generate_charts(df)
        else:
            total = 0
            deaths = 0
            injuries = 0

        charts = [
            {"title": "Accidents by Severity", "filename": "dashboard_severity.png"},
            {"title": "Accidents by Vehicle Type", "filename": "dashboard_vehicle.png"},
            {"title": "Accidents by Year", "filename": "dashboard_year.png"},
            {"title": "Accidents by Region", "filename": "dashboard_region.png"}
        ]

        return render_template_string(
            HTML,
            years=years,
            severities=severities,
            regions=regions,
            selected_year=selected_year,
            selected_severity=selected_severity,
            selected_region=selected_region,
            total=total,
            deaths=deaths,
            injuries=injuries,
            charts=charts,
            records=table_records,
            error=None
        )

    except Exception as error:
        app.logger.exception("Dashboard failed")
        return f"Dashboard error: {error}", 500

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


@app.route("/charts/<path:filename>")
def display_chart(filename):
    allowed_files = {
        "dashboard_severity.png",
        "dashboard_vehicle.png",
        "dashboard_year.png",
        "dashboard_region.png"
    }
    if filename not in allowed_files:
        return "Chart not found.", 404

    return send_from_directory(CHART_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True)