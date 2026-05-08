# -*- coding: utf-8 -*-
"""统计工具函数的单元测试"""

import pytest

from newword.stats import common_prefix_length, count_substrings, eta_mean, thres_mean


class TestCommonPrefixLength:
    """common_prefix_length 函数测试"""

    def test_identical_strings(self):
        """完全相同的字符串"""
        assert common_prefix_length("abc", "abc") == 3

    def test_empty_strings(self):
        """空字符串"""
        assert common_prefix_length("", "") == 0
        assert common_prefix_length("abc", "") == 0
        assert common_prefix_length("", "abc") == 0

    def test_no_common_prefix(self):
        """无公共前缀"""
        assert common_prefix_length("abc", "xyz") == 0

    def test_partial_prefix(self):
        """部分公共前缀"""
        assert common_prefix_length("abcd", "abef") == 2

    def test_one_is_prefix_of_other(self):
        """一个是另一个的前缀"""
        assert common_prefix_length("ab", "abcd") == 2
        assert common_prefix_length("abcd", "ab") == 2

    def test_single_char_prefix(self):
        """单字符公共前缀"""
        assert common_prefix_length("apple", "apricot") == 2

    def test_chinese_characters(self):
        """中文字符"""
        assert common_prefix_length("自然语言", "自然科学") == 2
        assert common_prefix_length("深度学习", "机器学习") == 0


class TestEtaMean:
    """eta_mean 函数测试"""

    def test_equal_values(self):
        """左右相等时均衡值为 1.0"""
        assert eta_mean(5, 5) == pytest.approx(1.0)

    def test_zero_values(self):
        """均为 0 时返回 0"""
        assert eta_mean(0, 0) == 0.0

    def test_one_zero(self):
        """一个为 0 时返回 0"""
        assert eta_mean(0, 5) == pytest.approx(0.0)
        assert eta_mean(5, 0) == pytest.approx(0.0)

    def test_asymmetric_values(self):
        """不对称值"""
        # 2*1*3/(1+9) = 6/10 = 0.6
        assert eta_mean(1, 3) == pytest.approx(0.6)

    def test_symmetry(self):
        """结果对称：eta_mean(a,b) == eta_mean(b,a)"""
        assert eta_mean(3, 7) == pytest.approx(eta_mean(7, 3))

    def test_large_values(self):
        """大数值"""
        result = eta_mean(1000, 1000)
        assert result == pytest.approx(1.0)


class TestThresMean:
    """thres_mean 函数测试"""

    def test_basic_calculation(self):
        """基本计算"""
        # sqrt(4) / (1/2 + 1/2) * 0.5 = 2 / 1 * 0.5 = 1.0
        assert thres_mean(4, 2, 2, 0.5) == pytest.approx(1.0)

    def test_higher_freq_higher_threshold(self):
        """词频越高，成词概率越高"""
        low = thres_mean(4, 2, 2, 0.5)
        high = thres_mean(16, 2, 2, 0.5)
        assert high > low

    def test_higher_pmi_higher_threshold(self):
        """PMI 越高，成词概率越高"""
        low = thres_mean(4, 2, 2, 0.1)
        high = thres_mean(4, 2, 2, 0.9)
        assert high > low

    def test_balanced_variety_higher_threshold(self):
        """左右邻均衡时成词概率更高"""
        balanced = thres_mean(4, 3, 3, 0.5)
        unbalanced = thres_mean(4, 1, 5, 0.5)
        # 均衡时 1/l + 1/r 更小，成词概率更高
        assert balanced > unbalanced


class TestCountSubstrings:
    """count_substrings 函数测试"""

    def test_empty_string(self):
        """空字符串不添加任何子串"""
        word_dict = {}
        count_substrings("", word_dict)
        assert word_dict == {}

    def test_single_char(self):
        """单字符产生 1 个子串"""
        word_dict = {}
        count_substrings("a", word_dict)
        assert word_dict == {"a": 1}

    def test_multiple_chars(self):
        """多字符产生 len 个后缀子串"""
        word_dict = {}
        count_substrings("abc", word_dict)
        assert word_dict == {"abc": 1, "bc": 1, "c": 1}

    def test_duplicate_substring(self):
        """重复子串累加计数"""
        # "abc" 的后缀子串为 "abc", "bc", "c"
        # "bcd" 的后缀子串为 "bcd", "cd", "d"
        # 两者共享后缀 "c" 和 "cd" 中的 "c" 部分，但 "bc" 只出现在 "abc" 中
        word_dict = {"c": 1}
        count_substrings("cd", word_dict)
        # "cd" 的后缀: "cd", "d"；"c" 不在后缀中
        assert word_dict["c"] == 1  # "c" 不受影响
        assert word_dict["cd"] == 1

    def test_chinese_string(self):
        """中文字符串"""
        word_dict = {}
        count_substrings("自然", word_dict)
        assert word_dict == {"自然": 1, "然": 1}

    def test_in_place_modification(self):
        """原地修改传入的字典"""
        word_dict = {}
        count_substrings("ab", word_dict)
        count_substrings("ac", word_dict)
        # "a" 不在结果中（因为是后缀子串，不是前缀子串）
        assert word_dict == {"ab": 1, "b": 1, "ac": 1, "c": 1}
