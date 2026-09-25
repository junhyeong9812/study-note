# html/syntax/08 — 스크립트 로딩: `defer`/`async`/`type=module`/`nomodule`·배치 위치 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★ **`async` 의 자리는 보장이 아니다.** 이 파일은 그것을 **가짓수**로 적는다(A2).
> ★★★ **관찰 한계** — `--dump-dom` 은 `load` + 마이크로태스크 + `setTimeout(…, 0)` 까지만 기다린다(A6). 이 문서의 모든 출력이 그 안에서 읽은 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 평범 → 인라인 → 본문 끝 → `defer` → 모듈 → `DOMContentLoaded` → `async` → `load`

**출력** (Chrome 151 headless, 로컬 HTTP 서버 위)

```text
===== 소스: html05b-order.html =====
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
===== dom http://127.0.0.1:18705/html05b-order.html | probe =====
평범(head)              트리의 data-mark = 0   readyState = loading
인라인(head)            트리의 data-mark = 0   readyState = loading
평범(</body> 앞)        트리의 data-mark = 3   readyState = loading
인라인(</body> 앞)      트리의 data-mark = 3   readyState = loading
defer                   트리의 data-mark = 3   readyState = interactive
type=module             트리의 data-mark = 3   readyState = interactive
DOMContentLoaded        트리의 data-mark = 3   readyState = interactive
async(늦게 오는 파일)   트리의 data-mark = 3   readyState = interactive
load                    트리의 data-mark = 3   readyState = complete
setTimeout 0            트리의 data-mark = 3   readyState = complete
(exit 0)
```

**왜 그런가**

| 순서 | 무엇 | `data-mark` | `readyState` | 왜 |
|---|---|---|---|---|
| 1 | 평범(head) | **0** | loading | 파싱을 막고 **그 자리에서** 실행 — 본문이 아직 없다 |
| 2 | 인라인(head) | 0 | loading | 〃 |
| 3 | 평범(`</body>` 앞) | **3** | loading | 본문을 다 읽은 뒤라 트리가 다 있다 |
| 4 | 인라인(`</body>` 앞) | 3 | loading | 〃 |
| 5 | `defer` | 3 | **interactive** | 파싱이 끝난 뒤 **문서 순서대로** |
| 6 | `type=module` | 3 | interactive | 모듈은 **암묵 `defer`** |
| 7 | `DOMContentLoaded` | 3 | interactive | `defer`·모듈이 **끝난 뒤** 난다 |
| 8 | `async`(늦게 오는 파일) | 3 | interactive | **받는 대로** — 이 판에서는 0.5초 늦었다 |
| 9 | `load` | 3 | **complete** | 모든 자원이 끝났다 |
| 10 | `setTimeout 0` | 3 | complete | 도구가 여기까지 기다린다(A6) |

- **배치 위치가 바꾸는 것은 「그때 트리에 무엇이 있나」다.** 1·2 는 0 개, 3·4 는 3 개 — **`data-mark` 한 칸이 그 답 전부**다.
- **`defer` 와 모듈이 `DOMContentLoaded` 앞에 있다.** 그래서 둘 다 **DOM 을 다 보고 시작**할 수 있다.
- **`nomodule` 이 로그에 없다.** 모듈을 아는 브라우저는 `nomodule` 붙은 스크립트를 실행하지 않는다. ★ **「받아 놓고 안 돈 것」인지 「안 받아 온 것」인지는 이 창으로 안 갈린다** — A9 가 그것을 가른다.
- ★ **8번 줄의 자리는 보장이 아니다.** 이 판에서 그 파일을 **0.5초 늦게 줬기 때문에** 여기 있다. 그 사실을 안 밝히면 「`async` 는 `DOMContentLoaded` 뒤다」라는 **없는 규칙**을 만들게 된다.

### 2. 가짓수는 2 — 갈리는 것은 `async` 한 줄뿐이다

**출력**

```text
===== for i in $(seq 1 40); do dom http://127.0.0.1:18705/html05b-order-race.html | probe | awk '{printf "%s ", $1}'; echo; done | sort -u | awk '{print "  " $0} END {print "가짓수 = " NR}' =====
  평범(head) 인라인(head) 평범(</body> 인라인(</body> async(빨리 defer type=module DOMContentLoaded load setTimeout 
  평범(head) 인라인(head) 평범(</body> 인라인(</body> defer type=module DOMContentLoaded async(빨리 load setTimeout 
가짓수 = 2
(exit 0)
```

