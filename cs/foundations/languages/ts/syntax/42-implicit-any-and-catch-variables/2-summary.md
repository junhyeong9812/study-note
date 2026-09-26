# ts/syntax/42 — 암시적 `any` 와 catch 변수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `noImplicitAny`](https://www.typescriptlang.org/tsconfig/#noImplicitAny) · [TSConfig — `useUnknownInCatchVariables`](https://www.typescriptlang.org/tsconfig/#useUnknownInCatchVariables).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** 그래서 본문의 사실은 **전부 직접 던져 받은 진단·방출물·`node` 출력**에만 세운다.
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`** · node 20 은 **`NODE20`**.

```text
===== tsc --version · "$TSC_OLD" · "$TSC_49" --version · node · "$NODE20" --version · nproc · CPU · PATH 의 tsc 첫 두 줄 (sh exit=0) =====
Version 7.0.2
Version 5.9.3
Version 4.9.5
v18.19.1
v20.19.6
nproc 24
Model name: 13th Gen Intel(R) Core(TM) i7-13700HX
#!/usr/bin/env node
import "../lib/tsc.js";
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 「암시적 `any` 격자」(자리 아홉 × `noImplicitAny` 켬/끔 × 두 판 — 칸마다 디렉토리와 `tsconfig.json` 을 따로)이다.** 둘째 기둥은 **3창(방출된 `.js` + `node`)** 이다 — `catch` 로 받은 값을 좁히는 꼴 넷 × 던지는 값 다섯(4절).
> ★★★ **제5의 상태 — `JSON.parse` 가 돌려준 `any` 는 진단 창이 끝까지 조용하다**(1절 `ia42h` 두 칸 다 OK). 「잡히나」를 **`node` 창으로 바꿔** 물었다(3절 — `TypeError`). 바꾼 창이 못 보는 것도 있다 — `node` 는 **실제로 지나간 줄**만 말한다.
> ★★★ **42 는 39 에서 온다.** [**39번 주제**](../39-strict-bundle/)가 **이미 쟀다** — 7.0.2 는 `strict` 키가 없어도 `noImplicitAny`(`TS7006`)와 `useUnknownInCatchVariables`(`TS18046`)가 켜져 있고, `catch` 줄은 `strictNullChecks` 유무로 **`TS2339` ↔ `TS18046`** 이 바뀐다(39편 2·5절). 여기서는 다시 재지 않고 **「어느 자리에서 `any` 가 새어 들어오나」와 「받은 오류 값을 어떻게 다루나」** 로 넓힌다.
> ★★ JS 쪽 사실 — **`throw` 는 아무 값이나 던지고 `stack` 은 `Error` 에만 있다 · 다른 realm 의 오류는 `instanceof Error` 가 `false`** — 는 JS 갈래 [32번](../../../js/syntax/32-error-handling-and-error/)이 쟀다. 여기서는 그 사실 위에서 **TS 의 좁히기 꼴이 무엇을 통과시키나**만 본다.
> ★★ 설정 실험은 **칸마다 디렉토리를 따로** 만들었다 — 7.0.2 는 위쪽 디렉토리에 `tsconfig.json` 이 있으면 파일을 직접 줘도 `TS5112` 로 거부한다(35편 6절). 격자 스크립트는 **칸에 `TS5xxx` 가 들면 멈추고, 모든 칸이 같은 코드면 멈춘다.** ★ 제출 전에 **가짜 옵션을 끼운 판으로 스크립트가 실제로 멈추는지** 먼저 돌려 봤다(`exit 4`).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | `node` 출력 — 4절의 표 · 3절의 `TypeError` 한 줄 | 값만 찍었다 · 스택은 안 찍었다(경로가 박힌다) · node 20 과 **한 글자도 같았다** |
| **판에 매인다** | ★ 종료 코드 — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3 은 `2` | 격자는 **진단 코드로** 갈랐다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 이 주제는 「`any` 가 **생기나**」와 「값을 **어떻게 읽나**」를 묻는다 — 선언의 모양을 묻지 않는다 | — |
| **안 잰 것** | `noImplicitAny` 가 검사 **시간**에 주는 영향 · 실제 코드베이스에서의 진단 분포 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**`noImplicitAny` 는 「이름표 없는 상자는 안 받는」 창고 규칙이다. 상자에 무엇이 들었는지 적혀 있지 않으면 창고지기가 **돌려보낸다.** 그런데 `JSON.parse` 는 상자에 **「아무거나」라는 이름표를 직접 붙여** 가져온다 — 이름표가 있으니 창고지기는 **받는다.** `catch` 로 받은 값은 7.0 에서 **「내용물 미확인」 스티커**(`unknown`)가 붙어 들어온다 — 뜯어서 확인하기 전에는 못 쓴다.**

| 비유 | 실체 |
|---|---|
| 이름표 없는 상자를 **돌려보낸다** | 매개변수·구조 분해·나머지·`o[k]` 에서 `TS7006`·`TS7031`·`TS7019`·`TS7053`(1절) |
| ★★ 들어온 뒤 **내용물을 보고 이름표를 채운다** | `let v; v = 1;` — 제어 흐름이 타입을 **키워 간다**(1절 `ia42d` OK) |
| ★★ 창고 밖 사람이 **아직 안 채운 상자를 꺼내 간다** | 함수가 `v` 를 읽으면 `TS7034`·`TS7005`(1절 `ia42e`) |
| ★★★ **「아무거나」 이름표를 붙여 온 상자** | `JSON.parse` 의 반환 — **명시적 `any`** 라 두 칸 다 OK · `node` 에서 `TypeError`(1·3절) |
| **「내용물 미확인」 스티커** | `catch (e)` 의 `e: unknown` — 좁히기 전에는 `TS18046`(39편) |
| ★★★ 스티커 위에 **「공구」라고 덧써 붙이기** | `e as Error` — 방출물에서 **사라지고**, 던진 것이 문자열이면 `message undefined`(4절) |
| ★★ **다른 창고의 상자**는 우리 인장이 없다 | 다른 realm 의 `Error` — `instanceof Error` 가 `else`, 모양을 보는 가드는 통과(4절) |

