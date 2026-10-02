# reliability/46-disaster-recovery — 재해 복구: RPO·RTO, 백업 리전, 복구 훈련 — 정리 (힌트)

## 해결하는 문제

고가용성(→ [25-high-availability-topology](../25-high-availability-topology/2-summary.md))은 **부품 하나**가 죽어도 버티게 한다. 그런데 데이터센터·리전이 통째로 안 되거나, 잘못된 `DELETE`가 복제본 전부에 퍼지면 이중화로는 못 버틴다.\
그때 "어디까지의 데이터를 들고, 얼마 안에, 어디서 다시 서비스하나"를 미리 정하고 준비해 두는 것이 재해 복구(DR)다.

```text
 고가용성(HA)                                  재해 복구(DR)
 부품 단위: 서버·디스크·AZ 하나                   작업 전체의 사본: 리전 하나, 데이터 손상
 자동 페일오버, 초~분                              선언 → 전환 절차, 분~시간
 복제는 고장을 막는다                              복제는 손상도 같이 옮긴다 → 시점 백업이 필요
```

- AWS 백서 "Disaster Recovery of Workloads on AWS"는 이 둘을 구분한다. 가용성은 작업의 **구성 요소**를, DR은 작업 전체의 **별도 사본**을 다룬다("High availability is not disaster recovery" 절).
- 같은 절: 계속 복제하는 저장소는 주 쪽에서 지우거나 망가뜨린 파일도 복제한다. 그래서 DR 전략에는 시점(point-in-time) 백업도 들어가야 한다.

쉬운 예: 집에 불이 났을 때의 가족사진이다.
- 같은 집 다른 방에 복사본을 두면(같은 AZ 복제) 불 한 번에 다 탄다.
- 다른 동네 친척 집에 두면(다른 리전) 살아남는다. 하지만 마지막으로 보낸 날 이후 사진은 없다(RPO).
- 사진을 되찾아 앨범을 다시 꾸미는 데 걸리는 시간이 RTO다. 친척 집 주소를 아무도 모르면(훈련 안 함) RTO는 무한이다.

똑같은 구조다.\
실무 예: 리전 장애 대비 백업 리전, DB 비동기 복제 + 시점 복구(PITR), 랜섬웨어 대비 불변 백업.\
기초(RTO·RPO 표, 다중 리전 모델 표, 백업 체크리스트)는 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1 「RTO / RPO」·§4 「다중 리전」·§6 「백업 — 복제와 다르다」에 있다. DB 백업과 PITR 자체는 [database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md).

## 동작·원리

### 1. RPO와 RTO — 시간축 하나에 둘

```text
        마지막 복구 지점                재해 발생                            서비스 복구
 ───────────●──────────────────────────✕───────────────────────────────────●──────▶ 시간
            |<──────── 잃는 데이터 ──────>|<──────────── 서비스 없음 ────────────>|
                     ≤ RPO                                ≤ RTO
```

- *RPO(Recovery Point Objective)*: "마지막 데이터 복구 지점 이후 허용하는 최대 시간". 곧 잃어도 되는 데이터의 양을 시간으로 적은 것이다(AWS 백서 BCP 절).
- *RTO(Recovery Time Objective)*: "서비스 중단부터 복구까지 허용하는 최대 지연"(같은 절).
- 둘은 **목표**다. 실제로 얼마나 잃고 얼마나 걸렸는지는 사고 때나 훈련 때 잰다. 목표와 실측을 구분해야 한다.
- 백서는 복구 목표를 비즈니스 영향 분석과 위험 평가에서 정하라고 한다. 복구 전략의 비용이 장애 손실보다 크면 규제 같은 다른 이유가 없는 한 두지 말라는 말도 있다.

### 2. 네 가지 전략 — 비용과 시간의 사다리

```text
 액티브/패시브 ──────────────────────────────────────────────┐
 백업·복원          파일럿 라이트          웜 스탠바이            │  다중 사이트 액티브/액티브
 RPO/RTO: 시간      RPO/RTO: 수십 분       RPO/RTO: 분           │  RPO/RTO: 실시간에 가까움
 사고 뒤 자원 생성   데이터는 상시 복제,      작게 상시 가동,        │  전 리전이 트래픽을 받음
 백업에서 복원       앱은 꺼 둠(켜는 법만)   사고 뒤 확장            │  "near zero data loss"
 비용 $             비용 $$                비용 $$$             │  비용 $$$$
```

