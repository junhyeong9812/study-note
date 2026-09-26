# ts/syntax/47 — 데코레이터 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript 5.0 릴리스 노트 — Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html) · [Handbook — Decorators](https://www.typescriptlang.org/docs/handbook/decorators.html) · [TC39 proposal-decorators](https://github.com/tc39/proposal-decorators).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** 「JS 데코레이터 제안은 2026-09 기준 stage 3 이고 어느 ES 판에도 없다」는 **README 의 서술**이고, 이 문서가 직접 보인 것은 **이 머신의 세 엔진(node 18 · node 20 · Chrome 151)이 `@` 를 파싱하지 못한다**는 것까지다(4절).
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`** · node 20 은 **`NODE20`**. **라이브러리는 설치하지 않았다**(`reflect-metadata` 포함).

```text
===== tsc --version · "$TSC_OLD" · "$TSC_49" · "$TSC_39" --version · node · "$NODE20" --version · google-chrome --version (sh exit=0) =====
Version 7.0.2
Version 5.9.3
Version 4.9.5
Version 3.9.3
v18.19.1
v20.19.6
Google Chrome 151.0.7922.173 
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 「두 데코레이터 판 격자」(자리 일곱 × 표준/`experimentalDecorators` × 판 셋 — 칸마다 진단 · 방출 도우미 · `node` 가 본 인자)이다.** 둘째 기둥은 **3창(방출물 + `node`)** — 시그니처 쌍 · 평가/적용 순서 · 메타데이터(2·3절).
> ★★★ **세 층을 가른다 — TS 구현 / TC39 제안 단계 / 엔진 지원.** 이 문서의 「표준 데코레이터」는 **TS 5.0 이 구현한 제안판**을 뜻한다. **JS 표준이 아니다** — 엔진은 아직 문법을 모른다(4절).
> ★★★ **제5의 상태 — 매개변수 데코레이터는 표준 판에서 「에러 + 방출에서 조용히 빠짐」** 이다. 진단 창은 `TS1206` 을 말하지만 **방출물은 여전히 나오고**, `node` 창에서는 그 데코레이터가 **한 번도 불리지 않는다**(1절 `param` 칸 — 창을 바꿔 `__param` 줄 수로 물었다).
> ★★ **47 은 32 에서 온다** — [**32번 주제**](../32-class-type-aspects/) 5절이 `useDefineForClassFields` 판 격자로 **필드 선언이 「정의」냐 「대입」이냐**를 쟀다. 여기서는 다시 재지 않고 **표준 필드 데코레이터가 그 세 설정에서 같은 값을 내나**만 본다(2절 끝).
> ★★ 격자 스크립트는 **설정 진단이 칸에 들면 멈추고(`exit 4`), 방출 도우미가 한 종류뿐이면 멈춘다(`exit 5`).** 둘 다 제출 전에 가짜 판으로 **실제로 멈추는지** 돌렸다(1절 끝).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드 · `(행,열)` · 방출 도우미 이름(`__esDecorate`·`__decorate`·`__param`) | 같은 입력·같은 판이면 같다 |
| **안 흔들린다** | `node` 가 찍은 인자 · 호출 순서 로그 | 결정적 — 5.9.3 방출물과 **한 글자도 같았다**(2절) |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 줄의 **수** | 스크립트가 센다 |
| **판에 매인다** | ★ 종료 코드 — 방출하면서 진단이 있으면 `2` | 격자는 **진단 코드·도우미·로그로** 갈랐다 |
| **판에 매인다** | ★ 방출물 **줄 수** — 7.0.2 는 `"use strict";` 한 줄이 더 붙는다(4절) | 뜻은 같다 |
| **★ 부적용 — 5창(`.d.ts`)** | 데코레이터는 선언 파일의 모양을 바꾸지 않는 **실행 시점의 함수 호출**이다 | — |
| **못 잰 것** | TC39 의 **현재 단계** · Chrome 의 실험 플래그 | 외부 문서를 열지 않았다 · 플래그 이름을 확인할 길이 없다 |

## 한눈에 — 쉽게 말하면

데코레이터는 「클래스가 만들어지는 순간 불려 오는 검수원」이다. 검수원은 두 회사가 있다 — 옛 회사(레거시)는 **물건과 창고 번호와 선반 명세서**(`target, key, descriptor`)를 받고, 새 회사(표준)는 **물건과 작업 지시서**(`value, context`)를 받는다. 같은 사람을 두 회사에 보내면 **서류가 달라** 엉뚱한 칸을 읽는다. 그리고 이 검수원 제도는 아직 **법(JS)이 아니라 TS 라는 대행사의 규칙**이다 — 대행사가 서류를 JS 로 풀어 써 주지 않으면 엔진은 알아듣지 못한다.

| 비유 | 실체 |
|---|---|
| 클래스가 **만들어지는 순간** 불려 오는 검수원 | 데코레이터 함수 — `new` 가 아니라 **클래스 정의 때** 돈다(2절 `-- new A()` 앞에서 끝남) |
| 옛 회사 서류 **셋** | 레거시 `(target, key, descriptor)` — 1절 `args=3` |
| ★★★ 새 회사 서류 **둘** | 표준 `(value, context)` — `context.kind`·`name`·`addInitializer`(1절 `args=2`) |
| ★★★ 같은 사람을 **두 회사에** | 레거시 모양 함수를 표준 판에 — 느슨하면 `key` 가 `[object Object]`, 엄격하면 `TypeError`(2절) |
| 옛 회사만 받는 **자리** | 매개변수 데코레이터 — 표준 판은 `TS1206` 후 **조용히 뺀다**(1절) |
| ★★ 대행사가 **풀어 써 주는** 서류 | `__esDecorate`(표준) · `__decorate`(레거시) 도우미 — `target` 이 `esnext` 면 **안 풀어 쓴다**(4절) |
| 법이 아직 **모르는** 제도 | node 18 · 20 · Chrome 151 이 `@d` 에서 `SyntaxError`(4절) |

- ★★★ 한 줄로 — 「TS 의 데코레이터는 두 벌이다. `experimentalDecorators` 가 켜지면 옛 벌(3인자·매개변수 가능·`emitDecoratorMetadata`), 꺼지면 5.0 부터의 새 벌(2인자·`context`·매개변수 불가·`context.metadata`). 어느 쪽이든 **TS 가 JS 로 풀어 써야** 돈다 — 엔진은 `@` 를 모른다.」

