import time
from zk import ZK

# Introduce a delay if needed
time.sleep(1)

machine_port = 4370
z = ZK('192.168.100.75', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
conn = z.connect()
z.enable_device()

try:
    # Get all attendance records
    attendances = conn.get_attendance()
    
    if not attendances:
        print("No attendance records found.")
    else:
        for attendance in attendances:
            if attendance is None:
                print("Invalid attendance record.")
            else:
                print(attendance)

    # Optionally, you can clear the attendance records after syncing
    # conn.clear_attendance()

except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the connection
    conn.disconnect()


# import time
# import schedule
# from zk import ZK

# def sync_attendance():
#     print("Syncing attendance...")

#     # Constant machine port
#     machine_port = 4370
#     z = ZK('192.168.100.75', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
#     conn = z.connect()
#     z.enable_device()

#     try:
#         # Get all attendance records
#         attendances = conn.get_attendance()

#         if not attendances:
#             print("No attendance records found.")
#         else:
#             for attendance in attendances:
#                 print("Attendance",attendance.user , attendance)
#                 if attendance is None:
#                     print("Invalid attendance record.")
#                 else:
#                     # Your sync logic here (e.g., send attendance data to a server)
#                     pass

#         # Optionally, you can clear the attendance records after syncing
#         # conn.clear_attendance()

#     except Exception as e:
#         print(f"Error: {e}")

#     finally:
#         # Close the connection
#         conn.disconnect()
#         print("Connection closed.")

# # Schedule the script to run at specific times
# schedule.every().day.at("19:00").do(sync_attendance)  # 7:00 PM
# schedule.every().day.at("09:30").do(sync_attendance)  # 9:30 AM

# # Run the scheduled jobs continuously
# while True:
#     schedule.run_pending()
#     time.sleep(1)