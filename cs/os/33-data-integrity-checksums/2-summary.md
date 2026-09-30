# os/33-data-integrity-checksums — 디스크가 말없이 틀린 값을 줄 때 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

32번의 RAID는 "디스크가 통째로 죽는다"를 가정한다(fail-stop).\
디스크가 죽으면 누구나 안다. 그래서 사본으로 넘어가면 된다.

그런데 실제 디스크는 **일부만** 고장 난다.

```text
  고장 종류                  디스크가 하는 말          알아챌 수 있나
  잠재 섹터 오류(LSE)          "못 읽겠다" (에러)        예 — 에러가 난다
  조용한 손상(corruption)      "여기 있다" (틀린 값)     아니오 — 멀쩡한 척한다
```

- 잠재 섹터 오류는 드라이브 내부 ECC가 못 고친 섹터다. 읽으면 에러를 낸다(OSTEP 45.1).
- **조용한 손상**은 디스크가 성공을 알리면서 틀린 데이터를 준다. 원인은 펌웨어 버그로 엉뚱한 위치에 쓰기, 버스에서 깨진 채 저장 등이다(OSTEP 45.1).

  - *fail-partial 모델*: 디스크가 통째로 죽기도 하지만, 살아 있는 채 일부 블록이 읽기 불가(LSE)가 되거나 틀린 내용(손상)을 담을 수 있다는 고장 모델이다(OSTEP 45.1, Prabhakaran 외).

조용한 손상이 무서운 이유는 **복제**된다는 점이다.\
손상된 블록을 읽은 앱은 그 값을 정상으로 알고 복제본·백업에 그대로 쓴다.\
RAID1 두 사본 중 어느 것이 옳은지도 RAID는 모른다(32번).

쉬운 예: 은행 통장 사본이다.
- 원본 숫자가 번졌는데 아무도 모른 채 사본을 떴다. 사본도, 사본의 사본도 틀린 숫자다.
- 숫자마다 **검산 번호**를 옆에 적어 두면, 번진 순간 검산이 안 맞아 알아챈다.

똑같은 구조다.\
데이터와 함께 작은 **체크섬**을 저장하고, 읽을 때마다 다시 계산해 비교한다.

실무 예:
- 몇 달 된 사진·백업을 열었더니 일부가 깨져 있다. 그 사이 백업도 깨진 파일을 복사해 갔다.
- DB 복제본으로 장애 조치했더니 특정 페이지가 틀렸다. 원본 디스크에서 이미 손상된 것이 복제되었다.

얼마나 흔한가(OSTEP Figure 45.1, 약 150만 대·약 3년, Bairavasundaram 외):

| | 저가 드라이브(주로 SATA) | 고가 드라이브(SCSI·FC) |
|---|---|---|
| LSE가 한 번 이상 | 9.40% | 1.40% |
| 조용한 손상이 한 번 이상 | 0.50% | 0.05% |

## 동작·원리

### 체크섬 — 데이터 옆에 작은 요약을 둔다

```text
  쓰기:  D -----> C(D) 계산 -----> 디스크에 [D][C(D)] 저장
  읽기:  디스크에서 [D'][C] 읽기 -> C(D') 다시 계산
         C(D') == C  -> 정상
         C(D') != C  -> 손상! -> 다른 사본으로 복구 (사본이 없으면 에러 반환)
```

- 체크섬은 큰 데이터(예: 4 KB)를 작은 값(예: 4·8바이트)으로 요약한다(OSTEP 45.3).
- 요약이라 **충돌**(다른 데이터, 같은 체크섬)은 피할 수 없다. 좋은 함수는 충돌을 줄이면서 계산이 싸다(OSTEP 45.3).
- 로컬 재현(Python, 예시): `balance=1000`의 한 비트를 뒤집어 `balance=9000`을 만들었다.

