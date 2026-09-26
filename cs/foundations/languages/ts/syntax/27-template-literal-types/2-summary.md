# ts/syntax/27 — 템플릿 리터럴 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html) ·
> [TypeScript 4.1 릴리스 노트 — Template Literal Types](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-1.html) ·
> [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)(2026-07-08 게시).
> 위는 **규칙 확인용 링크**이고, 본문의 진단·출력은 **전부 이 판에서 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다. ★ 비교용 **5.9.3** 은 이 머신의 **다른 프로젝트에 이미 깔려 있던 것을 읽기만** 했다(4절).

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 2창(`null` 탐침)이다. 그리고 README 의 과녁 하나는 「판 대조」가 본체다.**
> 문자열 타입이 무엇으로 계산됐는지는 **탐침이 아니면 안 보인다**(1·2·3절).
> 그런데 「**7.0 에서 무엇이 바뀌었나**」는 한 판만 던져서는 원리상 답이 안 나온다 — **같은 파일을 두 판에 던져 갈린 칸**을 읽어야 한다(4절).
> ★★ 네 번째 창은 둘이다 — **`TS2590` 격자**(5절, 유니온이 너무 커지는 벽)와 **멤버십 격자**(6절, 어떤 문자열이 `${number}` 에 드나).
> ★★ **27 은 26 과 JS 28 에서 온다.** 매핑의 `as` 자리에서 이름을 새로 짓는 도구가 이것이고([**26번 주제**](../26-mapped-types/) 5절),
> **값의 템플릿 리터럴**(`` `a-${x}` ``)이 JS 쪽 짝이다(JS 갈래 28번). 그리고 「한 글자」가 무엇이냐는 JS 갈래 **04번**(UTF-16)과 이어진다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ **이 문서에 이모지 글자 자체는 한 번도 안 나온다** — 소스는 전부 `\u{…}` 이스케이프로 적었고, 탐침도 글자를 찍지 않고 `"same"`/`"different"` 로 답하게 했다.
> **버전** — 템플릿 리터럴 타입과 `Uppercase`·`Lowercase`·`Capitalize`·`Uncapitalize` 는 **TS 4.1**, 코드 포인트 단위 추론은 **TS 7.0** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ README 의 과녁 — 「7.0 에서 유니코드 코드 포인트 취급이 바뀐 점」을 먼저 확인했다

**있다고 적기 전에 근거부터 댄다.** 두 가지로 확인했다.

1. **릴리스 노트** — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) 에
   **「Template Literal Types Now Preserve Unicode Code Points」** 라는 절이 있다.
   요지는 셋이다 — ① 템플릿 리터럴 타입에서 **추론할 때** 유니코드 코드 포인트를 한 단위로 다룬다
   ② 예전에는 JS 의 UTF-16 인덱싱을 따라 **서로게이트 쌍을 반으로 갈랐다**
   ③ `for...of`·스프레드 `[...str]` 와 같은 단위로 맞췄고, **UTF-16 코드 유닛을 일부러 흉내 낸 타입 수준 유틸리티에는 깨지는 변경**이다.
2. **실측** — 같은 파일을 **7.0.2 와 5.9.3** 에 던져 **갈린 칸을 셌다**(4절). 한 판만 던지는 것으로는 「바뀌었다」를 증명할 수 없다.

★ 릴리스 노트의 문장은 **언어 판의 선언**이고, 4절의 블록은 **그 선언이 이 판에서 실제로 그렇게 도는지**의 확인이다. 둘을 갈라 읽어라.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다 |
| **안 흔들린다** | 5·6절 격자의 **`OK`/`TS2590`/`TS2322` 배치**와 마지막 줄의 수 | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서**(`"bottom-left" \| …`) | 7절 — 5회 md5 **가짓수 1**. **관찰이지 보장이 아니다** |
| **★ 판에 달렸다** | ★★★ **4절 — 7.0.2 와 5.9.3 이 갈린 칸** | 그것이 이 주제의 과녁이다. **판이 오르면 다시 재라** |
| **★ 판에 달렸다** | 오류가 있을 때의 **종료 코드**(7.0.2 는 `1`, 5.9.3 은 `2`) | 4절 블록 — **종료 코드의 뜻이 판마다 다를 수 있다** |
| **★ 설정에 달렸다** | ★★ `--strict` 를 끄면 **`"id-null"` 이 유니온에서 사라진다** | 7절에 대조와 `diff` 를 실었다 |
| **★ 구현 층** | ★★★ `TS2590` 의 **경계 크기** | 5절 — **명세가 정한 수가 아니다** |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 **계산하지 않는다** | [**26번 주제**](../26-mapped-types/) 0절의 블록 — `Uppercase<"ab">` 가 **적은 그대로** 남는다 |
| **★ 부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** — 템플릿 리터럴 **타입**은 방출에 자국이 없다 | 이 문서의 `node` 블록은 **방출된 `.js` 가 아니라 JS 로 따로 쓴 대비**다 |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** 「템플릿 리터럴 타입이 컴파일을 느리게 한다」는 말을 **이 문서는 하지 않는다** |

## 한눈에 — 쉽게 말하면

**템플릿 리터럴 타입은 「빈칸이 뚫린 문자열 도장」이다. 빈칸에 여러 글자를 넣을 수 있으면, 찍혀 나오는 도장도 그 수만큼 늘어난다.**

| 비유 | 실체 |
|---|---|
| 빈칸이 뚫린 **문자열 도장** | `` `id-${number}` `` |
| 빈칸에 들어갈 수 있는 것이 **정해진 몇 개**면 도장을 **전부 찍어 늘어놓는다** | `` `${Side}-${Edge}` `` → 네 개(1절) |
| ★★ 빈칸이 둘이면 **곱**만큼 찍힌다 | 2 × 2 = 4 · 그리고 **너무 많으면 거부한다**(5절 `TS2590`) |
| 빈칸에 **아무 숫자나** 들어가면 도장은 **검사기**가 된다 | `` `id-${number}` `` 는 늘어놓지 않고 **맞는지 본다**(6절) |
| 찍을 때 **글자를 바꿔** 찍는 도장 | `Uppercase`·`Capitalize` — **JS 의 `toUpperCase` 와 같은 규칙**(2절) |
| ★★★ 찍힌 문자열을 **한 글자씩 뜯어 보는** 일 | `infer` 로 쪼개기 — **「한 글자」의 단위가 7.0 에서 바뀌었다**(3·4절) |

