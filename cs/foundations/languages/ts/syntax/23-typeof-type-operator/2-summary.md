# ts/syntax/23 — `typeof` 타입 연산자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Typeof Type Operator](https://www.typescriptlang.org/docs/handbook/2/typeof-types.html) ·
> [Handbook — Keyof Type Operator](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html) ·
> [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 핸드북은 **규칙 확인용 링크**이고, 본문의 진단·방출 전문·실행 출력은 **전부 이 판에서 직접 던져서 받은 것**이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · javac -version · rustc --version (sh exit=0) =====
Version 7.0.2
v18.19.1
javac 21.0.5
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(방출된 `.js` + `node` 실행)이다.**
> 이 배치의 네 주제 가운데 **`.js` 창이 본체인 것은 23 하나뿐**이다.
> [**22번 주제**](../22-keyof-and-indexed-access-types/)·[**24번 주제**](../24-conditional-types-and-distribution/)·[**25번 주제**](../25-infer-and-recursive-conditional-types/)에서는
> `.js` 창이 **부적용**이다 — 순수 타입 층이라 **잴 것이 없다**. 여기서만 **잴 것이 있다.**
> **23 은 「컴파일 타임에만 있는 것」의 정본**이고, 그것을 `.js` 로 증명하기에 딱 맞는 주제이기 때문이다.
>
> ★★★ **축이 다르다** — 22 → 24 → 25 는 「타입을 계산하는 사슬」이지만 23 은 그 사슬이 아니다.
> 23 의 축은 「**값 공간 / 타입 공간**」이다. 같은 이름이 두 공간에 **따로** 살고, `typeof` 는 **값 칸에서 타입 칸으로 건너오는 다리**다.
>
> ★★ **이 배치가 쓰는 탐침(2창)** — 추론된 타입은 눈에 안 보인다.
> 그래서 **일부러 틀린 주석**(`const probe: null = …`)을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 한다.
> 이 문서의 그 꼴은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 **대조용 배너**다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — 값에 `typeof` 를 쓰는 타입 질의는 **TS 1.0** 부터다. `typeof import(…)` 는 **TS 2.9**,
> `InstanceType<T>` 는 **TS 2.8** 이다. **7.0 에서 도는지는 외우지 않고 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★★ 방출된 `.js` 전문과 `node` 출력 | 방출기의 고정 형식 + 결정적 프로그램이다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서**(`"Blue" \| "Red"`) | ★★ 아래 블록 참고 — **이 파일로 잰 것이 아니다.** 배치의 다른 세 파일로 쟀다 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** | 8절. [**21번 주제**](../21-inference-control-const-and-noinfer/)와 **다른 결과**다 |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — `.d.ts` 는 **계산하지 않는다** | 0절에 근거 블록을 실었다 |
| **흔들린다** | ★★★ **절대 경로** — `typeof import(…)` 를 **통째로** 탐침하면 진단에 작업 디렉토리가 박힌다 | 그래서 **안 실었다.** 대신 `keyof` 를 씌워 **키만** 물었다(5절) |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | `typeof` 가 **검사 시간**에 주는 영향 | 재지 않았다. 수치를 적지 않았다 |
| **부적용 — 여러 번 돌려 보기** | 난수·시각·순서 비보장이 **한 칸도 없다** | 그래도 배치 차원에서 5회 확인했다 |

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

- ★★★ 이 블록이 잰 것은 `ex.22a.ts`·`ex.24a.ts`·`ex.25b.ts` 이고 **이 주제의 파일은 한 개도 들어 있지 않다.**
  유니온이 가장 많이 나오는 세 파일을 골라 **배치 대표로** 잰 것이다.
- ★★ 그러므로 4절의 `"Blue" | "Red"` 순서가 안 흔들린다는 것은 **이 배치의 관찰을 이 주제에 끌어다 쓴 것**이지
  **이 파일로 직접 잰 것이 아니다.** 판이 오르면 **이 주제의 파일로 다시 재야** 한다.
- ★ 그래도 **재대조는 이 주제의 블록에도 그대로 돈다** — 캡처를 처음부터 다시 돌려 `diff` 하는 검사는 전 블록이 대상이다.

## 한눈에 — 쉽게 말하면

**이름은 한 글자인데 사는 집이 둘이다. `typeof` 는 값 집의 주소를 타입 집에서 부르는 법이다.**

| 비유 | 실체 |
|---|---|
| 같은 동네에 **주민센터**와 **등기소**가 따로 있다 | 값 공간(value space)과 타입 공간(type space) |
| 두 곳에 **같은 이름이 각각 등록**돼 있어도 충돌이 아니다 | `const box` 와 `type box` 가 한 파일에 공존한다 |
| 등기소 창구에서 **사람 이름을 부르면** 「그건 여기 없다」 | `TS2749` — 값을 타입 자리에 쓴 것 |
| 주민센터 창구에서 **등기 번호를 부르면** 「그건 여기 없다」 | `TS2693` — 타입을 값 자리에 쓴 것 |
| ★★★ **등기소가 주민센터에 「그 사람 기록 좀」 하고 조회**하는 창구 | **`typeof`** — 타입 자리에서 값을 가리킨다 |
| 조회 결과는 **등기소 서류로만 남고** 사람은 안 따라온다 | 방출된 `.js` 에 그 줄이 **한 글자도 안 남는다** |
| ★ **관공서 건물은 퇴근하면 문을 닫는다** | 타입 공간은 **컴파일이 끝나면 사라진다** |

- ★★★ 한 줄로 — 「**`typeof` 는 값에서 타입으로 가는 한 방향 다리이고, 그 다리는 컴파일이 끝나면 걷힌다.**」
- ★★ 그런데 **JS 에도 `typeof` 가 있다.** 글자가 같고 하는 일이 다르다 —
  JS 쪽은 **런타임에 문자열을 돌려주는 연산자**이고, TS 쪽은 **타입 자리에서만 쓰는 타입 연산자**다.
  **한 파일에 둘이 같이 있을 수 있다**(6절이 그 증명이다).

```text
  ★★★ 두 공간 — 같은 이름이 각각 앉아 있다

  +--------------------------+        +--------------------------+
  |        값 공간           |        |       타입 공간          |
  |  (런타임까지 살아남는다)  |        |  (컴파일이 끝나면 사라진다)|
  +--------------------------+        +--------------------------+
  |  const box  = {w,h}      |        |  type box = {deep:true}  |
  |  const plain = 1         |        |  interface Only {q:1}    |
  |  class Both  ------------+--------+--> class Both            |
  |  enum Color  ------------+--------+--> enum Color            |
  +--------------------------+        +--------------------------+

   · const  = 값 공간에만 산다
   · type · interface = 타입 공간에만 산다
   · class · enum = 양쪽에 동시에 산다   ★ 이 둘만 다리를 안 타도 된다
```

```text
  ★★★ typeof 는 다리 하나다 — 방향이 하나뿐이다

      값 공간                        타입 공간
   +-----------+   typeof box     +--------------+
   |  box      | ───────────────> | {w:number;   |
   | {w:1,h:2} |                  |  h:number;}  |
   +-----------+                  +--------------+

   반대 방향은 다리가 없다
   +-----------+                  +--------------+
   |    ???    | <─────────────X  |  interface   |
   +-----------+   TS2693         |    Only      |
                                  +--------------+

   ★ 타입을 값으로 만드는 문법은 없다. 있으면 소거가 깨진다.
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **값 공간과 타입 공간이 정말 따로인가** — 같은 이름을 양쪽에 등록해 놓고 **진단으로 증명**한다(1절).
2. **`typeof` 뒤에 무엇이 올 수 있나** — 되는 것과 안 되는 것을 **전문으로** 받는다(2절). ★ 표현식은 안 된다.
3. **그 타입은 런타임에 남나** — 컴파일한 `.js` 를 꺼내 **직접 확인**한다(6절). **이 주제의 본체다.**

★ 선행은 [**11번 주제**](../11-literal-types-and-as-const/)(README 의 선행 칸)다 — `as const` 로 굳힌 값을 `typeof` 로 꺼내는 자리가 4절이다.
★★ 소거 자체의 정본은 [**01번 주제**](../01-what-ts-adds-and-erases/)이고, 검사 패스와 방출 패스가 갈린다는 것은 [**02번 주제**](../02-type-checking-vs-emit/)다.
여기서는 **「그 두 사실이 이름 하나에서 어떻게 드러나나」** 만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 창

**언제 쓰나** — 아래 모든 절이 이 창들 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 방출된 `.js` + `node` 실행** | 런타임에 **남는 것과 사라진 것** | 사실 | **본체**(6절) |
| ★★★ **진단 전문** | 어느 공간에서 찾았는지 — `TS2693`·`TS2749`·`TS2739`·`TS2741`·`TS2351` | 사실 | 1·3절 |
| ★★ **2창 — `null` 탐침** | 컴파일러가 **계산한** 타입 글자 | **계산된 것** | 3·4·5절 |
| ★ **파스 에러** | `typeof` 의 **문법 경계** — `TS1003`·`TS1005` | 사실 | 2절 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | **적은 것**(계산 안 함) | 아래 블록 |
| **★ 부적용 — 4창(종료 코드 격자)** | 이 주제에는 **한계를 칠 것이 없다** | — | [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 창이다 |

**5창을 닫는 근거** — `.d.ts` 방출기는 **적은 그대로** 남긴다. 계산하지 않는다.

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d22f ex.22f.ts (tsc exit=0) =====
===== 방출된 d22f/ex.22f.d.ts =====
interface User {
    id: number;
    name: string;
}
export type Keys = keyof User;
export declare const oneKey: keyof User;
export type Cond = string extends string ? "가" : "나";
export declare const frozen: readonly ["가", "나"];
export type Elem = (typeof frozen)[number];
export {};
```

- ★★ `keyof User` 도, 조건부 `string extends string ? …` 도, `(typeof frozen)[number]` 도 **풀리지 않은 채** 그대로다.
- ★★★ 그러므로 **「타입이 무엇으로 계산됐나」를 묻는 질문에 `.d.ts` 는 답하지 않는다.** 그 질문은 **2창(탐침)** 의 몫이다.
- ★ `.d.ts` 가 나은 자리는 **여러 줄을 한 번에 훑을 때**뿐이다. 이 주제에는 그런 자리가 없다.

★★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」가 이 주제에 하나 있다.** 5절에서 만난다.

비용 — 컴파일 여섯 번 + 방출 두 번 + `node` 한 번 + `javac` 한 번.

### (1) ★★★ 같은 이름이 두 공간에 따로 산다

**언제 쓰나** — 「`interface` 를 변수처럼 썼더니 왜 안 되지」·「`const` 를 타입 자리에 썼더니 왜 안 되지」일 때.

```ts
// ex.23a.ts
// 값 공간과 타입 공간은 따로다 -- 같은 이름이 양쪽에 각각 산다
const box = { w: 1, h: 2 };
type box = { deep: true };

const asType: box = { deep: true };
const asValue: typeof box = { w: 1, h: 2 };

interface Only {
    q: 1;
}
const useOnlyAsType: Only = { q: 1 };
const useOnlyAsValue = Only;

const plain = 1;
type FromPlain = plain;

class Both {
    x = 0;
}
const bothAsValue = Both;
const bothAsType: Both = new Both();

const deepPath: typeof box.w = 1;
const arrow = (n: number) => n + 1;
const fromArrow: typeof arrow = (n) => n;
console.log(asType, asValue, useOnlyAsType, useOnlyAsValue, bothAsValue, bothAsType, deepPath, fromArrow, null as unknown as FromPlain);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23a.ts (tsc exit=1) =====
ex.23a.ts(12,24): error TS2693: 'Only' only refers to a type, but is being used as a value here.
ex.23a.ts(15,18): error TS2749: 'plain' refers to a value, but is being used as a type here. Did you mean 'typeof plain'?
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **이 절의 결론은 진단이 두 건뿐이라는 사실 자체다.**
  이름을 값 자리 또는 타입 자리에서 **꺼내 쓴 곳이 아홉 군데**인데 **답한 것은 둘**이다 — 나머지 일곱은 **조용히 통과했다.**
- ★★★ 2행과 3행을 보라. `const box` 와 `type box` 가 **같은 파일, 같은 스코프에 나란히 있는데 충돌 진단이 없다.**
  **두 공간이 따로이기 때문에** 이름이 겹칠 수가 없다.
- ★★ 5행 `const asType: box = …` 는 **타입 공간의 `box`** 를 썼고, 6행 `const asValue: typeof box = …` 는
  **값 공간의 `box`** 를 썼다. **한 줄 차이로 서로 다른 것을 가리키는데 둘 다 통과한다.**
- ★★★ **12행이 첫 번째 진단**이다. `interface Only` 를 값 자리에 쓰면
  「`'Only' only refers to a type, but is being used as a value here.`」 — **`TS2693`** 이다.\
  **컴파일러가 「이 이름은 타입 공간에만 있다」고 글자로 말해 준다.**
- ★★★ **15행이 두 번째 진단**이고 이쪽이 더 친절하다.
  `const plain` 을 타입 자리에 쓰면 「`refers to a value, but is being used as a type here. Did you mean 'typeof plain'?`」 — **`TS2749`** 다.\
  ★ **컴파일러가 처방까지 말해 준다.** 그 처방의 이름이 **이 주제의 제목**이다.
- ★★ 20·21행이 **예외**다. `class Both` 는 **값으로도 타입으로도** 쓰이는데 **진단이 없다.**
  클래스는 **두 공간에 동시에 등록**되기 때문이다. `enum` 도 같다(4절).
- ★ 23·25행 — `typeof box.w` 와 `typeof arrow` 도 조용하다. `typeof` 뒤에 **이름 경로**가 오면 된다(2절).

```text
  아홉 군데를 물었고 둘이 답했다

   5행  box       를 타입 자리에    조용함   <- 타입 공간에 있다
   6행  typeof box 를 타입 자리에   조용함   <- 다리를 탔다
  11행  Only      를 타입 자리에    조용함
  12행  Only      를 값 자리에      TS2693   <- 타입 공간에만 있다
  15행  plain     를 타입 자리에    TS2749   <- 값 공간에만 있다 + 처방
  20행  Both      를 값 자리에      조용함   ★ 양쪽에 산다
  21행  Both      를 타입 자리에    조용함   ★ 양쪽에 산다
  23행  typeof box.w               조용함
  25행  typeof arrow               조용함
```

> **값 공간(value space)** — 런타임에 실제로 존재하는 이름이 사는 곳.\
> 예: `const`·`let`·`function`·`class`·`enum` 이 등록된다.

> **타입 공간(type space)** — 검사할 때만 존재하는 이름이 사는 곳.\
> 예: `type`·`interface`·타입 매개변수·`class`·`enum` 이 등록된다.

비용 — 없다. 오히려 **이름을 재사용할 수 있어 아낀다**(`interface Foo` + `const Foo` 조합이 라이브러리에서 흔하다).

### (2) ★ `typeof` 뒤에는 이름 경로만 온다 — 표현식은 안 된다

**언제 쓰나** — 「`typeof (a + b)` 같은 걸 쓰고 싶은데 왜 안 되지」일 때.

★★ 이 절의 파일만 **따로 떼어 던졌다.** 파스 에러가 나면 **같은 파일의 의미 검사가 통째로 멈추기** 때문이다 —
1절의 `TS2693`·`TS2749` 와 한 파일에 두면 **뒤엣것이 아예 안 나온다.**

```ts
// ex.23b.ts
// typeof 뒤에 올 수 있는 것과 없는 것 -- 표현식은 안 된다
const box = { w: 1, h: 2 };

type Ok1 = typeof box;
type Ok2 = typeof box.w;
type Ok3 = typeof box["w"];

type No1 = typeof { w: 1 };
type No2 = typeof (box);
type No3 = typeof box.w + 1;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23b.ts (tsc exit=1) =====
ex.23b.ts(8,19): error TS1003: Identifier expected.
ex.23b.ts(9,19): error TS1003: Identifier expected.
ex.23b.ts(10,25): error TS1005: ';' expected.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 4·5·6행에는 **진단이 없다.** `typeof box` · `typeof box.w` · `typeof box["w"]` 가 **전부 된다.**
  ★ 즉 **점 경로도 되고 대괄호 인덱스도 된다.** 「이름 하나만 된다」는 틀린 요약이다.
- ★★★ 8행 `typeof { w: 1 }` 은 **`TS1003`** — 「Identifier expected.」 **객체 리터럴은 표현식이라 못 온다.**
- ★★★ **9행이 가장 뜻밖이다.** `typeof (box)` 도 **`TS1003`** 이다 — **괄호 하나 때문에** 막힌다.
  값 자리에서는 괄호가 아무것도 안 바꾸는데 **타입 자리에서는 파서가 아예 다른 문법을 읽는다.**
- ★★ 10행 `typeof box.w + 1` 은 **`TS1005`** — 「`';' expected.`」 파서가 `+` 에서 **타입이 끝났다고 판단**한다.
- ★ 세 진단의 **열 번호**가 근거다(`8,19` · `9,19` · `10,25`). 값으로는 못 가르는 것을 **`(행,열)` 이 가른다.**

```text
  typeof 뒤에 올 수 있는 것 / 없는 것

  된다                      안 된다
  +---------------------+   +---------------------------+
  | typeof box          |   | typeof { w: 1 }   TS1003  |
  | typeof box.w        |   | typeof (box)      TS1003  |
  | typeof box["w"]     |   | typeof box.w + 1  TS1005  |
  +---------------------+   +---------------------------+
       이름 경로                    표현식

  ★ 괄호 하나가 「이름 경로」를 「표현식」으로 바꾼다
```

> **이름 경로(entity name)** — 식별자와 그 뒤에 붙는 `.` 접근을 이은 것.\
> 예: `box` · `box.w` · `ns.sub.item`. **호출·연산·리터럴은 아니다.**

비용 — 표현식의 타입이 필요하면 **그 표현식을 일단 `const` 에 담아야** 한다. 한 줄이 는다.

### (3) ★★★ `typeof Class` 는 인스턴스가 아니라 생성자다

**언제 쓰나** — 「클래스 자체를 인자로 받고 싶다」·「`typeof Point` 를 썼는데 `x` 가 없다고 한다」일 때.

★★★ **이 주제에서 가장 많이 틀리는 자리다.**

```ts
// ex.23c.ts
// typeof Class 는 인스턴스가 아니라 생성자다 -- 가장 많이 틀리는 자리
class Point {
    x = 0;
    static origin = new Point();
    static make(): Point {
        return new Point();
    }
}

const instanceSide: null = null as unknown as Point;
const staticSide: null = null as unknown as typeof Point;
const backToInstance: null = null as unknown as InstanceType<typeof Point>;

const wrong: typeof Point = new Point();
const right: typeof Point = Point;
const instWrong: Point = Point;

function makeFromCtor(Ctor: typeof Point): Point {
    return new Ctor();
}
function makeFromInstance(Ctor: Point): Point {
    return new Ctor();
}
console.log(instanceSide, staticSide, backToInstance, wrong, right, instWrong, makeFromCtor, makeFromInstance);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23c.ts (tsc exit=1) =====
ex.23c.ts(10,7): error TS2322: Type 'Point' is not assignable to type 'null'.
ex.23c.ts(11,7): error TS2322: Type 'typeof Point' is not assignable to type 'null'.
ex.23c.ts(12,7): error TS2322: Type 'Point' is not assignable to type 'null'.
ex.23c.ts(14,7): error TS2739: Type 'Point' is missing the following properties from type 'typeof Point': origin, make, prototype
ex.23c.ts(16,26): error TS2741: Property 'x' is missing in type 'typeof Point' but required in type 'Point'.
ex.23c.ts(22,16): error TS2351: This expression is not constructable.
  Type 'Point' has no construct signatures.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 10·11행을 나란히 읽어라. `Point` 는 **`Point`**(인스턴스 쪽), `typeof Point` 는 **`typeof Point`**(정적 쪽)다.
  ★ 탐침이 별칭 이름을 그대로 돌려주지만 **두 이름이 다르다는 것**이 이미 답이다.
- ★★★ **14행이 이 절의 별**이다. `const wrong: typeof Point = new Point();` 가 **`TS2739`** 로 막히고
  진단이 **빠진 속성 이름을 나열한다** — `origin`·`make`·`prototype`.\
  **전부 `static` 이거나 생성자 쪽에만 있는 것**이다. 즉 **`typeof Point` 는 정적 쪽 + 생성 시그니처**다.
- ★★★ **16행이 반대 방향**이다. `const instWrong: Point = Point;` 는 **`TS2741`** —
  「`Property 'x' is missing in type 'typeof Point' but required in type 'Point'.`」\
  **인스턴스 필드 `x` 가 클래스 값 쪽에는 없다.** 두 진단이 **서로의 거울**이다.
- ★★ 15행 `const right: typeof Point = Point;` 는 **조용하다.** 클래스 이름을 값으로 쓰면 그 타입이 **`typeof Point`** 다.
- ★★★ 22행 — `function makeFromInstance(Ctor: Point)` 안에서 `new Ctor()` 가 **`TS2351`** 이고
  이어지는 들여쓴 줄이 이유를 말한다: 「`Type 'Point' has no construct signatures.`」\
  ★ **인스턴스 타입에는 `new` 가 없다.** 19행(`Ctor: typeof Point`)은 조용하다.
- ★★ 12행 — `InstanceType<typeof Point>` 가 **다시 `Point`** 다. **왕복이 닫힌다.**

```text
  클래스 하나, 두 쪽

        class Point { x = 0; static origin; static make(); }
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
   타입 자리의 Point                  값 자리의 Point
   = 인스턴스 쪽                      = typeof Point (정적 쪽)
   +----------------+                 +---------------------+
   | x: number      |                 | origin              |
   |                |                 | make()              |
   |                |                 | prototype           |
   |                |                 | new (...) => Point  |
   +----------------+                 +---------------------+
        ▲                                 │
        └───── InstanceType<typeof Point> ┘

   섞어 쓰면 →  TS2739 「origin, make, prototype 이 없다」
                TS2741 「x 가 없다」
                TS2351 「생성 시그니처가 없다」
```

> **정적 쪽(static side)** — 클래스 값 자체가 가진 멤버의 타입.\
> 예: `static` 멤버 + `prototype` + 생성 시그니처. `typeof Cls` 가 이것이다.

> **`InstanceType<T>`** — 생성 시그니처의 반환 타입을 꺼내는 유틸리티(TS 2.8).\
> 예: `InstanceType<typeof Point>` 는 `Point` 다. 속은 [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 `infer` 다.

비용 — 클래스를 인자로 받는 API 는 **`typeof Cls` 라고 적어야** 하는데, 그러면 **그 클래스에 묶인다.**
아무 클래스나 받으려면 `new (…args) => T` 꼴을 직접 쓴다.

### (4) ★ enum 은 값이자 타입이다 — 그리고 `keyof typeof` 관용구

**언제 쓰나** — 「객체의 키 목록을 타입으로 쓰고 싶다」·「enum 이름 네 가지가 헷갈린다」일 때.

```ts
// ex.23d.ts
// enum 은 값이자 타입이다 -- 그리고 keyof typeof 관용구
enum Color {
    Red,
    Blue,
}
const pick: Color = Color.Red;
const asType: null = null as unknown as Color;
const asValueType: null = null as unknown as typeof Color;
const names: null = null as unknown as keyof typeof Color & {};
const member: null = null as unknown as Color.Red;

const setting = { level: 3, label: "높음", deep: { on: true } };
const settingKeys: null = null as unknown as keyof typeof setting & {};
const settingValue: null = null as unknown as (typeof setting)["level"];
const settingDeep: null = null as unknown as (typeof setting)["deep"];

const frozen = { 가: 1, 나: 2 } as const;
const frozenValues: null = null as unknown as (typeof frozen)[keyof typeof frozen];
console.log(pick, asType, asValueType, names, member, settingKeys, settingValue, settingDeep, frozenValues);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23d.ts (tsc exit=1) =====
ex.23d.ts(7,7): error TS2322: Type 'Color' is not assignable to type 'null'.
ex.23d.ts(8,7): error TS2322: Type 'typeof Color' is not assignable to type 'null'.
ex.23d.ts(9,7): error TS2322: Type '"Blue" | "Red"' is not assignable to type 'null'.
  Type '"Blue"' is not assignable to type 'null'.
ex.23d.ts(10,7): error TS2322: Type 'Color.Red' is not assignable to type 'null'.
ex.23d.ts(13,7): error TS2322: Type '"deep" | "label" | "level"' is not assignable to type 'null'.
  Type '"deep"' is not assignable to type 'null'.
ex.23d.ts(14,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.23d.ts(15,7): error TS2322: Type '{ on: boolean; }' is not assignable to type 'null'.
ex.23d.ts(18,7): error TS2322: Type '1 | 2' is not assignable to type 'null'.
  Type '1' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 7·8·9·10행이 **enum 하나에서 나오는 네 가지 이름**이고 **전부 다른 것**이다.\
  `Color`(7행, 멤버 전체의 타입) · `typeof Color`(8행, **값 객체의 타입**) ·
  `keyof typeof Color`(9행, **`"Blue" | "Red"`** — 이름들) · `Color.Red`(10행, **한 멤버의 타입**).
- ★★ 6행은 조용하다 — `const pick: Color = Color.Red;` 에서 **왼쪽은 타입 공간, 오른쪽은 값 공간**의 `Color` 다.
  **한 줄에 두 공간이 다 나온다.**
- ★★★ **9행이 이 절의 관용구**다. `keyof typeof X` 는 **두 연산자를 이어 붙인 것**이다 —
  먼저 `typeof` 가 값을 타입으로 건너오게 하고, 그다음 `keyof` 가 그 타입의 키를 뽑는다.\
  ★ `keyof` 쪽은 [**22번 주제**](../22-keyof-and-indexed-access-types/)가 정본이다. **22 와 23 이 만나는 자리가 여기다.**
- ★★ 13행 — 평범한 객체에도 같은 관용구가 그대로 먹는다. `keyof typeof setting` 이 **`"deep" | "label" | "level"`** 이다.
- ★★ 14·15행 — `(typeof setting)["level"]` 이 **`number`**, `(typeof setting)["deep"]` 이 **`{ on: boolean; }`** 다.\
  ★ **괄호가 필요하다.** 2절에서 `typeof (box)` 가 막혔던 것과 **다른 자리의 괄호**다 —
  여기 괄호는 `typeof` 의 **인자**를 감싸는 게 아니라 **`typeof setting` 전체**를 감싼다.
- ★★★ 18행이 [**11번 주제**](../11-literal-types-and-as-const/)와 만나는 자리다.
  `as const` 로 굳힌 객체에 `(typeof frozen)[keyof typeof frozen]` 를 씌우면 **`1 | 2`** 가 나온다 —
  **값 리터럴이 타입으로 건너왔다.** `as const` 가 없었다면 `number` 였을 것이다(22 절에서 나란히 던졌다).

```text
  enum Color { Red, Blue }  에서 나오는 네 이름

  값 공간                    타입 공간
  +-------------+
  | Color       |  typeof   +--------------------+
  | { Red:0,    | ────────> | typeof Color       |  8행
  |   Blue:1,   |           +--------------------+
  |   0:"Red",  |                   │ keyof
  |   1:"Blue"} |                   ▼
  +-------------+           +--------------------+
                            | "Blue" | "Red"     |  9행
                            +--------------------+

                            +--------------------+
                            | Color              |  7행  멤버 전체의 타입
                            | Color.Red          | 10행  멤버 하나의 타입
                            +--------------------+

  ★ 네 개가 전부 다른 것이다. 「Color 하나」라고 생각하면 틀린다
```

> **`keyof typeof x`** — 값 `x` 의 타입을 가져와 그 키 유니온을 만드는 관용구.\
> 예: `const setting = {level:3}` 에서 `keyof typeof setting` 은 `"level"` 이다.

비용 — enum 은 **방출물에 객체가 남는다**([목록의 **31번 주제**](../31-enum-pitfalls/)가 정본). 그 대가가 싫으면 `as const` + 유니온 리터럴을 쓴다.

### (5) ★★★ `typeof import(…)` — 그리고 제5의 상태

**언제 쓰나** — 「모듈을 실제로 import 하지 않고 그 모듈의 타입만 쓰고 싶다」일 때.

```ts
// mod23.ts
export const version = "1.0";
export function greet(who: string): string {
    return "안녕 " + who;
}
export interface Opts {
    deep: boolean;
}
```

```ts
// ex.23e.ts
// typeof import(...) -- 모듈을 열지 않고 그 모듈의 값 공간을 타입으로 받는다
const moduleKeys: null = null as unknown as keyof typeof import("./mod23") & {};
const oneExport: null = null as unknown as typeof import("./mod23").version;
const fnExport: null = null as unknown as typeof import("./mod23").greet;
const typeExport: null = null as unknown as import("./mod23").Opts;
console.log(moduleKeys, oneExport, fnExport, typeExport);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23e.ts (tsc exit=1) =====
ex.23e.ts(2,7): error TS2322: Type '"greet" | "version"' is not assignable to type 'null'.
  Type '"greet"' is not assignable to type 'null'.
ex.23e.ts(3,7): error TS2322: Type '"1.0"' is not assignable to type 'null'.
ex.23e.ts(4,7): error TS2322: Type '(who: string) => string' is not assignable to type 'null'.
ex.23e.ts(5,7): error TS2322: Type 'Opts' is not assignable to type 'null'.
```

★★★ **여기가 제5의 상태다 — 「같은 질문을 다른 창으로 물었다」.**
`typeof import("./mod23")` 를 **통째로** 2창에 물으면 진단이 그 모듈을 **절대 경로로** 찍는다.
그 경로는 **작업 디렉토리에 달려 있어** 다른 머신에서 재현되지 않는다 — 「흔들리는 칸」이다.
그래서 **그 탐침을 싣지 않고**, 대신 **`keyof` 를 씌워 키만** 물었다(2행).
★ 그런데 **바꿔 물은 쪽이 오히려 더 강한 근거였다.** 아래 해설을 보라.
★ 바꾼 창이 못 보는 것 — **모듈 타입의 전체 모양**은 여전히 못 본다. 키 목록과 낱낱의 export 만 안다.

그림 해설 — 한 단계에 한 문장.

- ★★★ **2행이 이 절의 별이다.** `keyof typeof import("./mod23")` 가 **`"greet" | "version"`** 인데
  `mod23.ts` 에는 **`Opts` 도 export** 돼 있다.\
  **`Opts` 가 키 목록에 없다** — `interface` 는 **값 공간에 없으므로** 모듈의 값 객체에도 없다.\
  ★★★ **목록의 공백이 답이다.** 1절의 `TS2693` 과 **같은 사실**을 모듈 단위에서 다시 본 것이다.
- ★★ 3행 — `typeof import("./mod23").version` 이 **`"1.0"`** 이다. `const` 로 선언된 문자열이라 **리터럴 타입 그대로** 온다.
- ★★ 4행 — 함수 export 는 **`(who: string) => string`** 으로 온다.
- ★★★ 5행이 **대비**다. `import("./mod23").Opts`(★ `typeof` 가 **없다**)는 **통과**하고 **`Opts`** 를 준다.\
  **같은 모듈을 타입 자리에서 열면 타입 공간이 보이고, `typeof` 로 열면 값 공간이 보인다.**
- ★ 즉 `import(…)` 는 **두 공간 양쪽에 문이 있고**, `typeof` 를 붙이느냐가 **어느 문으로 들어가느냐**를 정한다.

```text
  import("./mod23") 에는 문이 둘이다

                       +-- typeof import("./mod23") --> 값 공간
                       |      keys: "greet" | "version"      2행
   mod23.ts            |      ★ Opts 가 없다
   · export const version
   · export function greet   |
   · export interface Opts   |
                       +-- import("./mod23").Opts ----> 타입 공간
                              Opts                          5행
```

비용 — 경로 문자열이 **타입 안에 박힌다.** 파일을 옮기면 타입이 깨지고, 진단에 **절대 경로가 나올 수 있다**(위 참고).

### (6) ★★★ 본체 — 방출된 `.js` 가 두 `typeof` 를 갈라 준다

**언제 쓰나** — 「TS 의 `typeof` 와 JS 의 `typeof` 가 같은 것인가」를 **지울 때.**

```ts
// ex.23f.ts
// 글자가 같고 하는 일이 다르다 -- 타입 자리의 typeof 와 값 자리의 typeof
const setting = { level: 3, label: "높음" };

type Setting = typeof setting;
const copy: Setting = { level: 9, label: "낮음" };

const runtimeTag: string = typeof setting;

function describe(x: string | number): string {
    if (typeof x === "string") {
        return "문자 " + x.length;
    }
    return "숫자 " + x.toFixed(1);
}

class Shape {}
const ctorTag: string = typeof Shape;

console.log(copy.level, runtimeTag, describe("가나"), describe(3), ctorTag);
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e23f ex.23f.ts (tsc exit=0) =====
===== 방출된 e23f/ex.23f.js =====
"use strict";
// 글자가 같고 하는 일이 다르다 -- 타입 자리의 typeof 와 값 자리의 typeof
const setting = { level: 3, label: "높음" };
const copy = { level: 9, label: "낮음" };
const runtimeTag = typeof setting;
function describe(x) {
    if (typeof x === "string") {
        return "문자 " + x.length;
    }
    return "숫자 " + x.toFixed(1);
}
class Shape {
}
const ctorTag = typeof Shape;
console.log(copy.level, runtimeTag, describe("가나"), describe(3), ctorTag);
```

```text
===== node e23f/ex.23f.js (node exit=0) =====
9 object 문자 2 숫자 3.0 function
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **종료 코드가 `0` 이다** — 진단이 **0줄**이다. 이 절의 근거는 **에러가 아니라 방출물**이다.
- ★★★ 소스 4행 `type Setting = typeof setting;` 이 **방출물에 통째로 없다.**
  선언 한 줄이 **한 글자도 안 남았다.**
- ★★★ 소스 7행 `const runtimeTag: string = typeof setting;` 은 **`const runtimeTag = typeof setting;`** 로 남았다.\
  **타입 주석만 벗겨지고 `typeof` 는 그대로다.** 같은 여섯 글자가 **한쪽은 사라지고 한쪽은 남았다.**
- ★★★ 소스 5행 `const copy: Setting = …` 도 주석만 벗겨진다. **`Setting` 이라는 이름은 방출물 어디에도 없다.**
- ★★ 소스 10행 `if (typeof x === "string")` 은 **그대로 남았다.**\
  ★ **이 줄은 두 층에서 동시에 산다** — 런타임에는 분기이고, 검사에서는 좁히기다.
  좁히기 쪽은 [**12번 주제**](../12-narrowing/)가 정본이고, 여기서는 **두 `typeof` 가 만나는 자리**라는 것까지만 본다.
- ★★★ `node` 출력이 `9 object 문자 2 숫자 3.0 function` 이다.
  - `9` — 타입만 벗겼을 뿐 값은 그대로다.
  - **`object`** — `typeof setting` 의 런타임 답. **타입 자리에서 물었으면 `{ level: number; label: string; }` 였다.**
  - `문자 2`·`숫자 3.0` — 좁히기가 런타임에도 맞게 돌았다.
  - ★★ **`function`** — `typeof Shape` 가 **`function`** 이다. **클래스도 런타임에는 함수**다.
    ★ 같은 글자를 **타입 자리**에서 물으면 3절에서 본 **`typeof Point`**(정적 쪽)가 나온다. **완전히 다른 답이다.**

```text
  ★★★ 같은 여섯 글자, 두 운명

  소스 (ex.23f.ts)                      방출 (ex.23f.js)
  ─────────────────────────────────     ─────────────────────────────
  type Setting = typeof setting;   ──X   (줄 자체가 없다)
  const copy: Setting = {...};     ──>   const copy = {...};
  const runtimeTag: string =             const runtimeTag =
        typeof setting;            ──>         typeof setting;
  if (typeof x === "string")       ──>   if (typeof x === "string")
  const ctorTag: string =                const ctorTag =
        typeof Shape;              ──>         typeof Shape;

  타입 자리의 typeof  ->  사라진다
  값  자리의 typeof  ->  남는다 · node 가 "object" / "function" 을 찍는다
```

```text
  두 typeof 가 답하는 것이 다르다

                  typeof setting
                        │
        ┌───────────────┴───────────────┐
   타입 자리                        값 자리
   { level: number;                 "object"
     label: string; }               (문자열 여덟 종 중 하나)
        │                                │
   컴파일 때만 있다                 런타임에 계산된다
   node 는 못 본다                  tsc 는 값을 모른다
```

★★ JS 쪽 `typeof` 의 정본은
`` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **01번**([값의 종류와 `typeof`](../../../js/syntax/01-value-types-and-typeof/)) ``다.
**돌려주는 문자열의 종류와 `typeof null` 의 함정은 그쪽**이고, 여기서는 **글자가 같다는 사실**만 다룬다.

비용 — 없다. 다만 **읽는 사람이 헷갈린다.** 값 자리인지 타입 자리인지는 **문맥으로만** 갈린다.

### (7) ★ 교차 갈래 — Java 도 이름 공간이 둘이다

**언제 쓰나** — 「이 구분이 TS 만의 것인가」를 물을 때.

```java
// Erased.java
import java.util.List;

public class Erased {
    interface Opts {
        boolean deep();
    }

    static boolean isStrings(Object o) {
        return o instanceof List<String>;
    }

    static Object useTypeAsValue() {
        return Opts;
    }
}
```

```text
===== javac -d jout Erased.java (javac exit=1) =====
Erased.java:9: error: Object cannot be safely cast to List<String>
        return o instanceof List<String>;
               ^
Erased.java:13: error: cannot find symbol
        return Opts;
               ^
  symbol:   variable Opts
  location: class Erased
2 errors
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 13행 — `Opts`(중첩 인터페이스)를 값 자리에 쓰면 javac 가 「`cannot find symbol`」 뒤에
  **`symbol: variable Opts`** 라고 적는다.\
  ★★ **「변수 이름 공간에서 찾았다」고 컴파일러가 스스로 말한 것**이다. TS 의 `TS2693` 과 **같은 사실**이다.
- ★★ 9행 — `o instanceof List<String>` 이 「`Object cannot be safely cast to List<String>`」 으로 막힌다.
  **제네릭 인자가 런타임에 없기** 때문이다.
- ★★★ **그런데 TS 와 Java 는 지우는 범위가 다르다.**\
  Java 는 **제네릭 인자만** 지운다 — `List` 라는 클래스는 런타임에 **남는다**(`instanceof List` 는 된다).\
  TS 는 **타입 층 전체**를 지운다 — `interface Opts` 는 방출물에 **흔적이 없다**(6절).
- ★ 그래서 진단의 결이 다르다. Java 는 「**안전하게 캐스트할 수 없다**」고 말하고, TS 는 「**그런 값이 없다**」고 말한다.

```text
  지우개가 닿는 범위

  Java                              TypeScript
  +---------------------------+     +---------------------------+
  | class List      남는다    |     | interface Opts   사라진다 |
  |   <String>      지워진다  |     | type Setting     사라진다 |
  | class Erased    남는다    |     | class Shape      남는다   |
  +---------------------------+     +---------------------------+
   -> instanceof List 는 된다        -> 타입 이름으로는 아무것도 못 묻는다
   -> instanceof List<String> 막힘   -> 값으로 남는 것은 class·enum 뿐
```

★ 소거 쪽 정본은
`` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([타입 소거 — 런타임에 없는 것·제네릭 배열 금지·브리지 메서드](../../../java/syntax/19-type-erasure/)) ``다.
여기서는 **「이름 공간이 둘이다」라는 사실이 언어를 안 가린다**는 것까지만 본다.

비용 — 없다(비교만 했다).

### (8) ★ `strict` 대조 — 이 주제는 설정에 안 달렸다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.23a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★ 다섯 파일 **전부** `--strict` 를 꺼도 **출력이 한 글자도 같다.**
- ★★★ **[21번 주제](../21-inference-control-const-and-noinfer/)와 다른 결과**다 — 거기서는 여섯 파일 중 **하나가 갈렸다**(제약이 가변 배열인 자리).
  ★ 그러므로 「**`--strict` 는 늘 상관없다**」도 「**늘 상관있다**」도 틀렸다. **자리마다 던져 봐야 한다.**
- ★ 여기서 안 갈리는 이유를 한 줄로 — **`typeof` 는 추론을 하지 않는다.** 값의 선언된 타입을 **그대로 가져올 뿐**이다.
  `strict` 가 바꾸는 것은 주로 **추론과 널 취급**인데, 이 주제에는 그 둘이 걸린 칸이 없다.
  ★★ 단 **탐침 자체는 `strictNullChecks` 에 기댄다** — 그런데도 출력이 같았다는 것은 **이 판의 관찰**이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것

  const box = { w: 1, h: 2 };
  type T1 = typeof box;              ★ 값 -> 타입
  type T2 = typeof box.w;            ★ 점 경로도 된다
  type T3 = typeof box["w"];         ★ 대괄호도 된다

  type K  = keyof typeof box;        ★ 22 와 이어 붙이는 관용구
  type V  = (typeof box)["w"];       ★ 괄호로 감싸 인덱스 접근

  class Point { static make() {} }
  type Ctor = typeof Point;          ★ 정적 쪽 + 생성 시그니처
  type Inst = InstanceType<Ctor>;    ★ 다시 인스턴스 쪽

  type M  = typeof import("./mod23");      ★ 2.9 — 모듈의 값 공간
  type O  = import("./mod23").Opts;        ★ typeof 없이 -> 타입 공간
```

```text
금지 사례 — 던져서 받은 것 다섯. 전문은 「동작 방식」의 블록에 있다

  1) 타입을 값 자리에        ->  TS2693  「only refers to a type, but is being
                                          used as a value here」
  2) 값을 타입 자리에        ->  TS2749  「refers to a value, but is being used
                                          as a type here. Did you mean 'typeof …'?」
  3) typeof { w: 1 }        ->  TS1003  「Identifier expected」
     typeof (box)           ->  TS1003  ★ 괄호 하나 때문이다
     typeof box.w + 1       ->  TS1005  「';' expected」
  4) typeof Cls 자리에 인스턴스 ->  TS2739  빠진 속성을 이름으로 나열한다
     인스턴스 자리에 클래스     ->  TS2741
  5) 인스턴스 타입에 new       ->  TS2351  「no construct signatures」
