# distributed/21-kafka-internals — Kafka 내부: 파티션·세그먼트·오프셋 인덱스·페이지 캐시·zero-copy·ISR — 정리 (힌트)

## 해결하는 문제

Kafka는 모든 메시지를 디스크에 쓴다. 그러면서 두 가지를 동시에 해내야 한다.

```text
  ① 빠르게      초당 수십만 건을 쓰고, 여러 그룹이 각자 읽는다
  ② 안 잃게     브로커 한 대가 죽어도 "받았다"고 답한 메시지는 남아야 한다
```

- ①을 위한 답은 "디스크가 잘하는 일만 시킨다"이다. 끝에 붙이기(순차 쓰기), 앞에서 뒤로 읽기, OS 페이지 캐시, `sendfile`.
- ②를 위한 답은 fsync가 아니라 **복제**다. 다른 브로커에 사본이 있으면 한 대의 메모리 손실을 견딘다.
- 이 두 답이 만나는 곳에 설정 몇 개(`acks`, `min.insync.replicas`, 보존 설정)가 있다. 여기를 잘못 잡으면 "받았다"고 한 메시지가 사라진다.

쉬운 예: 은행 거래 장부를 지점 세 곳에 베껴 두는 것이다.
- 장부는 뒤에만 적는다(고치지 않는다). 그래서 빨리 적는다.
- 본점 직원이 "적었습니다"라고 말하는 시점이 중요하다. 자기 장부에만 적고 말했는데, 지점에 베끼기 전에 본점이 불타면 그 거래는 사라진다.

똑같은 구조다.\
`acks=1`은 "리더 장부에만 적고 답한다", `acks=all`은 "베끼는 중인 지점(ISR) 전원이 적은 뒤 답한다"이다.

실무 예:
- 브로커 재시작 뒤 프로듀서는 성공 콜백을 받았는데 컨슈머가 그 메시지를 못 찾는다.
- 보존 기간을 줄였더니 주말 동안 멈춰 있던 배치 그룹이 월요일에 메시지 대부분을 건너뛴다.

"왜 빠른가"의 기초(순차 vs 랜덤, 데이터 경로 그림, 배치·압축, 용어)는 원본 [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) 1~4절에 있다. 이 노트는 디스크 위 구조와 복제를 실험으로 판다.

## 동작·원리

### 1. 파티션 = 디렉터리, 세그먼트 = 파일

```text
  /tmp/kafka-logs/w21-seg-0/                          ← 토픽 w21-seg 파티션 0
    00000000000000000000.log        1,037,120 B      ← 오프셋 0..1023     (닫힌 세그먼트)
    00000000000000000000.index            504 B      ← 오프셋 → 파일 위치 (희소)
    00000000000000000000.timeindex        456 B      ← 타임스탬프 → 오프셋
    00000000000000001024.log        1,037,120 B      ← 오프셋 1024..2047 (닫힌 세그먼트)
    00000000000000001024.index            504 B
    00000000000000002048.log          964,228 B      ← 활성 세그먼트: 여기에만 쓴다
    00000000000000002048.index     10,485,760 B      ← 활성 세그먼트 인덱스는 미리 크게 잡아 둔다
```

- *세그먼트*: 파티션 로그를 일정 크기로 자른 파일. 파일 이름이 그 파일의 첫 오프셋(*base offset*)이다(Kafka 4.1 문서 5.4 Log). compaction 토픽에서는 앞쪽 레코드가 지워져 실제 첫 레코드가 이름보다 클 수 있다. 구현도 base offset을 "이 세그먼트 오프셋의 하한"이라고 적는다(`LogSegment` 생성자 주석).
- 쓰기는 마지막 세그먼트(활성 세그먼트) 끝에만 한다. 정해진 크기(`segment.bytes`)를 넘으면 새 파일로 넘어간다(*roll*).
  - 기본 `log.segment.bytes`는 1073741824(1GiB)다(공용 브로커 `kafka-configs --describe --all`로 확인).
  - Kafka 4.0부터 최솟값이 1MB다(KIP-1030, upgrade 노트). 실험에서 16384를 주자 `Value must be at least 1048576`으로 거절됐다.
