# network/18-tcp-congestion-control — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 혼잡 제어가 필요한 이유

- 수신 윈도는 **받는 호스트**의 여유만 말한다. 중간 병목 링크의 여유는 모른다.
- 여러 송신자가 각자 수신 윈도만큼 보내면 병목 라우터의 큐가 넘쳐 패킷이 버려진다.
- 버려진 패킷을 모두가 재전송하면 부하가 더 늘어난다. 망은 바쁜데 실제 전달량은 떨어진다(혼잡 붕괴).
- 그래서 송신자가 망 상태를 추정해 스스로 속도를 줄이는 장치가 필요하다. RFC 9293은 slow start·혼잡 회피·RTO 백오프를 필수로 정한다(MUST-19, §3.8.2).

### 2. cwnd, rwnd, ssthresh

- cwnd: 송신자가 스스로 정한, ACK 전에 망에 내보낼 수 있는 양의 상한. 헤더에 없고 송신 커널 안에만 있다.
- rwnd: 수신자가 헤더 Window 필드로 알린 남은 버퍼.
- ssthresh: slow start와 혼잡 회피를 가르는 문턱.
- 보낼 수 있는 양 = `min(cwnd, rwnd) − FlightSize`(RFC 5681 §3.1).

### 3. cwnd 시간 변화

```text
  cwnd
   ^                /|                       /|
   |    ssthresh - /-|------- /\ ----------- /-|
   |              /  |      /  (선형)       /  |
   |             /   |____/                    |
   |           /     ^ 3 dup ACK: 절반 부근     |  RTO: cwnd = 1 SMSS
   |      __ /                                 |___ 다시 slow start
   |  IW_/  (지수)
   +-------------------------------------------------> 시간
```

- slow start: RTT마다 약 두 배(세그먼트마다 ACK가 올 때).
- 혼잡 회피: RTT마다 약 1 SMSS.
- 중복 ACK 3개: ssthresh = max(FlightSize/2, 2·SMSS), fast recovery 뒤 cwnd = ssthresh.
- RTO: ssthresh를 같은 식으로 줄이고 cwnd = 1 SMSS, slow start부터(§3.1). 이미 타이머로 재전송한 세그먼트가 또 타임아웃이면 ssthresh는 유지한다.

### 4. slow start가 "slow"인 이유와 `min(N, SMSS)`

- 혼잡 제어 이전(Jacobson 1988 이전) 구현은 연결 시작부터 수신 윈도만큼 한꺼번에 보냈다(RFC 2001 §1 "Old TCPs would start a connection with the sender injecting multiple segments into the network, up to the window size advertised by the receiver"). 그에 비해 작은 초기 윈도에서 시작해 늘리니 "느린 시작"이다. 증가 속도 자체는 RTT마다 약 두 배인 지수다.
- `cwnd += min(N, SMSS)`(N = 새로 확인된 바이트)는 **ACK 분할** 공격을 막는다. 수신자가 한 세그먼트에 대해 ACK를 잘게 여러 번 보내면, ACK마다 SMSS씩 늘리는 송신자는 cwnd가 부당하게 커진다(RFC 5681 §3.1).

### 5. 중복 ACK 3개 vs RTO

- **ACK 클럭**: 수신자에 세그먼트가 도착할 때마다 ACK가 오고, 송신자는 그 ACK에 맞춰 새 세그먼트를 내보낸다. 망을 떠난 만큼만 들여보내는 자기 조절이다.
- 중복 ACK 3개: 유실된 것 뒤의 세그먼트들이 도착해 ACK가 계속 온다. 클럭은 살아 있다. 그래서 절반으로 줄이고 계속 보낸다(fast recovery, §3.2).
- RTO: 타이머가 끝날 때까지 새 데이터를 확인하는 ACK가 오지 않았다(중복 ACK는 타이머를 다시 시작시키지 않는다, RFC 6298 §5.3). 클럭이 끊겼고 망이 크게 막혔을 수 있다. 그래서 cwnd를 1 SMSS로 떨어뜨리고 slow start로 클럭을 다시 시작한다(§3.1).

### 6. 100KB 응답의 RTT 수

```text
  세그먼트 수 = ceil(100,000 / 1460) = 69
  RTT 1: 10   (누적 10)
  RTT 2: 20   (누적 30)
  RTT 3: 40   (누적 70 >= 69)   -> 3 RTT
```

- RTT 100ms면 전송에 약 300ms다(연결 수립·요청 시간은 별도). 유실 없는 이상적인 모델의 값이다.

### 7. 유휴 후 첫 응답이 느릴 때

