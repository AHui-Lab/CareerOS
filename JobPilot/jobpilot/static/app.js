const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

const STATUS = UI_TEXT.status;
const CATEGORY = UI_TEXT.category;
const JOB_CATEGORY = UI_TEXT.jobCategory;
const UNSUBMITTED_STATUSES = new Set(['inbox','interested','preparing']);
const SUBMITTED_STATUSES = new Set(['applied','interview','offer','rejected']);

let state = {
  opportunities:[], scheduleEvents:[], emails:[], emailSettings:{}, profile:{}, experiences:[], versions:[], interviewQuestions:[], roleFieldSets:[], dataStatus:{}, syncStatus:{}, health:{}, latestVersion:null,
  memoEditing:null, memoScope:'all', emailFilter:'pending', recommendations:[], recommendationDefaultIds:[], recommendationSignature:'',
  recommendationsLoading:false
};
let recommendationTimer = null;

function esc(v=''){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function notice(text,error=false){const el=$('#globalNotice');if(!el)return;el.textContent=text;el.classList.toggle('error',error);el.classList.remove('hidden');setTimeout(()=>el.classList.add('hidden'),7000);}
async function api(path,options={}){
  const headers={...(options.headers||{})};
  if(options.body && !(options.body instanceof FormData) && !headers['Content-Type']) headers['Content-Type']='application/json';
  const res=await fetch(path,{...options,headers});
  const raw=await res.text(); let data={};
  try{data=raw?JSON.parse(raw):{};}catch{data={detail:raw||`请求失败 ${res.status}`};}
  if(!res.ok) throw new Error(data.detail||`请求失败 ${res.status}`);
  return data;
}

async function loadAll(){
  try{
    const [ops,schedule,emailMessages,emailSettings,profile,exps,versions,questions,fieldSets,dataStatus,syncStatus,health]=await Promise.all([
      api('/api/opportunities'), api('/api/schedule-events'), api('/api/email/messages'), api('/api/email/settings'), api('/api/profile'), api('/api/experiences'), api('/api/resume-versions'), api('/api/interview-questions'), api('/api/role-field-sets'), api('/api/data/status'), api('/api/sync/status'), api('/api/health')
    ]);
    state.opportunities=ops.items||[];
    state.scheduleEvents=schedule.items||[];
    state.emails=emailMessages.items||[];
    state.emailSettings=emailSettings.settings||{};
    state.profile=profile.profile||{};
    state.experiences=exps.items||[];
    state.versions=versions.items||[];
    state.interviewQuestions=questions.items||[];
    state.roleFieldSets=fieldSets.items||[];
    state.dataStatus=dataStatus||{};
    state.syncStatus=syncStatus||{};
    state.health=health||{};
    state.latestVersion=state.latestVersion || state.versions[0] || null;
    const cvOk=!!health.careervault?.available;
    $('#aiBadge').textContent=`${cvOk?'经历已连接':'等待连接'} · ${health.ai_enabled?'智能增强已开启':'本地生成可用'}`;
    const cvText=cvOk
      ? '经历与项目已连接，生成简历前会根据岗位要求进行匹配。'
      : '经历和项目未连接；请先启动经历服务。';
    if($('#careerVaultState')) $('#careerVaultState').textContent=cvText;
    if($('#careerVaultProfileState')) $('#careerVaultProfileState').textContent=cvText;
    if($('#legacyChooserWrap')) $('#legacyChooserWrap').classList.toggle('hidden',cvOk);
    renderAll();
  }catch(e){notice(e.message,true);}
}

function renderAll(){renderDashboard();renderCalendar();renderEmail();renderMemo();renderProfile();renderPrivateProfile();renderExperiences();renderInterviewQuestions();renderRoleFieldSets();renderTargetOptions();renderExperienceChooser();renderVersions();renderDataStatus();renderSyncStatus();renderRecommendations();if(state.latestVersion)renderResumePreview(state.latestVersion);}

const EVENT_TYPE={application:'投递',written_test:'笔试',interview:'面试',deadline:'截止',follow_up:'跟进',other:'其他'};
const EVENT_CLASS={application:'event-application',written_test:'event-written-test',interview:'event-interview',deadline:'event-deadline',follow_up:'event-follow-up',other:'event-other'};
let calendarCursor=new Date(new Date().getFullYear(),new Date().getMonth(),1);
function localDate(date){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;}
function renderCalendar(){
  const grid=$('#calendarGrid');if(!grid)return;
  const year=calendarCursor.getFullYear(),month=calendarCursor.getMonth(),first=new Date(year,month,1),days=new Date(year,month+1,0).getDate(),offset=(first.getDay()+6)%7;
  $('#calendarMonth').textContent=`${year} 年 ${month+1} 月`;
  const names=['一','二','三','四','五','六','日'];let html=names.map(x=>`<div class="calendar-weekday">${x}</div>`).join('');
  for(let i=0;i<offset;i++)html+='<div class="calendar-day muted-day"></div>';
  for(let day=1;day<=days;day++){const key=localDate(new Date(year,month,day));const items=state.scheduleEvents.filter(x=>x.event_date===key);const today=key===localDate(new Date());html+=`<button class="calendar-day ${today?'today':''}" type="button" data-calendar-date="${key}"><span class="calendar-date">${day}</span>${items.slice(0,3).map(x=>`<span class="calendar-event ${EVENT_CLASS[x.event_type]||EVENT_CLASS.other}" title="${esc(x.title)}">${esc(x.event_time?`${x.event_time} `:'')}${esc(x.title)}</span>`).join('')}${items.length>3?`<span class="calendar-more">+${items.length-3} 条</span>`:''}</button>`;}
  grid.innerHTML=html;
  const upcoming=state.scheduleEvents.filter(x=>x.event_date>=localDate(new Date())).slice(0,5);
  $('#calendarUpcoming').innerHTML=`<div class="upcoming-head"><b>近期安排</b><span class="helper">${upcoming.length?`未来 ${upcoming.length} 条`:''}</span></div>${upcoming.length?upcoming.map(x=>`<div class="upcoming-item"><span class="event-dot ${EVENT_CLASS[x.event_type]||EVENT_CLASS.other}"></span><div><b>${esc(x.title)}</b><small>${esc(x.event_date)}${x.event_time?` · ${esc(x.event_time)}`:''}${x.company?` · ${esc(x.company)}`:''}</small></div>${x.source==='opportunity'?`<button class="link-button" type="button" data-edit-opportunity="${x.opportunity_id}">编辑岗位</button>`:`<button class="link-button" type="button" data-edit-schedule="${x.id}">编辑</button><button class="link-button danger-link" type="button" data-delete-schedule="${x.id}">删除</button>`}</div>`).join(''):'<div class="empty-state compact">还没有日程，点击“添加日程”记录下一次安排。</div>'}`;
}
function fillScheduleOpportunities(current=''){const select=$('#scheduleOpportunity');select.innerHTML='<option value="">不关联岗位</option>'+state.opportunities.map(x=>`<option value="${x.id}" ${String(x.id)===String(current)?'selected':''}>${esc(x.company||'待补充公司')} · ${esc(x.role||x.title||'岗位')}</option>`).join('');}
function openSchedule(item=null,date=''){const x=item||{};$('#scheduleId').value=x.id||'';$('#scheduleDialogTitle').textContent=item?'编辑日程':'添加日程';$('#scheduleType').value=x.event_type||'other';$('#scheduleTitle').value=x.title||'';$('#scheduleDate').value=x.event_date||date||localDate(new Date());$('#scheduleTime').value=x.event_time||'';$('#scheduleLocation').value=x.location||'';$('#scheduleNotes').value=x.notes||'';fillScheduleOpportunities(x.opportunity_id||'');$('#scheduleDialog').showModal();}
function closeSchedule(){if($('#scheduleDialog').open)$('#scheduleDialog').close();}

function renderEmail(){
  const s=state.emailSettings||{};if($('#emailHost')){$('#emailHost').value=s.imap_host||'';$('#emailPort').value=s.imap_port||993;$('#emailUsername').value=s.username||'';$('#emailFolder').value=s.folder||'INBOX';}if($('#emailConfiguredState'))$('#emailConfiguredState').textContent=s.imap_host&&s.username?`已配置：${s.username} · ${s.imap_host}`:'尚未配置邮箱，请先点击“邮箱配置”。';
  const pending=state.emails.filter(x=>x.status==='pending'), imported=state.emails.filter(x=>x.status==='imported'), ignored=state.emails.filter(x=>x.status==='ignored');
  if($('#emailCount'))$('#emailCount').textContent=`待确认 ${pending.length} · 已导入 ${imported.length} · 已忽略 ${ignored.length}`;
  if(!$('#emailList'))return;
  const visible=state.emailFilter==='all'?state.emails:state.emails.filter(x=>x.status===state.emailFilter);$('#emailList').innerHTML=visible.length?visible.map(x=>{const linked=x.company?` · ${esc(x.company)}${x.role?` / ${esc(x.role)}`:''}`:'';const status=x.status==='imported'?'<span class="email-status imported">已导入</span>':x.status==='ignored'?'<span class="email-status ignored">已忽略</span>':'<span class="email-status pending">待确认</span>';const selector=`<label class="email-link-label">${x.status==='imported'?'更新关联':'关联岗位'}<select data-email-opportunity="${x.id}"><option value="">不关联岗位</option>${state.opportunities.map(o=>`<option value="${o.id}" ${String(o.id)===String(x.opportunity_id||'')?'selected':''}>${esc(o.company||'待补充公司')} · ${esc(o.role||o.title||'岗位')}</option>`).join('')}</select>${x.status!=='ignored'?`<button class="link-button" type="button" data-link-email="${x.id}">保存</button>`:''}</label>`;return `<article class="email-card ${x.status==='imported'?'is-imported':''} ${x.status==='ignored'?'is-ignored':''}"><div class="email-select">${x.status==='pending'?`<input type="checkbox" data-email-choice="${x.id}" />`:''}</div><div class="email-main"><div class="email-head"><b>${esc(x.subject||'(无主题)')}</b><span>${status}${x.status==='pending'?` <button class="link-button danger-link" type="button" data-ignore-email="${x.id}">忽略</button>`:''}</span></div><div class="email-meta">${esc(x.received_at||'未知时间')} · ${esc(x.sender||'未知发件人')}${linked}</div><p>${esc(x.snippet||'（无正文摘要）')}</p>${x.status!=='ignored'?selector:''}</div></article>`;}).join(''):`<div class="empty-state compact">${state.emailFilter==='pending'?'还没有待确认邮件。':state.emailFilter==='imported'?'还没有已导入邮件。':state.emailFilter==='ignored'?'还没有已忽略邮件。':'还没有邮件记录。'}</div>`;
  $$('.email-filter').forEach(button=>button.classList.toggle('active',button.dataset.emailFilter===state.emailFilter));
  if($('#emailListTitle'))$('#emailListTitle').firstChild.textContent=state.emailFilter==='pending'?'待确认邮件 ':state.emailFilter==='imported'?'已导入邮件 ':state.emailFilter==='ignored'?'已忽略邮件 ':'全部邮件 ';
  $('#emailEmpty')?.classList.add('hidden');
}

function renderDashboard(){
  const jobs=state.opportunities;
  const count=status=>jobs.filter(x=>x.status===status).length;
  const pending=jobs.filter(x=>UNSUBMITTED_STATUSES.has(x.status)).length;
  [['#dashboardTotal',jobs.length],['#dashboardPreparing',count('preparing')],['#dashboardApplied',count('applied')],['#dashboardInterview',count('interview')],['#dashboardOffer',count('offer')]].forEach(([selector,value])=>{if($(selector))$(selector).textContent=value;});
  const recent=[...jobs].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||''))).slice(0,5);
  const recentBox=$('#dashboardRecentJobs');
  if(recentBox)recentBox.innerHTML=recent.length?recent.map(x=>`<button class="dashboard-job" type="button" data-dashboard-job="${x.id}"><span><b>${esc(x.company||'待补充公司')}</b><small>${esc(x.role||x.title||'待补充岗位')}${x.location?` · ${esc(x.location)}`:''}</small></span><em class="status-chip status-${esc(x.status||'inbox')}">${esc(STATUS[x.status]||STATUS.inbox)}</em></button>`).join(''):'<div class="empty-state compact">还没有岗位，先导入一个招聘链接。</div>';
  const taskBox=$('#dashboardTasks');
  if(taskBox){const missingApplied=jobs.filter(x=>SUBMITTED_STATUSES.has(x.status)&&!x.applied_at).length;const tasks=[];if(pending)tasks.push(`<button class="task-item" type="button" data-go-view="memo"><strong>${pending} 个岗位待处理</strong><span>补充信息或推进投递状态 →</span></button>`);if(missingApplied)tasks.push(`<button class="task-item" type="button" data-go-view="memo"><strong>${missingApplied} 个已投递岗位缺少投递时间</strong><span>请在岗位编辑中补充，日历才能准确记录 →</span></button>`);if(!state.health.careervault?.available)tasks.push('<button class="task-item" type="button" data-go-view="vault"><strong>经历和项目尚未连接</strong><span>连接后才能进行经历匹配和简历生成 →</span></button>');if(!tasks.length)tasks.push('<div class="empty-state compact">目前没有待处理事项，继续保持进度。</div>');taskBox.innerHTML=tasks.join('');}
}

