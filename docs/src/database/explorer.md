# Interactive waveform explorer

The table lists normalized waveform records with local search, filters, sorting, and
CSV export. A dash denotes an unavailable value. Frequencies are in kHz and masses are
in solar masses.

```@raw html
<section id="waveform-explorer" class="er-explorer" aria-label="Waveform database explorer">
  <div class="er-toolbar">
    <label class="er-search">Search records
      <input id="wf-search" type="search" placeholder="EOS, paper, author, simulation, notes…" autocomplete="off">
    </label>
    <button id="wf-reset" class="er-button" type="button">Reset filters</button>
  </div>
  <details class="er-filter-panel" open>
    <summary>Filters</summary>
    <div class="er-filter-grid">
      <label>EOS<select id="wf-eos"><option value="">All EOS</option></select></label>
      <label>Source paper<select id="wf-source"><option value="">All sources</option></select></label>
      <label>Simulation code<select id="wf-code"><option value="">All codes</option></select></label>
      <label>Spectral type<select id="wf-spectral"><option value="">All types</option></select></label>
      <label>Mass configuration<select id="wf-mass-kind"><option value="">All</option><option value="equal">Equal mass</option><option value="unequal">Unequal mass</option></select></label>
      <label>Frequency availability<select id="wf-availability"><option value="">Any</option><option value="f_peak_khz">Has peak frequency</option><option value="f_2_0_khz">Has mode-coupling frequency</option><option value="f_spiral_khz">Has spiral frequency</option></select></label>
    </div>
    <div id="wf-ranges" class="er-range-grid"></div>
  </details>
  <div class="er-results-bar">
    <strong id="wf-count" aria-live="polite">Loading…</strong>
    <div><button id="wf-download" class="er-button" type="button">Download filtered CSV</button>
    <a class="er-button" href="#" data-er-download="waveforms.csv" download>Full waveform CSV</a>
    <a class="er-button" href="#" data-er-download="eos.csv" download>EOS metadata</a></div>
  </div>
  <div class="er-table-wrap"><table id="wf-table" class="er-table">
    <thead><tr><th data-key="simulation_id">Simulation</th><th data-key="eos">EOS</th><th data-key="mtot_msun">\(M_{\mathrm{tot}}\)</th><th data-key="q">\(q\)</th><th data-key="lambda_tilde">\(\widetilde{\Lambda}\)</th><th data-key="f_peak_khz">\(f_{\mathrm{peak}}\)</th><th data-key="f_2_0_khz">\(f_{2-0}\)</th><th data-key="f_spiral_khz">\(f_{\mathrm{spiral}}\)</th><th data-key="source_id">Source</th></tr></thead>
    <tbody></tbody>
  </table></div>
  <div id="wf-empty" class="er-empty" hidden>No records match the active filters.</div>
  <nav class="er-pagination" aria-label="Waveform result pages"><button id="wf-prev" type="button">Previous</button><span id="wf-page"></span><button id="wf-next" type="button">Next</button></nav>
  <dialog id="wf-dialog" class="er-dialog"><button class="er-dialog-close" type="button" aria-label="Close">×</button><div class="er-dialog-body"></div></dialog>
</section>
```

The complete table, including the original numerical text, is available as
[`data/waveforms.csv`](https://github.com/svretina/EmpiricalRelations.jl/blob/master/data/waveforms.csv).
