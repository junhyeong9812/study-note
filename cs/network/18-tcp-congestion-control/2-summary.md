# network/18-tcp-congestion-control — 망이 막히지 않게 보내는 속도를 스스로 조절하는 법 — 정리 (힌트)

## 해결하는 문제

흐름 제어(17번)는 **받는 호스트**가 넘치지 않게 한다.\
그런데 두 호스트 사이의 라우터·링크도 넘친다.\
모든 송신자가 수신 윈도만큼 마구 보내면, 병목 라우터의 큐가 넘쳐 패킷이 버려진다.\
버려진 패킷을 모두가 재전송하면 망은 더 막힌다. 일은 많이 하는데 전달되는 양은 0에 가까워진다(혼잡 붕괴).

```text
  송신자 A ==(1 Gbit/s)==\
                          [라우터 큐 ||||||||||| 가득] ==(100 Mbit/s 병목)==> 수신자
  송신자 B ==(1 Gbit/s)==/        ^ 넘치면 drop
```

쉬운 예: 고속도로 진입 램프의 신호등이다.\
본선이 막히면 진입 간격을 늘리고, 뚫리면 조금씩 줄인다.\
운전자는 본선 상황을 직접 못 보고 "내 차가 얼마나 빨리 빠져나갔나"로만 추측한다.

똑같은 구조다.\
TCP 송신자는 망 상태를 직접 모른다.\
ACK가 돌아오는 속도, 유실, 지연을 보고 **혼잡 윈도(cwnd)**를 스스로 키우고 줄인다.\
RFC 9293은 slow start, 혼잡 회피, RTO 지수 백오프 구현을 필수로 정한다(MUST-19, §3.8.2).

실무 예:
- 한동안 쉬던 keep-alive 연결로 큰 응답을 보내니 첫 응답만 느리다(slow start 재시작).
- 업로드를 시작하면 같은 회선의 화상 통화·SSH가 수백 ms씩 끊긴다(bufferbloat).
- 유실이 조금 있는 장거리 회선에서 처리량이 링크 속도의 몇 분의 일밖에 안 나온다.

## 동작·원리

### 1. cwnd — 송신자가 스스로 정한 상한

```text
  보낼 수 있는 양 = min(cwnd, rwnd) - FlightSize
                    ^       ^
                    |       수신자가 알린 윈도 (흐름 제어, 17번)
                    송신자가 추정한 망 여유 (혼잡 제어, 이 노트)
```

- *cwnd(congestion window)*: ACK를 받기 전에 망에 내보낼 수 있는 양의 송신 측 상한이다(RFC 5681 §3.1).
- *ssthresh(slow start threshold)*: slow start와 혼잡 회피를 가르는 문턱이다.
- *SMSS*: 송신자가 보낼 수 있는 최대 세그먼트 크기다.
- cwnd는 헤더에 실리지 않는다. 송신자 커널 안에만 있다. 그래서 `ss -ti`로 봐야 한다.

### 2. 전체 흐름 — 톱니 모양

```text
  cwnd
   ^
   |                       x 3 dup ACK                        x 3 dup ACK
   |                      /|                                 /|
   |                     / |      /\ (선형 증가)             / |
   |    ssthresh ------ /--|-----/--\-------------------- ... |
   |                  /    |    /                             |
   |                 /     |___/  <- 절반으로 (fast recovery)  |
   |               /                                          |
   |            _/  <- slow start (지수)                       |      RTO!
   |         _/                                               |_____ cwnd = 1 SMSS
   |  IW  _/                                                         다시 slow start
   +----------------------------------------------------------------------------> 시간
```

### 3. slow start — 모르는 망은 작게 시작해 두 배씩

```text
  RTT 1:  [][][][][][][][][][]                          (IW = 10 세그먼트)
  RTT 2:  [][][][][][][][][][][][][][][][][][][][]      (20)
  RTT 3:  ... 40
  ACK 하나마다 cwnd += min(N, SMSS)  ->  RTT마다 약 두 배
```

