# software-design/08-function-design — 정답

## 정답

### 1. 시그니처는 약속

- 호출자는 이름·인자·반환 타입만 보고 함수를 쓴다. 본문을 열지 않아도 되게 하는 것이 함수의 가치다.
- 질의 이름(`get`·`is`)의 함수가 상태를 바꾸면, 로그·디버거·`toString()`·모니터링처럼 "읽기만 한다"고 믿고 부르는 코드가 결과를 바꾼다. Ousterhout–Martin 대담의 `isMultipleOfNthPrimeFactor`도 이름은 술어인데 부작용이 있어 읽는 사람을 속인 예다.

### 2. 로그 한 줄이 바꾼 수수료

(실험 A, JDK 21.0.12, 2026-10-02)

```text
1회 getBalance() = 10000
2회 getBalance() = 10100
디버그 로그 끔: fee = 500, auditLog 1건
디버그 로그 켬: fee = 0, auditLog 2건
CQS 분리, 로그 끔: fee = 0
CQS 분리, 로그 켬: fee = 0
```

- 두 번 부르면 10,000 → 10,100. 첫 호출이 캐시를 갱신했다.
- 로그를 켜면 로그가 먼저 옛값을 소비하고 판정은 새값을 봐서 수수료 0원. 끄면 판정이 옛값을 봐서 500원.
- CQS 분리: `refresh()`를 한 번 명시적으로 부르고 `balance()`는 상태를 안 바꾸므로 로그와 무관하게 0원.

### 3. CQS의 예외

- Fowler(2005)는 스택 `pop`처럼 상태를 바꾸는 질의가 유용한 관용구라고 든다. Java `Iterator.next()`는 값을 주면서 전진하는 예로 들고, 자신은 `advance`·`current`를 나눈 쪽을 선호한다고 쓴다.
- `pop`·`next`는 이름이 "꺼낸다·전진한다"는 명령을 드러낸다. `getBalance()`는 이름이 순수 조회를 약속하면서 명령을 숨겼다. 문제는 부작용 자체보다 **이름과 동작의 불일치**다.

### 4. 플래그 순서 실수

(실험 B)

```text
== [bad]   saved o-1 +알림발송   (exit 0)
== [good]  Flags.java:12: error: incompatible types: Audit cannot be converted to Notification
```

- boolean 쪽은 컴파일되고 실행된다. 의도(감사 로그만)의 정반대로 알림만 나갔다.
- enum 쪽은 같은 실수가 컴파일 오류가 된다. 더 나아가면 `saveWithAuditOnly(order)`처럼 플래그를 없앤다.

### 5. 분해와 복잡도

(실험 C, PMD 7.28.0)

- 최댓값: mixed `report` 순환 9(인지 12, NPath 36). split은 `discountOf` 순환 5가 최대(인지 5), NPath 최대는 `sql` 6.
- 합: mixed 9, split 2+1+4+5 = 12.
- "없앤다"고 말할 수 없다. 합은 오히려 늘었다. 분해는 복잡도를 이름 붙은 조각으로 나눠 담아, 한 번에 이해할 양과 변경이 닿는 범위를 줄인다.

### 6. 기본 임계

- PMD 7.28.0 문서 기본값: `ExcessiveParameterList` 10, `CyclomaticComplexity` 메서드 10(클래스 합 80), `CognitiveComplexity` 15, `NPathComplexity` 200.
- 실험 C mixed(순환 9·인지 12·NPath 36)는 기본 설정에서 **보고되지 않는다**. 실험은 임계를 1로 낮춰 값을 출력했다. 지표 통과가 좋은 설계를 뜻하지 않는다.

### 7. 길이 vs 깊이

- Martin: 함수는 작아야 하고, 그보다 더 작아야 한다(APOSD 9.8 인용).
- Ousterhout: 몇십 줄 수준부터는 더 줄여도 이득이 적고, 지나치게 나누면 함께 읽어야 하는 conjoined methods가 된다. "Depth is more important than length."
- 대담 요약: 둘 다 분해와 얽힘 회피를 중시하지만 가중치가 다르다.
- 판정 질문: **호출자가 나눈 함수의 본문을 열지 않고 쓸 수 있나?**

### 8. 정책 변경이 SQL을 깨뜨림

- 의심: 할인 정책과 SQL 조립이 한 함수에 있다(추상화 수준 혼합). 정책을 고치던 손이 같은 함수 안 SQL 줄을 건드렸다(병합 해결 등).
- 근거: 실험 C에서 같은 정책 변경의 hunk header가 mixed는 `report(...)`, split은 `discountOf(...)`였다.
- 고치기: `OrderQuery.sql()`과 `DiscountPolicy.discountOf()`로 나눈다(Extract Function·Split Phase). SQL은 쿼리 문자열 테스트로 지킨다.

### 9. 가드 절과 출력 인자

- 가드 절은 중첩을 없애 **인지 복잡도**를 줄인다. SonarSource 정의는 중첩된 흐름 단절에 추가 증가를 준다. 순환 복잡도는 분기 수가 같으면 그대로일 수 있다.
- 출력 인자: 결과를 반환하지 않고 인자로 받은 객체를 바꿔 전하는 것(`collectOverdue(List out)`). 시그니처에서 변경이 안 보인다. 반환값으로 바꾼다(`List<Invoice> overdueInvoices()`).
