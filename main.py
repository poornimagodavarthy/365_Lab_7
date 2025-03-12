import getpass
import mysql.connector

def connect_to_database():
    db_password = getpass.getpass("Enter the database password: ")
    conn = mysql.connector.connect(user='pgodavar', password=db_password,
                                host='mysql.labthreesixfive.com',
                                database='pgodavar')
    return conn

def get_rooms(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab7_rooms")
    result = cursor.fetchall()
    print(result)


def make_reservation(conn, firstname, lastname, roomcode, begindate, enddate, num_children, num_adults):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab7_rooms")
    result = cursor.fetchall()
    print(result)

def cancel_reservation(conn):
    pass
def search_reservation(conn):
    pass

def show_revenue(conn):
    pass

def main():
    conn = connect_to_database()
    if conn is None:
        print("Database didn't connect\n")
    else:
        print("Yay it connected!\n")

    while True:
        print("1. View rooms and rates\n")
        print("2. Make a reservation\n")
        print("3. Cancel Reservation\n")
        print("4. Search reservations\n")
        print("5. Revenue overview\n")
        print("6. Exit\n")

        choice = input("Select an option: ")

        if choice == "1":
            get_rooms(conn)
        elif choice == "2":
            firstname = input("FirstName: ")
            lastname = input("LastName: ")
            roomcode = input("Room code or Any: ")
            begindate = input("Begin Date: ")
            enddate = input("End Date: ")
            num_children = input("Number of Children: ")
            num_adults = input("Number of Adults: ")
            make_reservation(conn, firstname, lastname, roomcode, begindate, enddate, num_children, num_adults)
        elif choice == 3:
            cancel_reservation(conn)
        elif choice == 4: 
            search_reservation(conn)
        elif choice == "5":
                show_revenue(conn)
        elif choice == "6":
            print("byee!")
            break
        else:
            print("Invalid choice. Please try again.")
            break

if __name__ == "__main__":
    main()