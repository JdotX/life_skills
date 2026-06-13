---
name: cooking-program-manager
description: >
  管理每周烹饪计划。从文件中提取菜谱链接，获取菜谱内容，编排下周菜单，生成购物清单。
  当用户提到"菜单规划"、"每周菜单"、"购物清单"、"买菜计划"、"下周吃什么"或"菜谱管理"时触发。
  用户可通过 /cooking-program-manager 手动调用。
version: 1.0.0
user-invocable: true
---

# Cooking Program Manager

每周烹饪计划管理工具。按以下流程编排下周菜单、生成购物计划和每日预处理提醒。

## 工作流程

### 第一步：从源文件提取菜谱 URL

1. 确定源文件路径。默认使用 `recipes.md` 或用户指定的文件。
2. 使用 `extract_urls.py` 脚本从文件中提取所有 URL。
3. 识别哪些是菜谱链接、哪些是其他链接。

```bash
python3 scripts/extract_urls.py <文件路径>
```

### 第二步：获取菜谱内容

对每个菜谱 URL：
1. 尝试直接用 HTTP 获取内容
2. 如果获取不到（需要 JS 渲染），使用 `fetch_recipes.py` 的 headless browser 模式

```bash
python3 scripts/fetch_recipes.py <url> [--headless]
```

### 第三步：编排下周菜单

#### 约束条件

| 项目 | 要求 |
|------|------|
| 天数 | 5 个工作日（周一至周五） |
| 每天 | 1 道荤菜 + 1 道素菜，或 1 道荤素搭配菜 |
| 素菜限制 | 不能是白灼或清炒单一品种青菜 |
| 周内重复 | 一周之内不能有重复内容 |
| 与上周对比 | 尽量和上一周不重复（相同链接或内容相似的菜） |
| 主材料 | 尽量不要有重复的主材料（排骨和排骨不行；排骨和猪肉可接受但优先级不如排骨和牛肉） |
| 黑名单 | 尽量不选取黑名单中的菜 |

#### 数据文件

- **历史文件**：`data/history.csv`，格式同 CSV 输出
- **黑名单文件**：`data/blacklist.txt`，每行一个菜名
- **上周菜单**：从历史文件中倒序查找最近一周的记录

#### 输出格式

CSV 文件，列：`日期, index, 菜名, 链接`

保存到 `data/weekly_menu_<周次>.csv`

### 第四步：生成购物计划

按如下时间安排购买：

| 购买时间 | 覆盖天数 |
|----------|---------|
| 周日晚上 | 周一、周二 |
| 周三早晨 | 周三、周四 |
| 周五早晨 | 仅周五 |

输出文件：`data/shopping_plan_<周次>.csv`

### 第五步：设置每日预处理提醒（可选）

每天早上 9:00 可发送提醒到 webhook，内容如"提前2小时泡发木耳"。

- 读取 `config.json` 中的 webhook 地址
- 每天早上生成当天的预处理清单
- 发送到 webhook

如需启用，运行 `bash scripts/setup_cron.sh` 安装定时任务。

## 文件结构

```
cooking-program-manager/
├── SKILL.md            # 本文件
├── prompt.md           # 完整提示词
├── scripts/
│   ├── extract_urls.py        # 从文件中提取所有 URL
│   ├── fetch_recipes.py       # 获取菜谱内容（支持 headless browser）
│   ├── plan_menu.py           # 编排菜单（备选脚本方式）
│   ├── generate_shopping.py   # 生成购物计划
│   └── send_reminder.py       # （可选）发送 webhook 提醒
├── references/
│   └── data-structure.md      # 数据格式参考
└── data/
    ├── history.csv            # 历史菜谱记录
    ├── blacklist.txt          # 黑名单
    ├── config.json            # 配置（webhook 地址等）
    └── weekly_menu_*.csv      # 每周菜单输出
```

## 配置

`data/config.json` 示例：
```json
{
  "webhook_url": "https://example.com/webhook",
  "source_file": "recipes.md",
  "default_weekdays": ["周一", "周二", "周三", "周四", "周五"]
}
```

## 使用示例

```bash
# 用户输入
/cooking-program-manager

# 或
帮我规划下周的菜谱
```
