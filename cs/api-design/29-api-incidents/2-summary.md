# api-design/29-api-incidents — 실사건: Twitter 64비트 ID와 JS 정밀도 → `id_str`(2010) · Optus 인가 없는 API로 고객 정보 대량 조회(2022) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 API 계약의 빈틈을 **하나씩** 다룬다.\
ID를 JSON 숫자로 내면 JS에서 끝자리가 바뀐다는 것은 08번, 하위 호환을 지키며 필드를 바꾸는 법은 07번, 존재 여부가 새는 403/404는 03번, 순번 작업 ID로 남의 결과가 보이는 것은 13번이다.\
실제 사건에서는 이 빈틈이 **규모**와 **시간**을 만나 드러난다.

```text
  leaf 노트:   [숫자 타입 불일치 08-1]  [필드 추가로 호환 유지 07]  [순번 ID + 인가 누락 13-6]  [존재 노출 03-4]
  실사건:
    Twitter 2010   ID 생성 방식 변경(Snowflake) -> ID가 곧 2^53을 넘음 -> JS 클라이언트가 끝자리를 바꿔 읽음
                   -> 출시를 미루고 문자열 필드 id_str를 "추가"해 날짜를 공지
    Optus 2022     접근 제어 코드 오류(2018) -> 쓰지 않는 API가 인터넷에 노출(2020) -> 주 도메인만 수정(2021)
                   -> 요청을 반복해 고객 정보를 대량 조회(2022-09-17~20) -> 약 950만 명
```

쉬운 예: 아파트 우편함이다.\
Twitter 사건은 우편함 번호가 네 자리에서 다섯 자리로 바뀌는데, 일부 집배원 수첩에 네 칸밖에 없는 것과 같다. 관리사무소는 공사를 미루고 "번호를 글자로도 함께 적어 드립니다"라고 미리 알렸다.\
Optus 사건은 우편함이 잠기지 않은 채, 번호 순서대로 늘어서 있던 것과 같다. 한 칸만 열어 봐도 될 사람이 끝에서 끝까지 열어 볼 수 있었다.

이 노트는 공개 문서로 두 사건을 복원하고, **API 설계** 관점의 빈틈만 본다.
- **Twitter Snowflake·`id_str`(2010)**: 1차 출처 — Twitter 개발자 그룹 공지(2010-08-24, 2010-10-19, Matt Harris), Snowflake 저장소(README·`IdWorker.scala`, 태그 `snowflake-2010` — 2014-05-29에 만든 태그로 2010-05~2014-05 코드의 마지막 상태, `IdWorker.scala` 최종 변경 2012-03-01. `twepoch` 값은 커밋 이력으로 따로 확인), X 개발자 문서 "X IDs".
- **Optus 고객 정보 유출(2022-09)**: 1차 출처 — Optus 보도자료(2022-09-22), Optus 고객 서한(2022-10-25), OAIC 보도자료(2025-08-08). ACMA 소송 문서(2024)는 ACMA 사이트에 접속하지 못해(이 환경에서 응답 없음) 그 문서를 인용한 언론 보도(ABC·iTnews·CSO Online, 2024-06-20~21)로만 확인했다.

  - *사실과 해석*: 원문에 있는 사실은 출처와 함께 쓴다. 원문이 말하지 않는 추론은 "해석"이라고 표시한다.
  - *1차 출처*: 사건 당사자·규제기관이 직접 낸 문서다. 언론 보도는 2차 출처로 따로 표시한다.

## 동작·원리

### 사건 1 — Twitter Snowflake와 `id_str` (2010)

출처: Matt Harris, "Status IDs are changing on 21st September", twitter-development-talk, 2010-08-24 <https://groups.google.com/g/twitter-development-talk/c/eYLjsDfu75U> · Matt Harris, "Snowflake: An update and some very important information", 2010-10-19 <https://groups.google.com/g/twitter-development-talk/c/ahbvo3VTIYI> · Snowflake 저장소 `snowflake-2010` 태그의 `README.mkd`·`IdWorker.scala` <https://github.com/twitter-archive/snowflake/tree/snowflake-2010>(2021-09-18 보관 처리, 읽기 전용. 태그 메시지 "Snowflake first open source release. May 2010--May 2014") · `IdWorker.scala` 커밋 이력 `eacb6135ae`·`5d1ccf6437`·`1cd0af14db` <https://github.com/twitter-archive/snowflake/commit/1cd0af14db> · X 개발자 문서 "X IDs" <https://docs.x.com/fundamentals/x-ids>(2026-10-04 조회).

#### 사실 — 왜 ID 생성 방식을 바꿨나 (README 원문)

- 동기: "As we at Twitter move away from Mysql towards Cassandra, we've needed a new way to generate id numbers. There is no sequential id generation facility in Cassandra".
- 요구사항(발췌)
  - 조정 없음: "machines generating ids should not have to coordinate with each other."
  - 대략 시간순: "We have a number of API resources that assume an ordering (they let you look things up "since this id")." 그래서 ID가 "k-sorted"여야 한다("we're promising 1s, but shooting for 10's of ms").
  - 작게: "we need to keep our ids under 64bits."
- 구성: "time - 41 bits (millisecond precision w/ a custom epoch gives us 69 years)", "configured machine id - 10 bits", "sequence number - 12 bits - rolls over every 4096 per machine".
- 코드(`IdWorker.scala`): `twepoch = 1288834974657L`, `workerIdBits = 5L`, `datacenterIdBits = 5L`, `sequenceBits = 12L`. ID는 `((timestamp - twepoch) << timestampLeftShift) | (datacenterId << datacenterIdShift) | (workerId << workerIdShift) | sequence`. README의 "machine id 10 bits"는 코드에서 데이터센터 5비트 + 워커 5비트로 나뉜다.

