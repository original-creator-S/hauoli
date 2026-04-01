"""
ネイルトレンドエージェント オーケストレーター
3つのエージェントを順番に実行して週次トレンドレポートを生成・公開する

使い方:
    python run_agents.py              # 全エージェントを実行
    python run_agents.py --research   # リサーチのみ
    python run_agents.py --summary    # 要約のみ（research_cache.jsonが必要）
    python run_agents.py --website    # HTML更新のみ（summary_cache.jsonが必要）
    python run_agents.py --dry-run    # サンプルデータでテスト実行
"""

import anyio
import json
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# エージェントモジュールのインポート
sys.path.insert(0, os.path.dirname(__file__))
from agents.nail_trend_researcher import run_research_agent
from agents.trend_summarizer import run_summarizer_agent
from agents.website_updater import run_website_updater_agent

# キャッシュファイルのパス
CACHE_DIR = Path(__file__).parent / ".agent_cache"
RESEARCH_CACHE = CACHE_DIR / "research_cache.json"
SUMMARY_CACHE = CACHE_DIR / "summary_cache.json"
TRENDS_HTML = Path(__file__).parent / "trends.html"

# サンプルデータ（--dry-run 用）
DRY_RUN_RESEARCH = {
    "research_date": datetime.now().strftime("%Y-%m-%d"),
    "trends": [
        {
            "category": "デザイン",
            "title": "オーロラネイル（Aurora Nails）",
            "description": "光の当たり方で虹色に変化するオーロラ効果。パウダーやホイルを使用。",
            "sources": ["https://www.instagram.com/explore/tags/auroranails/"],
            "keywords": ["オーロラ", "ホログラム", "虹色", "aurora"],
            "relevance_score": 5,
        },
        {
            "category": "カラー",
            "title": "テラコッタ・アースカラー",
            "description": "秋冬に向けた土っぽい暖色系。テラコッタ、バーントオレンジ、モカブラウンが人気。",
            "sources": [],
            "keywords": ["テラコッタ", "アースカラー", "秋冬", "earth tones"],
            "relevance_score": 5,
        },
        {
            "category": "技法",
            "title": "グラスネイル（Glass Nails）",
            "description": "韓国発。カラーホイルを封入した透明感あるデザイン。",
            "sources": [],
            "keywords": ["グラスネイル", "ガラス", "透明感", "韓国ネイル"],
            "relevance_score": 4,
        },
        {
            "category": "デザイン",
            "title": "ミニマルフレンチ",
            "description": "細いラインのフレンチネイル。カラーフレンチも人気。",
            "sources": [],
            "keywords": ["フレンチ", "ミニマル", "細ライン"],
            "relevance_score": 4,
        },
        {
            "category": "ケア",
            "title": "ネイルケアへの注目",
            "description": "健康的な爪へのケアメニュー需要増。爪育成・保湿ケアが人気。",
            "sources": [],
            "keywords": ["ネイルケア", "爪育成", "保湿", "ヘルシーネイル"],
            "relevance_score": 3,
        },
    ],
    "hot_colors": ["テラコッタ", "ミルキーホワイト", "モーヴ", "バーガンディ", "ミルクチョコ"],
    "hot_techniques": ["オーロラパウダー", "グラスネイル", "フレンチ細ライン", "ベルベットネイル"],
    "summary_for_next_agent": "今週の最大トレンドはオーロラネイルとアースカラー。韓国ネイルトレンドも注目。秋冬シーズンへの移行期。",
}


def save_cache(data: dict, path: Path):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 キャッシュ保存: {path.name}")


