# ts/syntax/48 — JS 파일 타입 검사 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·타입 글자·방출은 `tsc` **7.0.2** 에서 실제로 얻었다. 판 비교는 **5.9.3** 을 환경변수(`TSC_OLD`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ **「7.0 에서 사라진 특례」는 이 문서의 격자에서 5.9.3 과 7.0.2 가 갈린 칸의 이름**이다 — 공식 목록과는 대조하지 못했다(출처 확인 못 함).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ A 열은 `j9`(`TS8010`) 말고 **전부 OK** · B 열 = C 열 · A 와 B 가 갈린 칸 **`14 / 18`** · 두 판이 갈린 탐침 **`0 / 9`**

**출력**

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

**왜 그런가**

- ★★★ `allowJs` 는 **들이기만** 한다. 검사는 `checkJs`(B) 나 파일 첫 줄 `// @ts-check`(C) — 둘의 진단이 **같다.**
- ★★ `j7` 은 `// @ts-nocheck` 가 B·C 를 다 끈다 · `j8` 은 JS 에서도 `// @ts-expect-error` 가 돌아 `TS2578` · `j9` 는 **문법** 오류라 스위치와 무관하다.

### 2. ★★★ **`strict` 를 안 적은 줄만 두 판이 갈린다** — 7.0.2 `TS7006` 둘 · 5.9.3 진단 0 · `--strict` 는 두 판 `TS7006` · `false` 두 줄은 두 판 조용

**출력**

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

**왜 그런가**

- ★★★ 7.0.2 는 `strict` 가 **기본으로 켜져** 있다([39번 주제](../39-strict-bundle/)) — 그래서 JSDoc 없는 매개변수가 설정을 안 바꿔도 새로 걸린다.
- ★★ `TS7006` 은 `noImplicitAny` 가 낸다 — 그것만 끄면 조용하다.

### 3. ★★★ 두 판이 갈린 칸 **`10 / 23`**(진단 코드까지 **`7 / 23`**) — `s04` `{?}` · `s08` `{...number}` · `s10` `Object.<…>` · `s12` Closure 함수 타입 · `s13` `@enum` · `s14`·`s15`·`s16` 생성자 함수 · `s18` 덧붙인 속성 · `s19` `module.exports` 두 번

**출력**

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

**왜 그런가**

- ★★★ 7.0.2 는 JSDoc 을 **TS 타입 문법 쪽으로** 읽는다 — TS 에 대응물이 없는 Closure 꼴(`{?}`·`function(…): …`)과 **JS 관용 추론**(생성자 함수 · `@enum` 객체 · `module.exports` 덧붙이기)이 빠졌다.
- ★★ `s08` 은 진단 코드가 같은데 **뜻이 바뀐** 칸이다 — 원소 하나에서 배열로.

### 4. ★★★ JSDoc 이 **TS 선언으로 옮겨진다**(`type Item` · `total(items: Item[]): number` · `first<T>` · `count: number`) · JSDoc 없는 `untyped` 는 `any` 셋 · 두 판의 `.d.ts` 는 **다르다** — 7.0.2 는 `declare` 를 붙이고 `Item` 을 맨 위에

**출력**

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

**왜 그런가**

- ★★ 뜻은 같고 **모양이 다르다** — `declare` 유무와 `type` 의 위치. `.d.ts` 를 글자로 비교하는 스냅숏은 판을 올리면 깨진다.
- ★ JSDoc 주석이 선언 위에 그대로 남는다.

### 5. ★★★ **나온다** — `TS2345` 가 나도 `o48/emit48.js` 가 생기고 `node` 는 **`4`** · `--noEmitOnError` 면 **`o48` 이 빈다**

**출력**

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

**왜 그런가**

- ★★★ 검사와 방출은 **분리**돼 있다 — JS 파일도 같다. JSDoc 은 **주석**이라 `node` 는 `"2" * 2` 를 그냥 계산한다.

### 6. ★★★ 「**검사하지 않았다**」 다 — 「검사해서 괜찮았다」가 아니다 · 같은 파일을 **B 열(`checkJs`)·C 열(`// @ts-check`)** 로 바꿔 물어, A 열의 OK 여덟 중 일곱이 진단을 낸다는 것으로 확인했다

