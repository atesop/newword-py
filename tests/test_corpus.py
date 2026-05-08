# -*- coding: utf-8 -*-
"""语料处理模块的单元测试"""

import os
import tempfile

import pytest

from newword.corpus import read_corpus, split_line


class TestSplitLine:
    """split_line 函数测试"""

    @pytest.fixture
    def basic_punct_set(self):
        """基本标点集"""
        return {"，", "。", "！", "？", " ", "\t"}

    def test_simple_line(self, basic_punct_set):
        """简单中文行，无标点"""
        word_dict, alnum_dict = split_line("自然语言处理", basic_punct_set, "utf8")
        # 应统计所有后缀子串
        assert "自然语言处理" in word_dict
        assert "语言处理" in word_dict
        assert len(alnum_dict) == 0

    def test_line_with_punctuation(self, basic_punct_set):
        """含标点的行：按标点分割"""
        word_dict, alnum_dict = split_line("自然语言，人工智能", basic_punct_set, "utf8")
        # "自然语言" 和 "人工智能" 分别统计
        assert "自然语言" in word_dict
        assert "人工智能" in word_dict

    def test_alnum_segment(self, basic_punct_set):
        """数字字母组合片段不参与成词"""
        word_dict, alnum_dict = split_line("CPU", basic_punct_set, "utf8")
        # CPU 编码后 isalnum() 为 True，应放入 alnum_dict
        # split_line 不做 lower()，保留原始大小写
        assert "CPU" in alnum_dict
        assert "CPU" not in word_dict

    def test_mixed_content(self, basic_punct_set):
        """混合内容：中文和数字字母"""
        word_dict, alnum_dict = split_line("模型GPT4技术", basic_punct_set, "utf8")
        # 无标点分割，整个行作为片段
        # "模型GPT4技术" 编码后非纯 alnum（含中文），所以参与成词
        # split_line 不做 lower()，保留原始大小写
        assert "模型GPT4技术" in word_dict

    def test_empty_line(self, basic_punct_set):
        """空行"""
        word_dict, alnum_dict = split_line("", basic_punct_set, "utf8")
        assert word_dict == {}
        assert alnum_dict == {}

    def test_reverse_mode(self, basic_punct_set):
        """反向模式：文本被反转"""
        word_dict, alnum_dict = split_line("自然语言", basic_punct_set, "utf8", reverse=True)
        # 反转后 "自然语言" → "言语然自"
        assert "言语然自" in word_dict

    def test_punctuation_at_edges(self, basic_punct_set):
        """标点在行首或行尾"""
        word_dict, alnum_dict = split_line("。自然语言。", basic_punct_set, "utf8")
        assert "自然语言" in word_dict

    def test_consecutive_punctuation(self, basic_punct_set):
        """连续标点"""
        word_dict, alnum_dict = split_line("自然，，语言", basic_punct_set, "utf8")
        assert "自然" in word_dict
        assert "语言" in word_dict

    def test_chinese_not_alnum(self, basic_punct_set):
        """中文字符不被误判为 alnum"""
        word_dict, alnum_dict = split_line("自然语言", basic_punct_set, "utf8")
        # 中文字符使用 .encode("utf8").isalnum() 应返回 False
        assert len(alnum_dict) == 0
        assert len(word_dict) > 0


class TestReadCorpus:
    """read_corpus 函数测试"""

    @pytest.fixture
    def basic_punct_set(self):
        """基本标点集"""
        return {"，", "。", "！", "？", " ", "\t"}

    def test_read_small_corpus(self, sample_corpus_path, basic_punct_set):
        """读取示例语料文件"""
        word_dict, alnum_dict = read_corpus(sample_corpus_path, "utf-8", basic_punct_set)
        # 语料无标点，整行作为片段，统计后缀子串
        # 最后一行 "深度学习是机器学习的一个分支" 的后缀 "分支" 出现 2 次
        assert word_dict.get("分支", 0) == 2
        # 验证字典非空
        assert len(word_dict) > 0

    def test_read_corpus_reverse(self, sample_corpus_path, basic_punct_set):
        """反向读取语料"""
        word_dict, alnum_dict = read_corpus(sample_corpus_path, "utf-8", basic_punct_set, reverse=True)
        # 反转后行的后缀子串会以反转后的行首字符开头
        # 第一行 "自然语言处理是人工智能的重要分支" 反转为 "支分要重的能智工人是理处言语然自"
        # 所以存在以 "支分" 开头的后缀子串
        assert any(k.startswith("支分") for k in word_dict)

    def test_read_nonexistent_file(self, basic_punct_set):
        """读取不存在的文件抛出异常"""
        with pytest.raises(FileNotFoundError):
            read_corpus("/nonexistent/corpus.txt", "utf-8", basic_punct_set)

    def test_merge_counts(self, basic_punct_set):
        """多行语料的词频正确合并"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("自然语言\n")
            f.write("自然语言\n")
            temp_path = f.name

        try:
            word_dict, _ = read_corpus(temp_path, "utf-8", basic_punct_set)
            # "自然语言" 出现 2 次
            assert word_dict["自然语言"] == 2
        finally:
            os.unlink(temp_path)
