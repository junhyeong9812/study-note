# language/04-semantic-analysis-and-scopes — 정답

## 정답

### 1. 의미 분석이 잡는 오류

- 정의되지 않은 이름 사용(`print(y)`에서 `y`가 어디에도 선언되지 않음).
- 같은 스코프의 중복 선언(Java `int x = 1; { int x = 2; }`).
- 타입이 안 맞는 연산·대입(정적 타입 언어, 05), Java 람다가 바뀌는 지역 변수를 캡처.
- 심벌 테이블: 이름 → 종류(변수·함수·매개변수·타입), 선언된 스코프, 타입(정적 타입 언어), 저장 위치(슬롯·오프셋). CPython `symtable`은 타입 없이 스코프와 쓰임(정의·사용·매개변수·자유 변수)을 기록한다.

### 2. 해시 테이블 스택

```text
  top ┌ 블록 { i }            i     → 0칸 위
      ├ 함수 { price, total } total → 1칸 위 (전역 total을 가림)
      └ 전역 { total, rate }  rate  → 2칸 위
                              ratee → 없음 → 정의되지 않은 이름 오류
```

- 블록을 나가면 그 표를 pop하므로 `i`는 더 이상 없다(정의되지 않음).
- 실험(`Scopes.java`)의 출력이 이 그대로다. `total`을 함수에 선언할 때 `WARN 'total' shadows Sym[name=total, kind=global, depth=0]`도 냈다.

### 3. 렉시컬 vs 동적

- 렉시컬: 이름은 **소스에 적힌 위치**의 바깥 블록에서 찾는다. 함수를 어디서 부르든 같은 선언을 본다.
  - Python의 예외: 클래스 본문은 메서드가 이름을 찾는 바깥 스코프가 아니다. 메서드 안의 `y`는 클래스 변수 `y`를 건너뛴다(실행 모델 §4.2.2, CPython 3.12.14 실험: `NameError: name 'y' is not defined`).
- 동적: 이름은 **호출 체인**을 따라 찾는다.
- 예: 전역 `x = 1`, `f() { return x }`, `g() { x = 2(g의 지역); return f() }`.
  - 렉시컬이면 `g()`는 1(f가 적힌 곳의 바깥 = 전역).
  - 동적이면 2(f를 부른 g의 지역).
- Java·JS·Python·C·Go·Rust는 렉시컬이다. 그래서 컴파일 시점에 이름을 렉시컬 주소로 바꿔 둘 수 있다.

### 4. 루프 캡처

- (a) `[3, 3, 3]` — `var`는 함수 스코프라 `i` 바인딩이 하나. 반복이 끝난 뒤 호출하면 마지막 값 3.
- (b) `[0, 1, 2]` — `for (let …)`은 반복마다 새 바인딩(ECMAScript 2024 §14.7.4.4).
- (c) `[2, 2, 2]` — 리스트 컴프리헨션의 `i` 하나를 람다들이 공유하고, 호출 시점에 읽는다(늦은 바인딩). `lambda i=i: i`면 `[0, 1, 2]`.
- (d) 컴파일 오류: `local variables referenced from a lambda expression must be final or effectively final`. `int k = i;`로 반복마다 새 지역 변수를 만들면 `[0, 1, 2]`.
- 모두 실험 출력 그대로다(node 22.23.2, CPython 3.12.14, Temurin 21.0.12).

### 5. `UnboundLocalError`

- `inc()` → `UnboundLocalError: cannot access local variable 'count' where it is not associated with a value`.
- 규칙(Python 3.12 실행 모델 §4.2.2): 코드 블록 안 어디서든 이름 바인딩(대입·`+=` 포함)이 있으면 그 블록 안 모든 사용이 현재 블록(지역)을 가리킨다. 이건 실행이 아니라 **컴파일 시점**에 블록 전체를 훑어 정한다.
- 그래서 대입 한 줄을 아래에 추가해도, 그 위의 읽기까지 지역 변수 읽기로 컴파일되고, 아직 값이 없어 실패한다. CPython 3.12의 `dis`로 보면 그 읽기는 `LOAD_FAST_CHECK`다. 이 명령이 값이 없음을 확인해 `UnboundLocalError`를 낸다(초기화가 보장된 읽기는 검사 없는 `LOAD_FAST`).
- 바깥 변수를 바꾸려면 `global count`(모듈 변수)나 `nonlocal`(바깥 함수 변수)을 선언한다.