// ---------- opportunities ----------
function memoRows(){
  const q=($('#memoSearch')?.value||'').trim().toLowerCase();
  const category=$('#memoCategoryFilter')?.value||'';
  const status=$('#memoStatusFilter')?.value||'';
  return state.opportunities.filter(x=>{
    if(state.memoScope==='unsubmitted'&&!UNSUBMITTED_STATUSES.has(x.status))return false;
    if(state.memoScope==='submitted'&&!SUBMITTED_STATUSES.has(x.status))return false;
    if(category&&x.job_category!==category)return false;
    if(status&&x.status!==status)return false;
    if(q&&!`${x.company||''} ${x.role||''} ${x.note||''} ${x.location||''} ${x.title||''}`.toLowerCase().includes(q))return false;
    return true;
  });
}
function statusOptions(current){return Object.entries(STATUS).map(([k,v])=>`<option value="${k}" ${current===k?'selected':''}>${v}</option>`).join('');}
function jobCategoryOptions(current){return Object.entries(JOB_CATEGORY).map(([k,v])=>`<option value="${k}" ${current===k?'selected':''}>${v}</option>`).join('');}
function renderMemo(){
  const rows=memoRows();
  if($('#memoCount')) $('#memoCount').textContent=`${rows.length} / ${state.opportunities.length}`;
  const counts={pending:0,preparing:0,submitted:0};
  state.opportunities.forEach(x=>{
    if(UNSUBMITTED_STATUSES.has(x.status)) counts.pending++;
    if(x.status==='preparing') counts.preparing++;
    if(SUBMITTED_STATUSES.has(x.status)) counts.submitted++;
  });
  if($('#summaryTotal')) $('#summaryTotal').textContent=state.opportunities.length;
  if($('#summaryPending')) $('#summaryPending').textContent=counts.pending;
  if($('#summaryPreparing')) $('#summaryPreparing').textContent=counts.preparing;
  if($('#summarySubmitted')) $('#summarySubmitted').textContent=counts.submitted;
  $('#memoList').innerHTML=rows.map(x=>`<article class="memo-card" data-id="${x.id}">
    <div><h3>${esc(x.company||'待补充公司')} · ${esc(x.role||x.title||'待补充岗位')}</h3>
    <div class="meta">${x.location?`<span>${esc(x.location)}</span>`:''}${x.applied_at?`<span>投递 ${esc(x.applied_at)}</span>`:''}${x.deadline?`<span>截止 ${esc(x.deadline)}</span>`:'<span>无明确截止时间</span>'}<span>${esc(STATUS[x.status]||'待判断')}</span><span>${esc(JOB_CATEGORY[x.job_category]||'未分类')}</span>${x.referral_code?`<span class="referral-chip">内推码：${esc(x.referral_code)}</span>`:''}</div>
      ${x.note?`<div class="memo-note">${esc(x.note)}</div>`:''}
    </div>
    <div class="memo-actions"><select data-action="job-category">${jobCategoryOptions(x.job_category)}</select><select data-action="status">${statusOptions(x.status)}</select>${x.source_url?`<a class="small-btn" href="${esc(x.source_url)}" target="_blank" rel="noopener">打开 ↗</a>`:'<span class="helper">无原链接</span>'}<button class="small-btn" data-action="edit">编辑</button><button class="small-btn danger" data-action="delete">删除</button></div>
  </article>`).join('');
  $('#memoEmpty').classList.toggle('hidden',rows.length>0);
}
function openMemoEditor(item){state.memoEditing=item;$('#memoEditId').value=item.id;$('#memoEditCompany').value=item.company||'';$('#memoEditRole').value=item.role||'';$('#memoEditCategory').value=item.job_category||'unclassified';$('#memoEditLocation').value=item.location||'';$('#memoEditDeadline').value=item.deadline||'';$('#memoEditAppliedAt').value=item.applied_at||'';$('#memoEditReferralCode').value=item.referral_code||'';$('#memoEditJd').value=item.jd_text||item.description||item.raw_text||'';$('#memoEditNote').value=item.note||'';$('#memoDialog').showModal();}
function closeMemoEditor(){if($('#memoDialog').open)$('#memoDialog').close();state.memoEditing=null;}

