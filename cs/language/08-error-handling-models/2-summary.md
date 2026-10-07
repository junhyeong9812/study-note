# language/08-error-handling-models — 에러 처리 모델: 특수값·에러 값·Result/Option·예외·panic — 정리 (힌트)

## 해결하는 문제

함수가 실패했을 때 그 사실을 **호출자에게 전하는 통로**가 없으면, 결과 값이 거짓말을 한다.

```text
  atoi("abc")  → 0        "0을 읽었다"인지 "못 읽었다"인지 구별 불가
  atoi("12a")  → 12       앞부분만 읽고 조용히 멈춤
```

- *에러 처리 모델*: 실패를 어떤 통로로 알리고, 호출자가 그것을 무시할 수 있는지를 정한 언어의 규칙.

쉬운 예: 택배 배송 실패를 알리는 방법이다.
- 문 앞에 빈 상자를 둔다 → 특수값(`0`, `-1`, `null`). 열어 보기 전엔 실패인지 모른다.
- 문자를 보낸다 → 에러 값 반환. 문자를 안 읽으면 모른다.
- 상자에 "성공/실패" 딱지를 붙여, 딱지를 떼야 내용물을 꺼낼 수 있게 한다 → Result/Option(합 타입).
- 경보를 울려 누군가 끌 때까지 층마다 울린다 → 예외.
- 건물 전체 대피 → panic·abort.

똑같은 구조다.\
통로가 다르면 "무시했을 때 무엇이 보이나"가 다르다. 운영에서 가장 비싼 것은 **아무것도 보이지 않는 실패**다.

실무 예:
- `catch (Exception e) {}` 한 줄 때문에 결제 실패가 로그 없이 "성공"으로 기록된다.
- `finally` 안의 `return` 때문에 던진 예외가 사라진다.
- Go에서 `n, _ := strconv.Atoi(s)`로 에러를 버려 잘못된 입력이 0으로 저장된다.
- 운영 로그에 `java.lang.NullPointerException`만 있고 스택 트레이스가 없다.

설계 쪽 질문(어디서 잡나, 예외냐 결과 타입이냐, HTTP로 어떻게 번역하나)은 [software-design/15](../../software-design/15-error-handling-design/2-summary.md)·[16](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md)에 있다. 이 노트는 **언어·런타임이 실패를 어떻게 나르나**를 다룬다.

## 동작·원리

### 1. 다섯 가지 통로

```text
                     실패가 가는 곳              무시하면                 컴파일러가 강제?
  특수값·errno (C)   반환값/전역 errno          조용히 틀린 값으로 진행   아니오
  에러 값 (Go)       반환값 중 error(관례상 마지막) 조용히 진행(함께 온 값 오용)  아니오(_ 로 버리기 가능)
  Result/Option      반환 타입 자체(합 타입)    값을 꺼낼 수 없음          부분(분기 또는 unwrap→panic 선택)
   (Rust, Java sealed)                          Rust는 미사용 시 경고
  예외 (Java·Python·JS) 호출 스택을 거슬러 위로   잡을 때까지 전파, 끝까지 가면 런타임별 종료*  Java 검사 예외만
  panic (Go·Rust)    스택을 되감으며 종료**      프로세스·스레드 종료(recover/catch_unwind 예외) 아니오
  *  Java: 그 스레드 종료(JVMS 2.10) / Python: 프로그램 종료(실행 모델 4.3) / node 22: 기본은 프로세스 종료(process 문서 'uncaughtException')
  ** Rust는 panic=abort 전략이면 되감지 않고 즉시 중단한다(Rust Reference "Panic")
```

