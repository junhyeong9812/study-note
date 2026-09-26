# html/syntax/33 — `output`·`progress`·`meter`: 계산 결과 / 진행 / 범위 안의 측정값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **역할 격자**다 — 요소마다 「**접근성 트리의 역할 · 라이브 속성 · 서버에 실리나 · 라벨이 붙나**」로 답하라. `meter` 는 「**값 막대가 어느 구역으로 그려지나**」로.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 1·2번 페이지가 읽는 「명세 열」 파일(`html33b-33-spec.js`·`html33b-33-meter-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [25번 주제](../25-label-association/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 폼 · 요소 다섯 · 여덟 열 (예측)

```html
<!-- html33b-33-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 세 요소</title>
<script src="html33b-rec.js"></script>
<script src="html33b-33-spec.js"></script>
</head>
<body>
<form id="f" action="/r" method="post">
  <label for="i">입력</label> <input id="i" name="i" value="1">
  <label for="o">결과</label> <output id="o" name="o" for="i">3</output>
  <label for="p1">진행</label> <progress id="p1" name="p1" value="30" max="100">30%</progress>
  <label for="p2">대기</label> <progress id="p2" name="p2" max="100"></progress>
  <label for="m1">측정</label> <meter id="m1" name="m1" value="0.6" low="0.3" high="0.7" optimum="0.9">60%</meter>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 줄 = [["i", "input"], ["o", "output"], ["p1", "progress · value 있음"], ["p2", "progress · value 없음"], ["m1", "meter · low/high/optimum"]];
window.__대상 = 줄.map(([k]) => [k, "#" + k]);
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [{ 이름: "requestSubmit()", 단계: [["js", "document.getElementById('f').requestSubmit(); 1"]] }];
window.__종합 = 결과 => {
  const 필드 = 결과[0].필드 || [];
  const f = document.getElementById("f");
  const 값 = k => {
    const a = __AX[k], e = document.getElementById(k);
    return {
      역할: a.역할,
      이름: JSON.stringify(a.이름),
      라이브: a.속성.live ? a.속성.live + " · atomic=" + a.속성.atomic : "—",
      제출: 필드.includes(e.getAttribute("name")) ? "실림" : "—",
      labels: String(e.labels.length),
      elements: [...f.elements].includes(e) ? "있음" : "—",
      AX값: a.값 === undefined || a.값 === null ? "—" : String(a.값),
      범위: a.속성.valuemin === undefined ? "—" : a.속성.valuemin + ".." + a.속성.valuemax,
    };
  };
  const 열 = ["역할", "라이브", "제출", "labels", "elements", "AX값"];
  const O = [칸("요소", 28) + 칸("역할", 13) + 칸("이름", 8) + 칸("라이브", 22) + 칸("제출", 6) + 칸("labels", 8) + 칸("elements", 10) + 칸("AX 값", 20) + "AX 범위"];
  let 갈림 = 0, 전체 = 0;
  for (const [k, 이름] of 줄) {
    const v = 값(k);
    O.push(칸(k + " " + 이름, 28) + 칸(v.역할, 13) + 칸(v.이름, 8) + 칸(v.라이브, 22) + 칸(v.제출, 6) + 칸(v.labels, 8) + 칸(v.elements, 10) + 칸(v.AX값, 20) + v.범위);
    for (const c of 열) if (명세[k][c] !== null) { 전체++; if (명세[k][c] !== v[c]) { 갈림++; O.push("  ↳ 명세 열과 갈림 — " + c + " : 명세 " + JSON.stringify(명세[k][c]) + " · 이 판 " + JSON.stringify(v[c])); } }
  }
  O.push("(라이브 = 접근성 노드의 live · atomic 속성 · 제출 = 서버가 받은 필드에 그 name 이 있나 · elements = form.elements 에 있나 · AX 범위 = valuemin..valuemax)");
  O.push("서버가 받은 필드 = " + (필드.join(",") || "(없음)"));
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 다섯 요소 각각의 역할 · 이름 · 라이브 속성 · 제출 · `labels.length` · `form.elements` · 접근성 값 · 범위는?
- 서버가 받은 필드는 무엇인가? 「명세 열과 갈린 칸 N / 22」의 N 은?

### 2. `meter` 열 개 (예측)

```html
<!-- html33b-33-meter.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 meter 의 구역</title>
<script src="html33b-33-meter-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [id, value, optimum] — 전부 min=0 max=1 low=0.3 high=0.7 · 마지막 줄만 low/high/optimum 없음
const 줄 = [
  ["g1", 0.2, 0.5], ["g2", 0.5, 0.5], ["g3", 0.8, 0.5],
  ["h1", 0.2, 0.9], ["h2", 0.5, 0.9], ["h3", 0.8, 0.9],
  ["l1", 0.2, 0.1], ["l2", 0.5, 0.1], ["l3", 0.8, 0.1],
  ["n1", 0.5, null],
];
const 자리 = document.getElementById("자리");
for (const [k, v, o] of 줄) {
  const m = document.createElement("meter");
  m.id = k; m.setAttribute("value", v);
  if (o !== null) { m.setAttribute("low", "0.3"); m.setAttribute("high", "0.7"); m.setAttribute("optimum", o); }
  자리.append(m);
}
window.__속대상 = 줄.map(([k]) => k);
window.__끝 = () => {
  const O = [칸("meter", 30) + 칸("값 막대의 pseudo", 36) + 칸("background-color", 22) + "명세 열(구역)"];
  let 갈림 = 0;
  const 이름 = { "-webkit-meter-optimum-value": "최적", "-webkit-meter-suboptimum-value": "차선", "-webkit-meter-even-less-good-value": "더 나쁨" };
  const 색 = new Set();
  for (const [k, v, o] of 줄) {
    const 값막대 = __속[k].find(([p]) => p.endsWith("-value"));
    const 구역 = 이름[값막대[0]] || "(모름)";
    const 기대 = 명세구역(v, o);
    갈림 += 구역 !== 기대;
    색.add(값막대[1]);
    O.push(칸(k + " value=" + v + " · optimum=" + (o === null ? "(없음)" : o), 30) + 칸(값막대[0], 36) + 칸(값막대[1], 22) + 기대);
  }
  O.push("그림자 트리의 pseudo 전부(g1) = " + __속.g1.map(([p]) => p).join(" · "));
  O.push("값 막대 색의 가짓수 = " + 색.size);
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 줄.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 열 개의 값 막대가 받는 `pseudo` 이름은 각각 무엇인가? 계산된 색은 몇 가지인가?
- 명세의 구역 규칙(최적 · 차선 · 더 나쁨)과 갈리는 칸이 있나?

### 3. `output` 의 값을 바꾸고 되돌리기 (예측)

```html
<!-- html33b-33-live.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 output 의 값 바꾸기</title>
</head>
<body>
<form id="f">
  <input id="a" type="number" value="2"> + <input id="b" type="number" value="1"> =
  <output id="o" for="a b">3</output>
</form>
<p id="보통">3</p>
<script>
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const o = document.getElementById("o"), f = document.getElementById("f");
const 줄 = [];
const 찍기 = 때 => 줄.push(때 + " — value=" + JSON.stringify(o.value) + " · defaultValue=" + JSON.stringify(o.defaultValue) + " · textContent=" + JSON.stringify(o.textContent));
window.__대상 = [["o", "#o"], ["보통", "#보통"]];
window.__바꾸기 = async () => {
  찍기("처음");
  o.value = "4";
  document.getElementById("보통").textContent = "4";
  await 두틀();
  찍기("o.value = '4' 뒤");
  return 1;
};
window.__끝 = () => {
  const 글자 = x => x.역할 + " · 글자=" + JSON.stringify(x.글자) + " · live=" + (x.속성.live || "—");
  const O = ["[창 ②]", ...줄.map(s => "  " + s)];
  f.reset();
  찍기("form.reset() 뒤");
  O.push("  " + 줄[줄.length - 1]);
  O.push("  htmlFor = " + Object.prototype.toString.call(o.htmlFor) + " · " + JSON.stringify([...o.htmlFor]) + " · 길이 " + o.htmlFor.length);
  O.push("[창 ⑦ 전] output = " + 글자(__AX전.o) + "  |  p = " + 글자(__AX전.보통));
  O.push("[창 ⑦ 뒤] output = " + 글자(__AX뒤.o) + "  |  p = " + 글자(__AX뒤.보통));
  const 이름 = Object.keys(__이벤트);
  O.push("바꾼 뒤 받은 Accessibility.* 이벤트 = " + (이름.length ? 이름.map(k => k + " " + __이벤트[k]).join(" · ") : "0 건"));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 세 시점(처음 · `value='4'` 뒤 · `reset()` 뒤)의 `value` · `defaultValue` · `textContent` 는?
- `htmlFor` 는 무슨 타입이고 무엇이 들어 있나?
- 바꾸기 전·뒤 트리의 두 노드(`output` · `p`)는 무엇이 같고 무엇이 다른가? 바꾼 뒤 받은 CDP `Accessibility.*` 이벤트는 몇 건인가?

### 4. `output` 이 폼에 연결되는 이유 (왜)

- 명세가 `output` 을 폼과 연결하는 이유로 드는 문장은? 그 문장 바로 뒤에 무엇이 적혀 있나?

### 5. 「디스크 사용량」 막대 (경계)

- `progress` 와 `meter` 중 무엇을 써야 하나? 명세가 두 요소에 각각 붙인 「이렇게 쓰지 마라」 문장은?

### 6. `value` 없는 `progress` (경계)

- 명세는 이것을 무엇이라 부르나? `value="0"` 과는 무엇이 다른가? 이 판의 트리에서 그 차이는 어느 칸에 보였나?

### 7. `low`·`high`·`optimum` 이 화면에 하는 일 (경계)

- 명세가 정하는 것과 정하지 않는 것은 각각 무엇인가? 이 판은 Chrome 이 구역을 어떻게 그리는지를 무엇으로 물었고, 그 창이 못 보는 것은?

### 8. `label` 의 `for` 와 `output` 의 `for` (연결)

- 둘은 가리키는 대상 · IDL 타입 · 하는 일에서 어떻게 다른가? `output` 에 이름을 주는 것은 어느 쪽인가?

### 9. 라이브 영역을 「확인했다」는 말 (경계)

- 이 판이 `output` 의 라이브 성질에 대해 **본 것**과 **못 본 것**을 갈라 대면? CDP 의 `Accessibility.*` 이벤트 수로 「알림이 났나」를 판정할 수 있나?

### 10. 명세·구현·관찰 가르기 (연결)

- 「`output` 의 값이 제출되나」·「`meter` 구역의 색」·「`output` 노드의 `live` 속성」·「불확정 `progress` 의 범위」는 각각 명세·구현·관찰 중 어느 층이 정하나?

### 11. 정본 경계 긋기 (연결)

- 라벨이 이름을 주는 규칙 · 제약 검증 API · 암묵 역할 일반 · `output` 이 서버에 안 가는 것의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
