# web-api/15 — 리스너 등록과 해제: `addEventListener` 옵션 객체·`removeEventListener` 의 동일성 조건·`handleEvent` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 여기서 다루는 것은 「이벤트가 어디로 흐르나」가 아니라 「**리스너를 어떻게 달고 어떻게 떼나**」다. 전파 3단계와 `stopPropagation` 은 목록의 **16번 주제**·**17번 주제**가 정본이고 여기서 다시 쓰지 않는다.\
> **기준 소스** — [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 의 「`EventTarget`」·「`AddEventListenerOptions`」·「add an event listener」·「remove an event listener」·「inner invoke」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다.\
> ★ **이 주제에는 「못 잰 것」이 많다** — `passive` 가 실제로 스크롤을 얼마나 빠르게 하는지, 리스너가 붙들고 있는 메모리가 얼마인지, 진짜 터치 입력에서 무엇이 달라지는지를 **하나도 재지 않았다**(아래 「도구가 못 보는 것」).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. 옵션 객체 꼴은 DOM 표준으로 사후 명세화된 표면이고 `signal` 이 가장 늦게 들어왔다(갈래 [`../README.md`](../README.md) 의 지원 표).\
> **선행** — [01번 주제](../01-document-and-node-tree/2-summary.md)(노드 트리)와 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **41번**(네이티브 시맨틱이 무료로 주는 키보드 동작).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 세는 것이 전부 **호출 횟수**이고 시간을 안 재기 때문이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 모든 호출 횟수 · 동일성 격자 14칸 · `defaultPrevented` 값 · 예외 이름과 문구 · 디스패치 도중 목록 변경의 순서 | 같은 판이면 결정적이다. **두 판을 돌려 한 글자도 같았다** |
| **흔들린다** | **콘솔 경고의 줄 수** | Chrome 이 같은 자리에서 난 경고를 합친다. 8번 부른 `preventDefault` 가 **두 줄**로만 남았다((9)) |
| **못 잰다** | `passive` 가 스크롤을 얼마나 빠르게 하나 | 프레임과 입력 지연을 이 도구로 통제하지 못한다. **안 돌려 본 것이 아니라 못 잰 것이다** |
| **못 잰다** | 리스너 하나가 붙들고 있는 **메모리** | 힙 스냅샷을 이 하네스로 찍지 않았다 |
| **부적용** | `--dump-dom` 트리 | 리스너는 트리에 자국을 안 남긴다(아래 창 표) |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ 리스너를 등록하는 것은 「함수를 준다」가 아니라 「세 칸짜리 열쇠를 명부에 적는다」다. 뗄 때는 그 열쇠 세 칸이 전부 맞아야 한다.**

출입 명부에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 명부에 **한 줄을 적는다** | `addEventListener(타입, 콜백, 옵션)` |
| 줄의 **첫 칸** — 어느 문인가 | 이벤트 타입(`'click'`) |
| 줄의 **둘째 칸** — 누가 서 있나 | 콜백 — **같은 사람(객체)** 이라야 한다 |
| 줄의 **셋째 칸** — 들어올 때인가 나갈 때인가 | `capture` — 내려가며 잡나 올라가며 잡나 |
| **줄을 지운다** | `removeEventListener(타입, 콜백, 옵션)` — **세 칸이 다 맞아야** 지워진다 |
| **똑같이 생긴 다른 사람** | 익명 함수 — 글자는 같아도 다른 객체다 |
| **일회용 출입증** | `once: true` — 한 번 쓰고 스스로 사라진다 |
| **여러 줄을 한 번에 회수하는 목줄** | `signal` — `AbortController` 하나로 전부 뗀다 |
| 「저는 **길을 막지 않겠습니다**」라는 약속 | `passive: true` — 그 약속을 어기면 조용히 무시된다 |
| **명부를 볼 수 있는 창구가 없다** | 표준에 「리스너 목록을 달라」는 API 가 없다 — 던져 봐야 안다 |

- ★ **열쇠에 안 들어가는 칸이 있다.** `once`·`passive`·`signal` 은 **적어 두든 말든 지워진다** — 셋은 열쇠가 아니라 **그 줄의 성질**이다.
- ★ **이 주제의 함정은 전부 「지운 줄 알았는데 안 지워졌다」에 있다.** 그리고 **예외가 하나도 안 난다.**

```text
   명부의 한 줄 — 세 칸짜리 열쇠

   +---------+----------------+-----------+   성질(열쇠가 아님)
   |  타입   |     콜백       |  capture  |   once · passive · signal
   +---------+----------------+-----------+
   | 'click' | f (같은 객체)  |   false   |
   +---------+----------------+-----------+

   removeEventListener 는 왼쪽 세 칸만 본다
```

## 이 주제가 답하려는 질문

1. **「같은 리스너」란 무엇인가** — 무엇이 같아야 `removeEventListener` 가 먹히나.
2. **콜백 자리에 함수 말고 무엇을 넣을 수 있나** — 그리고 그때 `this` 는 무엇인가.
3. **떼는 방법이 왜 셋인가** — `removeEventListener`·`once`·`signal` 은 각각 언제 쓰나.

## 이 갈래의 관측 창 — ★ 본체는 **창 ④** 다

★ **이 주제의 본체는 창 ④(디스패치 계수기)다.** 나머지 창은 원리상 아무 말도 못 한다 — **리스너는 트리에도 계산값에도 자국을 안 남기고**, `EventTarget` 의 표면은 명세상 `addEventListener`·`removeEventListener`·`dispatchEvent` **셋뿐**이라 「지금 무엇이 달려 있나」를 묻는 창구가 없다.

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋 위에 이 주제의 창을 얹으면 이렇게 된다.

| 창 | 이 주제에서 | 왜 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | ★ **부적용** | `addEventListener` 로 단 리스너는 **속성으로 남지 않는다.** 트리를 아무리 들여다봐도 안 보인다 |
| 창 ② 노드 단위 프로브 | ★ **부적용** | 노드에 물어볼 프로퍼티가 없다. `el.onclick` 은 **다른 표면**이라 이 주제의 답이 아니다 |
| 창 ③ 같은 것을 두 번 읽기 | ★ **제5의 상태 — 같은 질문을 다른 창으로 물었다** | 「되읽기」가 성립하지 않아 **「같은 이벤트를 두 번 던지기」로 바꿔** 물었다((6)의 `once` 가 그 자리다) |
| **창 ④ 디스패치 계수기** | ★ **본체** | 이벤트를 던지고 **몇 번 불렸나를 센다.** 0 이면 지워진 것이고 1 이면 남은 것이다 |
| 창 ⑤ 콘솔 | 보조 | `passive` 위반처럼 **콘솔에만 남는 경고**가 있다((9)). 다만 **줄 수를 믿으면 안 된다** |

```text
   창 ④ — 이 주제에서 「달려 있나」를 묻는 유일한 방법

   el.addEventListener('t', f);
   el.removeEventListener('t', f, ???);
            |
            v   물어볼 창구가 없다
   el.dispatchEvent(new Event('t'));   <- 던진다
            |
            v
   호출 횟수 0  ->  지워졌다
   호출 횟수 1  ->  ★ 안 지워졌다     (예외도 경고도 없다)
```

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **지금 달려 있는 리스너 목록** | 명세에 그런 API 가 없다. 창 ④ 로 **간접 판정**할 뿐이다 |
| **`passive` 의 값어치**(스크롤 지연·프레임) | 프레임과 입력 지연을 이 하네스로 통제하지 못한다. **재지 않았다** |
| **리스너가 붙들고 있는 메모리** | 힙 스냅샷을 안 찍었다. 누수 이야기는 **원리만** 적고 수치를 안 적는다 |
| **진짜 터치 입력** | 합성 이벤트로만 던졌다. 실제 손가락에서 달라지는 것은 확인하지 않았다 |
| **콘솔 경고의 정확한 건수** | Chrome 이 같은 자리를 합친다((9)의 두 줄이 그것이다) |
| **스크린리더가 무엇을 읽는지** | 접근성 트리는 보조 기술의 **입력**이지 출력이 아니다 |

## 동작 방식

### (1) 「같은 리스너인가」는 글자가 아니라 객체로 판정한다

**언제 쓰나** — 「분명히 지웠는데 계속 불린다」일 때.

**던진 것** — 아래 (2)·(3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-15-ident.html -->
<!doctype html>
<meta charset="utf-8">
<title>15-ident</title>
<div id="자리"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));

