---
name: cc-sdd-restack-after-merge
description: stacked PRの下位PRがマージされた後に上位branchをrestack（rebase/cherry-pick再構成）する際に使用。「restackして」「上位PRを更新して」「restack after merge」「PRのbaseを更新」「スタックを整理」という依頼でトリガーする。対象sliceの特定→rebase→変更ファイル確認と代表テスト実行→force-with-leaseでpush→PR base更新→auto-merge判定の順で進める。
---

# cc-sdd Restack After Merge

`cc-sdd-review-slice-stack` で作成した stacked PR の下位 PR がマージされた後、上位 branch を rebase して PR の base を更新する。条件を満たした PR には auto-merge を設定する。

## 全体フロー内の位置

1. `cc-sdd-review-slice-stack`: stacked draft PR を作成
2. 人間が bottom PR をレビュー・マージ
3. **本スキル**: 上位 branch を restack、PR base 更新、auto-merge 設定
4. 2〜3 を繰り返す
5. 全 slice マージ後、統合 PR（review trunk → main）で最終判断

## 前提条件

- `cc-sdd-review-slice-stack` で作成した stacked PR が存在すること
- 少なくとも 1 つの下位 PR がマージ済みであること
- `gh auth status` が通ること
- git working tree が clean であること

---

## Step 1: 現状認識

```powershell
$implBranch = git branch --show-current
$defaultBranch = gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'

# review slice branch 一覧を取得
$reviewBranches = git branch -r --list "origin/review/*" | ForEach-Object { $_.Trim() }

# マージ済みPRとオープンPRの特定
$openPRs = gh pr list --json number,headRefName,baseRefName,state --jq '.[] | select(.headRefName | startswith("review/"))'
```

以下を報告する。
- review trunk branch 名
- 各 slice branch の状態（merged / open / draft）
- マージ済み slice の一覧
- 未マージ slice の一覧と現在の base

## Step 2: restack 対象の特定

マージ済みの直上にある未マージ slice branch を特定する。

```powershell
# 例: slice 01 がマージ済み → slice 02 の base が stale
# slice 02 の新しい base は review trunk（slice 01 のコミットがマージ済み）
```

| 条件 | 対象にする slice | 新しい base | 次の動作 |
|---|---|---|---|
| 最下位の未マージ slice の直下がマージ済み | その slice | review trunk | rebase を実行 |
| 直下の slice が未マージ | なし | 変更なし | その slice はスキップ |
| 複数 slice が連続でマージ済み | 連続区間の直上にある最初の未マージ slice | review trunk | その 1 つだけ rebase してから上位へ連鎖更新 |
| すべてマージ済み | なし | なし | 統合 PR の状態確認へ進む |

### restack 順序

- bottom から順に処理する
- 直下がまだマージされていない slice はスキップ
- 複数の slice が連続でマージ済みなら、その直上の 1 つだけ restack

## Step 3: rebase 実行

```powershell
# 対象 slice branch をチェックアウト
git fetch origin
git checkout "review/<impl_branch>/02-<slice-key>"

# 新しい base に rebase
git rebase "origin/review/<impl_branch>/trunk"
```

**conflict 発生時は停止する。** 以下を報告して手動解決を求める。
- conflict のあるファイル一覧
- conflict の内容（`git diff --name-only --diff-filter=U`）
- 推奨する解決方法

## Step 4: 軽量検証

rebase 後に以下を実行する。

- `git diff --name-only origin/<rebase前のbase>...HEAD` で変更ファイル一覧を確認
- 変更範囲に対応する代表テストを 1 つ以上実行する
- テスト候補が複数ある場合は、変更ファイルに最も近い unit test を優先し、候補がなければ関連 integration test か `make check-all` を実行する
- 検証に失敗した場合は push せず停止し、失敗したコマンドと要約だけを報告する

## Step 5: push と PR base 更新

```powershell
# rebase 後の branch を force push
git push origin "review/<impl_branch>/02-<slice-key>" --force-with-lease

# PR の base を更新（下位 branch → マージ先に変更）
gh pr edit <pr-number> --base "review/<impl_branch>/trunk"
```

**`--force-with-lease`** を使い、他者の push を上書きしないよう保護する。

### 上位 slice の連鎖更新

slice 02 の rebase 後、slice 03 以降も同様に処理する。

```powershell
# slice 03 の base を slice 02 に rebase
git checkout "review/<impl_branch>/03-<slice-key>"
git rebase "origin/review/<impl_branch>/02-<slice-key>"
git push origin "review/<impl_branch>/03-<slice-key>" --force-with-lease
```

全未マージ slice について bottom から順に繰り返す。

## Step 6: auto-merge 設定

以下の条件をすべて満たす PR に auto-merge を設定する。

### auto-merge 条件

- PR が draft でないこと（`gh pr ready` 済み）
- CI が通っていること
- レビュー承認済みであること

### 設定コマンド

```powershell
# 条件を確認
$pr = gh pr view <pr-number> --json isDraft,reviewDecision,statusCheckRollup
# isDraft: false, reviewDecision: APPROVED, checks: all passing

# auto-merge を有効化
gh pr merge <pr-number> --auto --squash
```

**条件を満たさない PR には auto-merge を設定しない。** 理由を報告する。

### auto-merge が設定できない場合

- リポジトリで auto-merge が無効の場合: Settings → General → Allow auto-merge の有効化が必要
- 必要な status checks が未設定の場合: branch protection rule の設定が必要
- **いずれの場合も手順を報告し、手動マージの代替手順を提示する**

## Step 7: 最終報告

以下を一覧で出力する。

- restack した slice branch 一覧
- 各 branch の rebase 結果（成功 / conflict）
- 更新した PR の base 変更内容
- auto-merge 設定結果（設定済み / 条件未達の理由）
- 残りの未マージ slice 一覧
- 次のアクション（「次のレビュー対象は Slice N です」等）

### 全 slice マージ完了時

全 slice がマージされた場合は追加で以下を報告する。

- 統合 PR（review trunk → `$defaultBranch`）の状態
- 統合 PR を ready にして最終レビューを依頼するかの確認

```powershell
# 統合 PR を ready に変更
gh pr ready <integration-pr-number>
```

---

## 禁止事項

- 現在ブランチ（`$implBranch`）の履歴を変更すること
- conflict を勝手に解決すること
- `--force-with-lease` なしで force push すること
- auto-merge 条件を満たさない PR に auto-merge を設定すること
- レビュー未承認の PR を ready にすること
