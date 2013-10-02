import MySQLdb
import sys
import sys, stat, os, re, time, datetime
import xml.etree.ElementTree as ET
import base64, getpass, socket, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Email settings
mail_user = "email@email.com"
mail_pwd = "emailPassword"
FROM = 'email@email.com'
TO = ['email@email.com'] #must be a list
SUBJECT = "BETA TEST: GLSA Clearwell License update"

#These our or cpacity servers in a list
capacity = ["server1","server2","server3","server3"]
#These are our consumption based servers ina  list
consumption = ['server4','server5']

class Matter():
	def __init__(self,name):
		self.case = name
		self.used = 0
		
class Server():
	'This is the default Server Class, most of the work will be centered within this class'

	def __init__(self, host, Type):
		self.Matters = []
		self.GS_Matters = []
		self.UB_Matters = []
		self.License_Free = 0
		self.License_Used = 0
		self.License_Used_Percentage = 0
		self.License_Total = 0
		self.CW_Version = None
		self.databases = []
		self.host = host
		self.version = self.get_version()
		self.Type = Type
		self.expiry = None
		self.serviceTag = None

		#check cw version
		#change domain name if you need or remove all together
		if self.version == "V66":
			self.LICENSE_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V66\\license\\license.xml"
			self.LICENSE_USED_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V66\\license\\IndexByCapacity.cwss"
		elif self.version == "V711":
			self.LICENSE_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V711\\license\\current\\license.xml" #V711
			self.LICENSE_USED_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V711\\license\\IndexByCapacity.cwss" #711
		elif self.version == "V712":
			self.LICENSE_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V712\\license\\current\\license.xml" #V712
			self.LICENSE_USED_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V712\\license\\IndexByCapacity.cwss" #712
		elif self.version == "V713":
			self.LICENSE_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V713\\license\\current\\license.xml" #V713
			self.LICENSE_USED_FILE = "\\\\"+self.host+".ctecfts.com\\D$\\CW\\V713\\license\\IndexByCapacity.cwss" #713
		else:
			print "error: no match!"
		self.get_matters()
		self.get_license()
		self.get_expiry()
		self.get_serviceTag()
		self.get_expiry()
		#self.get_serviceTag()
		#self.get_expiry()
		

			
		#print self.Matters
		#is server cpacity? then get license info
	def used_check(self, default=None):
			for f in self.LIC_FILE_USED_LIST:
				try: 
					self.LICENSE_USED_FILE = f
					return self.LICENSE_USED_FILE
					
				except:
					continue
				else:
					break
	def get_version(self):
		db = MySQLdb.connect(host=self.host+".ctecfts.com", # your host, usually localhost
							 user="dbuser", # your username
							  passwd="password", # your password
							  db="esadb_lds_cluster_1") # name of the data base
		cur2 = db.cursor()
		cur2.execute("""select HOME_DIR FROM t_cluster_node""")
		for y in cur2.fetchall():
			#print y[0]
			if y[0] == "D:\CW\V66":
				return "V66"
			if y[0] == "D:\CW\V712":
				return "V712"
			if y[0] == "D:\CW\V711":
				return "V711"
			if y[0] == "D:\CW\V713":
				return "V713"
		
		#		grab version from db
		# defines: CW_Version

	def get_matters(self):
		self.get_databases()
		for i in self.databases:
			if (i.startswith("esadb_lds_case_")) and not (i.startswith("esadb_lds_case_group") or i.startswith("esadb_lds_case_appliance") or i.startswith("esadb_lds_case_temp")):
				db = MySQLdb.connect(host=self.host, # your host, usually localhost
							 user="dbuser", # your username
							  passwd="password", # your password
							  db=i) # name of the data base

				cur2 = db.cursor()
				cur2.execute("""select name FROM t_case""")
				for y in cur2.fetchall():
					self.Matters.append(y[0])
		for i in self.Matters:
			if i.startswith("GL"):

				self.GS_Matters.append(Matter(i))
			elif i.startswith("UB"):
				self.UB_Matters.append(i)
		#Grab matter list from db
		#defines: GS_matters, UB_matters, Matters
	
	def get_license(self):
		def get_total(root):
			for h in root[0]:
				if h.tag == "feature":
					for x in h:
						if x.text == "IndexByCapacity":
							for j in h:
								if j.tag == "props":
									for l in j:
										#print "\n\nClearwell total server license: "+l.attrib.get('value')
										value = (l.attrib.get('value'), "capacity")
										return value
						elif x.text == "IndexByConsumption":
							for j in h:
								if j.tag == "props":
									for l in j:
										#print "\n\nClearwell total server license: "+l.attrib.get('value')
										value = (l.attrib.get('value'), "consumption")			
										return value	
										
		def get_used(self, lic_quota):
			if self.Type == "capacity":
				CaseList = [('','','')]
				lic_quota2 = lic_quota
				for line in lic_quota:
					if not line.startswith("#") and not line.startswith("version") and not line.startswith("curBatchID"):
						line = line.rstrip('\n')
						line = line.split("=")
						CaseID = line[0].split("_")
						LineType = CaseID[0]
						CaseID = CaseID[1]
						#NewCase[2] = caseID[1]
						if not any(CaseID in c for c in CaseList):
								NewCase = ('','',CaseID)
								CaseList.append(NewCase)
						#print CaseList
						if LineType == "caseName":
							count = 0
							for x in CaseList:
								#print x[2] +" "+ CaseID
								if x[2] == CaseID:
									x2 = x
									CaseList.pop(count)
									x2 = list(x2)
									x2[0] = line[1]
									x2 = tuple(x2)
									CaseList.append(x2)									
								count = count + 1
						#NewCase[2] = caseID[1]
						elif LineType == "caseQuota":
							count = 0
							for x in CaseList:
								#print x[2] +" "+ CaseID
								if x[2] == CaseID:
									x2 = x
									CaseList.pop(count)
									x2 = list(x2)
									x2[1] = (int(line[1]) / (1024*1024*1024.0))
									x2[1] = round(x2[1],1)
									x2 = tuple(x2)
									CaseList.append(x2)									
								count = count + 1
				return CaseList
		def get_used_consuption():
			def get_databases(self, databases):
				db = MySQLdb.connect(host=self.host+".ctecfts.com", # your host, usually localhost
									 user="dbuser", # your username
									  passwd="password", # your password
									  db="esadb") # name of the data base

				# you must create a Cursor object. It will let
				#  you execute all the query you need
				cur = db.cursor() 

				# Use all the SQL you like
				cur.execute("show databases")

				# print all the first cell of all the rows
				for row in cur.fetchall() :
					#print row[0]
					databases.append(row[0])

			
			databases =[]
			result = ['','']
			get_databases(self, databases)
			cases = []
			for i in databases:
				if (i.startswith("esadb_lds_case_")) and not (i.startswith("esadb_lds_case_group") or i.startswith("esadb_lds_case_appliance") or i.startswith("esadb_lds_case_temp")):
					db = MySQLdb.connect(host=self.host+".ctecfts.com", # your host, usually localhost
								 user="dbuser", # your username
								  passwd="password", # your password
								  db=i) # name of the data base
					#cur.execute(""SELECT "NAME" FROM "+str(i)")
					cur2 = db.cursor()
					#cur2.execute("""select 'NAME' FROM t_case""")
					#print i prints source 
					cur2.execute("""select name FROM t_case""")
					for y in cur2.fetchall():
						result[0] = y[0]
					#cur2.execute("""select * FROM t_basicstat WHERE stattype = 'EMAIL_MESSAGES_ORIGINAL'""")
					#for k in cur2.fetchall():
						#print (float(k[4]) / (1024*1024*1024))
					cur2.execute("""select * FROM t_ds_meta_data_child_dbs""")
					for j in cur2.fetchall():
						if j[1].startswith("_lds_case_appliance_"):
							appliance = j[1]
							try:
								db2 = MySQLdb.connect(host=self.host+".ctecfts.com", # your host, usually localhost
											user="esadbuser", # your username
											passwd="esadbpassword", # your password
											db="esadb"+appliance) # name of the data base
								cur3 = db2.cursor()
								cur3.execute("""select * FROM t_indexstats""")
								hosted = 0
								for j in cur3.fetchall():
									if j[1].endswith("CRAWLED"):
										hosted = hosted + float(j[2])
								#print (hosted / (1024*1024*1024))
								if hosted < 1073741824:
									result[1] = str(round(hosted / (1024*1024),1))+"mb"
								else:
									result[1] = str(round(hosted / (1024*1024*1024),1))+"gb"
							except:
								pass
								#print "db was 0"
					cases.append([result[0], result[1]])
			return cases
						
		tree = ET.parse(self.LICENSE_FILE)
		root = tree.getroot()
		self.License_Total = int(get_total(root)[0]) / (1024*1024*1024.0)
		get_used_consuption()
		
		for matter in self.GS_Matters:
			cases = get_used(self,open(self.LICENSE_USED_FILE, "r" ))
			if self.Type == "capacity":
				for case in cases:
					if case[0] == matter.case:
						self.License_Used += case[1]
						matter.used += case[1]
			if self.Type == "consumption":
				cases = get_used_consuption()
				for case in cases:
					if case[0] == matter.case:
						#self.License_Used += case[1]
						matter.used = case[1]

				
	
	def get_databases(self):
		db = MySQLdb.connect(host=self.host+".ctecfts.com", # your host, usually localhost
							 user="dbuser", # your username
							  passwd="password", # your password
							  db="esadb") # name of the data base

		# you must create a Cursor object. It will let
		#  you execute all the query you need
		cur = db.cursor()

		# Use all the SQL you like
		cur.execute("show databases")

		# print all the first cell of all the rows
		for row in cur.fetchall() :
			#print row[0]
			self.databases.append(row[0])
			
	def get_serviceTag(self):
		tree = ET.parse(self.LICENSE_FILE)
		root = tree.getroot()
		serviceTag = None
		for h in root[0]:
			if h.tag == "feature":
				for x in h:
					if x.text == "System":
						for j in h:
							if j.tag == "props":
								for l in j:
									#print "\n\nClearwell total server license: "+l.attrib.get('value')
									if l.attrib.get('name') == "serviceTag":
										self.serviceTag = l.attrib.get('value')
									#return serviceTag
									
	def get_expiry(self):
		expiry = None
		tree = ET.parse(self.LICENSE_FILE)
		root = tree.getroot()
		for h in root[0]:
			if h.tag == "feature":
				for x in h:
					if x.text == "System":
						for j in h:
							if j.tag == "props":
								for l in j:
									#print "\n\nClearwell total server license: "+l.attrib.get('value')
									if l.attrib.get('name') == "expiry":
										self.expiry = l.attrib.get('value')
												

