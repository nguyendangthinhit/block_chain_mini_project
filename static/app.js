// Lost and Found Registry UI: talks to the Flask + web3.py API.
const $ = (id) => document.getElementById(id);
const state = { account: null, accounts: [] };

const short = (addr) => (addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : '–');
const same = (a, b) => !!a && !!b && a.toLowerCase() === b.toLowerCase();

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text ?? '');
  return div.innerHTML;
}

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  let data;
  try { data = await res.json(); } catch { data = { error: `HTTP ${res.status}` }; }
  if (!res.ok) throw Object.assign(new Error(data.error || `HTTP ${res.status}`), { rejected: !!data.rejected });
  return data;
}

function showTx(kind, html) {
  const box = $('tx-output');
  box.className = `tx ${kind}`;
  box.innerHTML = html;
}

async function sendTx(label, path, body) {
  if (!state.account) { showTx('error', '<strong>No account connected.</strong> Select a Ganache account and click Connect.'); return false; }
  showTx('pending', `⏳ <strong>${escapeHtml(label)}</strong> — sending from ${short(state.account)}…`);
  try {
    const r = await api(path, { method: 'POST', body: JSON.stringify({ ...body, account: state.account }) });
    const events = r.events.map((e) => `<li><code>${e.event}</code> ${escapeHtml(JSON.stringify(e.args))}</li>`).join('');
    showTx('success', `✅ <strong>${escapeHtml(label)} succeeded</strong>
      <div class="mono">Tx: ${r.txHash}</div><div>Block ${r.blockNumber} · Gas used ${r.gasUsed}</div>
      <ul>${events}</ul>`);
    await refresh();
    return true;
  } catch (err) {
    const title = err.rejected ? 'Rejected by contract' : 'Error';
    showTx('error', `❌ <strong>${escapeHtml(label)} — ${title}</strong><div>${escapeHtml(err.message)}</div>`);
    return false;
  }
}

function renderStatus(s) {
  state.accounts = s.accounts;
  // Drop an account remembered from an older Ganache session that no longer exists.
  if (state.account && !s.accounts.some((a) => same(a.address, state.account))) state.account = null;
  $('network-badge').textContent = `Ganache · chain ${s.chainId}`;
  $('network-badge').className = 'badge ok';
  $('chain-id').textContent = s.chainId;
  $('block-number').textContent = s.blockNumber;
  $('contract-address').textContent = s.contractAddress;
  $('counts').textContent = `${s.itemCount} / ${s.claimCount}`;
  const select = $('account-select');
  const previous = select.value;
  select.innerHTML = s.accounts.map((a, i) => `<option value="${a.address}">#${i} ${short(a.address)} (${Number(a.balanceEth).toFixed(2)} ETH)</option>`).join('');
  if (previous) select.value = previous;
  const current = s.accounts.find((a) => same(a.address, state.account));
  $('connected-account').textContent = state.account || 'Not connected';
  $('connected-balance').textContent = current ? `${Number(current.balanceEth).toFixed(4)} ETH` : '–';
}

function renderClaim(item, c) {
  const approve = item.status === 'Found' && c.status === 'Pending'
    ? `<button class="small" data-approve="${c.id}">Approve &amp; mark returned</button>` : '';
  return `<li class="claim ${c.status.toLowerCase()}">
    <div><strong>Claim #${c.id}</strong> <span class="pill ${c.status.toLowerCase()}">${c.status}</span>
      by <span class="mono" title="${c.claimant}">${short(c.claimant)}</span>${same(c.claimant, state.account) ? ' (you)' : ''}</div>
    <div class="muted">${escapeHtml(c.details)}</div>${approve}</li>`;
}

function renderItems(items) {
  if (!items.length) { $('item-list').innerHTML = '<p class="muted">No items registered yet.</p>'; return; }
  $('item-list').innerHTML = items.map((item) => `
    <article class="item">
      <div class="item-head"><h3>#${item.id} ${escapeHtml(item.name)}</h3>
        <span class="pill ${item.status.toLowerCase()}">${item.status}</span></div>
      <p>${escapeHtml(item.description)}</p>
      <p class="muted">Finder: <span class="mono" title="${item.finder}">${short(item.finder)}</span>${same(item.finder, state.account) ? ' (you)' : ''}
        ${item.approvedClaimId ? ` · Returned via claim #${item.approvedClaimId}` : ''}</p>
      <ul class="claims">${item.claims.map((c) => renderClaim(item, c)).join('') || '<li class="muted">No claims yet.</li>'}</ul>
      <form class="claim-form" data-item="${item.id}">
        <input name="details" maxlength="280" placeholder="Proof of ownership (e.g. contents, marks)" required>
        <button type="submit" class="secondary">Submit claim</button>
      </form>
    </article>`).join('');
}

function renderEvents(events) {
  $('event-list').innerHTML = events.map((e) => `<li><code>${e.event}</code> block ${e.blockNumber}
    <span class="muted">${escapeHtml(JSON.stringify(e.args))}</span></li>`).join('') || '<li class="muted">No events yet.</li>';
}

async function refresh() {
  try {
    const [status, items, events] = await Promise.all([api('/api/status'), api('/api/items'), api('/api/events')]);
    renderStatus(status);
    renderItems(items);
    renderEvents(events);
  } catch (err) {
    $('network-badge').textContent = 'Disconnected';
    $('network-badge').className = 'badge error';
    showTx('error', `❌ <strong>Cannot load blockchain data</strong><div>${escapeHtml(err.message)}</div>`);
  }
}

$('connect-btn').addEventListener('click', () => {
  state.account = $('account-select').value || null;
  try { localStorage.setItem('lf-account', state.account || ''); } catch { /* storage optional */ }
  refresh();
});

$('register-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const ok = await sendTx('Register item', '/api/items', { name: $('item-name').value, description: $('item-description').value });
  if (ok) event.target.reset();
});

$('item-list').addEventListener('submit', (event) => {
  if (!event.target.matches('.claim-form')) return;
  event.preventDefault();
  const itemId = event.target.dataset.item;
  sendTx(`Submit claim on item #${itemId}`, `/api/items/${itemId}/claims`, { details: event.target.details.value });
});

$('item-list').addEventListener('click', (event) => {
  const claimId = event.target.dataset.approve;
  if (claimId) sendTx(`Approve claim #${claimId}`, `/api/claims/${claimId}/approve`, {});
});

$('refresh-btn').addEventListener('click', refresh);

try { state.account = localStorage.getItem('lf-account') || null; } catch { state.account = null; }
refresh().then(() => { if (state.account) $('account-select').value = state.account; });
