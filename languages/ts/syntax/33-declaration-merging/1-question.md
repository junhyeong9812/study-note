# ts/syntax/33 — 선언 병합 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **33 은 08 에서 온다** — [**08번 주제**](../08-interface-vs-type/) 1절이 「`interface` 는 합쳐지고 `type` 은 `TS2300`」 · 충돌하면 `TS2717` · 호출 시그니처가 오버로드로 쌓인다는 것을 이미 쟀다.
> 여기서는 **짝을 여덟 가지로 넓히고**, **오버로드 순서**와 **전역·모듈 보강**을 방출물로 가른다.
> [**23번 주제**](../23-typeof-type-operator/)의 「값 공간과 타입 공간」을 떠올리지 못하면 1·6번이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교(2번)에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ 이 주제는 **파일이 여럿**이다 — 실험마다 파일 이름을 다르게 지었다. **어느 파일을 함께 컴파일했는가**가 답을 바꾼다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 이름을 여덟 짝으로 두 번 선언하면 (예측)

```bash
# ts30b-mergegrid.sh
#!/usr/bin/env bash
# 같은 이름 Thing 을 두 번 선언하는 여덟 짝 -- 짝마다 파일 하나씩 따로 던진다
# 칸: 진단 코드(탐침 줄 제외) · 탐침이 말하는 타입 · 방출물을 node 로 돌린 출력
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'   # 구분자는 탭 -- 선언 안에 ; 가 나온다(규칙 32)
pairs=(
  "interface+interface${T}interface Thing { a: number }${T}interface Thing { b: string }${T}null as unknown as keyof Thing & {}${T}"
  "interface+class${T}class Thing { a = 1 }${T}interface Thing { b: string }${T}null as unknown as keyof Thing & {}${T}JSON.stringify([new Thing().a, typeof new Thing().b])"
  "namespace+function${T}function Thing() { return 1 }${T}namespace Thing { export const b = \"x\" }${T}null as unknown as keyof typeof Thing${T}JSON.stringify([Thing(), Thing.b])"
  "namespace+enum${T}enum Thing { A }${T}namespace Thing { export function b() { return \"x\" } }${T}null as unknown as keyof typeof Thing${T}JSON.stringify([Thing.A, Thing.b()])"
  "namespace+class${T}class Thing { a = 1 }${T}namespace Thing { export const b = \"x\" }${T}null as unknown as keyof typeof Thing${T}JSON.stringify([new Thing().a, Thing.b])"
  "type+type${T}type Thing = { a: number }${T}type Thing = { b: string }${T}null as unknown as keyof Thing & {}${T}"
  "interface+type${T}interface Thing { a: number }${T}type Thing = { b: string }${T}null as unknown as keyof Thing & {}${T}"
  "class+class${T}class Thing { a = 1 }${T}class Thing { b = \"x\" }${T}null as unknown as keyof Thing & {}${T}"
)
merged=0; total=0
for p in "${pairs[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$p")
  if [ "$n" -ne 5 ]; then echo "칸 수 $n ≠ 5: $p"; exit 3; fi
  IFS="$T" read -r name one two probe run <<< "$p"
  { echo "$one"; echo "$two"; echo "const probe: null = $probe;"
    if [ -n "$run" ]; then echo "console.log($run);"; fi; } > "$D/c.ts"
  out=$(cd "$D" && tsc --pretty false --noEmit -t es2022 --strict c.ts 2>&1)
  diag=$(grep -v '^c.ts(3,' <<< "$out" | grep -o '^c.ts([0-9,]*): error TS[0-9]*' | sed 's/^c.ts//; s/: error / /' | tr '\n' ' ' | sed 's/ $//')
  typ=$(sed -n "s/^c.ts(3,7): error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p" <<< "$out" | head -1)
  echo "[$name]"
  printf '    진단   %s\n' "${diag:-OK}"
  printf '    탐침   %s\n' "${typ:-(탐침 줄에 TS2322 없음)}"
  if [ -n "$run" ]; then
    rm -rf "$D/o"; (cd "$D" && tsc --pretty false -t es2022 --strict --outDir o c.ts > /dev/null 2>&1)
    printf '    node   %s\n' "$(node "$D/o/c.js" 2>&1 | head -1)"
  fi
  total=$((total+1)); [ -z "$diag" ] && merged=$((merged+1))
done
echo
echo "진단 없이 합쳐진 짝 $merged / $total"
```

