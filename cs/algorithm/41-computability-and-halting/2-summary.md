# algorithm/41-computability-and-halting — 정지 문제·라이스 정리 — 정리 (힌트)

## 해결하는 문제

"이 프로그램이 끝나는지 미리 알려 주는 도구", "버그를 전부 찾고 오탐도 없는 정적 분석기"는 만들 수 없다. 이것은 기술이 부족해서가 아니라 **증명된 한계**다.

```text
  기대: 분석기(P) → "버그 있음" / "버그 없음"   (언제나 끝나고, 언제나 맞게)
  현실: 셋 중 하나를 포기한다
        ① 오탐(false positive)을 받아들인다   → 안전한 쪽으로 의심 (javac의 확정 대입 검사)
        ② 미탐(false negative)을 받아들인다   → 확실한 것만 보고 (많은 린터·버그 탐지기)
        ③ 끝나지 않을 수 있음을 받아들인다      → 실제로 돌려 본다 (테스트·퍼징·모델 검사의 상한 없는 탐색)
```

- 이 한계를 모르면 두 방향으로 다친다.
  - 도구가 하나 놓친 뒤 "분석기가 있었는데 왜?"라며 도구를 탓하고 갈아 끼운다.
  - 오탐을 "도구 버그"로 보고 경고를 통째로 끈다.

쉬운 예: 맞춤법 검사기는 철자는 잡지만 "문장이 사실과 다른지"는 못 잡는다. 문장의 **뜻**을 판정하는 일이기 때문이다.

똑같은 구조다. 프로그램의 문법은 기계로 검사된다. 프로그램이 **실행되면 무엇을 하는지**(끝나나, 이 함수를 부르나, null을 역참조하나)라는 일반적인 의미 성질은 기계로 완벽히 판정되지 않는다(라이스 정리).

실무 예:
- `javac`가 사람이 보기엔 멀쩡한 코드를 "variable x might not have been initialized"로 거부한다(아래 실험).
- CI가 "무한 루프 검사"로 타임아웃을 건다. 느리지만 정상인 작업이 죽는다.
- 이더리움은 계약 코드가 끝나는지 미리 판정하지 않는다. 실행 단계마다 gas를 매기고 한도를 넘으면 중단한다(ethereum.org gas 문서: "To avoid accidental or hostile infinite loops … each transaction is required to set a limit").

## 동작·원리

### 1. 결정 가능·인식 가능·결정 불가능

```text
  결정 가능(decidable)        입력마다 끝나고 예/아니오를 정확히 답하는 프로그램이 있다
  인식 가능(recognizable)     "예"면 언젠가 끝나며 예라고 답한다. "아니오"면 끝나지 않을 수 있다
  결정 불가능(undecidable)    결정하는 프로그램이 없다

  정지 문제 HALT = { (P, x) : P가 입력 x에서 끝난다 }
     인식 가능 O  — 그냥 돌려 보고, 끝나면 "예"
     결정 가능 X  — "아니오"(영원히 돈다)를 언제 말할지 정할 수 없다
```

- *튜링 기계(Turing machine)*: 무한 테이프와 유한 상태로 계산을 정의한 모델(Turing 1936). 처치–튜링 논제에 따라 "알고리즘으로 할 수 있는 일"을 이 모델로 본다(Sipser 3.3). 이 노트에서는 "Java 프로그램"으로 바꿔 읽어도 된다(메모리 제한은 무시).
- *결정 가능*: 입력이 무엇이든 멈추고 맞게 답하는 판정 프로그램이 있다는 뜻.
- *반결정(semi-decidable)*: 인식 가능과 같은 말.
  - 흔한 오해: "정지 문제는 튜링이 1936년에 그 이름으로 증명했다." 1936년 논문은 계산 가능한 수와 결정 문제(Entscheidungsproblem)를 다뤘다. "halting problem"이라는 이름과 지금 형태의 서술은 Martin Davis의 1958년 책 『Computability and Unsolvability』에 처음 나온다는 지적이 있다(Copeland 2004의 지적, S. Lucas 2021 "The origins of the halting problem"이 근거를 보탬). 같은 논문은 Kleene의 1952년 책이 사실상 지금의 정지 문제를 정식화했다고도 적는다.

