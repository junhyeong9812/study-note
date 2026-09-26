# ts/syntax/40 — `strictNullChecks` 의 파급 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `strictNullChecks`](https://www.typescriptlang.org/tsconfig/#strictNullChecks)(「When `strictNullChecks` is `false`, `null` and `undefined` are effectively ignored by the language. This can lead to unexpected errors at runtime.」 · 「When … `true`, `null` and `undefined` have their own distinct types」).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다.
> ★ 레퍼런스의 「unexpected errors at runtime」을 **이 문서가 격자로 셌다**(1절) — 여섯 탐침 중 몇이 실제로 터지나.
> **실행 검증** — 본판은 아래다.

```text
===== tsc --version · node --version · "$NODE20" --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
v20.19.6
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(끈 채 방출한 `.js` + `node`)이다.** 「끄면 조용해지는 칸」이 **런타임에서 무엇이 되나**를 탐침 여섯으로 센다(1절).
> ★★ **2창을 바꿨다 — `null` 탐침 대신 `symbol` 탐침**(제5의 상태). `strictNullChecks` 를 끄면 `null` 탐침이 `undefined` 를 **받아 버려** 침묵한다(2절 10행) — 그래서 이 문서의 타입 탐침은 `const p: symbol = …` 다.
> ★★ **DOM 탐침(`querySelector`)은 브라우저 대신 대역으로 돌렸다**(제5의 상태) — node 에는 `document` 가 없어 **찾는 요소가 없는 페이지**를 한 줄짜리 `shim40.cjs` 로 흉내 냈다. 바꾼 창이 못 보는 것 — **진짜 DOM 의 반환값**은 이 문서가 확인하지 않았다.
> ★★★ **40 은 12 와 39 에서 온다.** [**12번 주제**](../12-narrowing/) 5절이 「`--strict false` 로 좁히기 탐침 네 파일 중 셋이 갈린다」 · 「끄면 진단이 줄 뿐 버그가 주는 것은 아니다」를 **이미 쟀다.** [**39번 주제**](../39-strict-bundle/)가 `strictNullChecks` 를 **다른 하위 플래그가 기대는 축**으로 세웠다. [**30번 주제**](../30-type-assertions-and-non-null/) 2절이 **`!` 가 방출에서 지워지는 것**을 쟀다 — 인용한다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · `symbol` 탐침이 말하는 타입 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 두 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 예외는 **타입과 메시지만** 찍었다 — 스택(절대 경로)은 안 실었다 |
| **호스트에 매인다** | `TypeError` 의 **문구**(「Cannot read properties of undefined (reading '…')」) | node v18.19.1 의 V8 문구다 — **판이 오르면 문구는 바뀔 수 있다**, `TypeError` 라는 **타입**을 근거로 쓴다 |
| **★ 대역** | 1절 `nn40d` 의 `document` | `shim40.cjs` 가 `querySelector` 를 `null` 로 돌려주게 만들었다 — 진짜 DOM 이 아니다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | `strictNullChecks` 가 검사 **시간**에 주는 영향 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**`strictNullChecks` 는 「빈 상자」 딱지다. 켜면 「이 상자는 비어 있을 수 있음」이 상자 겉에 적혀서, 열기 전에 확인하라고 계산대가 붙잡는다. 끄면 딱지가 **모든 상자에서 떼어진다** — 빈 상자도 꽉 찬 상자와 똑같이 보이고, 계산대는 통과시키고, 집에서 열어 보면 비어 있다.**

| 비유 | 실체 |
|---|---|
| 「비어 있을 수 있음」 딱지 | `T \| undefined` · `T \| null` — `find`·`Map.get`·`?.`·`?` 매개변수가 붙인다 |
| 계산대가 붙잡는다 | 켬 — `TS18048`·`TS2532`·`TS18047`(1절) |
| ★★★ 딱지를 **전부** 뗀다 | 끔 — `null`·`undefined` 가 **모든 타입의 원소**가 된다(2절 — `let n: number = null` 통과) |
| ★★★ 계산대는 통과, 집에서 빈 상자 | 끈 채 방출 → node **`TypeError`**(1절 — **6 / 6**) |
| 상자 겉만 바꾼다 — 내용물은 같다 | 켜고 방출한 `.js` 와 끄고 방출한 `.js` 가 **한 글자도 같다**(1절 — **6 / 6**) |
| 열기 전에 확인하는 네 방법 | `if (x !== undefined)` · `?.` · `??` · `!`(3절) |
| ★★ 「비어 있지 않다고 **내가** 보증」 | `!` — 계산대만 통과시키고 **방출에서 지워진다**(3절 · 30편 2절) |

- ★★★ 한 줄로 — 「**`strictNullChecks` 는 `null`·`undefined` 를 따로 선 타입으로 만든다. 끄면 그 둘이 모든 타입에 흡수되어 진단이 사라지지만, 방출물은 한 글자도 안 바뀌고 런타임의 `undefined` 는 그대로 온다.**」

```text
  같은 한 줄, 스위치 두 판

  const hit = scores.find((n) => n > 90);      hit.toFixed(1)

  켬    hit: number | undefined     → TS18048 'hit' is possibly 'undefined'.   (여기서 멈춘다)
  끔    hit: number                 → 진단 없음 → 방출 → node: TypeError        ★ 방출물은 켬과 같은 글자
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 끄면 무엇이 조용해지고, 조용해진 칸은 실행에서 어떻게 되나** — 탐침 여섯 × 켬/끔 × 방출·`node`(1절).
2. **★★ 끄면 타입이 어떻게 바뀌나** — `null`·`undefined` 가 모든 타입의 원소가 되는 것(2절).
3. **★★★ 켜면 무엇이 필수가 되나** — 좁히기 네 수단과 그 흔적이 방출물에 남는가(3절 · 12편).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 끈 채 방출한 `.js` + `node`** | 조용해진 칸이 **런타임에서 무엇이 되나** | 실행 결과 | **본체**(1절 — 탐침 여섯, 따로 컴파일·따로 실행) |
| ★★★ **방출물 대조(`cmp`)** | 켬/끔의 방출물이 **같은 글자인가** | 참/거짓 | 1절 — 「타입만 바뀐다」의 증명 |
| ★★ **2창 변형 — `symbol` 탐침** | 켬/끔에서 **계산된 타입** | 계산된 것 | 2·3절 — ★ **제5의 상태**(`null` 탐침이 끈 판에서 침묵해서) |
| ★ **대역 — `shim40.cjs`** | DOM 탐침을 node 에서 | 흉내 | 1절 `nn40d` — ★ **제5의 상태** |
| ★ **교차 갈래 — Kotlin · C#** | 같은 질문(「`null` 을 타입이 아나」)의 다른 답 | **인용**(이 머신에서 다시 안 돌렸다) | 「구현 세부사항 대 언어 보장」 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — | — |

