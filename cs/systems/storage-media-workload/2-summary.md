# cs/storage-media-workload - 저장 매체와 워크로드 (HDD, SSD의 동작 방식과 데이터 특성별 선택 기준) - 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다.
> 따라 친 원고 없이, 포트폴리오 사례(랜덤 액세스 워크로드를 HDD에 두었다가 계층을 나눈 경험)를 일반화해 쓴 글이다. README 규칙상 서머리는 본인 문장이 원칙이니 읽다가 걸리는 곳은 본인 문장으로 바꿔 간다.
> **수치 근거(2026-09-20 접지)** — 전부 제조사 데이터시트다. HDD: Seagate Exos X24 / Exos M / Exos 2X18 / Exos 10E2400 / Exos 15E900 / BarraCuda, WD Ultrastar DC HC580 / He10, Toshiba MG 시리즈. SSD: Samsung PM893(SATA) / PM9A3, WD·SanDisk Ultrastar DC SN655, Kioxia CM7. PCIe 레인 대역폭은 PCI-SIG 표. 링크는 맨 아래 "수치 출처"에.
> **계산으로 확정한 값**: 회전 대기 = 60,000ms / rpm, 랜덤 접근 시간 = 탐색 + 회전 대기 + 전송, 그리고 거기서 나오는 IOPS 상한. 본문에 식을 같이 적어 둔다 — 외울 값이 아니라 유도할 값이다.
> **자릿수로만 적는 값**: 용량당 가격비(데이터시트에 없다), NAND 내부 시간과 적층 수(-> nand-flash 정본).
> SSD 내부(FTL, GC, Write Amplification)는 [nand-flash](../nand-flash/)가 정본이라 여기서는 접근 특성 수준으로만 다룬다.

## 전체 흐름

```text
[HDD]  플래터가 돌고 헤드가 움직여 읽는다 -> 접근 시간 = 탐색 + 회전 대기 + 전송
       -> 원하는 위치가 어디냐에 따라 ms 단위로 달라진다 = 순차는 빠르고 랜덤은 느리다
   |
[SSD]  기계 부품이 없고 수십 개 die가 병렬로 페이지를 읽는다 -> 위치와 무관하게 수십~수백 us
       -> 랜덤 읽기에서 HDD와의 격차가 가장 크게 벌어진다 (지연 약 100배, IOPS 수천 배)
       -> 대신 쓰기는 덮어쓸 수 없어 FTL, GC, WAF라는 다른 비용이 있다 (nand-flash)
   |
[최신]  HDD는 용량만 커지고 회전수는 그대로 -> 용량당 IOPS는 계속 나빠진다 (SMR은 랜덤 쓰기를 더 못 받는다)
       SSD는 층을 쌓고 셀당 비트를 늘려 싸지고, NVMe로 병렬성을 더 끌어낸다 (QLC는 읽기 강점 유지, 쓰기 수명 약화)
   |
[기준]  매체는 "데이터의 접근 패턴"으로 고른다
       순차로 쓰고 드물게 통째로 읽는 데이터(append-only 로그, 백업, 원본 보존) -> HDD
       흩어진 키를 사람이 기다리며 조회하는 데이터(인덱스, 상세 조회, 검색 세그먼트) -> SSD
       둘 다인 데이터 -> 전량은 HDD, 조회에 필요한 선별본만 SSD (계층 분리)
```

한 문장으로: **HDD와 SSD의 격차는 "얼마나 많이"가 아니라 "어디를 읽느냐"에서 벌어지고, 그래서 매체 선택은 용량이 아니라 접근 패턴으로 한다.**

## 1. HDD - 기계가 움직여야 읽는다

### 먼저 알아야 할 것

- 플래터(원판)가 분당 5,400\~7,200회(서버용은 10,000\~15,000회) 돈다.
- 데이터는 동심원 트랙 위의 섹터에 있고, 암 끝의 헤드가 트랙 위로 이동해 지나가는 섹터를 읽는다.
- 한 번의 읽기에 드는 시간 = **탐색(seek, 헤드 이동) + 회전 대기(원하는 섹터가 헤드 밑에 올 때까지) + 전송**.

