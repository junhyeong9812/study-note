# js/syntax/52 — `switch`·라벨·흐름 제어 세부: 「`case` 는 `===` 로 견주고, 한 번 들어가면 `break` 를 만날 때까지 아래로 흐른다 — `default` 는 자리가 아니라 『다 떨어진 뒤』 의 입구다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 판별식 여덟 개(`1` · `'1'` · `NaN` · `-0` · `0` · 객체 · `null` · `undefined`) × `case` 값 여덟 개 = **64칸**마다 「그 `case` 가 골라지나」 를 찍고, 같은 칸을 **`Object.is` · SameValueZero** 로 물은 답과 **스크립트가 견줘** 마지막 줄에 「**갈린 칸 N / 64**」 를 찍는다(동작 (1)).
> ★★ 보조로 **① 로그 심기**(`case` 식이 **언제·몇 개** 평가되나 · 몸통이 어떤 순서로 도나 — 동작 (2)) · **④ 예외의 이름 + 문구**(`let` 중복 · TDZ · 없는 라벨 — 동작 (3)·(4)) · **판 대조기**(node 18 · node 20 · Chrome 151 — 동작 (5))를 쓴다.
> ★★ **`switch` 가 `===` 를 쓴다는 것 자체는 [33번](../33-equality-three-kinds/2-summary.md)이 이미 쟀다**(서명 `nynynnny` — 짝 여덟 개를 `case b:` 한 칸짜리 `switch` 로). **그 서명을 다시 재지 않는다.** 이 문서가 더한 것은 **여러 `case` 가 줄지어 있을 때 어느 것에 들어가나**(순서가 답을 바꾸는 `-0`) · 64칸 전수 · 흐름(fallthrough · `default` 의 자리 · 평가 순서) · 스코프 · 라벨이다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — The switch Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-switch-statement) — `CaseClauseIsSelected` 「**Let exprRef be ? Evaluation of the Expression of C** … **Return IsStrictlyEqual(input, clauseSelector)**」 · note 「This operation does not execute C's StatementList」 · `CaseBlockEvaluation` — `default` 가 있는 꼴은 **앞 `CaseClauses` → 뒤 `CaseClauses` 를 차례로 시험**하고, 둘 다 안 걸리면 **`DefaultClause` 를 평가한 뒤** 「**NOTE: The following is another complete iteration of the second CaseClauses**」 로 뒤쪽 몸통을 **시험 없이** 돈다 · Early Errors — 「**It is a Syntax Error if the LexicallyDeclaredNames of CaseBlock contains any duplicate entries**, unless the host is a web browser or otherwise supports Block-Level Function Declarations Web Legacy Compatibility Semantics」(비엄격 + **함수 선언끼리만** 예외) · 「**LexicallyDeclaredNames … also occurs in the VarDeclaredNames**」 도 Syntax Error
> - [ECMA-262 — The continue Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-continue-statement) — 「**not nested, directly or indirectly (but not crossing function or static initialization block boundaries), within an IterationStatement**」 이면 Syntax Error
> - [ECMA-262 — Labelled Statements](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-labelled-statements) — `LabelledItem : FunctionDeclaration` 은 Syntax Error — 「**unless that source text is non-strict code and the host is a web browser or otherwise supports Labelled Function Declarations**」(Annex B.3.1) · `ContainsDuplicateLabels` · `ContainsUndefinedBreakTarget` · `ContainsUndefinedContinueTarget`
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML** 에서 읽었다(연산 이름과 짧은 인용만 싣는다).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1(판별 블록). ★★★ **네 탐침 모두 세 판(node 18 · node 20 · Chrome 151)이 한 글자도 같았다**(동작 (5)의 대조기 `8 / 8`) — 그래서 블록은 node 20 판 하나씩만 싣는다(규칙 10). **예외 문구까지 같았다** — ★ 문구는 판에 매이는 칸이라 **근거로는 예외의 종류(`SyntaxError`/`ReferenceError`)와 「컴파일 때냐 실행 때냐」 만** 쓴다(규칙 27).
> ★★ **이 주제는 시간·주소·순서가 흔들리는 칸이 없다** — 성능은 **재지 않았다**(아래 창 표).
>
> **버전** — `switch`·라벨 `break`/`continue` 는 **ES3**, `let`/`const` 와 그 TDZ 는 **ES2015** · 세 판 다 있다. 이 주제에서 판이 갈린 문법은 **없다.**
>
> **★★ 층 — 이 문서의 결론이 기대는 세 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★★ **ECMA-262 본문** | `case` 는 `IsStrictlyEqual` · `case` 식은 **골라질 때까지만** 평가 · fallthrough · `default` 의 순서 · 한 `CaseBlock` = 한 스코프 · 라벨의 Early Errors | 동작 (1)\~(4) |
> | ★★ **Annex B(웹 호환 — 호스트가 지원하면)** | 비엄격 코드에서 **`case` 사이의 같은 이름 함수 선언** 허용 · **라벨 붙은 함수 선언** 허용 | 동작 (3)의 `h` 두 줄 · 동작 (4)의 `lbl:` 두 줄 |
> | ★ **엔진(V8 판)** | 예외 **문구** — 이 세 판은 같았다 | 동작 (5) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체의 도구) | 64칸 × 「골라지나」 — 기준 두 자(`Object.is` · SameValueZero)와 **스크립트가 견준** 「갈린 칸 N / 64」(동작 (1)) |
> | ★★★ **「창을 바꿔 물었다」**(제5의 상태) | 「`case` 가 **무슨 비교**를 쓰나」 는 직접 볼 창이 없다(`IsStrictlyEqual` 에 끼어들 훅이 없다). 그래서 **「어느 몸통이 돌았나」 를 세고, 같은 칸을 알려진 자로 물은 답과 겹쳐 보는** 것으로 물었다. ★ 바꾼 창이 못 보는 것 — **`==`·`===` 처럼 64칸에서 답이 같은 두 자**는 이 격자로 못 가른다(그래서 판별식에 `'1'`·`null`/`undefined` 짝을 넣어 `==` 와는 갈리게 했다 — `'1'`·`1` 칸이 `.`) |
> | ★★ **① 로그 심기** | `case` 식에 부작용(`test(name, v)`)을 심어 **평가 순서·개수**와 **몸통 순서**를 한 줄로(동작 (2)) |
> | ★★ **④ 예외의 이름 + 문구** | `new Function` 으로 **컴파일 때(`SyntaxError`)** 와 **실행 때(`ReferenceError`)** 를 갈라 찍는다(동작 (3)·(4)) |
> | ★ **판 대조기** | 네 탐침 × (node 18 · Chrome 151) 대 node 20 — `8 / 8`(동작 (5)) |
> | ★ **부적용 — 성능** | V8 에는 `--switch-table-min-cases`(「Smi 정수 `case` 가 몇 개 이상이면 점프 테이블」) 같은 선택지가 **있다**(`node --v8-options` 에서 봤다). **이 문서는 재지 않았다** — 「`switch` 가 `if` 사슬보다 빠르다」 는 **한 줄도 쓰지 않는다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · ★ 예외 **문구**(이 세 판은 같았지만 판에 매인다 — 규칙 27) | 동작 (1)의 64칸과 요약 줄 · 동작 (2)의 로그 줄 전부 · 동작 (3)·(4)의 **예외 종류**와 「compile / run」 · 대조기 `8 / 8` — **재대조 동일** |
>
> **선행** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(직접 선행 — ★★★ **이미 쟀다**: `finally` 안의 `break`/`continue` 가 **던져지던 예외를 삼킨다**(`for: try throw; finally break → "after loop"`) · **라벨 블록에서 `finally { break out; }` 이 `return "T"` 를 지운다**(`label: try return; finally break out → "after block"`) — 거기 동작 (2). ★ 이 문서는 **그 조합을 다시 재지 않는다** — 라벨과 `break` 의 **기본 동작**만 잰다) ·
> [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md)(★★★ `switch` = `===` 의 서명 `nynynnny` · 「`case NaN:` 은 절대 안 걸린다」) ·
> [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md)(TDZ 의 정본) · [02 — 강제 변환과 `==`](../02-coercion-and-loose-equality/2-summary.md)(`'1' == 1` 이 참인 이유).
>
> ★★ **교차 갈래** — [Go 15 — `switch`·타입 스위치·`fallthrough`·라벨·`goto`](../../../go/syntax/15-switch-type-switch-fallthrough-labels-and-goto/2-summary.md)(★★★ **기본은 안 흘러내리고**, `fallthrough` 라고 적어야 내려가며 **다음 `case` 의 조건을 안 본다** — 거기 동작 (1)) · [Java 21 — `switch` 문과 `switch` 식](../../../java/syntax/21-switch-statement-and-expression/2-summary.md)(옛 `case 1:` 은 JS 와 같이 흘러내리고, 화살표 `case 1 ->` 는 안 흘러내린다 · `-Xlint:fallthrough` 로 경고를 받는다) · [Python 39 — `match` 문](../../../python/syntax/39-match-statement/2-summary.md)(흘러내림 자체가 없다).