비용 — 탐침 여섯 × (검사 둘 · 방출 둘 · `node` 하나) + 검사 넷 · 방출 둘 · `node` 하나.

```text
  이 주제의 축 — 「누가 null 을 아나」

  타입 검사(켬)       T | undefined 로 따로 든다       → 쓰기 전에 좁혀라 (TS18048 · TS2532 · TS18047)
  타입 검사(끔)       T 에 흡수된다                    → 아무 말 없다
  방출물             켬 · 끔 한 글자도 같다             → 타입 층의 스위치다
  node               undefined 는 늘 undefined        → 끈 쪽에서 좁히지 않은 줄이 TypeError
```

### (1) ★★★ 끄면 조용해지는 격자 — 그리고 node 에서 터진다

**언제 쓰나** — 「우리 프로젝트는 `strictNullChecks` 를 꺼 두었으니 이런 에러가 안 난다」가 **좋은 소식인지** 따질 때.

탐침 여섯 — 전부 **스크립트**(export 없음)이고 `try … catch` 가 예외의 **타입과 메시지**만 찍는다.

```ts
// nn40a.ts
interface Profile {
    nick?: { text: string };
}
const profile: Profile = {};
try {
    const len = profile.nick?.text.length;
    console.log("[a]", len.toFixed(0));
} catch (e) {
    console.log("[a]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40b.ts
const scores = [40, 55, 62];
try {
    const hit = scores.find((n) => n > 90);
    console.log("[b]", hit.toFixed(1));
} catch (e) {
    console.log("[b]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40c.ts
const labels = new Map<string, string>([["ko", "한국어"]]);
try {
    console.log("[c]", labels.get("en").toUpperCase());
} catch (e) {
    console.log("[c]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40d.ts
try {
    const el = document.querySelector(".banner");
    console.log("[d]", el.textContent);
} catch (e) {
    console.log("[d]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40e.ts
function lookup(id: number): string | undefined {
    return id === 1 ? "one" : undefined;
}
try {
    console.log("[e]", lookup(2).length);
} catch (e) {
    console.log("[e]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40f.ts
function shout(word?: string) {
    return word.toUpperCase();
}
try {
    console.log("[f]", shout());
} catch (e) {
    console.log("[f]", (e as Error).constructor.name, (e as Error).message);
}
```

