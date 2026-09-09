from typing import Dict, List, Optional, Tuple, Union, Callable
import json
import os
from dataclasses import dataclass
import numpy as np
from scipy import stats
from servegen.workload_types import Category, ArrivalPat, ClientWindow

@dataclass
class Client:
    """Represents a single client's data."""
    client_id: int
    trace: Dict[int, Optional[Dict]]  # timestamp -> {rate, cv, pat}
    dataset: Dict[int, Dict]  # timestamp -> {field_name: pdf}

    def validate(self) -> None:
        """Validate the client's data integrity.
        
        Raises:
            ValueError: If any validation check fails.
        """
        # Check trace timestamps are sorted
        trace_timestamps = sorted(self.trace.keys())
        if trace_timestamps != list(self.trace.keys()):
            raise ValueError("Trace timestamps must be in ascending order")

        # Validate trace data
        for ts, data in self.trace.items():
            if data is not None:
                if not isinstance(data, dict):
                    raise ValueError(f"Trace data at {ts} must be a dictionary")
                required_fields = {"rate", "cv", "pat"}
                if not required_fields.issubset(data.keys()):
                    raise ValueError(f"Trace data at {ts} missing required fields: {required_fields - set(data.keys())}")
                if not isinstance(data["rate"], (int, float)) or data["rate"] < 0:
                    raise ValueError(f"Rate at {ts} must be a non-negative number")
                if not isinstance(data["cv"], (int, float)) or data["cv"] < 0:
                    raise ValueError(f"CV at {ts} must be a non-negative number")
                if (not isinstance(data["pat"], tuple) and not isinstance(data["pat"], list)) or len(data["pat"]) != 2:
                    raise ValueError(f"Pattern at {ts} must be a tuple/list of (name, params) {data['pat']}")
                if data["pat"][0] not in [p.value for p in ArrivalPat]:
                    raise ValueError(f"Invalid arrival pattern at {ts}: {data['pat'][0]}")

        # Check dataset timestamps are sorted
        dataset_timestamps = sorted(self.dataset.keys())
        if dataset_timestamps != list(self.dataset.keys()):
            raise ValueError("Dataset timestamps must be in ascending order")

        # Validate dataset data
        for ts, fields in self.dataset.items():
            if not isinstance(fields, dict):
                raise ValueError(f"Dataset at {ts} must be a dictionary")
            for field_name, pdf in fields.items():
                if not isinstance(pdf, list):
                    raise ValueError(f"PDF for {field_name} at {ts} must be a list")
                if not all(isinstance(p, (int, float)) for p in pdf):
                    raise ValueError(f"PDF values for {field_name} at {ts} must be numbers")
                if not all(p >= 0 for p in pdf):
                    raise ValueError(f"PDF values for {field_name} at {ts} must be non-negative")
                if not np.isclose(sum(pdf), 1.0, atol=1e-6):
                    raise ValueError(f"PDF for {field_name} at {ts} must sum to 1.0")

