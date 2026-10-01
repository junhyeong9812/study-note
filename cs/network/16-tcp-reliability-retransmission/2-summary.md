# network/16-tcp-reliability-retransmission — TCP는 어떻게 "잃어버린 바이트"를 다시 보내나 — 정리 (힌트)

## 해결하는 문제

IP는 패킷을 "최선을 다해" 보낼 뿐이다.\
패킷은 사라지고, 순서가 바뀌고, 두 번 도착하기도 한다.\
TCP는 그 위에서 애플리케이션에게 "보낸 바이트가 빠짐없이, 순서대로, 한 번씩" 도착한 것처럼 보여 줘야 한다.

```text
  보낸 것 (IP 위)          도착한 것 (IP가 준 것)       앱이 받는 것 (TCP가 준 것)
  [1][2][3][4][5]   -->    [1][3][2][5][5]        -->   [1][2][3][4][5]
                           (4 유실, 2·3 뒤바뀜,          (빠짐·순서·중복 모두 해결)
                            5 중복)
```

쉬운 예: 번호 붙인 택배 상자를 여러 대의 트럭으로 보낸다.\
받는 사람은 "3번까지 다 받았어"라고 알려 준다.\
보내는 사람은 한참 소식이 없거나 "3번까지"라는 말만 반복해서 들리면 4번을 다시 보낸다.

똑같은 구조다.\
TCP는 바이트마다 번호(시퀀스 번호)를 붙이고, 받는 쪽은 "여기까지 받았다"(ACK)를 돌려주고, 보내는 쪽은 타이머와 중복 ACK로 유실을 판단해 재전송한다.

실무 예:
- 에러는 하나도 없는데 p99 지연만 튄다. 패킷 하나가 유실돼 재전송을 기다린 요청이다.
- 모바일·와이파이 구간에서 가끔 요청이 1초 이상 멈췄다가 정상 응답한다. RTO가 터진 경우다.
- 상대가 완전히 사라지면 재전송이 수십 번 반복되다가 약 15분 뒤에야 `ETIMEDOUT`이 난다.

## 동작·원리

### 1. 시퀀스 번호 — 바이트에 번호를 붙인다

```text
  송신 버퍼 (바이트 스트림)
  seq:  1000         1100         1200         1300
        |--- 100B ---|--- 100B ---|--- 100B ---|
        세그먼트 A     세그먼트 B     세그먼트 C
        <SEQ=1000>    <SEQ=1100>    <SEQ=1200>
```

- TCP 헤더의 시퀀스 번호는 **그 세그먼트 첫 바이트의 번호**다. 세그먼트 번호가 아니다(RFC 9293 §3.4).
- SYN과 FIN도 번호 하나씩을 차지한다. 그래야 SYN·FIN도 ACK로 확인하고 재전송할 수 있다(§3.4).
- 번호는 32비트이고 2^32에서 다시 0으로 돈다. 그래서 크기 비교는 모듈러 산술로 한다(§3.4).
- 첫 번호(ISN)는 연결마다 예측하기 어렵게 고른다(§3.4.1).
  - *ISN(Initial Sequence Number)*: 연결을 열 때 SYN에 싣는 시작 번호다. 이전 연결의 늦게 도착한 세그먼트와 헷갈리지 않고, 공격자가 번호를 추측하지 못하게 한다.

### 2. 누적 ACK — "여기까지 다 받았다"

```text
  송신자                                         수신자 (RCV.NXT = 다음에 기대하는 번호)
  A <SEQ=1000,100B> ----------------------->     RCV.NXT 1000 -> 1100
                    <-------------------------   <ACK=1100>   "1099까지 다 받음, 1100 줘"
  B <SEQ=1100,100B> ----X  (유실)
  C <SEQ=1200,100B> ----------------------->     구멍이 있다. C는 보관만 한다
                    <-------------------------   <ACK=1100>   (중복 ACK: 여전히 1100)
```

- ACK 번호는 "**다음에 받기를 기대하는 바이트 번호**"다. 그 앞은 모두 받았다는 뜻이다.
  - *누적 ACK(cumulative ACK)*: 한 번의 ACK가 그 번호 앞의 모든 바이트를 한꺼번에 확인하는 방식이다. ACK 하나가 유실돼도 다음 ACK가 대신 확인해 준다.
