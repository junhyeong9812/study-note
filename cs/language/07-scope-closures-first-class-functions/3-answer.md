# language/07-scope-closures-first-class-functions — 정답

## 정답

### 1. 환경이 힙에 남는다

```text
  전역 { counter, c1, c2 }
     ▲                ▲
  호출#1 { n: 2 }    호출#2 { n: 1 }
     ▲                ▲
   c1.inc            c2.inc
```

- 클로저는 만들어질 때의 환경 레코드를 가리킨다. 그 환경은 스택 프레임이 아니라 힙 객체로 살아 있다.
- `counter()`를 부를 때마다 새 환경이 생긴다. 그래서 `c1`과 `c2`는 다른 `n`을 본다(실험 A `c1: 2 c2: 1`).

### 2. 루프 클로저

- JS: `var: 3,3,3`, `let: 0,1,2`(실험 A). `var`는 함수 전체에 변수 하나, `let`의 `for`는 반복마다 새 환경(ECMAScript 2024 14.7.4.4).
- Python: `[2, 2, 2]`. 클로저가 변수(셀)를 캡처하고 호출 시점에 읽는다.
- 고침: JS는 `let`. Python은 `lambda i=i: i`(실험 `default arg : [0, 1, 2]`)나 `functools.partial`.

### 3. 캡처 대상

| 언어 | 캡처 대상 |
|---|---|
| JS | 변수(환경 칸) |
| Python | 변수(셀) — 다시 대입하려면 `nonlocal` |
| Java 람다 | effectively final 변수의 값 |
| Rust | 빌림(`&`·`&mut`) 또는 이동(`move`) — `Fn`/`FnMut`/`FnOnce` |

- JLS 15.27.2: "The restriction to effectively final variables prohibits access to dynamically-changing local variables, whose capture would likely introduce concurrency problems."

### 4. 클로저 변환 결과

- `x -> x + base`: `private static int lambda$main$2(int, int)`. `base`가 추가 매개변수가 됐다. 생성 지점은 `invokedynamic … applyAsInt:(I)Ljava/util/function/IntUnaryOperator;` — 캡처 값 `int` 하나를 받는다.
- `() -> payload.length`: `private java.lang.Integer lambda$usesField$0()`(인스턴스 메서드). 생성 지점은 `invokedynamic … get:(LCapture;)Ljava/util/function/Supplier;` — `this`를 받는다.
- 실행 중 람다 객체의 필드: 첫째는 정수 값, 둘째는 `Capture arg$1`(실험 B `captured fields: [Capture arg$1; ]`). 아무것도 안 쓰는 람다는 필드가 없다.

### 5. 익명 클래스의 `this$0`

- 바깥을 쓰지 않는 `Anon$1`: 없다(`class Anon$1 … { Anon$1(Anon); public void run(); }`).
- 바깥 필드를 쓰는 `Anon$2`: 있다(`final Anon this$0;`).
- JDK 18에서 바뀌었다(JDK 18 릴리스 노트 "Enclosing Instance Fields Omitted from Inner Classes That Don't Use Them", JDK-8271623). 그 전 javac는 쓰지 않아도 항상 `this$0`을 만들었다. 생성자에는 여전히 `Anon` 매개변수가 있다(노트: "the form of the inner class constructor is not affected").

### 6. V8 문맥 공유

- 회수되지 않는다. 실험 C: `shared closures=10 heapUsed 증가 = 152.6 MiB`, `alone`은 `-0.0 MiB`.
- 실행되지 않는 분기 안에 있어도 붙잡혔다(첫 시도에서 `alone`도 152.6 MiB). 캡처 여부는 실행이 아니라 소스 구조로 정해진다.
- 해석: V8이 한 스코프의 캡처 변수를 문맥 하나에 모으고, 같은 스코프에서 만든 클로저들이 그 문맥을 공유한다고 본다. `heapUsed`는 보유량만 보이므로 정확한 보유 경로는 힙 스냅숏으로 확인해야 한다(이 실험은 하지 않았다). V8 구현 동작이며 명세 요구가 아니다.

### 7. 람다가 요청 객체를 붙잡음

- 원인: 람다 본문이 인스턴스 필드(`this.requestContext…`)를 써서 `this`를 캡처했다. 그 람다가 오래 사는 이벤트 버스·리스너 목록에 등록되어 해제되지 않았다. 람다 → `this` → 요청 객체 전체가 GC 루트에서 도달 가능하다.
- 수정 방향
  - 필요한 값만 지역 변수로 복사해 캡처한다(`String userId = …; register(evt -> Audit.log(evt, userId))`). 호출하는 `log`가 인스턴스 메서드면 다시 `this`를 캡처하므로 static 메서드나 따로 캡처한 로거를 쓴다.
  - 등록 해제 경로를 만든다(`AutoCloseable` 핸들, `try/finally`).
  - 확인: `javap -p`로 캡처 필드, 힙 덤프 지배자 트리로 보유 경로([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)).

### 8. 캡처한 배열 칸 경쟁

- 결과: 대개 200만보다 적고 실행마다 다르다. 실험 D(`--cpus=2`): 1,787,539 / 1,456,068 / 1,616,233. 사실 점검 재실행 9라운드 중 유실이 난 8라운드는 1,323,530 ~ 1,834,261이었고 나머지 1라운드는 2,000,000이었다(겹치지 않으면 맞을 수도 있다 — 그래서 더 위험하다). `AtomicInteger`는 매번 2,000,000.
- 컴파일 통과 이유: 변수 `box`(배열 참조)는 다시 대입하지 않아 effectively final이다. 제한은 변수에만 걸리고 배열 칸에는 걸리지 않는다.
- 고침: `AtomicInteger`·`LongAdder`, 또는 공유 칸 없이 리덕션으로 센다(건수는 `IntStream.range(0, N).parallel().count()` — `.sum()`은 건수가 아니라 인덱스의 합이다).
