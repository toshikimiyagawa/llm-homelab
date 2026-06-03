# Spec: issue-52-resolver

## Intent

`llm01` の通常 resolver で `open-webui.solvelio.com` を解決できるようにし、#20 の AC5 を通常の `curl -kI https://open-webui.solvelio.com` で確認可能にする。

## Scope

### Include

- systemd-resolved に `solvelio.com` 専用の public DNS route を追加する Ansible 管理
- `llm01` への適用
- `open-webui.solvelio.com` の通常名前解決と HTTPS 応答確認

### Exclude

- ルーター `192.168.0.1` の設定変更
- Cloudflare DNS record の追加変更
- Open WebUI / Ollama / vLLM の構成変更

## Acceptance Criteria

1. common role が systemd-resolved drop-in `/etc/systemd/resolved.conf.d/solvelio.conf` を管理する。
2. drop-in は `solvelio.com` を public resolver に route し、ルーター DNS の空応答を回避する。
3. `llm01` で `getent hosts open-webui.solvelio.com` が `100.107.191.51` を返す。
4. `llm01` で `curl -kI https://open-webui.solvelio.com` が HTTP success/redirect を返す。
5. system playbook の再実行が冪等である。
6. 変更ファイルの lint/syntax/static tests が通る。
