# MazeVisualizer

[English README](README.md)

## 项目背景

MazeVisualizer 是一个基于 Python + Pygame 的迷宫生成与路径搜索可视化项目。
它面向《数据结构与算法》课程大作业，重点展示：

- 迷宫生成与图搜索算法的自主实现
- 算法逻辑与界面渲染的分离
- 多种搜索算法的过程对比
- 算法行为的可解释性，而不是单纯调用外部库

## 主要功能

- 迷宫生成：DFS 回溯、Prim、Kruskal
- 路径搜索：BFS、Dijkstra、A*、双向 BFS、Greedy、Weighted A*
- frontier / open set 可视化
- 双向 BFS 双侧扩展可视化
- 加权地形模式，用于展示带权最短路
- 运行统计信息：路径长度、访问节点数、搜索步数、路径总代价、最优性
- 同一迷宫上的算法对比面板

## 项目结构

```text
MazeVisualizer/
├── src/
│   ├── algorithms.py
│   ├── app.py
│   ├── config.py
│   ├── menu.py
│   ├── render.py
│   ├── main.py
│   └── ui.py
├── docs/
├── tests/
│   ├── test_algorithms.py
│   ├── test_algorithm_states.py
│   ├── test_app_logic.py
│   └── test_render_smoke.py
├── pytest.ini
├── README.md
├── README_zh.md
├── LICENSE
└── requirements.txt
```

## 核心算法说明

### 一、迷宫生成

#### 1. DFS 回溯生成

- 网格中 `0` 表示墙，`1` 表示路
- 搜索时每次跨两格移动，从而保留中间墙层
- 使用栈记录当前挖路路径
- 如果当前格四周没有未访问可扩展点，就回溯

这种方法生成的迷宫通常走廊较长、通路感明显。

#### 2. Prim 风格迷宫生成

- 将候选单元视为图中的节点
- 维护当前已连通区域边界上的 frontier
- 每次随机取一个 frontier 点，把它连到现有生成树中

这种方式通常会形成更多分支和死胡同。

#### 3. Kruskal 风格迷宫生成

- 将奇数坐标格点视为图顶点
- 将可打通的墙视为候选边
- 使用并查集判断两个区域是否已经连通

这本质上对应最小生成树思想，是并查集的直接应用。

### 二、路径搜索

| 算法 | 基本思想 | 是否最优 | 时间复杂度 | 空间复杂度 | 说明 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| BFS | 分层扩展 | 在无权图中最优 | `O(V+E)` | `O(V)` | 求最少步数 |
| Dijkstra | 按累计代价贪心扩展 | 是 | `O((V+E)logV)` | `O(V)` | 适合带权最短路 |
| A* | Dijkstra + 启发函数 | 启发函数可采纳时最优 | 通常优于 Dijkstra | `O(V)` | 本项目用 Manhattan 距离 |
| 双向 BFS | 从起点和终点同时扩展 | 在无权图中最优 | 实际中常更快 | `O(V)` | 可视化效果明显 |
| Greedy | 只看启发函数 | 否 | 通常较快 | `O(V)` | 可能走次优路径 |
| Weighted A* | `f(n)=g(n)+W*h(n)` | 不一定最优 | 通常比 A* 更快 | `O(V)` | 用速度换最优性 |

### 三、为什么加入加权地形

如果所有通路代价都相同，那么 BFS、Dijkstra、A* 往往得到相同的最短路径长度，差异主要体现在搜索顺序。
为了更好地体现“无权最短路”和“带权最短路”的区别，项目加入了可选的加权地形模式：

- 普通地形代价 = 1
- 中等地形代价 = 3
- 高代价地形 = 5

在这一模式下：

- BFS 仍然只保证“步数最少”
- Dijkstra 保证“总代价最小”
- A* / Weighted A* 同时利用代价和启发信息

这样更能体现课程中最短路算法选型的意义。

## 可视化设计

每个求解器不再只返回简单路径，而是逐步产出统一状态帧。每一帧包括：