- 구멍 뒤에 도착한 C는 버리지 않고 수신 버퍼에 보관한다. 하지만 ACK 번호는 1100에서 멈춘다.
  - *중복 ACK(duplicate ACK)*: ACK 번호가 앞으로 나가지 않은 채 같은 값으로 다시 온 ACK다.
- 수신자는 순서가 어긋난 세그먼트를 받으면 **즉시** 중복 ACK를 보내야 한다(SHOULD, RFC 5681 §3.2·§4.2). 구멍을 메우는 세그먼트를 받아도 즉시 ACK한다(SHOULD).
- 송신자 쪽 변수는 셋이다(RFC 9293 §3.3.1).

```text
          SND.UNA                 SND.NXT
             |                       |
  ... 확인됨 | 보냈지만 아직 ACK 없음 | 아직 안 보냄 ...
             |<----- in flight ----->|
```

  - *SND.UNA*: 아직 ACK를 못 받은 가장 오래된 바이트 번호.
  - *SND.NXT*: 다음에 보낼 바이트 번호.
  - *in flight(FlightSize)*: 보냈지만 아직 ACK되지 않은 양. SND.NXT − SND.UNA다.

### 3. 재전송 타이머(RTO) — 시간으로 유실을 판단한다

```text
  시간 --->
  송신: [B 전송] --------------- RTO ---------------> [B 재전송] ------ 2×RTO ------> [B 재전송]
                                                     (RTO 두 배)                    (또 두 배)
        ACK가 이 안에 오면 타이머 끔                    지수 백오프
```

RFC 6298이 RTO 계산을 정한다.\
RTT 측정값 R이 들어올 때마다 두 값을 갱신한다.

```text
  첫 측정:   SRTT <- R
             RTTVAR <- R/2
  이후 측정: RTTVAR <- (1 - 1/4) * RTTVAR + 1/4 * |SRTT - R'|    (먼저 계산)
             SRTT   <- (1 - 1/8) * SRTT   + 1/8 * R'
  공통:      RTO <- SRTT + max(G, 4 * RTTVAR)
```

  - *RTT(Round-Trip Time)*: 세그먼트를 보내고 그 ACK가 돌아오기까지 걸린 시간이다.
  - *SRTT(smoothed RTT)*: RTT의 지수 가중 이동 평균이다. 새 표본에 1/8, 과거에 7/8 가중치를 준다.
  - *RTTVAR*: RTT가 얼마나 흔들리는지(평균 편차)의 이동 평균이다. 가중치는 1/4이다.
  - *G*: 시계 해상도(clock granularity)다.

- 순서가 중요하다. RTTVAR를 **먼저**, 갱신 전 SRTT로 계산한다(MUST, §2.3).
- α=1/8, β=1/4는 권고값이다(SHOULD, §2.3).
- 측정값이 아직 없으면 RTO는 1초로 둔다(SHOULD, §2.1). 옛 규격은 3초였고, 지금도 1초보다 큰 값을 써도 된다(MAY).
- 계산한 RTO가 1초보다 작으면 1초로 올린다(SHOULD, §2.4). 최댓값을 둘 수 있지만 60초 이상이어야 한다(MAY, §2.5).
- 타이머가 만료되면 가장 오래된 미확인 세그먼트를 재전송하고(§5.4) **RTO를 두 배로** 한다(MUST, §5.5).
- 백오프된 RTO는 새 데이터가 재전송 없이 ACK될 때 새 RTT 표본으로 다시 계산되며 내려온다(§5 끝 Note, RFC 9293 §3.8.2).

**Karn의 알고리즘** — 재전송한 세그먼트로는 RTT를 재지 않는다(MUST, RFC 6298 §3).

```text
  B 전송(t=0) ----X
  B 재전송(t=1s) ----------->
                <----------- ACK   (t=1.05s)
  이 ACK는 첫 전송의 것인가, 재전송의 것인가?  -> 모른다 -> 표본으로 쓰지 않는다
```

- 타임스탬프 옵션을 쓰면 어느 전송에 대한 ACK인지 구분되므로 재전송 세그먼트로도 잴 수 있다(§3).

**리눅스는 RFC 권고와 다르다**

