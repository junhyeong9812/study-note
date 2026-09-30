# network/25-kernel-network-stack — 패킷이 NIC와 소켓 버퍼 사이를 오가는 길 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

앱은 `send()`·`recv()`만 부른다.\
그 아래에서 커널은 바이트를 패킷으로 만들고, NIC에 넘기고, 도착한 패킷을 다시 소켓까지 올린다.\
이 경로에는 **큐가 여러 개** 있다.\
아래쪽 큐(NIC 링, CPU 백로그, qdisc)가 넘치면 패킷이 버려진다.\
그런데 앱에는 에러가 바로 안 뜬다. TCP가 재전송으로 메우면 "조금 느려질" 뿐이다.\
(재전송이 끝내 실패하면 연결 타임아웃 에러가 된다. 소켓 송신 버퍼가 차면 버리지 않고 `send()`가 기다리거나, 논블로킹이면 `EAGAIN`을 돌려준다 — send(2).)

```text
  앱이 보는 것:    send() 성공 ........ 응답이 가끔 느림 (원인 모름)
  실제로는:        NIC 링 가득 -> 패킷 버림 -> TCP가 재전송 -> 재전송만큼 지연 (빠른 재전송 또는 RTO)
```

쉬운 예: 물류 센터다.\
트럭(NIC)이 상자를 하역장 선반(링 버퍼)에 내려놓는다.\
직원(CPU)이 선반에서 상자를 꺼내 분류(IP·TCP 처리)해서 각 집 우편함(소켓 버퍼)에 넣는다.\
선반이 가득 차면 트럭은 남은 상자를 **그냥 버리고** 떠난다.\
직원이 한 명만 일하면 다른 직원이 놀아도 선반은 넘친다.

똑같은 구조다.\
NIC 링 버퍼가 차면 NIC가 버리고, 한 CPU 코어만 수신 처리를 하면 그 코어가 병목이 된다.

실무 예:
- 트래픽이 몰리는 순간 p99 지연이 튄다. 앱 로그는 깨끗하다. `ip -s link`의 드롭 카운터만 오른다.
- 서버 CPU 사용률은 30%인데 코어 하나만 `%soft` 100%다.
- `tcpdump`에서는 패킷이 보였는데 앱은 못 받았다. 캡처 지점과 드롭 지점이 다르다.

## 동작·원리

### 전체 지도

```text
      송신 (위 -> 아래)                                 수신 (아래 -> 위)
  +--------------------------+                  +--------------------------+
  | 앱: send()/write()       |                  | 앱: recv()/read()        |
  +------------|-------------+                  +------------^-------------+
  | 소켓 송신 버퍼            |                  | 소켓 수신 버퍼            |
  | TCP (세그먼트, 재전송)     |                  | TCP (순서 맞춤, ACK)      |
  | IP (라우팅, 이웃/ARP)      |                  | IP (+ netfilter)         |
  |            v             |                  | 프로토콜 분기             |
  | qdisc (송신 큐 정책)       |                  | [tcpdump 수신 탭]         |
  | [tcpdump 송신 탭]          |                  | GRO / RPS 백로그          |
  | 드라이버 xmit             |                  | NAPI poll (softirq)       |
  +------------|-------------+                  +------------^-------------+
  | TX 링 (DMA 매핑)          |                  | RX 링 (DMA로 채워짐) + IRQ |
  +------------v-------------+                  +------------|-------------+
               NIC  =============== 선 ===============   NIC
```

- 위 그림은 packagecloud 블로그의 수신·송신 개요(리눅스 3.13 기준)를 옮긴 것이다. 함수 이름·세부 순서는 커널 버전마다 다르다.

### 수신 경로 — NIC에서 소켓 버퍼까지

```text
  (1) 패킷 도착
  (2) NIC가 DMA로 RX 링 버퍼(커널 메모리)에 복사
  (3) NIC가 하드웨어 인터럽트(IRQ)
  (4) 드라이버가 NAPI poll을 예약하고 IRQ를 잠시 끔
  (5) softirq(NET_RX)에서 poll: 링에서 패킷을 꺼내 sk_buff로 만든다 (budget만큼)
  (6) GRO로 비슷한 패킷을 합침, RPS면 다른 CPU 백로그로 넘김
  (7) 패킷 탭(tcpdump) -> IP(netfilter) -> TCP/UDP
  (8) 소켓 수신 버퍼에 넣고 recv() 대기 중인 앱을 깨움
```