(AWS 백서 그림 6 "Disaster recovery strategies"의 내용을 옮김)

- 다중 사이트 액티브/액티브의 데이터 손실이 "0"이 아니라 "near zero"라고 적힌 점에 주의한다. 리전 사이 복제가 비동기면 마지막 쓰기를 잃을 수 있다.
- 백서: 데이터센터 하나를 잃는 수준의 재해라면 잘 설계된 다중 AZ 작업에는 백업·복원으로 충분할 수 있다. 리전 전체나 규제 요건까지 대비하면 나머지 셋을 고려한다.
- 백서: 페일오버 절차에는 **데이터 플레인 작업만** 쓰라고 권한다. 제어 플레인(자원 생성·설정 API)은 가용성 목표가 더 낮아서, 재해 때 바로 그것이 안 될 수 있다.
  - *데이터 플레인*: 실제 서비스를 하는 경로(요청 처리, 이미 있는 자원의 읽기·쓰기).
  - *제어 플레인*: 자원을 만들고 바꾸는 관리 경로.

### 3. RPO는 복제 방식이 정한다

```text
 클라이언트 ──커밋──> 주(리전 A) ──WAL 전송──> 복제본(리전 B)

 비동기: 주가 디스크에 쓰면 바로 "커밋 성공" → 복제는 뒤따라감
         주가 죽는 순간 아직 안 건너간 커밋 = 잃는 데이터 (RPO = 그 순간의 복제 지연)
 동기:   복제본이 WAL을 받았다고 답해야 "커밋 성공"
         복제본이 안 보이면 커밋이 멈춘다 (RPO ≈ 0, 대신 쓰기 가용성을 내줌)
 백업만: 마지막 백업(또는 마지막 아카이브된 WAL) 이후 전부 잃음
```

- PostgreSQL 17 문서 26.2.5: 스트리밍 복제는 기본이 비동기이고, 대기 서버가 따라갈 만하면 지연은 보통 1초 미만이다.
- 같은 문서 26.2.8: 주가 죽으면 "커밋된 일부 트랜잭션이 복제되지 않아 데이터를 잃을 수 있고, 잃는 양은 페일오버 순간의 복제 지연에 비례한다". 동기 복제는 커밋마다 주와 대기 서버 양쪽 디스크에 WAL이 쓰였다는 확인을 기다린다. 26.2.8.4: 동기 대기 서버 하나가 죽으면 커밋이 "끝나지 않을 수 있다".
- 즉 "RPO 0"이라는 약속은 동기 복제(또는 그에 준하는 장치) 없이는 지킬 수 없다. 평소 지연이 1초 미만이어도, 링크가 나빠지는 순간 지연은 몇 초·몇 분으로 늘고 그만큼이 RPO가 된다.

### 4. 실험: 링크가 끊긴 뒤 주가 죽으면 무엇을 잃나 — 비동기 vs 동기

- 구성: PostgreSQL 17.11 주(pg1)·복제본(pg2) 일회용 컨테이너, 스트리밍 복제(`pg_basebackup -R -X stream`).
- 쓰기: Java(JDBC) 클라이언트가 1행씩 autocommit으로 넣고, 커밋 응답을 받은 마지막 id를 `acked`로 센다.
- 사고: 약 4초 뒤 복제본을 네트워크에서 떼고(리전 사이 링크 장애 흉내) → 약 3초 뒤 주를 `docker kill` → 복제본을 다시 붙여 `pg_promote()` → 복제본의 행 수를 센다.

```java
// Writer46 핵심
try (Connection c = DriverManager.getConnection(url)) {
    PreparedStatement ps = c.prepareStatement("INSERT INTO orders(id) VALUES (?)");
    for (long id = 1; System.currentTimeMillis() - t0 < 20_000; id++) {
        ps.setLong(1, id);
        ps.executeUpdate();          // autocommit: 돌아오면 클라이언트는 "저장됐다"고 믿는다
        acked.set(id);
    }
} catch (SQLException e) { /* 주가 죽으면 여기로 */ }
```

