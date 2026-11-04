const API_BASE = "/api";

// 工具函数
async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function show(el, html) {
  el.innerHTML = html;
}

function setLoading(progressEl, resultEl, loading) {
  progressEl.classList.toggle("hidden", !loading);
  if (loading) resultEl.innerHTML = "";
}

function fmtGB(gb) {
  if (gb >= 1024) return (gb / 1024).toFixed(2) + " TB";
  return gb.toFixed(2) + " GB";
}

function badge(level, text) {
  return `<span class="badge ${level}">${text}</span>`;
}

// 标签切换
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document
      .querySelectorAll(".tab")
      .forEach((t) => t.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((c) => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
  });
});

// ============ 诊断 ============
document.getElementById("btn-scan").addEventListener("click", async () => {
  const btn = document.getElementById("btn-scan");
  const progress = document.getElementById("scan-progress");
  const result = document.getElementById("scan-result");
  const stage = document.getElementById("scan-stage");
  const bar = document.getElementById("scan-bar");
  const noDeep = document.getElementById("scan-no-deep").checked;
  const forceRefresh = document.getElementById("scan-force").checked;

  btn.disabled = true;
  progress.classList.remove("hidden");
  result.innerHTML = "";

  // 模拟阶段提示（后端一次性返回，前端按时序展示）
  const stages = noDeep
    ? ["扫描磁盘...", "读取环境变量...", "扫描已装软件...", "分析中..."]
    : [
        "扫描磁盘...",
        "读取环境变量...",
        "扫描已装软件...",
        "扫描目录占用（较慢）...",
        "扫描大文件...",
        "分析中...",
      ];
  let i = 0;
  const timer = setInterval(
    () => {
      if (i < stages.length) {
        stage.textContent = stages[i];
        bar.style.width = ((i + 1) / stages.length) * 90 + "%";
        i++;
      }
    },
    noDeep ? 800 : 3000,
  );

  try {
    const data = await api(
      `/scan?no_deep=${noDeep}&force_refresh=${forceRefresh}`,
      { method: "POST" },
    );
    clearInterval(timer);
    bar.style.width = "100%";
    stage.textContent = `完成（${data.elapsed_seconds.toFixed(1)}s${data.from_cache ? "，来自缓存" : ""}）`;
    setTimeout(() => progress.classList.add("hidden"), 800);
    renderScanResult(result, data);
  } catch (e) {
    clearInterval(timer);
    progress.classList.add("hidden");
    show(result, `<div class="error">扫描失败：${e.message}</div>`);
  } finally {
    btn.disabled = false;
  }
});

function renderScanResult(el, data) {
  const { snapshot, analysis } = data;
  let html = "";

  // 磁盘
  html += '<div class="card"><h2>磁盘现状</h2>';
  if (snapshot.disks.length > 0) {
    html +=
      "<table><thead><tr><th>盘符</th><th>卷标</th><th>总容量</th><th>可用</th><th>使用率</th><th>状态</th></tr></thead><tbody>";
    snapshot.disks.forEach((d) => {
      const level =
        d.used_percent >= 90
          ? "critical"
          : d.used_percent >= 75
            ? "warning"
            : "ok";
      const statusText =
        d.used_percent >= 90 ? "紧张" : d.used_percent >= 75 ? "注意" : "充足";
      html += `<tr>
        <td><strong>${d.letter}:</strong></td>
        <td>${d.label || "-"}</td>
        <td>${fmtGB(d.total_gb)}</td>
        <td>${fmtGB(d.free_gb)}</td>
        <td>
          <div>${d.used_percent.toFixed(1)}%</div>
          <div class="bar"><div class="bar-fill ${level}" style="width:${d.used_percent}%"></div></div>
        </td>
        <td>${badge(level, statusText)}</td>
      </tr>`;
    });
    html += "</tbody></table>";
  } else {
    html += "<p>未采集到磁盘信息。</p>";
  }
  html += "</div>";

  // 环境变量问题
  if (analysis.env_issues && analysis.env_issues.length > 0) {
    html += '<div class="card"><h2>环境变量问题</h2><ul>';
    analysis.env_issues.forEach((i) => (html += `<li>⚠️ ${i}</li>`));
    html += "</ul></div>";
  }

  // 错位软件
  if (analysis.misplaced && analysis.misplaced.length > 0) {
    html += '<div class="card"><h2>装在 C 盘的软件</h2>';
    html +=
      "<table><thead><tr><th>软件</th><th>当前位置</th><th>推荐位置</th></tr></thead><tbody>";
    analysis.misplaced.forEach((m) => {
      html += `<tr><td><strong>${m.software_name}</strong></td><td><code>${m.current_path}</code></td><td><code>${m.recommended_path}</code></td></tr>`;
    });
    html += "</tbody></table></div>";
  }

  // 目录占用
  if (snapshot.top_dirs && snapshot.top_dirs.length > 0) {
    html += '<div class="card"><h2>目录占用 Top N</h2>';
    html +=
      "<table><thead><tr><th>路径</th><th>大小</th><th>文件数</th></tr></thead><tbody>";
    snapshot.top_dirs.forEach((d) => {
      html += `<tr><td><code>${d.path}</code></td><td>${fmtGB(d.size_gb)}</td><td>${d.file_count}</td></tr>`;
    });
    html += "</tbody></table></div>";
  }

  // 已装软件统计
  const bySource = {};
  snapshot.installed.forEach((s) => {
    bySource[s.source] = (bySource[s.source] || 0) + 1;
  });
  html += '<div class="card"><h2>已安装软件</h2>';
  html += `<p>共 ${snapshot.installed.length} 个：</p><ul>`;
  Object.entries(bySource).forEach(([k, v]) => (html += `<li>${k}: ${v}</li>`));
  html += "</ul></div>";

  show(el, html);
}