- **(2) DMA와 RX 링**
  - *DMA(Direct Memory Access)*: CPU를 거치지 않고 장치가 메모리에 직접 읽고 쓰는 방식이다.
  - *RX 링 버퍼*: 고정 개수의 "디스크립터" 칸을 원형으로 돌려 쓰는 배열이다. 칸마다 패킷을 담을 메모리 주소가 적혀 있다.
  - 링 크기는 `ethtool -g`로 보고 `ethtool -G`로 바꾼다. 대부분의 드라이버는 바꿀 때 인터페이스를 내렸다 올린다(packagecloud).
- **(3)~(5) IRQ → NAPI → softirq**
  - 패킷마다 인터럽트를 받으면 CPU가 인터럽트 처리만 하다 끝난다.
  - 그래서 첫 인터럽트에서 **폴링 모드로 바꾼다**. 드라이버는 NAPI를 예약하고, 폴링이 끝날 때까지 인터럽트를 가려 두라고 권고된다(kernel docs NAPI "Scheduling and IRQ masking" — "Drivers should keep the interrupts masked").
  - *NAPI*: 리눅스 네트워크 스택의 이벤트 처리 방식이다. "인터럽트로 깨어나 → 폴링으로 몰아서 처리"한다.
  - *softirq*: 하드웨어 인터럽트 처리에서 미룬 일을 나중에 실행하는 커널 메커니즘이다. CPU마다 `ksoftirqd/N` 스레드가 있다.
  - NAPI poll은 보통 softirq 문맥에서 돈다. threaded NAPI를 켜면 전용 커널 스레드에서, busy polling이면 앱 프로세스가 직접 패킷을 확인할 수도 있다(kernel docs NAPI).
  - 한 번의 poll은 **budget**(RX 패킷 수) 안에서만 처리한다. TX 완료 처리는 이 개수 제한을 받지 않는다(kernel docs NAPI).
  - softirq 한 주기(여러 poll)에는 총량·시간 한도가 따로 있다.
    - `net.core.netdev_budget`: 한 폴링 주기에서 모든 인터페이스를 합쳐 처리할 최대 패킷 수(kernel docs sysctl/net). 리눅스 3.13 기본값은 300이다(packagecloud).
    - `net.core.netdev_budget_usecs`: 한 주기의 최대 시간(µs).
    - 일이 남았는데 budget·시간이 다 되면 `/proc/net/softnet_stat`의 `time_squeeze`가 오른다.
- **(6) GRO·RPS**
  - *GRO(Generic Receive Offload)*: 같은 흐름의 연속 패킷을 하나의 큰 패킷으로 합쳐 위로 올린다. 처리 횟수가 준다.
    - tcpdump에서 MTU보다 큰 수신 패킷이 보이는 이유다(packagecloud).
  - *RPS(Receive Packet Steering)*: RSS의 소프트웨어판이다. 흐름 해시로 처리할 CPU를 고르고, 그 CPU의 백로그 큐에 넣는다(kernel docs scaling).
    - 백로그 큐 길이 상한이 `net.core.netdev_max_backlog`다. 넘으면 버리고 `softnet_stat`의 `dropped`를 올린다.
- **(7) 패킷 탭 위치**
  - tcpdump(libpcap, `AF_PACKET`)는 `__netif_receive_skb_core`에서 패킷을 받는다. **IP·netfilter보다 앞**이다(packagecloud).
  - 그래서 iptables가 DROP한 패킷도 tcpdump에는 보인다.

### RSS — 수신을 여러 CPU로 나누기

```text
               패킷 4-튜플 (src IP, dst IP, src port, dst port)
                              |
                         해시 (보통 Toeplitz)
                              |
                    하위 비트로 간접 테이블 조회
                              v
        +-------+-------+-------+-------+-------+-------+
        | q0    | q1    | q2    | q3    | q0    | q1    |  ... (indirection table)
        +-------+-------+-------+-------+-------+-------+
            |       |       |       |
         RX 큐0  RX 큐1  RX 큐2  RX 큐3  --(큐마다 IRQ)-->  CPU0 CPU1 CPU2 CPU3
```

