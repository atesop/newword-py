# -*- coding: utf-8 -*-
"""统计工具函数模块

提供 Nagao 新词发现算法所需的底层统计计算函数，包括：
- 公共前缀长度计算（用于构建前缀树式的词频统计）
- 左右邻均衡值计算
- 成词概率阈值计算
- 子串词频统计
"""

from collections import defaultdict
from math import sqrt
from typing import Dict


def common_prefix_length(str1: str, str2: str) -> int:
    """计算两个字符串的公共前缀长度

    在 Nagao 算法中，排序后的词表相邻项的公共前缀长度用于
    快速定位具有相同前缀的词组，避免重复遍历。

    Args:
        str1: 第一个字符串
        str2: 第二个字符串

    Returns:
        公共前缀的字符数
    """
    i = 0
    while i < len(str1) and i < len(str2):
        if str1[i] == str2[i]:
            i += 1
        else:
            return i
    return i


def eta_mean(a: int, b: int) -> float:
    """计算左右邻字种数的均衡值

    使用公式 2ab/(a²+b²) 衡量左右邻字种数的均衡程度。
    当左右邻字种数相等时取最大值 1.0，差异越大值越小。

    Args:
        a: 左邻字种数（或右邻字种数）
        b: 右邻字种数（或左邻字种数）

    Returns:
        均衡值，范围 [0, 1]。a 和 b 均为 0 时返回 0
    """
    if a == 0 and b == 0:
        return 0.0
    return 2.0 * a * b / (a * a + b * b)


def thres_mean(freq: int, left_variety: int, right_variety: int, min_pmi: float) -> float:
    """计算成词概率阈值

    综合词频、左右邻信息与最小点互信息(PMI)计算成词概率。
    公式：sqrt(freq) / (1/left + 1/right) * min_pmi

    词频越高、左右邻越丰富且均衡、PMI 越高，成词概率越大。

    Args:
        freq: 词频
        left_variety: 左邻字种数
        right_variety: 右邻字种数
        min_pmi: 最小点互信息值（所有可能切分中 PMI 的最小值）

    Returns:
        成词概率值
    """
    return sqrt(freq) / (1.0 / left_variety + 1.0 / right_variety) * min_pmi


def count_substrings(line: str, word_dict: Dict[str, int]) -> None:
    """统计字符串中所有后缀子串的出现次数

    对于输入字符串 "abc"，会统计以下子串各出现 1 次：
    "abc", "bc", "c"。这些子串是排序后计算公共前缀的基础数据。

    注意：此函数直接修改传入的 word_dict，累加计数。

    Args:
        line: 待统计的字符串（通常是按标点分割后的一个片段）
        word_dict: 词频字典，键为子串，值为出现次数，会被原地修改
    """
    for i in range(len(line)):
        word = line[i:]
        word_dict[word] = word_dict.get(word, 0) + 1
