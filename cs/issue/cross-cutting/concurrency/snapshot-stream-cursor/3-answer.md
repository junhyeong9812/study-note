# cs/issue/concurrency/snapshot-stream-cursor — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **두 순서의 실패.** "스냅샷 → 리스너"면 두 호출 사이에 도착한 출력이 스냅샷에도 없고 리스너도 못 받아 **유실**된다.\
   "리스너 → 스냅샷"만 하면 그 사이 도착분이 리스너로도 오고 스냅샷에도 포함돼 **중복**된다.\
   둘 다 막으려면 스냅샷과 스트림 사이를 원자적으로 경계 짓는 **커서(단조 증가 seq)**가 필요하다 — 리스너를 먼저 걸어 버퍼링하고, 스냅샷이 알려준 마지막 seq보다 큰 청크만 적용한다.
   > **커서** — 스트림에서 "여기까지 반영했다"를 가리키는 위치 값. 재개·중복 판정의 기준.

2. **원자 반환.** 스냅샷이 돌려준 `last_seq`가 돌려준 `bytes`의 끝과 정확히 일치해야 "이 seq 이후만 적용"이 성립한다.\
   seq 증가와 append가 다른 시점에 일어나면, 스냅샷이 "내용은 c5까지, seq는 4"를 볼 수 있어 c5가 중복되거나, 반대로 "내용은 c4까지, seq는 5"를 봐 c5가 유실된다.\
   그래서 `push`는 한 락 안에서 `seq += 1`과 append를 하고, `snapshot`도 같은 락 안에서 둘을 함께 읽는다.

3. **필터 키 지연 설정.** 리스너는 이미 걸려 있어도 필터가 "내 세션 id"와 일치하는 청크만 통과시킨다.\
   id를 스냅샷 뒤에 대입하면, 스냅샷 계산과 대입 사이의 청크는 스냅샷에도 없고 필터도 통과하지 못해 **버려진다**.\
   구독 필터 키까지 포함해 "구독 준비 완료"를 스냅샷 **전**에 끝내야 한다.

4. **앞설 수는 있어도 뒤처질 수는 없다.** 버스 락은 스트림 위치(seq)만 얼린다. 발행자는 상태를 먼저 바꾸고, 락을 풀고, 그다음 publish로 seq를 받는다.\
   그래서 스냅샷(락 안)이 "아직 seq를 받지 않은 변경"을 이미 볼 수 있다 → 그 변경이 나중에 라이브로 한 번 더 온다(중복 1회). 병합이 멱등이면 무해하다.\
   반대로 "publish 먼저 → 상태 변경"이면 스냅샷이 커서보다 **뒤처져**, 커서 이전이라 라이브로 다시 오지도 않는 변경이 영구 유실된다.\
   이 순서 규율은 합성 발행자 테스트로는 안 잡힌다 — 프로덕션 발행 경로를 태운 경합 테스트여야 순서를 뒤집었을 때 실패한다.
   > **멱등 병합** — 같은 변경을 두 번 적용해도 결과가 한 번 적용과 같은 병합.

5. **epoch:seq.** 서버가 재기동되면 seq가 다시 1부터 시작한다. seq만 있으면 이전 인스턴스의 커서 "seq 100"이 새 인스턴스의 전혀 다른 100번을 가리킨다.\
   재기동마다 바뀌는 epoch를 붙이면 "다른 인스턴스의 커서"를 **구조적으로** 알아보고, 버퍼를 넘은 오래된 커서·미래 커서·손상 커서와 함께 **명시적 Gap → 스냅샷 재동기**로 보낸다.\
   느린 소비자도 같은 경로로 처리한다 — 구독자에게 큐를 주지 않고 링 버퍼 위의 위치만 쥐게 하면, 링에서 밀려난 구독자는 "늦게 재접속한 클라이언트"와 똑같이 Gap을 받는다(메모리 유계).