```text
  비트 63      62 ............................ 22   21 ..... 17   16 ..... 12   11 .......... 0
  ┌───┬──────────────────────────────────────┬────────────┬────────────┬─────────────────┐
  │ 0 │  ms 단위 시각 - twepoch  (41비트)      │ 데이터센터 5 │  워커 5     │  순번 12         │
  └───┴──────────────────────────────────────┴────────────┴────────────┴─────────────────┘
  ID ≥ 2^53  ⇔  (시각 - twepoch) ≥ 2^31 ms  (= 약 24.86일)   ← 아래 비트와 무관
```

- 그림 해설: 41 + 5 + 5 + 12 = 63비트다. 맨 위 비트는 쓰지 않는다. 시각이 왼쪽으로 22비트 밀려 있으므로, 시각 필드가 2^31을 넘는 순간 ID 전체가 2^53을 넘는다.
  - *k-sorted*: 완전히 정렬되지는 않지만, 어떤 원소도 제자리에서 k칸(여기서는 시간 범위) 이상 벗어나지 않는 순서다.

#### 사실 — 공지와 날짜

| 날짜 | 사건 | 출처(원문 인용) |
|---|---|---|
| 2010-06-01 | Twitter 엔지니어링 블로그 "Announcing Snowflake" 게시 | 블로그 원문은 이 환경에서 403으로 열리지 않음. 날짜는 검색 결과·Wikipedia "Snowflake ID" 기준 `[?]`. 방증: GitHub API의 저장소 생성 시각 `2010-06-01T20:32:15Z`, 08-24 공지 "A while ago we let you know about ... Snowflake and published the source code" |
| 2010-08-24 | 9월 21일 전환 예고 | "at 10am PDT on Tuesday September 21st, 2010 Snowflake will be in use on our production systems and that status IDs will no longer be sequential." ID는 "a timestamp, a worker number and a sequence number"로 구성, "There will be a noticeable jump in the numerical value of status IDs" |
| (2010-10 둘째 주) | 전환 시도 보류 | 10-19 공지 첫 문장: "Last week you may remember Twitter planned to enable the new Status ID generator - 'Snowflake' but didn't." 9월 21일 계획에서 언제로 옮겼는지는 이 공지만으로 확인 못 함 `[?]` |
| 2010-10-19 | 보류 이유와 새 일정 공지 | "Before launch it came to our attention that some programming languages such as Javascript cannot support numbers with >53bits." |
| 2010-10-22 | 응답에 문자열 ID가 나타남(예고) | 10-19 공지의 일정표 |
| 2010-11-04 | Snowflake 가동(예고) | "Snowflake will be turned on but at ~41bit length". Matt Harris의 후속 Q&A(같은 스레드, 2010-10-20): "The factor influencing the length of the ID is the time", 53비트 초과는 "24 days after Snowflake starts counting" — 가동 직후 ID는 짧고 시각이 흐를수록 길어진다는 뜻으로 읽힌다(해석) |
| 2010-11-26 | Status ID가 53비트를 넘음(예고) | "Status IDs will break 53bits in length and cease being usable as Integers in Javascript based languages." |

- 범위(10-19 공지): "Status, User, Direct Message and Saved Search IDs in the Twitter API will now be returned as an integer and a string in JSON responses." 새 필드 이름: "a status object will now contain an id and an id_str".
- 범위 보충(10-20 후속 Q&A): "Only Tweet IDs (which includes mentions and retweets) will be moving to new Snowflake IDs." 다른 ID는 앞으로를 대비해 문자열을 함께 준다고 썼다. 같은 글에서 "Is it safe to parse and store IDs as signed 64bit Integers?"에 "Yes."라고 답했다.
- 영향(10-19 공지): "In affected JSON parsers the ID will not be converted successfully and will lose accuracy", "some parsers there may even be an exception".
- 개발자에게 요청한 일(10-19 공지): "If you develop in Javascript, know that you will have to update your code to read the string version instead of the integer version." 그리고 시험용 JSON `{"id": 10765432100123456789, "id_str": "10765432100123456789"}`를 자기 파서로 읽어 보라고 했다.
- 현재 문서(X IDs, 2026-10-04 조회): "In JavaScript, integers are limited to 53 bits." 예시로 `10765432100123456789`가 `"10765432100123458000"`로 찍힌다고 쓴다. "X API v2"는 ID를 기본으로 문자열로 주고, "X API v1.1"은 숫자와 문자열을 함께 준다고 쓴다.

#### 해석

- 해석: Twitter는 **숫자 필드를 문자열로 바꾸지 않고, 문자열 필드를 더했다.** 07번의 하위 호환 규칙(필드 추가는 호환, 타입 변경은 파괴적)과 같은 선택이다. 그 대신 숫자 `id`는 JS 클라이언트에게 "있지만 믿으면 안 되는 필드"로 남았다.
- 해석: 공지는 **실제로 깨지기 전에** 날짜를 박았다. 10월 22일(문자열 등장) → 11월 4일(가동) → 11월 26일(53비트 초과) 사이에 클라이언트가 옮길 시간이 있었다.
- 해석: 원인은 ID 생성 방식(저장소 이동에 따른 Snowflake)이었지 API 변경이 아니었다. 그런데 응답의 숫자 **값의 범위**가 바뀐 것만으로 API 계약이 깨질 뻔했다. 01번의 말로 하면, "ID는 2^53 아래"라는 문서에 없는 성질에 JS 클라이언트가 의존하고 있었다.