```text
===== 소스: html05b-race.html =====
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
===== dom http://127.0.0.1:18705/html05b-race.html | probe =====
async(빨리 오는 파일)   트리의 data-mark = 1   readyState = interactive
async(늦게 오는 파일)   트리의 data-mark = 1   readyState = interactive
(exit 0)
```

**왜 그런가**

- **40판을 `sort -u` 로 모으니 2가지**였다. 갈리는 것은 **`async(빨리 오는 파일)` 한 줄의 자리**이고, 나머지 아홉 줄은 **40판 전부 같은 자리**였다.
- **두 자리는 `DOMContentLoaded` 앞과 뒤에 걸쳐 있다.** 그러므로 **`async` 스크립트 안에서 「DOM 이 다 있다」를 가정할 수 없다.**
- **둘째 실험** — 문서에는 **늦게 오는 파일이 먼저** 적혀 있는데 **빨리 온 쪽이 먼저** 실행됐다. `async` 가 보는 것은 **도착 시각**뿐이고 문서 순서가 아니다.
- ★★ **「보장」으로 적으면 안 된다.** 이 배치가 쓴 형식이 그 답이다 — **순서를 그대로 싣지 않고 가짓수를 센다.** 가짓수 2 는 **「보장이 없다」의 실증**이고, 가짓수 1 이었다면 「**이 판에서는 안 갈렸다**」까지만 적어야 한다.

### 3. 세 줄 다 예외가 없는데 `<b>` 는 하나뿐이다 — 무음 실패

**출력**

```text
===== 소스: html05b-write.html =====
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
===== dom http://127.0.0.1:18705/html05b-write.html | probe =====
평범     -> 예외 없이 통과
defer    -> 예외 없이 통과
async    -> 예외 없이 통과
트리의 <b> 개수 = 1   글자 = ["평범한 스크립트가 쓴 글"]
(exit 0)
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr --dump-dom http://127.0.0.1:18705/html05b-write.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"Failed to execute 'write' on 'Document': It isn't possible to write into a document from an asynchronously-loaded external script unless it is explicitly opened.", source: http://127.0.0.1:18705/html05b-write-async.js (2)
"Failed to execute 'write' on 'Document': It isn't possible to write into a document from an asynchronously-loaded external script unless it is explicitly opened.", source: http://127.0.0.1:18705/html05b-write-defer.js (2)
(exit 0)
```

**왜 그런가**

- **예외는 세 줄 다 안 난다.** `try`/`catch` 가 전부 「예외 없이 통과」를 찍었다.
- **그런데 트리의 `<b>` 는 1개뿐**이고 글자는 `"평범한 스크립트가 쓴 글"` 하나다. `defer`·`async` 의 `document.write` 는 **아무 일도 안 했다.**
- **이것을 「무음 실패(silent failure)」라 부른다** — 코드도 그대로, 예외도 없음, 결과만 다름.
- **실제로 일어난 일은 콘솔에만 있다.** `--enable-logging=stderr` 를 붙여야 보이고, 문구는 「**비동기로 로드된 외부 스크립트에서는 문서에 write 할 수 없다**」는 뜻이다. ★ **따로 물어야 보이는 출력**이다 — 「경고도 출력이다」의 실물.
- **왜 막나** — `defer`/`async` 는 **파싱이 끝난 뒤**에 도는데 그때 `document.write` 를 허용하면 **이미 만든 문서를 지우고 다시 여는 것**이 된다. 그래서 명세가 **무시**하도록 정했다.

### 4. 모듈은 1번, 평범한 스크립트는 2번 평가된다

**출력**

```text
===== 소스: html05b-once.html =====
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
===== dom http://127.0.0.1:18705/html05b-once.html | probe =====
html05b-once.js 의 본문이 평가됐다
html05b-once.js 의 본문이 평가됐다
html05b-once.mjs 의 본문이 평가됐다
(exit 0)
```

**왜 그런가**

