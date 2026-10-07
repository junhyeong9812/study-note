# data-engineering/06-event-data-modeling — 정답

## 정답

### 1. 세 시각

| 시각 | 찍는 쪽 | 쓰임 |
|---|---|---|
| 이벤트 시각 | 생산자(기기·서비스). CloudEvents `time` | 업무 지표의 날짜·윈도 |
| 수집 시각 | 수집기·브로커(우리 서버). Kafka `LogAppendTime`도 이것 | "언제 알았나", 지연 측정, 늦게 온 데이터의 재계산 범위, 미래 이벤트 검사 |
| 처리 시각 | 집계 잡이 돈 시각 | 파이프라인 지연·운영 관측. 재처리하면 바뀌므로 업무 지표 기준으로는 맞지 않는다 |

- "10월 1일 매출"은 보통 이벤트 시각을 업무 시간대(예: Asia/Seoul)로 잘라 만든다.

### 2. 기준별 날짜별 건수 (실험 1)

- (a) 처리 시각 KST: 10-01 998, 10-02 1000, 10-03 2.
  - 10-01 23시대에 일어나 90분 늦게 처리된 2건이 10-02로 넘어갔다.
  - 10-02는 2건을 받고 2건을 10-03으로 보내 1000이 됐다. 합계는 같지만 날짜별 내용이 다르다.
- (b) 이벤트 시각 UTC: 09-30 375, 10-01 1000, 10-02 625.
  - KST 00:00~09:00(하루의 9/24 = 375건)이 UTC로는 전날이다.
- 진실(이벤트 시각 KST): 10-01 1000, 10-02 1000.

### 3. CloudEvents 1.0.2 속성

- 필수: `id`, `source`, `specversion`, `type`.
- 선택: `datacontenttype`, `dataschema`, `subject`, `time`.
- 본문 스키마 버전: 명세는 `type`에 버전을 담는 예(`com.example.object.deleted.v2`)를 들고, 호환되지 않는 스키마 변경은 다른 `dataschema` URI로 나타내라고 한다(SHOULD).
- `specversion`은 CloudEvents 명세 자체의 버전이다. 1.0.2 명세에서 값은 `1.0`이다. 본문 스키마 버전이 아니다.

### 4. 재전송 중복 (실험 2)

- ID 없음: 2,040행·204,000. 재전송 40건이 2% 부풀렸다.
- `(source, id)` 기본 키 + `ON CONFLICT DO NOTHING`: 2,000행·200,000.
- 내용 기반 추정: 같은 초·같은 금액의 서로 다른 주문 2건을 더 넣자 실제 2,002건이 추정 2,000건이 됐다. 진짜 다른 사건까지 지운다.
- 근거: CloudEvents는 `source` + `id`가 사건마다 유일하도록 생산자에게 요구하고(MUST), 같은 `source`·`id`를 소비자가 중복으로 볼 수 있다고 한다(MAY).

### 5. 미래 이벤트

- 원인: 이벤트 시각은 기기 시계로 찍는다. 사용자가 시계를 바꿨거나 NTP 동기화가 안 된 기기다([distributed/04](../../distributed/04-physical-clocks-and-ntp/2-summary.md)).
- 확인

```sql
SELECT count(*), max(event_time - received_at)
FROM order_event WHERE event_time > received_at + interval '5 minutes';
```

- 실험 3: 5건, 최대 02:59:58 앞섬.
- 정책 후보: 원래 값은 남기고 플래그를 단다. 집계 시각을 수집 시각으로 대체하거나 격리 테이블로 보낸다. 허용 오차(예시 5분)는 데이터에서 정한다.
- Kafka 4.1: `message.timestamp.type=CreateTime`이면 레코드 타임스탬프가 브로커 시각보다 `message.timestamp.after.max.ms`(기본 1시간)를 넘게 미래인 레코드를 브로커가 거부한다. 검사 대상은 본문의 `event_time`이 아니라 레코드 타임스탬프다. 기기 시각을 레코드 타임스탬프로 넣었거나 Kafka 생산자 자신의 시계가 1시간 넘게 빠르면 쓰기 실패가 난다. 생산자 오류 로그도 확인한다.

### 6. 상태 스냅샷의 한계

- 잃는 것
  - 스냅샷 사이의 중간 변경: 하루 안에 basic → gold → basic이면 "변화 없음"으로 보인다(예시 4의 user_007).
  - 변경 이유: "프로모션", "환불로 강등" 같은 원인은 스냅샷에 없다.
- 변경 이벤트로 바꾸면 소비자가 키별로 이벤트를 순서대로 적용(fold)해 현재 상태를 만든다. 순서·중복·누락 처리도 소비자 몫이 된다. 그래서 상태 토픽을 따로 두거나 이벤트에 바뀐 뒤 상태를 함께 싣기도 한다.

### 7. 블룸 필터 중복 제거의 위험

- 블룸 필터는 "없음"은 확실하지만 "있음"은 거짓 양성일 수 있다([data-structure/11](../../data-structure/11-bloom-filter/2-summary.md)).
- 중복 제거에 쓰면 처음 보는 진짜 이벤트를 "이미 봤다"로 판정해 **버릴 수 있다**. 에러 없이 데이터가 빠진다.
- 매출·결제처럼 빠지면 안 되는 이벤트에는 맞지 않는다. 클릭 수처럼 근사가 허용되는 지표라면 검토할 수 있다. 정확해야 하면 유일 인덱스나 해시 집합(보관 기간 한정)을 쓴다.

### 8. 날짜별로만 다른 매출

- 원인 후보
  - 처리 시각(또는 적재 시각)으로 하루를 잘랐다: 자정 근처 늦은 이벤트가 옆 날짜로 옮겨 간다.
  - 시간대가 다르다: 한쪽은 UTC 자정, 다른 쪽은 KST 자정으로 잘랐다.
- 가르는 쿼리

```sql
-- 적재(수집) 시각 가설: 두 날짜가 다른 이벤트 수가 차이와 비슷한가
-- (처리 시각 가설이면 received_at 대신 집계 잡의 processed_at으로 같은 비교를 한다)
SELECT (event_time AT TIME ZONE 'Asia/Seoul')::date AS ev_day,
       (received_at AT TIME ZONE 'Asia/Seoul')::date AS rcv_day, count(*)
FROM order_event
WHERE (event_time AT TIME ZONE 'Asia/Seoul')::date <> (received_at AT TIME ZONE 'Asia/Seoul')::date
GROUP BY 1, 2;
-- 시간대 가설: UTC 날짜와 KST 날짜로 각각 자른 값이 두 숫자와 맞는가
SELECT (event_time AT TIME ZONE 'UTC')::date, count(*) FROM order_event GROUP BY 1;
```

- 읽는 법: 각 가설대로 일별 값을 실제로 다시 계산해 대시보드 숫자와 맞는 쪽을 찾는다. 차이의 크기만으로는 가를 수 없다. 실험 1에서 UTC 기준은 375건을 전날로 옮겼지만, 하루 건수가 고르니 10-01은 나가는 375건과 들어오는 375건이 상쇄돼 KST·UTC 모두 1,000건(차이 0)이었다(해석).
