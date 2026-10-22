(function () {
  "use strict";

  const scriptURL = document.currentScript && document.currentScript.src;
  const dataURL = name => new URL(`../data/${name}.json`, scriptURL || document.baseURI).href;
  const downloadURL = name => new URL(`../downloads/${name}`, scriptURL || document.baseURI).href;
  const PAGE_SIZE = 25;
  const WAVEFORM_COLUMNS = ["id","source_id","catalogue","simulation_id","eos","eos_variant","m1_msun","m2_msun","mtot_msun","mchirp_msun","q","q_definition","q_original","q_original_definition","lambda1","lambda2","lambda_tilde","f_peak_khz","f_2_0_khz","f_2_0_status","f_spiral_khz","f_spiral_status","f_radial_khz","f_peak_early_khz","f_peak_late_khz","f_peak_mean_khz","f_peak_instantaneous_khz","f_merger_khz","f_gw_initial_hz","spectral_type","simulation_code","numerical_method","waveform_extraction","source_table","notes"];
  const RELATION_COLUMNS = ["relation_id","source_id","family","equation_label","equation_latex","dependent_variable","dependent_unit","independent_variables","calibration_population","applicability","source_table","source_path","r_squared_adjusted","max_residual","mean_residual","residual_std","residual_unit","review_status","notes"];
  const ranges = [
    ["mtot_msun", "Total mass (M☉)"], ["mchirp_msun", "Chirp mass (M☉)"],
    ["q", "Mass ratio q"], ["lambda_tilde", "Tidal deformability Λ̃"],
    ["f_peak_khz", "f_peak (kHz)"], ["f_2_0_khz", "f_2-0 (kHz)"],
    ["f_spiral_khz", "f_spiral (kHz)"],
  ];

  const text = value => value === null || value === undefined || value === "" ? "" : String(value);
  const shown = value => text(value) || "—";
  const escapeHTML = value => text(value).replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);
  const searchable = row => [
    ...Object.entries(row).filter(([, value]) => typeof value !== "object").map(([key, value]) => `${key} ${text(value)}`),
    row.source && `${row.source.title} ${row.source.authors} ${row.source.arxiv_id}`,
  ].join(" ").toLowerCase();
  const numericInRange = (value, minimum, maximum) => {
    if (minimum === "" && maximum === "") return true;
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return false;
    const number = Number(value);
    return (minimum === "" || number >= Number(minimum)) && (maximum === "" || number <= Number(maximum));
  };
  const compareValues = (left, right) => {
    if (left === null || left === "") return right === null || right === "" ? 0 : 1;
    if (right === null || right === "") return -1;
    if (typeof left === "number" && typeof right === "number") return left - right;
    return String(left).localeCompare(String(right), undefined, {numeric: true, sensitivity: "base"});
  };
  const csvCell = value => {
    const string = text(value);
    return /[",\n\r]/.test(string) ? `"${string.replace(/"/g, '""')}"` : string;
  };
  const rowsToCSV = (rows, columns) => [columns.join(","), ...rows.map(row => columns.map(column => csvCell(row[column])).join(","))].join("\r\n") + "\r\n";

  function filterWaveforms(records, filters) {
    const query = (filters.search || "").trim().toLowerCase();
    return records.filter(row => {
      if (query && !searchable(row).includes(query)) return false;
      if (filters.eos && row.eos !== filters.eos) return false;
      if (filters.eosVariant && row.eos_variant !== filters.eosVariant) return false;
      if (filters.source && row.source_id !== filters.source) return false;
      if (filters.code && row.simulation_code !== filters.code) return false;
      if (filters.spectral && row.spectral_type !== filters.spectral) return false;
      if (filters.massKind) {
        if (row.q === null) return false;
        const equal = Math.abs(Number(row.q) - 1) < 1e-9;
        if ((filters.massKind === "equal") !== equal) return false;
      }
      if (filters.availability && row[filters.availability] === null) return false;
      return Object.entries(filters.ranges || {}).every(([key, limits]) => numericInRange(row[key], limits.min, limits.max));
    });
  }

  function filterRelations(records, filters) {
    const query = (filters.search || "").trim().toLowerCase();
    return records.filter(row => (!query || searchable(row).includes(query)) &&
      (!filters.dependent || row.dependent_variable === filters.dependent) &&
      (!filters.family || row.family === filters.family) &&
      (!filters.source || row.source_id === filters.source) &&
      (!filters.status || row.implementation_status === filters.status));
  }

  window.EmpiricalRelationsExplorer = {filterWaveforms, filterRelations, compareValues, rowsToCSV, numericInRange};

  const load = name => fetch(dataURL(name)).then(response => {
    if (!response.ok) throw new Error(`Unable to load ${name}.json (${response.status})`);
    return response.json();
  });
  const selectOptions = (select, records, key, label = value => value) => {
    [...new Set(records.map(row => row[key]).filter(value => value !== null && value !== ""))]
      .sort((a, b) => compareValues(a, b)).forEach(value => select.add(new Option(label(value), value)));
  };
  const download = (filename, content) => {
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(new Blob([content], {type: "text/csv;charset=utf-8"}));
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(anchor.href);
  };
  const sourceLabel = row => row.source ? `${row.source.authors.split(";")[0]} (${row.source.publication_year})` : row.source_id;
  const sourceLink = row => row.source && row.source.abstract_url ? `<a href="${escapeHTML(row.source.abstract_url)}">${escapeHTML(row.source.title)}</a>` : escapeHTML(row.source_id);
  const detailList = entries => `<dl class="er-detail-grid">${entries.filter(([, value]) => value !== null && value !== "").map(([label, value]) => `<dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value)}</dd>`).join("")}</dl>`;
  const wireDialog = dialog => {
    dialog.querySelector(".er-dialog-close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  };
  const setSortable = (table, state, render) => table.querySelectorAll("th[data-key]").forEach(th => {
    th.tabIndex = 0; th.setAttribute("role", "button");
    const sort = () => { state.direction = state.sortKey === th.dataset.key && state.direction === 1 ? -1 : 1; state.sortKey = th.dataset.key; state.page = 1; render(); };
    th.addEventListener("click", sort);
    th.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); sort(); } });
  });
  const markSort = (table, state) => table.querySelectorAll("th[data-key]").forEach(th => th.setAttribute("aria-sort", th.dataset.key === state.sortKey ? (state.direction === 1 ? "ascending" : "descending") : "none"));

  async function initSummary() {
    const targets = [document.getElementById("er-summary"), document.getElementById("er-database-summary")].filter(Boolean);
    if (!targets.length) return;
    try {
      const metadata = await load("metadata");
      const cards = [[metadata.counts.waveforms, "waveforms"], [metadata.counts.eos, "EOS records"], [metadata.counts.relations, "relations"], [metadata.counts.sources, "source papers"]];
      const html = cards.map(([count, label]) => `<div class="er-stat"><strong>${count}</strong><span>${label}</span></div>`).join("") + `<div class="er-stat"><strong title="${metadata.dataset_sha256}">${metadata.dataset_sha256.slice(0, 8)}</strong><span>data fingerprint</span></div>`;
      targets.forEach(target => target.innerHTML = html);
    } catch (error) { targets.forEach(target => target.textContent = error.message); }
  }

  async function initWaveforms() {
    const root = document.getElementById("waveform-explorer"); if (!root) return;
    const records = await load("waveforms");
    const byId = id => document.getElementById(id);
    const table = byId("wf-table"), body = table.tBodies[0], dialog = byId("wf-dialog");
    const state = {page: 1, sortKey: "id", direction: 1, visible: records};
    selectOptions(byId("wf-eos"), records, "eos");
    selectOptions(byId("wf-source"), records, "source_id", value => sourceLabel(records.find(row => row.source_id === value)));
    selectOptions(byId("wf-code"), records, "simulation_code");
    selectOptions(byId("wf-spectral"), records, "spectral_type");
    const filterGrid = root.querySelector(".er-filter-grid");
    const variantLabel = document.createElement("label"); variantLabel.textContent = "EOS variant / family";
    const variant = document.createElement("select"); variant.id = "wf-eos-variant"; variant.add(new Option("All variants", "")); variantLabel.appendChild(variant); filterGrid.appendChild(variantLabel);
    selectOptions(variant, records, "eos_variant");
    byId("wf-ranges").innerHTML = ranges.map(([key, label]) => `<label>${label}<span class="er-range-pair"><input id="wf-${key}-min" type="number" step="any" inputmode="decimal" placeholder="Min" aria-label="Minimum ${label}"><input id="wf-${key}-max" type="number" step="any" inputmode="decimal" placeholder="Max" aria-label="Maximum ${label}"></span></label>`).join("");
    const controls = [...root.querySelectorAll("input, select")];
    const filters = () => ({search: byId("wf-search").value, eos: byId("wf-eos").value, eosVariant: variant.value, source: byId("wf-source").value, code: byId("wf-code").value, spectral: byId("wf-spectral").value, massKind: byId("wf-mass-kind").value, availability: byId("wf-availability").value, ranges: Object.fromEntries(ranges.map(([key]) => [key, {min: byId(`wf-${key}-min`).value, max: byId(`wf-${key}-max`).value}]))});
    const showDetail = row => {
      const physical = WAVEFORM_COLUMNS.map(key => [key, row[key]]);
      const provenance = (row.provenance || []).map(p => `${p.source_path}${p.source_line_start ? `:${p.source_line_start}` : ""} — ${p.review_status}`).join("; ");
      dialog.querySelector(".er-dialog-body").innerHTML = `<h2>${escapeHTML(row.simulation_id || row.id)}</h2>${detailList(physical)}<h3>Original publication</h3><p>${sourceLink(row)}<br>${escapeHTML(row.source.authors || "")}${row.source.doi ? `<br>DOI: ${escapeHTML(row.source.doi)}` : ""}</p><h3>Provenance</h3><p>${escapeHTML(provenance || "Unavailable")}</p>`;
      dialog.showModal();
    };
    const render = () => {
      state.visible = filterWaveforms(records, filters()).sort((a, b) => state.direction * compareValues(a[state.sortKey], b[state.sortKey]));
      const pages = Math.max(1, Math.ceil(state.visible.length / PAGE_SIZE)); state.page = Math.min(state.page, pages);
      const pageRows = state.visible.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);
      body.innerHTML = pageRows.map(row => `<tr tabindex="0" data-id="${escapeHTML(row.id)}"><td>${escapeHTML(shown(row.simulation_id || row.id))}</td><td>${escapeHTML(shown(row.eos))}</td><td>${escapeHTML(shown(row.mtot_msun))}</td><td>${escapeHTML(shown(row.q))}</td><td>${escapeHTML(shown(row.lambda_tilde))}</td><td>${escapeHTML(shown(row.f_peak_khz))}</td><td>${escapeHTML(shown(row.f_2_0_khz))}</td><td>${escapeHTML(shown(row.f_spiral_khz))}</td><td>${escapeHTML(sourceLabel(row))}</td></tr>`).join("");
      body.querySelectorAll("tr").forEach(tr => { const open = () => showDetail(records.find(row => row.id === tr.dataset.id)); tr.addEventListener("click", open); tr.addEventListener("keydown", event => { if (event.key === "Enter") open(); }); });
      byId("wf-count").textContent = `${state.visible.length} of ${records.length} waveforms`;
      byId("wf-empty").hidden = state.visible.length !== 0; table.parentElement.hidden = state.visible.length === 0;
      byId("wf-page").textContent = `Page ${state.page} of ${pages}`; byId("wf-prev").disabled = state.page === 1; byId("wf-next").disabled = state.page === pages;
      markSort(table, state);
    };
    controls.forEach(control => control.addEventListener(control.type === "search" ? "input" : "change", () => { state.page = 1; render(); }));
    byId("wf-reset").addEventListener("click", () => { controls.forEach(control => control.value = ""); state.page = 1; render(); });
    byId("wf-prev").addEventListener("click", () => { state.page--; render(); }); byId("wf-next").addEventListener("click", () => { state.page++; render(); });
    byId("wf-download").addEventListener("click", () => download("waveforms-filtered.csv", rowsToCSV(state.visible, WAVEFORM_COLUMNS)));
    setSortable(table, state, render); wireDialog(dialog); render();
  }

  async function initRelations() {
    const root = document.getElementById("relation-explorer"); if (!root) return;
    const records = await load("relations"); const byId = id => document.getElementById(id);
    const table = byId("rel-table"), body = table.tBodies[0], dialog = byId("rel-dialog");
    const state = {page: 1, sortKey: "relation_id", direction: 1, visible: records};
    selectOptions(byId("rel-dependent"), records, "dependent_variable"); selectOptions(byId("rel-family"), records, "family");
    selectOptions(byId("rel-source"), records, "source_id", value => sourceLabel(records.find(row => row.source_id === value)));
    const controls = [...root.querySelectorAll("input, select")];
    const filters = () => ({search: byId("rel-search").value, dependent: byId("rel-dependent").value, family: byId("rel-family").value, source: byId("rel-source").value, status: byId("rel-status").value});
    const showDetail = row => {
      const coefficients = row.coefficients.length ? row.coefficients.map(item => `<span class="er-chip">${escapeHTML(item.coefficient)} = ${escapeHTML(item.value)} (${escapeHTML(item.term)})</span>`).join("") : "<span class=\"er-missing\">No normalized coefficients</span>";
      const fields = [["Relation ID", row.relation_id], ["Predicts", `${row.dependent_variable} [${row.dependent_unit || "unit not reported"}]`], ["Independent variables", row.independent_variables], ["Calibration population", row.calibration_population], ["Applicability", row.applicability], ["Adjusted R²", row.r_squared_adjusted], ["Maximum residual", row.max_residual], ["Mean residual", row.mean_residual], ["Residual σ", row.residual_std], ["Residual unit", row.residual_unit], ["Review status", row.review_status], ["Implementation", row.implementation_status], ["Notes", row.notes]];
      dialog.querySelector(".er-dialog-body").innerHTML = `<h2>${escapeHTML(row.dependent_variable)} — ${escapeHTML(row.family)}</h2><h3>Published expression</h3><pre class="er-equation">${escapeHTML(row.equation_latex)}</pre><h3>Coefficients</h3><p>${coefficients}</p>${detailList(fields)}<h3>Original publication</h3><p>${sourceLink(row)}<br>${escapeHTML(row.source.authors || "")}</p>`;
      dialog.showModal();
    };
    const render = () => {
      state.visible = filterRelations(records, filters()).sort((a, b) => state.direction * compareValues(a[state.sortKey], b[state.sortKey]));
      const pages = Math.max(1, Math.ceil(state.visible.length / PAGE_SIZE)); state.page = Math.min(state.page, pages);
      const pageRows = state.visible.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);
      body.innerHTML = pageRows.map(row => `<tr tabindex="0" data-id="${escapeHTML(row.relation_id)}"><td>${escapeHTML(row.dependent_variable)}</td><td>${escapeHTML(row.family)}</td><td>${escapeHTML(row.independent_variables)}</td><td>${escapeHTML(shown(row.residual_std))} ${escapeHTML(row.residual_unit || "")}</td><td>${escapeHTML(sourceLabel(row))}</td><td>${escapeHTML(row.implementation_status)}</td></tr>`).join("");
      body.querySelectorAll("tr").forEach(tr => { const open = () => showDetail(records.find(row => row.relation_id === tr.dataset.id)); tr.addEventListener("click", open); tr.addEventListener("keydown", event => { if (event.key === "Enter") open(); }); });
      byId("rel-count").textContent = `${state.visible.length} of ${records.length} relations`; byId("rel-empty").hidden = state.visible.length !== 0; table.parentElement.hidden = state.visible.length === 0;
      byId("rel-page").textContent = `Page ${state.page} of ${pages}`; byId("rel-prev").disabled = state.page === 1; byId("rel-next").disabled = state.page === pages; markSort(table, state);
    };
    controls.forEach(control => control.addEventListener(control.type === "search" ? "input" : "change", () => { state.page = 1; render(); }));
    byId("rel-reset").addEventListener("click", () => { controls.forEach(control => control.value = ""); state.page = 1; render(); });
    byId("rel-prev").addEventListener("click", () => { state.page--; render(); }); byId("rel-next").addEventListener("click", () => { state.page++; render(); });
    byId("rel-download").addEventListener("click", () => download("relations-filtered.csv", rowsToCSV(state.visible, RELATION_COLUMNS)));
    setSortable(table, state, render); wireDialog(dialog); render();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-er-download]").forEach(link => { link.href = downloadURL(link.dataset.erDownload); });
    Promise.all([initSummary(), initWaveforms(), initRelations()]).catch(error => {
    const root = document.querySelector(".er-explorer"); if (root) root.innerHTML = `<p class="admonition is-danger">Explorer failed to load: ${escapeHTML(error.message)}</p>`;
    });
  });
}());
