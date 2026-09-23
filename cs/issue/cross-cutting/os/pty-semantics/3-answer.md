# cs/issue/os/pty-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **LF는 제출이 아니다.** raw 모드 TUI는 라인 디시플린의 줄 편집을 끄고 키 입력을 바이트 그대로 받는다.\
사람이 Enter를 누르면 터미널은 **CR(0x0D)**을 보낸다 — TUI의 "제출" 키 바인딩은 CR에 걸려 있다.\
그래서 `text + "\n"`은 제출되지 않고 줄바꿈 입력(또는 무시)으로 처리돼, 주입이 **조용히 죽었다**.\
단일 행은 `text + "\r"`로 제출한다.
   > **raw 모드** — 터미널 드라이버가 줄 단위 편집·신호 문자 해석을 하지 않고 바이트를 즉시 프로그램에 넘기는 모드.

2. **같은 청크의 CR.** TUI는 입력을 `read` 청크 단위로 파싱한다.\
bracketed paste 종료 표식과 CR이 **같은 청크**에 들어오면, TUI는 CR까지 붙여넣기 본문의 일부로 해석한다.\
별도 `write`로 나눠도 지연이 0이면 커널 버퍼에서 합쳐져 같은 read에 도착할 수 있다 — 그래서 0ms는 실패, 120ms 이상은 성공이었다(실측 하한 0<t≤120ms).\
교정은 본문을 paste로 보내고, **별도 write로 지연(실측 하한의 약 2.5배인 300ms) 후 CR**을 보내는 것이다.\
추가로 본문 꼬리의 개행은 입력 버퍼를 멀티라인 상태로 만들어 CR이 제출로 동작하지 않으므로 **꼬리 개행을 제거**한다.
   > **bracketed paste** — 수신 프로그램이 `ESC[?2004h`로 켜면, 붙여넣기 텍스트를 `ESC[200~`/`ESC[201~`로 감싸 키 입력과 구분하게 하는 터미널 모드.

3. **준비 전 쓰기.** TUI가 입력 핸들러를 설치하기 전에 도착한 바이트는 **버려진다**.\
고정 지연 1.8초는 실측 준비 임계(1.8<t≤2.0초) **바로 아래**라, 바이트를 고쳐도 여전히 소실됐다 — 두 결함(LF, 지연)이 각각 단독으로 재현됐다.\
고정 지연은 기계·부하에 따라 임계가 움직이면 언제든 깨진다. 이 사건은 지연을 실측 임계 위(3초)로 올리는 임시책으로 막았고, 근본 해법인 **PTY 출력 기반 준비 감지**는 후속 과제로 남겼다.\
판정 근거도 "보냈다"가 아니라 상대의 기록(사용자 턴 레코드 수)으로 삼았다.

4. **모드 미설정 붙여넣기 = 키 입력.** bracketed paste 격리는 수신 프로그램이 모드를 **켰을 때만** 성립한다.\
선택·권한 프롬프트 화면이 모드를 켜지 않은 상태라면, 주입된 바이트는 그 화면의 키 바인딩(숫자 선택·Enter)으로 해석돼 **의도치 않은 승인**이 가능하다.\
게이트를 클릭 시점에만 검사하면, 클릭과 실제 쓰기 사이에 상태가 바뀌는 **TOCTOU**가 남는다.\
그래서 "차단 상태"를 **클릭 시점 + 소비(쓰기) 직전** 모두 검사하고, 차단 해소 구독으로 자동 재시도(영구 잠금 금지)하며, 재주입 순서(소비 → 재스캔 → 차단 확인 → 쓰기)를 순수 규칙으로 고정했다.
   > **TOCTOU** — 검사 시점(time of check)과 사용 시점(time of use) 사이에 상태가 바뀌어 검사가 무효가 되는 경쟁.

5. **canonical 모드의 무음 절단.** canonical(line) 모드 라인 디시플린은 한 줄 입력 버퍼를 **MAX_CANON(4096)** 까지만 유지한다.\
개행 없이 그보다 긴 바이트가 오면 커널이 **받아들인 뒤 버린다** — 쓰는 쪽의 `write`는 `Ok`(200KiB, 9.7ms)를 돌려주지만 상대 수신은 0이거나 4095바이트로 잘린다.\
쓰는 쪽은 상대 터미널 모드를 볼 수 없어 이것을 막을 수 없다.\
그래서 계약을 "전달했다"에서 **"큐에 넣었다 — 이 크기는 아직 먹힐 수 있다"**로 낮추고, 위험 크기(≥MAX_CANON, 개행 없음)면 연결당 1회 경고로 **명명**했다.

6. **EIO = EOF.** Linux PTY는 slave 쪽이 모두 닫히면(자식 종료) master `read`가 빈 결과(EOF) 대신 **EIO 오류**를 돌려주는 것이 일반적이다.\
EOF만 기다리는 코드는 종료를 감지하지 못하고 세션을 살아 있는 것으로 둔다(무음 실패).\
`OSError`(EIO)를 EOF로 **정규화**하되, 논블로킹의 "데이터 없음"(EAGAIN)·신호 중단(EINTR)은 따로 분기해 종료로 오인하지 않는다.\
정규화 후 종료 통지를 내보내고 세션을 dead로 표시한다.

