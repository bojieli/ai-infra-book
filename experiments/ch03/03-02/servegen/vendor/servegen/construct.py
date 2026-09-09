from typing import Dict, List, Tuple, Union, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass
from servegen.clientpool import ClientPool, ClientPoolView, ClientWindow

@dataclass
class Request:
    """A single request in the workload."""
    request_id: int  # Incremental request ID
    timestamp: float  # Absolute timestamp
    data: Dict[str, int]  # field_name -> value

def _sample_iats(window: ClientWindow, target_rate: float, rng: np.random.RandomState) -> np.ndarray:
    """Sample inter-arrival times for a window based on its pattern and target rate.
    
    Args:
        window: The client window containing pattern information
        target_rate: The target rate to scale the IATs to
        rng: Random number generator
        
    Returns:
        Array of inter-arrival times
    """
    if window.rate is None or window.cv is None or window.arrival_pat is None:
        return np.array([])
    
    # Calculate how many requests to generate
    window_duration = window.window_size
    expected_requests = target_rate * window_duration
    n_requests = int(np.ceil(expected_requests))
    
    # Get the pattern parameters
    pat_name, (shape, scale) = window.arrival_pat
    
    # Sample IATs based on the pattern
    if pat_name == "Gamma":
        iats = stats.gamma.rvs(a=shape, loc=0, scale=scale, size=n_requests, random_state=rng)
       
    elif pat_name == "Weibull":
        iats = stats.weibull_min.rvs(c=shape, loc=0, scale=scale, size=n_requests, random_state=rng)
    else:
        raise ValueError(f"Unknown arrival pattern: {pat_name}")
    
    # Scale IATs to match target rate
    if target_rate > 0:
        scale_factor = window_duration / sum(iats)
        iats *= scale_factor
    
    return iats

def _sample_data_batch(window: ClientWindow, n_samples: int, rng: np.random.RandomState) -> List[Dict[str, Union[int, List[int]]]]:
    """Sample data fields from a window's dataset in batch.
    
    Args:
        window: The client window containing dataset information
        n_samples: Number of samples to generate
        rng: Random number generator
        
    Returns:
        List of dictionaries mapping field names to sampled values. For multimodal workloads,
        image/audio/video tokens are returned as lists, while counts and text/output tokens
        are returned as integers.
    """
    if window.dataset is None:
        raise ValueError(f"No dataset found for client {window.client_id} at timestamp {window.timestamp}")
        # return [{} for _ in range(n_samples)]
    
    # Pre-compute CDFs for all fields
    cdfs = {}
    for field_name, pdf in window.dataset.items():
        if field_name == "reason_ratio":
            # For reason_ratio, treat PDF as [0,1] range
            cdfs[field_name] = ("ratio", np.cumsum(pdf))
        else:
            # For all other fields, treat as [0,max_token] range
            cdfs[field_name] = ("token", np.cumsum(pdf))
    
    # Sample all random numbers at once
    random_values = rng.random(n_samples)
    
    # Generate all samples
    results = []
    for field_name, (data_type, cdf) in cdfs.items():
        if data_type == "ratio":
            # For reason_ratio, sample directly from [0,1] range
            values = np.searchsorted(cdf, random_values)
            # Convert to float in [0,1] range
            values = values.astype(float) / (len(cdf) - 1)
        else:
            # For token counts, sample from [0,max_token] range
            values = np.searchsorted(cdf, random_values)
        results.append(values)
    
    # Convert to list of dictionaries
    base_samples = [dict(zip(cdfs.keys(), values)) for values in zip(*results)]
    
    # For multimodal workloads, process image/audio/video tokens
    if "image_count" in window.dataset:
        for sample in base_samples:
            # Sample image tokens if count > 0
            if sample["image_count"] > 0:
                image_tokens = []
                for _ in range(sample["image_count"]):
                    # Sample one image token
                    token = np.searchsorted(cdfs["image_tokens"][1], rng.random())
                    image_tokens.append(token)
                sample["image_tokens"] = image_tokens
            else:
                sample["image_tokens"] = []
            
            # Sample audio tokens if count > 0
            if sample["audio_count"] > 0:
                audio_tokens = []
                for _ in range(sample["audio_count"]):
                    # Sample one audio token
                    token = np.searchsorted(cdfs["audio_tokens"][1], rng.random())
                    audio_tokens.append(token)
                sample["audio_tokens"] = audio_tokens
            else:
                sample["audio_tokens"] = []
            
            # Sample video tokens if count > 0
            if sample["video_count"] > 0:
                video_tokens = []
                for _ in range(sample["video_count"]):
                    # Sample one video token
                    token = np.searchsorted(cdfs["video_tokens"][1], rng.random())
                    video_tokens.append(token)
                sample["video_tokens"] = video_tokens
            else:
                sample["video_tokens"] = []
            
            # Remove count fields as they're no longer needed
            del sample["image_count"]
            del sample["audio_count"]
            del sample["video_count"]
    
    return base_samples

