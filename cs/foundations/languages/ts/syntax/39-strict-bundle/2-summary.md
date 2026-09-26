# ts/syntax/39 — `strict` 묶음 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `strict`](https://www.typescriptlang.org/tsconfig/#strict)(「Default: `true`」 · Enables — `alwaysStrict`·`strictNullChecks`·`strictBindCallApply`·`strictBuiltinIteratorReturn`·`strictFunctionTypes`·`strictPropertyInitialization`·`noImplicitAny`·`noImplicitThis`·`useUnknownInCatchVariables`) ·
> [`alwaysStrict`](https://www.typescriptlang.org/tsconfig/#alwaysStrict)(「Default: `true` if `strict` is enabled; `false` otherwise」).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다.
> ★★★ **레퍼런스와 7.0.2 가 어긋나는 칸이 하나 있다** — 레퍼런스는 `alwaysStrict` 를 `strict` 가 켜는 아홉 가운데 하나로 적지만, 7.0.2 에서는 **`strict: false` 로도 안 꺼지고 `alwaysStrict: false` 는 `TS5108`**(제거된 값)이다(4절).
> **실행 검증** — 본판은 아래다. ★ 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.

```text
===== tsc --version · node --version · "$NODE20" --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
v20.19.6
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 「탐침 격자」(하위 플래그마다 하나씩 걸리는 탐침 아홉 × 설정 넷 × 세 판 — 칸마다 디렉토리와 `tsconfig.json` 을 따로)이다.**
> ★★★ **제5의 상태 — 「`strict` 가 무엇을 켜나」를 도구로 뽑으려 했더니 `--showConfig` 가 5.9.3 에서만 펼쳐 적었다**(1절). 7.0.2·4.9.5 에서는 같은 질문을 **`--help --all` 의 기본값 문구**로 물었고, 그 문구도 믿지 않고 **탐침 격자로** 확인했다 — 4.9.5 의 도움말은 **실제와 한 칸 어긋났다**.
> ★★ **39 는 02 에서 온다.** [**02번 주제**](../02-type-checking-vs-emit/)가 「7.0 의 `strict` 기본 `true`」를 머리말에 적었고 `--strict false` 로 판을 가르는 방식을 세웠다. 여기서는 **설정 없이 던지는 칸**을 새로 재서(3절) 그 문장을 다시 확인한다 — 02편은 고치지 않는다.
> ★★ 설정 실험은 **칸마다 디렉토리를 따로** 만들었다 — 7.0.2 는 **위쪽 디렉토리에** `tsconfig.json` 이 있으면 파일을 직접 줘도 `TS5112` 로 검사를 거부한다(35편 6절). 격자 스크립트는 **칸에 `TS5112` 가 들면 멈추고, 모든 칸이 같은 코드면 멈춘다.**
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자·단계표의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **판에 매인다** | ★★★ **「키 없음」의 뜻** — 7.0.2 는 `strict` 가 켜진 것과 같고 5.9.3·4.9.5 는 꺼진 것과 같다(2·3절) | 결론 자체다 |
| **판에 매인다** | ★★ `--showConfig` 가 **펼치나** · `--help` 의 기본값 문구(1절) | 결론 자체다 — 도구의 성질도 판에 매인다 |
| **판에 매인다** | ★ 종료 코드 — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3 은 `2` | 격자는 **진단 코드로** 갈랐다 |
| **★ 설계 권고** | 5절의 「켜는 순서」 | ★★ **탐침 파일 한 장**에서 센 진단 수에 기댄다 — 실제 코드베이스의 비율이 아니다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** · **2창(`null` 탐침)** | 이 주제는 「**켜졌나**」를 진단 코드 하나로 묻는다 — 타입의 모양을 묻지 않는다 | — |
| **안 잰 것** | `strict` 가 검사 **시간**에 주는 영향 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**`strict` 는 「안전 점검 묶음 스위치」다. 스위치 하나가 점검 여러 개를 한꺼번에 켜고, 그 밑의 개별 스위치로 하나씩 끌 수 있다. 7.0 은 공장에서 이 묶음 스위치를 **켠 채로** 출고한다 — 그리고 한 점검(`alwaysStrict`)은 아예 **스위치를 떼어 버려** 끌 수 없게 했다.**

| 비유 | 실체 |
|---|---|
| **묶음 스위치** | `"strict": true` |
| **개별 스위치** | 하위 플래그 — `noImplicitAny`·`strictNullChecks`·… |
| ★★★ 공장 출고 상태가 **켜짐**으로 바뀌었다 | 7.0.2 — 설정 없이 던져도 `TS2322`(3절) · 5.9.3 은 0줄 |
| 묶음을 켜고 **하나만 끈다** | `"strict": true, "strictNullChecks": false` — 그 탐침만 조용해진다(2절 넷째 열) |
| ★★★ 스위치를 **떼어 버린** 점검 | `alwaysStrict` — 7.0.2 에서 `strict: false` 로도 안 꺼지고 `false` 는 `TS5108`(4절) |
| 「설명서에는 점검 아홉이라고 적혀 있다」 | 레퍼런스의 Enables 목록 — 7.0.2 에서 **끌 수 있는 것은 여덟** |
| 스위치 두 개를 **같이 올려야** 불이 들어오는 점검 | `strictPropertyInitialization` 은 `strictNullChecks` 없이 `TS5052`(5절) |

- ★★★ 한 줄로 — 「**`strict` 는 하위 플래그 묶음의 기본값을 바꾸는 스위치이고, 7.0 은 그 기본값을 켬으로 뒤집었다. 켜진 묶음은 하위 하나씩 끌 수 있는데, `alwaysStrict` 만은 7.0.2 에서 끌 수 없다.**」

```text
  "strict" 한 줄이 하는 일 — 7.0.2 기준

  "strict" 키 없음        ─> 하위 여덟이 켜진 것과 같다        (5.9.3 · 4.9.5 는 전부 꺼진 것)
  "strict": true          ─> 하위 여덟 켬
  "strict": false         ─> 하위 여덟 끔                    ★ alwaysStrict 는 그대로 켜져 있다
  "strict": true + "X": false  ─> X 하나만 끔               ★ X 가 alwaysStrict 면 TS5108
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `strict` 는 무엇을 켜나 — 도구로 뽑을 수 있나** — `--showConfig`·`--help --all` × 세 판(1절) · 그 목록이 실제와 맞나(2절 탐침 격자).
2. **★★★ 7.0 에서 기본값 `true` 는 무엇을 바꾸나** — 「키 없음」 열 · 설정 없이 던진 칸(2·3절) · `alwaysStrict` 가 묶음에서 빠진 것(4절).
3. **★★ 기존 코드에 어떤 순서로 켜나** — 하위 플래그를 하나씩 켠 진단 수(5절 — 설계 권고 층).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **탐침 격자** | 탐침 아홉 × (키 없음 · `true` · `false` · `true` + 하위 하나 `false`) × 세 판 | 칸마다 진단 코드 | **본체**(2절) |
| ★★ **도구 창 — `--showConfig`** | `strict` 를 **펼쳐 적나** | 설정 덤프 | 1절 — ★ 5.9.3 에서만 열렸다 |
| ★★ **도구 창 — `--help --all`** | 하위 플래그의 **기본값 문구** | 도움말 | 1절 — **제5의 상태**(`--showConfig` 가 안 열린 판에서 같은 질문을 이 창으로) |
| ★★ **3창 — 방출물** | `"use strict";` 가 붙나 | 방출물 | 4절 |
| ★★ **단계표** | 스크립트 한 장에 하위 플래그를 **하나씩** 켠 새 진단 수 | 수 | 5절 |
| ★ **부적용 — 5창(`.d.ts`)** · **2창(`null` 탐침)** | 켜졌나를 **진단 코드**로만 묻는다 | — | — |

비용 — 탐침 격자 108칸(아홉 × 넷 × 세 판) + 도구 창 둘(세 판) + 설정 없는 칸 · 방출 둘 · 단계표 열세 줄(두 판).

```text
  이 주제의 축 — 「누가 켜나」

  tsc 의 기본값           "strict" 키가 없을 때    7.0.2: 켬     5.9.3 · 4.9.5: 끔
  묶음 스위치             "strict": true/false     하위 여덟을 한꺼번에
  개별 스위치             "X": false               그것만 — 묶음보다 우선
  ★ 떼어 낸 스위치         alwaysStrict             7.0.2: 늘 켬 · false 는 TS5108
```

### (1) ★★ 도구로 뽑기 — `--showConfig` 는 한 판에서만 펼친다

**언제 쓰나** — 「우리 설정에서 `strict` 가 정확히 무엇을 켜고 있나」를 기억 말고 도구로 확인할 때.

```bash
# ts38b-show39.sh
#!/usr/bin/env bash
# "strict": true 한 줄짜리 tsconfig.json 을 판 셋의 --showConfig 에 준다 -- 펼쳐 적은 키를 본다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo 'export const a = 1;' > "$D/a39.ts"
keys() { node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{console.log(Object.keys(JSON.parse(s).compilerOptions).join(" "))})'; }
for s in true false; do
  printf '{ "compilerOptions": { "strict": %s }, "files": ["a39.ts"] }\n' "$s" > "$D/tsconfig.json"
  echo "---- \"strict\": $s"
  for v in 7 5 4; do
    case $v in 7) vn=7.0.2; c=(tsc) ;; 5) vn=5.9.3; c=(node "$OLD") ;; 4) vn=4.9.5; c=(node "$V49") ;; esac
    out=$(cd "$D" && "${c[@]}" --showConfig -p tsconfig.json); rc=$?
    echo "$vn (exit $rc) -- $(keys <<< "$out")"
  done
done
```

```text
===== bash ts38b-show39.sh (sh exit=0) =====
---- "strict": true
7.0.2 (exit 0) -- strict
5.9.3 (exit 0) -- strict noImplicitAny noImplicitThis strictNullChecks strictFunctionTypes strictBindCallApply strictPropertyInitialization strictBuiltinIteratorReturn alwaysStrict useUnknownInCatchVariables
4.9.5 (exit 0) -- strict
---- "strict": false
7.0.2 (exit 0) -- strict
5.9.3 (exit 0) -- strict
4.9.5 (exit 0) -- strict
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **5.9.3 만** `"strict": true` 를 **하위 아홉으로 펼쳐** 적었다 — `noImplicitAny` · `noImplicitThis` · `strictNullChecks` · `strictFunctionTypes` · `strictBindCallApply` · `strictPropertyInitialization` · `strictBuiltinIteratorReturn` · `alwaysStrict` · `useUnknownInCatchVariables`.
- ★★★ **7.0.2 와 4.9.5 는 `strict` 한 키만** 돌려준다 — `--showConfig` 는 이 두 판에서 **「무엇이 켜졌나」를 말해 주지 않는다.**
- ★ `"strict": false` 는 세 판 모두 `strict` 한 키 — 펼쳐 적는 5.9.3 도 **끈 것은 안 적는다.**

같은 질문을 **도움말 창**으로 묻는다.

```bash
# ts38b-help39.sh
#!/usr/bin/env bash
# 판 셋의 tsc --help --all 에서 기본값 설명에 `strict` 가 들어간 플래그와, alwaysStrict 의 기본값 설명을 뽑는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
pick() { awk '/^--/{f=$1} /^default:/{ if ($0 ~ /strict/ || f=="--alwaysStrict" || f=="--useUnknownInCatchVariables") print f "\t" $0 }' | sort; }
tsc --help --all > "$D/h7" 2>&1; node "$OLD" --help --all > "$D/h5" 2>&1; node "$V49" --help --all > "$D/h4" 2>&1
for v in 7 5 4; do
  case $v in 7) vn=7.0.2 ;; 5) vn=5.9.3 ;; 4) vn=4.9.5 ;; esac
  pick < "$D/h$v" > "$D/p$v"
  echo "---- $vn ($(wc -l < "$D/p$v")줄)"
  cat "$D/p$v"
