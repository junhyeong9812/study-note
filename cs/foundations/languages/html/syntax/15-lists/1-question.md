# html/syntax/15 — 목록: `ul`/`ol`(`start`·`reversed`·`value`)/`dl` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 물음은 하나다 — **「번호는 어디에 있나」.** 답할 때마다 **어느 창에서 읽었나**를 같이 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. WebKit 은 **미실행**이다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 열두 목록의 번호를 접근성 트리로 읽으면 (예측)

```html
<!-- html13b-15-num.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>15 번호는 어디 있나</title>
</head>
<body>
<ol id="base"><li>가</li><li>나</li><li>다</li></ol>
<ol id="s5" start="5"><li>가</li><li>나</li><li>다</li></ol>
<ol id="s0" start="0"><li>가</li><li>나</li><li>다</li></ol>
<ol id="sneg" start="-2"><li>가</li><li>나</li><li>다</li></ol>
<ol id="rev" reversed><li>가</li><li>나</li><li>다</li></ol>
<ol id="rev10" reversed start="10"><li>가</li><li>나</li><li>다</li></ol>
<ol id="val"><li>가</li><li value="7">나</li><li>다</li></ol>
<ol id="revval" reversed><li>가</li><li value="7">나</li><li>다</li></ol>
<ol id="a" type="a"><li>가</li><li>나</li><li>다</li></ol>
<ol id="I" type="I" start="4"><li>가</li><li>나</li><li>다</li></ol>
<ol id="bad" start="삼"><li>가</li><li>나</li><li>다</li></ol>
<ul id="ul"><li>가</li><li>나</li><li>다</li></ul>
<script>
const 목록 = ["base", "s5", "s0", "sneg", "rev", "rev10", "val", "revval", "a", "I", "bad", "ul"];
window.__대상 = [];
for (const id of 목록) for (let i = 1; i <= 3; i++)
  window.__대상.push([id + "/" + i, "#" + id + " > li:nth-child(" + i + ")"]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("목록".padEnd(12) + "속성".padEnd(22) + "ol.start  li.value 셋   ::marker content  접근성 트리의 표지          innerText");
  for (const id of 목록) {
    const L = document.getElementById(id);
    const 속성 = [...L.attributes].filter(a => a.name !== "id").map(a => a.name + (a.value ? "=" + a.value : "")).join(" ") || "—";
    const 값 = [...L.children].map(li => li.value).join(",");
    const 마커 = getComputedStyle(L.children[0], "::marker").content;
    const 이름 = [1, 2, 3].map(i => __AX[id + "/" + i].표지.join("")).map(J).join(" ");
    O.push(id.padEnd(10) + 속성.padEnd(22) + String(L.start ?? "—").padEnd(10) + 값.padEnd(12)
      + 마커.padEnd(17) + 이름.padEnd(26) + J(L.innerText));
  }
  O.push("");
  O.push("DOM 이 번호를 아나 — li.value 가 표지의 번호와 같은 칸을 센다(숫자 표지인 ol 만)");
  let 같음 = 0, 전체 = 0;
  const 같은칸 = [];
  for (const id of 목록) {
    const L = document.getElementById(id);
    if (L.nodeName !== "OL") continue;
    [...L.children].forEach((li, i) => {
      const n = parseInt(__AX[id + "/" + (i + 1)].표지.join(""), 10);
      if (Number.isNaN(n)) return;
      전체++;
      if (li.value === n) { 같음++; 같은칸.push(id + "/" + (i + 1) + " (" + n + ")"); }
    });
  }
  O.push("  같은 칸 = " + 같은칸.join(" · "));
  O.push("같은 칸 = " + 같음 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- `s0`·`sneg`·`rev`·`rev10` 의 세 표지를 적어라.
- `val`(둘째에 `value="7"`)과 `revval`(거꾸로 + 둘째에 `value="7"`)의 셋째 표지는?
- `bad`(`start="삼"`)의 표지는?
- `I`(`type="I" start="4"`)의 첫 표지는?

### 2. 같은 목록을 DOM 과 글자로 읽으면 (예측)

- 1번 소스 그대로다. `rev` 의 `ol.start` 는?
- `base` 의 세 `li.value` 는?
- `::marker` 의 계산값 `content` 는? `innerText` 에 번호가 들어가는가?
- 마지막 줄 「**같은 칸 = N / 27**」 의 N 은? 그 칸들은 왜 같은가?

### 3. `ul` 에 `li` 가 아닌 것을 넣고 `dl` 을 여러 꼴로 쓰면 (예측)

```html
<!-- html13b-15-tree.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>15 목록의 트리</title>
</head>
<body>
<ul id="섞임"><div>li 가 아닌 div</div>그냥 글자<li>진짜 li</li><p>p 도 넣었다</p></ul>
<ul id="없앰" style="list-style: none"><li>표지를 지운 목록</li><li>둘째</li></ul>
<li id="홀로">목록 밖의 li</li>
<dl id="묶음">
  <div><dt>사과</dt><dd>빨갛다</dd></div>
  <div><dt>포도</dt><dt>머루</dt><dd>보랏빛이다</dd><dd>송이로 달린다</dd></div>
