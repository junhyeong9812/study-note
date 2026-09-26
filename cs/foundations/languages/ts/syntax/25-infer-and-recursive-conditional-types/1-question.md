# ts/syntax/25 — `infer` 와 재귀 조건부 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **22 → 24 → 25 는 한 사슬이고 여기가 급소다** —
> [**24번 주제**](../24-conditional-types-and-distribution/)의 조건부를 떠올리지 못하면 답이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `javac` **21.0.5** · `rustc` **1.92.0**.
> 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — `infer` 는 **2.8**, 꼬리 재귀 꼴의 완화는 **4.5**, `infer X extends …` 는 **4.8** 이다.
> **7.0 에서 도는지는 던져서 확인했다.**
>
> ★★★ **계산된 타입을 눈으로 보는 법** — 블록에 `const probe: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★★ **그런데 이 주제에서는 탐침이 자주 침묵한다** — 답이 `never` 면 `null` 에도 할당되므로 **진단이 아예 안 난다.**
> 그래서 소스마다 `type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다"` 가 끼어 있다.
> **「진단이 없는 줄」도 답이다** — 그 줄이 무엇인지 함께 예측해라.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ 이 주제의 **본체 창은 4창(종료 코드 격자)이다** — 5·6번이 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 다섯 자리에 빈칸을 뚫으면 (예측)

```ts
// ex.25a.ts
// infer 로 뽑기 -- 요소 · 반환 · 매개변수 · 생성자, 그리고 안 맞으면 조용히 never
type Elem<T> = T extends (infer U)[] ? U : never;
type Ret<T> = T extends (...args: never[]) => infer R ? R : never;
type Par<T> = T extends (...args: infer P) => unknown ? P : never;
type Inst<T> = T extends new (...args: never[]) => infer I ? I : never;
type Head<T> = T extends [infer H, ...unknown[]] ? H : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const fromArray: null = null as unknown as Elem<string[]>;
const fromTuple: null = null as unknown as Elem<[1, "가"]>;
const fromReturn: null = null as unknown as Ret<(x: number) => string>;
const fromParams: null = null as unknown as Par<(x: number, y: string) => void>;

class Point {
    constructor(public x: number) {}
}
const fromCtor: null = null as unknown as Inst<typeof Point>;
const fromHead: null = null as unknown as Head<[1, 2, 3]>;

const silent: null = null as unknown as Elem<string>;
const silentNamed: null = null as unknown as IsNever<Elem<string>>;
const readonlyTuple: null = null as unknown as IsNever<Elem<readonly [1, "가"]>>;
console.log(fromArray, fromTuple, fromReturn, fromParams, fromCtor, fromHead, silent, silentNamed, readonlyTuple);
```

- 9·10·11·12행이 각각 무엇을 뱉는가? 12행은 **뜻밖의 것이 하나 딸려 온다**.
- 17행 `Inst<typeof Point>` 는 무엇인가? 그것이 [**23번 주제**](../23-typeof-type-operator/)와 어디서 만나는가?
- **진단이 없는 줄이 하나 있다.** 몇 행이고 왜 없는가?

### 2. 같은 이름을 두 자리에 쓰면 (예측)

```ts
// ex.25b.ts
// infer 가 여러 자리에 있으면 -- 공변 자리는 유니온, 반공변 자리는 교차
type Co<T> = T extends { a: infer U; b: infer U } ? U : never;
type Contra<T> = T extends { a: (x: infer U) => void; b: (x: infer U) => void } ? U : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const covariant: null = null as unknown as Co<{ a: string; b: number }>;
const contravariant: null = null as unknown as Contra<{ a: (x: { p: 1 }) => void; b: (x: { q: 2 }) => void }>;

type Clash = Contra<{ a: (x: string) => void; b: (x: number) => void }>;
const clashSilent: null = null as unknown as Clash;
const clashNamed: null = null as unknown as IsNever<Clash>;

type CoSame<T> = T extends { a: infer U; b: infer U } ? U : never;
const coSame: null = null as unknown as CoSame<{ a: "가"; b: "가" }>;
console.log(covariant, contravariant, clashSilent, clashNamed, coSame);
```

- 6행과 7행의 답을 나란히 적을 수 있는가? **합치는 법이 왜 다른가**?
- 10행과 11행은 같은 타입을 묻는다. **왜 한 줄만 말을 하는가**?
- 14행은 두 자리가 같은 타입이다. 벌어지는가?

