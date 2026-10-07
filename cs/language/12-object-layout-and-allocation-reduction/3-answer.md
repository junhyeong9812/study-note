# language/12-object-layout-and-allocation-reduction — 정답

## 정답

### 1. `Long`의 배치

```text
  0          8          12         16                  24
  [mark 8B  ][klass 4B ][빈칸 4B  ][ long value 8B    ]
```

- 헤더 12B(mark 8 + 압축 클래스 포인터 4). `long`은 8B 경계에 놓여 16에서 시작(실험 1 `16 long value`). 합 24B, 8의 배수.
- `Integer`: 헤더 12 + `int` 4 = 16B(`12 int value`).

### 2. `Order`의 오프셋

- 선언 순서가 아니다. 실험 1(JDK 21): `qty@12, amount@16, paid@24, status@25, customer@28`. JVM이 크기·정렬에 맞게 재배치한다(HotSpot 구현 동작, JLS는 배치를 정하지 않음).
- 크기: 압축 참조 켬 32B(히스토그램 1000개 32,000B), 끔 40B(참조 필드가 32에서 8B → 40B).

### 3. `List<Long>` vs `long[]`

- 실험 2: `long[]` 80,698,872B(8.1 B/개), `List<Long>` 281,084,096B(28.1 B/개). 3.5배.
- 원소당 28B = `Object[]` 칸의 참조 4B + `Long` 객체 24B(헤더 12 + 빈칸 4 + 값 8). `long[]`은 값 8B뿐, 배열 헤더 16B는 한 번.
- 압축 참조를 끄면 참조 8B → 32.1 B/개.

### 4. TLAB과 할당 비용

- TLAB은 스레드별 Eden 구간이라, 할당이 락 없이 포인터를 미는 것(bump)으로 끝난다.
- 그래도 줄이라는 이유: 할당이 쌓이면 Eden이 빨리 차 Young GC가 자주 온다(실험 3에서 탈출 분석을 꺼 할당이 2배 → Young GC 11 → 21회). 오래 사는 객체는 복사·승격 비용까지 낸다.

### 5. "스택 할당" 오해

- Shipilëv Quark #18: "Hotspot does not do stack allocations per se, but it does approximate that with Scalar Replacement." 객체를 스택에 통째로 두는 게 아니라 필드를 지역 변수로 쪼개 할당을 없앤다.
- 깨지는 경우(같은 글): 접근 전에 제어 흐름이 합쳐지는 경우, 인라인되지 않은(분석에 불투명한) 메서드 호출. 객체 동일성에 기대는 연산도 든다.

### 6. 탈출 분석 실험 (실험 3)

| | noEscape | escapes |
|---|---|---|
| 기본(EA 켬), 3~5라운드 | 0.00 B/call | 32.00 B/call |
| `-XX:-DoEscapeAnalysis` | 32.00 | 32.00 |
| `-XX:TieredStopAtLevel=1`(C1만) | 32.00 | 32.00 |

- 32B = `Point` 헤더 12 + `long` 2개 16 → 정렬 32.
- 탈출 분석·스칼라 치환은 C2 최적화라 C1만 쓰면 일어나지 않았다.

### 7. 객체 풀 (실험 4)

- Young GC 평균: 새로 만들기 2.43ms, 풀 44.8~51.4ms(약 20배). 총 시간 3.5s → 8.8~9.5s. 풀 쪽은 한 번 `Pause Full (G1 Compaction Pause)`까지.
- 이유: 풀 객체는 Old에 산다. 요청마다 새 `payload`를 매달면 Old → Young 참조가 생기고, 카드 테이블·기억 집합을 통해 Young GC의 루트가 된다. 50만 개 `payload`가 "산 객체"로 복사되고 승격돼 Old를 채운다는 해석이다. 로그(`Old regions: 687->769`, Mixed 수집)는 Old 영역이 82개 늘었다는 것까지만 보여 준다 — 승격된 것이 `payload`인지는 힙 덤프 등 별도 증거가 필요하다.

### 8. AoS vs SoA

- AoS: `Order[]` — 원소마다 객체(헤더·패딩) + 참조, 객체가 흩어질 수 있다.
- SoA: `long[] amounts; int[] qtys` — 필드별 원시 배열. 원소별 객체 헤더·참조 없이 연속이다(배열마다 헤더 16B 하나는 남는다).
- 메모리: AoS `Order[]`는 원소당 객체 32B + 배열 칸 참조 4B ≈ 36B(실험 1, 압축 참조 켬). SoA는 담는 필드만큼이다 — `amount`·`qty`만이면 8 + 4 = 12B, 다섯 필드를 다 담으면 8 + 4 + 1 + 1 + 4(참조) = 18B(+ 배열 헤더 5개). (`List<Long>` → `long[]`의 28B → 8B는 실험 2의 다른 비교다.) 지역성: 연속 배열은 캐시 라인을 꽉 채워 쓴다. [architecture/11 실험 3](../../architecture/11-memory-hierarchy-and-locality/2-summary.md)이 같은 합을 배치별로 잰 결과다.

### 9. 리팩터링 뒤 Young GC 두 배

- 의심: 탈출 분석이 깨져 사라졌던 할당이 되살아남(새 헬퍼 메서드가 인라인 안 됨, 분기 합류 뒤 접근 등), 새 박싱·람다 캡처.
- 확인: 핫 경로를 `ThreadMXBean.getThreadAllocatedBytes`로 호출당 할당 바이트를 잰다(워밍업 후 여러 라운드). 리팩터링 전후, 그리고 `-XX:-DoEscapeAnalysis`와 비교한다. JFR 할당 프로파일로 지점을 찾는다.

### 10. `Set<Long>` 1천만 개 OOM

- 히스토그램 상위: `java.lang.Long`(개당 24B)과 해시 집합 내부 노드·테이블. 원소 하나에 `Long` + 내부 노드 + 테이블 칸 참조가 붙는다.
- 순서: (1) 정말 집합이 필요한가(정렬된 `long[]` + 이진 탐색으로 충분한가) → (2) 원시형 특화 해시 집합(개방 주소법, 내부 `long[]`) → (3) 값 범위가 좁으면 비트셋. 바꾼 뒤 히스토그램으로 다시 잰다.