- 리눅스 커널의 최소 RTO는 200ms다(`TCP_RTO_MIN = HZ/5`, `include/net/tcp.h`, sysctl `tcp_rto_min_us` 기본 200000).
  - RFC 6298의 1초 하한(SHOULD)보다 낮다. 데이터센터처럼 RTT가 짧은 곳에서 1초를 기다리면 너무 느리기 때문이다.
- 최대 RTO는 120초(`TCP_RTO_MAX`, `tcp_rto_max_ms` 기본 120000), 초기 RTO는 1초(`TCP_TIMEOUT_INIT`)다.
- 재전송 포기 시점은 `tcp_retries2`(기본 15)가 정한다.
  - 커널 문서 기준으로 200ms에서 시작해 지수 백오프하면 가상 타임아웃이 924.6초(약 15분)다. 이것은 실제 타임아웃의 **하한**이다(ip-sysctl `tcp_retries2`).
  - tcp(7)은 RTO에 따라 약 13~30분이라고 적는다.
  - RFC 9293은 이 한도(R2)가 최소 100초는 되어야 한다고 권한다(SHOULD, SHLD-11, §3.8.3).

### 4. 빠른 재전송(fast retransmit) — 중복 ACK 3개면 기다리지 않는다

```text
  송신                                  수신 (ACK 번호)
  1 ---------------------------------->  ACK 2
  2 ---X
  3 ---------------------------------->  ACK 2  (dup 1)
  4 ---------------------------------->  ACK 2  (dup 2)
  5 ---------------------------------->  ACK 2  (dup 3)   <- 3번째 중복 ACK
  2 (재전송, RTO 안 기다림) ----------->  ACK 6  (구멍이 메워져 한꺼번에 확인)
```

- 중복 ACK 3개가 오면 해당 세그먼트가 유실됐다고 보고 즉시 재전송한다(SHOULD, RFC 5681 §3.2).
- 왜 1개가 아니라 3개인가? 중복 ACK는 유실이 아니라 **순서 바뀜(재정렬)** 때문에도 생긴다. 조금 늦게 온 세그먼트를 유실로 오해하지 않으려는 문턱이다.
- 중복 ACK가 온다는 건 뒤의 세그먼트들은 도착했다는 뜻이다. 그래서 망이 완전히 막힌 게 아니라고 보고, 혼잡 윈도를 1로 줄이지 않고 **fast recovery**로 넘어간다. 윈도 조절은 18번 노트의 몫이다.
- 리눅스의 중복 ACK 문턱 초깃값은 `tcp_reordering`(기본 3)이다(tcp(7)).

### 5. SACK — "구멍이 어디인지" 알려 준다

누적 ACK는 "1100까지 받았다"만 말한다.\
그 뒤에 무엇을 받았는지는 모른다.\
한 윈도 안에서 여러 개가 유실되면 송신자는 RTT마다 하나씩만 알아낸다.

```text
  수신 버퍼:  [..1099 받음][1100~1199 없음][1200~1399 받음][1400~1499 없음][1500~1599 받음]
  ACK:  <ACK=1100> <SACK: 1200-1400, 1500-1600>
               ^            ^
         누적 ACK    "이 블록들은 이미 있다"  -> 송신자는 1100~1199, 1400~1499만 재전송
```

- 연결을 열 때 SYN에 **SACK-permitted 옵션**(kind 4)을 실어 합의한다. SYN이 아닌 세그먼트에는 보내면 안 된다(MUST NOT, RFC 2018 §2).
- SACK 옵션(kind 5)은 받은 블록의 [왼쪽 끝, 오른쪽 끝)을 나열한다(§3).
  - 옵션 공간이 40바이트라 블록은 최대 4개다. 타임스탬프 옵션과 같이 쓰면 최대 3개다(§3).
  - 첫 블록은 이 ACK를 유발한 세그먼트가 속한 블록이어야 한다(MUST, §4). 그 세그먼트가 ACK 번호를 전진시켰으면 예외다.
- SACK으로 알린 데이터도 수신자가 버퍼가 부족하면 버릴 수 있다(reneging, §8).
  - 그래서 송신자는 **누적 ACK로 확인되기 전까지** 데이터를 버리면 안 된다(MUST, §8).
- 리눅스는 SACK를 기본으로 켠다(`tcp_sack`, tcp(7)).
- **D-SACK**(RFC 2883): 이미 받은 데이터가 또 오면 그 범위를 SACK 블록으로 알린다. 송신자는 "불필요한 재전송을 했다"는 것을 알게 된다. 리눅스 `tcp_dsack` 기본 켜짐(tcp(7)).