- ★★★ 한 줄로 — 「**`noImplicitAny` 는 타입을 「못 정해서」 생긴 `any` 만 잡는다. 누군가 `any` 라고 **적어 둔** 값(`JSON.parse`·`Promise` 의 거절 사유)은 통과시킨다. `catch` 변수는 7.0 에서 `unknown` 이라, 받은 값을 **무엇이든 될 수 있는 것**으로 다루는 꼴만 런타임에서 거짓말을 안 한다.**」

```text
  any 가 들어오는 두 문

  암시적 any   ─ 타입을 적지도 추론하지도 못했다   ─> noImplicitAny 가 잡는다   (TS7006 · TS7031 · TS7019 · TS7034 · TS7053)
  명시적 any   ─ 선언에 any 라고 적혀 있다          ─> 아무도 안 잡는다          (JSON.parse · Promise 의 reason)
                                                       └ 조용히 흘러가 node 에서 드러난다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 어느 자리에서 암시적 `any` 가 생기고, `noImplicitAny` 는 무엇을 잡나** — 자리 아홉 × 켬/끔 × 두 판(1절) · 끄면 **오히려** 진단이 나는 자리(2절).
2. **★★★ `noImplicitAny` 가 못 잡는 `any` 는 무엇이고 어디서 터지나** — `JSON.parse` 의 명시적 `any`(3절) · `Promise` 의 거절 사유(5절).
3. **★★★ `catch` 로 받은 `unknown` 을 어떻게 다루나** — 좁히기 꼴 넷 × 던지는 값 다섯의 `node` 출력(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **암시적 `any` 격자** | 자리 아홉 × `noImplicitAny` 켬/끔 × 7.0.2 · 5.9.3 | 칸마다 진단 코드 | **본체**(1절) |
| ★★★ **3창 — 방출물 + `node`** | 좁히기 꼴 넷 × 던지는 값 다섯 · `JSON.parse` 한 쌍 | 실행 결과 | **둘째 기둥**(3·4절) |
| ★★ **2창 — `null` 탐침** | `const p: null = e` — 그 자리의 타입이 `unknown` 이면 `TS2322`, `any` 면 **침묵** | 진단 코드 | 5절 — 거절 사유 × 세 판 |
| ★★★ **제5의 상태** | `JSON.parse` 의 `any` 는 진단 창이 **답하지 않는다** → `node` 창으로 바꿔 물었다 | — | 3절 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언의 모양을 묻지 않는다 | — | — |

비용 — 격자 36칸(자리 아홉 × 켬/끔 × 두 판) + 진단 전문 · `[]` 대조 셋 · `JSON.parse` 셋(검사 · 선언 줄 · 방출 · `node`) · `catch` 넷(두 판 검사 · 방출물 · node 18/20) · 거절 사유 격자 여섯 줄.

```text
  이 주제의 축 — 「any 는 어디서 왔나」와 「받은 값을 어떻게 읽나」

  타입이 안 적힌 자리      noImplicitAny 켬 ─> TS70xx      끔 ─> 조용히 any
  any 라고 적힌 선언       켬이든 끔이든 ─> 조용히 any       ★ node 에서만 드러난다
  catch (e)               useUnknownInCatchVariables 켬 ─> unknown   끔 ─> any
  .catch((r) => …)        ★ 그 플래그와 무관하게 any
