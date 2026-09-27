# ts/syntax/44 — 프로젝트 참조와 선언 방출 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Project References](https://www.typescriptlang.org/docs/handbook/project-references.html) · [TSConfig — `composite`](https://www.typescriptlang.org/tsconfig/#composite) · [`isolatedDeclarations`](https://www.typescriptlang.org/tsconfig/#isolatedDeclarations).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** 본문의 사실은 **전부 직접 던져 받은 진단·빌드 로그·생긴 파일 목록**에만 세운다. `isolatedDeclarations` 가 **5.5** 부터라는 README 의 문장은 「4.9.5 에 없다 · 5.9.3 에 있다」까지만 확인했다(4절).
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.

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

> ★★★ **본체 창 선언 — 이 주제의 본체는 「프로젝트 참조 격자」(`core` 의 `composite` 있음/없음 × `app` 의 `references` 있음/없음 × `tsc -b` / `tsc -p` × 두 판 — 칸마다 두 프로젝트를 새로 복사)이다.** 칸은 **진단 코드 · 종료 코드 · 생긴 `.js`/`.d.ts`** 셋이다.
> ★★★ **제5의 상태 — 「`app` 이 `core` 의 무엇을 보나」를 `--traceResolution` 에 물었더니 `core/src/index.ts` 라고 답했다**(2절 ①). 같은 질문을 **`--explainFiles`**(프로그램에 실제로 든 파일)로 바꿔 묻자 **`core/dist/index.d.ts`** 였다(②). 그리고 **`.d.ts` 한 줄을 손으로 바꿔 `app` 이 속는지** 던져 확인했다(③). 해석 창은 **「어느 경로로 풀었나」만** 보고 **「그 자리를 무엇으로 바꿔 끼웠나」는 못 본다.**
> ★★ **44 는 43 에서 온다.** [**43번 주제**](../43-remaining-tsconfig-choices/) 4절이 `incremental` 이 **바뀐 파일과 그 의존자만** 다시 방출하고, `declaration` 이 켜지면 **겉모습이 같은 변경의 의존자를 건너뛴다**는 것을 쟀다. 여기의 `tsc -b` 는 **그 규칙을 프로젝트 단위로** 올린 것이다(3절).
> ★★ 선언 방출 자체 — **`--declaration` 은 적힌 타입은 그대로 옮기고 안 적힌 자리만 추론한다** — 는 [**37번 주제**](../37-writing-declaration-files/) 5절이 쟀다. 4절의 `isolatedDeclarations` 는 **그 「추론」을 금지**하는 스위치다.
> ★★ 빌드 로그(3절)는 **mtime 을 비교해 판정**한다(로그의 「is older than」). 그래서 스크립트는 빌드마다 **`core` 는 2분 전 · `app` 은 1분 전으로 mtime 을 고정**한다 — 안 그러면 같은 초 안의 수정이 판정을 흔든다. ★ 이 고정이 **실험의 일부**다(3절 스크립트 첫머리).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다. `tsconfig.json` 은 두 개라 **경로째**(`===== 소스: p44/core/tsconfig.json =====`) 싣는다.
> ★ 진단 문구에 박히는 절대 경로는 스크립트가 **작업 디렉토리 기준으로 줄인다**(`sed`) — 그 줄이 스크립트 소스에 보인다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · 생긴 파일 목록 | 같은 입력·같은 설정이면 같다 |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | ★★ 3절 빌드 로그의 **판정 줄** | 시각 머리는 지웠고 mtime 은 고정했다 — ★ 고정 없이 돌린 탐색에서는 **세 번 돌려 md5 가 셋 다 달랐다**(흔들리는 판이라 블록으로 싣지 않았다) |
| **판에 매인다** | ★ 종료 코드 — `tsc -b` 의 `TS6059` 칸이 7.0.2 `2` · 5.9.3 `1` | 결론의 일부다(1절) |
| **판에 매인다** | ★★ `isolatedDeclarations` 의 진단 **코드와 자리** — 7.0.2 `TS9013` · 5.9.3 `TS9007`/`TS9008` | 4절 |
| **★ 부적용 — 시간** | 「참조로 쪼개면 빌드가 빨라진다」 | **재지 않았다** — 이 문서는 **무엇을 다시 짓나**만 센다 |

## 한눈에 — 쉽게 말하면

**프로젝트 참조는 「부품 공장과 조립 공장」이다. 조립 공장(`app`)은 부품 공장(`core`)의 **설계 도면(`.ts`)** 을 보지 않고, 부품 공장이 내보낸 **규격서(`.d.ts`)** 만 본다. 그래서 부품 공장은 규격서를 **반드시 내보내야** 하고(`composite`), 조립 공장은 **어느 부품 공장을 쓰는지** 적어야 한다(`references`). `tsc -b` 는 공장장이라 **부품 공장부터** 돌린다.**

| 비유 | 실체 |
|---|---|
| 부품 공장이 규격서를 **꼭 내보낸다** | `core` 의 `"composite": true` — 없으면 `TS6306`(1절) |
| 조립 공장이 **거래처를 적는다** | `app` 의 `"references": [{ "path": "../core" }]` — 없으면 `core` 의 `.ts` 를 자기 것으로 끌어와 `TS6059`(1절) |
| ★★★ 공장장이 **부품 공장부터** 돌린다 | `tsc -b app` — `core` 를 먼저 짓는다 · `tsc -p app` 은 안 짓고 `TS6305`(1절) |
| ★★★ 조립 공장은 **규격서만** 본다 | `--explainFiles` — `core/dist/index.d.ts` · 규격서를 고치면 **속는다**(2절 ③) |
| ★★ 부품 공장 **안쪽만** 바꾸면 조립 공장은 쉰다 | 몸통만 바꾸면 `app` 은 「up to date with .d.ts files」(3절) |
| ★★★ **창고(`dist`)만 비우고 일지는 남기면** | 공장장이 「최신」이라며 **아무것도 안 짓는다** — `exit 0`(3절 5단계) |
| 규격서를 **도면 없이** 쓸 수 있게 | `isolatedDeclarations` — 반환 타입 등을 **적어야** 한다(`TS9007`·`TS9013`)(4절) |

- ★★★ 한 줄로 — 「**참조된 프로젝트는 `composite` 로 `.d.ts` 를 내보내고, 참조하는 쪽은 그 `.d.ts` 를 본다. `tsc -b` 가 순서대로 짓고 겉모습이 안 바뀌면 의존자를 건너뛴다. `isolatedDeclarations` 는 그 `.d.ts` 를 파일 하나만 보고 쓸 수 있도록 **추론이 필요한 자리에 타입을 적게** 한다.**」

