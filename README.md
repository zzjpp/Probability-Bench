# Probability-Bench

基于谢践生《概率论引论》（**2024 年 9 月校稿版**）重要习题整理的中文概率论解题与证明 benchmark。

**81 道独立题目，全部内嵌完整参考解答，L1–L8 分层，5 种能力标签，逐题 4 分评分细则。** 这是核心选题集，包含 84 处原书题号（3 处重复题合并），另保留全书 451 道编号习题的定位索引。没有把未整理习题计入评测题数。

题库适用于本科概率论及部分荣誉课程内容，涵盖组合计数、概率空间、可测性与积分、独立性、期望、条件期望、连续分布、随机收敛、浓度不等式、特征函数、熵、矩问题及 Brown 桥。第一章主要为引导性讨论，本核心集从第二章开始选题。

## 数据与解答

| 文件 | 用途 |
|---|---|
| [data/items.jsonl](data/items.jsonl) | 唯一主数据；每行一道题，包含 `reference_solution`、`final_answer` 和 `scoring_rubric` |
| [schema/item.schema.json](schema/item.schema.json) | 统一 JSON Schema |
| [data/inputs/](data/inputs/) | 求解器输入：仅 `id`、`question`、`question_latex`、`assets` |
| [data/splits/](data/splits/) | 保留参考解答的评分端切分 |
| [data/questions.tex](data/questions.tex) | 标准化 LaTeX 题面源文件，未声称已编译 PDF |
| [docs/catalog.md](docs/catalog.md) | 81 道题的原书题号、页码、难度、主题与切分 |
| [sources/manifest.json](sources/manifest.json) | 版本、PDF 校验值、网页参考范围 |
| [sources/exercise_index.jsonl](sources/exercise_index.jsonl) | 451 道原书编号习题的元数据索引，不含全书正文 |
| [data/summary.json](data/summary.json) | 规模和覆盖统计 |

81 道题均有逐题数学核查记录，明确题面假设、关键推导与退化情形；该记录是模型辅助复核，不是独立专家审定。所有参考解答都在 JSON 内；没有仅链接到网页或缺少解答的正式评测项。重复题 5.15/9.2、B.2/11.35、B.5/11.38 各只计一道。相近方法题按 `family_id` 整组切分，当前 dev/validation/test 分别为 **14/12/55** 题。

本项目独立重写题面和解答，逐题记录标准化所补充的假设。知乎专栏中选中的 **10 道第七章题**已比较数学论证；其他题为项目自行推导并进行模型辅助核查。B站链接是 **25 秒预览**，只核实元数据及示例画面，未据此声称获得完整答案。详见 [数据说明](docs/dataset_card.md)。

## 难度与能力

| 难度 | 结构含义 | 题数 |
|---|---|---:|
| L1 | 定义或一步直接应用 | 4 |
| L2 | 明确的常规方法 | 12 |
| L3 | 多步标准应用 | 22 |
| L4 | 综合推理、条件与边界控制 | 16 |
| L5 | 关键技巧或辅助构造 | 10 |
| L6 | 深入证明、多段论证 | 13 |
| L7 | 复杂构造或跨方法综合 | 3 |
| L8 | 高阶挑战与非直接构造 | 1 |

难度已按**方法发现、论证深度、技术控制三个结构维度逐题复核**，尚未经模型或学生作答率校准，不能与 CMC-Bench 的同名等级直接比较。每题记录 `difficulty_profile`、`difficulty_rationale`、`prerequisites`；等级为 1 加三轴分值之和，逐题校核见 [docs/review.md](docs/review.md)。L8 仅 1 题，不能单独据此得出稳健能力结论；不为了平衡数量而抬高难度。校准方案见 [docs/difficulty.md](docs/difficulty.md)。

能力维度为 Mathematical Knowledge、Mathematical Computation、Mathematical Reasoning、Mathematical Proof、Mathematical Generalization。标签落实到评分点；“Generalization”表示方法迁移代理，不能代替独立的迁移实验。

## 本地验证

Python **3.10+**，核心工具与测试只使用标准库：

```bash
python tools/validate.py
python -m unittest discover -s tests -v
python tools/export.py
```

23 项测试包含本机 HTTP 模拟服务，无外部模型调用。受限环境需要允许本机回环连接。有限数学情形核查不等同于对全部证明的形式化认证。

## 评测

先准备无答案请求（不发起推理）：

```bash
python tools/prepare_run.py --split test --model YOUR_SOLVER --output runs/requests.jsonl
```

若使用兼容 Chat Completions 的服务，将密钥通过环境变量 `PROB_API_KEY` 提供，并替换下列端点和模型名。**下面的 solver/judge 命令会调用服务并可能产生费用；仓库本身没有预置密钥，也没有已运行的模型成绩。**

```bash
python tools/run_solver.py --inputs data/inputs/test.jsonl --output-dir runs/solver --endpoint https://YOUR_PROVIDER/v1/chat/completions --model YOUR_SOLVER
python tools/auto_evaluate.py prepare runs/solver/responses.jsonl --split test --output runs/plan.json
python tools/auto_evaluate.py judge runs/plan.json --output-dir runs/judge --endpoint https://YOUR_PROVIDER/v1/chat/completions --model YOUR_JUDGE --second-model YOUR_SECOND_JUDGE
python tools/auto_evaluate.py report runs/plan.json runs/judge/judgments.jsonl --output runs/report.json
```

求解器只应获得 `data/inputs/` 和执行所需程序；封闭评测时不挂载完整仓库、解答、网页或原书。`id` 只是记录元数据，不发给文本模型。公开书籍存在训练污染风险，这些隔离措施不能证明模型从未见过题目。

每题 4 分；两次评分采用不同审查提示、互不读取对方结果，可指定不同模型。分歧、参考解答疑点、评分调用失败均进入 `needs_review`，汇总给出未决项上下界；缺失、空回答、求解失败保留在分母中并按 0 计。自动一致仍可能共同出错，因此自动成绩为暂定结果。正式人工复核可使用 `tools/evaluate.py`，要求每题两名人工审阅者完成裁决。详细格式见 [评测协议](docs/evaluation.md)。

打包：

```bash
python tools/package.py --output dist/Probability-Bench.zip
```

代码包只收录明确允许的源码、题库和文档，排除密钥、运行日志、浏览器副本、原始 PDF、缓存和 Git 历史。代码许可与题库来源权利分开，见 [LICENSE](LICENSE) 与 [DATA_RIGHTS.md](DATA_RIGHTS.md)。