- *RSS(Receive Side Scaling)*: 멀티 큐 NIC가 패킷 헤더의 해시로 수신 큐를 고르는 기능이다(kernel docs scaling).
  - 큐마다 IRQ가 따로 있다. IRQ를 어느 CPU가 처리할지는 IRQ affinity로 정한다.
  - `irqbalance` 데몬이 수동 설정을 덮어쓸 수 있다(kernel docs scaling).
- 같은 흐름(4-튜플)은 늘 같은 큐로 간다. 그래서 패킷 순서가 흐름 안에서 유지된다.
- 뒤집어 말하면 **흐름 하나의 수신 처리 단계는 코어 하나를 넘지 못한다**(RPS를 켜면 IRQ·드라이버 CPU와 프로토콜 처리 CPU는 달라질 수 있다). 거대한 단일 연결은 RSS로 나뉘지 않는다. 단일 터널도 NIC가 바깥 헤더로만 해시하면 한 큐로 쏠린다(안쪽 헤더 해시 지원은 NIC마다 다르다).
- 간접 테이블은 `ethtool -x`로 보고 `ethtool -X`로 바꾼다.

### 송신 경로 — 소켓에서 NIC까지

```text
  (1) send(): 사용자 데이터를 소켓 송신 버퍼(sk_buff)로
  (2) TCP: 세그먼트 구성, 혼잡·흐름 제어 창 안에서 내보냄. 재전송용으로 보관
  (3) IP: 라우팅 조회, 이웃(ARP) 캐시로 다음 홉 MAC 결정
  (4) 송신 큐 선택 (XPS 또는 해시)
  (5) qdisc에 넣음 -> 바로 보내거나 NET_TX softirq에서 보냄
  (6) 패킷 탭(tcpdump) -> 드라이버 ndo_start_xmit
  (7) 드라이버가 DMA 매핑, TX 링에 디스크립터 등록, NIC에 알림
  (8) NIC가 메모리에서 읽어 전송 -> 완료 인터럽트 -> NAPI poll에서 버퍼 해제
```

- *qdisc(queueing discipline)*: 장치 앞의 송신 큐와 그 스케줄링 정책이다.
  - 단일 송신 큐 장치의 기본은 `pfifo_fast`, 멀티 큐 장치는 `mq`다(packagecloud, 3.13 기준). `net.core.default_qdisc`로 기본값을 바꿀 수 있다. 다만 물리 멀티 큐 장치는 루트가 여전히 `mq`이고, 바뀌는 것은 그 아래 큐별 qdisc다(kernel docs sysctl/net).
  - 큐 길이는 장치의 `txqueuelen`과 관계가 있다. 이더넷 기본값은 1000이다(packagecloud).
  - `tc -s qdisc show dev eth0`의 `dropped`·`overlimits`·`requeues`로 송신 쪽 드롭을 본다.
- 송신 쪽 tcpdump 탭은 qdisc를 **지난 뒤**, 드라이버 직전이다(packagecloud `dev_hard_start_xmit`). qdisc에서 버려진 패킷은 tcpdump에 안 나온다.
- 이웃 캐시에 MAC이 없으면 ARP가 먼저 나간다. 해석 대기 중인 패킷이 한도를 넘으면 버린다. 리눅스 3.3부터 한도는 바이트 단위 `unres_qlen_bytes`다. 옛 `unres_qlen`(패킷 수)은 deprecated다(kernel docs ip-sysctl).

### 드롭 카운터 지도 — 어디서 버려졌나

```text
  위치               카운터                                          명령
  NIC 링(버퍼 없음)   rx_missed_errors (/proc/net/dev에선 drop에 합산)  ip -s link, ethtool -S
  NIC/드라이버 기타   rx_dropped, 드라이버별 rx_fifo_errors 등          ethtool -S
  CPU 백로그          softnet_stat dropped                            /proc/net/softnet_stat
  softirq 시간 부족   softnet_stat time_squeeze (드롭 아님, 밀림)        /proc/net/softnet_stat
  qdisc(송신)         dropped                                        tc -s qdisc
  netfilter           규칙별 카운터                                   iptables -vnL / nft list ruleset
  소켓 수신 버퍼       프로토콜 통계(예: UDP RcvbufErrors)              nstat, netstat -s
```

