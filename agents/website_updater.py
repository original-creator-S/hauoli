"""
ウェブサイト更新エージェント
要約レポートをPythonテンプレートで美しいHTMLページにレンダリングして保存する
（Step 1/2 はAIエージェント、Step 3 は高品質なPythonテンプレートレンダリング）
"""

import json
import os
from datetime import datetime

OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trends.html"))

# ─── ヘルパー ────────────────────────────────────────────────

def _color_hex(name: str) -> str:
    color_map = {
        "テラコッタ": "#c8715a", "ミルキーホワイト": "#f5f2ee", "モーヴ": "#b8a0a8",
        "ヌード": "#d4b89a", "ベージュ": "#d4b896", "ピンク": "#f0a0b0",
        "レッド": "#c0392b", "コーラル": "#f08070", "オレンジ": "#e87040",
        "イエロー": "#f0d060", "グリーン": "#78a870", "ブルー": "#6090c0",
        "パープル": "#9060a0", "ホワイト": "#f8f8f8", "ブラック": "#303030",
        "シルバー": "#c0c0c0", "ゴールド": "#d4af37", "ブラウン": "#8b6553",
        "グレー": "#909090", "ラベンダー": "#c8b0d8", "ミント": "#98d8c8",
        "スカイブルー": "#88c8e8", "バーガンディ": "#800020", "ネイビー": "#203060",
        "モカ": "#967259", "ローズ": "#d08898", "チョコ": "#7b3f1e",
        "サーモン": "#fa8072", "マスタード": "#e1ad21", "カーキ": "#8b8048",
    }
    for key, val in color_map.items():
        if key in name:
            return val
    return "#d4af37"


def _difficulty_badge(difficulty: str) -> str:
    d = str(difficulty).lower()
    if d in ("easy", "簡単"):
        return '<span style="font-size:10px;font-family:Montserrat,sans-serif;font-weight:500;background:#d4edda;color:#2d6a4f;padding:3px 10px;border-radius:100px;">Easy</span>'
    if d in ("medium", "普通"):
        return '<span style="font-size:10px;font-family:Montserrat,sans-serif;font-weight:500;background:#fff3cd;color:#856404;padding:3px 10px;border-radius:100px;">Medium</span>'
    if d in ("hard", "難しい"):
        return '<span style="font-size:10px;font-family:Montserrat,sans-serif;font-weight:500;background:#f8d7da;color:#842029;padding:3px 10px;border-radius:100px;">Hard</span>'
    return f'<span style="font-size:10px;background:#eee;color:#666;padding:3px 10px;border-radius:100px;">{difficulty}</span>'


def _esc(text: str) -> str:
    """Simple HTML escape"""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _tags(items: list) -> str:
    return "".join(
        f'<span style="font-size:11px;font-family:Montserrat,sans-serif;background:#f5f0e8;color:#8a7a6a;padding:4px 10px;border-radius:100px;border:1px solid #e8e2d8;display:inline-block;margin:3px 3px 0 0;">{_esc(t)}</span>'
        for t in items
    )


def _action_items(items: list) -> str:
    lis = "".join(
        f'<li style="font-size:13px;padding:4px 0 4px 20px;position:relative;color:#4a4643;">'
        f'<span style="position:absolute;left:0;color:#d4af37;font-weight:bold;">→</span>{_esc(a)}</li>'
        for a in items
    )
    return f'<ul style="list-style:none;padding:0;margin:0 0 12px;">{lis}</ul>'


def _color_swatches(colors: list, hexes: list) -> str:
    pairs = [(c, _color_hex(c)) for c in colors]
    # Use provided hexes if available
    if hexes:
        pairs = [(h.get("name", ""), h.get("hex", _color_hex(h.get("name", "")))) for h in hexes]
    items = "".join(
        f'<div style="text-align:center;margin-right:12px;margin-bottom:12px;">'
        f'<div style="width:52px;height:52px;border-radius:50%;background:{hex_};margin:0 auto 6px;border:2px solid rgba(255,255,255,0.8);box-shadow:0 2px 8px rgba(0,0,0,0.12);"></div>'
        f'<span style="font-size:10px;font-family:Montserrat,sans-serif;color:#999;white-space:nowrap;">{_esc(name)}</span>'
        f'</div>'
        for name, hex_ in pairs
    )
    return f'<div style="display:flex;flex-wrap:wrap;">{items}</div>'


