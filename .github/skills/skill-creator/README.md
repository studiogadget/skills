# Skill Creator - GitHub Copilot 最適化版

このスキルは、GitHub Copilot 用の Agent Skills を新規作成・改修するためのガイドです。

## Claude 公式版からの主な改善点

### 1. コンテキスト制限への対応（柔軟な運用）
- **SKILL.md**: **200〜300行** を目標（必要に応じて400行まで許容）
- **参照ファイル**: **100行以内** を推奨（簡潔なリンク集等は柔軟に）
- **ファイル数**: **品質を損なわない範囲で最小化**（目安: 5〜8ファイル）
- **重要**: 必要な情報（公式リンク、ベストプラクティス等）まで削らない

### 2. description の強化
GitHub Copilot は description でスキルを選択するため、以下を明確化:
- 「〜する際に使用」で用途を明示
- トリガーワード（ユーザーが使いそうな言葉）を含める
- 3〜5行で完結させる

**例**:
```yaml
description: |-
  GitHub Copilot用のスキルを新規作成・改修する際に使用。
  「新しいスキルを作りたい」「既存スキルを改善したい」という依頼で起動。
  要件ヒアリング→設計→実装→検証の流れで進める。
  コンテキスト制限を考慮した簡潔な設計を重視。
```

### 3. instructions との棲み分け明確化
- **instructions**: プロジェクト全体に常に適用される規約・ルール
- **skills**: 特定のタスク・作業に必要なワークフロー・知識

スキルに入れないもの:
- コーディング規約（instructions で管理）
- プロジェクト構造の説明
- Git/PR の一般的なルール

### 4. ワークフローの簡潔化
- 各ステップは **1〜2行** で記述
- 複雑な判断は別の参照ファイルに分離
- コード例は **10行以内** を推奨

### 5. テストとチェックリストの追加
作成後の確認項目:
- [ ] description がトリガー条件を明確に示している
- [ ] SKILL.md が 200〜300行以内
- [ ] 手順に曖昧な表現がない
- [ ] コード例が実際に動く
- [ ] references ファイルが本当に必要か

## 使い方

### 1. スキル作成の開始
```bash
python .github/skills/skill-creator/scripts/init_skill.py <skill-name> --path .github/skills
```

### 2. ユーザーへのヒアリング
以下の質問で要件を明確化:

**必須確認項目**:
- このスキルで扱いたい対象は何ですか？
- ユーザーはどんな言い方で依頼しますか？
- スキルが"やらないこと"は何ですか？
- 入力として必要な情報は何ですか？
- 出力（成果物）は何ですか？

**GitHub Copilot 特有の確認項目**:
- 既存の instructions ファイルと重複する内容はありませんか？
- このスキルは単発タスクですか、それとも複数ステップですか？
- ワークスペースの特定のファイル/フォルダに依存しますか？

### 3. スキル実装
1. **最新情報の収集**（Web検索で公式ドキュメント、llms.txt 確認）
2. **references 作成**:
   - `docs_links.md`: 公式ドキュメントリンク集（必須）
   - `best_practices.md`: ベストプラクティス（推奨）
   - `api_reference.md`: API概要（必要に応じて）
3. **scripts 作成**（複数サンプル推奨）:
   - `basic_example.py`: 基本的な使い方
   - `advanced_example.py`: 高度な使い方
   - `test_example.py`: テスト統合例
4. **SKILL.md 作成**:
   - description を最優先で作成（トリガー条件を明確に）
   - 手順を簡潔に記述（各ステップ1〜2行）
5. チェックリストで最終確認

### 4. 検証
```bash
python .github/skills/skill-creator/scripts/quick_validate.py .github/skills/<skill-name>
```

## ファイル構成

```
skill-creator/
├── SKILL.md                  # メインガイド（GitHub Copilot 最適化版）
├── README.md                 # このファイル
├── LICENSE.txt              # Apache-2.0
├── references/
│   ├── output-patterns.md   # 出力形式のテンプレ
│   └── workflows.md         # ワークフロー設計パターン
└── scripts/
    ├── init_skill.py        # スキル雛形生成
    ├── quick_validate.py    # 構造検証
    └── package_skill.py     # パッケージ化
```

## GitHub Copilot 特有のベストプラクティス

### コンテキスト最適化（実用性とのバランス）
- SKILL.md は 200〜300行を目標（必要に応じて400行まで）
- 参照ファイルは簡潔に（リンク集等は短く、実例は適度に）
- ファイル数は品質を損なわない範囲で最小化
- コード例: 短い例は本文に、長い例は scripts に
- **重要な参照資料は省略しない**（docs_links.md, best_practices.md 等）

### description の書き方
```yaml
# ✅ 良い例
description: |-
  GitHub Actionsワークフローを新規作成・修正する際に使用。
  「CIを追加したい」「ワークフローを最適化したい」という依頼で起動。
  ワークフロー設計→YAMLテンプレ適用→バリデーションの流れで進める。

# ❌ 悪い例
description: GitHub Actionsを扱うスキル
```

### 簡潔さの徹底
- 各セクションは 5〜10行以内を目標
- 「適切に」「必要に応じて」等の曖昧な表現を避ける
- コード例は最小限（長い例は scripts に分離）

## ライセンス

Apache-2.0（詳細は [LICENSE.txt](LICENSE.txt) を参照）
