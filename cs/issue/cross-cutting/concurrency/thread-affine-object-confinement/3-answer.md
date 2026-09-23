# cs/issue/concurrency/thread-affine-object-confinement — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **thread-affine 객체.** 특정 스레드(또는 이벤트 루프) 안에서만 올바르게 동작하도록 만들어진 객체다.\
   이런 연결은 보통 자기 I/O 구동 태스크와 상태를 `Rc`·`RefCell`처럼 스레드 간 이동을 전제하지 않는 타입으로 공유하고, 그런 `!Send` future는 `spawn`이 아니라 `spawn_local`로 현재 스레드의 로컬 실행기에만 올릴 수 있다 — 공유 상태가 `!Send`이므로 객체 타입도 `!Send`가 되어 다른 스레드로 옮길 수 없다(`spawn_local` 호출 자체가 타입을 바꾸는 게 아니라, `!Send` 상태 공유가 원인이다).
   > **`Send` / `!Send`** — Rust에서 값을 다른 스레드로 옮겨도 안전하면 `Send`, 아니면 `!Send`. 컴파일러가 스레드 경계에서 검사한다.

2. **예측.** 요청 핸들러가 멀티스레드 런타임에서 임의 스레드로 옮겨 다니며 실행되면 핸들러 future가 `Send`여야 하므로(공유 상태는 `Sync`도), `!Send` 연결을 `.await` 너머로 붙잡는 순간 **컴파일이 Send 위반으로 막힌다**.\
   억지로 `LocalSet` 밖(예: 멀티스레드 런타임의 일반 태스크)에서 tokio `spawn_local`을 호출하면 **런타임 패닉**이 난다(tokio 기준 — 런타임·버전마다 다름).

3. **actor 패턴.** 전용 OS 스레드 하나를 띄워 그 안에서 단일 스레드 런타임과 `LocalSet`을 돌리고, 연결 객체는 **그 스레드 안에서만** 생성·사용한다(갇히는 것).\
   외부에는 `Send` 가능한 **명령 채널 송신 핸들**만 준다(노출되는 것). 이벤트는 반대 방향 채널로 내보내고, 별도 relay 스레드가 UI로 전달한다.\
   객체의 모든 조작이 한 스레드에서 순서대로 일어나므로 동기화 없이도 경쟁이 없다.
   > **actor** — 상태를 한 실행 주체 안에 가두고 메시지로만 조작하게 하는 동시성 모델.

4. **asyncio 교차 루프.** asyncio 객체(`Queue`·Future 등)는 자기 루프 스레드에서만 조작된다고 가정하고 락 없이 구현돼 있다.\
   다른 루프의 콜백에서 `put_nowait`을 직접 부르면 대기 중인 소비자를 깨우는 처리가 엉뚱한 루프에서 일어나 불안전하다.\
   합법 진입점은 대상 루프의 `loop.call_soon_threadsafe(fn, ...)` — 그 루프가 자기 차례에 `fn`을 실행하게 예약한다(코루틴을 실행시키려면 `asyncio.run_coroutine_threadsafe(coro, loop)`). 그래서 구독 시점에 큐와 함께 **그 큐의 루프**를 저장해 둔다.

5. **응답 경로.** 호출자가 결과를 기다려야 하면 요청에 **oneshot 송신단**을 실어 보내고, actor가 처리 후 그 oneshot으로 답한다(호출 측은 수신단에서 park).\
   채널 종류도 중요하다 — 비동기 컨텍스트가 아닌 곳에서 보내야 한다면 **동기 send가 되는 채널**(예: unbounded 송신, 표준 mpsc)을 골라야 호출 측이 막히거나 런타임을 요구하지 않는다.

6. **연결.** 둘 다 "공유 가변 상태에 주인을 하나만 둔다"는 생각이다 — lost update 방지가 저장 단위의 단일 writer라면, 이건 객체 조작의 단일 스레드다.\
   객체가 한 소유자에 갇혀 있으니, 테스트도 `current_thread` 런타임 + `LocalSet` + 인메모리 양방향 파이프로 **결정론적으로** 돌릴 수 있다.

## 문제 구조 (추상화 코드)

### 변형 A — `!Send` 연결을 멀티스레드 호출자가 직접 사용

```rust
// 문제: 임의 스레드의 핸들러가 !Send 연결을 들고 다님
struct State { conn: Connection }            // Connection: !Send (내부 spawn_local)
async fn handle(state: &State, req: Req) { state.conn.request(req).await; } // Send 위반
```

```rust
// 고침: 전용 스레드 actor + 채널 핸들만 노출
struct Host { commands: UnboundedSender<Cmd>, _thread: JoinHandle<()> }
fn start() -> Host {
    let (tx, rx) = unbounded_channel();
    let t = std::thread::spawn(move || {
        let rt = Builder::new_current_thread().enable_all().build().unwrap();
        LocalSet::new().block_on(&rt, host_main(rx)); // Connection 은 여기서만 생성·사용
    });
    Host { commands: tx, _thread: t }
}
// 응답이 필요하면 Cmd 에 oneshot::Sender 를 실어 보냄
```
무엇이 깨졌나: 핸들러가 임의 스레드에서 실행되는 구조와 로컬 태스크로 I/O를 돌리는 연결이 충돌했다(설계 제약 단계에서 확인).

### 변형 B — 다른 이벤트 루프의 asyncio 큐를 직접 조작

```python
# 문제: reader 콜백(서버 루프)이 클라이언트 루프의 큐를 직접 조작
def _broadcast(self, data):
    for q in self.clients:
        q.put_nowait(data)
```

```python
# 고침: 구독 시 큐의 루프를 함께 저장, 그 루프에 threadsafe 예약
async def attach(self, q):
    self.clients[q] = asyncio.get_running_loop()

def _broadcast(self, data):
    for q, loop in self.clients.items():
        loop.call_soon_threadsafe(_offer, q, data)
```
무엇이 깨졌나: 테스트 클라이언트가 연결마다 별도 이벤트 루프를 쓸 수 있어, 서버 루프의 콜백이 다른 루프의 큐를 건드리는 구조가 됐다(위험 원리 확인 단계, 실제 오동작 관찰 기록은 없음).\
선택하지 않은 방법: 교차 루프 reader 해제까지 보장하는 것 — "단일 루프 전제"를 문서에 명시하는 것으로 대신했다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