- ★★★ 한 줄로 — 「**템플릿 리터럴 타입은 문자열 모양을 타입으로 적는 것이고, 빈칸이 유한하면 곱으로 펼쳐지고 무한하면 검사기가 된다.**」

```text
  빈칸이 유한하냐 무한하냐

  `${"top"|"bottom"}-${"left"|"right"}`         `id-${number}`
               │                                        │
               ▼ 곱으로 펼친다                          ▼ 펼칠 수 없다
   "bottom-left" | "bottom-right"                "id-42"      ✓ 들어간다
   "top-left"    | "top-right"                   "id-abc"     ✗ TS2322
   (1절 4행)                                      (1절 10·11행 · 6절 격자)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **빈칸에 유니온을 넣으면 몇 개가 되고, 어디서 멈추나** — 곱을 늘려 가며 `TS2590` 을 직접 받는다(1·5절).
2. **`Uppercase` 같은 내장 조작은 무엇의 규칙을 따르나** — JS 의 `toUpperCase` 와 **같은 글자**를 넣어 견준다(2절).
3. **★★★ 「한 글자」는 무엇인가 — 그리고 7.0 에서 무엇이 바뀌었나** — `infer` 로 쪼개는 재귀를 **두 판에** 던진다(3·4절).

★★ 3번이 README 의 과녁이고 이 주제의 급소다.

```text
  이 주제가 어디서 오나 — README 의 선행 두 줄

  26 매핑 타입  ──  as 절에서 키 이름을 새로 짓는다 (`get${Capitalize<K>}`)  ──┐
                                                                                 ├─▶ 27
  JS 28 값의 템플릿 리터럴 `a-${x}`  ──  같은 모양을 값이 아니라 타입으로  ──────┘
        │
  JS 04 UTF-16  ──  "한 글자" 가 무엇이냐  ──▶  3·4절 (7.0 의 코드 포인트)
```

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **2창 — `null` 탐침** | 컴파일러가 **계산한** 문자열 타입 | 계산된 것 | **본체**(1·2·3절) |
| ★★★ **판 대조 — 같은 파일을 7.0.2 · 5.9.3 에** | 판이 바꾼 칸 | 갈린 칸 | **README 과녁의 본체**(4절) |
| ★★ **4창 — 종료 코드 격자** | `TS2590` 이 나느냐 | 참/거짓 | 5절 |
| ★★ **1창 — 멤버십 대입** | 문자열이 `` `${number}` `` 에 드느냐 | 에러가 나느냐 | 1절 10·11행 · 6절 격자 |
| ★ **JS 대비 — `node` 로 따로 쓴 `.mjs`** | 같은 글자를 JS 는 어떻게 다루나 | 실행 결과 | 2·3절 |
| ★ **부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | 방출기가 **적은 그대로** 남긴다 | 26편 0절의 블록 |
| ★ **부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** | 타입은 방출에 자국이 없다 | 방출 블록이 **하나도 없다** |

> ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
> 3절의 질문(「첫 글자가 무엇이냐」)을 탐침으로 그냥 물으면 **탐침이 이모지 글자 자체를 찍는다** —
> 이 문서에 **실을 수 없는 글자**다(원고 규칙 — astral 글자 금지). 5.9.3 은 거기서 **반쪽 서로게이트를 대체 문자로** 찍는다.
> 그래서 **비교 타입 `Same<A, B>` 로 바꿔** `"same"`/`"different"` 두 낱말로만 답하게 했다.\
> ★ **바꾼 창이 못 보는 것** — `Same` 은 「그것과 같으냐」만 말하지 **무엇인지는** 말하지 않는다. 그래서 **비교 대상을 두 개**(온전한 글자 · 앞쪽 반쪽) 두었다.


```text
  판 대조 창 — 한 판으로는 "바뀌었다" 를 못 말한다

  ex.27c.ts ──┬──▶ tsc 7.0.2 ──▶ 일곱 줄의 답
              │                         │
              └──▶ tsc 5.9.3 ──▶ 일곱 줄의 답
                                        ▼
                                 줄마다 견준다 → 갈린 줄 = 판이 바꾼 것
                                                  같은 줄 = 판과 무관한 것
```
비용 — 컴파일 세 번 + 판 대조 두 번 + 격자 여덟 번 + 멤버십 한 번(과 `node` 열네 번) + `node` 두 번 + `--strict` 대조 여섯 번.

### (1) ★★ 유니온을 끼우면 곱으로 펼친다 — 넓은 타입을 끼우면 검사기가 된다

**언제 쓰나** — 이벤트 이름·CSS 방향·경로처럼 **정해진 조각을 조합한 문자열**을 타입으로 적을 때.

```ts
// ex.27a.ts
// 템플릿 리터럴 타입 -- 유니온을 끼우면 · 넓은 타입을 끼우면
type Side = "top" | "bottom";
type Edge = "left" | "right";
const t1: null = null as unknown as `${Side}-${Edge}`;
const t2: null = null as unknown as `${Side | Edge}!`;
const t3: null = null as unknown as `id-${1 | 2 | true | null}`;
const t4: null = null as unknown as `${string}-${Side}`;

type NumId = `id-${number}`;
const n1: NumId = "id-42";
const n2: NumId = "id-abc";
let loose: string = "id-7";
const n3: NumId = loose;
console.log(t1, t2, t3, t4, n1, n2, n3);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27a.ts (tsc exit=1) =====
ex.27a.ts(4,7): error TS2322: Type '"bottom-left" | "bottom-right" | "top-left" | "top-right"' is not assignable to type 'null'.
  Type '"bottom-left"' is not assignable to type 'null'.
ex.27a.ts(5,7): error TS2322: Type '"bottom!" | "left!" | "right!" | "top!"' is not assignable to type 'null'.
  Type '"bottom!"' is not assignable to type 'null'.
ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-null" | "id-true"' is not assignable to type 'null'.
  Type '"id-1"' is not assignable to type 'null'.