- *errno*: C 표준 라이브러리 함수가 실패 원인을 적어 두는 전역(스레드별) 변수.
- *합 타입(sum type, 태그 유니언)*: "이것 아니면 저것" 중 하나를 담고, 어느 쪽인지 표시(태그)를 함께 가진 타입. `Result<T, E>` = `Ok(T) | Err(E)`, `Option<T>` = `Some(T) | None`.
- *예외(exception)*: 정상 반환 경로와 별개로 제어를 호출 스택 위쪽의 처리기로 옮기는 장치.
- *panic*: 복구를 기대하지 않는 실패. 보통 스택을 되감으며 종료한다(Rust `panic=abort`면 되감지 않고 중단).
- Go의 에러 값 위치: 함수가 정한다. 관례상 마지막 반환값이고, `os.Remove`처럼 `error` 하나만 돌려주는 함수도 있다. 에러를 버렸을 때 함께 온 값이 무엇인지도 함수 계약마다 다르다 — `strconv.Atoi`는 0(실험 A)이지만 `io.Reader.Read`는 `n > 0`과 에러를 함께 돌려줄 수 있다(Go `io` 문서).
- `Result`도 안전한 처리를 강제하지는 않는다. `unwrap()`·`expect()`는 분기 없이 컴파일되고 `Err`면 panic한다. `#[must_use]`는 기본이 경고다(std `result` 문서).

### 실험 A: 특수값과 에러 값은 무시할 수 있다

(실험, 호스트 gcc 13.3 `-O0` / `golang:1.23-alpine` go1.23.12, `scratchpad/lang/05/e08/errno.c`·`errval.go`, 2026-10-07)

```text
C   atoi("12a")  = 12   atoi("abc") = 0   (실패를 알릴 길이 없다)
    strtol("abc") = 0, 소비한 글자 = 0 → 호출자가 end로 판정
    strtol(큰 수)  = 9223372036854775807, errno == ERANGE: 1
Go  vet exit=0
    ignored error  -> n = 0
    checked error  -> strconv.Atoi: parsing "12a": invalid syntax (m = 0 )
    recovered panic -> runtime error: index out of range [3] with length 0
```

- C `atoi`는 실패를 알릴 통로가 없다. C 표준(N1570 7.22.1)은 결과를 표현할 수 없으면 `atoi`의 동작을 **정의하지 않는다**(UB). `strtol`은 끝 포인터와 `errno`(`ERANGE`)로 알린다.
- Go는 에러를 값으로 돌려준다(Go 블로그 "Error handling and Go": "Go code uses error values to indicate an abnormal state."). `_`로 버리면 `go vet`도 경고하지 않았다(exit 0).
- 범위 밖 인덱스는 에러 값이 아니라 panic이다. `recover`로 잡을 수 있지만, 그것은 예외적 용도다([languages/go/syntax/27](../../../languages/go/syntax/27-panic-recover-and-where-to-use-them/2-summary.md)).
- Rust `Result`는 `#[must_use]`가 붙어 있어 값을 무시하면 컴파일러가 경고한다(Rust std `result` 모듈 문서 "Results must be used"). 이 호스트에는 Rust 도구가 없어 실행하지 않았다.

### 2. 예외는 어떻게 날아가나 — 예외 테이블과 스택 되감기

```text
  static int handled(String s)
     0: aload_0
     1: invokestatic Integer.parseInt     ┐ try 구간 [0, 4)
     4: ireturn                           ┘ 정상 경로: 추가 명령 없음
     5: astore_1                          ← 처리기 (catch 본문)
     6: iconst_m1
     7: ireturn
    Exception table:
       from    to  target type
           0     4     5   Class java/lang/NumberFormatException

  throw 발생 → ① 현재 메서드 표를 위에서부터 검색 → 구간·타입이 맞으면 target으로 점프
             → ② 없으면 프레임을 버리고(pop) 호출자에서 ①을 반복 → … → 끝까지 없으면 스레드 종료
```