def _trend_card(trend: dict) -> str:
    rank = trend.get("rank", "")
    title = _esc(trend.get("title", ""))
    why = _esc(trend.get("why_important", ""))
    actions = _action_items(trend.get("action_items", []))
    hashtags = _tags(trend.get("sns_hashtags", []))
    diff = _difficulty_badge(trend.get("difficulty", ""))
    impact = _esc(trend.get("estimated_impact", ""))

    return f"""
<div style="background:white;border:1px solid #e8e2d8;border-radius:12px;padding:24px;
            display:grid;grid-template-columns:48px 1fr;gap:16px;margin-bottom:16px;
            transition:box-shadow 0.2s;box-shadow:0 1px 4px rgba(74,70,67,0.06);">
  <div style="width:48px;height:48px;background:#d4af37;color:white;border-radius:50%;
              display:flex;align-items:center;justify-content:center;
              font-family:'Cormorant Garamond',serif;font-size:22px;font-weight:600;flex-shrink:0;">{rank}</div>
  <div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap;">
      <h3 style="font-size:17px;font-weight:700;margin:0;color:#4a4643;">{title}</h3>
      {diff}
    </div>
    <p style="font-size:13px;color:#888;margin:0 0 14px;line-height:1.6;">{why}</p>
    {actions}
    {f'<p style="font-size:12px;color:#aaa;margin:0 0 10px;">📈 {impact}</p>' if impact else ''}
    <div>{hashtags}</div>
  </div>
</div>"""


def _menu_card(menu: dict) -> str:
    name = _esc(menu.get("menu_name", ""))
    desc = _esc(menu.get("description", ""))
    price = _esc(menu.get("suggested_price", ""))
    target = _esc(menu.get("target_customer", ""))
    return f"""
<div style="background:white;border:1px solid #e8e2d8;border-radius:12px;overflow:hidden;min-width:200px;">
  <div style="background:linear-gradient(135deg,#f5f0e8 0%,#ede8df 100%);padding:20px 20px 16px;border-bottom:1px solid #e8e2d8;">
    <h3 style="font-family:'Cormorant Garamond',serif;font-size:18px;font-weight:600;margin:0 0 4px;color:#4a4643;">{name}</h3>
    <span style="font-family:Montserrat,sans-serif;font-size:13px;color:#d4af37;font-weight:500;">{price}</span>
  </div>
  <div style="padding:16px 20px;">
    <p style="font-size:13px;color:#888;line-height:1.7;margin:0 0 10px;">{desc}</p>
    <span style="font-size:11px;font-family:Montserrat,sans-serif;background:#f5f0e8;color:#8a7a6a;padding:4px 10px;border-radius:100px;">{target}</span>
  </div>
</div>"""


def _idea_cards(ideas: list) -> str:
    return "".join(
        f'<div style="background:white;border:1px solid #e8e2d8;border-radius:10px;padding:16px;font-size:13px;line-height:1.7;color:#4a4643;">{_esc(idea)}</div>'
        for idea in ideas
    )


# ─── メインレンダラー ─────────────────────────────────────────

