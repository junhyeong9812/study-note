# ts/syntax/30 — 타입 단언과 non-null `!` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types (Type Assertions · Non-null Assertion Operator)](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html) ·
> [TypeScript 2.0 릴리스 노트 — Non-null assertion operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-0.html) ·
> [TypeScript 2.7 릴리스 노트 — Definite Assignment Assertions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-7.html) ·
> [TypeScript 3.7 릴리스 노트 — Assertion Functions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 이 판에서 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(방출된 `.js` + `node`)이다.**
> 아홉 가지 꼴을 **칸마다 파일 하나씩** 컴파일·방출·실행해, 「진단 / 방출된 줄 / `node` 결과」 세 칸을 스크립트가 찍고 **마지막 줄에서 센다**(1절).
> ★★★ **30 은 29 의 짝이다.** [**29번 주제**](../29-satisfies/)가 이미 잰 것 — **`as` 는 빠진 키·더한 키를 통과시키고 겹칠 수 없는 값만 `TS2352` 로 막는다** ·
> **`{} as User` 는 진단 0줄에 `exit=0`, 방출된 `.js` 에서 `as` 가 사라지고 `node` 에서 `TypeError`** — 는 **다시 재지 않고 인용한다.**
> 여기서 새로 재는 것은 **`as unknown as` · `!`(두 자리) · 단언 함수 · 타입 가드** 와 **「언제 써도 되나」** 다.
> ★ 단언 함수의 **몸통을 컴파일러가 검사하지 않는다**는 것은 [**14번 주제**](../14-assertion-signatures/)가, 타입 술어가 거짓말해도 믿는다는 것은 [**13번 주제**](../13-type-guards-and-predicates/)가 정본이다 — 인용한다.
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> **버전** — `!` 는 **2.0**(릴리스 노트가 「방출된 JavaScript 에서 그냥 지워진다」고 적는다), 확정 할당 단언은 **2.7**, 단언 함수는 **3.7**. ★ **7.0.2 에서 도는지는 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 1절 격자의 스물일곱 칸과 마지막 두 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 방출기의 고정 형식 · 예외는 **타입과 메시지만** 찍었다(경로가 박히는 스택은 안 찍었다) |
| **★ 부적용 — 5창(`.d.ts`)** | 이 주제는 **식에 붙는 연산자**라 `.d.ts` 로 물을 것이 **없다** | `.d.ts` 블록이 **하나도 없다** |
| **흔들린다** | 절대 경로 | 격자는 작업 디렉토리 아래 임시 폴더에서 돌리고 **경로를 출력에 안 찍었다** |
| **안 잰 것** | 검사 **시간** · 단언이 실행 속도에 주는 영향 | **재지 않았다** — 방출물에 **아무것도 안 남는다**는 것만 보였다 |

## 한눈에 — 쉽게 말하면

**`as`·`!` 는 「검문소 통과증」이다. 컴파일러라는 검문소에서만 쓰이고, 실행 세계로 넘어가는 순간 종이째 사라진다.**

| 비유 | 실체 |
|---|---|
| 검문소에 **「이건 사용자입니다」 통과증**을 내민다 — 검문은 **겉모양이 비슷한지**만 본다 | `x as User` — **겹칠 수 있으면** 통과(29편) |
| 통과증을 **두 장** 겹친다 — 첫 장은 「**정체불명**」이라 뭐든 된다 | `x as unknown as User` — 겹침 검사마저 넘는다 |
| **「비어 있지 않음」 도장**을 찍는다 | `x!` — `undefined`·`null` 을 타입에서 뺀다 |
| ★★★ 검문소를 지나면 **통과증·도장이 둘 다 없어진다** | 방출된 `.js` 에 `as`·`!` 가 **한 글자도 없다** |
| ★★ 대신 **실제 경비원**을 세운다 — 실행 세계에도 남는다 | 단언 함수 `assertUser(x)` · 가드 `isUser(x)` — **함수 호출**이라 남는다 |

- ★★★ 한 줄로 — 「**`as`·`!` 는 검사를 끄는 표시이고, 방출물에서 사라진다. 실행 세계에 검사를 남기려면 함수 호출(단언 함수·가드)이어야 한다.**」

```text
  컴파일 세계                         실행 세계(방출된 .js)

  (got as User).name     ──지운다──>  got.name
  got!.name              ──지운다──>  got.name
  assertUser(got);       ──남긴다──>  assertUser(got);      ← 이것만 실행 때 검사한다
  isUser(got) ? … : …    ──남긴다──>  isUser(got) ? … : …
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 검사를 우회하는 꼴들은 방출물에 무엇을 남기나** — 아홉 가지를 **한 격자**에 놓고 진단·방출·실행 세 칸을 센다(1절).
2. **`!` 는 어디서 터지나** — Kotlin `!!` 처럼 그 자리에서가 아니라 **값이 흘러간 곳**에서다(2절). 그리고 **선언 쪽 `!`** 은 다른 검사를 끈다(3절).
3. **그래서 언제 써도 되나** — 판단표를 **실패 사례로** 세운다(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 방출된 `.js` + `node`** | 우회 꼴이 **런타임에 남긴 것** | 실행 결과 | **본체**(1·2·3·4절) |
| ★★ **우회 격자** | 꼴 아홉 × (진단 · 방출 · 실행) | 칸마다 파일 하나 | 1절 — 3창을 **격자로 센 것** |
| ★ **진단이 0줄인 것** | 컴파일러가 **아무 말도 안 한 것** | 빈 블록 + `exit=0` | 2·4절 |
| ★ **설정 대조** | `--strict` 를 끄면 | 글자 단위 대조 | 5절 |
| ★ **부적용 — 5창(`.d.ts`)** | 식 쪽 연산자라 물을 것이 **없다** | — | — |
| ★ **제5의 상태 — 창을 바꿔 물었다** | Kotlin `!!` 의 런타임 검사 | 그쪽 갈래의 `javap` 실측 | 2절 — **이 머신에서 다시 돌리지 않고 인용** |

비용 — 격자 열여덟 번 컴파일(진단 9 · 방출 9) + `node` 9 번 + 파일 셋의 컴파일·방출·실행 + `--strict` 대조.

```text
  이 주제의 축 — 「무엇을 끄나」 × 「방출물에 남나」

                       끄는 검사                         방출물에
  x as T               겹칠 수 있는지만 보고 나머지       사라진다
  x as unknown as T    겹침 검사까지                       사라진다
  x!                   null·undefined 검사                 사라진다
  let x!: T            「대입 전 사용」 검사               사라진다(선언의 ! 만)
  asserts x is T       — (좁힐 뿐, 몸통은 안 본다: 14편)   ★ 남는다 — 함수 호출
  x is T (가드)        — (좁힐 뿐, 몸통은 안 본다: 13편)   ★ 남는다 — 함수 호출
```

### (1) ★★★ 우회 격자 — 같은 값을 아홉 가지로 쓴다

**언제 쓰나** — 「`as` 로 할까, `!` 로 할까, 가드를 짤까」를 고를 때. 이 주제의 결론이 전부 이 격자에 있다.

```bash
# ts30b-bypass.sh
#!/usr/bin/env bash
# 같은 값(undefined 가 올 수 있는 got)을 User 로 쓰는 일곱 가지 꼴 -- 칸마다 파일 하나씩
# 칸마다 세 가지를 묻는다: 컴파일 진단 · 방출된 줄이 소스 줄과 같나 · node 실행 결과
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
prelude='interface User {
    name: string;
}
function find(id: number): User | undefined {
    return id === 1 ? { name: "kim" } : undefined;
}
function isUser(v: unknown): v is User {
    return typeof v === "object" && v !== null && "name" in v && typeof v.name === "string";
}
function assertUser(v: unknown): asserts v is User {
    if (!isUser(v)) throw new Error("assertUser failed");
}
const got = find(2);
const num = 42;'
T=$'\t'   # 구분자는 탭 -- 행 안에 ; 가 나오므로 ; 는 못 쓴다(규칙 32)
rows=(
  "plain${T}"'const out = got.name.toUpperCase();'
  "as${T}"'const out = (got as User).name.toUpperCase();'
  "angle${T}"'const out = (<User>got).name.toUpperCase();'
  "bang${T}"'const out = got!.name.toUpperCase();'
  "unk${T}"'const out = (got as unknown as User).name.toUpperCase();'
  "asserts${T}"'assertUser(got); const out = got.name.toUpperCase();'
  "guard${T}"'const out = isUser(got) ? got.name.toUpperCase() : "(else branch)";'
  "num-as${T}"'const out = (num as User).name.toUpperCase();'
  "num-unk${T}"'const out = (num as unknown as User).name.toUpperCase();'
)
changed=0; total=0; threw=0
for row in "${rows[@]}"; do
  IFS="$T" read -r label use <<< "$row"
  n=$(awk -F'\t' '{print NF}' <<< "$row")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $row"; exit 3; fi
  { echo "$prelude"; echo "try {"; echo "    $use"; echo '    console.log("ok", out);'
    echo "} catch (e) {"; echo '    console.log((e as Error).constructor.name, (e as Error).message);'; echo "}"; } > "$D/c.ts"
  diag=$(tsc --pretty false --noEmit -t es2022 --strict "$D/c.ts" 2>&1 | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
  rm -rf "$D/o"; tsc --pretty false -t es2022 --strict --outDir "$D/o" "$D/c.ts" > /dev/null 2>&1
  emitted=$(sed -n '/^try {/,/console.log("ok"/p' "$D/o/c.js" | sed '1d;$d' | sed 's/^ *//' | tr '\n' ' ' | sed 's/ $//')
  if [ "$emitted" = "$use" ]; then same='같다'; else same='★ 바뀌었다'; changed=$((changed+1)); fi
  run=$(node "$D/o/c.js" 2>&1)
  case $run in ok\ *) ;; *) threw=$((threw+1)) ;; esac
  total=$((total+1))
  printf '[%s] %s\n' "$label" "$use"
  printf '    진단   %s\n' "${diag:-OK}"
  printf '    방출   %s   (%s)\n' "$emitted" "$same"
  printf '    node   %s\n' "$run"
