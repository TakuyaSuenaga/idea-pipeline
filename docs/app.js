'use strict';

const IDEAS_URL = './data/ideas.json';
const RESEARCH_URL = './data/research.json';

let allIdeas = [];
let currentFilter = 'all';

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderIdeas(ideas) {
  const filtered = currentFilter === 'all'
    ? ideas
    : ideas.filter(i => i.category === currentFilter);

  const grid = document.getElementById('ideas-grid');

  if (filtered.length === 0) {
    grid.innerHTML = '<p class="empty">No ideas yet. Trigger the pipeline to generate some.</p>';
    return;
  }

  grid.innerHTML = filtered.map(idea => `
    <article class="idea-card">
      <div class="card-header">
        <h3>${escapeHtml(idea.title)}</h3>
        <span class="badge badge-${escapeHtml(idea.category)}">${escapeHtml(idea.category)}</span>
        <span class="badge badge-difficulty-${escapeHtml(idea.difficulty)}">${escapeHtml(idea.difficulty)}</span>
      </div>
      <p class="description">${escapeHtml(idea.description)}</p>
      <dl class="details">
        <dt>Target Market</dt><dd>${escapeHtml(idea.target_market || '—')}</dd>
        <dt>Why Now</dt><dd>${escapeHtml(idea.why_now || '—')}</dd>
        <dt>Revenue Model</dt><dd>${escapeHtml(idea.revenue_model || '—')}</dd>
      </dl>
      <time class="generated-at">${new Date(idea.generated_at).toLocaleDateString('ja-JP')}</time>
    </article>
  `).join('');
}

function renderResearch(items) {
  const tbody = document.getElementById('research-tbody');
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">No research data yet.</td></tr>';
    return;
  }

  tbody.innerHTML = items.slice(0, 50).map(item => `
    <tr>
      <td>${escapeHtml(item.source)}</td>
      <td>${item.url
        ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>`
        : escapeHtml(item.title)}</td>
      <td><span class="badge badge-${escapeHtml(item.category)}">${escapeHtml(item.category)}</span></td>
      <td>${item.score != null ? escapeHtml(String(item.score)) : '—'}</td>
      <td>${new Date(item.fetched_at).toLocaleDateString('ja-JP')}</td>
    </tr>
  `).join('');
}

async function loadData() {
  try {
    const [ideasResp, researchResp] = await Promise.all([
      fetch(IDEAS_URL),
      fetch(RESEARCH_URL),
    ]);

    const ideasData = await ideasResp.json();
    const researchData = await researchResp.json();

    allIdeas = ideasData.ideas || [];

    document.getElementById('last-updated').textContent =
      `Last updated: ${new Date(ideasData.exported_at).toLocaleString('ja-JP')} — ${allIdeas.length} ideas`;

    renderIdeas(allIdeas);
    renderResearch(researchData.items || []);
  } catch (err) {
    document.getElementById('ideas-grid').innerHTML =
      '<p class="error">Failed to load data. Run the pipeline first, then refresh.</p>';
    console.error(err);
  }
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    renderIdeas(allIdeas);
  });
});

loadData();
