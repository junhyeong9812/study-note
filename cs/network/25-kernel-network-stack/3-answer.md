# network/25-kernel-network-stack — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 수신 경로

```text
NIC 도착 -> (DMA) RX 링 버퍼 -> (IRQ) 드라이버가 NAPI 예약 -> (softirq NET_RX) poll로 링에서 꺼내 sk_buff
 -> GRO / RPS 백로그 -> 패킷 탭 -> IP(netfilter) -> TCP -> 소켓 수신 버퍼 -> 앱 recv()
```

- DMA: NIC가 CPU 없이 패킷을 커널 메모리의 링 버퍼에 직접 쓴다.
- IRQ: "링에 새 패킷이 있다"고 CPU에 알린다.
- NAPI: 드라이버가 인터럽트 처리에서 poll을 예약한다.
- softirq: 예약된 poll이 보통 실제로 도는 문맥이다(threaded NAPI면 전용 커널 스레드). budget만큼 링에서 꺼내 위로 올린다.

### 2. 인터럽트 폭주와 NAPI

- 패킷마다 인터럽트를 걸면 고속 수신에서 CPU가 인터럽트 진입·복귀에만 시간을 쓴다. 정작 패킷을 처리할 시간이 없다.
- NAPI는 첫 인터럽트에서 poll을 예약하고, **폴링이 끝날 때까지 인터럽트를 가린다**(권고). 이후엔 폴링으로 몰아서 처리한다(kernel docs NAPI).
- poll 한 번은 budget(RX 패킷 수) 안에서만 일한다. softirq 한 주기도 `netdev_budget`(총량)·`netdev_budget_usecs`(시간) 안에서만 일하고 CPU를 돌려준다. 할 일을 다 하면 인터럽트를 다시 켠다.

### 3. RX 링 버퍼

- 고정 개수의 디스크립터를 원형으로 돌려 쓰는 **원형 큐**다. 생산자는 NIC, 소비자는 드라이버(poll)다.
- 가득 차면 NIC는 기다릴 곳이 없어 새 패킷을 **버린다**. 커널 정의상 이는 `rx_missed_errors`로 센다(`if_link.h`).
- 조용한 이유
  - 버려진 패킷은 소켓까지 오지 않는다. 그래서 어떤 시스템콜도 에러를 돌려주지 않는다.
  - TCP는 손실을 재전송으로 메운다. 메우는 동안 앱에는 "가끔 느림"으로만 보인다(끝내 못 메우면 연결 타임아웃). UDP는 데이터가 그냥 빈다.

### 4. RSS vs RPS

- RSS: **NIC 하드웨어**가 패킷 헤더 해시(보통 Toeplitz)로 수신 큐를 고른다. 큐마다 IRQ가 있어 처리 CPU가 갈린다.
- RPS: **커널 소프트웨어**가 흐름 해시로 CPU를 골라 그 CPU의 백로그 큐에 넣는다. 인터럽트 처리보다 위, 프로토콜 처리 단계에서 나눈다. 아무 NIC에서나 쓸 수 있다(kernel docs scaling).
- 둘 다 **흐름 단위 해시**다. 같은 4-튜플은 늘 같은 큐·CPU로 간다. 흐름 안 순서를 지키려는 설계다. 그래서 흐름 하나의 같은 처리 단계는 코어 하나를 넘지 못한다(RPS면 IRQ 처리 CPU와 프로토콜 처리 CPU가 다를 수는 있다).

### 5. 송신 경로와 qdisc

```text
send() -> 소켓 송신 버퍼 -> TCP(세그먼트, 재전송 보관) -> IP(라우팅, 이웃/ARP)
 -> 송신 큐 선택(XPS/해시) -> qdisc -> 패킷 탭 -> 드라이버 xmit -> TX 링(DMA) -> NIC -> 완료 IRQ -> 버퍼 해제
```

- qdisc(queueing discipline)는 장치 바로 앞의 **송신 큐와 스케줄링 정책**이다. 어떤 패킷을 언제 드라이버로 넘길지 정한다.
- 단일 큐 장치 기본은 `pfifo_fast`, 멀티 큐는 `mq`다(packagecloud, 3.13 기준). `net.core.default_qdisc`로 기본값을 바꿀 수 있다. 물리 멀티 큐 장치는 루트가 그대로 `mq`이고 그 아래 큐별 qdisc가 바뀐다(kernel docs sysctl/net).

