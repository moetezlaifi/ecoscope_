from django.core.management.base import BaseCommand
from datetime import date
import os
import joblib

from core.models import Site, SiteSignal, RiskSnapshot
from core.weather import fetch_weather, next_hours

MODEL_PATH = "core/ml/water_risk_model.pkl"
FEATURES = ["plastic_score", "rain_mm_24", "temp_max_24", "ndvi", "runoff_factor", "land_risk"]


class Command(BaseCommand):
    help = "Compute HydroScope (ML water risk) + BioScope (biodiversity stress) for each site."

    def handle(self, *args, **options):
        if not os.path.exists(MODEL_PATH):
            self.stdout.write(self.style.ERROR(f"❌ Model not found: {MODEL_PATH}"))
            self.stdout.write("Run: python core\\ml\\train_water_model.py")
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
                self.stdout.write(self.style.WARNING(f"Skip {site.name}: no SiteSignal"))
                continue

            # ---- Weather (real data) ----
            try:
                w = fetch_weather(site.lat, site.lon)
                rain24, tmax24 = next_hours(w, 24)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Weather error for {site.name}: {e}"))
                continue

            # =========================
            # HydroScope (ML prediction)
            # =========================
            X = [[
                float(sig.plastic_score),
                float(rain24),
                float(tmax24),
                float(sig.ndvi),
                float(site.runoff_factor),
                float(site.land_risk),
            ]]

            prob = float(model.predict_proba(X)[0][1])
            water_risk = prob * 100.0

            coef = model.coef_[0].tolist()
            water_explain = {
                "ml_probability": prob,
                "features": {
                    "plastic_score": float(sig.plastic_score),
                    "rain_mm_24": float(rain24),
                    "temp_max_24": float(tmax24),
                    "ndvi": float(sig.ndvi),
                    "runoff_factor": float(site.runoff_factor),
                    "land_risk": float(site.land_risk),
                },
                "feature_importance": {FEATURES[i]: float(coef[i]) for i in range(len(FEATURES))}
            }

            # =========================
            # BioScope (Explainable MVP)
            # =========================
            ndvi = float(sig.ndvi)     # 0..1
            temp = float(tmax24)       # °C
            rain = float(rain24)       # mm

            # Normalized stress components (0..1)
            ndvi_stress = max(0.0, min(1.0, (0.35 - ndvi) / 0.35))        # low NDVI => stress
            heat_stress = max(0.0, min(1.0, (temp - 30.0) / 12.0))        # >30 => stress
            rain_extreme = max(0.0, min(1.0, abs(rain - 10.0) / 25.0))    # far from ~10mm => stress

            bio_prob = 0.45 * ndvi_stress + 0.35 * heat_stress + 0.20 * rain_extreme
            bio_risk = bio_prob * 100.0

            bio_explain = {
                "signals": {"ndvi": ndvi, "temp_max_24": temp, "rain_mm_24": rain},
                "components": {
                    "ndvi_stress": ndvi_stress,
                    "heat_stress": heat_stress,
                    "rain_extreme": rain_extreme,
                },
                "bio_probability": bio_prob
            }

            # ---- Save snapshot with BOTH modes ----
            RiskSnapshot.objects.create(
                site=site,
                horizon_hours=24,
                water_risk=water_risk,
                bio_risk=bio_risk,
                explain_json={"water": water_explain, "bio": bio_explain},
            )

            computed += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Done. Computed Hydro+Bio for {computed} sites."))
