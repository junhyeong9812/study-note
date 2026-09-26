# html/syntax/19 — `figure`/`figcaption`·`address`·`hr`·`details` 밖의 잡다한 구조 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 본체는 **창 ⑦** 이다. 답할 때마다 「**이름**」·「**설명**」·「**역할**」 중 **어느 칸**의 이야기인지 적어라.
> ★ **명세·구현·관찰을 갈라라** — 뜻은 WHATWG HTML 이, 역할과 이름 계산은 HTML-AAM 이, 트리는 Chrome 이 만든다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [11번 주제](../11-sectioning-and-landmarks/1-question.md)(구획 요소 · 창 ⑦).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `figure` 열 개의 이름 (예측)

```html
<!-- html17b-19-figure.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>19 그림과 캡션</title>
</head>
<body>
<figure id="f1"><img id="i1" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>그림 1. 월별 방문자</figcaption></figure>
<figure id="f2"><figcaption>그림 2. 월별 방문자</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f3"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="앞 그림"><figcaption>그림 3. 가운데 캡션</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="뒤 그림"></figure>
<figure id="f4"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f5" aria-label="에어리아 이름"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>그림 5. 캡션</figcaption></figure>
<figure id="f6"><figcaption>첫 캡션</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>둘째 캡션</figcaption></figure>
<figure id="f7" title="제목 속성"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f8"><pre>코드 조각</pre><figcaption>예 8. 코드</figcaption></figure>
<figure id="f10" aria-labelledby="캡10"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption id="캡10">그림 10. 이어 붙인 캡션</figcaption></figure>
<div id="f9"><figcaption id="밖캡션">figure 밖의 figcaption</figcaption></div>
<script>
const 설명 = { f1: "img + 끝 figcaption", f2: "첫 figcaption + img", f3: "가운데 figcaption", f4: "img alt 만",
  f5: "aria-label + figcaption", f6: "figcaption 둘", f7: "title + img", f8: "pre + figcaption", f10: "aria-labelledby=캡션 id", f9: "figure 밖 figcaption" };
const 키 = Object.keys(설명);
window.__대상 = [...키.map(k => [k, "#" + k]), ["i1", "#i1"], ["밖캡션", "#밖캡션"]];
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["figure 마다 — CDP 역할·이름·설명 · 이름의 출처(내부 덤프 nameFrom) · 자식 순서(DOM)"];
  for (const k of 키) {
    const a = __AX[k], n = __INT[k];
    const 자식 = [...document.getElementById(k).children].map(e => e.localName).join(" ");
    O.push("  " + 설명[k].padEnd(24) + "역할 = " + a.역할.padEnd(8) + "이름 = " + J(a.이름).padEnd(20) + "설명 = " + J(a.설명).padEnd(14)
      + "nameFrom = " + ((n && n.속성.nameFrom) || "—").padEnd(15) + "자식 = " + 자식);
  }
  O.push("");
  O.push("  f1 안의 img  역할 = " + __AX.i1.역할 + " · 이름 = " + J(__AX.i1.이름));
  O.push("  figure 밖 figcaption  역할 = " + __AX["밖캡션"].역할 + " · 이름 = " + J(__AX["밖캡션"].이름));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `figure` 열 개(와 `figure` 밖의 `div`) 각각의 **역할·이름·설명·`nameFrom`** 은?
- `#f1` 안의 `img` 의 역할과 이름은?
- `figure` 밖의 `figcaption` 의 역할은 무엇으로 찍히는가?

### 2. 자리를 어긴 `figcaption` (예측)

- 1번 소스의 `#f3`(두 `img` 사이의 `figcaption`)을 `--dump-dom` 으로 찍으면 자식 순서는?
- 같은 `#f3` 를 트리로 찍으면 노드 순서는?
- `#f6`(`figcaption` 둘)과 `#f9`(`figure` 밖)는 파서가 고치는가?

### 3. `address` 셋과 `hr` 셋 (예측)

