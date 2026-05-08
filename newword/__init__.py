# -*- coding: utf-8 -*-
"""Nagao 新词发现工具

基于 Nagao 算法的轻量级新词发现与领域词典构建工具。

核心功能：
- 统计语料中可能成词的字符串频次
- 支持自定义分隔符与编码（UTF-8/GBK）
- 过滤数字字母组合（直接统计词频，不参与成词判断）
- 输出结果供领域词典建设使用

用法示例：
    >>> from newword import Newword, NewwordConfig
    >>> config = NewwordConfig.default()
    >>> nw = Newword(config)
    >>> for result in nw.process("corpus.txt"):
    ...     print(result)
"""

from .algorithm import Newword, VarietySide
from .config import NewwordConfig
from .stats import common_prefix_length, count_substrings, eta_mean, thres_mean

__all__ = [
    "Newword",
    "NewwordConfig",
    "VarietySide",
    "common_prefix_length",
    "count_substrings",
    "eta_mean",
    "thres_mean",
]
