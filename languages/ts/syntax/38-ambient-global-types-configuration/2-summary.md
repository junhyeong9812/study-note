# ts/syntax/38 — 앰비언트·전역 타입 구성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `types`](https://www.typescriptlang.org/tsconfig/#types)(「By default `types` is set to `[]`. For versions below TypeScript 6.0, by default all visible `@types` packages are included」) ·
> [`typeRoots`](https://www.typescriptlang.org/tsconfig/#typeRoots)(지정하면 **그 아래 패키지만**) · [`lib`](https://www.typescriptlang.org/tsconfig/#lib)(내장 JS API·브라우저 환경의 선언 파일을 고른다).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다.
> ★ 레퍼런스는 `types` 의 기본값 변화를 **6.0** 으로 적는다. 이 머신에는 6.x 가 없어 **7.0.2 와 5.9.3 사이**에서만 갈림을 봤다 — 「6.0 에서 바뀌었다」는 **문서의 말**이지 이 문서가 잰 것이 아니다.
> **실행 검증** — 본판은 아래다. ★ 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**. node 20 은 **`NODE20`**(nvm 판)이다.

```text
===== tsc --version · node --version · "$NODE20" --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
v20.19.6
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 「전역 가시성 격자」(선언 자리 둘 × `types` 셋 × 세 판 — `null` 탐침이 `TS2304` 인가 `TS2322` 인가)이고, 둘째 기둥은 3창(방출물 + `node` 두 판)이다.**
> ★★★ **38 은 37 에서 온다.** [**37번 주제**](../37-writing-declaration-files/)가 「`export` 없는 `.d.ts` 는 **전역**에 보인다 · 범위는 **함께 컴파일한 파일** · `skipLibCheck` 가 `TS2304`·`TS2403` 을 숨긴다 · 충돌한 전역 `var` 는 **파일 순서**로 타입이 바뀐다」를 **이미 쟀다** — 인용하고 다시 재지 않는다.
> 여기는 그 「컴파일에 든 전역 `.d.ts`」가 **어떤 설정으로 컴파일에 들어오나** — `types`·`typeRoots`·`lib` 쪽이다.
> ★★ **설정 실험은 칸마다 디렉토리를 따로** 만들었다 — 7.0.2 는 **위쪽 디렉토리에** `tsconfig.json` 이 있으면 파일을 직접 줘도 `TS5112` 로 검사를 거부한다(35편 6절 블록). 격자 스크립트는 **설정 진단(`TS5…`)이 칸에 들면 멈추고, 모든 칸이 같은 코드면 멈춘다.**
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ JSON(`tsconfig.json`)은 주석을 달 수 없어 **캡처가 `===== 소스: 경로 =====` 배너를 찍어** 싣는다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · `null` 탐침이 말하는 타입 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자 둘의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **판에 매인다** | ★★★ `types` **키 없음**의 뜻 — 7.0.2 와 5.9.3·4.9.5 가 **갈렸다**(1절) | 결론 자체다 |
| **판에 매인다** | ★★ 종료 코드 — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3 은 `2` | 격자는 **진단 코드로** 갈랐다 |
| **호스트에 매인다** | ★★★ 4절 — 같은 방출물이 **node v18 에서 `TypeError`, v20 에서 정상** | 결론 자체다 — `lib` 는 호스트에 대한 **주장**이다 |
| **안 흔들린다** | `node` 의 오류 | 예외는 **타입과 메시지** 또는 **`e.code`** 만 찍었다(절대 경로가 박히는 문구는 싣지 않았다) |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | 질문은 「**보이나**」다 |
| **안 잰 것** | `types: []` 가 줄이는 검사 **시간** | **재지 않았다** — 이 문서는 **무엇이 보이나**만 봤다 |

## 한눈에 — 쉽게 말하면

**전역 타입은 「게시판에 붙은 공지」다. 37편은 공지를 **어떻게 쓰나**(`export` 없이)를 봤고, 이 편은 **어느 공지를 게시판에 붙이나**를 본다. `types` 는 「이 공지들만 붙여라」는 목록이고, 7.0 은 그 목록을 **빈 칸으로** 시작한다 — 예전에는 「창고(`node_modules/@types`)에 있는 것 전부」였다.**

| 비유 | 실체 |
|---|---|
| **게시판** | 컴파일 전체의 **전역 이름 공간** |
| **창고에 쌓인 공지 묶음** | `node_modules/@types/<이름>` — 설치된 타입 패키지 |
| ★★★ 예전: **창고에 있으면 다 붙인다** | 5.9.3·4.9.5 — `types` 키가 없으면 보이는 `@types` **전부**(1절) |
| ★★★ 7.0: **목록에 적은 것만 붙인다**(목록은 비어 시작) | 7.0.2 — `types` 키가 없으면 **`[]` 와 같다**(1절) |
| 「창고를 다른 곳으로」 | `typeRoots` — 찾는 자리를 바꾼다(1절 둘째 행) |
| ★★ 공지 한 장을 **직접 들고 와서** 붙인다 | `import "x38"` · `/// <reference types>` — **목록과 무관하게** 들어오고, **모든 파일**이 본다(2절) |
| **건물 기본 안내판**(엘리베이터·비상구) | `lib` — 언어·호스트의 내장 API(`Array`·`document`·`console`)(3·4절) |
| ★★★ 안내판에 「**3층에 식당**」 — 실제 건물엔 없다 | `lib` 가 `toSorted` 를 약속하는데 **node v18 에는 없다** — `TypeError`(4절) |

- ★★★ 한 줄로 — 「**전역 타입은 컴파일에 든 선언의 합이다. `types`·`typeRoots` 는 `@types` 중 무엇을 넣을지, `lib` 는 내장 API 중 무엇을 넣을지 정한다. 7.0 은 `types` 를 비워서 시작하고, `lib` 는 실행 호스트와 대조되지 않는다.**」

```text
  전역 이름 공간에 선언이 들어오는 길 — 이 문서가 던진 넷

  컴파일 목록에 든 .d.ts (include·명령줄)     늘 들어온다                  (37편 3절)
  node_modules/@types/x · typeRoots 아래     types 가 허락할 때만          ★ 7.0: 키 없음 = []   (1절)
  import "x" · /// <reference types="x" />    types 와 무관하게 — 모든 파일이 본다   (2절)
  lib (es2020 · dom …)                        내장 API — 호스트와 대조 안 된다      (3·4절)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 설치된 `@types` 의 전역이 언제 보이나** — 선언 자리 둘 × `types` 셋 × 세 판(1절). 7.0 의 **`types: []` 기본값**이 무엇을 바꿨나.
2. **★★ `types` 를 비워 두고도 전역이 들어오는 길** — `import "x"` · `/// <reference types>` · `types: ["*"]`(2절). 들어온 전역은 **어느 파일에** 보이나.
3. **★★★ `lib` 는 무엇을 약속하고 무엇을 약속하지 않나** — `lib` 값 다섯 × 판 둘(3절) · 그 약속을 **node 두 판**이 지키나(4절) · `declare global` 의 자리(5절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **전역 가시성 격자** | 선언 자리 둘 × `types` 셋 × 세 판 — 칸마다 **디렉토리와 `tsconfig.json` 을 따로** | 칸마다 진단 코드 | **본체**(1절) |
| ★★ **2창 — `null` 탐침** | 보였을 때 **그 이름의 타입**(`string`) | 계산된 것 | 1·2·5절 — `TS2304`(안 보임) 과 `TS2322`(보임)를 한 줄이 가른다 |
| ★★ **`lib` 격자** | `lib` 값 다섯 × 판 둘 — 줄마다 코드 | 칸마다 진단 코드 | 3절 |
| ★★★ **3창 — 방출물 + `node` 두 판** | 타입이 약속한 전역·메서드가 **실행 때 있나** | 실행 결과 | **둘째 기둥**(2·4절) |
| ★ **부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — | — |
| ★ **부적용 — 4창(종료 코드 격자)** | 한계를 칠 것이 없다 | — | — |

비용 — 격자 둘(여섯 행 × 세 판 · 다섯 행 × 두 판) + 프로젝트 하나를 설정 셋으로 × 두 판 + 방출 둘 · `node` 셋.

```text
  이 주제의 축 — 「누가 전역에 넣나」

  컴파일러의 기본값     types 키가 없을 때     5.9.3 이하: 보이는 @types 전부   7.0.2: 아무것도 (= [])
  설정 파일             types · typeRoots      적은 것만 · 찾는 자리
  소스 한 줄            import · reference      ★ 설정을 건너뛰고 들어온다
  lib                   내장 API 선언          ★ 실행 호스트는 묻지 않는다
```

### (1) ★★★ 전역 가시성 격자 — `types` 키가 없을 때 판마다

**언제 쓰나** — 5.x 프로젝트를 7.0 으로 올렸더니 `describe`·`process` 같은 전역이 갑자기 `TS2304` 일 때.

`@types` 패키지를 **설치하지 않고** 흉내 냈다 — `index.d.ts` 한 장(`declare const X38_GLOBAL: string;`, `export` 없음 — 37편 3절의 **전역 선언 파일**)을 두 자리에 둔다.
탐침은 `const probe: null = X38_GLOBAL;` 한 줄 — **안 보이면 `TS2304`, 보이면 `TS2322`**(타입 `string` 이 `null` 에 안 들어간다).

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

```text
===== bash ts38b-vis38.sh (sh exit=0) =====
선언의 자리       types      7.0.2    5.9.3    4.9.5
node_modules/@types    (키 없음) TS2304   TS2322   TS2322
node_modules/@types    []         TS2304   TS2304   TS2304
node_modules/@types    ["x38"]    TS2322   TS2322   TS2322
typeRoots ./types      (키 없음) TS2304   TS2322   TS2322
typeRoots ./types      []         TS2304   TS2304   TS2304
typeRoots ./types      ["x38"]    TS2322   TS2322   TS2322

칸에 나온 코드 가짓수 2 · 7.0.2 와 5.9.3 이 갈린 행 2 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`types` 키 없음** — 7.0.2 는 **`TS2304`**(안 보임), 5.9.3·4.9.5 는 **`TS2322`**(보임). **여섯 행 중 갈린 것은 이 두 행**(`2 / 6`)이다.
- ★★★ 7.0.2 의 「키 없음」 행은 **`[]` 행과 코드가 같다** — 레퍼런스의 「By default `types` is set to `[]`」가 이 판에서 그대로 재현됐다.
- ★★ **`[]`** — 세 판 모두 `TS2304`. **`["x38"]`** — 세 판 모두 `TS2322`. **명시한 값은 판을 타지 않는다.**
- ★★ **`typeRoots`** 행은 `node_modules/@types` 행과 **칸마다 같다** — `typeRoots` 는 **찾는 자리**만 바꿨고, 넣을지 말지는 여전히 `types` 가 정했다.
- ★ 스크립트 마지막 줄의 **「코드 가짓수 2」** 는 자기검사다 — 모든 칸이 같은 코드였거나 `TS5…` 가 들었으면 **멈췄을 것**이다.

```text
  types 키가 없을 때 — 두 판의 「기본」

                    5.9.3 · 4.9.5                 7.0.2
  찾는 자리         node_modules/@types (또는 typeRoots)   같다
  넣는 것           ★ 거기 있는 패키지 전부          ★ 아무것도 — [] 와 같다
  고치는 법         —                             types 에 이름을 적는다 (["x38"])
                                                  또는 소스에서 끌어온다 (2절)
```

비용 — 7.0 으로 올리면 **테스트 러너·node 같은 전역 타입**이 한꺼번에 사라진다. 14편 6절의 `TS2591`(「… add 'node' to the types field in your tsconfig」)이 그 한 예다 — 진단 문구가 **고칠 자리(`types`)** 를 가리킨다.

### (2) ★★ `types: []` 인데 들어오는 길 — 그리고 들어오면 모든 파일이 본다

**언제 쓰나** — 「`types` 를 비웠는데 왜 이 전역이 보이지?」 · 「목록에 안 적고 한 파일에서만 쓰고 싶다」.

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

```text
===== cd p38 && tsc --pretty false --noEmit -p <tsconfig.json · tsconfig.ref.json · tsconfig.star.json> ; 각각 "$TSC_OLD" 로도 (sh exit=0) =====
---- 7.0.2 -p tsconfig.json
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.json
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 2)
---- 7.0.2 -p tsconfig.ref.json
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.ref.json
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 2)
---- 7.0.2 -p tsconfig.star.json
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.star.json
error TS2688: Cannot find type definition file for '*'.
  The file is in the program because:
    Entry point of type library '*' specified in compilerOptions
