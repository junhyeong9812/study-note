# api-design/07-versioning-and-compatibility — 정답

## 정답

### 1. 왜 모든 변경이 호환 질문이 되나

- 공개한 뒤에는 클라이언트의 업데이트 시점을 서버가 정하지 못한다. 구 앱·파트너 배치가 몇 년씩 남는다.
- 그래서 서버 변경은 "지금 살아 있는 구 클라이언트 전부와 맞나"를 따져야 한다.
- 서버가 새 응답을 내고 구 클라이언트가 읽는 것은 "옛 코드가 새 데이터를 읽는다" = **forward 호환**(DDIA 4장 정의)이다. 클라이언트가 모르는 추가분을 무시할 수 있어야 한다.
- 반대로 구 클라이언트의 요청을 새 서버가 읽는 것은 backward 호환이다.

### 2. 분류

| 변경 | 방향 | 판정 | 이유 |
|---|---|---|---|
| 필드 추가 | 응답 | 조건부 안전 | 클라이언트가 모르는 필드를 무시할 때만 |
| enum 값 추가 | 응답 | 조건부 | 엄격한 클라이언트는 실패. AIP-180도 "새 값을 우아하게 처리 못할 수 있다"고 경고 |
| 필드 삭제 | 응답 | 파괴 | 구 클라이언트는 기본값(0·null)을 받는다 |
| 필수 필드 추가 | 요청 | 파괴 | 구 클라이언트는 그 필드를 안 보낸다 |
| 최대 길이 축소 | 요청 | 파괴 | 전에 통과하던 요청이 거절된다(AIP-180: 길이 제한 변경 금지) |
| 단위 변경 | 응답 | 파괴(조용히) | 이름·타입이 같아 어떤 파서도 못 잡는다 — 의미 호환 위반 |

### 3. Jackson 예측 (실험 출력)

| 경우 | Jackson 2.19.2 기본 | Jackson 3.0.0 기본 |
|---|---|---|
| (a) `memo` 추가 | `UnrecognizedPropertyException` | 성공(`FAIL_ON_UNKNOWN_PROPERTIES=false`) |
| (b) `REFUNDED` | `InvalidFormatException` | `InvalidFormatException` |
| (c) `amount` 삭제 | 성공, `amount=0` | 성공, `amount=0` |

- 실험(JDK 21.0.11, 2026-10-04)에서 위와 같이 나왔다. `Long`으로 받으면 (c)는 `amount=null`이다.

### 4. 관대한 설정의 한계

- `FAIL_ON_UNKNOWN_PROPERTIES` 끄기 + `READ_UNKNOWN_ENUM_VALUES_USING_DEFAULT_VALUE` + `@JsonEnumDefaultValue UNKNOWN`으로 (a)·(b)는 해결된다(실험: `status=UNKNOWN`).
- (c) 삭제는 해결되지 않는다. 원래부터 예외가 아니라 **조용한 0**이었다.
- 막는 법
  - 서버: 삭제를 파괴적 변경으로 분류하고 하지 않는다(또는 Sunset 뒤에만).
  - 클라이언트: 필수 필드를 `Long`·`Optional`로 받아 null을 검사하거나, 생성자 기반 역직렬화에서 `FAIL_ON_MISSING_CREATOR_PROPERTIES`를 켠다.
- `UNKNOWN`을 받았을 때 화면·로직이 할 일도 정해야 한다.

### 5. 경로 버전 vs 날짜 버전

| | 경로 메이저 버전(AIP-185) | 날짜 버전(Stripe) |
|---|---|---|
| 버전 위치 | URL 경로·proto 패키지 `v1` | 계정에 고정된 날짜, 요청별 `Stripe-Version` 헤더 |
| 내부 구현 | 메이저 버전마다 따로. 마이너 변경은 같은 버전 안에서 제자리 갱신 | 최신 모양 하나 + 날짜순 변환을 거꾸로 적용 |
| 비용 | 메이저 버전 동시 운영(코드 경로·테스트 중복) | 변환 모듈을 계속 쌓고 유지 |

### 6. Deprecation·Sunset

- `Deprecation`: RFC 9745(2025-03). Structured Field Date — `Deprecation: @1688169599`.
- `Sunset`: RFC 8594(2019-05, Informational). HTTP-date — `Sunset: Sat, 31 Dec 2018 23:59:59 GMT`.
- `Deprecation`이 있어도 자원의 의미·기능은 바뀌지 않는다(RFC 9745). 실험에서도 v1은 그대로 200을 냈다.
- `Sunset` 시각은 `Deprecation` 시각보다 이르면 안 된다(RFC 9745, MUST NOT).
- 안내 문서는 `Link: <...>; rel="deprecation"`.

### 7. `amount`를 객체로 바꾸는 순서

1. **expand**: 새 필드 `amount_money: {value, currency}`를 추가하고 옛 `amount`도 계속 낸다.
2. 문서·SDK를 갱신하고, 옛 필드에 폐기 안내를 단다(엔드포인트 단위면 `Deprecation` 헤더).
3. **migrate**: 클라이언트가 새 필드로 옮긴다. 옛 필드 사용량을 클라이언트별로 측정한다.
4. **contract**: 사용량이 0이 되고 Sunset이 지나면 옛 필드를 지운다.
- 이름을 그대로 두고 타입만 바꾸는 것(`amount`를 숫자 → 객체)은 파괴적 변경이다. 그래야 한다면 메이저 버전.

### 8. Sunset 제거 사고

- 빠뜨린 것: 실제로 누가 아직 호출하는지 확인하지 않았다. 헤더·공지는 보냈지만 그 파트너의 클라이언트 코드는 헤더를 읽지 않았다.
- 보이는 형태: 게이트웨이의 v1 경로 4xx 급증, 특정 API 키에 집중.
- 다음에는: 버전별·클라이언트(API 키)별 호출 지표로 남은 호출자를 찾아 직접 연락하고, 사용량이 0이 된 것을 확인한 뒤 제거한다.

### 9. Jackson 3 업그레이드와 엄격성

- `FAIL_ON_UNKNOWN_PROPERTIES` 기본값이 2.19.2에서 true, 3.0.0에서 false였다(실험). Jackson 3.0의 의도된 기본값 변경이다(jackson-databind 3.0.0 `DeserializationFeature` 소스, 3.0 릴리스 노트 #493). 그래서 모르는 필드가 와도 예외가 나지 않아 400이 안 나간다.
- Spring의 `Jackson2ObjectMapperBuilder`도 이 값을 끈다(javadoc) — 프레임워크에 따라 원래부터 꺼져 있었을 수 있다.
- 대처: 기본값에 기대지 말고 설정을 코드에 명시한다.
  - 서버의 요청 본문 검증용 매퍼: 엄격(`FAIL_ON_UNKNOWN_PROPERTIES` 켬)으로 오타·잘못된 필드를 400으로 알린다.
  - 클라이언트의 응답 읽기용 매퍼: 관대(끔 + enum 폴백)로 서버의 추가에 견딘다.
- 요청 쪽을 엄격하게 하면, 나중에 클라이언트가 새 선택 필드를 보내기 시작할 때 구 서버가 400을 낸다. 서버를 먼저 배포하는 순서로 피한다.
