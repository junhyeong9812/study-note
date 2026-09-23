# cs/issue/os/subprocess-lifecycle-and-pipes — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **wait 없음 = 좀비.** 종료된 자식은 부모가 `wait`로 종료 상태를 회수하기 전까지 프로세스 테이블에 **좀비**로 남는다.\
`kill`만 보내고 끝내면 좀비가 남고, 회수 전에 "연결 끊김" 이벤트를 내보내 상태 순서도 어긋났다.\
자식 stdin 쓰기가 실패했을 때 바로 `return`하면 회수도 안 되고, 쓰기 실패(EPIPE)는 대개 자식이 **먼저 죽은 결과**라 진짜 원인은 자식의 stderr·종료 코드에 있는데 그것을 잃는다.\
쓰기 오류는 저장만 하고 **항상 wait_with_output**한 뒤, 반환 우선순위를 "자식 stderr > 쓰기 오류"로 둔다.\
단 입력을 전부 쓴 **뒤에** 출력을 읽기 시작하면, 입력·출력이 파이프 버퍼보다 클 때 2번과 같은 교착이 생긴다(자식은 stdout이 차서 멈추고 부모는 stdin 쓰기에서 멈춤) — 쓰기는 별도 스레드에서 드레인과 동시에 하고, 다 쓰면 stdin을 닫아 EOF를 준다.
   > **좀비(zombie)** — 실행은 끝났지만 부모가 종료 상태를 회수하지 않아 테이블 항목만 남은 프로세스.

2. **한 스트림만 드레인 → 교착.** 파이프는 유한 버퍼(리눅스 기본 64KiB — OS·설정마다 다름)다.\
자식이 stderr에 계속 쓰면 버퍼가 차는 순간 자식의 `write`가 **블록**된다.\
부모는 stdout의 EOF를 기다리고, 자식은 stderr 버퍼가 비기를 기다린다 — 서로를 기다리는 **교착**이다.\
타임아웃은 이것을 "부분적으로만" 막는다(멈춘 채 시간을 버림).\
교정은 **모든 스트림을 동시에 드레인**(스트림별 스레드)하는 것이다. 두 스트림을 합치는 방법(stderr → stdout 리다이렉트)은 stdout이 바이너리 산출물이면 텍스트가 섞여 **손상**되므로 선택하지 않았다.

3. **손자가 쥔 write-end.** 파이프 EOF는 그 파이프의 **모든 write-end가 닫혀야** 온다.\
자식을 kill해도, 자식이 띄운 손자 프로세스가 stdout write-end를 상속해 살아 있으면 EOF가 오지 않아 드레인 스레드와 그 `join`이 무한 대기한다.\
드레인 결과를 채널로 받아 **타임아웃 있는 수신**(`recv_timeout`)으로 기다리고, 성공 판정은 `exit 0 AND 출력이 비어 있지 않음`으로 한다.\
근본적으로 손자까지 정리하려면 프로세스 그룹 단위 종료가 필요하다(남은 과제로 기록 — [process-group-and-tree-termination](../process-group-and-tree-termination/)).

4. **stdio 순수성.** stdin/stdout을 프로토콜 전송로로 쓰면 그 채널에는 **프로토콜 메시지만** 흘러야 한다.\
패키지 러너가 "설치할까요?" 확인 프롬프트를 띄우면 그 프롬프트가 stdin(=프로토콜 채널)에서 응답을 기다리며 **영원히 멈추고**, 부모는 프로토콜 응답을 기다린다(러너·버전에 따라 비TTY에서는 자동 승인하기도 하므로, 동작에 기대지 말고 명시 옵션으로 고정한다).\
확인을 자동 승인 옵션으로 끄고(`--yes`), 로그는 stderr로 분리해 드레인·노출한다. 스모크로 stdout이 순수 프로토콜인지 확인했다.

5. **열린 stdin.** 입력 파일을 주지 않은 필터형 명령(`cat >> f` 류)이나 "추가 입력을 stdin에서 읽는" CLI는 **stdin의 EOF까지** 읽는다.\
비대화 실행 환경에서 stdin이 파이프·TTY로 열린 채 아무도 쓰지 않으면 EOF가 오지 않아 **영원히 블록**된다(출력 몇십 바이트에서 정지).\
예방은 stdin을 **명시적으로 닫는 것** — `< /dev/null`, 또는 입력이 있으면 명시 리다이렉트(`cat input | cmd -`).

6. **소비자 끊김과 보조 작업자 수명.** 소비자가 끊겨도 생산자 루프가 그것을 감지하지 못하면 `readline()`에서 계속 기다리고, 정리 경로(terminate·wait)가 돌지 않아 자식이 **누적**된다(수십 개).\
핸들을 dict로 추적하면서 같은 키로 중복 시작하면 이전 자식의 참조를 잃는 race도 겹쳤다(원문은 원인을 "추정"으로 기록).\
보조 스레드도 같다 — 폴링 스레드의 정지를 명시적 close 경로에만 묶으면, 자식이 **스스로 종료**하거나 시작에 실패할 때 스레드가 영원히 남는다.\
보조 작업자의 수명은 **대상 자원의 실제 수명**(자식이 죽으면 끊기는 채널)에 결박한다.

