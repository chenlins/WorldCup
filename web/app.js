const $ = (id) => document.getElementById(id);

const statusEl = $("status");
const rowsEl = $("rows");
const featuredEl = $("featured");
const runBtn = $("runBtn");
const matchDateEl = $("matchDate");
const stageFilterEl = $("stageFilter");
const confidenceFilterEl = $("confidenceFilter");
const hideDrawEl = $("hideDraw");
const marketDivOnlyEl = $("marketDivOnly");
const helpBtn = $("helpBtn");
const helpPanel = $("helpPanel");
const helpClose = $("helpClose");
const detailModal = $("detailModal");
const detailTitle = $("detailTitle");
const detailBody = $("detailBody");
const detailClose = $("detailClose");

let lastResults = [];
let lastPayload = null;

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function fmtPct(v) {
  return `${(v * 100).toFixed(1)}%`;
}

function outcomeClass(outcome) {
  if (outcome === "主胜") return "positive";
  if (outcome === "客胜") return "negative";
  return "neutral";
}

function renderDimensionBlock(block) {
  if (!block) return "";
  const points = (block.points || [])
    .slice(0, 5)
    .map((p) => `<li>${escapeHtml(p)}</li>`)
    .join("");
  const impact = block.impact
    ? `<div class="dim-impact">影响：${escapeHtml(block.impact)}</div>`
    : "";
  return `
    <div class="dim-section">
      <h3>${escapeHtml(block.title)}</h3>
      <p class="dim-summary">${escapeHtml(block.summary || "")}</p>
      <ul class="dim-points">${points}</ul>
      ${impact}
    </div>
  `;
}

function renderAnalystVerdict(verdict) {
  if (!verdict) return "";
  const tags = (verdict.risk_tags || [])
    .map((t) => `<span class="risk-tag">${escapeHtml(t)}</span>`)
    .join("");
  const caveats = (verdict.caveats || [])
    .map((c) => `<li>${escapeHtml(c)}</li>`)
    .join("");
  const confClass =
    verdict.confidence_level === "高"
      ? "positive"
      : verdict.confidence_level === "低"
        ? "negative"
        : "neutral";
  return `
    <div class="verdict-box">
      <h3>分析师综合研判</h3>
      <p class="verdict-summary">${escapeHtml(verdict.summary || "")}</p>
      <p><strong class="${confClass}">置信度：${escapeHtml(verdict.confidence_level || "中")}</strong>
        · ${escapeHtml(verdict.recommendation || "")}</p>
      <div class="risk-tags">${tags}</div>
      <ul class="caveat-list">${caveats}</ul>
    </div>
  `;
}

function renderMarketCompare(match, dim) {
  const mkt = dim?.market_implied;
  if (!mkt || !mkt.home_win) return "";
  return `
    <div class="market-compare">
      <h3>模型 vs 市场</h3>
      <table class="compare-table">
        <thead><tr><th>结果</th><th>模型</th><th>市场隐含</th><th>参考赔率</th></tr></thead>
        <tbody>
          <tr><td>主胜</td><td class="positive">${fmtPct(match.win_prob)}</td><td>${fmtPct(mkt.home_win)}</td><td>${mkt.odds?.home ?? "—"}</td></tr>
          <tr><td>平局</td><td class="neutral">${fmtPct(match.draw_prob)}</td><td>${fmtPct(mkt.draw)}</td><td>${mkt.odds?.draw ?? "—"}</td></tr>
          <tr><td>客胜</td><td class="negative">${fmtPct(match.loss_prob)}</td><td>${fmtPct(mkt.away_win)}</td><td>${mkt.odds?.away ?? "—"}</td></tr>
        </tbody>
      </table>
    </div>
  `;
}

function renderDimensions(dim, match) {
  if (!dim) return "";
  const adj = dim.xg_adjustments || {};
  const count = dim.dimension_count || 10;
  return `
    <div>
      <h3>${count}维综合分析</h3>
      <div class="xg-adj-bar">
        <span>十维修正系数：主队 <strong>${adj.home ?? "—"}</strong></span>
        <span>客队 <strong>${adj.away ?? "—"}</strong></span>
      </div>
      ${match ? renderMarketCompare(match, dim) : ""}
      ${renderAnalystVerdict(dim.analyst_verdict)}
      <div class="help-body dim-grid" style="margin-top:12px">
        ${renderDimensionBlock(dim.team_basics)}
        ${renderDimensionBlock(dim.head_to_head)}
        ${renderDimensionBlock(dim.key_players)}
        ${renderDimensionBlock(dim.tactical)}
        ${renderDimensionBlock(dim.external)}
        ${renderDimensionBlock(dim.tournament_pedigree)}
        ${renderDimensionBlock(dim.squad_depth)}
        ${renderDimensionBlock(dim.advanced_metrics)}
        ${renderDimensionBlock(dim.schedule_load)}
        ${renderDimensionBlock(dim.market_consensus)}
      </div>
    </div>
  `;
}