### 6. 꼬리 유실과 RACK-TLP — 뒤에 오는 세그먼트가 없을 때

```text
  송신: 1 2 3 4 5(X 유실)      <- 마지막 세그먼트가 유실
  수신: ACK 2 3 4 5            <- 5 뒤에 보낸 게 없으니 중복 ACK도 없다
  결과: 중복 ACK 3개가 절대 오지 않는다 -> RTO까지 기다린다
```

- 요청·응답의 **마지막** 세그먼트가 유실되면 fast retransmit이 동작할 재료(중복 ACK)가 없다. 그래서 RTO를 기다린다.
- **TLP(Tail Loss Probe)**: 약 2×SRTT(PTO) 동안 ACK가 없으면 세그먼트 하나를 탐침으로 보낸다. 그 ACK·SACK로 유실을 빨리 알아낸다(RFC 8985 §7).
- **RACK**: 중복 ACK 개수 대신 **시간**으로 유실을 판단한다.
  - "나보다 나중에 보낸 세그먼트가 이미 ACK됐는데, 나는 재정렬 창만큼 지나도 소식이 없다" → 유실로 본다(RFC 8985 §3.1).
  - 재정렬 창은 최대 SRTT로 묶어야 한다(MUST 묶음, 그 상한은 SHOULD SRTT, §3.3).
- RFC 8985는 RACK-TLP를 중복 ACK 문턱 방식의 대안으로 권한다(RECOMMENDED, §1).
- 리눅스는 RACK을 기본 손실 탐지로 쓰고(`tcp_recovery` 0x1), TLP도 기본으로 켠다(`tcp_early_retrans` 3)(ip-sysctl).

### 7. 앱에서 보이는 모습

```text
  네트워크에서 일어난 일            앱이 보는 것
  ---------------------------     ----------------------------------------------
  유실 1개 -> fast retransmit      에러 없음. 해당 요청만 약 1 RTT 늦음
  꼬리 유실 -> TLP                 에러 없음. 약 2 RTT 늦음
  꼬리 유실 -> RTO                 에러 없음. RTO(리눅스 최소 200ms)만큼 멈춤
  연속 RTO (지수 백오프)            에러 없음. 수 초~수십 초 멈춤
  상대 소멸 -> tcp_retries2 초과    한참 뒤 ETIMEDOUT
```

- 재전송은 커널 안에서 끝난다. 앱은 `read()`가 늦게 돌아오는 것만 본다.
- 그래서 재전송 문제는 **로그가 아니라 지연 분포와 커널 카운터**로 찾는다.

## 쓰이는 자료구조·알고리즘

- **슬라이딩 윈도(송신 측)** — SND.UNA와 SND.NXT 사이가 "보냈지만 확인 안 된" 구간이다.
  - ACK가 오면 왼쪽 끝(SND.UNA)이 오른쪽으로 민다. 윈도 크기 자체는 17번(흐름 제어)·18번(혼잡 제어)이 정한다.
- **재전송 큐** — 확인 안 된 세그먼트를 시퀀스 순으로 보관한다.
  - 리눅스는 4.15(2017년 10월 패치)부터 이 큐를 레드-블랙 트리로 바꿨다. 패치 설명은 "현대의 큰 BDP에 맞추기 위해"이고, kernelnewbies 4.15는 "100Gb에서 1GB 윈도면 꼭 필요해졌다"고 적는다(LWN "tcp: implement rb-tree based retransmit queue", kernelnewbies Linux_4.15). 윈도 안 세그먼트가 많으면 SACK 처리 때 연결 리스트를 훑는 비용이 커진다.
  - 순서가 어긋나 도착한 수신 데이터(out-of-order 큐)도 레드-블랙 트리로 관리한다(include/linux/tcp.h `struct rb_root out_of_order_queue`).
  - 개념은 [레드-블랙 트리](../../data-structure/16-red-black-tree/2-summary.md) 참고.
- **EWMA(지수 가중 이동 평균)** — SRTT와 RTTVAR. 과거 전체를 저장하지 않고 값 두 개로 "평균과 흔들림"을 추적한다.
  - `new = (1 - α) * old + α * sample`. α가 작을수록 느리게 반응하고 잡음에 강하다.
