# python/python-concurrency/08 — 멀티프로세싱 Queue/Pipe — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 네 줄 — 수신 세 줄 뒤에 `종료` 한 줄, PID 는 생산자의 것

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`C` 는 네 줄을 찍는다.

```text
  [C] 수신: item-0 (PID:<생산자 PID>)
  [C] 수신: item-1 (PID:<생산자 PID>)
  [C] 수신: item-2 (PID:<생산자 PID>)
  [C] 종료
```

`<생산자 PID>` 자리의 숫자는 실행할 때마다 운영체제가 정하므로 미리 알 수 없다.
세 줄 모두 같은 숫자다.

**왜 그런가**
`producer_proc` 는 `range(3)` 으로 세 항목을 넣고 끝에 `None` 을 넣는다.
`consumer_proc` 는 문자열 셋을 받을 때마다 `수신` 줄을 찍고, `None` 을 받으면 `종료` 를 찍고 `break` 한다.
문자열은 생산자 프로세스 안에서 `os.getpid()` 로 만들어지므로 PID 는 생산자의 번호다.
소비자가 먼저 `start` 되어도 빈 큐의 `get()` 에서 기다리므로 순서는 같다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 네 줄 — 마지막은 `[1, 2, 3]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [R] Pipe 수신: hello
  [R] Pipe 수신: world
  [R] Pipe 수신: 42
  [R] Pipe 수신: [1, 2, 3]
```

`종료` 같은 줄은 없다.

**왜 그런가**
`pipe_sender` 는 리스트의 네 항목을 차례로 `send` 한 뒤 `None` 을 보낸다.
`send` 는 pickle 로 보내고 `recv` 가 되돌리므로 마지막 항목은 리스트 그대로 받아지고, `print` 는 그것을 `[1, 2, 3]` 으로 찍는다.
`pipe_receiver` 는 `None` 을 받으면 아무것도 찍지 않고 `break` 한다.
원본 끝의 `# 출력:` 주석이 `42` 에서 끊긴 것은 실제 출력이 아니다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 8」.

### 3. 여섯 줄을 찍고, 약 2초 더 기다린 뒤 조용히 끝난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
소비자는 `#1` 부터 `#6` 까지 여섯 줄을 찍는다.
`P0` 와 `P1` 의 항목이 어떤 차례로 섞일지는 정해져 있지 않다.
여섯 번째 항목을 받은 뒤 `received` 는 6 이고 `6 < 8` 이므로 다시 `get(timeout=2)` 를 부른다.
더 올 항목이 없으니 약 2초 뒤 `queue.Empty` 가 나고, `except Exception: break` 로 빠져나온다.
오류 메시지는 찍히지 않는다.

**왜 그런가**
생산자 둘이 3개씩, 모두 6개만 넣는다.
`multi_consumer` 는 개수(`total`)로 끝을 정하고, 개수를 못 채우면 `timeout` 이 안전장치로 고리를 끊는다.
`timeout` 이 없었다면 일곱 번째 `get()` 에서 영원히 기다렸을 것이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」 · 「어디서 틀리나 9」.

### 4. 소비자가 마지막 `get()` 에서 영원히 기다리고, 부모의 `join` 도 같이 멈추기 때문이다

`consumer_proc` 는 `while True` 안에서 `queue.get()` 을 부르고, 멈추는 길은 `None` 을 받는 것 하나뿐이다.
`get()` 은 기본이 블로킹이므로 생산자가 끝난 뒤 빈 큐에서 기다리기만 한다.
부모는 `c1.join()` 에서 소비자가 끝나기를 기다리므로 프로그램 전체가 끝나지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. 자식 프로세스가 파일을 다시 불러올 때 프로세스를 띄우는 코드가 또 돌지 않게 하려고

원본 주석은 fork/spawn 보호를 위해 이 블록이 필수이고, 특히 Windows 에서 그렇다고 적는다.
spawn 방식에서는 자식이 이 파일을 다시 불러오는데, 보호가 없으면 그때 `Process(...).start()` 까지 다시 실행되어 자식이 또 자식을 띄우려 한다(원본에 근거 없음 — 추론).
`__main__` 블록은 파일을 직접 실행한 처음 프로세스에서만 돈다.
근거: 2-summary 「동작 방식 (5)」.

### 6. 기본은 자리가 날 때까지 기다리고, `block=False` 는 바로 예외, `timeout=1` 은 1초 기다린 뒤 예외

