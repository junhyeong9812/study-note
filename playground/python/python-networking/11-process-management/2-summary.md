# python/python-networking/11 — 프로세스 관리: subprocess와 시그널 — 정리 (힌트)

> 출처 — study-site 항목 `python/process-management`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/process-management.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**`subprocess` 는 「주방장이 외부 요리사에게 주문서를 넘기는 창구」다.**
주방장(파이썬 프로그램)은 요리를 직접 하지 않고 주문서(명령 리스트)를 써서 다른 요리사(외부 프로그램)에게 맡긴다.
주문을 넣고 접시가 나올 때까지 창구 앞에서 기다릴 수도 있고(`run`), 주문만 넣고 돌아와 접시가 나오는 대로 하나씩 받을 수도 있다(`Popen`).
요리사 여럿을 컨베이어로 이어 앞 사람의 결과를 뒷사람이 바로 받게 할 수도 있다(파이프).
요리사를 멈추게 할 때는 먼저 「마무리해 주세요」라고 말하고(`terminate`), 그래도 안 멈추면 전원을 내린다(`kill`).
운영체제의 프로세스 관리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주방장 | 부모 프로세스(파이썬 스크립트) |
| 외부 요리사 | 자식 프로세스(`echo` · `sort` · `python3` …) |
| 주문서 | 명령 리스트 `['echo', 'Hello']` |
| 창구 앞에서 기다리기 | `subprocess.run()` |
| 주문만 넣고 돌아오기 | `subprocess.Popen()` |
| 컨베이어 | 파이프(`stdout=PIPE` → 다음의 `stdin`) |
| 「마무리해 주세요」 | `terminate()` → `SIGTERM` |
| 전원 차단 | `kill()` → `SIGKILL` |
| 접시에 붙은 성공/실패 표 | `returncode` (0 = 성공) |

```text
 파이썬(부모)
   │  run(['echo','Hi'])            Popen([...])
   ▼                                 ▼
 [자식 시작] → 끝날 때까지 대기       [자식 시작] → 곧바로 돌아옴
   │                                 │
   ▼                                 ▼
 CompletedProcess                    proc.stdout 를 줄마다 읽기
 (stdout, stderr, returncode)        → proc.wait() 로 끝 기다리기
```

## 이 주제가 답하려는 질문

1. 파이썬에서 외부 명령을 실행하고 그 출력 · 에러 · 종료 코드를 어떻게 받나?
2. 한 번에 끝나는 실행과, 출력을 흘려 받거나 여러 명령을 잇는 실행은 어떻게 다르게 쓰나?
3. 프로세스끼리 시그널을 어떻게 주고받고, 내 프로세스는 시그널을 어떻게 처리하나?
4. 자식 프로세스를 남기지 않고 안전하게 끝내려면 어떤 순서를 밟아야 하나?

## 동작 방식

### (1) `subprocess.run()` — 실행하고 끝까지 기다리기

**언제 쓰나** — 명령 하나를 돌리고 결과를 한꺼번에 받으면 될 때 쓴다.
가장 흔한 경우다.

```text
subprocess.run(['echo', 'Hello subprocess'], capture_output=True, text=True)
   │
   ├─ 자식 프로세스 echo 시작 (셸을 거치지 않음)
   ├─ 자식의 stdout / stderr 를 파이프로 붙잡음 (capture_output=True)
   ├─ 자식이 끝날 때까지 기다림
   └─ 바이트를 문자열로 바꿈 (text=True)
   ▼
CompletedProcess(stdout='Hello subprocess\n', stderr='', returncode=0)
```

- `run` 은 자식을 띄우고 끝날 때까지 기다린 뒤 결과 객체를 돌려준다.
- `capture_output=True` 는 자식의 표준 출력과 표준 에러를 부모가 받아 두게 한다.
- `text=True` 가 있으면 `result.stdout` 이 `str` 이고, 없으면 `bytes` 다.
- `returncode` 는 자식의 종료 코드이고 0 이 성공이다.
- 출력 끝의 줄바꿈 때문에 예제는 `.strip()` 으로 양끝 공백을 걷어 낸다.
- 자식이 `print("err", file=sys.stderr)` 로 쓴 것은 `result.stderr` 에, 그냥 `print("out")` 한 것은 `result.stdout` 에 따로 담긴다.

> **CompletedProcess** — `run` 이 돌려주는 결과 객체로, `stdout` · `stderr` · `returncode` 를 담는다.\
> 예: `result.returncode == 0` 이면 성공이다.