- **지수 백오프** — 연속 RTO마다 대기 시간을 두 배로. 앱 수준 재시도의 [재시도·백오프](../../ops-patterns/01-retry-backoff/2-summary.md)와 같은 생각이다. 망이 막혔을 때 모두가 더 세게 두드리지 않게 한다.
- **구간 집합(interval set)** — SACK 블록은 "받은 바이트 구간" 목록이다. 새 블록이 오면 겹치는 구간을 합친다.
- **타이머** — 연결마다 재전송·TLP·지연 ACK 타이머가 붙는다. 리눅스는 이를 하나의 "on" 타이머로 보여 준다(ss(8) `-o`). 타이머 구조 일반은 data-structure `timer-structures` — 미작성([영역 표](../../data-structure/curriculum.md)).

## 적용 — 풀어나가는 법

### 1. RTO 추정기를 직접 써 본다

RFC 6298 §2를 그대로 옮긴 Java 코드다.\
숫자로 돌려 보면 "RTT가 흔들리면 RTO가 크게 뛴다"는 것이 보인다.

```java
final class RtoEstimator {
    private static final double ALPHA = 1.0 / 8, BETA = 1.0 / 4;
    private static final int K = 4;
    private final double g;          // 시계 해상도(초)
    private Double srtt, rttvar;     // 첫 측정 전에는 null
    private double rto = 1.0;        // RFC 6298 (2.1): 첫 RTO 1초

    RtoEstimator(double granularitySec) { this.g = granularitySec; }

    /** 재전송되지 않은 세그먼트의 RTT 표본만 넣는다 (Karn). */
    void onSample(double r) {
        if (srtt == null) {                       // (2.2)
            srtt = r;
            rttvar = r / 2;
        } else {                                  // (2.3) RTTVAR 먼저, 갱신 전 SRTT로
            rttvar = (1 - BETA) * rttvar + BETA * Math.abs(srtt - r);
            srtt = (1 - ALPHA) * srtt + ALPHA * r;
        }
        rto = Math.max(1.0, srtt + Math.max(g, K * rttvar));   // (2.4) 1초 하한
    }

    void onTimeout() { rto = Math.min(rto * 2, 60.0); }        // (5.5) 백오프, (2.5) 상한 예시 60초
    double rto() { return rto; }
}
```

- 예시: RTT가 100ms로 고르면 RTO는 1초 하한에 붙는다. RTT가 100ms와 400ms를 오가면 RTTVAR가 커져 RTO가 1초를 넘는다.
- 리눅스처럼 하한을 200ms로 바꿔 보면, 짧은 RTT 망에서 RTO가 얼마나 줄어드는지 비교할 수 있다.

### 2. 재전송이 있는지 먼저 확인한다

```bash
# 연결별: rto, rtt/rttvar, retrans(현재/누적), lost, sack 여부
ss -tin dst 10.0.0.5

#   예시 출력 일부:  sack cubic wscale:7,7 rto:204 rtt:3.5/1.2 ... retrans:0/12 lost:0

# 시스템 전체 카운터 (-a: 누적, -z: 0도 표시)
nstat -az TcpRetransSegs TcpExtTCPFastRetrans TcpExtTCPLossProbes \
          TcpExtTCPSpuriousRTOs TcpExtTCPSACKReorder

# 타이머 상태: timer:(on,120ms,2) = 재전송 타이머, 120ms 뒤 만료, 재전송 2회째
ss -tno state established dst 10.0.0.5
```

- `ss -i`의 `rto`는 밀리초이고, 실제 대기는 `rto << backoff`다(ss(8)).
  - 단, 현재 커널은 재전송 타임아웃 때 `icsk_rto` 자체를 두 배로 만든다(net/ipv4/tcp_timer.c `tcp_retransmit_timer`). 그래서 재전송 백오프 중 `rto`는 이미 백오프된 값이고, `backoff`는 연속 타임아웃 횟수로 읽는다. 남은 시간은 `ss -o`의 `timer:(on,…)`로 본다.
- `retrans:a/b`에서 a는 지금 재전송 중인(아직 ACK 안 된) 세그먼트 수, b는 연결 전체 누적이다(iproute2 misc/ss.c가 `tcpi_retrans`/`tcpi_total_retrans`를 찍고, 커널은 `tcpi_retrans = tp->retrans_out`, net/ipv4/tcp.c).
- `TcpExtTCPSpuriousRTOs`는 F-RTO가 "불필요했던 RTO"라고 판정한 횟수다(커널 snmp_counter 문서). 이 값이 크면 망이 느린 것이지 유실된 게 아닐 수 있다.

