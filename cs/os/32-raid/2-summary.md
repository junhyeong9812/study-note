# os/32-raid — 디스크 여러 개를 하나처럼, 하나가 죽어도 살아 있게 — 정리 (힌트)

## 해결하는 문제

디스크 한 개에는 세 가지 한계가 있다.

```text
  한계         디스크 1개                     원하는 것
  용량         디스크 크기까지                  여러 개를 합친 큰 볼륨
  성능         그 디스크의 IOPS·대역폭까지        여러 개에 나눠 병렬로
  신뢰성        죽으면 전부 잃음                  하나(또는 둘)가 죽어도 계속
```

**RAID**는 디스크 여러 개를 묶어 파일 시스템에는 **디스크 하나처럼** 보이게 한다.\
안에서는 블록을 나눠 놓고(striping), 복사하거나(mirroring), 패리티를 계산한다(parity).

  - *RAID(Redundant Array of Inexpensive Disks)*: 여러 디스크를 한 논리 디스크로 묶는 방식이다. 하드웨어 컨트롤러로도, 소프트웨어(리눅스 md)로도 만든다(OSTEP 38).

쉬운 예: 책 한 권을 여러 사람이 나눠 보관한다.
- 장을 번갈아 나눠 주면(0) 빨리 복사할 수 있지만, 한 사람이 잃으면 책이 망가진다.
- 두 사람이 같은 장을 가지면(1) 한 사람이 잃어도 되지만, 보관 공간이 두 배다.
- 세 사람이 장을 나눠 갖고 네 번째 사람이 "검산 쪽지"(패리티)를 가지면(5) 누구 하나가 잃어도 나머지로 되살린다.

똑같은 구조다.\
패리티는 XOR 한 번으로 만들고, XOR 한 번으로 잃은 조각을 되살린다.

실무 예:
- 디스크 하나가 죽었는데 서비스는 계속 돈다. 대신 **재구축**하는 몇 시간 동안 느리다. 그 사이 두 번째 디스크가 죽으면 전부 잃는다.
- 정전 뒤 RAID5가 "dirty"라며 자동으로 안 올라온다(write hole 보호).

## 동작·원리

### 줄무늬(striping) — RAID 0

```text
  디스크 0   디스크 1   디스크 2   디스크 3
    0         1         2         3        <- 스트라이프 0
    4         5         6         7        <- 스트라이프 1
    8         9        10        11
  논리 블록 A -> 디스크 = A % 4, 디스크 안 위치 = A / 4
```

- 블록을 디스크에 번갈아 놓는다. 큰 순차 I/O와 많은 랜덤 I/O가 모든 디스크에 퍼진다(OSTEP 38.4).
- 여러 블록을 한 디스크에 연속으로 두는 단위를 **청크(chunk)**라 한다. 청크가 크면 한 파일이 적은 디스크에 몰리고, 작으면 한 요청이 여러 디스크로 나뉜다(OSTEP 38.4).
- 중복이 없다. **디스크 하나만 죽어도 전체 데이터를 잃는다**.

### 거울(mirroring) — RAID 1, RAID 10

```text
  RAID 10 (1+0: 거울 쌍을 줄무늬로)
  디스크 0   디스크 1   디스크 2   디스크 3
    0         0         1         1
    2         2         3         3
    4         4         5         5
```

- 블록마다 사본을 둘 둔다. 읽기는 어느 쪽에서 해도 되고, 쓰기는 두 곳에 모두 한다(OSTEP 38.5).
- 거울 쌍을 줄무늬로 묶은 것이 RAID 10(1+0), 줄무늬 둘을 거울로 묶은 것이 RAID 01(0+1)이다(OSTEP 38.5).
- 용량은 절반이다. 디스크 하나는 확실히 견디고, 운이 좋으면(쌍마다 하나씩) N/2개까지 견딘다(OSTEP Figure 38.8).
- 리눅스 md RAID10은 사본 수와 배치(near·far·offset)를 고를 수 있다(md(4)).

### 패리티 — RAID 4, RAID 5

