from django.urls import path
from .views import home, api_sites, api_risk

urlpatterns = [
    path("", home, name="home"),
    path("api/sites", api_sites, name="api_sites"),
    path("api/risk", api_risk, name="api_risk"),
]