// ---------- legacy profile / experiences ----------
function renderProfile(){if(!$('#profileForm'))return;for(const el of [...$('#profileForm').elements])if(el.name)el.value=state.profile[el.name]||'';}
function renderPrivateProfile(){const form=$('#privateProfileForm');if(!form)return;$$('[data-private-field]',form).forEach(el=>{el.value=state.profile[el.dataset.privateField]||'';});const photo=state.profile.photo_path;$('#privatePhotoState').textContent=photo?`已保存：${photo}`:'仅保存到本机，不会自动上传到招聘网站。';}
function renderExperiences(){
  const filter=$('#experienceFilter')?.value||'';
  const rows=state.experiences.filter(x=>!filter||x.category===filter);
  $('#experienceList').innerHTML=rows.map(x=>`<article class="experience-card" data-id="${x.id}"><div><div class="meta"><span class="tag">${esc(CATEGORY[x.category]||x.category)}</span>${x.start_date||x.end_date?`<span>${esc(x.start_date||'')} ${x.end_date?'→ '+esc(x.end_date):''}</span>`:''}</div><h3>${esc(x.organization?`${x.organization} · `:'')}${esc(x.title||'未命名经历')}</h3>${x.description?`<p>${esc(x.description)}</p>`:''}</div><div class="memo-actions"><button class="small-btn" data-action="edit-exp">编辑</button><button class="small-btn danger" data-action="delete-exp">删除</button></div></article>`).join('');
  $('#experienceEmpty').classList.toggle('hidden',rows.length>0);
}
function openExperience(item=null){$('#experienceId').value=item?.id||'';$('#experienceDialogTitle').textContent=item?'编辑经历':'添加经历';$('#expCategory').value=item?.category||'project';$('#expTitle').value=item?.title||'';$('#expOrganization').value=item?.organization||'';$('#expLocation').value=item?.location||'';$('#expStart').value=item?.start_date||'';$('#expEnd').value=item?.end_date||'';$('#expDescription').value=item?.description||'';$('#expHighlights').value=(item?.highlights||[]).join('\n');$('#expTags').value=(item?.tags||[]).join(', ');$('#experienceDialog').showModal();}
function closeExperience(){if($('#experienceDialog').open)$('#experienceDialog').close();}
function renderExperienceChooser(){
  const box=$('#resumeExperienceChooser');
  if(!state.experiences.length){box.innerHTML='<div class="helper" style="padding:10px">暂时没有可选经历。连接经历和项目后会自动提供匹配推荐。</div>';return;}
  box.innerHTML=state.experiences.map(x=>`<label><input type="checkbox" data-exp-choice value="${x.id}" /><span><b>${esc(CATEGORY[x.category]||x.category)} · ${esc(x.title||'未命名')}</b>${x.organization?`<br><span class="helper">${esc(x.organization)}</span>`:''}</span></label>`).join('');
}

// ---------- resume / CareerVault selection ----------
function renderTargetOptions(){
  const select=$('#targetOpportunity'),current=select.value;
  select.innerHTML='<option value="">不绑定职位，手动填写</option>'+state.opportunities.map(x=>`<option value="${x.id}">${esc(x.company||'待补充')} · ${esc(x.role||x.title||'岗位')}</option>`).join('');
  if([...select.options].some(o=>o.value===current))select.value=current;
}
function targetPayload(){return {opportunity_id:Number($('#targetOpportunity').value)||null,target_company:$('#targetCompany').value.trim(),target_role:$('#targetRole').value.trim(),jd:$('#targetJd').value.trim()};}
function targetSignature(){const p=targetPayload();return JSON.stringify([p.opportunity_id,p.target_company,p.target_role,p.jd]);}
function invalidateRecommendations(){if(state.recommendationSignature!==targetSignature()){state.recommendations=[];state.recommendationDefaultIds=[];state.recommendationSignature='';renderRecommendations();}}
function selectedRecommendationIds(){return $$('[data-cv-choice]').filter(x=>x.checked).map(x=>x.value);}
function scoreClass(score){return score<=0?'zero':score<35?'low':'';}
function renderRecommendations(){
  const box=$('#careerRecommendations');if(!box)return;
  const toolbar=$('#recommendationToolbar');
  if(state.recommendationsLoading){box.innerHTML='<div class="recommendation-empty">正在读取经历并分析 JD…</div>';toolbar.classList.add('hidden');return;}
  if(!state.recommendations.length){box.innerHTML='<div class="recommendation-empty">还没有分析当前 JD。</div>';toolbar.classList.add('hidden');$('#recommendationState').textContent='选择岗位或填写 JD 后点击“分析匹配”。';return;}
  toolbar.classList.remove('hidden');
  const selectedCount=state.recommendations.filter(x=>x.selected).length;
  $('#recommendationSummary').textContent=`共 ${state.recommendations.length} 条 Resume Ready 经历 · 当前选择 ${selectedCount} 条`;
  $('#recommendationState').textContent='排名只是建议；最终进入简历的经历由你勾选决定。';
  box.innerHTML=state.recommendations.map(x=>{
    const score=Number(x.match_percent||0);const checked=x.selected?'checked':'';const reasons=(x.match_reasons||[]).map(r=>`<span class="reason-chip">${esc(r)}</span>`).join('');
    const meta=[CATEGORY[x.category]||x.category,x.organization,x.start_date&&x.end_date?`${x.start_date} → ${x.end_date}`:x.start_date||x.end_date].filter(Boolean).join(' · ');
    return `<label class="recommendation-card ${x.selected?'is-selected':''}" data-cv-card="${esc(x.id)}"><input type="checkbox" data-cv-choice value="${esc(x.id)}" ${checked}/><div><div class="recommendation-title">${esc(x.title||'未命名经历')}</div><div class="recommendation-meta">${esc(meta)}</div><div class="reason-list">${reasons}</div></div><div class="match-score ${scoreClass(score)}">${score}%</div></label>`;
  }).join('');
}
async function loadRecommendations({quiet=false}={}){
  if(!state.health.careervault?.available){if(!quiet)notice('经历和项目未连接，请先启动经历服务。',true);return false;}
  if(state.recommendationsLoading)return false;
  state.recommendationsLoading=true;renderRecommendations();
  try{
    const data=await api('/api/careervault/recommendations',{method:'POST',body:JSON.stringify(targetPayload())});
    const defaults=new Set(data.selected_default_ids||[]);
    state.recommendations=(data.items||[]).map(x=>({...x,selected:defaults.has(String(x.id))}));
    state.recommendationDefaultIds=[...defaults];
    state.recommendationSignature=targetSignature();
    if(!quiet)notice(`已分析 ${state.recommendations.length} 条匹配经历。`);
    return true;
  }catch(e){state.recommendations=[];state.recommendationDefaultIds=[];state.recommendationSignature='';if(!quiet)notice(e.message,true);return false;}
  finally{state.recommendationsLoading=false;renderRecommendations();}
}
function scheduleRecommendationAnalysis(){clearTimeout(recommendationTimer);invalidateRecommendations();const p=targetPayload();if(!state.health.careervault?.available)return;if(!p.opportunity_id&&p.jd.length<20)return;recommendationTimer=setTimeout(()=>loadRecommendations({quiet:true}),700);}

