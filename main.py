import getpass
import mysql.connector
from datetime import datetime
from datetime import datetime, timedelta
from decimal import Decimal
import random

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
                   """)
    result = cursor.fetchall()
    for row in result:
        print (f"Room: {row[0]}, Room Name: {row[1]}, Beds: {row[2]}, Bed Type: {row[3]}, Max Occ: {row[4]}, Base Price: {row[5]}, Decor: {row[6]}, Popularity: {row[7]}, Next Available Check-in: {row[8]}, Most Recent Stay: {row[9]} days, Check-out Date: {row[10]}")


def make_reservation(conn, firstname, lastname, roomcode, bedtype, begindate, enddate, num_children, num_adults):
    cursor = conn.cursor()
    roomcode, bedtype, firstname = str(roomcode), str(bedtype), str(firstname)
    begindate = datetime.strptime(begindate, "%Y-%m-%d")
    enddate = datetime.strptime(enddate, "%Y-%m-%d")
    num_children = int(num_children)
    num_adults = int(num_adults) 
    maxOccupancy = num_children + num_adults
    """
    cursor.execute("SELECT MAX(maxOcc) FROM lab7_rooms")
    max_allowed_occupancy = cursor.fetchone()[0]
    if maxOccupancy > max_allowed_occupancy:
        print("Sorry, no rooms can accomodate this many guests. Please try booking multiple rooms.")
        return
    """
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


    if not all_room_vals:
        suggested_rooms = suggest_alternatives(conn, roomcode, bedtype, begindate, enddate, maxOccupancy)
        if not suggested_rooms:
            print("Sorry, no rooms are availble for those dates, please select a different date.")
            return
        else:
            selected_room = present_suggestions(suggested_rooms)
            roomcode, bedtype, begindate, enddate, rate = selected_room[0], selected_room[3], datetime.strptime(selected_room[9], "%Y-%m-%d"), datetime.strptime(selected_room[11], "%Y-%m-%d"), selected_room[7]
    else:
        rate = all_room_vals[0][5]
        total_price = compute_total_price(begindate, enddate, rate)
    
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
    SELECT CODE, Room, CheckIn, CheckOut, Rate, LastName, FirstName, Adults, Kids, RoomName
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

    
    

def suggest_alternatives(conn, roomcode, bedtype, begindate, enddate, maxOccupancy):
    cursor = conn.cursor()
    #logic: rank on lower price, higher popularity, higher max occupancy
    
    query = f"""
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
                WHERE nextAvailableCheckIn <= '{begindate}'
                AND r.maxOcc >= {maxOccupancy}
                AND NOT EXISTS (
                    SELECT 1
                    FROM lab7_reservations r2
                    WHERE r2.CheckIn > '{begindate}' AND r2.CheckOut < '{enddate}'
                )
                )
            SELECT * FROM ranked_rooms
            WHERE row_rank <=5
            order by popularity DESC;
    """
    
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def present_suggestions(suggested_rooms):
    print("We couldn't find exact matches. Would you be interested in any of these other rooms? \n")
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
    cursor = conn.cursor()
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
    
    cursor.execute(query, sub_values)
    result = cursor.fetchall()
    for row in result:
        print (f"CODE: {row[0]}, Room: {row[1]}, Check-in: {row[2]}, CheckOut: {row[3]}, Rate: {row[4]}, Last Name: {row[5]}, FirstName: {row[6]}, Adults: {row[7]}, Kids: {row[8]}, Room Name: {row[9]}")
    cursor.close()

def is_valid_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def show_revenue(conn):
    cursor = conn.cursor()
    #revenue per night for each reservation
    # query = f"""
    #     SELECT 
    #         r.RoomCode,
    #         g.date,
    #         CASE 
    #             WHEN WEEKDAY(g.date) IN (5,6) THEN r.BasePrice * 1.10  
    #             ELSE r.BasePrice
    #         END AS revenue
    #     FROM lab7_reservations res
    #     JOIN (
    #         SELECT DATE_ADD(DATE_FORMAT(CURRENT_DATE, '%Y-01-01'), INTERVAL numbers.n DAY) AS date
    #         FROM (
    #             SELECT ones.n + tens.n + hundreds.n AS n
    #             FROM 
    #                 (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
    #                 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS ones
    #             JOIN 
    #                 (SELECT 0 AS n UNION ALL SELECT 10 UNION ALL SELECT 20 UNION ALL SELECT 30 UNION ALL SELECT 40
    #                 UNION ALL SELECT 50 UNION ALL SELECT 60 UNION ALL SELECT 70 UNION ALL SELECT 80 UNION ALL SELECT 90) AS tens
    #                 ON 1=1  
    #             JOIN 
    #                 (SELECT 0 AS n UNION ALL SELECT 100 UNION ALL SELECT 200 UNION ALL SELECT 300) AS hundreds
    #                 ON 1=1  
    #         ) AS numbers
    #         WHERE DATE_ADD(DATE_FORMAT(CURRENT_DATE, '%Y-01-01'), INTERVAL numbers.n DAY) <= DATE_FORMAT(CURRENT_DATE, '%Y-12-31')
    #     ) g ON g.date >= res.CheckIn AND g.date < res.CheckOut
    #     JOIN lab7_rooms r ON res.Room = r.RoomCode;
    #     """
    # result = cursor.fetchall(query)
    # return result

    cursor.execute(""" 
        WITH reservation_dates AS (
    -- Step 1: Generate one row per reservation with dates and price info
    SELECT 
        res.CODE,
        res.Room,
        r.RoomName,
        res.CheckIn,
        res.CheckOut,
        DATEDIFF(res.CheckOut, res.CheckIn) AS nights,
        -- Calculate weekday nights in the reservation
        (
            SELECT COUNT(*)
            FROM (
                SELECT ADDDATE(res.CheckIn, n) AS date
                FROM (
                    -- Generate sequence of numbers from 0 to 999 (adjust as needed)
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
        -- Weekday rate
        r.BasePrice AS weekday_rate,
        r.BasePrice * 1.10 AS weekend_rate
    FROM lab7_reservations res
    JOIN lab7_rooms r ON res.Room = r.RoomCode
),
monthly_stays AS (
    -- Step 2: Split reservations by month
    SELECT
        rd.Room,
        rd.RoomName,
        YEAR(rd.CheckIn) AS year,
        MONTH(rd.CheckIn) AS month_num,
        MONTHNAME(rd.CheckIn) AS month_name,
        -- Handle stays within a single month
        CASE
            WHEN MONTH(rd.CheckIn) = MONTH(rd.CheckOut - INTERVAL 1 DAY) THEN
                -- Calculate full stay price
                (rd.nights - rd.weekday_nights) * rd.weekend_rate + rd.weekday_nights * rd.weekday_rate
            ELSE
                -- Calculate partial stay price (for check-in month)
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
    
    -- Handle the checkout month for multi-month stays
    SELECT
        rd.Room,
        rd.RoomName,
        YEAR(rd.CheckOut) AS year,
        MONTH(rd.CheckOut) AS month_num,
        MONTHNAME(rd.CheckOut) AS month_name,
        -- Calculate partial stay price (for check-out month)
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
        -- Final pivot table
        SELECT 
            month_name,
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
            SUM(CASE WHEN month_num = 12 THEN monthly_revenue ELSE 0 END) AS 'Dec',
            SUM(monthly_revenue) AS Total
        FROM monthly_revenue
        GROUP BY month_name, month_num
        ORDER BY month_num
            """)
    result = cursor.fetchall()
    formatted_result = []
    for row in result:
        # Create a new tuple with formatted values
        formatted_row = list(row)  # Convert tuple to list so we can modify it
        
        # Format each decimal value as a price
        for i in range(1, len(formatted_row)):  # Skip the first element (month name)
            if isinstance(formatted_row[i], Decimal):
                # Format as currency with dollar sign, thousands separator, and 2 decimal places
                formatted_row[i] = "${:,.2f}".format(formatted_row[i])
        
        formatted_result.append(tuple(formatted_row))  # Convert back to tuple

    # Display or use the formatted result
    for row in formatted_result:
        for col in row:
            if col != '$0.00':
                print(col)

def main():
    conn = connect_to_database()
    if conn is None:
        print("Database didn't connect\n")
    else:
        print("Yay it connected!\n")

    # QUERY 2 TESTS
    #print(suggest_alternatives(conn, 'AUB', 'Queen', '2025-05-05', '2025-05-08', 1))
        
    #make_reservation(conn, 'jane', 'doe', 'HBB', 'Queen', '2025-05-05', '2025-05-08', 3, 1)
        
    #make_reservation(conn, "mary", "jane", "Any", "Any", '2025-05-16', '2025-05-18', 0, 1) #add more flexibility to suggest rooms, fix popularity not found
    #make_reservation(conn, "joe", "bob", "HBB", "Any", '2025-05-02', '2025-05-08', 1, 1)
   
    #make_reservation(conn, "joe", "bob", 'Any', 'Queen', '2025-05-02', '2025-05-08', 1, 1)
    make_reservation(conn, "joe", "bob", "HBB", "Queen", '2025-05-02', '2025-05-08', 1, 1)
    '''
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
            '''

#cancel_reservation
if __name__ == "__main__":
    main()