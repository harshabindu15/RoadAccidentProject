from db import connect_db

connection = connect_db()

if connection:
    cursor = connection.cursor()

    # Display available tables
    cursor.execute("SHOW TABLES")

    print("\nTables in MySQL:")
    for table in cursor.fetchall():
        print(table[0])

    # Display accident records
    print("\nAccident Records:")

    cursor.execute("SELECT * FROM Accident LIMIT 5")

    records = cursor.fetchall()

    for record in records:
        print(record)

    cursor.close()
    connection.close()

else:
    print("Database connection failed.")