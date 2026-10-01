# network/06-switching-and-vlan — 스위치는 목적지 포트를 어떻게 알아내고, 루프는 왜 망 전체를 멈추게 하나 — 정리 (힌트)

## 해결하는 문제

같은 건물 안 컴퓨터 수십 대를 이더넷으로 묶는다고 하자.\
프레임 하나를 목적지 한 대에게만 보내고 싶다.\
그런데 누가 어느 포트에 꽂혀 있는지는 아무도 알려주지 않는다.

```text
  허브(hub):   들어온 신호를 모든 포트로 그대로 복사한다
               A ---> [허브] ---> B, C, D  (B만 받으면 되는데 전원이 받는다)

  스위치:      "B는 2번 포트에 있다"를 스스로 배워서 그 포트로만 보낸다
               A ---> [스위치] ---> B      (C, D는 모른다)
```

쉬운 예: 아파트 우편함이다.\
처음 온 집배원은 편지를 모든 집 문 앞에 복사해서 둔다(플러딩).\
답장이 오면 봉투의 보낸 사람 주소와 동 호수를 적어 둔다(학습).\
다음부터는 그 집에만 넣는다(포워딩).

똑같은 구조다.\
스위치는 들어온 프레임의 **출발지** MAC을 보고 "이 주소는 이 포트 뒤에 있다"를 배운다.

스위치만으로는 두 문제가 남는다.
- **범위 문제**: 브로드캐스트(ARP 요청 등)는 여전히 모든 포트로 간다.
  - 부서가 늘면 브로드캐스트가 닿는 범위도 커진다.
  - 부서마다 스위치를 따로 사지 않고 한 장비를 논리적으로 쪼개고 싶다 → **VLAN**.
- **이중화 문제**: 장애 대비로 스위치를 두 경로로 이으면 **루프**가 생긴다.
  - 이더넷 프레임에는 수명(TTL) 필드가 없다. 그래서 루프를 도는 브로드캐스트는 스스로 사라지지 않는다.
  - 루프를 논리적으로 끊는 장치가 필요하다 → **STP**.

실무 예
- 데이터센터 랙의 ToR(Top of Rack) 스위치, 사무실 L2 스위치
- 리눅스 호스트 안의 브리지(`docker0`, KVM의 `br0`) — 소프트웨어로 만든 스위치다.
- 클라우드 VPC는 L2 스위칭을 사용자에게 드러내지 않는다. 그래도 온프레미스·가상화 호스트에서는 이 지식이 그대로 쓰인다.

## 동작·원리

### 허브 vs 스위치 — 충돌 도메인이 쪼개진다

```text
  허브 (한 덩어리)                      스위치 (포트마다 따로)
  +---------------------+              +---------------------+
  |  A   B   C   D      |              | [A] [B] [C] [D]     |
  |  \___|___|___/      |              |  |   |   |   |      |
  |   공유 매체 1개       |              |  스위치 패브릭        |
  +---------------------+              +---------------------+
  충돌 도메인 1개                         충돌 도메인 = 포트마다 1개
  브로드캐스트 도메인 1개                  브로드캐스트 도메인 1개 (VLAN 없으면)
```

  - *충돌 도메인(collision domain)*: 두 장비가 동시에 보내면 신호가 섞이는 범위다. 허브는 전체가 하나다.
  - *브로드캐스트 도메인*: 브로드캐스트 프레임(목적지 `ff:ff:ff:ff:ff:ff`)이 닿는 범위다. 스위치는 이것을 쪼개지 못한다. 쪼개려면 라우터나 VLAN이 필요하다.

- 허브는 비트를 복사하는 물리 계층 장비다.
- 스위치는 프레임을 받아 저장하고, 헤더를 읽고, 골라서 내보내는 링크 계층 장비다(K&R 6.4.3).
- 스위치는 호스트·라우터가 모르게 동작한다. 그래서 **투명(transparent)**하다고 한다(K&R 6.4.3).

### 자가 학습 — 스위치 테이블을 스스로 채운다

