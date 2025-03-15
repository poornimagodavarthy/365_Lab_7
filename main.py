import getpass
import warnings
import mysql.connector
from datetime import datetime
from datetime import datetime, timedelta
from decimal import Decimal
import random
import pandas as pd

def connect_to_database():
    db_password = getpass.getpass("Enter the database password: ")
    conn = mysql.connector.connect(user='pgodavar', password=db_password,
                                host='mysql.labthreesixfive.com',
                                database='pgodavar')
    return conn

def get_rooms(conn):
    warnings.filterwarnings("ignore")
    df = pd.read_sql("""
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
         select RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor,
                 COALESCE(ROUND(l.occupiedDays/180, 2), 0) as popularity, 
                 COALESCE(a.nextAvailableCheckIn, 'No future bookings'), 
                 COALESCE (m.lengthOfStay, 0) as lengthOfStay,
                 COALESCE (m.mostRecent, 'No past stays') as mostRecent
            from lab7_rooms as r
                left join last180Days as l on l.Room = r.RoomCode
                left join availableCheckInDays as a on a.Room = r.RoomCode
                left join mostRecentStays as m on m.Room = r.RoomCode
            order by popularity DESC
                   """, conn)
    df.columns = [
    "Room Code", "Room Name", "# Beds", "Bed Type",
    "Max Occ", "Base Price ($)", "Decor",
    "Popularity", "Next Available Check-in",
    "Last Stay Length", "Last Checkout Date"]

    if df.empty:
        print("No rooms found.")
    else:
        print(df.to_string(index=False))  

    return df


def make_reservation(conn, firstname, lastname, roomcode, bedtype, begindate, enddate, num_children, num_adults):
    cursor = conn.cursor()
    roomcode, bedtype, firstname = str(roomcode), str(bedtype), str(firstname)
    begindate = datetime.strptime(begindate, "%Y-%m-%d")
    enddate = datetime.strptime(enddate, "%Y-%m-%d")
    num_children = int(num_children)
    num_adults = int(num_adults) 
    maxOccupancy = num_children + num_adults
    cursor.execute("SELECT MAX(maxOcc) FROM lab7_rooms")
    max_allowed_occupancy = cursor.fetchone()[0]

    if maxOccupancy > max_allowed_occupancy:
        print("Sorry, no rooms can accomodate this many guests. Please try booking multiple rooms.")
        return
    
    if begindate >= enddate:
        raise ValueError("Begin Date > End")
    
    if roomcode != "Any" and bedtype == "Any":
        print("Error: You cannot specify 'Any' for bedtype. The room will come with its own bed type.")
        return
    
    elif roomcode == "Any" and bedtype != "Any":
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
         select DISTINCT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor, 
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
            AND r.BedType = '{bedtype}'
            order by popularity DESC
                   """
        rooms = ['AOB', 'IBD', 'RTE', 'HBB']
        roomcode = random.choice(rooms)

    elif roomcode == "Any" and bedtype == "Any":
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
         select DISTINCT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor, 
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
            order by popularity DESC
                   """
        rooms = ['AOB', 'IBD', 'RTE', 'HBB']
        beds = ['Queen','King', 'Double']
        roomcode = random.choice(rooms)
        bedtype = random.choice(beds)


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
         select DISTINCT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor, 
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
    if all_room_vals:
        selected_room = present_suggestions(all_room_vals)
        if selected_room:
            roomcode, bedtype, begindate, enddate, rate = selected_room[0], selected_room[3], datetime.strptime(selected_room[9], "%Y-%m-%d"), datetime.strptime(selected_room[11], "%Y-%m-%d"), selected_room[7]
            print("\nPlease confirm your reservation details before proceeding:")
            print("-" * 50)
            print(f"Room: {selected_room[1]} | Bed Type: {selected_room[3]} | Max Occupancy: {selected_room[4]}")
            print(f"Rate per night: ${rate}")
            print(f"Check-in Date: {begindate.strftime('%Y-%m-%d')}")
            print(f"Check-out Date: {enddate.strftime('%Y-%m-%d')}")
            print("-" * 50)
            confirmation = input("Do you want to confirm this reservation? (y/n): ")
            if confirmation.lower() == 'y':
                new_code = generate_code(conn)
                new_code = generate_code(conn)

                insert = f"""
                    INSERT INTO lab7_reservations (CODE, Room, CheckIn, Checkout, Rate, LastName, FirstName, Adults, Kids) 
                    VALUES
                    ({new_code}, '{roomcode}', '{begindate.strftime("%Y-%m-%d")}', '{enddate.strftime("%Y-%m-%d")}', {rate}, '{lastname}',  
                    '{firstname}', {num_children}, {num_adults}
                    )
                    """
                cursor.execute(insert)
                conn.commit()
                confirmation_query = """
                SELECT DISTINCT CODE, Room, CheckIn, CheckOut, Rate, LastName, FirstName, Adults, Kids, RoomName
                FROM lab7_reservations 
                JOIN lab7_rooms ON Room = RoomCode
                WHERE CODE = %s
                """
                cursor.execute(confirmation_query, (new_code,))
                reservation_details = cursor.fetchone()

                if reservation_details:
                    print("\nReservation Confirmed!")
                    print("-" * 50)
                    print(f"Reservation Code: {reservation_details[0]}")
                    print(f"Guest Name: {reservation_details[6]} {reservation_details[5]}")
                    print(f"Room: {reservation_details[1]} - {reservation_details[9]}")
                    print(f"Check-in Date: {reservation_details[2]}")
                    print(f"Check-out Date: {reservation_details[3]}")
                    print(f"Rate per Night: ${reservation_details[4]:.2f}")
                    print(f"Total Guests: {reservation_details[7]} Adults, {reservation_details[8]} Children")
                    print("-" * 50)
                    print("Thank you for booking with us!")
                

    if not all_room_vals:
        suggested_rooms = suggest_alternatives(conn, roomcode, bedtype, begindate, enddate, maxOccupancy)
        selected_room = present_suggestions(suggested_rooms)
        roomcode, bedtype, begindate, enddate, rate = selected_room[0], selected_room[3], datetime.strptime(selected_room[9], "%Y-%m-%d"), datetime.strptime(selected_room[11], "%Y-%m-%d"), selected_room[7]
    else:
        rate = all_room_vals[0][5]
        total_price = compute_total_price(begindate, enddate, rate)

    