7. **파이프 ≠ 터미널 → 버퍼링.** Python 등은 stdout이 터미널이면 줄 단위, **파이프면 블록 단위**로 버퍼링한다.\
그래서 부모가 줄 단위로 진행률을 파싱하려 해도 버퍼가 찰 때까지 아무것도 오지 않는다(`PYTHONUNBUFFERED=1`로 해결).\
2번과의 공통점: 둘 다 "자식의 stdout이 파이프라는 사실"이 동작을 바꾼다 — 파이프는 유한하고(교착), 버퍼링 정책이 다르다(지연).\
같은 사건에서 `-v`와 `-q`를 같이 줘 상쇄되어 파싱 대상 줄 자체가 안 찍힌 것도 겹쳤다.

8. **단일 인스턴스 위임.** 어떤 프로그램(예: 브라우저)은 같은 프로필로 두 번째 실행을 하면 **이미 떠 있는 인스턴스에 위임하고 즉시 종료**한다.\
그러면 "스폰한 프로세스 종료 = 창 닫힘"이라는 wait 전제가 깨져, 런처가 정리 코드를 조기에 실행했다.\
**전용 프로필 디렉토리**로 별도 인스턴스를 강제하면 스폰한 프로세스가 창 수명 동안 블록되어 wait 전제가 다시 성립한다 — 단 그 전용 프로필을 쓰는 인스턴스가 이미 떠 있으면 다시 위임되므로, 프로필은 이 런처만 쓰게 한다. 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — 회수(wait) 누락
① 문제 코드
```rust
fn stop(child: &mut Child) { child.start_kill(); emit(Disconnected); }   // 회수 전 이벤트, 좀비

fn run(input: &[u8]) -> Result<Out> {
    let mut child = spawn_piped()?;
    child.stdin.take().unwrap().write_all(input)?;   // 실패 시 즉시 return → wait·stderr 유실
    /* ... */
}
```
② 고친 코드
```rust
async fn stop(child: &mut Child) { child.start_kill(); child.wait().await; emit(Disconnected); }

fn run(input: &[u8]) -> Result<Out> {
    let mut child = spawn_piped()?;
    let mut stdin = child.stdin.take().unwrap();
    let data = input.to_vec();
    let writer = thread::spawn(move || stdin.write_all(&data));             // 쓰기와 드레인을 동시에 (큰 입출력 교착 방지), 끝나면 drop = EOF
    let out = child.wait_with_output()?;                                    // 항상 회수 (stdout·stderr 드레인)
    let write_err = writer.join().unwrap().err();                           // 쓰기 오류는 저장만
    if !out.status.success() { return Err(stderr_of(&out)); }             // 자식 stderr 우선
    if let Some(e) = write_err { return Err(e.into()); }
    Ok(parse(out.stdout))
}
```
무엇이 깨졌나: 종료 경로 중 일부가 wait를 건너뛰었다.\
같은 구조: reader 스레드가 블로킹 wait에 걸려 같은 핸들로 kill 불가 → kill 전용 핸들을 미리 복제 · 탭 전환(detach)·패널 닫기(kill)·앱 종료(drop)를 한 이벤트로 뭉개 누수·중복 생성 → 이벤트별 수명 분리.

### 변형 B — 파이프 드레인과 타임아웃
① 문제 코드
```java
Process p = new ProcessBuilder(cmd).redirectErrorStream(false).start();
while ((n = p.getInputStream().read(buf)) != -1) { /* ... */ }  // stderr 미소비 → 교착
p.waitFor(30, SECONDS);
```
```rust
let out = Command::new(cmd).output()?;          // 타임아웃 없음
// 또는 kill 후 drain_thread.join()  → 손자가 write-end 보유 → 무한 대기
```
② 고친 코드
```rust
let mut child = spawn(stdout=piped, stderr=piped)?;
let (otx, orx) = channel(); spawn_drain(child.stdout, CAP, otx);   // 스트림별 드레인 + 상한
spawn_drain_discard(child.stderr);                                 // 교착 방지용 소비 (진단이 필요하면 상한 두고 보관)
let status = loop {
    match child.try_wait()? {
        Some(st) => break Some(st),
        None if start.elapsed() >= TIMEOUT => { child.kill().ok(); child.wait().ok(); break None; }
        None => sleep(50ms),
    }
};
let text = orx.recv_timeout(3s).unwrap_or_default();              // join 대신 (손자가 write-end를 쥐면 드레인 스레드는 남는다 — 그룹 종료로 근본 정리)
match status { Some(st) if st.success() && !text.is_empty() => Ok(text), _ => Err(/* ... */) }
```
무엇이 깨졌나: 읽지 않은 스트림이 차서 자식이 블록됐고, 상속된 write-end 때문에 EOF가 오지 않았다.\
같은 구조: 요약 호출 러너 · 세션 아카이브 러너(스트림별 드레인 + 출력 상한 + kill/reap) · 외부 인코더 호출(스트림별 동시 드레인 채택, 스트림 합치기는 바이너리 손상으로 선택하지 않음).