스위치 테이블(리눅스 용어로 FDB, forwarding database)은 "MAC → 포트 → 마지막으로 본 시각"의 목록이다.

```text
  스위치 테이블 (FDB)
  +-------------------+------+---------------+
  | MAC 주소           | 포트  | 마지막으로 본 시각 |
  +-------------------+------+---------------+
  | aa:aa:aa:aa:aa:01 |  1   | 09:00:03      |
  | bb:bb:bb:bb:bb:02 |  2   | 09:00:05      |
  +-------------------+------+---------------+
```

  - *FDB(Forwarding Database)*: 스위치 테이블의 다른 이름이다. `bridge fdb show`가 이 표를 보여 준다(bridge(8)).
  - *CAM(Content-Addressable Memory)*: 하드웨어 스위치가 이 표를 담는 메모리다. 주소를 넣으면 위치가 아니라 내용으로 찾아 준다. 소프트웨어로 치면 해시 테이블 조회와 같은 역할이다.

프레임 한 개가 들어올 때 하는 일

```text
  포트 p로 프레임 도착 (출발지 S, 목적지 D)

  1) 학습:  table[S] = (p, 지금 시각)          <- 출발지로 배운다
  2) 조회:  table[D] 가 있나?
       없음 ------------------------------> 플러딩: p를 뺀 모든 포트로 복사
       있음, 포트 == p -------------------> 필터링: 버린다 (같은 쪽에 있으니 보낼 필요 없음)
       있음, 포트 != p -------------------> 포워딩: 그 포트로만 보낸다
  3) 에이징: 오래 안 보인 항목은 지운다
```

- 이 세 동작(학습·필터링·포워딩)은 K&R 6.4.3의 설명 그대로다.
- 브로드캐스트 목적지는 학습될 수 없으므로 기본적으로 플러딩된다. 리눅스 브리지는 포트별 `bcast_flood off`로 끌 수 있다(bridge(8), 기본 on).
- 에이징은 기기가 다른 포트로 옮겨 가도 결국 새 위치를 다시 배우게 해 준다.
  - 리눅스 브리지의 에이징 기본값은 300초다(kernel bridge 문서 "The default value is (300 * USER_HZ)").
  - `ip link ... type bridge ageing_time N`으로 바꾼다(ip-link(8)).

  - *플러딩(flooding)*: 목적지를 모를 때 들어온 포트만 빼고 모두에게 복사하는 동작이다.
  - *에이징(aging)*: 일정 시간 동안 그 출발지로 프레임이 안 오면 항목을 지우는 동작이다.

### VLAN — 한 스위치를 여러 개로 쪼갠다

```text
  물리 스위치 1대                              논리적으로는
  +--------------------------------+          [VLAN 10 스위치]  1  2  3
  | 1  2  3 | 4  5  6 | 7(트렁크)    |          [VLAN 20 스위치]  4  5  6
  | VLAN 10 | VLAN 20 | 10,20 태그   |          두 VLAN 사이 통신은 라우터(L3)를 거친다
  +--------------------------------+
```

- 포트마다 VLAN을 정한다. 같은 VLAN 포트끼리만 프레임이 오간다.
- 브로드캐스트도 같은 VLAN 안에서만 퍼진다. 즉 VLAN 하나 = 브로드캐스트 도메인 하나다.
- 스위치 여러 대에 VLAN을 걸치려면 스위치 사이 링크(**트렁크**)에서 프레임마다 "어느 VLAN 소속인지" 표시해야 한다. 이것이 802.1Q 태그다.