def generate_workload(
    pool: Union[ClientPool, ClientPoolView],
    rate_fn: Dict[int, float],
    duration: int,
    seed: Optional[int] = None
) -> List[Request]:
    """Generate a workload from a client pool and rate function.
    
    Args:
        pool: The client pool or view to generate from
        rate_fn: Dictionary mapping timestamps to target aggregate rates
        duration: Total duration in seconds.
        seed: Optional random seed for reproducibility
        
    Returns:
        List of requests sorted by timestamp
    """
    if duration <= 0:
        raise ValueError("Duration must be positive")
        
    # Initialize random number generator
    rng = np.random.RandomState(seed)
    
    pool = pool.span(0, duration)
    
    # Get all windows
    windows = pool.get()
    if not windows:
        return []
    
    # Validate rate function
    window_timestamps = sorted(set(w.timestamp for w in windows))
    rate_timestamps = sorted(ts for ts in rate_fn.keys() if ts >= 0 and ts < duration)
    if window_timestamps != rate_timestamps:
        raise ValueError(
            f"Rate function timestamps don't match pool timestamps. "
            f"Expected {window_timestamps}, got {rate_timestamps}"
        )
    
    # Group windows by timestamp
    windows_by_time: Dict[int, List[ClientWindow]] = {}
    for window in windows:
        if window.timestamp not in windows_by_time:
            windows_by_time[window.timestamp] = []
        windows_by_time[window.timestamp].append(window)
    
    # Generate requests for each timestamp
    all_requests: List[Request] = []
    
    for ts, window_group in windows_by_time.items():
        target_aggregate_rate = rate_fn[ts]
        
        # Calculate total rate of all clients in this window
        total_client_rate = sum(w.rate for w in window_group if w.rate is not None)
        if total_client_rate == 0:
            continue
        
        # Generate requests for each window
        for window in window_group:
            if window.rate is None:
                continue
                
            # Compute this client's target rate based on their relative contribution
            client_target_rate = target_aggregate_rate * (window.rate / total_client_rate)
            
            # Sample IATs
            iats = _sample_iats(window, client_target_rate, rng)
            if len(iats) == 0:
                continue
            
            # Convert IATs to absolute timestamps
            timestamps = np.cumsum(iats) + ts
            
            # Filter timestamps to be within window
            valid_timestamps = timestamps[timestamps < ts + window.window_size]
            if len(valid_timestamps) == 0:
                continue
            
            # Sample all data in batch
            data_samples = _sample_data_batch(window, len(valid_timestamps), rng)
            
            # Generate requests
            for t, data in zip(valid_timestamps, data_samples):
                request = Request(
                    request_id=None,
                    timestamp=t,
                    data=data
                )
                all_requests.append(request)
    
    # Sort all requests by timestamp
    all_requests.sort(key=lambda r: r.timestamp)
    for i, req in enumerate(all_requests):
        req.request_id = i

    return all_requests
