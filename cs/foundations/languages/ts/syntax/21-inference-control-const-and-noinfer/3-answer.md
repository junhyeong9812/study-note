# ts/syntax/21 — 추론 제어 — `const` 타입 매개변수·`NoInfer` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문은 `tsc` **7.0.2** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 7번은 **진단이 0줄인 것이 결론**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★ 이 주제에서는 **`TS2345` 가 나는 것 자체가 답인 자리**가 많다 — 「막혀야 정상」이기 때문이다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `string[]` → **`readonly ["가", "나"]`** — 고치는 것은 **속**이다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 9 | `keep(["가","나"])` | `string[]` — ★ [**19번 주제**](../19-generics-basics/) 2절의 고장 |
| 10 | ★★★ `keepConst(["가","나"])` | **`readonly ["가", "나"]`** |
| 12 | `keep({ mode:"auto", retry:3 })` | `{ mode: string; retry: number; }` |
| 13 | ★★★ `keepConst({ … })` | **`{ readonly mode: "auto"; readonly retry: 3; }`** |
| 21·22 | `firstOf` · `firstOfConst` | `string` · **`"가" \| "나"`** |
| 24·25 | ★★★ `keep("가")` · `keepConst("가")` | **둘 다 `"가"`** — 스칼라는 안 바뀐다 |
| 27 | `keep([…] as const)` | `readonly ["가", "나"]` — 호출자가 고친 쪽 |

- ★★★ 9·10행과 12·13행이 이 문항의 전부다. **인자는 글자까지 같고 수식어 하나만 다르다.**\
  `<const T>` 는 그 자리로 추론될 때 **`as const` 를 붙인 것처럼** 취급한다.
- ★★★ 24·25행이 **경계이자 흔한 오해의 자리**다. **스칼라에는 아무 일도 안 한다** —\
  [**19번 주제**](../19-generics-basics/) 2절에서 봤듯 스칼라 리터럴은 **원래 안 넓어진다.**\
  그러므로 **`<const T>` 가 고치는 것은 배열·객체 리터럴의 속**이다.
- ★★ 22행이 실용적으로 크다. 원소를 뽑는 꼴(`firstOfConst`)에서 `"가" | "나"` 가 나오면\
  그 값으로 `keyof`·템플릿 리터럴 타입을 계산할 수 있다([목록의 **22번 주제**](../22-keyof-and-indexed-access-types/)·목록의 **27번 주제**).
- ★ 27행이 3번의 예고다 — **같은 곳에 이르는 두 길**이다.

### 2. ★★★ **안 막힌다** — `C` 가 `"노랑" | "빨강" | "파랑"` 으로 벌어진다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 9·10 | ★★★ `lightNaive(["빨강","노랑"], "파랑")` | **통과** · `C` = **`"노랑" \| "빨강" \| "파랑"`** |
| 12 | ★★★ `lightFixed(["빨강","노랑"], "파랑")` | **`TS2345`** — 「not assignable to parameter of type `'"노랑" \| "빨강"'`」 |
| 14 | `lightFixed(["빨강","노랑"], "노랑")` | `"노랑" \| "빨강"` — 안 벌어진다 |
| 22 | ★★ `fillNaive([1,2], "빈칸")` | 탐침 `number[]` + **`TS2345`** — `NoInfer` 없이도 막힌다 |
| 23 | `fillFixed([1,2], "빈칸")` | `TS2345` |
| 25 | `lightNaive<"빨강" \| "노랑">(…)` | `"노랑" \| "빨강"` — **꺾쇠로 손수 고친 것** |

- ★★★ 9·10행이 고장이다. `fallback` 자리도 **추론 후보**라서 `"파랑"` 이 `C` 에 들어간다.\
  그 결과 `C` 가 넓어지고 **실수가 오히려 타입에 맞아 버린다.** 진단이 **하나도 안 난다.**
- ★★★ 12행이 고침이다. `NoInfer<C>` 는 그 자리를 **추론 후보에서 뺀다** — 검사는 그대로 받는다.\
  그래서 `C` 가 첫 인자에서만 `"노랑" | "빨강"` 으로 정해지고 `"파랑"` 이 막힌다.
- ★★★ 22행이 **브리핑 수준의 요약을 뒤집는 자리**다.\
  「`NoInfer` 가 없으면 조용히 통과한다」는 **항상 참이 아니다** —\
  `fillNaive<T>` 는 제약이 없어 `T` 가 **`number` 로 굳고**, 그 뒤 `"빈칸"` 이 검사에서 막힌다.\
  ★★ **조용해지는 것은 「합쳐질 수 있는 꼴」**(제약이 `string` 이라 리터럴들이 유니온으로 모이는 꼴)**뿐**이다.
