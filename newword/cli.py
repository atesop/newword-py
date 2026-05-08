# -*- coding: utf-8 -*-
"""命令行入口模块

提供 Nagao 新词发现工具的命令行接口。
支持两种调用方式：
    python3 -m newword input_file output_file [config_file]
    newword input_file output_file [config_file]  （安装后）
"""

import argparse
import sys

from .algorithm import Newword
from .config import NewwordConfig


def parse_args(args=None) -> argparse.Namespace:
    """解析命令行参数

    Args:
        args: 命令行参数列表，为 None 时使用 sys.argv

    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description="基于 Nagao 算法的新词发现工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python3 -m newword corpus.txt result.csv
  python3 -m newword corpus.txt result.csv newword.gbk.conf""",
    )
    parser.add_argument("input_file", help="输入语料文件路径")
    parser.add_argument("output_file", help="输出结果文件路径")
    parser.add_argument("config_file", nargs="?", default=None, help="配置文件路径（默认使用内置 UTF-8 配置）")
    return parser.parse_args(args)


def main(args=None) -> None:
    """主入口函数

    读取语料文件，运行 Nagao 新词发现算法，将结果输出为 CSV 文件。
    输出格式：词,词频,左邻,右邻,PMI,均衡值,成词概率

    Args:
        args: 命令行参数列表，为 None 时自动从 sys.argv 解析
    """
    parsed = parse_args(args)

    # 加载配置：指定了配置文件则使用，否则使用默认 UTF-8 配置
    if parsed.config_file is not None:
        config = NewwordConfig.from_file(parsed.config_file)
    else:
        config = NewwordConfig.default()

    # 运行算法
    newword = Newword(config)
    with open(parsed.output_file, "w", encoding=config.filecode) as f:
        for word, freq, left_variety, right_variety, pmi, eta, threshold in newword.process(parsed.input_file):
            f.write(f"{word},{freq},{left_variety},{right_variety},{pmi},{eta},{threshold}\n")


if __name__ == "__main__":
    main()