```

### (1) ★★★ 암시적 `any` 격자 — 자리 아홉 × 켬/끔 × 두 판

**언제 쓰나** — 「`noImplicitAny` 를 켜면 어디가 빨개지나」를 **코드 한 줄씩** 확인할 때. 그리고 **안 빨개지는 자리가 안전한지** 가를 때.

탐침 — 자리마다 **그것 하나만** 있는 파일 한 장.

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

```bash
# ts42b-grid42.sh
#!/usr/bin/env bash
# 암시적 any 가 생길 만한 자리 아홉 × noImplicitAny 켬/끔 × 판 둘 -- 칸마다 디렉토리와 tsconfig.json 을 따로 만든다
# 설정은 늘 "strict": true 위에 noImplicitAny 하나만 적는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
rows=(
  "ia42a.ts${T}매개변수"
  "ia42b.ts${T}구조 분해 매개변수"
  "ia42c.ts${T}나머지 매개변수"
  "ia42d.ts${T}let v; 뒤 대입"
  "ia42e.ts${T}let v; 을 함수가 읽음"
  "ia42f.ts${T}빈 배열 []"
  "ia42g.ts${T}콜백 매개변수"
  "ia42h.ts${T}JSON.parse 반환"
  "ia42i.ts${T}o[k] 인덱스 접근"
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
printf '%-9s %-6s %-16s %-10s %s\n' "탐침" "판" "켬" "끔" "자리"
all=""; i=0; split_flag=0; split_ver=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r probe where <<< "$r"
  declare -A got=()
  for s in true false; do
    i=$((i+1)); d="$D/c$i"; mkdir -p "$d" && cp "$probe" "$d/" || exit 3
    printf '{ "compilerOptions": { "strict": true, "noImplicitAny": %s, "target": "es2022", "noEmit": true }, "files": ["%s"] }\n' "$s" "$probe" > "$d/tsconfig.json"
    raw7=$(cd "$d" && tsc --pretty false -p tsconfig.json 2>&1); raw5=$(cd "$d" && node "$OLD" --pretty false -p tsconfig.json 2>&1)
    case "$raw7$raw5" in *"error TS5"*) echo "★ 설정 진단(TS5xxx)이 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
    got[7,$s]=$(codes <<< "$raw7"); got[5,$s]=$(codes <<< "$raw5")
  done
  for v in 7 5; do
    total=$((total+1))
    [ "${got[$v,true]}" != "${got[$v,false]}" ] && split_flag=$((split_flag+1))
    all="$all|${got[$v,true]:-OK}|${got[$v,false]:-OK}"
  done
  [ "${got[7,true]}${T}${got[7,false]}" != "${got[5,true]}${T}${got[5,false]}" ] && split_ver=$((split_ver+1))
  printf '%-9s %-6s %-16s %-10s %s\n' "$probe" "7.0.2" "${got[7,true]:-OK}" "${got[7,false]:-OK}" "$where"
  printf '%-9s %-6s %-16s %-10s %s\n' "" "5.9.3" "${got[5,true]:-OK}" "${got[5,false]:-OK}" ""
  unset got
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "칸에 나온 코드 가짓수 $kinds_seen · 켬과 끔이 갈린 칸 $split_flag / $total · 두 판이 갈린 탐침 $split_ver / ${#rows[@]}"
```

```text
===== bash ts42b-grid42.sh (sh exit=0) =====
탐침    판    켬              끔        자리
ia42a.ts  7.0.2  TS7006           OK         매개변수
          5.9.3  TS7006           OK         
ia42b.ts  7.0.2  TS7031           OK         구조 분해 매개변수
          5.9.3  TS7031           OK         
ia42c.ts  7.0.2  TS7019           OK         나머지 매개변수
          5.9.3  TS7019           OK         
ia42d.ts  7.0.2  OK               OK         let v; 뒤 대입
          5.9.3  OK               OK         
ia42e.ts  7.0.2  TS7005 TS7034    OK         let v; 을 함수가 읽음
          5.9.3  TS7005 TS7034    OK         
ia42f.ts  7.0.2  OK               TS2345     빈 배열 []
          5.9.3  OK               TS2345     
ia42g.ts  7.0.2  OK               OK         콜백 매개변수
          5.9.3  OK               OK         
ia42h.ts  7.0.2  OK               OK         JSON.parse 반환
          5.9.3  OK               OK         
ia42i.ts  7.0.2  TS7053           OK         o[k] 인덱스 접근
          5.9.3  TS7053           OK         

칸에 나온 코드 가짓수 7 · 켬과 끔이 갈린 칸 12 / 18 · 두 판이 갈린 탐침 0 / 9
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **켬에서 잡힌 자리 다섯** — 매개변수 `TS7006` · 구조 분해 `TS7031` · 나머지 `TS7019` · 함수가 읽는 `let v;` `TS7034`+`TS7005` · `o[k]` `TS7053`. 전부 **끄면 OK** 다.
- ★★★ **켬에서도 OK 인 자리 넷** — `let v;` 뒤 대입(`ia42d`) · 콜백 매개변수(`ia42g`) · `JSON.parse`(`ia42h`) · 빈 배열(`ia42f`). ★ 넷의 **까닭이 다르다** — 아래 그림.
- ★★★ **`ia42f` 는 거꾸로다** — 켬이 OK, **끔이 `TS2345`**. 2절이 이 칸을 쪼갠다.
- ★★ **두 판이 갈린 탐침 `0 / 9`** — 7.0.2 와 5.9.3 이 코드까지 같다. 판을 가르는 것은 **기본값**(39편 — 7.0.2 는 키가 없어도 켬)이지 **규칙이 아니다.**
- ★★ 마지막 줄 — **켬과 끔이 갈린 칸 `12 / 18`**(자리 여섯 × 두 판). 안 갈린 여섯 칸이 `ia42d`·`ia42g`·`ia42h` 이다.

```text
  켬에서도 조용한 넷 — 조용한 까닭이 서로 다르다

  ia42d  let v; v = 1;              제어 흐름이 대입을 보고 v 를 number 로 키웠다   ─ 암시적 any 가 아예 안 남았다
  ia42g  [1, 2].map(x => …)         x 가 map 의 매개변수 자리에서 타입을 받았다     ─ 문맥 타입 · any 가 아니다
  ia42f  const xs = []; xs.push(1)  빈 배열도 대입을 보며 키워 간다                  ─ 암시적 any 가 아예 안 남았다
  ia42h  JSON.parse("{}")           선언이 any 를 돌려준다고 적혀 있다               ─ ★ 명시적 any · 검사가 꺼진 채로 흐른다
```

진단 전문 — 격자가 코드만 찍은 칸의 문구.

```text
===== tsc --pretty false --noEmit -t es2022 ia42b.ts ia42c.ts ia42e.ts ia42i.ts (sh exit=0) =====
ia42b.ts(1,14): error TS7031: Binding element 'a' implicitly has an 'any' type.
ia42b.ts(1,17): error TS7031: Binding element 'b' implicitly has an 'any' type.
ia42c.ts(1,12): error TS7019: Rest parameter 'rest' implicitly has an 'any[]' type.
ia42e.ts(1,5): error TS7034: Variable 'v' implicitly has type 'any' in some locations where its type cannot be determined.
ia42e.ts(2,26): error TS7005: Variable 'v' implicitly has an 'any' type.
ia42i.ts(3,11): error TS7053: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type '{ a: number; }'.
  No index signature with a parameter of type 'string' was found on type '{ a: number; }'.
(exit 1)
```

