"""
Markov Load Model
==================

Markov Chain model for daily cluster state transitions.

Responsibilities:
    - Learn transition probabilities between daily clusters
    - Generate cluster sequences for synthetic load profiles
    - Handle smoothing to avoid zero-probability traps
"""

import numpy as np
from typing import Optional
import logging

from backend.core.models import MarkovTransitionMatrix

logger = logging.getLogger(__name__)


class MarkovLoadModel:
    """
    First-order Markov Chain for modeling daily load cluster transitions.
    
    Purpose:
        Model temporal dynamics: "If today is a high-load day, what's tomorrow?"
        
    Mathematical Foundation:
        P(S_t+1 = j | S_t = i) = Transition Matrix[i, j]
        
        Where:
            S_t = cluster state at day t
            Matrix[i, j] = probability of transitioning from cluster i to j
            
    Smoothing:
        Laplace smoothing prevents zero probabilities:
        P(i -> j) = (count(i -> j) + alpha) / (sum_k(count(i -> k)) + alpha * K)
        
    Complexity:
        Training: O(n_days)
        Generation: O(1) per day
        
    Assumptions:
        - First-order Markov (memoryless beyond previous day)
        - Stationary transition probabilities
    """
    
    def __init__(
        self,
        n_clusters: int,
        smoothing_alpha: float = 0.01
    ):
        """
        Initialize Markov model.
        
        Args:
            n_clusters: Number of cluster states
            smoothing_alpha: Laplace smoothing parameter (default: 0.01)
        """
        self.n_clusters = n_clusters
        self.smoothing_alpha = smoothing_alpha
        self.transition_matrix: Optional[MarkovTransitionMatrix] = None
        
        logger.info(f"MarkovLoadModel initialized (K={n_clusters}, alpha={smoothing_alpha})")
    
    def fit(self, cluster_sequence: np.ndarray) -> MarkovTransitionMatrix:
        """
        Learn transition probabilities from cluster sequence.
        
        Args:
            cluster_sequence: Array of shape (n_days,) with cluster labels
            
        Returns:
            MarkovTransitionMatrix object
            
        Raises:
            ValueError: If sequence is invalid
        """
        if cluster_sequence.ndim != 1:
            raise ValueError(f"Expected 1D array, got shape {cluster_sequence.shape}")
        
        if len(cluster_sequence) < 2:
            raise ValueError("Need at least 2 days to estimate transitions")
        
        logger.info(f"Fitting Markov model on {len(cluster_sequence)} days")
        
        # Initialize transition count matrix
        counts = np.zeros((self.n_clusters, self.n_clusters))
        
        # Count transitions
        for t in range(len(cluster_sequence) - 1):
            current_state = int(cluster_sequence[t])
            next_state = int(cluster_sequence[t + 1])
            
            if not (0 <= current_state < self.n_clusters):
                raise ValueError(f"Invalid cluster label: {current_state}")
            if not (0 <= next_state < self.n_clusters):
                raise ValueError(f"Invalid cluster label: {next_state}")
            
            counts[current_state, next_state] += 1
        
        logger.debug(f"Counted {np.sum(counts)} transitions")
        
        # Apply Laplace smoothing and normalize
        transition_probs = self._compute_probabilities(counts)
        
        # Create Markov transition matrix object
        self.transition_matrix = MarkovTransitionMatrix(
            matrix=transition_probs,
            n_clusters=self.n_clusters,
            smoothing_alpha=self.smoothing_alpha
        )
        
        logger.info("Markov model training complete")
        self._log_transition_summary(counts, transition_probs)
        
        return self.transition_matrix
    
    def _compute_probabilities(self, counts: np.ndarray) -> np.ndarray:
        """
        Compute transition probabilities with Laplace smoothing.
        
        Args:
            counts: Transition count matrix (n_clusters x n_clusters)
            
        Returns:
            Probability matrix with rows summing to 1
        """
        # Add smoothing to avoid zero probabilities
        smoothed_counts = counts + self.smoothing_alpha
        
        # Normalize each row to sum to 1
        row_sums = smoothed_counts.sum(axis=1, keepdims=True)
        probabilities = smoothed_counts / row_sums
        
        # Validate
        assert np.allclose(probabilities.sum(axis=1), 1.0), "Rows must sum to 1"
        
        return probabilities
    
    def _log_transition_summary(self, counts: np.ndarray, probs: np.ndarray):
        """Log summary of transition matrix."""
        total_transitions = np.sum(counts)
        
        if total_transitions == 0:
            logger.warning("No transitions observed (uniform random model)")
            return
        
        # Log most common transitions
        top_transitions = []
        for i in range(self.n_clusters):
            for j in range(self.n_clusters):
                if counts[i, j] > 0:
                    top_transitions.append((i, j, counts[i, j], probs[i, j]))
        
        top_transitions.sort(key=lambda x: x[2], reverse=True)
        
        logger.debug("Top 5 transitions:")
        for i, j, count, prob in top_transitions[:5]:
            logger.debug(f"  Cluster {i} -> {j}: count={count}, prob={prob:.4f}")
    
    def generate_sequence(
        self,
        n_days: int,
        initial_state: Optional[int] = None,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """
        Generate a sequence of cluster states using Markov chain.
        
        Args:
            n_days: Number of days to generate
            initial_state: Starting cluster (None = sample from stationary distribution)
            rng: Random number generator for reproducibility
            
        Returns:
            Array of shape (n_days,) with cluster labels
            
        Raises:
            ValueError: If model not trained
        """
        if self.transition_matrix is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        if n_days <= 0:
            raise ValueError("n_days must be positive")
        
        if rng is None:
            rng = np.random.default_rng()
        
        sequence = np.zeros(n_days, dtype=int)
        
        # Initialize first state
        if initial_state is None:
            # Sample from uniform distribution (or could use stationary distribution)
            sequence[0] = rng.integers(0, self.n_clusters)
        else:
            if not 0 <= initial_state < self.n_clusters:
                raise ValueError(f"Invalid initial_state: {initial_state}")
            sequence[0] = initial_state
        
        # Generate remaining states using Markov chain
        for t in range(1, n_days):
            current_state = sequence[t - 1]
            next_state = self.transition_matrix.sample_next_state(current_state, rng)
            sequence[t] = next_state
        
        logger.debug(f"Generated Markov sequence of {n_days} days")
        return sequence
    
    def get_stationary_distribution(
        self,
        max_iterations: int = 1000,
        tolerance: float = 1e-8
    ) -> np.ndarray:
        """
        Compute stationary distribution of the Markov chain.
        
        The stationary distribution π satisfies: π^T * P = π^T
        
        Args:
            max_iterations: Maximum power iterations
            tolerance: Convergence tolerance
            
        Returns:
            Array of shape (n_clusters,) with stationary probabilities
            
        Raises:
            ValueError: If model not trained
        """
        if self.transition_matrix is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        P = self.transition_matrix.matrix
        
        # Start with uniform distribution
        pi = np.ones(self.n_clusters) / self.n_clusters
        
        # Power iteration: π_{t+1} = π_t * P
        for iteration in range(max_iterations):
            pi_next = pi @ P
            
            # Check convergence
            if np.linalg.norm(pi_next - pi, ord=1) < tolerance:
                logger.debug(f"Stationary distribution converged after {iteration} iterations")
                return pi_next
            
            pi = pi_next
        
        logger.warning(f"Stationary distribution did not converge after {max_iterations} iterations")
        return pi
    
    def get_transition_summary(self) -> dict:
        """
        Get summary statistics of the transition matrix.
        
        Returns:
            Dictionary with transition statistics
            
        Raises:
            ValueError: If model not trained
        """
        if self.transition_matrix is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        P = self.transition_matrix.matrix
        stationary_dist = self.get_stationary_distribution()
        
        return {
            'n_clusters': self.n_clusters,
            'smoothing_alpha': self.smoothing_alpha,
            'transition_matrix_shape': P.shape,
            'stationary_distribution': stationary_dist.tolist(),
            'diagonal_mean': float(np.mean(np.diag(P))),  # Self-transition probability
            'diagonal_values': np.diag(P).tolist(),
        }
