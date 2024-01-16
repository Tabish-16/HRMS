from datetime import datetime
from urllib import response
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib import messages
from hrms.models import *


def userLogin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return HttpResponse("Username and password are required fields")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return HttpResponse("User not found or invalid credentials")
    else:
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return render(request, "login.html")


def logoutUser(request):
    logout(request)
    if request.user.is_authenticated:
        return redirect('login')
    else:
        return redirect("dashboard")


@login_required(login_url='/login')
def dashboard(request):
    user = request.user
    user_profile = Employee.objects.get(user=user)
    if user_profile.role.role == 'Line Manager':
        all_user = Employee.objects.all()
        total_employee = Employee.objects.count()
        leaves = Leave.objects.count()
        pendding_leaves = Leave.objects.filter(status='Pending')
        # for pl in pendding_leaves:
        #     print("Individual leave count:", pl.status)

        # print(leaves)
        # print(total_employee)
        context = {'page': 'Dashboard',
                   'all_users': all_user,
                   'user_profile': user_profile,
                   'total_employee': total_employee,
                   'leaves': leaves,
                   'pending_leaves': pendding_leaves.count(),
                   }
        return render(request, 'dashboard.html', context)
    else:

        context = {'page': 'Dashboard', 'users': user_profile}
        return render(request, 'dashboard.html', context)


@login_required(login_url='/login')
def employee(request):
    user = request.user
    user_profile = Employee.objects.get(user=user)

    if user_profile.role.role == 'Line Manager':
        all_user = Employee.objects.all()
        total_employee = Employee.objects.count()
        pendding_leaves = Leave.objects.filter(status='Pending')
        context = {'page': 'Dashboard',
                   'users': all_user,
                   'total_employee': total_employee,
                   'pending_leaves': pendding_leaves.count(),
                   'manager': user_profile,
                   }
        return render(request, 'employee.html', context)
    else:

        context = {'page': 'Dashboard', 'users': user_profile}
        return render(request, 'employeeDetails.html', context)


def leaves(request):

    user = request.user
    manager = Employee.objects.get(user=user)
    if manager.role.role == 'Line Manager':
        pending_leaves = Leave.objects.filter(status='Pending').select_related('employee')
        
        pending_leaves = Leave.objects.filter(status='Pending')
        leaves_data = []

        for leave in pending_leaves:
            leave_data = {
                'leave_id': leave.id,
                'employee_id': leave.employee.id,
                'image': leave.employee.image,
                'employee': leave.employee.full_name,
                'reason': leave.reason,
                'status': leave.status,
                'from_date': leave.start_date,
                'to_date': leave.end_date,
                'pending_leaves': pending_leaves.count()
            }
            leaves_data.append(leave_data)
        context = {'leaves_data': leaves_data, 'manager': manager}
        return render(request, 'leave.html', context)
    else:
        user = request.user.employee
        line_manager =  user.line_manager
        line_manager_email = line_manager.email
        leave_type = LeaveType.objects.all()
        user_leave_applications = Leave.objects.filter(employee=user,status='Pending')
        context = {'leave_types': leave_type,'applied_leave':user_leave_applications,'employee':user}
        if request.method=='POST':
            # employee = Employee.objects.get(user=user)
            employee_name = user
            employee_leave_type = request.POST.get('leave_type')
            reason = request.POST.get('reason')
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            leave_type_instance, created = LeaveType.objects.get_or_create(name=employee_leave_type)
            create_leave = Leave(employee = employee_name,
                                 leave_type=leave_type_instance,
                                 reason=reason,
                                 start_date=datetime.strptime(from_date, '%Y-%m-%d').date(),
        						 end_date=datetime.strptime(to_date, '%Y-%m-%d').date())
            create_leave.save()
            employee_leave_notif(create_leave,user_leave_applications,user,line_manager_email)
            return redirect('leaves')
        return render(request, 'leave.html',context )