7. **제어 터미널.** 커널은 터미널 신호(SIGWINCH·SIGINT 등)를 **제어 터미널을 가진 세션의 포그라운드 프로세스 그룹**에 보낸다.\
`setsid`(또는 새 세션 옵션)는 새 세션을 만들 뿐 제어 터미널을 붙이지 않는다.\
제어 터미널은 **세션 리더**가 `ioctl(fd, TIOCSCTTY)`로 얻는다 — 그래서 자식 쪽에서 표준 fd가 slave로 연결된 뒤 `setsid()` → `TIOCSCTTY` 순으로 호출한다.\
창 크기는 master에 `TIOCSWINSZ`를 걸면 커널이 SIGWINCH를 전달하고, 테스트는 `TIOCGWINSZ`로 커널에 적용된 값을 직접 조회했다.

## 문제 구조 (추상화 코드)

### 변형 A — 제출 바이트와 준비 시점
① 문제 코드
```ts
await sleep(1800);                                        // 준비 임계 바로 아래
pty.write(encode(text + "\n"));                           // LF = 제출 아님
// 또는
pty.write(encode("\x1b[200~" + text + "\x1b[201~" + "\r")); // CR이 같은 청크 → 본문
```
② 고친 코드
```ts
async function submitToSession(pty, text) {               // 제출 경로 단일화
  await sleep(READY_DELAY);                               // 3000ms — 실측 임계 위 (근본 해법 = 출력 기반 준비 감지, 후속)
  const body = text.replace(/\n+$/, "");                  // 꼬리 개행 제거
  if (!body.includes("\n")) { pty.write(encode(body + "\r")); return; }
  pty.write(encode("\x1b[200~" + body + "\x1b[201~"));   // 본문 = paste
  await sleep(300);                                       // 별도 write + 지연
  pty.write(encode("\r"));                                // 제출 = CR
}
```
무엇이 깨졌나: LF를 제출로 가정했고, CR이 본문과 한 청크로 합쳐졌고, 준비 전에 썼다.\
같은 구조: 두 결함(LF 미제출 + 준비 임계 미달)이 겹친 "이중 사망" 주입 — 지연×바이트 매트릭스 스모크와 옛 구현 대조군으로 각각 단독 재현.

### 변형 B — 모드 미설정 화면에 붙여넣기 (보안)
① 문제 코드
```ts
onClick(() => { if (!isBlocked(session)) inject(session, text); }); // 클릭 시점만
async function inject(s, t) { await rescan(s); s.write(paste(t)); } // 쓰기 직전 재검사 없음
```
② 고친 코드
```ts
onClick(() => tryInject(session, text));
async function tryInject(s, t) {
  consume(s); await rescan(s);
  if (isBlocked(s)) { onUnblocked(s, () => tryInject(s, t)); return; } // 소비 직전 재검사 + 자동 재시도
  s.write(paste(t));
}
```
무엇이 깨졌나: paste 모드를 켜지 않은 선택 프롬프트에서 주입 바이트가 키 입력으로 해석될 수 있었다.

### 변형 C — canonical 모드 write 성공 ≠ 전달
① 문제 코드
```rust
fn send(&self, data: &[u8]) -> io::Result<()> {
    self.master.write_all(data)            // Ok → "전달됨"으로 보고
}
```
② 고친 코드
```rust
fn send(&self, data: &[u8]) -> io::Result<bool> {   // 계약: "큐에 넣음"
    let mut q = self.queue.lock();
    q.bytes += data.len();
    q.chunks.push_back(data.to_vec());
    self.work.notify_all();
    Ok(data.len() >= MAX_CANON && !data.contains(&b'\n'))  // 위험 크기 → 호출자가 1회 경고
}
```
무엇이 깨졌나: 커널이 받아서 버리는 바이트를 "전달됨"으로 보고했다.

### 변형 D — 자식 종료 시 EIO
① 문제 코드
```python
data = os.read(master, CHUNK)
if data == b"":            # EOF만 종료로 간주 → EIO 예외로 루프가 깨지거나 종료 미감지
    on_exit()
```
② 고친 코드
```python
try:
    data = os.read(master, CHUNK)
except (BlockingIOError, InterruptedError):
    return                 # 데이터 없음/신호 중단 ≠ 종료
except OSError:            # EIO — slave 측 닫힘
    data = b""
if data == b"":
    broadcast_exit(); mark_dead()
```
무엇이 깨졌나: PTY 종료 신호가 EOF가 아니라 EIO로 왔다.

### 변형 E — 제어 터미널 설정
① 문제 코드
```python
Popen(cmd, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)  # 세션만, ctty 없음
```
② 고친 코드
```python
def set_controlling_tty():       # 표준 fd가 slave로 dup된 뒤 자식에서 호출
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
Popen(cmd, stdin=slave, stdout=slave, stderr=slave, preexec_fn=set_controlling_tty)
```
무엇이 깨졌나: 제어 터미널이 없으면 터미널 신호(창 크기 변경)가 TUI에 가지 않는다(예방 설계 — 관찰된 사고가 아니라 설계 근거).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