```text
  두 프로젝트 — 무엇이 무엇을 보나

  core/src/index.ts ──(tsc -b 가 먼저 짓는다)──> core/dist/index.js
                                            └─> core/dist/index.d.ts ◄── app 이 실제로 보는 것
  app/src/main.ts   import "../../core/src/index"   ← 적힌 경로는 .ts 쪽인데
                    tsc 가 그 자리에 .d.ts 를 끼운다   (references 가 있을 때)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `composite`·`references`·`tsc -b` 는 각각 무엇을 요구하고, 빠지면 무엇이 나나** — 격자 16칸(1절) · `rootDir` 없이 참조도 없으면(1절 끝).
2. **★★★ `app` 은 `core` 의 무엇을 보나 — 그리고 `core` 를 바꾸면 무엇이 다시 지어지나** — 해석 창 대 프로그램 창 · `.d.ts` 를 고쳐 보기(2절) · 빌드 로그 여섯 단계(3절).
3. **★★ `isolatedDeclarations` 는 어느 꼴을 막나** — export 꼴 열하나 × 세 판(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **참조 격자** | `composite` × `references` × `-b`/`-p` × 두 판 — 진단 · exit · 생긴 파일 | 칸마다 세 값 | **본체**(1절) |
| ★★ **해석 창 `--traceResolution`** | import 가 **어느 파일로 풀렸나** | 로그 한 줄 | 2절 ① — `core/src/index.ts` |
| ★★★ **프로그램 창 `--explainFiles`** | 프로그램에 **실제로 든 파일**과 그 까닭 | 파일 목록 | 2절 ② — **제5의 상태**(해석 창이 못 보는 것) |
| ★★ **빌드 로그 `tsc -b --verbose`** | 프로젝트마다 「최신인가 · 왜」 | 판정 줄 | 3절 — 시간이 아니라 **판정 문구** |
| ★★ **`isolatedDeclarations` 격자** | export 꼴 열하나 × 세 판 | 진단(행:코드) | 4절 |
| ★ **5창 — `.d.ts`** | 적은 판과 안 적은 판의 `.d.ts` | 방출물 | 4절 끝 — 37편 인용 |
| ★ **부적용 — 시간** | 빌드가 빨라지나 | — | 45편 |

비용 — 격자 16칸 + `-b` 자리 · `--dry` + 진단 전문 셋 + `rootDir` 없는 한 쌍 · 무엇을 보나 두 판 × 셋 · 빌드 로그 두 판 × 여섯 단계 · `isolatedDeclarations` 열두 행 × 세 판 + 전문 · `.d.ts` 한 쌍.

```text
  이 주제의 축 — 「누가 누구를 짓고, 누가 무엇을 보나」

  짓는 순서       tsc -b app  ─> core 먼저, 그다음 app        tsc -p app ─> app 만
  보는 것         references 있음 ─> core 의 .d.ts           없음 ─> core 의 .ts 를 자기 프로그램에
  다시 짓는 것     core 몸통만 ─> app 은 건너뜀                core 서명 ─> app 도
  .d.ts 를 쓰는 법  --declaration ─> 추론해서 적는다           isolatedDeclarations ─> 추론이 필요하면 진단
```

### (1) ★★★ 참조 격자 — `composite` × `references` × `-b`/`-p` × 두 판

**언제 쓰나** — 모노레포를 프로젝트 둘로 쪼갤 때, **어느 설정 하나가 빠졌을 때 무엇이 나는지** 미리 볼 때.

두 프로젝트 — `p44/core` 와 `p44/app`. 아래 두 `tsconfig.json` 이 격자의 **「있음 · 있음」 칸**이고, 다른 칸은 스크립트가 다시 쓴다.

```ts
// index.ts
export function add(a: number, b: number): number {
    return a + b;
}
```

```text
===== 소스: p44/core/tsconfig.json =====
{
    "compilerOptions": { "composite": true, "target": "es2022", "outDir": "dist", "rootDir": "src" },
    "include": ["src"]
}
===== 소스: p44/app/tsconfig.json =====
{
    "compilerOptions": { "target": "es2022", "outDir": "dist", "rootDir": "src" },
    "include": ["src"],
    "references": [{ "path": "../core" }]
}
```

```ts
// main.ts
import { add } from "../../core/src/index";
console.log(add(1, 2));
```

★ `-b` 는 **첫 인자**다 — 그리고 `--dry` 가 **짓는 순서**를 말해 준다.

```text
===== cd p44 && tsc --pretty false -b app ; 이어서 tsc -b app --pretty false --dry (sh exit=0) =====
error TS5023: Unknown compiler option '-b'.
(exit 1)
A non-dry build would build project 'core/tsconfig.json'
A non-dry build would build project 'app/tsconfig.json'
(exit 0)
p44 아래 dist: 0개
```

- ★★ `--pretty false -b app` 은 **`TS5023`**(「Unknown compiler option '-b'.」) — 빌드 모드 스위치는 **맨 앞**이라야 한다.
- ★★★ `tsc -b app --dry` — **`core` 다음 `app`** 순서로 「A non-dry build would build project …」. 아무것도 안 짓는다(`dist` `0`개).

```bash
# ts42b-refs44.sh
#!/usr/bin/env bash
# core·app 두 프로젝트 × core 의 composite 있음/없음 × app 의 references 있음/없음 × tsc -b app / tsc -p app × 판 둘
# 칸마다 p44 를 새 디렉토리에 복사하고 두 tsconfig.json 을 그 칸의 설정으로 다시 쓴다(p44 의 두 파일은 「있음 · 있음」 칸이다)
# 칸 = 진단 코드 · 종료 코드 · 생긴 .js/.d.ts
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
core_cfg() { printf '{ "compilerOptions": { %s"target": "es2022", "outDir": "dist", "rootDir": "src" }, "include": ["src"] }\n' "$([ "$1" = 있음 ] && echo '"composite": true, ')"; }
app_cfg()  { printf '{ "compilerOptions": { "target": "es2022", "outDir": "dist", "rootDir": "src" }, "include": ["src"]%s }\n' "$([ "$1" = 있음 ] && echo ', "references": [{ "path": "../core" }]')"; }
printf '%-10s %-12s %-6s %-6s %-14s %-5s %s\n' "composite" "references" "명령" "판" "진단" "exit" "생긴 파일"
i=0; ok=0; split=0; total=0; all=""
for comp in 있음 없음; do for refs in 있음 없음; do for cmd in -b -p; do
  declare -A got=()
  for v in 7.0.2 5.9.3; do
    i=$((i+1)); w="$D/c$i"; cp -r p44 "$w" || exit 3
    core_cfg "$comp" > "$w/core/tsconfig.json"; app_cfg "$refs" > "$w/app/tsconfig.json"
    if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
    raw=$(cd "$w" && "${c[@]}" "$cmd" app --pretty false 2>&1); rc=$?
    case "$raw" in *TS5112*|*TS5023*) echo "★ 설정·명령 진단이 칸에 들었다 -- 격자를 믿지 마라: $raw"; exit 4 ;; esac
    files=$(cd "$w" && find core app -path '*/dist/*' \( -name '*.js' -o -name '*.d.ts' \) | sort | tr '\n' ' ' | sed 's/ $//')
    got[$v]="$(codes <<< "$raw")|$rc|$files"
    IFS='|' read -r cd_ rc_ f_ <<< "${got[$v]}"
    printf '%-10s %-12s %-6s %-6s %-14s %-5s %s\n' "$comp" "$refs" "$cmd" "$v" "${cd_:-OK}" "$rc_" "${f_:-없음}"
    total=$((total+1)); [ -z "$cd_" ] && [ "$rc_" = 0 ] && ok=$((ok+1)); all="$all#${cd_:-OK}"
  done
  [ "${got[7.0.2]}" != "${got[5.9.3]}" ] && split=$((split+1))
  unset got
