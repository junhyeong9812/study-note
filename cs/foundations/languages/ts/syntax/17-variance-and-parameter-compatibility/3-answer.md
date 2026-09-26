# ts/syntax/17 — 변성과 매개변수 양립성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 1번의 둘째 블록과 4번은 **진단이 0줄인 것이 답**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **2건** — 메서드는 통과하고 프로퍼티만 막힌다

**출력**

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

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17a.ts (tsc exit=0) =====
```

**왜 그런가**

| 줄 | 대입 | 결과 |
|---|---|---|
| 28 | `MethodDog <- methodAnimal` — 넓은 쪽을 좁은 자리에 | ✓ 통과 — **안전한 방향** |
| 29 | `PropDog <- propAnimal` | ✓ 통과 — 같은 이유 |
| 32 | ★★★ `MethodAnimal <- methodDog` — 좁은 쪽을 넓은 자리에 | ★★★ **통과** — bivariance |
| 33 | ★★★ `PropAnimal <- propDog` — 같은 방향 | **TS2322** |
| 40 | `FnDog <- fnAnimal` | ✓ 통과 |
| 41 | `FnAnimal <- fnDog` | **TS2322** — 맨 함수 타입도 프로퍼티와 같다 |

- ★★★ 32행과 33행이 **이 주제의 전부**다. 두 대입은 **방향도 타입도 같다.**\
  다른 것은 인터페이스 안에 `handle(a: Dog): void` 로 적었나 `handle: (a: Dog) => void` 로 적었나 **하나뿐**이다.
- ★★★ 그런데 `strict` 가 켜져 있는데도 **메서드 쪽은 조용하다.** 이것이 **method bivariance** 다.\
  「`Animal` 을 받겠다」고 약속한 자리에 「`Dog` 만 받는다」가 들어갔는데 아무도 안 막는다.
- ★★ 33행의 진단이 **왜 위험한지**를 네 줄로 끝까지 짚는다 —\
  「Types of parameters 'a' and 'a' are incompatible.」 → 「Property 'bark' is missing in type 'Animal' but required in type 'Dog'.」\
  즉 **`Animal` 이 들어오면 `bark` 가 없다.**
- ★★★ 플래그를 끈 판은 **진단이 0줄**이고 종료 코드가 **`0`** 이다. 여섯 대입이 전부 통과한다.\
  그러므로 `strictFunctionTypes` 가 하는 일은 「**프로퍼티·맨 함수 타입의 매개변수를 contravariant 로 검사**」 하나이고,\
  ★★★ **메서드는 켜도 꺼도 통과**한다.

### 2. ★★★ 기본값 **4건** · 끄면 **2건** — 사라지는 것은 **38·39행**

**출력**

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

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17b.ts (tsc exit=1) =====
ex.17b.ts(41,7): error TS2322: Type 'RetAnimal' is not assignable to type 'RetDog'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17b.ts(43,7): error TS2322: Type 'TwoArgs' is not assignable to type 'OneArg'.
  Target signature provides too few arguments. Expected 2 or more, but got 1.
```

**왜 그런가**

| 줄 | 자리 | 기본값 | 끈 판 |
|---|---|---|---|
| 37 | ★★★ 클래스 **메서드** | ✓ 통과 | ✓ 통과 |
| 38 | 클래스 **필드를 함수 타입으로** | **TS2322** | ★ 사라진다 |
| 39 | ★★ **생성자 시그니처** | **TS2322** | ★ 사라진다 |
| 40 | 반환 타입 — 좁은 쪽을 넓은 자리에 | ✓ 통과 | ✓ 통과 |
| 41 | ★★★ 반환 타입 — 넓은 쪽을 좁은 자리에 | **TS2322** | ★ **남는다** |
| 42 | 매개변수를 **덜** 받는 함수 | ✓ 통과 | ✓ 통과 |
| 43 | 매개변수를 **더** 받는 함수 | **TS2322** | ★ **남는다** |
| 44 | ★★ 배열 `Animal[] <- Dog[]` | ✓ 통과 | ✓ 통과 |