def send_email(ServerList,gmail_user,gmail_pwd,FROM,TO,SUBJECT):
			msg = MIMEMultipart('alternative')
			msg['Subject'] = SUBJECT
			msg['From'] = FROM
			msg['To'] = ', '.join(TO)
			#msg['To'] = TO
			def printl(ServerList):
				Trash = []
				capacity_sum = 0
				capacity_total = 0
				GS_consumption_sum = 0
				UB_consumption_sum = 0
				for server in ServerList:		
					if server.Type == "capacity":
						Trash.append("<br><br>Clearwell <b>Enterprise Capacity</b> server license ("+str(server.host)+"): Capacity: "+str(server.License_Total)+" GB | Used: "+str(server.License_Used)+" | version: "+str(server.version)+" GB | ServiceTag: "+str(server.serviceTag)+" | Expiration: "+str(server.expiry)+"<br>")
					if server.Type == "consumption":
						Trash.append("<br><br>Clearwell <b>KPMG Consumption</b> server license ("+str(server.host)+"): Used: "+str(server.License_Used)+" | version: "+str(server.version)+" GB | ServiceTag: "+str(server.serviceTag)+" | Expiration: "+str(server.expiry)+"<br>")
					Trash.append("<table height=\"20\">")	
					for x in server.GS_Matters:
						Trash.append("<tr style=\"max-height:5px\"><td valign=top style=\"max-height:5px;background-color:#FFA500;text-align:left;\">"+str(x.case)+"</td><td valign=top style=\"background-color:#FFA500;text-align:left;\">"+str(x.used)+"</td></tr>")

					Trash.append("</table>")
				f = "<br>"
				#f = "<img src=\"http://www.abbl.lu/sites/abbl.lu/files/wysiwyg/logo_KPMG.gif\"><br>Top Level Statistics:<br><br><br>Enterprise Licence Total: "+str(capacity_sum)+"<br>Enterprise Licence Total Used: "+str(capacity_total)+" %"+str(round(((capacity_total / capacity_sum)*100),1))+"<br>Enterprise Licence Remaining: "+str(capacity_sum - capacity_total)+" %"+str(round((((capacity_sum - capacity_total) / capacity_sum)*100),1))+"<br><br><br>KPMG GLSA Consumption Licence Total Used: "+str(GS_consumption_sum)+"<br>KPMG UBIS Consumption Licence Total Used: "+str(UB_consumption_sum)+"<br><br>"
				for l in Trash:
						f = f+"<br>"+l
				return f
			
			TEXT = printl(ServerList)
			part1 = MIMEText(TEXT, 'html')
			msg.attach(part1)

			# Prepare actual message
			#message = """"\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
			if TEXT != None:
				try:
					#server = smtplib.SMTP(SERVER)
					server = smtplib.SMTP("smtpserver.com", 25) #or port 465 doesn't seem to work!
					server.ehlo()
					#server.starttls()
					#server.login(gmail_user)
					#server.login(gmail_user, gmail_pwd)
					#server.sendmail(FROM, TO, message)
					server.sendmail(FROM, TO, msg.as_string())
					#server.quit()
					server.close()
					print 'successfully sent the mail'
				except (RuntimeError, TypeError, NameError):
					#print "failed to send mail"
					pass

