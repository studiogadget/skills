---
name: cc-sdd-review-slice-stack
description: cc-sdd実装用統合ブランチのコミット群（ベースブランチとの差分）をreview slice単位のstacked PRに再構成する際に使用。「review sliceに分割」「stacked PRを作成」「PRをスタックして」「レビュー用にPRを分けて」「review slice stack」という依頼でトリガーする。dry-run（既定）でslice計画を提示し、apply指示で実際にブランチ・PRを作成する。
---

# cc-sdd Review Slice Stack

cc-sdd の `/kiro-impl` 実行後、統合ブランチのコミット群（ベースブランチとの差分）を、**現在の実装ブランチの履歴や内容を変更せず**に、新規 review trunk を起点とした stacked draft PR に再構成する。コミットが push 済みでも未 push でも動作する。

## 全体フロー（2 スキル連携）

1. **本スキル**: review slice 単位の stacked draft PR を作成
2. 人間が bottom PR から順にレビュー・マージ
3. **`cc-sdd-restack-after-merge`**: 下位 PR マージ後に上位 branch を restack
4. 条件を満たした PR は auto-merge を使用
5. 最後に review trunk → main の統合 PR で最終判断

## 前提条件

- cc-sdd 実装用統合ブランチで `/kiro-impl` を実行済み（コミットが push 済みでも未 push でも可）
- `gh auth status` と `gh repo view` が通ること
- git working tree が clean であること

## 実行モード

| モード | 説明 |
|---|---|
| **dry-run**（既定）| slice 計画を表示して停止。ブランチ・PR は作らない |
| **apply** | ユーザーが明示したときのみ実行。ブランチ作成・push・draft PR 作成 |

---

## Step 1: 現状認識

以下を確認し報告する。

```powershell
$implBranch = git branch --show-current
$defaultBranch = gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
$baseCommit = git merge-base HEAD "origin/$defaultBranch"
$commitCount = git rev-list --count "$baseCommit..HEAD"
$targetCommits = git log --oneline "$baseCommit..HEAD"
```

**方針**: 現在ブランチ（`$implBranch`）には commit、rebase、reset を行わない。`$baseCommit` から新規 review trunk を作成し、対象コミット（`$baseCommit..HEAD`）を cherry-pick して stacked PR に再構成する。

**停止条件**: `$targetCommits` が空（ベースブランチとの差分コミットがない）の場合は停止して報告する。

## Step 2: tasks.md の特定

### candidate の発見

以下のパターンで検索する。

- `docs/specs/**/tasks.md`
- `**/.kiro/specs/**/tasks.md`

### primary tasks.md の選定

candidate が複数ある場合、以下の証拠でスコアリングする。

| 証拠 | 内容 |
|---|---|
| 会話文脈 | 依頼文の機能名・ブランチ名・タスク番号 |
| commit 一致 | commit message の語彙と task title の一致 |
| ブランチ名 | 現在ブランチ名と spec ディレクトリの近さ |
| 更新日時 | 最近更新された spec ディレクトリを優先 |

- 1位と2位の差が十分大きい場合のみ自動決定
- 差が小さい場合は候補一覧を理由つきで表示して停止

### task graph の構築

primary tasks.md から以下を抽出する。

- task id / title / subtask ids
- `Depends:` → 依存関係
- `Boundary:` → アーキテクチャ領域
- `Requirements:` → 契約・目的

## Step 3: commit → task マッピング

```powershell
git log --reverse --format="%H %s" "$baseCommit..HEAD"
```

### マッピング優先順

1. commit message 中の明示 task ID（`1.1`, `Task 1.1`, `[1.1]` 等）
2. title / keyword 一致
3. changed files と boundary の一致
4. depends 近傍 task との整合

### フォールバック: task ID 不明の場合

commit message から task を判断できない場合は以下を仮定する。

- **1 task = 1 commit**
- **若い番号の task から順にコミットされている**
- task 数と commit 数が一致しない場合は dry-run で報告して停止

### 停止条件

- unresolved（割り当て不能）な commit がある場合、apply に進まない
- ambiguous（複数 task に該当）な commit がある場合、候補を表示して停止

## Step 4: review slice の推論

### フォールバック: 少タスク時

task 数が 1〜2 の場合は stacked PR にせず、通常の 1 PR として作成する。
この場合 Step 4〜5 の slice 推論はスキップし、直接 Step 6 の apply（単一 PR）に進む。

### 基本ルール

- target slice 数は **3〜7** を目安（task 数・diff 量で増減可）
- 依存が強い task は同じ slice に寄せる
- 同じ boundary の task は同じ slice 候補
- 同じファイル領域を触る task は同じ slice 候補
- cross-cutting task は最も密接な slice に吸収する

### 同じ slice にまとめやすい task

- 直接依存している
- 同一 boundary / 同一 API 契約
- 変更ファイルが大きく重なる

### 別 slice にしやすい task

- UI と backend のように責務が違う
- setup / docs / validation のように本体と切り分けやすい
- reviewer の観点が大きく変わる

### slice 推論手順

1. commit → task mapping をもとに task graph を構築
2. boundary / depends / changed files の類似度で task をクラスタリング
3. reviewer 観点で不自然なクラスタを分割 / 結合
4. slice 順序は dependency order を守る
5. 各 slice に review focus（2〜5 個）を生成

### confidence

| レベル | 条件 |
|---|---|
| high | primary tasks.md が明確、commit → task がほぼ一意 |
| medium | tasks.md は妥当だが一部 commit の割り当てが推定 |
| low | tasks.md 選定または commit 割り当てに曖昧さが大きい |

**confidence が low の場合は apply に進まず dry-run で停止する。**

## Step 5: dry-run 出力

