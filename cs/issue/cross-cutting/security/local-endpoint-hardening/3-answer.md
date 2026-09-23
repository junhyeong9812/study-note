# cs/issue/security/local-endpoint-hardening — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **바인드 주소는 "어느 네트워크 인터페이스로 온 접속을 받나"만 정한다.** 같은 호스트의 다른 프로세스는 루프백으로 접속하므로 바인드 조건을 만족한다.\
   브라우저도 같은 호스트의 프로세스다 — 사용자가 연 임의 웹페이지의 스크립트가 `ws://127.0.0.1:port`로 연결을 열면, 요청은 루프백에서 온다.\
   그래서 로컬 끝점도 "누가 보냈나(인증)", "어느 페이지가 시켰나(Origin)", "형식이 맞나(입력 검증)", "얼마나 버티나(자원 상한)"를 스스로 확인해야 한다.

2. **프로세스 목록에서 읽는다.** 명령행 인자는 `/proc/<pid>/cmdline`으로 노출되고 `ps`로 다른 사용자도 볼 수 있다.\
   토큰은 권한 0600 파일에 쓰고, 파일 **경로**만 env로 넘겨 요청 시 파일에서 읽어 싣는다(`curl -H @파일` 형태 — 스모크로 실증).\
   세션별 토큰을 발급해 "토큰 → 세션 id" 매핑과 요청 본문의 세션 id를 대조하면, 한 세션이 다른 세션을 사칭하는 위조도 403으로 막힌다.
   > **/proc/&lt;pid&gt;/cmdline** — 리눅스에서 프로세스의 명령행 인자를 노출하는 파일. 기본 설정(`/proc`의 `hidepid` 옵션 미사용)에서는 다른 사용자도 읽을 수 있다. 반면 `/proc/<pid>/environ`은 소유자(및 특권 프로세스)만 읽을 수 있다.

3. **WebSocket 핸드셰이크에는 CORS가 적용되지 않는다.** CORS는 브라우저가 "응답을 스크립트에 보여줘도 되나"를 서버에 묻는 장치이고, 서버가 `Content-Type: application/json`을 강제한다면 교차 출처 JSON POST는 preflight 대상이라 막힌다(simple request로 보낼 수 있는 `text/plain` 본문까지 받아 주면 preflight 없이 도달하므로, 이 방어는 서버의 Content-Type 강제가 전제다) — 그래서 CORS 미들웨어를 "깔지 않은 것"이 오히려 방어가 된다.\
   WebSocket은 연결이 성립하면 양방향 통신이 바로 가능하므로, 셸 권한을 가진 로컬 WebSocket이면 임의 페이지가 셸에 도달한다.\
   서버가 accept **전에** `Origin` 헤더를 허용목록과 대조하고, 불일치면 즉시 닫는다.\
   `Origin`이 없는 연결은 브라우저가 아니다(브라우저는 WebSocket 핸드셰이크에 항상 붙인다). **단일 사용자 호스트를 전제하면** 비브라우저 클라이언트는 이미 그 사용자 권한으로 코드를 실행 중인 주체라 이 위협 모델에서는 통과시켜도 된다 — 토큰 인증은 과설계로 판단해 선택하지 않았다.\
   다중 사용자 호스트라면 다른 사용자의 프로세스도 루프백으로 접속할 수 있으므로 토큰 인증이나 유닉스 소켓 파일 권한(0600) 같은 별도 장치가 필요하다.
   > **Origin 헤더** — 요청을 일으킨 페이지의 스킴·호스트·포트. 브라우저가 붙이며 페이지 스크립트는 바꿀 수 없다. 단 비브라우저 클라이언트는 임의 값을 넣을 수 있으므로, Origin 검사는 "브라우저 페이지" 위협만 막는다.

