# ts/syntax/45 — 타입 수준 성능 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript Wiki — Performance](https://github.com/microsoft/TypeScript/wiki/Performance) · [TSConfig — `extendedDiagnostics`](https://www.typescriptlang.org/tsconfig/#extendedDiagnostics) · [`generateTrace`](https://www.typescriptlang.org/tsconfig/#generateTrace).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** ★★★ **「7.0 네이티브 포트가 N배 빠르다」는 공식 수치도 이 머신에 받아 둔 문서가 없어 「출처 확인 못 함」이다** — 이 문서의 배수는 전부 **이 판 · 이 입력 · 7판 중앙값의 비**이고 흔들리는 칸이다(5절).
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**. ★ **`PATH` 의 `tsc` 는 node 로 시작하는 발사대**다(블록 끝 두 줄) — 7.0.2 의 벽시계 시간에도 **node 기동이 들어 있다.**

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

> ★★★ **본체 창 선언 — 이 주제의 본체는 가이드 규칙 24 다: 「한 판에서 잰 절댓값은 근거가 아니다 — 판 격자를 돌려라」.** 그래서 창이 둘로 갈린다 — **결정적 칸**(`--extendedDiagnostics` 의 `Types`·`Instantiations` · `TS2589`/`TS2590` 문턱)과 **흔들리는 칸**(시간). ★★★ **주장은 결정적 칸 위에만 세운다.** 시간은 **판 셋 × 입력 다섯 × 7판**의 중앙값·최소·최대로만 적고, 그 블록은 재대조에서 **「흔들린 칸」으로 선언**해 둔다.
> ★★★ **제5의 상태 — 「두 판의 타입 시스템이 같은 일을 하나」를 수로 물었더니 7.0.2 의 기본값이 답을 흐렸다.** 7.0.2 는 **검사기(checker) 넷을 기본으로 돌려** 표준 라이브러리 타입을 **검사기마다 따로** 만든다 — 같은 빈 파일의 `Types` 가 5.9.3 의 두 배 가까이 나온다(3절). **`--checkers 1` 로 창을 바꿔** 물으니 `Instantiations` 가 한 글자도 같아졌다(2절).
> ★★★ **45 는 25 에서 온다.** [**25번 주제**](../25-infer-and-recursive-conditional-types/) 5·6절이 7.0.2 에서 **`TS2589` 의 문턱**(길이를 세는 재귀 999 대 1000 · 스프레드로 쌓는 꼴 48 대 49)을 쟀고 **「이 절에 느리다는 말이 없다 — 시간을 재지 않았다」** 로 끝냈다. 여기서는 그 문턱을 **세 판**으로 다시 던지고(1절), **시간은 여기서 처음** 잰다(5절).
> ★ 탐침은 전부 **생성기 한 장**(`ts42b-gen45.sh`)이 찍는다 — 크기를 인자로 받아 2단 이상으로 키운다. 설정은 판 둘에 **같은 `tsconfig.json`**(`target`·`lib` es2022 · `types: []` · `strict` · `noEmit`).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | ★★★ `Types`·`Instantiations` — 같은 판 · 같은 입력 · 같은 `--checkers` | 재대조(캡처를 처음부터 한 번 더)에서 **동일** · 탐색에서 12판 되풀이도 **한 값**이었다(블록 없음) |
| **안 흔들린다** | ★★★ `TS2589`·`TS2590` 의 **문턱**(OK 와 진단이 갈리는 크기) | 진단 코드다 |
| **안 흔들린다** | ★★ `--generateTrace` 가 쓴 **파일 이름** | 이름만 찍었다 |
| **안 흔들린다** | ★★ 5절의 **`판정\|` 줄**(「범위가 안 겹친다: 참」) | 격차가 흔들림보다 크다 — 재대조에서 동일 |
| **★ 흔들린다** | ★★★ 5절의 **`시간\|` 줄 전부** — 벽시계 ms · `Check time` · 중앙값의 비 · 교차 대 인터페이스의 겹침 | **실행마다 바뀐다.** 재대조기는 이 줄을 `시간\|<흔들림>` 으로 정규화해 **「흔들린 칸」** 으로 센다 |
| **★ 판에 매인다** | ★★★ 7.0.2 의 `Types`·`Instantiations` 는 **`--checkers` 값에 매인다** | 3절 — 결론 자체다 |
| **안 잰 것** | 메모리 · 여러 파일 프로젝트에서의 병렬 이득 · 실제 코드베이스 | **재지 않았다** — 탐침은 **파일 하나**다 |

## 한눈에 — 쉽게 말하면

**타입 검사 비용은 「계산서 두 장」으로 읽는다. 한 장은 **몇 개를 만들었나**(타입 수 · 인스턴스화 수) — 같은 주문이면 늘 같은 숫자가 찍힌다. 다른 한 장은 **몇 분 걸렸나**(시간) — 같은 주문도 그날 부엌 사정에 따라 바뀐다. 7.0 은 **요리사를 바꾼** 것(Go 로 다시 쓴 컴파일러 · 검사기 여럿)이지 **조리법을 바꾼** 것이 아니다 — 그래서 첫 장은 같고 둘째 장만 달라진다.**

| 비유 | 실체 |
|---|---|
| **몇 개 만들었나** — 같은 주문이면 같은 숫자 | `Types`·`Instantiations` — 결정적(2절) |
| **몇 분 걸렸나** — 그날그날 다르다 | 벽시계 · `Check time` — 7판의 중앙값·범위로만(5절) |
| ★★★ **조리법은 같다** | `--checkers 1` 의 7.0.2 와 5.9.3 이 `Instantiations` **같은 행 `9 / 11`** · 두 크기 사이 증분은 **`5 / 5`** 같다(2절) |
| ★★★ 요리사 **넷이 각자 밑재료를 손질** | 7.0.2 기본 검사기 넷 — 빈 파일의 `Types` 가 `3340` → `6278`(3절) |
| **솥이 넘치는 선** | `TS2589`(깊이) · `TS2590`(유니온 크기) — **세 판이 같은 크기에서** 넘쳤다(1절) |
| ★★ 「이 요리법이 더 빠르다」는 소문 | 교차 대 인터페이스 — 인스턴스화 수는 **같고**, 타입 수는 **인터페이스가 더 많고**, 시간은 **겹치나 안 겹치나부터 캡처마다 바뀌었다**(4·5절) |

- ★★★ 한 줄로 — 「**같은 입력에서 타입 시스템이 만든 수는 두 판이 같다(검사기를 하나로 맞추면). 7.0 이 바꾼 것은 그 일을 하는 기계(네이티브 · 병렬)이고, 그 차이는 시간으로만 보이며, 시간은 판 격자와 여러 판의 중앙값으로만 말한다.**」

```text
  계산서 두 장 — 무엇을 근거로 쓰나

  결정적   Types · Instantiations · TS2589/TS2590 문턱    같은 입력 · 같은 판 · 같은 --checkers 면 같다   ─> 주장은 여기에
  흔들림   벽시계 ms · Check time · 판 사이의 배수         실행마다 다르다                                 ─> 7판 중앙값·범위로만, 「흔들린 칸」으로 선언
```