```

**규칙 불릿**

- ★★★ **이름은 두 공간에 따로 등록된다** — `const`/`function` 은 값 공간, `type`/`interface` 는 타입 공간,
  **`class`·`enum` 은 양쪽**(1절 20·21행 · 4절 6행).
- ★★★ **`typeof` 는 값 공간의 이름을 타입 자리에서 부르는 유일한 문법**이다. 반대 방향은 없다(1절 12행).
- ★★ **`typeof` 뒤에는 이름 경로만 온다** — 점 접근과 대괄호는 되고 **괄호와 표현식은 안 된다**(2절 8·9·10행).
- ★★★ **`typeof Cls` 는 정적 쪽**이다 — 인스턴스가 아니다(3절 14·16행). 되돌리려면 `InstanceType<typeof Cls>`(3절 12행).
- ★★ **`keyof typeof x` 는 두 연산자를 이어 붙인 것**이다 — 먼저 건너오고 그다음 키를 뽑는다(4절 9·13행).
- ★★ **`typeof import(…)` 는 값 공간**, **`import(…).T` 는 타입 공간**이다(5절 2·5행).
- ★★★ **타입 자리의 `typeof` 는 방출물에 한 글자도 안 남고, 값 자리의 `typeof` 는 그대로 남는다**(6절).
- ★ **`--strict` 를 꺼도 이 다섯 파일은 한 글자도 안 갈린다**(8절).

## 어디서 틀리나

- ★★★ 「**`typeof Cls` 면 그 클래스의 인스턴스겠지**」 — **아니다. 정적 쪽이다**(3절 14행).
  ★ 이 배치에서 **가장 많이 틀리는 자리**로 꼽은 곳이다. 진단이 `origin`·`make`·`prototype` 을 **이름으로 불러 준다.**
- ★★★ 「**TS 의 `typeof` 와 JS 의 `typeof` 는 같은 것이겠지**」 — **글자만 같다**(6절).
  하나는 타입을 주고 하나는 문자열을 준다. `typeof Shape` 가 타입 자리에서는 정적 쪽, 값 자리에서는 `function` 이다.
- ★★★ 「**같은 이름을 값과 타입에 둘 다 쓰면 충돌하겠지**」 — **충돌하지 않는다**(1절 2·3행). 공간이 다르다.
- ★★ 「**`interface` 를 변수에 담을 수 있겠지**」 — **없다**(1절 12행 `TS2693`). 런타임에 그런 값이 없다.
- ★★ 「**`typeof (box)` 쯤은 괄호니까 되겠지**」 — **`TS1003`** 이다(2절 9행). 괄호가 표현식 문법을 연다.
- ★★ 「**모듈을 `typeof import` 로 열면 타입도 같이 보이겠지**」 — **안 보인다**(5절 2행).
  `Opts` 가 키 목록에 **없다.** 타입을 꺼내려면 `typeof` 를 **빼야** 한다(5행).
- ★ 「**enum 의 `Color` 하나만 알면 되겠지**」 — **네 가지가 다른 것**이다(4절 7·8·9·10행).
- ★ 「**`typeof x` 를 쓰면 `x` 가 런타임에 필요하겠지**」 — **아니다.** `declare const` 로만 있어도 된다.
  ★★ 다만 **반대는 참이다** — 값 자리의 `typeof` 는 그 값을 **실제로 평가**한다(6절 방출물).
- ★ 「**`typeof` 가 추론을 하니까 `strict` 에 달렸겠지**」 — **이 다섯 파일에서는 안 갈렸다**(8절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(TS 1.0)** | 값 공간과 타입 공간이 **분리**돼 있고 `typeof` 가 값 -> 타입 **한 방향** 다리다 | 1절 12·15행 |
| **언어 보장** | `class`·`enum` 은 **양쪽 공간에 동시 등록**된다 | 1절 20·21행 · 4절 6행 |
| **언어 보장** | `typeof Cls` 는 **정적 쪽**이다 | 3절 14·16행 |
| **언어 보장(TS 2.9)** | `typeof import(…)` 가 모듈의 **값 공간**을 준다 | 5절 2행 |
| **언어 보장(소거)** | ★★★ 타입 층은 **방출물에 안 남는다** | 6절 — [**01번 주제**](../01-what-ts-adds-and-erases/)가 정본 |
| **★ 이 판(7.0.2)의 관찰** | `typeof` 의 **문법 경계** — 괄호가 `TS1003` 을 낸다는 것 | 2절 9행. **문법 오류의 코드·열은 판에 매인다** |
| **★ 이 판의 관찰** | 진단이 **빠진 속성 이름을 나열**해 주는 것(`origin, make, prototype`) | 3절 14행 — 문구는 판에 매인다 |
| **★ 이 판의 관찰** | 탐침이 **별칭 이름을 그대로 찍는 것**(`typeof Point`·`Color`) | 3절 11행 · 4절 7·8행 |
| **★ 이 판의 관찰** | 유니온 원소의 **표시 순서**(`"Blue" \| "Red"`) | 5회 md5 가짓수 1 — **관찰이지 보장이 아니다** |
| **★ 이 판의 관찰** | `--strict` 를 꺼도 **다섯 파일이 안 갈린다** | 8절 |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — 계산하지 않고 적은 그대로 남긴다 | 0절 |
| **★ 부적용 — 4창(격자)** | 한계를 칠 것이 이 주제에 없다 | — |
| **흔들린다** | `typeof import(…)` 를 통째로 물었을 때의 **절대 경로** | 그래서 **안 실었다**(5절) |
| **안 잰 것** | `typeof` 가 **검사 시간**에 주는 영향 | 재지 않았다 |

★★★ **이 주제는 「언어 보장」 칸이 가장 두껍다.** 22·24·25 와 반대다 —
거기서는 계산 결과가 **컴파일러 구현**에 달린 칸이 많지만, 여기서는 **공간 분리와 소거**가 언어의 뼈대이기 때문이다.

## 언제 쓰고 언제 안 쓰나

| `typeof` 를 쓴다 | 안 쓴다 |
|---|---|
| 값이 **이미 있고** 그 모양을 타입으로 **중복 없이** 쓰고 싶을 때(설정 객체·기본값) | 타입을 **먼저** 정하고 값을 거기 맞추고 싶을 때 — 그때는 `interface` 가 정본 |
| `as const` 로 굳힌 목록에서 **키·값 유니온**을 뽑을 때(4절 18행) | 값이 **넓게 추론**돼 있을 때 — `typeof` 는 **그 넓은 타입을 그대로** 가져온다 |
| 클래스를 **인자로 받을** 때(`typeof Cls`, 3절 19행) | 아무 클래스나 받고 싶을 때 — `new (…) => T` 를 직접 쓴다 |
| 모듈을 **실제로 import 하지 않고** 타입만 쓸 때(5절) | 경로가 자주 바뀌는 모듈 — 타입에 경로가 박힌다 |
| enum·객체의 **이름 목록**이 필요할 때(`keyof typeof`) | 이름 목록이 **바뀌어도 되는** 곳 — 유니온 리터럴을 직접 적는 쪽이 읽기 쉽다 |

## 핵심 문장

1. **이름은 두 공간에 따로 산다** — `const box` 와 `type box` 는 충돌하지 않는다.
2. **`typeof` 는 값 -> 타입 한 방향 다리다** — 반대 방향 문법은 없다(있으면 소거가 깨진다).
3. **`typeof` 뒤에는 이름 경로만 온다** — 괄호 하나가 `TS1003` 을 낸다.
4. **`typeof Cls` 는 정적 쪽이다** — 인스턴스는 `InstanceType<typeof Cls>` 다.
5. **`class`·`enum` 만 두 공간에 동시에 산다** — 나머지는 한쪽뿐이다.
6. **타입 자리의 `typeof` 는 사라지고 값 자리의 `typeof` 는 남는다** — 방출물이 그 증명이다.
7. **같은 이름을 두 공간에서 물으면 다른 답이 온다** — `typeof Shape` 가 정적 쪽이고 `function` 이다.

## 관련 자료

- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — **소거 자체가 그쪽 정본**이다.
  ★ 경계 — 그쪽은 「무엇이 지워지나」까지, 여기는 「**그 사실이 이름 하나에서 어떻게 드러나나**」부터.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 두 패스가 갈린다는 구조는 그쪽.
  ★ 경계 — 그쪽은 「에러가 있어도 방출된다」까지, 여기는 **방출물을 읽어 두 `typeof` 를 가르는 것**부터.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — README 가 지정한 **선행**이다.
  ★ 경계 — 그쪽은 「어떻게 굳히나」까지, 여기는 **굳힌 것을 타입 자리로 꺼내는 것**부터(4절 18행).
- [**12번 주제** — 좁히기](../12-narrowing/) — `typeof x === "string"` 의 **좁히기 규칙은 그쪽 정본**이다.
  ★ 경계 — 그쪽은 분기마다 타입이 어떻게 줄어드나까지, 여기는 **그 줄이 두 층에 동시에 산다**는 것까지만.
- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — `keyof` 와 `T[K]` 는 그쪽 정본.
  ★ 경계 — 그쪽은 `keyof` 가 무엇으로 펼쳐지나까지, 여기는 **`keyof typeof` 로 이어 붙이는 자리**만.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — `typeof` 로 뽑은 타입이 **이름이 아니라 모양**으로 비교되는 이유.
- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) · [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) —
  `InstanceType` 의 속이 그쪽 `infer` 다. **같은 배치의 나머지.**
- [목록의 **31번 주제**](../31-enum-pitfalls/)(열거형의 함정) — enum 이 **방출물에 남기는 것**과 `const enum` 은 그쪽이 정본.
  ★ 경계 — 여기서는 **enum 이 두 공간에 산다**는 사실까지만.
- [목록의 **36번 주제**](../36-type-only-imports-and-exports/)(타입 전용 import·export) — `import type` 이 방출에 주는 영향은 그쪽.
  ★ 경계 — 여기서는 `typeof import(…)` 가 **어느 공간을 여느냐**까지만.
- [목록의 **29번 주제**](../29-satisfies/)(`satisfies`) — 값을 검사하되 타입을 안 넓히는 도구. `typeof` 로 꺼내기 **전에** 쓰는 자리다.
- `` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **01번**([값의 종류와 `typeof`](../../../js/syntax/01-value-types-and-typeof/)) `` —
  **런타임 `typeof` 의 정본.** 돌려주는 문자열 여덟 종과 `typeof null` 의 함정은 그쪽이다.
- `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([타입 소거 — 런타임에 없는 것·제네릭 배열 금지·브리지 메서드](../../../java/syntax/19-type-erasure/)) `` —
  7절의 대비. ★ **지우개가 닿는 범위가 다르다.**

