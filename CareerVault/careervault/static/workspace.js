(() => {
  'use strict';
  const originalCard=expCard;
  expCard=function(item){const html=originalCard(item);const files=item.attachments?.length||0;return html.replace('<div class="card experience-card"','<button type="button" class="card experience-card"').replace(/<\/div>$/,`<div class="cv-card-footer"><span class="${item.resume_ready?'cv-ready':'cv-pending'}">${item.resume_ready?'✓ 可用于简历':'待整理 · 未用于简历'}</span><span>${files} 份证明材料 · 查看详情 →</span></div></button>`);};
  const originalForm=experienceForm;
  experienceForm=function(item){return originalForm(item).replace('<div class="full row wrap">',`<label class="full cv-resume-ready"><input id="f-resume-ready" type="checkbox" data-exp-field ${item.resume_ready?'checked':''}>已核对事实，允许这条经历用于岗位简历</label><div id="cvEditorSaveState" class="full cv-save-status" role="status">${item.id?'已载入 · 停止输入后自动保存':'新增记录 · 填写后点击创建记录'}</div><div class="full row wrap">`);};
  const originalPayload=payload;
  payload=function(type){const value=originalPayload(type),ready=$('#f-resume-ready');if(ready)value.resume_ready=ready.checked;return value;};
  const originalState=state;
  state=function(message){originalState(message);if($('#cvEditorSaveState'))$('#cvEditorSaveState').textContent=message;if(window.parent!==window)window.parent.postMessage({type:'careeros-vault-save-state',pending:/未保存|保存中|保存失败|请补充/.test(message)},'*');};
  let readyFilter='all';
  const originalRender=renderExperiences;
  renderExperiences=async function(){await originalRender();const toolbar=$('.experience-toolbar');if(!toolbar)return;
    const summary=document.createElement('div');summary.className='cv-summary';summary.innerHTML=`<span><strong>${experiences.length}</strong>条经历</span><span><strong>${experiences.filter(item=>item.resume_ready).length}</strong>可用于简历</span><span><strong>${experiences.filter(item=>!item.resume_ready).length}</strong>待整理</span>`;toolbar.before(summary);
    const filters=document.createElement('div');filters.className='cv-filter-switch';filters.setAttribute('role','group');filters.setAttribute('aria-label','按简历可用状态筛选');filters.innerHTML=[['all','全部状态'],['ready','可用于简历'],['pending','待整理']].map(([id,label])=>`<button type="button" data-ready-filter="${id}">${label}</button>`).join('');
    if(document.body.classList.contains('embedded-mode'))$('.experience-tabs').append(filters);else toolbar.append(filters);
    function filter(){const map=new Map(experiences.map(item=>[item.id,item]));$$('.experience-card').forEach(card=>{const item=map.get(card.dataset.id);card.hidden=readyFilter==='ready'?!item?.resume_ready:readyFilter==='pending'?!!item?.resume_ready:false;});$$('[data-ready-filter]').forEach(button=>{const active=button.dataset.readyFilter===readyFilter;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});}
    filters.addEventListener('click',event=>{const button=event.target.closest('[data-ready-filter]');if(button){readyFilter=button.dataset.readyFilter;filter();}});
    $('#experienceSearch').addEventListener('input',filter);$('.experience-tabs')?.addEventListener('click',()=>requestAnimationFrame(filter));filter();
  };
  window.addEventListener('message',event=>{if(event.origin!=='http://127.0.0.1:8765'&&event.origin!=='http://localhost:8765')return;if(event.data?.type==='careeros-theme')document.documentElement.dataset.theme=event.data.theme==='dark'?'dark':'light';});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!$('#modal').classList.contains('hidden'))closeModal();});
  const modal=$('#modal'),card=$('#modalCard');
  let lastFocus=null;
  new MutationObserver(()=>{
    const open=!modal.classList.contains('hidden');
    document.body.classList.toggle('capture-portal-open',open&&window.parent!==window);
    if(window.parent!==window)window.parent.postMessage({type:'careeros-vault-editor-state',open},'*');
    card.setAttribute('role','dialog');card.setAttribute('aria-modal',String(open));
    const heading=card.querySelector('h2');if(heading){heading.id='cvModalTitle';card.setAttribute('aria-labelledby','cvModalTitle');}
    if(open){lastFocus=document.activeElement;document.body.style.overflow='hidden';(card.querySelector('#f-title')||card.querySelector('input:not([type=hidden]),textarea,select,button'))?.focus({preventScroll:true});}
    else{document.body.style.overflow='';if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});}
  }).observe(modal,{attributes:true,attributeFilter:['class']});
  document.addEventListener('keydown',event=>{if(event.key!=='Tab'||modal.classList.contains('hidden'))return;const controls=[...card.querySelectorAll('button,input:not([type=hidden]),select,textarea,summary,a[href]')].filter(el=>!el.disabled&&el.getClientRects().length&&![...card.querySelectorAll('details:not([open])')].some(group=>group.contains(el)&&!group.querySelector('summary')?.contains(el)));if(!controls.length)return;const first=controls[0],last=controls[controls.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}});
  window.addEventListener('load',()=>{if($('#experiences').classList.contains('active'))renderExperiences();if(window.parent!==window)window.parent.postMessage({type:'careeros-vault-ready'},'*');});
  // Apply the new card presentation to an already-loaded initial list.
  if(experiences.length)renderExperiences();
})();
