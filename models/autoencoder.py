# Placeholder for models/autoencoder.py
"""
Autoencoder Model (Optional – Deep Anomaly Detection)
"""

import numpy as np

try:
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Dense
except ImportError:
    Model = None


class AutoencoderModel:
    def __init__(self, input_dim: int, latent_dim: int = 8):
        if Model is None:
            raise ImportError("TensorFlow not installed")

        input_layer = Input(shape=(input_dim,))
        encoded = Dense(latent_dim, activation="relu")(input_layer)
        decoded = Dense(input_dim, activation="linear")(encoded)

        self.autoencoder = Model(inputs=input_layer, outputs=decoded)
        self.autoencoder.compile(optimizer="adam", loss="mse")

    def train(self, X, epochs: int = 30, batch_size: int = 32):
        self.autoencoder.fit(X, X, epochs=epochs, batch_size=batch_size, verbose=0)

    def predict(self, X):
        return self.autoencoder.predict(X)
