# MazeVisualizer

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-2E8B57?style=for-the-badge)](https://www.pygame.org/)
[![Pytest](https://img.shields.io/badge/Tests-71%2B%20passing-0A7D38?style=for-the-badge)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[English README](README.md)

> 仓库地址：[https://github.com/janxu2417/MazeVisualizer](https://github.com/janxu2417/MazeVisualizer)

<details>
  <summary>目录</summary>
  <ol>
    <li><a href="#项目背景">项目背景</a></li>
    <li><a href="#主要功能">主要功能</a></li>
    <li><a href="#项目结构">项目结构</a></li>
    <li><a href="#技术栈">技术栈</a></li>
    <li><a href="#核心算法说明">核心算法说明</a></li>
    <li><a href="#交互式编辑">交互式编辑</a></li>
    <li><a href="#快捷键">快捷键</a></li>
    <li><a href="#快速开始">快速开始</a></li>
    <li><a href="#测试">测试</a></li>
    <li><a href="#路线图">路线图</a></li>
    <li><a href="#许可证">许可证</a></li>
    <li><a href="#致谢">致谢</a></li>
    <li><a href="#ai-工具声明">AI 工具声明</a></li>
  </ol>
</details>

<a id="项目背景"></a>
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

```
MazeVisualizer/
├── src/
│   ├── step_data.py       # 共享类型 (Grid, Point, CostMap, RunStats, StepState)
│   ├── maze_gen.py        # 迷宫生成 (DFS / Prim / Kruskal)
│   ├── pathfinding.py     # 6 种路径搜索器 + 共享辅助函数
│   ├── algorithms.py      # 再导出兼容层
│   ├── app.py             # FSM 事件循环, 状态管理, 编辑/运行逻辑
│   ├── render.py          # 所有绘图 (HUD, 图例, 菜单, 覆盖层, 对比面板)
│   ├── config.py          # AppConfig 数据类, 预设, 调色板, 帮助文本
│   ├── theme.py           # 4 套颜色主题 (dark / ocean / forest / sunset)
│   ├── menu.py            # 菜单按钮构建 + 点击分发
│   ├── edit.py            # 迷宫编辑器状态机 + 撤销栈
│   ├── main.py            # 入口
│   └── ui.py              # 备选入口
├── docs/                  # 截图
├── tests/
│   ├── conftest.py        # 共享 sys.path 配置
│   ├── test_algorithms.py # 算法正确性
│   ├── test_algorithm_states.py  # StepState 接口 + 双向 BFS 统计
│   ├── test_app_logic.py  # FSM 逻辑, 导入/导出, 历史导航
│   └── test_render_smoke.py     # 无头渲染冒烟测试
├── pytest.ini
├── README.md
├── README_zh.md
├── LICENSE
└── requirements.txt
```

### 数据流

```
用户输入 (鼠标 / 键盘)
        │
        ▼
  run_app()  ◄──  FSM: menu → algo → edit → run
        │
        ├── _dispatch_menu_event()
        ├── _dispatch_algo_event()
        ├── _dispatch_edit_event()
        └── _dispatch_run_event()
                │
                ▼
         _handle_keydown()  ──►  _reset_solver() / _reset_maze()
                │                       │
                ▼                       ▼
         _step_solver()  ◄──  SolverIterator (yield StepState)
                │
                ▼
         draw_run_view()
           ├── base_surface (静态网格 + 地形)
           ├── draw_overlay()  (已访问 / 前沿 / 路径 / 标记)
           └── draw_hud()
                 ├── 状态, 统计, 进度条
                 ├── draw_legend()
                 └── draw_comparison_board()
```

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="技术栈"></a>
## 技术栈

- Python 3.13
- Pygame 2.5+
- Pytest 8+
- Python 标准库：`deque`、`heapq`、`dataclasses`、自实现并查集

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="核心算法说明"></a>
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

### 课程知识点覆盖

本项目与课程《数据结构与算法》以下知识点直接对应：

| 课程知识点 | 应用位置 | 实现细节 |
| :-- | :-- | :-- |
| **DFS / 回溯** | DFS 迷宫生成 | 显式栈、每次跨两格挖路、无路可走时回溯 |
| **BFS / FIFO 队列** | BFS 求解、双向 BFS | `collections.deque`、逐层扩展 |
| **图的表示** | 所有求解器 | 隐式网格图 → 四方向邻接，无需显式边列表 |
| **优先队列 / 二叉堆** | Dijkstra、A*、Greedy、Weighted A* | `heapq`、元组 `(priority, ...)` 作堆元素 |
| **最短路（贪心范式）** | Dijkstra | 边松弛、非负权图最优性 |
| **启发式搜索 / 知情搜索** | A*、Greedy、Weighted A* | Manhattan 距离 `|dr|+|dc|`、可采纳且一致 |
| **双向搜索** | Bi-BFS | 两路 BFS 同时推进、交汇点检测与路径合并 |
| **并查集 / Union-Find** | Kruskal 迷宫生成 | 路径压缩 + 按秩合并，均摊近 O(1) |
| **最小生成树** | Prim、Kruskal 迷宫生成 | 边界扩张（Prim）、随机边处理（Kruskal） |
| **算法正确性与测试** | 完整测试套件 | 60 条自动化测试，覆盖最优性、边界情况、状态接口 |
| **关注点分离** | `src/` 模块划分 | `algorithms.py`（逻辑）与 `render.py`（界面）通过统一 `StepState` 帧解耦 |
| **复杂度分析** | 所有算法 | 时间复杂度与空间复杂度标注于 docstring 和 README 表格 |

### 综合复杂度对比

| 算法 | 最优情况 | 平均/期望 | 最坏情况 | 空间 | 最优性 | 启发式 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| DFS 迷宫 | Θ(V) | Θ(V) | Θ(V) | O(V) | — | — |
| Prim 迷宫 | Θ(V) | Θ(V) | Θ(V) | O(V) | — | — |
| Kruskal 迷宫 | Θ(V·α(V)) | Θ(V·α(V)) | Θ(V·α(V)) | O(V) | — | — |
| BFS | Ω(1) | Θ(V+E) | O(V+E) | O(V) | 是（无权图） | 否 |
| Dijkstra | Ω(1) | Θ((V+E)logV) | O((V+E)logV) | O(V) | 是（非负权） | 否 |
| A* | Ω(1) | < Dijkstra | O((V+E)logV) | O(V) | 是（可采纳） | Manhattan |
| Bi-BFS | Ω(1) | O(b^(d/2)) | O(b^d) | O(V) | 是（无权图） | 否 |
| Greedy | Ω(1) | 通常很快 | O((V+E)logV) | O(V) | 否 | Manhattan |
| Weighted A* | Ω(1) | < A* | O((V+E)logV) | O(V) | ε-可采纳 | Manhattan |

*V = 可通过单元数量，E = 可通过单元间边数，b = 分支因子，d = 最短路深度，α = 反 Ackermann 函数。*

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

<a id="交互式编辑"></a>
## 交互式编辑

本项目支持手动构造迷宫来替代预设 demo。从主菜单点击 **Edit Maze** 进入编辑模式，按 `R` 即可在当前自定义迷宫上运行所选算法。

| 工具 | 快捷键 | 功能 |
| :-- | :-- | :-- |
| Draw Wall/Path | `D` | 点击或拖拽切换墙与通路 |
| Place Start | `S` | 设置自定义起点 |
| Place Goal | `G` | 设置自定义终点 |
| Paint Terrain | `T` | 对通路循环设置地形代价 `1 → 3 → 5` |
| Inspect Cell | `I` | 查看单元格坐标、类型、代价和搜索状态 |
| Undo | `Ctrl+Z` | 撤销最近一次编辑 |

这使项目从固定展示升级为实验平台，用户可以主动构造边界情况。

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="快捷键"></a>
## 操作说明

- `Space`：暂停 / 继续
- `H`：显示帮助面板
- `N`：暂停时单步执行
- `+/-`：调节速度
- `[` / `]`：调节 Weighted A* 的参数 `W`
- `1-6`：切换算法并在同一迷宫上重新运行
- `R`：重启当前算法
- `T`：切换加权地形模式
- `C`：显示/隐藏对比面板
- `M`：生成新迷宫（保存当前迷宫到历史）
- `←` / `→`：浏览迷宫历史（对比板随地图切换）
- `F5`：导出对比结果 → `comparison_export.json`
- `F6`：导入迷宫 ← `maze_import.txt`
- `ESC`：关闭帮助面板或返回菜单
- `鼠标滚轮`：滚动帮助面板

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

### 自动化测试概括

为了说明测试设计，可以将本项目的自动化测试概括为三层：

1. **算法正确性测试**
   验证迷宫可达性、最短路性质、带权路径行为以及异常处理。
2. **状态与控制逻辑测试**
   验证配置切换、运行状态流转和 UI 所依赖的统一步态接口。
3. **渲染 smoke tests**
   使用 headless Pygame（`SDL_VIDEODRIVER=dummy`），验证主要界面绘制路径可以正常执行，不会在渲染时崩溃。

### 简短说明

> 本项目包含自动化测试，用于验证算法正确性、运行时状态流转以及可视化渲染的基本稳定性。  
> 目前全部测试均可在 Python 3.13 与 `pytest` 环境下通过，为迷宫生成、路径搜索、带权地形和核心可视化流程提供了可复现的正确性证据。

## 工程说明

- `algorithms.py`：核心算法与统一状态输出
- `app.py`：程序状态流转与 solver 驱动
- `render.py`：绘图、HUD、帮助面板、对比面板
- `menu.py`：菜单按钮布局与点击分发
- `config.py`：配置项与颜色常量

这种结构满足 GUI 项目“逻辑与界面分离”的课程要求。

<a id="路线图"></a>
## 路线图

- [x] 实现核心迷宫生成与路径搜索算法
- [x] 添加加权地形与算法对比面板
- [x] 添加交互式编辑模式
- [x] 添加多主题系统与响应式 HUD（含 compact 模式）
- [x] 添加画布缩放/平移功能
- [x] 拆分代码库为专注模块（step_data, maze_gen, pathfinding）
- [ ] 添加 GIF 录制功能
- [ ] 添加更多预设挑战迷宫

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="许可证"></a>
## 许可证

基于 MIT 许可证发布。详见 `LICENSE` 文件。

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="致谢"></a>
## 致谢

- 数据结构与算法课程大作业要求
- Pygame 文档与社区示例
- Best-README-Template 的 README 组织思路

<p align="right">(<a href="#mazevisualizer">返回顶部</a>)</p>

<a id="文档与截图"></a>
## 文档与截图

建议在 `docs/` 中保留截图或 GIF，并在 PDF 报告中展示。

![MazeVisualizer 菜单界面](docs/menu_v2.png)

![MazeVisualizer 搜索过程](docs/run_searching_v2.png)

![MazeVisualizer 搜索完成](docs/run_finished_v2.png)

建议报告中至少给出三类截图：

1. 主菜单
2. 算法运行中画面（能看出 frontier / visited / path）
3. 求解结束后的统计与对比面板

## AI 工具声明

AI 辅助情况：

- 使用 GitHub Copilot 和 Codex 协助搭建 UI 结构、重构模块、润色文档
- 迷宫生成与路径搜索核心逻辑由作者人工复核并调整
- 最终的算法说明、测试设计和课程作业表达由作者整理完成