### 3. 패킷으로 확인한다

```bash
# 재전송은 같은 seq가 두 번 나오는 것으로 보인다
tcpdump -ni eth0 'host 10.0.0.5 and tcp port 443' -ttt
```

- Wireshark는 `tcp.analysis.retransmission`, `tcp.analysis.fast_retransmission`, `tcp.analysis.duplicate_ack`로 걸러 볼 수 있다(Wireshark Display Filter Reference: tcp).
- 첫 전송과 재전송 사이 간격을 본다.
  - 약 RTT 1개 → fast retransmit
  - 약 2 RTT → TLP
  - 200ms 이상이고 이후 두 배씩 → RTO와 백오프

### 4. 앱 쪽 방어선을 둔다

- 재전송은 앱이 제어하지 못한다. 대신 **앱 타임아웃**을 요청 단위로 둔다(Java `setSoTimeout`, Node `socket.setTimeout` + `destroy`).
- 멱등한 요청은 타임아웃 뒤 **다른 연결로** 재시도하면 꼬리 지연이 줄어든다(hedged request [?]). 비멱등 요청은 재시도하지 않는다.
- 상대가 사라졌을 때 15분 기다리지 않으려면 `TCP_USER_TIMEOUT`을 쓴다. 21번 노트에서 다룬다.

## 장애 시나리오와 대처

### 1. 에러는 0인데 p99만 높다 — 유실·재정렬로 인한 꼬리 지연

- **현상**: 평균·p50은 정상이다. p99·p999만 수백 ms~1초 이상이다. 에러율은 0이다.
- **보이는 형태**
  - `nstat`의 `TcpRetransSegs`가 꾸준히 증가한다.
  - `ss -ti`의 `retrans:0/N`에서 N이 크다.
  - tcpdump에 같은 seq가 두 번 보인다.
- **원인**
  - 경로의 패킷 유실(혼잡한 링크, 오류 있는 NIC·케이블, 과부하 LB)이다.
  - 또는 경로가 여러 갈래라 순서가 자주 바뀐다. 흐름 단위 해시 ECMP는 보통 한 흐름을 한 경로에 두지만, 패킷 단위(라운드로빈) 분산이나 경로 변경은 재정렬을 만든다(RFC 2991 §2·§6). 그러면 중복 ACK 문턱에 걸려 불필요한 재전송이 나간다.
- **대처**
  - 어느 홉에서 유실되는지 찾는다(`mtr`, 인터페이스 `ip -s link`의 drop·error 카운터).
  - SACK이 양쪽에서 켜져 있는지 `ss -ti`의 `sack`로 확인한다. 중간 장비가 옵션을 떼면 없다.
  - 재정렬이 원인이면 `TcpExtTCPSACKReorder`가 오른다. RACK은 D-SACK를 받으면 재정렬 창을 넓힌다(SHOULD, RFC 8985 §3.3).

### 2. 요청이 계단 모양으로 멈췄다가 성공한다 — RTO와 지수 백오프

- **현상**: 특정 요청만 RTO, RTO×3(1+2), RTO×7(1+2+4)처럼 계단 모양으로 늦다.
  - 연결 수립(SYN) 단계면 초기 RTO가 1초다.
    - 클라이언트 SYN 유실: 리눅스 6.5+ 기본값(`tcp_syn_linear_timeouts`=4)은 처음 5번 재전송이 1초 간격이다(초기 1번 + 선형 4번). 약 1초, 2초, 3초, 4초, 5초, 7초… 계단이다(6.5 이전은 1초, 3초, 7초).
    - 서버 SYN-ACK 유실: 선형 설정이 적용되지 않아 1초, 3초, 7초 계단이다(ip-sysctl).
  - 수립된 연결이면 그 연결의 현재 RTO(리눅스 최소 200ms)에서 시작한다.
- **보이는 형태**
  - 지연 히스토그램에 계단형 봉우리가 있다.
  - tcpdump에서 재전송 간격이 두 배씩 늘어난다.
  - 연결 수립 단계면 SYN 재전송이다. 리눅스 초기 RTO는 1초다(`TCP_TIMEOUT_INIT`).
