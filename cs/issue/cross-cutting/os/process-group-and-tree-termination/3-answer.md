# cs/issue/os/process-group-and-tree-termination — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **부모만 kill → 고아.** 셸을 kill하면 셸이 띄운 손자는 부모를 잃고 init(또는 서브리퍼)으로 **reparent**되어 계속 실행된다.\
타임아웃이 셸만 죽여 고아 작업이 잔존 자원(컨테이너 등)을 만들었고, 오류 분기에서는 kill 자체를 안 하기도 했다.\
스폰할 때 **새 세션·프로세스 그룹**(`setsid` / `start_new_session`)으로 띄우면 그 자식이 그룹 리더(pid = pgid)가 되고, 종료할 때 **`killpg(pgid, SIGTERM)` → 유예 → SIGKILL → wait**로 손자까지 정리한다.\
그룹을 만들 수 없는 기존 프로세스는 `pgrep -P`로 자식·손자를 모아 트리째 TERM → KILL한다.
   > **프로세스 그룹(pgid)** — 신호를 한 번에 받는 프로세스 묶음. `killpg`는 그룹 전체에 신호를 보낸다.

2. **논리적 취소 ≠ OS 종료.** 상태 플래그는 부모 프로그램 안의 값일 뿐, 이미 fork된 프로세스는 그 값을 모른다 — 테스트가 끝까지 실행됐다.\
취소는 **추적 중인 프로세스 목록에 실제 kill**을 보내야 한다.\
권한이 다른(root로 띄운) 자손에게는 일반 사용자가 신호를 보낼 수 없어 `killpg`가 **EPERM**이다 — 원문은 이것을 best-effort 한계로 보안 백로그에 기록했다(미해결).

3. **`-f` 자기 매칭.** `pkill -f`/`pgrep -f`는 프로세스의 **전체 명령줄**을 패턴과 비교한다.\
패턴 문자열을 인자로 가진 내 셸(`bash -c "pkill -f job.py"`)이나 SSH 명령줄도 그 문자열을 포함하므로 **나 자신이 매칭**된다 — 대상은 살고 내 세션이 죽는다(exit 144, SSH 255).\
대괄호 트릭 `[j]ob.py`: 정규식으로는 `j` 한 글자 클래스라 `job.py`에 매칭되지만, 내 명령줄에 적힌 것은 리터럴 `[j]ob.py`라서 그 정규식에 **매칭되지 않는다**.\
`pgrep -P <pid>`는 문자열이 아니라 **부모 pid 관계**로 찾으므로 명령줄 내용과 무관하다. 종료 전에 조상 체인(`ps -o ppid=`)을 따라가 **내가 대상의 자손이 아닌지**도 확인한다.
   > **self-match** — 프로세스 목록을 문자열로 검색할 때 검색 명령 자신이 결과에 포함되는 현상.

4. **nohup의 한계.** 터미널(SSH) 세션이 끊기면 커널/세션 관리자가 그 세션의 그룹에 **SIGHUP**을 보낸다.\
`nohup`은 SIGHUP을 **무시**하게 할 뿐, 프로세스는 여전히 그 세션·그룹에 속하고 stdin도 터미널에 연결돼 있어 세션 정리 대상이 될 수 있다(실측: nohup rsync가 SIGHUP 계열 코드로 사망, nohup 브리지가 로그아웃과 함께 사망).\
`setsid cmd < /dev/null &`는 **새 세션**으로 옮겨 터미널 시그널에서 떼어내고 stdin도 끊는다.\
주의: 셸이 찍는 `[N] Done`은 setsid 런처가 끝났다는 뜻일 뿐 — 실제 작업은 init으로 reparent돼 돌고 있으므로 pid로 확인한다.\
상시 실행은 서비스 매니저 유닛으로 두는 것이 정석이다.

