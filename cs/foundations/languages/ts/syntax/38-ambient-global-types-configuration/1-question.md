# ts/syntax/38 — 앰비언트·전역 타입 구성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **38 은 37 에서 온다** — [**37번 주제**](../37-writing-declaration-files/)가 「`export` 없는 `.d.ts` 는 전역」 · 「범위는 함께 컴파일한 파일」을 이미 쟀다.
> 여기서는 그 전역 `.d.ts` 가 **어떤 설정으로 컴파일에 들어오나** — `types`·`typeRoots`·`lib` 를 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · **v20.19.6**(환경변수 `NODE20`). 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ `@types` 패키지는 **설치하지 않고** `index.d.ts` 한 장을 둔 디렉토리로 흉내 냈다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 선언 자리 둘 × `types` 셋 × 세 판 (예측)

```bash
# ts38b-vis38.sh
#!/usr/bin/env bash
# 전역 선언 한 장(x38)을 두 자리에 두고 types 를 세 가지로 -- 판 셋에서 use38.ts 가 그 이름을 보나
# 칸마다 디렉토리를 따로 만든다(7.0.2 는 위쪽 tsconfig.json 을 찾아 TS5112 를 낸다)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
places=(
  "node_modules/@types${T}node_modules/@types/x38${T}"
  "typeRoots ./types${T}types/x38${T}\"typeRoots\": [\"./types\"], "
)
kinds=(
  "(키 없음)${T}"
  "[]${T}\"types\": [], "
  "[\"x38\"]${T}\"types\": [\"x38\"], "
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-22s %-10s %-8s %-8s %s\n' "선언의 자리" "types" "7.0.2" "5.9.3" "4.9.5"
split=0; total=0; all=""; i=0
for p in "${places[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$p"); if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $p"; exit 3; fi
  IFS="$T" read -r pname pdir proot <<< "$p"
  for k in "${kinds[@]}"; do
    n=$(awk -F'\t' '{print NF}' <<< "$k"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $k"; exit 3; fi
    IFS="$T" read -r kname kopt <<< "$k"
    i=$((i+1)); c="$D/c$i"; mkdir -p "$c/$pdir"
    echo 'declare const X38_GLOBAL: string;' > "$c/$pdir/index.d.ts"
    printf '{ "compilerOptions": { %s%s"noEmit": true }, "include": ["use38.ts"] }\n' "$proot" "$kopt" > "$c/tsconfig.json"
    printf 'const probe: null = X38_GLOBAL;\nexport {};\n' > "$c/use38.ts"
    a=$(cd "$c" && tsc --pretty false -p tsconfig.json 2>&1 | codes)
    b=$(cd "$c" && node "$OLD" --pretty false -p tsconfig.json 2>&1 | codes)
    e=$(cd "$c" && node "$V49" --pretty false -p tsconfig.json 2>&1 | codes)
    printf '%-22s %-10s %-8s %-8s %s\n' "$pname" "$kname" "${a:-OK}" "${b:-OK}" "${e:-OK}"
    for x in "$a" "$b" "$e"; do case $x in *TS5*) echo "★ 설정 진단이 칸에 들었다($x) -- 격자를 믿지 마라"; exit 4 ;; esac; done
    all="$all|${a:-OK}|${b:-OK}|${e:-OK}"; total=$((total+1)); [ "$a" != "$b" ] && split=$((split+1))
  done
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "칸에 나온 코드 가짓수 $kinds_seen · 7.0.2 와 5.9.3 이 갈린 행 $split / $total"
```

- 여섯 행 × 세 판(7.0.2 · 5.9.3 · 4.9.5) 열여덟 칸에서 탐침은 각각 `TS2304` 인가 `TS2322` 인가? 7.0.2 와 5.9.3 이 갈리는 행은 어느 것인가?

### 2. `types: []` 인 프로젝트에서 (예측)

```ts
// index.d.ts
declare const X38_GLOBAL: string;
```

```ts
// a38i.ts
import "x38";
const probeA: null = X38_GLOBAL;
export {};
```

```ts
// a38r.ts
/// <reference types="x38" />
const probeA: null = X38_GLOBAL;
export {};
```

```ts
// b38.ts
const probeB: null = X38_GLOBAL;
export {};
```

