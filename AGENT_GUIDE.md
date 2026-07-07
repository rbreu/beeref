# BeeRef 项目结构指南（面向开发者 / Agent）

> 本文档用于帮助新加入的开发者或 AI Agent 快速理解 BeeRef 的代码结构、架构设计与开发约定。
> 阅读完本文即可定位代码、理解数据流，并安全地修改/扩展功能。

---

## 1. 项目概览

**BeeRef** 是一个极简的参考图查看器（Reference Image Viewer），用 Python + PyQt6 编写，
用途是让画师在创作时把参考图摆放在一个无限画布上，方便对照查看。

- 许可证：GPL-3.0
- 当前版本：`0.3.4-dev`（见 `beeref/constants.py` 的 `VERSION`）
- 入口脚本：`beeref.__main__:main`（由 `pyproject.toml` 的 `gui-scripts` 暴露为 `beeref` 命令）
- 原生文件格式：`.bee` 文件 = **SQLite 数据库**（图片以 sqlar 表存放，可直接用 `sqlite3 xxx.bee -Axv` 解包）

核心能力：移动/缩放/旋转/裁剪/翻转图像、批量归一化尺寸、批量排布
（最优/水平/垂直/方形）、文本便签、颜色采样、灰度、透明度、导出场景为图片/SVG、
窗口常驻置顶/无边框悬浮。

---

## 2. 技术栈

| 领域 | 选型 |
|------|------|
| 语言 | Python 3.9 – 3.12（`requires-python = ">=3.9,<3.13"`） |
| GUI 框架 | PyQt6（锁定 6.7.0） |
| 图形画布 | `QGraphicsScene` / `QGraphicsView` / `QGraphicsItem` |
| 撤销重做 | `QUndoStack` + `QUndoCommand` |
| 持久化 | `sqlite3`（原生 `.bee` 格式）+ sqlar 表存二进制图片 |
| 图片格式判定 | `exif`（EXIF 方向修正）、`lxml`（Pinterest 抓取） |
| 排布算法 | `rectangle-packer`（`rpack`，用于“最优排布”） |
| 打包 | PyInstaller（`BeeRef.spec`） |
| 测试 | pytest + coverage（flake8 做 lint） |

依赖详情见 `pyproject.toml` 与 `requirements/`（build / dev / test 三个文件）。

---

## 3. 目录结构

```
beeref/
├── __init__.py
├── __main__.py          # 程序入口：QApplication / MainWindow / main()
├── constants.py         # APPNAME、VERSION、配色 COLORS、版权等全局常量
├── logging.py           # 日志配置与日志文件路径
├── utils.py             # 通用工具：调色板、矩形、ActionList、颜色转换等
│
├── commands.py          # ★ 所有“撤销/重做命令”(QUndoCommand 子类)
├── scene.py             # ★ BeeGraphicsScene：画布、选中逻辑、排布算法、鼠标事件
├── view.py              # ★ BeeGraphicsView：视图、缩放/平移、所有菜单动作回调、文件读写入口
├── selection.py         # ★ 选中交互：BaseItemMixin / SelectableMixin / MultiSelectItem / RubberbandItem
├── items.py             # ★ 用户对象：BeePixmapItem(图) / BeeTextItem(文本) / BeeErrorItem(错误占位)
├── main_controls.py     # 右键菜单、拖放、无标题栏移动窗口的共享逻辑 (MainControlsMixin)
├── actions/             # 动作系统
│   ├── actions.py       # Action 类定义 + 全部 Action 清单 (actions 列表)
│   ├── mixin.py         # ActionsMixin：根据清单构建菜单/快捷键/启用分组
│   └── menu_structure.py# 菜单层级结构定义 menu_structure
├── config/              # 配置
│   ├── settings.py      # BeeSettings(QSettings)、BeeSettingsEvents、CommandlineArgs、最近文件
│   └── controls.py      # KeyboardSettings + 鼠标/滚轮动作配置（可自定义）
├── fileio/              # 文件读写
│   ├── __init__.py      # load_bee / save_bee / load_images / ThreadedIO（后台线程）
│   ├── sql.py           # SQLiteIO：.bee 读写、迁移、sqlar 处理
│   ├── schema.py        # 数据库 SCHEMA、USER_VERSION、MIGRATIONS
│   ├── export.py        # 导出器：场景→PNG/JPG/SVG、批量导出图片到目录
│   ├── image.py         # load_image：EXIF 方向修正、URL/Pinterest 抓取
│   └── errors.py        # BeeFileIOError、IMG_LOADING_ERROR_MSG
├── widgets/             # 各种对话框/覆盖层
│   ├── __init__.py      # 进度条、帮助/调试日志对话框、导出大小对话框、透明度、通知、取色控件
│   ├── settings.py      # SettingsDialog（设置面板）
│   ├── welcome_overlay.py   # 空场景时的欢迎页 + 最近文件列表
│   ├── color_gamut.py   # 色域可视化 GamutDialog
│   └── controls/        # 键盘&鼠标设置对话框（keyboard.py / mouse.py / mousewheel.py / common.py）
├── assets/              # 图标、自定义光标 PNG（BeeAssets 单例加载）
└── documentation/       # 帮助文档 HTML（controls.html 等）
```

