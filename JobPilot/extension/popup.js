const API='http://127.0.0.1:8765',EXTENSION_VERSION=chrome.runtime.getManifest().version;
const titleEl=document.querySelector('#pageTitle'),urlEl=document.querySelector('#pageUrl'),saveBtn=document.querySelector('#saveBtn'),fillBtn=document.querySelector('#fillBtn'),statusEl=document.querySelector('#status');
let page=null,tabId=null;
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
    return {title:clean(document.title),url:pageUrl,text:clean(document.body?.innerText||'').slice(0,180000),context:{page_url:pageUrl,hostname:location.hostname,pathname:location.pathname,site_name:meta('meta[property="og:site_name"]')||meta('meta[name="application-name"]'),description:meta('meta[name="description"]'),headings,brand_candidates:brand,job_posting:job?{title:clean(job.title||''),company:clean(company),location:clean(locationText),deadline:clean(job.validThrough||'')}:{} }};
  }});
  return result;
}

async function init(){
  try{
    const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tab?.id||!/^https?:/i.test(tab.url||''))throw new Error('当前页面不是普通网页');
    tabId=tab.id;page=await readPage(tabId);titleEl.textContent=page.title||'未命名页面';urlEl.textContent=page.url;
    const r=await fetch(`${API}/api/health`);if(!r.ok)throw new Error('CareerOS 未启动');const h=await r.json();saveBtn.disabled=false;fillBtn.disabled=false;
    const versionNote=h.version&&h.version!==EXTENSION_VERSION?` 扩展 ${EXTENSION_VERSION} / 后端 ${h.version}；接口可用，继续运行。`:'';
    setStatus(`CareerOS ${h.version||''} 已连接。${h.careervault?.available?'经历资产已连接。':'经历资产未连接。'}${versionNote}`,'ok');
  }catch(e){titleEl.textContent='无法连接';setStatus(e.message,'error');}
}

saveBtn.addEventListener('click',async()=>{
  if(!page)return;saveBtn.disabled=true;saveBtn.textContent='保存中…';
  try{const res=await fetch(`${API}/api/opportunities/import-page`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(page)});const data=await res.json();if(!res.ok)throw new Error(data.detail||'导入失败');setStatus(`已导入职位：${data.item?.company||'待补充公司'} · ${data.item?.role||'待补充岗位'}`,'ok');saveBtn.textContent='已导入';}
  catch(e){setStatus(`导入失败：${e.message}`,'error');saveBtn.disabled=false;saveBtn.textContent='重试导入';}
});

fillBtn.addEventListener('click',async()=>{
  if(!tabId)return;fillBtn.disabled=true;fillBtn.textContent='正在填写…';
  try{
    const res=await fetch(`${API}/api/autofill/package`);const data=await res.json();if(!res.ok)throw new Error(data.detail||'读取资料失败');
    const pack=data.package||{},structured=data.structured||{};if(!Object.values(pack).some(Boolean)&&!(structured.education||[]).length)throw new Error('没有可填写资料，请先在 CareerOS 生成一版岗位简历');
    await chrome.scripting.executeScript({target:{tabId,allFrames:true},files:['autofill-runtime.js']});
    const frameResults = await chrome.scripting.executeScript({target:{tabId,allFrames:true},args:[structured,pack,{allowSensitive:document.querySelector('#allowSensitive').checked}],func:async(structured,pack,options)=>{
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
      total_filled:total.total_filled+(item.total_filled||0)
    }),{adapter:'通用网页',scalar_filled:0,repeated_fields:0,repeated_rows:0,rows_added:0,skipped_files:0,total_filled:0});
    const version=data.resume_version?.name?`\n使用简历：${data.resume_version.name}`:'\n未找到定制简历，使用当前基础资料';
    const rows=result.repeated_rows?`，经历行 ${result.repeated_rows} 组 / ${result.repeated_fields} 个字段`:'';
    const added=result.rows_added?`，自动新增 ${result.rows_added} 行`:'';
    const files=result.skipped_files?`，${result.skipped_files} 个文件框需手动上传`:'';
    setStatus(`${result.adapter} 适配 · 已填写 ${result.scalar_filled} 个基础字段${rows}${added}${files}${version}\n请逐项检查后再提交。`,result.total_filled?'ok':'warn');
  }catch(e){setStatus(`填表失败：${e.message}`,'error');}
  finally{fillBtn.disabled=false;fillBtn.textContent='智能填写当前页面';}
});

init();