### 왜 순차는 빠르고 랜덤은 느린가

```text
순차 읽기:  헤드 한 번 이동 -> 트랙을 따라 연속 섹터를 그대로 읽음      -> 전송 시간만 든다 (180~300MB/s, 바깥 트랙 기준)
랜덤 읽기:  읽을 때마다 [탐색 평균 8ms] + [회전 대기 평균 4.2ms]        -> 4KB 하나에 약 12ms
            (전송은 4KB / 250MB/s = 0.016ms. 1%도 안 된다 - 랜덤은 위치 찾기가 전부다)
            큐 깊이 1이면 1000 / 12.2 = 초당 약 80번. 데이터시트 측정값(QD16~32)도 168~212 IOPS
```

- 회전 대기는 물리 법칙이다. 7,200rpm이면 60,000ms / 7,200 = 한 바퀴 8.33ms, 평균 반 바퀴 4.17ms. 데이터시트가 적는 "average latency 4.16ms"가 이 값이다. 어떤 컨트롤러도 이 아래로 못 내린다. 10,000rpm이면 3.0ms, 15,000rpm이면 2.0ms로 줄지만 자릿수는 그대로다.
- 그래서 HDD 성능은 **지역성**(locality)에 기댄다. 다음에 읽을 것이 지금 읽은 것 근처에 있어야 한다. OS의 readahead(앞을 미리 읽어 두기), 디스크 스케줄러의 엘리베이터 알고리즘(헤드 이동 방향으로 요청을 정렬), NCQ(디스크가 큐 안의 요청 순서를 회전 위치에 맞게 재배열)는 전부 "랜덤을 순차처럼 보이게" 하는 장치다.
- 반대로 말하면, **요청이 서로 아무 관계 없는 위치로 흩어지면 이 장치들이 전부 무력해진다.** 흩어진 키로 한 건씩 찾는 조회가 그 경우다.

## 2. SSD - 위치가 의미 없다

### 먼저 알아야 할 것

- 움직이는 부품이 없다. NAND 페이지(4\~16KB)를 읽는 데 수십 us, 컨트롤러가 수십 개 die에 요청을 동시에 뿌린다.
- 호스트가 보는 주소와 실제 NAND 위치는 FTL이 매핑 테이블로 이어 준다. 어느 주소든 조회 비용이 거의 같다.
- 자세한 내부 구조(페이지/블록, 덮어쓰기 불가, GC, WAF)는 [nand-flash](../nand-flash/).

### 접근 특성

```text
랜덤 4KB 읽기:   SATA 약 10만 IOPS, NVMe 89만~270만 IOPS   지연 78~125us (QD1 평균)
순차 읽기:       SATA 550MB/s, NVMe PCIe 4.0 약 6.8GB/s, PCIe 5.0 약 14GB/s
```

- 랜덤 읽기가 강한 이유는 탐색이 없어서만이 아니다. 요청이 여러 die로 흩어질수록 **병렬성이 오히려 올라간다**. 큐 깊이가 깊어야 이 병렬성이 나오고, NVMe가 SATA보다 빠른 이유의 하나가 큐가 훨씬 깊다는 점이다.
- 약점은 쓰기 쪽이다. 제자리에 덮어쓸 수 없어 새 페이지에 쓰고 옛 페이지를 무효화하며, 흩어진 랜덤 쓰기는 GC 복사량(WAF)을 키워 성능과 수명을 같이 깎는다. **HDD의 "순차 vs 랜덤" 격차가 SSD에서는 "순차 쓰기 vs 랜덤 쓰기"로 자리를 옮긴다.** 랜덤 읽기에는 이 비용이 없다.
- 순차 성능은 SLC 캐시가 소진되면 급락하므로(nand-flash 3절), 대량 지속 쓰기 워크로드는 카탈로그 수치가 아니라 캐시 고갈 후 수치를 본다.

