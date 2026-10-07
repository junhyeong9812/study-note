# language/07-scope-closures-first-class-functions — 1급 함수·클로저·람다: 함수가 환경을 들고 다닌다 — 정리 (힌트)

## 해결하는 문제

함수를 값처럼 넘기고 나중에 부르려면, 그 함수가 **만들어진 곳의 변수**를 기억해야 한다.

```text
  function counter() {            const c1 = counter();
    let n = 0;                    c1.inc(); c1.inc();
    return { inc: () => ++n };    → n은 counter()가 끝난 뒤에도 살아 있어야 한다
  }                                 (스택 프레임이 사라졌는데 어디에?)
```

- *1급 함수(first-class function)*: 함수를 변수에 담고, 인자로 넘기고, 반환할 수 있는 성질.
- *클로저(closure)*: 함수 코드 + 그 함수가 만들어질 때의 **환경(변수 묶음)** 에 대한 참조.
- *람다(lambda)*: 이름 없는 함수 식. 클로저를 만드는 흔한 문법이다.

쉬운 예: 레시피 카드와 냉장고다.
- 카드에 "냉장고의 우유 한 컵"이라고 적어 둔다. 카드를 친구에게 줘도 같은 냉장고를 가리킨다 → 변수 자체를 캡처(JS·Python).
- 카드에 "우유 200ml"라고 값을 적어 두면, 냉장고가 바뀌어도 카드는 그대로다 → 값을 캡처(Java 람다).
- 카드 한 장이 냉장고 전체를 붙잡고 있으면, 냉장고를 버릴 수 없다 → 클로저 메모리 누수.

똑같은 구조다.\
"무엇을 캡처하나(변수 vs 값)"와 "얼마나 붙잡나"가 운영 증상을 가른다.

실무 예:
- 스트림 연산·콜백·이벤트 리스너·비동기 핸들러에 넘기는 함수가 바깥 변수를 쓰면, 그 함수가 클로저다.
- 리스너로 등록한 람다가 요청 객체 전체를 붙잡아 힙이 계속 오른다.
- 람다 안에서 바깥 카운터를 올렸더니 병렬 실행에서 숫자가 모자란다.

람다 문법의 기초(파이썬 `lambda`는 식만 담고 `return`이 없다, 정렬 key로 쓰기)는 원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md) §9에 있다. 스코프 규칙(`global`·`nonlocal`, §3)은 [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md)가 잇는다.

## 동작·원리

### 1. 환경 레코드 체인 — 이름을 어디서 찾나

```text
  전역 환경          { counter: <fn>, c1: <obj>, c2: <obj> }
        ▲ outer                 ▲ outer
  counter() 호출 #1 { n: 2 }    counter() 호출 #2 { n: 1 }      ← 호출마다 새 환경
        ▲ [[Environment]]       ▲
  c1.inc 클로저                 c2.inc 클로저

  이름 n 찾기: 자기 환경 → outer → outer … → 전역 → 없으면 오류
```

- *환경 레코드(environment record)*: 이름 → 값 칸의 묶음. 함수 호출·블록마다 생긴다(ECMAScript 2024 9.1 "Environment Records").
- *스코프 체인*: 환경 레코드가 바깥 환경을 가리키는 사슬.
- 클로저는 만들어질 때의 환경을 가리킨다. 그래서 호출이 끝나도 그 환경은 힙에 남는다.
- SICP 3.2 "The Environment Model of Evaluation"이 이 모델을 프레임과 환경으로 설명한다(절 번호는 MIT Press 공개 HTML 목차로 확인).

### 실험 A: 호출마다 새 환경, 반복마다 새 환경

(실험, `node:22-alpine` v22.23.2 / 호스트 CPython 3.12.3, `scratchpad/lang/05/e07/loop.js`·`late.py`, 2026-10-07)

```text
JS     var: 3,3,3   let: 0,1,2
       c1: 2  c2: 1   (호출마다 새 환경)
Python late binding : [2, 2, 2]
       default arg  : [0, 1, 2]
       closure cell : 1  co_freevars: ('x',)
```

```text
  for (var i …)                        for (let j …)
  함수 환경 { i: 3 }  ← 하나            반복 #0 { j: 0 }  반복 #1 { j: 1 }  반복 #2 { j: 2 }
    ▲   ▲   ▲                              ▲               ▲               ▲
   f0  f1  f2   → 모두 3                  f0              f1              f2
```