- 当前节点 `current`
- 已访问集合 `visited`
- frontier / open set
- 当前预览路径 `path`
- 当前统计信息 `stats`
- 双向 BFS 的起点侧 / 终点侧访问集合

因此 UI 只负责“展示状态”，不再在界面层自己推断算法过程。这种设计更清晰，也更便于测试。

## 操作说明

- `Space`：暂停 / 继续
- `H`：显示帮助面板
- `N`：暂停时单步执行
- `+/-`：调节速度
- `[` / `]`：调节 Weighted A* 的参数 `W`
- `1-6`：切换算法并在同一迷宫上重新运行
- `R`：重启当前算法
- `T`：切换加权地形模式
- `C`：清空对比面板
- `M`：生成新迷宫
- `ESC`：关闭帮助面板或返回菜单

## 运行方式

1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

2. 启动程序

```bash
python src/main.py
```

也可以运行：

```bash
python src/ui.py
```

## 测试

### 运行方式

在项目根目录下运行全部测试：

```bash
python -m pytest
```

由于仓库中已经加入 `pytest.ini`，测试发现规则已经固定为：

- 测试目录：`tests/`
- 测试文件：`test_*.py`

如果只想运行某一组测试：

```bash
python -m pytest tests/test_algorithms.py
python -m pytest tests/test_algorithm_states.py
python -m pytest tests/test_app_logic.py
python -m pytest tests/test_render_smoke.py
```

### 当前测试覆盖

目前自动化测试覆盖：

- 迷宫尺寸自动规范化
- DFS / Prim / Kruskal 生成迷宫的可达性
- BFS 路径正确性与最短性
- Dijkstra 与 BFS 在无权图上的结果一致性
- A* 与 BFS 在无权图上的结果一致性
- Greedy 与 Weighted A* 返回路径的合法性
- 加权地形下 Dijkstra 的总代价行为
- 非法输入的异常处理
- `StepState` / `RunStats` 统一状态接口检查
- 双向 BFS 的 `meet_point` 与双侧访问状态检查
- `app.py` 中的非 GUI 逻辑：选项切换、边界夹紧、地形权重生成、solver 创建、暂停 / Help 状态流转
- 基于 headless Pygame 的渲染 smoke tests，用于验证主要绘制路径不会崩溃

### 报告 / PDF 中可以这样写

为了说明测试设计，可以将本项目的自动化测试概括为三层：

1. **算法正确性测试**
   验证迷宫可达性、最短路性质、带权路径行为以及异常处理。
2. **状态与控制逻辑测试**
   验证配置切换、运行状态流转和 UI 所依赖的统一步态接口。
3. **渲染 smoke tests**
   使用 headless Pygame（`SDL_VIDEODRIVER=dummy`），验证主要界面绘制路径可以正常执行，不会在渲染时崩溃。

### 可直接写进报告的简短说明

> 本项目包含自动化测试，用于验证算法正确性、运行时状态流转以及可视化渲染的基本稳定性。  
> 目前全部测试均可在 Python 3.13 与 `pytest` 环境下通过，为迷宫生成、路径搜索、带权地形和核心可视化流程提供了可复现的正确性证据。

## 工程说明

- `algorithms.py`：核心算法与统一状态输出
- `app.py`：程序状态流转与 solver 驱动
- `render.py`：绘图、HUD、帮助面板、对比面板
- `menu.py`：菜单按钮布局与点击分发
- `config.py`：配置项与颜色常量

这种结构满足 GUI 项目“逻辑与界面分离”的课程要求。

## 文档与截图

建议在 `docs/` 中保留截图或 GIF，并在 PDF 报告中展示。

![MazeVisualizer screenshot](docs/screenshot.png)

建议报告中至少给出三类截图：

1. 主菜单
2. 算法运行中画面（能看出 frontier / visited / path）
3. 求解结束后的统计与对比面板

## AI 工具声明

AI 辅助情况：

- 使用 GitHub Copilot 和 Codex 协助搭建 UI 结构、重构模块、润色文档
- 迷宫生成与路径搜索核心逻辑由作者人工复核并调整
- 最终的算法说明、测试设计和课程作业表达由作者整理完成