def suggest_alternatives(conn, roomcode, bedtype, begindate, enddate, maxOccupancy):
    cursor = conn.cursor()
    query = f"""
    with last180Days as (
             select DISTINCT Room, 
                    SUM(DATEDIFF(LEAST(CheckOut, CURDATE()), GREATEST(CheckIn, DATE_SUB(CURDATE(), INTERVAL 180 DAY)))) AS occupiedDays
             from lab7_reservations
             where LEAST(CheckOut, CURDATE()) > GREATEST(CheckIn, DATE_SUB(CURDATE(), INTERVAL 180 DAY))
             group by Room
             ),
         availableCheckInDays as (
             select DISTINCT Room, MIN(CheckOut) as nextAvailableCheckIn
             from lab7_reservations
             where CheckOut >= CURDATE()
             group by Room
             ),
         mostRecentStays as (
             select DISTINCT r1.Room, r1.CheckOut as mostRecent, DATEDIFF(r1.CheckOut, r1.CheckIn) as lengthOfStay
             from lab7_reservations as r1
             where r1.CheckOut = (
                 select MAX(r2.CheckOut)
                 from lab7_reservations as r2
                    where r2.Room = r1.Room and r2.CheckOut < CURDATE() 
                 )
             ),
             ranked_rooms AS (
                select RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor, 
                        (r.basePrice * (DATEDIFF('{enddate}','{begindate}'))) AS TotalPrice,
                        COALESCE(ROUND(l.occupiedDays/180, 2), 0) as popularity, 
                        COALESCE(a.nextAvailableCheckIn, 'No future bookings') AS nextAvailableCheckIn, 
                        COALESCE (m.lengthOfStay, 0) as lengthOfStay,
                        COALESCE (m.mostRecent, 'No past stays') as mostRecent,
                        ROW_NUMBER() OVER (ORDER BY r.basePrice ASC, l.occupiedDays DESC, r.maxOcc DESC) AS row_rank
                FROM lab7_rooms as r
                    left join last180Days as l on l.Room = r.RoomCode
                    left join availableCheckInDays as a on a.Room = r.RoomCode
                    left join mostRecentStays as m on m.Room = r.RoomCode
                WHERE (a.nextAvailableCheckIn BETWEEN DATE_SUB('{begindate}', INTERVAL 50 DAY) AND DATE_ADD('{begindate}', INTERVAL 50 DAY)
                    OR a.nextAvailableCheckIn BETWEEN DATE_SUB('{enddate}', INTERVAL 50 DAY) AND DATE_ADD('{enddate}', INTERVAL 50 DAY))
                AND r.maxOcc >= {maxOccupancy}
               
                )
            SELECT * FROM ranked_rooms
            WHERE row_rank <=5
            order by popularity DESC;
    """
    
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def present_suggestions(suggested_rooms):
    print("Would you be interested in any of these rooms? \n")
    for i, room in enumerate(suggested_rooms, 1):
        print(f"{i}. Room: {room[1]} | Beds: {room[2]} | Bed Type: {room[3]} | Max Occupancy: {room[4]} | Price: {room[5]} | Decor: {room[6]} | Available From: {room[8]} | Most Recent Stay: {room[9]}, \n")
    try: 
        option = int(input("Please select a room number (1-5): "))
        if option <1 or option > 5:
            print("Invalid selection, try again")
            return None
        selected_room = suggested_rooms[option -1]
        return selected_room
    except ValueError:
        print("Invalid input, please enter a number")
        return None
        