ex.27a.ts(7,7): error TS2322: Type '`${string}-bottom` | `${string}-top`' is not assignable to type 'null'.
  Type '`${string}-bottom`' is not assignable to type 'null'.
ex.27a.ts(11,7): error TS2322: Type '"id-abc"' is not assignable to type '`id-${number}`'.
ex.27a.ts(13,7): error TS2322: Type 'string' is not assignable to type '`id-${number}`'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 4행 — `` `${Side}-${Edge}` `` 가 **네 개**로 펼쳐졌다. 2 × 2 다. **빈칸마다 유니온이 분배되고 그 곱이 나온다.**
- ★ 5행 — 빈칸 **하나**에 유니온 넷을 넣으면 **네 개**. 곱이 아니라 그대로다.
- ★★ 6행 — `number`·`boolean`·`null` **리터럴도 글자로 바뀌어** 끼워진다(`"id-1"`·`"id-true"`·`"id-null"`).
  ★ 이 줄은 **`--strict` 에 달렸다** — 7절을 보라.
- ★★★ 7행 — 빈칸에 **`string`** 을 넣으면 펼치지 않고 **패턴**으로 남는다(`` `${string}-bottom` | `${string}-top` ``). 유니온 쪽만 펼쳐졌다.
- ★★ 10행에는 진단이 없고 **11행은 `TS2322`** — `` `id-${number}` `` 가 **`"id-42"` 는 받고 `"id-abc"` 는 막는다.** 여기서 타입은 **검사기**다.
- ★★ 13행 — **`string` 변수는 못 넣는다.** 값이 `"id-7"` 이어도 **타입이 `string`** 이면 모양을 모른다.

```text
  빈칸마다 분배되고 곱이 나온다

  `${"top" | "bottom"}-${"left" | "right"}`
        │                   │
        ├─ "top"    ────────┼─ "left"    →  "top-left"
        │                   └─ "right"   →  "top-right"
        └─ "bottom" ────────┬─ "left"    →  "bottom-left"
                            └─ "right"   →  "bottom-right"

  ★ 표시 순서는 사전순으로 보인다 — 관찰이지 보장이 아니다 (7절)
```

비용 — 곱은 **금방 커진다.** 그 벽이 5절이다.

### (2) ★★ 내장 문자열 조작 — JS 의 `toUpperCase` 와 같은 글자가 나오나

**언제 쓰나** — 키 이름을 `getId` 처럼 **대소문자를 바꿔** 지을 때. [**26번 주제**](../26-mapped-types/) 5절 16행이 이것을 썼다.

```ts
// ex.27b.ts
// 내장 문자열 조작 -- Uppercase · Lowercase · Capitalize · Uncapitalize
const c1: null = null as unknown as Uppercase<"hello">;
const c2: null = null as unknown as Capitalize<"hello world">;
const c3: null = null as unknown as Uncapitalize<"URL">;
const c4: null = null as unknown as Lowercase<"MiXeD">;
const c5: null = null as unknown as Capitalize<"get" | "set">;
const c6: null = null as unknown as Uppercase<"\u00DF">;
const c7: null = null as unknown as Uppercase<"\uFB01">;
const c8: null = null as unknown as Capitalize<"가나">;
const c9: null = null as unknown as Uppercase<string>;

let shout: Uppercase<string> = "ABC";
shout = "abc";
console.log(c1, c2, c3, c4, c5, c6, c7, c8, c9, shout);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27b.ts (tsc exit=1) =====
ex.27b.ts(2,7): error TS2322: Type '"HELLO"' is not assignable to type 'null'.
ex.27b.ts(3,7): error TS2322: Type '"Hello world"' is not assignable to type 'null'.
ex.27b.ts(4,7): error TS2322: Type '"uRL"' is not assignable to type 'null'.
ex.27b.ts(5,7): error TS2322: Type '"mixed"' is not assignable to type 'null'.
ex.27b.ts(6,7): error TS2322: Type '"Get" | "Set"' is not assignable to type 'null'.
  Type '"Get"' is not assignable to type 'null'.
ex.27b.ts(7,7): error TS2322: Type '"SS"' is not assignable to type 'null'.
ex.27b.ts(8,7): error TS2322: Type '"FI"' is not assignable to type 'null'.
ex.27b.ts(9,7): error TS2322: Type '"가나"' is not assignable to type 'null'.
ex.27b.ts(10,7): error TS2322: Type 'Uppercase<string>' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.27b.ts(13,1): error TS2322: Type 'string' is not assignable to type 'Uppercase<string>'.
```

JS 쪽 짝 — **같은 글자**를 값으로 `toUpperCase` 에 넣었다.

```js
// case27.mjs
// 같은 글자를 JS 의 toUpperCase 에 넣으면
for (const s of ["hello", "\u00DF", "\uFB01"]) {
    const up = s.toUpperCase();
    console.log(JSON.stringify(up), "length", s.length, "->", up.length);
}
```

```text
===== node case27.mjs (node exit=0) =====
"HELLO" length 5 -> 5
"SS" length 1 -> 2
"FI" length 1 -> 2
```

그림 해설 — 한 단계에 한 문장.

- ★★ 2\~5행 — `"HELLO"`·`"Hello world"`·`"uRL"`·`"mixed"`. **`Capitalize` 는 첫 글자 하나만** 바꾼다(3행 — `world` 는 그대로).
- ★ 6행 — 유니온을 넣으면 **멤버마다** 바뀐다(`"Get" | "Set"`).
- ★★★ **7·8행이 이 절의 과녁이다.** 소스에 U+00DF(독일어 에스체트)와 U+FB01(합자 fi)을 넣었더니
  `Uppercase` 가 **`"SS"`·`"FI"`** 를 냈다 — **글자 수가 늘었다**(한 글자 → 두 글자).
- ★★★ JS 블록이 **같은 글자**를 낸다 — `"SS" length 1 -> 2`·`"FI" length 1 -> 2`. **타입 쪽 규칙이 JS 의 `toUpperCase` 와 같다.**
  ★ 7.0 은 컴파일러가 Go 로 다시 쓰인 판인데도 **이 두 글자에서는 JS 와 같은 답**이 나왔다. 두 글자에서 본 것이지 **전 영역 보장이 아니다.**
