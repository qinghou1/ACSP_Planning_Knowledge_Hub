# Planning Knowledge Hub — GitHub Pages package

This package is ready for static hosting on GitHub Pages. No build, npm installation, API key, or server is required. `index.html` is an exact copy of `20261101Planning-Knowledge-Hub-Updated.html`; both contain the same complete website, catalog, styles, scripts, and cover images.

The prepared AI collection contains **60 resources: 20 Teaching, 20 Research, and 20 Applications**, with 20 different ACSP Full Member universities in each category. Research papers were first published in 2021–2026, with MDPI excluded. All research covers are attributed paper figures. The source audits and image credits are included.

## Publish on GitHub Pages

1. Extract this ZIP on your computer.
2. Add the extracted **contents** to the root of your GitHub repository. `index.html` must be directly at the repository root, rather than inside another folder. Upload the extracted files, rather than the ZIP itself.
3. Keep the empty `.nojekyll` file at the root. If your file browser hides dotfiles, enable hidden files or create an empty `.nojekyll` file in GitHub.
4. Commit the files to `main` (or the branch you choose for publishing).
5. In the repository, open **Settings → Pages → Build and deployment**. Set **Source: Deploy from a branch**, choose **main** and **/(root)**, then **Save**.
6. Once GitHub finishes deployment, use **Visit site** on the Pages settings screen.

GitHub's instructions: [configure a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [create a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

The navigation uses `#/` fragment routes and works under a GitHub project repository subpath. No repository name, username, base-path configuration, custom domain, or `404.html` fallback is needed. A domain can be configured later if requested.

## Included entry points

| File | Opens |
| --- | --- |
| `index.html` | Full Planning Knowledge Hub; the GitHub Pages homepage |
| `20261101Planning-Knowledge-Hub-Updated.html` | The identical full hub, also usable offline |
| `Planning-Knowledge-Hub-Resource-Collection.html` | The same hub with the AI collection selected initially |

The three HTML files contain the same prepared resource data and images. The collection file differs only in its initial route. The package preserves the separately delivered standalone HTML files without changing their content.

## Update the website from Excel

1. Edit the Teaching, Research, and Applications tabs in `ACSP-Resource-Collection.xlsx`. Preserve stable resource IDs and keep one primary member school per category. For added rows, extend the category table and Website Import formulas.
2. Recalculate and save the workbook in Excel so the Website Import formulas have current cached values.
3. Keep the assets, manifests, and member-school reference beside the workbook. Run locally with Python 3:

   ```sh
   python export_website_catalog.py ACSP-Resource-Collection.xlsx
   python update_html_from_catalog.py
   python verify_package.py
   ```

4. Commit the changed workbook, catalogs, images/manifests when applicable, and **all three HTML files**, including `index.html`. GitHub Pages then publishes the committed snapshot.

The default rebuild refreshes both named standalone files and `index.html` together after validating all resources. The optional `--html` argument is an advanced override that updates only the explicitly named files; use the default command for routine updates.

`verify_package.py` checks the workbook and CSV against the enhanced JSON, checks all HTML catalog fields and embedded images against the JSON/assets, verifies member-school uniqueness and research metadata rules, and requires `index.html` to be byte-identical to the full-hub file. It uses only the Python standard library. `Package-Validation.json` records the checks run for this delivered snapshot; rerun the verifier after making changes.

## Contribution and review demonstration

Image upload, preview, positioning, zoom, rotation, cropping, drafts, and review roles work in the browser. These interactions use browser-local storage. They do **not** write back to GitHub, Excel, or a shared database. To distribute changes, update the prepared catalog, rebuild the HTML files, and commit them. A rebuild starts a fresh browser workspace for the new snapshot; export local drafts or review history first.

GitHub Pages hosts the prepared prototype. Shared accounts, durable uploads, and centralized multi-user review still require a backend. Nothing in this ZIP configures or deploys changes to studyurbanplanning.com.

For the detailed metadata, image, provenance, and editorial rules, see [README.txt](README.txt), [Research-Journal-Audit.csv](Research-Journal-Audit.csv), [Teaching-Provenance-Audit.json](Teaching-Provenance-Audit.json), and [Image-Credits.csv](Image-Credits.csv).