- ★★★ 37행이 1번의 결론을 **클래스에서도** 확인한다. **클래스 메서드도 bivariant** 다.
- ★★ 39행이 덜 알려진 자리다. **생성자 시그니처(`new (a: Dog) => void`)도 플래그의 대상**이다 —\
  「함수 타입 자리」에 포함된다.
- ★★★ 41행과 43행이 **플래그와 무관하게 남는다.** 그 둘은 `strictFunctionTypes` 가 건드리는 규칙이 아니다 —\
  **반환 타입의 covariance** 와 **매개변수 개수**는 언제나 검사된다.
- ★★ 42행이 통과하는 것도 중요하다. 인자를 **덜** 받는 함수는 넣을 수 있다 —\
  JS 에서 남는 인자를 무시하는 것이 정상이기 때문이다.
- ★★★ 44행 `Animal[] <- Dog[]` 가 **양쪽 판 모두 통과**한다. **배열은 covariant** 이고 플래그와 무관하다 —\
  4번이 그 대가를 던진다.

### 3. ★★★ 진단 **3건** — **돈다.** 그리고 메서드 문법이 `out` 을 빠져나간다

**출력**

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

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17c.ts (tsc exit=1) =====
ex.17c.ts(18,25): error TS2636: Type 'WrongInMethod<super-T>' is not assignable to type 'WrongInMethod<sub-T>' as implied by variance annotation.
  The types returned by 'get()' are incompatible between these types.
    Type 'super-T' is not assignable to type 'sub-T'.
ex.17c.ts(28,7): error TS2322: Type 'Invariant<string>' is not assignable to type 'Invariant<string | number>'.
  Type 'string | number' is not assignable to type 'string'.
    Type 'number' is not assignable to type 'string'.
