PLANNING KNOWLEDGE HUB — VERIFIED TEACHING AND JOURNAL RESEARCH
Updated November 1, 2026

OPEN THE WEBSITE
For GitHub Pages, see README.md. The root index.html is byte-identical to the full hub. Keep .nojekyll at the publishing root.
20261101Planning-Knowledge-Hub-Updated.html opens the full hub homepage.
Planning-Knowledge-Hub-Resource-Collection.html opens the AI in Planning collection.
Both HTML files contain all images, styles, and scripts. Download and open either file in a browser. Internet access is needed to follow original source links.

COLLECTION AND SELECTION RULES
There are 60 resources: 20 Teaching, 20 Research, and 20 Applications.
Each category represents 20 different ACSP Full Member universities, with one entry per school within that category. A school may appear in another category. There are 29 distinct universities across the collection.
Membership was checked against the official ACSP list updated August 27, 2026: https://www.acsp.org/page/Members . ACSP-Membership-Audit.csv records the represented school and affiliation evidence for every entry. Coauthored papers appear once under a documented university affiliation; full collaborations remain in the source notes.

TEACHING VERIFICATION
MSU independently confirms the Urban AI program on https://ai.msu.edu/ai-ready . Its announcement names Si Chen and confirms the non-credit award category and planning/urban-development purpose. It does not link to the former GitHub URL or confirm hours and cohort details. The entry now uses the official MSU program announcement and omits unverified delivery and co-instructor claims. Its type is Other because the source is an announcement rather than a verified syllabus.
USC PPDE 642 and UW GEOG 495/428 now link to official university landing pages. Corroborated faculty-maintained materials remain supporting sources. UT Austin's Simple Syllabus account is university-authorized. Teaching-Provenance-Audit.json records verification and limitations for all 20 Teaching entries. A program announcement does not establish current enrollment availability.

RESEARCH VERIFICATION
All 20 Research entries are peer-reviewed journal papers first published in 2021–2026. MDPI journals, preprint-only records, conference-only records, and pre-2021 papers are excluded. Journal names are visible on the cards.
Research-Journal-Audit.csv and .json record each journal, publisher, DOI, publication year/date, article type, affiliation evidence, and selection rationale. Selection prioritizes peer review, subject relevance, documented methods, and scholarly journal standing. No automatic impact-factor or quartile ranking is asserted.
A few covers use publicly available author manuscripts of already-published journal papers. These figure versions are labeled, while the primary resource links to the published journal DOI. They are not unpublished research entries.
Removed-Research-Entries.csv records the 10 previous entries replaced in this update. Earlier curation logs are under history/.

IMAGES
University names appear at the top right of covers. All 20 Research covers use authentic paper figures, fitted whole on white with space above for the badge. Click a Research cover to open its source. Teaching and Applications use credited context photographs; campus images may be reused across categories.
All 49 distinct active cover assets are 800 x 450 JPEGs below 80,000 bytes each. Image-Credits.csv and Image-Manifest.json record attribution, source, figure version, and reuse terms. Rights vary; review individual terms before public integration.
The Contribute form retains image upload, preview, drag or slider positioning, zoom, rotation, crop application, removal, and credit fields. Choose Use crop before saving. Images and adjustments persist through local drafts, review, publication, and backups.

UPDATE THROUGH EXCEL
1. Edit the Teaching, Research, or Applications tabs of ACSP-Resource-Collection.xlsx. Keep stable Resource IDs and one primary member university per category. The Website Import tab contains 60 formula-linked rows.
2. Recalculate and save in Excel or compatible software. For added rows, extend the category table and Website Import formulas. Keep IDs and source URLs unique.
3. Keep photos/, figures/, Image-Manifest.json, ACSP-Member-School-Reference.json, and the scripts beside the workbook. Run with Python 3, using its standard library only:
   python export_website_catalog.py ACSP-Resource-Collection.xlsx
   This generates the CSV, enhanced JSON with images, and text-only legacy JSON.
4. In either revised HTML file, choose the Publisher demo role, then Import reviewed catalog. Validate the exported CSV or enhanced JSON. Matching IDs update; omitted rows remain. Restore prepared catalog returns to the supplied snapshot.
5. To rebuild both self-contained HTML files and the GitHub Pages index.html from the exported snapshot, run:
   python update_html_from_catalog.py
   python verify_package.py
   Validation finishes before any HTML file changes. The default rebuild keeps index.html identical to the full-hub HTML. Commit the regenerated files to publish changes through GitHub Pages. Rebuilt files use a separate browser workspace for that snapshot. Export drafts/history before switching, and refresh the member reference when ACSP changes its list.

RESEARCH FIELDS FOR FUTURE UPDATES
Resource Type: Publication.
Date: first journal-publication year/date, from 2021 onward.
Source Status: Peer-reviewed journal article · Journal name
Source Link: the published journal article or DOI, rather than an arXiv-only record.
Supporting Sources and Verification Notes: evidence of journal publication, school affiliation, and relevant limitations.
The website, exporter, and rebuild script check these metadata rules and the MDPI exclusion. Journal standing and article quality still require editorial review; a text label is not independent verification.
The legacy JSON targets the older October 22 prototype, which lacks covers and the new publication checks. Use the supplied revised HTML files for the current collection.

LOCAL WORKFLOW
The AI collection rejects a second published resource from the same school in the same category. Drafts can be prepared before eligibility is confirmed. Suggest a correction when a school/category entry already exists. Other collections retain their existing workflow.
This is a browser-local prototype with demo roles rather than sign-in. Nothing has been deployed to studyurbanplanning.com. Hosting integration, authentication, durable uploads, and production review permissions remain developer tasks. No official ACSP endorsement or editorial approval is asserted.