- `put(item)` — 누군가 `get` 해서 자리가 날 때까지 기다린다(블로킹).
- `put(item, block=False)` — 기다리지 않고 바로 `queue.Full` 예외가 난다.
- `put(item, timeout=1)` — 1초 동안 기다리고, 그 안에 자리가 나지 않으면 예외가 난다.

빈 큐의 `get` 도 같은 짝으로 동작한다(`get(block=False)` 는 바로 `queue.Empty`).
예제의 `bounded_q` 는 만들기만 하고 쓰지 않으므로 이 장면은 안내문으로만 나온다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 7」.

### 7. Pipe 한 끝의 동시 접근은 안전하지 않으므로 `Queue` 로 바꾼다

`Pipe` 는 1:1 통신에 맞춘 것이고, 원본은 여러 프로세스가 동시에 접근하면 안전하지 않다고 적는다.
보내는 쪽이 셋이면 다대일이므로, 여러 생산자에 안전한 `Queue` 를 쓴다 — 예제의 「다중 생산자-소비자」 절이 바로 그 꼴이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」 · 「언제 쓰고 언제 안 쓰나」.

### 8. 프로세스는 메모리를 나누지 않으므로 값을 바이트로 바꿔 건네야 한다 — 스레드는 같은 메모리를 본다

각 프로세스는 따로 메모리를 가지므로, 한 프로세스의 리스트 객체를 다른 프로세스가 그대로 가리킬 수 없다.
그래서 `send` · `put` 은 값을 pickle 로 직렬화해 보내고, 받는 쪽이 역직렬화해 새 객체를 만든다 — 그래서 리스트가 리스트로 나온다.
같은 프로세스 안의 스레드는 메모리를 함께 쓰므로 객체를 그대로 나눌 수 있다(원본에 근거 없음 — 추론).
대신 원본 주석대로 한 프로세스 안의 스레드는 GIL 하나를 나눠 쓰고, 프로세스는 GIL 을 따로 가져 CPU 를 많이 쓰는 일에 맞는다.
근거: 2-summary 「한눈에」 · 「동작 방식 (3)」 · 「동작 방식 (5)」.

### 9. 한 소비자만 `None` 을 받고 다른 하나는 영원히 기다린다 — 개수 + timeout 은 sentinel 없이 끝을 정하는 다른 길이다

`None` 하나는 한 번만 꺼내지므로, 그것을 꺼낸 소비자만 `종료` 하고 나머지는 빈 큐의 `get()` 에서 멈춘다.
소비자 수만큼 `None` 을 넣거나, 끝을 다른 방법으로 정해야 한다(원본에 근거 없음 — 추론).
`multi_consumer` 는 sentinel 대신 「받을 개수(`total`)」와 「`get(timeout=2)`」로 끝을 정한다 — 생산자가 끝 표시를 넣지 않아도 멈추는 방식이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. Queue · Pipe 로 프로세스끼리 주고받는 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 항목 문자열을 넣고 0.05초 쉰다 | `producer_proc` 의 `queue.put(item)` · `time.sleep(0.05)` |
| 2. 다 넣은 뒤 `None` | `producer_proc` 의 `queue.put(None)` |
| 3. 꺼내서 `수신` 줄 찍기 | `consumer_proc` 의 `item = queue.get()` · `print(f"  [{name}] 수신: {item}")` |
| 4. `None` 이면 `종료` 찍고 멈춤 | `consumer_proc` 의 `if item is None:` · `break` |
| 5. 큐 · 생산자(5) · 소비자 프로세스, 소비자 먼저 시작 | `queue = multiprocessing.Queue()` · `p1` · `c1` · `c1.start()` 다음 `p1.start()` |
| 6. 둘 다 기다리고 빈 줄 | `p1.join()` · `c1.join()` · `print()` |
| 7. `maxsize=3` 큐와 안내 네 줄 | `bounded_q = multiprocessing.Queue(maxsize=3)` · 뒤의 `print` 네 줄 |
| 8. 하나씩 보내고 `None` 뒤 닫기 | `pipe_sender` 의 `conn.send(item)` · `conn.send(None)` · `conn.close()` |
| 9. 받아 찍고 `None` 이면 멈춘 뒤 닫기 | `pipe_receiver` 의 `conn.recv()` · `if item is None: break` · `conn.close()` |
| 10. 두 끝을 나눠 주고 수신자 먼저 시작 | `parent_conn, child_conn = multiprocessing.Pipe()` · `sender` · `receiver` · `receiver.start()` |
| 11. 튜플을 넣고 0.02초 쉰다 | `multi_producer` 의 `queue.put((name, i, os.getpid()))` |
| 12. `total` 개까지 2초 한도로 꺼내 찍기 | `multi_consumer` 의 `queue.get(timeout=2)` · `producer, idx, pid = item` · `print(...)` |
| 13. 시간이 넘으면 멈춤 | `multi_consumer` 의 `except Exception: break` |
| 14. 공유 큐 · 생산자 둘 · 소비자(6) | `shared_queue` · `producers` 리스트 컴프리헨션 · `consumer` · `start` · `join` 고리 |
| 15. 비교 안내 | `=== Queue vs Pipe ===` 아래 `print` 줄들 |
| 16. 생성 보호 | `if __name__ == '__main__':` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-concurrency/reference/multiprocessing-queue.py`

```python
# [동시성 심화] 멀티프로세싱 Queue/Pipe
# 설명: multiprocessing.Queue와 Pipe를 이용한 프로세스 간 통신(IPC)
# 팁: Queue는 다중 생산자/소비자에 안전하지만 Pipe보다 느리다. Pipe는 1:1 통신에 최적화되어 있고 더 빠르다. 종료 신호로 None(sentinel)을 사용하는 패턴이 일반적이다. Queue.put()과 get()은 기본적으로 블로킹이며, block=False나 timeout으로 제어할 수 있다.

