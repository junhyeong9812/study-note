# data-engineering/12-data-retention-and-erasure — 보존 기한, 삭제 전파, crypto-shredding — 정리 (힌트)

## 해결하는 문제

회원 `user_007`이 탈퇴하며 개인정보 삭제를 요청했다. 운영 DB에서 `DELETE`를 실행하고 "삭제했습니다"라고 답했다. 그런데 데이터는 이렇게 흩어져 있었다.

```text
  app.users ──DELETE──▶ 0행  ✅
     │
     ├─ CTAS ──▶ dw.dim_user, dw.fct_orders          남아 있음 (1행, 5행)
     ├─ 색인 ──▶ search.user_doc                      남아 있음
     ├─ 이벤트 ─▶ ops.event_log (jsonb, 추가만)         남아 있음
     └─ 백업 ──▶ ops.users_backup_20261001             남아 있음
```

- 원천을 지워도 파생 복제본(01번의 파생 데이터)은 따로 산다. 삭제는 "한 테이블의 DELETE"가 아니라 **복제된 곳마다 전파하는 작업**이다(아래 실험).
- 반대 방향의 실수도 있다. 보존 기한을 정하지 않은 로그·이벤트는 계속 쌓여 비용이 늘고, 필요 이상 오래 둔 개인정보는 규제 위반이 된다.
  - *보존 기한(retention period)*: 데이터 종류마다 "언제까지 두고 그 뒤 지운다"를 정한 기간.
  - *삭제권(right to erasure)*: 정보주체가 자기 개인정보의 삭제를 요구할 권리. GDPR 제17조.

쉬운 예: 학급 사진 앨범이다.
- 한 학생이 "내 사진을 빼 주세요"라고 했다. 원본 앨범에서는 뺐다.
- 그런데 졸업 문집, 복사해 나눠 준 사본, 교무실 백업 CD에 그 사진이 있다. 누가 어디로 복사했는지 기록(계보)이 없으면 다 찾지 못한다.
- 처음부터 사진마다 학생별 자물쇠를 채워 두었다면, 그 학생의 열쇠만 녹여 버리면 흩어진 사본이 한 번에 못 쓰는 상태가 된다(crypto-shredding).

똑같은 구조다.\
실무 예: 분석 DW·검색 인덱스·Kafka 토픽·이벤트 저장소·백업에 남은 개인정보 때문에 삭제 요청에 사실과 다른 답을 하게 된다. 불변 이벤트 로그에 평문 이메일을 넣어 두면 지울 방법 자체가 마땅치 않다.

## 동작·원리

### 1. 법의 틀 — 무엇이 의무이고 무엇이 예외인가 (GDPR 원문 기준)

```text
  수집 ──▶ 목적에 필요한 동안 보관 ──▶ 목적 끝 / 삭제 요청 ──▶ 지체 없이 삭제 ──▶ 받은 곳에 알림
           제5조 1항 (e) 보관 제한        제17조 1항 사유             제17조 1항          제19조
                                          제17조 3항 예외면 삭제 안 함(법적 의무·법적 청구 등)
```

- 제5조 1항 (e) "storage limitation": 개인정보는 처리 목적에 필요한 기간보다 오래 **식별 가능한 형태로** 보관하지 않는다. 공익 기록보존·연구·통계 목적은 제89조 1항의 보호조치 아래 더 오래 둘 수 있다.
- 제17조 1항: 사유(더 이상 필요 없음, 동의 철회, 반대권 행사, 불법 처리, 법적 의무, 아동 정보사회서비스) 중 하나면 정보주체는 "without undue delay" 삭제를 요구할 수 있고, 컨트롤러(controller — 처리 목적과 수단을 정하는 쪽)는 지울 의무가 있다.
- 제17조 3항: 표현·정보의 자유, **법적 의무 이행**·공익 업무, 공중보건, 공익 기록보존·연구·통계(제89조 1항), **법적 청구의 제기·행사·방어**에 필요한 범위에서는 1·2항이 적용되지 않는다.
  - 그래서 "삭제 요청 = 전부 삭제"가 아니다. 세법상 보존해야 하는 거래 기록은 남기고, 나머지 개인정보를 지운다. 한국 법의 분리 보관·기한은 [engineering-practice/17-legal-standards](../../engineering-practice/17-legal-standards/2-summary.md) §5에 정리돼 있다.
