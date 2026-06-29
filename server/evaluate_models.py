#!/usr/bin/env python3
"""
ML Model Evaluation Pipeline
Comprehensive evaluation of the job matching ensemble model
Generates actual evaluation metrics from real model predictions
"""
import json
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GridSearchCV, KFold, train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.svm import SVR
    from sklearn.metrics import (
        mean_squared_error,
        mean_absolute_error,
        r2_score,
        median_absolute_error,
    )
    from xgboost import XGBRegressor
except Exception as exc:
    print(f"Missing ML dependency: {exc}", file=sys.stderr)
    sys.exit(1)


DATA_DIR = os.path.join(os.getcwd(), "datasets")
CAREER_PROFILES_PATH = os.path.join(DATA_DIR, "career_profiles.csv")
JOB_LISTINGS_PATH = os.path.join(DATA_DIR, "job_listings.csv")
EVAL_OUTPUT_DIR = os.path.join(os.getcwd(), "evaluation_results")
MODELS_DIR = os.path.join(os.getcwd(), "server", "models")

# Create directories if they don't exist
Path(EVAL_OUTPUT_DIR).mkdir(exist_ok=True)
Path(MODELS_DIR).mkdir(exist_ok=True)


def parse_pipe_list(value):
    """Parse pipe-separated values"""
    if pd.isna(value):
        return []
    return [part.strip().lower() for part in str(value).split("|") if part.strip()]


def normalize_location(value):
    """Normalize location strings"""
    return str(value or "").strip().lower()


def experience_to_numeric(value):
    """Convert experience level to numeric score"""
    value = str(value or "").strip().lower()
    mapping = {
        "entry": 0,
        "mid": 1,
        "senior": 2,
        "lead": 3,
        "manager": 3,
    }
    for key, score in mapping.items():
        if key in value:
            return score
    return 0


def build_features(profile, job):
    """Build feature vector from profile-job pair"""
    profile_skills = {skill.strip().lower() for skill in profile.get("technicalSkills", []) if skill}
    job_skills = {skill.strip().lower() for skill in parse_pipe_list(job.get("skillsRequired", ""))}

    shared_skills = profile_skills.intersection(job_skills)
    job_type = str(job.get("type", "")).strip().lower()
    profile_pref = str(profile.get("workPreference", "")).strip().lower()
    job_location = normalize_location(job.get("location"))
    profile_location = normalize_location(profile.get("location"))

    return {
        "profile_skill_count": len(profile_skills),
        "job_skill_count": len(job_skills),
        "shared_skill_count": len(shared_skills),
        "skill_overlap_ratio": len(shared_skills) / max(1, len(job_skills)),
        "prefers_remote": 1 if profile_pref == "remote" else 0,
        "job_is_remote": 1 if job_type == "remote" else 0,
        "job_is_hybrid": 1 if job_type == "hybrid" else 0,
        "job_is_onsite": 1 if job_type in ["on-site", "onsite", "on site"] else 0,
        "experience_distance": abs(
            experience_to_numeric(profile.get("experienceLevel")) - 
            experience_to_numeric(job.get("experience"))
        ),
        "location_match": 1 if profile_location and profile_location in job_location else 0,
        "headline_count": len(str(profile.get("headline", "")).split()),
    }


def build_match_label(profile, job):
    """Generate target label (match score 0-100) for profile-job pair"""
    job_skills = {skill.strip().lower() for skill in parse_pipe_list(job.get("skillsRequired", ""))}
    profile_skills = {skill.strip().lower() for skill in profile.get("technicalSkills", []) if skill}
    shared_count = len(profile_skills.intersection(job_skills))
    base_score = 100 * shared_count / max(1, len(job_skills))
    experience_match_bonus = 5 if experience_to_numeric(profile.get("experienceLevel")) == experience_to_numeric(job.get("experience")) else 0
    work_pref_bonus = 5 if (profile.get("workPreference", "")).strip().lower() == job.get("type", "").strip().lower() else 0
    return min(100.0, base_score + experience_match_bonus + work_pref_bonus)


