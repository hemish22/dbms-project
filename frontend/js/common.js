// common.js — shared utilities: sidebar active state, toasts, modals

const API = "http://localhost:5500/api";

// Mark active sidebar link
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav-link").forEach(link => {
        if (link.getAttribute("href") === path) {
            // Remove inactive classes
            link.classList.remove("text-neutral-500", "hover:text-neutral-200", "hover:bg-white/5");
            // Add active classes
            link.classList.add("text-white", "bg-orange-600/10", "border-b-2", "border-orange-600");
            const icon = link.querySelector(".material-symbols-outlined");
            if (icon) {
                icon.classList.add("text-primary", "scale-110");
            }
        }
    });

    // Close modals on clicking outside or escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const openModals = document.querySelectorAll(".tailwind-modal:not(.hidden)");
            openModals.forEach(modal => closeModal(modal.id));
        }
    });
});

// Modal System replacement for Bootstrap Modals
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("hidden");
        // small delay to trigger transition
        setTimeout(() => {
            modal.querySelector(".modal-backdrop")?.classList.add("opacity-100");
            modal.querySelector(".modal-backdrop")?.classList.remove("opacity-0");
            modal.querySelector(".modal-panel")?.classList.add("opacity-100", "translate-y-0", "scale-100");
            modal.querySelector(".modal-panel")?.classList.remove("opacity-0", "translate-y-4", "sm:translate-y-0", "sm:scale-95");
        }, 10);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.querySelector(".modal-backdrop")?.classList.remove("opacity-100");
        modal.querySelector(".modal-backdrop")?.classList.add("opacity-0");
        modal.querySelector(".modal-panel")?.classList.remove("opacity-100", "translate-y-0", "scale-100");
        modal.querySelector(".modal-panel")?.classList.add("opacity-0", "translate-y-4", "sm:translate-y-0", "sm:scale-95");
        setTimeout(() => {
            modal.classList.add("hidden");
        }, 300);
    }
}


// Toast system
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    const t = document.createElement("div");
    t.className = `toast-item toast-${type}`;
    t.textContent = message;
    container.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => {
        t.classList.remove("show");
        setTimeout(() => t.remove(), 300);
    }, 3500);
}

function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

function fmtRs(val) {
    const n = parseFloat(val);
    if (isNaN(n)) return "₹0.00";
    return "₹" + n.toFixed(2);
}

async function apiFetch(path, options = {}) {
    const res = await fetch(API + path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || res.statusText);
    return data;
}

async function apiGet(path) { return apiFetch(path, { method: "GET" }); }
async function apiPost(path, body = {}) { return apiFetch(path, { method: "POST", body: JSON.stringify(body) }); }
async function apiPut(path, body = {}) { return apiFetch(path, { method: "PUT", body: JSON.stringify(body) }); }
async function apiDelete(path) { return apiFetch(path, { method: "DELETE" }); }

// Tailwind Status badges
function statusBadge(status) {
    const cls = { 
        Running: "bg-tertiary-container/15 text-tertiary border-tertiary/20", 
        Stopped: "bg-error-container/20 text-error border-error/30 animate-pulse", 
        Idle: "bg-secondary/15 text-secondary border-secondary/20",
        Modifying: "bg-secondary/15 text-secondary border-secondary/20"
    };
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls[status] || 'bg-surface-container-high text-on-surface border-outline-variant/20'}">${status}</span>`;
}

// Tailwind Suggestion type badges
function stypeBadge(t) {
    const cls = { 
        Stop: "bg-error/10 text-error border-error/20", 
        Resize: "bg-secondary/10 text-secondary border-secondary/20", 
        Schedule: "bg-tertiary/10 text-tertiary border-tertiary/20", 
        Migrate: "bg-primary/10 text-primary border-primary/20" 
    };
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls[t] || 'bg-surface-container-high text-on-surface border-outline-variant/20'}">${t}</span>`;
}

// Generic Tailwind Table Renderer
function renderTable(containerId, rows, columns) {
    const el = document.getElementById(containerId);
    if (!rows || rows.length === 0) {
        el.innerHTML = '<p class="text-on-surface-variant p-6 text-sm">No results.</p>';
        return;
    }
    const cols = columns || Object.keys(rows[0]);
    const th = cols.map(c => `<th class="px-6 py-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wider">${c}</th>`).join("");
    const trs = rows.map(row =>
        `<tr class="hover:bg-surface-container-highest/50 transition-colors group">
            ${cols.map(c => `<td class="px-6 py-4 whitespace-nowrap text-on-surface text-sm">${row[c] !== null && row[c] !== undefined ? row[c] : "—"}</td>`).join("")}
        </tr>`
    ).join("");
    el.innerHTML = `
      <div class="overflow-x-auto bg-surface-container-high rounded-xl border border-outline-variant/10">
        <table class="w-full text-left border-collapse">
          <thead><tr class="bg-surface-container-lowest border-b border-outline-variant/10">${th}</tr></thead>
          <tbody class="divide-y divide-outline-variant/5">${trs}</tbody>
        </table>
      </div>`;
}
