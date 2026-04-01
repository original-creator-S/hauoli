"""
ネイルトレンドリサーチエージェント
毎週のネイル・ネイルサロントレンドをWebから調査するエージェント
"""

import anyio
import json
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

RESEARCH_SYSTEM_PROMPT = """あなたはネイル業界の専門リサーチャーです。
ネイルサロン経営者やネイリストに向けて、最新のネイルトレンドを調査・収集するのが専門です。

調査する内容:
1. 国内・海外の最新ネイルデザイントレンド（色、柄、技法）
2. 話題のネイルアート・ネイルアーティスト
3. SNS（Instagram、TikTok、Pinterest）で流行しているネイルスタイル
4. 季節・イベントに合わせたトレンドカラー
5. ネイルケア・ジェルネイル技術の新しい動向
6. 人気ネイルブランド・カラーの新製品情報

収集した情報は、後で要約エージェントが処理しやすいよう、
以下の構造でJSON形式にまとめてください:

{
  "research_date": "YYYY-MM-DD",
  "trends": [
    {
      "category": "カテゴリ名",
      "title": "トレンドタイトル",
      "description": "詳細説明",
      "sources": ["参考URL1", "参考URL2"],
      "keywords": ["キーワード1", "キーワード2"],
      "relevance_score": 1-5
    }
  ],
  "hot_colors": ["カラー1", "カラー2"],
  "hot_techniques": ["技法1", "技法2"],
  "summary_for_next_agent": "次のエージェントへの引き継ぎメモ"
}
"""

RESEARCH_PROMPT = """今週のネイルトレンドを徹底的にリサーチしてください。

以下の観点で調査してください:
1. 「ネイル トレンド 2024 2025」「nail trends」などで検索し、最新情報を収集
2. 季節のトレンドカラー（現在は{season}）
3. 海外（特にアメリカ・ヨーロッパ・韓国）のネイルトレンド
4. 日本国内のネイルサロンで人気のスタイル
5. SNSで話題のネイルデザイン

収集した情報を上記のJSON形式でまとめてください。
最低5つ以上のトレンドを調査してください。"""


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
    prompt = RESEARCH_PROMPT.format(season=season)

    print("🔍 リサーチエージェント起動中...")
    print(f"📅 調査日: {datetime.now().strftime('%Y年%m月%d日')} ({season})")
    print("-" * 50)

    result_text = ""

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["WebSearch", "WebFetch"],
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            max_turns=20,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
            print("✅ リサーチ完了")
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text:
                    print(f"  {block.text[:100]}..." if len(block.text) > 100 else f"  {block.text}")

    # JSONを抽出
    try:
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = result_text[start:end]
            research_data = json.loads(json_str)
        else:
            # JSON形式でなければテキストとしてラップ
            research_data = {
                "research_date": datetime.now().strftime("%Y-%m-%d"),
                "raw_text": result_text,
                "trends": [],
                "hot_colors": [],
                "hot_techniques": [],
                "summary_for_next_agent": result_text,
            }
    except json.JSONDecodeError:
        research_data = {
            "research_date": datetime.now().strftime("%Y-%m-%d"),
            "raw_text": result_text,
            "trends": [],
            "hot_colors": [],
            "hot_techniques": [],
            "summary_for_next_agent": result_text,
        }

    return research_data


if __name__ == "__main__":
    result = anyio.run(run_research_agent)
    print("\n📊 リサーチ結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