- 삭제도 세그먼트 단위다. 메시지 하나를 지우는 API는 없다(compaction 토픽 제외).

실험 — 세그먼트 1MB 토픽에 1000바이트 레코드 3000건을 넣었다.

```text
(실험, Kafka 4.1.0 브로커 3대 + 컨트롤러 1대(일회용), 2026-10-01)
3000 records sent, 2734.7 records/sec (2.61 MB/sec), ...
-rw-r--r-- 1 appuser appuser      504 Oct  1 01:06 00000000000000000000.index
-rw-r--r-- 1 appuser appuser  1037120 Oct  1 01:06 00000000000000000000.log
-rw-r--r-- 1 appuser appuser      504 Oct  1 01:06 00000000000000001024.index
-rw-r--r-- 1 appuser appuser  1037120 Oct  1 01:06 00000000000000001024.log
-rw-r--r-- 1 appuser appuser 10485760 Oct  1 01:06 00000000000000002048.index
-rw-r--r-- 1 appuser appuser   964228 Oct  1 01:06 00000000000000002048.log
```

- 세그먼트당 1024건씩 담겼다. 활성 세그먼트의 `.index`가 10485760바이트인 것은 `log.index.size.max.bytes` 기본값(10485760)만큼 미리 잡아 둔 것이다. 세그먼트가 닫히면 실제 쓴 만큼(504)으로 줄었다.

### 2. 오프셋 N 찾기 — 세그먼트 고르기 → 희소 인덱스 → 짧은 스캔

```text
  fetch(offset=1060)
   ① 세그먼트 고르기: base offset 목록 [0, 1024, 2048]에서 1060 이하 최대 → 1024
   ② 00000000000000001024.index 이진 탐색: 1060 이하 최대 항목
        offset: 1055 position: 16205   ← 이것
        offset: 1071 position: 32410
   ③ .log 파일 16205 바이트 위치부터 배치를 앞으로 훑는다
        [1040..1055] @16205 (건너뜀) → [1056..1071] @32410 ← 1060 여기
```

- *희소 인덱스*: 모든 메시지가 아니라 일정 바이트(`log.index.interval.bytes`, 기본 4096)를 쓸 때마다 한 항목만 둔다. 인덱스가 작아 메모리에 올리기 쉽고, 대가로 마지막에 짧게 훑는다.
- 실험 덤프

```text
(실험, Kafka 4.1.0, kafka-dump-log.sh)
Dumping /tmp/kafka-logs/w21-seg-0/00000000000000001024.index
offset: 1055 position: 16205
offset: 1071 position: 32410
offset: 1087 position: 48615
...
index 줄 수: 63

Dumping /tmp/kafka-logs/w21-seg-0/00000000000000001024.log
baseOffset: 1024 lastOffset: 1039 count: 16 ... producerId: 4000 ... position: 0     ... size: 16205
baseOffset: 1040 lastOffset: 1055 count: 16 ... producerId: 4000 ... position: 16205 ... size: 16205
baseOffset: 1056 lastOffset: 1071 count: 16 ... producerId: 4000 ... position: 32410 ... size: 16205
```

- 관찰
  - 디스크의 단위는 메시지가 아니라 **레코드 배치**(여기선 16건, 16205바이트)다.
  - 배치 하나가 4096바이트보다 커서 배치마다 인덱스 항목이 하나씩 생겼다. 1024건에 63항목이다(첫 배치 뒤부터).
  - 인덱스 파일 504바이트 ÷ 63항목 = 항목당 8바이트다(실험 수치로 계산).
  - 각 항목은 (배치의 마지막 오프셋, 그 배치의 파일 위치)다. 1055 → 16205는 배치 1040..1055의 시작 위치다.
  - `producerId`·`baseSequence`가 찍혀 있다. 멱등 프로듀서(17번)의 시퀀스 번호가 배치 헤더에 들어 있다.
- 이 오프셋 인덱스 방식은 원 논문 이후 바뀐 것이다. 2011 논문의 메시지 ID(논리 오프셋)는 "증가하지만 연속하지 않는" 값으로, 다음 ID = 현재 ID + 메시지 길이였다. 브로커는 세그먼트별 첫 오프셋 목록(in-memory index)만 두었고, 메시지는 flush된 뒤에야 소비자에게 보였다(Kreps 외 NetDB 2011 §3.1). 지금은 오프셋이 파티션별 단조 증가 정수이고(5.4), 소비자에게 보이는 기준은 flush가 아니라 ISR 복제다(4.9).

