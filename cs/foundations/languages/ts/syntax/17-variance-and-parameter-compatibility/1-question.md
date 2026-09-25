# ts/syntax/17 — 변성과 매개변수 양립성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 「**`strictFunctionTypes` 를 켜도 메서드는 여전히 bivariant 다**」이고,
> 그것을 **한 줄만 갈리는 대조 블록**으로 접지했다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **네 파일 전부** `--strictFunctionTypes false` 에서 갈린다. 그 자리는 **양쪽 판을 다 실었다.**
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 메서드 문법과 프로퍼티 문법이 갈리는 자리 (예측)

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

- `strict` 기본값에서 진단은 **몇 건**이고 어느 줄인가?
- 32행과 33행은 같은 방향의 대입인데 왜 갈리는가?
- 같은 파일을 `--strictFunctionTypes false` 로 던지면 어떻게 되는가?

### 2. `strictFunctionTypes` 는 어디에 걸리나 (예측)

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

- 기본값과 `--strictFunctionTypes false` 에서 각각 **몇 건**인가?
- 플래그를 꺼도 **남는 진단**은 어느 줄이고 왜 남는가?
- 37·39·44행(클래스 메서드·생성자 시그니처·배열)은 각각 통과하는가?

### 3. `in`/`out` 변성 표기가 이 판에서 도나 (예측)

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

- 진단은 **몇 건**이고 코드는 무엇인가?
- 12행 `WrongOutMethod<out T>` 는 왜 조용한데 15행 `WrongOutProp<out T>` 는 걸리는가?
- `--strictFunctionTypes false` 로 던지면 **어느 줄이 사라지는가**?

### 4. 배열이 covariant 라서 생기는 일 (예측)

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

- `tsc` 의 **종료 코드와 진단 건수**는 무엇인가?
- 네 줄의 실행 출력은 각각 무엇인가?
- `readonly Animal[]` 로 받으면 무엇이 달라지고 무엇이 안 달라지는가?

### 5. 왜 메서드를 bivariant 로 남겼나 (예측)

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

- 진단은 **몇 건**이고 어느 줄인가?
- 26·27·28행은 같은 모양의 인터페이스 셋인데 왜 갈리는가?
- 35행은 무슨 코드가 나오는가?

### 6. 변성 네 방향 (경계)

- covariant · contravariant · bivariant · invariant 를 이 주제의 **실측 자리**와 하나씩 짝지을 수 있는가?

### 7. 왜 매개변수는 contravariant 여야 안전한가 (왜)

- 1번 33행의 진단 전문을 근거로 **한 문장**으로 댈 수 있는가?

### 8. 왜 반환 타입은 covariant 인가 (왜)

- 2번 41행이 **플래그와 무관하게** 남는 이유를 설명할 수 있는가?

### 9. `readonly` 와 `in`/`out` 의 경계 (경계)

- 배열의 불안전을 막는 두 수단은 각각 **무엇까지** 막는가?

### 10. 16 과 잇기 (연결)

- [**16번 주제**](../16-function-types-and-overloads/)의 `.d.ts` 가 두 문법을 **구별해 실은 것**이 여기서 무슨 값을 내는가?

### 11. 09·07 과 잇기 (연결)

- 유니온([**09번 주제**](../09-union-types/))과 `readonly`([**07번 주제**](../07-object-type-details/))가 이 주제와 어떻게 이어지는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