```text
===== ./js48b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  tz 2023c  unicode 15.1  cldr 44.1
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  tz 2025b  unicode 16.0  cldr 47.0
Google Chrome 151.0.7922.173
```

## 한눈에 — 쉽게 말하면

**`switch` 는 「번호표를 든 손님과 창구 줄」 이다. 손님(판별식)의 번호표를 창구마다(`case`) 들고 가서 글자 그대로 같은지(`===`)만 본다. 맞는 창구를 찾으면 그 창구부터 칸막이(`break`)가 나올 때까지 아래 창구들을 전부 지나간다. 안내 데스크(`default`)는 줄 어디에 있든 모든 창구가 아니라고 한 뒤에야 문을 연다 — 그리고 문을 열면 그 아래 창구로 이어서 흘러간다.**

- ★★★ **`NaN` 은 어느 창구에도 안 들어간다** — `NaN === NaN` 이 거짓이다(동작 (1) — `NaN → default`).
- ★★★ **`-0` 은 `case 0` 에 들어간다** — `-0 === 0` 이 참이고, 줄에서 **먼저 나온 창구**가 이긴다(동작 (1) — `-0 → 0`, `Object.is` 라면 `-0`).
- ★★ **창구 번호는 차례로, 맞을 때까지만 읽는다** — 맞는 뒤쪽 `case` 식은 **평가조차 안 된다**(동작 (2)).
- ★★ **`switch` 의 `{ }` 전체가 방 하나다** — `case` 마다 `let a` 를 쓰면 `SyntaxError`, 다른 `case` 의 `let` 을 읽으면 TDZ(동작 (3)).
- ★★ **라벨은 문에 붙인 이름표** — `break 이름` 은 그 문 **밖으로**, `continue 이름` 은 그 **루프의 다음 바퀴**로. 루프가 아닌 블록에도 `break` 는 되지만 `continue` 는 안 된다(동작 (4)).

