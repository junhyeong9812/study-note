# os/11-heap-allocation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 사용자 공간 할당자가 필요한 이유

- **크기**: 커널은 페이지(보통 4KiB) 단위로 준다. 32바이트 노드마다 페이지를 받으면 나머지가 버려진다. 100만 개면 32MB로 될 것을 약 4GB 쓴다.
- **비용**: 요청마다 시스템 콜을 부르면 느리다. 할당자는 큰 덩어리를 한 번 받아 두고, 작은 요청은 사용자 공간에서 잘라 준다. 해제된 조각은 다음 요청에 재사용한다.

### 2. `malloc(100)` vs `malloc(200*1024)`

```text
brk(NULL)                         <- 현재 브레이크 확인
brk(0x...23000)                   <- malloc(100): 힙을 132KiB(요청 + M_TOP_PAD 128KiB) 늘림
mmap(NULL, 208896, ..., MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)   <- malloc(200KiB)
munmap(..., 208896)               <- free(큰 것): 바로 커널에 반납
                                  <- free(작은 것): 시스템 콜 없음 (free list로)
```

- 128KiB 이상이고 free list로 못 채우는 요청은 `mmap`을 쓴다(mallopt(3) `M_MMAP_THRESHOLD`). 문턱은 기본 상태에서 동적이라 큰 mmap 블록을 free하면 올라갈 수 있다. `M_TRIM_THRESHOLD`·`M_TOP_PAD`·`M_MMAP_THRESHOLD`·`M_MMAP_MAX` 중 하나라도 설정하면 고정된다(mallopt(3)).
- mmap 블록은 `free`하면 `munmap`으로 즉시 돌아간다. 힙 청크는 free list로 돌아갈 뿐 커널에 돌아가지 않는다.
- (예시, 리눅스 7.0 · glibc 2.39 로컬 재현)

### 3. 외부 vs 내부 단편화

```text
  외부: 빈32 조각 3개(합 96) 사이사이 사용 중 → 64 요청을 못 채움
  +------+빈32+------+빈32+------+빈32+
  | 사용 |    | 사용 |    | 사용 |    |

  내부: 33바이트 요청 → 48바이트 청크 → 15바이트는 청크 안에서 낭비
  [ 요청 33 ............ | 낭비 15 ]
```

- 외부 단편화 예: 가변 크기 free list(best/first fit)에서 할당·해제가 섞일 때. 커널 buddy에서 order 0 조각만 남아 고차 할당이 안 될 때.
- 내부 단편화 예: buddy가 2의 거듭제곱으로 올림할 때(9KiB → 16KiB). malloc이 정렬·크기 등급으로 올림할 때.

### 4. 해제 방식별 RSS

| | free 직후 | `malloc_trim(0)` 뒤 |
|---|---|---|
| (a) 마지막만 남김 | 그대로 (약 29MB, 예시) | 크게 줄어듦 (약 2.4MB, 예시) |
| (b) 짝수 번째만 free | 그대로 | 그대로 |

- (a) 마지막 청크가 힙 꼭대기에 살아 있어 `brk`로는 못 줄인다. `free`만으로는 RSS가 안 준다. `malloc_trim`은 glibc 2.8부터 페이지 전체가 빈 영역을 `madvise`로 돌려주므로(malloc_trim(3)) 아래쪽이 통째로 반납된다.
- (b) 절반이 비었지만 모든 페이지에 살아 있는 청크가 섞여 있다. 페이지 전체가 빈 곳이 없으니 trim도 돌려줄 게 없다. 외부 단편화의 모습이다.
- (예시, 리눅스 7.0 · glibc 2.39 로컬 재현)

### 5. buddy 분할과 병합

```text
  요청 16KiB (order 2), order-2 목록 비어 있음
  [          32KiB order 3           ]
  [ 16KiB 줌 (A) ][ 16KiB buddy (B) ]  → B는 order-2 free 목록에

  A 해제 시: B도 비어 있으면 A+B → 32KiB order 3으로 병합, 다시 위로 반복
```

- buddy 주소 = 내 블록 주소 XOR 블록 크기. 두 buddy는 주소가 한 비트만 다르다(OSTEP 17).
- 계산으로 바로 찾으니 병합이 싸다. 대가는 2의 거듭제곱 올림에 따른 내부 단편화다.

### 6. slab이 더해 주는 것

