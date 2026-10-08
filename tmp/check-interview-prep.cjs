const {chromium} = require('C:/Users/cyh/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'C:/Users/cyh/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe'});
  const sourceTitle = `浏览器验证来源 ${Date.now()}`;
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1100}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:8765/?view=interview_prep');
    assert.equal(await page.locator('#view-interview-prep').evaluate(element => element.classList.contains('active-view')), true);
    await page.getByRole('button', {name:'面试准备',exact:true}).click();
    await page.getByRole('button', {name:'查看三一锂能 · BMS 嵌入式准备',exact:true}).click();
    const frame = page.frameLocator('#interviewPrepFrame');
    await frame.getByRole('heading', {name:'三一锂能 · BMS 嵌入式',exact:true}).waitFor();
    await frame.getByRole('heading', {name:'JD 原文与准备重点',exact:true}).waitFor();
    assert.equal(await page.locator('#viewTitle').textContent(), '面试准备');
    await page.screenshot({path:'C:/CareerOS/tmp/interview-prep-desktop.png',fullPage:true});

    // Exercise mutations on an isolated data directory, never the user's notes.
    await page.goto('http://127.0.0.1:18765/static/interview-prep/index.html?workspace=sany-bms-202610');
    await page.getByRole('heading', {name:'JD 原文与准备重点',exact:true}).waitFor();
    await page.getByRole('button', {name:'公司与核心产品',exact:true}).click();
    await page.locator('#content table').waitFor();
    assert.ok(await page.locator('#content').textContent().then(text => text.includes('ESG261')));
    await page.getByRole('button', {name:'进度与笔记',exact:true}).click();
    await page.locator('#tasks input[value="can"]').check();
    await page.locator('#notesText').fill('浏览器验证：数据新鲜度与异常恢复');
    await page.locator('#interview_date').fill('2026-10-06');
    await page.getByRole('button', {name:'资料来源',exact:true}).click();
    await page.locator('#sourceTitle').fill(sourceTitle);
    await page.locator('#sourceUrl').fill('https://www.ti.com/product/BQ76952');
    await page.locator('#sourceNote').fill('<script>alert(1)</script> 原始文字');
    await page.getByRole('button', {name:'添加到收集区',exact:true}).click();
    assert.equal(await page.locator('#sourceList script').count(), 0);
    await page.getByRole('button', {name:'保存进度与笔记',exact:true}).click();
    await page.getByText('已保存到本机', {exact:true}).waitFor();
    await page.reload();
    await page.getByRole('heading', {name:'JD 原文与准备重点',exact:true}).waitFor();
    await page.getByRole('button', {name:'进度与笔记',exact:true}).click();
    assert.equal(await page.locator('#notesText').inputValue(), '浏览器验证：数据新鲜度与异常恢复');
    assert.equal(await page.locator('#tasks input[value="can"]').isChecked(), true);
    assert.equal(await page.locator('#interview_date').inputValue(), '2026-10-06');
    await page.getByRole('button', {name:'资料来源',exact:true}).click();
    assert.equal(await page.getByRole('link', {name:`${sourceTitle} ↗`,exact:true}).count(), 1);
    await page.getByRole('button', {name:'资料阅读',exact:true}).click();
    await page.getByRole('button', {name:'准备总览',exact:true}).click();
    await page.getByRole('link', {name:'00 JD 原文与准备重点',exact:true}).click();
    await page.getByRole('heading', {name:'JD 原文与准备重点',exact:true}).waitFor();
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', {name:'下载 Markdown',exact:true}).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), '00-jd-analysis.md');
    const backupPromise = page.waitForEvent('download');
    await page.getByRole('button', {name:'导出备份',exact:true}).click();
    assert.equal((await backupPromise).suggestedFilename(), 'sany-bms-202610-notes.json');
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'C:/CareerOS/tmp/interview-prep-mobile.png',fullPage:false});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    assert.deepEqual(errors, []);
    console.log('PASS: navigation, document reading, persisted notes/tasks/date/sources, escaping, Markdown links, downloads, mobile width, console.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