function renderVersions(){
  $('#versionList').innerHTML=state.versions.map(v=>{const r=v.resume||{};const source=r.source==='careervault'?'已确认经历':'本地资料';return `<article class="version-card" data-id="${v.id}"><div><b>${esc(v.name||'通用简历')}</b> <span class="source-badge ${source==='本地资料'?'legacy':''}">${source}</span><br><span>${esc(v.created_at||'')}${v.target_company||v.target_role?` · ${esc([v.target_company,v.target_role].filter(Boolean).join(' · '))}`:''}</span></div><div class="memo-actions"><button class="small-btn" data-action="preview-version">预览</button><a class="small-btn primary-link" href="/api/resume-versions/${v.id}/pdf">下载 PDF</a><a class="small-btn" href="/api/resume-versions/${v.id}/docx">DOCX</a><button class="small-btn danger" data-action="delete-version">删除</button></div></article>`;}).join('')||'<div class="empty-state">还没有生成过简历版本。</div>';
}
function renderResumePreview(version){
  state.latestVersion=version;const r=version.resume||{};const p=r.profile_snapshot||state.profile||{};
  const ids=r.selected_careervault_ids||[];
  const sourceNote=`<div class="resume-source-note"><b>本次使用：</b>${r.source==='careervault'?'已确认的经历与项目':'本地经历资料'}${r.selection_mode?` · ${esc(r.selection_mode)}`:''}${ids.length?`<br><b>已选经历：</b>${ids.map(esc).join('、')}`:''}</div>`;
  const sections=(r.sections||[]).map(sec=>`<section class="resume-section"><h3>${esc(sec.title||'')}</h3>${(sec.items||[]).map(item=>`<div class="resume-item"><div class="resume-item-head"><b>${esc([item.organization,item.title].filter(Boolean).join(' · '))}</b><span>${esc([item.date,item.location].filter(Boolean).join(' · '))}</span></div>${(item.bullets||[]).length?`<ul>${item.bullets.map(b=>`<li>${esc(b)}</li>`).join('')}</ul>`:''}</div>`).join('')}</section>`).join('');
  const contact=[p.phone,p.email,p.current_city,p.portfolio_url||p.website].filter(Boolean).join(' | ');
  const headline=version.target_role||r.headline||'';
  const photo=p.photo_path||state.profile.photo_path?'<img class="resume-preview-photo" src="/api/profile/photo" alt="证件照">':'';
  $('#resumePreview').classList.remove('empty-preview');
  $('#resumePreview').innerHTML=`${sourceNote}<div class="resume-preview-heading"><div><h2>${esc(p.name||'个人简历')}</h2>${contact?`<div class="contact">${esc(contact)}</div>`:''}</div>${photo}</div>${headline?`<div class="headline">${esc(headline)}</div>`:''}${r.summary?`<p class="summary">${esc(r.summary)}</p>`:''}${sections}${(r.skills||[]).length?`<section class="resume-section"><h3>技能</h3><p>${esc(r.skills.join('、'))}</p></section>`:''}`;
  $('#previewActions').innerHTML=`<a class="small-btn primary-link" href="/api/resume-versions/${version.id}/pdf">下载 PDF</a><a class="small-btn" href="/api/resume-versions/${version.id}/docx">下载 DOCX</a><button class="small-btn danger" type="button" data-preview-delete="${version.id}">删除此版本</button>`;
}
function renderInterviewQuestions(){
  const list=$('#interviewQuestionList');if(!list)return;
  const role=$('#interviewRoleFilter')?.value||'',type=$('#interviewTypeFilter')?.value||'',source=$('#interviewSourceFilter')?.value||'';
  const roles=[...new Set([...state.interviewQuestions.map(x=>x.role_category).filter(Boolean),...state.opportunities.map(x=>x.role).filter(Boolean)])];
  const select=$('#interviewRoleFilter'),current=select.value;select.innerHTML='<option value="">全部岗位类别</option>'+roles.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(roles.includes(current))select.value=current;
  const rows=state.interviewQuestions.filter(x=>(!role||x.role_category===role)&&(!type||x.question_type===type)&&(!source||x.source_type===source));
  list.innerHTML=rows.map(x=>`<article class="interview-question-card" data-id="${x.id}"><div class="interview-question-head"><div><span class="tag">${x.question_type==='written_test'?'笔试':'面试'}</span><span class="tag">${x.source_type==='network'?'网络题库':'亲身经历'}</span>${x.role_category?`<span class="tag">${esc(x.role_category)}</span>`:''}${x.company?`<span class="helper">${esc(x.company)}</span>`:''}</div><span class="helper">${esc(x.event_date||'')}</span></div><h3>${esc(x.question)}</h3>${x.answer?`<div class="question-block"><b>回答 / 参考答案</b><p>${esc(x.answer)}</p></div>`:''}${x.feeling?`<div class="question-block feeling"><b>复盘感受</b><p>${esc(x.feeling)}</p></div>`:''}<div class="interview-question-foot"><div class="tag-list">${(x.tags||[]).map(t=>`<span>${esc(t)}</span>`).join('')}</div><div class="memo-actions"><button class="small-btn" data-action="edit-question">编辑</button><button class="small-btn danger" data-action="delete-question">删除</button></div></div></article>`).join('');
  $('#interviewQuestionEmpty').classList.toggle('hidden',rows.length>0);
}
function openInterviewQuestion(item=null){const x=item||{};$('#interviewQuestionId').value=x.id||'';$('#interviewQuestionDialogTitle').textContent=item?'编辑题目':'记录笔面试题目';$('#interviewQuestionType').value=x.question_type||'interview';$('#interviewQuestionSource').value=x.source_type||'personal';$('#interviewQuestionRole').value=x.role_category||'';$('#interviewQuestionCompany').value=x.company||'';$('#interviewQuestionDate').value=x.event_date||localDate(new Date());$('#interviewQuestionText').value=x.question||'';$('#interviewQuestionAnswer').value=x.answer||'';$('#interviewQuestionFeeling').value=x.feeling||'';$('#interviewQuestionTags').value=(x.tags||[]).join(', ');const select=$('#interviewQuestionOpportunity');select.innerHTML='<option value="">不关联岗位</option>'+state.opportunities.map(o=>`<option value="${o.id}" ${String(o.id)===String(x.opportunity_id||'')?'selected':''}>${esc(o.company||'待补充公司')} · ${esc(o.role||o.title||'岗位')}</option>`).join('');$('#interviewQuestionDialog').showModal();}
function renderRoleFieldSets(){const list=$('#roleFieldSetList');if(!list)return;list.innerHTML=state.roleFieldSets.map(x=>`<article class="role-field-set-card" data-id="${x.id}"><div class="interview-question-head"><div><span class="tag">${esc(x.role_category)}</span><b>${esc(x.title||'常用字段')}</b></div></div>${x.self_evaluation?`<p><b>自我评价：</b>${esc(x.self_evaluation)}</p>`:''}${x.strengths?`<p><b>个人优势：</b>${esc(x.strengths)}</p>`:''}${(x.skills||[]).length?`<div class="tag-list">${x.skills.map(s=>`<span>${esc(s)}</span>`).join('')}</div>`:''}<div class="memo-actions"><button class="small-btn" data-action="edit-field-set">编辑</button><button class="small-btn danger" data-action="delete-field-set">删除</button></div></article>`).join('')||'<div class="empty-state compact">还没有岗位常用字段，先按岗位类别建立一组。</div>';}
function openRoleFieldSet(item=null){const x=item||{};$('#roleFieldSetId').value=x.id||'';$('#roleFieldSetDialogTitle').textContent=item?'编辑岗位常用字段':'新建岗位常用字段';$('#roleFieldSetRole').value=x.role_category||'';$('#roleFieldSetTitle').value=x.title||'';$('#roleFieldSetSelfEvaluation').value=x.self_evaluation||'';$('#roleFieldSetStrengths').value=x.strengths||'';$('#roleFieldSetSkills').value=(x.skills||[]).join('\n');$('#roleFieldSetAnswers').value=Object.entries(x.common_answers||{}).map(([k,v])=>`${k}：${v}`).join('\n');$('#roleFieldSetNotes').value=x.notes||'';$('#roleFieldSetDialog').showModal();}
function renderDataStatus(){const d=state.dataStatus||{};$('#dataDbPath').textContent=d.db_path||'未知';$('#dataCounts').textContent=`岗位 ${d.opportunities||0} · 经历 ${d.experiences||0} · 简历版本 ${d.resume_versions||0} · 备份 ${d.backup_count||0}`;}
function renderSyncStatus(){const s=state.syncStatus||{};const badge=$('#syncStateBadge');const text=$('#syncStateText');if(!badge||!text)return;if(s.encryption_available===false){badge.textContent='需安装依赖';text.textContent='同步加密依赖未安装，请在 JobPilot 目录运行 install.bat；不影响其他功能。';}else{badge.textContent=s.configured?(s.pending_remote?'有待确认更新':'已配置'):'未配置';text.textContent=!s.configured?'配置私有仓库地址和同步口令后即可使用。':s.pending_remote?'检测到远程更新，请先检查并确认后再接受。':`上次检查：${s.last_checked_at||'尚未检查'} · 上次提交：${s.last_sync_at||'尚未提交'}${s.last_error?' · '+s.last_error:''}`;}$('#syncAcceptBtn').disabled=!s.pending_remote;$('#syncRollbackBtn').disabled=!s.rollback_available;if(s.remote_url)$('#syncRemoteUrl').value=s.remote_url;if(s.branch)$('#syncBranch').value=s.branch;$('#syncAutoStart').checked=s.auto_start_check!==false;$('#syncAutoClose').checked=s.auto_close_sync!==false;}

