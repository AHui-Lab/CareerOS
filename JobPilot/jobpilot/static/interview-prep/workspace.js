(() => {
  'use strict';
  window.addEventListener('message',event=>{if(event.origin!==location.origin)return;if(event.data?.type==='careeros-theme')document.documentElement.dataset.theme=event.data.theme==='dark'?'dark':'light';});
})();
