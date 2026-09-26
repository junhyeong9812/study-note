# ts/syntax/27 — 템플릿 리터럴 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **27 은 26 과 JS 28 에서 온다** — [**26번 주제**](../26-mapped-types/)의 `as` 자리,
> 그리고 JS 갈래의 **값** 템플릿 리터럴과 **UTF-16**(JS 04번)을 떠올리지 못하면 3·4번이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · 비교용 `tsc` **5.9.3**(이 머신의 다른 프로젝트에 깔려 있던 것을 읽기만 했다).
> 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — 템플릿 리터럴 타입과 내장 문자열 조작은 **4.1** 이다.
>
> ★★★ **계산된 타입을 눈으로 보는 법** — 블록에 `const probe: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 3·4번의 소스에는 `Same<A, B>` 가 끼어 있다 — 글자를 직접 찍지 않고 `"same"`/`"different"` 두 낱말로만 답하게 하는 비교다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ 이 주제의 **본체 창은 2창(`null` 탐침)이고**, README 의 과녁(4번)은 **같은 파일을 두 판에 던진 대조**가 본체다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 빈칸에 유니온과 넓은 타입을 넣으면 (예측)

```ts
// ex.27a.ts
// 템플릿 리터럴 타입 -- 유니온을 끼우면 · 넓은 타입을 끼우면
type Side = "top" | "bottom";
type Edge = "left" | "right";
const t1: null = null as unknown as `${Side}-${Edge}`;
const t2: null = null as unknown as `${Side | Edge}!`;
const t3: null = null as unknown as `id-${1 | 2 | true | null}`;
const t4: null = null as unknown as `${string}-${Side}`;

type NumId = `id-${number}`;
const n1: NumId = "id-42";
const n2: NumId = "id-abc";
let loose: string = "id-7";
const n3: NumId = loose;
console.log(t1, t2, t3, t4, n1, n2, n3);
```

- 4·5·6·7행이 각각 무엇을 뱉는가? 4행은 **몇 개**로 펼쳐지는가?
- 10·11·13행 중 **진단이 나는 줄**은 어느 것인가?

### 2. 내장 문자열 조작 (예측)

```ts
// ex.27b.ts
// 내장 문자열 조작 -- Uppercase · Lowercase · Capitalize · Uncapitalize
const c1: null = null as unknown as Uppercase<"hello">;
const c2: null = null as unknown as Capitalize<"hello world">;
const c3: null = null as unknown as Uncapitalize<"URL">;
const c4: null = null as unknown as Lowercase<"MiXeD">;
const c5: null = null as unknown as Capitalize<"get" | "set">;
const c6: null = null as unknown as Uppercase<"\u00DF">;
const c7: null = null as unknown as Uppercase<"\uFB01">;
const c8: null = null as unknown as Capitalize<"가나">;
const c9: null = null as unknown as Uppercase<string>;

let shout: Uppercase<string> = "ABC";
shout = "abc";
console.log(c1, c2, c3, c4, c5, c6, c7, c8, c9, shout);
```

- 3행 `Capitalize<"hello world">` 는 무엇인가?
- 7·8행의 두 글자(U+00DF · U+FB01)를 `Uppercase` 에 넣으면 **글자 수**는 어떻게 되는가?
- 12·13행 중 어느 쪽이 막히는가?

### 3. 한 글자는 무엇인가 (예측)

```ts
// ex.27c.ts
// infer 로 문자열 쪼개기 -- 한 글자는 무엇인가
type Head<S extends string> = S extends `${infer C}${string}` ? C : never;
type Tail<S extends string> = S extends `${string}${infer R}` ? R : never;
type Len<S extends string, A extends unknown[] = []> =
    S extends `${string}${infer R}` ? Len<R, [...A, 1]> : A["length"];
type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? "same" : "different") : "different";

const n1: null = null as unknown as Len<"abc">;
const n2: null = null as unknown as Len<"가나다">;
const n3: null = null as unknown as Len<"\u{1F600}">;
const n4: null = null as unknown as Len<"e\u0301">;
const h1: null = null as unknown as Same<Head<"\u{1F600}x">, "\u{1F600}">;
const h2: null = null as unknown as Same<Head<"\u{1F600}x">, "\uD83D">;
const h3: null = null as unknown as Same<Tail<"\u{1F600}x">, "x">;
console.log(n1, n2, n3, n4, h1, h2, h3);
```

- 8\~11행의 `Len` 은 각각 몇인가? 10행(U+1F600 하나)과 11행(`e` + U+0301)을 특히 따로 적어라.
- 12·13·14행은 `"same"` 인가 `"different"` 인가?

### 4. 같은 파일을 옛 판에 던지면 (예측)

```bash
# ts26b-cmp59.sh
#!/usr/bin/env bash
# 같은 파일을 두 판의 tsc 로 던진다 -- 7.0.2 와, 이 머신의 다른 프로젝트에 깔려 있던 5.9.3
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
echo "== tsc $(tsc --version)"
tsc --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
echo "== node OLD $(node "$OLD" --version)"
node "$OLD" --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
```

- 3번의 일곱 줄 중 **5.9.3 에서 답이 바뀌는 줄**은 어느 것인가? 각각 무엇으로 바뀌는가?
- 두 판의 **종료 코드**는 같은가?

### 5. 곱을 키워 가면 (예측)

```bash
# ts26b-union.sh
#!/usr/bin/env bash
# 템플릿 리터럴이 유니온을 곱할 때 -- 원소 수 x 자리 수를 바꿔 가며 TS2590 을 받는다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
blocked=0; total=0
printf '%-6s %-6s %-8s %s\n' 원소 자리 곱 결과
for pair in 10:4 10:5 2:16 2:17 46:3 47:3 316:2 317:2; do
  b=${pair%:*}; n=${pair#*:}
  u=$(for ((i=0;i<b;i++)); do printf '"k%d"' "$i"; ((i<b-1)) && printf ' | '; done)
  t='`'; for ((i=0;i<n;i++)); do t="$t\${U}"; done; t="$t\`"
  { echo "type U = $u;"; echo "type P = $t;"; echo 'declare const p: P;'; echo 'export { p };'; } > "$D/p.ts"
  out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1); rc=$?
  case "$out" in *TS2590*) mark="TS2590 exit=$rc"; blocked=$((blocked+1));; '') mark="OK     exit=$rc";; *) mark="OTHER  exit=$rc";; esac
  total=$((total+1))
  printf '%-6s %-6s %-8s %s\n' "$b" "$n" "$((b**n))" "$mark"
