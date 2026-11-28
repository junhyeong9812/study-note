# python/python-networking/11 — 프로세스 관리: subprocess와 시그널 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `HELLO` — 셸이 파이프를 해석한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
셸 파이프: HELLO
```

`shell=True` 를 빼면 문자열 전체가 하나의 프로그램 이름으로 다뤄진다.
`echo "Hello" | tr a-z A-Z` 라는 이름의 프로그램은 없으니 실행이 실패하고, `|` 도 파이프로 해석되지 않는다.

**왜 그런가**
셸이 문자열을 해석해 `echo "Hello"` 의 출력 `Hello` 를 `tr a-z A-Z` 에 흘린다.
`tr` 은 소문자를 대문자로 바꾸므로 `HELLO` 가 되고, `.strip()` 이 끝의 줄바꿈을 걷어 낸다.
파이프 같은 셸 문법은 셸이 있어야 해석된다 — 2-summary 「동작 방식 (2)」.
`shell=True` 없는 문자열이 프로그램 이름 하나로 다뤄진다는 대목은 (원본에 근거 없음 — 추론).

### 2. `['hello', 'python', 'world']` — 단어로 쪼개진 뒤 정렬된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
파이프 체이닝: ['hello', 'python', 'world']
```

**왜 그런가**
`echo` 가 `hello world python` 을 내보낸다.
`tr ' ' '\n'` 이 공백을 줄바꿈으로 바꿔 `hello` · `world` · `python` 세 줄을 만든다.
`sort` 가 줄을 정렬해 `hello` · `python` · `world` 순서가 된다.
`communicate()[0]` 이 그 출력을 받고, `.strip().split(chr(10))` 이 줄마다 나눈 리스트를 만든다 — 2-summary 「동작 방식 (5)」.
정렬 순서는 로케일에 따라 달라질 수 있지만, 이 경우는 소문자 영단어뿐이라 차이가 나지 않을 것으로 본다 (원본에 근거 없음 — 추론).

