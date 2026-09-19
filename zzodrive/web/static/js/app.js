let currentFolder = '';
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
  // reset state so next open is clean
  if (uploadQueue.length === 0) {
    const summary = document.getElementById("upload-status-summary");
    if (summary) summary.style.display = "none";
  }
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

  const searchInput = $("#search");
  const query = q || (searchInput ? searchInput.value : "");
  const sortEl = $("#sort-select");
  const sort = sortEl ? sortEl.value : "name-asc";

  try {
    const params = new URLSearchParams({
      q: query,
      sort: sort,
      folder: currentFolder,
    });
    const res = await fetch(`/api/files?${params.toString()}`);
    const data = await res.json();
    renderBreadcrumb(data.current_folder || "");
    renderFiles(data.files, data.folders || []);
  } catch (e) {
    container.innerHTML = `<div class="empty">❌ ${e.message}</div>`;
  }
}


function renderBreadcrumb(folder) {
  const el = document.getElementById("breadcrumb");
  if (!el) return;
  const parts = folder ? folder.split("/") : [];
  let html = `<a href="#" onclick="goToFolder('');return false;">🏠 ${I18N.home || "Home"}</a>`;
  let path = "";
  for (const p of parts) {
    path = path ? (path + "/" + p) : p;
    html += ` <span class="bc-sep">/</span> <a href="#" onclick="goToFolder('${path}');return false;">${escapeHtml(p)}</a>`;
  }
  el.innerHTML = html;
}


function goToFolder(path) {
  currentFolder = path || "";
  // Clear selection when changing folder
  selectedFiles.clear();
  const searchInput = $("#search");
  if (searchInput) searchInput.value = "";
  loadFiles();
}


