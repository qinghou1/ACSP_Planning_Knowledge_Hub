# Proposed ownership and maintenance model

This is a setup proposal, not a list of appointed people or active committees.

## Responsibilities

| Role | Responsibility | Access to configure separately |
| --- | --- | --- |
| Platform owner | Confirm public name, scope, institutional ownership, license, and privacy/content rules. | GitHub organization/repository administration. |
| Content / collection editor | Maintain descriptions and resource metadata for a group; check links and attribution. | Appropriate repository access, usually branch-based contributions. |
| Student developer | Improve interface, accessibility, code, tests, and documentation. | Fork/pull-request contribution or assigned repository access. |
| Repository maintainer | Resolve issues, inspect changes, merge data/code updates, and oversee deployment. | Merge and release responsibilities under project rules. |

There is no assumed staffed editorial review board. The minimum publication action is a designated repository maintainer incorporating a change into shared source. More formal content curation may be added later, but the prototype does not claim it is operational.

## Continuity

Use shared organizational ownership rather than one student's personal repository for the long-term authoritative site. Keep at least two maintainers. Record public responsibilities, default branch, Pages settings, current configuration, known issues, and handover steps. Confirm access before a student's appointment ends.

For a student handover, have the incoming maintainer build the site, make a small test change on a branch, inspect checks, and identify the previous deployable commit. Remove unnecessary access through the platform administrator. Never document private tokens or passwords in this repository.

## Permission boundaries

CODEOWNERS can route change reviews to relevant groups after administrators configure actual users/teams and branch requirements. It does not grant write access, enforce independent per-committee content management, or make a local form into an authenticated editor. Users with general write access are not inherently limited to one data subfolder.

For stronger isolation or a non-GitHub browser editor, evaluate a separate authenticated content-management service. No such service is provisioned here. Until then, use contribution packets or GitHub branches and explicit maintainer publication.

## Content practice

Keep original-source links, public attribution, and known reuse conditions. Avoid claiming endorsement solely because a resource is linked. Confirm the authority of a committee name before assigning it as an organizer. Handle removals and broken links as normal repository changes with a recorded reason, rather than erasing source history silently.

Platform references are in `TECHNICAL_REFERENCES.md`.
