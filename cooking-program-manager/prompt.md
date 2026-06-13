# Cooking Program Manager - 完整执行提示词

## 任务概述

作为一个烹饪计划管理工具，你需要完成以下流程：

## Step 1: 提取 URL

从指定的源文件中提取所有 URL。源文件可能是 `.md`、`.txt` 或其他文本格式。

执行脚本：
```bash
python3 scripts/extract_urls.py <文件路径>
```

输出：所有 URL 列表，标记哪些是菜谱、哪些是其他链接。

## Step 2: 获取菜谱内容

对每个菜谱 URL 获取完整内容。优先直接 HTTP 获取，失败则使用 headless browser。

```bash
# 直接获取
python3 scripts/fetch_recipes.py <url>

# 需要 headless browser
python3 scripts/fetch_recipes.py <url> --headless
```

提取的信息包括：菜名、主料、辅料、烹饪步骤、预处理步骤（如泡发）。

## Step 3: 编排下周菜单

### 输入数据

- **菜谱池**：上一步获取的所有菜谱
- **历史记录**：`data/history.csv`（日期, index, 菜名, 链接）
- **黑名单**：`data/blacklist.txt`（每行一个菜名）

### 编排算法

1. 确定下周的日期范围（周一至周五）
2. 从历史文件中读取上周菜单（倒序查找最近5条记录）
3. 从菜谱池中挑选符合条件的菜：
   - 排除黑名单中的菜
   - 排除上周已选过的菜（相同链接或内容相似）
   - 优先避免主材料重复
4. 每天安排 1 道荤菜 + 1 道素菜/荤素搭配菜
   - 素菜不能是白灼或清炒单一品种青菜
5. 周内不能重复

### 输出

保存到 `data/weekly_menu_<周次>.csv`，格式：
```
日期,index,菜名,链接
2026-06-15,1,红烧排骨,http://...
2026-06-15,2,蒜蓉西兰花,http://...
...
```

## Step 4: 生成购物计划

根据菜单生成购物计划，按购买时间分组。

输出 `data/shopping_plan_<周次>.csv`：
```
购买时间,菜品,食材
周日晚上,红烧排骨,排骨500g 姜 蒜 酱油...
周日晚上,蒜蓉西兰花,西兰花 蒜...
周三早晨,麻婆豆腐,豆腐 肉末...
...
```

购买时间规则：
- 周日晚上 → 周一、周二的菜
- 周三早晨 → 周三、周四的菜
- 周五早晨 → 仅周五的菜

## 数据文件说明

### data/history.csv

累积所有历史菜单，用于去重和参考。

### data/blacklist.txt

用户不想吃的菜，每行一个菜名。

### data/config.json

```json
{
  "webhook_url": "https://your-webhook-url.com/endpoint",
  "source_file": "recipes.md",
  "default_weekdays": ["周一", "周二", "周三", "周四", "周五"]
}
```
