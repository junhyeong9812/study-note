# architecture/06-byte-order-and-alignment — 정답

## 정답

### 1. 두 바이트 순서

```text
  주소        a    a+1  a+2  a+3
  빅 엔디안   12   34   56   78
  리틀 엔디안 78   56   34   12
```

- 뒤집히는 단위는 바이트다. 바이트 `0x78` 안의 비트는 그대로다(실험 덤프 `78 56 34 12`).
- 확인 명령: `lscpu`(`바이트 순서: Little Endian`), `readelf -h`(`little endian`) 또는 `file`(`LSB`). Java는 `ByteOrder.nativeOrder()`.

### 2. `htons` 누락

- 8080 = 0x1F90은 리틀 엔디안 메모리에 `90 1F`로 놓인다. 그대로 보내면 상대는 큰 자리부터 읽어 0x901F = **36895**(실험).
- 빅 엔디안 호스트에서는 호스트 순서와 네트워크 순서가 같아 `htons`가 아무 일도 하지 않는다. 그래서 누락해도 결과가 같아 테스트에서 안 보인다.

### 3. 길이 256이 65536

- 보낸 바이트: `00 01 00 00`(리틀 엔디안 256).
- `ByteBuffer`의 처음 순서는 `BIG_ENDIAN`이라 첫 바이트를 최상위로 읽는다 → 0x00010000 = **65536**(실험).
- 고치는 코드

```java
int len = ByteBuffer.wrap(wire).order(ByteOrder.LITTLE_ENDIAN).getInt();   // 256
```

### 4. 바이트 사전순

(실험 `KeyOrder.java`, 같은 입력에 2·255 포함)

```text
LITTLE 바이트 사전순 = [0, 65536, 256, 1, 2, 255, -1]
BIG 바이트 사전순    = [0, 1, 2, 255, 256, 65536, -1]
BIG + 부호 비트 뒤집기 = [-1, 0, 1, 2, 255, 256, 65536]
```

- 리틀 엔디안은 작은 자리가 먼저라 사전순이 수치 순서와 다르다.
- 빅 엔디안은 0 이상에서 맞지만, −1(`FF FF FF FF`)은 무부호 바이트 비교에서 가장 크다.
- 부호 비트를 뒤집으면 음수는 `0x00…`~`0x7F…`, 0 이상은 `0x80…`~`0xFF…`가 되어 무부호 순서 = 부호 있는 순서가 된다.

### 5. 구조체 배치

```text
  오프셋 0: type | 1..3 패딩 | 4..7 len | 8..9 port | 10..15 패딩 | 16..23 id     sizeof 24
  큰 것부터 {id; len; port; type;}: 0 id, 8 len, 12 port, 14 type, 15 패딩       sizeof 16
```

- 실험(`endian.c`): `sizeof Msg=24 offsetof type=0 len=4 port=8 id=16`, `MsgSorted=16`.
- `-m32`: `sizeof` 20, `id` 오프셋 12. i386 ABI에서 `long long`의 구조체 내 정렬이 4라서다(실험 `_Alignof` 4). 같은 헤더라도 ABI가 다르면 배치가 다르다.

### 6. 비정렬 접근

- 커널 문서 "Unaligned Memory Accesses"의 네 가지: ① 투명하게 처리하지만 느림 ② 예외 + 처리기가 고쳐 줌(아주 느림) ③ 예외만 나고 못 고침 ④ 예외 없이 다른 접근을 조용히 수행.
- x86-64: 일반 load는 비정렬을 허용한다. 실험에서 주소 % 4 == 1의 load가 `0x12345678`을 읽었다.
- EFLAGS.AC=1: 같은 load가 `SIGBUS`(실험 3회). 정렬된 주소는 AC=1에서도 문제없었다.
- 이식 가능한 방법: `memcpy`. gcc 13.3 `-O2`는 x86-64에서 이를 load 한 번(`mov 0x1(%rdi),%eax`)으로 바꿨다. 커널 코드는 `get_unaligned()` 계열.

### 7. 구조체 통째 직렬화

- 원인 1 — 배치가 ABI마다 다르다: 패딩 위치·크기가 아키텍처·컴파일러 모드에 따라 바뀐다(`-m64` 24바이트 vs `-m32` 20바이트). 바이트 순서도 호스트를 따른다.
- 원인 2 — 패딩 값이 정해지지 않았다: 실험에서 패딩 칸에 이전 내용(`aa`)이 남았다. 해시·서명에 쓰레기가 섞인다.
- 대처: 필드별로 정해진 바이트 순서로 직렬화(`htonl` + `memcpy`), 또는 명세된 직렬화 형식. 구조체를 꼭 써야 하면 `_Static_assert`로 크기·필드별 오프셋을 고정한다. `memset(0)` 후 채워도 패딩 값은 보장되지 않는다(멤버 저장 때 패딩이 미지정 값이 될 수 있다 — N1570 §6.2.6.1 ¶6). 보낼 바이트는 필드별 직렬화로 만든다.

### 8. 바이트 교환 명령

(실험, `objdump -d`)

- `htons` → `rol $0x8,%ax`(16비트를 8비트 회전 = 두 바이트 교환).
- 손으로 쓴 시프트·OR 4바이트 교환 → `bswap %eax`.
- `__builtin_bswap32` → `bswap %eax`.
- Java: `Integer.reverseBytes`·`Short.reverseBytes`·`Long.reverseBytes`, 또는 `ByteBuffer.order(...)`로 읽고 쓰기.
