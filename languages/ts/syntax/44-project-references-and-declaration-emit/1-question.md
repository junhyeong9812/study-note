# ts/syntax/44 — 프로젝트 참조와 선언 방출 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **44 는 43 에서 온다** — [**43번 주제**](../43-remaining-tsconfig-choices/) 4절이 `incremental` 이 무엇을 다시 방출하는지 쟀다. 여기는 그것을 **프로젝트 둘**로 쪼갠다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 격자는 칸마다 두 프로젝트를 **새 디렉토리에 복사**해 두 `tsconfig.json` 을 그 칸의 설정으로 다시 썼다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 두 프로젝트 격자 (예측)

```ts
// index.ts
export function add(a: number, b: number): number {
    return a + b;
}
```

```ts
// main.ts
import { add } from "../../core/src/index";
console.log(add(1, 2));
```

```text
===== 소스: p44/core/tsconfig.json =====
{
    "compilerOptions": { "composite": true, "target": "es2022", "outDir": "dist", "rootDir": "src" },
    "include": ["src"]
}
===== 소스: p44/app/tsconfig.json =====
{
    "compilerOptions": { "target": "es2022", "outDir": "dist", "rootDir": "src" },
    "include": ["src"],
    "references": [{ "path": "../core" }]
}
```

- 위 두 설정이 「`composite` 있음 · `references` 있음」 칸이다. `core` 의 `composite` 를 빼거나 `app` 의 `references` 를 빼서 네 조합을 만들고, 각각 `tsc -b app` 과 `tsc -p app` 으로 7.0.2 · 5.9.3 에 던진다. 칸마다 무슨 진단이 나고, 진단 없이 빌드되는 칸은 몇 칸인가?
- 두 판이 다른 칸이 있다면 무엇이 다른가?

### 2. `app` 에게 물은 세 가지 (예측)

- 「있음 · 있음」 설정으로 `tsc -b app` 을 한 뒤 `app` 에게 ① `--traceResolution` 으로 import 가 어느 파일로 풀렸나 ② `--explainFiles` 로 프로그램에 `core` 의 어느 파일이 들었나를 묻는다. 각각 무엇이라고 답하는가?
- ③ 그다음 `core/dist/index.d.ts` 를 `export declare function add(a: string, b: string): string;` 한 줄로 바꾸고 `tsc -p app --noEmit` 을 던지면?

### 3. `tsc -b app --verbose` 여섯 단계 (예측)

- 처음 → 안 바꿈 → `core` 몸통만(`a + b` → `b + a`) → `core` 서명까지(매개변수 `c = 0` 추가) → `core/dist` 만 지움(`.tsbuildinfo` 는 남김) → `tsc -b app --clean` 뒤. 단계마다 `app` 은 다시 지어지는가? 5단계 뒤 `core/dist/index.d.ts` 는 있는가?

### 4. `isolatedDeclarations` 와 export 꼴 (예측)

```ts
// iso44a.ts
export function f(n: number) {
    return n * 2;
}
```

```ts
// iso44k.ts
export function one() {
    return 1;
}
```

```ts
// iso44d.ts
export const c = [1, 2];
```

```ts
// iso44e.ts
export const c = [1, 2] as const;
```

```ts
// iso44j.ts
const inner = (n: number) => n * 2;
export function g(n: number): number {
    return inner(n);
}
```

```ts
// iso44h.ts
export class K {
    m(n: number) {
        return n * 2;
    }
}
```

- 각각을 `--declaration --isolatedDeclarations` 로 7.0.2 · 5.9.3 · 4.9.5 에 던지면 무엇이 나는가? 두 판의 코드가 다른 행은?

### 5. `rootDir` 도 `references` 도 없는 `app` (예측)

- `app/tsconfig.json` 을 `{ "compilerOptions": { "target": "es2022", "outDir": "dist" }, "include": ["src"] }` 로 바꾸고 `tsc -p app` 을 두 판에 던지면 각각 무엇이 나고 `app/dist` 에 무엇이 생기는가?

### 6. `TS6305` 의 문구 (왜)

- 1번의 「있음 · 있음 · `tsc -p app`」 칸의 진단이 가리키는 파일은 무엇인가? 그 문구가 2번의 답을 어떻게 미리 말해 주는가?

### 7. `--traceResolution` 이 못 보는 것 (경계)

- 2번에서 ① 과 ② 가 다른 파일을 가리켰다. 해석 창은 무엇까지 보고 무엇을 못 보는가? ③ 이 그 둘 중 어느 쪽을 뒷받침하는가?

### 8. `iso44j.ts` 가 통과한 까닭 (왜)

- `iso44j.ts` 의 `inner` 에는 반환 타입이 없는데 `isolatedDeclarations` 가 막지 않았다. 왜인가? `isolatedDeclarations` 를 켜면 `iso44a.ts` 의 `.d.ts` 는 달라지는가?

### 9. 몸통만 바꾼 단계 (연결)

- 3번의 「`core` 몸통만」 단계에서 `app` 이 다시 안 지어진 것은 43편 4절의 어느 칸과 같은 성질인가?

### 10. 청소 (경계)

- 3번의 5단계 결과로 보면 `rm -rf core/dist` 와 `tsc -b app --clean` 은 무엇이 다른가? `tsc -b` 가 「최신인가」를 가르는 근거는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