# multiprocessing: 프로세스 기반 병렬 처리 (각 프로세스 독립 GIL → CPU 바운드에 적합)
import multiprocessing
# time: 작업 시뮬레이션용 sleep
import time
# os: 현재 프로세스 PID 조회
import os

# === multiprocessing.Queue 기본 ===
# Queue로 데이터를 보내는 생산자 프로세스 본체
def producer_proc(queue, count):
    """데이터를 Queue에 넣는 프로세스"""
    for i in range(count):
        # PID를 함께 넣어 어느 프로세스가 보냈는지 확인
        item = f"item-{i} (PID:{os.getpid()})"
        # put: 항목을 큐에 적재 (직렬화/역직렬화로 프로세스 간 전달됨)
        queue.put(item)
        time.sleep(0.05)
    # sentinel(None): 종료 신호 — 소비자가 None을 보면 종료
    queue.put(None)  # 종료 신호 (sentinel)

# Queue에서 데이터를 받는 소비자 프로세스 본체
def consumer_proc(queue, name):
    """Queue에서 데이터를 꺼내는 프로세스"""
    while True:
        # get: 데이터가 올 때까지 블로킹
        item = queue.get()  # 데이터가 올 때까지 블로킹
        if item is None:  # 종료 신호
            print(f"  [{name}] 종료")
            break
        print(f"  [{name}] 수신: {item}")

# === Pipe 기본 ===
# Pipe의 한쪽 끝(conn)으로 데이터를 송신하는 함수
def pipe_sender(conn, data):
    """Pipe로 데이터 전송"""
    for item in data:
        # send: pickle 직렬화하여 다른 끝으로 전송
        conn.send(item)
        time.sleep(0.05)
    conn.send(None)  # 종료 신호
    # close: Pipe 끝 닫기 (반대쪽에서 EOFError 가능)
    conn.close()

# Pipe의 한쪽 끝(conn)으로 데이터를 수신하는 함수
def pipe_receiver(conn, name):
    """Pipe에서 데이터 수신"""
    while True:
        # recv: 데이터가 올 때까지 블로킹, pickle 역직렬화
        item = conn.recv()  # 데이터 대기
        if item is None:
            break
        print(f"  [{name}] Pipe 수신: {item}")
    conn.close()

# === 다중 생산자-소비자 ===
# 다중 생산자: (이름, 인덱스, PID) 튜플을 큐에 넣음
def multi_producer(queue, name, count):
    for i in range(count):
        queue.put((name, i, os.getpid()))
        time.sleep(0.02)

# 다중 소비자: 정해진 개수(total)만큼 소비하면 종료
def multi_consumer(queue, name, total):
    received = 0
    while received < total:
        try:
            # timeout: 2초 안에 항목이 안 오면 queue.Empty 발생
            item = queue.get(timeout=2)
            received += 1
            producer, idx, pid = item
            print(f"  [{name}] #{received}: {producer}-{idx} (from PID:{pid})")
        except Exception:
            break

