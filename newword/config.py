# -*- coding: utf-8 -*-
"""配置加载模块

从 INI 格式的配置文件中加载 Nagao 新词发现算法的参数，
并将其封装为结构化的配置对象。

配置文件格式示例（与原始 newword.utf8.conf 兼容）：
    [newword]
    n_freq=10
    n_pmi=0.000001
    n_av=5
    n_eta=0.6
    n_size=2
    n_gram=8
    n_threshold=0.01

    [dictionary]
    punct=punct.utf8.dat

    [default]
    filecode=utf8
"""

import configparser
import os
from dataclasses import dataclass
from importlib import resources
from typing import Optional, Set


@dataclass
class NewwordConfig:
    """Nagao 新词发现算法的配置参数

    Attributes:
        min_freq: 最小词频阈值，出现次数低于此值的候选词被过滤
        min_pmi: 最小点互信息阈值，用于数字字母组合词的过滤
        min_av: 最小邻字种数阈值，左右邻字种数的较小值低于此值被过滤
        min_eta: 最小左右均衡值阈值，均衡值低于此值被过滤
        min_size: 最短词长度，短于此长度的候选词被过滤
        max_gram: 最大 n-gram 长度，超过此长度的子串不参与统计
        min_threshold: 最小成词概率阈值，成词概率低于此值被过滤
        filecode: 文件编码（如 utf8、gbk）
        punct_set: 标点符号集合，集合中的字符作为分隔符不参与成词
    """

    min_freq: int
    min_pmi: float
    min_av: int
    min_eta: float
    min_size: int
    max_gram: int
    min_threshold: float
    filecode: str
    punct_set: Set[str]

    @classmethod
    def from_file(cls, config_path: str) -> "NewwordConfig":
        """从 INI 配置文件加载配置

        配置文件中的参数名保持与原始格式兼容（n_freq, n_pmi 等），
        内部映射为语义清晰的属性名。

        标点文件的路径解析规则：
        - 如果配置文件中的 punct 路径为绝对路径，直接使用
        - 如果为相对路径，解析为相对于配置文件所在目录的路径
        - 如果相对于配置文件的路径不存在，尝试从包内置数据目录查找

        Args:
            config_path: 配置文件的路径

        Returns:
            加载后的 NewwordConfig 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            configparser.Error: 配置文件格式错误
        """
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        cf = configparser.ConfigParser()
        cf.read(config_path, encoding="utf-8")

        # 读取算法参数
        min_freq = cf.getint("newword", "n_freq")
        min_pmi = float(cf.get("newword", "n_pmi"))
        min_av = cf.getint("newword", "n_av")
        min_eta = float(cf.get("newword", "n_eta"))
        min_size = cf.getint("newword", "n_size")
        max_gram = cf.getint("newword", "n_gram")
        min_threshold = float(cf.get("newword", "n_threshold"))

        # 读取文件编码
        filecode = cf.get("default", "filecode")

        # 读取并定位标点符号文件
        punct_filename = cf.get("dictionary", "punct")
        punct_path = _resolve_punct_path(punct_filename, config_path)
        filecode_for_punct = filecode if filecode != "utf8" else "utf-8"

        # 加载标点符号集
        punct_set = set()
        if punct_path is not None:
            with open(punct_path, "r", encoding=filecode_for_punct) as f:
                punct_set = {w.strip() for w in f}
        # 空格和制表符始终作为分隔符
        punct_set.add(" ")
        punct_set.add("\t")

        return cls(
            min_freq=min_freq,
            min_pmi=min_pmi,
            min_av=min_av,
            min_eta=min_eta,
            min_size=min_size,
            max_gram=max_gram,
            min_threshold=min_threshold,
            filecode=filecode,
            punct_set=punct_set,
        )

    @classmethod
    def default(cls) -> "NewwordConfig":
        """使用默认的 UTF-8 配置创建实例

        从包内置的 newword.utf8.conf 加载配置。

        Returns:
            默认配置的 NewwordConfig 实例
        """
        config_path = _get_builtin_config_path("newword.utf8.conf")
        return cls.from_file(config_path)


def _resolve_punct_path(punct_filename: str, config_path: str) -> Optional[str]:
    """解析标点符号文件的实际路径

    依次尝试以下路径：
    1. 相对于配置文件所在目录
    2. 包内置数据目录

    Args:
        punct_filename: 配置文件中指定的标点文件名
        config_path: 配置文件的路径

    Returns:
        标点文件的实际路径，找不到时返回 None
    """
    # 优先：相对于配置文件所在目录
    config_dir = os.path.dirname(os.path.abspath(config_path))
    candidate = os.path.join(config_dir, punct_filename)
    if os.path.isfile(candidate):
        return candidate

    # 回退：包内置数据目录
    builtin_path = _get_builtin_data_path(punct_filename)
    if builtin_path is not None and os.path.isfile(builtin_path):
        return builtin_path

    return None


def _get_builtin_config_path(filename: str) -> str:
    """获取包内置配置文件的路径

    Args:
        filename: 配置文件名

    Returns:
        配置文件的绝对路径

    Raises:
        FileNotFoundError: 内置配置文件不存在
    """
    # Python 3.9+ 使用 importlib.resources.files
    try:
        data_dir = resources.files("newword") / "data"
        path = data_dir.joinpath(filename)
        # 尝试获取文件系统路径
        return str(path)
    except (AttributeError, TypeError):
        # 回退：基于 __file__ 定位
        package_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(package_dir, "data", filename)


def _get_builtin_data_path(filename: str) -> Optional[str]:
    """获取包内置数据文件的路径

    Args:
        filename: 数据文件名

    Returns:
        数据文件的绝对路径，不存在时返回 None
    """
    try:
        data_dir = resources.files("newword") / "data"
        path = data_dir.joinpath(filename)
        result = str(path)
        return result if os.path.isfile(result) else None
    except (AttributeError, TypeError):
        package_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(package_dir, "data", filename)
        return candidate if os.path.isfile(candidate) else None
