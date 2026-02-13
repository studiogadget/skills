# Before/After 実例集

記事から抽出した具体的な改善例。

## 1. 表面上の改善

### 1-1. 名前で情報を伝える

**Before**:
```python
def get(v, t):
    return fetch(v, timeout=t)
```

**After**:
```python
def fetch_user_profile(url: str, timeout_ms: int):
    return fetch(url, timeout=timeout_ms)
```

**改善点**:
- 関数名が具体的（`get` → `fetch_user_profile`）
- 引数名が明確（`v` → `url`, `t` → `timeout_ms`）
- 単位を明示（`timeout_ms`）

### 1-2. 誤解されない名前にする

**Before**:
```python
from dataclasses import dataclass

@dataclass
class User:
    age: int

def filter_users(users: list[User]) -> list[User]:
    return [u for u in users if u.age >= 20]

disable_notification = False
```

**After**:
```python
from dataclasses import dataclass

@dataclass
class User:
    age: int

def get_adult_users(users: list[User]) -> list[User]:
    return [u for u in users if u.age >= 20]

is_notification_enabled = True
```

**改善点**:
- 関数名がフィルタ条件を明示（`filter_users` → `get_adult_users`）
- ブール値を肯定形に（`disable_notification` → `is_notification_enabled`）
- 否定の二重否定を回避（`not disable_notification` → `is_notification_enabled`）

### 1-3. 美的配慮で読み順を固定する

**Before**:
```python
user = repo.find_user(user_id)
if user:
    invoice = billing.create_invoice(user)
    notifier.send(user.email, invoice)
log = logger.bind(scope="checkout")
```

**After**:
```python
log = logger.bind(scope="checkout")
user = repo.find_user(user_id)
if user is None:
    return

invoice = billing.create_invoice(user)
notifier.send(user.email, invoice)
```

**改善点**:
- ログ初期化を先頭に移動
- 早期return でネストを削減
- 段落構造を固定（初期化 → 検証 → 処理）

### 1-4. コメントは「なぜ」を残す

**Before**:
```python
# ユーザーをソートする
users.sort(key=lambda u: u.created_at)
```

**After**:
```python
# 新規作成ユーザーを先に処理しないと、無料枠判定が過去データで誤作動するため昇順に固定する。
users.sort(key=lambda u: u.created_at)
```

**改善点**:
- 「何」ではなく「なぜ」を説明
- 業務背景を明示
- 将来の変更時に判断材料となる

## 2. ループとロジックの単純化

### 2-1. ネストより早期return

**Before**:
```python
def charge(user, amount: int) -> bool:
    if user:
        if amount > 0:
            if not user.is_banned:
                return payment.charge(user.id, amount)
    return False
```

**After**:
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

**改善点**:
- 失敗条件を先頭に集約
- ネストを削減（3段 → 0段）
- 各条件が独立してテストしやすい

### 2-2. 巨大な式は説明変数へ分割

**Before**:
```python
if (
    not user.is_deleted
    and (user.role == "admin" or user.team_id == doc.team_id)
    and not doc.is_archived
    and not (doc.visibility == "private" and not user.has_private_access)
):
    publish(doc)
```

**After**:
```python
is_active_user = not user.is_deleted
can_access_team_doc = user.role == "admin" or user.team_id == doc.team_id
is_publishable_doc = not doc.is_archived
is_blocked_by_private_rule = (
    doc.visibility == "private" and not user.has_private_access
)

if is_active_user and can_access_team_doc and is_publishable_doc and not is_blocked_by_private_rule:
    publish(doc)
```

**改善点**:
- 条件を意図ごとに命名
- 論理構造が明確
- 修正時に影響範囲を限定しやすい

### 2-3. 変数は少なく・狭く・不変に

**Before**:
```python
total = 0
i = 0
while i < len(items):
    item = items[i]
    total = total + item.price * item.count
    i += 1
return total
```

**After**:
```python
total = sum(item.price * item.count for item in items)
return total
```

**改善点**:
- 可変状態を削減（`total`, `i`, `item` → なし）
- 内包表記で意図を明確に
- ループ制御のバグを排除

## 3. コードの再構成

### 3-1. 一度に1つのことだけをする

**Before**:
```python
async def register(input_data):
    if "@" not in input_data.email:
        raise ValueError("invalid email")
    password_hash = await hash_password(input_data.password)
    user = await db.user.create(
        data={"email": input_data.email, "password_hash": password_hash}
    )
    await mailer.send_welcome_mail(user.email)
    metrics.increment("user_registered")
    return user
```

**After**:
```python
def validate_register_input(input_data) -> None:
    if "@" not in input_data.email:
        raise ValueError("invalid email")

async def create_user(input_data):
    password_hash = await hash_password(input_data.password)
    return await db.user.create(
        data={"email": input_data.email, "password_hash": password_hash}
    )

async def register(input_data):
    validate_register_input(input_data)
    user = await create_user(input_data)
    await mailer.send_welcome_mail(user.email)
    metrics.increment("user_registered")
    return user
```

**改善点**:
- 検証・作成・通知を分離
- 各関数が単一責任
- テストが狙い撃ちしやすい

### 3-2. 思考を言語化してから実装する

**平易な手順**:
1. 在庫がない商品は除外する
2. 割引対象なら割引価格を使う
3. 合計金額を計算する

**実装**:
```python
def calc_total(products) -> int:
    in_stock_products = [p for p in products if p.stock > 0]
    prices = [
        p.discount_price if p.is_discount_target else p.price
        for p in in_stock_products
    ]
    return sum(prices)
```

**改善点**:
- 手順とコードが1対1対応
- コメント不要で自己説明的
- 修正時に該当ステップを特定しやすい

### 3-3. 最も読みやすいコードは書かないコード

**Before（自前実装）**:
```python
def uniq_by_id(users):
    user_map = {}
    for user in users:
        user_map[user.id] = user
    result = []
    for user_id in user_map:
        result.append(user_map[user_id])
    return result
```

**After（標準機能を活用）**:
```python
def uniq_by_id(users):
    return list({u.id: u for u in users}.values())
```

**改善点**:
- 行数削減（9行 → 2行）
- バグの可能性削減
- 保守コスト削減

## 4. 選択トピック

### 4-1. テストコードも読みやすく

**Before**:
```python
def test_1():
    a = build_order(10000, True, "JP")
    r = calc_shipping(a)
    assert r == 0
```

**After**:
```python
def test_shipping_fee_is_free_for_member_domestic_order():
    # Arrange
    order = build_order(amount=10_000, is_member=True, country="JP")
    # Act
    shipping_fee = calc_shipping(order)
    # Assert
    assert shipping_fee == 0
```

**改善点**:
- テスト名が意図を示す
- AAA パターンで構造化
- 引数に名前を付けて明確化（`10000` → `amount=10_000`）
