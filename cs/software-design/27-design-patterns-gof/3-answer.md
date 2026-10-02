# software-design/27-design-patterns-gof — 정답

## 정답

### 1. 패턴의 이름과 비용

- 특정 맥락에서 반복되는 설계 문제와 해법의 짝에 붙인 이름이다. GoF(1994)가 23개를 생성 5·구조 7·행위 11로 정리했다.
- 이름이 있으면 구조·장단점·대안을 한 단어로 전달해 리뷰와 코드 읽기가 빨라진다("여기 Strategy").
- 비용: 한 축의 변경을 싸게 하는 대신 간접 계층(인터페이스·위임 단계)이 늘어난다. 축이 실제로 안 바뀌면 비용만 남는다.

### 2. 고르는 순서

1. 바뀌는 것이 무엇인가(git log 변경 이력) 2. 그 변경이 지금 몇 곳을 건드리나 3. 언어 기능으로 충분한가 4. 프레임워크가 이미 하나 5. 그래도 아프면 가장 작은 형태의 패턴.
- 언어 기능 예: Visitor 대신 `sealed` + 패턴 매칭 `switch`, Strategy 대신 `Function` 람다, Command 대신 record 값.

### 3. 변경 1

(실험 A, 2026-10-02)

```text
  [plain]  1 file changed, 1 insertion(+), 1 deletion(-)
  [pattern]  1 file changed, 1 insertion(+), 1 deletion(-)
```

- 둘 다 1파일 1줄. 간접 계층은 규칙 수정에 도움이 없었다.

### 4. 변경 2·3

```text
== 변경2(결제수단별요율)
  [plain]  1 file changed, 10 insertions(+), 3 deletions(-)
  [pattern]  6 files changed, 19 insertions(+), 6 deletions(-)
== 변경3(가상계좌추가)
  [plain]  1 file changed, 2 insertions(+), 1 deletion(-)
  [pattern]  3 files changed, 5 insertions(+), 1 deletion(-)
```

- 변경 2는 pattern 판이 더 컸다. 미리 만든 팩토리 `create()`에 인자가 없어 "결제 수단"이라는 실제 축을 넣으려면 `FeeCalculator`·`FeeService` 시그니처를 층마다 고쳐야 했다 — 예측한 축과 실제 축이 달랐다. 6파일에는 진입점 `Main.java`가 들어 있다(plain은 main이 `Fees.java` 안). Main을 빼도 5파일이다.
- 변경 3은 축이 생긴 뒤라 둘 다 작았다.

### 5. 결론이 뒤집히는 경우

- 변형을 다른 모듈·팀·플러그인이 추가해 중앙 `switch`를 고칠 수 없을 때, 변형마다 상태나 연산이 여럿이라 한 `switch`에 다 담기 어려울 때.
- 이 실험은 그 경우를 재지 않았다(한 저장소·한 팀·변형 4개). 노트에도 그 범위를 적었다.

### 6. 리스너 예외

(실험 B1·B3)

```text
  ArrayList, 격리 없음
    리스너1 메일 발송 order#1
    publish 예외: IllegalStateException: 리스너2 포인트 적립 실패
[B3] Spring 6.2.11 이벤트: 리스너2가 예외를 던지면
    리스너1 order#3
    publishEvent 예외: IllegalStateException: 리스너2 실패
```

- 둘 다 리스너3이 불리지 않았다. 예외는 발행자에게 전파됐다.
- 근거: `SimpleApplicationEventMulticaster.setErrorHandler` javadoc — 기본은 없음, 리스너 예외가 현재 멀티캐스트를 멈추고 발행자에게 전파된다. 리스너마다 try/catch로 격리하자 리스너3까지 불렸다.

### 7. 순회 중 구독 해지

```text
  ArrayList
    1회용 리스너 order#2 → 구독 해지
    publish 예외: java.util.ConcurrentModificationException
  CopyOnWriteArrayList
    1회용 리스너 order#2 → 구독 해지
    리스너B order#2
    리스너C order#2
```

- `ArrayList`는 순회 중 구조 변경을 감지해 예외. `CopyOnWriteArrayList`는 순회 시작 시점의 배열을 돌아 나머지도 불렀다.
- 단, `ArrayList`에서 해지하는 리스너가 끝에서 두 번째이면 예외 없이 마지막 리스너가 조용히 빠진다(점검 재실행). fail-fast는 최선 노력이라 예외로 버그를 잡는다고 기대할 수 없다.

### 8. Composite의 `StackOverflowError`

- 원인: 부모가 자손 밑에 추가돼(또는 `parent_id` 데이터 오류로) 트리가 순환 그래프가 됐고, 재귀 합계가 끝나지 않는다(실험 C).
- 대처: `add` 때 조상 검사로 순환 거부, 트리 재구성 시 방문 집합(DFS 색칠)으로 순환 탐지, DB 쪽 순환 금지 검증.

### 9. 저자 표기

- 원본은 "Martin Fowler, 'Refactoring to Patterns'"라고 적었지만 저자는 Joshua Kerievsky(Addison-Wesley, 2004)다. Fowler는 소개 글을 썼다.
- 접근: GoF 패턴을 미리 설계하지 않고, 시스템이 자라면서 작은 리팩터링 단계로 패턴에 도달한다(Fowler 소개 글). 카탈로그에는 27개 리팩터링이 있고 Inline Singleton처럼 패턴에서 멀어지는 것도 있다.