(exit 2)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`tsconfig.json`**(`types: []`) — `a38i.ts` 의 **`import "x38";`** 한 줄이 전역을 들여왔다. 그리고 **`b38.ts` 도 `TS2322`** — import 를 **안 한 파일**도 그 전역을 본다. 들어온 것은 파일이 아니라 **컴파일 전체의 전역**이다(37편 3절과 같은 기제).
- ★★ **`tsconfig.ref.json`** — `/// <reference types="x38" />` 도 **같은 결과**. `types` 목록을 건너뛰는 두 번째 길이다.
- ★★★ **`tsconfig.star.json`**(`types: ["*"]`) — 7.0.2 는 **`b38.ts` 가 봤다**(와일드카드 = 보이는 `@types` 전부). **5.9.3 은 `TS2688`**(「Cannot find type definition file for '*'.」) — 그 판에는 그런 값이 **없다.** ★ 레퍼런스의 `types` 항목은 `"*"` 를 **싣지 않는다** — 이 칸은 던져서만 안다.
- ★ 종료 코드 — 같은 진단에 7.0.2 `(exit 1)` · 5.9.3 `(exit 2)`. 진단 코드로 가른다.

`import "x38"` 은 **값 쪽 줄**이기도 하다 — 방출해서 node 로 돌린다.

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