async function newFolder() {
  const name = prompt(I18N.new_folder_prompt || "Folder name:");
  if (!name || !name.trim()) return;
  try {
    const res = await fetch("/api/folders/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parent: currentFolder, name: name.trim() }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.folder_created || "Folder created", "success");
    loadFiles();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


async function renameFolder(path) {
  const name = prompt(I18N.rename_folder_prompt || "New folder name:", path.split("/").pop());
  if (!name || !name.trim()) return;
  try {
    const res = await fetch("/api/folders/rename", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old: path, new_name: name.trim() }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.folder_renamed || "Folder renamed", "success");
    loadFiles();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


async function deleteFolder(path) {
  if (!confirm((I18N.confirm_delete_folder || "Delete this folder and ALL its files?") + "\n\n" + path)) return;
  try {
    const res = await fetch("/api/folders/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.folder_deleted || "Folder deleted", "success");
    loadFiles();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

function renderFiles(files, folderItems) {
  const container = $("#files-container");
  if (!container) return;

  folderItems = folderItems || [];

  if (!files.length && !folderItems.length) {
    container.innerHTML = `<div class="empty">📂 ${I18N.no_files}</div>`;
    return;
  }

  // selection bar (only if some selected)
  const selectionBar = `
    <div id="selection-bar" class="selection-bar" style="display:none;">
      <div>
        <strong id="selected-count">0</strong> ${I18N.selected || "selected"}
      </div>
      <div class="selection-actions">
        <button class="btn btn-primary" onclick="bulkDownload()">⬇️ ${I18N.download_all || "Download"}</button>
        <button class="btn btn-ghost" onclick="bulkMove()">📁 ${I18N.move || "Move"}</button>
        <button class="btn btn-danger" onclick="bulkDelete()">🗑️ ${I18N.delete_all || "Delete"}</button>
        <button class="btn btn-ghost" onclick="clearSelection()">${I18N.clear || "Clear"}</button>
      </div>
    </div>`;

  // Folder cards
  const folderCards = folderItems.map(f => {
    const safePath = f.path.replace(/'/g, "\\'");
    return `
      <div class="folder-card" ondblclick="goToFolder('${safePath}')">
        <div class="folder-icon" onclick="goToFolder('${safePath}')">📁</div>
        <div class="folder-info" onclick="goToFolder('${safePath}')">
          <div class="folder-name">${escapeHtml(f.name)}</div>
          <div class="folder-meta">${I18N.folder || "Folder"}</div>
        </div>
        <div class="folder-actions">
          <button class="icon-btn" title="Rename" onclick="event.stopPropagation();renameFolder('${safePath}')">✏️</button>
          <button class="icon-btn danger" title="Delete" onclick="event.stopPropagation();deleteFolder('${safePath}')">🗑️</button>
        </div>
      </div>`;
  }).join("");

  // File cards
  const fileCards = files.map(f => `
    <div class="file-card" data-id="${f.id}">
      <label class="file-checkbox">
        <input type="checkbox" onchange="toggleSelect(${f.id}, this.checked)" ${selectedFiles.has(f.id) ? "checked" : ""}>
      </label>
      <div class="file-icon" ${canPreview(f.name) ? `onclick="showPreview(${f.id}, '${escapeHtml(f.name)}')" style="cursor:pointer;"` : ""}>${f.encrypted ? "🔐" : "📄"}</div>
      <div class="file-info">
        <div class="file-name" title="${escapeHtml(f.path)}">${escapeHtml(f.name)}</div>
        <div class="file-meta">
          <span>${f.size_human}</span>
          ${f.encrypted ? `<span class="enc-badge">${I18N.encrypted_badge}</span>` : ""}
        </div>
      </div>
      <div class="file-actions">
        ${canPreview(f.name) ? `<button class="icon-btn" data-action="preview" data-id="${f.id}" data-name="${escapeHtml(f.name)}">👁️</button>` : ""}
        <button class="icon-btn" title="Download" onclick="downloadFile(${f.id})">⬇️</button>
        <button class="icon-btn danger" title="Delete" onclick="deleteFile(${f.id})">🗑️</button>
      </div>
    </div>
  `).join("");

  container.innerHTML = selectionBar + folderCards + fileCards;
  updateSelectionBar();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"'\/`]/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
    "`": "&#x60;",
  })[c]);
}


// Escape for embedding in JS strings inside onclick="..." attributes
function escapeJs(s) {
  return String(s)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/</g, "\\x3C");
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
  const folderInput = $("#folder-input");
  if (!dz || !fi) return;

  // Remove any previously attached handlers by replacing the node
  // (defensive: in case of hot reloads)

  dz.addEventListener("click", (e) => {
    if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
    if (e.target.closest("button")) return;
    fi.click();
  });

  fi.addEventListener("change", () => {
    handleFiles([...fi.files]);
    fi.value = "";
  });

  if (folderInput) {
    folderInput.addEventListener("change", () => {
      handleFiles([...folderInput.files]);
      folderInput.value = "";
    });
  }

  // === Drag & drop (single handler) ===
  dz.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dz.classList.add("dragover");
  });
  dz.addEventListener("dragover", (e) => {
    e.preventDefault();
    dz.classList.add("dragover");
  });
  dz.addEventListener("dragleave", (e) => {
    e.preventDefault();
    if (e.target === dz) dz.classList.remove("dragover");
  });

  dz.addEventListener("drop", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    dz.classList.remove("dragover");

    const files = [];

    // Prefer items API (supports folders)
    if (e.dataTransfer.items && e.dataTransfer.items.length) {
      const tasks = [];
      for (const item of e.dataTransfer.items) {
        if (item.kind !== "file") continue;
        const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
        if (entry) {
          tasks.push(walkEntry(entry, "", files));
        } else if (item.getAsFile) {
          const f = item.getAsFile();
          if (f) files.push({ file: f, path: f.webkitRelativePath || f.name });
        }
      }
      await Promise.all(tasks);
    }

    // Fallback: plain files
    if (!files.length && e.dataTransfer.files && e.dataTransfer.files.length) {
      for (const f of e.dataTransfer.files) {
        files.push({ file: f, path: f.webkitRelativePath || f.name });
      }
    }

    if (!files.length) {
      console.warn("[zzoDrive] No files in drop event");
      return;
    }

    handleFiles(files);
  });
}


// Recursively read a FileSystemEntry (folder or file)
async function walkEntry(entry, prefix, out) {
  if (entry.isFile) {
    try {
      const file = await new Promise((resolve, reject) => entry.file(resolve, reject));
      if (file) {
        const name = file.name;
        const path = prefix ? (prefix + "/" + name) : name;
        out.push({ file: file, path: path });
      }
    } catch (err) {
      console.warn("[zzoDrive] Failed to read file entry:", err);
    }
  } else if (entry.isDirectory) {
    const reader = entry.createReader();
    const newPrefix = prefix ? (prefix + "/" + entry.name) : entry.name;
    // readEntries must be called repeatedly until empty
    while (true) {
      const entries = await new Promise((resolve, reject) => reader.readEntries(resolve, reject));
      if (!entries.length) break;
      for (const e of entries) {
        await walkEntry(e, newPrefix, out);
      }
    }
  }
}


function handleFiles(files) {
  if (!files || !files.length) return;

  const normalized = files.map((f) => {
    if (f instanceof File) {
      return { file: f, path: f.webkitRelativePath || f.name };
    }
    return f;
  });

  uploadQueue = uploadQueue.concat(normalized);
  renderUploadQueue();
  showUploadActions();
}


function renderUploadQueue() {
  const list = $("#upload-list");
  if (!list) return;
  list.innerHTML = uploadQueue.map((item, i) => {
    const file = item.file || item;
    const name = file.name || "unknown";
    const path = item.path || name;
    return `
    <div class="upload-item" data-idx="${i}" style="flex-direction:column;align-items:stretch;gap:6px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="name" style="font-weight:600;" title="${escapeHtml(path)}">${escapeHtml(path)}</span>
        <span class="status loading" style="font-size:.85rem;">${I18N.status_waiting}</span>
      </div>
      <div class="up-progress"><div class="up-progress-bar" style="width:0%"></div></div>
      <div class="up-meta">
        <span class="up-meta-left">—</span>
        <span class="up-meta-right">—</span>
      </div>
    </div>`;
  }).join("");
  showUploadActions();
}


async function uploadAll() {
  const enc = $("#encrypt-toggle")?.checked ? "1" : "0";
  const items = [...document.querySelectorAll(".upload-item")];

  for (let i = 0; i < uploadQueue.length; i++) {
    const item = uploadQueue[i];
    const file = item.file || item;
    const relPath = item.path || file.name || "unnamed";

    // Safety check: must be a File or Blob
    if (!(file instanceof File) && !(file instanceof Blob)) {
      console.error("[zzoDrive] Skipping invalid upload item:", item);
      const el = items[i];
      const status = el?.querySelector(".status");
      if (status) { status.textContent = "✗ invalid file"; status.className = "status err"; }
      continue;
    }

    const el = items[i];
    const status = el?.querySelector(".status");
    if (status) status.textContent = I18N.status_uploading;

    const fd = new FormData();
    fd.append("file", file, file.name || "unnamed");
    fd.append("encrypt", enc);
    fd.append("path", relPath);
    fd.append("folder", currentFolder || "");

    try {
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "failed");

      const taskId = data.task_id;
      const progressBar = el.querySelector(".up-progress-bar");
      const metaLeft = el.querySelector(".up-meta-left");
      const metaRight = el.querySelector(".up-meta-right");

      await new Promise((resolve, reject) => {
        const timer = setInterval(async () => {
          try {
            const r = await fetch(`/api/progress/${taskId}`);
            if (!r.ok) return;
            const p = await r.json();
            if (progressBar) progressBar.style.width = (p.percent || 0).toFixed(1) + "%";
            if (metaLeft) metaLeft.textContent = `${p.current_human || "—"} / ${p.total_human || "—"}`;
            if (metaRight) metaRight.textContent = p.speed_human || "—";
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
              if (p.status === "error") reject(new Error(p.error));
              else resolve();
            }
          } catch (e) { /* ignore */ }
        }, 400);
      });
    } catch (e) {
      if (status) { status.textContent = "✗ " + e.message; status.className = "status err"; }
    }
  }

  uploadQueue = [];
  showUploadActions();
  toast(I18N.toast_upload_done, "success");
  loadFiles($("#search")?.value || "");
}


