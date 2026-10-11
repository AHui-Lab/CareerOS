/* Overview: one level of orientation, details on demand. */
(() => {
  'use strict';
  const byId=id=>document.getElementById(id);
  const dialog=byId('overviewDialog');
  let assets=null,preps=null,extrasLoaded=false;
  function renderMetrics(){
    byId('overviewJobsMeta').textContent=`${state.opportunities.length} 个岗位`;
    byId('overviewResumesMeta').textContent=`${state.versions.length} 个简历版本`;
    const written=state.interviewQuestions.filter(item=>item.question_type==='written_test');
    byId('overviewWrittenMeta').textContent=`${new Set(written.map(item=>questionGroupName(item,'written_test'))).size} 套试卷 · ${written.length} 道题`;
    const pending=state.emails.filter(item=>item.status==='pending').length;
    byId('overviewMailMeta').textContent=pending?`${pending} 封待确认`:'暂无待确认邮件';
    byId('overviewAssetsMeta').textContent=assets?`${assets.length} 段经历 · ${assets.filter(item=>item.resume_ready).length} 可用于简历`:extrasLoaded?'经历服务暂未连接':'正在加载经历…';
    byId('overviewPrepsMeta').textContent=preps?`${preps.length} 个准备空间`:extrasLoaded?'准备资料暂未加载':'正在加载准备资料…';
  }
  function renderSchedule(){
    const now=new Date(),summary=CareerScheduleSummary.nearTerm(state.scheduleEvents.filter(event=>{const job=state.opportunities.find(job=>Number(job.id)===Number(event.opportunity_id));return event.source!=='opportunity'||!job||CareerJobOrganization.disposition(job)==='active';}),now);
    const tomorrow=new Date(now.getFullYear(),now.getMonth(),now.getDate()+1);
    const names={[summary.start]:'今天',[CareerScheduleSummary.dateKey(tomorrow)]:'明天',[summary.end]:'后天'};
    byId('overviewScheduleCount').textContent=summary.items.length?String(summary.items.length):'';
    byId('overviewScheduleTitle').parentElement.querySelector('.overview-section-hint').textContent=summary.items.length>3?'今天至后天 · 优先显示前 3 项':'今天、明天、后天';
    byId('overviewScheduleList').innerHTML=summary.items.length?summary.items.slice(0,3).map(item=>{
      const job=state.opportunities.find(job=>Number(job.id)===Number(item.opportunity_id));
      const company=item.company||job?.company||item.title||'日程';
      const type=item.source==='offer'&&item.event_type==='follow_up'?'回复 Offer':EVENT_TYPE[item.event_type]||'其他';
      const target=item.source==='opportunity'?'data-overview-detail="calendar"':`data-overview-event="${esc(item.id)}"`;
      return `<button type="button" class="overview-schedule-row" ${target} aria-label="${esc([names[item.event_date],item.event_time||'时间待定',company,type,item.title].filter(Boolean).join(' · '))}"><span class="overview-schedule-time"><strong>${esc(names[item.event_date])}</strong><small>${esc(item.event_time||'时间待定')}</small></span><span class="overview-schedule-company"><strong title="${esc(company)}">${esc(company)}</strong><small title="${esc(item.title)}">${esc(item.title||job?.role||type)}</small></span><span class="overview-schedule-type ${esc(EVENT_CLASS[item.event_type]||EVENT_CLASS.other)}">${esc(type)}</span></button>`;
    }).join(''):'<div class="overview-schedule-empty"><strong>近三天暂无安排</strong><p>确认笔面试或签约时间后，可以在这里记录。</p><button type="button" class="link-button" data-add-schedule>添加日程 →</button></div>';
  }
  function showTab(tab){
    const names={actions:'行动计划',calendar:'求职日历',recent:'最近关注岗位'};
    byId('overviewDetailTitle').textContent=names[tab];
    dialog.querySelectorAll('[data-overview-tab]').forEach(button=>{const active=button.dataset.overviewTab===tab;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
    dialog.querySelectorAll('[data-overview-panel]').forEach(panel=>panel.hidden=panel.dataset.overviewPanel!==tab);
    dialog.scrollTop=0;
  }
  document.addEventListener('click',event=>{const detail=event.target.closest('[data-overview-detail]');if(detail){showTab(detail.dataset.overviewDetail);if(detail.dataset.overviewDetail==='calendar'){const panel=document.querySelector('.calendar-panel');panel.classList.add('expanded');byId('calendarToggle').textContent='收起月历';byId('calendarToggle').setAttribute('aria-expanded','true');calendarCursor=new Date(new Date().getFullYear(),new Date().getMonth(),1);renderCalendar();}dialog.showModal();}const target=event.target.closest('[data-overview-event]');if(target){const item=state.scheduleEvents.find(item=>String(item.id)===target.dataset.overviewEvent);if(item)openSchedule(item);}});
  dialog.querySelectorAll('[data-overview-tab]').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.overviewTab)));
  // Close the overview before opening a record or navigating, so there is one active surface.
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');
    if(dialog.open&&button?.closest('#overviewDialog')&&button.matches('[data-go-view],[data-open-job],[data-open-event],[data-add-schedule],[data-delay-action],[data-job-resume],[data-job-prep],[data-edit-schedule],[data-calendar-date],#addScheduleBtn'))dialog.close();
  },true);
  window.addEventListener('careeros-view-changed',event=>{if(event.detail.view!=='dashboard'&&dialog.open)dialog.close();if(event.detail.view==='dashboard')window.CareerWorkspace?.refreshExtras();});
  document.querySelector('[data-overview-import]').addEventListener('click',()=>byId('globalAddBtn').click());
  document.querySelector('[data-overview-capture]').addEventListener('click',()=>{if(goView('vault'))byId('vaultQuickAdd').click();});
  document.querySelector('[data-overview-profile]').addEventListener('click',()=>{if(goView('vault'))document.querySelector('[data-vault-view="profile"]').click();});
  window.addEventListener('careeros-overview-extras',event=>{assets=event.detail.assets;preps=event.detail.preps;extrasLoaded=true;renderMetrics();});
  window.addEventListener('careeros-prep-list-loaded',event=>{preps=event.detail||[];renderMetrics();});
  window.addEventListener('careeros-workspace-updated',()=>{renderMetrics();renderSchedule();});
  window.addEventListener('careeros-view-changed',event=>{if(event.detail.view==='dashboard')renderSchedule();});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)renderSchedule();});
  renderMetrics();renderSchedule();
})();
