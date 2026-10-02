"""Optional Chromium UI smoke test using Playwright.

Usage: python tests/browser_smoke.py --chromium /path/to/chromium --output /tmp/hub-qa
Install Playwright and its Chromium browser, or supply an existing executable.
This test renders HTML in memory and uses a storage test-double for positive
persistence checks. It does not submit issues or test a live Pages deployment.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STORAGE_SHIM = """(initial) => {
  const data = Object.assign({}, initial || {});
  Object.defineProperty(window, 'localStorage', {configurable:true, value:{
    getItem:key => Object.hasOwn(data,key) ? data[key] : null,
    setItem:(key,value) => {data[key]=String(value)},
    removeItem:key => {delete data[key]},
    clear:() => {for(const key of Object.keys(data)) delete data[key]}
  }});
  window.__storageSnapshot = () => Object.assign({},data);
}"""


def run(chromium: str | None, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    fixture = json.loads((ROOT / 'data/examples.json').read_text(encoding='utf-8'))[0]
    checks, errors, requests = [], [], []
    def passed(name):
        checks.append(name)
        print('PASS', name)
    with sync_playwright() as p:
        kwargs = {'headless': True}
        if chromium:
            kwargs['executable_path'] = chromium
        browser = p.chromium.launch(**kwargs)
        context = browser.new_context(viewport={'width':1440,'height':1080}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(6000)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        page.evaluate(STORAGE_SHIM, {})
        page.set_content(html)
        page.screenshot(path=str(output / 'desktop-home.png'))
        assert page.locator('#publishedCount').inner_text() == '0'
        assert page.locator('#collectionGrid .collection-card').count() == 4
        assert page.locator('#planningTopic option').count() == 13
        assert page.locator('#repositoryLink').get_attribute('href') is None
        passed('Initial catalog empty; 12 tracks; 4 starter collections; disconnected links disabled')
        page.get_by_role('button', name='Example entries', exact=True).click()
        assert page.locator('#resourceList .resource-item').count() == 6
        assert page.locator('#exampleNotice').is_visible()
        assert page.locator('#resourceList a.resource-title').count() == 0
        page.select_option('#fieldFilter', 'environment')
        assert page.locator('#resourceList .resource-item').count() == 1
        page.click('#clearFilters')
        page.select_option('#planningTopic', 'track-1')
        assert page.locator('#resourceList .resource-item').count() == 1
        page.click('#clearFilters')
        page.select_option('#domain', 'Practice')
        page.select_option('#fieldFilter', 'design')
        assert page.locator('#resourceList .resource-item').count() == 1
        page.click('#clearFilters')
        page.fill('#search', 'syllabus housing')
        assert page.locator('#resourceList .resource-item').count() == 1
        page.click('#clearFilters')
        page.locator('#explore').screenshot(path=str(output / 'desktop-catalog.png'))
        passed('Example separation, field/topic/domain filtering, combined filters, and keyword search')
        page.click('#tab-resource')
        page.fill('#resourceTitle', 'Test non-AI resource <img src=x onerror=alert(1)>')
        page.fill('#resourceUrl', 'https://example.org/test-resource')
        page.select_option('#formDomain', 'Education')
        page.select_option('#formType', 'Course / Syllabus')
        page.check('#formFields input[value="planning"]')
        page.fill('#resourceDescription', fixture['description'])
        page.check('#resourceConsent')
        page.locator('#resourceForm button[type="submit"]').click()
        assert page.locator('#resourcePreview').is_visible()
        assert 'Saved in this browser only' in page.locator('#resourceStatus').inner_text()
        assert page.locator('#resourcePreviewCard img').count() == 0
        assert page.locator('#draftCount').inner_text() == '1'
        assert page.locator('#publishedCount').inner_text() == '0'
        assert page.locator('#resourceGitHub').get_attribute('href') is None
        assert page.locator('#resourcePreviewCard a.resource-title').get_attribute('rel') == 'noopener noreferrer'
        passed('Non-AI resource saved without topic or collection; safe rendering; no public mutation')
        with page.expect_download() as download_event:
            page.click('#downloadResource')
        downloaded = download_event.value
        downloaded.save_as(str(output / 'resource-packet.json'))
        packet = json.loads((output / 'resource-packet.json').read_text())
        assert packet['kind'] == 'resource'
        assert packet['record']['method'] == '' and packet['record']['topics'] == []
        resource_id = packet['record']['id']
        passed('Native browser JSON download produces a valid resource packet')
        page.click('#tab-collection')
        page.fill('#collectionTitle', 'Test Community Health Collection')
        page.select_option('#organizerType','Committee')
        page.fill('#organizer','Test group, not an actual committee')
        page.fill('#collectionDescription','This test collection brings together teaching materials and practical resources about community health and planning. It is only a test fixture for the contribution workflow and does not represent a real committee.')
        page.check('#collectionFields input[value="health"]')
        page.check('#collectionConsent')
        page.locator('#collectionForm button[type="submit"]').click()
        assert page.locator('#collectionPreview').is_visible()
        assert page.locator('#collectionGrid .collection-card').count() == 5
        with page.expect_download() as event:
            page.click('#downloadCollection')
        event.value.save_as(str(output / 'collection-packet.json'))
        cp = json.loads((output / 'collection-packet.json').read_text())
        collection_id = cp['record']['id']
        assert cp['record']['status'] == 'proposed'
        page.click('#tab-drafts')
        page.locator(f'[data-draft-action="edit"][data-kind="resource"][data-id="{resource_id}"]').click()
        page.check(f'#formCollections input[value="{collection_id}"]')
        page.check('#resourceConsent')
        page.locator('#resourceForm button[type="submit"]').click()
        page.click('[data-view="drafts"]')
        page.select_option('#collectionFilter', collection_id)
        assert page.locator('#resourceList .resource-item').count() == 1
        assert page.locator('#publishedCount').inner_text() == '0'
        passed('Collection draft creation, selection by resources, editing, and collection filtering')
        page.click('#tab-drafts')
        with page.expect_download() as event:
            page.click('#downloadAllDrafts')
        event.value.save_as(str(output / 'workspace.json'))
        workspace = json.loads((output / 'workspace.json').read_text())
        assert len(workspace['resources']) == 1 and len(workspace['collections']) == 1
        snap = page.evaluate('window.__storageSnapshot()')
        reloaded = context.new_page()
        reloaded.set_default_timeout(6000)
        reloaded.evaluate(STORAGE_SHIM, snap)
        reloaded.set_content(html)
        assert reloaded.locator('#draftCount').inner_text() == '1'
        assert reloaded.locator('#collectionGrid .collection-card').count() == 5
        passed('Workspace export and reload through the browser storage interface test-double')
        imported = context.new_page()
        imported.set_default_timeout(6000)
        imported.evaluate(STORAGE_SHIM,{})
        imported.set_content(html)
        imported.click('#tab-drafts')
        imported.locator('#importFile').set_input_files(str(output/'workspace.json'))
        imported.wait_for_function('document.getElementById("draftCount").textContent === "1"')
        assert 'Imported 2' in imported.locator('#workspaceStatus').inner_text()
        imported.locator('#importFile').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{not valid JSON'})
        imported.wait_for_function('document.getElementById("workspaceStatus").textContent.startsWith("Import stopped")')
        assert imported.locator('#draftCount').inner_text() == '1'
        passed('Workspace JSON import and malformed JSON rejection without data loss')
        bad = json.loads(json.dumps(packet)); bad['record']['url'] = 'javascript:alert(1)'
        imported.locator('#importFile').set_input_files({'name':'unsafe.json','mimeType':'application/json','buffer':json.dumps(bad).encode()})
        imported.wait_for_function('document.getElementById("workspaceStatus").textContent.includes("valid http")')
        assert imported.locator('#draftCount').inner_text() == '1'
        passed('Unsafe URL import rejected')
        imported.click('#tab-resource')
        imported.fill('#resourceTitle','Invalid short description')
        imported.fill('#resourceUrl','https://example.org/test')
        imported.select_option('#formDomain','Research')
        imported.select_option('#formType','Publication')
        imported.check('#formFields input[value="planning"]')
        imported.fill('#resourceDescription','Too short.')
        imported.check('#resourceConsent')
        imported.locator('#resourceForm button[type="submit"]').click()
        assert '50–100 words' in imported.locator('#resourceStatus').inner_text()
        assert imported.locator('#draftCount').inner_text() == '1'
        passed('Description length validation blocks incomplete contributions')
        mobile = context.new_page()
        mobile.set_viewport_size({'width':390,'height':844})
        mobile.set_default_timeout(6000)
        mobile.evaluate(STORAGE_SHIM,{})
        mobile.set_content(html)
        mobile.screenshot(path=str(output/'mobile-home.png'))
        for width in [320,390,768,1024,1440]:
            mobile.set_viewport_size({'width':width,'height':900})
            assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {width}'
        mobile.set_viewport_size({'width':390,'height':844})
        mobile.click('.nav-toggle')
        assert mobile.locator('.nav-toggle').get_attribute('aria-expanded') == 'true'
        mobile.keyboard.press('Escape')
        assert mobile.locator('.nav-toggle').get_attribute('aria-expanded') == 'false'
        mobile.click('#tab-resource')
        mobile.locator('#tab-resource').focus()
        mobile.keyboard.press('ArrowRight')
        assert mobile.locator('#tab-collection').get_attribute('aria-selected') == 'true'
        mobile.locator('#panel-collection').screenshot(path=str(output/'mobile-collection-form.png'))
        passed('320/390/768/1024/1440 px no horizontal overflow; mobile navigation; keyboard tabs')
        # Repository URL generation is tested without navigating or posting to GitHub.
        configured_html = html.replace('"githubRepository":""', '"githubRepository":"test-org/test-hub"', 1)
        configured = context.new_page()
        configured.set_default_timeout(6000)
        configured.evaluate(STORAGE_SHIM, {})
        configured.set_content(configured_html)
        assert configured.locator('#repositoryLink').get_attribute('href') == 'https://github.com/test-org/test-hub'
        configured.click('#tab-drafts')
        configured.locator('#importFile').set_input_files(str(output/'resource-packet.json'))
        configured.wait_for_function('document.getElementById("draftCount").textContent === "1"')
        configured.locator('[data-draft-action="edit"][data-kind="resource"]').click()
        configured.check('#resourceConsent')
        configured.locator('#resourceForm button[type="submit"]').click()
        assert configured.locator('#resourceGitHub').get_attribute('href').startswith('https://github.com/test-org/test-hub/issues/new?')
        passed('Configured repository and prefilled issue URLs generated without external submission')
        # Explicit storage-denied path.
        denied = context.new_page()
        denied.set_default_timeout(6000)
        denied.evaluate("Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage denied for test')},configurable:true})")
        denied.set_content(html)
        denied.click('#tab-drafts')
        denied.locator('#importFile').set_input_files(str(output/'resource-packet.json'))
        denied.wait_for_function('document.getElementById("draftCount").textContent === "1"')
        assert 'Storage is unavailable' in denied.locator('#workspaceStatus').inner_text()
        passed('Storage-denied fallback retains session drafts and warns to export')
        page.locator('#developers').screenshot(path=str(output/'desktop-developers.png'))
        assert not errors, errors
        assert not requests, requests
        passed('No JavaScript page errors or background network requests during primary rendering')
        report = {'checks_passed':len(checks),'checks':checks,'page_errors':errors,'primary_page_requests':requests,
                  'limitations':['HTML rendered in memory because this environment blocks file and localhost navigation.',
                                 'Positive persistence tested with a localStorage interface test-double, not native cross-session storage.',
                                 'Native browser JSON downloads tested; no live GitHub issue or Pages deployment performed.',
                                 'Chromium only; this is not a formal accessibility certification or cross-browser audit.']}
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        browser.close()
        return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium')
    parser.add_argument('--output',type=Path,default=Path('/tmp/planning-hub-qa'))
    args=parser.parse_args()
    run(args.chromium,args.output)
