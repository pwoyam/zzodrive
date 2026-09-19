// ============ zzoDrive Frontend ============

const $ = (sel) => document.querySelector(sel);

// ---------- Toast ----------
let toastTimer;
function toast(msg, kind = "success") {
  const el = $("#toast");
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${kind} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3000);
}

// ---------- Modal helpers ----------
function showUpload() {
  $("#upload-modal")?.classList.add("open");
}
function closeUpload() {
  $("#upload-modal")?.classList.remove("open");
}
function showSettings() {
  loadSettings();
  $("#settings-modal")?.classList.add("open");
}
function closeSettings() {
  $("#settings-modal")?.classList.remove("open");
}

// close modal on backdrop click
document.addEventListener("click", (e) => {
  if (e.target.classList?.contains("modal")) {
    e.target.classList.remove("open");
  }
});

// ---------- Files list ----------
async function loadFiles(q = "") {
  const container = $("#files-container");
  if (!container) return;

  container.innerHTML = `<div class="loading">${I18N.loading}</div>`;

  try {
    const res = await fetch(`/api/files?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderFiles(data.files);
  } catch (e) {
    container.innerHTML = `<div class="empty">❌ ${e.message}</div>`;
  }
}

function renderFiles(files) {
  const container = $("#files-container");
  if (!files.length) {
    container.innerHTML = `<div class="empty">📂 ${I18N.no_files}</div>`;
    return;
  }

  container.innerHTML = files.map(f => `
    <div class="file-card" data-id="${f.id}">
      <div class="file-icon">${f.encrypted ? "🔐" : "📄"}</div>
      <div class="file-info">
        <div class="file-name" title="${escapeHtml(f.path)}">${escapeHtml(f.path)}</div>
        <div class="file-meta">
          <span>${f.size_human}</span>
          ${f.encrypted ? `<span class="enc-badge">${I18N.encrypted_badge}</span>` : ''}
        </div>
      </div>
      <div class="file-actions">
        <button class="icon-btn" title="Download" onclick="downloadFile(${f.id})">⬇️</button>
        <button class="icon-btn danger" title="Delete" onclick="deleteFile(${f.id})">🗑️</button>
      </div>
    </div>
  `).join("");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// ---------- Download ----------
async function downloadFile(id) {
  // open modal
  const modal = document.getElementById("download-modal");
  const bar = document.getElementById("dl-progress-bar");
  const percent = document.getElementById("dl-percent");
  const speed = document.getElementById("dl-speed");
  const text = document.getElementById("dl-progress-text");
  const status = document.getElementById("dl-status");
  const nameEl = document.getElementById("dl-file-name");

  if (bar) bar.style.width = "0%";
  if (percent) percent.textContent = "0%";
  if (speed) speed.textContent = "—";
  if (text) text.textContent = "—";
  if (status) status.textContent = I18N.dl_preparing;
  if (nameEl) nameEl.textContent = "—";
  modal?.classList.add("open");

  try {
    // start download
    const res = await fetch(`/api/download/start/${id}`, { method: "POST" });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "start failed");

    const taskId = data.task_id;
    if (nameEl) nameEl.textContent = data.name;

    // poll progress
    await new Promise((resolve, reject) => {
      const timer = setInterval(async () => {
        try {
          const r = await fetch(`/api/progress/${taskId}`);
          if (!r.ok) return;
          const p = await r.json();
          if (bar) bar.style.width = (p.percent || 0).toFixed(1) + "%";
          if (percent) percent.textContent = (p.percent || 0).toFixed(1) + "%";
          if (speed) speed.textContent = p.speed_human || "—";
          if (text) text.textContent = `${p.current_human || "—"} / ${p.total_human || "—"}`;
          if (status) status.textContent = p.status === "running" ? I18N.status_uploading : "";
          if (p.status === "done" || p.status === "error") {
            clearInterval(timer);
            if (p.status === "error") return reject(new Error(p.error || "failed"));
            resolve();
          }
        } catch (e) { /* ignore */ }
      }, 400);
    });

    // fetch the finished file
    if (status) status.textContent = I18N.dl_done;
    if (bar) bar.style.width = "100%";
    if (percent) percent.textContent = "100%";

    // trigger browser download
    const dl = document.createElement("a");
    dl.href = `/api/download/finish/${taskId}`;
    dl.download = data.name;
    document.body.appendChild(dl);
    dl.click();
    document.body.removeChild(dl);

    setTimeout(() => closeDownload(), 1200);
  } catch (e) {
    if (status) status.textContent = (I18N.dl_error || "error") + ": " + e.message;
    if (bar) bar.style.background = "#ef4444";
    setTimeout(() => closeDownload(), 2500);
  }
}

function closeDownload() {
  document.getElementById("download-modal")?.classList.remove("open");
  const bar = document.getElementById("dl-progress-bar");
  if (bar) bar.style.background = "";  // reset
}

// ---------- Delete ----------
async function deleteFile(id) {
  if (!confirm(I18N.confirm_delete)) return;
  try {
    const res = await fetch(`/api/delete/${id}`, { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      toast(I18N.toast_file_deleted, "success");
      loadFiles($("#search")?.value || "");
    } else {
      toast(data.error || "Delete failed", "error");
    }
  } catch (e) {
    toast(`Error: ${e.message}`, "error");
  }
}

// ---------- Upload ----------
let uploadQueue = [];

function initUpload() {
  const dz = $("#dropzone");
  const fi = $("#file-input");
  if (!dz || !fi) return;

  dz.addEventListener("click", () => fi.click());
  fi.addEventListener("change", () => {
    handleFiles([...fi.files]);
    fi.value = "";
  });

  ["dragenter", "dragover"].forEach(ev =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach(ev =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
    })
  );
  dz.addEventListener("drop", (e) => {
    handleFiles([...e.dataTransfer.files]);
  });
}

function handleFiles(files) {
  if (!files.length) return;
  uploadQueue = uploadQueue.concat(files);
  renderUploadQueue();
  uploadAll();
}

function renderUploadQueue() {
  const list = $("#upload-list");
  if (!list) return;
  list.innerHTML = uploadQueue.map((item, i) => `
    <div class="upload-item" data-idx="${i}" style="flex-direction:column;align-items:stretch;gap:6px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="name" style="font-weight:600;">${escapeHtml(item.name)}</span>
        <span class="status loading" style="font-size:.85rem;">${I18N.status_waiting}</span>
      </div>
      <div class="up-progress"><div class="up-progress-bar" style="width:0%"></div></div>
      <div class="up-meta">
        <span class="up-meta-left">—</span>
        <span class="up-meta-right">—</span>
      </div>
    </div>
  `).join("");
}

async function uploadAll() {
  const enc = $("#encrypt-toggle")?.checked ? "1" : "0";
  const items = [...document.querySelectorAll(".upload-item")];

  for (let i = 0; i < uploadQueue.length; i++) {
    const f = uploadQueue[i];
    const el = items[i];
    const status = el?.querySelector(".status");
    if (status) status.textContent = I18N.status_uploading;

    const fd = new FormData();
    fd.append("file", f);
    fd.append("encrypt", enc);
    fd.append("path", f.name);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "failed");

      // poll progress
      const taskId = data.task_id;
      const progressBar = el.querySelector(".up-progress-bar");
      const metaLeft = el.querySelector(".up-meta-left");
      const metaRight = el.querySelector(".up-meta-right");

      await new Promise((resolve) => {
        const timer = setInterval(async () => {
          try {
            const r = await fetch(`/api/progress/${taskId}`);
            if (!r.ok) return;
            const p = await r.json();
            if (progressBar) progressBar.style.width = p.percent.toFixed(1) + "%";
            if (metaLeft) metaLeft.textContent = `${p.current_human} / ${p.total_human}`;
            if (metaRight) metaRight.textContent = p.speed_human;
            if (p.status === "done" || p.status === "error") {
              clearInterval(timer);
              if (status) {
                if (p.status === "done") {
                  status.textContent = "✓ " + I18N.status_done;
                  status.className = "status ok";
                } else {
                  status.textContent = "✗ " + (p.error || I18N.status_failed);
                  status.className = "status err";
                }
              }
              resolve();
            }
          } catch (e) { /* ignore */ }
        }, 400);
      });
    } catch (e) {
      if (status) { status.textContent = "✗ " + e.message; status.className = "status err"; }
    }
  }

  uploadQueue = [];
  toast(I18N.toast_upload_done, "success");
  loadFiles($("#search")?.value || "");
}

// ---------- Settings ----------
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    const input = $("#pwd-input");
    if (input) input.placeholder = data.password_set ? "••••••• " + I18N.settings_pwd_set : I18N.settings_pwd_placeholder;
  } catch (e) {
    // silent
  }
}

async function savePassword() {
  const pwd = $("#pwd-input")?.value || "";
  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd }),
    });
    toast(pwd ? I18N.toast_pwd_saved : I18N.toast_pwd_cleared, "success");
    $("#pwd-input").value = "";
    loadSettings();
  } catch (e) {
    toast(`Error: ${e.message}`, "error");
  }
}

async function clearPassword() {
  if (!confirm(I18N.confirm_clear_pwd)) return;
  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: "" }),
    });
    toast(I18N.toast_pwd_cleared, "success");
    loadSettings();
  } catch (e) {
    toast(`Error: ${e.message}`, "error");
  }
}

async function resetIndex() {
  if (!confirm(I18N.confirm_reset)) return;
  try {
    await fetch("/api/reset", { method: "POST" });
    toast(I18N.toast_index_reset, "success");
    loadFiles();
  } catch (e) {
    toast(`Error: ${e.message}`, "error");
  }
}

// ---------- Proxy ----------
async function showProxy() {
  try {
    const res = await fetch("/api/proxy");
    const data = await res.json();
    const current = data.proxy || "—";
    document.getElementById("proxy-current").textContent = current;
    document.getElementById("proxy-input").value = data.proxy || "";
    const toggle = document.getElementById("proxy-enabled-toggle");
    if (toggle) toggle.checked = data.enabled !== false;
  } catch (e) {
    // ignore
  }
  document.getElementById("proxy-modal")?.classList.add("open");
}


async function toggleProxyEnabled() {
  const enabled = document.getElementById("proxy-enabled-toggle")?.checked;
  try {
    await fetch("/api/proxy/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: enabled }),
    });
    toast(enabled ? "Proxy ON" : "Proxy OFF", "success");
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

function closeProxy() {
  document.getElementById("proxy-modal")?.classList.remove("open");
}

async function saveProxy() {
  const proxy = document.getElementById("proxy-input")?.value.trim() || "";
  try {
    const res = await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: proxy }),
    });
    const data = await res.json();
    if (data.ok) {
      toast(I18N.toast_proxy_saved, "success");
      setTimeout(() => window.location.reload(), 800);
    } else {
      toast(I18N.toast_proxy_test_fail + ": " + (data.error || "?"), "error");
    }
  } catch (e) {
    toast(I18N.toast_proxy_test_fail + ": " + e.message, "error");
  }
}

async function testProxy() {
  const proxy = document.getElementById("proxy-input")?.value.trim() || "";
  toast(I18N.status_uploading, "success");
  try {
    const res = await fetch("/api/proxy/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: proxy }),
    });
    const data = await res.json();
    if (data.ok) {
      toast(I18N.toast_proxy_test_ok, "success");
    } else {
      toast(I18N.toast_proxy_test_fail + ": " + (data.error || "?"), "error");
    }
  } catch (e) {
    toast(I18N.toast_proxy_test_fail + ": " + e.message, "error");
  }
}

async function clearProxy() {
  if (!confirm(I18N.confirm_clear_proxy)) return;
  try {
    await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: "" }),
    });
    toast(I18N.toast_proxy_cleared, "success");
    setTimeout(() => window.location.reload(), 800);
  } catch (e) {
    toast(I18N.toast_proxy_test_fail + ": " + e.message, "error");
  }
}

// ---------- Init ----------
document.addEventListener("DOMContentLoaded", () => {
  initUpload();

  const search = $("#search");
  if (search) {
    let t;
    search.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => loadFiles(search.value), 250);
    });
    loadFiles();
  }
});


// ============ Share ============


// ============ About ============
function showAbout() {
  document.getElementById("about-modal")?.classList.add("open");
}

function closeAbout() {
  document.getElementById("about-modal")?.classList.remove("open");
}
