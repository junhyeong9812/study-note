# software-design/17-error-messages-and-log-level-policy — 정답

## 정답

### 1. 세 독자

- 사용자: 무엇을 하면 되나(고칠 입력, 다시 시도할 시점).
- 운영자: 지금 사람이 움직여야 하나(알람).
- 개발자: 어디서 왜(스택 트레이스·SQLState·문맥).
- 열쇠: 에러 코드(실패 종류)와 incidentId(요청 ID). 응답과 로그에 같이 넣는다.

### 2. RFC 5424의 Severity

- §6.2.1 Table 2에 0 Emergency ~ 7 Debug를 두지만 "Facility and Severity values are not normative but often used"라고 적는다.
- 그래서 무엇을 ERROR로 찍을지는 팀이 조작적으로 정해야 한다. OWASP Logging Cheat Sheet도 분류를 조직이 일관되게 문서화하라고 적는다.

### 3. 조작적 정의

- ERROR: 지금 사람이 조치해야 하나?
- WARN: 자동으로 회복했지만 추세를 봐야 하나?
- INFO: 정상 흐름의 주요 사건인가?
- DEBUG: 조사할 때만 켤 세부인가?
- 4xx 검증 실패는 서버가 정상 동작한 결과라 INFO(또는 기록 없이 코드별 카운터). 급증은 지표로 본다. 이 표는 팀 규칙의 예이고 표준의 규정이 아니다.

### 4. 두 정책

(실험 A, JDK 21.0.12, 2026-10-01)

```text
정책 A(실패=ERROR)    레벨별={ERROR=48, INFO=952}  ERROR 중 사람이 조치할 것=2/48
정책 B(조작적 정의)      레벨별={ERROR=2, INFO=994, WARN=4}  ERROR 중 사람이 조치할 것=2/2
```

- A: ERROR 48건, 조치 대상 2건. B: ERROR 2건, 전부 조치 대상. 재시도 후 성공 4건은 B에서 WARN.

### 5. SQL 원문 노출과 분리

(실험 B)

```text
[나쁨] 응답 본문에 원문 노출:
  {"status":500,"message":"Table \"ORDERS_V2\" not found (this database is empty); SQL statement: select amount from orders_v2 where customer_id = 1001 [42104-232]"}
```

- 표 이름·SQL 문·DB 에러 코드가 보인다(공격 단서).
- 분리한 응답: problem+json에 사용자 문구(`detail`), 에러 코드(`INTERNAL`), `incidentId`.
- 서버 로그: 같은 `incidentId`와 `sqlState`·벤더 코드·메시지·스택 트레이스를 한 번.

### 6. `detail`과 에러 코드

- `detail`은 클라이언트가 문제를 고치는 데 초점을 두고 디버깅 정보를 담지 않는다(§3.1.4). 스택 덤프 같은 구현 세부를 HTTP로 노출하지 말라고 §5가 권한다.
- 클라이언트는 `detail`을 파싱하지 않는다("Consumers SHOULD NOT parse the "detail" member").
- 그래서 분기용으로 안정된 에러 코드(확장 필드)를 둔다. 문구는 바뀌어도 코드는 유지된다.

### 7. catch-log-rethrow

- 같은 사건이 계층 수만큼 기록돼 ERROR 수가 부풀고 스택 트레이스가 반복된다. 15의 실험에서 3계층 + 최상위는 SEVERE 4건·62줄, 경계 한 번은 1건·16줄이었다. 레벨을 잘 정해도 알람 수가 배로 늘어난다.

### 8. 로그 주입

(실험 C)

```text
2026-10-01T09:59:59Z WARN login failed user=mallory
2026-10-01T10:00:00Z INFO login success user=admin
```

- 일어나지 않은 "admin 로그인 성공" 줄이 생긴다.
- 막는 법: CR·LF를 이스케이프하거나(`\n`으로 기록) JSON 구조화 로그를 쓴다. OWASP Logging Cheat Sheet·CWE-117.

### 9. "오류가 발생했습니다"

- 빠진 것: 에러 코드와 incidentId(요청 ID). 로그와 문의를 이을 고리가 없다.
- 고치는 법: 응답과 화면에 코드 + incidentId를 보여 준다. 이 값은 내부 구현을 드러내지 않으면서 서버 로그의 같은 ID 줄을 바로 찾게 한다. 상세(SQL·스택)는 계속 로그에만 둔다.