```text
===== cd p38 && tsc --pretty false -p tsconfig.json --module commonjs --outDir e38 (tsc exit=2) =====
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
===== 방출된 e38/a38i.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("x38");
const probeA = X38_GLOBAL;
```

```text
===== cd p38 && node run38.cjs (node exit=0) =====
Error MODULE_NOT_FOUND
```

- ★★★ 방출물에 **`require("x38");`** 가 남았다 — 부작용 import 는 **지워지지 않는다**(36편 1절의 「`import "…"` 는 늘 남는다」).
- ★★★ node — **`Error MODULE_NOT_FOUND`**. `@types/x38` 은 **타입만** 있는 자리라 node 가 풀 `x38` 이 **없다.** 타입을 들여오려고 쓴 줄이 **실행 때 없는 모듈을 부른다.**
`/// <reference types>` 쪽도 같은 플래그로 방출한다.

```text
===== cd p38 && tsc --pretty false -p tsconfig.ref.json --module commonjs --outDir e38 (tsc exit=2) =====
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
===== 방출된 e38/a38r.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/// <reference types="x38" />
const probeA = X38_GLOBAL;
```

- ★★★ **`require` 가 없다** — 지시 주석은 **주석째** 남았을 뿐 값 쪽 줄이 아니다. 타입만 끌어올 목적이면 이쪽이 방출물에 **아무 호출도 안 남긴다.**

