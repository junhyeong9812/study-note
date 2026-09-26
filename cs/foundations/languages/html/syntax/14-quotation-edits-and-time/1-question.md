# html/syntax/14 — 인용·편집·시각: `blockquote`/`q`/`cite`·`ins`/`del`·`time` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제에는 **「없다」가 세 가지** 있다 — 재 봤더니 같았다 · 잴 것이 없다 · 못 잰 것. 답할 때 **어느 「없다」인지**를 같이 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [13번 주제](../13-phrasing-semantics/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `<q>` 를 겹쳐 쓰고 글자를 읽으면 (예측)

```html
<!-- html13b-14-q.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 q 의 따옴표</title>
</head>
<body>
<p id="ko">ko: <q>바깥 <q>안쪽 <q>셋째</q></q></q></p>
<p id="en" lang="en">en: <q>outer <q>inner</q></q></p>
<p id="fr" lang="fr">fr: <q>dehors <q>dedans</q></q></p>
<p id="ja" lang="ja">ja: <q>外 <q>内</q></q></p>
<p id="de" lang="de">de: <q>außen <q>innen</q></q></p>
<p id="없음" lang="">lang="": <q>바깥 <q>안쪽</q></q></p>
<script>
window.__대상 = [];
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("창 ③ — 따옴표는 글자로 남나");
  for (const id of ["ko", "en", "fr", "ja", "de", "없음"]) {
    const p = document.getElementById(id);
    O.push("  #" + id.padEnd(4) + " innerText   = " + J(p.innerText));
    O.push("  " + " ".repeat(6) + "textContent = " + J(p.textContent));
  }
  O.push("");
  O.push("창 ② — 따옴표를 누가 만드나");
  const q = document.querySelector("#ko q");
  O.push("  getComputedStyle(q, '::before').content = " + getComputedStyle(q, "::before").content);
  O.push("  getComputedStyle(q, '::after').content  = " + getComputedStyle(q, "::after").content);
  for (const id of ["ko", "en", "fr", "ja", "de", "없음"])
    O.push("  #" + id.padEnd(4) + " quotes = " + getComputedStyle(document.querySelector("#" + id + " q")).quotes);
  O.push("  자식 노드 = " + [...q.childNodes].map(n => n.nodeName).join(", "));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `#ko` 의 `innerText` 에 따옴표가 들어가는가?
- `textContent` 는?
- `--dump-dom` 트리에는 따옴표 노드가 생기는가?
- `::before` 의 계산값 `content` 는 무엇인가?

### 2. 같은 파일을 접근성 트리로 찍으면 (예측)

- 1번 소스 그대로다. 트리에 따옴표가 **글자로** 나오는가?
- `ko`·`fr`·`ja`·`de` 의 바깥/안쪽 따옴표를 하나씩 적어라.
- `ko` 의 **세 겹째** 따옴표는 무엇인가?
- 여섯 줄의 `quotes` 계산값이 같은데 글자가 갈린다면, 무엇이 고르는가?

### 3. `cite` 속성은 어디로 가나 (예측)

```html
<!-- html13b-14-cite.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 cite 속성과 cite 요소</title>
<base href="https://example.org/doc/">
</head>
<body>
<blockquote id="bq" cite="notes/talk.html#p3">
  <p>블록 인용의 본문</p>
</blockquote>
<p>짧은 인용 <q id="q" cite="https://example.com/a b">q 의 본문</q> 끝.</p>
<p><cite id="ci">어린 왕자</cite> 에서 인용했다.</p>
<p>값이 <del id="del" cite="log.html" datetime="2026-09-01">1만 원</del><ins id="ins" datetime="2026-09-26T09:00+09:00">2만 원</ins> 이 됐다.</p>
<script>
window.__대상 = [["bq", "#bq"], ["q", "#q"], ["ci", "#ci"], ["del", "#del"], ["ins", "#ins"]];
const $ = id => document.getElementById(id);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("cite 속성 — 속성값 · IDL 이 돌려주는 값 · 접근성 노드");
  for (const id of ["bq", "q", "del"]) {
    const el = $(id), a = __AX[id];
    O.push("  #" + id.padEnd(4) + "getAttribute = " + J(el.getAttribute("cite")));
    O.push("        .cite        = " + J(el.cite));
    O.push("        역할 = " + a.역할 + " · 이름 = " + J(a.이름) + " · 설명 = " + J(a.설명)
      + " · 속성 = " + J(Object.keys(a.속성)));
  }
  O.push("");
  O.push("cite 요소 · ins/del — 계산 스타일과 역할");
  for (const id of ["bq", "ci", "del", "ins"]) {
    const c = getComputedStyle($(id));
    O.push("  #" + id.padEnd(4) + "display = " + c.display.padEnd(7) + "font-style = " + c.fontStyle.padEnd(7)
      + "text-decoration = " + c.textDecorationLine.padEnd(13) + "margin-left = " + c.marginLeft.padEnd(5)
      + "역할 = " + __AX[id].역할);
  }
  O.push("");
  O.push("ins/del 의 datetime");
  for (const id of ["del", "ins"])
    O.push("  #" + id.padEnd(4) + ".dateTime = " + J($(id).dateTime));
  O.push("");
  O.push("창 ③ — 지운 글자도 글자인가");
  O.push("  innerText = " + J($("del").parentNode.innerText));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `#bq` 와 `#q` 의 `.cite` 는 각각 무엇인가? `getAttribute` 와 같은가?