- ★ 9행 — 한글은 대소문자가 없어 **그대로**다.
- ★★ 10행 — `Uppercase<string>` 은 **`Uppercase<string>` 이라는 타입 그대로** 남는다. 12행 `"ABC"` 는 들고 **13행 `"abc"` 는 `TS2322`** 로 막힌다.
  넓은 타입에 걸면 **「대문자로만 된 문자열」이라는 검사기**가 된다.

```text
  Uppercase 는 늘리기도 한다

   U+00DF (1 글자)  ──Uppercase──▶  "SS"  (2 글자)      타입 쪽 7행
                    ──toUpperCase─▶  "SS"  (2 글자)      JS 쪽 2행
   U+FB01 (1 글자)  ──Uppercase──▶  "FI"  (2 글자)      타입 쪽 8행
                    ──toUpperCase─▶  "FI"  (2 글자)      JS 쪽 3행

  ★ 대소문자 변환은 "글자마다 한 글자"가 아니다
```

비용 — 대소문자 변환 뒤의 **길이를 가정한 타입**은 이런 글자에서 어긋난다.

### (3) ★★★ `infer` 로 쪼개기 — 「한 글자」는 코드 포인트다

**언제 쓰나** — 문자열 타입을 **머리와 꼬리로 쪼개** 길이를 세거나 첫 글자를 바꿀 때.
쪼개는 재귀 자체는 [**25번 주제**](../25-infer-and-recursive-conditional-types/) 4절이 정본이다(`Split`·`FirstChar`) — 여기는 **「한 글자」의 단위**만 본다.

```ts
// ex.27c.ts
// infer 로 문자열 쪼개기 -- 한 글자는 무엇인가
type Head<S extends string> = S extends `${infer C}${string}` ? C : never;
type Tail<S extends string> = S extends `${string}${infer R}` ? R : never;
type Len<S extends string, A extends unknown[] = []> =
    S extends `${string}${infer R}` ? Len<R, [...A, 1]> : A["length"];
type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? "same" : "different") : "different";

const n1: null = null as unknown as Len<"abc">;
const n2: null = null as unknown as Len<"가나다">;
const n3: null = null as unknown as Len<"\u{1F600}">;
const n4: null = null as unknown as Len<"e\u0301">;
const h1: null = null as unknown as Same<Head<"\u{1F600}x">, "\u{1F600}">;
const h2: null = null as unknown as Same<Head<"\u{1F600}x">, "\uD83D">;
const h3: null = null as unknown as Same<Tail<"\u{1F600}x">, "x">;
console.log(n1, n2, n3, n4, h1, h2, h3);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27c.ts (tsc exit=1) =====
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"same"' is not assignable to type 'null'.
```

JS 쪽 짝 — **같은 글자**를 JS 는 세 가지로 센다.

```js
// cp27.mjs
// 같은 글자를 JS 는 몇 개로 세나
const samples = [["smile", "\u{1F600}"], ["accent", "e\u0301"], ["hangul", "가나다"]];
const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
for (const [name, s] of samples) {
    const graphemes = [...seg.segment(s)].length;
    console.log(name, "length", s.length, "spread", [...s].length, "graphemes", graphemes);
}
```

```text
===== node cp27.mjs (node exit=0) =====
smile length 2 spread 1 graphemes 1
accent length 2 spread 2 graphemes 1
hangul length 3 spread 3 graphemes 3
```

그림 해설 — 한 단계에 한 문장.

- ★ 8·9행 — `"abc"` 도 `"가나다"` 도 **`3`**. 한글 음절은 BMP 안의 글자라 **어느 단위로 세도 같다.**
- ★★★ 10행 — U+1F600(이모지 하나)의 `Len` 이 **`1`** 이다. JS 의 `length` 는 **`2`**(`smile length 2`) — 서로게이트 **쌍**이기 때문이다.
  **7.0.2 의 `infer` 는 `length` 가 아니라 스프레드(`spread 1`)와 같은 단위로 셌다.**
- ★★★ 12·13행 — 첫 글자를 뽑아 견줬다. **온전한 글자와 `"same"`**, 앞쪽 반쪽 U+D83D 와 **`"different"`**. 반으로 안 갈랐다.
- ★★ 14행 — 꼬리도 `"x"` 로 **`"same"`**. 머리가 한 글자를 통째로 가져갔으니 꼬리에 반쪽이 안 남는다.
- ★★★ **11행이 경계다.** `e` + U+0301(결합 악센트)은 화면에 **한 글자**로 보이는데 `Len` 이 **`2`** 다.
  JS 블록도 `accent … spread 2 graphemes 1` — **코드 포인트는 둘, 사람 눈의 글자(그래핌)는 하나**다.
  **7.0 이 맞춘 단위는 코드 포인트이지 그래핌이 아니다.**

```text
  같은 글자를 세 가지 단위로 센다

                 UTF-16 코드 유닛     코드 포인트          그래핌(눈에 보이는 글자)
                 JS .length           [...s] · for...of    Intl.Segmenter
  "abc"               3                    3                    3
  "가나다"            3                    3                    3
  U+1F600             2                    1  ◀── 7.0 의 infer  1
  e + U+0301          2                    2  ◀── 7.0 의 infer  1   ★ 여기서 갈린다

  ★ 7.0 은 가운데 칸에 맞췄다 — 오른쪽 칸이 아니다
```

비용 — 「글자 수」를 타입으로 셀 때 **결합 문자·국기·가족 이모지** 같은 것은 **여전히 여러 개로 센다.** 7.0 이 고친 것은 **서로게이트 쌍**까지다.

### (4) ★★★ 같은 파일을 두 판에 — 7.0 에서 무엇이 바뀌었나

**언제 쓰나** — README 의 과녁 「**7.0 에서 코드 포인트 취급이 바뀌었다**」를 **실측으로** 확인할 때.
★ **5.9.3 은 새로 설치하지 않았다** — 이 머신의 다른 프로젝트에 **이미 깔려 있던 `tsc` 를 읽기만** 했다. 경로는 스크립트에 있다.