- buddy는 페이지 단위다. 커널 객체(inode, dentry, task_struct 등)는 수십~수백 바이트다.
- slab은 **객체 종류(크기)별 캐시**를 만든다. buddy에서 페이지를 받아 같은 크기 칸으로 나누고, 해제된 칸을 그 캐시 안에서 재사용한다.
- 한 slab 안의 칸 크기가 모두 같다. 빈칸은 언제나 같은 크기의 요청을 채울 수 있으니 slab 안에서는 외부 단편화가 생기지 않는다. 다만 객체가 드문드문 남으면 slab 페이지를 buddy에 못 돌려주는 문제는 남는다.
- 현재 리눅스 소스의 slab 구현은 SLUB이다(mm/Kconfig).

### 7. 자바의 두 할당

- `new byte[1024]`: JVM 힙 안에서 할당한다. HotSpot은 스레드별 버퍼(TLAB)에서 포인터를 밀어 할당한다(HotSpot Glossary). glibc `malloc`을 거치지 않는다.
- `ByteBuffer.allocateDirect`: JDK 구현에서 `UNSAFE.allocateMemory` → HotSpot `os::malloc` → glibc `malloc`이다(OpenJDK 소스). 1MiB라 mmap 문턱 이상이면 `mmap`으로 받는다.
- 그래서 자바 힙(`-Xmx`)은 작아도 direct buffer·스레드 스택·JNI 라이브러리의 `malloc`, glibc arena의 여유 공간이 RSS를 키운다. 컨테이너에서는 이것이 limit 초과로 이어진다(13번).

### 8. double free → exit 134

- 같은 포인터를 두 번 `free`했다. glibc 2.39는 tcache에서 이미 들어 있는 청크를 다시 넣으려는 것을 알아채고 `free(): double free detected in tcache 2`를 출력한 뒤 `abort()`한다(malloc/malloc.c `malloc_printerr`).
- `abort()`는 `SIGABRT`(6)를 보낸다. 셸 종료 코드는 128 + 6 = **134**다.
- 습관
  - `free(p); p = NULL;` — `free(NULL)`은 아무 일도 하지 않는다(malloc(3)).
  - 해제 책임(소유권)을 한 곳으로 정한다.
  - 테스트에서 ASan을 켜 첫 번째·두 번째 free 스택을 함께 본다.

### 9. use-after-free가 늦게 터지는 이유

- 해제된 청크의 본문에는 할당자가 free list 포인터를 적어 둔다.
- 그 청크에 계속 쓰면 이 포인터를 덮는다. 그 순간에는 아무 일도 없다. 그 메모리는 여전히 프로세스에 매핑돼 있기 때문이다.
- 나중에 같은 크기의 `malloc`이 망가진 포인터를 따라가며 엉뚱한 주소를 쓰거나 읽는다. 그때 `SIGSEGV`(exit 139)나 glibc 손상 메시지 + abort가 난다. 크래시 위치와 원인이 멀다.
- 찾는 법: `-fsanitize=address`로 재현한다. 첫 잘못된 접근에서 "heap-use-after-free"와 함께 할당·해제·접근 스택을 모두 보여 준다. `MALLOC_PERTURB_`로 해제된 메모리를 특정 값으로 채우면 증상이 앞당겨진다.

### 10. 스레드 많은 서버의 설명 안 되는 RSS

- 의심: glibc **arena**가 많다. 스레드마다 경합을 피하려 arena가 생기고, 기본 상한은 CPU 수 × 8(64비트, malloc/malloc.c `NARENAS_FROM_NCORES`)이다. 스레드용 arena는 최대 64MiB짜리 heap을 `mmap`해 쓰고, 차면 heap을 더 만들어 잇는다(malloc/arena.c `HEAP_MAX_SIZE`, malloc.c `sysmalloc`의 `new_heap`). pmap의 64MiB 근처 영역이 그 heap들이다. 여러 arena일 수도, 한 arena의 여러 heap일 수도 있다.
- 각 arena가 해제된 청크·여유 공간을 따로 쥐고 있어 RSS가 부푼다.
- 확인·완화
  - `pmap -x <pid>`로 영역 크기·개수를 본다. 자바라면 NMT로 JVM이 아는 native 사용량과 비교한다(13번).
  - `MALLOC_ARENA_MAX`를 작게(예: 2~4, 예시) 설정해 비교한다. 대가는 할당 락 경합이다.
  - `malloc_trim`을 주기적으로 부르거나 jemalloc·tcmalloc으로 바꿔 측정한다.