- ★★ `ia42e` 가 **두 줄**이다 — 선언 자리 `(1,5)` 의 **`TS7034`**(「implicitly has type 'any' in some locations where its type cannot be determined.」)와 읽는 자리 `(2,26)` 의 **`TS7005`**. 함수 `read` 는 **언제 불릴지 모르므로** 제어 흐름이 `v` 의 타입을 그 안까지 넘겨주지 못한다.
- ★★ `ia42i` 의 **`TS7053`** 은 둘째 줄이 붙는다 — 「No index signature with a parameter of type 'string' was found on type '{ a: number; }'.」 `k` 가 `string` 이라 `"a"` 말고도 **아무 키**일 수 있다.

비용 — `noImplicitAny` 는 **「타입을 못 정했다」는 사실**만 본다. `any` 를 **돌려받은** 자리는 못 본다 — 3절이 그 구멍이다.

### (2) ★★ 끄면 진단이 **나는** 자리 — 빈 배열 `[]`

**언제 쓰나** — `noImplicitAny` 만 끄고 `strict` 는 둔 설정에서 `xs.push(1)` 이 갑자기 빨개질 때.

```text
===== tsc --pretty false --noEmit -t es2022 ia42f.ts 에 <--noImplicitAny false · --noImplicitAny false --strictNullChecks false · --strict false> (sh exit=0) =====
---- --noImplicitAny false
ia42f.ts(2,9): error TS2345: Argument of type '1' is not assignable to parameter of type 'never'.
(exit 1)
---- --noImplicitAny false --strictNullChecks false
(exit 0)
---- --strict false
(exit 0)
```

- ★★★ **`--noImplicitAny false`**(나머지 `strict` 는 켬) — **`TS2345`**(「Argument of type '1' is not assignable to parameter of type 'never'.」). 빈 배열이 **`never[]`** 가 됐다.
- ★★★ **`strictNullChecks` 까지 끄면 `(exit 0)`** — 그 칸을 `never[]` 로 굳힌 것은 **`strictNullChecks`** 쪽이다. **`--strict false`**(전부 끔)도 `(exit 0)`.
- ★★★ 그래서 빈 배열이 **대입을 보며 타입을 키워 가는 것**(1절 `ia42f` 켬 칸)은 `noImplicitAny` 가 **켜져 있을 때의** 동작이다. `noImplicitAny` 만 끄고 `strictNullChecks` 는 둔 칸에서만 `never[]` 로 굳는다.

```text
  const xs = [];  xs.push(1);  — 설정 넷

  strict 켬 (noImplicitAny 켬)                     xs 가 대입을 보며 number[] 로 자란다     OK
  strict 켬 + noImplicitAny 끔                     xs 가 never[] 로 굳는다                  TS2345
  strict 켬 + noImplicitAny 끔 + strictNullChecks 끔  조용하다                              OK
  strict 끔                                        조용하다                                 OK
```

비용 — 「`noImplicitAny` 를 끄면 **진단이 줄기만** 한다」는 틀린다. 끄는 순간 **다른 추론 규칙**이 들어온다.

### (3) ★★★ 조용한 구멍 — `JSON.parse` 는 명시적 `any` 다

**언제 쓰나** — 설정 파일·API 응답을 `JSON.parse` 로 받아 **바로 필드를 쓰는** 코드를 볼 때.

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

```text
===== tsc --pretty false --noEmit -t es2022 <json42a.ts · json42b.ts · json42c.ts 를 하나씩> (sh exit=0) =====
---- json42a.ts
(exit 0)
---- json42b.ts
json42b.ts(2,22): error TS18046: 'conf' is of type 'unknown'.
(exit 1)
---- json42c.ts
(exit 0)
```

- ★★★ **`json42a.ts` — `(exit 0)`, 진단 0줄.** `conf.port` 를 `number` 칸에 넣었는데 아무 말이 없다. `conf` 가 **`any`** 이기 때문이다 — 그리고 그 `any` 는 **`JSON.parse` 의 선언에 적혀 있는 것**이라 `noImplicitAny` 의 대상이 아니다(1절 `ia42h` 와 같은 칸).
- ★★★ **`json42b.ts` — 받는 쪽에 `: unknown` 한 단어를 붙이자 `TS18046`**(「'conf' is of type 'unknown'.」). `any` 가 **그 자리에서 멈췄다.**
- ★★ **`json42c.ts` — 좁힌 뒤에는 `(exit 0)`.** `typeof … === "object" && … !== null && "port" in … && typeof ….port === "number"` 네 조각이 다 있어야 `conf.port` 가 `number` 로 읽힌다([**04번 주제**](../04-any-unknown-never-void/) 2절의 좁히기와 같은 꼴).

그 `any` 가 어디에 적혀 있나 — 두 판이 싣고 다니는 표준 라이브러리 선언을 직접 읽는다.

```text
===== lib.es5.d.ts 에서 JSON.parse · Promise.prototype.catch 의 선언 줄 -- 7.0.2(PATH 의 tsc 곁 패키지) · 5.9.3("$TSC_OLD" 곁) (sh exit=0) =====
---- 7.0.2
1161:    parse(text: string, reviver?: (this: any, key: string, value: any) => any): any;
1562:    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): Promise<T | TResult>;
---- 5.9.3
1163:    parse(text: string, reviver?: (this: any, key: string, value: any) => any): any;
1564:    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): Promise<T | TResult>;
```

