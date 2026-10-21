"""
MANAS Provenance Tracker — Generates cryptographic fingerprints and software environment manifests
for full scientific reproducibility.
"""

import hashlib
import json
import platform
import sys
from typing import Dict, Any


class ProvenanceTracker:
    @staticmethod
    def get_environment_info() -> Dict[str, Any]:
        """Capture python runtime and key package versions."""
        env = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }
        packages = [
            "numpy", "scipy", "pandas", "scikit-learn",
            "statsmodels", "sqlalchemy", "fastapi", "pydantic"
        ]
        pkg_versions = {}
        for pkg in packages:
            try:
                mod = __import__(pkg.replace("-", "_"))
                pkg_versions[pkg] = getattr(mod, "__version__", "unknown")
            except ImportError:
                pkg_versions[pkg] = "not_installed"
        env["packages"] = pkg_versions
        return env

    @staticmethod
    def generate_manifest_hash(run_id: str, parameters: Dict[str, Any], seed: int) -> str:
        """Create a deterministic SHA-256 fingerprint of the run configuration."""
        payload = {
            "run_id": run_id,
            "parameters": parameters,
            "seed": seed,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