### 3. 페이지 캐시와 zero-copy — 요약

- Kafka는 메시지를 JVM 힙에 캐시하지 않고 OS 페이지 캐시에 맡긴다. 컨슈머가 따라붙어 있으면 읽기는 캐시에서 끝나 디스크 읽기가 거의 없다(Kafka 4.1 문서 4.2·4.3).
- 읽기는 `sendfile`(Java `FileChannel.transferTo`)로 페이지 캐시에서 소켓으로 바로 보낸다. **SSL을 켜면 `sendfile`을 쓰지 않는다** — TLS 라이브러리가 사용자 공간에서 돌고, Kafka는 커널 TLS의 `SSL_sendfile`을 지원하지 않는다(4.3).
- fsync는 기본으로 하지 않는다. `log.flush.interval.messages` 기본은 9223372036854775807(사실상 무한), `log.flush.interval.ms`는 미설정이다(브로커 설정 조회). 내구성은 복제가 맡는다.
- 경로 그림과 복사 횟수는 원본 2절과 [os/34-zero-copy-and-io-uring](../../os/34-zero-copy-and-io-uring/2-summary.md), 페이지 캐시는 [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md), fsync는 [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md).

### 4. 복제 — 리더, ISR, 하이 워터마크, acks

```text
  파티션 w21-acks1 (RF=3)
  리더 b2:   [0 ........ 99][100 ............ 1099]   ← acks=1이면 여기까지 쓰고 바로 "성공"
  팔로워 b3: [0 ........ 99]                          ← 리더에게 fetch해서 따라온다
  팔로워 b4: [0 ........ 99]
                            ▲
                   하이 워터마크(HW) = ISR 전원이 가진 끝 = 100
                   컨슈머는 HW 앞까지만 읽는다
```

- *리더·팔로워*: 파티션마다 리더 하나가 읽기·쓰기를 받고, 팔로워는 리더에게 fetch해 로그를 베낀다.
- *ISR(In-Sync Replicas)*: 리더를 충분히 따라오는 복제본 집합. 두 조건을 만족해야 한다(4.9 Replication).
  - 컨트롤러와 세션이 살아 있다(KRaft에서는 하트비트, `broker.session.timeout.ms`).
  - 리더 로그 끝을 `replica.lag.time.max.ms`(기본 30000) 안에 따라잡는다.
- *커밋된 메시지*: ISR 전원이 받은 메시지. 컨슈머에게는 이것만 보인다. 이 끝이 *하이 워터마크*다.
  - Kafka 4.1 문서(4.9)는 컨슈머에게 보이는 조건을 둘로 적는다: ISR 전원에 복제됐고, ISR 크기가 `min.insync.replicas` 이상일 것. `acks` 설정과 상관없이 그렇다.
- Kafka의 보장: 커밋된 메시지는 ISR이 하나라도 살아 있는 한 잃지 않는다(4.9).
- `acks`는 프로듀서가 언제 "성공"을 받을지다(`acks` 설정 문서).
  - `acks=0`: 기다리지 않는다.
  - `acks=1`: 리더가 자기 로그에 쓰면 성공. 팔로워가 베끼기 전에 리더가 죽으면 그 레코드는 사라진다.
  - `acks=all`: ISR 전원이 받으면 성공. kafka-clients 4.1.0 기본값이다.
