# python/python-concurrency/08 — 멀티프로세싱 Queue/Pipe — 정리 (힌트)

> 출처 — study-site 항목 `python/multiprocessing-queue`(항목 데이터 `data/python/concurrency-deep.json`) · 정답 코드 study-practice `python/python-concurrency/reference/multiprocessing-queue.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**`multiprocessing.Queue` 는 「여러 사람이 함께 쓰는 우체통」이고, `Pipe` 는 「두 사람만 잇는 전화선」이다.**
우체통에는 여러 사람이 편지를 넣을 수 있고 여러 사람이 꺼낼 수 있다.
우체통 안에서 누가 먼저 넣었는지를 관리하느라 조금 느리다.
전화선은 양 끝에 한 사람씩만 붙는다.
중간 관리가 없어서 빠르지만, 한쪽 수화기를 두 사람이 동시에 잡으면 말이 엉킨다.
파이썬 프로세스끼리 데이터를 주고받는 것도 똑같은 구조다.
프로세스는 메모리를 나눠 쓰지 않으므로, 보낼 값을 바이트로 바꿔(직렬화) 우체통이나 전화선에 실어 보낸다.

| 비유 | 실체 |
|---|---|
| 우체통 | `multiprocessing.Queue()` |
| 편지 넣기 / 꺼내기 | `queue.put(item)` / `queue.get()` |
| 전화선의 두 수화기 | `Pipe()` 가 돌려주는 `(parent_conn, child_conn)` |
| 말하기 / 듣기 | `conn.send(item)` / `conn.recv()` |
| 「이제 끝」이라고 적힌 쪽지 | 종료 신호 `None` (sentinel) |
| 우체통의 칸 수 제한 | `Queue(maxsize=3)` |

```text
  [생산자 프로세스]                         [소비자 프로세스]
   put("item-0") ──►┌────────── Queue ──────────┐──► get() → "item-0"
   put("item-1") ──►│  item-0  item-1  None     │──► get() → "item-1"
   put(None)     ──►└───────────────────────────┘──► get() → None → 종료

  [송신 프로세스]  child_conn ═══════ Pipe ═══════ parent_conn  [수신 프로세스]
                  send("hello") ─────────────────► recv() → "hello"
