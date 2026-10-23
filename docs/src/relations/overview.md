# Empirical relations

Each relation record specifies the dependent quantity, independent variables,
calibration population, applicability domain, reported residuals, and publication.
Coefficients are stored in a separate table keyed by `relation_id`.

Reviewed relations with status `implemented` can be evaluated through the Julia API.
The catalogue renders each relation's specialized mathematical expression and provides
copyable Julia and Python implementations together with its BibTeX citation.

The [relations catalogue](catalogue.md) provides search and filters for the recorded
fits.
