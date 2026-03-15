import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock astrbot module for testing without the AstrBot framework
import tests.mocks.astrbot_mock  # noqa: F401
