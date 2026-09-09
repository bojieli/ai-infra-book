from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
import numpy as np

class Category(Enum):
    """Categories of LLM workloads."""
    LANGUAGE = "language"
    MULTIMODAL = "multimodal"
    REASON = "reason"

class ArrivalPat(Enum):
    """Arrival patterns for request generation."""
    GAMMA = "Gamma"
    WEIBULL = "Weibull"

@dataclass
class ClientWindow:
    """Data for a single time window of a client."""
    client_id: int
    timestamp: int  # relative timestamp (shifted to start from 0)
    window_size: int  # size of this window (may be truncated at span boundaries)
    rate: Optional[float] = None
    cv: Optional[float] = None
    arrival_pat: Optional[Tuple[str, Tuple[float, ...]]] = None
    dataset: Optional[Dict[str, List[float]]] = None  # field_name -> pdf 