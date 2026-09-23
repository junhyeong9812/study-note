# cs/issue/reliability/shutdown-backstop-independence — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **강제 종료는 정상 생명주기를 건너뛴다.** 언마운트 cleanup은 UI 프레임워크가 컴포넌트를 "정상적으로" 제거할 때 실행된다.\
창 강제 파괴(destroy)나 프로세스 종료는 그 절차 없이 웹뷰·프로세스를 끝내므로 cleanup이 돌 기회가 없다 — 그 결과 보조 창을 닫아도 세션 프로세스·폴링 스레드가 남고, 디바운스 대기 중이던 자동 저장이 유실됐다.\
또 현재 화면만 훑어 정리 대상을 모으면 화면 밖(다른 레이아웃에 보관된) 자원을 놓친다.\
정리는 **닫기 경로 자체**(close 요청 핸들러)에서 모든 보관 위치를 훑어 명시적으로 수행하고, 그 완료를 기다린 뒤 파괴한다.

2. **예외·행이면 창이 영원히 안 닫힌다.** `preventDefault()`로 기본 닫기를 막았으므로, 뒤의 `destroy()`에 도달하지 못하면 아무도 창을 닫지 않는다.\
try/finally + 4초 워치독은 "teardown이 실패하거나 느려도 destroy는 실행"을 보장한다 — 단 **JS 이벤트 루프가 돌고 있다는 전제** 위에서다.\
teardown 도중 웹뷰의 JS 루프 자체가 멈추면 finally도 워치독 타이머 콜백도 같은 루프에서 실행되므로 함께 멈춘다. 1차 수정은 고장 지점과 같은 층에 백스톱을 둔 것이었다.

3. **백스톱이 구하려는 경로에 의존했다.** 앱 종료 API(`AppHandle::exit` 류)는 요청을 앱 이벤트 루프에 넣어 처리한다 — 그 루프가 멈춰 있으면 종료 요청도 처리되지 않는다.\
"최후 방어선"이 장애가 난 바로 그 경로를 지나가야 동작한다면, 장애 시에 동작하지 않는다.\
`process::exit`는 호출 즉시 OS 수준에서 프로세스를 끝낸다 — 이벤트 루프·다른 스레드·소멸자와 무관하다. 그래서 백스톱을 **독립 스레드**에서 걸고, 최종 수단을 OS 종료로 했다(소멸자가 안 도는 것은 의도적으로 수용, 그 전에 자식 프로세스는 회수).
   > **백스톱(backstop)** — 정상 경로가 모두 실패했을 때만 작동하는 최후 방어 장치. 정상 경로의 고장 원인과 독립이어야 의미가 있다.

4. **join은 종료를 외부 상대에 종속시킨다.** join은 대상 스레드가 끝날 때까지 기다린다. 그 스레드가 블록된 읽기나 응답 없는 원격 호스트로의 연결 중이면, 종료가 그 읽기·그 원격의 응답에 묶인다 — 타임아웃 없는 외부 상대가 앱 종료를 인질로 잡는다.\
종료 경로의 정리는 자식 프로세스에 종료 신호만 보내고 기다리지 않는다; 프로세스가 끝나면 OS가 스레드·소켓을 회수한다.\
반대로 **패널 하나 닫기**는 앱이 계속 살아 있으므로 join해서 누수를 막아야 한다 — 같은 정리라도 "앱이 곧 끝나는가"에 따라 전략이 다르다.

5. **오염된 락에 unwrap하면 정리가 패닉한다.** 다른 스레드가 락을 쥔 채 패닉하면 뮤텍스가 poison 상태가 되고, `lock().unwrap()`은 패닉해 그 뒤의 정리(자식 종료)를 건너뛴다.\
best-effort 정리에서는 `lock().unwrap_or_else(|p| p.into_inner())`로 오염돼도 guard를 회수해 계속 진행한다 — 종료 직전에는 데이터 일관성보다 "자식을 확실히 죽이는 것"이 우선이다.\
정리 함수는 여러 번 불려도 무해해야 한다(멱등) — 여러 종료 경로가 겹쳐 호출할 수 있다. (이 부분은 리뷰 지적 기반의 예방 설계다.)
   > **poison(락 오염)** — 락을 쥔 스레드가 패닉해 보호 데이터가 불완전할 수 있음을 표시한 상태.

