from django.contrib import admin
from .models import Site, SiteSignal, RiskSnapshot

admin.site.register(Site)
admin.site.register(SiteSignal)
admin.site.register(RiskSnapshot)
