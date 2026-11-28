# python/python-networking/07 — SSH 원격 명령 실행 — 정리 (힌트)

> 출처 — study-site 항목 `python/ssh-remote`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/ssh-remote.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**SSH 원격 명령 실행은 「잠긴 전용 전화선으로 먼 사무실의 비서에게 일을 시키는 것」이다.**
먼저 전화를 걸고, 상대 사무실이 진짜인지 신분증을 확인하고, 내가 누구인지 암호나 열쇠로 밝힌다.
그다음 「이 서류함 목록 좀 봐 줘」라고 지시하면, 비서는 일반 보고서와 사고 보고서를 따로 돌려주고 마지막에 「성공」 또는 「실패」 도장을 찍어 준다.
같은 전화선으로 서류를 주고받을 수도 있고, 사무실 안쪽 내선으로 돌려 달라고 할 수도 있다.
paramiko 로 하는 SSH 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 잠긴 전용 전화선 | SSH 연결 (TCP 22번 포트 위, 전 구간 암호화) |
| 사무실 신분증 확인 | 호스트 키 확인 (`set_missing_host_key_policy`) |
| 암호 / 열쇠로 나를 밝히기 | 비밀번호 인증 / 키 기반 인증 |
| 비서에게 지시 | `exec_command('명령')` |
| 일반 보고서 · 사고 보고서 | `stdout` · `stderr` |
| 성공 / 실패 도장 | 종료 코드 (`recv_exit_status()`) |
| 같은 선으로 서류 주고받기 | SFTP (`open_sftp()` → `put` / `get`) |
| 안쪽 내선으로 돌려 주기 | SSH 터널링 (포트 포워딩) |

```text
  내 PC (파이썬)                           원격 서버
 ┌──────────────┐   암호화된 SSH 연결   ┌──────────────┐
 │ SSHClient    │ ════════════════════> │ sshd (22번)  │
 │              │   명령: 'uptime'      │   └─ 셸이 실행│
 │ stdout/stderr│ <════════════════════ │ 결과 + 종료코드│
 └──────────────┘                       └──────────────┘
```

## 이 주제가 답하려는 질문

1. 파이썬에서 원격 서버에 명령을 보내고, 그 결과와 성공 여부를 어떻게 돌려받나?
2. 연결을 어떻게 열고(인증 · 호스트 키) 어떻게 빠짐없이 닫나?
3. 서버가 여러 대일 때 같은 명령을 어떻게 한꺼번에 돌리나?
4. 방화벽 뒤에 숨은 자원(예: 내부 DB)에 SSH 로 어떻게 닿나?

## 동작 방식

### (1) 연결 열기 — `SSHClient` · 호스트 키 정책 · 인증

**언제 쓰나** — 원격 서버와 무엇이든 하기 전에 한 번 연다.
SSH 는 TCP 위에서 동작하고, 기본 포트는 22 다.

```text
ssh = paramiko.SSHClient()                     → 빈 클라이언트 객체가 생긴다
ssh.set_missing_host_key_policy(AutoAddPolicy())→ 처음 보는 서버 키를 만나면 어떻게 할지 정한다
ssh.connect(host, username=..., password=...)  → TCP 연결 → 서버 키 확인 → 사용자 인증
   또는  connect(host, username=..., key_filename=...)  → 키 파일로 인증
                                                → 인증된 SSH 세션이 열린다
```

- `SSHClient()` 는 연결을 담을 그릇만 만든다.
- `set_missing_host_key_policy` 는 「모르는 서버 키를 만났을 때」의 규칙이다.
- `AutoAddPolicy` 는 처음 보는 키를 묻지 않고 받아들인다 — 개발용이다.
- `connect` 에 `password=` 를 주면 비밀번호 인증, `key_filename=` 을 주면 키 기반 인증이다.
- 키 객체를 직접 만들어 `pkey=paramiko.RSAKey.from_private_key_file(...)` 로 넘기는 방법도 있다.

> **호스트 키** — 서버가 자기 신원을 증명하는 공개키다.\
> 예: 처음 접속할 때 「이 서버의 지문이 맞습니까?」라고 묻는 그 키.

> **키 기반 인증** — 비밀번호 대신 개인키 파일로 내 신원을 증명하는 방식이다.\
> 예: `~/.ssh/id_rsa` 를 쓰는 로그인.

### (2) 명령 실행 — `exec_command` 와 세 개의 흐름

