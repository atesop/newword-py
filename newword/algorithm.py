# -*- coding: utf-8 -*-
"""Nagao 新词发现核心算法模块

实现基于 Nagao 算法的新词发现，核心流程：
1. 正向读取语料 → 构建排序后缀词表 → 计算右邻字种数
2. 反向读取语料 → 构建排序后缀词表 → 计算左邻字种数
3. 综合词频、左右邻信息、PMI（点互信息）等指标过滤并输出候选新词

statresults 数据结构说明：
    键为候选词字符串，值为包含以下字段的字典：
    - "freq": 词频（仅在正向扫描时记录）
    - "left_variety": 左邻字种数（在反向扫描时填充）
    - "right_variety": 右邻字种数（在正向扫描时填充）
    - "length": 词长度（仅在正向扫描时记录）

注意：原始代码中 statresults 使用数字键（1=词频, 2=左邻, 3=右邻, 4=词长），
重构后替换为语义清晰的字符串键，以提高可读性。
"""

from enum import Enum
from typing import Dict, Generator, Set, Tuple

from .config import NewwordConfig
from .corpus import read_corpus
from .stats import common_prefix_length, count_substrings, eta_mean, thres_mean


class VarietySide(Enum):
    """邻字种数的方向枚举

    用于标识当前扫描正在计算左邻还是右邻字种数。
    原始代码中使用整数 2 表示左邻、3 表示右邻。
    """

    LEFT = 2
    RIGHT = 3