def render_html(data: dict) -> str:
    report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt = datetime.strptime(report_date, "%Y-%m-%d")
        display_date = dt.strftime("%Y年%m月%d日")
    except Exception:
        display_date = report_date

    title = _esc(data.get("report_title", "週次ネイルトレンドレポート"))
    summary = _esc(data.get("executive_summary", ""))

    # トレンドカード
    trends_html = "".join(_trend_card(t) for t in data.get("priority_trends", []))

    # カラーパレット
    cp = data.get("color_palette", {})
    swatches = _color_swatches(cp.get("trending_colors", []), cp.get("color_hexes", []))
    color_story = _esc(cp.get("color_story", ""))
    combos = _tags(cp.get("recommended_combinations", []))

    # テクニックスポットライト
    ts = data.get("technique_spotlight", {})
    technique = _esc(ts.get("featured_technique", ""))
    tech_desc = _esc(ts.get("description", ""))
    tech_resource = _esc(ts.get("learning_resources", ""))

    # SNSヒント
    smt = data.get("social_media_tips", {})
    ideas_html = _idea_cards(smt.get("content_ideas", []))
    post_time = _esc(smt.get("best_posting_times", ""))
    eng_tips = _esc(smt.get("engagement_tips", ""))

    # メニュー
    menus_html = "".join(_menu_card(m) for m in data.get("menu_suggestions", []))

    # 来週の予告
    preview = _esc(data.get("next_week_preview", ""))

    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | PRIVATE NAIL SALON hauoli</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@300;400;500;700&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@200;300;400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Zen Kaku Gothic New', sans-serif; background: #fcfbf9; color: #4a4643; margin: 0; -webkit-font-smoothing: antialiased; }}
        .serif {{ font-family: 'Cormorant Garamond', serif; }}
        .brand {{ font-family: 'Montserrat', sans-serif; }}
        .section {{ max-width: 900px; margin: 0 auto; padding: 48px 20px 32px; border-bottom: 1px solid #e8e2d8; }}
        .section:last-of-type {{ border-bottom: none; }}
        .section-label {{ font-family: Montserrat, sans-serif; font-size: 9px; font-weight: 500; letter-spacing: 0.45em; color: #d4af37; text-transform: uppercase; margin-bottom: 8px; }}
        .section-title {{ font-family: 'Cormorant Garamond', serif; font-size: clamp(22px, 4vw, 30px); font-weight: 600; color: #4a4643; margin: 0 0 24px; line-height: 1.3; }}
        @media (max-width: 640px) {{
            .trend-grid-col {{ grid-template-columns: 36px 1fr !important; }}
            .info-grid {{ grid-template-columns: 1fr !important; }}
            .menu-grid {{ grid-template-columns: 1fr !important; }}
        }}
    </style>
</head>
<body>

<!-- ─ Header ─ -->
<header style="background:#4a4643;padding:18px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50;">
    <div>
        <div class="brand" style="font-weight:200;font-size:18px;letter-spacing:0.35em;color:#d4af37;text-transform:uppercase;">hauoli</div>
        <div class="brand" style="font-size:9px;letter-spacing:0.15em;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-top:2px;">Private Nail Salon</div>
    </div>
    <a href="index.html" style="font-family:Montserrat,sans-serif;font-size:10px;font-weight:400;letter-spacing:0.15em;color:rgba(255,255,255,0.6);text-decoration:none;text-transform:uppercase;border:1px solid rgba(255,255,255,0.2);padding:7px 16px;border-radius:100px;">← パーソナルカラー診断</a>
</header>

<!-- ─ Hero ─ -->
<section style="background:linear-gradient(135deg,#4a4643 0%,#2d2a28 60%,#3d3530 100%);color:white;text-align:center;padding:64px 24px 56px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(ellipse at 60% 40%,rgba(212,175,55,0.12) 0%,transparent 60%);pointer-events:none;"></div>
    <div class="brand" style="font-size:10px;font-weight:400;letter-spacing:0.4em;color:#d4af37;text-transform:uppercase;margin-bottom:16px;">Weekly Nail Trend Report</div>
    <h1 class="serif" style="font-size:clamp(30px,5vw,48px);font-weight:400;line-height:1.2;margin:0 0 12px;color:white;">{title}</h1>
    <p class="brand" style="font-size:11px;font-weight:300;letter-spacing:0.25em;color:rgba(255,255,255,0.5);text-transform:uppercase;margin:0 0 32px;">Curated for Nail Salon Owners</p>
    <span class="brand" style="display:inline-block;font-size:11px;font-weight:400;letter-spacing:0.15em;color:#d4af37;border:1px solid rgba(212,175,55,0.4);padding:8px 20px;border-radius:100px;">{display_date}</span>
</section>

<!-- ─ Executive Summary ─ -->
<div class="section">
    <p class="section-label">Executive Summary</p>
    <h2 class="section-title">今週のハイライト</h2>
    <div style="background:#f5f0e8;border-left:3px solid #d4af37;border-radius:0 8px 8px 0;padding:24px 28px;font-size:15px;line-height:1.9;color:#4a4643;white-space:pre-wrap;">{summary}</div>
</div>

<!-- ─ Priority Trends ─ -->
<div class="section">
    <p class="section-label">Priority Trends</p>
    <h2 class="section-title">注目トレンドランキング</h2>
    {trends_html if trends_html else '<p style="color:#aaa;font-size:14px;">データなし</p>'}
</div>

<!-- ─ Color Palette ─ -->
<div class="section">
    <p class="section-label">Color Palette</p>
    <h2 class="section-title">今週のカラーパレット</h2>
    {swatches}
    <div style="background:#f5f0e8;border-radius:8px;padding:16px 20px;font-size:14px;line-height:1.8;color:#6a6360;margin:16px 0;">{color_story}</div>
    <p class="brand" style="font-size:10px;letter-spacing:0.3em;color:#d4af37;text-transform:uppercase;margin:0 0 8px;">おすすめの組み合わせ</p>
    <div>{combos}</div>
</div>

<!-- ─ Technique Spotlight ─ -->
<div class="section">
    <p class="section-label">Technique Spotlight</p>
    <h2 class="section-title">今週の注目テクニック</h2>
    <div style="background:linear-gradient(135deg,#4a4643 0%,#3d3530 100%);color:white;border-radius:16px;padding:32px;">
        <p class="brand" style="font-size:9px;letter-spacing:0.4em;color:#d4af37;text-transform:uppercase;margin-bottom:12px;">Featured Technique</p>
        <h3 class="serif" style="font-size:28px;font-weight:400;margin:0 0 12px;">{technique}</h3>
        <p style="font-size:14px;line-height:1.8;color:rgba(255,255,255,0.75);margin:0 0 16px;">{tech_desc}</p>
        {f'<p style="font-size:13px;color:#e8d07a;border-top:1px solid rgba(255,255,255,0.15);padding-top:16px;margin:0;">💡 {tech_resource}</p>' if tech_resource else ''}
    </div>
</div>

<!-- ─ SNS Tips ─ -->
<div class="section">
    <p class="section-label">Social Media Guide</p>
    <h2 class="section-title">SNS活用ガイド</h2>
    <p class="brand" style="font-size:10px;letter-spacing:0.3em;color:#d4af37;text-transform:uppercase;margin-bottom:12px;">投稿アイデア</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:20px;" class="idea-grid">
        {ideas_html}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="info-grid">
        <div style="background:#f5f0e8;border-radius:10px;padding:16px 18px;">
            <p class="brand" style="font-size:9px;font-weight:500;letter-spacing:0.3em;color:#d4af37;text-transform:uppercase;margin:0 0 8px;">最適な投稿時間</p>
            <p style="font-size:13px;color:#4a4643;line-height:1.7;margin:0;">⏰ {post_time}</p>
        </div>
        <div style="background:#f5f0e8;border-radius:10px;padding:16px 18px;">
            <p class="brand" style="font-size:9px;font-weight:500;letter-spacing:0.3em;color:#d4af37;text-transform:uppercase;margin:0 0 8px;">エンゲージメントのコツ</p>
            <p style="font-size:13px;color:#4a4643;line-height:1.7;margin:0;">✨ {eng_tips}</p>
        </div>
    </div>
</div>

<!-- ─ Menu Suggestions ─ -->
<div class="section">
    <p class="section-label">Menu Suggestions</p>
    <h2 class="section-title">新メニュー提案</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;" class="menu-grid">
        {menus_html if menus_html else '<p style="color:#aaa;font-size:14px;">データなし</p>'}
    </div>
</div>

<!-- ─ Next Week Preview ─ -->
<div class="section">
    <p class="section-label">Coming Next Week</p>
    <h2 class="section-title">来週の予告</h2>
    <div style="background:#f5f0e8;border-radius:12px;padding:28px;border:1px solid #e8e2d8;display:flex;gap:20px;align-items:flex-start;">
        <span style="font-size:28px;flex-shrink:0;">🔭</span>
        <div>
            <h3 class="serif" style="font-size:20px;margin:0 0 8px;">次回リサーチテーマ</h3>
            <p style="font-size:14px;color:#888;line-height:1.8;margin:0;">{preview}</p>
        </div>
    </div>
</div>

<!-- ─ Footer ─ -->
<footer style="background:#4a4643;color:rgba(255,255,255,0.45);text-align:center;padding:36px 24px;">
    <p class="brand" style="font-weight:200;font-size:16px;letter-spacing:0.4em;color:#d4af37;text-transform:uppercase;margin:0 0 6px;">hauoli</p>
    <p style="font-size:11px;margin:0 0 8px;letter-spacing:0.05em;">PRIVATE NAIL SALON &nbsp;|&nbsp; Weekly Nail Trend Report</p>
    <p style="font-size:10px;margin:0;">最終更新: {now_str} &nbsp;|&nbsp; <a href="index.html" style="color:rgba(255,255,255,0.4);text-decoration:none;">パーソナルカラー診断へ</a></p>
</footer>

</body>
</html>"""


# ─── エントリポイント ─────────────────────────────────────────

async def run_website_updater_agent(summary_data: dict, output_path: str = OUTPUT_PATH) -> str:
    """レポートデータをHTMLに変換してファイルに保存する（同期処理）"""
    print("\n🎨 ウェブサイト更新エージェント起動中...")
    print("-" * 50)

    html = render_html(summary_data)
    abs_path = os.path.abspath(output_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ HTML生成完了")
    print(f"💾 保存先: {abs_path}")
    return abs_path


if __name__ == "__main__":
    import anyio

    sample = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "report_title": "週次ネイルトレンドレポート",
        "executive_summary": "今週はオーロラネイルとテラコッタカラーが引き続き人気。韓国発グラスネイルも注目度急上昇。",
        "priority_trends": [
            {"rank": 1, "title": "オーロラネイル", "why_important": "SNSでバイラル中。集客力No.1のデザイン",
             "action_items": ["オーロラパウダーを仕入れる", "見本を作りSNSに投稿する"],
             "sns_hashtags": ["#オーロラネイル", "#auroranails", "#春ネイル"],
             "difficulty": "medium", "estimated_impact": "新規客30%増の見込み"},
            {"rank": 2, "title": "テラコッタカラー", "why_important": "秋冬定番。今季特に需要が高い",
             "action_items": ["テラコッタ系カラーを充実させる", "アースカラーコーデ投稿"],
             "sns_hashtags": ["#テラコッタネイル", "#アースカラー"],
             "difficulty": "easy", "estimated_impact": "既存客のリピート率向上"},
        ],
        "color_palette": {
            "trending_colors": ["テラコッタ", "ミルキーホワイト", "モーヴ"],
            "color_story": "秋に向けてアースカラーが主流に。温かみのある色合いがトレンドです。",
            "recommended_combinations": ["テラコッタ×ゴールド", "モーヴ×ホワイト"],
        },
        "technique_spotlight": {
            "featured_technique": "グラスネイル",
            "description": "韓国発のトレンド。透明感のあるカラーホイルをジェルに封入することで、ガラスのような輝きを演出する技法。",
            "learning_resources": "YouTubeで「glass nail tutorial 2024」と検索。インスタのタグ #글라스네일 も参考に。",
        },
        "social_media_tips": {
            "content_ideas": ["before/afterリール動画（施術前後比較）", "カラーチップ並べて比較投稿", "「今月のネイル選び」Stories投票"],
            "best_posting_times": "平日12時台・19〜21時台が効果的",
            "engagement_tips": "ネイルチップのくるくる動画（ショートリール）がバズりやすい",
        },
        "menu_suggestions": [
            {"menu_name": "オーロラアート追加", "description": "既存デザインにオーロラ効果をプラス", "suggested_price": "+¥1,000〜¥1,500", "target_customer": "20〜30代トレンド志向の方"},
            {"menu_name": "秋アースカラーセット", "description": "テラコッタ×モーヴの秋パレットコース", "suggested_price": "¥7,000〜¥8,500", "target_customer": "シックなデザイン好きの方"},
        ],
        "next_week_preview": "クリスマスネイルのトレンドを先取りリサーチ予定。欧米発の最新デザインにも注目します。",
    }

    result = anyio.run(run_website_updater_agent, sample)
    print(f"✨ 完了: {result}")
    print(f"   ファイルサイズ: {os.path.getsize(result):,} bytes")
