# -*- coding: utf-8 -*-
"""CLI 集成测试"""

import os
import tempfile

import pytest

from newword.cli import main, parse_args


class TestParseArgs:
    """参数解析测试"""

    def test_required_args(self):
        """必选参数"""
        args = parse_args(["input.txt", "output.csv"])
        assert args.input_file == "input.txt"
        assert args.output_file == "output.csv"
        assert args.config_file is None

    def test_optional_config(self):
        """可选配置文件参数"""
        args = parse_args(["input.txt", "output.csv", "my.conf"])
        assert args.config_file == "my.conf"

    def test_missing_input_file(self):
        """缺少必选参数时报错"""
        with pytest.raises(SystemExit):
            parse_args(["output.csv"])

    def test_missing_all_args(self):
        """无参数时报错"""
        with pytest.raises(SystemExit):
            parse_args([])


class TestMainIntegration:
    """端到端集成测试"""

    def test_full_pipeline(self, sample_corpus_path, test_config_path):
        """完整流程：从语料到输出文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            main([sample_corpus_path, output_path, test_config_path])

            # 验证输出文件存在且非空
            assert os.path.exists(output_path)
            with open(output_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            assert len(lines) > 0

            # 验证 CSV 格式：7 列
            for line in lines:
                parts = line.split(",")
                assert len(parts) == 7
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_output_matches_golden(self, sample_corpus_path, test_config_path, golden_output_path):
        """端到端输出与 golden output 一致"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            main([sample_corpus_path, output_path, test_config_path])

            with open(output_path, "r", encoding="utf-8") as f:
                actual = f.read()
            with open(golden_output_path, "r", encoding="utf-8") as f:
                expected = f.read()

            assert actual == expected
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_default_config(self, sample_corpus_path):
        """使用默认配置运行"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            main([sample_corpus_path, output_path])
            # 默认配置下小语料可能无输出，主要验证不报错
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