```text
  같은 `@show` 한 줄이 두 판에서 받는 것

  experimentalDecorators 켬 (레거시)          끔 (표준 · TS 5.0+)
  ─────────────────────────────────          ─────────────────────────────
  메서드  (prototype, "m", descriptor)          (함수, { kind: "method", name: "m", … })
  필드    (prototype, "x", undefined)           (undefined, { kind: "field", name: "x", … })
  클래스  (생성자)                               (생성자, { kind: "class", name: "A", … })
  매개변수 (prototype, "m", 0)                   ✗ TS1206 — 방출에서 빠진다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 표준과 레거시는 무엇이 다르고 판마다 어떻게 갈리나** — 자리 일곱 × 두 판 × 판 셋 격자(1절) · 시그니처 쌍(2절).
2. **★★ 여러 데코레이터는 언제 평가되고 언제 적용되나 · 메타데이터가 필요하면 무엇을 고르나** — 순서 로그(2절) · `emitDecoratorMetadata` 대 `context.metadata`(3절).
3. **★★★ JS 쪽은 어디까지 왔나** — 엔진 셋의 파싱 · `target: esnext` 방출(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **두 판 격자** | 자리 일곱 × 표준/레거시 × 7.0.2 · 5.9.3 · 4.9.5 | 진단 · 방출 도우미 · `node` 가 본 인자 | **본체**(1절) |
| ★★★ **3창 — 방출물 + `node`** | 시그니처 쌍 · 순서 · 필드 초기화 · 메타데이터 | 실행 로그 | 둘째 기둥(2·3절) |
| ★★ **엔진 창** | `node --check` 둘 · Chrome 151 의 간접 `eval` | `SyntaxError` | 4절 |
| ★★★ **제5의 상태** | 표준 판의 매개변수 데코레이터 — 진단은 있는데 방출이 **조용히 뺀다** → `__param` 줄 수·`node` 로그로 바꿔 물었다 | — | 1절 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언 모양을 바꾸지 않는다 | — | — |

비용 — 격자 42칸(7 × 2 × 3) + 자기검사 둘 · 매개변수 둘 · 시그니처 둘 · 순서 둘 · 필드 초기화 셋 · 메타데이터 셋(node 18/20) · target 넷 · 엔진 셋.

### (1) ★★★ 두 판 격자 — 자리 일곱 × 표준/레거시 × 판 셋

**언제 쓰나** — 라이브러리가 「`experimentalDecorators` 를 켜라」고 하는데 켜면 **무엇이 바뀌는지** 한 표로 보고 싶을 때. 4.9.5 처럼 **표준 판이 아예 없는** 판을 쓰는 코드베이스를 옮길 때.

탐침 — 칸마다 파일 한 장 = 아래 `show47.ts` + 클래스 한 줄 + `new A();`. `show` 는 **어느 시그니처로 불려도 되게** 인자를 그대로 적는다. 방출물은 아래 `run47.cjs` 로 돈다(예외는 이름·메시지만 — 스택에는 경로가 박힌다).

```ts
// show47.ts
// 격자의 칸마다 앞에 붙는 데코레이터 -- 받은 인자를 그대로 적는다(두 판 어느 쪽 시그니처로도 불릴 수 있게 느슨하게)
function show(label: string) {
    return function (...args: any[]): any {
        const [a, b, c] = args;
        const second = typeof b === "object" && b !== null ? "kind=" + b.kind + " name=" + String(b.name) : "key=" + String(b);
        console.log(label, "args=" + args.length, "first=" + typeof a, second, "third=" + typeof c);
    };
}
```

```js
// run47.cjs
// 방출된 .js 를 불러 돌린다 -- 예외는 이름과 메시지만 찍는다(스택에는 경로가 박힌다)
const path = require("path");
for (const f of process.argv.slice(2)) {
    try {
        require(path.resolve(f));
    } catch (e) {
        console.log("threw " + e.constructor.name + ": " + e.message);
    }
}
```

```bash
# ts46b-grid47.sh
#!/usr/bin/env bash
# 데코레이터 두 판 격자 -- 자리 일곱 × (표준 · experimentalDecorators) × 판 셋
# 칸마다 파일 한 장 = show47.ts + 클래스 한 줄 + `new A();` · 칸마다 디렉토리를 따로 · -t es2022 로 방출해 node 로 돈다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"; V49="${TSC_49:?4.9.5 판을 TSC_49 로 준다}"
EXTRA=${EXTRA:-}   # 자기검사용
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\x1f'   # 구분자는 US(0x1f) -- 규칙 32
rows=(
  "class${T}@show(\"class\") class A {}"
  "method${T}class A { @show(\"method\") m() {} }"
  "static${T}class A { @show(\"static\") static s() {} }"
  "field${T}class A { @show(\"field\") x = 1; }"
  "getter${T}class A { @show(\"getter\") get g() { return 1; } }"
  "accessor${T}class A { @show(\"accessor\") accessor y = 2; }"
  "param${T}class A { m(@show(\"param\") p: number) {} }"
)
run() { case $1 in 7.0.2) tsc "${@:2}" ;; 5.9.3) node "$OLD" "${@:2}" ;; 4.9.5) node "$V49" "${@:2}" ;; esac; }
helper() { grep -o '__esDecorate\|__decorate\|__param' "$1" | sort -u | tr '\n' ' ' | sed 's/ $//'; }
split_mode=0; split_log=0; split_ver=0; nm=0; nv=0; kinds=""
for r in "${rows[@]}"; do
  n=$(awk -F'\x1f' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r id cls <<< "$r"
  echo "[$id] $cls"
  declare -A got=()
  for mode in std legacy; do
    for v in 7.0.2 5.9.3 4.9.5; do
      d="$D/$id-$mode-$v"; mkdir -p "$d" || exit 3
      { cat show47.ts; echo "$cls"; echo "new A();"; } > "$d/c.ts" || exit 3
      if [ $mode = legacy ]; then fl=(--experimentalDecorators); else fl=(); fi
      raw=$(cd "$d" && run $v --pretty false -t es2022 "${fl[@]}" $EXTRA --outDir o c.ts 2>&1); rc=$?
      if grep -qE '^error TS' <<< "$raw"; then echo "★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: $(grep -oE '^error TS[0-9]+' <<< "$raw" | sed 's/^error //' | sort -u | tr '\n' ' ')"; exit 4; fi
      codes=$(grep -o 'error TS[0-9]*' <<< "$raw" | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
      if [ -f "$d/o/c.js" ]; then h=$(helper "$d/o/c.js"); log=$(cd "$d" && node "$OLDPWD/run47.cjs" o/c.js 2>&1 | tr '\n' ';' | sed 's/;$//'); else h="(방출 없음)"; log="-"; fi
      got[$mode,$v]="${codes:-OK} | ${h:-(도우미 없음)} | ${log:-(로그 없음)}"; got[log,$mode,$v]="${log:-(로그 없음)}"
      kinds="$kinds${T}${h:-none}"
      printf '    %-6s %-6s tsc exit=%s  %s\n' "$mode" "$v" "$rc" "${got[$mode,$v]}"
    done
  done
  for v in 7.0.2 5.9.3 4.9.5; do nm=$((nm+1)); [ "${got[std,$v]}" != "${got[legacy,$v]}" ] && split_mode=$((split_mode+1)); [ "${got[log,std,$v]}" != "${got[log,legacy,$v]}" ] && split_log=$((split_log+1)); done
  for mode in std legacy; do nv=$((nv+1)); if [ "${got[$mode,7.0.2]}" != "${got[$mode,5.9.3]}" ] || [ "${got[$mode,7.0.2]}" != "${got[$mode,4.9.5]}" ]; then split_ver=$((split_ver+1)); fi; done
  unset got
done
k=$(tr "$T" '\n' <<< "$kinds" | sed '/^$/d' | sort -u | tr '\n' ' ' | sed 's/ $//')
case "$k" in *__esDecorate*__decorate*|*__decorate*__esDecorate*) ;; *) echo "★ 방출 도우미가 한 종류뿐이다($k) -- 모드 플래그가 안 먹은 격자, 멈춘다"; exit 5 ;; esac
echo
echo "표준과 레거시가 갈린 칸 $split_mode / $nm · 그중 node 로그까지 갈린 칸 $split_log / $nm · 한 판(모드)에서 세 판이 갈린 줄 $split_ver / $nv · 칸에 나온 방출 도우미 <$k>"
```

```text
===== bash ts46b-grid47.sh (sh exit=0) =====
[class] @show("class") class A {}
    std    7.0.2  tsc exit=0  OK | __esDecorate | class args=2 first=function kind=class name=A third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | class args=2 first=function kind=class name=A third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 7.0.2  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 5.9.3  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 4.9.5  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