## 용어 풀이

> **값 공간(value space)** — 런타임까지 살아남는 이름이 등록되는 곳.\
> 예: `const box` 는 값 공간에만 있어서 타입 자리에 쓰면 `TS2749` 다.

> **타입 공간(type space)** — 검사할 때만 존재하는 이름이 등록되는 곳.\
> 예: `interface Only` 는 타입 공간에만 있어서 값 자리에 쓰면 `TS2693` 이다.

> **타입 질의(type query)** — 타입 자리에서 값의 이름을 물어 그 타입을 얻는 문법.\
> 예: `typeof box`. **이름 경로만** 받는다.

> **이름 경로(entity name)** — 식별자와 `.` 접근을 이은 것.\
> 예: `box` · `box.w`. `(box)` 나 `{ w: 1 }` 은 아니다.

> **정적 쪽(static side)** — 클래스 값 자체의 타입. `static` 멤버 + `prototype` + 생성 시그니처.\
> 예: `typeof Point` 에 `origin`·`make`·`prototype` 이 들어 있다.

> **인스턴스 쪽(instance side)** — `new` 로 만든 객체의 타입.\
> 예: 타입 자리에 그냥 `Point` 라고 쓰면 이쪽이다.

> **`InstanceType<T>`** — 생성 시그니처의 반환 타입을 꺼내는 유틸리티(TS 2.8).\
> 예: `InstanceType<typeof Point>` 는 다시 `Point` 다.