def load_cache(path: Path) -> dict | None:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def print_banner():
    print("=" * 60)
    print("  🌸 hauoli ネイルトレンドエージェント 🌸")
    print("=" * 60)
    print(f"  実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 60)


async def run_all(dry_run: bool = False):
    """全エージェントをパイプラインで実行"""
    print_banner()

    # ─── Step 1: リサーチエージェント ───────────────────────
    print("\n【Step 1/3】ネイルトレンドリサーチ")
    if dry_run:
        print("  (ドライランモード: サンプルデータを使用)")
        research_data = DRY_RUN_RESEARCH
    else:
        research_data = await run_research_agent()

    save_cache(research_data, RESEARCH_CACHE)
    trend_count = len(research_data.get("trends", []))
    print(f"  → {trend_count}件のトレンドを収集")

    # ─── Step 2: 要約エージェント ───────────────────────────
    print("\n【Step 2/3】サロン経営者向け要約")
    summary_data = await run_summarizer_agent(research_data)
    save_cache(summary_data, SUMMARY_CACHE)
    priority_count = len(summary_data.get("priority_trends", []))
    print(f"  → {priority_count}件の優先トレンドをまとめました")

    # ─── Step 3: ウェブサイト更新エージェント ───────────────
    print("\n【Step 3/3】ウェブサイト更新")
    output_path = await run_website_updater_agent(summary_data, str(TRENDS_HTML))

    # 完了レポート
    print("\n" + "=" * 60)
    print("  ✨ 全エージェント完了！")
    print("=" * 60)
    print(f"  📊 リサーチ結果:  {RESEARCH_CACHE}")
    print(f"  📝 要約レポート:  {SUMMARY_CACHE}")
    print(f"  🌐 ウェブサイト:  {output_path}")
    print("=" * 60)

    return {
        "research": research_data,
        "summary": summary_data,
        "website": output_path,
    }


async def run_research_only():
    """リサーチエージェントのみ実行"""
    print_banner()
    print("\n【リサーチのみ実行】")
    data = await run_research_agent()
    save_cache(data, RESEARCH_CACHE)
    return data


async def run_summary_only():
    """要約エージェントのみ実行（キャッシュからリサーチデータを読み込む）"""
    print_banner()
    print("\n【要約のみ実行】")
    research_data = load_cache(RESEARCH_CACHE)
    if not research_data:
        print(f"❌ リサーチキャッシュが見つかりません: {RESEARCH_CACHE}")
        print("  先に --research を実行してください")
        return None
    data = await run_summarizer_agent(research_data)
    save_cache(data, SUMMARY_CACHE)
    return data


async def run_website_only():
    """HTML更新エージェントのみ実行（キャッシュから要約データを読み込む）"""
    print_banner()
    print("\n【ウェブサイト更新のみ実行】")
    summary_data = load_cache(SUMMARY_CACHE)
    if not summary_data:
        print(f"❌ 要約キャッシュが見つかりません: {SUMMARY_CACHE}")
        print("  先に --summary を実行してください")
        return None
    path = await run_website_updater_agent(summary_data, str(TRENDS_HTML))
    return path


def main():
    parser = argparse.ArgumentParser(
        description="hauoli ネイルトレンドエージェント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使い方:
  python run_agents.py              全エージェントを実行（推奨）
  python run_agents.py --dry-run    サンプルデータでテスト実行
  python run_agents.py --research   リサーチのみ
  python run_agents.py --summary    要約のみ
  python run_agents.py --website    HTML更新のみ
        """,
    )
    parser.add_argument("--research", action="store_true", help="リサーチエージェントのみ実行")
    parser.add_argument("--summary", action="store_true", help="要約エージェントのみ実行")
    parser.add_argument("--website", action="store_true", help="ウェブサイト更新エージェントのみ実行")
    parser.add_argument("--dry-run", action="store_true", help="サンプルデータでテスト実行（API不要）")

    args = parser.parse_args()

    if args.research:
        anyio.run(run_research_only)
    elif args.summary:
        anyio.run(run_summary_only)
    elif args.website:
        anyio.run(run_website_only)
    else:
        anyio.run(run_all, args.dry_run)


if __name__ == "__main__":
    main()
