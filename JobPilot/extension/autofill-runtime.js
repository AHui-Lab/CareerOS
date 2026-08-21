(()=>{
  if(window.JobPilotAutofill)return;

  const norm=s=>String(s||'').toLowerCase().replace(/\u00a0/g,' ').replace(/[\s:：*（）()\[\]_-]+/g,'');
  const clean=s=>String(s||'').replace(/\u00a0/g,' ').replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const risky=/薪资|工资|期望薪资|调剂|服从|加班|政治|党派|健康|疾病|婚姻|家庭|亲属|民族|宗教|身份证|证件号|是否愿意|是否接受/i;
  const forbiddenButton=/提交|保存并提交|下一步|完成申请|确认投递|立即申请|投递简历|submit|apply now/i;

  const scalarAliases={
    name:['姓名','名字','name','full name','username'],phone:['手机号','手机号码','联系电话','mobile','phone','tel'],email:['邮箱','电子邮箱','email','e-mail'],
    current_city:['现居地','当前城市','居住城市','所在城市','现居城市'],school:['毕业院校','学校名称','学校','院校','university','school'],college:['学院','院系','department'],major:['专业名称','所学专业','专业','major'],degree:['最高学历','学历','学位','degree'],education_start_date:['入学时间','入学日期','教育开始时间'],degree_type:['学位类型','学历类型','degree type'],graduation_date:['毕业时间','毕业日期','毕业年份','graduation'],gpa:['gpa','绩点'],rank:['专业排名','成绩排名','排名'],birth_date:['出生日期','生日','birth'],gender:['性别','gender'],id_type:['证件类型','证件类别','id type'],id_number:['身份证号','证件号码','证件号','id number'],ethnicity:['民族','ethnicity'],native_place:['籍贯','户籍所在地','生源地','native place'],political_status:['政治面貌','政治身份','political'],marital_status:['婚姻状况','婚姻','marital'],household_registration:['户口所在地','户籍','户口'],address:['详细地址','通讯地址','联系地址','address'],emergency_contact_name:['紧急联系人','紧急联系人姓名'],emergency_contact_phone:['紧急联系人电话','紧急联系电话'],portfolio_url:['作品集','作品链接','portfolio'],website:['个人网站','个人主页','website'],github_url:['github'],self_intro:['自我介绍','个人介绍','自我评价','个人优势','个人简介','summary','introduction'],education_experience:['教育经历','教育背景'],internship_experience:['实习经历','工作经历','实习经验','工作经验'],project_experience:['项目经历','项目经验','项目介绍'],campus_experience:['校园经历','学生工作','社团经历','校园活动'],research_experience:['科研经历','研究经历','科研项目'],awards:['荣誉奖项','获奖经历','奖励情况','奖项'],skills:['专业技能','技能特长','技能','skills']
  };

  const repeatedAliases={
    education:{school:['学校','院校','毕业院校','学校名称','school','university'],college:['学院','院系','college','department'],major:['专业','专业名称','所学专业','major'],degree:['学历','学位','degree'],start_date:['入学时间','开始时间','起始时间','入学日期','start'],end_date:['毕业时间','结束时间','毕业日期','毕业年份','end','graduation'],gpa:['gpa','绩点'],rank:['排名','专业排名']},
    internships:{organization:['公司','单位','企业','组织','实习单位','公司名称','company','organization'],title:['岗位','职位','职务','实习岗位','position','role','title'],start_date:['开始时间','入职时间','起始时间','start'],end_date:['结束时间','离职时间','截止时间','end'],location:['地点','工作地点','城市','location'],description:['工作内容','实习内容','职责','经历描述','工作描述','description','details']},
    projects:{organization:['组织','单位','项目单位','organization'],title:['项目名称','项目标题','项目','project name','title'],start_date:['开始时间','起始时间','start'],end_date:['结束时间','截止时间','end'],location:['地点','location'],description:['项目描述','项目内容','职责','主要工作','description','details']},
    research:{organization:['组织','单位','实验室','研究机构','organization'],title:['科研项目','研究项目','项目名称','课题名称','title'],start_date:['开始时间','起始时间','start'],end_date:['结束时间','截止时间','end'],description:['研究内容','项目描述','科研内容','description','details']},
    campus:{organization:['组织','社团','学院','部门','organization'],title:['职务','角色','学生工作','活动名称','title','role'],start_date:['开始时间','start'],end_date:['结束时间','end'],description:['经历描述','工作内容','活动内容','description','details']}
  };

  const sectionAliases={education:['教育经历','教育背景','学历信息','教育信息'],internships:['实习经历','工作经历','实习经验','工作经验'],projects:['项目经历','项目经验','项目实践'],research:['科研经历','研究经历','科研项目'],campus:['校园经历','学生工作','社团经历']};

  function detectAdapter(host=location.hostname){
    const h=String(host||'').toLowerCase();
    if(/(^|\.)(italent\.cn|beisen\.com|beisencloud\.com)$/.test(h)||h.includes('beisen'))return {id:'beisen',label:'北森 / iTalent'};
    if(/(^|\.)mokahr\.com$/.test(h)||h.includes('moka'))return {id:'moka',label:'Moka'};
    if(/(^|\.)nowcoder\.com$/.test(h)||h.includes('nowcoder'))return {id:'nowcoder',label:'牛客'};
    return {id:'generic',label:'通用网页'};
  }

  function labelFor(el){
    const parts=[];
    if(el.id){const l=document.querySelector(`label[for="${CSS.escape(el.id)}"]`);if(l)parts.push(l.innerText);}
    const parent=el.closest('label');if(parent)parts.push(parent.innerText);
    for(const a of ['placeholder','name','id','aria-label','title','data-label'])parts.push(el.getAttribute?.(a)||'');
    const prev=el.previousElementSibling;if(prev)parts.push(prev.innerText||prev.textContent||'');
    const p=el.parentElement;if(p)parts.push((p.innerText||'').slice(0,160));
    return clean(parts.filter(Boolean).join(' '));
  }

  function aliasMatch(label,aliases){const n=norm(label);let best=0;for(const a of aliases||[]){const na=norm(a);if(na&&n.includes(na))best=Math.max(best,na.length);}return best;}
  function classifyScalar(label,pack){if(risky.test(label))return null;let best=null,bestLen=0;for(const [key,list] of Object.entries(scalarAliases)){for(const a of list){const len=aliasMatch(label,[a]);if(len>bestLen&&pack[key]){best=key;bestLen=len;}}}return best;}

  function nativeSet(el,value){
    value=String(value??'').trim();if(!value)return false;
    if(el.tagName==='SELECT'){
      const v=norm(value),opts=[...el.options];const hit=opts.find(o=>norm(o.textContent)===v)||opts.find(o=>norm(o.textContent).includes(v)||v.includes(norm(o.textContent)));if(!hit)return false;el.value=hit.value;el.dispatchEvent(new Event('change',{bubbles:true}));return true;
    }
    const type=(el.getAttribute('type')||'text').toLowerCase();if(['hidden','file','password','submit','button','radio','checkbox','image','reset'].includes(type))return false;
    const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;const d=Object.getOwnPropertyDescriptor(proto,'value');if(d?.set)d.set.call(el,value);else el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));el.dispatchEvent(new Event('blur',{bubbles:true}));return true;
  }

  function formControls(root=document){return [...root.querySelectorAll('input,textarea,select')].filter(el=>!el.disabled&&!el.readOnly);}

  function fillScalars(pack){
    let filled=0,skippedFiles=0;const keys=[],used=new Set();
    for(const el of formControls(document)){
      const type=(el.getAttribute('type')||'text').toLowerCase();if(type==='file'){skippedFiles++;continue;}if(risky.test(labelFor(el)))continue;
      const key=classifyScalar(labelFor(el),pack);if(!key||used.has(key))continue;
      const value=String(pack[key]||'').trim();if(value&&nativeSet(el,value)){filled++;keys.push(key);used.add(key);}
    }
    return {filled,skippedFiles,keys:[...new Set(keys)]};
  }

  function findSection(kind){
    const aliases=sectionAliases[kind]||[],candidates=[];
    for(const el of document.querySelectorAll('section,fieldset,form,div')){
      const controls=el.querySelectorAll?.('input,textarea,select').length||0;if(!controls)continue;
      const text=clean((el.innerText||'').slice(0,1000));if(!aliases.some(a=>text.includes(a)))continue;
      candidates.push({el,controls,textLen:text.length});
    }
    candidates.sort((a,b)=>a.controls-b.controls||a.textLen-b.textLen);return candidates[0]?.el||document;
  }

  function controlsByField(root,kind){
    const map={},aliases=repeatedAliases[kind]||{};for(const field of Object.keys(aliases))map[field]=[];
    for(const el of formControls(root)){
      const label=labelFor(el);if(risky.test(label))continue;let best=null,bestLen=0;
      for(const [field,list] of Object.entries(aliases)){const len=aliasMatch(label,list);if(len>bestLen){best=field;bestLen=len;}}
      if(best)map[best].push(el);
    }
    return map;
  }

  function currentRowCapacity(map){return Math.max(0,...Object.values(map).map(x=>x.length));}
  function findAddButton(root,kind){
    const aliases=sectionAliases[kind]||[],buttons=[...root.querySelectorAll('button,[role="button"],a')];
    return buttons.find(el=>{const text=clean(el.innerText||el.textContent||'');if(!text||forbiddenButton.test(text))return false;const isAdd=/(新增|添加|增加|继续添加|add)/i.test(text);if(!isAdd)return false;return aliases.some(a=>text.includes(a))||text.length<=12;})||null;
  }
  function valueFor(kind,record,field){if(kind==='education'&&field==='school')return record.school||record.organization||'';if(field==='description')return record.description||((record.bullets||[]).join('\n'))||record.text||'';return record[field]||'';}

  async function ensureRows(kind,records,root,adapter){
    let map=controlsByField(root,kind),capacity=currentRowCapacity(map),added=0;
    while(capacity<records.length&&added<Math.min(5,records.length)){
      const button=findAddButton(root,kind)||findAddButton(document,kind);if(!button)break;
      const text=clean(button.innerText||button.textContent||'');if(forbiddenButton.test(text))break;
      button.click();added++;await sleep(adapter.id==='moka'?260:180);root=findSection(kind);map=controlsByField(root,kind);const next=currentRowCapacity(map);if(next<=capacity&&added>=2)break;capacity=next;
    }
    return {root,map,added};
  }

  async function fillRepeated(kind,records,adapter){
    if(!Array.isArray(records)||!records.length)return {kind,rows:0,fields:0,added:0};
    let root=findSection(kind);const ensured=await ensureRows(kind,records,root,adapter);root=ensured.root;const map=ensured.map;let fields=0;const rowsTouched=new Set();
    for(const [field,elements] of Object.entries(map)){
      for(let i=0;i<Math.min(records.length,elements.length);i++){
        const value=valueFor(kind,records[i],field);if(value&&nativeSet(elements[i],value)){fields++;rowsTouched.add(i);}
      }
    }
    return {kind,rows:rowsTouched.size,fields,added:ensured.added};
  }

  async function run(structured={},pack={},options={}){
    const adapter=detectAdapter(),previousRisky=risky.test;
    if(options?.allowSensitive)risky.test=()=>false;
    const scalar=fillScalars(pack||{}),repeated=[];
    for(const kind of ['education','internships','projects','research','campus'])repeated.push(await fillRepeated(kind,structured?.[kind]||[],adapter));
    const repeatedFields=repeated.reduce((n,x)=>n+x.fields,0),rowsAdded=repeated.reduce((n,x)=>n+x.added,0),rowsTouched=repeated.reduce((n,x)=>n+x.rows,0);
    if(options?.allowSensitive)risky.test=previousRisky;
    return {adapter:adapter.label,adapter_id:adapter.id,scalar_filled:scalar.filled,repeated_fields:repeatedFields,repeated_rows:rowsTouched,rows_added:rowsAdded,skipped_files:scalar.skippedFiles,total_filled:scalar.filled+repeatedFields,warning:'JobPilot 未点击任何提交/下一步按钮，请人工逐项检查。'};
  }

  window.JobPilotAutofill={run,detectAdapter};
})();