```text
  RAID 4 (패리티 디스크 고정)             RAID 5 (패리티를 돌려 놓음)
  D0  D1  D2  D3  P                    D0  D1  D2  D3  D4
   0   1   2   3  P0                    0   1   2   3  P0
   4   5   6   7  P1                    5   6   7  P1   4
   8   9  10  11  P2                   10  11  P2   8   9
  P0 = 0 XOR 1 XOR 2 XOR 3
  디스크 1 사망 -> 1 = 0 XOR 2 XOR 3 XOR P0
```

- **XOR 패리티**: 스트라이프의 데이터 블록을 모두 XOR한 값이다. 1의 개수가 짝수가 되게 맞춘다(OSTEP 38.6).
- 한 디스크가 죽으면 남은 블록과 패리티를 모두 XOR해 잃은 블록을 다시 만든다(md(4) RAID4).
- 로컬 재현(C, 8바이트 블록 3개 + 패리티, 예시): 디스크 1을 지우고 XOR로 되살리자 원래 값과 같았다(`match=1`).

**작은 쓰기 문제(small-write problem)**

```text
  블록 4 하나만 고치기 (빼기 방식)
    읽기: 옛 D4, 옛 P1                    (2 I/O)
    P1' = P1 XOR 옛D4 XOR 새D4
    쓰기: 새 D4, 새 P1'                   (2 I/O)
  -> 논리 쓰기 1번 = 물리 I/O 4번
```

- 스트라이프 전체를 다시 읽지 않고 **빼기(subtractive) 패리티**로 계산한다: `P_new = (C_old ⊕ C_new) ⊕ P_old`(OSTEP 식 38.1).
- RAID 4는 모든 작은 쓰기가 **패리티 디스크 하나**를 거친다. 그 디스크가 병목이 되어 쓰기가 직렬화된다(OSTEP 38.6).
- RAID 5는 패리티를 디스크마다 돌려 놓아 이 병목을 없앤다. 그래도 쓰기 한 번에 I/O 4번이라 작은 랜덤 쓰기 처리량은 N·R/4다(OSTEP 38.7).
- 스트라이프 전체를 한 번에 쓰면(full-stripe write) 읽기 없이 패리티를 계산할 수 있다. 큰 순차 쓰기나 LFS류가 유리한 이유다(OSTEP 43.13).

### 두 개까지 견디기 — RAID 6

- 패리티를 둘(P, Q) 둔다. **아무 디스크 둘**을 잃어도 데이터를 잃지 않는다. N개 데이터에 N+2 디스크가 필요하다(md(4) RAID6).
- P는 XOR, Q는 갈루아 체 GF(2⁸) 연산으로 만든다(H. Peter Anvin, "The mathematics of RAID-6"). 커널 인터페이스는 `raid6_gen_syndrome`·`raid6_recov_2data`다(include/linux/raid/pq.h).
- 평소·디스크 1개 고장 때 성능은 RAID5와 비슷하고, 2개 고장 상태에서는 매우 느리다(md(4)).

### 한눈에 비교 (OSTEP Figure 38.8, N = 디스크 수, B = 디스크 용량)

| | RAID 0 | RAID 1 | RAID 4 | RAID 5 |
|---|---|---|---|---|
| 용량 | N·B | N·B/2 | (N−1)·B | (N−1)·B |
| 견디는 고장 | 0 | 1 확실(운 좋으면 N/2) | 1 | 1 |
| 랜덤 읽기 | N·R | N·R | (N−1)·R | N·R |
| 랜덤 쓰기 | N·R | N/2·R | R/2 | N/4·R |
| 쓰기 지연 | T | T | 2T | 2T |

- R은 디스크 하나의 랜덤 I/O 대역폭, T는 요청 하나의 시간이다. 모델을 단순화한 비교다(OSTEP 38.8).

### 재구축 — 가장 위험한 시간

```text
  디스크 2 사망 -> degraded (중복 없음)
    |  새 디스크(또는 핫 스페어) 투입
    v
  재구축: 남은 디스크 전부를 처음부터 끝까지 읽어 XOR -> 새 디스크에 기록
    |  이 동안: 읽기마다 XOR 계산 -> 느림 / 남은 디스크에 부하 집중
    |  이 동안 디스크 하나 더 고장, 또는 읽을 수 없는 섹터(LSE) 발견 -> 그 스트라이프 복구 불가
    v
  완료 -> 다시 중복 있음
```

