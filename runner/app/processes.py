import subprocess
from typing import Dict, Tuple

# Dictionary to store process information
processes: Dict[str, Tuple[subprocess.Popen, float]] = {}