(실험, PostgreSQL 17.11 2대 + JDK 21.0.12, 각 컨테이너 `--cpus=1`, 같은 호스트, 2026-10-01 — 시각은 UTC, 처리량은 실행마다 다르다)

비동기(기본값)

```text
== 모드: async  (PostgreSQL 17.11)
replication: application_name=walreceiver sync_state=async
-- 06:15:22.716 복제 링크 끊기 (pg2를 네트워크에서 분리)
-- 06:15:26.014 주 서버 pg1 강제 종료 (docker kill)
06:15:22.169 acked=472 (+74)
06:15:22.669 acked=545 (+73)
06:15:23.170 acked=628 (+83)
06:15:24.672 acked=917 (+86)
06:15:25.674 acked=1131 (+109)
06:15:26.110 쓰기 실패: An I/O error occurred while sending to the backend.
FINAL acked=1220
-- 복제본 pg2 승격 후
pg2 rows=580 max(id)=580 마지막 행 커밋 시각=06:15:22.889(UTC)
```

동기(`synchronous_standby_names='*'`)

```text
== 모드: sync  (PostgreSQL 17.11)
replication: application_name=walreceiver sync_state=sync
-- 06:15:53.678 복제 링크 끊기 (pg2를 네트워크에서 분리)
-- 06:15:56.925 주 서버 pg1 강제 종료 (docker kill)
06:15:53.152 acked=392 (+63)
06:15:53.653 acked=456 (+64)
06:15:54.154 acked=477 (+21)
06:15:54.655 acked=477 (+0)
06:15:55.155 acked=477 (+0)
06:15:56.658 acked=477 (+0)
06:15:57.004 쓰기 실패: An I/O error occurred while sending to the backend.
FINAL acked=477
-- 복제본 pg2 승격 후
pg2 rows=478 max(id)=478 마지막 행 커밋 시각=06:15:53.812(UTC)
```

(진행 줄은 일부만 옮겼다. 전체는 scratchpad `e46/out-async.txt`·`out-sync.txt`)

- 관찰 1 — 비동기: 클라이언트는 1,220건을 "성공"으로 받았는데, 승격한 복제본에는 580건뿐이다. **640건이 사라졌다.** 복제본의 마지막 행은 22.889, 클라이언트의 마지막 성공은 26.110 직전이다. 실측 RPO ≈ 3.2초 = 링크가 끊겨 있던 시간이다.
- 관찰 2 — 비동기 반복: 같은 시나리오 3번 더 돌렸을 때 잃은 건수는 1,612·872·921건이었다(처리량이 실행마다 달라서). 링크를 끊지 않고 주만 죽인 대조 실행 3번은 잃은 건수가 0·0·0이었다. **평소에 재면 RPO가 0처럼 보인다.** 점검 재실행(같은 스크립트)에서도 링크 단절 2회는 1,572·985건을 잃었고, 대조 2회는 0·0건이었다.
- 관찰 3 — 동기: 링크가 끊긴 순간부터 `acked`가 477에서 멈췄다. 커밋이 대기 서버 확인을 기다리며 멈춘 것이다. 잃은 "성공" 커밋은 0이다. 대가는 링크 장애 동안 쓰기 불가다. 이 실행의 평소 처리량은 비동기 실행보다 낮았다(0.5초당 약 63건 vs 약 74~109건). 다만 점검 재실행에서는 동기 약 110건 vs 비동기 약 95~250건으로 겹쳤다. 복제본이 같은 호스트라 왕복이 짧아서, 동기의 지연 비용이 실행 편차에 묻힌다(리전 간이면 왕복 지연만큼 커진다).
- 관찰 4 — 동기의 함정: 복제본에는 478행이 있다. 클라이언트는 478번에 대해 성공 응답을 받지 못했다(실패로 끝남). 이 현상은 매번 나지는 않는다 — 점검 재실행에서는 acked 705 = 복제본 705행이었다. 링크가 끊긴 순간 그 커밋의 WAL이 이미 건너갔느냐에 달렸다. 즉 "실패 응답 = 저장 안 됨"이 아니다. 커밋 결과가 **모름**인 쓰기가 생긴다. 재시도는 멱등해야 한다(→ [13-idempotency](../13-idempotency/2-summary.md)).