```text
  보통 이더넷 프레임
  +--------+--------+-----------+----------------+-----+
  | 목적지 6 | 출발지 6 | EtherType 2 | 데이터           | FCS 4 |
  +--------+--------+-----------+----------------+-----+

  802.1Q 태그가 붙은 프레임 (+4바이트)
  +--------+--------+----------------------+-----------+---------+-----+
  | 목적지 6 | 출발지 6 | TPID 2   | TCI 2      | EtherType 2 | 데이터    | FCS 4 |
  |        |        | 0x8100   | PCP3 DEI1 VID12 |           |         |     |
  +--------+--------+----------------------+-----------+---------+-----+
```

  - *TPID(Tag Protocol Identifier)*: "여기 VLAN 태그가 있다"는 표시다. 802.1Q는 `0x8100`, 태그를 두 겹 쌓는 802.1ad는 `0x88A8`이다(kernel bridge 문서).
  - *VID(VLAN ID)*: 12비트 VLAN 번호다. 0과 4095(0xFFF)는 예약되어 있어 실제로 쓸 수 있는 번호는 1~4094다(IEEE 802.1Q, K&R 6.4.4).
  - *PCP*: 3비트 우선순위다. QoS에 쓴다.
  - *액세스 포트*: 태그 없는 프레임을 주고받는 포트다. 스위치가 들어올 때 VLAN을 붙이고 나갈 때 뗀다.
  - *트렁크 포트*: 여러 VLAN의 프레임을 태그를 단 채 나르는 포트다.
  - *PVID(Port VLAN ID)*: 태그 없이 들어온 프레임을 어느 VLAN으로 볼지 정하는 값이다. 리눅스 브리지의 기본 PVID는 1이다(kernel bridge 문서).

- 리눅스 브리지는 VLAN 필터링이 **기본 꺼짐**이다. 켜지 않으면 태그를 보지 않고 스위칭한다(kernel bridge 문서, ip-link(8) `vlan_filtering`).

### 루프 — 이중화가 만든 함정

```text
         +---------+                       브로드캐스트 1개가 들어오면
   A ----| 스위치 1 |======+                1 -> 2 -> 1 -> 2 -> ...
         +---------+      ||  링크 2개        (양방향으로 계속 복사)
         +---------+      ||
   B ----| 스위치 2 |======+                이더넷 헤더에는 TTL이 없다
         +---------+                       -> 프레임이 영원히 돈다
```

- 스위치 두 대를 링크 두 개로 이으면 브로드캐스트가 두 링크를 오가며 계속 복사된다.
- 스위치는 받은 브로드캐스트를 다시 플러딩하고, 이더넷 프레임에는 IP처럼 줄어드는 TTL이 없다.
- 결과는 **브로드캐스트 스톰**이다. 대역폭이 복사본으로 가득 차고, 장비 CPU가 올라가고, 망 전체가 멈춘다.
- 루프는 학습도 망가뜨린다.
  - 같은 출발지 MAC이 두 포트에서 번갈아 들어온다.
  - 테이블이 계속 바뀐다(MAC flapping).

### STP — 링크는 두고, 논리적으로 트리만 쓴다

```text
  물리 연결 (루프 있음)              STP가 만든 논리 트리
      [S1 루트]                        [S1 루트]
       /     \                          /     \
    [S2]-----[S3]                    [S2]     [S3]
                                        x----x   <- 한쪽 포트를 차단(blocking)
```

STP(Spanning Tree Protocol)는 스위치들이 BPDU라는 제어 프레임을 주고받아 다음을 정한다.

1. **루트 브리지 선출**: 브리지 ID(우선순위 + MAC)가 가장 작은 스위치가 루트가 된다. 우선순위 기본값이 모두 같으면(32768) MAC이 가장 작은 쪽이 된다(Cisco Catalyst STP 설정 가이드).
2. **루트 포트**: 각 스위치는 루트까지 경로 비용이 가장 작은 포트 하나를 고른다.
3. **지정 포트**: 각 링크 구간마다 루트까지 비용이 가장 작은 쪽의 포트 하나를 정한다. 그 구간을 트리에 이어 주는(그 구간으로 프레임을 내보내는) 포트다.
4. 나머지 포트는 **차단**한다. 차단 포트는 BPDU만 받고 데이터 프레임은 버린다.

  - *BPDU(Bridge Protocol Data Unit)*: STP 스위치끼리 주고받는 제어 프레임이다. 루트가 누구인지, 루트까지 비용이 얼마인지를 담는다.
  - *스패닝 트리*: 그래프의 모든 노드를 사이클 없이 잇는 부분 그래프다. STP의 트리는 "루트까지 최단 경로 트리"이지 "간선 가중치 합이 최소인 트리(MST)"와는 목적이 다르다.

