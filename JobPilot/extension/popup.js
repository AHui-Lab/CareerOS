const API='http://127.0.0.1:8765',EXTENSION_VERSION=chrome.runtime.getManifest().version;
const titleEl=document.querySelector('#pageTitle'),urlEl=document.querySelector('#pageUrl'),saveBtn=document.querySelector('#saveBtn'),fillBtn=document.querySelector('#fillBtn'),statusEl=document.querySelector('#status');
const undoBtn=document.querySelector('#undoBtn');
let page=null,tabId=null,preview=null;
function setStatus(text,type=''){statusEl.textContent=text;statusEl.className=`status ${type||'muted'}`;}

async function readPage(id){
  const [{result}] = await chrome.scripting.executeScript({target:{tabId:id},func:()=>{
    const clean=(v='')=>String(v||'').replace(/\u00a0/g,' ').replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
    const meta=s=>clean(document.querySelector(s)?.getAttribute('content')||'');
    const headings=[...document.querySelectorAll('h1,h2,h3')].map(x=>clean(x.innerText)).filter(x=>x&&x.length<180).slice(0,30);
    const brand=[...document.querySelectorAll('header img,[class*="logo" i] img,[class*="brand" i]')].flatMap(el=>[el.getAttribute?.('alt'),el.getAttribute?.('title'),el.innerText]).map(clean).filter(x=>x&&x.length<80).slice(0,20);
    const findJob=()=>{for(const s of document.querySelectorAll('script[type="application/ld+json"]')){try{const root=JSON.parse(s.textContent||'null');const walk=v=>{if(!v)return null;if(Array.isArray(v)){for(const x of v){const r=walk(x);if(r)return r;}}else if(typeof v==='object'){const t=v['@type'];if((Array.isArray(t)?t:[t]).some(x=>String(x).toLowerCase()==='jobposting'))return v;for(const x of Object.values(v)){const r=walk(x);if(r)return r;}}return null};const hit=walk(root);if(hit)return hit;}catch{}}return null;};
    const job=findJob();const org=job?.hiringOrganization;const company=typeof org==='string'?org:(org?.name||'');const loc=job?.jobLocation;let locationText='';if(loc){const x=Array.isArray(loc)?loc[0]:loc;const a=x?.address||x;if(typeof a==='string')locationText=a;else if(a)locationText=[a.addressLocality,a.addressRegion].filter(Boolean).join(' ');}
    const pageUrl=document.querySelector('link[rel="canonical"]')?.href||location.href;
    const jobDescription=job?.description?clean(new DOMParser().parseFromString(String(job.description),'text/html').body.textContent):'';
    const mainText=jobDescription||clean(document.querySelector('main,[role="main"],article')?.innerText||'');
    return {title:clean(document.title),url:pageUrl,text:clean(document.body?.innerText||'').slice(0,180000),context:{page_url:pageUrl,hostname:location.hostname,pathname:location.pathname,site_name:meta('meta[property="og:site_name"]')||meta('meta[name="application-name"]'),description:meta('meta[name="description"]'),main_text:mainText.slice(0,60000),headings,brand_candidates:brand,job_posting:job?{title:clean(job.title||''),company:clean(company),location:clean(locationText),deadline:clean(job.validThrough||'')}:{} }};
  }});
  return result;
}