5. **pty master 보유자의 죽음.** setsid는 자식을 **관찰자(SSH)의 프로세스 그룹**에서 분리한다 — 그래서 채널 종료 SIGHUP에는 살아남았다(대조군 실측).\
그러나 자식의 제어 터미널이 **데몬이 연 pty**라면, 데몬이 죽는 순간 master fd가 닫히고 커널이 그 터미널의 세션에 **hangup(SIGHUP)**을 보낸다.\
원인은 서비스 매니저의 kill 정책이 아니라 **제어 터미널 hangup**이었고, "setsid로 데몬 재시작에도 안전"이라던 코드 주석 여러 곳이 반대로 단언하고 있어 정정했다.\
"데몬 재시작 = 소유 세션도 사망"을 계약으로 정정하고 대안(master fd 놓기·pty 없이 스폰·재기동 후 인수)을 대가와 함께 기록했으며(설계 변경은 없음), 불변식(자식이 데몬의 세션·그룹을 떠났는가)은 `/proc/<pid>/stat`의 세션 필드로 테스트에서 단언했다.

6. **SIGKILL과 별세션 자식.** SIGKILL은 프로세스가 **잡을 수 없는** 신호라 서버의 종료 훅(자식 정리 코드)이 실행되지 않는다.\
프로세스 그룹 kill은 서버와 같은 그룹만 죽이는데, 서버가 PTY 자식을 `setsid`로 **새 세션**에 띄웠기 때문에 그 자식들은 그룹 밖이다.\
그래서 자식 정리는 서버의 **graceful 종료 경로**에만 의존한다 → 런처는 `SIGTERM`을 보내고 `wait`로 기다려 서버의 종료 훅(자식 terminate → 유예 → kill)이 돌게 한다.\
또 **내가 띄운 서버만** 정리하도록 소유 플래그를 둬, 이미 포트를 점유하던 외부 서버를 죽이지 않게 했다.

7. **원격 종료와 대기 루프.** 로컬 `Popen(ssh …).terminate()`는 **로컬 ssh 프로세스**만 끝낸다.\
TTY 없이 실행한 원격 명령은 SSH 연결이 끊겨도 SIGHUP을 받지 않아 계속 실행됐고, 측정 부하가 오염됐다(교차 검증 합계가 어긋나서 발견).\
원격 작업에 **이름을 붙여 직접 종료**하고, **실제로 끝났는지 확인**하고, 아니면 예외를 던진다 — "보냈다"와 "끝났다"를 가른다.\
대기 루프도 같은 원리다 — 종료 조건이 실제 완료 신호와 연결되지 않으면(존재할 수 없는 파일, 자기 자신을 매칭하는 `pgrep -f`) 루프는 대상과 무관하게 **영원히 돈다**(실측: 배경 루프 5개가 1시간 반 가까이 잔존). 폴링 대신 런타임의 완료 알림에 의존한다.

## 문제 구조 (추상화 코드)

### 변형 A — 부모만 kill / 논리적 취소
① 문제 코드
```python
proc = Popen(["sh", "-c", cmd])              # 셸 → 손자
try: proc.wait(timeout=T)
except TimeoutExpired: proc.kill()           # 셸만 죽음 → 손자 고아
def cancel(): state.current = None           # 논리적 취소 — fork된 프로세스는 계속
```
② 고친 코드
```python
proc = Popen(["sh", "-c", cmd], start_new_session=True)   # 새 그룹
active.append(proc)
def kill_tree(p):
    os.killpg(p.pid, SIGTERM); sleep(GRACE); os.killpg(p.pid, SIGKILL)  # 권한 다른 자손은 EPERM (한계)
    p.wait()
def cancel(): [kill_tree(p) for p in active]
```
무엇이 깨졌나: 종료 단위가 그룹이 아니라 프로세스 하나였다.\
같은 구조: 검증 러너 타임아웃이 자식 그룹을 안 죽이고 오류 분기에서 kill 누락 → setsid + killpg · 실행 중 앱 교체 시 앱만 죽여 자식이 고아 → `pgrep -P` 트리 수집 후 TERM → KILL.

