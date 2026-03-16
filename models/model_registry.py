# Placeholder for models/model_registry.py
"""
Model Registry
Centralized loader for anomaly detection models
"""

from models.isolation_forest import IsolationForestModel
from models.one_class_svm import OneClassSVMModel
from models.autoencoder import AutoencoderModel


class ModelRegistry:
    def __init__(self, model_config: dict):
        self.model_config = model_config
        self.models = {}

    def initialize(self, feature_dim: int):
        if self.model_config["isolation_forest"]["enabled"]:
            self.models["isolation_forest"] = IsolationForestModel(
                self.model_config["isolation_forest"]
            )

        if self.model_config["one_class_svm"]["enabled"]:
            self.models["one_class_svm"] = OneClassSVMModel(
                self.model_config["one_class_svm"]
            )

        if self.model_config["autoencoder"]["enabled"]:
            self.models["autoencoder"] = AutoencoderModel(
                input_dim=feature_dim,
                latent_dim=self.model_config["autoencoder"]["latent_dim"]
            )

        return self.models

    def train_all(self, X):
        for model in self.models.values():
            model.train(X)