```text
  types: [] 를 건너뛰는 두 줄 — 들어온 뒤엔 같다

  import "x38";                     타입: 전역에 들어온다 · 모든 파일   값: require("x38") 가 남는다 → MODULE_NOT_FOUND
  /// <reference types="x38" />     타입: 전역에 들어온다 · 모든 파일   값: 주석으로 남을 뿐 — require 없음
  types: ["*"]                      7.0.2: 전부 · 5.9.3: TS2688
```

비용 — **한 파일의 한 줄이 컴파일 전체의 전역을 바꾼다.** 「이 파일에서만」은 성립하지 않는다.

### (3) ★★ `lib` 격자 — 내장 API 의 선언을 고른다

**언제 쓰나** — `document` 가 `TS2584` 거나, `.at()` 이 `TS2550` 일 때.

```ts
// lib38.ts
const el = document.body;
const last = [1, 2, 3].at(-1);
const sorted = [3, 1, 2].toSorted();
console.log(last, sorted, el);
export {};
```

```bash
# ts38b-lib38.sh
#!/usr/bin/env bash
# lib38.ts 를 lib 값 다섯 × 판 둘로 -- 줄마다 난 진단 코드(행 번호 · 코드)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
libs=("(안 줌)" "es2020" "es2022" "es2023" "es2023,dom")
cells() { grep -o '^lib38.ts([0-9]*,[0-9]*): error TS[0-9]*' | sed 's/^lib38.ts(\([0-9]*\),[0-9]*): error /\1:/' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-12s %-40s %s\n' "--lib" "7.0.2" "5.9.3"
all=""; split=0; total=0
for l in "${libs[@]}"; do
  if [ "$l" = "(안 줌)" ]; then fl=(); else fl=(--lib "$l"); fi
  ar=$(tsc --pretty false --noEmit "${fl[@]}" lib38.ts 2>&1); br=$(node "$OLD" --pretty false --noEmit "${fl[@]}" lib38.ts 2>&1)
  case "$ar$br" in *"error TS5"*) echo "★ 설정 진단이 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
  a=$(cells <<< "$ar"); b=$(cells <<< "$br")
  printf '%-12s %-40s %s\n' "$l" "${a:-OK}" "${b:-OK}"
  all="$all|${a:-OK}|${b:-OK}"; total=$((total+1)); [ "$a" != "$b" ] && split=$((split+1))
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "7.0.2 와 5.9.3 이 갈린 행 $split / $total"
```

