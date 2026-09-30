# network/19-tcp-termination-fin-rst-half-open — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 왜 4-way인가

FIN은 "연결을 끊자"가 아니라 "**내 쪽 송신이 끝났다**"는 뜻이다.\
TCP는 양방향이고, 두 방향은 따로 닫힌다(RFC 9293 §3.6 "simplex fashion", §3.6.1).\
그래서 A→B 방향을 닫는 FIN+ACK, B→A 방향을 닫는 FIN+ACK가 각각 필요해 4개가 된다.

- 수동 종료 쪽은 FIN을 받자마자 자기 FIN을 보낼 수 없다. 자기 애플리케이션이 `close()`할 때까지 기다려야 하기 때문이다.
- 단, B가 FIN을 받고 곧바로 close하면 ACK와 FIN이 한 세그먼트로 합쳐질 수 있다. 그러면 패킷은 3개로 보인다.

### 2. 종료 상태 순서

```text
능동 종료: ESTABLISHED -> FIN-WAIT-1 -> FIN-WAIT-2 -> TIME-WAIT --(2MSL)--> CLOSED
수동 종료: ESTABLISHED -> CLOSE-WAIT -> LAST-ACK -> CLOSED
동시 종료: ESTABLISHED -> FIN-WAIT-1 -> CLOSING -> TIME-WAIT -> CLOSED   (양쪽 모두)
```

- 동시 종료에서는 FIN-WAIT-1에서 내 FIN의 ACK보다 상대 FIN을 먼저 받는다. 그래서 CLOSING을 거친다(RFC 9293 Figure 13).
- 동시 종료면 양쪽 모두 TIME-WAIT를 거친다.
- 위는 대표 경로다. 예를 들어 FIN-WAIT-1에서 내 FIN의 ACK와 상대 FIN을 한 세그먼트로 받으면 FIN-WAIT-2를 건너뛰고 TIME-WAIT로 간다(RFC 9293 §3.10.7.4 FIN 처리).

### 3. FIN 뒤의 read와 write, 그리고 close 뒤의 read

- `read()`/`recv()`는 버퍼에 남은 데이터를 다 돌려준 뒤 **0**을 반환한다(EOF, recv(2) "orderly shutdown"). Java `InputStream.read()`는 -1, Node는 `'end'` 이벤트다.
  - 0은 "상대 송신 끝"이다. 응용 메시지가 완전한지는 길이·프레이밍으로 따로 본다.
- `write()`는 **성공할 수 있다**.
  - FIN은 상대의 송신 방향만 닫았다. 내 → 상대 방향은 열려 있다(half-close).
  - 상대가 그 데이터를 받을지는 상대 앱에 달렸다.
  - 상대가 소켓을 완전히 `close()`했다면, 내 데이터에 상대 커널이 RST로 답할 수 있다(RFC 1122 §4.2.2.13 SHOULD, 리눅스는 그렇게 한다).
  - 리눅스에서는 FIN을 받은(CLOSE-WAIT) 연결에 RST가 오면 `EPIPE`를 저장한다(`tcp_reset`). 그래서 그다음 쓰기가 `EPIPE`+SIGPIPE다. 순서·에러 코드는 구현 의존이다.
- 반대로 내가 먼저 `close()`했다면, **내 앱은 그 fd로 더 못 읽는다**.
  - 커널 TCP는 FIN-WAIT-2에 있지만 fd는 이미 없다.
  - 이때 상대 데이터가 오면 리눅스 커널은 RST로 답한다(`tcp_input.c`, RFC 1122 §4.2.2.13).
  - 응답을 계속 받으려면 `shutdown(fd, SHUT_WR)`으로 송신만 닫는다.

### 4. FIN vs RST

