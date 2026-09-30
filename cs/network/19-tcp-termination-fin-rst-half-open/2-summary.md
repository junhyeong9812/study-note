# network/19-tcp-termination-fin-rst-half-open — TCP 연결은 어떻게 끝나고, 어떻게 "끝난 줄 모르게" 되나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

TCP 연결은 양쪽이 각자 상태를 들고 있다.\
끝낼 때도 두 쪽이 "이제 끝"에 합의해야 한다.\
합의 없이 한쪽만 사라지면, 다른 쪽은 연결이 살아 있다고 믿고 계속 기다린다.

```text
정상 종료:  A: "나 보낼 거 다 보냈어"(FIN)  --> B: "알았어"(ACK)
            B: "나도 다 보냈어"(FIN)        --> A: "알았어"(ACK)     양쪽 다 안다

강제 종료:  A: "이 연결 버려"(RST)          --> B: 에러로 받는다      B가 RST를 받으면 안다

아무 말 없음: A 서버 전원 꺼짐 (아무것도 안 보냄)
            B: 연결 살아 있음? ... 계속 기다림                     B만 모른다
```

쉬운 예: 전화 통화다.\
"이제 끊을게" "응, 나도" 하고 끊으면 둘 다 안다(FIN).\
상대가 "뚝" 끊으면 신호음으로 바로 안다(RST).\
그런데 상대 휴대폰 배터리가 나가서 말없이 조용해지면, 나는 "여보세요?"라고 말하기 전까지 모른다(half-open).

똑같은 구조다.\
TCP도 "말을 걸어야(보내야)" 상대가 없다는 걸 안다.

실무 예:
- 커넥션 풀의 연결이 방화벽·NAT 뒤에서 조용히 끊겼다.\
  다음 요청에서야 `ECONNRESET`이나 타임아웃이 난다.
- 서버가 재부팅됐는데 클라이언트는 `read()`로 응답을 기다린다.\
  보낼 게 없으니, 타임아웃이 없으면 계속 기다린다.
- 서버가 응답 도중 프로세스를 죽였다.\
  클라이언트는 FIN(정상 송신 종료)이 왔는지, RST(중단)가 왔는지를 구분해야 한다.\
  단, FIN이 왔다고 "응답이 다 왔다"는 뜻은 아니다. 응답의 끝은 길이·프레이밍으로 따로 확인한다.

## 동작·원리

### 4-way 종료 — 패킷 교환도

RFC 9293 Figure 12의 정상 종료를 옮긴 것이다(시퀀스 번호는 RFC 예시값).

```text
  A (능동 종료)                                          B (수동 종료)
  ESTABLISHED                                            ESTABLISHED
  close()
  FIN-WAIT-1  --- <SEQ=100><ACK=300><FIN,ACK> -------->  CLOSE-WAIT   B의 read()가 0을 받는다
  FIN-WAIT-2  <-- <SEQ=300><ACK=101><ACK> ------------   CLOSE-WAIT   (B는 아직 보낼 수 있다)
                                                         close()
  TIME-WAIT   <-- <SEQ=300><ACK=101><FIN,ACK> --------   LAST-ACK
  TIME-WAIT   --- <SEQ=101><ACK=301><ACK> ------------>  CLOSED
  (2MSL 대기)
  CLOSED
```

- FIN은 "**내 쪽 송신이 끝났다**"는 뜻이다. "연결을 끊자"가 아니다.
  - FIN은 시퀀스 번호 하나를 차지한다. 그래서 A의 FIN(SEQ=100)에 대한 ACK가 101이다.
- 두 방향은 따로 닫힌다. 그래서 FIN이 두 번, ACK가 두 번 오간다(4-way).
  - B가 FIN을 받고 곧바로 close하면 ACK와 FIN을 한 세그먼트로 합쳐 보낼 수 있다. 그러면 패킷은 3개로 보인다.
- 2번과 3번 사이에 B는 아직 데이터를 보낼 수 있다.
  - 이 상태를 **half-close**라 한다(RFC 9293 §3.6.1).

  - *half-close*: 한 방향만 닫힌 연결. 정상 기능이다. 이 노트 제목의 half-**open**과 이름이 비슷하지만 전혀 다르다.

### 커널 TCP 상태 ≠ 앱의 fd 상태

A가 FIN-WAIT-2에 있을 때 B의 데이터를 받을 수 있는지는 **A가 어떻게 닫았나**에 달렸다.

```text
  A가 부른 것            A의 TCP 상태        A 앱이 그 fd로 읽기     B가 더 보낸 데이터
  -------------------    ---------------     -------------------     ---------------------------
  shutdown(SHUT_WR)      FIN-WAIT-2          가능                     A 앱이 읽는다 (half-close)
  close()                FIN-WAIT-2          불가 (fd가 없다)          리눅스: A 커널이 RST로 답한다
```

- RFC 9293 §3.6의 "CLOSE 뒤에도 RECEIVE 가능"은 TCP 사용자 인터페이스 이야기다.
- 소켓 API의 `close()`는 fd 자체를 없앤다. 그래서 그 fd로는 더 못 읽는다.
  - RFC 1122 §4.2.2.13은 이런 "half-duplex close"를 허용한다(MAY).
  - 그 경우 CLOSE 뒤에 데이터가 오면 RST로 "데이터가 버려졌다"를 알린다(SHOULD).
  - 리눅스는 이를 따른다. `tcp_rcv_state_process`의 FIN-WAIT-1/2 분기가 RCV_SHUTDOWN 뒤 도착한 데이터에 연결을 리셋한다(`net/ipv4/tcp_input.c`, 주석 "RFC 1122 says we MUST send a reset").