```

**왜 그런가**

| 줄 | 선언 | 결과 |
|---|---|---|
| 2 / 5 / 8 | `Producer<out T>` · `Consumer<in T>` · `Invariant<in out T>` | ✓ 문법 오류 없음 — **4.7 표기가 돈다** |
| 12 | ★★★ `WrongOutMethod<out T> { set(v: T): void }` | ★★★ **조용하다** |
| 15 | `WrongOutProp<out T> { set: (v: T) => void }` | **TS2636** |
| 18 | `WrongInMethod<in T> { get(): T }` | **TS2636** — 메서드여도 걸린다 |
| 21 | `type MyFn<in A, out R> = (a: A) => R` | ✓ 통과 — 타입 별칭에도 쓸 수 있다 |
| 24 / 26 | `Producer` 넓히기 / `Consumer` 좁히기 | ✓ 표기대로 통과 |
| 28 | `Invariant<string \| number> <- Invariant<string>` | **TS2322** — invariance |

- ★★★ **4.7 의 `in`/`out` 변성 표기가 7.0.2 에서 그대로 돈다.** 문법 오류가 하나도 없고,\
  표기가 실제 쓰임과 어긋나면 **선언 자리에서** `TS2636` 으로 막는다 —\
  「…as implied by variance annotation.」
- ★★★ 12행과 15행의 대비가 이 번의 별이다. 두 인터페이스는 **`T` 를 받는 자리에만 쓴다**는 점에서 같다.\
  `out`(공변) 표기는 거짓말인데, **메서드 문법이면 그 거짓말이 안 드러난다.**\
  **bivariance 가 `out` 검사를 만족시켜 버리기** 때문이다 — 1번의 결론이 **변성 표기 검사에까지 스민다.**
- ★★ 18행은 메서드인데도 걸린다. **반환 자리는 bivariance 와 무관**하기 때문이다(2번 41행과 같은 이유).
- ★★★ 플래그를 끈 판에서 **15행이 사라진다.** 변성 표기 검사도 **`strictFunctionTypes` 에 달려 있다** —\
  끄면 프로퍼티 문법마저 bivariant 가 되어 거짓말이 드러날 자리가 없어진다.
- ★ 18행과 28행은 남는다 — **반환 자리와 invariance 는 플래그와 무관**하다.

### 4. ★★★ **진단 0건 · `tsc exit 0`** — 그리고 `d.bark is not a function` 으로 터진다

**출력**

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

**왜 그런가**

| 줄 | 출력 | 왜 |
|---|---|---|
| `dogs.length` | **`2`** | `Dog[]` 인데 **`bark` 없는 물건**이 들어갔다 |
| `readonlyAnimals[1]` | **`{"name":"나비"}`** | ★★ `readonly` 로 받아도 **이미 오염돼 있다** |
| (첫 원소) | `멍` | 진짜 `Dog` 라 짖는다 |
| `barkAll()` | 터졌다 → `d.bark is not a function` | 둘째 원소에서 죽는다 |

- ★★★ **`tsc` 종료 코드가 `0` 이고 진단이 한 줄도 없다.** 두 줄 다 타입상 옳다 —\
  `const animals: Animal[] = dogs;`(배열은 covariant) 와 `animals.push({ name: "나비" })`(`Animal` 배열에 `Animal`).
- ★★★ 그런데 두 줄을 이으면 **`Dog[]` 에 `Dog` 가 아닌 것이 들어간다.** 각각은 옳은데 **합이 틀렸다.**
- ★★ `readonly Animal[]` 이 막는 것과 못 막는 것을 가르자 —\
  ★ **막는다**: `readonlyAnimals.push(…)` 같은 **그 참조를 통한 변경**.\
  ★★★ **못 막는다**: **다른 참조(`animals`)가 같은 배열을 바꾸는 것**. `readonlyAnimals[1]` 이 이미 `나비` 다.
- ★★ 즉 `readonly` 는 **이 창구로는 못 넣는다**는 표기이지 **아무도 못 넣는다**는 보장이 아니다\
  ([**07번 주제**](../07-object-type-details/)).
- ★ 방출된 `.js` 에는 타입이 한 글자도 없다. `const animals = dogs;` 라는 **JS 대입만** 남는다 —\
  **변성을 지켜 주는 장치는 런타임 어디에도 없다.**

### 5. ★★★ 진단 **3건** — 같은 인터페이스를 **문법만 바꿔 적었더니** 갈린다

**출력**

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

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.17e.ts (tsc exit=1) =====
ex.17e.ts(28,7): error TS2322: Type 'MyArrayAnnotated<Dog>' is not assignable to type 'MyArrayAnnotated<Animal>'.
  Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.17e.ts(35,7): error TS4104: The type 'readonly Dog[]' is 'readonly' and cannot be assigned to the mutable type 'Dog[]'.
```

**왜 그런가**

| 줄 | 선언 | 기본값 | 끈 판 |
|---|---|---|---|
| 26 | ★★★ `MyArrayMethod<Animal> <- md` — **메서드 문법** | ✓ **통과** | ✓ 통과 |
| 27 | `MyArrayProp<Animal> <- pd` — **프로퍼티 문법** | **TS2322** | ★ 사라진다 |
| 28 | ★★ `MyArrayAnnotated<Animal> <- ad` — **`in out` 표기** | **TS2322** | ★ **남는다** |
| 32 / 33 | 표준 `Dog[]` 를 `Animal[]` / `readonly Animal[]` 에 | ✓ 통과 | ✓ 통과 |
| 35 | `Dog[] <- readonly Dog[]` | **TS4104** | ★ **남는다** |
| 40 | `each(dogs, takesAnimal)` — 느슨한 콜백 | ✓ 통과 | ✓ 통과 |

- ★★★ 26행과 27행이 **「왜 안 고쳤나」의 답**이다. 두 인터페이스는 **`push` 와 `at` 의 적는 꼴만** 다르다.\
  표준 `Array<T>` 의 메서드가 전부 메서드 문법이라, **메서드를 contravariant 로 바꾸면\
  `Dog[]` 를 `Animal[]` 에 넣는 코드가 전부 에러**가 된다. 그런 코드가 너무 많아서 TS 는 **호환을 골랐다.**
