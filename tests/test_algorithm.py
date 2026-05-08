# -*- coding: utf-8 -*-
"""核心算法模块的单元测试"""

import os
import tempfile

import pytest

from newword.algorithm import Newword, VarietySide
from newword.config import NewwordConfig


@pytest.fixture
def test_config():
    """创建测试用配置（低阈值）"""
    return NewwordConfig(
        min_freq=2,
        min_pmi=1e-6,
        min_av=1,
        min_eta=0.3,
        min_size=2,
        max_gram=8,
        min_threshold=0.001,
        filecode="utf8",
        punct_set={"，", "。", "！", "？", " ", "\t"},
    )


@pytest.fixture
def default_config():
    """创建默认配置"""
    return NewwordConfig.default()


class TestNewwordInit:
    """Newword 初始化测试"""

    def test_init_with_config(self, test_config):
        """使用配置对象初始化"""
        nw = Newword(test_config)
        assert nw.config.min_freq == 2
        assert nw.statresults == {}
        assert nw.alnum_dict == {}


class TestProcess:
    """process 方法测试"""

    def test_process_returns_results(self, test_config, sample_corpus_path):
        """process 返回非空结果"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        assert len(results) > 0

    def test_process_result_format(self, test_config, sample_corpus_path):
        """process 结果格式正确：7 元组"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for result in results:
            assert len(result) == 7
            word, freq, left, right, pmi, eta, threshold = result
            assert isinstance(word, str)
            assert isinstance(freq, int)
            assert freq >= test_config.min_freq

    def test_process_word_length_filter(self, test_config, sample_corpus_path):
        """所有输出词长度 >= min_size"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for word, *_ in results:
            assert len(word) >= test_config.min_size

    def test_process_freq_filter(self, test_config, sample_corpus_path):
        """所有输出词频 >= min_freq"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for _, freq, *_ in results:
            assert freq >= test_config.min_freq

    def test_process_av_filter(self, test_config, sample_corpus_path):
        """所有输出词左右邻最小值 >= min_av"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for _, _, left, right, _, _, _ in results:
            assert min(left, right) >= test_config.min_av

    def test_process_eta_filter(self, test_config, sample_corpus_path):
        """所有输出词均衡值 >= min_eta"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for _, _, _, _, _, eta, _ in results:
            assert eta >= test_config.min_eta

    def test_process_threshold_filter(self, test_config, sample_corpus_path):
        """所有输出词成词概率 > min_threshold"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))
        for _, _, _, _, _, _, threshold in results:
            assert threshold > test_config.min_threshold


class TestRegression:
    """回归测试：与原始代码输出对比"""

    def test_output_matches_golden(self, test_config, sample_corpus_path, golden_output_path):
        """输出与 golden output 一致"""
        nw = Newword(test_config)
        results = list(nw.process(sample_corpus_path))

        # 读取 golden output
        with open(golden_output_path, "r", encoding="utf-8") as f:
            golden_lines = [line.strip() for line in f if line.strip()]

        # 对比行数
        assert len(results) == len(golden_lines), (
            f"结果行数不匹配：实际 {len(results)}，期望 {len(golden_lines)}"
        )

        # 逐行对比
        for result, golden_line in zip(results, golden_lines):
            golden_parts = golden_line.split(",")
            assert len(golden_parts) == 7

            word, freq, left, right, pmi, eta, threshold = result
            assert word == golden_parts[0]
            assert freq == int(golden_parts[1])
            assert left == int(golden_parts[2])
            assert right == int(golden_parts[3])
            assert pmi == pytest.approx(float(golden_parts[4]))
            assert eta == pytest.approx(float(golden_parts[5]))
            assert threshold == pytest.approx(float(golden_parts[6]))


class TestVarietySide:
    """VarietySide 枚举测试"""

    def test_left_value(self):
        """LEFT 枚举值为 2"""
        assert VarietySide.LEFT.value == 2

    def test_right_value(self):
        """RIGHT 枚举值为 3"""
        assert VarietySide.RIGHT.value == 3


class TestDefaultConfigProcess:
    """默认配置下的处理测试"""

    def test_default_config_higher_threshold(self, default_config, sample_corpus_path):
        """默认配置的阈值较高，小语料可能无输出"""
        nw = Newword(default_config)
        results = list(nw.process(sample_corpus_path))
        # 小语料在默认阈值下可能没有结果，这是预期行为
        # 主要验证不报错即可
        assert isinstance(results, list)

    def test_empty_corpus(self, test_config):
        """空语料文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("")
            temp_path = f.name

        try:
            nw = Newword(test_config)
            results = list(nw.process(temp_path))
            assert results == []
        finally:
            os.unlink(temp_path)