- 응답을 계속 받아야 하면 `close()`가 아니라 `shutdown(fd, SHUT_WR)`을 쓴다(shutdown(2)).

### 상태 기계 — 11개 상태

RFC 9293은 연결의 일생을 11개 상태로 나눈다.\
그중 CLOSED는 "연결 정보가 아예 없음"을 뜻하는 가상의 상태다.

  - *TCB(Transmission Control Block)*: 커널이 연결 하나마다 들고 있는 상태 묶음이다. 시퀀스 번호·윈도·현재 상태가 들어 있다. TCB가 없으면 CLOSED다.

열기 쪽(자세한 내용은 15번 노트, 동시 열기 경로는 생략):

```text
  CLOSED                         CLOSED
    | 능동 open: SYN 보냄           | 수동 open
    v                              v
  SYN-SENT                       LISTEN
    | SYN+ACK 받음: ACK 보냄        | SYN 받음: SYN+ACK 보냄
    |                              v
    |                            SYN-RECEIVED
    |                              | ACK 받음
    v                              v
  ESTABLISHED                    ESTABLISHED
```

닫기 쪽(이 노트의 중심):

```text
                        ESTABLISHED
          내가 close:   /          \   상대 FIN 받음:
          FIN 보냄     v            v   ACK 보냄
               FIN-WAIT-1          CLOSE-WAIT
      내 FIN의    |      \               | 내가 close: FIN 보냄
      ACK 받음    v       \ 상대 FIN     v
               FIN-WAIT-2  \ 먼저 받음   LAST-ACK
      상대 FIN    |         v           | 내 FIN의 ACK 받음
      받음        |       CLOSING       v
                 |         | 내 FIN의  CLOSED
                 v         v ACK 받음
                 TIME-WAIT
                    | 2MSL
                    v
                  CLOSED
```

- 닫기 쪽 그림에서
  - 먼저 close한 쪽(**능동 종료**)은 FIN-WAIT-1 → FIN-WAIT-2 → TIME-WAIT로 간다.
  - 나중에 close한 쪽(**수동 종료**)은 CLOSE-WAIT → LAST-ACK → CLOSED로 간다.
  - 양쪽이 동시에 FIN을 보내면 FIN-WAIT-1에서 상대 FIN을 먼저 받는다. 이때 CLOSING을 거쳐 TIME-WAIT로 간다(RFC 9293 Figure 13).
- RST 화살표는 그림에서 뺐다. RFC 그림도 읽기 쉽게 하려고 생략했다(Figure 5 Note 3). RST 처리 규칙은 아래 「RST를 받은 쪽」에 있다.

  - *MSL(Maximum Segment Lifetime)*: 세그먼트 하나가 네트워크에 떠돌 수 있는 최대 시간이다. RFC 9293은 2분으로 잡는다(§3.4.2).
  - *2MSL*: TIME-WAIT의 대기 시간이다. 능동 종료 쪽은 이만큼 머물러야 한다(MUST-13, §3.6.1). 왜 기다리는지는 20번 노트에서 다룬다.

각 종료 상태가 "무엇을 기다리는지"를 알면 `ss` 출력이 읽힌다(RFC 9293 §3.3.2).

| 상태 | 무엇을 기다리나 | 오래 남아 있으면 의심할 것 |
|---|---|---|
| FIN-WAIT-1 | 내 FIN의 ACK(또는 상대 FIN) | 상대가 ACK를 못 보냄 — 상대 사망·경로 단절 |
| FIN-WAIT-2 | 상대의 FIN | 상대가 아직 보내는 중(정상 half-close)이거나, 상대 앱이 close를 안 함 |
| CLOSE-WAIT | **내 앱의** close | 내 앱이 응답을 마무리하는 중이거나, close 누락(fd 누수) |
| CLOSING | 내 FIN의 ACK(동시 종료) | 드물다 |
| LAST-ACK | 내 FIN의 ACK | 상대가 사라짐 |
| TIME-WAIT | 시간(2MSL) | 정상 상태다. 단 수가 많으면 임시 포트 고갈(20번) |

- 상태 하나만으로 "누구 버그"라고 확정하지 않는다. **지속 시간과 개수 추세**를 같이 본다.
- 리눅스는 TIME-WAIT를 RFC의 4분(2×2분)이 아니라 **60초**로 둔다(`include/net/tcp.h`의 `TCP_TIMEWAIT_LEN (60*HZ)`).

### 애플리케이션이 보는 모습

```text
  상대가 보낸 것      내 read()/recv()                내 write()/send()
  --------------     -----------------------------   ------------------------------------------
  FIN               남은 데이터를 다 읽은 뒤 0 반환   아직 가능 (상대 쪽 송신만 닫혔다)
                    (Java: -1, Node: 'end' 이벤트)
  RST               -1 + errno=ECONNRESET            리눅스: 첫 쓰기 ECONNRESET,
                    (Java: SocketException           그다음부터 EPIPE (+ SIGPIPE, MSG_NOSIGNAL 없으면)
                     "Connection reset")
  아무것도 없음       계속 블록 (타임아웃 없으면)       버퍼에 여유가 있으면 성공.
  (half-open)                                        재전송만 반복하다 결국 ETIMEDOUT
```

