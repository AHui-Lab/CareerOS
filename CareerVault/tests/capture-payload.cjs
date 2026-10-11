const assert = require('node:assert/strict');
const {formModel,makePayload}=require('../careervault/static/capture.js');
const types=['project','internship','award','patent','certificate','campus','education','research','work','paper','other'];
for(const type of types){
  const base={id:'fixture',type,title:'已有经历',organization:'原单位',role:'原角色',start:'2023-01',end:'至今',status:'verified',resume_ready:true,domains:['嵌入式','带,逗号的标签'],skills:['C++','带,逗号的技能'],related_experience_ids:['other-id'],summary:'原始介绍',facts:'完整事实\n第二行',results:'完整成果',notes:'原备注',details:{unknown:{important:['preserve',1]},hr_intro:'口述',award_level:'国家级',patent_number:'CN-original'}};
  if(type==='project')Object.assign(base.details,{project_pitch:'短介绍',personal_contribution:'短贡献',project_outcome:'短结果'});
  const model=formModel(base),payload=makePayload(base,{...model.values,resume_ready:base.resume_ready},model.mapped);
  for(const key of ['type','title','organization','role','start','end','status','resume_ready','domains','skills','related_experience_ids','summary','facts','results','notes','details'])assert.deepEqual(payload[key],base[key],`${type}: ${key} changed without user edits`);
  const changed=makePayload(base,{...model.values,title:'只修改名称',resume_ready:false},model.mapped);
  assert.equal(changed.title,'只修改名称');assert.equal(changed.resume_ready,false);assert.deepEqual(changed.details,base.details);assert.equal(changed.facts,base.facts);
  const edits={...model.mapped,[model.content]:'新的个人动作'};
  const updated=makePayload(base,model.values,edits);
  if(model.brief){assert.equal(updated.details.personal_contribution,'新的个人动作');assert.equal(updated.facts,base.facts);assert.equal(updated.results,base.results);}
  else assert.equal(updated[model.content],'新的个人动作');
}
const draft=makePayload({}, {title:'只记一个名字',type:'internship'}, {});
assert.equal(draft.status,'draft');assert.equal(draft.resume_ready,false);assert.equal(draft.title,'只记一个名字');
const summaryOnly={id:'legacy',type:'project',title:'旧版记录',summary:'只有原始介绍',facts:'',results:'',notes:'',details:{}};
const summaryModel=formModel(summaryOnly);assert.equal(summaryModel.content,'summary');
assert.equal(makePayload(summaryOnly,summaryModel.values,summaryModel.mapped).summary,'只有原始介绍');
console.log('Capture preservation checks passed for 11 experience types and new/legacy drafts.');
