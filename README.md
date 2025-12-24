# 🌍 EcoScope — Green AI for Environmental Prediction

EcoScope is a **CPU-only, zero-hardware AI platform** designed to **predict environmental risks** while keeping its **carbon footprint extremely low**.

Built during the Green AI hackathon by **RevolTech**, EcoScope demonstrates that **impactful AI does not require heavy infrastructure, GPUs, or IoT devices**.

---

## 🚀 What Does EcoScope Do?

EcoScope anticipates environmental risks **before** damage occurs by analyzing existing data sources.

It includes two complementary intelligence modes:

### 💧 HydroScope — Water Pollution Risk
Predicts the likelihood of pollution being transported through:
- Oueds
- Wetlands
- Coastal zones

**Prediction horizons:** 24h and 48h  
**Approach:** Lightweight Machine Learning (CPU-only)

---

### 🌿 BioScope — Biodiversity Stress
Estimates early-warning **habitat stress**, focusing on:
- Vegetation degradation
- Heat stress
- Rainfall extremes

**Approach:** Explainable ecological stress indices  
(No black-box AI)

---

## 🧠 How It Works (Technical Overview)

### Data Sources
- Satellite-derived indicators (NDVI)
- Plastic accumulation proxy
- Real-time weather forecasts (rainfall, temperature)
- Site-level environmental parameters (runoff, land risk)

### Intelligence Layer
- **HydroScope**
  - Machine Learning model (lightweight, explainable)
  - Outputs a pollution risk score (0–100)

- **BioScope**
  - Transparent stress-index model
  - Outputs a biodiversity stress score (0–100)

### Backend
- Django (Python)
- REST-style API for risk snapshots
- Django Admin to manage monitored sites

### Frontend
- Django Templates
- Leaflet.js for interactive mapping
- Chart.js for trends and indicators

---

## 🌱 Green AI by Design

EcoScope was intentionally designed to minimize environmental impact:

- ❌ No GPUs
- ❌ No IoT sensors
- ❌ No deep learning at runtime
- ✅ CPU-only inference
- ✅ Lightweight models
- ✅ No continuous retraining

### 🌍 Carbon Footprint
A full EcoScope prediction cycle (data ingestion + ML inference + visualization):

👉 **~0.01 g CO₂ equivalent per run**

That is **20–100× lower** than a single interaction with large generative AI models.

---

## 🗺️ Supported Site Types
EcoScope currently supports:
- `oued`
- `wetland`
- `coast`

Sites can be added and managed directly through the Django Admin interface.

---

## ⚙️ Installation (Local Demo)

```bash
git clone https://github.com/your-username/ecoscope.git
cd ecoscope
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