done; done; done
kinds_seen=$(tr '#' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "진단 없이 빌드된 칸 $ok / $total · 두 판이 갈린 칸(진단·exit·파일 중 하나라도) $split / $((total / 2))"
```

```text
===== bash ts42b-refs44.sh (sh exit=0) =====
composite  references   명령 판    진단         exit  생긴 파일
있음     있음       -b     7.0.2  OK             0     app/dist/main.js core/dist/index.d.ts core/dist/index.js
있음     있음       -b     5.9.3  OK             0     app/dist/main.js core/dist/index.d.ts core/dist/index.js
있음     있음       -p     7.0.2  TS6305         2     app/dist/main.js
있음     있음       -p     5.9.3  TS6305         2     app/dist/main.js
있음     없음       -b     7.0.2  TS6059         2     app/dist/main.js
있음     없음       -b     5.9.3  TS6059         1     app/dist/main.js
있음     없음       -p     7.0.2  TS6059         2     app/dist/main.js
있음     없음       -p     5.9.3  TS6059         2     app/dist/main.js
없음     있음       -b     7.0.2  TS6306         2     app/dist/main.js core/dist/index.js
없음     있음       -b     5.9.3  TS6306         2     app/dist/main.js core/dist/index.js
없음     있음       -p     7.0.2  TS6306         2     app/dist/main.js
없음     있음       -p     5.9.3  TS6306         2     app/dist/main.js
없음     없음       -b     7.0.2  TS6059         2     app/dist/main.js
없음     없음       -b     5.9.3  TS6059         1     app/dist/main.js
없음     없음       -p     7.0.2  TS6059         2     app/dist/main.js
없음     없음       -p     5.9.3  TS6059         2     app/dist/main.js

진단 없이 빌드된 칸 2 / 16 · 두 판이 갈린 칸(진단·exit·파일 중 하나라도) 2 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단 없이 빌드된 칸은 `2 / 16`** — `composite` 있음 · `references` 있음 · **`tsc -b`** 의 두 판뿐이다. 생긴 파일이 `core/dist/index.js` · **`index.d.ts`** · `app/dist/main.js` 셋.
- ★★★ **같은 설정인데 `tsc -p app` 이면 `TS6305`** — `core` 를 **안 짓는다.** 참조된 `core/dist/index.d.ts` 가 없으니 「아직 안 지어졌다」고 한다.
- ★★★ **`composite` 없이 참조하면 `TS6306`** — `-b` 도 `-p` 도. ★ 그런데 **`-b` 칸에는 `core/dist/index.js` 가 생겼다** — 공장장은 `core` 를 **짓기는 짓고**(`.d.ts` 없이) `app` 에서 멈췄다.
- ★★★ **`references` 가 없으면 `TS6059`** — `composite` 와 무관하다. `app` 이 `core/src/index.ts` 를 **자기 프로그램으로 끌어와** `rootDir: src` 밖이라고 막는다. `-b` 도 `core` 를 **짓지 않는다**(참조가 없으니 모른다).
- ★★ **두 판이 갈린 칸 `2 / 8`** — 둘 다 `TS6059` 의 `tsc -b` 칸이고 **종료 코드만** 다르다(7.0.2 `2` · 5.9.3 `1`). 진단 코드와 생긴 파일은 16칸 모두 같다.

진단 전문 — 격자가 코드만 찍은 셋.

```bash
# ts42b-msgs44.sh
#!/usr/bin/env bash
# 격자에 나온 진단 셋의 전문 -- 7.0.2 · 메시지에 박히는 절대 경로는 작업 디렉토리 기준으로 줄인다(sed)
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
rel() { sed "s|$1/||g"; }
cp -r p44 "$D/a" || exit 3
echo "---- composite 있음 · references 있음 · core 를 안 짓고 tsc -p app"
(cd "$D/a" && tsc -p app --pretty false 2>&1 | rel "$D/a"); echo "(exit $?)"
cp -r p44 "$D/b" || exit 3; sed -i 's/"composite": true, //' "$D/b/core/tsconfig.json"
echo "---- composite 없음 · references 있음 · tsc -b app"
(cd "$D/b" && tsc -b app --pretty false 2>&1 | rel "$D/b"); echo "(exit $?)"
cp -r p44 "$D/c" || exit 3; sed -i '/"references"/d; s/"include": \["src"\],/"include": ["src"]/' "$D/c/app/tsconfig.json"
echo "---- composite 있음 · references 없음 · tsc -p app"
(cd "$D/c" && tsc -p app --pretty false 2>&1 | rel "$D/c"); echo "(exit $?)"
```

```text
===== bash ts42b-msgs44.sh (sh exit=0) =====
---- composite 있음 · references 있음 · core 를 안 짓고 tsc -p app
app/src/main.ts(1,21): error TS6305: Output file 'core/dist/index.d.ts' has not been built from source file 'core/src/index.ts'.
(exit 2)
---- composite 없음 · references 있음 · tsc -b app
app/tsconfig.json(4,20): error TS6306: Referenced project 'core' must have setting "composite": true.
(exit 2)
---- composite 있음 · references 없음 · tsc -p app
app/src/main.ts(1,21): error TS6059: File 'core/src/index.ts' is not under 'rootDir' 'app/src'. 'rootDir' is expected to contain all source files.
(exit 2)
```

- ★★ **`TS6305`** — 「Output file 'core/dist/index.d.ts' has not been built from source file 'core/src/index.ts'.」 — **`app` 이 찾는 것이 `.d.ts`** 라는 것을 진단이 먼저 말한다.
- ★★ **`TS6306`** — 「Referenced project 'core' must have setting "composite": true.」 — 가리키는 자리가 **`app/tsconfig.json(4,20)`**, `references` 줄이다.
- ★★ **`TS6059`** — 「File 'core/src/index.ts' is not under 'rootDir' 'app/src'.」

```text
  격자 16칸 — 무엇이 빠지면 무엇이 나나 (두 판 같음 · exit 만 한 곳 다름)

                             tsc -b app                      tsc -p app
  composite ✓ references ✓   ★ 빌드됨 (core 먼저)            TS6305 — core 를 안 지었다
  composite ✗ references ✓   TS6306 (core 는 .js 만 지어짐)   TS6306
  composite ✓ references ✗   TS6059 (core 를 모른다)          TS6059
  composite ✗ references ✗   TS6059                          TS6059
```

★ `app` 에 `rootDir` 를 **안 적고** 참조도 없으면 — 판이 갈린다.

```bash
# ts42b-norootdir44.sh
#!/usr/bin/env bash
# references 도 rootDir 도 없는 app -- tsc -p app 이 core 의 .ts 를 어떻게 다루나 · 판 둘
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  echo '{ "compilerOptions": { "target": "es2022", "outDir": "dist" }, "include": ["src"] }' > "$w/app/tsconfig.json"
  (cd "$w" && "${c[@]}" -p app --pretty false) > "$D/out" 2>&1; rc=$?
  echo "---- $v : tsc -p app (exit $rc)"
  sed "s|$w/||g" "$D/out"
  echo "  생긴 파일: $(cd "$w" && find core app -path '*/dist/*' -type f | sort | tr '\n' ' ')"
done
```

```text
===== bash ts42b-norootdir44.sh (sh exit=0) =====
---- 7.0.2 : tsc -p app (exit 2)
app/tsconfig.json(1,44): error TS5011: The common source directory of 'tsconfig.json' is '..'. The 'rootDir' setting must be explicitly set to this or another path to adjust your output's file layout.
  Visit https://aka.ms/ts6 for migration information.
  생긴 파일: app/dist/src/main.js 
---- 5.9.3 : tsc -p app (exit 0)
  생긴 파일: app/dist/app/src/main.js app/dist/core/src/index.js 
```

- ★★★ **5.9.3 은 `(exit 0)`** — 그리고 `app/dist` 안에 **`core/src/index.js` 까지** 지었다. `core` 의 소스가 **`app` 의 출력으로 한 벌 더** 복사됐다 — 진단 한 줄 없이.
- ★★★ **7.0.2 는 `TS5011`** — 「The common source directory of 'tsconfig.json' is '..'. The 'rootDir' setting must be explicitly set …」. **`rootDir` 를 적으라고 멈춘다**(안내 링크 `aka.ms/ts6` 가 붙는다 — 열지 않았다). 그래도 `app/dist/src/main.js` 는 생겼다.

비용 — 참조 없는 모노레포는 **5.9.3 에서 조용히 부풀고**, 7.0.2 에서는 그 자리가 **설정 진단**이 된다. 격자가 `rootDir: src` 를 둔 까닭이 이것이다 — 없으면 `TS6059` 칸이 판마다 다른 모양이 된다.

### (2) ★★★ `app` 은 `core` 의 무엇을 보나 — 해석 창 · 프로그램 창 · `.d.ts` 를 고쳐 보기

**언제 쓰나** — 「`core` 를 고쳤는데 `app` 이 옛 타입을 본다」·「`app` 의 import 경로는 `.ts` 인데?」 를 판단할 때.

```bash
# ts42b-dts44.sh
#!/usr/bin/env bash
# tsc -b app 으로 지은 뒤 app 의 프로그램에 무엇이 들었나 -- 판 둘
#   ① --traceResolution : import 가 어느 파일로 풀렸나(마지막 한 줄)
#   ② --explainFiles    : 프로그램에 실제로 든 파일과 그 까닭(표준 라이브러리 줄은 뺀다)
#   ③ core/dist/index.d.ts 한 줄을 손으로 바꾸고 app 만 다시 검사한다(core/src 는 그대로)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  (cd "$w" && "${c[@]}" -b app --pretty false) > "$D/b.out" 2>&1; rc=$?
  echo "---- $v : tsc -b app (exit $rc)"
  echo "① $( (cd "$w" && "${c[@]}" -p app --pretty false --noEmit --traceResolution) | grep 'was successfully resolved' | sed "s|$w/||g")"
  echo "②"
  (cd "$w" && "${c[@]}" -p app --pretty false --noEmit --explainFiles) | sed "s|$w/||g" \
    | awk '/^[^ ]/{keep = ($0 ~ /^(core|app)\//)} keep'
  echo 'export declare function add(a: string, b: string): string;' > "$w/core/dist/index.d.ts"
  echo "③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit"
  (cd "$w" && "${c[@]}" -p app --pretty false --noEmit) | sed "s|$w/||g"; echo "(exit $?)"
done
```

```text
===== bash ts42b-dts44.sh (sh exit=0) =====
---- 7.0.2 : tsc -b app (exit 0)
① ======== Module name '../../core/src/index' was successfully resolved to 'core/src/index.ts'. ========
②
core/dist/index.d.ts
   Imported via "../../core/src/index" from file 'app/src/main.ts'
   File is output of project reference source 'core/src/index.ts'
app/src/main.ts
   Matched by include pattern 'src' in 'app/tsconfig.json'
③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit
app/src/main.ts(2,17): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
(exit 1)
---- 5.9.3 : tsc -b app (exit 0)
① ======== Module name '../../core/src/index' was successfully resolved to 'core/src/index.ts'. ========
②
core/dist/index.d.ts
  Imported via "../../core/src/index" from file 'app/src/main.ts'
  File is output of project reference source 'core/src/index.ts'
app/src/main.ts
  Matched by include pattern 'src' in 'app/tsconfig.json'
③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit
app/src/main.ts(2,17): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
(exit 2)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **① 해석 창** — import `../../core/src/index` 는 **`core/src/index.ts`** 로 풀렸다. 여기까지만 보면 `app` 이 **소스**를 보는 것 같다.
- ★★★ **② 프로그램 창** — 프로그램에 든 것은 **`core/dist/index.d.ts`** 다. 까닭 두 줄 — 「Imported via "../../core/src/index" from file 'app/src/main.ts'」 · **「File is output of project reference source 'core/src/index.ts'」**. 풀린 `.ts` 자리에 **그 출력 `.d.ts` 를 끼웠다.**
- ★★★ **③ `.d.ts` 한 줄을 `(a: string, b: string)` 으로 바꾸자** `app` 이 **`TS2345`**(「Argument of type 'number' is not assignable to parameter of type 'string'.」). `core/src/index.ts` 는 여전히 `number` 인데 — **`app` 은 `.d.ts` 에 속았다.** 이것이 「`.d.ts` 를 본다」의 행동 증거다.
- ★ 두 판이 **들여쓰기(3칸 · 2칸)** 말고 한 글자도 같다.

```text
  같은 import — 창 둘이 다른 답

  --traceResolution   "../../core/src/index" ─> core/src/index.ts        (어느 경로로 풀었나)
  --explainFiles      프로그램에 든 것        ─> core/dist/index.d.ts     (무엇으로 바꿔 끼웠나)
                                               "File is output of project reference source …"
  ★ .d.ts 를 고치면 app 이 속는다 ─> app 이 보는 것은 .d.ts 다
```

비용 — `core` 의 `.d.ts` 가 **낡으면 `app` 은 낡은 타입으로** 검사된다. 그래서 `tsc -p app` 만 돌리는 습관이 위험하다(1절 `TS6305` · 3절 5단계).

### (3) ★★ `core` 만 바꾸면 무엇이 다시 지어지나 — `tsc -b --verbose` 여섯 단계

**언제 쓰나** — 「`core` 를 조금 고쳤는데 `app` 까지 다시 짓나」를 **로그로** 확인할 때. ★ 시간이 아니라 **판정 문구**를 읽는다.

```bash
# ts42b-verbose44.sh
#!/usr/bin/env bash
# tsc -b app --verbose 의 판정 줄 -- 단계 다섯 × 판 둘 · 로그 첫머리의 시각은 지운다(판마다 형식도 다르다)
#   1 처음 · 2 안 바꿈 · 3 core 몸통만(선언 같음) · 4 core 서명까지 · 5 core/dist 만 지움(.tsbuildinfo 는 남김) · 6 tsc -b app --clean 뒤
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
settle() {   # 빌드마다 mtime 을 과거로 고정한다 -- core 는 2분 전 · app 은 1분 전(app 이 core 뒤에 지어진 순서 그대로)
  find "$1/core" -exec touch -d '120 seconds ago' {} +; find "$1/app" -exec touch -d '60 seconds ago' {} +; }
clean() { sed -E "s|$1/||g; s/^(오전|오후) [0-9:]+ - //; s/^[0-9:]+ [AP]M - //" | sed '/^$/d; /^Projects in this build/,/app\/tsconfig.json$/d'; }
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  for step in 1 2 3 4 5 6; do
    case $step in
      1) label="처음" ;;
      2) label="안 바꿈" ;;
      3) label="core 몸통만"; printf 'export function add(a: number, b: number): number {\n    return b + a;\n}\n' > "$w/core/src/index.ts" ;;
      4) label="core 서명까지"; printf 'export function add(a: number, b: number, c = 0): number {\n    return a + b + c;\n}\n' > "$w/core/src/index.ts" ;;
      5) label="core/dist 만 지움"; rm -rf "$w/core/dist" ;;
      6) label="--clean 뒤"; (cd "$w" && "${c[@]}" -b app --clean) > /dev/null 2>&1 ;;
    esac
    (cd "$w" && "${c[@]}" -b app --verbose --pretty false) > "$D/log" 2>&1; rc=$?; settle "$w"
    echo "---- $v · $step $label (exit $rc)"
    clean "$w" < "$D/log" | sed 's/^/  /'
    echo "  core/dist/index.d.ts 가 있나 $([ -f "$w/core/dist/index.d.ts" ] && echo 있음 || echo 없음)"
    clean "$w" < "$D/log" > "$D/log.$v.$step"
  done
