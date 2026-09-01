const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];
let experiences = [];
let currentExperience = null;
let editingExperience = {};
let saveTimer = null;
let editorSession = 0;
let experienceCategories = [];
const TYPE_LABELS = {project:'项目', internship:'实习', research:'科研', competition:'竞赛', award:'获奖', patent:'专利', paper:'论文', book:'专著', certificate:'软著', education:'教育', work:'工作', volunteer:'志愿/社会实践', campus:'校园经历', other:'其他'};

async function loadExperienceCategories(){
  const data=await api('/api/experience-categories');
  experienceCategories=data.items||[];
  experienceCategories.forEach(category=>{if(category.types?.length===1)TYPE_LABELS[category.types[0]]=category.label});
  return experienceCategories;
}
function typeOptions(current=''){
  const special={patent:'专利',certificate:'软著'};
  const values=experienceCategories.flatMap(category=>(category.types||[category.id]).map(value=>[value,special[value]||(category.types?.length===1?category.label:`${category.label} · ${TYPE_LABELS[value]||value}`)]));
  if(current&&!values.some(([value])=>value===current))values.push([current,TYPE_LABELS[current]||`历史分类（${current}）`]);
  return values.map(([value,label])=>`<option value="${esc(value)}">${esc(label)}</option>`).join('');
}

