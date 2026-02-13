---
name: python-readable-code
description: Pythonコードのリーダブルコード原則に基づくレビュー・改善・リファクタリングを行う際に使用。「コードレビュー」「コードを読みやすくして」「リーダブルコードの観点でチェック」「命名を改善して」「保守性を向上」「可読性を改善」「リファクタリング」「ベストプラクティスを適用」という依頼で起動。AI駆動開発時代における「理解速度最大化」を重視し、命名・制御フロー・コメント・構造・責務分離の改善を提案。
---

# Python Readable Code

## 概要

『リーダブルコード』の原則に基づき、Pythonコードの可読性を向上させる。AI駆動開発での「理解速度」を最大化する改善を提案する。

## 最重要原則

**「他人が理解するまでの時間」を最小化する**

- 「他人」= 未来の自分・チームメンバー・レビュー担当者・AI
- AI は生成を速めるが、理解責任は人間のチームにある
- ボトルネックは「書く」から「理解して判断する」に移っている

## 作業手順

コードレビュー・改善は次の順で進める:

1. **表面（命名・見た目）**: 名前・コメント・整形をチェック
2. **制御フロー**: ネスト・分岐・式の複雑さをチェック
3. **構造（責務）**: 関数分割・重複・不要コードをチェック
4. **改善提案**: Before/After で具体的な変更を示す

## チェックポイント（4カテゴリ）

### 1. 表面上の改善（名前・見た目・コメント）

#### 1-1. 名前で情報を伝える

- **単位を明示**: `timeout_ms`, `age_years`, `size_bytes`
- **境界を明示**: `get_adult_users` (>= 20), `is_valid_email`
- **意図を名前に**: `fetch_user_profile` (何を取得するか明確に)
- **避ける**: 短すぎる名前 (`v`, `t`, `get`)

#### 1-2. 誤解されない名前にする

- **ブール値は肯定形**: `is_enabled` (not `disable_flag`)
- **フィルタ系は具体的に**: `get_adult_users` (not `filter_users`)
- **境界条件を明確に**: `min_length` (>= or >?)

#### 1-3. 美的配慮で読み順を固定する

- **段落構造**: 変数定義 → 検証 → 処理 → 通知/ログ
- **早期return**: 失敗条件を先に処理してネストを減らす
- **一貫性**: 同じパターンを繰り返す

#### 1-4. コメントは「なぜ」を残す

- **書く**: 業務背景・判断理由・注意事項
- **書かない**: 「何をしているか」（コードで明らか）
- **例**: `# 新規ユーザーを先に処理しないと無料枠判定が誤作動するため昇順固定`

### 2. ループとロジックの単純化

#### 2-1. ネストより早期return

**NG**:
```python
def charge(user, amount: int) -> bool:
    if user:
        if amount > 0:
            if not user.is_banned:
                return payment.charge(user.id, amount)
    return False
```

**OK**:
```python
def charge(user, amount: int) -> bool:
    if user is None:
        return False
    if amount <= 0:
        return False
    if user.is_banned:
        return False
    return payment.charge(user.id, amount)
```

#### 2-2. 巨大な式は説明変数へ分割

**NG**: 複数条件を1行に詰め込む

**OK**:
```python
is_active_user = not user.is_deleted
can_access_team_doc = user.role == "admin" or user.team_id == doc.team_id
is_publishable_doc = not doc.is_archived

if is_active_user and can_access_team_doc and is_publishable_doc:
    publish(doc)
```

#### 2-3. 変数は少なく・狭く・不変に

- **スコープを狭く**: 必要な場所でのみ定義
- **不変化**: 再代入を避ける（`final`, `const`相当の意識）
- **内包表記活用**: `for` ループより `sum(... for ...)` 等

### 3. コードの再構成

#### 3-1. 一度に1つのことだけをする

**NG**: 検証・作成・通知・メトリクスを1関数に混在

**OK**:
```python
def validate_register_input(input_data) -> None:
    if "@" not in input_data.email:
        raise ValueError("invalid email")

async def create_user(input_data):
    password_hash = await hash_password(input_data.password)
    return await db.user.create(...)

async def register(input_data):
    validate_register_input(input_data)
    user = await create_user(input_data)
    await mailer.send_welcome_mail(user.email)
    metrics.increment("user_registered")
    return user
```

#### 3-2. 思考を言語化してから実装する

1. 平易な手順（日本語）を書く
2. その手順通りに実装する
3. 段階と関数を対応させる

#### 3-3. 最も読みやすいコードは書かないコード

- **標準ライブラリ・組み込み機能を優先**
- **自前実装が本当に必要か検討**
- **例**: 辞書内包表記で重複排除 `{u.id: u for u in users}.values()`

### 4. テストコードも読みやすく

- **テスト名は意図を示す**: `test_shipping_fee_is_free_for_member_domestic_order`
- **AAA パターン**: Arrange / Act / Assert で構造化
- **マジックナンバー避ける**: `amount=10_000`, `is_member=True` 等

## AI 駆動開発での運用ルール（6原則）

チーム運用で即効性のある6原則:

1. **命名レビューを最優先** - 単位・境界・意図を名前で表現
2. **「なぜこの実装か」を必須化** - PR テンプレに組み込む
3. **早期return で分岐を平坦化**
4. **複雑条件は説明変数へ分割**
5. **1関数1責務を守る**
6. **「書かない選択」を毎回検討** - 標準機能で置き換え可能か

## レビューチェックリスト

以下の質問で素早くチェック:

- [ ] 初見の同僚が短時間で説明できるか？
- [ ] 名前だけで意味・単位・境界条件が伝わるか？
- [ ] 分岐と式は、頭の中で反転せずに追えるか？
- [ ] 変数は必要最小限で、スコープは狭く、不変化できているか？
- [ ] コメントは背景・意図・注意点を短く正確に伝えているか？
- [ ] そのコードは本当に必要か？ライブラリで置き換えられないか？

## 改善提案の出し方

1. **カテゴリを明示**: 「命名の改善」「制御フローの簡素化」等
2. **Before/After を示す**: コード全体ではなく該当箇所のみ
3. **理由を1行で**: 「未来の変更時に影響範囲を限定しやすい」等
4. **優先度**: 致命的 / 推奨 / 好み の3段階

## 同梱リソース

- `references/principles.md`: 各原則の詳細説明
- `references/before_after_examples.md`: Before/After 実例集（記事から抽出）
- `references/review_checklist.md`: 詳細レビューチェックリスト