以下を必ず表示する。

### A. primary tasks.md 候補
- path / score / 選定理由 / 落選理由

### B. commit → task mapping
- commit hash / task id / reason / confidence

### C. proposed review slices
- slice key / title / included tasks / included commits / review focus / grouping 理由

### D. branch 計画
- 現在ブランチ: `<impl_branch>`（変更なし）
- review trunk（新規）: `review/<impl_branch>/trunk`
- slice branches: `review/<impl_branch>/01-<slice-key>` ...

### E. 停止条件（該当する場合）
- unresolved commits / ambiguous tasks

## Step 6: apply（ユーザー明示時のみ）

### 6.1 現在ブランチの保持確認

現在ブランチ（`$implBranch`）の履歴や内容は以降の操作で変更しない。
ベースブランチとの差分コミット一覧を確認する。

```powershell
git log --oneline "$baseCommit..HEAD"
```

### 6.2 review trunk の新規作成

`$baseCommit`（`$defaultBranch` との merge-base）から新規 review trunk を作成する。以降の checkout は作業位置を切り替えるためだけに行い、`$implBranch` 自体は変更しない。

```powershell
$reviewTrunk = "review/${implBranch}/trunk"
git checkout -b $reviewTrunk $baseCommit
```

### 6.3 slice branch 作成と cherry-pick

slice 順に branch を積む。

```powershell
# slice 01 (base: review/${implBranch}/trunk)
git checkout -b "review/${implBranch}/01-<slice-key>"
git cherry-pick <commit1> <commit2> ...

# slice 02 (base: review/${implBranch}/01-<slice-key>)
git checkout -b "review/${implBranch}/02-<slice-key>"
git cherry-pick <commit3> ...
```

**conflict 発生時は、解決方法が明確な場合に限り解消して継続する。** 片側の変更を採用すれば整合する場合、rename 追従のみの場合、generated file の再生成で整合する場合など、判断根拠を説明できるケースに限る。

- conflict を解消したら `git add <file>` の後に `git cherry-pick --continue` で継続する
- conflict を解消して進めた場合は、対象ファイル・採用した解決内容・判断根拠を Step 7 で必ず報告する

**解決方針が不明確な場合のみ停止する。** 停止時は以下を報告して手動解決を求める。

- conflict のあるファイル一覧（`git diff --name-only --diff-filter=U`）
- conflict 内容の要約
- 提示可能な解決方法と判断根拠

### 6.4 軽量検証

各 slice 作成後に以下を実行。

- 変更ファイル一覧の確認
- 代表テスト（`make test` 等）の実行
- 失敗時は PR を作らず停止

### 6.5 push と draft PR 作成

```powershell
# 各 slice branch を push
git push origin "review/${implBranch}/01-<slice-key>"

# draft PR 作成
gh pr create --draft `
  --base "<base-branch>" `
  --head "review/${implBranch}/01-<slice-key>" `
  --title "[Slice 1/N] <slice title>" `
  --body-file pr_body.md
```

- bottom PR の base は review trunk
- それ以外の PR の base はひとつ下の slice branch
- すべて draft で作成

### PR テンプレートの選択

```powershell
$templateDir = ".github/PULL_REQUEST_TEMPLATE"
$templates = @(Get-ChildItem $templateDir -Filter "*.md" -ErrorAction SilentlyContinue)
if ($templates.Count -eq 1) {
    # 1つのみ → 無確認で使用
    $templateContent = Get-Content $templates[0].FullName -Raw
} elseif ($templates.Count -gt 1) {
    # 複数あり → ユーザーにどれを使用するか確認してから続行
}
# テンプレートなし → body をそのまま生成
```

### PR body に含める内容

PR body の先頭には選択したテンプレートの内容（存在する場合）を記載し、続けて以下を含める。

- Selected tasks.md（パス）
- Included task ids
- Included commits（short hash）
- Review focus
- Dependency / base branch
- Confidence
- Validation 結果
- 「元の統合ブランチから review 用に再構成した PR です。bottom から順にレビューしてください」

### 6.6 統合 PR の作成

すべての slice PR 作成後、review trunk → `$defaultBranch` の統合 PR を作成する。

```powershell
git push origin $reviewTrunk
gh pr create --draft `
  --base "$defaultBranch" `
  --head "$reviewTrunk" `
  --title "Integration: <feature-name>" `
  --body-file integration_pr_body.md
```

この PR は全 slice がマージされた後に最終判断用として使う。body には全 slice PR の一覧とレビュー順を記載する。

## Step 7: 最終報告

以下を一覧で出力する。

- selected primary tasks.md と選定理由
- confidence
- 現在ブランチ名（変更なし）
- review trunk branch 名（新規作成）
- 作成した slice branches
- conflict を解消して進めた slice があれば、その解決内容（対象ファイル / 採用した変更 / 判断根拠）
- 作成した draft PR URL（slice + 統合）
- レビュー順（bottom → top、最後に統合 PR）
- unresolved / ambiguous commit 一覧（残っていれば）

### レビュー後の次ステップ

1. 人間が bottom PR からレビューし、承認後にマージ
2. 下位 PR マージ後、`cc-sdd-restack-after-merge` を実行して上位 branch を restack
3. 条件を満たした PR は auto-merge を有効化
4. 全 slice マージ後、統合 PR で最終判断

---

## 禁止事項

- 現在ブランチ（`$implBranch`）の履歴や内容を変更すること
- tasks.md 候補が僅差なのに勝手に 1 つに決めること
- task ID が曖昧な commit を勝手に slice に振り分けること
- pushed branch に対して無断で history rewrite すること
- confidence が low のまま apply に進むこと
- 解決方針が不明確な conflict を推測で解決して進めること
