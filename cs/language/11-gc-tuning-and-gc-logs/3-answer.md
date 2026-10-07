# language/11-gc-tuning-and-gc-logs — 정답

## 정답

### 1. 컨테이너 한도별 기본값 (실험 1)

| 한도 | 수집기 | MaxHeapSize |
|---|---|---|
| 2 CPU, 1GiB | Serial | 256MiB |
| 2 CPU, 4GiB | G1 | 1GiB |
| 1 CPU, 4GiB | Serial | 1GiB |

- 최대 힙은 한도 × `MaxRAMPercentage`(25%). 수집기는 서버급 판정(2번)으로 갈린다.

### 2. 1792MB 경계

- GC 튜닝 가이드 2장: 서버급 = "two or more processors and physical memory larger than or equal to 1792 MB".
- OpenJDK `os::is_server_class_machine`: `server_memory = 2UL * G`, `missing_memory = 256UL * M`, 조건 `phys_mem >= server_memory - missing_memory` = 1792MiB. CPU는 `active_processor_count() >= 2`.
- 컨테이너에서는 cgroup 한도가 물리 메모리·CPU 수로 쓰인다(`UseContainerSupport` 기본 true).

### 3. soft goal

- `java` 문서: "This is a soft goal, and the JVM will make its best effort to achieve it". 넘을 수 있다. 수집기는 최근 멈춤에 가중치를 둔 평균 + 분산이 목표를 넘으면 젊은 세대 크기 등을 조정한다(가이드 2장).
- `-Xmn` 고정은 그 조정 수단(젊은 세대 크기)을 빼앗는다. 가이드 8장 "Avoid limiting the young generation size to particular values by using options like -Xmn".

### 4. 할당률·승격량

- GC(14) 끝 1.318s에 226M, GC(15) 시작 1.445s에 474M(GC(15) 줄의 앞 값) → 248MB / 0.127s ≈ 1.95GB/s.
- 승격: Old 206 → 211 = 영역 5개 증가(1MB 영역이라 대략 5MB 안팎 — 영역 개수라 정확한 바이트는 아니다). 이번에 비운 Eden 248MB 대비 대략 2% 수준.

### 5. G1 영역과 collection set

```text
  [E][E][S][O][O][ ][H][H][O][E][ ][O]   같은 크기 영역, 이름표만 다름
  Young GC: E + S 전부
  Mixed GC: E + S 전부 + 회수 효율 높은 O 몇 개
```

- 동시 마킹 뒤 Old 후보 영역을 회수 효율 순(빈 공간이 많고 수집 시간이 짧은 영역 먼저)으로 정렬해 먼저 수집한다 → "Garbage-First"(JDK 21 G1 문서 Collection Set 절의 효율 순 정렬, 이름의 유래는 JDK 8 GC 튜닝 가이드 G1 장). 정해진 시간 예산 안의 탐욕 선택이다.

### 6. 설정 3가지 (실험 2, 2회)

| | Evac. Failure | Full GC | Young 평균 |
|---|---|---|---|
| 512m, 200ms | 10 / 10 | 3 / 3 | 13.8 / 13.5ms |
| 512m, 20ms | 12 / 8 | 0 / 2 | 9.8 / 11.6ms |
| 1g, 200ms | 0 / 0 | 0 / 0 | 27.0 / 25.4ms |

- 교훈: 공간 부족(evacuation failure → Full GC)은 힙을 늘려야 없어졌다. 목표를 낮추면 Young이 짧아질 뿐 공간 문제는 남았다. 힙을 늘리면 Young 한 번은 길어졌다 — 맞바꿈이다.

### 7. Evacuation Failure 자체

- G1 문서: 실패 GC는 이미 옮긴 것은 두고 나머지를 제자리에 둔 채 끝나며, "generally should be as fast as other young collections".
- 위험은 그 뒤다. "most objects were already moved" 가정이 틀리면 G1이 Full GC(전체 힙 제자리 압축, "might be very slow")를 건다. 실험 2에서 실패 몇 번 뒤 `Pause Full (G1 Compaction Pause) 511M->205M 81.5ms`.

### 8. humongous (실험 3)

- 400KB: GC 14~16회, 원인은 모두 `G1 Evacuation Pause`류(humongous 원인 0회).
- 600KB: GC 35~38회, 그중 35~37회가 `G1 Humongous Allocation`(나머지는 소스 파일 실행의 컴파일 중 GC). 문턱 = 영역의 절반 512KB(G1 문서 "larger or equal the size of half a region").
- 낭비: 600KB가 1MB 영역 하나를 차지 → 남은 424KB(약 40%)는 그 객체가 회수될 때까지 못 쓴다(G1 문서 "Any leftover space in the last region ... will be lost").

### 9. 작은 파드에서 나빠진 p99

- 첫 줄 `Using Serial`인지 본다. 2 CPU라도 1792MiB 미만이면 Serial이다(실험 1).
- Serial은 Old 수집을 STW 단일 스레드로 한다([10](../10-garbage-collection/2-summary.md) 실험 1 최대 149~201ms).
- 고침: `-XX:+UseG1GC`를 명시하거나 한도를 서버급 이상으로. CPU 1개면 동시 수집기의 몫도 따로 따진다.

### 10. 힙 90% → 로그 없는 재시작

- 커널이 cgroup 한도 초과로 SIGKILL(`OOMKilled`, exit 137)했다. 힙 밖(메타스페이스·스레드 스택·코드 캐시·direct buffer)이 남은 10%를 넘었다([os/13](../../os/13-oom-and-memory-limits/2-summary.md)).
- 나누기: 힙은 `MaxRAMPercentage`로 비율, 힙 밖은 NMT로 재고 `MaxMetaspaceSize`·`MaxDirectMemorySize`로 상한. 상한이 한도 안이면 그 영역이 넘칠 때 SIGKILL 대신 JVM의 `OutOfMemoryError`(Metaspace·Direct buffer memory)로 드러날 수 있다. 스레드 스택·코드 캐시·JNI 할당 등 두 상한 밖의 메모리는 여전히 cgroup 한도를 넘겨 `OOMKilled`가 될 수 있다.
