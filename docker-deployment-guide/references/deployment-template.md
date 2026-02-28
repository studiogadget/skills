# デプロイメント手順書テンプレート

本テンプレートの `{{...}}` プレースホルダーを実際の値に置換して使用する。
該当しないセクションは削除すること。

---

# {{service-display-name}} デプロイメント手順書

本ドキュメントは、`{{service-name}}`の本番環境へのデプロイ手順を記載する。

---

## 1. 前提条件

- Docker Engine 25.0以上がインストール済み
- Docker Composeがインストール済み（v2推奨）
- サーバーに十分なディスク容量がある（イメージ約{{image-size-estimate}} + データ領域）
- ファイル転送ツール（WinSCP等）が利用可能
- {{additional-prerequisites（不要なら削除）}}

---

## 2. 本番用Dockerイメージのビルド（ローカル環境、Docker Compose使用）

### 2.1 リポジトリをローカルに配置

```bash
git clone {{repository-url}} {{project-dir-name}}
cd {{project-dir-name}}
```

### 2.2 docker-compose.yamlに本番サービスを定義

既存の`docker-compose.yaml`に、本番用の`{{service-name}}`サービスを追加する。

```yaml
services:
  {{service-name}}:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        # 本番環境では開発依存を含めない
        INSTALL_EXTRAS: ${DOCKER_INSTALL_EXTRAS:-}
    image: {{docker-image-name}}:${IMAGE_TAG:-latest}
    container_name: {{service-name}}
    environment:
      PROJECT_ENV: production
      TZ: Asia/Tokyo
      LOG_LEVEL: INFO
    volumes:
      # 設定ファイルディレクトリ（読み取り専用）
      - ./config:/app/config:ro
      # 出力ディレクトリ
      - ./output:/app/output
      # ログディレクトリ
      - ./logs:/app/logs
    working_dir: /app
    command: {{default-command}}
```

### 2.3 Docker Composeでイメージをビルド

本番環境では開発依存を含めない。コマンドラインでバージョンタグを指定する。

**Linux / macOS（bash）での実行**:

```bash
# 環境変数を指定してビルド（yyyymmdd形式推奨）
IMAGE_TAG={{image-tag-example}} docker compose build {{service-name}}
```

**Windows（PowerShell）での実行**:

```powershell
# 方法1: 環境変数を設定してからビルド（推奨）
$env:IMAGE_TAG = "{{image-tag-example}}"
docker compose build {{service-name}}

# 方法2: 1行で実行する場合
$env:IMAGE_TAG = "{{image-tag-example}}"; docker compose build {{service-name}}

# 環境変数を確認
$env:IMAGE_TAG
```

**ビルド確認**:

```bash
docker images | grep {{docker-image-name}}

# 期待される出力例:
# {{docker-image-name}}   {{image-tag-example}} <IMAGE_ID>   X minutes ago   XXX MB
# {{docker-image-name}}   latest                <IMAGE_ID>   X minutes ago   XXX MB
```

### 2.4 イメージをファイル化してサーバーへ転送

本番サーバーへは、ビルド済みイメージをtarで保存し、WinSCPなどで転送する。

**Linux / macOS（bash）での実行**:

```bash
# 本日の日付でイメージをtar化（yyyymmdd形式）
IMAGE_TAG={{image-tag-example}}
docker save {{docker-image-name}}:${IMAGE_TAG} \
  -o {{docker-image-name}}-${IMAGE_TAG}.tar

# gzip圧縮（ファイル転送時の圧縮）
gzip {{docker-image-name}}-${IMAGE_TAG}.tar

# ファイル確認
ls -lh {{docker-image-name}}-${IMAGE_TAG}.tar.gz
```

**Windows（PowerShell）での実行**:

```powershell
# 環境変数を設定（前セクションで設定済みの場合はスキップ可）
$env:IMAGE_TAG = "{{image-tag-example}}"

# イメージをtar化
docker save "{{docker-image-name}}:$env:IMAGE_TAG" `
  -o "{{docker-image-name}}-$env:IMAGE_TAG.tar"

# 方法1: 7-Zipで圧縮（推奨、7-Zipがインストール済みの場合）
7z a -tgzip "{{docker-image-name}}-$env:IMAGE_TAG.tar.gz" `
  "{{docker-image-name}}-$env:IMAGE_TAG.tar"

# 方法2: tar コマンドで圧縮（Windows 11 / Server 2022推奨）
tar -czf "{{docker-image-name}}-$env:IMAGE_TAG.tar.gz" `
  "{{docker-image-name}}-$env:IMAGE_TAG.tar"

