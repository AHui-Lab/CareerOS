/* Read-only presentation of stored job facts; no inferred requirements or scores. */
(function(root){
  'use strict';
  const key=date=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  function dateValue(value){
    const match=String(value||'').match(/^(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})/);
    if(!match)return '';
    const result=`${match[1]}-${match[2].padStart(2,'0')}-${match[3].padStart(2,'0')}`;
    const parsed=new Date(result+'T00:00:00');return !Number.isNaN(parsed.valueOf())&&key(parsed)===result?result:'';
  }
  function excerpt(job){
    // Career homepages are not a verified job description.
    if(!job.role||/招聘主页|待识别|校园招聘$/.test(job.role)||(job.page_kind==='career_home'&&!String(job.jd_text||'').trim()))return '';
    const value=String(job.jd_text||job.description||'').replace(/<\/?(?:p|div|br|span|li|ul|ol|strong|b|em|h[1-6])(?:\s[^>]*)?\/?>/gi,' ').replace(/&nbsp;/g,' ');
    const lines=value.split(/\r?\n/).map(line=>line.replace(/^\s*[#*>•·\-]+\s*/,'').trim()).filter(Boolean);
    const requirements=lines.findIndex(line=>/^(任职要求|任职资格|职位要求|岗位要求|资格要求|招聘要求|岗位条件|任职条件|应聘条件)/.test(line));
    const responsibilities=lines.findIndex(line=>/^(岗位职责|工作职责|职位描述|岗位描述|工作内容|职责描述)/.test(line));
    const section=requirements>=0?requirements:responsibilities;
    let selected=section>=0?lines.slice(section):lines;
    if(requirements<0){const meaningful=selected.findIndex(line=>line.length>18&&/负责|熟悉|掌握|具备|应届毕业生|学历|岗位职责|任职/.test(line));if(meaningful>=0)selected=selected.slice(meaningful);}
    return selected.filter(line=>!/^(.{0,5}职责|任职要求|任职资格|职位要求|岗位要求|资格要求|招聘要求|岗位条件|任职条件|应聘条件|职位描述|岗位描述|工作内容|立即投递|立即申请|分享职位|返回列表)\s*[:：]?$/.test(line)).join(' ').slice(0,260);
  }
  function facts(job,{events=[],versions=[],preps=[],emails=[],now=new Date()}={}){
    const today=key(now),active=events.filter(event=>Number(event.opportunity_id)===Number(job.id)&&['interview','written_test','signing','deadline','follow_up'].includes(event.event_type)&&dateValue(event.event_date));
    active.sort((a,b)=>String(a.event_date).localeCompare(String(b.event_date))||String(a.event_time||'99:99').localeCompare(String(b.event_time||'99:99')));
    const next=active.find(event=>event.event_date>=today);
    const previous=[...active].reverse().find(event=>['interview','written_test','signing'].includes(event.event_type)&&event.event_date<today);
    const applied=dateValue(job.applied_at);
    const elapsed=applied?Math.round((Date.UTC(now.getFullYear(),now.getMonth(),now.getDate())-Date.parse(applied+'T00:00:00Z'))/86400000):null;
    return {excerpt:excerpt(job),applied,elapsed,deadline:dateValue(job.deadline),next,previous,
      versions:versions.filter(item=>Number(item.target_opportunity_id??item.opportunity_id)===Number(job.id)||(job.company&&job.role&&item.target_company===job.company&&item.target_role===job.role)).length,
      preps:preps.filter(item=>Number(item.opportunity_id)===Number(job.id)).length,
      emails:emails.filter(item=>Number(item.opportunity_id)===Number(job.id)).length};
  }
  const api={dateValue,excerpt,facts};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.CareerJobDisplay=api;
})(typeof window!=='undefined'?window:globalThis);