// ============ Upload queue actions ============
function showUploadActions() {
  const actions = document.getElementById("upload-actions");
  const summary = document.getElementById("upload-status-summary");
  const count = document.getElementById("upload-queue-count");
  if (actions) actions.style.display = uploadQueue.length ? "flex" : "none";
  if (summary) summary.style.display = "none";
  if (count) count.textContent = uploadQueue.length;
}


function clearUploadQueue() {
  if (!uploadQueue.length) return;
  if (!confirm(I18N.confirm_clear_queue || "Clear all files from the queue?")) return;
  uploadQueue = [];
  renderUploadQueue();
  showUploadActions();
  const summary = document.getElementById("upload-status-summary");
  if (summary) {
    summary.textContent = I18N.queue_cleared || "Queue cleared";
    summary.className = "upload-status-summary info";
    summary.style.display = "block";
  }
}


async function startUpload() {
  if (!uploadQueue.length) {
    toast(I18N.no_files_to_upload || "No files to upload", "error");
    return;
  }

  const confirmBtn = document.getElementById("upload-confirm-btn");
  const clearBtn = document.querySelector("#upload-actions .btn-ghost");
  const summary = document.getElementById("upload-status-summary");

  if (confirmBtn) { confirmBtn.disabled = true; confirmBtn.style.opacity = "0.6"; }
  if (clearBtn) { clearBtn.disabled = true; clearBtn.style.opacity = "0.6"; }

  // trigger actual upload
  await uploadAll();

  if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.style.opacity = "1"; }
  if (clearBtn) { clearBtn.disabled = false; clearBtn.style.opacity = "1"; }

  // summary
  if (summary) {
    summary.textContent = `✅ ${I18N.toast_upload_done || "Upload complete"}`;
    summary.className = "upload-status-summary success";
    summary.style.display = "block";
  }

  showUploadActions();
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


