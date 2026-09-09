from typing import Dict, List, Optional, Union, Tuple, Any
import numpy as np
import csv
from servegen.clientpool import ClientPool, ClientPoolView, ClientWindow
from servegen.construct import Request

def get_constant_rate_fn(
    pool: Union[ClientPool, ClientPoolView],
    target_rate: float
) -> Dict[int, float]:
    """Create a rate function with constant rate across all timestamps.
    
    Args:
        pool: The client pool or view to generate from
        target_rate: The target aggregate rate to maintain
        
    Returns:
        Dictionary mapping timestamps to target rates
    """
    windows = pool.get()
    if not windows:
        return {}
    
    # Get all timestamps
    timestamps = sorted(set(w.timestamp for w in windows))
    return {ts: target_rate for ts in timestamps}

def get_scaled_rate_fn(
    pool: Union[ClientPool, ClientPoolView],
    scale_factor: float
) -> Dict[int, float]:
    """Create a rate function by scaling the sum of client rates by a constant factor.
    
    Args:
        pool: The client pool or view to generate from
        scale_factor: Factor to multiply the sum of client rates by
        
    Returns:
        Dictionary mapping timestamps to target rates
    """
    windows = pool.get()
    if not windows:
        return {}
    
    # Group windows by timestamp
    windows_by_time: Dict[int, List[ClientWindow]] = {}
    for window in windows:
        if window.timestamp not in windows_by_time:
            windows_by_time[window.timestamp] = []
        windows_by_time[window.timestamp].append(window)
    
    # Calculate sum of rates for each timestamp
    rate_fn = {}
    for ts, window_group in windows_by_time.items():
        total_rate = sum(w.rate for w in window_group if w.rate is not None)
        if total_rate > 0:
            rate_fn[ts] = total_rate * scale_factor
    
    return rate_fn

def get_bounded_rate_fn(
    pool: Union[ClientPool, ClientPoolView],
    max_rate: float
) -> Dict[int, float]:
    """Create a rate function by scaling the sum of client rates to bound the maximum rate.
    
    Args:
        pool: The client pool or view to generate from
        max_rate: Maximum allowed aggregate rate
        
    Returns:
        Dictionary mapping timestamps to target rates
    """
    windows = pool.get()
    if not windows:
        return {}
    
    # Group windows by timestamp
    windows_by_time: Dict[int, List[ClientWindow]] = {}
    for window in windows:
        if window.timestamp not in windows_by_time:
            windows_by_time[window.timestamp] = []
        windows_by_time[window.timestamp].append(window)
    
    # Calculate sum of rates for each timestamp
    rate_fn = {}
    max_total_rate = 0
    for ts, window_group in windows_by_time.items():
        total_rate = sum(w.rate for w in window_group if w.rate is not None)
        if total_rate > 0:
            rate_fn[ts] = total_rate
            max_total_rate = max(max_total_rate, total_rate)
    
    # Scale all rates if max_total_rate exceeds max_rate
    if max_total_rate > max_rate:
        scale_factor = max_rate / max_total_rate
        rate_fn = {ts: rate * scale_factor for ts, rate in rate_fn.items()}
    
    return rate_fn

def sample_from_cdf(
    cdf: Tuple[np.ndarray, np.ndarray],
    n_samples: int = 1,
    rng: Optional[np.random.RandomState] = None
) -> np.ndarray:
    """Sample values from a CDF.
    
    Args:
        cdf: Tuple of (values, probabilities) representing the CDF
        n_samples: Number of samples to generate
        rng: Optional random number generator. If None, a new one will be created.
        
    Returns:
        Array of sampled values
        
    Example:
        values, probs = cdf["rate"][0]  # Get CDF for rate at timestamp 0
        samples = sample_from_cdf((values, probs), n_samples=100)
    """
    if rng is None:
        rng = np.random.RandomState()
    
    values, probs = cdf
    if len(values) == 0:
        return np.array([])
    
    # Generate random numbers
    r = rng.random(n_samples)
    
    # Use searchsorted to find indices
    indices = np.searchsorted(probs, r)
    
    # Handle edge case where random number is larger than all probabilities
    indices = np.clip(indices, 0, len(values) - 1)
    
    return values[indices]

def save_requests_to_csv(
    requests: List[Request],
    filename: str
) -> None:
    """Save list of Request objects to a CSV file.

    Args:
        requests: List of Request objects to save.
        filename: Path to the output CSV file.

    Raises:
        ValueError: If no requests are provided.
    """
    if not requests:
        raise ValueError("No requests to save.")

    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["request_id", "timestamp"] + list(requests[0].data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for req in requests:
            row = {
                "request_id": req.request_id,
                "timestamp": req.timestamp,
                **req.data  # Unpack the data dictionary
            }
            writer.writerow(row)
