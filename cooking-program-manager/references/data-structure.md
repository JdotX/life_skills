# 数据格式参考

## history.csv

累积记录所有执行过的菜单。

```csv
日期,index,菜名,链接
2026-06-08,1,红烧排骨,https://example.com/ribs
2026-06-08,2,清炒西兰花,https://example.com/broccoli
2026-06-09,1,麻婆豆腐,https://example.com/tofu
...
```

- 日期：ISO 格式 `YYYY-MM-DD`
- index：当天的第几道菜（从 1 开始）
- 菜名：菜的中文名
- 链接：菜谱 URL

## weekly_menu_<周次>.csv

每周输出，周次格式如 `2026-W25`。

## shopping_plan_<周次>.csv

```csv
购买时间,菜品,食材清单
周日晚上,红烧排骨,排骨500g,姜,蒜,生抽,老抽,料酒,冰糖
周日晚上,蒜蓉西兰花,西兰花,蒜,盐,油
周三早晨,麻婆豆腐,豆腐,肉末,豆瓣酱,花椒粉
周五早晨,清蒸鱼,鱼,姜,葱,蒸鱼豉油
```

## blacklist.txt

```
水煮白菜
白灼菜心
清炒油麦菜
```

## config.json

```json
{
  "webhook_url": "https://hooks.example.com/cooking-reminder",
  "source_file": "/path/to/recipes.md",
  "default_weekdays": ["周一", "周二", "周三", "周四", "周五"],
  "purchase_schedule": {
    "周日晚上": ["周一", "周二"],
    "周三早晨": ["周三", "周四"],
    "周五早晨": ["周五"]
  }
}
```