```js
// shim40.cjs
// node 에는 document 가 없다 -- 찾는 요소가 없는 페이지를 흉내 내는 한 줄짜리 대역
globalThis.document = { querySelector: () => null };
```

켠 판(7.0.2 기본 — `strict` 에 딸려 켜져 있다)의 진단부터.

```text
===== tsc --pretty false --noEmit -t es2022 <nn40a.ts … nn40f.ts 를 하나씩> (sh exit=0) =====
nn40a.ts(7,24): error TS18048: 'len' is possibly 'undefined'.
(exit 1)
nn40b.ts(4,24): error TS18048: 'hit' is possibly 'undefined'.
(exit 1)
nn40c.ts(3,24): error TS2532: Object is possibly 'undefined'.
(exit 1)
nn40d.ts(3,24): error TS18047: 'el' is possibly 'null'.
(exit 1)
nn40e.ts(5,24): error TS2532: Object is possibly 'undefined'.
(exit 1)
nn40f.ts(2,12): error TS18048: 'word' is possibly 'undefined'.
(exit 1)
```

```bash
# ts38b-off40.sh
#!/usr/bin/env bash
# 탐침 여섯 × strictNullChecks 켬/끔 -- 진단 코드 · 끈 채 방출한 .js 를 node 로 돌린 결과
# 탐침마다 따로 컴파일하고 따로 돌린다(한 탐침이 던져도 다음 칸이 안 가려지게) · 켠 채로도 방출해 끈 쪽과 cmp
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
probes=(nn40a.ts nn40b.ts nn40c.ts nn40d.ts nn40e.ts nn40f.ts)
codes() { grep -o '^[^ ]*: error TS[0-9]*' | sed 's/^[^(]*(\([0-9]*\),[0-9]*): error /\1:/' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-9s %-14s %-8s %s\n' "탐침" "켬" "끔" "끔 → 방출 → node -r ./shim40.cjs"
quiet=0; boom=0; same=0; total=0; all=""
for p in "${probes[@]}"; do
  onr=$(tsc --pretty false --noEmit -t es2022 "$p" 2>&1); offr=$(tsc --pretty false --noEmit -t es2022 --strictNullChecks false "$p" 2>&1)
  case "$onr$offr" in *"error TS5"*) echo "★ 설정 진단이 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
  on=$(codes <<< "$onr"); off=$(codes <<< "$offr")
  o="$D/${p%.ts}"; tsc --pretty false -t es2022 --strictNullChecks false --outDir "$o" "$p" > "$D/emit.log" 2>&1; erc=$?
  js="$o/${p%.ts}.js"
  if [ ! -f "$js" ]; then echo "★ 방출물이 없다($p, exit $erc)"; exit 6; fi
  tsc --pretty false -t es2022 --outDir "$o-on" "$p" > "$D/emit.log" 2>&1
  if cmp -s "$js" "$o-on/${p%.ts}.js"; then same=$((same+1)); fi
  run=$(node -r ./shim40.cjs "$js" 2>&1); nrc=$?
  printf '%-9s %-14s %-8s %s (exit %s)\n' "$p" "${on:-OK}" "${off:-OK}" "$run" "$nrc"
  total=$((total+1)); all="$all|${on:-OK}|${off:-OK}"
  [ -n "$on" ] && [ -z "$off" ] && quiet=$((quiet+1))
  [ -z "$off" ] && case $run in *TypeError*) boom=$((boom+1)) ;; esac
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 켬과 끔이 전부 같다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "끄면 진단이 사라진 탐침 $quiet / $total · 그중 방출물이 node 에서 TypeError 로 끝난 탐침 $boom / $total"
echo "켜고 방출한 .js 와 끄고 방출한 .js 가 한 글자도 같은 탐침 $same / $total"
```