## 이 주제가 답하려는 질문

원고가 없는 관용구 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 무엇이 검사를 태우나 — 그 경로는 어디서 벽에 닿나** — 깊은 재귀 조건부 · 거대 유니온의 문턱 × 세 판(1절) · 크기 2단의 수(2절).
2. **★★★ 7.0 네이티브 포트가 바꾼 것과 바꾸지 않은 것** — 같은 입력의 `Types`·`Instantiations`(2절) · 검사기 수가 수를 바꾸는 것(3절) · 시간(5절).
3. **★★ 줄이는 수 — 교차 대 인터페이스는 무엇으로 가르나** — 수(2·4절)와 시간(5절)이 각각 무엇을 말하나.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **결정적 칸 — `--extendedDiagnostics` 의 `Types`·`Instantiations`** | 타입 시스템이 **만든 수** | 같은 입력이면 같다 | **본체의 근거**(2·3·4절) |
| ★★★ **문턱 격자** | 크기 × 세 판 — `OK` 대 `TS2589`·`TS2590` | 진단 코드 | 1절 |
| ★★★ **시간 격자(규칙 24)** | 입력 다섯 × 설정 셋 × 7판 — 중앙값·최소·최대 | **흔들림** | 5절 — `판정\|` 줄만 결론 |
| ★★ **`--generateTrace`** | 트레이스 파일이 **생기나** · 몇 개인가 | 파일 이름 | 3절 — 검사기 수의 흔적 |
| ★★★ **제5의 상태 — `--checkers 1`** | 7.0.2 의 기본(검사기 넷)이 수를 부풀려 **같은 질문을 검사기 하나로** | 결정적 | 2·3절 |
| ★ **부적용 — 3창(방출)** | 전부 타입 층이다 — 설정이 `noEmit` | — | — |

비용 — 문턱 24칸(여덟 × 세 판) + 진단 전문 · 수 33판(열하나 × 셋) · 검사기 일곱 판 · 시간 105판(다섯 × 셋 × 7).

```text
  이 주제의 축 — 「무엇이 불어나나」와 「누가 계산하나」

  깊이      Count<[], N> · 스프레드로 쌓는 A<…>     Instantiations 가 N 따라 불어난다 ─> 끝에서 TS2589
  폭        `${A}-${A}` (N×N) · `${A}${A}${A}` (N³)  Types 가 원소 수 따라 불어난다    ─> 끝에서 TS2590
  모양      교차 D = B0 & … 대 interface D extends …  같은 관계를 두 모양으로
  계산하는 쪽  5.9.3 (JS) · 7.0.2 (네이티브 · 검사기 N 개)  ─> 수는 같게, 시간은 다르게
```

생성기 — 탐침은 전부 이 한 장이 찍는다.

```bash
# ts42b-gen45.sh
#!/usr/bin/env bash
# ts42b-gen45.sh <꼴> <크기> -- 45 의 탐침 파일을 표준 출력으로 찍는다
#   base   0  : export 한 줄 -- 표준 라이브러리만 검사하는 바닥
#   count  N  : 길이를 세는 꼬리 재귀 조건부 Count<[], N>
#   spread N  : 겹마다 튜플 스프레드로 쌓는 재귀 A<[1 × N]>(25편 6절의 A 꼴)
#   union  N  : 리터럴 N 개 유니온 A 로 `${A}-${A}` -- 원소 N×N
#   cube   N  : 같은 A 로 `${A}${A}${A}` -- 원소 N×N×N
#   xsect  K,M: 기반 인터페이스 K 개를 교차(&)로 묶은 타입 M 개 -- M 개끼리 서로 대입
#   iface  K,M: 같은 것을 interface … extends 로 -- D 를 만드는 줄 말고는 xsect 와 같다
set -u -o pipefail
kind=${1:?꼴} size=${2:?크기}
case $kind in
  base)
    echo 'export {};' ;;
  count)
    echo 'type Count<N extends readonly unknown[], Stop extends number> = N["length"] extends Stop ? N : Count<[...N, 1], Stop>;'
    echo "export type R = Count<[], $size>;"
    echo "export const r: R[\"length\"] = $size;" ;;
  spread)
    echo 'type A<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];'
    printf 'export type R = A<['; for ((i = 1; i <= size; i++)); do printf '1'; if ((i < size)); then printf ', '; fi; done; echo ']>;'
    echo 'export declare const r: R;' ;;
  union)
    printf 'type A ='; for ((i = 0; i < size; i++)); do printf ' | "a%d"' "$i"; done; echo ';'
    echo 'export type U = `${A}-${A}`;'
    echo 'export const u: U = "a0-a0";' ;;
  cube)
    printf 'type A ='; for ((i = 0; i < size; i++)); do printf ' | "a%d"' "$i"; done; echo ';'
    echo 'export type U = `${A}${A}${A}`;'
    echo 'export const u: U = "a0a0a0";' ;;
  xsect|iface)
    K=${size%,*} M=${size#*,}
    for ((b = 0; b < K; b++)); do echo "interface B$b<T> { p$b: T; q$b: string; }"; done
    for ((m = 0; m < M; m++)); do
      if [ "$kind" = xsect ]; then
        printf 'type D%d =' "$m"; for ((b = 0; b < K; b++)); do printf ' B%d<number> &' "$b"; done; echo ' { own: boolean };'
      else
        printf 'interface D%d extends' "$m"; for ((b = 0; b < K; b++)); do printf ' B%d<number>' "$b"; if ((b < K - 1)); then printf ','; fi; done; echo ' { own: boolean }'
      fi
      echo "declare const v$m: D$m;"
    done
    for ((m = 0; m < M; m++)); do for ((n = 0; n < M; n++)); do if ((m != n)); then echo "export const w${m}_$n: D$m = v$n;"; fi; done; done ;;
  *) echo "모르는 꼴: $kind" >&2; exit 2 ;;
esac
```

```text
===== bash ts42b-gen45.sh <union 3 · xsect 2,2 · iface 2,2> (sh exit=0) =====
---- union 3
type A = | "a0" | "a1" | "a2";
export type U = `${A}-${A}`;
export const u: U = "a0-a0";
---- xsect 2,2
interface B0<T> { p0: T; q0: string; }
interface B1<T> { p1: T; q1: string; }
type D0 = B0<number> & B1<number> & { own: boolean };
declare const v0: D0;
type D1 = B0<number> & B1<number> & { own: boolean };
declare const v1: D1;
export const w0_1: D0 = v1;
export const w1_0: D1 = v0;
---- iface 2,2
interface B0<T> { p0: T; q0: string; }
interface B1<T> { p1: T; q1: string; }
interface D0 extends B0<number>, B1<number> { own: boolean }
declare const v0: D0;
interface D1 extends B0<number>, B1<number> { own: boolean }
declare const v1: D1;
export const w0_1: D0 = v1;
export const w1_0: D1 = v0;
```

- ★ `union 3` 은 원소 `3 × 3`, `xsect`·`iface` 는 **D 를 만드는 줄만** 다르고 대입 줄(`w0_1`·`w1_0`)은 한 글자도 같다 — 두 모양에 **같은 관계 검사**를 시킨다.

