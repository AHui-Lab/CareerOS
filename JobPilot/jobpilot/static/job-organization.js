/* Organization is independent from the recorded application stage. */
(function(root){
  'use strict';
  const labels={active:'正在推进',later:'稍后再投',skipped:'暂不考虑',closed:'已结束'};
  function disposition(job){return job.disposition||({ignored:'skipped',rejected:'closed'}[job.status])||'active';}
  function snapshot(job){return {disposition:job.disposition||'',revisit_at:job.revisit_at||'',disposition_note:job.disposition_note||''};}
  function matches(job,view){const value=disposition(job);if(view==='records')return true;if(view==='ended')return value==='closed';if(view==='later'||view==='skipped')return value===view;return value==='active';}
  const api={disposition,snapshot,matches,labels};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.CareerJobOrganization=api;
})(typeof window==='undefined'?globalThis:window);
