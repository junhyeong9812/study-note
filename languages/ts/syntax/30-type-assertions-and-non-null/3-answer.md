# ts/syntax/30 — 타입 단언과 non-null `!` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 격자가 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단은 `[plain]`·`[num-as]` 만 · 방출물에 **그대로 남는 것은 `[plain]`·`[asserts]`·`[guard]`** · **6 / 9** 와 **8 / 9**

**출력**

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

**왜 그런가**

| 행 | 진단 | 방출 | node |
|---|---|---|---|
| `[plain]` | `TS18048` | 같다 | `TypeError` — 쓰는 줄 |
| `[as]` `[angle]` `[bang]` `[unk]` | `OK` | ★★★ **바뀌었다** — `got.name…` | `TypeError` — 쓰는 줄 |
| `[asserts]` | `OK` | ★★ **같다** — `assertUser(got);` 가 남는다 | ★★ **`Error assertUser failed`** — 확인하는 줄 |
| `[guard]` | `OK` | ★★ **같다** | ★★★ **`ok (else branch)`** — 유일하게 예외 없음 |
| `[num-as]` | ★ **`TS2352`** | 바뀌었다 | `TypeError` |
| `[num-unk]` | ★★ **`OK`** | 바뀌었다 | `TypeError` |

- ★★★ **`[asserts]` 와 `[bang]` 의 예외는 종류가 다르다** — `Error`(단언 함수가 **스스로 던진 것**, 메시지도 내가 적은 것) 대 `TypeError`(엔진이 `undefined.name` 에서 던진 것).
- ★★ `as`·`<T>`·`!`·`as unknown as` 넷은 방출물·실행이 **`[plain]` 과 구별되지 않는다.**

### 2. ★★★ 진단 **0줄** · 소스 7행이 방출물에서 **`const u = table.get(2);`** · 처음 터지는 줄은 **`[4]`(14행)**

**출력**

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

**왜 그런가**

- ★★★ `!` 는 방출물에서 **사라졌다** — 실행 세계에는 「없을 리 없다」는 주장이 없다.
- ★★ `[1] 1` · `[2] undefined` · `[3] {}` — **세 줄 동안 조용히** 흘러갔다. `[4]` 에서야 `TypeError`.
- ★★ **Kotlin `!!` 라면 7행에서** 멈췄다 — 6번.

### 3. ★★ `TS2454`(4행) · `TS2564`(7행) — `!` 붙인 둘은 **진단 없음** · 방출은 됐고 `!` 가 **사라졌다** · `NaN NaN` / `undefined undefined`

**출력**

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

**왜 그런가**

- ★★ 진단이 있어도 `tsc` 는 방출한다(`exit=2`). 방출물은 `let banged;` · `count;` — **선언만 남고 `!` 는 없다.**
- ★★★ 진단을 받은 쪽과 `!` 로 막은 쪽의 **실행 결과가 같다** — `!` 는 값을 만들지 않는다.

### 4. ★★ 진단 **0줄** · 예외 없이 틀린 값은 **`portOf missing -> NaN`**

**출력**

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.30c.ts (tsc exit=0) =====
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

**왜 그런가**

- ★★★ `portOf` 의 `!` 가 사라져 **`undefined + 1`** 이 되었고, 그 값은 **`NaN`** — **예외가 없어 멈추지도 않는다.**
- ★★ `readConfig partial` 과 `fakeRepo.save` 는 `TypeError` 로 **적어도 멈췄다.** 방출물의 `readConfig` 몸통은 `return JSON.parse(text);` 한 줄이다(요약 4절).

### 5. ★★ **겹칠 수 없는 값의 단언**(`TS2352`)이 통과된다 — `unknown` 은 무엇과도 겹치기 때문

- ★★ `42 as User` 는 `number` 와 `User` 가 겹칠 수 없어 `TS2352`. `42 as unknown` 은 **무엇이든 `unknown` 으로** 갈 수 있어 통과, `unknown as User` 는 **`unknown` 에서 무엇으로든** 갈 수 있어 통과.
- ★ **두 단계가 각각 규칙을 지킨다** — 결과만 규칙 밖이다. 핸드북도 「먼저 `any`(또는 `unknown`)로, 그다음 원하는 타입으로」라고 적는다.
- ★★★ 방출물에서는 둘 다 `num.name…` — **`[num-as]` 의 진단을 끈 것 말고는 달라진 것이 없다.**

### 6. ★★★ TS `!` 는 **값이 흘러간 곳(14행)** 에서 터졌다 — 방출물에서 **사라지기** 때문이다

- ★★★ TS 2.0 릴리스 노트 — `!` 는 「방출된 JavaScript 에서 그냥 지워진다」. 2번 방출물의 `const u = table.get(2);`(소스 7행)가 그 증거다.
- ★★ Kotlin 갈래 [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/) 3절 — `s!!` 가 **`Intrinsics.checkNotNull` 호출**로 컴파일되어 **그 줄에서** NPE. **이 머신에서 다시 돌리지 않았다 — 인용이다.**
- ★ 한 줄로 — **Kotlin `!!` 는 검사를 심고, TS `!` 는 검사를 지운다.**