```bash
# ts26b-cmp59.sh
#!/usr/bin/env bash
# 같은 파일을 두 판의 tsc 로 던진다 -- 7.0.2 와, 이 머신의 다른 프로젝트에 깔려 있던 5.9.3
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
echo "== tsc $(tsc --version)"
tsc --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
echo "== node OLD $(node "$OLD" --version)"
node "$OLD" --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
```

```text
===== bash ts26b-cmp59.sh (sh exit=0) =====
== tsc Version 7.0.2
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"same"' is not assignable to type 'null'.
(exit 1)
== node OLD Version 5.9.3
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"different"' is not assignable to type 'null'.
(exit 2)
```

그림 해설 — 한 단계에 한 문장.

- ★★ 8·9·11행 — 두 판이 **같다**(`3`·`3`·`2`). 서로게이트가 없는 글자, 그리고 결합 문자는 **판과 무관**하다.
- ★★★ **10행이 갈렸다** — 7.0.2 는 **`1`**, 5.9.3 은 **`2`**. 이모지 하나를 5.9.3 은 **두 조각**으로 셌다.
- ★★★ **12·13행이 뒤집혔다** — 7.0.2 는 머리가 온전한 글자와 `"same"` 이고, 5.9.3 은 **앞쪽 반쪽 U+D83D 와 `"same"`** 이다.
  **5.9.3 은 서로게이트 쌍을 반으로 갈랐다.** 릴리스 노트가 적은 그대로다.
- ★★ 14행 — 꼬리도 5.9.3 은 `"x"` 와 **`"different"`** — 뒤쪽 반쪽이 꼬리에 **붙어 남았다.**
- ★★ 갈린 칸은 **일곱 줄 중 넷**(10·12·13·14행)이고, **전부 서로게이트 쌍이 걸린 줄**이다.
- ★ 덤으로 — 종료 코드가 **7.0.2 는 `1`, 5.9.3 은 `2`** 다. 같은 「진단 있음」인데 **종료 코드의 값이 판마다 다르다.**
  스크립트가 종료 코드로 성공/실패를 가르면 **`0` 이냐 아니냐**로만 읽어라.

```text
  U+1F600 + "x" 를 머리와 꼬리로 쪼갠다

                  머리                        꼬리
  5.9.3   [ 앞쪽 반쪽 U+D83D ]      [ 뒤쪽 반쪽 U+DE00 + "x" ]     ← UTF-16 코드 유닛
  7.0.2   [ U+1F600 한 글자 ]       [ "x" ]                         ← 코드 포인트

  Len<U+1F600>    5.9.3 → 2       7.0.2 → 1
```

비용 — **깨지는 변경**이다. `Len` 을 **JS 의 `.length` 와 맞추려고** 짠 타입은 7.0 에서 **값이 바뀐다** — 에러 없이.

### (5) ★★ 곱이 커지면 — `TS2590` 을 직접 받는다

**언제 쓰나** — 「숫자 네 자리 문자열」처럼 **빈칸을 여러 개 이어** 쓰기 전에, 어디서 벽에 닿는지 알아 둘 때.

```bash
# ts26b-union.sh
#!/usr/bin/env bash
# 템플릿 리터럴이 유니온을 곱할 때 -- 원소 수 x 자리 수를 바꿔 가며 TS2590 을 받는다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
blocked=0; total=0
printf '%-6s %-6s %-8s %s\n' 원소 자리 곱 결과
for pair in 10:4 10:5 2:16 2:17 46:3 47:3 316:2 317:2; do
  b=${pair%:*}; n=${pair#*:}
  u=$(for ((i=0;i<b;i++)); do printf '"k%d"' "$i"; ((i<b-1)) && printf ' | '; done)
  t='`'; for ((i=0;i<n;i++)); do t="$t\${U}"; done; t="$t\`"
  { echo "type U = $u;"; echo "type P = $t;"; echo 'declare const p: P;'; echo 'export { p };'; } > "$D/p.ts"
  out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1); rc=$?
  case "$out" in *TS2590*) mark="TS2590 exit=$rc"; blocked=$((blocked+1));; '') mark="OK     exit=$rc";; *) mark="OTHER  exit=$rc";; esac
  total=$((total+1))
  printf '%-6s %-6s %-8s %s\n' "$b" "$n" "$((b**n))" "$mark"
done
echo "막힌 칸 $blocked / $total"
```

```text
===== bash ts26b-union.sh (sh exit=0) =====
원소 자리 곱      결과
10     4      10000    OK     exit=0
10     5      100000   TS2590 exit=1
2      16     65536    OK     exit=0
2      17     131072   TS2590 exit=1
46     3      97336    OK     exit=0
47     3      103823   TS2590 exit=1
316    2      99856    OK     exit=0
317    2      100489   TS2590 exit=1
막힌 칸 4 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★ 원소 10 개를 **네 자리**로 이으면 통과하고 **다섯 자리**면 **`TS2590`**「Expression produces a union type that is too complex to represent.」이다.
- ★★★ **원소 2 개는 열여섯 자리도 통과**한다. 자리 수로 보면 10 × 5 보다 훨씬 긴데 **살아남았다.**
- ★★★ 넷째 칸 **곱**을 보라 — 통과한 줄과 막힌 줄이 **자리 수가 아니라 곱의 크기**로 갈린다.
  46 × 3 자리와 47 × 3 자리, 316 × 2 자리와 317 × 2 자리가 **곱이 선을 넘는 자리**에서 한 줄씩 갈렸다.
- ★★ 마지막 줄 **막힌 칸 4 / 8** — 스크립트가 센 것이다.

```text
  무엇이 벽에 닿게 하나

  자리 수가 많다         2 가지 × 16 자리     통과
  자리 수가 적다         317 가지 × 2 자리    TS2590
                         ─────────────────────────────
  ★ 갈리는 축은 "몇 자리냐" 가 아니라 "펼치면 몇 개냐(곱)" 다
```

★★★ **수를 어떻게 읽을 것인가** — 정확한 경계는 **블록 안에 있고, 본문은 성질만 주장한다**:
「**곱이 어떤 크기를 넘으면 막히고, 자리 수 자체는 축이 아니다.**」
★★ **그 경계 크기는 구현(tsc 7.0.2) 층이다.** 명세가 정한 수가 아니고, **판이 오르면 다시 재야 한다.**
★★★ **그리고 이 절에 「느리다」는 말이 없다** — **시간을 재지 않았다.** 막히는 것은 **표현을 거부**하는 것이지 「느려서」가 아니다.
검사 비용이 궁금하면 [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능)가 그 자리다.

