# language/08-error-handling-models — 정답

## 정답

### 1. 다섯 통로 비교

| 모델 | 실패가 가는 곳 | 무시하면 | 컴파일러 강제 |
|---|---|---|---|
| 특수값·errno (C) | 반환값·`errno` | 틀린 값으로 진행 | 아니오 |
| 에러 값 (Go) | 반환값 중 `error`(관례상 마지막) | 함께 온 값으로 진행(`Atoi`는 0 — 함수 계약마다 다름) | 아니오 |
| Result/Option | 반환 타입 자체 | 값을 꺼낼 수 없음(Rust는 미사용 경고) | 부분(분기하거나 `unwrap`으로 panic을 골라야 꺼냄) |
| 예외 | 호출 스택 위 처리기 | 잡힐 때까지 전파 | Java 검사 예외만 |
| panic | 되감으며 종료(Rust `panic=abort`면 되감지 않고 중단) | 프로세스·스레드 종료 | 아니오 |

- 조용한 실패에 가장 취약한 것: 특수값과 버린 에러 값. 아무 신호 없이 틀린 값이 흐른다. 예외는 **삼키면**(빈 catch, finally return) 같은 정도로 취약해진다.

### 2. `atoi` vs `strtol`

- `atoi("12a") = 12`, `atoi("abc") = 0`(실험 A). 실패를 알릴 통로가 없다.
- `strtol`: 끝 포인터로 소비한 글자 수를 알려 준다(`"abc"`는 0글자 → 호출자가 실패로 판정). 범위 초과면 `errno = ERANGE`와, 부호에 따라 `LONG_MAX` 또는 `LONG_MIN`(N1570 7.22.1.4). 실험한 x86-64(64비트 `long`)에서 `LONG_MAX`는 `9223372036854775807`.
- N1570 7.22.1: `atoi` 등은 결과를 표현할 수 없으면 "the behavior is undefined"(UB).

### 3. 예외 테이블

```text
   0: aload_0
   1: invokestatic Integer.parseInt   ← try 구간 [0, 4)
   4: ireturn                         ← 정상 경로는 여기서 끝
   5: astore_1                        ← 처리기
   6: iconst_m1
   7: ireturn
  Exception table:  from 0  to 4  target 5  type NumberFormatException
```

- 정상 경로에는 검사 명령이 없다. 실행 중 표를 뒤지는 것은 던질 때다(로딩 때 검증기도 `catch_type` 등을 검사한다 — JVMS 4.10).
- 던질 때: ① 예외 객체 생성(기본은 스택 트레이스 기록) → ② 현재 메서드 표를 적힌 순서대로 처음부터 찾아 첫 일치(JVMS 2.10) → ③ 맞으면 `target`으로 점프 → ④ 없으면 프레임을 버리고 호출자에서 반복 → ⑤ 끝까지 없으면 스레드 종료.

### 4. 비용 배율

- 깊이 0: 스택 채움 608~732ns vs 안 채움 29~36ns → 약 20배(사실 점검 재실행 645~743 vs 23~35, 같은 경향). 스택 트레이스 기록이 대부분이었다.
- 깊이 200: 안 채워도 9,864~11,380ns. 해석: 프레임 200개를 되감는 비용과 재귀 호출 자체가 남는다(스택 채움은 17,465~21,060ns).
- 직접 측정(JMH 아님)이라 배율만 의미가 있다.

### 5. `finally` 안 `return`

- `1`이 반환되고 예외는 사라진다(실험 B `swallow() = 1 (예외 없음)`).
- JLS 14.20.2: finally가 급종료(reason S)하면 try 문은 S로 끝나고 "the throw of value V is discarded and forgotten".
- `javac -Xlint:finally`(또는 `-Xlint:all`): `warning: [finally] finally clause cannot complete normally`. 옵션 없이는 경고가 나오지 않았다.
- Python·JS도 같은 결과였다(`python f() = 1`, `js f() = 1`).

### 6. 검사 vs 비검사

- JLS 11.1.1: 비검사 예외 = `RuntimeException`과 그 하위 + `Error`와 그 하위. 검사 예외 = 그 밖의 모든 `Throwable`.
- 검사 예외는 `throws` 선언이나 처리가 컴파일 시점에 강제된다(JLS 11.2).
- 조용한 실패 경로: 컴파일을 통과시키려 `catch (IOException e) {}`로 막는다. 람다 안(`Function`은 검사 예외를 못 던짐)에서 특히 자주 생긴다.

### 7. 스택 없는 NPE

- 원인: HotSpot `OmitStackTraceInFastThrow`(기본 `true`). 컴파일된 코드에서 자주 나는 내장 예외를 스택 없는 미리 만든 객체로 던진다. 실험 D에서 약 5,181~5,272번째부터(집필 4회 + 점검 재실행 5회) `스택 트레이스 0줄, message=null`.
- 원인 줄 찾기
  1. 기동 직후 로그에서 같은 예외의 첫 발생(스택 있음)을 찾는다.
  2. 재현 환경이나 일시적으로 `-XX:-OmitStackTraceInFastThrow`를 켜고 재기동한다(실험 D: 20만 번 모두 스택 있음).
  3. 같은 예외가 수천 번 나는 경로 자체가 버그이므로 그 경로를 고친다.

### 8. Go에서 버린 에러

- `"12a"`가 에러 없이 `0`이 되어 저장된다(실험 A `ignored error -> n = 0`). 수량·금액이면 데이터 오염이다.
- `go vet`은 잡지 않았다(`vet exit=0`). 별도 린터(errcheck류)가 필요하다 [?].
- Rust: `Result`에 `#[must_use]`가 붙어 무시하면 컴파일 경고가 난다(기본은 오류가 아니라 경고). 값을 꺼내려면 `match`·`?`로 분기하거나, `unwrap()`·`expect()`로 `Err`일 때 panic을 고른다 — 조용히 0이 되지는 않지만 안전한 처리를 강제하지도 않는다(std `result` 문서 "Results must be used").

### 9. 흐름 제어용 예외

- 원인: 예상 가능한 실패(검증 실패)를 깊은 스택(필터·프록시 여러 겹) 아래에서 예외로 던졌다. 실패율에 비례해 스택 트레이스 기록과 되감기 비용이 늘었다(실험 C 깊이 200: 호출당 17~21µs, 호출의 절반이 실패).
- 대처
  1. 예상 가능한 실패는 결과 값으로 반환한다([software-design/16](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md)).
  2. 경계 가까이(요청 진입 직후)에서 일찍 검증해 깊은 스택에 들어가기 전에 거른다. 꼭 예외여야 하고 스택이 필요 없으면 `writableStackTrace=false` 생성자.
