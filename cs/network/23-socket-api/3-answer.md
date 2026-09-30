# network/23-socket-api — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 호출 순서

```text
서버:       socket -> bind -> listen -> accept -> recv/send ... -> close
클라이언트: socket -> (bind 생략 가능) -> connect -> send/recv ... -> close
```

- 3-way handshake는 클라이언트 `connect()`와 서버 커널 사이에서 일어난다.
- 서버 앱의 `accept()`는 핸드셰이크가 **끝난** 연결을 accept 큐에서 꺼낼 뿐이다. 핸드셰이크 자체는 서버가 `listen()`한 뒤 커널이 처리한다.
- 클라이언트가 bind하지 않으면 `connect()` 때 커널이 임시 포트를 자동으로 붙인다(ip(7)).

### 2. 리슨 소켓 vs 연결 소켓

- 리슨 소켓은 연결 요청을 받는 **수동 소켓**이다. 데이터를 주고받지 않는다(listen(2)).
- `accept()`는 연결마다 **새 소켓과 새 fd**를 만든다. 원래 리슨 소켓은 그대로 남는다(accept(2)).
- 연결 소켓은 4-튜플(내 IP·포트, 상대 IP·포트)로 구분된다. 상대 IP·포트가 다르면 같은 로컬 8080이어도 서로 다른 연결이다.
- 실제 한도는 fd 한도·메모리 쪽에서 온다.

### 3. `send()`가 전부 돌려줬다

- 말할 수 없다.
- `send()`의 반환값은 커널 **송신 버퍼로 복사한** 바이트 수다.
- 이후 커널이 세그먼트로 보내고, 상대 커널이 받아 ACK하고, 상대 앱이 `recv()`해야 "받았다"가 된다.
- 도중에 연결이 끊기면 버퍼의 데이터는 전달되지 않을 수 있다. 앱 수준 확인이 필요하면 응답·ACK 메시지를 프로토콜에 넣는다.

### 4. `HELLO`·`WORLD`의 수신 모습

- `"HELLOWORLD"` 한 번
- `"HEL"`, `"LOWORLD"` 두 번
- `"HELLO"`, `"WORLD"` 두 번 (우연히 경계가 맞은 경우)
- `"H"`, `"ELLOWOR"`, `"LD"` 세 번
- 순서만 보장된다. `recv()`는 지금 있는 만큼, 요청 크기 이하로 돌려준다(recv(2)). 메시지 경계는 앱이 프레이밍으로 정한다(24번).

### 5. 부분 쓰기

- 경우
  1. 논블로킹 소켓에서 송신 버퍼 여유가 요청보다 작다.
  2. 블로킹 쓰기가 일부 전송 뒤 시그널 핸들러에 끊겼다(write(2)).
  3. `SO_SNDTIMEO` 타임아웃이 일부 전송 뒤 걸렸다. 전송한 양을 돌려준다(socket(7)).
- 처리
  - 반환값만큼 버퍼 포인터를 옮기며 남은 길이가 0이 될 때까지 반복한다.
  - `EINTR`이면 다시 시도한다.
  - 논블로킹의 `EAGAIN`이면 남은 데이터를 보관하고 쓰기 가능 이벤트(`EPOLLOUT`, `OP_WRITE`, `'drain'`)를 기다린다.

### 6. backlog

- 리눅스 2.2부터 backlog는 **핸드셰이크가 끝나 `accept()`를 기다리는 연결 큐**의 길이다. 미완성 연결(SYN 큐)은 `tcp_max_syn_backlog`가 따로 정한다(listen(2) NOTES).
- `net.core.somaxconn`보다 큰 값은 **조용히** 그 값으로 잘린다.
- 기본 `somaxconn`은 리눅스 5.4부터 4096, 그 전에는 128이다. 구 커널에서는 65535를 써도 128이 된다.

### 7. `Address already in use`

- 원인 1: 이전 프로세스가 먼저 닫은 연결이 **TIME-WAIT**로 로컬 주소를 잡고 있다.
  - 확인: `ss -tan | grep ':8080'`에 `TIME-WAIT`가 보인다.
  - 대처: 리슨 소켓에 bind 전 `SO_REUSEADDR`를 켠다(ip(7), socket(7)).
- 원인 2: 이전 프로세스(또는 다른 프로그램)가 **아직 LISTEN 중**이다.
  - 확인: `ss -tlnp 'sport = :8080'`으로 소유 프로세스를 본다.
  - 대처: 그 프로세스를 정리한다. 이 경우 `SO_REUSEADDR`로도 bind할 수 없다(socket(7) — "except when there is an active listening socket").

### 8. `SO_REUSEADDR`의 리눅스 조건, `SO_REUSEPORT`와의 차이

- 리눅스는 **이전에 그 포트를 bind한 프로그램과 새 프로그램 둘 다** `SO_REUSEADDR`를 켰을 때만 재사용을 허락한다. FreeBSD 등은 새 쪽만 켜면 된다(socket(7) NOTES).
- 그래서 옛 버전 서버가 옵션 없이 떠 있었다면, 새 버전만 켜서는 TIME-WAIT 동안 실패할 수 있다.
- `SO_REUSEPORT`(리눅스 3.9+)는 목적이 다르다. 여러 소켓이 **같은 주소에 동시에** bind해서 들어오는 연결을 나눠 받게 한다(socket(7)).

### 9. `Too many open files`

- 먼저 **fd 누수인지 한도 부족인지** 가른다.
  - `ls /proc/<pid>/fd | wc -l` — 지금 연 fd 수
  - `grep -i 'open files' /proc/<pid>/limits` — 한도
  - `ss -tanp | grep <pid>`에서 `CLOSE-WAIT`가 많으면 상대가 닫았는데 내가 안 닫은 누수다(20번).
  - 시간이 지날수록 fd 수가 단조 증가하면 누수다.
- 대처
  - 누수: 모든 경로에서 소켓을 닫는다(try-with-resources, `finally`, `destroy()`).
  - 한도 부족: `ulimit -n`, systemd `LimitNOFILE=`로 올린다.

### 10. Node `'data'`와 `write()`의 `false`

- `'data'` 청크는 TCP로 도착한 바이트 덩어리다. 메시지 하나와 대응하지 않는다. 쪼개지거나 붙어서 온다.
  - 무시하면: 부하가 클 때만 파싱 오류가 나는 간헐 장애가 된다. 누적 버퍼 + 프레이밍으로 처리한다.
- `write()`의 `false`는 "데이터 전부 또는 일부가 커널이 아니라 사용자 메모리에 쌓였다"는 뜻이다. `'drain'` 뒤에 계속 써야 한다(Node `net` 문서).
  - 무시하면: 느린 상대에게 계속 쓰는 동안 프로세스 메모리가 불어나고, 결국 OOM이 날 수 있다.