def print_to_share(ServerList):
			def printl(ServerList):
				Trash = []
				capacity_sum = 0
				capacity_total = 0
				GS_consumption_sum = 0
				UB_consumption_sum = 0
				for server in ServerList:		
					if server.Type == "capacity":
						Trash.append("<br><br>Clearwell <b>Enterprise Capacity</b> server license ("+str(server.host)+"):<br>Capacity: "+str(server.License_Total)+" GB | Used: "+str(server.License_Used)+" | remaining: "+str((int(server.License_Total) - int(server.License_Used)))+" GB | version: "+str(server.version)+" | ServiceTag: "+str(server.serviceTag)+" | Expiration: "+str(server.expiry)+"<br>")
					if server.Type == "consumption":
						Trash.append("<br><br>Clearwell <b>KPMG Consumption</b> server license ("+str(server.host)+"):<br>Used: "+str(server.License_Used)+" GB | version: "+str(server.version)+" | ServiceTag: "+str(server.serviceTag)+" | Expiration: "+str(server.expiry)+"<br>")
					Trash.append("<table height=\"20\">")	
					for x in server.GS_Matters:
						Trash.append("<tr style=\"max-height:5px\"><td valign=top style=\"max-height:5px;background-color:#FFA500;text-align:left;\">"+str(x.case)+"</td><td valign=top style=\"background-color:#FFA500;text-align:left;\">"+str(x.used)+"</td></tr>")

					Trash.append("</table>")
				f = "<br>"
				#f = "<img src=\"http://www.abbl.lu/sites/abbl.lu/files/wysiwyg/logo_KPMG.gif\"><br>Top Level Statistics:<br><br><br>Enterprise Licence Total: "+str(capacity_sum)+"<br>Enterprise Licence Total Used: "+str(capacity_total)+" %"+str(round(((capacity_total / capacity_sum)*100),1))+"<br>Enterprise Licence Remaining: "+str(capacity_sum - capacity_total)+" %"+str(round((((capacity_sum - capacity_total) / capacity_sum)*100),1))+"<br><br><br>KPMG GLSA Consumption Licence Total Used: "+str(GS_consumption_sum)+"<br>KPMG UBIS Consumption Licence Total Used: "+str(UB_consumption_sum)+"<br><br>"
				for l in Trash:
						f = f+"<br>"+l
				return f
			
			TEXT = printl(ServerList)
			out = open ("\\\\tmp\\lic_stat.txt", 'w')
			out.write(TEXT)
			out.close
			
			finish = open("\\\\tmp\\job_complete", 'w')
			finish.close
			
		

print str(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
while 1:
	time.sleep (10)
	def file_check():
		for f in os.listdir("\\\\tmp"):
			if f == "job_start":
				try:
					print "job started: "+str(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
					time.sleep (5)
					os.remove("\\\\tmp\\job_start")
				except:
					file_check()
					break
						
				ServerList = []
				for server in capacity:
					Type = "capacity"
					#print server
					new = Server(server, Type)
					#print new.Matters
					#print new.License_Total
					#print new.License_Used
					
					#for i in new.GS_Matters:
					#	print i.case +" "+ str(i.used)
					#print new.UB_Matters
					ServerList.append(new)
					
				for server in consumption:
					#print server
					Type = "consumption"
					new = Server(server, Type)
					#print new.Matters
					#print new.License_Total
					#print new.License_Used
					#for i in new.GS_Matters:
					#	print i.case +" "+ str(i.used)
					ServerList.append(new)

				#send_email(ServerList,mail_user,mail_pwd,FROM,TO,SUBJECT)
				print_to_share(ServerList)
				print "job complete: "+str(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
	file_check()