### (2) 리스트 인자 대 `shell=True`

**언제 쓰나** — 기본은 리스트 인자다.
`|` · `>` 같은 셸 문법이 꼭 필요할 때만 `shell=True` 로 문자열을 셸에 넘긴다.

```text
리스트:  ['echo', 'Hello subprocess']
          └ 프로그램 echo 에 인자 하나 'Hello subprocess' 를 그대로 넘김
            (셸이 끼지 않음 → 공백·;·| 가 특수 의미를 갖지 않음)

문자열 + shell=True:  'echo "Hello" | tr a-z A-Z'
          └ 셸 /bin/sh 가 문자열을 해석
            → echo "Hello" 의 출력을 tr a-z A-Z 에 흘림
            → 소문자를 대문자로 바꿈
```

- 리스트 인자는 각 칸이 한 인자로 정해져 있어서, 칸 안의 글자가 명령으로 해석될 일이 없다.
- `shell=True` 는 셸이 문자열 전체를 해석하므로 파이프 · 리다이렉트를 쓸 수 있다.
- 그 대신 문자열에 사용자 입력이 섞이면 사용자가 `; rm -rf ~` 같은 글자로 다른 명령을 끼워 넣을 수 있다.
- 이것을 셸 인젝션이라 하고, 원본은 사용자 입력에는 `shell=True` 를 **절대** 쓰지 말라고 한다.

> **셸 인젝션** — 셸이 해석할 문자열에 바깥 입력이 섞여 의도하지 않은 명령이 실행되는 공격.\
> 예: 파일 이름 자리에 `a.txt; rm -rf ~` 를 넣는다.

### (3) `run` 의 옵션 — `check` · `timeout` · `input` · `env`

**언제 쓰나** — 실패를 예외로 받고 싶을 때, 오래 걸리면 끊고 싶을 때, 자식에게 입력을 주거나 환경을 바꿔 주고 싶을 때다.

```text
run(['false'], check=True)
  → false 는 0 이 아닌 코드로 끝남 → CalledProcessError 발생 (e.returncode 로 코드 확인)

run(['sleep', '10'], timeout=1)
  → 1초가 지나도 안 끝남 → 자식을 죽이고 → TimeoutExpired 발생

run([... 'print(input().upper())'], input='hello world', ...)
  → 'hello world' 가 자식의 stdin 으로 들어감 → 자식이 'HELLO WORLD' 출력

env = os.environ.copy(); env['MY_VAR'] = 'custom_value'
run([... 'print(os.environ.get("MY_VAR", "none"))'], env=env, ...)
  → 자식은 부모 환경 + MY_VAR 를 받음 → 'custom_value' 출력
```

- `check=True` 는 종료 코드가 0 이 아니면 `subprocess.CalledProcessError` 를 던진다.
- `check` 가 없으면 실패해도 예외가 없고, `returncode` 를 직접 봐야 한다.
- `timeout=초` 를 넘기면 `run` 이 자식을 죽이고 `subprocess.TimeoutExpired` 를 던진다(원본 주석: 「SIGKILL + TimeoutExpired」).
- `input=` 은 자식의 표준 입력에 넣을 데이터다. `text=True` 와 함께면 문자열로 준다.
- `env=` 를 주면 자식은 **그 사전만** 환경으로 받는다.
그래서 부모 환경을 `os.environ.copy()` 로 복사한 뒤 고쳐서 넘긴다.
- `env` 를 넘기지 않으면(`env=None`) 자식은 부모 환경을 그대로 물려받는다.
- 자식 코드의 `os.environ.get("MY_VAR", "none")` 은 변수가 없으면 `"none"` 을 돌려준다.

### (4) `Popen` — 띄우고 곧바로 돌아오기

**언제 쓰나** — 자식의 출력을 끝까지 기다리지 않고 나오는 대로 읽고 싶을 때(스트리밍), 또는 여러 자식을 동시에 띄워 이어야 할 때다.

```text
proc = Popen([... print(i, flush=True) ... for i in range(5)], stdout=PIPE, text=True)
   │  자식 시작 → Popen 은 즉시 반환 (자식은 아직 도는 중)
   ▼
for line in proc.stdout:        ← 자식이 한 줄 내보낼 때마다 한 번 돈다
    lines.append(line.strip())  ← '0', '1', '2', '3', '4'
   ▼
proc.wait()                     ← 자식이 끝날 때까지 기다림
```