done
echo "---- 플래그 이름만 -- 4.9.5 → 5.9.3 → 7.0.2"
cut -f1 "$D/p4" > "$D/n4"; cut -f1 "$D/p5" > "$D/n5"; cut -f1 "$D/p7" > "$D/n7"
echo "4.9.5 에 없고 5.9.3 에 있는 것: $(comm -13 "$D/n4" "$D/n5" | tr '\n' ' ')"
echo "5.9.3 에 없고 7.0.2 에 있는 것: $(comm -13 "$D/n5" "$D/n7" | tr '\n' ' ')"
echo "5.9.3 에 있고 7.0.2 에 없는 것: $(comm -23 "$D/n5" "$D/n7" | tr '\n' ' ')"
exit 0
```

```text
===== bash ts38b-help39.sh (sh exit=0) =====
---- 7.0.2 (9줄)
--alwaysStrict	default: true
--noImplicitAny	default: `true`, unless `strict` is `false`
--noImplicitThis	default: `true`, unless `strict` is `false`
--strictBindCallApply	default: `true`, unless `strict` is `false`
--strictBuiltinIteratorReturn	default: `true`, unless `strict` is `false`
--strictFunctionTypes	default: `true`, unless `strict` is `false`
--strictNullChecks	default: `true`, unless `strict` is `false`
--strictPropertyInitialization	default: `true`, unless `strict` is `false`
--useUnknownInCatchVariables	default: `true`, unless `strict` is `false`
---- 5.9.3 (9줄)
--alwaysStrict	default: `false`, unless `strict` is set
--noImplicitAny	default: `false`, unless `strict` is set
--noImplicitThis	default: `false`, unless `strict` is set
--strictBindCallApply	default: `false`, unless `strict` is set
--strictBuiltinIteratorReturn	default: `false`, unless `strict` is set
--strictFunctionTypes	default: `false`, unless `strict` is set
--strictNullChecks	default: `false`, unless `strict` is set
--strictPropertyInitialization	default: `false`, unless `strict` is set
--useUnknownInCatchVariables	default: `false`, unless `strict` is set
---- 4.9.5 (8줄)
--alwaysStrict	default: `false`, unless `strict` is set
--noImplicitAny	default: `false`, unless `strict` is set
--noImplicitThis	default: `false`, unless `strict` is set
--strictBindCallApply	default: `false`, unless `strict` is set
--strictFunctionTypes	default: `false`, unless `strict` is set
--strictNullChecks	default: `false`, unless `strict` is set
--strictPropertyInitialization	default: `false`, unless `strict` is set
--useUnknownInCatchVariables	default: false
---- 플래그 이름만 -- 4.9.5 → 5.9.3 → 7.0.2
4.9.5 에 없고 5.9.3 에 있는 것: --strictBuiltinIteratorReturn 
5.9.3 에 없고 7.0.2 에 있는 것: 
5.9.3 에 있고 7.0.2 에 없는 것: 
```

- ★★★ **7.0.2** — 여덟이 「`true`, unless `strict` is `false`」, **`alwaysStrict` 만 「default: true」** — 조건이 없다(4절이 이것을 던져 확인한다).
- ★★ **5.9.3** — 아홉이 전부 「`false`, unless `strict` is set」. 5.9.3 의 `--showConfig` 와 **같은 아홉**이다.
- ★★ **4.9.5** — `strictBuiltinIteratorReturn` 이 **없다**(4.9.5 → 5.9.3 사이에 들어왔다 — 스크립트의 `comm` 줄). ★★★ 그리고 **`useUnknownInCatchVariables` 가 「default: false」** — `strict` 와 **무관한 것처럼** 적혀 있다. 2절 격자는 그 문구가 **틀렸음**을 보인다(4.9.5 의 `true` 열이 `TS18046`).
- ★ 5.9.3 → 7.0.2 는 **이름 목록은 같다**(`comm` 두 줄이 비었다) — 바뀐 것은 **기본값 문구**다.

```text
  「strict 가 무엇을 켜나」를 물은 세 창 — 판마다 열린 창이 다르다

              --showConfig          --help --all 기본값 문구             탐침 격자(2절)
  7.0.2       strict 한 키 (안 열림)  여덟 "unless false" + alwaysStrict 무조건   여덟 + alwaysStrict 는 false 로도 켜짐
  5.9.3       ★ 아홉을 펼친다         아홉 "unless set"                       아홉
  4.9.5       strict 한 키 (안 열림)  일곱 "unless set" + useUnknown… false  ★ 여덟 (useUnknown… 도 켜진다)
