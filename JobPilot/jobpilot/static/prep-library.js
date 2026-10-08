(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let items = [], requestId = 0;

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '请检查输入和连接后重试。');
    return data;
  }
  function render() {
    const search = $('prepSearch').value.trim().toLocaleLowerCase();
    const filtered = items.filter(item => [item.title, item.team, item.summary].join(' ').toLocaleLowerCase().includes(search));
    $('prepCount').textContent = search ? `${filtered.length} / ${items.length} 个岗位` : `${items.length} 个岗位`;
    $('prepEmpty').classList.toggle('hidden', filtered.length > 0);
    $('prepWorkspaceList').innerHTML = filtered.map(item => {
      const progress = item.task_count ? `${item.completed_count} / ${item.task_count} 项已完成` : '尚未设置准备任务';
      const percent = item.task_count ? Math.round(item.completed_count / item.task_count * 100) : 0;
      return `<article class="prep-workspace-card"><div class="prep-card-heading"><span class="prep-card-label">岗位准备</span><span class="helper">${esc(item.interview_date || item.date_window || '时间待确认')}</span></div><h3>${esc(item.title)}</h3><p class="helper prep-card-team">${esc(item.team || '部门待补充')}</p><p class="prep-card-summary">${esc(item.summary || '整理岗位要求、待确认问题和个人笔记。')}</p><div class="prep-card-meta"><span>${item.document_count} 份准备资料</span><span>${progress}</span></div><progress max="100" value="${percent}" aria-label="${esc(item.title)}准备进度"></progress><div class="prep-card-footer"><span class="helper">${item.updated_at ? `上次保存 ${esc(new Date(item.updated_at).toLocaleDateString('zh-CN', {timeZone:'Asia/Shanghai'}))}` : '可记录进度与笔记'}</span><button type="button" class="primary-btn" data-open-prep="${esc(item.id)}" aria-label="查看${esc(item.title)}准备">查看准备 →</button></div></article>`;
    }).join('');
  }
  async function load() {
    const token = ++requestId;
    try {
      const data = await request('/api/interview-prep');
      if (token !== requestId) return;
      items = data.items || []; render();
    } catch (error) {
      if (token !== requestId) return;
      $('prepEmpty').classList.add('hidden');
      $('prepWorkspaceList').innerHTML = `<div class="empty-state"><h3>准备岗位加载失败</h3><p>${esc(error.message)}</p><button class="ghost-btn" type="button" data-retry-prep>重新加载</button></div>`;
    }
  }
  function canLeave() {
    const frame = $('interviewPrepFrame');
    return !frame.contentWindow?.requestPrepLeave || frame.contentWindow.requestPrepLeave();
  }
  function openWorkspace(item) {
    if (!canLeave()) return;
    $('prepDetailTitle').textContent = item.title;
    $('prepLibraryView').classList.add('hidden');
    $('prepDetailView').classList.remove('hidden');
    $('interviewPrepFrame').src = `/static/interview-prep/index.html?workspace=${encodeURIComponent(item.id)}`;
    $('backToPrepList').focus();
  }
  $('prepSearch').addEventListener('input', render);
  $('prepWorkspaceList').addEventListener('click', event => {
    if (event.target.closest('[data-retry-prep]')) { load(); return; }
    const button = event.target.closest('[data-open-prep]');
    const item = items.find(item => item.id === button?.dataset.openPrep);
    if (item) openWorkspace(item);
  });
  $('backToPrepList').addEventListener('click', () => {
    if (!canLeave()) return;
    $('interviewPrepFrame').src = 'about:blank';
    $('prepDetailView').classList.add('hidden');
    $('prepLibraryView').classList.remove('hidden');
    load(); $('prepSearch').focus();
  });
  $('addPrepBtn').addEventListener('click', () => {
    $('prepCreateError').hidden = true;
    $('prepCreateDialog').showModal();
  });
  for (const id of ['prepCreateClose', 'prepCreateCancel']) $(id).addEventListener('click', () => $('prepCreateDialog').close());
  $('prepCreateForm').addEventListener('submit', async event => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    payload.company = payload.company.trim(); payload.role = payload.role.trim();
    if (!payload.company || !payload.role) {
      $('prepCreateError').textContent = '请填写公司和岗位。'; $('prepCreateError').hidden = false; return;
    }
    $('prepCreateSubmit').disabled = true; $('prepCreateError').hidden = true;
    try {
      const data = await request('/api/interview-prep', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      $('prepCreateDialog').close(); $('prepCreateForm').reset();
      await load(); openWorkspace(data.workspace);
    } catch (error) {
      $('prepCreateError').textContent = error.message; $('prepCreateError').hidden = false;
    } finally { $('prepCreateSubmit').disabled = false; }
  });
  $('refreshBtn').addEventListener('click', load);
  window.addEventListener('careeros-data-restored', () => {
    load();
    const frame = $('interviewPrepFrame');
    if (frame.contentWindow?.interviewPrepDataRestored?.() === false) return;
    frame.src = 'about:blank';
    $('prepDetailView').classList.add('hidden');
    $('prepLibraryView').classList.remove('hidden');
  });
  document.querySelector('[data-view="interview_prep"]').addEventListener('click', load);
  window.addEventListener('message', event => {
    if (event.origin === location.origin && event.source === $('interviewPrepFrame').contentWindow && event.data?.type === 'interview-prep-saved') load();
  });
  load();
})();
