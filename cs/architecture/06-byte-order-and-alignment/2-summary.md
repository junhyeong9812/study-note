# architecture/06-byte-order-and-alignment — 바이트 순서·정렬·구조체 패딩: 여러 바이트 값이 메모리와 선 위에 놓이는 법 — 정리 (힌트)

## 해결하는 문제

메모리 주소 하나에는 1바이트가 들어간다. 4바이트 정수 `0x12345678`은 주소 네 칸에 나눠 놓아야 한다.\
그때 두 가지를 정해야 한다.
- 어느 바이트를 낮은 주소에 놓나(**바이트 순서**).
- 값이 시작하는 주소를 몇의 배수로 맞추나(**정렬**). 맞추려고 구조체 안에 빈칸(**패딩**)이 생긴다.

쉬운 예: 날짜 쓰는 순서.

```text
  2026-10-07   큰 단위부터 (연-월-일)
  07/10/2026   작은 단위부터 (일/월/연)
  "07/10" 을 받은 사람이 어느 약속인지 모르면 7월 10일로 읽는다.
```

똑같은 구조다.\
x86-64 메모리에는 `78 56 34 12`(작은 자리부터)로, 네트워크 헤더에는 `12 34 56 78`(큰 자리부터)로 놓인다. 받는 쪽이 약속을 모르면 값이 뒤집힌다.

실무 예:
- `htons` 없이 포트 8080을 소켓 주소에 넣었더니 서버가 36895번 포트에서 듣는다(아래 실험).
- 장비가 리틀 엔디안으로 보낸 길이 256을 Java `ByteBuffer` 기본값으로 읽어 65536이 된다(아래 실험).
- C 구조체를 `write(fd, &msg, sizeof msg)`로 그대로 보냈더니, 받는 쪽(다른 컴파일러·32비트)이 필드 위치를 다르게 읽는다.
- x86에서 잘 돌던 코드가 일부 ARM 장비에서 비정렬 접근으로 `SIGBUS`를 낸다.

## 동작·원리

### 1. 바이트 순서 — 큰 자리부터냐 작은 자리부터냐

```text
  값 0x12345678 (4바이트)        주소 →   a     a+1   a+2   a+3
  빅 엔디안   (큰 자리부터)               12    34    56    78     네트워크 바이트 순서
  리틀 엔디안 (작은 자리부터)             78    56    34    12     x86-64 메모리
```

- *빅 엔디안(big-endian)*: 가장 큰 자리 바이트를 가장 낮은 주소에 둔다.
- *리틀 엔디안(little-endian)*: 가장 작은 자리 바이트를 가장 낮은 주소에 둔다.
  - 흔한 오해: "리틀 엔디안은 비트 순서도 거꾸로다." 뒤집히는 단위는 **바이트**다. 한 바이트 안의 값 `0x78`은 그대로 `0x78`이다(아래 실험의 덤프).
- CS:APP 3판 2.1.3 "Addressing and Byte Ordering". 원고 [foundations/data-representation](../../foundations/data-representation/README.md) §2.7 끝에 같은 그림이 있다.
- 이 호스트에서 확인(실험)
  - `lscpu`: `바이트 순서: Little Endian`(i7-13700HX, x86-64).
  - `readelf -h`: `Data: 2's complement, little endian`. `file`: `ELF 64-bit LSB pie executable, x86-64`(LSB = 작은 자리부터).
  - Java: `ByteOrder.nativeOrder() = LITTLE_ENDIAN`.
