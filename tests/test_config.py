# -*- coding: utf-8 -*-
"""配置加载模块的单元测试"""

import os
import tempfile

import pytest

from newword.config import NewwordConfig


class TestNewwordConfigFromFile:
    """NewwordConfig.from_file 测试"""

    def test_load_utf8_config(self, test_config_path):
        """加载 UTF-8 配置文件"""
        config = NewwordConfig.from_file(test_config_path)
        assert config.min_freq == 2
        assert config.min_pmi == pytest.approx(1e-6)
        assert config.min_av == 1
        assert config.min_eta == pytest.approx(0.3)
        assert config.min_size == 2
        assert config.max_gram == 8
        assert config.min_threshold == pytest.approx(0.001)
        assert config.filecode == "utf8"

    def test_punct_set_loaded(self, test_config_path):
        """标点符号集正确加载"""
        config = NewwordConfig.from_file(test_config_path)
        # 测试配置中的标点文件有 18 个标点，加上空格和制表符 = 20
        assert "！" in config.punct_set
        assert "。" in config.punct_set
        # 空格和制表符始终包含
        assert " " in config.punct_set
        assert "\t" in config.punct_set

    def test_nonexistent_config_file(self):
        """不存在的配置文件抛出异常"""
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            NewwordConfig.from_file("/nonexistent/path/config.conf")

    def test_load_builtin_utf8_config(self):
        """加载内置 UTF-8 配置"""
        config = NewwordConfig.default()
        assert config.min_freq == 10
        assert config.filecode == "utf8"

    def test_load_gbk_config(self):
        """加载 GBK 配置文件"""
        # 内置的 GBK 配置
        gbk_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "newword", "data", "newword.gbk.conf"
        )
        if os.path.exists(gbk_config_path):
            config = NewwordConfig.from_file(gbk_config_path)
            assert config.filecode == "gbk"

    def test_custom_config_with_tempfile(self):
        """使用临时文件测试自定义配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False, encoding="utf-8") as f:
            f.write("[newword]\n")
            f.write("n_freq=5\n")
            f.write("n_pmi=0.001\n")
            f.write("n_av=3\n")
            f.write("n_eta=0.5\n")
            f.write("n_size=3\n")
            f.write("n_gram=6\n")
            f.write("n_threshold=0.1\n")
            f.write("\n[dictionary]\n")
            f.write("punct=punct.utf8.dat\n")
            f.write("\n[default]\n")
            f.write("filecode=utf8\n")
            temp_path = f.name

        try:
            config = NewwordConfig.from_file(temp_path)
            assert config.min_freq == 5
            assert config.min_size == 3
            assert config.max_gram == 6
        finally:
            os.unlink(temp_path)
