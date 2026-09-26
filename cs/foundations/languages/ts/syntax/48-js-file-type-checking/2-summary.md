# ts/syntax/48 — JS 파일 타입 검사 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `allowJs`](https://www.typescriptlang.org/tsconfig/#allowJs) · [TSConfig — `checkJs`](https://www.typescriptlang.org/tsconfig/#checkJs) · [Handbook — JSDoc Reference](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html) · [typescript-go 의 변경 목록](https://github.com/microsoft/typescript-go).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** 특히 **「7.0 에서 JSDoc 해석이 TS 문법과 정렬되며 사라진 특례」의 공식 목록은 출처 확인 못 함**이다. 이 문서의 목록은 **5.9.3 과 7.0.2 가 갈린 칸**으로만 세웠다(2절).
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3** 을 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`**.

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

> ★★★ **본체 창 선언 — 이 주제의 본체는 둘이다.** ① 「**점진 도입 격자**」(JS 탐침 아홉 × 설정 셋 × 두 판 — 진단 코드) · ② 「**JSDoc 해석 판 격자**」(JSDoc 꼴 스물셋 × 5.9.3/7.0.2 — `/** @type {null} */ const p = …` 로 그 자리의 타입을 뽑는다). 둘째 기둥은 **방출 창**(`.d.ts` · `.js`)이다(3절).
> ★★★ **제5의 상태 — JS 파일은 검사를 안 켜면 「진단 0」이 곧 「안 물었다」다.** 격자의 A 열(`allowJs` 만)이 그렇다 — 아홉 탐침 중 여덟이 OK 인데 **여덟 모두 B 열(`checkJs`)에서 진단을 낸다.** 침묵을 **B·C 열로 바꿔 물었다.**
> ★★ **48 은 36 에서 온다** — README 는 [**36번 주제**](../36-type-only-imports-and-exports/)(타입 전용 import·방출)를 선행으로 적었다. 여기서는 그쪽의 방출 규칙을 다시 재지 않고 **JS 파일이 방출에 들어갈 때**(3절)만 본다. JSDoc 없는 매개변수는 [**42번 주제**](../42-implicit-any-and-catch-variables/)의 `noImplicitAny` 가, JS 에서 `.d.ts` 를 뽑는 것은 [**37번 주제**](../37-writing-declaration-files/)가 이어받는다.
> ★★ 격자 스크립트 둘은 **설정 진단이 칸에 들면 멈추고**(`exit 4`), 한쪽은 **모든 칸이 같은 값이면**, 다른 쪽은 **전부 같거나 전부 갈리면** 멈춘다. 가짜 옵션을 끼운 판으로 실제로 멈추는지 돌렸다(1절 끝).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다. 격자 칸의 파일 이름은 늘 `c.js` 다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드 · `(행,열)` · 메시지 속 타입 글자 · `.d.ts` 글자 | 같은 입력·같은 판이면 같다 |
| **안 흔들린다** | ★★★ 두 격자의 칸과 마지막 줄의 **수** | 스크립트가 센다 |
| **판에 매인다** | ★ 종료 코드 — 진단 있는 `--noEmit` 이 7.0.2 `1` · 5.9.3 `2` | 격자는 **진단 코드로** 갈랐다 |
| **판에 매인다** | ★★★ **`strict` 를 안 적었을 때의 기본값** — 7.0.2 는 켬, 5.9.3 은 끔(1절 끝) | 격자는 **`"strict": true` 를 적어** 이 차이를 지웠다 |
| **★ 부적용 — `node` 로 값 보기** | 탐침이 묻는 것은 「검사기가 무엇이라고 읽나」다 — 3절 한 곳에서만 방출물을 돌렸다 | — |
| **출처 확인 못 함** | 7.0 의 공식 변경 목록 · 각 특례가 「의도된 제거」인지 | 외부 문서를 열지 않았다 |

## 한눈에 — 쉽게 말하면

JS 파일의 타입 검사는 「세관 검사를 켜는 스위치가 여러 개인 공항」이다. `allowJs` 는 **JS 짐도 통관장에 들여보내기**만 하고 검사는 안 한다. `checkJs` 는 **모든 JS 짐을 연다.** 파일 첫 줄의 `// @ts-check` 는 **그 짐 하나만 연다**, `// @ts-nocheck` 는 **그 짐만 안 연다.** 짐에 붙은 **꼬리표**(JSDoc)가 곧 신고서다. 그런데 7.0 에서 세관이 **꼬리표 읽는 법을 TS 문법에 맞춰** 바꿨다 — 옛 Closure 식 꼬리표 몇 종은 **이제 못 읽는다**.

| 비유 | 실체 |
|---|---|
| JS 짐을 **들여보내기만** | `allowJs` — 방출·해석은 하되 **진단 0**(1절 A 열) |
| **모든 JS 짐을 연다** | `checkJs` — `TS7006`·`TS2322`·`TS2345`…(1절 B 열) |
| **이 짐만** 연다 / 안 연다 | 파일 첫 줄 `// @ts-check` / `// @ts-nocheck`(1절 C 열 · `j7`) |
| **꼬리표**가 신고서 | `@param {number}` · `@type` · `@typedef` · `@template`(1절) |
| ★★★ 꼬리표 **읽는 법이 바뀌었다** | 7.0.2 가 5.9.3 과 갈린 칸 `10 / 23` — `@enum` · 생성자 함수 · Closure 함수 타입 · `{?}` · `module.exports` 덧붙이기(2절) |
| 신고서로 **세관 서류(`.d.ts`)를 만든다** | `allowJs + declaration` — JSDoc 이 TS 선언으로 옮겨진다(3절) |
| 검사에 걸려도 **짐은 나간다** | `checkJs` 진단이 있어도 `.js` 방출 · `noEmitOnError` 만 막는다(3절) |

- ★★★ 한 줄로 — 「`allowJs` 는 들이기, `checkJs`(또는 파일마다 `// @ts-check`)는 검사하기다. 검사는 JSDoc 을 타입으로 읽고, JSDoc 이 없으면 초기값에서 추론하며 `strict` 아래에서는 `noImplicitAny` 도 JS 에 걸린다. 7.0 은 JSDoc 을 **TS 타입 문법에 가깝게** 읽어 옛 특례 몇을 버렸다.」

```text
  JS 파일을 TS 가 보는 세 단계 — 점진 도입의 사다리

  ① allowJs                ─> 프로젝트에 넣는다 · 방출한다 · 검사는 안 한다   (A 열 — 진단 0, 단 TS 문법은 TS8010)
  ② 파일마다 // @ts-check   ─> 고친 파일부터 하나씩 검사                      (C 열)
  ③ checkJs                ─> 전부 검사 · 아직 못 고친 파일은 // @ts-nocheck  (B 열 · j7)
  ④ JSDoc 을 채운다         ─> 추론이 못 하는 자리(매개변수)에 타입            (j3 ~ j6)
```

