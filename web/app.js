// Reading Atlas viewer: a dependency-free canvas map with pan, zoom, search and details.
(() => {
  const canvas = document.getElementById("map");
  const ctx = canvas.getContext("2d");
  const tooltip = document.getElementById("tooltip");
  const panel = document.getElementById("panel");
  const detail = document.getElementById("detail");
  const search = document.getElementById("search");
  const countEl = document.getElementById("count");

  // Colour-blind-friendly categorical palette; cycles if there are more clusters.
  const PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948",
    "#b07aa1", "#ff9da7", "#9c755f", "#86bcb6", "#d37295", "#8cd17d"];

  let atlas = null;
  let view = { scale: 1, tx: 0, ty: 0 };
  let hovered = -1;
  let selected = -1;
  let visible = [];      // bool per point after source filter
  let matches = null;    // Set of indices matching search, or null

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const colorFor = (c) => (c < 0 ? css("--noise") : PALETTE[c % PALETTE.length]);

  // ---- geometry ----------------------------------------------------------
  function size() {
    const dpr = window.devicePixelRatio || 1;
    const { width, height } = canvas.getBoundingClientRect();
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { width, height };
  }
  function base() {
    const { width, height } = canvas.getBoundingClientRect();
    const pad = 40;
    // On wide screens, keep the map clear of the details panel when it is open.
    const reserve = !panel.hidden && width > 900 ? panel.offsetWidth + 12 : 0;
    const w = width - reserve;
    const s = Math.min(w, height) - pad * 2;
    return { s, ox: (w - s) / 2, oy: (height - s) / 2 };
  }
  function toScreen(x, y) {
    const b = base();
    return [(b.ox + x * b.s) * view.scale + view.tx, (b.oy + (1 - y) * b.s) * view.scale + view.ty];
  }

  // ---- drawing -----------------------------------------------------------
  function draw() {
    if (!atlas) return;
    const { width, height } = size();
    ctx.clearRect(0, 0, width, height);
    const r = Math.max(2.5, Math.min(7, 3.5 * Math.sqrt(view.scale)));
    const dim = matches !== null;

    atlas.points.forEach((p, i) => {
      if (!visible[i]) return;
      const [sx, sy] = toScreen(p.x, p.y);
      if (sx < -10 || sy < -10 || sx > width + 10 || sy > height + 10) return;
      const hit = !dim || matches.has(i);
      ctx.globalAlpha = hit ? 0.9 : 0.12;
      ctx.fillStyle = colorFor(p.c);
      ctx.beginPath();
      ctx.arc(sx, sy, hit && dim ? r + 1.5 : r, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;

    // Neighbour lines for the selected point.
    if (selected >= 0) {
      const p = atlas.points[selected];
      const [sx, sy] = toScreen(p.x, p.y);
      ctx.strokeStyle = css("--accent");
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.5;
      p.nn.forEach((j) => {
        const [nx, ny] = toScreen(atlas.points[j].x, atlas.points[j].y);
        ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(nx, ny); ctx.stroke();
      });
      ctx.globalAlpha = 1;
    }

    [hovered, selected].forEach((i) => {
      if (i < 0) return;
      const [sx, sy] = toScreen(atlas.points[i].x, atlas.points[i].y);
      ctx.strokeStyle = css("--text");
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(sx, sy, r + 3, 0, Math.PI * 2); ctx.stroke();
    });

    // Cluster labels, biggest first so they win when they collide.
    ctx.font = "600 12px ui-sans-serif, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const placed = [];
    [...atlas.clusters].sort((a, b) => b.size - a.size).forEach((c) => {
      const [sx, sy] = toScreen(c.x, c.y);
      const w = ctx.measureText(c.label).width + 12;
      const box = [sx - w / 2, sy - 10, sx + w / 2, sy + 10];
      if (placed.some((q) => box[0] < q[2] && box[2] > q[0] && box[1] < q[3] && box[3] > q[1])) return;
      placed.push(box);
      ctx.lineWidth = 4;
      ctx.strokeStyle = css("--bg");
      ctx.strokeText(c.label, sx, sy);
      ctx.fillStyle = css("--label");
      ctx.fillText(c.label, sx, sy);
    });
  }

  // ---- interaction -------------------------------------------------------
  function pick(mx, my) {
    let best = -1, bestD = 12 * 12;
    atlas.points.forEach((p, i) => {
      if (!visible[i]) return;
      const [sx, sy] = toScreen(p.x, p.y);
      const d = (sx - mx) ** 2 + (sy - my) ** 2;
      if (d < bestD) { bestD = d; best = i; }
    });
    return best;
  }

  let drag = null;
  canvas.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty, moved: false };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    if (drag) {
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) { drag.moved = true; canvas.classList.add("dragging"); }
      view.tx = drag.tx + dx; view.ty = drag.ty + dy;
      draw();
      return;
    }
    const i = pick(mx, my);
    if (i !== hovered) { hovered = i; draw(); }
    if (i >= 0) {
      tooltip.textContent = atlas.points[i].title;
      tooltip.hidden = false;
      tooltip.style.left = Math.min(mx + 14, rect.width - 290) + "px";
      tooltip.style.top = my + 14 + "px";
    } else {
      tooltip.hidden = true;
    }
  });
  canvas.addEventListener("pointerup", (e) => {
    const wasClick = drag && !drag.moved;
    drag = null;
    canvas.classList.remove("dragging");
    if (wasClick) {
      const rect = canvas.getBoundingClientRect();
      const i = pick(e.clientX - rect.left, e.clientY - rect.top);
      i >= 0 ? select(i) : closePanel();
    }
  });
  canvas.addEventListener("pointerleave", () => { hovered = -1; tooltip.hidden = true; draw(); });
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const k = Math.exp(-e.deltaY * 0.0015);
    const next = Math.min(40, Math.max(0.5, view.scale * k));
    const f = next / view.scale;
    view.tx = mx - (mx - view.tx) * f;
    view.ty = my - (my - view.ty) * f;
    view.scale = next;
    draw();
  }, { passive: false });

  // ---- panel -------------------------------------------------------------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function select(i) {
    selected = i;
    const p = atlas.points[i];
    const cluster = atlas.clusters.find((c) => c.id === p.c);
    const safeUrl = p.url && /^https?:\/\//.test(p.url) ? p.url : null;
    detail.innerHTML = `
      <h2>${esc(p.title)}</h2>
      <div class="meta muted">${esc(p.source)}${p.created ? " · " + esc(p.created) : ""}
        ${cluster ? " · " + esc(cluster.label) : ""}</div>
      ${p.tags.map((t) => `<span class="chip">${esc(t)}</span>`).join("")}
      ${p.snippet ? `<p>${esc(p.snippet)}</p>` : ""}
      ${safeUrl ? `<p><a href="${esc(safeUrl)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></p>` : ""}
      ${p.nn.length ? `<h3>Closest in meaning</h3><ul>${p.nn.map((j) =>
        `<li><button data-i="${j}">${esc(atlas.points[j].title)}</button></li>`).join("")}</ul>` : ""}
    `;
    detail.querySelectorAll("button[data-i]").forEach((b) =>
      b.addEventListener("click", () => select(Number(b.dataset.i))));
    panel.hidden = false;
    history.replaceState(null, "", "#p=" + p.id);  // shareable link to this item
    draw();
  }
  function closePanel() {
    selected = -1;
    panel.hidden = true;
    history.replaceState(null, "", location.pathname + location.search);
    draw();
  }
  function selectFromHash() {
    const id = new URLSearchParams(location.hash.slice(1)).get("p");
    const i = id ? atlas.points.findIndex((p) => p.id === id) : -1;
    if (i >= 0) select(i);
  }
  document.getElementById("close").addEventListener("click", closePanel);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePanel(); });

  // ---- search & filters --------------------------------------------------
  function applyFilters() {
    const on = new Set([...document.querySelectorAll(".filters input:checked")].map((x) => x.value));
    visible = atlas.points.map((p) => on.has(p.source));
    const q = search.value.trim().toLowerCase();
    matches = q
      ? new Set(atlas.points.flatMap((p, i) =>
          (p.title + " " + p.snippet + " " + p.tags.join(" ")).toLowerCase().includes(q) ? [i] : []))
      : null;
    const shown = visible.filter(Boolean).length;
    countEl.textContent = matches
      ? `${[...matches].filter((i) => visible[i]).length} of ${shown} match`
      : `${shown} items · ${atlas.clusters.length} topics`;
    draw();
  }
  search.addEventListener("input", applyFilters);
  document.querySelectorAll(".filters input").forEach((x) => x.addEventListener("change", applyFilters));

  // ---- boot --------------------------------------------------------------
  window.addEventListener("resize", draw);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
  fetch("data/atlas.json", { cache: "no-cache" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => { atlas = data; applyFilters(); selectFromHash(); })
    .catch(() => {
      countEl.textContent = "No atlas found. Run `atlas build` to create web/data/atlas.json.";
    });
})();