function hasMarketDivergence(match) {
  const tags = match.dimensions?.analyst_verdict?.risk_tags || [];
  return tags.includes("市场分歧");
}

function applyFilters(matches) {
  const stage = stageFilterEl.value;
  const minConf = Number(confidenceFilterEl.value);
  const hideDraw = hideDrawEl.checked;
  const marketDivOnly = marketDivOnlyEl.checked;

  return matches.filter((m) => {
    if (stage !== "all" && m.stage !== stage) return false;
    if (m.confidence < minConf) return false;
    if (hideDraw && m.draw_prob < 0.22) return false;
    if (marketDivOnly && !hasMarketDivergence(m)) return false;
    return true;
  });
}

function renderFeatured(match) {
  if (!match) {
    featuredEl.classList.add("hidden");
    featuredEl.innerHTML = "";
    return;
  }

  featuredEl.classList.remove("hidden");
  featuredEl.innerHTML = `
    <div class="rec-head">
      <div>
        <div class="rec-title">${escapeHtml(match.home_display)} vs ${escapeHtml(match.away_display)}</div>
        <p>当日置信度最高场次 · ${escapeHtml(match.stage)}${match.group ? ` · ${match.group}组` : ""} · ${escapeHtml(match.city)}</p>
      </div>
      <span class="badge">置信度 ${fmtPct(match.confidence)}</span>
    </div>
    <div class="plan-grid">
      <div class="metric"><span>预测比分</span><strong>${escapeHtml(match.predicted_score)}</strong></div>
      <div class="metric"><span>预测结果</span><strong class="${outcomeClass(match.outcome)}">${escapeHtml(match.outcome)}</strong></div>
      <div class="metric"><span>主胜 / 平 / 客胜</span><strong>${fmtPct(match.win_prob)} / ${fmtPct(match.draw_prob)} / ${fmtPct(match.loss_prob)}</strong></div>
      <div class="metric"><span>期望进球 xG</span><strong>${match.predicted_home_goals} : ${match.predicted_away_goals}</strong></div>
    </div>
    ${
      match.dimensions?.analyst_verdict
        ? `<div class="verdict-box compact-verdict">
            <p class="verdict-summary">${escapeHtml(match.dimensions.analyst_verdict.summary)}</p>
            <div class="risk-tags">${(match.dimensions.analyst_verdict.risk_tags || [])
              .slice(0, 4)
              .map((t) => `<span class="risk-tag">${escapeHtml(t)}</span>`)
              .join("")}</div>
          </div>`
        : ""
    }
    <ol class="reasons">
      ${match.analysis.slice(0, 3).map((r) => `<li>${escapeHtml(r)}</li>`).join("")}
    </ol>
    <div class="disclaimer">预测基于九维专业分析 + 分析师研判。足球偶然性极强，请结合风险标签理性参考。</div>
  `;
}

function renderRows(matches) {
  if (!matches.length) {
    rowsEl.innerHTML = `<tr><td colspan="9" class="empty">当前筛选条件下无比赛</td></tr>`;
    return;
  }

  rowsEl.innerHTML = matches
    .map(
      (m) => `
    <tr data-id="${m.match_id}">
      <td>#${m.match_id}</td>
      <td>
        <span class="team-name">${escapeHtml(m.home_display)}</span>
        <span class="small">vs</span>
        <span class="team-name">${escapeHtml(m.away_display)}</span>
        <span class="small">${escapeHtml(m.venue)} · ${escapeHtml(m.city)}</span>
      </td>
      <td>${escapeHtml(m.stage)}${m.group ? `<span class="small">${m.group}组</span>` : ""}</td>
      <td>${escapeHtml(m.time_et)}</td>
      <td><strong>${escapeHtml(m.predicted_score)}</strong><span class="small">xG ${m.predicted_home_goals}:${m.predicted_away_goals}</span></td>
      <td>
        <div class="wdl-bar">
          <div class="wdl-row"><span>主胜</span><span class="positive">${fmtPct(m.win_prob)}</span></div>
          <div class="wdl-row"><span>平局</span><span class="neutral">${fmtPct(m.draw_prob)}</span></div>
          <div class="wdl-row"><span>客胜</span><span class="negative">${fmtPct(m.loss_prob)}</span></div>
        </div>
        <span class="small ${outcomeClass(m.outcome)}">→ ${escapeHtml(m.outcome)}</span>
      </td>
      <td>${fmtPct(m.confidence)}</td>
      <td class="detail-text">${escapeHtml(m.key_factors.join(" · "))}</td>
      <td><button class="mini-btn detail-btn" data-id="${m.match_id}" type="button">详情</button></td>
    </tr>
  `
    )
    .join("");
}