```text
b'balance=9000\n' 0x6afabbf4 0x5a8af035     # CRC-32: 원본 vs 1비트 바뀐 것
bec355d7b18e77ec 7ea085b0d093021e           # SHA-256 앞 8바이트: 원본 vs 바뀐 것
```

**함수 고르기** (OSTEP 45.3, btrfs 문서)

```text
  XOR          빠름. 같은 자리 비트 두 개가 함께 바뀌면 못 잡음
  덧셈         빠름. 데이터가 밀리면(shift) 못 잡음
  Fletcher     두 합(s1, s2)으로 순서도 반영. 1비트·2비트 오류 모두, 많은 버스트 오류 검출
  CRC          데이터를 큰 이진수로 보고 약속된 값으로 나눈 나머지. 하드웨어·네트워크에서 흔함
  crc32c       btrfs 기본, ext4 메타데이터. 현대 CPU에 명령어 지원. 충돌 저항성은 없음
  xxhash       64비트, 빠르고 충돌 저항성 좋음 (btrfs, 커널 5.5+)
  SHA-256      암호학적 강도, 느림 (btrfs 5.5+, 콘텐츠 주소·중복 제거·위조 방지용)
```

- 저장 장치의 **우연한** 손상에는 CRC류로 충분하다. 누군가 **일부러** 바꿀 수 있다면 암호학적 해시(+ 서명·MAC)가 필요하다.

### 어디에 저장하나

```text
  (a) 520바이트 섹터: [데이터 512B][체크섬 8B]  -> 쓰기 1번
  (b) 체크섬 모음 블록: [C0 C1 C2 C3 C4][D0][D1][D2][D3][D4]
      -> D1 덮어쓰기 = 체크섬 블록 읽기 + 체크섬 블록 쓰기 + D1 쓰기
  (c) 부모에 저장 (ZFS·btrfs): 블록 포인터 옆에 자식의 체크섬
```

- (a)는 드라이브를 520바이트 섹터로 포맷해 섹터마다 8바이트를 더 쓴다(OSTEP 45.3).
- (b)는 어느 디스크에서나 되지만, 덮어쓰기에 읽기 1번·쓰기 2번이 든다(OSTEP 45.3).
- (c)는 아래 "잃어버린 쓰기"까지 잡는다.

### 체크섬만으로는 못 잡는 두 가지

```text
  잘못 간 쓰기 (misdirected write)          잃어버린 쓰기 (lost write)
  "블록 x에 D 써라" -> 실제로 y에 씀           "D 새 버전 써라" -> "완료" 응답, 실제로 안 씀
  y 자리: [D][C(D)]  <- 체크섬은 맞음!        자리: [D 옛 버전][C(옛)]  <- 체크섬은 맞음!
  해법: 체크섬에 (디스크 번호, 블록 번호)도      해법: 부모가 자식의 체크섬을 기억
        함께 저장 -> 읽을 때 위치 대조             부모 [ptr -> x, C(새 D)] vs 자식 C(옛) -> 불일치
```

- **잘못 간 쓰기**: 컨트롤러가 데이터를 올바르게 쓰되 엉뚱한 위치(다른 블록·다른 디스크)에 쓴다. 체크섬에 **물리 ID**(디스크·섹터 번호)를 함께 넣으면 잡는다(OSTEP 45.5).
- **잃어버린 쓰기**: 장치가 완료를 알렸지만 실제로는 기록하지 않았다. 옛 블록은 옛 체크섬과 맞고 위치도 맞아서 블록 자체의 체크섬으로는 못 잡는다(OSTEP 45.6).
  - 해법 하나: 쓰고 나서 다시 읽기(write verify). I/O가 두 배라 느리다(OSTEP 45.6).
  - 해법 둘: ZFS는 inode·간접 블록에 자식 블록의 체크섬을 넣는다. 데이터 쓰기만 잃으면 부모의 체크섬과 안 맞는다. 부모와 자식의 쓰기를 **둘 다** 잃으면 못 잡는다(OSTEP 45.6).