## 3. 격차는 어디서 벌어지는가 - 수치 정리

고정 차원(매체 x 접근 유형) 비교이므로 표로 둔다. 자릿수만 보라.

| | HDD (7,200rpm) | SSD (NVMe) | 격차 |
|---|---|---|---|
| 랜덤 읽기 지연 | 약 12ms (탐색 8 + 회전 4.2) | 0.08\~0.13ms | **약 100배** |
| 랜덤 4KB 읽기 IOPS | 168\~212 | 89만\~270만 | 수천 배 (데이터시트 최대치끼리면 1만 배를 넘는다) |
| 순차 읽기 대역폭 | 180\~300MB/s | 6.8\~14GB/s | 20\~80배 |
| 용량당 가격 | 낮다 | 높다 | 데이터시트에 없는 값이라 배수를 적지 않는다 |
| 랜덤 쓰기 | 느림 (탐색) | 빠르나 WAF, 수명 비용 | |

읽어야 할 것은 두 가지다.

1. **순차 대역폭 격차(수십 배)보다 랜덤 격차(수천 배)가 훨씬 크다.** 순차 워크로드라면 HDD도 "충분히 빠른" 경우가 많고, 랜덤 워크로드라면 HDD는 자릿수가 다르게 느리다.
2. **HDD의 랜덤 지연 약 12ms는 사람이 체감하는 단위다.** 한 화면을 그리는 데 흩어진 키를 100번 읽으면 1.2초다. 같은 일을 SSD는 10ms 남짓에 끝낸다.

## 4. 최신 HDD, SSD에서 달라진 것과 달라지지 않은 것

### HDD - 용량은 커졌고 회전은 그대로다

- **헬륨 충전**: 공기보다 저항이 작아 플래터를 더 얇고 많이 넣는다. 대용량 드라이브의 기본이 됐다.
- **SMR(Shingled Magnetic Recording)**: 트랙을 기와처럼 겹쳐 써서 밀도를 올린다. 겹친 트랙 하나를 고치려면 뒤쪽 트랙까지 다시 써야 하므로 **랜덤 덮어쓰기가 매우 느리다**. 순차로 쓰고 통째로 읽는 아카이브용이며, 일반 용도로 잘못 사면 지속 랜덤 쓰기에서 성능이 무너진다. 기존 방식은 CMR(PMR)이라 부른다.
- **HAMR / MAMR**: 레이저 열 또는 마이크로파로 기록 지점만 잠시 약하게 만들어 더 작은 비트를 쓴다. 에너지 보조 기록(WD의 EAMR)은 이미 24TB급 드라이브에 들어가 있고, HAMR(Seagate Mozaic)은 28\~32TB 드라이브로 나와 있다.
- **듀얼 액추에이터**: 암을 두 벌로 나눠 독립 동작시켜 IOPS를 약 2배로 올린다(데이터시트 4K QD16 랜덤 읽기: 단일 액추에이터 168\~170 -> 듀얼 304). 그래도 수백 IOPS 수준이다.
- **달라지지 않은 것**: 회전수. 용량은 수십 TB로 갔는데 IOPS는 그대로다 - 한 데이터시트 안에서 24TB 드라이브와 32TB 드라이브의 랜덤 읽기 IOPS가 똑같이 170으로 적혀 있다. 그래서 **용량당 IOPS(TB당 초당 몇 번 읽을 수 있나)는 세대마다 나빠진다.** 큰 HDD 하나에 랜덤 워크로드를 몰아넣는 것은 갈수록 더 나쁜 선택이 된다.

### SSD - 싸졌고 병렬성이 늘었고 쓰기 수명은 줄었다

