from django import forms
import datetime
from django.contrib import messages
import requests
from django.db import models

class CheckInForm(forms.Form):
	fname = forms.CharField(label="First Name", widget=forms.TextInput(attrs={'class': 'form-control'}))
	lname = forms.CharField(label="Last Name", widget=forms.TextInput(attrs={'class': 'form-control'}))
	dob = forms.DateField(initial=datetime.date.today, label="Date of Birth", widget=forms.TextInput(attrs={'class': 'form-control'}))

class UpdateInfoForm(forms.Form):

	def __init__(self, patient_object, appointment_schedules, *args, **kwargs):
		self.patient_object = patient_object if patient_object else []
		self.appoint = appointment_schedules if appointment_schedules else []
		super(UpdateInfoForm, self).__init__(*args, **kwargs)
		self.fields['appointments'].choices = [(idx, 'Appointment at ' + str(a['scheduled_time']).split("T")[0] + ' ' +str(a['scheduled_time']).split("T")[1]) for idx, a in enumerate(self.appoint)]
		for key in self.fields:
			if key == 'appointments': continue
			self.fields[key].initial = self.patient_object[key]
	

	email = forms.EmailField(label="Email ID", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	emergency_contact_name = forms.CharField(label="Emergency Contact Name", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	emergency_contact_phone = forms.CharField(label="Emergency Contact Phone", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	home_phone = forms.CharField(label="Home Phone", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	cell_phone = forms.CharField(label="Cell Phone", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	address = forms.CharField(label="Address", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	city = forms.CharField(label="City", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	state = forms.CharField(label="State", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
	zip_code = forms.CharField(label="Zip Code", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

	appointments = forms.MultipleChoiceField(
		required=True,
		widget=forms.RadioSelect(attrs={'class': 'custom-control custom-radio custom-control-input'}),
	)

class CreateAppointmentForm(forms.Form):

	def __init__(self, slots, *args, **kwargs):
		self.slots = slots
		#print(self.slots)
		super(CreateAppointmentForm, self).__init__(*args, **kwargs)
		self.fields['slot'] = forms.ChoiceField(
			choices=[(s, 'Appointment at ' + s) for s in self.slots]
			)
		#print(self.fields['slot'].choices)

	fname = forms.CharField(label="First Name", widget=forms.TextInput(attrs={'class': 'form-control'}))
	lname = forms.CharField(label="Last Name", widget=forms.TextInput(attrs={'class': 'form-control'}))
	dob = forms.DateField(initial=datetime.date.today, label="Date of Birth", widget=forms.TextInput(attrs={'class': 'form-control'}))
	slot = forms.MultipleChoiceField(
		required=True,
		widget=forms.RadioSelect(attrs={'class': 'custom-control custom-radio custom-control-input'}),
	)