def load_training_data():
    """Load and prepare training dataset"""
    if not os.path.exists(CAREER_PROFILES_PATH) or not os.path.exists(JOB_LISTINGS_PATH):
        raise FileNotFoundError("Required dataset files not found in datasets/ folder.")

    profiles = pd.read_csv(CAREER_PROFILES_PATH, keep_default_na=False)
    jobs = pd.read_csv(JOB_LISTINGS_PATH, keep_default_na=False)

    records = []
    for _, profile_row in profiles.iterrows():
        profile = {
            "technicalSkills": parse_pipe_list(profile_row.get("technicalSkills", "")),
            "experienceLevel": profile_row.get("experienceLevel", "Entry Level"),
            "workPreference": profile_row.get("workPreference", "Remote"),
            "location": profile_row.get("location", ""),
            "headline": profile_row.get("headline", ""),
        }

        for _, job_row in jobs.iterrows():
            job = job_row.to_dict()
            features = build_features(profile, job)
            features["label"] = build_match_label(profile, job)
            records.append(features)

    training_df = pd.DataFrame(records)
    if training_df.empty:
        raise ValueError("No training samples could be built from the dataset.")

    return training_df, profiles, jobs


def train_model(estimator, param_grid, X, y):
    """Train model with grid search and 5-fold CV"""
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    search = GridSearchCV(
        estimator, 
        param_grid, 
        cv=cv, 
        scoring="neg_mean_squared_error", 
        n_jobs=-1, 
        verbose=0
    )
    search.fit(X, y)
    return search.best_estimator_, search.best_params_


def evaluate_model(model, X_test, y_test, model_name):
    """Calculate evaluation metrics for a model"""
    y_pred = model.predict(X_test)
    
    metrics = {
        "model": model_name,
        "mse": mean_squared_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "mae": mean_absolute_error(y_test, y_pred),
        "median_ae": median_absolute_error(y_test, y_pred),
        "r2_score": r2_score(y_test, y_pred),
    }
    
    # For regression, calculate accuracy as percentage of predictions within ±10 match score
    within_10_pct = np.mean(np.abs(y_pred - y_test) <= 10) * 100
    metrics["accuracy_within_10"] = within_10_pct
    
    return metrics, y_pred


def perform_cross_validation(model, X, y, model_name, cv_folds=5):
    """Perform k-fold cross-validation"""
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="r2")
    cv_mse = -cross_val_score(model, X, y, cv=cv, scoring="neg_mean_squared_error")
    
    return {
        "model": model_name,
        "cv_folds": cv_folds,
        "r2_scores": cv_scores.tolist(),
        "r2_mean": float(cv_scores.mean()),
        "r2_std": float(cv_scores.std()),
        "mse_scores": cv_mse.tolist(),
        "mse_mean": float(cv_mse.mean()),
        "mse_std": float(cv_mse.std()),
    }