</dl>
<dl id="생략"><dt>생략한 dt<dd>생략한 dd<dt>다음 dt<dd>다음 dd</dl>
<dl id="거꾸로"><dd>dt 없이 dd 먼저</dd><dt>뒤늦은 dt</dt></dl>
</body>
</html>
```

- `--dump-dom` 에서 `#섞임` 의 `<div>`·글자·`<p>` 는 어디로 가는가?
- `#생략` 의 `dt`/`dd` 는 어떻게 되는가?
- `#거꾸로`(dd 가 먼저)는 파서가 고치는가?

### 4. 같은 파일을 접근성 트리로 찍으면 (예측)

- 3번 소스 그대로다. `#없앰`(`list-style: none`)은 `list` 역할이 남는가? 무엇이 사라지는가?
- `#묶음` 의 `div` 는 트리에 남는가?
- `dl` 의 역할 이름은 무엇으로 찍히는가? HTML-AAM 과 같은가?
- 목록 밖의 `<li>` 는?

### 5. `reversed` 목록의 `ol.start` 가 1 인 이유 (왜)

- 명세의 **시작 값** 알고리즘은 `reversed` 일 때 무엇을 돌려주는가?
- `start` IDL 에 붙은 명세 표기는 무엇인가?
- 그래서 이 불일치는 버그인가, 설계인가?

### 6. `value` 는 왜 뒤를 끌고 가나 (왜)

- 명세 서수 값 알고리즘에서 `value` 는 **무엇을** 바꾸는가?
- 거꾸로 목록에서 `value="7"` 뒤가 6 인 이유는?
- 명세가 `li.value` IDL 에 대해 따로 적어 둔 문장은?

### 7. `list-style: none` 과 목록 역할 (경계)

- 이 판(Chrome 151)에서 역할이 남았나?
- 「Safari 는 지운다」를 이 문서가 **실측으로** 적을 수 있는가? 그 상태의 이름은?
- 한 엔진에서 본 것을 어떻게 적어야 하는가?

### 8. 세 목록이 주장하는 것 (경계)

- `ul` 과 `ol` 을 가르는 기준은 「점 대 숫자」인가?
- `dl` 은 무엇을 주장하는가? `div` 로 묶은 정보는 보조 기술에 넘어가는가?

### 9. 명세·구현·관찰 가르기 (경계)

- 서수 값 알고리즘은 어느 층인가?
- `DescriptionList`·`ListMarker` 라는 이름은?
- 파서가 `<ul>` 안의 `<div>` 를 안 고친 것은?

### 10. 정본 경계 긋기 (연결)

- **`ul` 이 무엇을 담을 수 있나**의 정본은?
- **`::marker`·`counter()` 로 번호를 만드는 법**의 정본은?
- **`role="list"` 를 손으로 다는 처방의 옳고 그름**은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