```

> **IPC(프로세스 간 통신)** — 서로 다른 프로세스가 데이터를 주고받는 방법.\
> 예: 한 프로세스가 `queue.put()` 한 값을 다른 프로세스가 `queue.get()` 으로 받는다.

> **직렬화** — 파이썬 객체를 바이트 열로 바꿔 다른 곳으로 보낼 수 있게 하는 것(되돌리는 쪽은 역직렬화).\
> 예: `conn.send([1, 2, 3])` 는 리스트를 pickle 로 바꿔 보내고, `recv()` 가 다시 리스트로 되돌린다.

## 이 주제가 답하려는 질문

1. 메모리를 나눠 쓰지 않는 두 프로세스가 어떻게 값을 주고받나?
2. 받는 쪽은 「이제 더 올 것이 없다」를 어떻게 아나?
3. 큐가 비었거나 가득 찼을 때 `get` · `put` 은 어떻게 동작하고, 그것을 어떻게 바꾸나?
4. `Queue` 와 `Pipe` 중 어느 것을 언제 고르나?

## 동작 방식

### (1) Queue 로 생산자 → 소비자에게 보내고, `None` 으로 끝을 알린다

**언제 쓰나** — 한 프로세스가 만든 값을 다른 프로세스가 차례로 처리할 때 쓴다.
받는 쪽이 몇 개가 올지 모를 때 끝을 알리는 표시가 필요하다.

```text
입력 코드                                무엇이 일어나나                       결과
─────────────────────────────────────    ───────────────────────────────      ─────────────────────
c1.start(); p1.start()                   소비자 · 생산자 프로세스가 뜬다       두 프로세스가 동시에 돈다
consumer: item = queue.get()             큐가 비어 있으니 기다린다(블로킹)     아직 아무것도 안 찍힘
producer: queue.put("item-0 (PID:…)")    값을 직렬화해 큐에 싣는다             소비자가 깨어 "수신" 출력
producer: … count 번 반복 후 put(None)   종료 신호를 싣는다                    소비자가 None 을 받고 "종료" 출력, break
p1.join(); c1.join()                     부모가 두 프로세스의 끝을 기다린다    다음 절로 넘어간다
```

1. 부모 프로세스가 `Process(target=…, args=(queue, …))` 로 같은 큐를 두 자식에게 넘긴다.
2. 소비자는 먼저 시작되어도 `get()` 에서 멈춰 기다리므로 순서가 꼬이지 않는다.
3. 생산자는 `item-{i} (PID:{os.getpid()})` 꼴 문자열을 넣어, 어느 프로세스가 보냈는지 PID 로 드러낸다.
4. 생산자는 일을 다 하면 `None` 을 하나 넣는다.
5. 소비자는 `item is None` 을 보고 `"[이름] 종료"` 를 찍은 뒤 고리를 빠져나온다.
6. `None` 을 넣지 않으면 소비자는 마지막 `get()` 에서 영원히 기다린다.

> **sentinel(종료 신호)** — 진짜 데이터로는 나올 수 없는 값을 「끝」 표시로 약속해 보내는 것.\
> 예: 생산자가 마지막에 `queue.put(None)` 을 하고 소비자는 `if item is None: break` 로 멈춘다.

> **블로킹** — 호출한 함수가 조건이 채워질 때까지 돌아오지 않고 기다리는 것.\
> 예: 빈 큐에서 `queue.get()` 은 값이 들어올 때까지 다음 줄로 가지 않는다.

### (2) `put` · `get` 의 기다림을 조절한다 — `maxsize` · `block=False` · `timeout`

**언제 쓰나** — 생산자가 너무 빨라 큐가 한없이 커지는 것을 막거나, 소비자가 영원히 기다리지 않게 할 때 쓴다.

```text
호출                                큐 상태          무엇이 일어나나
──────────────────────────────────  ──────────────   ─────────────────────────────────
Queue(maxsize=3) 에 put(item)       이미 3개         자리가 날 때까지 기다린다(블로킹)
put(item, block=False)              이미 3개         바로 queue.Full 예외
put(item, timeout=1)                이미 3개         1초 기다려도 자리가 없으면 예외
get()                               비어 있음        값이 올 때까지 기다린다(블로킹)
get(block=False)                    비어 있음        바로 queue.Empty 예외
get(timeout=2)                      비어 있음        2초 안에 안 오면 queue.Empty 예외
```

1. `maxsize` 를 주지 않은 큐는 크기 제한이 없어 `put` 이 「가득 차서」 기다리는 일이 없다.
2. `maxsize=3` 을 주면 네 번째 `put` 부터는 누군가 `get` 할 때까지 기다린다.
3. `block=False` 는 「기다리지 말고 안 되면 바로 예외」다.
4. `timeout=초` 는 「그만큼만 기다리고 안 되면 예외」다.
5. 예외 이름은 `Full` · `Empty` 이고, 원본 주석은 이를 `queue.Full` · `queue.Empty` 로 적는다.

> **maxsize** — 큐에 동시에 담길 수 있는 항목 수의 상한.\
> 예: `multiprocessing.Queue(maxsize=3)` 은 세 개가 차면 다음 `put` 을 막는다.

### (3) Pipe 는 두 끝을 만들고, 한 끝에서 `send` 한 것을 다른 끝에서 `recv` 한다

**언제 쓰나** — 정확히 두 프로세스가 1:1 로 이야기할 때 쓴다.

```text
입력 코드                                         무엇이 일어나나                          결과
───────────────────────────────────────────────   ─────────────────────────────────────    ────────────────────────
parent_conn, child_conn = Pipe()                  연결된 두 끝을 만든다(기본 양방향)        두 Connection 객체
sender  ← child_conn,  data=["hello","world",42,[1,2,3]]
receiver← parent_conn
sender: conn.send(item)                           item 을 pickle 해 반대 끝으로 보낸다     receiver 의 recv() 가 깨어남
receiver: item = conn.recv()                      받은 바이트를 역직렬화한다               원래 객체(str · int · list)
sender: conn.send(None); conn.close()             종료 신호를 보내고 자기 끝을 닫는다       receiver 가 None 을 보고 break
```

1. `Pipe()` 는 `(parent_conn, child_conn)` 두 끝을 돌려준다.
2. 이름은 parent · child 지만 어느 끝을 어느 프로세스에 줄지는 코드가 정한다 — 예제는 child 끝을 송신자에게, parent 끝을 수신자에게 준다.
3. `send` 는 값을 pickle 로 바꿔 보내므로 문자열 · 정수 · 리스트를 그대로 보낼 수 있다.
4. `recv` 는 값이 올 때까지 기다린다(블로킹).
5. 기본값 `duplex=True` 이면 두 끝 모두 보내고 받을 수 있고, `duplex=False` 이면 한 방향만 된다.
6. 원본 주석에 따르면 한 끝을 닫으면 반대쪽에서 `EOFError` 가 날 수 있다.
7. 한 끝을 여러 프로세스가 동시에 쓰는 것은 안전하지 않다.

> **Connection** — `Pipe()` 가 돌려주는 끝 하나를 나타내는 객체. `send` · `recv` · `close` 를 가진다.\
> 예: `parent_conn.recv()` 는 `child_conn.send(x)` 로 보낸 `x` 를 받는다.

> **duplex** — 한 연결로 양쪽 모두 보내고 받을 수 있는지 정하는 `Pipe` 의 인자.\
> 예: `Pipe(duplex=False)` 는 한쪽은 받기만, 다른 쪽은 보내기만 한다.

### (4) 여러 생산자가 한 큐에 넣고, 소비자는 「개수」로 끝낸다

**언제 쓰나** — 일하는 프로세스 여럿이 결과를 한곳으로 모을 때 쓴다.
`Queue` 는 여러 프로세스가 동시에 `put` · `get` 해도 안전하다.

```text
P0: put(("P0",0,pid0)) put(("P0",1,pid0)) put(("P0",2,pid0))  ─┐
                                                               ├─► shared_queue ─► Consumer: get(timeout=2) × 6