- 제19조: 삭제를 하면 그 개인정보를 **제공받은 각 수령자에게 알린다**. 불가능하거나 과도한 노력이 드는 경우는 예외다.
- 제12조 3항: 요청에 대한 조치 정보는 지체 없이, 늦어도 접수 후 **1개월** 안에 준다. 복잡성·요청 수를 고려해 2개월 더 연장할 수 있다.
- 법 해석은 이 노트의 범위가 아니다. 위는 원문 요약이고, 실제 판단은 법무 확인 대상이다(해석·법률 자문 아님).

### 2. 삭제 전파 — 복제본 지도

```text
                         ┌─ 동기 복제·읽기 복제본      원천 DELETE가 복제로 따라간다
                         ├─ 캐시                       TTL 또는 무효화
  원천(app.users) ──────┼─ 분석 DW (CTAS·ELT)          다음 적재가 덮어쓰지 않으면 남는다 → 명시 삭제
   DELETE                ├─ 검색 인덱스                 재색인 또는 문서 삭제 API
                         ├─ 이벤트 로그·Kafka           불변/추가만 → compaction tombstone·보존 만료·암호 삭제
                         ├─ 백업                       선택 삭제가 어렵다 → 보존 주기 만료·암호 삭제
                         └─ 외부 수령자(SaaS·파트너)     제19조 알림
```

- 어떤 사본이 있는지는 계보(11번)로 찾는다. `SELECT *` 내보내기처럼 계보가 "미상"인 경로는 보수적으로 대상에 넣는다.
- 경로마다 지우는 방법이 다르다. 그래서 "삭제 요청 처리"는 경로별 작업 목록과 완료 확인으로 설계한다.

### 실험: 원천만 지우면 어디에 남나 (PostgreSQL 17)

(실험, `postgres:17` — PostgreSQL 17.11, `--network none`. 합성 사용자 20명·주문 100건. 원천에서 CTAS 사본·검색용 테이블·jsonb 이벤트 로그·백업 테이블을 만든 뒤 원천에서만 삭제.)

```sql
DELETE FROM app.users WHERE user_id = 'user_007';     -- FK ON DELETE CASCADE로 app.orders도 삭제

-- 잔존 탐색: 모든 일반 테이블의 text·jsonb 컬럼에서 주체 식별자 검색 (\gexec로 쿼리 생성 후 실행)
SELECT format('INSERT INTO hits SELECT %L, %L, count(*) FROM %I.%I WHERE strpos(%I::text, %L) > 0',
              table_schema || '.' || table_name, column_name, table_schema, table_name, column_name, 'user_007')
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog','information_schema') AND data_type IN ('text','jsonb','character varying')
\gexec
```

```text
 users_left | orders_left
          0 |           0
            tbl            |   col   | n
 dw.dim_user               | contact | 1
 dw.dim_user               | user_id | 1
 dw.fct_orders             | contact | 5
 dw.fct_orders             | user_id | 5
 ops.event_log             | payload | 1
 ops.users_backup_20261001 | contact | 1
 ops.users_backup_20261001 | user_id | 1
 search.user_doc           | body    | 1
 search.user_doc           | doc_id  | 1
```

- 원천과 FK로 묶인 주문은 0행이 됐다. 다섯 개 파생 테이블에는 그대로 남았다. 에러도 경고도 없다.
- 이 전수 검색은 **식별자 문자열이 그대로 들어 있는 곳만** 찾는다. 해시·가명(`sha256(email)`), 다른 키로 바뀐 사본, DB 밖(검색 엔진·객체 저장소·Kafka)은 못 찾는다. 그래서 1차 수단은 계보이고, 이런 검색은 "빠뜨린 곳이 없나" 확인용이다.

### 3. 불변 로그와 삭제권의 충돌