**언제 쓰나** — 원격에서 셸 명령 하나를 돌리고 결과를 받을 때.

```text
stdin, stdout, stderr = ssh.exec_command('ls -la /home')
        │        │        └─ 원격 명령의 에러 흐름
        │        └─ 원격 명령의 표준 흐름
        └─ 원격 명령에 입력을 보낼 쪽
stdout.read()                 → 원격 명령이 흐름을 닫을(EOF) 때까지 기다렸다 바이트를 받는다
          .decode()           → 바이트를 문자열로 바꾼다
stdout.channel.recv_exit_status() → 원격 명령의 종료 코드(정수)를 받는다
ssh.close()                   → 연결을 닫는다
```

- `exec_command` 는 명령을 보내고 곧바로 세 객체를 돌려준다.
- `read()` 는 EOF 까지 블로킹한다 — 그래서 「명령이 끝날 때까지 기다리는」 효과가 난다.
- 받은 것은 바이트라서 `.decode()` 로 문자열로 바꾼다.
- `stdout.channel` 은 이 명령이 오가는 채널이고, `recv_exit_status()` 가 그 채널에서 종료 코드를 꺼낸다.
- 종료 코드는 관례상 0 이면 성공, 0 이 아니면 실패다.
- 명령이 실패해도 파이썬 예외가 나지 않는다 — 실패는 `stderr` 내용과 0 이 아닌 종료 코드로만 알 수 있다.

> **종료 코드** — 프로그램이 끝나며 돌려주는 정수로, 0 은 성공을 뜻한다.\
> 예: 없는 디렉터리를 `ls` 하면 0 이 아닌 값이 나온다.

> **EOF** — 「더 올 데이터가 없다」는 흐름의 끝 표시다.\
> 예: 원격 명령이 끝나면 `stdout` 에 EOF 가 온다.

### (3) 래퍼 클래스와 `with` — `SSHManager`

**언제 쓰나** — 연결 · 실행 · 닫기를 매번 손으로 쓰지 않고, 닫기를 잊지 않게 할 때.

```text
with SSHManager('server.com', 'admin', password='secret') as ssh:
   │  __init__  → host · username · password · key_file · port(기본 22) 저장, client=None
   │  __enter__ → self.connect() 호출 → self 를 돌려줌 → ssh 에 묶임
   │     connect(): 함수 안에서 import paramiko
   │                SSHClient() + AutoAddPolicy
   │                connect_kwargs = {hostname, port, username}
   │                key_file 있으면 key_filename 추가, 없으면 password 추가
   │                client.connect(**connect_kwargs)
   │  블록 본문 → ssh.execute('uptime') → {'stdout', 'stderr', 'exit_code'} 딕셔너리
   └  __exit__  → self.close() → client 가 있으면 client.close()
```

- `__enter__` 가 연결을 열고 자기 자신을 돌려주므로 `as ssh` 로 받은 것이 곧 `SSHManager` 객체다.
- `__exit__(self, *args)` 는 블록이 정상으로 끝나든 예외로 끝나든 불린다.
- 이 `__exit__` 는 아무것도 돌려주지 않으므로(`None`) 블록 안의 예외는 삼켜지지 않고 바깥으로 나간다.
- `__enter__` 안의 `connect()` 에서 예외가 나면 `with` 블록에 들어가지 못한 것이라 `__exit__` 는 불리지 않는다.
- `connect` 는 **키를 먼저 본다** — `key_file` 이 있으면 `password` 를 줘도 쓰이지 않는다.
- `import paramiko` 를 함수 안에 둔 까닭: paramiko 가 없는 환경에서도 파일의 나머지 부분은 돌아가게 하려는 것이다. import 는 `connect()` 가 실제로 불릴 때에야 일어난다.
- `execute` 는 `stdout` · `stderr` 를 읽어 `.strip()` 한 문자열과 종료 코드를 딕셔너리로 묶어 돌려준다. `timeout`(기본 30)은 `exec_command` 에 그대로 넘긴다.

> **컨텍스트 매니저** — `__enter__` 와 `__exit__` 를 가진 객체로, `with` 문이 들어갈 때와 나올 때 자동으로 부른다.\
> 예: `with open(...) as f:` 의 파일 객체.

### (4) 파일 전송 — SFTP

**언제 쓰나** — 설정 파일을 올리거나 로그를 내려받을 때.