- 커널 `if_link.h` 주석 기준
  - `rx_missed_errors`: 장치가 **버퍼 공간 부족**으로 버린 패킷이다. 호스트가 수신 속도를 못 따라간다는 뜻이다. `/proc/net/dev`에서는 "drop" 칸에 합쳐 보인다.
  - `rx_dropped`: 받았지만 처리하지 않은 패킷이다(자원 부족, 모르는 프로토콜 등). 장치의 버퍼 고갈 드롭은 여기 넣지 말고 `rx_missed_errors`로 따로 세라고 적혀 있다.
- 커리큘럼의 "링 오버플로 → `rx_dropped`"는 `/proc/net/dev`(그리고 이를 읽는 `ifconfig`·`netstat -i`)의 drop 칸에서 보인다는 뜻으로 읽는다.
  - `ip -s link`는 netlink 통계를 읽어 `dropped`와 `missed`를 **따로** 보여 준다(iproute2 `ip/ipaddress.c`). 링 오버플로는 여기서 `missed` 칸으로 보인다.
  - 정확한 필드는 드라이버마다 다르다.
- `softnet_stat`의 열은 이름이 없고 커널 버전마다 바뀔 수 있다(packagecloud). 행 하나가 CPU 하나다.

## 쓰이는 자료구조·알고리즘

- **DMA 링 버퍼(원형 큐)** — RX·TX 모두 고정 크기 디스크립터 배열을 원형으로 쓴다.
  - 생산자와 소비자가 서로 다른 인덱스를 들고 돈다.
  - RX: 생산자는 NIC, 소비자는 드라이버다. 가득 차면 NIC는 기다리지 못하고 **버린다**.
  - TX: 생산자는 드라이버, 소비자는 NIC다. 링이 차기 전에 드라이버가 송신 큐를 멈추고, 완료 처리로 자리가 나면 다시 깨운다(kernel docs "Softnet Driver Issues"). 그래서 패킷은 위(qdisc)에서 기다린다.
  - 원형 버퍼 일반론은 `data-structure/25-ring-buffer`의 몫이다. 미작성([data-structure 영역 표](../../data-structure/curriculum.md)).
- **`sk_buff` 연결 리스트** — 커널 패킷 객체 `struct sk_buff`는 `next`·`prev` 포인터를 가진다. 큐 머리 `sk_buff_head`는 `next`·`prev`·`qlen`·`lock`으로 된 이중 연결 리스트다(`include/linux/skbuff.h`).
  - 헤더를 붙이고 벗길 때 보통 데이터를 복사하지 않는다. 고정된 `head`·`end` 안에서 `data`·`tail` 포인터만 옮긴다.
  - 앞 공간(headroom)이 모자라거나 버퍼를 다른 skb와 공유하면 새로 할당·복사한다(`skb_cow_head`, `pskb_expand_head`, kernel docs Networking API).
  - 개념은 [연결 리스트](../../data-structure/02-linked-list/2-summary.md) 참고.
  - 예외: TCP의 재전송 큐(`tcp_rtx_queue`)와 순서 어긋난 수신 큐(`out_of_order_queue`)는 연결 리스트가 아니라 레드블랙 트리로 `sk_buff`를 묶는다(`include/net/sock.h`, `include/linux/tcp.h`).
- **RSS 해시 + 간접 테이블** — 흐름 해시(보통 Toeplitz)의 하위 비트로 테이블을 인덱싱해 큐 번호를 얻는다. 큐 수가 2의 거듭제곱이 아니어도 고르게 나누려고 간접 테이블을 둔다(kernel docs scaling). [해시맵](../../data-structure/05-hashmap/2-summary.md)의 "해시 → 버킷"과 같은 모양이다.
- **예산(budget) 기반 협력 스케줄링** — NAPI poll은 RX 패킷 수 한도 안에서, softirq 한 주기는 총량·시간 한도 안에서만 일하고 CPU를 돌려준다. 한 장치가 CPU를 독점하지 못하게 하는 장치다.
- **인터럽트 → 폴링 전환** — 부하가 낮으면 인터럽트로 반응하고, 높으면 폴링으로 몰아서 처리한다. 인터럽트 병합(coalescing)도 같은 목적이다.