### 5. RTO는 전환 작업만이 아니다

```text
 재해 ──탐지──> 알림 ──에스컬레이션──> 판단(DR 선언) ──실행(전환·확장·DNS)──> 검증 ──> 서비스
       |<───────────────────────────── RTO 안에 다 들어가야 함 ─────────────────────────>|
```

- 백서 "Detection" 절: RTO가 1시간이면 그 1시간 안에 탐지·통보·에스컬레이션·평가·DR 선언·복구가 다 들어가야 한다.
- 같은 절: RTO가 위험한데도 DR을 발동하지 않기로 했다면 계획이 부실하거나 실행에 자신이 없다는 뜻일 수 있으니 계획과 목표를 다시 보라.
- 자동 페일오버는 탐지·판단 시간을 줄이지만, 백서는 불필요한 페일오버 자체가 가용성 위험이라고도 적는다(오탐 → [25](../25-high-availability-topology/2-summary.md) 실험).

### 6. 훈련 — 자주 실행한 경로만 동작한다

- 백서 "Testing disaster recovery": "Our experience has shown that the only error recovery that works is the path you test frequently." 그래서 복구 경로는 적게 두고 정기적으로 실행한다.
- 같은 절: 오래 안 해 본 페일오버는 보조 저장소의 능력·용량·리전의 서비스 할당량(quota)이 이미 부족할 수 있다. DR 리전의 **설정 드리프트**(이미지·할당량·설정)를 관리하라.
  - *설정 드리프트(configuration drift)*: 주 리전에서는 바꿨는데 DR 리전에는 반영되지 않아 둘이 달라지는 것.
- Google SRE 책 26장 "Data Integrity": "No one really wants to make backups; what people really want are restores." 백업의 가치는 복원이 되느냐에 있다.
- Fowler의 블루그린 글(2010)은 블루그린 전환이 핫 스탠바이와 같은 메커니즘이라서 "매 릴리스마다 재해 복구 절차를 시험하는 셈"이라고 적는다. 평소 쓰는 경로를 DR 경로로 삼으면 훈련이 일상이 된다.

## 쓰이는 자료구조·알고리즘

- **WAL·LSN 위치** — 복제·백업의 진행을 로그 위치로 잰다. PostgreSQL `pg_stat_replication`의 `sent_lsn`·`flush_lsn`·`replay_lsn`과 `write_lag`·`flush_lag`·`replay_lag`(PostgreSQL 17에서 열 이름 확인). 주의 현재 LSN과 복제본 LSN의 차이가 "지금 잃을 수 있는 양"이다. WAL 자체는 [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md).
- **기준 백업 + 로그 사슬(PITR)** — 전체 백업 하나에 WAL을 순서대로 재생해 원하는 시점까지 간다. 사슬 중간이 빠지면 그 뒤로 못 간다([database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md)).
- **런북 상태 기계** — 선언 → 데이터 승격 → 앱 확장 → 트래픽 전환 → 검증 → 정상화. 단계마다 확인 명령과 되돌림 조건을 둔다.
- **불변(immutable) 저장** — 한 번 쓰면 기한 전에는 지우거나 고칠 수 없는 백업 저장소. 권한 사고·랜섬웨어가 백업까지 지우는 것을 막는다(원본 §6 체크리스트).

## 적용 — 풀어나가는 법

### 1. 순서