- ★★★ **`parse(…): any;`** — 반환 타입이 선언에 **`any` 라고 적혀 있다.** 두 판이 줄 번호만 다르고 **글자가 같다.** `noImplicitAny` 가 못 보는 까닭이 이 한 줄이다.
- ★★ 같은 블록의 **`catch<TResult = never>(onrejected?: ((reason: any) => …`** — 5절의 거절 사유가 `any` 인 까닭도 **선언**에 있다.

방출해서 돌린다 — 스택에는 절대 경로가 박히므로, 던지면 **이름과 메시지만** 찍는 실행기를 쓴다.

```js
// run42.cjs
// 방출된 파일을 차례로 require 한다 -- 던지면 스택 대신 이름과 메시지만 찍는다(스택에는 절대 경로가 박힌다)
for (const f of process.argv.slice(2)) {
    console.log("---- " + f);
    try {
        require("./" + f);
    } catch (e) {
        console.log("threw " + e.name + " -- " + e.message);
    }
}
```

```text
===== tsc --pretty false -t es2022 --module commonjs --outDir e42 json42a.ts json42c.ts ; 이어서 node run42.cjs e42/json42a.js e42/json42c.js (sh exit=0) =====
(tsc exit 0)
---- e42/json42a.js
threw TypeError -- port.toFixed is not a function
---- e42/json42c.js
number 0.0
(node exit 0)
```

- ★★★ **`json42a.js` — `TypeError`(「port.toFixed is not a function」).** 타입은 `number` 라고 했지만 실제 값은 문자열 `"8080"` 이다. **tsc 가 아무 말도 안 한 줄이 `node` 에서 터졌다.**
- ★★ **`json42c.js` — `number 0.0`.** 좁히기가 `"8080"`(문자열)을 **걸러** 기본값 `0` 으로 갔다 — 같은 입력에서 **터지지 않는다.**

```text
  같은 JSON 한 줄 — 받는 꼴 셋

  const conf = JSON.parse(…)            any      tsc 조용   ─> node 에서 TypeError 「port.toFixed is not a function」
  const conf: unknown = JSON.parse(…)   unknown  tsc TS18046 (쓰기 전에 좁혀라)
  … 좁힌 뒤                               number   tsc 조용   ─> node 「number 0.0」  (문자열이라 기본값으로)
```

비용 — `: unknown` 한 단어가 **검사 구멍을 막는 비용의 전부**다. 대신 쓰는 자리마다 좁히기를 **직접 써야** 한다(`json42c` 의 네 조각).

### (4) ★★★ `catch` 변수 다루기 — 좁히는 꼴 넷 × 던지는 값 다섯

**언제 쓰나** — `catch (e)` 에서 `e.message` 를 찍으려는데 7.0 이 `TS18046` 을 낼 때(39편 2절 `pr39h`). **무엇으로 좁힐지** 고를 때.

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

```text
===== tsc --pretty false --noEmit -t es2022 catch42.ts ; 이어서 "$TSC_OLD" 로 --strict 를 붙여 같은 것 (sh exit=0) =====
(7.0.2 exit 0)
(5.9.3 exit 0)
```

- ★★★ **네 꼴 전부 두 판에서 `(exit 0)`** — `unknown` 을 받는 네 함수가 **모두 타입 검사를 통과한다.** 검사기는 **넷 중 무엇이 런타임에서 거짓말을 하는지** 가르지 않는다.
- ★ `declare const require` 한 줄은 `vm` 을 부르기 위한 것이다 — 이 머신에는 `@types/node` 가 없고 7.0.2 의 `types` 기본값은 `[]` 다(38편).

`e as Error` 가 방출물에서 무엇이 되나.

```text
===== tsc --pretty false -t es2022 --module commonjs --outDir e42c catch42.ts ; 방출물에서 viaAs 함수만 sed 로 (sh exit=0) =====
(tsc exit 0)
function viaAs(e) {
    return "message " + e.message;
}
```

- ★★★ **`(e as Error).message` → `e.message`.** `as Error` 는 **한 글자도 안 남는다** — 검사만 조용히 시키고 **실행 시 확인은 없다**([**30번 주제**](../30-type-assertions-and-non-null/)의 단언과 같은 칸).

```text
===== node e42c/catch42.js ; 이어서 "$NODE20" 로 같은 것을 돌려 cmp (sh exit=0) =====
(node exit 0)
thrown            instanceof   | typeof       | guard        | as Error
new Error("m")    Error m      | else         | message m    | message m
"m"               else         | string m     | else         | message undefined
null              else         | else         | else         | TypeError
{ message: "m" }  else         | else         | message m    | message m
vm realm Error    else         | else         | message m    | message m
node v20.19.6 의 출력: 한 글자도 같다
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`as Error` 열** — `"m"` 을 던지면 **`message undefined`**(에러 없이), `null` 을 던지면 **`TypeError`**. 앞쪽이 더 나쁘다 — **조용히 틀린 로그**가 남는다.
- ★★★ **`instanceof` 열** — `new Error` 만 `Error m`. **다른 realm 의 `Error` 는 `else`** — JS 32편 7절의 「다른 realm 의 오류는 `instanceof Error` 가 `false`」가 **TS 의 좁히기 결과를 그대로 바꾼다.**
- ★★ **`typeof` 열** — 문자열만 잡는다. **다른 것은 전부 `else`** — 이 꼴 하나로는 부족하고 **다른 꼴과 짝으로** 쓴다.
- ★★★ **`guard` 열**(`"message" in x && typeof x.message === "string"`) — `new Error` · 평범한 객체 · **다른 realm 의 `Error`** 셋을 잡고, 문자열·`null` 은 `else`. **모양을 보는 가드**라 realm 을 안 탄다 — 대신 `{ message: "m" }` 같은 **흉내**도 통과시킨다.
- ★ node 20 의 출력도 **한 글자도 같았다**(블록 끝 줄).

```text
  던진 값 × 좁히는 꼴 — 이 판의 출력

                     instanceof    typeof      guard        as Error
  new Error("m")     잡는다        else        잡는다       잡는다
  "m"                else          잡는다      else         ★ message undefined   (조용히 틀림)
  null               else          else        else         ★ TypeError           (읽는 순간 터짐)
  { message: "m" }   else          else        잡는다       잡는다
  다른 realm Error    ★ else        else        잡는다       잡는다
