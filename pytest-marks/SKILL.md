---
name: pytest-marks
description: "pytestのマーク体系を設計・実装するスキル。「テストをマークで分類したい」「CIでDockerテストをスキップしたい」「Dockerコンテナ内で実行できないテストを除外したい」「make testでDockerテストを実行したい」「テストの実行対象を環境ごとに切り替えたい」「新しいマークを追加したい」「skipifを使いたい」「pytestの--strict-markersで未定義マークエラーが出る」という依頼で起動。マーク設計→pyproject.toml登録→テストコード付与→CI/ローカルコマンド整合の流れで実装する。"
---

# pytest マーク体系設計・実装スキル

pytestのカスタムマークを用いて、実行環境・所要時間・外部依存に応じてテスト実行を制御するパターンを設計・実装する。

## 仕組みの概要

```
テスト実行環境          除外すべきテスト           コマンド
─────────────   →   ─────────────────   →   ─────────────────────────
GitHub Actions CI      docker, slow        -m "not docker and not slow"
ローカル開発            (任意)              -m "not slow" など
Docker コンテナ内        docker + skipif     自動除外（skipif が動作）
ローカルDocker実行       （全て実行）        make test  # MakefileでDocker切り替え時
```

---

## Step 1: マーク名の設計

テストを付与するマークは**実行環境・制約の種類**で命名する。`unit` / `integration` のような**実装段階そのものの分類名**をそのまま付けるのではなく、「このテストが動く／動かない条件」「何を必要とするか」を名前にする。

### マーク設計表（参考）

| マーク名 | 意味 | 除外すべき環境 |
|---------|------|----------------|
| `slow` | 実行に数十秒以上かかる | CI（高速化が必要な場合）、ローカル日常開発 |
| `integration` | **外部依存あり**をまとめて表す包括ラベル（外部サービス・ファイルシステム・DB など）。可能なら `external_service` / `db` / `filesystem` など、より具体的なマークを優先する | モック環境のみのCIジョブ |
| `docker` | Dockerコマンド・Docker Compose等のホストレベル操作を含む | CI、Dockerコンテナ内 |
| `network` | 外部URLへの実通信を含む | オフライン環境、CI回線制限時 |
| `browser` | Playwrightなどのブラウザ自動操作を含む | ブラウザ未インストール環境 |
| `flaky` | 環境依存・タイミング依存で不安定なテスト | CI strict実行 |

> **命名原則**: 「このテストが**何を必要とするか**」を名前にする。`integration` を使う場合も「結合テストだから」ではなく「外部依存があるため制御したい」という**制約ベースの意味**に限定する。`test_` メソッド名と重複させない。

---

## Step 2: pyproject.toml への登録

`markers` へ追加しないと `--strict-markers` 設定下でエラーになる。

```toml
[tool.pytest.ini_options]
addopts = [
    "--strict-markers",   # 未登録マーク使用をエラーにする（必須）
    "--strict-config",
    # ...
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "docker: marks tests as docker-related (deselect with '-m \"not docker\"')",
    # 追加する場合はここへ
    # "network: marks tests requiring outbound network access",
    # "browser: marks tests requiring a browser (Playwright etc.)",
]
```

**登録書式**:
```
"<マーク名>: <説明文>"
```

説明文は英語・日本語どちらでも可だが、英語が一般的。

---

## Step 3: テストコードへのマーク付与

### 3-A: クラスレベルマーク（推奨）

同一クラスのテスト全体に同じマークを付ける場合は、クラス宣言へデコレートする。

```python
import pytest
from pathlib import Path

@pytest.mark.docker
@pytest.mark.skipif(
    Path("/.dockerenv").exists(),
    reason="Dockerコンテナ内ではDockerコマンドが利用できないためスキップ",
)
class TestDockerBuild:
    """DockerビルドのテストはDockerホスト上でのみ実行する。"""
    ...
```

### 3-B: メソッドレベルマーク

一部のテストのみに付ける場合はメソッドへデコレートする。

```python
class TestReportGenerator:

    def test_正常系_HTMLレポートを生成する(self) -> None:
        ...  # マーク不要な軽量テスト

    @pytest.mark.slow
    def test_正常系_大量データでレポートを生成する(self) -> None:
        ...  # 重いテストのみ slow マーク
```

