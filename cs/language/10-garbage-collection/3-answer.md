# language/10-garbage-collection — 정답

## 정답

### 1. 삼색 마킹

```text
  시작   A 회    | B,C,D,E 흰
  1      A 검    B 회 | C,D,E 흰
  2      A,B 검  C 회 | D,E 흰
  3      A,B,C 검     | D,E 흰   → 회색 없음 = 마킹 끝
```

- D ↔ E는 서로 가리키지만 루트에서 닿지 않아 흰색으로 남는다. sweep이 둘을 해제한다.

### 2. 세 방식의 비용

| 방식 | 비용 비례 | 얻는 것 | 잃는 것 |
|---|---|---|---|
| mark-sweep | mark: 산 객체 / sweep: 힙 전체 | 객체를 안 옮김 | 단편화 |
| 복사 | 산 객체 | 빈칸이 하나로 이어짐 | 공간 두 배 |
| mark-compact | 산 객체 + 참조 수정 | 공간 그대로 + 이어진 빈칸 | 참조를 전부 고치는 일 |

- 복사·압축 뒤에는 빈칸이 한 덩어리라 다음 할당이 "포인터 하나 더하기"(bump pointer)가 된다.

### 3. 세대 가설과 카드 테이블

- JEP 439: "young objects tend to die young, while old objects tend to stick around". 젊은 영역의 대부분이 쓰레기라, 산 것만 복사하는 Young GC가 적은 일로 많은 공간을 얻는다.
- Old → Young 참조는 카드 테이블·기억 집합에 기록한다(G1: 기본 512바이트 카드). Serial·Parallel의 Young GC는 표시된 카드만 추가 루트로 훑는다. G1은 더러운 카드를 동시 정제로 영역별 기억 집합에 옮겨 두고, Young GC는 그 기억 집합(+남은 카드)을 루트로 훑는다.
- 비용: 참조 필드를 쓸 때마다 JIT가 넣은 쓰기 장벽이 돈다. 앱 스레드의 매 참조 쓰기에 붙는다.

### 4. 동시 마킹의 위험과 장벽

- 두 사건: (1) 이미 다 본 **검은** 객체가 **흰** 객체를 가리키게 되고, (2) 그 흰 객체로 가는 **회색** 쪽 경로가 지워진다. 그러면 수집기는 흰 객체를 다시 만날 길이 없어 산 객체를 지운다.
- G1: SATB — 마킹 시작 시점에 살아 있던 객체는 끝까지 산 것으로 본다(G1 문서). 참조를 덮어쓰기 전에 옛 값을 SATB 큐에 넣는 사전 쓰기 장벽으로 (2)를 막는다(OpenJDK jdk21u `G1BarrierSet::write_ref_field_pre`).
- ZGC: colored pointer + load barrier, 세대형은 store barrier도(JEP 439).

### 5. 수집기 4종 비교 (실험 1, 5회 범위)

| | STW 최대 | 앱 지연 최대 |
|---|---|---|
| Serial | 149~201ms | 149~201ms |
| Parallel | 94~216ms | 94~216ms |
| G1 | 69~111ms | 72~122ms |
| ZGC | 0.063~0.145ms | 11.9~30.1ms |

- STW형 수집기는 STW 최대가 앱 지연 최대와 거의 같았다(G1은 앱 쪽이 몇~10여 ms 더 컸다). 회차마다 값이 2배 가까이 갈려 범위로 읽는다.
- ZGC는 STW가 0.15ms 이하인데 앱 지연 최대가 12~30ms였다. CPU 2개를 동시 수집 스레드와 나눠 쓴 결과일 가능성이 있다는 해석이다(CPU 사용은 따로 재지 않았고, 호스트 부하로 인한 스케줄링 지연도 배제 못 한다).

### 6. static 리스트 누수 (실험 2)

- Parallel: `OutOfMemoryError: GC overhead limit exceeded`(28.2s·27.7s·28.2s). `Pause Full (Ergonomics) 61M->61M(63M) 288ms` 같은 줄이 연달아 99~101회, STW 합계 27.0~27.6s.
- G1: `OutOfMemoryError: Java heap space`(6.6~8.6s). Full GC 22~33회, 로그 마지막에 `GC Overhead Limit exceeded too often (5).`
- 둘 다 죽기 전에 "Full GC 뒤에도 힙이 거의 안 내려가는" 줄이 반복됐다.

### 7. 끄는 것이 처방이 아닌 이유

- 이 OOM은 GC가 시간의 98% 이상을 쓰고도 2% 미만만 회수한다는 뜻이다(`java` 문서). 산 데이터가 힙을 채운 상태다. Oracle 가이드는 전형적 원인을 "산 데이터가 힙에 겨우 들어감"으로 보고 힙 증설을 대처로 든다 — 누수 없이도 난다.
- 끄면 OOM 대신 거의 일 못 하는 상태가 더 오래 간다. 원인(누수 또는 힙 부족)은 그대로다. 힙 덤프로 무엇이 붙잡는지 먼저 본다.

### 8. 주기적 p99 스파이크

- 확정: `-Xlog:gc`로 시각을 남기고 지연 그래프와 겹쳐 본다. 스파이크의 구간·길이가 STW 구간과 맞으면 GC가 유력하다(다른 병목이 같은 구간에 겹쳤을 수도 있다). `Pause Full`인지 `Pause Young`인지, 몇 ms인지 본다.
- 조정 순서
  - 프로브 타임아웃을 관측된 최대 STW보다 넉넉하게.
  - Full GC면 원인(누수·힙 부족·humongous·evacuation failure — [11](../11-gc-tuning-and-gc-logs/2-summary.md))부터.
  - Young만 길면 할당률을 줄이거나([12](../12-object-layout-and-allocation-reduction/2-summary.md)), 지연형 수집기(ZGC)를 검토한다.

### 9. `Pause Full (System.gc())`

- 앱·라이브러리·모니터링 도구가 `System.gc()`를 부른다.
- G1 튜닝 가이드: 코드를 못 고치면 `-XX:+ExplicitGCInvokesConcurrent`(동시 사이클로) 또는 `-XX:+DisableExplicitGC`(무시). 외부 도구의 요청은 요청 자체를 없애야 한다.

### 10. 마크 스택

- 마킹은 그래프 순회다. 재귀 DFS는 객체 그래프 깊이만큼 호출 스택을 쓴다. 긴 연결 리스트(실험 2의 76만~80만 개짜리 체인) 하나로도 깊이가 수십만이 된다.
- 그래서 회색 집합을 명시적 스택(작업 목록)으로 들고 반복문으로 돈다 — 재귀를 스택 자료구조로 바꾸는 표준 기법([data-structure/03-stack](../../data-structure/03-stack/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)).
