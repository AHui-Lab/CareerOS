/* CareerOS daily workflow. This module uses the existing services and stored records. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const all = (selector, root=document) => [...root.querySelectorAll(selector)];
  const text = esc;
  const organization=CareerJobOrganization, selectedJobs=new Set();
  let organizing=false, organizationJobs=[], organizationTarget='later';
  const ended = new Set(['offer', 'rejected', 'ignored']);
  const stages = [['inbox','待核对'],['preparing','准备投递'],['applied','等待回复'],['interview','面试中'],['offer','Offer'],['rejected','已结束']];
  const ui = {view:'dashboard',range:'week',jobView:'all',layout:'list',detailId:null,detailTab:'overview',scroll:{},assets:[],preps:[],searchIndex:-1,undo:null,resumeStep:1,settings:'general',generatedSignatures:new Map()};
  const dirtyForms = new Set();
  let undoTimer, toastTimer, commandEntries=[], initialRouteApplied=false;
  let pendingVaultAction=null, vaultReady=false;
  function queueVaultAction(payload){pendingVaultAction=payload;if(vaultReady){byId('careerVaultFrame').contentWindow?.postMessage(payload,new URL(byId('careerVaultFrame').src).origin);pendingVaultAction=null;}}
  byId('careerVaultFrame').addEventListener('load',()=>{vaultReady=true;if(pendingVaultAction)queueVaultAction(pendingVaultAction);});
  const originalReloadVault=reloadCareerVaultFrame;
  reloadCareerVaultFrame=function(){if(ui.vaultPending){notice('经历或文件尚未保存完成，请稍后再刷新。',true);return;}vaultReady=false;originalReloadVault();};
  window.addEventListener('message',event=>{const frame=byId('careerVaultFrame');if(event.source!==frame.contentWindow||event.origin!==new URL(frame.src).origin)return;if(event.data?.type==='careeros-vault-save-state')ui.vaultPending=!!event.data.pending;if(event.data?.type==='careeros-vault-ready'){ui.vaultPending=false;vaultReady=true;setTheme(document.documentElement.dataset.theme);if(pendingVaultAction)queueVaultAction(pendingVaultAction);}});
  function readPreference(key, fallback) { try { const value=localStorage.getItem('careeros.workspace.'+key); return value===null?fallback:JSON.parse(value); } catch { return fallback; } }
  function savePreference(key, value) { try {localStorage.setItem('careeros.workspace.'+key, JSON.stringify(value));} catch {} }
  let starred = new Set(readPreference('starred', []).map(String));
  ui.layout=readPreference('jobLayout','list');
  if(!['list','board'].includes(ui.layout))ui.layout='list';
  document.body.classList.toggle('compact-jobs',!!readPreference('compact',false));
  byId('compactJobsBtn').setAttribute('aria-pressed',String(document.body.classList.contains('compact-jobs')));
  const preferredTheme=readPreference('theme','light');
  setTheme(preferredTheme);
  function setTheme(theme) {
    theme=theme==='dark'?'dark':'light';
    document.documentElement.dataset.theme=theme;
    byId('appearanceBtn').textContent=theme==='dark'?'切换浅色外观':'切换深色外观';
    for(const id of ['careerVaultFrame','interviewPrepFrame'])byId(id)?.contentWindow?.postMessage({type:'careeros-theme',theme},id==='careerVaultFrame'?'http://127.0.0.1:8776':location.origin);
  }
  byId('appearanceBtn').addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';setTheme(theme);savePreference('theme',theme);});
  for(const id of ['careerVaultFrame','interviewPrepFrame'])byId(id).addEventListener('load',()=>setTheme(document.documentElement.dataset.theme));
  byId('todayDate').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'});

  titles.dashboard='总览';titles.memo='岗位管理';titles.resume='简历工作室';titles.profile='基本资料与兼容工具';
  subtitles.dashboard='从这里进入各个功能，按需展开详细内容。';
  subtitles.memo='比较岗位要求，查看投递进展，安排下一步行动。';
  subtitles.resume='选择目标、确认经历，再核查并生成你的简历。';
  subtitles.profile='管理基础字段，或使用旧版本地经历兼容工具。';
  const originalGoView=goView;
  function updateMobileNav(){const hidden=matchMedia('(max-width:680px)').matches&&!document.body.classList.contains('mobile-nav-open');document.querySelector('.sidebar').inert=hidden;document.querySelector('.sidebar').setAttribute('aria-hidden',String(hidden));}
  window.addEventListener('resize',updateMobileNav);updateMobileNav();
  function canLeave(next) {
    if(next===ui.view)return true;
    if(ui.view==='interview_prep') { const frame=byId('interviewPrepFrame'); if(frame.contentWindow?.requestPrepLeave && !frame.contentWindow.requestPrepLeave())return false; }
    if((ui.view==='settings'&&dirtyForms.has('privateProfileForm'))||(ui.view==='profile'&&dirtyForms.has('profileForm')))
      return confirm('这里有尚未保存的资料，仍要切换页面吗？输入会暂时保留在本页。');
    return true;
  }
  function writeRoute(view,job=null,replace=false) {
    const url=new URL(location.href);url.searchParams.set('view',view);
    job?url.searchParams.set('job',String(job)):url.searchParams.delete('job');
    if(url.href!==location.href)history[replace?'replaceState':'pushState']({view,job},'',url);
  }
  goView=function(view,options={}) {
    if(!titles[view] || !canLeave(view))return false;
    const previous=ui.view;ui.scroll[previous]=window.scrollY;
    originalGoView(view);ui.view=view;
    all('.nav').forEach(button=>{button.classList.toggle('active',button.dataset.view===view);button.setAttribute('aria-current',button.dataset.view===view?'page':'false');});
    byId('currentBreadcrumb').textContent=titles[view];
    document.body.classList.remove('mobile-nav-open');byId('mobileMenuBtn').setAttribute('aria-expanded','false');
    updateMobileNav();
    window.dispatchEvent(new CustomEvent('careeros-view-changed',{detail:{view}}));
    if(!options.fromHistory)writeRoute(view,options.job||null,options.replace);
    if(previous!==view)window.scrollTo({top:options.restore?ui.scroll[view]||0:0,behavior:'instant'});
    if(view==='resume'){renderPreviewState();showResumeStep(ui.resumeStep);}
    return true;
  };
  window.addEventListener('popstate',()=>{
    const params=new URLSearchParams(location.search),view=params.get('view')||'dashboard';
    if(!goView(view,{fromHistory:true,restore:true})) {writeRoute(ui.view,ui.detailId,true);return;}
    const id=Number(params.get('job'));
    if(id)openJob(id,{route:false});else if(byId('jobDetailDialog').open)byId('jobDetailDialog').close();
  });
  openVaultAction=function(type){sendVaultView('experiences');queueVaultAction({type});};
  byId('mobileMenuBtn').addEventListener('click',()=>{const open=document.body.classList.toggle('mobile-nav-open');byId('mobileMenuBtn').setAttribute('aria-expanded',String(open));updateMobileNav();});
  document.addEventListener('click',event=>{if(document.body.classList.contains('mobile-nav-open')&&!event.target.closest('.sidebar,#mobileMenuBtn')){document.body.classList.remove('mobile-nav-open');byId('mobileMenuBtn').setAttribute('aria-expanded','false');updateMobileNav();}});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'){document.body.classList.remove('mobile-nav-open');byId('mobileMenuBtn').setAttribute('aria-expanded','false');updateMobileNav();}});

  // Preserve unsaved form input across background refreshes.
  for(const id of ['profileForm','privateProfileForm','syncConfigForm','emailSettingsForm'])byId(id).addEventListener('input',()=>dirtyForms.add(id));
  const originalProfile=renderProfile, originalPrivate=renderPrivateProfile, originalSync=renderSyncStatus, originalEmail=renderEmail;
  renderProfile=()=>{if(!dirtyForms.has('profileForm'))originalProfile();};
  renderPrivateProfile=()=>{if(!dirtyForms.has('privateProfileForm'))originalPrivate();};
  renderSyncStatus=()=>{const form=byId('syncConfigForm'),values=dirtyForms.has('syncConfigForm')?all('input',form).map(el=>[el,el.value,el.checked]):[];originalSync();values.forEach(([el,value,checked])=>{el.value=value;el.checked=checked;});};
  renderEmail=()=>{const values=dirtyForms.has('emailSettingsForm')?all('input',byId('emailSettingsForm')).map(el=>[el,el.value]):[];originalEmail();values.forEach(([el,value])=>el.value=value);};
  const originalApi=api;
  api=async function(path,options={}){const generationInput=path==='/api/resume/generate'?resumeInputSignature():null;const result=await originalApi(path,options);if(generationInput&&result.item)ui.generatedSignatures.set(result.item.id,generationInput);if(options.method&&options.method!=='GET'){if(path==='/api/profile'){let payload={};try{payload=JSON.parse(options.body||'{}');}catch{}dirtyForms.delete(Object.hasOwn(payload,'id_number')?'privateProfileForm':'profileForm');}if(path==='/api/sync/config')dirtyForms.delete('syncConfigForm');if(path==='/api/email/settings')dirtyForms.delete('emailSettingsForm');}return result;};
  window.addEventListener('beforeunload',event=>{if(dirtyForms.size||ui.vaultPending){event.preventDefault();event.returnValue='';}});

  notice=function(message,error=false){
    clearTimeout(toastTimer);byId('globalNotice').classList.add('hidden');
    byId('workspaceToastText').textContent=message;byId('workspaceToast').classList.remove('hidden');byId('workspaceToast').classList.toggle('error',error);
    byId('workspaceUndo').hidden=!ui.undo;
    if(!error)toastTimer=setTimeout(()=>byId('workspaceToast').classList.add('hidden'),ui.undo?20000:8000);
  };
  byId('dismissToast').addEventListener('click',()=>byId('workspaceToast').classList.add('hidden'));
  function setUndo(action) {clearTimeout(undoTimer);ui.undo=action;undoTimer=setTimeout(()=>{ui.undo=null;byId('workspaceUndo').hidden=true;},20000);}
  byId('workspaceUndo').addEventListener('click',async()=>{const action=ui.undo;if(!action)return;byId('workspaceUndo').disabled=true;try{await action();ui.undo=null;notice('已撤销本次操作。');await loadAll();}catch(error){notice(error.message,true);}finally{byId('workspaceUndo').disabled=false;byId('workspaceUndo').hidden=!ui.undo;}});
  all('[data-close-dialog]').forEach(button=>button.addEventListener('click',()=>byId(button.dataset.closeDialog).close()));
  all('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close();}}));
  byId('globalAddBtn').addEventListener('click',()=>{byId('jobImportDialog').showModal();byId('urlInput').focus();});

  function badge(job){return `<span class="status-chip status-${text(job.status||'inbox')}">${text(job.status==='applied'?'等待回复':STATUS[job.status]||'待处理')}</span>`;}
  function needsReview(job){return !job.role||/招聘主页|待识别|校园招聘$/.test(job.role)||(job.page_kind==='career_home'&&!(job.jd_text||'').trim())||!(job.jd_text||job.description||'').trim();}
  function dateValue(value){const match=String(value||'').match(/^(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})/);if(!match)return '';const key=`${match[1]}-${match[2].padStart(2,'0')}-${match[3].padStart(2,'0')}`;const parsed=new Date(key+'T00:00:00');return !Number.isNaN(parsed.valueOf())&&localDate(parsed)===key?key:'';}
  function defaultAction(job){return {inbox:'核对岗位信息',interested:'核对岗位信息',preparing:'制作岗位简历',applied:'记录跟进安排',interview:'打开面试准备',offer:'查看录用记录',rejected:'查看复盘记录',ignored:'查看岗位记录'}[job.status]||'查看详情';}
  function starButton(job){return `<button type="button" class="star-job" data-star-job="${job.id}" aria-pressed="${starred.has(String(job.id))}" aria-label="${starred.has(String(job.id))?'取消重点关注':'重点关注'} ${text(job.company||'岗位')}">${starred.has(String(job.id))?'★':'☆'}</button>`;}
  function toggleStar(id){const key=String(id);starred.has(key)?starred.delete(key):starred.add(key);savePreference('starred',[...starred]);renderMemo();if(ui.detailId===Number(id))renderJobDetail();notice(starred.has(key)?'已加入重点关注。':'已取消重点关注。');}

  const originalDashboard=renderDashboard;
  renderDashboard=function(){
    originalDashboard();
    const today=localDate(new Date()),limit=localDate(new Date(Date.now()+7*86400000));
    const tasks=[],eventKeys=new Set();
    const jobs=new Map(state.opportunities.map(job=>[Number(job.id),job]));
    for(const event of state.scheduleEvents){
      if(event.source==='offer')continue;
      if(!['interview','written_test','signing','deadline','follow_up'].includes(event.event_type)||!dateValue(event.event_date)||event.event_date<today)continue;
      const job=jobs.get(Number(event.opportunity_id));
      if(job&&ended.has(job.status)&&event.event_type!=='signing')continue;
      if(job&&event.source==='opportunity'&&organization.disposition(job)!=='active')continue;
      // Generated opportunity follow-ups and their next-action are the same task.
      if(event.source==='opportunity'&&event.event_type==='follow_up'&&job?.next_action)continue;
      const key=[event.opportunity_id,event.event_date,event.event_time,event.title].join('|');if(eventKeys.has(key))continue;eventKeys.add(key);
      tasks.push({date:event.event_date,time:event.event_time||'',title:event.title,subtitle:[EVENT_TYPE[event.event_type],event.company||job?.company].filter(Boolean).join(' · '),job:job?.id,event: event.source==='opportunity'?null:event.id,action:false});
    }
    for(const job of state.opportunities){if(!job.next_action||ended.has(job.status)||organization.disposition(job)!=='active')continue;const date=dateValue(job.next_action_at);tasks.push({date,time:'',title:job.next_action,subtitle:[job.company,job.role].filter(Boolean).join(' · '),job:job.id,action:true});}
    for(const job of state.opportunities){if(organization.disposition(job)==='later'&&dateValue(job.revisit_at))tasks.push({date:dateValue(job.revisit_at),time:'',title:'回看稍后再投的岗位',subtitle:[job.company,job.role].filter(Boolean).join(' · '),job:job.id,action:false,revisit:true});}
    for(const offer of state.offers||[]){
      if(offer.archived||['declined','withdrawn'].includes(offer.status))continue;
      if(['pending','negotiating'].includes(offer.status)&&dateValue(offer.reply_deadline))tasks.push({date:offer.reply_deadline,time:'',title:'回复 Offer',subtitle:[offer.company,offer.role].filter(Boolean).join(' · '),offer:offer.id,action:false});
      if(dateValue(offer.details?.signing_date)&&offer.details.signing_date>=today&&!state.scheduleEvents.some(event=>event.source!=='offer'&&event.event_type==='signing'&&event.event_date===offer.details.signing_date&&(event.company===offer.company||event.title.includes(offer.company))))tasks.push({date:offer.details.signing_date,time:offer.details.signing_time||'',title:'Offer 签约安排',subtitle:[offer.company,offer.role].filter(Boolean).join(' · '),offer:offer.id,action:false});
    }
    tasks.sort((a,b)=>(a.date||'9999').localeCompare(b.date||'9999')||a.time.localeCompare(b.time));
    // Plans stay complete; the overview is a stable three-item preview of near-term work.
    const weekly=tasks.filter(task=>!task.date||task.date<=limit);
    const visiblePlans=ui.range==='week'?weekly:tasks;
    const nearEnd=new Date();nearEnd.setDate(nearEnd.getDate()+2);
    const focusPlans=weekly.filter(task=>task.action||task.revisit||task.offer||task.date>localDate(nearEnd));
    const suggested=[...state.opportunities].filter(job=>organization.disposition(job)==='active'&&['preparing','interview'].includes(job.status)&&!job.next_action).sort((a,b)=>Number(b.status==='interview')-Number(a.status==='interview')||Number(starred.has(String(b.id)))-Number(starred.has(String(a.id)))).slice(0,3);
    const taskCard=task=>{
      const overdue=task.date&&task.date<today,label=!task.date?'日期待安排':overdue?`逾期 · ${task.date}`:task.date===today?'今天':task.date;
      const open=task.offer?`data-offer-detail="${task.offer}"`:task.job?`data-open-job="${task.job}"`:task.event?`data-open-event="${task.event}"`:'';
      return `<article class="workspace-task ${overdue?'overdue':''}"><span class="task-glyph" aria-hidden="true">${task.action?'✓':'◷'}</span><button type="button" class="task-open" ${open}><strong>${text(task.title)}</strong><small><span class="task-date ${overdue?'overdue':''}">${text(label)} ${text(task.time)}</span> · ${text(task.subtitle)}</small></button>${task.action?`<div class="task-operations"><button type="button" class="ghost-btn" data-complete-action="${task.job}">完成</button><button type="button" class="ghost-btn" data-delay-action="${task.job}">延期</button></div>`:''}</article>`;
    };
    const suggestionCards=suggested.map(job=>`<article class="workspace-task suggested-task"><span class="task-glyph" aria-hidden="true">${job.status==='interview'?'◫':'▧'}</span><button type="button" class="task-open" data-open-job="${job.id}"><strong>${text(defaultAction(job))}</strong><small>${text(job.company)} · ${text(job.role||'岗位名称待补充')}</small></button><div class="task-operations"><button type="button" class="ghost-btn" ${job.status==='interview'?`data-job-prep="${job.id}"`:`data-job-resume="${job.id}"`}>${job.status==='interview'?'准备':'制作'}</button></div></article>`).join('');
    const empty='<div class="overview-empty"><strong>近期没有待办安排</strong><p>可以先记录经历，或为下一场笔面试安排时间。</p><button type="button" class="link-button" data-add-schedule>添加日程 →</button></div>';
    byId('dashboardTasks').innerHTML=visiblePlans.length?visiblePlans.map(taskCard).join(''):'<div class="overview-empty"><strong>这里还没有行动计划</strong><p>在岗位详情记录下一步行动，或添加笔面试日程。</p><button type="button" class="ghost-btn" data-add-schedule>添加日程</button></div>';
    byId('overviewFocusTasks').innerHTML=focusPlans.length?focusPlans.slice(0,3).map(taskCard).join(''):suggestionCards||empty;
    byId('overviewFocusTitle').textContent=focusPlans.length?'近期重点':suggested.length?'建议下一步':'近期重点';
    byId('overviewFocusHint').textContent=focusPlans.length?(focusPlans.length>3?`优先显示 3 项，另有 ${focusPlans.length-3} 项可在计划中查看`:'未来 7 天与尚待安排的行动'):suggested.length?'优先推进面试准备与岗位投递':'';
    byId('overviewTaskCount').textContent=tasks.length?`(${tasks.length})`:'';
    const review=state.opportunities.filter(job=>organization.disposition(job)==='active'&&!['rejected','ignored'].includes(job.status)&&(['inbox','interested'].includes(job.status)||needsReview(job))).length;
    const missing=state.opportunities.filter(job=>organization.disposition(job)==='active'&&SUBMITTED_STATUSES.has(job.status)&&!job.applied_at).length;
    const pending=state.emails.filter(email=>email.status==='pending').length;
    const attentionRows=[[review,'review','岗位信息待核对'],[pending,'email','邮件待确认'],[missing,'dates','缺少投递日期']].filter(([count])=>count>0).map(([count,type,label])=>`<button type="button" class="attention-row" data-attention="${type}"><span>${label}</span><strong>${count}</strong></button>`).join('');
    byId('dashboardAttention').innerHTML=attentionRows||'<div class="overview-empty"><strong>暂时没有待确认事项</strong><p>岗位信息与求职邮件都已整理。</p></div>';
    byId('navMailCount').textContent=pending;byId('navMailCount').hidden=!pending;
    byId('dashboardRecentJobs').innerHTML=[...state.opportunities].sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at))).slice(0,4).map(job=>`<button type="button" class="dashboard-job" data-open-job="${job.id}"><span><b>${text(job.company||'待补充公司')}</b><small>${text(job.role||'岗位待补充')}</small></span>${badge(job)}</button>`).join('')||'<div class="empty-state compact">导入第一个岗位，开始管理你的求职。</div>';
  };
  all('[data-task-range]').forEach(button=>button.addEventListener('click',()=>{ui.range=button.dataset.taskRange;all('[data-task-range]').forEach(item=>item.classList.toggle('active',item===button));renderDashboard();}));

  const originalMemoRows=memoRows;
  memoRows=function(){return originalMemoRows().filter(job=>{
    if(!organization.matches(job,ui.jobView))return false;
    if(ui.jobView==='starred')return starred.has(String(job.id));
    if(ui.jobView==='review')return !['rejected','ignored'].includes(job.status)&&(needsReview(job)||['inbox','interested'].includes(job.status));
    if(ui.jobView==='dates')return SUBMITTED_STATUSES.has(job.status)&&!job.applied_at;
    if(['ended','later','skipped','records'].includes(ui.jobView))return true;
    if(['preparing','applied','interview','offer'].includes(ui.jobView))return job.status===ui.jobView;
    return true;
  });};
  function rowFacts(job){return CareerJobDisplay.facts(job,{events:state.scheduleEvents,versions:state.versions,preps:ui.preps,emails:state.emails});}
  function shortDate(value){const parsed=CareerJobDisplay.dateValue(value);return parsed?parsed.slice(5).replace('-','/'):(value||'');}
  function organizationChoice(job){return organizing?`<input type="checkbox" class="job-select" data-select-job="${job.id}" aria-label="选择 ${text(job.company)} ${text(job.role)}" ${selectedJobs.has(job.id)?'checked':''}>`:starButton(job);}
  function syncJobSelection(){
    const visible=memoRows(),count=visible.filter(job=>selectedJobs.has(job.id)).length;
    byId('selectVisibleJobs').checked=visible.length>0&&count===visible.length;
    byId('selectVisibleJobs').indeterminate=count>0&&count<visible.length;
    byId('jobSelectionCount').textContent=`已选 ${selectedJobs.size} 项${selectedJobs.size>count?`（其中 ${selectedJobs.size-count} 项不在当前结果）`:''}`;
    all('[data-organize-target]').forEach(button=>button.disabled=!selectedJobs.size);
    all('[data-select-job]').forEach(input=>input.checked=selectedJobs.has(Number(input.dataset.selectJob)));
  }
  byId('organizeJobsBtn').addEventListener('click',()=>{organizing=!organizing;if(organizing)ui.layout='list';else selectedJobs.clear();renderMemo();});
  byId('memoList').addEventListener('change',event=>{if(!event.target.dataset.selectJob)return;const id=Number(event.target.dataset.selectJob);event.target.checked?selectedJobs.add(id):selectedJobs.delete(id);syncJobSelection();});
  byId('selectVisibleJobs').addEventListener('change',event=>{memoRows().forEach(job=>event.target.checked?selectedJobs.add(job.id):selectedJobs.delete(job.id));syncJobSelection();});
  byId('clearJobSelection').addEventListener('click',()=>{selectedJobs.clear();syncJobSelection();});
  function openOrganization(ids,target='later'){
    organizationJobs=state.opportunities.filter(job=>ids.includes(job.id)).map(job=>({...job,expected:organization.snapshot(job)}));if(!organizationJobs.length)return;
    if(byId('jobDetailDialog').open)byId('jobDetailDialog').close();
    byId('jobOrganizationTarget').value=target;updateOrganizationTarget();
    byId('jobOrganizationContext').textContent=`正在整理 ${organizationJobs.length} 个岗位${organizationJobs.length>1?' · 去向、日期及备注将应用于所有选中岗位':''}`;
    byId('jobOrganizationNames').innerHTML=organizationJobs.slice(0,5).map(job=>`<li>${text(job.company)} · ${text(job.role||job.title)}</li>`).join('')+(organizationJobs.length>5?`<li>另有 ${organizationJobs.length-5} 个岗位</li>`:'');
    byId('jobRevisitDate').value=organizationJobs.length===1?dateValue(organizationJobs[0].revisit_at):'';
    byId('jobRevisitDate').min=localDate(new Date());
    byId('jobOrganizationNote').value=organizationJobs.length===1?organizationJobs[0].disposition_note||'':'';
    byId('jobOrganizationError').hidden=true;byId('jobOrganizationDialog').showModal();
  }
  function updateOrganizationTarget(){organizationTarget=byId('jobOrganizationTarget').value;byId('jobOrganizationTitle').textContent=organization.labels[organizationTarget];byId('jobRevisitLabel').hidden=organizationTarget!=='later';byId('jobRevisitDate').disabled=organizationTarget!=='later';}
  byId('jobOrganizationTarget').addEventListener('change',updateOrganizationTarget);
  all('[data-organize-target]').forEach(button=>button.addEventListener('click',()=>openOrganization([...selectedJobs],button.dataset.organizeTarget)));
  byId('jobOrganizationForm').addEventListener('submit',async event=>{
    event.preventDefault();const button=event.submitter;button.disabled=true;byId('jobOrganizationError').hidden=true;
    const after={disposition:organizationTarget,revisit_at:organizationTarget==='later'?byId('jobRevisitDate').value:'',disposition_note:byId('jobOrganizationNote').value.trim()};
    try{
      const result=await api('/api/opportunities/organize',{method:'POST',body:JSON.stringify({changes:organizationJobs.map(job=>({id:job.id,...after,expected:job.expected}))})});
      setUndo(async()=>{await api('/api/opportunities/organize',{method:'POST',body:JSON.stringify({changes:result.before.map(job=>({...job,expected:after}))})});});
      byId('jobOrganizationDialog').close();selectedJobs.clear();notice(`已将 ${result.items.length} 个岗位移至「${organization.labels[organizationTarget]}」。`);await loadAll();
    }catch(error){byId('jobOrganizationError').textContent=error.message;byId('jobOrganizationError').hidden=false;}finally{button.disabled=false;}
  });
  function jobMaterials(job,facts){
    const parts=[];
    if(facts.versions)parts.push(`简历 ${facts.versions}`);
    if(facts.preps)parts.push(`准备 ${facts.preps}`);
    return (parts.length?`<button type="button" class="job-materials-link" data-job-materials="${job.id}" title="查看简历与准备资料">${parts.join(' · ')}</button>`:'')+(facts.emails?`<button type="button" class="job-materials-link" data-job-records="${job.id}" title="查看关联邮件">邮件 ${facts.emails}</button>`:'');
  }
  function jobDatesAndAction(job,facts){
    const disposition=organization.disposition(job);
    if(disposition!=='active')return `<span class="job-organization-state">${text(organization.labels[disposition])}</span>${job.revisit_at?`<span class="job-row-date">回看 ${text(shortDate(job.revisit_at))}${job.revisit_at<localDate(new Date())?' · 已到期':''}</span>`:''}${job.disposition_note?`<small class="job-organization-note" title="${text(job.disposition_note)}">${text(job.disposition_note)}</small>`:''}<button type="button" class="job-plan-link unset" data-organize-job="${job.id}" data-organize-single="active">恢复推进 →</button>`;
    const event=facts.next||facts.previous;
    const schedule=event?`<button type="button" class="job-schedule-link ${facts.next?'upcoming':'past'}" ${event.source==='opportunity'?`data-open-job="${job.id}"`:`data-open-event="${event.id}"`} title="${text(event.title||'')}"><span>${facts.next?'近期':'最近记录'} · ${text(EVENT_TYPE[event.event_type]||'日程')}</span><strong>${text(shortDate(event.event_date))}${event.event_time?` ${text(event.event_time)}`:''}</strong></button>`:'';
    const deadline=!event&&job.deadline?`<span class="job-row-date">截止 ${text(shortDate(job.deadline))}</span>`:'';
    const action=job.next_action?`<button type="button" class="job-plan-link" data-job-plan="${job.id}" title="${text(job.next_action)}"><span>${text(job.next_action)}</span>${job.next_action_at?`<small>${text(shortDate(job.next_action_at))}${dateValue(job.next_action_at)&&dateValue(job.next_action_at)<localDate(new Date())?' · 已逾期':''}</small>`:''}</button>`:`<button type="button" class="job-plan-link unset" data-job-plan="${job.id}">+ 安排下一步</button>`;
    return schedule+deadline+action;
  }
  const originalMemo=renderMemo;
  renderMemo=function(){
    originalMemo();
    const rows=memoRows();byId('memoEmpty').classList.toggle('hidden',rows.length>0);
    const activeJobs=state.opportunities.filter(job=>organization.disposition(job)==='active');
    const counts={all:activeJobs.length,...Object.fromEntries(['preparing','applied','interview','offer'].map(stage=>[stage,activeJobs.filter(job=>job.status===stage).length]))};
    all('[data-job-count]').forEach(element=>element.textContent=counts[element.dataset.jobCount]);
    byId('jobsSpecialView').value=['review','starred','ended','later','skipped','records'].includes(ui.jobView)?ui.jobView:'';
    byId('memoScopeFilter').value=state.memoScope;
    const filters=[byId('memoCategoryFilter').value,byId('memoStatusFilter').value,state.memoScope==='all'?'':state.memoScope].filter(Boolean).length;
    byId('jobsFilterCount').textContent=filters?String(filters):'';
    all('[data-job-view]').forEach(button=>button.classList.toggle('active',button.dataset.jobView===ui.jobView));
    all('[data-job-layout]').forEach(button=>{const active=button.dataset.jobLayout===ui.layout;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));button.disabled=organizing&&button.dataset.jobLayout==='board';});
    byId('memoCount').textContent=`${rows.length} 项 · 共 ${state.opportunities.length} 条记录`;
    byId('jobOrganizationBar').hidden=!organizing;
    byId('organizeJobsBtn').textContent=organizing?'完成整理':'整理岗位';
    byId('organizeJobsBtn').setAttribute('aria-pressed',String(organizing));
    state.opportunities.length||selectedJobs.clear();
    for(const id of selectedJobs)if(!state.opportunities.some(job=>job.id===id))selectedJobs.delete(id);
    if(ui.layout==='board'&&!organizing){
      byId('memoList').innerHTML=`<div class="job-board">${stages.map(([stage,label])=>{
        const items=rows.filter(job=>stage==='inbox'?['inbox','interested'].includes(job.status):stage==='rejected'?['rejected','ignored'].includes(job.status):job.status===stage);
        return `<section class="job-lane"><div class="job-lane-heading">${label}<span>${items.length}</span></div>${items.map(job=>`<article class="job-board-card memo-card" data-id="${job.id}"><div class="job-board-meta"><span>${text(JOB_CATEGORY[job.job_category]||'未分类')}</span>${starButton(job)}</div><button type="button" class="job-main-button" data-open-job="${job.id}"><span class="job-company">${text(job.company||'待补充公司')}</span><span class="job-role">${text(job.role||job.title||'待补充岗位')}</span></button><div class="job-board-facts"><span>${text([job.location,job.applied_at?`投递 ${shortDate(job.applied_at)}`:''].filter(Boolean).join(' · '))}</span>${rowFacts(job).excerpt?`<button type="button" class="job-jd-excerpt" data-job-jd="${job.id}">${text(rowFacts(job).excerpt)}</button>`:''}${job.referral_code?`<button type="button" class="job-referral-code" data-copy-referral="${job.id}">内推 ${text(job.referral_code)}</button>`:''}${jobMaterials(job,rowFacts(job))}</div><div class="job-action-cell">${jobDatesAndAction(job,rowFacts(job))}</div><select data-action="status" aria-label="${text(job.company||'岗位')}投递状态">${statusOptions(job.status)}</select></article>`).join('')||'<div class="lane-empty">暂无岗位</div>'}</section>`;
      }).join('')}</div>`;
    }else{
      byId('memoList').innerHTML=(rows.length?'<div class="job-table-head" aria-hidden="true"><span></span><span>公司与岗位</span><span>JD 与求职材料</span><span>投递进展</span><span>日程与下一步</span><span></span></div>':'')+rows.map(job=>{
        const facts=rowFacts(job),location=[job.location,JOB_CATEGORY[job.job_category]||'未分类'].filter(Boolean).join(' · ');
        return `<article class="workspace-job-row memo-card" data-id="${job.id}">${organizationChoice(job)}<button type="button" class="job-main-button" data-open-job="${job.id}"><span class="job-company" title="${text(job.company||'')}"><span class="job-company-name">${text(job.company||'待补充公司')}</span>${needsReview(job)?'<span class="review-flag">待核对</span>':''}</span><span class="job-role" title="${text(job.role||job.title||'')}">${text(job.role||job.title||'待补充岗位')}</span><span class="job-location" title="${text(location)}">${text(location)}</span>${organizing?`<small class="job-collected-date">收集 ${text(dateValue(job.created_at)||'日期未知')}</small>`:''}</button><div class="job-evidence-cell">${facts.excerpt?`<button type="button" class="job-jd-excerpt" data-job-jd="${job.id}" title="查看完整 JD">${text(facts.excerpt)}</button>`:`<button type="button" class="job-jd-missing" data-edit-job-full="${job.id}">${needsReview(job)?'核对岗位并补充 JD':'补充岗位 JD'} →</button>`}<div class="job-row-materials">${jobMaterials(job,facts)}${job.referral_code?`<button type="button" class="job-referral-code" data-copy-referral="${job.id}" title="点击复制内推码 ${text(job.referral_code)}">内推 ${text(job.referral_code)}</button>`:''}</div></div><div class="job-stage-cell"><select class="job-status-control status-${text(job.status||'inbox')}" data-action="status" aria-label="${text(job.company||'岗位')}投递阶段">${statusOptions(job.status)}</select>${facts.applied?`<span class="job-applied-date">投递 ${text(shortDate(facts.applied))}</span>${facts.elapsed>=0?`<small class="job-elapsed">${facts.elapsed===0?'今天投递':`已过 ${facts.elapsed} 天`}</small>`:''}`:''}</div><div class="job-action-cell">${jobDatesAndAction(job,facts)}</div><div class="job-row-controls"><button type="button" class="small-btn" data-open-job="${job.id}">详情</button><button type="button" class="link-button" data-organize-job="${job.id}">整理</button></div></article>`;
      }).join('');
    }
    syncJobSelection();
  };
  function selectJobView(view){ui.jobView=view;state.memoScope='all';byId('memoStatusFilter').value='';byId('memoCategoryFilter').value='';byId('memoSearch').value='';all('[data-memo-scope]').forEach(button=>button.classList.toggle('active',button.dataset.memoScope==='all'));renderMemo();}
  all('[data-job-view]').forEach(button=>button.addEventListener('click',()=>selectJobView(button.dataset.jobView)));
  all('[data-overview-stage]').forEach(button=>button.addEventListener('click',()=>{if(!goView('memo'))return;selectJobView(button.dataset.overviewStage);}));
  byId('jobsSpecialView').addEventListener('change',event=>selectJobView(event.target.value||'all'));
  byId('memoScopeFilter').addEventListener('change',event=>{state.memoScope=event.target.value;renderMemo();});
  all('[data-job-layout]').forEach(button=>button.addEventListener('click',()=>{ui.layout=button.dataset.jobLayout;savePreference('jobLayout',ui.layout);renderMemo();}));
  byId('compactJobsBtn').addEventListener('click',()=>{const compact=document.body.classList.toggle('compact-jobs');byId('compactJobsBtn').setAttribute('aria-pressed',String(compact));savePreference('compact',compact);});
  byId('clearMemoFilters').addEventListener('click',()=>{ui.jobView='all';renderMemo();});

  let plannedJob=null;
  function openJobPlan(id){plannedJob=state.opportunities.find(job=>Number(job.id)===Number(id));if(!plannedJob)return;byId('jobPlanContext').textContent=[plannedJob.company,plannedJob.role].filter(Boolean).join(' · ');byId('jobPlanAction').value=plannedJob.next_action||'';byId('jobPlanDate').value=dateValue(plannedJob.next_action_at);byId('jobPlanError').hidden=true;byId('jobPlanDialog').showModal();byId('jobPlanAction').focus();}
  byId('jobPlanForm').addEventListener('submit',async event=>{event.preventDefault();if(!plannedJob)return;const action=byId('jobPlanAction').value.trim(),date=byId('jobPlanDate').value;byId('jobPlanError').hidden=true;if(date&&!action){byId('jobPlanError').textContent='选择日期后，请写明下一步行动。';byId('jobPlanError').hidden=false;return;}const button=event.submitter;button.disabled=true;try{await api(`/api/opportunities/${plannedJob.id}/edit`,{method:'POST',body:JSON.stringify({next_action:action,next_action_at:date})});byId('jobPlanDialog').close();notice('下一步行动已保存。');await loadAll();}catch(error){byId('jobPlanError').textContent=error.message;byId('jobPlanError').hidden=false;}finally{button.disabled=false;}});
  document.addEventListener('click',event=>{const filters=document.querySelector('.jobs-more-filters');if(filters.open&&!event.target.closest('.jobs-more-filters'))filters.open=false;});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')document.querySelector('.jobs-more-filters').open=false;});

  async function completeAction(id,button){const job=state.opportunities.find(item=>item.id===Number(id));if(!job?.next_action)return;button.disabled=true;const before={next_action:job.next_action,next_action_at:job.next_action_at||''};try{await api(`/api/opportunities/${job.id}/edit`,{method:'POST',body:JSON.stringify({next_action:'',next_action_at:''})});setUndo(async()=>{const fresh=await api('/api/opportunities');const item=fresh.items?.find(x=>x.id===job.id);if(item?.next_action)throw new Error('该岗位已有新的行动，请在详情中核对，避免覆盖。');await api(`/api/opportunities/${job.id}/edit`,{method:'POST',body:JSON.stringify(before)});});notice(`已完成「${before.next_action}」。`);await loadAll();}catch(error){notice(error.message,true);}finally{button.disabled=false;}}
  let delayedJob=null;
  function delayAction(id){const job=state.opportunities.find(item=>item.id===Number(id));if(!job)return;delayedJob=job;byId('actionDateDescription').textContent=`${job.company} · ${job.next_action||'请先在岗位详情填写行动'}`;byId('actionNewDate').value=dateValue(job.next_action_at)||localDate(new Date(Date.now()+86400000));byId('actionDateDialog').showModal();}
  byId('actionDateForm').addEventListener('submit',async event=>{event.preventDefault();if(!delayedJob?.next_action)return notice('请先在岗位详情填写下一步行动。',true);const button=event.submitter;button.disabled=true;try{await api(`/api/opportunities/${delayedJob.id}/edit`,{method:'POST',body:JSON.stringify({next_action_at:byId('actionNewDate').value})});byId('actionDateDialog').close();notice('行动日期已更新。');await loadAll();}catch(error){notice(error.message,true);}finally{button.disabled=false;}});

  function openJob(id,{route=true}={}){const job=state.opportunities.find(item=>item.id===Number(id));if(!job)return notice('这个岗位暂未找到，请刷新后重试。',true);ui.detailId=job.id;ui.detailTab='overview';renderJobDetail();if(!byId('jobDetailDialog').open)byId('jobDetailDialog').showModal();if(route)writeRoute(ui.view,job.id);}
  byId('jobDetailDialog').addEventListener('close',()=>{ui.detailId=null;writeRoute(ui.view,null,true);});
  function matchingVersions(job){return state.versions.filter(version=>Number(version.target_opportunity_id??version.opportunity_id)===job.id || job.company&&job.role&&version.target_company===job.company&&version.target_role===job.role);}
  function renderJobDetail(){
    const job=state.opportunities.find(item=>item.id===ui.detailId);if(!job)return;
    byId('jobDetailTitle').textContent=job.company||'待补充公司';
    const versions=matchingVersions(job),emails=state.emails.filter(item=>Number(item.opportunity_id)===job.id),preps=ui.preps.filter(item=>Number(item.opportunity_id)===job.id),questions=state.interviewQuestions.filter(item=>Number(item.opportunity_id)===job.id);
    const tabs=[['overview','概况与行动'],['jd','岗位 JD'],['materials',`简历与准备 (${versions.length+preps.length})`],['records',`邮件与记录 (${emails.length+questions.length})`]];
    let content='';
    if(ui.detailTab==='overview')content=`<div class="job-detail-section"><div class="job-detail-organization"><span>${text(organization.labels[organization.disposition(job)])}${job.revisit_at?` · 回看 ${text(job.revisit_at)}`:''}</span><button type="button" class="link-button" data-organize-job="${job.id}">整理去向 →</button></div>${job.disposition_note?`<p class="helper">整理备注：${text(job.disposition_note)}</p>`:''}<div class="job-next-action"><strong>下一步</strong>${text(job.next_action||defaultAction(job))}${job.next_action_at?`<p class="helper">计划日期：${text(job.next_action_at)}</p>`:''}</div><form id="jobQuickForm" class="job-detail-form"><label>投递阶段<select id="jobQuickStatus">${statusOptions(job.status)}</select></label><label>岗位方向<select id="jobQuickCategory">${jobCategoryOptions(job.job_category)}</select></label><label class="full-span">下一步行动<input id="jobQuickAction" maxlength="200" value="${text(job.next_action||'')}" placeholder="如：完善项目经历后投递"></label><label>计划日期<input id="jobQuickDate" type="date" value="${text(dateValue(job.next_action_at))}"></label><label>实际投递日期<input id="jobQuickApplied" type="date" value="${text(dateValue(job.applied_at))}"></label><div class="full-span"><button type="submit" class="primary-btn">保存行动与阶段</button><span id="jobQuickFeedback" class="helper" role="status"></span></div></form>${job.note?`<div><h3>岗位备注</h3><p class="detail-note">${text(job.note)}</p></div>`:''}<div class="detail-timeline"><div>收集岗位<small>${text(job.created_at||'时间待补充')}</small></div>${job.applied_at?`<div>记录投递日期<small>${text(job.applied_at)}</small></div>`:''}<div>当前阶段<small>${text(STATUS[job.status]||'待处理')}</small></div></div><div><button type="button" class="link-button" data-edit-job-full="${job.id}">编辑完整信息、JD 与内推码 →</button></div></div>`;
    if(ui.detailTab==='jd')content=`<div class="job-detail-section"><div class="section-title"><h3>岗位职责与要求</h3><button type="button" class="ghost-btn" data-edit-job-full="${job.id}">核对与编辑</button></div><div class="detail-jd">${text(job.jd_text||job.description||job.raw_text||'还没有 JD。请从招聘详情页导入，或粘贴真实岗位要求。')}</div>${job.referral_code?`<p class="helper">内推码：${text(job.referral_code)}</p>`:''}</div>`;
    if(ui.detailTab==='materials')content=`<div class="job-detail-section"><div><div class="section-title"><h3>岗位简历</h3><button type="button" class="primary-btn" data-job-resume="${job.id}">制作简历</button></div>${versions.map(version=>`<div class="detail-related-row"><div><b>${text(version.name||'岗位简历')}</b><small>${text(version.created_at)}</small></div><div class="toolbar-actions"><button type="button" class="small-btn" data-open-version="${version.id}">预览</button><a class="small-btn" href="/api/resume-versions/${version.id}/pdf">PDF</a><a class="small-btn" href="/api/resume-versions/${version.id}/docx">DOCX</a></div></div>`).join('')||'<p class="helper">尚未生成这个岗位的简历。</p>'}</div><div><div class="section-title"><h3>面试准备空间</h3><button type="button" class="ghost-btn" data-job-prep="${job.id}">新增准备</button></div>${preps.map(prep=>`<div class="detail-related-row"><div><b>${text(prep.title)}</b><small>${text(prep.interview_date||'时间待确认')} · ${prep.completed_count} / ${prep.task_count} 项完成</small></div><button type="button" class="small-btn" data-open-linked-prep="${text(prep.id)}">打开准备</button></div>`).join('')||'<p class="helper">还没有关联的准备空间。可以新建，或关联已有资料。</p>'}<div class="toolbar-actions"><select id="existingPrepSelect" aria-label="选择已有准备空间"><option value="">关联已有准备空间…</option>${ui.preps.filter(prep=>!prep.opportunity_id).map(prep=>`<option value="${text(prep.id)}">${text(prep.title)}</option>`).join('')}</select><button type="button" class="ghost-btn" data-link-existing-prep="${job.id}">确认关联</button></div></div></div>`;
    if(ui.detailTab==='records')content=`<div class="job-detail-section"><div><div class="section-title"><h3>笔面试与跟进安排</h3><button type="button" class="ghost-btn" data-job-schedule="${job.id}">添加安排</button></div>${state.scheduleEvents.filter(event=>Number(event.opportunity_id)===job.id).map(event=>`<div class="detail-related-row"><div><b>${text(event.title)}</b><small>${text(event.event_date)} ${text(event.event_time||'')}</small></div>${event.source==='opportunity'?'<span class="helper">来自岗位记录</span>':`<button type="button" class="small-btn" data-open-event="${event.id}">编辑</button>`}</div>`).join('')||'<p class="helper">暂无已记录的日程。</p>'}</div><div><h3>相关邮件</h3>${emails.map(email=>`<div class="detail-related-row"><div><b>${text(email.subject||'无主题邮件')}</b><small>${text(email.received_at||'')} · ${text(email.sender||'')}</small></div><button type="button" class="small-btn" data-job-emails="${job.id}">查看</button></div>`).join('')||'<p class="helper">尚未关联招聘邮件。</p>'}</div><div><div class="section-title"><h3>面试题与复盘</h3><button type="button" class="ghost-btn" data-job-question="${job.id}">记录问题</button></div>${questions.map(question=>`<div class="detail-related-row"><div><b>${text(question.question)}</b><small>${text(question.event_date||'')} · ${text(question.topic||'待分类')}</small></div><button type="button" class="small-btn" data-edit-linked-question="${question.id}">查看与编辑</button></div>`).join('')||'<p class="helper">面试后把真实问题与回答记录在这里。</p>'}</div></div>`;
    byId('jobDetailContent').innerHTML=`<div class="job-detail-hero"><div><p class="job-detail-role">${text(job.role||job.title||'岗位名称待补充')}</p><div class="job-detail-meta">${badge(job)}<span>${text(JOB_CATEGORY[job.job_category]||'未分类')}</span><span>${text(job.location||'地点待补充')}</span>${job.deadline?`<span>截止 ${text(job.deadline)}</span>`:''}</div></div>${starButton(job)}</div><div class="job-detail-actions"><button type="button" class="primary-btn" ${job.status==='interview'?`data-job-prep="${job.id}"`:`data-job-resume="${job.id}"`}>${job.status==='interview'?'打开 / 创建面试准备':'制作岗位简历'}</button><button type="button" class="ghost-btn" data-job-schedule="${job.id}">添加日程</button>${job.source_url&&/^https?:\/\//i.test(job.source_url)?`<a class="ghost-btn" href="${text(job.source_url)}" target="_blank" rel="noopener">招聘原页面 ↗</a>`:''}<button type="button" class="ghost-btn" data-edit-job-full="${job.id}">编辑</button><button type="button" class="ghost-btn danger" data-delete-job="${job.id}">删除</button></div><div class="job-detail-tabs" role="tablist" aria-label="岗位详情内容">${tabs.map(([id,label])=>`<button type="button" class="job-detail-tab ${ui.detailTab===id?'active':''}" data-detail-tab="${id}" role="tab" aria-selected="${ui.detailTab===id}" aria-controls="jobDetailPanel">${label}</button>`).join('')}</div><div id="jobDetailPanel" role="tabpanel">${content}</div>`;
    byId('jobQuickForm')?.addEventListener('submit',async event=>{event.preventDefault();const action=byId('jobQuickAction').value.trim(),date=byId('jobQuickDate').value;if(date&&!action)return notice('选择了计划日期，请同时写明下一步行动。',true);const button=event.submitter;button.disabled=true;try{await api(`/api/opportunities/${job.id}/edit`,{method:'POST',body:JSON.stringify({next_action:action,next_action_at:date,applied_at:byId('jobQuickApplied').value})});const status=byId('jobQuickStatus').value,category=byId('jobQuickCategory').value;if(status!==job.status)await api(`/api/opportunities/${job.id}/status`,{method:'POST',body:JSON.stringify({status})});if(category!==job.job_category)await api(`/api/opportunities/${job.id}/category`,{method:'POST',body:JSON.stringify({category})});notice('岗位行动与阶段已保存。');await loadAll();renderJobDetail();}catch(error){notice(error.message,true);}finally{button.disabled=false;}});
  }
  function jobResume(id){if(!goView('resume'))return;byId('jobDetailDialog').close();byId('targetOpportunity').value=String(id);byId('targetOpportunity').dispatchEvent(new Event('change'));showResumeStep(1);}
  function jobSchedule(id){byId('jobDetailDialog').close();openSchedule();fillScheduleOpportunities(id);const job=state.opportunities.find(item=>item.id===Number(id));byId('scheduleTitle').value=[job?.company,job?.role].filter(Boolean).join(' · ');byId('scheduleType').value=job?.status==='interview'?'interview':'follow_up';}
  async function jobPrep(id){const job=state.opportunities.find(item=>item.id===Number(id));if(!job)return;const linked=ui.preps.find(prep=>Number(prep.opportunity_id)===job.id);byId('jobDetailDialog').close();if(!goView('interview_prep'))return;if(linked){await window.PrepLibrary?.openById(linked.id);return;}window.PrepLibrary?.createForJob(job);}

  document.addEventListener('click',async event=>{
    const button=event.target.closest('button');if(!button)return;
    if(button.dataset.openJob){openJob(button.dataset.openJob);return;}
    if(button.dataset.organizeJob){openOrganization([Number(button.dataset.organizeJob)],button.dataset.organizeSingle||'later');return;}
    if(button.dataset.jobJd){openJob(button.dataset.jobJd);ui.detailTab='jd';renderJobDetail();return;}
    if(button.dataset.jobMaterials){openJob(button.dataset.jobMaterials);ui.detailTab='materials';renderJobDetail();return;}
    if(button.dataset.jobRecords){openJob(button.dataset.jobRecords);ui.detailTab='records';renderJobDetail();return;}
    if(button.dataset.jobPlan){openJobPlan(button.dataset.jobPlan);return;}
    if(button.dataset.copyReferral){const job=state.opportunities.find(item=>String(item.id)===button.dataset.copyReferral);if(job?.referral_code){try{await navigator.clipboard.writeText(job.referral_code);notice('内推码已复制。');}catch{notice('暂时无法复制，请在岗位详情查看内推码。',true);}}return;}
    if(button.dataset.starJob){toggleStar(button.dataset.starJob);return;}
    if(button.dataset.completeAction){await completeAction(button.dataset.completeAction,button);return;}
    if(button.dataset.delayAction){delayAction(button.dataset.delayAction);return;}
    if(button.hasAttribute('data-add-schedule')){openSchedule();return;}
    if(button.dataset.openEvent){byId('jobDetailDialog').close();const item=state.scheduleEvents.find(row=>String(row.id)===button.dataset.openEvent);if(item)openSchedule(item);return;}
    if(button.dataset.attention){const type=button.dataset.attention;if(type==='email'){goView('email');return;}if(goView('memo'))selectJobView(type==='dates'?'dates':'review');return;}
    if(button.dataset.detailTab){ui.detailTab=button.dataset.detailTab;renderJobDetail();return;}
    if(button.dataset.editJobFull){const job=state.opportunities.find(item=>String(item.id)===button.dataset.editJobFull);byId('jobDetailDialog').close();if(job)openMemoEditor(job);return;}
    if(button.dataset.jobResume){jobResume(button.dataset.jobResume);return;}
    if(button.dataset.jobPrep){await jobPrep(button.dataset.jobPrep);return;}
    if(button.dataset.jobSchedule){jobSchedule(button.dataset.jobSchedule);return;}
    if(button.dataset.openVersion){const version=state.versions.find(item=>String(item.id)===button.dataset.openVersion);if(version&&goView('resume')){byId('jobDetailDialog').close();renderResumePreview(version);}return;}
    if(button.dataset.openLinkedPrep){if(goView('interview_prep')){byId('jobDetailDialog').close();await window.PrepLibrary?.openById(button.dataset.openLinkedPrep);}return;}
    if(button.dataset.linkExistingPrep){const id=byId('existingPrepSelect').value;if(!id)return notice('请先选择要关联的准备空间。',true);button.disabled=true;try{await api(`/api/interview-prep/${encodeURIComponent(id)}/opportunity`,{method:'PATCH',body:JSON.stringify({opportunity_id:Number(button.dataset.linkExistingPrep)})});await loadExtra();renderJobDetail();notice('准备空间已关联到该岗位。');}catch(error){notice(error.message,true);}finally{button.disabled=false;}return;}
    if(button.dataset.jobEmails){if(goView('email')){byId('jobDetailDialog').close();state.emailFilter='all';renderEmail();const email=state.emails.find(row=>Number(row.opportunity_id)===Number(button.dataset.jobEmails));byId('emailList').querySelector(`[data-email-opportunity="${email?.id}"]`)?.closest('.email-card')?.scrollIntoView({block:'center'});}return;}
    if(button.dataset.jobQuestion){const job=state.opportunities.find(item=>String(item.id)===button.dataset.jobQuestion);byId('jobDetailDialog').close();openInterviewQuestion(null,'interview');byId('interviewQuestionOpportunity').value=String(job.id);byId('interviewQuestionCompany').value=job.company||'';return;}
    if(button.dataset.editLinkedQuestion){const question=state.interviewQuestions.find(item=>String(item.id)===button.dataset.editLinkedQuestion);byId('jobDetailDialog').close();if(question)openInterviewQuestion(question,question.question_type);return;}
    if(button.dataset.deleteJob){if(!confirm('删除这条岗位记录？此操作不会删除已生成的简历文件。'))return;button.disabled=true;try{await api(`/api/opportunities/${button.dataset.deleteJob}`,{method:'DELETE'});byId('jobDetailDialog').close();notice('岗位记录已删除。');await loadAll();}catch(error){notice(error.message,true);button.disabled=false;}return;}
  });

  // Three-step resume creation retains the original fields and generation pipeline.
  const builder=document.querySelector('.resume-builder'),form=byId('resumeGenerateForm');
  const stepNav=document.createElement('div');stepNav.className='resume-step-nav';stepNav.setAttribute('role','group');stepNav.setAttribute('aria-label','简历制作步骤');
  stepNav.innerHTML=[['1','确认目标'],['2','选择经历'],['3','核查与生成']].map(([id,label])=>`<button type="button" class="resume-step-button" data-resume-step="${id}"><span class="resume-step-number">${id}</span>${label}</button>`).join('');builder.insertBefore(stepNav,form);
  const groups=[[],[],[]];const children=[...form.children];
  children.forEach(el=>{const group=el.id==='careerRecommendationPanel'||el.id==='legacyChooserWrap'?2:el.id==='resumePreflight'||el.tagName==='BUTTON'?3:1;el.dataset.resumeGroup=group;groups[group-1].push(el);});
  const stepHelp=document.createElement('p');stepHelp.className='resume-step-help';builder.insertBefore(stepHelp,form);
  const stepActions=document.createElement('div');stepActions.className='resume-step-actions';stepActions.innerHTML='<button type="button" class="ghost-btn" id="resumeStepPrev">上一步</button><button type="button" class="primary-btn" id="resumeStepNext">下一步：选择经历</button>';form.append(stepActions);
  function showResumeStep(step){ui.resumeStep=Math.min(3,Math.max(1,Number(step)||1));for(const group of groups)for(const el of group)el.classList.toggle('workspace-step-hidden',Number(el.dataset.resumeGroup)!==ui.resumeStep);all('[data-resume-step]').forEach(button=>{const active=Number(button.dataset.resumeStep)===ui.resumeStep;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});byId('resumeStepPrev').hidden=ui.resumeStep===1;byId('resumeStepNext').hidden=ui.resumeStep===3;byId('resumeStepNext').textContent=ui.resumeStep===1?'下一步：选择经历':'下一步：核查与生成';stepHelp.textContent=['先确认目标公司、岗位和真实 JD。通用简历也可手动填写。','推荐是参考，进入简历的经历由你确认；事实保存在经历库中。','检查目标与经历，再生成版本。预览与导出始终对应具体版本。'][ui.resumeStep-1];renderResumePreflight();}
  all('[data-resume-step]').forEach(button=>button.addEventListener('click',()=>showResumeStep(button.dataset.resumeStep)));
  byId('resumeStepPrev').addEventListener('click',()=>showResumeStep(ui.resumeStep-1));
  byId('resumeStepNext').addEventListener('click',()=>{showResumeStep(ui.resumeStep+1);if(ui.resumeStep===2&&!state.recommendations.length&&state.health.careervault?.available)loadRecommendations({quiet:true});});
  const stepStyle=document.createElement('style');stepStyle.textContent='.workspace-step-hidden{display:none!important}';document.head.append(stepStyle);
  const previewBadge=document.createElement('div');previewBadge.className='preview-version-badge';previewBadge.id='previewVersionState';byId('resumePreview').before(previewBadge);
  const originalPreview=renderResumePreview;
  renderResumePreview=function(version){originalPreview(version);renderPreviewState();};
  function resumeInputSignature(){return JSON.stringify([targetSignature(),selectedRecommendationIds().sort(),all('[data-exp-choice]:checked').map(el=>el.value).sort()]);}
  function renderPreviewState(){const version=state.latestVersion;if(!version){previewBadge.textContent='尚未生成版本 · 完成左侧步骤后查看预览';previewBadge.classList.remove('stale');byId('previewActions').innerHTML='';byId('resumePreview').innerHTML='<p>完成左侧步骤并生成后，这里显示简历预览。</p>';byId('resumePreview').classList.add('empty-preview');return;}const target=targetPayload(),same=version.target_company===target.target_company&&version.target_role===target.target_role,current=ui.generatedSignatures.get(version.id)===resumeInputSignature();previewBadge.textContent=`${current?'当前生成版本':'历史版本'} #${version.id} · ${[version.target_company,version.target_role].filter(Boolean).join(' · ')||'通用简历'}${current?' · 与当前输入一致':same?' · 修改内容后需重新生成':' · 与当前编辑目标不同'}`;previewBadge.classList.toggle('stale',!same||ui.generatedSignatures.has(version.id)&&!current);}
  for(const id of ['targetOpportunity','targetCompany','targetRole','targetJd'])byId(id).addEventListener(id==='targetOpportunity'?'change':'input',renderPreviewState);
  form.addEventListener('change',renderPreviewState);
  const versionToolbar=document.createElement('div');versionToolbar.className='resume-version-tools';versionToolbar.innerHTML='<input id="versionSearch" type="search" aria-label="搜索简历版本" placeholder="搜索版本名称、公司或岗位…"><span class="helper">选择历史版本可预览并下载</span>';byId('versionList').before(versionToolbar);byId('versionSearch').addEventListener('input',()=>{const query=byId('versionSearch').value.toLowerCase();all('.version-card').forEach(card=>card.hidden=!card.textContent.toLowerCase().includes(query));});

  // Categorized settings keep every original panel and action accessible.
  const settingsGrid=document.querySelector('.settings-grid'),settingsNav=document.createElement('div');settingsNav.className='settings-nav';settingsNav.setAttribute('role','group');settingsNav.setAttribute('aria-label','设置分类');
  const settingsNames=[['general','概况与连接'],['private','私密资料'],['data','备份与同步'],['assistant','浏览器助手'],['help','帮助与兼容']];settingsNav.innerHTML=settingsNames.map(([id,label])=>`<button type="button" data-settings-tab="${id}">${label}</button>`).join('');settingsGrid.before(settingsNav);
  all(':scope > .panel',settingsGrid).forEach(panel=>{const heading=panel.querySelector('h2')?.textContent||'';panel.dataset.settingsGroup=panel.classList.contains('private-profile-panel')?'private':panel.classList.contains('sync-panel')||heading==='数据安全'?'data':heading==='浏览器插件'?'assistant':['新手教程','启动工作台','你的数据留在本地'].includes(heading)?'help':'general';});
  function settingsTab(id){ui.settings=id;all('[data-settings-tab]').forEach(button=>{const active=button.dataset.settingsTab===id;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});all('[data-settings-group]').forEach(panel=>panel.hidden=panel.dataset.settingsGroup!==id);}
  all('[data-settings-tab]').forEach(button=>button.addEventListener('click',()=>settingsTab(button.dataset.settingsTab)));settingsTab('general');

  // Search all local object types; sensitive profile fields are never indexed.
  async function loadExtra(){
    const results=await Promise.allSettled([api('/api/interview-prep'),fetch('http://127.0.0.1:8776/api/experiences').then(response=>{if(!response.ok)throw new Error('经历未连接');return response.json();})]);
    if(results[0].status==='fulfilled')ui.preps=results[0].value.items||[];
    if(results[1].status==='fulfilled')ui.assets=Array.isArray(results[1].value)?results[1].value:results[1].value.items||[];
    if(byId('commandDialog').open)renderCommand();if(byId('jobDetailDialog').open&&ui.detailTab!=='overview')renderJobDetail();
    if(ui.view==='memo')renderMemo();
    window.dispatchEvent(new CustomEvent('careeros-overview-extras',{detail:{assets:results[1].status==='fulfilled'?ui.assets:null,preps:results[0].status==='fulfilled'?ui.preps:null}}));
  }
  function openCommand(){byId('commandSearch').value='';ui.searchIndex=-1;renderCommand();byId('commandDialog').showModal();byId('commandSearch').focus();loadExtra();}
  byId('openCommandBtn').addEventListener('click',openCommand);
  document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(byId('commandDialog').open)byId('commandDialog').close();else if(!document.querySelector('dialog[open]'))openCommand();}});
  function renderCommand(){
    const query=byId('commandSearch').value.trim().toLowerCase();
    const matches=entry=>!query||[entry.title,entry.subtitle,entry.search].filter(Boolean).join(' ').toLowerCase().includes(query);
    const actions=[{kind:'navigate',id:'dashboard',title:'总览',subtitle:'功能入口、近期重点与求职进展'},{kind:'import',id:'',title:'导入新岗位',subtitle:'链接或招聘文字'},{kind:'navigate',id:'resume',title:'制作岗位简历',subtitle:'确认目标与经历'},{kind:'navigate',id:'vault',title:'经历和项目',subtitle:'维护真实资料'},{kind:'navigate',id:'settings',title:'备份与同步',subtitle:'设置 → 备份与同步'}];
    const collections=[['快捷操作',actions],['Offer 记录',(state.offers||[]).map(offer=>({kind:'offer',id:offer.id,title:offer.company,subtitle:[offer.role,offer.city,offer.archived?'已归档':''].filter(Boolean).join(' · ')}))],['岗位',state.opportunities.map(job=>({kind:'job',id:job.id,title:job.company||'待补充公司',subtitle:job.role||'岗位待补充',search:job.location}))],['经历与项目',ui.assets.map(asset=>({kind:'asset',id:asset.id,title:asset.title,subtitle:[asset.organization,asset.role].filter(Boolean).join(' · '),search:[asset.summary,asset.facts,...(asset.skills||[]),...(asset.domains||[])].join(' ')}))],['简历版本',state.versions.map(version=>({kind:'version',id:version.id,title:version.name||'通用简历',subtitle:[version.target_company,version.target_role].filter(Boolean).join(' · ')}))],['面试准备',ui.preps.map(prep=>({kind:'prep',id:prep.id,title:prep.title,subtitle:prep.summary}))],['面试与笔试题',state.interviewQuestions.map(question=>({kind:'question',id:question.id,title:question.question,subtitle:[question.company,question.paper_name,question.topic].filter(Boolean).join(' · ')}))]];
    commandEntries=[];let html='';
    for(const [label,entries]of collections){const rows=entries.filter(matches).slice(0,query?6:label==='快捷操作'?5:3);if(!rows.length)continue;html+=`<div class="command-group-label">${label}</div>`;for(const entry of rows){const index=commandEntries.push(entry)-1;html+=`<button type="button" class="command-result" data-command-index="${index}"><span class="command-result-glyph" aria-hidden="true">${{job:'▤',offer:'◇',asset:'◇',version:'▧',prep:'◫',question:'?',navigate:'↗',import:'+'}[entry.kind]}</span><span><strong>${text(entry.title)}</strong><small>${text(entry.subtitle||'')}</small></span></button>`;}}
    byId('commandResults').innerHTML=html||'<div class="empty-state compact">没有匹配结果，试试公司名称、项目或题目关键词。</div>';ui.searchIndex=-1;
  }
  byId('commandSearch').addEventListener('input',renderCommand);
  byId('commandSearch').addEventListener('keydown',event=>{if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();if(!commandEntries.length)return;ui.searchIndex=(ui.searchIndex+(event.key==='ArrowDown'?1:-1)+commandEntries.length)%commandEntries.length;all('[data-command-index]').forEach((button,index)=>button.classList.toggle('is-selected',index===ui.searchIndex));byId('commandResults').querySelector(`[data-command-index="${ui.searchIndex}"]`)?.scrollIntoView({block:'nearest'});}if(event.key==='Enter'){event.preventDefault();chooseCommand(Math.max(0,ui.searchIndex));}});
  byId('commandResults').addEventListener('click',event=>{const button=event.target.closest('[data-command-index]');if(button)chooseCommand(Number(button.dataset.commandIndex));});
  async function chooseCommand(index){const entry=commandEntries[index];if(!entry)return;byId('commandDialog').close();
    if(entry.kind==='navigate'){if(goView(entry.id)&&entry.id==='settings')settingsTab('data');}
    if(entry.kind==='import')byId('jobImportDialog').showModal();
    if(entry.kind==='job')openJob(entry.id);
    if(entry.kind==='offer')window.CareerOffers?.openDetail(entry.id);
    if(entry.kind==='version'){if(goView('resume'))renderResumePreview(state.versions.find(item=>item.id===entry.id));}
    if(entry.kind==='asset'){if(goView('vault'))queueVaultAction({type:'careeros-vault-open-experience',id:entry.id});}
    if(entry.kind==='prep'){if(goView('interview_prep'))await window.PrepLibrary?.openById(entry.id);}
    if(entry.kind==='question'){const question=state.interviewQuestions.find(item=>item.id===entry.id);if(question)openInterviewQuestion(question,question.question_type);}
  }

  const originalRenderAll=renderAll;
  renderAll=function(){originalRenderAll();renderPreviewState();showResumeStep(ui.resumeStep);if(byId('jobDetailDialog').open&&ui.detailTab!=='overview')renderJobDetail();
    if(!initialRouteApplied){initialRouteApplied=true;const params=new URLSearchParams(location.search);goView(params.get('view')&&titles[params.get('view')]?params.get('view'):'dashboard',{replace:true,job:Number(params.get('job'))||null});if(params.get('job'))openJob(params.get('job'),{route:false});}
    window.dispatchEvent(new Event('careeros-workspace-updated'));
  };
  window.addEventListener('careeros-data-restored',()=>{ui.assets=[];ui.preps=[];loadExtra();});
  window.addEventListener('careeros-workspace-updated',loadExtra);
  window.addEventListener('message',event=>{if(event.origin===location.origin&&event.data?.type==='interview-prep-saved')loadExtra();});
  window.addEventListener('careeros-prep-list-loaded',event=>{ui.preps=event.detail||[];});
  window.CareerWorkspace={openJob,refreshExtras:loadExtra,renderDashboard,renderMemo};
  showResumeStep(1);loadExtra();
  if(state.opportunities.length)renderAll();
})();
