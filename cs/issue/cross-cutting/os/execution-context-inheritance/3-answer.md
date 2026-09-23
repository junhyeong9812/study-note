# cs/issue/os/execution-context-inheritance — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `environment-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **표식 변수 상속.** 자식은 (스폰 시 따로 지정하지 않으면) 부모 환경을 그대로 받는다.\
오케스트레이터(앱·데몬)가 다른 에이전트 세션 안에서 실행되면, 그 세션의 "나는 자식 세션" 표식 변수가 오케스트레이터를 거쳐 스폰된 도구에까지 새어 들어간다.\
도구는 자신을 **중첩 실행**으로 인식해 다른 모드로 동작했다 — 한 경로에서는 "중첩 금지"로 세션 생성이 내부 오류로 실패했고, 다른 경로에서는 터미널에는 정상으로 떴는데 **전사 파일을 쓰지 않아** 타임라인이 영원히 비었다.\
에러 없이 산출물만 없으므로 "제출이 안 됐다" 같은 엉뚱한 원인으로 오판하기 쉽다(조용한 실패).\
진단 단서는 실행 중 프로세스의 환경(`/proc/<pid>/environ`)과 자식의 stderr 노출이었고, 교정은 스폰 전에 표식 변수들을 **스크럽**하는 것이다.

2. **실행 방식별 PATH·TERM.** 대화형 로그인 셸은 rc 파일을 읽어 `~/.local/bin` 같은 사용자 경로를 PATH에 넣고, 터미널 에뮬레이터가 `TERM`을 준다.\
GUI 런처로 실행한 프로그램은 데스크톱 세션의 환경을 받는데, 대화형 셸 rc(`.bashrc` 등)는 적용되지 않는 것이 일반적이고 `TERM`이 없다(로그인 프로필 적용 여부는 배포판·데스크톱 환경마다 다름).\
서비스 매니저 유닛은 **매니저의 기본 환경 + 유닛에 적은 것**만 받는다 — 기본 PATH는 `/usr/local/bin:/usr/bin` 류의 시스템 경로로, 셸 rc가 추가하던 사용자 경로는 없다(정확한 값은 배포판·매니저 설정에 따라 다름).\
도구가 띄우는 비대화 셸도 rc·credential helper가 적용되지 않는다.\
결과: 홈 설치 CLI를 못 찾음, 이름이 같은 다른 바이너리(다른 python·다른 유틸)가 잡힘, PTY 자식 TUI의 escape 시퀀스가 깨짐.\
재현은 `env -i PATH=/usr/bin:/bin`으로 GUI·서비스 환경을 흉내 낸다.
   > **로그인 셸** — 사용자 로그인 시 프로필·rc 파일을 읽어 대화형 환경을 구성하는 셸. 서비스·GUI 런처는 이 단계를 거치지 않는다.

3. **해석됨 ≠ 실행 가능.** 실행 파일이 `#!/usr/bin/env node` shebang을 가진 스크립트(또는 그 심링크)면, 커널은 `env`를 실행하고 `env`는 **자식의 PATH**에서 인터프리터를 찾는다.\
스크립트 자체는 절대경로로 찾았어도 인터프리터가 버전 관리자 경로에만 있으면 최소 PATH에서는 못 찾아 127로 죽는다.\
착수 스모크는 "바이너리 해석"만 확인하고 실제 실행은 안 해서 놓쳤다(개발 기계엔 시스템 인터프리터가 있어 우연히 생존).\
교정은 해석된 실행 파일의 **bin 디렉토리를 자식 PATH 선두에 추가**하는 순수 함수 + 실제 스폰 대조(127 → 0)였다.

4. **보호 키.** 호출자 env/argv를 그대로 병합하면 데몬이 장부로 의존하는 키(설정 디렉토리·홈·훅 포트·세션 id 인자)를 호출자가 덮어써 **데몬 불변식이 깨진다**.\
병합 순서를 "호출자 값 → 데몬 값"으로 두어 보호 키는 **데몬 값이 최종**이 되게 하고, 중복 인자(세션 id 두 번)도 거절한다.\
거절한 값은 조용히 버리지 않고 **통지(Notice)**로 보고한다 — 호출자가 "적용됐다"고 오해하지 않게.

