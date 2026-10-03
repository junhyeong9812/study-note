# api-design/29-api-incidents — 정답

## 정답

### 1. Snowflake의 동기·요구사항·구성

- 동기(README): "As we at Twitter move away from Mysql towards Cassandra, we've needed a new way to generate id numbers. There is no sequential id generation facility in Cassandra".
- 요구사항(README)
  - 조정 없음: "machines generating ids should not have to coordinate with each other."
  - 대략 시간순: "they let you look things up "since this id"" — API가 ID 순서에 기대므로 "k-sorted"("we're promising 1s, but shooting for 10's of ms").
  - 작게: "we need to keep our ids under 64bits."
- 구성: 시각 41비트(ms, 사용자 정의 epoch) + 기계 ID 10비트 + 순번 12비트. `IdWorker.scala`에서는 기계 ID가 `datacenterIdBits = 5L`, `workerIdBits = 5L`로 나뉜다. `sequenceBits = 12L`, `twepoch = 1288834974657L`. 합계 63비트.

### 2. 2010-10-19 공지

- 보류 이유: "Before launch it came to our attention that some programming languages such as Javascript cannot support numbers with >53bits."
- 날짜(예고)
  - 10-22: 응답에 문자열 ID가 나타남.
  - 11-04: Snowflake 가동("at ~41bit length"). 10-20 후속 Q&A는 ID 길이를 정하는 것이 시각이라고 했다("The factor influencing the length of the ID is the time") — 가동 직후엔 짧고 시간이 흐를수록 길어진다는 뜻으로 읽힌다(해석).
  - 11-26: "Status IDs will break 53bits in length and cease being usable as Integers in Javascript based languages."
- 범위: "Status, User, Direct Message and Saved Search IDs in the Twitter API will now be returned as an integer and a string in JSON responses."
- 요청: "If you develop in Javascript, know that you will have to update your code to read the string version instead of the integer version." 시험용 JSON `{"id": 10765432100123456789, "id_str": "10765432100123456789"}`를 자기 파서로 읽어 보라고 했다.

### 3. 2^53을 넘는 시각

- ID = (ts - twepoch) × 2^22 + (하위 22비트). 하위 22비트는 2^22 미만이므로 ID ≥ 2^53 ⇔ (ts - twepoch) ≥ 2^31 ms(약 24.86일).
- 실험 A(Node v22.23.2): `twepoch = 2010-11-04T01:42:54.657Z`, `id가 2^53을 넘는 시각 = 2010-11-28T22:14:18.305Z`.
- 10-20 후속 Q&A도 53비트 초과를 "24 days after Snowflake starts counting"이라고 같은 계산으로 적었다. 공지 일정표는 11월 26일을 예고했다. 계산값보다 이틀가량 이르다.
- 확인된 것: 공개 코드의 `twepoch`는 2010-11-04T01:44:21Z 커밋 "another twepoch"에서 가동 직전 시각으로 정해졌다(그 전엔 2006-03-21 epoch, GitHub 커밋 이력). 그래서 "가동일과 같은 날"은 우연이 아니다.
- 단정할 수 없는 것: 운영 배포에 이 값이 그대로 쓰였는지, 공지가 여유를 두고 날짜를 앞당겼는지. 원문으로 확인하지 못했다 `[?]`.

### 4. 연속 ID 1000개 → 5개 값

- 실험 A: `2026-10-04 id 예 = 2106534764344389632 비트 길이 61`, `연속 1000개를 JSON 숫자로 parse → 서로 다른 값 5 개`, `원래 값과 다른 것 996 개`.
- 이유: binary64는 53비트 정밀도다. 61비트 정수는 2^(61-53) = 256 간격으로만 표현된다. 순번만 다른 연속 ID 1000개(폭 약 1000)는 256 간격 칸 4~5개에 반올림되어 들어간다.
- 2차 피해: 끝자리 오류만이 아니라 **서로 다른 ID가 같은 값**이 된다. 클라이언트가 ID를 키로 쓰는 맵·중복 제거·선택 상태가 조용히 항목을 잃거나 엉뚱한 항목을 가리킨다. 그 값을 다시 서버로 보내면 404나 다른 자원이 나온다([08-1](../08-schema-and-serialization/2-summary.md)).
- 문자열로 보낸 경우: `id_str(문자열)로 parse → 서로 다른 값 1000 개, BigInt 복원 일치 true`.

### 5. 교체가 아니라 추가

- 07번 규칙: 응답에 필드를 **추가**하는 것은 (모르는 필드를 무시하는 클라이언트에게) 호환 변경이다. 필드의 **타입을 바꾸는 것**은 파괴적 변경이다.
- `id`를 문자열로 바꿨다면 숫자로 읽던 클라이언트 — Java·Objective-C처럼 64비트 정수를 정확히 다루던 클라이언트까지 — 가 역직렬화 단계에서 깨졌을 것이다(해석).
- 추가 방식의 대가: 숫자 `id`가 JS 클라이언트에게 "있지만 믿으면 안 되는 필드"로 남는다. 그래서 공지가 JS 개발자에게 문자열 쪽을 읽으라고 명시했다. 현재 X API v2는 ID를 기본으로 문자열로 준다(X IDs 문서).