- 처음에는 망 용량을 모른다. 그래서 작은 초기 윈도(IW)로 시작한다(RFC 5681 §3.1).
- 새 데이터를 확인하는 ACK마다 cwnd를 최대 SMSS만큼 늘린다. 세그먼트마다 ACK가 오면 ACK가 RTT당 cwnd개쯤 오니, RTT마다 약 두 배가 된다.
  - 지연 ACK로 두 세그먼트마다 ACK 하나가 오면, 아래 공식으로는 RTT마다 약 1.5배다(RFC 5681 §3.1·§4.2).
  - 리눅스는 ACK가 확인한 세그먼트 수만큼 cwnd를 늘린다(`tcp_slow_start`, net/ipv4/tcp_cong.c). 그래서 지연 ACK에서도 약 두 배에 가깝다.
  - 권고 공식은 `cwnd += min(N, SMSS)`다(N = 이 ACK가 새로 확인한 바이트, RECOMMENDED, §3.1). ACK를 잘게 쪼개 보내 cwnd를 부풀리는 수신자를 막는다.
- "slow"라는 이름과 달리 지수 증가다. 혼잡 제어 이전 구현의 "처음부터 수신 윈도만큼 한꺼번에"보다 느리다는 뜻이다(RFC 2001 §1 "Old TCPs would start a connection ... up to the window size advertised by the receiver").
- **초기 윈도(IW)**
  - RFC 5681 상한: SMSS에 따라 2~4 세그먼트(§3.1).
  - RFC 6928(실험적 RFC)은 `min(10*MSS, max(2*MSS, 14600))`, 즉 약 10 세그먼트를 제안한다.
  - 리눅스는 `TCP_INIT_CWND = 10`이다(`include/net/tcp.h`).
- cwnd가 ssthresh를 넘으면(또는 혼잡을 보면) slow start를 끝낸다(§3.1).
- RFC 9438은 CUBIC이 slow start에서 HyStart++(RFC 9406)를 쓰라고 권한다(SHOULD). 지연 증가를 보고 유실 전에 slow start를 멈추는 방식이다.

### 4. 혼잡 회피와 AIMD

```text
  혼잡 회피:  RTT마다 cwnd += 1 SMSS       (가법 증가, Additive Increase)
  혼잡 신호:  cwnd ≈ cwnd / 2              (승법 감소, Multiplicative Decrease)
```

- cwnd > ssthresh이면 RTT당 약 1 SMSS만 늘린다(§3.1). 한 RTT에 SMSS보다 많이 늘리면 안 된다(MUST NOT).
- 유실을 보면 절반으로 줄인다. 그래서 **AIMD**(가법 증가·승법 감소)다.
  - *AIMD*: 조금씩 늘리고 크게 줄이는 제어 규칙이다. 여러 흐름이 같은 병목을 나눌 때 공정한 몫으로 수렴한다(K&R 3.7).
- 유실을 혼잡 신호로 쓰는 이유: 병목 큐가 넘치면 버리기 때문이다. 이 방식을 **손실 기반**이라 한다(§3).

### 5. 유실에 대한 두 가지 반응

```text
  신호               판단                         반응 (RFC 5681)
  ----------------   --------------------------   ---------------------------------------------
  중복 ACK 3개       "하나 빠졌지만 뒤는 도착 중"   ssthresh = max(FlightSize/2, 2·SMSS)
                    (ACK 클럭이 살아 있다)          cwnd = ssthresh + 3·SMSS  -> fast recovery
                                                  새 ACK가 오면 cwnd = ssthresh (혼잡 회피로)
  RTO 만료           "새 데이터 ACK가 안 온다"       ssthresh = max(FlightSize/2, 2·SMSS)
                    (ACK 클럭이 끊겼다)             cwnd = 1 SMSS  -> slow start부터 다시
                                                  (같은 세그먼트가 또 타임아웃이면 ssthresh는 그대로)
```

