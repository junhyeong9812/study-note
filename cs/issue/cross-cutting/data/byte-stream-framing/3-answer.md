# cs/issue/data/byte-stream-framing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **read 경계 ≠ 레코드 경계.** read는 그 순간 파일에 있는 바이트까지 돌려줄 뿐, 쓰는 쪽이 한 줄을 다 썼는지 모른다. 그래서 한 read가 **줄 중간**에서 끝날 수 있다.\
   조각을 파싱하면 실패해 그 레코드가 **통째로 사라지거나**, 다음 read에서 나머지 절반이 또 다른 깨진 조각이 된다.\
   고침: 오프셋 이후 새 바이트를 버퍼에 이어 붙이고, `\n`까지 완성된 줄만 꺼내 디코드하며, 미완성 꼬리는 버퍼에 보관한다. 이러면 정확성이 폴링 주기나 쓰는 쪽의 flush 크기와 무관해지고 지연에만 영향을 준다.
   > **프레이밍** — 바이트 스트림에서 한 메시지(프레임)의 시작과 끝을 정하는 규칙(개행 구분, 길이 접두 등).

2. **줄 경계 = 문자 경계.** UTF-8에서 멀티바이트 문자의 뒤 바이트(continuation)는 모두 `10xxxxxx` 형태라 `0x0A`(`00001010`)가 될 수 없다.\
   따라서 (유효한 UTF-8이라면) `\n` 바이트 위치에서 자르면 **절대 문자 중간이 아니다** — 완성된 줄 단위로 디코드하면 부분 UTF-8 문제가 자동으로 사라진다.

3. **청크 단위 디코드.** PTY 출력 청크는 임의 크기라 한글(3바이트) 같은 문자가 두 청크에 걸칠 수 있다. 청크마다 text로 디코드하면 경계의 문자가 깨진다.\
   디코딩은 **스트림 상태를 가진 쪽**이 해야 한다 — 서버는 바이트 그대로 **binary 프레임**으로 보내고, 수신 측 터미널 에뮬레이터의 스트리밍 UTF-8 디코더에 넘긴다(미완성 바이트를 다음 청크까지 들고 있는다).

4. **창 첫 줄 폐기와 truncate.** 창 시작이 줄 중간이면 첫 줄은 잘린 줄이라 버리는 게 맞지만, 창 시작이 **정확히 줄 시작**(직전 바이트가 `\n`)이면 첫 줄은 온전하다 — "항상 버림"은 이 경우 멀쩡한 줄을 잃는다. 창 직전 바이트를 확인해 보정한다.\
   tail 대상이 truncate·재생성되면 **파일 길이 < 저장된 오프셋**이 되므로 이를 감지해 오프셋과 버퍼를 리셋한다(같거나 더 긴 길이로 교체되는 경우는 이 검사로 못 잡는다 — append-only 전제로 비해당이라고 한계를 문서화).

5. **중간 드롭 vs 앞 드롭.** 터미널 바이트 스트림은 이스케이프 시퀀스로 상태가 바뀌는 **상태 기계**다. 중간을 지우면 `ESC [ 3` 뒤가 사라지는 식으로 시퀀스가 잘려, 남은 접두(`ESC [ 3`)가 **뒤에 이어 붙은 무관한 바이트를 자기 인자로 삼키고**, 사라진 구간의 상태 변경(화면 모드·색 등)도 빠져 **이후 해석이 오염**될 수 있다(무음 손상 — 끝나지 않은 OSC 시퀀스처럼 종결자를 만날 때까지 출력을 삼키는 경우도 있다).\
   앞에서부터 드롭하면 잘리는 것은 가장 오래된 부분이고, 앞에 붙을 접두가 없으므로 선두의 잘린 시퀀스 잔여는 기껏해야 첫머리 몇 글자 깨짐·이전 상태 유실로 국한된다(수신기가 흡수하는 수준의 국소 손상) — "스크롤백 보존"의 의미를 "최근 raw replay"로 명시적으로 좁혀 이를 계약으로 삼았다.\
   절단본을 디스크 스냅샷에 저장하면 손상이 **영속화**되어 다시 열어도 복구되지 않는다.

6. **동기 reset과 비동기 write 큐.** `write()`는 큐에 넣고 나중에 처리되지만 `reset()`은 즉시 실행된다. "이전 도장분 write → reset → 재도장" 순서로 호출해도, reset이 큐에 남은 이전 도장분보다 **먼저** 실행돼 순서가 뒤바뀐다.\
   초기화도 제어 시퀀스(`ESC c`, 전체 초기화)로 만들어 **같은 write 큐**에 넣으면 FIFO가 보장된다.

## 문제 구조 (추상화 코드)

### 변형 A — 라이브로 쓰이는 파일의 증분 tail

