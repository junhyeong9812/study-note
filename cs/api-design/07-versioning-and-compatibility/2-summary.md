# api-design/07-versioning-and-compatibility — 하위 호환 규칙·버저닝·폐기(Deprecation/Sunset) — 정리 (힌트)

## 해결하는 문제

API를 공개하면 서버는 바꿀 수 있어도 클라이언트는 바꿀 수 없다.

```text
  서버 배포: 하루에 여러 번, 우리가 정한다
  클라이언트: 모바일 앱 구 버전, 파트너사 배치, 3년 전 스크립트 — 언제 바뀔지 우리가 못 정한다

  시간 →   서버 v1 ──── 서버 v2 ──── 서버 v3
           앱 1.0 ─────────────────────────────▶ (업데이트 안 한 사용자)
           앱 2.0           ───────────────────▶
           파트너 배치(v1 기준) ─────────────────▶
```

- 그래서 서버 변경 하나하나가 "지금 살아 있는 모든 구 클라이언트와 아직 맞나"라는 질문이 된다.
  - *하위 호환(backward compatible) 변경*: 구 클라이언트가 고치지 않아도 계속 동작하는 서버 변경.
  - *파괴적 변경(breaking change)*: 구 클라이언트 중 일부라도 고쳐야 동작하는 변경.

쉬운 예: 콘센트 규격이다.
- 콘센트에 USB 구멍을 **추가**해도 기존 플러그는 꽂힌다.
- 구멍 모양을 **바꾸면** 기존 플러그는 전부 못 꽂는다.

똑같은 구조다.\
API에서 "구멍 추가"는 새 필드·새 엔드포인트다. "모양 변경"은 필드 삭제·이름 변경·타입 변경·의미 변경이다.

실무 예:
- 주문 상태 enum에 `REFUNDED`를 추가했다. 엄격하게 역직렬화하던 구 앱이 주문 목록 화면에서 예외를 낸다.
- 응답에서 `amount`를 빼고 `amount_v2`로 옮겼다. 구 클라이언트는 에러 없이 금액을 0으로 보여 준다.
- `/v1`을 공지 없이 내렸다. 아직 호출하던 파트너 배치가 새벽에 전부 실패한다.

## 동작·원리

### 1. 호환의 두 방향

```text
                     읽는 쪽
                 구 코드          새 코드
  쓰는 쪽  구 데이터   (당연)       backward 호환 = 새 코드가 옛 데이터를 읽는다
          새 데이터   forward 호환   (당연)
                     = 옛 코드가 새 데이터를 읽는다
```

- DDIA 4장의 정의(1판, 인용 요약 경유로 확인)
  - *backward 호환*: 새 코드가 옛 코드가 쓴 데이터를 읽는다.
  - *forward 호환*: 옛 코드가 새 코드가 쓴 데이터를 읽는다. 옛 코드가 "모르는 추가분을 무시"해야 해서 더 어렵다.
- API에 대입하면
  - 서버가 새 응답을 내고 구 클라이언트가 읽는다 → 클라이언트 쪽에서 **forward 호환**이 필요하다.
  - 구 클라이언트가 옛 요청을 보내고 새 서버가 읽는다 → 서버 쪽에서 **backward 호환**이 필요하다.
- 요청과 응답은 방향이 반대다. 그래서 같은 "필드 추가"도 어느 쪽이냐에 따라 안전성이 다르다.

### 2. 변경 분류표

```text
  응답(서버 → 클라이언트)                요청(클라이언트 → 서버)
  ─────────────────────────            ─────────────────────────
  필드 추가      안전*                 선택 필드 추가        안전
  enum 값 추가   조건부(클라 관대할 때)  필수 필드 추가        파괴
  필드 삭제      파괴                  필드 삭제(서버가 무시) 대개 안전
  이름·타입 변경 파괴                  검증 강화(길이 축소)  파괴
  의미 변경      파괴(에러 없이)        enum 값 추가         안전
  * 클라이언트가 모르는 필드를 무시할 때만
```