- ★★ 25행이 `NoInfer` 없이 사는 길이다 — **꺾쇠를 호출자가 적는다.** 대가는 **매번 적어야** 한다는 것이다.

### 3. ★★ 같다 — 갈리는 것은 「**잊을 수 있느냐**」다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 9 | `plain([…] as const)` — 호출자가 적음 | `readonly ["가", "나"]` |
| 10 | `defined([…])` — 정의자가 적음 | `readonly ["가", "나"]` — ★ **글자까지 같다** |
| 12 | ★★★ `plain([…])` — 호출자가 **잊음** | **`string[]`** |
| 13 | ★★★ `defined([…])` | **`readonly ["가", "나"]`** — 잊을 수가 없다 |
| 15 | 둘 다 씀 | `readonly ["가", "나"]` — 해롭지 않지만 **불필요** |
| 18 | ★★★ `defined(source)` — **변수** | **`string[]`** — 둘 다 못 고친다 |
| 21 | `defined(literalInVariable)` — `as const` 변수 | `readonly ["가", "나"]` |

- ★★★ 12·13행이 이 문항의 답이다. **결과가 같을 때는 같고, 갈릴 때는 「호출자가 잊었을 때」 갈린다.**\
  `<const T>` 를 달면 **호출자는 잊을 수가 없다.**
- ★★★ 18행이 **둘 다 못 고치는 자리**다. `const source = ["가","나"];` 의 시점에서 **이미 `string[]`** 이므로\
  함수에 넘길 때는 넓힐 것도 없다. **넓어지기 전에 잡아야** 한다([**19번 주제**](../19-generics-basics/) 2절 18행).
- ★ 21행이 그 고침이다 — 변수 쪽에 `as const` 를 붙인다.

### 4. ★★★ **안 지킨다** — 셋 다 `string` 이다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 8 | `asAnnotation.mode`(타입 주석) | `string` |
| 9 | ★★★ `asSatisfies.mode`(`satisfies`) | **`string`** |
| 10 | `asPlain.mode`(그냥 둠) | `string` |
| 15 | ★★★ `takeConst({ … })` | **`{ readonly mode: "auto"; readonly retry: 3; }`** |
| 20 | `takePlain({ … } satisfies Config)` | `{ mode: string; retry: number; }` |
| 22 | `{ mode:"auto", retry:"셋" } satisfies Config` | `TS2322` — ★ **검사는 한다** |

- ★★★ 8·9·10행이 셋 다 `string` 인 이유는 **`Config` 의 `mode` 가 `string` 으로 선언돼 있기 때문**이다.\
  `satisfies` 는 「이 리터럴이 `Config` 를 만족하나」만 확인하고 **타입을 바꾸지 않는다.**\
  ★ 여기서 `asPlain` 과 답이 같다는 것이 「**`satisfies` 는 리터럴을 지키는 도구가 아니다**」의 증거다.
- ★★ 22행이 `satisfies` 의 진짜 일이다 — **오타·타입 불일치를 잡는다.** 그것이 전부다(목록의 **29번 주제**).
- ★★★ 15행과 20행을 나란히 보라. **`const` 타입 매개변수만이 속을 리터럴로 굳힌다.**\
  `satisfies` 를 붙여 넘겨도 20행은 여전히 넓다.
- ★ 그러므로 둘은 **하는 일이 다르고 같이 쓸 수 있다** — `satisfies` 는 검사, `<const T>` 는 추론 제어다.

### 5. ★★★ **`"가" | "나"`** 대 **`1`** — 합칠 수 있으면 합치고, 못 합치면 첫 후보가 이긴다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 3 | `two("가","나")` | **`"가" \| "나"`** — 두 자리가 합쳐진다 |
| 4 | ★★★ `two(1,"가")` | **`1`** + 두 번째 인자 `TS2345` — 못 합치면 첫 후보가 이긴다 |
| 8 | ★★ `const p3: string[] = fromReturn("가")` | **통과** — 인자에서 온 추론이 먼저다 |
| 11·12 | `viaCallback(1, (x) => …)` | `number` — 콜백 매개변수 `x` 도 `number` 로 들어온다 |
| 17 | ★★★ `callbackFirst(() => 1, "가")` | `T` = **`number`** · `"가"` 가 `TS2345` |
| 20 | `killSecond(1, "가")` — `NoInfer` | `TS2345` — 두 번째 자리가 죽었다 |
| 21 | `killSecond<number \| string>(1, "가")` | **통과** — 명시가 모든 추론을 이긴다 |