done
same=0; for s in 1 2 3 4 5 6; do cmp -s "$D/log.7.0.2.$s" "$D/log.5.9.3.$s" && same=$((same+1)); done
echo
echo "두 판의 판정 줄이 한 글자도 같은 단계 $same / 6"
```

```text
===== bash ts42b-verbose44.sh (sh exit=0) =====
---- 7.0.2 · 1 처음 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 2 안 바꿈 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 3 core 몸통만 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is up to date with .d.ts files from its dependencies
  Updating output timestamps of project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 4 core 서명까지 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output 'app/tsconfig.tsbuildinfo' is older than input 'core'
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 5 core/dist 만 지움 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 없음
---- 7.0.2 · 6 --clean 뒤 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 1 처음 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 2 안 바꿈 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 3 core 몸통만 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is up to date with .d.ts files from its dependencies
  Updating output timestamps of project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 4 core 서명까지 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output 'app/tsconfig.tsbuildinfo' is older than input 'core'
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 5 core/dist 만 지움 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 없음
---- 5.9.3 · 6 --clean 뒤 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음

두 판의 판정 줄이 한 글자도 같은 단계 6 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★ **1 처음** — 둘 다 「output file '….tsbuildinfo' does not exist」 → **`core` 먼저, 그다음 `app`** 을 짓는다. `composite` 의 일지는 **`tsconfig.tsbuildinfo`**(설정 옆)에 생겼다.
- ★★ **2 안 바꿈** — 둘 다 「is up to date because newest input … is older than output …」 — 아무것도 안 짓는다.
- ★★★ **3 `core` 몸통만**(`a + b` → `b + a`, 선언 같음) — `core` 는 다시 짓고, **`app` 은 「is up to date with .d.ts files from its dependencies」** → **타임스탬프만** 고친다. 43편 4절의 「`declaration` 이 겉모습을 비교한다」가 **프로젝트 단위**로 일어났다.
- ★★★ **4 `core` 서명까지**(매개변수 `c = 0` 추가) — `app` 도 「is older than input 'core'」 → **다시 짓는다.**
- ★★★ **5 `core/dist` 만 지움**(`.tsbuildinfo` 는 남김) — **둘 다 「up to date」, `exit 0`** — 그리고 **`core/dist/index.d.ts` 가 없다.** 공장장은 **일지만 보고** 창고가 빈 것을 모른다.
- ★★ **6 `--clean` 뒤** — 일지까지 지워져 1단계처럼 **처음부터** 짓는다.
- ★★ 마지막 줄 — **두 판의 판정 줄이 한 글자도 같은 단계 `6 / 6`**.

