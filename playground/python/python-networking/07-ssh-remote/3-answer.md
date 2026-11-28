# python/python-networking/07 — SSH 원격 명령 실행 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 따옴표 없이 `Hello from shell`, 종료 코드 0

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
stdout: Hello from shell
exit_code: 0
```

큰따옴표는 남지 않는다.

**왜 그런가**
- `shell=True` 라서 문자열을 POSIX 셸이 해석하고, 셸은 인자를 나누며 큰따옴표를 벗겨 낸다.
- `echo` 는 끝에 줄바꿈을 붙이지만 `.strip()` 이 떼어 낸다.
- `text=True` 라 `result.stdout` 은 이미 문자열이다.
- `echo` 는 성공하므로 종료 코드는 0 이다.
- 근거: 2-summary 「동작 방식 (7)」.

### 2. `hostname` · `port`(22) · `username` · `key_filename` — `password` 는 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`connect_kwargs` 는 `{'hostname': 'srv', 'port': 22, 'username': 'admin', 'key_filename': '/keys/id_rsa'}` 가 된다.

**왜 그런가**
- 딕셔너리는 먼저 `hostname` · `port` · `username` 셋으로 시작하고, `port` 는 기본값 22 다.
- `if self.key_file:` 이 참이라 `key_filename` 만 더하고, `else` 쪽의 `password` 는 건너뛴다.
- 키가 우선이라 비밀번호는 조용히 버려진다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 3. `stdout` 은 빈 문자열, `stderr` 에 에러 문장, `exit_code` 는 0 이 아닌 정수 — 예외는 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`result` 는 `{'stdout': '', 'stderr': '(ls 의 "그런 파일이나 디렉터리가 없다"는 문장)', 'exit_code': (0 이 아닌 정수)}` 꼴이다.
정확한 문장과 종료 코드 값은 원격의 `ls` 구현에 따라 다르다.
`execute` 줄에서 파이썬 예외는 나지 않는다.

**왜 그런가**
- `ls` 는 찾지 못한 것을 표준 흐름이 아니라 에러 흐름에 쓴다.
- `execute` 는 `stdout` · `stderr` 를 각각 읽어 `strip` 하고 `recv_exit_status()` 로 종료 코드를 받을 뿐, 실패를 예외로 바꾸지 않는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 4. 중간자 공격에 열리니 known_hosts 와 `RejectPolicy` 를 쓴다

처음 보는 호스트 키를 묻지 않고 받으면, 진짜 서버 대신 중간에서 서버인 척하는 공격자의 키도 받아들인다.
그러면 비밀번호나 명령 내용이 공격자에게 넘어갈 수 있다.
프로덕션에서는 믿을 서버 키를 known_hosts 에 두고, 거기 없는 키는 `RejectPolicy` 로 거절한다.
근거: 2-summary 「어디서 틀리나 1」 · 「동작 방식 (1)」.

### 5. paramiko 가 없어도 파일의 나머지가 돌아가게 하려고

함수 안의 `import` 는 그 함수가 실제로 불릴 때에야 실행된다.
그래서 paramiko 가 설치되지 않은 환경에서도 스크립트를 import 하거나 1~5 구획을 돌리는 데는 문제가 없고, `connect()` 를 부를 때에만 import 실패가 난다.
근거: 2-summary 「동작 방식 (3)」 · 「구현 세부사항 대 언어 보장」.

### 6. 대부분이 네트워크 대기라서 스레드로 대기 시간을 겹칠 수 있다

서버 한 대의 일은 접속 · 인증 · 명령 응답을 기다리는 시간이 대부분인 I/O 바운드 일이다.
여러 스레드가 동시에 각 서버를 기다리면 대기 시간이 겹쳐 전체 시간이 줄어든다.
이 효과는 CPython 이 I/O 대기 중에 GIL 을 놓는 구현 동작에 기댄다.
근거: 2-summary 「동작 방식 (5)」 · 「구현 세부사항 대 언어 보장」.

### 7. 연결은 닫히고, 예외는 바깥으로 나간다

`__exit__` 는 블록이 예외로 끝나도 불리므로 `close()` 가 실행된다.
`__exit__` 가 아무것도 돌려주지 않아(`None`) 예외를 삼키지 않으므로 예외는 `with` 바깥으로 전파된다.
근거: 2-summary 「동작 방식 (3)」.

### 8. `__exit__` 는 불리지 않고, `SSHClient` 는 닫히지 않은 채 남는다

`with` 는 `__enter__` 가 성공해야 블록에 들어가고 `__exit__` 를 약속한다.
`__enter__` 안의 `connect()` 가 예외를 던지면 `__exit__` 는 불리지 않는다.
`self.client` 에 이미 만든 `SSHClient` 는 `close()` 를 받지 못한다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 9. 내 PC 의 입구 → 암호화된 SSH 연결 → SSH 서버가 대신 DB 에 접속

`psycopg2` 는 내 PC 의 `127.0.0.1:local_bind_port` 로 붙는다.
`SSHTunnelForwarder` 가 그 연결을 받아 `ssh-server.com:22` 의 SSH 연결 속으로 넣는다.
SSH 서버가 그것을 꺼내 `db-server.internal:5432` 로 접속해 넘긴다.
`db-server.internal` 은 SSH 서버 쪽에서 풀리는 이름이다 — 내 PC 는 그 이름을 몰라도 된다.
근거: 2-summary 「동작 방식 (6)」.

### 10. `stdout.read().decode()` 와 `recv_exit_status()` 에 대응하고, 인젝션 위험은 원격에도 있다

`result.stdout`(`text=True` 라 이미 문자열)은 `stdout.read().decode()` 에, `result.returncode` 는 `stdout.channel.recv_exit_status()` 에 대응한다.
`exec_command` 로 보낸 문자열도 원격 셸이 해석하므로, 바깥 입력을 이어 붙이면 `shell=True` 와 같은 인젝션 위험이 있다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. SSH 원격 실행 학습 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 구획 1 머리줄 | `print("=== 1. SSH 기본 연결 및 명령 실행 ===")` |
| 2. 비밀번호 · 키 인증 예시 문자열 | 구획 1 의 `print("""…""")` (`set_missing_host_key_policy` · `exec_command` · `recv_exit_status` · `key_filename`) |
| 3. 구획 2 머리줄 | `print("=== 2. SSH 래퍼 클래스 ===")` |
| 4. 인자 저장 · `client = None` | `SSHManager.__init__` |
| 5. `with` 진입 · 종료 | `__enter__` (`self.connect()` · `return self`) · `__exit__` (`self.close()`) |
| 6. 함수 안 import · `AutoAddPolicy` · 키 우선 연결 | `connect` 의 `import paramiko` · `connect_kwargs` · `if self.key_file:` · `self.client.connect(**connect_kwargs)` |
| 7. 결과 딕셔너리 | `execute` 의 `exec_command(command, timeout=timeout)` · `'stdout'` · `'stderr'` · `'exit_code'` |
| 8. SFTP 올리기 · 내려받기 | `upload` (`open_sftp` · `put`) · `download` (`open_sftp` · `get`) |
| 9. 있을 때만 닫기 | `close` 의 `if self.client:` |
| 10. 사용 예시 문자열 | 클래스 아래 `print("""# 사용 예시 …""")` |
| 11. 멀티 서버 예시 | 구획 3 의 `servers` · `run_on_server` · `ThreadPoolExecutor(max_workers=5)` 문자열 |
| 12. 터널링 예시 | 구획 4 의 `SSHTunnelForwarder(…)` · `psycopg2.connect(…port=tunnel.local_bind_port…)` 문자열 |
| 13. 구획 5 머리줄 | `print("=== 5. 로컬 시뮬레이션 (subprocess) ===")` |
| 14. 세 명령 실행과 세 줄씩 찍기 | `for cmd in cmds:` 안의 `subprocess.run(cmd, shell=True, capture_output=True, text=True)` · `$ {cmd}` · `stdout:` · `exit_code:` |
| 15. 핵심 정리 | `print("\n=== 핵심 정리 ===")` 와 다섯 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/ssh-remote.py`