P1: put(("P1",0,pid1)) put(("P1",1,pid1)) put(("P1",2,pid1))  ─┘
```

1. 생산자 둘(`P0`, `P1`)이 각각 `(이름, 인덱스, PID)` 튜플을 3개씩 넣으므로 모두 6개다.
2. 생산자는 sentinel 을 넣지 않는다.
3. 소비자는 `total=6` 을 받아 6개를 셀 때까지만 돈다 — 「몇 개가 올지 안다」는 약속으로 끝을 정한 것이다.
4. 안전장치로 `get(timeout=2)` 를 써서 2초 안에 아무것도 안 오면 예외가 나고, `except Exception: break` 로 빠져나온다.
5. 두 생산자가 동시에 돌기 때문에 `P0` 와 `P1` 의 항목이 어떤 차례로 섞여 도착할지는 코드가 정하지 않는다(원본에 근거 없음 — 추론).
6. 받은 튜플은 `producer, idx, pid = item` 으로 풀어 `#번호: 생산자-인덱스 (from PID:…)` 꼴로 찍는다.

### (5) 프로세스를 띄우고 기다린다 — `Process` · `start` · `join` · `__main__` 보호

**언제 쓰나** — 위의 모든 통신은 자식 프로세스를 띄워야 일어난다.

```text
multiprocessing.Process(target=함수, args=(인자들))   → 프로세스 객체(아직 안 돈다)
p.start()                                             → 새 프로세스에서 함수가 돌기 시작
p.join()                                              → 부모가 p 가 끝날 때까지 기다림
if __name__ == '__main__':                            → 자식이 이 파일을 다시 불러올 때 이 블록은 안 돈다
```

1. `Process` 는 `target` 함수와 `args` 튜플을 받는다.
2. `start()` 를 불러야 실제로 새 프로세스가 생긴다.
3. `join()` 은 그 프로세스가 끝나야 돌아온다 — 예제는 절마다 `join` 해서 다음 절의 출력이 앞 절과 섞이지 않게 한다.
4. 원본 주석은 fork/spawn 보호를 위해 `if __name__ == '__main__':` 가 필수이고 특히 Windows 에서 그렇다고 적는다.
5. 보호가 없으면 자식이 파일을 다시 읽을 때 프로세스를 띄우는 코드까지 다시 돌게 된다(원본에 근거 없음 — 추론).
6. 원본 주석은 각 프로세스가 GIL 을 따로 가져 CPU 를 많이 쓰는 일에 맞는다고 적는다.