- `min.insync.replicas`: `acks=all` 쓰기에서 ISR 크기가 이보다 작으면 쓰기를 거부한다. 기본은 1이다(브로커 설정 조회). `acks=all`이어도 ISR이 리더 하나로 줄어 있으면 리더 혼자 받고 성공이다. 문서의 예: 복제본 2개 중 하나가 죽으면 `acks=all` 쓰기가 성공하지만 남은 하나마저 죽으면 잃는다(4.9 Availability and Durability Guarantees).
- *unclean leader election*: ISR이 모두 죽었을 때 ISR 밖 복제본을 리더로 세울지. 기본 `false`(데이터를 잃을 수 있는 선출을 막음 = 가용성 대신 일관성)다(4.9, 브로커 설정 조회).
- Kafka 4.1 새 클러스터는 *ELR*(Eligible Leader Replicas, KIP-966 1부)이 기본으로 켜진다. ISR에서 빠졌지만 데이터 손실 없이 리더가 될 수 있는 복제본을 컨트롤러가 따로 기록한다(upgrade 노트). 아래 실험의 `Elr:` 칸이 그것이다. ISR이 비어도 ELR에 펜싱 안 된 복제본이 있으면 컨트롤러가 그것을 리더로 뽑는다(4.1 운영 문서 "Eligible Leader Replicas"). 그래서 `false`여도 ISR 복귀만 기다리는 것은 아니다.

#### 실험: acks=1과 acks=all — 리더가 팔로워보다 앞선 채 죽으면

- 일회용 클러스터: KRaft 컨트롤러 1대 + 브로커 3대(b2·b3·b4), Kafka 4.1.0. 토픽 RF=3, 복제본 순서 2:3:4.
- 순서: 기준 100건(acks=all) → 팔로워 둘을 `docker pause` → 1000건 발행 → 리더를 `docker kill` → 팔로워 `docker unpause` → 20초 뒤 확인.
- 브로커 세션 타임아웃(`broker.session.timeout.ms` 기본 9000, 브로커 설정 조회)과 `replica.lag.time.max.ms`(30000) 안에 리더를 죽이도록 짰다. 그래서 일시정지된 팔로워는 ISR에 남아 있다.

```text
(실험, Kafka 4.1.0 컨트롤러 1 + 브로커 3, 일회용, 2026-10-01)
## acks=1, min.insync.replicas=1
[produce acks=all] 성공 응답(ack) 100건, 실패 0건 {}, 1460ms
## 2) 10:03:51 b3·b4 일시정지(docker pause) → 팔로워 복제 멈춤
[produce acks=1] 성공 응답(ack) 1000건, 실패 0건 {}, 7229ms
## 3) 10:03:59 리더 b2 강제 종료(docker kill) → b3·b4 재개
## 4) 10:04:19 20초 뒤
	Topic: w21-acks1	Partition: 0	Leader: 3	Replicas: 2,3,4	Isr: 3,4	Elr: 	LastKnownElr:
[count w21-acks1] log-start=0, log-end(HW)=100, 읽은 레코드 100건 {base=100}

## b2 재시작 뒤 b2의 로그
INFO [ReplicaFetcher replicaId=2, leaderId=3, fetcherId=0] Truncating partition w21-acks1-0 with TruncationState(offset=100, completed=true) ...
INFO [UnifiedLog partition=w21-acks1-0, dir=/tmp/kafka-logs] Truncating to offset 100

## acks=all, min.insync.replicas=2 (같은 절차, 리더는 b3)
[produce acks=all] 성공 응답(ack) 100건, 실패 0건 {}, 894ms
[produce acks=all] 성공 응답(ack) 0건, 실패 1000건 {TimeoutException=1000}, 10268ms
	Topic: w21-acksall	Partition: 0	Leader: 4	Replicas: 2,3,4	Isr: 4,2	Elr: 	LastKnownElr:
[count w21-acksall] log-start=0, log-end(HW)=100, 읽은 레코드 100건 {base=100}
```

- 관찰
  - `acks=1`: 프로듀서는 1000건 모두 성공을 받았다. 새 리더 b3에는 기준 100건만 있다. **성공 응답을 받은 1000건이 사라졌다.**
  - 돌아온 옛 리더 b2는 새 리더 기준으로 자기 로그를 100까지 잘라 냈다(truncate).
  - 새 리더는 ISR 안(b3·b4)에서 뽑혔다. unclean 선출 없이도 잃었다. ISR 판정은 "몇 초 안에 따라왔나"이지 "모든 레코드를 가졌나"가 아니기 때문이다.
  - `acks=all` + `min.insync.replicas=2`: 팔로워가 멈춘 동안 1000건이 모두 타임아웃으로 실패했다. 성공을 받은 메시지는 하나도 잃지 않았다.