- *예외 테이블(exception table)*: `[시작, 끝) 구간에서 이 타입이 던져지면 여기로` 를 적은 표(JVMS 4.7.3). 표의 순서가 의미를 가진다.
- *스택 되감기(stack unwinding)*: 처리기를 찾을 때까지 프레임을 하나씩 버리는 과정. JVMS 2.10: 현재 메서드에 처리기가 없으면 "the current method invocation completes abruptly … its frame is popped".
- 정상 경로에는 검사 명령이 없다. 비용은 **던질 때** 든다(예외 객체 생성, 스택 트레이스 기록, 처리기 검색).
- 위 바이트코드는 실험 B의 실제 `javap -c` 출력이다(`eclipse-temurin:21-jdk` 21.0.12, `Finally.java`).

### 실험 C: 던지는 비용은 스택 트레이스와 깊이가 정한다

(실험, `eclipse-temurin:21-jdk` 21.0.12, `-Xmx256m`, `--cpus=2`, `scratchpad/lang/05/e08/Cost.java`, 같은 JVM에서 워밍업 1회 후 5라운드, 이를 2번 실행해 첫 실행 5라운드 + 둘째 실행 마지막 2라운드를 기록, 호출의 절반이 실패, 단위 ns/호출, 2026-10-07)

| 방식 | 범위(7개 라운드) | 사실 점검 재실행(2회 × 5라운드) |
|---|---|---|
| Result 값 반환(sealed 인터페이스 + record) | 21 ~ 29 | 21 ~ 28 |
| 예외, 스택 트레이스 채움, 깊이 0 | 608 ~ 732 | 645 ~ 743 |
| 예외, 스택 트레이스 안 채움(`writableStackTrace=false`) | 29 ~ 36 | 23 ~ 35 |
| 예외, 스택 채움, 깊이 10 | 1,443 ~ 1,710 | 1,179 ~ 1,963 |
| 예외, 스택 채움, 깊이 200 | 17,465 ~ 21,060 | 17,939 ~ 19,912 |
| 예외, 스택 안 채움, 깊이 200 | 9,864 ~ 11,380 | 10,055 ~ 11,180 |

- JMH가 아닌 직접 측정이다. 숫자의 절대값보다 **배율**만 본다. 값은 "호출 1회당"이고 호출의 절반만 던지므로, 던지는 1회의 비용은 대략 그 두 배다(해석).
- 얕은 깊이에서는 스택 트레이스 기록(`fillInStackTrace`)이 비용의 대부분이었다(608~732 → 29~36).
- 깊이 200에서는 스택 트레이스를 안 채워도 9,864~11,380ns였다. 해석: 프레임 200개를 되감는 비용과 재귀 호출 자체가 남는다. JIT가 같은 메서드 안의 throw-catch를 점프로 바꿨는지는 로그로 확인하지 않았다.
- 결론: "예외는 느리다"가 아니라 "**깊은 스택에서 자주** 던지는 예외가 느리다". 정상 흐름에서 드물게 던지는 예외는 비용이 문제되지 않는다.

### 3. 검사 예외 — 컴파일러가 처리를 강요한다

- Java는 예외를 둘로 나눈다(JLS 11.1.1).
  - *검사 예외(checked)*: `Throwable` 중 `RuntimeException`·`Error`와 그 하위가 아닌 것. 메서드가 던질 수 있으면 `throws`로 선언하거나 잡아야 한다(JLS 11.2).
  - *비검사 예외(unchecked)*: `RuntimeException`·`Error` 계열. 선언 의무가 없다.
- 부작용: 컴파일을 통과시키려고 `catch (IOException e) {}`로 삼키는 코드가 생긴다. 표준 함수형 인터페이스(`Function` 등)는 검사 예외를 던질 수 없어, 람다 안에서 감싸거나 삼키게 된다.
- Kotlin·C#·Python·JS에는 검사 예외가 없다 [?]. 실패를 타입에 드러내려면 결과 타입을 쓴다.

### 4. `finally`가 예외를 지운다