// ============ 推荐 ============
document.getElementById("btn-recommend").addEventListener("click", async () => {
  const btn = document.getElementById("btn-recommend");
  const progress = document.getElementById("rec-progress");
  const result = document.getElementById("rec-result");
  const noDeep = document.getElementById("rec-no-deep").checked;
  const includeManual = document.getElementById("rec-include-manual").checked;

  btn.disabled = true;
  setLoading(progress, result, true);

  try {
    const data = await api(
      `/recommend?no_deep=${noDeep}&include_manual=${includeManual}&top=20`,
      { method: "POST" },
    );
    renderRecommendations(result, data);
  } catch (e) {
    show(result, `<div class="error">生成失败：${e.message}</div>`);
  } finally {
    btn.disabled = false;
    progress.classList.add("hidden");
  }
});

function renderRecommendations(el, data) {
  const recs = data.recommendations;

  if (recs.length === 0) {
    show(el, '<div class="card"><p>未发现需要处理的问题。</p></div>');
    return;
  }

  let html = `<div class="card"><h2>共 ${recs.length} 条推荐</h2>`;

  recs.forEach((rec) => {
    html += `<div class="rec-item ${rec.priority}">
      <div class="rec-header">
        <div class="rec-title">${rec.title}</div>
        ${badge(rec.priority, rec.priority)}
      </div>
      <div class="rec-meta">
        <span>类别：${rec.category}</span>
        <span>难度：${rec.difficulty}</span>
        <span>风险：${rec.risk}</span>
        ${rec.impact_gb > 0 ? `<span>释放：${fmtGB(rec.impact_gb)}</span>` : ""}
        <span>${rec.estimated_minutes} 分钟</span>
      </div>
      ${rec.reason ? `<p>${rec.reason}</p>` : ""}
      ${rec.conflict ? `<p style="color:#c0392b">⚠️ ${rec.conflict}</p>` : ""}
      <ol class="rec-steps">
        ${rec.steps
          .map(
            (s) => `<li>${s.description}${s.manual ? " <em>(手动)</em>" : ""}
          ${s.command ? `<pre><code>${s.command}</code></pre>` : ""}
          ${s.warning ? `<div style="color:#e67e22;font-size:13px">⚠️ ${s.warning}</div>` : ""}
        </li>`,
          )
          .join("")}
      </ol>
      <div class="rec-actions">
        <button class="btn secondary btn-sm" onclick="applyRec('${rec.id}', 'dry-run')">试运行</button>
        <button class="btn primary btn-sm" onclick="applyRec('${rec.id}', 'interactive')">执行</button>
      </div>
    </div>`;
  });

  html += "</div>";

  // 脚本
  html += `<div class="card"><h2>PowerShell 脚本</h2>
    <button class="btn secondary btn-sm" onclick="copyScript()">复制</button>
    <pre id="script-content"><code>${escapeHtml(data.script)}</code></pre>
  </div>`;

  show(el, html);
  window._script = data.script;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function copyScript() {
  navigator.clipboard
    .writeText(window._script)
    .then(() => alert("已复制到剪贴板"));
}

async function applyRec(recId, mode) {
  if (mode === "interactive" && !confirm(`确认执行推荐 ${recId}？`)) return;

  try {
    const data = await api("/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rec_id: recId, mode, no_deep: false }),
    });

    if (data.success) {
      alert(
        `执行成功！\nExec ID: ${data.exec_id}\n\n可用 diskadvisor rollback ${data.exec_id} 回滚`,
      );
    } else {
      alert(`执行部分失败，查看执行日志。`);
    }
  } catch (e) {
    alert(`执行失败：${e.message}`);
  }
}