- **fast recovery**: 중복 ACK가 온다는 건 뒤의 세그먼트가 수신자에 도착해 망을 떠났다는 뜻이다(§3.2).
  - 그래서 cwnd를 1로 떨어뜨리지 않고 절반 근처에서 계속 보낸다.
  - 중복 ACK 3개만큼(3·SMSS) 윈도를 임시로 부풀리고, 중복 ACK가 더 올 때마다 SMSS씩 더 부풀린다. 복구가 끝나면 ssthresh로 되돌린다(§3.2 단계 3·4·6).
- **RTO**: 재전송 타이머가 끝날 때까지 새 데이터를 확인하는 ACK가 없었다. 중복 ACK는 타이머를 다시 시작시키지 않는다(RFC 6298 §5.3). 망이 크게 막혔을 수 있다. cwnd를 1 SMSS(손실 윈도)로 떨어뜨리고 slow start로 다시 시작한다(MUST, §3.1).
  - ssthresh를 줄이는 것은 그 세그먼트의 첫 타이머 재전송 때다. 이미 타이머로 재전송한 세그먼트가 또 타임아웃되면 ssthresh는 유지한다(§3.1).
- 한 윈도에 여러 개가 유실되면 기본 fast recovery는 잘 복구하지 못한다(§3.2 Note). NewReno(RFC 6582)와 SACK 기반 복구(RFC 6675)가 이를 보완한다.
- 유실을 알아내는 방법 자체(중복 ACK, RACK-TLP)는 16번 노트의 몫이다.

### 6. 유휴 후 재시작 — 쉬고 나면 다시 작게

```text
  t=0     큰 응답 전송, cwnd가 100 세그먼트(예시)까지 커짐
  t=0~5s  유휴 (keep-alive 연결이 요청을 기다림)
  t=5s    다음 응답 전송
          -> 유휴 시간 > RTO 이므로 cwnd = min(IW, cwnd) = 10 으로 리셋 (RFC 5681 §4.1 기준)
          -> 다시 slow start: 여러 RTT가 더 걸림
```

- 오래 쉬면 ACK 클럭이 사라진다. 그 사이 망 상황도 바뀌었을 수 있다.
- 그래서 RTO보다 오래 데이터를 보내지 않았으면 cwnd를 RW = min(IW, cwnd) 이하로 줄이라고 권한다(SHOULD, RFC 5681 §4.1).
- 리눅스 `tcp_slow_start_after_idle`(기본 1)이 이 역할이다. 다만 방식은 RFC 2861이다. 유휴가 RTO 하나를 넘길 때마다 cwnd를 절반으로 줄이고, min(IW, cwnd)에서 멈춘다(ip-sysctl "provide RFC2861 behavior", net/ipv4/tcp_output.c `tcp_cwnd_restart`). 위 그림처럼 RTO의 수십 배를 쉬면 결과는 IW까지 내려간 것과 같다.
- HPBN은 오래 사는 HTTP 연결의 성능을 위해 서버에서 이것을 끄는 것을 권한다.

### 7. CUBIC — 시간의 3차 함수로 키운다

Reno식 선형 증가는 고BDP 망에서 느리다.\
윈도가 수천 세그먼트인데 유실 한 번에 절반으로 떨어지면, RTT당 1씩 늘려 원래대로 돌아가는 데 윈도의 절반만큼(수천) RTT가 걸린다(계산). RFC 9438 §1은 고BDP 망에서 유실 뒤 cwnd가 느리게 늘어 링크를 못 채우는 이 문제가 수백 패킷 윈도에서도 자주 관찰된다고 적는다.

