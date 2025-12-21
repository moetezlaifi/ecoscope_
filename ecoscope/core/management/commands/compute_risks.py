from django.core.management.base import BaseCommand
from datetime import date
import joblib
import os

from core.models import Site, SiteSignal, RiskSnapshot
from core.weather import fetch_weather, next_hours

MODEL_PATH = "core/ml/water_risk_model.pkl"
FEATURES = ["plastic_score","rain_mm_24","temp_max_24","ndvi","runoff_factor","land_risk"]

class Command(BaseCommand):
    help = "Compute ML-based water pollution risk (24h horizon)."

    def handle(self, *args, **options):
        if not os.path.exists(MODEL_PATH):
            self.stdout.write(self.style.ERROR("❌ ML model not found. Train it first."))
            return

        model = joblib.load(MODEL_PATH)
        today = date.today()
        computed = 0

        for site in Site.objects.all():
            sig = (
                SiteSignal.objects.filter(site=site, date=today).first()
                or SiteSignal.objects.filter(site=site).order_by("-date").first()
            )
            if not sig:
                self.stdout.write(self.style.WARNING(f"Skip {site.name}: no signal"))
                continue

            try:
                w = fetch_weather(site.lat, site.lon)
                rain24, tmax24 = next_hours(w, 24)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Weather error for {site.name}: {e}"))
                continue

            X = [[
                sig.plastic_score,
                rain24,
                tmax24,
                sig.ndvi,
                site.runoff_factor,
                site.land_risk,
            ]]

            prob = float(model.predict_proba(X)[0][1])
            risk = prob * 100.0

            coef = model.coef_[0].tolist()
            explain = {
                "ml_probability": prob,
                "features": {
                    "plastic_score": sig.plastic_score,
                    "rain_mm_24": rain24,
                    "temp_max_24": tmax24,
                    "ndvi": sig.ndvi,
                    "runoff_factor": site.runoff_factor,
                    "land_risk": site.land_risk,
                },
                "feature_importance": {
                    FEATURES[i]: coef[i] for i in range(len(FEATURES))
                }
            }

            RiskSnapshot.objects.create(
                site=site,
                horizon_hours=24,
                water_risk=risk,
                explain_json=explain
            )

            computed += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Computed ML risk for {computed} sites"))