### 변형 B — `-f` 자기 매칭
① 문제 코드
```bash
pkill -f job.py                        # 이 명령줄(또는 ssh "…pkill -f job.py")도 매칭
until ! pgrep -f 'worker exec'; do sleep 5; done   # 루프 자신을 매칭 → 무한
```
② 고친 코드
```bash
pkill -f '[j]ob.py'                    # 정규식은 대상에만, 리터럴 명령줄엔 불일치
ps -eo pid,args | awk '/[w]orker/'         # 검증 시 오탐 방지
kids=$(pgrep -P "$root")                   # 또는 pid 관계로 트리 순회
```
무엇이 깨졌나: 문자열 검색 대상에 검색하는 자신이 포함됐다.\
같은 구조: 재배포 스크립트의 self-match 주의(대상 부재로 우회) · 데스크톱 앱 재기동 스크립트의 자기 셸 kill.

### 변형 C — 세션·터미널 종료와 SIGHUP
① 문제 코드
```bash
nohup long_batch > out.log 2>&1 &          # SIGHUP 무시뿐 — 세션·stdin 묶임
rsync -a /src/ /dst/ &                     # 도구 타임아웃·SSH 종료에 함께 사망
```
② 고친 코드
```bash
setsid long_batch > out.log 2>&1 < /dev/null &   # 새 세션 + stdin 분리
pgrep -f '[l]ong_batch'                           # "[N] Done"은 런처 종료일 뿐 — 실제 확인
# 상시 실행은 서비스 유닛(Restart=on-failure)
```
무엇이 깨졌나: 작업이 호출한 세션(터미널·도구 호출)의 수명에 묶여 있었다.\
같은 구조: 수 시간짜리 인덱스 배치가 SSH 끊김으로 중단(nohup 미사용) · 도구 타임아웃보다 긴 백필 → setsid+nohup 분리 + 완료 모니터.

### 변형 D — pty master를 쥔 데몬의 죽음
① 문제 코드
```rust
// 자식: setsid + 데몬이 연 pty를 제어 터미널로
// 주석: "setsid 했으므로 데몬 재시작에도 세션 생존"   ← 틀림
let child = pty.spawn(cmd)?;
```
② 고친 코드
```rust
let child = pty.spawn(cmd)?;                         // 내부: fork → setsid → TIOCSCTTY
assert_ne!(session_of(child.pid()), session_of(self_pid()));  // 불변식: 관찰자 세션 이탈
// 데몬 재시작 = 소유 세션도 사망 (대안: master fd 놓기 / pty 없이 스폰 / 재기동 후 인수 — 대가와 함께 기록)
// 주석 정정: 데몬 종료 → master 닫힘 → 제어 터미널 hangup → SIGHUP
```
무엇이 깨졌나: setsid가 막는 신호(관찰자 그룹)와 못 막는 신호(제어 터미널 hangup)를 혼동했다.

### 변형 E — SIGKILL / 그룹 kill로 정리 경로 우회
① 문제 코드
```bash
kill -KILL "$server_pid"        # 종료 훅 미실행
kill -- -"$server_pgid"         # 별세션 자식은 그룹 밖 → 고아
```
② 고친 코드
```bash
cleanup() {
  [ "$started" = 1 ] && [ -n "$server_pid" ] || return 0   # 내가 띄운 것만
  kill -TERM "$server_pid" 2>/dev/null || true             # graceful → 종료 훅이 자식 정리
  wait "$server_pid" 2>/dev/null || true                   # 회수
}
trap cleanup EXIT INT TERM
```
무엇이 깨졌나: 자식 정리를 맡은 코드 경로를 신호 선택으로 건너뛰었다.

### 변형 F — 원격 종료와 만족 불가 대기
① 문제 코드
```python
p = Popen(["ssh", host, "docker run load-gen ..."]); p.terminate()   # 로컬 ssh만 종료
```
```bash
until [ -f /nonexistent ]; do sleep 30; done &                       # 영원히 거짓
```
② 고친 코드
```python
p = Popen(["ssh", host, f"docker run --name {name} load-gen ..."])
# ...
run(["ssh", host, f"docker kill {name}"])
if still_running(host, name): raise RuntimeError("remote load not stopped")   # 실제 종료 확인
```
```bash
# 폴링 루프 대신 런타임(백그라운드 작업) 완료 알림에 의존
```
무엇이 깨졌나: 종료 "요청"을 종료 "사실"로 간주했고, 종료 조건이 실제 완료 신호와 무관했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
