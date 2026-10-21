
import pandas as pd
import mysql.connector

df = pd.read_csv("synthetic_accidents.csv")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Hbindu@15",
    database="road_accident_db"
)

cursor = conn.cursor()

try:
    cursor.execute("""
        SELECT accident_id
        FROM Accidents
        ORDER BY accident_id
    """)
    accident_ids = [row[0] for row in cursor.fetchall()]

    if len(accident_ids) != len(df):
        raise ValueError(
            f"Count mismatch: DB={len(accident_ids)}, CSV={len(df)}"
        )

    updates = [
        (str(row["weather"]).strip(), accident_id)
        for accident_id, (_, row) in zip(accident_ids, df.iterrows())
    ]

    cursor.executemany(
        "UPDATE Accidents SET weather = %s WHERE accident_id = %s",
        updates
    )

    conn.commit()
    print("Weather update successful!")
    print("Records updated:", len(updates))

except Exception as e:
    conn.rollback()
    print("Update failed:", e)

finally:
    cursor.close()
    conn.close()

