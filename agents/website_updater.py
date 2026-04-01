"""
ウェブサイト更新エージェント
まとめられたトレンドレポートを美しいHTMLページとして出力するエージェント
"""

import anyio
import json
import os
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# trends.html の出力先パス（このファイルから2階層上）
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "trends.html")

WEBSITE_SYSTEM_PROMPT = """あなたはネイルサロン向けウェブデザイナー兼フロントエンドエンジニアです。
美しく洗練されたHTMLページを生成するのが専門です。

デザイン原則:
- ネイルサロン「hauoli」のブランドカラー（ゴールド #d4af37、クリーム #fcfbf9、茶色 #4a4643）を使用
- エレガントで女性らしいデザイン
- モバイルファースト・レスポンシブデザイン
- 日本語フォント: 'Zen Kaku Gothic New'（本文）、'Cormorant Garamond'（装飾）、'Montserrat'（ブランド名）
- Google Fontsを使用
- Tailwind CSSを使用
- アニメーションや視覚的なアクセントで読みやすさを高める
- 各セクションは明確に区分けし、スキャンしやすいレイアウトにする

必ず完全なHTMLファイル（<!DOCTYPE html>から</html>まで）を生成してください。
外部CDNのみ使用し、インラインCSS/JSで完結させてください。"""

WEBSITE_PROMPT_TEMPLATE = """以下のネイルトレンドレポートデータを元に、美しいHTMLページを生成してください。

【レポートデータ】
{summary_json}

HTMLページの要件:
1. **ヘッダー**: hauoliのロゴ（テキスト）、レポートタイトル、日付
2. **エグゼクティブサマリー**: 今週のハイライトを目立つデザインで表示
3. **注目トレンドランキング**: カード形式で各トレンドを表示（アクションアイテム付き）
4. **カラーパレット**: 今週のおすすめカラーを視覚的に（カラーボックス付き）
5. **注目テクニック**: 習得すべき技法のスポットライトセクション
6. **SNS活用ガイド**: 投稿アイデアをコピーしやすい形式で表示
7. **新メニュー提案**: メニューカードのデザインで表示
8. **来週の予告**: 次回に向けた情報
9. **フッター**: hauoli、更新日時

デザインの細部:
- 難易度は色付きバッジで表示（easy=緑、medium=黄、hard=赤）
- ランキングは数字バッジで強調
- カラースウォッチは実際の色で塗りつぶした丸で表示（予測される色名から）
- ハッシュタグはクリックしやすいタグ形式
- 全体的に上品でラグジュアリーな雰囲気

完全なHTMLファイルのみを出力してください（説明文は不要）。"""


def extract_color_hex(color_name: str) -> str:
    """色名から近似的なHEXカラーコードを返す（簡易マッピング）"""
    color_map = {
        "テラコッタ": "#c8715a",
        "ミルキーホワイト": "#f5f2ee",
        "モーヴ": "#b8a0a8",
        "ヌード": "#d4b89a",
        "ベージュ": "#d4b896",
        "ピンク": "#f0a0b0",
        "レッド": "#c0392b",
        "コーラル": "#f08070",
        "オレンジ": "#e87040",
        "イエロー": "#f0d060",
        "グリーン": "#78a870",
        "ブルー": "#6090c0",
        "パープル": "#9060a0",
        "ホワイト": "#f8f8f8",
        "ブラック": "#303030",
        "シルバー": "#c0c0c0",
        "ゴールド": "#d4af37",
        "ブラウン": "#8b6553",
        "グレー": "#909090",
        "ラベンダー": "#c8b0d8",
        "ミント": "#98d8c8",
        "スカイブルー": "#88c8e8",
        "バーガンディ": "#800020",
        "ネイビー": "#203060",
        "モカ": "#967259",
        "チェリー": "#c0304050",
        "ローズ": "#d08898",
    }
    for key, val in color_map.items():
        if key in color_name:
            return val
    return "#d4af37"  # デフォルトはゴールド


