# cs/issue/rust/tauri/command-boundary-execution-model — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **웹뷰 전체가 얼어붙는다.** Tauri는 동기(`fn`) 커맨드를 **메인(UI) 스레드**에서, async 커맨드를 별도 async 런타임에서 실행한다. 동기 커맨드가 최대 120초짜리 외부 프로세스를 기다리는 동안 메인 스레드의 이벤트 루프가 멈추므로, 창 다시 그리기·다른 입력·다른 커맨드 응답이 전부 멈춘다. 이 사례는 런타임에서 실제로 발생했다.
   > **메인(UI) 스레드** — 창 이벤트를 처리하고 화면을 그리는 단 하나의 스레드. 여기서 오래 걸리는 일을 하면 앱 전체가 응답하지 않는다.

2. **완전히 해결되지는 않는다.** `async fn`으로 바꾸면 UI 스레드는 풀려난다. 그러나 본문에서 블로킹 표준 호출(프로세스 대기·동기 I/O)을 하면 그동안 **async 런타임의 워커 스레드를 점유**해, 같은 런타임의 다른 async 작업이 굶는다. `spawn_blocking`은 본문을 **블로킹 전용 스레드 풀**로 보내고, async 커맨드는 그 완료만 await한다. 순위: ① async + `spawn_blocking`(최선) > ② async + 직접 블로킹(차선 — UI는 살지만 워커를 막음) > ③ 동기 fn(선택하지 않음 — UI 프리즈). 이 사례는 본문을 `_blocking` 동기 함수로 분리하고 `spawn_blocking`으로 감쌌다.
   > **spawn_blocking** — 블로킹 작업을 async 워커가 아닌 별도 블로킹 풀에서 실행하고, 결과를 `JoinHandle`로 돌려주는 런타임 기능.

3. **호출자가 소비자의 속도에 묶여 멈춘다.** bounded 채널이 가득 찼을 때 `blocking_send`는 빈자리가 생길 때까지 호출 스레드를 재운다. 소비자인 네트워크 루프가 호스트 키 확인·연결·지연·종료 중이면 채널이 비워지지 않으므로, 동기 커맨드(`write`/`resize`)를 부른 스레드가 그대로 멈춰 입력 지연이나 앱 정지가 된다. 동기 호출자는 async 소비자의 진행을 제어할 수 없으므로, **소비자 쪽의 어떤 지연도 호출 스레드(UI/IPC)의 정지로 번역**된다. 이 결함은 구현 전 계획 리뷰에서 지적됐다.

4. **`try_send`는 "가득 차면 즉시 에러"라서 입력을 잃을 수 있다.** 이것을 입력의 성격별로 보완했다.
   - **resize** — 중간값은 의미가 없으므로 **최신값만 남기는 병합**(watch 채널)으로 바꿨다. 가득 참 자체가 사라진다.
   - **연결 전 입력** — 생성 커맨드는 id를 **즉시 반환**하고 연결은 백그라운드에서 한다. ready 이전 입력은 큐에 버퍼링하고, resize는 ready 시점에 최신값 1회만 적용한다.
   - **상태** — 연결 진행·실패는 커맨드의 반환값 대신 **상태 이벤트**로 프런트엔드에 통지한다.
   원칙: 동기 경계에서는 **절대 기다리지 않고**, 그 대가(유실 가능성)는 데이터 성격에 맞는 구조로 흡수한다.
   > **backpressure** — 소비자가 느릴 때 생산자에게 속도를 늦추라는 신호가 전달되는 것. 동기 UI 스레드에 backpressure를 걸면 UI가 멈추므로, 경계에서는 거절·병합으로 바꾼다.

5. **커맨드 경계의 panic은 호출자에게 구조화된 에러를 주지 못하고 프로세스 안정성을 해친다.** `std::thread::Builder::spawn`은 스레드를 만들지 못하면 `io::Error`를 돌려준다. 이를 `expect`로 처리하면 자원 부족이라는 **예상 가능한 실패**가 panic이 되어, 프런트엔드는 "무엇이 왜 실패했나"를 받지 못한다(구체 증상은 실행 위치·빌드 설정에 따라 다르다 — 메인 스레드에서 도는 동기 커맨드의 panic은 앱 종료로 이어질 수 있고, `panic = "abort"` 프로필이면 즉시 종료, async 커맨드 태스크의 panic은 호출 promise가 응답 없이 남을 수 있다). `Result`로 전파하면 호출자는 앱 에러 형태(메시지·코드)를 받아 사용자에게 보여 주거나 재시도할 수 있다. 교정: `spawn`의 반환형을 `io::Result`로 바꾸고, 시작 커맨드가 이를 앱 에러로 매핑한다.
   > **커맨드 경계** — 웹뷰(JavaScript)와 네이티브(Rust)가 IPC로 만나는 지점. 여기서 나가는 모든 실패는 직렬화 가능한 에러 값이어야 호출자가 다룰 수 있다.

6. **원칙: 커맨드 경계를 넘는 것은 "값"이어야 한다 — 시간도 실패도.** `spawn_blocking`의 `JoinError`(블로킹 작업 안의 panic 등)를 앱 에러로 매핑한 것과, 스레드 생성 실패를 `io::Result`로 전파한 것은 모두 "실패를 panic이 아니라 호출자가 받는 에러 값으로" 바꾼 것이다. "블로킹을 UI 스레드 밖으로"는 **시간**을 경계 밖으로 빼는 것이다. 느린 일은 다른 스레드에서 하고 호출자는 완료를 기다리는 future를 받는다. 둘이 한 쌍을 이뤄, 커맨드 경계는 **빨리 돌아오고, 실패하면 구조화된 값으로 돌아온다.**

