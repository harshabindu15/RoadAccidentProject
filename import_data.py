import pandas as pd
import mysql.connector
import os
# Read the CSV file
df = pd.read_csv("synthetic_accidents.csv")

required_columns = [
    "accident_date", "accident_time", "state", "location",
    "vehicle_type", "severity", "deaths", "injuries", "weather"
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"CSV lo missing columns: {missing}")

conn = None
cursor = None

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ["DB_PASSWORD"],
        database="road_accident_db"
    )
    cursor = conn.cursor()

    # Clear old rows in the correct foreign-key order.
    # Keep the backup tables untouched.
    conn.start_transaction()
    cursor.execute("DELETE FROM Accidents")
    cursor.execute("DELETE FROM Locations")

    # Create unique locations and map them to their IDs.
    location_map = {}

    for _, row in df.iterrows():
        region = row["state"]
        road_name = row["location"]
        key = (region, road_name)

        if key not in location_map:
            cursor.execute(
                """
                INSERT INTO Locations (region, road_name)
                VALUES (%s, %s)
                """,
                (region, road_name)
            )
            location_map[key] = cursor.lastrowid

    # Insert accident records, including weather.
    for _, row in df.iterrows():
        key = (row["state"], row["location"])
        location_id = location_map[key]

        cursor.execute(
            """
            INSERT INTO Accidents
            (
                accident_date, accident_time, location,
                location_id, vehicle_type, severity,
                deaths, injuries, weather
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pd.to_datetime(row["accident_date"]).date(),
                row["accident_time"],
                row["location"],
                location_id,
                row["vehicle_type"],
                row["severity"],
                int(row["deaths"]),
                int(row["injuries"]),
                row["weather"]
            )
        )

    conn.commit()
    print("Import successful!")
    print("Accidents imported:", len(df))
    print("Locations imported:", len(location_map))
    print("Weather values imported:", df["weather"].nunique())

except Exception as e:
    if conn is not None:
        conn.rollback()
    print("Import failed:", e)

finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()