```text
sftp = client.open_sftp()   → 이미 열린 SSH 연결 위에 SFTP 세션을 연다
sftp.put(local, remote)     → 내 파일을 원격 경로로 올린다 (upload)
sftp.get(remote, local)     → 원격 파일을 내 경로로 내려받는다 (download)
sftp.close()                → SFTP 세션만 닫는다 (SSH 연결은 그대로)
```

- SFTP 는 별도 연결이 아니라 SSH 위에서 동작한다.
- `put` 은 (로컬, 원격), `get` 은 (원격, 로컬) 순서다 — 「보내는 쪽이 먼저」로 외우면 된다.

> **SFTP** — SSH 연결 위에서 파일을 주고받는 프로토콜이다.\
> 예: `sftp.put('local.conf', '/etc/app/config.conf')`.

### (5) 여러 서버에 한꺼번에 — `ThreadPoolExecutor`

**언제 쓰나** — 서버 수십 대에 같은 명령(`uptime`, 배포 스크립트 등)을 돌릴 때.

```text
servers = [web1, web2, db1]
pool.submit(run_on_server, s, 'uptime')  ×3 → 스레드들이 동시에 각 서버에 접속·실행
futures = [f1, f2, f3]                      → 제출한 순서대로 담긴 목록
for f in futures: f.result()                → f1 이 끝날 때까지 기다림 → f2 → f3
                                            → 각 서버의 stdout 을 차례로 찍음
```

- 한 서버의 일은 대부분 네트워크 응답을 기다리는 시간이다 — 이런 일을 I/O 바운드라 한다.
- I/O 바운드 일은 스레드로 나눠 돌리면 기다리는 시간이 겹쳐서 전체 시간이 줄어든다.
- `run_on_server` 는 서버마다 `SSHManager` 를 `with` 로 열고 닫는다 — 연결을 스레드끼리 나눠 쓰지 않는다.
- `futures` 를 제출 순서대로 돌며 `f.result()` 를 부르므로 찍히는 순서는 목록 순서다.
- 작업 안에서 예외가 났다면 `f.result()` 가 그 예외를 다시 던진다.

> **I/O 바운드** — 계산보다 입출력(네트워크 · 디스크) 대기에 시간을 쓰는 일이다.\
> 예: 원격 서버의 응답을 기다리는 SSH 명령.

> **Future** — 아직 끝나지 않았을 수 있는 작업의 결과를 나중에 꺼내는 표다.\
> 예: `pool.submit(...)` 이 돌려주는 것.

### (6) SSH 터널링 — 로컬 포트 포워딩

**언제 쓰나** — DB 가 방화벽 뒤 내부망에 있고, 밖에서는 SSH 서버만 닿을 때.

```text
psycopg2 → 127.0.0.1:5432 (내 PC)
              │  SSHTunnelForwarder 가 이 포트에서 받는다
              ▼
          ssh-server.com:22  ← 암호화된 SSH 연결
              │  SSH 서버가 대신 접속한다
              ▼
          db-server.internal:5432 (내부망 DB)
```

- `('ssh-server.com', 22)` 는 터널이 지나갈 SSH 서버다.
- `remote_bind_address` 는 **SSH 서버가 보기에** 닿을 목적지다 — `db-server.internal` 은 내 PC 가 아니라 SSH 서버 쪽에서 풀리는 이름이다.
- `local_bind_address` 는 내 PC 에서 열 입구다.
- 내 프로그램(`psycopg2`)은 `127.0.0.1` 의 `tunnel.local_bind_port` 로 붙기만 하면 내부 DB 와 말하게 된다.
- `sshtunnel` 은 paramiko 와 별개로 `pip install sshtunnel` 로 설치하는 라이브러리다.
- 방화벽이 SSH 는 허용하므로, SSH 로 감싼 길을 통해 DB 에 닿는다 — 원본은 이것을 「방화벽 우회」라 부른다.

> **로컬 포트 포워딩** — 내 PC 의 한 포트로 들어온 연결을 SSH 서버를 거쳐 다른 주소로 넘기는 것이다.\
> 예: 로컬 5432 → SSH 서버 → 원격 DB 5432.

### (7) 로컬 흉내 — `subprocess.run`

**언제 쓰나** — SSH 서버 없이 「명령 → stdout · 종료 코드」 흐름을 내 PC 에서 연습할 때.

