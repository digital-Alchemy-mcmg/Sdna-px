from __future__ import annotations

from typing import Any

from .demand import decompose_observation
from .engine import SpatialDNAEngine


def compile_scout_observation(
    engine: SpatialDNAEngine,
    observation: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    decomposed = decompose_observation(observation)
    return engine.compile(decomposed, strategy)
