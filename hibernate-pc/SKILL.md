---
name: hibernate-pc
description: "Put PC into hibernation after agent work completes. Use when: long-running tasks finish unattended, want PC to sleep after build/test/deploy. Windows only. Manual activation required."
user-invocable: true
disable-model-invocation: true
---

# Hibernate PC After Work

## When to Use

- 長時間タスク（ビルド、テスト、デプロイ等）の完了後にPCを休止状態にしたいとき
- 手動で `/hibernate-pc` を呼び出したときのみ実行される

## Procedure

1. 現在進行中のタスクをすべて完了させる
2. 全作業が正常終了したことを確認する
3. ユーザーに作業完了サマリーを表示する
4. 以下のコマンドでPCを休止状態にする:

```powershell
shutdown /h
```

## Important Notes

- このスキルは `disable-model-invocation: true` により、明示的に呼び出さない限り実行されない
- 休止状態コマンドは作業の**最後のステップ**として実行すること
- エラーが発生した場合は休止状態にせず、ユーザーに報告すること
- 休止状態実行前に未保存の変更がないことを確認すること