- `var`는 함수 단위 변수 하나다. 세 클로저가 같은 `i`를 보고, 반복이 끝난 뒤의 값 3을 읽는다.
- `let`을 쓴 `for`는 반복마다 새 환경을 만들고 값을 복사한다(ECMAScript 2024 14.7.4.4 CreatePerIterationEnvironment).
- Python 클로저도 **변수(셀)** 를 캡처한다. 호출 시점에 읽으므로 마지막 값 2가 나온다. 기본 인자 `i=i`는 정의 시점 값을 복사한다(Python 문서 Programming FAQ "Why do lambdas defined in a loop with different values all return the same result?").
  - *셀(cell)*: CPython이 클로저 변수를 담는 상자. `__closure__`·`co_freevars`로 보인다.
- Go 1.22부터 `for` 문이 `:=`로 선언한 루프 변수(`for i := …`, `for k, v := range …`)가 반복마다 새로 생긴다(Go 명세 "For statements": "Each iteration has its own separate declared variable"; 루프 밖 변수에 `=`로 대입하는 루프는 해당 없음; Go 1.22 릴리스 노트: "In Go 1.22, each iteration of the loop creates new variables"). 이 규칙은 `go.mod`의 `go` 지시어가 1.22 이상인 모듈의 패키지에만 적용된다(Go 블로그 "Fixing For Loops in Go 1.22", 세부는 [languages/go/syntax/13](../../../languages/go/syntax/13-closures-variable-capture-and-loop-variable-change/2-summary.md)).

### 2. 무엇을 캡처하나 — 변수 vs 값

| 언어 | 캡처 대상 | 바깥에서 나중에 바꾸면 | 안에서 바꾸기 |
|---|---|---|---|
| JS | 변수(환경 칸) | 보인다 | 가능 |
| Python | 변수(셀) | 보인다 | `nonlocal` 선언 필요 |
| Java 람다 | 값(effectively final만 허용) | 바꿀 수 없음(컴파일 오류) | 불가 |
| Rust | 빌림 또는 이동(`move`) — `Fn`/`FnMut`/`FnOnce` | 빌림 규칙이 막음 | 캡처 변수를 직접 바꾸면 `FnMut`(`Cell` 같은 내부 가변성은 `Fn`에서도 가능) |

- Java는 람다가 쓰는 지역 변수를 final 또는 effectively final로 제한한다(JLS 15.27.2).
  - JLS 15.27.2의 이유: "The restriction to effectively final variables prohibits access to dynamically-changing local variables, whose capture would likely introduce concurrency problems."
  - *effectively final*: `final`이라 쓰지 않았지만 초기화 뒤 다시 대입하지 않는 변수(JLS 4.12.4).
- Rust 클로저의 세 트레이트는 [languages/rust/syntax/34](../../../languages/rust/syntax/34-closures-fn-fnmut-fnonce-and-move/2-summary.md).

### 3. Java 람다는 어떻게 값을 캡처하나 — 클로저 변환

```text
  소스                                   javac 결과                           실행 중
  int base = 10;                         private static int lambda$main$2(int, int)   ← base가 매개변수로
  x -> x + base                          invokedynamic … applyAsInt:(I)IntUnaryOperator
                                                                              Capture$$Lambda 객체 { arg$1 = 10 }
  () -> payload.length  (인스턴스 필드)  private Integer lambda$usesField$0()   ← 인스턴스 메서드
                                         invokedynamic … get:(LCapture;)Supplier
                                                                              { arg$1 = this }  ← this 전체를 붙잡음
```

- *클로저 변환(closure conversion)*: 자유 변수를 객체 필드나 추가 매개변수로 옮겨, 환경 없이도 함수를 부를 수 있게 바꾸는 컴파일 기법.
- `invokedynamic`: 처음 실행될 때 부트스트랩 메서드(`LambdaMetafactory`)로 호출 지점을 연결하고(linkage), 그 뒤 실행될 때마다 캡처 값을 받아 함수 객체를 돌려주는(capture) JVM 명령(`LambdaMetafactory` API 문서의 세 단계: Linkage·Capture·Invocation). 생성된 클래스의 필드가 캡처한 값이다.