- **`.mjs` 는 `src` 두 번 + `import` 한 번 = 세 번 불렀는데 본문이 1번 평가**됐다. 같은 URL 은 **모듈 맵**에 한 번만 올라간다.
- **`.js` 는 두 번 불러 두 번 평가**됐다.
- **네트워크 요청은 둘 다 1번이다**(A9 의 요청 로그). ★ **그러니 「요청 1번」과 「평가 1번」은 다른 이야기다.** 모듈의 「한 번만」은 **평가** 쪽 보장이고, `.js` 쪽 1번은 **같은 URL 을 다시 받지 않은 것**일 뿐이다.
- ★ **그래서 모듈에서는 「최상위 코드 = 초기화」가 성립한다.** 평범한 스크립트에서는 성립하지 않는다.
- ★ 모듈 안의 `import`·라이브 바인딩·순환 의존은 JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**이 정본이다.

### 5. 인라인의 `defer`·`async` 는 무시되고, 함께 주면 `async` 가 이긴다

**출력**

```text
===== 소스: html05b-attr-edge.html =====
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
===== dom http://127.0.0.1:18705/html05b-attr-edge.html | probe =====
인라인에 defer          트리의 data-mark = 0   readyState = loading
인라인에 async          트리의 data-mark = 0   readyState = loading
DOMContentLoaded        트리의 data-mark = 3   readyState = interactive
defer 와 async 를 함께  트리의 data-mark = 3   readyState = interactive
type=module + async     트리의 data-mark = 3   readyState = interactive
load                    트리의 data-mark = 3   readyState = complete
(exit 0)
```

**왜 그런가**

- **인라인에 붙인 `defer`·`async` 는 무시된다.** 둘 다 **트리 0개 · `loading`** 에서 찍혔다 — 파싱 도중 **그 자리에서** 돈 것이다. 두 속성은 **`src` 가 있는 스크립트 전용**이다.
- **`defer async` 를 함께 주면 `async` 가 이긴다.** 0.5초 늦게 온 파일이 **`DOMContentLoaded` 뒤**에 돌았다 — `defer` 로 동작했다면 **앞**이었을 것이다(`defer` 는 `DOMContentLoaded` 를 기다리게 한다, A1 의 5·7 번 줄).
- **`type="module" async` 도 같다.** 모듈은 기본이 `defer` 처럼인데 `async` 를 붙이자 **경계선 뒤**로 갔다.
- **파일 이름에 `-slow` 가 붙은 이유** — 서버가 그 이름이 든 파일만 **0.5초 늦게** 준다. 지연이 없으면 두 파일이 **파싱 중에 도착**해 버려서 「앞이냐 뒤냐」가 안 갈린다. ★ **판정 지점을 일부러 만든 것**이다.
- ★ **`type="module"` 자체는 인라인에도 먹는다** — A4 의 세 번째 스크립트가 인라인 모듈이었고 그 `import` 가 실제로 돌았다. **`defer`/`async` 와 갈린다.**

### 6. `setTimeout(…, 0)` 까지다 — 1ms 부터는 못 본다

**출력**

```text
===== for i in 1 2 3; do dom html05b-wait.html | grep -o 'class="늦게">[^<]*' | sed 's/.*>//' | tr '\n' ' '; echo; done =====
파싱 중 동기 load 마이크로태스크 setTimeout 0 
파싱 중 동기 load 마이크로태스크 setTimeout 0 
파싱 중 동기 load 마이크로태스크 setTimeout 0 
(exit 0)
```

**왜 그런가**

- **찍히는 것** — 「파싱 중 동기」·「load」·「마이크로태스크」·「setTimeout 0」 **넷.**
- **안 찍히는 것** — `setTimeout` 1·5·10·20·50·200ms **여섯.** 일곱 중 **하나만** 들어온다.
- **경계는 0ms 와 1ms 사이다.** 「100ms 는 못 기다린다」보다 훨씬 이르다.
- **세 판이 한 글자도 같았다** — 이 경계는 **안 흔들리는 칸**이다.
- ★★★ **이 문서 전체에 뜻하는 것** — 이 갈래의 프로브는 **전부 `load` 뒤 `setTimeout(…, 0)` 에서 찍는다.** 그 안에 못 들어오는 것은 **이 도구로 관찰 불가**다. `async` 실험이 0.5초 지연을 쓸 수 있었던 것은 **그 지연이 `load` 안에 들어가기 때문**이고, 지연 로딩·`requestIdleCallback` 같은 것은 **이 배치가 못 본다.**
- ★ **`--virtual-time-budget` 으로 늘리지 않는다.** 가상 시간이 먼저 다 흘러 **「아무 일도 안 일어남」이 찍히는** 사고가 이 저장소에 실측으로 남아 있다.

### 7. 바꾸는 것은 실행 시점이 아니라 「그때 트리에 무엇이 있나」다