// ---------- navigation ----------
const titles=UI_TEXT.pageTitles;
const subtitles={vault:'统一管理项目、实习、获奖、专利软著和校园经历。'};
let vaultView='experiences';
function goView(view){$$('.nav').forEach(x=>x.classList.toggle('active',x.dataset.view===view));$$('.view').forEach(x=>x.classList.toggle('active-view',x.id===`view-${view}`));$('#viewTitle').textContent=titles[view]||'';$('#viewSubtitle').textContent=subtitles[view]||'集中查看岗位进展、待办事项和简历准备情况。';if(view==='vault'){vaultView='experiences';$$('[data-vault-view]').forEach(x=>x.classList.toggle('active',x.dataset.vaultView===vaultView));sendVaultView(vaultView);}}
function sendVaultView(view){const frame=$('#careerVaultFrame'),panel=$('#commonFieldsPanel');if(!frame)return;vaultView=view;const fields=view==='fields';frame.classList.toggle('hidden',fields);panel?.classList.toggle('hidden',!fields);if(!fields)frame.contentWindow?.postMessage({type:'careeros-vault-view',view},'*');}
function reloadCareerVaultFrame(){const frame=$('#careerVaultFrame');if(!frame)return;frame.src=`http://127.0.0.1:8766/?embedded=1&v=${Date.now()}`;}
$$('.nav').forEach(btn=>btn.addEventListener('click',()=>goView(btn.dataset.view)));
document.addEventListener('click',e=>{const go=e.target.closest('[data-go-view]');if(go)goView(go.dataset.goView);const job=e.target.closest('[data-dashboard-job]');if(job){goView('memo');const id=Number(job.dataset.dashboardJob);const item=state.opportunities.find(x=>x.id===id);if(item){$('#memoSearch').value=item.company||item.role||'';renderMemo();}}});
$('#refreshBtn').addEventListener('click',()=>{loadAll();reloadCareerVaultFrame()});$('#refreshCareerVault').addEventListener('click',()=>{loadAll();reloadCareerVaultFrame()});
$('#careerVaultFrame').addEventListener('load',()=>sendVaultView(vaultView));
$$('[data-vault-view]').forEach(btn=>btn.addEventListener('click',()=>{$$('[data-vault-view]').forEach(x=>x.classList.toggle('active',x===btn));sendVaultView(btn.dataset.vaultView);}));
function openVaultAction(type){const experienceTab=$('[data-vault-view="experiences"]');$$('[data-vault-view]').forEach(button=>button.classList.toggle('active',button===experienceTab));sendVaultView('experiences');setTimeout(()=>$('#careerVaultFrame').contentWindow?.postMessage({type},'*'),80)}
$('#vaultManageCategories').addEventListener('click',()=>openVaultAction('careeros-vault-manage-categories'));
$('#vaultQuickAdd').addEventListener('click',()=>openVaultAction('careeros-vault-new-experience'));
$('#careerAssetCreateClose').addEventListener('click',()=>$('#careerAssetCreateDialog').close());
$('#careerAssetCreateCancel').addEventListener('click',()=>$('#careerAssetCreateDialog').close());
$('#careerAssetCreateForm').addEventListener('submit',async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{const res=await fetch('http://127.0.0.1:8766/api/experiences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:$('#careerAssetType').value,title:$('#careerAssetTitle').value.trim(),organization:$('#careerAssetOrganization').value.trim(),role:$('#careerAssetRole').value.trim(),start:$('#careerAssetStart').value.trim(),end:$('#careerAssetEnd').value.trim(),summary:$('#careerAssetSummary').value.trim(),status:'active',resume_ready:false})});const data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||'创建经历失败');$('#careerAssetCreateDialog').close();$('#careerAssetCreateForm').reset();notice('经历记录已创建，已打开详情，可继续编辑并上传佐证文件。');sendVaultView('experiences');const frame=$('#careerVaultFrame');setTimeout(()=>frame.contentWindow?.postMessage({type:'careeros-vault-open-experience',id:data.id},'*'),80);}catch(err){notice(err.message,true);}finally{b.disabled=false;}});

// ---------- opportunity events ----------
$$('.mode[data-mode]').forEach(btn=>btn.addEventListener('click',()=>{$$('.mode[data-mode]').forEach(x=>x.classList.remove('active'));btn.classList.add('active');$('#urlForm').classList.toggle('hidden',btn.dataset.mode!=='url');$('#textForm').classList.toggle('hidden',btn.dataset.mode!=='text');}));
$('#openJobImportBtn').addEventListener('click',()=>$('#jobImportDialog').showModal());$('#jobImportClose').addEventListener('click',()=>$('#jobImportDialog').close());
$$('[data-memo-scope]').forEach(btn=>btn.addEventListener('click',()=>{state.memoScope=btn.dataset.memoScope;$$('[data-memo-scope]').forEach(x=>x.classList.toggle('active',x===btn));renderMemo();}));
$('#memoSearch').addEventListener('input',renderMemo);$('#memoCategoryFilter').addEventListener('change',renderMemo);$('#memoStatusFilter').addEventListener('change',renderMemo);
$('#clearMemoFilters').addEventListener('click',()=>{$('#memoSearch').value='';$('#memoCategoryFilter').value='';$('#memoStatusFilter').value='';state.memoScope='all';$$('[data-memo-scope]').forEach(x=>x.classList.toggle('active',x.dataset.memoScope==='all'));renderMemo();});
$('#urlForm').addEventListener('submit',async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{await api('/api/opportunities/import-url',{method:'POST',body:JSON.stringify({url:$('#urlInput').value.trim()})});$('#urlInput').value='';$('#jobImportDialog').close();notice('职位已导入列表。');await loadAll();}catch(err){notice(err.message,true);}finally{b.disabled=false;}});
$('#textForm').addEventListener('submit',async e=>{e.preventDefault();const text=$('#textInput').value.trim();if(text.length<10)return notice('请输入至少 10 个字符的职位信息。',true);const b=e.submitter;b.disabled=true;try{await api('/api/opportunities/import-text',{method:'POST',body:JSON.stringify({text})});$('#textInput').value='';$('#jobImportDialog').close();notice('职位信息已导入列表。');await loadAll();}catch(err){notice(err.message,true);}finally{b.disabled=false;}});
$('#memoList').addEventListener('change',async e=>{const action=e.target.dataset.action;if(!action)return;const id=Number(e.target.closest('.memo-card').dataset.id);try{if(action==='status')await api(`/api/opportunities/${id}/status`,{method:'POST',body:JSON.stringify({status:e.target.value})});if(action==='job-category')await api(`/api/opportunities/${id}/category`,{method:'POST',body:JSON.stringify({category:e.target.value})});await loadAll();}catch(err){notice(err.message,true);}});
$('#memoList').addEventListener('click',async e=>{const action=e.target.dataset.action;if(!action)return;const card=e.target.closest('.memo-card');if(!card)return;const id=Number(card.dataset.id),item=state.opportunities.find(x=>x.id===id);if(action==='edit'&&item)openMemoEditor(item);if(action==='delete'&&confirm('从职位列表中删除这条记录？')){try{await api(`/api/opportunities/${id}`,{method:'DELETE'});await loadAll();}catch(err){notice(err.message,true);}}});
$('#memoEditClose').addEventListener('click',closeMemoEditor);$('#memoEditCancel').addEventListener('click',closeMemoEditor);
$('#memoEditForm').addEventListener('submit',async e=>{e.preventDefault();const item=state.memoEditing;if(!item)return;const patch={company:$('#memoEditCompany').value.trim(),role:$('#memoEditRole').value.trim(),location:$('#memoEditLocation').value.trim(),deadline:$('#memoEditDeadline').value.trim(),applied_at:$('#memoEditAppliedAt').value.trim(),referral_code:$('#memoEditReferralCode').value.trim(),jd_text:$('#memoEditJd').value.trim(),note:$('#memoEditNote').value.trim()};try{await api(`/api/opportunities/${item.id}/edit`,{method:'POST',body:JSON.stringify(patch)});const cat=$('#memoEditCategory').value;if(cat!==(item.job_category||'unclassified'))await api(`/api/opportunities/${item.id}/category`,{method:'POST',body:JSON.stringify({category:cat})});closeMemoEditor();notice('职位信息已更新。');await loadAll();}catch(err){notice(err.message,true);}});

// ---------- legacy events ----------
$('#saveProfileBtn').addEventListener('click',async()=>{const payload={};for(const el of [...$('#profileForm').elements])if(el.name)payload[el.name]=el.value.trim();try{await api('/api/profile',{method:'PATCH',body:JSON.stringify(payload)});notice('基本资料已保存。');await loadAll();}catch(e){notice(e.message,true);}});
$('#privateProfileForm').addEventListener('submit',async e=>{e.preventDefault();const payload={};$$('[data-private-field]',e.currentTarget).forEach(el=>payload[el.dataset.privateField]=el.value.trim());try{await api('/api/profile',{method:'PATCH',body:JSON.stringify(payload)});$('#privateProfileState').textContent='✓ 已保存到本机';await loadAll();}catch(err){$('#privateProfileState').textContent='保存失败：'+err.message;}});
$('#privatePhotoFile').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;const fd=new FormData();fd.append('file',file);$('#privatePhotoState').textContent='证件照保存中…';try{const res=await fetch('/api/profile/photo',{method:'POST',body:fd});const data=await res.json();if(!res.ok)throw new Error(data.detail||'上传失败');state.profile=data.profile||state.profile;renderPrivateProfile();}catch(err){$('#privatePhotoState').textContent='保存失败：'+err.message;}});
$('#resumeImportForm').addEventListener('submit',async e=>{e.preventDefault();const file=$('#resumeFile').files[0];if(!file)return;const b=e.submitter;b.disabled=true;try{const fd=new FormData();fd.append('file',file);const res=await fetch('/api/resume/import',{method:'POST',body:fd});const data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||'导入失败');notice(`已导入旧版本地经历 ${data.count} 条。`);$('#resumeFile').value='';await loadAll();}catch(err){notice(err.message,true);}finally{b.disabled=false;}});
$('#experienceFilter').addEventListener('change',renderExperiences);$('#addExperienceBtn').addEventListener('click',()=>openExperience());$('#experienceClose').addEventListener('click',closeExperience);$('#experienceCancel').addEventListener('click',closeExperience);
$('#experienceForm').addEventListener('submit',async e=>{e.preventDefault();const id=$('#experienceId').value;const payload={category:$('#expCategory').value,title:$('#expTitle').value.trim(),organization:$('#expOrganization').value.trim(),location:$('#expLocation').value.trim(),start_date:$('#expStart').value.trim(),end_date:$('#expEnd').value.trim(),description:$('#expDescription').value.trim(),highlights:$('#expHighlights').value.split('\n').map(x=>x.trim()).filter(Boolean),tags:$('#expTags').value.split(/[,，]/).map(x=>x.trim()).filter(Boolean)};try{await api(id?`/api/experiences/${id}`:'/api/experiences',{method:id?'PATCH':'POST',body:JSON.stringify(payload)});closeExperience();await loadAll();}catch(err){notice(err.message,true);}});
$('#experienceList').addEventListener('click',async e=>{const action=e.target.dataset.action;if(!action)return;const id=Number(e.target.closest('.experience-card').dataset.id),item=state.experiences.find(x=>x.id===id);if(action==='edit-exp')openExperience(item);if(action==='delete-exp'&&confirm('删除这条经历？')){await api(`/api/experiences/${id}`,{method:'DELETE'});await loadAll();}});

