const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
global.window = {};
global.document = {currentScript: {src: "https://example.test/assets/js/database-explorer.js"}, addEventListener() {}};
vm.runInThisContext(fs.readFileSync("docs/src/assets/js/database-explorer.js", "utf8"));
const core = window.EmpiricalRelationsExplorer;

assert.strictEqual(core.symbolHTML("r_1_8_km"), String.raw`\(R_{1.8}\)`);
assert.strictEqual(core.symbolHTML("f_peak_khz"), String.raw`\(f_{\mathrm{peak}}\)`);
assert.strictEqual(core.symbolHTML("mchirp_msun"), String.raw`\(\mathcal{M}\)`);

const records = [
  {id:"a", eos:"DD2", q:1, mtot_msun:2.7, f_peak_khz:2.9, f_2_0_khz:null, f_spiral_khz:2.1, source_id:"s1", simulation_code:"SPH", spectral_type:"I", eos_variant:null, source:{title:"Alpha", authors:"A. Author", arxiv_id:"1"}},
  {id:"b", eos:"SLy", q:.8, mtot_msun:3.0, f_peak_khz:10.1, f_2_0_khz:2.2, f_spiral_khz:null, source_id:"s2", simulation_code:"BAM", spectral_type:"II", eos_variant:"cold", source:{title:"Beta", authors:"B. Author", arxiv_id:"2"}},
];
assert.equal(core.filterWaveforms(records, {search:"author", ranges:{}}).length, 2, "keyword search");
assert.equal(core.filterWaveforms(records, {eos:"DD2", ranges:{}}).length, 1, "categorical filter");
assert.equal(core.filterWaveforms(records, {ranges:{mtot_msun:{min:"2.8", max:""}}}).length, 1, "numeric filter");
assert.equal(core.filterWaveforms(records, {eos:"SLy", availability:"f_2_0_khz", massKind:"unequal", ranges:{f_peak_khz:{min:"10", max:"11"}}}).length, 1, "combined filters");
assert.equal(core.filterWaveforms(records, {availability:"f_2_0_khz", ranges:{}})[0].id, "b", "missing values");
assert(core.compareValues(2.9, 10.1) < 0, "numeric frequency sorting");
const exported = core.rowsToCSV([{id:"x", notes:'a, "quote"', f_peak_khz:null}], ["id","notes","f_peak_khz"]);
assert(exported.includes('"a, ""quote"""'), "filtered CSV quoting");

const synthetic = Array.from({length: 20000}, (_, i) => ({...records[i % 2], id:String(i), mtot_msun:2 + i / 10000}));
const start = performance.now();
const result = core.filterWaveforms(synthetic, {search:"alpha", ranges:{mtot_msun:{min:"2.5", max:"3.5"}}});
assert(result.length > 0 && performance.now() - start < 1500, "synthetic filtering performance");
console.log("database-explorer.js: all tests passed");