### (1) ★★★ 문턱 격자 — 깊이와 폭이 벽에 닿는 크기 × 세 판

**언제 쓰나** — 재귀 타입·템플릿 리터럴 유니온을 넣기 전에 **어디서 막히는지**, 그리고 **판을 올리면 문턱이 옮겨 가는지** 볼 때.

```bash
# ts42b-thresh45.sh
#!/usr/bin/env bash
# 문턱 격자 -- 탐침 여덟(문턱 양쪽 한 칸씩) × 판 셋 · 칸은 진단 코드(없으면 OK)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo '{ "compilerOptions": { "target": "es2022", "lib": ["es2022"], "types": [], "strict": true, "noEmit": true }, "files": ["p45.ts"] }' > "$D/tsconfig.json"
rows=("count 999" "count 1000" "spread 48" "spread 49" "union 316" "union 317" "cube 46" "cube 47")
elems() { case $1 in union) echo $(( $2 * $2 )) ;; cube) echo $(( $2 * $2 * $2 )) ;; *) echo - ;; esac; }   # 유니온 원소 수 -- 스크립트가 센다
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
printf '%-12s %-8s %-8s %-8s %s\n' "탐침" "7.0.2" "5.9.3" "4.9.5" "유니온 원소 수"
split=0; all=""
for r in "${rows[@]}"; do
  bash ts42b-gen45.sh $r > "$D/p45.ts" || exit 3
  a=$(cd "$D" && tsc --pretty false -p tsconfig.json 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" --pretty false -p tsconfig.json 2>&1 | codes)
  c=$(cd "$D" && node "$V49" --pretty false -p tsconfig.json 2>&1 | codes)
  case "$a$b$c" in *TS5*) echo "★ 설정 진단(TS5xxx)이 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
  printf '%-12s %-8s %-8s %-8s %s\n' "$r" "${a:-OK}" "${b:-OK}" "${c:-OK}" "$(elems $r)"
  { [ "$a" != "$b" ] || [ "$b" != "$c" ]; } && split=$((split+1)); all="$all|${a:-OK}"
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "세 판이 한 답이 아닌 행 $split / ${#rows[@]}"
```

```text
===== bash ts42b-thresh45.sh (sh exit=0) =====
탐침       7.0.2    5.9.3    4.9.5    유니온 원소 수
count 999    OK       OK       OK       -
count 1000   TS2589   TS2589   TS2589   -
spread 48    OK       OK       OK       -
spread 49    TS2589   TS2589   TS2589   -
union 316    OK       OK       OK       99856
union 317    TS2590   TS2590   TS2590   100489
cube 46      OK       OK       OK       97336
cube 47      TS2590   TS2590   TS2590   103823

세 판이 한 답이 아닌 행 0 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **깊이 둘** — `count`(꼬리 재귀로 길이를 셈)는 **999 OK · 1000 `TS2589`**, `spread`(겹마다 튜플 스프레드)는 **48 OK · 49 `TS2589`**. 25편 5·6절이 7.0.2 에서 잰 문턱과 **같은 자리**다.
- ★★★ **폭 둘** — `union`(`N × N`)은 **316 OK · 317 `TS2590`**, `cube`(`N³`)는 **46 OK · 47 `TS2590`**. 끝 열(스크립트가 센 원소 수)이 `99856`·`97336` 에서 통과, `100489`·`103823` 에서 막혔다 — **N 이 아니라 원소 수**가 같은 선(10만)을 넘을 때 막힌다.
- ★★★ **세 판이 한 답이 아닌 행 `0 / 8`** — 4.9.5 · 5.9.3 · 7.0.2 가 **같은 크기에서** 벽에 닿았다. 문턱은 **타입 시스템의 한도**이고 네이티브 포트가 **옮기지 않았다.**

진단 전문 — 두 벽의 문구.

```text
===== bash ts42b-gen45.sh <count 1000 · cube 47> 를 파일로 받아 tsc --pretty false --noEmit -t es2022 --lib es2022 두 파일 (sh exit=1) =====
===== 소스: count1000.ts =====
type Count<N extends readonly unknown[], Stop extends number> = N["length"] extends Stop ? N : Count<[...N, 1], Stop>;
export type R = Count<[], 1000>;
export const r: R["length"] = 1000;
===== 소스: cube47.ts =====
type A = | "a0" | "a1" | "a2" | "a3" | "a4" | "a5" | "a6" | "a7" | "a8" | "a9" | "a10" | "a11" | "a12" | "a13" | "a14" | "a15" | "a16" | "a17" | "a18" | "a19" | "a20" | "a21" | "a22" | "a23" | "a24" | "a25" | "a26" | "a27" | "a28" | "a29" | "a30" | "a31" | "a32" | "a33" | "a34" | "a35" | "a36" | "a37" | "a38" | "a39" | "a40" | "a41" | "a42" | "a43" | "a44" | "a45" | "a46";
export type U = `${A}${A}${A}`;
export const u: U = "a0a0a0";
===== tsc =====
count1000.ts(2,17): error TS2589: Type instantiation is excessively deep and possibly infinite.
cube47.ts(2,17): error TS2590: Expression produces a union type that is too complex to represent.
```

- ★★ **`TS2589`** 「Type instantiation is excessively deep and possibly infinite.」 · **`TS2590`** 「Expression produces a union type that is too complex to represent.」 — 둘 다 **`(2,17)`**, 즉 **타입 별칭을 쓰는 자리**를 가리킨다.

```text
  벽 두 개 — 무엇을 세다가 막히나 (세 판 같음)

  깊이   인스턴스화가 한 줄로 이어지는 깊이       count 999 / 1000  ·  spread 48 / 49   ─> TS2589
  폭     유니온 하나에 든 원소 수                union 316² / 317²  ·  cube 46³ / 47³  ─> TS2590
         ★ 쌓는 꼴(spread)은 세는 꼴(count)의 스무 배 앞에서 막힌다 — 25편 6절 「무엇을 쌓느냐」