## 적용 — 풀어나가는 법

### 1. "앱은 멀쩡한데 느리다"면 층마다 드롭을 센다

아래에서 위로 한 번씩 본다. 숫자가 **오르는** 곳이 병목이다(두 번 찍어 차이를 본다).

```bash
ip -s link show dev eth0                  # RX/TX errors, dropped, missed
ethtool -S eth0 | grep -Ei 'drop|miss|fifo|no_buf'   # 드라이버별 상세 (이름은 드라이버마다 다름)
ethtool -g eth0                           # 링 크기: 최대값 vs 현재값
cat /proc/net/softnet_stat                # CPU별: processed, dropped, time_squeeze ...
tc -s qdisc show dev eth0                 # 송신 큐 드롭
nstat -az | grep -Ei 'drop|overflow|prune|RcvbufErrors'   # 프로토콜 층 드롭
```

### 2. CPU 쏠림을 본다

```bash
mpstat -P ALL 1                           # 코어별 %soft(softirq), %irq
cat /proc/interrupts | grep eth0          # RX 큐별 IRQ가 어느 CPU에서 처리되나
cat /proc/softirqs | grep NET_RX          # CPU별 NET_RX softirq 횟수
ethtool -l eth0                           # 채널(큐) 수: 최대 vs 현재
ethtool -x eth0                           # RSS 간접 테이블
```

### 3. 조정 수단 (먼저 측정, 한 번에 하나씩)

```text
  증상                            조정                                          주의
  NIC missed/링 드롭 증가          ethtool -G eth0 rx <더 크게>                    대부분 링크 재시작
  한 코어 %soft 100%              ethtool -L로 큐 늘리기, IRQ affinity 분산,       irqbalance가 덮어쓸 수 있음
                                 RPS(rps_cpus) 켜기
  time_squeeze 증가               net.core.netdev_budget(_usecs) 올리기            다른 작업의 CPU 시간 감소
  softnet dropped 증가            net.core.netdev_max_backlog 올리기               RPS·loopback 경로와 관련
  qdisc 드롭                      txqueuelen·qdisc 설정 점검                       큐를 키우면 지연(버퍼블로트)
```

- packagecloud 글의 경고를 그대로 따른다.
  - 원격 접속한 채로 네트워크 설정을 바꾸면 스스로 접속을 끊을 수 있다.
  - 남의 sysctl 값을 통째로 복사하지 말고, 드롭 위치를 먼저 측정한다.
- RPS 설정 파일은 `/sys/class/net/<dev>/queues/rx-<n>/rps_cpus`다. 값은 CPU 비트맵이고, 기본값 0이면 꺼져 있다(kernel docs scaling).

### 4. 코드 쪽에서 할 수 있는 것

- 앱이 소켓을 제때 읽지 않으면 소켓 수신 버퍼가 찬다. TCP는 수신 윈도를 줄여 상대를 늦추고(17번), UDP는 그냥 버린다.
- 그래서 수신 루프를 무거운 처리와 분리한다(읽기 → 큐 → 작업자).

```java
// 읽기 스레드는 읽기만 한다. 처리는 작업자 풀로 넘긴다.
DatagramSocket sock = new DatagramSocket(9000);
sock.setReceiveBufferSize(4 * 1024 * 1024);   // 요청값(예시). 커널 rmem_max를 넘으면 잘린다
byte[] buf = new byte[65535];
while (true) {
    DatagramPacket p = new DatagramPacket(buf, buf.length);
    sock.receive(p);
    byte[] copy = Arrays.copyOf(p.getData(), p.getLength());
    workers.submit(() -> handle(copy));       // 여기서 오래 걸려도 수신은 계속된다
}
```

## 장애 시나리오와 대처

### 1. NIC 링 오버플로 — 조용한 손실