```text
  추가만 하는 로그 (Kafka 토픽, 이벤트 저장소)
  offset 10  key=user_007  {email: "user_007@…", plan: "pro"}
  offset 11  key=user_007  {plan: "free"}
  offset 12  key=user_007  null                          ← tombstone (값이 null인 레코드)

  compaction 후 (언젠가)    offset 12 tombstone만 남음 → delete.retention.ms가 지난 뒤의 compaction에서 tombstone도 제거
```

- Kafka 4.1 설계 문서 "Log Compaction" 기준. 이 동작은 `cleanup.policy=compact`(또는 `delete,compact`) 토픽에서만이다. Kafka 4.1 토픽 기본값은 `delete`라, 기본 토픽에 null 값을 보내도 옛 레코드는 compaction으로 지워지지 않는다(`TopicConfig` `cleanup.policy` 설명).
  - compaction은 키마다 **적어도 마지막 값**을 남긴다. 값이 null인 레코드(tombstone)는 그 키의 이전 레코드를 지우게 한다.
  - tombstone 자체도 "일정 시간 뒤" 로그에서 정리된다. `delete.retention.ms`(기본 24시간)는 tombstone을 **적어도** 남겨 두는 시간이고, 실제 제거는 그 뒤 log cleaner가 compaction을 돌릴 때다(제거 시각 보장이 아니다). 이보다 오래 뒤처진 소비자는 삭제 표시를 못 볼 수 있다.
  - **지금 쓰고 있는 세그먼트(active segment)는 compaction 대상이 아니다.** 지저분한 비율이 `min.cleanable.dirty.ratio`를 넘지 않으면 compaction이 안 일어날 수 있다. `max.compaction.lag.ms`로 상한을 둘 수 있지만, 문서는 이것이 엄격한 보장은 아니라고 적는다.
  - 즉 tombstone을 보낸 순간 옛 값이 디스크에서 사라지는 것이 아니다.
- compaction이 아닌 시간 기준 보존(`retention.ms`, 기본 7일 — [distributed/21-kafka-internals](../../distributed/21-kafka-internals/2-summary.md))은 세그먼트째 지운다. 메시지 하나만 골라 지우는 API는 없다. Admin API `deleteRecords`는 "주어진 오프셋보다 작은 레코드"를 파티션 앞쪽부터 통째로 지운다(Kafka 4.1 `Admin.java`).
- 이벤트 소싱 저장소에서 이벤트를 고치거나 지우는 것은 "이벤트는 바꾸지 않는다"는 전제와 충돌한다([distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)).
- 그래서 설계 단계의 선택지가 셋이다(event-driven.io, 2023-11-26 글).
  - **분리**: 개인정보를 일반 이벤트와 다른 토픽·저장소에 둔다.
  - **forgettable payload**: 이벤트에는 개인정보 대신 조회 링크(URN)만 싣고, 개인정보는 지울 수 있는 저장소에 둔다.
  - **crypto-shredding**: 개인정보 필드를 주체별 키로 암호화해 싣고, 삭제 요청 때 키를 지운다.
  - 같은 글은 토픽·스트림 **이름**에 이메일 같은 개인정보를 넣지 말라고 한다. tombstone 뒤에도 이름은 남기 때문이다.

### 4. crypto-shredding — 키를 지워 사본 전체를 못 읽게

```text
  키 저장소(KMS·볼트)               이벤트·DW·백업 (어디로 복제돼도 같은 암호문)
  user_001 → K1                    evt_1 user_001 amount=12000 contact=Enc_K1("…")
  user_002 → K2   ──삭제──▶ 없음    evt_2 user_002 amount=30000 contact=Enc_K2("…")  ← 이제 아무도 못 연다
  user_003 → K3                    evt_3 user_003 amount= 8000 contact=Enc_K3("…")
```

