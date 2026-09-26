# ts/syntax/17 — 변성과 매개변수 양립성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — More on Functions: Parameter type compatibility](https://www.typescriptlang.org/docs/handbook/2/functions.html) ·
> [TSConfig — `strictFunctionTypes`](https://www.typescriptlang.org/tsconfig/#strictFunctionTypes) ·
> [TypeScript 4.7 릴리스 노트 — Optional Variance Annotations](https://devblogs.microsoft.com/typescript/announcing-typescript-4-7/).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `strictFunctionTypes` 는 `strict` 에 딸려 **켜져 있다.**
> `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로 이 블록들은 설정 파일 없이도 그대로 재현된다.
> **버전** — `strictFunctionTypes` 는 TS 2.6, **`in`/`out` 변성 표기는 TS 4.7** 이다.
> ★★★ 「4.7 기능이 7.0 에서도 도는가」는 **외우지 않고 던져서 확인했다** — 3절이 그 결과다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ **4절의 「진단 0건」** — 이 주제의 본체 하나다 | 소스 전문을 옆에 뒀으니 다시 던질 수 있다 |
| **안 흔들린다** | ★★ `TS2636` 의 `sub-T`·`super-T` 라는 **가상 이름** | 보고기가 찍는 고정 표기다 |
| **★ 설정에 달렸다** | ★★★ **네 파일 전부** — `strictFunctionTypes` | 양쪽 판을 다 실었다. **이 주제는 플래그가 곧 주제다** |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다. 예외도 `message` 만 찍어 **스택을 안 남겼다** |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | 변성 계산의 **검사 시간** | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ 1절의 `--strictFunctionTypes false` 판은 **진단이 0줄**이다 — 그 블록도 **명령과 종료 코드까지** 캡처했다.

## 한눈에 — 쉽게 말하면

**변성은 「이 자리에 더 넓은 것을 넣어도 되나, 더 좁은 것을 넣어도 되나」의 규칙이다.**

| 비유 | 실체 |
|---|---|
| **받는 자리**는 넓을수록 안전하다 | 매개변수는 **contravariant** — 넓은 쪽을 넣어도 된다 |
| **주는 자리**는 좁을수록 안전하다 | 반환 타입은 **covariant** — 좁은 쪽을 줘도 된다 |
| ★★★ 그런데 **메서드만 양쪽을 다 허용**한다 | 메서드 문법은 **bivariant** — `strictFunctionTypes` 를 켜도 그렇다 |
| **읽고 쓰는 자리**는 한 치도 못 움직인다 | `in out` 표기 — **invariant** |
| 상자에 **다른 것을 넣을 수 있으면** 위험하다 | 배열은 covariant 라 **런타임에 터진다** |
| 상자를 **읽기 전용으로** 건네면 반은 막힌다 | `readonly T[]` — **넣는 것만** 막는다 |

- ★★★ 한 줄로 — 「**안전한 규칙은 contravariance 인데, TS 는 메서드에서 그것을 일부러 포기했다.**」
- ★★ 그래서 이 주제의 값은 규칙을 외우는 것이 아니라 **「어디가 일부러 뚫려 있는지」를 아는 것**이다.

```text
  안전한 방향은 어느 쪽인가        (Dog 는 Animal 이다)

  받는 자리 (매개변수)                     주는 자리 (반환 타입)
  ───────────────────────────              ───────────────────────────
  (a: Animal) => void                      () => Dog
        │ 넣을 수 있다                            │ 넣을 수 있다
        ▼                                        ▼
  (a: Dog) => void 자리                    () => Animal 자리

  ★ 매개변수는 넓은 쪽이 안전 (contravariant)
  ★ 반환 타입은 좁은 쪽이 안전 (covariant)
```

```text
  같은 뜻처럼 보이는 두 표기 — 검사가 다르다

  interface M { handle(a: Dog): void }       메서드 문법
  interface P { handle: (a: Dog) => void }   프로퍼티 문법

  MethodAnimal <- MethodDog    통과 ✓   ← bivariant (플래그 켜도)
  PropAnimal   <- PropDog      TS2322 ✗ ← contravariant
        │
        ▼  ★★★ strictFunctionTypes 는 프로퍼티 쪽에만 걸린다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **메서드와 프로퍼티가 정말 갈리나** — `strict` 를 켠 채로 던져 **한 줄만 갈리는 대조**를 받는다.
2. **플래그는 어디까지 걸리나** — 여덟 자리를 나란히 던져 **켜고 끈 두 판**을 글자 단위로 견준다.
3. **4.7 의 `in`/`out` 이 이 판에서 도나** — 외우지 않고 던진다. **메서드 문법이 `out` 을 빠져나가는 것**까지 본다.

★ [**16번 주제**](../16-function-types-and-overloads/)가 함수 타입 표기 세 꼴을 세웠다면 여기는 **그 꼴들이 대입에서 갈리는 지점**이다.
★★ [**16번 주제**](../16-function-types-and-overloads/)의 `.d.ts` 가 메서드와 프로퍼티를 **구별해 실은 이유**가 여기서 드러난다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **대입 한 줄 + 진단** | 그 방향이 허용되는지 | ★ 이 주제의 기본 도구 |
| ★★★ **같은 파일을 플래그 켜고 끄고** | 무엇이 **플래그에 달렸는지** | [**12번 주제**](../12-narrowing/)에서 이어받음 |
| ★ **방출 `.js` + `node` 실행** | **허용된 것이 안전하지 않은 것** | 4절 |

★★ 이 주제는 **탐침(`const x: null = …`)을 거의 안 쓴다.** 묻는 것이 「무슨 타입인가」가 아니라
「**이 대입이 되나**」이기 때문이다 — 진단의 유무가 곧 답이다.

비용 — 컴파일 두 번 + 실행 한 번.

### (1) ★★★ 메서드는 bivariant, 프로퍼티는 contravariant

**언제 쓰나** — 「콜백 타입을 느슨하게 적었는데 왜 통과하지」에서 막힐 때. **이 절이 이 주제의 본체다.**

```ts
// ex.17a.ts
// 메서드 문법은 bivariant, 프로퍼티 문법은 contravariant — strict 를 켠 채로 던진다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    bark(): void;
}

interface MethodDog {
    handle(a: Dog): void;
}
interface MethodAnimal {
    handle(a: Animal): void;
}
interface PropDog {
    handle: (a: Dog) => void;
}
interface PropAnimal {
    handle: (a: Animal) => void;
}

declare const methodDog: MethodDog;
declare const methodAnimal: MethodAnimal;
declare const propDog: PropDog;
declare const propAnimal: PropAnimal;

// ① 넓은 쪽을 좁은 쪽 자리에 — 안전한 방향(contravariance 가 허용한다)
const m1: MethodDog = methodAnimal;
const p1: PropDog = propAnimal;

// ② 좁은 쪽을 넓은 쪽 자리에 — 안전하지 않은 방향
const m2: MethodAnimal = methodDog;
const p2: PropAnimal = propDog;

// ③ 맨 함수 타입끼리도 같은 규칙
type FnDog = (a: Dog) => void;
type FnAnimal = (a: Animal) => void;
declare const fnDog: FnDog;
declare const fnAnimal: FnAnimal;
const f1: FnDog = fnAnimal;
const f2: FnAnimal = fnDog;
console.log(m1, p1, m2, p2, f1, f2);
```

```text
===== tsc --pretty false --noEmit ex.17a.ts (tsc exit=1) =====
ex.17a.ts(33,7): error TS2322: Type 'PropDog' is not assignable to type 'PropAnimal'.
  Types of property 'handle' are incompatible.
    Type '(a: Dog) => void' is not assignable to type '(a: Animal) => void'.
      Types of parameters 'a' and 'a' are incompatible.
        Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17a.ts(41,7): error TS2322: Type 'FnDog' is not assignable to type 'FnAnimal'.
  Types of parameters 'a' and 'a' are incompatible.
    Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
```

그림 해설 — 한 단계에 한 문장.

- 대입이 **여섯 개**인데 진단은 **두 건**이다 — 33행과 41행.
- 28·29행(넓은 쪽을 좁은 쪽 자리에) — 메서드도 프로퍼티도 **통과한다.** 이것이 **안전한 방향**이다.\
  `Dog` 를 받는 자리에 `Animal` 을 받는 함수를 넣으면, 들어오는 `Dog` 는 `Animal` 이기도 하니 문제없다.
- ★★★ 32행이 이 절의 별이다. **`MethodAnimal` 자리에 `MethodDog` 를 넣었는데 통과한다.**\
  「`Animal` 을 받겠다」고 약속한 자리에 「`Dog` 만 받는다」를 넣은 것이다 — **안전하지 않은 방향**인데 조용하다.
- ★★★ 33행이 그 대비다. **똑같은 방향인데 프로퍼티 문법이면 막힌다.**\
  `TS2322` 아래 네 줄이 이유를 끝까지 짚는다 — 「Property 'bark' is missing in type 'Animal' but required in type 'Dog'.」
- ★★ 41행 — 맨 함수 타입(`type FnDog = (a: Dog) => void`)도 **프로퍼티와 같다.** 막힌다.
- ★★★ 즉 **표기 꼴 하나가 검사의 엄격함을 가른다.** `handle(a: Dog): void` 와 `handle: (a: Dog) => void` 는\
  [**16번 주제**](../16-function-types-and-overloads/)의 `.d.ts` 에서 **구별돼 실렸는데**, 그 구별이 여기서 값을 낸다.

플래그를 끄면 어떻게 되나.

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17a.ts (tsc exit=0) =====
```

- ★★★ **진단이 0줄**이고 종료 코드가 **`0`** 이다. 여섯 대입이 **전부 통과**한다.
- ★★ 즉 `strictFunctionTypes` 가 하는 일은 「**프로퍼티·맨 함수 타입의 매개변수를 contravariant 로 검사한다**」 하나다.\
  ★★★ **메서드는 그 대상이 아니다** — 켜도 꺼도 통과한다(32행).

> **contravariance(반공변)** — 매개변수 자리는 **넓은 쪽**으로 바꿔도 안전하다는 규칙.\
> **bivariance(양공변)** — 양쪽 다 허용하는 것. **안전하지 않지만 TS 는 메서드에서 이것을 쓴다.**

비용 — 없음. 다만 **메서드로 적은 콜백은 검사가 느슨하다**는 것을 알고 써야 한다.

### (2) ★★★ `strictFunctionTypes` 의 범위 — 여덟 자리

**언제 쓰나** — 「플래그를 켰는데도 통과한다」거나 「껐는데도 막힌다」일 때.

```ts
// ex.17b.ts
// strictFunctionTypes 는 어디에 걸리고 어디에 안 걸리나 — 여덟 자리를 나란히 던진다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    bark(): void;
}

class MethodBoxDog {
    handle(a: Dog): void {}
}
class MethodBoxAnimal {
    handle(a: Animal): void {}
}
class PropBoxDog {
    handle: (a: Dog) => void = () => {};
}
class PropBoxAnimal {
    handle: (a: Animal) => void = () => {};
}
type CtorDog = new (a: Dog) => void;
type CtorAnimal = new (a: Animal) => void;
type RetDog = () => Dog;
type RetAnimal = () => Animal;
type TwoArgs = (a: Dog, b: Dog) => void;
type OneArg = (a: Dog) => void;

declare const methodBoxDog: MethodBoxDog;
declare const propBoxDog: PropBoxDog;
declare const ctorDog: CtorDog;
declare const retDog: RetDog;
declare const retAnimal: RetAnimal;
declare const oneArg: OneArg;
declare const twoArgs: TwoArgs;
declare const dogs: Dog[];

const s1: MethodBoxAnimal = methodBoxDog;
const s2: PropBoxAnimal = propBoxDog;
const s3: CtorAnimal = ctorDog;
const s4: RetAnimal = retDog;
const s5: RetDog = retAnimal;
const s6: TwoArgs = oneArg;
const s7: OneArg = twoArgs;
const s8: Animal[] = dogs;
console.log(s1, s2, s3, s4, s5, s6, s7, s8);
```

```text
===== tsc --pretty false --noEmit ex.17b.ts (tsc exit=1) =====
ex.17b.ts(38,7): error TS2322: Type 'PropBoxDog' is not assignable to type 'PropBoxAnimal'.
  Types of property 'handle' are incompatible.
    Type '(a: Dog) => void' is not assignable to type '(a: Animal) => void'.
      Types of parameters 'a' and 'a' are incompatible.
        Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17b.ts(39,7): error TS2322: Type 'CtorDog' is not assignable to type 'CtorAnimal'.
  Types of parameters 'a' and 'a' are incompatible.
    Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17b.ts(41,7): error TS2322: Type 'RetAnimal' is not assignable to type 'RetDog'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17b.ts(43,7): error TS2322: Type 'TwoArgs' is not assignable to type 'OneArg'.
  Target signature provides too few arguments. Expected 2 or more, but got 1.
```

같은 파일을 플래그만 끄고 다시 던진다.

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17b.ts (tsc exit=1) =====
ex.17b.ts(41,7): error TS2322: Type 'RetAnimal' is not assignable to type 'RetDog'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17b.ts(43,7): error TS2322: Type 'TwoArgs' is not assignable to type 'OneArg'.
  Target signature provides too few arguments. Expected 2 or more, but got 1.
```

그림 해설 — 한 단계에 한 문장.

- 기본값에서 **네 건**, 끄면 **두 건**이다. **사라지는 것은 38·39행**이고 **남는 것은 41·43행**이다.
- ★★★ 37행 `MethodBoxAnimal = methodBoxDog` — **클래스 메서드도 bivariant** 다. **양쪽 판 모두 조용**하다.
- ★★★ 38행 `PropBoxAnimal = propBoxDog` — **클래스 필드를 함수 타입으로 적으면** 걸린다. 끄면 사라진다.
- ★★ 39행 — **생성자 시그니처(`new (a: Dog) => void`)도 플래그의 대상**이다. 끄면 사라진다.
- ★★★ 41행 `RetDog = retAnimal` — **반환 타입은 covariant** 이고 **플래그와 무관**하다.\
  「`Dog` 를 준다」고 한 자리에 「`Animal` 을 준다」를 넣을 수는 없다. 양쪽 판에 그대로 남는다.
- ★★ 43행 — **매개변수 개수**도 플래그와 무관하다. 「Target signature provides too few arguments.」\
  ★ 반대로 42행(`TwoArgs = oneArg`, 인자를 **덜** 받는 함수)은 **조용하다.**
- ★★★ 44행 `Animal[] = dogs` — **배열은 covariant** 라 통과한다. 플래그와 무관하다 — 4절이 그 대가다.

```text
  strictFunctionTypes 의 범위 — 이 판에서 던진 여덟 자리

  걸린다 (끄면 사라진다)            안 걸린다 (양쪽 판 모두 같다)
  ─────────────────────             ─────────────────────────────
  프로퍼티 문법 필드   38행          클래스 메서드         37행  ✓ 통과
  생성자 시그니처      39행          반환 타입             41행  ✗ 막힘
                                     매개변수 개수 (많음)  43행  ✗ 막힘
                                     매개변수 개수 (적음)  42행  ✓ 통과
                                     배열의 covariance     44행  ✓ 통과
```

> **`strictFunctionTypes`** — 함수 **타입** 자리의 매개변수를 contravariant 로 검사하는 플래그(TS 2.6).\
> `strict` 에 딸려 7.0 기본 `true`. ★★★ **메서드 문법은 대상이 아니다.**

비용 — 없음. 다만 **끄면 이 주제의 절반이 조용해진다** — 켜고 쓰는 것이 기본이다.

### (3) ★★★ `in`/`out` 변성 표기가 이 판에서 돈다

**언제 쓰나** — 제네릭 인터페이스의 변성을 **손으로 못 박고 싶을 때**.

```ts
// ex.17c.ts
// in/out 변성 표기 (TS 4.7) 가 이 판에서 도나 — 그리고 메서드 문법이 out 을 빠져나간다
interface Producer<out T> {
    get(): T;
}
interface Consumer<in T> {
    set(v: T): void;
}
interface Invariant<in out T> {
    get(): T;
    set(v: T): void;
}
interface WrongOutMethod<out T> {
    set(v: T): void;
}
interface WrongOutProp<out T> {
    set: (v: T) => void;
}
interface WrongInMethod<in T> {
    get(): T;
}
type MyFn<in A, out R> = (a: A) => R;

declare const producerString: Producer<string>;
const p1: Producer<string | number> = producerString;
declare const consumerWide: Consumer<string | number>;
const c1: Consumer<string> = consumerWide;
declare const invariantString: Invariant<string>;
const i1: Invariant<string | number> = invariantString;
declare const fn: MyFn<string | number, string>;
const f1: MyFn<string, string | number> = fn;
console.log(p1, c1, i1, f1);
```

```text
===== tsc --pretty false --noEmit ex.17c.ts (tsc exit=1) =====
ex.17c.ts(15,24): error TS2636: Type 'WrongOutProp<sub-T>' is not assignable to type 'WrongOutProp<super-T>' as implied by variance annotation.
  Types of property 'set' are incompatible.
    Type '(v: sub-T) => void' is not assignable to type '(v: super-T) => void'.
      Types of parameters 'v' and 'v' are incompatible.
        Type 'super-T' is not assignable to type 'sub-T'.
ex.17c.ts(18,25): error TS2636: Type 'WrongInMethod<super-T>' is not assignable to type 'WrongInMethod<sub-T>' as implied by variance annotation.
  The types returned by 'get()' are incompatible between these types.
    Type 'super-T' is not assignable to type 'sub-T'.
ex.17c.ts(28,7): error TS2322: Type 'Invariant<string>' is not assignable to type 'Invariant<string | number>'.
  Type 'string | number' is not assignable to type 'string'.
    Type 'number' is not assignable to type 'string'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **4.7 의 `in`/`out` 표기가 7.0.2 에서 그대로 돈다.** 문법 오류가 하나도 없다.
- 진단이 **세 건**이고 코드는 **`TS2636` 둘 · `TS2322` 하나**다.
- 24·26행 — `Producer<out T>` 는 넓히는 방향이, `Consumer<in T>` 는 좁히는 방향이 통과한다. **표기대로다.**
- ★★★ 15행 — `WrongOutProp<out T> { set: (v: T) => void }` 가 **`TS2636`** 이다.\
  「…as implied by variance annotation.」 — **표기가 거짓말이면 선언 자리에서 막는다.**
- ★★★ **그런데 12행 `WrongOutMethod<out T> { set(v: T): void }` 는 조용하다.**\
  똑같이 `T` 를 **받는 자리**에만 썼는데 메서드 문법이면 통과한다 — **bivariance 가 `out` 을 만족시켜 버린다.**\
  1절의 결론이 **변성 표기 검사에까지 스며든 것**이다.
- ★★ 18행 — `WrongInMethod<in T> { get(): T }` 는 **메서드여도 걸린다.**\
  반환 자리는 bivariance 와 무관하기 때문이다(2절 41행과 같은 이유).
- ★ 28행 — `Invariant<in out T>` 는 **양방향 다 막는다.** 이것이 invariance 다.

플래그를 끄면 어떻게 되나.

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17c.ts (tsc exit=1) =====
ex.17c.ts(18,25): error TS2636: Type 'WrongInMethod<super-T>' is not assignable to type 'WrongInMethod<sub-T>' as implied by variance annotation.
  The types returned by 'get()' are incompatible between these types.
    Type 'super-T' is not assignable to type 'sub-T'.
ex.17c.ts(28,7): error TS2322: Type 'Invariant<string>' is not assignable to type 'Invariant<string | number>'.
  Type 'string | number' is not assignable to type 'string'.
    Type 'number' is not assignable to type 'string'.
```

- ★★★ **15행이 사라진다.** 변성 표기 검사도 **`strictFunctionTypes` 에 달려 있다** —\
  플래그를 끄면 프로퍼티 문법마저 bivariant 가 되어 `WrongOutProp` 의 거짓말이 **드러나지 않는다.**
- ★★ 18행과 28행은 남는다 — **반환 자리와 invariance 는 플래그와 무관**하다.

> **`in`/`out` 변성 표기** — 제네릭 매개변수 앞에 `in`(반공변)·`out`(공변)·`in out`(불변)을 적는 표기(TS 4.7).\
> **표기가 실제 쓰임과 어긋나면 `TS2636`** 으로 막는다. ★ 다만 **메서드 문법은 `out` 검사를 빠져나간다.**

비용 — 없음. 오히려 **변성을 계산하지 않고 표기대로 믿어 검사가 빨라지는** 쪽이 도입 동기였다.

### (4) ★★★ 배열이 covariant 라서 안전하지 않다 — 던져서 깨뜨린다

**언제 쓰나** — 「`Dog[]` 를 `Animal[]` 에 넣어도 되나」를 확인할 때.

```ts
// ex.17d.ts
// 배열이 covariant 라서 안전하지 않다 — 던져서 깨뜨린다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    name: string;
    bark(): void;
}

const dogs: Dog[] = [{ name: "바둑", bark: () => console.log("멍") }];
const animals: Animal[] = dogs;
animals.push({ name: "나비" });

const readonlyAnimals: readonly Animal[] = dogs;

function barkAll(): string {
    for (const d of dogs) {
        d.bark();
    }
    return "전부 짖었다";
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}
console.log("dogs.length         :", dogs.length);
console.log("readonlyAnimals[1]  :", JSON.stringify(readonlyAnimals[1]));
run("barkAll()           :", barkAll);
```

```text
===== tsc --pretty false ex.17d.ts (tsc exit=0) =====
===== 방출된 ex.17d.js =====
"use strict";
const dogs = [{ name: "바둑", bark: () => console.log("멍") }];
const animals = dogs;
animals.push({ name: "나비" });
const readonlyAnimals = dogs;
function barkAll() {
    for (const d of dogs) {
        d.bark();
    }
    return "전부 짖었다";
}
function run(label, f) {
    try {
        console.log(label, f());
    }
    catch (e) {
        console.log(label, "터졌다 ->", e.message);
    }
}
console.log("dogs.length         :", dogs.length);
console.log("readonlyAnimals[1]  :", JSON.stringify(readonlyAnimals[1]));
run("barkAll()           :", barkAll);
```

```text
===== node ex.17d.js (node exit=0) =====
dogs.length         : 2
readonlyAnimals[1]  : {"name":"나비"}
멍
barkAll()           : 터졌다 -> d.bark is not a function
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단이 한 줄도 없다. 종료 코드가 `0` 이다.** 그런데 **런타임에 터진다.**
- `const animals: Animal[] = dogs;` 가 통과한다 — **배열은 covariant** 다(2절 44행).
- ★★★ 그다음 줄 `animals.push({ name: "나비" })` 도 통과한다. **`Animal` 배열이니 `Animal` 을 넣는 것은 당연**하다.\
  그런데 그 배열은 **실제로는 `dogs`** 다.
- ★★ `dogs.length` 가 **`2`** 다 — `Dog[]` 라고 선언한 배열에 **`bark` 가 없는 물건**이 들어갔다.
- ★★★ `barkAll()` 이 **터진다** — 「`d.bark is not a function`」. 첫 원소는 `멍` 을 찍고 **둘째에서 죽는다.**
- ★★ `readonly Animal[]` 로 받아도 **`readonlyAnimals[1]` 은 `{"name":"나비"}`** 다 —\
  `readonly` 는 **그 참조로 넣는 것만** 막지 **다른 참조가 넣는 것은 못 막는다.**
- ★ 방출된 `.js` 에는 타입이 한 글자도 없다. `const animals = dogs;` 라는 **JS 대입만** 남는다.

```text
  컴파일 시각                           런타임
  ─────────────────────────────────────────────────────────────
  const animals: Animal[] = dogs;       같은 배열을 가리킨다
  animals.push({ name: "나비" });       Dog[] 에 bark 없는 물건이 들어간다
        │                                     │
        ▼                                     ▼
  둘 다 타입상 옳다                     dogs.length === 2
  tsc exit 0 · 진단 0건                 d.bark is not a function
```

> **배열의 covariance** — `Dog[]` 를 `Animal[]` 에 대입할 수 있다. **안전하지 않다** —\
> `push` 가 메서드 문법이라 **bivariance 로 통과**하기 때문이다(5절).

비용 — ★★★ **타입 검사가 잡아 주지 않는 버그가 여기 산다.** 넣는 쪽을 줄 자리에는 `readonly T[]` 를 쓴다.

### (5) ★★ 왜 메서드를 bivariant 로 남겼나 — 손으로 쓴 배열 셋

**언제 쓰나** — 「불안전한 줄 알면서 왜 안 고쳤나」가 궁금할 때.

```ts
// ex.17e.ts
// 왜 메서드를 bivariant 로 남겼나 — 손으로 쓴 배열 두 꼴을 나란히 던진다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    name: string;
    bark(): void;
}

