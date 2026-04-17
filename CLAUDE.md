# CLAUDE.md — idea-pipeline プロジェクトルール

このファイルに記載されたルールは、Claude Code がこのリポジトリで作業する際に**必ず**従うこと。

---

## 開発フロー

### 1. テスト駆動開発 (TDD)
- 新機能・バグ修正・リファクタリングのいずれでも、**実装前にテストを書く**
- `everything-claude-code:tdd-guide` スキルを積極的に使用すること
- テストは `tests/` 配下に配置し、`pytest tests/ -v` がパスした状態を維持する
- GitHub Actions の pipeline.yml はテストがパスしないとパイプラインを実行しない設計を守ること

### 2. フロントエンド開発
- UI の新規作成・大幅な変更には **`everything-claude-code:frontend-design` スキルを使用**すること
- 方向性を決めたらブレずに実行する（安全平均の UI は避ける）
- カードグリッドを安易に使わない — 現在のエディトリアルリスト形式を基準にする
- ライトモードがデフォルト、ダークモードトグルは常に動作させること
- デザイントークンは CSS 変数 (`--bg`, `--amber`, `--text` 等) で管理する

### 3. コードレビュー & セキュリティレビュー
- コードを変更したら必ず以下の 2 スキルを実行すること:
  - `everything-claude-code:code-reviewer`
  - `everything-claude-code:security-reviewer`
- CRITICAL / HIGH の指摘はマージ前に必ず解消する

---

## セキュリティ

- **API キーは絶対にコードにハードコードしない** — `ANTHROPIC_API_KEY` は GitHub Secrets のみ
- DB クエリはすべて `?` プレースホルダを使用する（SQL インジェクション防止）
- フロントエンドでユーザー入力を直接 HTML に渡さない（XSS 防止）
- `.env` ファイルは `.gitignore` に含まれており、コミットしないこと

---

## パイプライン設計

- `pipeline/` 各モジュールの関数は例外を内部で吸収し、空リストを返す（例外を外に伝播させない）
- Claude API の出力テキストフィールドはすべて**日本語**で生成する
  - `difficulty` / `category` は UI フィルタ用の英語 enum のまま維持する
- リサーチデータは 7 日より古いものを自動削除する設計を維持する
- `docs/data/ideas.json` と `docs/data/research.json` はパイプライン実行後に自動コミットされる — 手動編集しないこと
- `docs/data/meetings.json` は meeting.yml 実行後に自動コミットされる — 手動編集しないこと

---

## 会議システム設計

- `meeting/` 各モジュールの関数も例外を内部で吸収し、ログ出力して処理を継続する（例外を外に伝播させない）
- CEO エージェントの結論出力フォーマットは `結論: 採用` / `結論: 見送り` の完全フレーズ。部分一致で誤判定しないよう `_parse_conclusion()` は完全フレーズ検索を使うこと
- `github_issue_url` は `http`/`https` プロトコルのみ許可し、export 時（`_safe_url()`）と UI 表示時（`isSafeUrl()`）の両方で検証すること
- エージェントペルソナは `.claude/agents/*.md` に定義し、Python コードから system prompt として読み込む
- 対象アイデア条件: `eval_total >= 7.0` かつ `meeting_sessions` 未登録、スコア降順で最大 3 件/回

---

## Git ルール

- コミットは日本語または英語どちらでもよいが、内容を明確に記述する
- `data/ideas.db` と `docs/data/*.json` は意図的にリポジトリで管理する
- `public/data/` は `.gitignore` 対象 — コミットしないこと
- force push は行わない

---

## ページあたり件数（変更時は両方更新）

| 対象 | 件数 |
|---|---|
| アイデア | 20 件/ページ |
| リサーチ | 30 件/ページ |
