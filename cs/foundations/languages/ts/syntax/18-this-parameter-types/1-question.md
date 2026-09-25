# ts/syntax/18 — `this` 매개변수 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 「**`this` 매개변수는 컴파일 타임에만 있다**」이고,
> 그것을 **방출된 `.js` 전문**과 **`node` 실행 출력** 둘로 접지했다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 이 배치의 블록에는 `const probe: null = …` 이 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> 그 줄의 `TS2322` 는 **에러가 아니라 출력**이다 — 세지 말고 읽어라.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 떼어낸 메서드는 어느 줄에서 막히나 (예측)

```ts
// ex.18a.ts
// this 매개변수는 첫 매개변수 자리에만 오는 가짜 매개변수다 -- 떼어내 부르면 막힌다
interface Rect {
    w: number;
    h: number;
    area(this: Rect): number;
}

const rect: Rect = {
    w: 3,
    h: 4,
    area(this: Rect) {
        return this.w * this.h;
    },
};

const byMethod = rect.area();
const p1: null = byMethod;

const detached = rect.area;
detached();

function areaOf(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}
const p2: null = areaOf;
const p3: null = rect.area;

declare const noThis: { w: number; h: number };
areaOf.call(rect, 2);
console.log(byMethod, p1, p2, p3, noThis);
```

- 진단은 **몇 건**이고 어느 줄인가?
- 19행 `const detached = rect.area;` 와 20행 `detached();` 중 **어느 쪽**이 막히는가?
- 25행 탐침이 뱉는 타입 글자에 `this` 가 들어 있는가?

### 2. 컴파일하면 `this` 칸은 어떻게 되나 (예측)

```ts
// ex.18b.ts
// this 매개변수가 방출물에 남는가 -- 남지 않는다. 타입을 벗기면 JS 규칙이 그대로 돌아온다
interface Rect {
    w: number;
    h: number;
}

function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

const rect: Rect = { w: 3, h: 4 };
console.log("1) area.call(rect, 2) :", area.call(rect, 2));

const holder = { w: 5, h: 6, area };
console.log("2) holder.area(1)     :", holder.area(1));

const detached = area as unknown as (scale: number) => number;
try {
    detached(2);
} catch (e) {
    console.log("3) 떼어내 호출        :", (e as Error).constructor.name);
}

const bound = area.bind(rect);
console.log("4) bind 한 뒤         :", bound(10));
```

- `tsc` 의 진단은 몇 줄이고 종료 코드는 무엇인가?
- 방출된 `.js` 의 `area` 는 **매개변수를 몇 개** 받는가?
- 실행 출력 네 줄은 각각 무엇인가? 세 번째 줄이 왜 그렇게 되는가?

### 3. `call`·`apply`·`bind` 를 검사하는 것은 무엇인가 (예측)

```ts
// ex.18c.ts
// strictBindCallApply -- call / apply / bind 의 인자를 검사하게 만드는 플래그
interface Rect {
    w: number;
    h: number;
}

function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

const rect: Rect = { w: 3, h: 4 };
declare const notRect: { w: number };

area.call(rect, 2);
area.call(notRect, 2);
area.call(rect, "두 배");
area.apply(rect, [2]);
area.apply(rect, ["두 배"]);
area.bind(notRect);

function plain(x: number): number {
    return x;
}
plain.call(undefined, "문자열");
plain.apply(undefined, ["문자열"]);
```

- 기본 판의 진단은 **몇 건**인가? 16행과 18행의 **코드 번호가 같은가**?
- `--strictBindCallApply false` 를 주면 진단이 **몇 건**이 되는가?
- 24·25행의 `plain` 에는 `this` 매개변수가 없는데 왜 걸리는가?

### 4. `this: void` 자리에 무엇이 들어가나 (예측)

```ts
// ex.18d.ts
// this: void 는 "이 함수 안에서 this 를 쓰지 마라"는 계약이다 -- 그리고 화살표에는 this 매개변수를 못 단다
interface Tick {
    n: number;
}

declare function onTick(cb: (this: void, n: number) => void): void;

onTick(function (n) {
    console.log(n);
});

onTick(function (this: Tick, n) {
    console.log(this.n + n);
});

function useThis(this: Tick, n: number): void {
    console.log(this.n + n);
}
onTick(useThis);

function noThis(this: void, n: number): void {
    console.log(n, this);
}
onTick(noThis);

const arrowWithThis = (this: Tick, n: number) => n;

class Counter {
    n = 0;
    inc(this: Counter): void {
        this.n += 1;
    }
}
const counter = new Counter();
const incDetached = counter.inc;
incDetached();
```

- 진단은 몇 건이고 어느 줄인가? **8행과 22행은 걸리는가**?
- 26행은 무슨 코드인가?
- 36행은 1번의 어느 줄과 같은 코드인가?

### 5. `this` 를 타입으로 꺼내면 (예측)

```ts
// ex.18e.ts
// ThisParameterType 와 OmitThisParameter -- this 매개변수를 타입으로 꺼내고 지운다
export interface Rect {
    w: number;
    h: number;
}

export function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

export function plain(scale: number): number {
    return scale;
}

export type AreaThis = ThisParameterType<typeof area>;
export type PlainThis = ThisParameterType<typeof plain>;
export type AreaWithout = OmitThisParameter<typeof area>;
export const boundArea = area.bind({ w: 3, h: 4 });

declare const t1: AreaThis;
declare const t2: PlainThis;
declare const t3: AreaWithout;
const probe1: null = t1;
const probe2: null = t2;
const probe3: null = t3;
const probe4: null = boundArea;
console.log(probe1, probe2, probe3, probe4);
```

- 23행·24행·25행의 탐침은 각각 무엇을 뱉는가?
- 24행은 `this` 매개변수가 **없는** 함수다. 답이 `void` 인가?
- 26행 `area.bind(…)` 의 타입은 25행과 무엇이 다른가?

### 6. 한 소스에서 나온 두 방출물 (예측)

```ts
// ex.18f.ts
// 두 번째 창 -- .d.ts 에는 this 매개변수가 남고, 방출된 .js 에는 없다
export interface Rect {
    w: number;
    h: number;
}

export function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

export const bound = area.bind({ w: 3, h: 4 });
export const rectOnly = null as unknown as ThisParameterType<typeof area>;
export const without = null as unknown as OmitThisParameter<typeof area>;

export interface Handler {
    onTick(this: void, n: number): void;
}

export const method = {
    v: 1,
    read(this: { v: number }): number {
        return this.v;
    },
};
```

- `.d.ts` 와 `.js` 중 **어느 쪽에 `this` 칸이 남는가**?
- `rectOnly` 의 타입이 `.d.ts` 에 어떻게 적히는가? 5번의 탐침과 **같은 글자인가**?
- `bound` 는 왜 다르게 적히는가?

### 7. 왜 대입은 조용한가 (왜)

- 1번 19행이 막히지 않는 이유를 **한 문장**으로 댈 수 있는가?

### 8. 왜 화살표에는 `this` 매개변수를 못 다나 (왜)

- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **07번**을 근거로 설명할 수 있는가?

### 9. `this` 매개변수를 쓸 자리와 안 쓸 자리 (경계)

- 어떤 API 에 달고 어떤 API 에 안 다는가?

### 10. `strictBindCallApply` 의 범위 (경계)

- 그 플래그가 검사하는 것은 `this` 뿐인가? 끄면 무엇이 조용해지는가?

### 11. JS 의 네 규칙과 잇기 (연결)

- 2번 실행 출력의 네 줄을 JS 의 **기본·암시적·명시적·`bind`** 에 각각 대응시킬 수 있는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
