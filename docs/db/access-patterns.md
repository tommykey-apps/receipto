# Access Patterns

シングルテーブル設計の本質はアクセスパターン一覧。新クエリを追加するときは PK/SK だけで
解決できるか、フィルタや GSI が必要かを最初に判断する。

## 一覧

| # | Use case | API | PK | SK condition | Filter | Source |
|---|---|---|---|---|---|---|
| 1 | 支出一覧 (全期間) | `GET /api/expenses` | `USER#{u}` | `begins_with(EXP#)` | - | [dynamodb.py:54](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L54) |
| 2 | 支出一覧 (月指定) | `GET /api/expenses?month=YYYY-MM` | `USER#{u}` | `begins_with(EXP#YYYY-MM)` | - | [dynamodb.py:54](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L54) |
| 3 | 支出一覧 (カテゴリ絞り込み) | `GET /api/expenses?category=X` | `USER#{u}` | `begins_with(EXP#)` | post-filter (Python 側) | [dynamodb.py:67](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L67) |
| 4 | 支出取得 (id 指定) | `GET /api/expenses/{id}` | `USER#{u}` | `begins_with(EXP#)` | `id == X` (DDB FilterExpression) | [dynamodb.py:70](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L70) |
| 5 | 支出更新 / 削除 | `PUT/DELETE /api/expenses/{id}` | `USER#{u}` | (#4 で SK を解決して直接指定) | - | [dynamodb.py:93](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L93), [dynamodb.py:118](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L118) |
| 6 | レシート取得 | `GET /api/receipts/{id}` | `USER#{u}` | `RCV#{id}` (eq) | - | [dynamodb.py:144](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L144) |
| 7 | カテゴリ一覧 | `GET /api/categories` | `USER#{u}` | `begins_with(CAT#)` | - | [dynamodb.py:152](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L152) |
| 8 | 予算一覧 (月指定) | `GET /api/budgets?month=YYYY-MM` | `USER#{u}` | `begins_with(BDG#YYYY-MM)` | - | [dynamodb.py:191](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L191) |
| 9 | 月次集計取得 | `GET /api/summary/monthly?month=YYYY-MM` | `USER#{u}` | `SUM#{YYYY-MM}` (eq) | - | [dynamodb.py:213](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L213) |
| 10 | 月次集計の原子的加算 | (内部、支出登録時) | `USER#{u}` | `SUM#{YYYY-MM}` | - | [dynamodb.py:219](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L219) |

## ScanIndexForward

支出一覧 (#1, #2) は `ScanIndexForward=False` で SK 降順 = **時系列逆順** を返す
([dynamodb.py:63](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L63))。これは SK に ISO8601 timestamp を含める設計が前提。

## Anti-patterns / Known concerns

### A1. Expense の id 指定取得が O(n)
`get_expense` / `update_expense` / `delete_expense` ([dynamodb.py:70-125](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L70))
は SK に timestamp が含まれるため、id だけからは SK を再構築できない。よって `begins_with(EXP#)`
でユーザー全期間の支出を Query した上で `FilterExpression` で id 一致を探す。

- 計算量: ユーザーの累計支出件数 N に対して O(N) の Read Capacity 消費
- 影響: ユーザーあたりの累積支出が極端に増えた時 (年単位で数千件以上) RCU が無視できなくなる
- 改善案: 別 GSI `id-index` (PK=id, SK=created_at) を貼る、もしくは Expense 作成時に id 単独
  で参照可能なエイリアス item を別 SK で複製する

### A2. カテゴリフィルタが post-filter
`get_expenses(..., category=X)` ([dynamodb.py:67](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L67)) は Query 段階では
カテゴリで絞れず、Python 側で filter している。Query で読んだ全件分の RCU を消費する。

- 影響: A1 と同じく件数増で顕在化
- 改善案: `category` を SK prefix に含める設計に変更 (`EXP#{category}#{date}#{id}` 等) するか、
  GSI を貼る。ただし時系列ソートとの両立が難しい

### A3. MonthlySummary の 2段階更新
`update_monthly_summary` ([dynamodb.py:225-259](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L225)) は
`UpdateExpression` でマップ要素を加算するが、`by_category` 自体が存在しない初回は
DynamoDB が `ValidationException` を投げる (`if_not_exists` はマップの**サブパス**には効かない)。
`ClientError` で例外を捕捉して `put_item` でフォールバックしている。

- 副作用: 同時並行で同月初回の支出が2件登録された場合、両方が `put_item` 経路に入り
  片方が上書きされる可能性 (last-write-wins)
- 影響: 初月最初の数件の合計値がずれるリスク (本番では低頻度)
- 改善案: `INIT_SUMMARY` 的な明示初期化トランザクション、or `update_item` 失敗時は
  `ConditionExpression` で `attribute_not_exists(by_category)` の `put_item` にする

### A4. decrement_monthly_summary の例外握り潰し
`decrement_monthly_summary` ([dynamodb.py:284](https://github.com/tommykey-apps/receipto/blob/main/api/store/dynamodb.py#L284)) は `Exception: pass`
でエラーを完全に捨てる。サマリ未存在時 / 既に 0 のときは正常だが、それ以外 (ネットワーク
エラー、IAM 権限不足等) も握り潰される。

- 改善案: 具体的に `ClientError` の `ValidationException` のみ無視、それ以外は raise