[method] class A { @show("method") m() {} }
    std    7.0.2  tsc exit=0  OK | __esDecorate | method args=2 first=function kind=method name=m third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | method args=2 first=function kind=method name=m third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | method args=3 first=object key=m third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
[static] class A { @show("static") static s() {} }
    std    7.0.2  tsc exit=0  OK | __esDecorate | static args=2 first=function kind=method name=s third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | static args=2 first=function kind=method name=s third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | static args=3 first=function key=s third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
[field] class A { @show("field") x = 1; }
    std    7.0.2  tsc exit=0  OK | __esDecorate | field args=2 first=undefined kind=field name=x third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | field args=2 first=undefined kind=field name=x third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | field args=3 first=object key=x third=undefined
    legacy 7.0.2  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
    legacy 5.9.3  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
    legacy 4.9.5  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
[getter] class A { @show("getter") get g() { return 1; } }
    std    7.0.2  tsc exit=0  OK | __esDecorate | getter args=2 first=function kind=getter name=g third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | getter args=2 first=function kind=getter name=g third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | getter args=3 first=object key=g third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
[accessor] class A { @show("accessor") accessor y = 2; }
    std    7.0.2  tsc exit=0  OK | __esDecorate | accessor args=2 first=object kind=accessor name=y third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | accessor args=2 first=object kind=accessor name=y third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | accessor args=3 first=object key=y third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
[param] class A { m(@show("param") p: number) {} }
    std    7.0.2  tsc exit=2  TS1206 | (도우미 없음) | (로그 없음)
    std    5.9.3  tsc exit=2  TS1206 | (도우미 없음) | (로그 없음)
    std    4.9.5  tsc exit=2  TS1219 | __decorate __param | param args=3 first=object key=m third=number
    legacy 7.0.2  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number
    legacy 5.9.3  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number
    legacy 4.9.5  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number

표준과 레거시가 갈린 칸 21 / 21 · 그중 node 로그까지 갈린 칸 14 / 21 · 한 판(모드)에서 세 판이 갈린 줄 7 / 14 · 칸에 나온 방출 도우미 <__decorate __decorate __param __esDecorate none>
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **마지막 줄 — 표준과 레거시가 갈린 칸 `21 / 21`, 그중 `node` 로그까지 갈린 칸 `14 / 21`.** 로그가 안 갈린 일곱 칸이 **4.9.5** 다 — 4.9.5 에는 표준 판이 없어 플래그를 빼도 **레거시로 방출하고 `TS1219` 만 더한다.**
- ★★★ **인자 수가 판을 말한다** — 표준은 전부 `args=2`, 레거시는 클래스만 `args=1` 이고 나머지는 `args=3`.
- ★★ **표준의 둘째 인자는 `context`** — `kind` 가 `class`·`method`·`field`·`getter`·`accessor` 로 **자리를 스스로 말한다.** 레거시는 **이름 문자열**(`key=m`)이다.
- ★★ **필드** — 표준은 첫 인자가 `undefined`(값이 아직 없다), 레거시는 `prototype` 객체. `static` 메서드는 레거시에서 첫 인자가 **생성자**(`first=function`)다.
- ★★★ **매개변수(`param`)** — 표준 두 판은 `TS1206` · **도우미 없음 · 로그 없음.** 레거시는 `__param` 을 방출하고 `(prototype, "m", 0)` 을 준다(`third=number` 가 매개변수 **자리 번호**다).
- ★ **`accessor` 키워드는 레거시에서도 된다** — 4.9.5 까지 포함해 `args=3` 으로 받는다. 표준 판은 `kind=accessor`.
- ★★ **한 모드 안에서 세 판이 갈린 줄 `7 / 14`** — 전부 **표준 줄의 4.9.5** 다. 레거시 일곱 줄은 세 판이 같다.