### 2. 대각선 논법 — 표로 보기

```text
  프로그램 P_i 를 입력 P_j(의 소스)에 돌렸을 때 끝나나?  (H가 있다고 가정하면 이 표 전체를 계산할 수 있다)

             입력 P1   P2   P3   P4  ...
  P1          끝남    무한  끝남  끝남
  P2          무한    무한  끝남  무한
  P3          끝남    끝남  무한  끝남
  P4          무한    끝남  끝남  끝남
  ...
  D = 대각선을 뒤집은 프로그램:  D(P_i) = "P_i(P_i)가 끝나면 무한 루프, 무한이면 끝남"
  D           무한    끝남  끝남  무한  ...    ← 어느 행 P_i와도 i번째 칸에서 다르다
  그런데 D도 프로그램이니 어떤 행 P_k 여야 한다 → 칸 (k, k)에서 자기 자신과 달라야 한다 → 모순
```

- 칸토어가 실수가 셀 수 없음을 보인 방식과 같은 구조다(Sipser 4.2).

### 3. 정지 문제가 결정 불가능한 이유 — 코드 스케치

```java
// 가정: 이런 메서드가 있고, 어떤 (program, input)에서든 끝나며 정확히 답한다고 하자
static boolean halts(String programSource, String input) { /* ??? */ }

// 그러면 이런 프로그램을 쓸 수 있다
static void d(String src) {
    if (halts(src, src)) { while (true) { } }   // "끝난다"고 하면 영원히 돈다
    // "안 끝난다"고 하면 바로 끝난다
}
// d의 소스를 D라 하고 d(D)를 생각한다
//   halts(D, D) == true  → d(D)는 무한 루프 → 끝나지 않는다 → halts가 틀렸다
//   halts(D, D) == false → d(D)는 바로 끝난다 → halts가 틀렸다
// 어느 쪽이든 모순 → 그런 halts는 없다
```

- 이 증명은 `halts`의 구현을 보지 않는다. **어떤 후보든** 그 후보로 만든 `d`에서 틀린다.

### 실험: 후보 판정기 H를 실제로 만들어 대각선 프로그램에 넣어 보기

후보 H = "B걸음 안에 끝나면 '끝난다'". 넘으면 두 버전이 있다.
- 비관 H: B걸음을 넘으면 "안 끝난다".
- 낙관 H: B걸음을 넘으면 "끝난다".

D는 위 스케치 그대로다. 걸음 수는 중첩 시뮬레이션까지 바깥 예산에 합산한다.

```java
static boolean H(Prog p, Object x, long B, boolean pessimistic, Budget caller) {
    Budget mine = new Budget(B, caller);              // 안쪽 걸음도 바깥 예산에 더해진다
    try { p.run(x, mine); return true; }              // B걸음 안에 끝남 → "끝난다"
    catch (Exceeded e) { if (e.owner != mine) throw e; return !pessimistic; }
}
static Prog D(long B, boolean pessimistic) {
    return (x, b) -> {
        b.tick();
        if (H((Prog) x, x, B, pessimistic, b)) { while (true) b.tick(); }   // "끝난다"면 무한 루프
    };                                                                    // 아니면 끝
}
```

(실험, OpenJDK 21.0.12 Temurin, `docker --cpus=2`, 2026-10-05 — "실제"는 걸음 상한 없이 돌리고 벽시계 3초에서 관찰을 끊었다)

```text
[1] 500만 걸음 뒤 끝나는 프로그램: H(B=100만) = 안 멈춘다, 실제 = 끝남
[2] H(비관, B=1000) 예측 H(D,D) = 안 멈춘다, 실제 D(D) = 끝남
[2] H(낙관, B=1000) 예측 H(D,D) = 멈춘다, 실제 D(D) = 3초 안에 안 끝남(영원히 도는 루프)
```