interface MyArrayMethod<T> {
    push(v: T): void;
    at(i: number): T;
}
interface MyArrayProp<T> {
    push: (v: T) => void;
    at: (i: number) => T;
}
interface MyArrayAnnotated<in out T> {
    push(v: T): void;
    at(i: number): T;
}

declare const md: MyArrayMethod<Dog>;
declare const pd: MyArrayProp<Dog>;
declare const ad: MyArrayAnnotated<Dog>;
const m1: MyArrayMethod<Animal> = md;
const p1: MyArrayProp<Animal> = pd;
const a1: MyArrayAnnotated<Animal> = ad;

// 표준 배열도 메서드 문법이라 같은 자리에서 통과한다
declare const dogs: Dog[];
const std: Animal[] = dogs;
const ro: readonly Animal[] = dogs;
declare const roDogs: readonly Dog[];
const roBack: Dog[] = roDogs;

// 콜백 매개변수가 느슨해도 통과하는 이유
declare function each<T>(xs: T[], f: (v: T) => void): void;
declare const takesAnimal: (a: Animal) => void;
each(dogs, takesAnimal);
console.log(m1, p1, a1, std, ro, roBack);
```

```text
===== tsc --pretty false --noEmit ex.17e.ts (tsc exit=1) =====
ex.17e.ts(27,7): error TS2322: Type 'MyArrayProp<Dog>' is not assignable to type 'MyArrayProp<Animal>'.
  Types of property 'push' are incompatible.
    Type '(v: Dog) => void' is not assignable to type '(v: Animal) => void'.
      Types of parameters 'v' and 'v' are incompatible.
        Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17e.ts(28,7): error TS2322: Type 'MyArrayAnnotated<Dog>' is not assignable to type 'MyArrayAnnotated<Animal>'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17e.ts(35,7): error TS4104: The type 'readonly Dog[]' is 'readonly' and cannot be assigned to the mutable type 'Dog[]'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 27·28·35행.