- *crypto-shredding*: 데이터를 지우는 대신 **그 데이터를 연 유일한 키**를 지워 읽을 수 없게 만드는 삭제. 백업처럼 선택 삭제가 어려운 곳에 특히 쓸모 있다. 기본 개념과 봉투 암호화는 [security/27](../../security/27-pii-classification-masking-retention/2-summary.md) §4, [security/09](../../security/09-randomness-and-key-management/2-summary.md) §5.
- 이 노트의 초점은 데이터 파이프라인에서의 **암호화 범위 설계**다. 무엇을 키로 묶느냐가 키 폐기 뒤 남는 것을 정한다.
- EDPB Guidelines 02/2025(블록체인) 관련 문장 — 공개 의견 수렴 뒤 확정판 Version 2.0(2026-07-07 채택) §4.2 문단 51 기준. 수렴 전 v1.1(2025-04-08)에도 같은 취지 문장이 있다.
  - 복호 키를 지우면 암호화된 데이터는 이해할 수 없게 된다 — 단 알고리즘이 깨지거나, 복호 기법이 발전하거나, 키가 이미 유출된 경우는 예외다.
  - **암호화된 개인정보도 여전히 개인정보**이고, 암호화가 GDPR 준수 의무를 없애 주지 않는다.
  - "기술적 불가능"을 GDPR 미준수의 정당화로 쓸 수 없다(같은 §4.2 문단 50). 개인정보를 블록체인에 저장하는 것은 일반적으로 권하지 않는다(문단 48).
- 가명화도 같은 선상에 있다. GDPR 제4조 5항의 가명화는 "추가 정보 없이는 특정인에게 귀속되지 않게" 처리한 것이고, 전문 26은 가명 처리된 정보도 추가 정보로 귀속될 수 있으면 **식별 가능한 사람에 관한 정보**로 본다.

### 실험: 키 폐기 뒤 복호 불가, 그리고 암호화 범위 설계 오류 (Java 21)

(실험, `Shred.java`, eclipse-temurin:21-jdk — OpenJDK 21.0.12, `--network none`, JDK `javax.crypto`만. 주체 3명, 이벤트 6건. 설계 A는 연락처만 주체 키로 암호화하고 금액은 평문. 설계 B는 연락처와 금액을 한 덩어리로 주체 키로 암호화.)

```java
static byte[] seal(SecretKey k, String pt, String aad) throws Exception {
    byte[] n = new byte[12]; RNG.nextBytes(n);                       // 호출마다 새 96비트 nonce
    var c = Cipher.getInstance("AES/GCM/NoPadding");
    c.init(Cipher.ENCRYPT_MODE, k, new GCMParameterSpec(128, n));
    c.updateAAD(aad.getBytes(StandardCharsets.UTF_8));               // 이벤트 ID를 AAD로 묶음
    byte[] ct = c.doFinal(pt.getBytes(StandardCharsets.UTF_8));
    return ByteBuffer.allocate(12 + ct.length).put(n).put(ct).array();
}
// 설계 A: new EventA(id, subject, amount, seal(key(subject), contact, id))
// 설계 B: new EventB(id, subject, seal(key(subject), contact + "|" + amount, id))
keyStore.remove("user_002");                                          // 삭제 요청: 키 폐기
```

```text
== 삭제 전 총매출  A=103000  B=103000
== user_002 키 폐기 후
evt_2 백업 암호문 52B → 키 없음 — 복호 불가
evt_2 다른 주체(user_001) 키로 시도 → AEADBadTagException(Tag mismatch)
evt_5 백업 암호문 52B → 키 없음 — 복호 불가
evt_5 다른 주체(user_001) 키로 시도 → AEADBadTagException(Tag mismatch)
총매출  A=103000  B=32000  (B는 복호 못 한 금액이 빠짐)
남아 있던 키 사본으로 evt_2 → 복호 성공: user_002@example.invalid
```

- 두 번 돌려 같은 출력을 얻었다(nonce는 실행마다 다르지만 출력에 나오지 않는 값이다).
- 키를 지운 뒤 백업 사본의 암호문 52바이트(nonce 12 + 평문 24 + 태그 16)는 열 수 없다. 다른 키로 열려고 하면 GCM 태그 검증이 실패한다.
- **설계 B의 총매출이 103,000 → 32,000으로 줄었다.** user_002의 금액 30,000 + 41,000이 개인정보와 같은 키로 묶여 함께 사라졌다. 집계에 남겨야 할 금액까지 주체 키로 암호화하면, 삭제 요청마다 과거 집계가 소급해서 바뀐다(⚠ 커리큘럼 — 암호화 범위 설계 오류).
  - 주의: `user_002`에 연결된 개별 금액은 그 자체로 식별 가능한 사람의 거래 정보다(GDPR 제4조 1항). 즉 설계 A에도 개인정보가 남는다. 금액을 남길 근거는 제17조 3항 예외(예: 세법상 보존 의무)이거나, 사람을 식별할 수 없게 만든 집계여야 한다(해석).