### 7. ★★ 단언 함수는 **함수 호출**이라 방출물에 남는다 — 몸통이 틀렸다면 격자는 **아무것도 보장하지 않는다**

- ★★ `as`·`!` 는 **식에 붙은 표시**라 지울 수 있지만, `assertUser(got)` 는 **호출문**이라 지우면 프로그램이 바뀐다. 지워지는 것은 **시그니처의 `asserts v is User`** 뿐이다.
- ★★★ 컴파일러는 단언 함수의 **몸통을 검사하지 않는다** — [**14번 주제**](../14-assertion-signatures/) 2절이 빈 몸통·거꾸로 된 몸통으로 깨뜨렸다.
  1번 `[asserts]` 가 제자리에서 멈춘 것은 **`isUser` 를 제대로 짰기 때문**이지 `asserts` 덕이 아니다.

### 8. ★★ **다른 연산자다** — 식 뒤 `!` 는 null 검사를, 선언 뒤 `!` 는 대입 검사를 끈다

- ★ `got!` — `User | undefined` 에서 `undefined` 를 뺀다. 끄는 것은 `TS18048` 류.
- ★ `let banged!: number` — **확정 할당 단언**(2.7). 끄는 것은 `TS2454`, 필드면 `TS2564`.
- ★★ 공통점 — **둘 다 방출물에서 사라지고 값을 만들지 않는다**(1번 · 3번).

### 9. ★★★ 확인이 **코드에 있는** 자리에서만 — 바깥 데이터에는 안 된다

| 자리 | 판단 | 4번의 근거 |
|---|---|---|
| `JSON.parse(…) as Config` | ★★★ 안 된다 — 가드·단언 함수 | `readConfig partial` → `TypeError` |
| `ports.get(key)!` | ★★ 바로 앞에서 확인했을 때만 — 아니면 `??`·`throw` | `portOf missing` → **`NaN`**(조용) |
| `{…} as unknown as Repo` | ★ 테스트 안에서만 | `fakeRepo.save` → `TypeError` |

### 10. ★★ 29편과 **같은 모양의 실패**다 · 몸통은 **검사하지 않는다** — 14편·13편

- ★★ 29편 2절 — `{} as User` → 진단 0줄 → 방출물에서 `as` 가 사라짐 → `node` 에서 `TypeError`. 1번 `[as]` 는 `undefined` 에 대해 **같은 한살이**를 밟았다.
- ★★ 단언 함수의 몸통 — [**14번 주제**](../14-assertion-signatures/) · 타입 술어의 몸통 — [**13번 주제**](../13-type-guards-and-predicates/) 2절. **둘 다 컴파일러는 믿기만 한다.**

### 11. ★ 「사라진다」는 **언어 보장**이다 · 6 / 9 는 **이 아홉 행의 수**다 · `--strict false` 면 3번의 진단이 **사라진다**

| 층 | 이 주제의 예 |
|---|---|
| **언어 보장** | `!`·`as` 는 방출된 JS 에서 지워진다(2.0 릴리스 노트 · 핸드북) · 단언에는 런타임 검사가 없다 |
| **이 판의 관찰** | 진단 코드와 문구 · 방출기가 괄호까지 지움 · `node` 의 `TypeError` 문구 |
| **★ 설정** | `--strict false` 에서 `ex.30b.ts` 의 `TS2454`·`TS2564` 가 사라진다 |

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

- ★★ **6 / 9 는 행을 어떻게 고르느냐의 수**다 — `as` 꼴을 더 넣으면 늘어난다. 성질은 「**`as`·`!` 가 있는 행은 전부 바뀌고, 함수 호출 행은 전부 남는다**」 쪽이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 우회 격자 | `bash ts30b-bypass.sh` (9 × 진단·방출·실행 = **27회**) | exit 0 · **6 / 9** · **8 / 9** |
| `!` 가 흘러감 | `--noEmit`·`--outDir e30a`·`node` | ★ 진단 0줄 · 7행에서 `!` 사라짐 · `[4]` 에서 `TypeError` |
| 선언 쪽 `!` | `--noEmit`·`--outDir e30b`·`node` | exit 1 · **2건**(`TS2454`·`TS2564`) · `NaN NaN` / `undefined undefined` |
| 판단표의 근거 | `--noEmit`·`--outDir e30c`·`node` | 진단 0줄 · **`NaN`** 한 줄 · `TypeError` 두 줄 |
| `strict` 대조 | 세 파일을 `--strict false` 로 재실행 | **`ex.30b.ts` 만 갈림** — 두 진단이 사라짐 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ 방출기가 **괄호까지** 지우는 것(1절 방출 칸) — 같게 남으면 「바뀌었다」 칸 수가 달라진다.
- ★ 진단 **문구** — 코드가 더 오래 간다.
- ★ `node` 의 `TypeError` **메시지 문구** — 엔진 판에 매인다.

**안 돌려 본 것**

- ★★ **격자를 `--strict false` 로** — 파일 셋만 대조했다.
- ★★ **Kotlin `!!`** — 이 머신에서 다시 돌리지 않고 Kotlin 03편의 `javap` 실측을 인용했다.
- ★ **`--noEmitOnError`** — 진단이 난 칸의 방출을 막는 플래그. 던지지 않았다.