// ============ Multi-select ============
let selectedFiles = new Set();


// ============ Share ============


// ============ About ============
function showAbout() {
  document.getElementById("about-modal")?.classList.add("open");
}

function closeAbout() {
  document.getElementById("about-modal")?.classList.remove("open");
}


// ============ Preview ============
function canPreview(name) {
  const n = (name || "").toLowerCase();
  return (
    n.endsWith(".jpg") || n.endsWith(".jpeg") || n.endsWith(".png") ||
    n.endsWith(".gif") || n.endsWith(".webp") || n.endsWith(".bmp") ||
    n.endsWith(".svg") || n.endsWith(".mp4") || n.endsWith(".webm") ||
    n.endsWith(".mp3") || n.endsWith(".ogg") || n.endsWith(".wav") ||
    n.endsWith(".pdf")
  );
}

function showPreview(msgId, name) {
  const modal = document.getElementById("preview-modal");
  const title = document.getElementById("preview-title");
  const content = document.getElementById("preview-content");
  if (!modal || !content) return;

  title.textContent = name;

  const url = `/api/preview/${msgId}`;
  const n = name.toLowerCase();
  let html = "";

  if (/\.(mp4|webm)$/.test(n)) {
    html = `<video src="${url}" controls autoplay style="max-width:80vw;max-height:70vh;border-radius:8px;"></video>`;
  } else if (/\.(mp3|ogg|wav)$/.test(n)) {
    html = `<audio src="${url}" controls autoplay style="width:80%;"></audio>`;
  } else if (/\.pdf$/.test(n)) {
    html = `<iframe src="${url}" style="width:80vw;height:75vh;border:none;border-radius:8px;"></iframe>`;
  } else {
    html = `<img src="${url}" alt="${name}" style="max-width:80vw;max-height:75vh;border-radius:8px;">`;
  }

  // Rich loading indicator
  content.innerHTML = `
    <div style="text-align:center;padding:40px 20px;">
      <div class="preview-spinner"></div>
      <div style="margin-top:16px;color:var(--text-muted);font-size:0.95rem;">
        ${I18N.preview_loading || "Downloading preview..."}
      </div>
      <div style="margin-top:8px;color:var(--text-muted);font-size:0.8rem;">
        ${I18N.preview_hint || "This may take a few seconds depending on your connection"}
      </div>
    </div>`;

  modal.classList.add("open");

  // load the actual content
  setTimeout(() => {
    content.innerHTML = html;
    // once loaded, remove spinner (image/video will show)
    const img = content.querySelector("img, video, iframe, audio");
    if (img) {
      img.onload = () => {};
      img.onerror = () => {
        content.innerHTML = `<div class="empty" style="color:#ef4444;">❌ ${I18N.preview_failed || "Failed to load preview"}</div>`;
      };
    }
  }, 200);
}