```text
subprocess.run('echo "Hello from shell"', shell=True, capture_output=True, text=True)
   shell=True          → 문자열을 셸이 해석한다 (따옴표는 셸이 벗겨 낸다)
   capture_output=True → stdout · stderr 를 화면 대신 잡아 둔다
   text=True           → 바이트가 아니라 문자열로 받는다
result.stdout.strip()  → 끝의 줄바꿈을 떼어 낸 표준 흐름
result.returncode      → 종료 코드
```

- `exec_command` 의 `stdout.read().decode()` 에 해당하는 것이 `result.stdout`(`text=True` 덕에 이미 문자열)이다.
- `recv_exit_status()` 에 해당하는 것이 `result.returncode` 다.
- POSIX 셸에서 `echo "Hello from shell"` 의 큰따옴표는 셸이 인자를 나눌 때 벗겨지므로 `echo` 는 따옴표 없는 글자를 받는다.
- `date` 는 실행한 시각에 따라 내용이 달라지고, `python3 --version` 은 설치된 버전에 따라 달라진다.

## 문법 — 형태와 규칙

```python
import os
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())   # 개발용
client.connect('10.0.0.5', port=22, username='deploy',
               key_filename=os.path.expanduser('~/.ssh/id_ed25519'))
try:
    stdin, stdout, stderr = client.exec_command('uptime', timeout=10)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    if code != 0:
        print('실패:', err)
finally:
    client.close()
```

- 연결: `SSHClient()` → `set_missing_host_key_policy(...)` → `connect(hostname, port=22, username=..., password=... | key_filename=... | pkey=...)`.
- 실행: `stdin, stdout, stderr = client.exec_command(명령, timeout=초)`.
- 결과: `stdout.read().decode()` · `stderr.read().decode()` · `stdout.channel.recv_exit_status()`.
- 파일: `sftp = client.open_sftp()` → `sftp.put(로컬, 원격)` / `sftp.get(원격, 로컬)` → `sftp.close()`.
- 닫기: `client.close()` — `try/finally` 나 컨텍스트 매니저로 반드시 부르게 만든다.
- 터널: `SSHTunnelForwarder((SSH호스트, 22), ssh_username=..., ssh_pkey=..., remote_bind_address=(목적지, 포트), local_bind_address=('127.0.0.1', 포트))` 를 `with` 로 연다. 열린 입구 포트는 `tunnel.local_bind_port`.
- 병렬: `ThreadPoolExecutor(max_workers=N)` 안에서 `pool.submit(함수, 인자…)` → `future.result()`.

## 어디서 틀리나

### 1. `AutoAddPolicy` 를 프로덕션에 그대로 둔다

`AutoAddPolicy` 는 처음 보는 호스트 키를 묻지 않고 받아들인다.
그러면 중간에서 서버인 척하는 공격자(중간자)의 키도 그대로 받아들이게 된다.
원본의 팁은 「프로덕션에서는 known_hosts 를 사용해야 한다」고 하고, 원본 코드 끝의 핵심 정리는 「프로덕션은 RejectPolicy」라고 한다.
두 말은 서로 다른 말이 아니라 짝이다 — 믿을 서버 키를 known_hosts 에 미리 두고, 거기 없는 키는 `RejectPolicy` 로 거절하는 것이다.

### 2. 명령이 실패했는데 예외를 기다린다

`exec_command` 는 원격 명령이 실패해도 예외를 던지지 않는다.
실패는 `stderr` 의 내용과 0 이 아닌 종료 코드로만 드러난다.
`exit_code` 를 확인하지 않으면 실패를 성공으로 착각한다.

### 3. 「채널 3개」라는 원본 주석

원본 주석은 `exec_command` 가 「비동기 채널 3개 (stdin/stdout/stderr)」를 돌려준다고 적는다.
그런데 종료 코드를 `stdout.channel` 에서 꺼내는 걸 보면, 세 객체는 한 명령의 한 채널에 붙은 세 흐름으로 보는 편이 자연스럽다.
그래서 「채널 3개」라는 표현은 의심스럽다 (확인 필요).

### 4. 키 파일 경로에 `~` 를 그대로 쓴다

원본은 한쪽에서 `key_filename='/home/user/.ssh/id_rsa'` 처럼 절대 경로를 쓰고, 다른 쪽에서 `'~/.ssh/deploy_key'` · `from_private_key_file('~/.ssh/id_rsa')` 처럼 `~` 를 쓴다.
`~` 를 홈 디렉터리로 바꾸는 것은 셸의 일이고, 파이썬의 파일 열기는 이를 저절로 풀지 않는다.
라이브러리가 풀어 주는지 확실하지 않으니 `os.path.expanduser` 로 먼저 풀어 넘기는 편이 안전하다 (확인 필요).

