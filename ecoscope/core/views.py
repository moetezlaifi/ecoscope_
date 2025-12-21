from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Site, RiskSnapshot


def home(request):
    # This must match your template path below
    return render(request, "core/dashboard.html")


def level(x: float) -> str:
    if x > 65:
        return "RED"
    if x >= 35:
        return "ORANGE"
    return "GREEN"


@require_GET
def api_sites(request):
    return JsonResponse(
        list(Site.objects.values("id", "name", "site_type", "lat", "lon")),
        safe=False
    )


@require_GET
def api_risk(request):
    h = int(request.GET.get("h", "24"))
    out = []

    for s in Site.objects.all():
        snap = RiskSnapshot.objects.filter(site=s, horizon_hours=h).order_by("-timestamp").first()
        if not snap:
            continue

        out.append({
            "name": s.name,
            "lat": s.lat,
            "lon": s.lon,

            "water_risk": float(snap.water_risk),
            "bio_risk": float(snap.bio_risk),

            "level_water": level(float(snap.water_risk)),
            "level_bio": level(float(snap.bio_risk)),

            "explain": snap.explain_json,
            "timestamp": snap.timestamp.isoformat(),
        })

    return JsonResponse(out, safe=False)