### 3. 조각 하나를 붙이면 (예측)

```ts
// ex.25c.ts
// infer X extends -- 뽑으면서 좁힌다
type NumOf<S> = S extends `${infer N extends number}` ? N : never;
type NumOfPlain<S> = S extends `${infer N}` ? N : never;
type FirstChar<S> = S extends `${infer C}${string}` ? C : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const narrowed: null = null as unknown as NumOf<"42">;
const notNarrowed: null = null as unknown as NumOfPlain<"42">;
const notANumber: null = null as unknown as IsNever<NumOf<"가">>;
const firstChar: null = null as unknown as FirstChar<"가나다">;

type HeadStr<T> = T extends [infer H extends string, ...unknown[]] ? H : never;
const headOk: null = null as unknown as HeadStr<["가", 1]>;
const headNo: null = null as unknown as IsNever<HeadStr<[1, "가"]>>;
console.log(narrowed, notNarrowed, notANumber, firstChar, headOk, headNo);
```

- 7행과 8행의 답이 어떻게 다른가? 차이를 만든 것은 무엇인가?
- 9행은 왜 `IsNever` 를 거쳐 묻는가?
- 13행과 14행 중 **한쪽만 값이 나온다.** 어느 쪽이고 왜인가?

### 4. 한 겹씩 벗기면 (예측)

```ts
// ex.25d.ts
// 재귀 조건부 -- 문자열 쪼개기 · 튜플 뒤집기 · Awaited · 템플릿 리터럴
type Split<S extends string, D extends string> =
    S extends `${infer H}${D}${infer R}` ? [H, ...Split<R, D>] : [S];
type Rev<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [...Rev<R>, H] : [];
type Join<T extends readonly string[], D extends string> =
    T extends [infer H extends string, ...infer R extends string[]]
        ? R extends [] ? H : `${H}${D}${Join<R, D>}`
        : "";
type MyAwaited<T> = T extends Promise<infer U> ? MyAwaited<U> : T;

const split: null = null as unknown as Split<"가.나.다", ".">;
const reversed: null = null as unknown as Rev<[1, 2, 3, 4]>;
const joined: null = null as unknown as Join<["가", "나", "다"], "-">;
const roundTrip: null = null as unknown as Join<Split<"가.나.다", ".">, "-">;

const mine: null = null as unknown as MyAwaited<Promise<Promise<number>>>;
const stock: null = null as unknown as Awaited<Promise<Promise<Promise<string>>>>;
const notPromise: null = null as unknown as Awaited<number>;
console.log(split, reversed, joined, roundTrip, mine, stock, notPromise);
```

- 11·12·13행이 각각 무엇을 뱉는가?
- 14행은 13행과 같은가 다른가? 그 사실이 무엇을 말하는가?
- 17행 `Awaited<Promise<Promise<Promise<string>>>>` 는 몇 겹을 벗기는가?

### 5. 길이를 한 칸 올리면 (예측)

```ts
// ex.25e.ts
// 재귀가 어디서 멈추나 -- 길이를 올려 가며 TS2589 를 직접 받는다
type Count<N extends readonly unknown[], Stop extends number> =
    N["length"] extends Stop ? N : Count<[...N, 1], Stop>;

type Ok = Count<[], 999>;
const okLen: null = null as unknown as Ok["length"];

type TooDeep = Count<[], 1000>;
const deepLen: null = null as unknown as TooDeep["length"];

type Endless<T extends readonly unknown[]> = Endless<[...T, 1]>;
type Never = Endless<[]>;
console.log(okLen, deepLen, null as unknown as Never);
```

- 6행과 8행 중 어느 쪽이 벽에 닿는가? 진단 코드는 무엇인가?
- **9행에 진단이 없다.** 왜인가?
- 11행 `Endless` 는 5·8행과 **같은 진단인가 다른 진단인가**?

### 6. 네 가지 꼴을 같은 길이로 던지면 (예측)