```

비용 — **도구의 성질도 판에 매인다.** 「`--showConfig` 로 확인했다」는 **5.9.3 에서만** 참이었다. 그래서 이 문서의 결론은 **탐침 격자**에 세운다.

### (2) ★★★ 탐침 격자 — 하위 플래그 아홉 × 설정 넷 × 세 판

**언제 쓰나** — 「이 설정에서 이 검사가 켜져 있나」를 **코드 한 줄**로 확인할 때.

탐침 — 하위 플래그마다 **그것 하나에만** 걸리는 파일 한 장.

```ts
// pr39a.ts
function f(x) { return x; }
export {};
```

```ts
// pr39b.ts
function g() { return this.x; }
export {};
```

```ts
// pr39c.ts
let s: string = null;
export {};
```

```ts
// pr39d.ts
let h: (x: string | number) => void = (x: string) => {};
export {};
```

```ts
// pr39e.ts
function k(a: number) {}
k.call(undefined, "x");
export {};
```

```ts
// pr39f.ts
class C { p: number; }
export {};
```

```ts
// pr39g.ts
const r = [1].values().next();
if (r.done) { const v: number = r.value; }
export {};
```

```ts
// pr39h.ts
try {} catch (e) { e.message; }
export {};
```

```ts
// pr39i.ts
var package = 1;
```

```bash
# ts38b-grid39.sh
#!/usr/bin/env bash
# 탐침 아홉 × strict 설정 넷 × 판 셋 -- 칸마다 디렉토리와 tsconfig.json 을 따로 만든다
# 설정 넷: 키 없음 · "strict": true · "strict": false · "strict": true + 그 탐침의 하위 플래그 하나만 false
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
rows=(
  "pr39a.ts${T}noImplicitAny"
  "pr39b.ts${T}noImplicitThis"
  "pr39c.ts${T}strictNullChecks"
  "pr39d.ts${T}strictFunctionTypes"
  "pr39e.ts${T}strictBindCallApply"
  "pr39f.ts${T}strictPropertyInitialization"
  "pr39g.ts${T}strictBuiltinIteratorReturn"
  "pr39h.ts${T}useUnknownInCatchVariables"
  "pr39i.ts${T}alwaysStrict"
)
cols=("키없음" "true" "false" "true+끔")
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
opt() {                               # opt <열> <하위 플래그>
  case $1 in
    키없음) echo '' ;;
    true) echo '"strict": true, ' ;;
    false) echo '"strict": false, ' ;;
    true+끔) echo "\"strict\": true, \"$2\": false, " ;;
  esac
}
printf '%-9s %-8s' "탐침" "판"; for c in "${cols[@]}"; do printf ' %-14s' "$c"; done; echo
all=""; i=0; split75=0; split54=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r probe sub <<< "$r"
  declare -A got=()
  for c in "${cols[@]}"; do
    i=$((i+1)); d="$D/c$i"; mkdir -p "$d"; cp "$probe" "$d/"
    printf '{ "compilerOptions": { %s"target": "es2022", "noEmit": true }, "files": ["%s"] }\n' "$(opt "$c" "$sub")" "$probe" > "$d/tsconfig.json"
    got[7,$c]=$(cd "$d" && tsc --pretty false -p tsconfig.json 2>&1 | codes)
    got[5,$c]=$(cd "$d" && node "$OLD" --pretty false -p tsconfig.json 2>&1 | codes)
    got[4,$c]=$(cd "$d" && node "$V49" --pretty false -p tsconfig.json 2>&1 | codes)
    for v in 7 5 4; do case ${got[$v,$c]} in *TS5112*) echo "★ TS5112 가 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac; done
    total=$((total+1))
    [ "${got[7,$c]}" != "${got[5,$c]}" ] && split75=$((split75+1))
    [ "${got[5,$c]}" != "${got[4,$c]}" ] && split54=$((split54+1))
    all="$all|${got[7,$c]:-OK}|${got[5,$c]:-OK}|${got[4,$c]:-OK}"
  done
  for v in 7 5 4; do
    case $v in 7) vn=7.0.2 ;; 5) vn=5.9.3 ;; 4) vn=4.9.5 ;; esac
    if [ $v = 7 ]; then printf '%-9s %-8s' "$probe" "$vn"; else printf '%-9s %-8s' "" "$vn"; fi
    for c in "${cols[@]}"; do printf ' %-14s' "${got[$v,$c]:-OK}"; done; echo
  done
  unset got
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "칸에 나온 코드 가짓수 $kinds_seen · 7.0.2 와 5.9.3 이 갈린 칸 $split75 / $total · 5.9.3 과 4.9.5 가 갈린 칸 $split54 / $total"
```

```text
===== bash ts38b-grid39.sh (sh exit=0) =====
탐침    판      키없음      true           false          true+끔      
pr39a.ts  7.0.2    TS7006         TS7006         OK             OK            
          5.9.3    OK             TS7006         OK             OK            
          4.9.5    OK             TS7006         OK             OK            