- ★★★ 28행이 **막을 수 있는 길**을 보여 준다. `in out` 표기를 붙이면 **메서드여도 invariant 로 못 박힌다** —\
  3번의 `WrongOutMethod` 와 달리 `in out` 은 빠져나갈 구멍이 없다. 플래그를 꺼도 남는다.
- ★★ 35행 — `readonly Dog[]` 를 가변 `Dog[]` 에 넣는 것은 **`TS4104`** 로 막힌다.\
  전용 코드가 따로 있을 만큼 흔한 실수다. 이것도 플래그와 무관하다.
- ★★★ 40행이 **실무에서 가장 흔한 자리**다. `each(dogs, takesAnimal)` 처럼 콜백 매개변수를 느슨하게 적어도\
  통과하는 이유가 여기 있다 — 배열의 covariance 와 메서드의 bivariance 가 **함께** 통과시킨다.
- ★ 끈 판에서 **27행만** 사라진다. 28·35행은 남는다 — **`in out` 과 `readonly` 는 플래그와 무관**하다.

### 6. ★★ 네 방향과 실측 자리

| 방향 | 뜻 | 이 주제의 자리 |
|---|---|---|
| **covariant**(공변) | `Dog` → `Animal` 방향으로만 | 반환 타입(2번 40·41행) · **배열**(2번 44행 · 4번) · `Producer<out T>`(3번 24행) |
| **contravariant**(반공변) | `Animal` → `Dog` 방향으로만 | 프로퍼티 문법 매개변수(1번 33행) · 맨 함수 타입(1번 41행) · 생성자 시그니처(2번 39행) · `Consumer<in T>`(3번 26행) |
| **bivariant**(양공변) | ★ **양쪽 다** | ★★★ **메서드 문법 매개변수**(1번 32행 · 2번 37행 · 5번 26행) |
| **invariant**(불변) | ★ **어느 쪽도 안 됨** | `Invariant<in out T>`(3번 28행) · `MyArrayAnnotated<in out T>`(5번 28행) |

- ★★★ 안전한 규칙은 **covariant(주는 자리) + contravariant(받는 자리)** 둘이다.\
  **bivariant 는 안전하지 않고**, TS 는 그것을 **메서드에서 일부러** 쓴다.
- ★★ **invariant 는 가장 엄하지만 가장 불편하다.** 그래서 기본값이 아니라 **표기로 고르는 것**이다.
- ★ 「넓다·좁다」의 기준은 **할당 가능성**이고, 그것은 이름이 아니라 **모양**으로 정해진다([**05번 주제**](../05-structural-typing/)).

### 7. ★★★ **좁게 받는 함수를 넓게 받는 자리에 두면 감당 못 할 값이 들어오기** 때문이다

**왜 그런가**

- 1번 33행의 진단이 그 문장을 그대로 말한다 —\
  「Types of parameters 'a' and 'a' are incompatible.」 → 「Property 'bark' is missing in type 'Animal' but required in type 'Dog'.」
- ★★ 읽으면 이렇다. `PropAnimal.handle` 은 **`Animal` 을 받겠다**고 약속했다.\
  거기에 `propDog.handle`(`Dog` 만 받는다)을 넣으면, **고양이가 들어오는 순간** `a.bark()` 가 없다.
- ★★★ 반대 방향(28·29행)은 안전하다. **`Animal` 을 받는 함수는 `Dog` 가 들어와도 감당**한다 —\
  `Dog` 는 `Animal` 이기도 하기 때문이다. 이것이 **contravariance** 다.
- ★★ 그래서 규칙을 외우는 대신 이렇게 기억한다 — 「**받는 자리는 넓을수록 안전하다.**」
- ★ 그리고 이 안전을 **메서드에서는 포기했다**(1번 32행). 5번이 그 이유를 잰다.

