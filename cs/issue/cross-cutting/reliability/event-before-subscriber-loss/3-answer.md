# cs/issue/cross-cutting/reliability/event-before-subscriber-loss — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **발행자에게는 둘 다 "성공"이다.** 보관 없는 채널은 발행 순간 연결된 구독자 목록에만 복사해 넘기고 끝난다. 목록이 비어 있으면 넘길 곳이 없을 뿐 오류가 아니다.\
   그래서 "아직 등록 전"이든 "잠시 끊김"이든 그 구간의 사건은 **에러 없이 영구 유실**되고, 발행 측 로그는 정상으로 남는다.
   > **fire-and-forget** — 전달 확인 없이 보내고 잊는 방식. 받는 쪽이 없어도 보내는 쪽은 모른다.

2. **존재 ≠ 준비.** 창 생성 이벤트는 "창 객체가 생겼다"는 뜻이지, 그 창의 수신 리스너·UI API·필요한 컨텍스트가 준비됐다는 뜻이 아니다 — 그 틈에 emit한 이관 데이터가 사라졌다.\
   또 `listen()`은 비동기 등록이라 `await`하지 않으면 **등록이 끝났다는 보장이 없다** — 호출 직후에 온 이벤트는 받지 못한다.\
   교정: 대상 창이 API·리스너·컨텍스트가 **모두 준비된 뒤에** `ready`를 보내고, 원본은 그 ack를 받은 뒤에만 넘긴다. "창 생성됨"은 준비 신호로 쓰지 않는다.

3. **빠른 ack가 이중 소유를 만든다.** 원본이 패널을 떼고 emit한 뒤에 ack 리스너를 등록하면, 대상이 ack를 **빨리** 보낼 때 원본은 그 ack를 놓친다. 원본은 타임아웃을 실패로 보고 패널을 되돌려 넣는데, 대상은 이미 패널을 붙였으므로 **같은 세션이 두 창에** 생긴다.\
   교정: 이관 함수를 async로 바꾸고 `await listen(ack)`로 등록을 마친 **다음에** 떼고 emit한다.

4. **대상보다 요청이 먼저 도착한다.** `void create()`는 생성 완료를 기다리지 않으므로, 바로 뒤의 요청은 아직 없는 대상에게 가서 **아무도 처리하지 않고** 버려진다. 에러도 없어 "클릭했는데 아무 일도 안 일어남"으로만 보인다.\
   교정: 대상이 없으면 먼저 활성화·생성하고 그 뒤에 요청한다. 남은 경로는 "생성을 await한 뒤 요청"이 처방이다(그 잔여 경로의 수정은 기록되지 않았고, 당시 도달 불가 경로로 분류됐다).

5. **우연한 전제의 테스트.** 구독은 push만 하고 backfill을 하지 않으므로, 생성과 구독 사이에 생산자가 먼저 출력하면 늦은 구독자는 seq 2부터 받는다. 병렬 빌드·실행 부하가 스케줄링을 바꿀 때만 그 틈이 생겨 **가끔** 실패했다(단독 반복 실행에선 0회).\
   제품 유실은 아니었다 — 바이트는 스크롤백에 남고 스냅샷이 덮으며 실제 소비자는 "구독 먼저, 시드 나중" 순서였다. 틀린 것은 테스트가 단언한 "첫 seq == 1"이라는 **우연한 전제**다. 단언해야 할 실제 불변식은 `live seq > snapshot seq`다(처방으로 기록, 당시 수정 범위 밖이라 빚으로 등재).

6. **보관하는 스트림으로.** 재연결 루프(지수 백오프)는 끊긴 리스너를 **다시 듣게** 할 뿐, 끊겨 있던 동안 발행된 메시지를 돌려주지 않는다. 소비자 다운 구간까지 지키려면 메시지를 **저장하는 스트림**(길이 상한을 둔 append 로그)으로 바꿔 "구독 전이어도 쌓여 있게" 한다.\
   소비자 그룹 + ACK는 여기에 **처리 확인**을 더한다: 읽었지만 ACK 전에 죽은 메시지는 pending으로 남아 기동·재연결·주기 복구 때 다시 처리된다.\
   단, 데이터 결함(필드 누락 등)으로 항상 실패하는 메시지를 ACK하지 않으면 영원히 재전달되는 **poison pill**이 된다 — 데이터 결함은 ACK로 폐기, 인프라 오류만 pending 유지, N회 이상 재전달은 dead-letter 기록 후 ACK.
   > **poison pill** — 처리할 때마다 실패해 큐를 막는 메시지.