async function api(url, options={}) {
  const res = await fetch(url, {headers:{'Content-Type':'application/json', ...(options.headers||{})}, ...options});
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
function esc(v=''){return String(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
function csv(v){return (v||[]).join(', ')}
function parseCsv(v){return v.split(',').map(x=>x.trim()).filter(Boolean)}
function state(text){$('#saveState').textContent=text}

$$('.nav').forEach(b=>b.onclick=()=>showView(b.dataset.view));
async function showView(id){
  $$('.nav').forEach(x=>x.classList.toggle('active',x.dataset.view===id));
  $$('.view').forEach(x=>x.classList.toggle('active',x.id===id));
  if(id==='dashboard') await renderDashboard();
  if(id==='experiences') await renderExperiences();
  if(id==='profile') { await renderProfile(); $('#profile .notice')?.remove(); }
  if(id==='settings') renderSettings();
  if(id==='files') await renderFiles();
  if(id==='inbox') await renderInbox();
  if(id==='integration') renderIntegration();
}

async function renderDashboard(){
  const d=await api('/api/dashboard');
  $('#dashboard').innerHTML=`<div class="topbar"><div><h1>Career OS</h1><div class="muted">记录事实，生成简历，交给 JobPilot 使用。</div></div><button class="btn" id="quickAdd">+ 快速记录</button></div>
  <div class="grid">
    <div class="card metric">经历<strong>${d.experience_count}</strong></div>
    <div class="card metric">可用于简历<strong>${d.resume_ready_count}</strong></div>
    <div class="card metric">进行中<strong>${d.active_count}</strong></div>
    <div class="card metric">待整理 Inbox<strong>${d.inbox_count}</strong></div>
  </div>
  <h2>最近经历</h2><div class="list">${d.recent_experiences.map(expCard).join('')||'<div class="card muted">还没有经历，先创建第一条。</div>'}</div>
  <h2>Git 状态</h2><div class="card">${d.git.available ? `${d.git.changes.length} 个未提交变更` : '当前目录尚未初始化 Git 或 Git 不可用'}</div>`;
  $('#quickAdd').onclick=openQuickAdd;
  $$('.experience-card').forEach(x=>x.onclick=()=>openExperience(x.dataset.id));
}

function compactText(value='',limit=150){const text=String(value||'').replace(/\s+/g,' ').trim();return text.length>limit?text.slice(0,limit)+'…':text}
function experienceDateText(x){return [x.start,x.end].filter(Boolean).join(' ~ ')}
function expCard(x){const details=x.details||{},type=x.type||'other';let title=x.title||'未命名记录',meta='',description='';
  if(type==='project'){meta=[experienceDateText(x),x.role].filter(Boolean).join(' · ');description=x.summary||x.facts}
  else if(type==='internship'){title=x.organization||title;meta=[x.role,experienceDateText(x)].filter(Boolean).join(' · ');description=x.facts||x.summary}
  else if(type==='award'){meta=[x.start,details.award_level].filter(Boolean).join(' · ');description=x.summary}
  else if(['patent','certificate'].includes(type)){meta=[x.start,details.registration_number||details.patent_number||details.certificate_number].filter(Boolean).join(' · ')}
  else if(type==='campus'){description=x.results}
  else{meta=[x.organization,x.role,experienceDateText(x)].filter(Boolean).join(' · ');description=x.summary}
  return `<div class="card experience-card" data-id="${esc(x.id)}"><div class="row"><strong>${esc(title)}</strong><span class="status">${esc(TYPE_LABELS[type]||type||'其他')}</span></div>${meta?`<div class="muted">${esc(meta)}</div>`:''}${description?`<div class="experience-brief">${esc(compactText(description))}</div>`:''}</div>`}

window.addEventListener('message',event=>{if(event.data?.type==='careeros-vault-view'&&['experiences','inbox'].includes(event.data.view))showView(event.data.view);if(event.data?.type==='careeros-vault-new-experience'){showView('experiences').then(()=>setTimeout(()=>openExperience(),50))}if(event.data?.type==='careeros-vault-open-experience'&&event.data.id){showView('experiences').then(()=>openExperience(event.data.id))}if(event.data?.type==='careeros-vault-manage-categories'){showView('experiences').then(()=>openCategoryManager())}});

function dateRangeFields(x={}){const current=x.end==='至今';return `<label>开始时间<input data-exp-field id="f-start" value="${esc(x.start||'')}" placeholder="例如：2024-09"></label><label>结束时间<input data-exp-field id="f-end" value="${current?'':esc(x.end||'')}" placeholder="例如：2025-06" ${current?'disabled':''}><span class="current-date-option"><input data-exp-field id="f-current" type="checkbox" ${current?'checked':''}> 至今</span></label>`}
function awardLevelOptions(current=''){const values=['国际级','国家级','省市级','校级','院级'];if(current&&!values.includes(current))values.push(current);return `<option value="">请选择</option>`+values.map(value=>`<option value="${esc(value)}" ${value===current?'selected':''}>${esc(value)}</option>`).join('')}
function experienceFields(x={}){const type=x.type||'project',details=x.details||{};
  if(type==='project')return `<label class="full">项目名称<input data-exp-field id="f-title" value="${esc(x.title||'')}" required></label>${dateRangeFields(x)}<label class="full">职责<input data-exp-field id="f-role" value="${esc(x.role||'')}"></label><label class="full">项目描述<textarea data-exp-field id="f-summary">${esc(x.summary||'')}</textarea></label><label class="full">项目中职责<textarea data-exp-field id="f-facts">${esc(x.facts||details.project_role||'')}</textarea></label>`;
  if(type==='internship')return `<label class="full">实习单位名称<input data-exp-field id="f-org" value="${esc(x.organization||'')}" required></label>${dateRangeFields(x)}<label class="full">职位名称<input data-exp-field id="f-role" value="${esc(x.role||'')}"></label><label class="full">工作职责<textarea data-exp-field id="f-facts">${esc(x.facts||x.summary||'')}</textarea></label>`;
  if(type==='award')return `<label>获奖时间<input data-exp-field id="f-award-date" value="${esc(x.start||'')}" placeholder="例如：2025-06"></label><label>奖项级别<select data-exp-field id="f-award-level">${awardLevelOptions(details.award_level||'')}</select></label><label class="full">奖项内容<textarea data-exp-field id="f-award-content" required>${esc(x.title||x.summary||'')}</textarea></label>`;
  if(['patent','certificate'].includes(type)){const number=details.registration_number||details.patent_number||details.certificate_number||'';return `<label class="full">专利或软著名称<input data-exp-field id="f-title" value="${esc(x.title||'')}" required></label><label>取得时间<input data-exp-field id="f-obtained-date" value="${esc(x.start||'')}" placeholder="例如：2025-06"></label><label>登记号<input data-exp-field id="f-registration-number" value="${esc(number)}"></label>`}
  if(type==='campus')return `<label class="full">经历内容<textarea data-exp-field id="f-campus-content" required>${esc(x.summary||x.title||'')}</textarea></label><label class="full">获得的经验和收获<textarea data-exp-field id="f-campus-gain">${esc(x.results||'')}</textarea></label>`;
  return `<label class="full">名称<input data-exp-field id="f-title" value="${esc(x.title||'')}" required></label>${dateRangeFields(x)}<label class="full">职责<input data-exp-field id="f-role" value="${esc(x.role||'')}"></label><label class="full">描述<textarea data-exp-field id="f-summary">${esc(x.summary||'')}</textarea></label>`;
}
function experienceForm(x={}){return `<div class="topbar"><div><h2>${x.id?'编辑经历':'新增经历'}</h2><div class="muted">选择分类后，填写项会自动切换。</div></div><button class="btn ghost" id="closeModal">关闭</button></div><div class="form form-grid compact-experience-form"><label class="full">分类<select id="f-type">${typeOptions(x.type||'')}</select></label><div class="full form-grid" id="experienceFields">${experienceFields(x)}</div><div class="full row wrap"><button class="btn" id="saveExp">${x.id?'保存':'创建记录'}</button>${x.id?'<button class="btn ghost" id="uploadBtn">上传佐证文件</button><input type="file" id="fileInput" hidden><button class="btn danger" id="deleteExp">删除</button>':''}</div>${x.id?`<div class="full evidence-list">${(x.attachments||[]).map(a=>`<div>📎 ${esc(a.name)} <span class="muted">${Math.ceil(a.size/1024)} KB</span></div>`).join('')||'<span class="muted">暂未上传佐证文件。</span>'}</div>`:''}</div>`}

async function openExperience(id, seed={}){
  const session=++editorSession;
  if(!experienceCategories.length)await loadExperienceCategories();
  const x=id?await api('/api/experiences/'+id):seed; currentExperience=x.id||null;editingExperience={...x,details:{...(x.details||{})}};
  $('#modalCard').innerHTML=experienceForm(x); $('#modal').classList.remove('hidden');
  $('#f-type').value=x.type||'project'; wireExperienceFields();
  $('#closeModal').onclick=closeModal; $('#saveExp').onclick=()=>saveExperience(!x.id);
  if(x.id){
    $('#deleteExp').onclick=async()=>{if(confirm('确定删除这条经历及其附件？')){await api('/api/experiences/'+x.id,{method:'DELETE'});closeModal();await renderExperiences();}};
    $('#uploadBtn').onclick=()=>$('#fileInput').click();
    $('#fileInput').onchange=async e=>{const f=e.target.files[0];if(!f)return;const fd=new FormData();fd.append('file',f);state('上传中…');try{const res=await fetch(`/api/experiences/${x.id}/attachments`,{method:'POST',body:fd});if(!res.ok)throw new Error(await res.text());state('已上传');await openExperience(x.id)}catch(error){state('上传失败');alert(`上传失败：${error.message}`)}};
  }
  $('#f-type').addEventListener('change',()=>{const type=$('#f-type').value;$('#experienceFields').innerHTML=experienceFields({type,details:{}});wireExperienceFields()});
}
function closeModal(){editorSession++;$('#modal').classList.add('hidden');currentExperience=null;editingExperience={};clearTimeout(saveTimer)}
function fieldValue(id){return $('#'+id)?.value.trim()||''}
function wireExperienceFields(){const current=$('#f-current'),end=$('#f-end');if(current&&end){current.onchange=()=>{end.disabled=current.checked;if(current.checked)end.value='';scheduleAutosave()}};$$('[data-exp-field]').forEach(el=>el.addEventListener('input',scheduleAutosave))}
function endValue(){return $('#f-current')?.checked?'至今':fieldValue('f-end')}
function payload(){const type=$('#f-type').value,base=editingExperience;const p={type,status:base.status||'active',title:base.title||'',organization:base.organization||'',role:base.role||'',start:base.start||'',end:base.end||'',domains:base.domains||[],skills:base.skills||[],related_experience_ids:base.related_experience_ids||[],details:{...(base.details||{})},resume_ready:Boolean(base.resume_ready),summary:base.summary||'',facts:base.facts||'',results:base.results||'',notes:base.notes||''};
  if(type==='project')Object.assign(p,{title:fieldValue('f-title'),start:fieldValue('f-start'),end:endValue(),role:fieldValue('f-role'),summary:fieldValue('f-summary'),facts:fieldValue('f-facts')});
  else if(type==='internship'){const organization=fieldValue('f-org'),role=fieldValue('f-role');Object.assign(p,{organization,role,start:fieldValue('f-start'),end:endValue(),facts:fieldValue('f-facts'),title:[organization,role].filter(Boolean).join(' · ')})}
  else if(type==='award'){p.start=fieldValue('f-award-date');p.title=fieldValue('f-award-content');p.details.award_level=fieldValue('f-award-level')}
  else if(['patent','certificate'].includes(type)){p.title=fieldValue('f-title');p.start=fieldValue('f-obtained-date');const number=fieldValue('f-registration-number');p.details.registration_number=number;if(type==='patent')p.details.patent_number=number;else p.details.certificate_number=number}
  else if(type==='campus'){p.summary=fieldValue('f-campus-content');p.results=fieldValue('f-campus-gain');p.title=(p.summary.split(/\r?\n/)[0]||'校园经历').slice(0,80)}
  else Object.assign(p,{title:fieldValue('f-title'),start:fieldValue('f-start'),end:endValue(),role:fieldValue('f-role'),summary:fieldValue('f-summary')});return p}
async function saveExperience(create=false){const p=payload();if(!p.title)return alert('请填写经历名称');const session=editorSession;const id=currentExperience;state('保存中…');try{const x=await api(create?'/api/experiences':'/api/experiences/'+id,{method:create?'POST':'PATCH',body:JSON.stringify(p)});if(session!==editorSession)return x;currentExperience=x.id;state('✓ 已保存 '+new Date().toLocaleTimeString());if(create)await openExperience(x.id);return x}catch(error){if(session===editorSession){state('保存失败');alert(`保存失败，编辑窗口未关闭：${error.message}`)}throw error}}
function scheduleAutosave(){if(!currentExperience)return;state('未保存…');clearTimeout(saveTimer);saveTimer=setTimeout(()=>{if(!payload().title){state('请补充必填项');return}saveExperience(false).catch(()=>{})},700)}

function educationRows(items=[]){const rows=(items.length?items:[{}]);return rows.map((e,i)=>`<div class="card edu-row" data-index="${i}"><div class="row"><strong>教育经历 ${i+1}</strong><button type="button" class="btn ghost remove-edu">删除</button></div><div class="form-grid"><label>学校<input data-k="school" value="${esc(e.school||e.institution||'')}"></label><label>学院<input data-k="college" value="${esc(e.college||'')}"></label><label>专业<input data-k="major" value="${esc(e.major||'')}"></label><label>学历/学位<input data-k="degree" value="${esc(e.degree||'')}"></label><label>开始<input data-k="start" value="${esc(e.start||'')}"></label><label>毕业/结束<input data-k="end" value="${esc(e.end||e.graduation_date||'')}"></label><label>GPA<input data-k="gpa" value="${esc(e.gpa||'')}"></label><label>排名<input data-k="rank" value="${esc(e.rank||'')}"></label></div></div>`).join('')}
function collectEducation(){return $$('.edu-row').map(row=>{const out={};$$('[data-k]',row).forEach(el=>out[el.dataset.k]=el.value.trim());return out}).filter(x=>Object.values(x).some(Boolean))}
function wireEducation(){$$('.remove-edu').forEach(b=>b.onclick=()=>{if($$('.edu-row').length>1)b.closest('.edu-row').remove()})}
async function renderProfile(){const p=await api('/api/profile');$('#profile').innerHTML=`<div class="topbar"><div><h1>个人资料</h1><div class="muted">公开职业字段与本地敏感字段分开保存。</div></div></div><div class="notice">当前仓库为公开仓库。手机号和邮箱会写入 Git 忽略的 private/profile.yaml；实际经历数据也建议等仓库改成 Private 后再提交到 GitHub。</div><br><div class="card form form-grid"><label>姓名<input id="p-name" value="${esc(p.name||'')}"></label><label>城市<input id="p-city" value="${esc(p.city||'')}"></label><label class="full">一句话定位<input id="p-headline" value="${esc(p.headline||'')}"></label><label>邮箱（本地私有）<input id="p-email" value="${esc(p.email||'')}"></label><label>手机（本地私有）<input id="p-phone" value="${esc(p.phone||'')}"></label><label>GitHub<input id="p-github" value="${esc(p.github||'')}"></label><label>作品集<input id="p-portfolio" value="${esc(p.portfolio||'')}"></label><label class="full">技能（逗号）<input id="p-skills" value="${esc(csv(p.skills))}"></label></div><div class="topbar"><h2>教育经历</h2><button class="btn ghost" id="addEdu" type="button">+ 添加教育经历</button></div><div id="educationList" class="list">${educationRows(p.education||[])}</div><br><button class="btn" id="saveProfile">保存资料</button>`;wireEducation();$('#addEdu').onclick=()=>{$('#educationList').insertAdjacentHTML('beforeend',educationRows([{}]));wireEducation()};$('#saveProfile').onclick=async()=>{state('保存中…');await api('/api/profile',{method:'PUT',body:JSON.stringify({name:$('#p-name').value,city:$('#p-city').value,headline:$('#p-headline').value,email:$('#p-email').value,phone:$('#p-phone').value,github:$('#p-github').value,portfolio:$('#p-portfolio').value,skills:parseCsv($('#p-skills').value),education:collectEducation()})});state('✓ 已保存')}}
function renderSettings(){
  $('#settings').innerHTML=`<div class="topbar"><div><h1>配置</h1><div class="muted">低频使用的文件、Inbox 和 JobPilot 工具集中放在这里。</div></div></div><div class="grid config-grid"><button class="card config-card" data-config-view="files"><strong>文件</strong><span class="muted">浏览、上传和编辑 Markdown / YAML / JSON 等资料文件。</span></button><button class="card config-card" data-config-view="inbox"><strong>Inbox</strong><span class="muted">暂存想法、进展和待整理内容。</span></button><button class="card config-card" data-config-view="integration"><strong>JobPilot 集成</strong><span class="muted">查看 CareerVault 与求职管理模块的接口状态。</span></button></div>`;
  $$('[data-config-view]').forEach(button=>button.onclick=()=>showView(button.dataset.configView));
}

async function renderFiles(){const data=await api('/api/files');const items=data.items||[];$('#files').innerHTML=`<div class="topbar"><div><h1>文件</h1><div class="muted">Markdown / YAML / TXT / JSON 可直接编辑；PDF、DOCX、图片等保留原文件。</div></div><div class="row"><button class="btn" id="uploadGeneral">+ 添加文件</button><input type="file" id="generalFileInput" hidden></div></div><div class="list">${items.map(f=>`<div class="card file-card" data-path="${esc(f.path)}" data-editable="${f.text_editable?'1':'0'}"><div class="row"><strong>${esc(f.name)}</strong><span class="status">${esc(f.extension||'file')}</span></div><div class="muted">${esc(f.path)} · ${Math.max(1,Math.ceil(f.size/1024))} KB</div></div>`).join('')||'<div class="card muted">还没有文件。你可以把 PDF / DOCX / Markdown 等先丢进 Inbox 文件区。</div>'}</div>`;$('#uploadGeneral').onclick=()=>$('#generalFileInput').click();$('#generalFileInput').onchange=async e=>{const f=e.target.files[0];if(!f)return;const fd=new FormData();fd.append('file',f);fd.append('directory','inbox/files');state('上传中…');const r=await fetch('/api/files/upload',{method:'POST',body:fd});if(!r.ok)return alert(await r.text());state('✓ 已上传');renderFiles()};$$('.file-card').forEach(card=>card.onclick=()=>card.dataset.editable==='1'?openTextFile(card.dataset.path):window.open('/api/files/raw?path='+encodeURIComponent(card.dataset.path),'_blank'))}
async function openTextFile(path){const f=await api('/api/files/read?path='+encodeURIComponent(path));$('#modalCard').innerHTML=`<div class="topbar"><div><h2>${esc(path)}</h2><div class="muted">停止输入 700ms 后自动保存</div></div><button class="btn ghost" id="closeModal">关闭</button></div><div class="form"><textarea id="rawFileEditor" style="min-height:65vh;font-family:ui-monospace,SFMono-Regular,Consolas,monospace">${esc(f.content||'')}</textarea></div>`;$('#modal').classList.remove('hidden');$('#closeModal').onclick=closeModal;const editor=$('#rawFileEditor');editor.addEventListener('input',()=>{state('未保存…');clearTimeout(saveTimer);saveTimer=setTimeout(async()=>{state('保存中…');await api('/api/files/write',{method:'PUT',body:JSON.stringify({path,content:editor.value})});state('✓ 已保存 '+new Date().toLocaleTimeString())},700)})}

async function renderInbox(){const xs=await api('/api/inbox');$('#inbox').innerHTML=`<div class="topbar"><div><h1>草稿箱</h1><div class="muted">记录尚未整理的修改想法，需要时可转成正式经历继续完善。</div></div><button class="btn" id="quickAdd2">+ 新建草稿</button></div><div class="list">${xs.map(x=>`<div class="card draft-card"><div class="row"><strong>${esc(x.title)}</strong><span class="status">${esc(x.kind)}</span></div><p>${esc(x.content)}</p><div class="row wrap"><span class="muted">${esc(x.created_at)}</span><button class="btn promote-draft" data-id="${esc(x.id)}">转为经历</button><button class="btn ghost delete-inbox" data-id="${esc(x.id)}">删除</button></div></div>`).join('')||'<div class="card muted">草稿箱是空的。可以先写下待补充的事实、成果或修改想法。</div>'}</div>`;$('#quickAdd2').onclick=openQuickAdd;$$('.delete-inbox').forEach(b=>b.onclick=async()=>{if(confirm('确定删除这条草稿？')){await api('/api/inbox/'+b.dataset.id,{method:'DELETE'});renderInbox()}});$$('.promote-draft').forEach(b=>b.onclick=async()=>{const draft=xs.find(x=>x.id===b.dataset.id);if(!draft)return;b.disabled=true;try{const created=await api('/api/experiences',{method:'POST',body:JSON.stringify({type:'project',title:draft.title||'未命名草稿',summary:draft.content||'',notes:'由草稿箱转入',status:'draft',resume_ready:false})});await api('/api/inbox/'+draft.id,{method:'DELETE'});await showView('experiences');await openExperience(created.id)}catch(error){alert(`转换失败：${error.message}`);b.disabled=false}})}
async function openQuickAdd(){if(!experiences.length)experiences=await api('/api/experiences');const options=experiences.map(x=>`<option value="${esc(x.id)}">${esc(x.title)}</option>`).join('');$('#modalCard').innerHTML=`<div class="topbar"><h2>新建草稿</h2><button class="btn ghost" id="closeModal">关闭</button></div><div class="form"><label>标题<input id="q-title" placeholder="例如：补充项目量化成果"></label><label>类型<select id="q-kind"><option value="idea">修改想法</option><option value="note">记录</option><option value="log">进展日志</option></select></label><label>关联经历<select id="q-rel"><option value="">暂不关联</option>${options}</select></label><label>内容<textarea class="quick" id="q-content" autofocus></textarea></label><button class="btn" id="q-save">保存草稿</button></div>`;$('#modal').classList.remove('hidden');$('#closeModal').onclick=closeModal;$('#q-save').onclick=async()=>{const content=$('#q-content').value.trim();if(!content)return alert('请填写草稿内容');await api('/api/inbox',{method:'POST',body:JSON.stringify({title:$('#q-title').value.trim(),content,kind:$('#q-kind').value,related_experience_id:$('#q-rel').value})});closeModal();showView('inbox')}}

function renderIntegration(){$('#integration').innerHTML=`<div class="topbar"><div><h1>JobPilot 集成</h1><div class="muted">CareerVault = 事实库，JobPilot = JD 匹配 / 简历生成 / 网申填写。</div></div></div><div class="card"><h3>本地 API</h3><div class="code">GET  http://127.0.0.1:8766/api/jobpilot/profile\nGET  http://127.0.0.1:8766/api/jobpilot/experiences?resume_ready=true\nPOST http://127.0.0.1:8766/api/jobpilot/context</div><p>JobPilot 对每个 JD 调用 context 接口，即可拿到基础资料和排序后的 Resume Ready 经历。</p></div>`}

$('#gitSnapshot').onclick=async()=>{const msg=prompt('Git 提交说明','Update CareerVault');if(msg===null)return;const r=await api('/api/git/snapshot',{method:'POST',body:JSON.stringify({message:msg})});alert(r.ok?(r.commit?'已创建快照 '+r.commit:r.message):'失败：'+r.message)};
$('#modal').onclick=e=>{if(e.target.id==='modal')closeModal()};
function categoryForTab(tab){return experienceCategories.find(category=>category.id===tab)}
function matchesCategory(item, category){return Boolean(category?.types?.includes(item.type))}
function experienceMatchesSearch(item, query){return !query||[item.title,item.organization,item.role,...(item.skills||[]),...(item.domains||[])].join(' ').toLowerCase().includes(query)}
function wireExperienceCards(){$$('.experience-card').forEach(card=>card.onclick=()=>openExperience(card.dataset.id))}
function categorySection(category, items){return `<section class="experience-category-section"><div class="category-heading"><h2>${esc(category.label)}</h2><span>${items.length} 条</span></div><div class="list">${items.map(expCard).join('')||'<div class="card muted">这个分类还没有记录。</div>'}</div></section>`}

async function openCategoryManager(){
  if(!experienceCategories.length)await loadExperienceCategories();
  let working=experienceCategories.map(category=>({...category,types:[...(category.types||[])]}));
  const syncLabels=()=>{$$('[data-category-label]').forEach((input,index)=>{if(working[index])working[index].label=input.value.trim()})};
  const draw=()=>{
    $('#categoryRows').innerHTML=working.map((category,index)=>`<div class="category-row" data-index="${index}"><label>分类名称<input data-category-label value="${esc(category.label)}"></label><div class="category-key"><span class="muted">${esc((category.types||[]).join('、'))}</span><button class="btn ghost remove-category" type="button">删除</button></div></div>`).join('')||'<div class="card muted">当前没有分类，可以点击“添加分类”。</div>';
    $$('.remove-category').forEach(button=>button.onclick=()=>{syncLabels();const index=Number(button.closest('[data-index]').dataset.index);working.splice(index,1);draw()});
  };
  $('#modalCard').innerHTML=`<div class="topbar"><div><h2>管理分类</h2><div class="muted">可以改名、增加或隐藏分类；已有经历数据不会被删除。</div></div><button class="btn ghost" id="closeModal">关闭</button></div><div id="categoryRows" class="category-manager"></div><div class="row wrap category-manager-actions"><button class="btn ghost" id="addCategory" type="button">+ 添加分类</button><button class="btn" id="saveCategories" type="button">保存分类</button></div>`;
  $('#modal').classList.remove('hidden');draw();$('#closeModal').onclick=closeModal;
  $('#addCategory').onclick=()=>{syncLabels();const id=`custom_${Date.now()}`;working.push({id,label:'新分类',types:[id]});draw()};
  $('#saveCategories').onclick=async()=>{syncLabels();if(!working.length)return alert('请至少保留一个分类');if(working.some(category=>!category.label))return alert('分类名称不能为空');try{const data=await api('/api/experience-categories',{method:'PUT',body:JSON.stringify({items:working})});experienceCategories=data.items||[];closeModal();await renderExperiences()}catch(error){alert(`保存分类失败：${error.message}`)}};
}

async function renderExperiences(){
  [experiences]=await Promise.all([api('/api/experiences'),loadExperienceCategories()]);
  $('#experiences').innerHTML=`<div class="topbar"><div><h1>经历和项目</h1><div class="muted">按分类直接查看和维护经历；每条记录都可以上传佐证文件。</div></div></div><div class="experience-toolbar"><div class="row wrap"><button class="btn" id="innerNewExp">+ 新增记录</button><button class="btn ghost" id="manageCategories">管理分类</button></div><label class="experience-search">搜索<input id="experienceSearch" placeholder="名称、单位、技能…"></label></div><div class="row wrap experience-tabs"><button class="btn" data-exp-tab="all">全部</button>${experienceCategories.map(category=>`<button class="btn ghost" data-exp-tab="${esc(category.id)}">${esc(category.label)}</button>`).join('')}</div><div id="experienceList"></div>`;
  let tab='all';
  const draw=()=>{
    const query=$('#experienceSearch').value.trim().toLowerCase();
    const searched=experiences.filter(item=>experienceMatchesSearch(item,query));
    if(tab==='all'){
      const categorizedTypes=new Set(experienceCategories.flatMap(category=>category.types||[]));
      const sections=experienceCategories.map(category=>categorySection(category,searched.filter(item=>matchesCategory(item,category))));
      const historical=searched.filter(item=>!categorizedTypes.has(item.type));
      if(historical.length)sections.push(categorySection({label:'其他历史记录'},historical));
      $('#experienceList').innerHTML=sections.join('')||'<div class="card muted">还没有经历记录。</div>';
    }else{
      const category=categoryForTab(tab);const items=searched.filter(item=>matchesCategory(item,category));
      $('#experienceList').innerHTML=`<div class="list">${items.map(expCard).join('')||'<div class="card muted">这个分类还没有记录，可以点击“新增记录”。</div>'}</div>`;
    }
    wireExperienceCards();
  };
  $$('[data-exp-tab]').forEach(button=>button.onclick=()=>{$$('[data-exp-tab]').forEach(item=>item.classList.toggle('ghost',item!==button));tab=button.dataset.expTab;draw()});
  $('#experienceSearch').oninput=draw;$('#innerNewExp').onclick=()=>openExperience();$('#manageCategories').onclick=openCategoryManager;draw();
}
showView('experiences');