- **원인**: RTO보다 오래 보내지 않으면 cwnd를 RW = min(IW, cwnd)로 줄인다(SHOULD, RFC 5681 §4.1). 리눅스 `tcp_slow_start_after_idle=1`(기본)이 이 역할이다. 리눅스는 RFC 2861 방식으로 유휴 RTO마다 cwnd를 절반으로 줄여 min(IW, cwnd)까지 내린다(ip-sysctl, `tcp_cwnd_restart`). 큰 응답이 다시 slow start를 거친다.
- **확인**
  - `sysctl net.ipv4.tcp_slow_start_after_idle`
  - 유휴 직후 `ss -ti`의 `cwnd`가 10 근처로 떨어졌는지
  - 캡처에서 RTT마다 두 배로 불어나는 송신 모양
- **대처**: 서버에서 `tcp_slow_start_after_idle=0`을 검토한다(HPBN 권고).
- **트레이드오프**: 유휴 중에 망 상황이 바뀌었어도 옛 cwnd만큼 한꺼번에 버스트를 보낸다. RFC 5681 §4.1이 경고하는 문제다.

### 8. CUBIC이 고BDP에서 유리한 이유

- Reno의 혼잡 회피는 RTT당 1 SMSS씩 늘린다. 윈도가 수천 세그먼트인 망에서 유실 한 번에 절반이 되면, 원래대로 돌아가는 데 수천 RTT가 걸린다(계산). RFC 9438 §1은 이 "고BDP에서 느린 cwnd 회복" 문제를 CUBIC의 설계 동기로 든다.
- CUBIC은 `W(t) = C·(t−K)^3 + W_max`로 **경과 시간**의 3차 함수다.
  - W_max(직전 유실 지점)에서 멀면 빠르게, 가까우면 천천히(오목), 넘어서면 다시 점점 빠르게(볼록) 키운다.
- 혼잡 사건(중복 ACK 등) 때 0.7배로 줄인다(β_cubic, SHOULD). Reno의 0.5배보다 덜 줄인다. RTO에서는 Reno처럼 cwnd를 1 SMSS로 줄이고 ssthresh만 β_cubic으로 정한다(§4.8).
- 증가가 RTT가 아닌 시간 기준이라, Reno-friendly 구간 밖에서는 RTT가 달라도 윈도 크기가 비슷해진다. 그래서 처리량 비가 손실 환경과 무관하게 RTT 비에 선형이다. Reno는 동기 손실 환경(모든 흐름이 동시에 유실)에서 RTT 비의 제곱으로 벌어지므로, 그때 CUBIC이 RTT 긴 흐름에 덜 불리하다. 비동기 손실에서는 Reno도 선형이다(RFC 9438 §3.3).

### 9. BBR의 신호와 상태

- 손실 기반(Reno, CUBIC)은 **유실**(ECN이면 표시)을 혼잡 신호로 쓴다. 큐가 버리거나 표시할 때까지 키운다(tail-drop 큐면 넘칠 때까지).
- BBR은 **전달률(병목 대역폭 max_bw)과 최소 RTT(min_rtt)**를 재서 경로 모델을 만든다. 목표 in-flight를 그 곱(BDP) 근처로 둔다.
- 상태: Startup(지수 증가로 대역폭 탐색) → Drain(쌓인 큐 빼기) → ProbeBW(주기적으로 더 보내 보며 대역폭 재탐색) ↔ ProbeRTT(잠깐 줄여 min_rtt 재측정).
- IETF 문서는 Experimental 지향의 인터넷 드래프트(draft-ietf-ccwg-bbr, BBRv3)다. RFC가 아니다.

### 10. 업로드 중 SSH가 끊길 때

- 이름: **bufferbloat**.
- 원인: 병목 장비(공유기·모뎀)의 큰 FIFO 큐를 업로드 흐름의 손실 기반 TCP가 가득 채웠다. SSH 패킷도 그 큐 뒤에서 수백 ms를 기다린다. 큐가 크니 유실은 거의 없다.
- 확인: 업로드 중 `ping` RTT가 평소의 수 배 이상이다. 업로드 흐름의 `ss -ti` `rtt`가 계속 커진다.
- 대처
  - 병목 장비에 AQM을 켠다. FQ-CoDel(RFC 8290)은 흐름별로 큐를 나누고 체류 시간을 기준으로 버린다.
  - ECN으로 버리는 대신 표시해 알린다(RFC 3168).
  - 업로드를 병목보다 약간 낮게 속도 제한해 큐가 병목 장비에 쌓이지 않게 한다.
  - 측정 후 BBR 같은 모델 기반 알고리즘을 검토한다.