- ★★★ 26행 `MyArrayMethod<Animal> = md` 가 **통과한다.** `push(v: T)` 가 **메서드 문법**이기 때문이다.
- ★★★ 27행 `MyArrayProp<Animal> = pd` 는 **막힌다.** 똑같은 인터페이스를 **프로퍼티 문법**으로 적었을 뿐이다.
- ★★★ 이 둘의 대비가 **답 자체**다. 표준 `Array<T>` 의 `push`·`concat`·`indexOf` 가 전부 **메서드 문법**이라,\
  **메서드를 contravariant 로 바꾸면 `Dog[]` 를 `Animal[]` 에 넣는 것이 전부 에러가 된다.**\
  그 코드가 세상에 너무 많아서 TS 는 **메서드를 예외로 남겼다.**
- ★★ 28행 — `MyArrayAnnotated<in out T>` 는 **막힌다.** 변성 표기를 붙이면 **메서드여도 invariant 로 못 박힌다** —\
  3절의 `WrongOutMethod` 와 달리 `in out` 은 빠져나갈 구멍이 없다.
- ★★ 32·33행 — 표준 `Dog[]` 를 `Animal[]` 에도, `readonly Animal[]` 에도 넣을 수 있다.
- ★★★ 35행 — 반대 방향은 막힌다. **`TS4104`** — 「The type 'readonly Dog[]' is 'readonly' and cannot be assigned to the mutable type 'Dog[]'.」
- ★ 40행 `each(dogs, takesAnimal)` 이 조용한 것이 **실무에서 가장 흔한 자리**다.\
  콜백 매개변수를 느슨하게 적어도 통과하는 이유가 여기 있다.

