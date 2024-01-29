import os
from django import setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")
setup()
import schedule
import time as dt_time
from datetime import datetime
from zk import ZK, const
from hrms.models import Attendance, Employee
from django.core.exceptions import ObjectDoesNotExist


def calculate_hours_difference(datetime1, datetime2):
    time_difference = datetime2 - datetime1
    hours_difference = time_difference.total_seconds() / 3600  # 1 hour = 3600 seconds
    return int(round(hours_difference))

def is_within_time_range(datetime_obj, start_time_tuple, end_time_tuple):
    current_time = datetime_obj.time()
    start_time_parsed = datetime.strptime("{:02d}:{:02d}".format(*start_time_tuple), "%H:%M")
    end_time_parsed = datetime.strptime("{:02d}:{:02d}".format(*end_time_tuple), "%H:%M")
    return start_time_parsed.time() <= current_time <= end_time_parsed.time()

def format_time(dt, format="%Y-%m-%d %H:%M:%S"):
    return dt.strftime(format)

def check_status(dt):
    checkin_range_start = (7, 0)
    checkin_range_end = (11, 0)
    checkin_status = is_within_time_range(dt, checkin_range_start, checkin_range_end)

    checkout_range_start = (15, 0)
    checkout_range_end = (22, 0)
    checkout_status = is_within_time_range(dt, checkout_range_start, checkout_range_end)

    if checkin_status:
        return "Check-In"
    elif checkout_status:
        return "Check-out"
    else:
        return "Working"

def filter_user_attendance(attendance_list, user_id):
    attendance_list = [vars(a) for a in attendance_list]
    today = datetime.now()
    today = format_time(today, format="%Y-%m-%d")
    user_attendance = [att for att in attendance_list if att['user_id'] == user_id and format_time(att['timestamp'], format="%Y-%m-%d") == today]

    for i in range(0, len(user_attendance)):
        user_attendance[i]['type'] = check_status(user_attendance[i]['timestamp'])
        user_attendance[i]['date'] = format_time(user_attendance[i]['timestamp'])

    return user_attendance
    
def mark_absent(employee):
    # Function to mark an employee as absent for the day
    today = datetime.now().date()
    absent_entry = Attendance.objects.filter(employee=employee, check_in__date=today).first()

    if not absent_entry:
        # If no check-in entry exists, mark as absent
        absent_entry = Attendance(employee=employee, check_in=datetime.combine(today, datetime.min.time()),status="Absent")
        absent_entry.save()


def sync_attendance():
    # Configure your ZKTeco device details
    machine_ip = '192.168.100.75'
    machine_port = 4370
    timeout = 5

    z = None
    conn = None
    try:
        z = ZK(machine_ip, port=machine_port, timeout=timeout, password=0, force_udp=False, ommit_ping=False)
        conn = z.connect()
        
        z.enable_device()

        # Sync attendance
        users = conn.get_users()
        attendance = conn.get_attendance()
       
        # attendance = vars(attendance)
        # user_Att = [a for a in attendance if a.user_id == user.user_id]
        for user in users:
            privilege = 'User'
            if user.privilege == const.USER_ADMIN:
                privilege = 'Admin'
            
            user_Att = filter_user_attendance(attendance_list=attendance,user_id=user.user_id)
            try:
                employee = Employee.objects.get(zkaccess_id=user.user_id)

                if len(user_Att) > 0:
                    # Assuming you have an Employee instance corresponding to the user
                    # Extract check-in and check-out times
                    checkin_datetime = user_Att[0]['timestamp']
                    checkout_datetime = user_Att[-1]['timestamp']
                    working_hours = calculate_hours_difference(checkin_datetime, checkout_datetime)

                    # Check if there's an existing check-in entry for today
                    today = datetime.now().date()
                    existing_checkin_entry = Attendance.objects.filter(employee=employee, check_in__date=today, check_out__isnull=True,).first()
                   
                    if existing_checkin_entry:
                        # Update existing check-in entry with check-out details
                        existing_checkin_entry.check_out = checkout_datetime
                        existing_checkin_entry.status = "Present"
                        existing_checkin_entry.working_hours = working_hours
                        if checkin_datetime.time() > dt_time(9,15):
                            existing_checkin_entry.check_in_type = "Late Check In"
                        else:
                            existing_checkin_entry.check_in_type = "On Time Check In"    
                        # existing_checkin_entry.is_late_checkin()
                        # existing_checkin_entry.is_early_checkout()
                        if checkout_datetime.time() < dt_time(17,00):
                            existing_checkin_entry.check_out_type = "Ealry Check Out" 
                        else:
                            existing_checkin_entry.check_out_type = "On Time Check Out"           
                        existing_checkin_entry.save()
                    else:
                        # Create a new check-in entry
                        new_checkin_entry = Attendance(employee=employee, check_in=checkin_datetime,check_out=checkout_datetime, status="Present", working_hours=working_hours)

                        # Update check-in type and check-out type based on conditions
                        new_checkin_entry.is_late_checkin()
                        new_checkin_entry.is_early_checkout()
                        new_checkin_entry.save()

                else:
                    mark_absent(employee)
                    # No attendance records found, mark as absent
                    # Attendance.objects.filter(employee=employee, check_in__isnull=True, check_out__isnull=True).update(status="Absent", working_hours="N/A")

            except ObjectDoesNotExist:
                # Handle the case where the employee does not exist
                print(f"Employee with zkaccess_id {user.user_id} does not exist in the database.")
                        
    except Exception as e:
        print("Error aya hai ",e)
        import traceback
        traceback.print_exc()

        

if __name__ == "__main__":
    MORNING_SYNC_TIME = "17:05"
    schedule.every().day.at(MORNING_SYNC_TIME).do(sync_attendance)

    while True:
        schedule.run_pending()
        dt_time.sleep(1)




