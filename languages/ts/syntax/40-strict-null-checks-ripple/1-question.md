# ts/syntax/40 — `strictNullChecks` 의 파급 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **40 은 12 와 39 에서 온다** — [**12번 주제**](../12-narrowing/)가 좁히기 수단과 「`--strict false` 로 갈리는 칸」을, [**39번 주제**](../39-strict-bundle/)가 `strictNullChecks` 가 하위 플래그의 축인 것을 이미 쟀다.
> 여기서는 그 스위치를 **끈 쪽이 실행에서 무엇이 되나**를 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 1·2번의 탐침은 **하나씩 따로** 컴파일하고 따로 돌린다. node 에는 `document` 가 없어 `nn40d` 는 **`node -r ./shim40.cjs`** 로 대역을 먼저 싣는다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 탐침 여섯, 켠 판 (예측)

```ts
// nn40a.ts
interface Profile {
    nick?: { text: string };
}
const profile: Profile = {};
try {
    const len = profile.nick?.text.length;
    console.log("[a]", len.toFixed(0));
} catch (e) {
    console.log("[a]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40b.ts
const scores = [40, 55, 62];
try {
    const hit = scores.find((n) => n > 90);
    console.log("[b]", hit.toFixed(1));
} catch (e) {
    console.log("[b]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40c.ts
const labels = new Map<string, string>([["ko", "한국어"]]);
try {
    console.log("[c]", labels.get("en").toUpperCase());
} catch (e) {
    console.log("[c]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40d.ts
try {
    const el = document.querySelector(".banner");
    console.log("[d]", el.textContent);
} catch (e) {
    console.log("[d]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40e.ts
function lookup(id: number): string | undefined {
    return id === 1 ? "one" : undefined;
}
try {
    console.log("[e]", lookup(2).length);
} catch (e) {
    console.log("[e]", (e as Error).constructor.name, (e as Error).message);
}
```

```ts
// nn40f.ts
function shout(word?: string) {
    return word.toUpperCase();
}
try {
    console.log("[f]", shout());
} catch (e) {
    console.log("[f]", (e as Error).constructor.name, (e as Error).message);
}
```

```js
// shim40.cjs
// node 에는 document 가 없다 -- 찾는 요소가 없는 페이지를 흉내 내는 한 줄짜리 대역
globalThis.document = { querySelector: () => null };
```

- 7.0.2 기본(플래그 없음)으로 `tsc --noEmit -t es2022 <탐침>` 을 하나씩 던지면 각각 어느 줄에 어느 코드가 나는가? 코드는 몇 가지로 갈리고, 무엇이 가르는가?

### 2. 같은 여섯, 끈 판 — 방출해서 돌리면 (예측)

- 같은 탐침을 `--strictNullChecks false` 로 검사하면 진단은? 그 설정으로 방출한 `.js` 를 `node -r ./shim40.cjs` 로 돌리면 여섯은 각각 무엇을 찍는가? 켠 판에서 방출한 `.js` 와 끈 판에서 방출한 `.js` 는 같은가?

### 3. 대입 셋과 탐침 넷 (예측)

```ts
// absorb40.ts
let n: number = null;
let s: string = undefined;
const xs: number[] = [1, null, undefined];
declare const maybe: number | null;
declare const opt: { tag?: string };
const p1: symbol = maybe;
const p2: symbol = opt.tag;
const p3: symbol = xs.find((x) => x > 1);
declare const u: undefined;
const p4: null = u;
export {};
```

- 켠 판과 `--strictNullChecks false` 판에서 1·2·3행은 각각 통과하는가? 6·7·8행의 진단 문구에 나오는 타입과 10행은?

### 4. 좁히기 다섯 자리 (예측)

```ts
// flow40.ts
declare const found: number | undefined;
const p0: symbol = found;
if (found !== undefined) {
    const p1: symbol = found;
}
if (found) {
    const p2: symbol = found;
}
const p3: symbol = found ?? 0;
const p4: symbol = found?.toFixed(1);
const p5: symbol = found!;
export {};
```

- 켠 판에서 2·4·7·9·10·11행의 탐침은 각각 어느 타입을 말하는가?

### 5. 네 수단을 실행하면 (예측)

```ts
// bang40.ts
const scores = [40, 55, 62];
const hit = scores.find((n) => n > 90);
const a = hit !== undefined ? hit.toFixed(1) : "none";
const b = hit?.toFixed(1) ?? "none";
const c = hit!;
console.log("[1]", a, b, c);
try {
    console.log("[2]", hit!.toFixed(1));
} catch (e) {
    console.log("[2]", (e as Error).constructor.name, (e as Error).message);
}
```

- 켠 판의 검사 진단은? 방출물에서 `c` 줄과 `[2]` 줄은 어떻게 적히고, node 는 `[1]`·`[2]` 로 무엇을 찍는가?

### 6. `?.` 를 썼는데 (왜)

- `nn40a` 는 `profile.nick?.text.length` 로 `?.` 를 썼다. `?.` 는 어디까지를 지키고, 그 **결과**의 타입은 무엇인가? 그것으로 1·2번의 `nn40a` 칸을 설명하라.

### 7. 탐침의 과녁 (왜)

- 형제 편들은 `const p: null = …` 로 타입을 뽑는데, 3·4번은 `const p: symbol = …` 을 썼다. 3번 10행으로 그 까닭을 설명하라.

### 8. 스위치가 바꾸는 층 (경계)

- 「`strictNullChecks` 를 켜면 런타임 검사가 추가된다」는 맞는가? 2번의 방출물 대조와 5번의 `!` 로 답하라.

### 9. 비어 있는 값의 두 이름 (경계)

- 1·2번에서 **`null`** 이 흘러간 탐침과 **`undefined`** 가 흘러간 탐침을 가르라. 「`find` 는 못 찾으면 `null`」은 맞는가?

### 10. 12·30·37·Kotlin·C# 과 잇기 (연결)

- 3번의 6행 결과는 12편 5절의 어느 칸과 같은 모양인가?
- 5번의 `[2]` 는 30편 2절의 어느 결과와 같은 칸인가?
- 2번은 37편 2절의 어느 문장과 같은 모양인가?
- Kotlin [`../../../kotlin/syntax/03-null-safe-types/`](../../../kotlin/syntax/03-null-safe-types/)의 `!!` 와 C# [`../../../csharp/syntax/06-nullable-reference-types/`](../../../csharp/syntax/06-nullable-reference-types/)의 `string?` 중 TS 의 `strictNullChecks` 는 어느 쪽에 가까운가 — 런타임에 무엇이 남느냐로 답하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
