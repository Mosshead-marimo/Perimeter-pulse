# Placeholder for tests/test_models.py
"""
Tests for anomaly detection models
"""

import numpy as np
from models.isolation_forest import IsolationForestModel
from models.one_class_svm import OneClassSVMModel


def test_isolation_forest_training():
    X = np.random.rand(20, 5)

    model = IsolationForestModel({"n_estimators": 50})
    model.train(X)

    scores = model.decision_function(X)
    assert len(scores) == 20


def test_one_class_svm_training():
    X = np.random.rand(20, 5)

    model = OneClassSVMModel({"nu": 0.1})
    model.train(X)

    scores = model.decision_function(X)
    assert len(scores) == 20