- **3D 적층**: 축소 대신 층을 쌓아(200\~300층) 용량당 가격을 계속 내린다(nand-flash 4절).
- **TLC -> QLC**: 셀당 비트를 늘려 더 싸진다. **랜덤 읽기 강점은 유지**되지만 P/E 수명이 크게 줄고 SLC 캐시 밖의 지속 쓰기가 느리다. 읽기 위주 대용량(콜드에 가까운 데이터, 읽기 캐시)에 맞고 쓰기 집중 워크로드에는 내구 등급(DWPD)을 봐야 한다.
- **NVMe, PCIe 4.0/5.0**: SATA의 얕은 큐와 대역폭 한계를 벗어나 die 병렬성을 그대로 끌어낸다. 랜덤 IOPS의 자릿수가 한 단계 올라간 것은 매체가 아니라 인터페이스 덕이 크다.
- **DRAM-less + HMB**: 저가형은 매핑 테이블 캐시가 작아 대용량에 랜덤 접근을 흩뿌리면 순차 수치와 달리 급락한다(nand-flash 6절). "SSD니까 랜덤에 강하다"가 항상 참은 아니다.
- **ZNS, FDP**: 호스트가 순차 zone으로 쓰게 하거나 배치 힌트를 주어 WAF를 줄이는 인터페이스. append-only 소프트웨어와 짝이 맞는다(nand-flash [Claude 추가] D절).
- **달라지지 않은 것**: 덮어쓰기 불가와 유한 수명. 싸질수록(QLC) 이 제약은 더 세진다.

### 둘 사이의 자리

- 큰 흐름은 "HDD는 용량, SSD는 접근"으로 역할이 갈라지는 쪽이다. 용량당 가격 격차가 좁혀지고 있어 데이터센터에서는 SSD 단일 계층도 늘고 있지만, 수십 TB급 콜드 데이터의 단가는 아직 HDD가 앞선다(시점에 따라 다름, 확인 필요).
- 메모리도 한 층이다. 랜덤 읽기의 hot set이 RAM 페이지 캐시에 들어가면 매체가 뭐든 대부분 메모리에서 끝난다. 반대로 hot set이 RAM보다 크면 캐시 미스마다 매체 지연이 그대로 드러나고, 그때 HDD와 SSD의 100배 차이가 응답 시간의 꼬리(p99)로 나타난다.

## 5. 데이터 특성으로 매체를 고르는 기준

### 먼저 알아야 할 것 - 워크로드를 네 축으로 본다

1. **접근 패턴**: 순차인가 랜덤인가. 키가 연속인가 흩어져 있는가.
2. **지연 요구**: 사람이 기다리는 경로인가, 배치인가.
3. **쓰기 패턴**: 뒤에 붙이기만 하는가(append-only), 제자리 덮어쓰기가 많은가.
4. **용량 대비 비용과 보존 기간**: 얼마나 큰가, 얼마나 오래 두는가, 얼마나 자주 다시 읽는가.

### 판단 순서

```text
1. 접근이 순차인가?
   예  -> HDD 후보. 순차 대역폭은 HDD도 충분한 경우가 많다. 보존 위주면 SMR도 된다.
   아니오 -> 2로
2. 그 랜덤 읽기를 사람이 기다리는가?
   예  -> SSD. HDD의 약 12ms x 조회 횟수가 그대로 응답 시간이 된다.
   아니오(배치) -> 3으로
3. 랜덤 읽기의 hot set이 메모리에 들어가는가?
   예  -> HDD + 캐시로 버틸 수 있다. 단, 캐시 미스의 꼬리 지연을 감수한다.
   아니오 -> SSD.
4. 쓰기가 제자리 덮어쓰기 위주인가?
   예  -> SSD라도 WAF와 수명(DWPD)을 확인한다. 가능하면 append-only 구조(로그, LSM)로 바꿔 순차 쓰기로 만든다.
5. 필요한 용량이 SSD 예산을 넘는가?
   예  -> 매체를 늘리는 대신 데이터를 가른다. 전량은 HDD, 조회에 실제 필요한 선별본만 SSD.
```

### 데이터 종류별로 놓으면

