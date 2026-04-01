"""
ネイルトレンドリサーチエージェント
毎週のネイル・ネイルサロントレンドをWebから調査するエージェント
（claude -p --allowedTools WebSearch,WebFetch 版）
"""

import json
import subprocess
from datetime import datetime

RESEARCH_SYSTEM_PROMPT = """あなたはネイル業界の専門リサーチャーです。
ネイルサロン経営者やネイリストに向けて、最新のネイルトレンドを調査・収集するのが専門です。

調査する内容:
1. 国内・海外の最新ネイルデザイントレンド（色、柄、技法）
2. 話題のネイルアート・ネイルアーティスト
3. SNS（Instagram、TikTok、Pinterest）で流行しているネイルスタイル
4. 季節・イベントに合わせたトレンドカラー
5. ネイルケア・ジェルネイル技術の新しい動向
6. 人気ネイルブランドの新製品情報

収集した情報は以下のJSON形式のみで出力してください（前後の説明文不要）:
{
  "research_date": "YYYY-MM-DD",
  "trends": [
    {
      "category": "カテゴリ名",
      "title": "トレンドタイトル",
      "description": "詳細説明",
      "sources": ["参考URL1"],
      "keywords": ["キーワード1", "キーワード2"],
      "relevance_score": 1から5
    }
  ],
  "hot_colors": ["カラー1", "カラー2"],
  "hot_techniques": ["技法1", "技法2"],
  "summary_for_next_agent": "次のエージェントへの引き継ぎメモ"
}"""


def _call_claude(prompt: str, system: str = "", tools: str = "", timeout: int = 300) -> str:
    """claude -p でClaudeを呼び出し、テキスト結果を返す"""
    cmd = [
        "claude", "-p",
        "--no-session-persistence",
        "--output-format", "text",
    ]
    if tools:
        cmd += ["--allowedTools", tools]
    else:
        cmd += ["--allowedTools", ""]
    if system:
        cmd += ["--system-prompt", system]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd="/tmp",
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed (exit {result.returncode}): {result.stderr[:300]}")
    return result.stdout.strip()


def get_current_season() -> str:
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"


async def run_research_agent() -> dict:
    """ネイルトレンドリサーチを実行し、結果をdictで返す"""
    season = get_current_season()
    today = datetime.now().strftime("%Y年%m月%d日")

    print("🔍 リサーチエージェント起動中...")
    print(f"📅 調査日: {today} ({season})")
    print("-" * 50)

    prompt = f"""今日は{today}です。今週の最新ネイルトレンドを徹底的にリサーチしてください。

調査ポイント:
1. 「ネイル トレンド 2025」「nail trends {datetime.now().year}」などで検索
2. 季節のトレンドカラー（現在は{season}シーズン）
3. 海外（アメリカ・ヨーロッパ・韓国）の最新ネイルトレンド
4. 日本国内のネイルサロンで人気のスタイル
5. SNSで話題のネイルデザイン・ハッシュタグ

最低5つ以上のトレンドを調査し、指定のJSON形式のみで出力してください。"""

    raw = _call_claude(
        prompt,
        system=RESEARCH_SYSTEM_PROMPT,
        tools="WebSearch,WebFetch",
        timeout=300,
    )
    print("✅ リサーチ完了")

    # JSONを抽出
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            research_data = json.loads(raw[start:end])
        else:
            raise ValueError("JSON not found")
    except (json.JSONDecodeError, ValueError):
        research_data = {
            "research_date": datetime.now().strftime("%Y-%m-%d"),
            "raw_text": raw,
            "trends": [],
            "hot_colors": [],
            "hot_techniques": [],
            "summary_for_next_agent": raw,
        }

    return research_data


if __name__ == "__main__":
    import anyio
    result = anyio.run(run_research_agent)
    print("\n📊 リサーチ結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