- **원인**
  - 꼬리 유실이나 연속 유실로 fast retransmit·TLP가 못 잡은 경우다. RTO까지 기다리고, 또 유실되면 두 배로 기다린다.
  - SYN·SYN-ACK 유실은 RTT 표본이 아직 없어 초기 RTO(1초)부터 시작한다. 리눅스 6.5+의 SYN만 처음 4번은 두 배로 늘리지 않는다.
- **대처**
  - 짧은 요청은 앱 수준에서 타임아웃·재시도 예산을 짧게 두고, 멱등이면 다른 연결로 재시도한다.
  - 연결을 재사용(커넥션 풀)하면 SYN 단계의 1초 RTO 노출이 준다(35번).
  - 유실 자체를 줄이는 것이 근본 대처다.

### 3. 상대가 사라졌는데 15분 넘게 에러가 안 난다

- **현상**: 상대 서버가 네트워크에서 사라졌다(전원 차단, 방화벽이 조용히 drop). 보내는 쪽 요청이 한참 멈춰 있다.
- **보이는 형태**
  - `ss -tio`에 `timer:(on,…,N)`에서 N(재전송 횟수)이 계속 오른다. `Send-Q`가 쌓여 있다.
  - 결국 `ETIMEDOUT`(Java `SocketException: Connection timed out` [?], Node `Error: … ETIMEDOUT`)이다.
  - `nstat`의 `TcpExtTCPAbortOnTimeout`이 1 오른다.
- **원인**: RST도 ICMP도 오지 않으니 커널은 유실로만 본다. `tcp_retries2`(기본 15)로 계산한 시간 한도까지 백오프 재전송한 뒤 포기한다(15는 고정 횟수가 아니다). 하한이 약 924.6초다(ip-sysctl).
- **대처**
  - `TCP_USER_TIMEOUT`으로 "ACK 없이 버틸 최대 시간"을 연결별로 줄인다(tcp(7)).
  - `tcp_retries2`를 시스템 전체로 낮추는 것은 모든 연결에 영향을 준다. RFC 1122 권고(100초 이상)에 맞추려면 8 이상이어야 한다(ip-sysctl).
  - 앱 수준 요청 타임아웃을 반드시 둔다(21번).

### 4. 재전송이 폭증하는데 망에는 유실이 없다 — 불필요한 재전송

- **현상**: 재전송 카운터가 높은데 인터페이스·스위치 drop은 0이다.
- **보이는 형태**: `TcpExtTCPSpuriousRTOs`가 오르거나 D-SACK가 많이 보인다(Wireshark에서 이미 ACK된 범위를 SACK로 다시 알림).
- **원인**
  - RTT가 갑자기 늘었다(가상 머신 일시 정지, 무선 구간 재전송, 큐 적체). 기존 RTO보다 ACK가 늦게 와서 타이머가 먼저 터졌다.
  - 또는 재정렬이 중복 ACK 문턱을 넘었다.
- **대처**
  - 리눅스는 F-RTO(RFC 5682)로 불필요한 RTO를 감지한다. 감지 횟수가 `TcpExtTCPSpuriousRTOs`다(snmp_counter 문서).
  - 원인은 지연 급증이다. 큐 적체(bufferbloat, 18번)나 호스트 CPU 정체를 먼저 본다.

## 핵심 문장

- TCP는 **바이트**에 번호를 붙이고, ACK는 "다음에 기대하는 바이트 번호"다. 한 번의 ACK가 그 앞 전부를 확인한다(누적 ACK).
- 유실은 두 가지로 판단한다. 중복 ACK 3개(빠른 재전송)와 타이머 만료(RTO)다. RACK은 개수 대신 시간으로 판단한다.
- RTO는 SRTT + 4·RTTVAR이다. RTT의 평균과 흔들림을 EWMA로 추적하고, 재전송한 세그먼트로는 재지 않는다(Karn).
- RTO가 터지면 두 배씩 백오프한다. 그래서 "에러 없는 계단형 지연"이 생기고, 상대가 사라지면 리눅스는 약 15분 넘게 재전송한다.
- SACK은 누적 ACK가 말하지 못하는 "구멍의 위치"를 알려 준다. 한 윈도의 여러 유실을 한 RTT 안에 복구하게 한다.

## 관련 주제·근거