```text
  core 를 바꿨을 때 — app 은 무엇을 하나

  몸통만 (선언 같음)     core 다시 짓기 ─> .d.ts 가 같다 ─> app 은 「up to date with .d.ts files」 · 타임스탬프만
  서명까지              core 다시 짓기 ─> .d.ts 가 다르다 ─> app 다시 짓기
  ★ dist 만 지움        core 「up to date」 (일지를 믿는다) ─> 아무것도 안 짓는다 · exit 0 · .d.ts 없음
  --clean 뒤            일지 없음 ─> 전부 다시
```

비용 — **출력 폴더를 손으로 지우는 청소**는 `tsc -b` 에게 **보이지 않는다.** 일지와 출력을 같이 지우는 **`tsc -b --clean`** 을 쓴다. 이 로그는 **mtime 을 고정한 판**이다(머리말) — 판정이 mtime 에 기대므로 고정 없이 돌리면 같은 단계가 다른 문구를 냈다.

### (4) ★★★ `isolatedDeclarations`(5.5) — 파일 하나만 보고 `.d.ts` 를 쓸 수 있게

**언제 쓰나** — `.d.ts` 방출을 **타입 검사 없이**(파일 단위 도구로) 하고 싶을 때 — 그러려면 **추론이 필요한 export 자리**가 없어야 한다.

