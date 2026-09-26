# ts/syntax/45 — 타입 수준 성능 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 수·진단·시간은 `tsc` **7.0.2** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체는 규칙 24(판 격자)다 — 결정적 칸(`Types`·`Instantiations`·문턱) 위에만 주장을 세우고, 시간은 7판 중앙값·범위로만.** 7.0.2 기본의 수는 검사기 넷이 부풀려 **`--checkers 1` 로 창을 바꿔** 물었다(제5의 상태).\
> ★★★ **5번의 `시간|` 줄은 흔들리는 칸이다** — 다시 돌리면 숫자가 바뀐다. 결론은 `판정|` 줄에서만 읽는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 둘째 칸마다 막힌다 — `count 1000`·`spread 49` **`TS2589`** · `union 317`·`cube 47` **`TS2590`** — **세 판이 한 답**(`0 / 8`), 문턱이 **안 옮겨 간다**

**출력**

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

**왜 그런가**

- ★★★ 문턱은 **타입 시스템의 한도**다 — 4.9.5(JS) · 5.9.3(JS) · 7.0.2(네이티브)가 같은 크기에서 벽에 닿았다.
- ★★ 깊이는 **쌓는 꼴**(`spread`)이 **세는 꼴**(`count`)보다 스무 배 앞에서 막힌다 — 25편 6절의 「무엇을 쌓느냐」.

### 2. ★★★ 기본은 **다르다**(`6278 / 1998` 대 `3299 / 1178`) · `--checkers 1` 이면 `Instantiations` **같다**(`1178`) — 증분도 **같다**(`count` `77550` · `union` `0`)

**출력**

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

**왜 그런가**

- ★★★ `Instantiations` 가 같은 행 **`9 / 11`**, 두 크기 사이 증분이 같은 꼴 **`5 / 5`** — 같은 입력에서 **같은 계산**을 했다.
- ★★ `Types` 는 늘 **상수 `41`**(`spread` 만 `76`) 차 — 크기와 무관하다.
- ★★ 기본이 다른 까닭은 3번 — 검사기 넷.

### 3. ★★★ 검사기가 늘수록 **`Types` 가 는다**(1 `3340` · 2 `4702` · 4 `6278` · 8 `8014`) · 기본 = `--checkers 4` · `--singleThreaded` = `--checkers 1` · 트레이스는 **`types_N.json` 이 검사기 수만큼** + `legend.json` · 5.9.3 은 `trace.json`·`types.json` 둘

**출력**

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

**왜 그런가**

- ★★★ 7.0.2 는 **검사기마다** 표준 라이브러리 타입을 만든다고 읽어야 수가 맞는다 — 빈 파일인데 검사기를 늘릴수록 는다.
- ★★ 이것이 7.0 이 **바꾼 것** 하나다 — 계산을 **여러 기계가 나눠** 한다. 수가 바뀐 것은 **계산이 달라서가 아니라 계산하는 기계가 여럿이라서**다(2번과 같이 읽는다).

### 4. ★★★ `Instantiations` **같다**(`2378` · `2378`) · `Types` 는 **인터페이스 쪽이 많다**(`4820` 대 `6020`)

**출력** — 2번과 같은 블록이다. 읽을 곳은 `xsect`·`iface` 네 행(`10,30` 도 같은 방향 — `1478` 같음 · `3780` 대 `4080`).

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

**왜 그런가**

- ★★★ 이 탐침은 **D 끼리 서로 대입**한다 — 관계 검사가 제네릭 인스턴스화를 **두 모양에서 같은 수**만큼 부른다.
- ★★ 「인터페이스가 **덜** 만든다」는 이 탐침의 `Types` 와 **반대 방향**이다. 다른 쓰임새는 던지지 않았다.

### 5. ★★★ 「5.9.3 의 최소 > 7.0.2 두 설정의 최대」는 **다섯 입력 모두 참** · 교차 대 인터페이스의 범위는 **캡처마다 바뀌었다**(이 캡처 — 7.0.2 겹침 · 5.9.3 안 겹침)

**출력**

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

**왜 그런가**

- ★★★ **`판정|` 다섯 줄**이 재대조에서도 같았다 — 판 사이 격차가 한 설정 안의 흔들림을 **넘는다.**
- ★★★ 교차 대 인터페이스의 차이는 흔들림과 **같은 크기**다 — 이 문서를 쓰는 동안 앞선 두 캡처는 **둘 다 겹침**이었다. 그래서 그 줄은 `시간|`(흔들리는 칸)으로 찍었다.
- ★★ 중앙값의 비는 이 캡처에서 **2.6 에서 4.4** — 흔들리는 칸이다.