O.push('익명 함수는 왜 못 지우나');
const a = document.createElement('div');
let n = 0;
a.addEventListener('t', () => n++);
a.removeEventListener('t', () => n++);
a.dispatchEvent(new Event('t'));
O.push('  똑같이 생긴 익명 함수로 지운 뒤 호출 횟수 = ' + n);
O.push('  두 함수가 같은가: ' + ((() => 1).toString() === (() => 1).toString()) + ' (글자는 같다) · '
     + ((() => 1) === (() => 1)) + ' (참조는 다르다)');
const b = document.createElement('div');
let m = 0;
const 이름있는것 = () => m++;
b.addEventListener('t', 이름있는것);
b.removeEventListener('t', 이름있는것);
b.dispatchEvent(new Event('t'));
O.push('  같은 참조로 지운 뒤 호출 횟수 = ' + m);
O.push('  ★ 「같은 코드」가 아니라 「같은 객체」라야 한다. bind() 도 새 함수를 만든다:');
function 원본() {}
O.push('    원본.bind(null) === 원본.bind(null) 는 ' + (원본.bind(null) === 원본.bind(null)));
O.push('');

O.push('같은 리스너를 두 번 등록하면');
const c = document.createElement('div');
let k = 0;
const f = () => k++;
c.addEventListener('t', f);
c.addEventListener('t', f);
c.dispatchEvent(new Event('t'));
O.push('  두 번 등록하고 한 번 던지면 호출 횟수 = ' + k + '  <- 둘째 등록은 조용히 무시된다');
k = 0;
c.removeEventListener('t', f);
c.dispatchEvent(new Event('t'));
O.push('  한 번만 지우고 다시 던지면    호출 횟수 = ' + k + '  <- 둘 다 사라진다(애초에 하나였다)');
k = 0;
c.addEventListener('t', f, true);
c.addEventListener('t', f, false);
c.dispatchEvent(new Event('t'));
O.push('  capture 만 다르게 두 번 등록하면 호출 횟수 = ' + k + '  <- 이번엔 둘 다 산다');
O.push('');