def generate_dataset_report(profiles_df, jobs_df, training_df):
    """Generate dataset statistics report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset_statistics": {
            "career_profiles_count": len(profiles_df),
            "job_listings_count": len(jobs_df),
            "total_training_samples": len(training_df),
            "expected_combinations": len(profiles_df) * len(jobs_df),
        },
        "career_profiles_columns": list(profiles_df.columns),
        "job_listings_columns": list(jobs_df.columns),
        "training_features": list(training_df.drop(columns=["label"]).columns),
        "target_label_statistics": {
            "mean": float(training_df["label"].mean()),
            "std": float(training_df["label"].std()),
            "min": float(training_df["label"].min()),
            "max": float(training_df["label"].max()),
            "median": float(training_df["label"].median()),
        }
    }
    return report


def main():
    """Main evaluation pipeline"""
    print("=" * 80)
    print("ML MODEL EVALUATION PIPELINE")
    print("=" * 80)
    
    try:
        # Load data
        print("\n[1/6] Loading training data...")
        training_df, profiles_df, jobs_df = load_training_data()
        print(f"✓ Loaded {len(training_df)} training samples")
        print(f"  - Career Profiles: {len(profiles_df)}")
        print(f"  - Job Listings: {len(jobs_df)}")
        
        # Generate dataset report
        print("\n[2/6] Generating dataset statistics...")
        dataset_report = generate_dataset_report(profiles_df, jobs_df, training_df)
        print(f"✓ Dataset Report: {json.dumps(dataset_report['dataset_statistics'], indent=2)}")
        
        # Split data
        print("\n[3/6] Splitting data (80/20 train-test)...")
        X = training_df.drop(columns=["label"])
        y = training_df["label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"✓ Training set: {len(X_train)} samples")
        print(f"✓ Test set: {len(X_test)} samples")
        
        # Train models
        print("\n[4/6] Training ensemble models (with GridSearchCV + 5-fold CV)...")
        
        print("  Training RandomForest...")
        rf_model, rf_params = train_model(
            RandomForestRegressor(random_state=42),
            {
                "n_estimators": [50, 100],
                "max_depth": [5, 10, None],
                "min_samples_split": [2, 5],
            },
            X_train,
            y_train,
        )
        print(f"  ✓ RandomForest best params: {rf_params}")

        print("  Training XGBoost...")
        xgb_model, xgb_params = train_model(
            XGBRegressor(random_state=42, verbosity=0, objective="reg:squarederror"),
            {
                "n_estimators": [50, 100],
                "max_depth": [3, 6],
                "learning_rate": [0.05, 0.1],
                "subsample": [0.7, 1.0],
            },
            X_train,
            y_train,
        )
        print(f"  ✓ XGBoost best params: {xgb_params}")

        print("  Training SVM Pipeline...")
        svm_model, svm_params = train_model(
            Pipeline([("scaler", StandardScaler()), ("svm", SVR())]),
            {
                "svm__kernel": ["rbf"],
                "svm__C": [0.5, 1.0, 2.0],
                "svm__gamma": ["scale", "auto"],
            },
            X_train,
            y_train,
        )
        print(f"  ✓ SVM best params: {svm_params}")

        # Evaluate on test set
        print("\n[5/6] Evaluating models on test set...")
        rf_metrics, rf_pred = evaluate_model(rf_model, X_test, y_test, "RandomForest")
        xgb_metrics, xgb_pred = evaluate_model(xgb_model, X_test, y_test, "XGBoost")
        svm_metrics, svm_pred = evaluate_model(svm_model, X_test, y_test, "SVM")
        
        # Ensemble evaluation
        ensemble_pred = np.mean([rf_pred, xgb_pred, svm_pred], axis=0)
        ensemble_metrics = {
            "model": "Ensemble",
            "mse": mean_squared_error(y_test, ensemble_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, ensemble_pred)),
            "mae": mean_absolute_error(y_test, ensemble_pred),
            "median_ae": median_absolute_error(y_test, ensemble_pred),
            "r2_score": r2_score(y_test, ensemble_pred),
            "accuracy_within_10": np.mean(np.abs(ensemble_pred - y_test) <= 10) * 100,
        }
        
        print("\nTest Set Evaluation Metrics:")
        for metrics in [rf_metrics, xgb_metrics, svm_metrics, ensemble_metrics]:
            print(f"\n{metrics['model']}:")
            print(f"  R² Score: {metrics['r2_score']:.4f}")
            print(f"  RMSE: {metrics['rmse']:.4f}")
            print(f"  MAE: {metrics['mae']:.4f}")
            print(f"  Accuracy (±10): {metrics['accuracy_within_10']:.2f}%")

        # Cross-validation
        print("\n[6/6] Performing 5-fold cross-validation...")
        cv_results = []
        for model, name in [(rf_model, "RandomForest"), (xgb_model, "XGBoost"), (svm_model, "SVM")]:
            cv_res = perform_cross_validation(model, X_train, y_train, name, cv_folds=5)
            cv_results.append(cv_res)
            print(f"\n{name} CV Results:")
            print(f"  R² Mean: {cv_res['r2_mean']:.4f} ± {cv_res['r2_std']:.4f}")
            print(f"  MSE Mean: {cv_res['mse_mean']:.4f} ± {cv_res['mse_std']:.4f}")

        # Save all results
        print("\n" + "=" * 80)
        print("SAVING EVALUATION RESULTS")
        print("=" * 80)
        
        evaluation_results = {
            "timestamp": datetime.now().isoformat(),
            "dataset_statistics": dataset_report["dataset_statistics"],
            "data_split": {
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "test_split_ratio": 0.2,
            },
            "model_hyperparameters": {
                "RandomForest": rf_params,
                "XGBoost": xgb_params,
                "SVM": svm_params,
            },
            "test_set_evaluation": {
                "RandomForest": {k: float(v) if isinstance(v, np.floating) else v for k, v in rf_metrics.items()},
                "XGBoost": {k: float(v) if isinstance(v, np.floating) else v for k, v in xgb_metrics.items()},
                "SVM": {k: float(v) if isinstance(v, np.floating) else v for k, v in svm_metrics.items()},
                "Ensemble": {k: float(v) if isinstance(v, np.floating) else v for k, v in ensemble_metrics.items()},
            },
            "cross_validation": cv_results,
        }
        
        # Save to JSON
        results_json_path = os.path.join(EVAL_OUTPUT_DIR, "evaluation_results.json")
        with open(results_json_path, "w") as f:
            json.dump(evaluation_results, f, indent=2)
        print(f"✓ Saved evaluation_results.json: {results_json_path}")
        
        # Save metrics to CSV for easy comparison
        metrics_list = [rf_metrics, xgb_metrics, svm_metrics, ensemble_metrics]
        metrics_df = pd.DataFrame(metrics_list)
        metrics_csv_path = os.path.join(EVAL_OUTPUT_DIR, "model_metrics.csv")
        metrics_df.to_csv(metrics_csv_path, index=False)
        print(f"✓ Saved model_metrics.csv: {metrics_csv_path}")
        
        # Save cross-validation results to CSV
        cv_df = pd.DataFrame([
            {
                "model": cv["model"],
                "cv_folds": cv["cv_folds"],
                "r2_mean": cv["r2_mean"],
                "r2_std": cv["r2_std"],
                "mse_mean": cv["mse_mean"],
                "mse_std": cv["mse_std"],
            }
            for cv in cv_results
        ])
        cv_csv_path = os.path.join(EVAL_OUTPUT_DIR, "cross_validation_results.csv")
        cv_df.to_csv(cv_csv_path, index=False)
        print(f"✓ Saved cross_validation_results.csv: {cv_csv_path}")
        
        # Save dataset statistics
        dataset_stats_path = os.path.join(EVAL_OUTPUT_DIR, "dataset_statistics.json")
        with open(dataset_stats_path, "w") as f:
            json.dump(dataset_report, f, indent=2)
        print(f"✓ Saved dataset_statistics.json: {dataset_stats_path}")
        
        print("\n" + "=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)
        print(f"\nAll results saved to: {EVAL_OUTPUT_DIR}")
        print("\nGenerated files:")
        print("  - evaluation_results.json (comprehensive results)")
        print("  - model_metrics.csv (test set metrics)")
        print("  - cross_validation_results.csv (5-fold CV results)")
        print("  - dataset_statistics.json (dataset info)")
        
        return 0

    except Exception as exc:
        print(f"\n✗ Error during evaluation: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
