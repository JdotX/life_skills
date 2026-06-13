#!/usr/bin/env python3
"""
发送每日预处理提醒到 webhook。

用法：
  python3 send_reminder.py                    # 发送今天的提醒
  python3 send_reminder.py --date 2026-06-15  # 发送指定日期的提醒
  python3 send_reminder.py --dry-run          # 仅打印不发送
"""

import json
import sys
import argparse
from datetime import date, datetime
from pathlib import Path

import requests


def load_config(config_path: str = "data/config.json") -> dict:
    """加载配置文件。"""
    path = Path(config_path)
    if not path.exists():
        print(f"错误: 配置文件不存在 - {config_path}", file=sys.stderr)
        print("请先创建 data/config.json", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def load_menu_for_date(menu_dir: str, target_date: date) -> list[dict]:
    """加载指定日期的菜单项。"""
    menu_dir_path = Path(menu_dir)
    dishes = []
    for csv_file in sorted(menu_dir_path.glob("weekly_menu_*.csv")):
        lines = csv_file.read_text(encoding="utf-8").strip().splitlines()
        for line in lines[1:]:  # 跳过表头
            parts = line.split(",")
            if len(parts) >= 4:
                d, idx, name, link = parts[0], parts[1], parts[2], parts[3]
                if d == target_date.isoformat():
                    dishes.append({"菜名": name, "链接": link})
    return dishes


def generate_reminders(dishes: list[dict]) -> list[str]:
    """根据菜单生成预处理提醒。"""
    # 常见预处理关键词
    prep_keywords = {
        "泡发": ["木耳", "香菇", "海带", "腐竹", "粉条", "粉丝", "银耳"],
        "腌制": ["肉", "排骨", "鸡", "鱼", "牛肉", "虾"],
        "解冻": ["肉", "排骨", "鸡", "鱼", "虾", "牛肉"],
        "浸泡": ["米", "豆", "糯米"],
    }

    reminders = []
    for dish in dishes:
        name = dish["菜名"]
        for action, ingredients in prep_keywords.items():
            for ing in ingredients:
                if ing in name:
                    reminders.append(f"{action}{ing}")
                    break

    return list(set(reminders))  # 去重


def send_webhook(webhook_url: str, payload: dict, dry_run: bool = False) -> bool:
    """发送 webhook 请求。"""
    if dry_run:
        print(f"[DRY RUN] 将发送到 {webhook_url}")
        print(f"[DRY RUN] 载荷: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        return True

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        print(f"提醒发送成功: {resp.status_code}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"发送失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="发送每日预处理提醒")
    parser.add_argument("--date", type=str, help="日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不发送")
    parser.add_argument("--config", type=str, default="data/config.json", help="配置文件路径")
    parser.add_argument("--menu-dir", type=str, default="data", help="菜单文件目录")
    args = parser.parse_args()

    config = load_config(args.config)
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        print("错误: 配置中缺少 webhook_url", file=sys.stderr)
        sys.exit(1)

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    # 星期映射
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_name = weekday_names[target_date.weekday()]

    dishes = load_menu_for_date(args.menu_dir, target_date)
    if not dishes:
        print(f"{target_date} ({weekday_name}) 没有找到菜单", file=sys.stderr)
        return

    reminders = generate_reminders(dishes)

    payload = {
        "type": "cooking_reminder",
        "date": target_date.isoformat(),
        "weekday": weekday_name,
        "reminders": reminders,
        "message": f"【{weekday_name}预处理提醒】" + "、".join(reminders) if reminders else f"【{weekday_name}】今日无需特殊预处理",
    }

    send_webhook(webhook_url, payload, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
