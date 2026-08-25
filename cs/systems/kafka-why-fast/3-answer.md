# cs/kafka-why-fast — Kafka가 빠른 이유 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 기준 소스는 문서가 아니라 원전(원본 노트·코드)이다.
> ⚠️ **이 정답은 Claude 초안이다(2026-08-20).** 복습 전에 읽지 말 것. 본인 답과 다르면 어느 쪽이 맞는지 원본·코드로 확인하고 고친다.

## 정답

1. "디스크는 느리다"는 random access 기준이다. 같은 HDD에서 random write ~100 IOPS, sequential write ~600MB/s로 수천 배 차이 난다. Kafka는 로그를 끝에 append만 하고 offset 순서로 읽어 디스크 접근을 100% 순차로 강제한다. 여기에 OS 페이지 캐시(자기 캐시를 안 얹음, lag이 작으면 읽기가 RAM→RAM), sendfile zero-copy(JVM이 데이터 경로에서 빠짐), 배치+압축(한 번의 큰 순차 write)이 얹힌다. 핵심은 트릭이 아니라 데이터 모델(파티션=로그 파일, offset=컨슈머 소유 위치, 수정 API 없음)이 디스크가 잘하는 패턴만 쓰도록 강제한다는 것이다.

2. 일반: Disk →(DMA) Page Cache →(copy_to_user, CPU) JVM Buffer →(write, copy_from_user, CPU) Socket Buffer →(DMA) NIC. 복사 4회(DMA 2 + CPU 2), 컨텍스트 스위치 4회. Kafka: Page Cache →(sendfile, 소켓엔 page descriptor만) Network Stack →(scatter/gather DMA) NIC. CPU 복사 0회, DMA 2회, 스위치 2회 — JVM은 경로에서 빠진다. 다른 서버가 못 빼는 이유는 데이터를 객체로 만들기 때문이다(역직렬화 → 비즈니스 로직 → 직렬화). 바이트를 해석하는 순간 사용자 공간을 지나야 한다. Kafka 브로커는 메시지를 해석하지 않고(압축도 프로듀서가 배치 단위로, 브로커는 안 풂) 받은 바이트를 그대로 저장·전달하므로 가능하다.

3. 3시간 전 데이터는 페이지 캐시에서 밀려났으므로 fetch마다 실제 디스크 read가 발생한다. 이 읽기는 순차가 아니라 캐시 미스 패턴의 디스크 I/O이고, Kafka는 읽기/쓰기가 같은 디스크를 쓰므로 프로듀서의 append 쓰기와 디스크를 놓고 경쟁한다 — 쓰기 지연까지 같이 튄다. 추가로 읽어온 옛 데이터가 페이지 캐시를 채우면서 최신 데이터를 밀어내 다른 컨슈머의 캐시 히트율도 떨어뜨릴 수 있다. 이것이 consumer lag을 모니터링하는 이유이고, BookKeeper가 journal/ledger 디스크를 분리한 이유다.

4. 암호화는 사용자 공간(JVM)에서 해야 하므로 sendfile zero-copy를 쓸 수 없다. 페이지 캐시의 바이트를 JVM으로 복사해 암호화한 뒤 다시 소켓으로 써야 하므로 일반 경로(CPU 복사 2회)로 돌아가고 CPU 사용량과 GC 압박이 늘어난다. 특히 컨슈머 fetch와 팔로워 복제 fetch 경로(둘 다 같은 메커니즘)가 영향을 받는다. 쓰기 경로(프로듀서 → 브로커)는 원래 JVM을 지나므로 상대적으로 영향이 작다.

5. 페이지 캐시에만 있는 데이터는 전원 차단 시 유실되지만 Kafka는 복제로 막는다 — 다른 브로커에 복사본이 있으면 한 대는 죽어도 된다는 논리. acks=all은 "ISR 전원이 받았을 때 OK"(전체 replica가 아님). ISR은 replica.lag.time.max.ms 안에서 리더를 따라잡고 있는 replica 집합이고, 새 리더는 ISR 안에서만 뽑는다(뒤처진 replica를 리더로 세우면 유실). min.insync.replicas는 ISR이 이 수 아래로 줄면 쓰기를 거부하게 해서 "acks=all인데 ISR이 리더 혼자"인 상황을 막는다. 셋이 합쳐져야 fsync 없는 내구성이 성립한다.

6. ① 읽었다고 지울 필요가 없다 → append-only가 성립 ② 여러 컨슈머(그룹)가 같은 데이터를 각자 속도로 독립적으로 읽는다 ③ replay는 offset을 뒤로 돌리는 것뿐 ④ 브로커는 컨슈머 상태를 몰라도 되어 단순해지고, 파일 오프셋만 읽으면 되므로 sendfile이 가능 ⑤ pull 모델과 결합해 backpressure가 자동 ⑥ 팔로워 복제도 같은 fetch 메커니즘을 재사용한다. offset이 단조 증가하므로 읽기도 파일을 앞에서 뒤로 훑는 순차 읽기가 된다.

7. 원칙은 같고 저장소가 달라 답이 다르다. HDD 시대 Kafka는 "무조건 순차로"(append-only + 페이지 캐시), NVMe 시대 Redpanda는 "랜덤도 빠르니 병렬성과 코어를 최적화"(Direct I/O + thread-per-core, 페이지 캐시를 버림), 클라우드 시대 WarpStream은 "지연시간보다 비용"(로컬 디스크 없이 S3 직접). LSM은 디스크가 싫어하는 랜덤 쓰기를 메모리에서 모아 순차로 변환하고, Striping은 디스크 한 대의 한계를 여러 대로 분산해 넘고, Kafka는 변환도 분산도 필요 없는 데이터 모델을 설계해 디스크가 잘하는 패턴만 쓰게 한다 — 변환 / 분산 / 설계.
