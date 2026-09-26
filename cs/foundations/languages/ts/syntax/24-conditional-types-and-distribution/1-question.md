# ts/syntax/24 — 조건부 타입과 분배 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 문항은 대부분 **두 줄을 나란히 읽는 것**이다 —
> **같은 조건부를 네이키드로 한 번, `[T]` 로 감싸서 한 번** 던진 결과가 한 블록에 같이 들어 있다.
> **두 줄의 답을 각각 적어 보는 것**이 이 주제의 인출이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `javac` **21.0.5**.
> 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — 조건부 타입과 `Exclude`·`Extract`·`NonNullable` 은 **TS 2.8** 이다. **7.0 에서 도는지는 던져서 확인했다.**
>
> ★★★ **조건부의 결과를 눈으로 보는 법** — 블록에 `const probe: null = …` 이 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 그러므로 이 문서의 `TS2322` 는 **에러가 아니라 출력**이다. 세지 말고 읽어라.
> ★★★ 단 **탐침에는 눈 먼 구석이 하나 있다** — 10번 문항이 그것을 묻는다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 조건부를 두 꼴로 던지면 (예측)

```ts
// ex.24a.ts
// 분배를 켜고 끄는 대조 -- 같은 조건부를 네이키드로, 그리고 [T] 로 감싸서
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";

const nakedUnion: null = null as unknown as Naked<string | number>;
const wrappedUnion: null = null as unknown as Wrapped<string | number>;
const nakedOne: null = null as unknown as Naked<string>;
const wrappedOne: null = null as unknown as Wrapped<string>;

type ToArr<T> = T extends unknown ? T[] : never;
type ToArrOff<T> = [T] extends [unknown] ? T[] : never;
const arrOn: null = null as unknown as ToArr<string | number>;
const arrOff: null = null as unknown as ToArrOff<string | number>;

type NotNaked<T extends unknown[]> = T[number] extends string ? "문자" : "아님";
const notNaked: null = null as unknown as NotNaked<(string | number)[]>;
console.log(nakedUnion, wrappedUnion, nakedOne, wrappedOne, arrOn, arrOff, notNaked);
```

- 5행과 6행의 답을 **나란히** 적을 수 있는가?
- 7행과 8행은 어떤가 — 5·6행과 **무엇이 다른가**?
- 12행과 13행의 답이 어떻게 갈리는가? 16행은 왜 그 답인가?

### 2. `never` 를 넣으면 (예측)

```ts
// ex.24b.ts
// never 가 분배에서 사라진다 -- 빈 유니온이기 때문이다
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const nakedNever: null = null as unknown as IsNever<Naked<never>>;
const wrappedNever: null = null as unknown as Wrapped<never>;

type Always<T> = T extends unknown ? "항상" : "절대";
const alwaysNever: null = null as unknown as IsNever<Always<never>>;

type BadIsNever<T> = T extends never ? "never 다" : "never 가 아니다";
const badOnNever: null = null as unknown as IsNever<BadIsNever<never>>;
const badOnString: null = null as unknown as BadIsNever<string>;

const swallowed: null = null as unknown as Naked<string | never>;
console.log(nakedNever, wrappedNever, alwaysNever, badOnNever, badOnString, swallowed);
```

- 6행 `IsNever<Naked<never>>` 는 무엇을 뱉는가?
- 7행 `Wrapped<never>` 는 6행과 **같은 쪽인가 반대쪽인가**?
- 13행과 14행을 근거로, `BadIsNever` 가 참을 내는 입력이 **있는가**?

### 3. `boolean` 과 `any` 를 넣으면 (예측)

```ts
// ex.24c.ts
// boolean 은 true | false 로 분배되고, any 는 양쪽이 다 나온다
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";
type IsTrue<T> = T extends true ? "참" : "거짓";
type IsTrueOff<T> = [T] extends [true] ? "참" : "거짓";

const boolNaked: null = null as unknown as Naked<boolean>;
const boolSplit: null = null as unknown as IsTrue<boolean>;
const boolOff: null = null as unknown as IsTrueOff<boolean>;

const anyNaked: null = null as unknown as Naked<any>;
const anyWrapped: null = null as unknown as Wrapped<any>;
const unknownNaked: null = null as unknown as Naked<unknown>;
const neverArg: null = null as unknown as IsTrue<never>;

type Box<T> = T extends unknown ? { v: T } : never;
const boxed: null = null as unknown as Box<boolean>;
console.log(boolNaked, boolSplit, boolOff, anyNaked, anyWrapped, unknownNaked, neverArg, boxed);
```

- 7행과 8행의 답이 왜 개수가 다른가?
- 11행·12행·13행 셋을 나란히 적을 수 있는가?
- 14행에는 **진단이 없다.** 왜인가?

### 4. `Exclude` 를 손으로 다시 쓰면 (예측)

