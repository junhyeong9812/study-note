# ts/syntax/39 — `strict` 묶음 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물은 `tsc` **7.0.2** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 「탐침 격자」(탐침 아홉 × 설정 넷 × 세 판)이다.** `--showConfig` 가 안 열린 판에서는 **`--help` 창으로 바꿔** 물었다(제5의 상태).\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **5.9.3 만** 하위 아홉으로 펼친다 · 7.0.2 와 4.9.5 는 **`strict` 한 키** · `false` 는 세 판 모두 `strict` 한 키

**출력**

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

**왜 그런가**

- ★★★ `--showConfig` 가 `strict` 를 **펼쳐 적는 것은 5.9.3 의 성질**이다 — 7.0.2 에서는 「무엇이 켜졌나」를 이 도구로 알 수 없다.
- ★★ 그래서 같은 질문을 `--help --all` 로도 물었고(7번), 결론은 **탐침 격자**(2·3번)에 세웠다.

### 2. ★★★ a `noImplicitAny` `TS7006` · b `noImplicitThis` `TS2683` · c `strictNullChecks` `TS2322` · d `strictFunctionTypes` `TS2322` · e `strictBindCallApply` `TS2345` · f `strictPropertyInitialization` `TS2564` · g `strictBuiltinIteratorReturn` `TS2322` · h `useUnknownInCatchVariables` `TS18046` · i `alwaysStrict` `TS1212` — 「키 없음」은 7.0.2 **아홉** · 5.9.3·4.9.5 **0**

**출력**

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

**왜 그런가**

- ★★★ 7.0.2 는 `strict` 키가 없으면 **켜진 것과 같다** — 「키없음」 열이 `true` 열과 칸마다 같다. 5.9.3·4.9.5 는 **꺼진 것과 같다**(「키없음」 열이 전부 OK).
- ★★ 탐침 하나에 난 코드가 곧 「그 하위 플래그가 켜졌다」의 표시다 — 타입의 모양은 묻지 않았다.
- ★ 마지막 줄 — 7.0.2 와 5.9.3 이 갈린 칸 **`11 / 36`**, 5.9.3 과 4.9.5 가 갈린 칸 **`2 / 36`**. 스크립트는 칸에 `TS5112` 가 들거나 모든 칸이 같았으면 멈췄다.

### 3. ★★★ `false` — 여덟은 OK, **`pr39i` 만 `TS1212`** · `true+끔` — **그 탐침만 OK**, 단 **`pr39i` 는 `TS5108`** · 4.9.5 — `pr39g` 가 `true` 에서 **OK**, `true+끔` 에서 **`TS5023`**

**출력** — 2번의 격자 블록 `false`·`true+끔` 열.

**왜 그런가**

- ★★★ 하위 플래그 `false` 는 묶음 `true` 보다 **우선한다** — 그 탐침만 조용해졌다.
- ★★★ 7.0.2 의 `alwaysStrict` 는 `strict: false` 로 **안 꺼지고**, `alwaysStrict: false` 는 **제거된 값**(`TS5108`)이다 — 5번이 방출물로 확인한다.
- ★★ 4.9.5 에는 `strictBuiltinIteratorReturn` 이 **없다** — `strict: true` 로도 안 켜지고, 이름을 적으면 `TS5023`(모르는 옵션).

### 4. ★★★ 7.0.2 — **`TS2322`**(`pr39c`) + **`TS1212`**(`pr39i`) · `(exit 1)` · 5.9.3 — **진단 0줄** · `(exit 0)`

**출력**

```ts
// pr39c.ts
let s: string = null;
export {};
```

```ts
// pr39i.ts
var package = 1;
```

```text
===== tsc --pretty false --noEmit pr39c.ts pr39i.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
pr39c.ts(1,5): error TS2322: Type 'null' is not assignable to type 'string'.
pr39i.ts(1,5): error TS1212: Identifier expected. 'package' is a reserved word in strict mode.
(exit 1)
---- 5.9.3
(exit 0)
```

**왜 그런가**