done
echo
echo "방출된 줄이 소스 줄과 달라진 칸 $changed / $total"
echo "node 에서 예외로 끝난 칸 $threw / $total"
```

```text
===== bash ts30b-bypass.sh (sh exit=0) =====
[plain] const out = got.name.toUpperCase();
    진단   TS18048
    방출   const out = got.name.toUpperCase();   (같다)
    node   TypeError Cannot read properties of undefined (reading 'name')
[as] const out = (got as User).name.toUpperCase();
    진단   OK
    방출   const out = got.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'name')
[angle] const out = (<User>got).name.toUpperCase();
    진단   OK
    방출   const out = got.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'name')
[bang] const out = got!.name.toUpperCase();
    진단   OK
    방출   const out = got.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'name')
[unk] const out = (got as unknown as User).name.toUpperCase();
    진단   OK
    방출   const out = got.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'name')
[asserts] assertUser(got); const out = got.name.toUpperCase();
    진단   OK
    방출   assertUser(got); const out = got.name.toUpperCase();   (같다)
    node   Error assertUser failed
[guard] const out = isUser(got) ? got.name.toUpperCase() : "(else branch)";
    진단   OK
    방출   const out = isUser(got) ? got.name.toUpperCase() : "(else branch)";   (같다)
    node   ok (else branch)
