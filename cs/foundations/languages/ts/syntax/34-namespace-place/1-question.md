# ts/syntax/34 — `namespace` 의 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **34 는 33 에서 온다** — [**33번 주제**](../33-declaration-merging/) 3절이 「함수·enum 에 붙은 namespace 는 대상에 멤버를 다는 IIFE」 · 「`--erasableSyntaxOnly` 에서 값을 만드는 namespace 는 `TS1294`」를 이미 쟀다.
> 여기서는 **namespace 혼자 선 자리**, **7.0 이 막은 옛 표기**, 모듈이 표준이 된 뒤 **남은 용도**를 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 격자 스크립트는 **탐침을 한 파일씩 따로** 던지고, 판마다 **진단 코드**만 뽑는다(종료 코드는 판마다 다르다).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. `module` 낱말로 적은 꼴들을 판마다 (예측)

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

- 여덟 탐침 각각에 7.0.2 · 5.9.3 · 4.9.5 가 무엇을 내는가? 마지막 줄의 두 수는?

### 2. namespace 를 방출하면 (예측)

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

- 방출된 `.js` 에 `Shapes` 와 `Geo.Units` 는 각각 어떤 모양으로 남는가? `scale` 은?
- `node` 로 돌리면 `[3]` 에 무엇이 찍히는가?
- 같은 파일에 `--erasableSyntaxOnly` 를 주면 **몇 행**이 막히는가?

### 3. namespace 꼴들과 `--erasableSyntaxOnly` (예측)

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

- 여섯 꼴의 방출 줄 수는? 세 판의 진단은? 마지막 줄의 수는?

### 4. 옛 선언 파일의 한 줄 (예측)

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

- `useold34.ts old34.d.ts` 를 함께 던지면 7.0.2 가 무엇을 내는가? `--skipLibCheck` 를 붙이면?

### 5. `/// <reference path>` 가 있는 파일 하나 (예측)

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

- `ref34b.ts` **하나만** `--noEmit` 으로 던지면? `--listFilesOnly` 는 무엇을 찍는가?
- `--outDir e34r` 로 방출하면 파일이 몇 개 나오고, `node e34r/ref34b.js` 는 무엇을 찍는가?

### 6. 같은 `module` 낱말, 다른 답 (왜)

- 1번에서 `declare-module-id-dts` 와 `declare-module-string-dts` 는 둘 다 `.d.ts` 의 `declare module` 인데 7.0.2 의 답이 갈린다. 무엇이 둘을 가르는가?

### 7. `export` 하지 않은 멤버 (왜)

- 2번의 `scale` 은 방출물에 남는데 `Object.keys` 에는 없다. 방출물의 어느 구조가 그렇게 만드는가?

### 8. 3번의 수는 규칙인가 (경계)

- 3번 마지막 줄의 수를 근거로 「`--erasableSyntaxOnly` 는 방출물이 생기는 꼴만 막는다」고 **일반화**해도 되는가? 되지 않는다면 무엇이 더 필요한가?

### 9. 7.0 으로 올린 뒤의 「빌드가 된다」 (경계)

- 4번을 근거로, 7.0 으로 올린 프로젝트가 **진단 없이** 빌드된다는 사실이 옛 `.d.ts` 에 대해 무엇을 말하고 무엇을 말하지 않는가?

### 10. 33·02 와 잇기 (연결)

- 2번의 IIFE 는 33편 3절의 IIFE 와 **첫 줄이** 어떻게 다른가? 왜 다른가?
- 5번의 `ReferenceError` 를 7.0 이전에는 무엇이 막아 주었고, 그것은 02편 7절의 어느 칸과 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
