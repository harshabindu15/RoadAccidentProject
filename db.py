import mysql.connector
from mysql.connector import Error


def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Srihari@2512",
            database="road_accident_db"
        )

        if connection.is_connected():
            print("MySQL connected successfully!")
            return connection

    except Error as error:
        print("MySQL connection error:", error)

    return None