플래그를 끄면 어떻게 되나.

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17e.ts (tsc exit=1) =====
ex.17e.ts(28,7): error TS2322: Type 'MyArrayAnnotated<Dog>' is not assignable to type 'MyArrayAnnotated<Animal>'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17e.ts(35,7): error TS4104: The type 'readonly Dog[]' is 'readonly' and cannot be assigned to the mutable type 'Dog[]'.
```

- ★★ **27행이 사라진다.** 프로퍼티 문법마저 bivariant 가 되기 때문이다.
- ★ 28행(`in out`)과 35행(`readonly`)은 **남는다** — 둘 다 플래그와 무관한 규칙이다.

### (6) ★ 네 파일 전부 플래그에서 갈린다

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.17a.ts    exit 1 / exit 0 · ★ 다르다
ex.17b.ts    exit 1 / exit 1 · ★ 다르다
ex.17c.ts    exit 1 / exit 1 · ★ 다르다
ex.17e.ts    exit 1 / exit 1 · ★ 다르다
```

- ★★ 네 파일 **전부** `--strict false` 에서 갈린다. **이 주제는 플래그가 곧 주제**다.
- ★ `ex.17a.ts` 는 종료 코드까지 갈린다(`1` → `0`). 나머지 셋은 **일부 줄만** 사라진다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  interface M { handle(a: Dog): void }        ★ 메서드 문법  — bivariant
  interface P { handle: (a: Dog) => void }    ★ 프로퍼티 문법 — contravariant
  type F = (a: Dog) => void                   ★ 맨 함수 타입 — contravariant
  type C = new (a: Dog) => void               ★ 생성자 시그니처 — contravariant

  interface Producer<out T> { get(): T }      ★ 변성 표기 (4.7)
  interface Consumer<in T>  { set(v: T): void }
  interface Inv<in out T>   { get(): T; set(v: T): void }
  const ro: readonly Animal[] = dogs          ★ 넣는 것만 막는다
