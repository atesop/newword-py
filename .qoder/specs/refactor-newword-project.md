# Nagao 新词发现项目重构计划

## Context

项目 `newword-py` 是一个基于 Nagao 算法的 Python 新词发现工具，核心代码集中在单个 `newword.py`（215行）中。项目缺少标准开源项目结构、单元测试、完善的注释和类型提示。本次重构目标是在**不改变核心算法逻辑**的前提下，将其改造为结构规范的开源项目。

## 目标目录结构

```
newword-py/
├── pyproject.toml                  # 项目元数据和构建配置
├── README.md                       # 项目说明（重写）
├── LICENSE                         # MIT License
├── .gitignore                      # Git 忽略规则
│
├── newword/                        # 核心包
│   ├── __init__.py                 # 包入口，导出核心 API
│   ├── algorithm.py                # Nagao 核心算法类
│   ├── config.py                   # 配置加载与参数模型
│   ├── corpus.py                   # 语料读取与文本分割
│   ├── stats.py                    # 统计工具函数
│   ├── cli.py                      # 命令行入口
│   └── data/                       # 内置数据文件
│       ├── newword.utf8.conf
│       ├── newword.gbk.conf
│       ├── punct.utf8.dat
│       └── punct.gbk.dat
│
├── tests/                          # 测试目录
│   ├── __init__.py
│   ├── conftest.py                 # 公共 fixtures
│   ├── fixtures/                   # 测试数据
│   │   ├── sample_corpus.txt
│   │   ├── test.conf
│   │   └── test_punct.dat
│   ├── test_stats.py               # 纯函数单元测试
│   ├── test_config.py              # 配置加载测试
│   ├── test_corpus.py              # 语料处理测试
│   ├── test_algorithm.py           # 核心算法测试
│   └── test_cli.py                 # CLI 集成测试
│
└── newword.py                      # 兼容入口（薄包装，转发到 newword.cli）
```

## 实施步骤

### Phase 1: 基础设施与分支创建

1. **创建重构分支** `refactor/standardize`
2. **创建 `pyproject.toml`** — 项目元数据、依赖声明、entry_point 注册
3. **创建 `.gitignore`** — Python 标准忽略规则
4. **创建 `LICENSE`** — MIT License
5. **创建 `newword/` 包目录** 和 `tests/` 目录
6. **生成回归测试 golden output** — 用原始代码对一份中文语料运行，保存输出作为基准

### Phase 2: 模块拆分

#### 2.1 `newword/stats.py` — 统计工具函数
从 `newword.py` 迁移并重构：
- `lenOfSamePrefix` → `common_prefix_length(str1, str2) -> int`
- `eta_mean(a, b) -> float` — 保持名称
- `thres_mean(f, r, l, p) -> float` — 保持名称
- `countWord` → `count_substrings(line, word_dict)` — 使用 `defaultdict(int)` 简化

添加：中文文档字符串、类型提示、行内注释

#### 2.2 `newword/config.py` — 配置加载
创建 `NewwordConfig` dataclass：
- 字段映射：`n_freq→min_freq`, `n_pmi→min_pmi`, `n_av→min_av`, `n_eta→min_eta`, `n_size→min_size`, `n_gram→max_gram`, `n_threshold→min_threshold`
- `from_file(path)` 类方法从 INI 文件加载
- `punct_set` 属性：加载标点集，自动添加空格和制表符
- **修复路径 bug**：标点文件相对路径解析为相对于配置文件所在目录；内置数据文件通过 `importlib.resources` 定位

#### 2.3 `newword/corpus.py` — 语料处理
从 `Newword` 类迁移：
- `splitLine` → `split_line(line, punct_set, filecode, alnum_dict=None, reverse=False) -> tuple[dict, dict]`
- `readCorpus` → `read_corpus(file_path, filecode, punct_set, reverse=False) -> tuple[dict, defaultdict]`
- 返回构建好的字典，消除隐式副作用
- 保留 `.encode(filecode).isalnum()` 字节级判断（添加注释说明与 `str.isalnum()` 的差异）
- 不迁移 `splitLine1` 死代码