**자기검사** — 설정 진단이 칸에 들면 멈추고, **방출 도우미가 한 종류뿐이면** 멈춘다. 후자는 「모드 플래그가 안 먹은 격자」(예: 위쪽 `tsconfig.json` 이 플래그를 덮어쓴 경우)를 잡는다 — `EXTRA=--experimentalDecorators` 로 **모든 칸을 레거시로** 만들어 확인했다:

```text
===== EXTRA=<--bogusOpt · --experimentalDecorators> bash ts46b-grid47.sh 의 마지막 두 줄 (sh exit=0) =====
---- EXTRA=--bogusOpt
[class] @show("class") class A {}
★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: TS5023 
(exit 4)
---- EXTRA=--experimentalDecorators
    legacy 4.9.5  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number
★ 방출 도우미가 한 종류뿐이다(__decorate __decorate __param) -- 모드 플래그가 안 먹은 격자, 멈춘다
(exit 5)
```

매개변수 데코레이터를 칸 밖에서 한 번 더 — 표준 판이 **무엇을 방출하나**:

```ts
// param47.ts
// 매개변수 자리의 데코레이터 하나
function p(...args: any[]): any {
    console.log("param decorator args", args.length, String(args[1]), args[2]);
}
class A {
    m(@p x: number) {}
}
new A();
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 param47.ts ; __param 줄 수 ; node run47.cjs (sh exit=0) =====
---- (표준)
param47.ts(6,7): error TS1206: Decorators are not valid here.
(tsc exit 2)
방출물의 __param 줄: 0
(node exit 0)
---- --experimentalDecorators
(tsc exit 0)
방출물의 __param 줄: 1
param decorator args 3 m 0
(node exit 0)
```

- ★★★ 표준 판 — 진단 `TS1206` 은 나지만 `tsc` 는 **방출한다**(`noEmitOnError` 기본값 거짓 — [02번 주제](../02-type-checking-vs-emit/)). 방출물에 `__param` 이 **0줄**이고 `node` 는 **아무것도 안 찍는다.** 데코레이터가 **사라졌다.**
- ★★ 레거시 — `__param` 1줄 · `(prototype, "m", 0)`.

### (2) ★★★ 시그니처 쌍 · 평가와 적용의 순서 · 필드 초기화

**시그니처 쌍** — 레거시 모양으로 쓴 데코레이터 둘을 두 판에:

```ts
// sig47.ts
// 레거시 모양 (target, key, descriptor) 으로 쓴 데코레이터 둘 -- 하나는 느슨하게, 하나는 타입을 다 적어서
function logKey(target: any, key?: any): void {
    console.log("logKey got key:", String(key));
}
function wrap(target: any, key: string, d: PropertyDescriptor): void {
    const orig = d.value;
    d.value = function (this: unknown, ...a: unknown[]) {
        console.log("wrapped call:", key);
        return orig.apply(this, a);
    };
}
class A {
    @logKey m() {}
}
class B {
    @wrap n() {
        return 1;
    }
}
console.log("n() returned", new B().n());
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 sig47.ts ; node run47.cjs e47/sig47.js ; 이어서 "$TSC_OLD" 방출물의 node 출력을 cmp (sh exit=0) =====
---- (표준)
sig47.ts(16,5): error TS1241: Unable to resolve signature of method decorator when called as an expression.
  The runtime will invoke the decorator with 2 arguments, but the decorator expects 3.
(tsc exit 2)
logKey got key: [object Object]
threw TypeError: Cannot read properties of undefined (reading 'value')
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
---- --experimentalDecorators
(tsc exit 0)
logKey got key: m
wrapped call: n
n() returned 1
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
```

- ★★★ **느슨한 쪽(`logKey`)은 표준 판에서 진단 0 인데 틀린 값을 낸다** — `key` 자리에 `context` 객체가 와서 `[object Object]`. **TS 는 `(target: any, key?: any)` 가 두 인자로 불려도 되는지만 본다** — 받을 수 있으니 통과다.
- ★★★ **엄격한 쪽(`wrap`)은 `TS1241`** — 메시지가 「런타임은 인자 **2개**로 부르는데 데코레이터는 **3개**를 기대한다」고 **판 차이를 그대로** 말한다. 그래도 방출은 되고, `node` 에서 `d.value` 를 읽다 `TypeError`.
- ★★ 레거시에서는 둘 다 의도대로 — `key: m` · 감싼 메서드가 불린다.
- ★ 5.9.3 방출물의 `node` 출력이 **두 판 다 한 글자도 같다.**

**평가와 적용의 순서** — 데코레이터 **식**(`tag("c1")`)이 평가되는 때와, 그 결과 함수가 **적용**되는 때:

```ts
// ord47.ts
// 데코레이터 식이 언제 평가되고 언제 적용되나 -- 클래스 둘 · 메서드 둘 · 필드 · static
function tag(n: string) {
    console.log("evaluate", n);
    return function (...args: any[]): any {
        console.log("apply", n);
    };
}
@tag("c1") @tag("c2")
class A {
    @tag("m1") @tag("m2") m() {}
    @tag("f1") x = 1;
    @tag("s1") static s() {}
}
console.log("-- new A()");
new A();
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 ord47.ts ; node run47.cjs e47/ord47.js ; 이어서 "$TSC_OLD" 방출물의 node 출력을 cmp (sh exit=0) =====
---- (표준)
(tsc exit 0)
evaluate c1
evaluate c2
evaluate m1
evaluate m2
evaluate f1
evaluate s1
apply s1
apply m2
apply m1
apply f1
apply c2
apply c1
-- new A()
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
---- --experimentalDecorators
(tsc exit 0)
evaluate m1
evaluate m2
apply m2
apply m1
evaluate f1
apply f1
evaluate s1
apply s1
evaluate c1
evaluate c2
apply c2
apply c1
-- new A()
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
```

```text
  표준                                     레거시
  ────────────────────────────             ────────────────────────────
  평가  c1 c2 m1 m2 f1 s1   (전부 먼저,     평가·적용이 멤버마다 번갈아
        클래스 것부터 소스 순서)              m1 m2 → m2 m1 · f1 → f1 · s1 → s1
  적용  s1 · m2 m1 · f1 · c2 c1              클래스가 맨 끝  c1 c2 → c2 c1
        static 먼저 → 인스턴스 → 클래스
```

