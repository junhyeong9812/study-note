# reliability/37-memory-leak-and-heap-analysis — 정답

## 정답

### 1. 도달 가능성

- GC는 루트에서 강한 참조를 따라 **닿지 않는** 객체만 회수한다(약한 참조로만 닿으면 회수될 수 있다). 더 쓰지 않아도 강한 참조로 닿기만 하면 남는다. 누수 = 닿지만 쓰지 않는 객체.
- GC 루트 예(MAT 분류): static 필드를 가진 시스템 클래스(System Class), 실행 중인 스레드(Thread), 스택의 지역 변수(Java Local), JNI 전역 참조(JNI Global), 동기화 중인 모니터(Busy Monitor).

### 2. 바닥선

```text
 정상:   ╱╲╱╲╱╲╱╲╱╲   바닥(GC 직후)이 평평
 누수:   ╱╲╱╲ ╱╲╱╲╱    바닥이 우상향
```

- 톱니의 꼭대기는 할당 속도에 따라 출렁인다. **GC 직후 값(바닥선)** 의 추세를 본다.

### 3. 무제한 캐시 실험

(실험, JDK 21.0.12, `-Xmx128m`)

- 단계마다 약 10~11 MiB씩 올랐다(12 → 22 → 33 → … → 119 MiB).
- 11단계(세션 55,000개) 뒤 `java.lang.OutOfMemoryError: Java heap space`.
- OOM 직전 GC 로그: `Pause Full (Allocation Failure) 123M->123M(123M)`가 연달아 — Full GC가 돌아도 아무것도 회수하지 못하고, 그때마다 약 70ms씩 실행이 멈춘다(응답 시간은 재지 않았다).

### 4. 히스토그램의 함정

- 히스토그램은 클래스별 **shallow** 합이다. `byte[]`는 피해자일 뿐 누가 쥐고 있는지 말해 주지 않는다.
- retained size는 그 객체가 사라지면 함께 회수될 양이다. 지배자 트리에서 retained가 큰 것(실험 B의 `class Leak (static SESSIONS)` 6504)이 고칠 곳이다. byte[]를 줄여도(배열 크기 축소) 누수 속도만 늦어질 뿐 멈추지 않는다.

### 5. 지배자 트리 그리기

```text
 루트
  ├── A ── C
  ├── B
  └── D
```

- D는 A로도 B로도 닿는다. 모든 경로가 지나는 정점은 루트뿐이므로 D의 직접 지배자는 루트다.
- A의 retained set = {A, C}. D는 들어가지 않는다(A를 지워도 B로 닿는다).

### 6. retained 계산 순서

- **후위 순서**(자식을 먼저)로 돌며 `ret[v] += shallow[v]; ret[idom[v]] += ret[v]`. 자식의 합이 부모로 올라가 한 번에 끝난다.
- 장난감 실험의 `Config (공유)`: 세션들과 `Thread worker-1`이 함께 가리켜 직접 지배자가 `<GC 루트들>`이었다. 출력에서 `Config (공유)  40 / 40`이 루트 바로 아래에 있다. 그래서 `Session#1`의 retained(2088)에 들어가지 않았다.

### 7. 힙 밖 누수 실험

(실험, JDK 21.0.12, `-Xmx64m`)

- (A) `MaxDirectMemorySize=96m`: 5단계(80 MiB) 다음 할당에서 `OutOfMemoryError: Cannot reserve 1048576 bytes of direct buffer memory (allocated: 99622912, limit: 100663296)`. JVM 예외라 로그가 남는다. NMT에서는 `Other` committed 65546KB(4단계)로 잡혔다.
- (B) `1g` + 컨테이너 256m: 14단계(direct 224 MiB, RSS 265 MiB 표시)까지 간 뒤 커널이 죽였다. `OOMKilled=true ExitCode=137`, JVM 로그 없음.
- 힙 사용량은 두 경우 모두 끝까지 1 MiB.

### 8. RSS만 오를 때

1. 힙 바닥선(used)과 committed가 평평한지 확인 — 힙 밖이 맞나.
2. NMT를 켜고(`-XX:NativeMemoryTracking=summary`, 시작 옵션) `jcmd <pid> VM.native_memory baseline` → 시간 뒤 `summary.diff`. Other(direct buffer)·Thread·Class(metaspace) 중 무엇이 느나.
3. NMT 합계와 RSS(`grep VmRSS /proc/<pid>/status`)의 차이가 계속 벌어지면 NMT가 못 보는 메모리(JVM 밖 `malloc` 등)를 의심하는 단서다(집계 기준이 달라 차이 자체는 보통 있다) — 매핑(`/proc/<pid>/smaps`)과 할당 출처를 본다: async-profiler `nativemem` + `jfrconv --nativemem --leak`.
4. 재발 방지: JVM 쪽 한도(`MaxDirectMemorySize`, 스레드 수)를 컨테이너 한도 안쪽으로 둬서, 그 한도에 먼저 닿는 경우 커널 kill 대신 JVM 예외로 터지게 한다(나머지 메모리 몫의 여유도 둔다).

### 9. 운영 중 힙 덤프

- `GC.heap_dump`는 기본으로 full GC를 요청하고(STW) 살아 있는 힙 전체를 파일로 쓴다(jcmd 문서 Impact: High). 큰 힙이면 멈춤이 길어 헬스체크가 실패하고, 덤프가 로그 디스크를 채워 다른 쓰기도 실패한다. 실험의 65 MiB 힙은 46ms + 0.147초(재실행 43ms + 0.196초), 파일 75 MB였다 — 큰 힙의 수치는 재지 않았지만 힙 크기를 따라 커진다.
- 어떻게: 트래픽을 뺀 한 대에서, 여유 있는 별도 볼륨에 뜬다. 먼저 `GC.class_histogram`을 간격 두고 두 번 떠서 충분한지 본다. 덤프에는 개인정보가 있으니 접근 권한을 제한한다.

### 10. ThreadLocal 누수

- 조건: 스레드가 살아 있고 ThreadLocal 인스턴스에 닿을 수 있는 동안 스레드는 자기 사본을 쥔다(JDK `ThreadLocal` 문서). 풀 스레드는 죽지 않으므로 `remove()` 없이 값을 넣으면 남는다. 값이 앱의 클래스를 가리키면 재배포 때 옛 클래스로더까지 남는다(metaspace 누수).
- 처방: `try { CTX.set(x); … } finally { CTX.remove(); }`. 프레임워크 필터·인터셉터의 끝에서 지운다.
