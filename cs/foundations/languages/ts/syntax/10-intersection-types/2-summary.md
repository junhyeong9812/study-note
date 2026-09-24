# ts/syntax/10 — 인터섹션 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types: Intersection Types](https://www.typescriptlang.org/docs/handbook/2/objects.html#intersection-types) ·
> [Handbook — Functions: Overload Signatures](https://www.typescriptlang.org/docs/handbook/2/functions.html#overload-signatures-and-the-implementation-signature) ·
> [Handbook — Narrowing: Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> **버전** — 교차 타입은 TS 1.6, 「교차한 함수 타입이 오버로드처럼 해석되는 것」도 같은 계보다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문**·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★ **진단이 나지 않은 줄** — 이 주제에서는 그쪽이 근거다 | 소스 전문을 진단 옆에 뒀으니 다시 던질 수 있다 |
| **안 흔들린다** | ★ 교차가 **적은 순서를 지키는 것**(`B & A` 가 `B & A` 로 답한다) | 이 판에서 재실행해도 같았다. 다만 **보장이 아니라 관찰**이다(아래 표) |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **흔들린다** | `TS2769` 가 「마지막 오버로드」로 무엇을 고르는가 | 선언 순서에 달렸다. **코드가 `TS2769` 라는 것**만 성질로 읽는다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ 이 주제는 「**에러가 안 난 줄**」이 결정적 근거다. 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다 —
> 침묵을 근거로 쓰려면 **무엇이 침묵했는지**를 읽는 사람이 세어 볼 수 있어야 하기 때문이다.

## 한눈에 — 쉽게 말하면

**교차는 「둘 중 하나」의 반대다 — 「둘 다 동시에」다.**

| 비유 | 실체 |
|---|---|
| 상자에 「신발**이면서** 모자」라고 적혀 있다 | **교차 `A & B`** — 두 조건을 **동시에** 만족한다 |
| 꺼내 쓸 수 있는 것은 **양쪽 기능 전부** | **멤버가 합쳐진다** — `A` 의 것도 `B` 의 것도 쓴다 |
| 대신 **만들어 넣기가 어려워진다** | 객체 리터럴은 **양쪽 필수 칸을 다 채워야** 한다 |
| 「빨간색이면서 파란색」인 물건은 **없다** | **충돌 = `never`** — 만들 수 없는 타입이 조용히 생긴다 |
| ★ 없는 물건은 **상자를 열어도 아무 말이 없다** | **`never` 는 탐침을 통과한다** — 역방향으로 물어야 드러난다 |
| 설명서가 두 장이면 **경우에 따라 골라 읽는다** | **함수 교차 = 오버로드** — 인자에 맞는 시그니처가 골라진다 |

- ★★★ 한 줄로 — 「**유니온은 꺼내는 쪽이 좁고 넣는 쪽이 넓다. 교차는 정확히 반대다.**」
- ★★ 그리고 **충돌은 조용하다** — 선언한 자리에서는 아무 말도 안 하고, **쓰려는 자리에서 엉뚱한 문구로** 터진다.

```text
  A & B  (둘 다)                     vs      A | B  (둘 중 하나)

  꺼낸다:  A 의 멤버 + B 의 멤버              A 와 B 에 다 있는 멤버만
           (합집합)                           (교집합)

  넣는다:  A 이면서 B 인 값만                 A 이거나 B 인 값이면 된다
           (교집합)                           (합집합)

  함수:    오버로드 — 둘 다 부를 수 있다      매개변수가 never — 못 부른다
```

```text
  충돌의 두 얼굴

  string & number            ->  타입 **자체**가 never
        │                        (prim 이라는 값은 존재할 수 없다)
        └── null 탐침: 침묵 · 역방향 대입: TS2322 … type 'never'

  { p: string } & { p: number }
        │                    ->  타입은 살아 있고 **칸 하나만** never
        └── obj 를 찍으면 'PropClash' · obj.p 를 찍으면 침묵
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **교차한 값에서 무엇을 쓸 수 있고 무엇을 넣을 수 있나** — 유니온과 방향이 어떻게 뒤집히나.
2. **충돌하면 무엇이 `never` 가 되나** — 원시 충돌과 객체 프로퍼티 충돌을 가르고, **침묵하는 탐침을 어떻게 캐묻나**.
3. **함수와 유니온을 끼우면** — 교차가 오버로드가 되는 것과 `(A | B) & C` 가 분배되는 것.

★ [**09번 주제**](../09-union-types/)가 `|` 를 세웠다면 여기는 `&` 다. **두 주제는 한 쌍**이고, 이 문서의 표 절반이 09 와의 대비다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **`null` 탐침** | 계산된 타입을 컴파일러가 글자로 적어 준다 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★★ **역방향 대입** | **탐침이 침묵할 때** 그 타입이 `never` 인지 `any` 인지 가른다 | [**08번 주제**](../08-interface-vs-type/)에서 이어받음 |
| ★★ **진단의 들여쓴 줄** | 교차·유니온의 **어느 조각**이 문제인지 이름을 부른다 | [**09번 주제**](../09-union-types/)에서 이어받음 |
| ★★ **`.d.ts` 덤프 + 방출 `.js`** | 「적은 것」과 「런타임에 남는 것」 | [**01번 주제**](../01-what-ts-adds-and-erases/)·[**09번 주제**](../09-union-types/) |

★★★ **셋이 다른 답을 줄 때 무엇이 「적은 것」이고 무엇이 「계산된 것」인지**를 먼저 갈라야 한다.
`.d.ts` 는 **적은 것**을 옮기고, 탐침은 **계산된 것**을 찍고, 역방향 대입은 **탐침이 못 찍는 것**을 캐묻는다.

비용 — 컴파일 한 번.

### (1) ★★★ 교차는 멤버를 합치고 넣는 쪽을 좁힌다

**언제 쓰나** — 「조각 타입을 `&` 로 합쳐 하나를 만들 때」.

```ts
// ex.10a.ts
// 교차는 「둘 다」다 — 꺼내는 쪽이 넓어지고 넣는 쪽이 좁아진다
interface Named {
    name: string;
}
interface Aged {
    age: number;
}
type Person = Named & Aged;
declare const p: Person;

const useName = p.name;
const useAge = p.age;
const useNone = p.email;

const putBoth: Person = { name: "a", age: 1 };
const putOne: Person = { name: "a" };
const putExtra: Person = { name: "a", age: 1, email: "e" };

declare const onlyNamed: Named;
const widen: Named = p;
const narrow: Person = onlyNamed;

const probe: null = p;
const probeName: null = p.name;
console.log(useName, useAge, useNone, putBoth, putOne, putExtra, widen, narrow, probe, probeName);
```

```text
===== tsc --pretty false --noEmit ex.10a.ts (tsc exit=1) =====
ex.10a.ts(13,19): error TS2339: Property 'email' does not exist on type 'Person'.
ex.10a.ts(16,7): error TS2322: Type '{ name: string; }' is not assignable to type 'Person'.
  Property 'age' is missing in type '{ name: string; }' but required in type 'Aged'.
ex.10a.ts(17,47): error TS2353: Object literal may only specify known properties, and 'email' does not exist in type 'Person'.
ex.10a.ts(21,7): error TS2322: Type 'Named' is not assignable to type 'Person'.
  Property 'age' is missing in type 'Named' but required in type 'Aged'.
ex.10a.ts(23,7): error TS2322: Type 'Person' is not assignable to type 'null'.
ex.10a.ts(24,7): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **여섯 건**이다 — 13·16·17·21·23·24행. **11·12·15·20행은 통과했다.**
- 11·12행 `p.name` 과 `p.age` 가 **둘 다** 통과한다 — 교차는 **양쪽 멤버를 다 준다**. 09 의 유니온이라면 둘 다 막혔을 자리다.
- 13행 `p.email` 만 `TS2339` 다 — 없는 멤버는 여전히 없다.
- ★★ 16행 `const putOne: Person = { name: "a" }` 가 `TS2322` 이고, 들여쓴 줄이 **`Aged`** 를 짚는다 —\
  「Property 'age' is missing … but required in type 'Aged'.」 **어느 조각이 모자란지** 이름으로 말해 준다.
- 17행은 `TS2353` — 초과 프로퍼티 검사는 교차에서도 그대로 돈다([**06번 주제**](../06-excess-property-checks/)).
- ★★★ 20·21행이 이 절의 핵심 대비다. `const widen: Named = p`(**통과**) 와 `const narrow: Person = onlyNamed`(**TS2322**) —\
  **교차한 값은 각 조각 자리에 들어가지만, 조각은 교차 자리에 못 들어간다.**
- 23·24행 탐침이 확인한다 — `p` 는 **`Person`**, `p.name` 은 **`string`** 이다.

```text
  꺼내 쓰는 방향 (넓다)                    넣는 방향 (좁다)
  ┌────────────────────────────┐          ┌────────────────────────────┐
  │ Named & Aged 에서          │          │ Named & Aged 자리에        │
  │   쓸 수 있는 것 =          │          │   넣을 수 있는 것 =        │
  │   **양쪽 멤버 전부**       │          │   **양쪽을 다 만족하는 값**│
  │   (합집합)                 │          │   (교집합)                 │
  └────────────────────────────┘          └────────────────────────────┘
        ★ 09 의 유니온과 **정확히 뒤집혀 있다**
```

> **인터섹션 타입(intersection type)** — `A & B` 처럼 「이 값은 이것들 **전부**」를 적는 타입.\
> 예: `Named & Aged`. 멤버는 합쳐지고, 넣을 값은 양쪽을 다 만족해야 한다.

비용 — 없음. 다만 **조각이 늘수록 값을 만들기가 어려워진다.**

### (2) ★★★ 충돌의 두 얼굴 — 탐침이 침묵하는 자리

**언제 쓰나** — 「`&` 로 합쳤는데 아무 값도 안 들어간다」에서 막힐 때. **이 절이 이 주제의 본체다.**

```ts
// ex.10b.ts
// 충돌은 두 종류다 — 타입 전체가 never 가 되는 것과 칸 하나만 never 가 되는 것
type PrimClash = string & number;
declare const prim: PrimClash;

const probePrim: null = prim;
const asString: string = prim;
const asNumber: number = prim;
const putPrim: PrimClash = "x";

type PropClash = { p: string } & { p: number };
declare const obj: PropClash;

const probeObj: null = obj;
const probeProp: null = obj.p;
const propAsString: string = obj.p;
const propAsNumber: number = obj.p;
const putObj: PropClash = { p: "x" };

type OptClash = { q?: string } & { q: number };
declare const opt: OptClash;
const probeOpt: null = opt.q;
const putOpt: OptClash = { q: 1 };

type Narrowing = { r: string } & { r: "lit" };
declare const nar: Narrowing;
const probeNar: null = nar.r;
console.log(prim, asString, asNumber, putPrim, obj, propAsString, propAsNumber, putObj, opt, putOpt, nar);
```

```text
===== tsc --pretty false --noEmit ex.10b.ts (tsc exit=1) =====
ex.10b.ts(8,7): error TS2322: Type '"x"' is not assignable to type 'never'.
ex.10b.ts(13,7): error TS2322: Type 'PropClash' is not assignable to type 'null'.
ex.10b.ts(17,29): error TS2322: Type 'string' is not assignable to type 'never'.
ex.10b.ts(22,28): error TS2322: Type 'number' is not assignable to type 'never'.
ex.10b.ts(26,7): error TS2322: Type '"lit"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침과 역방향 대입이 **열두 줄**인데 진단은 **다섯 건**뿐이다 — 8·13·17·22·26행. **침묵한 일곱 줄이 답이다.**
- ★★★ 5·6·7행이 전부 침묵한다. `const probePrim: null = prim` 도, `const asString: string = prim` 도, `const asNumber: number = prim` 도 통과한다.\
  `string & number` 가 **`never`** 이고, `never` 는 **어디로든 들어가기 때문**이다([**04번 주제**](../04-any-unknown-never-void/)).
- ★★★ 그래서 **탐침으로는 못 묻는다.** 8행처럼 **거꾸로 넣어 봐야** 컴파일러가 말한다 —\
  「Type '"x"' is not assignable to type **'never'**.」
- ★★ 13행과 14행을 붙여 읽는 것이 이 절의 값이다. `obj` 를 찍으면 **`PropClash`** 라고 답하는데(살아 있다),\
  `obj.p` 를 찍으면 **침묵한다**(그 칸만 `never` 다). **원시 충돌은 타입 전체를, 프로퍼티 충돌은 칸 하나를** 죽인다.
- 15·16행도 침묵한다 — `obj.p` 를 `string` 에도 `number` 에도 넣을 수 있다. 다시 `never` 의 성질이다.
- 17행 역방향 대입이 그 칸을 드러낸다 — `TS2322`, 「Type 'string' is not assignable to type 'never'.」 **위치가 17행**인 것에 주의하라. **실수는 10행에서 했다.**
- ★ 21·22행 — 선택 프로퍼티도 마찬가지다. `{ q?: string } & { q: number }` 의 `q` 도 `never` 다.
- ★ 26행은 반대 경우다. `{ r: string } & { r: "lit" }` 은 충돌이 아니라 **좁혀지는 것**이라 `r` 이 **`"lit"`** 이 된다.

```text
  탐침이 침묵했다. 무엇일 수 있나?

        const probe: null = x;   ->  진단 없음
                │
        ┌───────┴────────┐
        │                │
     never 다          any 다
        │                │
        ▼                ▼
   const y: X = <값>   const y: X = <아무 값>
     -> TS2322            -> 진단 없음
        'never'
   ★ 역방향 대입 한 줄이 둘을 가른다
```

> **`never`** — 값이 하나도 없는 타입. **어디로든 들어가고 아무 값도 못 받는다**([**04번 주제**](../04-any-unknown-never-void/)).\
> 예: `string & number`. 교차가 충돌하면 여기로 떨어진다.

비용 — **교차는 실수를 늦게 알려 준다.** 선언 자리는 조용하고, 값을 만들려는 자리에서 터진다.

### (3) ★★ 교차도 정규화된다 — 다만 순서는 안 바꾼다

**언제 쓰나** — 09 에서 본 「적은 대로 남지 않는다」를 교차에도 물을 때.

```ts
// ex.10c.ts
// 교차도 적은 대로 남나 — 09 의 유니온과 같은 질문을 교차에 던진다
interface A {
    a: string;
}
interface B {
    b: number;
}
interface C {
    c: boolean;
}

declare const dup: A & A;
declare const withNever: A & never;
declare const withAny: A & any;
declare const withUnknown: A & unknown;
declare const nested: (A & B) & C;
declare const reordered: B & A;
declare const litBase: "a" & string;
declare const litClash: "a" & "b";
declare const objPrim: A & string;

const p1: null = dup;
const p2: null = withNever;
const p3: null = withAny;
const p4: null = withUnknown;
const p5: null = nested;
const p6: null = reordered;
const p7: null = litBase;
const p8: null = litClash;
const p9: null = objPrim;

const back2: A & never = { a: "x" };
const back3: A & any = "A 가 아닌 것";
const back8: "a" & "b" = "a";
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, back2, back3, back8);
```

```text
===== tsc --pretty false --noEmit ex.10c.ts (tsc exit=1) =====
ex.10c.ts(22,7): error TS2322: Type 'A' is not assignable to type 'null'.
ex.10c.ts(25,7): error TS2322: Type 'A' is not assignable to type 'null'.
ex.10c.ts(26,7): error TS2322: Type 'A & B & C' is not assignable to type 'null'.
ex.10c.ts(27,7): error TS2322: Type 'B & A' is not assignable to type 'null'.
ex.10c.ts(28,7): error TS2322: Type '"a"' is not assignable to type 'null'.
ex.10c.ts(30,7): error TS2322: Type 'A & string' is not assignable to type 'null'.
ex.10c.ts(32,7): error TS2322: Type '{ a: string; }' is not assignable to type 'never'.
ex.10c.ts(34,7): error TS2322: Type '"a"' is not assignable to type 'never'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침 아홉 개와 역방향 세 줄 중 진단은 **여덟 건**이다. **침묵한 것은 23·24·29·33행** 넷이다.
- 22행 — `A & A` 가 **`A`** 다. **중복이 제거된다.**
- ★★ 23행이 침묵하고 32행이 말한다 — `A & never` 가 **`never`** 다. 「Type '{ a: string; }' is not assignable to type 'never'.」
- ★★★ 24행과 33행이 **둘 다 침묵한다.** `A & any` 는 `never` 가 아니라 **`any`** 다 —\
  `never` 였다면 33행 `const back3: A & any = "A 가 아닌 것"` 이 막혔을 것이다. **역방향 대입 한 줄이 둘을 갈랐다.**
- 25행 — `A & unknown` 이 **`A`** 다. `unknown` 은 교차에서 **사라진다**(유니온에서는 반대로 **먹었다**).
- 26행 — `(A & B) & C` 가 **`A & B & C`** 다. **평탄화된다.**
- ★★★ 27행 — `B & A` 라고 적었더니 진단도 **`B & A`** 라고 답한다. **순서를 안 바꾼다.**\
  09 의 유니온은 `number | string` 을 `string | number` 로 **재정렬했다.** 여기서는 그러지 않는다.
- 28행 — `"a" & string` 이 **`"a"`** 다. **좁은 쪽이 남는다**(유니온에서는 넓은 쪽이 남아 `string` 이 됐다).
- 29행이 침묵하고 34행이 말한다 — `"a" & "b"` 는 **`never`** 다.
- ★ 30행 — `A & string` 은 **줄지 않는다.** `A & string` 그대로다. 객체와 원시의 교차는 **충돌로 치지 않는다**.

```text
  09 의 유니온과 나란히 놓으면

  적은 것                     유니온에서          교차에서
  ─────────────────────────────────────────────────────────
  X | X   /  X & X            X                   X          중복 제거 (같다)
  never                       사라진다            전부 삼킨다  ★ 뒤집힌다
  any                         전부 삼킨다         전부 삼킨다  (같다)
  unknown                     전부 삼킨다         사라진다     ★ 뒤집힌다
  리터럴과 기반 타입          넓은 쪽(string)     좁은 쪽("a") ★ 뒤집힌다
  중첩                        평탄화              평탄화       (같다)
  순서                        ★ 재정렬한다        ★ 안 바꾼다  ★ 갈린다
```

> **정규화(normalization)** — 타입을 만들 때 컴파일러가 평탄화·중복 제거·흡수를 해서 내부 표현을 정리하는 것.\
> 예: `(A & B) & C` 가 `A & B & C` 가 된다.

- ★★ **순서를 안 바꾸는 것은 「보장」이 아니라 「이 판의 관찰」이다.** 대조할 것은 순서가 아니라 「**같은 조각 집합으로 정리된다**」는 성질이다.

비용 — 없음. 다만 **진단이 내가 적은 것과 다르게 보일 수 있다** — 그 사실을 알고 읽어야 한다.

### (4) ★★★ 함수의 교차는 오버로드가 된다

**언제 쓰나** — 「하나의 값이 여러 시그니처로 불려야 할 때」. **09 의 정반대 자리다.**

```ts
// ex.10d.ts
// 함수의 교차는 오버로드가 된다 — 09 의 함수 유니온과 정반대다
type CrossFn = ((a: string) => string) & ((a: number) => number);
declare const cross: CrossFn;

const fromString: null = cross("s");
const fromNumber: null = cross(1);
cross(true);

interface OverFn {
    (a: string): string;
    (a: number): number;
}
declare const over: OverFn;
const overString: null = over("s");
over(true);

type UnionFn = ((a: string) => string) | ((a: number) => number);
declare const union: UnionFn;
union("s");

const asStringFn: (a: string) => string = cross;
const asNumberFn: (a: number) => number = cross;
const asBoolFn: (a: boolean) => boolean = cross;
console.log(fromString, fromNumber, overString, asStringFn, asNumberFn, asBoolFn);
```

```text
===== tsc --pretty false --noEmit ex.10d.ts (tsc exit=1) =====
ex.10d.ts(5,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10d.ts(6,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.10d.ts(7,7): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'boolean' is not assignable to parameter of type 'number'.
ex.10d.ts(14,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10d.ts(15,6): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'boolean' is not assignable to parameter of type 'number'.
ex.10d.ts(19,7): error TS2345: Argument of type '"s"' is not assignable to parameter of type 'never'.
ex.10d.ts(23,7): error TS2322: Type 'CrossFn' is not assignable to type '(a: boolean) => boolean'.
  Types of parameters 'a' and 'a' are incompatible.
    Type 'boolean' is not assignable to type 'string'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이다. 5·6행은 **탐침이라서** 난 것이고, **호출 자체는 둘 다 통과했다.**
- ★★★ 5행이 `string`, 6행이 `number` 라고 답한다 — `cross("s")` 는 첫 시그니처로, `cross(1)` 은 둘째 시그니처로 **각각 풀린다.**
- ★★★ 7행 `cross(true)` 가 `TS2769` — 「No overload matches this call.」\
  15행 `over(true)` 와 **글자 하나까지 같은 진단**이다. `over` 는 손으로 적은 **오버로드 인터페이스**다.\
  즉 **교차한 함수 타입은 오버로드와 같은 것으로 취급된다.**
- ★★★ 19행이 대비다 — 같은 두 시그니처를 `|` 로 묶은 `union("s")` 는 `TS2345`, 「parameter of type **`never`**」다.\
  **교차는 둘 다 부를 수 있게 하고, 유니온은 아무것도 못 부르게 한다.**
- 21·22행은 통과한다 — 교차한 함수는 **각 시그니처 자리에 그대로 들어간다.**
- 23행만 막힌다 — `(a: boolean) => boolean` 은 어느 시그니처도 아니다. 들여쓴 줄이 **첫 시그니처**를 기준으로 이유를 댄다.

```text
  ((a: string) => string) & ((a: number) => number)
                  │
                  ▼  「둘 다인 함수」 = 둘 다로 불릴 수 있다
          cross("s") -> string      cross(1) -> number
          cross(true) -> TS2769  No overload matches this call.

  ((a: string) => string) | ((a: number) => number)
                  │
                  ▼  「둘 중 하나인 함수」 = 어느 쪽인지 모른다
          union("s") -> TS2345  parameter of type 'never'
```

> **오버로드(overload)** — 같은 이름에 시그니처를 여럿 달아 인자에 따라 고르게 하는 것.\
> 예: `interface OverFn { (a: string): string; (a: number): number }`. **교차한 함수 타입도 같은 것이 된다.**

비용 — 오버로드 해석은 **위에서부터 맞는 것을 고른다.** 순서에 뜻이 생긴다 — 전면 서술은 목록의 **16번 주제**다.

### (5) ★★★ 유니온을 끼우면 분배된다

**언제 쓰나** — 「판별 유니온에 공통 칸을 덧붙일 때」. 실무에서 교차를 쓰는 가장 흔한 모양이다.

```ts
// ex.10e.ts
// (A | B) & C 는 분배된다 — 진단의 들여쓴 줄이 그 조각 이름을 부른다
interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
interface Tagged {
    id: string;
}

declare const shape: (Circle | Square) & Tagged;

const probeAll: null = shape;
const probeKind: null = shape.kind;
const probeId: null = shape.id;
shape.r;

declare const spelled: (Circle & Tagged) | (Square & Tagged);
const probeSpelled: null = spelled;

const putOk: (Circle | Square) & Tagged = { kind: "circle", r: 1, id: "x" };
const putNoTag: (Circle | Square) & Tagged = { kind: "circle", r: 1 };
const putMixed: (Circle | Square) & Tagged = { kind: "circle", r: 1, side: 2, id: "x" };

function split(s: (Circle | Square) & Tagged) {
    if (s.kind === "circle") {
        const inCircle: null = s;
    } else {
        const inSquare: null = s;
    }
}
console.log(probeAll, probeKind, probeId, probeSpelled, putOk, putNoTag, putMixed, split);
```

```text
===== tsc --pretty false --noEmit ex.10e.ts (tsc exit=1) =====
ex.10e.ts(16,7): error TS2322: Type '(Circle | Square) & Tagged' is not assignable to type 'null'.
  Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(17,7): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.10e.ts(18,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10e.ts(19,7): error TS2339: Property 'r' does not exist on type '(Circle | Square) & Tagged'.
  Property 'r' does not exist on type 'Square & Tagged'.
ex.10e.ts(22,7): error TS2322: Type '(Circle & Tagged) | (Square & Tagged)' is not assignable to type 'null'.
  Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(25,7): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type '(Circle | Square) & Tagged'.
  Type '{ kind: "circle"; r: number; }' is not assignable to type 'Circle & Tagged'.
    Property 'id' is missing in type '{ kind: "circle"; r: number; }' but required in type 'Tagged'.
ex.10e.ts(26,70): error TS2353: Object literal may only specify known properties, and 'side' does not exist in type 'Circle & Tagged'.
ex.10e.ts(30,15): error TS2322: Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(32,15): error TS2322: Type 'Square & Tagged' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **아홉 건**이다 — 16·17·18·19·22·25·26·30·32행. **24행은 통과했다.**
- ★★★ 16행 탐침의 **들여쓴 줄**이 답을 준다 — 「Type **'Circle & Tagged'** is not assignable to type 'null'.」\
  적은 것은 `(Circle | Square) & Tagged` 인데, 컴파일러는 그것을 **`Circle & Tagged`** 와 **`Square & Tagged`** 의 유니온으로 다룬다.
- 17행 `shape.kind` 가 **`"circle" | "square"`** 다 — 판별 칸이 **유니온으로 남는다**.
- 18행 `shape.id` 는 **`string`** 이다 — 공통 칸은 양쪽에 다 붙었다.
- ★★ 19행 `shape.r` 이 `TS2339` 이고 들여쓴 줄이 **`Square & Tagged`** 를 짚는다. **분배된 조각 이름을 그대로 부른다.**
- 22행이 못을 박는다 — 손으로 적은 `(Circle & Tagged) | (Square & Tagged)` 가 **같은 모양의 진단**을 낸다.
- ★★ 26행 초과 프로퍼티 검사도 **`Circle & Tagged`** 를 대고 막는다 — 분배된 뒤의 조각과 대조한다는 뜻이다.
- ★★★ 30·32행이 실무에서 중요한 칸이다 — `if (s.kind === "circle")` 로 갈면 **`Circle & Tagged`** 와 **`Square & Tagged`** 로 좁혀진다.\
  **판별 유니온에 공통 칸을 `&` 로 붙여도 좁히기가 살아 있다**([**12번 주제**](../12-narrowing/)로 이어진다).

```text
  (Circle | Square) & Tagged
            │
            ▼  분배된다
  (Circle & Tagged) | (Square & Tagged)
            │
            ├── .kind   ->  "circle" | "square"      판별 칸은 유니온
            ├── .id     ->  string                   공통 칸은 양쪽에
            └── .r      ->  TS2339  … on type 'Square & Tagged'
                                              ↑ 조각 이름을 그대로 부른다
```

비용 — 없음. 다만 **에러 메시지가 내가 안 적은 이름을 부른다** — 그 이름이 어디서 왔는지 알고 읽어야 한다.

### (6) ★★ 선언 방출은 적은 그대로, JS 방출에는 한 글자도 안 남는다

**언제 쓰나** — 2·3절의 결과를 「그럼 `.d.ts` 도 그렇겠지」로 넘기기 전에.

```ts
// ex.10f.ts
// 선언 방출은 교차를 적은 그대로 돌려준다 — 09 의 유니온과 같다
export interface A {
    a: string;
}
export interface B {
    b: number;
}
export type Dup = A & A;
export type WithNever = A & never;
export type PrimClash = string & number;
export type Nested = (A & B) & B;
export type Reordered = B & A;
export type CrossFn = ((a: string) => string) & ((a: number) => number);
export declare const merged: A & B;
export const made = { a: "x", b: 1 } as A & B;
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.10f.ts (tsc exit=0) =====
===== 방출된 ex.10f.d.ts =====
export interface A {
    a: string;
}
export interface B {
    b: number;
}
export type Dup = A & A;
export type WithNever = A & never;
export type PrimClash = string & number;
export type Nested = (A & B) & B;
export type Reordered = B & A;
export type CrossFn = ((a: string) => string) & ((a: number) => number);
export declare const merged: A & B;
export declare const made: A & B;
```

```ts
// ex.10g.ts
// 교차는 방출에 한 글자도 안 남는다 — 합치는 일은 JS 스프레드가 한다
interface A {
    a: string;
}
interface B {
    b: number;
}
type Both = A & B;

function merge(x: A, y: B): Both {
    return { ...x, ...y };
}

const both: Both = merge({ a: "hi" }, { b: 7 });
console.log("merge     :", JSON.stringify(both));
console.log("a / b     :", both.a, "/", both.b);
console.log("런타임 구분:", typeof both, Object.keys(both).join(","));
```

```text
===== tsc --pretty false ex.10g.ts (tsc exit=0) =====
===== 방출된 ex.10g.js =====
"use strict";
function merge(x, y) {
    return { ...x, ...y };
}
const both = merge({ a: "hi" }, { b: 7 });
console.log("merge     :", JSON.stringify(both));
console.log("a / b     :", both.a, "/", both.b);
console.log("런타임 구분:", typeof both, Object.keys(both).join(","));
```

```text
===== node ex.10g.js (node exit=0) =====
merge     : {"a":"hi","b":7}
a / b     : hi / 7
런타임 구분: object a,b
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `.d.ts` 가 **적은 그대로** 돌려준다 — `A & A` 도, `A & never` 도, `string & number` 도, `(A & B) & B` 의 괄호까지 손대지 않았다.
- ★★ 3절의 탐침과 **정반대 답**이다. 같은 선언인데 **창에 따라 다르게 보인다** — 09 에서 유니온으로 본 것과 같은 성질이다.
- ★ 값 쪽은 다르다 — `export const made = { a: "x", b: 1 } as A & B` 가 **`export declare const made: A & B`** 로 나온다.\
  **타입 별칭은 표기를 옮기고, 값 선언은 추론 결과를 적는다.**
- 방출된 `.js` 에는 `interface A`·`interface B`·`type Both` 가 **통째로 없다.** `"use strict";` 다음이 곧장 `function merge(x, y) {` 다.
- ★★★ 합치는 일을 실제로 하는 것은 **JS 스프레드**(`{ ...x, ...y }`)다. 교차는 그 결과에 이름을 붙였을 뿐이다.
- 실행 결과가 확인한다 — `{"a":"hi","b":7}` 이고 `typeof` 는 `object`, 키는 `a,b` 다. **런타임에 「교차」라는 것은 없다.**

비용 — 0. 방출에 한 글자도 안 남는다.

### (7) ★ `strict` 를 꺼도 답이 같다

**언제 쓰나** — 「이 결과가 `strict` 덕분 아닌가」를 의심할 때.

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.10a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ 다섯 파일이 **종료 코드도 출력도 글자 하나까지 같다.** 이 주제의 결론은 전부 **선언 구조**에서 나오고 `strict` 묶음과 무관하다.
- ★ 그래서 이 문서에는 **「설정에 달린 칸」이 0개**다. 반대로 [**12번 주제**](../12-narrowing/)는 세 파일이 갈린다 — 좁히기는 `strictNullChecks` 위에 서기 때문이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  type Person = Named & Aged                    기본형
  type PrimClash = string & number              ★ 타입 전체가 never
  type PropClash = { p: string } & { p: number } ★ 칸 하나만 never
  type CrossFn = ((a: string) => string) & ((a: number) => number)   ★ 오버로드
  type Dist = (Circle | Square) & Tagged        ★ 분배된다

  const probe: null = v;                        계산된 타입을 캐묻는다
  const back: X = <값>;                         ★ 탐침이 침묵할 때 역방향으로 캐묻는다
```

**규칙 불릿**

- ★★★ **꺼내는 쪽은 합집합, 넣는 쪽은 교집합**이다. 09 의 유니온과 **정확히 뒤집혀 있다.**
- ★★ **교차한 값은 각 조각 자리에 들어가지만, 조각은 교차 자리에 못 들어간다.**
- ★★★ **충돌은 두 얼굴이다** — 원시끼리면 **타입 전체가 `never`**, 객체 프로퍼티끼리면 **그 칸만 `never`** 다.
- ★★★ **`never` 는 탐침을 통과한다.** 침묵하면 **역방향 대입**으로 묻고, `any` 인지 `never` 인지도 그 한 줄로 가른다.
- ★★ **교차도 정규화된다** — 중복 제거 · `never` 가 전부 삼킴 · `any` 가 전부 삼킴 · `unknown` 은 사라짐 · 리터럴이 남음 · 평탄화. **순서는 안 바꾼다.**
- ★★★ **함수 교차는 오버로드**다 — 잘못된 인자는 `TS2769` 로 막힌다. **함수 유니온은 `TS2345` 의 `never` 다.**
- ★★ **`(A | B) & C` 는 분배된다** — 진단이 `A & C`·`B & C` 라는 **내가 안 적은 이름**을 부른다. 좁히기도 그 조각 단위로 된다.
- ★★ **`.d.ts` 는 정규화를 안 한다.** 방출된 `.js` 에는 한 글자도 안 남는다.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 교차 자리에 조각만 넣기   ->  TS2322  Type 'Named' is not assignable to type 'Person'.
                                   Property 'age' is missing in type 'Named' but required in type 'Aged'.
2) never 가 된 칸에 값 넣기   ->  TS2322  Type 'string' is not assignable to type 'never'.
3) 교차한 함수에 엉뚱한 인자  ->  TS2769  No overload matches this call.
4) 분배된 조각에 없는 멤버    ->  TS2339  Property 'r' does not exist on type '(Circle | Square) & Tagged'.
                                   Property 'r' does not exist on type 'Square & Tagged'.