```text
===== bash ts38b-lib38.sh (sh exit=0) =====
--lib        7.0.2                                    5.9.3
(안 줌)    OK                                       2:TS2550 3:TS2550
es2020       1:TS2584 2:TS2550 3:TS2550 4:TS2584      1:TS2584 2:TS2550 3:TS2550 4:TS2584
es2022       1:TS2584 3:TS2550 4:TS2584               1:TS2584 3:TS2550 4:TS2584
es2023       1:TS2584 4:TS2584                        1:TS2584 4:TS2584
es2023,dom   OK                                       OK

7.0.2 와 5.9.3 이 갈린 행 1 / 5
```

```text
===== tsc --pretty false --noEmit --lib es2020 lib38.ts (tsc exit=1) =====
lib38.ts(1,12): error TS2584: Cannot find name 'document'. Do you need to change your target library? Try changing the 'lib' compiler option to include 'dom'.
lib38.ts(2,24): error TS2550: Property 'at' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2022' or later.
lib38.ts(3,26): error TS2550: Property 'toSorted' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.
lib38.ts(4,1): error TS2584: Cannot find name 'console'. Do you need to change your target library? Try changing the 'lib' compiler option to include 'dom'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`--lib es2020`** — 넷 다 막혔다. `document`·`console` 은 **`TS2584`**(「… Try changing the 'lib' compiler option to include 'dom'.」), `.at`·`.toSorted` 는 **`TS2550`**(「… to 'es2022' or later.」·「… to 'es2023' or later.」).
- ★★★ **`console` 도 `dom` 에 있다** — `@types/node` 가 없는 이 컴파일에서 `console` 의 선언을 대 주는 것은 **`lib.dom`** 이었다. `lib` 를 좁히면 `console.log` 한 줄도 막힌다.
- ★★ `es2022` 는 `.at` 을, `es2023` 은 `.toSorted` 를 **더한다** — 줄이 하나씩 풀린다. `es2023,dom` 에서 0건.
- ★★★ **`(안 줌)`** — 7.0.2 는 **OK**, 5.9.3 은 `.at`·`.toSorted` 가 `TS2550`. **안 줬을 때의 `lib` 는 `target` 기본값을 따라가고**, 그 기본값이 판마다 다르다(02편 — 7.0.2 는 **es2025**, `es5` 는 제거). **갈린 행 `1 / 5`** 가 그 행이다.

비용 — `lib` 는 **목록**이라 하나를 적으면 기본 목록 전체를 **대체한다** — `es2020` 만 적은 칸에서 `dom` 이 빠진 것이 그것이다.

### (4) ★★★ `lib` 는 약속이다 — node 는 대조하지 않는다

**언제 쓰나** — 「tsc 가 통과시켰으니 그 메서드는 있다」를 믿기 전에.

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

```text
===== tsc --pretty false --noEmit rt38.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
(exit 0)
---- 5.9.3
rt38.ts(3,27): error TS2550: Property 'toSorted' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.
rt38.ts(5,49): error TS2339: Property 'name' does not exist on type 'Function'.
(exit 2)
```

```text
===== tsc --pretty false --outDir e38r rt38.ts (tsc exit=0) =====
===== 방출된 e38r/rt38.js =====
"use strict";
const xs = [3, 1, 2];
try {
    console.log("[1]", xs.toSorted());
}
catch (e) {
    console.log("[1]", e.constructor.name, e.message);
}
console.log("[2]", xs);
```

```text
===== node e38r/rt38.js ; 이어서 "$NODE20" 로 같은 것 (sh exit=0) =====
---- node v18.19.1
[1] TypeError xs.toSorted is not a function
[2] [ 3, 1, 2 ]
(exit 0)
---- node v20.19.6
[1] [ 1, 2, 3 ]
[2] [ 3, 1, 2 ]
(exit 0)
```

그림 해설 — 한 단계에 한 문장.

- ★★ 검사 — 7.0.2 는 **진단 0줄**(기본 `lib` 가 `toSorted` 를 싣는다). 5.9.3 은 `TS2550` 에 더해 **`TS2339`**(`name` — 기본 `lib` 가 **es5** 라 `Function.prototype.name` 도 없다).
- ★★ 방출 — `xs.toSorted()` 는 **그대로** 나왔다. tsc 는 메서드를 **바꿔 쓰지 않는다**(폴리필을 넣지 않는다).
- ★★★ **node v18.19.1** — **`[1] TypeError xs.toSorted is not a function`**. **node v20.19.6** — `[1] [ 1, 2, 3 ]`. **같은 `.js`** 가 호스트 판에 따라 갈렸다.
- ★★ `[2] [ 3, 1, 2 ]` — 둘 다 원본은 안 바뀌었다(`toSorted` 는 **복사본**을 준다 — v20 쪽에서 확인).

```text
  lib 의 약속과 호스트 — 37편 「.d.ts 는 주장이다」의 lib 판

  lib (기본, 7.0.2)     "Array 에 toSorted 가 있다"        ← tsc 가 믿는다 — 진단 0줄
  방출물                xs.toSorted()                     ← 그대로
  node v18.19.1         (없다)       → TypeError           ★ 대조한 사람이 없다
  node v20.19.6         (있다)       → [ 1, 2, 3 ]
