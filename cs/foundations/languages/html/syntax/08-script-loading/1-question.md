# html/syntax/08 — 스크립트 로딩: `defer`/`async`/`type=module`/`nomodule`·배치 위치 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 **「언제 실행되나」와 「그때 트리에 무엇이 있나」를 같이** 답한다.
> ★ **무엇이 명세의 보장이고 무엇이 이 판의 관찰인지** 갈라서 답하라. `async` 의 자리는 보장이 아니다.
> ★ 모든 실험은 **로컬 HTTP 서버** 위에서 돌렸다 — `async` 파일 하나를 **0.5초 늦게** 주어야 순서가 결정적이 된다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->`·`// 파일이름` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [03번 주제](../03-parser-and-error-recovery/1-question.md) · JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 가지 스크립트를 한 문서에 섞으면 (예측)

```html
<!-- html05b-order.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>네 조합을 한 문서에 섞는다</title>
<script src="html05b-log.js"></script>
<script src="html05b-classic.js"></script>
<script defer src="html05b-defer.js"></script>
<script async src="html05b-async-slow.js"></script>
<script type="module" src="html05b-module.mjs"></script>
<script nomodule src="html05b-nomodule.js"></script>
<script>window.__mark("인라인(head)");</script>
</head>
<body>
<div data-mark="1">본문 1</div>
<div data-mark="2">본문 2</div>
<div data-mark="3">본문 3</div>
<script src="html05b-bodyend.js"></script>
<script>
window.__mark("인라인(</body> 앞)");
document.addEventListener("DOMContentLoaded", () => window.__mark("DOMContentLoaded"));
window.addEventListener("load", () => {
  window.__mark("load");
  setTimeout(() => {
    window.__mark("setTimeout 0");
    const q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
</script>
</body>
</html>
```

```javascript
// html05b-log.js
window.__L = [];
window.__mark = function (이름) {
  const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
  window.__L.push(칸(이름, 24)
    + "트리의 data-mark = " + document.querySelectorAll("[data-mark]").length
    + "   readyState = " + document.readyState);
};
```

- 열 줄의 로그가 **어떤 순서**로 찍힐지 예측하라.
- 각 줄의 **트리 `data-mark` 개수**(0 또는 3)를 예측하라.
- 각 줄의 `readyState`(`loading`/`interactive`/`complete`)를 예측하라.
- 로그에 **나타나지 않는** 스크립트가 있는가?

### 2. 늦추지 않은 판을 40번 돌리면 · `async` 둘을 나란히 두면 (예측)

```html
<!-- html05b-order-race.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>async 를 늦추지 않은 판</title>
<script src="html05b-log.js"></script>
<script src="html05b-classic.js"></script>
<script defer src="html05b-defer.js"></script>
<script async src="html05b-async-fast.js"></script>
<script type="module" src="html05b-module.mjs"></script>
<script nomodule src="html05b-nomodule.js"></script>
<script>window.__mark("인라인(head)");</script>
</head>
<body>
<div data-mark="1">본문 1</div>
<div data-mark="2">본문 2</div>
<div data-mark="3">본문 3</div>
<script src="html05b-bodyend.js"></script>
<script>
window.__mark("인라인(</body> 앞)");
document.addEventListener("DOMContentLoaded", () => window.__mark("DOMContentLoaded"));
window.addEventListener("load", () => {
  window.__mark("load");
  setTimeout(() => {
    window.__mark("setTimeout 0");
    const q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
</script>
</body>
</html>
```