- 재구축 중 다른 디스크에서 **잠재 섹터 오류(LSE)**를 만나면 그 블록을 되살릴 수 없다. 그래서 패리티를 하나 더 두는 설계(NetApp RAID-DP, RAID6)가 나왔다(OSTEP 45.2).
- 규격 상한으로 가늠해 보기(예시): 데이터시트의 복구 불가 읽기 오류율이 "10¹⁴비트당 1회 미만"이다(WD Red Plus 제품 브리프). 4 TB 디스크 4개 RAID5에서 한 개가 죽으면 남은 3개 12 TB ≈ 9.6×10¹³비트를 읽는다. 상한 기준 기대 오류 수는 약 1회다. 규격 값은 "미만"의 상한이므로 이 계산은 최악의 추정이다. 실제 드라이브의 오류율 분포는 확인하지 못했다 [?].
- md는 재구축 속도를 `/proc/sys/dev/raid/speed_limit_min`·`max`(KiB/s)로 조절한다. 작성 환경 기본값은 1000·200000이었다(예시). 배열마다 `md/sync_speed_min`·`max`로 덮어쓸 수 있다(md.rst).

### write hole — 데이터와 패리티가 따로 놀 때

```text
  스트라이프:  D0  D1  D2  P      (P = D0^D1^D2)
  D0 새 값 기록 완료 --X 크래시 X-- P 기록 전
  -> P는 옛 D0 기준. 스트라이프가 조용히 불일치
  나중에 D2 디스크 사망 -> D2 = D0(새)^D1^P(옛) = 틀린 값 (에러 없이)
```

- 쓰기 하나가 여러 디스크를 고쳐야 하는 모든 RAID의 문제다. 거울에서도 두 사본이 달라질 수 있다(consistent-update problem, OSTEP 38.5).
- RAID5에서 크래시 뒤 패리티가 틀린 스트라이프가 남고, 그 상태로 디스크가 빠지면 복구한 데이터가 **조용히 틀린다**. 이것이 **RAID5 write hole**이다(raid5-ppl.rst).
- 로컬 재현(C, 예시): 데이터만 새로 쓰고 패리티를 안 고친 뒤 다른 디스크를 되살리자 원래 `CCCCCCC` 대신 `BBBBBBB`가 나왔다(`match=0`). 에러는 없었다.
- md의 대책
  - dirty(비정상 종료) **이면서** degraded인 RAID5/6은 PPL이 없으면 기본적으로 시작을 거부한다. `mdadm --assemble --force`나 모듈 파라미터 `md-mod.start_dirty_degraded=1`(루트 파일시스템용)로 강제할 수 있다. 손상 가능성은 남는다(md.rst).
  - PPL이 켜진 배열은 거부하지 않고 "starting dirty degraded array with PPL"을 남기고 시작한다(drivers/md/raid5.c `raid5_run`).
  - **PPL(Partial Parity Log)**: 쓰기 전에 부분 패리티를 로그로 남긴다. 쓰기 성능이 최대 30~40% 줄 수 있다(raid5-ppl.rst).
  - **저널(write journal) 디스크**: 데이터를 먼저 빠른 캐시 디스크에 쓰고 나서 RAID 디스크에 쓴다(raid5-cache.rst).
  - write-intent 비트맵: 크래시 뒤 전체 대신 쓰던 구간만 resync한다. PPL과 함께 쓸 수 없다(raid5-ppl.rst).

### 스크러빙 — 읽지 않는 블록도 주기적으로 읽는다

- 오래 안 읽은 블록의 오류는 재구축 때에야 드러난다. 그래서 전체를 주기적으로 읽어 확인한다(md(4) SCRUBBING, 33번).
- md: `echo check > /sys/block/mdX/md/sync_action`. 읽기 오류는 다른 디스크의 데이터로 다시 써서 고친다. 불일치는 `mismatch_cnt`에 센다(md(4)).
  - `check`는 불일치를 기록만 한다. `repair`는 RAID5/6이면 패리티를 새로 쓰고, RAID1/10이면 한 사본으로 나머지를 덮는다(md(4)). 이 동작은 **어느 쪽이 옳은지 따지지 않는다**. 그 판단은 체크섬이 있어야 가능하다(33번).
  - 깨끗한 RAID5/6의 불일치는 하드웨어 문제를 뜻한다. RAID1/10은 소프트웨어 동작(예: 스왑)으로 불일치가 보고될 수 있고 반드시 손상은 아니다(md(4)).