## 문제 구조 (추상화 코드)

### 변형 A — 동기 커맨드에서 장시간 블로킹 (UI 프리즈)
① 문제 코드
```rust
#[tauri::command]
pub fn generate_summary(app: AppHandle, cwd: String, id: String) -> Result<Summary, AppError> {
    run_external_process(&cwd, &id)          // 최대 120s — 메인(UI) 스레드에서 실행
}
```
② 고친 코드
```rust
#[tauri::command]
pub async fn generate_summary(app: AppHandle, cwd: String, id: String) -> Result<Summary, AppError> {
    tauri::async_runtime::spawn_blocking(move || generate_summary_blocking(app, cwd, id))
        .await
        .map_err(|_| AppError::new("Summary task failed to run"))?   // JoinError(panic 등)도 값으로
}

fn generate_summary_blocking(app: AppHandle, cwd: String, id: String) -> Result<Summary, AppError> {
    run_external_process(&cwd, &id)          // 블로킹 전용 풀
}
```
무엇이 깨졌나: 동기 커맨드가 어느 스레드에서 도는지 모른 채 긴 작업을 넣었다.

### 변형 B — 동기 커맨드에서 bounded 채널로 블로킹 전송 (계획 리뷰 단계 지적)
① 문제 코드
```rust
#[tauri::command]
pub fn terminal_write(state: State<Sessions>, id: Id, data: Vec<u8>) -> Result<(), AppError> {
    state.get(id)?.tx.blocking_send(Msg::Input(data))?;   // 소비자(연결·키 확인 대기)가 멈추면 호출자도 멈춤
    Ok(())
}
#[tauri::command]
pub fn terminal_resize(state: State<Sessions>, id: Id, cols: u16, rows: u16) -> Result<(), AppError> {
    state.get(id)?.tx.blocking_send(Msg::Resize(cols, rows))?;
    Ok(())
}
```
② 고친 코드
```rust
pub fn terminal_write(state: State<Sessions>, id: Id, data: Vec<u8>) -> Result<(), AppError> {
    state.get(id)?.tx.try_send(Msg::Input(data)).map_err(AppError::from)   // 절대 안 막힘
}
pub fn terminal_resize(state: State<Sessions>, id: Id, cols: u16, rows: u16) -> Result<(), AppError> {
    state.get(id)?.resize_tx.send_replace((cols, rows));                   // watch — 최신값 병합
    Ok(())
}
pub fn session_create(/* ... */) -> Result<Id, AppError> {
    let id = new_id();
    tauri::async_runtime::spawn(connect_in_background(id /* ... */));   // id 즉시 반환, 연결은 백그라운드 — 동기 커맨드(메인 스레드)엔 런타임 컨텍스트가 없으니 앱 런타임 핸들로 spawn
    Ok(id)                                        // ready 전 입력은 큐 버퍼, 상태는 이벤트로 통지
}
```
무엇이 깨졌나: 동기 호출자가 통제할 수 없는 async 소비자의 속도에 호출 스레드를 묶었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A·B)은 "블로킹을 커맨드 경계의 호출 스레드 밖으로 뺀다"이다. 같은 원리(커맨드 경계는 호출자에게 빨리, 구조화된 형태로 돌아와야 한다)에 다른 방안이 쓰인 사례:

### 방안 1 — 커맨드 경계에서 panic 대신 `Result` 전파
```rust
// 문제
impl Host {
    pub fn spawn(/* ... */) -> Host {
        std::thread::Builder::new().name("host".into())
            .spawn(move || host_main(/* ... */))
            .expect("failed to spawn host thread");     // 자원 부족 → panic
        // ...
    }
}

// 고친
impl Host {
    pub fn spawn(/* ... */) -> std::io::Result<Host> {
        std::thread::Builder::new().name("host".into())
            .spawn(move || host_main(/* ... */))?;      // 값으로 전파
        // ...
    }
}
#[tauri::command]
pub fn host_start(/* ... */) -> Result<(), AppError> {
    let host = Host::spawn(/* ... */).map_err(AppError::from)?;   // 경계에서 앱 에러로 매핑
    // ...
}
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 블로킹을 호출 스레드 밖으로 | 커맨드 본문이 오래 걸리거나 소비자 속도에 의존한다 | async 전환·spawn_blocking·채널 구조 변경 | 본문 깊은 곳의 블로킹 호출 하나가 남으면 재발 | 외부 프로세스·네트워크·채널 전송이 있는 커맨드 |
| 1. panic 대신 Result | 실패가 예상 가능하다(자원 할당·I/O) | 반환형 변경과 매핑 | 경계 밖 스레드의 panic 은 여전히 별도 처리 필요 | 커맨드가 스레드·자원을 새로 만드는 경로 |

**결론**: 둘은 경쟁하는 방안이 아니라 커맨드 경계 계약의 두 축이다 — 기본 방안은 **시간**(빨리 돌아온다), 방안 1은 **실패**(값으로 돌아온다)를 다룬다.\
블로킹 작업을 스레드 밖으로 빼면 그 스레드의 실패(`JoinError`)가 새로 생기므로, 기본 방안을 적용할 때는 방안 1의 원칙도 함께 적용해야 한다(변형 A의 `map_err`).
