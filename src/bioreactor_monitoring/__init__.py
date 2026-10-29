"""Core package for the fed-batch penicillin monitoring-to-control prototype.

Modules:
- config: typed access to the YAML configuration.
- loader: reading the IndPenSim dataset archive into canonical tables.
- preprocess: time alignment, merging, and batch-level splits.
- monitor: golden-band monitoring and alarms.
- softsensor: penicillin soft-sensor baselines.
- simulator: Bajpai-Reuss fed-batch penicillin plant model.
- recommender: rule-based and constrained-MPC feed recommendations.
- gates: constraint checks and fallback behaviour.
- evaluate: protocol metrics.
"""

__version__ = "0.1.0"