- 해석: `acks=all`의 실패는 "결과를 모름"이다(03번). 리더 로그에는 들어갔을 수 있다. 프로듀서 **내부** 재시도(`retries`)의 중복은 멱등 프로듀서가 막는다(17번). 하지만 애플리케이션이 다시 `send`하거나 새 프로듀서 세션으로 보내면 중복 제거되지 않는다(`KafkaProducer` Javadoc: application level re-sends는 dedup 불가, 한 세션 안에서만 보장). 그 경우는 메시지 ID로 소비자 쪽 중복 제거를 둔다.

### 5. 보존 — 세그먼트째 지운다

- `retention.ms`(브로커 기본 `log.retention.hours`=168, 7일)와 `retention.bytes`(기본 −1, 무제한)로 정한다. 브로커는 `log.retention.check.interval.ms`(기본 300000, 5분)마다 검사한다(브로커 설정 조회).
- 판정 단위는 세그먼트다. 세그먼트 안 **가장 큰 타임스탬프**가 기간을 넘으면 그 세그먼트를 통째로 지운다(아래 브로커 로그 문구).
- 컨슈머 그룹의 커밋 위치는 보존에 아무 영향이 없다. 아무도 안 읽었어도 기간이 지나면 지운다.

#### 실험: 보존 15초 + 멈춘 그룹

- 일회용 클러스터(검사 주기를 5초로 줄임). 토픽 `retention.ms=15000`, 3000건. 그룹 `w21-slow`의 커밋을 오프셋 10으로 둔다.

```text
(실험, Kafka 4.1.0 일회용 클러스터, log.retention.check.interval.ms=5000, 2026-10-01)
## 10:06:47 직후 세그먼트
00000000000000000000.log  00000000000000001024.log  00000000000000002048.log
## 10:07:22 35초 뒤 세그먼트
00000000000000003000.log
GROUP     TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
w21-slow  w21-ret  0          10              3000            2990
## 그룹으로 재개(auto.offset.reset=earliest)
0
INFO [LocalLog partition=w21-ret-0, ...] Rolled new log segment at offset 3000 in 1 ms.
INFO [UnifiedLog partition=w21-ret-0, ...] Incremented log start offset to 3000 due to segment deletion
INFO [UnifiedLog partition=w21-ret-0, ...] Deleting segment LogSegment(baseOffset=0, size=1037120, ...) due to log retention time 15000ms breach based on the largest record timestamp in the segment
```

- 관찰
  - 기간이 지나자 세 세그먼트가 모두 지워졌다. 활성 세그먼트(2048)도 새 세그먼트 3000으로 roll된 뒤 지워졌다(로그의 `Rolled new log segment at offset 3000` 직후 삭제).
  - 그룹은 오프셋 10에 머물러 있었다. `--describe`는 LAG 2990을 보여 주지만, 그 2990건은 이미 디스크에 없다.
  - 재개한 소비자는 0건을 받았다. 커밋 위치가 로그 시작(3000)보다 앞이라 `auto.offset.reset`(여기선 earliest)으로 3000으로 옮겨졌다. 2990건이 한 번도 처리되지 않고 사라졌다.

## 쓰이는 자료구조·알고리즘

- **세그먼트 로그 + 희소 오프셋 인덱스** — base offset으로 정렬된 세그먼트 목록에서 이진 탐색 → 인덱스 파일에서 이진 탐색 → 파일 위치부터 순차 스캔. [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md). 인덱스는 "몇 KB마다 한 점"이라, B+Tree의 안쪽 노드가 아래 페이지마다 키 하나만 두는 희소 인덱스인 것과 같은 발상이다.
- **타임 인덱스** — 타임스탬프 → 오프셋. `offsetsForTimes`·시간 기준 리셋(`--to-datetime`)이 이것으로 오프셋을 찾는다.
- **append-only 로그 = WAL과 같은 구조** — 고치지 않고 붙이기만 한다. DB의 WAL과 다른 점은 로그 자체가 데이터라는 것이다. [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)
- **하이 워터마크 + 리더 에포크 기반 truncate** — 새 리더가 정한 끝까지 팔로워가 자기 로그를 잘라 맞춘다. 실험의 `Truncating to offset 100`. 복제 로그의 기본 동작은 [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md)와 같은 계열이다.
- **레코드 배치** — 압축·CRC·프로듀서 ID/시퀀스가 배치 헤더에 있다. 배치가 저장·전송·인덱스의 단위다.