- 부모가 자식의 체크섬을 갖고, 그 부모의 체크섬을 다시 그 위가 갖는 구조가 **머클 트리**다. 루트 하나가 맞으면 아래 전체가 맞다.

### 스크러빙 — 안 읽는 데이터도 주기적으로 검사한다

```text
  평소 검사: 앱이 읽을 때만   -> 몇 년 안 읽는 데이터는 손상이 쌓여도 모름
  스크럽:    주기적으로 전부 읽어 체크섬 확인 -> 사본이 아직 멀쩡할 때 고침
```

- 대부분 데이터는 거의 읽히지 않는다. 검사하지 않은 데이터는 비트 부패가 **모든 사본**에 퍼질 때까지 모를 수 있다(OSTEP 45.7).
- 그래서 주기적으로 모든 블록을 읽어 체크섬을 확인한다. 흔히 매일 밤·매주 돌린다(OSTEP 45.7).
- 현장 연구에서도 대부분의 LSE가 스크럽으로 발견되었다(OSTEP 45.1).
- 체크섬이 있어야 스크럽이 "어느 사본이 옳은가"를 안다. md RAID 스크럽은 불일치만 알고 옳은 쪽은 모른다(32번).

### 리눅스 파일 시스템의 현실

```text
  ext4 (metadata_csum)   메타데이터만 crc32c        데이터 블록은 체크섬 없음
  btrfs                  데이터 + 메타데이터         기본 crc32c, 복제 프로파일이면 스크럽이 자동 수리
  ZFS                    데이터 + 메타데이터         블록 포인터에 자식 체크섬 (OSTEP 45.6)
```

- ext4의 `metadata_csum`은 모든 주요 ext4·jbd2 메타데이터 구조에 체크섬을 둔다. 알고리즘은 crc32c다(ext4 문서 checksums). 데이터 블록은 체크섬이 없다.
- 로컬 재현(16 MiB ext4 이미지, 예시)

```text
  데이터 블록 1바이트 변경 ('1'->'9', 1비트)   메타데이터(inode 12) 1바이트 변경
  debugfs cat -> balance=9000  (조용히)        debugfs cat -> Inode checksum does not match inode
  e2fsck -fn  -> exit 0, 문제 없음              e2fsck -fn  -> Inode 12 passes checks, but checksum
                                                             does not match inode.  (exit 4)
```

- btrfs는 데이터와 메타데이터를 기본으로 체크섬한다. 메타데이터는 b-트리 노드 헤더에, 데이터는 별도의 체크섬 트리에 둔다(btrfs 문서 Checksumming).
  - 기본은 crc32c다. 커널 5.5부터 xxhash·sha256·blake2b도 고를 수 있다.
  - RAID1 같은 복제 프로파일에서는 스크럽과 평소 읽기가 검증된 사본으로 손상을 자동 수리한다(btrfs 문서 Scrub).
  - `chattr +C`(NOCOW)를 준 파일은 데이터 체크섬도 꺼진다. 이 파일은 스크럽이 데이터를 검증·수리하지 못한다. systemd는 저널 파일에, libvirt 6.6+는 스토리지 풀 디렉터리에 기본으로 `+C`를 둔다(btrfs 문서 Scrub 경고).

### 끝에서 끝까지(end-to-end) — 앱도 확인한다

- 저장 장치·파일 시스템 체크섬은 **그 층 아래**의 손상만 잡는다. 메모리·네트워크·앱 버그로 이미 틀린 값을 쓰면 체크섬은 "틀린 값"을 정확히 지킨다.
- 그래서 중요한 데이터는 **만든 곳에서 체크섬을 계산해 끝까지 들고 간다**. 업로드 청크 체크섬, 백업 아카이브 해시, DB 페이지 체크섬이 그 예다.
- PostgreSQL 데이터 페이지 체크섬은 I/O 시스템의 조용한 손상을 감지한다. PostgreSQL 18 문서 기준 `initdb`의 기본값은 켜짐이다(`--no-data-checksums`로 끔). 17 문서에서는 `--data-checksums`로 켜는 선택 사항이었다. 실패는 `pg_stat_database`에 집계된다(PostgreSQL 문서 initdb).