# ファイル確認
Get-Item "{{docker-image-name}}-$env:IMAGE_TAG.tar.gz" | `
  Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
```

**転送**:

- WinSCPで `{{docker-image-name}}-{{image-tag-example}}.tar.gz` をサーバーへ転送
- 送付先の例: `~/{{project-dir-name}}/images/`

**バージョン管理（yyyymmdd形式推奨）**:

| 形式 | 用途 | 例 |
|------|------|------|
| yyyymmdd | **推奨**：日付ベース、追跡可能 | `20260228`, `20260101` |
| yyyymmdd-HHmm | より詳細な時刻管理 | `20260228-1030` |
| yyyymmdd-feature | フィーチャー付き | `20260228-fix-v2` |
| セマンティック | 正式リリース（個別管理） | `1.0.0`, `2.0.0` |

**サーバー側でロード**:

```bash
# サーバー上で受信したファイルを展開
cd ~/{{project-dir-name}}/images/
gunzip {{docker-image-name}}-{{image-tag-example}}.tar.gz

# イメージをロード
docker load -i {{docker-image-name}}-{{image-tag-example}}.tar

# ロード確認
docker images | grep {{docker-image-name}}
# {{docker-image-name}}   {{image-tag-example}}   <ID>   ...
```

---

## 3. サーバーへの配置とディレクトリ構成

### 3.1 必要なディレクトリの作成

```bash
# サーバーで実行（配置先ディレクトリ）
cd ~/{{project-dir-name}}
mkdir -p config
mkdir -p output
mkdir -p logs
mkdir -p images
# {{additional-dirs（不要なら削除）}}
```

### 3.2 ディレクトリ構成

本番環境で必要なディレクトリ構成（`cd ~/{{project-dir-name}}` 後）:

```
./
├── config/                      # 設定ファイル
│   └── config.yaml
├── output/                      # 出力先
│   └── {{output-dir-structure}}
├── logs/                        # ログ出力先
│   └── {{log-filename}}
└── images/                      # Dockerイメージ
    └── {{docker-image-name}}-{{image-tag-example}}.tar
```

**注意事項**:
- `output/`配下のサブディレクトリは実行時に自動作成される（該当する場合）
- `logs/`, `output/`は書き込み権限を設定すること（コンテナ内UID: 1001）

---

## 4. 設定ファイルの作成

### 4.1 config.yamlの作成

```bash
# config.example.yamlをコピーして本番設定を作成
cp config/config.example.yaml config/config.yaml
```

**編集が必要な箇所**:

```yaml
{{config-yaml-excerpt}}
```

**設定検証**:

```bash
cd ~/{{project-dir-name}}
docker run --rm -v "./config:/app/config:ro" \
  {{docker-image-name}}:{{image-tag-example}} \
  python -c "import yaml; yaml.safe_load(open('/app/config/config.yaml'))"
```

### 4.2 .envファイルの作成（オプション）

Docker Composeを使用する場合は`.env`ファイルを作成する。

```bash
cp .env.example .env
```

```dotenv
# 本番環境では開発依存を含めない
DOCKER_INSTALL_EXTRAS=
{{additional-env-vars（不要なら削除）}}
```

---

## 5. Docker Composeを使用した動作確認（ローカル開発環境向け）

ローカルで開発・検証する場合は、以下の方法で動作確認できる。

```bash
# docker-compose.yamlのサービスを実行
docker compose run --rm {{service-name}} \
  {{run-command}} --help
```

本番サーバーで実行する場合は、セクション6以降の手順に従う。

---

## 6. 動作確認

### 6.1 ヘルプ表示

```bash
cd ~/{{project-dir-name}}
docker run --rm \
  -v "./config:/app/config:ro" \
  -v "./output:/app/output" \
  -v "./logs:/app/logs" \
  {{docker-image-name}}:{{image-tag-example}} \
  {{run-command}} --help
```

**期待される出力**:

```
{{help-output}}
```

### 6.2 本番実行

```bash
cd ~/{{project-dir-name}}
docker run --rm \
  -v "./config:/app/config:ro" \
  -v "./output:/app/output" \
  -v "./logs:/app/logs" \
  {{docker-image-name}}:{{image-tag-example}} \
  {{run-command}}
```