// ============ 咨询 ============
document.getElementById("btn-advise").addEventListener("click", async () => {
  const input = document.getElementById("advise-input");
  const result = document.getElementById("advise-result");
  const name = input.value.trim();

  if (!name) {
    show(result, '<div class="error">请输入软件名</div>');
    return;
  }

  try {
    const data = await api(`/advise/${encodeURIComponent(name)}`);
    renderAdvice(result, data);
  } catch (e) {
    show(result, `<div class="error">${e.message}</div>`);
  }
});

function renderAdvice(el, data) {
  let html = `<div class="card"><h2>${data.software_name} 安装建议</h2>
    <table><tbody>
      <tr><th>推荐安装路径</th><td><code>${data.recommended_install_path}</code></td></tr>
      ${data.recommended_data_path ? `<tr><th>推荐数据路径</th><td><code>${data.recommended_data_path}</code></td></tr>` : ""}
      ${data.install_method ? `<tr><th>安装方式</th><td>${data.install_method}</td></tr>` : ""}
      ${data.install_command ? `<tr><th>安装命令</th><td><code>${data.install_command}</code></td></tr>` : ""}
    </tbody></table>`;

  if (data.env_vars && data.env_vars.length > 0) {
    html += "<h3>环境变量</h3><ul>";
    data.env_vars.forEach(
      (v) =>
        (html += `<li><code>${v.name}</code> = <code>${v.value}</code> (${v.scope})</li>`),
    );
    html += "</ul>";
  }

  if (data.version_management) {
    html += "<h3>版本管理</h3>";
    html += `<p>工具：${data.version_management.tool}</p>`;
    html += `<p>方法：${data.version_management.method}</p>`;
    if (data.version_management.commands) {
      html +=
        "<pre><code>" +
        data.version_management.commands.join("\n") +
        "</code></pre>";
    }
  }

  if (data.migration_steps && data.migration_steps.length > 0) {
    html += "<h3>迁移步骤</h3><ol>";
    data.migration_steps.forEach((s) => (html += `<li>${s}</li>`));
    html += "</ol>";
  }

  if (data.notes) {
    html += `<p style="margin-top:16px;padding:12px;background:#fef9e7;border-radius:6px">📝 ${data.notes}</p>`;
  }

  html += "</div>";
  show(el, html);
}

// ============ 执行日志 ============
document.getElementById("btn-journal").addEventListener("click", loadJournal);

async function loadJournal() {
  const result = document.getElementById("journal-result");
  try {
    const entries = await api("/journal");
    if (entries.length === 0) {
      show(result, '<div class="card"><p>暂无执行记录。</p></div>');
      return;
    }
    let html =
      '<div class="card"><h2>执行日志</h2><table><thead><tr><th>Exec ID</th><th>推荐</th><th>状态</th><th>时间</th><th>操作</th></tr></thead><tbody>';
    entries.forEach((e) => {
      const success = e.operations.every((op) => op.success);
      const status = e.rolled_back ? "已回滚" : success ? "成功" : "部分失败";
      const level = e.rolled_back ? "low" : success ? "ok" : "error";
      html += `<tr>
        <td><code>${e.exec_id}</code></td>
        <td>${e.rec_title}</td>
        <td>${badge(level, status)}</td>
        <td>${new Date(e.timestamp).toLocaleString()}</td>
        <td>${e.rolled_back ? "-" : `<button class="btn secondary btn-sm" onclick="rollback('${e.exec_id}')">回滚</button>`}</td>
      </tr>`;
    });
    html += "</tbody></table></div>";
    show(result, html);
  } catch (e) {
    show(result, `<div class="error">加载失败：${e.message}</div>`);
  }
}