- `run` 은 「띄우기 + 기다리기」를 한 번에 하고, `Popen` 은 띄우기만 하고 바로 돌아온다(원본 주석: 「run은 wait까지 한 번에」).
- `stdout=subprocess.PIPE` 를 주면 `proc.stdout` 이 파일처럼 열린다.
- `proc.stdout` 을 `for` 로 돌면 줄 단위로 읽는다.
- 자식 쪽의 `flush=True` 는 찍은 줄을 붙잡아 두지 않고 곧바로 내보낸다.
- 자식 코드의 `print(i, flush=True) or time.sleep(0.01)` 은 `print` 가 `None` 을 돌려주므로 `or` 뒤의 `sleep` 까지 실행하게 만드는 한 줄 꼼수다.
- 다 읽은 뒤 `proc.wait()` 로 자식이 끝나기를 기다린다.

> **스트리밍** — 결과를 다 모아서 받지 않고 나오는 대로 조금씩 받는 것.\
> 예: 로그가 찍히는 대로 한 줄씩 화면에 보여 준다.

### (5) 파이프 체이닝 — `echo | tr | sort` 를 직접 잇기

**언제 쓰나** — 셸 없이(`shell=True` 없이) 여러 명령의 출력과 입력을 잇고 싶을 때다.

```text
p1: echo 'hello world python'  ──stdout──▶  p2: tr ' ' '\n'  ──stdout──▶  p3: sort ──▶ 부모
                                  (PIPE)        stdin=p1.stdout   (PIPE)     stdin=p2.stdout

부모: p1.stdout.close(); p2.stdout.close()   ← 부모 손의 파이프 끝을 놓는다
부모: output = p3.communicate()[0]           ← p3 의 출력을 다 받고 끝을 기다린다

'hello world python' → 'hello\nworld\npython\n' → 'hello\npython\nworld\n'
```

- 앞 단계의 `stdout=PIPE` 로 생긴 `p1.stdout` 을 다음 단계의 `stdin=` 에 넘기면 두 자식이 직접 이어진다.
- `tr ' ' '\n'` 은 공백을 줄바꿈으로 바꿔 단어를 한 줄에 하나씩 놓는다.
- `sort` 는 줄을 정렬한다.
- `communicate()` 는 출력을 끝까지 모으고 자식이 끝날 때까지 기다린 뒤 `(stdout, stderr)` 짝을 돌려준다.
그래서 `[0]` 이 표준 출력이다.
- `chr(10)` 은 줄바꿈 문자 `'\n'` 이다. `output.strip().split(chr(10))` 은 줄마다 나눈 리스트를 만든다.
- 부모가 `p1.stdout.close()` 를 하는 까닭(원본 주석: 「SIGPIPE 처리를 위해 상위 stdout close」):
p1 의 출력 파이프는 p2 와 부모가 함께 쥐고 있다.
부모가 계속 쥐고 있으면, p2 가 먼저 끝나도 그 파이프를 읽을 쪽이 아직 남아 있는 셈이라 p1 이 「읽는 쪽이 사라졌다」는 신호(`SIGPIPE`)를 받지 못하고 남을 수 있다.
부모가 놓아 두면 읽는 쪽은 p2 하나뿐이 된다.

> **파이프** — 한 프로세스의 출력을 다른 프로세스의 입력으로 곧장 흘려보내는 통로.\
> 예: 셸의 `ls | sort`.

> **SIGPIPE** — 읽는 쪽이 모두 닫힌 파이프에 쓰려는 프로세스에게 보내지는 시그널.\
> 예: `p2` 가 끝난 뒤 `p1` 이 더 쓰려 하면 받는다.

### (6) 시그널 — 핸들러 등록 · 보내기 · 되돌리기

**언제 쓰나** — 프로세스가 바깥의 알림(Ctrl+C, 종료 요청, 사용자 정의 신호)에 반응하게 하거나, 다른 프로세스에 알림을 보낼 때다.

```text
original = signal.signal(signal.SIGUSR1, signal_handler)
   │  SIGUSR1 이 오면 signal_handler 를 부르도록 등록
   │  반환값 = 그전에 등록돼 있던 핸들러 → original 에 보관
   ▼
os.kill(os.getpid(), signal.SIGUSR1)
   │  내 PID 로 SIGUSR1 을 보냄 (이름은 kill 이지만 「시그널 송신」)
   ▼
signal_handler(signum, frame) 실행 → "  시그널 수신: SIGUSR1 (번호)"
   ▼
signal.signal(signal.SIGUSR1, original)   ← 원래 핸들러로 되돌림
```