## 적용 — 풀어나가는 법

### 1. 잃으면 안 되는 토픽의 기본 조합

```bash
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic payments \
  --partitions 12 --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config unclean.leader.election.enable=false
```

```java
props.put("acks", "all");                 // kafka-clients 4.1.0 기본값
props.put("enable.idempotence", "true");  // 기본값. 프로듀서 내부 재시도의 중복 방지
props.put("delivery.timeout.ms", "120000");
producer.send(rec, (md, e) -> {
    if (e != null) outbox.markRetry(rec);  // 실패 = 결과 모름. 재시도 경로로(앱 재전송은 중복될 수 있어 소비자가 ID로 거른다)
});
```

- RF=3, `min.insync.replicas=2`, `acks=all`이면 브로커 하나가 죽어도 쓰기가 계속되고, 확인된 메시지는 두 곳 이상에 있다.
- `acks=1`은 위 실험처럼 확인된 메시지를 잃을 수 있다. 쓰려면 "잃어도 되는 데이터"라고 명시한다.

### 2. 진단 명령

```bash
# 리더·복제본·ISR·ELR
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic payments
# ISR이 복제본 수보다 작은 파티션만
kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions
# ISR이 min.insync.replicas 아래인 파티션만 (acks=all 쓰기가 거부되는 중)
kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-min-isr-partitions
# 세그먼트·인덱스 들여다보기
kafka-dump-log.sh --files /var/lib/kafka/payments-0/00000000000000001024.index
# 토픽 설정(보존·세그먼트) 확인
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type topics --entity-name payments --describe
```

### 3. 보존과 lag을 함께 본다

- 그룹 lag을 **시간**으로 환산한다(가장 오래된 미처리 메시지의 나이). 이 값이 `retention.ms`에 다가가면 경보다.
- 보존을 줄이는 변경 전에 모든 그룹의 lag을 확인한다. 줄인 직후 다음 검사 주기에 오래된 세그먼트가 바로 지워진다.

## 장애 시나리오와 대처

### 1. ISR 축소·acks=1 → 확인된 메시지 유실 (⚠)

- **현상**: 프로듀서는 성공 콜백을 받았는데 컨슈머 어디에도 그 메시지가 없다. 브로커 장애·재시작 직후의 구간이다.
- **보이는 형태**: 돌아온 옛 리더의 로그에 `Truncating partition ... TruncationState(offset=N ...)`·`Truncating to offset N`. 장애 전후로 `--under-replicated-partitions`에 그 파티션이 있었다.
- **원인**
  - `acks=1`: 리더만 쓰고 답했다. 팔로워가 베끼기 전에 리더가 죽었다. 실험에서 1000건이 이렇게 사라졌다.
  - ISR이 리더 하나로 줄어든 상태 + `min.insync.replicas=1`: `acks=all`이어도 리더 혼자 받고 성공한다. 그 리더가 죽으면 같은 결과다(문서 4.9의 예).
- **대처**: `acks=all` + `min.insync.replicas=2` + RF=3. ISR 축소(under-replicated)에 경보를 건다. `unclean.leader.election.enable=false` 유지.

### 2. ISR이 min.insync.replicas 아래 → 쓰기 실패

- **현상**: 브로커 하나를 점검하는 사이 프로듀서 오류가 늘고 지연이 치솟는다.
- **보이는 형태**: 프로듀서 `NotEnoughReplicasException`(ISR이 줄어든 뒤) 또는 그 전의 `TimeoutException`(팔로워가 멈췄지만 아직 ISR에 남아 있는 동안 — 실험에서 1000건 모두 이것). `--under-min-isr-partitions`에 파티션이 나온다.
- **원인**: 내구성을 위해 일부러 고른 동작이다. 사본이 충분하지 않으면 받지 않는다.
- **대처**: RF를 `min.insync.replicas + 1` 이상으로 둬 브로커 하나를 빼도 쓰기가 되게 한다. 롤링 재시작은 under-replicated 0을 확인하며 한 대씩 한다. 실패한 쓰기는 결과 모름이다. 프로듀서 내부 재시도는 멱등 프로듀서가 중복을 막지만, 애플리케이션 재전송은 소비자 쪽 중복 제거로 막는다.