- [1]: 걸음 상한 판정기는 "느리게 끝나는" 프로그램을 무한 루프로 오판한다. 상한을 늘려도 그보다 느린 프로그램이 있다.
- [2]: 비관 H든 낙관 H든, 그 H로 만든 D에서 정확히 반대로 틀렸다. 증명의 모순이 실행으로 보인다.
- 한계: 낙관 쪽의 "영원히 돈다"는 3초 관찰이다. 코드상 `while (true)`라 끝나지 않는다는 것은 소스로 확인한다.
- 처음 시도에서 B=100만으로 [2]를 돌리자 H → D → H 중첩이 깊어져 `StackOverflowError`가 났다. 그래서 [2]는 B=1000이다.

### 4. 라이스 정리 — 정지 문제 하나가 의미 성질 전부로 번진다

```text
  라이스 정리 (Rice 1953; Sipser 5장 연습 문제, 번호 [?])
  프로그램이 "받아들이는 언어"(어떤 입력에 예라고 답하나)에 대한 성질 Π가
    ① 자명하지 않고(어떤 프로그램은 만족, 어떤 프로그램은 불만족)
    ② 언어에만 의존하면(같은 언어를 받아들이는 두 프로그램은 같은 답)
  → Π를 결정하는 프로그램은 없다

  환원 스케치: "deleteAll()을 부르는가?"를 판정하는 완벽한 분석기 A가 있다고 하자
     정지 문제 입력 (M, w) 를 받으면 아래 프로그램 Q를 만든다:
         Q() { M(w) 를 실행;  deleteAll(); }        (M과 w 안에는 deleteAll 호출이 없다고 하자)
     A(Q) == "부른다"  ⇔  M(w)가 끝난다
     → A로 정지 문제를 푼다 → 모순 → A는 없다
  ※ "deleteAll() 호출"은 받아들이는 언어의 성질이 아니다(같은 언어라도 한쪽만 부를 수 있다).
    그래서 라이스 정리를 그대로 쓰지 않고, 위처럼 정지 문제를 직접 환원해 보인다.
```

- *의미 성질(semantic property)*: 코드 모양이 아니라 실행 동작에 대한 성질. "null을 역참조할 수 있다", "이 비밀번호가 로그로 나갈 수 있다", "끝난다"가 예다.
- *구문 성질(syntactic property)*: 소스 텍스트 모양에 대한 성질. "`System.exit`라는 글자가 있다"는 결정 가능하다. 라이스 정리의 대상이 아니다.
  - 흔한 오해: "라이스 정리 때문에 정적 분석은 쓸모없다." 정리가 막는 것은 **정확하고 언제나 끝나는** 판정기다. 오탐·미탐을 허용한 근사 분석은 가능하고, 실무 도구는 그쪽이다.

### 5. 그래서 분석기는 고른다 — 건전성 vs 완전성

```text
                        실제로 버그 있음        실제로 버그 없음
  분석기 "버그 있음"      참 양성                 오탐 (false positive)
  분석기 "버그 없음"      미탐 (false negative)   참 음성

  건전(sound, "버그 없음"이라 하면 정말 없다) = 미탐 0, 대신 오탐을 낸다
  완전(complete, "버그 있음"이라 하면 정말 있다) = 오탐 0, 대신 미탐을 낸다
  둘 다 + 언제나 끝남  = 라이스 정리로 불가능 (자명하지 않은 의미 성질일 때)
```

- 용어 주의: "건전/완전"의 방향은 분야마다 반대로 쓰기도 한다(논리학·타입 시스템·버그 탐지기). 문서를 읽을 때 "무엇을 놓치지 않는다는 보장인가"로 확인한다.

### 실험: javac의 보수적 확정 대입 검사 (건전한 쪽을 고른 예)