- ★★★ 3행과 4행의 대비가 규칙이다. **합칠 수 있으면 유니온으로 합치고**(둘 다 `string` 계열),\
  **못 합치면**(`number` 와 `string`) **첫 후보가 이기고 나머지는 검사 대상**이 된다.
- ★★ 8행이 뜻밖일 수 있다. 반환 자리에 `string[]` 이라는 **문맥이 있는데도** 인자가 먼저다 —\
  `fromReturn("가")` 는 `string[]` 이 되고 그것이 문맥과 맞아떨어져 조용하다(7행 탐침이 `string[]` 로 확인).
- ★★★ 17행이 이 절의 별이다. **콜백의 반환 타입도 추론 후보**다.\
  `() => 1` 에서 `T` 가 `number` 로 정해지고 두 번째 인자 `"가"` 가 막힌다.
- ★★ 21행이 **가장 강한 규칙**이다 — **명시한 꺾쇠가 모든 추론을 이긴다**([**19번 주제**](../19-generics-basics/) 1절).
- ★★★ **이 표 전체가 「이 판의 관찰」** 이다. 릴리스 노트에 이 우선순위가 정리돼 있지 않다 —\
  실무의 규칙은 둘뿐이다: ① **명시가 이긴다** ② **모르겠으면 탐침을 한 줄 던진다.**

### 6. ★★★ **에러가 아니다** — `["가", "나"]` 로 `readonly` 만 빠진다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 5 | ★★★ `needsMutable([…])` — `const T extends string[]` | **`["가", "나"]`** — `readonly` 가 **빠졌다** |
| 10 | `needsReadonly([…])` — `const T extends readonly string[]` | `readonly ["가", "나"]` |
| 13 | ★★ `xs.sort()` | `TS2339` — 제약이 `readonly number[]` 라 `sort` 가 없다 |
| 21 | ★★★ `list.push("나")` | `TS2345` — `const` 가 **반환까지 좁혀** 호출자를 가둔다 |
| 25 | ★★★ `idConst(runtime)` — **변수** | `string` — **아무 일도 안 한다** |
| 28 | `idPlain([…] as const)` | `readonly ["가", "나"]` — 정의자가 꼭 달 필요는 없다 |

- ★★★ 5행이 **가장 예측이 빗나가는 줄**이다. 제약이 **가변** 배열(`string[]`)이라\
  `readonly ["가","나"]` 는 그 제약을 만족하지 못한다 — 그런데 **에러가 아니다.**\
  컴파일러가 `const` 의 효과를 **부분적으로 물린다**: 리터럴 원소는 남기고 **`readonly` 만 뺀다.**\
  ★★ 그리고 **그 자리는 `--strict` 를 끄면 또 달라진다**(실행 검증 표의 마지막 행) — **명세 보장이 아니라 이 판의 동작**이다.
- ★★ 13행은 `const` 와 무관하다. **제약이 `readonly` 면 `sort` 가 없다**([**20번 주제**](../20-generic-constraints-and-defaults/) 1절).
- ★★★ 21행이 **진짜 「쓰지 마라」 사례**다. `wideOnPurpose("가")` 의 반환이 `"가"[]` 라서 **호출자가 배열을 못 늘린다.**\
  `readonly` 뿐 아니라 **원소 타입까지** 좁아져 나간다.
- ★★★ 25행이 실무에서 가장 자주 실망하는 자리다. **인자가 변수면 `const` 는 아무것도 못 한다.**\
  라이브러리에 달아도 호출자가 값을 변수에 담아 넘기면 효과가 없다.

### 7. ★★★ **`readonly` 가 반환으로 새어 나가기** 때문이다

**왜 그런가**

- 6번 21행이 근거다. `const` 로 굳힌 타입은 **반환 타입에 그대로 실려 나간다** —\
  `wideOnPurpose("가")` 가 `"가"[]` 라서 호출자가 `push` 를 못 한다.
- ★★ 이것을 **모든 제네릭의 기본**으로 만들면 기존 코드의 호출자가 **대량으로 깨진다.**\
  배열을 받아 바꾸던 코드가 전부 `readonly` 벽에 막힌다.
- ★★★ 그래서 TS 는 **자리마다 정의자가 고르게** 했다 — `<const T>` 는 **옵트인**이다.
- ★ 같은 이유로 `as const` 도 **호출자의 옵트인**이다. 둘 다 「**기본은 넓히기**」 위에 얹힌 예외다.