6. **커서와 로컬 상태의 짝.** 커서는 "이 로컬 상태에는 seq N까지 반영돼 있다"는 뜻이다.\
   detach하면서 화면 상태를 버리고 커서만 들고 재attach하면, 서버는 "N 이후로 새 일 없음"이라고 옳게 답한다 — 그러나 N까지의 세계(세션 목록 등)는 이미 클라이언트에 없다.\
   그래서 상태를 버리면 커서도 버린다(재attach = fresh + 스냅샷). epoch가 바뀌었을 때도 세션과 커서를 함께 폐기한다.

7. **해석 못 한 메시지와 push 버스.** 커서는 "처리한 위치"다.\
   모르는 이벤트라도 봉투에 seq가 있으면 **소비한 것으로 치고 전진 + 알림**(멈추면 같은 줄을 영원히 재생하는 라이브락).\
   위치가 없는 줄(읽지 못한 줄, 모르는 프레임)로는 커서를 움직이지 않고 알림만 한다. 줄 전체를 파싱 오류로 버리면 봉투의 seq까지 버려져 커서가 멎거나 무음 skip이 된다.\
   replay 없는 push 버스는 구독 전 사건을 보관하지 않으므로 "구독 먼저 → 현재 스냅샷 seed → 늦게 온 seed가 새 라이브를 덮지 않게 비교 병합"이 필요하다. 끝내 순서를 보장하기 어려운 1회성 이벤트는 이벤트를 없애고 스냅샷 조회로 흡수하는 쪽이 단순하다.

## 문제 구조 (추상화 코드)

### 변형 A — 스냅샷과 구독 사이의 틈 (유실 또는 중복)

```ts
// 문제 1: 스냅샷 먼저 → 틈 사이 출력 유실
const snap = await getSnapshot(id);
render(snap);
await listen("output", p => apply(p));

// 문제 2: 구독 먼저, 커서 없음 → 겹친 구간 중복
await listen("output", p => apply(p));
render(await getSnapshot(id));
```

```rust
// 고침 (서버): 위치와 내용을 같은 락에서 움직이고, 둘을 원자적으로 반환
fn push(&mut self, data: &[u8]) -> u64 {
    self.last_seq += 1;
    self.buf.extend(data);
    while self.buf.len() > self.cap { self.buf.pop_front(); }
    self.last_seq
}
fn snapshot(&self) -> (Vec<u8>, u64) { (self.buf.clone(), self.last_seq) } // 같은 락 안
```

```ts
// 고침 (클라): 구독 먼저 → 스냅샷 → seq > last_seq 만
let ready = false, lastApplied = 0; const pending = [];
const applyLive = p => { if (p.seq > lastApplied) { apply(p); lastApplied = p.seq; } }; // 라이브도 seq 비교
await listen("output", p => ready ? applyLive(p) : pending.push(p));
const { bytes, lastSeq } = await getSnapshot(id);
render(bytes); lastApplied = lastSeq;
for (const p of pending) applyLive(p);   // seq > lastSeq 만 적용
ready = true;                            // 드레인과 전환은 같은 동기 구간 — 그 사이 이벤트가 끼지 않음(단일 스레드 이벤트 루프 전제)
```
무엇이 깨졌나: 탭 복귀 시 출력 보존을 만족할 수 없었다 — 순서 자체가 계약이다.

### 변형 B — 복원 시드가 seq 공간을 차지

```rust
// 고침: 디스크에서 복원한 내용은 순수 백필 — seq는 0 유지, 첫 라이브 청크가 seq=1
fn seed(&self, bytes: &[u8]) {
    let mut sb = self.lock();
    sb.buf.clear(); sb.buf.extend(bytes);
    // last_seq 는 건드리지 않음
}
```
무엇이 깨졌나(설계 리뷰에서 발견): 재시작 후 복원 데이터에 seq를 어떻게 이을지 정하지 않으면 첫 라이브 청크와의 중복/누락 판정이 어긋난다.

### 변형 C — 구독 필터 키를 스냅샷 뒤에 설정