```

비용 — 벽 앞의 크기는 **통과한다** — 그러나 2절이 보이듯 **벽 앞에서 이미 수가 크게 불어나** 있다. 문턱 아래라고 싸다는 뜻이 아니다.

### (2) ★★★ 결정적 칸 — 같은 입력의 `Types`·`Instantiations` 를 두 판에

**언제 쓰나** — 「7.0 이 타입 검사를 **다르게** 하나, **빠르게** 하나」를 가를 때. **시간을 보지 않고** 수만 본다.

```bash
# ts42b-counts45.sh
#!/usr/bin/env bash
# 탐침 열하나 × (7.0.2 · 7.0.2 --checkers 1 · 5.9.3) -- --extendedDiagnostics 의 Types · Instantiations
# 설정은 판 둘에 같은 tsconfig.json(target·lib es2022 · types [] · strict · noEmit) -- 시간 줄은 찍지 않는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo '{ "compilerOptions": { "target": "es2022", "lib": ["es2022"], "types": [], "strict": true, "noEmit": true }, "files": ["p45.ts"] }' > "$D/tsconfig.json"
rows=("base 0" "count 100" "count 400" "spread 20" "spread 40" "union 100" "union 300" "xsect 10,30" "xsect 20,60" "iface 10,30" "iface 20,60")
num() { awk -v k="$1" '$1 == k":" {print $2}' "$2"; }
run() {   # run <이름> <명령...>
  local name=$1; shift
  (cd "$D" && "$@" --pretty false -p tsconfig.json --extendedDiagnostics) > "$D/$name" 2>&1
  if grep -q 'error' "$D/$name"; then echo "★ 진단이 나왔다 -- $name: $(grep error "$D/$name")"; exit 4; fi
}
printf '%-12s | %-17s | %-17s | %-17s | %s\n' "탐침" "7.0.2 T / I" "--checkers 1 T / I" "5.9.3 T / I" "(--checkers 1) − 5.9.3 : T · I"
sameI=0; total=0; tdiffs=""; declare -A I1 I5
for r in "${rows[@]}"; do
  bash ts42b-gen45.sh $r > "$D/p45.ts" || exit 3
  run a tsc; run b tsc --checkers 1; run c node "$OLD"
  ta=$(num Types "$D/a"); ia=$(num Instantiations "$D/a"); tb=$(num Types "$D/b"); ib=$(num Instantiations "$D/b"); tc=$(num Types "$D/c"); ic=$(num Instantiations "$D/c")
  if [ -z "$ta$tb$tc" ] || [ -z "$ia" ] || [ -z "$ib" ] || [ -z "$ic" ]; then echo "★ 수를 못 뽑았다 -- $r"; exit 5; fi
  total=$((total+1)); if [ "$ib" = "$ic" ]; then sameI=$((sameI+1)); fi
  tdiffs="$tdiffs $((tb - tc))"; I1[$r]=$ib; I5[$r]=$ic
  printf '%-12s | %8s / %-6s | %8s / %-6s | %8s / %-6s | %s · %s\n' "$r" "$ta" "$ia" "$tb" "$ib" "$tc" "$ic" "$((tb - tc))" "$((ib - ic))"