포트 상태와 시간 (리눅스 브리지 기준)

```text
  BLOCKING --> LISTENING --(forward_delay)--> LEARNING --(forward_delay)--> FORWARDING
  (BPDU만)     (BPDU만, 데이터 버림)            (MAC 학습만, 전달 안 함)       (정상 전달)
```

- 리눅스 브리지는 포트 상태를 0 DISABLED, 1 LISTENING, 2 LEARNING, 3 FORWARDING, 4 BLOCKING으로 둔다(bridge(8)).
- 타이머 기본값: hello 2초, max_age 20초, forward_delay 15초다(kernel bridge 문서).
  - 새 포트가 올라오면 LISTENING 15초 + LEARNING 15초 = 약 30초 동안 데이터가 흐르지 않는다.
  - 상위 스위치가 조용히 죽으면 max_age 20초를 기다려야 알아챈다. 그다음 30초를 더 쓰므로 최악 약 50초가 걸린다. 이 수치는 위 기본값에서 계산한 값이다.
- 리눅스 브리지는 STP가 **기본 꺼짐**이다(kernel bridge 문서 `stp_state` "default value is 0").
- 느린 수렴을 줄이려고 RSTP가 나왔다. IEEE 802.1D-2004는 원래 STP를 빼고 RSTP를 넣었다(kernel bridge 문서).

  - *RSTP(Rapid STP)*: 포트 역할 협상으로 수렴을 빠르게 한 STP 개정판이다. 리눅스에서는 `mstpd` 같은 사용자 공간 데몬이 맡는다(kernel bridge 문서).

## 쓰이는 자료구조·알고리즘

- **해시 테이블 + 타임스탬프(스위치 테이블)**
  - 키는 MAC(VLAN을 쓰면 (VLAN, MAC))이고 값은 (포트, 마지막 시각)이다.
  - 프레임마다 조회 1번, 갱신 1번이 일어나므로 O(1) 조회가 필수다.
  - 하드웨어는 CAM으로, 리눅스 브리지는 해시 테이블(`struct rhashtable fdb_hash_tbl`, 키 = (MAC, VLAN) — net/bridge/br_private.h·br_fdb.c)로 구현한다.
  - 개념: [해시맵](../../data-structure/05-hashmap/2-summary.md).
  - 에이징은 "오래된 것부터 지우기"라 [LRU 캐시](../../data-structure/10-lru-cache/2-summary.md)와 닮았다. 다만 LRU는 용량이 차야 지우고, 에이징은 시간이 지나면 지운다.
- **스패닝 트리(그래프)**
  - 스위치 = 노드, 링크 = 간선이다.
  - 루트에서의 최단 경로(경로 비용 합)로 트리를 만든다. 분산 버전 최단 경로 트리다.
  - 가중치 합 최소 트리인 [MST](../../algorithm/17-mst/2-summary.md)와 이름은 같지만 목적이 다르다. 같은 "사이클 없는 부분 그래프"라는 점만 공통이다.
- **포트별 VLAN 멤버십 = 비트 집합**
  - VID가 12비트이므로 포트마다 4096비트 비트맵 하나로 "이 포트가 어느 VLAN에 속하나"를 표현할 수 있다.
  - 개념: [비트셋](../../data-structure/18-bitset/2-summary.md). 실제 장비 구현은 다양하다 [?].

## 적용 — 풀어나가는 법

### 1. 학습 스위치를 코드로 흉내 낸다 (TypeScript)

```ts
type Frame = { src: string; dst: string; inPort: number };

class LearningSwitch {
  private fdb = new Map<string, { port: number; seen: number }>();
  constructor(private ports: number[], private agingMs = 300_000) {} // 300초 = 리눅스 기본값

  receive(f: Frame, now: number): number[] {
    this.fdb.set(f.src, { port: f.inPort, seen: now });        // 1) 학습
    const e = this.fdb.get(f.dst);
    if (e && now - e.seen > this.agingMs) this.fdb.delete(f.dst); // 3) 에이징(조회 시 지연 삭제)
    const hit = this.fdb.get(f.dst);
    if (f.dst === 'ff:ff:ff:ff:ff:ff' || !hit)                  // 모르는 목적지·브로드캐스트
      return this.ports.filter(p => p !== f.inPort);            //   -> 플러딩
    if (hit.port === f.inPort) return [];                       //   -> 필터링
    return [hit.port];                                          //   -> 포워딩
  }
}
```