- `recv()`가 0을 돌려주는 것은 에러가 아니다. "상대가 정상적으로 송신을 끝냈다(orderly shutdown)"는 뜻이다(recv(2)).
  - 이것은 **TCP 사건**이다. 응용 메시지(HTTP 응답 등)가 다 왔는지는 길이·청크·프로토콜 종료 조건으로 따로 확인한다.
- `EPIPE`는 "내 쪽 송신이 이미 닫힌 소켓에 썼다"는 뜻이다(send(2) "The local end has been shut down").
  - 내가 `shutdown(SHUT_WR)`한 뒤 써도, 연결이 RST로 끝난 뒤 써도 난다.
  - 이때 프로세스는 `SIGPIPE` 신호도 받는다. 신호를 처리하지 않으면 프로세스가 죽는다(send(2), write(2)).
  - *SIGPIPE*: "읽는 쪽이 없는 파이프·소켓에 썼다"를 알리는 유닉스 신호다. 기본 동작은 프로세스 종료다(signal(7)).
  - `send(..., MSG_NOSIGNAL)`을 쓰면 신호 없이 `EPIPE`만 받는다(send(2)).
- RST 뒤 에러 순서는 **구현 의존**이다. 리눅스 기준은 아래와 같다.

```text
  RST 도착 --> tcp_reset(): sk_err = ECONNRESET (CLOSE-WAIT였다면 EPIPE), 송신 방향 닫음
  write 1 --> sk_stream_error(): 저장된 sk_err를 꺼내 반환하고 지운다  --> ECONNRESET, SIGPIPE 없음
  write 2 --> sk_err 비어 있음, 송신 방향 닫힘                          --> EPIPE + SIGPIPE
```

  - 근거: `net/ipv4/tcp_input.c` `tcp_reset()`, `net/core/stream.c` `sk_stream_error()`, `net/ipv4/tcp.c` `tcp_sendmsg_locked()`.
  - 상대 FIN을 이미 받은(CLOSE-WAIT) 연결에 RST가 오면 리눅스는 `EPIPE`를 저장한다. 그래서 첫 쓰기부터 `EPIPE`+SIGPIPE다.
  - 같은 `sk_err`는 `read()`가 먼저 가져갈 수도 있다. 그래서 "몇 번째 호출에서 무엇"은 호출 순서·타이밍에 따라 달라진다.
- RFC 9293은 애플리케이션이 "정상 종료인지, 중단(abort)인지"를 구분해 들을 수 있어야 한다고 정한다(MUST-12, §3.6).

### FIN vs RST — 두 가지 끝내는 방법

```text
               FIN (정상 해제, orderly release)          RST (중단, abortive release)
  의미         "내 송신 끝"                              "이 연결은 없다 / 버린다"
  버퍼 데이터   남은 데이터를 보내고 FIN                   송신 대기 데이터 버림
               (재전송하며 전달 시도, 실패하면 타임아웃)
  상대 반응    read() = 0                               read()/write() = ECONNRESET 등
  응답         ACK로 확인                                RST에는 RST로 답하지 않는다 (§3.5.2)
  TIME-WAIT    능동 종료 쪽이 2MSL 머묾                  구현마다 다름 (아래)
```

- TIME-WAIT와 RST의 관계는 조심해서 읽는다.
  - RFC 9293은 RST를 보낸 쪽도 TIME-WAIT에 들어가는 것을 권한다(소문자 should, §3.5.2).
  - 리눅스에서 `SO_LINGER {on, 0}`으로 닫으면 `__tcp_close`가 `tcp_disconnect`를 불러 RST를 보내고 바로 CLOSED로 간다. TIME-WAIT를 거치지 않는다(`net/ipv4/tcp.c`).

RST가 나가는 대표 경우는 넷이다.

```text
  (1) 없는 포트로 SYN        --> 커널: RST          (클라이언트: ECONNREFUSED)
  (2) 상대가 모르는 연결에 데이터 --> 상대 커널: RST   (half-open 발견, 아래)
  (3) 안 읽은 수신 데이터를 두고 close() --> RST     ("데이터가 버려졌다" 알림)
  (4) SO_LINGER{on, 0} 후 close()     --> RST       (앱이 일부러 중단)
```

- (1)·(2): 연결이 없는(CLOSED) 쪽은 RST 아닌 모든 세그먼트에 RST로 답한다(RFC 9293 §3.5.2 그룹 1).
- (3): close할 때 아직 읽지 않은 수신 데이터가 남아 있으면 RST를 보내라고 권한다(SHOULD, SHLD-3, §3.6.1). 데이터가 유실됐음을 알리기 위해서다.
  - 리눅스 `__tcp_close`는 이 경우 FIN 대신 RST를 보낸다. 소스 주석이 RFC 2525 §2.17을 근거로 든다(`net/ipv4/tcp.c`).
  - Oracle의 Java 문서도 같은 동작을 설명한다.
- (4): Java는 `socket.setSoLinger(true, 0)` 뒤 `close()`다. Node는 `socket.resetAndDestroy()`(v18.3.0, v16.17.0부터)가 RST로 끊는다.
  - *SO_LINGER*: close가 송신 버퍼를 얼마나 기다렸다 닫을지 정하는 소켓 옵션이다(socket(7)). 리눅스에서 linger 시간을 0으로 켜면 기다리지 않고 버퍼를 버린 채 RST를 보낸다(`__tcp_close`의 zero-linger 분기).