- Google AIP-180(Backwards compatibility)의 분류
  - 세 종류의 호환: *소스 호환*(기존 코드가 새 버전에 대해 컴파일·실행), *와이어 호환*(구 클라이언트가 새 서버와 통신), *의미 호환*(동작이 합리적 기대와 맞음).
  - 허용: 새 인터페이스·메서드·메시지·필드·enum·enum 값 추가.
  - 금지: 삭제·이름 변경, 필드 타입 변경, 기본값 변경, 문자열 길이 제한 변경, 값 형식·생성 알고리즘 변경 등.
  - enum 값: "요청에만 쓰는 enum은 자유롭게 추가할 수 있다". 응답 enum은 허용하되 "사용자 코드가 새 값을 우아하게 처리하지 못할 수 있다"고 경고한다.
  - 의미 변경: "합리적인 사용자 코드를 깨뜨릴 만한 방식으로 보이는 동작이나 의미를 바꾸면 안 된다".
- Stripe(2017 블로그 "APIs as infrastructure: future-proofing Stripe with versioning", Brandur Leach): "전에 있던 필드는 계속 있어야 하고, 같은 타입과 이름을 유지해야 한다."
- 분류표는 **회사 관례**다. RFC가 정한 것이 아니다. AIP는 Google API용 권고, Stripe는 자사 API의 약속이다.

### 3. 관대한 읽기 — 호환의 절반은 클라이언트 몫

```text
  서버 v2 응답  {"id":1,"amount":5000,"status":"REFUNDED","memo":"gift"}
                                       ▲새 enum 값          ▲새 필드
  엄격한 클라이언트: 모르는 것을 만나면 예외  → 서버의 "안전한 추가"가 장애가 된다
  관대한 클라이언트: 모르는 필드는 버리고, 모르는 enum은 UNKNOWN으로
```

- Fowler "TolerantReader"(2011-05-09): 받는 쪽은 필요한 것만 꺼내고 모르는 것은 무시하라. Postel의 법칙 "보내는 것은 보수적으로, 받는 것은 너그럽게"를 서비스 연동에 적용한 것이다(저자 주장).
- 서버가 "필드 추가는 안전"이라고 말할 수 있는 근거는 **클라이언트가 관대하다는 가정**이다. 이 가정은 라이브러리 기본값에 달려 있다.

### 실험: Jackson 기본값이 "안전한 추가"를 장애로 바꾼다

v1 클라이언트 DTO(`id`·`amount`·`status{PAID}`)가 v2 서버 응답 세 가지를 받는다.

```java
public enum Status { PAID }                                   // v1이 아는 값
public enum TolerantStatus { PAID, @JsonEnumDefaultValue UNKNOWN }
public static class OrderV1 { public long id; public long amount; public Status status; }

static final String ADD_FIELD = "{\"id\":1,\"amount\":5000,\"status\":\"PAID\",\"memo\":\"gift\"}";
static final String ADD_ENUM  = "{\"id\":2,\"amount\":5000,\"status\":\"REFUNDED\"}";
static final String REMOVE    = "{\"id\":3,\"status\":\"PAID\"}";      // v2가 amount를 뺐다

ObjectMapper strict = new ObjectMapper();                      // Jackson 2.x 기본값
ObjectMapper tolerant = new ObjectMapper()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .enable(DeserializationFeature.READ_UNKNOWN_ENUM_VALUES_USING_DEFAULT_VALUE);
tools.jackson.databind.ObjectMapper j3 = new tools.jackson.databind.ObjectMapper();  // Jackson 3.x 기본값
```

(실험, maven:3.9-eclipse-temurin-21 / JDK 21.0.11, Jackson 2.19.2 · 3.0.0, 2026-10-04)