```text
  cwnd
   ^                                               ,
   |                                             ,'   볼록: W_max 위로 점점 빠르게
   |                                          ,-'     (새 상한 탐색)
   |  W_max . . . . . . . . . . ,.-------.-''  . . . .   <- 직전 유실 시점의 윈도
   |                        _,-'     ^
   |                    _,-'         K 부근: 기울기가 거의 0
   |                 ,-'   오목: 빨리 다가가다 W_max 근처에서 천천히
   |               /
   |  β·W_max    o
   +--------------------------------------------------------> 유실 후 경과 시간 t
                                     K

  W_cubic(t) = C·(t - K)^3 + W_max,     K = 세제곱근((W_max - cwnd_epoch) / C)
```

- 증가량이 **RTT가 아니라 경과 시간**의 함수다. 그래서 RTT가 다른 흐름끼리도 (Reno-friendly 구간 밖에서는) 윈도 크기가 RTT와 무관하게 비슷해진다(RTT 공정성, §3.3).
- 혼잡 사건(중복 ACK 등으로 본 유실) 뒤 cwnd를 0.7배로 줄인다(β_cubic, SHOULD 0.7, §4.6). Reno의 0.5보다 덜 줄인다.
  - RTO에서는 Reno처럼 cwnd를 줄이고(1 SMSS), ssthresh만 β_cubic으로 정한다(§4.8).
- C는 0.4를 권한다(SHOULD, §5.1).
- Reno보다 느려지는 구간에서는 Reno처럼 동작한다(Reno-friendly region, §4.3).
- 리눅스·윈도·애플 스택의 기본 혼잡 제어다(RFC 9438 §1). 리눅스 커널 설정의 기본 선택도 CUBIC이다(`net/ipv4/Kconfig` `DEFAULT_CUBIC`).

### 8. BBR — 유실 대신 "대역폭과 최소 RTT"를 잰다

```text
  손실 기반 (Reno, CUBIC)                       모델 기반 (BBR)
  유실(또는 ECN 표시)이 올 때까지 키운다          병목 대역폭(max_bw)과 최소 RTT(min_rtt)를 측정
  -> 병목 큐를 가득 채운 채 운영                   -> 목표 in-flight ≈ max_bw × min_rtt (= BDP)
  -> 큐잉 지연이 늘어남                           -> 큐를 거의 비운 채 운영하려 함

  BBR 상태:  Startup (지수 증가) -> Drain (쌓인 큐 빼기) -> ProbeBW (주기적으로 더 보내 보기)
                                                          <-> ProbeRTT (잠깐 줄여 min_rtt 재측정)
```

- BBR은 전달률·RTT·유실률 측정으로 경로의 명시적 모델을 만든다(draft-ietf-ccwg-bbr).
- 얕은 버퍼나 무작위 유실이 있는 병목에서 손실 기반보다 처리량이 높다고 설명한다(draft).
- 상태: 이 문서는 IETF 실험(Experimental) 지향의 **인터넷 드래프트**이고 BBRv3를 기술한다. RFC가 아니다.
- 리눅스에는 `tcp_bbr` 모듈이 있다. Kconfig 도움말은 fq(Fair Queue) 페이싱 스케줄러가 필요하다고 적는다(`net/ipv4/Kconfig`).

### 9. bufferbloat — 큰 큐가 지연을 만든다

```text
  병목 라우터 큐가 너무 크다 (예시: 수백 ms 분량)
  손실 기반 TCP: 유실이 날 때까지 cwnd를 키움 -> (tail-drop 큐면) 큐가 꽉 참
  -> 같은 큐를 지나는 모든 패킷(작은 요청·DNS·게임·음성)이 수백 ms 대기
```