##API
def SEND_EMAIL(to,subject,html):
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    port = 587
    smtp_server = "smtp.gmali.com"
    if type(to)==list:
        li = to
    if type(to) ==str:
        li = [to]
        
    from_email = "tabishali121619@gmail.com"
    from_pswd = "aiox ybzb wcqm jkwo"
    for dest in li:
        try:
            import time
            message = MIMEMultipart()
            date_format = '%d-%m-%Y'
            current_time = time.strftime(date_format)
            message[
				"Subject"] =subject
            message["From"] = from_email
            message["To"] = dest
            
            part1 = MIMEText(html, "html")
            message.attach(part1)
            s = smtplib.SMTP(smtp_server, port)
            s.starttls()
            s.login(from_email, from_pswd)
            message = message.as_string()
            s.sendmail(from_email, dest, message)
            s.quit()
            print(dest, "SENT")
        except Exception as e:
            print(dest, f"FAILED *{str(e)}*")
    
def modify_leave(request):
    u = request.GET.get("user")

    leaveID = request.GET.get("leaveId")
    status = request.GET.get("status")
    text = f'''
	u = {u}<br>
    leaveID = {leaveID}<br>
    status  ={status}
'''
    leave_old = Leave.objects.get(id=leaveID)
    if leave_old.status.lower() == 'pending':
        Leave.objects.filter(id=leaveID).update(status=status)
        leave = Leave.objects.get(id = leaveID)
        notify_employee_leave_status(leave)
        return HttpResponse("<h1 style='text-align:center; color:green;'>Thank You </h1><br><center><a  onclick='window.close()'><h3>Close</h3></a></center>")
    else:
        return HttpResponse(f"<h1 style='text-align:center; color:green;'>Leave Already {leave_old.status}</h1><br><center><a  onclick='window.close()'><h3>Close</h3></a></center>")
##AP END
def notify_employee_leave_status(leave):
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    employe_name = leave.employee.full_name
    email = leave.employee.email
    status = leave.status
    if status != 'Pending':
        port = 587
        smtp_server = "smtp.gmail.com"
        li = [email]
        from_email = "tabishali121619@gmail.com"
        from_pswd = "aiox ybzb wcqm jkwo"
        for dest in li:
            try:
                import time
                message = MIMEMultipart()
                date_format = '%d-%m-%Y'
                current_time = time.strftime(date_format)
                message[
					"Subject"] = f"Your Leave Status"
                message["From"] = from_email
                message["To"] = dest
                html = f"""
							{employe_name}, Your Leave Application Status has been {status}
					"""
                part1 = MIMEText(html, "html")
                message.attach(part1)
                s = smtplib.SMTP(smtp_server, port)
                s.starttls()
                s.login(from_email, from_pswd)
                message = message.as_string()
                s.sendmail(from_email, dest, message)
                s.quit()
                print(dest, "SENT")
            except Exception as e:
                print(dest, f"FAILED *{str(e)}*")
    return "ALL OK"

	
	# leave_user = leave_user.last()
    # if leave_user.status is not 'Pending':