> **`keyof typeof x`** — 값 `x` 의 타입을 가져와 그 키 유니온을 만드는 관용구.\
> 예: `keyof typeof Color` 가 `"Blue" | "Red"` 다.

> **소거(erasure)** — 컴파일 뒤 타입 층이 사라지는 것.\
> 예: `type Setting = typeof setting;` 한 줄이 방출물에 아예 없다.

> **동적 import 타입(`import("…")`)** — 모듈을 타입 자리에서 가리키는 문법(TS 2.9).\
> 예: `typeof import("./mod23")` 는 값 공간, `import("./mod23").Opts` 는 타입 공간이다.

> **`TS2693`** — 타입 이름을 값 자리에 썼을 때의 코드.\
> 예: `const x = Only;` (`Only` 가 `interface` 일 때).

> **`TS2749`** — 값 이름을 타입 자리에 썼을 때의 코드. **처방까지 말해 준다.**\
> 예: `type T = plain;` 에서 「Did you mean 'typeof plain'?」이 붙는다.

## 더 들어가면

- **왜 반대 방향 다리가 없나** — 타입을 값으로 만드는 문법(`valueof` 같은 것)이 있으면 **타입이 런타임에 남아야** 한다.
  그러면 [**01번 주제**](../01-what-ts-adds-and-erases/)의 전제(「지우기만 하면 JS 가 된다」)가 깨지고,
  [목록의 **36번 주제**](../36-type-only-imports-and-exports/)의 `erasableSyntaxOnly` 같은 방향도 성립하지 않는다.
  ★ **`class` 와 `enum` 이 양쪽에 사는 것은 예외가 아니라 그 둘이 원래 값을 만들기 때문**이다.