```

비용 — **어느 한 꼴도 다섯을 다 맞히지 못한다.** `instanceof` 는 realm 을 타고, 가드는 흉내를 통과시키고, `typeof` 는 하나만 본다. 그래서 흔한 꼴은 **`instanceof Error` → 아니면 `String(e)`** 처럼 **남는 경우를 문자열로 떨어뜨리는 것**이다 — 이것은 **설계 권고**이고 위 표의 칸 수로 증명한 것은 아니다.

### (5) ★★ 거절 사유는 `unknown` 이 아니다 — `Promise` 의 콜백

**언제 쓰나** — `try/catch` 는 `unknown` 인데 **`.catch((r) => r.message)` 는 왜 조용한지** 물을 때.

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

```bash
# ts42b-reason42.sh
#!/usr/bin/env bash
# reason42.ts 를 useUnknownInCatchVariables 켬/끔 × 판 셋으로 -- 줄마다 난 진단(행:코드)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
cells() { grep -o '^reason42.ts([0-9]*,[0-9]*): error TS[0-9]*' | sed 's/^reason42.ts(\([0-9]*\),[0-9]*): error /\1:/' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-8s %-6s %s\n' "판" "설정" "행:코드"
all=""
for v in 7.0.2 5.9.3 4.9.5; do
  for u in true false; do
    case $v in 7.0.2) c=(tsc) ;; 5.9.3) c=(node "$OLD") ;; 4.9.5) c=(node "$V49") ;; esac
    raw=$("${c[@]}" --pretty false --noEmit -t es2022 --strict --useUnknownInCatchVariables "$u" reason42.ts 2>&1)
    case "$raw" in *"error TS5"*) echo "★ 설정 진단(TS5xxx)이 들었다 -- 멈춘다"; exit 4 ;; esac
    got=$(cells <<< "$raw"); all="$all|$got"
    printf '%-8s %-6s %s\n' "$v" "$u" "$got"
  done
done
echo
echo "켬/끔 × 판 여섯 줄에서 서로 다른 답 $(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)가지"
```

```text
===== bash ts42b-reason42.sh (sh exit=0) =====
판      설정 행:코드
7.0.2    true   2:TS2322 5:TS2322 7:TS1196
7.0.2    false  5:TS2322 7:TS1196
5.9.3    true   2:TS2322 5:TS2322 7:TS1196
5.9.3    false  5:TS2322 7:TS1196
4.9.5    true   2:TS2322 5:TS2322 7:TS1196
4.9.5    false  5:TS2322 7:TS1196

켬/끔 × 판 여섯 줄에서 서로 다른 답 2가지
```

- ★★★ **2행(`catch (e)`)은 켬에서만 `TS2322`**(「Type 'unknown' is not assignable to type 'null'.」) — 끄면 `any` 라 **침묵**한다. `useUnknownInCatchVariables` 가 **이 자리만** 바꾼다.
- ★★★ **3·4행(`.catch` 콜백 · `.then` 의 둘째 콜백)은 켬에서도 끔에서도 침묵** — 거절 사유 `r` 은 **플래그와 무관하게 `any`** 다. 세 판이 같다. 선언이 `(reason: any)` 라고 적어 둔 자리다(3절의 선언 줄).
- ★★ **5행(`catch (e: unknown)`)은 늘 `TS2322`** — 직접 적으면 플래그와 무관하게 `unknown`. **6행(`e: any`)은 늘 침묵.**
- ★★ **7행(`catch (e: Error)`)은 늘 `TS1196`**(「Catch clause variable type annotation must be 'any' or 'unknown' if specified.」) — `catch` 변수에 **`Error` 를 적을 수 없다.**
- ★ 마지막 줄 — 여섯 줄에서 **서로 다른 답 2가지** — 켬 셋이 한 글자도 같고, 끔 셋이 한 글자도 같다. **판은 답을 안 바꿨다.**

```text
  오류 값이 들어오는 자리 × 받는 타입 (세 판 공통)

                                   useUnknownInCatchVariables 켬     끔
  try {…} catch (e)                unknown                            any
  catch (e: unknown)               unknown                            unknown
  catch (e: any)                   any                                any
  catch (e: Error)                 TS1196 — 적을 수 없다               TS1196
  p.catch((r) => …)                ★ any                              any
  p.then(_, (r) => …)              ★ any                              any
