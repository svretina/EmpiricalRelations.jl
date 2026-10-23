# Release checklist

This checklist defines the release gate for EmpiricalRelations.jl. A release tag must
not be created while an unchecked item remains in the **Required sign-off** section.

## Automated checks

- [ ] `python3 scripts/generate_julia_registry.py --check`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `node tests/database-explorer.test.js`
- [ ] `julia --project=. -e 'using Pkg; Pkg.test()'`
- [ ] `julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'`
- [ ] `julia --project=docs docs/make.jl`
- [ ] Install and load the package from a clean checkout on the minimum supported Julia
      version.
- [ ] Confirm that `git status --short` is empty and all GitHub Actions jobs pass.

## Required sign-off

- [ ] Review the canonical expression, coefficient mapping, units, applicability, and
      source location for every relation in `data/relations/relations.csv`.
- [ ] Record an independent numerical reference case for every implemented relation or
      document why an exact source-table comparison is the applicable verification.
- [ ] Review the three open items in `data/review_issues.csv`; retain them as documented
      source discrepancies unless new primary-source evidence resolves them.
- [ ] Confirm the software/data release boundary in `DATA_NOTICE.md` and the terms of
      the intended Zenodo deposit.
- [ ] Confirm creator names, ordering, affiliations, ORCIDs, funding, and acknowledgments
      for the release metadata.
- [ ] Replace `forthcoming` in `CHANGELOG.md` with the release date.
- [ ] Confirm that `Project.toml` and `CITATION.cff` contain the same version.

## GitHub, General registry, and Zenodo

- [ ] Enable this GitHub repository in Zenodo before publishing the GitHub release.
- [ ] If registering in Julia General, submit the release commit through Registrator and
      allow TagBot to create the version tag.
- [ ] Otherwise, create an annotated `v0.1.0` tag and GitHub release from the reviewed
      release commit.
- [ ] Inspect the Zenodo draft files, creators, description, related identifiers,
      license, and version before publishing the DOI.
- [ ] After publication, add the version DOI badge and citation to the README and docs.
