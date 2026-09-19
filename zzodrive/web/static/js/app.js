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

  // Skeleton loading (5 rows)
  const skeletonHTML = `
    <div class="skeleton-list">
      ${Array.from({length: 5}).map(() => `
        <div class="skeleton-row">
          <div class="skeleton-box check"></div>
          <div class="skeleton-box icon"></div>
          <div class="skeleton-box name"></div>
          <div class="skeleton-box size"></div>
          <div class="skeleton-box date"></div>
          <div class="skeleton-box actions"></div>
        </div>
      `).join("")}
    </div>
  `;
  container.innerHTML = skeletonHTML;

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
    updateBackButton();
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
  updateBackButton();
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
    container.innerHTML = `<div class="empty">📂 ${I18N.no_files || "No files yet"}</div>`;
    return;
  }

  // selection bar
  const selectionBar = `
    <div id="selection-bar" class="selection-bar" style="display:none;">
      <div><strong id="selected-count">0</strong> ${I18N.selected || "selected"}</div>
      <div class="selection-actions">
        <button class="btn btn-glass" onclick="bulkDownload()">⬇️ ${I18N.download_all || "Download"}</button>
        <button class="btn btn-glass" onclick="bulkMove()">📁 ${I18N.move || "Move"}</button>
        <button class="btn btn-danger" onclick="bulkDelete()">🗑️ ${I18N.delete_all || "Delete"}</button>
        <button class="btn btn-ghost" onclick="clearSelection()">${I18N.clear || "Clear"}</button>
      </div>
    </div>`;

  // header row — با sort کلیک‌پذیر
  const curSort = ($("#sort-select")?.value) || "name-asc";
  const sortField = curSort.split("-")[0];   // name, size, date
  const sortDir = curSort.split("-")[1];     // asc, desc

  function sortIcon(field) {
    if (sortField !== field) return '<span class="sort-icon">↕</span>';
    return sortDir === "asc"
      ? '<span class="sort-icon active">↑</span>'
      : '<span class="sort-icon active">↓</span>';
  }

  const header = `
    <div class="file-row header">
      <div></div>
      <div></div>
      <div class="sortable" onclick="sortBy('name')">
        ${I18N.name || "Name"} ${sortIcon("name")}
      </div>
      <div class="sortable" onclick="sortBy('size')">
        ${I18N.size || "Size"} ${sortIcon("size")}
      </div>
      <div class="sortable" onclick="sortBy('date')">
        ${I18N.modified || "Modified"} ${sortIcon("date")}
      </div>
      <div></div>
    </div>`;

  // folder rows
  const folderRows = folderItems.map(f => {
    return `
      <div class="file-row folder-row" data-action="goto-folder" data-path="${escapeHtml(f.path)}">
        <div class="file-checkbox"></div>
        <div class="file-icon-wrap folder">${icon("folder", "icon-sm")}</div>
        <div class="file-info">
          <div class="file-name">${escapeHtml(f.name)}</div>
          <div class="file-path">${I18N.folder || "Folder"}</div>
        </div>
        <div class="file-meta-cell">—</div>
        <div class="file-meta-cell">—</div>
        <div class="row-actions">
          <button class="row-btn" title="Rename" data-action="rename-folder" data-path="${escapeHtml(f.path)}" onclick="event.stopPropagation()">${icon("settings", "icon-sm")}</button>
          <button class="row-btn danger" title="Delete" data-action="delete-folder" data-path="${escapeHtml(f.path)}" onclick="event.stopPropagation()">${icon("trash", "icon-sm")}</button>
        </div>
      </div>`;
  }).join("");

  // file rows
  const fileRows = files.map(f => {
    const iconName = iconFor(f.name);
    const cls = pickIconClass(f.name);
    const dateStr = f.uploaded_at ? new Date(f.uploaded_at * 1000).toLocaleDateString() : "—";
    const encBadge = f.encrypted ? `<span class="file-enc-badge">🔐 ${I18N.encrypted_badge || "Encrypted"}</span>` : "";
    return `
      <div class="file-row">
        <label class="file-checkbox">
          <input type="checkbox" class="file-check" data-id="${f.id}" ${selectedFiles.has(f.id) ? "checked" : ""}>
        </label>
        <div class="${cls}" ${canPreview(f.name) ? `data-action="preview" data-id="${f.id}" data-name="${escapeHtml(f.name)}" style="cursor:pointer;"` : ""}>${icon(iconName, "icon-sm")}</div>
        <div class="file-info">
          <div class="file-name" title="${escapeHtml(f.path || f.name)}">${escapeHtml(f.name)}</div>
          ${f.encrypted ? `<div class="file-path">${encBadge}</div>` : ""}
        </div>
        <div class="file-meta-cell">${f.size_human}</div>
        <div class="file-meta-cell">${dateStr}</div>
        <div class="row-actions">
          ${canPreview(f.name) ? `<button class="row-btn" title="Preview" data-action="preview" data-id="${f.id}" data-name="${escapeHtml(f.name)}">${icon("eye", "icon-sm")}</button>` : ""}
          <button class="row-btn" title="Download" data-action="download" data-id="${f.id}">${icon("download", "icon-sm")}</button>
          <button class="row-btn danger" title="Delete" data-action="delete" data-id="${f.id}">${icon("trash", "icon-sm")}</button>
        </div>
      </div>`;
  }).join("");

  container.innerHTML = selectionBar + header + folderRows + fileRows;
  updateSelectionBar();
  renderRecent(files);
}


