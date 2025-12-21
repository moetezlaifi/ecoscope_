from django.db import models

class Site(models.Model):
    OUED = "OUED"
    WETLAND = "WETLAND"
    COAST = "COAST"
    SITE_TYPES = [(OUED, "Oued"), (WETLAND, "Wetland"), (COAST, "Coast")]

    name = models.CharField(max_length=120)
    site_type = models.CharField(max_length=10, choices=SITE_TYPES, default=OUED)
    lat = models.FloatField()
    lon = models.FloatField()

    runoff_factor = models.FloatField(default=0.5)   # 0..1
    land_risk = models.FloatField(default=0.3)       # 0..1

    def __str__(self):
        return self.name


class SiteSignal(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="signals")
    date = models.DateField()

    plastic_score = models.FloatField(default=0.0)  # 0..1
    ndvi = models.FloatField(default=0.3)           # 0..1

    class Meta:
        unique_together = ("site", "date")


class RiskSnapshot(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="snapshots")
    timestamp = models.DateTimeField(auto_now_add=True)
    horizon_hours = models.IntegerField(default=24)

    water_risk = models.FloatField()  # 0..100 (ML probability * 100)
    bio_risk = models.FloatField(default=0.0)
    
    explain_json = models.JSONField(default=dict)