**왜 그런가**

- **둘 다 「그 자리에서 바로」 실행된다.** 실행 규칙은 같다 — 다른 것은 **그 자리에 도달했을 때 파서가 얼마나 읽었나**다.
- **`<head>` 의 스크립트에서 본문 요소를 찾으면 `null` 이다.** A1 의 첫 줄에서 `data-mark` 가 **0 개**였다.
- **옛 처방이 피하려던 것** — ① 본문을 못 찾는 것, ② **파싱 차단**으로 화면이 안 그려지는 것. 둘 다 같은 원인에서 온다.
- **오늘은 `defer` 가 그 자리를 대신한다.** 더 나은 점은 **받기를 파싱과 함께 시작**한다는 것이다 — `</body>` 앞에 두면 **거기까지 읽어야** 받기 시작한다.\
  ★ 이 배치는 **실행 순서**만 로그로 찍었고 **언제 요청이 나갔나**는 안 봤다 — 「받기를 더 일찍 시작한다」는 **명세를 읽어 적은 것**이다.

### 8. 보장은 셋, 관찰은 하나

**왜 그런가**

| | 무엇 | 근거 |
|---|---|---|
| **보장** | 평범한 스크립트는 **문서 순서대로 · 그 자리에서** | 명세 |
| **보장** | `defer` 들끼리 · 모듈들끼리 **문서 순서대로**, 둘 다 `DOMContentLoaded` **앞** | 명세 |
| **보장** | `defer`/`async` 의 `document.write` 는 **무시** · `nomodule` 은 **실행 안 함** | 명세 |
| **관찰** | `async` 가 **어디에** 끼어드나 | 이 판·이 머신·이 서버 |

- **보장이 없는 것을 이 문서는 「가짓수」로 적었다.** 순서를 그대로 실으면 독자가 그것을 규칙으로 읽는다.
- **「40판에 두 가지」는 「보장이 없다」의 실증**이다 — 반증이 확증보다 강하다.
- **「40판에 한 가지」였다면** 「보장된다」가 아니라 「**이 판에서는 안 갈렸다**」로 적어야 한다. 같은 바이너리를 20번 돌려 처음 세 번이 같아서 통과할 뻔한 사고가 이 저장소에 남아 있다.

### 9. 「안 받아 옴」과 「받아 놓고 안 돎」 — 요청 로그로만 갈린다

**출력**

```text
===== grep -o '/html05b-[^ ]*' html05b-srv.log | sort | uniq -c =====
     41 /html05b-async-fast.js
      2 /html05b-async-slow.js
      1 /html05b-attr-edge.html
     41 /html05b-bodyend.js
      1 /html05b-both-slow.js
     41 /html05b-classic.js
     41 /html05b-defer.js
     43 /html05b-log.js
      1 /html05b-modasync-slow.mjs
     41 /html05b-module.mjs
      1 /html05b-once.html
      1 /html05b-once.js
      1 /html05b-once.mjs
     40 /html05b-order-race.html
      1 /html05b-order.html
      1 /html05b-race.html
      2 /html05b-write-async.js
      2 /html05b-write-defer.js
      2 /html05b-write-plain.js
      2 /html05b-write.html
(exit 0)
```

**왜 그런가**

- **원인 둘** — ① **파일을 받아 오지도 않았다** ② **받아 놓고 실행하지 않았다.**
- **실행 로그로는 못 가른다.** 둘 다 **로그에 줄이 없다**로 똑같이 보인다(A1 의 `nomodule`).
- **요청 로그를 보면 갈린다.** `html05b-nomodule.js` 는 **목록에 한 줄도 없다** — 다른 파일들이 41번씩 요청되는 동안 **한 번도 요청되지 않았다.**
- **`nomodule` 은 ① 쪽이다.** 모듈을 아는 브라우저는 **아예 받아 오지 않는다** — 대역폭을 안 쓴다.
- ★★ **이 블록이 없으면 「`nomodule` 이 안 돈다」까지만 말할 수 있다.** 창 하나가 더 필요했던 이유이고, 「**이 주제의 네 번째 창은 무엇인가**」의 답이다.

### 10. 정본 경계

**왜 그런가**

