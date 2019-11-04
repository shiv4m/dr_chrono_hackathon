from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from drchrono.forms import CheckInForm, UpdateInfoForm, CreateAppointmentForm
#84310429
from drchrono.utils import DoctorUtils, PatientUtils, AppointmentUtils, FormUtils, TimeUtils
import requests
import sqlite3

class SetupView(DoctorUtils, FormUtils, TimeUtils, AppointmentUtils, PatientUtils, TemplateView):
    """
    The beginning of the OAuth sign-in flow. Logs a user into the kiosk, and saves the token.
    """
    template_name = 'kiosk_setup.html'

class UpdateStatus(SetupView):
    def get(self, request,  **kwargs):
        print(type(self.kwargs['a_id']))
        app_id = int(str(self.kwargs['a_id'])[:-1])
        action = str(self.kwargs['a_id'])[-1]
        if action == '0':
            app_id = str(app_id).decode("utf-8")
            if self.update_appointment_status(id=app_id, data={'status':'In Session'}):
                self.save_end_timestamp(app_id)
                return redirect('/view-appointments/')
        elif action == '1':
            summary = request.GET['summary']
            p_id = request.GET['p_id']
            self.save_summary(p_id, summary)
            if self.update_appointment_status(id=app_id, data={'status':'Complete'}):
                return redirect('/view-appointments/')
        elif action == '2':
            if self.update_appointment_status(id=app_id, data={'status':'No Show'}):
                return redirect('/view-appointments/')


class DoctorWelcome(SetupView):
    
    template_name = 'doctor_welcome.html'

    def get_context_data(self, **kwargs):
        kwargs = super(DoctorWelcome, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        doctor_details = self.doctor_details()
        kwargs['doctor'] = doctor_details
        return kwargs

class AppointmentSchedule(DoctorWelcome, SetupView):

    template_name = 'view_appointment.html'

    def patients_with_appointments(self, appointments):
        patients_with_appointments = []
        for appointment in appointments:
            patient_object_from_local = self.get_patient_object(appointment['patient'])
            if not patient_object_from_local:
                patient_object = self.get_patient_by_id(appointment['patient'])
                print("updating from server")
                self.update_patient_object(patient_object['id'], patient_object)
            else:
                print("updating from local")
                patient_object = patient_object_from_local
            patient_object.update(appointment)
            summary = self.get_summary(patient_object['patient'])
            print(summary)
            patient_object.update({'summary': summary})
            patients_with_appointments.append(patient_object)
        return patients_with_appointments

    def get_context_data(self, **kwargs):
        kwargs = super(AppointmentSchedule, self).get_context_data(**kwargs)
        appointment_details = self.fetch_appointment()
        kwargs['appointments'] = self.patients_with_appointments(appointment_details)
        # if status == arrived: get time_stamp else, if status == no show display 0.00
        #if status == complete get time stamp difference, if status == insession return diff
        #else return 0.00
        print(kwargs['appointments'][0]['scheduled_time'], type(kwargs['appointments'][0]['scheduled_time']))
        app_ids = []
        for apps in kwargs['appointments']:
            app_ids.append(apps['id'])
        self.create_ts_for_all_appointments(app_ids)
        wait_t = {}  #kwargs[app] is array
        for ids in app_ids:
            wait_t[ids] = self.get_wait_time(ids)
        kwargs['wait_time'] = wait_t
        kwargs['avg_time'] = "%.2f" % (self.get_average_wait_time())
        return kwargs


class CheckInKiosk(SetupView):
    template_name = 'check_in.html'

    def get(self, request, **kwargs):
        error_code = int(self.kwargs['e_code'])
        form = CheckInForm()
        error = []
        success = []
        if error_code != 0 and error_code != 100:
            error += ['Sorry, Looks like you have no appointments today.', "Looks like something's wrong. Please try again."]
            error = [error[error_code-1]]
        elif error_code == 100:
            error = []
            avg_time= "%.2f" % (self.get_average_wait_time())
            success = ['You are all set. Have a seat! Currently, the average waiting time is '+ str(avg_time) +' minutes.']
        return render(request, self.template_name, {'form': form, 'error':error, 'success':success})

    def post(self, request, **kwargs):
        form = CheckInForm(request.POST)
        if form.is_valid():
            fname, lname, dob = self.collectCheckInData(form)
            patient_id = self.get_patient_details_with_first_last_dob(fname, lname, dob)
            if patient_id:
                url = "/update_information/" + str(patient_id)
                return redirect(url)
            else:
                return render(request, self.template_name, {'form': CheckInForm(), 'error': ["No matching records were found. Please check your name."]})
        elif form.errors:
            error = [str(value) for value in form.errors.values()]
            return render(request, self.template_name, {'form': CheckInForm(), 'error': error})

class UpdateInformation(SetupView):
    template_name ='update_demo.html'

    def get(self, request, error=None, **kwargs):
        patient_id = self.kwargs['iid']
        appointments_for_patient = self.check_if_patient_has_an_appointment(self.kwargs['iid'])
        if not appointments_for_patient:
            return redirect('/check-in-kiosk/1')

        patient_object = self.get_patient_by_id(patient_id)
        form = UpdateInfoForm(patient_object, appointments_for_patient)
        return render(request, self.template_name, {'form': form, 'error': error, 'patient':patient_object})

    def post(self, request, **kwargs):
        if request.POST:
            form = request.POST.dict()
            pat_data, appointment, app_data = self.collectUpdateInfoData(form)
            appointments_for_patient = self.check_if_patient_has_an_appointment(self.kwargs['iid'])
            appointment_id = appointments_for_patient[appointment]['id']
            if self.update_patient_details(idx=self.kwargs['iid'], data=pat_data) and self.update_appointment_status(id=appointment_id, data=app_data):
                print("details updated")
                self.save_start_timestamp(appointment_id)
                return redirect('/check-in-kiosk/100')
            elif form.errors:
                print("errors in form update")
                error = [str(value) for value in form.errors.values()]
                return redirect('check-in-kiosk/2')

class WalkInAppointment(SetupView):
    template_name = 'walk-in.html'

    def get(self, request, **kwargs):
        walk_in_code = self.kwargs['walk_in_code']

        if not int(walk_in_code):
            #render user info section
            slots = self.create_available_slots_for_new_appointments()
            #print(slots)
            form = CreateAppointmentForm(slots)
            return render(request, self.template_name, {'form': form})
        else:
            slot_time = request.session['app_time']
            self.create_appointment(walk_in_code, slot_time)
            return redirect('/walk-in-appointment/0/')
            #render book appointment slot section

    def post(self, request, **kwargs):
        if request.POST:
            form = request.POST.dict()
            patient_id, time = self.collectNewAppointment(form)
            if patient_id:
                request.session['app_time'] = time
                return redirect('/walk-in-appointment/'+str(patient_id))
            else:
                return render(request, self.template_name, {form: CreateAppointmentForm()})
           