### 사건 2 — Optus 고객 정보 유출 (2022-09)

출처: Optus, "Optus notifies customers of cyberattack compromising customer information", 2022-09-22 <https://www.optus.com.au/about/media-centre/media-releases/2022/09/optus-notifies-customers-of-cyberattack> · Optus, "A letter to our customers", 2022-10-25 <https://www.optus.com.au/content/dam/optus/documents/for-you/support/cyberattack/cyber_incident_letter_251022.pdf>(PDF 작성일 메타데이터 2022-10-25) · OAIC, "Australian Information Commissioner takes civil penalty action against Optus", 2025-08-08 <https://www.oaic.gov.au/news/media-centre/australian-information-commissioner-takes-civil-penalty-action-against-optus> · (2차) ABC News 2022-09-23 "Optus rejects insider claims of 'human error'…", ABC News 2022-09-26 "Home Affairs Minister Clare O'Neil says Optus 'left the window open'…", ABC News 2024-06-20 "Optus cyber attack could have been prevented four years prior, ACMA says", iTnews 2024-06-20, CSO Online 2024-06-21 "Optus breach occurred due to a coding error, alleges ACMA".

#### 사실 — 날짜

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2018-09 | 접근 제어 하나에 코딩 오류가 들어감 | ACMA 소송 문서를 인용한 CSO Online(2024-06-21): "in September 2018 when a coding error was introduced to one of the access controls" (2차) |
| 2020-06 | 주 도메인과 대상 도메인이 코딩 오류를 가진 채 인터넷에 노출 | 같은 기사: "both domains became internet-facing with the coding error in June 2020" (2차) |
| 2021-08 | Optus가 주 도메인의 오류를 발견·수정, 대상 도메인은 그대로 | 같은 기사: "Optus detected the coding error that left the main domain vulnerable in August 2021 and fixed it but did not apply the same to the target domain." (2차) |
| 2022-09-17~20 | 공격 기간 | ACMA 소송(ABC·iTnews 2024 보도) · OAIC 2025는 위반 기간 끝을 2022-09-20으로 적음 |
| 2022-09-22 | Optus가 공개 발표 | Optus 보도자료(1차). OAIC 2025: "the data breach made public by Optus on 22 September 2022" |
| 2022-09-23 | Optus가 내부자의 "인적 오류" 주장(API가 인터넷에 닿는 시험망에 노출)을 부인 | ABC 2022-09-23 (2차, 양쪽 주장 모두 보도) |
| 2022-09-26 | 내무부 장관 Clare O'Neil이 "effectively left the window open"이라 하고, 정교한 공격이었냐는 질문에 "Well, it wasn't." | ABC 2022-09-26 (2차) |
| 2024-05~06 | ACMA가 연방법원에 제소(2024-05), 2024-06-19 연방법원 빅토리아 등록소에 주장 문서 제출 | CSO Online 2024-06-21: "ACMA filed a document with the allegations with the Victoria Registry of the Federal Court of Australia on June 19." · ABC 2024-05-23·2024-06-20 (2차) |
| 2025-08-08 | OAIC가 연방법원에 민사 제재금 소송 제기 | OAIC 보도자료(1차) |

#### 사실 — 무엇이 노출됐나, 몇 명인가

- Optus 2022-09-22(1차): "Information which may have been exposed includes customers' names, dates of birth, phone numbers, email addresses, and, for a subset of customers, addresses, ID document numbers such as driver's licence or passport numbers." "Payment detail and account passwords have not been compromised."
- Optus 2022-10-25 서한(1차): 노출된 데이터를 "raw log files"에서 재구성했다고 쓰고, "We are aware of 10,000 customer details being released on the web"이라고 쓴다.
- OAIC 2025-08-08(1차): "approximately 9.5 million Australians"(OAIC가 프라이버시 침해를 주장하는 인원). 배경 절은 "The personal information held by Optus included"로 시작해 여권·운전면허·Medicare 번호, 출생·혼인 증명 정보 등 "government related identifiers"를 나열한다 — **Optus가 보유한 정보의 목록**이지, 항목별 노출 건수가 아니다.
- ABC 2024-06-20(2차, ACMA 소송 보도): "Of the active subscribers of an Optus service, 3,154,171 customers had their physical address accessed and 2,470,036 had identity information accessed." — 활성 가입자 기준 수치다.
- 초기 보도의 "약 980만 명"·"신분증 번호 210만 명"은 언론 보도(예: BleepingComputer "Optus confirms 2.1 million ID numbers exposed in data breach" — Optus의 2022-10-03 발표로 보도)에서 확인했고, 그 수치를 담은 Optus 원문은 찾지 못했다 `[?]`. 이 노트는 규제기관 수치(약 950만)를 기준으로 쓴다.

#### 사실 — 어떻게 (규제기관 주장, 법원 판단 아님)