def compute_total_price(begindate, enddate, base_rate):
    total_cost = 0
    current_date = begindate
    while current_date < enddate:  
        if current_date.weekday() < 4:  
            total_cost += base_rate
        else:  
            total_cost += base_rate * Decimal('1.1')
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
    cursor.execute(""" 
        select * from lab7_reservations where CODE = %s
        """, [code])
    result = cursor.fetchone()
    if not result:
        print ("No reservations exist with that code")
        return
    confirmation = input("Are you sure you want to cancel your reservation? Type Y to confirm, N to go back\n")
    if confirmation.upper() == "Y":
        try:
            cursor.execute("""
            delete from lab7_reservations
            where CODE = %s
            """, [code])
            conn.commit()
            print("Reservation canceled successfully.")
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally: 
            cursor.close()
    elif confirmation == "N":
        print("Cancellation terminated.")
        return
    else:
        print("Invalid option, please try again")
        return
    
def search_reservation(conn, firstname, lastname, startdate, enddate, roomcode, rsvcode):
    warnings.filterwarnings("ignore")
    conditions = []
    sub_values = []
 
    if firstname:
        conditions.append("FirstName LIKE %s")
        sub_values.append(firstname + "%")
    if lastname:
        conditions.append("LastName LIKE %s")
        sub_values.append(lastname + "%")
    if roomcode:
        conditions.append("Room LIKE %s")
        sub_values.append(roomcode + "%")
    if rsvcode:
        conditions.append("CODE = %s")
        sub_values.append(rsvcode)
    if startdate and enddate:
        conditions.append("CheckIn < %s AND CheckOut > %s")
        sub_values.append(startdate)
        sub_values.append(enddate)
    elif startdate:
        conditions.append("CheckIn <= %s")
        sub_values.append(startdate)
    elif enddate:
        conditions.append("CheckOut >= %s")
        sub_values.append(enddate)

    query = "select CODE, Room, CheckIn, CheckOut, Rate, LastName, FirstName, Adults, Kids, RoomName from lab7_reservations join lab7_rooms on Room = RoomCode"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    df = pd.read_sql(query, conn, params=sub_values)

    df.columns = [
    "Room Code", "Room Name", "Check-In", "Check-Out",
    "Rate", "Last Name", "First Name",
    "Adults", "Kids",
    "Room Name"]

    if df.empty:
        print("No rooms found.")
    else:
        print(df.to_string(index=False))
    return df


