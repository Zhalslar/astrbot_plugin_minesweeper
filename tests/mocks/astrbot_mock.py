"""Mock astrbot module for testing without the AstrBot framework"""

import sys
from unittest.mock import MagicMock


# Create base mock modules with proper package support
class MockPackage:
    def __init__(self):
        self.__path__ = []


# Base astrbot module
astrbot = MockPackage()
astrbot.api = MagicMock()
astrbot.api.logger = MagicMock()
sys.modules["astrbot"] = astrbot
sys.modules["astrbot.api"] = astrbot.api
sys.modules["astrbot.api.event"] = MagicMock()

# astrbot.core package
astrbot_core = MockPackage()
sys.modules["astrbot.core"] = astrbot_core
sys.modules["astrbot.core.message"] = MagicMock()
sys.modules["astrbot.core.message.components"] = MagicMock()

# astrbot.core.config
astrbot_core_config = MagicMock()
astrbot_core_config.AstrBotConfig = MagicMock
sys.modules["astrbot.core.config"] = astrbot_core_config
sys.modules["astrbot.core.config.astrbot_config"] = astrbot_core_config

# astrbot.core.star
astrbot_core_star = MockPackage()
sys.modules["astrbot.core.star"] = astrbot_core_star
sys.modules["astrbot.core.star.context"] = MagicMock()
sys.modules["astrbot.core.star.star_tools"] = MagicMock()

# astrbot.core.utils
astrbot_core_utils = MagicMock()
sys.modules["astrbot.core.utils"] = astrbot_core_utils
sys.modules["astrbot.core.utils.astrbot_path"] = MagicMock()

# astrbot.core.platform
astrbot_core_platform = MockPackage()
sys.modules["astrbot.core.platform"] = astrbot_core_platform
sys.modules["astrbot.core.platform.sources"] = MagicMock()
sys.modules["astrbot.core.platform.sources.aiocqhttp"] = MagicMock()
sys.modules["astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event"] = (
    MagicMock()
)