done
slope=0; pairs=0
for p in "count 100:count 400" "spread 20:spread 40" "union 100:union 300" "xsect 10,30:xsect 20,60" "iface 10,30:iface 20,60"; do
  s1=${p%%:*} s2=${p#*:}; pairs=$((pairs+1))
  d1=$(( ${I1[$s2]} - ${I1[$s1]} )); d5=$(( ${I5[$s2]} - ${I5[$s1]} ))
  echo "  ${s1%% *} 두 크기 사이 Instantiations 증분 -- --checkers 1 $d1 · 5.9.3 $d5"
  if [ "$d1" = "$d5" ]; then slope=$((slope+1)); fi
done
echo
echo "Instantiations 가 같은 행(--checkers 1 대 5.9.3) $sameI / $total · 두 크기 사이 증분이 같은 꼴 $slope / $pairs · Types 차의 가짓수 $(tr ' ' '\n' <<< "$tdiffs" | sed '/^$/d' | sort -u | wc -l)"
```

```text
===== bash ts42b-counts45.sh (sh exit=0) =====
탐침       | 7.0.2 T / I       | --checkers 1 T / I | 5.9.3 T / I       | (--checkers 1) − 5.9.3 : T · I
base 0       |     6278 / 1998   |     3340 / 1178   |     3299 / 1178   | 41 · 0
count 100    |    12025 / 7868   |     9056 / 7048   |     9015 / 7048   | 41 · 0
count 400    |    89275 / 85418  |    86306 / 84598  |    86265 / 84598  | 41 · 0
spread 20    |     6694 / 2596   |     3751 / 1775   |     3675 / 1741   | 76 · 34
spread 40    |     7463 / 3506   |     4493 / 2685   |     4417 / 2651   | 76 · 34
union 100    |    16582 / 1998   |    13644 / 1178   |    13603 / 1178   | 41 · 0
union 300    |    97182 / 1998   |    94244 / 1178   |    94203 / 1178   | 41 · 0
xsect 10,30  |     6718 / 2298   |     3780 / 1478   |     3739 / 1478   | 41 · 0
xsect 20,60  |     7758 / 3198   |     4820 / 2378   |     4779 / 2378   | 41 · 0
iface 10,30  |     7018 / 2298   |     4080 / 1478   |     4039 / 1478   | 41 · 0
iface 20,60  |     8958 / 3198   |     6020 / 2378   |     5979 / 2378   | 41 · 0
  count 두 크기 사이 Instantiations 증분 -- --checkers 1 77550 · 5.9.3 77550
  spread 두 크기 사이 Instantiations 증분 -- --checkers 1 910 · 5.9.3 910
  union 두 크기 사이 Instantiations 증분 -- --checkers 1 0 · 5.9.3 0
  xsect 두 크기 사이 Instantiations 증분 -- --checkers 1 900 · 5.9.3 900
  iface 두 크기 사이 Instantiations 증분 -- --checkers 1 900 · 5.9.3 900

Instantiations 가 같은 행(--checkers 1 대 5.9.3) 9 / 11 · 두 크기 사이 증분이 같은 꼴 5 / 5 · Types 차의 가짓수 2
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **첫 열(7.0.2 기본)과 셋째 열(5.9.3)은 같은 입력에서도 다르다** — 빈 파일(`base 0`)부터 `Types` `6278` 대 `3299`, `Instantiations` `1998` 대 `1178`. 이대로 읽으면 「7.0 이 일을 **두 배** 한다」는 틀린 결론이 나온다(3절이 까닭).
- ★★★ **둘째 열(`--checkers 1`)과 5.9.3 을 대면 `Instantiations` 가 같은 행 `9 / 11`** — `count`·`union`·`xsect`·`iface` 는 한 글자도 같다. `spread` 두 행만 **`34` 씩** 7.0.2 가 많다 — 그런데 **크기와 무관하게 늘 `34`** 다.
- ★★★ **두 크기 사이의 증분은 `5 / 5` 꼴에서 같다** — `count` `77550` · `spread` `910` · `union` `0` · `xsect`·`iface` `900`. **입력이 커질 때 늘어나는 양**은 두 판이 **정확히 같다.**
- ★★ **`Types` 차는 늘 `41`(`spread` 만 `76`)** — 가짓수 `2`. 크기와 무관한 **상수**다 — 표준 라이브러리 쪽 차이로 읽힌다(그 이상은 가르지 않았다).
- ★★ **`union` 은 `Instantiations` 가 늘지 않는다**(`0`) — 템플릿 리터럴 곱은 **제네릭 인스턴스화가 아니라 유니온 원소**로 불어난다. 불어나는 것은 `Types`(`13644` → `94244`)다.

```text
  7.0 이 바꾸지 않은 것 — 같은 입력, 같은 수 (--checkers 1 대 5.9.3)

                   Instantiations              입력을 키울 때의 증분
  count 100 · 400  같다 · 같다                 77550 = 77550
  spread 20 · 40   +34 · +34 (상수)            910 = 910
  union 100 · 300  같다 · 같다                 0 = 0        ← 유니온은 Types 로 불어난다
  xsect · iface    같다 · 같다                 900 = 900
  ★ 알고리즘이 같다는 증거는 「같은 값」보다 「같은 증분」이 더 강하다 — 상수 차는 증분에서 지워진다
```

비용 — 이 수는 **타입 시스템이 한 일의 양**이지 시간이 아니다. 같은 수를 **얼마나 빨리** 해치웠나는 5절이 따로 잰다.

### (3) ★★★ 7.0.2 가 바꾼 것 하나 — 검사기가 여럿이다

**언제 쓰나** — 7.0.2 의 `--extendedDiagnostics` 수가 5.x 와 안 맞을 때 — 그리고 **`--generateTrace` 가 파일을 몇 개 쓰는지** 볼 때.

```bash
# ts42b-checkers45.sh
#!/usr/bin/env bash
# 바닥 탐침(base) 하나를 7.0.2 의 --checkers 값 넷 · --singleThreaded 로 -- Types · Instantiations · --generateTrace 가 쓴 파일
# 끝 행은 같은 것을 5.9.3 으로
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo '{ "compilerOptions": { "target": "es2022", "lib": ["es2022"], "types": [], "strict": true, "noEmit": true }, "files": ["p45.ts"] }' > "$D/tsconfig.json"
bash ts42b-gen45.sh base 0 > "$D/p45.ts" || exit 3
num() { awk -v k="$1" '$1 == k":" {print $2}' "$D/out"; }
printf '%-22s %-7s %-7s %s\n' "설정" "Types" "Inst." "--generateTrace 가 쓴 파일"
for fl in "(기본)" "--checkers 1" "--checkers 2" "--checkers 4" "--checkers 8" "--singleThreaded" "5.9.3"; do
  case "$fl" in "(기본)") c=(tsc) ;; 5.9.3) c=(node "$OLD") ;; *) read -ra extra <<< "$fl"; c=(tsc "${extra[@]}") ;; esac
  rm -rf "$D/tr"
  (cd "$D" && "${c[@]}" --pretty false -p tsconfig.json --extendedDiagnostics) > "$D/out" 2>&1 || { echo "★ 실패 $fl"; exit 4; }
  (cd "$D" && "${c[@]}" --pretty false -p tsconfig.json --generateTrace tr) > /dev/null 2>&1 || { echo "★ 트레이스 실패 $fl"; exit 4; }
  printf '%-22s %-7s %-7s %s\n' "$fl" "$(num Types)" "$(num Instantiations)" "$(ls "$D/tr" | tr '\n' ' ')"
done
```

```text
===== bash ts42b-checkers45.sh (sh exit=0) =====
설정                 Types   Inst.   --generateTrace 가 쓴 파일
(기본)               6278    1998    legend.json trace.json types_0.json types_1.json types_2.json types_3.json 
--checkers 1           3340    1178    legend.json trace.json types_0.json 
--checkers 2           4702    1594    legend.json trace.json types_0.json types_1.json 
--checkers 4           6278    1998    legend.json trace.json types_0.json types_1.json types_2.json types_3.json 
--checkers 8           8014    2385    legend.json trace.json types_0.json types_1.json types_2.json types_3.json types_4.json types_5.json types_6.json types_7.json 
--singleThreaded       3340    1178    legend.json trace.json types_0.json 
5.9.3                  3299    1178    trace.json types.json 
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **기본과 `--checkers 4` 가 한 글자도 같다** — `6278 / 1998`. 7.0.2 의 기본 검사기 수는 **넷**이다(이 판 · 이 머신 `nproc 24` 에서).
- ★★★ **검사기 수를 늘릴수록 빈 파일의 수가 는다** — 1 `3340` · 2 `4702` · 4 `6278` · 8 `8014`. 표준 라이브러리 타입을 **검사기마다 따로** 만든다고 읽어야 앞뒤가 맞는다.
- ★★ **`--singleThreaded` 는 `--checkers 1` 과 같다** — `3340 / 1178`.
- ★★★ **`--generateTrace` 가 쓴 `types_N.json` 수가 검사기 수와 같다** — 넷이면 `types_0` … `types_3`. 5.9.3 은 **`types.json` 하나**. 트레이스 파일은 **두 판 모두 생긴다** — 이 문서는 그 안을 **읽지 않았다.**

```text
  7.0.2 — 검사기 수가 수를 바꾼다 (빈 파일)

  --checkers 1 (= --singleThreaded)   Types 3340   Inst. 1178   types_0.json
  --checkers 2                        Types 4702   Inst. 1594   types_0 · 1
  --checkers 4 (= 기본)                Types 6278   Inst. 1998   types_0 … 3
  --checkers 8                        Types 8014   Inst. 2385   types_0 … 7
  5.9.3                               Types 3299   Inst. 1178   types.json
```

비용 — **판 사이에 `--extendedDiagnostics` 를 대려면 `--checkers 1` 로 맞춰야** 한다. 안 맞추면 7.0.2 가 **일을 더 하는 것처럼** 보인다.

### (4) ★★ 교차 대 인터페이스 — 수로 가르면

**언제 쓰나** — 「교차(`&`) 대신 `interface … extends` 로 바꾸면 빨라진다」를 **확인해 보고 싶을** 때. ★ 여기는 **수만** 본다 — 시간은 5절.

2절 표의 `xsect`·`iface` 네 행을 옮겨 읽는다(같은 블록이다).

- ★★★ **`Instantiations` 는 두 모양이 같다** — `10,30` 에서 `1478` · `20,60` 에서 `2378`(`--checkers 1`). 이 탐침에서 **인스턴스화 수는 두 모양을 가르지 않는다.**
- ★★★ **`Types` 는 인터페이스 쪽이 더 많다** — `3780` 대 `4080` · `4820` 대 `6020`. 「인터페이스가 **덜** 만든다」는 이 탐침의 수와 **반대 방향**이다.
- ★★ 두 모양 다 **5.9.3 과 증분이 같다**(`900`) — 모양의 차이도 **판이 안 바꿨다.**

```text
  같은 관계 검사 — 두 모양의 계산서 (--checkers 1)

                 Types          Instantiations
  xsect 10,30    3780           1478
  iface 10,30    4080  (더 많다)  1478  (같다)
  xsect 20,60    4820           2378
  iface 20,60    6020  (더 많다)  2378  (같다)
  ★ 「인터페이스가 교차보다 싸다」는 이 두 수로는 서지 않는다 — 시간은 5절에서 따로
```

비용 — **어느 수로 재느냐에 따라 답이 달라진다.** 이 탐침은 **D 끼리 서로 대입**하는 한 가지 쓰임새다 — 다른 쓰임새(깊게 겹친 교차 · 교차 안의 제네릭)는 **던지지 않았다.**

### (5) ★★★ 흔들리는 칸 — 시간 격자(입력 다섯 × 설정 셋 × 7판)

**언제 쓰나** — 「7.0 이 몇 배 빠르다」·「이 수가 검사를 얼마나 늦추나」를 **이 머신에서** 말해야 할 때 — 그리고 **그 말을 어디까지 해도 되나** 정할 때.

```bash
# ts42b-time45.sh
#!/usr/bin/env bash
# 시간 격자 -- 입력 다섯 × 설정 셋 × 7판 · 판을 번갈아 돌린다(k 바깥 · 설정 안쪽)
#   벽시계 ms 는 date +%s%N 의 차 · Check 는 --extendedDiagnostics 의 「Check time」(초)
#   「시간|」 줄은 흔들리는 칸이다 -- 「판정|」 줄만 결론에 쓴다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
N=7
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
inputs=("base 0" "union 150" "union 300" "xsect 20,60" "iface 20,60")
cfgs=("7.0.2" "7.0.2-st" "5.9.3")
for inp in "${inputs[@]}"; do
  d="$D/${inp// /_}"; mkdir -p "$d"
  echo '{ "compilerOptions": { "target": "es2022", "lib": ["es2022"], "types": [], "strict": true, "noEmit": true }, "files": ["p45.ts"] }' > "$d/tsconfig.json"
  bash ts42b-gen45.sh $inp > "$d/p45.ts" || exit 3
done
for ((k = 1; k <= N; k++)); do
  for inp in "${inputs[@]}"; do
    d="$D/${inp// /_}"
    for cf in "${cfgs[@]}"; do
      case $cf in 7.0.2) c=(tsc) ;; 7.0.2-st) c=(tsc --singleThreaded) ;; 5.9.3) c=(node "$OLD") ;; esac
      t0=$(date +%s%N)
      (cd "$d" && "${c[@]}" --pretty false -p tsconfig.json --extendedDiagnostics) > "$d/out" 2>&1 || { echo "★ 실패 $inp $cf"; exit 4; }
      t1=$(date +%s%N)
      echo "$(( (t1 - t0) / 1000000 )) $(awk '$1 == "Check" && $2 == "time:" {sub(/s$/, "", $3); print $3 * 1000}' "$d/out")" >> "$d/$cf.t"
    done
  done