```text
   switch (x)   ─ 판별식은 한 번만 평가
      │
      ▼   case 식을 소스 순서대로 하나씩 평가 → IsStrictlyEqual(x, 값)
   ┌─────────────┐   아니오   ┌─────────────┐   아니오   ┌─────────────┐   아니오
   │ case A      │──────────▶│ case B      │──────────▶│ case C      │──────────▶  (전부 아니오)
   └──────┬──────┘           └──────┬──────┘           └──────┬──────┘                │
          │ 예                      │ 예                      │ 예                     ▼
          ▼                         ▼                         ▼               default 몸통부터
     몸통 A ──▶ (default 몸통) ──▶ 몸통 B ──▶ 몸통 C ──▶ 끝      ← 소스 순서로 흘러내림 · break 에서 멈춤
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 번호표 | 판별식 — **한 번만** 평가 | 동작 (2)의 `[4]` |
| 창구마다 글자 그대로 대조 | `CaseClauseIsSelected` → `IsStrictlyEqual` | 동작 (1) |
| 창구 번호를 차례로 읽기 | `case` 식은 **소스 순서 · 골라질 때까지만** 평가 | 동작 (2)의 `test …` |
| 칸막이 | `break` — 없으면 아래 몸통으로 계속(fallthrough) | 동작 (2)의 `[1]` 대 `[2]` |
| 안내 데스크 | `default` — **자리와 무관하게 마지막 수단**, 열면 아래로 흐른다 | 동작 (2)의 `x = 9` |
| 창구 줄 전체가 방 하나 | `CaseBlock` 하나 = 렉시컬 스코프 하나 | 동작 (3) |
| 문에 붙인 이름표 | 라벨 — `break 이름` · `continue 이름` | 동작 (4) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`case NaN:` 으로 잘못된 입력을 걸렀는데 한 번도 안 걸린다**」,
「**`break` 를 빠뜨려 다음 `case` 의 처리까지 돌았다**」,
「**`default` 를 중간에 두었더니 뒤쪽 `case` 몸통까지 실행됐다**」,
「**두 `case` 에서 같은 이름으로 `let` 을 썼더니 파일 전체가 `SyntaxError` 로 안 뜬다**」,
「**`forEach` 콜백 안에서 `break outer` 를 썼더니 컴파일이 안 된다**」가 그것이다(동작 (1)\~(4)).

> **fallthrough(흘러내림)** — 골라진 `case` 의 몸통이 끝나도 `break` 가 없으면 **아래 `case` 의 몸통을 시험 없이 이어서** 도는 것.\
> 예: `case 1: a(); case 2: b();` 에서 `x = 1` 이면 `a` 와 `b` 가 둘 다 돈다.

## 이 주제가 답하려는 질문

1. **`case` 는 무엇으로 견주나 — 그리고 `case` 가 여럿 줄지어 있으면 어느 것에 들어가나** — `NaN` · `-0` · 같은 모양의 객체 · `null`/`undefined` 에서?
2. **`case` 식은 언제 · 몇 개 평가되고, 몸통은 어떤 순서로 도나** — `break` 가 없을 때 · `default` 가 중간에 있을 때?
3. **`switch` 블록과 라벨은 이름·흐름의 경계를 어디에 긋나** — `let` 은 어느 스코프에 사나 · `break`/`continue` 는 어디까지 뛸 수 있나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 64칸 격자 — `switch` 가 고른 것 대 `Object.is` · SameValueZero

**언제 쓰나** — `switch (x)` 에 들어올 수 있는 값에 `NaN`·`-0`·객체가 섞일 때.
★★ `[1]` 은 **`case` 아홉 개가 줄지어 있는** 진짜 `switch` 하나 — 판별식마다 **어느 `case` 에 들어가나**, 같은 목록을 `Object.is`·SameValueZero 로 **앞에서부터 찾으면** 어느 것을 고르나. `[2]` 는 **`case` 하나짜리** `switch` 로 판별식 × `case` 값 64칸을 전부 묻는다. 객체는 `objA`·`objB` 가 **모양만 같은 두 객체**다.

```js
// js48b-52a-case-grid.js
// js48b-52a-case-grid.js
// [1] One switch with nine case clauses and a default. For each discriminant: which clause does the switch enter,
//     and which clause would a search with Object.is (and with SameValueZero) pick from the same list?
// [2] Every discriminant against every case value, one clause at a time (a 8 x 8 matrix):
//     is the clause selected? The last lines count the cells where the switch answer differs from Object.is / SameValueZero.
const objA = { a: 1 };
const objB = { a: 1 };
const names = ["1", "'1'", "NaN", "-0", "0", "objA {a:1}", "null", "undefined"];
const values = [1, "1", NaN, -0, 0, objA, null, undefined];
const caseNames = ["1", "'1'", "NaN", "0", "-0", "objB {a:1}", "null", "undefined", "objA"];
const caseValues = [1, "1", NaN, 0, -0, objB, null, undefined, objA];
function enter(x) {
  switch (x) {
    case caseValues[0]: return caseNames[0];
    case caseValues[1]: return caseNames[1];
    case caseValues[2]: return caseNames[2];
    case caseValues[3]: return caseNames[3];
    case caseValues[4]: return caseNames[4];
    case caseValues[5]: return caseNames[5];
    case caseValues[6]: return caseNames[6];
    case caseValues[7]: return caseNames[7];
    case caseValues[8]: return caseNames[8];
    default: return "default";
  }
}
const sameValueZero = (a, b) => [a].includes(b);
const pick = (x, eq) => {
  const i = caseValues.findIndex((c) => eq(x, c));
  return i === -1 ? "default" : caseNames[i];
};
console.log("[1] case list in source order: " + caseNames.join(" | ") + " | default");
console.log("  " + "switch (x)".padEnd(14) + "switch enters".padEnd(16) + "Object.is picks".padEnd(18) + "SameValueZero picks");
for (let i = 0; i < values.length; i++) {
  console.log("  " + names[i].padEnd(14) + enter(values[i]).padEnd(16) + pick(values[i], Object.is).padEnd(18) + pick(values[i], sameValueZero));
}
console.log("");
console.log("[2] one clause at a time: y = the clause is selected (rows: discriminant, columns: case value)");
const colValues = values.slice();
colValues[5] = objB;
const colNames = names.slice();
colNames[5] = "objB";
const selected = (x, c) => { switch (x) { case c: return true; default: return false; } };
console.log("  " + "".padEnd(12) + colNames.map((n) => n.padEnd(10)).join("").trimEnd());
let cells = 0, vsIs = 0, vsZero = 0;
const diffIs = [];
for (let i = 0; i < values.length; i++) {
  let line = "  " + names[i].padEnd(12);
  for (let j = 0; j < colValues.length; j++) {
    const s = selected(values[i], colValues[j]);
    cells += 1;
    if (s !== Object.is(values[i], colValues[j])) { vsIs += 1; diffIs.push(names[i] + " / " + colNames[j]); }
    if (s !== sameValueZero(values[i], colValues[j])) vsZero += 1;
    line += (s ? "y" : ".").padEnd(10);
  }
  console.log(line.trimEnd());
}
console.log("  cells that differ from Object.is: " + diffIs.join(" · "));
console.log("cells where switch differs from Object.is: " + vsIs + " / " + cells + " · from SameValueZero: " + vsZero + " / " + cells);
```

```text
===== node20 js48b-52a-case-grid.js (exit=0) =====
[1] case list in source order: 1 | '1' | NaN | 0 | -0 | objB {a:1} | null | undefined | objA | default
  switch (x)    switch enters   Object.is picks   SameValueZero picks
  1             1               1                 1
  '1'           '1'             '1'               '1'
  NaN           default         NaN               NaN
  -0            0               -0                0
  0             0               0                 0
  objA {a:1}    objA            objA              objA
  null          null            null              null
  undefined     undefined       undefined         undefined

[2] one clause at a time: y = the clause is selected (rows: discriminant, columns: case value)
              1         '1'       NaN       -0        0         objB      null      undefined
  1           y         .         .         .         .         .         .         .
  '1'         .         y         .         .         .         .         .         .
  NaN         .         .         .         .         .         .         .         .
  -0          .         .         .         y         y         .         .         .
  0           .         .         .         y         y         .         .         .
  objA {a:1}  .         .         .         .         .         .         .         .
  null        .         .         .         .         .         .         y         .
  undefined   .         .         .         .         .         .         .         y
  cells that differ from Object.is: NaN / NaN · -0 / 0 · 0 / -0
cells where switch differs from Object.is: 3 / 64 · from SameValueZero: 1 / 64
```

```text
   [1] 줄지은 case 에서 -0 이 들어가는 곳
       case 목록:   1 │ '1' │ NaN │ 0 │ -0 │ objB │ null │ undefined │ objA │ default
                                  ▲    ▲
       switch (-0)  ─ === ─────────┘    │     -0 === 0  참 → 먼저 나온 「0」 에서 멈춘다
       Object.is    ─ SameValue ────────┘     Object.is(-0, 0) 거짓 → 「-0」 까지 간다

       switch (NaN) ─ === ─ 전부 거짓 ──────────────────────────────────────▶ default
       Object.is    ─ NaN 칸에서 참

   [2] 64칸에서 Object.is 와 갈린 칸 = NaN/NaN · -0/0 · 0/-0          → 3 / 64
                 SameValueZero 와 갈린 칸 = NaN/NaN                   → 1 / 64
