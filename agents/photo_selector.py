"""
ネイル写真選択エージェント
Wikimedia Commons APIでネイルアート写真を検索し、
Claudeが各トレンドのイメージに最も合う3枚を選択する
"""

import json
import subprocess
from pathlib import Path

CACHE_PATH = Path(__file__).parent.parent / ".agent_cache" / "photo_cache.json"
WM_REDIRECT = "https://commons.wikimedia.org/wiki/Special:Redirect/file/"

# 既知の正しいネイルアートファイル名（APIが使えない場合のフォールバック）
# ※ Complex_nail_art.jpg はミニーマウス絵柄のため除外
_KNOWN_NAIL_FILES = [
    # ── 汎用ネイルアート ──────────────────────────────────
    "Nail_art_example,_Nov_2013.jpg",      # クラシックなネイルアート
    "Nail_art_(2).jpg",                     # ネイルアート
    "Nail_art_(3).jpg",                     # ネイルアート
    "Nail_polish_art.jpg",                  # ネイルポリッシュアート
    "Nail_art_in_Mexico_city.jpg",          # メキシコシティのネイルアート
    # ── 技法別 ───────────────────────────────────────────
    "Gel_nail_art.jpg",                     # ジェルネイル（透明感・グラス系に）
    "French_tip_nail_art.jpg",              # フレンチネイル
    "Acryl-for-nail-art-by-diamond-nails.jpg",  # アクリルネイル
    "Swirly_purple_konad_nail_art.jpg",     # パープル系・スタンピング
    "Konad_nail_art.jpg",                   # スタンピングアート
    "Water_marble_nail_art.jpg",            # ウォーターマーブル
    # ── デザイン別 ────────────────────────────────────────
    "Flower_nail_art.jpg",                  # フラワーネイル
    "Galaxies_nail_art.jpg",               # ギャラクシー（オーロラ・ホログラム系に）
    "Pink_nail_art.jpg",                    # ピンクネイル（桜・春系に）
    "Holographic_nail_art.jpg",             # ホログラフィックネイル
    "Chrome_nails.jpg",                     # クロームネイル
    "Ombre_nail_art.jpg",                   # オンブレグラデーション
    "Marble_nail_art.jpg",                  # マーブルネイル
    "Rose_gold_nails.jpg",                  # ローズゴールドネイル
    "Pastel_nail_art.jpg",                  # パステルネイル（春系）
    "Spring_nail_art.jpg",                  # 春ネイル
    "Mint_green_nails.jpg",                 # ミントグリーン
    "Lavender_nails.jpg",                   # ラベンダー
    "Aurora_nails.jpg",                     # オーロラネイル
    "Glass_nails.jpg",                      # グラスネイル
]


def _call_claude(prompt: str, tools: list | None = None, timeout: int = 120) -> str:
    """claude -p サブプロセスを呼び出す"""
    cmd = ["claude", "-p", "--no-session-persistence", "--output-format", "text"]
    if tools:
        cmd += ["--allowedTools"] + tools
    else:
        cmd += ["--allowedTools", ""]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd="/tmp",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude error: {result.stderr[:300]}")
    return result.stdout.strip()


def _fetch_wikimedia_files() -> list:
    """Wikimedia Commons のネイルアートカテゴリからファイル名一覧を取得"""
    prompt = """以下の2つのURLをWebFetchで取得してください。

URL1: https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Nail_art&cmtype=file&cmlimit=50&format=json
URL2: https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Nail_care&cmtype=file&cmlimit=30&format=json

取得したJSONのquery.categorymembersの各要素から"title"フィールドを取り出し、
"File:"プレフィックスを除いたファイル名のみを全て集めてください。

必ずJSON形式だけで出力してください（説明文は不要）:
{"files": ["ファイル名1", "ファイル名2", ...]}"""

    raw = _call_claude(prompt, tools=["WebFetch"], timeout=90)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    data = json.loads(raw[start:end])
    return data.get("files", [])