- **현상**: 트래픽 폭증 순간에 p99 지연이 튀고 TCP 재전송이 는다. 앱 에러 로그는 없다.
- **보이는 형태**
  - `ip -s link`의 RX `dropped`/`missed`가 폭증 시각에 오른다.
  - `ethtool -S`의 `rx_missed_errors`·`rx_no_buffer_count` 류 카운터가 오른다(이름은 드라이버마다 다름).
  - `ss -ti`의 `retrans`가 오른다. UDP면 그냥 데이터가 빈다.
- **원인**: 패킷이 들어오는 속도를 CPU가 링에서 꺼내는 속도가 못 따라갔다. 링이 가득 차 NIC가 버렸다. 이 드롭은 소켓·앱까지 알림이 가지 않는다.
- **대처**
  - `ethtool -g`로 최대값을 확인하고 `-G`로 링을 키운다(링크 재시작 주의).
  - 근본적으로는 소비 속도를 올린다. 큐·CPU를 늘리고(RSS), budget을 조정한다.
  - `ip -s link` 드롭 카운터를 모니터링 지표로 수집한다. 조용한 손실은 지표가 없으면 안 보인다.

### 2. softirq가 한 코어에 몰림

- **현상**: 전체 CPU 사용률은 낮은데 처리량이 더 오르지 않는다. 지연이 들쭉날쭉하다.
- **보이는 형태**
  - `mpstat -P ALL`에서 CPU0 하나만 `%soft`가 100%에 가깝고 나머지는 한가하다.
  - `top`에서 `ksoftirqd/0`이 CPU를 많이 쓴다.
  - `/proc/interrupts`에서 NIC IRQ가 한 CPU 열에만 쌓인다.
  - 그 CPU 행의 `softnet_stat` `time_squeeze`·`dropped`가 오른다.
- **원인**
  - NIC 수신 큐가 하나뿐이거나(가상 NIC 등), 모든 큐 IRQ가 한 CPU에 묶였다.
  - 또는 트래픽이 사실상 흐름 하나다(대형 단일 연결, 해시에 쓰이는 필드가 같은 캡슐화 트래픽). RSS는 흐름 단위로만 나눈다.
- **대처**
  - `ethtool -L`로 큐 수를 늘리고, IRQ affinity를 코어별로 나눈다(`irqbalance` 설정 확인).
  - 하드웨어 큐가 부족하면 RPS로 소프트웨어 분산을 켠다.
  - 단일 흐름이 원인이면 연결을 여러 개로 나누는 설계가 필요하다.

### 3. tcpdump에는 보였는데 앱은 못 받았다

- **현상**: "패킷은 분명히 도착했다"(tcpdump 증거)는데 서버 앱 로그에 요청이 없다.
- **보이는 형태**: tcpdump에 SYN·데이터가 보인다. 그런데 `ss`에 연결이 없거나, 앱이 읽은 흔적이 없다.
- **원인**
  - 수신 탭은 IP·netfilter보다 **앞**이다. 이후 단계에서 버려질 수 있다.
  - 예: iptables/nftables DROP, rp_filter, accept 큐 넘침(15번), 소켓 수신 버퍼 부족(UDP).
- **대처**
  - 방화벽 규칙 카운터(`iptables -vnL`, `nft list ruleset`)와 `nstat`의 드롭 카운터를 본다.
  - "캡처된 위치 = 전달 보장 위치"가 아님을 전제로 층별로 좁힌다.

### 4. 송신 쪽 qdisc 드롭 — 보냈는데 선에 안 나감

- **현상**: 대량 송신 중 재전송이 늘고 처리량이 떨어진다. 수신 측 문제는 없다.
- **보이는 형태**: `tc -s qdisc show dev eth0`의 `dropped`가 오른다. 로컬 tcpdump에는 그 패킷이 안 보인다(탭이 qdisc 뒤라서).
- **원인**: 앱·TCP가 NIC 속도보다 빨리 밀어 넣어 qdisc 큐가 찼다. 또는 트래픽 셰이핑 qdisc 설정이 한도를 걸었다.
- **대처**
  - qdisc 종류·설정(`tc qdisc show`)을 확인한다.
  - 큐를 무작정 키우면 지연이 커진다(버퍼블로트). 설정 없이 잘 동작하는 큐(`fq_codel`, `codel`, `sfq` 등)를 검토한다(kernel docs sysctl/net `default_qdisc` 설명).