### 실험 B: 람다가 무엇을 붙잡았나

(실험, `eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e07/Capture.java`·`Anon.java`·`NotFinal.java`, 2026-10-07)

```text
add(5) = 15
Capture$$Lambda/…            captured fields: [Capture arg$1; ]     ← usesField(): this
Capture$$Lambda/…            captured fields: []                    ← noField(): 없음
                             captured fields: []                    ← 바깥을 안 쓰는 익명 클래스
javap -p -c
       1: invokedynamic #13,  0   // InvokeDynamic #0:get:(LCapture;)Ljava/util/function/Supplier;
       0: invokedynamic #17,  0   // InvokeDynamic #1:get:()Ljava/util/function/Supplier;
       4: invokedynamic #25,  0   // InvokeDynamic #2:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;
  private static int lambda$main$2(int, int);
  private static java.lang.Integer lambda$noField$1();
  private java.lang.Integer lambda$usesField$0();
javap -p Anon$1 / Anon$2
  class Anon$1 implements java.lang.Runnable { Anon$1(Anon); public void run(); }
  class Anon$2 implements java.lang.Runnable { final Anon this$0; Anon$2(Anon); public void run(); }
NotFinal.java:4: error: local variables referenced from a lambda expression must be final or effectively final
```

- 인스턴스 필드를 쓰는 람다는 `this` 전체를 붙잡는다. 필드 하나만 필요해도 객체 전체가 살아남는다.
- 바깥을 쓰지 않는 람다는 아무것도 붙잡지 않는다(정적 메서드로 컴파일).
- 익명 클래스: JDK 21 javac는 바깥 인스턴스를 쓰지 않는 익명 클래스에 `this$0` 필드를 만들지 않았다(`Anon$1`). 바깥 필드를 쓰면 만든다(`Anon$2`). 이 변화는 JDK 18 릴리스 노트의 "Enclosing Instance Fields Omitted from Inner Classes That Don't Use Them"(JDK-8271623)이다.
  - 흔한 오해: "익명 클래스는 항상 바깥 객체를 붙잡는다". JDK 17 이하 javac에서 만든 클래스 파일에는 맞는 말이다 — 릴리스 노트: "Prior to JDK 18, when javac compiles an inner class it always generates a private synthetic field … even if the inner class does not reference its enclosing instance". `java.io.Serializable` 하위 클래스는 JDK 18 이후에도 이 변경에서 제외된다(같은 노트). 확인은 `javap -p`로 `this$0` 필드를 본다.

### 4. 클로저가 생각보다 많이 붙잡는 경우 — V8의 문맥 공유

```text
  makeShared() 호출 환경(V8 Context) { big: Array(2,000,000) }
        ▲                         ▲
   unused = () => big.length    returned = () => 42        ← big을 안 쓰지만 같은 Context를 가리킴
   (버려짐)                      (살아남음 → big도 살아남음)
```

### 실험 C: big을 안 쓰는 클로저가 big을 붙잡는다

(실험, `node:22-alpine` v22.23.2, `node --expose-gc`, `scratchpad/lang/05/e07/leak.js`, 각 3회, 2026-10-07)

```text
alone   closures=10  heapUsed 증가 = -0.0 MiB
shared  closures=10  heapUsed 증가 = 152.6 MiB
(3회 모두 같은 값)
```

- 반환한 클로저는 두 경우 모두 `() => 42`다. 그런데 같은 함수 안에 `big`을 쓰는 다른 클로저가 **있기만 해도** `big`이 살아남았다.
- 해석: V8은 클로저가 캡처하는 변수를 스코프마다 문맥(Context) 하나에 모으고(V8 문서 "Scopes and ScopeInfos": 함수 문맥 외에 블록 문맥 등도 있다), 같은 스코프에서 만든 클로저들이 그 문맥을 공유한다. 그래서 한 클로저가 쓰는 변수를 다른 클로저도 붙잡는다고 본다. `heapUsed` 차이는 보유량만 보여 줄 뿐 보유 경로를 보여 주지 않는다 — 정확한 경로는 힙 스냅숏의 retainer로 확인해야 한다(이 실험에서는 하지 않았다). 이것은 ECMAScript 명세가 아니라 V8 구현 동작이다. 문맥 배정 알고리즘은 V8 소스로 확인하지 않았다 [?].
- 처음 시도에서는 `if (MODE === "shared")` 안에 `unused`를 두었는데, 실행하지 않는 분기여도 `big`이 붙잡혔다(`alone`도 152.6 MiB). 캡처 여부는 실행이 아니라 **소스 구조(정적 분석)** 로 정해진다는 증거다. 위 결과는 함수를 둘로 나눈 판이다.