- ACMA 소송 문서를 인용한 보도(2차)
  - 대상: 주 도메인 `www.optus.com.au`와 별도인 `api.www.optus.com.au`("the target domain")의 API. "The Target Domain was permitted to sit dormant and vulnerable to attack for two years and was not decommissioned despite the lack of any need for it."(CSO Online)
  - 방법: "the cyberattack was not highly sophisticated or one that required advanced skills or proprietary or internal knowledge of Optus' Processes or systems. It was carried out through a simple process of trial and error."
  - Optus 쪽 설명(iTnews 2024-06-20에 준 성명, 임시 CEO Michael Venter): 공격자가 "mimicking usual customer activity and rotating through tens of thousands of different IP addresses to evade detection". Optus는 "정교하지 않았다"는 ACMA 주장에 다투며 "The cyber-attacker commenced the cyberattack with a high degree of knowledge of Optus' systems"라고 연방법원 답변서(Statement of Defence)에서 주장했다(ChannelNews 2024-10-28 보도, 2차).
- OAIC 2025-08-08(1차): 위반 기간을 "from on or around 17 October 2019 to 20 September 2022"로 적는다. 소송 이유는 "failing to take reasonable steps to protect their personal information". 개인정보위원 Carly Kind: "the risks associated with external-facing websites and domains, particularly when these interact with internal databases holding personal information".
- OAIC가 다른 조직에 권한 것(1차, 발췌): "implement procedures that ensure clear ownership and responsibility over internet-facing domains", "ensure that requests for customers' personal information are authorised to access that information", "layer security controls to avoid a single point of failure".
- 순번 식별자(+1)를 차례로 조회했다는 설명은 보안 업체 글(예: UpGuard)에 예시(5567 → 5568)로 나온다. 이 노트가 읽은 규제기관 원문과 Optus 원문에는 그 문장이 없다 `[?]`. 커리큘럼의 "무인증 API 열거"는 이 2차 설명에 기댄 표현이다.

#### 사실 — 제재

- OAIC(1차): 2022-12 이전 위반에는 위반 1건당 최대 2.22백만 호주달러, 피해자 1명당 1건을 주장. 2022-12에 시행된 최대 5천만 호주달러 제재는 이 사건에 적용되지 않는다. "Whether a civil penalty order is made, and the amount, are matters before the court."
- ACMA 소송: Telecommunications (Interception and Access) Act 1979 위반 주장(ACMA 사이트 미접속 — 보도 기준, 2차).
- 2026-10-04 기준 두 소송의 판결·제재금 확정 여부는 확인하지 못했다 `[?]`.
- 혼동 주의: 2025-09-24 연방법원이 승인한 Optus 1억 호주달러 제재(ACCC)는 매장 판매의 비양심적 행위 사건이다. 이 유출 사건과 별개다.

#### 해석

- 해석: 규제기관 주장대로라면 실패는 **세 겹**이다. (1) 인가 검사 코드의 결함, (2) 쓰지 않는 API를 인터넷에 둔 채 아무도 소유하지 않음, (3) 한 도메인에서 고친 결함을 같은 코드를 쓰는 다른 도메인에 퍼뜨리지 않음. API 설계 영역의 빈틈은 (1)이다 — 객체 단위 인가가 요청마다 강제되지 않았다(13-6, 03-4).
- 해석: "수만 개 IP를 돌렸다"는 Optus 설명은 IP 기준 속도 제한이 이 공격을 막기 어려웠다는 뜻으로 읽힌다(14-1의 반대 방향). 속도 제한은 **피해 규모를 줄이는 층**이지 인가를 대신하지 않는다.
- 해석: 순번 ID는 원인이 아니라 **증폭기**다. 인가가 맞으면 순번이어도 남의 것을 못 보고, 인가가 틀리면 무작위 ID도 어딘가에서 샌 ID로 열린다(실험 B).

### 두 사건을 나란히 (해석)

| | Twitter 2010 | Optus 2022 |
|---|---|---|
| 깨진 계약 | 숫자 ID의 **값 범위**(문서에 없는 "2^53 아래") | 자원 조회의 **인가**(요청한 사람이 그 고객인가) |
| 원인 계층 | ID 생성기(저장소 이동) | 접근 제어 코드 + 노출된 미사용 API |
| 보이는 계층 | JS 클라이언트(끝자리 변형) — 공지로 사전 차단 | 없음(조회는 정상 응답) — 유출 뒤 발견 |
| 대처 방식 | 문자열 필드 **추가** + 날짜 공지 | 소송 중(규제기관 권고: 인가 확인·도메인 소유권·다층 통제) |
| leaf | [08-1](../08-schema-and-serialization/2-summary.md) · [07](../07-versioning-and-compatibility/2-summary.md) · [01](../01-api-as-contract/2-summary.md) | [13-6](../13-long-running-operations/2-summary.md) · [03-4](../03-status-codes-for-apis/2-summary.md) · [14-1](../14-rate-limit-and-quota-contracts/2-summary.md) |

### 실험 A: 실제 크기의 Snowflake ID를 JS로 읽으면

(실험, `node:22-alpine` — Node v22.23.2, `--network none`, 일회용 컨테이너 `sn-ad-w28-node`, 2026-10-04)

`IdWorker.scala`의 공식으로 ID를 만들고 `JSON.parse`에 넣었다.

```javascript
const TWEPOCH = 1288834974657n;
const mk = (ms, dc, w, seq) => ((BigInt(ms) - TWEPOCH) << 22n) | (BigInt(dc) << 17n) | (BigInt(w) << 12n) | BigInt(seq);
const crossMs = TWEPOCH + (1n << 31n);                       // id >= 2^53 <=> (ts - twepoch) >= 2^31
const ms = Date.parse('2026-10-04T00:00:00Z');
const ids = []; for (let s = 0; s < 1000; s++) ids.push(mk(ms, 1, 3, s));   // 같은 밀리초, 연속 1000개
const parsed = JSON.parse('[' + ids.map(String).join(',') + ']');           // 숫자로 보냄
const strParsed = JSON.parse(JSON.stringify(ids.map(String)));              // 문자열로 보냄
```

