# network/03-latency-bandwidth-bdp — 지연 4요소, 대역폭과 지연, BDP — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

"네트워크가 느리다"에는 두 가지 전혀 다른 뜻이 섞여 있다.\
**한 번 왕복하는 데 오래 걸린다**(지연)와 **초당 조금밖에 못 보낸다**(대역폭·처리량)다.\
둘을 구분하지 못하면 엉뚱한 처방을 한다. 지연이 문제인데 회선을 늘리는 식이다.

```text
  지연(latency)   = 첫 비트가 도착하기까지 걸리는 시간      "도로의 길이"
  대역폭(bandwidth) = 초당 밀어 넣을 수 있는 비트 수         "도로의 차선 수"
  처리량(throughput) = 실제로 초당 전달된 데이터 양          "실제로 지나간 차"
```

쉬운 예: 서울에서 부산까지 이삿짐을 옮긴다.\
트럭을 10대로 늘리면(대역폭) 한 번에 많이 옮긴다.\
그래도 한 번 다녀오는 시간(지연)은 그대로다.\
"확인 도장을 받아야 다음 트럭을 보낸다"는 규칙이 있으면, 트럭이 많아도 도장 왕복 시간 때문에 느리다.

똑같은 구조다.\
TCP는 받았다는 확인(ACK)이 와야 더 보낼 수 있다.\
그래서 먼 거리에서는 대역폭이 남아도 **확인 없이 보낼 수 있는 양(윈도)**이 처리량을 막는다.

실무 예:
- 서울–미국 동부 간 DB 복제가 회선 속도의 일부밖에 안 나온다. 회선을 늘려도 그대로다.
- 대용량 업로드를 하는 동안 같은 망의 화상회의·SSH가 끊길 듯 느려진다. 대역폭 부족이 아니라 공유기 큐가 꽉 찬 탓이다(bufferbloat).
- API 한 번에 DB 쿼리를 20번 순차로 부른다. 같은 리전에선 괜찮다. 리전을 건너면 20 × RTT가 그대로 응답 시간이 된다.

## 동작·원리

### 지연 4요소 — 한 홉을 지날 때

```text
  패킷 도착                                                          다음 라우터 도착
     |                                                                     |
     v                                                                     v
  [처리] --> [큐에서 대기] --> [링크에 비트 밀어 넣기] --> [선로 위를 이동] -->
  d_proc      d_queue           d_trans = L / R            d_prop = 거리 / 전파 속도

  d_nodal = d_proc + d_queue + d_trans + d_prop                (K&R 1.4.1)
```

- **처리 지연(d_proc)**: 헤더를 보고, 비트 오류를 검사하고, 어디로 보낼지 정하는 시간.
- **큐잉 지연(d_queue)**: 출력 링크가 바빠서 큐에서 기다리는 시간. 그때그때 트래픽에 따라 0에서 매우 크게까지 변한다.
- **전송 지연(d_trans)**: 패킷의 모든 비트를 링크에 밀어 넣는 시간. 패킷 길이 L ÷ 링크 속도 R.
- **전파 지연(d_prop)**: 비트 하나가 선로를 따라 이동하는 시간. 거리 ÷ 전파 속도.
- HPBN도 같은 넷(propagation·transmission·processing·queuing)으로 나눈다.

  - *전송 지연 vs 전파 지연*: 전송은 "문을 빠져나가는 시간"(패킷 크기·링크 속도에 비례), 전파는 "도로를 달리는 시간"(거리에 비례). 둘은 서로 관계가 없다.

숫자로 감을 잡는다(직접 계산한 값).

```text
  전송 지연 (1500바이트 = 12,000비트)
    100 Mbps   ->  12,000 / 100,000,000  = 120 µs
    1 Gbps     ->  12 µs
    10 Gbps    ->  1.2 µs

  전파 지연 (광섬유 속 빛 ~200,000 km/s, HPBN)
    200 km     ->  1 ms (편도)
    뉴욕-런던 5,585 km -> 편도 28 ms, 왕복 56 ms  (HPBN 표 1-1)
```