7. **이미 지나간 사건.** 프레임워크가 DOM 생성과 스크립트 실행 시점을 소유하면, 레거시 모듈이 실행될 때 `DOMContentLoaded`는 **이미 발생한 뒤**다. 이 이벤트는 다시 발생하지 않으므로 리스너는 영영 불리지 않는다.\
   pub/sub와 같은 구조다 — "사건이 나고 나서 구독했다". 교정도 같은 방향이다: 사건을 기다리지 말고 **지금 상태를 확인해 직접 실행**한다(마운트 후 모듈을 주입하고 init 함수를 직접 호출).

## 문제 구조 (추상화 코드)

### 변형 A — 소비 조건이 안 됐는데 요청을 "소비 완료"로 지움
① 문제 코드
```ts
useEffect(() => {
  const req = store.openRequest;
  store.openRequest = null;           // 먼저 지움
  if (!api) return;                   // api 재마운트 중이면 요청만 사라짐
  api.open(req);
}, [store.openRequest]);
```
② 고친 코드
```ts
useEffect(() => {
  if (!api) return;                   // 지우지 않고 남겨둠 → api 준비 시 재실행
  api.open(store.openRequest);
  store.openRequest = null;
}, [store.openRequest, api, activeContext]);
```
무엇이 깨졌나: 소비 가능 여부를 확인하기 전에 요청을 삭제했다.\
같은 구조: 연결 실패 상태를 짧은 수명 패널이 받게 해, 패널 생성 전에 emit된 `failed`가 무음 → 수명 긴 전역 리스너에서 실패를 받아 알림 보장.

### 변형 B — 구독 등록 완료 전에 상대를 움직임
① 문제 코드
```ts
function handOff(id) {
  detach(id);
  emit("transfer", envelope);
  listen("transfer-result", onAck);   // 등록 완료 전 ack 가 오면 유실
}
```
② 고친 코드
```ts
async function handOff(id) {
  const un = await listen("transfer-result", onAck);   // 등록 완료 보장
  beginTransfer(id); api.getPanel(id)?.close(); endTransfer(id);
  if (api.getPanel(id)) return;                          // 실제 제거 확인
  void emit("transfer", envelope);
}
// 새 창 경로: await listen → 창 생성 → 대상의 "ready" ack 후에만 detach
```
무엇이 깨졌나: "창 생성됨"을 준비 신호로 썼고, 비동기 등록을 기다리지 않았다.

### 변형 C — 생성을 기다리지 않고 대상에게 요청
① 문제 코드
```ts
void store.addContext(ctx);          // 비동기 생성 시작
requestFocus(sessionId);             // 대상 dock 이 아직 없음 → 무동작
```
② 고친 코드 (처방)
```ts
await store.addContext(ctx);
requestFocus(sessionId);
```
무엇이 깨졌나: 요청이 대상보다 먼저 도착했다.

### 변형 D — backfill 없는 구독에서 "처음부터 받는다"를 전제
① 문제 코드
```rust
let s = Session::create(cmd);         // 자식 프로세스가 곧바로 출력 시작
let rx = s.subscribe();               // push 만, 과거 재전송 없음
assert_eq!(rx.recv().seq, 1);         // 부하 시 seq 2 부터 → 가끔 실패
```
② 고친 코드 (처방)
```rust
let snap = s.snapshot();
let rx = s.subscribe();
assert!(rx.recv().seq > snap.seq);    // 실제 불변식만 단언
```
무엇이 깨졌나: 스케줄링에 따라 달라지는 순서를 불변식처럼 단언했다.\
같은 구조: 같은 테스트가 전체 실행 1회차에서 1건 실패, 이후 6회 green — 같은 원인으로 진단만 남기고 빚 등재.

