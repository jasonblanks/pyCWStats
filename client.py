import sys, stat, os, re, time, base64, getpass, socket, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Email settings
mail_user = "email@email.com"
mail_pwd = "password"
FROM = 'email@email.com'
TO = ['email@email.com'] #must be a list
SUBJECT = "BETA TEST: GLSA Clearwell License update"


def send_email(gmail_user,gmail_pwd,FROM,TO,SUBJECT):
			msg = MIMEMultipart('alternative')
			msg['Subject'] = SUBJECT
			msg['From'] = FROM
			msg['To'] = ', '.join(TO)
			#msg['To'] = TO
			with open ("\\\\jason\\tmp\\lic_stat.txt", "r") as myTEXT:
				TEXT=myTEXT.read().replace('\n', '')


			#TEXT = open ("\\\\jason\\tmp\\lic_stat.txt", 'r')
			#TEXT = printl(ServerList)
			part1 = MIMEText(TEXT, 'html')
			msg.attach(part1)

			if TEXT != None:
				try:

					server = smtplib.SMTP("smtpout.server.com", 25) #or port 465 doesn't seem to work!
					server.ehlo()
					server.sendmail(FROM, TO, msg.as_string())
					server.close()
					print 'successfully sent the mail'
				except (RuntimeError, TypeError, NameError):

					pass

def start_job():
	startjob = open("\\\\jason\\tmp\\job_start", 'w')
	startjob.close
job = 1
start_job()
while job:
	time.sleep(10)
	def file_check():
		for f in os.listdir("\\\\jason\\tmp"):
			if f == "job_complete":
				try:
					time.sleep (5)
					os.remove("\\\\jason\\tmp\\job_complete")
				except:
					file_check()
  
  
  
				'''
				for f in os.listdir("\\\\jason\\tmp"):
				if f == "job_complete":
					send_email(mail_user,mail_pwd,FROM,TO,SUBJECT)
					try:
						os.remove("\\\\jason\\tmp\\job_complete")
					except:
						file = True
						while file:
						  for f in os.listdir("\\\\jason\\tmp"):
							if f == "job_complete":
								file = True
								break
							else:
								file = False

								os.remove("\\\\jason\\tmp\\job_complete")
				'''
				job = 0
				send_email(mail_user,mail_pwd,FROM,TO,SUBJECT)
				sys.exit()
	file_check()
