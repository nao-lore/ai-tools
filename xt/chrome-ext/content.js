// X抽出 — ツイートをタップで選択してURLコピー（全ページ対応）

const selected = new Set();
let bar = null;
let lastUrl = location.href;
let scanTimer = null;

function getTweetUrl(article) {
  const timeLink = article.querySelector('a[href*="/status/"] time');
  if (timeLink) {
    return timeLink.parentElement.href.split("?")[0];
  }
  return null;
}

function updateCount() {
  const el = document.getElementById("xt-count");
  if (el) el.textContent = selected.size;
}

function toggleArticle(article) {
  const url = getTweetUrl(article);
  if (!url) return;

  if (selected.has(url)) {
    selected.delete(url);
    article.classList.remove("xt-selected");
  } else {
    selected.add(url);
    article.classList.add("xt-selected");
  }
  updateCount();
}

function setupArticle(article) {
  if (article.dataset.xtReady) return;
  article.dataset.xtReady = "1";

  // 既に選択済みのURLなら見た目を復元
  const url = getTweetUrl(article);
  if (url && selected.has(url)) {
    article.classList.add("xt-selected");
  }

  article.addEventListener("click", (e) => {
    if (document.body.classList.contains("xt-disabled")) return;
    const tag = e.target.closest("a, button, video, [role='button'], [data-testid]");
    if (tag && (tag.tagName === "A" || tag.tagName === "BUTTON" || tag.tagName === "VIDEO" || tag.getAttribute("role") === "button")) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    toggleArticle(article);
  });
}

function scanArticles() {
  document.querySelectorAll("article").forEach((article) => {
    setupArticle(article);
    const url = getTweetUrl(article);
    if (url && selected.has(url) && !article.classList.contains("xt-selected")) {
      article.classList.add("xt-selected");
    }
  });
}

// デバウンス付きスキャン — DOM変更が連続しても300ms間隔に抑える
function debouncedScan() {
  if (scanTimer) return;
  scanTimer = setTimeout(() => {
    scanTimer = null;
    scanArticles();
    ensureBar();
  }, 300);
}

// ビューポート内のarticleだけ返す
function getVisibleArticles() {
  const articles = document.querySelectorAll("article");
  const visible = [];
  for (const article of articles) {
    const rect = article.getBoundingClientRect();
    if (rect.bottom > 0 && rect.top < window.innerHeight) {
      visible.push(article);
    }
  }
  return visible;
}

function selectVisible() {
  const articles = getVisibleArticles();
  articles.forEach((article) => {
    const url = getTweetUrl(article);
    if (url) {
      selected.add(url);
      article.classList.add("xt-selected");
    }
  });
  updateCount();
}

function selectRecent50() {
  const articles = document.querySelectorAll("article");
  let count = 0;
  for (const article of articles) {
    if (count >= 50) break;
    const url = getTweetUrl(article);
    if (url) {
      selected.add(url);
      article.classList.add("xt-selected");
      count++;
    }
  }
  updateCount();
}

function deselectAll() {
  selected.clear();
  document.querySelectorAll("article.xt-selected").forEach((a) => {
    a.classList.remove("xt-selected");
  });
  updateCount();
}

async function copySelected() {
  if (!selected.size) return;
  const urls = [...selected];

  try {
    await navigator.clipboard.writeText(urls.join("\n"));
    showCopyFeedback(urls.length);
  } catch (e) {
    // フォールバック: execCommand
    try {
      const ta = document.createElement("textarea");
      ta.value = urls.join("\n");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      showCopyFeedback(urls.length);
    } catch (e2) {
      // 最終フォールバック: プロンプト表示
      window.prompt("コピーに失敗しました。手動でコピーしてください:", urls.join("\n"));
    }
  }
}

function showCopyFeedback(count) {
  const btn = document.querySelector(".xt-btn-copy");
  if (btn) {
    btn.textContent = `コピー済み (${count}件)`;
    btn.style.background = "#00875a";
    setTimeout(() => {
      btn.textContent = "コピー";
      btn.style.background = "";
    }, 2000);
  }
}

function createBar() {
  const b = document.createElement("div");
  b.id = "xt-bar";
  b.innerHTML = `
    <span id="xt-count">0</span><span>件選択</span>
    <button class="xt-btn-select" id="xt-sel-visible">表示中を選択</button>
    <button class="xt-btn-select xt-btn-recent" id="xt-sel-50">直近50件</button>
    <button class="xt-btn-cancel" id="xt-desel">全解除</button>
    <button class="xt-btn-copy">コピー</button>
    <button class="xt-btn-close" id="xt-close">✕</button>
  `;

  b.querySelector("#xt-sel-visible").addEventListener("click", selectVisible);
  b.querySelector("#xt-sel-50").addEventListener("click", selectRecent50);
  b.querySelector("#xt-desel").addEventListener("click", deselectAll);
  b.querySelector(".xt-btn-copy").addEventListener("click", copySelected);
  b.querySelector("#xt-close").addEventListener("click", () => {
    deselectAll();
    b.classList.add("xt-hidden");
    document.body.classList.add("xt-disabled");
  });

  return b;
}

// バーがDOMに存在するか確認し、なければ再生成
function ensureBar() {
  if (document.body.classList.contains("xt-disabled")) return;

  const existing = document.getElementById("xt-bar");
  if (existing) {
    bar = existing;
    updateCount();
    return;
  }

  // バーがDOMから消えた → 再生成
  bar = createBar();
  document.body.appendChild(bar);
  updateCount();
}

// SPA ナビゲーション検知
function onNavigate() {
  scanArticles();
  ensureBar();
}

function checkUrlChange() {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    onNavigate();
  }
}

// --- 初期化 ---
function init() {
  bar = createBar();
  document.body.appendChild(bar);
  scanArticles();
}

// bodyが準備できてから初期化（まれにcontent scriptが早すぎるケース対策）
if (document.body) {
  init();
} else {
  document.addEventListener("DOMContentLoaded", init);
}

// DOM変更を監視（デバウンス付き）
new MutationObserver(debouncedScan).observe(document.body || document.documentElement, {
  childList: true,
  subtree: true,
});

// SPA navigation: popstate
window.addEventListener("popstate", () => {
  lastUrl = location.href;
  onNavigate();
});

// Navigation API (Chrome 102+)
if (typeof navigation !== "undefined") {
  navigation.addEventListener("navigate", () => {
    setTimeout(() => {
      lastUrl = location.href;
      onNavigate();
    }, 300);
  });
}

// タブがアクティブに戻った時に復元チェック
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    ensureBar();
    scanArticles();
  }
});

// 拡張アイコンクリックでバーを再表示
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "toggle-bar") {
    const existing = document.getElementById("xt-bar");
    if (existing && !existing.classList.contains("xt-hidden")) {
      // 表示中 → 閉じる
      deselectAll();
      existing.classList.add("xt-hidden");
      document.body.classList.add("xt-disabled");
    } else {
      // 非表示 → 再表示
      document.body.classList.remove("xt-disabled");
      if (existing) {
        existing.classList.remove("xt-hidden");
      } else {
        bar = createBar();
        document.body.appendChild(bar);
      }
      scanArticles();
      updateCount();
    }
  }
});

// 定期チェック（URL変更 + バー存在確認 + 未セットアップarticle検出）
setInterval(() => {
  checkUrlChange();
  ensureBar();
  // 未セットアップのarticleだけ処理（軽量）
  document.querySelectorAll("article:not([data-xt-ready])").forEach(setupArticle);
}, 500);
