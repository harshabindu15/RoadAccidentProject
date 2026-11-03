import pandas as pd
from db import connect_db

# Excel file path
file_path = "dataset/road_accident_two_tables_sample_2011_to_2026.xlsx"


def import_data():
    connection = None
    cursor = None

    try:
        # ----------------------------------
        # STEP 1: Read Excel sheets
        # ----------------------------------
        locations = pd.read_excel(
            file_path,
            sheet_name="Location Table"
        )

        accidents = pd.read_excel(
            file_path,
            sheet_name="Accident Table"
        )

        print("Excel file loaded successfully!")
        print("Location records:", len(locations))
        print("Accident records:", len(accidents))

        # ----------------------------------
        # STEP 2: Validate required columns
        # ----------------------------------
        location_columns = [
            "Location ID",
            "Region",
            "Road Name"
        ]

        accident_columns = [
            "Accident ID",
            "Accident Date",
            "Accident Time",
            "Location ID",
            "Vehicle Type",
            "Severity",
            "Deaths",
            "Injuries",
            "Weather"
        ]

        if not set(location_columns).issubset(locations.columns):
            raise ValueError(
                "Location Table is missing required columns."
            )

        if not set(accident_columns).issubset(accidents.columns):
            raise ValueError(
                "Accident Table is missing required columns."
            )

        # ----------------------------------
        # STEP 3: Clean and prepare data
        # ----------------------------------

        # Convert dates safely
        accidents["Accident Date"] = pd.to_datetime(
            accidents["Accident Date"],
            errors="raise"
        ).dt.date

        # Convert times safely
        def convert_time(value):
            if pd.isna(value):
                return None

            if hasattr(value, "strftime"):
                return value.strftime("%H:%M:%S")

            return pd.to_datetime(
                str(value),
                errors="raise"
            ).strftime("%H:%M:%S")

        accidents["Accident Time"] = (
            accidents["Accident Time"].apply(convert_time)
        )

        # Ensure numeric fields are valid
        for column in ["Deaths", "Injuries"]:
            accidents[column] = pd.to_numeric(
                accidents[column],
                errors="raise"
            )

            if accidents[column].isna().any():
                raise ValueError(
                    f"Missing values found in {column}."
                )

            if (accidents[column] < 0).any():
                raise ValueError(
                    f"Negative values found in {column}."
                )

            if (
                accidents[column] % 1 != 0
            ).any():
                raise ValueError(
                    f"Non-integer values found in {column}."
                )

            accidents[column] = accidents[column].astype(int)

        # Check duplicate IDs in the input
        if locations["Location ID"].duplicated().any():
            raise ValueError(
                "Duplicate Location IDs found in Excel."
            )

        if accidents["Accident ID"].duplicated().any():
            raise ValueError(
                "Duplicate Accident IDs found in Excel."
            )

        # ----------------------------------
        # STEP 4: Connect to MySQL
        # ----------------------------------
        connection = connect_db()

        if connection is None:
            raise RuntimeError(
                "Could not connect to MySQL."
            )

        cursor = connection.cursor()

        # Check whether tables already contain data.
        # This prevents accidental duplicate imports.
        cursor.execute("SELECT COUNT(*) FROM location")
        existing_locations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM accident")
        existing_accidents = cursor.fetchone()[0]

        if existing_locations > 0 or existing_accidents > 0:
            raise RuntimeError(
                "Import stopped: one or both tables already "
                "contain records. Check the tables before retrying."
            )

        # ----------------------------------
        # STEP 5: Insert Location records
        # ----------------------------------
        location_sql = """
            INSERT INTO location
                (location_id, region, road_name)
            VALUES (%s, %s, %s)
        """

        location_data = [
            (
                str(row["Location ID"]),
                str(row["Region"]),
                str(row["Road Name"])
            )
            for _, row in locations.iterrows()
        ]

        cursor.executemany(
            location_sql,
            location_data
        )

        print("Locations inserted:", cursor.rowcount)

        # ----------------------------------
        # STEP 6: Insert Accident records
        # ----------------------------------
        accident_sql = """
            INSERT INTO accident (
                accident_id,
                accident_date,
                accident_time,
                location_id,
                vehicle_type,
                severity,
                deaths,
                injuries,
                weather
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        accident_data = []

        for _, row in accidents.iterrows():
            accident_time = row["Accident Time"]

            if pd.isna(accident_time):
                accident_time = None

            accident_data.append(
                (
                    str(row["Accident ID"]),
                    row["Accident Date"],
                    accident_time,
                    str(row["Location ID"]),
                    str(row["Vehicle Type"]),
                    str(row["Severity"]),
                    int(row["Deaths"]),
                    int(row["Injuries"]),
                    str(row["Weather"])
                    if pd.notna(row["Weather"])
                    else None
                )
            )

        cursor.executemany(
            accident_sql,
            accident_data
        )

        print("Accident records inserted:", cursor.rowcount)

        # ----------------------------------
        # STEP 7: Save all changes
        # ----------------------------------
        connection.commit()

        print("\nSUCCESS!")
        print("All records imported into MySQL.")

        # Verify totals
        cursor.execute("SELECT COUNT(*) FROM location")
        print(
            "Total locations in MySQL:",
            cursor.fetchone()[0]
        )

        cursor.execute("SELECT COUNT(*) FROM accident")
        print(
            "Total accidents in MySQL:",
            cursor.fetchone()[0]
        )

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        print("\nIMPORT FAILED")
        print("Reason:", error)
        print("Database changes were rolled back where applicable.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

        print("\nDatabase connection closed.")


if __name__ == "__main__":
    import_data()