```java
static int f(int n) {
    int x;
    if (n > 0) x = 1;
    if (n <= 0) x = 2;      // 두 if 중 하나는 실행된다 — 사람은 안다
    return x;
}
```

(실험, OpenJDK 21.0.12 `javac`, 2026-10-05)

```text
Conservative.java:6: error: variable x might not have been initialized
        return x;               // javac는 "초기화 안 됐을 수도"라고 거부
               ^
1 error
javac exit=1
```

- JLS 21 16장: "the values of expressions are not taken into account in the flow analysis"(`&&`·`||`·`!`·`? :`와 boolean 상수 식만 특별 취급). `n > 0`과 `n <= 0`이 서로 여집합이라는 사실을 보지 않는다.
- 이 규칙 덕분에 "초기화 안 된 변수 읽기"는 컴파일된 Java에서 생기지 않는다(미탐 0). 대가로 이 코드처럼 멀쩡한 것도 거부한다(오탐).
- 고치는 법은 `if … else`로 구조를 바꾸는 것이다. 더미 초기화(`int x = 0;`)는 오탐을 지우면서 진짜 누락까지 숨길 수 있다(장애 3).

## 쓰이는 자료구조·알고리즘

이 주제가 쓰는 하위 구조:
- 대각선 논법·귀류법(수학 영역, [math 커리큘럼](../../math/README.md)), 환원([40-complexity-p-np](../40-complexity-p-np/2-summary.md)).
- 프로그램을 데이터로 다루기(소스·인코딩), 시뮬레이션(인터프리터).

