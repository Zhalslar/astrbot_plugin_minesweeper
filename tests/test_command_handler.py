from core.command_handler import GameInitializer


class MockPluginConfig:
    """模拟 PluginConfig 用于测试"""

    default_skin = "winxp"

    def __init__(self):
        self.levels = {
            "初级": (8, 8, 10),
            "中级": (16, 16, 40),
            "高级": (16, 30, 99),
        }

    def is_supported_level(self, name: str) -> bool:
        return name in self.levels

    def get_spec(self, name: str):
        from core.model import GameSpec

        rows, cols, mines = self.levels.get(name, (8, 8, 10))
        return GameSpec(rows, cols, mines)


class MockSkinManager:
    """模拟 SkinManager 用于测试"""

    def load(self, name, spec):
        return None

    def get_skin_by_index(self, index):
        return "winxp"


class TestGameInitializer:
    """测试游戏初始化器的参数解析"""

    def setup_method(self):
        self.cfg = MockPluginConfig()
        self.skin_mgr = MockSkinManager()
        self.initializer = GameInitializer(self.cfg, self.skin_mgr)

    def test_parse_args_beginner(self):
        spec, skin_index, err = self.initializer.parse_args(["初级"])
        assert spec is not None
        assert spec.rows == 8
        assert spec.cols == 8
        assert spec.mines == 10
        assert skin_index is None
        assert err is None

    def test_parse_args_beginner_with_skin(self):
        spec, skin_index, err = self.initializer.parse_args(["中级", "2"])
        assert spec is not None
        assert spec.rows == 16
        assert skin_index == 2
        assert err is None

    def test_parse_args_custom_numbers(self):
        spec, skin_index, err = self.initializer.parse_args(["10", "10", "20"])
        assert spec is not None
        assert spec.rows == 10
        assert spec.cols == 10
        assert spec.mines == 20
        assert err is None

    def test_parse_args_custom_with_skin(self):
        spec, skin_index, err = self.initializer.parse_args(["10", "10", "20", "3"])
        assert spec is not None
        assert skin_index == 3
        assert err is None

    def test_parse_args_keyword_custom(self):
        spec, skin_index, err = self.initializer.parse_args(
            ["自定义", "15", "15", "30"]
        )
        assert spec is not None
        assert spec.rows == 15
        assert spec.cols == 15
        assert spec.mines == 30
        assert err is None

    def test_parse_args_empty(self):
        spec, skin_index, err = self.initializer.parse_args([])
        assert spec is None
        assert skin_index is None
        assert err is not None
        assert "用法" in err

    def test_parse_args_invalid_custom(self):
        spec, skin_index, err = self.initializer.parse_args(["10", "10"])
        assert spec is None
        assert err is not None

    def test_parse_args_mine_too_many(self):
        spec, skin_index, err = self.initializer.parse_args(["5", "5", "30"])
        assert spec is None
        assert err is not None
        assert "雷数必须小于格子总数" in err

    def test_parse_args_zero_rows(self):
        spec, skin_index, err = self.initializer.parse_args(["0", "10", "5"])
        assert spec is None
        assert err is not None
        assert "行数和列数必须大于 0" in err

    def test_parse_args_negative_mines(self):
        spec, skin_index, err = self.initializer.parse_args(["10", "10", "0"])
        assert spec is None
        assert err is not None
        assert "雷数必须大于 0" in err

    def test_parse_args_advanced(self):
        spec, skin_index, err = self.initializer.parse_args(["高级"])
        assert spec is not None
        assert spec.rows == 16
        assert spec.cols == 30
        assert spec.mines == 99
        assert err is None

    def test_parse_args_unknown_difficulty(self):
        spec, skin_index, err = self.initializer.parse_args(["未知难度"])
        assert spec is None
        assert err is not None

    def test_parse_args_skin_index_zero(self):
        spec, skin_index, err = self.initializer.parse_args(["初级", "0"])
        assert spec is not None
        assert skin_index == 0
        assert err is None

    def test_parse_args_non_numeric_skin(self):
        spec, skin_index, err = self.initializer.parse_args(["初级", "abc"])
        assert spec is not None
        assert skin_index is None
        assert err is None

    def test_parse_args_custom_with_keyword_and_skin(self):
        spec, skin_index, err = self.initializer.parse_args(
            ["自定义", "12", "12", "25", "2"]
        )
        assert spec is not None
        assert spec.rows == 12
        assert spec.cols == 12
        assert spec.mines == 25
        assert skin_index == 2
        assert err is None

    def test_parse_args_custom_with_keyword_partial_invalid(self):
        spec, skin_index, err = self.initializer.parse_args(
            ["自定义", "abc", "12", "25"]
        )
        assert spec is None
        assert err is not None

    def test_parse_args_custom_numbers_with_skin(self):
        spec, skin_index, err = self.initializer.parse_args(["8", "8", "15", "1"])
        assert spec is not None
        assert spec.rows == 8
        assert spec.cols == 8
        assert spec.mines == 15
        assert skin_index == 1
        assert err is None