- 링크를 빠르게 하면 전송 지연은 줄어든다. 그러나 **전파 지연은 물리 한계**라 줄지 않는다.
  - 광섬유의 굴절률이 약 1.5라서 빛이 진공보다 느리다(HPBN).
  - 실제 RTT는 이 최솟값보다 크다. 케이블이 직선이 아니고, 홉마다 처리·큐잉이 더해지기 때문이다.

### 큐잉 지연 — 이용률이 1에 가까우면 폭증한다

```text
  큐잉 지연
    ^
    |                                  |
    |                                 /
    |                               _/
    |                            __/
    |                      ___--
    |  _______-------------
    +------------------------------------->  트래픽 강도 La/R
    0                                  1
```

- *트래픽 강도(traffic intensity)*: La/R. a는 초당 도착하는 패킷 수, L은 패킷 크기(비트), R은 링크 속도다. "들어오는 비트 속도 ÷ 나갈 수 있는 비트 속도"다(K&R 1.4.2).
  - La/R > 1이면 들어오는 속도가 나가는 속도보다 빠르다. 큐가 끝없이 자란다.
  - La/R ≤ 1이어도 1에 가까워질수록 평균 큐잉 지연이 급격히 커진다.
- 큐가 유한하면 꽉 찼을 때 새 패킷을 버린다. 이게 **패킷 손실**이다.
- 같은 수학이 서버의 스레드 풀·커넥션 풀에도 적용된다(대기 행렬 이론 — [queueing·Little's law](../../systems/server-design/01-scaling-principles.md)).

### 처리량 — 경로에서 가장 좁은 곳

```text
  서버 --(1 Gbps)-- 라우터 --(100 Mbps)-- 라우터 --(1 Gbps)-- 클라이언트
                               ^
                          병목 링크: 처리량 ≤ 100 Mbps
```

- 종단 간 처리량은 경로 위 링크 속도 중 **최솟값(병목)**을 넘지 못한다(K&R 1.4.4).
- 병목 링크는 다른 흐름과 나눠 쓰니 실제로는 더 적다.

### BDP — "선로 위에 떠 있을 수 있는 양"

```text
       <------------------ RTT 동안 ------------------>
  송신 [][][][][][][][][][][][][][][][][][][][][][][][]  --->  수신
       |<---- 대역폭 × RTT 만큼 보내야 선로가 꽉 찬다 ---->|
                            = BDP
```

  - *BDP(Bandwidth-Delay Product)*: 병목 대역폭 × RTT. ACK를 기다리지 않고 "보내 놓은 채(in flight)" 있어야 하는 데이터 양이다.
  - *RTT(Round-Trip Time)*: 보낸 세그먼트에 대한 ACK가 돌아오기까지의 왕복 시간.

TCP 송신자는 한 RTT 동안 최대 **윈도**만큼만 보낼 수 있다.

```text
  처리량 ≤ 윈도 / RTT

  예시) RTT 100 ms, 링크 1 Gbps
    BDP = 1,000,000,000 bit/s × 0.1 s = 100,000,000 bit = 12.5 MB
    윈도가 64 KiB(65,535바이트)면
      처리량 ≤ 65,535 × 8 / 0.1 ≈ 5.2 Mbps          <- 1 Gbps 회선의 0.5%
```

- 윈도는 수신 윈도(수신 버퍼 여유, 17번)와 혼잡 윈도(18번) 중 작은 쪽이다.
- TCP 헤더의 윈도 필드는 16비트다. 그래서 확장 없이는 최대 64 KiB다(RFC 7323).
  - *window scaling*: SYN에 실어 보내는 옵션으로 윈도 값을 2^n배로 해석하게 한다. n은 최대 14이고, 윈도는 최대 1 GiB가 된다(RFC 7323).
  - 이 옵션은 SYN 세그먼트에서만 교환한다(RFC 7323). 그래서 연결 도중에는 켤 수 없다.
- BDP가 아주 큰 경로를 가진 망을 *LFN(Long Fat Network)*이라 부른다(RFC 7323 §1.1).

### 대역폭보다 지연이 문제인 경우가 많다

- 작은 요청을 많이 주고받는 웹 트래픽은 대부분 RTT에 묶인다.
- HPBN은 "대부분의 웹사이트에서 성능 병목은 대역폭이 아니라 지연"이라고 적는다.
- 이유
  - 연결 수립(TCP 1 RTT, TLS 1~2 RTT)부터 RTT 단위로 비용이 든다.
  - 혼잡 윈도는 작게 시작해서 RTT마다 커진다(18번). 짧은 전송은 창이 다 커지기 전에 끝난다.
  - 응용이 순차로 여러 번 왕복하면 그 수만큼 RTT가 곱해진다.

### bufferbloat — 큐가 너무 커서 생기는 지연

```text
  업로드 폭주 전:  [ ]                               큐 비어 있음, ping 20 ms (예시)
  업로드 폭주 중:  [#][#][#][#][#][#][#][#][#][#]... 큐 가득, ping 수백 ms (예시)
                  ^ 모든 패킷이 이 줄 끝에서 기다린다
```

- 망의 버퍼는 **순간적인 몰림(burst)을 흡수**하려고 둔다(RFC 7567).
- 그런데 큐가 꽉 찼을 때만 버리는(tail drop) 방식이면, 큐가 오랫동안 거의 가득 찬 채로 남을 수 있다(RFC 7567).
  - 손실 기반 혼잡 제어(Reno·CUBIC)는 손실(또는 ECN 표시)이 올 때까지 보내는 양을 늘린다. 그래서 큰 버퍼를 채울 때까지 늘린다.
  - CUBIC은 리눅스·Windows·Apple 스택의 기본 혼잡 제어다(RFC 9438 §1). BBR 같은 모델 기반 방식은 큐를 덜 채운다(18번).
  - 그 뒤로 지나가는 모든 패킷이 가득 찬 큐를 기다린다.
- 이렇게 큐가 커서 지연이 늘어나는 현상을 *bufferbloat*라 부른다.
- 처방은 **AQM(능동 큐 관리)**이다.
  - RFC 7567: 망 장비는 AQM을 구현해야 한다(SHOULD).
  - CoDel·FQ-CoDel은 큐에 머문 시간을 기준으로 일찍 버린다. FQ-CoDel의 기본값은 target 5 ms, interval 100 ms다(RFC 8290).
  - *AQM(Active Queue Management)*: 큐가 가득 차기 전에 미리 패킷을 버리거나 표시해서 송신자에게 속도를 줄이라고 알리는 방식.

## 쓰이는 자료구조·알고리즘

- **큐(FIFO)** — 라우터·NIC·소켓 버퍼 어디든 "나가기를 기다리는 줄"이 있다. 큐잉 지연은 이 큐의 길이 ÷ 나가는 속도다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md) 참고.
- **대기 행렬 이론(Little's law, L = λW)** — 평균 큐 길이 = 도착률 × 평균 대기 시간. 이용률이 1에 가까우면 대기 시간이 비선형으로 커진다. [systems/server-design/01-scaling-principles](../../systems/server-design/01-scaling-principles.md)(Little's law 절) 참고.
- **EWMA(지수 가중 이동 평균)** — TCP는 RTT를 표본마다 `SRTT ← (1 − 1/8)·SRTT + 1/8·R'`로 부드럽게 추정한다(RFC 6298 §2). `ss -ti`의 `rtt:` 값이 이 평균과 편차다(ss(8)).
- **슬라이딩 윈도** — "ACK 없이 보낼 수 있는 양"이 윈도다. 처리량 ≤ 윈도 / RTT의 윈도가 이것이다(16·17번).
- **공정 큐잉(FQ)의 해시** — FQ-CoDel은 흐름마다 큐를 두고, 흐름을 해시로 큐에 배정한다(RFC 8290).

## 적용 — 풀어나가는 법

### 1. 지연과 처리량을 따로 잰다

```bash
# 지연: 최소 RTT가 곧 전파+처리의 하한. 편차가 크면 큐잉
ping -c 20 db.us-east.example.com

# 경로의 홉별 지연·손실
mtr -rwc 50 db.us-east.example.com

# 처리량: 서버에서 iperf3 -s, 클라이언트에서
iperf3 -c db.us-east.example.com -t 10          # 클라이언트 -> 서버
iperf3 -c db.us-east.example.com -t 10 -R       # 서버 -> 클라이언트 (-R 역방향)
```

- iperf3의 `-w`는 양쪽 소켓 버퍼(=윈도) 크기를 정한다. 값을 바꿔 가며 처리량이 윈도에 묶였는지 확인할 수 있다(iperf3 문서).

### 2. 연결 하나의 상태를 본다

```bash
ss -tin dst 203.0.113.10
#  ... rtt:98.4/1.2 ... cwnd:10 ... send 1.2Mbps ... rcv_space:...      (출력 모양 예시)
```

- `rtt:<rtt>/<rttvar>`는 평균 RTT와 편차(ms)다. `cwnd`는 혼잡 윈도, `send`는 송신 속도 추정이다(ss(8)).
- `send`가 회선 속도보다 훨씬 작고 RTT가 크면, BDP에 비해 윈도가 작은지 의심한다.

### 3. BDP로 버퍼 크기를 계산한다

```js
// 필요한 윈도(= 버퍼) 크기 추정
function bdpBytes(bandwidthBps, rttMs) {
  return Math.ceil((bandwidthBps * (rttMs / 1000)) / 8);
}
bdpBytes(1e9, 100);   // 12,500,000 바이트 ≈ 12.5 MB (예시: 1 Gbps, 100 ms)
bdpBytes(1e9, 1);     // 125,000 바이트 ≈ 125 KB  (예시: 같은 리전, 1 ms)
```

- 리눅스는 기본으로 수신 버퍼를 자동 조절한다(`tcp_moderate_rcvbuf`, 기본 켜짐). 상한은 `tcp_rmem`의 세 번째 값이다(ip-sysctl).
  - `tcp_rmem` 최대 기본값은 메모리 크기에 따라 131072바이트~32MB 사이다(Linux 6.16부터. 6.15까지는 131072바이트~6MB, ip-sysctl).
  - 송신 쪽 `tcp_wmem` 최대 기본값은 64K~4MB 사이다(ip-sysctl).
- 앱이 `SO_RCVBUF`를 직접 설정하면 그 소켓의 자동 조절이 **꺼진다**(ip-sysctl `tcp_rmem`). 작은 값을 박아 두면 고BDP 경로에서 처리량이 묶인다.
- 64 KiB보다 큰 윈도가 필요하면 버퍼 크기를 **연결 전에** 정해야 한다. window scale이 SYN에서 정해지기 때문이다.

```java
Socket s = new Socket();
s.setReceiveBufferSize(16 * 1024 * 1024);   // 16MB(예시). 반드시 connect 전에
s.connect(new InetSocketAddress(host, port), 3_000);
// 서버 쪽은 ServerSocket.setReceiveBufferSize()를 bind 전에 불러야 accept된 소켓에 적용된다
```

- Javadoc: 64K보다 큰 수신 윈도가 필요하면 연결 전에 요청해야 한다. 클라이언트 소켓은 connect 전, 서버는 `ServerSocket`을 bind 하기 전에 설정한다.
- 커널 상한 `net.core.rmem_max`를 넘는 값은 잘린다(socket(7), kernel sysctl net 문서).
  - 기본값은 Linux 6.18부터 4194304(4MB)다.
  - 6.17까지는 `SK_RMEM_MAX`(256 × `SKB_TRUESIZE(256)`, 플랫폼마다 다름)로 훨씬 작았다. x86_64에서 흔히 212992바이트다 [?].
  - 그래서 구 커널 기본 설정에서는 위 16MB 요청이 약 200KB로 잘린다. 운영 커널에서 `sysctl net.core.rmem_max net.ipv4.tcp_rmem`으로 실제 값을 확인한다.
- 대부분은 **직접 설정하지 않고 자동 조절에 맡기는 편이 낫다**. 직접 설정하면 자동 조절이 꺼지기 때문이다.

### 4. 왕복 수를 줄인다

- 지연이 병목이면 대역폭을 늘려도 소용없다. **왕복 횟수**를 줄인다.
  - 순차 쿼리를 배치·조인으로 합친다.
  - 연결을 재사용한다(연결 수립 RTT 제거, 35번).
  - 데이터를 사용자 가까이 둔다(CDN, 리전 복제).

## 장애 시나리오와 대처

### 1. 고BDP(대륙 간) 링크에서 윈도 부족 — 대역폭을 놔두고 느리다

- **현상**: 서울–미국 동부 복제·백업 전송이 1 Gbps 회선에서 수십 Mbps밖에 안 나온다. 회선을 늘려도 그대로다.
- **보이는 형태**
  - `iperf3` 단일 스트림은 느린데, `-P 8`(병렬)로는 훨씬 빠르다.
  - `ss -ti`에 RTT가 크고(예: 150 ms, 예시), `send` 속도가 윈도/RTT 계산값과 맞는다.
- **원인**: 처리량 ≤ 윈도 / RTT다. 윈도가 BDP보다 작다.
  - 앱이 `SO_RCVBUF`를 작게 고정해 자동 조절이 꺼졌다.
  - `tcp_rmem`·`rmem_max` 상한이 작다.
  - 중간 장비가 window scale 옵션을 지워 윈도가 64 KiB에 묶였다.
- **대처**
  - `SO_RCVBUF` 고정을 없애 자동 조절에 맡기거나, BDP 이상으로 연결 전에 설정한다.
  - `tcp_rmem`/`tcp_wmem`의 최대값을 BDP 이상으로 올린다.
  - SYN 패킷을 캡처해 `wscale` 옵션이 양쪽에 있는지 확인한다.
  - 손실이 있는 경로라면 혼잡 제어도 병목이 된다(18번).

### 2. bufferbloat — 부하가 걸리면 지연이 수백 ms로 뛴다

- **현상**: 대용량 업로드·백업 중 같은 망의 SSH·화상회의·API 호출 지연이 급증한다. 업로드가 끝나면 정상이다.
- **보이는 형태**
  - 부하 없을 때 `ping` 20 ms(예시) → 부하 중 수백 ms(예시). 손실은 거의 없다.
  - `tc -s qdisc show dev eth0`에 backlog(큐에 쌓인 바이트)가 크게 보인다.
- **원인**: 병목 장비(공유기·게이트웨이·NIC 큐)의 버퍼가 크고 tail drop 방식이다. 대량 전송 TCP가 버퍼를 가득 채우고, 모든 패킷이 그 줄 뒤에서 기다린다(RFC 7567).
- **대처**
  - 병목 지점에 AQM(FQ-CoDel 등)을 켠다. 예: `tc qdisc replace dev eth0 root fq_codel`.
  - 리눅스 `net.core.default_qdisc`의 커널 기본값은 `pfifo_fast`다(kernel sysctl net 문서). 배포판이 다른 값으로 바꿔 두기도 하니 실제 값을 확인한다.
  - 업로드 속도를 병목보다 약간 낮게 제한(shaping)하면 큐가 병목 장비가 아닌 내 쪽(제어 가능한 곳)에 생긴다.

### 3. 회선을 늘렸는데 응답 시간이 그대로다 — 지연 지배 워크로드

- **현상**: 대역폭을 10배로 늘렸는데 API p50 응답 시간이 거의 안 줄었다.
- **보이는 형태**: 요청·응답이 작다(수 KB). 트레이스에 원격 호출이 순차로 여러 번 있다.
- **원인**: 작은 전송은 전송 지연이 아니라 RTT(전파·연결 수립·왕복 횟수)가 지배한다. HPBN이 말하는 "지연이 병목"인 경우다.
- **대처**: 왕복 수를 줄인다. 배치 호출, 연결 재사용(keep-alive, HTTP/2), 데이터 지역화(같은 리전·CDN)를 쓴다.

### 4. 이용률이 높아지자 지연이 갑자기 튄다

- **현상**: 링크 이용률 60%일 때는 멀쩡하다. 90%를 넘자 p99 지연과 손실이 급증한다.
- **보이는 형태**: 인터페이스 이용률 그래프와 지연 그래프가 비선형으로 함께 뛴다. 인터페이스 드롭 카운터가 오른다.
- **원인**: 트래픽 강도 La/R이 1에 가까워지면 큐잉 지연이 급격히 커진다(K&R 1.4.2). 큐가 차면 손실까지 난다.
- **대처**: 용량 계획에서 이용률 상한에 여유를 둔다. 평균이 아니라 버스트 기준으로 본다. 링크 증설이나 트래픽 분산을 한다.

## 핵심 문장

- 한 홉의 지연은 처리 + 큐잉 + 전송(L/R) + 전파(거리/속도)다. 전송 지연은 링크를 빠르게 하면 줄지만, 전파 지연은 물리 한계다.
- 처리량은 경로의 병목 링크를 넘지 못하고, TCP에서는 "윈도 / RTT"도 넘지 못한다.
- BDP = 대역폭 × RTT는 선로를 꽉 채우려면 확인 없이 떠 있어야 하는 양이다. 윈도가 BDP보다 작으면 회선이 남는다.
- 트래픽 강도가 1에 가까워지면 큐잉 지연이 급증한다. 버퍼가 크고 tail drop이면 큐가 계속 가득 차서 bufferbloat가 된다.
- 작은 요청이 많은 워크로드에서 병목은 대역폭이 아니라 왕복 횟수 × RTT인 경우가 많다.

## 관련 주제·근거

- 선행: [02-encapsulation](../02-encapsulation/2-summary.md) — 헤더가 붙은 프레임 크기(전송 지연의 L)
- 후속·연결
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — RTT 추정(EWMA)과 RTO.
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — 수신 윈도·window scaling.
  - [18-tcp-congestion-control](../18-tcp-congestion-control/2-summary.md) — 혼잡 윈도·손실 기반 vs 지연 기반.
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 연결 재사용으로 RTT 줄이기.
  - [systems/server-design/01-scaling-principles](../../systems/server-design/01-scaling-principles.md) — Little's law, 이용률과 대기 시간
  - [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md) — 큐
- 교재·문서
  - Kurose & Ross 8판 1.4 "Delay, Loss, and Throughput in Packet-Switched Networks"(1.4.1 지연 4요소, 1.4.2 트래픽 강도, 1.4.4 처리량·병목)
  - Grigorik, HPBN "Primer on Latency and Bandwidth" — 지연 4요소, 광섬유 굴절률 ~1.5, 표 1-1(뉴욕–런던 RTT 56 ms), bufferbloat·CoDel <https://hpbn.co/primer-on-latency-and-bandwidth/>
- RFC
  - RFC 7323 — 16비트 윈도(64 KiB), window scale 최대 14(1 GiB, §2.3), SYN에서만 교환(§2.1), LFN(§1.1) <https://www.rfc-editor.org/rfc/rfc7323>
  - RFC 6298 §2 — SRTT/RTTVAR EWMA(α=1/8, β=1/4) <https://www.rfc-editor.org/rfc/rfc6298>
  - RFC 7567 — 버퍼는 버스트 흡수용, tail drop의 문제, AQM SHOULD <https://www.rfc-editor.org/rfc/rfc7567>
  - RFC 8290 — FQ-CoDel, target 5 ms, interval 100 ms <https://www.rfc-editor.org/rfc/rfc8290>
- Linux 문서
  - ip-sysctl `tcp_rmem`·`tcp_wmem`(SO_RCVBUF/SO_SNDBUF 설정 시 자동 조절 꺼짐)·`tcp_moderate_rcvbuf`·`tcp_window_scaling` <https://docs.kernel.org/networking/ip-sysctl.html>
    - `tcp_rmem` 최대 기본값: v6.15 문서 "between 131072 and 6MB", v6.16 문서 "between 131072 and 32MB"
  - sysctl net — `rmem_max`(v6.18 문서부터 "Default: 4194304"), `default_qdisc`(pfifo_fast) <https://docs.kernel.org/admin-guide/sysctl/net.html>
  - Linux 소스 `net/core/sock.c` — v6.18 `sysctl_rmem_max = 4 << 20`, v6.17 `= SK_RMEM_MAX`(`include/net/sock.h`)
- RFC 9438 §1 — CUBIC이 리눅스·Windows·Apple의 기본 혼잡 제어 <https://www.rfc-editor.org/rfc/rfc9438>
  - socket(7) `SO_RCVBUF`(커널이 2배로 잡음) · tcp(7) 버퍼는 listen/connect 전에 설정 <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - ss(8) `-i`의 `rtt`, `cwnd`, `send` <https://man7.org/linux/man-pages/man8/ss.8.html>
- iperf3 옵션 `-c`, `-t`, `-R`, `-w`, `-P` <https://software.es.net/iperf/invoking.html>
- Java `Socket.setReceiveBufferSize` Javadoc — 64K 초과 윈도는 connect 전 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/Socket.html>