pr39b.ts  7.0.2    TS2683         TS2683         OK             OK            
          5.9.3    OK             TS2683         OK             OK            
          4.9.5    OK             TS2683         OK             OK            
pr39c.ts  7.0.2    TS2322         TS2322         OK             OK            
          5.9.3    OK             TS2322         OK             OK            
          4.9.5    OK             TS2322         OK             OK            
pr39d.ts  7.0.2    TS2322         TS2322         OK             OK            
          5.9.3    OK             TS2322         OK             OK            
          4.9.5    OK             TS2322         OK             OK            
pr39e.ts  7.0.2    TS2345         TS2345         OK             OK            
          5.9.3    OK             TS2345         OK             OK            
          4.9.5    OK             TS2345         OK             OK            
pr39f.ts  7.0.2    TS2564         TS2564         OK             OK            
          5.9.3    OK             TS2564         OK             OK            
          4.9.5    OK             TS2564         OK             OK            
pr39g.ts  7.0.2    TS2322         TS2322         OK             OK            
          5.9.3    OK             TS2322         OK             OK            
          4.9.5    OK             OK             OK             TS5023        
pr39h.ts  7.0.2    TS18046        TS18046        OK             OK            
          5.9.3    OK             TS18046        OK             OK            
          4.9.5    OK             TS18046        OK             OK            
pr39i.ts  7.0.2    TS1212         TS1212         TS1212         TS5108        
          5.9.3    OK             TS1212         OK             OK            
          4.9.5    OK             TS1212         OK             OK            

칸에 나온 코드 가짓수 10 · 7.0.2 와 5.9.3 이 갈린 칸 11 / 36 · 5.9.3 과 4.9.5 가 갈린 칸 2 / 36
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **「키없음」 열** — 7.0.2 는 **아홉 전부** 진단이 났고 5.9.3·4.9.5 는 **아홉 전부 OK**. 7.0.2 에서 키가 없으면 **`strict: true` 와 같다.**
- ★★ **`true` 열** — 세 판이 **거의 같다.** 다른 칸은 4.9.5 의 `pr39g`(OK) 하나 — 그 판에는 `strictBuiltinIteratorReturn` 이 **없다.**
- ★★ **`false` 열** — 여덟은 세 판 모두 OK. ★★★ **`pr39i`(예약어 `package`)만 7.0.2 에서 `TS1212`** — `strict: false` 로도 **엄격 모드 파싱이 안 꺼졌다**(4절).
- ★★★ **`true+끔` 열**(묶음을 켜고 그 탐침의 하위 하나만 `false`) — **그 탐침만 조용해졌다**(OK). 하위 스위치가 묶음보다 **우선**한다.
  ★ 예외 둘 — 7.0.2 의 `pr39i` 는 **`TS5108`**(`alwaysStrict: false` 가 제거된 값), 4.9.5 의 `pr39g` 는 **`TS5023`**(그런 옵션이 없다).
- ★★ 4.9.5 의 `pr39h`(`catch` 변수) `true` 열이 **`TS18046`** — 1절 도움말의 「default: false」와 달리 **`strict` 가 켠다.** 도움말 문구가 틀렸다.
- ★★★ 마지막 줄 — **7.0.2 와 5.9.3 이 갈린 칸 `11 / 36`**(「키없음」 아홉 + `pr39i` 의 `false`·`true+끔` 둘) · **5.9.3 과 4.9.5 가 갈린 칸 `2 / 36`**(`pr39g` 의 `true`·`true+끔`).