done
stat() { sort -n | awk '{a[NR] = $1} END {printf "%d %d %d", a[int((NR + 1) / 2)], a[1], a[NR]}'; }   # 중앙값 최소 최대
for inp in "${inputs[@]}"; do
  d="$D/${inp// /_}"
  for cf in "${cfgs[@]}"; do
    read -r wm wlo whi <<< "$(cut -d' ' -f1 "$d/$cf.t" | stat)"; read -r cm clo chi <<< "$(cut -d' ' -f2 "$d/$cf.t" | stat)"
    echo "시간| $(printf '%-12s %-9s' "$inp" "$cf") 벽시계 ms 중앙 $wm (최소 $wlo · 최대 $whi) · Check ms 중앙 $cm (최소 $clo · 최대 $chi)"
    eval "W_${cf//[.-]/_}=\"$wm $wlo $whi\""
  done
  read -r a_m a_lo a_hi <<< "$W_7_0_2"; read -r s_m s_lo s_hi <<< "$W_7_0_2_st"; read -r o_m o_lo o_hi <<< "$W_5_9_3"
  echo "시간| $(printf '%-12s' "$inp") 벽시계 중앙값 비 5.9.3 / 7.0.2 = $(awk -v a="$o_m" -v b="$a_m" 'BEGIN {printf "%.1f", a / b}') · 5.9.3 / 7.0.2-st = $(awk -v a="$o_m" -v b="$s_m" 'BEGIN {printf "%.1f", a / b}')"
  echo "판정| $(printf '%-12s' "$inp") 5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): $([ "$o_lo" -gt "$a_hi" ] && [ "$o_lo" -gt "$s_hi" ] && echo 참 || echo 거짓)"
  eval "X_${inp%% *}=\"$a_m $a_lo $a_hi $o_m $o_lo $o_hi\""
done
read -r xa xal xah xo xol xoh <<< "$X_xsect"; read -r ia ial iah io iol ioh <<< "$X_iface"
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then xm=$xa xl=$xal xh=$xah im=$ia il=$ial ih=$iah; else xm=$xo xl=$xol xh=$xoh im=$io il=$iol ih=$ioh; fi
  echo "시간| xsect 대 iface  $v 벽시계 중앙 $xm 대 $im · 범위가 겹치나 $([ "$xl" -le "$ih" ] && [ "$il" -le "$xh" ] && echo 겹친다 || echo 안 겹친다)"
