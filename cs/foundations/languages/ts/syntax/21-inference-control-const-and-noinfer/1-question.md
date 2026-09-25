# ts/syntax/21 — 추론 제어 — `const` 타입 매개변수·`NoInfer` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 두 도구는 **고치는 도구**다 —
> **고장을 먼저 떠올리지 못하면 답이 안 선다.** [**19번 주제**](../19-generics-basics/) 2절을 먼저 보고 오면 쉽다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — `const` 타입 매개변수는 **5.0**, `NoInfer<T>` 는 **5.4** 다. **7.0 에서 도는지는 던져서 확인했다.**
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 블록에 `const probe: null = …` 이 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 이 주제에서는 **`TS2345` 가 나는 것 자체가 답인 자리**가 많다 — 「막혀야 정상」이기 때문이다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 수식어 하나를 붙이면 무엇이 달라지나 (예측)

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

- 9행과 10행의 답을 나란히 적을 수 있는가?
- 12행과 13행은 객체다. 무엇이 붙는가?
- 24행과 25행은 **같은 답인가 다른 답인가**?

### 2. 목록에 없는 값을 기본값으로 주면 (예측)

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

- 9행 `lightNaive(["빨강","노랑"], "파랑")` 은 **막히는가**? 10행 탐침은 무엇을 뱉는가?
- 12행은 무슨 코드이고 진단이 무엇이라 말하는가?
- 22·23행 `fillNaive`/`fillFixed` 는 어떤가? 여기서도 `NoInfer` 가 있어야 막히는가?

### 3. 누가 적느냐 (예측)

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

- 9행과 10행의 답이 같은가?
- 12행과 13행 중 **넓어지는 쪽**은 어느 것인가?
- 18행은 변수를 넘긴다. `defined` 가 고쳐 주는가?

### 4. `satisfies` 는 리터럴을 지키나 (예측)

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

- 8·9·10행의 답이 셋 다 같은가?
- 15행 `takeConst({ … })` 는 무엇을 뱉는가?
- 20행처럼 `satisfies` 를 붙여 넘기면 추론이 좁아지는가?

### 5. 추론 자리가 여럿일 때 (예측)

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

- 3행 `two("가","나")` 와 4행 `two(1,"가")` 의 답이 어떻게 다른가?
- 8행은 반환 자리에 `string[]` 이라는 문맥이 있다. 통과하는가?
- 17행 `callbackFirst(() => 1, "가")` 에서 `T` 는 무엇이 되는가?

### 6. `const` 를 달면 안 되는 자리 (예측)

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

- 5행 `needsMutable(["가","나"])` 는 **에러인가**? 답이 무엇인가?
- 13행 `xs.sort()` 는 통과하는가? 왜인가?
- 21행 `list.push("나")` 는 통과하는가?

### 7. 왜 `const` 를 기본으로 안 했나 (왜)

- 6번 21행을 근거로 **한 문장**으로 댈 수 있는가?

### 8. 왜 `NoInfer` 가 필요했나 (왜)

- 2번 10행의 고장이 「실수인데 타입이 넓어져 맞아 버린다」인 이유를 설명할 수 있는가?

### 9. `const` 타입 매개변수를 쓸 자리와 안 쓸 자리 (경계)

- 인자가 **변수로 들어오는** API 에 달면 어떻게 되는가?

### 10. `satisfies` 와의 경계 (경계)

- 둘이 **하는 일이 무엇으로 갈리는가**? 같이 쓸 수 있는가?

### 11. 19·20 과 잇기 (연결)

- [**19번 주제**](../19-generics-basics/) 2절의 고장 다섯 줄을 [**20번 주제**](../20-generic-constraints-and-defaults/)의 제약과 이 주제의 `const` 가 **각각 어디까지** 고치는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판(7.0.2)의 관찰** · **설정에 달린 것**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