- *bufferbloat*: 라우터 등 망 장비가 데이터를 너무 많이 버퍼링해서 생기는 바람직하지 않은 지연이다(bufferbloat.net).
- 손실 기반 혼잡 제어는 큐가 버리거나 표시해야 혼잡을 알아챈다. 넘칠 때만 버리는 큰 FIFO(tail-drop) 큐에서는 **큐가 넘쳐야** 알아챈다. 큐가 클수록 알아채기 전까지 지연이 커진다.
- 대처는 큐 쪽에 있다.
  - *AQM(Active Queue Management)*: 큐가 넘치기 전에 일찍 버리거나 표시해서 송신자에게 신호를 주는 큐 관리다.
  - CoDel(RFC 8289)은 큐 체류 **시간**을 보고 버린다. FQ-CoDel(RFC 8290)은 흐름별로 큐를 나누고 CoDel을 적용한다. 둘 다 실험적 RFC다.
  - ECN(RFC 3168)은 버리는 대신 IP 헤더에 "혼잡" 표시를 해서 알린다. RFC 9293은 ECN 구현을 권한다(SHOULD, SHLD-8).

## 쓰이는 자료구조·알고리즘

- **AIMD 제어 루프(피드백 제어)** — 측정(ACK·유실·RTT) → 판단 → 조작(cwnd). 망을 모르는 채로 되먹임만으로 공정한 몫에 수렴한다.
  - 앱 수준 동시성 제한(적응형 동시성 제한 [?])이나 [백오프](../../ops-patterns/01-retry-backoff/2-summary.md)도 같은 뼈대다.
- **cwnd 상태 기계** — slow start / 혼잡 회피 / fast recovery / RTO 후 slow start. 입력은 ACK·중복 ACK·타이머다.
  - 리눅스는 이를 `enum tcp_ca_state`(`TCP_CA_Open`, `Disorder`, `CWR`, `Recovery`, `Loss`)로 관리한다(include/uapi/linux/tcp.h).
- **지수 탐색** — slow start는 "용량을 모를 때 두 배씩 키워 상한을 찾는" 탐색이다. 갤로핑 탐색과 같은 생각이다.
- **3차 함수 보간** — CUBIC은 직전 상한(W_max)을 기억하고 그 근처에서는 천천히, 멀어지면 빠르게 움직인다.
- **윈도 최소·최대 필터** — BBR은 최근 구간의 최대 전달률과 최소 RTT를 추적한다. 리눅스는 최소 RTT 추적에 윈도 최소 필터를 쓴다(`tcp_min_rtt_wlen` 기본 300초, ip-sysctl).
- **큐** — 병목 라우터의 FIFO 큐가 문제의 무대다. 큐잉 이론 일반은 math `queueing-and-littles-law`([영역 표](../../math/README.md)).

## 적용 — 풀어나가는 법

### 1. slow start를 숫자로 느껴 본다

TypeScript로 쓴 단순 모델이다(유실 없음, RTT 단위).

```ts
// 응답 크기를 보내는 데 몇 RTT가 드는지 (slow start만, 유실 없음)
function rttsToSend(bytes: number, mss = 1460, iw = 10): number {
  const segs = Math.ceil(bytes / mss);
  let cwnd = iw, sent = 0, rtts = 0;
  while (sent < segs) {
    sent += cwnd;      // 이번 RTT에 cwnd만큼 보냄
    cwnd *= 2;         // slow start: RTT마다 두 배
    rtts++;
  }
  return rtts;
}

rttsToSend(14_000);    // 1  (IW10 안에 들어감)
rttsToSend(100_000);   // 3  (10 + 20 + 40 = 70 세그먼트)
rttsToSend(1_000_000); // 7
```

- 예시: RTT 100ms면 100KB 응답은 전송에만 약 300ms가 든다. 연결을 새로 열거나 유휴 후 재시작하면 매번 이 비용을 낸다.
- 그래서 커넥션 재사용(35번), 응답 크기 줄이기가 지연에 직접 효과가 있다.

### 2. 현재 상태를 본다

```bash
# 사용 가능한/기본 알고리즘
sysctl net.ipv4.tcp_available_congestion_control net.ipv4.tcp_congestion_control

# 연결별 cwnd, ssthresh, 알고리즘 이름, rtt, retrans
ss -tin dst 203.0.113.10
#   예시: cubic wscale:7,7 rto:204 rtt:3.2/0.8 mss:1448 cwnd:48 ssthresh:36 ...

# 유휴 후 slow start 재시작 여부
sysctl net.ipv4.tcp_slow_start_after_idle
```

