const sportEl = document.getElementById("sport");
const minutesEl = document.getElementById("minutes");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");

document.getElementById("gamesBtn").addEventListener("click", loadGames);
document.getElementById("analyzeBtn").addEventListener("click", analyze);

let chartRegistry = {};

function params() {
  return `sport=${encodeURIComponent(sportEl.value)}&minutes=${encodeURIComponent(minutesEl.value)}`;
}

function setStatus(text) {
  statusEl.innerHTML = text ? `<div class="notice">${text}</div>` : "";
}

function decisionFromMarket(m) {
  const odds = Number(m.odds || 0);
  const openOdds = Number(m.open_odds || 0);
  const avg = Number(m.market_avg || 0);
  const dropRate = openOdds > 0 ? ((openOdds - odds) / openOdds) * 100 : 0;
  const edge = avg > 0 ? ((avg - odds) / odds) * 100 : 0;
  if (dropRate >= 5 && edge >= 2) return "BET";
  if (dropRate >= 2 || edge >= 1) return "WATCH";
  return "NO BET";
}

function decisionClass(decision) {
  if (decision === "BET") return "bet";
  if (decision === "WATCH") return "watch";
  return "nobet";
}

function riskLabel(risk) {
  if (risk === "low") return "낮음";
  if (risk === "medium") return "보통";
  if (risk === "high") return "높음";
  return risk || "-";
}

function chartId(index) {
  return `oddsChart_${index}`;
}

function destroyCharts() {
  Object.values(chartRegistry).forEach(chart => {
    try { chart.destroy(); } catch (e) {}
  });
  chartRegistry = {};
}