```text
  탐침 하나 = 하위 플래그 하나 (7.0.2 · "strict": true 에서 난 코드)

  pr39a  function f(x)                      noImplicitAny                TS7006
  pr39b  function g() { this.x }            noImplicitThis               TS2683
  pr39c  let s: string = null               strictNullChecks             TS2322
  pr39d  (x: string) 를 (x: string|number) 자리에   strictFunctionTypes    TS2322
  pr39e  k.call(undefined, "x")             strictBindCallApply          TS2345
  pr39f  class C { p: number; }             strictPropertyInitialization TS2564
  pr39g  done 인 next() 의 value            strictBuiltinIteratorReturn  TS2322
  pr39h  catch (e) { e.message }            useUnknownInCatchVariables   TS18046
  pr39i  var package = 1  (스크립트)          alwaysStrict                 TS1212
```

비용 — 탐침은 **켜졌다**는 것만 말한다. 그 플래그가 **무엇을 더 잡는지**의 전모는 각자의 주제다(40편 `strictNullChecks` · [목록의 **42번 주제**](../42-implicit-any-and-catch-variables/) `noImplicitAny`·`useUnknownInCatchVariables` · 17편 `strictFunctionTypes`).

### (3) ★★★ 설정 없이 던지면 — 7.0.2 의 기본값

**언제 쓰나** — `tsc 파일.ts` 로 빠르게 확인하는 습관이 있을 때. 판이 바뀌면 **같은 명령의 뜻**이 바뀐다.

```text
===== tsc --pretty false --noEmit pr39c.ts pr39i.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
pr39c.ts(1,5): error TS2322: Type 'null' is not assignable to type 'string'.
pr39i.ts(1,5): error TS1212: Identifier expected. 'package' is a reserved word in strict mode.
(exit 1)
---- 5.9.3
(exit 0)
```

- ★★★ **7.0.2** — `tsconfig.json` 도 플래그도 없이 **`TS2322`**(`null` → `string`)와 **`TS1212`**. 설정 없이도 `strictNullChecks` 와 엄격 모드가 **켜져 있다.** 02편 머리말의 「7.0 의 `strict` 기본 `true`」가 **설정 없는 칸에서도** 재현됐다.
- ★★ **5.9.3** — **`(exit 0)`**, 진단 0줄. 같은 명령이 **아무것도 안 잡는다.**
- ★ 이 블록은 **`tsconfig.json` 이 위쪽 어디에도 없는** 디렉토리에서 던졌다 — 있었다면 7.0.2 는 `TS5112` 로 검사를 거부했다(35편 6절).

비용 — 「`tsc a.ts` 로 확인했다」는 **판을 적지 않으면** 뜻이 없다. 같은 한 줄이 7.0.2 에서는 엄격 검사, 5.9.3 에서는 느슨한 검사다.

### (4) ★★★ `alwaysStrict` — 7.0.2 에서 묶음 밖으로 나갔다

**언제 쓰나** — `strict: false` 로 옛 코드를 받아들이려는데 예약어·`with` 류 **엄격 모드 파싱 에러**가 안 사라질 때.

```text
===== tsc --pretty false -t es2022 --strict false --outDir e39 pr39i.ts ; "$TSC_OLD" 로 같은 것 ; 이어서 tsc --pretty false --noEmit -t es2022 --alwaysStrict false pr39i.ts (sh exit=0) =====
---- 7.0.2 --strict false
pr39i.ts(1,5): error TS1212: Identifier expected. 'package' is a reserved word in strict mode.
(exit 2)
== 방출된 e39/pr39i.js ==
"use strict";
var package = 1;
---- 5.9.3 --strict false
(exit 0)
== 방출된 e39/pr39i.js ==
var package = 1;
---- 7.0.2 --alwaysStrict false
error TS5108: Option 'alwaysStrict=false' has been removed. Please remove it from your configuration.
(exit 1)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **7.0.2 `--strict false`** — 여전히 **`TS1212`**(「'package' is a reserved word in strict mode.」)이고 방출물 첫 줄에 **`"use strict";`** 가 붙었다.
- ★★ **5.9.3 `--strict false`** — 진단 0줄, 방출물에 `"use strict"` **없음**. 레퍼런스의 「Default: `true` if `strict` is enabled; `false` otherwise」는 **이 판의 동작**이다.
- ★★★ **7.0.2 `--alwaysStrict false`** — **`TS5108`**(「Option 'alwaysStrict=false' has been removed.」). **끌 수 있는 값 자체가 없어졌다** — 02편 7절의 `TS5108`(제거된 값) 집안이다.
- ★★ 그래서 7.0.2 에서 `strict` 가 끄고 켜는 하위 플래그는 **여덟**이다 — 레퍼런스의 Enables 목록(아홉)과 **한 칸 어긋난다.**

```text
  alwaysStrict — 판마다

              "strict": false 일 때       "alwaysStrict": false
  5.9.3       꺼진다 (use strict 없음)     받는다
  7.0.2       ★ 안 꺼진다 (use strict 있음) ★ TS5108 — 제거된 값
