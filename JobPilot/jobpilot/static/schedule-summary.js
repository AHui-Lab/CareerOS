/* Date-window selection shared by the homepage and its boundary checks. */
(function(root){
  'use strict';
  const dateKey=date=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  function nearTerm(events,now=new Date()){
    const start=new Date(now.getFullYear(),now.getMonth(),now.getDate());
    const end=new Date(start);end.setDate(end.getDate()+2);
    const first=dateKey(start),last=dateKey(end);
    const items=events.filter(event=>{
      const key=String(event.event_date||'');
      if(!/^\d{4}-\d{2}-\d{2}$/.test(key)||key<first||key>last)return false;
      const parsed=new Date(key+'T00:00:00');
      if(Number.isNaN(parsed.valueOf())||dateKey(parsed)!==key)return false;
      // An automatically recorded past application is history, not an appointment.
      return !(event.source==='opportunity'&&event.event_type==='application');
    }).slice().sort((a,b)=>String(a.event_date).localeCompare(String(b.event_date))||String(a.event_time||'99:99').localeCompare(String(b.event_time||'99:99'))||Number(a.id||0)-Number(b.id||0));
    return {items,start:first,end:last};
  }
  const api={nearTerm,dateKey};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.CareerScheduleSummary=api;
})(typeof window!=='undefined'?window:globalThis);
