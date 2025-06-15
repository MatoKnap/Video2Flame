# backend/bo_logic.py

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

class BayesianCurveFitter:
    def __init__(self, freq_range=(40, 16000)):
        self.freq_range = freq_range
        self.log_freq_range = (np.log10(freq_range[0]), np.log10(freq_range[1]))
        
        # Define frequency bands for stratified sampling
        self.bands = {
            "low": (np.log10(40), np.log10(500)),
            "mid": (np.log10(500), np.log10(4000)),
            "high": (np.log10(4000), np.log10(16000))
        }
        
        self.reset()
        
        # Address the ConvergenceWarning by giving the optimizer more room to find a low noise value.
        kernel = ConstantKernel(1.0) * RBF(length_scale=0.5) + WhiteKernel(
            noise_level=0.5, noise_level_bounds=(1e-10, 1e+1)
        )
        self.gp = GaussianProcessRegressor(
            kernel=kernel, 
            n_restarts_optimizer=15,
            normalize_y=True
        )

    def reset(self):
        self.X_train = []
        self.y_train = []

    def add_points(self, freqs, volumes):
        """Adds a batch of new measured points."""
        for freq, vol in zip(freqs, volumes):
            self.X_train.append([np.log10(freq)])
            self.y_train.append(vol)

    def fit_model(self):
        if len(self.X_train) < 2:
            return
        self.gp.fit(self.X_train, self.y_train)

    def get_next_points_stratified(self, n_points=3):
        """
        Uses acquisition function to find the best points to test in each defined band.
        """
        if len(self.X_train) < 2:
            # For the very first test, return predefined seed points
            return {
                "low": 120.0,
                "mid": 750.0,
                "high": 6000.0
            }

        next_points = {}
        for band_name, (log_min, log_max) in self.bands.items():
            search_space = np.linspace(log_min, log_max, 100).reshape(-1, 1)
            _, std = self.gp.predict(search_space, return_std=True)
            
            # Select the point with the highest uncertainty in this band
            next_log_freq_index = np.argmax(std)
            next_log_freq = search_space[next_log_freq_index][0]
            next_points[band_name] = 10**next_log_freq
        
        return next_points

    def get_full_curve(self):
        if len(self.X_train) < 2:
            return {'freqs': [], 'mean': [], 'std': [], 'points': []}

        log_freq_curve = np.linspace(self.log_freq_range[0], self.log_freq_range[1], 200).reshape(-1, 1)
        mean, std = self.gp.predict(log_freq_curve, return_std=True)
        points = {
            'freqs': (10**np.array(self.X_train).flatten()).tolist(),
            'volumes': self.y_train
        }

        return {
            'freqs': (10**log_freq_curve).flatten().tolist(),
            'mean': mean.tolist(),
            'std': std.tolist(),
            'points': points
        }