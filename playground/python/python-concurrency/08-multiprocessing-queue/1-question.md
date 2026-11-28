# python/python-concurrency/08 — 멀티프로세싱 Queue/Pipe — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 생산자가 세 개를 보내면 소비자가 찍는 줄 (예측)

```python
# 질문용 발췌 — producer_proc · consumer_proc 는 원본 그대로
queue = multiprocessing.Queue()
p = multiprocessing.Process(target=producer_proc, args=(queue, 3))
c = multiprocessing.Process(target=consumer_proc, args=(queue, "C"))
c.start(); p.start(); p.join(); c.join()
```

- 소비자 `C` 는 모두 몇 줄을 찍고, 마지막 줄은 무엇인가?
- 각 줄의 `PID:` 뒤 숫자는 어느 프로세스의 번호인가?

### 2. Pipe 로 네 가지 값을 보내면 (예측)

```python
# 질문용 발췌 — pipe_sender · pipe_receiver 는 원본 그대로
parent_conn, child_conn = multiprocessing.Pipe()
s = multiprocessing.Process(target=pipe_sender, args=(child_conn, ["hello", "world", 42, [1, 2, 3]]))
r = multiprocessing.Process(target=pipe_receiver, args=(parent_conn, "R"))
r.start(); s.start(); s.join(); r.join()
```

- 수신자 `R` 는 몇 줄을 찍고, 마지막 줄은 무엇인가?

### 3. 소비자가 기다리는 개수를 8 로 바꾸면 (예측)

```python
# 질문용 발췌 — multi_producer · multi_consumer 는 원본 그대로
shared_queue = multiprocessing.Queue()
producers = [multiprocessing.Process(target=multi_producer, args=(shared_queue, f"P{i}", 3)) for i in range(2)]
consumer = multiprocessing.Process(target=multi_consumer, args=(shared_queue, "Consumer", 8))
consumer.start()
for p in producers: p.start()
for p in producers: p.join()
consumer.join()
```

- 소비자는 몇 줄을 찍고, 마지막 항목을 받은 뒤 언제 어떻게 끝나는가?

### 4. 생산자가 마지막에 `None` 을 넣는 까닭 (왜)

- `producer_proc` 끝의 `queue.put(None)` 을 지우면 왜 프로그램 전체가 끝나지 않는가?

### 5. 프로세스를 띄우는 코드를 `if __name__ == '__main__':` 아래에 두는 까닭 (왜)

- 이 보호가 왜 필요하다고 하는가?

### 6. `maxsize=3` 큐가 가득 찼을 때 (경계)

- 가득 찬 큐에 `put(item)` · `put(item, block=False)` · `put(item, timeout=1)` 을 부르면 각각 어떻게 다른가?

### 7. 보내는 프로세스가 셋이 되면 (경계)

- 세 프로세스가 같은 `Pipe` 끝으로 동시에 `send` 하려 한다면 어떤 문제가 있고 무엇으로 바꿔야 하는가?

### 8. 리스트를 보내도 받는 쪽에서 리스트로 나오는 까닭 — 스레드와 견주기 (연결)

- 프로세스 사이에서는 왜 값을 직렬화해 보내야 하고, 이것이 같은 프로세스 안의 스레드끼리 값을 나눌 때와 어떻게 다른가?

### 9. 소비자가 둘일 때의 종료 방법 (연결)

- `consumer_proc` 같은 소비자를 둘 띄우고 생산자가 `None` 을 하나만 넣으면 어떻게 되고, `multi_consumer` 의 끝내는 방식은 이 문제와 어떻게 이어지는가?

## 실습

### 실습 1. Queue · Pipe 로 프로세스끼리 주고받는 데모 만들기

**만들 것** — 한 파일 안에서 네 장면을 차례로 보여 주는 스크립트를 만든다.
Queue 로 1:1 주고받기, Queue 크기 제한 안내, Pipe 로 1:1 주고받기, 두 생산자 → 한 소비자 모으기, 그리고 Queue 와 Pipe 비교 안내를 찍는다.

**요구 조건**

1단계 — Queue 기본
1. `producer_proc(queue, count)` 는 `count` 번 돌며 `item-{i} (PID:{현재 PID})` 문자열을 큐에 넣고, 넣을 때마다 0.05초 쉰다.
2. `producer_proc` 는 다 넣은 뒤 종료 신호 `None` 을 넣는다.
3. `consumer_proc(queue, name)` 는 큐에서 하나씩 꺼내(기다리며) `  [name] 수신: 항목` 을 찍는다.
4. `consumer_proc` 는 `None` 을 받으면 `  [name] 종료` 를 찍고 멈춘다.
5. 메인에서 큐 하나를 만들고, 생산자(`count=5`)와 소비자(`"Consumer"`)를 프로세스로 띄운다 — 소비자를 먼저 `start` 한다.
6. 두 프로세스를 `join` 한 뒤 빈 줄을 찍는다.

2단계 — 크기 제한 안내
7. `maxsize=3` 인 큐를 만들고, 블로킹 · `block=False` · `timeout` · `get(block=False)` 의 동작을 설명하는 네 줄을 찍는다.

