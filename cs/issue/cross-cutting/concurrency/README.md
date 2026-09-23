# concurrency — 순서·공유·취소

동시에 도는 실행 단위가 같은 상태를 만질 때의 패턴이다.\
공통 원리: **완료 순서는 발행 순서가 아니고, 공유 상태는 한 소유자·한 임계구역에서만 바뀌어야 한다.**\
늦게 도착한 결과·재사용된 식별자·덮어쓰인 슬롯이 최신 상태를 조용히 오염시키는 것이 대표 증상이다.

## 공통 원리

```
  요청 A ──발행──┐                ┌── 응답 A (늦게 도착)
  요청 B ──발행──┼─▶ 비동기 실행 ─┼── 응답 B (먼저 도착)
                 │                │
                 ▼                ▼
          공유 상태 ◀── 누가, 어떤 순서로 쓰나?
            ├─ 세대 토큰·CAS 없음   → 옛 결과가 최신을 덮음
            ├─ check-then-act       → lost update
            └─ 취소 미전파          → 영구 대기·누수
```

## 패턴 카드

- [aba-reusable-identifier](aba-reusable-identifier/) — 재사용되는 식별자(pid·세션 id·재시작마다 리셋되는 카운터·txId)로 수명 조작을 키잉하면 늦게 도착한 정리가 같은 이름의 다음 세대를 건드린다 — 세대(epoch)를 포함한 재사용 불가 키를 쓴다.
- [cancellation-reachability](cancellation-reachability/) — 취소 신호를 확인하지 않는 블로킹·await 지점이 하나라도 있으면 취소가 전파되지 않아 스레드·자식 프로세스가 영구 대기로 샌다.
- [capture-context-at-request-time](capture-context-at-request-time/) — 대상·출처·귀속을 실행 시점의 전역 "현재" 상태에서 다시 읽으면 발행~실행 사이 상태 변화에 오염된다 — 요청 시점에 값으로 캡처해 메시지와 함께 운반한다.
- [critical-section-design](critical-section-design/) — 하나의 불변식은 하나의 임계구역에서 원자적으로 갱신하고(check-then-act 금지), 락 안에서는 느린 I/O·join을 하지 않으며, 중복 작업은 single-flight로 합친다.
- [event-loop-head-of-line-blocking](event-loop-head-of-line-blocking/) — 단일 수신 루프에서 처리·송신을 직접 await하면 가장 느린 작업·구독자가 루프 전체를 막아(HOL) 무관한 메시지까지 지연·타임아웃된다.
- [out-of-order-completion](out-of-order-completion/) — 비동기 응답·이벤트의 완료 순서는 발행 순서와 무관하다 — 세대 토큰·CAS·단조 전이로 늦게 도착한 옛 결과가 최신 상태를 덮지 못하게 한다.
- [single-slot-handoff-loss](single-slot-handoff-loss/) — 용량 1 슬롯·전역 요청 버스에 요청을 두면 동시·버스트 생산자가 서로를 덮어 무음 유실된다 — 큐·id 맵·ACK 후 소비·소비자 단일화로 정확히 1회 전달한다.
- [single-writer-ownership](single-writer-ownership/) — 여러 writer가 락 없이 같은 저장 단위를 read-modify-write하면 lost update가 난다 — 저장소를 writer별로 분리하거나 원자 갱신(조건부 UPDATE·upsert·CAS)으로 단일 소유를 강제한다.
- [snapshot-stream-cursor](snapshot-stream-cursor/) — 스냅샷과 라이브 스트림을 이을 때는 먼저 구독하고 원자적 커서(epoch:seq) 이후만 적용해야 무손실·무중복이며, 커서는 짝이 되는 로컬 상태와 함께만 의미가 있다.
- [thread-affine-object-confinement](thread-affine-object-confinement/) — 특정 스레드·이벤트 루프에 묶인 객체는 그 소유자 안에 가두고 외부에는 채널·threadsafe 진입점만 노출한다(actor 패턴).

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(2) · `race-condition`(7) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
