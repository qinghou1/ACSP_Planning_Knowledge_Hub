# Planning Knowledge Hub
https://qinghou1.github.io/ACSP_Planning_Knowledge_Hub/

A broader successor to `AI-in-Planning-Repository-Self-Contained.html`.

**Working title:** Planning Knowledge Hub  
**Scope:** Planning and allied fields, across Education, Research, and Practice.  
**Status:** A working static prototype and a development handoff package, not a deployed multi-user service.

## Start here

Open `Planning-Knowledge-Hub-Self-Contained.html` or `index.html` in a modern browser. Both files contain the complete interface, CSS, JavaScript, taxonomy, starter collections, and example data. No installation, CDN, external font, build service, or network connection is needed to render the interface. External resources and GitHub links require connectivity. Local storage may be unavailable in restricted browsers or for local files; export drafts to retain them.

The original resource array was empty, and the published catalog remains empty. Select **Example entries** to test six explicitly fictional records. These examples are not published resources, endorsements, or real committee contributions.

## What changed

| Feedback | Implemented response |
| --- | --- |
| The site should not be limited to Urban Planning AI. | Broader name, scope, domain descriptions, field filters, resource types, and optional methods. The twelve original planning tracks remain unchanged. AI is one track and one starter collection. |
| Other fields or committees should add content themselves. | Separate resource and collection forms; multi-field classification; cross-listed collections; local preview, editing, JSON import/export, and configurable GitHub issue handoff. Content can be maintained as data rather than by editing HTML. |
| Student developers from other universities should co-design and maintain the site. | Separate source/data files, documented build process, contribution instructions, issue and pull-request templates, validation tests, deployment workflow, and a CODEOWNERS example. |

## What works immediately

Search and combine filters; switch between published/example/local views; create and edit local resource and collection drafts; export and import structured JSON; preview external resource links; use responsive navigation; read the embedded developer guide. A resource does not require an AI method, a planning track, an institution, or a committee membership.

**Saving a draft does not submit or publish it.** This package contains no authentication, shared database, email sender, or deployed submission service. A GitHub issue is a proposal, not an automatic publication.

## Connect shared contribution and publishing

1. Create or choose a shared organization-owned GitHub repository. Decide its public name, ownership, maintainers, license, and contribution policy. Copy the contents of this ZIP into the repository root, including `.github/`.
2. Set `githubRepository` in `data/config.json` to the real `owner/repository`. The default is deliberately empty. The supplied workflows assume the branch is named `main`; update both workflow branch filters if the project uses another branch.
3. Enable Issues. Configure **Settings → Pages → Build and deployment → Source: GitHub Actions**. Enable Actions as permitted by your organization. Do not use branch-based Pages deployment for the collaborative data workflow.
4. Assign at least two maintainers. Grant committee editors and student developers appropriate repository access. Configure branch rules, required checks, and review responsibilities. `CODEOWNERS.example` is a template only and grants no access.
5. Run the build locally or push the source to `main` after configuration. The deployment workflow validates and rebuilds from `src/` and `data/`, then publishes only `_site/`. Test a real submission with an authorized account before announcing public contribution.

GitHub actions and issue links are prepared, but no repository has been created or connected by this package. Current platform instructions and source links are in `docs/TECHNICAL_REFERENCES.md`.

## Local development

Python 3.10 or newer is sufficient for validation, import, and build; those scripts use only the standard library. Node is needed only for the optional JavaScript syntax check. Browser testing has optional Playwright dependencies.

```sh
python scripts/validate.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/build.py
python -m http.server 8000
```

Browse the local server on port 8000. On Windows, use `py` in place of `python` when that is your configured Python launcher.

Edit **`src/` and `data/`**, not the generated HTML. The build writes root-level portable snapshots and `_site/` deployment files. GitHub deployment always regenerates from source, so committee contributors can edit JSON in GitHub without manually rebuilding HTML. Root-level snapshots in a repository are only as current as the last committed build; the deployed site always reflects the source of its deployment commit. Before distributing a new ZIP, rebuild its snapshots.

## Import a contribution packet

Work on a branch. Inspect the source, metadata, attribution, and group association first.

```sh
python scripts/import_packet.py path/to/contribution.json
python scripts/import_packet.py path/to/contribution.json --apply
python scripts/validate.py
python scripts/build.py
```

The first command is a dry run. Replacing an existing ID also requires `--replace`. An update packet must refer to an existing shared record. Nothing is published by the import script; publication follows a merge and successful Pages deployment. No editorial review panel is assumed or represented as operational.

## Repository layout

```text
index.html                                  Generated portable snapshot
Planning-Knowledge-Hub-Self-Contained.html    Identical, descriptive filename
src/index.template.html                     Page layout and public copy
src/styles.css                              Shared visual design
src/app.js                                  Search, forms, and local workspace
data/config.json                            Site name and repository setting
data/taxonomy.json                           Domains, fields, tracks, and types
data/collections/*.json                      One file per collection
data/resources/<collection-id>/*.json        One file per resource
data/examples.json                          Fictional examples, never published
scripts/                                    Validate, build, and import
schemas/                                    Editor-assistance JSON schemas
tests/                                      Data, build, and optional browser tests
docs/                                       Setup, contribution, maintenance, and QA
.github/                                    GitHub templates and workflows
```

A resource is stored once and may reference multiple `collectionIds`. Its first collection supplies the default source-data folder for imports; that folder is organizational, not an access-control mechanism.

## Important limits

A public repository is not automatically an approved open-source project. No license has been selected on the owner's behalf. See `docs/LICENSING.md`. Starter collections do not establish official committee membership or assigned stewardship. Private contact details, access tokens, restricted datasets, and third-party full text do not belong in this public static catalog or its local workspace.

Test results and their boundaries are documented in `docs/QA_REPORT.md`.