- 이 모델에서 링크 두 개로 스위치 두 대를 이으면 브로드캐스트 한 개가 끝없이 되돌아온다. 직접 돌려 보면 루프가 왜 치명적인지 보인다.

### 2. 리눅스 브리지로 직접 본다

```bash
# 브리지 만들고 STP 켜기 (기본은 꺼짐)
ip link add br0 type bridge stp_state 1 vlan_filtering 1
ip link set eth1 master br0
ip link set eth2 master br0

# 스위치 테이블: 어떤 MAC이 어느 포트에 있나
bridge fdb show br br0
bridge -s fdb show br br0        # -s: 마지막 갱신·사용 시각

# 포트 STP 상태 (forwarding / blocking ...)
bridge link show

# 포트별 VLAN과 PVID
bridge vlan show
bridge vlan add dev eth2 vid 20 pvid untagged   # VLAN 20을 PVID·untagged로 추가
bridge vlan del dev eth2 vid 1                  # 자동으로 붙은 기본 VLAN 1을 지워야 VLAN 20 전용 액세스 포트가 된다

# 브리지 세부 옵션 (ageing_time, stp_state, forward_delay ...)
ip -d link show br0
```

- 포트를 브리지에 붙이면 커널이 기본 PVID(1)를 `PVID untagged`로 자동 등록한다(`net/bridge/br_vlan.c` `nbp_vlan_init()`).
  - VID 20을 `pvid`로 추가하면 PVID 표시만 20으로 옮겨 간다. VLAN 1 멤버십과 untagged 설정은 남는다.
  - 그대로 두면 VLAN 1의 브로드캐스트가 eth2로 태그 없이 계속 나간다. `bridge vlan show`로 VID 1이 남았는지 확인한다.
  - 브리지를 만들 때 `vlan_default_pvid 0`을 주면 처음부터 기본 PVID가 붙지 않는다(kernel bridge 문서 `IFLA_BR_VLAN_DEFAULT_PVID`).

### 3. 패킷에서 링크 계층을 본다

```bash
# -e: 이더넷 헤더(MAC)까지 출력
tcpdump -e -ni eth0 ether broadcast          # 브로드캐스트만
tcpdump -e -ni eth0 vlan                     # 802.1Q 태그 붙은 프레임만
tcpdump -e -ni eth0 'ether proto 0x88cc or stp'  # LLDP·STP BPDU
```

- `tcpdump -e` 출력에 `vlan 20` 같은 태그 표시가 붙으면 트렁크로 들어온 프레임이다.
- 같은 ARP 요청이 초당 수천 번 반복되면 루프를 의심한다.

### 4. 설계할 때 정할 것

- 이중화 링크가 있으면 STP(가능하면 RSTP)를 켠다.
- 호스트·서버가 붙는 포트는 "엣지 포트"로 설정해 30초 대기를 건너뛴다. 벤더마다 이름이 다르다. Cisco의 PortFast는 listening·learning을 건너뛰고 곧바로 forwarding으로 보낸다(Cisco Catalyst 9200 "Configuring Optional Spanning-Tree Features").
- 엣지 포트에서 BPDU가 들어오면 포트를 닫게 한다. Cisco BPDU guard는 PortFast 포트에 BPDU가 오면 그 포트를 error-disabled 상태로 만든다(같은 Cisco 문서). 누군가 작은 스위치를 꽂아 루프를 만드는 사고를 막는다.
- VLAN은 트렁크 양쪽에서 허용 목록과 태그 없는 VLAN(PVID·native VLAN)을 **같게** 맞춘다.

## 장애 시나리오와 대처

