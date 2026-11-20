# issue/cross-cutting/concurrency/lost-wakeup-on-flag-clear — 정답

태그: `race-condition` · `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **신호가 ③의 `clear()`에 지워지고, 대기자는 아무도 다시 깨우지 않는 ④로 들어간다.**\
   정리 쪽은 `handing_off = True`를 세우고 모든 대기자의 플래그를 `set()`한다 — 대기자가 ②에 멈춰 있으면 그 `set()`은 아직 아무도 기다리지 않는 플래그에 기록될 뿐이다.\
   대기자가 이어지면 바로 ③에서 `clear()`로 그 기록을 지우고, ④에서 플래그를 기다린다 — 그런데 깨울 일은 이미 끝났으므로 다음 깨움은 오지 않는다.\
   ①의 조건 확인은 ② **앞**에서 끝났으므로, 그 사이에 바뀐 조건을 이 회차는 보지 못한다.
   > **lost wakeup(깨움 유실)** — 대기자가 "확인"과 "잠들기" 사이에 온 깨움 신호를 놓쳐, 이미 참이 된 조건을 모른 채 잠드는 결함.

2. **`yield`는 소비자가 다음 값을 달라고 할 때까지 멈춘다 — 그 사이 이벤트 루프는 다른 코루틴을 돌린다.**\
   asyncio는 선점하지 않지만, 코루틴이 스스로 멈추는 지점(`await`, 비동기 제너레이터의 `yield`)마다 다른 작업이 끼어든다.\
   이 대기자는 HTTP 스트리밍 응답의 이벤트 생산자였다 — `yield`한 이벤트를 응답 쪽이 내보낸 뒤에야 다음 값을 요청하므로, 그동안 정리 요청 처리기가 돌아 `set()`을 실행할 수 있었다.

3. **하트비트(시간 제한 재확인) 덕분이다 — 대가는 최대 하트비트 한 주기의 지연이다.**\
   ④의 대기에는 상한(`timeout = min(heartbeat, 남은 시간)`)이 있어, 운영 설정 10초가 지나면 루프가 ①로 돌아가 조건을 다시 보고 그제야 넘겨졌다.\
   "결국 넘겨졌다"만 보면 결함이 없어 보이지만, 넘기기는 교체 중인 서버의 대기자를 새 서버로 빨리 보내는 기능이다 — 그 기능의 핵심 속성(곧바로)이 하트비트 주기만큼 무너진다.\
   또한 하트비트는 원래 "프록시 무응답 시한을 넘기지 않으려는 재전송"이지 깨움 장치가 아니다 — 다른 목적의 상한에 정확성이 기대고 있었다는 것이 문제다.

4. **지운 다음에 봐야, 본 뒤에 온 신호가 플래그에 남는다.**\
   clear → 확인 → 대기 순서면: 확인 전에 온 신호는 확인이 조건으로 잡고, 확인 뒤에 온 신호는 플래그에 남아 대기가 곧바로 깬다 — 어느 쪽이든 놓치지 않는다.\
   확인 → (멈춤) → clear 순서면: 확인 뒤·clear 전에 온 신호는 조건에도 안 잡히고(이미 봤다) 플래그에서도 지워진다.\
   조건 변수의 관용구 `while not 조건: wait()`도 같은 원리다 — 잠들기 직전에 **조건을 다시 보고**, 잠들고 깨는 것은 "다시 볼 때가 됐다"는 신호로만 쓴다(일반 원리).
   > **술어 루프(predicate loop)** — 깨어남을 결과로 믿지 않고, 깰 때마다 조건(술어)을 다시 평가하는 대기 방식. 가짜 깨움·깨움 유실을 함께 막는다.

5. **하트비트 10초가 잃어버린 깨움을 10초 지연으로 바꿨고, 테스트는 "결국 retry를 받았나"만 봤다.**\
   테스트는 대기자들이 `retry`를 받고 순번대로 나가는지를 단언했다 — 결과는 맞았고, 시간만 길었다(테스트 전체 약 24초).\
   교정: 테스트의 하트비트를 60초로 늘리고 시나리오마다 시간 상한 3초(`wait_for`)를 걸었다 — 이제 깨움이 아니라 하트비트로 넘겨지면 상한에서 실패한다.\
   그리고 **고친 줄을 빼면 그 테스트가 실패하는지** 확인했다(변이 확인) — 고친 뒤 테스트 전체는 약 5초가 됐다.
   > **변이 확인(mutation check)** — 방어 코드를 일부러 지우거나 되돌려, 그 결함을 겨냥한 테스트가 실제로 빨개지는지 보는 것. 빨개지지 않으면 그 테스트는 증거가 아니다.

6. **첫 이벤트만 받고 다음 값을 요청하지 않은 채 신호를 보낸다.**\
   제너레이터에서 첫 `queued`를 꺼낸 뒤 다음 `__anext__()`를 부르지 않으면, 대기자는 `yield`에 멈춘 상태(②)에 머문다 — 그때 정리를 시작하고, 나머지 이벤트를 시간 상한 안에 모은다.\
   반대로 "다음 이벤트를 기다리는 상태(④ 안)"까지 들여보낸 대기자는 `set()`을 대기 중에 받으므로 곧바로 깬다 — 결함이 있는 창(②~③)을 지나지 않아 통과한다.\
   두 상태를 각각 만드는 보조 함수를 따로 두고, 기존 시나리오는 "대기 지점 안" 상태로, 새 시나리오는 "이벤트 사이" 상태로 시험했다.

7. **둘 다 "보관 없는 신호를 늦게 보면 사라진다"이다.**\
   플래그는 값 하나짜리 상태라, 그 위에 누가 `clear()`하면 이전 `set()`은 흔적이 없다 — 보관·재생이 없는 이벤트 채널에서 구독 전에 일어난 사건이 사라지는 것과 같다([event-before-subscriber-loss](../../reliability/event-before-subscriber-loss/)).\
   매 tick 덮어쓰기로 "본 적 있음"이 지워지는 edge 판정 결함도 같은 모양이다([edge-detection-on-raw-signals](../../reliability/edge-detection-on-raw-signals/)).\
   공통 처방은 "신호를 결과로 믿지 말고, 깰 때·확정할 때 **원천 상태(조건)**를 다시 읽는다"이다.

## 문제 구조 (추상화 코드)

### 변형 A — 확인과 clear 사이의 양보 지점에서 깨움 유실

① 문제 코드
```python
class WaitQueue:
    def begin_handoff(self):
        self.handing_off = True
        for flag in self.flags:            # 기다리는 사람들을 깨운다
            flag.set()

