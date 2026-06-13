#!/usr/bin/env python3
"""
根据每周菜单生成购物计划。

用法：
  python3 generate_shopping.py --menu data/weekly_menu_<周次>.csv [--output data/shopping_plan_<周次>.csv]
"""

import csv
import json
import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

# 购买时间与覆盖日期的映射
PURCHASE_SCHEDULE = {
    "周日晚上": [0, 1],   # 周一(0)、周二(1)
    "周三早晨": [2, 3],   # 周三(2)、周四(3)
    "周五早晨": [4],       # 仅周五(4)
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五"]


def load_menu(menu_path: str) -> list[dict]:
    """加载菜单 CSV。"""
    path = Path(menu_path)
    if not path.exists():
        print(f"错误: 菜单文件不存在 - {menu_path}", file=sys.stderr)
        sys.exit(1)

    dishes = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 跳过注释行
            if row.get("日期", "").startswith("#"):
                continue
            dishes.append(row)
    return dishes


def group_dishes_by_date(dishes: list[dict]) -> dict[str, list[dict]]:
    """按日期分组。"""
    groups = {}
    for dish in dishes:
        d = dish["日期"]
        if d not in groups:
            groups[d] = []
        groups[d].append(dish)
    return groups


def get_dates_for_purchase(menu_dates: list[date]) -> dict[str, list[str]]:
    """计算每个购买时间对应的日期和菜品。"""
    result = {}
    for purchase_time, weekday_indices in PURCHASE_SCHEDULE.items():
        covered_dates = []
        for idx in weekday_indices:
            if idx < len(menu_dates):
                covered_dates.append({
                    "date": str(menu_dates[idx]),
                    "weekday": WEEKDAY_NAMES[idx],
                })
        result[purchase_time] = covered_dates
    return result


def main():
    parser = argparse.ArgumentParser(description="生成购物计划")
    parser.add_argument("--menu", required=True, help="每周菜单 CSV 文件路径")
    parser.add_argument("--output", default=None, help="输出 CSV 路径")
    args = parser.parse_args()

    dishes = load_menu(args.menu)
    if not dishes:
        print("错误: 菜单为空", file=sys.stderr)
        sys.exit(1)

    # 确定下周日期
    today = date.today()
    days_ahead = 7 - today.weekday()
    next_monday = today + timedelta(days=days_ahead)
    menu_dates = [next_monday + timedelta(days=i) for i in range(5)]

    week_num = menu_dates[0].strftime("%Y-W%W")
    output_path = args.output or f"data/shopping_plan_{week_num}.csv"

    by_date = group_dishes_by_date(dishes)
    purchase_dates = get_dates_for_purchase(menu_dates)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["购买时间", "日期", "菜品", "食材清单"])

        for purchase_time, covered in purchase_dates.items():
            for item in covered:
                d = item["date"]
                weekday = item["weekday"]
                day_dishes = by_date.get(d, [])
                for dish in day_dishes:
                    writer.writerow([purchase_time, f"{d}({weekday})", dish.get("菜名", ""), ""])

    print(f"购物计划已生成: {output_path}", file=sys.stderr)
    print(json.dumps({
        "output_file": output_path,
        "purchase_schedule": {
            k: [c["date"] for c in v]
            for k, v in purchase_dates.items()
        }
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