이 주제를 쓰는 곳(🔧):
- 정적 분석·타입 검사의 한계: 타입은 불변식을 컴파일 시점에 강제하는 건전한 근사다([24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md)).
- 테스트·커버리지의 한계([16-coverage-and-its-limits](../../testing/16-coverage-and-its-limits/2-summary.md)), 속성 기반 테스트([14-property-based-testing](../../testing/14-property-based-testing/2-summary.md)).
- 분산 시스템의 불가능성 결과(FLP 등, [25-impossibility-results](../../distributed/25-impossibility-results/2-summary.md)) — "어떤 알고리즘으로도 안 된다"를 증명하는 같은 계열의 사고.
- 실행 예산 설계: 타임아웃([05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)), 블록체인 gas([31-byzantine-and-blockchain](../../distributed/31-byzantine-and-blockchain/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. "끝나는지 미리 알 수 없다" → 실행 예산으로 막는다

```java
// 사용자 제공 규칙·스크립트 실행: 끝나는지 사전 판정 대신 시간·걸음 예산
ExecutorService ex = Executors.newSingleThreadExecutor();
Future<Result> f = ex.submit(() -> engine.evaluate(rule, input));
try {
    return f.get(2, TimeUnit.SECONDS);
} catch (TimeoutException e) {
    f.cancel(true);                                   // 인터럽트를 확인하는 코드여야 실제로 멈춘다
    throw new RuleBudgetExceeded(rule.id(), "2s");    // "무한 루프"가 아니라 "예산 초과"로 보고한다
}
```

- 예산 초과는 "무한 루프였다"는 증명이 아니다(실험 [1]). 메시지·지표에 "예산 초과"로 남긴다.
- 언어 자체를 제한하는 방법도 있다. 반복 횟수 상한이 문법에 있는 설정 언어, 재귀 없는 규칙 엔진은 정지가 구조로 보장된다. 표현력을 일부 포기하는 대신이다.

### 2. 정적 분석 도구를 고르고 쓰는 법

- 도구 문서에서 "무엇을 놓치지 않는다고 보장하나(건전성)"를 찾는다. 대부분의 버그 탐지 린터는 보장하지 않는다(미탐 있음).
- 오탐은 **억제 사유와 함께** 개별 억제한다(`@SuppressWarnings("…") // 이유`). 규칙을 통째로 끄지 않는다.
- 미탐이 사고로 이어졌다면 도구를 갈아 끼우기 전에, 그 버그 유형을 잡는 **구조**(타입·불변 객체·검증 계층)나 테스트를 더한다.

### 3. javac 오류 읽기

- `variable x might not have been initialized`: 실제로 그런 실행이 있다는 뜻이 아니다. "확정 대입 규칙상" 대입이 보장되지 않는 경로가 있다는 뜻이다. 값으로 추론하지 않는다(JLS 16장).
- `missing return statement`, `unreachable statement`도 같은 계열의 보수적 흐름 분석이다(JLS 14.22).

### 4. 진단 — "멈춘 건가, 느린 건가"

- 스레드 덤프를 간격을 두고 2~3번 뜬다(`jcmd <pid> Thread.print`). 같은 루프 프레임에서 **진행 상태**(카운터·처리 건수 로그)가 바뀌는지 본다.
- 진행 지표(처리 건수·오프셋)를 내보내는 작업은 "느림"과 "멈춤"을 가를 단서를 얻는다(지표 정체는 의심 신호이지 증명은 아니다). 정지 문제는 일반 판정을 막을 뿐, 작업이 스스로 진행 상황을 보고하는 설계는 막지 않는다.

## 장애 시나리오와 대처

### 1. "모든 버그를 잡는 정적 분석기" 기대 → 오탐/미탐 불가피성 오해

- 현상: 정적 분석을 도입했는데 운영 null 버그가 났다. "분석기가 통과시켰다"며 도구를 교체한다. 또는 오탐 수백 건에 질려 전 규칙을 끈다.
- 보이는 형태: 사후 검토에 "분석기 미탐"이 원인으로 적힌다. 경고 수 그래프가 0으로 떨어진 날이 "규칙 비활성화" 커밋과 같다.
- 원인: null 역참조 여부 같은 실행 동작 성질은 정지 문제를 직접 환원해 정확하고 언제나 끝나는 판정이 불가능하다(언어의 성질이면 라이스 정리가 같은 결론을 준다, §4). 언제나 끝나는 도구는 오탐이나 미탐 중 하나를 받아들인다.
- 대처: 도구의 보장 방향을 문서로 확인하고 팀에 공유한다. 오탐은 사유를 달아 개별 억제한다. 미탐 영역은 타입(예: `Optional`, null 금지 주석 + 건전한 검사기)·테스트로 메운다.
- ⚠ 커리큘럼: "'모든 버그를 잡는 정적 분석기' 기대 → 오탐/미탐 불가피성 오해".

### 2. 타임아웃을 "무한 루프 검출"로 착각

- 현상: 데이터가 커진 날 정상 배치가 "무한 루프"로 판정돼 죽고, 재시도마다 같은 지점에서 또 죽는다.
- 보이는 형태: `TimeoutException`, 작업 상태 `KILLED`, 알림 문구 "infinite loop detected". 처리 건수 로그는 계속 늘고 있었다.
- 원인: 걸음·시간 상한은 "느리게 끝나는 것"과 "안 끝나는 것"을 구분하지 못한다(실험 [1]).
- 대처: 알림 문구를 "예산 초과"로 바꾼다. 진행 지표를 함께 보고, 진행 중이면 연장·분할 처리한다. 예산은 입력 크기에 비례해 정한다.

### 3. 보수적 컴파일러 오류를 더미 초기화로 회피 → 진짜 누락이 숨는다

- 현상: 새 분기를 추가했는데 그 경로에서 값이 0으로 계산돼 잘못된 금액이 나간다. 예외는 없다.
- 보이는 형태: 로그·예외 없음. 결과 값만 이상하다. 코드에 `int amount = 0; // 컴파일 오류 회피`.
- 원인: `might not have been initialized` 오탐을 지우려고 넣은 기본값이, 이후 실제 누락 경로까지 조용히 통과시켰다.
- 대처: `if … else`·`switch` 식(Java 14+의 `switch` 식은 경우를 빠짐없이 다루도록 요구한다)으로 구조를 바꿔 컴파일러가 검사하게 둔다. 더미 기본값을 리뷰에서 막는다.

### 4. 사용자 제공 코드에 실행 예산이 없다

- 현상: 고객이 올린 규칙(스크립트·정규식·템플릿) 하나가 워커 스레드를 영원히 붙잡는다. 워커 풀이 차례로 고갈된다.
- 보이는 형태: 활성 스레드 수가 풀 최대치에 붙는다. 큐 대기 증가. 스레드 덤프에 같은 평가 프레임.
- 원인: 업로드 시점에 "끝나는가"를 검사하려 했지만 일반적으로 불가능하다(정지 문제). 실행 예산을 두지 않았다.
- 대처: 시간·걸음·메모리 예산, 인터럽트 확인, 격리 실행(별도 스레드 풀·프로세스). 이더리움 gas처럼 단계마다 비용을 매기고 한도에서 중단하는 방식도 같은 생각이다.

## 핵심 문장

- 정지 문제는 결정 불가능하다. 어떤 후보 판정기든, 그 판정기로 만든 대각선 프로그램에서 틀린다.
- 정지 문제는 인식 가능하다. 끝나는 경우는 돌려 보면 알지만, 안 끝나는 경우는 언제 "안 끝난다"고 말할지 정할 수 없다.
- 라이스 정리: 프로그램이 받아들이는 언어의 자명하지 않은 성질은 정확하고 언제나 끝나는 판정기가 없다. 언제나 끝나는 정적 분석기는 오탐이나 미탐 중 하나를 받아들인다(끝나지 않을 수 있음을 받아들이는 길도 있다).
- javac의 확정 대입 검사는 미탐 0을 고르고 오탐을 받아들인 건전한 근사다.
- 끝나는지 미리 못 아니까 실무는 실행 예산(타임아웃·gas)으로 막고, 예산 초과를 무한 루프라고 부르지 않는다.

## 관련 주제·근거

선행·후속:
- 선행: P·NP·환원([40-complexity-p-np](../40-complexity-p-np/2-summary.md)).
- 함께: 타입과 불변식([24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md)), 커버리지의 한계([16-coverage-and-its-limits](../../testing/16-coverage-and-its-limits/2-summary.md)), 분산 불가능성 결과([25-impossibility-results](../../distributed/25-impossibility-results/2-summary.md)), 타임아웃([05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)). 커리큘럼 표는 [../curriculum.md](../curriculum.md).

근거:
- A. M. Turing, "On Computable Numbers, with an Application to the Entscheidungsproblem", Proc. London Math. Soc., 1936.
- H. G. Rice, "Classes of Recursively Enumerable Sets and Their Decision Problems", Trans. AMS, 1953.
- Sipser 『Introduction to the Theory of Computation』 3판 2부 계산 가능성 이론 — 3장(처치–튜링 논제), 4장(결정 가능성, 4.2 대각선 논법·결정 불가능성), 5장(환원 가능성, 라이스 정리는 연습 문제). 세부 정리·문제 번호는 확인 못 함 [?].
- S. Lucas, "The origins of the halting problem", J. Logical and Algebraic Methods in Programming 2021, doi:10.1016/j.jlamp.2021.100687(초록을 OpenAlex로 확인) — https://www.sciencedirect.com/science/article/pii/S235222082100050X ("halting problem" 명칭의 출처).
- JLS SE 21 16장 Definite Assignment — https://docs.oracle.com/javase/specs/jls/se21/html/jls-16.html , 14.22 Unreachable Statements.
- ethereum.org, "Gas and fees" — https://ethereum.org/developers/docs/gas/

실험 목록(전부 2026-10-05, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`):
- 후보 판정기 H(걸음 상한) vs 느린 프로그램·대각선 프로그램 D: `Halting.java`.
- javac 확정 대입 오탐: `Conservative.java`(`javac` 컴파일 오류 출력).