### 6.3 オプション付き実行例

<!-- 対象サービスのCLIオプションに応じて記載。不要なら削除 -->

```bash
cd ~/{{project-dir-name}}

# 例: オプション付き実行
docker run --rm \
  -v "./config:/app/config:ro" \
  -v "./output:/app/output" \
  -v "./logs:/app/logs" \
  {{docker-image-name}}:{{image-tag-example}} \
  {{run-command}} {{example-options}}
```

### 6.4 出力確認

```bash
# 出力ファイルの確認
ls -lh output/{{expected-output-path}}
```

### 6.5 ログ確認

```bash
tail -f logs/{{log-filename}}
```

**正常実行時のログ例**:

```json
{{log-output-example}}
```

---

## 7. 定期実行の設定（cron）

### 7.1 本番実行コマンド

**基本形式（yyyymmdd形式のバージョンタグを使用）**:

```bash
cd ~/{{project-dir-name}}

# タグ付きイメージで実行
docker run --rm \
  -v "./config:/app/config:ro" \
  -v "./output:/app/output" \
  -v "./logs:/app/logs" \
  {{docker-image-name}}:{{image-tag-example}} \
  {{run-command}}
```

**最新ビルドを利用する場合（開発・テスト時）**:

```bash
# latestタグを指定（または省略可）
docker run --rm \
  -v "./config:/app/config:ro" \
  -v "./output:/app/output" \
  -v "./logs:/app/logs" \
  {{docker-image-name}}:latest \
  {{run-command}}
```

### 7.2 cronジョブの設定例

{{cron-schedule-description（例: 毎日午前1時に実行する例）}}:

```bash
# crontabを編集
crontab -e

# 以下を追加（1行で記載、yyyymmddは本番稼働日に合わせて更新）
{{cron-expression}} cd ~/{{project-dir-name}} && docker run --rm -v "./config:/app/config:ro" -v "./output:/app/output" -v "./logs:/app/logs" {{docker-image-name}}:{{image-tag-example}} {{run-command}} >> /var/log/{{cron-log-filename}} 2>&1
```

**バージョンアップ時の更新例**:

```bash
# 新しいビルド日（{{image-tag-example-next}}）でリリースされた場合
crontab -e

# 以下に変更
{{cron-expression}} cd ~/{{project-dir-name}} && docker run --rm -v "./config:/app/config:ro" -v "./output:/app/output" -v "./logs:/app/logs" {{docker-image-name}}:{{image-tag-example-next}} {{run-command}} >> /var/log/{{cron-log-filename}} 2>&1
```

**環境変数で管理する場合（オプション）**:

```bash
# /etc/environment に追加
{{IMAGE_TAG_ENV_VAR}}={{image-tag-example}}

# crontabで明示的に環境を読み込む
{{cron-expression}} . /etc/environment; cd ~/{{project-dir-name}} && docker run --rm -v "./config:/app/config:ro" -v "./output:/app/output" -v "./logs:/app/logs" {{docker-image-name}}:${{{IMAGE_TAG_ENV_VAR}}} {{run-command}} >> /var/log/{{cron-log-filename}} 2>&1
```

### 7.3 ログローテーション

```bash
sudo tee /etc/logrotate.d/{{logrotate-name}} > /dev/null <<EOF
/var/log/{{cron-log-filename}} {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

---

## 8. トラブルシューティング

### 8.1 イメージビルド失敗

**現象**: Dockerビルド時にエラーが発生する

**確認事項**:
- Docker Engineのバージョンが20.10以上か
- ディスク容量は十分か
- ネットワーク接続は正常か（依存パッケージのダウンロードに必要）

**解決方法**:

```bash
# ビルドキャッシュをクリアして再ビルド
docker builder prune -a
IMAGE_TAG={{image-tag-example}} docker compose build {{service-name}}
```

### 8.2 設定ファイルが見つからない

**現象**: `Config file not found` エラー

**確認事項**:
- `config/config.yaml`が存在するか
- Dockerボリュームマウントが正しいか

**解決方法**:

```bash
# 設定ファイルの存在確認
ls -l config/config.yaml

# 存在しない場合はconfig.example.yamlをコピー
cp config/config.example.yaml config/config.yaml
```

### 8.3 出力ディレクトリへの書き込み失敗

**現象**: `Permission denied` エラー

**確認事項**:
- `output/`, `logs/`ディレクトリのパーミッション

**解決方法**:

```bash
# ディレクトリが存在しない場合は作成
mkdir -p output logs

