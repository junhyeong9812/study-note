# python/python-networking/11 — 프로세스 관리: subprocess와 시그널 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 셸 파이프 한 줄의 결과 (예측)

```python
# 질문용 발췌
result = subprocess.run('echo "Hello" | tr a-z A-Z', shell=True, capture_output=True, text=True)
print(f"셸 파이프: {result.stdout.strip()}")
```

- 이 두 줄이 찍는 한 줄은 무엇인가?
- `shell=True` 를 빼고 같은 문자열을 넘기면 무엇이 문제인가?

### 2. 세 단계 파이프 체인이 만드는 리스트 (예측)

```python
# 질문용 발췌
p1 = subprocess.Popen(['echo', 'hello world python'], stdout=subprocess.PIPE)
p2 = subprocess.Popen(['tr', ' ', '\n'], stdin=p1.stdout, stdout=subprocess.PIPE)
p3 = subprocess.Popen(['sort'], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
p1.stdout.close()
p2.stdout.close()
output = p3.communicate()[0]
print(f"파이프 체이닝: {output.strip().split(chr(10))}")
```

- 마지막 `print` 가 찍는 리스트는 무엇인가?

### 3. `with` 블록이 끝날 때의 `ManagedProcess` (예측)

```python
# 질문용 발췌
with ManagedProcess(
    ['python3', '-c', 'import time; print("started", flush=True); time.sleep(0.1); print("done", flush=True)'],
    stdout=subprocess.PIPE, text=True
) as proc:
    output = proc.communicate(timeout=5)[0]
    print(f"관리된 프로세스 출력: {output.strip()}")
print(f"프로세스 종료 코드: {proc.returncode}")
```

- `__exit__` 에서 `terminate()` 가 불리는가?
- 마지막 줄이 찍는 종료 코드는 무엇인가?

### 4. `check=True` 를 뺀 `false` (경계)
- `subprocess.run(['false'])` 처럼 `check` 없이 실패하는 명령을 돌리면 예외가 나는가?
- 그때 실패를 알아채려면 무엇을 봐야 하나?

### 5. 명령을 리스트로 넘기는 까닭 (왜)
- 사용자가 입력한 파일 이름을 명령에 넣을 때 `shell=True` 문자열보다 리스트 인자가 안전한 까닭은 무엇인가?

### 6. 부모가 `p1.stdout.close()` 를 부르는 까닭 (왜)
- 파이프 체이닝에서 부모가 앞 단계의 `stdout` 을 닫지 않으면 어떤 일이 생길 수 있나?

### 7. 잡을 수 있는 시그널과 없는 시그널 (경계)
- `SIGTERM` 과 `SIGKILL` 중 핸들러로 잡을 수 있는 것은 어느 쪽인가?
- 그 차이 때문에 `ManagedProcess.__exit__` 은 왜 `kill()` 을 맨 처음이 아니라 마지막에 두나?

### 8. `env` 를 넘기는 방법에 따라 달라지는 것 (경계)
- `env` 를 아예 넘기지 않으면 자식은 어떤 환경을 받나?
- `os.environ.copy()` 없이 `{'MY_VAR': 'custom_value'}` 만 넘기면 무엇을 잃나?

### 9. `run` 과 `Popen` 의 관계 (연결)
- `subprocess.run()` 은 `Popen` 에 비해 어떤 단계를 더 해 주는가?
- 출력이 나오는 대로 한 줄씩 받아야 할 때 `run` 대신 `Popen` 을 고르는 까닭은 무엇인가?

### 10. 핸들러를 되돌리는 패턴과 `with` 문 (연결)
- `original = signal.signal(...)` 로 받아 두고 나중에 다시 등록하는 패턴은 `ManagedProcess` 의 `__enter__` · `__exit__` 와 어떤 점에서 닮았나?

## 실습

### 실습 1. subprocess · 시그널 · 안전한 종료를 한 스크립트로 엮기

**만들 것** — 외부 명령 실행부터 파이프 체이닝, 시그널 핸들러, 컨텍스트 매니저로 감싼 안전한 종료까지 다섯 절로 나눈 데모 스크립트를 완성한다.

**준비물** — 유닉스 계열 OS(리눅스 · macOS)와 `echo` · `tr` · `sort` · `sleep` · `false` · `python3` 명령. 표준 라이브러리만 쓴다.