- 설계 A는 연락처만 주체 키로 묶어 총매출이 그대로다. 금액은 남지만 연락처는 못 읽는다.
- 마지막 줄: 어떤 서비스가 메모리·캐시에 들고 있던 **키 사본**으로는 여전히 열린다. 키 저장소에서 지워도, 키가 복제된 곳(캐시·로그·백업된 키 저장소)이 남아 있으면 crypto-shredding은 성립하지 않는다.

### 5. 보존 기한 — 넣을 때 지울 때를 정한다

```text
  데이터 종류          보존 근거                 기한(예시)     만료 처리
  ──────────────      ─────────────────────    ────────────   ─────────────────────────
  주문·결제 기록        세법·전자상거래법          5년            분리 보관 → 기한 후 삭제
  운영 로그(개인정보 X)  장애 분석                 30일           세그먼트·파티션째 삭제
  행동 이벤트(가명)      분석 목적                 13개월         파티션 DROP
  탈퇴 회원 프로필       목적 소멸                 지체 없이       삭제 + 전파
  백업                 복구                     35일 순환        순환 만료(그 안의 삭제분은 복원 시 재삭제)
```

- 기한은 예시다. 실제 기한은 법·계약·목적으로 정한다(한국 법령 기준 표는 [engineering-practice/17](../../engineering-practice/17-legal-standards/2-summary.md) §5).
- 시간으로 자른 파티션에 두면 만료가 `DROP`/세그먼트 삭제 한 번이다. 행 단위 `DELETE`로 오래된 데이터를 지우는 것은 대량 DML 문제가 된다([database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md), [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)).
- 백업 안의 삭제분: 백업을 복원하면 지운 사람이 되살아난다. 복원 절차에 "삭제 요청 로그를 다시 적용"을 넣거나, 백업의 개인정보를 crypto-shredding으로 묶는다(해석).

## 쓰이는 자료구조·알고리즘

- **주체별 키 맵** — 주체 ID → 데이터 키(DEK). 키 폐기 = 맵에서 항목 삭제 + 그 키의 모든 사본 파기. 실무에서는 KMS의 키 포장(KEK)으로 DEK를 포장해 데이터 옆에 둔다([security/09](../../security/09-randomness-and-key-management/2-summary.md) §5).
- **AEAD(AES-GCM)** — 기밀성 + 무결성. 잘못된 키·조작된 암호문은 `AEADBadTagException`으로 거부된다([security/03-symmetric-encryption-and-aead](../../security/03-symmetric-encryption-and-aead/2-summary.md)).
- **tombstone·compaction** — 키별 최신 값만 남기는 로그 정리. 삭제는 "null 값 레코드 추가"로 표현되고 실제 제거는 나중의 compaction이 한다.
- **계보 그래프 하류 순회** — 삭제 전파 대상 목록(11번의 BFS).
- **카탈로그 전수 검색** — `information_schema.columns`로 쿼리를 생성해 식별자 잔존을 찾는 확인 절차(실험).

## 적용 — 풀어나가는 법

### 1. 삭제 요청 처리 순서

1. 요청 접수 기록(언제·누가·무엇을) — 처리 기한(제12조 3항 1개월)을 재는 기준점.
2. 보존 의무 확인 — 제17조 3항 예외(법적 의무·법적 청구 등)에 해당하는 데이터는 분리 보관으로 옮긴다.
3. 계보(11번)로 사본 목록을 만든다. "미상" 경로는 포함.
4. 경로별 삭제 실행: DB `DELETE`, 검색 인덱스 문서 삭제, Kafka tombstone(compact 토픽에서만 — 기본 `delete` 토픽은 보존 만료·정리된 새 토픽으로 재작성), DW 파티션 재적재, 외부 수령자 알림(제19조).
5. 키 폐기(crypto-shredding을 쓰는 경로): 키 저장소·캐시·백업된 키 사본까지.
6. 확인 검색: 잔존 탐색 쿼리(실험)를 돌려 0건인지 본다. 결과를 처리 기록에 남긴다.