- 표준·프로토콜의 약속
  - 인터넷 헤더는 큰 자리부터 보낸다(RFC 791 부록 B — [network/02-encapsulation](../../network/02-encapsulation/2-summary.md)에 정리). `man 3 byteorder`: "On the i386 the host byte order is Least Significant Byte first, whereas the network byte order, as used on the Internet, is Most Significant Byte first."
  - Java `ByteBuffer`의 처음 순서는 `BIG_ENDIAN`이다(Java 21 API "The initial order of a byte buffer is always BIG_ENDIAN"). `DataInput.readInt`도 첫 바이트를 최상위로 조립한다(API 문서의 식 `((a & 0xff) << 24) | …`).
  - 그래서 Java 코드끼리, 또는 Java와 네트워크 헤더 사이에는 기본값이 맞는다. 어긋나는 것은 **리틀 엔디안으로 쓴 파일·장비 프로토콜**(일부 바이너리 포맷, x86 C 구조체 덤프)을 읽을 때다.

### 2. 변환 함수 — `htons`·`ntohl`과 바이트 스왑 명령

```text
  호스트(리틀)     htons(8080)                      네트워크(빅)
  0x1F90 → 메모리 90 1F  ──바이트 교환──▶  메모리 1F 90  ──선 위──▶  1F 90 = 8080

  htons 누락:     메모리 90 1F  ───────────────────────────▶  받는 쪽이 0x901F = 36895 로 읽음
```

- `htonl`·`htons`(host to network long/short), `ntohl`·`ntohs`는 호스트 순서와 네트워크 순서를 바꾼다(`man 3 byteorder`).
- 빅 엔디안 호스트에서는 이 함수들이 아무것도 하지 않는다. 그래서 `htons` 누락 버그는 빅 엔디안에서 테스트하면 안 보이고 리틀 엔디안에서만 드러난다(해석 — 함수 정의에서 따라 나온다).
- x86-64 gcc 13.3 `-O2`에서(실험)
  - `__builtin_bswap32` → `bswap %eax` 명령 하나.
  - 시프트·OR로 손으로 쓴 4바이트 교환도 같은 `bswap` 하나로 바뀌었다.
  - `htons` → `rol $0x8,%ax`(16비트 값을 8비트 회전 = 두 바이트 교환).
- Java: `Integer.reverseBytes`, `Short.reverseBytes`, 또는 `ByteBuffer.order(ByteOrder.LITTLE_ENDIAN)`로 읽기.

### 3. 바이트 사전순과 엔디안 — 정렬 가능한 키

```text
  키-값 저장소는 키를 바이트 사전순으로 정렬한다
  int 1   = BIG 00 00 00 01      LITTLE 01 00 00 00
  int 256 = BIG 00 00 01 00      LITTLE 00 01 00 00
            BIG: 1 < 256 ✓       LITTLE: 256 이 앞에 옴 ✗

  int −1  = BIG FF FF FF FF  → 음수가 가장 큰 키로 감 ✗
  부호 비트 뒤집기 (v ^ 0x80000000):  −1 → 7F FF FF FF,  0 → 80 00 00 00   ✓
```

- 0 이상의 정수는 빅 엔디안으로 쓰면 바이트 사전순과 수치 순서가 같다. 리틀 엔디안은 같지 않다.
- 음수를 섞으려면 부호 비트를 뒤집는다. 2의 보수에서 음수는 맨 위 비트가 1이라 무부호 바이트 비교에서 가장 크게 보이기 때문이다([01](../01-number-systems-twos-complement/2-summary.md)).
- 실무: RocksDB 계열 키 설계에서 순번을 빅 엔디안으로 넣는 예가 [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)에 있다.

### 4. 정렬 — 주소가 크기의 배수인가

```text
  주소   0x10000 0x10001 0x10002 0x10003 0x10004 0x10005 0x10006 0x10007 0x10008
         [──── 4바이트 정렬됨 (addr % 4 == 0) ────]
                  [──── 비정렬 (addr % 4 == 1) ─────]
```