- ★★ 제5의 상태다 — 진단 창이 조용한 까닭이 **기준(검사 스위치)** 에 있었다. A 열이 유일하게 말한 것은 `j9` 의 `TS8010`(문법)뿐이다.

### 7. ★★ **`j7` 의 C 열** — 첫 줄 `// @ts-check`(격자가 붙인 것) 아래에 `// @ts-nocheck` · **끄는 쪽이 이겼다**(두 판 OK)

- ★ B 열(`checkJs`)도 같이 껐다 — `// @ts-nocheck` 가 가장 세다.

### 8. ★★★ 말할 수 없는 것 — **공식 목록과의 대조** · **의도된 제거인지 미구현인지** · **던지지 않은 꼴** · 가르면 — 진단이 새로 난 칸 **7**(`s04`·`s12`·`s13`·`s14`·`s15`·`s16`·`s19`) · 뜻만 바뀐 칸 **1**(`s08`) · 표시만 바뀐 칸 **2**(`s10`·`s18`)

- ★★ 스크립트가 센 것은 「갈린 칸 `10`」과 「진단 코드까지 갈린 칸 `7`」이다. 남은 셋을 **뜻**(`s08`)과 **표시**(`s10`·`s18`)로 가른 것은 **사람의 판정**이다 — `number | undefined` 대 `number[]` 는 뜻이 다르고, `{ [x: string]: number; }` 대 `Record<string, number>` 는 같은 타입의 두 표기다.

### 9. ★★ grep 할 꼴 — `@enum` · `@constructor`·`@class` · `.prototype.` 에 함수 붙이기 · `function(` 가 든 JSDoc 타입 · `{?}` · `module.exports.` 덧붙이기 · `{...` 가 붙은 보통 매개변수 · 고치는 법 — 생성자 함수는 **`class`** 로, `@enum` 은 **`@typedef` + 객체**나 TS 파일로, Closure 함수 타입은 **`(s: string) => number`** 꼴로

- ★ 고친 꼴이 7.0.2 에서 읽힌다는 것은 **안 갈린 칸**(`@typedef`·`@callback`·`@template`)이 보인다. **`class` 로 바꾼 판은 따로 던지지 않았다.**

### 10. ★★ `j1` — 42편의 **`noImplicitAny` 가 매개변수에서 `TS7006` 을 낸다**가 JS 에서도 · 4번 — 37편의 **`.d.ts` 의 모양**을 JSDoc 에서 **자동으로** 얻는다 · 5번 — 02편의 「**검사 오류가 있어도 방출한다**」가 JS 에서도

- [**42번 주제**](../42-implicit-any-and-catch-variables/) · [**37번 주제**](../37-writing-declaration-files/) · [**02번 주제**](../02-type-checking-vs-emit/).

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"` · `node` | `7.0.2` · `5.9.3` · `v18.19.1` |
| ★★★ 점진 도입 격자 | `bash ts46b-adopt48.sh` — 9 × 3 × 2 | A·B 가 갈린 칸 **`14 / 18`** · 두 판이 갈린 탐침 **`0 / 9`** |
| ★★★ JSDoc 판 격자 | `bash ts46b-jsdoc48.sh` — 23 × 2 | 갈린 칸 **`10 / 23`** · 코드까지 **`7 / 23`** |
| ★ 자기검사 | `EXTRA=--bogusOpt` 로 두 격자 | 둘 다 **`exit 4`** |
| ★★ `strict` 기본값 | `nia48.js` × 네 설정 × 두 판 | 안 적은 줄만 갈림 |
| ★★ 방출 | `dts48.js` · `emit48.js` | `.d.ts` 가 판마다 다름 · 오류가 있어도 방출 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **3번의 갈린 칸 열**(7.0.2 의 JSDoc 해석) — 7.x 가 오르면 가장 먼저 다시 던질 자리다.
- ★★ **`.d.ts` 의 `declare`·순서**(4번) · **`strict` 기본값**(2번).

**안 돌려 본 것**

- ★★ **공식 변경 목록** — 출처를 확인하지 못했다(외부 네트워크 금지).
- ★ 여러 파일의 CommonJS(`exports.x`) · `@augments`·`@implements`·`@import` · 생성자 함수를 `class` 로 바꾼 판.