### 8. ★★★ **반환 타입은 `strictFunctionTypes` 가 건드리는 규칙이 아니기** 때문이다

**왜 그런가**

- 2번 41행 `const s5: RetDog = retAnimal;` 이 **양쪽 판 모두 막힌다.**
- ★★ 이유는 대칭이다. 「**`Dog` 를 주겠다**」고 약속한 자리에 「`Animal` 을 준다」를 넣으면,\
  받는 쪽이 `d.bark()` 를 부르는 순간 없다. **주는 자리는 좁을수록 안전하다.**
- ★★★ 그리고 이 규칙은 **애초에 느슨했던 적이 없다.** `strictFunctionTypes` 는 TS 2.6 이 **매개변수만** 고친 플래그다 —\
  반환 타입의 covariance 는 그 전부터 늘 검사됐고, 플래그와 **관계가 없다.**
- ★★ 같은 이유로 3번 18행 `WrongInMethod<in T> { get(): T }` 가 **메서드인데도** 걸린다.\
  bivariance 는 **매개변수 자리의 이야기**이고, 반환 자리에는 적용되지 않는다.
- ★ 매개변수 **개수**(2번 43행)도 같다 — 플래그와 무관하게 늘 검사된다.

### 9. ★★ `readonly` 는 **창구 하나**를, `in out` 은 **타입의 방향**을 막는다

**왜 그런가**

| | `readonly T[]` | `in out` 변성 표기 |
|---|---|---|
| 무엇을 막나 | ★ **그 참조를 통한 변경** | ★ **그 타입의 대입 방향** |
| 다른 참조가 바꾸는 것 | ★★★ **못 막는다**(4번 `readonlyAnimals[1]`) | 해당 없음 — 대입 자체를 막는다 |
| `Dog[] <- readonly Dog[]` | ★ 막는다(5번 35행 `TS4104`) | 해당 없음 |
| 메서드 문법의 bivariance | 관계없다 | ★★★ **`in out` 이면 뚫린다**(5번 28행) · `out` 만이면 못 잡는다(3번 12행) |
| 플래그를 끄면 | 그대로 | `in out` 은 그대로 · `out`/`in` 의 일부는 조용해진다(3번 15행) |

- ★★★ 4번이 `readonly` 의 한계를 실물로 보여 준다. `readonlyAnimals` 로 받았는데도 **인덱스 1 이 이미 `나비`** 다.\
  다른 이름(`animals`)이 같은 배열을 가리키고 있었기 때문이다.
- ★★ 그러므로 **`readonly` 는 「내가 안 바꾸겠다」는 약속**이지 「아무도 안 바꾼다」는 보장이 아니다\
  ([**07번 주제**](../07-object-type-details/)).
- ★★ 진짜로 방향을 막으려면 **`in out`** 이 필요하다. 5번 28행이 그 자리다 — **메서드 문법이어도 막힌다.**
- ★ 실무 조합 — **넣는 쪽을 줄 자리에는 `readonly T[]`**, **직접 만드는 제네릭 컨테이너에는 `in`/`out` 표기.**

### 10. ★★ 구별해 실었기 때문에 **`.d.ts` 를 고치면 소비자 쪽 검사 결과가 바뀐다**

**왜 그런가**

- [**16번 주제**](../16-function-types-and-overloads/)의 `.d.ts` 전문에 `run(x: string): number` 와 `run: (x: string) => number` 가 **다른 줄**로 남았다.\
  합쳐지지 않는 것이 **형식이 아니라 의미** 때문이라는 것을 이 주제가 증명한다.
- ★★★ 1번 32·33행이 그 값이다 — **같은 대입이 메서드면 통과하고 프로퍼티면 막힌다.**\
  선언 파일에서 메서드를 프로퍼티로 바꾸면 **소비자 코드가 갑자기 에러를 낸다.** 반대도 마찬가지다.