### RST를 받은 쪽 — 검사하고, 상태별로 처리한다

RST를 그냥 믿지 않는다.\
아무나 RST를 위조해 남의 연결을 끊지 못하게 하려는 것이다.

```text
  기본 검사 (RFC 9293 §3.5.3)
    RST의 SEQ가 수신 윈도 안?  -- 아니오 --> 버린다
                               -- 예   --> 유효한 RST

  RFC 5961 방어를 구현한 스택 (RFC 9293 §3.10.7.4에 반영)
    SEQ가 윈도 밖            --> 조용히 버린다
    SEQ == RCV.NXT (정확히)   --> 연결 리셋
    SEQ가 윈도 안이지만 ≠     --> challenge ACK 전송 후 RST는 버린다
                                (진짜 상대라면 그 ACK를 보고 정확한 SEQ로 RST를 다시 보낸다)
```

  - *challenge ACK*: "정말 네가 보낸 RST가 맞나?"를 되묻는 ACK다. 윈도 안의 아무 값을 맞힌 위조 RST를 한 번 더 걸러 낸다.
  - SYN-SENT에서는 예외로, RST가 내 SYN을 ACK하고 있어야 받아들인다(§3.5.3).

유효한 RST를 받은 뒤의 상태 처리(§3.5.3):

- LISTEN이면 무시한다.
- SYN-RECEIVED이고 LISTEN에서 왔다면 LISTEN으로 돌아간다. 능동 open에서 왔다면 "연결 거절"을 알리고 CLOSED로 간다.
- 그 밖의 상태면 연결을 중단하고 사용자에게 알린 뒤 CLOSED로 간다.
  - ESTABLISHED·FIN-WAIT·CLOSE-WAIT에서는 모든 세그먼트 큐를 비우라고 한다(should, §3.10.7.4). 실제로 받아 둔 데이터를 버리는지는 구현마다 다르다.

### half-open — 한쪽만 연결이 있다고 믿는 상태

RFC 9293 §3.5.1의 정의:\
한쪽이 상대 모르게 연결을 닫았거나, 장애·재부팅으로 연결 정보를 잃어 양쪽이 어긋난 상태다.

```text
  A (재부팅)                                    B
  연결 정보 없음                                 ESTABLISHED (A가 살아 있다고 믿음)

  경우 1: B가 보낼 게 있다
          <-- <SEQ=300><ACK=100><DATA=10> ---   B가 데이터 전송
  "모르는 연결"
          --- <SEQ=100><RST> -------------->   B: ECONNRESET, 연결 정리     (RFC Figure 10)

  경우 2: B가 보낼 게 없다 (read()만 하고 있다)
          (아무것도 오가지 않는다)                B: read()가 타임아웃 없으면 계속 블록
```

- 경우 1은 스스로 드러난다. 보내는 순간 RST가 돌아오기 때문이다.
- 경우 2가 위험하다. 아무 패킷도 오가지 않으니 B의 커널도 모른다.
- 케이블이 끊기거나 중간 방화벽이 연결 기록을 지운 경우도 비슷하다.
  - 이때는 RST조차 돌아오지 않을 수 있다.
  - B가 보내면 재전송만 반복하다가 한참 뒤 `ETIMEDOUT`으로 끝난다.
  - 리눅스는 재전송 한도 `tcp_retries2`의 기본값이 15다. tcp(7)은 이것이 RTO에 따라 약 13~30분에 해당한다고 적는다.

  - *RTO(Retransmission Timeout)*: ACK가 안 오면 재전송하기까지 기다리는 시간이다. 재전송마다 늘어난다. 16번 노트에서 다룬다.

half-open을 다루는 수단은 두 종류다.

```text
  종류               방법                       누가         무엇을 하나
  말을 걸어 드러내기   TCP keepalive             커널         idle 연결에 probe 전송, 응답 없으면 종료
                     앱 heartbeat              애플리케이션   주기적으로 핑, 응답 없으면 닫기
  기다림에 한도 두기   read 타임아웃              애플리케이션   정한 시간 안에 데이터가 없으면 포기
                     TCP_USER_TIMEOUT          커널         보낸 데이터가 N ms 동안 ACK 안 되면 종료
```

- 타임아웃은 상대가 죽었다는 **증명이 아니다**. "이만큼 기다리면 포기한다"는 한도다. 느린 상대도 같은 모양으로 보인다.
- `TCP_USER_TIMEOUT`은 스스로 탐지 패킷을 보내지 않는다. 보낸 데이터가 ACK 안 되거나 제로 윈도로 못 보낼 때만 작동한다(tcp(7)). 유휴 연결 탐지는 keepalive와 함께 써야 한다.
- RFC 9293은 keepalive를 선택 기능으로 둔다. 구현한다면 **기본은 꺼짐**이어야 하고, 간격 기본값은 2시간 이상이어야 한다(MUST-25, MUST-28, §3.8.4).
- 리눅스 기본값은 idle 7200초 뒤 probe를 보낸다. 이후 75초 간격 9번 probe로 약 11분이 더 걸린다(tcp(7) `tcp_keepalive_time`·`_intvl`·`_probes`).
- 세부 튜닝은 21번 노트에서 다룬다.