def employee_leave_notif(create_leave,user_leave_applications,user,line_manager_email):
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    port = 587
    smtp_server = "smtp.gmail.com"
    li = [line_manager_email]
    from_email = "tabishali121619@gmail.com"
    from_pswd = "aiox ybzb wcqm jkwo"
    for dest in li:
        try:
            import time
            message = MIMEMultipart()
            date_format = '%d-%m-%Y'
            current_time = time.strftime(date_format)
            message[
                "Subject"] = f"A new leave request by {user.full_name}. Leave ID: {create_leave.id}"
            message["From"] = from_email
            message["To"] = dest
            for leave in user_leave_applications:
                reason = leave.reason
                status = leave.status
            html = '''
<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="en">

<head>
	<title></title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<style>
		* {
			box-sizing: border-box;
		}

		body {
			margin: 0;
			padding: 0;
		}

		a[x-apple-data-detectors] {
			color: inherit !important;
			text-decoration: inherit !important;
		}

		#MessageViewBody a {
			color: inherit;
			text-decoration: none;
		}

		p {
			line-height: inherit
		}

		.desktop_hide,
		.desktop_hide table {
			mso-hide: all;
			display: none;
			max-height: 0px;
			overflow: hidden;
		}

		.image_block img+div {
			display: none;
		}

		@media (max-width:590px) {
			.desktop_hide table.icons-inner {
				display: inline-block !important;
			}

			.icons-inner {
				text-align: center;
			}

			.icons-inner td {
				margin: 0 auto;
			}

			.mobile_hide {
				display: none;
			}

			.row-content {
				width: 100% !important;
			}

			.stack .column {
				width: 100%;
				display: block;
			}

			.mobile_hide {
				min-height: 0;
				max-height: 0;
				max-width: 0;
				overflow: hidden;
				font-size: 0px;
			}

			.desktop_hide,
			.desktop_hide table {
				display: table !important;
				max-height: none !important;
			}
		}
	</style>
</head>

<body style="background-color: #ffffff; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;">
	<table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;">
		<tbody>
			<tr>
				<td>
					<table class="row row-1" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 570px; margin: 0 auto;" width="570">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="heading_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<h1 style="margin: 0; color: #7747FF; direction: ltr; font-family: Arial, Helvetica, sans-serif; font-size: 38px; font-weight: 700; letter-spacing: normal; line-height: 120%; text-align: center; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 45.6px;"><span class="tinyMce-placeholder">Leave Request</span></h1>
															</td>
														</tr>
													</table>
													<table class="divider_block block-2" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<div class="alignment" align="center">
																	<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																		<tr>
																			<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 1px solid #dddddd;"><span>&#8202;</span></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-3" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad">
																<div style="color:#101112;direction:ltr;font-family:Georgia, Times, 'Times New Roman', serif;font-size:20px;font-weight:400;letter-spacing:0px;line-height:120%;text-align:left;mso-line-height-alt:33.6px;">
																	<p style="margin: 0;">
                                                                    '''
            html = html + f"""
				I hope this message finds you well.<br>

				I am writing to request a leave:<br>

				Name: {user.full_name}<br>
				Leave ID: {create_leave.id}<br>
				Reason: <strong>{reason}</strong><br>
				Status: <strong>{status}</strong><br>

				I kindly request your approval for this leave. Thank you for your attention.<br>

				Sincerely,<br>
				{user.full_name}<br>
			"""
            html = html+ f'''
                                                                </p>
																</div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-2" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-radius: 0; color: #000000; width: 570px; margin: 0 auto;" width="570">
										<tbody>
											<tr>
												<td class="column column-1" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="button_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<div class="alignment" align="center"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="link" style="height:42px;width:99px;v-text-anchor:middle;" arcsize="10%" stroke="false" fillcolor="#5cb85c">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#ffffff; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://127.0.0.1:8000/modifyLeave?user={user.full_name}&status=approved&leaveId={create_leave.id}" target="_blank" style="text-decoration:none;display:inline-block;color:#ffffff;background-color:#5cb85c;border-radius:4px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:5px;padding-bottom:5px;font-family:Arial, Helvetica, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:20px;padding-right:20px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Approve</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
															</td>
														</tr>
													</table>
												</td>
												<td class="column column-2" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="button_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<div class="alignment" align="center"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="link" style="height:42px;width:85px;v-text-anchor:middle;" arcsize="10%" stroke="false" fillcolor="#d9534f">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#ffffff; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://127.0.0.1:8000/modifyLeave?user={user.full_name}&status=rejected&leaveId={create_leave.id}" target="_blank" style="text-decoration:none;display:inline-block;color:#ffffff;background-color:#d9534f;border-radius:4px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:5px;padding-bottom:5px;font-family:Arial, Helvetica, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:20px;padding-right:20px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Reject</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-3" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 570px; margin: 0 auto;" width="570">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="icons_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="vertical-align: middle; color: #1e0e4b; font-family: 'Inter', sans-serif; font-size: 15px; padding-bottom: 5px; padding-top: 5px; text-align: center;">
																<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																																	</table>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
				</td>
			</tr>
		</tbody>
	</table><!-- End -->
</body>

</html>
			'''

          
            part1 = MIMEText(html, "html")
            message.attach(part1)
            s = smtplib.SMTP(smtp_server, port)
            s.starttls()
            s.login(from_email, from_pswd)
            message = message.as_string()
            s.sendmail(from_email, dest, message)
            s.quit()
            print(dest, "SENT")
        except Exception as e:
            print(dest, f"FAILED *{str(e)}*")
    return "ALL OK"