### 변형 E — 수신자 없는 메시지 · 늦게 연결되는 소비자
① 문제 코드
```js
// 브라우저 확장 콘텐츠 스크립트: 측정값을 즉시 보냄 (패널이 아직 안 열렸으면 수신자 없음)
runtime.sendMessage({ metric });          // "Receiving end does not exist" / 유실
```
② 고친 코드
```js
latest[metric.name] = metric;                    // 콘텐츠 스크립트가 캐시 역할
runtime.sendMessage({ metric }).catch(() => {});
onConsumerConnected(port => port.postMessage(latest));   // 새 소비자에게 재전송(backfill)
// 이벤트가 한 번도 없는 지표(값 0)는 초기값을 명시 보고
```
무엇이 깨졌나: 페이지 로드 시점 사건을 나중에 연결되는 소비자가 받을 길이 없었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(변형 A~E)은 "구독·준비를 먼저 확정하고 발행한다, 늦은 소비자에게는 캐시를 재전송한다"이다. 같은 원리에 다른 방안이 쓰인 사례:

### 방안 1 — 재연결 백오프 + 보관 스트림으로 전환
```python
# 문제: pub/sub 리스너에 재연결이 없고, 소비자 다운 중 발행분은 사라짐
await broker.publish("search.log", payload)

# 고친 (1) 리스너 재연결 (계획서 기준 — 적용 여부 미기록)
delay = 3
while True:
    ps = client.pubsub()
    try:
        await ps.subscribe(CH); delay = 3
        async for msg in ps.listen(): handle(msg)
    except asyncio.CancelledError:
        await ps.unsubscribe(); return
    except Exception:
        await asyncio.sleep(delay); delay = min(delay * 2, 30)
# 고친 (2) 보관 스트림 — 소비자가 구독 전이어도 쌓여 있음, 길이 상한으로 메모리 보호
await stream.append("stream:search.log", payload, maxlen=100_000, approximate=True)
```
부수: `create_task`로 띄운 발행 코루틴의 예외는 호출자에게 전파되지 않으므로 태스크 내부에서 잡아야 한다.

### 방안 2 — 소비자 그룹 + ACK 의미론
```python
for msg in stream.read_group(GROUP, CONSUMER, only_new=True):
    try:
        handle(msg); stream.ack(GROUP, msg.id)
    except DataError:                     # 데이터 결함 → 폐기 (poison pill 방지)
        stream.ack(GROUP, msg.id)
    except InfraError:                    # 인프라 오류 → pending 유지, 재처리
        raise
# 기동·재연결·60초 주기로 pending 복구, 5회 이상 재전달 = dead-letter 기록 후 ACK
```

### 방안 3 — 이미 지난 사건은 기다리지 않고 직접 호출
```js
// 문제: 프레임워크가 하이드레이션 후 레거시 모듈을 실행 → 로드 이벤트는 이미 지나감
document.addEventListener("DOMContentLoaded", init);   // 영영 안 불림

// 고친: 마운트 후 모듈 주입 + init 직접 호출
useEffect(() => { loadModule().then(m => m.init()); }, []);
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 구독 먼저·준비 핸드셰이크·캐시 재전송 | 생산자와 소비자가 같은 프로세스·앱 안 | 순서 코드·ack 프로토콜 | 준비 조건 하나를 빠뜨리면 다시 유실 | UI·창 간 이벤트, 짧은 수명 구독 |
| 1. 재연결 + 보관 스트림 | 소비자가 다운될 수 있고 그동안의 메시지가 중요 | 저장 공간(상한으로 제한) | 상한 초과 시 가장 오래된 것부터 트리밍 | 서비스 간 로그·이벤트 수집 |
| 2. 소비자 그룹 + ACK | 처리 중 크래시에도 재처리가 필요 | pending 복구·dead-letter 운영 | 결함 메시지를 ACK 안 하면 poison pill | 통계 원천처럼 유실이 곧 데이터 훼손 |
| 3. 상태 확인 후 직접 호출 | 사건이 다시 발생하지 않는 일회성 | 실행 시점 소유자에게 맞춤 | 호출 시점이 너무 이르면 대상 DOM 없음 | 프레임워크 안에 이식한 레거시 코드 |

**결론**: 같은 프로세스 안이면 순서(구독 먼저)와 준비 핸드셰이크로 충분하다(기본).\
소비자의 부재가 정상 상황(재시작·장애)에 포함되면 순서로는 못 막는다 — 보관하는 스트림(1)이 필요하고, 처리 실패까지 복구하려면 ACK(2)를 쓴다.\
일회성 사건은 "늦게 구독"을 고칠 수 없으니 사건 대신 상태를 확인한다(3).