| | FIN(정상 해제) | RST(중단) |
|---|---|---|
| 송신 버퍼 | 남은 데이터를 보낸 뒤 FIN을 보낸다. 재전송하며 전달을 시도하지만, 끝내 ACK가 없으면 타임아웃으로 끝날 수 있다(§3.6) | 대기 중인 데이터를 버린다(§3.10.5 ABORT) |
| 상대 앱 | `read()`가 0(EOF) | 보통 `ECONNRESET`(Java `SocketException: Connection reset` 등). 이후 호출의 에러는 구현 의존 |
| 확인 | ACK로 확인한다 | 확인하지 않는다. RST에 RST로 답하지도 않는다(§3.5.2) |

RFC 9293은 애플리케이션이 이 둘을 구분해 들을 수 있어야 한다고 정한다(MUST-12).

### 5. 요청 본문을 다 읽지 않고 close하면

서버 커널이 FIN 대신 **RST**를 보낼 수 있다.\
아직 읽지 않은 수신 데이터가 있는 채로 close하면 데이터가 유실되기 때문이다.

- RFC 9293 §3.6.1 SHLD-3은 이를 RST로 알리라고 권한다(SHOULD — MUST가 아니다).
- 리눅스는 그렇게 구현했다(`net/ipv4/tcp.c` `__tcp_close`, RFC 2525 §2.17 주석). Oracle의 Java 문서도 같은 동작을 설명한다.

클라이언트는 응답을 받기도 전에(또는 받는 도중에) `ECONNRESET`을 볼 수 있다.\
서버가 이미 보낸 응답이 있어도 잃을 수 있다. RFC 9293 §3.10.7.4는 RST를 받으면 세그먼트 큐를 비우라고 하기 때문이다(should). 실제로 버리는지는 구현마다 다르다.\
대처는 서버가 본문을 끝까지 읽거나 버린 뒤(drain) 닫는 것이다.

### 6. half-open vs half-close

- **half-open**: 한쪽이 상대 모르게 연결을 닫았거나, 장애·재부팅으로 연결 정보를 잃은 상태다. 양쪽이 어긋나 있고 한쪽만 연결이 있다고 믿는다(RFC 9293 §3.5.1). **이상 상태**다.
- **half-close**: 한 방향만 FIN으로 닫고 다른 방향은 계속 쓰는 상태다. 양쪽이 모두 합의했다. **정상 기능**이다(§3.6.1, `shutdown(SHUT_WR)`).

### 7. 상대 재부팅 뒤

- (a) 보내는 경우
  - 재부팅한 쪽에는 그 연결의 TCB가 없다. 그래서 "모르는 연결"로 보고 RST로 답한다(§3.5.2 그룹 1, Figure 10).
  - 내 쪽은 `ECONNRESET`을 받고 연결을 정리한다. 곧바로 드러난다.
- (b) read로만 기다리는 경우
  - 아무 패킷도 오가지 않는다. 그래서 내 커널도 모르고, 타임아웃이 없는 `read()`는 계속 블록된다.
  - read 타임아웃·keepalive·heartbeat 중 하나가 있어야 풀린다.
- 케이블 단절처럼 RST조차 못 오는 경우도 있다. 이때 (a)는 `tcp_retries2`(기본 15, tcp(7) 기준 약 13~30분) 재전송 끝에 `ETIMEDOUT`이 된다.

### 8. SIGPIPE로 조용히 죽음

- 송신이 이미 닫힌 소켓에 `write()`했다.
  - 흔한 예: 상대가 RST로 끊은 연결에 계속 쓰기. 내가 `shutdown(SHUT_WR)`한 뒤 쓰기도 같은 결과다.
- 커널은 `EPIPE`를 돌려주면서 프로세스에 `SIGPIPE`를 보낸다. 기본 동작이 종료라서 로그를 남길 틈도 없이 죽었다(send(2), signal(7)).
- 리눅스에서 RST 직후의 첫 `write()`는 보통 **SIGPIPE를 일으키지 않는다**.
  - `tcp_reset`이 `sk_err = ECONNRESET`을 저장하고, 첫 쓰기가 그 값을 꺼내 `ECONNRESET`을 돌려준다(`sk_stream_error`).
  - 두 번째 쓰기부터 `EPIPE`+SIGPIPE다.
  - 예외: 상대 FIN을 이미 받은(CLOSE-WAIT) 상태였다면 저장값이 `EPIPE`라 첫 쓰기부터 SIGPIPE다.
