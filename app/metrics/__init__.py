"""Pure measurement functions a teardown harness imports to score itself.

No database access and no I/O lives here: every function takes plain data
in and returns a plain number out, so the same harness code that calls
these during a real cycle can also be unit tested against them directly.
"""

from app.metrics.calibration import brier_score
from app.metrics.gates import gate_flip_rate
from app.metrics.judges import flip_rate
from app.metrics.power import minimum_detectable_effect
from app.metrics.ranking import rank_correlation
from app.metrics.retrieval import ndcg_at_k, precision_at_k, recall_at_k

__all__ = [
    "recall_at_k",
    "precision_at_k",
    "ndcg_at_k",
    "brier_score",
    "flip_rate",
    "rank_correlation",
    "gate_flip_rate",
    "minimum_detectable_effect",
]
