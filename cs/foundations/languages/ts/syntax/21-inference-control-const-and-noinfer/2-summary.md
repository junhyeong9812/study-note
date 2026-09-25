# ts/syntax/21 — 추론 제어 — `const` 타입 매개변수·`NoInfer` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript 5.0 릴리스 노트 — `const` Type Parameters](https://devblogs.microsoft.com/typescript/announcing-typescript-5-0/#const-type-parameters) ·
> [TypeScript 5.4 릴리스 노트 — The `NoInfer` Utility Type](https://devblogs.microsoft.com/typescript/announcing-typescript-5-4/#the-noinfer-utility-type) ·
> [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 릴리스 노트는 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version (sh exit=0) =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 **5.0·5.4 기능이 7.0 에서 도는가는 외우지 않고 던져서 확인했다** — 1·2절이 그 결과다.
> 블록은 **옵션을 배너에 적힌 것만** 준 결과이고 `-t es2022 --strict` 를 **전부 명시**했다.
> **버전** — `const` 타입 매개변수는 **TS 5.0**, `NoInfer<T>` 는 **TS 5.4** 다. `as const` 는 TS 3.4 다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 배치가 쓰는 탐침 — 「컴파일러가 타입을 말하게 하는 법」

**추론된 타입은 눈에 안 보인다.** 그래서 이 갈래는 **일부러 틀린 주석을 달아 컴파일러가 답을 뱉게** 한다.

```text
  const probe: null = 무엇인가;
                      └─ 이 자리의 타입이 X 라면

  error TS####: Type 'X' is not assignable to type 'null'.   <- 실제 코드는 TS2322
                      ↑ 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ 이 주제에서는 **`TS2345` 가 결론인 자리가 많다** — 「막혀야 정상」이기 때문이다. 2절이 그렇다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★ 유니온 원소의 **순서**(`'"노랑" \| "빨강" \| "파랑"'`) | 5회 재실행 md5 동일 — **관찰이지 보장이 아니다** |
| **안 흔들린다** | `.d.ts` 전문 | 방출기의 고정 형식이다 |
| **★ 설정에 달렸다** | ★★★ 6절의 **`ex.21f.ts` 한 파일** — `--strict` 를 끄면 **추론 결과가 바뀐다** | 8절에 양쪽을 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **★ 부적용** | 방출 `.js` | ★★ **잴 것이 없다** — `const` 수식어도 `NoInfer` 도 **전부 타입 층**이다 |
| **안 잰 것** | `const` 타입 매개변수가 **검사 시간**에 주는 영향 | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 7절의 `tsc` 는 **진단이 0줄**이다 — 그 블록도 **명령과 종료 코드까지** 캡처했다.

## 한눈에 — 쉽게 말하면

**이 주제의 두 도구는 「고치는 도구」다. 고장부터 봐야 뜻이 선다.**

| 비유 | 실체 |
|---|---|
| 받아쓰기 하는 비서가 **「사과, 배」를 「과일」로 적는다** | [**19번 주제**](../19-generics-basics/) 2절의 고장 — 배열의 속이 넓어진다 |
| ★ 손님이 매번 **「그대로 적어 주세요」** 라고 말한다 | `as const` — **호출자**가 적는다 |
| ★★★ 비서의 **수첩에 「그대로 적기」라고 새겨 둔다** | `<const T>` — **정의자**가 적는다 |
| 비서가 **안 물어본 칸까지 보고 추측한다** | 두 자리에서 추론돼 유니온이 벌어진다 |
| ★★★ 그 칸에 **「여기는 보지 마」** 딱지를 붙인다 | `NoInfer<T>` — **추론 자리 하나를 죽인다** |

- ★★★ 한 줄로 — 「**`const` 는 넓어지는 것을 막고, `NoInfer` 는 엉뚱한 데서 추론되는 것을 막는다.**」
- ★★ 둘 다 **컴파일러가 이미 하고 있는 일을 끄는 도구**다. 그래서 **고장을 먼저 봐야** 한다.

```text
  ★★★ 추론 자리 — 어디서 추론되고 어디를 죽이나

  function light<C extends string>(colors: C[],  fallback: C): C
                                      └──┬──┘             └┬┘
                                    추론 자리 ①        추론 자리 ②

     light(["빨강","노랑"], "파랑")

       ①에서 C <- "빨강" | "노랑"
       ②에서 C <- "파랑"                 ← 여기도 후보가 된다
       ─────────────────────────
       합치면 C = "노랑" | "빨강" | "파랑"   ★ 조용히 통과한다 (고장)


  function light<C extends string>(colors: C[],  fallback: NoInfer<C>): C
                                      └──┬──┘             └────┬────┘
                                    추론 자리 ①            ★ 죽은 자리

       ①에서만 C <- "빨강" | "노랑"
       ②는 후보를 안 낸다 — 대신 검사만 받는다
       ─────────────────────────
       "파랑" 을 넣으면  TS2345   ★ 막힌다 (고침)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **[19](../19-generics-basics/) 의 고장을 무엇이 고치나** — 같은 줄을 다시 던져 `<const T>` 를 붙인다(1절).
2. **`NoInfer` 없이는 무엇이 조용히 통과하나** — ★★★ **고장을 먼저** 보이고 도구를 뒤에 둔다(2절).
3. **여러 자리에서 추론될 때 무엇이 이기나** — 네 가지 배치를 던져 본다(5절).

★★★ **19 → 20 → 21 은 한 사슬이고 여기가 급소다** — 「**추론을 언제 막나**」가 이 주제의 전부다.
★★ [**20번 주제**](../20-generic-constraints-and-defaults/)의 제약과 **싸우는 자리**가 6절이다.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 |
|---|---|---|
| ★★★ **`null` 탐침** | 컴파일러가 **계산한** 타입 인자 | **계산된 것** |
| ★★★ **`TS2345` 가 나는 것 자체** | 「막혀야 정상」인 자리가 막혔다 | 사실 |
| ★★ **`--declaration` 의 `.d.ts`** | 고침 전후를 **여러 줄 한꺼번에** | **적은 것** |
| ★ **부적용 — 방출 `.js`** | ★★ **잴 것이 없다** | `const` 수식어도 `NoInfer` 도 **방출에 아무 자국이 없다** |

★★ 마지막 줄이 [**20번 주제**](../20-generic-constraints-and-defaults/)와 같다 — 이 두 주제는 **순수 타입 층**이라 `.js` 창이 부적용이다.
「재 봤더니 같았다」가 아니라 **잴 것이 없다.**

비용 — 컴파일 여덟 번.

### (1) ★★★ 19 의 고장과 `<const T>` 의 고침 — 나란히

**언제 쓰나** — 「배열을 넘겼는데 리터럴 유니온이 아니라 `string[]` 이 나온다」일 때.

```ts
// ex.21a.ts
// 19 에서 본 고장과 그 고침 -- 같은 파일에 나란히 둔다
function keep<T>(x: T): T {
    return x;
}
function keepConst<const T>(x: T): T {
    return x;
}

const broken1: null = keep(["가", "나"]);
const fixed1: null = keepConst(["가", "나"]);

const broken2: null = keep({ mode: "auto", retry: 3 });
const fixed2: null = keepConst({ mode: "auto", retry: 3 });

function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}
function firstOfConst<const T>(xs: T[]): T {
    return xs[0]!;
}
const broken3: null = firstOf(["가", "나"]);
const fixed3: null = firstOfConst(["가", "나"]);

const scalarBroken: null = keep("가");
const scalarFixed: null = keepConst("가");

const already: null = keep(["가", "나"] as const);
console.log(broken1, fixed1, broken2, fixed2, broken3, fixed3, scalarBroken, scalarFixed, already);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21a.ts (tsc exit=1) =====
ex.21a.ts(9,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.21a.ts(10,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21a.ts(12,7): error TS2322: Type '{ mode: string; retry: number; }' is not assignable to type 'null'.
ex.21a.ts(13,7): error TS2322: Type '{ readonly mode: "auto"; readonly retry: 3; }' is not assignable to type 'null'.
ex.21a.ts(21,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21a.ts(22,7): error TS2322: Type '"가" | "나"' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.21a.ts(24,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.21a.ts(25,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.21a.ts(27,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 9행과 10행을 나란히 읽어라. **같은 인자 `["가","나"]`** 인데\
  `keep` 은 **`string[]`**, `keepConst` 는 **`readonly ["가", "나"]`** 다.\
  차이는 **`<T>` 냐 `<const T>` 냐** 하나뿐이다.
- ★★★ 12·13행이 객체 쪽이다. `{ mode: "auto", retry: 3 }` 가\
  **`{ mode: string; retry: number; }`** 에서 **`{ readonly mode: "auto"; readonly retry: 3; }`** 로 바뀐다.\
  **속성이 리터럴로 굳고 `readonly` 가 붙는다.**
- ★★ 21·22행 — 원소를 뽑는 꼴에서도 같다. `firstOf` 는 `string`, `firstOfConst` 는 **`"가" | "나"`** 다.
- ★★★ 24·25행이 **경계**다. **스칼라 인자는 둘 다 `"가"`** 다 — `const` 를 붙여도 **안 바뀐다.**\
  [**19번 주제**](../19-generics-basics/) 2절에서 본 대로 스칼라는 **원래 안 넓어진다.**\
  즉 **`<const T>` 가 고치는 것은 배열·객체 리터럴의 속**이다.
- ★ 27행 — 이미 `as const` 가 붙은 인자는 `keep` 으로도 `readonly ["가", "나"]` 다. **둘은 같은 결과에 이르는 두 길**이다(3절).

```text
  같은 인자, 수식어 하나 차이

  keep(["가","나"])        ->  string[]                        ★ 19 의 고장
  keepConst(["가","나"])   ->  readonly ["가", "나"]            ★ 21 의 고침

  keep({mode:"auto"})      ->  { mode: string; retry: number }
  keepConst({mode:"auto"}) ->  { readonly mode: "auto"; readonly retry: 3 }

  keep("가")               ->  "가"      ★ 스칼라는 원래 안 넓어진다
  keepConst("가")          ->  "가"      ★ const 를 붙여도 그대로
```

비용 — `readonly` 가 **반환 타입에 따라 나간다.** 호출자가 그 배열을 바꾸려 하면 막힌다(6절).

### (2) ★★★ `NoInfer` — 고장을 먼저 보고 도구를 본다

**언제 쓰나** — 「기본값 인자가 목록에 없는 값인데 조용히 통과한다」일 때.

```ts
// ex.21b.ts
// NoInfer -- 추론 자리를 하나 죽인다. 없을 때 무엇이 조용히 넘어가는지 먼저 본다
function lightNaive<C extends string>(colors: C[], fallback: C): C {
    return fallback;
}
function lightFixed<C extends string>(colors: C[], fallback: NoInfer<C>): C {
    return fallback;
}

const naive = lightNaive(["빨강", "노랑"], "파랑");
const p1: null = naive;

lightFixed(["빨강", "노랑"], "파랑");
const ok = lightFixed(["빨강", "노랑"], "노랑");
const p2: null = ok;

function fillNaive<T>(xs: T[], filler: T): T[] {
    return xs.map(() => filler);
}
function fillFixed<T>(xs: T[], filler: NoInfer<T>): T[] {
    return xs.map(() => filler);
}
const p3: null = fillNaive([1, 2], "빈칸");
fillFixed([1, 2], "빈칸");

const p4: null = lightNaive<"빨강" | "노랑">(["빨강"], "노랑");
console.log(p1, p2, p3, p4);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21b.ts (tsc exit=1) =====
ex.21b.ts(10,7): error TS2322: Type '"노랑" | "빨강" | "파랑"' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
ex.21b.ts(12,26): error TS2345: Argument of type '"파랑"' is not assignable to parameter of type '"노랑" | "빨강"'.
ex.21b.ts(14,7): error TS2322: Type '"노랑" | "빨강"' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
ex.21b.ts(22,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.21b.ts(22,36): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
ex.21b.ts(23,19): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
ex.21b.ts(25,7): error TS2322: Type '"노랑" | "빨강"' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **10행이 고장이다.** `lightNaive(["빨강","노랑"], "파랑")` 이 **에러 없이 통과**하고\
  `C` 가 **`"노랑" | "빨강" | "파랑"`** 으로 벌어진다.\
  「목록에 없는 색을 기본값으로 줬다」는 실수가 **조용히 넘어간다** — 오히려 **타입이 넓어져 맞아 버린다.**
- ★★★ **12행이 고침이다.** `fallback` 을 `NoInfer<C>` 로 감싸면 같은 호출이 **`TS2345`** 다 —\
  「Argument of type '"파랑"' is not assignable to parameter of type '"노랑" | "빨강"'.」\
  **`C` 는 첫 인자에서만 추론되고, 두 번째 자리는 검사만 받는다.**
- ★★ 14행 — 목록에 있는 값(`"노랑"`)은 통과한다. `C` 가 **`"노랑" | "빨강"`** 으로 **안 벌어진다.**
- ★★★ 22·23행이 같은 고장의 **더 나쁜 얼굴**이다.\
  `fillNaive([1,2], "빈칸")` 은 **두 진단**을 낸다 — 탐침이 `number[]` 라고 답하는 **동시에** 인자가 막힌다.\
  ★ 즉 이 꼴에서는 `NoInfer` 없이도 막히기는 한다. **`T` 가 스칼라로 굳은 뒤 두 번째 인자가 검사**되기 때문이다.\
  ★★ **그러므로 「`NoInfer` 가 없으면 항상 조용히 통과한다」는 틀린 요약**이다 —\
  **제약이 `string` 인 꼴(리터럴이 살아 유니온으로 합쳐지는 꼴)에서만** 조용해진다.
- ★★ 25행이 **`NoInfer` 없이 손으로 고치는 길**이다. `lightNaive<"빨강" | "노랑">(…)` 처럼 **꺾쇠를 적으면**\
  추론이 아예 안 일어나 벌어지지 않는다. 대신 **호출자가 매번 적어야** 한다.

> **`NoInfer<T>`** — 그 자리를 **추론 후보에서 뺀다**(TS 5.4). 검사는 그대로 받는다.\
> **하나 이상의 다른 자리에서 `T` 가 추론돼야** 쓸모가 있다.

비용 — 진단이 **한 자리 뒤로 밀린다.** 고장 난 인자가 아니라 **그 인자가 안 맞는다**는 메시지가 나온다.

### (3) ★★ `as const` 와 `<const T>` — 누가 적느냐

**언제 쓰나** — 둘 중 어느 것을 쓸지 고를 때.

```ts
// ex.21c.ts
// as const 는 호출자가 적고 const 타입 매개변수는 정의자가 적는다
function plain<T>(x: T): T {
    return x;
}
function defined<const T>(x: T): T {
    return x;
}

const byCaller: null = plain(["가", "나"] as const);
const byDefiner: null = defined(["가", "나"]);

const callerForgot: null = plain(["가", "나"]);
const definerAlways: null = defined(["가", "나"]);

const both: null = defined(["가", "나"] as const);

const source = ["가", "나"];
const fromVariable: null = defined(source);

const literalInVariable = ["가", "나"] as const;
const fromConstVariable: null = defined(literalInVariable);
console.log(byCaller, byDefiner, callerForgot, definerAlways, both, fromVariable, fromConstVariable);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21c.ts (tsc exit=1) =====
ex.21c.ts(9,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21c.ts(10,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21c.ts(12,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.21c.ts(13,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21c.ts(15,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21c.ts(18,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.21c.ts(21,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이고 전부 탐침이다.
- ★★★ 9행과 10행의 답이 **글자까지 같다** — `readonly ["가", "나"]`.\
  `plain(… as const)`(호출자가 적음)와 `defined([…])`(정의자가 적음)가 **같은 곳에 도착**한다.
- ★★★ 12행과 13행이 **차이가 드러나는 자리**다. **호출자가 `as const` 를 잊으면** `plain` 은 `string[]` 로 넓어지고\
  `defined` 는 **여전히** `readonly ["가", "나"]` 다. **정의자가 적으면 잊을 수가 없다.**
- ★★ 15행 — 둘을 겹쳐 써도 **결과가 같다.** 해롭지 않지만 **불필요**하다.
- ★★★ 18행이 **둘 다 못 고치는 자리**다. **변수에 담아 넘기면** `const` 타입 매개변수도 `string[]` 을 준다 —\
  값이 이미 넓어진 뒤이기 때문이다([**19번 주제**](../19-generics-basics/) 2절 18행).
- ★ 21행 — 변수 쪽에 `as const` 를 붙여 두면 살아난다. **넓어지기 전에 잡아야** 한다.

```text
  누가 적느냐 — 그리고 누가 잊을 수 있느냐

  as const        호출자가 적는다   ->  한 번이라도 잊으면 넓어진다 (12행)
  <const T>       정의자가 적는다   ->  호출자가 잊을 수 없다      (13행)
  변수에 담은 뒤   ★ 둘 다 못 고친다 ->  string[]                  (18행)
```

비용 — `<const T>` 는 **라이브러리 저자의 결정**이 된다. 호출자가 「넓히고 싶다」고 해도 되돌릴 수 없다.

### (4) ★★ `satisfies` 와의 관계 — 겹치는 곳과 안 겹치는 곳

**언제 쓰나** — 「`satisfies` 로 충분한가, `const` 타입 매개변수가 필요한가」를 고를 때.

```ts
// ex.21d.ts
// satisfies 는 검사만 하고 추론을 넓히지 않는다 -- const 타입 매개변수와 무엇이 겹치나
type Config = { mode: string; retry: number };

const asAnnotation: Config = { mode: "auto", retry: 3 };
const asSatisfies = { mode: "auto", retry: 3 } satisfies Config;
const asPlain = { mode: "auto", retry: 3 };

const p1: null = asAnnotation.mode;
const p2: null = asSatisfies.mode;
const p3: null = asPlain.mode;

function takeConst<const T extends Config>(c: T): T {
    return c;
}
const p4: null = takeConst({ mode: "auto", retry: 3 });

function takePlain<T extends Config>(c: T): T {
    return c;
}
const p5: null = takePlain({ mode: "auto", retry: 3 } satisfies Config);

const bad = { mode: "auto", retry: "셋" } satisfies Config;
console.log(p1, p2, p3, p4, p5, bad);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21d.ts (tsc exit=1) =====
ex.21d.ts(8,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21d.ts(9,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21d.ts(10,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21d.ts(15,7): error TS2322: Type '{ readonly mode: "auto"; readonly retry: 3; }' is not assignable to type 'null'.
ex.21d.ts(20,7): error TS2322: Type '{ mode: string; retry: number; }' is not assignable to type 'null'.
ex.21d.ts(22,29): error TS2322: Type 'string' is not assignable to type 'number'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 8·9·10행의 답이 **셋 다 `string`** 이다. `Config` 의 `mode` 가 `string` 으로 선언돼 있으니\
  주석을 달든 `satisfies` 를 쓰든 그냥 두든 **속성 하나를 읽으면 `string`** 이다.\
  ★ **`satisfies` 는 리터럴을 지키는 도구가 아니다** — 여기서는 `asPlain` 과 답이 같다.
- ★★ `satisfies` 가 하는 일은 **22행**이다. `{ mode: "auto", retry: "셋" }` 이 `TS2322` 로 막힌다 —\
  **검사는 하되 타입은 안 바꾼다**(목록의 **29번 주제**).
- ★★★ 15행이 대비다. `takeConst({ mode: "auto", retry: 3 })` 가 **`{ readonly mode: "auto"; readonly retry: 3; }`** 다 —\
  **`const` 타입 매개변수만이 속을 리터럴로 굳힌다.**
- ★★ 20행 — `satisfies` 를 붙여 넘겨도 `takePlain` 은 **`{ mode: string; retry: number; }`** 다.\
  **`satisfies` 로는 추론을 못 좁힌다.**
- ★ 즉 둘은 **하는 일이 다르다** — `satisfies` 는 **검사**, `const` 타입 매개변수는 **추론 제어**다. 같이 쓸 수 있다.

### (5) ★★ 추론 자리가 여럿일 때 무엇이 이기나

**언제 쓰나** — 「어느 인자가 타입을 정했는지 모르겠다」일 때.

```ts
// ex.21e.ts
// 추론 자리가 여럿일 때 -- 무엇이 이기나
declare function two<T>(a: T, b: T): T;
const p1: null = two("가", "나");
const p2: null = two(1, "가");

declare function fromReturn<T>(x: T): T[];
const p3: string[] = fromReturn("가");
const p4: null = fromReturn("가");

declare function viaCallback<T>(seed: T, f: (x: T) => void): T;
const p5: null = viaCallback(1, (x) => {
    const inner: null = x;
    console.log(inner);
});

declare function callbackFirst<T>(f: () => T, fallback: T): T;
const p6: null = callbackFirst(() => 1, "가");

declare function killSecond<T>(a: T, b: NoInfer<T>): T;
killSecond(1, "가");
const p7: null = killSecond<number | string>(1, "가");
console.log(p1, p2, p3, p4, p5, p6, p7);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21e.ts (tsc exit=1) =====
ex.21e.ts(3,7): error TS2322: Type '"가" | "나"' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.21e.ts(4,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.21e.ts(4,25): error TS2345: Argument of type '"가"' is not assignable to parameter of type '1'.
ex.21e.ts(8,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.21e.ts(11,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.21e.ts(12,11): error TS2322: Type 'number' is not assignable to type 'null'.
ex.21e.ts(17,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.21e.ts(17,41): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
ex.21e.ts(20,15): error TS2345: Argument of type '"가"' is not assignable to parameter of type '1'.
ex.21e.ts(21,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **열 건**이다.
- ★★ 3행 — `two("가", "나")` 는 **`"가" | "나"`** 다. 두 자리가 **합쳐진다**(2절의 고장과 같은 기제다).
- ★★★ 4행이 다르다. `two(1, "가")` 는 **`1`** 이고 **두 번째 인자가 `TS2345`** 로 막힌다.\
  **합칠 수 있으면 합치고, 못 합치면 첫 후보가 이기고 나머지는 검사 대상**이 된다.
- ★★ 8행 — `const p3: string[] = fromReturn("가");` 는 **조용하다.** 반환 자리에 문맥이 있어도\
  **인자에서 온 추론이 먼저**다(`fromReturn("가")` 는 `string[]`).
- ★★ 11·12행 — 콜백의 매개변수 `x` 는 **`number`** 로 채워져 들어온다. **`seed` 에서 이미 정해진 뒤** 콜백이 문맥을 받는다.
- ★★★ 17행이 뜻밖이다. `callbackFirst(() => 1, "가")` 에서 **`T` 가 `number`** 가 되고 `"가"` 가 막힌다 —\
  **콜백의 반환 타입도 추론 후보**이고, 여기서는 그쪽이 먼저 쓰였다.
- ★★ 20·21행 — `NoInfer` 로 두 번째 자리를 죽이면 `killSecond(1, "가")` 가 막히고,\
  꺾쇠로 `<number | string>` 을 적으면 **둘 다 통과**한다. **명시가 모든 추론을 이긴다**([**19번 주제**](../19-generics-basics/) 1절).

```text
  실측한 우선순위 (이 판의 관찰)

  명시한 꺾쇠            >  모든 추론              (21행)
  인자에서 온 추론        >  반환 자리의 문맥        ( 8행)
  합칠 수 있으면 합친다   ->  "가" | "나"            ( 3행)
  못 합치면 첫 후보가 이김 ->  1, 나머지는 TS2345    ( 4행)
  콜백의 반환도 후보다    ->  number, "가" 가 막힘   (17행)
  NoInfer 로 죽인 자리    ->  후보에서 빠진다        (20행)
```

★★★ 이것은 **이 판의 관찰**이다 — 「명세가 보장한다」로 적지 마라. 규칙 이름을 외우지 말고 **던져서 확인하는 습관**이 답이다.

### (6) ★★★ 언제 쓰지 말아야 하나 — 그리고 제약과 싸울 때

**언제 쓰나** — `<const T>` 를 달기 **전에** 읽을 절이다.

```ts
// ex.21f.ts
// const 타입 매개변수를 안 쓸 자리 -- readonly 가 새어 나가고, 변수 인자에는 아무 일도 안 일어난다
function needsMutable<const T extends string[]>(xs: T): T {
    return xs;
}
const p1: null = needsMutable(["가", "나"]);

function needsReadonly<const T extends readonly string[]>(xs: T): T {
    return xs;
}
const p2: null = needsReadonly(["가", "나"]);

function sortIt<const T extends readonly number[]>(xs: T): number {
    xs.sort();
    return xs.length;
}

function wideOnPurpose<const T>(x: T): T[] {
    return [x];
}
const list = wideOnPurpose("가");
list.push("나");

declare function idConst<const T>(x: T): T;
declare const runtime: string;
const p3: null = idConst(runtime);

declare function idPlain<T>(x: T): T;
const p4: null = idPlain(["가", "나"] as const);
console.log(p1, p2, p3, p4, sortIt, list);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.21f.ts (tsc exit=1) =====
ex.21f.ts(5,7): error TS2322: Type '["가", "나"]' is not assignable to type 'null'.
ex.21f.ts(10,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21f.ts(13,8): error TS2339: Property 'sort' does not exist on type 'T'.
ex.21f.ts(21,11): error TS2345: Argument of type '"나"' is not assignable to parameter of type '"가"'.
ex.21f.ts(25,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21f.ts(28,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 5행이 **가장 뜻밖의 줄**이다. `const T extends string[]`(**가변** 배열 제약)에 `["가","나"]` 를 주면\
  결과가 **`["가", "나"]`** 다 — `readonly` 가 **붙지 않은** 리터럴 튜플이다.\
  ★★ 즉 **`const` 가 제약과 싸우다 지는 것이 아니라, 제약에 맞게 `readonly` 를 뺀다.**\
  「제약을 어겨서 에러가 난다」고 예상했다면 **틀린다** — 던져야 안다.
- ★★ 10행 — 제약이 `readonly string[]` 이면 `readonly ["가", "나"]` 가 그대로 나온다.
- ★★ 13행 — `xs.sort()` 가 **`TS2339`** 다. **제약이 `readonly number[]` 라 `sort` 가 없다**([**20번 주제**](../20-generic-constraints-and-defaults/) 1절).\
  `const` 와 무관하게 **제약이 정하는 것**이다.
- ★★★ 21행이 **진짜 「쓰지 마라」 사례**다. `wideOnPurpose("가")` 의 반환이 `"가"[]` 라서\
  `list.push("나")` 가 **`TS2345`** 다 — **`const` 가 반환 타입까지 좁혀 호출자를 가둔다.**
- ★★ 25행 — **변수 인자에는 아무 일도 안 일어난다.** `idConst(runtime)` 이 `string` 이다.\
  **`const` 타입 매개변수는 「리터럴을 직접 적은 호출」에만 값을 낸다.**
- ★ 28행 — 호출자가 `as const` 를 쓰면 평범한 `<T>` 로도 `readonly ["가", "나"]` 다. **정의자가 꼭 달아야 하는 건 아니다.**

### (7) ★★ 두 번째 창 — `.d.ts` 가 고침 전후를 한 번에

```ts
// ex.21g.ts
// 두 번째 창 -- const 타입 매개변수와 NoInfer 의 결과를 .d.ts 가 글자로 적어 준다
export function keep<T>(x: T): T {
    return x;
}
export function keepConst<const T>(x: T): T {
    return x;
}
export function light<C extends string>(colors: C[], fallback: NoInfer<C>): C {
    return fallback;
}
export function lightNaive<C extends string>(colors: C[], fallback: C): C {
    return fallback;
}

export const plainArray = keep(["가", "나"]);
export const constArray = keepConst(["가", "나"]);
export const plainObject = keep({ mode: "auto", retry: 3 });
export const constObject = keepConst({ mode: "auto", retry: 3 });
export const fixed = light(["빨강", "노랑"], "노랑");
export const naive = lightNaive(["빨강", "노랑"], "파랑");
```

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d21g ex.21g.ts (tsc exit=0) =====
===== 방출된 ex.21g.d.ts =====
export declare function keep<T>(x: T): T;
export declare function keepConst<const T>(x: T): T;
export declare function light<C extends string>(colors: C[], fallback: NoInfer<C>): C;
export declare function lightNaive<C extends string>(colors: C[], fallback: C): C;
export declare const plainArray: string[];
export declare const constArray: readonly ["가", "나"];
export declare const plainObject: {
    mode: string;
    retry: number;
};
export declare const constObject: {
    readonly mode: "auto";
    readonly retry: 3;
};
export declare const fixed: "노랑" | "빨강";
export declare const naive: "노랑" | "빨강" | "파랑";
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 종료 코드가 **`0`** 이고 진단이 **0줄**인데 **고침 전후가 나란히** 글자로 나왔다.
- ★★ `plainArray: string[]` ↔ `constArray: readonly ["가", "나"]` · `plainObject` ↔ `constObject` 가 **1·4절의 결론 그대로**다.
- ★★★ 마지막 두 줄이 2절의 고장을 **가장 짧게** 보여 준다 —\
  `fixed: "노랑" | "빨강"`(`NoInfer` 를 쓴 쪽)와 `naive: "노랑" | "빨강" | "파랑"`(안 쓴 쪽).\
  **한 글자가 아니라 한 항목이 늘어나 있다.**
- ★★ `.d.ts` 가 `const` 수식어와 `NoInfer<C>` 를 **적은 그대로** 남긴다 — 계산하지 않는다([**16번 주제**](../16-function-types-and-overloads/)).
- ★ **두 창의 판정** — 값 하나를 정확히 읽을 때는 **탐침**(계산된 것), **고침 전후를 훑을 때는 `.d.ts`**.\
  [**19번 주제**](../19-generics-basics/) 7절에서 `.d.ts` 가 `"가"` 로 이스케이프한 전례가 있으니 **글자를 근거로 쓸 때는 탐침**이다.

### (8) ★★★ `strict` 대조 — 추론 결과가 바뀌는 파일이 있다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.21a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.21b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.21c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.21d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.21e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.21f.ts    exit 1 = exit 1 · ★ 출력이 다르다
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict false ex.21f.ts (tsc exit=1) =====
ex.21f.ts(5,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.21f.ts(10,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.21f.ts(13,8): error TS2339: Property 'sort' does not exist on type 'T'.
ex.21f.ts(21,11): error TS2345: Argument of type '"나"' is not assignable to parameter of type '"가"'.
ex.21f.ts(25,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.21f.ts(28,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
```

- ★★ 여섯 파일 중 **`ex.21f.ts` 하나만** 갈린다.
- ★★★ 갈린 자리가 **이 주제의 핵심 칸**이다. 6절 5행의 `needsMutable(["가","나"])` 가\
  켠 판에서는 **`["가", "나"]`**(리터럴 튜플), 끈 판에서는 **`string[]`** 이다.\
  **`--strict` 를 끄면 `const` 타입 매개변수의 효과가 그 자리에서 사라진다.**
- ★★★ 나머지 다섯 줄은 **글자까지 같다** — 1·2·3·4·5절의 결론은 `strict` 와 **무관**하다.
- ★ 그러므로 **「`const` 타입 매개변수는 설정과 무관하다」는 틀렸다.** 제약이 **가변 배열**일 때만 갈린다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function keep<const T>(x: T): T { … }                 ★ 5.0 — 정의자가 적는다
  keep(["가","나"] as const)                            ★ 3.4 — 호출자가 적는다
  function light<C extends string>(c: C[], f: NoInfer<C>): C { … }   ★ 5.4
  const x = { … } satisfies Config;                     ★ 4.9 — 검사만 한다

  function f<const T extends string[]>(xs: T): T { … }          ★ readonly 가 빠진다 (6절)
  function f<const T extends readonly string[]>(xs: T): T { … }  ★ readonly 가 남는다
```

**규칙 불릿**

- ★★★ **`<const T>` 는 배열·객체 리터럴의 속을 굳힌다** — `readonly` + 리터럴(1절 10·13행).
- ★★★ **스칼라 인자에는 아무 일도 안 한다** — 원래 안 넓어지기 때문이다(1절 24·25행).
- ★★★ **변수 인자에도 아무 일도 안 한다** — 값이 이미 넓어진 뒤다(3절 18행 · 6절 25행).
- ★★★ **`NoInfer<T>` 는 그 자리를 추론 후보에서 뺀다** — 검사는 그대로 받는다(2절 12행).
- ★★ **`NoInfer` 가 없으면 「항상」 조용히 통과하는 것은 아니다** — 합쳐질 수 있는 꼴에서만 그렇다(2절 10행 대 22행).
- ★★ **`as const` 는 호출자가, `<const T>` 는 정의자가 적는다** — 결과는 같은 곳에 도착한다(3절 9·10행).
- ★★ **`satisfies` 는 추론을 안 좁힌다** — 검사만 한다(4절 8·9·20행).
- ★★ **명시한 꺾쇠가 모든 추론을 이긴다**(5절 21행).
- ★★ **콜백의 반환 타입도 추론 후보다**(5절 17행).
- ★★★ **제약이 가변 배열이면 `const` 가 `readonly` 를 뺀다** — 에러가 아니다(6절 5행). ★ 그리고 **`--strict` 를 끄면 그 자리가 갈린다**(8절).
- ★ **`const` 는 반환 타입까지 좁혀 호출자를 가둘 수 있다**(6절 21행).

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) NoInfer 자리에 목록 밖 값   ->  TS2345  Argument of type '"파랑"' is not assignable to
                                           parameter of type '"노랑" | "빨강"'.
2) const 로 좁힌 배열에 push   ->  TS2345  Argument of type '"나"' is not assignable to
                                           parameter of type '"가"'.
3) readonly 제약에 sort        ->  TS2339  Property 'sort' does not exist on type 'T'.
```

## 어디서 틀리나

- ★★★ 「**`<const T>` 를 붙이면 뭐든 리터럴로 굳겠지**」 — **스칼라와 변수 인자에는 아무 일도 안 한다**(1절 24행 · 6절 25행).
- ★★★ 「**`NoInfer` 가 없으면 항상 조용히 통과하겠지**」 — 아니다. **합쳐질 수 있는 꼴에서만** 조용하다(2절 10행 대 22행).
- ★★★ 「**`const T extends string[]` 는 제약을 어겨서 에러가 나겠지**」 — **`readonly` 를 빼고 통과한다**(6절 5행).
- ★★ 「**`satisfies` 로도 리터럴이 지켜지겠지**」 — **안 지켜진다**(4절 8·9·20행). 하는 일이 다르다.
- ★★ 「**`as const` 와 `<const T>` 는 같은 것이겠지**」 — 결과는 같아도 **누가 적느냐가 다르다**(3절 12·13행).
- ★★ 「**반환 자리의 문맥이 인자보다 세겠지**」 — **인자가 먼저**다(5절 8행).
- ★★ 「**콜백 반환은 추론에 안 쓰이겠지**」 — **쓰인다**(5절 17행).
- ★ 「**`const` 는 공짜겠지**」 — `readonly` 가 **반환으로 새어 나가** 호출자를 가둔다(6절 21행).
- ★ 「**추론 규칙은 `strict` 와 무관하겠지**」 — **한 자리가 갈린다**(8절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(5.0)** | `<const T>` 가 배열·객체 리터럴의 속을 굳힌다 | 1절 10·13행 |
| **언어 보장(5.4)** | `NoInfer<T>` 가 그 자리를 추론 후보에서 뺀다 | 2절 12행 |
| **언어 보장** | 명시한 꺾쇠가 **모든 추론을 이긴다** | 5절 21행 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ **추론 우선순위 전반** — 합치기·첫 후보·콜백 반환 | 5절 3·4·8·17행 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | ★★★ `const T extends string[]` 가 **`readonly` 를 뺀다** | 6절 5행 |
| **★ 설정에 달림** | ★★★ **그 자리 하나** — `--strict` 를 끄면 `string[]` 이 된다 | 8절 |
| **★ 부적용 — 방출된 JS** | ★★ **잴 것이 없다** — 둘 다 순수 타입 층이다 | 0절 |
| **`.d.ts` 방출** | `const` 수식어와 `NoInfer<C>` 를 **적은 그대로** 남긴다 | 7절 |
| **이 판의 관찰** | 유니온 원소의 **순서** | 5회 재실행 md5 동일 — **관찰이지 보장이 아니다** |
| **이 판의 관찰** | 진단 **문구** 전문 | 코드(`TS2345`·`TS2339`·`TS2322`)가 더 오래 간다 |
| **안 잰 것** | `const` 타입 매개변수의 **검사 시간** | 재지 않았다 |

★★★ **이 주제는 「이 판의 관찰」 칸이 유난히 두껍다.** 추론 우선순위는 릴리스 노트에 다 적혀 있지 않다 —
**규칙 이름을 외우는 것보다 탐침 한 줄을 던지는 쪽이 빠르고 정확하다.**

## 언제 쓰고 언제 안 쓰나

| `<const T>` 를 쓴다 | 안 쓴다 |
|---|---|
| 호출자가 **리터럴을 직접 적는** API(설정 객체·라우트 목록·상태 키) | 인자가 **변수로 들어오는** API — 아무 일도 안 한다(6절 25행) |
| 그 리터럴로 **다른 타입을 계산**해야 할 때(`keyof`·템플릿 리터럴) | 반환 배열을 호출자가 **바꿔야** 할 때 — `readonly` 가 새어 나간다(6절 21행) |
| 호출자가 `as const` 를 **잊으면 곤란할 때**(3절 12행) | 호출자가 **넓히고 싶을 수도** 있을 때 — 되돌릴 수 없다 |

| `NoInfer<T>` 를 쓴다 | 안 쓴다 |
|---|---|
| 한 자리는 **목록을 정하고** 다른 자리는 **그 목록에 속해야** 할 때 | 추론 자리가 **하나뿐**일 때 — 죽일 것이 없다 |
| 기본값·대비값이 **목록 밖으로 새면 안 될** 때(2절) | 유니온이 벌어지는 것이 **의도일** 때 |
| ★ 꺾쇠를 호출자가 **매번 적기 싫을** 때(2절 25행의 대안) | 진단이 **한 자리 뒤로 밀리는 것**이 혼란스러울 때 |

## 핵심 문장

1. **두 도구는 고치는 도구다** — 고장을 먼저 보지 않으면 어디에 쓸지 모른다.
2. **`<const T>` 는 배열·객체 리터럴의 속을 굳힌다** — 스칼라와 변수 인자에는 아무 일도 안 한다.
3. **`NoInfer<T>` 는 추론 자리 하나를 죽인다** — 검사는 그대로 받는다.
4. **`as const` 는 호출자가, `<const T>` 는 정의자가 적는다** — 잊을 수 있느냐가 갈린다.
5. **`satisfies` 는 검사만 한다** — 추론을 좁히지 않는다.
6. **제약이 가변 배열이면 `const` 가 `readonly` 를 뺀다** — 그리고 그 자리가 `strict` 에 달려 있다.

## 관련 자료

- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — ★★★ **1절이 고치는 고장이 그쪽 2절**이다. **먼저 읽어라.**
- [**20번 주제** — 제네릭 제약과 기본 타입 인자](../20-generic-constraints-and-defaults/) — 6절이 **그쪽의 제약과 싸우는** 자리다.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — 3절의 호출자 쪽 길은 그쪽이 정본이다.
- [**18번 주제** — `this` 매개변수 타입](../18-this-parameter-types/) — **같은 배치의 첫 주제.**
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — 7절의 `.d.ts` 가 별칭을 안 펴는 성질은 그쪽.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — `readonly` 가 **런타임을 막지 않는다**는 사실은 그쪽.
- 목록의 **29번 주제**(`satisfies`) — 4절의 정본. 여기서는 **추론 제어와의 관계**까지만.
- 목록의 **22번 주제**(`keyof` 와 인덱스 접근 타입) · 목록의 **27번 주제**(템플릿 리터럴 타입) — `const` 로 굳힌 리터럴을 **써먹는** 자리.
- 목록의 **46번 주제**(가변 튜플 타입) — 1절의 `readonly ["가", "나"]` 가 튜플이라는 사실이 거기서 값을 낸다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**([제네릭 선언](../../../java/syntax/17-generic-declarations/)) — ★ Java 에는 **추론 제어 장치가 없다.** 꺾쇠를 적거나 안 적거나뿐이다.

## 용어 풀이

> **`const` 타입 매개변수(`<const T>`)** — TS 5.0.\
> 그 매개변수로 추론될 때 **`as const` 를 붙인 것처럼** 취급한다. **배열·객체 리터럴의 속**에만 효과가 있다.

> **`NoInfer<T>`** — TS 5.4.\
> 그 자리를 **추론 후보에서 뺀다.** 검사는 그대로 받는다 — 즉 **「읽지만 말하지는 않는 자리」** 다.

> **추론 자리(inference site)** — 타입 매개변수가 나타나 **후보를 낼 수 있는** 위치.\
> 인자·콜백의 반환 타입 등. `NoInfer` 는 그중 하나를 죽인다.

> **넓히기(widening)** — 리터럴 타입이 기반 타입으로 올라가는 것(`"가"` → `string`).\
> **변경 가능한 자리**에서 일어난다 — 그래서 `readonly` 를 붙이면 멈춘다([**19번 주제**](../19-generics-basics/) 더 들어가면).

## 더 들어가면

- **왜 `const` 를 「기본」으로 안 했나** — 모든 추론을 리터럴로 굳히면 **반환 타입에 `readonly` 가 대량으로 새어 나간다**(6절 21행). 기존 코드의 호출자가 그 배열을 바꾸고 있었다면 전부 깨진다. 그래서 TS 는 **정의자가 자리마다 고르게** 했다 — `<const T>` 는 **옵트인**이다.
- **`NoInfer` 는 어떻게 만들어졌나** — 5.4 전에는 `T & {}`·조건부 타입 같은 **트릭**으로 흉내 냈다. 그 트릭들은 진단 문구를 망가뜨리거나 다른 추론까지 건드렸다. 5.4 가 **내장 유틸리티**로 올린 것은 「추론 후보에서 빼기」가 **컴파일러 내부의 개념**이었기 때문이다 — 사용자 코드로는 정확히 표현할 수 없었다. 이 배치에서는 **트릭 쪽을 안 던졌다.**
- **6절 5행이 왜 에러가 아닌가** — `const T extends string[]` 에서 `readonly ["가","나"]` 는 제약 `string[]` 을 **만족하지 못한다**(가변 배열이 아니다). 그때 컴파일러는 **에러를 내는 대신 `const` 의 효과를 부분적으로 물린다** — 리터럴 원소는 남기고 `readonly` 만 뺀다. 결과가 `["가", "나"]` 다. ★★ **이 동작은 릴리스 노트의 한 줄보다 던져 보는 쪽이 빠르고, `--strict` 를 끄면 또 달라진다**(8절). **「tsc 가 이렇게 한다」이지 「명세가 보장한다」가 아니다.**
- **추론 우선순위를 외울 수 있나** — 5절의 표는 **이 판의 관찰**이다. TS 컴파일러 안에는 추론 후보마다 **우선순위 값**이 있고 그 목록은 공개 문서에 정리돼 있지 않다. 실무에서 쓸 수 있는 규칙은 둘뿐이다 — ① **명시가 모든 것을 이긴다** ② **모르겠으면 탐침을 한 줄 던진다.** 나머지는 자리마다 확인한다.
- **`const` 와 `satisfies` 를 같이** — 4절에서 둘이 **하는 일이 다르다**는 것을 봤다. 실제 라이브러리에서는 `<const T extends Config>` 로 받고 호출자가 `satisfies` 없이 리터럴을 적는 꼴이 흔하다 — **정의자가 둘 다 책임지는 설계**다. 그 설계의 대가(호출자가 넓히지 못함)는 3절 비용 줄에 있다.