- 막는 법
  - `send(fd, buf, len, MSG_NOSIGNAL)`을 쓴다. 호출 단위로 적용된다.
  - 또는 `signal(SIGPIPE, SIG_IGN)`으로 신호를 무시한다. 프로세스 전체에 적용된다.
  - 그 뒤 `EPIPE`를 에러로 처리하고 연결을 정리한다.
- 참고: JVM·Node는 SIGPIPE를 기본으로 무시한다. Go는 소켓 fd에서는 `EPIPE` 에러로 돌려준다(fd 1·2만 SIGPIPE 종료, Go `os/signal` 문서).

### 9. half-open 대응 수단

| 종류 | 수단 | 누가 | 방식 |
|---|---|---|---|
| 말을 걸어 드러내기 | TCP keepalive (`SO_KEEPALIVE`) | 커널 | idle 연결에 probe를 보내고, 응답이 없으면 종료 |
| 말을 걸어 드러내기 | 앱 heartbeat | 애플리케이션 | 주기적으로 핑, 응답이 없으면 닫기 |
| 기다림에 한도 두기 | read 타임아웃 | 애플리케이션 | 정한 시간 안에 데이터가 없으면 포기 |
| 기다림에 한도 두기 | `TCP_USER_TIMEOUT` | 커널 | 보낸 데이터가 N ms 동안 ACK 안 되면 종료, `ETIMEDOUT` |

- 한도 두기는 상대 사망을 **증명하지 않는다**. 느린 상대도 같은 결과가 된다.
- `TCP_USER_TIMEOUT`은 스스로 probe를 보내지 않는다. 유휴 연결에는 keepalive와 함께 쓴다.

리눅스 keepalive 기본값은 idle 7200초(2시간) 뒤 첫 probe를 보낸다. 이후 75초 간격 9번이라 약 11분이 더 걸린다(tcp(7)).\
그래서 죽은 연결을 2시간 넘게 들고 있게 된다.\
게다가 그보다 짧은 NAT·LB idle timeout이 먼저 연결 상태를 지우는 것을 **막지 못한다**. keepalive는 그 뒤의 단절을 늦게 알아낼 뿐이다.\
그래서 `TCP_KEEPIDLE` 등을 연결마다 중간 장비의 idle timeout보다 짧게 조정하거나, 앱 heartbeat를 둔다(21번).

### 10. RST 시퀀스 검사 이유

RST는 확인 없이 연결을 즉시 없앤다.\
그러니 아무 RST나 믿으면, 4-튜플만 아는 제3자가 위조 RST로 남의 연결을 끊을 수 있다.\
RFC 9293 §3.5.3은 그래서 RST의 SEQ가 **수신 윈도 안에** 있어야 유효하다고 정한다.\
SYN-SENT 상태에서는 예외로, 내가 보낸 SYN을 ACK하고 있어야 받아들인다.

윈도가 크면 윈도 안의 값을 맞히기가 그리 어렵지 않다. 그래서 RFC 5961 방어가 한 겹 더 있다(RFC 9293 §3.10.7.4에 반영).

- SEQ가 윈도 밖이면 조용히 버린다.
- SEQ가 `RCV.NXT`와 **정확히** 같으면 연결을 리셋한다.
- 윈도 안이지만 다르면 **challenge ACK**를 보내고 그 RST는 버린다(MUST).
  - 진짜 상대라면 그 ACK를 보고 정확한 SEQ로 RST를 다시 보낸다.
  - 위조자는 ACK를 볼 수 없으니 정확한 값을 한 번에 맞혀야 한다.