- ★★ 그래서 선언 파일을 손으로 쓸 때 규칙은 이렇다 —\
  ★ **콜백을 받는 자리**는 프로퍼티 문법으로 적어 **엄하게 검사**되게 한다.\
  ★ **컬렉션처럼 covariance 가 편한 자리**는 메서드 문법으로 둔다(5번 26행).
- ★★ 그리고 3번 12행이 **함정**이다. `out` 표기를 붙여 두고 메서드 문법으로 적으면\
  **표기가 거짓말인데도 컴파일러가 안 잡는다.** 표기를 믿고 읽는 사람만 속는다.
- ★ [**16번 주제**](../16-function-types-and-overloads/)의 5번에서 둘이 서로 대입됐던 것은 **매개변수 타입이 같아서**다 —\
  차이가 드러나려면 **부모·자식 관계의 두 타입**이 필요하다. 이 주제의 모든 예가 그렇게 짜였다.

### 11. ★★ **09 가 「넓다·좁다」를 정의하고, 07 이 `readonly` 의 한계를 정의한다**

**왜 그런가**

| 주제 | 이 주제와의 관계 |
|---|---|
| [**05번 주제**](../05-structural-typing/) | `Dog` 가 `Animal` 인 것은 **이름이 아니라 모양** 때문이다 — 변성의 전제 |
| [**09번 주제**](../09-union-types/) | 「넓다·좁다」의 기준인 **할당 가능성**. 1번의 모든 판정이 그 위에 선다 |
| [**07번 주제**](../07-object-type-details/) | `readonly` 가 **런타임을 막지 않는다** — 4번이 그것을 배열에서 확인한다 |
| [**15번 주제**](../15-control-flow-analysis-limits/) | 4번과 같은 종류의 「컴파일 통과 · 런타임 폭발」 |
| [**16번 주제**](../16-function-types-and-overloads/) | 세 꼴의 표기. 그 구별이 여기서 값을 낸다 |

- ★★★ 변성은 **할당 가능성의 파생**이다. 「`F<Dog>` 를 `F<Animal>` 에 넣어도 되나」는\
  「`Dog` 를 `Animal` 에 넣어도 되나」를 **`F` 가 어떻게 전파하는가**의 문제다.
- ★★ 그래서 [**05번 주제**](../05-structural-typing/)의 구조적 타이핑이 전제다 — `Dog` 가 `Animal` 인 것은 `extends` 라고 적어서가 아니라\
  **모양이 포함하기** 때문이다. 이 주제의 예들이 `interface Dog extends Animal` 을 쓴 것은 **읽기 편하라고**일 뿐이다.
- ★★ [**07번 주제**](../07-object-type-details/)와의 연결이 4번의 핵심이다 — `readonly` 는 **타입 쪽 표기**이고,\
  방출된 `.js` 에는 **한 글자도 안 남는다.** 그러니 다른 참조를 막을 방법이 없다.
- ★ [**15번 주제**](../15-control-flow-analysis-limits/)와 나란히 읽으면 패턴이 보인다 — TS 가 **의도적으로 unsound 한 자리**가 둘 있고,\
  둘 다 **편의를 위해** 그렇게 됐으며, 둘 다 **런타임에 같은 모양으로 터진다.**

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 반환 타입은 **covariant**(플래그 무관) · 매개변수 **개수** 규칙(플래그 무관) · ★★★ **메서드 문법은 bivariant**(켜도 그렇다) · `in`/`out` 표기가 거짓말이면 `TS2636` · `readonly T[]` 를 가변 배열에 못 넣는다(`TS4104`) · 배열은 covariant |
| **설정에 달린 것** | ★★★ **네 파일 전부**. 프로퍼티 문법·맨 함수 타입·**생성자 시그니처**의 매개변수 검사가 `strictFunctionTypes`(`strict` 에 딸려 7.0 기본 `true`)에 달렸고, **변성 표기 검사의 일부**(3번 15행)도 그렇다. **양쪽 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | ★★★ **4.7 의 `in`/`out` 이 도는 것**(3번) — 외우지 말고 다시 던져라 · ★★ **메서드 문법이 `out` 검사를 빠져나가는 것**(3번 12행) · `TS2636` 의 `sub-T`·`super-T` 라는 가상 이름 · 진단의 들여쓴 설명 줄 깊이 · 진단 문구 전문 |