# 멀티프로세싱은 fork/spawn 보호를 위해 if __name__ == '__main__' 필수 (특히 Windows)
if __name__ == '__main__':
    # === Queue 기본 ===
    print("=== multiprocessing.Queue ===")
    # multiprocessing.Queue: 다중 생산자/소비자 안전, 내부적으로 파이프 + 락 + 직렬화
    queue = multiprocessing.Queue()

    # Process: 별도 프로세스 생성 (target 함수 + args)
    p1 = multiprocessing.Process(target=producer_proc, args=(queue, 5))
    c1 = multiprocessing.Process(target=consumer_proc, args=(queue, "Consumer"))

    # start: 프로세스 시작
    c1.start()
    p1.start()
    # join: 해당 프로세스가 끝날 때까지 대기
    p1.join()
    c1.join()
    print()

    # === Queue 크기 제한 ===
    print("=== Queue 크기 제한 ===")
    # maxsize 지정 시 가득 차면 put이 블로킹
    bounded_q = multiprocessing.Queue(maxsize=3)
    # 옵션 안내
    print(f"  maxsize=3: 가득 차면 put()이 블로킹")
    print(f"  put(item, block=False): 가득 차면 queue.Full 예외")
    print(f"  put(item, timeout=1): 1초 내 공간 없으면 예외")
    print(f"  get(block=False): 비어있으면 queue.Empty 예외")
    print()

    # === Pipe ===
    print("=== Pipe ===")
    # Pipe(): 양방향 (parent_conn, child_conn) 두 끝 반환, duplex=False면 단방향
    parent_conn, child_conn = multiprocessing.Pipe()

    # 한쪽 끝을 송신, 다른 쪽을 수신으로 사용
    sender = multiprocessing.Process(
        target=pipe_sender, args=(child_conn, ["hello", "world", 42, [1, 2, 3]])
    )
    receiver = multiprocessing.Process(
        target=pipe_receiver, args=(parent_conn, "Receiver")
    )

    receiver.start()
    sender.start()
    sender.join()
    receiver.join()
    print()

    # === 다중 생산자-소비자 ===
    print("=== 다중 생산자-소비자 ===")
    shared_queue = multiprocessing.Queue()

    # 두 생산자가 같은 큐에 동시 put — Queue는 다중 생산자에 안전
    producers = [
        multiprocessing.Process(target=multi_producer, args=(shared_queue, f"P{i}", 3))
        for i in range(2)
    ]
    consumer = multiprocessing.Process(
        target=multi_consumer, args=(shared_queue, "Consumer", 6)
    )

    consumer.start()
    for p in producers: p.start()
    for p in producers: p.join()
    consumer.join()
    print()

    # === Queue vs Pipe 비교 ===
    print("=== Queue vs Pipe ===")
    # 선택 가이드
    print("Queue:")
    print("  - 다중 생산자/소비자 안전")
    print("  - 내부적으로 Lock 사용")
    print("  - maxsize로 크기 제한 가능")
    print("  - 약간 느리지만 안전")
    print("Pipe:")
    print("  - 1:1 통신에 최적화")
    print("  - Queue보다 빠름")
    print("  - duplex=True(기본): 양방향, duplex=False: 단방향")
    print("  - 다중 프로세스 동시 접근 시 안전하지 않음")

# 출력:
# === multiprocessing.Queue ===
# [Consumer] 수신: item-0 (PID:12345)
# [Consumer] 수신: item-1 (PID:12345)
# ...
# === Pipe ===
# [Receiver] Pipe 수신: hello
# [Receiver] Pipe 수신: world
# [Receiver] Pipe 수신: 42
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 받는 쪽(`c1` · `receiver` · `consumer`)을 먼저 `start` 해도 안전한 것은 `get` · `recv` 가 값이 올 때까지 기다리기 때문이다.
- 1:1 장면은 sentinel `None` 으로, 다대일 장면은 「개수 + `timeout`」으로 끝을 정한다 — 두 방법을 나란히 보는 것이 이 데모의 요점이다.
- 시작 코드의 `def main(): … main()` 꼴은 정답에서 `if __name__ == '__main__':` 블록이 된다.
- 절마다 `join` 해 두어야 다음 절의 출력이 앞 절과 섞이지 않는다.
- `except Exception` 은 정답 코드 그대로지만, 기다린 예외는 `Empty` 하나라는 점을 기억해 둔다.
- PID 숫자와 다중 생산자 항목의 차례는 실행마다 달라질 수 있으니 확인할 때 그 둘은 기준으로 삼지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