- 여덟 짝 중 **진단이 나는** 짝은 어느 것이고, 코드는 무엇인가?
- `[interface+class]` 의 탐침과 `node` 칸은 각각 무엇인가?
- `[namespace+enum]` 의 탐침은 무엇인가?
- 마지막 줄의 수는 몇 / 몇인가?

### 2. 같은 이름의 메서드가 두 블록에 (예측)

```ts
// ex.33a.ts
// 같은 이름의 메서드가 두 인터페이스 블록에 -- 부르면 어느 쪽이 잡히나
interface Merged {
    pick(x: string): "from-block-1";
}
interface Merged {
    pick(x: string | number): "from-block-2";
}
type Single = {
    pick(x: string): "from-block-1";
    pick(x: string | number): "from-block-2";
};
declare const m: Merged;
declare const s: Single;

const p1: null = m.pick("a");
const p2: null = s.pick("a");
const p3: null = null as unknown as Merged["pick"];
const p4: null = null as unknown as Single["pick"];

interface Lit {
    tag(x: "on"): "literal-in-block-1";
    tag(x: string): "string-in-block-1";
}
interface Lit {
    tag(x: string): "string-in-block-2";
}
declare const l: Lit;
const p5: null = l.tag("on");
const p6: null = l.tag("off");
```

```bash
# ts30b-cmp33.sh
#!/usr/bin/env bash
# ex.33a.ts 를 세 판의 tsc 로 던져 출력을 글자 단위로 견준다 -- 옛 두 판은 이 머신의 다른 프로젝트에 깔린 것을 읽기만 했다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
a=$(tsc --pretty false --noEmit -t es2022 --strict ex.33a.ts 2>&1)
b=$(node "$OLD" --pretty false --noEmit -t es2022 --strict ex.33a.ts 2>&1)
c=$(node "$V49" --pretty false --noEmit -t es2022 --strict ex.33a.ts 2>&1)
echo "tsc $(tsc --version) · OLD $(node "$OLD" --version) · V49 $(node "$V49" --version)"
if [ "$a" = "$b" ]; then echo "7.0.2 = 5.9.3 · 진단 출력 한 글자도 같다"; else echo "7.0.2 ≠ 5.9.3"; diff <(echo "$a") <(echo "$b"); fi
if [ "$a" = "$c" ]; then echo "7.0.2 = 4.9.5 · 진단 출력 한 글자도 같다"; else echo "7.0.2 ≠ 4.9.5"; diff <(echo "$a") <(echo "$c"); fi
```

- 15행과 16행의 탐침은 각각 무엇인가? **같은가**?
- 17행과 18행의 탐침은 **같은가**?
- 28·29행은 각각 무엇인가?
- 세 판의 진단 출력은 같은가?

### 3. 함수·enum 에 namespace 를 덧붙이면 (예측)

```ts
// ex.33b.ts
// 함수와 namespace, enum 과 namespace -- 방출물과 node
function greet(name: string): string {
    return greet.prefix + name;
}
namespace greet {
    export const prefix = "hi ";
}
enum Color {
    Red,
    Blue,
}
namespace Color {
    export function parse(s: string): Color | undefined {
        return s === "red" ? Color.Red : s === "blue" ? Color.Blue : undefined;
    }
}
console.log("[1]", greet("kim"));
console.log("[2]", Color.parse("blue"));
console.log("[3]", Object.keys(Color));
```

- 진단은 몇 줄인가? 방출물에서 두 `namespace` 는 각각 무엇이 되는가?
- `node` 의 `[3]` 은 무엇을 찍는가?
- `--erasableSyntaxOnly` 를 주면 어느 줄이 막히는가?