- 선행: [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md)
- 후속·연결
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — 수신 윈도가 송신 윈도의 상한을 정한다
  - [18-tcp-congestion-control](../18-tcp-congestion-control/2-summary.md) — 유실 신호에 대해 혼잡 윈도가 어떻게 반응하나(fast recovery)
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 재전송 끝에 연결이 죽는 경우
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — `TCP_USER_TIMEOUT`으로 재전송 포기 시점 줄이기
  - [22-nagle-and-delayed-ack](../22-nagle-and-delayed-ack/2-summary.md) — 지연 ACK가 RTT 측정과 ACK 흐름에 주는 영향
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — 앱 수준의 지수 백오프
  - [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md) — 리눅스 재전송 큐
- RFC
  - RFC 9293 (TCP) <https://www.rfc-editor.org/rfc/rfc9293> — §3.4 시퀀스 번호 · §3.4.1 ISN · §3.3.1 SND.UNA/SND.NXT/RCV.NXT · §3.8.1 RTO는 RFC 6298을 따름(MUST-18) · §3.8.2 지수 백오프 필수(MUST-19) · §3.8.3 R1·R2(R2 ≥ 100초, SHLD-11)
  - RFC 6298 (Computing TCP's Retransmission Timer) <https://www.rfc-editor.org/rfc/rfc6298> — §2 SRTT·RTTVAR·RTO 공식과 α=1/8·β=1/4 · §2.1 초기 1초 · §2.4 1초 하한 · §2.5 상한 ≥ 60초 · §3 Karn · §5 타이머 관리·백오프
  - RFC 5681 (TCP Congestion Control) <https://www.rfc-editor.org/rfc/rfc5681> — §3.2 중복 ACK 3개 fast retransmit · §4.2 순서 어긋난 세그먼트에 즉시 ACK
  - RFC 2018 (SACK) <https://www.rfc-editor.org/rfc/rfc2018> — §2 SACK-permitted(kind 4, SYN 전용) · §3 블록 최대 4개/타임스탬프와 3개 · §4 첫 블록 규칙 · §8 reneging
  - RFC 2883 (D-SACK) <https://www.rfc-editor.org/rfc/rfc2883>
  - RFC 8985 (RACK-TLP) <https://www.rfc-editor.org/rfc/rfc8985> — §3.1 시간 기반 유실 판단 · §3.3 재정렬 창 · §7 PTO = 2·SRTT
  - RFC 5682 (F-RTO) <https://www.rfc-editor.org/rfc/rfc5682>
  - RFC 2991 (Multipath Issues) §2·§6 — 패킷 단위 분산의 재정렬 <https://www.rfc-editor.org/rfc/rfc2991>
- Linux
  - tcp(7) — `tcp_retries2`(15, 약 13~30분), `tcp_reordering`(3), `tcp_sack`, `tcp_dsack` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - 커널 문서 ip-sysctl — `tcp_retries2`(가상 924.6초 하한), `tcp_rto_min_us`(200000), `tcp_rto_max_ms`(120000), `tcp_recovery`(RACK), `tcp_early_retrans`(TLP), `tcp_syn_linear_timeouts`(6.5+, SYN 선형 백오프 기본 4, SYN-ACK 미적용) <https://docs.kernel.org/networking/ip-sysctl.html>
  - `include/net/tcp.h` — `TCP_RTO_MIN`(HZ/5), `TCP_RTO_MAX`(120초), `TCP_TIMEOUT_INIT`(1초) <https://github.com/torvalds/linux/blob/master/include/net/tcp.h>
  - 커널 문서 snmp_counter — `TcpExtTCPSpuriousRTOs`, `TcpExtTCPLossProbes`, `TcpExtTCPAbortOnTimeout` <https://docs.kernel.org/networking/snmp_counter.html>
  - ss(8) — `-i`의 `rto`·`backoff`·`rtt`, `-o` 타이머 <https://man7.org/linux/man-pages/man8/ss.8.html>
  - LWN, "tcp: implement rb-tree based retransmit queue"(2017) <https://lwn.net/Articles/735881/>
- 교재
  - Kurose & Ross 8판 3.4(신뢰적 데이터 전송 원리)·3.5(TCP)
  - Stevens, 『TCP/IP Illustrated Vol.1』 2판 14장 "TCP Timeout and Retransmission"