function pickIconClass(name) {
  const n = (name || "").toLowerCase();
  if (n.match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/)) return "file-icon-wrap image";
  if (n.match(/\.(mp4|webm|mkv|mov|avi)$/)) return "file-icon-wrap video";
  if (n.match(/\.(txt|md|log|doc|docx|pdf)$/)) return "file-icon-wrap text";
  if (n.match(/\.(zip|rar|7z|tar|gz)$/)) return "file-icon-wrap archive";
  return "file-icon-wrap";
}


function icon(name, cls) {
  const sizeMap = {
    "icon-sm": 15,
    "icon-lg": 22,
    "icon-xl": 36,
  };
  let size = 18;
  if (cls) {
    for (const k in sizeMap) {
      if (cls.includes(k)) size = sizeMap[k];
    }
  }
  const style = `width:${size}px;height:${size}px;min-width:${size}px;min-height:${size}px;max-width:${size}px;max-height:${size}px;display:inline-block;vertical-align:middle;flex-shrink:0;fill:none;color:inherit;`;
  return `<svg class="icon ${cls || ""}" width="${size}" height="${size}" style="${style}" aria-hidden="true"><use href="#i-${name}"/></svg>`;
}


function iconFor(filename) {
  const n = (filename || "").toLowerCase();
  if (n.match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/)) return "file-image";
  if (n.match(/\.(mp4|webm|mkv|mov|avi)$/)) return "file-video";
  if (n.match(/\.(mp3|ogg|wav|flac|m4a)$/)) return "file-audio";
  if (n.match(/\.pdf$/)) return "file";
  if (n.match(/\.(zip|rar|7z|tar|gz)$/)) return "file-archive";
  if (n.match(/\.(doc|docx)$/)) return "file";
  if (n.match(/\.(xls|xlsx|csv)$/)) return "file";
  if (n.match(/\.(py|js|ts|go|rs|java|cpp|c|h)$/)) return "file-code";
  return "file";
}


