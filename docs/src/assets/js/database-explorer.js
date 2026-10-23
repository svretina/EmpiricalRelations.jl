(function () {
  "use strict";

  const scriptURL = document.currentScript && document.currentScript.src;
  const dataURL = name => new URL(`../data/${name}.json`, scriptURL || document.baseURI).href;
  const downloadURL = name => new URL(`../downloads/${name}`, scriptURL || document.baseURI).href;
  const PAGE_SIZE = 25;
  const WAVEFORM_COLUMNS = ["id","source_id","catalogue","simulation_id","eos","eos_variant","m1_msun","m2_msun","mtot_msun","mchirp_msun","q","q_definition","q_original","q_original_definition","lambda1","lambda2","lambda_tilde","f_peak_khz","f_2_0_khz","f_2_0_status","f_spiral_khz","f_spiral_status","f_radial_khz","f_peak_early_khz","f_peak_late_khz","f_peak_mean_khz","f_peak_instantaneous_khz","f_merger_khz","f_gw_initial_hz","spectral_type","simulation_code","numerical_method","waveform_extraction","source_table","notes"];
  const RELATION_COLUMNS = ["relation_id","source_id","family","equation_label","equation_latex","dependent_variable","dependent_unit","independent_variables","calibration_population","applicability","source_table","source_path","r_squared_adjusted","max_residual","mean_residual","residual_std","residual_unit","review_status","notes"];
  const ranges = [
    ["mtot_msun", "Total mass (M☉)", String.raw`M_{\mathrm{tot}}\,[M_\odot]`],
    ["mchirp_msun", "Chirp mass (M☉)", String.raw`\mathcal{M}\,[M_\odot]`],
    ["q", "Mass ratio q", "q"], ["lambda_tilde", "Tidal deformability", String.raw`\widetilde{\Lambda}`],
    ["f_peak_khz", "Peak frequency (kHz)", String.raw`f_{\mathrm{peak}}\,[\mathrm{kHz}]`],
    ["f_2_0_khz", "Mode-coupling frequency (kHz)", String.raw`f_{2-0}\,[\mathrm{kHz}]`],
    ["f_spiral_khz", "Spiral frequency (kHz)", String.raw`f_{\mathrm{spiral}}\,[\mathrm{kHz}]`],
  ];
  const symbols = {
    m1_msun: String.raw`m_1`, m2_msun: String.raw`m_2`,
    mtot_msun: String.raw`M_{\mathrm{tot}}`, total_mass_msun: String.raw`M_{\mathrm{tot}}`,
    mchirp_msun: String.raw`\mathcal{M}`, q: "q", eta: String.raw`\eta`,
    lambda1: String.raw`\Lambda_1`, lambda2: String.raw`\Lambda_2`, lambda_tilde: String.raw`\widetilde{\Lambda}`,
    kappa_2_T: String.raw`\kappa_2^T`, f_peak_khz: String.raw`f_{\mathrm{peak}}`, f_peak_hz: String.raw`f_{\mathrm{peak}}`,
    f_2_0_khz: String.raw`f_{2-0}`, f_spiral_khz: String.raw`f_{\mathrm{spiral}}`, f_radial_khz: String.raw`f_0`,
    f_peak_early_khz: String.raw`f_{\mathrm{peak}}^{\mathrm{early}}`, f_peak_late_khz: String.raw`f_{\mathrm{peak}}^{\mathrm{late}}`,
    f_peak_mean_khz: String.raw`\overline{f}_{\mathrm{peak}}`, f_peak_instantaneous_khz: String.raw`f_{\mathrm{peak}}^{\mathrm{inst}}`,
    f_peak_instantaneous_hz: String.raw`f_{\mathrm{peak}}^{\mathrm{inst}}`, f_merger_khz: String.raw`f_{\mathrm{mrg}}`,
    f_merger_hz: String.raw`f_{\mathrm{mrg}}`, f_gw_initial_hz: String.raw`f_{\mathrm{GW}}^{\mathrm{initial}}`,
    r_1_2_km: String.raw`R_{1.2}`, r_1_4_km: String.raw`R_{1.4}`, r_1_6_km: String.raw`R_{1.6}`, r_1_8_km: String.raw`R_{1.8}`,
    "Mf_2": String.raw`M f_2`, "f_peak_khz*mchirp_msun": String.raw`f_{\mathrm{peak}}\mathcal{M}`,
    "M\\omega_22^\\textmrg": String.raw`M\omega_{22}^{\mathrm{mrg}}`, "E_b^\\textmrg": String.raw`E_b^{\mathrm{mrg}}`,
    "j^\\textmrg": String.raw`j^{\mathrm{mrg}}`, "R": "R", "R^90\\%": String.raw`R^{90\%}`,
    "R^cc": String.raw`R^{\mathrm{cc}}`, "\\Lambda^1/5": String.raw`\Lambda^{1/5}`,
  };

  const text = value => value === null || value === undefined || value === "" ? "" : String(value);
  const shown = value => text(value) || "—";
  const escapeHTML = value => text(value).replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);
  const inlineMath = latex => `\\(${escapeHTML(latex)}\\)`;
  const symbolHTML = value => {
    const valueText = text(value);
    const direct = symbols[valueText];
    if (direct) return inlineMath(direct);
    const power = valueText.match(/^(.+)\^\(([-+]?\d+(?:\/\d+)?)\)$/);
    if (power && symbols[power[1]]) return inlineMath(`${symbols[power[1]]}^{${power[2]}}`);
    return escapeHTML(valueText);
  };
  const variablesHTML = value => text(value).split(";").map(symbolHTML).join(", ");
  const fieldLabelHTML = key => symbols[key] ? inlineMath(symbols[key]) : escapeHTML(text(key).replaceAll("_", " "));
  const equationLatex = value => {
    let latex = text(value).trim().replace(/^\$|\$$/g, "").replace(/,\s*$/, "");
    const aliases = [
      [/\bM_chirp\b/g, String.raw`\mathcal{M}`], [/\bf_j\b/g, String.raw`f_j`],
      [/\bR_x\b/g, String.raw`R_x`], [/\bkappa_2_T\b/g, String.raw`\kappa_2^T`],
      [/\bMsun\b/g, String.raw`M_\odot`], [/\blog10\b/g, String.raw`\log_{10}`],
      [/\b([abcdn])([0-9])\b/g, "$1_{$2}"],
    ];
    aliases.forEach(([pattern, replacement]) => { latex = latex.replace(pattern, replacement); });
    if (latex.includes("&") || latex.includes(String.raw`\\`)) {
      latex = String.raw`\begin{aligned}` + latex.replaceAll(String.raw`\nonumber`, "") + String.raw`\end{aligned}`;
    }
    return latex;
  };
  const queueMathJax2 = (engine, element) => {
    if (engine && engine.Hub) engine.Hub.Queue(["Typeset", engine.Hub, element]);
  };
  const typesetMath = (element, attempt = 0) => {
    if (!element) return;
    if (!window.MathJax) {
      if (typeof window.require === "function") {
        window.require(["mathjax"], engine => queueMathJax2(engine, element));
        return;
      }
      if (attempt < 50) window.setTimeout(() => typesetMath(element, attempt + 1), 100);
      return;
    }
    if (window.MathJax.typesetPromise) {
      if (window.MathJax.typesetClear) window.MathJax.typesetClear([element]);
      window.MathJax.typesetPromise([element]).catch(() => {});
    } else queueMathJax2(window.MathJax, element);
  };
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

  window.EmpiricalRelationsExplorer = {filterWaveforms, filterRelations, compareValues, rowsToCSV, numericInRange, symbolHTML};

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
  const copyText = async (value, button) => {
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
      else {
        const area = document.createElement("textarea");
        area.value = value; area.style.position = "fixed"; area.style.opacity = "0";
        document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove();
      }
      const original = button.textContent; button.textContent = "Copied";
      window.setTimeout(() => { button.textContent = original; }, 1600);
    } catch (_) {
      button.textContent = "Copy failed";
    }
  };
  const sourceLabel = row => row.source ? `${row.source.authors.split(";")[0]} (${row.source.publication_year})` : row.source_id;
  const sourceLink = row => row.source && row.source.abstract_url ? `<a href="${escapeHTML(row.source.abstract_url)}">${escapeHTML(row.source.title)}</a>` : escapeHTML(row.source_id);
  const detailList = entries => `<dl class="er-detail-grid">${entries.filter(([, value]) => value !== null && value !== "").map(([label, value, valueIsHTML = false]) => `<dt>${fieldLabelHTML(label)}</dt><dd>${valueIsHTML ? value : escapeHTML(value)}</dd>`).join("")}</dl>`;
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
    byId("wf-ranges").innerHTML = ranges.map(([key, label, latex]) => `<label>${inlineMath(latex)}<span class="er-range-pair"><input id="wf-${key}-min" type="number" step="any" inputmode="decimal" placeholder="Min" aria-label="Minimum ${label}"><input id="wf-${key}-max" type="number" step="any" inputmode="decimal" placeholder="Max" aria-label="Maximum ${label}"></span></label>`).join("");
    typesetMath(byId("wf-ranges"));
    const controls = [...root.querySelectorAll("input, select")];
    const filters = () => ({search: byId("wf-search").value, eos: byId("wf-eos").value, eosVariant: variant.value, source: byId("wf-source").value, code: byId("wf-code").value, spectral: byId("wf-spectral").value, massKind: byId("wf-mass-kind").value, availability: byId("wf-availability").value, ranges: Object.fromEntries(ranges.map(([key]) => [key, {min: byId(`wf-${key}-min`).value, max: byId(`wf-${key}-max`).value}]))});
    const showDetail = row => {
      const physical = WAVEFORM_COLUMNS.map(key => [key, row[key]]);
      const provenance = (row.provenance || []).map(p => `${p.source_path}${p.source_line_start ? `:${p.source_line_start}` : ""} — ${p.review_status}`).join("; ");
      dialog.querySelector(".er-dialog-body").innerHTML = `<h2>${escapeHTML(row.simulation_id || row.id)}</h2>${detailList(physical)}<h3>Original publication</h3><p>${sourceLink(row)}<br>${escapeHTML(row.source.authors || "")}${row.source.doi ? `<br>DOI: ${escapeHTML(row.source.doi)}` : ""}</p><h3>Provenance</h3><p>${escapeHTML(provenance || "Unavailable")}</p>`;
      dialog.showModal();
      typesetMath(dialog.querySelector(".er-dialog-body"));
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
      const predicts = symbolHTML(row.dependent_variable);
      const fields = [["Relation ID", row.relation_id], ["Predicts", predicts, true], ["Independent variables", variablesHTML(row.independent_variables), true], ["Calibration population", row.calibration_population], ["Applicability", row.applicability], ["Adjusted R²", row.r_squared_adjusted], ["Maximum residual", row.max_residual], ["Mean residual", row.mean_residual], ["Residual σ", row.residual_std], ["Residual unit", row.residual_unit], ["Review status", row.review_status], ["Implementation", row.implementation_status], ["Notes", row.notes]];
      const initialLanguage = "julia";
      dialog.querySelector(".er-dialog-body").innerHTML = `<h2>${symbolHTML(row.dependent_variable)} — ${escapeHTML(row.family)}</h2><h3>Published expression</h3><div class="er-equation">\\[${escapeHTML(equationLatex(row.equation_latex))}\\]</div><h3>Coefficients</h3><p>${coefficients}</p>${detailList(fields)}<h3>Implementation</h3><div class="er-snippet-toolbar"><label>Language <select class="er-code-language"><option value="julia">Julia</option><option value="python">Python</option></select></label><button class="er-button er-copy-code" type="button">Copy code</button></div><pre class="er-code-block"><code>${escapeHTML(row.code[initialLanguage])}</code></pre><h3>Citation</h3><div class="er-snippet-toolbar"><span>BibTeX</span><button class="er-button er-copy-bibtex" type="button">Copy BibTeX</button></div><pre class="er-code-block er-bibtex"><code>${escapeHTML(row.source.bibtex)}</code></pre><h3>Original publication</h3><p>${sourceLink(row)}<br>${escapeHTML(row.source.authors || "")}</p>`;
      const language = dialog.querySelector(".er-code-language");
      const code = dialog.querySelector(".er-code-block code");
      language.addEventListener("change", () => { code.textContent = row.code[language.value]; });
      dialog.querySelector(".er-copy-code").addEventListener("click", event => copyText(row.code[language.value], event.currentTarget));
      dialog.querySelector(".er-copy-bibtex").addEventListener("click", event => copyText(row.source.bibtex, event.currentTarget));
      dialog.showModal();
      typesetMath(dialog.querySelector(".er-dialog-body"));
    };
    const render = () => {
      state.visible = filterRelations(records, filters()).sort((a, b) => state.direction * compareValues(a[state.sortKey], b[state.sortKey]));
      const pages = Math.max(1, Math.ceil(state.visible.length / PAGE_SIZE)); state.page = Math.min(state.page, pages);
      const pageRows = state.visible.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);
      body.innerHTML = pageRows.map(row => `<tr tabindex="0" data-id="${escapeHTML(row.relation_id)}"><td>${symbolHTML(row.dependent_variable)}</td><td>${escapeHTML(row.family)}</td><td>${variablesHTML(row.independent_variables)}</td><td>${escapeHTML(shown(row.residual_std))} ${escapeHTML(row.residual_unit || "")}</td><td>${escapeHTML(sourceLabel(row))}</td><td>${escapeHTML(row.implementation_status)}</td></tr>`).join("");
      typesetMath(body);
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
