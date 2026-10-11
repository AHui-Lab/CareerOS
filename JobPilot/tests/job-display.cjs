'use strict';
const assert=require('node:assert/strict');
const {facts,excerpt,dateValue}=require('../jobpilot/static/job-display.js');
const job={id:7,role:'软件工程师',jd_text:'公司介绍\n企业欢迎你\n任职要求：\n1. 熟悉 C++ 与 <C++> 模板。\n2. 具备 Linux 开发经验。',applied_at:'2026-10-01',deadline:'2026年10月31日'};
const before=JSON.stringify(job);
const result=facts(job,{now:new Date(2026,9,10),events:[
 {id:1,opportunity_id:7,event_type:'interview',event_date:'2026-10-09',event_time:'14:00'},
 {id:2,opportunity_id:7,event_type:'signing',event_date:'2026-10-12',event_time:'10:00'},
 {id:3,opportunity_id:8,event_type:'interview',event_date:'2026-10-10'}],
 versions:[{target_opportunity_id:7},{target_opportunity_id:8}],preps:[{opportunity_id:7}],emails:[]});
assert.equal(result.elapsed,9);assert.equal(result.deadline,'2026-10-31');
assert.equal(result.next.id,2);assert.equal(result.previous.id,1);
assert.equal(result.versions,1);assert.equal(result.preps,1);
assert.ok(result.excerpt.includes('C++'));assert.ok(result.excerpt.includes('<C++>'));
assert.ok(!result.excerpt.includes('公司介绍'));assert.ok(!result.excerpt.includes('企业欢迎'));
assert.equal(excerpt({role:'招聘主页',description:'公司宣传'}),'');
assert.equal(excerpt({role:'AI创新人才',page_kind:'career_home',description:'公司介绍与岗位列表'}),'');
assert.equal(dateValue('2026-02-30'),'');assert.equal(dateValue('2028-02-29'),'2028-02-29');
assert.equal(facts({id:99}).elapsed,null);assert.equal(JSON.stringify(job),before);
console.log('Stored job facts: JD evidence, dates, links, missing values and no mutation passed.');
