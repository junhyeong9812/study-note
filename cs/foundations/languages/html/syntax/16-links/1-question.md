# html/syntax/16 — 링크: `href` 의 형태·`target`·`rel`(`noopener`/`noreferrer`/`nofollow`)·`download` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **화면에 없다.** 서버가 받은 `Referer` · 새 창의 `window.opener` · `a.href` 가 푼 값 — **어느 창에서 읽었나**를 같이 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 서버는 **127.0.0.1:18713(A)** 과 **127.0.0.1:18714(B)** 둘이다 — 포트가 달라 **다른 출처**다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [07번 주제](../07-id-and-fragments/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `href` 열다섯 형태의 `a.href` (예측)

```html
<!-- html13b-16-href.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 href 의 형태</title>
</head>
<body>
<p><a id="h1" href="b.html">1</a> <a id="h2" href="./b.html">2</a> <a id="h3" href="../b.html">3</a>
<a id="h4" href="/b.html">4</a> <a id="h5" href="?q=1">5</a> <a id="h6" href="#끝">6</a>
<a id="h7" href="">7</a> <a id="h8" href="//127.0.0.1:18714/b.html">8</a>
<a id="h9" href="http://127.0.0.1:18714/b.html">9</a>
<a id="h10" href="HTTP://127.0.0.1:18714/x/../%7Euser/b.html">10</a>
<a id="h11" href="  b.html  ">11</a> <a id="h12" href="javascript:void(0)">12</a>
<a id="h13" href="mailto:a@example.com">13</a> <a id="h14" href="http://[틀림">14</a>
<a id="h15">15</a></p>
<script>
const 번호 = Array.from({ length: 15 }, (_, i) => "h" + (i + 1));
window.__대상 = 번호.map(id => [id, "#" + id]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("문서 URL = " + location.href);
  O.push("");
  O.push(" #   " + "href 속성".padEnd(46) + "a.href".padEnd(58) + ":link  포커스  역할");
  for (const id of 번호) {
    const a = document.getElementById(id);
    a.focus();
    const 포커스 = document.activeElement === a ? "된다" : "안 됨";
    O.push((" " + id).padEnd(5) + (a.hasAttribute("href") ? J(a.getAttribute("href")) : "(속성 없음)").padEnd(46)
      + J(a.href).padEnd(58) + String(a.matches(":link")).padEnd(7) + 포커스.padEnd(7) + __AX[id].역할);
  }
  const 있음 = 번호.map(id => document.getElementById(id)).filter(a => a.hasAttribute("href"));
  const 그대로 = 있음.filter(a => a.href === a.getAttribute("href"));
  O.push("");
  O.push("해석해도 글자가 그대로인 칸 = " + 그대로.map(a => "#" + a.id).join(" · "));
  O.push("그대로인 칸 = " + 그대로.length + " / " + 있음.length);
  O.push("");
  O.push("rel 의 지원 토큰 — a.relList.supports()");
  const a = document.getElementById("h1");
  for (const t of ["noopener", "noreferrer", "opener", "nofollow", "stylesheet", "zzz"]) {
    let r;
    try { r = String(a.relList.supports(t)); } catch (e) { r = e.name + " 「" + e.message + "」"; }
    O.push("  " + t.padEnd(11) + r);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 문서 URL 은 `http://127.0.0.1:18713/d/html13b-16-href.html` 이다. `h3`(`../b.html`)·`h5`(`?q=1`)·`h7`(`""`) 의 `a.href` 는?
- `h8`(`//127.0.0.1:18714/b.html`)·`h10`(대문자 스킴 + `x/../`) 은?
- `h14`(`http://[틀림`) 의 `a.href` 는? `:link` 는 참인가?
- `h15`(`href` 없음)의 `:link`·포커스·역할은?

### 2. 브라우저가 처리하는 `rel` (예측)

- 1번 소스 그대로다. `a.relList.supports()` 가 참을 돌려주는 토큰은 여섯 중 어느 것인가?
- `nofollow` 는? `stylesheet` 는?
- 마지막 두 줄 「그대로인 칸 = N / 14」 의 N 은?

### 3. `rel` 조합을 하나씩 누르면 (예측)