```text
===== bash ts38b-off40.sh (sh exit=0) =====
탐침    켬            끔      끔 → 방출 → node -r ./shim40.cjs
nn40a.ts  7:TS18048      OK       [a] TypeError Cannot read properties of undefined (reading 'toFixed') (exit 0)
nn40b.ts  4:TS18048      OK       [b] TypeError Cannot read properties of undefined (reading 'toFixed') (exit 0)
nn40c.ts  3:TS2532       OK       [c] TypeError Cannot read properties of undefined (reading 'toUpperCase') (exit 0)
nn40d.ts  3:TS18047      OK       [d] TypeError Cannot read properties of null (reading 'textContent') (exit 0)
nn40e.ts  5:TS2532       OK       [e] TypeError Cannot read properties of undefined (reading 'length') (exit 0)
nn40f.ts  2:TS18048      OK       [f] TypeError Cannot read properties of undefined (reading 'toUpperCase') (exit 0)

끄면 진단이 사라진 탐침 6 / 6 · 그중 방출물이 node 에서 TypeError 로 끝난 탐침 6 / 6
켜고 방출한 .js 와 끄고 방출한 .js 가 한 글자도 같은 탐침 6 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★ **켬** — 여섯 다 막혔다. 코드는 셋으로 갈린다 — 이름이 있는 값은 **`TS18048`**(「'hit' is possibly 'undefined'.」) · `null` 쪽은 **`TS18047`**(「'el' is possibly 'null'.」) · 호출 결과처럼 이름이 없는 식은 **`TS2532`**(「Object is possibly 'undefined'.」).
- ★★★ **끔** — 여섯 다 **`OK`**. 스크립트 마지막 줄 — **「끄면 진단이 사라진 탐침 6 / 6」.**
- ★★★ **끈 채 방출 → node** — 여섯 다 **`TypeError`** — 「Cannot read properties of undefined (reading '…')」, `nn40d` 만 **`of null`**. **「그중 … TypeError 로 끝난 탐침 6 / 6」.** 레퍼런스의 「unexpected errors at runtime」이 **여섯 중 여섯**이었다.
- ★★★ **「켜고 방출한 `.js` 와 끄고 방출한 `.js` 가 한 글자도 같은 탐침 6 / 6」** — 스위치는 **방출물을 한 글자도 안 바꿨다.** 켰을 때 나던 진단은 **이 `TypeError` 를 미리 가리킨 것**이었다.
- ★ `nn40a` — `?.` 는 **그 자리**에서만 멈춘다. `profile.nick?.text.length` 는 `undefined` 를 **돌려주고**, 다음 줄의 `len.toFixed` 가 터졌다. `?.` 를 썼다고 **결과가 안전해지지 않는다.**

끈 채 방출한 파일 하나를 연다.

```text
===== tsc --pretty false -t es2022 --strictNullChecks false --outDir e40 nn40b.ts (tsc exit=0) =====
===== 방출된 e40/nn40b.js =====
"use strict";
const scores = [40, 55, 62];
try {
    const hit = scores.find((n) => n > 90);
    console.log("[b]", hit.toFixed(1));
}
catch (e) {
    console.log("[b]", e.constructor.name, e.message);
}
```

- ★★ 방출물은 **소스에서 타입만 지운 것**이다 — `hit.toFixed(1)` 을 막을 어떤 검사도 **심어지지 않았다.** 01편의 「타입은 방출물에 남지 않는다」가 `null` 쪽에서 그대로다.

```text
  여섯 탐침 — 켬에서 붙잡힌 자리 = 끔에서 터진 자리

  탐침     undefined/null 을 만드는 것          켬 (진단)       끔 → node
  nn40a   ?. 의 결과를 다시 씀                   TS18048        TypeError … (reading 'toFixed')
  nn40b   Array.prototype.find                 TS18048        TypeError … (reading 'toFixed')
  nn40c   Map.prototype.get                    TS2532         TypeError … (reading 'toUpperCase')
  nn40d   document.querySelector (대역)         TS18047        TypeError … of null (reading 'textContent')
  nn40e   T | undefined 를 돌려주는 함수          TS2532         TypeError … (reading 'length')
  nn40f   선택 매개변수 word?                     TS18048        TypeError … (reading 'toUpperCase')
          ★ 방출물은 켬 · 끔 6 / 6 같은 글자