비용 — 벽에 닿으면 **그 타입이 통째로 쓸 수 없게** 된다. 큰 조합은 `` `${number}` `` 같은 **검사기 꼴**로 바꾸는 편이 낫다(6절).

### (6) ★★ `${number}` 에 드는 문자열 — `Number()` 와 견준다

**언제 쓰나** — `` `id-${number}` `` 같은 **검사기 꼴**이 **정확히 어떤 문자열을 받는지** 알아야 할 때.

```bash
# ts26b-numstr.sh
#!/usr/bin/env bash
# `${number}` 에 드는 문자열 -- tsc 의 멤버십 대입과 JS 의 Number() 를 나란히 둔다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
samples=('42' '1e3' '0x1F' '0b11' '.5' '-0' ' 7' '7 ' ' ' '' 'abc' 'Infinity' 'NaN' '1_000')
{ echo 'type N = `${number}`;'
  i=0; for s in "${samples[@]}"; do printf 'export const v%d: N = "%s";\n' "$i" "$s"; i=$((i+1)); done; } > "$D/n.ts"
out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/n.ts" 2>&1)
split=0; total=0; i=0
printf '%-12s %-8s %s\n' '문자열' 'tsc' 'Number.isFinite(Number(s))'
for s in "${samples[@]}"; do
  line=$((i+2))
  case "$out" in *"n.ts($line,"*) t=TS2322;; *) t=OK;; esac
  j=$(node -e 'console.log(Number.isFinite(Number(process.argv[1])))' -- "$s")
  if [ "$t" = OK ]; then tv=true; else tv=false; fi
  total=$((total+1)); if [ "$tv" != "$j" ]; then split=$((split+1)); fi
  printf '%-12s %-8s %s\n' "\"$s\"" "$t" "$j"
  i=$((i+1))
done
echo "tsc 와 Number() 가 갈린 칸 $split / $total"
```

```text
===== bash ts26b-numstr.sh (sh exit=0) =====
문자열    tsc      Number.isFinite(Number(s))
"42"         OK       true
"1e3"        OK       true
"0x1F"       OK       true
"0b11"       OK       true
".5"         OK       true
"-0"         OK       true
" 7"         OK       true
"7 "         OK       true
" "          OK       true
""           TS2322   true
"abc"        TS2322   false
"Infinity"   TS2322   false
"NaN"        TS2322   false
"1_000"      TS2322   false
tsc 와 Number() 가 갈린 칸 1 / 14
```

그림 해설 — 한 단계에 한 문장.

- ★★ `"1e3"`·`"0x1F"`·`"0b11"`·`".5"`·`"-0"` 이 **전부 통과**한다. 「십진 정수」가 아니라 **JS 가 숫자로 읽는 것**이다.
- ★★★ **공백이 섞인 `" 7"`·`"7 "`, 그리고 공백만 있는 `" "` 까지 통과**한다. `Number(" ")` 가 `0` 이기 때문으로 읽힌다.
- ★★ `"Infinity"`·`"NaN"`·`"1_000"`·`"abc"` 는 **`TS2322`**. JS 쪽도 전부 `false`(유한한 수가 아니다)다.
- ★★★ **딱 한 칸이 갈렸다** — 빈 문자열 `""`. JS 는 `Number("")` 가 `0` 이라 `true` 인데 **tsc 는 막는다.**
- ★ 마지막 줄 **갈린 칸 1 / 14**. 그러므로 이 판의 관찰로는 「**비어 있지 않고, `Number()` 가 유한한 수를 내는 문자열**」이 `` `${number}` `` 에 든다.
  ★★ **이것은 명세 문장이 아니라 열네 칸에서 읽은 규칙**이다.

```text
  `${number}` 의 문턱 — 이 판에서 열네 칸을 던져 본 것

   "42" "1e3" "0x1F" "0b11" ".5" "-0"      들어간다
   " 7" "7 " " "                           ★ 들어간다 — 공백도
   ""                                       ★ 막힌다 — Number("") 는 0 인데도
   "abc" "Infinity" "NaN" "1_000"          막힌다
```

비용 — **「숫자 모양 문자열」로 쓰기엔 너그럽다.** 공백과 16진수까지 받으므로, 엄격한 형식이 필요하면 **런타임 검사**가 따로 있어야 한다.

### (7) ★ 설정 대조와 표시 순서 — 근거로 쓸 칸을 먼저 못 박는다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.27a.ts    exit 1 = exit 1 · ★ 출력이 다르다
ex.27b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.27c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.27a.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.27a.ts) (sh exit=1) =====
5c5
< ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-null" | "id-true"' is not assignable to type 'null'.
---
> ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-true"' is not assignable to type 'null'.
```

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.26c.ts    5회 md5 가짓수 1
ex.27a.ts    5회 md5 가짓수 1
ex.28a.ts    5회 md5 가짓수 1
ex.28b.ts    5회 md5 가짓수 1
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **27a 한 파일이 갈렸다.** `diff` 가 말한다 — **`"id-null"` 이 유니온에서 사라졌다.**
  `strictNullChecks` 가 꺼지면 `null` 이 **따로 서는 타입이 아니게 되어** 유니온 `1 | 2 | true | null` 에서 **흡수된다** — 그래서 끼워 넣을 글자가 없다.
- ★★ 27b·27c 는 **안 갈렸다.** 대소문자 조작과 코드 포인트 쪼개기는 **설정을 안 탄다.**

```text
  --strict 를 끄면 null 이 흡수된다 — 27a 6행

  --strict          `id-${1 | 2 | true | null}`  →  "id-1" | "id-2" | "id-null" | "id-true"
  --strict false    `id-${1 | 2 | true | null}`  →  "id-1" | "id-2" | "id-true"
                                   └─ null 이 따로 서지 않는다 → 끼워 넣을 글자가 없다