```text
node v22.23.2 | MAX_SAFE_INTEGER = 9007199254740991
twepoch            = 2010-11-04T01:42:54.657Z
id가 2^53을 넘는 시각 = 2010-11-28T22:14:18.305Z (epoch + 2^31 ms)
공지 예시  id     -> 10765432100123458000 | id_str -> 10765432100123456789
2026-10-04 id 예   = 2106534764344389632 비트 길이 61
연속 1000개를 JSON 숫자로 parse → 서로 다른 값 5 개
원래 값과 다른 것 996 개 | 예: 2106534764344389633 -> 2106534764344389600
id_str(문자열)로 parse → 서로 다른 값 1000 개, BigInt 복원 일치 true
경계 9007199250550783 -> JSON.parse 9007199250550783 같음
경계 9007199254740993 -> JSON.parse 9007199254740992 다름
```

- 관찰
  - `twepoch`는 2010-11-04 01:42:54.657Z다. 공지의 가동일(11월 4일)과 같은 날인 것은 우연이 아니다. 커밋 이력(GitHub API로 확인)에서 이 값은 2010-11-04T01:44:21Z 커밋 "another twepoch"(`1cd0af14db`)가 정했다 — 커밋 약 1.5분 전 시각이다. 그 전 코드의 epoch는 `1142974214000L`(주석 "Tue, 21 Mar 2006 20:50:14.000 GMT")이었고, 11-03~11-04 사이에 세 번 바뀌었다(`eacb6135ae`·`5d1ccf6437`·`1cd0af14db`).
  - 계산: 2006 epoch였다면 가동 시점의 (ts - twepoch)가 2^31 ms의 약 68배라 ID가 처음부터 2^53을 넘었다(60비트). epoch를 가동 직전으로 옮겨 53비트 초과까지 약 24일을 벌었다는 것이 이 이력과 맞는 해석이다(해석).
  - 이 공식으로는 시각 필드가 2^31 ms를 넘는 **2010-11-28 22:14 UTC**부터 모든 ID가 2^53 이상이다. 10-20 후속 Q&A도 "31bits is only enough for 24 days", 53비트 초과는 "24 days after Snowflake starts counting"이라고 같은 계산을 적었다. 공지 일정표는 11월 26일을 예고했다. 공개 코드의 epoch가 가동 시각(11-04)에 맞춰졌다는 것은 커밋 이력으로 확인된다(위). 운영 배포에 같은 값이 쓰였는지, 이틀 차이가 공지가 여유를 두고 앞당긴 날짜인지는 원문으로 확인하지 못했다 `[?]`.
  - 공지의 시험 값은 Node에서 `10765432100123458000`이 됐다. X 문서의 예시와 같다.
  - 2026년 크기의 ID(61비트)는 인접한 표현 가능 값 사이가 2^(61-53) = 256이다. 같은 밀리초의 연속 ID 1000개가 **5개 값으로 뭉쳤다.** 끝자리만 틀리는 것이 아니라 **서로 다른 ID가 같은 값이 된다.**
  - 문자열로 보낸 1000개는 모두 서로 다르고 `BigInt`로 원래 값과 일치했다.
- 해석: "끝자리가 0으로 바뀐다"(08-1)는 증상의 뒤에는 "여러 ID가 하나로 합쳐진다"가 있다. 클라이언트에서 ID를 키로 쓰는 맵·중복 제거가 조용히 항목을 잃는다.
- 덧붙임(계산): 공지 시험 값 `10765432100123456789`는 2^63(9223372036854775808)보다 크다. Snowflake 구성(63비트)의 ID는 Java `long`의 양수 범위에 들어가지만, 이 시험 값은 Java `long`에도 들어가지 않는다. 공지는 "unsigned" 64비트라 썼지만, 같은 스레드 10-20 Q&A 11번에서 Matt Harris가 "Strictly speaking the Snowflake is a signed 64bit long under the hood. That being said, we will never use the negative bit"라고 답했다. 실제 ID는 부호 비트를 쓰지 않는 63비트 범위다. 이 시험 값은 실제 ID 범위보다 넓은 "정밀도 손실 확인용" 값으로 읽힌다(해석).

### 실험 B: 순번 ID vs 무작위 ID vs 인가 검사 — 인증 없는 공격자

(실험, `node:22-alpine` — Node v22.23.2 `node:http`, `--network none`, 일회용 컨테이너 `sn-ad-w28-node`, 2026-10-04 — 같은 결과로 3회 실행, 시간만 다르다)

고객 1000명을 담은 작은 서버를 세 가지로 띄우고, 같은 공격자(인증 없음, 요청 5000건)를 붙였다. 공격자는 자기 계정의 ID 하나만 안다.

```javascript
const id = mode === 'random' ? randomUUID() : String(5000 + i);      // 순번은 5000부터
// 서버: GET /contacts/:id
if (mode === 'authz') {                                               // 순번 ID + 소유자 검사
  if (!c || req.headers['x-session-user'] !== c.owner) { res.writeHead(404); return res.end(); }
} else if (!c) { res.writeHead(404); return res.end(); }
// 공격자: 순번이면 +1씩, 무작위면 UUID를 새로 만들어 추측
const guess = mode === 'random' ? (k) => randomUUID() : (k) => String(Number(known) + 1 + k);
```