### 3. 세그먼트 보존 설정 실수 → 읽기 전에 삭제 (⚠)

- **현상**: 멈춰 있던 배치 그룹을 다시 켰더니 처리 건수가 거의 없다. 오류도 없다.
- **보이는 형태**: 브로커 로그 `Deleting segment ... due to log retention time ...ms breach`, `Incremented log start offset to N due to segment deletion`. 그룹의 CURRENT-OFFSET이 로그 시작보다 작다. 소비자는 `auto.offset.reset`에 따라 조용히 이동한다(`none`이면 오류).
- **원인**: `retention.ms`·`retention.bytes`를 그룹이 따라올 수 있는 시간보다 짧게 잡았다. 보존은 커밋 위치를 보지 않는다. 실험에서 2990건이 이렇게 사라졌다.
- **대처**: 보존 기간 ≥ 가장 느린 그룹의 최대 정지 시간 + 여유. 중요한 그룹은 `auto.offset.reset=none`으로 두어 조용한 건너뛰기 대신 오류를 낸다. lag을 시간으로 보고 경보를 건다.

### 4. 반대 방향 실수 — 보존이 안 돼 디스크가 찬다

- **현상**: 보존 7일인데 디스크 사용량이 줄지 않는다.
- **보이는 형태**: 오래된 세그먼트 파일이 그대로 있다. 세그먼트의 가장 큰 타임스탬프가 미래이거나, 세그먼트가 커서 한 파일에 오래된 것과 새 것이 섞여 있다.
- **원인**: 삭제는 세그먼트 단위이고 판정은 세그먼트 안 **가장 큰** 타임스탬프 기준이다(실험 로그 문구).
  - 프로듀서가 미래 타임스탬프를 넣으면 그 세그먼트는 기간이 차지 않는다.
  - 쓰기가 적지만 끊기지 않는 파티션은 세그먼트가 1GiB까지 안 차고(시간 기준 roll은 `log.roll.hours` 기본 168시간), 한 세그먼트에 오래된 레코드와 새 레코드가 섞인다. 가장 새 레코드가 기간을 넘을 때까지 오래된 레코드도 같이 남는다. (실험처럼 활성 세그먼트의 가장 새 레코드까지 기간이 지나면 roll하고 지운다.)
- **대처**: 타임스탬프 소스를 확인한다(`message.timestamp.type`, 프로듀서 시계). 쓰기가 적은 토픽은 `segment.ms`를 보존 기간보다 짧게 잡아 세그먼트가 시간 단위로 끊기게 한다. `retention.bytes`로 상한을 둔다.

### 5. lag이 커지면 페이지 캐시가 깨진다

- **현상**: 한 그룹이 오래된 데이터를 재처리하기 시작하자 다른 그룹과 프로듀서 지연까지 늘었다.
- **보이는 형태**: 브로커 디스크 읽기 I/O가 0 근처에서 갑자기 오른다. 따라붙어 있던 그룹의 fetch 지연도 늘어난다.
- **원인**: 따라붙은 소비자는 페이지 캐시에서 읽어 디스크 읽기가 없다(문서 4.3). 오래된 세그먼트를 읽으면 디스크에서 올리고, 그 페이지가 최신 페이지를 캐시에서 밀어낸다.
- **대처**: 대량 재처리는 쿼터를 걸거나 한가한 시간에 한다. 브로커 힙을 작게 두어 페이지 캐시 몫을 남긴다(원본 [Claude 추가] C).

## 핵심 문장