```
- ★★ 같은 명령을 5회 돌려 md5 **가짓수가 1** 이다(27a 줄). **유니온 표시 순서가 안 흔들렸다.** ★ **관찰이지 보장이 아니다.**

비용 — 없다. 이 절은 **뒤의 모든 인용이 딛고 설 바닥**을 깐다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  `${A}-${B}`                         A·B 가 유니온이면 곱으로 펼친다      (1절)
  `${string}-top`                     넓은 타입 → 패턴(검사기)으로 남는다   (1절)
  `id-${number}`                      숫자로 읽히는 문자열만 받는다          (1·6절)
  Uppercase<S> · Lowercase<S>         JS 의 toUpperCase/toLowerCase 규칙    (2절)   ★ 4.1
  Capitalize<S> · Uncapitalize<S>     첫 글자만 바꾼다                       (2절)
  S extends `${infer C}${infer R}`    머리 한 글자 · 꼬리 — ★ 7.0 부터 코드 포인트 (3·4절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다. 전문은 「동작 방식」의 블록에 있다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| 곱이 너무 큰 템플릿 리터럴 | `TS2590` | 5절 |
| `` `id-${number}` `` 에 `"id-abc"` | `TS2322` | 1절 11행 |
| `` `id-${number}` `` 에 `string` 변수 | `TS2322` | 1절 13행 |
| `Uppercase<string>` 에 `"abc"` | `TS2322` | 2절 13행 |

**규칙 불릿**

- ★★ **빈칸마다 유니온이 분배되고 곱이 나온다**(1절 4행).
- ★★ **넓은 타입(`string`·`number`)을 넣으면 펼치지 않고 검사기가 된다**(1절 7·11행).
- ★★ **`string` 변수는 모양을 모르므로 못 넣는다**(1절 13행).
- ★★★ **내장 조작은 JS 의 대소문자 규칙과 같은 글자를 냈다** — 글자 수가 늘기도 한다(2절 7·8행).
- ★★★ **7.0 부터 `infer` 의 「한 글자」는 코드 포인트다** — 서로게이트 쌍을 안 가른다(3·4절).
- ★★ **그래핌이 아니다** — 결합 문자는 여전히 여럿으로 센다(3절 11행).
- ★★ **곱이 선을 넘으면 `TS2590`** — 축은 자리 수가 아니라 곱이다(5절). ★ **그 선은 구현 층**이다.
- ★ **`${number}` 는 너그럽다** — 공백·16진수·지수 표기를 받고 빈 문자열은 막는다(6절).

## 어디서 틀리나

- ★★★ 「**`infer` 로 한 글자씩 세면 JS 의 `.length` 와 같겠지**」 — 7.0 에서는 **코드 포인트**로 센다. 이모지 하나가 `.length` 2 대 `Len` 1 이다(3절 10행).
- ★★★ 「**7.0 이 사람 눈의 글자로 센다**」 — **아니다.** 결합 악센트는 여전히 둘이다(3절 11행).
- ★★★ 「**자리가 몇 개를 넘으면 폭발한다**」 — 축은 **곱**이다. 두 가지짜리는 열여섯 자리도 통과했다(5절).
- ★★ 「**`Uppercase` 는 글자 수를 안 바꾸겠지**」 — U+00DF 는 **두 글자** `"SS"` 가 된다(2절 7행).
- ★★ 「**`${number}` 는 숫자 문자만 받겠지**」 — 공백·`"0x1F"`·`"1e3"` 도 받는다(6절).
- ★★ 「**`Capitalize` 는 단어마다 바꾸겠지**」 — **첫 글자 하나만**(2절 3행).
- ★ 「**`--strict` 와 무관하겠지**」 — `null` 을 끼운 유니온이 **한 원소를 잃는다**(7절).
- ★ 「**템플릿 리터럴 타입은 컴파일을 느리게 한다**」 — **이 문서는 시간을 재지 않았다.** `TS2590` 은 **거부**이지 속도 측정이 아니다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(4.1)** | 템플릿 리터럴 타입 · 빈칸의 유니온 분배 · 내장 네 조작 | 1·2절 |
| **★★★ 언어 판의 변경(7.0)** | ★★★ `infer` 가 **코드 포인트** 단위로 쪼갠다 — **깨지는 변경** | 릴리스 노트 「Template Literal Types Now Preserve Unicode Code Points」 + 4절 실측 |
| **★ 이 판(7.0.2)의 관찰** | 결합 문자는 코드 포인트 **여럿**으로 센다 — 그래핌이 아니다 | 3절 11행 |
| **★ 이 판의 관찰** | `Uppercase` 가 U+00DF·U+FB01 에서 **JS 와 같은 글자**를 낸다 | 2절 — **두 글자에서 본 것**이다 |
| **★ 이 판의 관찰** | `${number}` 의 문턱 — 비어 있지 않고 `Number()` 가 유한 | 6절 — **열네 칸에서 읽었다** |
| **★★★ 구현(tsc 7.0.2) 층** | ★★★ **`TS2590` 의 경계 크기** | 5절 — **명세가 정한 수가 아니다.** 판이 오르면 **다시 재라** |
| **★ 판에 달렸다** | 진단이 있을 때의 **종료 코드 값**(7.0.2 `1` · 5.9.3 `2`) | 4절 |
| **★ 설정에 달렸다** | `--strict` 를 끄면 `null` 원소가 **흡수된다** | 7절 |
| **이 판의 관찰** | 유니온 원소의 **표시 순서** | 7절 — 5회 md5 가짓수 1 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | 26편 0절 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** | 방출 블록이 없다 |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/) |

## 언제 쓰고 언제 안 쓰나

| 템플릿 리터럴 타입을 쓴다 | 안 쓴다 |
|---|---|
| 조각이 **적고 정해진** 문자열(방향·이벤트 이름) | 조각의 **곱이 큰** 것 — `TS2590`(5절) |
| 매핑의 `as` 자리에서 **키 이름을 새로 지을** 때 | 형식이 **엄격해야** 하는 입력 — `${number}` 는 공백도 받는다(6절) |
| 문자열 모양을 **검사기로** 쓸 때(`` `id-${number}` ``) | **사람 눈의 글자 수**를 세야 할 때 — 그래핌은 타입이 못 센다(3절) |
| `infer` 로 **구분자 기준** 쪼개기 | 7.0 이전 판과 **같은 결과를 기대하는** 글자 수 계산 — 4절 |

## 핵심 문장

1. **템플릿 리터럴 타입은 문자열 모양을 타입으로 적는 것이다** — 빈칸이 유한하면 곱으로 펼치고, 무한하면 검사기가 된다.
2. **곱이 선을 넘으면 `TS2590`** — 축은 자리 수가 아니라 곱이고, 그 선은 구현 층이다.
3. **내장 조작은 JS 의 대소문자 규칙과 같은 글자를 낸다** — 글자 수가 늘 수도 있다.
4. **★★★ 7.0 부터 `infer` 의 「한 글자」는 코드 포인트다** — 5.9.3 은 서로게이트 쌍을 반으로 갈랐다.
5. **그래도 그래핌은 아니다** — 결합 문자는 여전히 여럿이다.

## 관련 자료

- [**26번 주제** — 매핑 타입](../26-mapped-types/) — ★★ **README 의 선행.** `as` 자리에서 `` `get${Capitalize<…>}` `` 로 키를 새로 짓는 것이 이 주제의 첫 쓰임이다. 5창 부적용 블록도 그쪽에 있다.
- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) — `Split`·`FirstChar` 같은 **쪼개는 재귀**는 그쪽이 정본. 여기는 **「한 글자」의 단위**만.
- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) — 빈칸마다 유니온이 **분배**되는 것은 그쪽의 분배와 같은 집안이다.
- [**28번 주제**](../28-utility-types/)(유틸리티 타입) — 사슬의 다음. 내장 문자열 조작 넷도 `lib.es5.d.ts` 에는 `intrinsic` 으로만 적혀 있다.
- [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능) — ★★★ **검사 시간은 그쪽이다.** 이 문서는 **재지 않았다.**
- `` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **28번**([`String` 메서드와 템플릿 리터럴](../../../js/syntax/28-string-methods-and-template-literals/)) `` — ★★ **짝.** 그쪽은 **값을 만드는** 템플릿 리터럴과 `toUpperCase` 까지, 여기는 **타입을 만드는** 템플릿 리터럴까지.
- `` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **04번**([문자열과 UTF-16](../../../js/syntax/04-strings-and-utf16/)) `` — ★★ `length` 가 코드 유닛이라는 것·서로게이트 쌍·`Intl.Segmenter` 의 정본. 3절의 세 단위 표가 그쪽에서 온다.

## 용어 풀이

> **템플릿 리터럴 타입** — `` `…${X}…` `` 꼴로 **문자열 모양을 적는 타입**(TS 4.1).\
> 예: `` `${"a" | "b"}-x` `` 는 `"a-x" | "b-x"` 이다.

> **코드 유닛(code unit)** — UTF-16 에서 **16비트 한 칸**. JS 의 `.length` 가 세는 단위다.\
> 예: U+1F600 은 코드 유닛 **두 칸**(서로게이트 쌍)이다.

> **코드 포인트(code point)** — 유니코드가 글자 하나에 준 **번호 하나**. `for...of`·스프레드가 세는 단위다.\
> 예: U+1F600 은 코드 포인트 **하나**다. 7.0 의 `infer` 가 이 단위로 쪼갠다.

> **서로게이트 쌍(surrogate pair)** — BMP 밖의 글자를 UTF-16 으로 적을 때 쓰는 **코드 유닛 두 개**.\
> 예: U+1F600 은 U+D83D·U+DE00 두 칸이다. 5.9.3 은 이것을 **반으로 갈랐다**(4절).

> **그래핌(grapheme)** — 사람이 **한 글자로 보는** 단위. 코드 포인트 여러 개일 수 있다.\
> 예: `e` + U+0301 은 그래핌 하나, 코드 포인트 둘이다(3절 11행).

> **BMP** — 유니코드의 **첫 65,536 자리**. 여기 있는 글자는 코드 유닛 하나로 적힌다.\
> 예: 한글 음절은 BMP 안이라 세 단위가 **다 같다**.

> **`TS2590`** — 「Expression produces a union type that is too complex to represent.」\
> 예: 원소 열 개를 다섯 자리로 이으면 난다(5절). **자리가 아니라 곱**이 부른다.

> **`intrinsic`** — 선언 파일에 몸통 없이 적힌 **컴파일러 내장** 타입의 표시.\
> 예: `type Uppercase<S extends string> = intrinsic;` — 규칙이 `.d.ts` 가 아니라 **컴파일러 안**에 있다.

## 더 들어가면

- **왜 `null` 이 `--strict` 를 끄면 사라지나** — `strictNullChecks` 가 꺼지면 `null`·`undefined` 가 **모든 타입에 이미 들어 있는** 값으로 취급된다.
  그래서 유니온 `1 | 2 | true | null` 이 **`null` 을 따로 적지 않는 모양**으로 줄고, 끼워 넣을 글자가 없어진다.
  ★ **이 해석은 7절의 `diff` 한 줄에서 읽은 것**이다. 명세 문장으로 확인하지는 않았다.
- **`${number}` 의 문턱은 왜 그 모양인가** — 6절은 **열네 칸에서 읽은 관찰**이다. 「`Number()` 가 유한한 수를 내고 비어 있지 않다」와
  **어긋나는 칸을 더 찾으면** 이 문장은 고쳐야 한다. `"+7"`·`"7."`·`"\t7"` 같은 칸은 **안 던졌다.**
- **7.0 이전 판에 맞춘 `Length` 타입을 어떻게 옮기나** — 릴리스 노트가 **깨지는 변경**이라고 적은 자리다.
  JS 의 `.length` 와 맞춰야 하면 **타입 수준에서 코드 유닛을 세는 방법이 7.0 에는 없다**고 읽힌다 — **확인은 안 했다.**
- **대소문자 변환이 JS 와 어긋나는 글자가 있나** — 2절은 **두 글자**를 견줬을 뿐이다. 로케일에 따라 갈리는 글자(터키어의 점 있는 I 등)는
  JS 의 `toUpperCase` 자체가 **로케일을 안 받는다**는 점까지만 알고, **타입 쪽은 안 던졌다.**