- ★★★ 설정 파일이 **없어도** 7.0.2 의 기본값은 `strict: true` 와 같다 — `strictNullChecks` 와 엄격 모드가 켜져 있다.
- ★★ 5.9.3 은 같은 명령이 **아무것도 안 잡는다.** 「`tsc a.ts` 로 확인했다」는 판을 적어야 뜻이 있다.
- ★ 위쪽에 `tsconfig.json` 이 있었다면 7.0.2 는 `TS5112` 로 거부했다(35편 6절).

### 5. ★★★ 7.0.2 — **`TS1212`** + 첫 줄 **`"use strict";`** · 5.9.3 — **0줄** + `"use strict"` **없음** · `--alwaysStrict false` — **`TS5108`**

**출력**

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

**왜 그런가**

- ★★★ 7.0.2 에서 `alwaysStrict` 는 `strict` 묶음 **밖**이다 — 끄는 값 자체가 없다(「Option 'alwaysStrict=false' has been removed.」).
- ★★ 5.9.3 은 레퍼런스의 「Default: `true` if `strict` is enabled; `false` otherwise」 그대로다 — `strict: false` 로 꺼졌다.
- ★ 7.0.2 방출은 진단이 있어도 돌았다 — `(exit 2)`(02편 1절).

### 6. ★★★ 혼자서 안 되는 셋 — `strictPropertyInitialization` **`TS5052`**(설정 에러) · `strictBuiltinIteratorReturn` **0건** · (`strictBindCallApply` 는 21행을 **못 낸다**) · 합 **11** ≠ 한 번에 **14**

**출력**

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

**왜 그런가**

- ★★★ `strictPropertyInitialization` 은 **`strictNullChecks` 를 전제**로 한다 — 없으면 설정 진단 `TS5052`. 둘을 같이 켜야 23·24행 `TS2564`.
- ★★★ `strictBuiltinIteratorReturn` 혼자는 `value` 를 `undefined` 로 만들지만 **`strictNullChecks` 가 꺼져 있으면** `undefined` 가 `number` 에 들어간다 — 0건. 같이 켜야 30행.
- ★★ 21행(`apply` 의 튜플)은 `strictBindCallApply` + `strictFunctionTypes` **짝**에서만 났다. 35행은 `strictNullChecks` 유무로 **`TS2339` ↔ `TS18046`** 코드가 바뀐다.
- ★★ 그래서 하나씩 켠 합(11 — 그중 하나는 설정 진단)과 한 번에 켠 14 가 **다르다.** 두 판의 수는 **행마다 같았다.**

### 7. ★★★ **도움말 문구가 실제와 다를 수 있기 때문** — 4.9.5 도움말은 `useUnknownInCatchVariables` 를 「default: false」(`strict` 무관)로 적는데, 탐침은 **`strict: true` 에서 `TS18046`**

**출력**

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

**왜 그런가**

- ★★★ 4.9.5 의 그 줄만 「unless `strict` is set」이 **빠져 있다** — 2번 격자의 4.9.5 `pr39h` `true` 열이 `TS18046` 이라 **`strict` 가 켠다.** 문구가 틀렸다.
- ★★ README 머리말의 「`tsc --help --all` 이 이미 제거된 옵션을 싣는다」와 같은 집안 — **옵션의 성질은 던져서** 확인한다.
- ★ 도움말 창에서도 쓸모 있는 것은 **이름 목록**이다 — `strictBuiltinIteratorReturn` 이 4.9.5 → 5.9.3 사이에 들어온 것이 `comm` 줄로 보인다.

### 8. ★★★ **여덟** — 빠진 `alwaysStrict` 는 **늘 켜져 있고 끌 수 없다**(`strict: false` 로도 `TS1212`·`"use strict"` · `false` 는 `TS5108`)

- ★★ 3번 `false` 열의 `pr39i` 가 `TS1212`, `true+끔` 열이 `TS5108` — 5번의 방출물에 `"use strict";`.
- ★★ 레퍼런스의 Enables 목록은 **5.9.3 의 `--showConfig`(아홉)** 와 맞는다 — 7.0.2 와는 한 칸 어긋난다.