class ClientPool:
    """Manages a pool of clients and provides methods to query and analyze them."""
    
    def __init__(self, category: Category, model: str, clients: Optional[Dict[int, Client]] = None):
        """Initialize the client pool.
        
        Args:
            category: The workload category.
            model: The model name. 
            	Data should be provided in data/{category}/{model}.json.
        """
        self.category = category
        self.model = model
        if clients is None:
            self.clients = {}
            self._load_data(category, model)
        else:
            self.clients = clients
            self.validate()

    def validate(self) -> None:
        """Validate the client pool's data integrity.
        
        Raises:
            ValueError: If any validation check fails.
        """
        # Validate each client
        for client in self.clients.values():
            client.validate()

        # Check that all clients have identical trace timestamps
        first_client = next(iter(self.clients.values()))
        expected_trace_timestamps = set(first_client.trace.keys())
        for client_id, client in self.clients.items():
            client_trace_timestamps = set(client.trace.keys())
            if client_trace_timestamps != expected_trace_timestamps:
                raise ValueError(
                    f"Client {client_id} has different trace timestamps than the first client. "
                    f"Expected {sorted(expected_trace_timestamps)}, got {sorted(client_trace_timestamps)}"
                )

        # Check that all dataset timestamps are subsets of trace timestamps
        for client_id, client in self.clients.items():
            dataset_timestamps = set(client.dataset.keys())
            if not dataset_timestamps.issubset(expected_trace_timestamps):
                extra_timestamps = dataset_timestamps - expected_trace_timestamps
                raise ValueError(
                    f"Client {client_id} has dataset timestamps that are not in trace timestamps: "
                    f"{sorted(extra_timestamps)}"
                )

    @classmethod
    def from_clients(cls, category: Category, model: str, clients: List[Client]) -> 'ClientPool':
        """Create a ClientPool from a list of clients.
        
        Args:
            category: The workload category.
            model: The model name.
            clients: List of Client objects.
            
        Returns:
            A new ClientPool instance.
            
        Raises:
            ValueError: If any client validation fails.
        """
        # Check for duplicate client IDs
        client_ids = set()
        for client in clients:
            if client.client_id in client_ids:
                raise ValueError(f"Duplicate client ID: {client.client_id}")
            client_ids.add(client.client_id)

        client_dict = {client.client_id: client for client in clients}
        return cls(category, model, clients=client_dict)

    def _load_data(self, category: Category, model: str):
        """Load client data from the JSON and CSV files."""
        data_dir = os.path.join("data", category.value, model)
        if not os.path.exists(data_dir):
            raise ValueError(f"Data directory not found: {data_dir}")

        # Find all dataset and trace files
        dataset_files = [f for f in os.listdir(data_dir) if f.endswith('-dataset.json')]
        trace_files = [f for f in os.listdir(data_dir) if f.endswith('-trace.csv')]

        # Process each client's data
        for dataset_file in dataset_files:
            # Extract client ID from filename
            client_id = int(dataset_file.split('-')[1])
            
            # Load dataset data
            dataset_path = os.path.join(data_dir, dataset_file)
            with open(dataset_path, 'r') as f:
                dataset_data = json.load(f)
            
            # Convert dataset data to the expected format
            dataset = {}
            for ts, fields in dataset_data.items():
                data = {}
                skip = False
                for k, v in fields.items():
                    pdf = eval(v)
                    if len(pdf) == 0:
                        skip = True
                        break 
                    if isinstance(next(iter(pdf.keys())), int):
                        max_bin = max(pdf.keys())
                        pdf = [pdf[bin] if bin in pdf else 0.0 for bin in range(0, max_bin + 1)]
                    else:
                        pdf = list(pdf.values())
                    data[k] = pdf
                if skip:
                    continue
                dataset[int(ts)] = data

            # Load trace data
            trace_file = f"chunk-{client_id}-trace.csv"
            if trace_file not in trace_files:
                raise ValueError(f"Trace file not found for client {client_id}: {trace_file}")
            
            trace_path = os.path.join(data_dir, trace_file)
            trace = {}
            with open(trace_path, 'r') as f:
                for line in f:
                    # Parse CSV line
                    timestamp, rate, cv, pat_name, pat_arg1, pat_arg2 = line.strip().split(',')
                    timestamp = int(timestamp)
                    rate = float(rate)
                    cv = float(cv)
                    pat_arg1 = float(pat_arg1)
                    pat_arg2 = float(pat_arg2)

                    if pat_name == "":
                        trace[timestamp] = None
                    else:
                        # Convert pattern to tuple format
                        pat = (pat_name, (pat_arg1, pat_arg2))
                        
                        trace[timestamp] = {
                            "rate": rate,
                            "cv": cv,
                            "pat": pat
                        }

            # Create client object
            self.clients[client_id] = Client(
                client_id=client_id,
                trace=trace,
                dataset=dataset
            )
        
        self.validate()

    def span(self, start_time: int, end_time: int) -> 'ClientPoolView':
        """Create a view of clients within the given time range."""
        return ClientPoolView(self, start_time, end_time)

    def filter(self, condition: Callable[[ClientWindow], bool]) -> 'ClientPoolView':
        """Add a filter condition that operates on individual windows."""
        return ClientPoolView(self, 0, float('inf')).filter(condition)

    def filter_by_cv(self, min_cv: float, max_cv: float) -> 'ClientPoolView':
        """Filter windows by their coefficient of variation."""
        return ClientPoolView(self, 0, float('inf')).filter_by_cv(min_cv, max_cv)

    def filter_by_avg_input_len(self, min_len: float, max_len: float) -> 'ClientPoolView':
        """Filter windows by the average input length."""
        return ClientPoolView(self, 0, float('inf')).filter_by_avg_input_len(min_len, max_len)
    
    def filter_by_avg_output_len(self, min_len: float, max_len: float) -> 'ClientPoolView':
        """Filter windows by the average output length."""
        return ClientPoolView(self, 0, float('inf')).filter_by_avg_output_len(min_len, max_len)
    
    def filter_by_max_input_len(self, max_len: float) -> 'ClientPoolView':
        """Filter windows by the max input length."""
        return ClientPoolView(self, 0, float('inf')).filter_by_max_input_len(max_len)
    
    def filter_by_max_output_len(self, max_len: float) -> 'ClientPoolView':
        """Filter windows by the max output length."""
        return ClientPoolView(self, 0, float('inf')).filter_by_max_output_len(max_len)

    def get(self) -> List[ClientWindow]:
        """Get all client data."""
        return ClientPoolView(self, 0, float('inf')).get()

    def get_cdfs(self) -> Dict[str, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """Get CDFs of various client behaviors across all clients."""
        return ClientPoolView(self, 0, float('inf')).get_cdfs()

class ClientPoolView:
    """A view of ClientPool with a specific time range and filters."""
    
    def __init__(self, pool: ClientPool, start_time: int, end_time: int):
        self.pool = pool
        self.start_time = start_time
        self.end_time = end_time
        self.filters: List[Callable[[ClientWindow], bool]] = []

    def _get_dataset_window(self, client: Client, trace_ts: int) -> Optional[Dict]:
        """Get the dataset window that contains the given trace timestamp."""
        if not client.dataset:
            return None
        
        # Find the largest dataset timestamp that's <= trace_ts
        for ts in reversed(client.dataset.keys()):
            if ts <= trace_ts:
                return client.dataset[ts]
        return None

    def _process_client(self, client: Client) -> List[ClientWindow]:
        """Process a client's data within the time range."""
        # Get all trace windows that overlap with our span range
        # A window at timestamp T represents [T, T+window_size)
        trace_windows = []
        for ts in client.trace.keys():
            # Get the next timestamp to determine window size
            next_ts = next((t for t in client.trace.keys() if t > ts), float('inf')) 
            window_size = next_ts - ts
            
            # Check if window overlaps with our span range
            window_end = ts + window_size
            if window_end <= self.start_time or ts >= self.end_time:
                continue
                
            # Calculate truncated window size and start time
            truncated_start = max(ts, self.start_time)
            truncated_end = min(window_end, self.end_time)
            truncated_size = truncated_end - truncated_start
            
            trace_data = client.trace[ts]
            dataset_data = self._get_dataset_window(client, ts)
            
            window = ClientWindow(
                client_id=client.client_id,
                timestamp=truncated_start - self.start_time,
                window_size=truncated_size,
                rate=trace_data["rate"] if trace_data else None,
                cv=trace_data["cv"] if trace_data else None,
                arrival_pat=trace_data["pat"] if trace_data else None,
                dataset=dataset_data if dataset_data else None
            )
            trace_windows.append(window)

        return trace_windows

    def span(self, start_time: int, end_time: int) -> 'ClientPoolView':
        """Create a new view with a different time range."""
        # Adjust the new time range relative to the current view's start time
        new_start = self.start_time + start_time
        new_end = self.start_time + end_time
        view = ClientPoolView(self.pool, new_start, new_end)
        view.filters = self.filters.copy()
        return view

    def filter(self, condition: Callable[[ClientWindow], bool]) -> 'ClientPoolView':
        """Add a filter condition that operates on individual windows."""
        self.filters.append(condition)
        return self

    def filter_by_cv(self, min_cv: float, max_cv: float) -> 'ClientPoolView':
        """Filter windows by their coefficient of variation."""
        def cv_filter(window: ClientWindow) -> bool:
            if window.cv is None:
                return False
            return min_cv <= window.cv <= max_cv
        return self.filter(cv_filter)

    def filter_by_avg_input_len(self, min_len: float, max_len: float) -> 'ClientPoolView':
        """Filter windows by the average input length."""
        def len_filter(window: ClientWindow) -> bool:
            if not window.dataset or 'input_tokens' not in window.dataset:
                return False
            pdf = window.dataset['input_tokens']
            avg_len = sum(i * p for i, p in enumerate(pdf, 0))
            return min_len <= avg_len <= max_len
        return self.filter(len_filter)
    
    def filter_by_avg_output_len(self, min_len: float, max_len: float) -> 'ClientPoolView':
        """Filter windows by the average output length."""
        def len_filter(window: ClientWindow) -> bool:
            if not window.dataset or 'output_tokens' not in window.dataset:
                return False
            pdf = window.dataset['output_tokens']
            avg_len = sum(i * p for i, p in enumerate(pdf, 0))
            return min_len <= avg_len <= max_len
        return self.filter(len_filter)
    
    def filter_by_max_input_len(self, max_len: float) -> 'ClientPoolView':
        """Filter windows by the max input length."""
        def len_filter(window: ClientWindow) -> bool:
            if not window.dataset or 'input_tokens' not in window.dataset:
                return False
            pdf = window.dataset['input_tokens']
            window_max_len = max(len(pdf) - 1, 0)
            return window_max_len <= max_len
        return self.filter(len_filter)
    
    def filter_by_max_output_len(self, max_len: float) -> 'ClientPoolView':
        """Filter windows by the max output length."""
        def len_filter(window: ClientWindow) -> bool:
            if not window.dataset or 'output_tokens' not in window.dataset:
                return False
            pdf = window.dataset['output_tokens']
            window_max_len = max(len(pdf) - 1, 0)
            return window_max_len <= max_len
        return self.filter(len_filter)

    def get(self) -> List[ClientWindow]:
        """Get the filtered and processed client data."""
        result = []
        for client in self.pool.clients.values():
            windows = self._process_client(client)
            if not windows:
                continue

            # Apply filters to each window
            filtered_windows = []
            for window in windows:
                if all(f(window) for f in self.filters):
                    filtered_windows.append(window)

            if any(w.rate is not None for w in filtered_windows):
                result.extend(filtered_windows)

        return result

    def get_cdfs(self) -> Dict[str, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """Get CDFs of various client behaviors across all clients for each window.
        
        Returns a dictionary with the following structure:
        {
            "rate": {
                0: (values, probabilities),  # CDF for timestamp 0
                600: (values, probabilities),  # CDF for timestamp 600
                ...
            },
            "cv": { ... },
            "input_tokens": {
                "avg": {  # CDFs of average values across clients
                    0: (values, probabilities),
                    600: (values, probabilities),
                    ...
                },
                "p50": { ... },  # CDFs of median values
                "p95": { ... },  # CDFs of 95th percentile values
                "p99": { ... },  # CDFs of 99th percentile values
            },
            "output_tokens": { ... },
            ...
        }
        For rate and cv, each CDF represents the distribution of values across all clients at that timestamp.
        For dataset fields, each CDF represents the distribution of statistics (avg/p50/p95/p99) across clients.
        """
        windows = self.get()
        if not windows:
            return {}

        # Group windows by their timestamp
        windows_by_time: Dict[int, List[ClientWindow]] = {}
        for window in windows:
            if window.timestamp not in windows_by_time:
                windows_by_time[window.timestamp] = []
            windows_by_time[window.timestamp].append(window)

        # Initialize result structure
        result = {
            "rate": {},
            "cv": {}
        }

        # Get all dataset fields
        dataset_fields = set()
        for window in windows:
            if window.dataset:
                dataset_fields.update(window.dataset.keys())
        for field in dataset_fields:
            result[field] = {
                "avg": {},
                "p50": {},
                "p95": {},
                "p99": {}
            }

        # Convert to CDFs
        def to_cdf(values: List[float]) -> Tuple[np.ndarray, np.ndarray]:
            if not values:
                return np.array([]), np.array([])
            sorted_values = np.sort(values)
            return sorted_values, np.linspace(0, 1, len(sorted_values)+1)[1:]

        def to_weighted_cdf(values: List[float], weights: List[float]) -> Tuple[np.ndarray, np.ndarray]:
            """Convert values and their weights to a weighted CDF.
            
            Args:
                values: List of values to convert to CDF
                weights: List of weights corresponding to each value
                
            Returns:
                Tuple of (sorted_values, cumulative_probabilities)
            """
            if not values:
                return np.array([]), np.array([])
            
            # Sort values and weights together
            sorted_pairs = sorted(zip(values, weights))
            sorted_values = np.array([v for v, _ in sorted_pairs])
            sorted_weights = np.array([w for _, w in sorted_pairs])
            
            # Normalize weights to sum to 1.0
            total_weight = sum(sorted_weights)
            if total_weight == 0:
                return np.array([]), np.array([])
            normalized_weights = sorted_weights / total_weight
            
            # Compute cumulative probabilities
            cum_probs = np.cumsum(normalized_weights)
            
            return sorted_values, cum_probs

        # Helper function to compute statistics from a PDF
        def compute_stats(pdf: List[float]) -> Tuple[float, float, float, float]:
            if not pdf:
                return 0.0, 0.0, 0.0, 0.0
            # Create a list of values with their probabilities
            values = []
            probs = []
            for i, p in enumerate(pdf, 0):
                if p > 0:
                    values.append(i)
                    probs.append(p)
            # Normalize probabilities
            total_prob = sum(probs)
            if total_prob == 0:
                return 0.0, 0.0, 0.0, 0.0
            probs = [p/total_prob for p in probs]
            # Compute statistics
            avg = sum(v * p for v, p in zip(values, probs))
            # For percentiles, we need to sort values and use cumulative probabilities
            sorted_pairs = sorted(zip(values, probs))
            values = [v for v, _ in sorted_pairs]
            probs = [p for _, p in sorted_pairs]
            cum_probs = np.cumsum(probs)
            # Find percentiles
            p50_idx = np.searchsorted(cum_probs, 0.5)
            p95_idx = np.searchsorted(cum_probs, 0.95)
            p99_idx = np.searchsorted(cum_probs, 0.99)
            p50 = values[p50_idx] if p50_idx < len(values) else values[-1]
            p95 = values[p95_idx] if p95_idx < len(values) else values[-1]
            p99 = values[p99_idx] if p99_idx < len(values) else values[-1]
            return avg, p50, p95, p99

        # Process each timestamp
        for ts in windows_by_time:
            window_group = windows_by_time[ts]
            
            # Process rate and cv
            rate_values = [w.rate for w in window_group if w.rate is not None]
            cv_values = [w.cv for w in window_group if w.cv is not None]
            cv_weights = [w.rate for w in window_group if w.cv is not None]  # Use rates as weights for CV
            
            if rate_values:
                result["rate"][ts] = to_cdf(rate_values)  # Rate CDFs remain unweighted
            if cv_values:
                result["cv"][ts] = to_weighted_cdf(cv_values, cv_weights)  # CV CDFs are weighted by rate

            # Process dataset fields
            for field in dataset_fields:
                # Collect statistics for each client
                avg_values = []
                p50_values = []
                p95_values = []
                p99_values = []
                weights = []  # Store rates for weighting
                
                for window in window_group:
                    if window.dataset and field in window.dataset:
                        pdf = window.dataset[field]
                        avg, p50, p95, p99 = compute_stats(pdf)
                        avg_values.append(avg)
                        p50_values.append(p50)
                        p95_values.append(p95)
                        p99_values.append(p99)
                        weights.append(window.rate if window.rate is not None else 0.0)
                
                # Create weighted CDFs for each statistic
                if avg_values:
                    result[field]["avg"][ts] = to_weighted_cdf(avg_values, weights)
                if p50_values:
                    result[field]["p50"][ts] = to_weighted_cdf(p50_values, weights)
                if p95_values:
                    result[field]["p95"][ts] = to_weighted_cdf(p95_values, weights)
                if p99_values:
                    result[field]["p99"][ts] = to_weighted_cdf(p99_values, weights)

        return result
