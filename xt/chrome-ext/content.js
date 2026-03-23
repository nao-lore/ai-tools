// X抽出 — ツイートをタップで選択してURLコピー（全ページ対応）

const selected = new Set();
let bar = null;
let lastUrl = location.href;

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
  document.querySelectorAll("article").forEach(setupArticle);
  // DOM再生成で xt-selected が消えたarticleを再ハイライト
  document.querySelectorAll("article").forEach((article) => {
    const url = getTweetUrl(article);
    if (url && selected.has(url)) {
      article.classList.add("xt-selected");
    }
  });
}

// ビューポート内のarticleだけ返す
function getVisibleArticles() {
  const articles = document.querySelectorAll("article");
  const visible = [];
  for (const article of articles) {
    const rect = article.getBoundingClientRect();
    // 画面内に少しでも見えていればOK
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
    const btn = document.querySelector(".xt-btn-copy");
    if (btn) {
      btn.textContent = `コピー済み (${urls.length}件)`;
      btn.style.background = "#00875a";
      setTimeout(() => {
        btn.textContent = "コピー";
        btn.style.background = "";
      }, 2000);
    }
  } catch (e) {
    const ta = document.createElement("textarea");
    ta.value = urls.join("\n");
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
}

function initBar() {
  bar = document.createElement("div");
  bar.id = "xt-bar";
  bar.innerHTML = `
    <span id="xt-count">0</span><span>件選択</span>
    <button class="xt-btn-select" id="xt-sel-visible">表示中を選択</button>
    <button class="xt-btn-select xt-btn-recent" id="xt-sel-50">直近50件</button>
    <button class="xt-btn-cancel" id="xt-desel">全解除</button>
    <button class="xt-btn-copy">コピー</button>
    <button class="xt-btn-close" id="xt-close">✕</button>
  `;
  document.body.appendChild(bar);

  bar.querySelector("#xt-sel-visible").addEventListener("click", selectVisible);
  bar.querySelector("#xt-sel-50").addEventListener("click", selectRecent50);
  bar.querySelector("#xt-desel").addEventListener("click", deselectAll);
  bar.querySelector(".xt-btn-copy").addEventListener("click", copySelected);
  bar.querySelector("#xt-close").addEventListener("click", () => {
    deselectAll();
    bar.classList.add("xt-hidden");
    document.body.classList.add("xt-disabled");
  });
}

// SPA ナビゲーション検知
function onNavigate() {
  // URL変更時にarticleを再スキャン（selectionは保持）
  scanArticles();
  // バーが非表示でなければ表示を維持
}

function checkUrlChange() {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    onNavigate();
  }
}

// 初期化
initBar();
scanArticles();

// DOM変更を監視（Xがarticleを再生成するたびに復元）
new MutationObserver(scanArticles).observe(document.body, {
  childList: true,
  subtree: true,
});

// SPA navigation: popstate + polling (pushState doesn't fire popstate)
window.addEventListener("popstate", () => {
  lastUrl = location.href;
  onNavigate();
});

// Navigation API (Chrome 102+) for pushState/replaceState detection
if (typeof navigation !== "undefined") {
  navigation.addEventListener("navigate", () => {
    setTimeout(() => {
      lastUrl = location.href;
      onNavigate();
    }, 300);
  });
}

// スクロール時にも定期的に復元 + URL変更チェック
setInterval(() => {
  checkUrlChange();
  document.querySelectorAll("article").forEach((article) => {
    const url = getTweetUrl(article);
    if (url && selected.has(url) && !article.classList.contains("xt-selected")) {
      article.classList.add("xt-selected");
    }
    if (!article.dataset.xtReady) setupArticle(article);
  });
}, 300);