### 5. 캡처한 가변 상태와 경쟁

```text
  스레드 1: 읽기 box[0]=5 ──── 더하기 6 ──── 쓰기 6
  스레드 2:        읽기 box[0]=5 ──── 더하기 6 ──── 쓰기 6     → 두 번 더했는데 1만 늘어남
```

- 람다가 같은 가변 칸을 캡처하고 여러 스레드에서 실행되면, 그 칸은 공유 메모리다.

### 실험 D: effectively final 우회 → 갱신 유실

(실험, `eclipse-temurin:21-jdk` 21.0.12 `--cpus=2`, `scratchpad/lang/05/e07/Race.java`, 2026-10-07)

```text
round 1: int[] box = 1,787,539   AtomicInteger = 2,000,000   (기대 2,000,000)
round 2: int[] box = 1,456,068   AtomicInteger = 2,000,000   (기대 2,000,000)
round 3: int[] box = 1,616,233   AtomicInteger = 2,000,000   (기대 2,000,000)
```

- 사실 점검 재실행(같은 환경, JVM 3회 × 3라운드): 9라운드 중 유실이 난 8라운드의 `int[] box`는 1,323,530 ~ 1,834,261이었고, 나머지 1라운드는 **2,000,000**(유실 없음)이었다. 경쟁은 겹칠 때만 드러나므로 한 번 맞았다고 안전한 것이 아니다. `AtomicInteger`는 9라운드 모두 2,000,000.

