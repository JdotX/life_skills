#!/bin/bash
# 设置系统定时任务（cron）用于自动生成购物计划和发送预处理提醒
#
# 购买时间：
#   周日晚上 → 周一、周二
#   周三早晨 → 周三、周四
#   周五早晨 → 仅周五
# 提醒时间：
#   每天 9:00 → 发送当日预处理提醒
#
# 用法: bash scripts/setup_cron.sh

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CRON_FILE="/tmp/cooking-cron-$$"

cat > "$CRON_FILE" << EOF
# === Cooking Program Manager 定时任务 ===
# 每周日 20:00 生成购物计划（周一、周二食材）
0 20 * * 0 cd $SKILL_DIR && python3 scripts/generate_shopping.py --menu data/weekly_menu_*.csv >> data/cron.log 2>&1

# 每周三 07:00 生成购物计划（周三、周四食材）
0 7 * * 3 cd $SKILL_DIR && python3 scripts/generate_shopping.py --menu data/weekly_menu_*.csv >> data/cron.log 2>&1

# 每周五 07:00 生成购物计划（周五食材）
0 7 * * 5 cd $SKILL_DIR && python3 scripts/generate_shopping.py --menu data/weekly_menu_*.csv >> data/cron.log 2>&1

# 每天 9:00 发送当日预处理提醒
0 9 * * * cd $SKILL_DIR && python3 scripts/send_reminder.py >> data/cron.log 2>&1
EOF

echo "将添加以下定时任务："
cat "$CRON_FILE"
echo ""
echo "是否安装这些定时任务？(y/n)"
read -r answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    crontab -l 2>/dev/null | cat - "$CRON_FILE" | crontab -
    echo "定时任务已安装。"
    echo ""
    echo "当前所有定时任务："
    crontab -l
else
    echo "已取消。"
fi

rm -f "$CRON_FILE"
