from social_django.models import UserSocialAuth
from drchrono.endpoints import DoctorEndpoint, AppointmentEndpoint, PatientEndpoint
from datetime import date, timedelta, datetime
import ast, time, random
import dateutil.parser as parser

class GetToken():

	def get_token(self):
		oauth_provider = UserSocialAuth.objects.get(provider='drchrono')
		access_token = oauth_provider.extra_data['access_token']
		return access_token

class DoctorUtils(GetToken):
	
	def doctor_details(self):
		access_token = self.get_token()
		api = DoctorEndpoint(access_token)
		return next(api.list())


class PatientUtils(GetToken):

	def update_patient_details(self, idx, data):
		api = PatientEndpoint(self.get_token())
		response = api.update(id=idx, data=data)
		if not response:
			return 1

	def get_patient_by_id(self, patientId):
		api = PatientEndpoint(self.get_token())
		return api.fetch(id=patientId)

	def get_patient_details_with_first_last_dob(self, fname, lname, dob):
		api = PatientEndpoint(self.get_token())
		for patients in api.list():
			if patients['first_name'] == fname and patients['last_name'] == lname and str(patients['date_of_birth']) == str(dob):
				return patients['id']

	def patient_dictionary(self):
		with open('patient.txt', 'r') as f:
			data = ast.literal_eval(f.read())
			f.close()
			return data

	def get_patient_object(self, patient_id):
		data = self.patient_dictionary()
		if patient_id in data:
			return data[patient_id]
		else:
			return 0

	def update_patient_object(self, key, value):
		data = self.patient_dictionary()
		data[key] = value
		with open('patient.txt', 'w') as f:
			f.write(str(data))
			f.close()

class AppointmentUtils(GetToken):

	def fetch_appointment(self, today=None):
		if not today:
			today = "2019-10-25"
		todays_date = date.today().strftime("%Y-%m-%d")
		api = AppointmentEndpoint(self.get_token())
		return api.list(date=today)

	def check_if_patient_has_an_appointment(self, patientId):
		all_appointments = self.fetch_appointment()
		appointments = []
		for a in all_appointments:
			if int(a['patient']) == int(patientId) and str(a['status']) != 'Arrived' and str(a['status']) != 'In Session' and str(a['status']) != 'Complete' and str(a['status']) != 'No Show':
				appointments.append(a)
		return appointments

	def update_appointment_status(self, id, data):
		api = AppointmentEndpoint(self.get_token())
		response = api.update(id=id, data=data)
		if not response:
			return 1

	def create_appointment(self, patientId, timeString):
		api = AppointmentEndpoint(self.get_token())
		s = str(date.today()) + " " + timeString
		print(s)
		ts = parser.parse(s)
		d = ts.isoformat()
		print(d)
		data = {
			'patient': patientId,
			'doctor': 252357,
			'duration': 30,
			'exam_room': 4,
			'office': 268772,
			'status': 'Confirmed',
			'scheduled_time': d
		}
		return api.create(data=data)

	def create_available_slots_for_new_appointments(self):
		apps = self.fetch_appointment(today="2019-11-04")
		times = set()
		ftr = [60, 1]
		for a in apps:
			t = a['scheduled_time'][11:16]
			times.add(sum([a*b for a,b in zip(ftr, map(int, t.split(':')))]))
		slots = []
		for i in range(540, 1021, random.choice([30, 45])):
			if i not in times:
				slots.append(str(timedelta(minutes=i)))
		return slots

	def summary_dictionary(self):
		with open('summary.txt', 'r') as f:
			data = ast.literal_eval(f.read())
			f.close()
			return data

	def save_summary(self, patientId, summary):
		data = self.summary_dictionary()
		data[patientId] = summary
		with open('summary.txt', 'w') as f:
			f.write(str(data))
			f.close()

	def get_summary(self, patientId):
		data = self.summary_dictionary()
		patientId = str(patientId).decode("utf-8")
		if patientId in data:
			print("yes")
			return data[patientId]
		return ''

class FormUtils():

	def collectCheckInData(self, form):
		fname = form.cleaned_data['fname']
		fname = fname[0].upper() + fname[1:]
		lname = form.cleaned_data['lname']
		lname = lname[0].upper() + lname[1:]
		dob = form.cleaned_data['dob']
		return fname, lname, dob
	
	def collectUpdateInfoData(self, form):
		pat_data = {}
		for field, value in form.items():
			if field == 'appointments': continue
			pat_data[field] = value
		return pat_data, int(form['appointments']), {'status':'Arrived'}

	def collectNewAppointment(self, form):
		time = form['slot']
		fname, lname, dob = form['fname'], form['lname'], form['dob']
		patient_id = self.get_patient_details_with_first_last_dob(fname, lname, dob)
		return patient_id, time

class TimeUtils():
	#everything in seconds
	def time_dictionary(self):
		with open('time_logs.txt', 'r') as f:
			data = f.read()
			if not data:
				return {}
			data = ast.literal_eval(data)
			f.close()
			return data

	def create_ts_for_all_appointments(self, app_ids):
		data = self.time_dictionary()
		for ids in app_ids:
			if ids not in data:
				data[ids] = [0, 0]

		with open('time_logs.txt', 'w') as f:
			f.write(str(data))
			f.close()

	def save_start_timestamp(self, app_id):
		data = self.time_dictionary()
		data[app_id] = [time.time(), 0]
		with open('time_logs.txt', 'w') as f:
			f.write(str(data))
			f.close()

	def get_wait_time(self, app_id):
		data = self.time_dictionary()
		if app_id in data:
			if data[app_id][0] != 0 and data[app_id][1] == 0:
				return (time.time() - data[app_id][0]) // 60
			else:
				return (data[app_id][1] - data[app_id][0]) // 60

	def save_end_timestamp(self, app_id):
		data = self.time_dictionary()
		data[app_id] = [data[app_id][0], time.time()]
		with open('time_logs.txt', 'w') as f:
			f.write(str(data))
			f.close()

	def get_average_wait_time(self):
		data = self.time_dictionary()
		t = 0
		for start, end in data.values():
			if start != 0 and end == 0:
				t += (time.time() - start) // 60
			else:
				t += (end - start) // 60
		return t / len(data)			