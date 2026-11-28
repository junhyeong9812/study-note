# python/python-networking/07 — SSH 원격 명령 실행 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 로컬 셸로 `echo` 를 돌리면 (예측)

```python
# 질문용 발췌 — POSIX 셸(bash 등)에서 돌린다고 가정
import subprocess
result = subprocess.run('echo "Hello from shell"', shell=True,
                        capture_output=True, text=True)
print(f"stdout: {result.stdout.strip()}")
print(f"exit_code: {result.returncode}")
```

- 두 줄은 각각 어떻게 찍히나?
- 큰따옴표는 찍히는 글자에 남나?

### 2. 키와 비밀번호를 둘 다 주면 (예측)

```python
# 질문용 발췌
mgr = SSHManager('srv', 'admin', password='pw', key_file='/keys/id_rsa')
mgr.connect()   # connect 안에서 만들어지는 connect_kwargs 를 본다
```

- `client.connect(**connect_kwargs)` 직전, `connect_kwargs` 에는 어떤 키들이 어떤 값으로 들어 있나?

### 3. 없는 디렉터리를 원격에서 `ls` 하면 (예측)

```python
# 질문용 발췌
with SSHManager('server.com', 'admin', password='secret') as ssh:
    result = ssh.execute('ls /no-such-dir')
    print(result)
```

- `result` 의 `stdout` · `stderr` · `exit_code` 는 각각 어떤 꼴의 값인가?
- 이 줄에서 파이썬 예외가 나나?

### 4. `AutoAddPolicy` 를 프로덕션에서 피하는 까닭 (왜)

- 처음 보는 호스트 키를 자동으로 받아들이면 어떤 공격에 열리나?
- 대신 무엇을 쓰라고 하나?

### 5. `connect` 안에서 `import paramiko` 를 하는 까닭 (왜)

- 파일 맨 위가 아니라 메서드 안에 import 를 두면 무엇이 달라지나?

### 6. 여러 서버 실행에 스레드 풀이 잘 맞는 까닭 (왜)

- 서버 한 대에 SSH 명령을 돌리는 일은 시간을 주로 어디에 쓰며, 그것이 스레드와 어떻게 이어지나?

### 7. `with SSHManager(...)` 블록 안에서 예외가 나면 (경계)

- 연결은 닫히나?
- 그 예외는 `with` 바깥으로 나가나, 삼켜지나?

### 8. `__enter__` 의 `connect()` 가 인증 실패로 예외를 던지면 (경계)

- 이때 `__exit__` 는 불리나?
- 만들어 둔 `SSHClient` 는 어떻게 되나?

### 9. 터널을 지나 DB 에 닿는 길 (연결)

- `psycopg2` 가 `127.0.0.1` 로 붙을 때 실제 데이터는 어떤 경로로 `db-server.internal` 에 닿나?
- `remote_bind_address` 의 `db-server.internal` 은 누구 기준에서 풀리는 이름인가?

### 10. `subprocess.run` 과 `exec_command` 의 짝 (연결)

- `result.stdout` 과 `result.returncode` 는 paramiko 의 무엇에 각각 대응하나?
- `shell=True` 가 품은 위험은 원격 `exec_command` 에도 있나?

## 실습

### 실습 1. SSH 원격 실행 학습 스크립트 만들기

**만들 것** — paramiko 사용법 · `SSHManager` 래퍼 · 멀티 서버 · 터널링을 구획별로 찍어 보여 주고, 마지막에 `subprocess` 로 「명령 → stdout · 종료 코드」를 로컬에서 실제로 돌려 보는 스크립트를 만든다.

**준비물** — 스크립트 자체는 표준 라이브러리만으로 돌아간다. paramiko · sshtunnel · psycopg2 는 설명 문자열 안에만 나오거나 `connect()` 를 실제로 부를 때만 import 되므로, 실제 서버에 붙어 보지 않는다면 설치하지 않아도 된다. SSH 서버 접속은 이 실습에서 하지 않는다 — 5구획의 `subprocess` 가 그 흐름을 로컬에서 흉내 낸다.

**요구 조건**

1단계 — paramiko 기본 사용 (구획 1)
1. `=== 1. SSH 기본 연결 및 명령 실행 ===` 머리줄을 찍는다.
2. 비밀번호 인증 연결 → `exec_command` → `stdout` · `stderr` 읽기 → `recv_exit_status()` → `close()` 와, `key_filename` 을 쓰는 키 기반 `connect` 예시를 여러 줄 문자열로 찍는다.

2단계 — `SSHManager` 클래스 (구획 2)
3. `=== 2. SSH 래퍼 클래스 ===` 머리줄을 찍는다.
4. `__init__` 은 `host` · `username` · `password`(기본 `None`) · `key_file`(기본 `None`) · `port`(기본 22)를 저장하고 `client` 를 `None` 으로 둔다.
5. `__enter__` 는 `connect()` 를 부르고 자기 자신을 돌려주며, `__exit__` 는 `close()` 를 부른다.
6. `connect` 는 함수 안에서 `paramiko` 를 import 하고, `SSHClient` 를 만들어 `AutoAddPolicy` 를 건 뒤, `hostname` · `port` · `username` 을 담은 딕셔너리에 `key_file` 이 있으면 `key_filename` 을, 없으면 `password` 를 넣어 `connect(**…)` 로 연결한다.
7. `execute(command, timeout=30)` 는 `exec_command` 를 부르고 `stdout` · `stderr` 를 읽어 디코드 · `strip` 한 문자열과 종료 코드를 `'stdout'` · `'stderr'` · `'exit_code'` 키의 딕셔너리로 돌려준다.
8. `upload(local, remote)` 와 `download(remote, local)` 은 `open_sftp()` 로 세션을 열어 각각 `put` · `get` 을 하고 세션을 닫는다.
9. `close` 는 `client` 가 있을 때만 닫는다.
10. 클래스 아래에 `with SSHManager(...) as ssh:` 로 `uptime` · `df -h` 를 실행하고 파일을 올리는 사용 예시를 문자열로 찍는다.