```bash
# ts22b-depth.sh
#!/usr/bin/env bash
# 재귀 조건부의 한계를 격자로 친다 -- 네 가지 꼴 x 다섯 가지 길이
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
tup() { local n=$1 i; printf '['; for ((i=1;i<=n;i++)); do printf '1'; ((i<n)) && printf ', '; done; printf ']'; }
decl_A='type A<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];'
decl_B='type B<T extends readonly unknown[], Acc extends readonly unknown[] = []> = T extends [infer H, ...infer R] ? B<R, [H, ...Acc]> : Acc;'
decl_C='type C<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [C<R>, H] : [];'
decl_E='type E<T extends readonly unknown[]> = T extends [unknown, ...infer R] ? { n: E<R> } : null;'
echo 'A  꼬리 아님 + 튜플 스프레드    type A<T> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];'
echo 'B  꼬리 + 누산기 스프레드      type B<T, Acc = []> = T extends [infer H, ...infer R] ? B<R, [H, ...Acc]> : Acc;'
echo 'C  꼬리 아님 + 스프레드 없음   type C<T> = T extends [infer H, ...infer R] ? [C<R>, H] : [];'
echo 'E  꼬리 아님 + 객체로 감쌈     type E<T> = T extends [unknown, ...infer R] ? { n: E<R> } : null;'
echo
echo '길이 |       A       |       B       |       C       |       E'
echo '-----+---------------+---------------+---------------+---------------'
for n in 48 49 500 999 1000; do
  row=$(printf '%4s |' "$n")
  for k in A B C E; do
    eval "d=\$decl_$k"
    { echo "$d"; echo "type Deep = $k<$(tup "$n")>;"; echo 'declare const p: Deep;'; echo 'export { p };'; } > "$D/probe.ts"
    out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/probe.ts" 2>&1); rc=$?
    case "$out" in *TS2589*) mark="TS2589 exit=$rc";; '') mark="OK     exit=$rc";; *) mark="OTHER  exit=$rc";; esac
    row="$row $(printf '%-14s' "$mark")|"
  done
  echo "${row%|}" | sed "s/ *$//"
done
```

- 네 꼴 중 **가장 먼저 막히는 것**은 어느 것인가?
- **C 와 E 는 꼬리 재귀가 아니다.** 그런데도 어떻게 되는가?
- 이 격자가 「깊이 한계」라는 이름에 대해 무엇을 말하는가?

### 7. 서식이 안 맞았을 때 왜 에러가 아닌가 (왜)

- 1번 20행을 근거로 **한 문장**으로 댈 수 있는가?
- 그 설계가 문법상 **왜 그럴 수밖에 없는지** 말할 수 있는가?

### 8. 탐침이 `never` 앞에서 침묵하는 이유 (왜)

- `const probe: null = null as unknown as never;` 가 왜 통과하는가?
- 그래서 이 주제가 **창을 어떻게 바꿔** 물었는가?

### 9. `TS2589` 와 `TS2456` 의 경계 (경계)

- 둘은 각각 **무엇이 잘못됐을 때** 나는가?
- 재귀 타입을 짜다 `TS2589` 를 만났을 때 **무엇부터 확인해야** 하는가?

### 10. 재귀 조건부를 쓸 자리와 안 쓸 자리 (경계)

- 「길이가 입력에 따라 커지는 것」에 재귀 조건부를 쓰면 무엇이 기다리는가?
- **경계 길이를 외워서 쓰면 안 되는 이유**는 무엇인가?

### 11. Java 의 포획·Rust 의 연관 타입과 잇기 (연결)

```java
// Capture.java
import java.util.List;

public class Capture {
    static void copyFirstBack(List<?> xs) {
        xs.set(0, xs.get(0));
    }

    static <T> void copyFirstBackNamed(List<T> xs) {
        xs.set(0, xs.get(0));
    }

    static void addToBounded(List<? extends CharSequence> xs) {
        xs.add("가");
    }
}
```

```rust
// assoc.rs
// 이름으로 뽑는다 -- Rust 는 트레이트가 미리 선언한 연관 타입만 꺼낼 수 있다
trait Source {
    type Item;
    fn get(&self) -> Self::Item;
}

struct Counter;

impl Source for Counter {
    type Item = u32;
    fn get(&self) -> u32 {
        7
    }
}

fn pull<S: Source>(s: &S) -> S::Item {
    s.get()
}

fn main() {
    let c = Counter;
    let probe: u8 = pull(&c);
    println!("{}", probe);
}
```

- javac 의 `CAP#1` 은 TS 의 무엇에 해당하는가? **무엇이 다른가**?
- Java 파일에서 **진단이 없는 메서드가 하나** 있다. 어느 것이고 왜 통과하는가?
- Rust 의 `S::Item` 과 TS 의 `infer U` 를 가르는 **한 낱말**은 무엇인가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **구현(tsc 7.0.2) 층** · **이 판의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?
- 이 문서에 **「느리다」는 말이 한 줄도 없는 이유**는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