```html
<!-- html17b-19-misc.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>19 address 와 hr</title>
</head>
<body>
<address id="a1">홍길동 · <a href="mailto:hong@example.com">hong@example.com</a></address>
<article id="글"><h2>기사</h2><p>본문</p><address id="a2">글쓴이 연락처 · <a href="tel:+82-2-000-0000">02-000-0000</a></address></article>
<address id="a3" aria-label="연락처">서울시 어딘가 1</address>
<p id="p1">앞</p>
<hr id="h1">
<p>뒤</p>
<select id="고르기"><option>가</option><hr id="h2"><option>나</option></select>
<div id="d1" role="separator"></div>
<script>
window.__대상 = [["a1", "#a1"], ["a2", "#a2"], ["a3", "#a3"], ["h1", "#h1"], ["h2", "#h2"], ["d1", "#d1"], ["글", "#글"]];
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["요소마다 — CDP 역할·이름 · 무시 여부 · 내부 덤프 역할 · 부모(DOM)"];
  for (const [k] of window.__대상) {
    const a = __AX[k], n = __INT[k], e = document.getElementById(k);
    O.push("  #" + k.padEnd(4) + ("<" + e.localName + (e.getAttribute("role") ? " role=" + e.getAttribute("role") : "") + ">").padEnd(22)
      + "CDP 역할 = " + (a.무시 ? "(무시)" : a.역할).padEnd(11) + "이름 = " + J(a.이름).padEnd(8)
      + "내부 = " + (n ? (n.속성.ignored ? "(무시)" : n.역할) : "(덤프에 없음)").padEnd(18) + "부모 = <" + e.parentElement.localName + ">");
  }
  O.push("");
  O.push("  address 셋의 계산 font-style = " + ["a1", "a2", "a3"].map(k => getComputedStyle(document.getElementById(k)).fontStyle).join(" · "));
  O.push("  select.options.length = " + document.getElementById("고르기").options.length
    + " · select 의 자식 = " + [...document.getElementById("고르기").children].map(e => e.localName).join(" "));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `#a1`·`#a2`·`#a3` 의 CDP 역할과 이름은? `body` 안과 `article` 안이 다른가?
- `#h1`·`#h2`·`#d1` 의 CDP 역할과 내부 덤프 역할은?
- `select` 의 자식 순서와 `select.options.length` 는?
- `address` 셋의 계산 `font-style` 은?

### 4. `figure` 의 이름 계산 규칙 (왜)

- HTML-AAM 편집본의 「figure 요소의 이름 계산」은 이름 출처로 무엇을 드는가? `figcaption` 에 대해 무엇이라 적는가?
- 1번에서 `#f10` 이 이름을 얻은 경로는? 그 `nameFrom` 값은 무엇을 뜻하나?
- `#f4` 의 `img alt` 글자는 트리의 **어느 노드**의 이름 칸에 있나?

### 5. 「연락처」 판단 (경계)

- 다음 넷 중 명세상 `<address>` 가 맞는 것은? ① 이 기사의 기자 이메일 ② 쇼핑몰 주문서의 배송지 ③ 회사 소개 페이지 맨 아래의 대표 전화 ④ 글쓴이의 약력
- 3번의 트리는 그 판단을 도와주는가? 그것은 제 몇의 상태인가?

### 6. 두 캡션의 이름 계산 (연결)

- [17번 주제](../17-table-structure/1-question.md)의 표 `caption` 과 이 주제의 `figcaption` 은 부모의 **이름**에 대해 각각 어떻게 다른가? 근거는 HTML-AAM 의 어느 절인가?
- 두 요소의 **역할**은 HTML-AAM 에서 무엇이고, 이 판의 트리에서는 무엇으로 찍히는가?

### 7. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 **명세 ↔ Chrome 불일치**는 어디인가?
- `select` 안의 `hr` 을 `separator` 로 둔 것은 불일치인가? HTML-AAM 의 문장으로 답하라.
- `select` 안의 `hr` 이 DOM 에 남는 것은 명세의 어느 절이 정하나?

### 8. 이 판이 못 보는 것 (경계)

- 「스크린리더가 `figure` 에 들어가며 캡션을 읽는다」를 이 문서가 쓸 수 있는가?
- `select` 안 `hr` 의 **다른 엔진** 파싱은?

### 9. 정본 경계 긋기 (연결)

- 「파서가 안 고치는 것」과 `figure` 밖 `figcaption` 의 정본은?
- `details`/`summary` 의 정본은?
- 이미지 `alt` 판단과 이름 계산 전체의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