```

**규칙 불릿**

- ★★★ **매개변수는 contravariant, 반환 타입은 covariant** 가 안전한 규칙이다(2절 41행).
- ★★★ **메서드 문법만 bivariant** 다 — `strictFunctionTypes` 를 **켜도 그렇다**(1절 32행 · 2절 37행).
- ★★ **`strictFunctionTypes` 가 걸리는 것**은 프로퍼티 문법 · 맨 함수 타입 · **생성자 시그니처**다(2절 38·39행).
- ★★ **안 걸리는 것**은 메서드 문법 · 반환 타입 · 매개변수 개수 · 배열의 covariance 다(2절 37·41·43·44행).
- ★★★ **`in`/`out` 변성 표기가 이 판에서 돈다**(3절). 표기가 거짓말이면 **선언 자리에서 `TS2636`**.
- ★★ **메서드 문법은 `out` 검사를 빠져나간다**(3절 12행). `in out` 은 못 빠져나간다(5절 28행).
- ★★ **변성 표기 검사도 `strictFunctionTypes` 에 달려 있다**(3절 — 끄면 15행이 사라진다).
- ★★★ **배열은 covariant 라 안전하지 않다**(4절). `readonly T[]` 는 **그 참조로 넣는 것만** 막는다.
- ★ **인자를 덜 받는 함수는 넣을 수 있고**(2절 42행) **더 받는 함수는 못 넣는다**(43행).

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 좁은 매개변수를 넓은 자리에 (프로퍼티)  ->  TS2322  Types of parameters 'a' and 'a' are incompatible.
2) 넓은 반환을 좁은 자리에                 ->  TS2322  Property 'bark' is missing in type 'Animal' …
3) 변성 표기가 실제와 어긋남               ->  TS2636  … as implied by variance annotation.
4) readonly 배열을 가변 배열에             ->  TS4104  The type 'readonly Dog[]' is 'readonly' and cannot
                                                       be assigned to the mutable type 'Dog[]'.
```

