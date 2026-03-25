---
name: create-issue
description: 'GitHub Issueを作成してGitHubに投稿するスキル。「Issueを作成」「Issue作成」「Issueにして」「Issueとして投稿」「GitHubにIssue」「create issue」「open issue」「バグ報告」「機能追加をIssueに」「改善提案をIssueに」などの依頼でトリガーする。コンテキスト収集→Issue本文生成→ラベル存在確認・作成→gh issue create投稿の流れでIssueを作成する。'
---

# GitHub Issue 作成スキル

ユーザーが指定した内容（機能追加・バグ修正・改善提案など）について、構造化されたGitHub Issueを作成し `gh issue create` コマンドで投稿する。

## トリガー条件

- 「〇〇のIssueを作成して」
- 「〇〇をIssueにして」
- 「〇〇をGitHubにIssue投稿して」
- 「〇〇の改善提案をIssueにして」
- 「〇〇のバグをIssue報告して」
- 英語: "create issue for ○○", "open issue for ○○"

## ワークフロー（5ステップ）

### Step 1: コンテキスト収集

Issue の内容を充実させるため、以下を自律的に調査する。

**必須調査項目**:
1. **会話コンテキスト** — ユーザーとの直近の会話から、変更理由・背景・課題を抽出
2. **関連コード** — 変更対象ファイルの現状実装を確認（ファイルパス・行番号を特定）
3. **仕様書** — `docs/specs/` 配下の requirements.md, design.md（存在する場合）
4. **設定ファイル** — 関連する `config.yaml` のセクション

**判断が必要な場合のみユーザーに確認**:
- Issue の種別が不明確な場合（feature / fix / refactor）
- 影響範囲が曖昧な場合

### Step 2: Issue 本文の生成

[Issue テンプレート](./references/issue-template.md) に従って本文を生成する。

**生成ルール**:
- 言語: 日本語（コード・識別子は英語）
- WHY / WHAT / Acceptance Criteria を必ず含める
- 禁止語を使用しない: best / optimal / faster / always / never / perfect
- コード参照はファイルパス・行番号を明記する
- 疑似コードを含める場合は実装イメージが伝わる程度に簡潔に記載する
- secrets / PII を含めない
- 判断が必要な場合以外は確認なしで即座に実行すること

**ラベル選択ルール**:

| Issue 種別 | ラベル |
|---|---|
| 新機能 | `enhancement` |
| バグ修正 | `bug` |
| リファクタ | `refactor` |
| ドキュメント | `documentation` |
| テスト | `test` |
| 性能改善 | `performance` |

### Step 3: ラベルの存在確認と作成

投稿前に、使用するラベルがリポジトリに存在するか確認し、存在しない場合は作成する。

```powershell
# ラベルの存在確認
$labelExists = gh label list --json name --jq ".[].name" | Select-String -Quiet "^<label>$"

if (-not $labelExists) {
    # ラベルが存在しない場合は作成
    gh label create --force "<label>" --color "<color>"
}
```

**ラベルカラー対応表**:

| ラベル | カラー |
|---|---|
| `enhancement` | `#a2eeef` |
| `bug` | `#d73a4a` |
| `refactor` | `#e4e669` |
| `documentation` | `#0075ca` |
| `test` | `#bfd4f2` |
| `performance` | `#f9d0c4` |

### Step 4: gh CLI で投稿

1. Issue 本文を一時ファイル `issue_body.md` に書き出す
2. `gh issue create` コマンドで投稿する
3. 一時ファイルを削除する（2で失敗した場合も必ず実行すること）

```powershell
try {
    # 投稿コマンド
    gh issue create --title "<title>" --body-file issue_body.md --label "<label>"
}
finally {
    # クリーンアップ（成功・失敗にかかわらず実行）
    Remove-Item issue_body.md -ErrorAction SilentlyContinue
}
```

**タイトル形式**: `<type>(<scope>): <summary>`
- type: feat / fix / refactor / docs / test / chore / perf
- scope: 対象モジュール/機能の短縮名
- summary: 変更内容の要約（日本語可）

### Step 5: 結果報告

- 作成された Issue の URL を提示する
- Issue 内容の要点（WHY / WHAT / AC の概要）を箇条書きで要約する

## 注意事項

- `gh` CLI がインストール済みかつ認証済みであることを前提とする
- `gh` コマンドが失敗した場合は、エラー内容をユーザーに報告し対処法を提示する
- `gh` コマンドが失敗した場合も、`issue_body.md` は必ず削除すること（クリーンアップの徹底）
- PowerShell 環境でのヒアドキュメント（`@- << 'EOF'`）は非対応のため、一時ファイル経由で投稿する
