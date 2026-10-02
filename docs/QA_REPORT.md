# Prototype validation report

## Release checked

Planning Knowledge Hub v2.0.0. The release has zero published resources, four clearly labeled starter collections, and six separate fictional examples. Test contributions were created only in temporary test workspaces and are not included in the published catalog.

## Automated checks completed

- **10 Python unit tests passed:** data/schema constraints, non-AI contributions, URL restrictions, required and unknown fields, description length, collection references, sample exclusion, cross-listing, private/unknown property rejection, and safe embedded-data generation.
- **13 grouped Chromium browser checks passed:** empty default catalog and disconnected links; example separation; combined search/filter controls; non-AI draft creation; escaped text rendering; native JSON downloads; collection creation/editing/association; workspace export/import; malformed and unsafe imports; description validation; responsive layout/navigation/keyboard tabs; configured GitHub issue-link generation; unavailable-storage fallback; and absence of JavaScript errors or background network requests during primary rendering.
- **Responsive widths checked:** 320, 390, 768, 1,024, and 1,440 pixels. No horizontal page overflow was observed in the tested views. Desktop and mobile screenshots were visually inspected.
- **Importer integration checked in an isolated temporary copy:** dry-run preview, applying resource and collection packets, validation/build after import, duplicate-ID rejection, and explicit replacement. The release data remained unchanged.
- JavaScript syntax validation and the portable HTML build completed successfully.

## Test boundaries

The browser environment blocked direct file and local-server navigation. Browser checks therefore rendered the complete HTML in memory. Successful persistence/reload behavior was checked against a test-double implementing the localStorage interface, not native cross-session storage. The storage-denied fallback and native browser JSON downloads were exercised. Normal file-opening behavior and browser-specific persistence should also be checked on the deployment team's computers.

Tests used Chromium, not a cross-browser matrix. This is not a formal accessibility audit or security certification. No real GitHub issue was submitted, repository permission configured, or Pages deployment performed. The GitHub links and workflow files require real repository settings and a live acceptance test.

## Reproduce core checks

```sh
python scripts/validate.py
python -m unittest discover -s tests -p "test_*.py"
node --check src/app.js
python scripts/build.py
```

The optional browser test requires Playwright and a compatible Chromium browser:

```sh
python tests/browser_smoke.py --chromium /path/to/chromium --output /path/to/test-output
```

Keep browser-test output outside the repository. It includes fictional draft packets and screenshots, not production content. See the browser test's help output for the default-browser option.

## Before opening public contributions

Test opening the portable HTML in the team's browsers. Configure the real repository and deployment settings. Test one contribution from a non-maintainer account and one editor change through a branch/pull request. Verify that a successful merge rebuilds the public site, that drafts are never published automatically, and that issue templates, branch rules, and review assignments behave as intended. Confirm organization ownership, responsible maintainers, licensing, and privacy guidance before inviting other universities.