## 쓰이는 자료구조·알고리즘

- **유한 상태 기계(FSM)** — TCP 연결은 11상태 FSM이다.
  - 입력은 사용자 호출(OPEN·SEND·RECEIVE·CLOSE·ABORT), 도착 세그먼트(SYN·ACK·RST·FIN), 타임아웃이다(RFC 9293 §3.3.2).
  - 출력은 보낼 세그먼트와 앱에 줄 신호다.
  - 설계 관점: "상태 × 이벤트" 표로 모든 조합을 채워야 빠진 경우가 드러난다. RFC 9293 §3.10 "Event Processing"이 바로 이 표다.
- **해시 테이블(연결 조회)** — 도착한 세그먼트가 어느 TCB 것인지 찾아야 한다.
  - 키는 (출발 IP, 출발 포트, 도착 IP, 도착 포트) 4-튜플이다.
  - 찾지 못하면 "연결 없음"이고, RST 생성 규칙 그룹 1이 적용된다.
  - 리눅스는 이 조회에 established 해시 테이블(`ehash`)을 쓴다(`include/net/inet_hashtables.h`의 `__inet_lookup_established`). 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md) 참고.
- **윈도 범위 검사** — RST 유효성은 "SEQ가 수신 윈도 안에 있나"라는 구간 비교다(§3.5.3). 모듈러 산술로 비교한다(시퀀스 번호가 2^32에서 돌기 때문, §3.4).
- **타이머** — 연결마다 타이머가 여러 개 붙는다.
  - TIME-WAIT 2MSL, FIN-WAIT-2 타임아웃(`tcp_fin_timeout`), keepalive, 재전송.
  - `ss -o`가 이 타이머를 `timer:(이름,남은 시간,재전송 횟수)`로 보여 준다. 이름은 `on`(재전송 계열)·`keepalive`·`timewait`·`persist`(제로 윈도 probe)다(ss(8)).

## 적용 — 풀어나가는 법

### 1. 코드에서 "정상 종료"와 "중단"을 구분한다

Java — `read()`의 -1과 예외를 따로 처리한다.

```java
try (Socket s = new Socket(host, port)) {
    s.setSoTimeout(30_000);                  // read가 30초(예시) 넘게 막히면 SocketTimeoutException
    InputStream in = s.getInputStream();
    byte[] buf = new byte[8192];
    int n;
    while ((n = in.read(buf)) != -1) {       // -1 = 상대가 FIN (상대 송신 종료)
        handle(buf, n);
    }
    // 여기 왔다 = 상대가 송신을 끝냈다. 메시지가 완전한지는 길이·프레이밍으로 확인한다
} catch (SocketTimeoutException e) {
    // 시간 안에 아무것도 안 왔다 = half-open일 수도, 그냥 느릴 수도 있다. 연결을 버린다
} catch (SocketException e) {
    // "Connection reset" = RST를 받았다. 응답이 잘렸을 수 있다
}
```

Node.js — `'end'`와 `'error'`를 따로 듣는다.

```js
const net = require('node:net');
const sock = net.connect({ host, port });
sock.setTimeout(30_000);                       // 30초(예시) idle이면 'timeout' 이벤트만 온다
sock.on('timeout', () => sock.destroy());      // setTimeout은 연결을 끊지 않는다. 직접 끊는다
sock.on('end', () => { /* 상대 FIN: 읽기 끝 */ });
sock.on('error', (err) => {
  if (err.code === 'ECONNRESET') { /* 상대 RST */ }
  if (err.code === 'EPIPE')      { /* 송신이 닫힌 연결에 썼다 */ }
});
```

- Node는 `allowHalfOpen`의 기본값이 `false`다. 읽기 쪽이 끝나면(상대 FIN) 쓰기 쪽도 자동으로 끝낸다(Node `net` 문서).
- `socket.setTimeout()`은 이벤트만 줄 뿐 연결을 끊지 않는다. 끊기는 직접 해야 한다.

C — 요청을 다 보냈음을 알리고 응답은 계속 받는 half-close.

```c
/* send()는 일부만 보낼 수 있다. 다 보낼 때까지 반복한다 (send(2) RETURN VALUE) */
size_t off = 0;
while (off < len) {
    ssize_t w = send(fd, req + off, len - off, MSG_NOSIGNAL);   /* SIGPIPE로 죽지 않게 */
    if (w < 0) { if (errno == EINTR) continue; goto fail; }      /* EPIPE·ECONNRESET 등 */
    off += (size_t)w;
}
shutdown(fd, SHUT_WR);              /* FIN 전송: "요청 끝". 읽기는 계속 가능 */
while ((n = recv(fd, buf, sizeof buf, 0)) > 0) { /* 응답 처리 */ }
if (n == 0)  { /* 서버 FIN: 서버 송신 종료. 응답이 완전한지는 길이·프레이밍으로 확인 */ }
if (n < 0 && errno == ECONNRESET) { /* 서버 RST: 응답이 잘렸을 수 있다 */ }
close(fd);
```

### 2. 내 서버가 "먼저 닫는지, 나중에 닫는지" 정한다