测试在仓库根的 `tests/` 下，按模块分目录（`tests/actions`、`tests/fileio`、`tests/items` …），
外加 `test_view.py`、`test_scene.py`、`test_main.py` 等顶层测试。`conftest.py` 提供 fixtures。

---

## 4. 核心架构（心智模型）

BeeRef 是典型的 **MVC + 命令模式** 结构，三者职责清晰：

```
              ┌─────────────────────────────────────────┐
              │            BeeGraphicsView (view.py)     │
              │  • 缩放/平移/取色/裁剪等视图层交互        │
              │  • 所有动作回调 on_action_*()             │
              │  • 文件打开/保存/导出的“调度者”          │
              │  • 持有 undo_stack & scene               │
              └───────────────┬─────────────────────────┘
                              │ 操作 items
                              ▼
              ┌─────────────────────────────────────────┐
              │         BeeGraphicsScene (scene.py)      │
              │  • 管理所有 item、选中集合                │
              │  • 排布算法 (arrange_*) / 归一化          │
              │  • 鼠标事件分发（移动 / 框选）            │
              │  • 内部剪贴板                             │
              └───────────────┬─────────────────────────┘
                              │ 增删改
                              ▼
              ┌─────────────────────────────────────────┐
              │      Items (items.py / selection.py)     │
              │  • BeePixmapItem / BeeTextItem / Error   │
              │  • SelectableMixin：选区轮廓/手柄/缩放旋转 │
              └─────────────────────────────────────────┘

   每次“会改动场景”的操作 → 包装成 commands.py 里的 QUndoCommand
   → push 进 view.undo_stack → 自动支持 Ctrl+Z / Ctrl+Shift+Z
```

**关键设计点：**
- `BeeGraphicsView` 通过 **多重继承** 组合：`class BeeGraphicsView(MainControlsMixin, QGraphicsView, ActionsMixin)`。
  这样既拿到视图能力，又混入“主控件（拖放/移动窗口）”和“动作系统”。
- 用户对象（图片/文本）与 UI 辅助对象（多选框 `MultiSelectItem`、框选框 `RubberbandItem`）通过
  **`save_id` 属性** 区分：`selectedItems(user_only=True)` 只返回带 `save_id` 的对象，
  确保保存/排布/变换不会波及 UI 元素。

---

## 5. 关键模块详解

### 5.1 `view.py` — 视图与“总调度”
- 构造函数里创建 `undo_stack`（上限 100 步）、`scene`、`welcome_overlay`，
  调用 `build_menu_and_actions()` 构建菜单，并解析命令行传入的文件。
- **动作回调**：几乎每个菜单项对应一个 `on_action_*` 方法（如 `on_action_save`、`on_action_crop`）。
  阅读这里是理解“功能入口”的最快路径。
- **文件读写**：`open_from_file()` / `do_save()` 不是直接读盘，而是把 `fileio.load_bee` / `fileio.save_bee`
  丢进 `ThreadedIO`（`QThread`）后台执行，配合 `BeeProgressDialog` 显示进度，避免界面卡死。