## 어디서 틀리나

- ★★★ 「**`strictFunctionTypes` 를 켰으니 매개변수가 다 엄해졌겠지**」 — **메서드는 그대로다**(1절 32행 · 2절 37행).
- ★★★ 「**메서드 문법과 프로퍼티 문법은 같은 말이겠지**」 — **검사가 다르다.** [**16번 주제**](../16-function-types-and-overloads/)의 `.d.ts` 가 구별해 싣는 이유다.
- ★★ 「**`Dog[]` 를 `Animal[]` 에 넣는 건 안전하겠지**」 — **안 안전하다**(4절). 런타임에 터진다.
- ★★ 「**`readonly T[]` 로 받으면 안전하겠지**」 — **그 참조로 넣는 것만** 막는다(4절 `readonlyAnimals[1]`).
- ★★ 「**`out` 을 붙이면 잘못 쓴 걸 잡아 주겠지**」 — **메서드 문법이면 못 잡는다**(3절 12행).
- ★★ 「**반환 타입도 플래그를 끄면 느슨해지겠지**」 — **안 바뀐다**(2절 41행).
- ★ 「**생성자 시그니처는 메서드 같은 거겠지**」 — **플래그의 대상**이다(2절 39행).
- ★ 「**인자 개수가 다르면 무조건 에러겠지**」 — **덜 받는 쪽은 통과**한다(2절 42행).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 반환 타입은 **covariant** — 플래그와 무관 | 2절 41행 |
| **언어 보장** | 매개변수 **개수** 규칙 — 플래그와 무관 | 2절 42·43행 |
| **언어 보장** | ★★★ **메서드 문법은 bivariant** — 켜도 그렇다 | 1절 32행 · 2절 37행 · 5절 26행 |
| **언어 보장** | **`in`/`out` 표기**가 거짓말이면 `TS2636` | 3절 15·18행 |
| **언어 보장** | `readonly T[]` 를 가변 배열에 못 넣는다 | 5절 35행 `TS4104` |
| **방출된 JS** | ★★★ 변성은 **한 글자도 안 남는다** | 4절 방출 전문 — `const animals = dogs;` 만 남는다 |
| **방출된 JS** | ★ 허용된 대입을 지켜 주는 장치가 **없다** | 4절 실행 출력 — `d.bark is not a function` |
| **★ 설정에 달림** | ★★★ **프로퍼티·맨 함수 타입·생성자 시그니처의 매개변수 검사** | `strictFunctionTypes`. **네 파일 전부 양쪽 판을 실었다** |
| **★ 설정에 달림** | ★★ **변성 표기 검사의 일부**(3절 15행) | 같은 플래그. 끄면 프로퍼티도 bivariant 가 된다 |
| **이 판(7.0.2)의 관찰** | ★★★ **4.7 의 `in`/`out` 이 도는 것** | 3절. **외우지 말고 다시 던져라** |
| **이 판의 관찰** | `TS2636` 의 `sub-T`·`super-T` 라는 가상 이름 | 보고기의 표기다 |
| **이 판의 관찰** | 진단 문구 전문과 **들여쓴 설명 줄의 깊이** | 코드가 더 오래 간다 |
| **안 잰 것** | 변성 계산의 **검사 시간** | 재지 않았다 |

