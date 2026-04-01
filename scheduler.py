"""
週次ネイルトレンドエージェント スケジューラー
毎週月曜日の朝9時に自動実行する常駐スクリプト
実行方法: python scheduler.py
バックグラウンド実行: nohup python scheduler.py > scheduler.log 2>&1 &
"""

import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "scheduler.log"
AGENT_SCRIPT = Path(__file__).parent / "run_agents.py"
PYTHON = sys.executable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def run_weekly_agents():
    logger.info("=" * 50)
    logger.info("週次ネイルトレンドエージェント 自動実行開始")
    logger.info("=" * 50)
    try:
        result = subprocess.run(
            [PYTHON, str(AGENT_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=1200,  # 20分
            cwd=str(Path(__file__).parent),
        )
        if result.returncode == 0:
            logger.info("✅ エージェント実行完了")
            logger.info(result.stdout)
        else:
            logger.error(f"❌ エージェント実行失敗 (exit {result.returncode})")
            logger.error(result.stderr)
    except subprocess.TimeoutExpired:
        logger.error("❌ タイムアウト (20分超過)")
    except Exception as e:
        logger.error(f"❌ 予期せぬエラー: {e}")


# 毎週月曜日 09:00 に実行
schedule.every().monday.at("09:00").do(run_weekly_agents)

if __name__ == "__main__":
    logger.info(f"スケジューラー起動: 毎週月曜日 09:00 に実行予定")
    logger.info(f"次回実行予定: {schedule.next_run()}")
    logger.info("停止するには Ctrl+C を押してください")

    while True:
        schedule.run_pending()
        time.sleep(60)