### 비용

- 공간: 4 KB 블록마다 8바이트면 약 0.19%다(OSTEP 45.8).
- 시간: 쓸 때와 읽을 때 CPU가 체크섬을 계산한다. 어차피 하는 복사(페이지 캐시 → 사용자 버퍼)와 체크섬 계산을 한 번에 하면 줄일 수 있다(OSTEP 45.8).
- I/O: 체크섬을 데이터와 따로 저장하면 추가 읽기가 든다. 스크럽은 한가한 시간에 돌린다(OSTEP 45.8).

## 쓰이는 자료구조·알고리즘

- **CRC(다항식 나눗셈의 나머지)** — 데이터를 GF(2) 다항식으로 보고 생성 다항식으로 나눈 나머지다. OSTEP 45.3은 이를 "데이터를 큰 이진수로 보고 약속된 값으로 나눈 나머지"로 설명한다.
- **Fletcher 체크섬** — `s1 = (s1 + d_i) mod 255`, `s2 = (s2 + s1) mod 255`. 두 번째 합이 위치(순서)를 반영한다(OSTEP 45.3).
- **머클 트리(체크섬 트리)** — 부모가 자식의 체크섬을 갖는다. 잃어버린 쓰기와 위치 뒤바뀜까지 잡고, 루트 하나로 전체를 검증한다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- **물리 ID 태그** — 체크섬에 (디스크, 블록) 번호를 섞어 잘못 간 쓰기를 잡는다.
- **백그라운드 스캔(스크러빙)** — 전체를 순서대로 읽는 저우선순위 작업. 속도 제한으로 서비스 I/O와 균형을 맞춘다.

## 적용 — 풀어나가는 법

### 1. 앱에서 체크섬을 저장하고 읽을 때 확인한다

Java — `java.util.zip.CRC32C`(Java 9+).

```java
static long crc32c(byte[] b) { var c = new java.util.zip.CRC32C(); c.update(b); return c.getValue(); }

void save(Path p, byte[] data) throws IOException {
    ByteBuffer buf = ByteBuffer.allocate(8 + data.length);
    buf.putLong(crc32c(data)).put(data).flip();
    // 24번의 원자적 교체로 저장 (tmp write -> force -> ATOMIC_MOVE -> 디렉터리 force)
}
byte[] load(Path p) throws IOException {
    ByteBuffer buf = ByteBuffer.wrap(Files.readAllBytes(p));
    long stored = buf.getLong();
    byte[] data = new byte[buf.remaining()]; buf.get(data);
    if (crc32c(data) != stored) throw new IOException("checksum mismatch: " + p);  // 조용히 넘기지 않는다
    return data;
}
```

Node.js — 백업·업로드 파일은 SHA-256을 함께 보관하고 복원 때 비교한다.

```js
const crypto = require('node:crypto');
const fs = require('node:fs');
function sha256File(path) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    fs.createReadStream(path).on('data', (c) => h.update(c)).on('end', () => resolve(h.digest('hex'))).on('error', reject);
  });
}
// 백업 시 manifest에 { path, sha256 } 기록 -> 복원 시 다시 계산해 비교
```

### 2. 파일 시스템·장치 수준에서 본다

```bash
dumpe2fs -h /dev/<dev> | grep -o metadata_csum   # ext4 메타데이터 체크섬 켜짐 여부
btrfs scrub start /mnt && btrfs scrub status /mnt  # btrfs 스크럽 (체크섬 오류·수리 수)
btrfs device stats /mnt                            # 장치별 read/write/corruption 오류 누계
lsattr <파일>                                       # btrfs에서 C(NOCOW) 플래그 = 데이터 체크섬 없음
smartctl -a /dev/sdX                               # 재할당·보류 섹터, CRC 오류 카운터
cat /sys/block/md0/md/mismatch_cnt                 # md 스크럽 불일치 (32번)
```

