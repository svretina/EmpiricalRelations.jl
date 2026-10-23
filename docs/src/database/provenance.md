# Provenance and citation

Every normalized waveform record has a stable ID. Its `source_id` identifies a row in
`sources.csv`, and its provenance record gives the source path, line range, table label,
extraction method, and review status. Original LaTeX is stored in `provenance.csv` but
omitted from the smaller JSON file used by the explorer.

When reusing a value:

1. cite the original publication shown in the record details;
2. cite this database release or repository revision;
3. retain the waveform ID and source ID in derived data;
4. inspect the original table and notes for source-specific qualifications.

Configurations are not deduplicated across publications. If two papers report the same
simulation, each reported instance retains its own source ID and provenance.