$('#addInterviewQuestionBtn').addEventListener('click',()=>openInterviewQuestion());$('#interviewQuestionClose').addEventListener('click',()=>$('#interviewQuestionDialog').close());$('#interviewQuestionCancel').addEventListener('click',()=>$('#interviewQuestionDialog').close());$('#interviewRoleFilter').addEventListener('change',renderInterviewQuestions);$('#interviewTypeFilter').addEventListener('change',renderInterviewQuestions);$('#interviewSourceFilter').addEventListener('change',renderInterviewQuestions);
$('#interviewQuestionForm').addEventListener('submit',async e=>{e.preventDefault();const id=$('#interviewQuestionId').value;const payload={question_type:$('#interviewQuestionType').value,source_type:$('#interviewQuestionSource').value,role_category:$('#interviewQuestionRole').value.trim(),company:$('#interviewQuestionCompany').value.trim(),event_date:$('#interviewQuestionDate').value,opportunity_id:Number($('#interviewQuestionOpportunity').value)||null,question:$('#interviewQuestionText').value.trim(),answer:$('#interviewQuestionAnswer').value.trim(),feeling:$('#interviewQuestionFeeling').value.trim(),tags:$('#interviewQuestionTags').value.split(/[,，]/).map(x=>x.trim()).filter(Boolean)};try{await api(id?`/api/interview-questions/${id}`:'/api/interview-questions',{method:id?'PATCH':'POST',body:JSON.stringify(payload)});$('#interviewQuestionDialog').close();notice(id?'题目已更新。':'题目已保存。');await loadAll();}catch(err){notice(err.message,true);}});
$('#interviewQuestionList').addEventListener('click',async e=>{const action=e.target.dataset.action;if(!action)return;const id=Number(e.target.closest('.interview-question-card').dataset.id),item=state.interviewQuestions.find(x=>x.id===id);if(action==='edit-question')openInterviewQuestion(item);if(action==='delete-question'&&confirm('删除这道题目？')){await api(`/api/interview-questions/${id}`,{method:'DELETE'});await loadAll();}});