- `int[] box = {0}`은 effectively final(배열 참조가 안 바뀜)이라 컴파일된다. 하지만 배열 칸은 가변이다. 두 스레드의 `box[0]++`(읽기-더하기-쓰기)가 겹쳐 갱신이 사라졌다.
- JLS가 막으려던 "동적으로 바뀌는 지역 변수 캡처"를 배열로 우회하면, 막으려던 문제가 그대로 돌아온다.
- 경쟁 조건 일반은 [os/15-race-conditions](../../os/15-race-conditions/2-summary.md), 메모리 모델은 [13-language-memory-model](../13-language-memory-model/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **환경 레코드 체인**(설명용 모델 — 명세의 환경 레코드는 추상 모델이고, V8은 컴파일 때 슬롯 번호를 정해 배열 같은 `Context` 칸으로 읽는다): 각 환경 = 이름 → 칸 해시 맵, 환경끼리는 바깥을 가리키는 연결 리스트([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)). 이름 찾기는 사슬을 따라 올라간다.
  - 컴파일 시점에는 같은 구조를 "해시 테이블 스택"(심벌 테이블)으로 쓴다 — [language 04](../04-semantic-analysis-and-scopes/2-summary.md).
- **클로저 변환**: 자유 변수 집합을 계산해(함수 본문에서 쓰이지만 선언되지 않은 이름) 객체 필드로 옮긴다. Java `arg$1`, CPython 셀, V8 Context가 각 구현의 결과물이다.
- **도달 가능성**: 클로저 → 환경 → 캡처 변수 → 큰 객체로 이어지는 참조 경로가 있으면 GC가 회수하지 못한다([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)의 지배자 트리).

## 적용 — 풀어나가는 법

1. **증상**: 힙이 계속 오르고, 힙 덤프의 지배자 트리에 람다·익명 클래스가 큰 객체를 쥐고 있다.
   - 원리: 클로저가 `this`나 함수 문맥 전체를 붙잡았다.
   - 확인(Java): `jcmd <pid> GC.heap_dump <파일>` 후 분석 도구에서 `…$$Lambda` 인스턴스의 `arg$N` 필드, 익명 클래스의 `this$0`를 본다. 클래스 파일은 `javap -p`로 캡처 필드를 확인한다(실험 B).
   - 확인(node): `node --inspect`·`--heapsnapshot-signal`로 힙 스냅숏을 떠서 클로저가 가리키는 문맥(context)을 본다 [?].
   - 대처: 람다가 필드 대신 필요한 값만 지역 변수로 복사해 쓰게 한다. 등록한 리스너는 해제 경로를 둔다.
2. **증상**: 루프에서 만든 콜백이 모두 마지막 값을 쓴다.
   - 원리: 변수 캡처 + 루프 변수가 하나(JS `var`, Python).
   - 대처: JS는 `let`, Python은 기본 인자나 `functools.partial`로 값을 고정.
3. **증상**: 람다 안 카운터가 병렬에서 모자란다.
   - 원리: 캡처한 가변 상태의 비원자 갱신.
   - 대처: `AtomicInteger`·`LongAdder`, 더 좋게는 부수효과 없이 `reduce`·`collect`로 합친다([18](../18-functional-concepts/2-summary.md)).

```java
// 나쁜 예: 필드를 쓰는 람다 → this(요청 컨텍스트 전체)를 붙잡아 오래 사는 버스에 등록
eventBus.register(evt -> log(evt, this.requestContext.userId()));

// 나은 예: 필요한 값만 지역 변수로 복사해 캡처 → 람다는 문자열 하나만 붙잡는다
// 단 log가 static 메서드일 때다. 인스턴스 메서드면 log(...) 호출이 this를 다시 캡처한다(JLS 15.12.4.1)
String userId = this.requestContext.userId();
eventBus.register(evt -> Audit.log(evt, userId));   // Audit.log: static (예시)
```

## 장애 시나리오와 대처

### 1. 클로저가 큰 객체를 붙잡아 누수 (⚠ 커리큘럼)

- 현상: node 서비스의 힙이 요청 수에 비례해 오르고 GC 뒤에도 안 내려간다.
- 보이는 형태: `heapUsed` 우상향. 힙 스냅숏에서 작은 콜백이 큰 배열을 붙잡는 경로.
- 원인: 콜백 자체는 큰 객체를 안 쓰지만, 같은 함수 안 다른 클로저가 써서 V8 문맥에 들어갔다(실험 C: 10개에 152.6 MiB).
- 대처: 큰 객체를 쓰는 처리와 오래 사는 콜백을 만드는 함수를 분리한다. 다 쓴 변수는 `null`로 끊는다. 재현은 실험 C처럼 `--expose-gc` + `heapUsed` 차이로 확인한다.

### 2. 캡처한 가변 변수 경쟁 (⚠ 커리큘럼)

- 현상: 병렬 처리한 건수 통계가 매번 다르고 실제보다 적다.
- 보이는 형태: 같은 입력인데 결과가 1,323,530 ~ 1,834,261처럼 흔들리고, 가끔은 기대값 2,000,000이 그대로 나와 재현이 어렵다(실험 D와 재실행, 12라운드).
- 원인: effectively final 제한을 `int[]`·가변 객체로 우회해 람다들이 같은 칸을 동시에 고쳤다.
- 대처: 원자 타입, 또는 스레드별 부분 합을 내고 마지막에 합친다(`parallel().sum()`, `collect`).

### 3. 루프 클로저가 마지막 값만 본다

- 현상: 버튼 10개의 클릭 핸들러가 모두 10번 항목을 연다. Python 콜백 목록이 모두 같은 ID로 요청한다.
- 원인: 루프 변수 하나를 모든 클로저가 공유(실험 A `var: 3,3,3`, `late binding : [2, 2, 2]`).
- 대처: JS `let`, Python `lambda i=i:`. Go는 `go.mod`의 `go` 버전을 1.22 이상으로 올리거나 루프 안에서 복사.

### 4. 리스너 람다가 `this`를 붙잡아 요청 객체가 쌓인다

- 현상: Java 서비스의 Old 영역이 계속 차고 Full GC 뒤에도 회수량이 작다.
- 보이는 형태: 힙 덤프에서 `…$$Lambda` 인스턴스 수가 요청 수만큼 있고, `arg$1`이 요청 처리 객체를 가리킨다.
- 원인: 필드를 쓰는 람다는 `this`를 캡처한다(실험 B `[Capture arg$1; ]`). 그 람다가 애플리케이션 수명의 이벤트 버스에 등록되어 해제되지 않았다.
- 대처: 필요한 값만 지역 변수로 복사해 캡처(적용의 코드). 등록 해제를 `try/finally`·`AutoCloseable`로 묶는다. 누수 분석 순서는 [reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md).

## 핵심 문장

- 클로저는 함수 코드와 그 함수가 만들어질 때의 환경에 대한 참조다. 그래서 호출이 끝난 뒤에도 환경이 힙에 남는다.
- JS·Python은 변수를 캡처하고, Java 람다는 effectively final 변수의 값을 캡처한다.
- JS `let` 루프는 반복마다 새 환경을 만들고, `var`는 변수 하나를 공유한다.
- 인스턴스 필드를 쓰는 Java 람다는 `this` 전체를 붙잡는다.
- V8에서는 같은 함수에서 만든 클로저들이 문맥을 공유해, 쓰지 않는 큰 객체까지 붙잡을 수 있다.
- 가변 상태를 캡처해 여러 스레드에서 고치면 갱신이 사라진다.

## 관련 주제·근거

- 원고: [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md) §9(람다 함수 기초). §3(전역·지역·`nonlocal`)은 [language 04](../04-semantic-analysis-and-scopes/2-summary.md)가 잇는다.
- 선행: [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md) · [06-values-references-passing](../06-values-references-passing/2-summary.md)
- 후속: [18-functional-concepts](../18-functional-concepts/2-summary.md) · [13-language-memory-model](../13-language-memory-model/2-summary.md) · [14-concurrency-models](../14-concurrency-models/2-summary.md)
- 다른 영역
  - [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md) — 힙 덤프·지배자 트리
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) — 읽기-수정-쓰기 경쟁
  - 언어별: [js/05 var/let/const](../../../languages/js/syntax/05-var-let-const-and-tdz/2-summary.md), [js/06 scope-and-closures](../../../languages/js/syntax/06-scope-and-closures/2-summary.md), [python/21 LEGB](../../../languages/python/syntax/21-scope-legb-global-nonlocal/2-summary.md), [python/22 late binding](../../../languages/python/syntax/22-closures-and-late-binding/2-summary.md), [java/29 lambda](../../../languages/java/syntax/29-lambda-expressions/2-summary.md), [go/13 loop variable](../../../languages/go/syntax/13-closures-variable-capture-and-loop-variable-change/2-summary.md), [rust/34 closures](../../../languages/rust/syntax/34-closures-fn-fnmut-fnonce-and-move/2-summary.md)
