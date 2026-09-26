# ts/syntax/33 — 선언 병합 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html)(인터페이스 멤버의 병합 순서 · 단일 문자열 리터럴 매개변수의 예외 · namespace 가 합쳐지는 짝 · 「클래스는 다른 클래스·변수와 합쳐지지 않는다」 · 보강의 두 제약) ·
> [TypeScript 5.8 릴리스 노트 — `--erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 본판은 아래다. ★ 2절의 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 병합 규칙 격자(2창 탐침)이고, 급소는 3창(방출된 `.js` + `node`)이다.**
> 같은 이름을 **여덟 짝**으로 두 번 선언해 진단·탐침·실행을 격자로 세고(1절), 오버로드 순서를 탐침으로 묻는다(2절).
> ★★★ 그리고 **보강**(전역·모듈)은 **컴파일이 깨끗한데 실행이 깨지는** 자리다 — 타입은 있는데 **값은 없다**(4\~6절).
> ★★★ **33 은 08 에서 온다.** [**08번 주제**](../08-interface-vs-type/) 1절이 「`interface` 셋이 하나로 합쳐지고 `type` 은 `TS2300` · 같은 이름 다른 타입이면 `TS2717` · 호출 시그니처는 오버로드로 쌓인다」를 **이미 쟀다** — 인용한다.
> ★ 값 공간·타입 공간이 따로라는 것은 [**23번 주제**](../23-typeof-type-operator/) 1절이 정본이다.
> ★★★ **이 주제는 파일이 여럿이다** — 실험마다 파일 이름을 다르게 지었고(`aug33`·`set33a`…), **배너에 함께 컴파일한 파일 목록**을 적었다. **그 목록이 답을 바꾼다.**
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 1절 격자의 칸(진단·탐침 여덟씩 · `node` 넷)과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다 |
| **안 흔들린다** | ★★ 2절 — 세 판(4.9.5 · 5.9.3 · 7.0.2)의 진단 출력 | **한 글자도 같았다** — 그러나 「여러 판에서 같다」는 **보장이 아니다** |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 예외는 **타입과 메시지만** 찍었다 — ESM 링크 에러도 `import()` 로 받아 **경로 없이** 찍었다 |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | 보강의 결론은 **`.js` 에 무엇이 없나**다 |
| **안 잰 것** | 병합·보강이 검사 **시간**에 주는 영향 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**선언 병합은 「같은 이름의 서류철에 종이를 끼워 넣는 것」이다. 끼워 넣은 종이(타입)는 서류철에 들어가지만, 그 종이가 약속한 물건(값)은 누가 따로 가져다 놓아야 한다.**

| 비유 | 실체 |
|---|---|
| 같은 서류철에 **종이를 더 끼운다** | `interface` + `interface` — 멤버가 합쳐진다 |
| **서류철 이름이 겹치면 반려** | `type` + `type` · `class` + `class` — `TS2300` |
| ★★ 나중에 끼운 종이가 **맨 앞에** 온다 — 그런데 **목차는 끼운 순서대로** 적혀 있다 | 오버로드 해결은 **뒤 블록 먼저**, 표시된 타입은 **선언 순서** |
| **공용 서류철**에 종이를 끼운다 — 건물 전체가 본다 | `declare global { interface Array<T> { … } }` |
| ★★★ 종이에 「계산기 있음」이라 적었는데 **계산기는 없다** | 보강한 메서드를 부르면 `TypeError` — **타입은 있는데 값은 없다** |
| 개인 서류철인 줄 알았는데 **공용 서류철**이었다 | `export {}` 없는 파일 — 전역 스크립트라 **다른 파일의 같은 이름과 합쳐진다** |

- ★★★ 한 줄로 — 「**병합은 타입 공간의 일이다. 보강으로 더한 멤버는 방출물에 아무것도 만들지 않으므로, 값은 따로 채워야 한다.**」

```text
  보강의 한살이

  declare global { interface Array<T> { total(): number } }   ← 타입 공간에 종이 한 장
         │ 방출
  export {};                                                   ← 값 공간에는 아무것도 없다
         │
  [1, 2, 3].total()   tsc: exit 0   node: TypeError            ← 약속만 있고 물건이 없다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 어느 짝이 합쳐지고 어느 짝이 막히나** — 여덟 짝 × (진단 · 탐침 · 실행)(1절). 그리고 **같은 이름 메서드는 어느 순서로** 합쳐지나(2절).
2. **namespace 가 합쳐지면 방출물에 무엇이 생기나** — 함수·enum 에 붙는 즉시 실행 함수(3절).
3. **★★★ 전역·모듈 보강은 어디까지 닿고, 무엇을 약속하지 못하나** — 함께 컴파일한 파일 · `export {}` · 값 없는 타입(4\~6절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **병합 규칙 격자** | 짝 여덟 × (진단 · 탐침 · 실행) | 짝마다 파일 하나 | **본체**(1절) |
| ★★ **2창 — `null` 탐침** | 합쳐진 타입 · 고른 오버로드 | 계산된 것 | 1·2절 |
| ★★★ **3창 — 방출된 `.js` + `node`** | 보강·병합이 **런타임에 남긴 것(과 안 남긴 것)** | 실행 결과 | **급소**(3\~6절) |
| ★★ **판 격자** | 2절을 세 판으로 | 글자 대조 | 2절 |
| ★★ **「함께 컴파일한 파일」 대조** | 같은 파일을 **동반 파일을 바꿔** 두 번 | 진단 대조 | 4·5절 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — | — |

비용 — 격자 여덟 짝(검사 여덟 · 방출 넷 · `node` 넷) + 파일 열셋의 검사 아홉 번 · 방출 세 번 · `node` 세 번 + 세 판 대조.

```text
  이 주제의 축 — 「무엇과 무엇이 합쳐지나」 × 「값이 생기나」

                        합쳐지나     방출물에 값이 생기나
  interface + interface  ✓           아니다 — 둘 다 타입
  interface + class      ✓           class 몫만 — interface 가 더한 멤버는 값이 없다
  namespace + function   ✓           ✓ — 함수에 프로퍼티를 다는 IIFE
  namespace + enum       ✓           ✓ — enum 객체에 함수를 다는 IIFE
  namespace + class      ✓           ✓ — 클래스에 정적 값을 다는 IIFE
  type + type            TS2300
  interface + type       TS2300
  class + class          TS2300
  declare global / declare module    ✓(타입)   ★ 아니다 — 방출물에 흔적이 없다
```

### (1) ★★★ 병합 규칙 격자 — 같은 이름을 여덟 짝으로

**언제 쓰나** — 「이 두 선언이 합쳐지나 막히나」를 판단할 때. 이 주제의 규칙이 전부 이 격자에 있다.

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

```text
===== bash ts30b-mergegrid.sh (sh exit=0) =====
[interface+interface]
    진단   OK
    탐침   "a" | "b"
[interface+class]
    진단   OK
    탐침   "a" | "b"
    node   [1,"undefined"]
[namespace+function]
    진단   OK
    탐침   "b"
    node   [1,"x"]
[namespace+enum]
    진단   OK
    탐침   "A" | "b"
    node   [0,"x"]
[namespace+class]
    진단   OK
    탐침   "b" | "prototype"
    node   [1,"x"]
[type+type]
    진단   (1,6) TS2300 (2,6) TS2300
    탐침   "a"
[interface+type]
    진단   (1,11) TS2300 (2,6) TS2300
    탐침   "a"
[class+class]
    진단   (1,7) TS2300 (2,7) TS2300
    탐침   "a"

진단 없이 합쳐진 짝 5 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★ **`[interface+interface]`** — 진단 없음, `keyof Thing` 이 **`"a" | "b"`**. 08편 1절과 **같은 답**이다.
- ★★★ **`[interface+class]`** — 진단 없음, 탐침 **`"a" | "b"`** — 클래스 인스턴스 타입에 `b` 가 **붙었다.**
  그런데 `node` 는 **`[1,"undefined"]`** — `new Thing().b` 는 **`undefined`** 다. 클래스 몸통에는 `b` 가 **없으니까.** **타입은 있는데 값은 없다.**
- ★★ **`[namespace+function]`** — 탐침 `keyof typeof Thing` 이 **`"b"`**, `node` **`[1,"x"]`** — 함수에 `b` 가 **실제로** 달렸다.
- ★★ **`[namespace+enum]`** — 탐침 **`"A" | "b"`**, `node` **`[0,"x"]`** — enum 객체에 함수 `b` 가 달렸다.
- ★★ **`[namespace+class]`** — 탐침 **`"b" | "prototype"`**, `node` **`[1,"x"]`** — 클래스(생성자)에 정적 값이 달렸다.
- ★★★ **`[type+type]`·`[interface+type]`·`[class+class]`** — 셋 다 **`TS2300`**, **두 줄 모두**에 난다(`(1,…)` · `(2,…)`). 탐침은 **`"a"` — 첫 선언**을 가리킨다.
- ★★ 마지막 줄 **진단 없이 합쳐진 짝 5 / 8**.
- ★ 탐침에 **`& {}`** 를 붙였다 — 안 붙이면 `keyof Thing` 이 **펼쳐지지 않고 그 글자 그대로** 나왔다. 23편 4절도 `keyof typeof Color & {}` 로 펼쳤다.

```text
  여덟 짝 — 이 판의 격자를 그림으로

  짝                     진단                  탐침                 node
  interface+interface    OK                    "a" | "b"            —
  interface+class        OK                    "a" | "b"            ★ [1,"undefined"]   ← 타입만 붙었다
  namespace+function     OK                    "b"                  [1,"x"]             ← 값도 붙었다
  namespace+enum         OK                    "A" | "b"            [0,"x"]
  namespace+class        OK                    "b" | "prototype"    [1,"x"]
  type+type              TS2300 × 2            "a"(첫 선언)          —
  interface+type         TS2300 × 2            "a"
  class+class            TS2300 × 2            "a"
```

- ★★★ **합쳐지는 짝의 규칙** — 한쪽이 **타입만** 만드는 선언(`interface`)이거나 **값에 멤버를 다는** 선언(`namespace`)이면 합쳐진다.
  **둘 다 같은 공간을 「통째로」 차지하려는 짝**(`type`+`type` · `type`+`interface` · `class`+`class`)은 막힌다. 핸드북 — 「클래스는 다른 클래스나 변수와 합쳐지지 않는다.」

비용 — `interface`+`class` 는 **값이 없는 멤버를 타입에 달 수 있는** 유일한 짝이다. 믹스인 구현을 **따로** 붙이지 않으면 1절처럼 `undefined` 가 나온다.

### (2) ★★★ 오버로드 순서 — 고른 것과 표시된 것이 다르다

**언제 쓰나** — 라이브러리 타입을 보강해 **같은 이름 메서드에 새 시그니처**를 더할 때(`Document.createElement` 류).

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.33a.ts (tsc exit=1) =====
ex.33a.ts(15,7): error TS2322: Type '"from-block-2"' is not assignable to type 'null'.
ex.33a.ts(16,7): error TS2322: Type '"from-block-1"' is not assignable to type 'null'.
ex.33a.ts(17,7): error TS2322: Type '{ (x: string): "from-block-1"; (x: string | number): "from-block-2"; }' is not assignable to type 'null'.
ex.33a.ts(18,7): error TS2322: Type '{ (x: string): "from-block-1"; (x: string | number): "from-block-2"; }' is not assignable to type 'null'.
ex.33a.ts(28,7): error TS2322: Type '"literal-in-block-1"' is not assignable to type 'null'.
ex.33a.ts(29,7): error TS2322: Type '"string-in-block-2"' is not assignable to type 'null'.
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

```text
===== bash ts30b-cmp33.sh (sh exit=0) =====
tsc Version 7.0.2 · OLD Version 5.9.3 · V49 Version 4.9.5
7.0.2 = 5.9.3 · 진단 출력 한 글자도 같다
7.0.2 = 4.9.5 · 진단 출력 한 글자도 같다
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **15행 `m.pick("a")`(두 블록에 나뉜 `Merged`) → `"from-block-2"`.** **16행 `s.pick("a")`(한 블록의 `Single`) → `"from-block-1"`.**
  같은 두 시그니처인데 **고른 것이 다르다.** `Merged` 는 **뒤에 선언된 블록**의 시그니처를 먼저 봤다.
- ★★★ **그런데 17·18행이 한 글자도 같다** — 둘 다 `{ (x: string): "from-block-1"; (x: string | number): "from-block-2"; }`.
  **표시된 타입은 선언 순서**로 적히고, **오버로드 해결은 뒤 블록 먼저**다. **목차와 실제 순서가 다르다.**
- ★★ **28행 `l.tag("on")` → `"literal-in-block-1"`** — 뒤 블록이 먼저인데도 **첫 블록의 `"on"` 시그니처**가 잡혔다.
  핸드북의 예외 — 「매개변수 타입이 **단일 문자열 리터럴**인 시그니처는 병합된 오버로드 목록의 **맨 위로 올라간다**.」
- ★★ **29행 `l.tag("off")` → `"string-in-block-2"`** — 리터럴이 안 맞으면 다시 **뒤 블록 먼저**다.
- ★★ **세 판(4.9.5 · 5.9.3 · 7.0.2)의 진단 출력이 한 글자도 같다.** 이 규칙은 **최소한 4.9.5 부터** 같게 동작했다 — 그 이전은 모른다.

```text
  병합된 오버로드 — 해결 순서 대 표시 순서

  interface Merged { pick(x: string): "from-block-1" }               ← 블록 1
  interface Merged { pick(x: string | number): "from-block-2" }      ← 블록 2

  해결할 때 보는 순서(뒤 블록 먼저)          표시된 타입(선언 순서)
   ① (x: string | number): "from-block-2"    { (x: string): "from-block-1";
   ② (x: string): "from-block-1"               (x: string | number): "from-block-2"; }

  m.pick("a") → ① 이 먼저 맞는다 → "from-block-2"          ★ 표시만 보고 예측하면 틀린다

  예외: 단일 문자열 리터럴 매개변수는 맨 위로 — l.tag("on") → "literal-in-block-1"
```

- ★★ **이 순서가 왜 있나** — 보강하는 쪽(뒤 블록)이 **원래 시그니처보다 구체적인 것**을 더할 때 그것이 먼저 잡히게 하려는 규칙으로 읽힌다(핸드북의 `createElement` 예가 그 모양이다).
  이 문서의 `Merged` 는 거꾸로 **뒤 블록이 더 넓어서** 좁은 시그니처를 **가려 버렸다.**

비용 — 병합된 인터페이스의 오버로드는 **에디터가 보여 주는 타입으로 예측하면 틀린다.** 뒤 블록에 **넓은 시그니처**를 더하면 앞의 좁은 시그니처가 **안 쓰이게** 된다.

### (3) ★★ namespace 가 붙는 짝 — 방출물에 IIFE 가 생긴다

**언제 쓰나** — 함수에 속성을 달거나(`greet.prefix`), enum 에 도우미 함수를 달 때.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.33b.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e33n ex.33b.ts (tsc exit=0) =====
===== 방출된 e33n/ex.33b.js =====
"use strict";
// 함수와 namespace, enum 과 namespace -- 방출물과 node
function greet(name) {
    return greet.prefix + name;
}
(function (greet) {
    greet.prefix = "hi ";
})(greet || (greet = {}));
var Color;
(function (Color) {
    Color[Color["Red"] = 0] = "Red";
    Color[Color["Blue"] = 1] = "Blue";
})(Color || (Color = {}));
(function (Color) {
    function parse(s) {
        return s === "red" ? Color.Red : s === "blue" ? Color.Blue : undefined;
    }
    Color.parse = parse;
})(Color || (Color = {}));
console.log("[1]", greet("kim"));
console.log("[2]", Color.parse("blue"));
console.log("[3]", Object.keys(Color));
```

```text
===== node e33n/ex.33b.js (node exit=0) =====
[1] hi kim
[2] 1
[3] [ '0', '1', 'Red', 'Blue', 'parse' ]
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단 **0줄**.
- ★★★ 방출물 — `namespace greet { export const prefix = "hi "; }` 이 **`(function (greet) { greet.prefix = "hi "; })(greet || (greet = {}));`** 가 됐다.
  **이미 있는 함수 `greet` 에 프로퍼티를 다는 즉시 실행 함수**다. `namespace Color` 도 **enum 객체 `Color` 에 `parse` 를 다는** IIFE 가 됐다.
- ★★ `node` `[1] hi kim` · `[2] 1` — 둘 다 **값이 실제로 달렸다.**
- ★★★ **`[3] [ '0', '1', 'Red', 'Blue', 'parse' ]`** — enum 의 `Object.keys` 에 **함수 이름 `parse` 가 섞였다.**
  [**31번 주제**](../31-enum-pitfalls/) 1절에서 숫자 enum 의 `keys` 가 이미 **넷**(역매핑)이었다 — namespace 를 붙이면 **다섯**이 된다. enum 을 순회하는 코드가 **함수를 멤버로** 읽는다.

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.33b.ts (tsc exit=1) =====
ex.33b.ts(5,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.33b.ts(8,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.33b.ts(12,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

- ★★ `--erasableSyntaxOnly` 를 주면 **5행 `namespace greet`** · **8행 `enum Color`** · **12행 `namespace Color`** 가 각각 **`TS1294`**. 값을 만드는 namespace 는 **지우기만 해서는 JS 가 안 된다.**

```text
  namespace 병합 — 방출물

  function greet(…) {…}                  function greet(…) {…}
  namespace greet { prefix = "hi " }  ─> (function (greet) { greet.prefix = "hi "; })(greet || (greet = {}));

  enum Color { Red, Blue }            ─> var Color; (function (Color) { … 역매핑 … })(…);
  namespace Color { parse(…) }        ─> (function (Color) { … Color.parse = parse; })(Color || (Color = {}));

  Object.keys(Color) → [ '0', '1', 'Red', 'Blue', 'parse' ]   ← 멤버와 함수가 한 객체에
```

비용 — **enum + namespace 는 enum 순회를 깨뜨린다**(`[3]`). 도우미를 enum 밖 함수로 두면 이 문제가 없다.

### (4) ★★★ 전역 보강 — 보이는 범위는 「함께 컴파일한 파일」이다

**언제 쓰나** — `Array`·`Window`·`String` 같은 **전역 타입에 멤버를 더할 때**(폴리필·프레임워크 확장).

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict aug33.ts user33.ts ; 이어서 user33.ts 하나만 (sh exit=0) =====
(exit 0)
user33.ts(2,36): error TS2339: Property 'total' does not exist on type 'number[]'.
(exit 1)
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e33 aug33.ts user33.ts (tsc exit=0) =====
===== 방출된 e33/aug33.js =====
export {};
===== 방출된 e33/user33.js =====
"use strict";
try {
    console.log("total", [1, 2, 3].total());
}
catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== node e33/user33.js (node exit=0) =====
TypeError [1,2,3].total is not a function
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`aug33.ts user33.ts` 를 함께** — **`(exit 0)`**. `user33.ts` 는 `aug33.ts` 를 **import 하지 않았는데** `[1, 2, 3].total()` 이 통과했다.
- ★★★ **`user33.ts` 하나만** — **`TS2339`**(「Property 'total' does not exist on type 'number[]'.」). **같은 파일, 다른 답.**
  보강이 보이는 범위는 import 가 아니라 **「그 컴파일에 들어간 파일 전체」** 다. `tsconfig.json` 의 `include` 가 넓으면 **프로젝트 전체**가 본다.
- ★★★ 방출물 — `aug33.js` 는 **`export {};` 한 줄**이다. `declare global` 은 **흔적도 없다.** `user33.js` 는 `[1, 2, 3].total()` 을 **그대로** 부른다.
- ★★★ `node` — **`TypeError [1,2,3].total is not a function`**. 컴파일은 `exit 0` 이었다. **타입은 있는데 값은 없다.**

```ts
// noexp33.ts
declare global {
    interface Array<T> {
        other(): number;
    }
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict noexp33.ts (tsc exit=1) =====
noexp33.ts(1,9): error TS2669: Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.
```

- ★★ `export {}` 를 빼면 **`TS2669`**(「Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.」).
  `declare global` 은 **모듈 안에서만** 쓸 수 있다 — 스크립트 파일은 **이미 전역**이라 감쌀 필요가 없기 때문이다(5절).

```text
  전역 보강이 닿는 범위

  tsc aug33.ts user33.ts      ─> user33 이 total() 을 본다   exit 0
  tsc user33.ts               ─> 못 본다                      TS2339
                                 ★ import 한 줄 없이 — 「같은 컴파일에 있나」가 전부다

  방출물: aug33.js = export {};   → 값 공간에 total 은 없다 → node: TypeError
```

비용 — 전역 보강은 **구현을 어디서 로드했는지**를 타입이 모른다. 폴리필을 **로드하지 않은 진입점**에서도 타입은 통과한다.

### (5) ★★★ `export {}` 가 없으면 — 파일끼리 합쳐진다

**언제 쓰나** — 「이 파일의 `interface Settings` 는 이 파일 것」이라고 믿고 있을 때.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict set33a.ts set33b.ts ; 이어서 set33c.ts set33d.ts (sh exit=0) =====
set33a.ts(4,7): error TS2741: Property 'host' is missing in type '{ port: number; }' but required in type 'Settings'.
set33b.ts(4,7): error TS2741: Property 'port' is missing in type '{ host: string; }' but required in type 'Settings'.
(exit 1)
(exit 0)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`set33a.ts set33b.ts`** — **두 파일 다 `TS2741`**. `set33a` 는 「`host` 가 빠졌다」, `set33b` 는 「`port` 가 빠졌다」.
  **다른 파일의 `interface Settings` 가 합쳐졌다.** import·export 가 하나도 없는 파일은 **전역 스크립트**라 최상위 선언이 **전부 전역**이다.
- ★★ **`set33c.ts set33d.ts`**(끝에 `export {};` 한 줄) — **`(exit 0)`**. 파일이 **모듈**이 되어 `Settings` 가 **파일 안에** 갇혔다.
- ★★ 소스 차이는 **한 줄**(`export {};`)뿐이다.

```text
  같은 두 파일, 한 줄 차이

  set33a.ts  interface Settings { port }      set33c.ts  interface Settings { port }   export {};
  set33b.ts  interface Settings { host }      set33d.ts  interface Settings { host }   export {};
             ↓ 전역 스크립트 둘 → 합쳐진다                 ↓ 모듈 둘 → 따로
             TS2741 × 2                                     exit 0
```

비용 — `export {}` 없는 파일의 `interface` 는 **의도하지 않은 전역 보강**이다. 이름이 겹치는 순간 **엉뚱한 파일에서** 에러가 난다.

### (6) ★★★ 모듈 보강 — 원래 모듈까지 바꾸고, 없는 값도 약속한다

**언제 쓰나** — 라이브러리의 **export 된 인터페이스**에 멤버를 더할 때(플러그인 시스템·프레임워크 확장).

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict lib33.mts aug33a.mts (tsc exit=1) =====
aug33a.mts(7,16): error TS2664: Invalid module name in augmentation, module './lib33-typo.mjs' cannot be found.
lib33.mts(5,5): error TS2741: Property 'version' is missing in type '{ name: string; }' but required in type 'Plugin'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`lib33.mts(5,5): error TS2741`** — 「Property 'version' is missing …」. 진단이 **보강한 파일이 아니라 원래 라이브러리 파일**에서 났다.
  `aug33a` 가 `Plugin` 에 `version: number` 를 **필수로** 더하자, `lib33` 의 `make()` 가 돌려주는 `{ name }` 이 **더 이상 `Plugin` 이 아니게** 됐다.
  **보강은 원래 모듈의 타입을 바꾼다** — 그 모듈 안의 코드까지.
- ★★ **`aug33a.mts(7,16): error TS2664`** — 「Invalid module name in augmentation, module './lib33-typo.mjs' cannot be found.」 **이름이 틀리면 막아 준다**(모듈 파일 안에서는).

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

```text
===== tsc --pretty false -t es2022 --strict --outDir e33b lib33.mts aug33b.mts (tsc exit=0) =====
===== 방출된 e33b/aug33b.mjs =====
import { make, extra } from "./lib33.mjs";
console.log("version", make("x").version);
console.log("extra", extra());
```

```text
===== cp run33.mjs e33b/ && cd e33b && node run33.mjs (node exit=0) =====
SyntaxError The requested module './lib33.mjs' does not provide an export named 'extra'
```

- ★★ `aug33b` 는 `version` 을 **선택(`?`)** 으로 더하고, **`function extra(): string;`** 을 새로 선언했다. **진단 0줄, `exit 0`.**
- ★★★ 방출물 — `import { make, extra } from "./lib33.mjs";` 가 **그대로 남았다.** `declare module` 블록은 **흔적도 없다.**
- ★★★ `node` — **`SyntaxError The requested module './lib33.mjs' does not provide an export named 'extra'`**. ESM 은 **링크 단계**에서 없는 export 를 잡는다 — **한 줄도 실행되기 전에** 멈췄다.
- ★★★ **핸드북과 이 판이 어긋난 자리다.** 핸드북은 보강의 제약으로 「**새 최상위 선언을 만들 수 없다** — 기존 선언의 패치만」이라고 적는다.
  7.0.2 는 `function extra(): string;` 을 **진단 없이 받았다.** 막았다면 컴파일에서 끝났을 일이 **런타임 `SyntaxError`** 로 넘어갔다.
  ★ 이것이 규칙이 바뀐 것인지, 문서가 낡은 것인지, 이 모양이 「새 최상위 선언」에 **해당하지 않는** 것인지는 **확인하지 못했다.** 던져서 본 것은 「통과했고 런타임에 깨졌다」까지다.

```text
  모듈 보강 — 세 가지가 한꺼번에

  declare module "./lib33.mjs" { interface Plugin { version: number } }
      → lib33.mts 안의 make() 가 TS2741            ★ 원래 모듈이 깨진다

  declare module "./lib33-typo.mjs" { … }
      → TS2664                                       이름 오타는 잡는다

  declare module "./lib33.mjs" { function extra(): string; }
      → tsc exit 0 → 방출물에 import { extra } 가 남는다 → node: SyntaxError   ★ 값 없는 약속
```

비용 — 모듈 보강은 **라이브러리의 소스를 고치지 않고 타입만** 바꾼다. 필수 멤버를 더하면 **라이브러리 쪽 코드가 깨지고**, 값을 약속하면 **아무도 그 값을 만들지 않는다.**

### (7) ★ 설정 대조

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.33a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.33b.ts    exit 0 = exit 0 · 출력 한 글자도 같다
```

- ★★ `--strict` 를 꺼도 **두 파일 다 한 글자도 같다.** 병합 규칙은 `strict` 에 **안 달렸다.**
- ★ 4\~6절의 여러 파일 실험은 `--strict` 로만 돌렸다.

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  interface T { a }  interface T { b }         멤버가 합쳐진다                        (1절 · 08편)
  class C { a }      interface C { b }         인스턴스 타입에 b — 값은 없다          (1절)
  function f() {}    namespace f { export … }  함수에 프로퍼티 — IIFE 방출           (1·3절)
  enum E { … }       namespace E { export … }  enum 객체에 멤버 — IIFE 방출          (1·3절)
  declare global { interface Array<T> { … } }  전역 보강 — 모듈 파일 안에서만        (4절)
  declare module "./m.mjs" { interface I { … } }  모듈 보강 — 원래 모듈의 타입이 바뀐다 (6절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `type` 두 번 · `interface`+`type` · `class` 두 번 | `TS2300` × 2 | 1절 |
| 병합한 같은 이름 프로퍼티의 타입이 다름 | `TS2717` | 08편 1절 |
| 보강한 멤버를 보강 파일 **없이** 컴파일 | `TS2339` | 4절 |
| 스크립트 파일에서 `declare global` | `TS2669` | 4절 |
| 전역 스크립트 둘이 같은 `interface` | `TS2741`(합쳐진 결과) | 5절 |
| 필수 멤버 보강 → 원래 모듈의 반환값 | `TS2741` — **원래 모듈 파일에서** | 6절 |
| 없는 모듈 이름으로 보강 | `TS2664` | 6절 |
| `--erasableSyntaxOnly` 에서 값을 만드는 `namespace`·`enum` | `TS1294` | 3절 |

**규칙 불릿**

- ★★★ **`interface`·`namespace` 는 합쳐지고, `type`·`class` 끼리는 `TS2300`**(1절).
- ★★★ **병합된 오버로드는 뒤 블록이 먼저 해결된다 — 표시된 타입은 선언 순서다**(2절). 단일 문자열 리터럴 시그니처는 **맨 위로.**
- ★★ **namespace 병합은 값을 만든다** — 대상 객체에 멤버를 다는 IIFE(3절).
- ★★★ **보강은 타입만 만든다** — 방출물에 흔적이 없고, 값은 따로 채워야 한다(4·6절).
- ★★★ **전역 보강이 닿는 범위는 「같은 컴파일에 들어간 파일」이다** — import 와 무관하다(4절).
- ★★ **`export {}` 없는 파일은 전역 스크립트다** — 같은 이름이 파일을 건너 합쳐진다(5절).

## 어디서 틀리나

- ★★★ 「**보강했으니 그 메서드를 쓸 수 있다**」 — **타입만** 있다. 구현을 로드하지 않으면 `TypeError`(4절)·`SyntaxError`(6절).
- ★★★ 「**전역 보강은 import 한 파일에서만 보인다**」 — **컴파일에 들어간 모든 파일**이 본다(4절). 보강 파일이 빠지면 **같은 코드가 `TS2339`**.
- ★★★ 「**에디터가 보여 주는 오버로드 순서대로 해결된다**」 — **뒤 블록 먼저**다(2절 15·16행). 표시(17·18행)는 같은데 고른 것이 다르다.
- ★★★ 「**모듈 보강은 내 파일 안의 일이다**」 — **원래 모듈의 타입을 바꿔** 그쪽 파일에서 `TS2741` 이 난다(6절).
- ★★ 「**이 파일의 `interface` 는 이 파일 것**」 — `export {}` 가 없으면 **전역**이다(5절).
- ★★ 「**`class` 에 `interface` 를 합치면 멤버가 생긴다**」 — **타입만** 생긴다. `undefined`(1절).
- ★★ 「**enum 에 도우미를 namespace 로 붙여도 순회는 그대로**」 — `Object.keys` 에 **`parse` 가 섞인다**(3절).
- ★ 「**핸드북대로 보강에서 새 선언은 막힌다**」 — 이 판은 **`function extra()` 를 받았다**(6절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(핸드북)** | 병합된 인터페이스의 함수 멤버는 오버로드가 되고 **뒤 선언이 우선**(목록 앞) · 단일 문자열 리터럴 시그니처는 **맨 위로** | 핸드북 · 2절 15·28·29행 |
| **언어 보장(핸드북)** | namespace 는 클래스·함수·enum·namespace 와 합쳐진다 · 클래스는 다른 클래스·변수와 합쳐지지 않는다 | 핸드북 · 1절 |
| **언어 보장(핸드북)** | 보강은 **새 최상위 선언을 만들 수 없고** default export 는 보강할 수 없다 | 핸드북 — ★ 6절에서 **첫째 문장과 어긋나는 관찰**이 나왔다 |
| **언어 보장(5.8)** | `--erasableSyntaxOnly` 는 런타임 코드가 있는 namespace·enum 을 막는다 | 릴리스 노트 · 3절 |
| **★ 이 판(7.0.2)의 관찰** | ★★ 병합된 오버로드의 **표시 순서가 선언 순서** — 해결 순서와 다르다 | 2절 17·18행 |
| **★ 이 판의 관찰** | ★★★ 보강 안의 `function extra(): string;` 이 **진단 없이** 통과 | 6절 |
| **★ 판 격자** | 2절 진단 출력이 4.9.5 · 5.9.3 · 7.0.2 에서 **같다** | 2절 — **보장이 아니라 세 번의 관찰**이다 |
| **★ 엔진(node v18)의 관찰** | 없는 export 는 ESM **링크 단계**의 `SyntaxError` | 6절 |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | 검사 **시간** | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **`interface` 병합** — 라이브러리가 **확장 지점으로 열어 둔** 인터페이스(플러그인 옵션 등) | 자기 코드의 타입을 **여러 파일에 흩어** 적을 때 — 어디서 더했는지 추적이 어렵다(08편) |
| **전역 보강** — 폴리필을 **진입점에서 반드시** 로드할 때 · 전역 변수(`window.__APP__`)의 타입 | 구현이 **어떤 진입점에서는 안 로드될 수** 있을 때 — 4절 `TypeError` |
| **모듈 보강** — 라이브러리가 **선택 멤버**를 더하라고 안내할 때 | ★★★ **필수 멤버**를 더할 때 — 원래 모듈이 깨진다(6절) · **값을 약속할 때** — `SyntaxError`(6절) |
| **namespace + 함수** — 함수에 정적 속성을 다는 옛 API 의 타입 | ★★ **enum 에 도우미** — 순회가 깨진다(3절) · `--erasableSyntaxOnly` 를 쓸 때 |
| **`export {}`** — 모든 `.ts` 파일(모듈이 되게) | — |

## 핵심 문장

1. **`interface`·`namespace` 는 합쳐지고 `type`·`class` 끼리는 막힌다** — 격자 **5 / 8**.
2. **병합된 오버로드는 뒤 블록이 먼저 해결되는데, 표시는 선언 순서다** — 보이는 타입으로 예측하면 틀린다.
3. **보강은 타입만 만든다** — 방출물에 흔적이 없고, 값이 없으면 컴파일이 깨끗한 채 `TypeError`·`SyntaxError` 로 깨진다.
4. **보강이 닿는 범위는 import 가 아니라 컴파일에 든 파일 전체이고, `export {}` 없는 파일은 그 자체가 전역이다.**

## 관련 자료

- [**08번 주제** — `interface` 대 `type`](../08-interface-vs-type/) — ★★★ **README 의 선행.** `interface` 병합 · `type` 의 `TS2300` · 충돌하면 `TS2717` · 호출 시그니처의 오버로드 쌓임은 그쪽 1절이 정본이다. **여기는 짝을 넓히고, 순서와 보강을 방출물로 보는 데서부터.**
- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — 값 공간·타입 공간이 따로라는 정본. 1절의 「타입만 붙었다」가 그 위에 선다.
- [**31번 주제** — 열거형의 함정](../31-enum-pitfalls/) — enum 의 `Object.keys` 가 이미 넷이다. 3절이 거기에 **다섯째**를 더한다.
- [**30번 주제** — 타입 단언과 non-null `!`](../30-type-assertions-and-non-null/) — 「타입은 있는데 값은 없다」의 다른 모양(`as`·`!`).
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — 오버로드가 **위에서부터** 맞춰진다는 일반 규칙. 2절의 병합 순서는 그 목록을 **누가 어떤 순서로 만드나**다.
- [목록의 **34번 주제**](../34-namespace-place/)(`namespace` 의 자리) — namespace 자체의 용도는 그쪽.
- [목록의 **37번 주제**](../37-writing-declaration-files/)(선언 파일 작성) · **38번 주제**(앰비언트·전역 타입 구성) — `.d.ts`·`declare module "x"`(앰비언트 모듈 선언)·`types`/`typeRoots` 는 그쪽. **여기서는 보강(augmentation)만** 봤다.

## 용어 풀이

> **선언 병합(declaration merging)** — 같은 이름의 선언 여러 개를 컴파일러가 **하나로 합치는** 것. 타입 공간에서 일어난다.\
> 예: 1절 `[interface+interface]` — `keyof` 가 `"a" | "b"`.

> **전역 보강(global augmentation)** — 모듈 파일 안에서 `declare global { … }` 로 전역 타입에 멤버를 더하는 것.\
> 예: 4절 `Array<T>` 에 `total()`.

> **모듈 보강(module augmentation)** — `declare module "경로" { … }` 로 **다른 모듈이 export 한 선언**에 멤버를 더하는 것.\
> 예: 6절 `Plugin` 에 `version`.

> **전역 스크립트** — import·export 가 하나도 없는 파일. 최상위 선언이 **전역**에 놓인다.\
> 예: 5절 `set33a.ts`·`set33b.ts` 의 `Settings` 가 합쳐졌다.

> **`export {}`** — 아무것도 내보내지 않지만 파일을 **모듈로 만드는** 한 줄.\
> 예: 5절 `set33c.ts` — 합쳐지지 않는다.

> **`TS2300`** — 「Duplicate identifier 'X'.」 합쳐질 수 없는 두 선언.\
> 예: 1절 `[type+type]`.

> **`TS2669`** — 「Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.」\
> 예: 4절 `noexp33.ts`.

> **`TS2664`** — 「Invalid module name in augmentation, module '…' cannot be found.」\
> 예: 6절 `./lib33-typo.mjs`.

## 더 들어가면

- **2절의 해결 순서가 왜 「뒤 블록 먼저」인가** — 핸드북은 규칙만 적는다(「later … higher precedence」). 표시 순서가 선언 순서인 것은 **이 판의 관찰**이고, 둘이 왜 다른지는 명세 문장으로 확인하지 않았다.
- **스크립트 파일에서 `interface Array<T> { … }` 만 적으면** — `declare global` 없이도 전역 `Array` 가 보강된다(5절과 같은 기제로 **읽히지만 던지지 않았다**).
- **보강 파일 안의 `import` 의 역할** — 6절의 `aug33a`·`aug33b` 는 `lib33` 을 **import 한 모듈**이다. import 없이 `declare module "./lib33.mjs"` 만 적으면 보강이 아니라 **앰비언트 모듈 선언**이 될 수 있다 — [목록의 **37번 주제**](../37-writing-declaration-files/). **여기서는 안 던졌다.**
- **default export 는 보강할 수 없다** — 핸드북의 둘째 제약. **던지지 않았다.**