```text
Jackson2 version=2.19.2 FAIL_ON_UNKNOWN_PROPERTIES=true
[J2 기본] 필드 추가 -> UnrecognizedPropertyException: Unrecognized field "memo" (class exp.Compat07$OrderV1), not marked as ignorable (3 known properties: "amount", "status", "id"])
[J2 기본] enum 값 추가 -> InvalidFormatException: Cannot deserialize value of type `exp.Compat07$Status` from String "REFUNDED": not one of the values accepted for Enum class: [PAID]
[J2 기본] 필드 삭제(long) -> OK id=3 amount=0 status=PAID
[J2 기본] 필드 삭제(Long) -> OK id=3 amount=null status=PAID
[J2 관대] 필드 추가 -> OK id=1 amount=5000 status=PAID
[J2 관대] enum 값 추가 -> OK id=2 amount=5000 status=UNKNOWN
Jackson3 version=3.0.0 FAIL_ON_UNKNOWN_PROPERTIES=false
[J3 기본] 필드 추가 -> OK id=1 amount=5000 status=PAID
[J3 기본] enum 값 추가 -> InvalidFormatException: Cannot deserialize value of type `exp.Compat07$Status` from String "REFUNDED": not one of the values accepted for Enum class: [PAID]
[J3 기본] 필드 삭제(long) -> OK id=3 amount=0 status=PAID
```

