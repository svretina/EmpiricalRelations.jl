# Empirical-relations catalogue

Search published relations by dependent variable, fit family, or publication. Record
details include coefficients, applicability limits, reported residuals, and the source
equation. Each record also provides a copyable BibTeX citation and dependency-free
Julia and Python implementations. Frequencies are expressed in kHz, masses in solar
masses, and radii in km unless a record states otherwise. Variable names therefore
omit units; the residual column retains the unit reported by the publication.

```@raw html
<section id="relation-explorer" class="er-explorer" aria-label="Empirical relations explorer">
  <div class="er-toolbar"><label class="er-search">Search relations<input id="rel-search" type="search" placeholder="Frequency, variable, author, paper…"></label><button id="rel-reset" class="er-button" type="button">Reset filters</button></div>
  <div class="er-filter-grid">
    <label>Predicted quantity<select id="rel-dependent"><option value="">All quantities</option></select></label>
    <label>Relation family<select id="rel-family"><option value="">All families</option></select></label>
    <label>Source paper<select id="rel-source"><option value="">All sources</option></select></label>
    <label>Implementation<select id="rel-status"><option value="">Any status</option><option value="catalogued">Catalogued</option></select></label>
  </div>
  <div class="er-results-bar"><strong id="rel-count" aria-live="polite">Loading…</strong><div><button id="rel-download" class="er-button" type="button">Download filtered CSV</button><a class="er-button" href="#" data-er-download="relations.csv" download>Full relations CSV</a><a class="er-button" href="#" data-er-download="coefficients.csv" download>Coefficients CSV</a></div></div>
  <div class="er-table-wrap"><table id="rel-table" class="er-table"><thead><tr><th data-key="dependent_variable">Predicts</th><th data-key="family">Family</th><th data-key="independent_variables">Inputs</th><th data-key="residual_std">Residual σ</th><th data-key="source_id">Source</th><th data-key="implementation_status">Status</th></tr></thead><tbody></tbody></table></div>
  <div id="rel-empty" class="er-empty" hidden>No relations match the active filters.</div>
  <nav class="er-pagination" aria-label="Relation result pages"><button id="rel-prev" type="button">Previous</button><span id="rel-page"></span><button id="rel-next" type="button">Next</button></nav>
  <dialog id="rel-dialog" class="er-dialog"><button class="er-dialog-close" type="button" aria-label="Close">×</button><div class="er-dialog-body"></div></dialog>
</section>
```