```text
  try { throw E }  ──>  finally 실행
                          ├─ 정상 종료  → try 문은 E로 끝남 (E가 위로 전파)
                          └─ return/throw/break(급종료 S) → try 문은 S로 끝남, E는 버려진다
```

- JLS 14.20.2: "If the finally block completes abruptly for reason S, then the try statement completes abruptly for reason S (and the throw of value V is discarded and forgotten)."

### 실험 B: `finally` 안 `return`

(실험, `eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e08/Finally.java`·`FinallyLint.java`, 2026-10-07)

```text
swallow()   = 1   (예외 없음)          ← IllegalStateException("결제 실패")가 사라짐
overwrite() = 1                        ← try의 return 값은 finally 전에 정해짐
handled(x)  = -1
javac -Xlint:finally:
FinallyLint.java:4: warning: [finally] finally clause cannot complete normally
```

- 예외가 로그도 없이 사라졌다. 이 경고는 기본으로 켜져 있지 않아 `-Xlint:finally`(또는 `-Xlint:all`)를 줘야 보였다.
- `try`에서 `return x` 뒤 `finally`에서 `x`를 바꿔도 반환값은 그대로다(`overwrite() = 1`). 반환할 값이 이미 정해졌기 때문이다.
- Python·JS도 같다. 로컬 실행(호스트 CPython 3.12.3 `fin.py`, `node:22-alpine` v22.23.2 `fin.js`)에서 `raise`/`throw` 뒤 `finally: return 1`이 `python f() = 1`, `js f() = 1`을 냈다(예외 없음).

### 5. 런타임이 스택 트레이스를 생략한다 — HotSpot fast throw

```text
  인터프리터·초기 실행          JIT 컴파일 뒤(자주 나는 내장 예외)
  NPE 객체 새로 생성            미리 만든 NPE 객체를 그대로 던짐
  스택 트레이스 기록            스택 트레이스 없음, 메시지 없음
```

- 같은 코드라도 실행 단계에 따라 예외 객체의 모양이 바뀔 수 있다. 아래 실험이 그 전환을 보인다.

### 실험 D: 같은 NPE가 어느 순간부터 스택 없이 나온다

(실험, `eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e08/FastThrow.java`, 같은 `null` 역참조를 20만 번, 2026-10-07)

```text
기본
i=0 스택 2줄, message=Cannot invoke "Object.toString()" because "<parameter1>" is null
i=5245 스택 트레이스 0줄, message=null
NPE 200000회, 스택 없는 NPE 처음 등장 = i=5245     (반복 실행: i=5257, 5253, 5181 / 사실 점검 재실행 5회: 5244~5272)
-XX:-OmitStackTraceInFastThrow
i=0 스택 2줄, message=Cannot invoke "Object.toString()" because "<parameter1>" is null
NPE 200000회, 스택 없는 NPE 처음 등장 = 없음
```

- 같은 코드가 처음에는 스택과 상세 메시지(JEP 358의 helpful NPE)를 내고, 약 5천 번 뒤부터 스택 0줄·메시지 `null`이 됐다.
- 원인: HotSpot의 `OmitStackTraceInFastThrow`(OpenJDK 21 `globals.hpp`, 기본 `true`, 설명 "Omit backtraces for some 'hot' exceptions in optimized code"). 컴파일된 코드에서 자주 나는 일부 내장 예외를 미리 만든 객체로 던진다(해석: 시점이 JIT 컴파일 시점과 맞물린다. 컴파일 로그로 대조하지는 않았다).
- 운영 의미: 오래 돈 서버의 로그에는 스택 없는 예외만 남는다. 첫 발생 로그를 찾거나 이 옵션을 끈다.
- `<parameter1>`로 나온 것은 `-g` 없이 컴파일해 지역 변수 이름 정보가 없어서다.

## 쓰이는 자료구조·알고리즘

