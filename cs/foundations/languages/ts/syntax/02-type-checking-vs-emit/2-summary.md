# ts/syntax/02 — 타입 검사와 코드 방출의 분리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `noEmit`](https://www.typescriptlang.org/tsconfig/#noEmit) ·
> [`noEmitOnError`](https://www.typescriptlang.org/tsconfig/#noEmitOnError) ·
> [`isolatedModules`](https://www.typescriptlang.org/tsconfig/#isolatedModules) ·
> [`verbatimModuleSyntax`](https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax) ·
> [Handbook — The Basics: Emitting with Errors](https://www.typescriptlang.org/docs/handbook/2/basic-types.html).
> 문서는 **규칙 확인용으로만** 열었다. 본문의 종료 코드·진단·산출물 유무는 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ **`tsc` 가 7.0.2 다 — 5.x 가 아니다.** 옵션 이름과 기본값이 다르다.
> 이 문서에서 실제로 확인한 7.0 의 변화 — `strict` 기본 **`true`** · `target` 기본 **es2025**(`es5` 는 **제거**) ·
> **`outFile`·`downlevelIteration` 제거**(`TS5102`) · `moduleResolution: node10` **제거**(`TS5108`).\
> ★★ 그런데 **`tsc --help --all` 은 `outFile`·`downlevelIteration` 을 여전히 목록에 싣는다** — 도움말과 실제가 어긋나 있다.
> **옵션 유무는 도움말이 아니라 던져서** 확인한다.
> **버전** — `noEmitOnError`·`noEmit` 은 1.x, `isolatedModules` 는 1.5, `verbatimModuleSyntax` 는 5.0, `noCheck` 는 5.6 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | **종료 코드** · 에러 코드 · 에러 문구 · `(행,열)` · 산출물 유무 · 방출된 JS 전문 | 같은 입력·같은 옵션이면 같은 값이다. 10회 재실행에서 한 글자도 안 바뀌었다 |
| **안 흔들린다** | `node` 의 `SyntaxError` 문구와 스택 프레임 이름 | `v18.19.1` 고정 |
| **흔들린다** | `node` 가 찍는 **절대 경로** | `file:///…/ex.02d.js` 의 앞부분. 그래서 배너에 적은 `sed` 로 잘라 `file:…/ex.02d.js` 로 정규화했다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ **소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다** — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 한눈에 — 쉽게 말하면

**교정자와 인쇄기가 한 사무실에 있지만 서로를 안 기다린다.**

| 비유 | 실체 |
|---|---|
| 교정자 — 빨간 펜으로 표시만 한다 | **타입 검사 패스** — 진단을 내지만 산출물을 안 만든다 |
| 인쇄기 — 포스트잇만 떼고 찍는다 | **방출 패스** — 타입이 맞는지 **묻지 않는다** |
| 교정지에 빨간 줄이 있어도 인쇄물은 나온다 | **에러가 있어도 `.js` 가 나온다** |
| 「빨간 줄 있으면 인쇄 멈춰」라고 시키는 것 | **`noEmitOnError`** |
| 「인쇄는 아예 하지 마, 교정만 봐」 | **`noEmit`** |
| 「교정 안 볼 테니 그냥 찍어」 | **`noCheck`**(5.6) |
| 접수 도장 — 0·1·2 세 종류 | **종료 코드** — 0 통과 · 1 에러이고 **산출물 없음** · 2 에러인데 **산출물 있음** |

- ★★★ 한 줄로 — **「`tsc` 는 타입 검사기이자 트랜스파일러인데, 그 둘이 서로를 기다리지 않는다.」**
- ★★ 그래서 **종료 코드 없이는 이 주제가 성립하지 않는다.** 「에러가 났다」와 「파일이 나왔다」가 **동시에 참**인 자리가 이 주제의 본체다.

```text
                     ex.02a.ts
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        타입 검사 패스          방출 패스
      (진단을 만든다)        (타입 표기를 떼고 JS 를 쓴다)
              │                     │
              │  ex.02a.ts(5,7):    │  ex.02a.js 가 생긴다
              │  error TS2322 …     │  그리고 node 로 돌아간다
              └──────────┬──────────┘
                         ▼
                    종료 코드 2
              「에러가 있었고 산출물도 나왔다」

  * 두 패스 사이에 화살표가 없다 — 방출은 검사 결과를 안 본다.
```

```text
  종료 코드 세 값
  +---------+--------------------------------+-----------------+
  |   0     | 진단 없음                      | 산출물 있음     |
  |   1     | 진단 있음 + 산출물 **없음**    | noEmit ·        |
  |         |                                | noEmitOnError   |
  |   2     | 진단 있음 + 산출물 **있음**    | 기본값          |
  +---------+--------------------------------+-----------------+
    「경고 0건」이 뜻이 없듯 **「에러 있음」만으로는 무슨 일이 났는지 모른다.**
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **에러가 있는데 왜 파일이 나오나** — 그것이 버그가 아니라 **설계**인 이유를 [**01번 주제**](../01-what-ts-adds-and-erases/)의 결론에서 이을 수 있나.
2. **그래서 CI 에서 무엇을 봐야 하나** — 「빌드가 됐다」는 통과의 증거가 아니다. 무엇을 보면 되나.
3. **파일 하나만 보고 변환하는 도구는 왜 제약이 붙나** — `isolatedModules`·`verbatimModuleSyntax` 가 막는 것이 무엇인가.

★ [**01번 주제**](../01-what-ts-adds-and-erases/)가 「**타입은 런타임에 없다**」를 세웠다면, 여기는 **그래서 방출이 검사를 안 기다려도 된다**는 결과를 본다. 둘은 한 쌍이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **종료 코드** | 0 / 1 / 2 가 **서로 다른 사건**이다 | ★ 이 주제의 본체 |
| ★★ **산출물이 생겼나** | 같은 진단에 같은 파일이 나오기도 하고 안 나오기도 한다 | ★ 이 주제의 고유 창 |
| **진단 전문** | 어느 플래그가 **무엇을 새로 막는가** | 모든 주제 공통 |
| **`node` 실행** | **방출은 됐는데 실행이 터지는** 자리 | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

비용 — 없음. 종료 코드는 셸이 이미 들고 있다(`echo $?`).

### (1) ★★★ 에러가 있는데 `.js` 가 나온다

**언제 쓰나** — 「빌드가 됐으니 타입은 맞겠지」를 의심할 때. 이 절이 이 주제의 전부다.

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    없음
```

```text
===== node ex.02a.js (node exit=0) =====
42 42
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **한 건** 났다 — `const label: string = 42` 가 `TS2322` 다.
- **그런데 `ex.02a.js` 가 생겼다.** 배너의 `tsc exit=2` 와 「산출물」 칸을 같이 읽어야 이 사건이 보인다.
- 그 파일을 `node` 로 돌리면 **정상 종료하고 `42 42` 를 찍는다** — `label` 자리에 숫자 `42` 가 그대로 들어 있다.
- ★★ 즉 타입 에러는 **실행을 막지 않는다.** `: string` 을 떼고 나면 `const label = 42;` 는 **완벽하게 유효한 JS** 이기 때문이다.

> **종료 코드 2** — 「진단이 있었고 산출물도 만들었다」는 뜻. 이 판에서 **기본값으로 에러가 난 모든 컴파일**이 이 값이었다.

비용 — 없음. 오히려 **비용을 아끼려고** 이렇게 설계됐다 — 타입이 틀려도 나머지 코드를 돌려 보며 고칠 수 있다.

### (2) ★★★ 세 플래그가 각각 무엇을 바꾸나

**언제 쓰나** — CI 스크립트를 짤 때. **무엇을 써야 「에러면 멈춘다」가 되는지** 고를 때.

같은 `ex.02a.ts` 를 옵션만 바꿔 네 번 더 던진다.

같은 `ex.02a.ts` 를 옵션만 바꿔 던진다(파일은 한 글자도 안 바꿨다).

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --noEmitOnError ex.02a.ts (tsc exit=1) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      없음
ex.02a.d.ts    없음
```

```text
===== tsc --pretty false --noEmit ex.02a.ts (tsc exit=1) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      없음
ex.02a.d.ts    없음
```

이어지는 두 판도 같은 파일이다.

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --noCheck ex.02a.ts (tsc exit=0) =====
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    없음
```

```text
===== tsc --pretty false --declaration ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    생김
```

그림 해설 — 한 단계에 한 문장.

- **`--noEmitOnError`** — 진단은 **똑같이** 나오는데 파일이 **안 생겼다**. 종료 코드가 `2` 에서 **`1`** 로 내려갔다.
- **`--noEmit`** — 결과가 `--noEmitOnError` 와 **글자 하나까지 같다.** 이 파일에서는 둘을 구별할 수 없다.\
  ★ 차이는 **에러가 없을 때** 드러난다 — `--noEmit` 은 그때도 안 쓰고, `--noEmitOnError` 는 쓴다.
- **`--noCheck`**(5.6) — 진단이 **0건**이고 종료 코드가 **`0`**, 파일은 **생겼다**. 검사 패스를 통째로 끈 것이다.
- **`--declaration`** — 진단은 그대로인데 `ex.02a.js` 와 **`ex.02a.d.ts` 가 둘 다 생겼다**. 에러가 있어도 **선언 파일까지 나온다**.

선언 파일까지 뽑아 보면 이렇다. 소스는 같은 파일이다.

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --declaration ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
===== 방출된 ex.02a.d.ts =====
export declare function twice(n: number): number;
```

- ★ 그 `.d.ts` 를 보면 **에러가 난 `const label` 이 아예 없다.** `export` 가 붙은 `twice` 만 실렸다 — 선언 방출은 **모듈 밖으로 나가는 것**만 적는다.

| 플래그 | 진단 | 산출물 | 종료 코드 | 언제 쓰나 |
|---|---|---|---|---|
| (없음) | 난다 | **생긴다** | **2** | 개발 중 — 고치면서 돌려 본다 |
| `--noEmitOnError` | 난다 | 안 생긴다 | **1** | 빌드 — 깨진 산출물을 남기고 싶지 않을 때 |
| `--noEmit` | 난다 | 안 생긴다 | **1** | CI 검사 전용 — 번들러가 따로 방출할 때 |
| `--noCheck` | **안 난다** | 생긴다 | **0** | 방출만 급할 때. ★ **검사를 끈 것이지 통과한 게 아니다** |

비용 — `--noCheck` 는 빠르지만 **아무것도 보장하지 않는다.** 이 표에서 종료 코드 `0` 이 두 뜻을 갖는 유일한 자리다.

### (3) ★★ 구문 에러여도 파일이 나온다

**언제 쓰나** — 「그래도 문법이 깨졌으면 멈추겠지」를 의심할 때.

```ts
// ex.02b.ts
// 괄호가 안 닫힌 구문 에러 — 타입 에러보다 앞 단계에서 걸린다
function twice(n: number {
    return n * 2;
}
```

```text
===== tsc --pretty false ex.02b.ts (tsc exit=2) =====
ex.02b.ts(2,26): error TS1005: ',' expected.
ex.02b.ts(3,12): error TS1005: ':' expected.
ex.02b.ts(3,14): error TS1005: ',' expected.
ex.02b.ts(3,16): error TS1003: Identifier expected.
ex.02b.ts(3,17): error TS1138: Parameter declaration expected.
ex.02b.ts(4,1): error TS1138: Parameter declaration expected.
ex.02b.ts(5,1): error TS1005: ')' expected.
===== 방출된 ex.02b.js =====
"use strict";
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이다 — 파서가 괄호를 못 닫고 계속 복구를 시도했다.
- **그런데도 `ex.02b.js` 가 생겼다.** 내용은 `"use strict";` 한 줄뿐이다.
- 종료 코드는 여기서도 **`2`** 다 — 「진단 있음 + 산출물 있음」.
- ★★ 즉 **「에러의 종류」로도 방출이 갈리지 않는다.** 타입 에러든 구문 에러든 같다.

비용 — 이 자리가 위험하다. **빈 파일이 배포로 흘러가면 런타임에 아무 일도 안 일어난다** — 에러도 안 난다.

### (4) ★★ 진단은 stdout 으로 나온다 — 갈라 받아 확인했다

**언제 쓰나** — 로그 파이프를 짤 때. `2>` 로만 받으면 **아무것도 안 잡힌다.**

```text
===== tsc --pretty false ex.02a.ts 1>split.stdout 2>split.stderr (tsc exit=2) =====
----- split.stdout (1줄) -----
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- split.stderr (0줄) -----
```

그림 해설 — 한 단계에 한 문장.

- `1>` 로 받은 쪽에 진단 한 줄이 들어왔고, `2>` 로 받은 쪽은 **0줄**이다.
- ★ 이 배치에서 돌린 **`tsc` 실행 전부**(30여 판)에서 stderr 가 **0바이트**였다.
- ★★ 그래서 `tsc ... 2>&1 | grep error` 는 되지만 `tsc ... 2>log.txt` 는 **빈 파일을 만든다.**
- ★ 이 성질 덕분에 이 갈래는 [작성 가이드의 규칙 18](../../../../../../reference/study-note-guide.md)(stdout·stderr 섞임)에서 자유롭다 — 진단과 `console.log` 가 **다른 프로그램**(`tsc` 와 `node`)에서 나오므로 애초에 섞이지 않는다.

비용 — 없음. 한 번 확인하면 끝이다.

### (5) ★★ 파일 하나만 보는 도구가 못 하는 일 — `isolatedModules`

**언제 쓰나** — Babel·esbuild·SWC 처럼 **파일 단위로 변환하는 도구**를 쓸 때.

```ts
// ex.02c-types.ts
// 타입 하나와 값 하나를 같이 내보낸다
export interface Point {
    x: number;
    y: number;
}
export const origin: Point = { x: 0, y: 0 };
```

```ts
// ex.02c.ts
// 타입인지 값인지는 다른 파일을 봐야 안다 — isolatedModules 가 막는 자리
import { Point, origin } from "./ex.02c-types.js";

export { Point };
export const start = origin;
```

옵션 없이 던지면 통과하고, 방출에서 `Point` 가 사라진다.

```text
===== tsc --pretty false --module esnext ex.02c.ts ex.02c-types.ts (tsc exit=0) =====
===== 방출된 ex.02c.js =====
// 타입인지 값인지는 다른 파일을 봐야 안다 — isolatedModules 가 막는 자리
import { origin } from "./ex.02c-types.js";
export const start = origin;
```

같은 코드에 `--isolatedModules` 를 붙이면 막힌다.

```text
===== tsc --pretty false --module esnext --isolatedModules --noEmit ex.02c.ts ex.02c-types.ts (tsc exit=1) =====
ex.02c.ts(4,10): error TS1205: Re-exporting a type when 'isolatedModules' is enabled requires using 'export type'.
```

그림 해설 — 한 단계에 한 문장.

- 기본 컴파일은 `ex.02c-types.ts` 를 **같이 읽어서** `Point` 가 타입임을 알아내고 `export { Point }` 를 지웠다.
- 방출된 파일에는 `import { origin }` 과 `export const start` 만 남았다.
- ★★ **파일 하나만 보는 도구는 그 판단을 못 한다.** `ex.02c.ts` 만 봐서는 `Point` 가 타입인지 값인지 알 수 없다.
- 그래서 `--isolatedModules` 는 `TS1205` 로 **미리 막는다** — 「`export type` 을 쓰라」.

```text
  전체를 보는 컴파일러                   파일 하나만 보는 변환기
  +---------------------------+          +---------------------------+
  | ex.02c.ts 와              |          | ex.02c.ts 만              |
  | ex.02c-types.ts 를 둘 다  |          |                           |
  | 읽는다                    |          | Point 가 타입인지 값인지  |
  |                           |          | **알 수 없다**            |
  | → export { Point } 를     |          | → 지워야 하나 남겨야 하나 |
  |   지운다                  |          |   판단 불가               |
  +---------------------------+          +---------------------------+
    통과                                   isolatedModules 가 TS1205 로 막는다
```

비용 — 코드에 `export type` 을 명시해야 한다. 그 대신 **어떤 변환기에 태워도 같은 결과**가 나온다.

### (6) ★★★ 방출은 됐는데 실행이 터지는 자리 — `verbatimModuleSyntax`

**언제 쓰나** — 「타입 이름을 지우는 판단」을 컴파일러에게 맡기지 않기로 했을 때.

```ts
// ex.02d-lib.ts
// 타입과 값을 같이 내보내는 모듈
export interface Shape {
    area(): number;
}
export class Circle implements Shape {
    constructor(public r: number) {}
    area() {
        return 3 * this.r * this.r;
    }
}
```

```ts
// ex.02d.ts
// verbatimModuleSyntax 를 켜면 타입 이름이 import 목록에 그대로 남는다
import { Shape, Circle } from "./ex.02d-lib.js";

const s: Shape = new Circle(2);
console.log(s.area());
```

```text
===== tsc --pretty false --module esnext --verbatimModuleSyntax ex.02d.ts ex.02d-lib.ts (tsc exit=2) =====
ex.02d.ts(2,10): error TS1484: 'Shape' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
===== 방출된 ex.02d.js =====
// verbatimModuleSyntax 를 켜면 타입 이름이 import 목록에 그대로 남는다
import { Shape, Circle } from "./ex.02d-lib.js";
const s = new Circle(2);
console.log(s.area());
```

```text
===== node ex.02d.js 2>&1 | sed -E "s#^file://.*/(ex\.02d\.js)#file:…/\1#" (node exit=1) =====
file:…/ex.02d.js:2
import { Shape, Circle } from "./ex.02d-lib.js";
         ^^^^^
SyntaxError: The requested module './ex.02d-lib.js' does not provide an export named 'Shape'
    at ModuleJob._instantiate (node:internal/modules/esm/module_job:123:21)
    at async ModuleJob.run (node:internal/modules/esm/module_job:191:5)
    at async ModuleLoader.import (node:internal/modules/esm/loader:336:24)
    at async loadESM (node:internal/process/esm_loader:34:7)
    at async handleMainPromise (node:internal/modules/run_main:106:12)

Node.js v18.19.1
```

그림 해설 — 한 단계에 한 문장.

- 진단은 `TS1484` 한 건 — 「타입은 `import type` 으로 가져오라」.
- **그런데 파일이 나왔고, 그 파일의 첫 import 줄에 `Shape` 가 그대로 남았다.** `verbatimModuleSyntax` 가 「적힌 그대로 방출」이기 때문이다.
- `node` 로 돌리면 **`SyntaxError`** 가 난다 — `ex.02d-lib.js` 에 `Shape` 라는 export 가 없기 때문이다(인터페이스는 소거됐다).
- ★★★ 이것이 이 주제의 가장 센 증거다 — **`tsc` 가 낸 파일이 유효한 JS 가 아닐 수 있다.** 「빌드 통과 = 실행 가능」이 아니다.
- 종료 코드는 `tsc` 쪽 **2**, `node` 쪽 **1** 이다. 둘을 갈라 적는다.

비용 — 없음. 오히려 이 조합이 **에러를 내 준 덕분에** 고칠 수 있다. `--noEmitOnError` 를 같이 켜면 이 파일은 애초에 안 나온다.

### (7) ★ `tsconfig.json` 을 쓰면 — 7.0 에서 사라진 옵션

**언제 쓰나** — 5.x 시절 설정을 그대로 들고 7.0 으로 올릴 때.

```json
// tsconfig.02e.json
{
    "compilerOptions": {
        "target": "es5",
        "moduleResolution": "node10"
    },
    "files": ["ex.02e.ts"]
}
```

```ts
// ex.02e.ts
// tsconfig.json 으로 컴파일하는 판 — 7.0 에서 사라진 옵션 둘을 넣어 뒀다
export const n: number = "문자열";
```

```text
===== tsc --pretty false (tsc exit=2) =====
tsconfig.json(3,19): error TS5108: Option 'target=ES5' has been removed. Please remove it from your configuration.
tsconfig.json(4,29): error TS5108: Option 'moduleResolution=node10' has been removed. Please remove it from your configuration.
----- 산출물 -----
ex.02e.js      생김
```

그림 해설 — 한 단계에 한 문장.

- 진단 두 건이 **`tsconfig.json` 의 행·열**을 가리킨다 — 소스 파일이 아니다.
- `target: "es5"` 와 `moduleResolution: "node10"` 이 **둘 다 제거**됐다(`TS5108`).
- ★ **그런데 여기서도 `ex.02e.js` 가 생겼다.** 설정 에러여도 방출은 돈다.
- ★★ `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시한다**(`tsc --help` 의 문구). 그래서 이 문서의 다른 블록들은 설정 파일과 무관하게 재현된다.

> **`TS5102` 와 `TS5108`** — 전자는 「옵션이 제거됐다」(`outFile`·`downlevelIteration`), 후자는 「그 **값**이 제거됐다」(`target=ES5`·`moduleResolution=node10`).\
> 예: 같은 「7.0 에서 없어졌다」인데 **옵션 이름이 없어진 것**과 **고를 수 있는 값이 줄어든 것**으로 갈린다.

비용 — 마이그레이션 비용. 대신 진단이 **정확히 어느 줄인지** 알려 준다.

## 문법 — 형태와 규칙

이 주제의 「문법」은 소스 문법이 아니라 **명령줄과 종료 코드의 규약**이다.

```text
형태 — 네 가지 호출과 그 뜻
  tsc ex.ts                     검사 + 방출. 에러여도 방출한다        -> 0 또는 2
  tsc --noEmit ex.ts            검사만. 절대 안 쓴다                  -> 0 또는 1
  tsc --noEmitOnError ex.ts     검사 통과할 때만 쓴다                 -> 0 또는 1
  tsc --noCheck ex.ts           방출만. 검사를 끈다                   -> 0

  tsc ex.ts               ← 파일을 직접 주면 tsconfig.json 을 **무시**한다
  tsc                     ← 현재 디렉토리의 tsconfig.json 으로 컴파일
  tsc -p ./dir            ← 지정한 설정으로 컴파일
```

**규칙 불릿**

- ★★★ **종료 코드 세 값을 갈라 읽는다** — `0` 진단 없음 · `1` 진단 있고 **산출물 없음** · `2` 진단 있고 **산출물 있음**.
- ★★ **「에러 없음」과 「종료 코드 0」은 다르다** — `--noCheck` 는 검사를 껐는데도 `0` 이다.
- ★ **진단은 stdout 으로 나온다.** `2>` 로만 받으면 빈 파일이 된다.
- ★ **설정 에러도 진단이다** — `tsconfig.json(행,열): error TS5108: …` 처럼 설정 파일의 좌표를 가리킨다.
- ★ **파일 좌표가 없는 진단도 있다** — `error TS5102: Option 'outFile' has been removed.` 는 앞에 `파일(행,열):` 이 없다. 로그를 정규식으로 파싱한다면 **이 모양을 빠뜨리기 쉽다**.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) isolatedModules 아래에서 타입을 재수출  ->  TS1205  Re-exporting a type …
2) verbatimModuleSyntax 아래에서 타입을 값 import  ->  TS1484  'Shape' is a type …
3) 7.0 에서 제거된 옵션 값                 ->  TS5108  Option 'target=ES5' has been removed.
4) 7.0 에서 제거된 옵션 이름               ->  TS5102  Option 'outFile' has been removed.
```

## 어디서 틀리나

- ★★★ **「빌드가 됐으니 타입은 맞다」** — 아니다. 기본값에서는 **에러가 있어도 `.js` 가 나온다**(종료 코드 2).\
  CI 에서 봐야 하는 것은 **산출물의 존재가 아니라 종료 코드**다.
- ★★★ **「종료 코드가 0이 아니면 파일은 안 나왔겠지」** — 아니다. `2` 는 **나왔다**는 뜻이다. 남은 파일이 **다음 단계로 흘러간다.**
- ★★ **「구문 에러면 멈추겠지」** — 안 멈춘다. `"use strict";` 한 줄짜리 파일이 나온다 — **실행해도 아무 일이 안 일어난다.**
- ★★ **「`--noEmit` 과 `--noEmitOnError` 는 같은 것」** — 에러가 있을 때만 같다. **에러가 없으면 정반대**다(앞은 안 쓰고 뒤는 쓴다).
- ★★ **「`tsc` 가 만든 건 유효한 JS 다」** — 아니다. `verbatimModuleSyntax` 판에서 `node` 가 `SyntaxError` 를 냈다.
- ★ **「`--noCheck` 로 빌드가 빨라졌고 통과했다」** — 통과한 게 아니라 **안 본 것**이다. 종료 코드 `0` 이 두 뜻을 갖는 유일한 자리다.
- ★ **「`tsc ex.ts` 가 내 `tsconfig.json` 을 읽겠지」** — 안 읽는다. 파일을 직접 주면 **무시하고 기본 옵션**으로 돈다.
- ★ **「진단은 stderr 겠지」** — stdout 이다. 30여 판 전부 stderr 가 0바이트였다.
- ★ **「도움말에 있으니 쓸 수 있겠지」** — `--help --all` 은 `outFile`·`downlevelIteration` 을 싣지만 실제로 주면 `TS5102` 다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 방출은 **타입 검사 결과를 보지 않는다** — 타입에만 속한 조각을 떼는 일에 타입의 정합성이 필요 없다 | 핸드북의 「Emitting with Errors」 절이 이것을 설계로 못 박는다. 이 판의 종료 코드 2 가 그 결과다 |
| **언어 보장** | `noEmitOnError`·`noEmit` 은 **방출만 끈다** — 검사 결과(진단)는 그대로다 | 세 판의 진단 줄이 **글자 하나까지 같다** |
| **언어 보장** | `isolatedModules` 는 **파일 단위 변환에서 모호해지는 문법**을 금지한다 | `TS1205` 의 문구가 그 규칙이다 |
| **이 판(7.0.2)의 관찰** | 종료 코드가 **정확히 0·1·2** 라는 것 | 관찰이다. 다른 값(프로젝트 참조 오류 등)도 있을 수 있다 — 이 배치에서는 그 셋만 봤다 |
| **이 판의 관찰** | 진단이 **stdout** 으로 나가는 것 | 30여 판 전수 확인. 그래도 「보장」이 아니라 「이 판의 관찰」이다 |
| **이 판의 관찰** | 구문 에러 판의 진단이 **일곱 건**이라는 것 | 파서의 복구 전략에 달렸다. 「그래도 방출된다」만 성질로 읽는다 |
| **7.0 에서 바뀐 것** | `target=ES5`·`moduleResolution=node10`·`outFile`·`downlevelIteration` 제거 | `TS5108`·`TS5102` 를 직접 받았다 |

★ **「여러 번 돌려 같았다」는 보장이 아니다.** 종료 코드와 stdout 은 이 판의 관찰이다 — 판이 오르면 다시 던진다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| CI 의 검사 단계에 `tsc --noEmit` — 번들러가 따로 방출할 때 | `tsc` 만 돌리고 **종료 코드를 안 보는 것** |
| 빌드에 `--noEmitOnError` — 깨진 산출물을 안 남긴다 | `--noCheck` 를 CI 에 — 검사를 끈 것을 통과로 읽게 된다 |
| `isolatedModules` — 변환기를 바꿔도 결과가 같다 | 아무 플래그 없이 배포 산출물을 만드는 것 |
| `verbatimModuleSyntax` — import/export 를 적힌 그대로 | `verbatimModuleSyntax` 만 켜고 `--noEmitOnError` 를 안 켜는 것 — **안 도는 파일**이 남는다 |

## 핵심 문장

1. **`tsc` 안에서 검사 패스와 방출 패스는 서로를 기다리지 않는다** — 타입이 틀려도 JS 는 만들 수 있다.
2. **종료 코드 `2` 는 「에러가 났는데 파일도 나왔다」는 뜻이다** — 이 값을 안 보면 이 주제가 성립하지 않는다.
3. **`--noEmit` 과 `--noEmitOnError` 는 에러가 없을 때 갈린다** — 앞은 그때도 안 쓴다.
4. **`--noCheck` 의 종료 코드 `0` 은 통과가 아니라 안 본 것이다.**
5. **`tsc` 가 낸 파일이 유효한 JS 라는 보장은 없다** — `verbatimModuleSyntax` 판이 `node` 에서 `SyntaxError` 를 냈다.
6. **진단은 stdout 으로 나오고, 설정 파일의 좌표를 가리킬 수도 있고, 좌표가 아예 없을 수도 있다.**

## 관련 자료

- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「**무엇이 지워지나**」는 그쪽이 정본이다. 여기는 「**그래서 지우는 일과 검사하는 일이 왜 따로 도나**」부터.
- `cs/foundations/compiler-pipeline/` — 어휘 분석·구문 분석·중간 표현 같은 **컴파일러 일반론**은 그쪽. 여기서는 TS 고유의 **검사 패스와 방출 패스 분리**만 본다.
- `history/js/05-빌드-생태계.md` — 트랜스파일러·번들러가 왜 생겼나는 그쪽. 여기서는 **현재 플래그의 의미**만 본다.
- 목록의 **35번 주제**(모듈 해석) · **36번 주제**(타입 전용 import·export) — `moduleResolution`·`verbatimModuleSyntax` 의 전면 비교는 그쪽.
- 목록의 **39번 주제**(`strict` 묶음) · **43번 주제**(`tsconfig` 의 나머지 선택) — 플래그 지도는 그쪽.

## 용어 풀이

> **방출(emit)** — 컴파일러가 산출물(`.js`·`.d.ts`·`.js.map`)을 파일로 쓰는 단계.\
> 예: `tsc ex.02a.ts` 가 `ex.02a.js` 를 만드는 것. 진단이 있어도 이 단계는 돈다.

> **패스(pass)** — 컴파일러가 소스를 한 번 훑는 단계. 여러 패스가 순서대로 돈다.\
> 예: `tsc` 는 검사 패스에서 진단을 모으고, 방출 패스에서 파일을 쓴다.

> **종료 코드(exit code)** — 프로그램이 끝나면서 셸에 넘기는 숫자. 0이 관례상 「성공」이다.\
> 예: `tsc ex.02a.ts; echo $?` 가 `2` 를 찍으면 「에러가 났고 파일도 나왔다」는 뜻이다.

> **트랜스파일(transpile)** — 한 언어를 **비슷한 추상 수준의 다른 언어**로 옮기는 것.\
> 예: TS → JS. 기계어로 내려가는 것이 아니라 옆으로 간다.

> **파일 단위 변환(single-file transform)** — 다른 파일을 안 읽고 한 파일만 보고 변환하는 방식.\
> 예: esbuild·SWC·Babel 이 그렇게 돈다. 그래서 「이 이름이 타입인가 값인가」를 못 푼다.

> **선언 방출(declaration emit)** — `.d.ts` 파일을 만드는 것. **모듈 밖으로 나가는 것**만 적는다.\
> 예: `--declaration` 을 주면 `export declare function twice(n: number): number;` 가 나온다.

> **`use strict`** — JS 의 엄격 모드 선언. TS 는 `alwaysStrict`(기본 `true`) 때문에 스크립트 파일에 이것을 붙인다.\
> 예: 모듈(`import`/`export` 가 있는 파일)은 이미 엄격 모드라 안 붙는다.

## 더 들어가면

- **CI 에 쓸 한 줄** — `tsc --noEmit` 을 별도 단계로 두고 **종료 코드로만** 판정한다. 산출물 유무를 보지 않는다.
- **번들러와 나누는 법** — 요즘은 `tsc --noEmit` 이 검사를, esbuild·SWC 가 방출을 맡는 구성이 흔하다. 그때 `isolatedModules` 는 **선택이 아니라 필수**가 된다.
- **`--noCheck` 의 제자리** — 5.6 에서 들어왔고, 모노레포에서 **선언 파일을 빨리 뽑을 때** 쓴다. 검사는 다른 단계가 따로 한다는 전제가 있어야 한다.
- **이 판에서 확인한 7.0 의 옵션 제거** — `outFile`·`downlevelIteration`(`TS5102`) · `target=es5`·`moduleResolution=node10`(`TS5108`) · `namespace` 의 `module` 표기(`TS1540`). ★ **도움말에는 아직 실려 있는 것이 있으므로 던져서 확인한다.**