- **缩放/平移**：`zoom()`、`pan()`、`wheelEvent()`、`fit_rect()`（双击适配），均有“最大/最小尺寸”保护防止溢出。
- **交互模式**：`PAN_MODE` / `ZOOM_MODE` / `SAMPLE_COLOR_MODE` 与 scene 的 `MOVE_MODE` / `RUBBERBAND_MODE` 协作。

### 5.2 `scene.py` — 画布与排布
- 维护 `max_z` / `min_z` 与 `Z_STEP`，实现“置顶/置底”。
- 排布算法：`arrange()`（线形）、`arrange_optimal()`（用 `rpack` 矩形装箱）、`arrange_square()`（方形网格），
  均通过 `commands.ArrangeItems` 入栈以支持撤销。
- 鼠标事件：`mousePressEvent` 判定点中 item → `MOVE_MODE`，否则空白 → `RUBBERBAND_MODE`（框选）。
- `itemsBoundingRect()` 被重写，排除选中手柄，保证框选/导出范围准确。
- `on_selection_change` 在多项选中时显示 `MultiSelectItem` 外框。

### 5.3 `selection.py` — 选中交互的数学
- `BaseItemMixin`：给 item 增加带 **锚点(anchor)** 的 `setScale`/`setRotation`/`do_flip`
  （`with_anchor` 装饰器保证变换时锚点固定），以及 `bring_to_front`、`flip()`（通过变换矩阵 `m11` 判断 1/-1）。
- `SelectableMixin`：绘制选区轮廓与四角手柄（缩放）、旋转区、翻转边；处理 hover 光标、缩放/旋转/翻转的鼠标逻辑。
  所有交互区域尺寸都经 `fixed_length_for_viewport()` 按视图缩放归一化，保证“屏幕上的可点击区域恒定”。
- `MultiSelectItem`：对多选项的统一定界框，其 `selection_action_items()` 返回当前所有选中 item。
- `RubberbandItem`：框选矩形。

### 5.4 `items.py` — 用户对象
- **注册机制**：`@register_item` 装饰器把类按 `TYPE`（`'pixmap'`/`'text'`/`'error'`）注册进 `item_registry`。
  加载 `.bee` 时按 `type` 字段反查类，未知类型回退到 `BeeErrorItem`。
- `BeePixmapItem`：图片项。负责裁剪（crop 模式与 `crop_temp` 临时状态）、灰度（缓存 `_grayscale_pixmap`）、
  透明度、色域计算、`pixmap_to_bytes()`（按设置决定存 PNG 还是 JPG）、`create_copy()`。
- `BeeTextItem`：文本项。可编辑（`enter_edit_mode`/`exit_edit_mode`），空文本退出时自动删除。
- `BeeErrorItem`：加载失败时的占位（永不翻转，“原 save_id”会被保留，保存时不会被覆盖）。
- 保存辅助：`get_extra_save_data()` 返回写入 `items.data` JSON 列的额外字段（filename/opacity/grayscale/crop）。

### 5.5 `actions/` — 动作与菜单系统
- `actions.py`：声明式定义所有 `Action`（id、text、快捷键、回调名、所属启用分组 group）。
  **新增菜单项 = 在这里加一条 Action + 在 `view.py` 加对应 `on_action_*` 方法 + 在 `menu_structure.py` 挂到菜单。**
- `mixin.py`（`ActionsMixin`）：`_create_actions()` 把清单变成 `QAction` 并关联到 view 的回调；
  `bee_actiongroups` 按 group 批量启用/禁用（如 `active_when_selection`、`active_when_can_undo`）。
- `menu_structure.py`：`menu_structure` 列表即菜单树，字符串引用 actions id，dict 表示子菜单，`MENU_SEPARATOR` 为分隔符。