### 4. 전역 보강 — 누가 보나 (예측)

```ts
// aug33.ts
declare global {
    interface Array<T> {
        total(): number;
    }
}
export {};
```

```ts
// user33.ts
try {
    console.log("total", [1, 2, 3].total());
} catch (e) {
    console.log((e as Error).constructor.name, (e as Error).message);
}
```

```ts
// noexp33.ts
declare global {
    interface Array<T> {
        other(): number;
    }
}
```

- `aug33.ts user33.ts` 를 함께 컴파일하면? `user33.ts` 하나만이면?
- 함께 방출해 `node e33/user33.js` 로 돌리면 무엇이 찍히는가?
- `noexp33.ts` 는 무엇이라고 막히는가?

### 5. `export {}` 가 없는 두 파일 (예측)

```ts
// set33a.ts
interface Settings {
    port: number;
}
const first: Settings = { port: 80 };
```

```ts
// set33b.ts
interface Settings {
    host: string;
}
const second: Settings = { host: "h" };
```

```ts
// set33c.ts
interface Settings {
    port: number;
}
const first: Settings = { port: 80 };
export {};
```

```ts
// set33d.ts
interface Settings {
    host: string;
}
const second: Settings = { host: "h" };
export {};
```

- `set33a.ts set33b.ts` 를 함께 컴파일하면 무엇이 나는가? `set33c.ts set33d.ts` 는?

### 6. 모듈 보강 (예측)

```ts
// lib33.mts
export interface Plugin {
    name: string;
}
export function make(name: string): Plugin {
    return { name };
}
```

```ts
// aug33a.mts
import { make } from "./lib33.mjs";
declare module "./lib33.mjs" {
    interface Plugin {
        version: number;
    }
}
declare module "./lib33-typo.mjs" {
    interface Plugin {
        typo: number;
    }
}
console.log(make("x").version);
```

```ts
// aug33b.mts
import { make, extra } from "./lib33.mjs";
declare module "./lib33.mjs" {
    interface Plugin {
        version?: number;
    }
    function extra(): string;
}
console.log("version", make("x").version);
console.log("extra", extra());
```

```js
// run33.mjs
try {
    await import("./aug33b.mjs");
} catch (e) {
    console.log(e.constructor.name, e.message);
}
```

- `lib33.mts aug33a.mts` 를 컴파일하면 진단이 **어느 파일에서** 나는가?
- `lib33.mts aug33b.mts` 는 컴파일되는가? 방출물을 `run33.mjs` 로 부르면 무엇이 찍히는가?

### 7. 네 탐침과 병합 규칙 (왜)

- 2번의 15\~18행 네 탐침을 병합 규칙 **한 문장**으로 설명할 수 있는가?

### 8. 세 실행 결과 (왜)

- 1번 `[interface+class]` · 4번 · 6번 `aug33b` 의 실행 결과에 **공통된 모양**이 있는가? 있다면 한 줄로 적고, 컴파일러가 그것을 왜 못 막는지 말할 수 있는가?

### 9. 보강의 경계 (경계)

- 4번에서 `user33.ts` 는 `aug33.ts` 를 **import 하지 않았다.** 4번의 두 컴파일을 가르는 것은 무엇인가? 「보강이 어디까지 닿나」의 경계는 **파일인가, 무엇인가**?

### 10. 병합이 안 되는 짝 (경계)

- 1번에서 진단이 난 짝들의 탐침은 **어느 쪽 선언**을 가리키는가? 그 짝들에 공통인 것은 무엇인가?

### 11. 08·23·31 과 잇기 (연결)

- 1번 `[interface+interface]` 는 08편의 어느 실측과 같은 답인가?
- 3번 `[3]` 은 31편의 어느 칸과 이어지는가?
- 핸드북은 「보강은 **새 최상위 선언**을 만들 수 없다」고 적는다. 6번 `aug33b` 는 그 문장과 **맞는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
