# api-design/04-error-format-problem-details — 정답

## 정답

### 1. 형식 표준화가 필요한 이유

- 상태 코드는 분류만 준다. 무슨 문제인지, 어느 입력이 틀렸는지, 어떻게 고치는지, 어느 발생 건인지는 본문에 담아야 한다.
- 형식이 없을 때
  - **클라이언트 파싱 실패**: 형식마다 처리 코드가 필요하고, 처음 보는 형식(HTML 오류 페이지 등)에서 파싱이 실패한다.
  - **내부 정보 노출**: 정해진 틀이 없으니 예외 메시지·스택 트레이스를 그대로 내보내기 쉽다.

### 2. Problem Details 한 개

```text
  HTTP/1.1 403 Forbidden
  Content-Type: application/problem+json
  {
   "type": "https://example.com/probs/out-of-credit",    기계용(주 식별자)
   "title": "You do not have enough credit.",            사람용(유형 요약)
   "status": 403,                                        기계용 사본(참고)
   "detail": "Your current balance is 30, but that costs 50.",   사람용(이번 건)
   "instance": "/account/12345/msgs/abc",                발생 건 식별(지원·추적용)
   "balance": 30                                         확장 — 기계용 값
  }
```

### 3. 멤버 규칙

- `type`: 소비자는 문제 유형의 주 식별자로 써야 한다(MUST). 자동 역참조는 하지 않아야 한다(SHOULD NOT). 없으면 `about:blank`로 간주.
- `title`: 발생마다 바뀌지 않아야 한다(SHOULD NOT, 현지화 제외). `about:blank`이면 상태 코드 표준 문구와 같아야 한다(SHOULD).
- `detail`: 소비자는 파싱해서 정보를 뽑지 않아야 한다(SHOULD NOT). 확장 멤버가 맞는 길이다.
- `status`: 참고용. 생성자는 실제 HTTP 응답과 같은 코드를 써야 한다(MUST). 범용 소프트웨어는 HTTP 상태를 쓴다.
- 멤버 값 타입이 명세와 다르면 그 멤버는 무시해야 한다(MUST, §3.1).
- 모르는 확장 멤버는 무시해야 한다(MUST, §3.2). 문제 유형이 진화할 수 있게 하려는 것이다.

### 4. 새 문제 유형 정의

- 반드시 문서화(MUST, §4): `type` URI, 적절한 `title`, 함께 쓸 HTTP 상태 코드.
- `type` URI는 해결 방법을 설명하는 HTML 문서로 이어지는 게 좋다(SHOULD).
- 만들지 말 경우
  - 어떤 자원에나 해당하는 범용 문제: 상태 코드로 충분하다(예: PUT에 403).
  - 구현 디버깅 정보를 내보내려는 목적: Problem Details는 디버깅 도구가 아니다.
  - 이미 앱 전용 오류 형식이 있으면 그것을 쓰는 편이 낫다고 RFC가 적는다(§4.1).

### 5. Spring Boot 4.1.1 기본 응답

(실험, Spring Boot 4.1.1 · Spring Framework 7.0.9)

| 호출 | 기본값 | `problemdetails` 켬 |
|---|---|---|
| `/orders/7`(도메인, 직접 처리) | 404 `application/problem+json` [detail, instance, status, title, type, orderId] | 같음 |
| `/orders/abc`(프레임워크) | 400 `application/json` [timestamp, status, error, path] | 400 `application/problem+json` [detail, instance, status, title] |
| `/boom`(처리 안 된 예외) | 500 `application/json` [timestamp, status, error, path] | **그대로** 500 `application/json` |

- 기본값에서 한 앱이 두 형식을 낸다. `problemdetails`는 Spring MVC 예외(`ResponseEntityExceptionHandler` 범위)만 바꾸고 처리 안 된 일반 예외는 덮지 않았다. 마지막 그물(`@ExceptionHandler(Exception.class)`)을 직접 둬야 통일된다.

### 6. 트레이스 노출 설정

- `server.error.include-stacktrace=always`: Spring Boot 4.1.1에서는 반영되지 않았다(키 [timestamp, status, error, path]). Boot 4.0부터 `server.error.*`가 `spring.web.error.*`로 바뀌었기 때문이다(메타데이터: deprecation level error, since 4.0.0).
- `spring.web.error.include-stacktrace=always`(+ `include-message=always`): `/boom` 본문이 4622자로 커지고 `trace`·`message`가 생겼다.
- 노출된 것: 예외 클래스(`java.lang.IllegalStateException`), SQL 문(`insert into member (email,password_hash) ...`), 제약 조건 이름(`uk_member_email`), 소스 위치(`ex.App.boom(App.java:25)`), 프레임워크 내부 호출 경로.
- 교훈: 설정 파일만 보고 판단하지 말고 실제 응답으로 확인한다. 운영에서는 트레이스·메시지를 응답에 넣지 않는다.

### 7. 여러 오류 담기

- 같은 유형의 여러 발생: 유형이 정의한 확장 배열(`errors`)에 담고, 각 항목에 `detail`과 요청 본문 위치를 가리키는 JSON Pointer(`"#/profile/color"`)를 둔다(RFC 9457 §3 예시).
- 서로 다른 유형이 섞이면: 가장 관련 있거나 급한 문제 하나를 응답하는 것이 권장(RECOMMENDED). 서로 다른 유형을 묶는 배치 유형은 HTTP 의미와 잘 맞지 않는다고 적는다.

### 8. 세 형식 대응

| 역할 | RFC 9457 | Google AIP-193 | Stripe |
|---|---|---|---|
| 기계용 식별자 | `type` | `ErrorInfo.reason` + `domain`(+`metadata`) | `code`(일부), `type` 4종 |
| 사람용 설명 | `title`, `detail` | `message`, `LocalizedMessage` | `message` |
| 어느 입력이 | 확장(`errors[].pointer` 등) | `BadRequest` 상세 | `param` |

### 9. `Unexpected character '<'`와 `type` null

- 원인 후보
  - `'<'`: 게이트웨이·LB·서블릿 컨테이너가 만든 HTML 오류 페이지(502·504·413 등)를 JSON으로 파싱했다.
  - `type` null: 프레임워크 기본 오류 형식(`timestamp·status·error·path`)처럼 problem+json이 아닌 본문. 실험에서 Jackson 2.19.2로 읽으면 예외 없이 `type=null`이 됐다.
- 서버 대처: 마지막 그물까지 problem+json으로 통일, 앞단 오류 페이지도 맞추거나 최소한 `Content-Type`을 정확히.
- 클라이언트 대처: `Content-Type`이 `application/problem+json`일 때만 문제 상세로 파싱하고, 아니면 상태 코드 분류로만 처리한다. 모르는 필드는 무시.

### 10. `detail`에서 숫자 뽑기

- 문제: RFC 9457 §3.1.4는 소비자가 `detail`을 파싱하지 않아야 한다고 적는다(SHOULD NOT). 문구는 사람용이라 다국어화·문구 개선으로 바뀐다. 바뀌면 계산이 조용히 틀린다(01의 Hyrum).
- 서버 변경: 필요한 값을 확장 멤버로 준다. RFC 예시 그대로 `"balance": 30`을 두고, 필요한 금액도 `"required": 50`처럼 따로. 충전 경로는 `accounts` 같은 링크 확장으로.
- 클라이언트: `type`으로 "잔액 부족"을 판별하고, 확장 멤버 값으로 계산한다.