async function rollback(execId) {
  if (!confirm(`确认回滚 ${execId}？`)) return;
  try {
    await api(`/rollback/${execId}`, { method: "POST" });
    alert("回滚成功");
    loadJournal();
  } catch (e) {
    alert(`回滚失败：${e.message}`);
  }
}

// ============ 知识库 ============
document.getElementById("btn-kb-list").addEventListener("click", loadKBList);
document
  .getElementById("btn-kb-validate")
  .addEventListener("click", validateKB);
document.getElementById("btn-kb-search").addEventListener("click", searchKB);

async function loadKBList() {
  const result = document.getElementById("kb-result");
  try {
    const entries = await api("/kb/list");
    const byCategory = {};
    entries.forEach((e) => {
      if (!byCategory[e.category]) byCategory[e.category] = [];
      byCategory[e.category].push(e);
    });

    let html =
      '<div class="card"><h2>知识库（' + entries.length + " 个软件）</h2>";
    Object.entries(byCategory).forEach(([cat, items]) => {
      html += `<h3>${cat}</h3><ul>`;
      items.forEach((e) => {
        html += `<li><strong>${e.name}</strong> <code>${e.id}</code> → <code>${e.recommendedInstallPath}</code></li>`;
      });
      html += "</ul>";
    });
    html += "</div>";
    show(result, html);
  } catch (e) {
    show(result, `<div class="error">加载失败：${e.message}</div>`);
  }
}

async function validateKB() {
  const result = document.getElementById("kb-result");
  try {
    const data = await api("/kb/validate");
    let html = '<div class="card"><h2>知识库校验</h2>';
    if (data.total === 0) {
      html += '<div class="success">✅ 校验通过，无问题</div>';
    } else {
      if (data.errors.length > 0) {
        html += `<h3 style="color:#c0392b">错误（${data.errors.length}）</h3><ul>`;
        data.errors.forEach((e) => (html += `<li>${e}</li>`));
        html += "</ul>";
      }
      if (data.warnings.length > 0) {
        html += `<h3 style="color:#e67e22">警告（${data.warnings.length}）</h3><ul>`;
        data.warnings.forEach((w) => (html += `<li>${w}</li>`));
        html += "</ul>";
      }
    }
    html += "</div>";
    show(result, html);
  } catch (e) {
    show(result, `<div class="error">校验失败：${e.message}</div>`);
  }
}

async function searchKB() {
  const q = document.getElementById("kb-search").value.trim();
  if (!q) return;
  const result = document.getElementById("kb-result");
  try {
    const data = await api(`/kb/search?q=${encodeURIComponent(q)}`);
    if (data.length === 0) {
      show(result, '<div class="card"><p>无匹配结果。</p></div>');
      return;
    }
    let html = `<div class="card"><h2>搜索结果（${data.length}）</h2><ul>`;
    data.forEach(
      (e) =>
        (html += `<li><strong>${e.name}</strong> <code>${e.id}</code> (${e.category})</li>`),
    );
    html += "</ul></div>";
    show(result, html);
  } catch (e) {
    show(result, `<div class="error">搜索失败：${e.message}</div>`);
  }
}

// ============ 初始化 ============
(async function init() {
  try {
    const v = await api("/version");
    document.getElementById("version").textContent = "v" + v.version;
  } catch (e) {
    console.warn("获取版本失败", e);
  }
})();

async function startScan(noDeep, forceRefresh) {
  // 1. 创建任务
  const { task_id } = await api(
    `/scan/async?no_deep=${noDeep}&force_refresh=${forceRefresh}`,
    { method: "POST" },
  );

  // 2. 轮询
  while (true) {
    const task = await api(`/scan/task/${task_id}`);
    stage.textContent = task.stage;
    if (task.status === "done") return task.result;
    if (task.status === "failed") throw new Error(task.error);
    await new Promise((r) => setTimeout(r, 500));
  }
}
