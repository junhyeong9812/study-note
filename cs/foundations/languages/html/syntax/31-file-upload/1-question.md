# html/syntax/31 — 파일 업로드: `accept`/`multiple`/`capture` 와 `enctype=multipart/form-data` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **서버가 받은 부분**이다 — 칸마다 「**부분이 몇 개 · `filename` 은 무엇 · 부분 `Content-Type` 은 무엇 · 내용이 갔나 이름만 갔나**」로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 올린 파일 셋 — `p1.png`(1×1 PNG · 67 바이트) · `t1.txt`(글자 `abc` + 줄바꿈 · 4 바이트) · `t2.png`(글자 `xyz` + 줄바꿈 · 4 바이트). 넣는 길 셋 — `files`(CDP `DOM.setFileInputFiles`) · `drop`(CDP 끌어다 놓기) · `chooser`(진짜 마우스로 칸을 눌러 뜬 고르기 창에 넣기).
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [21번 주제](../21-form-submission-model/1-question.md) · [24번 주제](../24-input-types-choice-special/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `accept` 셋 · 파일 셋 · 넣는 길 셋 (예측)

```html
<!-- html29b-31-accept.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 accept 와 넣는 길</title>
<script src="html29b-rec.js"></script>
<style>input[type=file] { display: block; width: 300px; height: 40px; margin: 6px; }</style>
</head>
<body>
<form id="폼" action="/r" method="post" enctype="multipart/form-data">
  <input type="file" id="a1" name="a1" accept="image/png">
  <input type="file" id="a2" name="a2" accept=".png">
  <input type="file" id="a3" name="a3" accept="image/*">
  <button id="보냄">보냄</button>
</form>
<script>
addEventListener("change", e => 적기("change(" + e.target.id + " · isTrusted=" + e.isTrusted + ")"), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 칸들 = ["a1", "a2", "a3"];
const 파일 = ["p1.png", "t1.txt", "t2.png"];
const 길 = ["files", "drop", "chooser"];
const 넣은뒤 = "['a1','a2','a3'].map(id => { const e = document.getElementById(id); return id + ':files=' + e.files.length + ',valid=' + e.validity.valid; }).join(' ')";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [];
for (const g of 길) for (const f of 파일) {
  const 단계 = 칸들.map(id => [g, "#" + id, [f]]);
  단계.push(["js", "(() => { 적기('넣은 뒤 ' + " + 넣은뒤 + "); return 1; })()"]);
  단계.push(["click", "#보냄"]);
  window.__시도.push({ 이름: g + " · " + f, 단계 });
}
window.__종합 = 결과 => {
  const O = [(칸("길 · 파일", 22) + 칸들.map(id => 칸(id + " " + document.getElementById(id).accept, 24)).join("")).trimEnd()];
  let 거부 = 0, 전체 = 0;
  for (const r of 결과) {
    const 서버 = r.서버.join("\n");
    let 행 = 칸(r.이름, 22);
    for (const id of 칸들) {
      const m = 서버.match(new RegExp(id + "=「[^」]*」 \\(filename=「([^」]*)」"));
      const 받음 = m && m[1] !== "";
      전체++; 거부 += !받음;
      행 += 칸(받음 ? "받음 " + m[1] : "— (빈 부분)", 24);
    }
    O.push(행.trimEnd());
  }
  const 무효 = 결과.map(r => (r.기록.find(x => x.startsWith("넣은 뒤")) || "").split(" ").filter(x => x.includes("valid=false")).length).reduce((a, b) => a + b, 0);
  const 변경 = 결과.map(r => r.기록.filter(x => x.startsWith("change(")).length).reduce((a, b) => a + b, 0);
  O.push("넣은 뒤 validity.valid 가 false 인 칸 = " + 무효 + " / " + 전체 + " · change 이벤트 = " + 변경 + "번 (isTrusted=true " + 결과.map(r => r.기록.filter(x => x.includes("isTrusted=true")).length).reduce((a, b) => a + b, 0) + "번)");
  O.push("거부된 칸 = " + 거부 + " / " + 전체 + "  (「받음 이름」= 서버가 받은 부분의 filename · 「— (빈 부분)」= 이름 빈 부분)");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 27 칸 각각에서 서버가 받은 부분의 `filename` 은? 「거부된 칸 N / 27」의 N 은?
- 넣은 뒤 `validity.valid` 가 `false` 인 칸은 몇 개인가? `change` 이벤트의 `isTrusted` 는?
- `t2.png` 의 부분 `Content-Type` 은?

### 2. 파일 칸이 있는 폼 × `enctype` 셋 (예측)

```html
<!-- html29b-31-enctype.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 enctype 과 파일</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r" method="post">
  <input name="t" value="가"><input type="file" id="갑파일" name="f"><button id="갑보냄">보냄</button>
</form>
<form id="을" action="/r" method="post" enctype="multipart/form-data">
  <input name="t" value="가"><input type="file" id="을파일" name="f"><button id="을보냄">보냄</button>
</form>
<form id="병" action="/r" method="post" enctype="text/plain">
  <input name="t" value="가"><input type="file" id="병파일" name="f"><button id="병보냄">보냄</button>
</form>
<script>
window.__시도 = [
  { 이름: "갑 · enctype 없음", 단계: [["files", "#갑파일", ["p1.png"]], ["click", "#갑보냄"]] },
  { 이름: "을 · multipart/form-data", 단계: [["files", "#을파일", ["p1.png"]], ["click", "#을보냄"]] },
  { 이름: "병 · text/plain", 단계: [["files", "#병파일", ["p1.png"]], ["click", "#병보냄"]] },
];
</script>
</body>
</html>
```

- 세 폼 각각에서 서버의 `Content-Type` 과 본문(또는 부분), `f` 의 값은?

### 3. `multiple` · 파일 둘 · `capture` 다섯 시도 (예측)

```html
<!-- html29b-31-multiple.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 multiple 과 capture</title>
<script src="html29b-rec.js"></script>
<style>input[type=file] { display: block; width: 300px; height: 40px; margin: 6px; }</style>
</head>
<body>
<form id="폼" action="/r" method="post" enctype="multipart/form-data">
  <input type="file" id="m1" name="m1" multiple>
  <input type="file" id="m2" name="m2">
  <input type="file" id="m3" name="m3" capture="user" accept="image/*">
  <input type="file" id="m4" name="m4" capture="zzz">
  <button id="보냄">보냄</button>
</form>
<script>
const 적어 = 식 => ["js", "(() => { 적기(" + 식 + "); return 1; })()"];
const 개수 = "['m1','m2','m3','m4'].map(id => id + '=' + document.getElementById(id).files.length).join(' ')";
window.__시도 = [
  { 이름: "chooser 로 m1 에 둘 · m2 에 하나", 단계: [["chooser", "#m1", ["p1.png", "t1.txt"]], ["chooser", "#m2", ["t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "setFileInputFiles 로 m2(multiple 없음)에 둘", 단계: [["files", "#m2", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "drop 으로 m2(multiple 없음)에 둘", 단계: [["drop", "#m2", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "drop 으로 m1(multiple)에 둘", 단계: [["drop", "#m1", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "capture 칸 m3·m4 를 chooser 로", 단계: [["chooser", "#m3", ["p1.png"]], ["chooser", "#m4", ["t1.txt"]],
    적어("'capture in HTMLInputElement.prototype=' + ('capture' in HTMLInputElement.prototype) + ' · capture IDL m3=' + String(document.getElementById('m3').capture) + ' m4=' + String(document.getElementById('m4').capture) + ' · getAttribute m3=' + document.getElementById('m3').getAttribute('capture') + ' · files.length ' + " + 개수), ["click", "#보냄"]] },
];
</script>
</body>
</html>
```

- 시도마다 고르기 창의 `mode` · `files.length` · 서버가 받은 부분 수와 `filename` 은?
- `'capture' in HTMLInputElement.prototype` 과 `m3.capture` 는?

### 4. `accept` 가 보장이 아닌 이유 (왜)

- 명세가 `accept` 에 대해 UA 에게 요구하는 문장의 세기(must / should)는? File Upload 상태에 `accept` 로 된 제약(깃발)이 있나?

### 5. urlencoded 에 파일 이름만 가는 이유 (왜)

- 명세의 어느 변환 단계가 `File` 을 글자로 바꾸나? 그 단계를 거치는 인코딩 둘은?

### 6. 부분의 `Content-Type` 은 어디서 오나 (경계)

- 글자 파일의 이름을 `.png` 로 두면 서버는 무엇을 받나? 서버가 형식을 가르려면 무엇을 봐야 하나?

### 7. `multiple` 없는 칸에 파일 둘 (경계)

- 스크립트 길과 끌어다 놓기가 각각 무엇을 했나? 둘 다 지킨 명세 문장은?

### 8. `capture` — 무시인가 못 잰 것인가 (경계)

- 이 판이 `capture` 에 대해 잰 것과 못 잰 것은? WHATWG HTML 에서 `capture` 를 찾으면?

### 9. 이 판이 못 본 한 가지 (경계)

- 「실제 운영체제 고르기 창은 `accept` 로 거른다 / 안 거른다」 중 이 판이 말할 수 있는 것은? 왜?

### 10. 명세·구현·관찰 가르기 (연결)

- 「끌어다 놓기가 둘을 통째로 거절」·「고른 파일이 없으면 `application/octet-stream`」·「부분 형식이 확장자에서」·「거부 0 / 27」은 각각 어느 층인가?

### 11. 정본 경계 긋기 (연결)

- `enctype` 여섯 칸 · 빈 파일 칸 · `FormData` 에 `File` 을 넣을 때의 `filename` · 받은 `File` 미리보기의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