- **합 타입(태그 유니언)**: 태그 + 값 중 하나. 패턴 매칭으로 꺼내며, 모든 경우를 다뤘는지 컴파일러가 검사할 수 있다(Java `sealed` + `switch`, Rust `match`). 설계 쪽 실험은 [software-design/16](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md) 실험 B.
- **예외 테이블**: 바이트코드 구간 → 처리기 주소의 순서 있는 표. 던질 때 표에 적힌 순서대로 처음부터 찾아 첫 일치를 고른다(JVMS 2.10 — 명세는 이 순서 의미를 정할 뿐, 검색 구현 방식까지 정하지는 않는다).
- **호출 스택**: 되감기는 처리기를 찾을 때까지의 스택 팝이다([data-structure/03-stack](../../data-structure/03-stack/2-summary.md), 프레임 모양은 [architecture/10](../../architecture/10-calling-convention-and-stack-frame/2-summary.md)). 스택 트레이스 기록 비용이 깊이에 비례하는 이유다(실험 C).
- **원인 사슬**: 예외의 `cause`는 연결 리스트다. 번역할 때 원인을 붙이지 않으면 사슬이 끊긴다.

## 적용 — 풀어나가는 법

1. **증상**: 결과가 틀렸는데 에러 로그가 없다.
   - 원리: 실패가 통로에서 버려졌다(빈 `catch`, `finally` 안 `return`, 버린 에러 값, 확인 안 한 특수값).
   - 확인
     - Java: `javac -Xlint:all`(`finally` 경고 포함), 빈 catch 검색 `grep -rnE 'catch \([^)]*\) *\{ *\}' src/`.
     - Go: `_`로 받은 에러 검색 `grep -rnE ', *_ *:?= ' --include=*.go`. `go vet`은 이를 잡지 않았다(실험 A).
     - C: `atoi`류를 `strtol`류 + 끝 포인터 + `errno` 검사로 바꾼다.
2. **증상**: 로그에 스택 트레이스 없는 `NullPointerException`·`ArithmeticException`만 반복된다.
   - 원리: HotSpot fast throw(실험 D).
   - 확인·대처: 서버 기동 직후 로그에서 같은 예외의 첫 발생(스택 있음)을 찾는다. 필요하면 `-XX:-OmitStackTraceInFastThrow`로 재기동한다(같은 예외가 폭주하면 로그량이 늘 수 있다).
3. **증상**: CPU 프로파일 상위에 `fillInStackTrace`·`Throwable.<init>`이 있다.
   - 원리: 예상 가능한 실패(검증 실패·없음)를 깊은 스택에서 예외로 자주 던진다(실험 C).
   - 대처: 예상 가능한 실패는 결과 값으로([software-design/16](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md)). 꼭 예외여야 하면 스택이 필요한지 따져 `writableStackTrace=false` 생성자를 쓴다.

```java
// 원인을 보존하는 번역 — cause를 넘긴다
try {
    return gateway.charge(req);
} catch (IOException e) {
    throw new PaymentUnavailableException("PG 호출 실패 orderId=" + req.orderId(), e);   // e를 버리지 않는다
}

// 결과 타입 — 실패 종류가 타입에 드러나고, switch 식에서 빠진 경우는 컴파일 오류가 된다
sealed interface ParseResult permits Parsed, Invalid {}
record Parsed(int value) implements ParseResult {}
record Invalid(String input, String reason) implements ParseResult {}
```

## 장애 시나리오와 대처

### 1. 삼킨 예외(`catch {}`) → 조용한 실패 (⚠ 커리큘럼)

- 현상: 정산 데이터 일부가 빠졌는데 에러 알람도 로그도 없다.
- 보이는 형태: 처리 건수 지표만 조금 낮다. 로그에는 아무것도 없다.
- 원인: 검사 예외를 컴파일러가 요구해서 `catch (IOException e) {}`로 막아 두었다. 실패한 건이 "처리됨"으로 지나갔다.
- 대처: 빈 catch를 금지하는 정적 규칙. 잡았으면 처리하거나 원인을 붙여 다시 던진다. 설계 원칙은 [software-design/15](../../software-design/15-error-handling-design/2-summary.md)의 "삼킨 예외".