```

- ★★★ **요약 줄 — `cells where switch differs from Object.is: 3 / 64 · from SameValueZero: 1 / 64`.** 갈린 칸이 **정확히 `NaN`/`NaN` · `-0`/`0` · `0`/`-0`** 셋이다(`cells that differ from Object.is:` 줄). 나머지 61칸은 세 자가 같은 답이다 — 33번의 「`NaN` 과 `-0` 두 행만 가르면 된다」 를 **`case` 자리에서 64칸으로** 다시 본 것이다.
- ★★★ **`NaN → default`** — `[2]` 의 `NaN` 행이 **여덟 칸 전부 `.`**(자기 자신 `NaN` 칸까지). `case NaN:` 은 **어떤 판별식에도** 안 걸린다(명세 — `IsStrictlyEqual`).
- ★★★ **`-0 → 0`** — `[1]` 에서 `switch` 는 **`0`** 에 들어갔고 `Object.is` 는 **`-0`** 을 골랐다. ★★ **SameValueZero 도 `0`** 이다 — 여기서는 `switch` 와 같다. 순서가 답을 정한다 — 목록에서 `0` 이 `-0` 보다 **앞에** 있기 때문이다. `[2]` 에서 `-0`·`0` 두 행 두 열이 **네 칸 다 `y`** 인 것이 그 이유다.
- ★★ **객체는 정체성** — `objA` 판별식은 **모양이 같은 `objB` 칸을 지나쳐** 맨 뒤의 `objA` 에 들어갔다. `[2]` 의 `objA {a:1}` 행은 **전부 `.`**(열에 `objA` 가 없고 `objB` 뿐이다).
- ★★ **강제 변환은 없다** — `'1'` 은 `case 1` 에 **안** 들어가고(`[2]` 의 `'1'`/`1` 칸 `.`), `null` 은 `case undefined` 에 **안** 들어간다. `==` 였다면 두 칸 다 `y` 다(02번).

### (2) ★★★ `case` 식의 평가 순서와 몸통의 순서 — `default` 가 중간에 있을 때

**언제 쓰나** — `break` 를 일부러 빼거나(여러 값에 같은 처리), `default` 를 목록 중간에 둘 때 · `case` 식에 함수 호출을 쓸 때.
★★ 두 `switch` 모두 소스 순서가 **`case A(1)` · `default` · `case B(2)` · `case C(3)`** 이다. `test(name, v)` 가 **평가될 때마다** `test <name>` 을 남긴다.

```js
// js48b-52b-clause-order.js
// js48b-52b-clause-order.js
// The order in which a switch tests case expressions and runs clause bodies.
// test(name, v) logs "test <name>" and returns v, so every evaluated case expression leaves a trace.
// Source order of the clauses in both switches: case A (1) · default · case B (2) · case C (3).
let log;
const test = (name, v) => { log.push("test " + name); return v; };
function noBreak(x) {
  log = [];
  switch (x) {
    case test("A", 1): log.push("body A");
    default: log.push("body default");
    case test("B", 2): log.push("body B");
    case test("C", 3): log.push("body C");
  }
  return log.join(" > ");
}
function withBreak(x) {
  log = [];
  switch (x) {
    case test("A", 1): log.push("body A"); break;
    default: log.push("body default"); break;
    case test("B", 2): log.push("body B"); break;
    case test("C", 3): log.push("body C"); break;
  }
  return log.join(" > ");
}
console.log("[1] no break anywhere");
for (const x of [1, 2, 3, 9]) console.log("  x = " + x + "   " + noBreak(x));
console.log("[2] break at the end of every clause");
for (const x of [1, 2, 3, 9]) console.log("  x = " + x + "   " + withBreak(x));
console.log("[3] two clauses with the same value");
function twice(x) {
  log = [];
  switch (x) {
    case test("first 1", 1): log.push("body first"); break;
    case test("second 1", 1): log.push("body second"); break;
  }
  return log.join(" > ");
}
console.log("  x = 1   " + twice(1));
console.log("[4] where the discriminant is evaluated");
function once() {
  log = [];
  switch (test("discriminant", 3)) {
    case test("A", 1): break;
    case test("B", 2): break;
    case test("C", 3): log.push("body C"); break;
  }
  return log.join(" > ");
}
console.log("  " + once());
```

```text
===== node20 js48b-52b-clause-order.js (exit=0) =====
[1] no break anywhere
  x = 1   test A > body A > body default > body B > body C
  x = 2   test A > test B > body B > body C
  x = 3   test A > test B > test C > body C
  x = 9   test A > test B > test C > body default > body B > body C
[2] break at the end of every clause
  x = 1   test A > body A
  x = 2   test A > test B > body B
  x = 3   test A > test B > test C > body C
  x = 9   test A > test B > test C > body default
[3] two clauses with the same value
  x = 1   test first 1 > body first
[4] where the discriminant is evaluated
  test discriminant > test A > test B > test C > body C
```

```text
   소스 순서:   case A(1)  ·  default  ·  case B(2)  ·  case C(3)

   x = 9, break 없음
     시험:   test A ✗ ──────────────▶ test B ✗ ──▶ test C ✗        ← default 를 건너뛰고 뒤쪽까지 먼저 다 본다
     몸통:                body default ──▶ body B ──▶ body C        ← 그다음 default 부터, 아래로 흘러내린다(시험 없이)

   x = 1, break 없음
     시험:   test A ✓                                               ← 여기서 시험 끝. B·C 의 case 식은 평가 안 됨
     몸통:   body A ──▶ body default ──▶ body B ──▶ body C          ← default 도 흘러내림 길 위의 몸통 하나일 뿐