| 무엇 | 정본 | 여기는 |
|---|---|---|
| `import`/`export`·라이브 바인딩·순환 의존·동적 `import` | JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**·**44번** | 모듈 **안**은 그쪽. 여기는 **마크업이 그 모듈을 어떻게 켜나** |
| 스타일시트가 렌더를 막는 것·`preload` | 목록의 **09번 주제** | 그쪽은 `<link>`, 여기는 `<script>` |
| 파싱 차단이 왜 파서를 멈추게 하나 | [03번 주제](../03-parser-and-error-recovery/3-answer.md) | 트리 만들기 절차가 그쪽 |
| `innerHTML` 로 넣은 `<script>` 가 안 도는 것 | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **04번** | 그쪽 표면 |

- **JS 갈래와 독립인 이유** — JS 쪽이 답하는 것은 「**모듈 코드가 어떻게 평가되나**」이고, 여기가 답하는 것은 「**마크업의 속성 네 개가 그 평가를 언제 시키나**」다. 속성은 JS 문법이 아니라 **HTML 의 표면**이고, 그래서 **`nomodule`·배치 위치·`document.write` 처럼 JS 에는 대응물이 없는 것**이 이 주제에 남는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.**

**하네스** — 05\~08 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe` 가 그 함수들이고, `serve` 는 **이 주제에서만** 쓴다.

```bash
# html05b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
serve() { python3 html05b-server.py >"$1" 2>&1 & echo $!; }
```

**서버** — 이 주제는 `file://` 이 아니라 **로컬 HTTP 서버** 위에서 돌렸다. 이유가 둘이다.\
① **`async` 파일 하나를 0.5초 늦게 주어야** 실행 순서가 결정적이 된다. ② **요청 로그**(A9)가 있어야 「안 받아 옴」과 「받아 놓고 안 돎」이 갈린다.

```python
# html05b-server.py
import http.server
import time


class 느린서버(http.server.SimpleHTTPRequestHandler):
    """이름에 `-slow` 가 든 파일만 0.5초 늦게 준다.

    async 의 실행 시점은 「내려받기가 끝난 순간」이라 그냥 두면 판마다 자리가 바뀐다.
    한 파일만 확실히 늦게 주면 그 사실이 결정적인 출력으로 드러난다.
    ThreadingHTTPServer 라야 한 요청을 재우는 동안 다른 요청이 지나간다.
    """

    def do_GET(self):
        if "-slow" in self.path:
            time.sleep(0.5)
        return super().do_GET()

    def log_message(self, fmt, *args):
        print(self.path, flush=True)


http.server.ThreadingHTTPServer(("127.0.0.1", 18705), 느린서버).serve_forever()
```

- ★ **`ThreadingHTTPServer` 라야 한다** — 한 요청을 재우는 동안 다른 요청이 지나가야 하기 때문이다.
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).
- ★ **프로브는 `load` 뒤 `setTimeout(…, 0)` 에서 찍는다** — 그것이 `--dump-dom` 의 한계선이다(A6).

**실험에 쓴 외부 스크립트** — 전부 한 줄짜리다. 로그 함수는 위 A1 의 질문 파일에 실려 있다.

```javascript
// html05b-classic.js
window.__mark("평범(head)");
```

```javascript
// html05b-defer.js
window.__mark("defer");
```

```javascript
// html05b-async-slow.js
window.__mark("async(늦게 오는 파일)");
```

```javascript
// html05b-async-fast.js
window.__mark("async(빨리 오는 파일)");
```

```javascript
// html05b-module.mjs
window.__mark("type=module");
```

```javascript
// html05b-nomodule.js
window.__mark("nomodule");
```

```javascript
// html05b-bodyend.js
window.__mark("평범(</body> 앞)");
```

```javascript
// html05b-both-slow.js
window.__mark("defer 와 async 를 함께");
```

```javascript
// html05b-modasync-slow.mjs
window.__mark("type=module + async");
```

```javascript
// html05b-once.mjs
window.__L = window.__L || [];
window.__L.push("html05b-once.mjs 의 본문이 평가됐다");
export const n = 1;
```

```javascript
// html05b-once.js
window.__L = window.__L || [];
window.__L.push("html05b-once.js 의 본문이 평가됐다");
```