6. **정상 경로에 우선권, 최악에 상한.** 유예를 ack 대기 2.5초 < 화면 워치독 4초 < 런타임 백스톱 5초로 두면, 정상 경로(보조 창 정리 ack)가 먼저 끝날 기회를 갖고, 그다음 화면 쪽 워치독, 마지막에 하드 종료가 온다.\
순서가 뒤집히면 하드 종료가 정상 정리를 잘라 먹는다. 동시에 최악의 경우도 5초로 상한이 있다.\
X를 반복 클릭해도 타이머가 쌓이지 않도록 원자 플래그 `swap(true)`로 **한 번만 arm**한다.\
(닫기 경로의 명시 저장도 같은 원리로 1200ms 예산을 둬 워치독 4초를 잠식하지 않게 했다.)

7. **런타임은 "메인" 의미를 모른다.** 런타임이 창 목록이 비었을 때만 종료 이벤트를 보내면, 메인 창만 파괴되고 보조 창이 남은 경우 종료 이벤트가 오지 않아 앱 프로세스와 자식 프로세스가 계속 남는다.\
"메인 닫기 = 앱 종료"는 애플리케이션의 의미이므로 애플리케이션이 명시적으로 보장한다 — 메인 창 파괴 이벤트에서 `kill_all()` + 종료, 보조 창 닫기는 라벨 가드로 제외.

## 문제 구조 (추상화 코드)

### 변형 A — 언마운트·현재 화면에 의존한 정리 (정리 누락)
① 문제 코드
```ts
useEffect(() => () => closeSession(id), [id]);        // destroy 는 언마운트를 보장하지 않음
useEffect(() => () => saver.flush(), []);             // 디바운스 창 안에서 종료하면 저장 유실
win.onCloseRequested(async () => {
  for (const p of visiblePanels()) await closeSession(p.sessionId);   // 화면 밖 레이아웃의 세션 누락
  win.destroy();
});
```
② 고친 코드
```ts
win.onCloseRequested(async (e) => {
  e.preventDefault();
  shuttingDown.current = true;                          // await 전에 세팅 (앱 종료 vs 사용자 창 닫기 구분)
  try {
    await withBudget(1200, flushAllSavers());           // 명시 flush — 실패는 keep + 사유 (성공 시에만 dirty 제거)
    const ids = [...visiblePanels(), ...allStoredLayouts()].map(sessionIdOf);
    await Promise.all(ids.map(closeSession));
  } finally {
    win.destroy();                                      // 예외여도 파괴
  }
});
// 메인 종료: 보조 창들에 shutdown 알림 → 각자 정리 후 ack → ack 대기(2.5s fallback) 후 파괴
```
무엇이 깨졌나: 정리를 정상 생명주기와 보이는 화면에 걸어, 강제 종료·화면 밖 자원 경로에서 빠졌다.