```

- ★★★ **`x = 9`(아무 `case` 도 안 맞음) — `test A > test B > test C > body default > body B > body C`.** `default` 가 A 와 B 사이에 있어도 **B·C 를 먼저 시험**하고, 전부 아니어야 `default` 몸통이 돈다. 그리고 `break` 가 없으면 **`default` 아래의 B·C 몸통이 시험 없이** 이어서 돈다 — 명세 `CaseBlockEvaluation` 의 「**another complete iteration of the second CaseClauses**」 가 그 줄이다.
- ★★★ **`x = 1` — `test A > body A > body default > body B > body C`.** 시험은 **A 하나에서 끝난다** — B·C 의 `case` 식은 **평가조차 안 됐다**(`test B` 가 없다). 그리고 흘러내림은 **소스 순서**라 `default` 몸통도 그 길 위에 있다.
- ★★ **`x = 2`·`x = 3`** — 시험이 A 부터 순서대로 가서 맞는 곳에서 멈추고, 몸통은 그 자리부터 아래로. **`default` 는 B 보다 위라** 흘러내림 길에 없다(`x = 2 → body B > body C`).
- ★★ **`[2]` `break` 를 다 달면** 몸통이 **하나만** 돈다 — 시험 순서는 `[1]` 과 **글자까지 같다**(`x = 9 → test A > test B > test C > body default`).
- ★★ **`[3]` 같은 값의 `case` 가 둘이어도 에러가 없고** 첫째만 골라진다 — 둘째 `case` 식은 평가도 안 된다(`test first 1 > body first`). ★ Go(gc)는 상수 `case` 가 겹치면 **컴파일 에러**다(Go 15번 — 거기서도 **명세 보장이 아니라 구현**이라 적었다) — JS 는 `case` 식이 **아무 식**이나 될 수 있어 겹침을 미리 볼 수 없다.
- ★★ **`[4]` 판별식은 맨 먼저 한 번** — `test discriminant > test A > test B > test C > body C`.

### (3) ★★ `switch` 블록 하나가 스코프 하나 — `let` 중복 · TDZ · 함수 선언

**언제 쓰나** — `case` 마다 임시 변수를 두고 싶을 때.
★ 조각마다 **`new Function` 으로 컴파일한 뒤 부른다** — `compile:` 은 **컴파일 때 막힌 것(`SyntaxError`)**, `run:` 은 **실행해서 얻은 값 또는 실행 중 예외**다. `new Function` 의 몸통은 **비엄격**이다(`'use strict'` 를 붙인 줄만 엄격).

```js
// js48b-52c-switch-scope.js
// js48b-52c-switch-scope.js
// Declarations inside the clauses of a switch. Each snippet is compiled with new Function and then called,
// so a SyntaxError (at compile time) and an error thrown while running are told apart.
const run = (label, body) => {
  let f;
  try { f = new Function(body); } catch (e) { console.log("  " + label.padEnd(44) + "compile: " + e.constructor.name + " 「" + e.message + "」"); return; }
  try { console.log("  " + label.padEnd(44) + "run: " + String(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + "run: " + e.constructor.name + " 「" + e.message + "」"); }
};
console.log("[1] let with the same name in two clauses");
run("case 0: let a · case 1: let a", "switch (1) { case 0: let a = 'zero'; return a; case 1: let a = 'one'; return a; }");
run("the same, each clause in braces", "switch (1) { case 0: { let a = 'zero'; return a; } case 1: { let a = 'one'; return a; } }");
run("case 0: var a · case 1: var a", "switch (1) { case 0: var a = 'zero'; return a; case 1: var a = 'one'; return a; }");
run("case 0: let a · case 1: var a", "switch (1) { case 0: let a = 'zero'; return a; case 1: var a = 'one'; return a; }");
console.log("[2] a let declared in one clause, used in another");
run("case 0: let a · case 1: return a", "switch (1) { case 0: let a = 'zero'; case 1: return a; }");
run("case 0: let a · case 1: a = 'one'", "switch (1) { case 0: let a = 'zero'; case 1: a = 'one'; return a; }");
run("case 0: let a · case 1: typeof a", "switch (1) { case 0: let a = 'zero'; case 1: return typeof a; }");
run("case 0: let a · x = 0 falls into case 1", "switch (0) { case 0: let a = 'zero'; case 1: return a; }");
run("case 0: var a · case 1: return a", "switch (1) { case 0: var a = 'zero'; case 1: return a; }");
console.log("[3] const and function declarations");
run("case 0: const c · case 1: const c", "switch (1) { case 0: const c = 0; break; case 1: const c = 1; return c; }");
run("case 0: function g · case 1: g()", "switch (1) { case 0: function g() { return 'g'; } case 1: return g(); }");
run("the same, 'use strict'", "'use strict'; switch (1) { case 0: function g() { return 'g'; } case 1: return g(); }");
run("case 0: function h · case 1: function h", "switch (1) { case 0: function h() { return 0; } case 1: function h() { return 1; } } return h();");
run("the same, 'use strict'", "'use strict'; switch (1) { case 0: function h() { return 0; } case 1: function h() { return 1; } }");
run("case 0: class K · case 1: new K", "switch (1) { case 0: class K {} case 1: return typeof new K(); }");
```

```text
===== node20 js48b-52c-switch-scope.js (exit=0) =====
[1] let with the same name in two clauses
  case 0: let a · case 1: let a               compile: SyntaxError 「Identifier 'a' has already been declared」
  the same, each clause in braces             run: one
  case 0: var a · case 1: var a               run: one
  case 0: let a · case 1: var a               compile: SyntaxError 「Identifier 'a' has already been declared」
[2] a let declared in one clause, used in another
  case 0: let a · case 1: return a            run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · case 1: a = 'one'           run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · case 1: typeof a            run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · x = 0 falls into case 1     run: zero
  case 0: var a · case 1: return a            run: undefined
[3] const and function declarations
  case 0: const c · case 1: const c           compile: SyntaxError 「Identifier 'c' has already been declared」
  case 0: function g · case 1: g()            run: g
  the same, 'use strict'                      run: g
  case 0: function h · case 1: function h     run: 1
  the same, 'use strict'                      compile: SyntaxError 「Identifier 'h' has already been declared」
  case 0: class K · case 1: new K             run: ReferenceError 「Cannot access 'K' before initialization」
```

```text
   switch (1) {                         ← CaseBlock 하나 = 렉시컬 스코프 하나
     case 0:  let a = 'zero';           ┐
     case 1:  return a;                 ┘  같은 방의 a — case 0 을 건너뛰었으니 초기화 전(TDZ)
   }

   switch (1) {
     case 0: { let a = 'zero'; … }      ← 중괄호마다 방이 따로
     case 1: { let a = 'one';  … }
   }
```

- ★★★ **`case 0: let a · case 1: let a` → `compile: SyntaxError 「Identifier 'a' has already been declared」`** — 두 `case` 가 **같은 스코프**라 한 스코프에 `a` 가 둘이다. 부르기도 전에 **컴파일에서** 막힌다(명세 Early Error — `LexicallyDeclaredNames` 중복). `let`·`var` 섞어도 같다(`VarDeclaredNames` 와 겹침).
- ★★★ **TDZ — `case 1` 에서 `a` 를 읽고·쓰고·`typeof` 해도 전부 `ReferenceError 「Cannot access 'a' before initialization」`.** `x = 1` 이 `case 0` 을 **건너뛰어** `let a` 문이 한 번도 안 돌았기 때문이다. ★ **`typeof` 도 던진다** — TDZ 는 「이름이 없다」 가 아니라 「있는데 아직 못 쓴다」 이다. 같은 코드를 **`x = 0` 으로 흘러내리면 `zero`** — 초기화 문을 지나갔기 때문이다. **같은 소스가 들어오는 값에 따라** 던지기도 하고 안 던지기도 한다.
- ★★ **`var` 는 `undefined`** — `var` 는 함수 스코프에 올라가 있고 TDZ 가 없다.
- ★★ **고치는 법은 중괄호** — `the same, each clause in braces → run: one`.
- ★★ **함수 선언은 블록 맨 앞으로 끌어올려진다** — `case 0` 을 건너뛰어도 `g()` 가 `g` 를 돌려준다(엄격·비엄격 둘 다). **`class` 는 아니다** — `class K` 는 `let` 처럼 TDZ(`ReferenceError 「Cannot access 'K' before initialization」`).
- ★★ **같은 이름 함수 선언 둘 — 비엄격은 `run: 1`(뒤의 것), 엄격은 `SyntaxError`.** 명세 본문은 중복을 금지하고, **Annex B(웹 호환)** 가 「비엄격 + 함수 선언끼리만」 을 풀어 준다. node 도 V8 이라 같은 예외를 탔다 — **층이 ECMA-262 본문이 아니라 Annex B** 인 칸이다.

### (4) ★★ 라벨 — 중첩 루프 탈출 · 루프 아닌 블록 · 컴파일에서 막히는 자리

**언제 쓰나** — 이중 루프에서 **바깥까지** 끝내거나 바깥의 다음 바퀴로 가고 싶을 때 · 조기 탈출이 필요한 블록.

```js
// js48b-52d-labels.js
// js48b-52d-labels.js
// Labels with break and continue. [1]-[3] run; [4] compiles snippets with new Function and prints what happens.
const out = [];
console.log("[1] nested loops, break and continue with and without the label");
outer: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (j === 1) continue outer;
    out.push(i + "" + j);
  }
}
console.log("  continue outer at j === 1   " + out.join(" "));
out.length = 0;
outer2: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (i === 1 && j === 1) break outer2;
    out.push(i + "" + j);
  }
}
console.log("  break outer2 at i,j === 1,1 " + out.join(" "));
out.length = 0;
for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (i === 1 && j === 1) break;
    out.push(i + "" + j);
  }
}
console.log("  plain break at i,j === 1,1  " + out.join(" "));