```

비용 — 끄면 **진단 여섯이 `TypeError` 여섯**으로 바뀐다. 실패 지점은 같지만 **발견 시점**이 검사에서 실행으로 밀린다. 37편 2절의 「`.d.ts` 거짓말 — 컴파일 통과, node 에서 드러남」과 **같은 모양**이다.

### (2) ★★ 끄면 `null`·`undefined` 가 모든 타입의 원소가 된다

**언제 쓰나** — 「끄면 무엇이 달라지나」를 **타입의 글자**로 볼 때.

```ts
// absorb40.ts
let n: number = null;
let s: string = undefined;
const xs: number[] = [1, null, undefined];
declare const maybe: number | null;
declare const opt: { tag?: string };
const p1: symbol = maybe;
const p2: symbol = opt.tag;
const p3: symbol = xs.find((x) => x > 1);
declare const u: undefined;
const p4: null = u;
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 absorb40.ts ; 이어서 --strictNullChecks false 를 붙여 한 번 더 (sh exit=0) =====
absorb40.ts(1,5): error TS2322: Type 'null' is not assignable to type 'number'.
absorb40.ts(2,5): error TS2322: Type 'undefined' is not assignable to type 'string'.
absorb40.ts(3,26): error TS2322: Type 'null' is not assignable to type 'number'.
absorb40.ts(3,32): error TS2322: Type 'undefined' is not assignable to type 'number'.
absorb40.ts(6,7): error TS2322: Type 'number | null' is not assignable to type 'symbol'.
  Type 'null' is not assignable to type 'symbol'.