★★★ 「**진단 0건」이 근거인 블록이 둘**이다 — 1절의 `--strictFunctionTypes false` 판과 4절의 `tsc`.
그 블록들도 **명령과 종료 코드까지** 캡처했다.
★ **설정에 달린 칸은 네 파일 전부**다 — 이 갈래에서 가장 많다. **이 주제는 플래그가 곧 주제**이기 때문이다.

## 언제 쓰고 언제 안 쓰나

| 이렇게 쓴다 | 이렇게 안 쓴다 |
|---|---|
| 콜백을 받는 자리는 **프로퍼티 문법**으로 — 검사가 엄해진다 | 메서드 문법으로 적어 두고 「엄하게 검사되겠지」 |
| 넣는 쪽을 줄 자리에는 **`readonly T[]`** | 가변 배열을 그대로 건네고 covariance 를 믿는 것 |
| 제네릭 컨테이너에는 **`in`/`out` 표기** — 의도를 못 박는다 | 표기를 붙이고 **메서드 문법으로 적는 것**(3절 12행) |
| `strictFunctionTypes` 는 **켜 둔다**(7.0 기본) | 에러를 없애려고 끄는 것 — 이 주제의 절반이 조용해진다 |
| 진짜 불변이 필요하면 **`in out`** | `readonly` 하나로 다 막았다고 믿는 것(4절) |