```rust
// 문제: read 한 덩어리를 그대로 줄로 쪼개 파싱
let chunk = read_from(offset); offset += chunk.len();
for line in String::from_utf8_lossy(&chunk).lines() { parse(line); } // 마지막 조각 = 깨진 레코드

// 고침: 완성된 줄만 디코드, 꼬리는 보관, truncate 감지
struct Tail { offset: u64, buf: Vec<u8> }
fn poll(&mut self, path: &Path) -> Vec<String> {
    let len = match metadata(path) { Ok(m) => m.len(), Err(_) => return vec![] }; // 없음 = 빈 결과
    if len < self.offset { self.offset = 0; self.buf.clear(); }                     // truncate/재생성
    self.buf.extend(read_range(path, self.offset, len)); self.offset = len;
    let (mut out, mut start) = (vec![], 0);
    for i in 0..self.buf.len() {
        if self.buf[i] == b'\n' { out.push(String::from_utf8_lossy(&self.buf[start..i]).into_owned()); start = i + 1; }
    }
    self.buf.drain(..start);
    out
}
```
무엇이 깨졌나(설계로 방어한 위험): 쓰기 도중 읽힌 조각을 파싱하면 레코드가 사라지고, 줄 끝에서 쪼개진 멀티바이트 문자가 깨진다.

### 변형 B — 파일 끝 창의 첫 줄 처리

```rust
// 문제: 창 첫 줄은 항상 잘렸다고 가정
let text = read_range(path, len - WINDOW, len);
let lines = text.split('\n').skip(1);                  // 창이 줄 시작과 일치하면 온전한 줄 폐기

// 고침: 창 직전 바이트가 개행이면 첫 줄 보존
let prev_is_nl = start == 0 || read_byte(path, start - 1) == b'\n';
let lines = text.split('\n').skip(if prev_is_nl { 0 } else { 1 });
```
무엇이 깨졌나: 창 경계가 줄 시작과 정확히 겹칠 때 온전한 첫 줄이 사라졌다(보정 + 테스트로 고정 — 기록은 "경계 보정"까지만 있어, 위 직전 바이트 검사 코드는 원리 설명용 재구성).

### 변형 C — 청크 단위 UTF-8 디코드

```python
# 문제: 서버가 청크마다 text 로 디코드해 전송
await ws.send_text(chunk.decode("utf-8", errors="replace"))   # 경계의 멀티바이트 문자 깨짐

# 고침: 바이트 그대로 binary 프레임, 디코딩은 수신 측 스트리밍 디코더에
await ws.send_bytes(chunk)
```
```ts
ws.binaryType = "arraybuffer";
ws.onmessage = (e) => term.write(new Uint8Array(e.data));
```
무엇이 깨졌나(예방 설계): 한글처럼 멀티바이트 문자가 청크 사이에 걸치는 경우를 서버가 보장해야 하는 구조였다.

### 변형 D — 상한 버퍼의 절단 위치와 재동기

```rust
// 고침(서버 스크롤백): raw 바이트 링버퍼, 상한 초과분은 앞에서부터 드롭
fn push(&mut self, data: &[u8]) {
    self.buf.extend(data);
    while self.buf.len() > self.cap { self.buf.pop_front(); }   // 선두만 잘림
}
```

```ts
// 문제(클라 pending): 상한 드롭이 스냅샷 이후 도착분(스트림 중간)을 지움, 큰 단일 청크엔 상한 미적용
pending.push(chunk); while (total(pending) > CAP) pending.shift();

// 고침: 드롭 여부를 신호로 반환 → drain 직전 재스냅샷 + 초기화 후 재도장
const dropped = pushCapped(pending, chunk);
if (dropped) {
  const snap = await getSnapshot(id);               // (bytes, lastSeq) 원자 반환 전제
  term.write("\x1bc");            // 초기화도 같은 write 큐로 (동기 reset() 금지)
  term.write(snap.bytes);
  const after = pending.filter(p => p.seq > snap.lastSeq);  // await 동안 도착한 스냅샷 이후분은 보존
  pending.length = 0;             // 매 회 pending 비움 + 스냅샷 완전 대체
  after.forEach(p => term.write(p.bytes));
}
// 지속적인 홍수에는 갭 대신 스냅샷 폴링으로 강등
```
무엇이 깨졌나: 패널 준비 전 버퍼 상한 드롭이 스트림 중간을 잘라 이스케이프 시퀀스가 깨졌고(무음 손상), 동기 reset이 큐의 이전 도장분보다 먼저 실행돼 순서가 뒤바뀌었으며, 반복 상한(10회) 직후 재드롭 때 갭이 남았다.\
같은 구조: 절단된 버퍼가 디스크 스냅샷으로 저장돼, 다시 열어도 절단이 고정됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