### 2. 삭제 요청을 이벤트로 전파 (Java)

```java
// 삭제 요청을 "삭제 이벤트"로 내보내고, 각 사본 소유 팀이 소비해 자기 저장소를 지운다
record ErasureRequested(String requestId, String subjectId, Instant receivedAt, Set<String> retainedCategories) {}

@Transactional
public void requestErasure(String subjectId, Instant now) {
    var req = new ErasureRequested(UUID.randomUUID().toString(), subjectId, now, Set.of("ORDER_RECORD"));
    jdbc.update("INSERT INTO erasure_request(id, subject_id, received_at, status) VALUES (?, ?, ?, 'OPEN')",
                req.requestId(), subjectId, Timestamp.from(now));
    outbox.append("privacy.erasure-requested", subjectId, req);   // 같은 트랜잭션의 outbox(distributed/16)
    keyStore.destroy(subjectId);                                   // 주체 키 폐기 — 개인정보 필드만 묶은 키
}
// 각 소비자는 처리 후 erasure_ack(request_id, store, done_at)를 남긴다 → 모든 사본의 ack가 모이면 CLOSED
```

- 이벤트에 연락처 같은 직접 식별 정보는 싣지 않는다. 주체 ID(가명)와 요청 ID만 싣는다.
  - 단 주체 ID도 각 저장소가 대상을 찾는 데 쓰는, 사람에게 연결되는 값이다. 가명 정보도 개인정보로 보는 전문 26에 따라 이 이벤트 토픽 자체의 보존·접근 범위도 관리한다(해석).
- `outbox`·`keyStore`는 가상의 컴포넌트다. outbox 패턴은 [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).

### 3. 진단 쿼리

```sql
-- 열린 삭제 요청 중 기한(1개월)이 다가오는 것
SELECT id, subject_id, received_at, received_at + interval '1 month' AS due
FROM erasure_request WHERE status = 'OPEN' ORDER BY received_at;

-- 사본별 미완료 확인
SELECT r.id, s.store FROM erasure_request r CROSS JOIN expected_store s
WHERE NOT EXISTS (SELECT 1 FROM erasure_ack a WHERE a.request_id = r.id AND a.store = s.store);

-- 보존 기한이 지난 파티션 (예: 월 파티션 이름 events_YYYYMM)
SELECT inhrelid::regclass AS partition FROM pg_inherits
WHERE inhparent = 'events'::regclass
  AND to_date(right(inhrelid::regclass::text, 6), 'YYYYMM') < date_trunc('month', now() - interval '13 months');
```

- 위 세 쿼리는 테이블 이름이 가상이라 이 노트에서 실행하지 않았다. 잔존 탐색 쿼리는 실험에서 실행했다.

## 장애 시나리오와 대처

### 1. 원본은 지웠는데 백업·분석 복제본·로그에 남아 있다 (⚠ 커리큘럼)

- 현상: 삭제 완료로 답한 사람의 정보가 분석 대시보드나 검색 결과에 보인다.
- 보이는 형태: 실험에서 원천 0행, 파생 다섯 테이블(DW 2·검색 1·이벤트 로그 1·백업 1)에 잔존. 에러 없음.
- 원인: 삭제가 원천 한 곳에서 끝났다. 사본 목록(계보)과 경로별 삭제 절차가 없었다.
- 대처: 즉시 — 잔존 탐색으로 사본을 찾아 지우고 처리 기록을 고친다. 재발 방지 — 계보 기반 사본 목록, 삭제 이벤트 + 사본별 ack, 마지막에 확인 검색.

### 2. 불변 이벤트 로그에 평문 PII → 지울 방법이 없다 (⚠ 커리큘럼)