### 5. 키와 비밀번호를 둘 다 넘기고 비밀번호가 쓰일 거라 믿는다

`SSHManager.connect` 는 `key_file` 이 있으면 `key_filename` 만 넣고 `password` 는 넣지 않는다.
둘 다 주면 비밀번호는 조용히 버려진다.

### 6. `connect` 실패 때 `__exit__` 가 정리해 줄 거라 믿는다

`with` 는 `__enter__` 가 끝까지 성공해야 블록에 들어가고, 그래야 나올 때 `__exit__` 를 부른다.
`__enter__` 안의 `connect()` 가 예외를 던지면 `__exit__` 는 불리지 않는다.
이때 `self.client` 에 만들어 둔 `SSHClient` 는 `close()` 없이 남는다 (원본에 근거 없음 — 추론).

### 7. `shell=True` 에 바깥 입력을 이어 붙인다

원본 주석은 `shell=True` 를 「데모 단순화 (실제 SSH는 인젝션 위험 주의)」라고 적는다.
명령 문자열을 셸이 해석하므로, 사용자 입력에 `; rm -rf …` 같은 것이 섞이면 그대로 실행된다.
`exec_command` 로 보낸 문자열도 원격 셸이 해석하므로 같은 위험이 있다.

### 8. 병렬 실행에서 한 서버의 실패가 전체를 멈춘다

`for f in futures: f.result()` 는 실패한 작업의 예외를 그 자리에서 다시 던진다.
예외를 잡지 않으면 그 뒤 서버들의 결과는 찍히지 않는다 (원본에 근거 없음 — 추론).

### 9. 터널 입구 포트가 이미 쓰이고 있다

