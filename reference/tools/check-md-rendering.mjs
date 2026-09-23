// 마크다운이 **의도대로 렌더되는지** 검사한다. 지금 두 가지를 본다.
//
//   ① 볼드(`**…**`)가 안 닫혀 별표가 그대로 보이는 것
//   ② 범위 표기의 물결표(`0~1023`)가 GFM 취소선으로 먹혀 **글자가 지워지는 것**
//   ③ 표의 칸 수가 행마다 다른 것 (셀 안의 `|` 를 이스케이프 안 해서)
//
// ②가 ①보다 나쁘다 — 별표가 보이는 정도가 아니라 본문이 삭제된 것처럼 보인다.
// 실측: `well-known은 0~1023, 등록은 1024~49151` -> `0<del>1023, 등록은 1024</del>49151`
// 고치는 법은 물결표를 이스케이프(`0\~1023`)하는 것. 의도한 취소선 `~~…~~` 는 그대로 둔다.
//
// ---------------------------------------------------------------------------
// ① 볼드가 왜 깨지나
//
// 왜 필요한가
// -----------
// CommonMark 는 닫는 `**` 가 **오른쪽 밀착(right-flanking)** 일 때만 볼드를 닫는다.
// 닫는 `**` 바로 앞이 문장부호이고 바로 뒤가 글자면 밀착 조건이 깨져 **볼드가 안 닫히고
// 별표가 그대로 보인다.** 한국어 문서에서 이 조합이 자연스럽게 자주 나온다:
//
//     **이동(move)**이고      -> 깨짐   (앞이 `)`, 뒤가 `이`)
//     **"인용"**가            -> 깨짐
//     **「보장」**이다         -> 깨짐
//     **`code`**를            -> 깨짐
//     **문자 **(양끝 공백)     -> 깨짐   (닫는 ** 앞이 공백)
//
// 고치는 법은 **꼬리 문장부호를 볼드 밖으로 빼는 것**이다. 뜻과 띄어쓰기가 그대로 남는다:
//
//     **이동**(move)이고 · "**인용**"가 · 「**보장**」이다 · `code`를
//
// 실측(2026-09-21): repo 전체에서 877건이 이렇게 깨져 있었다.
//
// 왜 정규식으로 안 찾나
// --------------------
// 한 줄에 볼드가 여럿이면 정규식이 **짝을 가로질러** 잡아 거짓 양성이 쏟아진다.
// 여러 줄에 걸친 볼드도 줄 단위로 보면 전부 깨진 것처럼 보인다.
// 그래서 **파일 전체를 실제로 렌더해서** 본문에 `**` 가 남았는지로 판정한다.
// 렌더러는 배포가 쓰는 것과 같은 micromark + remark-gfm 이다(react-markdown 이 이것을 쓴다).
//
// 쓰는 법
// -------
//     find . -name '*.md' -not -path './.git/*' > /tmp/md.txt
//     node reference/tools/check-bold-rendering.mjs /tmp/md.txt
//
// 코드 블록·인라인 코드 안의 `**` 는 제외한다(JS 의 거듭제곱 연산자 등).

import fs from 'fs';
import path from 'path';

const NM = process.env.MICROMARK_DIR
  || '/home/jun/project/deploy-study-note/study-note-deploy-system-front/node_modules/';
const { micromark } = await import(path.join(NM, 'micromark/index.js'));
const { gfm, gfmHtml } = await import(path.join(NM, 'micromark-extension-gfm/index.js'));

const listFile = process.argv[2];
if (!listFile) {
  console.error('쓰는 법: node check-bold-rendering.mjs <검사할 .md 경로가 줄마다 적힌 파일>');
  process.exit(2);
}

const files = fs.readFileSync(listFile, 'utf8').trim().split('\n').filter(Boolean);
let scanned = 0;
const bad = [];

