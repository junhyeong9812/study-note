# cs/issue/reliability/debounce-trailing-contract — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **trailing 계약.** trailing-edge 디바운스는 "변경이 몰리는 동안은 미루되, **마지막 변경 뒤에는 반드시 한 번 실행**한다"가 계약이다.\
마지막 실행은 변경이 **멎은 뒤**에 일어나야 하므로, 새 변경이 아니라 **시간(매 틱·타이머)**이 그 실행을 일으켜야 한다.\
변경 이벤트에 실행을 매달면 변경이 멎는 순간 실행 계기도 사라진다.
   > **trailing edge** — 연속 이벤트 묶음의 끝 쪽. trailing 디바운스는 묶음이 끝난 뒤 한 번 실행한다.

2. **게이트 뒤의 플러시.** 변화 없는 틱은 `continue`로 루프 앞으로 돌아가므로 그 뒤의 플러시에 **영영 도달하지 못한다**.\
마지막 턴이 끝난 뒤로는 변화가 없으니 보류된 마지막 저장이 착지하지 않고, 정상 종료할 때마다 마지막 턴 스냅샷이 빠진다 — 오류는 없다.\
교정: 틱 순서를 계약으로 고정해 플러시를 fp 게이트·poll **앞**(매 틱 실행)으로 옮긴다.

3. **실패 시 dirty와 last_save.** 저장 실패에도 `dirty = false`로 내리면 "저장할 변경이 있다"는 기억이 사라져 **재시도 기회를 잃는다** — 일시 디스크 오류가 변경을 영구 누락시킨다.\
반대로 실패 때 `last_save`를 갱신하지 않으면 디바운스 간격 조건이 계속 참이라 매 틱 저장을 재시도하는 **핫루프**가 된다.\
교정: `last_save`는 성공·실패와 무관하게 갱신(재시도 간격 유지), `dirty`는 **성공했을 때만** 내린다.

4. **stop과 플러시의 경쟁.** 닫기 → 스냅샷 삭제 뒤에 루프가 한 틱 더 돌아 플러시하면 **방금 지운 스냅샷을 되살린다**.\
sleep 직후와 저장 직전에 `stop`을 재검사하면 경쟁 창이 "재검사 ~ 저장 syscall" 한 구간으로 줄어든다.\
완전히 닫으려면 삭제와 저장이 **같은 락**을 공유해야 하는데, 이는 새 전역 상태와 교착 표면을 만든다 — 원문은 남은 창(syscall 1개)을 수용하고 기록하는 쪽을 택했다.
   > **TOCTOU** — 검사 시점과 사용 시점 사이에 상태가 바뀌는 경쟁.

5. **보류가 만드는 순서.** 즉시 전송만 있으면 이벤트는 발생 순서대로 나간다.\
보류 전송은 "발생"과 "전송" 사이에 시간을 끼워 넣으므로, 그 사이에 **다른 경로로 즉시 나가는 이벤트**(프로세스 종료 → `closed`)가 보류분을 앞지른다.\
결과는 두 가지다 — 보류분이 종료와 함께 버려지면 마지막 답변 **유실**, 나중에 flush되면 `closed` 뒤에 `timeline`이 도착하는 **역순**.\
종결 경로마다 flush·순서 보정을 따로 붙여야 하므로 결함 표면이 증식한다.
   > **held-back 전송** — 이벤트를 곧바로 보내지 않고 잠시 붙잡아 두었다가 모아서 보내는 방식(스로틀·디바운스).

6. **점 패치 vs 제거.** 1차: 자연 종료 시 trailing 유실 → 보류분 강제 flush → 2차: `closed`→`timeline` 역순 경합 등 → 무조건 최종 emit + 수신 쪽 종결 우선 → 3차: 역순 시 늦은 내용 미반영·종료 flush의 활성 서브스트림 누락이 또 나옴.\
같은 결함 계열을 세 번 고쳐도 새 코너가 나오는 것은 **토대(보류 상태) 자체가 틀렸다**는 신호로 보고, 디바운스를 통째 제거해 검증된 이전 구조(변화 시 즉시 emit)로 되돌렸다.\
대가는 트래픽 절감의 후퇴(−92% → −80%, payload 절감만 유지)이며, "순서 안전과 즉시 라이브의 값어치"로 명시적으로 수용했다.

