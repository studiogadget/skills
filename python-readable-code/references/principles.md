# リーダブルコード原則の詳細

## なぜ今、リーダブルコードが再重要化するのか

AI駆動開発では、コード生成コストが下がる一方で、次のコストが相対的に上がる:

- **理解コスト**: 意図・前提・境界条件の把握
- **検証コスト**: 仕様適合、例外系、副作用の確認
- **修正コスト**: 将来変更時の影響範囲の見積もり

**ボトルネックは「書く」から「理解して判断する」に移っている**

## 1. 表面上の改善（第2章〜第6章）

### 1-1. 名前で情報を伝える（第2章）

**原則**: 名前は最も重要なドキュメント

**チェックポイント**:
- 単位が必要な値（時間・距離・金額）は必ず名前に含める
  - `timeout_ms`, `distance_km`, `price_jpy`
- 境界条件を明示
  - `min_length` (>= か > か?)
  - `max_retries` (inclusive or exclusive?)
- 意図を名前に埋め込む
  - `fetch_user_profile` (何を取得？)
  - `validate_email_format` (何を検証？)

**AI時代の注意点**:
- 生成コードは短名になりがち (`v`, `t`, `data`)
- 呼び出し側が読んだ瞬間に意味が立つ名前へ寄せる
- 単位明示は事故予防コストを激減させる

### 1-2. 誤解されない名前にする（第3章）

**原則**: 「他の意味に取られない」ことを優先

**NG例**:
```python
disable_notification = False  # True/False が直感的に逆
filter_users(users)  # 何を基準にフィルタ？
```

**OK例**:
```python
is_notification_enabled = True  # 肯定形で思考の反転を避ける
get_adult_users(users)  # フィルタ条件を名前で明示
```

**AI時代の注意点**:
- 曖昧な命名は、次のAI修正でも曖昧さを再生産しやすい
- ブール否定は「人間にもAIにも」条件反転ミスの温床
- 命名段階で誤解可能性を潰すと、後工程の指示精度が上がる

### 1-3. 美的配慮で読み順を固定する（第4章）

**原則**: 一貫したレイアウトは認知負荷を下げる

**推奨構造**:
```python
# 1. ログ・コンテキスト初期化
log = logger.bind(scope="checkout")

# 2. 入力取得
user = repo.find_user(user_id)

# 3. 検証・早期return
if user is None:
    return

# 4. 処理
invoice = billing.create_invoice(user)

# 5. 通知・副作用
notifier.send(user.email, invoice)
```

**AI時代の注意点**:
- 人間レビューは「形のパターン認識」で高速化される
- 一貫した段落構造は、生成コードの混在でも追跡しやすい
- 読み順の固定は、修正指示（「この段落だけ変える」）もしやすくする

### 1-4. コメントは「なぜ」を残す（第5章・第6章）

**原則**: コードは「何」を説明、コメントは「なぜ」を説明

**書くべきコメント**:
- 業務背景・判断理由
- 注意事項・罠（gotcha）
- TODO（いつまでに・誰が・なぜ）

**書かないコメント**:
- コードで明らかな「何」
- 古い情報・リンク切れ
- コードと矛盾する内容

**例**:
```python
# NG: ユーザーをソートする
users.sort(key=lambda u: u.created_at)

# OK: 新規作成ユーザーを先に処理しないと、無料枠判定が過去データで誤作動するため昇順に固定
users.sort(key=lambda u: u.created_at)
```

**AI時代の注意点**:
- AIはコードは読めても、業務背景までは持っていないことが多い
- 変更理由が明確だと、AIへの追加指示も短く正確に書ける

## 2. ループとロジックの単純化（第7章〜第9章）

### 2-1. ネストより早期return（第7章）

**原則**: 失敗条件を先に処理してネストを減らす

**効果**:
- 深いネストは、レビュー時の思考スタックを圧迫する
- 失敗条件を先に返すと、AIへの修正依頼の粒度も揃う
- 可読な制御フローは、テストケース作成の漏れも減らす

**パターン**:
```python
# Before: ネストが深い
def charge(user, amount: int) -> bool:
    if user:
        if amount > 0:
            if not user.is_banned:
                return payment.charge(user.id, amount)
    return False

# After: 早期return
def charge(user, amount: int) -> bool:
    if user is None:
        return False
    if amount <= 0:
        return False
    if user.is_banned:
        return False
    return payment.charge(user.id, amount)
```

### 2-2. 巨大な式は説明変数へ分割（第8章）

**原則**: 複雑な条件式は、意図ごとに名前を付けて分割

**効果**:
- 分割命名は「意図をコード内に埋める」行為
- 人間レビューでもAIレビューでも、どの条件が怪しいかを局所化できる
- ロジック変更時に影響点を限定しやすい

