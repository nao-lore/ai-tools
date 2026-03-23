// X Bookmarks URL Extractor
// ブックマークバーに登録して、x.com/i/bookmarks で実行する
//
// 使い方:
// 1. Chromeのブックマークバーに新しいブックマークを作成
// 2. 名前: 「X抽出」
// 3. URL欄に以下のワンライナーを貼り付け:
//
// javascript:void(function(){const a=[...document.querySelectorAll('article')],u=[];a.forEach(e=>{const l=e.querySelector('a[href*="/status/"]time')?.parentElement;if(l){const h=l.href.split('?')[0];if(!u.includes(h))u.push(h)}});if(!u.length){alert('ツイートが見つかりません。ブックマークページでスクロールしてから再実行してください。');return}const d=document.createElement('div');d.id='xt-picker';d.innerHTML='<div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:99999;display:flex;align-items:center;justify-content:center"><div style="background:#1a1a2e;border-radius:12px;padding:24px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto;color:#e0e0e0;font-family:system-ui"><h2 style="margin:0 0 16px;color:#fff">X抽出 ('+u.length+'件)</h2><div id="xt-list"></div><div style="margin-top:16px;display:flex;gap:8px"><button id="xt-all" style="padding:8px 16px;background:#1d9bf0;color:#fff;border:none;border-radius:8px;cursor:pointer">全選択</button><button id="xt-none" style="padding:8px 16px;background:#333;color:#fff;border:none;border-radius:8px;cursor:pointer">全解除</button><button id="xt-copy" style="padding:8px 16px;background:#00ba7c;color:#fff;border:none;border-radius:8px;cursor:pointer;margin-left:auto">コピー</button><button id="xt-close" style="padding:8px 16px;background:#555;color:#fff;border:none;border-radius:8px;cursor:pointer">閉じる</button></div></div></div>';document.body.appendChild(d);const list=d.querySelector('#xt-list');u.forEach((url,i)=>{const id=url.split('/status/')[1];const user=url.split('.com/')[1].split('/')[0];const div=document.createElement('div');div.style.cssText='padding:8px;border-bottom:1px solid #333;display:flex;align-items:center;gap:8px';div.innerHTML='<input type="checkbox" checked class="xt-cb" data-url="'+url+'" style="width:18px;height:18px;cursor:pointer"><span style="color:#888">@'+user+'</span><span style="color:#aaa;font-size:12px">/'+id+'</span>';list.appendChild(div)});d.querySelector('#xt-all').onclick=()=>d.querySelectorAll('.xt-cb').forEach(c=>c.checked=true);d.querySelector('#xt-none').onclick=()=>d.querySelectorAll('.xt-cb').forEach(c=>c.checked=false);d.querySelector('#xt-close').onclick=()=>d.remove();d.querySelector('#xt-copy').onclick=()=>{const sel=[...d.querySelectorAll('.xt-cb:checked')].map(c=>c.dataset.url);if(!sel.length){alert('1つ以上選択してください');return}navigator.clipboard.writeText(sel.join('\\n')).then(()=>{const btn=d.querySelector('#xt-copy');btn.textContent='コピー済み! ('+sel.length+'件)';btn.style.background='#00875a';setTimeout(()=>d.remove(),1000)})}}())
//
// ↑ この1行をURL欄に貼り付ける

// === 以下は読みやすい版（参考用） ===

void(function() {
  // 全articleからツイートURLを抽出
  const articles = [...document.querySelectorAll('article')];
  const urls = [];

  articles.forEach(article => {
    // ツイートの日時リンクからURLを取得（最も正確）
    const timeLink = article.querySelector('a[href*="/status/"]time')?.parentElement;
    if (timeLink) {
      const href = timeLink.href.split('?')[0]; // クエリパラメータ除去
      if (!urls.includes(href)) {
        urls.push(href);
      }
    }
  });

  if (!urls.length) {
    alert('ツイートが見つかりません。ブックマークページでスクロールしてから再実行してください。');
    return;
  }

  // ピッカーUIを表示
  const overlay = document.createElement('div');
  overlay.id = 'xt-picker';
  // ... (UIは上のワンライナーと同じ)

  // チェックボックス付きリスト表示
  // 「全選択」「全解除」「コピー」ボタン
  // 選択したURLをクリップボードにコピー
}());
