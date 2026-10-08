const {chromium} = require('C:/Users/cyh/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'C:/Users/cyh/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1050}});
    const errors=[];
    page.on('pageerror', error=>errors.push(error.message));
    await page.route('**/api/sync/status', route=>route.fulfill({json:{configured:true,encryption_available:true,pending_remote:true,rollback_available:true}}));
    await page.route('**/api/sync/accept', route=>route.fulfill({json:{}}));
    await page.route('**/api/sync/rollback', route=>route.fulfill({json:{}}));
    await page.goto('http://127.0.0.1:18765/?view=interview_prep');
    await page.getByRole('button',{name:'查看三一锂能 · BMS 嵌入式准备',exact:true}).click();
    let frame=page.frameLocator('#interviewPrepFrame');
    await frame.getByRole('heading',{name:'JD 原文与准备重点',exact:true}).waitFor();
    await page.getByRole('button',{name:'设置和帮助',exact:true}).click();
    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:'接受远程更新',exact:true}).click();
    await page.getByText('远程数据已接受，本机已更新。',{exact:true}).waitFor();
    await page.getByRole('button',{name:'面试准备',exact:true}).click();
    assert.equal(await page.locator('#prepDetailView').isVisible(),false);
    assert.equal(await page.locator('#prepLibraryView').isVisible(),true);
    await page.getByRole('button',{name:'查看三一锂能 · BMS 嵌入式准备',exact:true}).click();
    frame=page.frameLocator('#interviewPrepFrame');
    await frame.getByRole('button',{name:'进度与笔记',exact:true}).click();
    await frame.locator('#notesText').fill('同步期间尚未保存的草稿');
    await page.getByRole('button',{name:'设置和帮助',exact:true}).click();
    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:'回滚上次接受',exact:true}).click();
    await page.getByText('已回滚到接受更新前的本机版本。',{exact:true}).waitFor();
    await page.getByRole('button',{name:'面试准备',exact:true}).click();
    assert.equal(await frame.locator('#notesText').inputValue(),'同步期间尚未保存的草稿');
    assert.equal(await frame.locator('#save').isDisabled(),true);
    assert.equal(await frame.locator('#export').isEnabled(),true);
    assert.ok((await frame.locator('#notice').textContent()).includes('请先导出'));
    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:'返回准备岗位',exact:false}).click();
    assert.equal(await page.locator('#prepLibraryView').isVisible(),true);
    assert.deepEqual(errors,[]);
    console.log('PASS: accept refreshes preparation list; rollback preserves unsaved drafts for export and prevents overwriting restored notes; no script errors.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