**パターン**:
```python
# Before: 1行に詰め込み
if (not user.is_deleted and (user.role == "admin" or user.team_id == doc.team_id)
    and not doc.is_archived and not (doc.visibility == "private" and not user.has_private_access)):
    publish(doc)

# After: 説明変数で分割
is_active_user = not user.is_deleted
can_access_team_doc = user.role == "admin" or user.team_id == doc.team_id
is_publishable_doc = not doc.is_archived
is_blocked_by_private_rule = doc.visibility == "private" and not user.has_private_access

if is_active_user and can_access_team_doc and is_publishable_doc and not is_blocked_by_private_rule:
    publish(doc)
```

### 2-3. 変数は少なく・狭く・不変に（第9章）

**原則**: 可変状態の最小化

**チェックポイント**:
- スコープを狭く: 必要な場所でのみ定義
- 不変化: 再代入を避ける
- 内包表記活用: `for` ループより `sum(... for ...)`

**効果**:
- 追跡すべき可変状態が少ないほど、レビューとデバッグが速い
- 不要な再代入を減らすと、AIの追加変更による副作用も起きにくい

**パターン**:
```python
# Before: 可変状態が多い
total = 0
i = 0
while i < len(items):
    item = items[i]
    total = total + item.price * item.count
    i += 1
return total

# After: 不変・内包表記
return sum(item.price * item.count for item in items)
```

## 3. コードの再構成（第10章〜第13章）

### 3-1. 一度に1つのことだけをする（第10章・第11章）

**原則**: 関数は単一責任

**効果**:
- 職務分離された関数は、AIへの指示単位として扱いやすい
- 「検証だけ直す」「通知だけ差し替える」が安全にできる
- テストが狙い撃ちしやすくなる

**パターン**:
```python
# Before: 1関数に複数責務
async def register(input_data):
    if "@" not in input_data.email:
        raise ValueError("invalid email")
    password_hash = await hash_password(input_data.password)
    user = await db.user.create(...)
    await mailer.send_welcome_mail(user.email)
    metrics.increment("user_registered")
    return user

# After: 責務ごとに分割
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

### 3-2. 思考を言語化してから実装する（第12章）

**原則**: 人間向け手順を先に書く → その通りに実装する

**効果**:
- 人間向け手順を先に書くと、AIへのプロンプト品質も上がる
- 説明とコードの段階を一致させると、差分レビューが速くなる

**パターン**:
```python
# 1. 平易な手順を書く
# 1. 在庫がない商品は除外する
# 2. 割引対象なら割引価格を使う
# 3. 合計金額を計算する

# 2. 手順通りに実装
def calc_total(products) -> int:
    in_stock_products = [p for p in products if p.stock > 0]
    prices = [
        p.discount_price if p.is_discount_target else p.price
        for p in in_stock_products
    ]
    return sum(prices)
```

### 3-3. 最も読みやすいコードは書かないコード（第13章）

**原則**: 書ける ≠ 書くべき

**チェックポイント**:
- 標準ライブラリ・組み込み機能で置き換え可能か？
- 自前実装のメンテコストは正当化できるか？
- 「いつか使うかも」で残していないか？

**効果**:
- 生成可能なコード量が増えた時代ほど、不要実装は増えやすい
- 「書ける」ではなく「持つべきか」で判断する

**パターン**:
```python
# Before: 自前実装
def uniq_by_id(users):
    user_map = {}
    for user in users:
        user_map[user.id] = user
    result = []
    for user_id in user_map:
        result.append(user_map[user_id])
    return result

# After: 標準機能活用
def uniq_by_id(users):
    return list({u.id: u for u in users}.values())
```

## 4. 選択トピック（第14章・第15章）

### 4-1. テストコードも読みやすく（第14章）

**原則**: テストも本番コードと同じ基準で書く

**チェックポイント**:
- テスト名は意図を示す（`test_1` → `test_shipping_fee_is_free_for_member_domestic_order`）
- AAA パターン（Arrange / Act / Assert）で構造化
- マジックナンバー避ける（`amount=10_000`, `is_member=True`）

**効果**:
- テスト名は「意図のラベル」であり、将来の検索キーになる
- 構造化されたテストは、AIによる追加ケース生成も安定しやすい

### 4-2. 設計は比較して選ぶ（第15章）

**原則**: 同じ要件でも、設計案を複数比較して選ぶ

**比較基準**:
- 可読性（理解時間）
- 性能（計算量・メモリ）
- 保守性（変更容易性）

**AI時代の注意点**:
- AIが候補を複数出せる時代だからこそ、比較基準を人間側で持つ