- *자연 정렬(natural alignment)*: N바이트를 읽을 때 시작 주소가 N의 배수(`addr % N == 0`)인 것. Linux 커널 문서 "Unaligned Memory Accesses"의 정의다.
- 비정렬 접근을 했을 때 아키텍처마다 다르다(같은 커널 문서의 요약).
  - 투명하게 처리하지만 성능 비용이 큰 것.
  - 프로세서 예외를 내고, 예외 처리기가 고쳐 주지만 아주 느린 것.
  - 예외를 내는데 고칠 정보가 없는 것.
  - 예외 없이 **다른 주소를 조용히 읽는 것**("subtle code bug that is hard to detect").
- x86-64: 일반 load/store는 비정렬을 허용한다. 실험에서 주소 % 4 == 1의 4바이트 load가 `0x12345678`을 그대로 읽었다.
  - 다만 EFLAGS의 AC(정렬 검사) 비트를 켜면 x86-64에서도 같은 load가 `SIGBUS`가 되었다(실험). 정렬된 주소는 AC가 켜져도 문제없었다. Intel SDM의 `MOV` 명령 설명(비공식 사본)은 #AC 조건을 "정렬 검사가 켜져 있고 CPL 3(사용자 모드)에서 비정렬 참조"로 적는다. "켜져 있음"이 CR0.AM과 EFLAGS.AC 두 비트라는 것은 SDM 3권 원문을 열지 않았다 `[?]`.
- ARM: 32비트 ARM Linux는 `/proc/cpu/alignment`로 사용자 프로세스의 비정렬 접근 처리를 고른다. 비트 1은 커널이 고쳐 주기(느림, 운영 비권장), 비트 2는 `SIGBUS` 보내기다(커널 문서 `arch/arm/mem_alignment`). AArch64는 일반 load/store의 비정렬을 (일반 메모리 속성에서) 허용하고, 배타적·원자적 접근은 기본적으로 정렬을 요구한다 `[?]`(Arm 아키텍처 매뉴얼 원문 미확인). 다만 정렬 요구는 명령·메모리 속성·확장에 따라 달라서, FEAT_LSE2(Armv8.4)부터는 16바이트 정렬 블록 안에 들어가는 일부 원자 접근의 비정렬이 허용된다고 알려져 있다 `[?]`(Arm 매뉴얼 원문 미확인).
- 이식 가능한 비정렬 읽기는 `memcpy`다(실험: `memcpy load = 0x12345678`). gcc 13.3 `-O2`는 x86-64에서 `memcpy(&v, p+1, 4)`를 `mov 0x1(%rdi),%eax` load 한 번으로 바꿨다(실험 `mc.c`).

### 5. 구조체 패딩 — 정렬을 맞추려는 빈칸

```text
  struct Msg { uint8_t type; uint32_t len; uint16_t port; uint64_t id; };   x86-64 gcc

  오프셋  0    1  2  3   4  5  6  7   8  9   10 … 15   16 ……………… 23
         type [ 패딩 ]  [── len ──]  [port] [ 패딩 6 ]  [──── id ────]     sizeof = 24

  큰 것부터 { id; len; port; type; }      0..7 id, 8..11 len, 12..13 port, 14 type, 15 패딩   sizeof = 16
  __attribute__((packed))                type 0, len 1, port 5, id 7                       sizeof = 15
```

- 각 멤버는 자기 정렬의 배수 오프셋에 놓인다. 구조체 크기는 가장 큰 정렬의 배수로 맞춘다(실험의 `offsetof`·`sizeof`). CS:APP 3.9.3 "Data Alignment".
- 패딩 바이트의 값은 정해져 있지 않다. 실험에서 `memset(0xAA)` 뒤 필드만 채우자 패딩 칸에 `aa`가 그대로 남았다. 구조체를 통째로 보내면 이 쓰레기도 함께 나간다.
- 정렬은 **ABI**가 정한다. 같은 소스를 gcc 13.3 `-m32`(i386)로 컴파일하자 `sizeof(struct Msg) = 20`, `id` 오프셋 12였다(`-m64`는 24, 16). i386에서 `long long`의 구조체 내 정렬이 4라서다(실험 `_Alignof` = 4).
  - *ABI(Application Binary Interface)*: 타입 크기·정렬·호출 규약 같은 기계어 수준의 약속. 아키텍처·OS·컴파일러 모드마다 다르다.