function renderDetail(match) {
  detailTitle.textContent = `${match.home_display} vs ${match.away_display}`;
  const scores = match.top_scores
    .map((s) => `<li>${s.home}-${s.away}（${fmtPct(s.probability)}）</li>`)
    .join("");

  detailBody.innerHTML = `
    <div class="detail-grid">
      <div class="metric"><span>比赛日期</span><strong>${escapeHtml(match.date)} ${escapeHtml(match.time_et)} ET</strong></div>
      <div class="metric"><span>赛段</span><strong>${escapeHtml(match.stage)}</strong></div>
      <div class="metric"><span>球场</span><strong>${escapeHtml(match.venue)}</strong></div>
      <div class="metric"><span>预测比分</span><strong>${escapeHtml(match.predicted_score)}</strong></div>
      <div class="metric"><span>预测结果</span><strong class="${outcomeClass(match.outcome)}">${escapeHtml(match.outcome)}</strong></div>
      <div class="metric"><span>置信度</span><strong>${fmtPct(match.confidence)}</strong></div>
    </div>
    <div class="plan-grid">
      <div class="metric"><span>主胜概率</span><strong class="positive">${fmtPct(match.win_prob)}</strong></div>
      <div class="metric"><span>平局概率</span><strong class="neutral">${fmtPct(match.draw_prob)}</strong></div>
      <div class="metric"><span>客胜概率</span><strong class="negative">${fmtPct(match.loss_prob)}</strong></div>
      <div class="metric"><span>期望进球</span><strong>${match.predicted_home_goals} : ${match.predicted_away_goals}</strong></div>
    </div>
    <div>
      <h3>最可能比分 Top 5</h3>
      <ol class="score-list">${scores}</ol>
    </div>
    <div>
      <h3>分析师解读</h3>
      <ol class="reasons">${match.analysis.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ol>
    </div>
    <div class="tactical-box">
      <strong>战术展望：</strong>${escapeHtml(match.tactical)}
    </div>
    ${renderDimensions(match.dimensions, match)}
    ${match.uncertainty_note ? `<div class="warn-box">${escapeHtml(match.uncertainty_note)}</div>` : ""}
    <div class="disclaimer">本分析由五维综合模型生成，不构成投注建议。红牌、点球误判、临场伤病等不可预测因素仍可能改变结果。</div>
  `;
  detailModal.classList.remove("hidden");
}

async function runAnalysis() {
  const date = matchDateEl.value;
  if (!date) return;

  runBtn.disabled = true;
  statusEl.textContent = `正在分析 ${date} 的世界杯赛事...`;

  try {
    const res = await fetch(`/api/analyze?date=${encodeURIComponent(date)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "分析请求失败");
    }
    lastPayload = await res.json();
    lastResults = lastPayload.matches || [];

    const filtered = applyFilters(lastResults);
    statusEl.textContent = lastPayload.day_summary || `共 ${lastResults.length} 场比赛`;
    renderFeatured(lastPayload.featured);
    renderRows(filtered);
  } catch (e) {
    statusEl.textContent = `分析失败：${e.message}`;
    rowsEl.innerHTML = `<tr><td colspan="9" class="empty">${escapeHtml(e.message)}</td></tr>`;
    featuredEl.classList.add("hidden");
  } finally {
    runBtn.disabled = false;
  }
}

function rerenderFilters() {
  if (!lastResults.length) return;
  const filtered = applyFilters(lastResults);
  renderRows(filtered);
}

runBtn.addEventListener("click", runAnalysis);
stageFilterEl.addEventListener("change", rerenderFilters);
confidenceFilterEl.addEventListener("change", rerenderFilters);
hideDrawEl.addEventListener("change", rerenderFilters);
marketDivOnlyEl.addEventListener("change", rerenderFilters);

helpBtn.addEventListener("click", () => helpPanel.classList.remove("hidden"));
helpClose.addEventListener("click", () => helpPanel.classList.add("hidden"));

rowsEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".detail-btn");
  if (!btn) return;
  const id = Number(btn.dataset.id);
  const match = lastResults.find((m) => m.match_id === id);
  if (match) renderDetail(match);
});

detailClose.addEventListener("click", () => detailModal.classList.add("hidden"));
detailModal.addEventListener("click", (e) => {
  if (e.target === detailModal) detailModal.classList.add("hidden");
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") detailModal.classList.add("hidden");
});
