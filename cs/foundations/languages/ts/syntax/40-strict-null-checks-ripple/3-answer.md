# ts/syntax/40 — `strictNullChecks` 의 파급 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(끈 채 방출한 `.js` + `node`)이다.** 타입 탐침은 `null` 대신 **`symbol`** 로 바꿨고(3·7번), DOM 탐침은 **대역**으로 돌렸다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 여섯 다 막힌다 — 이름은 **`TS18048`**(`a`·`b`·`f`) · `null` 쪽 이름은 **`TS18047`**(`d`) · 이름 없는 식은 **`TS2532`**(`c`·`e`)

**출력**

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

**왜 그런가**

- ★★ 여섯 다 **`T | undefined`**(`d` 는 `T | null`)인 값의 멤버에 곧장 닿았다. 7.0.2 는 기본으로 `strictNullChecks` 가 켜져 있다(39편 3절).
- ★ 코드를 가르는 것은 **값에 이름이 있느냐**(`'hit' is possibly 'undefined'.`)와 **어느 쪽이 비었느냐**(`'null'`)다 — 호출 결과 같은 식은 「Object is possibly 'undefined'.」.

### 2. ★★★ 진단 **여섯 다 사라진다** · node — 여섯 다 **`TypeError`**(`d` 만 「of null」) · 방출물은 켬과 끔이 **여섯 다 한 글자도 같다**

**출력**

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

**왜 그런가**

- ★★★ 끄면 `undefined`·`null` 이 `number`·`string`·`Element` 에 **흡수**되어(3번) 멤버 접근을 막을 근거가 없다. 그런데 **실행의 값은 그대로** `undefined`·`null` 이다.
- ★★★ 스위치는 **검사만** 바꾼다 — `cmp` 가 6 / 6 같다고 했다. 켰을 때의 진단은 **이 `TypeError` 의 자리**를 미리 가리킨 것이었다.
- ★ 스크립트는 켬과 끔이 전부 같으면 멈추게 되어 있다 — 여기서는 「코드 여럿 / OK」로 갈렸다.

### 3. ★★★ 켬 — 1·2·3행 **`TS2322` 넷** / 끔 — **통과** · 6·7·8행 켬 **`number | null`·`string | undefined`·`number | undefined`** → 끔 **`number`·`string`·`number`** · 10행 켬 `TS2322` / 끔 **진단 없음**

**출력**

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

**왜 그런가**

- ★★★ 끄면 `null`·`undefined` 는 **모든 타입의 원소**다 — 대입이 통과하고, 유니온에 적은 `| null` 이 **흡수되어** 글자에서 사라진다.
- ★★ 10행 — 끈 판에서 `null` 타입이 `undefined` 를 **받는다.** `null` 탐침이 침묵하는 칸이다(7번).

### 4. ★★ 2행 **`number | undefined`** · 4·7·9·11행 **`number`** · 10행 **`string | undefined`**

**출력**

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

**왜 그런가**

- ★★ `!== undefined`·진릿값·`??`·`!` 넷은 **`number`** 로 만든다. 수단의 정본은 12편 1·2절이다.
- ★★★ `?.` 는 좁히지 않는다 — **`undefined` 를 결과로 흘려보내** `string | undefined` 가 된다(6번).

### 5. ★★★ 검사 **0줄** · 방출물 — **`const c = hit;`** · **`hit.toFixed(1)`**(`!` 가 지워짐) · node — **`[1] none none undefined`** · **`[2] TypeError Cannot read properties of undefined (reading 'toFixed')`**

**출력**

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

**왜 그런가**

- ★★ `!==`·`?.`·`??` 는 **JS 연산자**라 방출에 **남아** 실행에서도 지킨다 — `none`·`none`.
- ★★★ `!` 는 **타입 층의 주장**이라 방출에서 **지워진다.** `c` 는 `undefined` 그대로 찍혔고, `[2]` 는 2번의 끈 판과 **같은 `TypeError`** 다.

### 6. ★★ `?.` 는 **`nick` 이 없을 때 그 자리에서 멈추고 `undefined` 를 돌려준다** — 결과 `len` 은 **`number | undefined`** · 켠 판은 7행 `len.toFixed` 를 붙잡고, 끈 판은 **바로 그 7행**에서 `TypeError`

- ★★ `profile.nick?.text.length` 는 `nick` 이 없어서 **식 전체가 `undefined`** 가 됐다. `?.` 가 지킨 것은 `.text` 접근까지다.
- ★★★ 1번 `nn40a(7,24) TS18048` 이 `len` 을 가리킨다 — `?.` 가 **없애 준 것이 아니라 옮겨 놓은** `undefined` 다. 2번 끈 판의 `(reading 'toFixed')` 가 그 자리다(4번 10행과 같은 칸).

### 7. ★★ 끈 판에서 **`null` 타입이 `undefined` 를 받아** `null` 탐침이 **침묵**하기 때문 — `symbol` 은 켬·끔 모두 `null`·`undefined` 를 **안 받는다**