O.push('동일성 조건 — 등록 옵션과 해제 옵션을 격자로 던진다');
O.push(padw('등록 옵션', 44) + padw('해제 옵션', 44) + '결과');
const 격자 = [];
const 판정 = (등록, 해제) => {
  const e = document.createElement('div');
  let 횟수 = 0;
  const h = () => 횟수++;
  e.addEventListener('t', h, 등록);
  e.removeEventListener('t', h, 해제);
  e.dispatchEvent(new Event('t'));
  const 결과 = 횟수 === 0 ? '지워졌다' : '★ 안 지워졌다';
  격자.push(결과);
  O.push(padw(String(JSON.stringify(등록)), 44) + padw(String(JSON.stringify(해제)), 44) + 결과);
};
판정(undefined, undefined);
판정({ capture: true }, { capture: true });
판정({ capture: true }, undefined);
판정(undefined, { capture: true });
판정(true, { capture: true });
판정({ capture: false }, true);
판정(false, undefined);
판정({ once: true }, undefined);
판정({ once: true }, { once: false });
판정({ passive: true }, { passive: false });
판정({ passive: true }, undefined);
판정({ capture: true, once: true, passive: true }, { capture: true });
판정({ capture: false, once: true }, { capture: true });
판정({ signal: new AbortController().signal }, undefined);
O.push('');
O.push('안 지워진 칸 = ' + 격자.filter(x => x !== '지워졌다').length + ' / ' + 격자.length);
O.push('★ 키에 들어가는 것은 셋뿐이다 — 이벤트 종류 · 콜백(같은 객체) · capture.');
O.push('★ once·passive·signal 은 키가 아니다. 넣든 빼든 반대로 넣든 지워진다.');
O.push('★ 세 번째 인자가 불리언이면 그것이 곧 capture 다 — true 와 {capture:true} 는 같은 키다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
익명 함수는 왜 못 지우나
  똑같이 생긴 익명 함수로 지운 뒤 호출 횟수 = 1
  두 함수가 같은가: true (글자는 같다) · false (참조는 다르다)
  같은 참조로 지운 뒤 호출 횟수 = 0
  ★ 「같은 코드」가 아니라 「같은 객체」라야 한다. bind() 도 새 함수를 만든다:
    원본.bind(null) === 원본.bind(null) 는 false
(exit 0)
```

- **똑같이 생긴 익명 함수로 지우면 안 지워진다** — 호출 횟수가 1 이다. 예외도 경고도 없다.
- **두 함수의 글자는 같은데**(`toString()` 이 `true`) **참조는 다르다**(`===` 가 `false`). 명부가 보는 것은 뒤엣것이다.
- **같은 참조로 지우면 0 이다** — 변수에 담아 두는 것이 유일한 길이다.
- ★ **`bind()` 도 새 함수를 만든다.** `원본.bind(null) === 원본.bind(null)` 이 `false` 다 — **등록할 때 만든 그 함수를 붙들고 있어야** 지울 수 있다.

```text
   같은 코드 / 다른 객체

   addEventListener('t', () => n++)      <- 함수 객체 A 를 명부에 적었다
   removeEventListener('t', () => n++)   <- 함수 객체 B 를 들고 와서 지워 달란다

   A 와 B 는 글자가 같다            toString() === toString()  ->  true
   A 와 B 는 다른 객체다            A === B                    ->  false
   그래서 명부에서 B 를 못 찾는다   -> 아무 일도 안 일어난다
```

```text
   bind 는 지울 수 없는 함수를 만든다

   el.addEventListener('t', 원본.bind(this));   <- 여기서 만든 함수는 이름이 없다
   el.removeEventListener('t', 원본.bind(this)); <- 또 새 함수를 만들어 온다

   고치는 법 — 만든 것을 변수에 담는다
   const 묶은것 = 원본.bind(this);
   el.addEventListener('t', 묶은것);
   el.removeEventListener('t', 묶은것);
```

비용 — 지우려면 **함수 참조를 어딘가에 들고 있어야 한다.** 그 참조가 곧 (7)의 `signal` 이 없애려는 부담이다.

### (2) 같은 리스너를 두 번 등록하면

**언제 쓰나** — 초기화 코드가 두 번 돌았을 때 무슨 일이 나는지.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,11p'
같은 리스너를 두 번 등록하면
  두 번 등록하고 한 번 던지면 호출 횟수 = 1  <- 둘째 등록은 조용히 무시된다
  한 번만 지우고 다시 던지면    호출 횟수 = 0  <- 둘 다 사라진다(애초에 하나였다)
  capture 만 다르게 두 번 등록하면 호출 횟수 = 2  <- 이번엔 둘 다 산다
(exit 0)
```

- **두 번 등록해도 한 번만 불린다.** 둘째 등록은 **조용히 무시**된다 — 명세가 「같은 열쇠가 이미 있으면 아무것도 하지 마라」로 정한다.
- **그래서 한 번만 지우면 둘 다 사라진다.** 애초에 한 줄이었기 때문이다.
- ★ **`capture` 만 다르게 두 번 등록하면 둘 다 산다** — 호출 횟수가 2 다. **열쇠의 셋째 칸이 다르면 다른 줄**이다.

```text
   두 번 등록 — 열쇠가 같으면 한 줄

   addEventListener('t', f)              명부:  [ t | f | false ]
   addEventListener('t', f)   (또)       명부:  [ t | f | false ]   <- 안 늘어난다
   dispatchEvent                          호출 1회

   열쇠가 다르면 두 줄

   addEventListener('t', f, true)        명부:  [ t | f | true  ]
   addEventListener('t', f, false)       명부:  [ t | f | true  ]
                                                [ t | f | false ]   <- 늘어났다
   dispatchEvent                          호출 2회
```

- ★ **중복 등록이 안전해 보이는 것이 함정이다.** 「두 번 달아도 한 번만 불리니까 괜찮다」가 성립하는 것은 **참조가 같을 때뿐**이다. 매번 새 화살표 함수를 넘기면 **부를 때마다 한 줄씩 쌓인다.**

### (3) ★ 동일성 격자 — 안 지워진 칸은 넷이고 전부 같은 이유다

**언제 쓰나** — 「옵션을 어디까지 다시 적어야 하나」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,33p'
동일성 조건 — 등록 옵션과 해제 옵션을 격자로 던진다
등록 옵션                                   해제 옵션                                   결과
undefined                                   undefined                                   지워졌다
{"capture":true}                            {"capture":true}                            지워졌다
{"capture":true}                            undefined                                   ★ 안 지워졌다
undefined                                   {"capture":true}                            ★ 안 지워졌다
true                                        {"capture":true}                            지워졌다
{"capture":false}                           true                                        ★ 안 지워졌다
false                                       undefined                                   지워졌다
{"once":true}                               undefined                                   지워졌다
{"once":true}                               {"once":false}                              지워졌다
{"passive":true}                            {"passive":false}                           지워졌다
{"passive":true}                            undefined                                   지워졌다
{"capture":true,"once":true,"passive":true} {"capture":true}                            지워졌다
{"capture":false,"once":true}               {"capture":true}                            ★ 안 지워졌다
{"signal":{}}                               undefined                                   지워졌다

안 지워진 칸 = 4 / 14
★ 키에 들어가는 것은 셋뿐이다 — 이벤트 종류 · 콜백(같은 객체) · capture.
★ once·passive·signal 은 키가 아니다. 넣든 빼든 반대로 넣든 지워진다.
★ 세 번째 인자가 불리언이면 그것이 곧 capture 다 — true 와 {capture:true} 는 같은 키다.
(exit 0)
```

- **안 지워진 칸이 14 중 4** 다. **그 넷의 공통점은 하나** — 등록 때의 `capture` 와 해제 때의 `capture` 가 다르다.
- **`capture` 를 안 적으면 `false` 로 읽힌다.** 그래서 `{capture: true}` 로 달고 옵션 없이 지우면 **안 지워진다.**
- ★ **`true` 와 `{capture: true}` 는 같은 키다** — 세 번째 인자가 불리언이면 **그것이 곧 `capture`** 다. 격자의 다섯째 줄이 그것을 보인다.
- ★ **`once`·`passive`·`signal` 은 키가 아니다.** 넣든 빼든 **반대로** 넣든(`{passive:true}` 로 달고 `{passive:false}` 로 지워도) 지워진다.
- **`{capture:true, once:true, passive:true}` 로 달고 `{capture:true}` 만으로 지우면 지워진다** — 나머지 둘은 안 보기 때문이다.

```text
   열쇠 세 칸만 본다 — 격자의 결론

   등록                                    해제                   결과
   ------------------------------------    -------------------    --------
   {capture:true}                          {capture:true}         지워졌다
   {capture:true}                          (안 적음 = false)      ★ 안 지워졌다
   (안 적음 = false)                       {capture:true}         ★ 안 지워졌다
   {once:true, passive:true}               (안 적음)              지워졌다
   {capture:true, once:true, passive:true} {capture:true}         지워졌다

   ★ 갈린 자리는 전부 capture 한 칸이다
```

```text
   옵션 객체는 두 무리로 나뉜다

   열쇠 칸                    성질 칸
   +-----------+              +----------+----------+----------+
   |  capture  |              |   once   | passive  |  signal  |
   +-----------+              +----------+----------+----------+
   지울 때 맞춰야 한다         지울 때 안 봐도 된다

   ★ 한 낱말로 외운다: 「capture 는 어디에 서느냐, 나머지는 어떻게 구느냐」
```

### (4) 콜백 자리에 객체를 넣으면 — `handleEvent`

**언제 쓰나** — 상태를 들고 다니는 리스너를 만들 때.

**던진 것** — 아래 (5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-15-obj.html -->
<!doctype html>
<meta charset="utf-8">
<title>15-obj</title>
<div id="겉"><button id="속">단추</button></div>
<script>
const O = [];
const $ = id => document.getElementById(id);
const 겉 = $('겉');

O.push('함수가 아니라 객체를 리스너로 넘기면');
const 손잡이 = {
  이름: '나는 객체다',
  센횟수: 0,
  handleEvent(e) {
    this.센횟수++;
    O.push('  handleEvent 가 불렸다 · this.이름 = ' + this.이름 + ' · e.type = ' + e.type
         + ' · this === 등록한 객체 ? ' + (this === 손잡이));
  }
};
겉.addEventListener('가', 손잡이);
겉.dispatchEvent(new Event('가'));
겉.removeEventListener('가', 손잡이);
겉.dispatchEvent(new Event('가'));
O.push('  removeEventListener(같은 객체) 뒤 다시 던졌고, 위 줄은 한 번만 찍혔다 (센횟수=' + 손잡이.센횟수 + ')');
O.push('');
O.push('handleEvent 는 언제 찾나');
const 늦은 = {};
겉.addEventListener('나', 늦은);
let 예외 = '예외 없음';
try { 겉.dispatchEvent(new Event('나')); } catch (e) { 예외 = e.name + ' 「' + e.message + '」'; }
O.push('  handleEvent 가 없는 객체를 등록하고 던지면 = ' + 예외);
늦은.handleEvent = () => O.push('  나중에 붙인 handleEvent 가 불렸다');
겉.dispatchEvent(new Event('나'));
O.push('  ★ 등록할 때가 아니라 부를 때마다 찾는다. 등록 시점에는 검사도 안 한다.');
const 숫자 = 1;
let 예외2 = '예외 없음';
try { 겉.addEventListener('다', 숫자); } catch (e) { 예외2 = e.name + ' 「' + e.message + '」'; }
O.push('  숫자를 리스너로 등록하면 = ' + 예외2);
let 예외3 = '예외 없음';
try { 겉.addEventListener('다', null); } catch (e) { 예외3 = e.name + ' 「' + e.message + '」'; }
O.push('  null 을 등록하면        = ' + 예외3 + ' (조용히 아무 일도 안 한다)');
O.push('');

O.push('this 가 무엇인가');
겉.addEventListener('라', function (e) {
  O.push('  보통 함수   this === e.currentTarget ? ' + (this === e.currentTarget)
       + ' · this = ' + (this.id ? '#' + this.id : this));
});
const 화살표 = (e) => O.push('  화살표 함수 this === window ? ' + (화살표this === window)
     + ' · e.currentTarget = #' + e.currentTarget.id);
var 화살표this = this;
겉.addEventListener('라', 화살표);
겉.addEventListener('라', function () { O.push('  bind 한 함수 this.표 = ' + this.표); }.bind({ 표: '내가 묶은 것' }));
const 객체리스너 = { 표: '객체 자신', handleEvent() { O.push('  handleEvent  this.표 = ' + this.표); } };
겉.addEventListener('라', 객체리스너);
겉.dispatchEvent(new Event('라'));
O.push('  ★ 보통 함수의 this 는 currentTarget 이다 — target 이 아니다.');
O.push('  ★ 화살표 함수는 바깥 this 를 그대로 쓰므로 currentTarget 을 잃는다. e.currentTarget 으로 받는다.');
O.push('  ★ 객체를 넘기면 this 가 그 객체다 — 상태를 들고 다니는 리스너가 된다.');
O.push('');

O.push('한 객체를 두 요소에 등록하면');
const 세는것 = { 표: [], handleEvent(e) { this.표.push('#' + e.currentTarget.id); } };
겉.addEventListener('마', 세는것);
$('속').addEventListener('마', 세는것);
$('속').dispatchEvent(new Event('마', { bubbles: true }));
O.push('  한 번 던지고 모아 둔 것 = ' + JSON.stringify(세는것.표) + '  <- 같은 객체가 두 자리에서 각각 불린다');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,3p'
함수가 아니라 객체를 리스너로 넘기면
  handleEvent 가 불렸다 · this.이름 = 나는 객체다 · e.type = 가 · this === 등록한 객체 ? true
  removeEventListener(같은 객체) 뒤 다시 던졌고, 위 줄은 한 번만 찍혔다 (센횟수=1)
(exit 0)
```

- **`handleEvent` 메서드를 가진 객체는 그대로 리스너가 된다.** 함수를 싸지 않아도 된다.
- **`this` 가 등록한 객체**다 — `this === 등록한 객체` 가 `true` 다. 상태를 객체 안에 둘 수 있다.
- **지울 때도 같은 객체를 넘긴다** — 열쇠의 둘째 칸이 그 객체다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,10p'
handleEvent 는 언제 찾나
  handleEvent 가 없는 객체를 등록하고 던지면 = 예외 없음
  나중에 붙인 handleEvent 가 불렸다
  ★ 등록할 때가 아니라 부를 때마다 찾는다. 등록 시점에는 검사도 안 한다.
  숫자를 리스너로 등록하면 = TypeError 「Failed to execute 'addEventListener' on 'EventTarget': parameter 2 is not of type 'Object'.」
  null 을 등록하면        = 예외 없음 (조용히 아무 일도 안 한다)
(exit 0)
```

- ★ **`handleEvent` 는 등록할 때가 아니라 부를 때마다 찾는다.** 없는 객체를 등록해도 **예외가 없고**, 나중에 붙이면 **그때부터 불린다.**
- **등록 시점에는 검사도 안 한다** — 「달았는데 안 불린다」의 원인이 오타 하나일 수 있고 **아무도 말해 주지 않는다.**
- **숫자를 넘기면 `TypeError` 로 막힌다** — 객체도 함수도 아니기 때문이다.
- **`null` 을 넘기면 예외가 없고 조용히 아무 일도 안 한다** — 명세가 `null` 을 허용값으로 정했다.

```text
   콜백 자리에 올 수 있는 것

   함수            f                       -> 그대로 부른다
   객체            { handleEvent(e) {} }   -> e 를 받는 메서드를 부른다
   null            null                    -> 조용히 무시 (예외 없음)
   그 밖           1 · 'x'                 -> TypeError 로 막힌다
```

```text
   handleEvent 를 찾는 시점

   addEventListener('t', 객체)   <- 이때는 안 본다 (검사도 안 한다)
            |
            v
   dispatchEvent                  <- 이때 객체.handleEvent 를 읽는다
            |
            +-- 있으면  -> 부른다
            +-- 없으면  -> 아무 일도 안 한다 (예외 없음)

   ★ 그래서 오타 하나가 「조용히 안 불림」이 된다
```

### (5) 리스너 안의 `this` 는 무엇인가

**언제 쓰나** — 리스너 안에서 `this` 를 쓰려다 `undefined` 를 만났을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,19p'
this 가 무엇인가
  보통 함수   this === e.currentTarget ? true · this = #겉
  화살표 함수 this === window ? true · e.currentTarget = #겉
  bind 한 함수 this.표 = 내가 묶은 것
  handleEvent  this.표 = 객체 자신
  ★ 보통 함수의 this 는 currentTarget 이다 — target 이 아니다.
  ★ 화살표 함수는 바깥 this 를 그대로 쓰므로 currentTarget 을 잃는다. e.currentTarget 으로 받는다.
  ★ 객체를 넘기면 this 가 그 객체다 — 상태를 들고 다니는 리스너가 된다.
(exit 0)
```

- **보통 함수의 `this` 는 `currentTarget`** 이다 — **`target` 이 아니다.** 위임(목록의 **18번 주제**)에서 이 구분이 결정적이다.
- **화살표 함수는 바깥 `this` 를 그대로 쓴다** — 모듈 최상위가 아닌 곳에서는 `window` 가 된다. `currentTarget` 을 잃으므로 **`e.currentTarget` 으로 받아야** 한다.
- **`bind` 한 함수는 묶은 것이 `this`** 다 — 대신 (1)에서 본 대로 **지우기가 어려워진다.**
- **객체 리스너는 `this` 가 그 객체**다 — `bind` 없이 상태를 들고 다니는 길이다.

```text
   같은 자리에서 this 가 넷으로 갈린다

   el.addEventListener('t', function (e) { ... });
        this === e.currentTarget          (= el)

   el.addEventListener('t', (e) => { ... });
        this === 바깥의 this              (여기서는 window)

   el.addEventListener('t', f.bind(무엇));
        this === 무엇                      <- 지우기가 어려워진다

   el.addEventListener('t', { handleEvent(e) { ... } });
        this === 그 객체                   <- 지우기도 쉽다
```

- **`this` 네 규칙의 정본은 JS 갈래** 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **07번** 이다. 여기서는 **그 규칙이 리스너 자리에서 어떻게 보이나**만 적는다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,22p'
한 객체를 두 요소에 등록하면
  한 번 던지고 모아 둔 것 = ["#속","#겉"]  <- 같은 객체가 두 자리에서 각각 불린다
(exit 0)
```

- **한 객체를 두 요소에 등록하면 두 자리에서 각각 불린다** — `["#속","#겉"]` 순서는 버블 순서다(정본은 목록의 **16번 주제**).
- ★ **`this` 는 두 번 다 같은 객체**이고 **`currentTarget` 만 갈린다.** 객체 리스너에서 「어디서 불렸나」를 알려면 `this` 가 아니라 `e.currentTarget` 을 본다.

```text
   객체 하나 · 명부 두 줄

   #겉  명부: [ '마' | 세는것 | false ]      this = 세는것 · currentTarget = #겉
   #속  명부: [ '마' | 세는것 | false ]      this = 세는것 · currentTarget = #속

   한 번 던지면 둘 다 불린다 — this 는 같고 currentTarget 만 다르다
```

### (6) `once` — 일회용 출입증

**언제 쓰나** — 한 번만 받고 떼고 싶을 때.

**던진 것** — 아래 (7)·(8)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-15-life.html -->
<!doctype html>
<meta charset="utf-8">
<title>15-life</title>
<div id="겉"><button id="속">단추</button></div>
<script>
const O = [];
const $ = id => document.getElementById(id);
const 겉 = $('겉');

O.push('once — 한 번 불리고 스스로 사라진다');
let k = 0;
겉.addEventListener('가', () => k++, { once: true });
겉.dispatchEvent(new Event('가'));
겉.dispatchEvent(new Event('가'));
겉.dispatchEvent(new Event('가'));
O.push('  세 번 던졌는데 호출 = ' + k + '회');
let 순서 = [];
겉.addEventListener('나', function 자기자신() {
  순서.push('불렸다');
  겉.addEventListener('나', 자기자신, { once: true });
}, { once: true });
겉.dispatchEvent(new Event('나'));
겉.dispatchEvent(new Event('나'));
O.push('  once 안에서 자기를 다시 등록하고 두 번 던지면 = ' + JSON.stringify(순서));
let 던짐 = 0;
겉.addEventListener('다', () => { 던짐++; throw new Error('리스너가 터진다'); }, { once: true });
겉.dispatchEvent(new Event('다'));
겉.dispatchEvent(new Event('다'));
O.push('  once 리스너가 예외를 던져도 = ' + 던짐 + '회 (사라지는 것은 그대로다 · 예외는 콘솔로 샌다)');
O.push('');

O.push('signal — 여러 개를 한 번에 뗀다');
const 지휘 = new AbortController();
let s = 0;
겉.addEventListener('라', () => s++, { signal: 지휘.signal });
$('속').addEventListener('라', () => s++, { signal: 지휘.signal });
document.addEventListener('라', () => s++, { signal: 지휘.signal });
겉.dispatchEvent(new Event('라')); $('속').dispatchEvent(new Event('라')); document.dispatchEvent(new Event('라'));
O.push('  abort 전에 세 자리에 던지면 호출 = ' + s + '회');
지휘.abort();
s = 0;
겉.dispatchEvent(new Event('라')); $('속').dispatchEvent(new Event('라')); document.dispatchEvent(new Event('라'));
O.push('  abort() 한 뒤 같은 것을 던지면 = ' + s + '회');
const 이미 = new AbortController();
이미.abort();
let z = 0;
겉.addEventListener('마', () => z++, { signal: 이미.signal });
겉.dispatchEvent(new Event('마'));
O.push('  이미 abort 된 signal 로 등록하면 = ' + z + '회 (등록 자체가 안 된다)');
O.push('  ★ removeEventListener 는 등록 옵션을 다시 적어야 하는데 signal 은 안 그렇다 — 요즘 관용구다.');
O.push('');

O.push('디스패치 도중에 리스너 목록을 건드리면');
const g = document.createElement('div');
const 로그 = [];
const 뒤늦 = () => 로그.push('나중에 더한 것');
g.addEventListener('바', () => { 로그.push('첫째'); g.addEventListener('바', 뒤늦); });
g.addEventListener('바', () => 로그.push('둘째'));
g.dispatchEvent(new Event('바'));
O.push('  ① 리스너 안에서 새 리스너를 더하면  = ' + JSON.stringify(로그));
로그.length = 0;
g.dispatchEvent(new Event('바'));
O.push('     그 다음 디스패치에서는          = ' + JSON.stringify(로그));
const h = document.createElement('div');
const 로그2 = [];
const 셋째 = () => 로그2.push('셋째');
h.addEventListener('사', () => { 로그2.push('첫째'); h.removeEventListener('사', 셋째); });
h.addEventListener('사', () => 로그2.push('둘째'));
h.addEventListener('사', 셋째);
h.dispatchEvent(new Event('사'));
O.push('  ② 리스너 안에서 뒤엣것을 지우면    = ' + JSON.stringify(로그2));
const i = document.createElement('div');
const 로그3 = [];
const 자기 = () => 로그3.push('자기');
i.addEventListener('아', () => { 로그3.push('첫째'); i.removeEventListener('아', 자기); i.addEventListener('아', 자기); });
i.addEventListener('아', 자기);
i.dispatchEvent(new Event('아'));
O.push('  ③ 지웠다가 곧바로 다시 더하면      = ' + JSON.stringify(로그3));
O.push('  ★ 더한 것은 이번 디스패치에 안 들어오고, 지운 것은 이번 디스패치에서 곧바로 빠진다.');
O.push('  ★ 비대칭이다 — 명세가 「목록을 복사해 두되 지워진 것은 건너뛴다」로 정했기 때문이다.');
O.push('');

O.push('stopImmediatePropagation 과 견주면');
const j = document.createElement('div');
const 로그4 = [];
j.addEventListener('자', e => { 로그4.push('첫째'); e.stopImmediatePropagation(); });
j.addEventListener('자', () => 로그4.push('둘째'));
j.dispatchEvent(new Event('자'));
O.push('  같은 요소의 뒤엣것을 막으면 = ' + JSON.stringify(로그4) + '  (정본은 목록의 17번 주제다)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,4p'
once — 한 번 불리고 스스로 사라진다
  세 번 던졌는데 호출 = 1회
  once 안에서 자기를 다시 등록하고 두 번 던지면 = ["불렸다","불렸다"]
  once 리스너가 예외를 던져도 = 1회 (사라지는 것은 그대로다 · 예외는 콘솔로 샌다)
(exit 0)
```

- **세 번 던져도 한 번만 불린다** — **부르기 직전에** 명부에서 지워지기 때문이다(명세가 그렇게 정한다).
- ★ **`once` 안에서 자기를 다시 등록하면 다음 번에 또 불린다** — 「불렸다」가 두 개다. **떼고 다는 것을 손으로 하는 것과 같다.**
- ★ **리스너가 예외를 던져도 `once` 는 그대로 사라진다** — 호출이 1회에서 멈춘다. **예외는 콘솔로 새고 디스패치는 계속된다.**
- ★ **이것이 창 ③ 의 자리다** — 「대입하고 되읽기」가 성립하지 않아 **「같은 이벤트를 두 번 던지기」로 바꿔** 물었다.

```text
   once 의 수명 — 지우고 나서 부른다

   dispatchEvent 1회
        |
        +-- 명부에서 그 줄을 먼저 지운다
        +-- 그 다음 콜백을 부른다      <- 여기서 예외가 나도 이미 지워졌다
        |
   dispatchEvent 2회                     -> 명부에 없다. 안 불린다
```

### (7) `signal` — 목줄 하나로 여럿을 뗀다

**언제 쓰나** — 컴포넌트가 사라질 때 자기가 단 것을 전부 떼야 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '6,10p'
signal — 여러 개를 한 번에 뗀다
  abort 전에 세 자리에 던지면 호출 = 3회
  abort() 한 뒤 같은 것을 던지면 = 0회
  이미 abort 된 signal 로 등록하면 = 0회 (등록 자체가 안 된다)
  ★ removeEventListener 는 등록 옵션을 다시 적어야 하는데 signal 은 안 그렇다 — 요즘 관용구다.
(exit 0)
```

- **한 `AbortController` 로 세 자리를 묶고 `abort()` 한 번에 전부 떼였다** — 3회가 0회가 됐다.
- ★ **이미 `abort()` 된 signal 로 등록하면 등록 자체가 안 된다** — 호출이 0회다. 명세가 「신호가 이미 중단됐으면 그냥 돌아가라」로 정한다.
- ★ **`removeEventListener` 는 `capture` 를 다시 적어야 하는데 `signal` 은 안 그렇다.** (3)의 격자에서 본 실수가 **원리상 생기지 않는다** — 그래서 요즘 관용구다.

```text
   떼는 세 가지 길

   ① removeEventListener(타입, 콜백, {capture})
        - 세 칸을 다시 맞춰야 한다     <- (3) 의 네 칸이 여기서 샌다
        - 함수 참조를 들고 있어야 한다

   ② { once: true }
        - 한 번 불리면 저절로
        - 「여러 번 받다가 그만」에는 못 쓴다

   ③ { signal: 지휘.signal }  +  지휘.abort()
        - 여러 줄을 한 번에
        - 참조도 capture 도 다시 안 적는다
```

```text
   signal 하나가 묶는 것

                 지휘 = new AbortController()
                          |
        +-----------------+-----------------+
        v                 v                 v
   #겉 의 '라'       #속 의 '라'       document 의 '라'

   지휘.abort()  ->  세 줄이 한꺼번에 명부에서 빠진다
```

비용 — `AbortController` 하나가 **모든 리스너를 한 묶음으로 만든다.** 일부만 떼고 싶으면 **컨트롤러를 나눠야** 한다.

### (8) ★ 디스패치 도중에 목록을 건드리면 — 더하기와 빼기가 비대칭이다

**언제 쓰나** — 리스너 안에서 리스너를 붙이거나 떼는 코드를 볼 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,18p'
디스패치 도중에 리스너 목록을 건드리면
  ① 리스너 안에서 새 리스너를 더하면  = ["첫째","둘째"]
     그 다음 디스패치에서는          = ["첫째","둘째","나중에 더한 것"]
  ② 리스너 안에서 뒤엣것을 지우면    = ["첫째","둘째"]
  ③ 지웠다가 곧바로 다시 더하면      = ["첫째"]
  ★ 더한 것은 이번 디스패치에 안 들어오고, 지운 것은 이번 디스패치에서 곧바로 빠진다.
  ★ 비대칭이다 — 명세가 「목록을 복사해 두되 지워진 것은 건너뛴다」로 정했기 때문이다.
(exit 0)
```

- **① 더한 것은 이번 디스패치에 안 들어온다** — `["첫째","둘째"]` 다. **그 다음 디스패치**에서야 셋이 된다.
- **② 지운 것은 이번 디스패치에서 곧바로 빠진다** — 「셋째」가 안 불렸다.
- ★ **③ 지웠다가 곧바로 다시 더하면 이번 디스패치에서 안 불린다** — `["첫째"]` 뿐이다. **「지워서 빠지고」 + 「더해서 안 들어오고」가 겹친다.**
- **명세가 「목록을 복사해 두되, 부르기 직전에 아직 남아 있는지 다시 본다」로 정하기 때문**이다. 복사 때문에 더한 것이 안 보이고, 다시 보기 때문에 지운 것이 빠진다.

```text
   디스패치가 하는 일 — 복사해 두고, 부르기 전에 다시 본다

   dispatchEvent 시작
        |
        +-- 지금 명부를 통째로 복사한다      [ 첫째 · 둘째 · 셋째 ]
        |
        +-- 첫째를 부르기 전: 아직 명부에 있나? 있다 -> 부른다
        |      (첫째가 '넷째' 를 더한다)     복사본에는 없다 -> 이번엔 안 불린다
        |      (첫째가 '셋째' 를 지운다)     명부에서 빠졌다
        |
        +-- 둘째를 부르기 전: 있나? 있다 -> 부른다
        |
        +-- 셋째를 부르기 전: 있나? 없다 -> 건너뛴다
```

```text
   ③ 지웠다가 곧바로 다시 더하면

   복사본:  [ 첫째 · 자기 ]
   첫째가 돌면서  remove(자기)  ->  명부에서 빠졌다
                  add(자기)     ->  명부에 다시 들어갔지만 복사본에는 없다

   「자기」를 부를 차례
        복사본의 그 줄은 이미 명부에 없는 줄이다  ->  건너뛴다
        명부의 새 줄은 복사본에 없다              ->  이번엔 안 본다

   결과: ["첫째"]  — 한 번도 안 불린다
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,21p'
stopImmediatePropagation 과 견주면
  같은 요소의 뒤엣것을 막으면 = ["첫째"]  (정본은 목록의 17번 주제다)
(exit 0)
```

- **`stopImmediatePropagation()` 은 같은 요소의 뒤엣것까지 막는다** — 목록을 건드리지 않고도 같은 모양이 나온다.
- **둘은 다른 일이다** — 지우기는 **명부를 바꾸고**, `stopImmediatePropagation` 은 **이번 디스패치만 멈춘다.** 정본은 목록의 **17번 주제**다.

### (9) `passive` — 「막지 않겠다」는 약속을 어기면 조용히 무시된다

**언제 쓰나** — `preventDefault()` 를 불렀는데 아무 일도 안 일어날 때.

**던진 것** — 아래 (10)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-15-passive.html -->
<!doctype html>
<meta charset="utf-8">
<title>15-passive</title>
<div id="상자" style="height:200px;overflow:auto"><div style="height:2000px">긴 내용</div></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);