```ts
// ex.24d.ts
// Exclude · Extract · NonNullable 을 직접 다시 만들어 본다
type MyExclude<T, U> = T extends U ? never : T;
type MyExtract<T, U> = T extends U ? T : never;
type MyNonNullable<T> = T extends null | undefined ? never : T;

type Color = "빨강" | "노랑" | "파랑";

const mineExclude: null = null as unknown as MyExclude<Color, "노랑">;
const stockExclude: null = null as unknown as Exclude<Color, "노랑">;
const mineExtract: null = null as unknown as MyExtract<Color | 1 | 2, string>;
const stockExtract: null = null as unknown as Extract<Color | 1 | 2, string>;
const mineNonNull: null = null as unknown as MyNonNullable<string | null | undefined>;
const stockNonNull: null = null as unknown as NonNullable<string | null | undefined>;

type NoDistr<T, U> = [T] extends [U] ? never : T;
const brokenExclude: null = null as unknown as NoDistr<Color, "노랑">;

type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";
const allGone: null = null as unknown as IsNever<MyExclude<Color, Color>>;
console.log(mineExclude, stockExclude, mineExtract, stockExtract, mineNonNull, stockNonNull, brokenExclude, allGone);
```

- 8행과 9행의 답이 같은가?
- 16행 `NoDistr<Color, "노랑">` 은 무엇을 뱉는가?
- 19행은 왜 `IsNever` 로 감싸서 물었는가?

### 5. 제네릭 안에서 조건부를 물으면 (예측)

```ts
// ex.24e.ts
// 조건부가 지연된다 -- 제네릭 안에서는 아직 안 풀린다
type IsStr<T> = T extends string ? "문자" : "아님";

function inside<T>(x: T): IsStr<T> {
    const stillOpen: null = null as unknown as IsStr<T>;
    const cannotFill: IsStr<T> = "문자";
    console.log(stillOpen, cannotFill);
    return x as IsStr<T>;
}
const outsideStr: null = inside("가");
const outsideNum: null = inside(1);

type Deep<T> = IsStr<T> extends "문자" ? "안쪽도 문자" : "아님";
const deepKnown: null = null as unknown as Deep<string>;
function nested<T>(): Deep<T> {
    const stillOpen: null = null as unknown as Deep<T>;
    console.log(stillOpen);
    return null as unknown as Deep<T>;
}
console.log(outsideStr, outsideNum, deepKnown, nested);
```

- 5행 탐침은 무엇이라고 답하는가? 그 아래 **들여쓴 줄**은 무엇을 더 말해 주는가?
- 6행은 무슨 코드이고, 왜 막히는가?
- 10행과 11행은 5행과 **무엇이 달라져서** 풀리는가?

### 6. 같은 것을 Java 에 적으면 (예측)

```java
// Union.java
import java.util.List;

public class Union {
    static List<String | Integer> mixed() {
        return null;
    }

    static <T extends CharSequence & Comparable<T>> T bothBounds(T x) {
        return x;
    }
}
```

- 진단이 **몇 행에서** 났는가? 파서 단계인가 의미 검사 단계인가?
- 9행에는 진단이 있는가 없는가? 그 사실이 무엇을 말하는가?

### 7. `extends` 왼쪽 모양 하나로 갈리는 이유 (왜)

- 「네이키드」의 조건을 **한 문장**으로 말하고, 1번 16행이 왜 분배되지 않는지 그 문장으로 설명할 수 있는가?

### 8. `T extends never` 로는 `never` 를 못 잡는 이유 (왜)

- 2번 13·14행 **두 줄을 같이** 근거로 대며 설명할 수 있는가?

### 9. 분배를 끄면 무엇을 잃나 (경계)

- 4번 16행을 근거로, `[T]` 로 감싸는 것의 **대가**를 말할 수 있는가?
- 2번 7행은 그 대가의 **다른 얼굴**이다. 어떻게 이어지는가?

### 10. 탐침이 침묵할 때 (경계)

- 3번 14행처럼 **탐침에 진단이 안 나는** 경우가 왜 생기는가?
- 그때 **무엇으로 바꿔 물어야** 하는가? 그 새 창이 **못 보는 것**은 무엇인가?

### 11. 22 · 25 와 잇기 (연결)

- [**22번 주제**](../22-keyof-and-indexed-access-types/)가 주는 것과 [**25번 주제**](../25-infer-and-recursive-conditional-types/)가 더하는 것을 이 주제 기준으로 **한 줄씩** 말할 수 있는가?
- [**23번 주제**](../23-typeof-type-operator/)가 **왜 이 사슬에 안 들어가는지** 말할 수 있는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판(7.0.2)의 관찰** · **부적용인 창**에 해당하는 항목을 하나씩 댈 수 있는가?
- 이 주제에서 **재지 않은 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
