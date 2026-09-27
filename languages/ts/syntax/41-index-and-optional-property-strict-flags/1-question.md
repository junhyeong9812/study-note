# ts/syntax/41 — 인덱스·선택 프로퍼티 엄격 플래그 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **41 은 40 에서 온다** — [**40번 주제**](../40-strict-null-checks-ripple/)가 `undefined` 를 따로 선 타입으로 만드는 스위치를 쟀다. [**07번 주제**](../07-object-type-details/) 4절이 이 편의 두 플래그를 **처음** 켜 봤다.
> 여기서는 두 플래그가 **어느 꼴에 걸리고 어느 꼴에 안 걸리나**와, 막는 것이 **런타임에서 왜 의미가 있나**를 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★ 타입은 `const p: symbol = 식;` 한 줄로 뽑는다 — 진단 문구의 `Type '…'` 가 그 식의 타입이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 꼴 열하나 × 켬/끔 (예측)

```ts
// idx41.ts
declare const arr: number[];
declare const dict: { [k: string]: number };
declare const rec: Record<string, number>;
declare const fixed: Record<"a" | "b", number>;
declare const pair: [number, string];
const p1: symbol = arr[0];
const p2: symbol = dict["k"];
const p3: symbol = dict.k;
const p4: symbol = rec.k;
const p5: symbol = fixed.a;
const p6: symbol = pair[0];
for (const v of arr) {
    const p7: symbol = v;
}
const [first] = arr;
const p8: symbol = first;
const { k } = dict;
const p9: symbol = k;
const p10: symbol = arr.at(0);
for (let i = 0; i < arr.length; i++) {
    const p11: symbol = arr[i];
}
export {};
```

- `tsc --noEmit -t es2022 idx41.ts` 와 `--noUncheckedIndexedAccess` 를 붙인 판에서 11개 탐침은 각각 어느 타입을 말하는가? 켜서 달라지는 것은 어느 행인가?

### 2. 선택 프로퍼티에 쓰기와 읽기 (예측)

```ts
// eopt41.ts
interface Opts {
    retries?: number;
}
const a: Opts = {};
const b: Opts = { retries: undefined };
const c: Opts = {};
c.retries = undefined;
delete c.retries;
function read(o: Opts) {
    const p1: symbol = o.retries;
}
interface Loose {
    retries?: number | undefined;
}
const d: Loose = { retries: undefined };
export {};
```

- 기본과 `--exactOptionalPropertyTypes` 판에서 5·7·8·10·15행은 각각 무엇을 내는가?

### 3. 없는 키와 `undefined` 인 키 (예측)

```ts
// eoptrun41.ts
interface Opts {
    retries?: number;
}
const defaults = { retries: 3 };
const given: Opts = { retries: undefined };
const empty: Opts = {};
const merged = { ...defaults, ...given };
console.log("[1]", "retries" in given, "retries" in empty);
console.log("[2]", Object.keys(given).length, Object.keys(empty).length);
console.log("[3]", JSON.stringify(given), JSON.stringify(empty));
console.log("[4]", merged.retries, typeof merged.retries);
const p1: symbol = merged.retries;
console.log("[5]", { ...defaults, ...empty }.retries);
```

- 기본 판의 검사 진단은? 방출해서 node 로 돌리면 `[1]`~`[5]` 는 각각 무엇을 찍는가? `--exactOptionalPropertyTypes` 판에서는 어느 줄이 새로 막히는가?

### 4. 한 장에 두 플래그의 네 조합 (예측)

```ts
// cost41.ts
// 두 플래그 없이 통과하던 코드를 흉내 낸 한 장
interface Row {
    id: string;
    note?: string;
}
const rows: Row[] = [{ id: "a" }, { id: "b", note: "x" }];
const byId: Record<string, Row> = {};
for (const r of rows) byId[r.id] = r;

function firstId(list: Row[]): string {
    return list[0].id;
}
function noteOf(id: string): string {
    return byId[id].note ?? "";
}
function total(xs: number[]): number {
    let t = 0;
    for (let i = 0; i < xs.length; i++) t += xs[i];
    return t;
}
function update(r: Row, note: string | undefined): Row {
    return { ...r, note: note };
}
function clear(r: Row) {
    r.note = undefined;
}
const [head] = rows;
console.log(firstId(rows), noteOf("a"), total([1, 2]), update(head, undefined), clear(head));
export {};
```

- 둘 다 끔 · `noUncheckedIndexedAccess` 만 · `exactOptionalPropertyTypes` 만 · 둘 다 — 네 조합에서 진단은 몇 건이고 어느 줄인가?

### 5. 길이를 검사한 루프 (왜)

- `for (let i = 0; i < arr.length; i++)` 안의 `arr[i]` 에 대해 `noUncheckedIndexedAccess` 는 무엇이라 말하는가? 루프 조건 `i < arr.length` 가 그 판단에 쓰이는가?

### 6. 튜플·`Record`·`for…of`·`.at()` (경계)

- 1번에서 튜플의 자리 · 키가 `"a" | "b"` 인 `Record` · `for…of` 의 원소 · `.at()` 는 각각 켬/끔에 어떻게 반응하는가? 레퍼런스의 「un-declared field」라는 말로 경계를 그어라.

### 7. `given` 과 `empty` (왜)

- 3번의 두 값을 `in`·`Object.keys`·`JSON.stringify`·스프레드로 견주면 어디서 같고 어디서 다른가? 까닭은? 「`undefined` 나 없는 거나 같다」가 어디서 사고가 되는지 `[4]` 와 12행으로 답하라.

### 8. 막는 방향 (경계)

- `exactOptionalPropertyTypes` 는 선택 프로퍼티의 **쓰기**와 **읽기** 중 어느 쪽을 바꾸는가? `undefined` 를 받게 하고 싶으면 무엇을 적는가?

### 9. `strict` 와의 관계 (경계)

- `"strict": true` 로 두 플래그가 켜지는가? 세 판의 도움말과 07편 4절로 답하라.

### 10. 07·40·39 와 잇기 (연결)

- 2번의 5행 코드는 07편 4절의 어느 진단과 같은가?
- 4번에서 `!` 를 줄마다 붙여 진단을 없애면 40편의 어느 결론으로 돌아가는가?
- 9번의 답은 39편의 탐침 격자와 무엇이 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