- `ss -i`의 `cong_alg` 자리에 알고리즘 이름이 나온다. ss(8)은 기본이 "cubic"이라고 적는다.

### 3. 알고리즘을 바꾼다 (측정 후에만)

```bash
# 시스템 전체 (새 연결부터)
modprobe tcp_bbr
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

```c
/* 연결 하나만: TCP_CONGESTION 소켓 옵션 (tcp(7)) */
const char *cc = "bbr";
setsockopt(fd, IPPROTO_TCP, TCP_CONGESTION, cc, strlen(cc));
```

- 리스닝 소켓의 선택은 수락한 연결이 물려받는다(ip-sysctl `tcp_congestion_control`).
- 바꾸기 전후로 처리량·지연·재전송률을 같이 잰다. 한 지표만 보면 다른 흐름을 밀어내는 것을 놓친다.

### 4. bufferbloat을 재고 줄인다

```bash
# 부하 중 지연 측정: 큰 업로드를 돌리면서 ping
ping -i 0.2 8.8.8.8          # 평소 20ms(예시)가 업로드 중 500ms(예시)로 뛰면 bufferbloat

# 내 호스트의 큐 규칙
tc qdisc show dev eth0
tc qdisc replace dev eth0 root fq_codel
```

- 리눅스 `net.core.default_qdisc`의 커널 기본값은 `pfifo_fast`다(커널 문서 sysctl/net). 배포판이 다른 값으로 바꿔 두기도 한다. 예: systemd의 `sysctl.d/50-default.conf`는 `net.core.default_qdisc = fq_codel`로 둔다.
- 병목이 내 호스트가 아니라 공유기·모뎀이면 그 장비에서 AQM(fq_codel 등)을 켜야 효과가 있다.

## 장애 시나리오와 대처

### 1. 쉬었다가 보낸 첫 응답만 느리다 — 유휴 후 slow start 재시작

- **현상**: keep-alive 연결에서 연속 요청은 빠른데, 몇 초 쉰 뒤 첫 큰 응답만 수백 ms 느리다.
- **보이는 형태**
  - 지연이 응답 크기에 비례해 계단형(RTT 배수)으로 늘어난다.
  - 유휴 직후 `ss -ti`의 `cwnd`가 10 근처로 내려가 있다.
  - 패킷 캡처에서 송신이 RTT마다 두 배로 불어나는 모양이다.
- **원인**: 유휴 시간이 RTO를 넘어 cwnd가 줄었다(RFC 5681 §4.1, `tcp_slow_start_after_idle=1`). 리눅스는 유휴 RTO마다 절반씩 줄인다. 그래서 RTO의 몇 배 이상 쉬면 초기 윈도(10)까지 내려간다.
- **대처**
  - 서버의 `net.ipv4.tcp_slow_start_after_idle=0`을 검토한다(HPBN 권고). 대신 유휴 후 한꺼번에 큰 버스트가 나간다는 트레이드오프가 있다(RFC 5681 §4.1).
  - 응답을 줄이거나 압축한다.

### 2. 업로드만 하면 모든 게 느려진다 — bufferbloat

- **현상**: 대용량 업로드·백업 중 같은 회선의 웹·SSH·화상 통화 지연이 수백 ms로 뛴다. 유실은 거의 없다.
- **보이는 형태**
  - 부하 중 `ping` RTT가 평소의 수 배~수십 배다.
  - 업로드 흐름의 `ss -ti` `rtt`가 계속 커진다. `retrans`는 적다.
- **원인**: 병목 장비의 큰 FIFO 큐를 손실 기반 TCP가 채웠다. 다른 흐름의 패킷도 그 큐 뒤에 줄 선다.
- **대처**
  - 병목 장비에 AQM(FQ-CoDel, RFC 8290)을 켠다.
  - 업로드를 병목보다 조금 낮게 속도 제한(쉐이핑)해 큐를 내 쪽으로 가져온다 [?].
  - BBR처럼 큐를 채우지 않으려는 알고리즘을 검토한다(측정 후).

### 3. 장거리·약간의 유실 회선에서 처리량이 안 나온다

- **현상**: 대역폭은 충분한데 원거리 전송이 링크의 몇 분의 일에 머문다. 윈도 스케일링(17번)은 정상이다.
- **보이는 형태**
  - `ss -ti`의 `cwnd`가 작은 값과 중간값 사이를 오르내린다. `retrans`가 조금씩 있다.
  - 재전송률은 낮은데(예: 0.1% (예시)) 처리량이 크게 떨어진다.
- **원인**: 손실 기반 혼잡 제어는 유실을 보면(혼잡이 아니어도) cwnd를 줄인다. 한 윈도 안의 여러 유실은 보통 한 번의 혼잡 사건으로 친다(RFC 5681 §4.3). 고BDP에서는 원래 크기로 되돌아가는 데 오래 걸린다(RFC 9438 §1).
- **대처**
  - 기본 CUBIC인지 확인한다(Reno보다 고BDP에 강하다).
  - 무작위 유실이 많은 경로는 BBR을 시험한다. draft는 얕은 버퍼·무작위 유실에서 처리량이 높다고 설명한다.
  - 유실 원인(무선 구간, 폴리서)을 찾는다.

### 4. 알고리즘을 바꿨더니 다른 서비스가 느려졌다

- **현상**: 한 서버군에 BBR을 켠 뒤, 같은 링크를 쓰는 다른 CUBIC 흐름의 처리량이 떨어졌다.
- **보이는 형태**: 링크 사용률은 같거나 높아졌는데, 흐름별 처리량 분포가 한쪽으로 쏠린다.
- **원인**: 서로 다른 알고리즘은 같은 병목을 다르게 나눈다. 버퍼 크기에 따라 한쪽이 더 많이 가져갈 수 있다 [?].
- **대처**: 전면 적용 전에 같은 병목을 공유하는 흐름들을 함께 측정한다. 흐름별 공정 큐(fq, fq_codel)를 병목에 둔다.

## 핵심 문장

- 흐름 제어는 수신 호스트를, 혼잡 제어는 **중간 망**을 보호한다. 송신량은 `min(cwnd, rwnd)`다.
- slow start는 작은 초기 윈도(리눅스 10)에서 RTT마다 두 배로 키운다. 혼잡 회피는 RTT마다 1 SMSS씩 늘리고, 혼잡을 보면 크게 줄인다(AIMD).
- 중복 ACK 3개는 "하나 빠졌지만 흐름은 산다"여서 절반으로 줄이고 계속 보낸다(fast recovery). RTO는 "다 멈췄다"여서 cwnd를 1로 떨어뜨린다.
- 오래 쉬면 cwnd가 초기 윈도 쪽으로 줄어든다(리눅스는 유휴 RTO마다 절반, 최저 IW). 그래서 유휴 뒤 첫 큰 응답이 느리다.
- 손실 기반 알고리즘은 큐가 버리거나(tail-drop이면 넘쳐야) ECN으로 표시해야 멈춘다. 큐가 크면 그 자체가 지연이 된다(bufferbloat). 해법은 큐 관리(AQM·ECN)와 모델 기반 제어(BBR)다.

## 관련 주제·근거

- 선행: [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — rwnd, `min(cwnd, rwnd)`의 다른 한쪽
- 연결
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 유실 탐지(중복 ACK, RTO, RACK-TLP)
  - [03-latency-bandwidth-bdp](../03-latency-bandwidth-bdp/2-summary.md) — BDP, 큐잉 지연
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 커넥션 재사용으로 slow start 비용 줄이기
  - [37-http3-quic](../37-http3-quic/2-summary.md) — QUIC도 같은 혼잡 제어 계열을 쓴다(RFC 9002)
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — 되먹임으로 부하를 줄이는 같은 생각
- RFC·드래프트
  - RFC 5681 (TCP Congestion Control) <https://www.rfc-editor.org/rfc/rfc5681> — §3.1 cwnd·rwnd·ssthresh, IW, slow start, 혼잡 회피, RTO 후 cwnd=1 SMSS, 반복 타임아웃 시 ssthresh 유지 · §3.2 fast retransmit/fast recovery · §4.1 유휴 후 재시작(RW) · §4.3 한 윈도 여러 유실
  - RFC 6298 §5.3 — 새 데이터를 확인하는 ACK에서 재전송 타이머 재시작 <https://www.rfc-editor.org/rfc/rfc6298>
  - RFC 9293 §3.8.2 — slow start·혼잡 회피·RTO 백오프 필수(MUST-19), ECN 권고(SHLD-8) <https://www.rfc-editor.org/rfc/rfc9293>
  - RFC 6928 (Increasing TCP's Initial Window, 실험적) <https://www.rfc-editor.org/rfc/rfc6928>
  - RFC 6582 (NewReno) <https://www.rfc-editor.org/rfc/rfc6582> · RFC 6675 (SACK 기반 손실 복구) <https://www.rfc-editor.org/rfc/rfc6675>
  - RFC 9438 (CUBIC) <https://www.rfc-editor.org/rfc/rfc9438> — §1 기본 채택 현황 · §4.2 W_cubic·K · §4.3 Reno-friendly · §4.6 β=0.7 · §4.8 타임아웃 · §3.3 RTT 공정성 · §5.1 C=0.4 · §4.10 HyStart++ 권고(SHOULD)
  - RFC 9406 (HyStart++) <https://www.rfc-editor.org/rfc/rfc9406>
  - draft-ietf-ccwg-bbr (BBR, Experimental 지향 인터넷 드래프트) <https://datatracker.ietf.org/doc/draft-ietf-ccwg-bbr/>
  - RFC 3168 (ECN) <https://www.rfc-editor.org/rfc/rfc3168> · RFC 8289 (CoDel) <https://www.rfc-editor.org/rfc/rfc8289> · RFC 8290 (FQ-CoDel) <https://www.rfc-editor.org/rfc/rfc8290>
- Linux
  - tcp(7) — `tcp_congestion_control`, `TCP_CONGESTION`, `tcp_slow_start_after_idle` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - 커널 문서 ip-sysctl — `tcp_congestion_control`(리스너 선택 상속), `tcp_slow_start_after_idle`(기본 1, RFC 2861 방식), `tcp_min_rtt_wlen` <https://docs.kernel.org/networking/ip-sysctl.html>
  - 커널 문서 sysctl/net — `default_qdisc`(기본 pfifo_fast) <https://docs.kernel.org/admin-guide/sysctl/net.html>
  - `net/ipv4/tcp_cong.c` `tcp_slow_start`(확인된 세그먼트 수만큼 증가) · `net/ipv4/tcp_output.c` `tcp_cwnd_restart`(유휴 RTO마다 절반)
  - `include/net/tcp.h` — `TCP_INIT_CWND 10` · `net/ipv4/Kconfig` — `DEFAULT_CUBIC`, `TCP_CONG_BBR`(fq 필요) <https://github.com/torvalds/linux>
  - ss(8) — `cwnd`, `ssthresh`, 알고리즘 이름 <https://man7.org/linux/man-pages/man8/ss.8.html>
- bufferbloat.net, "Introduction" <https://www.bufferbloat.net/projects/bloat/wiki/Introduction/>
- 교재
  - Kurose & Ross 8판 3.6(혼잡 제어 원리)·3.7(TCP 혼잡 제어)
  - Grigorik, 『High Performance Browser Networking』 "Building Blocks of TCP" — slow start, slow-start restart(SSR), IW10 <https://hpbn.co/building-blocks-of-tcp/>
