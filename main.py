import getpass
import mysql.connector

def connect_to_database():
    db_password = getpass.getpass("Enter the database password: ")
    conn = mysql.connector.connect(user='pgodavar', password=db_password,
                                host='mysql.labthreesixfive.com',
                                database='pgodavar')
    return conn

def get_rooms():
    pass

def make_reservation():
    pass

def cancel_reservation():
    pass
def search_reservation():
    pass
def revenue():
    pass

def main():
    conn = connect_to_database()
    if conn is None:
        print("Database didn't connect")
    else:
        print("Yay it connected!")

if __name__ == "__main__":
    main()