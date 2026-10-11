/* A single capture-and-organize flow over the existing fact schema. */
(() => {
  'use strict';
  const bodyLabels={summary:'完整经历介绍',facts:'完整事实记录',results:'完整结果记录',notes:'备注'};
  function formModel(item={}){
    const details=item.details||{};
    const brief=item.type==='project'&&['project_pitch','personal_contribution','project_outcome'].some(key=>String(details[key]||'').trim());
    const content=brief?'details.personal_contribution':item.facts?'facts':item.summary?'summary':'facts';
    const result=brief?'details.project_outcome':'results';
    const intro=brief?'details.project_pitch':content==='summary'?null:'summary';
    const values={title:item.title||'',organization:item.organization||'',role:item.role||'',start:item.start||'',end:item.end||'',type:item.type||'project',skills:(item.skills||[]).join(', '),domains:(item.domains||[]).join(', ')};
    const mapped={};
    for(const key of new Set([content,result,intro,...Object.keys(bodyLabels),'details.hr_intro','details.award_level','details.registration_number'].filter(Boolean))){
      mapped[key]=key.startsWith('details.')?String(details[key.slice(8)]??''):String(item[key]??'');
    }
    if(!mapped['details.registration_number'])mapped['details.registration_number']=String(details.patent_number||details.certificate_number||'');
    return {brief,content,result,intro,values,mapped,archive:Object.keys(bodyLabels).filter(key=>![content,result,intro].includes(key))};
  }
  function makePayload(base={},values={},mapped={}){
    const result={type:values.type||base.type||'project',title:base.title||'',organization:base.organization||'',role:base.role||'',start:base.start||'',end:base.end||'',status:base.status||'draft',resume_ready:!!base.resume_ready,domains:[...(base.domains||[])],skills:[...(base.skills||[])],related_experience_ids:[...(base.related_experience_ids||[])],details:{...(base.details||{})},summary:base.summary||'',facts:base.facts||'',results:base.results||'',notes:base.notes||''};
    for(const key of ['title','organization','role','start','end'])if(Object.hasOwn(values,key))result[key]=String(values[key]).trim();
    if(Object.hasOwn(values,'resume_ready'))result.resume_ready=!!values.resume_ready;
    for(const key of ['skills','domains'])if(Object.hasOwn(values,key)&&values[key]!== (base[key]||[]).join(', '))result[key]=String(values[key]).split(/[,，]/).map(value=>value.trim()).filter(Boolean);
    for(const [key,value] of Object.entries(mapped)){
      if(key.startsWith('details.')){
        const name=key.slice(8),previous=formModel(base).mapped[key];
        if(String(value)!==previous){result.details[name]=String(value);if(name==='registration_number'){if(result.type==='patent')result.details.patent_number=String(value);if(result.type==='certificate')result.details.certificate_number=String(value);}}
      }else if(Object.hasOwn(bodyLabels,key))result[key]=String(value);
    }
    return result;
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={formModel,makePayload};
  if(typeof document==='undefined')return;
  const escape=esc;
  const read=key=>document.getElementById(key);
  let scope='all',category='all',query='',request=0;
  let unsavedNew=false;
  document.addEventListener('input',event=>{if(event.target.closest('#captureEditor')&&!currentExperience){unsavedNew=true;state('未保存…');}});
  window.addEventListener('beforeunload',event=>{if(unsavedNew&&!currentExperience&&!read('modal').classList.contains('hidden')){event.preventDefault();event.returnValue='';}});
  const field=(target,label,value,rows=3,placeholder='')=>`<label class="full capture-field">${label}<textarea data-exp-field data-capture-target="${target}" rows="${rows}" placeholder="${escape(placeholder)}">${escape(value||'')}</textarea></label>`;
  experienceFields=function(item={}){
    const model=formModel(item);
    return `<label class="full capture-field">经历名称<input data-exp-field id="f-title" value="${escape(item.title||'')}" maxlength="200" placeholder="例如：割草机定位项目 / 软件开发实习 / 传感器竞赛获奖" required></label>
      ${model.brief?'<p class="full capture-context">这里编辑简历用的短表述，已有完整记录保留在“更多资料”中。</p>':''}
      ${field(model.content,'我做了什么',model.mapped[model.content],4,'先记录真实动作和负责的部分，可以直接粘贴已有内容。')}
      ${field(model.result,'结果或收获（可稍后补充）',model.mapped[model.result],2,'交付了什么、验证到哪一步，或者获得了什么。没有数字也可以先记录。')}
      <details class="full capture-extra"><summary>时间、单位与角色 <span>可选</span></summary><div class="form-grid capture-metadata"><label>单位 / 团队<input data-exp-field id="f-org" value="${escape(item.organization||'')}" placeholder="学校、公司或个人项目"></label><label>我的角色<input data-exp-field id="f-role" value="${escape(item.role||'')}" placeholder="负责的工作或担任的职位"></label>${dateRangeFields(item)}</div></details>
      <details class="full capture-extra"><summary>更多资料 <span>介绍、标签、原始记录</span></summary><div class="capture-extra-fields">
      ${model.intro?field(model.intro,'一句话介绍',model.mapped[model.intro],2,'这段经历解决了什么问题？'):''}
      ${model.archive.map(key=>field(key,bodyLabels[key],model.mapped[key],key==='notes'?3:5)).join('')}
      <div class="form-grid"><label>技能标签<input data-exp-field id="captureSkills" value="${escape((item.skills||[]).join(', '))}" placeholder="如：C、STM32、BLE"></label><label>相关方向<input data-exp-field id="captureDomains" value="${escape((item.domains||[]).join(', '))}" placeholder="如：嵌入式、算法"></label></div>
      ${field('details.hr_intro','口述练习（可选）',model.mapped['details.hr_intro'],3)}
      ${item.type==='award'?`<label>奖项级别<select data-exp-field data-capture-target="details.award_level">${awardLevelOptions(item.details?.award_level||'')}</select></label>`:''}
      ${['patent','certificate'].includes(item.type)?`<label>登记号<input data-exp-field data-capture-target="details.registration_number" value="${escape(model.mapped['details.registration_number'])}"></label>`:''}
      </div></details>`;
  };
  experienceForm=function(item={}){
    const attachments=(item.attachments||[]).map(file=>`<a class="capture-file" href="/api/files/raw?path=${encodeURIComponent(String(file.path||'').replace(/^vault\//,''))}" target="_blank" rel="noopener"><span>${escape(file.name)}</span><small>${Math.max(1,Math.ceil(file.size/1024))} KB · 查看 ↗</small></a>`).join('');
    return `<div class="topbar capture-editor-heading"><div><h2>${item.id?'整理经历':'记录一段经历'}</h2><div class="muted">${item.id?'补充内容，停止输入后自动保存。':'先记下来，时间和其它资料可以以后补充。'}</div></div><div class="capture-heading-tools"><label class="capture-type-label">类型<select id="f-type">${typeOptions(item.type||'project')}</select></label><button class="btn ghost" id="closeModal" type="button">${item.id?'完成':'取消'}</button></div></div>
      <div id="captureEditor" class="form form-grid compact-experience-form capture-editor"><div class="capture-editor-content"><div class="full form-grid" id="experienceFields">${experienceFields(item)}</div>
      ${item.id?`<section class="full capture-evidence"><div class="capture-evidence-heading"><h3>证明材料</h3><button class="btn ghost" id="uploadBtn" type="button">+ 添加材料</button><input id="fileInput" type="file" hidden></div>${attachments||'<p class="muted">证书、项目截图或文档可以直接加到这条经历。</p>'}</section>`:'<p class="full capture-context">保存后可以添加证书、截图和文档。</p>'}
      </div><div class="full capture-save-footer"><label class="cv-resume-ready"><input id="f-resume-ready" type="checkbox" data-exp-field ${item.resume_ready?'checked':''}>已整理好，可用于简历</label><div class="capture-save-actions"><span id="cvEditorSaveState" role="status" class="cv-save-status">${item.id?'已载入':'尚未保存'}</span><button id="saveExp" class="btn" type="button">${item.id?'保存':'保存经历'}</button>${item.id?'<details class="capture-delete-menu"><summary aria-label="更多经历操作">···</summary><button id="deleteExp" class="btn danger" type="button">删除这条经历</button></details>':''}</div></div></div>`;
  };
  payload=function(typeOverride){
    const values={type:typeOverride||read('f-type').value,resume_ready:read('f-resume-ready')?.checked??!!editingExperience.resume_ready};
    for(const [key,id] of Object.entries({title:'f-title',organization:'f-org',role:'f-role',start:'f-start',end:'f-end',skills:'captureSkills',domains:'captureDomains'}))if(read(id))values[key]=read(id).value;
    if(read('f-current')?.checked)values.end='至今';
    const mapped={};document.querySelectorAll('[data-capture-target]').forEach(element=>mapped[element.dataset.captureTarget]=element.value);
    return makePayload(editingExperience,values,mapped);
  };
  expCard=function(item){
    const details=item.details||{},description=details.personal_contribution||item.facts||details.project_pitch||item.summary||'',outcome=details.project_outcome||item.results||'';
    const meta=[item.organization&&!String(item.title||'').includes(item.organization)?item.organization:'',item.role,experienceDateText(item)].filter(Boolean).join(' · ');
    const missing=!description.trim()?'补充经历内容':!outcome.trim()&&['project','internship','work'].includes(item.type)?'补充结果或收获':'整理后可加入简历';
    return `<button type="button" class="card experience-card capture-card" data-id="${escape(item.id)}"><div class="row"><strong>${escape(item.title||item.organization||'未命名经历')}</strong><span class="status">${escape(TYPE_LABELS[item.type]||item.type)}</span></div>${meta?`<div class="muted capture-card-meta">${escape(meta)}</div>`:''}<p class="capture-card-copy">${escape(compactText(description,210)||'还没有记录具体内容，打开后可以继续补充。')}</p>${outcome?`<p class="capture-card-result">${escape(compactText(outcome,120))}</p>`:''}<div class="cv-card-footer"><span class="${item.resume_ready?'cv-ready':'cv-pending'}">${item.resume_ready?'可用于简历':'待整理'}</span><span>${item.resume_ready?'':escape(missing)}${item.attachments?.length?`${item.resume_ready?'':' · '}${item.attachments.length} 份证明材料`:''} · 打开 →</span></div></button>`;
  };
  function matchingItems(){
    const group=experienceCategories.find(item=>item.id===category);
    return experiences.filter(item=>(scope==='all'||(scope==='ready'?item.resume_ready:!item.resume_ready))&&(category==='all'||group&&matchesCategory(item,group))&&experienceMatchesSearch(item,query.toLowerCase()));
  }
  function draw(){
    const box=read('experienceList');if(!box||!read('captureScopeTabs'))return;
    const items=matchingItems();
    box.innerHTML=items.length?`<div class="list capture-list">${items.map(expCard).join('')}</div>`:`<div class="capture-empty"><h3>${query?'没有匹配的经历':scope==='pending'?'暂时没有待整理经历':scope==='ready'?'还没有可用于简历的经历':'还没有记录经历'}</h3><p>${query?'试试名称、单位或技能关键词。':scope==='ready'?'打开一条经历，核对内容后标记为可用于简历。':'先记下名称和你做过的事，之后可以继续完善。'}</p><button type="button" class="btn ghost" id="captureEmptyAdd">记录经历</button></div>`;
    for(const [name,test] of [['all',()=>true],['pending',item=>!item.resume_ready],['ready',item=>item.resume_ready]]){
      const button=document.querySelector(`[data-capture-scope="${name}"]`),count=experiences.filter(test).length;button.classList.toggle('active',scope===name);button.setAttribute('aria-pressed',String(scope===name));button.querySelector('span').textContent=count;
    }
    read('captureListCount').textContent=query||category!=='all'?`${items.length} 条匹配`:`${items.length} 条经历`;
    wireExperienceCards();read('captureEmptyAdd')?.addEventListener('click',()=>openExperience());
  }
  renderExperiences=async function(){
    const token=++request;
    try{
      const [items]=await Promise.all([api('/api/experiences'),loadExperienceCategories()]);if(token!==request)return;experiences=items;
      if(category!=='all'&&!experienceCategories.some(item=>item.id===category))category='all';
      read('experiences').classList.add('capture-active');
      read('experiences').innerHTML=`<div class="topbar"><div><h1>我的经历</h1><p class="muted">先记录，逐步整理，再用于简历。</p></div><div class="row"><button class="btn ghost" id="manageCategories" type="button">管理分类</button><button class="btn" id="innerNewExp" type="button">+ 记录经历</button></div></div>
      <div class="capture-library-toolbar"><div id="captureScopeTabs" class="capture-scope-tabs" role="group" aria-label="经历整理状态"><button type="button" data-capture-scope="all">全部经历 <span>0</span></button><button type="button" data-capture-scope="pending">待整理 <span>0</span></button><button type="button" data-capture-scope="ready">可用于简历 <span>0</span></button></div><div class="capture-library-filters"><input id="experienceSearch" type="search" aria-label="搜索经历" placeholder="搜索名称、单位或技能" value="${escape(query)}"><select id="captureCategory" aria-label="经历类型"><option value="all">全部类型</option>${experienceCategories.map(item=>`<option value="${escape(item.id)}" ${category===item.id?'selected':''}>${escape(item.label)}</option>`).join('')}</select></div></div><div class="capture-list-label"><span id="captureListCount"></span><span>打开一条即可继续整理</span></div><div id="experienceList"></div>`;
      read('experienceSearch').addEventListener('input',()=>{query=read('experienceSearch').value.trim();draw();});
      read('captureCategory').addEventListener('change',()=>{category=read('captureCategory').value;draw();});
      read('captureScopeTabs').addEventListener('click',event=>{const button=event.target.closest('[data-capture-scope]');if(button){scope=button.dataset.captureScope;draw();}});
      read('innerNewExp').onclick=()=>openExperience();read('manageCategories').onclick=openCategoryManager;draw();
    }catch(error){if(token!==request)return;read('experiences').innerHTML=`<div class="capture-empty"><h3>经历暂未载入</h3><p>${escape(error.message)}</p><button id="captureRetry" class="btn ghost" type="button">重新加载</button></div>`;read('captureRetry').onclick=renderExperiences;}
  };
  const beforeState=state;
  state=function(message){beforeState(message);if(message.startsWith('✓ 已保存'))draw();};
  window.VaultCapture={formModel,makePayload,editorClosed(){if(unsavedNew){unsavedNew=false;state('已取消未保存的录入');}},refreshItem(item){experiences=experiences.map(value=>value.id===item.id?item:value);draw();},async afterCreate(item){
    unsavedNew=false;
    editorSession++;currentExperience=null;editingExperience={};clearTimeout(saveTimer);saveTimer=null;read('modal').classList.add('hidden');
    query='';category='all';scope=item.resume_ready?'ready':'pending';await renderExperiences();
    const card=document.querySelector(`.experience-card[data-id="${CSS.escape(item.id)}"]`);card?.classList.add('capture-just-saved');
    read('captureListCount').textContent='已保存，之后可以继续整理';
  }};
  window.addEventListener('load',()=>{if(read('experiences').classList.contains('active'))renderExperiences();});
})();