- 명세·문서
  - JLS SE 21 15.27.2 Lambda Body · 4.12.4 final Variables — <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - ECMAScript 2024(15판) 9.1 Environment Records · 14.7.4.4 CreatePerIterationEnvironment — <https://262.ecma-international.org/15.0/>
  - Python Programming FAQ "Why do lambdas defined in a loop with different values all return the same result?" — <https://docs.python.org/3/faq/programming.html>
  - Go 블로그 "Fixing For Loops in Go 1.22" — <https://go.dev/blog/loopvar-preview> · Go 1.22 릴리스 노트 — <https://go.dev/doc/go1.22>
  - JDK 18 릴리스 노트 "Enclosing Instance Fields Omitted from Inner Classes That Don't Use Them"(JDK-8271623) — <https://www.oracle.com/java/technologies/javase/18-relnote-issues.html> · Java SE 21 API `LambdaMetafactory` — <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/invoke/LambdaMetafactory.html>
  - Abelson·Sussman 『SICP』 3.2 The Environment Model of Evaluation — <https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/6515/sicp.zip/full-text/book/book.html>
- 실험 목록(모두 `scratchpad/lang/05/e07/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `loop.js`·`late.py`: 루프 클로저·호출별 환경 — `node:22-alpine` v22.23.2, 호스트 CPython 3.12.3
  - B `Capture.java`·`Anon.java`·`NotFinal.java`: 캡처 필드·`javap`·effectively final 오류 — `eclipse-temurin:21-jdk` 21.0.12
  - C `leak.js`: V8 문맥 공유로 인한 보유량 — `node --expose-gc`, 각 모드 3회
  - D `Race.java`: 캡처한 가변 배열 경쟁 — `eclipse-temurin:21-jdk`, 3라운드(사실 점검 때 JVM 3회 × 3라운드 추가)