```python
# [네트워크 & 시스템] SSH 원격 명령 실행
# 설명: paramiko로 SSH 연결, 원격 명령 실행, 터널링 개념
# 팁: paramiko는 Python SSH 라이브러리로, exec_command로 원격 명령 실행, open_sftp로 파일 전송을 한다. 프로덕션에서는 AutoAddPolicy 대신 known_hosts를 사용해야 한다. sshtunnel 라이브러리로 SSH 터널을 만들면 방화벽 뒤의 DB에도 접근할 수 있다.

"""SSH 원격 명령 실행: paramiko, 터널링 개념"""

# === 1. paramiko SSH 기본 사용 ===
print("=== 1. SSH 기본 연결 및 명령 실행 ===")
# SSH는 포트 22에서 TCP 위에 동작 (전 구간 암호화 + 키 기반 인증 가능)
print("""
import paramiko

# --- 비밀번호 인증 ---
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 호스트 키 자동 수락
ssh.connect('192.168.1.100', username='user', password='password', port=22)

# 명령 실행
stdin, stdout, stderr = ssh.exec_command('ls -la /home')
print(stdout.read().decode())  # 표준 출력
print(stderr.read().decode())  # 에러 출력
exit_code = stdout.channel.recv_exit_status()  # 종료 코드

ssh.close()

# --- 키 기반 인증 ---
ssh.connect(
    '192.168.1.100',
    username='user',
    key_filename='/home/user/.ssh/id_rsa',
    # 또는 pkey=paramiko.RSAKey.from_private_key_file('~/.ssh/id_rsa')
)
""")

# === 2. SSH 래퍼 클래스 ===
print("=== 2. SSH 래퍼 클래스 ===")

# 컨텍스트 매니저로 자동 연결/해제
class SSHManager:
    """SSH 연결 관리 클래스 (개념 구현)"""

    # 비밀번호 또는 키 파일 중 하나 선택
    def __init__(self, host: str, username: str,
                 password: str = None, key_file: str = None, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port
        self.client = None

    # with 진입
    def __enter__(self):
        self.connect()
        return self

    # with 종료
    def __exit__(self, *args):
        self.close()

    # 실제 연결 로직
    def connect(self):
        """SSH 연결"""
        # 함수 내 import: 모듈 미설치 환경에서도 다른 부분 실행 가능
        import paramiko
        self.client = paramiko.SSHClient()
        # AutoAddPolicy: 처음 보는 호스트 키 자동 수락 (개발용; 프로덕션은 known_hosts)
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            'hostname': self.host,
            'port': self.port,
            'username': self.username,
        }
        # 키 우선, 없으면 비밀번호
        if self.key_file:
            connect_kwargs['key_filename'] = self.key_file
        else:
            connect_kwargs['password'] = self.password
        self.client.connect(**connect_kwargs)

    # 원격에서 명령 실행
    def execute(self, command: str, timeout: int = 30) -> dict:
        """원격 명령 실행"""
        # 비동기 채널 3개 (stdin/stdout/stderr)
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        return {
            # read는 EOF까지 블로킹 (명령 완료 대기 효과)
            'stdout': stdout.read().decode().strip(),
            'stderr': stderr.read().decode().strip(),
            # recv_exit_status: 원격 종료 코드
            'exit_code': stdout.channel.recv_exit_status()
        }

    # SFTP 업로드 (SSH 위에서 동작)
    def upload(self, local: str, remote: str):
        """SFTP로 파일 업로드"""
        sftp = self.client.open_sftp()
        sftp.put(local, remote)
        sftp.close()

    # SFTP 다운로드
    def download(self, remote: str, local: str):
        """SFTP로 파일 다운로드"""
        sftp = self.client.open_sftp()
        sftp.get(remote, local)
        sftp.close()

    def close(self):
        if self.client:
            self.client.close()

print("""
# 사용 예시
with SSHManager('server.com', 'admin', password='secret') as ssh:
    result = ssh.execute('uptime')
    print(result['stdout'])

    result = ssh.execute('df -h')
    print(result['stdout'])

    ssh.upload('local.conf', '/etc/app/config.conf')
""")

# === 3. 여러 서버에 명령 실행 ===
print("=== 3. 멀티 서버 실행 패턴 ===")
# ThreadPoolExecutor: 병렬로 N개 서버에 SSH 명령 (I/O 바운드 → 스레드 효과적)
print("""
from concurrent.futures import ThreadPoolExecutor

servers = [
    {'host': 'web1.example.com', 'user': 'deploy'},
    {'host': 'web2.example.com', 'user': 'deploy'},
    {'host': 'db1.example.com', 'user': 'admin'},
]

def run_on_server(server_info, command):
    with SSHManager(server_info['host'], server_info['user'],
                    key_file='~/.ssh/deploy_key') as ssh:
        return {
            'host': server_info['host'],
            'result': ssh.execute(command)
        }

# 병렬 실행
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(run_on_server, s, 'uptime') for s in servers]
    for f in futures:
        r = f.result()
        print(f"{r['host']}: {r['result']['stdout']}")
""")

# === 4. SSH 터널링 (포트 포워딩) 개념 ===
print("=== 4. SSH 터널링 ===")
# Local Forwarding: 로컬 포트를 SSH로 묶어 원격 내부 자원에 접근 (방화벽 우회)
print("""
import paramiko
from sshtunnel import SSHTunnelForwarder  # pip install sshtunnel

# Local Port Forwarding
# 로컬 5432 -> SSH 서버 -> 원격 DB의 5432
with SSHTunnelForwarder(
    ('ssh-server.com', 22),
    ssh_username='user',
    ssh_pkey='~/.ssh/id_rsa',
    remote_bind_address=('db-server.internal', 5432),
    local_bind_address=('127.0.0.1', 5432)
) as tunnel:
    print(f"터널 열림: localhost:{tunnel.local_bind_port}")
    # 이제 localhost:5432로 원격 DB에 접근 가능
    import psycopg2
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=tunnel.local_bind_port,
        database='mydb',
        user='dbuser',
        password='dbpass'
    )
""")

# === 5. 실행 가능한 데모 (subprocess로 로컬 시뮬레이션) ===
print("=== 5. 로컬 시뮬레이션 (subprocess) ===")
# paramiko 미설치 시에도 동작하도록 subprocess로 시뮬레이션
import subprocess

cmds = ['echo "Hello from shell"', 'date', 'python3 --version']
for cmd in cmds:
    # shell=True: 데모 단순화 (실제 SSH는 인젝션 위험 주의)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"  $ {cmd}")
    print(f"    stdout: {result.stdout.strip()}")
    print(f"    exit_code: {result.returncode}")

print("\n=== 핵심 정리 ===")
print("1. paramiko.SSHClient()로 SSH 연결")
print("2. exec_command()로 원격 명령 실행 (stdin, stdout, stderr)")
print("3. open_sftp()로 파일 전송")
print("4. AutoAddPolicy: 호스트 키 자동 수락 (프로덕션은 RejectPolicy)")
print("5. sshtunnel로 SSH 터널링 (원격 DB 접근 등)")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 1 · 3 · 4 구획과 사용 예시는 실행되는 코드가 아니라 `print` 로 찍는 설명 문자열이라, paramiko · sshtunnel · psycopg2 없이도 스크립트가 돈다.
- `SSHManager` 는 정의만 되고 호출되지 않는다 — `connect` 안의 `import paramiko` 덕분에 정의 단계에서 import 실패가 나지 않는다.
- `connect` 의 핵심은 「키 우선, 없으면 비밀번호」 분기와 `**connect_kwargs` 펼치기다.
- `execute` 는 원격 실패를 예외로 바꾸지 않고 `exit_code` 로 돌려준다 — 부르는 쪽이 그 값을 확인해야 한다.
- 5구획만 실제로 명령을 돌린다; `exec_command` 의 세 값 대신 `result.stdout` · `result.returncode` 를 쓰는 같은 흐름이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