```

비용 — 7.0 에서 **비엄격 모드 JS 에만 성립하는 코드**(예약어 이름·`with`·`arguments` 조작)는 TS 파일로 둘 수 없다. `strict: false` 는 **타입 검사**만 느슨하게 한다.

### (5) ★★ 단계적으로 켜기 — 하나씩 켠 진단 수(설계 권고 층)

**언제 쓰나** — `strict` 없이 자란 코드베이스에 묶음을 켜야 할 때 — **한 번에 켜면 어디서부터 고칠지** 보이지 않는다.

```ts
// legacy39.ts
// strict 없이 자란 코드를 흉내 낸 한 장
function sum(xs) {
    let t = 0;
    for (const x of xs) t += x;
    return t;
}
function format(prefix, value) {
    return prefix + ": " + value;
}
function describe() {
    return this.name + " (" + this.age + ")";
}
let current: string = null;
let pending: number = undefined;
const handlers: { [k: string]: (e: string | number) => void } = {};
handlers.click = (e: string) => console.log(e.length);
function pad(n: number, width: number) {
    return String(n).padStart(width, "0");
}
pad.call(undefined, "7", 3);
pad.apply(undefined, [7]);
class Account {
    id: number;
    owner: string;
    balance = 0;
}
const it = new Set([1, 2]).values();
const step = it.next();
if (step.done) {
    const last: number = step.value;
}
try {
    JSON.parse("{");
} catch (err) {
    console.log(err.message);
}
export { sum, format, describe, current, pending, Account };
```

```bash
# ts38b-stage39.sh
#!/usr/bin/env bash
# legacy39.ts 한 장에 "strict": false 를 바닥으로 두고 하위 플래그를 하나씩만 켠다 -- 판 둘
# 칸 = 새로 난 진단 수와 코드(바닥에서 난 것은 뺀다)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
flags=(noImplicitAny noImplicitThis strictNullChecks strictFunctionTypes strictBindCallApply
       strictPropertyInitialization strictBuiltinIteratorReturn useUnknownInCatchVariables
       strictNullChecks+strictPropertyInitialization strictNullChecks+strictBuiltinIteratorReturn
       strictBindCallApply+strictFunctionTypes strictNullChecks+useUnknownInCatchVariables)