def _select_photos_for_trends(trends: list, candidates: list) -> dict:
    """Claudeが各トレンドに合う写真を候補リストから3枚ずつ選ぶ"""
    trends_info = [
        {
            "title": t.get("title", ""),
            "description": t.get("why_important", t.get("description", ""))[:120],
            "keywords": t.get("sns_hashtags", [])[:4],
        }
        for t in trends
    ]

    # 候補が多すぎる場合は絞る
    cand_list = candidates[:100]

    prompt = f"""あなたはプライベートネイルサロン「hauoli」のWebサイト担当です。
各ネイルトレンドに最も合う参考写真を、候補ファイル名リストから3枚ずつ選んでください。

【候補ファイル名リスト】
{json.dumps(cand_list, ensure_ascii=False)}

【各トレンドの情報】
{json.dumps(trends_info, ensure_ascii=False, indent=2)}

■ 選び方のルール（厳守）:
1. ファイル名からネイルの色・デザインを推測して選ぶ
   例: flower→フラワー系、purple/swirly→ラベンダー系、galaxies→オーロラ系
2. 各トレンドの色・イメージに合うファイルを優先する
3. 候補にないファイル名は絶対に使わない（存在しない可能性があるため）
4. 3枚選べない場合は重複使用可
5. 迷ったら「nail」「art」「polish」など汎用系を使う

■ 絶対に選ばないもの:
- キャラクター・アニメ系（mickey, minnie, disney等が名前に含まれるもの）
- 人物・風景・食べ物の写真
- ネイルと無関係なもの

必ずJSON形式だけで出力（余分な説明不要）:
{{
  "トレンドタイトル": ["ファイル名A", "ファイル名B", "ファイル名C"],
  ...
}}"""

    raw = _call_claude(prompt, tools=None, timeout=120)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    return json.loads(raw[start:end])


def run_photo_selector_agent(trends: list) -> dict:
    """
    各トレンドに合ったWikimedia Commons写真URLを選択して返す

    Returns:
        {トレンドタイトル: ["url1", "url2", "url3"], ...}
    """
    print("\n📸 写真選択エージェント起動中...")
    print("-" * 50)

    # Step1: Wikimedia CommonsからAPIでファイル一覧を取得
    print("  📂 Wikimedia Commons API でファイル一覧を取得中...")
    try:
        candidates = _fetch_wikimedia_files()
        print(f"  → {len(candidates)}件の候補ファイルを取得")
    except Exception as e:
        print(f"  ⚠️  API取得失敗 ({e.__class__.__name__}): {e}")
        candidates = []

    # フォールバック: 既知の正しいファイル名を追加
    all_candidates = list(dict.fromkeys(candidates + _KNOWN_NAIL_FILES))
    print(f"  → 合計 {len(all_candidates)}件の候補で選択します")

    # Step2: Claudeが各トレンドに合う3枚を選ぶ
    print("  🤖 Claude がトレンドに合う写真を選択中...")
    try:
        selection = _select_photos_for_trends(trends, all_candidates)
        print(f"  → {len(selection)}件のトレンドの写真を選択完了")
    except Exception as e:
        print(f"  ⚠️  写真選択失敗 ({e.__class__.__name__}): {e}")
        selection = {}

    # Step3: ファイル名 → URL に変換 + フォールバック処理
    result = {}
    fallback_urls = [WM_REDIRECT + fn for fn in _KNOWN_NAIL_FILES[:3]]

    for trend in trends:
        title = trend.get("title", "")
        selected_filenames = selection.get(title, [])

        if len(selected_filenames) >= 3:
            urls = [WM_REDIRECT + fn for fn in selected_filenames[:3]]
        else:
            # 足りない分はフォールバックで補完
            urls = [WM_REDIRECT + fn for fn in selected_filenames] + fallback_urls
            urls = urls[:3]

        result[title] = urls

    # キャッシュに保存
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 写真キャッシュ保存: {CACHE_PATH.name}")
    print("✅ 写真選択完了")
    return result


def load_photo_cache() -> dict:
    """保存済みの写真キャッシュを読み込む（なければ空dict）"""
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}