- ★★★ 「**진단 0줄」이 답인 블록이 둘**이다 — 1번의 `--strictFunctionTypes false` 판과 4번의 `tsc`.\
  그 블록도 **명령과 종료 코드까지** 캡처해야 근거가 된다.
- ★★ **설정에 달린 칸이 네 파일 전부**인 것은 이 갈래에서 가장 많다. **이 주제는 플래그가 곧 주제**이기 때문이다.
- ★ 그래도 **메서드 bivariance 는 플래그와 무관**하다 — 그것이 이 주제에서 가장 오래 갈 사실이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 메서드 대 프로퍼티 | `--noEmit ex.17a.ts` | exit 1 · **2건**(33·41행) · ★★★ **32행은 통과** |
| 〃 플래그 끔 | `--noEmit --strictFunctionTypes false ex.17a.ts` | ★ **exit 0 · 진단 0줄** |
| 플래그의 범위 여덟 자리 | `--noEmit ex.17b.ts` | exit 1 · **4건**(38·39·41·43행) |
| 〃 플래그 끔 | `--noEmit --strictFunctionTypes false ex.17b.ts` | exit 1 · **2건**(41·43행) — 반환·개수는 **남는다** |
| `in`/`out` 변성 표기 | `--noEmit ex.17c.ts` | exit 1 · **3건** · ★★★ **4.7 표기가 7.0.2 에서 돈다** · 12행 **조용** |
| 〃 플래그 끔 | `--noEmit --strictFunctionTypes false ex.17c.ts` | exit 1 · **2건** — 15행이 **사라진다** |
| ★ 배열 covariance | `tsc ex.17d.ts` + `node ex.17d.js` | ★★★ **tsc exit 0 · 진단 0건** · node exit 0 · `d.bark is not a function` |
| 손으로 쓴 배열 셋 | `--noEmit ex.17e.ts` | exit 1 · **3건**(27·28·35행) · ★ **26행은 통과** |
| 〃 플래그 끔 | `--noEmit --strictFunctionTypes false ex.17e.ts` | exit 1 · **2건** — 27행이 **사라진다** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★★ **네 파일 전부 갈림** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`in`/`out` 변성 표기가 도는 것**(3번) — 4.7 기능이다. **외우지 말고 다시 던져라.**
- ★★ **메서드 문법이 `out` 검사를 빠져나가는 것**(3번 12행) — 두 규칙이 겹치는 자리라 구현에 달렸다.
- ★★ `TS2636` 이 `sub-T`·`super-T` 라는 **가상 이름**을 쓰는 것 — 보고기의 표기다.
- 진단의 들여쓴 설명 줄이 **몇 단까지 내려가는가**(1번 33행은 네 단) — 보고기의 구현이다.
- `TS2322`·`TS4104` 의 문구 전문 — 코드가 더 오래 간다.
- 런타임 예외 문구 `d.bark is not a function` — `node` v18 의 메시지다.

**안 돌려 본 것**

- **제네릭 함수의 변성** — 타입 매개변수가 붙은 함수끼리의 대입은 **안 던졌다.** [목록의 **19번 주제**](../19-generics-basics/).
- **조건부 타입·매핑 타입에서의 변성** — [목록의 **24번**](../24-conditional-types-and-distribution/)·**26번 주제**. **안 던졌다.**
- **가변 튜플의 변성** — [목록의 **46번 주제**](../46-variadic-tuple-types/). **안 던졌다.**
- **`in`/`out` 을 붙였을 때의 검사 시간 변화** — **재지 않았고 수치를 적지 않았다.**
- **`void` 반환의 특례**(반환값을 버리는 자리) — **안 던졌다.**
