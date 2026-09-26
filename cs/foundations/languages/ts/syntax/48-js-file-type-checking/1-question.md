# ts/syntax/48 — JS 파일 타입 검사 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **48 은 36 에서 온다** — [**36번 주제**](../36-type-only-imports-and-exports/)가 방출 규칙을 쟀다. JSDoc 없는 매개변수는 [**42번 주제**](../42-implicit-any-and-catch-variables/), `.d.ts` 는 [**37번 주제**](../37-writing-declaration-files/)와 잇는다.
> 그 자리의 타입은 `/** @type {null} */ const p = …;` 의 `TS2322` 메시지에서 읽는다 — **그 메시지가 답**이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3** 을 **읽기만** 해서 썼다(환경변수 `TSC_OLD`).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 탐침 아홉 × 설정 셋 × 두 판 (예측)

- 아래 격자에서 칸마다 어떤 진단 코드가 나는가? A 열과 B 열이 갈리는 칸은 몇 개이고, 두 판이 갈리는 탐침은?

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

### 2. `strict` 를 적지 않으면 (예측)

- 아래를 두 판에 `--allowJs --checkJs` 로 던지되 `strict` 를 (안 적음 · `--strict` · `--strict false` · `--strict --noImplicitAny false`) 로 바꾸면 줄마다 무엇이 나는가?

```js
// nia48.js
function add(a, b) {
    return a + b;
}
console.log(add(1, 2));
```

### 3. JSDoc 꼴 스물셋 × 두 판 (예측)

- 아래 격자에서 칸마다 `p` 의 타입과 진단은 무엇인가? 두 판이 갈리는 칸은 어느 것인가?

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

### 4. JSDoc 에서 `.d.ts` (예측)

- 아래를 두 판에서 `--allowJs --declaration --emitDeclarationOnly --strict false` 로 방출하면 `.d.ts` 에 무엇이 나오고, 두 판의 `.d.ts` 는 같은가?

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

### 5. 검사 오류와 방출 (예측)

- 아래를 `--allowJs --checkJs` 로 방출하면 `.js` 가 나오는가? `node` 는 무엇을 찍는가? `--noEmitOnError` 를 붙이면?

```js
// emit48.js
/** @param {number} n */
function double(n) {
    return n * 2;
}
console.log(double("2"));
```

### 6. `allowJs` 만의 진단 0줄 (왜)

- `allowJs` 만 켠 설정에서 「진단 0줄」은 무엇을 뜻하나? 이 문서는 그 뜻을 어느 창으로 확인했나?

### 7. 두 주석 스위치가 한 파일에 (경계)

- 파일 첫 줄에 `// @ts-check`, 둘째 줄에 `// @ts-nocheck` 가 있으면 1번 격자의 어느 칸이 그 경우이고, 어느 쪽이 이겼나?

### 8. 「사라진 특례」라는 말 (경계)

- 3번 격자만으로 「7.0 에서 사라진 특례」 목록을 세울 때 이 문서가 말할 수 **없는** 것은 무엇인가? 목록의 칸을 「진단이 새로 난 칸」과 「뜻만 바뀐 칸」과 「표시만 바뀐 칸」으로 가르면?

### 9. 7.0 이행 준비 (왜)

- 5.x 에서 `checkJs` 로 깨끗한 코드베이스를 7.0 으로 올리기 전에 무엇을 grep 하고, 걸린 자리는 어떻게 고치겠나?

### 10. 42·37·02편과 잇기 (연결)

- 1번의 `j1`, 4번의 `.d.ts`, 5번의 방출은 각각 42편·37편·02편의 어느 결론이 JS 파일에서도 성립함을 보이나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