**요구 조건**

1단계 — `run` 기본
1. `['echo', 'Hello subprocess']` 를 `run` 으로 돌려 표준 출력과 종료 코드를 찍는다(출력은 문자열로 받는다).
2. `'echo "Hello" | tr a-z A-Z'` 를 셸을 거쳐 실행해 결과를 찍는다.
3. `python3 -c` 로 표준 출력에 `out`, 표준 에러에 `err` 를 쓰는 자식을 돌려 둘을 따로 찍는다.
4. `false` 를 「실패하면 예외」 모드로 돌리고, `CalledProcessError` 를 잡아 종료 코드를 찍는다.

2단계 — `run` 옵션
5. `sleep 10` 을 1초 제한으로 돌리고 `TimeoutExpired` 를 잡아 「타임아웃 발생」을 찍는다.
6. `'hello world'` 를 자식의 표준 입력으로 넣어, 대문자로 바꿔 찍는 자식의 결과를 받는다.
7. 부모 환경을 복사해 `MY_VAR` 를 더한 환경을 자식에게 주고, 자식이 읽은 `MY_VAR` 를 찍는다.

3단계 — `Popen`
8. 0~4 를 한 줄씩 내보내는 자식을 `Popen` 으로 띄우고, 표준 출력을 줄마다 읽어 리스트로 모은 뒤 종료를 기다린다.
9. `echo 'hello world python'` → `tr ' ' '\n'` → `sort` 를 `Popen` 셋으로 잇고, 부모 쪽 앞 단계 출력을 닫은 뒤 마지막 단계의 출력을 리스트로 찍는다.

4단계 — 시그널
10. `(signum, frame)` 을 받아 시그널 이름과 번호를 찍는 핸들러를 만든다.
11. `SIGUSR1` 이 있을 때만: 핸들러를 등록하며 이전 핸들러를 보관하고, 자기 자신에게 `SIGUSR1` 을 보낸 뒤, 이전 핸들러로 되돌린다.
12. 주요 시그널 여섯 개의 이름 · 번호 · 뜻을 찍되 그 OS 에 없는 이름은 건너뛴다.

5단계 — 안전한 종료
13. `ManagedProcess` 클래스: 생성자에서 명령과 `Popen` 키워드 인자를 보관하고, `with` 진입 때 `Popen` 으로 시작해 돌려준다.
14. `with` 종료 때 아직 실행 중이면 정상 종료를 요청하고 5초 기다리며, 시간 초과면 강제 종료 뒤 다시 기다린다.
15. `ManagedProcess` 로 `started` · `done` 을 찍는 자식을 돌려 출력을 받고, 블록 뒤에서 종료 코드를 찍는다.
16. 끝에 핵심 정리 여섯 줄을 찍는다.

**시작 코드**

