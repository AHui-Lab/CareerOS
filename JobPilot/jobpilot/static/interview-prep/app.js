(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const workspaceId = new URLSearchParams(location.search).get('workspace');
  if (!workspaceId) { location.replace('/?view=interview_prep'); return; }
  const base = `/api/interview-prep/${encodeURIComponent(workspaceId)}`;
  let workspace, notes, sources = [], dirty = false, generation = 0, saving = false, docRequest = 0;

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `请求失败（${response.status}），请检查输入和连接。`);
    return data;
  }
  function notify(message, error = false) {
    $('notice').textContent = message;
    $('notice').classList.toggle('error', error);
    $('notice').hidden = false;
  }
  function changed() {
    dirty = true; generation += 1;
    $('saveState').textContent = '有修改尚未保存';
  }
  function safeExternal(url) {
    try { const parsed = new URL(url); return ['https:', 'http:'].includes(parsed.protocol) ? parsed.href : ''; }
    catch { return ''; }
  }
  function inline(raw) {
    const matcher = /\[([^\]]+)\]\(([^\s)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*/g;
    let result = '', offset = 0, match;
    while ((match = matcher.exec(raw))) {
      result += esc(raw.slice(offset, match.index));
      if (match[1]) {
        const id = match[2].replace(/\.md$/, '');
        if (workspace.documents.some(doc => doc.id === id)) result += `<a href="#doc=${encodeURIComponent(id)}" data-doc="${esc(id)}">${esc(match[1])}</a>`;
        else {
          const url = safeExternal(match[2]);
          result += url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(match[1])}</a>` : esc(match[1]);
        }
      } else if (match[3]) result += `<code>${esc(match[3])}</code>`;
      else result += `<strong>${esc(match[4])}</strong>`;
      offset = matcher.lastIndex;
    }
    return result + esc(raw.slice(offset));
  }
  function markdown(raw) {
    const lines = raw.replace(/\r/g, '').split('\n');
    const html = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;
      if (line.startsWith('```')) {
        const code = [];
        while (++i < lines.length && !lines[i].startsWith('```')) code.push(lines[i]);
        html.push(`<pre><code>${esc(code.join('\n'))}</code></pre>`);
      } else if (line.startsWith('|')) {
        const rows = [];
        while (i < lines.length && lines[i].startsWith('|')) rows.push(lines[i++]);
        i -= 1;
        const cells = row => row.split('|').slice(1, -1).map(cell => cell.trim());
        const header = cells(rows[0]).map(cell => `<th>${inline(cell)}</th>`).join('');
        const body = rows.slice(1).filter(row => !/^[\s|:\-]+$/.test(row)).map(row => `<tr>${cells(row).map(cell => `<td>${inline(cell)}</td>`).join('')}</tr>`).join('');
        html.push(`<div class="table-wrap"><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div>`);
      } else if (/^#{1,3} /.test(line)) {
        const level = line.indexOf(' ');
        html.push(`<h${level}>${inline(line.slice(level + 1))}</h${level}>`);
      } else if (line.startsWith('- ')) {
        const items = [];
        while (i < lines.length && lines[i].startsWith('- ')) items.push(`<li>${inline(lines[i++].slice(2))}</li>`);
        i -= 1; html.push(`<ul>${items.join('')}</ul>`);
      } else html.push(`<p>${inline(line)}</p>`);
    }
    return html.join('');
  }
  async function openDocument(id) {
    const doc = workspace.documents.find(item => item.id === id);
    if (!doc) return;
    const token = ++docRequest;
    document.querySelectorAll('[data-doc]').forEach(button => button.classList.toggle('active', button.dataset.doc === id));
    $('content').textContent = '正在加载资料…';
    $('docLabel').textContent = doc.title;
    $('download').href = `${base}/documents/${encodeURIComponent(id)}/download`;
    try {
      const data = await request(`${base}/documents/${encodeURIComponent(id)}`);
      if (token === docRequest) $('content').innerHTML = markdown(data.content);
    } catch (error) { if (token === docRequest) { $('content').textContent = '资料加载失败，可重试。'; notify(error.message, true); } }
  }
  function progress() {
    const count = document.querySelectorAll('#tasks input:checked').length;
    $('progress').max = Math.max(1, workspace.tasks.length); $('progress').value = count;
    $('progress').hidden = !workspace.tasks.length;
    $('progressText').textContent = `${count} / ${workspace.tasks.length}`;
    $('taskOverview').textContent = workspace.tasks.length ? `${count} / ${workspace.tasks.length} 项完成` : '从岗位要求开始';
  }
  function showJobDescription() {
    $('docLabel').textContent = '岗位 JD';
    $('download').hidden = true;
    $('content').innerHTML = `<h1>岗位 JD</h1><p style="white-space:pre-wrap">${esc($('jd').value || '还没有岗位 JD。请在“进度与笔记”中补充岗位要求。')}</p>`;
  }
  function renderSources() {
    $('sourceList').innerHTML = sources.map((source, index) => {
      const url = safeExternal(source.url);
      return `<article class="source-card"><div>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a>` : `<strong>${esc(source.title)}</strong>`}<p>${esc(source.note)}</p><small>${esc(source.url)}</small></div><button type="button" data-remove="${index}">移除</button></article>`;
    }).join('') || '<p class="muted">还没有资料，先添加一个可信来源。</p>';
  }
  function collect() {
    return {
      revision: notes.revision,
      interview_date: $('interview_date').value,
      location: $('location').value,
      jd: $('jd').value, questions: $('questions').value, notes: $('notesText').value,
      completed: [...document.querySelectorAll('#tasks input:checked')].map(input => input.value),
      sources: sources.map(source => ({...source}))
    };
  }
  function stamp(value) {
    return value ? `上次保存：${new Date(value).toLocaleString('zh-CN', {timeZone:'Asia/Shanghai'})}` : '手动保存 · 可导出备份';
  }
  async function save() {
    if (saving || !notes) return;
    saving = true; $('save').disabled = true;
    const capturedGeneration = generation;
    const body = collect();
    $('saveState').textContent = '正在保存…';
    try {
      const data = await request(`${base}/notes`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
      notes = data.notes;
      dirty = generation !== capturedGeneration;
      $('saveState').textContent = dirty ? '本次已保存，仍有新修改待保存' : '已保存到本机';
      $('savedAt').textContent = stamp(notes.updated_at);
      $('dateWindow').textContent = notes.interview_date || workspace.date_window;
      if (!workspace.documents.length) showJobDescription();
      if (window.parent !== window) window.parent.postMessage({type:'interview-prep-saved'}, location.origin);
      notify(dirty ? '保存完成；保存期间的新修改请再保存一次。' : '进度、岗位档案、笔记和资料链接已保存。');
    } catch (error) {
      $('saveState').textContent = '保存失败，当前内容仍在页面中';
      notify(error.message, true);
    } finally { saving = false; $('save').disabled = false; }
  }
  function selectTab(tab) {
    document.querySelectorAll('[data-tab]').forEach(button => {
      const selected = button.dataset.tab === tab;
      button.classList.toggle('active', selected); button.setAttribute('aria-pressed', String(selected));
    });
    document.querySelectorAll('.tab-panel').forEach(panel => { panel.hidden = panel.id !== tab; });
  }
  document.querySelectorAll('[data-tab]').forEach(button => button.addEventListener('click', () => selectTab(button.dataset.tab)));
  document.addEventListener('click', event => {
    const doc = event.target.closest('[data-doc]');
    if (doc) { event.preventDefault(); selectTab('reading'); openDocument(doc.dataset.doc); }
    const remove = event.target.closest('[data-remove]');
    if (remove) { sources.splice(Number(remove.dataset.remove), 1); changed(); renderSources(); }
  });
  $('notes').addEventListener('input', () => { changed(); progress(); });
  $('sourceForm').addEventListener('submit', event => {
    event.preventDefault();
    const url = safeExternal($('sourceUrl').value.trim());
    const title = $('sourceTitle').value.trim();
    if (!url || !title) return notify('请填写标题和 http/https 资料链接。', true);
    if (sources.length >= 300) return notify('最多保存 300 条来源，请先整理现有资料。', true);
    sources.push({title, url, note:$('sourceNote').value.trim()});
    changed(); renderSources(); $('sourceForm').reset();
    notify('已添加到收集区，点击底部保存后写入本机。');
  });
  $('save').addEventListener('click', save);
  $('export').addEventListener('click', () => {
    if (!notes) return;
    const payload = {workspace:workspace.id, exported_at:new Date().toISOString(), ...collect()};
    const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = `${workspace.id}-notes.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  window.requestPrepLeave = () => {
    if (saving) { notify('正在保存，请保存完成后再返回。'); return false; }
    if (dirty && !window.confirm('当前准备内容尚未保存。确定放弃修改并返回岗位列表？')) return false;
    dirty = false; return true;
  };
  async function load() {
    try {
      const data = await request(base); workspace = data.workspace; notes = data.notes; sources = notes.sources.map(source => ({...source}));
      $('title').textContent = workspace.title; $('summary').textContent = workspace.summary;
      document.title = `${workspace.title} · 面试准备`;
      $('dateWindow').textContent = notes.interview_date || workspace.date_window; $('team').textContent = workspace.team || '部门待补充';
      $('documentTotal').textContent = `${workspace.documents.length} 份资料`;
      $('documents').innerHTML = workspace.documents.map(doc => `<button type="button" data-doc="${esc(doc.id)}">${esc(doc.title)}</button>`).join('') || '<p class="muted">暂无准备资料，可在“资料来源”中添加链接。</p>';
      let lastDate = '';
      $('tasks').innerHTML = workspace.tasks.map(task => {
        const heading = task.date !== lastDate ? `<p class="task-date">${esc(task.date)}</p>` : ''; lastDate = task.date;
        return `${heading}<label class="task"><input type="checkbox" value="${esc(task.id)}" ${notes.completed.includes(task.id) ? 'checked' : ''}><span>${esc(task.text)}</span></label>`;
      }).join('') || '<p class="muted">暂无准备任务，可先在个人笔记中记录准备计划。</p>';
      for (const key of ['interview_date', 'location', 'jd', 'questions']) $(key).value = notes[key] || '';
      $('notesText').value = notes.notes || '';
      renderSources(); progress();
      $('save').disabled = false; $('export').disabled = false;
      $('saveState').textContent = notes.updated_at ? '已载入保存的笔记' : '准备资料已就绪';
      $('savedAt').textContent = stamp(notes.updated_at);
      if (workspace.documents.length) await openDocument(workspace.documents.find(doc => doc.id === '00-jd-analysis')?.id || workspace.documents[0].id);
      else showJobDescription();
    } catch (error) { $('title').textContent = '准备资料暂未连接'; $('saveState').textContent = '连接失败'; notify(`${error.message} 请启动或重新启动 CareerOS 后刷新。`, true); }
  }
  load();
})();
