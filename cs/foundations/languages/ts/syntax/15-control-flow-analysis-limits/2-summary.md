# ts/syntax/15 — 제어 흐름 분석의 한계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Narrowing: Control flow analysis](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#control-flow-analysis) ·
> [Handbook — Narrowing: Using type predicates](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates) ·
> [TypeScript 4.4 릴리스 노트 — Aliased conditions](https://devblogs.microsoft.com/typescript/announcing-typescript-4-4/).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> ★★★ 이 주제의 격자는 **언어 명세가 아니라 이 판의 관찰**이다. 조건은 판마다 넓어질 수 있다 — **외우지 말고 다시 던져라.**
> ★★ `exactOptionalPropertyTypes`·`noUncheckedIndexedAccess` 는 **`strict` 밖**이고 기본 `false` 다 — 이 문서는 **안 켰다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ **4절의 「진단 0건」** — 이 주제의 본체다 | 소스 전문을 옆에 뒀으니 다시 던질 수 있다 |
| **안 흔들린다** | ★ 런타임 예외 문구 두 가지 | `node` v18 의 메시지다. **판이 오르면 문구가 바뀔 수 있다** |
| **★ 설정에 달렸다** | 1·3·5절 격자의 **다섯 칸** | `strictNullChecks`. 양쪽을 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다. 예외도 `message` 만 찍어 **스택을 안 남겼다** |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | 제어 흐름 분석의 **검사 시간** | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ **4절은 진단이 한 줄도 없다.** 그러므로 **소스 전문과 실행 출력이 곧 근거**다 — 셋을 나란히 실었다.

## 한눈에 — 쉽게 말하면

**컴파일러는 「이 줄에 오기까지의 경로」만 읽는다. 경로가 끊기면 좁힘도 끊긴다.**

| 비유 | 실체 |
|---|---|
| 한 줄로 걸어온 길은 **되짚을 수 있다** | 같은 함수 안의 순차 코드 — 좁힘이 산다 |
| ★ **언제 열릴지 모르는 상자**에 코드를 넣으면 | 콜백 — **부르는 시점을 모른다** |
| 상자를 **지금 당장 열면** 괜찮다 | 즉시 실행 함수(IIFE) — 좁힘이 산다 |
| 이름표가 **못 박힌** 물건은 안심한다 | `const`·재대입 없는 `let`·재대입 없는 매개변수 |
| 남의 **주머니 속**은 아무도 장담 못 한다 | `b.v` 같은 **프로퍼티** — 콜백에서 무조건 풀린다 |
| ★★★ 지나가는 사람을 **의심하지 않는다** | 함수 호출 뒤 — **믿어 주지만 보장이 아니다** |
| 고치는 법은 **꺼내서 손에 쥐는 것** | 지역 `const` 하나 |

- ★★★ 한 줄로 — 「**좁힘은 참조에 붙지 값에 붙지 않는다. 참조를 못 믿게 되는 순간 풀린다.**」
- ★★ 그래서 이 주제의 값은 「어디서 풀리나」를 외우는 것이 아니라 **「무엇을 믿고 있는지」를 아는 것**이다.

```text
  좁힘이 사는 범위

  if (b.v) {                    ← 여기서 b.v 가 string 이 된다
      touch();                  ← 함수 호출: 믿어 준다 (보장 아님)
      await …;                  ← await: 믿어 준다 (보장 아님)
      (() => b.v)();            ← 즉시 실행: 산다
      cb(() => b.v);            ← 콜백: 풀린다  ★ 프로퍼티라서
  }
  b.v                           ← 분기 밖: 풀린다
```

```text
  무엇을 좁혔나가 결과를 가른다

   좁힌 것이 …          콜백 안에서
   ─────────────────────────────────
   변수 이름 v          대입이 없으면 산다
   매개변수 s           대입이 없으면 산다   ← 판별 유니온이 여기 있다
   프로퍼티 b.v         언제나 풀린다
   this.v               언제나 풀린다        ← 프로퍼티다
   readonly o.v         언제나 풀린다        ← readonly 는 못 막는다
   호출식 o.v()         애초에 안 좁혀진다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어디서 풀리고 어디서 안 풀리나** — [**12번 주제**](../12-narrowing/)가 일곱 자리를 쟀다. 여기서 **서른세 자리**로 넓힌다.
2. **`let` 과 `const` 가 진짜 기준인가** — 아니다. 「**어딘가에서 대입되는가**」다. 일곱 칸 격자로 가른다.
3. **안 풀리는 자리는 안전한가** — **아니다.** 함수 호출 뒤를 던져서 깨뜨린다. **이 주제의 본체다.**

★ [**12번 주제**](../12-narrowing/)가 「좁히는 수단」이라면 여기는 「**좁힘이 얼마나 오래 사는가**」다.
★★ [**13번 주제**](../13-type-guards-and-predicates/)·[**14번 주제**](../14-assertion-signatures/)가 만든 좁힘도 **같은 규칙을 받는다**(5절·11번 답).

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **자리마다 박은 `null` 탐침** | 그 줄에서 타입이 무엇인지 | [**12번 주제**](../12-narrowing/)에서 이어받음 |
| ★★★ **방출 `.js` + `node` 실행** | **「안 풀린다」가 보장이 아닌 것** | ★ 이 주제의 본체 |
| ★ **같은 파일을 `--strict false` 로 다시** | 탐침이 갈리는 칸을 가르려고 | [**12번 주제**](../12-narrowing/)에서 이어받음 |

★★★ **`never`·`any` 는 탐침을 통과한다** — `const x: null = v;` 가 조용하면 `v` 가 `null` 이거나 `never` 이거나 `any` 다.
이 문서의 탐침 서른셋은 **전부 진단을 냈다**. 조용한 자리가 없으므로 **역방향 대입까지 갈 일이 없었다.**

비용 — 컴파일 한 번 + 실행 한 번.

### (1) ★★★ 경계를 넘는 열한 자리

**언제 쓰나** — 「분명히 체크했는데 콜백 안에서 또 `undefined` 일 수 있다고 한다」에서 막힐 때.

```ts
// ex.15a.ts
// 좁힘이 풀리는 자리와 안 풀리는 자리 — 1부: 경계를 넘는 여덟 모양
interface Box {
    v?: string;
}
declare function touch(): void;
declare function takeCb(f: () => void): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const a1: null = b.v;
    }
}
async function afterAwait(b: Box) {
    if (b.v) {
        await Promise.resolve();
        const a2: null = b.v;
    }
}
function inCallback(b: Box) {
    if (b.v) {
        takeCb(() => {
            const a3: null = b.v;
        });
    }
}
function inNestedDecl(b: Box) {
    if (b.v) {
        function inner() {
            const a4: null = b.v;
        }
        inner();
    }
}
function inIIFE(b: Box) {
    if (b.v) {
        (() => {
            const a5: null = b.v;
        })();
    }
}
function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const a6: null = v;
        v = 1;
        const a7: null = v;
    }
}
function byLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const a8: null = v;
        });
    }
}
let mutable: string | number = "s";
function overModuleLet() {
    if (typeof mutable === "string") {
        const a9: null = mutable;
        takeCb(() => {
            const a10: null = mutable;
        });
    }
}
const frozen: string | number = "s";
function overModuleConst() {
    if (typeof frozen === "string") {
        takeCb(() => {
            const a11: null = frozen;
        });
    }
}
console.log(afterCall, afterAwait, inCallback, inNestedDecl, inIIFE, afterReassign, byLocalConst, overModuleLet, overModuleConst);
```

```text
===== tsc --pretty false --noEmit ex.15a.ts (tsc exit=1) =====
ex.15a.ts(11,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(23,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15a.ts(30,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15a.ts(38,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(46,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15a.ts(53,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(62,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15a.ts(70,19): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **열한 개**이고 진단도 열한 건이다. 읽을 것은 「몇 건」이 아니라 「**무엇이라고**」다.
- ★★★ **풀린 것은 넷**이다 — 23행(콜백) · 30행(중첩 함수 선언) · 46행(재대입) · 62행(모듈 `let` 을 콜백에서).
- 11행 `afterCall` — 다른 함수를 부른 뒤에도 **`string`** 이다. **안 풀린다.**
- ★★ 17행 `afterAwait` — **`await` 뒤에도 안 풀린다.** 그 사이에 다른 코드가 얼마든지 돌 수 있는데도 그렇다.
- ★★★ 23행 `inCallback` — 콜백 안의 `b.v` 는 **`string | undefined`** 다. **풀린다.**
- 30행 `inNestedDecl` — 중첩 **함수 선언**도 같다. 호이스팅돼 어디서든 불릴 수 있다.
- ★★★ 38행 `inIIFE` 가 이 절의 별이다. **즉시 실행 함수 안에서는 안 풀린다** — `string` 그대로다.\
  **「지금 당장 부른다」는 것이 문법에 보이면** 컴파일러가 그 흐름을 이어 준다.
- 44·46행 `afterReassign` — 재대입 전은 `string`, 후는 **`number`** 다. 대입이 좁힘을 **갱신**한다.
- ★★ 53행 `byLocalConst` — 같은 값을 **지역 `const`** 에 담으면 콜백 안에서도 **`string`** 이다. **이것이 고치는 법이다.**
- ★★★ 60·62·70행이 `let` 과 `const` 의 대비다. 모듈 `let` 은 콜백에서 **`string | number`** 로 풀리는데,\
  모듈 `const` 는 **`string`** 그대로다. **다시 대입될 수 있는지가 갈랐다.**

> **제어 흐름 분석(control flow analysis)** — 「이 줄에 도달하기까지의 경로」를 따라 참조의 타입을 좁히는 분석.\
> 경로가 끊기거나 참조를 못 믿게 되면 **선언 타입으로 되돌아간다.**

비용 — 없음. 다만 **어디서 끊기는지 모르면 「왜 여기서만 에러가 나지」로 헤맨다.**

### (2) ★★★ 무엇을 좁혔나 — 열다섯 자리

**언제 쓰나** — 「배열 원소를 체크했는데 타입이 안 줄었다」거나 「`this.v` 가 콜백에서 풀린다」일 때.

```ts
// ex.15b.ts
// 2부: 무엇을 좁혔나 — 인덱스·게터·메서드 호출·판별 유니온·this·구조 분해·readonly
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;

function byIndexParam(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const b1: null = xs[i];
    }
}
function byIndexLiteral(xs: (string | number)[]) {
    if (typeof xs[0] === "string") {
        const b2: null = xs[0];
    }
}
function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const b3: null = o.v;
    }
}
function byMethodCall(o: { v(): string | number }) {
    if (typeof o.v() === "string") {
        const b4: null = o.v();
    }
}
function duAfterCall(s: Shape, f: () => void) {
    if (s.kind === "circle") {
        f();
        const b5: null = s.r;
    }
}
function duInCallback(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const b6: null = s.r;
        });
    }
}
class Holder {
    v: string | number = "s";
    afterCall(f: () => void) {
        if (typeof this.v === "string") {
            const b7: null = this.v;
            f();
            const b8: null = this.v;
        }
    }
    inCallback() {
        if (typeof this.v === "string") {
            takeCb(() => {
                const b9: null = this.v;
            });
        }
    }
}
function byDestructure(b: { v?: string }) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const b10: null = v;
        });
    }
}
function byReadonlyProp(o: { readonly v: string | number }) {
    if (typeof o.v === "string") {
        takeCb(() => {
            const b11: null = o.v;
        });
    }
}
function inLoopBody(b: { v?: string }) {
    if (b.v) {
        for (let i = 0; i < 1; i++) {
            const b12: null = b.v;
        }
    }
}
function inTryFinally(b: { v?: string }) {
    if (b.v) {
        try {
            const b13: null = b.v;
        } finally {
            const b14: null = b.v;
        }
    }
}
function viaOptionalChain(b: { inner?: { v?: string } }) {
    if (b.inner?.v) {
        const b15: null = b.inner.v;
    }
}
console.log(byIndexParam, byIndexLiteral, byGetter, byMethodCall, duAfterCall, duInCallback, Holder, byDestructure, byReadonlyProp, inLoopBody, inTryFinally, viaOptionalChain);
```

```text
===== tsc --pretty false --noEmit ex.15b.ts (tsc exit=1) =====
ex.15b.ts(9,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(14,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(19,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(24,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(30,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15b.ts(36,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15b.ts(44,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(46,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(52,23): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(61,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(68,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(75,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(82,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(84,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(90,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **열다섯 개**이고 진단도 열다섯 건이다. **풀리거나 안 좁혀진 것은 셋**이다 — 24·52·68행.
- ★★ 9·14행 — **인덱스 접근도 좁혀진다.** `xs[i]`(매개변수 `i`)도, `xs[0]`(리터럴)도 **`string`** 이다.\
  단 조건이 있다 — 3절이 그것을 가른다.
- ★★ 19행 — **게터도 좁혀진다.** `{ get v(): string | number }` 의 `o.v` 가 `string` 이다.\
  ★★★ **게터는 부를 때마다 다른 값을 줄 수 있는데도 그렇다** — 4절이 그 대가를 던진다.
- ★★★ 24행 — **메서드 호출 결과는 애초에 안 좁혀진다.** `o.v()` 는 `string | number` 그대로다.\
  「풀렸다」가 아니라 **처음부터 좁힐 대상이 아니다** — 호출식은 **참조가 아니다.**
- 30행 — 판별 유니온은 함수 호출 뒤에도 `number` 다.
- ★★★ 36행이 놀라운 자리다. **판별 유니온은 콜백 안에서도 `number` 다** — 안 풀린다.\
  좁혀진 것이 **프로퍼티가 아니라 매개변수 `s` 자신**이고, `s` 는 **어디서도 대입되지 않기** 때문이다.
- 44·46행 — `this.v` 도 함수 호출 뒤에는 유지된다.
- ★★★ 52행 — 그런데 **`this.v` 를 콜백 안에서 보면 `string | number`** 로 풀린다. 36행과 정반대다.\
  `this.v` 는 **프로퍼티 접근**이기 때문이다.
- ★★ 61행 — 구조 분해한 `const` 는 콜백 안에서도 `string` 이다. 53행(1절)과 같은 고침이다.
- ★★★ 68행 — **`readonly` 는 좁힘을 지켜 주지 않는다.** 콜백 안에서 `string | number` 로 풀린다.\
  `readonly` 는 **이 타입으로 쓰지 말라**는 표기일 뿐 **런타임 불변을 보장하지 않는다**([**07번 주제**](../07-object-type-details/)).
- 75·82·84·90행 — 루프 몸통·`try`·`finally`·옵셔널 체이닝 뒤는 전부 **유지**된다.

```text
  2절의 열다섯 자리 — 유지 12 · 풀림 또는 안 좁혀짐 3

  ✓ xs[i]  (i 가 매개변수)      ✓ this.v  (호출 뒤)
  ✓ xs[0]  (리터럴)             ✗ this.v  (콜백 안)        ← 프로퍼티
  ✓ o.v    (게터)               ✓ 구조 분해한 const (콜백 안)
  ✗ o.v()  (호출식)             ✗ readonly o.v (콜백 안)   ← readonly 못 막는다
  ✓ 판별 유니온 (호출 뒤)        ✓ for 루프 몸통
  ✓ 판별 유니온 (콜백 안)        ✓ try / finally
                                 ✓ 옵셔널 체이닝 뒤
```

> **참조(reference)** — 좁힘이 붙는 대상. 변수 이름 · 프로퍼티 접근(`o.v`) · 상수 인덱스 접근(`xs[0]`) 등.\
> **호출식(`o.v()`)은 참조가 아니다** — 좁힐 자리가 없다.

비용 — 없음. 다만 **`readonly` 를 안전장치로 착각하면** 68행 같은 자리에서 놀란다.

### (3) ★★★ `let` 대 `const` 가 아니라 「어딘가에서 대입되는가」다

**언제 쓰나** — 「`const` 로 바꿨더니 됐다」의 **진짜 이유**를 알고 싶을 때.

```ts
// ex.15c.ts
// let 대 const 가 아니라 「어딘가에서 대입되는가」가 기준이다
declare function takeCb(f: () => void): void;
type Tagged = { kind: "a"; x: number } | { kind: "b" };

function constLocal(b: { v?: string }) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const c1: null = v;
        });
    }
}
function letNeverAssigned(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c2: null = v;
        });
    }
}
function letAssignedLater(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c3: null = v;
        });
    }
    v = undefined;
}
function paramNeverAssigned(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c4: null = s.x;
        });
    }
}
function paramAssignedLater(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c5: null = s.kind;
        });
    }
    s = { kind: "b" };
}
function indexByConstIndex(xs: (string | number)[]) {
    const i = 0;
    if (typeof xs[i] === "string") {
        const c6: null = xs[i];
    }
}
function indexByAssignedIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const c7: null = xs[i];
    }
    i = 1;
}
console.log(constLocal, letNeverAssigned, letAssignedLater, paramNeverAssigned, paramAssignedLater, indexByConstIndex, indexByAssignedIndex);
```

```text
===== tsc --pretty false --noEmit ex.15c.ts (tsc exit=1) =====
ex.15c.ts(9,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(25,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15c.ts(33,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15c.ts(40,19): error TS2322: Type '"a" | "b"' is not assignable to type 'null'.
  Type '"a"' is not assignable to type 'null'.
ex.15c.ts(48,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(54,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **일곱 개**다. **풀린 것은 셋**(25·40·54행)이고 **넷은 유지**된다.
- 9행 `constLocal` — 지역 `const` 는 콜백 안에서도 `string` 이다.
- ★★★ 17행 `letNeverAssigned` — **`let` 인데도 유지된다.** 선언 뒤 **한 번도 대입되지 않았기** 때문이다.
- ★★★ 25행 `letAssignedLater` — 같은 `let` 인데 **풀린다**. 다른 점은 단 하나, **함수 끝에 `v = undefined;` 가 있다.**\
  그 대입은 **콜백보다 뒤**에 있는데도 영향을 준다 — 분석은 **함수 전체를 보고** 판단한다.
- ★★ 33행 `paramNeverAssigned` — 매개변수도 같다. 대입이 없으면 콜백 안에서 유지된다.
- 40행 `paramAssignedLater` — 뒤에서 `s = { kind: "b" };` 하면 **풀린다.**
- ★★★ 48·54행이 같은 규칙을 **인덱스**에서 보여 준다. `const i = 0` 이면 `xs[i]` 가 좁혀지고,\
  `let i = 0` 인데 뒤에서 `i = 1` 을 하면 **안 좁혀진다.** **인덱스 변수도 참조의 일부**다.
- ★★ 즉 규칙은 하나다 — 「**그 참조를 이루는 모든 이름이 그 함수 안에서 한 번도 대입되지 않으면**\
  콜백 안에서도 좁힘이 산다」. `const` 는 그 조건을 **문법으로 보장하는 지름길**일 뿐이다.

```text
  3절의 일곱 칸 — 기준은 「그 함수 안에서 대입되는가」

  ✓ const v            = b.v                 대입 없음
  ✓ let   v            = b.v                 대입 없음      ★ let 인데 산다
  ✗ let   v = b.v;  …  v = undefined;        뒤에서 대입     ★ 콜백보다 뒤인데도
  ✓ 매개변수 s          (대입 없음)
  ✗ 매개변수 s;     …  s = { kind: "b" };    뒤에서 대입
  ✓ xs[i]  (const i = 0)
  ✗ xs[i]  (let i = 0; … i = 1)              인덱스도 참조의 일부
```

★★ 이 파일은 `--strict false` 에서 갈린다. 같은 파일을 다시 던졌다.

```text
===== tsc --pretty false --noEmit --strict false ex.15c.ts (tsc exit=1) =====
ex.15c.ts(9,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(25,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(33,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15c.ts(40,19): error TS2322: Type '"a" | "b"' is not assignable to type 'null'.
  Type '"a"' is not assignable to type 'null'.
ex.15c.ts(48,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(54,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

- ★★★ **25행의 글자가 바뀐다** — `string | undefined` 가 **`string`** 이 된다.
- ★★ 이유는 「풀리지 않게 됐다」가 아니라 「**풀린 것이 안 보이게 됐다**」다.\
  `strictNullChecks` 가 꺼지면 `undefined` 가 모든 타입에 흡수되어 **탐침이 차이를 못 잡는다.**
- ★★★ 즉 **플래그를 끄면 이 주제의 실험 자체가 안 보인다.** 나머지 여섯 줄은 글자 하나까지 같다.

### (4) ★★★ 「안 풀린다」는 보장이 아니다 — 던져서 깨뜨린다

**언제 쓰나** — 「컴파일이 됐으니 안전하겠지」를 멈춰야 할 때. **이 절이 이 주제의 본체다.**

```ts
// ex.15d.ts
// 분석이 「믿어 주는」 자리 — 보장이 아니라는 것을 던져서 깨뜨린다
interface Box {
    v?: string;
}
function wipe(b: Box): void {
    delete b.v;
}
function afterCall(b: Box): string {
    if (b.v) {
        wipe(b);
        return b.v.toUpperCase();
    }
    return "없다";
}

let flip = 0;
const spy = {
    get v(): string | number {
        flip += 1;
        return flip % 2 === 1 ? "문자열" : 42;
    },
};
function afterGetter(): string {
    if (typeof spy.v === "string") {
        return spy.v.toUpperCase();
    }
    return "숫자다";
}

const shared: Box = { v: "안녕" };
async function afterAwait(): Promise<string> {
    if (shared.v) {
        await Promise.resolve();
        return shared.v.toUpperCase();
    }
    return "없다";
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}
run("afterCall  :", () => afterCall({ v: "안녕" }));
run("afterGetter:", () => afterGetter());
afterAwait().then(
    (r) => console.log("afterAwait :", r),
    (e) => console.log("afterAwait : 터졌다 ->", (e as Error).message),
);
shared.v = undefined;
```

```text
===== tsc --pretty false ex.15d.ts (tsc exit=0) =====
===== 방출된 ex.15d.js =====
"use strict";
function wipe(b) {
    delete b.v;
}
function afterCall(b) {
    if (b.v) {
        wipe(b);
        return b.v.toUpperCase();
    }
    return "없다";
}
let flip = 0;
const spy = {
    get v() {
        flip += 1;
        return flip % 2 === 1 ? "문자열" : 42;
    },
};
function afterGetter() {
    if (typeof spy.v === "string") {
        return spy.v.toUpperCase();
    }
    return "숫자다";
}
const shared = { v: "안녕" };
async function afterAwait() {
    if (shared.v) {
        await Promise.resolve();
        return shared.v.toUpperCase();
    }
    return "없다";
}
function run(label, f) {
    try {
        console.log(label, f());
    }
    catch (e) {
        console.log(label, "터졌다 ->", e.message);
    }
}
run("afterCall  :", () => afterCall({ v: "안녕" }));
run("afterGetter:", () => afterGetter());
afterAwait().then((r) => console.log("afterAwait :", r), (e) => console.log("afterAwait : 터졌다 ->", e.message));
shared.v = undefined;
```

```text
===== node ex.15d.js (node exit=0) =====
afterCall  : 터졌다 -> Cannot read properties of undefined (reading 'toUpperCase')
afterGetter: 터졌다 -> spy.v.toUpperCase is not a function
afterAwait : 터졌다 -> Cannot read properties of undefined (reading 'toUpperCase')
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단이 한 줄도 없다. 종료 코드가 `0` 이다.** 그런데 **세 줄이 전부 터진다.**
- ★★★ `afterCall` — `if (b.v)` 로 좁힌 뒤 `wipe(b)` 가 **그 프로퍼티를 지운다.**\
  컴파일러는 「함수 호출 뒤에는 안 풀린다」고 믿었고, 런타임은 「Cannot read properties of undefined」라고 답한다.
- ★★★ `afterGetter` — 게터가 **부를 때마다 다른 값**을 준다. `if` 에서 한 번, `return` 에서 또 한 번 부른다.\
  「`spy.v.toUpperCase is not a function`」 — **같은 표현식이 두 번 다른 값**이었다.
- ★★ `afterAwait` — `await` 사이에 **다른 코드가 프로퍼티를 지웠다.** 1절 17행의 「안 풀린다」가 여기서 값을 치른다.
- ★★★ 그래서 정확한 표현은 「**안 풀린다**」가 아니라 「**분석이 믿어 준다**」다.\
  안전해서 믿는 것이 아니라 **매 호출마다 다시 의심하면 쓸 수 있는 코드가 거의 없어지기 때문**이다.
- ★ 방출된 `.js` 를 보면 타입 관련 글자가 **하나도 없다.** `if (b.v)` 라는 **JS 조건문만** 남는다.

```text
  컴파일 시각                          런타임
  ───────────────────────────────────────────────────────────
  if (b.v) { wipe(b); b.v… }          wipe(b) 가 b.v 를 지운다
        │                                    │
        ▼                                    ▼
  b.v 는 string 이다 (믿는다)          b.v 가 undefined
  b.v.toUpperCase() 통과               TypeError
        │                                    │
        ▼                                    ▼
  tsc exit 0 · 진단 0건                node 가 대신 말한다
```

> **믿어 주는 자리(unsound narrowing)** — 분석이 좁힘을 유지하지만 런타임이 그것을 지켜 주지는 않는 자리.\
> 함수 호출 뒤 · `await` 뒤 · 게터 재접근이 대표적이다. **컴파일이 통과해도 터질 수 있다.**

비용 — ★★★ **타입 검사가 잡아 주지 않는 버그가 여기 산다.** 프로퍼티를 지우거나 갈아 끼우는 코드가 있으면 의심하라.

### (5) ★★ 고치는 법 — 지역 `const` 하나

**언제 쓰나** — 위의 자리를 실제로 고칠 때.

```ts
// ex.15e.ts
// 고치는 법 — 지역 const 하나. 같은 코드를 고치기 전과 뒤로 나란히 둔다
interface Box {
    v?: string;
}
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;
declare function assertDefined<T>(v: T): asserts v is NonNullable<T>;

function brokenByProperty(b: Box) {
    if (b.v) {
        takeCb(() => {
            const e1: null = b.v;
        });
    }
}
function fixedByLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const e2: null = v;
        });
    }
}
function fixedByDestructure(b: Box) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const e3: null = v;
        });
    }
}
function fixedByAssertion(b: Box) {
    assertDefined(b.v);
    const e4: null = b.v;
    takeCb(() => {
        const e5: null = b.v;
    });
}
function brokenIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const e6: null = xs[i];
    }
    i = 1;
}
function fixedIndex(xs: (string | number)[]) {
    let i = 0;
    const x = xs[i];
    if (typeof x === "string") {
        const e7: null = x;
    }
    i = 1;
}
function brokenDiscriminant(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const e8: null = s.kind;
        });
    }
    s = { kind: "square", side: 1 };
}
function fixedDiscriminant(s: Shape) {
    const shape = s;
    if (shape.kind === "circle") {
        takeCb(() => {
            const e9: null = shape.r;
        });
    }
    s = { kind: "square", side: 1 };
}
console.log(brokenByProperty, fixedByLocalConst, fixedByDestructure, fixedByAssertion, brokenIndex, fixedIndex, brokenDiscriminant, fixedDiscriminant);
```

```text
===== tsc --pretty false --noEmit ex.15e.ts (tsc exit=1) =====
ex.15e.ts(14,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15e.ts(22,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(36,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(38,15): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15e.ts(52,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(59,19): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.15e.ts(68,19): error TS2322: Type 'number' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **아홉 개**다. 「고치기 전」 넷과 「고친 뒤」 다섯을 나란히 뒀다.
- 14행 `brokenByProperty` — 프로퍼티를 콜백에서 보면 `string | undefined` 다.
- ★★★ 22행 `fixedByLocalConst` — **지역 `const` 하나**면 `string` 이다. **이것이 정석이다.**
- ★★ 30행 `fixedByDestructure` — 구조 분해도 같다. `const { v } = b;` 가 하는 일은 같다.
- ★★★ 36·38행이 이 절의 함정이다. `assertDefined(b.v)`([**14번 주제**](../14-assertion-signatures/)) 뒤의 36행은 **`string`** 인데,\
  같은 단언 뒤의 **콜백 안**인 38행은 다시 **`string | undefined`** 다.\
  **단언은 「고치는 법」이 아니다** — 좁힘을 만드는 수단이 달라도 **지켜지는 규칙은 하나**다.
- 44·52행 — 인덱스도 같다. `xs[i]` 를 그대로 쓰면 안 되고 **`const x = xs[i];`** 로 꺼내야 한다.
- ★★ 59·68행 — 판별 유니온도 같다. 매개변수가 뒤에서 대입되면 풀리므로 **`const shape = s;`** 로 못 박는다.
- ★ 고침의 공통점은 하나다 — 「**다시 읽지 않아도 되게 한 번만 읽어 손에 쥔다.**」

비용 — 변수 하나. 대신 **원본이 바뀌어도 손에 쥔 값은 안 바뀐다** — 그것이 안전의 값이자 **의미의 변화**다.

### (6) ★ `strict` 를 꺼도 규칙은 같다 — 보이지 않게 될 뿐

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.15a.ts    exit 1 / exit 1 · ★ 다르다
ex.15b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.15c.ts    exit 1 / exit 1 · ★ 다르다
ex.15e.ts    exit 1 / exit 1 · ★ 다르다
```

- ★★ 네 파일 중 **셋이 갈린다.** 다만 갈리는 방향이 전부 같다 — **탐침이 차이를 못 보여 주게** 된다.
- 1절의 파일을 다시 던진 것이 아래다.

```text
===== tsc --pretty false --noEmit --strict false ex.15a.ts (tsc exit=1) =====
ex.15a.ts(11,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(23,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(38,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(46,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15a.ts(53,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(62,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15a.ts(70,19): error TS2322: Type 'string' is not assignable to type 'null'.
```

- ★★★ **23·30행의 글자가 `string`** 으로 바뀐다. 11·17행(안 풀린 자리)과 **같은 글자**가 된다.
- ★ 62행은 `string | number` 로 남는다 — 그 유니온에는 `null`·`undefined` 가 없어서 플래그와 무관하다.

5절의 파일도 같은 방향으로 갈린다.

```text
===== tsc --pretty false --noEmit --strict false ex.15e.ts (tsc exit=1) =====
ex.15e.ts(14,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(22,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(36,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(38,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15e.ts(52,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(59,19): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.15e.ts(68,19): error TS2322: Type 'number' is not assignable to type 'null'.
```

- ★★ **14행과 38행이 `string`** 이 된다 — 「고치기 전」과 「단언 뒤 콜백」이 **고쳐진 자리와 구별되지 않는다.**
- ★★ 교훈 — **이 주제를 실험하려면 `strictNullChecks` 가 켜져 있어야 한다.** 7.0 기본값이 `true` 라 그대로 된다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  if (b.v) { touch(); b.v }          ★ 유지 — 함수 호출 뒤
  if (b.v) { await …; b.v }          ★ 유지 — await 뒤
  if (b.v) { cb(() => b.v) }         ✗ 풀림 — 콜백 안의 프로퍼티
  if (b.v) { (() => b.v)() }         ★ 유지 — 즉시 실행 함수
  const v = b.v; if (v) { cb(() => v) }   ★ 고치는 법
  if (typeof o.v() === "string") o.v()    ✗ 애초에 안 좁혀짐 (호출식)
  if (typeof xs[i] === "string") xs[i]    ★ i 가 대입되지 않으면 유지
```

**규칙 불릿**

- ★★★ **좁힘은 참조에 붙는다** — 변수 이름·프로퍼티 접근·상수 인덱스 접근. **호출식은 참조가 아니다**(2절 24행).
- ★★★ **콜백 안에서는 프로퍼티 좁힘이 무조건 풀린다**(1절 23행 · 2절 52·68행). **`readonly` 도 못 막는다.**
- ★★★ **변수 좁힘은 「그 함수 안에서 한 번도 대입되지 않으면」 콜백 안에서도 산다**(3절).\
  `const` 냐 `let` 이냐가 아니라 **대입의 유무**다.
- ★★ **즉시 실행 함수 안에서는 유지된다**(1절 38행) — 「지금 부른다」가 문법에 보이기 때문이다.
- ★★ **함수 호출 뒤·`await` 뒤에는 유지되지만 그것은 보장이 아니다**(4절). 런타임이 지워 버릴 수 있다.
- ★★ **재대입은 좁힘을 갱신한다**(1절 46행) — 푸는 것이 아니라 **새 타입으로 바꾼다.**
- ★ **인덱스 접근은 인덱스 변수까지 참조의 일부**다(3절 48·54행).
- ★ **고치는 법은 지역 `const` 하나**다(5절). 단언(`asserts`)은 고치는 법이 **아니다**(5절 38행).

**금지 사례** — 이 주제는 **에러 코드가 아니라 「타입이 안 줄었다」로 나타난다.** 셋만 뽑는다.

```text
1) 콜백 안에서 프로퍼티 재접근   ->  에러 코드 없음. 그냥 string | undefined 로 돌아간다
2) 호출식을 좁히려는 시도        ->  에러 코드 없음. 처음부터 안 좁혀진다
3) ★ 믿어 주는 자리를 그대로 신뢰 ->  진단 없음. tsc exit 0. 런타임에 TypeError
```

## 어디서 틀리나

- ★★★ 「**함수 호출 뒤에도 안 풀리니 안전하다**」 — **보장이 아니다.** 4절이 셋 다 런타임에 터뜨린다.
- ★★★ 「**`const` 로 바꾸면 되는 건 `const` 라서다**」 — 아니다. 「**대입이 없어서**」다. 3절 17행이 `let` 으로도 된다.
- ★★ 「**`readonly` 면 콜백에서도 안 풀리겠지**」 — 풀린다(2절 68행). `readonly` 는 **런타임 불변이 아니다.**
- ★★ 「**콜백이면 무조건 풀린다**」 — 변수 좁힘은 **대입이 없으면 산다**(3절 33행). 판별 유니온도 그렇다(2절 36행).
- ★★ 「**즉시 실행 함수도 함수니까 풀리겠지**」 — 안 풀린다(1절 38행).
- ★★ 「**`asserts` 를 쓰면 콜백까지 좁혀지겠지**」 — 안 된다(5절 38행).
- ★ 「**게터는 프로퍼티처럼 안전하겠지**」 — 게터는 **부를 때마다 값이 다를 수 있다**(4절 둘째 줄).
- ★ 「**배열 원소는 못 좁힌다**」 — 좁혀진다(2절 9·14행). 단 **인덱스가 대입되지 않아야** 한다(3절 54행).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 좁힘은 **참조**에 붙고 호출식에는 안 붙는다 | 2절 24행 |
| **언어 보장** | 콜백 안에서 **프로퍼티 좁힘은 풀린다** | 1절 23행 · 2절 52·68행 |
| **언어 보장** | 재대입은 좁힘을 **갱신**한다 | 1절 46행 |
| **★ 이 판의 관찰** | ★★★ **「대입이 없으면 콜백에서도 산다」는 조건** | 3절. **구현의 경계다 — 다시 던져라** |
| **★ 이 판의 관찰** | 즉시 실행 함수에서 유지되는 것 | 1절 38행 |
| **★ 이 판의 관찰** | 인덱스 접근이 좁혀지는 조건 | 2절 9·14행 · 3절 48·54행 |
| **방출된 JS** | ★★★ **좁힘은 한 글자도 안 남는다** | 4절 방출 전문 — `if (b.v)` 라는 JS 조건문만 남는다 |
| **방출된 JS** | ★ 「안 풀린다」를 지켜 주는 장치가 **없다** | 4절 실행 출력 — 셋 다 터진다 |
| **★ 설정에 달림** | 1·3·5절 격자의 **다섯 칸**의 표시 | `strictNullChecks`. **양쪽 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | 진단 문구 전문 | 코드(`TS2322`)가 더 오래 간다 |
| **이 판의 관찰** | 런타임 예외 문구 두 가지 | `node` v18 의 메시지다 |
| **안 잰 것** | 제어 흐름 분석의 **검사 시간** | 재지 않았다 |

★★★ 「**진단 0건」이 근거인 블록이 하나**다(4절). 그 블록은 **소스 전문 + 방출 전문 + 실행 출력** 셋을 다 실어야 근거가 된다.
★ **설정에 달린 칸은 다섯**이다(1절 둘 · 3절 하나 · 5절 둘) — 전부 `strictNullChecks` 하나에 달렸고, 방향도 하나다(**차이가 안 보이게 된다**).

## 언제 쓰고 언제 안 쓰나

| 이렇게 쓴다 | 이렇게 안 쓴다 |
|---|---|
| 콜백에 넘길 값은 **미리 지역 `const`** 로 꺼낸다 | 콜백 안에서 `b.v` 를 다시 읽는 것 |
| 판별 유니온은 **객체 자체**를 좁힌다 | 판별 칸만 뽑아 변수에 담는 것 — 연결이 끊긴다 |
| 인덱스는 **값을 꺼내** 쓴다(`const x = xs[i]`) | `xs[i]` 를 검사하고 또 `xs[i]` 를 쓰는 것 |
| 게터는 **한 번만 읽어** 쓴다 | `if (o.v)` 뒤에 `o.v` 를 다시 읽는 것 |
| 「믿어 주는 자리」는 **사람이 다시 본다** | 「컴파일 통과했으니 안전」 — 4절이 반례다 |

## 핵심 문장

1. **좁힘은 참조에 붙는다** — 호출식은 참조가 아니라 처음부터 좁혀지지 않는다.
2. **콜백 안에서 프로퍼티 좁힘은 무조건 풀린다** — `readonly` 도 못 막는다.
3. **변수 좁힘은 대입이 없으면 콜백에서도 산다** — `const` 냐 `let` 이냐가 아니다.
4. **함수 호출 뒤·`await` 뒤에는 유지되지만 보장이 아니다** — 런타임이 지워 버릴 수 있다.
5. **고치는 법은 지역 `const` 하나**다 — 단언은 고치는 법이 아니다.
6. **`strictNullChecks` 를 끄면 이 실험 자체가 안 보인다** — 규칙이 바뀌는 것이 아니다.

## 관련 자료

- [**12번 주제** — 좁히기](../12-narrowing/) — 좁히는 **수단**은 전부 그쪽. **12 → 15 는 한 사슬**이다.
- [**13번 주제** — 타입 가드와 타입 술어](../13-type-guards-and-predicates/) — 술어가 만든 좁힘도 같은 한계를 받는다.
- [**14번 주제** — 단언 시그니처 `asserts`](../14-assertion-signatures/) — 5절 38행이 「단언도 고치는 법이 아니다」를 보여 준다.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — `readonly` 가 런타임을 막지 않는다는 것은 그쪽이 정본이다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 판별 유니온의 설계는 그쪽.
- [목록의 **40번 주제**](../40-strict-null-checks-ripple/)(`strictNullChecks` 의 파급) — 6절이 그쪽의 맛보기다.
- [목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/)(인덱스·선택 프로퍼티 엄격 플래그) — `noUncheckedIndexedAccess` 를 켜면 2절의 인덱스 칸이 달라진다. **여기서는 안 켰다.**
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **06번** — 클로저가 환경을 붙드는 런타임 의미는 그쪽이 정본이다.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **13번** — 게터의 런타임 의미는 그쪽.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **39번** — `await` 가 중단·재개하는 지점은 그쪽.

## 용어 풀이

> **제어 흐름 분석(control flow analysis)** — 「이 줄에 도달하기까지의 경로」를 따라 참조의 타입을 좁히는 분석.\
> 경로가 끊기면 **선언 타입으로 되돌아간다.**

> **참조(reference)** — 좁힘이 붙는 대상. 변수 이름 · `o.v` 같은 프로퍼티 접근 · `xs[0]` 같은 상수 인덱스 접근.\
> **호출식은 참조가 아니다.**

> **믿어 주는 자리(unsound narrowing)** — 분석이 좁힘을 유지하지만 런타임이 지켜 주지 않는 자리.\
> 함수 호출 뒤 · `await` 뒤 · 게터 재접근.

> **즉시 실행 함수(IIFE)** — `(() => { … })()` 처럼 정의하자마자 부르는 함수.\
> 「지금 부른다」가 문법에 보여 **좁힘이 유지된다.**

## 더 들어가면

- **왜 콜백에서 풀리나** — 콜백은 **언제 불릴지 모른다.** `setTimeout` 에 실려 한참 뒤에 불릴 수도, 여러 번 불릴 수도 있다. 그 사이에 프로퍼티가 바뀔 수 있으므로 **프로퍼티 좁힘은 통째로 버린다.** 반대로 변수는 「그 함수 안에서 아무도 대입하지 않았다」를 **컴파일러가 스스로 확인할 수 있어서** 남겨 둔다 — 3절의 격자가 그 확인의 결과다.
- **왜 함수 호출 뒤에는 안 버리나** — 버리면 **거의 모든 코드가 다시 체크를 요구**하게 된다. `if (x) { log(); x.f() }` 같은 흔한 모양이 전부 에러가 난다. 그래서 TS 는 **의도적으로 unsound 한 선택**을 했다 — 4절이 그 대가를 실물로 보여 준다. 「타입 시스템이 틀렸다」가 아니라 「**여기까지만 책임진다**」는 선언이다.
- **`noUncheckedIndexedAccess` 를 켜면** — 2절의 인덱스 칸이 전부 `| undefined` 를 달고 나온다. 검사 뒤 좁힘의 모양도 달라진다. **이 배치에서는 안 켰다** — [목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/)다.
- **게터를 안전하게 쓰는 수** — 한 번 읽어 지역 `const` 에 담는다. 4절의 `afterGetter` 가 터진 것은 **같은 표현식을 두 번 읽었기** 때문이다. 5절의 고침이 그대로 적용된다.
- **판이 오르면** — 3절의 「대입이 없으면 산다」와 1절의 「즉시 실행 함수에서 산다」는 **구현의 경계**다. 넓어질 수도 좁아질 수도 있다 — **외우지 말고 다시 던져라.** 이 문서가 격자를 파일 셋으로 남겨 둔 이유다.
