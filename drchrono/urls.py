from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import admin
admin.autodiscover()

import views


urlpatterns = [
    url(r'^setup/$', views.SetupView.as_view(), name='setup'),
    url(r'^welcome/$', views.DoctorWelcome.as_view(), name='setup'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^view-appointments/$', views.AppointmentSchedule.as_view(), name='view-appointments'),
    url(r'^check-in-kiosk/(?P<e_code>\d+)/$', views.CheckInKiosk.as_view(), name='check-in-kiosk'),
    url(r'^update_information/(?P<iid>\d+)/$', views.UpdateInformation.as_view(), name='update_information'),
    url(r'^update_status/(?P<a_id>\d+)/$', views.UpdateStatus.as_view(), name='update_status'),
    url(r'^walk-in-appointment/(?P<walk_in_code>\d+)/$', views.WalkInAppointment.as_view(), name='walk-in-appointment'),
]