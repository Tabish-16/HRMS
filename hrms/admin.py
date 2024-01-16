
from django.contrib import admin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from hrms.models import *
from hrms.views import notify_employee_leave_status



admin.site.register(Attendance)
admin.site.register(LeaveType)

admin.site.register(Location)
admin.site.register(Role)

@receiver(post_save, sender=Leave)
def changeStatus(sender, instance, **kwargs):
    if instance.status != 'Pending':
        notify_employee_leave_status(instance)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'designation', 'role', 'email')
    list_filter = ('office', 'department', 'designation', 'role', 'line_manager')
    search_fields = ('full_name', 'cnic', 'email')

    def employee_name(self,obj):
        return obj.full_name
admin.site.register(Employee, EmployeeAdmin)

class PayRollAdmin(admin.ModelAdmin):
    list_display = ('employee_full_name', 'basic_pay', 'total_allowance', 'total_deduction', 'net_salary')
    list_filter = ('employee__department', 'employee__designation')  # Add filters based on your needs
    search_fields = ('employee__full_name', 'employee__cnic')  # Add search fields based on your needs

    def employee_full_name(self, obj):
        return obj.employee.full_name
    employee_full_name.short_description = 'Employee Full Name'

admin.site.register(PayRoll, PayRollAdmin)

class LeaveAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "type of leave", "status")

admin.site.register(Leave)