```ts
// 문제
const snap = await getSnapshot(existing);
sessionId = existing;          // 이 전에 온 청크는 필터(sessionId 일치)를 통과 못 함

// 고침
sessionId = existing;          // 스냅샷 전에 대입 → 리스너가 처음부터 pending에 버퍼
const snap = await getSnapshot(existing);
write(snap.data); lastApplied = snap.lastSeq;
```
무엇이 깨졌나: 다른 창에서 세션을 다시 붙일 때 사이의 출력이 사라졌다. 무손실은 링 버퍼 용량 안에서만 성립한다.

### 변형 D — 발행 순서와 스냅샷 cut (재개 프로토콜)

```rust
// 발행자 규율: 상태 변경 → 락 해제 → publish
state.apply(change);
bus.publish(event);            // 여기서 seq 부여

// attach: 한 번의 락 획득에서 (재생할 바이트, 커서)를 함께 캡처
fn attach(&self, cursor: Option<Cursor>) -> Attach {
    let g = self.lock();
    match decide(cursor, g.epoch, g.ring_range()) {
        Resume(from) => Attach::Replay(g.ring_from(from)),
        Gap(reason)  => Attach::Snapshot(g.snapshot(), g.position()),
    }
}
```
무엇이 깨졌나: 계약 주석이 "중복도 없다"고 적었는데 거짓이었다(정정: 중복 1회 가능, 유실 없음). 순서를 뒤집으면 실패하는 테스트를 프로덕션 발행 경로로 고정했다.

### 변형 E — 상태를 버리고 커서만 들고 재개

```rust
// 문제: detach 후에도 커서를 이어받아 재attach
fn reattach(&mut self) { self.attach(self.saved_cursor) }   // 서버: "놓친 것 없음"

// 고침: 상태를 버리면 커서도 버림 / epoch 변화 시 전부 폐기
fn detach(&mut self) { self.sessions.clear(); self.cursor = None; }
fn on_handshake(&mut self, epoch: u64) {
    if Some(epoch) != self.epoch { self.sessions.clear(); self.cursor = None; notify(); }
}
```
무엇이 깨졌나: e2e 테스트가 재attach 뒤 세션 1개 소실을 잡았다.

### 변형 F — 해석 못 한 메시지와 커서 전진

```rust
// 문제: 모르는 종류를 파싱 오류로 줄째 거부 → 봉투 seq까지 버려짐
let frame: Frame = parse(line)?;          // Err → 커서 정지(무한 재생) 또는 무음 skip

// 고침: Unknown을 값으로 디코드하고, 위치 유무로 전진 결정
match parse(line) {
    Ok(Frame::Event { seq, ev: Event::Unknown(kind) }) => { warn_once(kind); cursor = seq; }
    Ok(Frame::Unknown(_)) | Err(_)                      => { warn(); /* 커서 그대로 */ }
    Ok(f) => { handle(f); cursor = f.seq(); }
}
```
무엇이 깨졌나(설계 시 식별): 서버가 더 새로우면 모르는 태그가 온다. 모르는 필드는 무시(가산 호환), 프로토콜 버전 불일치는 치명 오류로 분리.\
같은 구조: 모르는 세션 키의 이벤트도 (세션, 종류)당 1회 알리고 전진 — 멈추면 라이브락.

### 변형 G — replay 없는 push 이벤트 + 컴포넌트 로컬 상태

```tsx
// 문제: 화면 상태가 컴포넌트 로컬, 이벤트는 재방출 없음, 구독이 invoke보다 늦음
useEffect(() => { invoke("attach"); }, []);
useEffect(() => { listen("ended", h); }, []);     // 등록 전 발행된 종료 사유는 영구 유실

// 고침: 구독 먼저 → seed → 비교 병합, 구독 실패도 표면화
const un = await listen("timeline", h).catch(e => setStreamError(e));
const seed = await invoke("timelines");
setState(prev => mergeSnapshot(prev, seed));           // 늦은 seed가 새 라이브를 덮지 않음(버전·seq 비교 병합)
```
무엇이 깨졌나: 탭 이탈 후 복귀하면 타임라인이 사라졌고, 끝난 세션은 영구 빈 화면이었다.\
최종적으로 1회성 종료 이벤트는 없애고 스냅샷 조회(짧은 주기 폴링)로 흡수했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