7. **종결 우선.** 즉시 emit이어도 `closed`와 `timeline`이 서로 다른 채널이면 도착 순서는 보장되지 않는다.\
수신 쪽 규칙: 닫힌 id를 기억해 **같은 id의 늦게 도착한 이벤트는 최종 내용만 반영하고 "종료" 표시를 되돌리지 않는다**, 새 id(재개)만 다시 연다.\
송신 쪽 순서 보장은 모든 종결 경로에 규칙을 심어야 하지만, 수신 쪽 규칙은 **한 곳**에서 어떤 도착 순서든 같은 최종 상태로 수렴시킨다 — 순서 의존 자체를 없앤다.

## 문제 구조 (추상화 코드)

### 변형 A — trailing 플러시가 변화 게이트 뒤에 있음
① 문제 코드
```rust
while !stop.load(Relaxed) {
    sleep(TICK);
    tail.poll()?;                                    // 오류 틱이면 아래 플러시도 건너뜀
    let fp = fingerprint(&state);
    if fp == last_fp { continue; }                   // 변화 없는 틱은 여기서 끝
    emit(&state); last_fp = fp; dirty = true;
    if dirty && last_save.elapsed() >= DEBOUNCE {    // ✗ 변화가 멎으면 도달 불가
        if save(&state).is_ok() {} ; dirty = false;  // ✗ 실패해도 dirty 해제
        last_save = now();
    }
}
```
② 고친 코드
```rust
while !stop.load(Relaxed) {
    sleep(TICK);
    if stop.load(Relaxed) { break; }                             // ⓐ 닫힌 세션이 한 틱 더 돌지 않게
    if dirty && last_save.elapsed() >= DEBOUNCE {                // ⓑ 매 틱 — 게이트·poll 앞
        last_save = now();                                       //    성공·실패 무관 (핫루프 방지)
        if !stop.load(Relaxed) && save(&state).is_ok() { dirty = false; }   // 성공 시에만 해제
    }
    let _ = tail.poll();                                         // ⓒ
    let fp = fingerprint(&state);
    if fp == last_fp { continue; }                               // ⓕ
    emit(&state); last_fp = fp; dirty = true;
}
```
무엇이 깨졌나: "변화가 멎은 뒤" 와야 할 실행을 "변화가 있을 때만" 도는 경로에 두었다.\
남은 창: 저장 직전 재검사 ~ 저장 syscall 사이의 삭제 경쟁(락 공유 비용 대비 수용).

### 변형 B — 보류 emit이 종결 이벤트와 순서를 뒤집음
① 문제 코드
```rust
// 폴 스레드
if fp != last_fp {
    pending = Some(build(&state));
    if last_emit.elapsed() >= EMIT_MIN_INTERVAL { emit_timeline(pending.take()); last_emit = now(); }
}
// 종료 감지 경로 (다른 채널)
on_process_exit(|| emit_closed(id));      // 보류분보다 먼저 나감 → 유실 또는 역순
```
② 고친 코드
```rust
// 송신: 보류 개념 제거 — 변화 시 즉시
if fp != last_fp { emit_timeline(build(&state)); last_fp = fp; }
```
```ts
// 수신: 종결 우선 (도착 순서 무관하게 같은 최종 상태)
onClosed(id => { closedIds.add(id); markEnded(id) })
onTimeline(ev => {
  if (closedIds.has(ev.id)) { replaceContent(ev); return }   // 내용만 반영, 종료 표시 유지
  render(ev)                                                  // 새 id(재개)만 다시 연다
})
```
무엇이 깨졌나: 보류 상태가 생기면서 종결 이벤트와의 순서가 새 불변식이 됐고, 종결 경로마다 보정이 필요해 결함이 반복됐다.\
거쳐 간 시도: 종료 시 보류분 강제 flush(수동/자연 종료 구분 플래그), 자연 종료면 무조건 최종 poll+emit — 매 라운드 리뷰에서 같은 순서 표면의 새 코너(역순·서브스트림 누락)가 나왔다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