1. 작업별로 RPO·RTO를 정한다. 비즈니스 영향(시간대별로 다를 수 있다 — 백서의 급여 시스템 예)과 비용으로.
2. RPO에 맞는 데이터 경로를 고른다. RPO ≈ 0 → 동기 복제(쓰기 지연·가용성 비용 수용). RPO 분 단위 → 비동기 복제 + 지연 경보. RPO 시간 단위 → 백업.
3. RTO에 맞는 전략(백업·복원/파일럿 라이트/웜 스탠바이/액티브-액티브)을 고른다.
4. 복제 외에 **시점 백업**을 다른 장애 도메인(다른 리전·다른 계정)에 둔다.
5. 런북을 쓴다. 전환은 데이터 플레인 작업으로만 되게 한다(미리 구성한 상태 검사 결과로 라우팅이 바뀌게 하거나, Route 53 ARC 라우팅 제어를 켜고 끄는 식). 레코드 값·가중치를 API로 바꾸는 것은 제어 플레인 작업이다(AWS 백서 "AWS Fault Isolation Boundaries" 부록 B).
6. 훈련한다. 정기적으로 실제 전환하고, 걸린 시간·잃은 데이터를 잰다. 그것이 실측 RTO·RPO다.
7. 드리프트를 관리한다. DR 리전의 이미지·설정·할당량·비밀을 주 리전과 비교하는 검사를 자동으로 돈다.

### 2. RPO 감시 — 복제 지연을 RPO 예산과 비교 (Java, JDBC)

```java
/** 주 서버에서 복제본마다의 재생 지연을 읽어 RPO 예산과 비교한다. */
void checkRpo(Connection primary, Duration rpoBudget) throws SQLException {
    String sql = """
        SELECT application_name, sync_state,
               COALESCE(EXTRACT(EPOCH FROM replay_lag), 0) AS lag_s,
               pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS behind_bytes
          FROM pg_stat_replication
        """;
    int seen = 0;
    try (ResultSet rs = primary.createStatement().executeQuery(sql)) {
        while (rs.next()) {
            seen++;
            double lag = rs.getDouble("lag_s");
            metrics.gauge("replica_replay_lag_seconds", lag, "replica", rs.getString(1));
            if (lag > rpoBudget.toSeconds()) alert("RPO 예산 초과: " + rs.getString(1) + " " + lag + "s");
        }
    }
    if (seen == 0) alert("복제본이 하나도 붙어 있지 않다 — 지금 주가 죽으면 마지막 복구 가능 지점(백업 + 아카이브된 WAL) 이후를 잃는다");
}
```

- 복제본 연결이 끊긴 것이 감지되면 `pg_stat_replication`에서 행이 사라진다. 지연이 0인 것과 행이 없는 것을 구분해야 한다(위 코드의 `seen == 0`).
  - 감지되지 않은 네트워크 단절이면 WAL sender가 `wal_sender_timeout`(PostgreSQL 17 기본 60초)까지 남아, 그동안 행과 옛 값이 보일 수 있다. `reply_time`(마지막 응답 시각)이 멈췄는지도 본다.
- `replay_lag`는 "최근 WAL이 재생되고 그 통보가 오기까지 걸린 시간"이지 "지금 몇 초 뒤처졌나"가 아니다(PostgreSQL 17 문서). 다 따라잡고 쓰기가 없으면 잠시 옛 값을 보이다 NULL이 된다(코드의 `COALESCE`가 0으로 바꾼다). 그래서 RPO 판단에는 `behind_bytes`(주 현재 LSN − 복제본 LSN)와 `flush_lsn`(복제본 디스크에 남은 위치)을 함께 본다. 이 코드는 경보의 출발점이지 RPO 판정 자체가 아니다.

### 3. 훈련 점검표

```bash
# 1) 복제 상태 (주에서)
psql -c "select application_name, sync_state, replay_lag from pg_stat_replication"
# 2) 복제본에서 마지막으로 재생한 트랜잭션 시각 — 실측 RPO의 근거
psql -h <dr-replica> -c "select pg_is_in_recovery(), pg_last_xact_replay_timestamp()"
# 3) 승격 (훈련 환경에서)
psql -h <dr-replica> -c "select pg_promote()"
# 4) 앱의 접속 대상·비밀·할당량이 DR 리전에 맞나 — 런북의 '설정 대조' 단계
```

- 훈련 결과로 남길 것: 서비스 중단(장애 주입)부터 서비스 복구까지 걸린 시간(실측 RTO — 탐지·통보·선언 시간 포함, 선언→복구 구간도 따로), 복제본 마지막 트랜잭션 시각과 사고 시각의 차(실측 RPO), 런북에서 빠진 단계, 수동으로 고친 설정 목록.

