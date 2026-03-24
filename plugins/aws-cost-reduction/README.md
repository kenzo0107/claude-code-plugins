# claude-plugins

Claude Code プラグイン集。

## プラグイン一覧

### aws-cost-reduction

複数リポジトリのオープン PR を取得し、優先度 (High / Medium / Low) を付与して一覧表示する。

#### インストール

```bash
# add marketplace
/plugin marketplace add https://github.com/kenzo0107/claude-plugins

# install plugin
/plugin install aws-cost-reduction@claude-code-plugins
```

#### 使い方

```bash
/aws-cost-reduction:generate ~/reports/clinpeer/info.md
```

### 前提条件

1. **AWS Cost Explorer MCP**: 本プラグインにより自動的にインストールされます。事前に AWS プロファイル `claude` を設定してください。

```bash
awsume <profile> -o claude
```

2. **Datadog MCP**: 対象組織の Datadog MCP をプロジェクトの `.mcp.json` で設定する必要があります。

```json
{
  "mcpServers": {
    "datadog-{org}": {
      "type": "http",
      "url": "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp"
    }
  }
}
```

3. **CloudWatch**（Datadog を利用しない場合）: 本プラグインにより `aws-cw` として自動的にインストールされます。info.md から `# Datadog` セクションを削除すると、このモードで動作します。