관찰
- Jackson 2.19.2 기본값에서는 서버의 **필드 추가**도 클라이언트 예외가 된다(`FAIL_ON_UNKNOWN_PROPERTIES=true`).
- **enum 값 추가**는 Jackson 2.19.2와 3.0.0 모두 기본값에서 실패했다. 커리큘럼 ⚠ 칸의 "엄격 역직렬화 클라이언트 실패"가 이것이다.
- **필드 삭제**는 어느 설정에서도 예외가 나지 않았다. 원시 `long`은 0, `Long`은 null이 된다. 엄격한 설정도 삭제를 잡아 주지 않는다. 금액 0원이 화면에 조용히 나간다.
- Jackson 3.0.0은 `FAIL_ON_UNKNOWN_PROPERTIES` 기본값이 false였다(이 실행에서 확인). 의도된 변경이다 — jackson-databind 3.0.0 소스의 `DeserializationFeature`는 `FAIL_ON_UNKNOWN_PROPERTIES(false)`이고 주석에 "disabled by default as of Jackson 3.0 (in 2.x it was enabled)"라고 적는다(3.0 릴리스 노트 "Config default changes" #493). 같은 코드라도 메이저 버전에 따라 결과가 갈린다.
  - 같은 3.0에서 `FAIL_ON_NULL_FOR_PRIMITIVES`는 반대로 기본 true가 됐다(같은 소스). 원시 타입 필드에 JSON `null`이 **명시적으로** 오면 3.0은 실패한다. 이 실험의 "필드 삭제"는 필드가 아예 없는 경우라 0이 됐다.
- Spring Framework의 `Jackson2ObjectMapperBuilder`는 `FAIL_ON_UNKNOWN_PROPERTIES`를 끈다(javadoc). 이 빌더는 Spring Framework 7.0에서 폐기 예정(deprecated for removal)으로 표시됐다. Spring을 쓰면 직접 `new ObjectMapper()`한 코드와 동작이 다를 수 있다.

### 4. 파괴적 변경이 필요할 때 — 버저닝

```text
  (a) 경로에 메이저 버전          (b) 날짜 버전 + 변환 체인 (Stripe)
  GET /v1/orders/1               GET /v1/charges/ch_1   Stripe-Version: 2017-05-24
  GET /v2/orders/1                     │
   └ 두 구현이 나란히 산다              ▼ 핸들러는 최신 모양으로 응답을 만든다
                                 [최신 응답] ─ 변환(2020-08-27) ─ 변환(2019-02-19) ─▶ 요청 버전 모양
                                 계정은 첫 요청 때의 버전에 고정된다
```

- (a) 경로 버전 — Google AIP-185
  - 메이저 버전을 proto 패키지와 REST 경로에 넣는다(`v1`). 마이너·패치 번호는 노출하지 않는다.
  - 하위 호환 변경은 같은 메이저 버전 안에서 제자리 갱신한다. 사용자는 이전 없이 새 기능을 받는다.
  - 새 메이저 버전은 이전 메이저 버전에 의존하면 안 된다.
  - 베타 채널 기능은 폐기 뒤 제거까지 180일을 권한다.
- (b) 날짜 버전 — Stripe(2017 블로그, 현재 문서 "Upgrade your integration")
  - 계정은 첫 API 요청 때의 버전에 고정된다. 요청마다 `Stripe-Version` 헤더로 바꿀 수 있다.
  - 내부는 최신 모양 하나로 응답을 만든다. 날짜 순으로 쌓인 "version change module"을 거꾸로 적용해 옛 모양으로 바꾼다.
  - 현재 문서는 Java·Go·.NET처럼 타입이 강한 SDK는 SDK 출시 시점의 API 버전에 고정된다고 적는다.
- 어느 쪽이든 버전을 올리는 것은 **마지막 수단**이다. 버전 하나가 늘 때마다 유지·테스트할 조합이 는다.

### 5. 폐기 수명주기 — Deprecation → Sunset → 제거

```text
  시간 →
  ─────●───────────────────●───────────────────●──────────
    폐기 공지              Sunset 시각             제거
    응답에 Deprecation      이후 응답하지 않을 수 있음   410 Gone 또는 404
    + Link rel=deprecation  (RFC 8594)
    (RFC 9745)
    동작은 그대로!
    └──── 사용량 지표로 남은 호출자를 찾아 연락하는 기간 ────┘
```

- `Deprecation` 헤더 — RFC 9745(2025-03, 표준 트랙)
  - 값은 Structured Field의 Date: `Deprecation: @1688169599`(유닉스 초).
  - 이 헤더가 있다고 자원의 의미나 기능이 바뀌는 것은 아니다. 폐기된 자원도 똑같이 동작한다.
  - `Link: <...>; rel="deprecation"`로 이전 안내 문서를 가리킨다.
  - `Sunset` 시각은 `Deprecation` 시각보다 이르면 안 된다(MUST NOT).
- `Sunset` 헤더 — RFC 8594(2019-05, Informational)
  - 값은 HTTP-date: `Sunset: Sat, 31 Dec 2018 23:59:59 GMT`.
  - 뜻: 이 URI가 그 시각 이후 응답하지 않게 될 가능성이 높다.
  - 두 헤더의 날짜 형식이 다른 것은 역사적 이유다(RFC 9745 예시 설명).

### 실험: 폐기 예정 버전이 헤더를 붙이고, 클라이언트가 경고로 남긴다

```java
h.add("Deprecation", "@" + deprecatedAt.getEpochSecond());
h.add("Sunset", DateTimeFormatter.RFC_1123_DATE_TIME.format(sunsetAt.atZone(ZoneOffset.UTC)));
h.add("Link", "<https://api.example.com/docs/migrate-v2>; rel=\"deprecation\"; type=\"text/html\"");
// 클라이언트(JDK HttpClient): deprecation 헤더가 있으면 경고 로그
r.headers().firstValue("deprecation").ifPresent(d -> log.warn(...));
```

(실험, JDK 21.0.11 `com.sun.net.httpserver` + `java.net.http.HttpClient`, 2026-10-04)

```text
GET /v1/orders/1 -> 200 {"id":1,"amount":5000}
  WARN deprecated-api path=/v1/orders/1 deprecatedAt=2026-10-01T00:00:00Z sunset=Thu, 1 Apr 2027 00:00:00 GMT link=<https://api.example.com/docs/migrate-v2>; rel="deprecation"; type="text/html"
GET /v2/orders/1 -> 200 {"id":1,"amount":{"value":5000,"currency":"KRW"}}
```

- v1 응답은 그대로 200이다. 헤더는 신호일 뿐 동작을 바꾸지 않는다.
- 헤더를 **읽는 코드가 있어야** 의미가 있다. 그래서 클라이언트 SDK·게이트웨이 로그에서 이 헤더를 지표로 올리는 것이 실무 포인트다.
- 주의: 이 실험 코드의 `DateTimeFormatter.RFC_1123_DATE_TIME`은 날짜를 한 자리(`Thu, 1 Apr 2027`)로 냈다. RFC 9110 §5.6.7의 IMF-fixdate는 `day = 2DIGIT`이고, HTTP-date를 만드는 쪽은 IMF-fixdate로 내야 한다(MUST). 실제 서버는 `DateTimeFormatter.ofPattern("EEE, dd MMM yyyy HH:mm:ss 'GMT'", Locale.US)`처럼 두 자리로 낸다(`Thu, 01 Apr 2027 00:00:00 GMT`).

## 쓰이는 자료구조·알고리즘

- **필드 집합 비교** — 응답 스키마 변경이 하위 호환인지 = "옛 필드 집합 ⊆ 새 필드 집합, 그리고 공통 필드의 타입이 같다". OpenAPI diff 도구나 스키마 레지스트리의 호환성 검사가 이 비교를 자동화한다(data-engineering/09-data-contracts-and-schema-registry 미작성 — [data-engineering 영역](../../data-engineering/README.md)).
- **변환 체인(역순 적용)** — Stripe식 날짜 버전. 날짜순으로 정렬된 변환 목록에서 "요청 버전보다 새로운 것"만 골라 최신 → 옛 순서로 적용한다.

```java
// 날짜 오름차순으로 정렬된 변환 목록. 각 변환은 "이 날짜 이전 모양으로 되돌리는 법"을 안다.
record VersionChange(LocalDate date, UnaryOperator<Map<String, Object>> downgrade) {}

static Map<String, Object> render(Map<String, Object> latest, LocalDate requested, List<VersionChange> changes) {
    Map<String, Object> body = latest;
    for (int i = changes.size() - 1; i >= 0; i--) {               // 최신 변환부터
        if (changes.get(i).date().isAfter(requested)) body = changes.get(i).downgrade().apply(body);
        else break;                                               // 요청 버전 이전 변환은 적용하지 않는다
    }
    return body;
}
```

- **enum 폴백** — 모르는 값을 `UNKNOWN` 같은 센티널로 사상한다. 집합에 없는 키를 기본값으로 바꾸는 해시 조회와 같다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **계약을 글로 둔다** — OpenAPI·proto 파일. 무엇이 약속인지 적혀 있어야 변경을 분류할 수 있다([01-api-as-contract](../01-api-as-contract/2-summary.md) — 문서에 없는 동작도 누군가 의존한다는 Hyrum의 법칙).
2. **변경마다 분류표로 판정한다** — 응답인가 요청인가, 추가인가 변경·삭제인가.
3. **응답 enum은 처음부터 "늘어날 수 있다"고 문서에 쓴다** — AIP-180의 경고. 클라이언트 SDK는 `UNKNOWN` 폴백을 넣어 배포한다.
4. **이름·타입을 바꿔야 하면 expand → migrate → contract** 순서로 한다.
   - 새 필드를 추가한다(옛 필드와 함께 내보낸다) → 클라이언트가 옮겨 간다 → 옛 필드 사용량이 0이 되면 지운다.
   - DB 스키마의 expand/contract와 같은 생각이다([database/26-schema-migration](../../database/26-schema-migration/2-summary.md)).
5. **그래도 안 되면 메이저 버전** — 두 버전을 나란히 운영할 비용을 예산에 넣는다.
6. **폐기는 헤더 → 공지 → 사용량 0 확인 → Sunset → 제거** 순서로 한다.

### 2. 클라이언트를 관대하게 만든다 (Java, Jackson 2.x)

```java
ObjectMapper mapper = JsonMapper.builder()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)              // 새 필드 무시
    .enable(DeserializationFeature.READ_UNKNOWN_ENUM_VALUES_USING_DEFAULT_VALUE) // 새 enum → @JsonEnumDefaultValue
    .build();

public enum OrderStatus { PAID, SHIPPED, @JsonEnumDefaultValue UNKNOWN }
```

- 필드 삭제는 이 설정으로 못 잡는다(위 실험). 필수 필드는 `Long`·`Optional`로 받아 **null을 검사**하거나, 생성자 기반 역직렬화에서 `FAIL_ON_MISSING_CREATOR_PROPERTIES`를 켠다.
- `UNKNOWN`을 받았을 때 화면·로직이 무엇을 할지도 정해야 한다. 예외를 피했다고 끝이 아니다.

### 3. 서버 쪽 검증 — 계약 테스트와 diff

- 소비자 계약 테스트로 "어떤 소비자가 어떤 필드를 쓰는지"를 알면 삭제가 안전한지 판단할 수 있다([testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md)).
- PR마다 OpenAPI·proto의 이전 판과 새 판을 비교해 파괴적 변경을 막는다(Protobuf는 [08](../08-schema-and-serialization/2-summary.md)에서 다루는 `reserved`가 같은 역할).

### 4. 진단 — 폐기 버전을 누가 아직 부르나

```bash
# 응답 헤더 확인
curl -sS -i https://api.example.com/v1/orders/1 | grep -i -E '^(deprecation|sunset|link):'
# 게이트웨이·액세스 로그에서 버전별·클라이언트별 호출 수 (로그 필드 이름은 예시)
jq -r 'select(.path|startswith("/v1/")) | .api_key_id' access.log | sort | uniq -c | sort -rn | head
```

- 버전별 호출 수를 클라이언트 ID별로 쪼갠 지표가 없으면 Sunset 날짜를 정할 근거가 없다.

## 장애 시나리오와 대처

### 1. enum 값 추가 → 엄격 역직렬화 클라이언트 실패 (⚠ 커리큘럼)

- 현상: 서버가 `REFUNDED`를 추가한 직후 구 앱의 주문 목록이 열리지 않는다.
- 보이는 형태: 클라이언트 로그 `InvalidFormatException: ... not one of the values accepted for Enum class: [PAID]`. 서버 지표는 정상(200)이다.
- 원인: 클라이언트가 enum을 닫힌 집합으로 역직렬화한다. Jackson 2.19.2·3.0.0 모두 기본값에서 실패한다(실험).
- 대처: 즉시 — 새 값을 노출하지 않도록 서버 플래그를 끈다(또는 구 버전 클라이언트에는 옛 값으로 사상). 재발 방지 — SDK에 `UNKNOWN` 폴백, 문서에 "enum은 늘어난다" 명시, 새 enum 값은 클라이언트 배포가 퍼진 뒤 노출.

### 2. 필드 삭제·의미 변경 → 구 클라이언트가 조용히 틀린다 (⚠ 커리큘럼)

- 현상: 정산 화면에 금액 0원이 찍힌다. 예외는 없다.
- 보이는 형태: 에러 로그 없음. 고객 문의·데이터 대사에서 발견된다.
- 원인: 삭제된 필드는 역직렬화에서 기본값(0·null)이 된다(실험). 단위 변경(원 → 전)처럼 이름이 같고 의미만 바뀐 변경은 어떤 파서도 잡지 못한다.
- 대처: 삭제·의미 변경은 파괴적 변경으로 분류한다. 새 이름의 필드를 추가하고 옛 필드는 Sunset까지 유지한다. 클라이언트는 필수 필드의 null을 검사한다.

### 3. 라이브러리 메이저 업그레이드로 엄격성이 바뀐다

- 현상: Jackson 2 → 3으로 올린 뒤, "모르는 필드가 오면 실패해야 한다"는 테스트가 깨지거나, 반대로 오타 난 필드 이름이 조용히 무시된다.
- 원인: `FAIL_ON_UNKNOWN_PROPERTIES` 기본값이 2.19.2에서 true, 3.0.0에서 false였다(실험, jackson-databind 3.0.0 `DeserializationFeature` 소스). Spring 빌더도 이 값을 바꾼다.
- 대처: 기본값에 기대지 말고 `ObjectMapper` 설정을 코드에 명시한다. 요청 본문 검증(서버)은 엄격하게, 응답 읽기(클라이언트)는 관대하게 따로 설정할 수 있다.

### 4. Sunset 날짜에 내렸는데 아직 호출자가 있었다

- 현상: v1 제거 직후 특정 파트너의 배치가 404·410으로 실패한다.
- 보이는 형태: 게이트웨이의 v1 경로 4xx 급증, 한 API 키에 집중.
- 원인: 공지·헤더만 보내고 실제 호출자를 확인하지 않았다. 헤더를 읽는 클라이언트 코드가 없었다.
- 대처: 버전별·키별 호출 지표로 남은 호출자를 찾아 직접 연락한다. 제거 전에 일정 시간 일부러 실패시키는 "brownout"을 쓰는 회사도 있다 — 효과·기간은 회사 관례라 여기서 수치는 정하지 않는다 `[?]`.

### 5. 버전이 쌓여 유지비가 폭증한다

- 현상: `/v1`~`/v4`가 각자 다른 코드 경로·버그를 가진다. 수정 하나를 네 번 한다.
- 원인: 파괴적 변경마다 메이저 버전을 올리고, 구현을 통째로 복사했다.
- 대처: 하위 호환 변경으로 최대한 흡수한다(AIP-185는 마이너 변경을 같은 메이저 버전 안에서 제자리 갱신). 버전을 나눠야 하면 핵심 로직은 하나로 두고 경계에서 모양만 바꾼다(Stripe식 변환 체인).

## 핵심 문장

- 호환은 양쪽의 일이다. 서버의 "필드 추가는 안전하다"는 클라이언트가 모르는 것을 무시한다는 가정 위에서만 참이다.
- 응답 enum에 값을 더하는 것은 엄격한 클라이언트에게 파괴적 변경이다. Jackson 2.19.2와 3.0.0 기본값 모두 실패했다.
- 필드 삭제와 의미 변경은 예외 없이 틀린 값을 만든다. 가장 위험한 깨짐은 조용한 깨짐이다.
- 이름·타입 변경은 expand → migrate → contract로 쪼개고, 메이저 버전은 마지막 수단이다.
- `Deprecation`(RFC 9745)은 동작을 바꾸지 않는 신호이고, `Sunset`(RFC 8594)은 응답하지 않게 될 시각이다. 제거 판단은 헤더가 아니라 사용량 지표로 한다.

## 관련 주제·근거

- 선행: [01-api-as-contract](../01-api-as-contract/2-summary.md), [software-design/23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md)
- 후속·연결: [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md)(Protobuf·Avro의 진화 규칙), [testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md), [database/26-schema-migration](../../database/26-schema-migration/2-summary.md)(expand/contract), [21-api-documentation-openapi](../21-api-documentation-openapi/2-summary.md), 사례 [26-case-delivery-webhook](../26-case-delivery-webhook/)
- 근거
  - Google AIP-180 Backwards compatibility — https://google.aip.dev/180
  - Google AIP-185 API Versioning — https://google.aip.dev/185
  - RFC 9745 The Deprecation HTTP Response Header Field (2025-03) — https://www.rfc-editor.org/rfc/rfc9745
  - RFC 8594 The Sunset HTTP Header Field (2019-05) — https://www.rfc-editor.org/rfc/rfc8594
  - Stripe 블로그 "APIs as infrastructure: future-proofing Stripe with versioning"(2017-08-05) — https://stripe.com/blog/api-versioning
  - Stripe 문서 "Upgrade your integration" — https://docs.stripe.com/upgrades
  - Fowler "TolerantReader"(2011-05-09) — https://martinfowler.com/bliki/TolerantReader.html
  - Kleppmann, DDIA 1판 4장 "Encoding and Evolution"(backward·forward 호환 정의 — 책 본문 대신 인용 요약으로 확인)
  - jackson-databind 3.0.0 `DeserializationFeature` 소스 — https://github.com/FasterXML/jackson-databind/blob/jackson-databind-3.0.0/src/main/java/tools/jackson/databind/DeserializationFeature.java (`FAIL_ON_UNKNOWN_PROPERTIES(false)`, `FAIL_ON_NULL_FOR_PRIMITIVES(true)`), Jackson 3.0 릴리스 노트 — https://github.com/FasterXML/jackson/wiki/Jackson-Release-3.0 (#493)
  - RFC 9110 §5.6.7 Date/Time Formats(IMF-fixdate `day = 2DIGIT`) — https://www.rfc-editor.org/rfc/rfc9110
  - Spring Framework `Jackson2ObjectMapperBuilder` javadoc — https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/converter/json/Jackson2ObjectMapperBuilder.html
  - Hyrum's Law — https://www.hyrumslaw.com/
- 실험 목록
  - Jackson 2.19.2 vs 3.0.0, 필드 추가·enum 값 추가·필드 삭제 역직렬화 — maven:3.9-eclipse-temurin-21(JDK 21.0.11), `--network none`
  - Deprecation·Sunset·Link 헤더 발신과 클라이언트 경고 — JDK 21.0.11 `com.sun.net.httpserver`·`HttpClient`