## 장애 시나리오와 대처

### 1. ⚠ DR 훈련을 안 함 → 실제 전환 때 설정 누락

- 현상: 리전 장애로 DR을 선언했는데, DR 리전 앱이 뜨지 않거나 엉뚱한 곳에 붙는다. RTO를 훌쩍 넘긴다.
- 보이는 형태: DR 리전에 없는 이미지·비밀·인증서, 서비스 할당량 부족으로 확장 실패, 앱 설정이 여전히 주 리전 DB 주소를 가리킴, DNS TTL이 길어 전환이 늦음.
- 원인: 주 리전에서만 바꾼 설정(드리프트). 한 번도 실행하지 않은 경로. 전환 절차가 제어 플레인 API에 기댐.
- 대처: 정기 실전 전환, 드리프트 자동 검사(백서: AWS Config·CloudFormation 드리프트 감지 예), 전환을 데이터 플레인 작업으로(미리 구성한 상태 검사·ARC 라우팅 제어 — 레코드 가중치 변경은 제어 플레인이다).

### 2. ⚠ RPO 약속과 복제 방식이 맞지 않음

- 현상: "RPO 0"을 약속했는데 페일오버 뒤 "성공" 응답을 받은 주문이 사라졌다.
- 보이는 형태: 실험처럼 클라이언트 성공 1,220건 vs 승격된 복제본 580건. 복제본의 마지막 행 시각이 사고 몇 초 전에서 끊김. 평소 지연 지표는 1초 미만이라 문제를 못 봤다.
- 원인: 비동기 복제. RPO = 페일오버 순간의 복제 지연이고, 그 지연은 링크가 나빠질 때 커진다.
- 대처: RPO 0이 정말 필요한 데이터만 동기 복제(동기 대기 서버를 둘 이상 이름 지어 하나가 죽어도 커밋이 안 멈추게 — PG 문서 26.2.8.4). 나머지는 RPO를 "지연 경보 기준"으로 바꿔 적고 지연을 감시한다. 페일오버 전 옛 주의 미복제 WAL을 회수할 수 있으면 회수한다.

### 3. 동기 복제가 쓰기를 멈춤

- 현상: 리전 간 링크가 불안정해지자 주 DB의 쓰기가 전부 멈췄다. 주 DB 자체는 멀쩡하다.
- 보이는 형태: 실험의 `acked` 정체(+0). `pg_stat_activity`의 `wait_event`가 `SyncRep`("동기 복제 중 원격 서버의 확인을 기다림", PostgreSQL 17 문서 27.2 대기 이벤트 표)인 세션이 쌓인다. 앱 커넥션 풀 고갈.
- 원인: 커밋이 동기 대기 서버의 확인을 기다린다. 대기 서버가 하나뿐이었다.
- 대처: 동기 대기 서버 후보를 여럿(`ANY 1 (s1, s2)` 같은 쿼럼 방식), 같은 리전 안 동기 + 리전 간 비동기 조합. 동기를 끄는 수동 절차를 런북에 두되, 끄는 순간 RPO가 바뀐다는 것을 기록한다.

### 4. 복제가 손상을 옮김

- 현상: 잘못된 배치가 테이블을 지웠고, DR 리전 복제본에서도 지워져 있다.
- 보이는 형태: 주와 복제본이 똑같이 틀림. DR 전환이 아무것도 되돌려 주지 않음.
- 원인: 복제는 고장을 막지만 논리 사고를 그대로 옮긴다(백서 HA≠DR 절, 원본 §6).
- 대처: 다른 장애 도메인의 시점 백업 + WAL 아카이브로 사고 직전으로 PITR. 복원을 정기적으로 실제로 해 본다(SRE 26장: 사람들이 원하는 것은 복원이다).

### 5. 결과를 모르는 커밋을 재시도해 중복

- 현상: 페일오버 뒤 일부 주문이 두 번 들어갔다.
- 보이는 형태: 실험 관찰 4처럼, 클라이언트는 실패를 받았는데 데이터는 새 주에 있다. 재시도가 같은 내용을 또 넣었다.
- 원인: 커밋 응답이 오기 전에 연결이 끊기면 결과는 "모름"이다.
- 대처: 쓰기에 멱등 키를 붙이고, 재시도 전에 키로 존재를 확인한다([13-idempotency](../13-idempotency/2-summary.md)).