### 3. 백업은 "복원 검증"까지가 백업이다

- 백업 시 해시를 남기고, 주기적으로 **복원해 해시를 비교**한다.
- 보존 기간을 둔다. 손상이 늦게 발견되어도 손상 전 버전이 남아 있어야 한다.

## 장애 시나리오와 대처

### 1. 비트 부패가 복제·백업까지 전파

- **현상**: 오래된 파일·레코드가 깨져 있다. 복제본도, 최근 백업도 똑같이 깨져 있다.
- **보이는 형태**: 에러가 없다. 앱 수준에서 이미지 디코딩 실패, 압축 해제 CRC 오류(`gzip: invalid compressed data--crc error` 류), 파싱 오류로 뒤늦게 드러난다.
- **원인**
  - 저장 장치가 조용히 틀린 값을 돌려주었다. ext4처럼 데이터 체크섬이 없는 층은 그대로 전달했다(로컬 재현: 데이터 1비트 변경은 `e2fsck` exit 0).
  - 앱·복제·백업이 그 값을 정상으로 알고 복사했다.
- **대처**
  - 데이터 체크섬이 있는 층을 하나 이상 둔다: btrfs·ZFS, DB 페이지 체크섬, 앱 체크섬.
  - 백업은 해시 manifest와 함께 두고, 보존 기간 안의 옛 버전을 유지한다.
  - 스크럽을 정기적으로 돌려 사본이 아직 멀쩡할 때 고친다.

### 2. RAID1 repair가 틀린 사본으로 덮어씀

- **현상**: md 스크럽 `mismatch_cnt`가 떠서 `repair`했는데, 이후 일부 파일이 깨졌다.
- **보이는 형태**: `mismatch_cnt > 0` 뒤 `repair`, 앱 수준 오류.
- **원인**: md는 블록 내용의 정답을 모른다. RAID1/10 repair는 한 사본으로 나머지를 덮는다(md(4)). 하필 손상된 쪽이 기준이 될 수 있다.
- **대처**: `repair` 전에 SMART·커널 로그로 의심 디스크를 가린다. 가능하면 체크섬이 있는 층(btrfs RAID1·ZFS mirror)이 "검증된 사본"으로 고치게 한다.

### 3. btrfs NOCOW 파일의 조용한 손상

- **현상**: btrfs RAID1인데 VM 이미지·DB 파일이 깨졌다. 스크럽은 데이터 오류를 보고하지 않았다.
- **보이는 형태**: `lsattr`에 `C` 플래그. `btrfs scrub status`는 깨끗하다.
- **원인**: `+C`(NOCOW)는 데이터 체크섬을 끈다. 어느 사본이 옳은지 몰라 손상된 사본을 그대로 읽을 수 있다(btrfs 문서 Scrub 경고).
- **대처**: NOCOW를 쓴 파일은 앱 수준 체크섬(DB 페이지 체크섬 등)에 의존한다는 것을 알고 설계한다. 필요 없으면 `+C`를 쓰지 않는다. 이미 데이터가 있는 파일은 `chattr -C`로 안 풀리니(fs/btrfs/ioctl.c — 크기 0인 일반 파일만 변경) `C` 없는 디렉터리에 새 파일로 복사해 교체한다.

### 4. 체크섬 오류가 났는데 앱이 무시

- **현상**: 로그에 가끔 checksum 오류가 찍히는데 서비스는 계속 돈다. 어느 날 복구할 사본이 없다.
- **보이는 형태**: PostgreSQL `page verification failed, calculated checksum ... but expected ...`, `pg_stat_database`의 체크섬 실패 수, btrfs 커널 메시지 `csum failed root ... ino ... off ... csum ... expected csum ... mirror N`(fs/btrfs/inode.c).
- **원인**: 감지는 했지만 경보·복구 절차가 없었다. 첫 신호는 대개 디스크 열화의 시작이다.
- **대처**: 체크섬 실패 카운터에 경보를 건다. 감지 즉시 해당 장치를 점검하고, 사본·백업에서 그 블록을 복원한다.