3단계 — Pipe
8. `pipe_sender(conn, data)` 는 `data` 의 항목을 하나씩 보내고(사이 0.05초), 끝에 `None` 을 보낸 뒤 자기 끝을 닫는다.
9. `pipe_receiver(conn, name)` 는 받을 때마다 `  [name] Pipe 수신: 항목` 을 찍고, `None` 을 받으면 멈춘 뒤 자기 끝을 닫는다.
10. 메인에서 `Pipe()` 로 두 끝을 만들고, 한 끝은 송신자(데이터 `["hello", "world", 42, [1, 2, 3]]`), 다른 끝은 수신자(`"Receiver"`)에게 준다 — 수신자를 먼저 `start` 하고 둘을 `join` 한다.

4단계 — 다중 생산자 · 한 소비자
11. `multi_producer(queue, name, count)` 는 `(name, i, 현재 PID)` 튜플을 `count` 번 넣고, 사이에 0.02초 쉰다.
12. `multi_consumer(queue, name, total)` 는 `total` 개를 받을 때까지 2초 한도로 기다리며 꺼내고, `  [name] #받은번호: 생산자-인덱스 (from PID:pid)` 를 찍는다.
13. `multi_consumer` 는 2초 안에 아무것도 안 오면 예외를 잡아 멈춘다.
14. 메인에서 공유 큐 하나에 생산자 둘(`P0` · `P1`, 각 3개)과 소비자 하나(`total=6`)를 붙여 띄우고 모두 `join` 한다.

5단계 — 비교 안내
15. Queue 와 Pipe 의 차이를 정리한 안내 줄을 찍는다.

16. 프로세스를 띄우는 코드는 모두 `if __name__ == '__main__':` 아래에 둔다.

**시작 코드**

```python
import multiprocessing
import time
import os

# === multiprocessing.Queue 기본 ===
def producer_proc(queue, count):
    """데이터를 Queue에 넣는 프로세스"""
    for i in range(count):
        item = f"item-{i} (PID:{os.getpid()})"
        # TODO: item 을 큐에 넣는다
        time.sleep(0.05)
    # TODO: 종료 신호를 넣는다

def consumer_proc(queue, name):
    """Queue에서 데이터를 꺼내는 프로세스"""
    while True:
        item = None  # TODO: 큐에서 하나 꺼낸다(올 때까지 기다림)
        # TODO: 종료 신호면 "  [{name}] 종료" 를 찍고 멈춘다
        print(f"  [{name}] 수신: {item}")

# === Pipe 기본 ===
def pipe_sender(conn, data):
    """Pipe로 데이터 전송"""
    for item in data:
        # TODO: item 을 보낸다
        time.sleep(0.05)
    # TODO: 종료 신호를 보내고 자기 끝을 닫는다

def pipe_receiver(conn, name):
    """Pipe에서 데이터 수신"""
    while True:
        item = None  # TODO: 하나 받는다(올 때까지 기다림)
        # TODO: 종료 신호면 멈춘다
        print(f"  [{name}] Pipe 수신: {item}")
    # TODO: 자기 끝을 닫는다

# === 다중 생산자-소비자 ===
def multi_producer(queue, name, count):
    for i in range(count):
        # TODO: (name, i, 현재 PID) 튜플을 넣는다
        time.sleep(0.02)

def multi_consumer(queue, name, total):
    received = 0
    while received < total:
        # TODO: 2초 한도로 꺼내고, 시간이 넘으면 예외를 잡아 멈춘다
        #       꺼냈으면 received 를 늘리고 튜플을 풀어 아래 꼴로 찍는다
        # print(f"  [{name}] #{received}: {producer}-{idx} (from PID:{pid})")
        pass

# TODO: 아래 블록 전체를 프로세스 생성 보호 아래에 둔다
def main():
    print("=== multiprocessing.Queue ===")
    # TODO: 큐를 만들고 생산자(count=5) · 소비자("Consumer") 프로세스를 만든다
    # TODO: 소비자 먼저 start, 생산자 start, 둘 다 join
    print()

    print("=== Queue 크기 제한 ===")
    # TODO: maxsize=3 인 큐를 만든다
    print(f"  maxsize=3: 가득 차면 put()이 블로킹")
    print(f"  put(item, block=False): 가득 차면 queue.Full 예외")
    print(f"  put(item, timeout=1): 1초 내 공간 없으면 예외")
    print(f"  get(block=False): 비어있으면 queue.Empty 예외")
    print()

    print("=== Pipe ===")
    # TODO: Pipe 의 두 끝을 만든다
    # TODO: 송신자(child 끝, ["hello", "world", 42, [1, 2, 3]]) · 수신자(parent 끝, "Receiver") 프로세스
    # TODO: 수신자 먼저 start, 송신자 start, 둘 다 join
    print()

    print("=== 다중 생산자-소비자 ===")
    # TODO: 공유 큐, 생산자 둘(P0 · P1, 각 3개), 소비자 하나(total=6)
    # TODO: 소비자 start → 생산자들 start → 생산자들 join → 소비자 join
    print()

    print("=== Queue vs Pipe ===")
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

main()
```

**확인 방법** — `python multiprocessing-queue.py` 로 돌려, 네 절의 제목 아래에 각각 수신 줄이 찍히고 프로그램이 멈추지 않고 끝나는지 본다.
Queue 절의 마지막 줄이 `[Consumer] 종료` 인지, Pipe 절에 네 값이 모두 찍히는지, 다중 절에 `#1` 부터 `#6` 까지 찍히는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