class Newword:
    """Nagao 新词发现算法的核心实现

    通过两遍扫描语料（正向和反向），统计候选词的词频、左右邻字种数，
    再根据 PMI、均衡值、成词概率等指标过滤出可能的新词。

    Attributes:
        config: 算法配置参数
        statresults: 候选词统计结果字典，键为候选词，值为统计信息字典
        alnum_dict: 数字字母组合的词频字典
    """

    def __init__(self, config: NewwordConfig) -> None:
        """初始化新词发现器

        Args:
            config: NewwordConfig 配置对象
        """
        self.config = config
        self.statresults: Dict[str, Dict[str, int]] = {}
        self.alnum_dict: Dict[str, int] = {}

    def _compute_variety(
        self,
        is_forward_pass: bool,
        variety_side: VarietySide,
        word_dict: Dict[str, int],
        prefix_list: list,
        lcp_list: list,
        b_len: int,
        e_len: int,
    ) -> None:
        """基于排序后缀词表计算邻字种数

        这是 Nagao 算法的核心步骤。利用排序后的后缀列表和最长公共前缀(LCP)数组，
        高效地统计每个候选词在给定长度范围内的邻字种数。

        算法原理：
        - 排序后的后缀列表中，具有相同前缀的子串会相邻排列
        - LCP 数组记录相邻子串的公共前缀长度
        - 通过遍历 LCP 数组，可以高效计算相同前缀的词频和邻字种数

        注意：此方法会修改 self.statresults，这是算法核心的聚合步骤。

        Args:
            is_forward_pass: 是否为正向扫描。
                True 表示正向扫描（同时记录词频和词长），
                False 表示反向扫描（仅记录邻字种数）
            variety_side: 邻字种数的方向（LEFT 或 RIGHT）
            word_dict: 子串词频字典
            prefix_list: 排序后的后缀列表
            lcp_list: 最长公共前缀长度数组（相邻项的 LCP）
            b_len: 起始词长
            e_len: 结束词长（不含）
        """
        nlr = variety_side.value  # 2=左邻, 3=右邻

        for i in range(b_len, e_len):
            # 找到第一个长度 >= i 的后缀作为起点
            j = 0
            while j < len(prefix_list) and len(prefix_list[j]) < i:
                j += 1
            if j == len(prefix_list):
                continue

            # 当前候选词：取后缀的前 i 个字符
            x_word = prefix_list[j][:i]
            # 反向扫描时，候选词需要反转回来
            if nlr == VarietySide.LEFT.value:
                x_word = x_word[::-1]

            # 累计当前候选词的词频
            x_count = word_dict[prefix_list[j]]
            # 邻字种数：如果后缀恰好长度为 i，则邻字种数等于词频；
            # 否则说明该后缀延伸了当前候选词，邻字种数 +1
            if len(prefix_list[j]) == i:
                x_variety = word_dict[prefix_list[j]]
            else:
                x_variety = 1

            # 遍历后续后缀，按 LCP 分组统计
            for k in range(j, len(lcp_list)):
                if lcp_list[k] >= i:
                    # 当前后缀与下一个后缀共享至少 i 个前缀字符
                    x_count += word_dict[prefix_list[k + 1]]
                    if lcp_list[k] == i:
                        # LCP 恰好为 i，说明下一个后缀延伸了当前候选词
                        if len(prefix_list[k + 1]) == i:
                            x_variety += word_dict[prefix_list[k + 1]]
                        else:
                            x_variety += 1
                else:
                    # LCP < i，说明当前候选词的前缀组结束，记录结果
                    if len(x_word) == i:
                        if is_forward_pass:
                            self.statresults.setdefault(x_word, {})["freq"] = x_count
                        self.statresults.setdefault(x_word, {})["length"] = i
                        self.statresults.setdefault(x_word, {})[nlr] = x_variety

                    # 开始新的前缀组
                    x_count = word_dict[prefix_list[k + 1]]
                    if len(prefix_list[k + 1]) == i:
                        x_variety = word_dict[prefix_list[k + 1]]
                    else:
                        x_variety = 1
                    x_word = prefix_list[k + 1][:i]
                    if nlr == VarietySide.LEFT.value:
                        x_word = x_word[::-1]

            # 处理最后一个前缀组
            if len(x_word) == i:
                if is_forward_pass:
                    self.statresults.setdefault(x_word, {})["freq"] = x_count
                self.statresults.setdefault(x_word, {})["length"] = i
                self.statresults.setdefault(x_word, {})[nlr] = x_variety

    def filter_results(self) -> Generator:
        """根据阈值过滤候选词，生成最终结果

        过滤条件：
        1. 词长度 >= min_size
        2. 词频 >= min_freq
        3. 左右邻字种数的较小值 >= min_av
        4. 左右均衡值 >= min_eta
        5. 对所有可能的切分点计算 PMI，取最小值 min_pmi
        6. 成词概率 >= min_threshold

        数字字母组合单独处理：只要词频 >= min_freq 就输出。

        Yields:
            (word, freq, left_variety, right_variety, min_pmi, eta, threshold) 元组
        """
        for sr, sr_dict in self.statresults.items():
            # 计算左右均衡值
            sr_eta_mean = eta_mean(sr_dict[VarietySide.LEFT.value], sr_dict[VarietySide.RIGHT.value])

            # 应用基本过滤条件
            if (
                sr_dict["length"] < self.config.min_size
                or sr_dict["freq"] < self.config.min_freq
                or min(sr_dict[VarietySide.LEFT.value], sr_dict[VarietySide.RIGHT.value]) < self.config.min_av
                or sr_eta_mean < self.config.min_eta
            ):
                continue

            # 计算最小 PMI（点互信息）
            # 对候选词的所有可能切分点，计算 PMI = freq(word) / freq(left_part) / freq(right_part)
            # 取最小值作为该词的 PMI 指标
            min_pmi = float("inf")
            for j in range(1, sr_dict["length"]):
                tmp_pmi = sr_dict["freq"] / (
                    self.statresults[sr[:j]]["freq"] * self.statresults[sr[j:]]["freq"]
                )
                if min_pmi > tmp_pmi:
                    min_pmi = tmp_pmi

            # 计算成词概率
            sr_threshold = thres_mean(
                sr_dict["freq"],
                sr_dict[VarietySide.RIGHT.value],
                sr_dict[VarietySide.LEFT.value],
                min_pmi,
            )
            if sr_threshold > self.config.min_threshold:
                yield (
                    sr,
                    sr_dict["freq"],
                    sr_dict[VarietySide.LEFT.value],
                    sr_dict[VarietySide.RIGHT.value],
                    min_pmi,
                    sr_eta_mean,
                    sr_threshold,
                )

        # 处理数字字母组合
        for sr, count in self.alnum_dict.items():
            if count >= self.config.min_freq:
                yield sr, count, count, count, self.config.min_pmi, self.config.min_eta, self.config.min_threshold

    def process(self, file_corpus: str) -> Generator:
        """执行 Nagao 新词发现算法的完整流程

        流程：
        1. 正向读取语料 → 构建排序后缀词表 → 计算词频和右邻字种数
        2. 反向读取语料 → 构建排序后缀词表 → 计算左邻字种数
        3. 综合过滤并输出结果

        注意：语料文件会被读取两次，在程序执行完毕之前不要修改语料文件。

        Args:
            file_corpus: 语料文件路径

        Yields:
            (word, freq, left_variety, right_variety, min_pmi, eta, threshold) 元组
        """
        # 第一遍：正向扫描，计算词频和右邻字种数
        word_dict, self.alnum_dict = read_corpus(
            file_corpus, self.config.filecode, self.config.punct_set, reverse=False
        )
        prefix_list = list(sorted(word_dict))
        lcp_list = [common_prefix_length(prefix_list[i], prefix_list[i + 1]) for i in range(len(prefix_list) - 1)]
        self._compute_variety(
            is_forward_pass=True,
            variety_side=VarietySide.RIGHT,
            word_dict=word_dict,
            prefix_list=prefix_list,
            lcp_list=lcp_list,
            b_len=1,
            e_len=self.config.max_gram,
        )

        # 第二遍：反向扫描，计算左邻字种数
        word_dict, _ = read_corpus(
            file_corpus, self.config.filecode, self.config.punct_set, reverse=True
        )
        prefix_list = list(sorted(word_dict))
        lcp_list = [common_prefix_length(prefix_list[i], prefix_list[i + 1]) for i in range(len(prefix_list) - 1)]
        self._compute_variety(
            is_forward_pass=False,
            variety_side=VarietySide.LEFT,
            word_dict=word_dict,
            prefix_list=prefix_list,
            lcp_list=lcp_list,
            b_len=1,
            e_len=self.config.max_gram,
        )

        # 释放中间数据
        del word_dict, prefix_list, lcp_list

        return self.filter_results()
