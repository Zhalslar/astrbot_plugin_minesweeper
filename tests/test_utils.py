from core.utils import (
    tokenize_positions,
    expand_position_token,
    parse_position_tokens,
    parse_position,
)


class TestTokenizePositions:
    """测试 tokenize_positions 函数"""

    def test_single_position(self):
        assert tokenize_positions("a1") == ["a1"]

    def test_multiple_space_separated(self):
        assert tokenize_positions("a1 b2 c3") == ["a1", "b2", "c3"]

    def test_continuous_no_space(self):
        assert tokenize_positions("a1b2c3") == ["a1", "b2", "c3"]

    def test_mixed_space_and_continuous(self):
        assert tokenize_positions("a1 b2c3") == ["a1", "b2", "c3"]

    def test_col_range(self):
        assert tokenize_positions("a1-5") == ["a1-5"]
        assert tokenize_positions("a1-5 b1-3") == ["a1-5", "b1-3"]

    def test_row_range(self):
        assert tokenize_positions("a-c5") == ["a-c5"]

    def test_rect_range(self):
        assert tokenize_positions("a1-b2") == ["a1-b2"]
        assert tokenize_positions("a1-c3") == ["a1-c3"]
        assert tokenize_positions("a1-5 b1-c3") == ["a1-5", "b1-c3"]

    def test_continuous_with_ranges(self):
        assert tokenize_positions("a1-5b1-3") == ["a1-5", "b1-3"]

    def test_mixed_continuous_and_ranges(self):
        assert tokenize_positions("a1b-c5d1-3") == ["a1", "b-c5", "d1-3"]

    def test_with_quote_prefix(self):
        # tokenize_positions 不负责处理引号，引号在前置处理中去除
        assert tokenize_positions("'a1b2") == ["a1", "b2"]

    def test_with_chinese_prefix(self):
        assert tokenize_positions("标雷 a1b2") == ["a1", "b2"]

    def test_complex_mixed(self):
        assert tokenize_positions("a1b2 c3d4-6 e5-10") == [
            "a1",
            "b2",
            "c3",
            "d4-6",
            "e5-10",
        ]

    def test_empty_string(self):
        assert tokenize_positions("") == []

    def test_invalid_text(self):
        assert tokenize_positions("hello") == []
        assert tokenize_positions("123") == []


class TestExpandPositionToken:
    """测试单个位置令牌扩展"""

    def test_single_position_lowercase(self):
        assert expand_position_token("a1") == ["a1"]
        assert expand_position_token("c5") == ["c5"]

    def test_single_position_uppercase(self):
        assert expand_position_token("A1") == ["a1"]
        assert expand_position_token("C5") == ["c5"]

    def test_row_range_ascending(self):
        assert expand_position_token("a-c5") == ["a5", "b5", "c5"]

    def test_row_range_descending(self):
        assert expand_position_token("c-a5") == ["c5", "b5", "a5"]

    def test_col_range_ascending(self):
        assert expand_position_token("a1-5") == ["a1", "a2", "a3", "a4", "a5"]

    def test_col_range_descending(self):
        assert expand_position_token("a5-1") == ["a5", "a4", "a3", "a2", "a1"]

    def test_invalid_token(self):
        assert expand_position_token("invalid") is None
        assert expand_position_token("1a") is None


class TestParsePositionTokens:
    """测试多个位置令牌解析"""

    def test_continuous_no_space(self):
        tokens = tokenize_positions("a1b2c3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b2", "c3"]
        assert invalid == []

    def test_mixed_continuous_and_ranges(self):
        tokens = tokenize_positions("a1b-c5d1-3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b5", "c5", "d1", "d2", "d3"]
        assert invalid == []

    def test_with_spaces(self):
        tokens = tokenize_positions("a1 b2 c3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b2", "c3"]
        assert invalid == []

    def test_complex_input(self):
        tokens = tokenize_positions("a1-3b-d5e1")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "a2", "a3", "b5", "c5", "d5", "e1"]
        assert invalid == []

    def test_invalid_tokens_collected(self):
        tokens = ["a1", "invalid", "b2"]
        positions, invalid = parse_position_tokens(tokens)
        assert "a1" in positions
        assert "b2" in positions
        assert invalid == ["invalid"]

    def test_all_invalid_tokens(self):
        tokens = ["invalid", "hello", "123"]
        positions, invalid = parse_position_tokens(tokens)
        assert positions == []
        assert invalid == ["invalid", "hello", "123"]

    def test_mixed_valid_invalid_ranges(self):
        tokens = ["a-c5", "invalid", "d1-3", "bad"]
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a5", "b5", "c5", "d1", "d2", "d3"]
        assert invalid == ["invalid", "bad"]


class TestCommandScenarios:
    """测试实际命令场景"""

    def test_scenario_continuous_click_a1b2c3(self):
        tokens = tokenize_positions("a1b2c3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b2", "c3"]
        assert invalid == []
        assert parse_position(positions[0]) == (0, 0)
        assert parse_position(positions[1]) == (1, 1)
        assert parse_position(positions[2]) == (2, 2)

    def test_scenario_continuous_with_ranges(self):
        tokens = tokenize_positions("a1-3b1-3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "a2", "a3", "b1", "b2", "b3"]
        assert invalid == []

    def test_scenario_row_range_a_c10(self):
        tokens = tokenize_positions("a-c10")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a10", "b10", "c10"]
        assert invalid == []

    def test_scenario_mixed_input(self):
        tokens = tokenize_positions("a1b-c5d1-3")
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b5", "c5", "d1", "d2", "d3"]
        assert invalid == []

    def test_scenario_full_row_sweep(self):
        tokens = tokenize_positions("a-z1")
        positions, invalid = parse_position_tokens(tokens)
        assert len(positions) == 26
        assert positions[0] == "a1"
        assert positions[-1] == "z1"


class TestQuotePrefixMark:
    """测试小引号 ' 标雷功能"""

    def test_quote_single(self):
        text = "'a1"
        if text.startswith("'"):
            text = text[1:]
        tokens = tokenize_positions(text)
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1"]

    def test_quote_multiple(self):
        text = "'a1b2c3"
        if text.startswith("'"):
            text = text[1:]
        tokens = tokenize_positions(text)
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b2", "c3"]

    def test_quote_with_ranges(self):
        text = "'a-c5d1-3"
        if text.startswith("'"):
            text = text[1:]
        tokens = tokenize_positions(text)
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a5", "b5", "c5", "d1", "d2", "d3"]

    def test_chinese_prefix_biao_lei(self):
        text = "标雷 a1b2"
        if text.startswith("标雷"):
            text = text[2:]
        tokens = tokenize_positions(text.strip())
        positions, invalid = parse_position_tokens(tokens)
        assert positions == ["a1", "b2"]