#### 2.4 `newword/algorithm.py` — 核心算法
保留 `Newword` 类，做以下改进：

**statresults 魔法数字 → 命名键**：
- `1` → `"freq"` (词频)
- `2` → `"left_variety"` (左邻字种数)
- `3` → `"right_variety"` (右邻字种数)
- `4` → `"length"` (词长)

**参数重命名**：
- `modef` → `is_forward_pass`
- `nlr` (2/3) → `variety_side` (枚举 `VarietySide.LEFT`/`RIGHT`)
- `getWordFreq` → `_compute_variety`
- `yieldItem` → `filter_results`
- `processNagao` → `process`

**方法签名调整**：
- `__init__` 接收 `NewwordConfig` 对象，不再直接读文件；移除 print 副作用
- `_compute_variety` 和 `filter_results` 添加完整中文注释说明遍历逻辑
- `process` 流程不变：正向→反向两遍扫描

#### 2.5 `newword/cli.py` — 命令行入口
- 使用 `argparse` 替代 `sys.argv` 手动解析
- 正确处理配置文件路径（相对/绝对/默认）
- 输出格式保持 `词,词频,左邻,右邻,PMI,eta,threshold` 不变

#### 2.6 `newword/__init__.py`
导出 `Newword`, `NewwordConfig` 和统计工具函数

#### 2.7 根目录 `newword.py` 兼容入口
3-5行转发代码，保持 `python3 newword.py input output [conf]` 用法

### Phase 3: 单元测试

按依赖顺序编写，从底层到顶层：

1. **`test_stats.py`** — `common_prefix_length`, `eta_mean`, `thres_mean`, `count_substrings` 的边界和典型值测试
2. **`test_config.py`** — 配置文件加载、标点集验证、路径解析、异常处理
3. **`test_corpus.py`** — 文本分割、alnum 识别、反向读取、语料文件读取
4. **`test_algorithm.py`** — 用小语料验证完整流程，与 golden output 回归对比
5. **`test_cli.py`** — 参数解析、端到端集成测试

### Phase 4: 收尾

1. 更新 `README.md`
2. 移动数据文件到 `newword/data/`，删除根目录原文件
3. 运行完整回归测试，确认输出一致
4. 运行 `pytest` 全量测试通过

## 关键设计决策

| 决策 | 选项 | 理由 |
|------|------|------|
| statresults 键替换 | 命名字符串键 | 消除魔法数字，极大提升可读性；用回归测试保障正确性 |
| _compute_variety 保持副作用 | 修改 self.statresults | 算法核心聚合步骤，函数式改写增加内存开销不值得 |
| .encode().isalnum() 保留 | 字节级判断 | 中文字符在字符级 `str.isalnum()` 返回 True，必须用字节级判断 |
| splitLine1 移除 | 不迁移 | 死代码，从未被调用 |
| 配置参数名 | INI 文件保持原名，代码内部用语义名 | 配置文件是用户接口，改动会破坏兼容性 |

## 验证方案

1. **回归测试**：重构前用原始代码生成 golden output；重构后对相同语料运行，逐行对比输出
2. **单元测试**：`pytest tests/` 全部通过
3. **兼容性测试**：`python3 newword.py input output` 和 `python3 -m newword input output` 均可正常工作
4. **路径修复验证**：从非项目目录运行，确认能找到配置和数据文件

## 风险与应对

| 风险 | 应对 |
|------|------|
| statresults 键替换遗漏 | 全局搜索数字键访问点逐一替换 + 回归测试 |
| getWordFreq 遍历逻辑理解偏差 | 该方法只做变量重命名和注释，不改结构 |
| 浮点精度差异 | 回归对比时考虑浮点误差容忍 |
| 配置路径解析变更 | 单元测试覆盖各种路径场景 |