```

비용 — **`Promise` 를 쓰는 코드는 `try/catch` 로 옮기거나 `(r: unknown)` 을 직접 적어야** `catch` 절과 같은 보호를 받는다. 플래그가 대신해 주지 않는다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  "noImplicitAny": true                        타입을 못 정한 자리를 TS70xx 로 잡는다          (1절)
  const x: unknown = JSON.parse(s)             명시적 any 를 그 자리에서 멈춘다 — 쓰기 전에 좁힌다   (3절)
  catch (e)                                    7.0.2 기본 unknown — useUnknownInCatchVariables  (39편 · 5절)
  catch (e: unknown) · catch (e: any)          적을 수 있는 둘                                   (5절)
  e instanceof Error · typeof e === "string"   좁히는 꼴 — 무엇을 통과시키나는 4절 표
  function g(x: unknown): x is { message: string }   사용자 가드 — 모양을 본다                   (4절)
  p.catch((r: unknown) => …)                   거절 사유는 직접 적어야 unknown                    (5절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `function f(x) {}` (켬) | `TS7006` | 1절 |
| `function f({ a, b }) {}` (켬) | `TS7031` | 1절 |
| `function f(...rest) {}` (켬) | `TS7019` | 1절 |
| `let v;` 를 함수가 읽음 (켬) | `TS7034` + `TS7005` | 1절 |
| `o[k]` — `k: string` (켬) | `TS7053` | 1절 |
| `const xs = []; xs.push(1)` — `noImplicitAny` 만 끔 | `TS2345`(`never`) | 2절 |
| `const c: unknown = JSON.parse(…)` 뒤 바로 `c.port` | `TS18046` | 3절 |
| `catch (e: Error)` | `TS1196` | 5절 |

**규칙 불릿**

- ★★★ **`noImplicitAny` 는 「못 정해서 생긴」 `any` 만 잡는다** — `JSON.parse` 처럼 선언이 `any` 를 돌려주면 켬에서도 조용하다(1·3절).
- ★★★ **`let v;`·`[]` 는 대입을 보며 타입이 자란다** — 켬에서도 OK. 단 **함수가 그 변수를 읽으면** `TS7034`(1절).
- ★★★ **`as Error` 는 방출물에 안 남는다** — 문자열을 던지면 `message undefined`(4절).
- ★★★ **거절 사유는 `useUnknownInCatchVariables` 와 무관하게 `any`** — 세 판 공통(5절).
- ★★ **`catch` 변수 주석은 `unknown`·`any` 둘뿐** — `Error` 는 `TS1196`(5절).

## 어디서 틀리나

- ★★★ 「**`noImplicitAny` 를 켰으니 `any` 는 없다**」 — **명시적 `any`** 는 그대로 흐른다. `JSON.parse` 가 대표다(3절 — tsc 0줄, `node` 는 `TypeError`).
- ★★★ 「**`catch (e)` 에서 `(e as Error).message` 면 된다**」 — 문자열을 던지면 **`undefined`** 가 조용히 찍히고 `null` 이면 터진다(4절). `as` 는 **검사를 끌 뿐** 확인하지 않는다.
- ★★★ 「**`e instanceof Error` 면 모든 오류를 잡는다**」 — **다른 realm 의 `Error`** 를 놓친다(4절 · JS 32편 7절).
- ★★★ 「**`useUnknownInCatchVariables` 가 `Promise` 의 `.catch` 도 덮는다**」 — 안 덮는다. 거절 사유는 **`any`**(5절).
- ★★ 「**`noImplicitAny` 를 끄면 진단이 줄기만 한다**」 — `strictNullChecks` 가 켜진 채면 빈 배열이 `never[]` 가 되어 **`TS2345` 가 새로 난다**(2절).
- ★★ 「**`let v;` 는 무조건 암시적 `any` 다**」 — 대입을 보며 자라면 **진단이 없다.** 걸리는 것은 **함수가 그 변수를 읽을 때**다(1절 `ia42d` 대 `ia42e`).
- ★ 「**`catch (e: Error)` 로 적으면 된다**」 — `TS1196`. 적을 수 있는 것은 `unknown`·`any` 뿐이다(5절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **ECMAScript** | `throw` 는 아무 값이나 던진다 · 다른 realm 의 `Error` 는 `instanceof Error` 가 `false` | JS 32편 6·7절(이 편은 다시 재지 않았다) |
| **★★★ tsc 동작 — 두 판 같음** | 자리 아홉의 진단 코드 · `JSON.parse` 가 `any` | 1절 — 갈린 탐침 `0 / 9` |
| **★★★ tsc 동작 — 세 판 같음** | `catch` 변수 주석 · 거절 사유 `any` · `TS1196` | 5절 — 서로 다른 답 2가지 |
| **★ 판의 기본값** | 7.0.2 는 키가 없어도 `noImplicitAny`·`useUnknownInCatchVariables` 켬 | 39편(인용) |
| **★ 선언 파일(`lib`)** | `JSON.parse` 의 반환 · 거절 사유가 `any` 인 것은 **`lib.es5.d.ts` 에 그렇게 적혀 있어서**다 | 3절 선언 줄 — 두 판이 글자가 같다 |
| **node 동작** | 4절 표 · 3절 `TypeError` 한 줄 | node 18 · 20 이 한 글자도 같다 |
| **★ 설계 권고** | `instanceof` → 아니면 문자열로 떨어뜨리기 | 4절 비용 — **표로 증명한 것이 아니다** |
| **안 잰 것** | 검사 시간 · 실제 코드베이스의 진단 분포 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **경계 밖 값은 `: unknown` 으로 받는다** — `JSON.parse`·`catch`·거절 사유 | 받은 `any` 를 그대로 필드 접근 — 검사가 **꺼진 채** 흐른다(3절) |
| ★★★ **`catch` 는 `instanceof` + 남는 경우의 처리를 둘 다** 둔다 | `e as Error` 하나로 끝내기 — 조용히 `undefined`(4절) |
| ★★ **모양을 봐야 할 때는 사용자 가드** — realm 을 안 탄다 | 가드만 믿고 흉내(`{ message }`)도 오류로 치기 — 목적에 맞는지 먼저 본다(4절) |
| ★★ **`.catch((r: unknown) => …)` 를 직접 적는다** | 플래그가 거절 사유까지 덮을 것이라 믿기(5절) |
| ★ `noImplicitAny` 는 **켠 채로** 둔다 | 부분적으로 끄기 — 빈 배열이 `never[]` 가 되는 칸이 생긴다(2절) |

## 핵심 문장

1. **`noImplicitAny` 는 타입을 못 정해서 생긴 `any` 만 잡는다** — 자리 다섯에서 `TS70xx`, 대입을 보며 자라는 `let v;`·`[]` 와 콜백 매개변수는 조용하다(격자 `12 / 18`).
2. **명시적 `any` 는 아무도 안 잡는다** — `JSON.parse` 는 켬에서도 0줄이고, 그 줄이 `node` 에서 `TypeError` 로 터진다. `: unknown` 한 단어가 그 자리에서 멈춘다.
3. **`as Error` 는 방출물에 안 남는다** — 문자열을 던지면 `message undefined` 가 조용히 찍힌다.
4. **좁히는 꼴은 각자 다른 것을 놓친다** — `instanceof` 는 다른 realm 을, 가드는 흉내를, `typeof` 는 나머지 전부를.
5. **거절 사유는 플래그와 무관하게 `any`** 이고 `catch` 변수에 적을 수 있는 주석은 `unknown`·`any` 둘뿐이다(`TS1196`).

## 관련 자료

- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — ★★★ **README 의 선행.** 7.0.2 기본값 · `pr39a`(`TS7006`) · `pr39h`(`TS18046`) · `strictNullChecks` 유무로 `TS2339` ↔ `TS18046`. **여기는 그 두 플래그의 자리와 다루는 법부터.**
- JS 갈래 [**32번** — 오류 처리와 `Error`](../../../js/syntax/32-error-handling-and-error/) — ★★★ **README 의 선행.** `throw` 임의 값 · `stack` · 다른 realm. **그쪽은 값이 무엇이냐, 여기는 TS 가 그 값을 어떻게 좁히느냐.**
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) 2·3절 — `unknown` 이 좁히기를 강제하고 `any` 는 번진다.
- [**12번 주제** — 좁히기](../12-narrowing/) · [**13번 주제** — 타입 가드와 술어](../13-type-guards-and-predicates/) — 4절의 `instanceof`·`typeof`·`in` · 사용자 가드. 13편 2절은 **거짓말하는 술어**를 쟀다.
- [**30번 주제** — 타입 단언과 non-null](../30-type-assertions-and-non-null/) — `as` 가 방출물에서 사라지는 칸.
- [**40번 주제** — `strictNullChecks` 의 파급](../40-strict-null-checks-ripple/) — 2절에서 빈 배열을 `never[]` 로 굳힌 플래그의 전모.
- 예외 타입이 언어로 정해진 갈래의 대비 — Kotlin 갈래 [**34번**](../../../kotlin/syntax/34-exceptions-nothing-and-try-expression/) · Java 갈래 [**25번**](../../../java/syntax/25-exceptions/). **이 편은 그쪽을 다시 재지 않았다.**

## 용어 풀이

> **암시적 `any`(implicit any)** — 타입을 적지도 추론하지도 못해 컴파일러가 `any` 로 둔 것. `noImplicitAny` 가 `TS70xx` 로 잡는다.\
> 예: 1절 `function f(x)`.

> **명시적 `any`** — 선언에 `any` 라고 적혀 있는 것. `noImplicitAny` 의 대상이 아니다.\
> 예: 3절 `JSON.parse` 의 반환.

> **제어 흐름으로 자라는 타입(evolving type)** — 타입 없이 선언한 `let v;`·`[]` 가 뒤의 대입을 보며 타입을 얻는 것.\
> 예: 1절 `ia42d`·`ia42f` — 켬에서도 OK.

> **`useUnknownInCatchVariables`** — `catch (e)` 의 `e` 를 `any` 대신 `unknown` 으로 두는 플래그. 거절 사유는 안 바꾼다.\
> 예: 5절 2행 대 3·4행.

> **사용자 가드(type predicate)** — `x is T` 를 돌려주는 함수. 참이면 그 분기에서 `x` 를 `T` 로 읽는다. 몸통이 맞는지는 **검사하지 않는다**(13편).\
> 예: 4절 `hasMessage`.

> **realm** — 전역 객체·내장 생성자 한 벌. `vm` 의 새 컨텍스트는 **다른 `Error`** 를 가진다.\
> 예: 4절 「vm realm Error」 행.

> **`TS1196`** — 「Catch clause variable type annotation must be 'any' or 'unknown' if specified.」\
> 예: 5절 7행.

## 더 들어가면

- **`Error.isError`(ES2026)** — realm 을 안 타는 판정이다. JS 32편 7절이 쟀다 — **이 편은 던지지 않았다.**
- **`noImplicitAny` 와 JS 파일** — `checkJs` 에서 JSDoc 없는 매개변수가 어떻게 되는지는 목록의 **48번 주제**(JS 파일 타입 검사)다. **던지지 않았다.**
- **`@typescript-eslint/no-unsafe-*`** — 명시적 `any` 가 흐르는 자리를 잡는 린트 규칙. tsc 밖이라 **던지지 않았다.**