O.push('passive 가 preventDefault 를 막는다');
const 상자 = $('상자');
let 결과1, 결과2;
상자.addEventListener('wheel', e => { e.preventDefault(); 결과1 = e.defaultPrevented; }, { passive: true });
상자.dispatchEvent(new WheelEvent('wheel', { cancelable: true, bubbles: true }));
const 상자2 = document.createElement('div'); document.body.appendChild(상자2);
상자2.addEventListener('wheel', e => { e.preventDefault(); 결과2 = e.defaultPrevented; }, { passive: false });
상자2.dispatchEvent(new WheelEvent('wheel', { cancelable: true, bubbles: true }));
O.push('  passive: true  에서 preventDefault() 뒤 defaultPrevented = ' + 결과1);
O.push('  passive: false 에서 preventDefault() 뒤 defaultPrevented = ' + 결과2);
O.push('  ★ 예외가 아니라 「아무 일도 안 일어남」이다. 경고 한 줄이 콘솔에만 남는다.');
O.push('  ★ cancelable 은 그대로 true 다 — 이벤트가 막을 수 없게 된 것이 아니라 이 리스너가 못 막는 것이다.');
O.push('');

O.push('기본값이 passive 인 자리 — 같은 코드가 대상에 따라 갈린다');
O.push(padw('어디에 달았나', 26) + padw('이벤트', 14) + 'preventDefault 가 먹히나');
const 판정 = (대상, 라벨, 형) => {
  let 먹혔나;
  const h = e => { e.preventDefault(); 먹혔나 = e.defaultPrevented; };
  대상.addEventListener(형, h);
  대상.dispatchEvent(new Event(형, { cancelable: true }));
  대상.removeEventListener(형, h);
  O.push(padw(라벨, 26) + padw(형, 14) + (먹혔나 ? '먹힌다' : '★ 안 먹힌다 (기본이 passive)'));
};
for (const 형 of ['touchstart', 'touchmove', 'wheel', 'mousewheel', 'click']) {
  판정(window, 'window', 형);
}
판정(document, 'document', 'touchstart');
판정(document.body, 'document.body', 'touchstart');
판정(document.documentElement, 'document.documentElement', 'touchstart');
판정($('상자'), '평범한 div', 'touchstart');
판정($('상자'), '평범한 div', 'wheel');
O.push('');
O.push('★ window·document·body·html 에 다는 touchstart·touchmove·wheel·mousewheel 은 기본이 passive 다.');
O.push('★ 나머지는 기본이 passive 가 아니다. 같은 한 줄이 대상에 따라 다르게 산다.');
O.push('');

