# newword-py

基于 Nagao 算法的新词发现与领域词典构建工具。

## 算法原理

对于候选词 x=(c₁c₂...cₙ)，判断成词的依据：

| 指标 | 参数 | 说明 |
|------|------|------|
| 词频 | `n_freq` | 候选词在语料中出现的次数 |
| 左右邻较小值 | `n_av` | min(l_av, r_av)，左右邻字种数的较小值 |
| 左右邻均衡值 | `n_eta` | 2·l_av·r_av/(l_av²+r_av²)，值越接近 1 越均衡 |
| 最小词长度 | `n_size` | 候选词的最短长度 |
| 最大 n-gram | `n_gram` | 统计的最大词长度 |
| 最小成词概率 | `n_threshold` | √n_freq / (1/l_av + 1/r_av) · min PMI |

## 安装

```bash
pip install .
```

开发模式安装（可编辑）：

```bash
pip install -e ".[dev]"
```

## 使用方法

### 命令行

```bash
# 安装后使用
newword input_file output_file [config_file]

# 模块方式运行
python3 -m newword input_file output_file [config_file]

# 兼容方式运行
python3 run_newword.py input_file output_file [config_file]
```

默认使用 UTF-8 编码配置。如果语料编码为 GBK，需指定对应的配置文件：

```bash
python3 -m newword input.txt output.csv newword.gbk.conf
```

### Python API

```python
from newword import Newword, NewwordConfig

# 使用默认配置
config = NewwordConfig.default()

# 或从配置文件加载
config = NewwordConfig.from_file("newword.utf8.conf")

# 运行算法
nw = Newword(config)
for word, freq, left, right, pmi, eta, threshold in nw.process("corpus.txt"):
    print(f"{word}: 词频={freq}, PMI={pmi:.4f}")
```

## 输出格式

输出为 CSV 文件，每行 7 列：

```
词,词频,左邻字种数,右邻字种数,最小PMI,均衡值,成词概率
```

## 配置文件

配置文件为 INI 格式，内置 UTF-8 和 GBK 两种配置：

```ini
[newword]
n_freq=10        # 最小词频阈值
n_pmi=0.000001   # 最小 PMI 阈值
n_av=5           # 最小邻字种数阈值
n_eta=0.6        # 最小均衡值阈值
n_size=2         # 最短词长度
n_gram=8         # 最大 n-gram 长度
n_threshold=0.01 # 最小成词概率阈值

[dictionary]
punct=punct.utf8.dat  # 标点符号文件

[default]
filecode=utf8  # 文件编码
```

## 项目结构

```
newword/
├── __init__.py     # 包入口，导出核心 API
├── __main__.py     # python -m 入口
├── algorithm.py    # Nagao 核心算法
├── config.py       # 配置加载
├── corpus.py       # 语料读取与文本分割
├── stats.py        # 统计工具函数
├── cli.py          # 命令行接口
└── data/           # 内置配置与数据文件
tests/              # 单元测试
```

## 注意事项

1. 标点符号文件中的字符作为分隔符，不会出现在候选词中。如需包含某个字符，从标点文件中删除即可。
2. 算法需要统计左邻和右邻信息，语料文件会被读取两次。在程序执行完毕前，不要对语料文件进行移动、修改或删除。
3. 本工具基于 Python dict 实现词频统计，读取语料与使用内存的占比约为 1:100。
4. 被标点分割后如果片段为数字字母组合（如 "CPU"、"3.5"），不参与成词统计，而是直接统计词频。

## 运行测试

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