- 먼저 닫는 쪽이 TIME-WAIT를 진다. 연결을 많이 여닫는 쪽이 어디인지 보고 정한다(20번).
- 상대 FIN을 받았으면 남은 응답을 다 보낸 뒤 `close()`한다. 이것을 빠뜨리면 CLOSE-WAIT가 쌓인다(20번).
- 요청 본문을 다 읽지 않고 닫으면 RST가 나갈 수 있다. 본문을 끝까지 읽거나 버린(drain) 뒤 닫는다.
- 일부러 RST로 끊는 것(`SO_LINGER 0`)은 마지막 수단이다. 보낼 데이터가 버려지고, 상대는 에러로 받는다.

### 3. 진단 명령

```bash
# 상태별 연결 수 — CLOSE-WAIT·FIN-WAIT-2·TIME-WAIT가 튀는지
ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c

# 특정 상태만: 타이머 정보(-o)까지
ss -tano state close-wait
ss -tano state fin-wait-2
#   timer:(on,1.2s,3)       재전송 타이머, 1.2초 뒤 만료, 재전송 3회 -> 상대가 ACK를 안 한다 (예시 값)
#   timer:(keepalive,...)   유휴 연결, keepalive 대기 중

# FIN/RST 패킷만 잡기 — 누가 먼저 끊었나
tcpdump -ni any 'tcp[tcpflags] & (tcp-fin|tcp-rst) != 0 and port 8080'

# 커널 기본값 확인
sysctl net.ipv4.tcp_fin_timeout net.ipv4.tcp_retries2 net.ipv4.tcp_keepalive_time net.ipv4.tcp_orphan_retries
```

- `tcpdump` 출력에서 플래그는 `[F.]`(FIN+ACK), `[R]`(RST), `[R.]`(RST+ACK)로 보인다.
- "누가 먼저 FIN을 보냈나"가 곧 "누가 능동 종료했나"다.
- `tcp_orphan_retries`(기본 8)는 내가 이미 닫은 연결의 상대를 몇 번까지 더 찔러 볼지 정한다(tcp(7)).
  - 단, 위 sysctl을 찍으면 보통 **0**이 나온다. 커널은 0을 "상대가 최근까지 응답했으면 8회"로 해석한다(net/ipv4/tcp_timer.c `tcp_orphan_retries`). 문서의 "기본 8"은 이 실효값이다. 작성 환경(Linux 7.0)도 0이었다.

## 장애 시나리오와 대처

### 1. 응답을 읽다가 `ECONNRESET` / `Connection reset by peer`

- **현상**: 간헐적으로 요청이 실패한다. 특히 한동안 쉬었던 풀 연결의 첫 요청에서 많다.
- **보이는 형태**
  - Java `java.net.SocketException: Connection reset` (예: 흔히 보이는 메시지. 런타임·버전에 따라 다를 수 있다)
  - Node `Error: read ECONNRESET` (예시)
  - tcpdump에 상대 쪽 `[R]`/`[R.]` 패킷
- **원인**
  - 상대 서버(또는 LB·NAT·방화벽)가 idle 연결을 먼저 정리했다. 이쪽은 그걸 모르고 옛 연결에 요청을 썼다(half-open 경우 1).
  - 또는 상대 앱이 수신 데이터를 다 읽지 않고 close했다(RST 경우 3).
- **대처**
  - tcpdump로 RST의 **방향과 직전 패킷**을 본다.
  - 클라이언트 풀의 idle timeout을 서버·LB의 idle timeout보다 **짧게** 둔다(35번).
  - 멱등한 요청만 자동 재시도한다.
  - 서버는 요청 본문을 끝까지 읽은 뒤 닫는다.

### 2. 닫힌 연결에 쓰다가 `EPIPE` — 프로세스가 조용히 죽는다

- **현상**: C·C++ 같은 네이티브 서버가 로그 없이 종료된다.
- **보이는 형태**
  - 셸에서 종료 코드 141이다. bash는 신호 N으로 죽은 명령에 128+N을 쓰고(bash 매뉴얼 "Exit Status"), x86·ARM 리눅스의 SIGPIPE는 13이다(signal(7)).
  - 애플리케이션 로그에는 아무것도 없다.
- **원인**
  - 송신이 닫힌 소켓에 `write()`했다. 예: RST를 받은 연결에 두 번째로 쓰기, RST를 받은 CLOSE-WAIT 연결에 쓰기, 내가 `shutdown(SHUT_WR)`한 뒤 쓰기.
  - 커널이 `EPIPE`와 함께 `SIGPIPE`를 보냈고, 기본 동작이 종료다.
- **대처**
  - `send(..., MSG_NOSIGNAL)`을 쓰거나 `SIGPIPE`를 무시(`SIG_IGN`)하도록 설정한다.
  - 그러면 `EPIPE` 에러로 받아서 처리할 수 있다.
  - 런타임은 대부분 이미 막아 둔다.
    - HotSpot JVM은 SIGPIPE를 무시하도록 설정한다(`signals_posix.cpp`). 그래서 `IOException`("Broken pipe" 등)으로만 온다.
    - Node는 SIGPIPE를 기본으로 무시한다(Node `process` 문서 "Signal events").
    - Go는 fd 1·2가 아닌 곳(소켓 등)에서는 SIGPIPE로 죽지 않고 `EPIPE` 에러를 돌려준다. fd 1·2(표준 출력·에러)에서는 SIGPIPE로 종료한다(Go `os/signal` 문서).

### 3. half-open — 상대 재부팅·케이블 단절 뒤 `read()`가 안 끝난다