### 5.6 `config/` — 配置
- `settings.py`：
  - `BeeSettings(QSettings)`：应用设置。`FIELDS` 字典声明可配置项及其 default/cast/validate，
    用 `valueOrDefault(key)` 读取（校验失败回退默认值）。设置项含：图片存储格式、排列间距、
    默认排列法、图片内存上限等。
  - `settings_events`：全局信号代理（在 Qt app 创建前无法实例化 `BeeSettings`，故用事件中转）。
  - `CommandlineArgs`：argparse 单例（`--settings-dir` / `-l` 日志级别 / 三个 `--debug-*` 调试开关 / 位置参数文件）。
  - 最近文件：`update_recent_files` / `get_recent_files`。
- `controls.py`：`KeyboardSettings`（独立 ini 文件 `KeyboardSettings.ini`）+ `MouseConfig`/`MouseWheelConfig`，
  支持用户在设置面板修改键鼠映射，并提供冲突检测。

### 5.7 `fileio/` — 持久化与导出
- `sql.py`（`SQLiteIO`）：
  - 表结构：`items`（id/type/x/y/z/scale/rotation/flip/data(JSON)）+ `sqlar`（name/item_id/mode/sz/data(BLOB)），外键级联删除。
  - `read()` 读取并 `add_item_later()` 入队，`write()` 增量更新（已 `save_id` 的 update，否则 insert），删除不再存在的项，最后 `VACUUM`。
  - 迁移：`_migrate()` 按 `USER_VERSION` 执行 `MIGRATIONS`。
  - `handle_sqlite_errors` 装饰器统一处理异常、回滚、通知主线程。
- `schema.py`：`SCHEMA`、`USER_VERSION=2`、`APPLICATION_ID`、`MIGRATIONS`。
- `export.py`：导出器通过 `@register_exporter` 注册到 `exporter_registry`，按扩展名自动选择
  （默认 PNG/JPG、SVG）。`ImagesToDirectoryExporter` 单独走“导出全部图片到目录”菜单。
- `image.py`：`load_image()` 支持本地路径、拖放的 URL、以及 Pinterest 页面抓图；`exif_rotated_image()` 按 EXIF 方向自动旋转。

### 5.8 `widgets/` — 对话框与覆盖层
- `__init__.py` 内聚了多个通用弹窗：`BeeProgressDialog`、`HelpDialog`、`DebugLogDialog`、
  `SceneToPixmapExporterDialog`、`ChangeOpacityDialog`、`BeeNotification`（顶部自动消失提示）、
  `SampleColorWidget`（取色浮窗）、`ExportImagesFileExistsDialog`。
- `welcome_overlay.py`：空场景时的欢迎页 + 最近文件列表（`MainControlsMixin` 子类，可拖放/移动窗口）。
- `settings.py` / `widgets/controls/*`：设置与键鼠映射对话框。

---

## 6. 数据流速查

### 6.1 启动
`__main__.main()` → 初始化日志/设置 → 创建 `BeeRefApplication` → `BeeRefMainWindow`（持有 `BeeGraphicsView` 为中央部件）
→ view 构造函数解析命令行文件（`.bee` 则 `open_from_file`，否则 `do_insert_images`）。

### 6.2 加载 .bee
`view.open_from_file()` → 清空场景 → `ThreadedIO(fileio.load_bee)` → `SQLiteIO.read()`
读到每行 → `scene.add_item_later(data)`（入队）→ 线程结束 `on_loading_finished` → `scene.add_queued_items()`
（`item_registry[type].create_from_data(**data)` 实例化，`update_from_data` 还原变换）→ `fit_scene`。

### 6.3 保存 .bee
`view.on_action_save[_as]()` → `do_save()` → `ThreadedIO(fileio.save_bee)` → `SQLiteIO.write()`
遍历 `scene.items_for_save()` → `insert_item`/`update_item` + 图片字节进 `sqlar` → 删除过期项 → `VACUUM` → `undo_stack.setClean()`。

### 6.4 撤销 / 重做（命令模式）
所有改动都走 `commands.py` 的 `QUndoCommand` 子类，子类必须实现 `redo()`/`undo()`。
约定：交互过程中先“预览”（直接改 item），松开鼠标时 `push` 一个带 `ignore_first_redo=True` 的命令
（首帧 redo 跳过，因为预览已经改过了）。新增可撤销功能应在 `commands.py` 加命令并在 view 的对应 `on_action_*` 里 push。

