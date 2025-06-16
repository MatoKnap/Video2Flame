# backend/bo_logic.py

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

class BayesianCurveFitter:
    def __init__(self, freq_range=(40, 16000)):
        # Use log space for frequency, as human perception is logarithmic
        self.log_freq_range = (np.log10(freq_range[0]), np.log10(freq_range[1]))
        self.reset()
        
        # Define the Gaussian Process kernel. RBF is good for smooth functions.
        # WhiteKernel accounts for noise in the user's measurements.
        kernel = ConstantKernel(1.0) * RBF(length_scale=0.5) + WhiteKernel(
            noise_level=0.5, 
            noise_level_bounds=(1e-10, 1e5) # Explicitly set a lower bound
        )
        self.gp = GaussianProcessRegressor(
            kernel=kernel, 
            n_restarts_optimizer=15,
            normalize_y=True,
            alpha=1e-5 # Small value for numerical stability
        )

    def reset(self):
        """Resets the model to its initial state."""
        self.X_train = []  # List of tested log-frequencies
        self.y_train = []  # List of resulting volumes

    def add_point(self, freq, volume):
        """Adds a new measured point to the training data."""
        self.X_train.append([np.log10(freq)])
        self.y_train.append(volume)

    def fit_model(self):
        """Fits the Gaussian Process model to the current data."""
        if len(self.X_train) < 2:
            return
        self.gp.fit(self.X_train, self.y_train)

    def get_next_point(self):
        """
        Uses the acquisition function (max uncertainty) to find the next best
        frequency to test.
        """
        if len(self.X_train) < 2:
            # Start with a known anchor point
            return 1000.0

        # Define the search space to find the point of max uncertainty
        search_space = np.linspace(self.log_freq_range[0], self.log_freq_range[1], 300).reshape(-1, 1)
        
        _, std = self.gp.predict(search_space, return_std=True)
        
        # Select the point with the highest standard deviation (most uncertainty)
        next_log_freq_index = np.argmax(std)
        next_log_freq = search_space[next_log_freq_index][0]
        
        return 10**next_log_freq

    def get_full_curve(self):
        """
        Generates a smooth curve and uncertainty bands for plotting.
        """
        if len(self.X_train) < 2:
            return {'freqs': [], 'mean': [], 'std': [], 'points': []}

        # Generate a dense grid of frequencies for a smooth plot
        log_freq_curve = np.linspace(self.log_freq_range[0], self.log_freq_range[1], 200).reshape(-1, 1)
        
        mean, std = self.gp.predict(log_freq_curve, return_std=True)
        
        # Get the original points back for plotting
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