- 핸들러 함수는 `(signum, frame)` 두 인자를 받는 꼴이어야 한다.
- `signal.Signals(signum).name` 은 번호를 `'SIGUSR1'` 같은 이름으로 바꾼다.
- `signal.signal()` 은 **이전 핸들러를 돌려준다**. 받아 두었다가 다시 등록하면 원상태로 돌아간다.
- `os.kill(pid, sig)` 는 프로세스를 죽이는 함수가 아니라 시그널을 보내는 함수다. 무엇이 일어날지는 시그널 종류와 받는 쪽 핸들러가 정한다.
- 윈도우에는 `SIGUSR1` 이 없다. 예제는 `hasattr(signal, 'SIGUSR1')` 로 있는지 먼저 확인하고, 목록을 찍을 때도 `hasattr` 로 없는 이름을 건너뛴다.

주요 시그널(원본 목록):

| 이름 | 뜻 |
|---|---|
| `SIGINT` | 인터럽트 (Ctrl+C) |
| `SIGTERM` | 종료 요청 — 받는 쪽이 잡을 수 있다 |
| `SIGKILL` | 강제 종료 — 잡을 수 없다(처리 불가) |
| `SIGHUP` | 터미널 끊김 |
| `SIGUSR1` | 사용자 정의 1 |
| `SIGUSR2` | 사용자 정의 2 |

- 목록 출력의 `{name:>10}` · `{num:>2}` 는 오른쪽 맞춤 폭 지정이다.
- 번호는 `getattr(signal, name)` 으로 그 자리에서 읽는다. 번호를 코드에 박아 두지 않는다.

> **시그널** — 운영체제가 프로세스에 보내는 짧은 비동기 알림.\
> 예: Ctrl+C 를 누르면 전경 프로세스가 `SIGINT` 를 받는다.

> **핸들러** — 시그널이 왔을 때 대신 불리도록 등록해 둔 함수.\
> 예: `signal.signal(signal.SIGUSR1, signal_handler)`.

### (7) 안전한 종료 — `terminate` → 기다림 → `kill`

**언제 쓰나** — 자식이 무슨 이유로든 남아 돌지 않게, 블록을 벗어날 때 정리를 보장하고 싶을 때다.

```text
with ManagedProcess([...], stdout=PIPE, text=True) as proc:
   │ __enter__ : Popen 으로 자식 시작, proc 을 돌려줌
   │ (블록 본문) proc.communicate(timeout=5) ...
   ▼
__exit__:
   proc.poll() is None ?  ── 아니오(이미 끝남) ──▶ 아무것도 안 함
        │ 예(아직 도는 중)
        ▼
   terminate()  (SIGTERM — "마무리해 주세요")
   wait(timeout=5)
        │ 5초 안에 끝남 ──▶ 끝
        │ TimeoutExpired
        ▼
   kill()  (SIGKILL — 잡을 수 없는 강제 종료) → wait()
```

- `poll()` 은 기다리지 않고 상태만 본다. `None` 이면 아직 실행 중이고, 끝났으면 종료 코드를 돌려준다.
- `terminate()` 는 `SIGTERM` 을 보낸다. 받는 쪽은 이것을 잡아 파일을 닫는 등 정리할 기회를 얻는다.
- 그래도 정해진 시간 안에 끝나지 않으면 `kill()` 로 `SIGKILL` 을 보낸다. 이것은 잡을 수 없어서 반드시 끝난다.
- `kill()` 뒤에도 `wait()` 를 불러 자식이 끝난 것을 거둔다.
- `__exit__` 은 `with` 블록이 정상으로 끝나든 예외로 끝나든 불린다. 그래서 정리가 보장된다.
- 예제의 사용처에서는 본문의 `communicate()` 가 이미 자식의 끝을 기다렸으므로, `__exit__` 에 이르렀을 때 `poll()` 은 `None` 이 아니다.
- `with` 뒤에도 `proc` 이름은 살아 있어서 `proc.returncode` 로 종료 코드를 볼 수 있다.

> **컨텍스트 매니저** — `with` 문에 쓰이며 `__enter__` 로 자원을 얻고 `__exit__` 로 반드시 정리하는 객체.\
> 예: `with open(...) as f:`.