- `#pragma pack`·`packed`는 패딩을 없애는 대신 비정렬 필드를 만든다. 위 4절의 문제가 다시 생긴다.
- `sizeof`·`offsetof`·`_Alignas`의 규칙 전체는 [languages/c/syntax/08](../../../languages/c/syntax/08-sizeof-alignment-and-offsetof/2-summary.md), 패딩 값·`memcmp`·`pack`은 [languages/c/syntax/22](../../../languages/c/syntax/22-struct-padding-and-alignment/2-summary.md)에 있다. 여기서는 "와이어·파일 형식과 메모리 배치는 다른 약속"까지만 본다.
- 같은 원리가 DB 행에도 있다. PostgreSQL은 칼럼을 타입 정렬에 맞춰 놓아 칼럼 순서로 행 크기가 바뀐다([database/06-pages-and-tuple-layout](../../database/06-pages-and-tuple-layout/2-summary.md)).

### 실험: 덤프·스왑·키 순서·비정렬·패딩

- 환경: i7-13700HX(x86-64, Little Endian), Linux 7.0.0-34, gcc 13.3.0(호스트) / OpenJDK 21.0.12+8-LTS(`eclipse-temurin:21-jdk`, Docker `--cpus=2 --network none`, `os.arch=amd64`), 2026-10-07. 결정적 출력(2회 이상 같음).
- C(`endian.c`, gcc `-O0 -Wall -Wextra -Wpadded`) 출력:

```text
warning: padding struct to align 'len' [-Wpadded]
warning: padding struct to align 'id' [-Wpadded]
warning: padding struct size to alignment boundary with 1 bytes [-Wpadded]
0x12345678 in memory:     78 56 34 12
htonl(0x12345678):        12 34 56 78
port 8080 = 0x1F90; wire(htons) bytes 1f 90; wire(no htons) bytes 90 1f -> peer reads 36895
sizeof Msg=24  offsetof type=0 len=4 port=8 id=16
sizeof MsgSorted=16  offsetof id=0 len=8 port=12 type=14
sizeof MsgPacked=15  offsetof len=1 id=7
_Alignof uint64_t=8, uint32_t=4, uint16_t=2
struct Msg raw bytes:     01 aa aa aa 10 00 00 00 90 1f aa aa aa aa aa aa 01 00 00 00 00 00 00 00
```

- 관찰 1: 원시 바이트에서 `len`(0x10)은 `10 00 00 00`, `port`(8080)는 `90 1f`, `id`(1)는 `01 00 …`로 놓였다. 리틀 엔디안 + 패딩 `aa`가 한 줄에 다 보인다.
- `layout.c`(헤더 없이 내장 타입만, `gcc -S`로 상수 확인): `-m64` → sizeof 24, `id` 오프셋 16, `_Alignof(unsigned long long)` 8 / `-m32` → 20, 12, 4.
- `swap.c`(gcc `-O2`, `objdump -d`): `sw32` → `bswap %eax`, 손으로 쓴 교환 → `bswap %eax`, `htons` → `rol $0x8,%ax`.
- `unaligned.c`(gcc `-O0`) — 3회 실행 같은 결과:

```text
addr % 4 = 1, unaligned load = 0x12345678
memcpy load = 0x12345678
set EFLAGS.AC=1 and load the same address
caught SIGBUS (alignment check)                       ← 종료 코드 7 (처리기에서 _exit(7))
```

- 대조: 같은 프로그램을 정렬된 주소(`buf + 4`)로 바꾸자 AC=1에서도 `not trapped`로 끝났다.
- Java(`Endian.java`) 출력:

```text
nativeOrder = LITTLE_ENDIAN, new ByteBuffer order = BIG_ENDIAN
putInt(0x12345678) BIG    = 12 34 56 78
putInt(0x12345678) LITTLE = 78 56 34 12
wire 00 01 00 00 -> read BIG = 65536, read LITTLE = 256
Integer.reverseBytes(256) = 65536, Short.reverseBytes((short)8080) & 0xFFFF = 36895
putDouble(0.1) BIG    = 3f b9 99 99 99 99 99 9a
putDouble(0.1) LITTLE = 9a 99 99 99 99 99 b9 3f
```

- Java(`KeyOrder.java`) — 정수를 4바이트로 인코딩해 `Arrays.compareUnsigned`(바이트 사전순)로 정렬:

```text
숫자 순서            = [-1, 0, 1, 2, 255, 256, 65536]
LITTLE 바이트 사전순 = [0, 65536, 256, 1, 2, 255, -1]
BIG 바이트 사전순    = [0, 1, 2, 255, 256, 65536, -1]
BIG + 부호 비트 뒤집기 = [-1, 0, 1, 2, 255, 256, 65536]
```

- `printf '\x78\x56\x34\x12' | xxd` → `00000000: 7856 3412` — `xxd`는 파일 바이트를 주소 순서대로 보여 준다. 리틀 엔디안 4바이트 정수를 덤프에서 읽을 때는 거꾸로 읽어야 한다.

## 쓰이는 자료구조·알고리즘

- **바이트 스왑**(🔧): `bswap`·`rol $8` 명령, `Integer.reverseBytes`, `__builtin_bswap*`. 손으로 쓴 시프트·OR도 컴파일러가 같은 명령으로 바꾼다(실험).
- **정렬 가능한 키 인코딩**: 빅 엔디안 + 부호 비트 뒤집기(정수), `doubleToLongBits` 뒤 부호별 비트 뒤집기(부동소수 — [03](../03-floating-point-ieee754/2-summary.md)). LSM·B-트리 키 설계 → [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md).
- **TLV·헤더 파싱**: 길이 필드를 정해진 바이트 순서로 읽고 오프셋을 계산한다 → [network/02-encapsulation](../../network/02-encapsulation/2-summary.md).
- **정렬 올림 계산**: `(x + a - 1) & ~(a - 1)`(a는 2의 거듭제곱) — 할당기·패딩 계산에 쓴다 → [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md), [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md).
- **링 버퍼의 슬롯 정렬**: 캐시 라인 정렬·패딩으로 거짓 공유를 피한다 → [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)(캐시 라인은 영역 표의 12 cache-organization).

## 적용 — 풀어나가는 법

### 1. 증상 → 원인

| 증상 | 의심 |
|---|---|
| 값이 256배·65536배 또는 1/256로 틀림, 8080 ↔ 36895 | 바이트 순서 불일치(`htons` 누락, `ByteBuffer` 기본 BIG) |
| 길이 필드가 거대해 `OutOfMemoryError`·할당 실패 | 리틀 엔디안 길이를 빅 엔디안으로 읽음(또는 반대) |
| 키 범위 스캔 결과가 숫자 순서와 다름 | 리틀 엔디안 키, 음수 키의 부호 비트 |
| 구조체 덤프를 다른 플랫폼·언어가 읽으면 필드가 밀림 | 패딩·ABI 차이(`-m32` 20바이트 vs `-m64` 24바이트) |
| ARM·특정 설정에서만 `SIGBUS`(Bus error) | 비정렬 접근(`packed` 구조체, 바이트 버퍼를 `uint32_t*`로 캐스트) |

### 2. 확인하는 법

