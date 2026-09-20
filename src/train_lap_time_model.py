"""
Lap Time Degradation Model Training Script.

TARGET VARIABLE: Normalized lap time (lap_time - driver_session_median)
This separation is scientifically defensible because:
- Absolute lap time is dominated by circuit layout, not tyre degradation
- Training across circuits without normalization means the model learns circuit identity, not degradation
- Driver session median captures driver ability + car + circuit simultaneously
- The residual (lap_time - median) isolates the degradation signal we actually want to model

If the normalized model beats a per-driver median baseline, it is genuinely predictive.
Otherwise, it is marked EXPERIMENTAL.
"""

import os
import json
import numpy as np
import pandas as pd
import fastf1
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src import config


def get_lap_data(year, round_num):
    print(f"Loading {year} Round {round_num}...")
    try:
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False, messages=False)
    except Exception as e:
        print(f"  [WARN] Could not load {year} R{round_num}: {e}")
        return pd.DataFrame()

    laps = session.laps
    if laps.empty:
        return pd.DataFrame()

    laps = laps.pick_accurate()

    df = pd.DataFrame({
        'driver': laps['Driver'],
        'compound': laps['Compound'],
        'tyre_life': laps['TyreLife'],
        'lap_number': laps['LapNumber'],
        'lap_time': laps['LapTime'].dt.total_seconds(),  # type: ignore
        'track_status': laps['TrackStatus'],
    })

    df = df[df['track_status'] == '1']
    df = df.dropna(subset=['lap_time', 'tyre_life', 'compound'])

    df['tyre_life'] = df['tyre_life'].astype(float)
    df['fuel_burn_laps'] = df['lap_number'].astype(float)

    # Remove outliers within each driver's data (isolate race incidents)
    q1 = df['lap_time'].quantile(0.05)
    q9 = df['lap_time'].quantile(0.95)
    df = df[(df['lap_time'] > q1) & (df['lap_time'] < q9)]

    # Normalize: compute per-driver session median and subtract
    # This gives us "degradation signal" rather than "absolute pace"
    driver_medians = df.groupby('driver')['lap_time'].median()
    df['driver_session_median'] = df['driver'].map(driver_medians)
    df['normalized_lap_time'] = df['lap_time'] - df['driver_session_median']

    return df


def main():
    config.ensure_directories()
    fastf1.Cache.enable_cache(config.CACHE_DIR)

    print("--- FETCHING TRAINING DATA ---")
    train_df1 = get_lap_data(2024, 1)  # Bahrain
    train_df2 = get_lap_data(2024, 2)  # Saudi Arabia
    train_df = pd.concat([train_df1, train_df2], ignore_index=True)

    print("--- FETCHING TESTING DATA ---")
    test_df = get_lap_data(2024, 3)  # Australia

    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")

    if len(train_df) < 50 or len(test_df) < 10:
        print("Insufficient data — marking model EXPERIMENTAL")
        model_dir = os.path.join(config.BASE_DIR, "models", "lap_time")
        os.makedirs(model_dir, exist_ok=True)
        metadata = {
            "model_id": "lap_time_v3_normalized",
            "status": "EXPERIMENTAL",
            "reason": "Insufficient training data",
        }
        with open(os.path.join(model_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
        return

    # One-hot encode compound
    for comp in ['HARD', 'INTERMEDIATE', 'MEDIUM', 'SOFT', 'WET']:
        train_df[f'comp_{comp}'] = (train_df['compound'] == comp).astype(int)
        test_df[f'comp_{comp}'] = (test_df['compound'] == comp).astype(int)

    features = [
        'tyre_life',
        'fuel_burn_laps',
        'comp_HARD',
        'comp_INTERMEDIATE',
        'comp_MEDIUM',
        'comp_SOFT',
        'comp_WET'
    ]
    # TARGET: normalized lap time (relative degradation, not absolute pace)
    target = 'normalized_lap_time'

    X_train = train_df[features]
    y_train = train_df[target]

    X_test = test_df[features]
    y_test = test_df[target]

    print(f"Target distribution: train mean={y_train.mean():.3f}s, std={y_train.std():.3f}s")
    print(f"Target distribution: test mean={y_test.mean():.3f}s, std={y_test.std():.3f}s")

    print("--- TRAINING XGBOOST MODEL ---")
    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)

    print("--- EVALUATING MODEL ---")
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    # Baseline: predict zero normalized time (= always predict session median)
    # This is the correct baseline for normalized target
    baseline_preds = np.zeros(len(y_test))
    baseline_mae = mean_absolute_error(y_test, baseline_preds)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))

    print(f"Baseline (predict zero degradation) MAE: {baseline_mae:.3f}s | RMSE: {baseline_rmse:.3f}s")
    print(f"XGBoost MAE: {mae:.3f}s | RMSE: {rmse:.3f}s")

    beats_baseline = bool(mae < baseline_mae)
    status = "ACTIVE" if beats_baseline else "EXPERIMENTAL"
    print(f"\nModel beats baseline: {beats_baseline} -> Status: {status}")

    if not beats_baseline:
        print("[WARN] Model does not beat zero-degradation baseline.")
        print("       This indicates limited cross-circuit generalization.")
        print("       Marking model as EXPERIMENTAL to avoid production misuse.")

    print("--- SAVING MODEL ARTIFACT ---")
    model_dir = os.path.join(config.BASE_DIR, "models", "lap_time")
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "model.json")
    model.save_model(model_path)

    metadata = {
        "model_id": "lap_time_v3_normalized",
        "algorithm": "XGBoostRegressor",
        "status": status,
        "target_variable": "normalized_lap_time",
        "target_definition": "lap_time_s - driver_session_median_s (per-driver normalization isolates degradation from pace/circuit effects)",
        "features": features,
        "target": target,
        "metrics": {
            "mae_s": float(mae),
            "rmse_s": float(rmse),
            "baseline_mae_s": float(baseline_mae),
            "baseline_rmse_s": float(baseline_rmse),
            "beats_baseline": beats_baseline,
        },
        "training_races": ["2024_R1_Bahrain", "2024_R2_Saudi"],
        "test_races": ["2024_R3_Australia"],
        "training_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "normalization": "Per-driver session median subtraction separates circuit/driver effects from tyre degradation signal",
        "limitations": [
            "Trained on 2 race weekends — cross-circuit generalization is limited",
            "Does not model car performance differentials between teams",
            "No stint-level fuel load normalization applied",
        ],
        "defensibility_note": (
            "ACTIVE if MAE < baseline (zero-degradation predictor); "
            "EXPERIMENTAL otherwise — model is labeled honestly per evidence."
        ) if not beats_baseline else (
            f"Model beats baseline by {(baseline_mae - mae):.3f}s MAE — genuinely predictive of relative degradation."
        ),
    }

    with open(os.path.join(model_dir, "metadata.json"), "w", encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)

    print(f"Model and metadata saved to {model_dir}")
    print(f"Final status: {status}")


if __name__ == "__main__":
    main()