### 8. ★★★ 실수가 **타입을 넓혀 스스로 맞아 버리기** 때문이다

**왜 그런가**

- 2번 9·10행이 근거다. `lightNaive(["빨강","노랑"], "파랑")` 에서 `"파랑"` 은 **목록에 없는 값**이다 —\
  **그런데 그 값이 `C` 의 추론 후보가 되어** `C` 가 `"노랑" | "빨강" | "파랑"` 으로 넓어진다.
- ★★★ 그러면 **`"파랑"` 은 이제 `C` 에 속한다.** 검사가 통과한다 — 진단이 **하나도 안 난다.**\
  「틀린 값을 줬더니 타입이 그 값을 포함하도록 늘어났다」는 **자기 충족**이다.
- ★★ 이런 고장은 **조용하다**는 점이 가장 나쁘다. 컴파일도 되고 테스트도 통과할 수 있다 —\
  런타임에 「목록에 없는 색」으로 분기하다 터진다.
- ★★★ `NoInfer<C>` 는 그 자리를 **후보에서 빼서** 「말하지는 말고 검사만 받아라」로 만든다.\
  **추론 자리가 둘 이상일 때만** 쓸모가 있다 — 하나뿐이면 죽일 것이 없다.

### 9. ★★ 변수 인자에는 **아무 일도 안 일어난다**

**왜 그런가**

- 6번 25행이 근거다. `idConst(runtime)` 이 `string` 이다 — 값이 **이미 넓어진 뒤**라서 굳힐 리터럴이 없다.
- ★★ 3번 18행도 같은 사건이다. 라이브러리에 `<const T>` 를 달아도 **호출자가 변수에 담아 넘기면 효과가 없다.**

| `<const T>` 를 쓴다 | 안 쓴다 |
|---|---|
| 호출자가 **리터럴을 직접 적는** API(설정·라우트·상태 키) | 인자가 **변수로 들어오는** API |
| 그 리터럴로 **다른 타입을 계산**할 때(`keyof`·템플릿 리터럴) | 반환 배열을 호출자가 **바꿔야** 할 때(6번 21행) |
| 호출자가 `as const` 를 **잊으면 곤란할 때**(3번 12행) | 호출자가 **넓히고 싶을 수도** 있을 때 — 되돌릴 수 없다 |

- ★ 제약이 **가변 배열**이면 `readonly` 가 빠진다는 것도 기억해 둔다(6번 5행) — **설정에 달린 칸**이다.

### 10. ★★★ `satisfies` 는 **검사**, `const` 는 **추론 제어**다

**왜 그런가**

- 4번 8·9·10행 — `satisfies` 를 써도 **타입이 안 바뀐다.** 22행 — 대신 **틀린 값을 잡는다.**
- ★★ 4번 15행 — `<const T>` 는 **타입을 바꾼다.** 20행 — `satisfies` 로는 못 바꾼다.
- ★★★ 그래서 **같이 쓸 수 있다.** 실제 라이브러리에서는 `<const T extends Config>` 로 받아\
  **정의자가 검사와 추론을 둘 다 책임지는** 설계가 흔하다 — 그때 호출자는 `satisfies` 를 안 써도 된다.
- ★ 한 줄로 — 「**`satisfies` 는 「이게 맞나」를 묻고, `const` 는 「이대로 기억해」라고 말한다.**」

### 11. ★★★ 제약은 **스칼라까지**, `const` 는 **속까지**, `NoInfer` 는 **자리까지**

**왜 그런가**

| [**19번**](../19-generics-basics/) 2절의 줄 | 제약([**20번**](../20-generic-constraints-and-defaults/)) | `<const T>`(이 주제) | `NoInfer`(이 주제) |
|---|---|---|---|
| `keep("가")` → `"가"` | 이미 괜찮다 | 안 바뀐다(1번 25행) | — |
| `pickMode("auto")` → `"auto"` | ★ **제약이 고쳤다** | — | — |
| `keep(["가","나"])` → `string[]` | ✗ | ★★★ **고친다**(1번 10행) | — |
| `keep({mode:"auto"})` → `{mode: string}` | ✗ | ★★★ **고친다**(1번 13행) | — |
| `keep(mutable)` → `string` | ✗ | ✗ **못 고친다**(3번 18행) | — |
| 기본값이 엉뚱한 자리에서 추론 | ✗ | ✗ | ★★★ **고친다**(2번 12행) |

- ★★★ 사슬의 역할 분담이 이 표다 — **19 가 고장을 보이고, 20 이 하한을 걸고, 21 이 정의 쪽에서 막는다.**
- ★★ **둘 다 못 고치는 칸이 하나 있다** — 변수에 담긴 값(3번 18행). 그때는 **변수 쪽에 `as const`** 를 붙인다.

