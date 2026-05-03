# Entities

DynamoDB シングルテーブル `expense-tracker` には 6種類の論理エンティティが SK prefix で
区別されて格納される。すべてのアイテムは `pk = USER#{cognito_sub}` を持ち、ユーザーごとに
完全分離される (マルチテナント境界は PK)。

## 一覧

| Entity | SK pattern | Pydantic class | Source |
|---|---|---|---|
| User | (暗黙的、PK のみ) | - | `api/auth.py` (Cognito sub) |
| Expense | `EXP#{ISO8601}#{ulid}` | [`Expense`](../api/models/schemas.py#L6) | [`put_expense`](../api/store/dynamodb.py#L35) |
| Receipt | `RCV#{receipt_id}` | (dict) | [`put_receipt`](../api/store/dynamodb.py#L129) |
| Category | `CAT#{name}` | [`Category`](../api/models/schemas.py#L30) | [`put_category`](../api/store/dynamodb.py#L161) |
| Budget | `BDG#{YYYY-MM}#{category}` | [`Budget`](../api/models/schemas.py#L37) | [`put_budget`](../api/store/dynamodb.py#L199) |
| MonthlySummary | `SUM#{YYYY-MM}` | [`MonthlySummary`](../api/models/schemas.py#L47) | [`update_monthly_summary`](../api/store/dynamodb.py#L219) |

---

## Expense

ユーザーの個別の支出レコード。

- **PK**: `USER#{cognito_sub}`
- **SK**: `EXP#{created_at_iso8601}#{ulid_id}`
  - 例: `EXP#2026-05-03T01:23:45.678+00:00#01HXYZABCDEF...`
  - 設計意図: 月別クエリで `begins_with(EXP#YYYY-MM)` が効く + 同月内は降順スキャンで時系列逆順

| Field | Type | Source |
|---|---|---|
| `id` | str (ULID) | [schemas.py:7](../api/models/schemas.py#L7) |
| `amount` | int (円) | [schemas.py:8](../api/models/schemas.py#L8) |
| `category` | str (Category.name) | [schemas.py:9](../api/models/schemas.py#L9) |
| `store_name` | str (default `""`) | [schemas.py:10](../api/models/schemas.py#L10) |
| `memo` | str (default `""`) | [schemas.py:11](../api/models/schemas.py#L11) |
| `receipt_id` | str \| None | [schemas.py:12](../api/models/schemas.py#L12) |
| `created_at` | str (ISO8601) | [schemas.py:13](../api/models/schemas.py#L13) |

サンプル:
```json
{
  "pk": "USER#abc-123",
  "sk": "EXP#2026-05-03T01:23:45.678+00:00#01HXYZABCDEF",
  "id": "01HXYZABCDEF",
  "amount": 1200,
  "category": "food",
  "store_name": "セブンイレブン",
  "memo": "",
  "receipt_id": null,
  "created_at": "2026-05-03T01:23:45.678+00:00"
}
```

---

## Receipt

レシート画像のメタ情報。S3 の実画像と Textract OCR 結果のステータスを保持。

- **PK**: `USER#{cognito_sub}`
- **SK**: `RCV#{receipt_id}`

| Field | Type | Source |
|---|---|---|
| `id` | str | [dynamodb.py:134](../api/store/dynamodb.py#L134) |
| `s3_key` | str (S3 オブジェクトキー) | [dynamodb.py:135](../api/store/dynamodb.py#L135) |
| `filename` | str | [dynamodb.py:136](../api/store/dynamodb.py#L136) |
| `status` | str (`processing` \| `complete`) | [dynamodb.py:137](../api/store/dynamodb.py#L137) |
| `created_at` | str (ISO8601) | [dynamodb.py:138](../api/store/dynamodb.py#L138) |

Pydantic model は無く、`dict[str, Any]` で扱われる (`get_receipt` / `put_receipt` 参照)。

---

## Category

ユーザーごとの支出カテゴリ。デフォルトは [`init_default_categories`](../api/store/dynamodb.py#L171) で
10種類が初期投入される (food, transport, daily, entertainment, utility, telecom, medical, clothing, education, other)。

- **PK**: `USER#{cognito_sub}`
- **SK**: `CAT#{name}`
  - `name` はカテゴリ識別子 (英語キー、`food` 等)

| Field | Type | Source |
|---|---|---|
| `name` | str (識別子) | [schemas.py:31](../api/models/schemas.py#L31) |
| `display_name` | str (UI 表示名、日本語) | [schemas.py:32](../api/models/schemas.py#L32) |
| `icon` | str (default `"tag"`) | [schemas.py:33](../api/models/schemas.py#L33) |
| `sort_order` | int (default `0`) | [schemas.py:34](../api/models/schemas.py#L34) |

---

## Budget

月別 × カテゴリ別の予算上限。

- **PK**: `USER#{cognito_sub}`
- **SK**: `BDG#{YYYY-MM}#{category}`
  - 例: `BDG#2026-05#food`
  - 設計意図: 月指定で `begins_with(BDG#2026-05)` で全カテゴリ取得

| Field | Type | Source |
|---|---|---|
| `category` | str (Category.name) | [schemas.py:38](../api/models/schemas.py#L38) |
| `amount` | int (円) | [schemas.py:39](../api/models/schemas.py#L39) |
| `alert_threshold_pct` | int (default `80`) | [schemas.py:40](../api/models/schemas.py#L40) |
| `month` | str (`YYYY-MM`、SK と冗長) | [dynamodb.py:204](../api/store/dynamodb.py#L204) |

`month` 属性は SK と冗長だが、`get_budgets` で SK を除外しても `month` が読める利便のため
重複して持つ ([dynamodb.py:195](../api/store/dynamodb.py#L195) で `pk` `sk` `month` を除外している)。

---

## MonthlySummary

月次集計。`update_monthly_summary` で支出登録のたびに加算される。

- **PK**: `USER#{cognito_sub}`
- **SK**: `SUM#{YYYY-MM}`
  - 1ユーザー1月1アイテム

| Field | Type | Source |
|---|---|---|
| `month` | str (`YYYY-MM`) | [schemas.py:48](../api/models/schemas.py#L48) |
| `total` | int (円、月内合計) | [schemas.py:49](../api/models/schemas.py#L49) |
| `by_category` | `dict[str, int]` (カテゴリ別合計) | [schemas.py:50](../api/models/schemas.py#L50) |
| `expense_count` | int (件数) | [schemas.py:51](../api/models/schemas.py#L51) |

サンプル:
```json
{
  "pk": "USER#abc-123",
  "sk": "SUM#2026-05",
  "month": "2026-05",
  "total": 45200,
  "by_category": {"food": 28000, "transport": 12000, "daily": 5200},
  "expense_count": 17
}
```

更新は `UpdateExpression` の `if_not_exists` で原子的に加算 ([dynamodb.py:226-247](../api/store/dynamodb.py#L226))。
`by_category` map がまだ存在しない初回は `update_item` が `ClientError` を投げるので
`put_item` でフォールバック ([dynamodb.py:248-259](../api/store/dynamodb.py#L248))。