### 변형 C — stdio 프로토콜 순수성
① 문제 코드
```rust
Command::new("pkg-runner").arg("adapter")        // 첫 실행 시 설치 확인 프롬프트가 stdin 점유
    .stdin(piped()).stdout(piped()).spawn()?;
```
② 고친 코드
```rust
Command::new("pkg-runner").arg("--yes").arg("adapter")   // 대화형 확인 끔
    .stdin(piped()).stdout(piped()).stderr(piped())       // 로그는 stderr로 분리·드레인
    .spawn()?;
```
무엇이 깨졌나: 프로토콜 채널에 대화형 프롬프트가 끼어들어 양쪽이 서로의 응답을 기다렸다.

### 변형 D — 열린 stdin
① 문제 코드
```bash
cat >> timeline.md                  # 입력 없음 → stdin EOF 대기
review-cli exec "$PROMPT" > out.txt  # "추가 입력을 stdin에서 읽는 중..." → 정지
```
② 고친 코드
```bash
review-cli exec "$PROMPT" < /dev/null > out.txt 2>&1
cat input.txt | review-cli exec - > out.txt   # 입력이 있으면 명시 리다이렉트
```
무엇이 깨졌나: 비대화 환경에서 stdin이 열린 채라 EOF가 오지 않았다.

### 변형 E — 소비자 끊김·보조 작업자 수명
① 문제 코드
```python
active[name] = await create_subprocess_exec("tool", "logs", "-f", name)   # 중복 시작 시 덮어쓰기
while line := await proc.stdout.readline():
    await ws.send(line)             # ws 끊김을 감지 못함 → 정리 경로 안 돎
```
```rust
thread::spawn(move || while !stop.load() { poll(); sleep(..) });   // stop은 close에서만 세팅
```
② 고친 코드
```rust
thread::spawn(move || {
    while let Ok(chunk) = rx.recv() { emit(chunk); }   // 자식이 죽으면 sender drop → 루프 종료
    stop.store(true);                                   // 자연 종료 경로도 폴링 정지
});
```
```python
# 설계(미구현): 자식 프로세스 대신 엔진 API 스트림을 직접 읽고, 태스크 취소 시 응답을 해제
# 임시: 서비스 재시작으로 cgroup 내 자식 일괄 정리
```
무엇이 깨졌나: 정리 트리거가 대상의 실제 수명(자식 종료·소비자 끊김)과 연결돼 있지 않았다.

### 변형 F — 파이프 블록 버퍼링
① 문제 코드
```python
proc = Popen(["python", "-m", "pytest", "-v", "-q"], stdout=PIPE)   # -v/-q 상쇄 + 블록 버퍼
```
② 고친 코드
```python
proc = Popen(["python", "-m", "pytest", "-v"], stdout=PIPE,
             env={**os.environ, "PYTHONUNBUFFERED": "1"})
```
무엇이 깨졌나: 파이프에 연결된 자식이 출력을 블록 버퍼링해 진행 줄이 실시간으로 오지 않았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

같은 원리(자식 수명 = 작업 수명으로 관리)에서, 그 전제가 프로그램에 따라 깨지는 경우의 두 방안.

### 방안 1 — spawn한 자식을 wait로 회수 (위 변형 A~F)
```rust
let status = child.wait()?;   // 자식 종료 = 작업 종료
cleanup();
```

### 방안 2 — 단일 인스턴스 위임 프로그램: 전용 프로필로 별도 인스턴스 강제
```bash
"$BROWSER" --app="$URL" --user-data-dir="$DEDICATED_PROFILE" \
  --no-first-run >/dev/null 2>&1 || true
cleanup   # 이 호출이 반환(창 닫힘)해야 실행
```

| | 방안 1: wait 회수 | 방안 2: 전용 프로필 강제 |
|---|---|---|
| 전제 | 스폰한 프로세스가 작업을 직접 수행하고 끝나면 반환 | 프로그램이 같은 프로필의 기존 인스턴스에 위임하고 즉시 종료 |
| 비용 | 모든 종료 경로에 wait·드레인 | 별도 프로필 디렉토리(디스크·첫 실행 비용) |
| 실패 모드 | 경로 하나 누락 시 좀비·교착 | 기본 프로필로 실행하면 즉시 반환 → 정리 조기 실행 · 프로필 락 충돌 |
| 맞는 조건 | 일반 CLI·서브프로세스 | 브라우저처럼 프로필 락 기반 단일 인스턴스 프로그램 |

결론: 기본은 방안 1이다.\
방안 1의 전제(스폰 프로세스 종료 = 작업 종료)가 프로그램의 인스턴스 모델 때문에 깨질 때만, 방안 2로 **전제를 다시 성립시킨 뒤** 방안 1을 쓴다.\
방안 2는 사용자 메인 프로필을 오염시키지 않는 부수 효과도 있다.