```text
===== 소스: p38/tsconfig.json =====
{
    "compilerOptions": { "types": [] },
    "files": ["a38i.ts", "b38.ts"]
}
===== 소스: p38/tsconfig.ref.json =====
{
    "compilerOptions": { "types": [] },
    "files": ["a38r.ts", "b38.ts"]
}
===== 소스: p38/tsconfig.star.json =====
{
    "compilerOptions": { "types": ["*"] },
    "files": ["b38.ts"]
}
```

- `cd p38 && tsc --noEmit -p <세 설정>` 을 7.0.2 와 5.9.3 으로 던지면 설정마다 어느 파일에 무엇이 나는가? 특히 `b38.ts` 의 탐침은?

### 3. 끌어온 줄을 방출해서 돌리면 (예측)

```js
// run38.cjs
// 방출된 a38i.js 를 부른다 -- require 가 던지면 오류 코드만 찍는다
try {
    require("./e38/a38i.js");
    console.log("loaded");
} catch (e) {
    console.log(e.constructor.name, e.code);
}
```

- `cd p38 && tsc -p tsconfig.json --module commonjs --outDir e38` 이 쓴 `e38/a38i.js` 에는 무엇이 남고, `node run38.cjs` 는 무엇을 찍는가?

### 4. `lib` 값 다섯 (예측)

```ts
// lib38.ts
const el = document.body;
const last = [1, 2, 3].at(-1);
const sorted = [3, 1, 2].toSorted();
console.log(last, sorted, el);
export {};
```

- `--lib` 를 `(안 줌)` · `es2020` · `es2022` · `es2023` · `es2023,dom` 으로 바꿔 7.0.2 와 5.9.3 에 던지면 줄마다 어느 코드가 나는가? `console` 줄은?

### 5. 같은 방출물, node 두 판 (예측)

```ts
// rt38.ts
const xs = [3, 1, 2];
try {
    console.log("[1]", xs.toSorted());
} catch (e) {
    console.log("[1]", (e as Error).constructor.name, (e as Error).message);
}
console.log("[2]", xs);
```

- 7.0.2 로 `--noEmit` 하면 진단이 나는가? `tsc --outDir e38r rt38.ts` 로 방출한 `.js` 를 node v18.19.1 과 v20.19.6 에서 돌리면 `[1]`·`[2]` 는 각각 무엇인가?

### 6. 전역을 더하는 세 파일 (예측)

```ts
// modg38.ts
declare global {
    var FROM_MODULE: number;
}
export {};
```

```ts
// scrg38.ts
declare global {
    var FROM_SCRIPT: number;
}
```

```ts
// scrv38.ts
declare var FROM_PLAIN: number;
```

```ts
// useg38.ts
const p1: null = FROM_MODULE;
const p2: null = FROM_PLAIN;
export {};
```

- `tsc --noEmit useg38.ts modg38.ts scrv38.ts` · `useg38.ts` 혼자 · `scrg38.ts` 혼자 — 셋은 각각 무엇을 내는가?

### 7. 판을 올린 프로젝트의 전역 이름 (왜)

- `types` 키가 없는 `tsconfig.json` 으로 5.9.3 에서 `describe`·`process` 같은 전역을 쓰던 프로젝트를 7.0.2 로 그대로 던진다. 1번 격자로 무엇이 달라지는지 설명하고, 판을 안 타게 만드는 한 줄을 적어라.

### 8. `typeRoots` 와 `types` (경계)

- 1번의 둘째 묶음(`typeRoots ./types`)과 첫째 묶음을 칸마다 견주면 어떻게 되는가? 두 옵션이 각각 **무엇을** 정하는지로 설명하라.

### 9. `console` 이 막히는 자리 (왜)

- 이 컴파일에는 `@types/node` 가 없다. 그렇다면 `console` 의 선언은 어디서 오는가? 4번의 `console` 줄 결과를 그것으로 설명하라.

### 10. 「이 파일에서만」 (경계)

- 「한 파일에서만 그 전역을 쓰겠다」는 뜻은 2번의 `import "x38"` 과 `/// <reference types="x38" />` 중 어느 쪽으로 이뤄지는가? 두 줄이 **값 쪽**에서 어떻게 다를 수 있는지도 3번으로 답하라.

### 11. 37·14·36 과 잇기 (연결)

- 2번의 `b38.ts` 결과는 37편 3절의 어느 문장과 같은 기제인가?
- 14편 6절의 `TS2591` 문구가 가리키는 고칠 자리는 1번 격자의 어느 칸인가?
- 3번 방출물의 남은 한 줄은 36편 1절의 어느 규칙인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
