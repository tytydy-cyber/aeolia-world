import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';

const about=readFileSync(new URL('../outputs/about.html',import.meta.url),'utf8');
const stageDesign=readFileSync(new URL('../outputs/stage-design.html',import.meta.url),'utf8');
const index=readFileSync(new URL('../outputs/index.html',import.meta.url),'utf8');
assert.ok(index.includes('href="about.html"')&&index.includes('ゲームと制作過程'),'world select links to the introduction');
for(const [page,name] of [['aeolia.html','浮島の街'],['liminal.html?stage=parallax','閉鎖施設'],['liminal.html?stage=somnia','郊外'],['playroom.html','遊戯室']]){
  assert.ok(about.includes(`href="${page}"`),`${name} links to the actual game`);
  assert.ok(about.includes(name),`${name} is explained`);
}
for(const asset of ['floating-islands.jpg','closed-complex.jpg','solarpunk-suburb.jpg','dreamcore-playroom.jpg','traveler-ember.jpg','traveler-mist.jpg','traveler-lilac.jpg']){
  assert.ok(about.includes(asset),`${asset} appears in the page`);
  assert.ok(existsSync(new URL('../outputs/assets/thumbnails/'+asset,import.meta.url)),`${asset} exists`);
}
for(const text of ['このゲームで何をするのか','主人公は3種類','操作方法','どのように作ったか','見た目と操作のために工夫したこと','検知して修正した不具合','うまくいかなかったこと','人とAIの分担'])assert.ok(about.includes(text),`${text} section exists`);
for(const control of ['↑↓←→','WASD','SPACE','SHIFT','Ctrl','Q','C','画面スワイプ','手を振る、お辞儀、回転'])assert.ok(about.includes(control),`${control} is explained`);
for(const step of ['要望を設計へ変える','画像で方向を確認する','Blenderで立体を作る','Three.jsでゲームにする','音を付ける','動作を確認する','公開する'])assert.ok(about.includes(step),`${step} is explained`);
for(const detail of ['受け取るもの','確認方法','生成画像をそのまま歩ける空間にはできません','立体の形、色、画像、動きを一つにまとめたファイル形式','Webページの中に3D空間を表示','プログラムから機能を使うための窓口','GitHubに保存したWebページを、そのまま公開URLで配信'])assert.ok(about.includes(detail),`production detail exists: ${detail}`);
for(const bug of ['床や水面がちらつく','虹が裏から薄く見える','フードの主人公が飛ぶと頭部が欠ける','見えない壁で止まる','高く飛ぶと屋根面だけが見える'])assert.ok(about.includes(bug),`bug history includes ${bug}`);
for(const failure of ['デモ画像を先に作りすぎた','広さを増やせば探索になると考えた','閉鎖施設と郊外の差が弱かった','進捗を過大評価した','修正した問題が戻った'])assert.ok(about.includes(failure),`failure history includes ${failure}`);
assert.equal((about.match(/<figure class="bug-case">/g)||[]).length,4,'four bug mechanisms have labelled diagrams');
assert.ok(about.includes('模式図は当時の画面キャプチャではありません。'),'bug diagrams are not presented as historical screenshots');
assert.ok(about.includes('https://tytydy-cyber.github.io/aeolia-world/')&&about.includes('assets/aeolia-world-qr.svg'),'public URL and QR code are shown together');
assert.ok(existsSync(new URL('../outputs/assets/aeolia-world-qr.svg',import.meta.url)),'QR code asset exists');
assert.ok(about.includes('約13秒の紹介映像')&&about.includes('<video controls')&&about.includes('assets/aeolia-introduction.mp4'),'the finished trailer is embedded near the end');
assert.ok(existsSync(new URL('../outputs/assets/aeolia-introduction.mp4',import.meta.url)),'embedded trailer exists');
assert.ok(about.includes('href="stage-design.html"'),'introduction links to the written stage requirements');
for(const stage of ['浮島の街','閉鎖施設','郊外','遊戯室'])assert.ok(stageDesign.includes(`<h2>${stage}</h2>`)&&stageDesign.includes('現在の未達'),`${stage} states its design and remaining gap`);
for(const requirement of ['世界観の定義','区域と回遊','要件','確認方法','完成条件'])assert.ok(stageDesign.includes(requirement),`stage requirements explain ${requirement}`);
assert.ok(about.includes('.label,.step-title b{display:none}')&&about.includes('.world p,.world dl,.character p')&&about.includes('font-size:13px'),'redundant bilingual labels are hidden and supporting copy has a readable size floor');
assert.ok(about.includes('h1,h2,h3,h4{text-wrap:balance}')&&about.includes('p,li,dd,figcaption{text-wrap:pretty}')&&!about.includes('<br'),'headings and copy wrap naturally without fixed line breaks');
assert.ok(about.includes('@media(max-width:760px)')&&about.includes('@media(prefers-reduced-motion:reduce)')&&about.includes(':focus-visible'),'page supports mobile, reduced motion and keyboard focus');
assert.ok(!/<h[123][^>]*>[^<]*<br>/.test(about),'headings do not force Japanese line breaks');
console.log('PASS: introduction explains the game first, then the complete production loop, fixes and failures.');