### 3. `terminate()` 는 불리지 않고, 종료 코드는 0

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
관리된 프로세스 출력: started
done
프로세스 종료 코드: 0
```

**왜 그런가**
본문의 `communicate(timeout=5)` 가 출력을 다 모으고 자식이 끝날 때까지 기다린다.
그래서 `__exit__` 에 이르렀을 때 `poll()` 은 `None` 이 아니고, `terminate()` 가지에 들어가지 않는다.
자식은 `started` 와 `done` 을 찍고 정상으로 끝나므로 종료 코드는 0 이다.
`output.strip()` 은 양끝만 걷으므로 두 줄 사이의 줄바꿈은 남는다.
`with` 뒤에도 `proc` 이름이 살아 있어 `returncode` 를 읽을 수 있다 — 2-summary 「동작 방식 (7)」.

### 4. 예외가 나지 않는다 — `returncode` 를 직접 봐야 한다

`check=True` 가 없으면 실패한 명령도 예외 없이 `CompletedProcess` 를 돌려준다.
실패를 알아채려면 `result.returncode` 가 0 이 아닌지 직접 확인해야 한다.
`check=True` 를 주면 그 확인을 `CalledProcessError` 로 대신해 준다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 5. 리스트의 각 칸은 셸이 해석하지 않는 「인자 하나」라서

리스트로 넘기면 셸을 거치지 않고, 각 칸이 프로그램에 그대로 한 인자로 들어간다.
파일 이름에 `;` · `|` 같은 글자가 들어 있어도 명령으로 해석되지 않는다.
`shell=True` 문자열에 사용자 입력을 이어 붙이면 셸이 그 글자를 해석해, 사용자가 다른 명령을 끼워 넣을 수 있다(셸 인젝션).
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 6. 뒷 단계가 먼저 끝나도 앞 단계가 `SIGPIPE` 를 받지 못해 남을 수 있다

앞 단계의 출력 파이프는 다음 단계와 부모가 함께 쥐고 있다.
부모가 계속 쥐고 있으면, 다음 단계가 먼저 끝나도 그 파이프를 읽을 쪽이 아직 열려 있는 셈이다.
그러면 앞 단계는 「읽는 쪽이 사라졌다」는 `SIGPIPE` 를 받지 못하고 계속 남을 수 있다.
부모가 닫으면 읽는 쪽이 다음 단계 하나뿐이 된다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」 (원본 주석 「SIGPIPE 처리를 위해 상위 stdout close」를 풀어 쓴 것).

### 7. 잡을 수 있는 것은 `SIGTERM` — 그래서 `kill` 은 마지막 수단이다

`SIGTERM` 은 받는 쪽이 핸들러로 잡아 정리할 수 있다.
`SIGKILL` 은 처리할 수 없는 시그널이라 핸들러를 걸 수 없고, 받으면 무조건 끝난다.
그래서 먼저 `terminate()` 로 정리할 기회를 주고, 5초 안에 끝나지 않을 때만 `kill()` 로 확실히 끝낸다.
처음부터 `kill()` 하면 자식이 임시 파일 정리 같은 마무리를 할 틈이 없다.
근거: 2-summary 「동작 방식 (6)」 시그널 표 · 「동작 방식 (7)」 · 「어디서 틀리나 3」.

### 8. 안 넘기면 부모 환경 그대로, 새 사전만 넘기면 부모 환경을 전부 잃는다

`env` 를 넘기지 않으면(`env=None`) 자식은 부모 환경을 그대로 물려받는다.
`env=` 를 주면 그 사전이 자식 환경 전체가 된다.
`{'MY_VAR': 'custom_value'}` 만 넘기면 자식은 부모의 다른 환경 변수를 하나도 받지 못한다.
그래서 `os.environ.copy()` 로 복사한 뒤 바꿀 것만 고친다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 9. `run` 은 끝날 때까지 기다리는 단계를 묶어 준다

`Popen` 은 자식을 띄우고 곧바로 돌아온다.
`run` 은 띄운 뒤 자식이 끝날 때까지 기다리고, 붙잡은 출력과 종료 코드를 `CompletedProcess` 로 돌려준다(원본 주석: 「run은 wait까지 한 번에」).
출력을 나오는 대로 받으려면 자식이 아직 도는 동안 `proc.stdout` 을 읽어야 하므로, 곧바로 돌아오는 `Popen` 이 필요하다.
`run` 은 끝난 뒤에야 결과를 주므로 그 중간을 볼 수 없다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」.

### 10. 둘 다 「바꿔 쓰고 끝에 원상태로 돌려놓기」다

`signal.signal()` 은 이전 핸들러를 돌려주므로, 그것을 받아 두었다가 다시 등록하면 원상태로 돌아간다.
`ManagedProcess` 도 `__enter__` 에서 자원(자식 프로세스)을 얻고 `__exit__` 에서 반드시 정리한다.
둘 다 시작할 때 바꾸고 끝날 때 되돌려, 블록 밖에 흔적을 남기지 않는다는 생각이다.
차이는, 시그널 예제는 되돌리기를 손으로 부르고 `with` 는 예외가 나도 `__exit__` 을 불러 준다는 점이다.
근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (7)」 · 「어디서 틀리나 10」 (두 패턴을 견주는 대목은 원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. subprocess · 시그널 · 안전한 종료를 한 스크립트로 엮기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `echo` 실행, 출력 · 종료 코드 | `subprocess.run(['echo', 'Hello subprocess'], capture_output=True, text=True)` · `result.returncode` |
| 2. 셸 파이프 | `subprocess.run('echo "Hello" \| tr a-z A-Z', shell=True, ...)` |
| 3. stdout · stderr 분리 | `capture_output=True` · `result.stdout` · `result.stderr` |
| 4. 실패를 예외로 | `subprocess.run(['false'], check=True)` · `except subprocess.CalledProcessError as e` |
| 5. 1초 제한 | `subprocess.run(['sleep', '10'], timeout=1)` · `except subprocess.TimeoutExpired` |
| 6. stdin 주입 | `input='hello world'` |
| 7. 환경 변수 | `env = os.environ.copy()` · `env['MY_VAR'] = 'custom_value'` · `env=env` |
| 8. 줄 단위 읽기 | `subprocess.Popen(..., stdout=subprocess.PIPE, text=True)` · `for line in proc.stdout` · `proc.wait()` |
| 9. 세 단계 파이프 | `p1` · `p2(stdin=p1.stdout)` · `p3(stdin=p2.stdout)` · `p1.stdout.close()` · `p2.stdout.close()` · `p3.communicate()[0]` |
| 10. 핸들러 | `def signal_handler(signum, frame)` · `signal.Signals(signum).name` |
| 11. 등록 · 송신 · 복원 | `hasattr(signal, 'SIGUSR1')` · `original = signal.signal(...)` · `os.kill(os.getpid(), signal.SIGUSR1)` · `signal.signal(signal.SIGUSR1, original)` |
| 12. 시그널 목록 | `signal_info` · `hasattr(signal, name)` · `getattr(signal, name)` |
| 13. 보관 · 시작 | `ManagedProcess.__init__` · `__enter__` 의 `subprocess.Popen(self.cmd, **self.kwargs)` |
| 14. 안전한 종료 | `__exit__` 의 `poll() is None` · `terminate()` · `wait(timeout=5)` · `kill()` · `wait()` |
| 15. 사용 · 종료 코드 | `with ManagedProcess(...) as proc` · `proc.communicate(timeout=5)[0]` · `proc.returncode` |
| 16. 핵심 정리 | 마지막 `print` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/process-management.py`