## 문법 — 형태와 규칙

```python
import subprocess, signal, os

r = subprocess.run(['ls', '-l'], capture_output=True, text=True, check=True, timeout=5)
print(r.returncode, r.stdout[:20])

p = subprocess.Popen(['ping', '-c', '3', 'localhost'], stdout=subprocess.PIPE, text=True)
for line in p.stdout:
    print('>', line.rstrip())
p.wait()

def on_usr1(signum, frame):
    print('got', signal.Signals(signum).name)

old = signal.signal(signal.SIGUSR1, on_usr1)
os.kill(os.getpid(), signal.SIGUSR1)
signal.signal(signal.SIGUSR1, old)
```

| 쓰는 것 | 하는 일 |
|---|---|
| `subprocess.run(cmd, ...)` | 실행하고 끝까지 기다려 `CompletedProcess` 반환 |
| `capture_output=True` | stdout · stderr 를 붙잡음 |
| `text=True` | 입출력을 `str` 로 다룸 |
| `check=True` | 종료 코드가 0 이 아니면 `CalledProcessError` |
| `timeout=초` | 넘기면 자식을 죽이고 `TimeoutExpired` |
| `input=데이터` | 자식의 stdin 에 넣음 |
| `env=사전` | 자식의 환경 전체를 이 사전으로 |
| `shell=True` | 문자열 명령을 셸이 해석 (보안 주의) |
| `subprocess.Popen(cmd, ...)` | 띄우고 즉시 반환 |
| `stdout=subprocess.PIPE` | 자식 출력을 읽을 파이프를 만듦 |
| `stdin=앞.stdout` | 앞 단계 출력을 이 단계 입력으로 |
| `proc.wait(timeout=)` | 끝날 때까지 기다림 |
| `proc.communicate(timeout=)` | 출력 다 모으고 기다린 뒤 `(stdout, stderr)` |
| `proc.poll()` | 기다리지 않고 상태 확인 (`None` = 실행 중) |
| `proc.terminate()` / `proc.kill()` | `SIGTERM` / `SIGKILL` 보내기 |
| `signal.signal(sig, handler)` | 핸들러 등록, 이전 핸들러 반환 |
| `os.kill(pid, sig)` | 시그널 송신 |

- 명령은 리스트로 쓰는 것이 기본이다. 첫 칸이 프로그램, 나머지가 인자다.
- `shell=True` 일 때만 명령을 한 줄 문자열로 쓴다.
- 핸들러는 `(signum, frame)` 꼴이다.
- 자식 정리는 `terminate` → `wait(timeout)` → (시간 초과 시) `kill` → `wait` 차례다.

## 어디서 틀리나

### 1. `run` 과 `Popen` 을 거꾸로 고른다
원본 팁: `run()` 은 간단한 명령 실행에, `Popen` 은 스트리밍이나 파이프 체이닝에 쓴다.
출력이 끝없이 나오는 명령을 `run(capture_output=True)` 로 돌리면 끝날 때까지 아무것도 받지 못한다.
반대로 한 번 돌리고 끝나는 명령에 `Popen` 을 쓰면 `wait` · `communicate` 를 직접 챙겨야 해서 빠뜨리기 쉽다.

### 2. 사용자 입력에 `shell=True`
원본 팁: `shell=True` 는 셸 인젝션 위험이 있으므로 사용자 입력에 쓰지 않는다.
셸 문법이 필요하면 (5) 처럼 `Popen` 을 직접 이어서 셸 없이 만든다.

### 3. 바로 `kill` 부터 한다
원본 팁: 종료할 때는 `terminate`(SIGTERM) 후 타임아웃이면 `kill`(SIGKILL)하는 패턴이 안전하다.
`SIGKILL` 은 잡을 수 없어서 자식이 임시 파일 정리 · 버퍼 기록을 할 틈이 없다.
반대로 `terminate` 만 하고 기다리지 않으면, 자식이 `SIGTERM` 을 무시할 때 계속 남는다.

### 4. `check` 없이 실패를 놓친다
`check=True` 를 쓰지 않으면 명령이 실패해도 예외가 없다.
`returncode` 를 보지 않으면 실패를 모른 채 다음 줄로 넘어간다.

### 5. `text=True` 를 빼고 문자열처럼 다룬다
`text=True` 가 없으면 `stdout` 은 `bytes` 다.
`input=` 에도 `bytes` 를 넘겨야 한다.