### 1. 브로드캐스트 스톰 — 망 전체가 한꺼번에 느려진다

- **현상**: 같은 스위치 영역의 모든 서버가 동시에 느려지거나 끊긴다. 원격 접속조차 안 된다.
- **보이는 형태**
  - 스위치 포트 카운터에서 브로드캐스트·멀티캐스트 수가 폭증한다.
  - `tcpdump -e`에 같은 ARP 요청 프레임이 계속 반복된다.
  - 스위치 로그에 MAC flapping(같은 MAC이 두 포트를 오감) 경고가 뜬다 [?].
  - 호스트 CPU가 오른다. 모든 브로드캐스트를 받아 처리하기 때문이다.
- **원인**: L2 루프 + STP 부재(또는 꺼짐). 이중화 케이블, 잘못 꽂은 패치 케이블, 가상 브리지 두 개를 이은 설정이 흔한 원인이다.
- **대처**
  - 즉시: 루프를 만든 링크를 뽑는다. 최근 바뀐 케이블·포트부터 본다.
  - 재발 방지: STP/RSTP를 켠다. 엣지 포트에 BPDU guard를 둔다. 스위치의 storm control(브로드캐스트 비율 상한)을 건다 [?].
  - 리눅스 브리지는 STP가 기본 꺼짐이다. 여러 브리지를 이어 붙였다면 반드시 확인한다.

### 2. 스위치 테이블이 가득 차서 유니캐스트가 플러딩된다

- **현상**: 네트워크가 전반적으로 느리다. 엉뚱한 서버에서 남의 트래픽이 보인다.
- **보이는 형태**: 관계없는 호스트에서 `tcpdump`를 돌리면 다른 호스트끼리의 유니캐스트가 잡힌다.
- **원인**
  - 테이블 용량보다 많은 MAC이 보였다. 가상 머신·컨테이너가 많거나, 공격자가 가짜 출발지 MAC을 쏟아 부었다(MAC flooding).
  - 테이블에 없는 목적지는 플러딩되므로, 스위치가 사실상 허브가 된다.
- **대처**
  - 포트당 학습 MAC 수를 제한한다(port security 류) [?].
  - L2 영역(브로드캐스트 도메인)을 VLAN·L3로 쪼갠다.
  - 보안 관점: 플러딩되면 도청이 가능해진다. 민감 트래픽은 L2를 믿지 말고 TLS로 암호화한다.

### 3. 새 서버를 꽂았는데 30초 동안 DHCP·네트워크가 안 된다

- **현상**: 부팅 직후 DHCP가 실패해 `169.254.x.x` 주소를 받는다. 1분쯤 뒤 재시도하면 된다.
- **보이는 형태**: 링크는 올라왔는데 첫 30초가량 어떤 응답도 없다. 스위치 포트 상태가 listening/learning이다.
- **원인**: STP가 켜진 포트는 LISTENING·LEARNING을 거쳐야 전달을 시작한다. 기본 forward_delay 15초 × 2 = 약 30초다(kernel bridge 문서 기본값).
- **대처**
  - 서버가 붙는 포트를 엣지 포트(PortFast 류)로 설정한다.
  - 가능하면 RSTP를 쓴다.

### 4. 트렁크 양쪽 VLAN 설정 불일치 — 특정 VLAN만 안 된다

- **현상**: 같은 VLAN인데 스위치 A 쪽 서버와 스위치 B 쪽 서버가 통신하지 못한다. 다른 VLAN은 된다.
- **보이는 형태**
  - ARP 요청은 나가는데 응답이 없다(`ip neigh`에 `FAILED`/`INCOMPLETE`).
  - `tcpdump -e`로 보면 트렁크 한쪽에서는 `vlan 20` 태그가 붙어 나가는데 다른 쪽에서는 안 보인다.
- **원인**: 트렁크 허용 VLAN 목록에서 빠졌다. 또는 태그 없는 VLAN(PVID/native VLAN)이 양쪽에서 다르다.
- **대처**
  - 트렁크 양쪽의 허용 목록과 PVID를 같게 맞춘다.
  - 리눅스에서는 `bridge vlan show`로 포트별 VID·PVID·untagged를 확인한다.