```text
sequential 요청 5000 → 200  999건, 404 4001건, 고객 1000명 중 노출 999명 (13493ms)
random     요청 5000 → 200    0건, 404 5000건, 고객 1000명 중 노출 0명 (11549ms)
random     샌 ID 50개로 조회 → 200 50건
authz      요청 5000 → 200    0건, 404 5000건, 고객 1000명 중 노출 0명 (10251ms)
authz      본인(user-0)이 자기 ID 조회 → 200
authz      샌 ID 50개로 조회 → 200 0건
```

- 관찰
  - 순번 ID + 인가 없음: 요청 5000건으로 자기를 뺀 999명 전부가 나왔다.
  - 무작위 ID + 인가 없음: 추측으로는 0명. 그러나 다른 경로(로그·Referer·공유 링크)로 **샌 ID 50개는 50개 모두 열렸다.**
  - 순번 ID + 소유자 검사: 추측 0명, 샌 ID 0명. 본인 조회는 200.
  - 시간은 실행마다 다르다(세 번 실행해 순번 약 13.2~13.5초). 1 CPU 제한 컨테이너의 루프백 값이다.
- 해석: 무작위 ID는 **열거 비용**을 올리고, 인가 검사는 **조회 자체**를 막는다. 막는 층은 인가다. 무작위 ID·속도 제한은 그 층이 틀렸을 때 피해를 줄이는 층이다.
- 이 실험은 Optus의 실제 API 구조를 재현한 것이 아니다. "인가 없는 조회 API + 추측 가능한 식별자"라는 모양만 본다.

## 쓰이는 자료구조·알고리즘