```

비용 — `lib` 를 **실행 호스트의 판에 맞추는 것**은 사람 몫이다. 넓게 두면 v18 에서 터지고, 좁게 두면 쓸 수 있는 API 가 막힌다.

### (5) ★★ `declare global` — 모듈 안에서만 된다

**언제 쓰나** — 모듈 파일에서 전역을 하나 더하고 싶을 때.

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

```text
===== tsc --pretty false --noEmit <useg38.ts modg38.ts scrv38.ts · useg38.ts 혼자 · scrg38.ts 혼자> (sh exit=0) =====
---- useg38.ts modg38.ts scrv38.ts
useg38.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
useg38.ts(2,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
---- useg38.ts
useg38.ts(1,18): error TS2304: Cannot find name 'FROM_MODULE'.
useg38.ts(2,18): error TS2304: Cannot find name 'FROM_PLAIN'.
(exit 1)
---- scrg38.ts
scrg38.ts(1,9): error TS2669: Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.
(exit 1)
```

그림 해설 — 한 단계에 한 문장.

- ★★ **셋을 함께** — `FROM_MODULE`(모듈 안 `declare global`)·`FROM_PLAIN`(스크립트의 맨 `declare var`) 둘 다 **보였다**(`TS2322` 둘, 타입 `number`).
- ★★ **`useg38.ts` 혼자** — 둘 다 `TS2304`. 전역도 **컴파일에 든 파일**에서만 온다(37편 3절).
- ★★★ **`scrg38.ts`**(모듈이 **아닌** 파일의 `declare global`) — **`TS2669`**(「Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.」). 스크립트 파일은 **이미 전역**이라 `declare global` 로 감쌀 자리가 없다.

```text
  전역을 더하는 두 꼴 — 파일이 모듈이냐가 가른다

  스크립트(.ts · export 없음)     declare var X: T;                 ← 그대로 전역
  모듈(export 있음)               declare global { var X: T; }       ← 모듈 안에서 전역으로 빠져나간다
  스크립트 + declare global       TS2669
```

비용 — 모듈 파일에 `export {}` 한 줄이 **있느냐 없느냐**로 같은 선언이 에러가 되기도 하고 안 되기도 한다(33편 5절 · 37편 3절과 같은 `export` 스위치).

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  "types": ["x38"]                  x38 만 전역에 넣는다                        (1절)
  "types": []                       아무것도 안 넣는다 — 7.0.2 에서는 키 없음과 같다  (1절)
  "typeRoots": ["./types"]          @types 를 찾는 자리를 바꾼다                  (1절)
  "types": ["*"]                    7.0.2 — 보이는 것 전부 · 5.9.3 — TS2688       (2절)
  import "x38";                     types 와 무관하게 들여온다 — 방출에 남는다     (2절)
  /// <reference types="x38" />     types 와 무관하게 들여온다                    (2절)
  --lib es2023,dom                  내장 API 선언을 고른다 — 기본을 대체한다        (3절)
  declare global { var X: T; }      모듈 파일 안에서만                            (5절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `types` 가 막은 `@types` 의 전역 이름 | `TS2304` | 1절 |
| 5.9.3 에서 `types: ["*"]` | `TS2688` | 2절 |
| `lib` 에 `dom` 이 없는데 `document`·`console` | `TS2584` | 3절 |
| `lib` 판보다 새 메서드(`.at`·`.toSorted`) | `TS2550` | 3·4절 |
| 스크립트 파일의 `declare global` | `TS2669` | 5절 |

**규칙 불릿**

- ★★★ **7.0.2 에서 `types` 키가 없으면 `[]` 와 같다** — 5.9.3·4.9.5 는 **보이는 `@types` 전부**였다(1절).
- ★★ **`typeRoots` 는 찾는 자리, `types` 는 넣을 목록**이다(1절).
- ★★★ **`import "x"`·`/// <reference types="x" />` 는 `types` 와 무관하게 들여오고, 들어온 전역은 모든 파일이 본다**(2절).
- ★★ **`lib` 는 목록이라 적으면 기본을 대체한다** — `dom` 이 빠지면 `console` 까지 막힌다(3절).
- ★★★ **`lib` 는 호스트와 대조되지 않는다** — 같은 방출물이 node v18 에서 `TypeError`(4절).
- ★★ **`declare global` 은 모듈 안에서만** — 스크립트면 `TS2669`(5절).

## 어디서 틀리나

- ★★★ 「**`types` 를 안 적었으니 기본값 — 설치된 것은 다 보인다**」 — **5.9.3 까지의 기본값**이다. 7.0.2 는 **아무것도 안 넣는다**(1절 `2 / 6`).
- ★★ 「**`typeRoots` 를 주면 그 아래가 다 들어온다**」 — 7.0.2 에서는 **`types` 가 여전히 `[]`** 라 아무것도 안 들어온다(1절 둘째 묶음).
- ★★★ 「**`import "x"` 한 파일에서만 그 전역이 보인다**」 — **컴파일 전체**다. 안 한 `b38.ts` 도 봤다(2절).
- ★★★ 「**타입 패키지를 `import "x"` 로 끌어오면 된다**」 — 방출물에 **`require("x")`** 가 남아 node 가 `MODULE_NOT_FOUND`(2절).
- ★★ 「**`lib: ["es2020"]` 은 ES 기능만 줄인다**」 — **`dom` 이 빠져** `document`·`console` 이 `TS2584`(3절).
- ★★★ 「**tsc 가 `toSorted` 를 통과시켰으니 실행된다**」 — `lib` 는 **약속**이고 node v18 에는 **없다**(4절).
- ★ 「**`declare global` 은 어디서나 쓴다**」 — 스크립트 파일이면 `TS2669`(5절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **문서(TSConfig 레퍼런스)** | `types` 기본값 `[]`(6.0 부터라고 적는다) · `typeRoots` 는 그 아래만 · `lib` 는 내장 API 선언 | 기준 소스 |
| **★★★ 판 격자** | `types` 키 없음 — 7.0.2 `[]` · 5.9.3·4.9.5 **보이는 `@types` 전부** | 1절 `2 / 6` |
| **★ 판 격자** | `types: ["*"]` — 7.0.2 받는다 · 5.9.3 `TS2688` | 2절 |
| **★ 판 격자** | `lib` 를 안 줬을 때 — `target` 기본값을 따라 7.0.2 와 5.9.3 이 다르다 | 3절 `1 / 5` · 02편 |
| **컴파일러 동작** | 전역 `.d.ts` 는 **컴파일 전체**의 전역 — 끌어온 파일만이 아니다 | 2절 `b38.ts` · 37편 3절 |
| **컴파일러 동작** | 부작용 import 는 방출에 남는다 | 2절 `require("x38")` · 36편 1절 |
| **호스트(node v18 · v20)** | `toSorted` — v18 없음 · v20 있음 | 4절 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — |
| **컴파일러 동작** | `/// <reference types>` 는 방출물에 **주석으로만** 남는다 | 2절 `a38r.js` |
| **안 잰 것** | `types: []` 의 검사 시간 효과 · 진짜 `@types/node` | **재지 않았다** · `node_modules` 는 손으로 만든 디렉토리 하나뿐 |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`types: ["node", …]` 를 명시** — 7.0 에서 전역 타입이 필요한 패키지를 **목록으로** 적는다. 판을 안 탄다(1절) | 「키 없음」에 기대기 — **판마다 뜻이 다르다** |
| ★★ **`typeRoots`** — 손으로 쓴 전역 선언을 모은 디렉토리가 따로 있을 때 | `typeRoots` 만 주고 `types` 를 잊기 — 7.0 에서 아무것도 안 들어온다 |
| ★ **`/// <reference types>`** — 한 파일이 그 전역을 **필요로 한다는 표시**로 | 「이 파일에서만」 쓰려는 뜻으로 — **컴파일 전체**가 본다(2절) |
| ★★ **`lib`** — 실행 호스트가 가진 것에 **맞춰서** | 넓게 두고 잊기 — v18 에서 `TypeError`(4절) |
| ★ **`declare global`** — 모듈 파일에서 전역 하나를 보강할 때 | 스크립트 파일에서 — `TS2669` |

## 핵심 문장

1. **7.0.2 에서 `types` 키가 없으면 `[]` 와 같다** — 5.9.3·4.9.5 의 「보이는 `@types` 전부」와 **여섯 행 중 두 행**이 갈렸다.
2. **`import "x"`·`/// <reference types>` 는 `types` 를 건너뛰고, 들어온 전역은 컴파일 전체가 본다** — `import` 쪽은 방출물에 `require` 까지 남기고, `reference` 쪽은 주석만 남긴다.
3. **`lib` 는 내장 API 에 대한 약속이고, 적으면 기본 목록을 대체한다** — `dom` 이 빠지면 `console` 도 없다.
4. **tsc 는 `lib` 를 실행 호스트와 대조하지 않는다** — 같은 `.js` 가 node v18 에서 `TypeError`, v20 에서 정상.

## 관련 자료

- [**37번 주제** — 선언 파일 작성](../37-writing-declaration-files/) — ★★★ **README 의 선행.** `export` 없는 `.d.ts` 는 전역 · 범위는 함께 컴파일한 파일 · `skipLibCheck` 가 숨기는 것 · 충돌 전역의 파일 순서 — 그쪽 3·6절이 정본이다. **여기는 「어떤 설정이 그 `.d.ts` 를 컴파일에 넣나」부터.**
- [**14번 주제** — 단언 시그니처](../14-assertion-signatures/) 6절 — `@types/node` 가 없는 7.0 기본 설정의 `TS2591`.
- [**35번 주제** — 모듈 해석](../35-module-resolution/) — `TS5112`(파일을 직접 줄 때 위쪽 `tsconfig.json`) · 판마다 다른 기본값을 격자로 본 방식.
- [**36번 주제** — 타입 전용 import·export](../36-type-only-imports-and-exports/) — 부작용 import 가 방출에 남는 것(1절).
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 7.0 의 `target` 기본값 es2025(3절 `(안 줌)` 행의 까닭).
- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — 7.0 이 바꾼 또 하나의 기본값.
- [목록의 **43번 주제**](../43-remaining-tsconfig-choices/)(`tsconfig` 의 나머지 선택) — `target`·`lib`·`skipLibCheck` 의 판단은 그쪽.

## 용어 풀이

> **전역 이름 공간** — import 없이 이름으로 부를 수 있는 선언의 합. 컴파일에 든 전역 `.d.ts`·`lib` 가 채운다.\
> 예: 1절 `X38_GLOBAL`.

> **`types`** — 자동으로 전역에 넣을 `@types` 패키지의 **목록**. 7.0.2 에서 키가 없으면 `[]`.\
> 예: 1절 — 키 없음 `TS2304`(7.0.2) · `TS2322`(5.9.3).

> **`typeRoots`** — `@types` 패키지를 **찾는 디렉토리**. 기본은 `node_modules/@types`.\
> 예: 1절 `./types`.

> **`lib`** — 내장 API(ES 판별 표준 라이브러리·DOM)의 선언 파일 목록. 적으면 기본 목록을 대체한다.\
> 예: 3절 `es2020` — `TS2584`·`TS2550`.

> **`/// <reference types="x" />`** — 파일 맨 위의 지시 주석. 패키지 `x` 의 타입을 컴파일에 넣는다.\
> 예: 2절 `a38r.ts`.

> **`declare global { … }`** — 모듈 파일 안에서 전역 이름 공간에 선언을 더하는 꼴. 스크립트 파일이면 `TS2669`.\
> 예: 5절 `modg38.ts`.

> **`TS2584`** — 「Cannot find name '…'. Do you need to change your target library? Try changing the 'lib' compiler option to include 'dom'.」\
> 예: 3절 `document`·`console`.

> **`TS2550`** — 「Property '…' does not exist on type '…'. Do you need to change your target library? …」 — `lib` 판이 낮다.\
> 예: 3절 `.at`·`.toSorted`.

> **`TS2688`** — 「Cannot find type definition file for '…'.」 — `types` 에 적은 이름을 못 찾았다.\
> 예: 2절 5.9.3 의 `"*"`.

## 더 들어가면

- **진짜 `@types/node`·`@types/jest`** — 이 문서는 `index.d.ts` 한 장으로 흉내 냈다. 진짜 패키지는 `package.json` 의 `types` 필드·의존 `@types` 까지 따라가므로 들어오는 선언이 **훨씬 넓다.** `npm install` 을 하지 않아 **던지지 않았다.**
- **`types` 와 `skipLibCheck` 의 겹침** — 37편 6절의 「충돌 전역의 파일 순서」는 `types` 가 무엇을 넣느냐에 따라 **충돌 자체가 생기거나 안 생긴다.** 둘을 한 격자로 **던지지 않았다.**
- **`noLib`** · **`lib` 에 `dom.iterable`·`webworker`** — 이 문서는 `es20xx`·`dom` 만 던졌다.