- ★★ 3번 10행 `const p4: null = u`(`u: undefined`) — 켬 `TS2322`, 끔 **진단 없음**. 끈 판의 `null` 탐침은 「타입이 무엇인가」를 말하지 못한다.
- ★ 같은 질문을 **과녁만 바꿔** 물었다(제5의 상태) — 6·7·8행은 두 판 모두 문구가 나와 타입을 읽을 수 있었다.

### 8. ★★★ **틀리다** — 방출물은 켬·끔 **6 / 6 한 글자도 같다** · 켬이 바꾸는 것은 **검사**뿐이고, 검사를 `!` 로 넘기면 런타임은 끈 판과 같다

- ★★★ 2번 마지막 줄 — 「켜고 방출한 `.js` 와 끄고 방출한 `.js` 가 한 글자도 같은 탐침 6 / 6」.
- ★★ 5번 — `!` 가 방출에서 지워졌다. 런타임에 남는 것은 **사람이 쓴 `!==`·`?.`·`??`** 뿐이다.
- ★ Kotlin 의 `!!` 는 반대로 **검사를 심는다** — 10번.

### 9. ★★ **`null`** — `nn40d`(`querySelector` 대역) · **`undefined`** — 나머지 다섯(`?.`·`find`·`Map.get`·`T | undefined` 반환·선택 매개변수) · 「`find` 는 `null`」은 **틀리다**

- ★★ 2번의 `nn40b` — 「Cannot read properties of **undefined** (reading 'toFixed')」. 1번의 켠 판도 `'hit' is possibly **'undefined'**` 라고 적었다.
- ★ `nn40d` 의 `null` 은 **대역**이 돌려준 값이다 — 진짜 브라우저의 반환은 이 문서가 확인하지 않았다. 타입 쪽(`TS18047` — 'null')은 `lib.dom` 의 선언이 말한 것이다.

### 10. ★★ 12편 5절 **「`object | null` 이 그냥 `object`」** · 30편 2절 **`[4] TypeError … (reading 'name')`**(`!` 가 사라지고 흘러간 곳에서 터짐) · 37편 2절 **「컴파일은 통과하고 node 에서 드러난다」** · **C# 쪽** — 둘 다 런타임에 아무것도 안 남긴다

- ★★ [**12번 주제**](../12-narrowing/) 5절 — 끈 판에서 유니온의 `null` 이 흡수됐다. 3번 6행의 `number | null` → `number` 가 같은 칸이다.
- ★★ [**30번 주제**](../30-type-assertions-and-non-null/) 2절 — `table.get(2)!` 가 방출에서 사라지고 **흘러간 줄**에서 `TypeError`. 5번의 `hit!` 과 같다.
- ★★ [**37번 주제**](../37-writing-declaration-files/) 2절 — `.d.ts` 의 거짓말이 `exit 0` 으로 통과하고 node 에서 드러났다. 2번은 **스위치가 거짓말을 한 판**이다.
- ★★★ Kotlin(03편)은 `String`·`String?` 가 **처음부터 다른 타입**이고 `!!` 가 **`Intrinsics.checkNotNull` 을 심는다.** C#(06편)은 널 허용 주석이 **경고**이고 **IL 이 같다.** TS 는 방출물이 같다(2번) — **C# 쪽**이다. 다른 것은 켠 판의 진단이 **에러**라는 점이다. 두 갈래 모두 **인용**이다 — 이 머신에서 다시 돌리지 않았다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `"$NODE20" --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `v20.19.6` · `Python 3.12.3` |
| ★★ 켠 판 | `--noEmit` × 탐침 여섯 | `TS18048` 셋 · `TS2532` 둘 · `TS18047` 하나 |
| ★★★ 끈 판 격자 | `bash ts38b-off40.sh` — 검사 둘 · 방출 둘 · `node` 하나씩 | 사라짐 **6 / 6** · `TypeError` **6 / 6** · 방출물 같음 **6 / 6** |
| ★★ 흡수 | `absorb40.ts` 켬/끔 | 대입 넷 통과 · 유니온 흡수 · `null` 탐침 침묵 |
| ★★ 좁히기 | `flow40.ts` · `bang40.ts` 검사 · 방출 · `node` | `number` 넷 · `?.` 는 `\| undefined` · `!` 만 지워짐 · `[2] TypeError` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **진단 코드의 갈림**(`TS18048`·`TS2532`) — 7.0.2 의 것이다.
- ★ **`TypeError` 문구** — node v18 의 V8 문구다. 근거는 **`TypeError` 라는 타입**이다.

**안 돌려 본 것**

- ★★ **진짜 브라우저의 `querySelector`** — 대역으로 돌렸다.
- ★ **Kotlin·C# 대비** — 형제 갈래의 실측을 인용했다. **검사 시간**은 재지 않았다.