- `cite` 속성이 **접근성 노드**에 나타나는가?
- `<cite>` 요소의 `font-style` 과 역할은?
- `del` 이 들어간 문단의 `innerText` 에 `1만 원` 이 있는가?

### 4. `time` 에 열네 가지를 넣으면 (예측)

```html
<!-- html13b-14-time.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 time 의 datetime</title>
</head>
<body>
<ul>
<li><time id="t1" datetime="2026-09-26">오늘</time> 날짜
<li><time id="t2" datetime="2026-09">이번 달</time> 달
<li><time id="t3" datetime="09-26">매년 이날</time> 연도 없는 날짜
<li><time id="t4" datetime="14:30">오후 두 시 반</time> 시각
<li><time id="t5" datetime="2026-09-26T14:30+09:00">오늘 오후</time> 전역 날짜·시각
<li><time id="t6" datetime="2026-W39">39주</time> 주
<li><time id="t7" datetime="2026">올해</time> 연도
<li><time id="t8" datetime="PT2H">두 시간</time> 기간
<li><time id="t9" datetime="2026-02-30">없는 날</time> 틀림 — 2월 30일
<li><time id="t10" datetime="26/09/2026">슬래시</time> 틀림 — 형식
<li><time id="t11" datetime="내일">내일</time> 틀림 — 낱말
<li><time id="t12" datetime="">빈 값</time> 틀림 — 빈 문자열
<li><time id="t13">2026-09-26</time> datetime 없음 — 내용이 값
<li><time id="t14">어제</time> datetime 없음 — 내용도 틀림
</ul>
<script>
const 번호 = Array.from({ length: 14 }, (_, i) => "t" + (i + 1));
window.__대상 = 번호.map(id => [id, "#" + id]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push(" #   " + "getAttribute".padEnd(26) + ".dateTime".padEnd(26) + "역할  이름  설명  속성  display  innerText");
  const 틀린것 = new Set(["t9", "t10", "t11", "t12", "t14"]);
  const 서명 = {};
  for (const id of 번호) {
    const el = document.getElementById(id), a = __AX[id];
    const 줄 = [a.역할, J(a.이름), J(a.설명), J(Object.keys(a.속성)), getComputedStyle(el).display];
    서명[id] = 줄.join("|");
    O.push((" " + id).padEnd(5) + J(el.getAttribute("datetime")).padEnd(26) + J(el.dateTime).padEnd(26)
      + 줄.join("  ") + "  " + J(el.innerText));
  }
  O.push("");
  O.push("유효한 것과 틀린 것이 갈리는 칸 — 역할·이름·설명·속성·display 다섯 칸을 t1 과 견준다");
  let 갈림 = 0, 전체 = 0;
  for (const id of 번호) {
    if (id === "t1") continue;
    const a = 서명.t1.split("|"), b = 서명[id].split("|");
    a.forEach((v, i) => { 전체++; if (v !== b[i]) 갈림++; });
  }
  O.push("갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- `t9`(`2026-02-30`)·`t11`(`내일`)의 `.dateTime` 은?
- `t13`(`datetime` 없이 내용이 `2026-09-26`)의 `.dateTime` 은?
- 마지막 줄 「**갈린 칸 = N / 65**」 의 N 은?
- 콘솔에 몇 줄이 찍히는가?

### 5. `<q>` 안에 따옴표를 손으로 쓰면 안 되는 이유 (왜)

- 명세는 그것을 어떻게 적는가?
- 손으로 쓴 따옴표는 **`lang` 이 바뀌면** 어떻게 되는가?
- 그럼에도 글자 따옴표를 직접 써야 하는 자리는 어디인가?

### 6. 「검증자가 없다」 대 「잴 것이 없다」 대 「못 잰 것」 (경계)

- 틀린 `datetime` 의 결과 0 / 65 는 셋 중 무엇인가?
- `cite` 속성의 **요청**은 셋 중 무엇인가?
- HTML-AAM 이 적는 **`datetime` 의 플랫폼 속성**은 셋 중 무엇인가?
- 「어느 형식이 유효한가」를 이 문서가 **실행으로** 말할 수 있는가?

### 7. 「datetime 값」과 `.dateTime` 은 같은가 (경계)

- 명세가 정한 「datetime 값」은 `datetime` 속성이 없을 때 무엇인가?
- `.dateTime` 은 그때 무엇을 돌려주는가? 왜인가(IDL 의 어느 규칙)?
- `.cite` 와 `.dateTime` 의 반영 규칙은 무엇이 다른가?

### 8. 명세·구현·관찰 가르기 (경계)

- `q::before { content: open-quote }` 는 어느 층인가?
- `fr` 의 따옴표가 `«` 라는 것은 어느 층인가? HTML 명세에 그 표가 있는가?
- `<cite>` 가 `generic` 인 것은?

### 9. 정본 경계 긋기 (연결)

- **`::before`·`content`·`quotes` 가 상자를 만드는 방식**의 정본은?
- **반영(reflect) 의 일반 규칙**의 정본은?
- **날짜를 브라우저가 실제로 파싱하는 자리**는 어느 주제인가?
- **`lang` 이 미치는 영향 전체**는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
