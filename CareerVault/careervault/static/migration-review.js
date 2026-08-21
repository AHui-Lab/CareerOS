(() => {
  let migrationItems = new Map();
  let pendingCount = 0;
  let decorateScheduled = false;
  let activeExperienceId = '';

  async function requestJson(url, options = {}) {
    const res = await fetch(url, {
      headers: {'Content-Type': 'application/json', ...(options.headers || {})},
      ...options,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async function refreshMigrationState() {
    try {
      const res = await fetch('/api/experiences');
      if (!res.ok) return;
      const items = await res.json();
      migrationItems = new Map(
        (Array.isArray(items) ? items : [])
          .filter(x => x?.migration_review === 'required')
          .map(x => [String(x.id), x])
      );
      pendingCount = migrationItems.size;
      scheduleDecorate();
    } catch (_) {
      // Optional decoration must never block the core CareerVault UI.
    }
  }

  function decorateDashboard() {
    const root = document.querySelector('#dashboard');
    if (!root || !root.classList.contains('active')) return;
    const grid = root.querySelector('.grid');
    if (!grid) return;

    let card = root.querySelector('[data-migration-review-summary]');
    if (!card) {
      card = document.createElement('div');
      card.className = 'card';
      card.dataset.migrationReviewSummary = '1';
      grid.insertAdjacentElement('afterend', card);
    }

    const nextHtml = pendingCount
      ? `<strong>待审核迁移：${pendingCount} 条</strong><div class="muted" style="margin-top:6px">这些经历来自旧 Resume / Obsidian。打开任意“待审核迁移”经历，核对事实后点击“完成迁移审核”。审核前 JobPilot 不会使用它们。</div>`
      : '<strong>旧资料迁移已全部审核</strong><div class="muted" style="margin-top:6px">当前没有需要人工确认的旧资料。</div>';

    if (card.innerHTML !== nextHtml) {
      card.innerHTML = nextHtml;
    }
  }

  function decorateExperienceCards() {
    document.querySelectorAll('.experience-card[data-id]').forEach(card => {
      const id = String(card.dataset.id || '');
      const needsReview = migrationItems.has(id);
      let badge = card.querySelector('[data-migration-review-badge]');

      if (needsReview && !badge) {
        const row = card.querySelector('.row');
        if (!row) return;
        badge = document.createElement('span');
        badge.className = 'tag';
        badge.dataset.migrationReviewBadge = '1';
        badge.textContent = '待审核迁移';
        row.appendChild(badge);
      } else if (!needsReview && badge) {
        badge.remove();
      }
    });
  }

  function collectCurrentForm() {
    const csv = value => String(value || '').split(',').map(x => x.trim()).filter(Boolean);
    return {
      type: document.querySelector('#f-type')?.value || 'project',
      status: document.querySelector('#f-status')?.value || 'draft',
      title: document.querySelector('#f-title')?.value.trim() || '',
      organization: document.querySelector('#f-org')?.value.trim() || '',
      role: document.querySelector('#f-role')?.value.trim() || '',
      start: document.querySelector('#f-start')?.value.trim() || '',
      end: document.querySelector('#f-end')?.value.trim() || '',
      domains: csv(document.querySelector('#f-domains')?.value),
      skills: csv(document.querySelector('#f-skills')?.value),
      resume_ready: !!document.querySelector('#f-ready')?.checked,
      summary: document.querySelector('#f-summary')?.value || '',
      facts: document.querySelector('#f-facts')?.value || '',
      results: document.querySelector('#f-results')?.value || '',
      notes: document.querySelector('#f-notes')?.value || '',
    };
  }

  async function completeReview(id, button) {
    if (!id || !migrationItems.has(id)) return;
    const title = document.querySelector('#f-title')?.value.trim() || '';
    if (!title) {
      alert('请先确认经历名称。');
      return;
    }

    button.disabled = true;
    button.textContent = '正在完成审核…';
    const saveState = document.querySelector('#saveState');
    if (saveState) saveState.textContent = '正在保存并完成迁移审核…';

    try {
      const current = collectCurrentForm();
      await requestJson(`/api/experiences/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify(current),
      });
      const reviewed = await requestJson(`/api/experiences/${encodeURIComponent(id)}/migration-review`, {
        method: 'POST',
        body: JSON.stringify({resume_ready: current.resume_ready}),
      });

      migrationItems.delete(String(id));
      pendingCount = migrationItems.size;
      if (document.querySelector('#f-status')) document.querySelector('#f-status').value = reviewed.status || 'verified';
      if (document.querySelector('#f-ready')) document.querySelector('#f-ready').checked = !!reviewed.resume_ready;
      if (saveState) saveState.textContent = `✓ 迁移审核完成${reviewed.resume_ready ? ' · 已可用于简历' : ' · 暂不用于简历'}`;
      await refreshMigrationState();
      scheduleDecorate();
    } catch (error) {
      alert(`迁移审核失败：${error.message}`);
      if (saveState) saveState.textContent = '迁移审核失败';
      button.disabled = false;
      button.textContent = '确认事实无误，完成迁移审核';
    }
  }

  function decorateMigrationModal() {
    const modal = document.querySelector('#modal');
    const modalCard = document.querySelector('#modalCard');
    if (!modal || !modalCard || modal.classList.contains('hidden')) return;

    const id = String(activeExperienceId || '');
    const needsReview = !!id && migrationItems.has(id);
    let panel = modalCard.querySelector('[data-migration-review-panel]');

    if (!needsReview) {
      if (panel) panel.remove();
      return;
    }
    if (panel) return;

    const form = modalCard.querySelector('.form');
    if (!form) return;

    panel = document.createElement('div');
    panel.className = 'notice';
    panel.dataset.migrationReviewPanel = '1';
    panel.style.marginBottom = '16px';
    panel.innerHTML = `
      <div style="font-weight:700;margin-bottom:8px">这是一条旧资料迁移记录，需要你确认一次</div>
      <div class="muted" style="line-height:1.7">
        ① 核对名称、单位、角色和日期；<br>
        ② 核对“事实记录”和“量化成果”，尤其是数字；<br>
        ③ 删除团队做过但不是你本人完成的内容；<br>
        ④ 如果希望 JobPilot 使用它，再勾选下方“可用于简历生成”。
      </div>
      <div style="margin-top:12px"><button type="button" class="btn" data-complete-migration-review>确认事实无误，完成迁移审核</button></div>
      <div class="muted" style="margin-top:7px">完成后“待审核迁移”标记会消失。若当前状态仍是“草稿”，系统会自动改为“已验证”。</div>
    `;
    form.insertAdjacentElement('beforebegin', panel);
    panel.querySelector('[data-complete-migration-review]').onclick = event => completeReview(id, event.currentTarget);
  }

  function decorate() {
    decorateDashboard();
    decorateExperienceCards();
    decorateMigrationModal();
  }

  function scheduleDecorate() {
    if (decorateScheduled) return;
    decorateScheduled = true;
    requestAnimationFrame(() => {
      decorateScheduled = false;
      decorate();
    });
  }

  const observer = new MutationObserver(() => scheduleDecorate());
  observer.observe(document.body, { childList: true, subtree: true });

  document.addEventListener('click', event => {
    const experienceCard = event.target.closest('.experience-card[data-id]');
    if (experienceCard) {
      activeExperienceId = String(experienceCard.dataset.id || '');
      setTimeout(scheduleDecorate, 30);
    }

    if (event.target.closest('#closeModal')) {
      activeExperienceId = '';
    }

    if (event.target.closest('.nav, #refreshBtn, #saveExp, #closeModal, [data-complete-migration-review]')) {
      setTimeout(refreshMigrationState, 150);
    }
  });

  refreshMigrationState();
})();
