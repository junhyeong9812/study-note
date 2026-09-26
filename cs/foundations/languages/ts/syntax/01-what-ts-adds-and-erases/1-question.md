# ts/syntax/01 — TS 가 더하는 것과 지우는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드를 컴파일하면 무엇이 나오는가**」를 묻는다.
> ★★ 이 주제에서 예측할 것은 **둘**이다 — ① `tsc` 가 무슨 진단을 내나 ② **방출된 `.js` 에 무엇이 남나**.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 답을 적고 시작한다. 방출 결과는 **줄 단위로** 적어 본다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 모든 블록은 `--pretty false` 로, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 표기를 모아 놓고 돌리면 (예측)

```ts
// ex.01a.ts
// 타입에만 속하는 표기를 모아 놓고, 방출된 JS 에 무엇이 남는지 본다
type Id = string;
type Handler<T> = (value: T) => void;
interface User {
    id: Id;
    name: string;
    nickname?: string;
}

function greet(u: User): string {
    return "안녕 " + u.name;
}

const onUser: Handler<User> = (u) => console.log(greet(u));
const raw = JSON.parse('{"id":"u-1","name":"준"}') as User;
const size = { w: 10, h: 20 } satisfies Record<string, number>;
let count!: number;
count = 3;

onUser(raw);
console.log(size.w, count);
```

- `tsc ex.01a.ts` 의 **종료 코드**는 무엇이고, 방출된 `ex.01a.js` 는 **몇 줄**인가?
- `type`·`interface`·`as`·`satisfies`·`!` 중 방출에 **흔적을 남기는 것**이 하나라도 있는가?

### 2. TS 고유 문법 넷을 돌리면 (예측)

```ts
// ex.01b.ts
// TS 고유 문법 넷 — 이것들은 방출에서 사라지지 않는다
enum Color {
    Red,
    Green,
}
const enum Dir {
    Up,
    Down,
}
namespace Config {
    export const retry = 3;
}
class Point {
    constructor(public x: number, private y: number) {}
    sum() {
        return this.x + this.y;
    }
}

console.log(Color.Red, Color[0], Dir.Up, Config.retry, new Point(1, 2).sum());
```

- 방출된 `ex.01b.js` 에서 네 선언(`enum`·`const enum`·`namespace`·생성자)이 각각 **어떤 JS** 가 되는가?
- `node ex.01b.js` 의 출력 **다섯 칸**을 적어 보라 — 특히 둘째 칸(`Color[0]`)이 무엇인가?

### 3. 컴파일러에게 세어 달라고 하면 (예측)

- 위 `ex.01b.ts` 를 `tsc --erasableSyntaxOnly --noEmit ex.01b.ts` 로 던지면 **에러가 몇 건**이고 **어느 줄·어느 칸**을 가리키는가?
- 같은 플래그로 1번의 `ex.01a.ts` 를 던지면 **몇 건**인가?

### 4. 두 `enum` 이 갈리는 자리 (경계)

- `enum` 과 `const enum` 중 **방출에 선언이 남는 쪽**은 어느 것이고, 안 남는 쪽은 사용처에 **무엇을 남기는가**?
- 그 차이가 「소거된다 / 안 된다」의 **둘로 갈리지 않는** 이유를 한 문장으로 말할 수 있는가?

### 5. 타입 이름을 값 자리에 쓰면 (예측)

```ts
// ex.01c.ts
// 타입은 값이 아니다 — 값 자리에 쓰면 무엇이라고 하나
interface User {
    id: string;
}
type Id = string;

function isUser(v: unknown): boolean {
    return v instanceof User;
}
const kind = typeof Id;
console.log(isUser({}), kind);
```

- 에러는 **몇 건**이고 **에러 코드**는 무엇인가?
- `interface` 는 걸리는데 **`class` 는 안 걸리는** 이유를 한 문장으로 말할 수 있는가?

### 6. 두 가지 import 를 돌리면 (예측)

```ts
// ex.01e.ts
// 타입만 쓰는 이름은 import 목록에서 지워진다
import { Shape, Circle } from "./ex.01e-lib.js";
import type { Shape as Shape2 } from "./ex.01e-lib.js";

const s: Shape = new Circle(2);
const t: Shape2 = s;
console.log(s.area(), t.area());
```

- 방출된 `ex.01e.js` 의 **첫 줄**은 어떻게 생겼고, **둘째 줄**은 어디로 갔는가?
- `import type` 을 안 썼다면 이 판의 방출이 **달라졌겠는가**?

### 7. 데코레이터를 붙여 돌리면 (예측)

```ts
// ex.01f.ts
// 레거시 데코레이터는 지워지기는커녕 헬퍼 함수를 덧붙인다
function log(_target: unknown, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    desc.value = function (this: unknown, ...args: unknown[]) {
        console.log("호출:", key);
        return orig.apply(this, args);
    };
}

class Svc {
    @log
    run(n: number) {
        return n * 2;
    }
}

console.log(new Svc().run(21));
```

- 옵션 없이 `tsc --noEmit ex.01f.ts` 를 던지면 무엇이라고 하는가?
- `--experimentalDecorators` 를 켜면 방출된 파일이 원본보다 **길어지는가 짧아지는가**, 그리고 `node` 출력의 **첫 줄**은 무엇인가?

### 8. 타입으로 할 수 없는 검사 (왜)

- `JSON.parse` 로 받은 값이 `User` 인지 **타입으로는 왜 확인할 수 없는지** 설명하고, 대신 무엇을 쓰는지 셋 이상 댈 수 있는가?

### 9. `enum` 을 쓰면 무엇을 치르나 (경계)

- `enum` 하나를 쓸 때 **방출에서 치르는 비용**과 **런타임에 생기는 객체**를 각각 말할 수 있는가?

### 10. `private` 이 감추는 것과 못 감추는 것 (경계)

- TS 의 `private` 과 JS 의 `#` 중 **방출된 파일에서 이름이 사라지는 쪽**은 어느 것인가?
- 매개변수 프로퍼티에 붙은 `private` 은 방출에서 **어떤 줄**이 되는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판(7.0.2)·이 옵션의 관찰** · **설정에 달린 것**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

### 12. 다음 주제로 넘어가는 자리 (연결)

- 「타입이 런타임에 없다」는 사실에서 「**타입 에러가 있어도 `.js` 가 나온다**」가 왜 따라 나오는지 한 문장으로 이을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