```html
<!-- html13b-16-rel.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 rel 격자</title>
</head>
<body>
<p><a id="none" target="_blank" href="/html13b-16-dest.html?k=none">rel 없음</a></p>
<p><a id="noopener" target="_blank" rel="noopener" href="/html13b-16-dest.html?k=noopener">noopener</a></p>
<p><a id="noreferrer" target="_blank" rel="noreferrer" href="/html13b-16-dest.html?k=noreferrer">noreferrer</a></p>
<p><a id="nofollow" target="_blank" rel="nofollow" href="/html13b-16-dest.html?k=nofollow">nofollow</a></p>
<p><a id="opener" target="_blank" rel="opener" href="/html13b-16-dest.html?k=opener">opener</a></p>
<p><a id="policy" target="_blank" referrerpolicy="no-referrer" href="/html13b-16-dest.html?k=policy">referrerpolicy=no-referrer</a></p>
<p><a id="cross" target="_blank" href="http://127.0.0.1:18714/html13b-16-dest.html?k=cross">다른 출처 · rel 없음</a></p>
<p><a id="crossopener" target="_blank" rel="opener" href="http://127.0.0.1:18714/html13b-16-dest.html?k=crossopener">다른 출처 · rel=opener</a></p>
<p><a id="named" target="창이름1" href="/html13b-16-dest.html?k=named">target=창이름1 · rel 없음</a></p>
<p><a id="namednoopener" target="창이름2" rel="noopener" href="/html13b-16-dest.html?k=namednoopener">target=창이름2 · noopener</a></p>
<p><a id="namednoref" target="창이름3" rel="noreferrer" href="/html13b-16-dest.html?k=namednoref">target=창이름3 · noreferrer</a></p>
<p><a id="namedpolicy" target="창이름4" referrerpolicy="no-referrer" href="/html13b-16-dest.html?k=namedpolicy">target=창이름4 · referrerpolicy=no-referrer</a></p>
<p><a id="self" href="/html13b-16-dest.html?k=self">target 없음 (같은 탭)</a></p>
</body>
</html>
```

```html
<!-- html13b-16-dest.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>도착</title>
</head>
<body>
<p>도착한 쪽</p>
</body>
</html>
```

- `_blank · rel 없음` 의 새 창에서 `window.opener` 는?
- `_blank · noreferrer` 의 서버 `Referer` 와 `document.referrer` 는?
- `_blank · 다른 출처` 의 서버 `Referer` 는 무엇인가?
- `_blank · nofollow` 는 `rel 없음` 과 몇 칸이 갈리는가?

### 4. 이름 target 에서 (예측)

- 3번 소스의 `창이름1`\~`창이름4` 넷이다. 각각의 `window.opener` 는?
- `창이름3`(noreferrer)과 `창이름4`(referrerpolicy=no-referrer)는 몇 칸 갈리는가?
- 마지막 줄 「**갈린 칸 = N / 27**」 의 N 은?

### 5. `download` 와 `javascript:` (예측)

```html
<!-- html13b-16-dl.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 download</title>
</head>
<body>
<p><a id="same" href="/html13b-16-file.txt?k=same" download="저장한-이름.txt">같은 출처 · download 있음</a></p>
<p><a id="cross" href="http://127.0.0.1:18714/html13b-16-file.txt?k=cross" download="저장한-이름.txt">다른 출처 · download 있음</a></p>
<p><a id="plain" href="/html13b-16-file.txt?k=plain">같은 출처 · download 없음</a></p>
<p><a id="js" href="javascript:document.title='javascript: 가 돌았다'">javascript: URL</a></p>
</body>
</html>
```

- 같은 출처 `download` 의 결과와 저장된 파일 이름은?
- 다른 출처 `download` 의 결과는? 서버 B 는 요청을 받는가?
- `javascript:` 링크를 누르면 `document.title`·`location.href`·서버 요청은?

### 6. `_blank` 가 `noopener` 를 요구했고 지금은 기본인 이유 (왜)

- `window.opener` 가 있으면 새 창이 원래 창에 무엇을 할 수 있나?
- 명세의 「요소의 noopener 구하기」 알고리즘에서 `_blank` 는 어느 줄인가?
- 기본이 바뀐 뒤 `rel="opener"` 는 왜 필요해졌나?

### 7. `nofollow` 는 제 몇의 상태인가 (경계)

- 브라우저 쪽 결과(0 / 3 · `supports` 거짓)는 「잴 것이 없다」인가 「재 봤더니 같았다」인가? 근거 둘을 대라.
- 「검색 엔진이 따라가지 않는다」는 어느 상태인가?
- 이 문서가 그 둘을 섞으면 무엇이 틀리게 되는가?

### 8. `noreferrer` 대 `referrerpolicy="no-referrer"` (경계)

- `_blank` 에서 둘은 몇 칸 갈리는가? 이름 target 에서는?
- 명세가 `noreferrer` 에 대해 적은 「함의」는?
- 서버 로그가 `document.referrer` 보다 강한 근거인 이유는?

### 9. 링크와 버튼이 갈리는 기준 (경계)

- `href` 없는 `<a>` 는 무엇을 잃는가(창 ② · 창 ⑦)?
- `href="#"`·`href="javascript:…"` 로 버튼을 흉내 내면 무엇이 남고 무엇이 틀리는가?
- 네이티브 차이의 정본은 어느 주제인가?

### 10. 명세·구현·관찰 가르기 (경계)

- 교차 출처 `download` 를 **이동으로** 처리한 것은 명세인가 구현인가? 명세는 무엇이라 적는가?
- 다른 출처로 `Referer` 가 출처만 간 것은 어느 층의 무엇 때문인가?
- 「`_blank` 기본 `noopener`」를 **다른 엔진에서도 그렇다**고 적을 수 있는가?

### 11. 정본 경계 긋기 (연결)

- **HTTP 헤더·요청 모델**의 연혁은 어디인가? 거기에 `Referer` 절이 있는가?
- **`#fragment` 가 무엇을 찾나**의 정본은?
- **`rel` 토큰 전체 지도**는?
- **`window.opener` 를 스크립트로 다루는 표면**은 어느 갈래이고, 지금 주제가 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