- 바이트를 본다: `xxd file | head`, `tcpdump -X`·Wireshark의 16진 칸, Java `HexFormat`. 값 하나를 알고 있으면(예: 길이 256) 그 바이트가 `00 00 01 00`인지 `00 01 00 00`인지로 순서를 판정한다.
- 호스트 순서: `lscpu | grep -i 'byte order\|바이트 순서'`, 바이너리는 `file`·`readelf -h`(LSB/MSB).
- 배치: C는 `offsetof`·`sizeof`를 찍거나 `-Wpadded`. 형식 계약은 `_Static_assert(sizeof(struct Msg) == 24, …)`와 필드마다 `_Static_assert(offsetof(struct Msg, id) == 16, …)`(x86-64 실험값)로 컴파일 시점에 검사한다. 크기만 보면 오프셋이 바뀐 것을 놓친다. 바이트 순서는 이 검사로 못 잡으니 직렬화 코드에서 정한다.
- 비정렬: `-Wcast-align=strict`(gcc), x86에서 재현할 때는 AC 비트 실험처럼 강제로 검사하거나 ARM 장비·에뮬레이터에서 돌린다.

### 3. 코드로 고정한다

```java
// Java 21 — 형식이 리틀 엔디안이면 명시한다
ByteBuffer bb = ByteBuffer.wrap(frame).order(ByteOrder.LITTLE_ENDIAN);
int len = bb.getInt(4);                       // 오프셋도 형식 명세대로
long key = Integer.toUnsignedLong(id ^ Integer.MIN_VALUE);   // 정렬 가능한 키(부호 비트 뒤집기)
```

```c
/* C — 구조체를 통째로 보내지 않고 필드별로 직렬화 */
uint8_t out[15];
out[0] = m->type;
uint32_t nlen = htonl(m->len);  memcpy(out + 1, &nlen, 4);
uint16_t nport = htons(m->port); memcpy(out + 5, &nport, 2);
/* id 는 64비트 — htobe64(<endian.h>) 또는 바이트 단위 시프트 */
```

## 장애 시나리오와 대처

### 1. `htons` 누락 → 포트·길이 필드 뒤집힘 (⚠ 커리큘럼)

- **현상**: 8080에서 듣도록 한 서버에 접속이 안 된다. `ss -ltn`에 `:36895`가 보인다. 또는 헤더 길이 필드가 엉뚱해 상대가 연결을 끊는다.
- **보이는 형태**: `Connection refused`, 패킷 덤프의 `90 1f`(8080이면 `1f 90`이어야 함).
- **원인**: 호스트(리틀) 순서 값을 그대로 `sin_port`에 넣었다(2절, 실험 8080 → 36895). 빅 엔디안 장비에서는 같은 코드가 동작해 놓치기 쉽다.
- **대처**: 소켓 주소·프로토콜 필드는 `htons`/`htonl`을 거친다. 가능하면 `getaddrinfo`처럼 순서를 대신 처리하는 API를 쓴다([network/23-socket-api](../../network/23-socket-api/2-summary.md)).

### 2. 길이 256이 65536으로 — 리틀 엔디안 장비 프로토콜

- **현상**: 산업 장비·게임 클라이언트가 보낸 메시지를 Java 서버가 파싱하다 메모리를 크게 잡거나 `BufferUnderflowException`을 낸다.
- **보이는 형태**: 길이 로그 65536, 16777216 같은 256의 거듭제곱 배수.
- **원인**: 형식은 리틀 엔디안인데 `ByteBuffer` 기본(BIG_ENDIAN)으로 읽었다(실험 `wire 00 01 00 00 -> read BIG = 65536`).
- **대처**: 형식 명세에 바이트 순서를 적고 파서에서 `order(...)`를 명시한다. 길이 상한 검사를 둔다(위반 시 연결 종료).

### 3. ARM 비정렬 접근 `SIGBUS` (⚠ 커리큘럼)