function drawOddsChart(canvasId, history) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !window.Chart || !history || history.length === 0) return;

  if (chartRegistry[canvasId]) {
    chartRegistry[canvasId].destroy();
  }

  chartRegistry[canvasId] = new Chart(canvas, {
    type: "line",
    data: {
      labels: history.map(h => h.time),
      datasets: [{
        label: "배당",
        data: history.map(h => h.odds),
        tension: 0.35,
        pointRadius: 4,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: true } },
      scales: {
        x: { ticks: { color: "rgba(255,255,255,0.75)" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { ticks: { color: "rgba(255,255,255,0.75)" }, grid: { color: "rgba(255,255,255,0.06)" } }
      }
    }
  });
}

function bookmakerTable(bookmakers) {
  if (!bookmakers || bookmakers.length === 0) return "";
  return `
    <div class="book-table">
      <h3>북메이커 배당</h3>
      ${bookmakers.map(b => `
        <div class="book-row">
          <span>${b.bookmaker}</span>
          <b>${b.odds}</b>
        </div>
      `).join("")}
    </div>
  `;
}

function flowTable(market, index) {
  const history = market.history || [];
  if (!history.length) return "";

  return `
    <div class="two-col">
      <div class="book-table">
        <h3>배당 흐름</h3>
        ${history.map(h => `
          <div class="book-row">
            <span>${h.time}</span>
            <b>${h.odds}</b>
          </div>
        `).join("")}
      </div>
      <div class="book-table">
        <h3>Closing Odds 예측</h3>
        <div class="book-row"><span>현재 배당</span><b>${market.odds ?? "-"}</b></div>
        <div class="book-row"><span>예상 Closing</span><b>${market.closing_prediction ?? "-"}</b></div>
        <div class="book-row"><span>Consensus</span><b>${market.consensus_rate ?? "-"}%</b></div>
      </div>
    </div>
    <div class="chart-box">
      <h3>배당 차트</h3>
      <canvas id="${chartId(index)}"></canvas>
    </div>
  `;
}

function renderGames(games) {
  destroyCharts();

  if (!games || games.length === 0) {
    resultsEl.innerHTML = `<div class="card">조건에 맞는 경기가 없습니다.</div>`;
    return;
  }

  resultsEl.innerHTML = games.map((game, index) => {
    const market = (game.markets || [])[0] || {};
    const decision = decisionFromMarket(market);
    const odds = Number(market.odds || 0);
    const openOdds = Number(market.open_odds || 0);
    const avg = Number(market.market_avg || 0);
    const pinnacle = Number(market.pinnacle_odds || 0);
    const dropRate = openOdds > 0 ? (((openOdds - odds) / openOdds) * 100).toFixed(1) : "-";
    const edge = avg > 0 ? (((avg - odds) / odds) * 100).toFixed(1) : "-";
    const ev = pinnacle > 0 ? (((pinnacle / odds - 1) * 100).toFixed(1)) : edge;

    return `
      <article class="card game-card ${decisionClass(decision)}">
        <div class="card-top">
          <div class="tag">${game.sport || "-"} · ${game.league || "-"}</div>
          <div class="decision ${decisionClass(decision)}">${decision}</div>
        </div>
        <h2>${game.home || "-"} vs ${game.away || "-"}</h2>
        <p class="muted">시작까지 ${game.start_in_minutes ?? "-"}분</p>
        <div class="pick-box">
          <small>추천픽</small>
          <b>${market.pick || "-"}</b>
        </div>
        <div class="summary-grid">
          <div><small>현재배당</small><b>${market.odds ?? "-"}</b></div>
          <div><small>초기배당</small><b>${market.open_odds ?? "-"}</b></div>
          <div><small>Pinnacle</small><b>${market.pinnacle_odds ?? "-"}</b></div>
          <div><small>시장평균</small><b>${market.market_avg ?? "-"}</b></div>
          <div><small>하락률</small><b>${dropRate}%</b></div>
          <div><small>Edge</small><b>${edge}%</b></div>
          <div><small>EV</small><b>${ev}%</b></div>
          <div><small>북메이커</small><b>${market.bookmaker || "-"}</b></div>
          <div><small>Sharp</small><b>${market.sharp_score ?? "-"}점</b></div>
          <div><small>Steam</small><b>${market.steam_score ?? "-"}점</b></div>
          <div><small>CLV</small><b>${market.clv_score ?? "-"}점</b></div>
          <div><small>RLM</small><b>${market.rlm_score ?? "-"}점</b></div>
        </div>
        ${flowTable(market, index)}
        ${bookmakerTable(market.bookmakers || [])}
      </article>
    `;
  }).join("");

  games.forEach((game, index) => {
    const market = (game.markets || [])[0] || {};
    drawOddsChart(chartId(index), market.history || []);
  });
}

async function loadGames() {
  setStatus("경기 불러오는 중...");
  resultsEl.innerHTML = `<div class="card">불러오는 중...</div>`;
  try {
    const res = await fetch(`/api/live-games?${params()}`);
    const data = await res.json();
    setStatus(data.notice || `총 ${data.count || 0}경기`);
    renderGames(data.games);
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = `<div class="card danger">경기 불러오기 실패</div>`;
  }
}

function renderBestPick(best) {
  return `
    <article class="card highlight game-card ${decisionClass(best.decision)}">
      <div class="card-top">
        <div class="tag">🏅 BEST PICK</div>
        <div class="decision ${decisionClass(best.decision)}">${best.decision || "BET"}</div>
      </div>
      <h2>${best.game || "-"}</h2>
      <div class="pick-box">
        <small>추천픽</small>
        <b>${best.pick || "-"}</b>
      </div>
      <div class="summary-grid">
        <div><small>등급</small><b>${best.grade || "-"}</b></div>
        <div><small>신뢰도</small><b>${best.confidence ?? best.score ?? 0}%</b></div>
        <div><small>현재배당</small><b>${best.odds ?? "-"}</b></div>
        <div><small>초기배당</small><b>${best.open_odds ?? "-"}</b></div>
        <div><small>Pinnacle</small><b>${best.pinnacle_odds ?? "-"}</b></div>
        <div><small>시장평균</small><b>${best.market_avg ?? "-"}</b></div>
        <div><small>하락률</small><b>${best.drop_rate ?? "-"}%</b></div>
        <div><small>EV</small><b>${best.ev ?? "-"}%</b></div>
        <div><small>Edge</small><b>${best.ai_edge ?? "-"}%</b></div>
        <div><small>Sharp</small><b>${best.sharp_score ?? "-"}점</b></div>
        <div><small>Steam</small><b>${best.steam_score ?? "-"}점</b></div>
        <div><small>CLV</small><b>${best.clv_score ?? "-"}점</b></div>
        <div><small>RLM</small><b>${best.rlm_score ?? "-"}점</b></div>
        <div><small>Kelly</small><b>${best.kelly ?? "-"}%</b></div>
        <div><small>Consensus</small><b>${best.consensus_rate ?? "-"}%</b></div>
        <div><small>위험도</small><b>${riskLabel(best.risk)}</b></div>
      </div>
      <p class="reason">${(best.reasons || ["배당 흐름과 시장 평균 기준으로 우위가 있습니다."]).join(" · ")}</p>
      <p class="reason">AI 분석: ${best.ai_analysis || "-"}</p>
    </article>
  `;
}

function renderSummary(summary) {
  return `
    <article class="card">
      <h2>오늘 분석 요약</h2>
      <div class="summary-grid">
        <div><small>분석픽</small><b>${summary?.total_picks ?? 0}</b></div>
        <div><small>BET</small><b>${summary?.bet_count ?? 0}</b></div>
        <div><small>관찰</small><b>${summary?.watch_count ?? 0}</b></div>
        <div><small>No Bet</small><b>${summary?.no_bet_count ?? 0}</b></div>
        <div><small>평균 EV</small><b>${summary?.avg_ev ?? 0}%</b></div>
        <div><small>평균 Edge</small><b>${summary?.avg_edge ?? 0}%</b></div>
      </div>
      <p class="reason">${summary?.message || ""}</p>
    </article>
  `;
}

function renderCombos(combos) {
  if (!combos || combos.length === 0) return "";
  return `
    <article class="card highlight">
      <h2>3폴더 추천 조합</h2>
      ${combos.slice(0, 3).map(combo => `
        <div class="combo-box">
          <h3>${combo.type}</h3>
          <div class="summary-grid">
            <div><small>폴더수</small><b>${combo.folder_size}</b></div>
            <div><small>총배당</small><b>${combo.total_odds}</b></div>
            <div><small>예상 적중률</small><b>${combo.estimated_hit_rate ?? "-"}%</b></div>
            <div><small>추천 금액</small><b>${combo.stake_guide ?? "-"}</b></div>
            <div><small>평균신뢰도</small><b>${combo.avg_confidence}%</b></div>
            <div><small>평균EV</small><b>${combo.avg_ev}%</b></div>
            <div><small>평균Edge</small><b>${combo.avg_edge}%</b></div>
            <div><small>평균Kelly</small><b>${combo.avg_kelly}%</b></div>
          </div>
          <p class="reason">${combo.profile_memo || ""}</p>
          ${(combo.picks || []).map(p => `<p class="reason">• ${p.game} / ${p.pick} / ${p.odds} / 신뢰도 ${p.confidence}%</p>`).join("")}
        </div>
      `).join("")}
    </article>
  `;
}

function renderTopPicks(picks) {
  if (!picks || picks.length <= 1) return "";
  return `
    <article class="card">
      <h2>단일픽 TOP</h2>
      ${picks.slice(1, 10).map((p, i) => `
        <div class="pick">
          <div class="tag">#${i + 2} ${p.decision || "-"}</div>
          <h3>${p.game || "-"}</h3>
          <p><b>추천: ${p.pick || "-"}</b></p>
          <p>신뢰도: ${p.confidence ?? p.score ?? 0}% / EV: ${p.ev ?? "-"}% / Edge: ${p.ai_edge ?? "-"}%</p>
          <p>Sharp ${p.sharp_score ?? "-"}점 / Steam ${p.steam_score ?? "-"}점 / CLV ${p.clv_score ?? "-"}점</p>
        </div>
      `).join("")}
    </article>
  `;
}

async function analyze() {
  destroyCharts();
  setStatus("AI 분석 중...");
  resultsEl.innerHTML = `<div class="card">AI 분석 중...</div>`;
  try {
    const res = await fetch(`/api/recommendations?${params()}`);
    const data = await res.json();
    setStatus(data.notice || "AI 분석 완료");
    const picks = data.top_picks || [];
    const best = picks[0];
    if (!best) {
      resultsEl.innerHTML = `<div class="card danger">추천 가능한 픽이 없습니다.</div>`;
      return;
    }
    resultsEl.innerHTML = renderBestPick(best) + renderSummary(data.summary || {}) + renderCombos(data.combos || []) + renderTopPicks(picks);
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = `<div class="card danger">AI 분석 실패</div>`;
  }
}

loadGames();
