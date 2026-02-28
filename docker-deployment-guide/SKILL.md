---
name: docker-deployment-guide
description: Dockerベースのアプリケーションのデプロイメント手順書（Markdown）を作成するスキル。「デプロイ手順書」「デプロイメント手順」「deployment guide」「本番環境への配置手順」「サーバーへの配置手順」などの依頼でトリガーする。Docker Composeビルド→イメージ転送→サーバー配置→設定→動作確認→cron設定の流れで手順書を生成する。
---

# Docker デプロイメント手順書作成スキル

ユーザーが指定した対象（サービス/モジュール/機能）について、Dockerベースの本番デプロイメント手順書をMarkdown形式で作成する。

## トリガー条件

- 「〇〇のデプロイ手順書を作成して」
- 「〇〇の本番環境への配置手順を書いて」
- 「〇〇のデプロイメントガイドを作って」
- 「〇〇のサーバーへの配置手順書」
- 英語: "create deployment guide for ○○"

## ワークフロー（4ステップ）

### Step 1: コンテキスト収集

以下を自律的に調査し、手順書に必要な情報を収集する。

**必須調査項目**:
1. **Dockerfile** — ビルド引数（`ARG`）、ベースイメージ、依存インストール手順、`ENTRYPOINT`/`CMD`
2. **docker-compose.yaml** — 既存サービス定義、ボリュームマウント、環境変数、`image:`のタグ設定
3. **エントリポイント** — 対象モジュールの`__main__.py`やCLI定義（引数、実行コマンド）
4. **設定ファイル** — `config.example.yaml`や`.env.example`の構造と必須項目
5. **仕様書** — `docs/specs/`配下のrequirements.md, design.md（存在する場合）

**判断が必要な場合のみユーザーに確認**:
- サーバー配置先パス（デフォルト: `~/{{project-dir-name}}/`）
- cron実行スケジュール（デフォルト: 毎日午前1時）
- 開発環境のOS（デフォルト: Windows PowerShell）

### Step 2: 手順書の生成

`references/deployment-template.md` のテンプレート構造に従い、Step 1で収集した情報を埋め込む。

**生成ルール**:
- セクション番号は連番を維持する
- プロジェクト固有のプレースホルダー `{{...}}` をすべて実際の値に置換する
- 該当しないセクションは削除する（空セクションを残さない）
- CLIの`--help`出力例は、実際のCLI定義から正確に記載する
- config.yaml例は、`config.example.yaml`から対象セクションを抜粋する
- コマンド例は、実際のDockerfileの構成に合わせる（`uv run`、`python -m` 等）

**OS別コマンド記載ルール**:
- ビルドとイメージ保存（ローカル実行）は **bash と PowerShell の両方** を記載する
- サーバー側コマンド（動作確認、cron等）は **bash のみ** で記載する
- PowerShellでの環境変数: `$env:VAR = "value"` 形式
- PowerShellでの行継続: バッククォート `` ` ``
- bash構文 `VAR=value command` はPowerShellで動作しないことに注意

**バージョンタグルール**:
- Docker Composeの`image:`に`${IMAGE_TAG:-latest}`を使用
- yyyymmdd形式を推奨（例: `20260228`）
- ビルド時にコマンドラインで`IMAGE_TAG`を指定（.envファイルへの書き込みは避ける）

**サーバーパス運用ルール**:
- `cd ~/{{project-dir-name}}`で移動後、相対パス`./config`, `./output`, `./logs`を使用する
- cronコマンドでは`cd ~/{{project-dir-name}} && docker run ...`パターンを使用する
- 絶対パスの重複記載を避け、一貫性を保つ

### Step 3: 配置場所の決定と出力

**配置ルール**:
- `docs/specs/{feature-name}/` が存在する場合 → そこに `deployment.md` を作成
- 存在しない場合 → `docs/` 直下に `deployment-{feature-name}.md` を作成

### Step 4: セルフチェック

生成した手順書を以下の観点で検証する:

- [ ] 全プレースホルダーが置換済み
- [ ] コマンド例がプロジェクトの実構成と一致
- [ ] secrets/APIキー/PIIが平文で記載されていない
- [ ] 必須セクション（ビルド、配置、設定、動作確認）がすべて存在
- [ ] ディレクトリパスが一貫している（相対パス運用が統一されている）
- [ ] ローカル実行コマンドにbash/PowerShellの両方が記載されている
- [ ] バージョンタグが全セクションで統一されている（yyyymmdd形式）
- [ ] cronコマンドに`cd && docker run`パターンが使用されている

## 同梱リソース

- `references/deployment-template.md` — 手順書のテンプレート（プレースホルダー付き）

## 注意事項

- 手順書内でsecrets/トークン/APIキーを平文で記載しない（環境変数で管理）
- 禁止語を使用しない: best / optimal / faster / always / never / perfect
- 出力言語は日本語（コマンド/識別子は英語）