done
echo "N=$N 판 · 입력 ${#inputs[@]} × 설정 ${#cfgs[@]}"
```

```text
===== bash ts42b-time45.sh (sh exit=0) =====
시간| base 0       7.0.2     벽시계 ms 중앙 194 (최소 192 · 최대 224) · Check ms 중앙 19 (최소 17 · 최대 28)
시간| base 0       7.0.2-st  벽시계 ms 중앙 210 (최소 183 · 최대 234) · Check ms 중앙 25 (최소 21 · 최대 34)
시간| base 0       5.9.3     벽시계 ms 중앙 845 (최소 794 · 최대 989) · Check ms 중앙 240 (최소 230 · 최대 280)
시간| base 0       벽시계 중앙값 비 5.9.3 / 7.0.2 = 4.4 · 5.9.3 / 7.0.2-st = 4.0
판정| base 0       5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): 참
시간| union 150    7.0.2     벽시계 ms 중앙 216 (최소 198 · 최대 270) · Check ms 중앙 31 (최소 29 · 최대 39)
시간| union 150    7.0.2-st  벽시계 ms 중앙 234 (최소 210 · 최대 251) · Check ms 중앙 46 (최소 42 · 최대 61)
시간| union 150    5.9.3     벽시계 ms 중앙 860 (최소 809 · 최대 894) · Check ms 중앙 290 (최소 270 · 최대 320)
시간| union 150    벽시계 중앙값 비 5.9.3 / 7.0.2 = 4.0 · 5.9.3 / 7.0.2-st = 3.7
판정| union 150    5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): 참
시간| union 300    7.0.2     벽시계 ms 중앙 292 (최소 283 · 최대 307) · Check ms 중앙 108 (최소 103 · 최대 121)
시간| union 300    7.0.2-st  벽시계 ms 중앙 307 (최소 291 · 최대 343) · Check ms 중앙 118 (최소 109 · 최대 123)
시간| union 300    5.9.3     벽시계 ms 중앙 921 (최소 904 · 최대 1031) · Check ms 중앙 390 (최소 370 · 최대 530)
시간| union 300    벽시계 중앙값 비 5.9.3 / 7.0.2 = 3.2 · 5.9.3 / 7.0.2-st = 3.0
판정| union 300    5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): 참
시간| xsect 20,60  7.0.2     벽시계 ms 중앙 647 (최소 639 · 최대 715) · Check ms 중앙 462 (최소 441 · 최대 514)
시간| xsect 20,60  7.0.2-st  벽시계 ms 중앙 714 (최소 608 · 최대 923) · Check ms 중앙 502 (최소 424 · 최대 576)
시간| xsect 20,60  5.9.3     벽시계 ms 중앙 1882 (최소 1766 · 최대 1996) · Check ms 중앙 1210 (최소 1130 · 최대 1350)
시간| xsect 20,60  벽시계 중앙값 비 5.9.3 / 7.0.2 = 2.9 · 5.9.3 / 7.0.2-st = 2.6
판정| xsect 20,60  5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): 참
시간| iface 20,60  7.0.2     벽시계 ms 중앙 564 (최소 543 · 최대 666) · Check ms 중앙 379 (최소 361 · 최대 463)
시간| iface 20,60  7.0.2-st  벽시계 ms 중앙 589 (최소 539 · 최대 625) · Check ms 중앙 389 (최소 365 · 최대 419)
시간| iface 20,60  5.9.3     벽시계 ms 중앙 1612 (최소 1506 · 최대 1714) · Check ms 중앙 980 (최소 910 · 최대 1040)
시간| iface 20,60  벽시계 중앙값 비 5.9.3 / 7.0.2 = 2.9 · 5.9.3 / 7.0.2-st = 2.7
판정| iface 20,60  5.9.3 의 최소가 7.0.2 두 설정의 최대보다 크다(범위가 안 겹친다): 참
시간| xsect 대 iface  7.0.2 벽시계 중앙 647 대 564 · 범위가 겹치나 겹친다
시간| xsect 대 iface  5.9.3 벽시계 중앙 1882 대 1612 · 범위가 겹치나 안 겹친다
N=7 판 · 입력 5 × 설정 3
```

★★★ **이 블록의 `시간|` 줄은 전부 흔들리는 칸이다** — 다시 돌리면 숫자가 바뀐다. 재대조는 그 줄을 정규화하고 **`판정|` 줄과 마지막 줄만** 대조한다. 아래 해설의 숫자는 **이 한 번의 캡처**에서 읽은 것이다.

그림 해설 — 한 단계에 한 문장.

- ★★★ **`판정|` 다섯 줄이 전부 「참」** — 입력 다섯 모두에서 **5.9.3 의 가장 빠른 판이 7.0.2 두 설정의 가장 느린 판보다 느렸다.** 흔들림보다 격차가 크다 — 이것이 이 문서가 시간에 대해 **주장하는 전부**다.
- ★★ **중앙값의 비**(`시간|` 줄)는 이 캡처에서 **2.6 에서 4.4** 사이였다 — 빈 파일이 가장 크고 관계 검사가 많은 입력이 작았다. ★ **흔들리는 칸이다** — 「7.0 이 3배」라고 **일반화하지 않는다.**
- ★★ **`base 0`(빈 파일)에도 5.9.3 은 수백 ms** 가 든다 — 벽시계에는 **기동**이 들어 있다. 7.0.2 도 `PATH` 의 `tsc` 가 **node 발사대**라 기동이 있다(머리말 블록).
- ★★ **`7.0.2-st`(`--singleThreaded`)와 기본의 차이는 이 입력들에서 작다** — 탐침이 **파일 하나**라 검사기 넷이 나눌 일이 없다. 병렬 이득은 **여러 파일 프로젝트**에서나 물을 수 있고, **재지 않았다.**
- ★★ **교차 대 인터페이스**(끝 두 `시간|` 줄) — 이 캡처에서 중앙값은 두 판 모두 인터페이스 쪽이 낮았고, 범위는 **7.0.2 가 겹치고 5.9.3 은 안 겹쳤다.** ★ 이 문서를 쓰는 동안 앞서 돌린 두 캡처에서는 **둘 다 겹쳤다** — **겹침 여부 자체가 흔들리는 칸**이라 주장하지 않는다(그래서 `판정|` 줄이 아니라 `시간|` 줄로 찍었다).

```text
  시간 격자를 읽는 법 — 무엇을 말해도 되나

  말해도 된다   「이 머신 · 이 입력 다섯 · 7판에서 5.9.3 의 최소 > 7.0.2 의 최대」   판정| 줄 · 재대조에서 같다
  조건을 달아   「이 캡처의 중앙값 비는 2.6 에서 4.4 사이」                               시간| 줄 · 흔들린다
  말하지 않는다  「7.0 은 N배 빠르다」 · 「인터페이스가 교차보다 빠르다」             공식 수치는 출처 확인 못 함 · 겹침이 캡처마다 바뀌었다