absorb40.ts(7,7): error TS2322: Type 'string | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
absorb40.ts(8,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
absorb40.ts(10,7): error TS2322: Type 'undefined' is not assignable to type 'null'.
(exit 1)
absorb40.ts(6,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
absorb40.ts(7,7): error TS2322: Type 'string' is not assignable to type 'symbol'.
absorb40.ts(8,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
(exit 1)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **켬** — 1·2·3행의 대입이 **`TS2322` 넷**(「Type 'null' is not assignable to type 'number'.」 · `'undefined'` → `'string'` · 배열 원소 둘).
- ★★★ **끔** — 1·2·3행이 **통과**했다. `null`·`undefined` 가 `number`·`string` 에 **들어간다.** 레퍼런스의 「effectively ignored by the language」다.
- ★★★ **`symbol` 탐침**(6·7·8행) — 켬 **`number | null`** · **`string | undefined`** · **`number | undefined`** → 끔 **`number`** · **`string`** · **`number`**. 유니온의 `null`·`undefined` 가 **흡수되어 사라졌다.** 12편 5절의 「`object | null` 이 그냥 `object`」와 같은 칸이다.
- ★★★ **10행 `const p4: null = u`**(`u: undefined`) — 켬 `TS2322`, 끔 **진단 없음.** 끈 판에서 `null` 타입이 `undefined` 를 **받아 버린다** — 그래서 이 문서는 `null` 탐침 대신 **`symbol` 탐침**을 쓴다(머리말의 제5의 상태).

```text
  한 타입의 원소 — 스위치 두 판

  켬    number = { 1, 2, 3, … }                    null · undefined 는 따로 선 타입
  끔    number = { 1, 2, 3, …, null, undefined }   ★ 모든 타입이 둘을 품는다 → 유니온에서 흡수된다
```

비용 — 끄면 **「이 값은 비어 있을 수 없다」를 타입으로 적을 방법이 없다.** 모든 타입이 이미 `null`·`undefined` 를 품기 때문이다.

### (3) ★★★ 켜면 좁히기가 필수가 된다 — 네 수단과 방출물

**언제 쓰나** — 1절의 여섯 진단을 **고칠 때**.

```ts
// flow40.ts
declare const found: number | undefined;
const p0: symbol = found;
if (found !== undefined) {
    const p1: symbol = found;
}
if (found) {
    const p2: symbol = found;
}
const p3: symbol = found ?? 0;
const p4: symbol = found?.toFixed(1);
const p5: symbol = found!;
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 flow40.ts (tsc exit=1) =====
flow40.ts(2,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
flow40.ts(4,11): error TS2322: Type 'number' is not assignable to type 'symbol'.
flow40.ts(7,11): error TS2322: Type 'number' is not assignable to type 'symbol'.
flow40.ts(9,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
flow40.ts(10,7): error TS2322: Type 'string | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
flow40.ts(11,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ **2행** — 좁히기 전 `found` 는 **`number | undefined`**.
- ★★★ **4행 `if (found !== undefined)`** · **7행 `if (found)`** · **9행 `found ?? 0`** · **11행 `found!`** — 넷 다 **`number`**. 좁히기 수단은 12편 1·2절이 정본이다.
- ★★ **10행 `found?.toFixed(1)`** — **`string | undefined`**. `?.` 는 좁히는 것이 아니라 **`undefined` 를 결과로 흘려보낸다** — 1절 `nn40a` 가 거기서 터졌다.
- ★ 7행의 진릿값 좁히기는 **`0` 도 거짓**으로 친다 — 12편 2절이 그 칸(「`""` 와 `0` 도 거짓이기 때문」)을 쟀다. 이 탐침은 타입만 봤다.

네 수단을 **실행되는 코드**로 쓰고 방출한다.

```ts
// bang40.ts
const scores = [40, 55, 62];
const hit = scores.find((n) => n > 90);
const a = hit !== undefined ? hit.toFixed(1) : "none";
const b = hit?.toFixed(1) ?? "none";
const c = hit!;
console.log("[1]", a, b, c);
try {
    console.log("[2]", hit!.toFixed(1));
} catch (e) {
    console.log("[2]", (e as Error).constructor.name, (e as Error).message);
}
```

```text
===== tsc --pretty false --noEmit -t es2022 bang40.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --outDir e40b bang40.ts (tsc exit=0) =====
===== 방출된 e40b/bang40.js =====
"use strict";
const scores = [40, 55, 62];
const hit = scores.find((n) => n > 90);
const a = hit !== undefined ? hit.toFixed(1) : "none";
const b = hit?.toFixed(1) ?? "none";
const c = hit;
console.log("[1]", a, b, c);
try {
    console.log("[2]", hit.toFixed(1));
}
catch (e) {
    console.log("[2]", e.constructor.name, e.message);
}
```

```text
===== node e40b/bang40.js (node exit=0) =====
[1] none none undefined
[2] TypeError Cannot read properties of undefined (reading 'toFixed')
```

- ★★ 검사 — **진단 0줄.** 네 수단 모두 `TS18048` 을 **없앴다.**
- ★★★ 방출물 — `hit !== undefined ? …` · `hit?.toFixed(1) ?? "none"` 은 **그대로 남았고**, `const c = hit!;` 은 **`const c = hit;`** · `hit!.toFixed(1)` 은 **`hit.toFixed(1)`** — **`!` 만 지워졌다.**
- ★★★ node — `[1] none none undefined` · **`[2] TypeError Cannot read properties of undefined (reading 'toFixed')`**. 검사를 **실제로 하는** 셋(`!==`·`?.`·`??`)은 안전했고, **`!` 는 진단만 없애고 1절의 끈 판과 같은 `TypeError`** 를 냈다(30편 2절).

```text
  좁히기 네 수단 — 검사 층과 실행 층

  수단                      tsc (켬)          방출물              node (hit = undefined)
  if (hit !== undefined)    number 로 좁힘     그대로 남는다        안전 — "none"
  hit?.toFixed(1)           string | undefined 그대로 남는다        안전 — undefined
  hit ?? "none"             number 로 좁힘     그대로 남는다        안전 — "none"
  hit!                      number 로 우김     ★ 지워진다           ★ TypeError — 끈 판과 같다
```

비용 — 켜면 **`T | undefined` 가 흘러가는 자리마다** 좁히기가 한 번 필요하다. 그 수고를 **`!` 로 때우면** 1절의 끈 판으로 돌아간다 — 진단만 없는 쪽으로.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  --strictNullChecks false                  null · undefined 가 모든 타입에 흡수된다      (2절)
  "strict": true, "strictNullChecks": false   묶음은 두고 이것만 끈다(39편 2절)
  if (x !== undefined) { … }                좁힌다 — 방출에 남는다                        (3절)
  x ?? 기본값                                좁힌다 — 방출에 남는다                        (3절)
  x?.m()                                    결과가 T | undefined — 좁히지 않는다          (1·3절)
  x!                                        우긴다 — 방출에서 지워진다                     (3절 · 30편)
```

**금지 사례** — 켠 판에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `T \| undefined` 인 **이름**에 멤버 접근 | `TS18048` | 1절 `nn40a`·`b`·`f` |
| `T \| null` 인 이름에 멤버 접근 | `TS18047` | 1절 `nn40d` |
| `T \| undefined` 인 **식**(호출 결과)에 멤버 접근 | `TS2532` | 1절 `nn40c`·`e` |
| `let n: number = null` · `number[]` 에 `undefined` | `TS2322` | 2절 |

**규칙 불릿**

- ★★★ **끄면 `null`·`undefined` 가 모든 타입의 원소**가 된다 — 유니온에서 흡수된다(2절).
- ★★★ **켬/끔은 방출물을 안 바꾼다** — 6 / 6 한 글자도 같다(1절).
- ★★★ **끄고 조용해진 칸은 런타임에서 `TypeError`** 다 — 6 / 6(1절).
- ★★ **`?.` 의 결과는 `T | undefined`** — 좁히지 않는다(1절 `nn40a` · 3절 10행).
- ★★★ **`!` 는 검사 층에서만 좁힌다** — 방출에서 지워지고 런타임은 끈 판과 같다(3절).

## 어디서 틀리나

- ★★★ 「**끄면 이런 에러가 안 난다**」 — **검사 진단**이 안 날 뿐이다. 같은 줄이 node 에서 `TypeError`(1절 6 / 6).
- ★★★ 「**켜면 런타임 검사가 추가된다**」 — 방출물은 **한 글자도 같다**(1절 `cmp` 6 / 6). 켬이 바꾸는 것은 **검사**뿐이다.
- ★★ 「**`?.` 를 썼으니 안전하다**」 — `?.` 는 **`undefined` 를 돌려준다.** 그 결과를 다시 쓰면 터진다(1절 `nn40a`).
- ★★★ 「**`!` 로 고쳤다**」 — 진단만 없어졌다. 방출에서 지워지고 끈 판과 같은 `TypeError`(3절).
- ★★ 「**끈 판에서도 `null` 탐침으로 타입을 볼 수 있다**」 — 끈 판의 `null` 타입은 `undefined` 를 **받아 버린다**(2절 10행). 탐침을 `symbol` 로 바꿔야 한다.
- ★ 「**`find` 는 못 찾으면 `null`**」 — **`undefined`** 다(1절 `nn40b` — 「of undefined」). `null` 을 돌려준 것은 `querySelector`(대역) 쪽이다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **문서(TSConfig 레퍼런스)** | 끄면 `null`·`undefined` 가 사실상 무시된다 · 켜면 따로 선 타입 | 기준 소스 |
| **컴파일러 동작** | 켬/끔이 방출물을 안 바꾼다 | 1절 `cmp` 6 / 6 |
| **컴파일러 동작** | 끄면 유니온의 `null`·`undefined` 가 흡수된다 · `null` 타입이 `undefined` 를 받는다 | 2절 |
| **컴파일러 동작** | `!` 는 방출에서 지워진다 | 3절 · 30편 2절 |
| **★ 이 판(7.0.2)의 관찰** | 진단 코드가 이름/식에 따라 `TS18048`·`TS2532` 로 갈린다 | 1절 |
| **호스트(node v18)** | 없는 값의 멤버 접근은 `TypeError` — 문구는 V8 의 것 | 1·3절 |
| **★ 대역** | `document.querySelector` 가 `null` 을 돌려주는 페이지 | `shim40.cjs` — **진짜 DOM 은 확인하지 않았다** |
| **교차 갈래 — Kotlin** | `String` 과 `String?` 는 **처음부터 다른 타입**이다(세 가지 에러) · `!!` 는 **런타임 검사를 심는다**(`Intrinsics.checkNotNull`) — 컴파일러가 심는 다른 검사는 플래그로 끌 수 있어도 `!!` 는 안 꺼진다 | [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/) 1·3·5절 — **인용**, 이 머신에서 다시 안 돌렸다 |
| **교차 갈래 — C#** | 널 허용 참조 타입은 **경고**(`CS8600`·`CS8602`)이고 **IL 이 같다** — 켜도 런타임은 그대로 | [`../../../csharp/syntax/06-nullable-reference-types/`](../../../csharp/syntax/06-nullable-reference-types/) 1·2절 — **인용** |
| **안 잰 것** | 검사 시간 · 진짜 브라우저의 `querySelector` | **재지 않았다** · 대역으로 돌렸다 |

- ★★★ 세 언어를 한 줄로 — **Kotlin 은 `null` 가능성이 타입에 처음부터 들어 있고 `!!` 가 검사를 심는다. C# 은 주석(경고)이고 IL 이 같다. TS 는 스위치로 켜고 끄며 방출물이 같다** — C# 쪽에 가깝고, 켠 판의 진단이 **에러**라는 점만 다르다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **켠다**(7.0 기본) — 1절의 여섯이 전부 검사에서 잡힌다 | ★★★ **끄기** — 진단이 `TypeError` 로 바뀔 뿐이다(1절) |
| ★★ **`!==`·`??`** — 좁히면서 **실행에도 남는** 검사 | `?.` 로 끝내기 — 결과를 다시 쓰면 터진다(1절 `nn40a`) |
| ★ **`!`** — 정말 **다른 곳이 보증하는** 값에만(초기화 순서 등) | `!` 로 진단 없애기 — 끈 판과 같다(3절) |
| ★ 옮기는 동안 **`strict: true` + `strictNullChecks: false`** 로 잠시(39편) | 끈 채로 두기 — 39편 5절의 플래그 셋이 이것에 기댄다 |

## 핵심 문장

1. **`strictNullChecks` 는 `null`·`undefined` 를 따로 선 타입으로 만든다** — 끄면 둘이 모든 타입에 흡수되어 `let n: number = null` 이 통과한다.
2. **끄면 조용해진 여섯 칸이 node 에서 여섯 다 `TypeError` 였다** — 스위치는 방출물을 한 글자도 안 바꿨고(6 / 6), 켰을 때의 진단은 그 `TypeError` 를 미리 가리킨 것이다.
3. **켜면 `T | undefined` 가 흐르는 자리마다 좁히기가 필수다** — `!==`·`??` 는 방출에 남아 실행도 지키고, `?.` 는 `undefined` 를 흘려보내고, `!` 는 방출에서 지워진다.
4. **`!` 로 진단을 없애면 끈 판으로 돌아간다** — 같은 `TypeError` 다.

## 관련 자료

- [**12번 주제** — 좁히기](../12-narrowing/) — ★★★ **README 의 선행.** 좁히기 수단의 정본(1·2절)과 「`--strict false` 로 네 파일 중 셋이 갈린다」(5절). **여기는 그 스위치를 끈 쪽이 런타임에서 무엇이 되나부터.**
- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — ★★★ **README 의 선행.** `strictNullChecks` 가 하위 플래그의 **축**인 것(5절) · 묶음을 두고 이것만 끄는 법(2절).
- [**30번 주제** — 타입 단언과 non-null `!`](../30-type-assertions-and-non-null/) 2절 — `!` 가 방출에서 사라지고 **흘러간 곳**에서 터지는 것. 3절의 `[2]` 가 같은 칸이다.
- [**37번 주제** — 선언 파일 작성](../37-writing-declaration-files/) 2절 — 「컴파일 통과, node 에서 드러남」의 `.d.ts` 판.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) 1절 — `?` 가 `\| undefined` 를 만드는 것이 이 플래그에 달린 것.
- [**41번 주제** — 인덱스·선택 프로퍼티 엄격 플래그](../41-index-and-optional-property-strict-flags/) — 이 플래그가 **안 붙이는** `undefined` 를 붙이는 둘.
- 교차 갈래 — Kotlin [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/) · C# [`../../../csharp/syntax/06-nullable-reference-types/`](../../../csharp/syntax/06-nullable-reference-types/).

## 용어 풀이

> **`strictNullChecks`** — `null`·`undefined` 를 별도 타입으로 분리하는 플래그. `strict` 에 딸려 7.0.2 기본 켬.\
> 예: 2절 — 끄면 `number | null` 이 `number`.

> **흡수** — 끈 판에서 모든 타입이 이미 `null`·`undefined` 를 품어, 유니온에 적어도 **글자에서 사라지는** 것.\
> 예: 2절 `symbol` 탐침 6·7·8행.

> **`TS18048`** — 「'…' is possibly 'undefined'.」 — `T | undefined` 인 **이름**에 멤버 접근.\
> 예: 1절 `nn40b` 의 `hit`.

> **`TS18047`** — 「'…' is possibly 'null'.」\
> 예: 1절 `nn40d` 의 `el`.

> **`TS2532`** — 「Object is possibly 'undefined'.」 — 이름이 없는 **식**(호출 결과)에 멤버 접근.\
> 예: 1절 `nn40c` 의 `labels.get("en")`.

> **`symbol` 탐침** — `const p: symbol = 식;` 으로 진단 문구에서 **식의 타입**을 뽑는 한 줄. `null` 탐침이 끈 판에서 침묵해서 바꿨다.\
> 예: 2·3절.

> **대역(`shim40.cjs`)** — node 에 없는 `document` 를 `querySelector` 가 `null` 을 돌려주는 한 줄로 흉내 낸 파일. `node -r` 로 먼저 싣는다.\
> 예: 1절 `nn40d`.

## 더 들어가면

- **진짜 브라우저의 `querySelector`** — 이 문서는 대역으로 돌렸다. 헤드리스 브라우저로 **던지지 않았다.**
- **`strictNullChecks` 를 끈 채 쓴 `.d.ts` 를 켠 프로젝트가 읽으면** — `null` 을 적지 않은 선언이 켠 판에서 「비어 있을 수 없음」으로 읽힌다. 37편 2절의 거짓말과 같은 모양일 것으로 읽히지만 **던지지 않았다.**
- **`NonNullable<T>`·타입 술어로 좁히기** — [**13번 주제**](../13-type-guards-and-predicates/)(타입 가드)가 정본이다.