- ★★★ **한 자리 안에서는 두 판이 같다** — `@m1 @m2` 는 **평가 위→아래, 적용 아래→위**(`m2` 가 먼저 감싸고 `m1` 이 바깥).
- ★★★ **자리 사이의 순서는 다르다** — 표준은 **모든 식을 먼저 평가**(클래스 데코레이터 식까지)하고 **`static` 멤버 → 인스턴스 멤버 → 클래스** 순으로 적용한다. 레거시는 **멤버마다 평가·적용을 끝내고** 소스 순서(인스턴스 → `static`)로 가다가 클래스를 맨 끝에 한다.
- ★ 둘 다 `-- new A()` **앞에서** 끝났다 — 데코레이터는 **인스턴스를 만들 때가 아니라 클래스를 정의할 때** 돈다.

**표준 필드 데코레이터의 초기화** — 32편의 세 설정에서:

```ts
// init47.ts
// 표준 필드 데코레이터 -- 초기값을 바꾸는 함수를 돌려주고 addInitializer 를 건다
function times10(_value: undefined, context: ClassFieldDecoratorContext<P, number>) {
    context.addInitializer(function () {
        console.log("addInitializer ran for", String(context.name));
    });
    return function (this: P, initial: number) {
        console.log("field initializer got", initial);
        return initial * 10;
    };
}
class P {
    @times10 n = 4;
    constructor() {
        console.log("constructor body sees", this.n);
    }
}
console.log("-- first");
new P();
console.log("-- second");
console.log("n =", new P().n);
```

```text
===== tsc --pretty false <-t es2022 · -t es2022 --useDefineForClassFields false · -t es2021> --outDir e47 init47.ts ; node run47.cjs (sh exit=0) =====
---- -t es2022
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
---- -t es2022 --useDefineForClassFields false
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
---- -t es2021
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
```

- ★★ 필드 데코레이터가 돌려준 함수는 **인스턴스마다** 초기값을 받아 바꾼다(`4` → `40`) · `addInitializer` 도 **인스턴스마다** 돈다 · 생성자 몸통은 **바뀐 값**을 본다.
- ★★ 세 설정(`es2022` · `useDefineForClassFields false` · `es2021`)의 출력이 **같다.** 필드가 정의냐 대입이냐([32번 주제](../32-class-type-aspects/) 5절)는 이 탐침에 **안 드러난다** — 부모 접근자와 겹치는 자리는 **재지 않았다.**

### (3) ★★ 메타데이터 — `emitDecoratorMetadata` 대 `context.metadata`

**언제 쓰나** — DI 컨테이너·검증 라이브러리가 「매개변수 타입을 런타임에 알고 싶다」고 할 때.

레거시 + `emitDecoratorMetadata`:

```ts
// meta47a.ts
// 레거시 + emitDecoratorMetadata -- 방출물이 무엇을 부르나, 그리고 읽으려 하면
function mark(...args: any[]): any {}
class Svc {
    @mark greet(name: string, n: number): boolean {
        return true;
    }
}
console.log("typeof Reflect.metadata:", typeof (Reflect as any).metadata);
console.log((Reflect as any).getMetadata("design:paramtypes", Svc.prototype, "greet"));
```

```text
===== tsc --pretty false -t es2022 --experimentalDecorators --emitDecoratorMetadata --outDir e47 meta47a.ts ; 방출물의 metadata 줄 ; node run47.cjs (sh exit=0) =====
(tsc exit 0)
===== 방출물에서 metadata 가 든 줄 =====
8:var __metadata = (this && this.__metadata) || function (k, v) {
9:    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
20:    __metadata("design:type", Function),
21:    __metadata("design:paramtypes", [String, Number]),
22:    __metadata("design:returntype", Boolean)
24:console.log("typeof Reflect.metadata:", typeof Reflect.metadata);
===== node =====
typeof Reflect.metadata: undefined
threw TypeError: Reflect.getMetadata is not a function
(node exit 0)
```

- ★★★ 방출물이 **타입을 값으로 옮겨 적는다** — `design:paramtypes` 에 `[String, Number]` · `design:returntype` 에 `Boolean`. **TS 가 타입을 런타임에 남기는 드문 자리**다.
- ★★★ **그 호출은 가드돼 있다** — `__metadata` 는 `Reflect.metadata` 가 함수일 때만 부른다. 그래서 **`reflect-metadata` 없이도 클래스 정의는 조용히 지나간다.** 터지는 것은 **읽으려 할 때**다 — `Reflect.getMetadata is not a function`.

표준의 `context.metadata` — 폴리필 없이 / 첫 줄에 폴리필:

```ts
// meta47b.ts
// 표준 데코레이터의 context.metadata -- 폴리필 없이
function mark(_value: unknown, context: ClassMethodDecoratorContext) {
    console.log("typeof context.metadata:", typeof context.metadata);
    (context.metadata as any)[context.name] = "marked";
}
class Svc {
    @mark greet() {}
}
console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
console.log((Svc as any)[Symbol.metadata]);
```

```ts
// meta47c.ts
// 표준 데코레이터의 context.metadata -- 첫 줄에 Symbol.metadata 폴리필
(Symbol as any).metadata ??= Symbol("Symbol.metadata");
function mark(_value: unknown, context: ClassMethodDecoratorContext) {
    console.log("typeof context.metadata:", typeof context.metadata);
    (context.metadata as any)[context.name] = "marked";
}
class Svc {
    @mark greet() {}
}
console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
console.log((Svc as any)[Symbol.metadata]);
```