```ts
// iso44a.ts
export function f(n: number) {
    return n * 2;
}
```

```ts
// iso44b.ts
export function f(n: number): number {
    return n * 2;
}
```

```ts
// iso44k.ts
export function one() {
    return 1;
}
```

```ts
// iso44c.ts
export const c = 10;
```

```ts
// iso44d.ts
export const c = [1, 2];
```

```ts
// iso44e.ts
export const c = [1, 2] as const;
```

```ts
// iso44f.ts
function two(): number {
    return 2;
}
export const c = two();
```

```ts
// iso44g.ts
export const f = (n: number) => n;
```

```ts
// iso44h.ts
export class K {
    m(n: number) {
        return n * 2;
    }
}
```

```ts
// iso44i.ts
function make(): number {
    return 1;
}
export default make();
```

```ts
// iso44j.ts
const inner = (n: number) => n * 2;
export function g(n: number): number {
    return inner(n);
}
```

```bash
# ts42b-iso44.sh
#!/usr/bin/env bash
# isolatedDeclarations -- export 꼴 열하나 × 판 셋 · 칸은 진단(행:코드) · 늘 --declaration 을 같이 준다
# 끝 행은 --declaration 없이 준 것(설정 진단을 보려고) -- 파일은 iso44b.ts
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
T=$'\t'
rows=(
  "iso44a.ts${T}function f(n) { return n * 2 }${T}--declaration"
  "iso44b.ts${T}function f(n): number { … }${T}--declaration"
  "iso44k.ts${T}function one() { return 1 }${T}--declaration"
  "iso44c.ts${T}const c = 10${T}--declaration"
  "iso44d.ts${T}const c = [1, 2]${T}--declaration"
  "iso44e.ts${T}const c = [1, 2] as const${T}--declaration"
  "iso44f.ts${T}const c = two()${T}--declaration"
  "iso44g.ts${T}const f = (n) => n${T}--declaration"
  "iso44h.ts${T}class K { m(n) { … } }${T}--declaration"
  "iso44i.ts${T}export default make()${T}--declaration"
  "iso44j.ts${T}export 는 적고 안쪽은 안 적음${T}--declaration"
  "iso44b.ts${T}(--declaration 없이)${T}"
)
cells() { sed -n 's/^[^ ]*(\([0-9]*\),[0-9]*): error \(TS[0-9]*\).*/\1:\2/p; s/^error \(TS[0-9]*\).*/설정:\1/p' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-10s %-12s %-12s %-12s %s\n' "파일" "7.0.2" "5.9.3" "4.9.5" "꼴"
ok7=0; split=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $r"; exit 3; fi
  IFS="$T" read -r f what extra <<< "$r"
  # shellcheck disable=SC2086
  a=$(tsc --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  # shellcheck disable=SC2086
  b=$(node "$OLD" --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  # shellcheck disable=SC2086
  c=$(node "$V49" --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  case "$a$b$c" in *TS5112*) echo "★ TS5112 -- 위쪽 디렉토리의 tsconfig.json 이 끼었다, 격자를 믿지 마라"; exit 4 ;; esac
  a=$(cells <<< "$a"); b=$(cells <<< "$b"); c=$(cells <<< "$c")
  printf '%-10s %-12s %-12s %-12s %s\n' "$f" "${a:-OK}" "${b:-OK}" "${c:-OK}" "$what"
  total=$((total+1)); [ -z "$a" ] && ok7=$((ok7+1)); [ "$a" != "$b" ] && split=$((split+1))
done
echo
echo "7.0.2 가 받은 행 $ok7 / $total · 7.0.2 와 5.9.3 이 갈린 행 $split / $total"
```

