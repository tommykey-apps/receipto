# Receipto

レシートOCR + 支出管理 + 予算アラートの家計簿アプリ。AWSポートフォリオ第3弾。

## 技術スタック

- **Backend**: Python 3.12 + FastAPI + Mangum (Lambda/HTTP デュアルモード)
- **Frontend**: SvelteKit 5 + Svelte 5 + Tailwind CSS v4 + shadcn-svelte (new-york)
- **DB**: DynamoDB On-Demand (シングルテーブル)
- **Auth**: Cognito + API Gateway JWT Authorizer
- **OCR**: Textract AnalyzeExpense → Step Functions Express
- **通知**: SNS (予算アラート) + SES (週次ダイジェスト)
- **スケジューラー**: EventBridge Scheduler
- **IaC**: Terraform
- **CI/CD**: GitHub Actions + flox
- **パッケージマネージャー**: pnpm (web), pip (api)

## 開発コマンド

```bash
# 環境
flox activate

# API (ローカルHTTPモード port 8080)
cd api && pip install -r requirements.txt && python main.py

# Web (port 5173, proxy /api → 8080)
cd web && pnpm install && pnpm dev

# ローカルDynamoDB
docker run -p 8000:8000 amazon/dynamodb-local

# Terraform
cd infra && terraform init && terraform plan
cd infra && terraform apply
cd infra && terraform destroy

# テスト
cd api && python -m pytest
cd web && pnpm build && pnpm check
```

## 環境変数

```bash
# ローカル開発
export DYNAMODB_ENDPOINT=http://localhost:8000
export DYNAMODB_TABLE=expense-tracker
export AWS_REGION=ap-northeast-1
export DEV_USER_ID=local-dev-user    # Cognito認証スキップ

# 本番 (Lambda環境変数)
DYNAMODB_TABLE, RECEIPTS_BUCKET, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID
SNS_TOPIC_ARN, SES_FROM_EMAIL
```

## API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| POST | /api/receipts/upload | S3 presigned URL発行 |
| GET | /api/receipts/{id} | レシート詳細 |
| GET | /api/expenses | 支出一覧 |
| POST | /api/expenses | 手動登録 |
| PUT | /api/expenses/{id} | 編集 |
| DELETE | /api/expenses/{id} | 削除 |
| GET | /api/categories | カテゴリ一覧 |
| POST | /api/categories | カテゴリ追加 |
| GET | /api/summary/monthly | 月次集計 |
| GET | /api/summary/trend | トレンド |
| GET | /api/budgets | 予算一覧 |
| PUT | /api/budgets | 予算更新 |

## DynamoDB シングルテーブル

PK: `USER#{cognito_sub}`, SK: `EXP#`, `RCV#`, `CAT#`, `BDG#`, `SUM#`

## AWS構成

- ドメイン: expense.tommykeyapp.com
- リージョン: ap-northeast-1
- VPC/EKS: url-shortener-vpc / url-shortener-cluster (共有)
- State: s3://tommykeyapp-tfstate key=expense-tracker/terraform.tfstate

## Git ルール

- npm は使わない。pnpm のみ
