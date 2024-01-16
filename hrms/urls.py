"""
URL configuration for hrms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django import views
from django.contrib import admin
from django.urls import path, re_path
from hrms import settings, views
from django.views.static import serve 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',views.userLogin,name='login'),
    path('logout/',views.logoutUser,name='logout'),
    path('',views.dashboard,name='dashboard'),
    path('employee',views.employee,name='employee'),
    path('leaves',views.leaves,name='leaves'),
    path('leaves_actions',views.leaves_actions,name='leaves_actions'),
    path('editemployee/<str:pk>/',views.editemployee,name='editemployee'),
    path('updateEmployee/<str:pk>/',views.updateEmployee,name='updateEmployee'),
    path('employeeDetails/<str:pk>/',views.employeeDetails,name='employeeDetails'),
    path('modifyLeave',views.modify_leave,name="modifyLeave"),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 
]
