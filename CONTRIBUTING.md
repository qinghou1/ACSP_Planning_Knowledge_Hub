# Contributing

Contributions from students, faculty, committees, practitioners, and developers at different universities are welcome under the policy adopted by the repository owner. These instructions are a proposed operational model, not evidence that access has already been granted.

## Content contributors: no website code required

Use the Resource form to create an entry and the Collection form to propose a group collection. AI is optional. A planning track is optional. Select at least one field, including Other / Interdisciplinary when needed, and use keywords for a more specific subject.

A resource description must contain 50–100 words; a collection description must contain 20–100 words. Links must use http or https without embedded credentials. Only provide public metadata. The form does not upload the original work or grant its reuse rights.

Click Preview & save locally, inspect the entry, and download its JSON packet. Once configured, Continue on GitHub opens a prefilled issue. You must sign in and submit the issue there. For long entries, copy the submission text and paste it into the issue. Until a real repository is connected, download the packet and share it with the designated project contact outside this site; this package invents no contact address.

## Committee / collection editors

An administrator can assign editors to maintain source data. Editors can use GitHub's browser interface to create a branch and modify JSON without touching HTML or JavaScript. Add a resource file under `data/resources/<collection-id>/` with a filename matching its ID. Edit collection descriptions in `data/collections/`. Store each resource once; list additional collections in `collectionIds` rather than copying it.

For form-generated packets, use `scripts/import_packet.py` on a branch or ask a maintainer to do so. First run it without `--apply`, inspect the proposed changes, then apply. An authorized maintainer merges the data change; the Pages workflow rebuilds the site. The issue itself never publishes data.

A collection is not a permission boundary. Repository access and protection rules must be set in GitHub. CODEOWNERS routes reviews; it does not create accounts or isolate one committee's files from all other write-access users.

## Student developers and co-designers

Read the README and `docs/ARCHITECTURE.md`. Use an issue to describe a substantial design change before implementing it. Fork the shared repository, create a small branch, make the change, and open a pull request against the shared project's `main` branch. Contributors with access may use a branch within the shared repository instead.

Keep data changes separate from layout changes where practical. Preserve the three domains, the original twelve track labels, external-title-link behavior, and the separation between published data and local drafts. Additional fields and categories should be added through the taxonomy file, with corresponding validation/schema updates when needed.

Run:

```sh
python scripts/validate.py
python -m unittest discover -s tests -p "test_*.py"
node --check src/app.js
python scripts/build.py
```

Include desktop and mobile checks with interface changes. Do not commit browser workspace exports, credentials, downloaded third-party content, virtual environments, or build caches.

## Maintenance and handover

Record responsibilities, open problems, setup decisions, and deployment ownership in repository documentation. Keep two maintainers from different continuity points where possible, rather than depending on a graduating student's personal account. Review privileges during handover and ensure an incoming maintainer can validate, build, and recover a previous version.

No repository or remote settings are changed by these instructions. Platform references: `docs/TECHNICAL_REFERENCES.md`.