### 6. tcpdump에 보이나

- iptables DROP한 수신 패킷: **보인다**. 수신 탭(`__netif_receive_skb_core`)이 IP 계층·netfilter보다 앞에 있기 때문이다.
- qdisc에서 버려진 송신 패킷: **안 보인다**. 송신 탭(`dev_hard_start_xmit`)이 qdisc를 지난 뒤, 드라이버 직전에 있기 때문이다.
- 그래서 tcpdump는 "그 지점까지 왔다"는 증거일 뿐이다. 이후 전달을 보장하지 않는다.

### 7. `sk_buff`의 자료구조

- `sk_buff`는 `next`·`prev` 포인터를 가진다. 큐 머리 `sk_buff_head`(`next`·`prev`·`qlen`·`lock`)와 함께 **이중 연결 리스트**를 이룬다(`include/linux/skbuff.h`).
- 버퍼 경계 `head`·`end`는 두고 `data`·`tail` 포인터를 옮겨 헤더 공간을 늘리거나 줄인다. 앞 공간이 충분하고 버퍼를 혼자 쓰면 데이터 자체는 복사하지 않는다(모자라거나 공유 중이면 `skb_cow_head` 등으로 재할당·복사).
- 예: 수신에서 이더넷 헤더를 벗기면 `data` 포인터만 헤더 길이만큼 앞으로 간다.

### 8. 드롭 위치 찾기 순서

아래 층부터 위로, 두 번 찍어 **증가분**을 본다.

1. `ip -s link show dev eth0` — RX dropped/missed/errors
2. `ethtool -S eth0` — 드라이버별 드롭·FIFO·no buffer 카운터, `ethtool -g`로 링 크기
3. `/proc/net/softnet_stat` — CPU별 `dropped`(백로그 넘침), `time_squeeze`(budget 부족)
4. `tc -s qdisc show dev eth0` — 송신 쪽 드롭
5. `iptables -vnL` / `nft list ruleset` — 방화벽 드롭
6. `nstat -az` — 프로토콜 층 드롭(accept 큐 넘침, 수신 버퍼 부족)
7. `ss -ti` — 연결별 `retrans`

### 9. CPU0만 `%soft` 100%

- 원인 후보
  - NIC 수신 큐가 하나뿐이다(가상 NIC 등). `ethtool -l`로 확인한다.
  - 큐는 여럿인데 IRQ affinity가 모두 CPU0이다. `/proc/interrupts`로 확인한다.
  - 트래픽이 사실상 흐름 하나라 해시가 한 큐로만 보낸다.
- 대처
  - `ethtool -L`로 큐 수를 늘린다. IRQ affinity를 분산한다(`irqbalance`가 덮어쓰는지 확인).
  - 하드웨어 큐가 부족하면 RPS(`rps_cpus`)를 켠다.
  - 단일 흐름이 원인이면 연결을 여러 개로 나눈다. 커널 설정으로는 흐름 하나를 쪼갤 수 없다.

### 10. `rx_dropped` vs `rx_missed_errors`

- `rx_missed_errors`: 장치가 **버퍼 공간 부족**으로 버린 패킷이다. 호스트가 수신 속도를 못 따라간다는 신호다.
- `rx_dropped`: 받았지만 처리하지 않은 패킷이다(자원 부족, 모르는 프로토콜 등). 커널 주석은 장치의 버퍼 고갈 드롭을 여기에 넣지 말고 `rx_missed_errors`로 따로 세라고 한다(`if_link.h`).
- `/proc/net/dev`(그리고 `ifconfig`·`netstat -i`)는 두 카운터를 **drop 칸에 합쳐** 보여 준다(`if_link.h` 주석).
- `ip -s link`는 netlink 통계를 읽어 RX 줄에 `dropped`와 `missed`를 **따로** 찍는다(iproute2 `ip/ipaddress.c`). 링 오버플로는 `missed` 쪽에서 보인다.
- 드라이버마다 어느 카운터에 넣는지 다를 수 있으니, 정확한 구분은 `ethtool -S`와 드라이버 문서로 한다.