### 변형 B — 백스톱이 고장 지점과 같은 층 (멈춘 이벤트 루프)
① 문제 코드
```ts
// 화면 층
win.onCloseRequested(async (e) => {
  e.preventDefault();
  setTimeout(() => win.destroy(), 4000);               // 워치독도 같은 JS 루프 → 루프가 멈추면 같이 멈춤
  try { await teardown(); } finally { win.destroy(); }
});
```
```rust
// 런타임 층
WindowEvent::Destroyed if label == "main" => { kill_all(); app.exit(0); }   // exit 은 멈춘 이벤트 루프를 경유
```
② 고친 코드
```rust
static BACKSTOP_ARMED: AtomicBool = AtomicBool::new(false);

app.build(ctx)?.run(|app, ev| match ev {
    RunEvent::WindowEvent { label, event: WindowEvent::CloseRequested { .. }, .. } if label == "main" => {
        // JS preventDefault 와 무관하게 런타임에서 발화
        if !BACKSTOP_ARMED.swap(true, Ordering::SeqCst) {            // 1회만 arm
            let h = app.clone();
            std::thread::spawn(move || {                              // 이벤트 루프와 독립된 스레드
                std::thread::sleep(Duration::from_secs(5));           // 워치독 4s·ack 2.5s 보다 길게
                h.state::<Sessions>().kill_all();                     // 자식 회수 (비블로킹)
                std::process::exit(0);                                // OS 수준 즉시 종료
            });
        }
    }
    _ => {}
});
```
무엇이 깨졌나: 최후 방어선(워치독·종료 API)이 장애 지점(멈춘 이벤트 루프)을 지나가야만 동작했다.\
같은 구조: 1차 수정만 하고 실제 닫기를 검증하지 않아 운영 환경에서 재발한 뒤에야 발견했다(종료 신호로는 정상 종료되어 가려짐).

### 변형 C — 종료 경로 정리 코드의 블로킹·패닉
① 문제 코드
```rust
fn kill_all(&self) {
    let mut map = self.sessions.lock().unwrap();        // 오염된 락 → 패닉 → 정리 건너뜀
    for s in map.values_mut() {
        s.kill();
        s.reader.join().unwrap();                       // 블록된 read 에서 멈춤
    }
}
// 원격 링크 정리
fn detach_all(&self) { for l in &self.links { l.stop(); } }   // stop() 이 join — 응답 없는 원격 connect 중이면 종료가 걸림
```
② 고친 코드
```rust
fn kill_all(&self) {
    let mut map = self.sessions.lock().unwrap_or_else(|p| p.into_inner());   // poison 복구
    for s in map.values_mut() {
        match &mut s.transport {
            Transport::Local { killer, .. } => { let _ = killer.kill(); }     // 신호만, join 없음
            Transport::Remote(h) => h.cancel(),
        }
        s.shared.set_dead();
    }
    // map 은 비우지 않는다 — 곧 종료되므로 무해, 여러 번 불려도 멱등
}
// 앱 종료 경로에서 join 하는 stop()/detach_all 은 제거 — 원격 연결은 프로세스 종료로 닫힌다
// 패널 하나 닫기(remove)는 반대로 join 을 유지해 누수를 막는다
```
무엇이 깨졌나: best-effort여야 할 종료 정리가 외부 응답(블록된 read·원격 connect)과 다른 스레드의 패닉에 종속됐다.\
(join·poison 부분은 설계 근거·리뷰 지적 기반 예방, 원격 detach 부분은 "닫기가 안 닫히던" 사고를 두 번 겪은 뒤 세 번째 경로를 차단한 것)

### 변형 D — "메인 닫기 = 앱 종료"를 런타임이 보장한다고 가정
① 문제 코드
```rust
app.run(ctx);                                           // 종료 이벤트는 창 목록이 비었을 때만
// 메인 창만 파괴되고 보조 창이 남으면 → 종료 이벤트 없음 → 프로세스·자식 잔존
```
② 고친 코드
```rust
app.build(ctx)?.run(|app, ev| match ev {
    RunEvent::WindowEvent { label, event: WindowEvent::Destroyed, .. } if label == "main" => {
        app.state::<Sessions>().kill_all();
        app.exit(0);                                    // 보조 창 닫기는 라벨 가드로 제외
    }
    RunEvent::ExitRequested { .. } => app.state::<Sessions>().kill_all(),   // 두 번 불려도 멱등
    _ => {}
});
```
무엇이 깨졌나: 애플리케이션의 종료 의미를 런타임의 기본 종료 조건이 대신해 줄 것이라 가정했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