- **`typeof` 가 `const` 의 넓어짐을 그대로 가져온다는 것** — `const setting = { level: 3 }` 의 `level` 은 `number` 로 넓어져 있고,
  `typeof setting` 은 **그 넓어진 결과**를 가져온다(4절 14행이 `number` 다).
  좁히고 싶으면 **값 쪽에서** `as const` 를 붙여야 한다(4절 18행이 `1 | 2` 인 이유).
  ★ 즉 **`typeof` 는 계산하지 않고 가져오기만 한다** — 이 점에서 `keyof`·조건부와 성질이 다르다.
- **`typeof` 와 오버로드** — 오버로드된 함수에 `typeof` 를 붙이면 **오버로드 목록 전체**가 온다.
  이 배치에서는 **안 던졌다.** [**16번 주제**](../16-function-types-and-overloads/)가 오버로드의 정본이다.
- **`typeof` 와 제네릭 함수** — 타입 매개변수가 살아 있는 채로 온다. **안 던졌다.**
- **`typeof this`·`typeof globalThis`** — **안 던졌다.**
- **`typeof` 가 `unique symbol` 과 만나는 자리** — `declare const s: unique symbol` 에서 `typeof s` 는 그 심볼 하나만 가리킨다.
  README 의 「뺀 것」에 `unique symbol` 이 있어 **안 던졌다.**
- **모듈 보강에서 `typeof` 로 전역을 읽는 것** — [목록의 **33번 주제**](../33-declaration-merging/)·[목록의 **37번 주제**](../37-writing-declaration-files/)의 몫이다. **안 던졌다.**
