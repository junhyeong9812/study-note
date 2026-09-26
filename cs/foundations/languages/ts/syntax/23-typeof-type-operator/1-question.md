# ts/syntax/23 — `typeof` 타입 연산자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 축은 「**값 공간 / 타입 공간**」이다 —
> [**22번 주제**](../22-keyof-and-indexed-access-types/) → [**24번 주제**](../24-conditional-types-and-distribution/) → [**25번 주제**](../25-infer-and-recursive-conditional-types/) 사슬과는 **다른 축**이다.
> **「이 이름이 어느 공간에 사나」를 먼저 물으면 대부분 풀린다.**
> ★★★ **본체 창은 3창(방출된 `.js` + `node` 실행)이다** — 6번이 그 문항이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `javac` **21.0.5**.
> 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — 타입 질의(`typeof x`)는 **TS 1.0**, `typeof import(…)` 는 **2.9**, `InstanceType` 은 **2.8** 이다.
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 블록에 `const probe: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 그 꼴은 **에러가 아니라 출력**이다 — 세지 말고 읽어라.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 먼저 — 이 주제를 푸는 한 가지 물음

**막히면 늘 이것부터 물어라.**

```text
  이 이름은 어느 공간에 사는가?

     const · let · function  ->  값 공간에만
     type · interface        ->  타입 공간에만
     class · enum            ->  양쪽에

  그리고 이 자리는 어느 공간인가?

     : 뒤 · type ... = 뒤 · <> 안   ->  타입 자리
     그 밖의 거의 전부              ->  값 자리

  두 답이 어긋나면 -> 진단이 난다.  맞으면 -> 조용하다.
```

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 이름을 두 번 선언하면 (예측)

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

- 2행과 3행이 **같은 이름**을 선언한다. **충돌 진단이 나는가**?
- 이 파일에서 이름을 꺼내 쓴 자리가 아홉 군데다. **몇 군데가 진단을 내는가**? 어느 줄인가?
- 20행과 21행은 같은 `Both` 다. **둘 다 통과하는가**?
- 15행의 진단은 **다른 진단에 없는 것을 하나 더** 담고 있다. 무엇인가?

### 2. `typeof` 뒤에 무엇을 놓을 수 있나 (예측)

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

- 4·5·6행 중 **막히는 것이 있는가**?
- 8·9·10행은 각각 어떤 코드를 내는가? **세 개가 다 같은 코드인가**?
- 9행은 괄호 하나만 더 있다. **결과가 4행과 같은가 다른가**?
- ★ 이 파일만 **따로 떼어 던졌다.** 왜 1번 파일에 같이 넣지 않았겠는가?

### 3. 클래스 이름을 두 자리에 쓰면 (예측)

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

- 10행과 11행의 탐침 답을 **나란히** 적을 수 있는가?
- 14행 `const wrong: typeof Point = new Point();` 는 통과하는가? 막힌다면 **진단이 무엇을 이름으로 부르는가**?
- 22행 `new Ctor()` 는 19행과 무엇이 다른가?
- 16행은 14행의 **반대 방향**이다. 진단이 부르는 이름이 14행과 어떻게 다른가?
- 12행 `InstanceType<typeof Point>` 는 어디로 돌아오는가?

### 4. enum 하나에서 나오는 이름들 (예측)

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

- 7·8·9·10행의 답 **네 개가 다 다른가**?
- 6행 `const pick: Color = Color.Red;` 에서 왼쪽 `Color` 와 오른쪽 `Color` 는 같은 것인가?
- 18행은 `as const` 가 붙은 객체다. 14행과 견주면 **무엇이 달라지는가**?
- 9행과 13행에 붙은 `& {}` 는 무엇을 하려는 장치인가?

### 5. 모듈을 타입 자리에서 열면 (예측)

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

- 2행의 키 목록에 **몇 개가 들어 있는가**? `mod23.ts` 가 export 한 것은 셋인데 왜 그런가?
- 5행에는 `typeof` 가 **없다**. 통과하는가?
- 2행과 5행이 **같은 모듈을 열었다**. 두 줄이 보는 것이 같은가?
- ★ `typeof import("./mod23")` 를 **통째로** 탐침하지 않은 이유가 있다. 무엇이겠는가?

### 6. 방출하면 무엇이 남나 (예측)

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

- 이 파일의 **종료 코드**는 무엇인가?
- 소스 4행과 소스 7행 중 **방출물에 남는 것**은 어느 쪽인가?
- `node` 로 돌리면 `typeof setting` 과 `typeof Shape` 가 각각 **무엇을 찍는가**?
- 소스 10행 `if (typeof x === "string")` 은 방출물에 남는가? 그 줄은 **몇 개의 층에서 일하는가**?
- 방출물 어디에 `Setting` 이라는 이름이 있는가?

### 7. 왜 값 -> 타입 다리만 있고 반대는 없나 (왜)

- 타입을 값으로 만드는 문법이 있으면 **무엇이 깨지는가**? 한 문장으로 댈 수 있는가?
- `class` 와 `enum` 이 양쪽에 사는 것은 **예외인가, 아니면 당연한가**?
- ★ Java 도 이름 공간이 둘이다. **지우개가 닿는 범위**는 TS 와 같은가?

### 8. 왜 `typeof (box)` 가 막히나 (왜)

- 값 자리에서는 괄호가 아무것도 안 바꾸는데 타입 자리에서는 왜 다른가?

### 9. `typeof Cls` 와 `Cls` 의 경계 (경계)

- 클래스를 **인자로 받는** 함수의 매개변수에는 둘 중 무엇을 적어야 하는가? 반대로 적으면 어느 코드가 나는가?
- 경계를 **한 줄로** 가르는 물음은 무엇인가?

### 10. `typeof import(…)` 와 `import(…).T` 의 경계 (경계)

- 둘은 **같은 모듈의 무엇을 각각** 보는가? 한 줄로 가를 수 있는가?
- 둘 다 치르는 **공통 대가**가 하나 있다. 무엇인가?

### 11. 22 와 만나는 자리 (연결)

- `keyof typeof x` 는 연산자 **둘을 이어 붙인 것**이다. 어느 쪽이 먼저 도는가?
  그리고 [**22번 주제**](../22-keyof-and-indexed-access-types/)와 이 주제의 **경계가 어디인가**?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판(7.0.2)의 관찰** · **부적용인 창**에 해당하는 항목을 하나씩 댈 수 있는가?
  ★ 그리고 이 주제의 **`--strict` 결과가 [21번 주제](../21-inference-control-const-and-noinfer/)와 어떻게 달랐는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