- **append-only 로그, WAL, 이벤트 스트림, 백업, 원본 보존용 lake**: 순차로 쓰고 드물게 통째로 읽는다 -> HDD. Kafka가 HDD에서도 빠른 이유가 이것이다([kafka-why-fast](../kafka-why-fast/)).
- **인덱스, 키 기반 상세 조회, 검색 엔진 세그먼트, DB 페이지(랜덤 읽기), 사용자 응답 경로 전부**: 흩어진 위치를 사람이 기다리며 읽는다 -> SSD.
- **랜덤 쓰기가 많은 데이터(카운터, 세션, 자주 갱신되는 행)**: SSD + 내구 등급 확인, 또는 LSM처럼 쓰기를 순차로 바꾸는 저장 구조([lsm-tree](../lsm-tree/)).
- **같은 데이터가 두 얼굴을 가질 때**(전량은 보존해야 하고, 그중 일부만 빠르게 조회해야 할 때): 전량은 HDD에 원본 그대로, 조회에 필요한 필드만 뽑아 SSD의 인덱스로. 계층을 나누면 SSD 용량이 "전체 크기"가 아니라 "조회에 필요한 크기"로 줄어든다.

## 6. 예제 - 두 단으로

### 쉬운 예 - 레코드판과 플레이리스트

레코드판은 바늘을 원하는 곡 위치로 옮겨야 한다. 앨범을 처음부터 끝까지 듣는 것(순차)은 문제없지만, 여러 판에 흩어진 곡을 한 곡씩 골라 듣는 것(랜덤)은 판을 갈고 바늘을 옮기는 시간이 곡마다 든다. 디지털 플레이리스트는 어느 곡이든 바로 튼다. 곡이 많아서 느린 게 아니라 **어디 있는 곡을 어떤 순서로 트느냐**가 속도를 정한다.

### 같은 구조를 실무로 - 원본 전량과 조회용 선별본

똑같은 구조다. 수십억 행의 원본을 파일로 받아 그대로 적재해 두는 것은 앨범을 통째로 듣는 일이다. 순차로 쓰고 가끔 통째로 다시 읽으므로 HDD로 충분하다. 반면 사용자가 번호 하나로 상세를 조회하는 것은 흩어진 곡을 한 곡씩 고르는 일이다. 키가 연속이지 않아 매 조회가 랜덤 액세스이고, 사람이 기다리므로 HDD의 약 12ms가 그대로 체감된다. 그런데 전량을 SSD에 둘 예산이 없다면 매체를 늘릴 게 아니라 데이터를 가른다. 원본 전량은 HDD lake에 두고, 조회에 실제 필요한 필드만 뽑아 SSD의 인덱스와 조회용 저장소에 둔다. 그러면 SSD가 감당할 크기는 "전체"가 아니라 "조회에 필요한 만큼"이 된다.

## 현장에서 만나는 상황

- "디스크가 큰데 왜 느리지" - 용량과 IOPS는 다른 축이다. 큰 HDD 하나는 용량당 IOPS가 가장 나쁜 구성이다.
- "SSD로 바꿨는데 랜덤이 안 빨라진다" - DRAM-less에 큰 용량, 얕은 큐(동시 요청 1\~2개), 또는 hot set이 원래 RAM에 있었던 경우를 의심한다.
- "HDD에 랜덤 쓰기 배치를 돌리면 밤새 안 끝난다" - 순차로 정렬해 쓰거나(키 순 정렬 후 적재), 쓰기를 append-only로 바꾸거나, 그 부분만 SSD로 옮긴다.
- "아카이브용 HDD를 샀는데 랜덤 쓰기에서 죽는다" - SMR인지 확인한다.
- "SSD가 꽉 차니 느려진다" - OP 소진과 SLC 캐시 고갈이 겹친 것이다(nand-flash 8절).

## 핵심 문장