### 6. Java의 두 섀도잉

- `int x = 1; { int x = 2; }` → `error: variable x is already defined in method main(String[])`. JLS 21 §6.4: 지역 변수 v의 이름을 v의 스코프 안에서 새 변수 선언에 쓰면 컴파일 오류다(그 안의 지역·익명 클래스 선언 안은 예외).
- `void add(int count) { count = count + 1; }` → 컴파일된다. 매개변수 선언은 같은 이름의 필드를 그 스코프 동안 가린다(§6.4.1). 필드는 `this.count`로 여전히 닿을 수 있어 허용된다.
- 결과: 실험에서 `s.add(5)` 뒤 `field count = 0`. 매개변수만 바뀌었다.

### 7. 캡처 방식과 effectively final

- Java 람다는 캡처한 지역 변수의 **값**을 가져간다. 원본 변수가 나중에 바뀌면 람다 안 값과 어긋난다. 그래서 바뀌지 않는(final·effectively final) 변수만 허용한다.
- JS·Python 클로저는 **변수(바인딩) 자체**를 공유한다. 바깥에서 바꾸면 클로저도 바뀐 값을 본다. 그래서 제한이 없고, 대신 늦은 바인딩 버그(4번)가 생긴다.
- JLS 21 §15.27.2의 이유: 동적으로 바뀌는 지역 변수의 캡처는 동시성 문제를 부를 가능성이 커서 막는다.

### 8. `symtable`과 `dis`로 본 자유 변수

- `symtable`(3.12.14): `inner [('x', 'global'), ('y', 'free')]`. `x`는 전역, `y`는 자유 변수.
- `dis(inner)`: `COPY_FREE_VARS 1` → `LOAD_GLOBAL 0 (x)` → `LOAD_DEREF 0 (y)` → `BINARY_OP 0 (+)`. 전역은 이름으로 찾고, 자유 변수는 셀에서 읽는다.
- `outer`가 끝나도 `y`가 사는 이유: 컴파일러가 `y`를 프레임 슬롯이 아니라 **셀**에 두고, `inner.__closure__`가 그 셀을 참조한다. 별도 실험(`late.py` — `outer` 안의 `x = 1`을 `inner`가 읽는 예제)에서 `outer().__closure__`는 셀 하나, `co_freevars`는 `('x',)`였다(그 예제의 자유 변수가 `x`라서다).

### 9. 마지막 인덱스만 보이는 콜백

- 원인: 콜백이 반복 변수의 **값**이 아니라 **바인딩**을 캡처했다. 바인딩이 하나(JS `var`, Python 반복 변수)이고, 콜백은 반복이 끝난 뒤에 실행돼 마지막 값을 읽는다.
- 고침
  - JS: `var` → `let`(반복마다 새 바인딩).
  - Python: `lambda i=i: …`(정의 시점 값을 기본 인자로 묶음), `functools.partial(f, i)`.
  - Java라면 애초에 컴파일 오류이므로 반복마다 새 지역 변수를 만든다.

### 10. `int[] sum = {0}` 우회

- 잘못: 배열 원소는 effectively final 규칙의 대상이 아니라 컴파일은 통과한다. 하지만 여러 스레드가 `sum[0] += x`를 동기화 없이 한다. 읽기-수정-쓰기가 겹쳐 갱신이 사라진다(데이터 레이스). JLS §15.27.2가 막으려던 바로 그 동시성 문제를 우회로 되살렸다.
- 고침: 결과를 반환하는 연산을 쓴다. `list.parallelStream().mapToInt(Integer::intValue).sum()`, `reduce`, `collect`. 공유 가변 상태가 꼭 필요하면 `LongAdder` 등 동시성 도구와 메모리 모델 규칙([language 13](../13-language-memory-model/2-summary.md))을 따른다.