O.push('되돌리려면 passive: false 를 명시한다');
let 되돌림;
window.addEventListener('touchstart', e => { e.preventDefault(); 되돌림 = e.defaultPrevented; }, { passive: false });
window.dispatchEvent(new Event('touchstart', { cancelable: true }));
O.push('  window + {passive: false} 에서 = ' + 되돌림);
O.push('');
O.push('passive 는 동일성 키가 아니므로 지울 때는 안 적어도 된다');
let p = 0;
const 리 = () => p++;
window.addEventListener('scroll', 리, { passive: true });
window.removeEventListener('scroll', 리);
window.dispatchEvent(new Event('scroll'));
O.push('  {passive:true} 로 달고 옵션 없이 지운 뒤 호출 = ' + p + '회');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
passive 가 preventDefault 를 막는다
  passive: true  에서 preventDefault() 뒤 defaultPrevented = false
  passive: false 에서 preventDefault() 뒤 defaultPrevented = true
  ★ 예외가 아니라 「아무 일도 안 일어남」이다. 경고 한 줄이 콘솔에만 남는다.
  ★ cancelable 은 그대로 true 다 — 이벤트가 막을 수 없게 된 것이 아니라 이 리스너가 못 막는 것이다.
(exit 0)
```

- **`passive: true` 에서 `preventDefault()` 는 아무 일도 안 한다** — `defaultPrevented` 가 `false` 다. **예외가 아니다.**
- **`passive: false` 에서는 먹힌다** — `true` 다.
- ★ **`cancelable` 은 그대로 `true`** 다. **이벤트가 막을 수 없게 된 것이 아니라 이 리스너가 못 막는 것**이다 — `cancelable` 만 보고 판정하면 틀린다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --enable-logging=stderr --dump-dom wa12b-15-passive.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sed 's#, source: file://[^ ]*/# · #'
"Unable to preventDefault inside passive event listener invocation." · wa12b-15-passive.html (14)
"Unable to preventDefault inside passive event listener invocation." · wa12b-15-passive.html (14)
(exit 0)
```

