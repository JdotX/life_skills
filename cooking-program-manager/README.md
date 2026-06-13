# Cooking Program Manager — 每周烹饪计划管理

自动编排下周菜单、生成购物清单。从收藏的菜谱链接中获取内容，按约束条件规划一周饮食。

## 快速开始

```bash
# 1. 把菜谱链接放入 bookmarks.txt
echo "https://www.douguo.net/cookbook/xxx.html" >> data/bookmarks.txt

# 2. 提取并获取所有菜谱内容
python3 scripts/extract_urls.py data/bookmarks.txt
python3 scripts/fetch_recipes.py --batch data/bookmarks.txt

# 3. 编排菜单 → 输出到 data/weekly_menu_<周次>.csv
# 4. 生成购物计划 → 输出到 data/shopping_plan_<周次>.csv
```

## 文件结构

```
cooking-program-manager/
├── SKILL.md                    # Claude Code 技能定义（调用入口）
├── prompt.md                   # 完整执行提示词
├── README.md                   # 本文件
├── scripts/
│   ├── extract_urls.py         # 从文件中提取所有 URL，标记菜谱
│   ├── fetch_recipes.py        # 获取页面内容（HTTP / headless / CDP）
│   ├── plan_menu.py            # 编排菜单辅助脚本
│   ├── generate_shopping.py    # 生成购物计划辅助脚本
│   └── send_reminder.py        # （可选）发送 webhook 提醒
├── references/
│   └── data-structure.md       # 数据格式参考
└── data/
    ├── bookmarks.txt           # （个人）收藏的菜谱链接
    ├── config.json             # （个人）配置文件
    ├── blacklist.txt           # 黑名单
    ├── history.csv             # （自动生成）历史菜单记录
    ├── weekly_menu_*.csv       # （自动生成）每周菜单
    └── shopping_plan_*.csv     # （自动生成）购物计划
```

> `data/` 中标明"个人"或"自动生成"的文件已加入 `.gitignore`，不会被提交到仓库。

## 编排规则

| 项目 | 要求 |
|------|------|
| 天数 | 5 个工作日（周一至周五） |
| 每天 | 1 道荤菜 + 1 道素菜，或 1 道荤素搭配菜 |
| 素菜限制 | 不能是白灼或清炒单一品种青菜 |
| 周内重复 | 一周之内不能有重复内容 |
| 历史去重 | 尽量与上周不重复（相同链接或相似菜品） |
| 主材料 | 避免重复主材料（排骨和排骨不行；排骨和猪肉可接受） |
| 黑名单 | 尽量不选取黑名单中的菜 |

## 购买时间安排

| 购买时间 | 覆盖天数 |
|----------|---------|
| 周日晚上 | 周一、周二 |
| 周三早晨 | 周三、周四 |
| 周五早晨 | 仅周五 |

## 输出示例

### 菜单（`data/weekly_menu_2026-W25.csv`）

```
日期,index,菜名,链接
2026-06-15,1,清炖牛肋条,https://www.douguo.net/cookbook/3299891.html
2026-06-15,2,脆皮豆腐,https://www.douguo.net/cookbook/1377192.html
...
```

### 购物计划（`data/shopping_plan_2026-W25.csv`）

```
购买时间,菜品,食材
周日晚上,清炖牛肋条,牛肋条500g 姜1块 葱2根 料酒 盐
周日晚上,脆皮豆腐,老豆腐1块 鸡蛋1个 淀粉 番茄酱 糖 醋
...
```

## 支持的菜谱网站

| 网站 | 状态 |
|------|------|
| 豆果美食 douguo.net | 正常，他的访问平摊下来rate limit应该是5秒一次，但我不确定是不是有什么原因让这个结果不稳定 |
| 美食天下 meishichina.com | 正常，没去研究rate limit到底是多少 |
| 头条 toutiao.com | 正常，不过头条不太好专门找菜谱帖子 |
| 下厨房 xiachufang.com | 大哥，作为一个菜谱网站，你robot.txt不允许爬菜谱这是玩啥呢？于是我deepseek问这是不是一家xx系公司，答：他不是，只是高管曾任职于XX |
| 小红书 xiaohongshu.com | 需 CDP 连接登录浏览器，但是我还没试，可能后面研究怎么用吧 |

## 配置

复制 `data/config.json` 模板：

```json
{
  "webhook_url": "https://your-webhook-url.com/cooking-reminder",
  "bookmarks_file": "data/bookmarks.txt",
  "use_lack_cli": false,
  "default_weekdays": ["周一", "周二", "周三", "周四", "周五"],
  "purchase_schedule": {
    "周日晚上": ["周一", "周二"],
    "周三早晨": ["周三", "周四"],
    "周五早晨": ["周五"]
  }
}
```