### 3-C: skipif パターン（環境依存スキップ）

テストを除外する方法は2つある。使い分けを間違えないこと。

| 方法 | 動作 | 用途 |
|------|------|------|
| `-m "not docker"` | コレクション時点で除外（テスト一覧に出ない） | CI の実行対象制御 |
| `pytest.mark.skipif(...)` | 収集するが実行時スキップ（"s"と表示） | 実行環境での自動判定 |

**Docker コンテナ内での自動スキップ**:

```python
@pytest.mark.docker
@pytest.mark.skipif(
    Path("/.dockerenv").exists(),   # /.dockerenv はDockerコンテナ内に存在するファイル
    reason="Dockerコンテナ内ではDockerコマンドが利用できないためスキップ",
)
class TestDockerBuild:
    ...
```

**他のskipif条件の例**:

```python
import os
import sys
import shutil

# OS依存
@pytest.mark.skipif(sys.platform != "linux", reason="Linuxのみ対応")

# コマンド依存
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker コマンドが見つからない")

# 環境変数依存
@pytest.mark.skipif(
    os.environ.get("SLACK_WEBHOOK_URL") is None,
    reason="SLACK_WEBHOOK_URL が未設定",
)
```

---

## Step 4: CI（GitHub Actions）での活用

### 4-A: 基本パターン（重いテスト・環境依存テストを除外）

```yaml
- name: Run tests
  run: |
    uv run pytest tests/ \
      --ignore=tests/poc \
      -m "not docker and not slow" \
      -v
```

### 4-B: 複数ジョブで役割分担する

```yaml
jobs:
  test-unit:
    name: Unit Tests
    steps:
      - run: uv run pytest tests/ -m "not docker and not slow and not network"

  test-integration:
    name: Integration Tests
    if: github.ref == 'refs/heads/main'   # mainブランチのみ
    steps:
      - run: uv run pytest tests/ -m "integration and not docker"

  test-docker:
    name: Docker Tests
    if: github.ref == 'refs/heads/main'
    steps:
      - run: uv run pytest tests/ -m "docker"
```

### 4-C: スケジュール実行で重いテストだけ実行

```yaml
on:
  schedule:
    - cron: "0 0 * * 1"   # 毎週月曜

jobs:
  test-slow:
    name: Slow Tests (Weekly)
    steps:
      - run: uv run pytest tests/ -m "slow"
```

---

## Step 5: ローカル開発でのコマンド例

```bash
# 全テスト（ローカル通常実行）
uv run pytest tests/

# docker・slow を除いて実行（CI相当）
uv run pytest tests/ -m "not docker and not slow"

# docker テストだけ実行
uv run pytest tests/ -m "docker"

# slow テストだけ実行（週次レビュー等）
uv run pytest tests/ -m "slow"

# Docker コンテナ内でテスト実行（docker マーク付きは skipif で自動除外）
make test  # MakefileでDocker実行に切り替え後
```

---

## チェックリスト

新しいマークを追加するとき:

- [ ] `pyproject.toml` の `markers` に登録した（`--strict-markers` でエラーにならないか確認）
- [ ] マーク名が「何を必要とするか」を示している（実装内容ではなく制約）
- [ ] `skipif` が必要な場合は条件式が正しい（`Path("/.dockerenv").exists()` 等）
- [ ] CI workflow で適切に除外または含めている
- [ ] ローカル開発用コマンド（Makefile 等）を更新した

---

## アンチパターン

| アンチパターン | 問題 | 代替策 |
|----------------|------|--------|
| `unit` / `e2e` という名前のマーク | 実装分類であり、実行可否の判断に使えない | `slow`, `docker`, `network` など制約ベースで命名 |
| `--strict-markers` なしでマーク使用 | タイポが検出されず、指定したマークが無視される | `addopts` に `--strict-markers` を追加 |
| skipif のみで CI 制御（`-m` なし） | テストが収集されるため実行時間が増加する | `-m "not docker"` で収集前に除外する |
| 全テストに `integration` マーク | CIでユニットテストも除外されてしまう | マークは「特別な条件が必要なもの」だけに付与 |