```python
# [네트워크 & 시스템] 프로세스 관리: subprocess와 시그널
# 설명: subprocess로 외부 프로세스 실행, 파이프, 시그널 처리
# 팁: subprocess.run()은 간단한 명령 실행, Popen은 스트리밍이나 파이프 체이닝에 사용한다. shell=True는 셸 인젝션 위험이 있으므로 사용자 입력에 쓰지 않는다. 프로세스 종료 시 terminate(SIGTERM) 후 타임아웃이면 kill(SIGKILL)하는 패턴이 안전하다.

"""프로세스 관리: subprocess, Popen, 시그널"""
# subprocess: 자식 프로세스 생성/제어 (os.system 대체)
import subprocess
# signal: POSIX 시그널 처리
import signal
# sys: 표준 입출력
import sys
# os: PID, kill 등
import os

# === 1. subprocess.run() - 기본 ===
print("=== 1. subprocess.run() ===")

# 간단한 명령 실행
# 리스트 인자 권장 (셸 미경유 → 인젝션 안전)
result = subprocess.run(['echo', 'Hello subprocess'], capture_output=True, text=True)
# stdout: 표준 출력, text=True면 str
print(f"stdout: {result.stdout.strip()}")
# returncode: 0=성공
print(f"returncode: {result.returncode}")

# 셸 명령 (파이프 사용 시)
# shell=True: 셸 메타문자(|, > 등) 사용 가능. 사용자 입력엔 절대 금지
result = subprocess.run('echo "Hello" | tr a-z A-Z', shell=True, capture_output=True, text=True)
print(f"셸 파이프: {result.stdout.strip()}")

# 에러 처리
# stderr 분리 캡처
result = subprocess.run(
    ['python3', '-c', 'import sys; print("out"); print("err", file=sys.stderr)'],
    capture_output=True, text=True
)
print(f"\nstdout: '{result.stdout.strip()}'")
print(f"stderr: '{result.stderr.strip()}'")

# check=True: 비정상 종료 시 예외
try:
    # false: 항상 returncode 1로 종료하는 명령
    subprocess.run(['false'], check=True)
except subprocess.CalledProcessError as e:
    # check=True에서 returncode≠0이면 예외
    print(f"\nCalledProcessError: returncode={e.returncode}")

# === 2. subprocess.run() 옵션들 ===
print("\n=== 2. 유용한 옵션 ===")

# 타임아웃
try:
    # timeout 초과 시 SIGKILL + TimeoutExpired
    subprocess.run(['sleep', '10'], timeout=1)
except subprocess.TimeoutExpired:
    print("타임아웃 발생 (1초 초과)")

# 입력 전달 (stdin)
# input 파라미터로 stdin 데이터 주입
result = subprocess.run(
    ['python3', '-c', 'print(input().upper())'],
    input='hello world',
    capture_output=True, text=True
)
print(f"stdin 입력 결과: {result.stdout.strip()}")

# 환경 변수
# 부모 환경 복사 후 수정 (env=None이면 부모 그대로 상속)
env = os.environ.copy()
env['MY_VAR'] = 'custom_value'
result = subprocess.run(
    ['python3', '-c', 'import os; print(os.environ.get("MY_VAR", "none"))'],
    capture_output=True, text=True, env=env
)
print(f"환경 변수: {result.stdout.strip()}")

# === 3. Popen - 스트리밍/비동기 ===
print("\n=== 3. Popen (스트리밍) ===")

# 실시간 출력 읽기
# Popen: 프로세스를 띄우고 즉시 반환 (비동기). run은 wait까지 한 번에
proc = subprocess.Popen(
    ['python3', '-c', 'import time; [print(i, flush=True) or time.sleep(0.01) for i in range(5)]'],
    stdout=subprocess.PIPE, text=True
)
lines = []
# stdout iterable: 한 줄씩 스트리밍 읽기
for line in proc.stdout:
    lines.append(line.strip())
# 종료 대기
proc.wait()
print(f"실시간 읽기: {lines}")

# 파이프 체이닝
# 셸의 echo | tr | sort 를 파이썬에서 직접 구성
p1 = subprocess.Popen(['echo', 'hello world python'], stdout=subprocess.PIPE)
# stdin=p1.stdout: 이전 단계의 stdout을 stdin으로 연결
p2 = subprocess.Popen(['tr', ' ', '\n'], stdin=p1.stdout, stdout=subprocess.PIPE)
p3 = subprocess.Popen(['sort'], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
# SIGPIPE 처리를 위해 상위 stdout close (관용 패턴)
p1.stdout.close()
p2.stdout.close()
# communicate: 모든 출력 수집 + wait
output = p3.communicate()[0]
print(f"파이프 체이닝: {output.strip().split(chr(10))}")

# === 4. 시그널 처리 ===
print("\n=== 4. 시그널 처리 ===")

# 시그널 핸들러 등록
# (signum, frame) 시그니처 필수
def signal_handler(signum, frame):
    # signal.Signals 열거형으로 이름 조회
    sig_name = signal.Signals(signum).name
    print(f"  시그널 수신: {sig_name} ({signum})")

# SIGUSR1 핸들러 등록 (Unix)
# 윈도우에는 SIGUSR1 없음
if hasattr(signal, 'SIGUSR1'):
    # signal.signal 반환값 = 이전 핸들러
    original = signal.signal(signal.SIGUSR1, signal_handler)

    # 자기 자신에게 시그널 전송
    # os.kill(pid, sig): 시그널 송신
    os.kill(os.getpid(), signal.SIGUSR1)

    # 원래 핸들러 복원
    signal.signal(signal.SIGUSR1, original)

# 사용 가능한 시그널 목록
print("\n주요 시그널:")
# 자주 쓰는 시그널과 의미
signal_info = [
    ("SIGINT", "인터럽트 (Ctrl+C)"),
    ("SIGTERM", "종료 요청"),
    ("SIGKILL", "강제 종료 (처리 불가)"),
    ("SIGHUP", "터미널 끊김"),
    ("SIGUSR1", "사용자 정의 1"),
    ("SIGUSR2", "사용자 정의 2"),
]
for name, desc in signal_info:
    if hasattr(signal, name):
        num = getattr(signal, name)
        print(f"  {name:>10} ({num:>2}): {desc}")

# === 5. 안전한 프로세스 관리 ===
print("\n=== 5. 안전한 프로세스 관리 ===")

# 컨텍스트 매니저로 프로세스 생명주기 보장
class ManagedProcess:
    """안전한 프로세스 관리 래퍼"""

    # 명령과 Popen kwargs 저장
    def __init__(self, cmd: list, **kwargs):
        self.cmd = cmd
        self.kwargs = kwargs
        self.proc = None

    # with 진입: 프로세스 시작
    def __enter__(self):
        self.proc = subprocess.Popen(self.cmd, **self.kwargs)
        return self.proc

    # with 종료: terminate → 5초 대기 → kill
    def __exit__(self, *args):
        # poll(): None이면 아직 실행 중
        if self.proc and self.proc.poll() is None:
            # SIGTERM: 정상 종료 요청 (잡을 수 있음)
            self.proc.terminate()  # 정상 종료 시도
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # SIGKILL: 강제 종료 (잡을 수 없음)
                self.proc.kill()  # 강제 종료
                self.proc.wait()

# 사용
with ManagedProcess(
    ['python3', '-c', 'import time; print("started", flush=True); time.sleep(0.1); print("done", flush=True)'],
    stdout=subprocess.PIPE, text=True
) as proc:
    output = proc.communicate(timeout=5)[0]
    print(f"관리된 프로세스 출력: {output.strip()}")

# 컨텍스트 매니저 종료 후 returncode 확인
print(f"프로세스 종료 코드: {proc.returncode}")

print("\n=== 핵심 정리 ===")
print("subprocess.run():  간단한 실행 + 결과 반환")
print("subprocess.Popen:  스트리밍, 파이프, 비동기")
print("capture_output:    stdout/stderr 캡처")
print("shell=True:        셸 파이프 사용 (보안 주의)")
print("signal.signal():   시그널 핸들러 등록")
print("terminate() -> kill(): 정상 종료 -> 강제 종료")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 명령은 모두 리스트로 넘기고, 셸 문법이 필요한 한 줄만 `shell=True` 로 쓴다.
- `run` 은 끝까지 기다려 결과를 주고, `Popen` 은 곧바로 돌아오므로 `wait` · `communicate` 를 직접 부른다.
- 파이프 체인에서는 `stdin=앞.stdout` 으로 잇고, 부모 쪽 앞 단계 출력을 닫는다.
- `signal.signal()` 의 반환값을 받아 두었다가 되돌린다. `SIGUSR1` 은 `hasattr` 로 있는지 먼저 본다.
- `__exit__` 은 `poll()` 로 아직 도는지 확인하고, `terminate` → `wait(timeout=5)` → `kill` → `wait` 차례로 정리한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