> **PID** — 운영체제가 프로세스마다 붙이는 번호.\
> 예: `os.getpid()` 는 지금 코드가 도는 프로세스의 번호를 돌려준다.

> **GIL** — 한 파이썬 프로세스 안에서 한 번에 한 스레드만 파이썬 코드를 돌리게 하는 잠금.\
> 예: 스레드 여럿으로 계산을 나눠도 한 프로세스 안이면 동시에 계산하지 못한다.

## 문법 — 형태와 규칙

```python
import multiprocessing

def work(q):
    q.put("hi")          # 보내기
    q.put(None)          # 끝 표시

if __name__ == '__main__':
    q = multiprocessing.Queue()            # maxsize=3 처럼 상한을 줄 수 있다
    p = multiprocessing.Process(target=work, args=(q,))
    p.start()
    while (x := q.get()) is not None:      # 받기(블로킹)
        print(x)
    p.join()

    a, b = multiprocessing.Pipe()          # duplex=True 가 기본
    b.send([1, 2, 3]); print(a.recv())     # 한 끝에서 보내고 다른 끝에서 받기
```

- `Queue()` — 크기 제한 없는 큐. `Queue(maxsize=n)` — 상한 n.
- `put(item)` · `get()` — 기본은 블로킹이다.
- `put(item, block=False)` — 가득 차면 바로 `Full` 예외. `put(item, timeout=t)` — t초 뒤 예외.
- `get(block=False)` — 비어 있으면 바로 `Empty` 예외. `get(timeout=t)` — t초 뒤 예외.
- `Pipe()` — `(conn1, conn2)` 두 끝. `Pipe(duplex=False)` — 단방향.
- `conn.send(obj)` · `conn.recv()` — pickle 로 바꿔 보내고 되돌려 받는다. `recv` 는 블로킹이다.
- `conn.close()` — 자기 끝을 닫는다.
- `Process(target=f, args=(…,))` → `start()` → `join()`.
- 프로세스를 띄우는 코드는 `if __name__ == '__main__':` 아래에 둔다.

## 어디서 틀리나

### 1. sentinel 을 빠뜨리면 소비자가 끝나지 않는다
`while True: item = queue.get()` 꼴 소비자는 `None` 이 오지 않으면 마지막 `get()` 에서 멈춘다.
부모의 `c1.join()` 도 같이 멈추므로 프로그램 전체가 끝나지 않는다.
종료 신호로 `None` 을 쓰는 것이 원본이 말하는 일반적 패턴이다.

### 2. 소비자가 여럿이면 sentinel 하나로 부족하다
`None` 하나는 한 소비자만 꺼낸다.
나머지 소비자는 계속 기다린다.
소비자 수만큼 `None` 을 넣거나, 예제의 `multi_consumer` 처럼 개수 · `timeout` 으로 끝을 정해야 한다(원본에 근거 없음 — 추론).

### 3. 블로킹이 기본이다
`put` · `get` · `recv` 는 기본적으로 기다린다.
상대 프로세스가 죽었거나 아무것도 안 보내면 영원히 기다릴 수 있다.
`block=False` 나 `timeout` 으로 기다림에 한도를 둔다.

### 4. `except Exception` 은 너무 넓다
`multi_consumer` 는 `get(timeout=2)` 의 `Empty` 를 잡으려고 `except Exception` 을 쓴다.
이러면 튜플 풀기 실패 같은 다른 오류도 조용히 `break` 로 삼켜진다.
원본 주석대로 기다린 예외는 `queue.Empty` 이므로 그 예외만 잡는 편이 의도가 드러난다(원본에 근거 없음 — 추론).

### 5. 변수 이름 `queue` 가 표준 모듈 이름과 겹친다
예제의 `__main__` 블록은 큐 객체를 `queue` 라는 변수에 담는다.
`queue.Empty` · `queue.Full` 은 표준 `queue` 모듈의 이름인데, 이 파일은 그 모듈을 `import` 하지 않았다.
같은 자리에서 `except queue.Empty` 를 쓰면 큐 객체에서 `Empty` 를 찾게 되어 깨진다(원본에 근거 없음 — 추론).