- **경고가 콘솔에만 남는다** — 화면에도 반환값에도 아무 표시가 없다.
- ★ ★ **줄 수를 믿으면 안 된다.** 이 실행에서 `passive` 리스너 안의 `preventDefault()` 는 **여덟 번** 불렸는데 콘솔에는 **두 줄**만 남았다. Chrome 이 **같은 자리에서 난 경고를 합친다**(두 줄 다 같은 소스 줄을 가리킨다). **「경고가 안 보인다」를 「안 났다」로 읽으면 안 된다.**

```text
   passive 가 막는 것은 딱 하나다

   e.preventDefault()  안에서 무슨 일이 나나

   passive: false     ->  defaultPrevented = true   · 기본 동작이 안 난다
   passive: true      ->  defaultPrevented = false  · 기본 동작이 그대로 난다
                          + 콘솔에 경고 한 줄
                          + e.cancelable 은 여전히 true   <- 여기서 헷갈린다
```

```text
   이 주제의 조용한 실패 네 가지

   ① 옵션이 달라 안 지워짐      -> 계속 불린다      (예외 없음)
   ② 익명 함수라 안 지워짐      -> 계속 불린다      (예외 없음)
   ③ handleEvent 오타          -> 영영 안 불린다   (예외 없음)
   ④ passive 에서 preventDefault -> 안 막힌다       (콘솔에만)

   ★ 전부 창 ④ (던져서 세기) 로만 드러난다
```

### (10) 기본값이 `passive` 인 자리 — 같은 한 줄이 대상에 따라 다르게 산다

**언제 쓰나** — 「나는 `passive` 를 쓴 적이 없는데」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,21p'
기본값이 passive 인 자리 — 같은 코드가 대상에 따라 갈린다
어디에 달았나             이벤트        preventDefault 가 먹히나
window                    touchstart    ★ 안 먹힌다 (기본이 passive)
window                    touchmove     ★ 안 먹힌다 (기본이 passive)
window                    wheel         ★ 안 먹힌다 (기본이 passive)
window                    mousewheel    ★ 안 먹힌다 (기본이 passive)
window                    click         먹힌다
document                  touchstart    ★ 안 먹힌다 (기본이 passive)
document.body             touchstart    ★ 안 먹힌다 (기본이 passive)
document.documentElement  touchstart    ★ 안 먹힌다 (기본이 passive)
평범한 div                touchstart    먹힌다
평범한 div                wheel         먹힌다

