# Receipto

レシートを撮影するだけで支出を自動記録する家計簿アプリ。OCRで金額・店名を読み取り、カテゴリ自動分類、予算アラート、週次ダイジェストメールまで対応。

## 構成図

![Architecture](docs/architecture.svg)

> [docs/architecture.drawio](docs/architecture.drawio) を draw.io で開くと編集できる

## 使った技術

| | |
|---|---|
| バックエンド | Python 3.12 + FastAPI (Lambda) |
| フロント | SvelteKit 2, Svelte 5, Tailwind CSS v4, shadcn-svelte |
| 認証 | Cognito (JWT, SRP認証) |
| DB | DynamoDB (シングルテーブル設計) |
| OCR | Textract (AnalyzeExpense) |
| ワークフロー | Step Functions (Express) |
| 通知 | SNS (予算アラート) + SES (週次ダイジェスト) |
| スケジューラー | EventBridge Scheduler |
| IaC | Terraform (S3バックエンド + DynamoDB state lock) |
| CI/CD | GitHub Actions + flox |
| 配信 | CloudFront (S3 + API Gateway を同一ドメインで配信) |

## 使ってるAWSサービス

| サービス | 何してるか |
|---------|-----------|
| Lambda | Python API + OCR処理 + 週次ダイジェスト生成 |
| API Gateway | HTTPリクエストをLambdaにルーティング + Cognito JWT認証 |
| DynamoDB | 支出・レシート・カテゴリ・予算・月次集計の保存 |
| S3 | レシート画像 + フロントのビルド成果物 + Terraform state |
| CloudFront | CDN。S3とAPI Gatewayの前に立ってHTTPS配信 |
| Cognito | ユーザー登録、ログイン、JWT発行 (マルチユーザー対応) |
| Textract | レシート画像からOCRで金額・店名・日付を抽出 |
| Step Functions | レシートアップロード → OCR → 分類 → 保存 → 予算チェックのワークフロー |
| SNS | 予算超過時のメール通知 |
| SES | 週次ダイジェストメール送信 |
| EventBridge | 毎週月曜にダイジェスト生成を起動 |
| Route 53 | カスタムドメイン (expense.tommykeyapp.com) のDNS管理 |
| ACM | SSL証明書 (*.tommykeyapp.com ワイルドカード) |
| IAM | LambdaにDynamoDB/S3/Textract等のアクセス権限を付与 |

## 機能

- ユーザー認証（サインアップ、ログイン、JWT）
- レシート撮影 → OCR自動解析（金額・店名・日付）
- 支出の手動登録・編集・削除
- カテゴリ自動分類（ルールベース）
- カテゴリ別予算設定 + 消化率プログレスバー
- 月次サマリー + カテゴリ別ドーナツチャート
- 支出トレンド（過去N月の推移）
- 予算超過メールアラート（SNS）
- 週次ダイジェストメール（SES + EventBridge）

## ディレクトリ構成

```
receipto/
├── api/          # Python FastAPI (Lambda対応、Mangumでデュアルモード)
├── functions/    # Step Functions用Lambda (OCR, 分類, 通知等)
├── web/          # SvelteKit フロント（shadcn-svelte new-york）
├── infra/        # Terraform（Cognito, DynamoDB, Lambda, Step Functions等）
├── docs/         # 構成図 (draw.io)
└── .github/      # GitHub Actions（Lambda deploy + Terraform apply）
```

## API

| Method | Path | 何するか |
|--------|------|---------|
| POST | `/api/receipts/upload` | レシート画像アップロード用 presigned URL 発行 |
| GET | `/api/receipts/{id}` | レシート詳細（OCR結果含む） |
| GET | `/api/expenses` | 支出一覧（月・カテゴリでフィルタ可） |
| POST | `/api/expenses` | 支出の手動登録 |
| PUT | `/api/expenses/{id}` | 支出の編集 |
| DELETE | `/api/expenses/{id}` | 支出の削除 |
| GET | `/api/categories` | カテゴリ一覧 |
| POST | `/api/categories` | カスタムカテゴリ追加 |
| GET | `/api/summary/monthly` | 月次集計 |
| GET | `/api/summary/trend` | 過去N月のトレンド |
| GET | `/api/budgets` | 予算一覧 |
| PUT | `/api/budgets` | 予算設定 |

## ローカルで動かす

開発ツールは全部floxで管理してるので、まずfloxを入れる。

```bash
nix profile install --accept-flake-config github:flox/flox
```

あとはactivateすればpython, terraform, pnpm等が全部使える。

```bash
flox activate

# DynamoDB Local を起動
docker run -d -p 8000:8000 amazon/dynamodb-local
aws dynamodb create-table --table-name expense-tracker \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000

# API起動
cd api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEV_USER_ID=local-dev-user DYNAMODB_TABLE=expense-tracker DYNAMODB_ENDPOINT=http://localhost:8000 python main.py &

# フロント起動
cd web && pnpm install && pnpm dev
```

Viteのプロキシ設定で `/api/*` がPythonのAPIに流れるようにしてある。
DEVモードではCognito認証をスキップするので、ログインなしでUI確認できる。

## デプロイ

```bash
cd infra && terraform apply
```

使い終わったら壊す。

```bash
cd infra && terraform destroy
```

## コストについて

サーバーレス構成なので、アクセスがなければほぼ $0。
DynamoDBはオンデマンドモード、Textractは使った分だけ課金。月額 $1〜4 程度。