### 6. ★★★ 결론은 **`판정|` 줄**(범위가 안 겹치나 — 참/거짓) · 쓰지 않는 것은 **`시간|` 줄 전부**(ms · 중앙값의 비 · 교차 대 인터페이스의 겹침) — 결정적인 칸에만 주장을 세우기 때문이다

- ★★ 한 판의 절댓값은 근거가 아니다(규칙 24). 7판의 **범위가 안 겹칠 때만** 「느리다·빠르다」의 방향을 말하고, 배수는 조건을 달아 적는다. 공식 「N배」는 **출처를 확인하지 못했다.**
- ★ 그래서 재대조는 `시간|` 줄을 정규화하고 **`판정|` 줄과 마지막 줄만** 대조한다.

### 7. ★★★ **입력을 키울 때의 증분**을 본다 — `spread` 는 값이 `+34` 로 다르지만 **크기와 무관한 상수**라 증분(`910` = `910`)에서 지워진다

- ★★ 알고리즘이 다르면 **크기에 따라** 차이가 벌어져야 한다. 차이가 **늘 같은 수**면 그것은 계산의 모양이 아니라 **고정된 밑바닥**(표준 라이브러리 · 초기화)의 차이로 읽힌다 — 그 밑바닥이 무엇인지는 **가르지 않았다.**

### 8. ★★★ **`--checkers 1`**(또는 `--singleThreaded`)로 맞춘다 · 안 맞추면 「**7.0 이 일을 두 배 가까이 한다**」는 틀린 결론이 나온다

- ★★ 기본 검사기 넷이 표준 라이브러리 타입을 **넷이 따로** 만든다(3번). 같은 계산이 **네 번 세어진** 것이지 **다른 계산**이 아니다(2번 — `--checkers 1` 이면 `Instantiations` 같음).

### 9. ★★ **끝 열(스크립트가 센 유니온 원소 수)** — `99856`·`97336` 통과 · `100489`·`103823` 막힘 — 둘 다 **원소 10만**을 넘을 때 · `union` 이 커질 때 늘어나는 것은 **`Types`**(`Instantiations` 증분 `0`)

- ★★ N 으로 보면 317 대 47 로 다르지만 **원소 수**로 보면 같은 선이다. 2번 블록의 `union 100` → `300` 에서 `Types` 가 `13644` → `94244`, `Instantiations` 는 그대로.

### 10. ★★ 25편 **5절**(`Count` 999 OK · 1000 `TS2589`)과 **6절**(A 꼴 48 OK · 49 `TS2589`) · 채운 방식 — **판을 셋으로 늘려** 문턱을 다시 던지고, 시간은 **판 격자 × 7판**으로만 재서 **범위가 안 겹친 칸**만 결론으로

- ★★ [**25번 주제**](../25-infer-and-recursive-conditional-types/)는 7.0.2 한 판에서 문턱을 쟀다. 여기서 4.9.5·5.9.3 도 **같은 자리**라는 것이 더해졌다 — 문턱이 **구현이 아니라 타입 시스템 한도**임을 판 격자가 보인다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 · 머신 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"` · `node` · `nproc` · CPU · `PATH` 의 `tsc` | `7.0.2` · `5.9.3` · `4.9.5` · `v18.19.1` · `24` · i7-13700HX · node 발사대 |
| ★★★ 문턱 | `bash ts42b-thresh45.sh` — 여덟 × 세 판 | 세 판이 한 답이 아닌 행 **`0 / 8`** |
| ★★★ 수 | `bash ts42b-counts45.sh` — 열하나 × 셋 | `Instantiations` 같은 행 **`9 / 11`** · 증분 같은 꼴 **`5 / 5`** |
| ★★★ 검사기 | `bash ts42b-checkers45.sh` — 일곱 판 | `Types` 가 검사기 수를 따라간다 · `types_N.json` 수 = 검사기 수 |
| ★★★ 시간 | `bash ts42b-time45.sh` — 다섯 × 셋 × 7판 | `판정\|` 다섯 줄 **참** · `시간\|` 는 흔들림 |
| ★ 가짜 격자 자기검사 | 가짜 옵션을 끼운 판 | 문턱·수 스크립트가 **`exit 4`** 로 멈췄다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **검사기 기본값과 그것이 수를 바꾸는 것**(3·8번) — 7.0.2 의 구현이다.
- ★★ **`Types` 상수 차 `41`·`76` · `spread` 의 `+34`**(2·7번) — 판 사이 밑바닥 차이다.
- ★ **문턱**(1번) — 세 판이 같았다. 한도가 바뀌면 여기가 먼저 움직인다.

**안 돌려 본 것**

- ★★ **여러 파일 프로젝트의 병렬 이득** · **메모리** — 재지 않았다.
- ★ **트레이스 파일의 안** — 생기는 것까지만 확인했다.
- ★ **공식 「N배」 수치** — 출처를 확인하지 못했다(외부 네트워크 금지).