4. **워커 하나가 무기한 점유된다.** 블로킹 서버에서 요청 전체를 읽을 때까지 기다리면, 한 바이트씩 천천히 보내는 클라이언트가 그 워커를 계속 붙잡는다(slowloris). 동시 연결 상한이 없으면 이런 연결을 늘려 전체를 세운다.\
   교정은 커넥션당 스레드 + 상한(최대 8), 읽기 타임아웃(500ms), 읽기 횟수 상한이다.\
   로컬 유닉스 소켓도 원격 전송의 끝점이 되면 원격 사용자가 같은 공격을 할 수 있으므로, 요청 타임아웃과 연결 상한(32)을 둔다.
   > **slowloris** — 요청을 아주 느리게 보내 서버의 연결 슬롯을 오래 점유하는 서비스 거부 공격.

5. **느슨한 비교는 공격자가 고른 값을 통과시킨다.** `starts_with("localhost")`는 `localhost.evil.example`도 통과시킨다 → 호스트부 **정확 일치**.\
   `Content-Length`가 두 개면 파서마다 다른 값을 고를 수 있고(요청 경계 혼동), 숫자가 아니면 파싱 결과가 구현 의존이다 → **정확히 1개·숫자**만.\
   "무음 축소 없이 400"은 이상한 요청을 조용히 잘라 일부만 처리하지 않고 명시적으로 거절한다는 뜻이다 — 잘라서 받으면 검증한 것과 처리한 것이 달라진다.\
   경로 속 id(uuid)도 형식을 검증하고, 여러 앱 인스턴스가 서로의 파일을 지우지 않게 인스턴스(pid)별 디렉토리를 쓴다. 이벤트 종류는 화이트리스트로 제한한다.
   > **framing** — 바이트 스트림에서 요청 하나의 경계를 정하는 규칙(HTTP에선 헤더 끝과 Content-Length).

6. **확인과 점유 사이에 틈이 있다.** 경로 상태를 확인한 뒤 bind하기까지 사이에 다른 인스턴스가 같은 경로를 점유·정리할 수 있다.\
   옆에 락 파일을 두고 `flock`을 잡은 인스턴스만 경로를 정리·bind하게 하면 확인과 점유가 원자적이 된다.\
   소켓 파일은 0600(리눅스 기준 소유자만 연결 — 소켓 파일 권한을 무시하는 OS도 있어 디렉토리 권한이 실효 방어), 그 부모 런타임 디렉토리는 0700으로 **미리** 만들어 다른 사용자가 경로를 선점하거나 들여다보지 못하게 한다.
   > **TOCTOU(time-of-check to time-of-use)** — 검사한 시점과 사용하는 시점 사이에 상태가 바뀌어 검사가 무의미해지는 경쟁 조건.

## 문제 구조 (추상화 코드)

### 변형 A — 루프백 수신기의 인증: 토큰 전달 채널과 세션 결속
① 문제 코드
```rust
let child = Command::new("agent")
    .args(["--token", &token, "--port", &port.to_string()])             // argv → /proc 노출
    .spawn()?;
// 수신기: 토큰이 "하나라도 유효"하면 본문의 session_id 를 그대로 믿음
```
② 고친 코드
```rust
write_file_mode(&hdr_path, format!("Authorization: Bearer {token}\n"), 0o600)?;   // 세션별 토큰
let child = Command::new("agent").env("AGENT_HDR_FILE", &hdr_path).env("AGENT_PORT", port.to_string()).spawn()?;
// 자식 측 호출: curl -s -m 3 -H @"$AGENT_HDR_FILE" --data-binary @- http://127.0.0.1:$AGENT_PORT/events/<event> || true
// 수신기:
if session_for_token(&registry, &token).as_deref() != Some(body.session_id.as_str()) {
    return respond(stream, 403);                                      // 세션 간 위조 차단
}
```
무엇이 깨졌나: 비밀이 world-readable 채널로 흘렀고, 토큰이 특정 세션에 결속되지 않았다.\
실패 격리: 수신기 실패는 기능 저하(대체 수단으로 폴백)일 뿐 본 세션을 막지 않게, 호출 측은 짧은 타임아웃·항상 성공 종료.