- **현상**: 스레드가 멈춘 채 풀리지 않는다. 컨슈머가 메시지를 안 받는데 연결은 ESTABLISHED로 보인다.
- **보이는 형태**
  - 스레드 덤프에 `SocketInputStream.read`(또는 `NioSocketImpl.read`)에서 멈춘 스레드가 보인다.
  - `ss -tan`에는 ESTABLISHED로 보인다.
  - `ss -tano`의 Send-Q가 0이고 재전송 타이머(`on`)가 없다. 보낼 게 없으니 재전송도 없다.
  - 로컬 `ss`만으로는 "상대 사망"과 "상대가 그냥 조용함"을 구분할 수 없다. 상대 호스트에서 같은 4-튜플이 있는지 확인한다.
- **원인**: 상대 쪽 TCB가 사라졌다(재부팅·NAT 상태 삭제). 그런데 이쪽은 보낼 게 없어 RST를 받을 기회가 없다.\
  Cloudflare 글의 표현대로, keepalive도 전송도 없는 ESTABLISHED 연결은 통신이 끊겨도 그 상태로 남는다.
- **대처**
  - 블로킹 read에 타임아웃을 건다. Java는 `setSoTimeout`, Node는 `setTimeout` 후 `destroy`다.
  - 오래 쉬는 연결에는 앱 heartbeat나 TCP keepalive(`SO_KEEPALIVE`)를 켜고, 간격을 짧게 조정한다.
  - 리눅스 keepalive 기본값은 2시간이라 대개 너무 길다(21번).

### 4. 보내는 중인데 상대가 사라짐 — 수십 분 뒤에야 `ETIMEDOUT`

- **현상**: 요청이 한참 멈췄다가 실패한다. 앱 로그에는 "보냈다"가 남아 있을 수 있다.
- **보이는 형태**
  - `ss -tano`에 Send-Q가 쌓여 있고 `timer:(on,…,N)`의 N이 오른다.
  - 결국 `ETIMEDOUT`이 난다(Java `SocketException: Connection timed out` [?]).
- **원인**
  - `write()` 성공은 "커널 송신 버퍼에 들어갔다"이지 "상대가 받았다"가 아니다.
  - 상대 호스트가 응답하지 않는다. RST도 오지 않는다.
  - 커널은 `tcp_retries2`(기본 15, 약 13~30분, tcp(7))의 한도에 이를 때까지 재전송한 뒤에야 포기한다.
  - 참고로 Cloudflare의 한 실험에서는 약 940초였다. 기본값이 아니라 그 환경의 측정값이다.
- **대처**
  - `TCP_USER_TIMEOUT`(리눅스 2.6.37+)으로 "ACK 없이 버틸 최대 시간"을 줄인다.
  - keepalive와 함께 쓰면 keepalive 실패로 닫는 시점도 user timeout이 정한다(tcp(7) "will override keepalive"). 그래서 대략 `KEEPIDLE + KEEPINTVL × KEEPCNT`로 맞추라는 권고가 있다(Cloudflare).
  - 앱 수준의 전체 요청 타임아웃을 따로 둔다. 완료는 상대의 **앱 수준 응답**으로 판단한다.

### 5. FIN-WAIT-2가 쌓인다

- **현상**: 내가 먼저 close했는데 상대가 오래도록 FIN을 안 보낸다.
- **보이는 형태**: `ss -tan state fin-wait-2`의 개수가 늘어나고, 오래된 것이 줄지 않는다.
- **원인**
  - 상대가 half-close 상태에서 아직 보내는 중이면 정상이다.
  - 오래 남는다면 상대 앱이 FIN을 받고도 `close()`를 안 했을 가능성이 크다. 그러면 상대 쪽은 CLOSE-WAIT에 머문다.
- **대처**
  - 상대 호스트의 같은 4-튜플이 CLOSE-WAIT인지, 얼마나 오래됐는지 확인한다.
  - 리눅스는 앱이 이미 놓아 버린(orphan) FIN-WAIT-2 소켓을 `tcp_fin_timeout`(기본 60초) 뒤 강제로 닫는다.
    - *고아(orphan) 소켓*: 앱은 `close()`했지만 커널이 종료 절차를 마무리하느라 아직 들고 있는 소켓이다.
    - `shutdown(SHUT_WR)`만 한 소켓은 고아가 아니므로 이 타이머가 적용되지 않는다.
  - tcp(7)은 이 강제 종료가 "엄밀히는 TCP 명세 위반이지만 DoS 방지에 필요하다"고 적는다.
  - 근본 대처는 상대 쪽 CLOSE-WAIT 누수를 고치는 것이다(20번).

## 핵심 문장

- FIN은 "연결을 끊자"가 아니라 "**내 송신이 끝났다**"이다. 두 방향이 따로 닫히므로 4-way가 되고, 그 사이의 half-close는 정상 기능이다.
- FIN은 TCP 사건이다. `read()`의 0(EOF)은 "상대 송신 끝"이지 "응답 완결"이 아니다. 메시지의 끝은 길이·프레이밍으로 확인한다.
- RST는 "이 연결은 없다"는 통보다. 버퍼를 버리고 확인을 기다리지 않는다. 수신 윈도 검사(RFC 5961 스택은 정확한 SEQ 또는 challenge ACK)를 통과해야 인정된다.
- 리눅스에서 RST를 받은 뒤 첫 쓰기는 `ECONNRESET`, 다음 쓰기부터 `EPIPE`+`SIGPIPE`다. 순서는 구현 의존이다.
- half-open은 한쪽만 연결이 있다고 믿는 상태다. 보내는 순간 RST로 드러나지만, **보낼 게 없으면 계속 살아 보인다**.
- "상대가 끊으면 알려주겠지"에 기대지 않는다. 유휴 연결에는 read 타임아웃·keepalive·heartbeat 중 하나를 둔다.