★ window·document·body·html 에 다는 touchstart·touchmove·wheel·mousewheel 은 기본이 passive 다.
★ 나머지는 기본이 passive 가 아니다. 같은 한 줄이 대상에 따라 다르게 산다.
(exit 0)
```

- ★ **`window`·`document`·`document.body`·`document.documentElement` 에 다는 `touchstart`·`touchmove`·`wheel`·`mousewheel` 은 기본이 `passive`** 다. 옵션을 안 적었는데 그렇다.
- **같은 네 대상이라도 `click` 은 아니다** — 목록에 든 네 종류만 그렇다.
- **평범한 요소에 달면 `touchstart` 도 `wheel` 도 먹힌다** — **대상이 갈림길**이다.
- ★ **그래서 「같은 한 줄」이 `window` 에서는 안 먹히고 `div` 에서는 먹힌다.** 코드만 봐서는 안 보인다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '23,27p'
되돌리려면 passive: false 를 명시한다
  window + {passive: false} 에서 = true

passive 는 동일성 키가 아니므로 지울 때는 안 적어도 된다
  {passive:true} 로 달고 옵션 없이 지운 뒤 호출 = 0회
(exit 0)
```

- **되돌리려면 `{passive: false}` 를 명시**한다 — `window` 에서도 먹힌다.
- **지울 때는 `passive` 를 안 적어도 된다** — (3)의 격자대로 열쇠가 아니기 때문이다. 호출이 0회다.

```text
   같은 코드 · 다른 결과

   window.addEventListener('touchstart', e => e.preventDefault());
        -> 안 먹힌다 (기본이 passive)

   div   .addEventListener('touchstart', e => e.preventDefault());
        -> 먹힌다

   window.addEventListener('touchstart', e => e.preventDefault(), {passive: false});
        -> 먹힌다
```

```text
   기본이 passive 인 칸

                 touchstart  touchmove  wheel  mousewheel  click
   window            P           P        P        P         -
   document          P           ?        ?        ?         ?
   body              P           ?        ?        ?         ?
   html              P           ?        ?        ?         ?
   평범한 요소       -           ?        -        ?         ?

   P = 기본이 passive (실측)   - = 아니다 (실측)   ? = 이 문서가 안 던졌다
```

비용 — **재지 않았다.** `passive` 가 스크롤을 얼마나 빠르게 하는지 이 문서는 **주장하지 않는다.** 규칙(무엇이 먹히고 무엇이 안 먹히나)만 실측했다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// wa12b-15-form.js
// 세 번째 인자는 두 꼴이다
el.addEventListener('click', f);                 // 옵션 없음 = {capture: false}
el.addEventListener('click', f, true);           // 불리언 = capture
el.addEventListener('click', f, { capture: true, once: true, passive: true, signal: s });

// 떼는 세 길
el.removeEventListener('click', f, { capture: true });   // 열쇠 세 칸을 맞춘다
el.addEventListener('click', f, { once: true });         // 한 번 쓰고 저절로
const 지휘 = new AbortController();
el.addEventListener('click', f, { signal: 지휘.signal });
지휘.abort();                                            // 묶은 것을 전부

// 콜백 자리에 올 수 있는 것
el.addEventListener('click', f);                         // 함수
el.addEventListener('click', { handleEvent(e) {} });     // 객체
el.addEventListener('click', null);                      // 조용히 무시
```

```text
   세 번째 인자 두 꼴 — 같은 것을 말하는 두 방법

   addEventListener('t', f, true)            ==  addEventListener('t', f, {capture: true})
   addEventListener('t', f, false)           ==  addEventListener('t', f, {capture: false})
   addEventListener('t', f)                  ==  addEventListener('t', f, {capture: false})

   ★ 불리언 꼴로는 once·passive·signal 을 줄 수 없다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// wa12b-15-bad.js
// 1. 익명 함수로 달고 익명 함수로 지운다 — 영영 안 지워진다
el.addEventListener('click', () => 무엇());
el.removeEventListener('click', () => 무엇());
const 지울것 = () => 무엇();                     // 이렇게 담아 둔다

// 2. bind 를 인자 자리에서 만든다 — 위와 같은 실수다
el.addEventListener('click', this.눌림.bind(this));
this.묶은것 = this.눌림.bind(this);              // 이렇게 담아 둔다

// 3. capture 로 달고 옵션 없이 지운다 — 안 지워진다
el.addEventListener('click', f, { capture: true });
el.removeEventListener('click', f);              // 안 지워진다
el.removeEventListener('click', f, { capture: true });

// 4. 지울 때 once·passive 까지 다시 적는다 — 해롭지는 않지만 오해를 부른다
el.removeEventListener('click', f, { once: true, passive: true });

// 5. passive 인 자리에서 preventDefault 로 막으려 한다 — 조용히 무시된다
window.addEventListener('touchstart', e => e.preventDefault());
window.addEventListener('touchstart', e => e.preventDefault(), { passive: false });

// 6. cancelable 만 보고 「막을 수 있다」고 판정한다
if (e.cancelable) e.preventDefault();            // passive 면 그래도 안 먹힌다