5. **전역 env와 다중 테넌트.** 환경 변수는 **프로세스 전역** 상태다.\
한 데몬이 여러 계정을 동시에 서비스하면서 계정별 홈을 env로 고르면, 요청끼리 서로의 값을 덮어쓴다.\
또 어떤 함수는 설정 디렉토리 변수를 무시하고 `$HOME`만 읽어 "env 주입만으로 계정 전환"이라는 가정이 부분 반증됐다.\
교정: 데몬 안에서는 홈을 **인자로 받는** 경로 함수를 단일 출처로 쓰고, env로 홈을 넘기는 것은 **스폰되는 자식에게만** 한다.

6. **cwd 앵커와 루트 전제.** 에이전트 도구의 Bash는 `cd`가 다음 명령에도 **영속**되고, 훅이 받는 `cwd`도 세션 시작 디렉토리가 아니라 그 현재 디렉토리를 따라간다.\
상태 파일을 `$CWD/...`로 찾으면 하위 디렉토리에서 찾다 "없음 → 초기 상태"로 판단해 **거짓 차단**했고, 그 자리에 새 상태 파일(유령)을 만들었으며, 결국 무관한 저장소 트리에 부산물이 떨어져 커밋에 섞였다.\
교정: cwd부터 **조상으로 올라가며 기존 상태 파일을 앵커로** 채택하고, 없으면 cwd가 아니라 **cwd가 속한 워크트리 루트**로 폴백하며, 상태 디렉토리 생성을 한 함수로 모으고 자기 자신을 무시하는 ignore 파일을 같이 만든다.\
"저장소 루트 기준 상대경로에 `docs/`가 있는가"로 판정하는 규칙은 ① 저장소가 없는 작업 공간(루트를 못 찾음 → 가장 보수적 분기) ② `docs/` **자체가** 독립 저장소 루트인 배치(상대경로에서 `docs/`가 사라짐)에서 뒤집혀, 게이트를 여는 문서 쓰기까지 막는 **교착**이 났다.\
같은 시스템의 다른 훅은 절대경로 패턴으로 판정해 기준이 서로 달랐다.

7. **플랫폼 주입과 암묵 상속.** 오케스트레이터는 (기본 설정에서, 파드 생성 시점에 이미 존재하던) 같은 네임스페이스의 서비스마다 `<NAME>_PORT=tcp://…` 형식 변수를 파드에 **자동 주입**한다(서비스 링크 주입을 끄는 옵션이 있다) — 서비스 이름이 앱 설정 변수 접두사와 같으면 설정값이 URL 문자열로 덮여 숫자 파싱이 실패했다(서비스 이름 변경 + 설정 명시로 해결).\
어떤 언어의 프로세스 API는 env 목록이 **nil이면 부모 환경 전체를 상속**하므로(빈 목록과 nil을 구분), 주입값을 한 번도 append하지 않아 슬라이스가 nil로 남는 순간 격리가 무음으로 풀린다. 컴포즈 도구는 작업 디렉토리의 `.env`를 자동으로 읽는다.\
공통 교훈: 실행 문맥에는 **내가 넣지 않은 값이 들어온다**. 금지 목록(이것만 빼자)은 새 주입 경로를 못 막는다 → **허용 집합(PATH + 명시 주입값)**으로 env를 구성하고, 자동 로드 파일의 부재를 실행 직전에 단언한다.

## 문제 구조 (추상화 코드)