## 관련 주제·근거

- 선행: [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md)
- 후속·연결
  - [20-time-wait-and-close-wait](../20-time-wait-and-close-wait/2-summary.md) — TIME-WAIT의 존재 이유, CLOSE-WAIT 누수.
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — half-open 탐지 튜닝.
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 풀 idle timeout 정렬.
  - [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md) — 프로세스 종료 시 연결을 FIN으로 정리하는 순서
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — 4-튜플로 연결 찾기
- RFC 9293 (TCP, 2022) <https://www.rfc-editor.org/rfc/rfc9293>
  - §3.3.2 상태 기계 개요·Figure 5 상태 다이어그램
  - §3.4.2 MSL = 2분
  - §3.5.1 half-open 정의·Figure 9·10
  - §3.5.2 RST 생성 규칙(3그룹) · §3.5.3 RST 처리(윈도 검사, 상태별 처리)
  - §3.6 연결 종료 3가지 경우·Figure 12(정상)·Figure 13(동시)·MUST-12
  - §3.6.1 half-close·SHLD-3(안 읽은 데이터 close 시 RST)·TIME-WAIT 2MSL(MUST-13)
  - §3.8.3 재전송 한도 R1·R2(R2 ≥ 100초) · §3.8.4 keepalive(기본 꺼짐, 2시간 이상)
  - §3.10.5 ABORT 호출 → RST · §3.10.7.4 RST 검사(RFC 5961 challenge ACK)·큐 비우기
- RFC 1122 §4.2.2.13 — half-duplex close(MAY), CLOSE 뒤 데이터 도착 시 RST(SHOULD) <https://www.rfc-editor.org/rfc/rfc1122>
- RFC 5961 — 윈도 내 blind reset 공격과 challenge ACK <https://www.rfc-editor.org/rfc/rfc5961>
- Linux 소스 <https://github.com/torvalds/linux>
  - `include/net/tcp.h` — `TCP_TIMEWAIT_LEN (60*HZ)`
  - `net/ipv4/tcp.c` — `__tcp_close`(미수신 데이터 → RST, RFC 2525 §2.17 주석, zero-linger 분기) · `tcp_sendmsg_locked`
  - `net/ipv4/tcp_input.c` — `tcp_reset`(ECONNRESET, CLOSE-WAIT면 EPIPE) · FIN-WAIT-1/2에서 close 뒤 데이터 → 리셋
  - `net/core/stream.c` — `sk_stream_error`(저장된 오류 우선, EPIPE일 때만 SIGPIPE)
  - `include/net/inet_hashtables.h` — `ehash`, `__inet_lookup_established`
- Linux man-pages
  - recv(2) — orderly shutdown이면 0 반환 <https://man7.org/linux/man-pages/man2/recv.2.html>
  - send(2)·write(2) — 부분 전송, `EPIPE`, `SIGPIPE`, `MSG_NOSIGNAL` <https://man7.org/linux/man-pages/man2/send.2.html>
  - shutdown(2) — `SHUT_WR` <https://man7.org/linux/man-pages/man2/shutdown.2.html>
  - socket(7) — `SO_LINGER` <https://man7.org/linux/man-pages/man7/socket.7.html>
  - tcp(7) — `tcp_fin_timeout`(60), `tcp_retries2`(15), `tcp_orphan_retries`(8 — sysctl 값 0의 실효값, tcp_timer.c), keepalive 7200/75/9, `TCP_USER_TIMEOUT` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - ss(8) — `-o` 타이머 형식 <https://man7.org/linux/man-pages/man8/ss.8.html>
  - signal(7) — SIGPIPE 번호·기본 동작 <https://man7.org/linux/man-pages/man7/signal.7.html>
- GNU Bash 매뉴얼 "Exit Status"(128+N) <https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html>
- Oracle, "Orderly Versus Abortive Connection Release in Java" <https://docs.oracle.com/javase/8/docs/technotes/guides/net/articles/connection_release.html>
- OpenJDK HotSpot `src/hotspot/os/posix/signals_posix.cpp` — SIGPIPE 무시 <https://github.com/openjdk/jdk/blob/master/src/hotspot/os/posix/signals_posix.cpp>
- Node.js `net` 문서 — `'end'`, `allowHalfOpen`, `resetAndDestroy()`(v18.3.0·v16.17.0), `setTimeout()` <https://nodejs.org/api/net.html> · `process` 문서 "Signal events"(SIGPIPE 기본 무시) <https://nodejs.org/api/process.html#signal-events>
- Go `os/signal` 문서 — SIGPIPE 처리(fd 1·2 vs 그 외) <https://pkg.go.dev/os/signal>
- Cloudflare, "When TCP sockets refuse to die" <https://blog.cloudflare.com/when-tcp-sockets-refuse-to-die/>
- Stevens, 『TCP/IP Illustrated Vol.1』 2판 13장 "TCP Connection Management"