## 이 주제가 답하려는 질문

원고가 없는 관용구 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 설정·주석 스위치가 JS 파일의 검사를 어떻게 켜고 끄나** — 탐침 아홉 × 설정 셋 × 두 판(1절).
2. **★★★ 7.0 에서 JSDoc 해석이 무엇이 바뀌었나** — 꼴 스물셋 × 두 판(2절) · 「사라진 특례」 목록.
3. **★★ JS 파일이 방출에 들어가면 무엇이 나오나** — `.d.ts`(JSDoc 이 옮겨지나) · 진단이 있을 때의 `.js`(3절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **점진 도입 격자** | JS 탐침 아홉 × (A `allowJs` · B `+checkJs` · C `+// @ts-check`) × 5.9.3 · 7.0.2 | 진단 코드 | **본체 ①**(1절) |
| ★★★ **JSDoc 해석 판 격자** | JSDoc 꼴 스물셋 × 5.9.3 · 7.0.2 | `TS2322` 속 타입 글자 + 진단 코드 | **본체 ②**(2절) |
| ★★ **방출 창** | `allowJs + declaration` 의 `.d.ts` 두 판 · 진단 있는 JS 의 `.js` | 방출 글자 · `node` | 3절 |
| ★★★ **제5의 상태** | A 열의 침묵은 「통과」가 아니라 「안 물었다」 → B·C 열로 바꿔 물었다 | — | 1절 |
| ★ **부적용** | 방출물을 `node` 로 돌려 값 보기 — 3절 한 곳뿐 | — | — |

비용 — 격자 54칸(9 × 3 × 2) + 46칸(23 × 2) + 자기검사 둘 · `noImplicitAny` 여덟 · `.d.ts` 둘 · 방출 둘.

### (1) ★★★ 점진 도입 격자 — JS 탐침 아홉 × 설정 셋 × 두 판

**언제 쓰나** — JS 코드베이스에 TS 를 들일 때 **어느 스위치부터 켤지** 정할 때. 그리고 **켜지 않은 스위치가 무엇을 조용히 넘기는지** 알고 싶을 때.

설정은 셋 다 `"strict": true` 위에 얹는다. C 열은 `allowJs` 만 두고 **파일 첫 줄에 `// @ts-check` 를 붙인다.**

```bash
# ts46b-adopt48.sh
#!/usr/bin/env bash
# 점진 도입 격자 -- JS 파일 아홉 × 설정 셋 × 판 둘 · 칸마다 디렉토리와 tsconfig.json 을 따로
#   A = allowJs      B = allowJs + checkJs      C = allowJs 만 두고 파일 첫 줄에 `// @ts-check` 를 붙인다
#   설정은 셋 다 "strict": true 위에 얹는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
EXTRA=${EXTRA:-}   # 자기검사용
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\x1f'   # 구분자 US -- 규칙 32
rows=(
  "j1 JSDoc 없는 매개변수${T}function add(a, b) {\n    return a + b;\n}\nadd(1, 2);"
  "j2 초기값에서 추론${T}let count = 1;\ncount = \"many\";"
  "j3 @param${T}/** @param {number} n */\nfunction double(n) {\n    return n * 2;\n}\ndouble(\"2\");"
  "j4 @type${T}/** @type {string} */\nlet title = 42;"
  "j5 @typedef${T}/** @typedef {{ id: number, name: string }} User */\n/** @type {User} */\nconst u = { id: 1 };"
  "j6 @template${T}/**\n * @template T\n * @param {T} a\n * @param {T} b\n * @returns {T[]}\n */\nfunction pair(a, b) {\n    return [a, b];\n}\n/** @type {number[]} */\nconst xs = pair(1, \"2\");"
  "j7 // @ts-nocheck${T}// @ts-nocheck\nlet count = 1;\ncount = \"many\";"
  "j8 // @ts-expect-error${T}// @ts-expect-error\nlet count = 1;"
  "j9 TS 문법(타입 표기)${T}let count: number = 1;"
)
run() { case $1 in 7.0.2) tsc "${@:2}" ;; 5.9.3) node "$OLD" "${@:2}" ;; esac; }
codes() { grep -o '^c\.js([0-9]*,[0-9]*): error TS[0-9]*' | sed 's/.*error //' | sort | uniq -c | awk '{ printf "%s%s ", $2, ($1 > 1 ? "×" $1 : "") }' | sed 's/ $//'; }
split_check=0; split_ver=0; nc=0; nv=0; i=0; seen=""
printf '%-26s %-6s %-14s %-14s %s\n' "탐침" "판" "A allowJs" "B +checkJs" "C +@ts-check"
for r in "${rows[@]}"; do
  n=$(awk -F'\x1f' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r id body <<< "$r"
  declare -A got=()
  for col in A B C; do
    for v in 5.9.3 7.0.2; do
      i=$((i+1)); d="$D/c$i"; mkdir -p "$d" || exit 3
      if [ $col = C ]; then printf '// @ts-check\n%b\n' "$body" > "$d/c.js"; else printf '%b\n' "$body" > "$d/c.js"; fi || exit 3
      cj=false; [ $col = B ] && cj=true
      printf '{ "compilerOptions": { "allowJs": %s, "checkJs": %s, "strict": true, "target": "es2022", "noEmit": true }, "files": ["c.js"] }\n' true $cj > "$d/tsconfig.json"
      raw=$(cd "$d" && run $v --pretty false -p tsconfig.json $EXTRA 2>&1)
      if grep -qE '^error TS|^tsconfig\.json' <<< "$raw"; then echo "★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: $(grep -oE '^error TS[0-9]+' <<< "$raw" | sed 's/^error //' | sort -u | tr '\n' ' ')"; exit 4; fi
      c=$(codes <<< "$raw"); got[$col,$v]=${c:-OK}; seen="$seen${T}${got[$col,$v]}"
    done
  done
  for v in 5.9.3 7.0.2; do
    printf '%-26s %-6s %-14s %-14s %s\n' "$( [ $v = 5.9.3 ] && echo "$id" )" "$v" "${got[A,$v]}" "${got[B,$v]}" "${got[C,$v]}"
    nc=$((nc+1)); [ "${got[A,$v]}" != "${got[B,$v]}" ] && split_check=$((split_check+1))
  done
  nv=$((nv+1)); [ "${got[A,5.9.3]}${T}${got[B,5.9.3]}${T}${got[C,5.9.3]}" != "${got[A,7.0.2]}${T}${got[B,7.0.2]}${T}${got[C,7.0.2]}" ] && split_ver=$((split_ver+1))
  unset got
done
k=$(tr "$T" '\n' <<< "$seen" | sed '/^$/d' | sort -u | wc -l)
if [ "$k" -lt 2 ]; then echo "★ 모든 칸이 같은 값이다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "A 와 B(checkJs 끔/켬)가 갈린 칸 $split_check / $nc · 두 판이 갈린 탐침 $split_ver / $nv · 칸에 나온 값 가짓수 $k"
```

```text
===== bash ts46b-adopt48.sh (sh exit=0) =====
탐침                     판    A allowJs      B +checkJs     C +@ts-check
j1 JSDoc 없는 매개변수 5.9.3  OK             TS7006×2      TS7006×2
                           7.0.2  OK             TS7006×2      TS7006×2
j2 초기값에서 추론  5.9.3  OK             TS2322         TS2322
                           7.0.2  OK             TS2322         TS2322
j3 @param                  5.9.3  OK             TS2345         TS2345
                           7.0.2  OK             TS2345         TS2345
j4 @type                   5.9.3  OK             TS2322         TS2322
                           7.0.2  OK             TS2322         TS2322
j5 @typedef                5.9.3  OK             TS2741         TS2741
                           7.0.2  OK             TS2741         TS2741
j6 @template               5.9.3  OK             TS2345         TS2345
                           7.0.2  OK             TS2345         TS2345
j7 // @ts-nocheck          5.9.3  OK             OK             OK
                           7.0.2  OK             OK             OK
j8 // @ts-expect-error     5.9.3  OK             TS2578         TS2578
                           7.0.2  OK             TS2578         TS2578
j9 TS 문법(타입 표기) 5.9.3  TS8010         TS8010         TS8010
                           7.0.2  TS8010         TS8010         TS8010

A 와 B(checkJs 끔/켬)가 갈린 칸 14 / 18 · 두 판이 갈린 탐침 0 / 9 · 칸에 나온 값 가짓수 7
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **A 열은 `j9` 하나 빼고 전부 OK** — `allowJs` 만으로는 **검사하지 않는다.** 그 OK 여덟이 B 열에서는 **일곱이 진단**을 낸다(`j7` 은 스스로 `// @ts-nocheck`).
- ★★★ **마지막 줄 — A 와 B 가 갈린 칸 `14 / 18` · 두 판이 갈린 탐침 `0 / 9`.** 스위치의 뜻은 두 판이 같다.
- ★★★ **C 열 = B 열** — 파일 첫 줄 `// @ts-check` 가 그 파일에 한해 `checkJs` 와 **같은 진단**을 낸다.
- ★★ **`j7` — `// @ts-nocheck` 는 B 열도 끈다.** C 열(첫 줄에 `// @ts-check`, 둘째 줄에 `// @ts-nocheck`)도 OK 다 — **둘이 같이 있으면 끄는 쪽이 이겼다.**
- ★★ **`j1` — JSDoc 없는 매개변수가 `TS7006` 두 개** — `strict` 의 `noImplicitAny` 가 **JS 에도 걸린다**(아래 블록 · [42번 주제](../42-implicit-any-and-catch-variables/)).
- ★★ **`j2` — JSDoc 이 없어도 초기값에서 추론한다** — `let count = 1` 뒤 문자열 대입이 `TS2322`.
- ★★ **`j8` — `// @ts-expect-error` 가 JS 에서도 돈다** — 아래 줄에 오류가 없으니 `TS2578`(쓸데없는 지시). A 열에서는 그것도 **조용하다.**
- ★★★ **`j9` — TS 타입 표기는 A 열에서도 `TS8010`** — JS 파일에 **TS 문법을 쓰는 것**은 검사 스위치와 무관하게 막힌다(문법 오류라서).

**자기검사** — 격자 둘을 가짜 옵션으로:

```text
===== EXTRA=--bogusOpt bash <ts46b-adopt48.sh · ts46b-jsdoc48.sh> 의 마지막 두 줄 (sh exit=0) =====
---- ts46b-adopt48.sh
탐침                     판    A allowJs      B +checkJs     C +@ts-check
★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: TS5023 
(exit 4)
---- ts46b-jsdoc48.sh
    | /** @type {null} */ const p = o;
★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: TS5023 
(exit 4)
```

**`strict` 를 안 적으면 — 판 기본값이 갈린다:**

```js
// nia48.js
function add(a, b) {
    return a + b;
}
console.log(add(1, 2));
```

```text
===== tsc · "$TSC_OLD" --pretty false --noEmit --allowJs --checkJs -t es2022 <(strict 안 적음) · --strict · --strict false · --strict --noImplicitAny false> nia48.js (sh exit=0) =====
---- 7.0.2 (strict 안 적음)
nia48.js(1,14): error TS7006: Parameter 'a' implicitly has an 'any' type.
nia48.js(1,17): error TS7006: Parameter 'b' implicitly has an 'any' type.
(exit 1)
---- 5.9.3 (strict 안 적음)
(exit 0)
---- 7.0.2 --strict
nia48.js(1,14): error TS7006: Parameter 'a' implicitly has an 'any' type.
nia48.js(1,17): error TS7006: Parameter 'b' implicitly has an 'any' type.
(exit 1)
---- 5.9.3 --strict
nia48.js(1,14): error TS7006: Parameter 'a' implicitly has an 'any' type.
nia48.js(1,17): error TS7006: Parameter 'b' implicitly has an 'any' type.
(exit 2)
---- 7.0.2 --strict false
(exit 0)
---- 5.9.3 --strict false
(exit 0)
---- 7.0.2 --strict --noImplicitAny false
(exit 0)
---- 5.9.3 --strict --noImplicitAny false
(exit 0)
```

- ★★★ **`strict` 를 안 적은 줄에서 두 판이 갈린다** — 7.0.2 는 `TS7006` 둘, 5.9.3 은 진단 0. 7.0.2 는 `strict` 가 **기본으로 켜져 있다**([39번 주제](../39-strict-bundle/)). 그래서 격자는 `"strict": true` 를 **적어서** 두 판을 맞췄다.
- ★★ `--strict false` 나 `--noImplicitAny false` 면 두 판 다 조용하다 — `checkJs` 의 `TS7006` 은 **`noImplicitAny` 가 내는 것**이다.

### (2) ★★★ JSDoc 해석 판 격자 — 7.0 에서 사라진 특례

**언제 쓰나** — 5.x 에서 `checkJs` 로 깨끗하던 JS 코드베이스를 **7.0 으로 올렸더니 새 진단이 쏟아질 때** 어느 꼬리표가 원인인지 가를 때.

```bash
# ts46b-jsdoc48.sh
#!/usr/bin/env bash
# JSDoc 해석 판 격자 -- JS 파일 한 장씩 × (5.9.3 · 7.0.2) · 설정은 둘 다 allowJs + checkJs + strict
# 탐침은 `/** @type {null} */ const p = <식>;` -- 그 자리의 타입을 TS2322 의 메시지에서 읽는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
EXTRA=${EXTRA:-}   # 자기검사용
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\x1f'   # 구분자 US -- 규칙 32 (칸 안의 \n 은 printf %b 가 줄바꿈으로 편다)
P='/** @type {null} */ const p ='
rows=(
  "s01 Object${T}/** @type {Object} */\nlet o = {};\n$P o;"
  "s02 Object 위의 속성${T}/** @type {Object} */\nlet o = {};\nconst v = o.foo;"
  "s03 {*}${T}/** @param {*} x */\nfunction f(x) {\n    $P x;\n}"
  "s04 {?}${T}/** @param {?} x */\nfunction f(x) {\n    $P x;\n}"
  "s05 {?number}${T}/** @param {?number} x */\nfunction f(x) {\n    $P x;\n}"
  "s06 {!number}${T}/** @param {!number} x */\nfunction f(x) {\n    $P x;\n}"
  "s07 {number=}${T}/** @param {number=} x */\nfunction f(x) {\n    $P x;\n}"
  "s08 {...number} 를 보통 매개변수에${T}/** @param {...number} xs */\nfunction f(xs) {\n    $P xs;\n}"
  "s09 Array.<number>${T}/** @type {Array.<number>} */\nlet a = [];\n$P a;"
  "s10 Object.<string, number>${T}/** @type {Object.<string, number>} */\nlet m = {};\n$P m;"
  "s11 String(대문자)${T}/** @type {String} */\nlet s = \"a\";\n$P s;"
  "s12 function(string): number${T}/** @type {function(string): number} */\nconst fn = (s) => s.length;\n$P fn;"
  "s13 @enum${T}/** @enum {number} */\nconst Color = { Red: 0, Blue: 1 };\n/** @type {Color} */\nlet c = Color.Red;\n$P c;"
  "s14 @constructor 함수${T}/** @constructor */\nfunction Pt() {\n    this.x = 1;\n}\n$P new Pt();"
  "s15 @class 함수${T}/** @class */\nfunction Pt() {\n    this.x = 1;\n}\n$P new Pt();"
  "s16 prototype 에 붙인 함수${T}function Pt() {\n    this.x = 1;\n}\nPt.prototype.get = function () {\n    return this.x;\n};\n$P new Pt().get();"
  "s17 함수에 붙인 속성${T}function f() {}\nf.extra = 1;\n$P f.extra;"
  "s18 객체에 나중에 붙인 속성${T}const m = {};\nm.a = 1;\n$P m;"
  "s19 module.exports 에 두 번${T}module.exports = { a: 1 };\nmodule.exports.b = \"x\";\n$P module.exports;"
  "s20 @typedef + @property${T}/**\n * @typedef {Object} Opts\n * @property {string} name\n * @property {number} [size]\n */\n/** @type {Opts} */\nconst o = { name: \"a\" };\n$P o.size;"
  "s21 @template${T}/**\n * @template T\n * @param {T} x\n * @returns {T}\n */\nfunction id(x) {\n    return x;\n}\n$P id(1);"
  "s22 @callback${T}/**\n * @callback Cb\n * @param {string} s\n * @returns {number}\n */\n/** @type {Cb} */\nconst cb = (s) => s.length;\n$P cb;"
  "s23 형 변환 주석${T}const x = /** @type {number} */ (JSON.parse(\"1\"));\n$P x;"
)
run() { case $1 in 7.0.2) tsc "${@:2}" ;; 5.9.3) node "$OLD" "${@:2}" ;; esac; }
split=0; split_code=0; i=0
for r in "${rows[@]}"; do
  n=$(awk -F'\x1f' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r id body <<< "$r"
  i=$((i+1)); d="$D/c$i"; mkdir -p "$d" || exit 3
  printf '%b\n' "$body" > "$d/c.js" || exit 3
  printf '{ "compilerOptions": { "allowJs": true, "checkJs": true, "strict": true, "target": "es2022", "module": "commonjs", "noEmit": true }, "files": ["c.js"] }\n' > "$d/tsconfig.json"
  echo "[$id]"
  sed 's/^/    | /' "$d/c.js"
  declare -A got=() cd=()
  for v in 5.9.3 7.0.2; do
    raw=$(cd "$d" && run $v --pretty false -p tsconfig.json $EXTRA 2>&1)
    if grep -qE '^error TS|^tsconfig\.json' <<< "$raw"; then echo "★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: $(grep -oE '^error TS[0-9]+' <<< "$raw" | sed 's/^error //' | sort -u | tr '\n' ' ')"; exit 4; fi
    ty=$(sed -n "s/^c\.js([0-9]*,[0-9]*): error TS2322: Type '\(.*\)' is not assignable to type 'null'\.\$/\1/p" <<< "$raw")
    codes=$(grep -o '^c\.js([0-9]*,[0-9]*): error TS[0-9]*' <<< "$raw" | sed 's/^c\.js//; s/: error / /' | tr '\n' ' ' | sed 's/ $//')
    got[$v]="p: ${ty:-(탐침 진단 없음)}"; cd[$v]="${codes:-OK}"
    printf '    %-6s %s   <%s>\n' "$v" "${got[$v]}" "${cd[$v]}"
  done
  if [ "${got[5.9.3]}${cd[5.9.3]}" != "${got[7.0.2]}${cd[7.0.2]}" ]; then split=$((split+1)); echo "    -> 두 판이 갈렸다"; fi
  a=$(grep -o 'TS[0-9]*' <<< "${cd[5.9.3]}" | sort | tr '\n' ' '); b=$(grep -o 'TS[0-9]*' <<< "${cd[7.0.2]}" | sort | tr '\n' ' ')
  [ "$a" != "$b" ] && split_code=$((split_code+1))
  unset got cd
done
if [ $split -eq 0 ] || [ $split -eq $i ]; then echo "★ 전부 같거나 전부 갈렸다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "두 판이 갈린 칸 $split / $i · 그중 진단 코드 목록까지 갈린 칸 $split_code / $i"
```

```text
===== bash ts46b-jsdoc48.sh (sh exit=0) =====
[s01 Object]
    | /** @type {Object} */
    | let o = {};
    | /** @type {null} */ const p = o;
    5.9.3  p: Object   <(3,27) TS2322>
    7.0.2  p: Object   <(3,27) TS2322>
[s02 Object 위의 속성]
    | /** @type {Object} */
    | let o = {};
    | const v = o.foo;
    5.9.3  p: (탐침 진단 없음)   <(3,13) TS2339>
    7.0.2  p: (탐침 진단 없음)   <(3,13) TS2339>
[s03 {*}]
    | /** @param {*} x */
    | function f(x) {
    |     /** @type {null} */ const p = x;
    | }
    5.9.3  p: (탐침 진단 없음)   <OK>
    7.0.2  p: (탐침 진단 없음)   <OK>
[s04 {?}]
    | /** @param {?} x */
    | function f(x) {
    |     /** @type {null} */ const p = x;
    | }
    5.9.3  p: (탐침 진단 없음)   <OK>
    7.0.2  p: (탐침 진단 없음)   <(1,14) TS1110>
    -> 두 판이 갈렸다
[s05 {?number}]
    | /** @param {?number} x */
    | function f(x) {
    |     /** @type {null} */ const p = x;
    | }
    5.9.3  p: number | null   <(3,31) TS2322>
    7.0.2  p: number | null   <(3,31) TS2322>
[s06 {!number}]
    | /** @param {!number} x */
    | function f(x) {
    |     /** @type {null} */ const p = x;
    | }
    5.9.3  p: number   <(3,31) TS2322>
    7.0.2  p: number   <(3,31) TS2322>
[s07 {number=}]
    | /** @param {number=} x */
    | function f(x) {
    |     /** @type {null} */ const p = x;
    | }
    5.9.3  p: number | undefined   <(3,31) TS2322>
    7.0.2  p: number | undefined   <(3,31) TS2322>
[s08 {...number} 를 보통 매개변수에]
    | /** @param {...number} xs */
    | function f(xs) {
    |     /** @type {null} */ const p = xs;
    | }
    5.9.3  p: number | undefined   <(3,31) TS2322>
    7.0.2  p: number[]   <(3,31) TS2322>
    -> 두 판이 갈렸다
[s09 Array.<number>]
    | /** @type {Array.<number>} */
    | let a = [];
    | /** @type {null} */ const p = a;
    5.9.3  p: number[]   <(3,27) TS2322>
    7.0.2  p: number[]   <(3,27) TS2322>
[s10 Object.<string, number>]
    | /** @type {Object.<string, number>} */
    | let m = {};
    | /** @type {null} */ const p = m;
    5.9.3  p: { [x: string]: number; }   <(3,27) TS2322>
    7.0.2  p: Record<string, number>   <(3,27) TS2322>
    -> 두 판이 갈렸다
[s11 String(대문자)]
    | /** @type {String} */
    | let s = "a";
    | /** @type {null} */ const p = s;
    5.9.3  p: string   <(3,27) TS2322>
    7.0.2  p: string   <(3,27) TS2322>
[s12 function(string): number]
    | /** @type {function(string): number} */
    | const fn = (s) => s.length;
    | /** @type {null} */ const p = fn;
    5.9.3  p: (arg0: string) => number   <(3,27) TS2322>
    7.0.2  p: Function   <(1,20) TS1005 (2,13) TS7006 (3,27) TS2322>
    -> 두 판이 갈렸다
[s13 @enum]
    | /** @enum {number} */
    | const Color = { Red: 0, Blue: 1 };
    | /** @type {Color} */
    | let c = Color.Red;
    | /** @type {null} */ const p = c;
    5.9.3  p: number   <(5,27) TS2322>
    7.0.2  p: (탐침 진단 없음)   <(3,12) TS2749>
    -> 두 판이 갈렸다
[s14 @constructor 함수]
    | /** @constructor */
    | function Pt() {
    |     this.x = 1;
    | }
    | /** @type {null} */ const p = new Pt();
    5.9.3  p: Pt   <(5,27) TS2322>
    7.0.2  p: (탐침 진단 없음)   <(3,5) TS2683 (5,31) TS7009>
    -> 두 판이 갈렸다
[s15 @class 함수]
    | /** @class */
    | function Pt() {
    |     this.x = 1;
    | }
    | /** @type {null} */ const p = new Pt();
    5.9.3  p: Pt   <(5,27) TS2322>
    7.0.2  p: (탐침 진단 없음)   <(3,5) TS2683 (5,31) TS7009>
    -> 두 판이 갈렸다
[s16 prototype 에 붙인 함수]
    | function Pt() {
    |     this.x = 1;
    | }
    | Pt.prototype.get = function () {
    |     return this.x;
    | };
    | /** @type {null} */ const p = new Pt().get();
    5.9.3  p: number   <(7,27) TS2322>
    7.0.2  p: (탐침 진단 없음)   <(2,5) TS2683 (7,31) TS7009>
    -> 두 판이 갈렸다
[s17 함수에 붙인 속성]
    | function f() {}
    | f.extra = 1;
    | /** @type {null} */ const p = f.extra;
    5.9.3  p: number   <(3,27) TS2322>
    7.0.2  p: number   <(3,27) TS2322>
[s18 객체에 나중에 붙인 속성]
    | const m = {};
    | m.a = 1;
    | /** @type {null} */ const p = m;
    5.9.3  p: typeof m   <(3,27) TS2322>
    7.0.2  p: { a: number; }   <(3,27) TS2322>
    -> 두 판이 갈렸다
[s19 module.exports 에 두 번]
    | module.exports = { a: 1 };
    | module.exports.b = "x";
    | /** @type {null} */ const p = module.exports;
    5.9.3  p: { a: number; b: "x"; }   <(3,27) TS2322>
    7.0.2  p: { a: number; }   <(1,1) TS2309 (2,16) TS2339 (3,27) TS2322>
    -> 두 판이 갈렸다
[s20 @typedef + @property]
    | /**
    |  * @typedef {Object} Opts
    |  * @property {string} name
    |  * @property {number} [size]
    |  */
    | /** @type {Opts} */
    | const o = { name: "a" };
    | /** @type {null} */ const p = o.size;
    5.9.3  p: number | undefined   <(8,27) TS2322>
    7.0.2  p: number | undefined   <(8,27) TS2322>
[s21 @template]
    | /**
    |  * @template T
    |  * @param {T} x
    |  * @returns {T}
    |  */
    | function id(x) {
    |     return x;
    | }
    | /** @type {null} */ const p = id(1);
    5.9.3  p: 1   <(9,27) TS2322>
    7.0.2  p: 1   <(9,27) TS2322>
[s22 @callback]
    | /**
    |  * @callback Cb
    |  * @param {string} s
    |  * @returns {number}
    |  */
    | /** @type {Cb} */
    | const cb = (s) => s.length;
    | /** @type {null} */ const p = cb;
    5.9.3  p: Cb   <(8,27) TS2322>
    7.0.2  p: Cb   <(8,27) TS2322>
[s23 형 변환 주석]
    | const x = /** @type {number} */ (JSON.parse("1"));
    | /** @type {null} */ const p = x;
    5.9.3  p: number   <(2,27) TS2322>
    7.0.2  p: number   <(2,27) TS2322>

두 판이 갈린 칸 10 / 23 · 그중 진단 코드 목록까지 갈린 칸 7 / 23
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **마지막 줄 — 두 판이 갈린 칸 `10 / 23`, 그중 진단 코드 목록까지 갈린 칸 `7 / 23`.** 나머지 셋(`s08`·`s10`·`s18`)은 **타입 글자만** 갈렸다.
- ★★★ **`s13` `@enum` — 7.0.2 는 `TS2749`**(「`Color` 는 값인데 타입 자리에 썼다」). `@enum` 태그를 **타입을 만드는 선언으로 읽지 않는다.**
- ★★★ **`s14`·`s15`·`s16` — 생성자 함수가 사라졌다.** `@constructor`·`@class` 를 달아도, `prototype` 에 메서드를 붙여도 7.0.2 는 `this` 를 `any` 로 보고(`TS2683`) `new` 에 생성 시그니처가 없다(`TS7009`). 5.9.3 은 셋 다 `Pt` 로 읽었다.
- ★★★ **`s12` Closure 함수 타입 `function(string): number` — 7.0.2 는 파싱 실패**(`TS1005`) 후 `Function` 으로 떨어지고, 화살표 매개변수에 `TS7006` 까지 붙는다.
- ★★★ **`s04` `{?}`(Closure 의 「알 수 없음」) — 7.0.2 는 `TS1110`**(타입이 와야 한다).
- ★★★ **`s19` `module.exports = {…}` 뒤 `module.exports.b = …` — 7.0.2 는 `TS2309` + `TS2339`.** 5.9.3 은 두 줄을 **합쳐** `{ a: number; b: "x"; }` 로 읽었다.
- ★★ **`s08` `@param {...number}` 를 보통 매개변수에** — 5.9.3 은 `number | undefined`(원소 하나), 7.0.2 는 `number[]`(TS 의 나머지 매개변수처럼). **진단 코드는 같은데 뜻이 바뀌었다.**
- ★ **`s10`·`s18` 은 표시만** — `{ [x: string]: number; }` → `Record<string, number>` · `typeof m` → `{ a: number; }`.
- ★★ **안 갈린 13칸** — `Object`·`{*}`·`{?number}`·`{!number}`·`{number=}`·`Array.<number>`·`String`·함수 덧붙이기·`@typedef`·`@template`·`@callback`·형 변환 주석. Closure 꼴이라도 **TS 타입으로 옮길 수 있는 것**은 남았다.

```text
  7.0.2 에서 5.9.3 과 갈린 칸 — 이 문서가 「사라진 특례」라고 부르는 것

  진단이 새로 난다 (7칸)
    @enum 으로 타입 만들기                  s13   TS2749
    @constructor · @class · prototype 붙이기 s14 s15 s16   TS2683 · TS7009
    Closure 함수 타입 function(…): …         s12   TS1005 (그리고 Function 으로)
    {?}                                     s04   TS1110
    module.exports 에 두 번                  s19   TS2309 · TS2339
  뜻이 바뀐다 (1칸)
    @param {...T} 를 보통 매개변수에         s08   원소 하나 -> 배열
  표시만 바뀐다 (2칸)
    Object.<K, V> · 나중에 붙인 속성         s10 s18
```

- ★★★ 이 목록은 **이 격자가 던진 스물셋 안에서 찾은 것**이다 — 공식 목록과 **대조하지 못했고**, 던지지 않은 꼴(`@this` 조합 · `@augments` · `exports.x` 덧붙이기 여러 파일 등)은 모른다.
- ★ 「사라졌다」가 **의도된 제거인지 아직 구현 안 된 것인지**도 이 머신에서는 가를 수 없다 — 출처 확인 못 함.

### (3) ★★ 방출 창 — JSDoc 에서 `.d.ts` · 진단이 있을 때의 `.js`

**JS 에서 선언 파일 뽑기** — [37번 주제](../37-writing-declaration-files/)는 `.d.ts` 를 **손으로** 썼다. 여기서는 JSDoc 이 달린 JS 에서 **뽑는다:**

```js
// dts48.js
/**
 * @typedef {Object} Item
 * @property {string} name
 * @property {number} [qty]
 */

/**
 * @param {Item[]} items
 * @returns {number}
 */
export function total(items) {
    return items.reduce((s, it) => s + (it.qty ?? 1), 0);
}

/**
 * @template T
 * @param {T[]} xs
 * @returns {T | undefined}
 */
export function first(xs) {
    return xs[0];
}

export function untyped(a, b) {
    return a + b;
}

export class Counter {
    /** @type {number} */
    count = 0;
    /** @param {number} by */
    add(by) {
        this.count += by;
    }
}
```

```text
===== tsc · "$TSC_OLD" --pretty false --allowJs --declaration --emitDeclarationOnly --strict false -t es2022 --module es2022 --outDir <d7 · d5> dts48.js ; 두 .d.ts ; diff (sh exit=0) =====
(7.0.2 exit 0)
(5.9.3 exit 0)
===== 7.0.2 가 방출한 d7/dts48.d.ts =====
/**
 * @typedef {Object} Item
 * @property {string} name
 * @property {number} [qty]
 */
export type Item = {
    name: string;
    qty?: number;
};
/**
 * @param {Item[]} items
 * @returns {number}
 */
export declare function total(items: Item[]): number;
/**
 * @template T
 * @param {T[]} xs
 * @returns {T | undefined}
 */
export declare function first<T>(xs: T[]): T | undefined;
export declare function untyped(a: any, b: any): any;
export declare class Counter {
    /** @type {number} */
    count: number;
    /** @param {number} by */
    add(by: number): void;
}
===== 5.9.3 이 방출한 d5/dts48.d.ts =====
/**
 * @typedef {Object} Item
 * @property {string} name
 * @property {number} [qty]
 */
/**
 * @param {Item[]} items
 * @returns {number}
 */
export function total(items: Item[]): number;
/**
 * @template T
 * @param {T[]} xs
 * @returns {T | undefined}
 */
export function first<T>(xs: T[]): T | undefined;
export function untyped(a: any, b: any): any;
export class Counter {
    /** @type {number} */
    count: number;
    /** @param {number} by */
    add(by: number): void;
}
export type Item = {
    name: string;
    qty?: number;
};
===== diff d5/dts48.d.ts d7/dts48.d.ts =====
5a6,9
> export type Item = {
>     name: string;
>     qty?: number;
> };
10c14
< export function total(items: Item[]): number;
---
> export declare function total(items: Item[]): number;
16,18c20,22
< export function first<T>(xs: T[]): T | undefined;
< export function untyped(a: any, b: any): any;
< export class Counter {
---
> export declare function first<T>(xs: T[]): T | undefined;
> export declare function untyped(a: any, b: any): any;
> export declare class Counter {
24,27d27
< export type Item = {
<     name: string;
<     qty?: number;
< };
(diff exit 1)
```

- ★★★ **JSDoc 이 TS 선언으로 옮겨진다** — `@typedef` → `export type Item`, `@param`/`@returns` → 매개변수·반환 타입, `@template T` → `<T>`, `@type` 필드 → `count: number`. **JSDoc 주석도 그대로 남는다.**
- ★★ JSDoc 없는 `untyped` 는 **`any` 셋**이 된다(`--strict false` 로 뽑았다 — `strict` 면 `TS7006` 이지만 방출은 된다).
- ★★ **두 판의 `.d.ts` 가 다르다** — 7.0.2 는 **`declare` 를 붙이고** `Item` 을 **맨 위**에 둔다. 5.9.3 은 `declare` 가 없고 `Item` 이 **맨 끝**이다. `diff` 가 넷 덩이. 타입의 뜻은 같다.

**JS 파일의 타입 오류는 방출을 막나:**

```js
// emit48.js
/** @param {number} n */
function double(n) {
    return n * 2;
}
console.log(double("2"));
```

```text
===== tsc --pretty false --allowJs --checkJs -t es2022 [--noEmitOnError] --outDir o48 emit48.js ; o48 의 파일 ; node (sh exit=0) =====
---- (noEmitOnError 없음)
emit48.js(5,20): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
(tsc exit 2)
o48 의 파일: emit48.js 
4
(node exit 0)
---- --noEmitOnError
emit48.js(5,20): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
(tsc exit 1)
o48 의 파일: 
```

- ★★★ **막지 않는다** — `TS2345` 가 나도 `o48/emit48.js` 가 나오고 `node` 는 `"2" * 2` 를 계산해 `4` 를 찍는다. [02번 주제](../02-type-checking-vs-emit/)의 「검사와 방출의 분리」가 JS 파일에도 그대로다.
- ★★ **`noEmitOnError` 면 `o48` 이 비었다**(tsc exit 1).

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  "allowJs": true                           JS 파일을 프로젝트에 넣는다 — 검사 없음            (1절 A)
  "checkJs": true                           JS 파일을 전부 검사                                (1절 B)
  // @ts-check   (파일 첫 줄)               그 파일만 검사                                     (1절 C)
  // @ts-nocheck                            그 파일은 검사 안 함 — checkJs 도, @ts-check 도 이긴다  (1절 j7)
  // @ts-expect-error                       다음 줄의 오류를 기대 — JS 에서도                   (1절 j8)
  /** @param {number} n */                  매개변수 타입                                      (1절 j3)
  /** @type {string} */                     변수 타입                                          (1절 j4)
  /** @typedef {{ id: number }} User */     타입 별칭                                          (1절 j5 · 3절)
  /** @template T */                        타입 매개변수                                      (1절 j6 · 3절)
  const x = /** @type {number} */ (e)       형 변환 — 괄호가 필수                               (2절 s23)
  "allowJs" + "declaration"                 JS 에서 .d.ts                                      (3절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 판 |
|---|---|---|
| JS 파일에 `let count: number = 1` | `TS8010` | 두 판 · **검사 스위치와 무관** |
| JS 파일에 `u!`(non-null 단언) | `TS8013` | 두 판(탐색 중 확인) |
| `/** @type {Color} */` — `Color` 가 `@enum` 객체 | `TS2749` | **7.0.2 만** |
| `new Pt()` — `Pt` 가 `@constructor` 함수 | `TS2683` · `TS7009` | **7.0.2 만** |
| `/** @type {function(string): number} */` | `TS1005` | **7.0.2 만** |
| `/** @param {?} x */` | `TS1110` | **7.0.2 만** |
| `module.exports = {…}` 뒤 `module.exports.b = …` | `TS2309` · `TS2339` | **7.0.2 만** |

**규칙 불릿**

- ★★★ **`allowJs` 는 들이기, `checkJs`·`// @ts-check` 는 검사하기** — A 와 B 가 갈린 칸 `14 / 18`(1절).
- ★★★ **`// @ts-nocheck` 가 가장 세다** — `checkJs` 도, 같은 파일의 `// @ts-check` 도 이긴다(1절 `j7`).
- ★★★ **`strict` 는 JS 에도 걸린다** — JSDoc 없는 매개변수가 `TS7006`. 7.0.2 는 `strict` 를 안 적어도 켜져 있다(1절 끝).
- ★★★ **7.0.2 는 Closure 식 꼬리표 몇과 생성자 함수·`@enum`·`module.exports` 덧붙이기를 버렸다** — 2절의 `10 / 23`.
- ★★ **JS 의 타입 오류도 방출을 막지 않는다** — `noEmitOnError` 만 막는다(3절).

## 어디서 틀리나

- ★★★ 「**`allowJs` 를 켰으니 JS 도 검사된다**」 — A 열은 여덟 탐침이 조용했다. 검사는 `checkJs` 나 파일 첫 줄 `// @ts-check`(1절).
- ★★★ 「**5.x 에서 `checkJs` 가 깨끗했으니 7.0 에서도 깨끗하다**」 — `@enum` · 생성자 함수 · Closure 함수 타입 · `{?}` · `module.exports` 덧붙이기가 7.0.2 에서 진단을 낸다(2절).
- ★★★ 「**JS 에는 `noImplicitAny` 가 없다**」 — `strict` 면 `TS7006` 이다. 그리고 7.0.2 는 **기본이 `strict`** 라 설정을 안 바꿔도 새로 난다(1절 끝).
- ★★ 「**`// @ts-check` 를 붙이면 `// @ts-nocheck` 를 이긴다**」 — 반대다(1절 `j7` C 열).
- ★★ 「**`@param {...number} xs` 는 `xs` 를 배열로 만든다**」 — 5.9.3 은 원소 하나(`number | undefined`)로 읽었다. 7.0.2 부터 배열이다 — **판을 적어라**(2절 `s08`).
- ★★ 「**JS 파일에서 `.d.ts` 는 두 판이 같다**」 — `declare` 와 순서가 다르다(3절). 뜻은 같지만 **글자 비교하는 도구**(스냅숏 테스트)는 깨진다.
- ★ 「**JS 에 검사 오류가 있으면 빌드가 멈춘다**」 — 방출된다(3절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **JS(런타임)** | JSDoc 은 **주석**이다 — 실행에 아무 영향이 없다 | 3절 — `"2" * 2` 가 `4` |
| **★★★ TS 설정의 뜻(두 판 공통)** | `allowJs`·`checkJs`·`// @ts-check`·`// @ts-nocheck`·`// @ts-expect-error` | 1절 `0 / 9` |
| **★★★ TS 7.0.2 의 JSDoc 해석** | 2절의 갈린 열 칸 | `10 / 23` |
| **★★ 판 기본값** | 7.0.2 는 `strict` 기본 켬 | 1절 끝 |
| **★ 방출 모양** | `.d.ts` 의 `declare`·순서 | 3절 |
| **출처 확인 못 함** | 7.0 의 공식 변경 목록 · 의도된 제거인지 | 외부 문서를 열지 않았다 |
| **안 잰 것** | 여러 파일에 걸친 `exports.x` · `@augments`·`@implements` · `@import` · 대형 코드베이스의 진단 분포 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **들이기 → 파일마다 `// @ts-check` → `checkJs` + 남은 파일 `// @ts-nocheck`** 순서로 | 처음부터 `checkJs` 를 켜고 진단 수천 개와 싸우기 |
| ★★★ **7.0 으로 올리기 전에 2절의 꼴을 grep** — `@enum` · `@constructor`·`@class` · `function(` · `{?}` · `module.exports.` | 「5.x 에서 깨끗했다」로 넘기기 |
| ★★ **생성자 함수는 `class` 로** 바꾼다 — 7.0.2 가 읽는다 | 7.0 에서도 `@constructor` 에 기대기 |
| ★★ **JS 라이브러리의 `.d.ts` 는 JSDoc + `allowJs + declaration` 으로** 뽑는다(3절) | 손으로 쓴 `.d.ts` 와 JSDoc 을 **둘 다** 유지하기 — 어긋난다 |
| ★ **`noEmitOnError`** 로 검사 오류가 있는 JS 를 내보내지 않기 | 검사 진단이 있어도 나가는 빌드를 배포 |

## 핵심 문장

1. **`allowJs` 는 JS 파일을 들이기만 하고 검사는 `checkJs` 나 파일 첫 줄 `// @ts-check` 가 한다** — A 와 B 가 갈린 칸 `14 / 18`, 스위치의 뜻은 두 판이 같다(`0 / 9`).
2. **`// @ts-nocheck` 가 가장 세고, `// @ts-expect-error` 는 JS 에서도 돈다** — 쓸데없으면 `TS2578`.
3. **`strict` 의 `noImplicitAny` 는 JS 에도 걸린다** — 7.0.2 는 `strict` 를 안 적어도 JSDoc 없는 매개변수에 `TS7006` 을 낸다.
4. **7.0.2 는 JSDoc 을 TS 타입 문법에 맞춰 읽는다** — 5.9.3 과 갈린 칸 `10 / 23`: `@enum` · 생성자 함수 셋 · Closure 함수 타입 · `{?}` · `module.exports` 덧붙이기 · `@param {...T}` 의 뜻 · 표시 둘. 공식 목록과는 대조하지 못했다.
5. **JSDoc 은 `.d.ts` 로 옮겨지고, JS 의 검사 오류는 방출을 막지 않는다** — `noEmitOnError` 만 막는다.

## 관련 자료

- [**36번 주제** — 타입 전용 import·export](../36-type-only-imports-and-exports/) — ★★ **README 의 선행.** 방출 규칙(`verbatimModuleSyntax`·`isolatedModules`)의 정본. 여기서는 JS 파일이 방출에 들어갈 때만 봤다.
- [**42번 주제** — 암시적 `any` 와 catch 변수](../42-implicit-any-and-catch-variables/) — 1절 `j1` 의 `TS7006` 이 JS 에서도 같다는 것. 자리 아홉 격자는 그쪽이 정본.
- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — 7.0.2 의 `strict` 기본값.
- [**37번 주제** — 선언 파일 작성](../37-writing-declaration-files/) — 손으로 쓰는 `.d.ts`. 여기서는 JSDoc 에서 **뽑았다**(3절).
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 3절의 「오류가 있어도 방출」.
- [**44번 주제** — 프로젝트 참조와 선언 방출](../44-project-references-and-declaration-emit/) — `declaration` 방출의 나머지.

## 용어 풀이

> **`allowJs`** — `.js` 파일을 컴파일 대상에 넣는다. 해석·방출은 하되 **타입 검사는 안 한다.**\
> 예: 1절 A 열.

> **`checkJs`** — `allowJs` 로 들인 JS 파일을 **전부 검사**한다.\
> 예: 1절 B 열.

> **`// @ts-check` · `// @ts-nocheck`** — 파일 머리의 주석 스위치. 앞은 그 파일만 켜고 뒤는 그 파일만 끈다. 둘이 같이 있으면 끄는 쪽이 이겼다.\
> 예: 1절 C 열 · `j7`.

> **JSDoc 타입** — `/** @param {T} x */` 꼴 주석에 적은 타입. JS 파일에서 TS 가 **타입 표기로 읽는다.**\
> 예: 1절 `j3`.

> **Closure 식 표기** — Google Closure Compiler 에서 온 JSDoc 타입 문법(`{?}` · `function(string): number` · `{?number}` · `{number=}`). 7.0.2 는 일부만 읽는다.\
> 예: 2절 `s04`·`s12`.

> **생성자 함수** — `class` 없이 `function Pt() { this.x = 1 }` 과 `new Pt()` 로 쓰는 옛 JS 꼴. 5.9.3 은 타입으로 읽었고 7.0.2 는 읽지 않았다.\
> 예: 2절 `s14`\~`s16`.

> **`TS8010`** — 「Type annotations can only be used in TypeScript files.」 — JS 파일에 TS 문법.\
> 예: 1절 `j9`.

> **`TS2749`** — 「'X' refers to a value, but is being used as a type here.」 — 값 이름을 타입 자리에.\
> 예: 2절 `s13`.

## 더 들어가면

- **`@import` 태그(5.5)와 `@satisfies`(5.0)** — JS 에서 타입만 들여오기·`satisfies` 쓰기. `@satisfies` 는 두 판 같게 통과했다(탐색 중). **격자에 넣지 않았다.**
- **여러 파일에 걸친 CommonJS** — `exports.x = …` 를 여러 파일이 `require` 하는 모양. 탐색에서 메시지에 **절대 경로가 박혀**(`typeof import("…")`) 싣지 않았다.
- **대형 코드베이스에서 7.0 이행 시 진단 분포** — 재지 않았다.