- 현상: Kafka 장기 보존 토픽·이벤트 저장소에 이메일·전화번호가 평문으로 있다. 삭제 요청을 처리할 수 없다.
- 원인: 설계 때 개인정보를 일반 이벤트에 섞었다. compaction은 키별 마지막 값만 다루고, active segment는 대상이 아니며, 시간 보존은 세그먼트째 지운다.
- 대처: 새 이벤트부터 분리·forgettable payload·crypto-shredding 중 하나로 바꾼다. 이미 쌓인 것은 토픽을 정리된 형태로 다시 써서 옮기고 옛 토픽을 지우는 마이그레이션이 필요할 수 있다(해석). 토픽 이름에 개인정보를 넣지 않는다.

### 3. 보존 기한이 없는 로그 → 비용과 규제 위반 (⚠ 커리큘럼)

- 현상: 로그·이벤트 저장 비용이 매달 늘고, 5년 전 탈퇴 회원의 행동 로그가 남아 있다.
- 원인: 데이터 종류별 기한을 정하지 않았다(제5조 1항 (e) 보관 제한).
- 대처: 종류별 보존 기한 표를 만들고 시간 파티션·세그먼트 단위로 자동 만료. 기한 없는 데이터셋을 관측 지표로 센다(10번).

### 4. 키를 폐기했더니 남겨야 할 데이터까지 못 읽는다 (⚠ 커리큘럼)

- 현상: 삭제 요청을 처리한 다음 날, 지난 분기 매출 리포트 숫자가 줄었다.
- 보이는 형태: 실험 설계 B — 키 폐기 뒤 총매출 103,000 → 32,000. 복호 실패 행을 건너뛰는 집계가 에러 없이 합계를 줄였다.
- 원인: 보존·집계에 남겨야 할 금액을 지울 연락처와 같은 주체 키로 암호화했다(암호화 범위 설계 오류).
- 대처: 주체 키는 삭제 요청 때 지울 필드에만 쓴다(설계 A). 남기는 금액은 보존 근거(제17조 3항)를 두거나 식별 불가능한 집계로 옮긴다. 이미 섞였다면 키 폐기 전에 남길 필드를 다른 키나 평문으로 다시 써 둔다. 복호 실패 행은 건너뛰지 말고 세어서 알린다.

### 5. 키 사본이 남아 crypto-shredding이 성립하지 않는다

- 현상: 키를 지웠는데 어느 서비스에서는 여전히 그 사람의 연락처가 보인다.
- 보이는 형태: 실험 마지막 줄 — 메모리에 남은 키 사본으로 복호 성공.
- 원인: 키 캐시, 로그에 찍힌 키, 백업된 키 저장소.
- 대처: 키 캐시 TTL을 짧게, 키는 로그에 남기지 않음, 키 저장소 백업의 보존 기한을 정함. 이 조건이 갖춰질 때만 키 폐기를 삭제로 볼 수 있다(security/27의 NIST SP 800-88 Cryptographic Erase 언급과 같은 조건).

## 핵심 문장

- 삭제는 한 테이블의 `DELETE`가 아니라 복제된 곳마다의 전파 작업이다. 사본 목록은 계보로 만들고, 마지막에 확인 검색을 한다.
- GDPR 제17조의 삭제 의무에는 3항 예외(법적 의무·법적 청구 등)가 있다. 보존 의무가 있는 데이터는 분리 보관하고 나머지를 지운다.
- 불변 로그에서 tombstone은 즉시 삭제가 아니고, compact 토픽에서만 삭제 수단이 된다. compaction은 키별 마지막 값을 남기고 active segment를 건드리지 않는다. 개인정보는 처음부터 분리·링크·암호화로 설계한다.
- crypto-shredding은 키를 지워 흩어진 사본을 한 번에 못 읽게 한다. 단 키 사본이 남아 있으면 성립하지 않고, 암호화된 개인정보도 여전히 개인정보다.
- 주체 키로 남겨야 할 금액까지 묶으면, 삭제 요청마다 과거 집계가 소급해서 바뀐다. 키는 삭제 때 지울 필드에만 쓰고, 남기는 값은 보존 근거나 식별 불가능한 집계로 정당화한다.

## 관련 주제·근거