```

## 어디서 틀리나

- ★★★ 「**`&` 는 또는을 뜻한다**」 — 반대다. `&` 가 「**둘 다**」이고 `|` 가 「**둘 중 하나**」다. 기호를 보고 **집합의 교집합**을 떠올리면 헷갈린다 — **멤버로 보면 합집합**이다.
- ★★★ 「**탐침에 진단이 없으니 문제가 없다**」 — `never` 도 `any` 도 **탐침을 통과한다.** 침묵은 「멀쩡하다」가 아니라 「**더 물어야 한다**」는 신호다.
- ★★★ 「**충돌하면 선언 자리에서 에러가 난다**」 — 안 난다. `type PropClash = { p: string } & { p: number }` 는 **조용히 통과**하고, **값을 만들려는 줄**에서 엉뚱한 문구로 터진다.
- ★★ 「**`string & number` 도 객체 충돌과 같겠지**」 — 다르다. **원시 충돌은 타입 전체**가 `never` 이고, **객체 프로퍼티 충돌은 그 칸만** `never` 다.
- ★★ 「**핸들러를 `&` 로 묶으면 못 쓰겠지**」 — 반대다. `&` 로 묶으면 **오버로드가 되어 둘 다 쓸 수 있다.** 못 쓰게 되는 것은 `|` 쪽이다([**09번 주제**](../09-union-types/)).
- ★★ 「**`A & unknown` 은 `unknown` 이겠지**」 — 유니온에서는 그랬지만 교차에서는 **`A`** 다. `unknown` 은 교차에서 사라진다.
- ★ 「**`A & never` 는 `A` 겠지**」 — **`never`** 다. `never` 는 교차에서 전부 삼킨다.
- ★ 「**순서를 바꾸면 다른 타입**」 — 같은 타입이다. 다만 **진단에 찍히는 글자는 적은 순서 그대로**라 달라 보인다.
- ★ 「**`.d.ts` 를 보면 계산된 타입을 알 수 있다**」 — `.d.ts` 는 **적은 그대로**다. 계산 결과는 **탐침**이 답한다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 교차는 **멤버를 합치고 넣는 값을 좁힌다** | 핸드북 「Intersection Types」. `ex.10a.ts` 의 11·12행 통과와 16·21행 `TS2322` |
| **언어 보장** | 프로퍼티는 **교차**된다 — `string & number` 는 `never` | `ex.10b.ts` 의 **침묵한 일곱 줄 + 역방향 대입 세 건** |
| **언어 보장** | 교차는 **평탄화·중복 제거·흡수**로 정규화된다 | `ex.10c.ts` 의 탐침 아홉 개와 역방향 세 줄 |
| **언어 보장** | 함수 교차는 **오버로드**가 된다 | `cross(true)` 와 손으로 적은 `over(true)` 가 **같은 `TS2769`** |
| **언어 보장** | `(A \| B) & C` 는 **분배**된다 | `TS2339` 의 들여쓴 줄이 `Square & Tagged` 를 부른다 |
| **언어 보장** | 교차는 **방출에 안 남는다** | `ex.10g.js` 전문과 `node` 출력 |
| **설정에 달림** | ★ **없다** | 다섯 파일을 `--strict false` 로 다시 던져 **종료 코드와 출력이 전부 같은 것**을 확인했다((7)절) |
| **이 판(7.0.2)의 관찰** | ★★ 교차가 **적은 순서를 지키는 것** — `B & A` 가 `A & B` 로 재정렬되지 않는다 | 09 의 유니온은 재정렬했다. **대조 기준으로 쓰지 않는다** |
| **이 판의 관찰** | `TS2769` 가 「The last overload」로 **어느 시그니처를 고르는가** | 선언 순서를 따른다. 코드가 `TS2769` 라는 것만 성질로 읽는다 |
| **이 판의 관찰** | `.d.ts` 가 교차 표기를 **괄호까지 그대로** 싣는 것 | 선언 방출기의 구현이다 |
| **안 잰 것** | 조각이 늘 때의 **검사 시간** | 아래 「더 들어가면」을 보라 |

★★★ 「**에러가 안 난 줄」이 이 주제의 지배적 근거다** — 2절에서 열두 줄 중 **일곱 줄이 침묵**했고, 그 침묵이 곧 `never` 의 증거다.
그래서 이 문서는 **모든 진단 블록 옆에 소스 전문**을 두었다. 진단만 실으면 **무엇이 침묵했는지 셀 수 없다.**

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 겹치지 않는 조각을 합친다 — `Named & Aged` | 같은 키를 다른 타입으로 갖는 조각을 겹치는 것 — **조용히 `never`** |
| 판별 유니온에 공통 칸 붙이기 — `(Circle \| Square) & Tagged` | 원시끼리 교차 — `string & number` 는 만들 수 없는 타입이다 |
| 하나의 값에 시그니처 여럿 — **함수 교차 = 오버로드** | 콜백·핸들러를 `\|` 로 묶는 것 — 매개변수가 `never` 가 된다([**09번 주제**](../09-union-types/)) |
| 브랜드 타입 — `string & { __brand: "Id" }` | 「합치면 뭐든 되겠지」로 조각을 쌓는 것 — 진단이 **엉뚱한 줄에서** 난다 |
| 믹스인처럼 기능을 얹는 자리 | 충돌 여부를 **선언 자리에서** 잡고 싶을 때 — 그때는 `interface extends`([**08번 주제**](../08-interface-vs-type/)) |

## 핵심 문장

1. **교차는 유니온을 뒤집은 것이다** — 꺼내는 쪽이 합집합, 넣는 쪽이 교집합이다.
2. **충돌은 조용하다** — 선언 자리는 통과하고, 값을 만들려는 자리에서 `never` 로 터진다.
3. **`never` 는 탐침을 통과한다** — 침묵하면 **역방향 대입**으로 묻는다. 그 한 줄이 `never` 와 `any` 도 가른다.
4. **원시 충돌은 타입 전체를, 프로퍼티 충돌은 칸 하나를** 죽인다.
5. **함수 교차는 오버로드다** — `TS2769` 가 손으로 적은 오버로드와 같은 문구로 말한다.
6. **`(A | B) & C` 는 분배된다** — 진단이 내가 안 적은 조각 이름을 부른다.
7. **`.d.ts` 는 적은 그대로, `.js` 에는 한 글자도 안 남는다.**

## 관련 자료

- [**09번 주제** — 유니온 타입](../09-union-types/) — 이 주제와 **한 쌍**이다. 방향이 뒤집히는 네 칸은 그쪽과 나란히 읽는다.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `never` 가 **어디로든 들어간다**는 성질은 그쪽이 정본이다. 2절이 그 위에 선다.
- [**08번 주제** — `interface` 대 `type`](../08-interface-vs-type/) — **역방향 대입**이라는 수법과 「`extends` 는 말하고 교차는 침묵한다」는 그쪽.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — 대상이 교차일 때 그 검사가 **분배된 조각**과 대조되는 것은 5절.
- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — `null` 탐침과 `.d.ts` 덤프의 두 창은 그쪽에서 세웠다.
- [**12번 주제** — 좁히기](../12-narrowing/) — 분배된 교차가 `s.kind` 로 갈리는 자리는 그쪽이 전면 서술이다.
- 목록의 **16번 주제**(함수 타입과 오버로드) — 오버로드 해석 순서와 구현 시그니처는 그쪽.
- 목록의 **24번 주제**(조건부 타입과 분배) — 「분배」라는 말이 조건부 타입에서 다시 나온다. **같은 말, 다른 규칙**이다.
- 목록의 **28번 주제**(유틸리티 타입) — `Omit` 으로 충돌 키를 빼는 관용구는 그쪽.

## 용어 풀이

> **인터섹션 타입(intersection type)** — `A & B` 처럼 「이 값은 이것들 **전부**」를 적는 타입.\
> 예: `Named & Aged`. 멤버는 합쳐지고, 넣을 값은 양쪽을 다 만족해야 한다.

> **역방향 대입** — 탐침이 침묵할 때 **거꾸로 값을 넣어 보는** 수법.\
> 예: `const back: A & never = { a: "x" };` — 진단이 나면 그 타입은 `never` 다.

> **`never`** — 값이 하나도 없는 타입. 어디로든 들어가고 아무 값도 못 받는다.\
> 예: `string & number` · `"a" & "b"`.

> **분배(distribution)** — 유니온을 끼운 연산이 **멤버마다 따로 계산되는** 것.\
> 예: `(A \| B) & C` 가 `(A & C) \| (B & C)` 로 다뤄진다.

> **오버로드(overload)** — 같은 값에 시그니처를 여럿 달아 인자에 따라 고르게 하는 것.\
> 예: `((a: string) => string) & ((a: number) => number)`.

> **브랜드 타입(branded type)** — 원시 타입에 표시용 칸을 교차해 **명목 구분**을 흉내 내는 관용구.\
> 예: `type Id = string & { __brand: "Id" }`([**05번 주제**](../05-structural-typing/)).

## 더 들어가면

- **왜 멤버는 합집합인데 값은 교집합인가** — 「이 값은 `A` 이면서 `B` 다」라는 **하나의 전제**에서 둘 다 나온다. 전제를 믿으면 양쪽 멤버를 다 쓸 수 있고, 전제를 만들려면 양쪽 조건을 다 채워야 한다.
- **충돌을 미리 잡는 법** — 겹치기 전에 `interface X extends A` 로 한 번 받아 보면 `TS2430` 이 **선언 자리에서** 말한다([**08번 주제**](../08-interface-vs-type/)). 또는 `Omit` 으로 충돌 키를 먼저 뺀다.
- **브랜드 타입** — `A & string` 이 줄지 않는다(3절의 30행)는 성질이 브랜드 타입의 토대다. `string & { __brand: "Id" }` 는 런타임에 그냥 문자열이면서 타입에서만 구분된다.
- **조각이 늘면 검사가 느려진다** — 할당 가능성 판정이 조각 수에 따라 늘어난다. 이 배치에서는 **재지 않았다** — 목록의 **45번 주제**에서 잰다.