### 6. Pipe 한 끝을 여러 프로세스가 함께 쓰지 않는다
`Pipe` 는 1:1 통신에 맞춘 것이고, 여러 프로세스가 같은 끝에 동시에 접근하면 안전하지 않다.
보내는 쪽이나 받는 쪽이 여럿이면 `Queue` 를 쓴다.

### 7. 「크기 제한」 절은 큐를 만들기만 한다
`bounded_q = multiprocessing.Queue(maxsize=3)` 은 만들어지지만 한 번도 쓰이지 않는다.
그 절의 네 줄은 `print` 로 찍는 안내문일 뿐, `Full` · `Empty` 가 실제로 나는 장면은 없다.

### 8. 원본 끝의 `# 출력:` 주석은 실제 출력이 아니다
**원본의 주장** — `[Consumer] 수신: item-0 (PID:12345)` 처럼 나온다.
**왜 의심스러운가** — PID 는 실행할 때마다 운영체제가 정하므로 `12345` 는 자리값으로 보인다.
코드는 `"  [..."` 처럼 앞에 공백 두 칸을 찍는데 주석에는 없다.
Pipe 절의 데이터는 `["hello", "world", 42, [1, 2, 3]]` 네 개인데 주석은 세 줄에서 끊긴다.
중간 절들은 `...` 로 생략되어 있다.

### 9. 여러 생산자의 순서를 기대하지 않는다
`P0` 와 `P1` 이 동시에 `put` 하므로 소비자가 받는 차례는 두 프로세스의 실행 타이밍에 달려 있다.
`#1` 이 반드시 `P0-0` 이라고 가정하면 안 된다(원본에 근거 없음 — 추론).

### 10. Queue 가 Pipe 보다 느리다는 말에는 수치가 없다
원본은 「Queue 는 Pipe 보다 느리다」「Pipe 는 더 빠르다」고 말하지만 얼마나 차이 나는지는 적지 않았다.
고를 때는 속도보다 「1:1 인가 다대다인가」를 먼저 본다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `put` · `get` · `recv` 는 기본이 블로킹이다 | `multiprocessing` 표준 라이브러리의 API 동작 |
| `Queue` 는 여러 생산자 · 소비자에 안전하다 | `multiprocessing` 표준 라이브러리의 API 약속 |
| `Queue` 는 내부적으로 Lock(과 파이프)을 쓴다 | 표준 라이브러리 구현 방식 — 원본 주석의 서술 (확인 필요) |
| `send` · `put` 은 pickle 로 직렬화한다 | `multiprocessing` 의 동작 — 원본 주석의 서술 |
| Pipe 가 Queue 보다 빠르다 | 원본의 주장 — 수치 없음 (확인 필요) |
| `__main__` 보호가 필수다(특히 Windows) | 프로세스 시작 방식(fork/spawn)에 달린 것 — 플랫폼마다 다르다 (확인 필요) |
| 각 프로세스가 GIL 을 따로 가진다 | CPython 구현 — 언어 보장 아님 |
| PID 값 | 운영체제가 실행 때마다 정한다 |
| 여러 생산자 항목이 섞이는 차례 | 아무도 보장하지 않는다 — 실행 타이밍 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 프로세스 둘이 1:1 로 주고받는다 | `Pipe()` | — |
| 일꾼 여럿이 결과를 한곳에 모은다 | `Queue()` | 끝 하나를 공유하는 `Pipe` |
| 생산자가 너무 빨라 메모리가 걱정된다 | `Queue(maxsize=n)` | 상한 없는 `Queue()` |
| 받는 쪽이 개수를 모른다 | sentinel `None` | 무한 `get()` 만 두기 |
| 받는 쪽이 개수를 안다 | 개수 세기 + `timeout` | sentinel 에만 기대기 |
| 상대가 멈춰도 계속 가야 한다 | `block=False` · `timeout` | 기본 블로킹 호출 |
| 한 방향으로만 보낸다 | `Pipe(duplex=False)` | 쓸모없는 양방향 |

## 핵심 문장