[num-as] const out = (num as User).name.toUpperCase();
    진단   TS2352
    방출   const out = num.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'toUpperCase')
[num-unk] const out = (num as unknown as User).name.toUpperCase();
    진단   OK
    방출   const out = num.name.toUpperCase();   (★ 바뀌었다)
    node   TypeError Cannot read properties of undefined (reading 'toUpperCase')

방출된 줄이 소스 줄과 달라진 칸 6 / 9
node 에서 예외로 끝난 칸 8 / 9
```

그림 해설 — 한 단계에 한 문장.

- ★ `got` 은 `find(2)` 라서 **실제로 `undefined`** 다. 타입은 `User | undefined`.
- ★★ **`[plain]`** — 아무것도 안 붙이면 **`TS18048`**(「'got' is possibly 'undefined'」). 컴파일러가 막는 **원래 자리**다.
  ★ 진단이 있어도 **방출은 됐고**(`noEmitOnError` 기본값이 꺼져 있다), `node` 에서 **`TypeError`** 가 났다 — 경고를 무시하면 이렇게 된다.
- ★★★ **`[as]`·`[angle]`·`[bang]`·`[unk]`** — 넷 다 **진단 `OK`**, 방출 칸은 **`const out = got.name.toUpperCase();`** 로 **한 글자도 같다.**
  `(got as User)` · `(<User>got)` · `got!` · `(got as unknown as User)` 가 **괄호째 지워졌다.** 그리고 넷 다 **`plain` 행과 같은 `TypeError`** 로 끝난다.
  ★ **네 꼴은 방출물에서 구별이 안 된다** — 컴파일러의 입만 막았지 실행은 `[plain]` 과 똑같다.
- ★★★ **`[asserts]`** — 진단 `OK`, 방출 칸이 **소스와 같다**(`(같다)`). **`assertUser(got);` 가 그대로 남았다.**
  `node` 는 **`Error assertUser failed`** — **단언 함수 자신이 던진** 예외다. 터진 자리가 **쓰는 줄이 아니라 확인하는 줄**이다.
- ★★ **`[guard]`** — 역시 **같게 남았고**, `node` 는 **`ok (else branch)`** — 아홉 행 중 **유일하게 예외 없이** 끝났다. `undefined` 를 **다른 가지로 보냈다.**
- ★★★ **`[num-as]`** — `42 as User` 는 **`TS2352`**(겹칠 수 없다 — 29편과 같은 코드). **`[num-unk]`** 는 가운데 `unknown` 을 끼워 **`OK`**. 둘 다 방출물에서 `num.name…` 이 되어 같은 `TypeError`.
- ★★★ 마지막 두 줄 — **방출된 줄이 소스 줄과 달라진 칸 6 / 9** · **`node` 에서 예외로 끝난 칸 8 / 9**.
  달라진 여섯이 전부 **`as`·`<T>`·`!` 가 있던 행**이고, 같게 남은 셋이 **`[plain]`·`[asserts]`·`[guard]`** 다.

```text
  아홉 행을 두 축으로 — 방출물에 흔적이 남나 × 실행이 어떻게 끝나나

                      방출물              node
  [plain]             그대로              TypeError  (쓰는 줄)     ← 진단 TS18048 을 무시한 값
  [as] [angle]        ★ 지워짐            TypeError  (쓰는 줄)
  [bang] [unk]        ★ 지워짐            TypeError  (쓰는 줄)
  [num-as] [num-unk]  ★ 지워짐            TypeError  (쓰는 줄)     ← num-as 는 TS2352
  [asserts]           그대로              Error      ★ 확인하는 줄
  [guard]             그대로              ok         ★ 다른 가지로
```

- ★★ **`[asserts]` 의 이득은 「안 터진다」가 아니라 「제자리에서 터진다」다.** 메시지도 **내가 적은 것**이다(`assertUser failed`).
  `[bang]` 의 `Cannot read properties of undefined (reading 'name')` 는 **무엇이 `undefined` 였는지**를 말하지 않는다.

비용 — 가드·단언 함수는 **실행 비용이 있는 진짜 코드**다(함수 호출 한 번 · `typeof`·`in` 검사). `as`·`!` 는 비용이 없는 대신 **아무것도 안 한다.** ★ 그 비용은 **재지 않았다.**

### (2) ★★★ `!` 는 흘러간 곳에서 터진다 — Kotlin `!!` 와 반대

**언제 쓰나** — `map.get(k)!` · `find(…)!` 처럼 **「없을 리 없다」** 를 적는 자리.

```ts
// ex.30a.ts
// ! 를 붙인 값이 곧바로 쓰이지 않고 다른 곳으로 흘러가면
interface User {
    name: string;
}
const table = new Map<number, User>([[1, { name: "kim" }]]);