### 12. ★★ 세 층

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장(5.0·5.4)** | `<const T>` 가 배열·객체 리터럴의 속을 굳힌다 · `NoInfer<T>` 가 그 자리를 추론 후보에서 뺀다 · 명시한 꺾쇠가 모든 추론을 이긴다 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ **추론 우선순위 전반**(5번 표) · ★★★ `const T extends string[]` 가 **`readonly` 를 뺀다**(6번 5행) · 유니온 원소의 **순서** · 진단 **문구** 전문 |
| **설정에 달린 것** | ★★★ 6번 5행 **한 자리** — `--strict` 를 끄면 `["가", "나"]` 가 **`string[]`** 이 된다 |
| **★ 부적용 — 방출된 JS** | ★★ **잴 것이 없다** — `const` 수식어도 `NoInfer` 도 **전부 타입 층**이다. 이 문서에는 `.js` 블록이 **하나도 없다** |

- ★★★ **이 주제는 「이 판의 관찰」 칸이 가장 두껍다.** 그래서 **규칙 이름을 외우는 것보다 탐침 한 줄이 빠르다.**
- ★★ [**18번**](../18-this-parameter-types/)·[**19번**](../19-generics-basics/)이 `.js` 로 결론을 낸 자리가 [**20번**](../20-generic-constraints-and-defaults/)·21 에서는 **부적용**이다 —\
  「재 봤더니 같았다」가 아니라 **잴 것이 없다.** 그 구분 자체가 이 두 주제의 성질이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| ★★★ 19 의 고장과 고침 | `--noEmit ex.21a.ts` | exit 1 · **9건** · `string[]` → **`readonly ["가", "나"]`** |
| ★★★ `NoInfer` 없을 때 | `--noEmit ex.21b.ts` | exit 1 · **8건** · 9행 **통과**(`C` = `"노랑" \| "빨강" \| "파랑"`) · 12행 `TS2345` |
| 누가 적느냐 | `--noEmit ex.21c.ts` | exit 1 · **7건** · 12행 `string[]` 대 13행 `readonly […]` |
| `satisfies` 와의 관계 | `--noEmit ex.21d.ts` | exit 1 · **6건** · 8·9·10행 **셋 다 `string`** |
| 추론 우선순위 | `--noEmit ex.21e.ts` | exit 1 · **10건** · 4행 `1` · 17행 `number` |
| 쓰지 말아야 할 자리 | `--noEmit ex.21f.ts` | exit 1 · **6건** · ★ 5행 **`["가", "나"]`**(에러 아님) |
| `.d.ts` 창 | `--declaration --emitDeclarationOnly ex.21g.ts` | ★ **exit 0 · 진단 0줄** · `fixed` 대 `naive` 가 **한 항목 차이** |
| `strict` 대조 | 여섯 파일을 `--strict false` 로 재실행 | ★★★ `ex.21f.ts` **하나만** 갈림 — 5행이 **`string[]`** 이 된다 |
| 반복 실행 | 같은 명령 **5회** | ★★ md5 **동일** — 유니온 순서가 안 흔들렸다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **추론 우선순위 전반**(5번의 표) — 릴리스 노트에 정리돼 있지 않다. **던져서 얻은 관찰**이다.
- ★★★ `const T extends string[]` 가 **`readonly` 를 빼고 통과**하는 것 — 그리고 **`--strict` 를 끄면 `string[]`** 이 되는 것.
- ★★ 유니온 원소의 **순서**(`"노랑" | "빨강" | "파랑"`) — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★★ 진단 **문구** 전문 — `TS2345`·`TS2339`·`TS2322` 라는 **코드**가 더 오래 간다.
- `.d.ts` 의 들여쓰기 4칸·줄 순서 — 방출기의 형식이다.

**안 돌려 본 것**

- **`NoInfer` 이전의 트릭**(`T & {}`·조건부 타입으로 흉내 내기) — **안 던졌다.**
- **`const` 타입 매개변수를 클래스·인터페이스에 다는 것** — **안 던졌다.** 함수에만 던졌다.
- **`NoInfer` 를 여러 자리에 겹쳐 쓰는 것** — **안 던졌다.**
- **템플릿 리터럴 타입과 함께 쓰는 것** — **안 던졌다.** 목록의 **27번 주제**.
- **`const` 타입 매개변수가 검사 시간에 주는 영향** — **재지 않았고 수치를 적지 않았다.**