async function init(){
  try{
    const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tab?.id||!/^https?:/i.test(tab.url||''))throw new Error('当前页面不是普通网页');
    tabId=tab.id;page=await readPage(tabId);titleEl.textContent=page.title||'未命名页面';urlEl.textContent=page.url;
    const r=await fetch(`${API}/api/health`);if(!r.ok)throw new Error('CareerOS 未启动');const h=await r.json();fillBtn.disabled=false;
    const [previewResponse,versionsResponse]=await Promise.all([
      fetch(`${API}/api/opportunities/preview-page`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(page)}),
      fetch(`${API}/api/resume-versions`)
    ]);
    if(previewResponse.ok){preview=await previewResponse.json();const draft=preview.draft||{};for(const [key,id] of Object.entries({company:'company',role:'role',location:'location',deadline:'deadline',jd_text:'jd'}))document.querySelector('#'+id).value=draft[key]||'';document.querySelector('#review').classList.remove('hidden');document.querySelector('#reviewWarning').textContent=[preview.warning,preview.existing?'此链接已导入。确认后会更新岗位信息并保留投递状态。':'请核对后再导入。'].filter(Boolean).join(' ');saveBtn.textContent=preview.existing?'更新已有职位':'确认导入职位';saveBtn.disabled=false;}
    if(versionsResponse.ok){const versions=(await versionsResponse.json()).items||[];const select=document.querySelector('#resumeVersion');for(const version of versions){const option=document.createElement('option');option.value=String(version.id);option.textContent=[version.target_company,version.target_role,version.created_at].filter(Boolean).join(' · ')||version.name||`版本 ${version.id}`;select.append(option);}}
    try{const frames=await chrome.scripting.executeScript({target:{tabId,allFrames:true},func:()=>Boolean(window.JobPilotAutofill?.hasUndo?.())});undoBtn.disabled=!frames.some(x=>x.result);}catch{}
    const versionNote=h.version&&h.version!==EXTENSION_VERSION?` 扩展 ${EXTENSION_VERSION} / 后端 ${h.version}；接口可用，继续运行。`:'';
    setStatus(`CareerOS ${h.version||''} 已连接。${h.careervault?.available?'经历资产已连接。':'经历资产未连接。'}${preview?'请核对岗位字段后导入。':'岗位解析失败，可在工作台粘贴职位文字导入。'}${versionNote}`,preview?'ok':'warn');
  }catch(e){titleEl.textContent='无法连接';setStatus(e.message,'error');}
}

saveBtn.addEventListener('click',async()=>{
  if(!page)return;saveBtn.disabled=true;saveBtn.textContent='保存中…';
  try{const review={company:document.querySelector('#company').value.trim(),role:document.querySelector('#role').value.trim(),location:document.querySelector('#location').value.trim(),deadline:document.querySelector('#deadline').value.trim(),jd_text:document.querySelector('#jd').value.trim()};if(!review.company||!review.role)throw new Error('请先补全公司和岗位');const res=await fetch(`${API}/api/opportunities/import-page`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...page,review,refresh_existing:true})});const data=await res.json();if(!res.ok)throw new Error(data.detail||'导入失败');setStatus(`${data.refreshed?'已更新':'已导入'}职位：${data.item?.company||'待补充公司'} · ${data.item?.role||'待补充岗位'}。请在工作台确认 JD 和截止时间。`,'ok');saveBtn.textContent='已保存';}
  catch(e){setStatus(`导入失败：${e.message}`,'error');saveBtn.disabled=false;saveBtn.textContent='重试导入';}
});