## 쓰이는 자료구조·알고리즘

- **XOR 패리티** — `a ⊕ a = 0`, `a ⊕ 0 = a`라서 "전부의 XOR"에서 하나를 빼면 잃은 값이 나온다. 빼기 방식 갱신 `P' = P ⊕ D_old ⊕ D_new`도 같은 성질이다.
- **리드-솔로몬 계열(GF(2⁸))** — RAID6의 Q. 두 개를 잃어도 연립식을 풀어 되살린다(Anvin).
- **주소 사상(나머지·몫)** — 논리 블록 A → (디스크 A mod N, 위치 A div N). 청크가 있으면 청크 단위로 같은 계산을 한다(OSTEP 38.4). 해시 샤딩·[systems/striping](../../systems/striping/2-summary.md)과 같은 발상이다.
- **write-intent 비트맵** — 구간마다 "쓰는 중" 비트를 먼저 디스크에 적어, 크래시 뒤 그 구간만 다시 맞춘다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **쓰기 전 로그(PPL·저널)** — 23번 저널링과 같은 WAL 규칙을 블록 장치 층에서 쓴다.

## 적용 — 풀어나가는 법

### 1. 레벨 고르기

```text
  질문                                          추천(보통)
  성능만, 데이터는 다른 곳에 있다(캐시·임시)         RAID 0
  랜덤 쓰기 많은 DB, 빠른 재구축                    RAID 10
  용량 효율 + 1개 고장, 쓰기 적음                   RAID 5 (큰 디스크면 재구축 위험 검토)
  큰 디스크·많은 디스크, 2개 고장 대비               RAID 6
```

- 어느 레벨도 **백업이 아니다**. 실수로 지운 파일·랜섬웨어·앱 버그는 모든 사본에 즉시 복제된다.

### 2. 패리티 계산 (C)

```c
/* 스트라이프의 패리티: 모든 데이터 블록의 XOR */
void parity(unsigned char *p, unsigned char **d, int ndata, size_t bs) {
    memset(p, 0, bs);
    for (int i = 0; i < ndata; i++)
        for (size_t k = 0; k < bs; k++) p[k] ^= d[i][k];
}
/* 작은 쓰기: 옛 데이터·옛 패리티만 읽어 새 패리티 계산 */
void small_write(unsigned char *p, const unsigned char *old_d, const unsigned char *new_d, size_t bs) {
    for (size_t k = 0; k < bs; k++) p[k] ^= old_d[k] ^ new_d[k];
}
```

### 3. 리눅스 md 상태 보기

```bash
cat /proc/mdstat                                  # 배열 목록, [UU_U] 같은 디스크 상태, 재구축 진행률
mdadm --detail /dev/md0                           # State(clean/degraded/resyncing), 각 디스크 상태
cat /sys/block/md0/md/degraded                    # 빠진 디스크 수 (정상 0)
cat /sys/block/md0/md/sync_action                 # idle / resync / recover / check / repair
echo check | sudo tee /sys/block/md0/md/sync_action   # 스크럽 시작 (운영 시간 외)
cat /sys/block/md0/md/mismatch_cnt                # 스크럽 뒤 불일치 섹터 수
sysctl dev.raid.speed_limit_min dev.raid.speed_limit_max   # 재구축 속도 (KiB/s)
smartctl -a /dev/sdX                              # 재할당·보류 섹터 수 (디스크 건강)
```

## 장애 시나리오와 대처

### 1. 재구축 중 두 번째 고장·URE → 배열 유실