- **비트 필드 압축(Snowflake)**: 시각·위치·순번을 시프트와 OR로 정수 하나에 담는다. 시각이 상위 비트라 정수 비교 = 대략 시간 비교가 된다. 그래서 `since_id` 같은 "이 ID 이후" 조회가 가능하다(README).
- **binary64**: 가수 52비트 + 숨은 비트 1개. 2^53 이상의 정수는 2^(비트길이-53) 간격으로만 표현된다. 61비트 ID면 간격 256 → [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md).
- **열거 공간 크기**: 순번 ID의 추측 성공률은 (존재하는 ID 수 / 추측 범위) ≈ 1에 가깝다. UUIDv4는 무작위 비트 122개라 추측 성공률이 사실상 0이다. 단 샌 ID에는 아무 효과가 없다(실험 B).
- **객체 단위 인가**: 요청마다 (주체, 동작, 자원) 세 쌍을 정책에 묻는 검사 → [security/15-access-control-models](../../security/15-access-control-models/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 API 설계 관점으로 읽는 순서

1. **깨진 계약**을 한 줄로 쓴다. 값의 범위인가, 필드의 존재인가, 인가인가, 순서인가.
2. **원인 계층과 보이는 계층**을 나눈다(28의 0절). 둘이 다르면 왜 늦게 보였는지가 핵심이다.
3. 날짜표를 원문에서 만든다. 1차·2차 출처를 칸으로 구분한다.
4. 원문이 말하지 않는 것은 "해석"으로 표시한다. 특히 소송 중인 사건은 "규제기관 주장"과 "법원 판단"을 섞지 않는다.
5. 내 시스템에서 같은 계약이 어디에 있는지 찾는다(아래 점검 목록).

### 2. 내 API로 옮길 점검 목록

| 점검 | 방법 | 관련 |
|---|---|---|
| 응답의 64비트 정수가 2^53-1을 넘을 수 있나 | ID 생성기 공식으로 1년 뒤 값을 계산. 넘으면 문자열 필드를 지금 추가 | [08-1](../08-schema-and-serialization/2-summary.md) · 실험 A |
| 숫자 → 문자열 전환을 **교체**로 하고 있지 않나 | 숫자 필드 유지 + 문자열 필드 추가 + Deprecation·Sunset 날짜 | [07](../07-versioning-and-compatibility/2-summary.md) |
| 모든 자원 조회가 "요청자가 이 자원에 접근할 수 있나"를 검사하나 | 다른 계정의 ID로 조회하는 음성 테스트를 엔드포인트마다 | [13-6](../13-long-running-operations/2-summary.md) · 실험 B |
| 쓰지 않는 API·도메인이 인터넷에 떠 있지 않나 | 게이트웨이 경로 목록 vs 호출 지표, 소유자 없는 경로 제거 | [19](../19-api-gateway-and-bff/2-summary.md) · [07-4](../07-versioning-and-compatibility/2-summary.md) |
| 한 곳에서 고친 결함이 같은 코드의 다른 배포처에 남지 않았나 | 같은 핸들러·라이브러리를 쓰는 도메인·버전 목록으로 수정 전파 확인 | — |
| 한 주체가 다른 자원을 연속으로 조회하는 패턴을 보나 | 주체(토큰·계정)별 서로 다른 자원 ID 수, 404 비율 | [03-4](../03-status-codes-for-apis/2-summary.md) · [14-1](../14-rate-limit-and-quota-contracts/2-summary.md) |

### 3. 음성 테스트 — 남의 ID로 조회하면 막히는가 (Java)

```java
// JDK 21 HttpClient. A로 로그인한 토큰으로 B의 자원을 조회하면 403 또는 404여야 한다.
@ParameterizedTest
@ValueSource(strings = {"/contacts/%s", "/orders/%s", "/operations/%s"})
void otherUsersResourceIsNotReadable(String pathTemplate) throws Exception {
    String bResourceId = fixtures.createResourceOwnedBy("user-b", pathTemplate);
    HttpResponse<String> r = http.send(
        HttpRequest.newBuilder(URI.create(base + pathTemplate.formatted(bResourceId)))
            .header("Authorization", "Bearer " + tokenOf("user-a")).build(),
        HttpResponse.BodyHandlers.ofString());
    assertThat(r.statusCode()).isIn(403, 404);          // 팀 규칙으로 하나를 고른다(03-4)
    assertThat(r.body()).doesNotContain(bResourceId);
}
```

- `fixtures`·`tokenOf`는 테스트 도우미다(예시). 핵심은 **엔드포인트마다** 다른 주체로 조회하는 음성 테스트가 있다는 것이다. 양성 테스트(본인 조회 200)만으로는 인가 누락이 보이지 않는다.

## 장애 시나리오와 대처

### 1. 값의 범위가 커지는 변경을 API 변경으로 보지 않음 — Twitter형

- **현상**: ID 생성기·시퀀스 시작값·샤딩 방식을 바꿨다. API 스키마는 그대로다. 몇 주 뒤 웹 클라이언트에서만 404·다른 주문이 뜬다.
- **보이는 형태**: 서버 404 로그의 ID가 실제 ID와 앞자리만 같다. 같은 밀리초의 여러 ID가 클라이언트에서 하나로 합쳐져 목록이 줄어든다(실험 A: 1000개 → 5개 값).
- **원인**: "ID < 2^53"이 문서에 없는 계약이었다. 응답 필드의 타입은 같지만 값의 범위가 바뀌었다.
- **대처**: 생성기 변경 전에 실험 A처럼 미래 값을 계산한다. 문자열 필드를 먼저 추가하고 날짜를 공지한다(Twitter 2010-10-19 공지의 순서). → [08-1](../08-schema-and-serialization/2-summary.md)

### 2. 숫자 필드를 문자열로 **교체** — 고치다가 깨뜨림

- **현상**: 끝자리 문제를 고치려고 `id`를 `"id": "123…"`로 바꿨다. Java·Kotlin·iOS 클라이언트가 일제히 역직렬화 오류를 낸다.
- **보이는 형태**: 숫자로 읽던 클라이언트의 `MismatchedInputException` 류 오류(라이브러리마다 다름 `[?]`), 배포 직후 급증.
- **원인**: 필드 타입 변경은 파괴적 변경이다. Twitter는 같은 문제를 필드 **추가**로 풀었다.
- **대처**: 문자열 필드 추가 → 클라이언트 이전 → 숫자 필드 폐기 절차. → [07](../07-versioning-and-compatibility/2-summary.md)

### 3. 조회 API에 인가가 없음 — Optus형(규제기관 주장 기준)

- **현상**: 한 주체가 짧은 기간에 많은 고객의 정보를 받아 갔다. 응답은 모두 정상 200이라 오류 지표에 안 잡혔다.
- **보이는 형태**: 주체(또는 토큰 없음)별로 서로 다른 자원 ID 수가 비정상적으로 많다. 404·200이 섞인 연속 ID 조회. IP가 수만 개로 흩어지면 IP별 지표로는 안 보인다.
- **원인**: 요청마다 "이 요청자가 이 자원에 접근할 수 있나"를 검사하지 않았다. 순번 ID가 열거를 쉽게 만들었다(실험 B: 5000건으로 999명).
- **대처**: 객체 단위 인가를 모든 조회 경로에 강제하고, 다른 주체로 조회하는 음성 테스트를 둔다(적용 3). 추측 불가능한 ID와 주체별 속도 제한은 피해를 줄이는 추가 층으로 둔다. → [13-6](../13-long-running-operations/2-summary.md) · [03-4](../03-status-codes-for-apis/2-summary.md)

### 4. 쓰지 않는 API가 아무의 것도 아님

- **현상**: 한 도메인에서 고친 결함이 다른 도메인의 같은 API에 몇 년 남아 있었다(ACMA 주장, 보도 기준).
- **보이는 형태**: 게이트웨이·DNS 목록에는 있는데 호출 지표가 거의 없는 경로. 담당 팀이 없는 경로.
- **원인**: 경로의 소유권과 폐기 절차가 없었다. 수정이 코드 단위가 아니라 배포처 단위로 이뤄졌다.
- **대처**: 인터넷에 노출된 경로마다 소유자를 둔다(OAIC 권고 "clear ownership and responsibility over internet-facing domains"). 호출이 없는 경로는 Sunset 절차로 내린다([07-4](../07-versioning-and-compatibility/2-summary.md)). 결함 수정 때 같은 코드를 쓰는 배포처 목록을 확인한다.

### 5. 무작위 ID를 인가로 착각

- **현상**: 순번 ID를 UUID로 바꾸고 "열거 문제 해결"로 닫았다. 나중에 로그·공유 링크로 샌 ID로 남의 자원이 열린다.
- **보이는 형태**: 조회 요청의 `Referer`가 외부 사이트, 또는 로그 수집 도구에서 ID가 노출된 기록.
- **원인**: 무작위 ID는 추측을 막을 뿐 소유 여부를 확인하지 않는다(실험 B: 샌 ID 50개 중 50개 열림).
- **대처**: 인가 검사를 먼저 고친다. 무작위 ID는 그 위의 층이다.

## 핵심 문장

- Twitter 2010: ID 생성기가 바뀌자 ID가 2^53을 넘게 됐고, JS 클라이언트는 그 값을 정확히 읽지 못한다. Twitter는 출시를 미루고 문자열 필드 `id_str`를 **추가**해 날짜와 함께 공지했다(2010-10-19).
- 61비트 크기의 ID를 JSON 숫자로 읽으면 인접 표현 값 간격이 256이라, 같은 밀리초의 연속 ID 1000개가 5개 값으로 합쳐졌다(실험 A).
- Optus 2022: 규제기관 주장에 따르면 2018년의 접근 제어 코딩 오류가 쓰지 않는 API 도메인에 남아 2022-09-17~20 공격에 쓰였고, 약 950만 명이 영향을 받았다. 두 소송의 결과는 2026-10-04 기준 확인하지 못했다.
- 순번 ID는 인가 누락의 증폭기다. 막는 층은 객체 단위 인가이고, 무작위 ID·속도 제한은 피해를 줄이는 층이다(실험 B).
- 사고 보고서는 깨진 계약 → 원인 계층·보이는 계층 → 1차/2차 출처 날짜표 → 사실과 해석 순서로 읽는다.

## 관련 주제·근거

- 선행: [28-api-symptom-index](../28-api-symptom-index/2-summary.md)(4절 ID 끝자리 변형, 10절 노출)
- leaf: [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md)(64비트 ID·JS 정밀도) · [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md)(필드 추가·폐기 절차) · [01-api-as-contract](../01-api-as-contract/2-summary.md)(문서에 없는 성질 의존) · [13-long-running-operations](../13-long-running-operations/2-summary.md)(13-6 순번 작업 ID) · [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md)(03-4 존재 노출) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md)(제한 키) · [19-api-gateway-and-bff](../19-api-gateway-and-bff/2-summary.md)(노출 경로 관리)
- 다른 영역: [security/15-access-control-models](../../security/15-access-control-models/2-summary.md)(IDOR/BOLA) · [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md) · 실사건 형식 참고 [testing/21-test-incidents](../../testing/21-test-incidents/2-summary.md) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md)
- 근거 문서
  - Matt Harris, "Status IDs are changing on 21st September", twitter-development-talk, 2010-08-24 <https://groups.google.com/g/twitter-development-talk/c/eYLjsDfu75U>
  - Matt Harris, "Snowflake: An update and some very important information", twitter-development-talk, 2010-10-19 <https://groups.google.com/g/twitter-development-talk/c/ahbvo3VTIYI>
    - 같은 스레드의 Matt Harris 후속 Q&A(2010-10-20 게시 — 영향 필드, 53비트로 줄이지 않은 이유, "24 days after Snowflake starts counting")
  - Twitter, Snowflake 저장소 `snowflake-2010` 태그(2014-05-29 생성) `README.mkd`·`src/main/scala/com/twitter/service/snowflake/IdWorker.scala` <https://github.com/twitter-archive/snowflake/tree/snowflake-2010>, `IdWorker.scala` 커밋 이력(GitHub API `commits?path=…&sha=snowflake-2010`, 커밋 `eacb6135ae`·`5d1ccf6437`·`1cd0af14db`의 diff)
  - X, "X IDs" <https://docs.x.com/fundamentals/x-ids>(2026-10-04 조회). 옛 주소 developer.x.com/en/docs/twitter-ids는 이 환경에서 402로 열리지 않음
  - Ryan King, "Announcing Snowflake", Twitter Engineering Blog, 2010-06-01 `[?]`(원문 403 — 날짜는 검색 결과 기준)
  - Optus, "Optus notifies customers of cyberattack compromising customer information", 2022-09-22 · "A letter to our customers", 2022-10-25(PDF)
  - OAIC, "Australian Information Commissioner takes civil penalty action against Optus", 2025-08-08
  - (2차) ABC News 2022-09-23·2022-09-26·2024-06-20, iTnews 2024-06-20 "Optus breach allegedly enabled by access control coding error", CSO Online 2024-06-21 "Optus breach occurred due to a coding error, alleges ACMA"
  - (2차) ChannelNews 2024-10-28 "Optus Disputes Severity Of Cyberattack"(Optus 답변서 인용), BleepingComputer 2022-10 "Optus confirms 2.1 million ID numbers exposed in data breach"
  - (혼동 주의) ACCC, "Federal Court orders Optus to pay $100m penalty for unconscionable conduct" — 별개 사건
- 실험 목록
  - 실험 A — 주장: Snowflake 공식의 ID는 2010-11-28 22:14 UTC부터 2^53 이상이고, 61비트 ID를 JSON 숫자로 읽으면 연속 ID가 뭉친다. 코드 `scratchpad/ad/28/exp/snowflake.mjs`. 명령 `docker run --rm --name sn-ad-w28-node -u $(id -u):$(id -g) -e HOME=/tmp --network none --cpus=1 -v "$PWD":/w -w /w node:22-alpine node snowflake.mjs`. 환경 Node v22.23.2.
  - 실험 B — 주장: 인가 없는 순번 ID 조회는 요청 5000건으로 999명을 노출, 무작위 ID는 추측 0명이나 샌 ID 50/50, 소유자 검사는 0명. 코드 `scratchpad/ad/28/exp/enum.mjs`. 명령은 실험 A와 같고 파일만 `enum.mjs`. 3회 실행, 건수는 같고 시간만 다름.