$('#addRoleFieldSetBtn').addEventListener('click',()=>openRoleFieldSet());$('#roleFieldSetClose').addEventListener('click',()=>$('#roleFieldSetDialog').close());$('#roleFieldSetCancel').addEventListener('click',()=>$('#roleFieldSetDialog').close());
$('#roleFieldSetForm').addEventListener('submit',async e=>{e.preventDefault();const id=$('#roleFieldSetId').value;const answers={};$('#roleFieldSetAnswers').value.split('\n').map(x=>x.trim()).filter(Boolean).forEach(line=>{const i=line.search(/[:：]/);if(i>0)answers[line.slice(0,i).trim()]=line.slice(i+1).trim();});const payload={role_category:$('#roleFieldSetRole').value.trim(),title:$('#roleFieldSetTitle').value.trim(),self_evaluation:$('#roleFieldSetSelfEvaluation').value.trim(),strengths:$('#roleFieldSetStrengths').value.trim(),skills:$('#roleFieldSetSkills').value.split('\n').map(x=>x.trim()).filter(Boolean),common_answers:answers,notes:$('#roleFieldSetNotes').value.trim()};try{await api(id?`/api/role-field-sets/${id}`:'/api/role-field-sets',{method:id?'PATCH':'POST',body:JSON.stringify(payload)});$('#roleFieldSetDialog').close();notice(id?'岗位常用字段已更新。':'岗位常用字段已保存。');await loadAll();}catch(err){notice(err.message,true);}});
$('#roleFieldSetList').addEventListener('click',async e=>{const action=e.target.dataset.action;if(!action)return;const id=Number(e.target.closest('.role-field-set-card').dataset.id),item=state.roleFieldSets.find(x=>x.id===id);if(action==='edit-field-set')openRoleFieldSet(item);if(action==='delete-field-set'&&confirm('删除这组岗位常用字段？')){await api(`/api/role-field-sets/${id}`,{method:'DELETE'});await loadAll();}});

// ---------- recommendation / resume events ----------
$('#targetOpportunity').addEventListener('change',()=>{const id=Number($('#targetOpportunity').value||0);const item=state.opportunities.find(x=>x.id===id);if(item){$('#targetCompany').value=item.company||'';$('#targetRole').value=item.role||'';$('#targetJd').value=item.jd_text||item.description||item.raw_text||'';}invalidateRecommendations();scheduleRecommendationAnalysis();});
['targetCompany','targetRole','targetJd'].forEach(id=>$('#'+id).addEventListener('input',scheduleRecommendationAnalysis));
$('#analyzeCareerVaultBtn').addEventListener('click',()=>loadRecommendations());
$('#careerRecommendations').addEventListener('change',e=>{if(!e.target.matches('[data-cv-choice]'))return;const item=state.recommendations.find(x=>String(x.id)===e.target.value);if(item)item.selected=e.target.checked;renderRecommendations();});
$('#selectRecommendedBtn').addEventListener('click',()=>{const defaults=new Set(state.recommendationDefaultIds);state.recommendations.forEach(x=>x.selected=defaults.has(String(x.id)));renderRecommendations();});
$('#clearRecommendedBtn').addEventListener('click',()=>{state.recommendations.forEach(x=>x.selected=false);renderRecommendations();});
$('#toggleAllExperiences').addEventListener('click',()=>{const boxes=$$('[data-exp-choice]');const all=boxes.length&&boxes.every(x=>x.checked);boxes.forEach(x=>x.checked=!all);});
$('#resumeGenerateForm').addEventListener('submit',async e=>{
  e.preventDefault();const b=e.submitter;const cvOk=!!state.health.careervault?.available;let payload=targetPayload();
  if(cvOk){
    if(state.recommendationSignature!==targetSignature()||!state.recommendations.length){const ok=await loadRecommendations();if(!ok)return;}
    const ids=selectedRecommendationIds();if(!ids.length)return notice('请至少勾选一条匹配经历。',true);
    payload.careervault_experience_ids=ids;payload.experience_ids=[];
  }else{
    const ids=$$('[data-exp-choice]').filter(x=>x.checked).map(x=>Number(x.value));if(!ids.length)return notice('经历和项目未连接；如需继续生成，请先选择已有经历。',true);payload.experience_ids=ids;
  }
  b.disabled=true;b.textContent=cvOk?'正在生成岗位简历…':'正在生成简历…';
  try{const data=await api('/api/resume/generate',{method:'POST',body:JSON.stringify(payload)});notice(`岗位简历已生成 · ${data.selection_mode||''}`);state.latestVersion=data.item;await loadAll();renderResumePreview(data.item);}catch(err){notice(err.message,true);}finally{b.disabled=false;b.textContent='生成岗位简历';}
});
async function deleteResumeVersion(id){if(!confirm('确定删除这份简历版本吗？已下载到本地的 DOCX 不会受到影响。'))return;try{await api(`/api/resume-versions/${id}`,{method:'DELETE'});if(String(state.latestVersion?.id)===String(id))state.latestVersion=null;notice('简历版本已删除。');await loadAll();}catch(err){notice(err.message,true);}}
$('#versionList').addEventListener('click',e=>{const action=e.target.dataset.action;if(action==='preview-version'){const id=Number(e.target.closest('.version-card').dataset.id);const v=state.versions.find(x=>x.id===id);if(v)renderResumePreview(v);}if(action==='delete-version')deleteResumeVersion(Number(e.target.closest('.version-card').dataset.id));});
$('#previewActions').addEventListener('click',e=>{if(e.target.dataset.previewDelete)deleteResumeVersion(Number(e.target.dataset.previewDelete));});