```html
<!-- html05b-race.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>async 두 개는 문서 순서를 안 본다</title>
<script src="html05b-log.js"></script>
<script async src="html05b-async-slow.js"></script>
<script async src="html05b-async-fast.js"></script>
</head>
<body>
<div data-mark="1">본문</div>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

- 40판의 순서를 `sort -u` 로 모으면 **몇 가지**가 나오겠는가?
- 갈리는 줄은 **몇 번째 줄**인가?
- 둘째 파일에서 문서에 먼저 적힌 것과 먼저 실행되는 것이 같은가?
- 그 결과를 「보장」으로 적어도 되는가?

### 3. 같은 한 줄을 세 자리에 넣으면 (예측)

```html
<!-- html05b-write.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>document.write 와 defer·async</title>
</head>
<body>
<p id="앞">앞</p>
<script src="html05b-write-plain.js"></script>
<script defer src="html05b-write-defer.js"></script>
<script async src="html05b-write-async.js"></script>
<p id="뒤">뒤</p>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
  const o = [];
  for (const k of ["평범", "defer", "async"]) o.push(칸(k, 8) + " -> " + window.__결과[k]);
  o.push("트리의 <b> 개수 = " + document.querySelectorAll("b").length
         + "   글자 = " + JSON.stringify([...document.querySelectorAll("b")].map(b => b.textContent)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

```javascript
// html05b-write-plain.js
window.__결과 = window.__결과 || {};
try { document.write("<b>평범한 스크립트가 쓴 글</b>"); window.__결과["평범"] = "예외 없이 통과"; }
catch (e) { window.__결과["평범"] = "예외: " + e.name; }
```

```javascript
// html05b-write-defer.js
window.__결과 = window.__결과 || {};
try { document.write("<b>defer 스크립트가 쓴 글</b>"); window.__결과["defer"] = "예외 없이 통과"; }
catch (e) { window.__결과["defer"] = "예외: " + e.name; }
```

```javascript
// html05b-write-async.js
window.__결과 = window.__결과 || {};
try { document.write("<b>async 스크립트가 쓴 글</b>"); window.__결과["async"] = "예외 없이 통과"; }
catch (e) { window.__결과["async"] = "예외: " + e.name; }
```

- 세 줄 중 **예외를 던지는** 것이 있는가?
- 트리에 `<b>` 가 **몇 개** 생기는지 예측하라.
- 두 답이 어긋난다면 그 사실을 무엇이라 부르는가?
- 실제로 일어난 일은 **어디에** 기록되는가?

### 4. 같은 파일을 여러 번 부르면 (예측)

```html
<!-- html05b-once.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>모듈은 한 번만 평가된다</title>
</head>
<body>
<script type="module" src="html05b-once.mjs"></script>
<script type="module" src="html05b-once.mjs"></script>
<script type="module">import "./html05b-once.mjs";</script>
<script src="html05b-once.js"></script>
<script src="html05b-once.js"></script>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

- `.mjs` 의 본문이 **몇 번** 평가되는지 예측하라.
- `.js` 의 본문은 **몇 번** 평가되는가?
- 두 파일의 **네트워크 요청 횟수**는 각각 몇 번이겠는가?
- 「요청 횟수」와 「평가 횟수」가 같은 이야기인가?

### 5. 붙였는데 안 먹는 네 자리 (예측)

```html
<!-- html05b-attr-edge.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>인라인에 붙인 defer·async 와 속성 조합</title>
<script src="html05b-log.js"></script>
<script defer>window.__mark("인라인에 defer");</script>
<script async>window.__mark("인라인에 async");</script>
<script defer async src="html05b-both-slow.js"></script>
<script type="module" async src="html05b-modasync-slow.mjs"></script>
</head>
<body>
<div data-mark="1">본문 1</div>
<div data-mark="2">본문 2</div>
<div data-mark="3">본문 3</div>
<script>
document.addEventListener("DOMContentLoaded", () => window.__mark("DOMContentLoaded"));
window.addEventListener("load", () => {
  window.__mark("load");
  setTimeout(() => {
    const q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
</script>
</body>
</html>
```

- 다섯 줄의 로그 순서를 예측하라.
- 인라인 스크립트의 `defer`·`async` 는 먹는가?
- 뒤의 두 파일은 `DOMContentLoaded` **앞**인가 **뒤**인가? 그 답이 뜻하는 것은?
- 이 문서에서 뒤의 두 파일 이름에 `-slow` 가 붙은 이유는?

### 6. 도구가 어디까지 기다리나 (예측)

```html
<!-- html05b-wait.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>--dump-dom 이 어디까지 기다리나</title>
</head>
<body>
<script>
const 찍다 = t => { const d = document.createElement("div"); d.className = "늦게"; d.textContent = t; document.body.appendChild(d); };
찍다("파싱 중 동기");
window.addEventListener("load", () => {
  찍다("load");
  queueMicrotask(() => 찍다("마이크로태스크"));
  for (const ms of [0, 1, 5, 10, 20, 50, 200]) setTimeout(() => 찍다("setTimeout " + ms), ms);
});
</script>
</body>
</html>
```

- 덤프에 찍히는 줄을 **전부** 예측하라.
- `setTimeout` 일곱 중 몇 개가 찍히는가?
- 경계는 몇 ms 와 몇 ms 사이인가?
- 이 결과가 이 문서 전체에 뜻하는 것은?

### 7. 배치 위치가 바꾸는 것 (왜)

- `<head>` 와 `</body>` 앞의 평범한 스크립트가 **바꾸는 것**은 실행 시점인가 다른 것인가?
- `<head>` 의 스크립트에서 본문 요소를 찾으면 무엇이 오는가?
- 「스크립트를 `</body>` 앞에 두라」는 옛 처방이 피하려던 것은 무엇인가?
- 오늘 그 자리를 무엇이 대신하는가? 무엇이 더 나은가?

### 8. 보장과 관찰을 가르기 (경계)

- 이 주제에서 **명세가 보장하는** 순서를 대라.
- **보장이 없는** 것을 대라. 그것을 이 문서는 어떻게 적었는가?
- 「40판 돌렸더니 두 가지였다」는 무엇의 근거인가?
- 「40판 돌렸더니 한 가지였다」면 무엇이라 적어야 하는가?

### 9. 「실행 안 됨」의 두 가지 (경계)

- 스크립트가 안 돌았을 때 가능한 원인 둘을 대라.
- 그 둘을 실행 로그로 가를 수 있는가?
- 무엇을 보면 갈리는가?
- `nomodule` 은 그중 어느 쪽인가?

### 10. 정본 경계 긋기 (연결)

- `import`/`export`·라이브 바인딩·순환 의존의 정본은 어느 갈래인가?
- 스타일시트가 렌더를 막는 이야기의 정본은 어느 주제인가?
- 파싱 차단이 왜 파서를 멈추게 하는지의 정본은 어느 주제인가?
- 이 주제가 JS 갈래와 겹치면서도 독립인 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