## 핵심 문장

- HA는 부품을 지키고 DR은 작업 전체의 별도 사본을 지킨다. 복제는 손상도 옮기므로 DR에는 시점 백업이 필요하다.
- RPO는 잃어도 되는 데이터의 시간, RTO는 멈춰 있어도 되는 시간이다. 둘 다 목표이고, 실측은 사고나 훈련에서 잰다.
- RPO는 복제 방식이 정한다. 실험에서 비동기 복제는 링크가 끊긴 3.2초 동안의 640건을 잃었고, 링크가 멀쩡할 때는 0건이라 평소에는 문제가 안 보였다.
- 동기 복제는 RPO를 0에 가깝게 하는 대신, 대기 서버가 안 보이면 쓰기를 멈춘다. 실패 응답을 받은 쓰기가 복제본에 있을 수도 있다.
- RTO에는 탐지·판단·선언 시간이 들어간다. 자주 실행한 복구 경로만 동작한다 — DR 리전의 설정 드리프트를 관리하고 정기적으로 실제 전환한다.

## 관련 주제·근거

- 선행
  - [25-high-availability-topology](../25-high-availability-topology/2-summary.md) — 이중화·페일오버
  - [database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md) — 백업 방식·PITR·복원 검증
  - 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1 RTO/RPO, §4 다중 리전 표, §6 백업. 참고: 원본 §4 표의 액티브-액티브 RPO "~0"은 동기 복제일 때 이야기다. 비동기 리전 간 복제면 AWS 백서 그림 6의 표현대로 "near zero"이고 페일오버 순간의 지연만큼 잃는다(위 실험).
- 후속·연결
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 동기 수준·복제 지연·페일오버에서 잃는 것
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 사고 선언·지휘
  - [44-runbooks-and-operational-readiness](../44-runbooks-and-operational-readiness/2-summary.md) — DR 런북, [45-chaos-and-resilience-testing](../45-chaos-and-resilience-testing/2-summary.md) — 게임 데이·장애 주입으로 하는 훈련
  - [13-idempotency](../13-idempotency/2-summary.md) — 결과 모름 쓰기의 재시도
  - [51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md) — 리전 장애 때 스탬프의 영향
- 문서·글
  - AWS 백서 "Disaster Recovery of Workloads on AWS: Recovery in the Cloud"(2021-02-12) — "High availability is not disaster recovery", "Business Continuity Plan (BCP)"(RTO·RPO 정의), "Disaster recovery options in the cloud"(그림 6, 데이터 플레인만으로 페일오버), "Detection", "Testing disaster recovery" <https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-workloads-on-aws.html>
  - PostgreSQL 17 문서 26.2 "Log-Shipping Standby Servers" — 26.2.5 스트리밍 복제(기본 비동기), 26.2.8 동기 복제(비동기의 데이터 손실 설명 포함), 26.2.8.4 고가용성 계획 <https://www.postgresql.org/docs/17/warm-standby.html>
  - Google SRE 책 26장 "Data Integrity: What You Read Is What You Wrote" <https://sre.google/sre-book/data-integrity/>
  - Fowler, "BlueGreenDeployment", 2010 — 매 릴리스가 DR 절차의 시험
- 실험 목록
  - E46: PostgreSQL 17.11 주·복제 일회용 컨테이너 + Java JDBC 쓰기 — 링크 단절 3초 후 주 강제 종료, 비동기(4회: 잃은 건 640·1,612·872·921) vs 동기(잃은 성공 커밋 0, 쓰기 정체), 대조로 링크 정상 비동기(3회: 0건). 점검 재실행: 비동기 2회 1,572·985건, 동기 1회 0건(acked 705 = 복제본 705), 대조 2회 0·0건. 코드 scratchpad `rel/23/e46/{Writer46.java,run46.sh,run46b.sh}`, 컨테이너 `sn-rl-w23-{pg1,pg2,writer}`