## 핵심 문장

- 수신은 NIC → DMA로 링 버퍼 → IRQ → NAPI poll(softirq) → IP → TCP → 소켓 버퍼다. 송신은 그 반대 방향에 qdisc와 TX 링이 끼어 있다.
- 이 경로의 큐(RX 링, CPU 백로그, qdisc, UDP 소켓 수신 버퍼)는 넘치면 **조용히 버린다**. TCP가 복구하는 동안 앱에는 에러 대신 재전송 지연으로 보인다.
- 링 오버플로는 `ip -s link`의 `missed`(`rx_missed_errors`, `/proc/net/dev`에서는 drop에 합산), CPU 쪽 부족은 `/proc/net/softnet_stat`으로 본다.
- RSS·RPS는 흐름 해시로 CPU를 나눈다. 흐름 하나의 같은 처리 단계는 코어 하나를 넘지 못한다.
- tcpdump의 수신 탭은 netfilter보다 앞, 송신 탭은 qdisc보다 뒤다. 캡처 위치와 드롭 위치를 구분해 읽는다.

## 관련 주제·근거

- 선행
  - [23-socket-api](../23-socket-api/2-summary.md) — `send()`·`recv()`와 소켓 버퍼
  - `architecture/15-io-devices-interrupts-dma` — 인터럽트·DMA 기초. 미작성([architecture 영역 표](../../architecture/README.md))
- 후속·연결
  - [26-packet-journey](../26-packet-journey/2-summary.md) — 이 노트의 경로를 호스트 밖까지 이어 한 장으로
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — 수신 버퍼가 차면 윈도가 줄어드는 이야기.
  - [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) — netfilter 훅.
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — `ss`·`tcpdump`·`ethtool` 종합.
- packagecloud, "Monitoring and Tuning the Linux Networking Stack: Receiving Data" (리눅스 3.13, igb 기준) <https://blog.packagecloud.io/monitoring-tuning-linux-networking-stack-receiving-data/>
- packagecloud, "Monitoring and Tuning the Linux Networking Stack: Sending Data" <https://blog.packagecloud.io/monitoring-tuning-linux-networking-stack-sending-data/>
- send(2) — 송신 버퍼가 차면 블록, 논블로킹이면 `EAGAIN` <https://man7.org/linux/man-pages/man2/send.2.html>
- Linux kernel docs
  - "Scaling in the Linux Networking Stack" — RSS·RPS·RFS·XPS, `rps_cpus` <https://docs.kernel.org/networking/scaling.html>
  - "NAPI" — 인터럽트 마스킹, budget(RX 패킷 수), threaded NAPI·busy polling <https://docs.kernel.org/networking/napi.html>
  - "Softnet Driver Issues" — TX 큐 미리 멈추기 <https://docs.kernel.org/networking/driver.html>
  - ip-sysctl — `unres_qlen_bytes`·`unres_qlen`(deprecated) <https://docs.kernel.org/networking/ip-sysctl.html>
  - Networking API — `skb_cow_head`, `pskb_expand_head` <https://docs.kernel.org/networking/kapi.html>
  - sysctl/net — `netdev_budget`, `netdev_budget_usecs`, `netdev_max_backlog`, `default_qdisc` <https://docs.kernel.org/admin-guide/sysctl/net.html>
- Linux 커널 소스
  - `include/uapi/linux/if_link.h` — `rx_dropped`·`rx_missed_errors`·`rx_fifo_errors` 정의 <https://github.com/torvalds/linux/blob/master/include/uapi/linux/if_link.h>
- iproute2 `ip/ipaddress.c` — `ip -s link`의 RX 열(`dropped`·`missed` 분리 출력) <https://github.com/iproute2/iproute2/blob/main/ip/ipaddress.c>
  - `include/linux/skbuff.h` — `struct sk_buff`, `struct sk_buff_head` <https://github.com/torvalds/linux/blob/master/include/linux/skbuff.h>