const u = table.get(2)!;
const list: User[] = [u];
console.log("[1] list.length", list.length);
console.log("[2] typeof list[0]", typeof list[0]);
const copy = { ...list[0] };
console.log("[3] copy", JSON.stringify(copy));
try {
    console.log("[4]", list[0].name.length);
} catch (e) {
    console.log("[4]", (e as Error).constructor.name, (e as Error).message);
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.30a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e30a ex.30a.ts (tsc exit=0) =====
===== 방출된 e30a/ex.30a.js =====
"use strict";
const table = new Map([[1, { name: "kim" }]]);
const u = table.get(2);
const list = [u];
console.log("[1] list.length", list.length);
console.log("[2] typeof list[0]", typeof list[0]);
const copy = { ...list[0] };
console.log("[3] copy", JSON.stringify(copy));
try {
    console.log("[4]", list[0].name.length);
}
catch (e) {
    console.log("[4]", e.constructor.name, e.message);
}
```

```text
===== node e30a/ex.30a.js (node exit=0) =====
[1] list.length 1
[2] typeof list[0] undefined
[3] copy {}
[4] TypeError Cannot read properties of undefined (reading 'name')
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단 **0줄**에 `exit=0` — `table.get(2)!` 에 아무 말이 없다.
- ★★★ 소스 7행이 방출물에서 **`const u = table.get(2);`** — `!` 가 **사라졌다.** 실행 세계에는 「없을 리 없다」는 주장 자체가 **없다.**
- ★★★ `[1] list.length 1` · `[2] typeof list[0] undefined` — **`undefined` 가 `User[]` 에 조용히 들어갔다.**
- ★★ `[3] copy {}` — 스프레드는 `undefined` 를 **빈 객체로** 넘긴다. 여기서도 **안 터진다.**
- ★★★ `[4]` 에서야 **`TypeError Cannot read properties of undefined (reading 'name')`**. 틀린 `!` 는 7행인데 **터진 것은 14행**이다.

```text
  같은 「없을 리 없다」, 두 언어

  Kotlin   val u = table[2]!!            ← 이 줄에서 NPE          (checkNotNull 호출이 심어진다)
  TS       const u = table.get(2)!;      ← 이 줄은 조용하다        (방출물에서 ! 가 사라진다)
           const list = [u];               조용
           { ...list[0] }                  조용
           list[0].name.length           ← ★ 여기서 TypeError      (값이 흘러간 곳)
```

- ★★★ **Kotlin 쪽은 이 머신에서 다시 돌리지 않았다 — 창을 바꿔 인용한다(제5의 상태).**
  Kotlin 갈래 [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/) 3절이 `javap -c` 로
  **`s!!` 가 `Intrinsics.checkNotNull` 호출로 컴파일되고**, 실행하면 **`!!` 가 적힌 줄에서 NPE** 가 난다는 것을 실측했다.
  ★ 그러니 두 기호는 모양만 닮았다 — **Kotlin `!!` 는 런타임 검사를 심고, TS `!` 는 검사를 지운다.**
- ★ 이 차이는 [**01번 주제**](../01-what-ts-adds-and-erases/)의 「타입은 방출물에 남지 않는다」의 한 사례다.

```text
  2절의 값이 걸어간 길 — 어느 줄도 멈추지 않는다

  7행   table.get(2)!         undefined   ← 틀린 주장(방출물에서 사라짐)
  8행   [u]                   [undefined]
  9행   list.length           1           ← 조용
  10행  typeof list[0]        "undefined" ← 조용
  11행  { ...list[0] }        {}          ← 조용
  14행  list[0].name.length   TypeError   ★ 여기서야
```

비용 — `!` 가 틀리면 **실패 지점이 원인에서 멀어진다.** 고칠 줄은 7행인데 터지는 줄은 14행이다.

### (3) ★★ 선언 쪽의 `!` — 확정 할당 단언

**언제 쓰나** — 초기화를 **다른 함수·프레임워크가 해 주는** 필드·변수에 「대입 전 사용」 에러가 날 때.

```ts
// ex.30b.ts
// 선언 쪽의 ! -- 확정 할당 단언
let plain: number;
let banged!: number;
console.log(plain + 1, banged + 1);

class NoInit {
    count: number;
}
class BangInit {
    count!: number;
}
console.log(new NoInit().count, new BangInit().count);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.30b.ts (tsc exit=1) =====
ex.30b.ts(4,13): error TS2454: Variable 'plain' is used before being assigned.
ex.30b.ts(7,5): error TS2564: Property 'count' has no initializer and is not definitely assigned in the constructor.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e30b ex.30b.ts (tsc exit=2) =====
ex.30b.ts(4,13): error TS2454: Variable 'plain' is used before being assigned.
ex.30b.ts(7,5): error TS2564: Property 'count' has no initializer and is not definitely assigned in the constructor.
===== 방출된 e30b/ex.30b.js =====
"use strict";
// 선언 쪽의 ! -- 확정 할당 단언
let plain;
let banged;
console.log(plain + 1, banged + 1);
class NoInit {
    count;
}
class BangInit {
    count;
}
console.log(new NoInit().count, new BangInit().count);
```

```text
===== node e30b/ex.30b.js (node exit=0) =====
NaN NaN
undefined undefined
```

그림 해설 — 한 단계에 한 문장.

- ★★ `!` 없는 두 선언만 진단이 났다 — 4행 **`TS2454`**(「Variable 'plain' is used before being assigned.」) · 7행 **`TS2564`**(「Property 'count' has no initializer …」).
- ★★★ `let banged!: number` 와 `count!: number` 는 **진단이 없다.** 선언에 붙은 `!` 는 **「이 이름은 확실히 대입된다」** 는 주장이다.
- ★ 진단이 있어도 방출은 됐다(`tsc exit=2`) — 방출물에서 `let banged;` · `count;` 로 **`!` 가 사라졌다.**
  ★ `count;` 는 필드 **선언**으로 남았다 — `-t es2022` 라 **네이티브 필드**로 방출된 것이다. 이것이 [**32번 주제**](../32-class-type-aspects/)의 `useDefineForClassFields` 와 이어진다.
- ★★★ `node` — **`NaN NaN`** 과 **`undefined undefined`**. 진단을 받은 쪽도, `!` 로 입을 막은 쪽도 **실행 결과는 같다.** `!` 는 값을 **만들어 주지 않는다.**

```text
  ! 의 두 자리 — 같은 글자, 다른 검사를 끈다

  식 뒤      got!             끄는 것: 「possibly 'undefined'」   TS18048 · TS2532 류
  선언 뒤    let banged!: T   끄는 것: 「대입 전 사용」            TS2454
             count!: T        끄는 것: 「초기화 안 된 필드」       TS2564
  공통       방출물에서 사라진다 · 값을 만들지 않는다
```

비용 — **`!` 로 끈 필드는 `undefined` 로 시작한다.** 초기화를 맡긴 쪽이 안 불리면 3절의 `undefined` 가 그대로 나간다.

### (4) ★★★ 언제 써도 되나 — 세 자리를 입력만 바꿔 던진다

**언제 쓰나** — 코드 리뷰에서 「이 `as` 괜찮나」를 판단할 때. **판단의 근거를 실패 사례로** 세운다.

```ts
// ex.30c.ts
// 단언을 쓴 세 자리 -- 같은 코드가 입력만 바뀌면
interface Config {
    host: string;
    port: number;
}
interface Repo {
    load(id: number): string;
    save(v: string): void;
}
function readConfig(text: string): Config {
    return JSON.parse(text) as Config;
}
function portOf(ports: Map<string, number>, key: string): number {
    return ports.get(key)!;
}
const fakeRepo = { load: (id: number) => "row" + id } as unknown as Repo;

const tries: [string, () => unknown][] = [
    ["readConfig full   ", () => readConfig('{"host":"a","port":1}').host.length],
    ["readConfig partial", () => readConfig('{"port":1}').host.length],
    ["portOf present    ", () => portOf(new Map([["web", 80]]), "web") + 1],
    ["portOf missing    ", () => portOf(new Map([["web", 80]]), "db") + 1],
    ["fakeRepo.load     ", () => fakeRepo.load(7)],
    ["fakeRepo.save     ", () => fakeRepo.save("x")],
];
for (const [label, f] of tries) {
    try {
        console.log(label, "->", f());
    } catch (e) {
        console.log(label, "->", (e as Error).constructor.name, (e as Error).message);
    }
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.30c.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e30c ex.30c.ts (tsc exit=0) =====
===== 방출된 e30c/ex.30c.js =====
"use strict";
function readConfig(text) {
    return JSON.parse(text);
}
function portOf(ports, key) {
    return ports.get(key);
}
const fakeRepo = { load: (id) => "row" + id };
const tries = [
    ["readConfig full   ", () => readConfig('{"host":"a","port":1}').host.length],
    ["readConfig partial", () => readConfig('{"port":1}').host.length],
    ["portOf present    ", () => portOf(new Map([["web", 80]]), "web") + 1],
    ["portOf missing    ", () => portOf(new Map([["web", 80]]), "db") + 1],
    ["fakeRepo.load     ", () => fakeRepo.load(7)],
    ["fakeRepo.save     ", () => fakeRepo.save("x")],
];
for (const [label, f] of tries) {
    try {
        console.log(label, "->", f());
    }
    catch (e) {
        console.log(label, "->", e.constructor.name, e.message);
    }
}
```

```text
===== node e30c/ex.30c.js (node exit=0) =====
readConfig full    -> 1
readConfig partial -> TypeError Cannot read properties of undefined (reading 'length')
portOf present     -> 81
portOf missing     -> NaN
fakeRepo.load      -> row7
fakeRepo.save      -> TypeError fakeRepo.save is not a function
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 컴파일러는 **진단 0줄**이다. 세 자리가 **입력이 맞을 때도, 틀릴 때도** 같은 소스다.
- ★★ **`readConfig`** — 방출물의 몸통이 **`return JSON.parse(text);`** 한 줄이다. `as Config` 가 사라졌으니 **검증이 0**이다.
  `full` 은 `1`, `partial` 은 **`TypeError … (reading 'length')`** — `host` 가 없는데 `Config` 라고 적었다.
- ★★★ **`portOf`** — `present` 는 `81`, **`missing` 은 `NaN`** 이다. **예외조차 안 났다.** `undefined + 1` 이 `NaN` 이 되어 **조용히 틀린 값**이 나갔다.
  여섯 줄 중 **가장 나쁜 줄**이다 — 1절의 `TypeError` 들은 적어도 멈췄다.
- ★★ **`fakeRepo`** — `as unknown as Repo` 로 **메서드 하나짜리 객체**를 `Repo` 라고 했다. `load` 는 `row7`, **`save` 는 `TypeError fakeRepo.save is not a function`**.

```text
  세 자리 — 무엇을 믿었나, 누가 그 믿음을 지키나

  JSON.parse(text) as Config        믿은 것: 바깥 데이터의 모양      지키는 이: 없다  → partial 에서 TypeError
  ports.get(key)!                   믿은 것: 키가 있다               지키는 이: 호출자 → missing 에서 NaN (조용)
  { load } as unknown as Repo       믿은 것: save 는 안 불린다        지키는 이: 테스트 범위 → save 에서 TypeError
```

**판단표 — 근거는 전부 이 문서의 실패 칸이다.**

| 자리 | 써도 되나 | 근거(실패 사례) | 대신 |
|---|---|---|---|
| 바깥 데이터(`JSON.parse`·`fetch`·`localStorage`) 에 `as T` | ★★★ **안 된다** | 4절 `readConfig partial` → `TypeError` | 가드·단언 함수로 **모양을 확인** — 1절 `[asserts]`·`[guard]` 가 방출물에 남았다 |
| `map.get(k)!` · `find(…)!` | ★★ **바로 앞에서 확인했을 때만** | 4절 `portOf missing` → **`NaN`** · 2절 → 14행에서 터짐 | `?? 기본값` 이나 `if (v === undefined) throw …` — 제자리에서 멈춘다 |
| 테스트 더블에 `as unknown as T` | ★ **테스트 안에서만** | 4절 `fakeRepo.save` → `TypeError` | 필요한 메서드만 가진 **좁은 인터페이스**를 받게 설계 |
| `42 as User` 처럼 겹칠 수 없는 값 | ★★★ **컴파일러가 이미 막았다** | 1절 `[num-as]` → `TS2352` | `as unknown as` 로 **넘기지 마라** — `[num-unk]` 가 같은 `TypeError` |
| 컴파일러가 **못 따라오는** 좁힘(15편의 콜백 뒤 등) | ★ **된다 — 그 자리에서 확인이 끝났다면** | — (이 자리는 실패 사례를 안 만들었다) | 지역 변수로 고정해 좁힘을 살리는 쪽이 먼저([**15번 주제**](../15-control-flow-analysis-limits/)) |
| 초기화를 프레임워크가 하는 필드에 `count!` | ★ **된다 — 초기화 경로가 확실할 때** | 3절 → `undefined` 로 시작 | 생성자에서 받는 쪽이 낫다 |

```text
  단언을 적기 전에 묻는 세 가지 — 4절의 실패 칸에서 거꾸로 세웠다

  ① 이 값은 바깥에서 왔나(JSON·네트워크·저장소)?
        예 ──> as·! 금지. 가드·단언 함수로 모양을 확인한다         (readConfig partial)
        아니오
  ② 「없을 리 없다」의 근거가 바로 앞 줄에 있나?
        아니오 ──> ?? 기본값 · throw 로 제자리에서 멈춘다            (portOf missing → NaN)
        예
  ③ 틀렸을 때 어디서 터지나 — 적은 줄인가, 먼 줄인가?
        먼 줄 ──> 단언 함수로 바꿔 제자리에서 멈추게 한다            (2절 7행 → 14행)
        적은 줄 ──> 써도 된다. 근거를 주석 한 줄로 남긴다
```

비용 — 판단표의 「된다」는 전부 **「내가 컴파일러보다 더 안다」** 의 다른 이름이다. 그 앎이 **코드에 안 남으면** 다음 사람이 모른다.

### (5) ★ 설정 대조

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.30a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.30b.ts    exit 1 = exit 0 · ★ 출력이 다르다
ex.30c.ts    exit 0 = exit 0 · 출력 한 글자도 같다
```

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.30b.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.30b.ts) (sh exit=1) =====
1,2d0
< ex.30b.ts(4,13): error TS2454: Variable 'plain' is used before being assigned.
< ex.30b.ts(7,5): error TS2564: Property 'count' has no initializer and is not definitely assigned in the constructor.
```

- ★★ `ex.30b.ts` 만 갈렸다 — `--strict false` 에서 **`TS2454`·`TS2564` 가 둘 다 사라져** `exit 0` 이 된다.
  `strictNullChecks`·`strictPropertyInitialization` 이 꺼지면 **선언 쪽 `!` 는 끌 검사가 없다.**
- ★ `ex.30a.ts`·`ex.30c.ts` 는 두 판 다 `exit 0` 이고 글자도 같다 — `!`·`as` 가 **이미 입을 막아서** 설정이 바꿀 것이 없다.
- ★ 1절 격자는 `--strict` 로만 돌렸다. **꺼진 쪽 격자는 안 돌렸다** — `[plain]` 행의 `TS18048` 이 사라질 것으로 **예상만** 한다.

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  x as T                  겹칠 수 있으면 통과 · 방출물에서 사라진다            (1절 · 29편)
  <T>x                    as 와 같다                                          (1절 [angle])
  x as unknown as T       겹침 검사까지 넘는다 · 사라진다                       (1절 [unk] [num-unk])
  x!                      null·undefined 를 타입에서 뺀다 · 사라진다  ★ 2.0   (1·2절)
  let x!: T / f!: T       대입 전 사용·초기화 검사를 끈다 · 사라진다  ★ 2.7   (3절)
  function f(v): asserts v is T   호출이 방출물에 남는다              ★ 3.7   (1절 [asserts] · 14편)
  function f(v): v is T           호출이 방출물에 남는다                      (1절 [guard] · 13편)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `User \| undefined` 를 그대로 씀 | `TS18048` | 1절 `[plain]` |
| `42 as User` — 겹칠 수 없다 | `TS2352` | 1절 `[num-as]` |
| `let plain: number;` 를 대입 전에 씀 | `TS2454` | 3절 4행 |
| 초기화 없는 필드 `count: number;` | `TS2564` | 3절 7행 |

**규칙 불릿**

- ★★★ **`as`·`<T>`·`!`·`as unknown as` 는 방출물에서 괄호째 사라진다** — 1절 방출 칸 **6 / 9**.
- ★★★ **단언 함수·가드는 함수 호출이라 방출물에 남는다** — 실행 때 검사가 되는 것은 이 둘뿐이다.
- ★★ **`as unknown as T` 는 겹침 검사(`TS2352`)마저 넘는다** — `unknown` 은 무엇과도 겹치기 때문이다(1절 `[num-unk]`).
- ★★ **`!` 는 두 자리에 붙는다** — 식 뒤(null 검사를 끈다)와 선언 뒤(대입 검사를 끈다). 둘 다 **값을 만들지 않는다**(3절).

## 어디서 틀리나

- ★★★ 「**`x!` 는 null 이면 던진다**」 — **안 던진다.** 방출물에서 사라진다(2절). **Kotlin `!!` 와 반대다.**
- ★★★ 「**`as` 는 타입을 변환한다**」 — **변환도 검사도 없다.** `(got as User)` 가 `got` 이 된다(1절).
- ★★★ 「**`as unknown as` 는 `as` 보다 조금 더 센 정도**」 — **겹침 검사 하나 남은 것까지 끈다.** `42 as unknown as User` 가 통과한다(1절).
- ★★ 「**`!` 가 틀리면 그 줄에서 에러가 난다**」 — **값이 흘러간 곳**에서 난다(2절 — 7행 대신 14행). 스프레드는 `{}` 로, 산술은 **`NaN`** 으로 **조용히 넘어간다**(2·4절).
- ★★ 「**`count!: number` 는 필드를 초기화해 준다**」 — **`undefined` 로 둔다**(3절).
- ★★ 「**단언 함수를 쓰면 안전하다**」 — **몸통이 맞을 때만.** 컴파일러는 몸통을 **안 본다**([**14번 주제**](../14-assertion-signatures/) 2절). 1절 `[asserts]` 가 제자리에서 멈춘 것은 **몸통을 제대로 짰기 때문**이다.
- ★ 「**`<User>got` 은 옛 문법이라 다르게 동작한다**」 — 방출·실행 칸이 **`[as]` 와 한 글자도 같다**(1절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(2.0 · 핸드북)** | `!` 와 `as`·`<T>` 는 **방출된 JavaScript 에서 지워진다** · 단언에는 **런타임 검사가 없다** | 2.0 릴리스 노트 · 핸드북 문장 · 1절 방출 칸 |
| **언어 보장(핸드북)** | `as` 는 「더 구체적이거나 덜 구체적인」 쪽으로만 · 막히면 `any`/`unknown` 을 거쳐 두 번 | 핸드북 · 1절 `[num-as]`/`[num-unk]` |
| **언어 보장(2.7)** | 선언 뒤 `!` 는 확정 할당 단언 | 2.7 릴리스 노트 · 3절 |
| **언어 보장(3.7)** | 단언 함수는 **반환하면 좁힌다** — 몸통은 사용자 책임 | 3.7 릴리스 노트 · 14편 |
| **★ 이 판(7.0.2)의 관찰** | 진단 코드(`TS18048`·`TS2352`·`TS2454`·`TS2564`)와 문구 | 1·3절 |
| **★ 이 판의 관찰** | 방출기가 `(got as User)` 의 **괄호까지** 지운다 | 1절 — 괄호를 남길지는 방출기 몫이다 |
| **★ 엔진(node v18)의 관찰** | `TypeError` 메시지 문구 | 1·2·4절 |
| **★ 부적용 — 5창(`.d.ts`)** | 식 쪽 연산자라 물을 것이 없다 | — |
| **안 잰 것** | 검사 **시간** · 가드의 실행 비용 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **가드·단언 함수** — 바깥에서 들어온 값(JSON·네트워크·저장소) | 값이 이미 좁혀진 자리에서 **또** — 이중 비용 |
| **`x!`** — **바로 앞 줄에서** 확인이 끝났는데 컴파일러가 못 따라올 때 | ★★★ 「**아마** 있을 것이다」일 때 — 4절 `NaN` |
| **`as T`** — 컴파일러보다 **내가 더 아는 것이 확실하고**, 그 근거가 **코드 가까이** 있을 때 | ★★★ 바깥 데이터 — 4절 `partial` |
| **`as unknown as T`** — 테스트 더블 등 **범위가 닫힌** 자리 | ★★★ 제품 코드에서 `TS2352` 를 **끄려고** — 1절 `[num-unk]` |
| **`count!: T`** — 초기화 경로가 **확실한** 필드 | 초기화를 **잊을 수 있는** 필드 — 3절 `undefined` |

## 핵심 문장

1. **`as`·`<T>`·`!`·`as unknown as` 는 방출물에서 사라진다** — 검사를 끌 뿐 아무것도 하지 않는다(1절 **6 / 9**).
2. **실행 때 검사가 남는 것은 함수 호출뿐이다** — 단언 함수는 **제자리에서** 멈추고, 가드는 **다른 가지로** 보낸다.
3. **TS `!` 는 Kotlin `!!` 와 반대다** — 런타임 검사를 심지 않으므로 **값이 흘러간 곳**에서 터지거나 **`NaN` 으로 조용히** 틀린다.
4. **단언은 「내가 더 안다」는 주장이다** — 그 근거가 코드에 없으면 바깥 데이터 앞에서 무너진다.

## 관련 자료

- [**29번 주제** — `satisfies`](../29-satisfies/) — ★★★ **README 의 선행.** `as` 가 빠진 키·더한 키를 통과시키고 `TS2352` 만 막는다는 것, `{} as User` 의 한살이(진단 0줄 → 방출에서 사라짐 → `TypeError`)는 그쪽이 정본이다. **여기는 `as unknown as`·`!`·단언 함수와 나란히 놓았을 때부터.**
- [**14번 주제** — 단언 시그니처](../14-assertion-signatures/) — `asserts x is T` 의 **몸통을 컴파일러가 안 본다**는 실측은 그쪽. 1절 `[asserts]` 행은 몸통이 **맞게** 짜인 경우다.
- [**13번 주제** — 타입 가드와 술어](../13-type-guards-and-predicates/) — `x is T` 가 거짓말해도 믿는다는 것은 그쪽.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `as unknown as` 가 통하는 이유(`unknown` 은 무엇과도 겹친다)의 바탕.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「방출물에서 사라진다」의 일반론.
- [**15번 주제** — 제어 흐름 분석의 한계](../15-control-flow-analysis-limits/) — `!` 를 쓰고 싶어지는 자리(좁힘이 풀리는 곳)의 정본.
- [**32번 주제** — 클래스의 타입 측면](../32-class-type-aspects/) — 3절 `count!` 가 방출물에서 필드 선언으로 남는 것과 이어진다.
- Kotlin 갈래 [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/) — `!!` 가 `Intrinsics.checkNotNull` 로 컴파일되는 `javap` 실측. **2절의 대비는 그쪽 출력을 인용한 것**이다.
- 목록의 **40번 주제**(`strictNullChecks` 의 파급) — `!` 가 할 일이 생기는 **이유** 자체는 그쪽.

## 용어 풀이

> **타입 단언(type assertion)** — `x as T`·`<T>x`. 컴파일러에게 「이건 `T` 다」라고 **알려 주는** 것. 검사는 **겹침**뿐이고 방출물에서 사라진다.\
> 예: 1절 `[as]` — `(got as User).name` 이 방출물에서 `got.name`.

> **이중 단언** — `x as unknown as T`. 가운데 `unknown` 을 거쳐 **겹침 검사까지** 넘는다.\
> 예: 1절 `[num-unk]` — `42 as unknown as User` 가 진단 없이 통과.

> **non-null 단언(`!`)** — 식 뒤에 붙여 그 식의 타입에서 `null`·`undefined` 를 뺀다. **런타임 검사가 없다**(TS 2.0).\
> 예: 2절 `table.get(2)!` — 방출물에서 `table.get(2)`.

> **확정 할당 단언** — 선언 뒤의 `!`(`let x!: T` · 필드 `f!: T`). 「대입 전 사용」·「초기화 안 됨」 검사를 끈다(TS 2.7).\
> 예: 3절 `banged!` — `TS2454` 가 안 난다. 값은 `undefined`.

> **단언 함수(assertion function)** — 반환 타입이 `asserts v is T` 인 함수. **돌아오면** 인자가 `T` 로 좁혀진다(TS 3.7).\
> 예: 1절 `assertUser(got)` — 방출물에 **호출이 남는다.**

> **타입 가드(사용자 정의)** — 반환 타입이 `v is T` 인 함수. `if` 로 부르면 가지마다 좁혀진다.\
> 예: 1절 `isUser(got) ? … : …` — `undefined` 가 `else` 로 갔다.

> **`TS18048`** — 「'x' is possibly 'undefined'.」 `strictNullChecks` 아래에서 `undefined` 가 섞인 값을 바로 쓸 때.\
> 예: 1절 `[plain]`.

> **`TS2352`** — 「Conversion of type … may be a mistake because neither type sufficiently overlaps with the other.」 `as` 가 막는 유일한 자리.\
> 예: 1절 `[num-as]`.

## 더 들어가면

```text
  as unknown as 의 두 단계 — 각 단계는 규칙을 지킨다

  42 ──as unknown──> unknown ──as User──> User
       (무엇이든 unknown 으로)   (unknown 은 무엇으로든)
  42 ──────────as User──────────> ✗ TS2352   (number 와 User 는 겹칠 수 없다)