def leaves_actions(request):
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave = Leave.objects.get(id=leave_id)
        if action == 'Accept':
            leave.status = 'Manager Approved'
            leave.save()
            s = send_admin_notification(leave)
            messages.success(request, 'Leave request approved by manager.')
            return redirect('leaves')
        elif action == 'Reject':
            leave.status = 'Manager Rejected'
            leave.save()
            s = send_admin_notification(leave)
            messages.success(request, 'Leave request rejected by manager.')
            return redirect('leaves')
    return HttpResponse('<h1>Invalid request.</h1>')


def send_admin_notification(leave):
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    port = 587
    smtp_server = "smtp.gmail.com"
    li = ["mktickabc@gmail.com", "tabishyt121619@gmail.com",
          "tabishali121619@gmail.com"]
    from_email = "tabishali121619@gmail.com"
    from_pswd = "aiox ybzb wcqm jkwo"
    for dest in li:
        try:
            import time
            message = MIMEMultipart()
            date_format = '%d-%m-%Y'
            current_time = time.strftime(date_format)
            message[
                "Subject"] = f"A new leave request needs admin approval. Leave ID: {leave.id}"
            message["From"] = from_email
            message["To"] = dest

            html = '''

<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="en">

<head>
	<title></title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0"><!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
	<style>
		* {
			box-sizing: border-box;
		}

		body {
			margin: 0;
			padding: 0;
		}

		a[x-apple-data-detectors] {
			color: inherit !important;
			text-decoration: inherit !important;
		}

		#MessageViewBody a {
			color: inherit;
			text-decoration: none;
		}

		p {
			line-height: inherit
		}

		.desktop_hide,
		.desktop_hide table {
			mso-hide: all;
			display: none;
			max-height: 0px;
			overflow: hidden;
		}

		.image_block img+div {
			display: none;
		}

		@media (max-width:670px) {

			.desktop_hide table.icons-inner,
			.social_block.desktop_hide .social-table {
				display: inline-block !important;
			}

			.icons-inner {
				text-align: center;
			}

			.icons-inner td {
				margin: 0 auto;
			}

			.image_block div.fullWidth {
				max-width: 100% !important;
			}

			.mobile_hide {
				display: none;
			}

			.row-content {
				width: 100% !important;
			}

			.stack .column {
				width: 100%;
				display: block;
			}

			.mobile_hide {
				min-height: 0;
				max-height: 0;
				max-width: 0;
				overflow: hidden;
				font-size: 0px;
			}

			.desktop_hide,
			.desktop_hide table {
				display: table !important;
				max-height: none !important;
			}

			.reverse {
				display: table;
				width: 100%;
			}

			.reverse .column.first {
				display: table-footer-group !important;
			}

			.reverse .column.last {
				display: table-header-group !important;
			}

			.row-3 td.column.first .border,
			.row-3 td.column.last .border {
				padding: 5px 20px;
				border-top: 0;
				border-right: 0px;
				border-bottom: 0;
				border-left: 0;
			}

			.row-1 .column-1 .block-5.image_block td.pad {
				padding: 25px 0 0 !important;
			}
		}
	</style>
</head>

<body style="background-color: #000000; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;">
	<table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #000000;">
		<tbody>
			<tr>
				<td>
					<table class="row row-1" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #000000; background-size: auto;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-size: auto; background-color: #000000; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="image_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-bottom:30px;padding-top:10px;width:100%;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div style="max-width: 167px;"><a href="http://www.example.com" target="_blank" style="outline:none" tabindex="-1"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/7466/Yourlogo_black.png" style="display: block; height: auto; border: 0; width: 100%;" width="167" alt="Your Logo" title="Your Logo"></a></div>
																</div>
															</td>
														</tr>
													</table>
													<table class="heading_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-bottom:5px;text-align:center;width:100%;">
																<h1 style="margin: 0; color: #ffffff; direction: ltr; font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 56px; font-weight: 700; letter-spacing: normal; line-height: 120%; text-align: center; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 67.2px;">Maximum innovation and technology</h1>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-3" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-bottom:20px;">
																<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:center;mso-line-height-alt:24px;">
																	<p style="margin: 0;">Lorem ipsum dolor sit amet, consectetur adipiscing elit. </p>
																</div>
															</td>
														</tr>
													</table>
													<table class="button_block block-4" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-bottom:15px;text-align:center;">
																<div class="alignment" align="center"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="http://www.example.com" style="height:52px;width:196px;v-text-anchor:middle;" arcsize="0%" stroke="false" fillcolor="#ffffff">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#000000; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://www.example.com" target="_blank" style="text-decoration:none;display:inline-block;color:#000000;background-color:#ffffff;border-radius:0px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:10px;padding-bottom:10px;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:25px;padding-right:25px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Know more about us</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
															</td>
														</tr>
													</table>
													<table class="image_block block-5" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-top:5px;width:100%;padding-right:0px;padding-left:0px;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div class="fullWidth" style="max-width: 422.5px;"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/7466/laptop-p.png" style="display: block; height: auto; border: 0; width: 100%;" width="422.5" alt="Laptop" title="Laptop"></div>
																</div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-2" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-size: auto;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-size: auto; background-color: #000000; border-radius: 0; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="image_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="width:100%;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div style="max-width: 285px;"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/7466/face1.png" style="display: block; height: auto; border: 0; width: 100%;" width="285" alt="Facebook" title="Facebook"></div>
																</div>
															</td>
														</tr>
													</table>
												</td>
												<td class="column column-2" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="social_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:left;padding-right:0px;padding-left:0px;">
																<div class="alignment" align="left">
																	<table class="social-table" width="36px" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block;">
																		<tr>
																			<td style="padding:0 4px 0 0;"><a href="https://www.facebook.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/facebook@2x.png" width="32" height="32" alt="Facebook" title="facebook" style="display: block; height: auto; border: 0;"></a></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="heading_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:center;width:100%;">
																<h1 style="margin: 0; color: #ffffff; direction: ltr; font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 38px; font-weight: 700; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 45.6px;"><span class="tinyMce-placeholder">Like us on Facebook</span></h1>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-3" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-bottom:20px;">
																<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:left;mso-line-height-alt:24px;">
																	<p style="margin: 0;">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
																</div>
															</td>
														</tr>
													</table>
													<table class="button_block block-4" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:left;">
																<div class="alignment" align="left"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="http://www.example.com" style="height:52px;width:117px;v-text-anchor:middle;" arcsize="0%" stroke="false" fillcolor="#ffffff">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#000000; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://www.example.com" target="_blank" style="text-decoration:none;display:inline-block;color:#000000;background-color:#ffffff;border-radius:0px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:10px;padding-bottom:10px;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:25px;padding-right:25px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Follow us</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-3" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-size: auto;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-size: auto; background-color: #000000; border-radius: 0; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr class="reverse">
												<td class="column column-1 first" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="border">
														<table class="social_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
															<tr>
																<td class="pad" style="text-align:left;padding-right:0px;padding-left:0px;">
																	<div class="alignment" align="left">
																		<table class="social-table" width="36px" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block;">
																			<tr>
																				<td style="padding:0 4px 0 0;"><a href="https://www.instagram.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/instagram@2x.png" width="32" height="32" alt="Instagram" title="Instagram" style="display: block; height: auto; border: 0;"></a></td>
																			</tr>
																		</table>
																	</div>
																</td>
															</tr>
														</table>
														<table class="heading_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
															<tr>
																<td class="pad" style="text-align:center;width:100%;">
																	<h1 style="margin: 0; color: #ffffff; direction: ltr; font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 38px; font-weight: 700; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 45.6px;"><span class="tinyMce-placeholder">Follow us on Instagram</span></h1>
																</td>
															</tr>
														</table>
														<table class="paragraph_block block-3" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
															<tr>
																<td class="pad" style="padding-bottom:20px;">
																	<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:left;mso-line-height-alt:24px;">
																		<p style="margin: 0;">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
																	</div>
																</td>
															</tr>
														</table>
														<table class="button_block block-4" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
															<tr>
																<td class="pad" style="text-align:left;">
																	<div class="alignment" align="left"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="http://www.example.com" style="height:52px;width:117px;v-text-anchor:middle;" arcsize="0%" stroke="false" fillcolor="#ffffff">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#000000; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://www.example.com" target="_blank" style="text-decoration:none;display:inline-block;color:#000000;background-color:#ffffff;border-radius:0px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:10px;padding-bottom:10px;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:25px;padding-right:25px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Follow us</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
																</td>
															</tr>
														</table>
													</div>
												</td>
												<td class="column column-2 last" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="border">
														<table class="image_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
															<tr>
																<td class="pad" style="width:100%;">
																	<div class="alignment" align="center" style="line-height:10px">
																		<div style="max-width: 285px;"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/7466/insta3.png" style="display: block; height: auto; border: 0; width: 100%;" width="285" alt="Instagram" title="Instagram"></div>
																	</div>
																</td>
															</tr>
														</table>
													</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-4" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #000000; border-radius: 0; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="image_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="width:100%;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div style="max-width: 285px;"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/7466/link1.png" style="display: block; height: auto; border: 0; width: 100%;" width="285" alt="LinkedIn" title="LinkedIn"></div>
																</div>
															</td>
														</tr>
													</table>
												</td>
												<td class="column column-2" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-left: 20px; padding-right: 20px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="social_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:left;padding-right:0px;padding-left:0px;">
																<div class="alignment" align="left">
																	<table class="social-table" width="36px" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block;">
																		<tr>
																			<td style="padding:0 4px 0 0;"><a href="https://www.linkedin.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/linkedin@2x.png" width="32" height="32" alt="LinkedIn" title="LinkedIn" style="display: block; height: auto; border: 0;"></a></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="heading_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:center;width:100%;">
																<h1 style="margin: 0; color: #ffffff; direction: ltr; font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 38px; font-weight: 700; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 45.6px;"><span class="tinyMce-placeholder">Like us on LinkedIn</span></h1>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-3" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-bottom:20px;">
																<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:left;mso-line-height-alt:24px;">
																	<p style="margin: 0;">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
																</div>
															</td>
														</tr>
													</table>
													<table class="button_block block-4" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:left;">
																<div class="alignment" align="left"><!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="http://www.example.com" style="height:52px;width:117px;v-text-anchor:middle;" arcsize="0%" stroke="false" fillcolor="#ffffff">
<w:anchorlock/>
<v:textbox inset="0px,0px,0px,0px">
<center style="color:#000000; font-family:Arial, sans-serif; font-size:16px">
<![endif]--><a href="http://www.example.com" target="_blank" style="text-decoration:none;display:inline-block;color:#000000;background-color:#ffffff;border-radius:0px;width:auto;border-top:0px solid transparent;font-weight:400;border-right:0px solid transparent;border-bottom:0px solid transparent;border-left:0px solid transparent;padding-top:10px;padding-bottom:10px;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:25px;padding-right:25px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="word-break: break-word; line-height: 32px;">Follow us</span></span></a><!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-5" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #000000; border-radius: 0; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:35px;line-height:35px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-6" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #000000; border-radius: 0; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="social_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="text-align:center;padding-right:0px;padding-left:0px;">
																<div class="alignment" align="center">
																	<table class="social-table" width="108px" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block;">
																		<tr>
																			<td style="padding:0 2px 0 2px;"><a href="https://www.facebook.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/facebook@2x.png" width="32" height="32" alt="Facebook" title="facebook" style="display: block; height: auto; border: 0;"></a></td>
																			<td style="padding:0 2px 0 2px;"><a href="https://www.linkedin.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/linkedin@2x.png" width="32" height="32" alt="Linkedin" title="linkedin" style="display: block; height: auto; border: 0;"></a></td>
																			<td style="padding:0 2px 0 2px;"><a href="https://www.instagram.com" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-only-logo-white/instagram@2x.png" width="32" height="32" alt="Instagram" title="instagram" style="display: block; height: auto; border: 0;"></a></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-bottom:5px;">
																<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:16px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:center;mso-line-height-alt:24px;">
																	<p style="margin: 0;">2022 © All rights reserved</p>
																</div>
															</td>
														</tr>
													</table>
													<table class="paragraph_block block-3" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-bottom:5px;padding-left:20px;padding-right:20px;">
																<div style="color:#ffffff;direction:ltr;font-family:Helvetica Neue, Helvetica, Arial, sans-serif;font-size:12px;font-weight:400;letter-spacing:0px;line-height:180%;text-align:center;mso-line-height-alt:21.6px;">
																	<p style="margin: 0;"><a href="http://example.com" target="_blank" style="text-decoration: none; color: #737172;" rel="noopener">Unsuscribe</a></p>
																</div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-7" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="icons_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="vertical-align: middle; color: #1e0e4b; font-family: 'Inter', sans-serif; font-size: 15px; padding-bottom: 5px; padding-top: 5px; text-align: center;">
																<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																	<tr>
																		<td class="alignment" style="vertical-align: middle; text-align: center;"><!--[if vml]><table align="center" cellpadding="0" cellspacing="0" role="presentation" style="display:inline-block;padding-left:0px;padding-right:0px;mso-table-lspace: 0pt;mso-table-rspace: 0pt;"><![endif]-->
																			<!--[if !vml]><!-->
																			<table class="icons-inner" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block; margin-right: -4px; padding-left: 0px; padding-right: 0px;" cellpadding="0" cellspacing="0" role="presentation"><!--<![endif]-->
																				<tr>
																					<td style="vertical-align: middle; text-align: center; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 6px;"><a href="http://designedwithbeefree.com/" target="_blank" style="text-decoration: none;"><img class="icon" alt="Beefree Logo" src="https://d1oco4z2z1fhwp.cloudfront.net/assets/Beefree-logo.png" height="32" width="34" align="center" style="display: block; height: auto; margin: 0 auto; border: 0;"></a></td>
																					<td style="font-family: 'Inter', sans-serif; font-size: 15px; font-weight: undefined; color: #1e0e4b; vertical-align: middle; letter-spacing: undefined; text-align: center;"><a href="http://designedwithbeefree.com/" target="_blank" style="color: #1e0e4b; text-decoration: none;">Designed with Beefree</a></td>
																				</tr>
																			</table>
																		</td>
																	</tr>
																</table>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
				</td>
			</tr>
		</tbody>
	</table><!-- End -->
</body>

</html>

'''
            part1 = MIMEText(html, "html")
            message.attach(part1)
            s = smtplib.SMTP(smtp_server, port)
            s.starttls()
            s.login(from_email, from_pswd)
            message = message.as_string()
            s.sendmail(from_email, dest, message)
            s.quit()
            print(dest, "SENT")
        except Exception as e:
            print(dest, f"FAILED *{str(e)}*")
    return "ALL OK"


