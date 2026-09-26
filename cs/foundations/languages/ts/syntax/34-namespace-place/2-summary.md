# ts/syntax/34 — `namespace` 의 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Namespaces and Modules](https://www.typescriptlang.org/docs/handbook/namespaces-and-modules.html)(「새 프로젝트는 모듈이 권장되는 조직 방식」 · namespace 는 전역의 이름 붙은 객체라 `outFile` 로 이어 붙일 수 있다 · 모듈 파일을 `/// <reference>` 로 가리키는 것은 흔한 실수) ·
> [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)(「`namespace` 자리에 `module` 을 쓰는 것은 이제 **hard deprecation**」 · `outFile` 제거) ·
> [TypeScript 5.8 릴리스 노트 — `--erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 본판은 아래다. ★ 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.
> ★ **6.0 은 이 머신에 없다** — 「6.0 에서 deprecation」은 릴리스 글의 문장이고, 던져서 본 것은 **5.9.3 은 받고 7.0.2 는 막는다**까지다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 판 격자(세 판 × 진단 코드)이고, 급소는 3창(방출된 `.js` + `node`)이다.**
> README 의 과녁 「7.0 에서 `module` 키워드 표기가 막혔다」를 **세 판**으로 확인하고(1절), 값이 든 namespace 가 **IIFE** 가 되는 것과 타입만 든 namespace 가 **아무것도 안 남기는** 것을 방출물로 가른다(2·3절).
> ★★★ **34 는 33(선언 병합) 의 결론에서 온다.** [**33번 주제**](../33-declaration-merging/) 3절이 「함수·enum 에 붙은 namespace 는 **대상에 멤버를 다는 IIFE**」 · 「`--erasableSyntaxOnly` 에서 값을 만드는 namespace 는 `TS1294`」 · enum 순회에 `parse` 가 섞이는 것을 **이미 쟀다** — 인용한다. **여기는 namespace 혼자 선 자리와, 모듈이 표준이 된 뒤 남은 용도**다.
> ★ `--erasableSyntaxOnly` 가 enum 을 막는 판 격자는 [**31번 주제**](../31-enum-pitfalls/) 3절, 매개변수 프로퍼티는 [**32번 주제**](../32-class-type-aspects/) 3절이 정본이다. **여기서는 namespace 꼴 여섯 칸만** 더한다.
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 1·3절 격자의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **판에 매인다** | ★★ **종료 코드** — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3 은 `2`([**35번 주제**](../35-module-resolution/) 6절의 블록) | 그래서 격자는 **종료 코드가 아니라 진단 코드로** 갈랐다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 예외는 **타입과 메시지만** 찍었다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | 이 주제의 질문은 **`.js` 에 무엇이 남나**다 — `.d.ts` 는 **입력**으로만 썼다(4절) |
| **안 잰 것** | namespace 가 번들 크기·로딩 시간에 주는 영향 | **재지 않았다** — 방출 **줄 수**만 셌다 |

## 한눈에 — 쉽게 말하면

**namespace 는 「건물 안에 칸막이를 친 사무실」이고, 모듈은 「따로 떨어진 건물」이다. 칸막이는 TS 가 쳐 주는 것이라, 칸막이 안에 가구(값)가 있으면 방출물에 칸막이 공사(IIFE)가 남고, 서류(타입)만 있으면 공사 흔적이 없다.**

| 비유 | 실체 |
|---|---|
| **칸막이 사무실**(한 건물 안) | `namespace Geo { … }` — 전역의 **이름 붙은 객체** 하나 |
| **따로 떨어진 건물**(주소가 있다) | `import`/`export` 가 있는 파일 — **모듈** |
| 칸막이 안에 **가구가 있다** → 공사가 남는다 | 값이 든 namespace → 방출물에 **IIFE** |
| 칸막이 안에 **서류만 있다** → 공사 흔적 없음 | 타입만 든 namespace → 방출물 **0줄** |
| ★★ 옛 간판 「`module` 호」를 **7.0 이 떼어 냈다** | `module Foo {}` → 7.0.2 `TS1540`, 5.9.3·4.9.5 는 **통과** |
| 「옆 사무실 서류 참조」 쪽지 | `/// <reference path>` — **컴파일에 파일을 더할 뿐**, 실행 때 옆 파일을 **불러 주지 않는다** |

- ★★★ 한 줄로 — 「**namespace 는 TS 가 JS 객체로 번역해 주는 문법이다. 값이 들면 번역물(IIFE)이 생기고, 그래서 `--erasableSyntaxOnly` 가 막고, 새 코드에서는 모듈이 그 자리를 가져갔다.**」

```text
  namespace 의 두 얼굴

  namespace Shapes { export interface Point {…} }   ─ 방출 ─>  (아무것도 없다)        ← 타입 공간만
  namespace Geo.Units { export const meter = 1 }    ─ 방출 ─>  var Geo; (function (Geo) { … })(…);   ← 값 공간에 객체

  module Foo { … }     7.0.2: TS1540      5.9.3 · 4.9.5: 통과      ← 같은 뜻, 옛 표기
  declare module "x"   세 판 모두 통과                             ← 따옴표면 「모듈 선언」 — 다른 물건
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `module` 키워드로 쓴 namespace 는 어느 판에서 막히나** — 여덟 꼴 × 세 판(1절). 따옴표를 쓴 `declare module "x"` 도 같이 막히나?
2. **★★ namespace 는 방출물에 무엇을 남기나** — 값이 든 것·타입만 든 것·점으로 이은 것(2절). 그리고 **그 차이가 곧 `--erasableSyntaxOnly` 의 경계인가**(3절).
3. **★★ 모듈이 표준이 된 뒤 namespace 는 어디에 남나** — `declare namespace`(타입 묶기) · 병합(33 인용) · 옛 `.d.ts` 와 `skipLibCheck`(4절) · `/// <reference>` 의 경계(5절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **판 격자** | 꼴 여덟 × (7.0.2 · 5.9.3 · 4.9.5) 의 진단 코드 | 세 판 대조 | **본체**(1절) |
| ★★★ **3창 — 방출된 `.js` + `node`** | namespace 가 **값 공간에 남긴 것** | 실행 결과 | **급소**(2·5절) |
| ★★ **방출 줄 수 × 진단 격자** | 꼴 여섯 × (방출 줄 · 세 판의 `--erasableSyntaxOnly`) | 수로 센다 | 3절 |
| ★ **「함께 컴파일한 파일」 목록** | `--listFilesOnly` — `/// <reference>` 가 무엇을 끌어오나 | 파일 목록 | 5절 |
| ★ **부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — | — |
| **2창 — `null` 탐침** | 4절 한 칸(`Legacy.a` 가 `number`) | 계산된 것 | 조수로만 |

비용 — 격자 두 벌(꼴 여덟 × 세 판 · 꼴 여섯 × 방출 + 세 판) + 파일 다섯의 검사·방출·`node`(정답 파일 「실행 검증」 표).

```text
  이 주제의 축 — 「어떻게 적었나」 × 「무엇이 남나」 × 「어느 판인가」

                               방출물          --erasableSyntaxOnly    7.0.2 에서
  namespace N { 타입만 }        0줄             OK                      OK
  namespace N { 값 }            IIFE            TS1294                  OK
  declare namespace N { … }     0줄             OK                      OK
  module N { … }                (namespace 와 같다)                     ★ TS1540
  declare module "x" { … }      0줄             —                       OK   ← 이름이 따옴표면 모듈 선언(37번)
```

### (1) ★★★ `module` 키워드 — 세 판 격자

**언제 쓰나** — 옛 코드·옛 `.d.ts` 를 7.0 으로 올릴 때. `module Foo {}` 는 **`namespace` 가 생기기 전의 표기**다.

```bash
# ts34b-modkw.sh
#!/usr/bin/env bash
# 식별자 이름 namespace 를 module 키워드로 적은 꼴과 그 이웃 -- 세 판의 tsc 에 한 파일씩 던진다
# 칸: 판마다 진단 코드(없으면 OK) -- 옛 두 판은 이 머신의 다른 프로젝트에 깔린 것을 읽기만 했다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'   # 구분자는 탭 -- 소스 안에 ; 가 나온다(규칙 32)
probes=(
  "module-value${T}ts${T}module Foo { export const a = 1; }"
  "module-dotted${T}ts${T}module Foo.Bar { export const a = 1; }"
  "module-types-only${T}ts${T}module Foo { export type T = string; }"
  "declare-module-id${T}ts${T}declare module Foo { const a: number; }"
  "declare-module-id-dts${T}d.ts${T}declare module Foo { const a: number; }"
  "namespace-value${T}ts${T}namespace Foo { export const a = 1; }"
  "declare-namespace-dts${T}d.ts${T}declare namespace Foo { const a: number; }"
  "declare-module-string-dts${T}d.ts${T}declare module \"foo\" { export const a: number; }"
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-28s %-16s %-16s %s\n' "탐침" "7.0.2" "5.9.3" "4.9.5"
blocked=0; split=0; total=0
for p in "${probes[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$p")
  if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $p"; exit 3; fi
  IFS="$T" read -r name ext src <<< "$p"
  echo "$src" > "$D/c.$ext"
  a=$(cd "$D" && tsc --pretty false --noEmit -t es2022 --strict "c.$ext" 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" --pretty false --noEmit -t es2022 --strict "c.$ext" 2>&1 | codes)
  c=$(cd "$D" && node "$V49" --pretty false --noEmit -t es2022 --strict "c.$ext" 2>&1 | codes)
  rm -f "$D/c.$ext"
  printf '%-28s %-16s %-16s %s\n' "$name" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1))
  [ -n "$a" ] && blocked=$((blocked+1))
  [ "$a" != "$b" ] && split=$((split+1))
done
echo
echo "7.0.2 에서 진단이 난 탐침 $blocked / $total · 7.0.2 와 5.9.3 이 갈린 탐침 $split / $total"
```

```text
===== bash ts34b-modkw.sh (sh exit=0) =====
탐침                       7.0.2            5.9.3            4.9.5
module-value                 TS1540           OK               OK
module-dotted                TS1540 TS1540    OK               OK
module-types-only            TS1540           OK               OK
declare-module-id            TS1540           OK               OK
declare-module-id-dts        TS1540           OK               OK
namespace-value              OK               OK               OK
declare-namespace-dts        OK               OK               OK
declare-module-string-dts    OK               OK               OK

7.0.2 에서 진단이 난 탐침 5 / 8 · 7.0.2 와 5.9.3 이 갈린 탐침 5 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`module-value`·`module-dotted`·`module-types-only`·`declare-module-id` 넷이 7.0.2 에서 `TS1540`** — 「A 'namespace' declaration should not be declared using the 'module' keyword. Please use the 'namespace' keyword instead.」
  같은 넷이 **5.9.3 · 4.9.5 에서는 `OK`** 다. README 의 과녁 「7.0 에서 막혔다」가 **세 판으로 확인됐다.**
- ★★★ **`declare-module-id-dts` — `.d.ts` 안이어도 `TS1540`**. `declare` 가 붙어도, 선언 파일이어도 **이름이 식별자면** 막힌다.
- ★★ **`module-dotted` 는 `TS1540` 이 둘** — `Foo.Bar` 의 **이름 조각마다** 하나씩 난다.
- ★★ **`namespace-value`·`declare-namespace-dts` 는 세 판 다 `OK`** — 막힌 것은 **뜻이 아니라 낱말**이다. `module` → `namespace` 한 낱말을 바꾸면 끝난다.
- ★★★ **`declare-module-string-dts`(`declare module "foo"`) 는 세 판 다 `OK`** — 이름이 **따옴표 문자열**이면 namespace 가 아니라 **앰비언트 모듈 선언**이다. 같은 `module` 낱말인데 **다른 물건**이라 안 막힌다(목록의 **37번 주제**).
- ★★ 마지막 줄 **7.0.2 에서 진단이 난 탐침 5 / 8 · 7.0.2 와 5.9.3 이 갈린 탐침 5 / 8** — 갈린 다섯이 **정확히 7.0.2 가 막은 다섯**이다.
- ★ **5.9.3 은 한 줄도 안 낸다** — 릴리스 글이 말하는 「6.0 의 hard deprecation」은 **이 머신에 6.0 이 없어 못 봤다.** 5.9.3 이 명령줄에 **경고조차 안 찍는다**는 것까지가 관찰이다.

```text
  module 낱말의 두 뜻 — 7.0.2

  module Foo { … }            이름이 식별자 → namespace 의 옛 표기   → TS1540 (조각마다)
  declare module Foo { … }    〃 (.d.ts 안이어도)                    → TS1540
  declare module "foo" { … }  이름이 문자열 → 앰비언트 모듈 선언     → OK
                              ★ 낱말은 같고, 가르는 것은 이름의 따옴표다
```

비용 — **옛 `.d.ts` 한 줄이 7.0 빌드를 깬다.** 단 4절에서 보듯 `skipLibCheck` 를 켠 프로젝트는 **그 진단을 못 본다.**

### (2) ★★★ 방출물 — 타입만 든 namespace 는 흔적이 없다

**언제 쓰나** — 「namespace 로 묶으면 런타임 비용이 있나」를 판단할 때.

```ts
// ex.34a.ts
// 타입만 든 namespace 와 값이 든 namespace -- 방출물에 무엇이 남나
namespace Shapes {
    export interface Point {
        x: number;
        y: number;
    }
    export type Id = string;
}
namespace Geo.Units {
    export const meter = 1;
    export function km(n: number): number {
        return n * 1000 * meter;
    }
    const scale = 3;
}
const p: Shapes.Point = { x: 1, y: 2 };
console.log("[1]", p);
console.log("[2]", Geo.Units.km(2));
console.log("[3]", Object.keys(Geo.Units));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.34a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e34a ex.34a.ts (tsc exit=0) =====
===== 방출된 e34a/ex.34a.js =====
"use strict";
var Geo;
(function (Geo) {
    var Units;
    (function (Units) {
        Units.meter = 1;
        function km(n) {
            return n * 1000 * Units.meter;
        }
        Units.km = km;
        const scale = 3;
    })(Units = Geo.Units || (Geo.Units = {}));
})(Geo || (Geo = {}));
const p = { x: 1, y: 2 };
console.log("[1]", p);
console.log("[2]", Geo.Units.km(2));
console.log("[3]", Object.keys(Geo.Units));
```

```text
===== node e34a/ex.34a.js (node exit=0) =====
[1] { x: 1, y: 2 }
[2] 2000
[3] [ 'meter', 'km' ]
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단 **0줄**.
- ★★★ **`namespace Shapes` 는 방출물에 한 글자도 없다** — 인터페이스와 타입 별칭만 들어 있어 **지울 것만 있다.** `p` 의 타입 표기 `Shapes.Point` 도 사라졌다.
- ★★★ **`namespace Geo.Units` 는 IIFE 두 겹**이 됐다 — `var Geo; (function (Geo) { var Units; (function (Units) { … })(Units = Geo.Units || (Geo.Units = {})); })(Geo || (Geo = {}));`.
  점으로 이은 이름은 **바깥 객체 안에 안쪽 객체를 만드는** 중첩이다.
- ★★ `export` 한 `meter`·`km` 은 **`Units.meter = 1` · `Units.km = km`** 로 객체에 달렸고, `export` 안 한 `scale` 은 **IIFE 안의 지역 `const`** 로 남았다.
- ★★ `node` `[3] [ 'meter', 'km' ]` — **`export` 한 것만** 객체의 키다. 지역 `scale` 은 **남아 있지만 밖에서 안 보인다**(클로저 — JS 의 함수 스코프).
- ★ 33편 3절의 IIFE 는 **이미 있는 함수·enum 에 멤버를 다는** 꼴(`greet || (greet = {})`)이었다. 여기는 **namespace 혼자** 라 `var Geo;` 를 **새로 만든다.** 모양은 같다.

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.34a.ts (tsc exit=1) =====
ex.34a.ts(9,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.34a.ts(9,15): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

- ★★ 같은 파일에 `--erasableSyntaxOnly` — **9행 `Geo.Units` 의 두 조각(열 11·15)** 만 `TS1294`. **2행 `Shapes` 는 안 걸렸다.** 3절이 그 경계를 격자로 센다.

```text
  namespace 의 방출 — 넣은 것과 남은 것

  namespace Shapes {                      (없음)
    export interface Point {…}
    export type Id = string;
  }
  namespace Geo.Units {                   var Geo;
    export const meter = 1;          ─>   (function (Geo) { var Units; (function (Units) {
    export function km(…) {…}                 Units.meter = 1;  function km(n) {…}  Units.km = km;
    const scale = 3;                          const scale = 3;              ← 지역으로 남는다
  }                                       })(Units = Geo.Units || (Geo.Units = {})); })(Geo || (Geo = {}));
```

비용 — 값이 든 namespace 는 **전역 변수 하나 + 즉시 실행 함수**다. 모듈이라면 번들러가 쓰지 않는 export 를 떨어낼 수 있지만, IIFE 안의 대입은 **한 덩어리**다(떨어내는지는 **재지 않았다**).

### (3) ★★ `--erasableSyntaxOnly` — 방출 줄이 있는 꼴만 막히나

**언제 쓰나** — 타입만 지우고 실행하는 도구(node 의 타입 제거 실행 등)와 같이 쓸 코드를 고를 때. 이 플래그의 뜻은 「**지우기만 해서 JS 가 되는 문법**만 허용」이다(5.8 릴리스 노트).

```bash
# ts34b-erase34.sh
#!/usr/bin/env bash
# namespace 꼴 여섯 -- 7.0.2 의 방출 줄 수(끔) 와 --erasableSyntaxOnly 를 세 판에 준 진단
# 방출 줄 수 = 방출된 .js 에서 빈 줄과 "use strict"; 를 뺀 줄 수
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
probes=(
  "types-only${T}namespace N { export type T = string; export interface I { a: number } }"
  "value${T}namespace N { export const v = 1; }"
  "dotted-value${T}namespace A.B { export const v = 1; }"
  "empty${T}namespace N {}"
  "declare${T}declare namespace N { const v: number; }"
  "alias-of-declare${T}declare namespace N { const v: number; } import V = N.v;"
)
codes() { grep -o '([0-9,]*): error TS[0-9]*' | sed 's/: error / /' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-18s %-8s %-26s %-26s %s\n' "탐침" "방출줄" "7.0.2" "5.9.3" "4.9.5"
same=0; total=0
for p in "${probes[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$p")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $p"; exit 3; fi
  IFS="$T" read -r name src <<< "$p"
  echo "$src" > "$D/c.ts"
  rm -rf "$D/o"; (cd "$D" && tsc --pretty false -t es2022 --strict --outDir o c.ts > /dev/null 2>&1)
  lines=$(grep -v -e '^$' -e '^"use strict";$' "$D/o/c.js" | wc -l)
  a=$(cd "$D" && tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly c.ts 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly c.ts 2>&1 | codes)
  c=$(cd "$D" && node "$V49" --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly c.ts 2>&1 | grep -o 'error TS[0-9]*' | sed 's/^error //')
  printf '%-18s %-8s %-26s %-26s %s\n' "$name" "$lines" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1))
  if { [ "$lines" -gt 0 ] && [ -n "$a" ]; } || { [ "$lines" -eq 0 ] && [ -z "$a" ]; }; then same=$((same+1)); fi
done
echo
echo "「방출 줄이 있다」와 「7.0.2 에서 TS1294」가 같은 답을 낸 탐침 $same / $total"
```

```text
===== bash ts34b-erase34.sh (sh exit=0) =====
탐침             방출줄 7.0.2                      5.9.3                      4.9.5
types-only         0        OK                         OK                         TS5023
value              4        (1,11) TS1294              (1,11) TS1294              TS5023
dotted-value       7        (1,11) TS1294 (1,13) TS1294 (1,11) TS1294 (1,13) TS1294 TS5023
empty              0        OK                         OK                         TS5023
declare            0        OK                         OK                         TS5023
alias-of-declare   1        (1,42) TS1294              (1,42) TS1294              TS5023

「방출 줄이 있다」와 「7.0.2 에서 TS1294」가 같은 답을 낸 탐침 6 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`types-only`·`empty`·`declare` 는 방출 0줄 · `TS1294` 없음.** **`value`(4줄)·`dotted-value`(7줄)·`alias-of-declare`(1줄)는 방출 줄이 있고 `TS1294`.**
- ★★★ 마지막 줄 **6 / 6** — 이 여섯 꼴에서는 「**방출물이 생기는가**」와 「**`TS1294` 가 나는가**」가 **한 칸도 안 어긋났다.**
  ★ 단 이것은 **이 여섯 칸의 관찰**이다 — 36번 주제에서 **방출 0줄인데 `TS1294`** 인 꼴(`import type X = require(…)`)이 나온다. 이 규칙은 「방출물의 유무」가 아니라 **문법 꼴**로 판정한다고 읽는 편이 안전하다.
- ★★ **`alias-of-declare`** — `declare namespace` 는 값이 없는데도, 그 멤버를 **`import V = N.v;` 로 별칭하는 순간** `var V = N.v;` 한 줄이 생기고 `TS1294`(열 42 — `import` 자리).
- ★★ **`dotted-value` 는 `TS1294` 가 둘**(열 11·13) — 1절의 `TS1540` 처럼 **이름 조각마다**.
- ★★ 4.9.5 는 **전부 `TS5023`** — 「Unknown compiler option」. 이 플래그는 **5.8** 부터다(31편 3절과 같은 칸).
- ★ 7.0.2 와 5.9.3 이 **여섯 칸 다 같다.**

```text
  --erasableSyntaxOnly 가 보는 것 (이 여섯 칸)

  types-only · empty · declare      방출 0줄  →  OK
  value · dotted-value              방출 IIFE →  TS1294  (이름 조각마다)
  declare + import V = N.v          방출 1줄  →  TS1294  (import 자리)
                                    ★ 6 / 6 일치 — 그러나 규칙은 「꼴」이다(36번)
```

비용 — `--erasableSyntaxOnly` 를 켜면 **값이 든 namespace 는 전부** 못 쓴다. 타입 묶기(`types-only`)와 `declare namespace` 는 남는다.

### (4) ★★ 남은 용도 — `declare namespace` 와 옛 `.d.ts` 의 `module`

**언제 쓰나** — 전역 스크립트 라이브러리(`<script>` 로 싣는 것)의 타입을 **점 표기**로 묶을 때 · 옛 타입 선언을 가진 의존성을 7.0 으로 올릴 때.

```ts
// old34.d.ts
declare module Legacy {
    const a: number;
}
```

```ts
// useold34.ts
const probe: null = Legacy.a;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict useold34.ts old34.d.ts ; 이어서 --skipLibCheck 를 붙여 한 번 더 (sh exit=0) =====
old34.d.ts(1,16): error TS1540: A 'namespace' declaration should not be declared using the 'module' keyword. Please use the 'namespace' keyword instead.
useold34.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
useold34.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

그림 해설 — 한 단계에 한 문장.

- ★★ 그냥 던지면 — **`old34.d.ts(1,16) TS1540`**. 옛 `.d.ts` 의 `declare module Legacy` 가 1절과 같이 막혔다.
- ★★ `useold34.ts(1,7) TS2322`(「Type 'number' …」) — 탐침이 `Legacy.a` 를 **`number` 로 읽었다.** 막혔어도 **선언 자체는 쓰였다.**
- ★★★ **`--skipLibCheck` 를 붙이면 `TS1540` 이 사라진다** — 탐침의 `TS2322` 만 남는다. `skipLibCheck` 는 **`.d.ts` 의 진단을 통째로 건너뛴다**(목록의 **37번 주제**가 그 창이다).
  그래서 `node_modules` 의 옛 선언이 이 표기를 써도 **`skipLibCheck` 프로젝트는 7.0 에서 안 깨진다** — 그리고 **안 깨졌다는 사실 때문에 모른다.**

**남은 용도 정리** — 던진 것과 인용한 것을 갈라 적는다.

| 용도 | 근거 | 7.0.2 에서 |
|---|---|---|
| ★★ **`declare namespace` 로 전역 라이브러리의 타입을 점 표기로 묶기** | 1절 `declare-namespace-dts` · 3절 `declare` — 방출 0줄 · `TS1294` 없음 | 된다 |
| ★★ **타입만 묶기**(`namespace Shapes { interface … }`) | 2절 · 3절 `types-only` | 된다 — 방출 0줄 |
| ★★ **함수·enum·클래스에 정적 멤버 달기** | [**33번 주제**](../33-declaration-merging/) 1·3절 — IIFE · enum 순회에 섞임 | 된다 — 단 `--erasableSyntaxOnly` 에서 `TS1294` |
| ★ **`<script>` 여러 개를 `outFile` 로 이어 붙이기** | 핸드북의 원래 용도 · [**02번 주제**](../02-type-checking-vs-emit/) 7절 — **`outFile` 은 7.0 에서 `TS5102`** | ★ **이어 붙이는 도구 쪽이 사라졌다**(5절) |
| — **새 코드의 조직 단위** | 핸드북 — 「새 프로젝트는 모듈이 권장」 | 모듈을 쓴다 |

비용 — **`skipLibCheck` 는 이 주제의 판 경계를 가린다.** 7.0 으로 올린 뒤 「빌드가 된다」는 **`.d.ts` 를 안 봤다**는 뜻일 수 있다.

### (5) ★ `/// <reference path>` 의 경계 — 컴파일에는 더하고 실행에는 안 불러 준다

**언제 쓰나** — 파일을 건너는 namespace(전역 스크립트) 코드를 읽을 때.

```ts
// ref34a.ts
namespace App {
    export const name = "app34";
}
```

```ts
// ref34b.ts
/// <reference path="ref34a.ts" />
try {
    console.log("[1]", App.name);
} catch (e) {
    console.log((e as Error).constructor.name, (e as Error).message);
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ref34b.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --listFilesOnly ref34b.ts | grep -v '/lib\.' | sed "s#$PWD#.#" (tsc exit=0) =====
./ref34a.ts
./ref34b.ts
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e34r ref34b.ts (tsc exit=0) =====
===== 방출된 e34r/ref34a.js =====
"use strict";
var App;
(function (App) {
    App.name = "app34";
})(App || (App = {}));
===== 방출된 e34r/ref34b.js =====
"use strict";
/// <reference path="ref34a.ts" />
try {
    console.log("[1]", App.name);
}
catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== node e34r/ref34b.js (node exit=0) =====
ReferenceError App is not defined
```

그림 해설 — 한 단계에 한 문장.

- ★★ **`ref34b.ts` 하나만** 던졌는데 진단 **0줄** — `App.name` 이 보였다.
- ★★ `--listFilesOnly` 가 **`./ref34a.ts` · `./ref34b.ts`** 둘을 찍는다 — `/// <reference path>` 가 **`ref34a.ts` 를 컴파일에 끌어왔다**(lib 파일 줄은 배너의 `grep -v` 로 뺐다).
  33편 4절 「보강이 보이는 범위는 **함께 컴파일한 파일**」과 같은 기제다 — 여기서는 **파일이 스스로** 목록을 늘렸다.
- ★★ 방출은 **파일 둘** — `ref34a.js` 가 IIFE, `ref34b.js` 는 **`/// <reference path="ref34a.ts" />` 주석을 그대로 싣고** `App.name` 을 부른다.
- ★★★ `node e34r/ref34b.js` → **`ReferenceError App is not defined`**. 주석은 **node 에게 아무 뜻이 없다** — `ref34a.js` 를 누가 먼저 실어 주지 않으면 `App` 은 없다.
- ★ 그 「먼저 실어 주기」를 해 주던 것이 **`outFile` 로 한 파일에 이어 붙이기**였고, 7.0 에서 **`outFile` 이 없어졌다**(02편 7절 `TS5102` — 여기서는 다시 안 던졌다). `<script>` 순서로 싣는 HTML 이 아니면 **파일을 건너는 namespace 는 받쳐 줄 도구가 없다.**

```text
  /// <reference path> — 두 층이 다르게 읽는다

  tsc   : ref34b.ts 가 ref34a.ts 를 가리킨다 → 둘 다 컴파일 → App 이 보인다     exit 0
  방출  : ref34a.js · ref34b.js 두 파일 (주석은 그대로)
  node  : ref34b.js 만 실행 → 주석은 그냥 주석 → App 없음                         ReferenceError
          ★ import 가 아니다 — 실행 순서를 아무도 정해 주지 않는다
```

비용 — `/// <reference path>` 는 **타입 검사기에게만 하는 말**이다. 모듈의 `import` 는 **런타임이 따르는 말**이다. 핸드북도 「모듈 파일을 `/// <reference>` 로 가리키는 것은 흔한 실수」라고 적는다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  namespace N { export … }            전역 객체 N 하나 — 값이 들면 IIFE               (2절)
  namespace A.B { … }                  중첩 IIFE — 이름 조각마다 진단이 따로 난다       (1·2·3절)
  namespace N { export interface … }   타입만 — 방출 0줄                                (2·3절)
  declare namespace N { … }            값 없이 모양만 — 방출 0줄 · .d.ts 에서 점 표기   (1·3·4절)
  import V = N.v;                      namespace 멤버 별칭 — var 한 줄                  (3절)
  /// <reference path="a.ts" />        컴파일에 파일을 더한다 — 실행과 무관             (5절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `module Foo { … }` · `declare module Foo { … }`(식별자 이름) — 7.0.2 | `TS1540` — 이름 조각마다 | 1절 · 4절 |
| 같은 꼴 — 5.9.3 · 4.9.5 | **없음** | 1절 |
| `--erasableSyntaxOnly` 에서 값이 든 namespace · `import V = N.v` | `TS1294` | 2·3절 |
| 4.9.5 에서 `--erasableSyntaxOnly` | `TS5023` | 3절 |
| 7.0 에서 `--outFile` | `TS5102` | 02편 7절 |

**규칙 불릿**

- ★★★ **7.0.2 는 식별자 이름의 `module` 선언을 `TS1540` 으로 막는다** — `.d.ts` 안이어도. 5.9.3·4.9.5 는 조용하다(1절).
- ★★★ **따옴표 이름의 `declare module "x"` 는 다른 물건이다** — 세 판 다 받는다(1절).
- ★★ **값이 든 namespace 는 IIFE, 타입만 든 것은 0줄**(2절).
- ★★ **`--erasableSyntaxOnly` 는 값이 든 namespace 와 별칭 `import =` 을 막는다** — 이 여섯 칸에서 방출 유무와 6 / 6 일치(3절).
- ★ **`/// <reference path>` 는 컴파일 목록을 늘릴 뿐 실행을 준비하지 않는다**(5절).

## 어디서 틀리나

- ★★★ 「**`module Foo` 와 `namespace Foo` 는 같으니 둘 다 된다**」 — 뜻은 같지만 **7.0.2 는 앞쪽을 `TS1540`** 으로 막는다(1절). 5.9.3 에서 경고 한 줄 없이 통과했으니 **올리기 전에는 모른다.**
- ★★★ 「**`module` 낱말이 막혔으니 `declare module "x"` 도 고쳐야 한다**」 — **따옴표 이름은 안 막힌다**(1절). 고칠 것은 식별자 이름 쪽뿐이다.
- ★★★ 「**7.0 으로 올렸는데 빌드가 되니 옛 `.d.ts` 는 괜찮다**」 — `skipLibCheck` 가 **`TS1540` 을 숨겼을** 수 있다(4절).
- ★★ 「**namespace 로 묶으면 무조건 런타임 코드가 생긴다**」 — **타입만 들면 0줄**(2·3절).
- ★★ 「**`export` 안 한 멤버는 방출에서 빠진다**」 — **지역 변수로 남는다**, 밖에서 안 보일 뿐이다(2절 `scale`).
- ★★ 「**`declare namespace` 는 값이 없으니 `--erasableSyntaxOnly` 와 늘 산다**」 — **`import V = N.v` 로 별칭하면** `TS1294`(3절).
- ★ 「**`/// <reference path>` 는 옛날식 `import` 다**」 — 컴파일 목록만 늘린다. 실행은 `ReferenceError`(5절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(핸드북)** | namespace 는 **전역의 이름 붙은 JS 객체**이고 파일을 건널 수 있다 · 새 프로젝트는 모듈이 권장 | 핸드북 · 2절 |
| **언어 보장(릴리스 글)** | `namespace` 자리의 `module` 은 **6.0 에서 hard deprecation** · `outFile` 제거 | 6.0 릴리스 글 — ★ 6.0 은 **던지지 못했다** |
| **컴파일러(7.0.2) 구현** | ★★★ 식별자 이름 `module` 선언에 **`TS1540`**(이름 조각마다) | 1절 |
| **컴파일러(5.9.3 · 4.9.5)** | 같은 꼴을 **진단 없이** 받는다 | 1절 |
| **언어 보장(5.8)** | `--erasableSyntaxOnly` 는 런타임 코드가 있는 namespace 를 막는다 | 릴리스 노트 · 3절 |
| **★ 이 판의 관찰** | 여섯 꼴에서 「방출 줄 있음」 ⇔ `TS1294` 가 **6 / 6** | 3절 — ★ 36번의 반례가 있다 |
| **★ 이 판의 관찰** | `skipLibCheck` 가 `.d.ts` 의 `TS1540` 을 숨긴다 | 4절 |
| **호스트(node v18)** | `/// <reference>` 주석은 **아무 뜻이 없다** — 실행 순서를 안 정한다 | 5절 `ReferenceError` |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | 번들 크기·로딩 시간 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **`declare namespace`** — `<script>` 로 싣는 전역 라이브러리의 타입(점 표기) | **새 코드의 파일 나누기** — 모듈(`import`/`export`)을 쓴다 |
| **타입만 묶는 namespace** — 방출 0줄 · `--erasableSyntaxOnly` 와도 산다 | ★★★ **`module Foo {}` 표기** — 7.0.2 `TS1540` |
| **함수·enum 에 정적 멤버**(33편) — 옛 API 의 모양을 그대로 적을 때 | ★★ **`--erasableSyntaxOnly` 를 쓰는 프로젝트의 값 namespace** — `TS1294` |
| — | ★ **파일을 건너는 namespace + `/// <reference>`** — 7.0 에서 `outFile` 이 없어 실행을 받쳐 줄 도구가 없다 |

## 핵심 문장

1. **7.0.2 는 `module Foo {}` 를 `TS1540` 으로 막고, 5.9.3·4.9.5 는 조용히 받는다** — 격자 **5 / 8** 이 7.0.2 에서 막혔고, 갈린 다섯이 그 다섯이다. 따옴표 이름의 `declare module "x"` 는 다른 물건이라 안 막힌다.
2. **값이 든 namespace 는 IIFE 가 되고, 타입만 든 namespace 는 0줄이다** — 그래서 `--erasableSyntaxOnly` 는 앞쪽만 막는다(이 여섯 칸에서 **6 / 6**).
3. **`skipLibCheck` 는 옛 `.d.ts` 의 `TS1540` 을 숨긴다** — 올린 뒤 「된다」가 「안 봤다」일 수 있다.
4. **`/// <reference path>` 는 컴파일 목록을 늘릴 뿐이다** — 실행 순서를 정하던 `outFile` 이 7.0 에서 없어졌으니, 새 코드의 자리는 모듈이다.

## 관련 자료

- [**33번 주제** — 선언 병합](../33-declaration-merging/) — ★★★ **README 의 선행.** namespace + 함수·enum·클래스 병합 · IIFE · enum 순회에 `parse` 가 섞이는 것 · `TS1294` 셋은 그쪽이 정본이다. **여기는 namespace 혼자 선 자리와 판 경계부터.**
- [**31번 주제** — 열거형의 함정](../31-enum-pitfalls/) — `--erasableSyntaxOnly` 판 격자(7.0.2·5.9.3 `TS1294`, 4.9.5 `TS5023`)의 정본.
- [**32번 주제** — 클래스의 타입 측면](../32-class-type-aspects/) — 같은 플래그가 매개변수 프로퍼티를 막는 칸.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — `outFile` 의 `TS5102` · 제거된 값의 `TS5108` 은 그쪽 7절.
- 목록의 **36번 주제**(타입 전용 import·export) — `--erasableSyntaxOnly` 의 import 쪽 칸. 3절의 6 / 6 에 **반례**가 거기 있다.
- 목록의 **37번 주제**(선언 파일 작성) — `declare module "x"`(앰비언트 모듈 선언) · `skipLibCheck` 의 본체.

## 용어 풀이

> **namespace** — TS 전용 문법. 전역에 **이름 붙은 객체** 하나를 만들고 그 안에 멤버를 모은다. 값이 들면 방출물에 IIFE 가 생긴다.\
> 예: 2절 `namespace Geo.Units` → `var Geo; (function (Geo) { … })(…)`.

> **IIFE(즉시 실행 함수)** — 정의하자마자 부르는 함수 `(function (x) { … })(…)`. 지역 변수를 가둬 두는 옛 JS 관용구다.\
> 예: 2절 `scale` 이 IIFE 의 지역으로 남았다.

> **`declare namespace`** — 값 없이 **모양만** 적는 namespace. 방출물에 아무것도 안 남는다.\
> 예: 1절 `declare-namespace-dts` · 3절 `declare`.

> **앰비언트 모듈 선언** — `declare module "이름" { … }` — **따옴표 이름**의 모듈에 타입을 붙인다. namespace 와 낱말만 같다.\
> 예: 1절 `declare-module-string-dts` 가 세 판 다 `OK`.

> **`TS1540`** — 「A 'namespace' declaration should not be declared using the 'module' keyword. Please use the 'namespace' keyword instead.」 7.0.2 에서 본 코드.\
> 예: 1절 `module-value`.

> **`TS1294`** — 「This syntax is not allowed when 'erasableSyntaxOnly' is enabled.」\
> 예: 3절 `value`.

> **`/// <reference path="…" />`** — 세 줄 빗금 지시문. 가리킨 파일을 **컴파일에 더한다.** 실행에는 영향이 없다.\
> 예: 5절 `--listFilesOnly` 에 `ref34a.ts` 가 나타났다.

## 더 들어가면

- **6.0 의 모습** — 릴리스 글은 「hard deprecation」이라 적는다. 5.x 의 deprecation 관례대로라면 **경고를 끄는 설정**이 있었을 것으로 읽히지만, **6.0 이 이 머신에 없어 던지지 못했다.**
- **`export namespace`** — 모듈 파일 안의 `export namespace N { … }` 는 모듈이면서 namespace 다. 그 꼴과 `export module N {}` 은 **캡처하지 않았다.**
- **namespace 와 트리 셰이킹** — IIFE 안의 대입은 번들러가 떨어내기 어렵다고 흔히 말한다. **재지 않았다.**