```

- **왜 `unknown` 을 끼우면 통하나** — `as` 는 **한쪽이 다른 쪽으로 좁혀질 여지**가 있으면 통과시킨다(핸드북의 「더 구체적이거나 덜 구체적인」 · 29편의 「겹침」). `unknown` 에는 무엇이든 할당되고, `unknown` 은 무엇으로든 단언된다 — **두 단계가 각각 규칙을 지킨다.** 결과만 규칙 밖이다.
- **`[plain]` 행이 실행까지 된 이유** — `tsc` 는 진단이 있어도 방출한다(`noEmitOnError` 기본값 `false`). 격자는 그 성질을 이용해 **진단이 난 칸도 실행 칸을 채웠다.** CI 에서 `--noEmitOnError` 를 켜는 이유가 이것이다 — **이 플래그 자체는 던지지 않았다.**
- **`!` 대신 무엇을** — `??`(기본값) · `?.`(없으면 `undefined` 로 계속) · `if (v === undefined) throw new Error("…")`(제자리에서 멈춤). JS 쪽 연산자는 JS 갈래 [`../../../js/syntax/12-optional-chaining-nullish-and-logical-assignment/`](../../../js/syntax/12-optional-chaining-nullish-and-logical-assignment/) 가 정본이다.
- **격자를 `--strict false` 로 돌리면** — 안 돌렸다(5절). `[plain]` 과 `[bang]` 의 진단 칸이 같아질 것이라는 **예상**만 있다.