function renderRecent(files) {
  const el = document.getElementById("recent-list");
  if (!el) return;
  const recent = [...files].sort((a, b) => (b.uploaded_at || 0) - (a.uploaded_at || 0)).slice(0, 5);
  if (!recent.length) {
    el.innerHTML = `<div class="muted" style="font-size:0.85rem;text-align:center;padding:16px;">—</div>`;
    return;
  }
  el.innerHTML = recent.map(f => {
    const iconName = iconFor(f.name);
    return `
      <div class="recent-item">
        <div class="recent-icon">${icon(iconName, "icon-sm")}</div>
        <div class="recent-info">
          <div class="recent-name">${escapeHtml(f.name)}</div>
          <div class="recent-meta">${f.size_human}</div>
        </div>
      </div>`;
  }).join("");
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




// ============================================================
// Back button — ناوبری به پوشه‌ی والد
// ============================================================
function updateBackButton() {
  const btn = document.getElementById("back-btn");
  const titleEl = document.getElementById("page-title");
  if (!btn) return;

  if (currentFolder && currentFolder.length > 0) {
    // داخل پوشه‌ایم
    btn.style.display = "inline-flex";
    if (titleEl) {
      const parts = currentFolder.split("/");
      const folderName = parts[parts.length - 1];
      titleEl.textContent = "📁 " + folderName;
    }
  } else {
    // در root هستیم
    btn.style.display = "none";
    if (titleEl) {
      titleEl.textContent = "📁 " + (I18N.my_drive || "My Drive");
    }
  }
}

function goBack() {
  if (!currentFolder) return;
  const parts = currentFolder.split("/");
  parts.pop();
  const parent = parts.join("/");
  goToFolder(parent);
}


// ---------- Init ----------
document.addEventListener("DOMContentLoaded", () => {
  initPowerSave();
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




// ============================================================
// Sort by clicking on header
// ============================================================
function sortBy(field) {
  const sel = document.getElementById("sort-select");
  if (!sel) return;

  const current = sel.value;
  const [curField, curDir] = current.split("-");

  let newDir;
  if (curField === field) {
    // toggle direction
    newDir = curDir === "asc" ? "desc" : "asc";
  } else {
    // default direction per field
    newDir = field === "name" ? "asc" : "desc";
  }

  sel.value = `${field}-${newDir}`;
  loadFiles();
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

// ============================================================
// Proxy display: mask + copy
// ============================================================
function maskProxy(url) {
  if (!url || url === "—" || url.length < 20) return url || "—";
  const head = url.slice(0, 20);
  const tail = url.slice(-8);
  const stars = "★".repeat(Math.min(12, Math.max(4, url.length - 30)));
  return head + "  " + stars + "  " + tail;
}

function copyProxy() {
  const el = document.getElementById("proxy-current");
  if (!el) return;
  const real = el.dataset.full || el.textContent.trim();
  if (!real || real === "—") return;
  navigator.clipboard.writeText(real).then(
    () => toast(I18N.copied || "Copied!", "success"),
    () => toast("Copy failed", "error")
  );
}

// Override showProxy to display masked
async function showProxy() {
  const modal = document.getElementById("proxy-modal");
  if (!modal) return;
  modal.classList.add("open");

  try {
    const res = await fetch("/api/proxy");
    const data = await res.json();
    const currentEl = document.getElementById("proxy-current");
    const inputEl = document.getElementById("proxy-input");
    const toggleEl = document.getElementById("proxy-enabled-toggle");

    if (currentEl) {
      const real = data.proxy || "—";
      const maskEl = currentEl.querySelector(".proxy-mask");
      if (maskEl) {
        maskEl.textContent = maskProxy(real);
      } else {
        currentEl.textContent = maskProxy(real);
      }
      currentEl.dataset.full = real;
    }
    if (inputEl) inputEl.value = data.proxy || "";
    if (toggleEl) toggleEl.checked = data.enabled !== false;
  } catch (e) {
    console.warn("[zzoDrive] showProxy failed:", e);
  }
}

// ============================================================
// Power Save Mode
// ============================================================
const POWER_SAVE_KEY = "zzodrive_power_save";

function applyPowerSave(enabled) {
  if (enabled) {
    document.body.classList.add("power-save");
  } else {
    document.body.classList.remove("power-save");
  }
  // update status badge
  const status = document.getElementById("power-save-status");
  if (status) {
    status.textContent = enabled ? "ON" : "OFF";
    status.className = "power-save-status " + (enabled ? "on" : "off");
  }
  // update checkbox
  const toggle = document.getElementById("power-save-toggle");
  if (toggle) toggle.checked = enabled;
}

function togglePowerSave() {
  const toggle = document.getElementById("power-save-toggle");
  const enabled = toggle ? toggle.checked : false;
  try {
    localStorage.setItem(POWER_SAVE_KEY, enabled ? "1" : "0");
  } catch (e) { /* ignore */ }
  applyPowerSave(enabled);
  toast(enabled ? (I18N.power_save_on || "Power save ON") : (I18N.power_save_off || "Power save OFF"), "success");
}

function initPowerSave() {
  let enabled = false;
  try {
    enabled = localStorage.getItem(POWER_SAVE_KEY) === "1";
  } catch (e) { /* ignore */ }
  applyPowerSave(enabled);
}

// ============================================================
// Clear cache
// ============================================================
async function clearCache() {
  const btn = document.getElementById("cache-clear-btn");
  const status = document.getElementById("cache-status");
  if (btn) { btn.disabled = true; btn.style.opacity = "0.6"; }
  if (status) status.textContent = I18N.cache_clearing || "Clearing...";

  try {
    const res = await fetch("/api/cache/clear", { method: "POST" });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");
    if (status) status.textContent = (I18N.cache_cleared || "Freed") + ": " + data.freed_human;
    toast((I18N.cache_cleared || "Cache cleared") + " — " + data.freed_human, "success");
  } catch (e) {
    if (status) status.textContent = "";
    toast("Error: " + e.message, "error");
  } finally {
    if (btn) { btn.disabled = false; btn.style.opacity = "1"; }
  }
}

// ============================================================
// Saved proxies (multi-proxy manager)
// ============================================================

function maskProxyShort(url) {
  if (!url || url.length < 24) return url || "";
  return url.slice(0, 22) + "…" + url.slice(-6);
}

async function loadProxyList() {
  const list = document.getElementById("proxy-list");
  if (!list) return;

  try {
    const [proxiesRes, toggleRes] = await Promise.all([
      fetch("/api/proxies"),
      fetch("/api/proxy"),
    ]);
    const data = await proxiesRes.json();
    const toggleData = await toggleRes.json();

    // update master toggle
    const toggleEl = document.getElementById("proxy-enabled-toggle");
    if (toggleEl) toggleEl.checked = toggleData.enabled !== false;

    const items = data.proxies || [];
    if (!items.length) {
      list.innerHTML = `<div class="loading-small">${I18N.no_proxies || "No saved proxies yet"}</div>`;
      return;
    }

    list.innerHTML = items.map(p => `
      <div class="proxy-item ${p.active ? "active" : ""}" data-id="${p.id}"
           onclick="activateProxy('${p.id}')">
        <div class="proxy-radio"></div>
        <div class="proxy-info">
          <div class="proxy-name">
            ${escapeHtml(p.name)}
            ${p.active ? `<span class="proxy-badge">${I18N.active || "Active"}</span>` : ""}
          </div>
          <div class="proxy-url-mask" title="${escapeHtml(p.url)}">${escapeHtml(maskProxyShort(p.url))}</div>
        </div>
        <div class="proxy-actions">
          <button class="proxy-delete" title="${I18N.delete_all || "Delete"}"
                  onclick="event.stopPropagation(); deleteProxy('${p.id}')">
            <svg><use href="#i-trash"/></svg>
          </button>
        </div>
      </div>
    `).join("");
  } catch (e) {
    list.innerHTML = `<div class="loading-small">Error: ${e.message}</div>`;
  }
}

async function addProxy() {
  const nameEl = document.getElementById("new-proxy-name");
  const urlEl = document.getElementById("new-proxy-url");
  const name = nameEl ? nameEl.value.trim() : "";
  const url = urlEl ? urlEl.value.trim() : "";

  if (!url) {
    toast(I18N.proxy_url_required || "Proxy URL is required", "error");
    return;
  }

  try {
    const res = await fetch("/api/proxies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name || "Proxy", url: url }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "failed");

    if (nameEl) nameEl.value = "";
    if (urlEl) urlEl.value = "";
    toast(I18N.proxy_saved_short || "Proxy saved", "success");
    loadProxyList();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function activateProxy(id) {
  try {
    const res = await fetch(`/api/proxies/${id}/activate`, { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      toast(I18N.proxy_activated || "Proxy activated", "success");
      loadProxyList();
    } else {
      toast((I18N.proxy_test_fail || "Failed") + ": " + (data.error || "?"), "error");
      loadProxyList();
    }
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function deleteProxy(id) {
  if (!confirm(I18N.confirm_delete_proxy || "Delete this proxy?")) return;
  try {
    await fetch(`/api/proxies/${id}`, { method: "DELETE" });
    toast(I18N.proxy_deleted || "Proxy deleted", "success");
    loadProxyList();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function testCurrentProxyInput() {
  const urlEl = document.getElementById("new-proxy-url");
  const url = urlEl ? urlEl.value.trim() : "";
  if (!url) {
    toast(I18N.proxy_url_required || "Proxy URL is required", "error");
    return;
  }
  toast(I18N.testing || "Testing...", "success");
  try {
    const res = await fetch("/api/proxy/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxy: url }),
    });
    const data = await res.json();
    if (data.ok) {
      toast(I18N.proxy_test_ok || "Connection OK", "success");
    } else {
      toast((I18N.proxy_test_fail || "Failed") + ": " + (data.error || "?"), "error");
    }
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

// override showProxy
async function showProxy() {
  const modal = document.getElementById("proxy-modal");
  if (!modal) return;
  modal.classList.add("open");
  loadProxyList();
}