- HDD의 접근 시간은 탐색 + 회전 대기라 위치에 따라 ms 단위로 달라지고, SSD는 위치와 무관하게 수십\~수백 us다.
- 격차는 순차(수십 배)가 아니라 랜덤 읽기(지연 약 100배, IOPS 수천 배)에서 벌어진다.
- HDD의 순차 vs 랜덤 격차는 SSD에서 순차 쓰기 vs 랜덤 쓰기 격차로 자리를 옮긴다. 랜덤 읽기에는 그 비용이 없다.
- 최신 HDD는 용량만 커지고 회전은 그대로라 용량당 IOPS가 나빠지고, 최신 SSD는 싸지는 대신 쓰기 수명이 줄어든다.
- 매체는 용량이 아니라 접근 패턴으로 고른다. 순차로 쓰고 통째로 읽으면 HDD, 흩어진 키를 사람이 기다리며 읽으면 SSD.
- 용량이 예산을 넘으면 매체가 아니라 데이터를 가른다. 전량은 HDD, 선별본만 SSD.

## 관련 자료

- [nand-flash](../nand-flash/) - SSD 내부(FTL, GC, WAF). 이 문서 2절과 4절의 근거.
- [kafka-why-fast](../kafka-why-fast/), [lsm-tree](../lsm-tree/) - append-only가 매체를 가리지 않고 유리한 이유.
- [striping](../striping/) - 여러 매체에 나눠 병렬성을 얻는 쪽.
- 적용 사례: [포트폴리오 - 랜덤 액세스 워크로드와 저장 매체](../../../portfolio/k-brand-guard/01_저장소_계층_설계와_레거시_통합/문제상황/03_랜덤_액세스_워크로드와_저장_매체/post.md), [접근 패턴별 계층 분리](../../../portfolio/k-brand-guard/01_저장소_계층_설계와_레거시_통합/해결과정/04_접근_패턴별_계층_분리/post.md)

## 수치 출처

본문의 값은 전부 아래 제조사 데이터시트에서 가져왔거나, 그 값으로부터 계산했다.

**HDD**