done
echo "막힌 칸 $blocked / $total"
```

- 여덟 줄 중 **어느 줄**이 막히는가?
- 원소 2 개 × 16 자리와 원소 10 개 × 5 자리 중 어느 쪽이 먼저 막히는가? **무엇이 축**인가?

### 6. 어떤 문자열이 `${number}` 에 드나 (예측)

```bash
# ts26b-numstr.sh
#!/usr/bin/env bash
# `${number}` 에 드는 문자열 -- tsc 의 멤버십 대입과 JS 의 Number() 를 나란히 둔다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
samples=('42' '1e3' '0x1F' '0b11' '.5' '-0' ' 7' '7 ' ' ' '' 'abc' 'Infinity' 'NaN' '1_000')
{ echo 'type N = `${number}`;'
  i=0; for s in "${samples[@]}"; do printf 'export const v%d: N = "%s";\n' "$i" "$s"; i=$((i+1)); done; } > "$D/n.ts"
out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/n.ts" 2>&1)
split=0; total=0; i=0
printf '%-12s %-8s %s\n' '문자열' 'tsc' 'Number.isFinite(Number(s))'
for s in "${samples[@]}"; do
  line=$((i+2))
  case "$out" in *"n.ts($line,"*) t=TS2322;; *) t=OK;; esac
  j=$(node -e 'console.log(Number.isFinite(Number(process.argv[1])))' -- "$s")
  if [ "$t" = OK ]; then tv=true; else tv=false; fi
  total=$((total+1)); if [ "$tv" != "$j" ]; then split=$((split+1)); fi
  printf '%-12s %-8s %s\n' "\"$s\"" "$t" "$j"
  i=$((i+1))
done
echo "tsc 와 Number() 가 갈린 칸 $split / $total"
```

- `" 7"`·`" "`·`""`·`"0x1F"` 는 각각 통과하는가?
- tsc 와 `Number()` 가 **갈리는 칸**은 어느 것인가?

### 7. 빈칸 두 개에 유니온을 넣을 때 (왜)

- 빈칸 두 개에 유니온을 넣으면 **왜 그 개수**가 나오는가? [**24번 주제**](../24-conditional-types-and-distribution/)의 무엇과 같은 집안인가?
- `string` 을 넣으면 **왜 펼치지 않는가**?

### 8. `--strict` 를 끄면 한 원소가 사라지는 까닭 (왜)

- 1번 6행을 `--strict false` 로 던지면 무엇이 달라지는가? 왜 그런가?

### 9. 코드 포인트와 그래핌 (경계)

- 7.0 의 `infer` 가 맞춘 단위는 **코드 유닛 · 코드 포인트 · 그래핌** 중 무엇인가?
- 사람 눈의 글자 수를 타입으로 세려 하면 **어디서 어긋나는가**?

### 10. `TS2590` 을 어떻게 읽을 것인가 (경계)

- 경계 크기를 **외워서 쓰면 안 되는 이유**는 무엇인가?
- `TS2590` 은 「느리다」는 뜻인가?

### 11. JS 의 값 템플릿 리터럴·UTF-16 과 잇기 (연결)

```js
// cp27.mjs
// 같은 글자를 JS 는 몇 개로 세나
const samples = [["smile", "\u{1F600}"], ["accent", "e\u0301"], ["hangul", "가나다"]];
const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
for (const [name, s] of samples) {
    const graphemes = [...seg.segment(s)].length;
    console.log(name, "length", s.length, "spread", [...s].length, "graphemes", graphemes);
}
```

- 이 `.mjs` 가 찍는 세 수(`length`·`spread`·`graphemes`) 중 **7.0 의 `infer` 와 같은 것**은 어느 것인가?
- `Uppercase` 와 JS 의 `toUpperCase` 는 2번의 두 글자에서 **같은 답**을 냈는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 판의 변경** · **구현(tsc 7.0.2) 층** · **이 판의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
