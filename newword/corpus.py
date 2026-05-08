# -*- coding: utf-8 -*-
"""语料读取与文本分割模块

负责从文件中读取语料，按标点符号分割文本行，
区分中文文本和数字字母组合（alnum），为 Nagao 算法提供统计输入。

核心逻辑：
- 标点符号作为分隔符，分割后的片段参与成词统计
- 数字字母组合（如 "3.5"、"CPU"）不参与成词，而是直接统计词频
- 支持正向和反向读取语料（反向用于统计左邻信息）
"""

from collections import defaultdict
from typing import Dict, Set, Tuple

from .stats import count_substrings


def split_line(
    line: str,
    punct_set: Set[str],
    filecode: str,
    reverse: bool = False,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """按标点符号分割一行文本，统计子串词频

    将文本按标点符号分割为多个片段：
    - 中文片段：调用 count_substrings 统计所有后缀子串
    - 数字字母组合片段：直接统计整个片段的出现次数

    注意：数字字母组合的判断使用 .encode(filecode).isalnum()，
    即字节级判断。这与 Python 的 str.isalnum()（字符级判断）不同：
    中文字符在字符级 isalnum() 下返回 True，但在字节级返回 False。
    保留字节级判断是为了确保中文字符不被误判为数字字母组合。

    Args:
        line: 待分割的文本行
        punct_set: 标点符号集合
        filecode: 文件编码名称，用于 isalnum() 字节级判断
        reverse: 是否反转文本（反向读取语料时使用）

    Returns:
        (word_dict, alnum_dict) 元组：
        - word_dict: 中文子串的词频字典
        - alnum_dict: 数字字母组合的词频字典
    """
    word_dict: Dict[str, int] = {}
    alnum_dict: Dict[str, int] = defaultdict(int)

    # 反向读取时，先将整行反转
    if reverse:
        line = line[::-1]

    b_pos = 0  # 当前片段的起始位置
    for i in range(len(line)):
        if line[i] in punct_set:
            # 遇到标点，提取标点前的片段
            segment = line[b_pos:i]
            _process_segment(segment, filecode, word_dict, alnum_dict)
            b_pos = i + 1

    # 处理行末最后一个片段
    if b_pos < len(line):
        segment = line[b_pos:]
        _process_segment(segment, filecode, word_dict, alnum_dict)

    return word_dict, dict(alnum_dict)


def _process_segment(
    segment: str,
    filecode: str,
    word_dict: Dict[str, int],
    alnum_dict: Dict[str, int],
) -> None:
    """处理一个被标点分割的文本片段

    判断片段是否为数字字母组合：
    - 是：直接统计整个片段的出现次数
    - 否：调用 count_substrings 统计所有后缀子串

    Args:
        segment: 文本片段
        filecode: 文件编码
        word_dict: 中文子串词频字典，会被原地修改
        alnum_dict: 数字字母组合词频字典，会被原地修改
    """
    if not segment:
        return
    # 使用字节级 isalnum() 判断数字字母组合
    if segment.encode(filecode).isalnum():
        alnum_dict[segment] += 1
    else:
        count_substrings(segment, word_dict)


def read_corpus(
    file_path: str,
    filecode: str,
    punct_set: Set[str],
    reverse: bool = False,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """读取语料文件，统计所有子串词频

    逐行读取语料文件，对每行调用 split_line 进行分割和统计，
    将结果合并到总的词频字典中。

    Args:
        file_path: 语料文件路径
        filecode: 文件编码（如 utf-8、gbk）
        punct_set: 标点符号集合
        reverse: 是否反向读取（用于统计左邻信息）

    Returns:
        (word_dict, alnum_dict) 元组：
        - word_dict: 所有中文子串的合并词频字典
        - alnum_dict: 所有数字字母组合的合并词频字典
    """
    total_word_dict: Dict[str, int] = {}
    total_alnum_dict: Dict[str, int] = defaultdict(int)

    with open(file_path, "r", encoding=filecode, errors="ignore") as f:
        for line in f:
            line = line.strip().lower()
            if not line:
                continue
            word_dict, alnum_dict = split_line(line, punct_set, filecode, reverse=reverse)
            # 合并词频
            for word, count in word_dict.items():
                total_word_dict[word] = total_word_dict.get(word, 0) + count
            for word, count in alnum_dict.items():
                total_alnum_dict[word] += count

    return total_word_dict, dict(total_alnum_dict)
