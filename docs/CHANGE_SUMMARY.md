# Feedback response and demonstration guide

## 1. Broader scope and independent content contributions

The working title is now **Planning Knowledge Hub**, with the description **A shared resource hub for planning and allied fields**. This broadens the original AI-focused framing without losing the planning purpose. AI in Planning remains Track 1 and a starter collection, not a prerequisite for inclusion.

The Education, Research, and Practice domains and all twelve original planning-track labels are retained. The search interface adds Field / discipline and Collection / group. AI-specific filtering becomes an optional Method / tool field with non-AI choices. New resource types include policy/guidance, reports, teaching materials, projects, and events/recordings.

Resource and collection forms are separate. Contributors can choose multiple fields and planning tracks, cross-list resources, omit an AI method entirely, and describe additional topics through keywords. They can preview, save, edit, export, and import local drafts without changing website code. Proposed collections become available to local resource drafts immediately, while remaining explicitly unpublished.

Starter collections are demonstration structures, not claims about active ACSP committees. The initial published catalog is still empty, preserving the source HTML's empty resource array. Six fictional records appear only in Example entries.

## 2. Shared development and maintenance

A Developers section explains co-design, data contribution, testing, and handover. The development package separates HTML, CSS, JavaScript, resource files, collection files, and taxonomy configuration. The build generates a portable single-file site, retaining the convenience of the original self-contained HTML.

The package includes contribution instructions, issue templates, a pull-request template, validation tests, a data-import helper, GitHub checks and Pages deployment workflows, and a CODEOWNERS example. The intended shared repository can be maintained across universities rather than by a single student or one personal account.

## Demonstration sequence

1. Open the self-contained HTML and show the new scope and three-domain structure.
2. In Explore, choose Example entries. Filter Environment & Sustainability or Design & Built Environment to show that AI is not required. Clear filters and choose Track 1 to show that AI has not been removed.
3. Open Collections to show the shared structure and the distinction between group collections and subject tracks.
4. Prepare a non-AI resource with no planning track. Save it locally. Show its preview and JSON export, then the separate My drafts view.
5. Propose a collection and show that a local resource can be associated with it. Show the Developers section and source package to discuss cross-university collaboration.

## Decisions still needed before public contribution

Confirm the public title and organizational ownership; create or select the shared repository; appoint maintainers and content editors; choose a code license and content policy; configure permissions, Issues, Actions, and Pages; test a real submission and publication. Nothing in this package asserts that those steps are already complete.

A suitable explanation for the supervisor:

> I broadened the prototype into a Planning Knowledge Hub, with AI as one topic rather than the site's overall boundary. Committees and other groups can prepare their own resource entries and collections without editing the website code. I also separated the source files and documented a shared GitHub workflow so student developers from different universities can co-design and maintain the site. The local tools are working; shared submission and publishing still require a connected repository and assigned maintainers.