**demo 블록** — ★ **이 주제는 `demo` 블록을 두지 않는다.** `demo` 는 외부 파일에 기대지 않는 **자기완결 블록**이어야 하는데, `defer`·`async`·`nomodule` 은 **`src` 가 있는 스크립트에만 먹는다**(A5 가 그 실측이다). 자기완결 블록으로는 이 주제를 보일 수 없다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **네 조합 + 인라인 둘을 한 문서에** | 2 | 동작 방식 (1) · A1 · A7 |
| **늦추지 않은 판 40회** — `sort -u` 가짓수 | 2 (각 40회) | 동작 방식 (2) · A2 · A8 |
| `async` 둘을 나란히 | 2 | 동작 방식 (2) · A2 |
| `document.write` 세 자리 + **콘솔 경고** | 2 | 동작 방식 (3) · A3 |
| 같은 모듈 3회 · 같은 스크립트 2회 | 2 | 동작 방식 (4) · A4 |
| **속성이 무시되는 네 자리** | 2 | 동작 방식 (5) · A5 |
| **요청 로그** | 2 | 동작 방식 (6) · A9 |
| **`--dump-dom` 의 대기 한계** (한 판에 3회) | 2 | 동작 방식 (7) · A6 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| **`async` 의 자리** | 40판에 **2가지** | 경주라 **판마다 바뀐다** — 가짓수만 근거로 쓴다 |
| 콘솔 경고의 문구 | `"Failed to execute 'write' …"` | Blink 의 문구다. **막힌다는 사실**만 명세가 정한다 |
| `--dump-dom` 의 대기 한계 | `setTimeout(…, 0)` 까지 | **도구의 성질**이다. 판이 오르면 다시 잰다 |
| 요청 횟수의 절댓값 | 41·42 | 몇 판을 돌렸나에 달렸다 — **0 인가 아닌가**만 근거로 쓴다 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **내려받기 시각** — 실행 순서만 찍었고 **언제 요청이 나갔나**는 안 봤다(요청 **횟수**만 봤다). 그래서 A7 의 「`defer` 가 받기를 더 일찍 시작한다」는 명세를 읽어 적은 것이다. ③ **`type="module"` 에 `defer` 를 붙이는 경우** — (5) 에서 `async` 조합만 던졌다. ④ **모듈을 모르는 브라우저** — 그런 엔진이 없어 **`nomodule` 의 반대쪽 절반을 못 던졌다.** ⑤ **`innerHTML` 로 넣은 `<script>`** — web-api 04번의 표면이다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — **`setTimeout(…, 1)` 이후에 일어나는 것 전부.** `--dump-dom` 이 그 앞에서 덤프를 뜨므로 **측정 수단 자체가 거기서 끝난다**(A6). 쪼개서 잰 조각은 **경계가 0 과 1 사이라는 것**까지다. ★ `--virtual-time-budget` 으로 늘리는 것은 **금지**다 — 가상 시간이 먼저 흘러 「아무 일도 안 일어남」이 찍힌다.

**부적용인 창** — **창 ③(`innerText` 대 `textContent`)과 창 ④(`compatMode`).** 스크립트 로딩 속성은 렌더된 글자도 문서 모드도 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ 그 대신 이 주제는 **「서버 요청 로그」를 창 하나로 더 썼다**(A9).

## 용어 풀이

- **파싱 차단(parser-blocking)** — 스크립트를 받아 실행할 때까지 파서가 멈추는 것.
- **`defer`** — 받기는 지금, 실행은 파싱이 끝난 뒤 **문서 순서대로.** `src` 가 있는 스크립트에만 먹는다.
- **`async`** — 받기는 지금, 실행은 **받는 대로.** 순서 보장이 없다.
- **`type="module"`** — 모듈로 평가한다. 암묵으로 `defer` 처럼 동작하고 **인라인에도 먹는다.**
- **`nomodule`** — 모듈을 아는 브라우저에서는 실행하지 않는다. 이 판에서는 **요청도 안 됐다.**
- **`DOMContentLoaded`** — HTML 파싱과 `defer`·모듈 실행이 끝났을 때 나는 이벤트.
- **`load`** — 모든 자원이 끝났을 때 나는 이벤트.
- **`document.readyState`** — `loading` → `interactive` → `complete`.
- **모듈 맵(module map)** — URL 마다 모듈을 한 번만 올려 두는 표. 「한 번만 평가된다」의 근거.
- **무음 실패(silent failure)** — 예외도 경고도 없이 결과만 다른 것. `defer`/`async` 의 `document.write` 가 그것이다.
- **가짓수 세기** — 순서가 안 정해진 출력을 `sort -u` 로 모아 **서로 다른 줄이 몇 가지인지** 세는 것. 그 수는 흔들리지 않는다.