function closePreview() {
  const modal = document.getElementById("preview-modal");
  if (!modal) return;
  modal.classList.remove("open");
  document.getElementById("preview-content").innerHTML = "";
}


// ============ Multi-select functions ============
function toggleSelect(id, checked) {
  if (checked) selectedFiles.add(id);
  else selectedFiles.delete(id);
  updateSelectionBar();
}

function updateSelectionBar() {
  const bar = document.getElementById("selection-bar");
  const count = document.getElementById("selected-count");
  if (!bar) return;
  if (selectedFiles.size === 0) {
    bar.style.display = "none";
  } else {
    bar.style.display = "flex";
    if (count) count.textContent = selectedFiles.size;
  }
}

function clearSelection() {
  selectedFiles.clear();
  document.querySelectorAll(".file-checkbox input").forEach(cb => cb.checked = false);
  updateSelectionBar();
}

async function bulkDelete() {
  if (selectedFiles.size === 0) return;
  if (!confirm((I18N.confirm_delete_all || "Delete selected files?") + ` (${selectedFiles.size})`)) return;

  const ids = [...selectedFiles];
  let ok = 0, fail = 0;
  for (const id of ids) {
    try {
      const res = await fetch(`/api/delete/${id}`, { method: "POST" });
      const data = await res.json();
      if (data.ok) ok++;
      else fail++;
    } catch (e) { fail++; }
  }
  toast(`Deleted: ${ok}, failed: ${fail}`, ok > 0 ? "success" : "error");
  selectedFiles.clear();
  loadFiles();
}

async function bulkDownload() {
  if (selectedFiles.size === 0) return;
  const ids = [...selectedFiles];
  toast(`${I18N.download_starting || "Starting downloads"}: ${ids.length}...`, "success");
  // Download one by one with a small delay
  for (let i = 0; i < ids.length; i++) {
    await downloadFile(ids[i], true);
    await new Promise(r => setTimeout(r, 1000));
  }
}


// ============ Move files ============
let moveFoldersAll = [];

async function bulkMove() {
  if (selectedFiles.size === 0) return;
  document.getElementById("move-modal")?.classList.add("open");
  document.getElementById("move-search").value = "";
  document.getElementById("move-new-folder").value = "";

  try {
    const res = await fetch("/api/folders/list");
    const data = await res.json();
    moveFoldersAll = data.folders || [];
  } catch (e) {
    moveFoldersAll = [];
  }
  renderMoveFolders("");
}


function renderMoveFolders(filter) {
  const container = document.getElementById("move-folders");
  if (!container) return;
  const q = (filter || "").toLowerCase();

  const items = [
    { path: "", label: "🏠 " + (I18N.home || "Home") },
    ...moveFoldersAll
      .filter(f => !q || f.toLowerCase().includes(q))
      .map(f => ({ path: f, label: "📁 " + f })),
  ];

  container.innerHTML = items.map(it => `
    <div class="move-folder-item" onclick="doMove('${it.path.replace(/'/g, "\\\\'")}')">
      ${escapeHtml(it.label)}
    </div>
  `).join("");
}


function filterMoveFolders() {
  const q = document.getElementById("move-search").value;
  renderMoveFolders(q);
}


