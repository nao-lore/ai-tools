// 拡張アイコンクリックでバーの表示/非表示を切り替え
chrome.action.onClicked.addListener(async (tab) => {
  if (tab.url && (tab.url.includes("x.com") || tab.url.includes("twitter.com"))) {
    chrome.tabs.sendMessage(tab.id, { action: "toggle-bar" });
  }
});