### 변형 B — 엄격 입력 검증 (framing·Host·경로)
① 문제 코드
```rust
let len: usize = headers.get("content-length").and_then(|v| v.parse().ok()).unwrap_or(0);
if !headers.get("host").unwrap_or("").starts_with("localhost") { return 403 }
let path = format!("{dir}/{}.json", url_segment);                     // 경로 조작
```
② 고친 코드
```rust
let cl = headers.get_all("content-length");
if cl.len() != 1 || !cl[0].bytes().all(|b| b.is_ascii_digit()) { return respond(stream, 400) }
if host_part(headers.get("host")?) != "127.0.0.1" && host_part(..) != "localhost" { return respond(stream, 400) }
if !ALLOWED_EVENTS.contains(&event) { return respond(stream, 400) }
if !is_valid_id(url_segment) { return respond(stream, 400) }        // 형식 검증
let path = instance_dir(std::process::id()).join(format!("{url_segment}.json"));   // 인스턴스별
```
무엇이 깨졌나: "대충 맞으면 통과"하는 비교가 공격자가 고른 변형을 받아들였다.

### 변형 C — 자원 상한 (slowloris·로컬 소켓 DoS)
① 문제 코드
```rust
for stream in listener.incoming() {
    handle(stream?);                  // 한 연결이 끝날 때까지 다음 연결 대기, 읽기 무기한
}
```
② 고친 코드
```rust
let permits = Semaphore::new(8);                                   // 동시 연결 상한
for stream in listener.incoming() {
    let s = stream?;
    let Some(p) = permits.try_acquire() else { drop(s); continue };
    s.set_read_timeout(Some(Duration::from_millis(500)))?;         // 읽기 타임아웃
    thread::spawn(move || { let _p = p; handle_with_read_cap(s, MAX_READS) });
}
```
무엇이 깨졌나: 느린 클라이언트 하나가 처리 루프 전체를 멈출 수 있었다.\
같은 구조: 원격 요청의 끝점이 된 로컬 유닉스 소켓 데몬에 요청 타임아웃·연결 상한(32) 추가.

### 변형 D — 브라우저 오리진 (WebSocket은 CORS 밖)
① 문제 코드
```python
@app.websocket("/ws/terminal")
async def terminal(ws):
    await ws.accept()                 # 127.0.0.1 바인드만 믿음 → 임의 페이지가 PTY에 도달
```
② 고친 코드
```python
ALLOWED_WS_ORIGINS = {"http://127.0.0.1:PORT", "http://localhost:PORT"}
def origin_ok(ws): 
    o = ws.headers.get("origin")
    return o is None or o in ALLOWED_WS_ORIGINS     # 없음 = 비브라우저(단일 사용자 호스트 전제 — 다중 사용자면 토큰 필요)
@app.websocket("/ws/terminal")
async def terminal(ws):
    if not origin_ok(ws):
        await ws.close(code=4403); return            # accept 전에 거절
    await ws.accept()
# 새 WebSocket 라우트도 같은 origin_ok 를 공유 (패리티)
```
무엇이 깨졌나: 브라우저 보호(CORS)가 WebSocket에도 적용된다고 가정했다.

### 변형 E — 유닉스 소켓 경로 점유와 권한
① 문제 코드
```rust
if path.exists() { fs::remove_file(&path)?; }        // 확인 ─┐ 틈
let l = UnixListener::bind(&path)?;                   // 점유 ─┘
```
② 고친 코드
```rust
fs::create_dir_all(&runtime_dir)?; set_mode(&runtime_dir, 0o700)?;   // 사전 생성
let _lock = flock_exclusive(runtime_dir.join("daemon.lock"))?;        // 락을 잡은 인스턴스만
let _ = fs::remove_file(&path);
let l = UnixListener::bind(&path)?;
set_mode(&path, 0o600)?;
```
무엇이 깨졌나: 경로 확인과 bind가 원자적이지 않았다(① 은 bind TOCTOU의 전형적 형태를 보인 구조 예시 — 기록된 교정은 락 파일 `flock`).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
