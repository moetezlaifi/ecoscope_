import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression

DATA_PATH = "../data/train_water_risk.csv"
MODEL_PATH = "core/ml/water_risk_model.pkl"

df = pd.read_csv(DATA_PATH)

# Features (must match your CSV header)
X = df[["plastic_score", "rain_mm_24", "temp_max_24", "ndvi", "runoff_factor", "land_risk"]]
y = df["event"]

model = LogisticRegression(max_iter=300)
model.fit(X, y)

joblib.dump(model, MODEL_PATH)

print(f"✅ Model trained on {len(df)} rows")
print(f"✅ Saved model to: {MODEL_PATH}")
print("Coefficients:", model.coef_[0])
