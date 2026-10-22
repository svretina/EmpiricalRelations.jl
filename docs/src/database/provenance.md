# Provenance and citation

Every normalized waveform record has a stable ID and resolves through `source_id` to
`sources.csv`. Its provenance entry records the source-project path, line range, table
label, extraction method, and review status. The explorer exposes these fields without
including bulky manuscript text in its JSON payload.

When reusing a value:

1. cite the original publication shown in the record details;
2. cite this database release or repository revision;
3. retain the waveform ID and source ID in derived data;
4. inspect the original table and notes for source-specific qualifications.

Cross-paper configurations are not automatically deduplicated. A nominally identical
simulation cited by two sources remains two independently traceable records until a
reviewed identity policy exists.