### 변형 A — 부모 세션 표식 상속과 호출자 덮어쓰기
① 문제 코드
```rust
let mut cmd = Command::new(agent_bin);           // 부모 env 전체 상속 (중첩 표식 포함)
for (k, v) in caller_env { cmd.env(k, v); }      // 데몬 소유 키도 덮어씀
cmd.args(caller_args);                            // 중복 --session-id
```
② 고친 코드
```rust
const NESTED_MARKERS: &[&str] = &["PARENT_SESSION", "PARENT_CHILD_SESSION", "PARENT_SESSION_ID", "PARENT_ENTRYPOINT"];
const PROTECTED_ENV: &[&str] = &["CONFIG_DIR", "TOOL_HOME", "HOOK_PORT", /* ... */];
let mut cmd = Command::new(agent_bin);
for k in NESTED_MARKERS { cmd.env_remove(k); }                  // 스크럽
for (k, v) in caller_env {
    if PROTECTED_ENV.contains(&k.as_str()) { notices.push(rejected(k)); continue; }  // 통지
    cmd.env(k, v);
}
for (k, v) in daemon_env { cmd.env(k, v); }                     // 데몬 값이 최종
```
무엇이 깨졌나: 부모 세션의 표식이 자식의 동작 모드를 바꿨고, 호출자 입력이 데몬 불변식을 덮었다.\
같은 구조: 앱 시작 시 전역에서 표식 4종 제거 · 스모크 하네스도 같은 제거로 앱과 동일 조건 재현 · 원격 데몬 스모크에서 스크럽이 숨은 필수 요소로 확인.

### 변형 B — 런처·서비스의 TERM 부재
① 문제 코드
```rust
let mut b = PtyCommand::new(shell);     // TERM 미지정 → 부모(GUI 런처 = TERM 없음) 상속
```
② 고친 코드
```rust
let mut b = PtyCommand::new(shell);
b.env("TERM", "xterm-256color");        // 명시 (env 전체를 지우지 않고 두 값만)
b.env("COLORTERM", "truecolor");
for (k, v) in user_env { b.env(k, v); } // 사용자 값은 그 뒤(나중 값 우선)
```
무엇이 깨졌나: 개발 셸이 우연히 주던 `TERM`이 프로덕션 런처에는 없었다.\
선택하지 않은 방법: 런처 스크립트에서 export(다른 실행 경로가 빠짐) · 앱 전역 env 변경(부작용).

### 변형 C — PATH 차이 (최소 PATH·shebang·이름 충돌)
① 문제 코드
```python
subprocess.run(["tool", ...])                    # 서비스/GUI PATH엔 ~/.local/bin 없음
subprocess.run(["python", "-m", ...])            # 배포판에 python 이름 없음 → ENOENT
spawn(find_tool())                               # 스크립트는 찾았지만 shebang 인터프리터가 PATH에 없음 → 127
```
② 고친 코드
```python
TOOL_BIN = os.getenv("TOOL_BIN", DEFAULT_ABS_PATH)          # 절대경로 + 환경 주입
def child_path(tool: Path, inherited: str) -> str:            # 인터프리터 동반 디렉토리 선두
    return f"{tool.parent}:{inherited}"
def find_python():                                            # 이름이 아니라 기능으로 선택
    for c in candidates:
        if run([c, "-c", "import needed_modules"]).returncode == 0: return c
```
```ini
# 서비스 유닛: 로그인 셸이 유효한 설치 시점에 경로를 고정
[Service]
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=TOOL_BIN=<설치 시 command -v 결과>
ExecStart=<실제 설치 경로로 치환>
```
무엇이 깨졌나: 실행 파일·인터프리터를 이름으로 찾았는데 실행 방식마다 PATH가 달랐다.\
같은 구조: 비대화 셸에서만 홈 CLI 실패(원인 규명만, 조치 미기록) · 유닛 템플릿 경로와 실제 설치 경로 불일치 → 치환 후 검증 · 검증 명령을 설치 전에 돌려 항상 실패 → 설치 후로 이동 · 원격 대상에 빌드 도구 없음 → 로컬 빌드 산출물 전송 모드 · 사용자 서비스는 사용자 매니저 수명에 묶임 — 기본 동작은 마지막 세션 종료 시 사용자 매니저가 멈추므로(원문의 로그아웃 후 생존 관측은 조건 의존), 로그아웃·재부팅 생존을 보장하려면 linger 필요.