### 2. `finally` 안 `return`이 예외를 지운다 (⚠ 커리큘럼)

- 현상: 결제 실패가 성공 코드(1)로 반환된다.
- 보이는 형태: 예외 로그 없음. 반환값만 정상처럼 보인다(실험 B `swallow() = 1 (예외 없음)`).
- 원인: JLS 14.20.2 — `finally`가 급종료하면 `try`의 예외는 "discarded and forgotten".
- 대처: `finally`에서는 정리만 하고 `return`·`throw`·`break`를 쓰지 않는다. `javac -Xlint:finally`를 CI에서 오류로. 자원 정리는 try-with-resources로(정리 중 예외는 suppressed로 보존된다 — [languages/java/syntax/26](../../../languages/java/syntax/26-try-with-resources/2-summary.md)).

### 3. 체크 안 한 에러 반환값 (⚠ 커리큘럼)

- 현상: 사용자 입력 `"12a"`가 수량 0 또는 12로 저장된다.
- 보이는 형태: 에러 없음. 데이터만 이상하다(실험 A: Go `ignored error -> n = 0`, C `atoi("12a") = 12`).
- 원인: Go `_`로 에러를 버렸다. C `atoi`는 실패를 알릴 수 없다(N1570 7.22.1: 표현 불가 시 UB).
- 대처: Go는 받은 에러를 버리지 말고 분기한 뒤 래핑해 올린다([languages/go/syntax/24](../../../languages/go/syntax/24-error-wrapping-and-errors-is-as-join/2-summary.md)). 무시 검사 도구를 린터에 둔다(errcheck류 — 실행하지 않음 [?]). C는 `strtol`+끝 포인터+`errno`. Rust는 `Result`의 `#[must_use]` 경고를 오류로 다룬다.

### 4. 스택 없는 예외만 남은 로그

- 현상: 장애 분석 중 로그에 `java.lang.NullPointerException` 한 줄만 수천 개.
- 보이는 형태: 스택 트레이스 0줄, 메시지 `null`(실험 D).
- 원인: `OmitStackTraceInFastThrow`(기본 켜짐)가 자주 나는 내장 예외의 스택을 생략했다.
- 대처: 기동 직후의 첫 발생 로그를 찾는다. 재현 환경이나 일시적으로 `-XX:-OmitStackTraceInFastThrow`. 근본적으로는 같은 예외가 수천 번 나는 경로 자체를 고친다.

### 5. 흐름 제어용 예외가 깊은 스택에서 CPU를 먹는다

- 현상: 트래픽은 그대로인데 검증 실패 비율이 오르자 CPU가 급등한다.
- 보이는 형태: 프로파일에서 `Throwable.fillInStackTrace`가 상위. 깊은 프레임(프레임워크 필터·프록시 수십 겹) 아래에서 던진다.
- 원인: 실패 1건당 스택 트레이스 기록 + 되감기(실험 C: 깊이 200에서 호출당 약 17~21µs — 호출의 절반이 실패한 측정).
- 대처: 예상 가능한 실패는 결과 값으로 바꾼다. 경계 가까이에서 일찍 검증해 깊은 스택에 들어가기 전에 거른다.

## 핵심 문장

