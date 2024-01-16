from django.contrib.auth.models import User
from django.db import models

 

class Location(models.Model):
    office = models.CharField(max_length=30)

    def __str__(self):
        return self.office

class Role(models.Model):
    role = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return self.role


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True)
    full_name = models.CharField(max_length=255, null=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=16, blank=True,null=True)
    cnic = models.CharField(max_length=200, null=True)
    address = models.TextField(blank=True, null=True)
    office = models.ForeignKey(Location, on_delete=models.CASCADE,null=True)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_resignation = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=100, null=True, default="")
    designation = models.CharField(max_length=100, null=True, default="")
    salary = models.CharField(max_length=100, null=True, default="")
    role = models.ForeignKey(Role, on_delete=models.CASCADE,null=True)
    line_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees_managed')
    image = models.ImageField(upload_to='employee_images', default="",null=True)
    education = models.ImageField(upload_to='employee_images', default="",null=True)
    educational_certificates = models.ImageField(upload_to='employee_images', default="",null=True)
    experience_letter = models.ImageField(upload_to='employee_images', default="",null=True)
    email = models.CharField(max_length=200, null=True)
    


    


    def __str__(self):
        return self.full_name

class LeaveType(models.Model):
    name = models.CharField(max_length=50)    

    def __str__(self):
        return self.name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    in_out = models.CharField(max_length=100,null=True)
    

    def __str__(self):
        return self.employee.full_name
    

class Leave(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')  # Status can be Pending, Approved, Rejected
    reason = models.TextField()    

    def __str__(self):
        return self.employee.full_name +" "+ self.leave_type.name +" "+ self.status
    
class PayRoll(models.Model):
    employee = models.OneToOneField(Employee,on_delete=models.CASCADE)
    basic_pay = models.DecimalField(max_digits=8,decimal_places=2)
    total_allowance = models.DecimalField(max_digits=8, decimal_places=2)
    total_deduction = models.DecimalField(max_digits=8, decimal_places=2)
    net_salary = models.DecimalField(max_digits=8, decimal_places=2)


    def __str__(self):
        return self.employee.full_name + " " + str(self.net_salary) 
    