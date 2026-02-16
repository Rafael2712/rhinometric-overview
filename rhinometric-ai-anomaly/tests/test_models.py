"""
Unit Tests for AI Anomaly Detection
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

from app.models import (
    IsolationForestModel,
    LOFModel,
    StatisticalModel,
    ModelEnsemble
)
from app.config import ModelConfig


@pytest.fixture
def sample_data():
    """Generate sample data for testing"""
    np.random.seed(42)
    # Normal data
    normal = np.random.normal(50, 10, 100)
    # Add some anomalies
    anomalies = np.array([150, 160, 5, 0])
    return np.concatenate([normal, anomalies])


@pytest.fixture
def model_config():
    """Sample model configuration"""
    return ModelConfig(
        isolation_forest={"enabled": True, "contamination": 0.1, "n_estimators": 50},
        lof={"enabled": True, "n_neighbors": 20, "contamination": 0.1},
        ocsvm={"enabled": False},
        statistical={"enabled": True, "zscore_threshold": 3.0}
    )


class TestIsolationForestModel:
    """Test Isolation Forest model"""
    
    def test_initialization(self):
        """Test model initialization"""
        config = {"contamination": 0.1, "n_estimators": 100}
        model = IsolationForestModel(config)
        
        assert model.name == "isolation_forest"
        assert not model.trained
        assert model.last_trained is None
    
    def test_training(self, sample_data):
        """Test model training"""
        config = {"contamination": 0.1, "n_estimators": 50}
        model = IsolationForestModel(config)
        
        X = sample_data.reshape(-1, 1)
        success = model.train(X)
        
        assert success
        assert model.trained
        assert model.last_trained is not None
    
    def test_prediction(self, sample_data):
        """Test anomaly prediction"""
        config = {"contamination": 0.1, "n_estimators": 50}
        model = IsolationForestModel(config)
        
        X = sample_data.reshape(-1, 1)
        model.train(X)
        
        predictions = model.predict(X)
        
        assert len(predictions) == len(sample_data)
        assert set(predictions).issubset({-1, 1})
        # Should detect some anomalies
        assert np.sum(predictions == -1) > 0


class TestLOFModel:
    """Test Local Outlier Factor model"""
    
    def test_initialization(self):
        """Test model initialization"""
        config = {"n_neighbors": 20, "contamination": 0.1}
        model = LOFModel(config)
        
        assert model.name == "lof"
        assert not model.trained
    
    def test_training_and_prediction(self, sample_data):
        """Test training and prediction"""
        config = {"n_neighbors": 20, "contamination": 0.1, "novelty": True}
        model = LOFModel(config)
        
        X = sample_data.reshape(-1, 1)
        model.train(X)
        
        assert model.trained
        
        predictions = model.predict(X)
        assert len(predictions) == len(sample_data)


class TestStatisticalModel:
    """Test statistical anomaly detection"""
    
    def test_zscore_detection(self, sample_data):
        """Test Z-score based detection"""
        config = {"zscore_threshold": 3.0}
        model = StatisticalModel(config)
        
        X = sample_data.reshape(-1, 1)
        model.train(X)
        
        assert model.trained
        assert model.mean is not None
        assert model.std is not None
        
        predictions = model.predict(X)
        # Should detect extreme values
        assert np.sum(predictions == -1) > 0


class TestModelEnsemble:
    """Test model ensemble"""
    
    def test_initialization(self, model_config):
        """Test ensemble initialization"""
        ensemble = ModelEnsemble(model_config)
        
        assert len(ensemble.models) == 3  # IF, LOF, Statistical (OCSVM disabled)
        assert "isolation_forest" in ensemble.models
        assert "lof" in ensemble.models
        assert "statistical" in ensemble.models
    
    def test_train_all(self, model_config, sample_data):
        """Test training all models"""
        ensemble = ModelEnsemble(model_config)
        
        results = ensemble.train_all(sample_data)
        
        assert len(results) == 3
        assert all(results.values())  # All should succeed
    
    def test_detect_anomalies(self, model_config, sample_data):
        """Test ensemble anomaly detection"""
        ensemble = ModelEnsemble(model_config)
        ensemble.train_all(sample_data)
        
        predictions, scores = ensemble.detect_anomalies(sample_data, voting="soft")
        
        assert len(predictions) == len(sample_data)
        assert len(scores) > 0
        # Should detect some anomalies
        assert np.sum(predictions == -1) > 0


class TestAnomalyDetector:
    """Test main detector class"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test detector initialization"""
        # This would require mocking Prometheus and Alertmanager
        # Skipped in unit tests, covered in integration tests
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
