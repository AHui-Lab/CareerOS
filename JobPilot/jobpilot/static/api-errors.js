/* Render API errors without leaking request contents or coercing objects to strings. */
(function(root){
  'use strict';
  const fields={url:'招聘链接',title:'页面标题',text:'招聘文字',company:'公司',role:'岗位',location:'地点',deadline:'截止时间',jd_text:'岗位 JD',note:'备注'};
  function message(detail,fallback='请求失败，请稍后重试。'){
    if(typeof detail==='string')return detail.trim()||fallback;
    if(Array.isArray(detail))return [...new Set(detail.map(item=>message(item,'')).filter(Boolean))].slice(0,4).join('；')||fallback;
    if(detail&&typeof detail==='object'){
      const field=Array.isArray(detail.loc)?detail.loc.filter(x=>x!=='body').at(-1):'',label=fields[field]||'';
      const limit=detail.ctx||{};
      if(detail.type==='string_too_short')return `${label||'内容'}至少需要 ${limit.min_length||10} 个字符。`;
      if(detail.type==='string_too_long')return `${label||'内容'}不能超过 ${limit.max_length||'规定数量'} 个字符，请精简后重试。`;
      if(detail.type==='missing')return `请填写${label||'必填内容'}。`;
      if(detail.type==='string_type')return `${label||'内容'}格式不正确，请重新填写。`;
      if(typeof detail.msg==='string')return (label?label+'：':'')+detail.msg.replace(/^Value error, /,'');
      if(typeof detail.message==='string')return detail.message;
    }
    return fallback;
  }
  if(typeof module==='object'&&module.exports)module.exports={message};else root.CareerApiErrors={message};
})(typeof window==='undefined'?globalThis:window);