def is_valid_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def show_revenue(conn):
    warnings.filterwarnings("ignore")
    cursor = conn.cursor()
    df = pd.read_sql(""" 
        WITH months as (
            SELECT 1 as month_num, 'January' as month_name UNION ALL
            SELECT 2, 'February' UNION ALL
            SELECT 3, 'March' UNION ALL
            SELECT 4, 'April' UNION ALL
            SELECT 5, 'May' UNION ALL
            SELECT 6, 'June' UNION ALL
            SELECT 7, 'July' UNION ALL
            SELECT 8, 'August' UNION ALL
            SELECT 9, 'September' UNION ALL
            SELECT 10, 'October' UNION ALL
            SELECT 11, 'November' UNION ALL
            SELECT 12, 'December' 
                   ),
        reservation_dates AS (
            SELECT 
                res.CODE,
                res.Room,
                r.RoomName,
                res.CheckIn,
                res.CheckOut,
                DATEDIFF(res.CheckOut, res.CheckIn) AS nights,
                (
                    SELECT COUNT(*)
                    FROM (
                        SELECT ADDDATE(res.CheckIn, n) AS date
                        FROM (
                            SELECT a.i + b.i*10 + c.i*100 AS n
                            FROM 
                                (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                                (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
                                (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c
                        ) numbers
                        WHERE ADDDATE(res.CheckIn, n) < res.CheckOut
                        AND WEEKDAY(ADDDATE(res.CheckIn, n)) NOT IN (5, 6)
                    ) weekday_dates
                ) AS weekday_nights,
                r.BasePrice AS weekday_rate,
                r.BasePrice * 1.10 AS weekend_rate
            FROM lab7_reservations res
            JOIN lab7_rooms r ON res.Room = r.RoomCode
        ),
        monthly_stays AS (
            SELECT
                rd.Room,
                rd.RoomName,
                YEAR(rd.CheckIn) AS year,
                MONTH(rd.CheckIn) AS month_num,
                MONTHNAME(rd.CheckIn) AS month_name,
                CASE
                    WHEN MONTH(rd.CheckIn) = MONTH(rd.CheckOut - INTERVAL 1 DAY) THEN
                        (rd.nights - rd.weekday_nights) * rd.weekend_rate + rd.weekday_nights * rd.weekday_rate
                    ELSE
                        (DATEDIFF(LAST_DAY(rd.CheckIn) + INTERVAL 1 DAY, rd.CheckIn) - 
                            (
                                SELECT COUNT(*)
                                FROM (
                                    SELECT ADDDATE(rd.CheckIn, n) AS date
                                    FROM (
                                        SELECT a.i + b.i*10 AS n
                                        FROM 
                                            (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                                            (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) b
                                    ) numbers
                                    WHERE ADDDATE(rd.CheckIn, n) < LAST_DAY(rd.CheckIn) + INTERVAL 1 DAY
                                    AND WEEKDAY(ADDDATE(rd.CheckIn, n)) IN (5, 6)
                                ) weekend_dates
                            )
                        ) * rd.weekday_rate + 
                        (
                            SELECT COUNT(*)
                            FROM (
                                SELECT ADDDATE(rd.CheckIn, n) AS date
                                FROM (
                                    SELECT a.i + b.i*10 AS n
                                    FROM 
                                        (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                                        (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) b
                                ) numbers
                                WHERE ADDDATE(rd.CheckIn, n) < LAST_DAY(rd.CheckIn) + INTERVAL 1 DAY
                                AND WEEKDAY(ADDDATE(rd.CheckIn, n)) IN (5, 6)
                            ) weekend_dates
                        ) * rd.weekend_rate
                END AS month_revenue
            FROM reservation_dates rd
            
            UNION ALL
            
            SELECT
                rd.Room,
                rd.RoomName,
                YEAR(rd.CheckOut) AS year,
                MONTH(rd.CheckOut) AS month_num,
                MONTHNAME(rd.CheckOut) AS month_name,
                     
                (DATEDIFF(rd.CheckOut, DATE_FORMAT(rd.CheckOut, '%Y-%m-01')) - 
                    (
                        SELECT COUNT(*)
                        FROM (
                            SELECT ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n) AS date
                            FROM (
                                SELECT a.i + b.i*10 AS n
                                FROM 
                                    (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                                    (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) b
                            ) numbers
                            WHERE ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n) < rd.CheckOut
                            AND WEEKDAY(ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n)) IN (5, 6)
                        ) weekend_dates
                    )
                ) * rd.weekday_rate + 
                (
                    SELECT COUNT(*)
                    FROM (
                        SELECT ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n) AS date
                        FROM (
                            SELECT a.i + b.i*10 AS n
                            FROM 
                                (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                                (SELECT 0 i UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) b
                        ) numbers
                        WHERE ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n) < rd.CheckOut
                        AND WEEKDAY(ADDDATE(DATE_FORMAT(rd.CheckOut, '%Y-%m-01'), n)) IN (5, 6)
                    ) weekend_dates
                ) * rd.weekend_rate
            FROM reservation_dates rd
            WHERE MONTH(rd.CheckIn) <> MONTH(rd.CheckOut - INTERVAL 1 DAY)
                ),
                monthly_revenue AS (
                    SELECT
                        Room,
                        RoomName,
                        month_num,
                        month_name,
                        ROUND(SUM(month_revenue)) AS monthly_revenue
                    FROM monthly_stays
                    WHERE year = YEAR(CURDATE())  -- Only current year
                    GROUP BY Room, RoomName, month_num, month_name
                )
                     
                SELECT 
                    Room, RoomName,
                    SUM(CASE WHEN month_num = 1 THEN monthly_revenue ELSE 0 END) AS Jan,
                    SUM(CASE WHEN month_num = 2 THEN monthly_revenue ELSE 0 END) AS Feb,
                    SUM(CASE WHEN month_num = 3 THEN monthly_revenue ELSE 0 END) AS Mar,
                    SUM(CASE WHEN month_num = 4 THEN monthly_revenue ELSE 0 END) AS Apr,
                    SUM(CASE WHEN month_num = 5 THEN monthly_revenue ELSE 0 END) AS May,
                    SUM(CASE WHEN month_num = 6 THEN monthly_revenue ELSE 0 END) AS Jun,
                    SUM(CASE WHEN month_num = 7 THEN monthly_revenue ELSE 0 END) AS Jul,
                    SUM(CASE WHEN month_num = 8 THEN monthly_revenue ELSE 0 END) AS Aug,
                    SUM(CASE WHEN month_num = 9 THEN monthly_revenue ELSE 0 END) AS Sep,
                    SUM(CASE WHEN month_num = 10 THEN monthly_revenue ELSE 0 END) AS Oct,
                    SUM(CASE WHEN month_num = 11 THEN monthly_revenue ELSE 0 END) AS Nov,
                    SUM(CASE WHEN month_num = 12 THEN monthly_revenue ELSE 0 END) AS `Dec`,
                    SUM(monthly_revenue) AS Total
                FROM monthly_revenue 
                GROUP BY Room, RoomName
                            
            UNION ALL 

        SELECT 
            'TOTAL' AS Room, 
            'TOTAL' AS RoomName,  
            SUM(CASE WHEN month_num = 1 THEN monthly_revenue ELSE 0 END) AS Jan,
            SUM(CASE WHEN month_num = 2 THEN monthly_revenue ELSE 0 END) AS Feb,
            SUM(CASE WHEN month_num = 3 THEN monthly_revenue ELSE 0 END) AS Mar,
            SUM(CASE WHEN month_num = 4 THEN monthly_revenue ELSE 0 END) AS Apr,
            SUM(CASE WHEN month_num = 5 THEN monthly_revenue ELSE 0 END) AS May,
            SUM(CASE WHEN month_num = 6 THEN monthly_revenue ELSE 0 END) AS Jun,
            SUM(CASE WHEN month_num = 7 THEN monthly_revenue ELSE 0 END) AS Jul,
            SUM(CASE WHEN month_num = 8 THEN monthly_revenue ELSE 0 END) AS Aug,
            SUM(CASE WHEN month_num = 9 THEN monthly_revenue ELSE 0 END) AS Sep,
            SUM(CASE WHEN month_num = 10 THEN monthly_revenue ELSE 0 END) AS Oct,
            SUM(CASE WHEN month_num = 11 THEN monthly_revenue ELSE 0 END) AS Nov,
            SUM(CASE WHEN month_num = 12 THEN monthly_revenue ELSE 0 END) AS `Dec`,
            SUM(monthly_revenue) AS Total
        FROM monthly_revenue
        GROUP BY month_name, month_num
        ORDER BY month_num
            """)
    
    result = cursor.fetchall()
    formatted_result = []
    for row in result:
        formatted_row = list(row) 
        for i in range(1, len(formatted_row)):  
            if isinstance(formatted_row[i], Decimal):
                formatted_row[i] = "${:,.2f}".format(formatted_row[i])
        
        formatted_result.append(tuple(formatted_row))  

    for row in formatted_result:
        for col in row:
            if col != '$0.00':
                print(col)

    
    df.columns = ["Room", "RoomName", "Jan", "Feb", "Mar", "Apr", 
                  "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Total"]
    if df.empty:
        print("Error, please try again. ")
    else:
        print(df.to_string(index=False))  

    return df

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
            make_reservation(conn, firstname, lastname, roomcode, bedtype, begindate, enddate, num_children, num_adults)
        elif choice == "3":
            code = input("Enter your reservation code: ")
            cancel_reservation(conn, code)
        elif choice == "4": 
            firstname = input("FirstName: ")
            lastname = input("LastName: ")
            startdate = input("Begin Date: ")
            if not (startdate == "" or is_valid_date(startdate)):
                print ("Please enter a valid date, try again")
                startdate = input("Begin Date: ")
            enddate = input("End Date: ")
            if not (enddate == "" or is_valid_date(enddate)):
                print ("Please enter a valid date, try again")
                enddate = input("End Date: ")
            roomcode = input(" Room Code: ")
            rsvcode = input("Reservation Code: ")
            if (len(rsvcode) < 5 and len(rsvcode) != 0):
                print ("Please enter the full reservation code, try again")
                rsvcode = input("Reservation Code: ")
            search_reservation(conn, firstname, lastname, startdate, enddate, roomcode, rsvcode)
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