### 6. Optus 날짜표

| 날짜 | 사건·주장 | 출처 구분 |
|---|---|---|
| 2018-09 | 접근 제어 하나에 코딩 오류가 들어감 | 2차(ACMA 소송 문서를 인용한 CSO Online 2024-06-21) |
| 2020-06 | 주 도메인과 대상 도메인(`api.www.optus.com.au`)이 오류를 가진 채 인터넷에 노출 | 2차(같은 기사) |
| 2021-08 | 주 도메인 오류만 발견·수정, 대상 도메인은 그대로 | 2차(같은 기사) |
| 2022-09-17~20 | 공격 기간. "simple process of trial and error"(ACMA 주장) | 2차(ABC·iTnews 2024) · OAIC 2025(1차)는 위반 기간 끝을 2022-09-20으로 적음 |
| 2022-09-22 | Optus가 공개 발표 — 이름·생년월일·전화·이메일, 일부는 주소·신분증 번호 노출 가능, 결제 정보·비밀번호는 아님 | 1차(Optus 보도자료) |
| 2025-08-08 | OAIC가 연방법원에 민사 제재금 소송. 2019-10-17경~2022-09-20, 약 950만 명, 위반 1건당 최대 2.22백만 호주달러 | 1차(OAIC 보도자료) |

### 7. 수치의 출처와 `[?]`

| 수치 | 출처 |
|---|---|
| 약 950만 명 | OAIC 2025-08-08(1차), ACMA 소송 보도(2차) |
| 약 980만 명 | 2022년 언론 보도. 이 수치를 담은 Optus 원문은 찾지 못함 `[?]` |
| 2,470,036명(신분 정보 접근, 활성 가입자 기준) | ABC 2024-06-20의 ACMA 소송 보도(2차) |

- "순번 식별자 +1 열거"는 보안 업체 글에 예시(5567 → 5568)로 나오지만, 이 노트가 읽은 규제기관(OAIC 보도자료)·Optus 원문과 ACMA 소송 보도에는 그 문장이 없다. ACMA 쪽 표현은 "trial and error"까지다. 그래서 단정하지 않고 `[?]`로 둔다.

### 8. 실험 B

| 서버 | 요청 5000건 노출 | 샌 ID 50개 |
|---|---|---|
| 순번 + 인가 없음 | 999명(자기 제외 전원) | — |
| 무작위(UUID) + 인가 없음 | 0명 | 50개 모두 200 |
| 순번 + 소유자 검사 | 0명 | 0개 |

- 막는 층: 객체 단위 인가(요청자가 그 자원의 소유자인가). 순번이어도, ID가 새도 막는다.
- 줄이는 층: 추측 불가능한 ID(열거 비용을 올림), 주체별 속도 제한(대량 조회 속도를 늦춤). 인가가 틀렸을 때 피해를 줄일 뿐 조회 자체를 막지 못한다.

### 9. IP 기준 제한이 약한 이유

- 수만 개 IP로 요청을 흩으면 IP 하나당 요청 수가 작아 IP별 한도에 걸리지 않는다. 14-1이 다룬 문제(NAT 뒤 정상 사용자가 함께 막힘)의 반대 방향이다.
- 더 잘 보는 지표: 주체(토큰·계정, 또는 "인증 없음") 단위의 **서로 다른 자원 ID 수**, 연속 ID 조회 패턴, 404·200 혼합 비율, 엔드포인트 전체의 고유 자원 조회 수 급증. 인가가 없는 API라면 주체 자체가 없으므로 엔드포인트 단위 지표가 마지막 그물이다(해석).

### 10. 비교와 구분

| | Twitter 2010 | Optus 2022 |
|---|---|---|
| 깨진 계약 | 숫자 ID의 값 범위(문서에 없는 "2^53 아래") | 자원 조회의 인가 |
| 원인 계층 | ID 생성기(저장소 이동) | 접근 제어 코드 + 노출된 미사용 API |
| 보이는 계층 | JS 클라이언트 — 공지로 사전 차단 | 정상 응답이라 보이지 않음 — 유출 뒤 발견 |

- 구분 이유: ACMA·OAIC의 문서는 소송의 **주장**이다. 2026-10-04 기준 판결·제재금 확정 여부를 확인하지 못했다. 주장을 법원이 인정한 사실처럼 쓰면 노트가 틀린 단정을 담게 된다.
- 2025-09-24 1억 호주달러 제재: ACCC가 제기한 **매장 판매의 비양심적 행위** 사건이다. 이 유출 사건과 별개다.
