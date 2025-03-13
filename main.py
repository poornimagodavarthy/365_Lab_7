import getpass
import mysql.connector
from datetime import datetime
from datetime import datetime, timedelta

# PARAMETRIZE EVERYTHINGG


def connect_to_database():
    #db_password = getpass.getpass("Enter the database password: ")
    conn = mysql.connector.connect(user='pgodavar', password='Wtr25_365_028373715',
                                host='mysql.labthreesixfive.com',
                                database='pgodavar')
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
    # TO DO
        # no matches = suggest 5
        # notify if exceeds maxOcc
        # present numbered list of available rooms
        # error check: if ONE is Any not both
        # option to cancel 
        # booking confirmation screen
    roomcode, bedtype, firstname = str(roomcode), str(bedtype), str(firstname)
    begindate = datetime.strptime(begindate, "%Y-%m-%d")
    enddate = datetime.strptime(enddate, "%Y-%m-%d")
    num_children = int(num_children)
    num_adults = int(num_adults) 
    maxOccupancy = num_children + num_adults
    if begindate >= enddate:
        raise ValueError("Begin Date > End")

    if roomcode == "Any" and bedtype == "Any":
        all_rooms = f"""
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
             where CheckOut >= CURDATE()
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
         select RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor,
                 (r.basePrice * (DATEDIFF('{enddate}','{begindate}'))) AS TotalPrice
            from lab7_rooms as r
                left join last180Days as l on l.Room = r.RoomCode
                left join availableCheckInDays as a on a.Room = r.RoomCode
                left join mostRecentStays as m on m.Room = r.RoomCode
            WHERE nextAvailableCheckIn <= '{begindate}'
            AND r.maxOcc >= {maxOccupancy}
            AND NOT EXISTS (
                SELECT 1
                FROM lab7_reservations r2
                WHERE r2.CheckIn > '{begindate}' AND r2.CheckOut < '{enddate}'
            )

            order by popularity DESC
                   """
        
    else:
        all_rooms = f"""
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
             where CheckOut >= CURDATE()
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
         select RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor, 
                (r.basePrice * (DATEDIFF('{enddate}','{begindate}'))) AS TotalPrice,
                 COALESCE(ROUND(l.occupiedDays/180, 2), 0) as popularity, 
                 COALESCE(a.nextAvailableCheckIn, 'No future bookings') AS nextAvailableCheckIn, 
                 COALESCE (m.lengthOfStay, 0) as lengthOfStay,
                 COALESCE (m.mostRecent, 'No past stays') as mostRecent
            from lab7_rooms as r
                left join last180Days as l on l.Room = r.RoomCode
                left join availableCheckInDays as a on a.Room = r.RoomCode
                left join mostRecentStays as m on m.Room = r.RoomCode
            WHERE nextAvailableCheckIn <= '{begindate}'
            AND r.maxOcc >= {maxOccupancy}
            AND NOT EXISTS (
                SELECT 1
                FROM lab7_reservations r2
                WHERE r2.CheckIn > '{begindate}' AND r2.CheckOut < '{enddate}'
            )
            AND r.RoomCode = '{roomcode}' AND r.BedType = '{bedtype}'
            order by popularity DESC
                   """
    cursor.execute(all_rooms)
    all_room_vals = cursor.fetchall()
    print("VALUES: ", all_room_vals)
    rate = all_room_vals[0][5]

    total_price = compute_total_price(begindate, enddate, rate)
    print(total_price)
    
    new_code = generate_code(conn)
    print(new_code)

    insert = f"""
        INSERT INTO lab7_reservations (CODE, Room, CheckIn, Checkout, Rate, LastName, FirstName, Adults, Kids) 
        VALUES
        ({new_code}, '{roomcode}', '{begindate.strftime("%Y-%m-%d")}', '{enddate.strftime("%Y-%m-%d")}', {rate}, '{lastname}',  
        '{firstname}', {num_children}, {num_adults}
        )
        """
    cursor.execute(insert)
    conn.commit()


def compute_total_price(begindate, enddate, base_rate):
    total_cost = 0
    current_date = begindate
    while current_date < enddate:  
        if current_date.weekday() < 4:  
            total_cost += base_rate
        else:  
            total_cost += base_rate * 1.1  
        current_date += timedelta(days=1)
    return round(total_cost, 2)


def generate_code(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CODE) FROM lab7_reservations")
    max_code = cursor.fetchone()[0]
    if max_code:
        return max_code + 1
    else:
        return 10101


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
            #print(res)
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