## 핵심 문장

- 디스크는 통째로 죽기도 하지만, 일부 섹터를 못 읽거나(LSE) 에러 없이 틀린 값을 주기도 한다(조용한 손상).
- 체크섬은 데이터 옆에 작은 요약을 저장하고 읽을 때 다시 계산해 비교한다. 우연한 손상에는 CRC류, 고의 변경에는 암호학적 해시가 맞다.
- 블록 자체의 체크섬은 잘못 간 쓰기·잃어버린 쓰기를 못 잡는다. 물리 ID와 부모에 둔 체크섬(머클 트리)이 필요하다.
- 스크러빙은 안 읽는 데이터를 주기적으로 검사해, 손상이 모든 사본에 퍼지기 전에 고친다.
- ext4는 메타데이터만 체크섬한다. 데이터 손상은 조용히 통과해 복제·백업까지 퍼질 수 있다.
- 체크섬은 자기 층 아래만 지킨다. 중요한 데이터는 만든 곳에서 끝까지 체크섬을 들고 간다.

## 관련 주제·근거

- 선행: [32-raid](../32-raid/2-summary.md) — fail-stop 가정, 재구축, md 스크럽
- 연결
  - [23-crash-consistency-and-journaling](../23-crash-consistency-and-journaling/2-summary.md) — 찢어진 페이지를 체크섬으로 감지
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — lost write와 fsync 오류
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) — 체크섬 트리
  - [network/42-large-file-upload-patterns](../../network/42-large-file-upload-patterns/2-summary.md) — 청크 체크섬
  - [reliability/README](../../reliability/README.md) — `46-disaster-recovery`(RPO/RTO·백업·복구 훈련). 미작성
- 교재
  - OSTEP 45장 "Data Integrity and Protection" — 45.1 고장 모드·Figure 45.1, 45.2 LSE, 45.3 체크섬 함수·배치, 45.5 misdirected write, 45.6 lost write·ZFS, 45.7 스크러빙, 45.8 비용 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-integrity.pdf>
  - 원 연구: Bairavasundaram 외, LSE(SIGMETRICS 2007)·데이터 손상(FAST 2008) — OSTEP [B+07], [B+08]로 인용
- 파일 시스템 문서
  - Documentation/filesystems/ext4/checksums.rst — `metadata_csum`, crc32c <https://docs.kernel.org/filesystems/ext4/checksums.html>
  - btrfs 문서 Checksumming(crc32c 기본, 5.5+ xxhash·sha256·blake2b, 6.14+ O_DIRECT 폴백)·Scrub(자동 수리, NOCOW 경고) <https://btrfs.readthedocs.io/>
  - md(4) SCRUBBING AND MISMATCHES <https://man7.org/linux/man-pages/man4/md.4.html>
  - chattr(1) `C` 플래그 · fs/btrfs/ioctl.c `btrfs_fileattr_set()` — NOCOW는 크기 0인 일반 파일에서만 변경 <https://raw.githubusercontent.com/torvalds/linux/master/fs/btrfs/ioctl.c>
- PostgreSQL 18 `initdb --data-checksums`(기본 켜짐) <https://www.postgresql.org/docs/current/app-initdb.html>, 17 문서(선택 사항) <https://www.postgresql.org/docs/17/app-initdb.html>
- Java SE `java.util.zip.CRC32C`, Node.js `crypto.createHash`
- 로컬 재현(e2fsprogs 1.47.0, Python 3): ext4 이미지에서 데이터 블록 손상은 `debugfs cat`·`e2fsck` 모두 조용히 통과, inode 손상은 `Inode checksum does not match inode`로 감지. CRC-32·SHA-256이 1비트 변경을 검출