for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  if (!src.includes('**')) continue;
  scanned++;
  let html = micromark(src, { extensions: [gfm()], htmlExtensions: [gfmHtml()] });
  html = html.replace(/<pre[\s\S]*?<\/pre>/g, '').replace(/<code[\s\S]*?<\/code>/g, '');
  const hits = html.match(/[^\n]{0,70}\*\*[^\n]{0,40}/g);
  if (hits) bad.push([f, hits]);
}

const total = bad.reduce((a, b) => a + b[1].length, 0);
console.log(`[볼드] ** 를 쓰는 파일 ${scanned}개 검사 · 렌더 후 ** 가 본문에 남은 파일 ${bad.length}개 · 총 ${total}건`);
for (const [f, hits] of bad) {
  console.log('  ' + f + `  (${hits.length}건)`);
  for (const h of hits.slice(0, 3)) console.log('      ' + h.replace(/\s+/g, ' ').trim());
}

// ③ 표의 칸 수가 행마다 다른 것 — 대개 셀 안의 `|` 를 이스케이프하지 않아서다.
//    ★★ 렌더 결과로는 못 잡는다. GFM 은 **머리글 칸 수에 맞춰 잘라내므로**
//    `<td>` 개수는 그대로이고 **넘친 칸의 글자가 통째로 사라진다**(실측으로 확인).
//    그래서 이 검사만 원본에서 센다 — 이스케이프되지 않은 `|` 의 개수를 행마다 비교한다.
//    코드 스팬 안의 `|` 도 GFM 은 칸 구분자로 본다. 그것이 바로 이 사고의 모양이다.
function countPipes(line) {
  let n = 0;
  for (let i = 0; i < line.length; i++) {
    if (line[i] === '\\') { i++; continue; }      // `\|` 는 건너뛴다
    if (line[i] === '|') n++;
  }
  return n;
}

const tableBad = [];
let tableTotal = 0;
for (const f of files) {
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  let fence = false, head = null, headLine = 0;
  lines.forEach((line, idx) => {
    if (line.trimStart().startsWith('```')) { fence = !fence; return; }
    if (fence) return;
    const t = line.trim();
    const isRow = t.startsWith('|') && t.endsWith('|');
    if (!isRow) { head = null; return; }
    if (/^\|[\s:|-]+\|$/.test(t)) return;          // 구분선
    const n = countPipes(t);
    if (head === null) { head = n; headLine = idx + 1; return; }
    if (n !== head) {
      tableBad.push([f, idx + 1,
        `${n - 1}칸 (${headLine}행 머리글은 ${head - 1}칸) — 셀 안의 | 를 \\| 로 이스케이프했는지 보라`,
        t.slice(0, 70)]);
      tableTotal++;
    }
  });
}
console.log(`[표] 칸 수가 머리글과 다른 행 ${tableTotal}건`);
for (const [f, ln, why, txt] of tableBad.slice(0, 12)) {
  console.log(`  ${f}:${ln}  ${why}`);
  console.log(`      ${txt}`);
}

// ② 의도치 않은 취소선 — 소스의 `~~` 쌍 수보다 <del> 이 많으면 범위 표기가 먹힌 것이다
const strike = [];
let strikeTotal = 0;
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  if (!src.includes('~')) continue;
  let html = micromark(src, { extensions: [gfm()], htmlExtensions: [gfmHtml()] });
  html = html.replace(/<pre[\s\S]*?<\/pre>/g, '').replace(/<code[\s\S]*?<\/code>/g, '');
  const dels = html.match(/<del>[\s\S]{0,80}?<\/del>/g);
  if (!dels) continue;
  const intended = (src.match(/~~/g) || []).length / 2;
  if (dels.length > intended) {
    strike.push([f, dels.length - intended, dels.slice(0, 2)]);
    strikeTotal += dels.length - intended;
  }
}
console.log(`[취소선] 범위 표기가 취소선으로 먹힌 파일 ${strike.length}개 · 약 ${strikeTotal}건`);
for (const [f, n, ex] of strike) {
  console.log('  ' + f + `  (${n}건)`);
  for (const d of ex) console.log('      ' + d.replace(/\s+/g, ' '));
}

process.exit(total + strikeTotal + tableTotal ? 1 : 0);