- 에러 처리 모델은 "실패를 어떤 통로로 나르고, 무시하면 무엇이 보이나"로 비교한다.
- 특수값·에러 값은 무시해도 컴파일러가 막지 않는다. 합 타입은 꺼내려면 분기하거나 `unwrap`처럼 실패 시 panic을 명시적으로 골라야 하고, 예외는 잡을 때까지 위로 간다.
- JVM 예외는 정상 경로에 비용이 없고, 던질 때 스택 트레이스 기록과 되감기 비용이 깊이에 비례해 든다.
- `finally`가 `return`으로 끝나면 `try`의 예외는 버려진다(JLS 14.20.2).
- HotSpot은 자주 나는 일부 내장 예외의 스택 트레이스를 기본으로 생략한다.
- 조용한 실패를 막는 것은 언어 기능(합 타입·must_use·검사 예외)과 린터 규칙의 조합이다.

## 관련 주제·근거

- 선행: [05-type-systems](../05-type-systems/2-summary.md)(합 타입의 바탕)
- 후속: [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md) — `CompletableFuture` 예외 미처리 · [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md)
- 다른 영역
  - [software-design/15-error-handling-design](../../software-design/15-error-handling-design/2-summary.md) · [16-error-strategy-exceptions-vs-results](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md) · [18-absence-and-null-design](../../software-design/18-absence-and-null-design/2-summary.md)(JEP 358 helpful NPE 실험)
  - [architecture/10-calling-convention-and-stack-frame](../../architecture/10-calling-convention-and-stack-frame/2-summary.md)
  - 언어별: [java/25 exceptions](../../../languages/java/syntax/25-exceptions/2-summary.md), [java/26 try-with-resources](../../../languages/java/syntax/26-try-with-resources/2-summary.md), [go/23 errors as values](../../../languages/go/syntax/23-error-interface-and-errors-as-values/2-summary.md), [go/27 panic/recover](../../../languages/go/syntax/27-panic-recover-and-where-to-use-them/2-summary.md), [rust/22 Result·?](../../../languages/rust/syntax/22-result-question-mark-and-from/2-summary.md), [rust/23 panic vs Result](../../../languages/rust/syntax/23-panic-vs-result/2-summary.md), [c/46 errno](../../../languages/c/syntax/46-errno-and-error-return-conventions/2-summary.md), [python/25 exceptions·finally](../../../languages/python/syntax/25-exceptions-and-finally/2-summary.md)
- 명세·문서
  - JLS SE 21 11.1.1 The Kinds of Exceptions · 11.2 Compile-Time Checking · 14.20.2 try-finally — <https://docs.oracle.com/javase/specs/jls/se21/html/jls-11.html>, <https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html>
  - JVMS SE 21 2.10 Exceptions · 4.7.3 The Code Attribute(exception_table) — <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html>
  - OpenJDK 21 `src/hotspot/share/runtime/globals.hpp`의 `OmitStackTraceInFastThrow` — <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/hotspot/share/runtime/globals.hpp>
  - C11 초안 N1570 7.22.1 Numeric conversion functions — <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>
  - Go 블로그 "Error handling and Go" — <https://go.dev/blog/error-handling-and-go>
  - Rust std `result` 모듈 "Results must be used" — <https://doc.rust-lang.org/std/result/>
  - Pierce 『TAPL』 14장 Exceptions(목차로 확인, 본문 미열람)
- 실험 목록(모두 `scratchpad/lang/05/e08/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `errno.c`·`errval.go`: 특수값·에러 값·panic — 호스트 gcc 13.3, `golang:1.23-alpine` go1.23.12
  - B `Finally.java`·`FinallyLint.java`: `finally` 안 `return`, `javap -c` 예외 테이블, `-Xlint:finally` — `eclipse-temurin:21-jdk` 21.0.12
  - C `Cost.java`: Result vs 예외 비용, 깊이별 — 같은 이미지, `-Xmx256m`, 2회 실행에서 7라운드 기록
  - D `FastThrow.java`: fast throw 스택 생략, `-XX:-OmitStackTraceInFastThrow` 비교 — 같은 이미지, 4회(사실 점검 때 5회 추가)
  - `fin.py`·`fin.js`: Python·JS의 `finally` 안 `return` — 호스트 CPython 3.12.3, `node:22-alpine`