fillBtn.addEventListener('click',async()=>{
  if(!tabId)return;fillBtn.disabled=true;fillBtn.textContent='正在填写…';
  try{
    const versionId=document.querySelector('#resumeVersion').value;const res=await fetch(`${API}/api/autofill/package${versionId?`?version_id=${encodeURIComponent(versionId)}`:'?base_only=true'}`);const data=await res.json();if(!res.ok)throw new Error(data.detail||'读取资料失败');
    const pack=data.package||{},structured=data.structured||{};if(!Object.values(pack).some(Boolean)&&!(structured.education||[]).length)throw new Error('没有可填写资料，请先在 CareerOS 生成一版岗位简历');
    await chrome.scripting.executeScript({target:{tabId,allFrames:true},files:['autofill-runtime.js']});
    const frameResults = await chrome.scripting.executeScript({target:{tabId,allFrames:true},args:[structured,pack,{allowSensitive:document.querySelector('#allowSensitive').checked,overwriteFilled:document.querySelector('#overwriteFilled').checked,addRows:document.querySelector('#addRows').checked}],func:async(structured,pack,options)=>{
      if(!window.JobPilotAutofill)throw new Error('JobPilot Autofill Runtime 未加载');
      return await window.JobPilotAutofill.run(structured,pack,options);
    }});
    const result=frameResults.map(x=>x.result).filter(Boolean).reduce((total,item)=>({
      ...total,
      adapter:item.adapter||total.adapter,
      scalar_filled:total.scalar_filled+(item.scalar_filled||0),
      repeated_fields:total.repeated_fields+(item.repeated_fields||0),
      repeated_rows:total.repeated_rows+(item.repeated_rows||0),
      rows_added:total.rows_added+(item.rows_added||0),
      skipped_files:total.skipped_files+(item.skipped_files||0),
      total_filled:total.total_filled+(item.total_filled||0),
      undo_available:total.undo_available+(item.undo_available||0),
      filled_labels:[...total.filled_labels,...(item.filled_labels||[])],
      skipped_existing:[...total.skipped_existing,...(item.skipped_existing||[])],
      skipped_manual:[...total.skipped_manual,...(item.skipped_manual||[])],
      repeated_sections:[...total.repeated_sections,...(item.repeated_sections||[])],
      unmatched_controls:[...(total.unmatched_controls||[]),...(item.unmatched_controls||[])]
    }),{adapter:'通用网页',scalar_filled:0,repeated_fields:0,repeated_rows:0,rows_added:0,skipped_files:0,total_filled:0,undo_available:0,filled_labels:[],skipped_existing:[],skipped_manual:[],repeated_sections:[],unmatched_controls:[]});
    const version=data.resume_version?.name?`\n使用简历：${data.resume_version.name}`:'\n仅使用当前基础资料';
    const rows=result.repeated_rows?`，经历行 ${result.repeated_rows} 组 / ${result.repeated_fields} 个字段`:'';
    const added=result.rows_added?`，自动新增 ${result.rows_added} 行`:'';
    const files=result.skipped_files?`，${result.skipped_files} 个文件框需手动上传`:'';
    const unmatched=result.unmatched_controls?.length?`\n未识别字段：${[...new Set(result.unmatched_controls)].slice(0,6).join(' / ')}`:'';
    setStatus(`${result.adapter} 适配 · 已填写 ${result.scalar_filled} 个基础字段${rows}${added}${files}${version}${unmatched}\n请逐项检查后再提交。`,result.total_filled?'ok':'warn');
    const lines=[];const unique=items=>[...new Set(items)].filter(Boolean).slice(0,12);
    if(result.filled_labels.length)lines.push(`已填：${unique(result.filled_labels).join(' / ')}`);
    if(result.repeated_sections.length)lines.push(`经历：${result.repeated_sections.map(x=>`${x.kind} ${x.fields} 字段`).join(' / ')}`);
    if(result.skipped_existing.length)lines.push(`保留原值：${unique(result.skipped_existing).join(' / ')}`);
    if(result.skipped_manual.length)lines.push(`需人工判断或授权：${unique(result.skipped_manual).join(' / ')}`);
    if(result.skipped_files)lines.push(`文件上传框：${result.skipped_files} 个，需手动处理`);
    document.querySelector('#fillReportBody').textContent=lines.join('\n')||'本次没有改动页面字段。';
    document.querySelector('#fillReport').classList.remove('hidden');
    undoBtn.disabled=!result.undo_available;
  }catch(e){setStatus(`填表失败：${e.message}`,'error');}
  finally{fillBtn.disabled=false;fillBtn.textContent='智能填写当前页面';}
});

undoBtn.addEventListener('click',async()=>{if(!tabId)return;undoBtn.disabled=true;try{const frames=await chrome.scripting.executeScript({target:{tabId,allFrames:true},func:()=>window.JobPilotAutofill?.undo?.()||{restored:0}});const count=frames.reduce((n,x)=>n+(x.result?.restored||0),0);setStatus(`已撤销 ${count} 个已填字段。自动新增的经历行需要手动删除。`,'ok');document.querySelector('#fillReport').classList.add('hidden');}catch(e){setStatus(`撤销失败：${e.message}`,'error');undoBtn.disabled=false;}});

init();