### 6. `env` 에 바꿀 것만 담아 넘긴다
`env=` 는 환경 전체를 갈아 끼운다.
`{'MY_VAR': ...}` 만 넘기면 자식은 부모의 다른 환경 변수를 하나도 받지 못한다.
그래서 `os.environ.copy()` 로 복사한 뒤 고친다.

### 7. 파이프 체이닝에서 부모 쪽 파이프를 안 닫는다
`p1.stdout.close()` 를 빠뜨리면 뒷 단계가 먼저 끝났을 때 앞 단계가 `SIGPIPE` 를 받지 못해 남을 수 있다((5) 참고).

### 8. `SIGKILL` 핸들러를 만들려 한다
`SIGKILL` 은 처리할 수 없는 시그널이라 핸들러를 걸 수 없다.
정리 코드는 `SIGTERM` · `SIGINT` 에 건다.

### 9. 윈도우를 잊는다
`SIGUSR1` 같은 시그널은 윈도우에 없다.
예제처럼 `hasattr(signal, 'SIGUSR1')` 로 먼저 확인한다.
예제가 부르는 `echo` · `tr` · `sort` · `sleep` · `false` 도 유닉스 계열 명령이다.

### 10. 핸들러를 바꾸고 되돌리지 않는다
`signal.signal()` 의 반환값을 버리면 원래 동작으로 돌아갈 방법이 없다.
잠깐만 바꿀 때는 반환값을 받아 두었다가 다시 등록한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `run` · `Popen` · `check` · `timeout` · `communicate` 의 동작 | 파이썬 표준 라이브러리 `subprocess` 의 규약 (언어 문법이 아니다) |
| `timeout` 초과 시 자식이 `SIGKILL` 로 죽는다 (원본 주석) | 유닉스 계열에서 `kill()` 이 `SIGKILL` 을 보내기 때문 — 윈도우에는 `SIGKILL` 이 없다 (확인 필요) |
| `false` 는 「항상 returncode 1」로 끝난다 (원본 주석) | 원본의 주장 → 명령 구현이 정한다. 0 이 아닌 값이라는 것까지만 믿는 편이 안전하다 (확인 필요) |
| `SIGUSR1` 의 번호 · 목록에 찍히는 번호 | 운영체제가 정한다. 같은 이름이라도 OS 마다 번호가 다를 수 있어 `getattr` 로 읽는다 (확인 필요) |
| `SIGKILL` 은 잡을 수 없다 | 운영체제(POSIX) 규약 |
| `SIGUSR1` 이 윈도우에 없다 | 운영체제 차이 — `signal` 모듈은 그 OS 에 있는 것만 제공한다 |
| `echo` · `tr` · `sort` 의 출력 형태 | 각 명령의 구현 · 로케일 (`sort` 순서는 로케일에 따라 달라질 수 있다 — 확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 명령 하나 돌리고 결과 받기 | `subprocess.run(리스트, capture_output=True, text=True)` | `Popen` + 손수 `wait` |
| 실패를 예외로 다루기 | `check=True` + `CalledProcessError` | `returncode` 를 안 보고 넘어가기 |
| 오래 걸릴 수 있는 명령 | `timeout=` + `TimeoutExpired` | 무한정 기다리기 |
| 출력을 나오는 대로 보기 | `Popen(stdout=PIPE)` + `for line in proc.stdout` | `run` 으로 끝까지 모으기 |
| 여러 명령 잇기 | `Popen` 체인 + `stdin=앞.stdout` + 부모 쪽 `close()` | 사용자 입력이 섞인 `shell=True` 문자열 |
| 고정된 셸 한 줄(입력 없음) | `shell=True` 도 가능 | 바깥 입력을 문자열에 이어 붙이기 |
| 자식 환경 바꾸기 | `os.environ.copy()` 후 수정 → `env=` | 바꿀 변수만 담은 새 사전 |
| 자식 끝내기 | `terminate` → `wait(timeout)` → `kill` → `wait` | 곧바로 `kill` |
| 시그널에 반응하기 | `signal.signal(sig, handler)` (반환값 보관) | `SIGKILL` 핸들러 |

## 핵심 문장

1. **`run` 은 「띄우고 기다리기」를 한 번에, `Popen` 은 「띄우기」만 한다** — 그래서 스트리밍 · 파이프 체이닝은 `Popen` 몫이다.
2. **명령은 리스트로 넘긴다** — `shell=True` 는 셸이 문자열을 해석하므로 사용자 입력과 만나면 인젝션이 된다.
3. **실패 · 지연 · 입력 · 환경은 `run` 의 인자로 다룬다** — `check` · `timeout` · `input` · `env`.
4. **시그널은 핸들러로 받고 `os.kill` 로 보낸다** — `signal.signal` 은 이전 핸들러를 돌려주므로 되돌릴 수 있다.
5. **끝낼 때는 `SIGTERM` 으로 부탁하고, 안 들으면 `SIGKILL`** — 컨텍스트 매니저의 `__exit__` 에 넣으면 정리가 보장된다.

## 관련 자료

- [ssh-remote](../07-ssh-remote/2-summary.md)
- `file-monitoring` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `environment` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `process-management`

## 용어 풀이

- **프로세스** — 실행 중인 프로그램 하나. 저마다 PID 를 가진다.
- **자식 프로세스** — 다른 프로세스(부모)가 띄운 프로세스.
- **PID** — 프로세스 번호. `os.getpid()` 로 내 PID 를 얻는다.
- **표준 입력 · 출력 · 에러 (stdin · stdout · stderr)** — 프로세스가 기본으로 쓰는 세 입출력 통로.
- **종료 코드 (returncode)** — 프로세스가 끝나며 남기는 정수. 0 이 성공이다.
- **CompletedProcess** — `run` 의 결과 객체.
- **셸** — 명령 줄을 해석해 실행하는 프로그램. `|` · `>` 같은 문법을 처리한다.
- **셸 인젝션** — 셸이 해석할 문자열에 바깥 입력이 섞여 엉뚱한 명령이 실행되는 공격.
- **파이프** — 한 프로세스의 출력을 다른 프로세스의 입력으로 흘리는 통로.
- **스트리밍** — 결과를 나오는 대로 조금씩 받는 방식.
- **시그널** — 운영체제가 프로세스에 보내는 짧은 비동기 알림.
- **핸들러** — 시그널이 오면 불리도록 등록한 함수.
- **SIGTERM** — 종료 요청. 받는 쪽이 잡아서 정리할 수 있다.
- **SIGKILL** — 강제 종료. 잡을 수 없다.
- **SIGPIPE** — 읽는 쪽이 모두 닫힌 파이프에 쓰려 할 때 받는 시그널.
- **컨텍스트 매니저** — `__enter__` · `__exit__` 로 `with` 블록의 시작과 정리를 맡는 객체.
- **환경 변수** — 프로세스가 물려받는 이름=값 설정 묶음. `os.environ` 으로 본다.

## 더 들어가면

- `Popen` 자체도 컨텍스트 매니저라서 `with subprocess.Popen(...) as p:` 로 쓸 수 있다. 다만 블록을 나갈 때 파이프를 닫고 기다릴 뿐 `terminate` 를 해 주지는 않는다 (확인 필요).
- 파이썬의 시그널 핸들러는 운영체제의 저수준 핸들러 안에서 곧바로 돌지 않는다. 저수준 쪽은 표시만 해 두고, 인터프리터가 다음 바이트코드 사이에서 파이썬 핸들러를 부른다 (확인 필요).
- `signal.signal()` 은 메인 스레드에서만 부를 수 있다 (확인 필요).
- 윈도우에서는 `terminate()` 와 `kill()` 이 같은 일을 한다고 알려져 있다 (확인 필요).
- 파이썬 자식의 표준 출력이 파이프로 이어지면 줄 단위가 아니라 덩어리 단위로 버퍼링될 수 있다. 그래서 예제의 자식은 `flush=True` 를 쓴다 (확인 필요).
- 예제가 `'\n'` 대신 `chr(10)` 을 쓴 것은 파이썬 3.12 이전에는 f-string 의 `{}` 안에 백슬래시를 쓸 수 없었기 때문으로 보인다 (확인 필요).
- `stdout=PIPE` 와 `stderr=PIPE` 를 함께 걸고 `wait()` 만 부르면, 자식이 파이프를 가득 채워 서로 기다리는 교착이 날 수 있어 `communicate()` 를 권한다 (확인 필요).
- 자식을 통째로(손자 프로세스까지) 끝내려면 `start_new_session=True` 와 `os.killpg` 로 프로세스 그룹에 시그널을 보내는 방법이 있다 (확인 필요).