`local_bind_address=('127.0.0.1', 5432)` 는 내 PC 의 5432 번을 연다.
내 PC 에 이미 PostgreSQL 이 5432 번에서 돌고 있으면 그 포트를 열 수 없다 (원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `__enter__` 가 실패하면 `__exit__` 가 불리지 않는다 · `__exit__` 가 `None` 이면 예외가 전파된다 | 언어(`with` 문 규칙) |
| 함수 안의 `import` 는 그 함수가 불릴 때 실행된다 | 언어 |
| `future.result()` 가 작업의 예외를 다시 던진다 | 표준 라이브러리(`concurrent.futures`) |
| I/O 대기 중인 스레드끼리 시간이 겹쳐 빨라진다 | CPython 구현(I/O 대기 중 GIL 을 놓는 동작)에 기댄다 |
| `shell=True` 의 따옴표 처리 | 운영체제의 셸 (POSIX 셸 기준 · Windows 는 다를 수 있음, 확인 필요) |
| `read()` 가 EOF 까지 블로킹 · `recv_exit_status()` 가 종료 코드를 준다 | paramiko 라이브러리 |
| 종료 코드 0 = 성공 | 운영체제 · 프로그램 관례 |
| SSH 기본 포트 22 | 관례(서버 설정으로 바꿀 수 있다) |
| `python3 --version`, `date` 가 찍는 내용 | 설치된 버전 · 실행 시각 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 원격 서버에 명령 하나 돌리기 | `exec_command` + 종료 코드 확인 | 결과 문자열만 보고 성공 판단 |
| 연결을 열고 반드시 닫기 | 컨텍스트 매니저(`with`) 또는 `try/finally` | `close()` 를 맨 끝에 한 줄로만 두기 |
| 프로덕션 접속 | known_hosts + `RejectPolicy` | `AutoAddPolicy` |
| 설정 파일 올리기 · 로그 받기 | `open_sftp()` 의 `put` / `get` | `exec_command('cat ...')` 로 파일 내용 옮기기 |
| 서버 여러 대에 같은 명령 | `ThreadPoolExecutor` 로 서버마다 연결 | 한 대씩 차례로 기다리기 |
| 방화벽 뒤 DB 접속 | `SSHTunnelForwarder` 로컬 포워딩 | DB 포트를 바깥에 그대로 열기 |
| SSH 없이 흐름 연습 | `subprocess.run` | 바깥 입력을 섞은 `shell=True` |

## 핵심 문장

1. **`exec_command` 는 세 흐름을 돌려주고, 성공 여부는 종료 코드로만 안다** — 원격 실패는 예외가 아니다.
2. **연결은 `SSHClient` → 호스트 키 정책 → `connect`(비밀번호 또는 키) 순서로 연다** — `AutoAddPolicy` 는 개발용이다.
3. **컨텍스트 매니저로 감싸면 블록이 어떻게 끝나든 연결이 닫힌다** — 단, 연결 자체가 실패하면 `__exit__` 는 불리지 않는다.
4. **SFTP 와 터널은 같은 SSH 연결 위에 얹힌다** — 파일 전송도, 내부 DB 접속도 암호화된 길을 지난다.
5. **여러 서버는 I/O 바운드라 스레드 풀이 잘 맞는다.**

## 관련 자료

- [ftp-sftp](../06-ftp-sftp/2-summary.md)
- [process-management](../11-process-management/2-summary.md)
- `async-server` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `ssh-remote`

## 용어 풀이

- **SSH** — TCP 위에서 암호화된 원격 접속을 제공하는 프로토콜, 기본 포트 22.
- **paramiko** — 파이썬으로 쓴 SSH 라이브러리.
- **`SSHClient`** — paramiko 의 SSH 연결 객체.
- **호스트 키** — 서버가 자기 신원을 증명하는 공개키.
- **known_hosts** — 믿을 서버들의 호스트 키를 적어 둔 파일.
- **`AutoAddPolicy`** — 처음 보는 호스트 키를 자동으로 받아들이는 정책.
- **`RejectPolicy`** — 모르는 호스트 키를 거절하는 정책.
- **키 기반 인증** — 개인키 파일로 신원을 증명하는 인증.
- **`exec_command`** — 원격에서 명령을 돌리고 stdin · stdout · stderr 를 돌려주는 메서드.
- **종료 코드** — 프로그램이 끝나며 돌려주는 정수, 0 이 성공.
- **EOF** — 흐름에 더 올 데이터가 없다는 표시.
- **SFTP** — SSH 위에서 파일을 주고받는 프로토콜.
- **컨텍스트 매니저** — `__enter__` · `__exit__` 를 가져 `with` 와 함께 쓰는 객체.
- **I/O 바운드** — 입출력 대기가 대부분인 일.
- **Future** — 나중에 결과를 꺼낼 작업의 표.
- **터널링 / 포트 포워딩** — 한 포트로 들어온 연결을 SSH 를 거쳐 다른 주소로 넘기는 것.
- **`SSHTunnelForwarder`** — `sshtunnel` 라이브러리의 터널 객체.
- **`shell=True`** — `subprocess` 가 명령 문자열을 셸에게 해석시키는 옵션.
- **인젝션** — 입력에 섞인 글자가 명령으로 해석되어 의도하지 않은 일이 실행되는 것.

## 더 들어가면

- known_hosts 를 쓰려면 `client.load_system_host_keys()` 로 시스템의 known_hosts 를 읽고 `RejectPolicy()` 를 거는 꼴이 흔하다 (확인 필요).
- `exec_command` 의 `timeout` 은 명령 전체의 제한 시간이라기보다 채널에서 데이터를 기다리는 시간 제한으로 동작한다고 알려져 있다 (확인 필요).
- `stdout` 을 끝까지 읽은 뒤에 `stderr` 를 읽는 방식은, 원격 명령이 `stderr` 로 아주 많이 쓰면 버퍼가 차서 서로 기다리는 상황이 생길 수 있다 — `get_pty=True` 나 `channel.set_combine_stderr(True)` 를 쓰는 해법이 있다 (확인 필요).
- 원격 포트 포워딩(`ssh -R`)은 방향이 반대로, 원격 서버의 포트를 내 PC 쪽으로 넘긴다 (확인 필요).
- `local_bind_address` 에 포트 0 을 주면 운영체제가 빈 포트를 골라 주고, 그 값을 `local_bind_port` 로 읽는 방식이 충돌을 피한다 (확인 필요).
- 명령에 바깥 값을 넣어야 하면 `shlex.quote` 로 감싸 셸 인젝션을 막는다 (확인 필요).
- Windows 의 `cmd.exe` 에서는 `echo "Hello"` 가 따옴표까지 찍는다 (확인 필요).
- 서버가 아주 많으면 Fabric · Ansible 같은 도구가 이 패턴을 감싸 준다 (확인 필요).