```text
===== tsc --pretty false -t es2022 --lib es2022,esnext.decorators,dom --outDir e47 <meta47b.ts · meta47c.ts 를 하나씩> ; node 18 · node 20 으로 node run47.cjs (sh exit=0) =====
(tsc meta47b exit 0)
(tsc meta47c exit 0)
===== meta47b 방출물에서 Symbol.metadata 가 든 줄 =====
46:            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
49:            if (_metadata) Object.defineProperty(this, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
57:console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
58:console.log(Svc[Symbol.metadata]);
---- node v18.19.1 meta47b
typeof context.metadata: undefined
threw TypeError: Cannot set properties of undefined (setting 'greet')
(node exit 0)
---- node v18.19.1 meta47c
typeof context.metadata: object
typeof Symbol.metadata: symbol
[Object: null prototype] { greet: 'marked' }
(node exit 0)
---- node v20.19.6 meta47b
typeof context.metadata: undefined
threw TypeError: Cannot set properties of undefined (setting 'greet')
(node exit 0)
---- node v20.19.6 meta47c
typeof context.metadata: object
typeof Symbol.metadata: symbol
[Object: null prototype] { greet: 'marked' }
(node exit 0)
```

- ★★★ **node 18 · 20 에 `Symbol.metadata` 가 없다** — 방출물이 `Symbol.metadata ? Object.create(null) : void 0` 으로 만들기 때문에 **`context.metadata` 가 `undefined`** 가 되고 거기에 쓰면 `TypeError`.
- ★★ 첫 줄에 `Symbol.metadata` 를 심으면 **같은 방출 코드가** 객체를 만들고 클래스의 `[Symbol.metadata]` 에 붙인다.
- ★ 타입 쪽에도 조건이 있다 — `Symbol.metadata` 를 쓰려면 `lib` 에 `esnext.decorators`(없으면 `TS2550`, 탐색 중 확인). 이 블록은 `--lib es2022,esnext.decorators,dom` 이다.
- ★★ **담기는 것이 다르다** — 레거시는 **컴파일러가 타입을** 적어 주고, 표준은 **데코레이터가 스스로 적은 것만** 담긴다. 표준 판에는 `design:paramtypes` 에 해당하는 것이 **없다**(매개변수 데코레이터도 없다).

### (4) ★★★ 세 층 — TS 구현 / TC39 제안 / 엔진

**`target` 에 따라 TS 가 풀어 쓰나:**

```ts
// nat47.ts
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value: unknown, context: ClassDecoratorContext) {
    console.log("decorated", String(context.name));
}
@d
class A {}
```

```text
===== tsc · "$TSC_OLD" --pretty false <-t es2022 · -t esnext> --outDir e47 nat47.ts ; esnext 방출물 ; node --check (sh exit=0) =====
---- 7.0.2 -t es2022 (tsc exit 0) 방출물 56줄 · __esDecorate 2곳
node --check exit 0: (진단 없음)
---- 7.0.2 -t esnext (tsc exit 0) 방출물 8줄 · __esDecorate 0곳
"use strict";
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value, context) {
    console.log("decorated", String(context.name));
}
@d
class A {
}
node --check exit 1: SyntaxError: Invalid or unexpected token
---- 5.9.3 -t es2022 (tsc exit 0) 방출물 55줄 · __esDecorate 2곳
node --check exit 0: (진단 없음)
---- 5.9.3 -t esnext (tsc exit 0) 방출물 7줄 · __esDecorate 0곳
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value, context) {
    console.log("decorated", String(context.name));
}
@d
class A {
}
node --check exit 1: SyntaxError: Invalid or unexpected token
```

- ★★★ **`-t esnext` 는 `@d` 를 그대로 둔다** — 7.0.2 · 5.9.3 모두. 그 방출물을 `node --check` 하면 `SyntaxError`. **TS 가 「esnext 엔진은 안다」고 가정한 것이 이 머신의 엔진보다 앞서 있다.**
- ★★ `-t es2022` 는 `__esDecorate` 도우미로 풀어 써 **55\~56줄**이 된다 — [43번 주제](../43-remaining-tsconfig-choices/)의 target 방출 격자에 한 칸을 더하는 셈이다.

**엔진이 `@` 를 파싱하나 — node 둘:**

```js
// nat47.js
function d(value, context) {
    return value;
}
@d
class A {}
```

```bash
# ts46b-native47.sh
#!/usr/bin/env bash
# 엔진이 @ 문법을 파싱하나 -- node 18 · node 20 의 --check (스택 줄은 빼고 첫 두 줄만 -- 전부 받은 뒤 거른다, 규칙 19-A)
set -u -o pipefail
N20="${NODE20:?node 20 의 경로를 NODE20 으로 준다}"
for n in node "$N20"; do
  out=$("$n" --check nat47.js 2>&1); rc=$?
  echo "---- node $("$n" --version) --check nat47.js (exit $rc)"
  sed -n '1,/Error/p' <<< "$out" | sed "s|^$PWD/||" | sed -n '1p;/Error/p'
done
```

```text
===== bash ts46b-native47.sh (sh exit=0) =====
---- node v18.19.1 --check nat47.js (exit 1)
nat47.js:4
SyntaxError: Invalid or unexpected token
---- node v20.19.6 --check nat47.js (exit 1)
nat47.js:4
SyntaxError: Invalid or unexpected token
```

**Chrome 151:**

```html
<!-- c47.html -->
<!doctype html>
<meta charset="utf-8">
<pre id="o"></pre>
<script>
  // 엔진이 @ 문법을 파싱하나 -- 문자열을 간접 eval 로 던져 예외 이름·메시지를 적는다
  const cases = [
    ["class decorator", "function d(v, c) { return v; }\n@d\nclass A {}"],
    ["method decorator", "function d(v, c) { return v; }\nclass B { @d m() {} }"],
    ["no decorator", "class C {}"],
    ["typeof Symbol.metadata", "typeof Symbol.metadata"],
  ];
  const out = [];
  for (const [label, src] of cases) {
    try {
      out.push(label + " — ok " + String((0, eval)(src)));
    } catch (e) {
      out.push(label + " — " + e.name + ": " + e.message);
    }
  }
  document.getElementById("o").textContent = out.join("\n");
</script>
```

```text
===== google-chrome --headless=new --disable-gpu --no-sandbox --dump-dom file://…/c47.html 의 <pre> 안 (sh exit=0) =====
class decorator — SyntaxError: Invalid or unexpected token
method decorator — SyntaxError: Invalid or unexpected token
no decorator — ok undefined
typeof Symbol.metadata — ok undefined
```

