/// 内嵌 HTML 管理面板 — 单文件 SPA
pub const DASHBOARD_HTML: &str = r#"<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Windsurf Toolkit Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1e293b, #334155); padding: 20px 30px; border-bottom: 1px solid #475569; }
.header h1 { font-size: 24px; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header p { color: #94a3b8; margin-top: 4px; }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
.card h3 { font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.card .value { font-size: 32px; font-weight: 700; color: #f8fafc; }
.card .value.green { color: #4ade80; }
.card .value.yellow { color: #fbbf24; }
.card .value.red { color: #f87171; }
.keys-table { width: 100%; border-collapse: collapse; }
.keys-table th { text-align: left; padding: 12px; color: #94a3b8; border-bottom: 1px solid #334155; font-size: 13px; }
.keys-table td { padding: 12px; border-bottom: 1px solid #1e293b; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.badge.ok { background: #064e3b; color: #4ade80; }
.badge.err { background: #450a0a; color: #f87171; }
.badge.cool { background: #422006; color: #fbbf24; }
.section { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 24px; }
.section h2 { font-size: 18px; margin-bottom: 16px; color: #f1f5f9; }
.models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
.model-item { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; }
.model-item .name { font-weight: 600; font-size: 13px; }
.model-item .provider { font-size: 11px; color: #64748b; }
.refresh-btn { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.refresh-btn:hover { background: #2563eb; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
#log { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; height: 200px; overflow-y: auto; white-space: pre-wrap; color: #94a3b8; }
</style>
</head>
<body>
<div class="header">
  <h1>⚡ Windsurf Toolkit</h1>
  <p>OpenAI 兼容反代 · Key 管理 · 实时监控</p>
</div>
<div class="container">
  <div class="grid" id="stats"></div>

  <div class="section">
    <div class="toolbar">
      <h2>🔑 Key Pool</h2>
      <button class="refresh-btn" onclick="refresh()">刷新</button>
    </div>
    <table class="keys-table">
      <thead><tr><th>Key</th><th>状态</th><th>调用</th><th>错误</th><th>信息</th></tr></thead>
      <tbody id="keys-body"></tbody>
    </table>
  </div>

  <div class="section">
    <h2>🤖 可用模型</h2>
    <div class="models-grid" id="models"></div>
  </div>

  <div class="section">
    <h2>📋 请求日志</h2>
    <div id="log">等待请求...</div>
  </div>
</div>

<script>
const BASE = window.location.origin;

async function refresh() {
  try {
    // 状态
    const status = await (await fetch(BASE + '/v1/status')).json();
    document.getElementById('stats').innerHTML = `
      <div class="card"><h3>总 Key 数</h3><div class="value">${status.total}</div></div>
      <div class="card"><h3>可用</h3><div class="value green">${status.available}</div></div>
      <div class="card"><h3>不可用</h3><div class="value ${status.total - status.available > 0 ? 'red' : ''}">${status.total - status.available}</div></div>
    `;

    // Keys
    const tbody = document.getElementById('keys-body');
    tbody.innerHTML = status.keys.map(k => `
      <tr>
        <td><code>${k.key_preview}</code></td>
        <td><span class="badge ${k.available ? 'ok' : k.healthy ? 'cool' : 'err'}">${k.available ? '可用' : k.healthy ? '冷却中' : '不健康'}</span></td>
        <td>${k.total_calls}</td>
        <td>${k.total_errors}</td>
        <td style="color:#64748b;font-size:12px">${k.error_message || '-'}</td>
      </tr>
    `).join('');

    // 模型
    const models = await (await fetch(BASE + '/v1/models')).json();
    document.getElementById('models').innerHTML = models.data.map(m => `
      <div class="model-item">
        <div class="name">${m.id}</div>
        <div class="provider">${m.owned_by}</div>
      </div>
    `).join('');
  } catch(e) {
    console.error(e);
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"#;
