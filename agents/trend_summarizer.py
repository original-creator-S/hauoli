"""
ネイルトレンド要約エージェント
リサーチ結果をネイルサロン経営者向けに分かりやすくまとめるエージェント
"""

import json
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

SUMMARIZER_SYSTEM_PROMPT = """あなたはネイルサロン経営のコンサルタントです。
ネイリストや美容師の資格を持ち、ネイルサロンの経営・集客・トレンド分析が専門です。

あなたの役割:
- リサーチエージェントが収集したトレンド情報を、サロン経営者の視点で整理する
- 「今すぐ取り入れるべき」「準備しておくべき」など優先度をつける
- 集客・SNS投稿・メニュー開発への活用方法を提案する
- 専門用語は分かりやすく説明し、初心者サロンオーナーでも理解できるようにする

必ず以下のJSON構造のみを出力してください（前後の説明文は不要）:
{
  "report_date": "YYYY-MM-DD",
  "report_title": "週次ネイルトレンドレポート",
  "executive_summary": "1〜2段落の要約",
  "priority_trends": [
    {
      "rank": 1,
      "title": "トレンド名",
      "why_important": "サロン経営者にとってなぜ重要か",
      "action_items": ["具体的なアクション1", "アクション2"],
      "sns_hashtags": ["#ハッシュタグ1", "#ハッシュタグ2"],
      "difficulty": "easy/medium/hard",
      "estimated_impact": "集客効果の見込み"
    }
  ],
  "color_palette": {
    "trending_colors": ["カラー名1", "カラー名2"],
    "color_story": "今季のカラーストーリー説明",
    "recommended_combinations": ["組み合わせ1", "組み合わせ2"]
  },
  "technique_spotlight": {
    "featured_technique": "注目技法",
    "description": "技法の説明",
    "learning_resources": "習得方法のヒント"
  },
  "social_media_tips": {
    "content_ideas": ["投稿アイデア1", "投稿アイデア2"],
    "best_posting_times": "最適な投稿時間帯",
    "engagement_tips": "エンゲージメントを高めるコツ"
  },
  "menu_suggestions": [
    {
      "menu_name": "メニュー名",
      "description": "メニュー説明",
      "suggested_price": "価格帯",
      "target_customer": "ターゲット顧客"
    }
  ],
  "next_week_preview": "来週注目すべきポイント"
}"""


async def run_summarizer_agent(research_data: dict) -> dict:
    """リサーチデータをサロン経営者向けレポートにまとめる"""
    print("\n📝 要約エージェント起動中...")
    print("-" * 50)

    research_json = json.dumps(research_data, ensure_ascii=False, indent=2)
    prompt = f"""以下のネイルトレンドリサーチデータを、ネイルサロン経営者向けの週次レポートにまとめてください。

【リサーチデータ】
{research_json}

要件:
1. サロン経営者が「今すぐ何をすべきか」が明確になるよう優先度をつける
2. 各トレンドについて、具体的なSNS投稿アイデアを提案する
3. 新メニュー開発のヒントを含める
4. 難しい専門用語は避け、分かりやすい言葉で書く
5. JSON形式のみで出力する（前後の説明文は不要）"""

    result_text = ""

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=[],
            system_prompt=SUMMARIZER_SYSTEM_PROMPT,
            max_turns=3,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
            print("✅ 要約完了")

    # JSONを抽出
    try:
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start != -1 and end > start:
            summary_data = json.loads(result_text[start:end])
        else:
            raise ValueError("JSON not found")
    except (json.JSONDecodeError, ValueError):
        summary_data = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_title": "週次ネイルトレンドレポート",
            "executive_summary": result_text,
            "priority_trends": [],
            "color_palette": {"trending_colors": [], "color_story": "", "recommended_combinations": []},
            "technique_spotlight": {"featured_technique": "", "description": "", "learning_resources": ""},
            "social_media_tips": {"content_ideas": [], "best_posting_times": "", "engagement_tips": ""},
            "menu_suggestions": [],
            "next_week_preview": "",
        }

    return summary_data


if __name__ == "__main__":
    import anyio

    sample_research = {
        "research_date": datetime.now().strftime("%Y-%m-%d"),
        "trends": [{"category": "デザイン", "title": "オーロラネイル", "description": "光の当たり方で虹色に変化", "sources": [], "keywords": ["オーロラ"], "relevance_score": 5}],
        "hot_colors": ["テラコッタ", "ミルキーホワイト"],
        "hot_techniques": ["オーロラパウダー"],
        "summary_for_next_agent": "オーロラネイルが今季最大のトレンド",
    }

    result = anyio.run(run_summarizer_agent, sample_research)
    print(json.dumps(result, ensure_ascii=False, indent=2))