// ---------- application calendar ----------
$('#calendarPrev').addEventListener('click',()=>{calendarCursor.setMonth(calendarCursor.getMonth()-1);renderCalendar();});
$('#calendarNext').addEventListener('click',()=>{calendarCursor.setMonth(calendarCursor.getMonth()+1);renderCalendar();});
$('#addScheduleBtn').addEventListener('click',()=>openSchedule());
$('#scheduleClose').addEventListener('click',closeSchedule);$('#scheduleCancel').addEventListener('click',closeSchedule);
$('#calendarGrid').addEventListener('click',e=>{const day=e.target.closest('[data-calendar-date]');if(day)openSchedule(null,day.dataset.calendarDate);});
$('#calendarUpcoming').addEventListener('click',async e=>{const jobEdit=e.target.closest('[data-edit-opportunity]');if(jobEdit){const item=state.opportunities.find(x=>String(x.id)===jobEdit.dataset.editOpportunity);if(item){goView('memo');openMemoEditor(item);}return;}const edit=e.target.closest('[data-edit-schedule]');if(edit){const item=state.scheduleEvents.find(x=>String(x.id)===edit.dataset.editSchedule);if(item)openSchedule(item);return;}const remove=e.target.closest('[data-delete-schedule]');if(remove&&confirm('删除这条日程？')){try{await api(`/api/schedule-events/${remove.dataset.deleteSchedule}`,{method:'DELETE'});await loadAll();}catch(err){notice(err.message,true);}}});
$('#scheduleForm').addEventListener('submit',async e=>{e.preventDefault();const id=$('#scheduleId').value;const payload={event_type:$('#scheduleType').value,title:$('#scheduleTitle').value.trim(),event_date:$('#scheduleDate').value,event_time:$('#scheduleTime').value,location:$('#scheduleLocation').value.trim(),notes:$('#scheduleNotes').value.trim(),opportunity_id:Number($('#scheduleOpportunity').value)||null};try{await api(id?`/api/schedule-events/${id}`:'/api/schedule-events',{method:id?'PATCH':'POST',body:JSON.stringify(payload)});closeSchedule();notice(id?'日程已更新。':'日程已添加。');await loadAll();}catch(err){notice(err.message,true);}});

// ---------- email tracking ----------
$('#openEmailConfigBtn').addEventListener('click',()=>$('#emailConfigDialog').showModal());$('#emailConfigClose').addEventListener('click',()=>$('#emailConfigDialog').close());$('#openEmailHelpBtn').addEventListener('click',()=>$('#emailHelpDialog').showModal());$('#emailHelpClose').addEventListener('click',()=>$('#emailHelpDialog').close());
$('#emailSettingsForm').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/email/settings',{method:'POST',body:JSON.stringify({imap_host:$('#emailHost').value.trim(),imap_port:Number($('#emailPort').value)||993,username:$('#emailUsername').value.trim(),password:$('#emailPassword').value,folder:$('#emailFolder').value.trim()||'INBOX'})});$('#emailPassword').value='';$('#emailConfigDialog').close();notice('邮箱配置已保存。');await loadAll();}catch(err){notice(err.message,true);}});
$('#syncEmailBtn').addEventListener('click',async()=>{const button=$('#syncEmailBtn');button.disabled=true;button.textContent='检查中…';try{const data=await api('/api/email/sync',{method:'POST'});notice(`本次检查 ${data.checked||0} 封新邮件，新增 ${data.added||0} 封。`);await loadAll();}catch(err){notice(err.message,true);}finally{button.disabled=false;button.textContent='检查新邮件';}});
$$('.email-filter').forEach(button=>button.addEventListener('click',()=>{state.emailFilter=button.dataset.emailFilter;renderEmail();}));
$('#ignorePendingEmailBtn').addEventListener('click',async()=>{const count=state.emails.filter(x=>x.status==='pending').length;if(!count)return notice('当前没有待确认邮件。');if(!confirm(`确定忽略剩余 ${count} 封待确认邮件吗？`))return;try{const data=await api('/api/email/messages/ignore-pending',{method:'POST'});notice(`已忽略 ${data.ignored||0} 封邮件。`);await loadAll();}catch(err){notice(err.message,true);}});
$('#importEmailBtn').addEventListener('click',async()=>{const ids=$$('[data-email-choice]:checked');if(!ids.length)return notice('请先勾选需要导入的邮件。',true);const items=ids.map(box=>({email_id:Number(box.dataset.emailChoice),opportunity_id:Number($(`[data-email-opportunity="${box.dataset.emailChoice}"]`)?.value)||null}));const button=$('#importEmailBtn');button.disabled=true;try{const data=await api('/api/email/import',{method:'POST',body:JSON.stringify({items})});notice(`已导入 ${data.imported||0} 封求职邮件。`);await loadAll();}catch(err){notice(err.message,true);}finally{button.disabled=false;}});
$('#emailList').addEventListener('click',async e=>{const ignore=e.target.closest('[data-ignore-email]');if(ignore){try{await api(`/api/email/messages/${ignore.dataset.ignoreEmail}/ignore`,{method:'POST'});notice('邮件已忽略。');await loadAll();}catch(err){notice(err.message,true);}return;}const link=e.target.closest('[data-link-email]');if(link){const id=link.dataset.linkEmail;try{await api(`/api/email/messages/${id}/link`,{method:'POST',body:JSON.stringify({opportunity_id:Number($(`[data-email-opportunity="${id}"]`)?.value)||null})});notice('邮件关联已更新。');await loadAll();}catch(err){notice(err.message,true);}}});

// ---------- data safety ----------
$('#backupDbBtn').addEventListener('click',async()=>{const b=$('#backupDbBtn');b.disabled=true;try{const data=await api('/api/data/backup',{method:'POST'});notice(`备份完成：${data.path}`);await loadAll();}catch(err){notice(err.message,true);}finally{b.disabled=false;}});
$('#mergeDbForm').addEventListener('submit',async e=>{e.preventDefault();const file=$('#oldDbFile').files[0];if(!file)return notice('请选择需要导入的数据文件。',true);const b=e.submitter;b.disabled=true;try{const fd=new FormData();fd.append('file',file);const res=await fetch('/api/data/merge-db',{method:'POST',body:fd});const data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||'合并失败');const m=data.merged||{};notice(`数据已合并：岗位 +${m.opportunities||0}，经历 +${m.experiences||0}。`);$('#oldDbFile').value='';await loadAll();}catch(err){notice(err.message,true);}finally{b.disabled=false;}});
$('#syncConfigForm').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/sync/config',{method:'POST',body:JSON.stringify({remote_url:$('#syncRemoteUrl').value.trim(),branch:$('#syncBranch').value.trim()||'main',passphrase:$('#syncPassphrase').value,auto_start_check:$('#syncAutoStart').checked,auto_close_sync:$('#syncAutoClose').checked})});$('#syncPassphrase').value='';notice('同步配置已保存。同步口令只保存在本机。');await loadAll();}catch(err){notice(err.message,true);}});
async function syncAction(id,path,success){const b=$(id);b.disabled=true;try{await api(path,{method:'POST'});notice(success);await loadAll();}catch(err){notice(err.message,true);}finally{renderSyncStatus();}}
$('#syncCheckBtn').addEventListener('click',()=>syncAction('#syncCheckBtn','/api/sync/check','远程检查完成。'));
$('#syncAcceptBtn').addEventListener('click',()=>{if(confirm('接受远程数据会覆盖本机当前数据，但系统会先自动备份。确定继续吗？'))syncAction('#syncAcceptBtn','/api/sync/accept','远程数据已接受，本机已更新。');});
$('#syncCommitBtn').addEventListener('click',()=>syncAction('#syncCommitBtn','/api/sync/commit','当前全部数据已加密提交到私有仓库。'));
$('#syncRollbackBtn').addEventListener('click',()=>{if(confirm('确定回滚到上次接受远程更新前的本机版本吗？'))syncAction('#syncRollbackBtn','/api/sync/rollback','已回滚到接受更新前的本机版本。');});

loadAll();
