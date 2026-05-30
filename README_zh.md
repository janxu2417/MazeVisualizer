# MazeVisualizer

## 项目背景 (Project Background)

MazeVisualizer 用于展示迷宫生成与寻路过程的 step-by-step 可视化。
目标是把课程里的数据结构与算法知识落到一个小型交互工具中。

## 主要特性 (Key Features)

- 迷宫生成：DFS、Prim、Kruskal
- 迷宫类型：长廊型(DFS)、死胡同型(Prim)、Prim Dense、Kruskal Sparse
- 寻路可视化：BFS、Dijkstra、A*、Bi-BFS、Greedy、Weighted A*
- 启动菜单包含 Help
- 菜单可选迷宫大小、复杂度、迷宫种类与算法
- 支持暂停、重启求解器、切换算法、新迷宫

## 核心算法 (Core Algorithms)

### 迷宫生成 (DFS Backtracking)

- 网格中 0 表示墙，1 表示路
- 行列数会自动调整为奇数，便于“跳墙挖通”，保持墙/路结构规整
- Loop chance 会随机打通部分墙，形成更多回路

### 寻路 (Pathfinding)

- **BFS**：无权图最短路径
- **Dijkstra**：加权最短路基线（此处权重一致）
- **A***：使用 Manhattan 距离启发式
- **Bi-BFS**：起点与终点双向扩展
- **Greedy Best-First**：只用启发式，速度快但非最短
- **Weighted A***：$f(n)=g(n)+W\times h(n)$，速度与最优性权衡

## 操作说明 (Controls)

- Space：暂停/继续
- H：Help 面板（会暂停）
- N：单步执行（暂停时，按住可连续）
- +/-：加速/减速
- [ / ]：调整 Weighted A* 的 W
- R：同一迷宫上重启算法
- 1/2/3：切换 BFS/Dijkstra/A*
- 4/5/6：切换 Bi-BFS/Greedy/Weighted A*
- M：生成新迷宫
- ESC：返回菜单/关闭帮助面板

## 运行方式 (Run)

1. 安装依赖：
   - `python -m pip install -r requirements.txt`
2. 启动程序：
   - `python src/main.py`
   - 或 `python src/ui.py`

## 工程说明 (Engineering Notes)

- 逻辑/UI 分离：算法在 `src/algorithms.py`，渲染和输入在 `src/ui.py`
- 求解器使用 generator，UI 每帧消费一步用于动画

## 文档与截图 (Docs and Screenshots)

将截图或 GIF 放入 `docs/` 并在报告中引用。

![MazeVisualizer screenshot](docs/screenshot.png)

## AI 工具说明 (AI Tool Declaration)

AI 辅助情况：使用 GitHub Copilot 生成 UI 框架与 README 草稿，
核心算法由本人复核并做了调整。
