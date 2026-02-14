# 追加の使用例（VS Code Chat Export JSON）

## 例: 複数セッションをまとめて分析

```
ユーザー: 「Copilot Chat の履歴から繰り返しタスクを探して」
実行内容:
1) VS Code で対象セッションごとに `Chat: Export Chat...` を実行し、JSON を `exports/` に集約
2) `scripts/filter-vscode-chat-export.py` で縮約し、`/tmp/vscode-chat-filtered.jsonl` を作る
3) WHAT/HOW/FLOW の三軸でパターンを抽出し、頻度が高いものを候補として提示
4) ユーザーが上位のパターンを選択
5) 選択パターンに対応するスキルを生成
```

## 例: 時間範囲を指定した分析

```
ユーザー: 「過去30日分で繰り返しタスクを探して」
実行内容:
1) Export JSON を `exports/` に集約
2) 縮約スクリプトを `--days 30` で実行し、直近分だけに絞った JSONL を作る
3) 抽出結果を「スキル化推奨」「価値あり」に分けて提示
```
