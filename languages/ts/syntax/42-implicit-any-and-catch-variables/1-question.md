# ts/syntax/42 — 암시적 `any` 와 catch 변수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **42 는 39 에서 온다** — [**39번 주제**](../39-strict-bundle/)가 7.0.2 에서 `noImplicitAny`·`useUnknownInCatchVariables` 가 기본으로 켜져 있음을 쟀다.
> 여기서는 **어느 자리에서 `any` 가 새어 들어오나**와 **`catch` 로 받은 값을 어떻게 읽나**를 가른다. JS 쪽 사실(`throw` 임의 값 · 다른 realm)은 JS 갈래 [32번](../../../js/syntax/32-error-handling-and-error/)이 정본이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 설정 실험은 **칸마다 디렉토리와 `tsconfig.json` 을 따로** 만들어 `-p` 로 던졌다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 자리 아홉 × `noImplicitAny` (예측)

```ts
// ia42a.ts
function f(x) { return x; }
export {};
```

```ts
// ia42b.ts
function f({ a, b }) { return a + b; }
export {};
```

```ts
// ia42c.ts
function f(...rest) { return rest; }
export {};
```

```ts
// ia42d.ts
let v;
v = 1;
const n: number = v;
export {};
```

```ts
// ia42e.ts
let v;
function read() { return v; }
v = 1;
export {};
```

```ts
// ia42f.ts
const xs = [];
xs.push(1);
const ys: number[] = xs;
export {};
```

```ts
// ia42g.ts
const ys = [1, 2].map(x => x + 1);
export {};
```

```ts
// ia42h.ts
const conf = JSON.parse("{}");
const n: number = conf.a.b;
export {};
```

```ts
// ia42i.ts
const o = { a: 1 };
declare const k: string;
const n = o[k];
export {};
```

- 칸마다 `{ "compilerOptions": { "strict": true, "noImplicitAny": 켬/끔, "target": "es2022", "noEmit": true } }` 로 던진다. 켬에서 진단이 나는 탐침은 어느 것이고 코드는 무엇인가? 끔에서는?
- 7.0.2 와 5.9.3 의 답이 다른 탐침이 있는가?

### 2. 빈 배열 탐침의 설정 셋 (예측)

- 1번의 `ia42f.ts` 를 `--noImplicitAny false`(나머지 `strict` 는 켬) · `--noImplicitAny false --strictNullChecks false` · `--strict false` 로 7.0.2 에 던지면 각각 무엇이 나는가?

### 3. `JSON.parse` 를 받는 꼴 셋 (예측)

```ts
// json42a.ts
const conf = JSON.parse('{"port":"8080"}');
const port: number = conf.port;
console.log(typeof port, port.toFixed(1));
export {};
```

```ts
// json42b.ts
const conf: unknown = JSON.parse('{"port":"8080"}');
const port: number = conf.port;
console.log(typeof port, port.toFixed(1));
export {};
```

```ts
// json42c.ts
const conf: unknown = JSON.parse('{"port":"8080"}');
const port =
    typeof conf === "object" && conf !== null && "port" in conf && typeof conf.port === "number"
        ? conf.port
        : 0;
console.log(typeof port, port.toFixed(1));
export {};
```

- 셋을 `tsc --noEmit -t es2022` 로 하나씩 던지면 각각 무엇이 나는가?
- `json42a.ts` 와 `json42c.ts` 를 방출해 `node` 로 돌리면 각각 무엇을 찍는가?

### 4. 좁히는 꼴 넷 × 던지는 값 다섯 (예측)