## 핵심 문장

- 스위치는 **출발지** MAC으로 배우고, **목적지** MAC으로 고른다. 모르는 목적지는 들어온 포트만 빼고 모두에게 보낸다(플러딩).
- 스위치는 충돌 도메인을 포트마다 쪼개지만 브로드캐스트 도메인은 쪼개지 못한다. 쪼개는 것은 VLAN과 라우터다.
- 802.1Q 태그는 4바이트이고, 그 안의 12비트 VID가 VLAN 번호다.
- 이더넷 프레임에는 TTL이 없어서 L2 루프의 브로드캐스트는 스스로 사라지지 않는다. 그래서 STP가 여분 링크를 논리적으로 차단한다.
- STP는 안전하지만 느리다. 기본 타이머로는 포트가 전달을 시작하기까지 약 30초가 걸린다. 엣지 포트 설정과 RSTP가 이를 줄인다.

## 관련 주제·근거

- 선행: [04-ethernet-and-mac](../04-ethernet-and-mac/2-summary.md)
- 후속·연결
  - [05-arp](../05-arp/2-summary.md) — 브로드캐스트로 IP→MAC을 묻는다. 스톰 때 가장 먼저 보이는 프레임이다.
  - [07-ip-addressing-cidr](../07-ip-addressing-cidr/2-summary.md) — VLAN 하나에 서브넷 하나를 대응시키는 것이 흔한 설계다.
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — VLAN 사이 통신은 L3 라우팅이다.
  - [12-dhcp](../12-dhcp/2-summary.md) — STP 대기 중 DHCP 실패.
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) · [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md) · [algorithm/17-mst](../../algorithm/17-mst/2-summary.md)
- 교재: Kurose & Ross 8판 6.4.3 "Link-Layer Switches"(학습·필터링·포워딩, 에이징), 6.4.4 "Virtual Local Area Networks"(802.1Q 태그)
- Linux kernel, "Ethernet Bridging" <https://docs.kernel.org/networking/bridge.html>
  - FDB 에이징 기본 300초, STP 기본 꺼짐, forward_delay 15·hello 2·max_age 20초
  - VLAN 필터링 기본 꺼짐, PVID 기본 1, TPID 0x8100(802.1Q)·0x88A8(802.1ad)
  - 802.1D-2004가 원래 STP를 빼고 RSTP를 포함했다는 설명, 사용자 공간 STP 데몬(mstpd)
- bridge(8) — `bridge fdb`, `bridge link`의 STP 포트 상태 0~4, `learning`·`flood` 기본 on, `bridge vlan`의 `pvid`·`untagged` <https://man7.org/linux/man-pages/man8/bridge.8.html>
- Linux 소스 `net/bridge/br_vlan.c` `nbp_vlan_init()` — 포트 추가 시 `default_pvid`를 PVID·UNTAGGED로 등록 <https://github.com/torvalds/linux/blob/master/net/bridge/br_vlan.c>
- ip-link(8) — `type bridge`의 `ageing_time`·`stp_state`·`forward_delay`·`vlan_filtering` <https://man7.org/linux/man-pages/man8/ip-link.8.html>
- Cisco, Catalyst 9200 "Configuring Optional Spanning-Tree Features" — PortFast, BPDU guard <https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9200/software/release/16-12/configuration_guide/lyr2/b_1612_lyr2_9200_cg/configuring_optional_spanning_tree_features.html>
- Cisco, Catalyst 9200 "Configuring Spanning Tree Protocol" — 기본 우선순위 32768, 같으면 MAC이 가장 작은 스위치가 루트 <https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9200/software/release/16-12/configuration_guide/lyr2/b_1612_lyr2_9200_cg/configuring_spanning_tree_protocol.html>
- IEEE 802.1Q(VLAN 태그 형식, VID 0·4095 예약), IEEE 802.1D(브리지·STP) — 표준 원문은 직접 대조하지 못했다. 태그 형식은 K&R 6.4.4와 kernel 문서로 교차 확인했다.