- [Seagate Exos X24 데이터시트 (DS2080)](https://www.seagate.com/content/dam/seagate/en/content-fragments/products/datasheets/exos-x24/exos-x24-DS2080-2307US-en_US.pdf) - 7200RPM, 최대 지속 전송률 285MB/s, `Random Read/Write 4K QD16 WCD (IOPS) 168/550`.
- [Seagate Exos M 데이터시트 (DS2045-4)](https://www.seagate.com/content/dam/seagate/en/content-fragments/products/datasheets/exos-m-v1-2/exos-m-v1-2-dsmDS2045-4-2504US-en_US.pdf) - HAMR(Mozaic) 32/30/28/24TB, 네 용량 모두 `Random Read/Write 4K QD16 WCD (IOPS) 170/350`, `Average Latency 4.16ms`. [Mozaic 소개](https://www.seagate.com/innovation/mozaic/)가 "harnesses HAMR technology"라 적는다.
- [Seagate Exos 2X18 데이터시트 (DS2093)](https://www.seagate.com/www-content/datasheets/pdfs/exos-2x18-DS2093-1-2202US-en_US.pdf) - 듀얼 액추에이터(MACH.2), `Random Read/Write 4K QD16 (IOPS) 304/560`, 최대 지속 전송률 554MB/s, "up to 2x the performance of an enterprise single-actuator" 3.5" HDD.
- [Seagate Exos 10E2400](https://www.seagate.com/files/www-content/datasheets/pdfs/exos-10e2400-DS1959-6-2004US-en_US.pdf) - 10,000RPM, `Average Latency 2.9ms`, `Sustained Transfer Rate (Outer to Inner Diameter) 266 to 130 MB/s`(바깥/안쪽 트랙 차이의 근거). [Exos 15E900](https://www.seagate.com/files/www-content/datasheets/pdfs/ex-os-15-e-900-DS1958-1-1709US-en_US.pdf) - 15,000RPM, `Average Latency 2.0ms`.
- [WD Ultrastar DC HC580 데이터시트](https://documents.westerndigital.com/content/dam/doc-library/en_us/assets/public/western-digital/product/data-center-drives/ultrastar-dc-hc500-series/data-sheet-ultrastar-dc-hc580.pdf) - 7200RPM, `Latency average 4.16ms`, 최대 지속 전송률 298MB/s, `Random Read 4KB QD=32 212 IOPS`, SATA 인터페이스 최대 600MB/s. EAMR을 쓴 24TB 드라이브다. [제품 매뉴얼](https://documents.westerndigital.com/content/dam/doc-library/en_us/assets/public/western-digital/product/data-center-drives/ultrastar-dc-hc500-series/product-manual-ultrastar-dc-hc580-sata-oem-spec.pdf) Table 5가 `7200 RPM | 한 바퀴 8.3ms | 평균 4.16ms`로 계산 결과를 그대로 싣는다.
- [WD Ultrastar He10 데이터시트](https://documents.westerndigital.com/content/dam/doc-library/en_us/assets/public/western-digital/product/data-center-drives/ultrastar-hdd-sata-series/ultrastar-he10/data-sheet-ultrastar-he10.pdf) - `Seek time (read/write, ms, typical) 8.0/8.6`. **탐색 시간을 아직 싣는 드물어진 데이터시트**라 랜덤 접근 시간 계산의 탐색 항을 여기서 가져왔다.
- [Toshiba MG 시리즈 데이터시트](https://www.toshiba-storage.com/wp-content/uploads/2019/09/TOSH_DS_MG_Series_print.pdf) - 7200RPM, `Average Latency 4.2ms`, `Average Seek Time read 8.5ms / write 8.5~9.5ms`, 지속 전송률 184\~260MB/s. 탐색 시간의 두 번째 출처.
- [Seagate BarraCuda 데이터시트](https://www.seagate.com/content/dam/seagate/migrated-assets/www-content/datasheets/pdfs/3-5-barracudaDS1900-14-2007US-en_US.pdf) - 데스크톱 드라이브의 5400RPM / 7200RPM.

**SSD**

- [Samsung PM893 데이터시트](https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_SSD_PM893_Data_Sheet_Rev1.0.pdf) - SATA 6Gb/s, `Sequential Read 550 MB/s`, `4KB Ran. Read (QD32) 98 KIOPS`.
- [WD·SanDisk Ultrastar DC SN655 데이터시트](https://documents.sandisk.com/content/dam/asset-library/en_us/assets/public/western-digital/product/data-center-drives/ultrastar-nvme-series/data-sheet-ultrastar-dc-sn655.pdf) - PCIe Gen4 x4, `Read IOPS (max, Rnd 4KiB) 890K~1100K`, `Read Throughput (max, Seq 128KiB) 6,800MB/s`, **`Read Latency 78~125 µS`(각주: "Average random read latency at 4KiB, QD=1")**. SSD 랜덤 읽기 지연의 출처.
- [Samsung PM9A3 데이터시트](https://image.semiconductor.samsung.com/resources/data-sheet/samsung_ssd_pm9a3_data_sheet_rev1_0.pdf) - PCIe Gen4 x4, `4KB Ran. Read (QD32) 580~1,100 KIOPS`, `Sequential Read 6,500~6,900 MB/s`.
- [Kioxia 엔터프라이즈 SSD 데이터시트 (CM7 시리즈)](https://americas.kioxia.com/content/dam/kioxia/shared/business/ssd/enterprise-ssd/asset/datasheet/EnterpriseSSD_DataSheet_E.pdf) - PCIe Gen5 x4, `Sequential Read 최대 14,000 MB/s`, `Random Read 최대 2,700 KIOPS`.
- PCIe 레인 대역폭: PCI-SIG 표([Kioxia FAQ Table 1](https://www.kioxia.com/content/dam/kioxia/shared/business/ssd/asset/KIOXIA_What_You_Need_To_Know_About_PCIe_4_NVMe_SSDs_FAQ_v2_6.pdf)에 "Source: PCI-SIG"로 재수록) - PCIe 4.0 = 16.0 GT/s, x4에서 7.88GB/s. PCIe 5.0 = 32.0 GT/s, x4에서 15.75GB/s. 위 SSD들의 6.8\~14GB/s는 이 이론 상한의 85\~90%다.