- 파티션은 디렉터리, 세그먼트는 첫 오프셋(base offset)을 이름으로 한 파일이다. 쓰기는 활성 세그먼트 끝에만, 삭제는 세그먼트째로만 한다.
- 오프셋 찾기는 세그먼트 이진 탐색 → 희소 인덱스 이진 탐색 → 짧은 순차 스캔이다. 인덱스 항목은 레코드 배치마다 하나꼴로 생겼다.
- 내구성은 fsync가 아니라 복제다. 커밋된 메시지(ISR 전원이 받은 것)만 ISR 하나가 살아 있는 동안 보장된다.
- `acks=1`은 팔로워가 베끼기 전에 리더가 죽으면 성공 응답을 받은 메시지를 잃는다. 실험에서 1000건이 ISR 안의 정상 선출로도 사라졌다.
- 보존은 커밋 위치를 보지 않는다. 그룹이 보존 기간보다 오래 멈추면 그 메시지가 든 세그먼트가 처리 전에 지워질 수 있다. 그러면 소비자는 `auto.offset.reset`(earliest·latest)으로 조용히 건너뛰고, `none`이면 오류를 낸다.

## 관련 주제·근거

- 선행
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) — 오프셋·전달 보장·멱등 프로듀서
  - [os/34-zero-copy-and-io-uring](../../os/34-zero-copy-and-io-uring/2-summary.md) — sendfile, TLS와 zero-copy
  - 원본 [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) — 순차 I/O, 데이터 경로, 배치·압축, 용어 전체
- 연결
  - [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md) — lag과 리밸런스
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 리더-팔로워 복제, 동기/비동기 복제의 유실 창
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) — 해시 분할과 핫 파티션
  - [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md) · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 단일 리더 복제
- 논문: Kreps·Narkhede·Rao, NetDB 2011 — 세그먼트 파일, in-memory index, 페이지 캐시 의존, sendfile <https://notes.stephenholiday.com/Kafka.pdf>
- Kafka 4.1 문서(소스 `docs/design.html`·`docs/implementation.html`·`docs/upgrade.html` @ 4.1.0) <https://kafka.apache.org/41/documentation.html>
  - 4.2 Persistence, 4.3 Efficiency — 페이지 캐시, sendfile, "sendfile is not used when SSL is enabled"
  - 4.9 Replication — ISR 두 조건, `replica.lag.time.max.ms`, 커밋 정의, unclean leader election, Availability and Durability Guarantees(`min.insync.replicas`, 복제본 2개 예)
  - 5.4 Log — 세그먼트 파일 이름 = 첫 오프셋, roll, 읽기 경로
  - Upgrade 4.0/4.1 — 최소 `segment.bytes` 1MB(KIP-1030), ELR 기본(KIP-966)
  - Operations "Eligible Leader Replicas" — 선출 순서 ISR → ELR → 마지막 리더 <https://kafka.apache.org/41/operations/eligible-leader-replicas/>
- 소스(4.1.0): `KafkaProducer` 클래스 Javadoc(앱 재전송은 dedup 불가, 한 세션 안에서만 멱등) · `LogSegment` 생성자 주석(baseOffset = 하한) <https://github.com/apache/kafka/tree/4.1.0>
- `ProducerConfig` `acks` 설정 문서, 기본값(kafka-clients 4.1.0 `configDef()` 출력), 브로커 기본값(`kafka-configs --describe --all`: `log.segment.bytes`·`log.index.interval.bytes`·`log.index.size.max.bytes`·`log.retention.*`·`log.flush.*`·`min.insync.replicas`·`replica.lag.time.max.ms`·`unclean.leader.election.enable`)
- 실험 목록
  - 공용 `sn-dw-kafka`(Kafka 4.1.0 KRaft 단일 노드): 브로커 기본 설정 조회
  - 일회용 `sn-dw-w17-c1`(KRaft 컨트롤러) + `sn-dw-w17-b2·b3·b4`(브로커), Kafka 4.1.0, 네트워크 `sn-dw-w17-net`, 힙 256MB
    - 세그먼트 1MB·1000바이트×3000건 → 세그먼트 3개(1024건씩), `.index` 63항목(504B), `kafka-dump-log`로 인덱스·배치 확인, `segment.bytes=16384` 거절
    - acks=1 + 팔로워 pause + 리더 kill → 성공 1000건 유실, 옛 리더 truncate 로그 / acks=all + min.insync=2 → 1000건 TimeoutException, 확인된 유실 0
    - `retention.ms=15000` + 멈춘 그룹(커밋 10) → 세그먼트 전부 삭제, 재개 시 0건(2990건 미처리 삭제)