// 7. handleEvent 를 handleevent 로 적는다 — 예외도 경고도 없다
el.addEventListener('click', { handleevent(e) {} });
```

### 어디서 헷갈리나

- **`capture` 와 `once`** — 둘 다 옵션 객체의 칸인데 **하나는 열쇠고 하나는 성질**이다.
- **`this` 와 `e.target`** — 보통 함수의 `this` 는 `currentTarget` 이지 `target` 이 아니다.
- **`cancelable` 과 `passive`** — 앞엣것은 **이벤트의 성질**, 뒤엣것은 **리스너의 성질**이다.
- **`removeEventListener` 와 `stopPropagation`** — 앞엣것은 명부를 바꾸고 뒤엣것은 이번 디스패치만 멈춘다(정본은 목록의 **17번 주제**).

## 어디서 틀리나

### 1. 익명 함수로 달고 지우려 한다

**글자가 같아도 다른 객체**라 안 지워진다. 실측에서 호출 횟수가 1 이었다. 예외도 경고도 없다. **변수에 담아 두는 것**이 유일한 길이고, 그러기 싫으면 `signal` 을 쓴다.

### 2. `capture` 를 한쪽에만 적는다

동일성 격자 **14칸 중 안 지워진 4칸이 전부 이것**이다. **등록과 해제의 `capture` 가 같아야** 한다.

### 3. `once`·`passive` 를 지울 때도 적어야 한다고 믿는다

**안 봐도 된다.** 격자에서 `{passive:true}` 로 달고 `{passive:false}` 로 지워도 지워졌다. 다만 **적어도 해롭지는 않다** — 읽는 사람이 헷갈릴 뿐이다.

### 4. `handleEvent` 오타를 못 잡는다

**등록 시점에 검사가 없다.** 「달았는데 안 불린다」의 원인이 메서드 이름 하나일 수 있고 **콘솔에도 안 남는다.**

### 5. 리스너 안에서 목록을 바꿔 놓고 이번 디스패치에 반영될 거라 믿는다

**더한 것은 안 들어오고 지운 것은 빠진다.** 특히 **지웠다 다시 더하면 이번 판에서 한 번도 안 불린다**((8)의 ③).

### 6. `passive` 인 줄 모르고 `preventDefault()` 를 쓴다

`window`·`document`·`body`·`html` 의 `touchstart`·`touchmove`·`wheel`·`mousewheel` 은 **기본이 `passive`** 다. 코드에 아무 표시가 없다. **`{passive: false}` 를 명시**해야 한다.

### 7. 콘솔 경고가 안 보이니 문제가 없다고 읽는다

실측에서 **여덟 번의 위반이 두 줄로 합쳐졌다.** 경고의 **건수는 근거가 아니다.**

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 동일성 키가 **타입·콜백·`capture`** 인 것 | **명세**(DOM — add/remove an event listener) |
| 세 번째 인자가 불리언이면 `capture` 인 것 | **명세**(DOM — flatten / flatten more) |
| 같은 열쇠로 두 번 등록해도 **한 줄**인 것 | **명세**(DOM — 「이미 있으면 아무것도 하지 않는다」) |
| `once` 가 **부르기 직전에** 지워지는 것 | **명세**(DOM — inner invoke) |
| **디스패치가 목록을 복사**하고, 지워진 것은 건너뛰는 것 | **명세**(DOM — inner invoke) |
| 이미 abort 된 `signal` 로는 **등록 자체가 안 되는** 것 | **명세**(DOM — add an event listener) |
| `handleEvent` 를 **호출할 때마다 찾는** 것 | **명세**(DOM — inner invoke 가 그때 `handleEvent` 를 가져온다) |
| `null` 이 **조용히 무시**되는 것 | **명세**(IDL — `EventListener?`) |
| `passive` 가 `preventDefault()` 를 **무효로 만드는** 것 | **명세**(DOM — set the canceled flag 는 passive 면 아무것도 안 한다) |
| 예외 문구(`parameter 2 is not of type 'Object'.` 등) | ★ **구현.** 문구는 Chrome 의 것이다. 외울 것은 **이름**(`TypeError`)이다 |
| **`window`·`document`·`body`·`html` 의 네 종류가 기본 `passive`** 인 것 | ★ **구현 관행이 명세로 올라간 자리**다. 이 문서는 **Chrome 151 의 관찰**로만 적는다 |
| **콘솔 경고의 줄 수** | ★ **구현.** Chrome 이 같은 자리를 합친다 |
| `passive` 의 **성능 이득** | ★ **재지 않았다.** 이 문서는 주장하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 나중에 떼야 한다 | 참조를 변수에 담기 · `signal` | 인자 자리에서 만든 화살표 함수·`bind` |
| 여러 리스너를 한꺼번에 뗀다 | `AbortController` 하나 | 참조를 배열에 모아 두고 순회 |
| 한 번만 받는다 | `{ once: true }` | 리스너 안에서 자기를 `removeEventListener` |
| `capture` 단계에서 받는다 | `{ capture: true }` — **지울 때도 같이** | 불리언 꼴과 객체 꼴을 섞어 쓰기 |
| 상태를 들고 다니는 리스너 | `handleEvent` 객체 | 매번 새로 `bind` 한 함수 |
| 리스너 안에서 `this` 가 요소여야 한다 | `function` 꼴 · 객체 리스너 | 화살표 함수(`e.currentTarget` 으로 받아라) |
| 스크롤 중 기본 동작을 막아야 한다 | `{ passive: false }` 를 **명시** | 옵션 없이 `window` 에 달기 |
| 「지워졌나」를 확인한다 | **던져서 세기**(창 ④) | 트리·계산값 들여다보기 |
| 전파를 멈춘다 | 목록의 **17번 주제** | `removeEventListener` 로 흉내 내기 |

## 핵심 문장

1. **리스너의 열쇠는 세 칸이다** — 타입 · 콜백(같은 객체) · `capture`. **지울 때 세 칸이 다 맞아야 한다.**
2. **`once`·`passive`·`signal` 은 열쇠가 아니라 성질이다** — 지울 때 안 적어도 된다.
3. **익명 함수와 `bind` 는 지울 수 없는 리스너를 만든다** — 참조를 담아 두거나 `signal` 을 쓴다.
4. **콜백 자리에 객체를 넣으면 `handleEvent` 가 불리고 `this` 가 그 객체다** — 그 메서드는 **부를 때마다** 찾는다.
5. **보통 함수의 `this` 는 `currentTarget`** 이지 `target` 이 아니다.
6. **디스패치는 목록을 복사한다** — 더한 것은 이번 판에 안 들어오고 지운 것은 곧바로 빠진다.
7. **`passive` 는 `preventDefault()` 를 조용히 무효로 만든다** — `cancelable` 은 그대로 `true` 다.
8. **`window`·`document`·`body`·`html` 의 스크롤 관련 네 종류는 기본이 `passive`** — 같은 한 줄이 대상에 따라 다르게 산다.
9. **이 주제의 실패는 전부 조용하다** — 던져서 세는 것(창 ④)이 유일한 진단이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 15번)
- [01번 주제](../01-document-and-node-tree/2-summary.md) — 이 갈래의 창 ①\~③ 을 세운 편. **여기서는 그 셋이 거의 부적용**이다
- [12번 주제](../12-shadow-dom/2-summary.md) — 그림자 경계를 넘는 이벤트. **리스너를 어디에 다느냐가 `e.target` 을 바꾼다**
- 목록의 **13번 주제**(커스텀 요소 수명주기) — `connectedCallback` 에서 달고 `disconnectedCallback` 에서 떼는 짝. **`signal` 이 그 짝을 한 줄로 만든다**
- 목록의 **16번 주제**(전파 3단계) — ★ **`capture` 가 무엇을 하는지의 정본이 그쪽**이다. 여기는 **그것이 동일성 키라는 것**까지
- 목록의 **17번 주제**(`stopPropagation` 대 `preventDefault`) — ★ **`stopImmediatePropagation` 과 `preventDefault` 의 정본**
- 목록의 **18번 주제**(이벤트 위임) — `this` 와 `e.target` 의 구분이 값어치를 내는 자리
- 목록의 **19번 주제**(`passive` 와 스크롤 성능) — ★ **`passive` 가 왜 생겼나와 실제 이득의 정본이 그쪽**이다. 여기는 **「무엇이 무효가 되나」라는 규칙만**
- 목록의 **20번 주제**(리스너 수명과 누수) — ★ **리스너가 무엇을 붙들고 있나의 정본.** 여기는 **떼는 방법 셋**까지
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **07번** — `this` 네 규칙의 정본
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **09번** — `bind` 가 새 함수를 만든다는 것의 정본
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **41번** — `AbortController`/`AbortSignal` 이 호스트 API 라는 것
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **41번** — `<button>` 이 무료로 주는 키보드 동작. **리스너를 달기 전에 확인할 것**

## 용어 풀이

- **리스너(event listener)** — 명부의 한 줄. 타입·콜백·`capture` 와 성질(`once`·`passive`·`signal`)로 이루어진다.
- **콜백(callback)** — 그 줄에 적힌 함수 또는 `handleEvent` 를 가진 객체.
- **동일성 조건** — `removeEventListener` 가 「같은 줄」로 인정하는 조건. **타입 · 콜백 · `capture` 셋**이다.
- **`capture`** — 이벤트가 **내려갈 때** 잡을지 **올라갈 때** 잡을지. 단계 자체의 정본은 목록의 **16번 주제**.
- **`once`** — 한 번 불리고 스스로 빠지는 성질. **부르기 직전에** 빠진다.
- **`passive`** — 「기본 동작을 막지 않겠다」는 약속. 어기면 `preventDefault()` 가 **조용히 무효**가 된다.
- **`signal`** — `AbortSignal`. `abort()` 한 번으로 그 신호에 묶인 리스너를 전부 뗀다.
- **`handleEvent`** — 객체를 리스너로 쓸 때 불리는 메서드 이름. **호출할 때마다** 찾는다.
- **`currentTarget`** — 지금 이 리스너가 달려 있는 요소. 보통 함수의 `this` 가 이것이다.
- **`defaultPrevented`** — `preventDefault()` 가 실제로 먹혔는지. `passive` 면 `false` 로 남는다.
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제에 네 가지가 있다.
- **창 ④ (디스패치 계수기)** — 이벤트를 던져 **몇 번 불렸나를 세는** 관측. 이 주제의 본체다.

## 더 들어가면

- **`el.onclick` 은 다른 표면**이다 — 한 자리에 하나만 들어가고 덮어쓰기가 된다. `addEventListener` 와 **명부가 다르다**. **이 문서는 그 표면을 던져 보지 않았다.**
- **`capture` 단계에서 `stopPropagation()` 을 부르면 타깃까지 못 간다** — 정본은 목록의 **17번 주제**이고 **여기서 던지지 않았다.**
- **그림자 경계를 넘는 리스너**는 [12번 주제](../12-shadow-dom/2-summary.md)가 정본이다. **같은 콜백이 어느 트리에 달렸느냐에 따라 `e.target` 이 달라진다.**
- **리스너가 만드는 누수**는 「요소를 지웠는데 리스너가 클로저를 붙들고 있는」 모양이다. **이 문서는 메모리를 재지 않았다** — 정본은 목록의 **20번 주제**.
- **`AbortSignal.timeout()`·`AbortSignal.any()`** 로 신호를 합칠 수 있다. **던져 보지 않았다** — 목록의 **27번 주제** 몫이다.
- **`{ passive: true }` 가 실제로 얼마나 이득인가**는 **재지 않았다.** 목록의 **19번 주제**가 그 자리다.
- **`el.addEventListener` 의 반환값은 `undefined`** 이고 **「등록됐나」를 알려 주지 않는다.** 그래서 창 ④ 가 필요하다.