```

비용 — 105판 동안 기계가 한 일이다. **신호 대 잡음** — 판 사이의 격차는 `판정|` 줄이 보이듯 **한 설정 안의 최소–최대 폭을 넘었고**, 교차 대 인터페이스의 차이는 **그 폭과 같은 크기**라 겹침 여부가 캡처마다 바뀌었다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  tsc -p tsconfig.json --extendedDiagnostics     Types · Instantiations · Check time 을 찍는다     (2·3·5절)
  tsc … --checkers 1   (7.0.2)                   검사기 하나 — 5.x 와 수를 댈 때                    (2·3절)
  tsc … --singleThreaded   (7.0.2)               --checkers 1 과 같은 수                            (3절)
  tsc … --generateTrace <디렉토리>               trace.json · types*.json 을 쓴다 (7.0.2 는 legend.json 도)  (3절)
  type Count<N, Stop> = N["length"] extends Stop ? N : Count<[...N, 1], Stop>   깊이 탐침          (1절)
  type U = `${A}-${A}`                           폭 탐침 — 원소 N×N                                 (1절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다(세 판 같음).

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `Count<[], 1000>` | `TS2589` | 1절 |
| 스프레드로 쌓는 `A<[…49개]>` | `TS2589` | 1절 |
| 원소 317개 유니온 둘의 `${A}-${A}` | `TS2590` | 1절 |
| 원소 47개 유니온의 `${A}${A}${A}` | `TS2590` | 1절 |

**규칙 불릿**

- ★★★ **`Types`·`Instantiations` 는 결정적이다 — 주장은 여기 위에** · 시간은 판 격자 × 여러 판의 중앙값·범위로만(2·5절).
- ★★★ **7.0.2 와 5.x 의 수를 대려면 `--checkers 1`** — 기본(넷)은 표준 라이브러리 타입을 검사기마다 만든다(3절).
- ★★★ **문턱(`TS2589`·`TS2590`)은 세 판이 같다** — 네이티브 포트가 옮기지 않았다(1절).
- ★★ **깊이는 `Instantiations` 로, 폭은 `Types` 로 불어난다** — `union` 은 인스턴스화 증분이 `0` 이었다(2절).

## 어디서 틀리나

- ★★★ 「**7.0 은 N배 빠르다**」 — 이 문서가 말할 수 있는 것은 **이 머신 · 이 입력 · 7판에서 범위가 안 겹쳤다**뿐이다. 배수는 흔들리고 공식 수치는 **출처를 확인하지 못했다**(5절).
- ★★★ 「**7.0.2 의 `--extendedDiagnostics` 가 5.x 보다 크니 일을 더 한다**」 — 기본 검사기 **넷**이 수를 부풀린다. `--checkers 1` 이면 `Instantiations` 가 같다(2·3절).
- ★★★ 「**네이티브 포트가 한도를 풀었다**」 — `TS2589`·`TS2590` 문턱이 **세 판 같다**(1절).
- ★★★ 「**인터페이스가 교차보다 싸다**」 — 이 탐침에서 `Instantiations` 는 **같고** `Types` 는 **인터페이스가 많고** 시간은 **겹침 여부부터 캡처마다 바뀌었다**(4·5절). 다른 쓰임새는 던지지 않았다.
- ★★ 「**한 번 재 보니 이쪽이 빨랐다**」 — 한 판의 절댓값은 근거가 아니다(규칙 24). 교차 대 인터페이스의 중앙값 차는 **흔들림과 같은 크기**였다(5절).
- ★★ 「**문턱 아래면 싸다**」 — `count 400` 도 `Instantiations` 가 `84598` 이다. 벽 앞에서 **이미 불어나 있다**(2절).
- ★ 「**`--generateTrace` 는 파일 두 개를 쓴다**」 — 7.0.2 는 검사기 수만큼 `types_N.json` 과 `legend.json` 을 쓴다(3절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어(TS 타입 시스템)** | 재귀 조건부 · 템플릿 리터럴 유니온이 불어나는 **모양** | 2절 — 증분이 두 판 같다 |
| **★★★ 타입 시스템의 한도(판 공통)** | `TS2589` 깊이 · `TS2590` 원소 수 | 1절 — `0 / 8` |
| **★★★ 7.0.2 의 구현** | 검사기 여럿(기본 넷) · 수가 `--checkers` 에 매인다 · 트레이스 파일 수 | 3절 |
| **★ 판 사이 상수** | `Types` 차 `41`·`76` · `spread` 의 `Instantiations` `+34` | 2절 — 크기와 무관 |
| **★ 흔들리는 관찰** | 시간 · 중앙값의 비 · 교차 대 인터페이스의 시간 | 5절 — `시간\|` |
| **★ 결론으로 쓴 관찰** | 5.9.3 최소 > 7.0.2 최대 (입력 다섯) | 5절 — `판정\|` |
| **출처 확인 못 함** | 공식 「N배」 수치 | 외부 문서를 열지 않았다 |
| **안 잰 것** | 메모리 · 여러 파일 병렬 · 실제 코드베이스 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`--extendedDiagnostics` 의 `Types`·`Instantiations` 로 전후를 댄다** — 결정적이다 | 한 번 잰 `Check time` 으로 전후를 대기 — 흔들린다 |
| ★★★ **판 사이를 댈 때 `--checkers 1`** | 7.0.2 기본의 수를 5.x 와 그대로 대기 — 부풀어 있다(3절) |
| ★★ **스프레드로 쌓는 재귀를 줄인다** — 문턱이 스무 배 앞이다(1절 · 25편 6절) | 꼬리 재귀로만 바꾸면 된다고 믿기 — 25편 6절이 반례를 쟀다 |
| ★★ **템플릿 리터럴 곱은 원소 수를 먼저 센다** — `N×N`·`N³` 가 10만을 넘기 전에 | 「리터럴 몇 개쯤이야」 — 47개의 세제곱에서 막혔다 |
| ★ 교차 대 인터페이스는 **자기 코드에서 수와 여러 판 시간으로** 잰다 | 소문으로 고르기 — 이 탐침에서는 수가 반대 방향이었다(4절) |

## 핵심 문장

1. **`Types`·`Instantiations` 는 결정적이고 시간은 흔들린다** — 주장은 앞쪽에 세우고, 시간은 판 격자와 7판 중앙값·범위로만 말한다.
2. **네이티브 포트는 타입 시스템의 계산을 바꾸지 않았다** — `--checkers 1` 이면 `Instantiations` 같은 행 `9 / 11`, 입력을 키울 때의 증분은 `5 / 5` 꼴에서 같다.
3. **7.0.2 는 검사기를 기본 넷 돌려 수를 부풀린다** — 빈 파일의 `Types` 가 `3340` 에서 `6278` 로, 트레이스 파일도 검사기 수만큼 생긴다.
4. **깊이와 폭의 벽은 세 판이 같은 크기에 있다** — `count` 1000 · `spread` 49 · 원소 10만을 넘는 유니온.
5. **이 머신에서 5.9.3 의 가장 빠른 판은 7.0.2 의 가장 느린 판보다 느렸다** — 입력 다섯 모두. 배수는 흔들리고, 공식 수치는 출처를 확인하지 못했다.

## 관련 자료

- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) 5·6절 — ★★★ **README 의 선행.** 7.0.2 의 `TS2589` 문턱과 「무엇을 쌓느냐」. **거기서 멈춘 「시간」을 여기서 잰다.**
- [**27번 주제** — 템플릿 리터럴 타입](../27-template-literal-types/) — 1절 폭 탐침의 문법.
- [**10번 주제** — 교차 타입](../10-intersection-types/) · [**08번 주제** — `interface` 대 `type`](../08-interface-vs-type/) — 4절이 견준 두 모양.
- [**43번 주제**](../43-remaining-tsconfig-choices/) · [**44번 주제**](../44-project-references-and-declaration-emit/) — `incremental`·`tsc -b` 는 **무엇을 다시 하나**만 쟀다. 시간은 여기뿐이다.
- 가이드 [`reference/study-note-guide.md`](../../../../../../reference/study-note-guide.md) §2-1 **규칙 24** — 「한 판에서 잰 절댓값은 근거가 아니다」.

## 용어 풀이

> **`Types`** — 이번 검사에서 만든 타입 객체 수. 같은 입력·판·검사기 수면 같다.\
> 예: 2절 `union 300` 의 `94244`.

> **`Instantiations`** — 제네릭 타입·별칭을 인자로 채워 새로 만든 횟수. 깊은 재귀가 이것을 불린다.\
> 예: 2절 `count 400` 의 `84598`.

> **`TS2589`** — 「Type instantiation is excessively deep and possibly infinite.」 — 인스턴스화 깊이의 벽.\
> 예: 1절 `count 1000`.

> **`TS2590`** — 「Expression produces a union type that is too complex to represent.」 — 유니온 원소 수의 벽.\
> 예: 1절 `union 317` · `cube 47`.

> **검사기(checker) · `--checkers`** — 7.0.2 가 타입 검사를 나눠 맡기는 단위와 그 수. 기본 넷 · `--singleThreaded` 는 하나.\
> 예: 3절.

> **`--generateTrace`** — 검사 과정의 이벤트 트레이스와 타입 목록을 파일로 쓴다. 7.0.2 는 검사기마다 `types_N.json`.\
> 예: 3절 끝 열.

> **판 격자(규칙 24)** — 한 판의 절댓값 대신 판 × 입력 × 되풀이를 돌려 **움직인 칸과 안 움직인 칸**을 가르는 것.\
> 예: 5절.

## 더 들어가면

- **트레이스 파일 읽기** — `trace.json` 을 브라우저 성능 도구에 올려 어느 타입이 오래 걸렸나 보는 길. **파일이 생기는 것까지만** 확인했다.
- **여러 파일 프로젝트의 병렬 이득** — 검사기 넷이 **파일을 나눠 가질 때** 시간이 어떻게 되나. 탐침이 한 파일이라 **재지 않았다.**
- **메모리** — `--extendedDiagnostics` 가 `Memory used` 를 찍지만 **흔들리는 칸이라 싣지 않았다.**