- 선행
  - [11-data-lineage](../11-data-lineage/2-summary.md) — 사본 목록(하류 BFS), "미상" 경로
  - [security/03-symmetric-encryption-and-aead](../../security/03-symmetric-encryption-and-aead/2-summary.md), [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md)
- 후속·연결
  - [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md) — 분류·마스킹·가명화, crypto-shredding 기본 실험
  - [engineering-practice/17-legal-standards](../../engineering-practice/17-legal-standards/2-summary.md) — 한국 법령의 보존 기한·분리 보관·파기
  - [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) §6 — 로그에 남긴 것이 삭제 범위가 된다
  - [distributed/21-kafka-internals](../../distributed/21-kafka-internals/2-summary.md)(세그먼트 보존), [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(불변 이벤트), [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)
  - [database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md), [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md), [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)
  - [15-data-mesh-and-data-products](../15-data-mesh-and-data-products/2-summary.md) — 도메인별 데이터 제품의 보존 정책 소유
- 후속(AI 엔지니어링): [ai-engineering/18-index-freshness-and-reembedding](../../ai-engineering/18-index-freshness-and-reembedding/2-summary.md) — 벡터 인덱스의 삭제 전파
- 근거
  - GDPR(Regulation (EU) 2016/679) 제4조 5항·제5조 1항 (e)·제12조 3항·제17조·제19조, 전문 26 — EUR-Lex 원문 <https://eur-lex.europa.eu/eli/reg/2016/679/oj>. EUR-Lex가 직접 요청에는 빈 응답(202)을 줘서, Internet Archive의 EUR-Lex HTML 사본(2026-01-02)으로 위 조문 문구를 대조했다 <https://web.archive.org/web/20260102051858/https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679>. 2차 사본 gdpr-info.eu <https://gdpr-info.eu/art-17-gdpr/>도 같은 문구다.
  - EDPB Guidelines 02/2025 on processing of personal data through blockchain technologies, Version 2.0, Adopted on 07 July 2026(공개 의견 수렴 뒤 확정판) — §4.2 문단 48·50·51(저장 권고, 기술적 불가능, 암호화), §5.2 Right to erasure <https://www.edpb.europa.eu/system/files/2026-07/edpb_guidelines_202502_blockchain_v2_en.pdf> · 수렴 전 Version 1.1(2025-04-08) <https://www.edpb.europa.eu/system/files/2025-04/edpb_guidelines_202502_blockchain_en.pdf>
  - Apache Kafka 4.1 Design "Log Compaction" — 마지막 값 보장, tombstone, `delete.retention.ms` 기본 24시간, active segment 제외, `min.cleanable.dirty.ratio`·`max.compaction.lag.ms` <https://github.com/apache/kafka/blob/4.1/docs/design/design.md> · Kafka 4.1 `TopicConfig.java` — `cleanup.policy` 기본 `delete`, `delete.retention.ms`는 compacted 토픽 tombstone 보존 시간 <https://github.com/apache/kafka/blob/4.1/clients/src/main/java/org/apache/kafka/common/config/TopicConfig.java>
  - Oskar Dudycz, "GDPR in event-driven architecture"(event-driven.io, 2023-11-26) — 분리, 보존 정책, compaction·tombstone, forgettable payload, crypto-shredding <https://event-driven.io/en/gdpr_in_event_driven_architecture/>
    - 같은 글의 "For GDPR, it's 30 days"는 제12조 3항의 "1개월(2개월 연장 가능)"을 줄여 말한 것으로 보인다(해석). 이 노트는 조문 문구를 따른다.
- 실험 목록
  - 원천 삭제 후 파생 사본 잔존 탐색(`information_schema` + `\gexec`) — postgres:17(PostgreSQL 17.11) 일회용 컨테이너, `--network none`, 합성 사용자 20·주문 100
  - 주체별 AES-256-GCM 키 폐기 후 복호 불가·다른 키 `AEADBadTagException`·암호화 범위에 따른 총매출 차이·키 사본 — `Shred.java`, eclipse-temurin:21-jdk(OpenJDK 21.0.12), `--network none`, 2회 실행 동일 출력