- **현상**: 디스크 하나 교체 후 재구축하던 중 배열이 실패한다. 파일 시스템이 사라지거나 일부 파일을 못 읽는다.
- **보이는 형태**: `dmesg`에 남은 디스크의 읽기 오류(`I/O error`, `Medium Error`/`Unrecovered read error` 류), `/proc/mdstat`의 두 번째 `(F)` 표시, 앱의 `EIO`.
- **원인**
  - RAID5는 재구축 동안 중복이 없다. 남은 디스크 전부를 끝까지 읽어야 한다.
  - 그때 다른 디스크의 읽을 수 없는 섹터(LSE·URE)나 고장이 나면 그 스트라이프는 되살릴 수 없다(OSTEP 45.2).
  - 같은 시기에 산 디스크는 비슷한 시기에 늙는다는 경험칙이 있다 [?].
- **대처**
  - 큰 디스크·많은 디스크는 RAID6·RAID10을 쓴다.
  - 정기 스크럽으로 LSE를 재구축 **전에** 찾아 고친다. md 스크럽은 읽기 오류를 다른 디스크의 데이터로 다시 써서 고친다(md(4)). 현장 연구에서도 대부분의 LSE가 스크럽으로 발견되었다(OSTEP 45.1).
  - 핫 스페어를 둬 degraded 시간을 줄인다. 재구축 속도 하한을 너무 낮추지 않는다.
  - 백업에서 복구할 수 있게 한다. RAID는 백업이 아니다.

### 2. RAID5 write hole → 조용히 틀린 복구

- **현상**: 정전 뒤 한동안 문제없다가, 디스크 하나를 교체·재구축한 뒤 일부 파일 내용이 깨져 있다.
- **보이는 형태**: 재구축은 "성공". 에러 없이 틀린 데이터. 파일 시스템·DB 체크섬 오류로 뒤늦게 드러난다.
- **원인**: 크래시 순간 데이터와 패리티 중 하나만 기록되었다. 불일치한 패리티로 다른 디스크를 되살렸다(raid5-ppl.rst).
- **대처**
  - 정전 뒤에는 degraded가 되기 **전에** resync를 끝낸다(md는 dirty 배열을 resync한다).
  - PPL·저널 디스크·배터리 백업 캐시로 write hole을 막는다.
  - dirty+degraded 배열을 `--force`로 올릴 때는 손상 가능성을 전제하고 백업과 대조한다(md.rst).

### 3. degraded 상태의 성능 급락

- **현상**: 디스크 하나 고장 뒤 서비스 지연이 크게 오른다. 재구축이 시작되면 더 나빠진다.
- **보이는 형태**: `/proc/mdstat`의 `[UU_U]`와 `recovery = 12.3%` 류 진행률, `iostat -x`의 모든 멤버 `%util` 상승.
- **원인**: 죽은 디스크의 블록을 읽을 때마다 남은 디스크 전부를 읽어 XOR한다. 재구축 I/O가 서비스 I/O와 경쟁한다.
- **대처**: 재구축 속도(`speed_limit_min/max`, `sync_speed_*`)로 서비스와 복구 사이 균형을 잡는다. 너무 늦추면 위험한 degraded 시간이 길어진다.

### 4. RAID 0 한 디스크 고장 → 전부 유실

- **현상**: 디스크 하나가 죽자 볼륨 전체가 사라졌다.
- **보이는 형태**: 마운트 실패, 배열 시작 실패.
- **원인**: 줄무늬에는 중복이 없다. 큰 파일과 파일 시스템 메타데이터가 여러 디스크에 흩어져 있어, 한 디스크 몫이 빠지면 볼륨이 성립하지 않는다.
- **대처**: RAID 0에는 다시 만들 수 있는 데이터(캐시·임시·복제본의 한 노드)만 둔다.

### 5. 스크럽 `mismatch_cnt` > 0

- **현상**: 주간 스크럽 뒤 경보가 온다.
- **보이는 형태**: `/sys/block/md0/md/mismatch_cnt`가 0이 아니다. 값은 섹터 수이고 IO 단위로 더해진다(128 = 64 KB 한 번일 수 있다, md(4)).
- **원인**: RAID5/6이면 하드웨어 문제 신호다. RAID1/10은 스왑 등 소프트웨어 동작으로도 생길 수 있다(md(4)).
- **대처**: `repair`는 어느 사본이 옳은지 모른 채 맞춘다. 먼저 SMART·커널 로그를 보고, 파일 시스템·앱 수준 체크섬(33번)으로 실제 손상을 확인한다.