- ★★★ **세 엔진 모두 `SyntaxError: Invalid or unexpected token`** — `@` 를 **토큰으로도** 모른다. 데코레이터 없는 클래스는 통과한다.
- ★★ **`Symbol.metadata` 도 셋 다 없다** — 3절의 폴리필이 필요한 까닭.
- ★ 이 관찰은 「**stage 3 이라 어느 ES 판에도 없다**」와 **맞아떨어지지만 그것을 증명하지는 않는다** — 제안 단계는 TC39 문서의 사실이고 이 머신이 말할 수 있는 것은 **엔진 셋이 모른다**까지다.

```text
  세 층 — 누가 무엇을 말하나

  TS 구현       tsc 5.0+ 가 표준 판을 구현 · experimentalDecorators 가 옛 판      <- 1·2·3절 (방출물로 확인)
  TC39 제안     proposal-decorators — README: 2026-09 stage 3                    <- 출처 확인 못 함
  엔진          node 18 · node 20 · Chrome 151 — @ 에서 SyntaxError              <- 4절 (직접 확인)
```

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것 (표준 = experimentalDecorators 없음 · TS 5.0+)
  function dec(value, context: ClassMethodDecoratorContext) { … }   표준 메서드 데코레이터 — 인자 둘      (1·2절)
  context.kind · context.name · context.addInitializer(fn)          자리 · 이름 · 초기화 훅               (1·2절)
  return (initial) => …                                              필드 데코레이터의 초기값 변환          (2절)
  context.metadata  +  lib esnext.decorators                         표준 메타데이터 — Symbol.metadata 필요  (3절)
  --experimentalDecorators                                           레거시 — (target, key, descriptor)     (1절)
  m(@dec p: number)                                                  매개변수 데코레이터 — 레거시만         (1절)
  --emitDecoratorMetadata                                            레거시 전용 — design:* 를 방출         (3절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 판 |
|---|---|---|
| 표준 판에서 `m(@p x: number)` | `TS1206` — **방출에서 빠진다** | 7.0.2 · 5.9.3 |
| 표준 판에서 3인자 데코레이터 `(target, key: string, d: PropertyDescriptor)` | `TS1241` | 7.0.2 · 5.9.3 |
| 4.9.5 에서 플래그 없이 데코레이터 | `TS1219` — 레거시로 방출 | 4.9.5 |
| `static @dec s()` (키워드 뒤에 `@`) | `TS1436` | 세 판(탐색 중 확인) |
| `lib` 에 `esnext.decorators` 없이 `Symbol.metadata` | `TS2550` | 7.0.2(탐색 중 확인) |

**규칙 불릿**

- ★★★ **`experimentalDecorators` 가 판을 고른다** — 켜면 레거시, 끄면 표준(5.0+). **4.9.5 에는 표준이 없다**(1절).
- ★★★ **표준은 `(value, context)` 두 인자, 레거시는 `(target, key, descriptor)`** — 같은 함수를 양쪽에 쓰면 느슨한 타입은 **조용히 틀리고**, 엄격한 타입은 `TS1241`(2절).
- ★★★ **매개변수 데코레이터 · `emitDecoratorMetadata` 는 레거시 전용**(1·3절).
- ★★ **평가는 위→아래, 적용은 아래→위** — 두 판 공통. 자리 사이의 순서는 판마다 다르다(2절).
- ★★ **엔진은 `@` 를 모른다** — `target` 이 `esnext` 면 TS 도 안 풀어 준다(4절).

## 어디서 틀리나

- ★★★ 「**데코레이터는 JS 표준이다**」 — TS 5.0 이 **제안판을 구현**했을 뿐이다. node 18 · 20 · Chrome 151 이 전부 `SyntaxError`(4절).
- ★★★ 「**`experimentalDecorators` 는 이제 필요 없다 — 표준이 같은 일을 한다**」 — 인자가 다르고(1절), 매개변수 데코레이터와 `emitDecoratorMetadata` 가 **표준 판에 없다**(1·3절). Angular·NestJS 류가 레거시에 묶이는 까닭이다.
- ★★★ 「**레거시 데코레이터를 표준 판으로 옮겨도 컴파일되면 된다**」 — 느슨한 타입이면 **진단 0 인데 `key` 가 `[object Object]`**(2절).
- ★★ 「**표준 판에서 매개변수 데코레이터는 에러라서 안 돈다 — 알 수 있다**」 — 에러는 나지만 **방출은 된다**. `noEmitOnError` 가 없는 빌드는 데코레이터가 **사라진 코드를 내보낸다**(1절).
- ★★ 「**`emitDecoratorMetadata` 는 `reflect-metadata` 가 없으면 터진다**」 — 방출된 `__metadata` 는 **가드돼 있어 정의 때는 조용하다.** 터지는 것은 `Reflect.getMetadata` 를 **부르는** 쪽이다(3절).
- ★★ 「**`context.metadata` 는 늘 객체다**」 — `Symbol.metadata` 가 없는 런타임(node 18 · 20)에서는 `undefined`(3절).
- ★ 「**`@a @b` 는 `a` 가 먼저 적용된다**」 — 평가는 `a` 먼저, **적용은 `b` 먼저**(2절).
- ★ 「**`target: esnext` 면 최신 엔진에서 그대로 돈다**」 — `@` 가 남아 이 머신의 엔진 셋에서 `SyntaxError`(4절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **JS(엔진)** | `@` 문법 없음 · `Symbol.metadata` 없음 | 4절 — node 18 · 20 · Chrome 151 |
| **TC39 제안** | proposal-decorators 의 단계 | **출처 확인 못 함** — README 서술만 |
| **★★★ TS 구현 — 표준 판(5.0+)** | `(value, context)` · `__esDecorate` · 매개변수 불가 · `context.metadata` | 1·2·3절 |
| **★★★ TS 구현 — 레거시** | `(target, key, descriptor)` · `__decorate`·`__param` · `design:*` | 1·3절 |
| **★ 판 차이** | 4.9.5 는 표준 판이 없다 · 7.0.2 방출물에 `"use strict";` | 1·4절 |
| **★ 두 판 공통** | 한 자리 안에서 평가 위→아래 · 적용 아래→위 · 클래스 정의 때 돈다 | 2절 |
| **안 잰 것** | 부모 접근자와 겹치는 필드 데코레이터 · `-t es2015` 이하 방출 · 실험 플래그를 켠 엔진 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **새 코드는 표준 판** — 인자 둘 · `context.kind` 로 자리를 스스로 안다 | 새 코드에 `experimentalDecorators` 를 **습관으로** 켜기 |
| ★★★ **레거시가 필요한 때** — 매개변수 데코레이터 · `design:paramtypes` 에 기대는 DI(Angular·NestJS 류) | 두 판 모두에서 도는 「범용」 데코레이터를 `any` 로 쓰기 — 한쪽에서 조용히 틀린다(2절) |
| ★★ **메타데이터가 필요하면** — 레거시는 `reflect-metadata` 를 **읽는 쪽**이 들여오고, 표준은 **`Symbol.metadata` 폴리필** | 폴리필 없이 `context.metadata` 에 쓰기 — node 18 · 20 에서 `TypeError` |
| ★★ **`noEmitOnError`** 를 켜 둔다 — 표준 판의 매개변수 데코레이터가 **조용히 빠진 방출물**을 막는다 | 진단이 있어도 방출되는 빌드를 그대로 배포 |
| ★ 브라우저·node 대상은 **`target` 을 `es2022` 이하로** | `target: esnext` 로 `@` 를 그대로 내보내기(4절) |

## 핵심 문장

1. **TS 데코레이터는 두 벌이다** — `experimentalDecorators` 를 켜면 레거시 `(target, key, descriptor)`, 끄면 5.0 부터의 표준 `(value, context)`. 격자에서 두 판이 갈린 칸 `21 / 21`, `node` 로그까지 `14 / 21`(4.9.5 에는 표준이 없다).
2. **매개변수 데코레이터는 표준에 없다** — 표준 판은 `TS1206` 을 내고도 방출하며, 그 데코레이터를 **조용히 뺀다.**
3. **같은 데코레이터 함수를 두 판에 쓰면 느슨한 타입은 진단 0 으로 틀린 값을, 엄격한 타입은 `TS1241` 을 낸다.**
4. **메타데이터는 두 길이 다르다** — 레거시는 컴파일러가 `design:*` 로 타입을 적고, 표준은 데코레이터가 `context.metadata` 에 적는다. 후자는 `Symbol.metadata` 가 없는 node 18 · 20 에서 `undefined` 다.
5. **엔진은 아직 `@` 를 모른다** — node 18 · 20 · Chrome 151 이 `SyntaxError`. TS 표준 데코레이터는 **JS 표준이 아니라 TS 의 제안판 구현**이다.

## 관련 자료

- [**32번 주제** — 클래스의 타입 측면](../32-class-type-aspects/) 5절 — ★★★ **README 의 선행.** `useDefineForClassFields` 판 격자의 정본. 여기서는 표준 필드 데코레이터가 그 세 설정에서 같은 값을 내는 것만 봤다.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 1절 「진단이 있어도 방출한다」.
- [**43번 주제**](../43-remaining-tsconfig-choices/) — `target` 방출 격자. 4절이 `esnext` 한 칸을 더했다.
- Python 갈래 [**24번** — 데코레이터](../../../python/syntax/24-decorators/) — ★ 대비: Python 의 `@` 는 **언어 문법**이고 정의 시점에 **평범한 함수 호출**로 평가된다. TS 의 표준 판도 클래스 정의 때 돈다는 점은 같지만, **엔진이 문법을 아느냐**가 다르다.
- Java 갈래 [**16번** — 애너테이션](../../../java/syntax/16-annotations/) · Kotlin 갈래 [**35번** — 애너테이션과 사용 지점 대상](../../../kotlin/syntax/35-annotations-and-use-site-targets/) — ★ 대비: 애너테이션은 **메타데이터일 뿐 코드를 바꾸지 않고** 읽는 쪽(리플렉션·처리기)이 뜻을 준다. TS 데코레이터는 **함수라서 값을 바꿔 치운다**(2절 `wrap`·`times10`). 레거시의 `emitDecoratorMetadata` 만 애너테이션 쪽에 가깝다.

## 용어 풀이

> **표준 데코레이터(이 문서의 뜻)** — `experimentalDecorators` 없이 TS 5.0+ 가 구현한 판. TC39 제안을 따른 것이지 **JS 표준이 아니다.**\
> 예: 1절 `args=2 … kind=method`.

> **레거시 데코레이터** — `experimentalDecorators` 를 켠 판. `(target, key, descriptor)`.\
> 예: 1절 `args=3 … key=m`.

> **`context` 객체** — 표준 판이 둘째 인자로 주는 것. `kind` · `name` · `static` · `private` · `access` · `addInitializer` · `metadata`.\
> 예: 2절 `init47.ts`.

> **`addInitializer`** — 데코레이터가 초기화 때 돌 함수를 거는 자리. 필드·메서드는 **인스턴스마다** 돈다.\
> 예: 2절 `addInitializer ran for n` 두 번.

> **`__esDecorate` · `__decorate` · `__param` · `__metadata`** — TS 가 방출에 넣는 도우미. 앞의 것이 표준, 뒤 셋이 레거시.\
> 예: 1절 격자의 가운데 칸.

> **`emitDecoratorMetadata`** — 레거시 전용. 데코레이터가 붙은 선언의 **타입을 `design:type`·`design:paramtypes`·`design:returntype` 로 방출**한다.\
> 예: 3절 `[String, Number]`.

> **`Symbol.metadata`** — 표준 판 메타데이터가 클래스에 붙는 심볼. node 18 · 20 · Chrome 151 에 **없다.**\
> 예: 3·4절.

> **`TS1206` · `TS1241` · `TS1219`** — 「여기에 데코레이터를 못 쓴다」 · 「데코레이터 시그니처를 못 맞춘다(인자 수)」 · 「실험 기능(4.9.5)」.\
> 예: 1·2절.

## 더 들어가면

- **`access` 객체와 `private` 멤버 데코레이터** — `context.access.get/set` 으로 `#x` 를 읽는 길. **재지 않았다.**
- **`-t es2015` 이하의 표준 데코레이터 방출** — `static` 블록 없이 어떻게 풀어 쓰나. **재지 않았다.**
- **Chrome 의 실험 플래그** — 탐색 중에 `--js-flags` 로 두 이름을 붙여 봤지만 결과가 같았고, **그 이름이 V8 에 실제로 있는지 확인할 길이 없어** 싣지 않았다.
