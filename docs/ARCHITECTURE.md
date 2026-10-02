# Architecture and data model

## Static output, structured input

The deployed site is one generated HTML file. `src/index.template.html`, `src/styles.css`, `src/app.js`, and JSON data are combined by `scripts/build.py`. The app performs no fetch or background submission. Rendering, filters, local forms, examples, and exports work without external assets. GitHub and original-source links are the only explicit external destinations.

`data/config.json` contains the working title and the shared repository path. Leave `githubRepository` empty until a real project is available; links intentionally remain disabled. `githubBranch` records the intended default branch for documentation. It does not rewrite workflow branch filters automatically. The supplied workflow files assume `main`.

## Resource record

Required fields are `id`, `title`, `description`, `url`, `domain`, `resourceType`, and a nonempty `fields` array. The description contains 50–100 whitespace-delimited words. Optional fields are `topics`, `collectionIds`, `method`, `keywords`, `institution`, `contributor`, `date`, `geography`, `license`, and `audience`.

Fields and planning topics use stable taxonomy IDs. The twelve original planning topics are preserved under `track-1` through `track-12`. Topic selection is optional so allied-field content is not forced into a mismatched track. New disciplines can be added in `data/taxonomy.json`; keywords support free-text specificity in the meantime. AI methods have no special required status.

One resource may reference several collections, but it is stored once. The default import path is `data/resources/<first-collection-id>/<resource-id>.json`, or `data/resources/general/` without a collection. Other valid subfolder organizations are accepted by the recursive build. A folder is not an access-control boundary.

## Collection record

A collection has an `id`, `title`, `description`, nonempty `fields`, `organizerType`, optional `organizer`, optional `institution`, optional `topics`, and a `status` of `starter`, `proposed`, or `active`. These describe display status, not authentication or official approval. Browser-created collections are always proposed local drafts. Administrators must verify group identity before marking a collection active in shared data.

## Contribution packet

Forms export this wrapper, not a shared-data record directly:

```json
{
  "schemaVersion": 1,
  "kind": "resource",
  "action": "add",
  "record": {"id": "res-example", "title": "A record with the remaining required metadata"}
}
```

This abbreviated illustration is not a valid record to publish. `kind` is resource or collection; `action` is add or update. Workspace exports contain arrays of such packets under `resources` and `collections`. The importer validates the record, strips the wrapper by writing only `record`, and requires explicit replacement permission for existing IDs.

## Three data scopes

**Published** contains records embedded at build time from `data/resources/`. It is read-only in the browser. **Examples** contains six fictional display-only records with no external resource URLs. **My drafts** contains only records held in the current browser or in memory when storage is unavailable. Draft counts never enter published counts.

A saved draft is not an authenticated identity, shared database row, publication, or approval. Draft storage is namespaced by the configured repository and prototype version. Connecting the prototype to a repository changes that namespace; export local drafts before changing configurations. Device/browser changes and cleared storage also require reimport.

## Security and privacy boundaries

Dynamic text is escaped before HTML rendering. URLs must use http or https, with no embedded username/password. Build-time JSON escapes HTML-sensitive characters before being embedded in the document. IDs are limited to lowercase letters, digits, and hyphens. Import helpers restrict paths, sizes, known categories, and expected data fields. Examples cannot pass published-resource validation.

These checks do not assess copyright, factual quality, malicious destination pages, group authority, or appropriateness. Maintainers still need to inspect source links and public metadata. Browser storage is not encrypted and is not a suitable place for confidential information. Public GitHub issue content is public. Never place API keys, private contact details, restricted datasets, or original third-party files in the catalog.

GitHub workflows use `pull_request`, not `pull_request_target`, for untrusted changes. Validation jobs request read access only. Pages deployment requests the platform permissions required for publication and is limited to the `main` workflow's build/deploy path. Administrators should configure environment restrictions and branch rules before enabling the public workflow.

## Editor schemas

The JSON schema files assist editors. The build validator is authoritative: it also enforces word counts, live taxonomy membership, collection references, unique IDs, filenames, and example separation. When changing taxonomy options, update schema enums as appropriate so editor suggestions remain aligned. Do not add a `$schema` property inside data records; configure your editor to associate `schemas/resource.schema.json` and `schemas/collection.schema.json` with their corresponding data folders.
