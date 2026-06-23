# MazeVisualizer

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-2E8B57?style=for-the-badge)](https://www.pygame.org/)
[![Pytest](https://img.shields.io/badge/Tests-78%20passed-0A7D38?style=for-the-badge)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://github.com/janxu2417/MazeVisualizer/blob/main/LICENSE)

<div align="center">
  <h3>迷宫生成与路径搜索可视化项目</h3>
  <p>基于 Python 和 Pygame 的《数据结构与算法》课程项目。</p>
  <p>
    <a href="https://github.com/janxu2417/MazeVisualizer/blob/main/README.md"><strong>English README</strong></a>
    ·
    <a href="https://github.com/janxu2417/MazeVisualizer">GitHub 仓库</a>
  </p>
</div>

## 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [项目截图](#项目截图)
- [主要功能](#主要功能)
- [项目结构](#项目结构)
- [核心算法](#核心算法)
- [综合复杂度对比](#综合复杂度对比)
- [运行指南](#运行指南)
- [操作说明](#操作说明)
- [测试](#测试)
- [开发路线](#开发路线)
- [参考与说明](#参考与说明)
- [AI 工具声明](#ai-工具声明)
- [联系方式](#联系方式)
- [许可证](#许可证)
- [致谢](#致谢)

## 项目简介

MazeVisualizer 是一个基于 Python + Pygame 的迷宫生成与路径搜索可视化项目，用于展示算法运行过程，而不仅是最终答案。项目面向《数据结构与算法》课程作业，重点在于：

- 自主实现迷宫生成与图搜索逻辑
- 把算法过程显式可视化
- 比较无权最短路与带权最短路算法的差异
- 将算法逻辑、状态管理与渲染模块清晰分离

当前版本不仅是一个演示程序，而是一个可交互的算法实验平台。用户可以生成迷宫、切换算法、编辑地图、绘制地形权重、检查单元格、比较多次运行结果，并导出统计信息。

## 技术栈

- [Python 3.13](https://www.python.org/)
- [Pygame 2.5+](https://www.pygame.org/)
- [Pytest](https://docs.pytest.org/)

## 项目截图

### 主菜单

![MazeVisualizer 主菜单](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/menu.png)

### BFS 运行中

![MazeVisualizer BFS 运行中|215](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_searching_BFS.png)

### 双向 BFS 运行中

![MazeVisualizer 双向 BFS|236](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_searching_Bi-BFS.png)

### 结束界面与对比面板

![MazeVisualizer 最终结果|199](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_finished%26comparison.png)

### 编辑模式

![MazeVisualizer 编辑模式](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/edit_maze_inspect.png)

## 主要功能

- 支持 DFS 回溯、Prim 风格、Kruskal 风格三种迷宫生成算法
- 支持 BFS、Dijkstra、A*、Bi-BFS、Greedy Best-First、Weighted A* 六种路径搜索算法
- 通过统一的 `StepState` 状态帧接口实现逐步可视化
- 支持 `x1`、`x3`、`x5` 三档加权地形
- 支持显示路径长度、访问结点数、步数、总代价和运行状态
- 支持同一迷宫下的多算法 comparison board
- 支持交互式编辑模式：画墙、设起点、设终点、绘制地形、检查单元格、撤销
- 支持迷宫历史浏览
- 支持画布缩放与平移
- 支持导出对比 JSON 与导入文本迷宫
- 支持 `dark`、`ocean`、`forest`、`sunset` 四套主题

## 项目结构

```text
MazeVisualizer/
├─ src/
│  ├─ step_data.py       # Grid / Point / CostMap / RunStats / StepState
│  ├─ maze_gen.py        # DFS / Prim / Kruskal 迷宫生成
│  ├─ pathfinding.py     # 6 种路径搜索算法
│  ├─ algorithms.py      # 兼容导出层
│  ├─ app.py             # FSM、事件分发、solver 驱动、历史、导入导出
│  ├─ render.py          # HUD、帮助面板、图例、对比面板、编辑/运行绘制
│  ├─ edit.py            # 编辑状态机与撤销
│  ├─ menu.py            # 菜单布局与点击分发
│  ├─ config.py          # 运行配置、预设、帮助文本
│  ├─ theme.py           # 主题系统
│  ├─ main.py            # 主入口
│  └─ ui.py              # 备用入口
├─ docs/                 # 截图
├─ tests/                # 自动化测试
├─ README.md
├─ README_zh.md
├─ LICENSE
├─ pytest.ini
└─ requirements.txt
```

## 核心算法

### 迷宫生成

#### DFS 回溯生成

- 使用显式栈维护当前挖路路径
- 每次跨两格移动，以保留墙层
- 当没有未访问邻居时执行回溯

对应课程知识点：

- 深度优先搜索
- 栈
- 回溯

#### Prim 风格生成

- 维护已连通区域外侧 frontier
- 每次随机选择 frontier 单元并接入已生成区域
- 适合展示 frontier 扩张思路

对应课程知识点：

- 最小生成树思想
- frontier 扩张

#### Kruskal 风格生成

- 将可通行单元视为顶点、可打通墙视为候选边
- 用并查集判断两区域是否已经连通
- 在避免成环的前提下构造生成树结构

对应课程知识点：

- 并查集
- 路径压缩
- 按秩合并
- 最小生成树

### 路径搜索

| 算法                | 核心思想                           | 最优性(总代价最小) | 说明                |
| :---------------- | :----------------------------- | :--------- | :---------------- |
| BFS               | 用 FIFO 队列分层扩展                  | 无权图最优      | 最小步数              |
| Dijkstra          | 按累计代价贪心扩展                      | 非负权图最优     | 适合带权地形            |
| A*                | 在 Dijkstra 基础上加入 Manhattan 启发式 | 启发式可采纳时最优  | 通常比 Dijkstra 扩展更少 |
| Bi-BFS            | 从起点和终点同时做 BFS                  | 无权图最优      | 适合展示双向搜索          |
| Greedy Best-First | 仅按启发式扩展                        | 不保证最优      | 通常更快，但可能次优        |
| Weighted A*       | `f(n)=g(n)+W*h(n)`             | 一般不保证最优    | 速度与路径质量折中         |

### 课程知识点覆盖

| 课程知识点    | 应用位置                               | 实现细节                     |
| :------- | :--------------------------------- | :----------------------- |
| DFS / 回溯 | DFS 迷宫生成                           | 显式栈、死路回溯                 |
| BFS      | BFS、双向 BFS                         | `collections.deque` 分层扩展 |
| 图表示      | 全部求解器                              | 隐式网格图，四邻接关系              |
| 优先队列 / 堆 | Dijkstra、`A*`、Greedy、`Weighted A*` | `heapq`                  |
| 最短路径     | Dijkstra                           | 非负权图边松弛                  |
| 启发式搜索    | `A*`、Greedy、`Weighted A*`          | Manhattan 距离             |
| 双向搜索     | Bi-BFS                             | 双前沿推进与交汇点合并              |
| 并查集      | Kruskal 迷宫生成                       | 路径压缩与按秩合并                |
| 最小生成树    | Prim / Kruskal 迷宫生成                | frontier 扩张 / 连通性维护      |
| 关注点分离    | 全项目结构                              | 算法、状态和渲染分模块实现            |

## 综合复杂度对比

记 `V` 为可通行单元数，`E` 为可通行单元之间的邻接边数，`b` 为分支因子，`d` 为最短路径深度。对四邻域网格迷宫，结点度有上界，因此 `E = O(V)`。

| 算法                | 平均 / 典型表现                  | 最坏情况                | 空间复杂度  | 最优性 | 条件 / 说明                |
| :---------------- | :------------------------- | :------------------ | :----- | :-- | :--------------------- |
| DFS 迷宫生成          | `Theta(V)`                 | `Theta(V)`          | `O(V)` | 不适用 | 每个可达单元只会被常数次处理         |
| Prim 迷宫生成         | `Theta(V)`                 | `Theta(V)`          | `O(V)` | 不适用 | 有界度网格下 frontier 处理保持线性 |
| Kruskal 迷宫生成      | `Theta(V alpha(V))`        | `Theta(V alpha(V))` | `O(V)` | 不适用 | 并查集采用路径压缩与按秩合并         |
| BFS               | `Theta(V + E)`             | `O(V + E)`          | `O(V)` | 是   | 适用于无权或等权图              |
| Dijkstra          | 常接近 `Theta((V + E) log V)` | `O((V + E) log V)`  | `O(V)` | 是   | 要求边权非负                 |
| A*                | 与启发式质量强相关，通常优于 Dijkstra    | `O((V + E) log V)`  | `O(V)` | 是   | 要求启发式有效                |
| 双向 BFS            | 在树状搜索空间中常写作 `O(b^(d/2))`   | `O(V + E)`          | `O(V)` | 是   | 适用于无权或等权图              |
| Greedy Best-First | 常较快，但输入依赖强                 | `O((V + E) log V)`  | `O(V)` | 否   | 仅依赖启发式                 |
| Weighted A*       | 通常比 A* 扩展更少                | `O((V + E) log V)`  | `O(V)` | 否   | `W > 1` 时牺牲严格最优性       |

如果只考虑有界度网格迷宫，可简化为：

- BFS：`O(V)`
- Dijkstra：`O(V log V)`
- A*：`O(V log V)`
- 双向 BFS：`O(V)`
- Greedy Best-First：`O(V log V)`
- Weighted A*：`O(V log V)`

### 为什么要加入加权地形

在均匀网格上，BFS、Dijkstra 和 A* 往往会得到相同路径长度，差别主要体现在搜索顺序上。加入加权地形后：

- `x1`：普通道路
- `x3`：中等代价地形
- `x5`：高代价地形

此时：

- BFS 仍只保证步数最少
- Dijkstra 保证总代价最小
- A* 同时利用代价和启发式
- Weighted A* 用更激进的启发式换取更少扩展

这样更能体现课程中不同最短路算法的适用场景差异。

## 运行指南

### 环境要求

- Python 3.13
- `pip`

### 安装

1. 克隆仓库：

```bash
git clone https://github.com/janxu2417/MazeVisualizer.git
cd MazeVisualizer
```

2. 安装依赖：

```bash
python -m pip install -r requirements.txt
```

### 启动

主入口：

```bash
python src/main.py
```

备用入口：

```bash
python src/ui.py
```

## 操作说明

- `Space`：暂停 / 继续
- `H`：显示帮助面板
- `N`：暂停时单步执行
- `+/-`：调整速度
- `[` / `]`：调整 Weighted A* 的 `W`
- `1-6`：切换算法并在当前迷宫上重新运行
- `R`：重启当前求解器
- `T`：切换加权地形
- `C`：显示 / 隐藏 comparison board
- `E`：从运行界面进入编辑模式
- `U`：切换主题
- `M`：生成新迷宫并保存当前迷宫到历史
- `Left / Right`：浏览迷宫历史
- `F5`：导出 `comparison_export.json`
- `F6`：从 `maze_import.txt` 导入迷宫
- `Mouse wheel`：缩放画布
- `Right mouse drag`：平移画布
- `ESC`：关闭帮助面板或返回菜单

### 编辑模式快捷键

- `D`：绘制墙 / 路
- `S`：设置起点
- `G`：设置终点
- `T`：绘制地形
- `I`：检查单元格
- `Ctrl+Z`：撤销
- `R`：在当前编辑结果上运行算法

## 测试

### 当前状态

当前测试总数为 78 项：

- `tests/test_algorithm_states.py`：25
- `tests/test_algorithms.py`：11
- `tests/test_app_logic.py`：26
- `tests/test_render_smoke.py`：16

实测命令：

```bash
python -m pytest --basetemp .pytest_tmp_report
```

实测结果：

```text
78 passed in 46.15s
```

### 测试覆盖内容

- 迷宫尺寸规范化与非法尺寸处理
- DFS / Prim / Kruskal 生成迷宫的可解性
- BFS 最短路径正确性
- Dijkstra 与 A* 在均匀网格上与 BFS 的一致性
- Greedy 与 Weighted A* 的路径合法性
- 加权地形行为
- `StepState` 与 `RunStats` 接口一致性
- 双向 BFS 的交汇点与双前沿状态
- app 层非 GUI 逻辑：历史、编辑刷新、导入导出、切换、solver 创建
- headless Pygame 下的菜单、HUD、运行界面、帮助面板、缩放平移渲染

### 测试运行说明

当前环境如果直接使用系统默认临时目录，`tmp_path` 相关测试可能因权限受限而失败。使用项目内 `--basetemp` 后，全套测试可以通过。

## 开发路线

- [x] 实现核心迷宫生成与路径搜索算法
- [x] 增加加权地形与 comparison board
- [x] 增加交互式编辑模式
- [x] 增加多主题与紧凑 HUD 布局
- [x] 增加缩放和平移
- [x] 将代码拆分为职责清晰的模块
- [ ] 增加 GIF 录制
- [ ] 增加更多挑战迷宫

## 参考与说明

README 模板参考：

- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

项目参考资料：

- [Pygame documentation](https://www.pygame.org/docs/)

本项目的核心算法逻辑与系统组织由作者自主实现与整理，未使用第三方算法库作为黑盒求解器。

## AI 工具声明

AI 工具主要用于以下辅助工作：

- 提供部分 UI 结构与组织建议
- 提供模块重构建议
- 润色 README 和项目报告文字

迷宫生成逻辑、路径搜索逻辑、状态接口设计和最终项目组织均由作者人工核对并定稿。

## 联系方式

- 作者：徐前
- 仓库地址：[janxu2417/MazeVisualizer](https://github.com/janxu2417/MazeVisualizer)

## 许可证

本项目基于 MIT License 发布。详见 `LICENSE`。

## 致谢

- 数据结构与算法课程： [GMyhf/2026spring-cs201](https://github.com/GMyhf/2026spring-cs201)
- Pygame 官方文档与社区示例
- Best-README-Template 提供的文档结构思路