- **현상**: x86 개발 서버에서 문제없던 C 확장·네이티브 라이브러리가 ARM 장비에서 `Bus error (core dumped)`로 죽는다.
- **보이는 형태**: 종료 시그널 7(`SIGBUS`), 커널 로그의 alignment trap 메시지(32비트 ARM의 `/proc/cpu/alignment` 비트 0 설정 시).
- **원인**: `packed` 구조체나 바이트 버퍼를 `uint32_t*`로 캐스트해 비정렬 주소에서 여러 바이트를 읽었다. 아키텍처·설정에 따라 예외가 난다(4절, 커널 문서).
- **재현**: x86-64에서도 EFLAGS.AC를 켜면 같은 load가 `SIGBUS`가 된다(실험).
- **대처**: `memcpy`로 읽는다. 커널 코드라면 `get_unaligned()` 계열(커널 문서). `-Wcast-align=strict`를 켠다.

### 4. 패딩 포함 직렬화 → 프로토콜 불일치 (⚠ 커리큘럼)

- **현상**: 구조체를 `write`로 그대로 보내는 서버와, 같은 헤더를 32비트·다른 컴파일러로 빌드한 클라이언트가 `id`를 다르게 읽는다. 또는 같은 메시지의 해시·서명이 매번 다르다.
- **보이는 형태**: 필드가 4바이트씩 밀린 값, 패딩 칸의 무작위 바이트(실험의 `aa aa aa`).
- **원인**: 패딩 위치·크기는 ABI가 정한다(실험 `-m64` 24바이트 vs `-m32` 20바이트). 패딩 값은 정해지지 않았다.
- **대처**: 필드별 직렬화(위 C 코드), 또는 형식이 명세된 직렬화(Protocol Buffers 등). 구조체를 쓸 수밖에 없으면 `_Static_assert`로 크기·오프셋을 고정한다. `memset(0)` 뒤 채워도 패딩 값은 보장되지 않는다. C11은 구조체나 그 멤버에 값을 저장할 때 패딩 바이트가 미지정 값이 된다고 적는다(N1570 §6.2.6.1 ¶6). 해시·서명·전송할 바이트는 필드별 직렬화로 만든다([languages/c/syntax/22](../../../languages/c/syntax/22-struct-padding-and-alignment/2-summary.md)).

### 5. 키 범위 스캔이 숫자 순서와 다름

- **현상**: 순번 키로 "최근 100건" 범위 조회를 했더니 순서가 뒤섞이거나 음수 키가 맨 뒤에 온다.
- **원인**: 키를 리틀 엔디안(호스트 순서)으로 썼거나, 부호 있는 정수를 빅 엔디안으로만 썼다(3절, 실험).
- **대처**: 빅 엔디안 + 부호 비트 뒤집기. 이미 쌓인 키는 재인코딩 마이그레이션이 필요하다.

## 핵심 문장

- 바이트 순서는 여러 바이트 값의 **바이트**를 어느 쪽부터 놓느냐의 약속이다. 바이트 안의 비트는 뒤집히지 않는다.
- x86-64 메모리는 리틀 엔디안, 인터넷 헤더와 Java `ByteBuffer` 기본값은 빅 엔디안이다.
- `htons`·`htonl`은 빅 엔디안 호스트에서 아무 일도 하지 않으므로, 누락 버그는 리틀 엔디안에서만 드러난다.
- 0 이상의 정수를 빅 엔디안으로 쓰면 바이트 사전순이 수치 순서가 된다. 음수까지 맞추려면 부호 비트를 뒤집는다.
- 정렬은 아키텍처마다 다르게 강제된다. x86-64는 허용(AC 비트로 검사 가능), 일부 ARM 설정은 `SIGBUS`를 낸다. 이식 가능한 비정렬 읽기는 `memcpy`다.
- 구조체 배치는 ABI의 약속이지 와이어 형식이 아니다. 필드별로 직렬화한다.

## 관련 주제·근거