# ディレクトリのオーナーをコンテナ実行ユーザーに変更
# 例: Dockerfile内の appuser の UID/GID が 1001:1001 の場合
chown -R 1001:1001 output logs

# 必要最小限のパーミッションを付与（所有者: 読み書き実行, グループ: 読み書き実行, その他: アクセス不可）
chmod -R 770 output logs
```

### 8.4 イメージバージョンが見つからない

**現象**: `docker: Error response from daemon: manifest not found`

**確認事項**:
- ロードしたイメージのバージョンタグを確認したか
- `docker images`でイメージが存在するか

**解決方法**:

```bash
# ロード済みのイメージを確認
docker images | grep {{docker-image-name}}

# イメージが見つからない場合は再ロード
cd ~/{{project-dir-name}}
docker load -i ./images/{{docker-image-name}}-{{image-tag-example}}.tar
```

### 8.5 cronでイメージバージョンタグが認識されない

**現象**: cronジョブが失敗し、`image not found`エラー

**確認事項**:
- `/etc/environment`またはcrontabに環境変数が正しく設定されているか
- cronが環境変数を読み込んでいるか

**推奨される解決方法（yyyymmddはハードコード）**:

```bash
# crontabに具体的なバージョンタグを記載（最も安定）
{{cron-expression}} cd ~/{{project-dir-name}} && docker run --rm -v "./config:/app/config:ro" -v "./output:/app/output" -v "./logs:/app/logs" {{docker-image-name}}:{{image-tag-example}} {{run-command}} >> /var/log/{{cron-log-filename}} 2>&1
```

**環境変数で運用する場合**:

```bash
# /etc/environment に追加
{{IMAGE_TAG_ENV_VAR}}={{image-tag-example}}

# crontabで明示的に環境を読み込む
{{cron-expression}} . /etc/environment; cd ~/{{project-dir-name}} && docker run --rm -v "./config:/app/config:ro" -v "./output:/app/output" -v "./logs:/app/logs" {{docker-image-name}}:${{{IMAGE_TAG_ENV_VAR}}} {{run-command}} >> /var/log/{{cron-log-filename}} 2>&1
```

<!-- 以下、対象サービス固有のトラブルシューティングを追加 -->

---

## 9. クリーンアップ

### 9.1 Dockerイメージの削除

```bash
# 特定バージョンのイメージを削除
docker rmi {{docker-image-name}}:{{image-tag-example}}

# 未使用イメージを一括削除
docker image prune -a
```

### 9.2 出力データの削除

```bash
# 古い出力データを削除（例: 1年以上前のデータ）
find output/ -type f -name "*.csv" -mtime +365 -delete

# ログファイルを削除
rm -f logs/{{log-filename}}*
```

---

## 10. セキュリティとコンプライアンス

<!-- 対象サービスに固有のセキュリティ/コンプライアンス事項を記載。不要なら削除 -->

### 10.1 {{compliance-section-title}}

{{compliance-content}}

### 10.2 データ保管と取り扱い

- 取得したデータは社内利用のみとし、第三者への再配布は行わない
- データの保管期間を定め、不要になったデータは削除する
- 個人情報は含めない。機密情報がある場合は適切に管理する

---

## 11. TODO: クラウド環境へのデプロイ手順（今後追加予定）

以下のクラウド環境へのデプロイ手順は、今後追加予定です。

- [ ] **Amazon Web Services (AWS)**
  - ECR への Docker イメージ登録
  - ECS/Fargate での コンテナ実行
  - Lambda での サーバーレス実行（該当する場合）
  - CloudWatch でのログ管理
  - EventBridge / DynamoDB での スケジューリング/フロー管理

- [ ] **Google Cloud Platform (GCP)**
  - Artifact Registry へのイメージ登録
  - Cloud Run でのマネージドコンテナ実行
  - Cloud Scheduler でのジョブ スケジューリング
  - Cloud Logging でのログ管理
  - Pub/Sub でのイベント駆動

---

## 12. 参考情報

<!-- プロジェクト内の関連ドキュメントへのリンクを記載 -->

- [仕様書](./requirements.md)
- [設計書](./design.md)
- [Dockerfile](../../docker/Dockerfile)
- [設定例](../../config/config.example.yaml)

---

## 13. 変更履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|-----------|---------|-------|
| {{date}} | 1.0 | 初版作成 | - |
