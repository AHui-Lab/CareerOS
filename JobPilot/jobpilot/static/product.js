(() => {
  'use strict';
  titles.vault='资料库';subtitles.vault='记录真实经历，整理成可以反复使用的求职材料。';
  titles.profile='旧版资料工具';
  let editorOpen=false,currentView='dashboard';
  function lockEditor(){
    const locked=editorOpen&&currentView==='vault';document.body.classList.toggle('vault-editor-open',locked);
    document.querySelectorAll('.sidebar,.workspace-commandbar,.topbar,.vault-frame-tabs').forEach(element=>{element.inert=locked||(element.classList.contains('sidebar')&&matchMedia('(max-width:680px)').matches&&!document.body.classList.contains('mobile-nav-open'));});
  }
  window.addEventListener('message',event=>{const frame=document.getElementById('careerVaultFrame');if(event.source!==frame.contentWindow||event.origin!==new URL(frame.src).origin)return;if(event.data?.type==='careeros-vault-editor-state'){editorOpen=!!event.data.open;lockEditor();}});
  window.addEventListener('resize',lockEditor);
  function update(view){
    currentView=view;lockEditor();
    document.body.dataset.currentView=view;
    document.getElementById('currentBreadcrumb').textContent=titles[view]||view;
    if(view==='vault'){document.getElementById('viewTitle').textContent=titles.vault;document.getElementById('viewSubtitle').textContent=subtitles.vault;}
  }
  window.addEventListener('careeros-view-changed',event=>update(event.detail.view));
  const active=document.querySelector('.view.active-view');if(active)update(active.id.replace(/^view-/,'').replace(/-/g,'_'));
  document.querySelectorAll('.vault-library-tools button').forEach(button=>button.addEventListener('click',()=>button.closest('details').removeAttribute('open')));
  document.getElementById('vaultQuickAdd').addEventListener('click',()=>{
    document.querySelectorAll('[data-vault-view]').forEach(button=>button.classList.toggle('active',button.dataset.vaultView==='experiences'));
  });
  const help=document.querySelector('[data-settings-group="help"]');
  if(help){const entry=document.createElement('button');entry.type='button';entry.className='ghost-btn';entry.dataset.goView='profile';entry.textContent='打开旧版资料与导入工具';help.append(entry);}
})();
