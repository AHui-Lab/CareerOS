/* Recorded facts stay separate from company averages and incomplete first-year plans. */
(function(root){
 'use strict';
 const number=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
 const phaseNames={internship:'学生实习期',trainee:'见习期',probation:'劳动合同试用期',regular:'转正 / 常态待遇',other:'其他阶段'};
 function phasePay(phase,details={}){
   if(phase.pay_method==='fixed')return {monthly:number(phase.monthly_amount),estimated:false};
   if(phase.pay_method==='discount'){
     const base=phase.discount_base_type==='specified'?number(phase.discount_base_monthly):phase.discount_base_type==='regular'?number(details.monthly_base):null,pct=number(phase.percentage);
     return {monthly:base!==null&&pct!==null?base*pct/100:null,estimated:true};
   }
   return {monthly:null,estimated:false};
 }
 function calculate(offer){
   const d=offer.details||{},base=number(d.monthly_base),months=number(d.guaranteed_months),direct=number(d.guaranteed_annual_cash);
   const salary=base!==null&&months!==null?base*months:null;
   const allowance=number(d.monthly_allowance),fixed=number(d.fixed_bonus);
   const annual=direct??(salary===null?null:salary+(allowance??0)*12+(fixed??0));
   const target=annual!==null&&number(d.bonus_target)!==null?annual+d.bonus_target:null;
   const signing=number(d.signing_bonus),relocation=number(d.relocation_bonus);
   const oneTime=signing===null&&relocation===null?null:(signing??0)+(relocation??0);
   const net=number(d.net_monthly),cost=number(d.monthly_living_cost);
   const fundBase=number(d.fund_base),fundPct=number(d.fund_employer_pct),fundActual=number(d.fund_employer_actual);
   const fundEmployerMonthly=fundActual??(fundBase!==null&&fundPct!==null?fundBase*fundPct/100:null);
   const missing=[];
   if(direct===null){if(base===null)missing.push('固定月薪');if(months===null)missing.push('保证计薪月数');if(fixed===null)missing.push('另计固定奖金');if(allowance===null)missing.push('固定现金补贴');}
   const phases=(d.pay_phases||[]).filter(p=>p.included_in_first_year),known=phases.filter(p=>number(p.duration_months)!==null&&phasePay(p,d).monthly!==null);
   const firstYearMonths=phases.reduce((sum,p)=>sum+(number(p.duration_months)??0),0);
   const firstYearUnknown=phases.length-known.length;
   const firstYearKnownMonths=known.reduce((sum,p)=>sum+p.duration_months,0);
   const firstYearSubtotal=known.length?known.reduce((sum,p)=>sum+p.duration_months*phasePay(p,d).monthly,0):null;
   return {salary,annual,annualBasis:direct!==null?'direct':'monthly',target,oneTime,fundEmployerMonthly,fundEstimated:fundActual===null&&fundEmployerMonthly!==null,balance:net!==null&&cost!==null?net-cost:null,missing,incompleteOneTime:[signing,relocation].some(x=>x===null),firstYearMonths,firstYearKnownMonths,firstYearUnknown,firstYearSubtotal,firstYearComplete:phases.length>0&&firstYearMonths===12&&firstYearUnknown===0};
 }
 function unanswered(offer){
   const d=offer.details||{},items=[];
   if(['annual_average','annual_range'].includes(d.pay_quote_type)){
     if(!d.annual_reference_scope)items.push('平均 / 区间年收入对应哪些人，包含哪些绩效、奖金和福利？');
     if(number(d.guaranteed_annual_cash)===null&&(number(d.monthly_base)===null||number(d.guaranteed_months)===null))items.push('平均年收入之外，实际保证的固定金额是多少？');
   }else if(number(d.guaranteed_annual_cash)===null&&(number(d.monthly_base)===null||number(d.guaranteed_months)===null))items.push('固定月薪和保证计薪月数是多少？');
   if((d.pay_phases||[]).some(p=>p.pay_method==='discount'&&phasePay(p,d).monthly===null))items.push('实习 / 试用期打折针对哪个工资基数，实际每月金额是多少？');
   if((d.pay_phases||[]).some(p=>p.pay_method==='unknown'))items.push('实习、见习或试用阶段的支付方式与每月金额分别是什么？');
   if(!d.first_year_bonus_rules&&offer.start_date)items.push('入职首年、实习或试用期间，13 薪和年终奖金如何折算？');
   if(number(d.bonus_target)!==null&&!d.bonus_rules)items.push('浮动奖金的达成条件和发放时间是什么？');
   if(!d.evidence?.pay||d.evidence.pay.status!=='written')items.push('薪酬条件是否已取得书面确认？');
   if(number(d.fund_employer_actual)===null&&(number(d.fund_base)===null||number(d.fund_employer_pct)===null))items.push('公积金的缴存城市、政策年度、基数、比例及实际月缴额是什么？');
   if(!d.pay_phases?.some(p=>p.phase_type==='probation')&&(number(d.probation_months)===null||number(d.probation_pay)===null))items.push('试用期时长、薪资和转正条件是什么？');
   if(!d.employment_entity)items.push('劳动合同与实际发薪主体是谁？');
   if(!offer.reply_deadline)items.push('最晚需要什么时候回复 Offer？');
   return items;
 }
 function daysUntil(key,today){if(!key)return null;const days=(Date.parse(key+'T00:00:00Z')-Date.parse(today+'T00:00:00Z'))/86400000;return Number.isFinite(days)?days:null;}
 function deadlines(items,today){return items.filter(o=>!o.archived&&['pending','negotiating'].includes(o.status)&&o.reply_deadline).sort((a,b)=>a.reply_deadline.localeCompare(b.reply_deadline));}
 const api={calculate,unanswered,phasePay,phaseNames,daysUntil,deadlines};if(typeof module==='object'&&module.exports)module.exports=api;else root.CareerOfferMath=api;
})(typeof window==='undefined'?globalThis:window);