### 6.5 动作 → 菜单 → 快捷键
`actions.py` 定义 → `ActionsMixin._create_actions()` 建 `QAction` 并绑定 view 回调 →
`menu_structure.py` 决定菜单位置 → `KeyboardSettings` 提供可自定义快捷键。

---

## 7. 配置与运行

开发环境搭建（见 `CONTRIBUTING.rst`）：
```bash
pip install -e .                 # 安装 beeref + 依赖
pip install -r requirements/dev.txt
pytest --cov .                   # 跑测试 + 覆盖率
flake8 .                         # lint
beeref --help                    # 查看命令行选项与调试开关
```
打包可执行文件：`pyinstaller BeeRef.spec`（产物在 `dist/`）。

调试开关（非常有用）：
- `--debug-boundingrects` 画 item 包围盒
- `--debug-shapes` 画鼠标命中区域
- `--debug-handles` 画变换手柄区域

---

## 8. 给未来开发者的注意事项（坑与约定）

1. **永远通过命令模式改场景**：不要绕过 `undo_stack` 直接改 item，否则撤销栈会失真。
2. **`save_id` 是分水岭**：带 `save_id` 的是用户对象；UI 辅助 item（多选框、框选框）不带，
   遍历/保存必须用 `user_only=True` 或 `items_for_save()`。
3. **新增 item 类型**：在 `items.py` 定义类、`@register_item`、设好 `TYPE` 与 `get_extra_save_data()` /
   `create_from_data()` / `create_copy()`；如需进菜单再加 Action。
4. **新增菜单动作**：三处联动——`actions.py` 加 `Action`、`view.py` 加 `on_action_*` 回调、
   `menu_structure.py` 挂菜单（否则动作存在但不可见）。
5. **耗时操作进后台线程**：I/O、图片解码、导出都走 `ThreadedIO`，并通过 `worker.progress` /
   `finished` 信号与进度条通信，切勿在主线程阻塞。
6. **`.bee` 是 SQLite**：可用任意 sqlite 工具直接查看/抽取，调试文件加载问题时优先用 `sqlite3` 确认结构。
7. **视图缩放相关**：交互区域尺寸必须除以视图缩放与 item 缩放（`fixed_length_for_viewport`），否则不同缩放下点不中。
8. **配色与主题**：全局配色在 `constants.COLORS`，由 `utils.create_palette_from_dict` 生成
   `QPalette`；新增 UI 元素应复用这些颜色常量，保持暗色风格统一。
9. **`BeeSettings`/`CommandlineArgs`/`BeeAssets` 都是单例**：多次实例化返回同一实例，注意不要重复初始化。
10. **测试**：改动核心逻辑后务必跑 `pytest`；`tests/` 已按模块划分，新增功能建议补对应测试。

---

## 9. 速查索引（改某某功能看哪里）

| 想改/加的功能 | 主要文件 |
|---------------|----------|
| 菜单项 / 快捷键 | `actions/actions.py`、`actions/menu_structure.py`、`view.py` |
| 图片变换（缩放/旋转/翻转/裁剪） | `selection.py`、`items.py`、`commands.py` |
| 排布 / 对齐 | `scene.py`（`arrange_*`、`normalize_*`） |
| 画布交互（缩放/平移/双击） | `view.py` |
| 文本便签 | `items.py`（`BeeTextItem`） |
| 颜色采样 / 灰度 / 透明度 | `items.py`、`view.py`、`widgets/` |
| 保存 / 加载 .bee | `fileio/sql.py`、`fileio/__init__.py`、`schema.py` |
| 导出图片 / SVG | `fileio/export.py` |
| 设置面板 | `widgets/settings.py`、`config/settings.py` |
| 键鼠映射 | `config/controls.py`、`widgets/controls/` |
| 撤销重做 | `commands.py` |
| 欢迎页 / 最近文件 | `widgets/welcome_overlay.py`、`config/settings.py` |
| 图标 / 光标 | `assets/`、`assets/__init__.py` |
| 打包 | `BeeRef.spec`、`tools/` |