- 선행: [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md)
- 원고: [foundations/data-representation](../../foundations/data-representation/README.md) §2.7(0.1의 비트 분해와 엔디안)
- 이 영역: [03-floating-point-ieee754](../03-floating-point-ieee754/2-summary.md)(double의 바이트), [09 ISA](../09-isa-and-machine-code/2-summary.md)·[10 스택 프레임](../10-calling-convention-and-stack-frame/2-summary.md)·[12 캐시 라인](../12-cache-organization/2-summary.md)
- 연결
  - [network/02-encapsulation](../../network/02-encapsulation/2-summary.md) — 네트워크 바이트 순서(RFC 791 부록 B), `ByteBuffer`로 헤더 파싱
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — 소켓 주소 구조체
  - [languages/c/syntax/08-sizeof-alignment-and-offsetof](../../../languages/c/syntax/08-sizeof-alignment-and-offsetof/2-summary.md) · [languages/c/syntax/22-struct-padding-and-alignment](../../../languages/c/syntax/22-struct-padding-and-alignment/2-summary.md)
  - [database/06-pages-and-tuple-layout](../../database/06-pages-and-tuple-layout/2-summary.md)(칼럼 정렬 패딩) · [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)(빅 엔디안 키)
  - [os/06-signals](../../os/06-signals/2-summary.md) — `SIGBUS`·`SIGSEGV` 전달
- 근거
  - CS:APP 3판 — 2.1.3 Addressing and Byte Ordering, 3.9.3 Data Alignment(절 번호: <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf> 목차)
  - Linux man-pages `byteorder(3)`(`htonl`·`htons`·`ntohl`·`ntohs`, i386 LSB first vs 네트워크 MSB first)
  - Linux 커널 문서 "Unaligned Memory Accesses"(자연 정렬 정의, 아키텍처별 네 가지 결과) <https://docs.kernel.org/core-api/unaligned-memory-access.html>, "Memory alignment"(ARM `/proc/cpu/alignment` 비트 0·1·2) <https://docs.kernel.org/arch/arm/mem_alignment.html>
  - Java SE 21 API `ByteBuffer`("initial order … BIG_ENDIAN"), `ByteOrder.nativeOrder`, `DataInput.readInt`(조립 식) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/ByteBuffer.html>
  - RFC 791 부록 B "Data Transmission Order" <https://www.rfc-editor.org/rfc/rfc791>
  - Intel SDM `MOV` 명령의 #AC(0) 조건 — 비공식 HTML 사본 <https://www.felixcloutier.com/x86/mov>. CR0.AM·EFLAGS.AC 세부(SDM 3권), Arm 아키텍처 매뉴얼의 AArch64 비정렬 규칙 — 원문 미확인 `[?]`
- 실험 목록
  - `endian.c` — 0x12345678 메모리 덤프, `htonl`, `htons` 누락 시 8080 → 36895, `Msg`·`MsgSorted`·`MsgPacked`의 `sizeof`·`offsetof`, 패딩 바이트(0xAA). gcc 13.3.0 `-O0 -Wall -Wextra -Wpadded`. `file`·`readelf -h`·`lscpu`·`xxd`.
  - `layout.c` — `-m64` vs `-m32`의 `sizeof`·`offsetof`·`_Alignof`(`gcc -S` 상수, 32비트 libc 헤더가 없어 내장 타입만 사용).
  - `mc.c` — 비정렬 `memcpy` 읽기의 `-O2` 어셈블리(load 1회).
  - `swap.c` — `__builtin_bswap32`·손 교환·`htons`의 `objdump -d`(`-O2`).
  - `unaligned.c` — x86-64 비정렬 load 허용, `memcpy` 읽기, EFLAGS.AC=1에서 `SIGBUS`(3회), 정렬 주소 대조.
  - `Endian.java` — `nativeOrder`, `ByteBuffer` 기본 순서, 리틀 길이 256을 BIG으로 읽어 65536, `reverseBytes`, double 바이트. `KeyOrder.java` — 바이트 사전순 정렬과 부호 비트 뒤집기. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - 파일 위치: scratchpad `arch/01/e06/`.