```text
===== bash ts42b-iso44.sh (sh exit=0) =====
파일     7.0.2        5.9.3        4.9.5        꼴
iso44a.ts  2:TS9013     1:TS9007     설정:TS5023 function f(n) { return n * 2 }
iso44b.ts  OK           OK           설정:TS5023 function f(n): number { … }
iso44k.ts  OK           OK           설정:TS5023 function one() { return 1 }
iso44c.ts  OK           OK           설정:TS5023 const c = 10
iso44d.ts  1:TS9017     1:TS9017     설정:TS5023 const c = [1, 2]
iso44e.ts  OK           OK           설정:TS5023 const c = [1, 2] as const
iso44f.ts  4:TS9010     4:TS9010     설정:TS5023 const c = two()
iso44g.ts  1:TS9007     1:TS9007     설정:TS5023 const f = (n) => n
iso44h.ts  3:TS9013     2:TS9008     설정:TS5023 class K { m(n) { … } }
iso44i.ts  4:TS9037     4:TS9037     설정:TS5023 export default make()
iso44j.ts  OK           OK           설정:TS5023 export 는 적고 안쪽은 안 적음
iso44b.ts  설정:TS5069 설정:TS5069 설정:TS5023 (--declaration 없이)

7.0.2 가 받은 행 5 / 12 · 7.0.2 와 5.9.3 이 갈린 행 2 / 12
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **막힌 꼴** — 반환 타입을 안 적은 함수(`n * 2`) · `[1, 2]`(`TS9017` — 「Only const arrays can be inferred」) · 호출 결과 `two()`(`TS9010`) · 화살표 함수(`TS9007`) · 메서드 · `export default make()`(`TS9037`).
- ★★★ **통과한 꼴** — 반환 타입을 **적은** 함수 · **`return 1`**(리터럴이라 보고 안다) · `const c = 10` · **`[1, 2] as const`** · **`export` 만 적고 안쪽 헬퍼는 안 적은 것**(`iso44j`).
- ★★★ **`iso44j` 가 급소다** — 안쪽 `inner` 는 타입이 안 적혔어도 **export 되지 않으니** `.d.ts` 에 안 나온다. `isolatedDeclarations` 가 요구하는 것은 **공개 표면**뿐이다.
- ★★★ **판이 갈린 행 `2 / 12`** — `iso44a`·`iso44h`. 7.0.2 는 **`TS9013`**(식 자리), 5.9.3 은 **`TS9007`/`TS9008`**(함수·메서드 이름 자리). 막는 **꼴은 같고 진단 코드와 자리가 다르다.**
- ★★ **`--declaration` 없이 주면 `TS5069`**(두 판) — 「cannot be specified without specifying option 'declaration' or option 'composite'」.
- ★★ **4.9.5 는 열두 행 전부 `TS5023`** — 옵션을 모른다(README 의 「5.5」와 어긋나지 않는다).

진단 전문 — 갈린 두 행.

```text
===== tsc --pretty false --noEmit --declaration --isolatedDeclarations iso44a.ts iso44h.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
iso44a.ts(2,12): error TS9013: Expression type can't be inferred with --isolatedDeclarations.
iso44h.ts(3,16): error TS9013: Expression type can't be inferred with --isolatedDeclarations.
(exit 1)
---- 5.9.3
iso44a.ts(1,17): error TS9007: Function must have an explicit return type annotation with --isolatedDeclarations.
iso44h.ts(2,5): error TS9008: Method must have an explicit return type annotation with --isolatedDeclarations.
(exit 2)
```

- ★★ 7.0.2 의 `TS9013` 「Expression type can't be inferred with --isolatedDeclarations.」은 **`n * 2` 를 가리킨다**(`(2,12)`). 5.9.3 의 `TS9007` 「Function must have an explicit return type annotation …」은 **함수 이름 `f`** 를 가리킨다(`(1,17)`).

적으면 무엇이 달라지나 — 37편 5절의 「`--declaration` 은 안 적힌 자리를 추론한다」를 한 쌍으로.

```text
===== tsc --pretty false --declaration --emitDeclarationOnly --outDir e44 iso44a.ts iso44b.ts ; 방출된 .d.ts 둘 (sh exit=0) =====
(exit 0)
===== 방출된 e44/iso44a.d.ts =====
export declare function f(n: number): number;
===== 방출된 e44/iso44b.d.ts =====
export declare function f(n: number): number;
두 .d.ts 가 한 글자도 같다
```

- ★★★ **두 `.d.ts` 가 한 글자도 같다** — 반환 타입을 적든 안 적든 `--declaration` 은 **`: number`** 를 썼다. `isolatedDeclarations` 는 **결과를 바꾸는 스위치가 아니라, 그 결과를 「추론 없이」 얻을 수 있게 하는 스위치**다.

```text
  같은 .d.ts 를 얻는 두 길

  --declaration                   타입 검사기가 n * 2 의 타입을 추론 ─> f(n: number): number
  --declaration --isolatedDeclarations   적힌 타입만 옮긴다 ─> 안 적었으면 TS9013 / TS9007 로 멈춘다
                                  ★ 적어 두면 파일 하나만 보는 도구도 같은 .d.ts 를 쓸 수 있다