3단계 — 멀티 서버 · 터널링 (구획 3 · 4)
11. `=== 3. 멀티 서버 실행 패턴 ===` 머리줄 뒤에, 서버 세 대 목록 · `run_on_server` 함수 · `ThreadPoolExecutor(max_workers=5)` 로 `submit` 하고 `result()` 를 차례로 찍는 예시를 문자열로 찍는다.
12. `=== 4. SSH 터널링 ===` 머리줄 뒤에, `SSHTunnelForwarder` 로 로컬 5432 → SSH 서버 → 원격 DB 5432 터널을 열고 `psycopg2` 로 `tunnel.local_bind_port` 에 붙는 예시를 문자열로 찍는다.

4단계 — 로컬 시뮬레이션과 정리 (구획 5)
13. `=== 5. 로컬 시뮬레이션 (subprocess) ===` 머리줄을 찍는다.
14. `echo "Hello from shell"` · `date` · `python3 --version` 세 명령을 차례로 `subprocess.run(..., shell=True, capture_output=True, text=True)` 로 돌리고, 명령마다 `  $ 명령` · `    stdout: …`(strip 한 값) · `    exit_code: …` 세 줄을 찍는다.
15. 빈 줄 뒤에 `=== 핵심 정리 ===` 와 다섯 줄의 정리를 찍는다.

**시작 코드**

```python
"""SSH 원격 명령 실행: paramiko, 터널링 개념"""

# === 1. paramiko SSH 기본 사용 ===
print("=== 1. SSH 기본 연결 및 명령 실행 ===")
print("""
# TODO: 비밀번호 인증 연결 → exec_command → stdout/stderr 읽기 → 종료 코드 → close
# TODO: key_filename 을 쓰는 키 기반 connect 예시
""")

# === 2. SSH 래퍼 클래스 ===
print("=== 2. SSH 래퍼 클래스 ===")

class SSHManager:
    """SSH 연결 관리 클래스 (개념 구현)"""

    def __init__(self, host: str, username: str,
                 password: str = None, key_file: str = None, port: int = 22):
        pass  # TODO: 인자를 저장하고 client 를 None 으로

    def __enter__(self):
        pass  # TODO: 연결하고 자기 자신을 돌려준다

    def __exit__(self, *args):
        pass  # TODO: 닫는다

    def connect(self):
        """SSH 연결"""
        # TODO: 함수 안에서 paramiko import → SSHClient → AutoAddPolicy
        # TODO: hostname/port/username 딕셔너리 + (key_filename 또는 password) → connect(**...)
        pass

    def execute(self, command: str, timeout: int = 30) -> dict:
        """원격 명령 실행"""
        # TODO: exec_command → stdout/stderr 를 읽어 decode().strip(), 종료 코드
        pass

    def upload(self, local: str, remote: str):
        """SFTP로 파일 업로드"""
        pass  # TODO

    def download(self, remote: str, local: str):
        """SFTP로 파일 다운로드"""
        pass  # TODO

    def close(self):
        pass  # TODO: client 가 있을 때만 닫는다

print("""
# 사용 예시
# TODO: with SSHManager(...) as ssh: uptime, df -h, upload
""")

# === 3. 여러 서버에 명령 실행 ===
print("=== 3. 멀티 서버 실행 패턴 ===")
print("""
# TODO: servers 목록, run_on_server, ThreadPoolExecutor 로 병렬 실행
""")

# === 4. SSH 터널링 (포트 포워딩) 개념 ===
print("=== 4. SSH 터널링 ===")
print("""
# TODO: SSHTunnelForwarder 로 로컬 5432 -> SSH 서버 -> 원격 DB 5432, psycopg2 접속
""")

# === 5. 실행 가능한 데모 (subprocess로 로컬 시뮬레이션) ===
print("=== 5. 로컬 시뮬레이션 (subprocess) ===")
import subprocess

cmds = ['echo "Hello from shell"', 'date', 'python3 --version']
for cmd in cmds:
    # TODO: subprocess.run(...) 으로 실행하고 세 줄을 찍는다
    pass

print("\n=== 핵심 정리 ===")
# TODO: 정리 다섯 줄
```

**확인 방법** — `python3 ssh-remote.py` 로 돌려, 다섯 구획의 머리줄과 각 설명 문자열이 차례로 찍히고, 5구획에서 세 명령마다 `$ 명령` · `stdout:` · `exit_code:` 세 줄이 찍히는지 본다. 실제 SSH 서버가 있다면 `with SSHManager(...)` 로 `uptime` 을 돌려 `execute` 가 돌려주는 딕셔너리를 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