### 9. ★★★ **`strictNullChecks` 를 축으로** — 그것 없이는 `strictPropertyInitialization` 이 **설정 에러**, `strictBuiltinIteratorReturn` 이 **0건**, `useUnknownInCatchVariables` 가 **다른 코드**를 낸다

- ★★ 「진단이 적은 것부터」만 따르면 `strictPropertyInitialization`(혼자 1건 — 그것도 `TS5052`)이나 `strictBuiltinIteratorReturn`(0건)을 **먼저 켜서 끝났다고** 착각한다.
- ★★ 혼자 성립하는 넷(`strictFunctionTypes` 1 · `strictBindCallApply` 1 · `noImplicitThis` 2 · `noImplicitAny` 3)을 먼저, `strictNullChecks`(2) 다음, 그 위에서 기대는 셋 — 이것은 **설계 권고**이고 수는 **탐침 한 장**의 것이다.
- ★ 맞물린 진단(21행)은 짝을 다 켠 뒤에야 나온다 — 마지막에 `strict: true` 로 한 번 더 던져 **남은 차이**를 본다.

### 10. ★★ 02편 머리말 「7.0 의 **`strict` 기본 `true`**」 · 02편 7절 **`TS5108`(제거된 값)** — `target=ES5`·`moduleResolution=node10` 과 같은 코드 · 35편 6절 **`TS5112`**

- ★★ [**02번 주제**](../02-type-checking-vs-emit/) — 4번은 그 문장을 **설정 파일 없는 칸**에서 다시 확인했다. 02편 7절은 「파일을 직접 주면 `tsconfig.json` 을 무시한다」고 적었는데, 7.0.2 는 **위쪽에 설정이 있으면 거부**한다(35편 6절) — 그래서 4번은 **설정이 없는** 디렉토리에서 던졌다.
- ★★ `TS5108` — 옵션 이름은 있고 **그 값이** 없어졌다. `TS5102`(옵션째 없어짐)와 다르다.
- ★★ [**35번 주제**](../35-module-resolution/) 6절 — `TS5112`. 칸마다 디렉토리를 따로 두고 스크립트가 칸의 `TS5112` 를 검사한 까닭이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `"$NODE20" --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `v20.19.6` · `Python 3.12.3` |
| ★★ `--showConfig` | `bash ts38b-show39.sh` — 두 설정 × 세 판 | **5.9.3 만** 펼친다 |
| ★★ `--help` 기본값 문구 | `bash ts38b-help39.sh` — 세 판 | 7.0.2 `alwaysStrict` 무조건 · 4.9.5 `useUnknown…` 「false」 |
| ★★★ 탐침 격자 | `bash ts38b-grid39.sh` — 108칸, 칸마다 디렉토리 | 7.0.2↔5.9.3 **`11 / 36`** · 5.9.3↔4.9.5 **`2 / 36`** |
| ★★★ 설정 없이 | `--noEmit pr39c.ts pr39i.ts` × 두 판 | 7.0.2 `TS2322`·`TS1212` · 5.9.3 0줄 |
| ★★★ `alwaysStrict` | 방출 × 두 판 · `--alwaysStrict false` | `"use strict"` 유무 · `TS5108` |
| ★★ 단계표 | `bash ts38b-stage39.sh` — 열두 행 × 두 판 + 한 번에 | 합 11 ≠ 14 · `TS5052` · 0건 · 코드 바뀜 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **「키 없음」의 뜻**(2·4번) · **`alwaysStrict` 가 묶음 밖인 것**(3·5번) — 이미 판마다 달랐다.
- ★★ **`--showConfig` 가 펼치나 · `--help` 문구**(1·7번) — 도구의 성질이 판에 매였다.
- ★ **맞물린 진단**(6번 21·30·35행) — 이 판들에서 두 판이 같았다.

**안 돌려 본 것**

- ★★ **6.x 판** — 이 머신에 없다. 레퍼런스가 「6.0 에서 바뀐」 기본값을 적지만 **확인하지 못했다.**
- ★ **검사 시간** · **실제 코드베이스의 진단 분포** — 재지 않았다.