diag() { grep -o '^[^ ]*: error TS[0-9]*' | sort; }
short() { sed 's/^legacy39.ts(\([0-9]*\),[0-9]*): error /\1:/; s/^tsconfig.json([0-9]*,[0-9]*): error /설정:/' | sort -t: -k1,1n; }
run() {                               # run <판> <추가 compilerOptions>
  local d; d=$(mktemp -d "$D/c.XXXXXX"); cp legacy39.ts "$d/"
  printf '{ "compilerOptions": { "strict": false, %s"target": "es2022", "noEmit": true }, "files": ["legacy39.ts"] }\n' "$2" > "$d/tsconfig.json"
  if [ "$1" = 7 ]; then (cd "$d" && tsc --pretty false -p tsconfig.json 2>&1) | diag
  else (cd "$d" && node "$OLD" --pretty false -p tsconfig.json 2>&1) | diag; fi
}
run 7 '' > "$D/base7"; run 5 '' > "$D/base5"
echo "바닥(\"strict\": false) -- 7.0.2 $(wc -l < "$D/base7")건 $(sed 's/.*error //' "$D/base7" | tr '\n' ' ')· 5.9.3 $(wc -l < "$D/base5")건"
printf '%-30s %-6s %-6s %s\n' "하나만 켠 플래그" "7.0.2" "5.9.3" "7.0.2 의 새 진단(행:코드)"
tot=0; k=0
for f in "${flags[@]}"; do
  o=""; for g in ${f//+/ }; do o="$o\"$g\": true, "; done
  run 7 "$o" > "$D/o7"; run 5 "$o" > "$D/o5"
  n7=$(comm -13 "$D/base7" "$D/o7" | wc -l); n5=$(comm -13 "$D/base5" "$D/o5" | wc -l)
  what=$(comm -13 "$D/base7" "$D/o7" | short | tr '\n' ' ')
  printf '%-30s %-6s %-6s %s\n' "$f" "$n7" "$n5" "$what"
  k=$((k+1)); [ $k -le 8 ] && tot=$((tot+n7))
done
run 7 '"strict": true, ' > "$D/all7"
echo
echo "하나만 켠 여덟 행의 합 -- 7.0.2 $tot건"
echo "\"strict\": true 로 한 번에 -- 7.0.2 $(wc -l < "$D/all7")건: $(short < "$D/all7" | tr '\n' ' ')"
```

```text
===== bash ts38b-stage39.sh (sh exit=0) =====
바닥("strict": false) -- 7.0.2 0건 · 5.9.3 0건
하나만 켠 플래그        7.0.2  5.9.3  7.0.2 의 새 진단(행:코드)
noImplicitAny                  3      3      2:TS7006 7:TS7006 7:TS7006 
noImplicitThis                 2      2      11:TS2683 11:TS2683 
strictNullChecks               2      2      13:TS2322 14:TS2322 
strictFunctionTypes            1      1      16:TS2322 
strictBindCallApply            1      1      20:TS2345 
strictPropertyInitialization   1      1      설정:TS5052 
strictBuiltinIteratorReturn    0      0      
useUnknownInCatchVariables     1      1      35:TS2339 
strictNullChecks+strictPropertyInitialization 4      4      13:TS2322 14:TS2322 23:TS2564 24:TS2564 
strictNullChecks+strictBuiltinIteratorReturn 3      3      13:TS2322 14:TS2322 30:TS2322 
strictBindCallApply+strictFunctionTypes 3      3      16:TS2322 20:TS2345 21:TS2345 
strictNullChecks+useUnknownInCatchVariables 3      3      13:TS2322 14:TS2322 35:TS18046 

하나만 켠 여덟 행의 합 -- 7.0.2 11건
"strict": true 로 한 번에 -- 7.0.2 14건: 2:TS7006 7:TS7006 7:TS7006 11:TS2683 11:TS2683 13:TS2322 14:TS2322 16:TS2322 20:TS2345 21:TS2345 23:TS2564 24:TS2564 30:TS2322 35:TS18046 
```

그림 해설 — 한 단계에 한 문장.

- ★★ **바닥(`strict: false`)은 0건**, `strict: true` 로 한 번에 켜면 **14건**. 두 판의 수가 **행마다 같았다**.
- ★★★ **하나만 켠 여덟 행의 합은 11건**이고 그중 하나는 **설정 진단**(`TS5052`)이다 — 한 번에 켠 14건과 **안 맞는다.** 플래그끼리 **맞물린 진단**이 있기 때문이다.
- ★★★ **맞물림 넷**(아래 네 행으로 쪼개 확인했다) —
  `strictPropertyInitialization` 은 혼자면 **`TS5052`**(`strictNullChecks` 없이는 못 켠다) — 둘을 같이 켜야 23·24행 `TS2564` 가 난다.
  `strictBuiltinIteratorReturn` 은 혼자면 **0건** — `undefined` 가 `number` 에 들어가 버린다. `strictNullChecks` 와 같이 켜야 30행이 난다.
  `strictBindCallApply` 혼자는 20행만 — **21행**(`apply` 의 튜플)은 `strictFunctionTypes` 와 **같이** 켜야 났다.
  `useUnknownInCatchVariables` 혼자는 35행 **`TS2339`**, `strictNullChecks` 와 같이면 **`TS18046`** — 같은 줄의 **코드가 바뀐다.**
- ★ 한 줄에서 여럿이 난 칸 — 7행 `TS7006` 둘(매개변수 둘) · 11행 `TS2683` 둘(`this` 둘).

```text
  이 탐침 한 장에서 센 것 — 켜는 순서의 근거 (설계 권고 층)

  먼저 — 혼자 켜도 성립하고 진단이 적은 것
    strictFunctionTypes 1 · strictBindCallApply 1 · noImplicitThis 2 · noImplicitAny 3
  축 — 다른 플래그가 기대는 것
    strictNullChecks 2  ← strictPropertyInitialization · strictBuiltinIteratorReturn · useUnknownInCatchVariables 가
                           이것 없이는 못 켜지거나(TS5052) · 0건이거나 · 다른 코드를 낸다
  그 뒤 — strictNullChecks 위에서 켜는 것 (짝 행에서 13·14행 밖의 줄)
    strictPropertyInitialization 23·24행 · strictBuiltinIteratorReturn 30행 · useUnknownInCatchVariables 35행
  ★ 수는 이 한 장의 것이다 — 코드베이스마다 다르다. 맞물림(TS5052 · 0건 · 코드 바뀜)은 탐침과 무관한 성질이다
```

비용 — 하나씩 켜면 **맞물린 진단이 마지막에 한꺼번에** 나온다(합 11 ≠ 14). 그래서 순서는 「진단이 적은 것부터」만으로 못 정하고 **`strictNullChecks` 를 축으로** 둔다. 이 권고는 **탐침 한 장의 수**에 기댄 것이다 — 실제 코드베이스에서 몇 % 가 줄어드는지는 **재지 않았다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  "strict": true                              하위 여덟(5.9.3 은 아홉)을 켠다          (2절)
  "strict": true, "strictNullChecks": false     그것만 끈다 — 하위가 묶음보다 우선      (2절)
  "strict": false                              하위 여덟을 끈다 — 7.0.2 에서 alwaysStrict 는 안 꺼진다  (4절)
  (키 없음)                                     7.0.2 는 true 와 같다 · 5.9.3 · 4.9.5 는 false  (2·3절)
  tsc --showConfig -p tsconfig.json            5.9.3 만 하위를 펼쳐 적는다              (1절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| 7.0.2 에서 `"alwaysStrict": false` | `TS5108` | 2·4절 |
| 4.9.5 에서 `"strictBuiltinIteratorReturn": false` | `TS5023` | 2절 |
| `strictNullChecks` 없이 `"strictPropertyInitialization": true` | `TS5052` | 5절 |
| 7.0.2 · `"strict": false` 에서 예약어 이름 `package` | `TS1212` | 4절 |

**규칙 불릿**

- ★★★ **7.0.2 에서 `strict` 키가 없으면 켜진 것과 같다** — 5.9.3·4.9.5 는 꺼진 것(2·3절).
- ★★★ **하위 플래그 `false` 가 묶음 `true` 보다 우선한다** — 그 탐침만 조용해진다(2절 넷째 열).
- ★★★ **7.0.2 에서 `alwaysStrict` 는 묶음 밖이다** — `strict: false` 로 안 꺼지고 `false` 는 `TS5108`(4절).
- ★★ **`--showConfig` 가 `strict` 를 펼치는 것은 5.9.3 의 성질**이다 — 7.0.2·4.9.5 는 안 펼친다(1절).
- ★★ **`strictPropertyInitialization` 은 `strictNullChecks` 없이 못 켠다**(`TS5052`)(5절).

## 어디서 틀리나

- ★★★ 「**`strict` 를 안 적었으니 느슨하다**」 — **5.9.3 까지**다. 7.0.2 는 **켜져 있다**(3절 — 설정 없이도 `TS2322`).
- ★★★ 「**`strict: false` 면 엄격 모드 에러도 사라진다**」 — 7.0.2 에서 `alwaysStrict` 는 **안 꺼진다**(4절 `TS1212` · `"use strict"`).
- ★★ 「**`--showConfig` 로 켜진 하위 플래그를 확인한다**」 — **5.9.3 에서만** 펼친다(1절).
- ★★ 「**도움말의 기본값 문구가 진실이다**」 — 4.9.5 의 `useUnknownInCatchVariables` 「default: false」는 **틀렸다**(2절 `TS18046`). README 머리말의 「도움말과 실제가 어긋난다」와 같은 집안이다.
- ★★ 「**하위 플래그를 하나씩 켠 진단 수를 더하면 한 번에 켠 수다**」 — **11 ≠ 14**. 맞물린 진단이 있다(5절).
- ★★ 「**`strictPropertyInitialization` 만 먼저 켜 보자**」 — `strictNullChecks` 없이는 **설정 에러**(`TS5052`)(5절).
- ★ 「**`strict` 가 켜는 것은 아홉 — 레퍼런스에 그렇게 적혀 있다**」 — 7.0.2 에서 **끌 수 있는 것은 여덟**이다(4절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **문서(TSConfig 레퍼런스)** | `strict` 기본 `true` · Enables 아홉(`alwaysStrict` 포함) | 기준 소스 |
| **★★★ 판 격자** | 「키 없음」 — 7.0.2 켬 · 5.9.3·4.9.5 끔 | 2절 「키없음」 열 · 3절 |
| **★★★ 판 격자** | `alwaysStrict` — 7.0.2 는 `strict: false` 로 안 꺼지고 `false` 가 `TS5108` · 5.9.3 은 꺼진다 | 4절 — **레퍼런스와 어긋난다** |
| **★ 판 격자** | `strictBuiltinIteratorReturn` — 4.9.5 에 없다(`TS5023`) | 2절 · 1절 `comm` |
| **★ 도구의 판** | `--showConfig` 가 펼치나 — 5.9.3 만 | 1절 |
| **★ 도구의 판** | `--help` 기본값 문구 — 4.9.5 의 `useUnknownInCatchVariables` 가 실제와 다르다 | 1·2절 |
| **컴파일러 동작** | 하위 `false` 가 묶음 `true` 보다 우선 · `strictPropertyInitialization` 은 `strictNullChecks` 를 요구 | 2절 · 5절 `TS5052` |
| **★ 설계 권고** | 켜는 순서 — `strictNullChecks` 를 축으로 | 5절 — **탐침 한 장의 수** |
| **안 잰 것** | 검사 시간 · 실제 코드베이스에서의 진단 분포 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`"strict": true` 를 명시** — 7.0 에서 기본이라도 **적어 두면 판을 안 탄다** | 「키 없음」에 기대기 — 5.x 로 돌린 도구·CI 에서 **뜻이 뒤집힌다** |
| ★★ **`strict: true` + 하위 하나 `false`** — 옮기는 동안 한 플래그만 잠시 끌 때 | `strict: false` 로 **전부** 끄기 — 되켤 때 맞물린 진단이 한꺼번에 온다(5절) |
| ★★ **탐침 한 장으로 설정 확인** — 도구가 안 펼쳐 줄 때(7.0.2) | `--showConfig`·도움말만 믿기 — 판마다 다르고 틀리기도 한다(1절) |
| ★ **`strictNullChecks` 를 축으로 순서 잡기** | 진단 수만 보고 `strictPropertyInitialization` 먼저 — `TS5052` |

## 핵심 문장

1. **7.0.2 에서 `strict` 키가 없으면 켜진 것과 같다** — 설정 없이 던져도 `TS2322`, 5.9.3 은 0줄(격자에서 `11 / 36` 이 갈렸다).
2. **하위 플래그 `false` 는 묶음 `true` 보다 우선한다** — 그 탐침 하나만 조용해진다.
3. **7.0.2 에서 `alwaysStrict` 는 묶음 밖이다** — `strict: false` 로도 `"use strict"` 가 붙고, `alwaysStrict: false` 는 `TS5108` 이다. 레퍼런스의 Enables 목록과 한 칸 어긋난다.
4. **「무엇이 켜졌나」를 도구로 묻는 창은 판마다 다르다** — `--showConfig` 는 5.9.3 만 펼치고, 4.9.5 의 도움말은 틀렸다. 결론은 탐침에 세운다.
5. **하위 플래그는 맞물린다** — 하나씩 켠 합(11)이 한 번에 켠 수(14)와 다르고, `strictNullChecks` 없이는 못 켜거나 조용한 플래그가 있다.

## 관련 자료

- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — ★★★ **README 의 선행.** 7.0 의 `strict` 기본 `true`·`TS5108`·`TS5102` 를 적은 머리말과 7절. **여기는 그 기본값이 무엇을 켜는지 — 하위 플래그 격자부터.**
- [**35번 주제** — 모듈 해석](../35-module-resolution/) — 판마다 다른 기본값을 세 판 격자로 본 방식 · `TS5112`.
- [**12번 주제** — 좁히기](../12-narrowing/) 5절 · [**04번 주제**](../04-any-unknown-never-void/) — `--strict false` 로 같은 파일이 갈리는 칸.
- [**17번 주제** — 변성과 매개변수 양립성](../17-variance-and-parameter-compatibility/) — `strictFunctionTypes` 의 범위.
- [**40번 주제** — `strictNullChecks` 의 파급](../40-strict-null-checks-ripple/) — 5절의 「축」이 무엇을 바꾸는지.
- [**41번 주제** — 인덱스·선택 프로퍼티 엄격 플래그](../41-index-and-optional-property-strict-flags/) — **`strict` 에 안 드는** 두 엄격 플래그.
- [목록의 **42번 주제**](../42-implicit-any-and-catch-variables/)(암시적 `any` 와 catch 변수) — `noImplicitAny`·`useUnknownInCatchVariables` 의 전모. **43번 주제**(`tsconfig` 의 나머지 선택).

## 용어 풀이

> **`strict`** — 엄격 검사 하위 플래그 묶음의 기본값을 한꺼번에 정하는 스위치. 7.0.2 기본 `true`.\
> 예: 2절 「키없음」 열.

> **하위 플래그(strict mode family)** — `strict` 가 기본값을 정하는 개별 플래그. 개별로 적으면 묶음보다 우선한다.\
> 예: 2절 `true+끔` 열.

> **`alwaysStrict`** — 파일을 ECMAScript 엄격 모드로 파싱하고 `"use strict"` 를 방출한다. 7.0.2 에서는 늘 켜져 있고 `false` 는 `TS5108`.\
> 예: 4절 `pr39i`.

> **`--showConfig`** — 설정 파일을 읽어 **실제로 쓸 설정**을 JSON 으로 찍는다. `strict` 를 펼치는 것은 5.9.3 에서만 봤다.\
> 예: 1절.

> **`TS5052`** — 「Option '…' cannot be specified without specifying option '…'.」 — 다른 플래그를 전제로 하는 플래그.\
> 예: 5절 `strictPropertyInitialization`.

> **`TS5023`** — 「Unknown compiler option '…'.」 — 그 판에 없는 옵션.\
> 예: 2절 4.9.5 의 `strictBuiltinIteratorReturn`.

> **`TS1212`** — 「Identifier expected. '…' is a reserved word in strict mode.」 — 엄격 모드의 예약어.\
> 예: 4절 `var package`.

## 더 들어가면

- **`noImplicitOverride`·`noPropertyAccessFromIndexSignature`·`noFallthroughCasesInSwitch`** — 이름에 「엄격」이 들어도 **`strict` 묶음이 아니다.** 41편의 두 플래그와 같은 자리다 — 이 문서는 **던지지 않았다.**
- **`// @ts-nocheck`·파일 단위 완화** — 단계적 전환에서 파일마다 끄는 길. **던지지 않았다.**
- **6.x 판** — 레퍼런스가 「6.0 에서 바뀐」 기본값을 여럿 적는다. 이 머신에 6.x 가 없어 **7.0.2 와 5.9.3 사이**만 봤다.