@login_required(login_url='/login')
def editemployee(request, pk):
    user = request.user
    manager = Employee.objects.get(user=user)
    employee = Employee.objects.get(id=pk)
    if manager.role.role == 'Line Manager':
        pending_leaves = Leave.objects.filter(status='Pending')
        context = {'manager': manager,
                   'employee': employee,
                   'pending_leaves': pending_leaves.count(),
                   }
        return render(request, 'editEmployee.html', context)
    return render(request, 'editemployee.html')


def updateEmployee(request, pk):
    employee = Employee.objects.get(id=pk)
    if request.method == 'POST':
        employee.full_name = request.POST.get('full_name')
        employee.address = request.POST.get('address')
        employee.email = request.POST.get('email')
        employee.cnic = request.POST.get('cnic')
        employee.phone = request.POST.get('phone')
        employee.salary = request.POST.get('salary')
        employee.department = request.POST.get('department')
        employee.designation = request.POST.get('designation')
        if 'emp_img' in request.FILES:
            employee.image = request.FILES['emp_img']
        if 'emp_exp_doc' in request.FILES:
            employee.education = request.FILES['emp_exp_doc']
        if 'emp_edu_cert' in request.FILES:
            employee.educational_certificates = request.FILES['emp_edu_cert']
        if 'emp_edu_doc' in request.FILES:
            employee.experience_letter = request.FILES['emp_edu_doc']

        employee.save()
    return redirect('employee')


def employeeDetails(request, pk):
    user = request.user
    manager = Employee.objects.get(user=user)
    employee = Employee.objects.get(id=pk)
    if manager.role.role == 'Line Manager':
        pending_leaves = Leave.objects.filter(status='Pending')
        context = {
            "employeeDetails": employee,
            'manager': manager,
            'pending_leaves': pending_leaves.count(),
        }
        return render(request, "employeeDetails.html", context)
    else:
        return render(request, 'employeeDetails.html', context={'employeeDetails': employee})