async def queue_wait_events(queue, flag):          # 비동기 제너레이터 — 응답 스트림의 이벤트 생산자
    while True:
        if queue.handing_off and queue.is_first(flag):
            yield {"type": "retry"}        # 새 서버로 넘긴다
            return
        yield {"type": "queued", "position": queue.position(flag)}   # ← 소비자가 다음을 요청할 때까지 멈춤
        flag.clear()                                                  # ← 멈춘 사이 온 set()을 지움
        await wait_first(flag.wait(), slot_acquired,
                         timeout=queue.heartbeat)                     # 아무도 다시 안 깨움 → 하트비트까지 잠
```
② 고친 코드
```python
async def queue_wait_events(queue, flag):
    while True:
        if queue.handing_off and queue.is_first(flag):
            yield {"type": "retry"}
            return
        yield {"type": "queued", "position": queue.position(flag)}
        flag.clear()
        if queue.handing_off:                 # clear 뒤에 조건을 다시 본다 — 멈춘 사이 시작됐을 수 있다
            if queue.is_first(flag):
                continue                   # 기다리러 가지 않고 곧바로 위에서 처리
            # 맨 앞이 아니면: 앞사람이 나갈 때 그 쪽이 다시 깨운다(대기 중이므로 놓치지 않음)
        await wait_first(flag.wait(), slot_acquired, timeout=queue.heartbeat)
```
무엇이 깨졌나: 조건 확인과 플래그 clear 사이에 양보 지점(`yield`)이 있어, 그 사이 온 깨움이 지워졌다 — 하트비트 상한이 지연으로 덮었다.

### 변형 B — 시간 제한 재확인이 결함을 가린 테스트

① 문제 코드
```python
queue = WaitQueue(slots=1, heartbeat=10.0)       # 재확인 주기 10초
waiter = open_stream(queue)
assert await waiter.__anext__() == {"type": "queued", "position": 1}
queue.begin_handoff()
rest = await read_all(waiter)                     # 시간 상한 없음 — 10초 뒤 재확인으로 결국 retry
assert rest == [{"type": "retry"}]               # 결과만 단언 → 초록
```
② 고친 코드
```python
queue = WaitQueue(slots=1, heartbeat=60.0)       # 재확인으로는 상한 안에 못 오게
waiter = open_stream(queue)
assert await waiter.__anext__() == {"type": "queued", "position": 1}   # yield에 멈춘 상태 그대로
queue.begin_handoff()
rest = await asyncio.wait_for(read_all(waiter), 3.0)   # 깨움으로만 통과 가능한 시간 상한
assert rest == [{"type": "retry"}]
# 검증: 변형 A ②의 재확인 줄을 지우면 이 테스트가 시간 상한에서 실패한다
```
무엇이 깨졌나: 결과는 맞고 시간만 틀린 결함을, 시간을 재지 않는 테스트가 통과시켰다.

## 검증 기록
- 2026-11-20: 사건 기록·수정 diff 대조·추상화(Claude 초안) — 결함은 구현 리뷰에서 지적, 수정 후 변이 확인(고친 줄 제거 시 실패)·테스트 전체 24초 → 5초 기록. 조건 변수 술어 루프 대응은 일반 원리.

## 관련 카드
- [green-masking](../../testing/green-masking/) — 초록불은 테스트가 실패할 수 있었을 때만 증거다(변형 B와 같은 처방: 변이 확인).
- [event-before-subscriber-loss](../../reliability/event-before-subscriber-loss/) — 보관 없는 신호는 받을 준비 전에 오면 사라진다.
- [edge-detection-on-raw-signals](../../reliability/edge-detection-on-raw-signals/) — 덮어쓰기로 "본 적 있음"이 지워지는 같은 모양.
- [single-slot-handoff-loss](../single-slot-handoff-loss/) — 용량 1짜리 신호 자리가 덮여 조용히 유실되는 경우.