### 변형 D — 프로세스 전역 env로 테넌트 선택
① 문제 코드
```rust
fn projects_root() -> PathBuf { PathBuf::from(env::var("HOME").unwrap()).join(".tool/projects") }
// 데몬이 계정마다 env::set_var("HOME", ...) → 동시 요청끼리 덮어씀
```
② 고친 코드
```rust
fn projects_root(home_override: Option<&Path>) -> PathBuf { /* 인자 우선 */ }
// 데몬 안: 계정 홈을 인자로 전달 / 자식 스폰 시에만 cmd.env("HOME", account_home)
```
무엇이 깨졌나: 요청마다 달라야 하는 값을 프로세스 전역 상태에 넣었다.

### 변형 E — cwd·저장소 루트에 앵커링한 상태·판정
① 문제 코드
```sh
state="$CWD/.state/$SID"                                  # 영속 cd를 따라 하위 디렉토리로
rel=${path#$(git -C "$dir" rev-parse --show-toplevel)/}
[[ $rel == docs/* || $rel == */docs/* ]] && exempt        # docs 자체가 루트면 rel=plans/... → 비면제
```
② 고친 코드
```sh
state=$(find_ancestor_state "$CWD" "$SID") \
  || state="$(env -u GIT_DIR -u GIT_WORK_TREE git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || echo "$CWD")/.state/$SID"
state_ensure_dir "$(dirname "$state")"                    # 생성 단일화 + 자기무시 ignore 파일(*)
# 루트 판정: 저장소 없는 작업 공간엔 저장소 초기화 + 셀프테스트로 판정 결과 상시 단언
# docs가 루트인 배치: 루트 자체가 docs인 경우를 면제 조건에 포함
```
무엇이 깨졌나: 세션 도중 바뀌는 cwd와 배치마다 다른 저장소 루트를 고정 앵커로 가정했다.\
같은 구조: 상태 파일 상대경로 해석 실패로 일시 차단(cwd 복귀로 해소) · 상대 경로 출력이 브라우저에서 `file://` 뒤 첫 세그먼트를 호스트로 해석해 빈 페이지 → 절대경로 고정 · 임시 HTML 위치가 원본과 달라 상대 이미지 경로가 안 풀림.

### 변형 F — 플랫폼 주입·암묵 상속·해석 주체 차이
① 문제 코드
```yaml
kind: Service
metadata: { name: app-master }       # → 파드에 APP_MASTER_PORT=tcp://... 자동 주입 → 설정 충돌
```
```go
cmd := exec.Command("compose", "up")
cmd.Env = injected                    // injected가 nil(append 0회)이면 → 부모 env 전체 상속, .env 자동 로드
```
② 고친 코드
```yaml
metadata: { name: app-master-svc }   # 설정 접두사와 겹치지 않는 이름 + 설정 명시
```
```go
cmd.Env = append([]string{"PATH=" + checkedPath}, injected...)   // 허용 집합
assertNoDotEnv(projectDir)                                     // 기록 전 + 실행 직전 이중 단언
```
무엇이 깨졌나: 내가 넣지 않은 값(플랫폼 주입·암묵 상속·자동 로드)이 실행 문맥에 들어왔다.\
같은 구조: 컨테이너 안에서 호스트 데몬 소켓으로 명령 → 경로 해석은 호스트 데몬이 하므로 호스트 기준 경로 필요, CLI 플러그인·동적 링크 바이너리는 컨테이너 userland와 별개 → 최종적으로 호스트 서비스로 전환 · 파일 전송 도구가 실행 비트를 보존하지 않아 서비스가 "실행 불가"로 실패 → 실행 비트를 저장소에 커밋 · 유닛 파일 교체 후 reload 없이 시작 → reload → restart 순서 명시.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