## 핵심 문장

1. **매개변수는 contravariant, 반환 타입은 covariant** 가 안전한 규칙이다.
2. **메서드 문법만 bivariant 다** — `strictFunctionTypes` 를 켜도 그렇다.
3. **플래그가 걸리는 것**은 프로퍼티 문법·맨 함수 타입·생성자 시그니처뿐이다.
4. **`in`/`out` 변성 표기가 이 판에서 돈다** — 다만 메서드 문법은 `out` 검사를 빠져나간다.
5. **배열은 covariant 라 안전하지 않다** — 컴파일 통과하고 런타임에 터진다.
6. **`readonly T[]` 는 그 참조로 넣는 것만 막는다** — 다른 참조가 넣는 것은 못 막는다.

## 관련 자료

- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — 세 꼴의 표기와 `.d.ts` 가 둘을 구별해 싣는 것은 그쪽. **16 → 17 은 한 사슬**이다.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — `readonly` 가 런타임을 막지 않는다는 것은 그쪽이 정본이다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 「넓다·좁다」의 기준인 할당 가능성은 그쪽.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — `Dog` 가 `Animal` 인 이유는 이름이 아니라 모양이다.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 반환 타입 `void` 가 변성에서 특별한 것은 그쪽과 함께 읽는다.
- [**15번 주제** — 제어 흐름 분석의 한계](../15-control-flow-analysis-limits/) — 4절과 같은 종류의 「컴파일은 통과하는데 런타임이 터진다」가 그쪽에도 있다.
- [목록의 **19번 주제**](../19-generics-basics/)(제네릭 기본)·**20번 주제**(제네릭 제약) — 3절의 `in`/`out` 은 제네릭 위에 선다.
- 목록의 **46번 주제**(가변 튜플 타입) — 배열의 변성과 이어지는 자리. **이 배치에서는 안 던졌다.**
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **15번** — `Dog` 가 `Animal` 을 상속하는 런타임 구조는 그쪽이 정본이다.

## 용어 풀이

> **공변(covariance)** — `Dog` 가 `Animal` 이면 `F<Dog>` 도 `F<Animal>` 인 관계.\
> **반환 타입**과 **배열**이 이쪽이다.

> **반공변(contravariance)** — `Dog` 가 `Animal` 이면 `F<Animal>` 이 `F<Dog>` 인 관계(방향이 뒤집힌다).\
> **매개변수**가 이쪽이고, 그것이 **안전한 규칙**이다.

> **양공변(bivariance)** — 양쪽 방향을 다 허용하는 것. **안전하지 않다.**\
> TS 는 **메서드 문법**에서 이것을 쓴다 — `strictFunctionTypes` 를 켜도 그렇다.

> **불변(invariance)** — 어느 방향도 허용하지 않는 것. `in out` 표기가 이것을 만든다.

> **`strictFunctionTypes`** — 함수 **타입** 자리의 매개변수를 contravariant 로 검사하는 플래그(TS 2.6).\
> `strict` 에 딸려 7.0 기본 `true`. **메서드 문법은 대상이 아니다.**

## 더 들어가면

- **왜 메서드를 안 고쳤나** — 5절이 답이다. 표준 `Array<T>` 의 `push`·`concat` 이 전부 메서드 문법이라, 메서드를 contravariant 로 바꾸면 **`Dog[]` 를 `Animal[]` 에 넣는 코드가 전부 에러**가 된다. 그런 코드가 세상에 너무 많아서 TS 2.6 은 **함수 타입만 고치고 메서드는 남겼다.** 「안전보다 호환」을 고른 자리이고, 4절이 그 대가를 실물로 보여 준다.
- **왜 매개변수가 contravariant 여야 하나** — 「`Animal` 을 받겠다」고 약속한 자리에 「`Dog` 만 받는다」를 넣으면, 그 자리에 고양이가 들어오는 순간 깨진다. 1절 33행의 진단이 그 문장을 그대로 말한다 — 「Property 'bark' is missing in type 'Animal' but required in type 'Dog'.」 **받는 쪽은 넓을수록 안전하다.**
- **`readonly` 와 `in out` 의 분업** — `readonly T[]` 는 **그 참조로 넣는 것**을 막고, `in out` 표기는 **타입 자체의 대입 방향**을 막는다. 4절에서 `readonlyAnimals[1]` 이 이미 오염돼 있던 것이 전자의 한계이고, 5절 28행이 후자가 막는 자리다. **둘은 다른 문제를 푼다.**
- **변성 표기의 원래 동기** — 4.7 의 `in`/`out` 은 안전보다 **성능**이 동기였다. 컴파일러가 구조를 훑어 변성을 계산하는 대신 **표기를 믿는다.** 그래서 표기가 거짓말이면 `TS2636` 으로 막는다 — 3절이 그 검사다. **깊은 제네릭 구조에서 검사 시간이 줄어든다고 알려져 있으나 이 배치에서는 재지 않았다.**
- **판이 오르면** — 3절의 「메서드 문법이 `out` 을 빠져나간다」는 **이 판의 관찰**이다. 1절의 메서드 bivariance 는 오래된 설계라 잘 안 바뀌겠지만, **외우지 말고 다시 던져라.** 이 문서가 파일 다섯을 남겨 둔 이유다.
