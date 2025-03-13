import getpass
import mysql.connector
from datetime import datetime


def connect_to_database():
    db_password = getpass.getpass("Enter the database password: ")
    conn = mysql.connector.connect(user='aramchan', password=db_password,
                                host='mysql.labthreesixfive.com',
                                database='aramchan')
    return conn

def get_rooms(conn):
    cursor = conn.cursor()
    cursor.execute("""
         with last180Days as (
             select Room, 
                    SUM(DATEDIFF(LEAST(CheckOut, CURDATE()), GREATEST(CheckIn, DATE_SUB(CURDATE(), INTERVAL 180 DAY)))) AS occupiedDays
             from lab7_reservations
             where LEAST(CheckOut, CURDATE()) > GREATEST(CheckIn, DATE_SUB(CURDATE(), INTERVAL 180 DAY))
             group by Room
             ),
         availableCheckInDays as (
             select Room, MIN(CheckOut) as nextAvailableCheckIn
             from lab7_reservations
             where CheckOut > CURDATE()
             group by Room
             ),
         mostRecentStays as (
             select r1.Room, r1.CheckOut as mostRecent, DATEDIFF(r1.CheckOut, r1.CheckIn) as lengthOfStay
             from lab7_reservations as r1
             where r1.CheckOut = (
                 select MAX(r2.CheckOut)
                 from lab7_reservations as r2
                    where r2.Room = r1.Room and r2.CheckOut < CURDATE()
                 )
             )
         select RoomName, 
                 COALESCE(ROUND(l.occupiedDays/180, 2), 0) as popularity, 
                 COALESCE(a.nextAvailableCheckIn, 'No future bookings'), 
                 COALESCE (m.lengthOfStay, 0) as lengthOfStay,
                 COALESCE (m.mostRecent, 'No past stays') as mostRecent
            from lab7_rooms as r
                left join last180Days as l on l.Room = r.RoomCode
                left join availableCheckInDays as a on a.Room = r.RoomCode
                left join mostRecentStays as m on m.Room = r.RoomCode
            order by popularity DESC
                   """)
    result = cursor.fetchall()
    for row in result:
        print (f"Room: {row[0]}, Popularity: {row[1]}, Next Available Check-in: {row[2]}, Most Recent Stay: {row[3]} days, Check-out Date: {row[4]}")


def make_reservation(conn, firstname, lastname, roomcode, bedtype, begindate, enddate, num_children, num_adults):
    cursor = conn.cursor()
    # check room availability with a query
        # if Any, show *
    # display available rooms
        # roomcode, room name, num beds, price
    # calc total price
    # insert into lab_7_reservations
    roomcode, bedtype = str(roomcode), str(bedtype)
    begindate = datetime.strptime(begindate, "%Y-%m-%d")
    enddate = datetime.strptime(enddate, "%Y-%m-%d")
    if roomcode == "Any" and bedtype == "Any":
        query = f"""
        SELECT * 
        FROM lab7_reservations 
        JOIN lab7_rooms ON lab7_rooms.RoomCode = lab7_reservations.Room
        WHERE Room = '{roomcode}' AND bedType = '{bedtype}'
        """
    else:
        query = """
        SELECT RoomCode, RoomName, BedType, maxOcc, basePrice
        FROM lab7_reservations 
        JOIN lab7_rooms ON lab7_rooms.RoomCode = lab7_reservations.Room
        """
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def cancel_reservation(conn, code):
    cursor = conn.cursor()
    code = str(code)
    confirmation = input("Are you sure you want to cancel your reservation? Type Y to confirm, N to go back")
    if confirmation == "Y":
        cursor.execute(""""
        delete from lab7_reservations
        where CODE = '{code}'
         """)
    elif confirmation == "N":
        return
    else:
        print("Invalid option, please try again")
        return
    
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
            bedtype = input("Bed Type: ")
            begindate = input("Begin Date: ")
            enddate = input("End Date: ")
            num_children = input("Number of Children: ")
            num_adults = input("Number of Adults: ")
            res = make_reservation(conn, firstname, lastname, roomcode, bedtype, begindate, enddate, num_children, num_adults)
            print(res)
        elif choice == 3:
            code = input("Enter your reservation code: ")
            cancel_reservation(conn, code)
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
#cancel_reservation
if __name__ == "__main__":
    main()