```

비용 — **공개 표면에 타입을 적는 수고.** 대신 `.d.ts` 가 **파일 단위로** 나온다 — 참조 격자에서 `app` 이 기다리는 것이 그 `.d.ts` 다(1·2절). 그것으로 빌드가 **얼마나** 빨라지는지는 **재지 않았다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  core:  "composite": true                    .d.ts 를 내보내고 참조될 수 있게 한다          (1절)
  app:   "references": [{ "path": "../core" }] core 의 출력 .d.ts 를 보게 한다              (1·2절)
  tsc -b app                                  참조 순서대로 짓는다 — core 먼저             (1·3절)
  tsc -b app --verbose                        프로젝트마다 「최신인가 · 왜」                 (3절)
  tsc -b app --clean                          일지와 출력을 같이 지운다                     (3절)
  "isolatedDeclarations": true (+ declaration)  공개 표면의 추론을 금지한다               (4절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `composite` 없는 프로젝트를 `references` 로 | `TS6306` | 1절 |
| 참조된 `core` 를 안 짓고 `tsc -p app` | `TS6305` | 1절 |
| `references` 없이 `core` 의 `.ts` 를 import (`rootDir: src`) | `TS6059` | 1절 |
| 7.0.2 · `rootDir` 도 참조도 없이 밖의 `.ts` 를 import | `TS5011` | 1절 |
| `isolatedDeclarations` + 반환 타입 없는 export 함수 | 7.0.2 `TS9013` · 5.9.3 `TS9007` | 4절 |
| `isolatedDeclarations` + `export const c = [1, 2]` | `TS9017` | 4절 |
| `isolatedDeclarations` 만 (`declaration` 없이) | `TS5069` | 4절 |

**규칙 불릿**

- ★★★ **참조되는 쪽은 `composite`, 참조하는 쪽은 `references`, 짓는 명령은 `tsc -b`** — 하나라도 빠지면 16칸 중 14칸이 진단(1절).
- ★★★ **`app` 은 `core` 의 `.d.ts` 를 본다** — 해석은 `.ts` 로 풀려도 프로그램에는 출력 `.d.ts` 가 든다(2절).
- ★★★ **겉모습이 같은 `core` 변경은 `app` 을 다시 짓지 않는다** — 서명이 바뀌면 짓는다(3절).
- ★★★ **`dist` 만 지우면 `tsc -b` 는 모른다** — `--clean` 을 쓴다(3절).
- ★★ **`isolatedDeclarations` 는 공개 표면에만 타입을 요구한다** — 안쪽 헬퍼는 자유(4절 `iso44j`).

## 어디서 틀리나

- ★★★ 「**`references` 를 적었으니 `tsc -p app` 이 `core` 도 짓는다**」 — 안 짓는다. **`TS6305`**(1절). 짓는 것은 `tsc -b` 다.
- ★★★ 「**`app` 은 import 한 `core` 의 `.ts` 를 검사한다**」 — `.d.ts` 를 본다. `.d.ts` 를 고치면 **`core/src` 와 무관하게** 속는다(2절 ③).
- ★★★ 「**`dist` 를 지웠으니 다음 `tsc -b` 는 다시 짓는다**」 — 일지(`.tsbuildinfo`)가 남아 있으면 **「최신」이라며 `exit 0`**(3절 5단계).
- ★★ 「**`composite` 가 없으면 아무것도 안 지어진다**」 — `tsc -b` 는 `core` 의 **`.js` 는 짓고** `app` 에서 `TS6306`(1절).
- ★★ 「**참조 없이도 모노레포는 된다**」 — 5.9.3 은 `core` 를 `app/dist` 안에 **한 벌 더** 짓고(`exit 0`), 7.0.2 는 `TS5011`(1절 끝).
- ★★ 「**`isolatedDeclarations` 는 모든 함수에 반환 타입을 요구한다**」 — **export 된 것만**, 그리고 `return 1` 같은 **리터럴 반환은 통과**했다(4절).
- ★ 「**`isolatedDeclarations` 를 켜면 `.d.ts` 가 달라진다**」 — **한 글자도 같았다**(4절 끝). 바뀌는 것은 **얻는 방법**이다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **tsc 빌드 모드의 계약** | `composite`·`references`·`tsc -b` 의 요구 — `TS6306`·`TS6305`·`TS6059` | 1절 — 두 판 같음 |
| **★★★ tsc 동작** | 참조된 import 자리에 출력 `.d.ts` 를 끼운다 | 2절 ② ③ |
| **★★★ tsc 동작 — mtime** | `tsc -b` 의 「최신인가」는 **일지와 mtime** 을 본다 — 출력 폴더의 존재는 안 본다 | 3절 5단계 · 판정 문구의 「older than」 |
| **★ 판에 매인 것** | `tsc -b` 의 `TS6059` 종료 코드 · `rootDir` 없는 칸(`TS5011` 대 `exit 0`) · `isolatedDeclarations` 진단 코드 | 1·4절 |
| **★ 판의 존재** | `isolatedDeclarations` — 4.9.5 `TS5023` · 5.9.3 있음 | 4절 |
| **안 잰 것** | 빌드 시간 · 병렬 빌드(`--builders`) | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **패키지 경계가 뚜렷한 모노레포** — `core` 는 `composite`, `app` 은 `references`, CI 는 `tsc -b` | `tsc -p app` 만 돌리기 — `core` 가 낡으면 `TS6305` 이거나 낡은 `.d.ts` 로 검사된다(1·2절) |
| ★★★ 청소는 **`tsc -b --clean`** | `rm -rf dist` — 일지가 남아 `tsc -b` 가 아무것도 안 짓는다(3절) |
| ★★ `rootDir` 를 **명시** | 비워 두기 — 5.9.3 은 조용히 부풀고 7.0.2 는 `TS5011`(1절 끝) |
| ★★ `isolatedDeclarations` — `.d.ts` 를 **파일 단위 도구**로 뽑고 싶을 때 | 공개 표면이 추론에 크게 기댈 때 — 전부 적어야 한다(4절) |

## 핵심 문장

1. **참조되는 쪽은 `composite`, 참조하는 쪽은 `references`, 짓는 명령은 `tsc -b`** — 셋이 다 있는 칸만 빌드됐다(`2 / 16`).
2. **`app` 은 `core` 의 `.d.ts` 를 본다** — 해석 창은 `.ts` 라고 답해도 프로그램 창은 `.d.ts` 를 보여 주고, `.d.ts` 를 고치면 `app` 이 속는다.
3. **`tsc -b` 는 겉모습이 같은 변경의 의존자를 건너뛴다** — 몸통만 바꾸면 `app` 은 「up to date with .d.ts files」, 서명을 바꾸면 다시 짓는다.
4. **`dist` 만 지우면 `tsc -b` 는 일지를 믿고 아무것도 안 짓는다** — `exit 0` 인데 `.d.ts` 가 없다. `--clean` 을 쓴다.
5. **`isolatedDeclarations` 는 공개 표면의 추론을 금지할 뿐 `.d.ts` 를 바꾸지 않는다** — 판마다 진단 코드와 자리가 달랐다(`TS9013` 대 `TS9007`).

## 관련 자료

- [**43번 주제** — `tsconfig` 의 나머지 선택](../43-remaining-tsconfig-choices/) — ★★★ **README 의 선행.** `incremental` 이 바뀐 파일과 의존자만 다시 방출 · `declaration` 이 겉모습을 비교. **여기는 그것을 프로젝트 단위로.**
- [**37번 주제** — 선언 파일 작성](../37-writing-declaration-files/) 5절 — `--declaration` 이 안 적힌 자리를 추론해 쓴다. 4절의 한 쌍이 그 인용이다.
- [**35번 주제** — 모듈 해석](../35-module-resolution/) 3절 — `--traceResolution` 을 처음 쓴 곳. 2절 ①.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) 5절 — 파일 하나만 보는 도구의 한계. `isolatedDeclarations` 는 **`.d.ts` 쪽의** 같은 문제다.
- [**45번 주제**](../45-type-level-performance/)(타입 수준 성능) — 이 문서가 재지 않은 **시간**.

## 용어 풀이

> **프로젝트 참조(project references)** — 한 `tsconfig.json` 이 다른 프로젝트를 `references` 로 가리키는 것. 참조된 프로젝트의 **출력 `.d.ts`** 를 본다.\
> 예: 2절 ② 「File is output of project reference source」.

> **`composite`** — 참조될 수 있는 프로젝트의 표시. `.d.ts` 방출과 일지(`.tsbuildinfo`)를 켠다. 없으면 참조하는 쪽이 `TS6306`.\
> 예: 1절 · 3절 `core/tsconfig.tsbuildinfo`.

> **`tsc -b`(build mode)** — 참조 그래프를 따라 프로젝트를 순서대로, 필요한 것만 짓는다. `-b` 는 **첫 인자**라야 한다(1절 — 뒤에 두면 `TS5023`).\
> 예: 3절 로그.

> **`TS6305`** — 「Output file '…' has not been built from source file '…'.」 — 참조된 프로젝트의 출력이 없다.\
> 예: 1절 `-p` 칸 · 진단 전문.

> **`isolatedDeclarations`** — 공개 표면의 타입을 **추론 없이** 옮길 수 있게, 추론이 필요한 자리를 진단으로 막는 옵션. `declaration` 또는 `composite` 가 필요하다(`TS5069`).\
> 예: 4절.

> **`TS9013` · `TS9007` · `TS9008` · `TS9010` · `TS9017` · `TS9037`** — `isolatedDeclarations` 의 진단 — 식 · 함수 · 메서드 · 변수 · 배열 · 기본 export.\
> 예: 4절 격자.

## 더 들어가면

- **병렬 빌드** — 여러 프로젝트를 동시에 짓는 쪽은 **던지지 않았다.**
- **`prepend`·`outFile` 참조** — 43편 1절에서 `outFile` 이 7.0.2 `TS5102` 다. 이 문서는 **다루지 않는다.**
- **런타임** — `app/dist/main.js` 를 `node` 로 돌리는 것은 **던지지 않았다.** 참조가 방출물의 import 경로를 어떻게 다루는지도 이 문서는 **묻지 않았다.**
