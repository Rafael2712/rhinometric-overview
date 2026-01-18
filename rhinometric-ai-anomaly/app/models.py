"""
Machine Learning Models
Multiple algorithms for anomaly detection
"""
import os
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pickle
import gzip

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from scipy import stats

from app.config import ModelConfig

logger = logging.getLogger(__name__)


class AnomalyModel:
    """Base class for anomaly detection models"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.trained = False
        self.scaler = StandardScaler()
        self.last_trained: Optional[datetime] = None
    
    def train(self, X: np.ndarray) -> bool:
        """
        Train the model
        
        Args:
            X: Training data
            
        Returns:
            True if training successful
        """
        raise NotImplementedError
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies
        
        Args:
            X: Data to predict
            
        Returns:
            Array of predictions (-1 = anomaly, 1 = normal)
        """
        raise NotImplementedError
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores
        
        Args:
            X: Data to score
            
        Returns:
            Array of anomaly scores
        """
        raise NotImplementedError
    
    def needs_retraining(self, hours_since_last: float) -> bool:
        """Check if model needs retraining"""
        if not self.trained:
            return True
        if self.last_trained is None:
            return True
        return hours_since_last >= 6  # Retrain every 6 hours


class IsolationForestModel(AnomalyModel):
    """Isolation Forest anomaly detector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("isolation_forest", config)
        # Read contamination from env var with fallback to config
        contamination = float(os.getenv("ANOMALY_CONTAMINATION", config.get("contamination", 0.1)))
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=config.get("n_estimators", 100),
            max_samples=config.get("max_samples", "auto"),
            random_state=config.get("random_state", 42),
            n_jobs=config.get("n_jobs", -1)
        )
    
    def train(self, X: np.ndarray) -> bool:
        """Train Isolation Forest"""
        try:
            # Scale data
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled)
            self.trained = True
            self.last_trained = datetime.now()
            
            logger.info(f"Isolation Forest trained with {len(X)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training Isolation Forest: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores (lower = more anomalous)"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.score_samples(X_scaled)


class LOFModel(AnomalyModel):
    """Local Outlier Factor anomaly detector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("lof", config)
        # Read from env vars with fallback to config
        n_neighbors = int(os.getenv("ANOMALY_LOF_NEIGHBORS", config.get("n_neighbors", 20)))
        contamination = float(os.getenv("ANOMALY_CONTAMINATION", config.get("contamination", 0.1)))
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=config.get("novelty", True)
        )
    
    def train(self, X: np.ndarray) -> bool:
        """Train LOF model"""
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            self.trained = True
            self.last_trained = datetime.now()
            
            logger.info(f"LOF trained with {len(X)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training LOF: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.score_samples(X_scaled)


class OneClassSVMModel(AnomalyModel):
    """One-Class SVM anomaly detector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ocsvm", config)
        self.model = OneClassSVM(
            kernel=config.get("kernel", "rbf"),
            gamma=config.get("gamma", "auto"),
            nu=config.get("nu", 0.1)
        )
    
    def train(self, X: np.ndarray) -> bool:
        """Train One-Class SVM"""
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            self.trained = True
            self.last_trained = datetime.now()
            
            logger.info(f"One-Class SVM trained with {len(X)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training One-Class SVM: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.decision_function(X_scaled)


class StatisticalModel(AnomalyModel):
    """Statistical methods for anomaly detection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("statistical", config)
        # Read from env var with fallback to config
        self.zscore_threshold = float(os.getenv("ANOMALY_ZSCORE_THRESHOLD", config.get("zscore_threshold", 3.0)))
        self.moving_avg_window = config.get("moving_avg_window", 12)
        self.ema_alpha = config.get("ema_alpha", 0.3)
        self.mean = None
        self.std = None
    
    def train(self, X: np.ndarray) -> bool:
        """Calculate statistics"""
        try:
            self.mean = np.mean(X)
            self.std = np.std(X)
            self.trained = True
            self.last_trained = datetime.now()
            
            logger.info(f"Statistical model updated: mean={self.mean:.2f}, std={self.std:.2f}")
            return True
        except Exception as e:
            logger.error(f"Error training statistical model: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using Z-score"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        z_scores = np.abs((X - self.mean) / (self.std + 1e-10))
        predictions = np.where(z_scores > self.zscore_threshold, -1, 1)
        return predictions
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Get Z-scores (inverted so lower = more anomalous)"""
        if not self.trained:
            raise ValueError("Model not trained")
        
        z_scores = np.abs((X - self.mean) / (self.std + 1e-10))
        return -z_scores  # Invert so lower = more anomalous


class ModelEnsemble:
    """Ensemble of multiple anomaly detection models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.models: Dict[str, AnomalyModel] = {}
        
        # Initialize enabled models
        if config.isolation_forest.get("enabled", True):
            self.models["isolation_forest"] = IsolationForestModel(
                config.isolation_forest
            )
        
        if config.lof.get("enabled", True):
            self.models["lof"] = LOFModel(config.lof)
        
        if config.ocsvm.get("enabled", False):
            self.models["ocsvm"] = OneClassSVMModel(config.ocsvm)
        
        if config.statistical.get("enabled", True):
            self.models["statistical"] = StatisticalModel(config.statistical)
        
        logger.info(f"Model ensemble initialized with {len(self.models)} models")
    
    def train_all(self, X: np.ndarray) -> Dict[str, bool]:
        """
        Train all models
        
        Args:
            X: Training data
            
        Returns:
            Dictionary of model names and training success
        """
        results = {}
        X_reshaped = X.reshape(-1, 1)
        
        for name, model in self.models.items():
            try:
                success = model.train(X_reshaped)
                results[name] = success
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                results[name] = False
        
        return results
    
    def detect_anomalies(
        self,
        X: np.ndarray,
        model_names: Optional[List[str]] = None,
        voting: str = "soft"
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Detect anomalies using ensemble
        
        Args:
            X: Data to analyze
            model_names: List of model names to use (None = all)
            voting: "soft" (scores) or "hard" (predictions)
            
        Returns:
            Tuple of (final_predictions, individual_scores)
        """
        X_reshaped = X.reshape(-1, 1)
        
        # Select models
        if model_names:
            selected_models = {
                name: model for name, model in self.models.items()
                if name in model_names and model.trained
            }
        else:
            selected_models = {
                name: model for name, model in self.models.items()
                if model.trained
            }
        
        if not selected_models:
            logger.warning("No trained models available")
            return np.ones(len(X)), {}
        
        # Get predictions from each model
        predictions = {}
        scores = {}
        
        for name, model in selected_models.items():
            try:
                predictions[name] = model.predict(X_reshaped)
                scores[name] = model.score(X_reshaped)
            except Exception as e:
                logger.error(f"Error predicting with {name}: {e}")
                continue
        
        if not predictions:
            return np.ones(len(X)), {}
        
        # Ensemble voting
        if voting == "hard":
            # Majority voting
            pred_array = np.array(list(predictions.values()))
            final_pred = np.apply_along_axis(
                lambda x: -1 if np.sum(x == -1) > len(x) / 2 else 1,
                axis=0,
                arr=pred_array
            )
        else:  # soft
            # Average scores - ensure all score arrays have same shape
            score_list = []
            for name, score in scores.items():
                # Ensure 1D array
                if isinstance(score, np.ndarray):
                    score = score.flatten()
                score_list.append(score)
            
            # Verify all have same length before stacking
            score_lens = [len(s) for s in score_list]
            if len(set(score_lens)) > 1:
                logger.warning(f"Score arrays have different lengths: {score_lens}, using shortest")
                min_len = min(score_lens)
                score_list = [s[:min_len] for s in score_list]
            
            score_array = np.array(score_list)
            avg_scores = np.mean(score_array, axis=0)
            # Lower scores = more anomalous
            final_pred = np.where(avg_scores < np.percentile(avg_scores, 10), -1, 1)
        
        return final_pred, scores
    
    def get_model(self, name: str) -> Optional[AnomalyModel]:
        """Get specific model"""
        return self.models.get(name)
    
    def save_models(self, directory: Path, compression: bool = True):
        """
        Save all models to disk
        
        Args:
            directory: Directory to save models
            compression: Use gzip compression
        """
        directory.mkdir(parents=True, exist_ok=True)
        
        for name, model in self.models.items():
            if model.trained:
                filename = f"{name}_model.pkl"
                if compression:
                    filename += ".gz"
                
                filepath = directory / filename
                
                try:
                    model_data = {
                        "model": model.model if hasattr(model, "model") else None,
                        "scaler": model.scaler,
                        "config": model.config,
                        "trained": model.trained,
                        "last_trained": model.last_trained,
                        "name": model.name
                    }
                    
                    if compression:
                        with gzip.open(filepath, "wb") as f:
                            pickle.dump(model_data, f)
                    else:
                        with open(filepath, "wb") as f:
                            pickle.dump(model_data, f)
                    
                    logger.info(f"Saved model {name} to {filepath}")
                except Exception as e:
                    logger.error(f"Error saving model {name}: {e}")
    
    def load_models(self, directory: Path):
        """
        Load models from disk
        
        Args:
            directory: Directory containing saved models
        """
        if not directory.exists():
            logger.warning(f"Model directory does not exist: {directory}")
            return
        
        for name in self.models.keys():
            filepath = directory / f"{name}_model.pkl.gz"
            if not filepath.exists():
                filepath = directory / f"{name}_model.pkl"
            
            if filepath.exists():
                try:
                    if filepath.suffix == ".gz":
                        with gzip.open(filepath, "rb") as f:
                            model_data = pickle.load(f)
                    else:
                        with open(filepath, "rb") as f:
                            model_data = pickle.load(f)
                    
                    # Restore model
                    model = self.models[name]
                    if "model" in model_data and hasattr(model, "model"):
                        model.model = model_data["model"]
                    model.scaler = model_data["scaler"]
                    model.trained = model_data["trained"]
                    model.last_trained = model_data["last_trained"]
                    
                    logger.info(f"Loaded model {name} from {filepath}")
                except Exception as e:
                    logger.error(f"Error loading model {name}: {e}")
