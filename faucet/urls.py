from django.conf.urls import url
from . import views

app_name = "faucet"

urlpatterns = [
    url(r'', views.request_neo, name='request_neo')
]