## 핵심 문장

- RAID 0은 줄무늬로 속도·용량을 얻고 중복이 없다. RAID 1/10은 사본으로, RAID 5/6은 패리티로 고장을 견딘다.
- 패리티는 스트라이프의 XOR이다. 하나를 잃으면 나머지의 XOR로 되살린다.
- RAID 5의 작은 쓰기는 옛 데이터·옛 패리티 읽기 + 새 데이터·새 패리티 쓰기, I/O 4번이다.
- 재구축은 남은 디스크 전부를 읽는 가장 위험한 시간이다. 그 사이 두 번째 고장이나 읽기 오류가 나면 RAID5는 데이터를 잃는다.
- write hole은 데이터와 패리티가 크래시로 어긋난 상태다. degraded와 겹치면 조용히 틀린 데이터가 나온다.
- RAID는 가용성 장치다. 백업도, 조용한 손상 감지기도 아니다.

## 관련 주제·근거

- 선행: [architecture/16-storage-media-workload](../../architecture/16-storage-media-workload/2-summary.md) — 디스크 IOPS·순차/랜덤
- 후속·연결
  - [33-data-integrity-checksums](../33-data-integrity-checksums/2-summary.md) — RAID가 못 잡는 조용한 손상, 스크러빙
  - [23-crash-consistency-and-journaling](../23-crash-consistency-and-journaling/2-summary.md) — 같은 문제(여러 블록 원자적 갱신)의 파일 시스템 판
  - [systems/striping](../../systems/striping/2-summary.md) — 분산 시스템의 스트라이핑
  - [distributed/06-replication-strategies](../../distributed/06-replication-strategies/2-summary.md)(복제)
- 교재
  - OSTEP 38장 "Redundant Arrays of Inexpensive Disks (RAIDs)" — 38.2 fail-stop, 38.4 RAID0·청크, 38.5 RAID1·consistent-update, 38.6 RAID4·빼기 패리티(식 38.1)·small-write, 38.7 RAID5, Figure 38.8 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-raid.pdf>
  - OSTEP 45장 45.1 LSE 통계, 45.2 재구축 중 LSE와 RAID-DP <https://pages.cs.wisc.edu/~remzi/OSTEP/file-integrity.pdf>
- Linux
  - md(4) — RAID4·5·6·10, RECOVERY, SCRUBBING AND MISMATCHES <https://man7.org/linux/man-pages/man4/md.4.html>
  - Documentation/admin-guide/md.rst — dirty+degraded 시작 거부·`start_dirty_degraded`, `sync_action`, `mismatch_cnt`, `sync_speed_*`, `degraded` <https://docs.kernel.org/admin-guide/md.html>
  - Documentation/driver-api/md/raid5-ppl.rst(write hole, PPL 30~40%), raid5-cache.rst(저널 디스크)
  - drivers/md/raid5.c `raid5_run()` — dirty+degraded에서 PPL이면 시작, `ok_start_degraded`면 경고 후 시작, 아니면 거부 <https://raw.githubusercontent.com/torvalds/linux/master/drivers/md/raid5.c>
  - include/linux/raid/pq.h — RAID6 P/Q syndrome
- H. Peter Anvin, "The mathematics of RAID-6" <https://www.kernel.org/pub/linux/kernel/people/hpa/raid6.pdf>
- WD Red Plus 제품 브리프 — Non-recoverable errors per bits read <1 in 10¹⁴ <https://documents.westerndigital.com/content/dam/doc-library/en_us/assets/public/western-digital/product/internal-drives/wd-red-plus-hdd/product-brief-western-digital-wd-red-plus-hdd.pdf>
- 로컬 재현(gcc 13.3): 8바이트 블록 RAID5 흉내 — XOR 재구축 성공, 빼기 패리티 갱신 뒤 재구축 성공, 패리티 미갱신(write hole) 뒤 재구축이 에러 없이 틀린 값. `/proc/sys/dev/raid/speed_limit_min/max` 확인
