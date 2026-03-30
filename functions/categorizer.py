"""Categorize expense based on store name using rule-based mapping."""

from __future__ import annotations

# Store name patterns → category mapping
CATEGORY_RULES: list[tuple[list[str], str]] = [
    # 食費
    (["セブン", "ローソン", "ファミマ", "ファミリーマート", "マクドナルド", "すき家",
      "松屋", "吉野家", "スタバ", "スターバックス", "イオン", "西友", "マルエツ",
      "ライフ", "OK", "業務スーパー", "コストコ", "成城石井", "デニーズ",
      "ガスト", "サイゼリヤ", "CoCo壱", "丸亀", "モス", "ケンタッキー", "KFC",
      "ピザ", "寿司", "弁当", "食堂", "レストラン", "カフェ", "ベーカリー"], "food"),
    # 交通費
    (["JR", "メトロ", "地下鉄", "バス", "タクシー", "Suica", "PASMO",
      "定期", "新幹線", "航空", "ANA", "JAL", "Uber"], "transport"),
    # 日用品
    (["ドラッグ", "マツキヨ", "ウエルシア", "ダイソー", "セリア", "無印",
      "ニトリ", "ホームセンター", "カインズ", "コーナン"], "daily"),
    # 娯楽
    (["映画", "シネマ", "カラオケ", "ゲーム", "Netflix", "Spotify",
      "Amazon Prime", "Disney", "書店", "本屋", "紀伊國屋"], "entertainment"),
    # 光熱費
    (["電力", "ガス", "水道", "東京電力", "東京ガス", "TEPCO", "関西電力"], "utility"),
    # 通信費
    (["ドコモ", "au", "ソフトバンク", "楽天モバイル", "UQ", "NTT",
      "プロバイダ", "Wi-Fi"], "telecom"),
    # 医療費
    (["病院", "クリニック", "薬局", "調剤", "歯科", "眼科", "内科"], "medical"),
    # 衣服
    (["ユニクロ", "GU", "ZARA", "H&M", "しまむら", "ABCマート"], "clothing"),
    # 教育
    (["書籍", "Udemy", "学校", "塾", "教材", "セミナー"], "education"),
]


def _categorize(store_name: str) -> str:
    name_lower = store_name.lower()
    for patterns, category in CATEGORY_RULES:
        for pattern in patterns:
            if pattern.lower() in name_lower:
                return category
    return "other"


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    receipt_id = event["receipt_id"]
    user_id = event["user_id"]
    extracted = event["extracted"]
    store_name = extracted.get("store_name", "")

    category = _categorize(store_name)

    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "extracted": extracted,
        "category": category,
    }
