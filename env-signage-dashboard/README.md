# 環境監視ダッシュボード

> Wiki情報自動取得機能付きの環境監視サイネージサービス

## 概要

このプロジェクトは、複数のWikiプラットフォーム（Confluence、GitHub Wiki、Notion等）から環境情報を自動取得し、リアルタイムでヘルスチェックを行う環境監視ダッシュボードです。GitHub Pagesでホストされる静的サイトとして動作します。

## 主な機能

### 🔍 Wiki情報自動取得
- **Confluence**: REST APIを使用したテーブル情報の抽出
- **GitHub Wiki**: マークダウンテーブルの自動解析
- **Notion**: Database APIを使用したデータ取得
- **汎用HTML**: スクレイピングによる情報抽出

### 📊 リアルタイム監視
- 環境・サービスのヘルスチェック
- レスポンスタイム測定
- 状態の可視化（正常、警告、エラー、メンテナンス）
- 自動更新（60秒間隔）

### 🔐 セキュリティ機能
- ログイン情報の暗号化表示
- ワンクリックコピー機能
- アクセス制御対応

### 📱 レスポンシブデザイン
- デスクトップ、タブレット、スマートフォン対応
- 高コントラストモード対応
- アクセシビリティ配慮

## システム構成

```
環境監視ダッシュボード
├── GitHub Pages (静的ホスティング)
├── GitHub Actions (自動データ取得・更新)
├── Wiki情報取得 (Confluence/GitHub/Notion)
└── ヘルスチェック機能
```

## ディレクトリ構成

```
/
├── index.html              # メインページ
├── css/
│   ├── main.css           # メインスタイル
│   └── responsive.css     # レスポンシブ対応
├── js/
│   ├── main.js            # メインロジック
│   ├── api.js             # API通信処理
│   ├── wiki-parser.js     # Wiki解析処理
│   └── config.js          # 設定管理
├── config/
│   ├── environments.json  # 環境設定
│   └── wiki-sources.json  # Wiki情報源設定
├── data/
│   └── wiki-cache.json    # Wiki取得データキャッシュ
├── scripts/
│   ├── fetch-confluence.js   # Confluence取得スクリプト
│   ├── fetch-github-wiki.js  # GitHub Wiki取得スクリプト
│   └── fetch-notion.js       # Notion取得スクリプト
├── .github/
│   └── workflows/
│       ├── update-wiki.yml    # Wiki情報更新
│       └── health-check.yml   # ヘルスチェック・デプロイ
└── README.md
```

## セットアップ

### 1. リポジトリの準備

```bash
# リポジトリをクローン
git clone https://github.com/your-org/env-signage-dashboard.git
cd env-signage-dashboard
```

### 2. GitHub Secrets の設定

以下のSecretをGitHubリポジトリに設定してください：

```
# Confluence (必要に応じて)
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_TOKEN=your_confluence_api_token
CONFLUENCE_USERNAME=your_username

# GitHub Wiki (自動設定)
GITHUB_TOKEN=自動的に利用可能

# Notion (必要に応じて)
NOTION_TOKEN=your_notion_integration_token
```

### 3. 設定ファイルの編集

#### config/wiki-sources.json
```json
{
  "sources": [
    {
      "type": "confluence",
      "name": "開発環境一覧",
      "url": "https://yourcompany.atlassian.net/wiki/spaces/DEV/pages/123456",
      "auth": {
        "type": "api_token",
        "token_env": "CONFLUENCE_TOKEN"
      }
    }
  ]
}
```

#### config/environments.json
```json
{
  "environments": [
    {
      "id": "dev",
      "name": "開発環境",
      "url": "https://dev.example.com",
      "healthCheck": "https://dev.example.com/health"
    }
  ]
}
```

### 4. GitHub Pages の有効化

1. GitHubリポジトリの Settings → Pages
2. Source: GitHub Actions を選択
3. 設定を保存

## 使用方法

### 基本操作

1. **環境カード**: クリックで詳細情報を表示
2. **ログイン情報**: パスワード表示・コピー機能
3. **手動更新**: F5キーまたはCtrl+Rで手動更新
4. **自動更新**: 60秒間隔で自動実行

### Wiki情報の更新

- **自動更新**: 6時間毎にGitHub Actionsで実行
- **手動更新**: GitHubのActionsタブから実行可能

### ヘルスチェック

- **実行間隔**: 15分毎
- **タイムアウト**: 5秒
- **対象**: 各環境のhealthCheckエンドポイント

## Wiki連携設定

### Confluence設定

1. Confluence API トークンの取得
2. wiki-sources.json に設定追加
3. テーブル形式でのデータ作成

### GitHub Wiki設定

1. WikiページをMarkdownテーブル形式で作成
2. パブリックリポジトリまたはアクセス権限の設定

### Notion設定

1. Notion Integration の作成
2. Database へのアクセス許可
3. データベースIDの取得と設定

## カスタマイズ

### デザイン変更

- `css/main.css`: メインスタイル
- `css/responsive.css`: レスポンシブ対応

### 設定変更

- `js/config.js`: 更新間隔、しきい値などの設定

### 新しいWikiプラットフォーム対応

1. `js/wiki-parser.js` にパーサー追加
2. `scripts/` にフェッチスクリプト追加
3. `.github/workflows/update-wiki.yml` に処理追加

## トラブルシューティング

### よくある問題

1. **Wiki取得エラー**
   - APIトークンの有効性確認
   - アクセス権限の確認
   - URL形式の確認

2. **ヘルスチェック失敗**
   - CORS設定の確認
   - エンドポイントURLの確認
   - ネットワーク接続の確認

3. **GitHub Actions失敗**
   - Secretsの設定確認
   - 権限設定の確認

### デバッグ方法

```javascript
// コンソールでデバッグモード有効化
Config.DEBUG = true;
Config.LOG_LEVEL = 'debug';

// API キャッシュクリア
api.clearCache();

// 手動データ更新
dashboard.manualUpdate();
```

## セキュリティ考慮事項

- 機密情報はGitHub Secretsで管理
- パスワードはマスク表示
- HTTPS通信の使用
- 社内ネットワーク制限の推奨

## ライセンス

MIT License

## 貢献方法

1. このリポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## サポート・お問い合わせ

- Issues: [GitHub Issues](https://github.com/your-org/env-signage-dashboard/issues)
- Wiki: [GitHub Wiki](https://github.com/your-org/env-signage-dashboard/wiki)

---

**作成日**: 2025年7月12日  
**バージョン**: 1.0  
**作成者**: システム開発チーム