```python
"""프로세스 관리: subprocess, Popen, 시그널"""
import subprocess
import signal
import sys
import os

# === 1. subprocess.run() - 기본 ===
print("=== 1. subprocess.run() ===")

result = None  # TODO: ['echo', 'Hello subprocess'] 실행, 출력 캡처 + 문자열로
print(f"stdout: {result.stdout.strip()}")
print(f"returncode: {result.returncode}")

result = None  # TODO: 'echo "Hello" | tr a-z A-Z' 를 셸로 실행
print(f"셸 파이프: {result.stdout.strip()}")

result = None  # TODO: ['python3', '-c', 'import sys; print("out"); print("err", file=sys.stderr)'] 실행
print(f"\nstdout: '{result.stdout.strip()}'")
print(f"stderr: '{result.stderr.strip()}'")

try:
    pass  # TODO: ['false'] 를 실패하면 예외가 나도록 실행
except subprocess.CalledProcessError as e:
    print(f"\nCalledProcessError: returncode={e.returncode}")

# === 2. subprocess.run() 옵션들 ===
print("\n=== 2. 유용한 옵션 ===")

try:
    pass  # TODO: ['sleep', '10'] 을 1초 제한으로 실행
except subprocess.TimeoutExpired:
    print("타임아웃 발생 (1초 초과)")

result = None  # TODO: ['python3', '-c', 'print(input().upper())'] 에 'hello world' 를 stdin 으로
print(f"stdin 입력 결과: {result.stdout.strip()}")

env = None  # TODO: 부모 환경 복사
# TODO: env 에 MY_VAR = 'custom_value'
result = None  # TODO: ['python3', '-c', 'import os; print(os.environ.get("MY_VAR", "none"))'] 를 env 로 실행
print(f"환경 변수: {result.stdout.strip()}")

# === 3. Popen - 스트리밍/비동기 ===
print("\n=== 3. Popen (스트리밍) ===")

proc = None  # TODO: ['python3', '-c', 'import time; [print(i, flush=True) or time.sleep(0.01) for i in range(5)]'] 를 Popen 으로, stdout 파이프 + 문자열
lines = []
# TODO: proc.stdout 을 줄마다 읽어 strip 해서 lines 에 넣기
# TODO: 종료 대기
print(f"실시간 읽기: {lines}")

p1 = None  # TODO: ['echo', 'hello world python'], stdout 파이프
p2 = None  # TODO: ['tr', ' ', '\n'], 입력은 p1 의 출력, stdout 파이프
p3 = None  # TODO: ['sort'], 입력은 p2 의 출력, stdout 파이프 + 문자열
# TODO: 부모 쪽 p1, p2 의 stdout 닫기
output = None  # TODO: p3 의 출력을 다 받고 종료 대기
print(f"파이프 체이닝: {output.strip().split(chr(10))}")

# === 4. 시그널 처리 ===
print("\n=== 4. 시그널 처리 ===")

def signal_handler(signum, frame):
    sig_name = None  # TODO: 번호 → 시그널 이름
    print(f"  시그널 수신: {sig_name} ({signum})")

if hasattr(signal, 'SIGUSR1'):
    original = None  # TODO: SIGUSR1 에 signal_handler 등록 (이전 핸들러 보관)
    # TODO: 자기 자신에게 SIGUSR1 보내기
    # TODO: 원래 핸들러 복원

print("\n주요 시그널:")
signal_info = [
    ("SIGINT", "인터럽트 (Ctrl+C)"),
    ("SIGTERM", "종료 요청"),
    ("SIGKILL", "강제 종료 (처리 불가)"),
    ("SIGHUP", "터미널 끊김"),
    ("SIGUSR1", "사용자 정의 1"),
    ("SIGUSR2", "사용자 정의 2"),
]
for name, desc in signal_info:
    # TODO: 이 OS 에 있는 이름만, 번호를 읽어서
    #       print(f"  {name:>10} ({num:>2}): {desc}")
    pass

# === 5. 안전한 프로세스 관리 ===
print("\n=== 5. 안전한 프로세스 관리 ===")

class ManagedProcess:
    """안전한 프로세스 관리 래퍼"""

    def __init__(self, cmd: list, **kwargs):
        # TODO: cmd, kwargs 보관, proc 은 None
        pass

    def __enter__(self):
        # TODO: Popen 으로 시작하고 돌려주기
        pass

    def __exit__(self, *args):
        # TODO: 아직 실행 중이면 terminate → 5초 wait → 시간 초과면 kill → wait
        pass

with ManagedProcess(
    ['python3', '-c', 'import time; print("started", flush=True); time.sleep(0.1); print("done", flush=True)'],
    stdout=subprocess.PIPE, text=True
) as proc:
    output = None  # TODO: 5초 제한으로 출력 받기
    print(f"관리된 프로세스 출력: {output.strip()}")

print(f"프로세스 종료 코드: {proc.returncode}")

print("\n=== 핵심 정리 ===")
print("subprocess.run():  간단한 실행 + 결과 반환")
print("subprocess.Popen:  스트리밍, 파이프, 비동기")
print("capture_output:    stdout/stderr 캡처")
print("shell=True:        셸 파이프 사용 (보안 주의)")
print("signal.signal():   시그널 핸들러 등록")
print("terminate() -> kill(): 정상 종료 -> 강제 종료")
```

**확인 방법** — `python3 process-management.py` 로 돌려, 다섯 절의 머리줄이 차례로 찍히고 타임아웃 절이 약 1초 뒤 넘어가며, 시그널 절에 `시그널 수신: SIGUSR1` 줄이 나오고 마지막에 종료 코드와 핵심 정리 여섯 줄이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