async function doMove(dest) {
  const ids = [...selectedFiles];
  if (!ids.length) return;
  try {
    const res = await fetch("/api/files/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: ids, dest: dest }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(`📁 ${I18N.moved || "Moved"}: ${data.moved}`, "success");
    selectedFiles.clear();
    closeMove();
    loadFiles();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


async function moveToNew() {
  const name = document.getElementById("move-new-folder").value.trim();
  if (!name) return;
  // create folder first
  try {
    const res = await fetch("/api/folders/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parent: "", name: name }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    await doMove(data.path);
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


function closeMove() {
  document.getElementById("move-modal")?.classList.remove("open");
}


// ============================================================
// Settings + Proxy functions (restored)
// ============================================================

// ---------- Settings ----------
function showSettings() {
  const modal = document.getElementById("settings-modal");
  if (!modal) return;
  modal.classList.add("open");
  loadSettings();
}

function closeSettings() {
  document.getElementById("settings-modal")?.classList.remove("open");
}

async function loadSettings() {
  loadLanStatus();
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    const input = document.getElementById("pwd-input");
    if (input) {
      input.placeholder = data.password_set
        ? (I18N.settings_pwd_set || "(set)") + " " + (I18N.settings_pwd_placeholder || "")
        : (I18N.settings_pwd_placeholder || "Enter new password");
      input.value = "";
    }
  } catch (e) {
    console.warn("[zzoDrive] loadSettings failed:", e);
  }
}

async function savePassword() {
  const pwd = document.getElementById("pwd-input")?.value || "";
  if (!pwd) {
    toast("Enter a password first", "error");
    return;
  }
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "failed");
    toast(I18N.toast_pwd_saved || "Password saved", "success");
    const input = document.getElementById("pwd-input");
    if (input) input.value = "";
    loadSettings();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function clearPassword() {
  if (!confirm(I18N.confirm_clear_pwd || "Clear encryption password?")) return;
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: "" }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "failed");
    toast(I18N.toast_pwd_cleared || "Password cleared", "success");
    loadSettings();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function resetIndex() {
  if (!confirm(I18N.confirm_reset || "Reset local index? Files on Telegram will NOT be deleted.")) return;
  try {
    const res = await fetch("/api/reset", { method: "POST" });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "failed");
    toast(I18N.toast_index_reset || "Index reset", "success");
    loadFiles();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


// ---------- Proxy ----------
async function showProxy() {
  const modal = document.getElementById("proxy-modal");
  if (!modal) {
    console.warn("[zzoDrive] proxy-modal not found in DOM");
    return;
  }
  modal.classList.add("open");

  // load current
  try {
    const res = await fetch("/api/proxy");
    const data = await res.json();
    const currentEl = document.getElementById("proxy-current");
    const inputEl = document.getElementById("proxy-input");
    const toggleEl = document.getElementById("proxy-enabled-toggle");
    if (currentEl) currentEl.textContent = data.proxy || "—";
    if (inputEl) inputEl.value = data.proxy || "";
    if (toggleEl) toggleEl.checked = data.enabled !== false;
  } catch (e) {
    console.warn("[zzoDrive] showProxy failed:", e);
  }
}

function closeProxy() {
  document.getElementById("proxy-modal")?.classList.remove("open");
}

async function saveProxy() {
  const proxy = document.getElementById("proxy-input")?.value.trim() || "";
  const enabled = document.getElementById("proxy-enabled-toggle")?.checked ?? true;

  try {
    const res = await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: proxy, enabled: enabled }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "failed");
    toast(I18N.toast_proxy_saved || "Proxy saved", "success");
    setTimeout(() => window.location.reload(), 800);
  } catch (e) {
    toast((I18N.toast_proxy_test_fail || "Failed") + ": " + e.message, "error");
  }
}

async function testProxy() {
  const proxy = document.getElementById("proxy-input")?.value.trim() || "";
  toast(I18N.status_uploading || "Testing...", "success");
  try {
    const res = await fetch("/api/proxy/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: proxy }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "failed");
    toast(I18N.toast_proxy_test_ok || "Connection OK", "success");
  } catch (e) {
    toast((I18N.toast_proxy_test_fail || "Failed") + ": " + e.message, "error");
  }
}

async function toggleProxyEnabled() {
  const enabled = document.getElementById("proxy-enabled-toggle")?.checked ?? false;
  try {
    const res = await fetch("/api/proxy/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: enabled }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "failed");
    toast(enabled ? "Proxy ON" : "Proxy OFF", "success");
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function clearProxy() {
  if (!confirm(I18N.confirm_clear_proxy || "Remove proxy?")) return;
  try {
    const res = await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: "" }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "failed");
    toast(I18N.toast_proxy_cleared || "Proxy removed", "success");
    setTimeout(() => window.location.reload(), 800);
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}


// ---------- generic close-on-backdrop ----------
document.addEventListener("click", (e) => {
  if (e.target.classList?.contains("modal")) {
    e.target.classList.remove("open");
  }
});


// ---------- Event delegation for file actions (safer than inline onclick) ----------
document.addEventListener("change", (e) => {
  if (e.target.matches(".file-check")) {
    const id = parseInt(e.target.dataset.id, 10);
    toggleSelect(id, e.target.checked);
  }
});

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const action = btn.dataset.action;
  const id = parseInt(btn.dataset.id, 10);
  const name = btn.dataset.name || "";

  if (action === "preview") {
    e.preventDefault();
    showPreview(id, name);
  } else if (action === "download") {
    e.preventDefault();
    downloadFile(id);
  } else if (action === "delete") {
    e.preventDefault();
    deleteFile(id);
  } else if (action === "rename-folder") {
    e.preventDefault();
    renameFolder(btn.dataset.path || "");
  } else if (action === "delete-folder") {
    e.preventDefault();
    deleteFolder(btn.dataset.path || "");
  } else if (action === "goto-folder") {
    e.preventDefault();
    goToFolder(btn.dataset.path || "");
  }
});


// ============ LAN mode ============
async function loadLanStatus() {
  try {
    const res = await fetch("/api/lan/token");
    const data = await res.json();
    const statusEl = document.getElementById("lan-status");
    const tokenBox = document.getElementById("lan-token-box");
    if (!statusEl) return;

    if (data.enabled) {
      statusEl.innerHTML = `<span style="color:var(--success);font-weight:600;">● ${I18N.lan_active || "LAN access is ON"}</span>`;
      if (tokenBox) {
        tokenBox.style.display = "block";
        tokenBox.textContent = data.token || "";
      }
      document.getElementById("lan-enable-btn").style.display = "none";
      document.getElementById("lan-regen-btn").style.display = "";
      document.getElementById("lan-disable-btn").style.display = "";
    } else {
      statusEl.innerHTML = `<span style="color:var(--text-muted);">○ ${I18N.lan_off || "LAN access is OFF (local only)"}</span>`;
      if (tokenBox) tokenBox.style.display = "none";
      document.getElementById("lan-enable-btn").style.display = "";
      document.getElementById("lan-regen-btn").style.display = "none";
      document.getElementById("lan-disable-btn").style.display = "none";
    }
  } catch (e) {
    console.warn("[zzoDrive] loadLanStatus:", e);
  }
}

async function enableLan() {
  try {
    const res = await fetch("/api/lan/enable", { method: "POST" });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.lan_enabled || "LAN access enabled", "success");
    loadLanStatus();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function regenLan() {
  if (!confirm(I18N.lan_regen_confirm || "Regenerate token? Old links will stop working.")) return;
  try {
    const res = await fetch("/api/lan/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "regenerate" }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.lan_regen_done || "New token generated", "success");
    loadLanStatus();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function disableLan() {
  if (!confirm(I18N.lan_disable_confirm || "Disable LAN access?")) return;
  try {
    const res = await fetch("/api/lan/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "disable" }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    toast(I18N.lan_disabled || "LAN access disabled", "success");
    loadLanStatus();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}