```ts
// catch42.ts
// catch 로 받은 값을 네 가지 꼴로 읽는다 -- 던지는 값 다섯 가지
declare const require: (id: string) => { runInNewContext(code: string): unknown };
const vm = require("node:vm");

function viaInstanceof(e: unknown): string {
    return e instanceof Error ? "Error " + e.message : "else";
}
function viaTypeof(e: unknown): string {
    return typeof e === "string" ? "string " + e : "else";
}
function hasMessage(x: unknown): x is { message: string } {
    return typeof x === "object" && x !== null && "message" in x && typeof x.message === "string";
}
function viaGuard(e: unknown): string {
    return hasMessage(e) ? "message " + e.message : "else";
}
function viaAs(e: unknown): string {
    return "message " + (e as Error).message;
}

const throwers: [string, () => never][] = [
    ['new Error("m")', () => { throw new Error("m"); }],
    ['"m"', () => { throw "m"; }],
    ["null", () => { throw null; }],
    ['{ message: "m" }', () => { throw { message: "m" }; }],
    ["vm realm Error", () => { throw vm.runInNewContext('new Error("m")'); }],
];
const forms = [viaInstanceof, viaTypeof, viaGuard, viaAs];
console.log("thrown".padEnd(18) + ["instanceof", "typeof", "guard", "as Error"].map(s => s.padEnd(12)).join(" | ").trimEnd());
for (const [label, t] of throwers) {
    const cells: string[] = [];
    try {
        t();
    } catch (e) {
        for (const f of forms) {
            try {
                cells.push(f(e));
            } catch (x) {
                cells.push(x instanceof TypeError ? "TypeError" : "other");
            }
        }
    }
    console.log((label.padEnd(18) + cells.map(s => s.padEnd(12)).join(" | ")).trimEnd());
}
export {};
```

- 이 파일은 두 판에서 타입 검사를 통과하는가?
- 방출해 `node` 로 돌리면 다섯 행 × 네 열에 무엇이 찍히는가? 특히 `"m"` 행과 `null` 행의 `as Error` 칸, `vm realm Error` 행의 `instanceof` 칸은?

### 5. 오류 값이 들어오는 자리 여섯 (예측)

```ts
// reason42.ts
// 거절 사유와 catch 변수 -- 각 자리의 타입을 null 탐침으로 묻는다
try { throw 1; } catch (e) { const p1: null = e; }
Promise.reject(1).catch((r) => { const p2: null = r; });
Promise.reject(1).then(undefined, (r) => { const p3: null = r; });
try { throw 1; } catch (e: unknown) { const p4: null = e; }
try { throw 1; } catch (e: any) { const p5: null = e; }
try { throw 1; } catch (e: Error) { }
export {};
```

- `--strict --useUnknownInCatchVariables` 를 켬/끔으로 세 판(7.0.2 · 5.9.3 · 4.9.5)에 던지면 어느 행에서 무엇이 나는가? 판에 따라 달라지는 칸이 있는가?

### 6. `let v;` 두 탐침 (왜)

- 1번의 `ia42d.ts` 와 `ia42e.ts` 는 둘 다 `let v;` 로 시작한다. 켬에서 한쪽만 진단이 나는 까닭은 무엇인가?

### 7. `noImplicitAny` 가 `JSON.parse` 를 못 보는 까닭 (왜)

- 3번의 `json42a.ts` 는 켬에서도 진단 0줄인데 `node` 에서 터진다. `noImplicitAny` 가 이 `any` 를 잡지 못하는 까닭은 무엇이고, 한 단어로 막는 수는 무엇인가?

### 8. `e as Error` 가 방출물에서 (경계)

- 4번의 `viaAs` 는 방출물에서 어떤 모양이 되는가? 그것이 `"m"` 을 던졌을 때의 출력과 어떻게 이어지는가?

### 9. `catch` 변수에 적을 수 있는 주석 (경계)

- `catch (e: Error)` 로 적으면 무엇이 나는가? 적을 수 있는 주석은 무엇인가? `Promise` 의 `.catch((r) => …)` 에서 `r` 의 보호를 받으려면 어떻게 하는가?

### 10. 39 · JS 32 와 잇기 (연결)

- 39편 2절의 `pr39h` 는 이 주제의 어느 절이 넓힌 것인가?
- 4번의 `vm realm Error` 행의 `instanceof` 칸은 JS 32편의 어느 사실이 TS 에 나타난 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