async def run_website_updater_agent(summary_data: dict, output_path: str = OUTPUT_PATH) -> str:
    """レポートデータを美しいHTMLに変換してファイルに保存する"""
    print("\n🎨 ウェブサイト更新エージェント起動中...")
    print("-" * 50)

    # カラー情報を補完
    if "color_palette" in summary_data:
        colors = summary_data["color_palette"].get("trending_colors", [])
        summary_data["color_palette"]["color_hexes"] = [
            {"name": c, "hex": extract_color_hex(c)} for c in colors
        ]

    summary_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
    prompt = WEBSITE_PROMPT_TEMPLATE.format(summary_json=summary_json)

    result_text = ""

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=[],
            system_prompt=WEBSITE_SYSTEM_PROMPT,
            max_turns=5,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
            print("✅ HTML生成完了")

    # HTMLを抽出して保存
    html_content = _extract_html(result_text)

    abs_output_path = os.path.abspath(output_path)
    with open(abs_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"💾 保存先: {abs_output_path}")
    return abs_output_path


def _extract_html(text: str) -> str:
    """テキストからHTMLを抽出する"""
    # コードブロックから抽出
    if "```html" in text:
        start = text.find("```html") + 7
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            candidate = text[start:end].strip()
            if "<!DOCTYPE" in candidate or "<html" in candidate:
                return candidate

    # DOCTYPE / html タグを探す
    for marker in ["<!DOCTYPE html>", "<!DOCTYPE HTML>", "<html"]:
        idx = text.find(marker)
        if idx != -1:
            # </html> まで
            end_idx = text.rfind("</html>")
            if end_idx > idx:
                return text[idx : end_idx + 7]
            return text[idx:]

    # フォールバック: エラーページを返す
    return _fallback_html()


def _fallback_html() -> str:
    now = datetime.now().strftime("%Y年%m月%d日")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ネイルトレンドレポート | hauoli</title>
    <link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@300;400;700&family=Cormorant+Garamond:ital,wght@0,400;1,400&family=Montserrat:wght@200;400&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Zen Kaku Gothic New', sans-serif; background: #fcfbf9; color: #4a4643; text-align: center; padding: 60px 20px; }}
        h1 {{ font-family: 'Montserrat', sans-serif; color: #d4af37; font-weight: 200; letter-spacing: 0.2em; }}
        p {{ color: #888; }}
    </style>
</head>
<body>
    <h1>hauoli</h1>
    <h2>Nail Trend Report</h2>
    <p>更新日: {now}</p>
    <p>レポートの生成に問題が発生しました。再度実行してください。</p>
</body>
</html>"""


if __name__ == "__main__":
    # テスト用サンプルデータ
    sample_summary = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "report_title": "週次ネイルトレンドレポート",
        "executive_summary": "今週はオーロラネイルとテラコッタカラーが引き続き人気。韓国発のグラスネイルも注目度上昇中。",
        "priority_trends": [
            {
                "rank": 1,
                "title": "オーロラネイル",
                "why_important": "SNSでバイラル中。集客力No.1のデザイン",
                "action_items": ["オーロラパウダーを仕入れる", "見本を作りSNSに投稿する"],
                "sns_hashtags": ["#オーロラネイル", "#auroranails"],
                "difficulty": "medium",
                "estimated_impact": "新規客獲得30%増の見込み",
            }
        ],
        "color_palette": {
            "trending_colors": ["テラコッタ", "ミルキーホワイト", "モーヴ"],
            "color_story": "秋に向けてアースカラーが主流に",
            "recommended_combinations": ["テラコッタ×ゴールド", "モーヴ×ホワイト"],
        },
        "technique_spotlight": {
            "featured_technique": "グラスネイル",
            "description": "透明感のあるカラーホイルを封入するテクニック",
            "learning_resources": "YouTubeで検索「glass nail tutorial」",
        },
        "social_media_tips": {
            "content_ideas": ["before/afterリール動画", "カラー比較投稿"],
            "best_posting_times": "平日12時・夜20時以降",
            "engagement_tips": "施術中の動画がリールで人気",
        },
        "menu_suggestions": [
            {
                "menu_name": "オーロラアート追加",
                "description": "既存デザインに＋オーロラ効果",
                "suggested_price": "+¥1,000〜1,500",
                "target_customer": "20〜30代トレンド志向の方",
            }
        ],
        "next_week_preview": "クリスマスネイルのトレンドを先取り調査予定",
    }

    result = anyio.run(run_website_updater_agent, sample_summary)
    print(f"\n✨ 生成完了: {result}")