console.log("[2] a label on a block that is not a loop");
out.length = 0;
block: {
  out.push("a");
  if (out.length === 1) break block;
  out.push("b");
}
out.push("after");
console.log("  " + out.join(" > "));

console.log("[3] break and continue inside a switch that sits in a loop");
out.length = 0;
for (let i = 0; i < 4; i++) {
  switch (i) {
    case 1: out.push("case 1 break"); break;
    case 2: out.push("case 2 continue"); continue;
    default: out.push("default " + i);
  }
  out.push("end of body " + i);
}
console.log("  " + out.join(" > "));

console.log("[4] compiled with new Function");
const compile = (label, body) => {
  let r;
  try { r = "compiles, returns " + String(new Function(body)()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(40) + r);
};
compile("break nope   (no such label)", "for (;;) { break nope; }");
compile("blk: { continue blk; }", "blk: { continue blk; }");
compile("blk: { break blk; }", "blk: { break blk; } return 'ok';");
compile("break outside any loop or switch", "break;");
compile("continue in a switch, no loop", "switch (1) { case 1: continue; }");
compile("a: a: ;   (the same label twice)", "a: a: ;");
compile("break outer inside a callback", "outer: for (const x of [1]) { [1].forEach(() => { break outer; }); }");
compile("lbl: function f() {}", "lbl: function f() {} return typeof f;");
compile("'use strict'; lbl: function f() {}", "'use strict'; lbl: function f() {}");
```

```text
===== node20 js48b-52d-labels.js (exit=0) =====
[1] nested loops, break and continue with and without the label
  continue outer at j === 1   00 10 20
  break outer2 at i,j === 1,1 00 01 02 10
  plain break at i,j === 1,1  00 01 02 10 20 21 22
[2] a label on a block that is not a loop
  a > after
[3] break and continue inside a switch that sits in a loop
  default 0 > end of body 0 > case 1 break > end of body 1 > case 2 continue > default 3 > end of body 3
[4] compiled with new Function
  break nope   (no such label)            SyntaxError 「Undefined label 'nope'」
  blk: { continue blk; }                  SyntaxError 「Illegal continue statement: 'blk' does not denote an iteration statement」
  blk: { break blk; }                     compiles, returns ok
  break outside any loop or switch        SyntaxError 「Illegal break statement」
  continue in a switch, no loop           SyntaxError 「Illegal continue statement: no surrounding iteration statement」
  a: a: ;   (the same label twice)        SyntaxError 「Label 'a' has already been declared」
  break outer inside a callback           SyntaxError 「Undefined label 'outer'」
  lbl: function f() {}                    compiles, returns function
  'use strict'; lbl: function f() {}      SyntaxError 「In strict mode code, functions can only be declared at top level or inside a block.」
```

```text
   outer: for i ─┬─ for j ─┬─ continue outer ──▶ 바깥 루프의 다음 i (안쪽 루프의 나머지는 버림)
                 │         ├─ break outer    ──▶ 바깥 루프 밖으로
                 │         └─ break          ──▶ 안쪽 루프만 끝, 바깥은 계속
   block: { … break block; … }  ──▶ 블록 밖으로 (루프가 아니어도 된다)

   for (…) { switch (…) { case: break;    ──▶ switch 만 끝 → 루프 몸통의 다음 줄
                          case: continue; ──▶ switch 를 지나 루프의 다음 바퀴 (몸통의 나머지를 건너뜀)
   ── 함수 경계는 라벨이 못 넘는다: forEach(() => { break outer; }) 는 「없는 라벨」 ──
```

- ★★★ **`[1]` — `continue outer` 는 `00 10 20`, `break outer2` 는 `00 01 02 10`, 라벨 없는 `break` 는 `00 01 02 10 20 21 22`.** 라벨이 없으면 **안쪽 루프 하나만** 끝난다.
- ★★ **`[2]` 루프가 아닌 블록에도 `break 라벨` 이 된다** — `a > after`(`b` 를 건너뜀).
- ★★★ **`[3]` `switch` 안의 `break` 는 `switch` 만 끝낸다** — `case 1 break > end of body 1`. **`switch` 안의 `continue` 는 바깥 루프에 걸린다** — `case 2 continue` 뒤에 `end of body 2` 가 **없다.** `switch` 는 `break` 의 표적은 되지만 `continue` 의 표적은 못 된다.
- ★★★ **`[4]` 는 전부 컴파일 때 막힌다(`SyntaxError`)** — 부르기 전이다.
  - `break nope` → `「Undefined label 'nope'」` · **`forEach` 콜백 안의 `break outer` 도 같은 `「Undefined label 'outer'」`** — 명세가 라벨의 범위를 **함수 경계에서 끊는다**(`continue` 의 Early Error 문장 「**not crossing function … boundaries**」). 콜백 안에서는 바깥 라벨이 **없는 이름**이다.
  - `blk: { continue blk; }` → `「Illegal continue statement: 'blk' does not denote an iteration statement」` — **`continue` 는 루프 라벨만**.
  - 맨몸 `break;` → `「Illegal break statement」` · 루프 없는 `switch` 안의 `continue` → `「Illegal continue statement: no surrounding iteration statement」`.
  - `a: a: ;` → `「Label 'a' has already been declared」`.
- ★★ **라벨 붙은 함수 선언** — 비엄격은 `compiles, returns function`, 엄격은 `SyntaxError 「In strict mode code, functions can only be declared at top level or inside a block.」`. 명세 본문은 금지하고 **Annex B.3.1** 이 비엄격만 풀어 준다. ★★ **이 문구는 원인을 가리키지 않는다** — 문제는 「블록 밖」 이 아니라 「라벨이 붙었다」 이다. 근거로는 **`SyntaxError` 라는 종류와 엄격/비엄격의 갈림만** 쓴다(규칙 27).

### (5) ★ 세 판 대조 — 문구까지 같았다

**언제 쓰나** — 「이 에러 문구가 다른 엔진·판에서도 같나」 를 판단할 때.

```sh
# js48b-52e-three-runtimes.sh
#!/usr/bin/env bash
# Every probe of this topic (js48b-52[a-d]-*.js) on node18, node20 and Chrome 151: is the output the same as node20's, byte for byte?
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0; total=0
for f in js48b-52[a-d]-*.js; do
  b="$("$N20" "$f")" || exit 1
  a="$("$N18" "$f")" || exit 1
  w="$(./js48b-browser.sh "$f")" || exit 1
  [ "$a" = "$b" ] && r18=identical || r18=DIFFERS
  [ "$w" = "$b" ] && rw=identical || rw=DIFFERS
  for r in "$r18" "$rw"; do total=$((total + 1)); [ "$r" = identical ] && same=$((same + 1)); done
  printf '%-32s node18/node20 %-10s Chrome/node20 %s\n' "$f" "$r18" "$rw"
done
echo "comparisons identical to node20: $same / $total"
```

```text
===== ./js48b-52e-three-runtimes.sh (exit=0) =====
js48b-52a-case-grid.js           node18/node20 identical  Chrome/node20 identical
js48b-52b-clause-order.js        node18/node20 identical  Chrome/node20 identical
js48b-52c-switch-scope.js        node18/node20 identical  Chrome/node20 identical
js48b-52d-labels.js              node18/node20 identical  Chrome/node20 identical
comparisons identical to node20: 8 / 8
```

- ★★ **`comparisons identical to node20: 8 / 8`** — 격자·로그뿐 아니라 동작 (3)·(4)의 **예외 문구까지** 세 판이 한 글자도 같았다. ★ 이것은 **이 세 판(V8 10.2 · 11.3 · Chrome 151)의 관찰**이다 — 다른 엔진(SpiderMonkey·JavaScriptCore)의 문구는 **돌리지 않았다.** 문구는 명세가 정하지 않는다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 층 | 어디서 봤나 |
|---|---|---|---|
| `switch (e) { case v: … }` | `e` 를 **한 번** 평가 · `case` 식을 **순서대로, 골라질 때까지만** 평가해 `===` 로 견준다 | ECMA-262 | 동작 (1)·(2) |
| `break` 없는 `case` | 아래 몸통으로 **시험 없이** 흘러내린다 | ECMA-262 | 동작 (2) `[1]` |
| `default:` | **모든 `case` 가 아닌 뒤에** 들어간다 · 자리와 무관 · 열면 아래로 흐른다 | ECMA-262 | 동작 (2) `x = 9` |
| `case` 안의 `let`/`const`/`class` | `switch` 블록 **전체**가 한 스코프 — 중복은 컴파일 에러 · 건너뛴 초기화는 TDZ | ECMA-262 | 동작 (3) |
| `case 0: { let a … }` | 중괄호로 **따로** 스코프 | ECMA-262 | 동작 (3) |
| `이름: 문` | 라벨 — `break 이름`(아무 문) · `continue 이름`(루프만) · **함수 경계를 못 넘는다** | ECMA-262 | 동작 (4) |
| 라벨 붙은 함수 선언 · `case` 사이 같은 이름 함수 | **비엄격에서만** 허용 | ★ **Annex B** | 동작 (3)·(4) |

## 어디서 틀리나

### (1) ★★★ `case NaN:` 으로 `NaN` 을 거른다

**절대 안 걸린다** — 64칸의 `NaN` 행이 전부 `.`(동작 (1)). `switch (true) { case Number.isNaN(x): … }` 꼴이나 `switch` 앞의 `if (Number.isNaN(x))` 로 뺀다(33번과 같은 결론).

### (2) ★★ `-0` 과 `0` 을 `case` 로 가르려 한다

`-0 === 0` 이 참이라 **먼저 나온 쪽**이 이긴다(`-0 → 0`). 가르려면 `Object.is(x, -0)` 을 `if` 로.

### (3) ★★ 같은 모양의 객체 · 문자열 `'1'` 이 `case` 에 걸릴 것으로 기대한다

`===` 는 **정체성**이고 **강제 변환이 없다** — `objB` 칸 · `'1'`/`1` 칸이 `.`(동작 (1)).

### (4) ★★★ `break` 를 빠뜨린다 · `default` 를 중간에 두고 거기서 끝난다고 믿는다

흘러내림은 **소스 순서**다 — `default` 가 중간이면 **그 아래 `case` 몸통까지** 돈다(`x = 9 → body default > body B > body C`). ★ 두 node 판은 이 탐침을 돌리며 **표준 오류에 한 줄도 안 냈다**(`capture.sh` 는 표준 오류가 나오면 멈춘다 — 경고 창구가 없다). Java 는 `-Xlint:fallthrough` 로 경고를 받는다(Java 21번).

### (5) ★★ `case` 식에 부작용이 있는 호출을 쓰고 「다 한 번씩 돈다」 고 믿는다

**골라진 `case` 에서 멈추고 뒤는 평가도 안 된다**(동작 (2) `x = 1 → test A` 뿐). 값마다 평가 개수가 다르다.

### (6) ★★★ `case` 마다 `let` 을 쓴다

`SyntaxError`(컴파일) 또는 TDZ `ReferenceError`(실행 — **들어온 값에 따라서만**) — 동작 (3). 중괄호를 쳐라.

### (7) ★★ `forEach` 콜백 안에서 `break`/`break outer` 로 바깥 루프를 끊으려 한다

라벨은 **함수 경계를 못 넘는다** — `「Undefined label 'outer'」`(동작 (4)). `for…of` 로 바꾸거나 `some`/`find` 로 조기 종료한다.

### (8) ★ `switch` 안의 `continue` 가 `switch` 를 다시 돈다고 읽는다

`continue` 는 **바깥 루프의 다음 바퀴**다(동작 (4) `[3]`). 루프가 없으면 컴파일 에러.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262 본문)

- ★★★ **`case` 의 비교는 `IsStrictlyEqual`** — `NaN` 은 안 걸리고 `-0`/`0` 은 같다(동작 (1)의 `3 / 64` 칸 셋).
- ★★★ **`case` 식은 소스 순서로, 골라질 때까지만 평가** · 판별식은 한 번 · `default` 는 앞뒤 `case` 를 다 시험한 뒤 · 흘러내림은 소스 순서(동작 (2)).
- ★★ **한 `CaseBlock` = 한 스코프** · 중복 선언은 Early Error · TDZ(동작 (3)).
- ★★ **라벨** — `continue` 는 루프만 · 없는 라벨·중복 라벨은 Early Error · 함수 경계에서 끊긴다(동작 (4)).

### Annex B(웹 호환 — 「호스트가 지원하면」)

- ★★ 비엄격 코드의 **`case` 사이 같은 이름 함수 선언**(`run: 1`) · **라벨 붙은 함수 선언**. 명세 문장이 「**host is a web browser or otherwise supports …**」 로 조건을 건다 — node 도 V8 이라 **같이 지원했다**(관찰). 엄격 모드에서는 둘 다 `SyntaxError`.

### 엔진(V8 판) · 이 판의 관찰

- ★ 예외 **문구** — 세 판이 같았다(동작 (5)). 라벨 붙은 함수의 문구는 **원인을 가리키지 않는다.**
- ★ `switch` 를 점프 테이블로 바꾸는 최적화(`--switch-table-min-cases`)는 **V8 의 것**이고 **재지 않았다.**

### 그래서 이렇게 적으면 틀린다

- ✗ 「`switch` 는 값이 같은 `case` 로 간다」 → ○ 「**`===` 로 같은** `case` 중 **처음 것**으로 간다 — `NaN` 은 어디에도, `-0` 은 먼저 나온 `0` 으로」
- ✗ 「`default` 는 맨 마지막에 도는 몸통이다」 → ○ 「**모든 `case` 가 아닐 때 들어가는 입구**이고, 들어가면 **그 아래 몸통으로 흘러내린다**」
- ✗ 「`case` 는 각각 블록이다」 → ○ 「**`switch` 의 `{ }` 하나가 블록**이다 — 중괄호를 쳐야 `case` 가 따로 선다」
- ✗ 「`break 라벨` 은 루프에서만 된다」 → ○ 「**아무 라벨 문**에서 된다 — `continue 라벨` 만 루프 전용이다」

## 언제 쓰고 언제 안 쓰나

- **`switch`** — 판별식이 **원시 값 몇 개**(문자열 태그·작은 정수) 중 하나일 때. 여러 값이 같은 처리면 **빈 `case` 를 겹쳐** 흘러내림을 의도적으로 쓴다(`case "a": case "b": …; break;`).
- **`if`/객체 조회** — `NaN`·`-0`·객체 정체성·범위(`x > 10`)가 걸리면. 값 → 처리의 표는 `Map`/객체 리터럴 조회가 흘러내림 사고가 없다.
- **`switch (true) { case 조건: }`** — 조건 목록을 `switch` 모양으로 쓰는 관용구. `case` 식이 **순서대로·첫 참에서 멈춰** 평가된다는 동작 (2)가 그 보증이다. 다만 조건이 불리언이 아니면(`case x && y:` 가 객체를 내면) `true` 와 `===` 가 아니라 안 걸린다 — ★ 이 줄은 **재지 않았다**(동작 (1)의 「강제 변환이 없다」 에서 끌어낸 것).
- **라벨** — 중첩 루프 탈출에만. 대부분은 **함수로 빼고 `return`** 하는 쪽이 읽기 쉽다.
- ★ **안 쓰는 자리** — `case` 식에 부작용 · 중괄호 없는 `case` 안의 `let` · 콜백 안에서 바깥 루프 제어.

## 핵심 문장

1. ★★★ **`case` 는 `===`(IsStrictlyEqual)** — 64칸 중 `Object.is` 와 갈린 칸은 **`NaN`/`NaN` · `-0`/`0` · `0`/`-0` 의 `3 / 64`**. `NaN` 은 어느 `case` 에도 안 들어가고 `-0` 은 먼저 나온 `case 0` 에 들어간다.
2. ★★★ **`case` 식은 소스 순서로, 골라질 때까지만 평가된다** · `default` 는 앞뒤 `case` 를 다 시험한 **뒤의** 입구이고, 들어가면 **아래로 흘러내린다**(`test A > test B > test C > body default > body B > body C`).
3. ★★ **`switch` 의 `{ }` 하나가 스코프 하나** — `case` 마다 `let` 은 `SyntaxError`, 건너뛴 `let` 을 읽으면 TDZ(`typeof` 도). 중괄호를 쳐라.
4. ★★ **라벨** — `break 라벨` 은 아무 문, `continue 라벨` 은 루프만 · `switch` 안의 `continue` 는 바깥 루프 · **함수 경계를 못 넘는다**(`Undefined label`).
5. ★ 라벨 붙은 함수 · `case` 사이 같은 이름 함수는 **Annex B** 가 비엄격에서만 푼다 — 세 판의 문구는 같았지만 문구는 근거가 아니다.

## 관련 자료

- [ECMA-262 — The switch Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-switch-statement) · [Labelled Statements](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-labelled-statements) · [The continue Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-continue-statement)
- [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md) — ★ **경계**: 비교 알고리즘 넷과 `switch` 의 서명(`nynynnny`)은 거기. 여기는 **줄지은 `case` · 흐름 · 스코프 · 라벨**.
- [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — ★ **경계**: `finally` 안의 `break`/`continue` 가 반환값·예외를 지우는 것은 거기. 여기는 **라벨과 `break`/`continue` 의 기본 동작**.
- [Go 15](../../../go/syntax/15-switch-type-switch-fallthrough-labels-and-goto/2-summary.md) · [Java 21](../../../java/syntax/21-switch-statement-and-expression/2-summary.md) · [Python 39](../../../python/syntax/39-match-statement/2-summary.md).

## 용어 풀이

- **판별식(discriminant)** — `switch ( … )` 괄호 안의 식. 한 번만 평가된다.
- **`CaseClauseIsSelected`** — 명세 연산. `case` 식을 평가해 판별식과 `IsStrictlyEqual` 로 견준다. 몸통은 돌리지 않는다.
- **`IsStrictlyEqual`** — `===` 의 명세 이름. `NaN` 은 자기와도 다르고 `+0`/`-0` 은 같다(33번).
- **fallthrough(흘러내림)** — `break` 없이 아래 `case` 몸통으로 이어서 도는 것. JS·C·옛 Java 는 기본, Go 는 `fallthrough` 라고 적어야 한다.
- **`CaseBlock`** — `switch` 의 `{ … }` 전체. 렉시컬 스코프 하나다.
- **TDZ(temporal dead zone)** — `let`/`const`/`class` 가 선언은 됐지만 **초기화 문이 아직 안 돈** 구간. 읽기·쓰기·`typeof` 가 `ReferenceError`.
- **라벨(label)** — 문 앞의 `이름:`. `break 이름`·`continue 이름` 이 부른다.
- **Early Error** — 코드를 **실행하기 전**(구문 분석 때) 내는 `SyntaxError`. 이 문서의 `compile:` 줄들.
- **Annex B** — 명세의 부록. 웹에 남은 옛 코드를 위해 **비엄격 모드에서만** 허용하는 동작들.

## 더 들어가면

- **흘러내림 경고** — JS 엔진은 안 낸다. 린터(ESLint 의 `no-fallthrough`)가 그 몫인데 **이 머신에 없어 돌리지 않았다**(npm 설치 금지 배치).
- **`switch` 의 완료 값** — `eval("switch (1) { case 1: 'a'; }")` 가 무엇을 돌려주나(`UpdateEmpty`). 이 문서는 재지 않았다.
- **점프 테이블 최적화** — V8 의 `--switch-table-min-cases`. 성능은 재지 않았다.