1. **프로세스는 메모리를 나누지 않으므로 값은 직렬화되어 `Queue` 나 `Pipe` 로 건너간다.**
2. **`Queue` 는 다대다에 안전한 우체통, `Pipe` 는 1:1 에 맞춘 두 끝짜리 전화선이다.**
3. **`put` · `get` · `recv` 는 기본이 블로킹이고, `block=False` · `timeout` 으로 기다림을 끊는다.**
4. **받는 쪽의 끝은 sentinel `None` 이나 「정해진 개수 + timeout」으로 알린다.**
5. **프로세스는 `start` 로 띄우고 `join` 으로 기다리며, 그 코드는 `if __name__ == '__main__':` 아래에 둔다.**

## 관련 자료

- `multiprocessing-shared` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `process-pool` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `threading-condition` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `asyncio-queue` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/concurrency-deep.json` 의 `multiprocessing-queue`

## 용어 풀이

- **IPC(프로세스 간 통신)** — 서로 다른 프로세스가 데이터를 주고받는 방법.
- **프로세스** — 운영체제가 따로 메모리를 주고 돌리는 프로그램 실행 단위.
- **직렬화 · 역직렬화** — 객체를 바이트로 바꾸는 것과 그 반대.
- **pickle** — 파이썬 객체를 직렬화하는 표준 방식.
- **`Queue`** — 여러 프로세스가 함께 쓰는 선입선출 통로.
- **`Pipe`** — 연결된 두 끝(`Connection`)을 만드는 1:1 통로.
- **`Connection`** — `Pipe` 의 끝 하나. `send` · `recv` · `close` 를 가진다.
- **duplex** — 한 연결로 양방향이 되는지 정하는 인자.
- **블로킹** — 조건이 채워질 때까지 호출이 돌아오지 않는 것.
- **sentinel** — 「끝」을 뜻하도록 약속한 특별한 값(여기서는 `None`).
- **maxsize** — 큐에 담길 항목 수의 상한.
- **`Full` · `Empty`** — 가득 찬 큐에 기다리지 않고 넣을 때, 빈 큐에서 기다리지 않고 꺼낼 때 나는 예외.
- **생산자 · 소비자** — 데이터를 만들어 넣는 쪽과 꺼내 쓰는 쪽.
- **`start` · `join`** — 프로세스를 실제로 띄우는 것, 끝날 때까지 기다리는 것.
- **PID** — 운영체제가 프로세스마다 붙이는 번호.
- **GIL** — 한 CPython 프로세스 안에서 한 번에 한 스레드만 파이썬 코드를 돌리게 하는 잠금.
- **fork · spawn** — 자식 프로세스를 만드는 방식. spawn 은 새 인터프리터가 파일을 다시 불러온다.

## 더 들어가면

- 공식 문서는 한 프로세스가 넣은 항목끼리는 넣은 차례대로 도착하지만, 여러 프로세스가 넣은 항목 사이의 차례는 어긋날 수 있다고 적는 것으로 안다 (확인 필요).
- `multiprocessing.Queue` 의 `put` 은 값을 곧장 파이프에 쓰지 않고 내부 버퍼와 백그라운드 스레드(feeder)를 거쳐 보낸다고 알려져 있다 (확인 필요).
- 그 때문에 큐에 넣은 항목이 다 빠져나가지 않은 상태에서 그 프로세스를 `join` 하면 멈출 수 있다는 주의가 문서에 있다 (확인 필요).
- `Pipe` 의 `recv` 가 `EOFError` 를 내려면 반대쪽 끝을 가진 모든 프로세스가 그 끝을 닫아야 한다 — 예제의 부모 프로세스는 두 끝을 모두 쥔 채로 있다 (확인 필요).
- `Connection.poll(timeout)` 으로 `recv` 전에 받을 것이 있는지 볼 수 있다 (확인 필요).
- 작업을 여러 프로세스에 나눠 결과만 모을 때는 `multiprocessing.Pool` 이나 `concurrent.futures.ProcessPoolExecutor` 가 큐를 직접 다루는 것보다 간단할 때가 많다 (확인 필요).
- 공유 메모리(`multiprocessing.shared_memory`, `Value`, `Array`)는 직렬화 없이 같은 메모리를 보는 다른 길이다 (확인 필요).
