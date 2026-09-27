# CS 기본기 커리큘럼 — 영역 → 단원 → 주제(leaf) (2026-09-27, L0 설계)

> **용도**: study-note `cs/` 재편의 기준 트리. 1차 리서치 [`roadmap.md`](roadmap.md)를 출발점으로, 교수 관점에서 빈 곳을 채우고 기존 노트 전부를 새 트리에 매핑했다.
> **상태**: 설계안(L0). 폴더 생성·이동·이관은 **하지 않았다** — 착수는 영역별로 별도 결정한다.
> **표기**: `[?]` = 원문(목차·장 번호)을 이번 작업에서 직접 확인하지 못한 항목 — 노트 작성 시 재확인한다. 장 번호 없이 **장 제목만** 적은 근거는 제목 수준에서만 주장한다.

---

## 0. 설계 원칙

### 0.1 교육 철학 — 지식 + "어디서 깨지면 어떻게 보이나"

모든 leaf는 서머리(2-summary) 끝에 **「⚠ 깨지면」 절**을 둔다. 형식은 4칸 고정이다.

| 칸 | 묻는 것 | 예 (network/19) |
|---|---|---|
| 현상 | 무엇이 일어났나 | 상대 프로세스가 강제 종료됐다 |
| 보이는 형태 | 애플리케이션·로그·도구에서 무엇이 보이나 (에러코드·exit code·지표 모양) | `read()` → `ECONNRESET`, 다음 `write()` → `EPIPE`/SIGPIPE |
| 왜 | 이 주제의 메커니즘 중 어느 지점 때문인가 | 커널이 RST를 받고 소켓을 즉시 폐기 |
| 대처 | 진단 도구 + 설계 방어선 | `ss -tanp`, `tcpdump 'tcp[tcpflags] & tcp-rst != 0'`, SIGPIPE 무시·재시도 경계 |

근거: Stevens 『TCP/IP Illustrated』가 이상 상황을 별도 장이 아니라 프로토콜 설명 안(13·14·17장)에서 다룬다 — 장애는 **주제 안에서** 가르친다.

### 0.2 자료구조·알고리즘 연결 규칙

모든 leaf에 `🔧` 칸을 둔다. 여기 적힌 자료구조·알고리즘은 **`data-structure/`·`algorithm/` leaf로 역링크**한다(예: network/08 LPM → `data-structure/20-radix-trie`). 결과적으로 DS·ALG 영역은 "문제풀이 연습장"이 아니라 **시스템 전체가 기대는 부품 창고**가 된다. DS·ALG leaf의 🔧 칸은 반대로 "쓰이는 곳"을 적는다.

### 0.3 층위 순서 (학습 순서의 뼈대)

```text
Part 0  도구 트랙 (병행)        math · data-structure · algorithm
Part 1  컴퓨터 한 대            architecture → os → language
Part 2  두 대 사이              network → security
Part 3  데이터                  database
Part 4  여러 대                 distributed → reliability
Part 5  만드는 법               software-design → domain-modeling → testing → api-design → web-platform → engineering-practice
Part 6  판단하는 법             data-analysis
```

- Part 0은 **한 번에 끝내지 않는다.** Part 1~6의 🔧 칸이 가리킬 때 해당 DS·ALG leaf를 당겨 읽는다(필수 등급만 선행 학습).
- 영역 끝에는 항상 **「증상→원인 역색인」 leaf 1개 + 「실사건」 leaf 1개**가 온다. 역색인은 그 영역 leaf들의 ⚠ 칸을 증상 기준으로 뒤집은 것이고, 실사건은 공개 포스트모템·논문을 그 영역 leaf에 매핑한 것이다.

### 0.4 leaf 크기 규칙

- leaf 1개 = 노트 1개 = `1-question.md` / `2-summary.md` / `3-answer.md` 3파일.
- **서머리 1편으로 닫히는 크기** — 질문 5~8개로 덮이는 범위. 질문이 10개를 넘기 시작하면 쪼갠다.
- 기존 **컬렉션**(README + 여러 편: server-design·engineering-axes·development-standards·languages 등)은 이식 시 leaf 여러 개로 **분할**하거나, 연습 트랙(domain-modeling basic/advanced 등)처럼 **컬렉션 그대로 유지**하고 leaf 1개가 그것을 가리킨다.

### 0.5 표 읽는 법

| 칸 | 뜻 |
|---|---|
| `slug` | 폴더 이름. 영역 안에서 `01-`부터. **같은 영역은 slug만, 다른 영역은 `영역/slug`** 로 참조 |
| 요지 | 한 줄 |
| 선행 | 먼저 읽을 leaf (`—` = 없음) |
| ⚠ 깨지면 | 장애·함정 1~3개 — 가능한 한 **보이는 형태**(에러코드·메시지·지표)까지 |
| 🔧 | 이 주제 안에서 쓰이는 자료구조·알고리즘 (DS·ALG 영역에선 "쓰이는 곳") |
| 📚 | 근거 — 교재 장·RFC·논문. 약어는 §21 출처 |
| 등급 | **필수**(백엔드 개발자가 모르면 장애를 못 읽음) / **권장**(실무에서 곧 만남) / **심화**(특정 직무·깊이) |
| 기존 | 이미 있는 노트 경로(`cs/` 기준) 또는 `신규`. `(분할)` = 기존 노트 일부 절만 해당, `(연결)` = 본문은 신규, 기존 노트는 실습·사례로 링크 |

### 0.6 영역 폴더 이름 (제안)

| # | 영역 | 폴더 | 기존 흡수 대상 |
|---|---|---|---|
| 1 | CS 수학 | `math/` | (없음) |
| 2 | 자료구조 | `data-structure/` | data-structure 전부, foundations/data-structures-basics, systems/thrashing |
| 3 | 알고리즘 | `algorithm/` | algorithm 전부, foundations/algorithm-basics |
| 4 | 컴퓨터 구조 | `architecture/` | foundations/hardware-basics·data-representation·memory-management(일부), systems/call-stack·nand-flash·storage-media-workload |
| 5 | 운영체제 | `os/` | foundations/process-thread·memory-management(일부), systems/semaphore |
| 6 | 프로그래밍 언어·컴파일러 | `language/` | foundations/compiler-pipeline·variables-and-memory, languages/언어-특성 |
| 7 | 네트워크 | `network/` | systems/resp-protocol, server-design/02 |
| 8 | 보안 | `security/` | foundations/security 6편 |
| 9 | 데이터베이스 | `database/` | systems/lsm-tree·partitioning-vs-sharding·clickhouse·postgres-rls·timeseries, engineering/data-access, server-design/03·04 |
| 10 | 분산 시스템 | `distributed/` | ops-patterns 07·08·11~16·18, systems/event-sourcing·orchestration·outbox·kafka×2·striping |
| 11 | 운영·신뢰성 | `reliability/` | ops-patterns 01~06·09·10·19·deadline·failure×2, server-design 01·05·06·08~11, systems/straggler·Hysteresis, engineering/failure-point-checklist |
| 12 | 소프트웨어 설계 | `software-design/` | engineering/clean-code·solid·gof·engineering-axes, foundations/oop-basics, systems/architecture-styles·multi-tenancy |
| 13 | 도메인 모델링 | `domain-modeling/` | domain-modeling 전부 |
| 14 | 테스트 | `testing/` | (없음) |
| 15 | API 설계 | `api-design/` | api-design 01~06 |
| 16 | 웹 플랫폼 | `web-platform/` | (개념만 신설 — DOM API 레퍼런스는 CS 밖) |
| 17 | 엔지니어링 실천 | `engineering-practice/` | engineering/agile-and-squad·development-standards, foundations/three-virtues |
| 18 | 데이터 분석·통계 | `data-analysis/` | (없음) |

- CS2023 17개 KA와의 대응: AL→2·3, AR→4, DM→9, FPL→6, MSF→1·18, NC→7, OS→5, PDC→10, SEC→8, SDF→12, SE→12~17, SF→4·5·11, SPD→16. **AI·GIT(그래픽스)·HCI·SEP는 이 트리에서 뺐다** — 백엔드 개발 기본기 범위 밖(HCI 일부는 web-platform/11 접근성으로만).
- SWEBOK v4 18 KA 대응: Requirements·Management·Process·Economics·Professional Practice·Config Mgmt→17, Architecture·Design·Construction·Models→12·13, Testing→14, Quality→12/20·17, Security→8, **Operations(v4 신설)→11**, Maintenance→12/05~06, Computing/Mathematical/Engineering Foundations→1~6.

---

# Part 0 — 도구 트랙 (병행)

## 1. CS 수학 (`math/`)

> 백엔드에서 수학이 "틀리면" 보이는 곳: 정렬 예외, 음수 샤드 인덱스, ID 충돌, 부동소수 합계 불일치, 이용률 80% 절벽. 증명보다 **불변식·확률·큐잉**을 우선한다.
> 뼈대: MIT 6.042 『Mathematics for Computer Science』(Lehman·Leighton·Meyer, 이하 MCS — 장 번호 `[?]`), CLRS 3판 부록, OpenIntro 3·4장(확률 부분).

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 07 → 08 → 09 → 10 → 15 → (06 · 11 · 12 · 13 · 14 필요 시) → 16 → 17

### 1.1 논리·증명·관계

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-propositional-logic | 명제·술어 논리, 드모르간, 조건문의 부정 | — | `!(a && b)` 를 `!a && !b` 로 바꿔 경계 조건 누락 → 권한 검사 우회; 단락 평가 순서에 기댄 null 검사 붕괴 | 불리언 대수·진리표·SAT | MCS 1부 Proofs [?] | 필수 | 신규 |
| 02-induction-and-invariants | 수학적 귀납과 루프 불변식 — 코드 정확성 논증의 기본 도구 | 01 | off-by-one(마지막 원소 누락); 종료 조건 불변식 부재 → 무한 루프·CPU 100% | 루프 불변식(이진 탐색 정확성), 재귀 정당성 | CLRS 3판 2.1 · MCS 귀납 장 [?] | 필수 | 신규 |
| 03-sets-relations-orders | 집합·함수·동치관계·부분/전순서 | 01 | `equals` 비대칭 → `HashSet` 중복 원소; 비교자 추이성 위반 → `IllegalArgumentException: Comparison method violates its general contract!` | 동치류=union-find, 부분순서=위상정렬, 전순서=정렬 | MCS 관계 장 [?] | 필수 | 신규 |

### 1.2 이산 구조·세기

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-graph-theory-basics | 그래프·트리·DAG·연결성·사이클의 정의와 성질 | 03 | 순환 의존(DAG 가정 위반) → 무한 재귀 `StackOverflowError`, 빌드/마이그레이션 순서 교착 | 인접 리스트·위상정렬·사이클 탐지(DFS 색칠) | MCS 그래프 장 [?] · CLRS 부록 B.4 | 필수 | 신규 |
| 05-counting-and-birthday-bound | 경우의 수·비둘기집·이항계수·생일 한계 | 03 | 32비트 랜덤 ID는 약 7.7만 개에서 충돌 확률 50% → 간헐 PK 중복 `duplicate key`; 짧은 해시 prefix 충돌 | 해시 충돌 확률, UUID/Snowflake 비트 설계 | MCS 세기 장 [?] · CLRS 5.4.1(생일 역설) | 필수 | 신규 |
| 06-modular-arithmetic | 모듈러·GCD·소수·모듈러 역원·빠른 거듭제곱 | 05 | `-7 % 3` 이 언어마다 다름(Java −1 / Python 2) → 음수 샤드 인덱스 `ArrayIndexOutOfBounds`; `Math.abs(Integer.MIN_VALUE)` 음수 | 유클리드 호제법·빠른 거듭제곱 → RSA·해시 | CLRS 31장 | 권장 | 신규 (연결: `algorithm/28-number-theory`) |
| 07-recurrences-and-asymptotics | 점화식·급수·로그 — 마스터 정리까지 | 02 | 선형 재귀 깊이 → 스택 오버플로; 지수 점화 → 입력 30만 넘자 타임아웃 | 분할정복 분석·재귀 트리 | CLRS 3·4장 | 필수 | 신규 |

### 1.3 확률

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 08-probability-and-bayes | 확률 공리·조건부 확률·독립·베이즈 정리 | 05 | 기저율 무시 → "99% 정확한 이상탐지"가 알람의 대부분을 오탐으로 채움(알람 피로) | 블룸 필터 FP 계산, 나이브 베이즈 | OpenIntro 3.1–3.2 · MCS 확률 장 [?] | 필수 | 신규 |
| 09-expectation-variance-tails | 기댓값 선형성·분산·꼬리 부등식(마르코프·체비셰프·체르노프) | 08 | 평균만 보고 꼬리(p99) 무시; "독립" 가정한 가용성 곱셈 → 같은 랙·같은 AZ 동시 장애를 과소평가 | 해시 테이블 기대 탐색 길이, 랜덤 퀵정렬 분석 | CLRS 5장·부록 C · OpenIntro 3.4 | 필수 | 신규 |
| 10-common-distributions | 균등·기하·이항·포아송·지수·정규·멱법칙(Zipf) | 09 | 트래픽을 포아송으로 가정 → 버스트·핫키(Zipf) 과소평가로 캐시·샤드 과부하 | 지수 백오프, 포아송 도착, Zipf와 캐시 적중률 | OpenIntro 4장 | 권장 | 신규 |
| 11-randomness-and-prng | 의사난수·시드·CSPRNG·셔플·샘플링 | 10 | 같은 시드의 인스턴스들이 같은 지터 → thundering herd 재발; `Math.random()` 토큰 → 예측 가능 세션 | LCG·xorshift, Fisher–Yates, reservoir sampling | CLRS 5.3 · Knuth TAOCP 2권 3장 [?] | 권장 | 신규 |

### 1.4 선형대수·정보·수치·큐잉

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 12-linear-algebra-essentials | 벡터·행렬·내적·노름·코사인 유사도 | 07 | 정규화 누락 → 유사도 검색 순위 왜곡; 행/열 순회 방향 → 캐시 미스로 10배 느림 | 행렬곱, 임베딩 근사 최근접 탐색(ANN) | MIT 18.06 (Strang) [?] | 권장 | 신규 |
| 13-information-theory-basics | 엔트로피·부호화·압축 한계·오류 검출/정정 부호 | 08 | 이미 압축·암호화된 데이터 재압축 → 오히려 커짐; 압축 폭탄(zip bomb) OOM | 허프만 부호, CRC, 해밍 코드 | Shannon 1948 · MCS [?] | 권장 | 신규 |
| 14-numerical-stability | 부동소수 오차 누적·파국적 상쇄·Kahan 합 | architecture/03-floating-point-ieee754 | 큰 수+작은 수 반복 합산 손실 → 집계 합계가 원장과 불일치; 병렬 합산 순서마다 다른 결과 | Kahan summation, pairwise sum | Goldberg 1991 · Higham 『Accuracy and Stability of Numerical Algorithms』 [?] | 권장 | 신규 |
| 15-queueing-and-littles-law | L=λW, M/M/1, 이용률과 대기시간의 비선형 관계 | 10 | 이용률 80% 넘자 지연 급등(대기 ∝ ρ/(1−ρ)); 스레드풀·커넥션풀 크기 오산정 | 큐, 포아송 도착, 서비스 시간 분포 | Little 1961 · Harchol-Balter 『Performance Modeling and Design of Computer Systems』 [?] | 필수 | `systems/server-design/01-scaling-principles.md` (분할 — Little's Law 절) |

### 1.5 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 16-math-symptom-index | 증상→원인 역색인: 정렬 계약 위반 예외, 음수 모듈러, 간헐 ID 충돌, 합계 불일치, 이용률 절벽 | 01~15 | (역색인 — 위 ⚠ 칸 전부를 증상 기준으로 뒤집음) | — | 이 영역 leaf | 필수 | 신규 |
| 17-math-incidents | 실사건: Debian OpenSSL PRNG(2008, 키 공간 32,767개로 축소) · Java 7 TimSort 계약 위반 예외 대량 발생 · TimSort 자체 버그의 형식 검증 발견(de Gouw 외 2015) | 16 | (사건별 현상→보이는 형태→원인 leaf→대처) | — | Debian DSA-1571 · de Gouw 외 CAV 2015 | 권장 | 신규 |

---

## 2. 자료구조 (`data-structure/`)

> 기존 01~35 번호를 **그대로 유지**한다(재번호 churn 방지). 신규는 36번부터. 🔧 칸 = **"쓰이는 곳"** — 다른 영역 leaf로 역링크된다.
> 근거: CLRS 3판(이하 CLRS), Sedgewick 『Algorithms』 4판, 각 자료구조 원논문.

**권장 학습 순서**: 36 → 01 → 02 → 03 → 04 → 05 → 29 → 06 → 07 → 08 → 09 → 20 → 10 → 14 → 15 → 16 → 24 → 40 → 11 → 19 → 12 → 31 → 32 → 38 → 37 → 27 → 41 → 39 → 33 → 35 → 34 → (13 · 17 · 18 · 21 · 22 · 23 · 25 · 26 · 28 · 30 심화) → 42 → 43

### 2.1 선형 구조

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 36-adt-and-cost-contracts | ADT = 연산 + 비용 계약. 같은 인터페이스, 다른 비용 | algorithm/31-asymptotic-analysis | `List.get(i)` 를 LinkedList에 루프로 호출 → O(n²) 느려짐(인터페이스만 보고 비용 계약 무시) | 모든 컬렉션 선택 | CLRS 10장 서론 · Sedgewick 1.3 | 필수 | `foundations/data-structures-basics` (분할 — ADT·선택 기준 절) |
| 01-dynamic-array | 연속 메모리 + 용량 2배 확장 = 분할상환 O(1) | 36 | resize 순간 지연 스파이크; C++ 재할당 후 반복자 무효화 → 크래시; 무한 성장 OOM | ArrayList·Go slice·소켓 버퍼 | CLRS 17.4 | 필수 | `data-structure/01-dynamic-array` |
| 02-linked-list | 포인터 연결, O(1) 삽입·삭제, 캐시 비친화 | 36 | 캐시 미스로 배열보다 느림; 동시 수정 시 순환 리스트 → 무한 루프(JDK7 HashMap resize) | LRU 이중 연결, free list, 커널 `sk_buff` 큐 | CLRS 10.2 | 필수 | `data-structure/02-linked-list` · `foundations/data-structures-basics` (분할) |
| 03-stack | LIFO — 호출·되돌리기·파싱 | 01 | 재귀 깊이 초과 `StackOverflowError`/SIGSEGV | 호출 스택, 괄호·표현식 파서, 반복 DFS | CLRS 10.1 | 필수 | `data-structure/03-stack` · `foundations/data-structures-basics` (분할) |
| 04-queue-deque | FIFO·양방향 큐 | 01 | 무한 큐 → 메모리 폭증·지연 누적(백프레셔 부재, OOM) | 작업 큐, BFS, 링 버퍼, 슬라이딩 윈도 최댓값 | CLRS 10.1 | 필수 | `data-structure/04-queue-deque` · `foundations/data-structures-basics` (분할) |
| 38-ring-buffer | 고정 크기 원형 버퍼 — 생산자/소비자, 덮어쓰기 정책 | 04 | 가득 찼을 때 정책 부재 → 조용한 드롭(NIC `rx_dropped`)·또는 생산자 블로킹; head/tail 경합 | NIC DMA 링, 로그 버퍼, LMAX Disruptor, TCP 송수신 버퍼 | LMAX Disruptor 논문 2011 [?] · packagecloud 커널 네트워크 글 | 권장 | 신규 |

### 2.2 해시

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 05-hashmap | 체이닝·로드 팩터·리해시·트리화 | 01, math/05-counting-and-birthday-bound | 충돌 공격 → O(n) 저하·CPU 100%(HashDoS); 가변 키 수정 후 `get` 이 null; equals/hashCode 불일치 | 심벌 테이블, conntrack, 버퍼풀 page table, 캐시 | CLRS 11.1–11.3 | 필수 | `data-structure/05-hashmap` |
| 29-open-addressing | 선형·이차 탐사·로빈후드, tombstone | 05 | 삭제 tombstone 누적 → 탐색 길이 증가로 점진적 느려짐; 로드 팩터 0.9↑ 급격 저하 | Python dict, SwissTable, 커널 해시 | CLRS 11.4 | 권장 | `data-structure/29-open-addressing` |
| 31-consistent-hashing | 해시 링·가상 노드 — 노드 증감 시 최소 재배치 | 05 | 가상 노드 없음 → 부하 불균형; 핫키는 해결 못 함 | 샤딩, 캐시 클러스터, L4 LB(Maglev), Dynamo | Karger 외 1997 | 필수 | `data-structure/31-consistent-hashing` |

### 2.3 트리·힙·트라이

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 06-binary-search-tree | 정렬 불변식, 탐색 O(h) | 03 | 정렬된 입력 삽입 → 편향 트리 O(n) | 정렬 맵의 기초 | CLRS 12 | 필수 | `data-structure/06-binary-search-tree` · `foundations/data-structures-basics` (분할 — 트리·BST 절) |
| 16-red-black-tree | 색 규칙으로 높이 O(log n) 보장 | 06 | 회전 구현 오류 → 불변식 붕괴(조용한 오답) | Java TreeMap, Linux CFS(vruntime), epoll 관심 목록 | CLRS 13 | 권장 | `data-structure/16-red-black-tree` |
| 15-b-tree | 다분기·노드=페이지, 높이 3~4로 수억 행 | 06 | 랜덤 키(UUIDv4) 삽입 → 페이지 분할·단편화로 쓰기 증폭 | DB 인덱스(B+Tree), 파일시스템 디렉터리(ext4 htree) | CLRS 18 | 필수 | `data-structure/15-b-tree` |
| 23-splay-tree | 접근 시 루트로 — 지역성 적응 | 06 | 읽기가 구조를 바꿈 → 동시 읽기에도 락 필요 | 캐시형 탐색, 일부 할당기 | Sleator–Tarjan 1985 | 심화 | `data-structure/23-splay-tree` |
| 07-heap | 완전 이진 트리 + 힙 순서, top/pop O(log n) | 01 | 같은 우선순위 순서 보장 안 됨(FIFO 기대 붕괴); 무한 성장 | 타이머, 스케줄러, top-k, 다익스트라 | CLRS 6 | 필수 | `data-structure/07-heap` |
| 37-timer-structures | 타이머 힙 vs 계층형 타이머 휠 | 07, 38 | 타이머 수백만 개에서 힙 O(log n) 비용 누적; 휠 해상도보다 짧은 타임아웃이 늦게 발화 | 커널 타이머, TCP RTO, Netty HashedWheelTimer, Kafka purgatory | Varghese–Lauck 1987 | 권장 | 신규 |
| 09-trie | 문자 단위 분기 — 접두사 질의 | 06 | 노드 폭증 메모리 | 자동완성, 라우터 경로 매칭 | Sedgewick 5.2 | 권장 | `data-structure/09-trie` |
| 20-radix-trie | 압축 트라이(PATRICIA) | 09 | 비트 경계 처리 오류 → 잘못된 경로 선택 | **라우팅 테이블 최장 접두사 매칭**, HTTP 라우터 | Morrison 1968 | 필수 | `data-structure/20-radix-trie` |
| 13-segment-tree | 구간 질의·갱신 O(log n) | 06 | 배열 크기 4n 미만 할당 → 인덱스 초과; 구간 경계 off-by-one | 구간 합·최솟값 | cp-algorithms "Segment Tree" | 심화 | `data-structure/13-segment-tree` |
| 17-fenwick-tree | 비트 트릭 누적합 | 13 | 1-indexed 규칙 위반 → 무한 루프 | 누적 빈도·순위 | Fenwick 1994 | 심화 | `data-structure/17-fenwick-tree` |
| 30-interval-tree | 겹치는 구간 질의 | 16 | 경계 포함/제외 규칙 불일치 → 예약 중복 | 예약·스케줄 충돌 탐지 | CLRS 14.3 | 심화 | `data-structure/30-interval-tree` |
| 22-sparse-table | 정적 RMQ O(1) | 13 | 갱신 불가 구조에 갱신 요구 | RMQ·LCA | Bender–Farach-Colton 2000 | 심화 | `data-structure/22-sparse-table` |
| 25-spatial-index | R-tree·쿼드트리·geohash | 15 | geohash 셀 경계 근처 이웃 누락 | 위치 검색 | Guttman 1984 | 심화 | `data-structure/25-spatial-index` |

### 2.4 그래프·집합·확률적 구조

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 08-graph | 인접 행렬 vs 리스트 | math/04-graph-theory-basics | 인접 행렬 V² 메모리 폭발 | 의존성, 라우팅, 소셜 그래프 | CLRS 22.1 | 필수 | `data-structure/08-graph` |
| 14-union-find | 경로 압축 + 랭크 | 08 | 경로 압축 누락 → O(n) 체인 | 연결성, 크루스칼, 동치류 | CLRS 21 | 권장 | `data-structure/14-union-find` |
| 18-bitset | 비트 단위 집합·Roaring | 01 | 희소 데이터에 고정 비트셋 → 메모리 낭비; 시프트 부호 확장 | 페이지 할당 비트맵, 블룸 필터, 권한 플래그 | Chambi 외 2016 (Roaring) | 권장 | `data-structure/18-bitset` |
| 11-bloom-filter | "없음"은 확실, "있음"은 확률 | 05, math/08-probability-and-bayes | 설계 용량 초과 삽입 → FP 급증; 삭제 불가 | LSM SSTable 조회 생략, 캐시 관통 방어 | Bloom 1970 | 필수 | `data-structure/11-bloom-filter` |
| 19-probabilistic-counting | HyperLogLog·Count-Min | 11 | 작은 카디널리티 편향; Count-Min 과대 추정 | UV 집계, heavy hitter | Flajolet 외 2007 · Cormode–Muthukrishnan 2005 | 권장 | `data-structure/19-probabilistic-counting` |
| 12-skip-list | 확률적 다층 연결 리스트 | 02 | 최악 O(n)(확률적 보장) | Redis ZSET, LSM memtable | Pugh 1990 | 권장 | `data-structure/12-skip-list` |

### 2.5 문자열·영속·동시성 구조

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 21-suffix-array | 모든 접미사 정렬 | algorithm/25-string-matching | 구성 O(n log² n) 메모리 초과 | 전문 검색, 압축 | Manber–Myers 1990 | 심화 | `data-structure/21-suffix-array` |
| 28-rope | 트리로 쪼갠 문자열 | 06 | 작은 편집마다 재균형 비용 | 텍스트 에디터 버퍼 | Boehm 외 1995 | 심화 | `data-structure/28-rope` |
| 32-inverted-index | 단어→문서 목록 | 05 | 토크나이저 불일치(한국어 형태소) → 검색 누락 | 검색 엔진, 로그 검색 | Manning 외 『Introduction to Information Retrieval』 1장 | 권장 | `data-structure/32-inverted-index` |
| 26-persistent | 구조 공유로 버전 유지 | 06 | 옛 버전 참조 → 메모리 회수 불가 | 불변 컬렉션, MVCC 사고방식 | Driscoll 외 1989 · Okasaki 1998 | 심화 | `data-structure/26-persistent` |
| 27-merkle-tree | 해시의 트리 — 부분 검증 | 05 | 트리 구성 규칙(패딩·정렬) 불일치 → 전 노드 해시 불일치 | git 객체, anti-entropy 동기화, Certificate Transparency | Merkle 1987 | 권장 | `data-structure/27-merkle-tree` |
| 39-concurrent-data-structures | 락 기반·lock-free 큐·해시맵, ABA | 05, os/16-locks-and-spinlocks | 동시 수정 → `ConcurrentModificationException`; lock-free의 ABA → 조용한 손상 | ConcurrentHashMap, 작업 훔치기 deque | OSTEP 29 · Michael–Scott 1996 | 심화 | 신규 |

### 2.6 시스템 구현형 (구현 챕터)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 10-lru-cache | 해시맵 + 이중 연결 리스트, 교체 정책 계열(LRU/LFU/CLOCK/W-TinyLFU) | 05, 02 | 순차 스캔 한 번에 캐시 전체 오염; 용량 과소 → 적중률 절벽 | 버퍼풀, CDN, 앱 캐시, 페이지 교체 | OSTEP 22 · Einziger 외 2017 (TinyLFU) | 필수 | `data-structure/10-lru-cache` |
| 24-lsm-tree | memtable + SSTable + compaction | 12, 11 | compaction 밀림 → 쓰기 정지(write stall); 읽기 증폭 | RocksDB, Cassandra, Kafka 계열 스토리지 | O'Neil 외 1996 | 필수 | `data-structure/24-lsm-tree` |
| 40-lsm-merge-model | LSM 병합 모델 — 레벨·티어 트레이드오프 | 24 | 레벨/티어 선택 오류 → 공간·쓰기 증폭 폭증 | compaction 전략 | O'Neil 외 1996 · RocksDB wiki | 심화 | `data-structure/lsm-merge-model` |
| 41-resize-thrashing | 동적 배열 확장/축소 임계값이 붙으면 resize 반복 | 01 | 원소 수가 경계에서 진동 → 매 연산 O(n) 재할당, CPU 급등 | 축소 임계 1/4(히스테리시스) | CLRS 17.4.2 | 권장 | `systems/thrashing` |
| 33-filesystem | inode·디렉터리 트리 구현 | 06, 18 | 경로 정규화 누락 → `..` 로 트리 밖 접근 | → os/23 | OSTEP 40 | 권장 | `data-structure/33-filesystem` |
| 35-allocator | free list·버디·단편화 | 02 | 외부 단편화 → 총 여유는 충분한데 할당 실패 | → os/11 malloc | OSTEP 17 | 권장 | `data-structure/35-allocator` |
| 34-dependency-resolver | 위상정렬·사이클·버전 해결 | 08, algorithm/12-dfs | 순환 의존 → 해결 불가 에러; 다이아몬드 의존 | → language/17 패키지 관리, 빌드 | CLRS 22.4 | 권장 | `data-structure/34-dependency-resolver` |

### 2.7 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 42-ds-symptom-index | 역색인: `ConcurrentModificationException`, 해시 성능 절벽, `StackOverflowError`, 무한 큐 OOM, resize 스파이크, 캐시 적중률 절벽 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 43-ds-incidents | 실사건: HashDoS(28C3, 2011) → Java 8 HashMap 트리화·Python 해시 랜덤화 · JDK7 HashMap 동시 resize 무한 루프 | 42 | — | — | Klink–Wälde 28C3 2011 · JEP 180 | 권장 | 신규 |

---

## 3. 알고리즘 (`algorithm/`)

> 기존 01~30 유지, 신규 31번부터. 🔧 칸 = "쓰이는 곳".

**권장 학습 순서**: 31 → 32 → 06 → 01 → 02 → 03 → 04 → 33 → 05 → 34 → 35 → 10 → 08 → 09 → 07 → 11 → 12 → 14 → 15 → 18 → 17 → 23 → 24 → 21 → 22 → 13 → 25 → 27 → 26 → 28 → 29 → (16 · 19 · 20 · 30 · 36 · 37 · 38 심화) → 39 → 40

### 3.1 분석·기초

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 31-asymptotic-analysis | 빅오·최악/평균·분할상환 | math/07-recurrences-and-asymptotics | 테스트 데이터(100건)에선 빠른 O(n²)가 운영(100만 건)에서 타임아웃 | 모든 선택의 기준 | CLRS 3·17 | 필수 | `foundations/algorithm-basics` (분할 — 빅오·분할상환 절) |
| 32-recursion | 재귀 = 귀납의 코드. 기저·축소·꼬리 재귀 | 31, math/02-induction-and-invariants | 기저 누락 → `StackOverflowError`; 중복 부분문제 → 지수 시간 | DFS, 파서, 분할정복 | CLRS 2.3 · 4 | 필수 | `foundations/data-structures-basics` (분할 — 재귀 절) |

### 3.2 정렬·탐색

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 06-binary-search | 불변식으로 구간 절반 | 31 | `(lo+hi)/2` 정수 오버플로(Bloch 2006); 경계 갱신 실수 → 무한 루프 | 인덱스 탐색, 일관 해시 링 조회 | CLRS 2.3 연습 · Bloch 2006 | 필수 | `algorithm/06-binary-search` · `foundations/algorithm-basics` (분할) |
| 01-elementary-sort | 선택·삽입·버블 | 31 | 운영 데이터에서 O(n²) 폭발; 삽입정렬은 거의 정렬된 입력에 강함 | TimSort 내부 삽입정렬 | CLRS 2.1 | 필수 | `algorithm/01-elementary-sort` · `foundations/algorithm-basics` (분할) |
| 02-merge-sort | 분할정복·안정 정렬 | 32 | 추가 메모리 O(n) → 대용량 OOM | 외부 정렬, TimSort | CLRS 2.3 | 필수 | `algorithm/02-merge-sort` |
| 03-quick-sort | 분할·피벗 | 32 | 나쁜 피벗 → 정렬된 입력 O(n²)·재귀 깊이 폭증 → introsort로 방어 | 언어 기본 정렬(원시 타입) | CLRS 7 | 필수 | `algorithm/03-quick-sort` · `foundations/algorithm-basics` (분할) |
| 04-heap-sort | 제자리 O(n log n) | data-structure/07-heap | 캐시 비친화로 실측 느림 | introsort 폴백 | CLRS 6.4 | 권장 | `algorithm/04-heap-sort` |
| 33-sorting-in-practice | 안정성·비교자 계약·TimSort·다중 키 | 02, math/03-sets-relations-orders | 비교자 추이성 위반 → `Comparison method violates its general contract!`; 불안정 정렬로 2차 키 순서 뒤섞임 → 페이지네이션 중복 | TimSort, 다중 키 정렬 | Peters `listsort.txt` · de Gouw 외 2015 | 필수 | 신규 |
| 05-non-comparison-sort | 계수·기수 정렬 | 33 | 키 범위 큼 → 메모리 폭발 | 정수 키 대량 정렬 | CLRS 8 | 권장 | `algorithm/05-non-comparison-sort` |
| 34-external-sort-and-k-way-merge | 메모리보다 큰 데이터 정렬, k-way 병합 | 02, data-structure/07-heap | 정렬 메모리 초과 → DB 디스크 스필로 쿼리 수십 배 느림 | DB `ORDER BY`, LSM compaction, MapReduce shuffle | CMU 15-445 L11 | 권장 | 신규 |
| 35-hash-functions | 좋은 해시의 조건·유니버설 해싱·SipHash, 암호/비암호 구분 | data-structure/05-hashmap | 예측 가능 해시 → HashDoS; 암호 해시를 해시맵에 → 느림, 비암호 해시를 무결성에 → 위조 | 해시맵, 샤딩, 체크섬 | CLRS 11.3 · Aumasson–Bernstein 2012 (SipHash) | 권장 | 신규 |

### 3.3 기법

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 10-prefix-sum | 누적합으로 구간 합 O(1) | 31 | 누적 오버플로(int) | 통계 집계, 시계열 | CLRS 연습 [?] | 필수 | `algorithm/10-prefix-sum` |
| 08-two-pointers | 정렬 전제 양 끝 수렴 | 06 | 정렬 전제 위반 → 조용한 오답 | 병합, 중복 제거 | — | 필수 | `algorithm/08-two-pointers` |
| 09-sliding-window | 고정/가변 창 | 08 | 창 경계 포함/제외 혼동 | **rate limiter 슬라이딩 윈도**, TCP 윈도 개념 | — | 필수 | `algorithm/09-sliding-window` |
| 07-parametric-search | 최적화 → 결정 문제 + 이진 탐색 | 06 | 단조성 가정 위반 → 오답 | 용량 산정 역산 | — | 권장 | `algorithm/07-parametric-search` |
| 23-greedy | 국소 최적 선택과 교환 논증 | 31 | 증명 없는 탐욕 → 반례에서 오답 | 허프만, 스케줄링, MST | CLRS 16 | 필수 | `algorithm/23-greedy` |
| 24-divide-conquer | 분할정복·마스터 정리 | 32 | 균형 안 맞는 분할 → 최악 복잡도 | 병합 정렬, 분산 집계 | CLRS 4 | 필수 | `algorithm/24-divide-conquer` |
| 21-dp-basics | 최적 부분 구조 + 중복 부분 문제 | 32 | 메모이제이션 없는 재귀 → 지수 시간 | diff(LCS), 편집 거리 | CLRS 15 | 필수 | `algorithm/21-dp-basics` |
| 22-dp-advanced | 비트마스크·구간·트리 DP | 21 | 상태 공간 폭발 → OOM | 최적 스케줄, 쿼리 조인 순서 최적화(System R) | CLRS 15 · Selinger 외 1979 | 심화 | `algorithm/22-dp-advanced` |
| 13-backtracking | 가지치기 전수 탐색 | 32 | 지수 시간 → **정규식 백트래킹(ReDoS)** 로 이어짐 | 제약 만족, 정규식 엔진 | — | 권장 | `algorithm/13-backtracking` |
| 29-bit-manipulation | 비트 트릭·마스크 | 31 | 부호 있는 오른쪽 시프트 부호 확장; 1<<31 음수 | 플래그, 비트맵, 해시 | Warren 『Hacker's Delight』 | 권장 | `algorithm/29-bit-manipulation` |
| 30-sweeping | 이벤트 정렬 후 스윕 | 33 | 동시각 이벤트 처리 순서 오류 → 겹침 오판 | 예약 충돌, 구간 합집합 | CLRS 33.2 | 심화 | `algorithm/30-sweeping` |

### 3.4 그래프

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 11-bfs | 레벨 순회·최단 홉 | data-structure/08-graph, data-structure/04-queue-deque | 방문 표시를 큐 삽입이 아닌 꺼낼 때 → 중복 폭증 | 최단 홉, GC 도달성, 크롤러 | CLRS 22.2 | 필수 | `algorithm/11-bfs` |
| 12-dfs | 깊이 순회·색칠·위상정렬 | 11 | 재귀 DFS 스택 오버플로; 사이클 미탐지 | **데드락 wait-for 사이클 탐지**, 의존성 순서, GC 마킹 | CLRS 22.3–22.4 | 필수 | `algorithm/12-dfs` |
| 18-scc | 강연결요소(Tarjan·Kosaraju) | 12 | — (순환 그룹을 못 찾으면 순환 의존 방치) | 순환 의존 묶음 탐지 | CLRS 22.5 · Tarjan 1972 | 권장 | `algorithm/18-scc` |
| 14-dijkstra | 음이 아닌 가중치 최단 경로 | 11, data-structure/07-heap | 음수 가중치 → 조용한 오답 | **OSPF 링크 상태 라우팅** | CLRS 24.3 | 필수 | `algorithm/14-dijkstra` |
| 15-bellman-floyd | 벨만-포드·플로이드 | 14 | 음수 사이클 → 발산; 거리 벡터 count-to-infinity | **거리 벡터 라우팅(RIP)** | CLRS 24.1 · 25.2 | 권장 | `algorithm/15-bellman-floyd` |
| 17-mst | 크루스칼·프림 | data-structure/14-union-find | — | 망 설계, 클러스터링 | CLRS 23 | 권장 | `algorithm/17-mst` |
| 20-a-star | 휴리스틱 최단 경로 | 14 | 과대 추정 휴리스틱 → 최적 아님 | 경로 탐색 | Hart–Nilsson–Raphael 1968 | 심화 | `algorithm/20-a-star` |
| 16-euler-path | 모든 간선 한 번 | 12 | — | 경로 재구성 | Hierholzer 1873 [?] | 심화 | `algorithm/16-euler-path` |
| 19-network-flow | 최대 유량·이분 매칭 | 11 | 용량 모델링 오류 → 할당 오답 | 작업 배정, 대역폭 | CLRS 26 | 심화 | `algorithm/19-network-flow` |

### 3.5 문자열·수론

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 25-string-matching | KMP 실패 함수 | 31 | 나이브 매칭 O(nm) 로그 검색 폭증 | grep, 필터 | CLRS 32.4 | 권장 | `algorithm/25-string-matching` |
| 27-string-hashing | 롤링 해시(Rabin-Karp) | 35 | anti-hash 입력 충돌 → 오답 | 중복 탐지, rsync 청크 | CLRS 32.2 | 권장 | `algorithm/27-string-hashing` |
| 26-aho-corasick | 다중 패턴 오토마톤 | 25, data-structure/09-trie | 패턴 수 폭증 메모리 | WAF·IDS 시그니처, 금칙어 필터 | Aho–Corasick 1975 | 심화 | `algorithm/26-aho-corasick` |
| 28-number-theory | 소수·GCD·모듈러 역원 | math/06-modular-arithmetic | 모듈러 곱셈 오버플로 | RSA, 해시 | CLRS 31 | 권장 | `algorithm/28-number-theory` |

### 3.6 확률·계산 이론

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 쓰이는 곳 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 36-randomized-algorithms | 라스베이거스·몬테카를로, 기대 복잡도 | math/09-expectation-variance-tails | 결정적 시드 → 적대적 입력에 최악 재현 | 랜덤 피벗, 스킵 리스트, 샘플링 | CLRS 5 · 7.3 | 심화 | 신규 |
| 37-complexity-p-np | P·NP·NP완전·환원·근사 | 31 | NP-hard 문제에 정확해 고집 → 무한 대기; 근사·휴리스틱 선택 기준 부재 | 스케줄링·빈 패킹·SAT 솔버 | CLRS 34 · Sipser 3부 [?] | 권장 | 신규 |
| 38-computability-and-halting | 정지 문제·라이스 정리 | 37 | "모든 버그를 잡는 정적 분석기" 기대 → 오탐/미탐 불가피성 오해 | 정적 분석·타입 검사의 한계 | Sipser 4·5장 [?] | 심화 | 신규 |

### 3.7 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 39-alg-symptom-index | 역색인: 데이터 늘자 타임아웃(복잡도), 정렬 계약 예외, 재귀 스택 오버플로, 정규식 CPU 100%, 이진 탐색 무한 루프 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 40-alg-incidents | 실사건: JDK 이진 탐색 오버플로(Bloch 2006) · Stack Overflow 정규식 장애(2016-07-20) · Cloudflare WAF 정규식 백트래킹 전역 CPU 100%(2019-07-02) | 39 | — | — | Bloch 2006 Google Research 블로그 · Stack Exchange 포스트모템 2016 · Cloudflare 블로그 2019-07-12 | 권장 | 신규 |

# Part 1 — 컴퓨터 한 대

## 4. 컴퓨터 구조 (`architecture/`)

> 비트 → 게이트 → CPU → 메모리 계층 → 저장장치. 백엔드가 여기서 만나는 장애: 정수 오버플로, 부동소수 오차, 인코딩 깨짐, 아키텍처 불일치 바이너리, false sharing, SSD 지연 스파이크.
> 뼈대: CS:APP 3판(2·3·4·5·6장), OSTEP 36·37·44, Patterson&Hennessy 『Computer Organization and Design』(이하 P&H — 장 번호 `[?]`).

**권장 학습 순서**: 01 → 02 → 03 → 05 → 04 → 06 → 07 → 08 → 09 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → (10 · 11 · 19 · 20 심화) → 21 → 22

### 4.1 데이터 표현

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-number-systems-twos-complement | 진수 변환·2의 보수·부호/무부호 | math/01-propositional-logic | signed/unsigned 비교 → `-1 > 0u` 참; 부호 확장 실수 | 비트 연산 | CS:APP 2.1–2.2 | 필수 | `foundations/data-representation` (분할 — 진수·2의 보수 절) |
| 02-integer-overflow-and-truncation | 오버플로 wrap, 좁히기 캐스팅 절단 | 01 | Java `int` 21억 초과 → 음수 금액; 64→16비트 변환 예외(Ariane 5); `size_t` 언더플로 → 거대 할당 | 포화 산술, `Math.addExact` | CS:APP 2.3 | 필수 | 신규 (연결: `foundations/languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions`) |
| 03-floating-point-ieee754 | 부호·지수·가수, ε, 특수값(NaN·Inf) | 01 | `0.1+0.2 != 0.3`; `NaN != NaN` 으로 정렬·집합 붕괴; 돈을 `double` 로 → 원 단위 불일치 | 반올림 모드, Kahan 합(math/14) | CS:APP 2.4 · Goldberg 1991 | 필수 | `foundations/data-representation` (분할 — IEEE 754 절) |
| 04-byte-order-and-alignment | 엔디안·정렬·구조체 패딩 | 01 | 네트워크 바이트 순서 누락 → 포트·길이 필드 뒤집힘; ARM 비정렬 접근 `SIGBUS`; 패딩 포함 직렬화로 프로토콜 불일치 | 바이트 스왑 | CS:APP 2.1.3 · 3.9.3 | 권장 | `foundations/data-representation` (분할 — 엔디안 절) · 연결: `languages/c/syntax/08·22` |
| 05-character-encoding-unicode | 코드 포인트·UTF-8/16·서로게이트·정규화 | 01 | 모지바케(`Ã©`); 서로게이트 쌍 중간 절단 → `�`; NFC/NFD 불일치 → 같은 파일명 두 개; MySQL `utf8`(3바이트)에 이모지 → `Incorrect string value` | 가변 길이 부호화, 바이트 경계 탐색 | RFC 3629 · Unicode Standard 2·3장 [?] | 필수 | `foundations/data-representation` (분할 — ASCII/유니코드 절) |

### 4.2 논리 회로에서 명령어까지

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 06-logic-gates-to-adder | 트랜지스터→게이트→가산기·ALU | 01 | 캐리 전파 지연이 클록 상한을 정함(타이밍 위반) | 불리언 대수, ripple O(n) vs lookahead O(log n) | P&H 부록 A [?] · CS:APP 4.2 | 권장 | `foundations/hardware-basics` (분할 — 게이트·가산기 절) |
| 07-sequential-logic-clock | 플립플롭·클록·레지스터·상태 기계 | 06 | 비동기 신호 동기화 실패 → 메타안정성(간헐 오동작) | 유한 상태 기계 | CS:APP 4.2.5 · P&H 부록 A [?] | 권장 | `foundations/hardware-basics` (분할 — 플립플롭·클록·레지스터 절) |
| 08-isa-and-machine-code | ISA·레지스터·어셈블리(x86-64/ARM64) | 07 | arm64 이미지를 amd64에서 실행 → `exec format error`; 에뮬레이션(Rosetta·QEMU)로 수배 느림 | 명령어 인코딩 | CS:APP 3장 | 필수 | `foundations/hardware-basics` (분할 — 인스트럭션 세트 절) |
| 09-calling-convention-and-stack-frame | 호출 규약·스택 프레임·ESP/RSP | 08, data-structure/03-stack | 깊은 재귀 → `StackOverflowError`/`SIGSEGV`; 버퍼 오버플로로 반환 주소 덮어쓰기 | 스택 | CS:APP 3.7 | 필수 | `systems/call-stack` · `foundations/memory-management` (분할 — 스택 프레임 절) |
| 10-pipelining-and-branch-prediction | 파이프라인·해저드·분기 예측 | 08 | 분기 예측 실패 → 정렬 안 된 데이터 루프가 수배 느림 | 2비트 포화 카운터 예측기 | CS:APP 4.4–4.5 · P&H 4장 [?] | 심화 | 신규 |
| 11-out-of-order-and-speculation | 비순차·투기 실행과 부채널 | 10 | Spectre/Meltdown — 권한 밖 메모리가 캐시 타이밍으로 샘; 패치 후 syscall 성능 저하 | 재정렬 버퍼 | Kocher 외 2019 · Lipp 외 2018 | 심화 | 신규 |

### 4.3 메모리 계층

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 12-memory-hierarchy-and-locality | 레지스터→캐시→DRAM→SSD, 시간·공간 지역성 | 08 | 열 우선 순회·포인터 추적 → 캐시 미스로 수~수십 배 느림 | 배열 vs 연결 리스트 선택 근거 | CS:APP 6.1–6.3 | 필수 | `foundations/memory-management` (분할 — 메모리 계층·캐시 지역성 절) |
| 13-cache-organization | 라인·집합 연관·쓰기 정책·교체 | 12 | **false sharing** → 멀티스레드 카운터가 단일보다 느림; 2의 거듭제곱 stride 충돌 미스 | 의사 LRU, 인덱스 비트 해싱 | CS:APP 6.4–6.6 | 필수 | 신규 |
| 14-latency-numbers | 지연 자릿수 감각·AMAT | 12 | "네트워크 1회 ≈ 메모리 접근 수십만 회"를 무시한 루프 내 원격 호출(N+1) | AMAT 계산 | Dean "Latency Numbers" · CS:APP 6.1 | 필수 | 신규 |
| 15-cache-coherence-and-memory-ordering | MESI·저장 버퍼·재정렬·배리어·CAS | 13 | 가시성 결여 → 플래그 대기 무한 루프; 재정렬로 DCL 싱글턴 반쯤 초기화된 객체 노출 | MESI 상태 기계, CAS | Sorin·Hill·Wood 『A Primer on Memory Consistency and Cache Coherence』 [?] · CS:APP 12.5 [?] | 필수 | 신규 |

### 4.4 I/O·저장장치·병렬

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 16-io-devices-interrupts-dma | 폴링 vs 인터럽트, DMA, 장치 레지스터 | 12 | 인터럽트 폭주 → 한 코어 softirq 100%; DMA 링 가득 → 패킷 드롭 | 디스크립터 링(data-structure/38) | OSTEP 36 | 필수 | 신규 |
| 17-storage-media-workload | HDD 탐색·회전 vs SSD, 순차/랜덤 IOPS 유도 | 16 | 랜덤 I/O 워크로드를 HDD에 → IOPS 한계로 지연 폭증 | 엘리베이터 스케줄링 | OSTEP 37 | 필수 | `systems/storage-media-workload` |
| 18-nand-flash-ftl | 셀·블록·FTL·GC·쓰기 증폭 | 17 | SSD 내부 GC → 주기적 지연 스파이크; 쓰기 증폭 → 수명 소진·`SMART` 경고 | 로그 구조 매핑, 웨어 레벨링 | OSTEP 44 | 권장 | `systems/nand-flash` |
| 19-multicore-and-numa | 멀티코어·SMT·NUMA 원격 메모리 | 15 | NUMA 원격 접근 → 같은 코드인데 지연 편차; 코어 수 이상 스레드 → 경합 | 스레드 배치(affinity) | CS:APP 12.6 [?] · Drepper 2007 | 심화 | 신규 |
| 20-simd-and-gpu | 데이터 병렬(SIMD·GPU)의 모양 | 19 | 분기 많은 코드를 GPU로 → 워프 분기로 느림 | 벡터화 루프 | P&H 6장 [?] | 심화 | 신규 |

### 4.5 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 21-arch-symptom-index | 역색인: `SIGSEGV`/`SIGBUS`/`SIGILL`, `exec format error`, 음수 금액, 합계 불일치, 모지바케, 멀티스레드가 더 느림, SSD 지연 톱니 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 22-arch-incidents | 실사건: Patriot 미사일 시계 오차 누적(1991) · Ariane 5 64→16비트 변환(1996) · Intel FDIV(1994) · Spectre/Meltdown(2018) · 2038년 문제 | 21 | — | — | GAO/IMTEC-92-26 · Ariane 501 조사보고서 1996 · Spectre/Meltdown 논문 | 권장 | 신규 |

---

## 5. 운영체제 (`os/`)

> 가상화(CPU·메모리) → 동시성 → 영속성 → I/O·격리. 기존 부트캠프 노트는 프로세스·메모리 기초만 덮는다 — **동기화 심화·시그널·파일시스템·fsync·I/O 모델·컨테이너**가 신규의 중심.
> 뼈대: OSTEP(장 번호 확인), CS:APP 3판 7~12장, Linux man-pages(`signal(7)`·`epoll(7)`·`fsync(2)`).

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 22 → 23 → 24 → 25 → 28 → 29 → 21 → 34 → 32 → 31 → 35 → (26 · 27 · 30 · 33 심화·권장) → 36 → 37

### 5.1 커널과 프로세스

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-kernel-and-user-mode | OS의 역할, 보호 링, 제한된 직접 실행 | architecture/08-isa-and-machine-code | 유저 코드가 특권 명령 → `SIGILL`/`SIGSEGV` 로 강제 종료 | 트랩 테이블 | OSTEP 2·6 | 필수 | 신규 |
| 02-system-calls | syscall 경로·비용·`strace` | 01 | 작은 `write` 반복 → sys CPU 급등; `EINTR` 미처리 → 간헐 실패 | syscall 테이블(배열 인덱스 디스패치) | OSTEP 6 · CS:APP 8.1 · `syscalls(2)` | 필수 | 신규 |
| 03-interrupts-traps-faults | 인터럽트·트랩·폴트·예외적 제어흐름 | 02 | page fault 폭주(major fault) → 디스크 대기로 지연 급등 | 인터럽트 벡터 테이블 | CS:APP 8.1 | 필수 | 신규 |
| 04-process-and-lifecycle | 프로세스 추상화·5상태·PCB | 03 | 좀비(`<defunct>`) 누적 → PID 고갈 `fork: Resource temporarily unavailable`; 고아 프로세스 | PCB 연결 리스트, 상태 기계 | OSTEP 4 · CS:APP 8.2 | 필수 | `foundations/process-thread` (분할 — 5상태·PCB 절) |
| 05-fork-exec-wait | 프로세스 API | 04 | 컨테이너 PID 1이 자식 회수 안 함 → 좀비 누적(tini 필요); fork 후 fd 상속 → 소켓 안 닫힘 | copy-on-write 페이지 | OSTEP 5 · CS:APP 8.4 | 필수 | 신규 |
| 06-signals | 시그널 전달·핸들러·async-signal-safe | 05 | SIGPIPE로 조용한 종료; SIGTERM 무시 → k8s 유예 후 SIGKILL(`exit 137`); 핸들러 안 `malloc` → 데드락 | 대기 비트마스크 | CS:APP 8.5 · `signal(7)` | 필수 | 신규 |
| 07-threads-and-context-switch | 스레드·TCB·컨텍스트 스위칭 비용 | 04 | 스레드 과다 → 컨텍스트 스위치 폭증(`vmstat cs`); `OutOfMemoryError: unable to create native thread` | 실행 큐 | OSTEP 26 · 27 | 필수 | `foundations/process-thread` (분할 — 컨텍스트 스위칭·멀티스레드 절) |
| 08-cpu-scheduling | FIFO·SJF·RR·MLFQ·CFS·멀티코어 | 07 | 기아; cgroup CPU quota throttling → 평균 CPU 낮은데 p99 급등 | MLFQ 다중 큐, **CFS 레드블랙트리**(vruntime), 힙 | OSTEP 7·8·9·10 | 필수 | `foundations/process-thread` (분할 — 스케줄링 절) |

### 5.2 메모리 가상화

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 09-address-space | 가상 주소 공간·코드/데이터/힙/스택·세그먼트 | 04 | null·해제된 주소 접근 `SIGSEGV`(exit 139) | 베이스/바운드 | OSTEP 13 · 15 · 16 | 필수 | `foundations/memory-management` (분할 — 가상 주소 4세그먼트 절) |
| 10-paging-and-tlb | 페이지 테이블·다단계·TLB | 09, architecture/13-cache-organization | TLB 미스 폭증 → 큰 힙 랜덤 접근 느림(huge page 검토) | **다단계 페이지 테이블 = 기수 트리**, TLB = 연관 캐시 | OSTEP 18·19·20 | 필수 | `foundations/memory-management` (분할 — MMU·페이징·TLB 절) |
| 11-heap-allocation | malloc·free list·단편화·buddy·slab | 09, data-structure/35-allocator | 단편화로 RSS가 안 줄어듦; double free·use-after-free 크래시 | free list, buddy, slab | OSTEP 14 · 17 | 필수 | `foundations/memory-management` (분할 — 힙 절) · 연결: `data-structure/35-allocator` |
| 12-swapping-and-page-replacement | 스왑·교체 정책·작업 집합·스래싱 | 10 | 스왑 폭주 → 시스템 전체 멈춘 듯(스래싱); 교체 정책이 스캔에 오염 | **LRU 근사 = CLOCK**, 작업 집합 | OSTEP 21 · 22 | 필수 | 신규 (연결: `systems/thrashing` 은 자료구조 resize 스래싱 — 용어 대비) |
| 13-oom-and-memory-limits | overcommit·OOM killer·cgroup memory | 12 | 컨테이너 `OOMKilled`(exit 137); JVM 힙 < limit인데 native·메타스페이스로 초과 | oom_score 선택 | `proc(5)` · 커널 문서 cgroup v2 | 필수 | 신규 |
| 14-mmap-and-page-cache | 파일 매핑·페이지 캐시·dirty writeback | 10 | `free` 가 "사용 중"으로 보여 메모리 누수 오판; 매핑 중인 파일 절단 → `SIGBUS` | 기수 트리(page cache 인덱스) | OSTEP 23 · CS:APP 9.8 | 권장 | 신규 (연결: `systems/kafka-why-fast` 페이지 캐시 절) |

### 5.3 동시성

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 15-race-conditions | 임계 구역·원자성·check-then-act | 07 | `count++` 유실; 재고 음수; 테스트에선 안 나고 부하에서만 | — | OSTEP 26 | 필수 | `foundations/process-thread` (분할 — 경쟁 조건·Lock 절) |
| 16-locks-and-spinlocks | test-and-set·CAS·futex·공정성 | 15, architecture/15-cache-coherence-and-memory-ordering | 스핀락 과점유 → CPU 낭비; 락 경합 → 코어 늘려도 처리량 역전 | CAS, 티켓 락(큐) | OSTEP 28 · 29 | 필수 | 신규 |
| 17-condition-variables-and-monitors | 대기/통지·모니터 | 16 | `if` 로 대기 → spurious wakeup 후 빈 큐 접근; lost wakeup → 영원히 대기 | 대기 큐 | OSTEP 30 | 필수 | 신규 |
| 18-semaphores | 카운팅 세마포어·생산자/소비자 | 17 | release 누락(예외 경로) → permit 영구 소진 hang | 카운터 + 대기 큐 | OSTEP 31 | 필수 | `systems/semaphore` |
| 19-deadlock | 4조건·예방·회피·탐지 | 16 | 스레드 덤프 `Found one Java-level deadlock`; DB `1213 Deadlock found` / `40P01` | **wait-for 그래프 사이클 탐지(DFS)**, 락 전순서, 은행원 알고리즘 | OSTEP 32 | 필수 | 신규 |
| 20-concurrency-bugs | 원자성 위반·순서 위반·기아·라이브락·우선순위 역전 | 19 | 우선순위 역전 → 워치독 리셋(Mars Pathfinder); 라이브락 → CPU 바쁜데 진행 0 | 우선순위 상속 | OSTEP 32 · Lu 외 ASPLOS 2008 | 필수 | 신규 |
| 21-event-based-concurrency | 이벤트 루프·reactor·콜백 | 29 | 이벤트 루프에서 블로킹 호출 → 모든 요청 동시 지연 | 이벤트 큐·타이머 힙 | OSTEP 33 | 필수 | 신규 |

### 5.4 영속성·I/O

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-files-and-descriptors | fd·inode·링크·open/close 의미 | 05 | fd 누수 `EMFILE: Too many open files`; 삭제한 로그가 공간을 안 돌려줌(열린 fd) | fd 테이블(배열) | OSTEP 39 · CS:APP 10 | 필수 | 신규 |
| 23-file-system-implementation | 블록·inode·비트맵·디렉터리·VFS·FFS | 22, data-structure/33-filesystem | `df` 여유 있는데 `No space left on device`(inode 고갈) | 비트맵, 다단계 인덱스, 디렉터리 B-트리(htree) | OSTEP 40 · 41 | 필수 | 신규 (연결: `data-structure/33-filesystem`) |
| 24-crash-consistency-and-journaling | fsck·저널링·COW·LFS | 23 | 전원 장애 후 0바이트 파일·torn write | **WAL(저널)**, 로그 구조 | OSTEP 42 · 43 | 필수 | 신규 |
| 25-fsync-and-durability | write≠디스크, fsync·fdatasync·rename 원자성·디렉터리 fsync | 24 | fsync `EIO` 후 재시도 "성공" 위장 → 조용한 유실(fsyncgate); 디렉터리 fsync 누락 → rename 소실 | — | `fsync(2)` · LWN 752063 · Pillai 외 OSDI 2014 | 필수 | 신규 |
| 26-raid | RAID 0/1/5/6/10·재구축 | architecture/17-storage-media-workload | 재구축 중 2차 디스크 장애·URE → 어레이 유실; RAID5 write hole | 패리티(XOR) | OSTEP 38 | 권장 | 신규 |
| 27-data-integrity-checksums | 조용한 손상·체크섬·스크러빙 | 26 | 비트 부패가 에러 없이 복제·백업까지 전파 | CRC, 체크섬 트리(Merkle) | OSTEP 45 | 권장 | 신규 |
| 28-io-models | 블로킹/논블로킹·동기/비동기 4분면 | 22 | 논블로킹 소켓에서 `EAGAIN` 무시 → busy loop CPU 100% | — | CS:APP 12.2 [?] · Stevens UNP 6.2 [?] | 필수 | 신규 |
| 29-io-multiplexing-epoll | select/poll/epoll, 레벨 vs 엣지 트리거 | 28 | 엣지 트리거에서 끝까지 안 읽음 → 연결 hang; select `FD_SETSIZE` 1024 초과 | select 비트맵 O(n) vs **epoll RB트리 + ready list** | `epoll(7)` · Kegel "C10K" | 필수 | 신규 |
| 30-zero-copy-and-io-uring | sendfile·splice·mmap·io_uring | 29, 14 | zero-copy 경로에 TLS 끼면 사라짐; io_uring 보안 비활성 환경 | 제출/완료 링 버퍼 | `sendfile(2)` · Axboe "Efficient IO with io_uring" 2019 | 심화 | 신규 (연결: `systems/kafka-why-fast` zero-copy 절) |

### 5.5 IPC·링킹·격리·관측

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 31-ipc | 파이프·공유 메모리·유닉스 소켓·메시지 큐 | 22 | 자식 stdout을 안 읽음 → 파이프 버퍼(64KiB) 가득 → 부모·자식 교착 | 링 버퍼 | CS:APP 10·11 [?] · `pipe(7)` | 권장 | 신규 |
| 32-linking-and-loading | 정적/동적 링킹·심볼 해석·PIC·로더 | architecture/08-isa-and-machine-code | `undefined reference to`; `error while loading shared libraries`; alpine(musl)에서 glibc 바이너리 `GLIBC_2.xx not found` | 심볼 테이블(해시), 재배치 | CS:APP 7장 | 권장 | 신규 (연결: `languages/c/syntax/44·45`) |
| 33-virtualization-hypervisor | 하이퍼바이저·VM·steal time | 01 | noisy neighbor → steal time 증가로 원인 모를 지연 | 섀도/중첩 페이지 테이블 | OSTEP 부록 B [?] | 권장 | 신규 |
| 34-containers-namespaces-cgroups | namespace·cgroup·이미지 레이어 | 13, 08 | 컨테이너가 호스트 코어 수를 보고 스레드풀 과다; CPU throttling; PID 1 시그널 미전달 | 계층형 cgroup 트리, 유니온 FS | `namespaces(7)` · `cgroups(7)` | 필수 | 신규 |
| 35-os-observability-tools | top·vmstat·iostat·strace·perf·/proc, USE 방법론 | 02 | load average를 CPU 사용률로 오해(D 상태 I/O 대기 포함) | 샘플링 프로파일러 | Gregg 『Systems Performance』 2판 2장 [?] | 권장 | 신규 |

### 5.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 36-os-symptom-index | 역색인: errno(`EINTR`·`EAGAIN`·`EMFILE`·`ENOSPC`·`ENOMEM`·`EIO`), exit code(137·139·143), D 상태, 좀비, load 높은데 CPU 낮음 | 전체 | — | — | 이 영역 leaf · `errno(3)` | 필수 | 신규 |
| 37-os-incidents | 실사건: Mars Pathfinder 우선순위 역전(1997) · fsyncgate(PostgreSQL, 2018) · 2012 윤초 커널 hrtimer 버그로 Java·MySQL CPU 폭주 · ext4 지연 할당 0바이트 파일(2009) [?] | 36 | — | — | Reeves 1997 (UNC 사본) · LWN 752063 · Red Hat/LKML 2012-07 [?] | 권장 | 신규 |

---

## 6. 프로그래밍 언어·컴파일러 (`language/`)

> **언어 중립 원리**만 둔다(문법 레퍼런스는 CS 밖 — §19 판정). 코드가 실행되기까지(어휘→구문→의미→코드), 타입, 메모리 관리, 동시성 모델, 의존성.
> 뼈대: Aho 외 『Compilers』(Dragon Book, 장 번호 `[?]`), Pierce 『TAPL』 [?], Jones 외 『The Garbage Collection Handbook』 [?], JSR-133(JMM), CS2023 FPL.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 06 → 07 → 08 → 09 → 12 → 13 → 14 → 15 → 16 → 11 → 10 → 17 → 18 → 19 → (05 심화) → 20 → 21

### 6.1 실행 모델과 컴파일 파이프라인

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-compile-interpret-jit | 컴파일·인터프리트·바이트코드·JIT | architecture/08-isa-and-machine-code | JIT 워밍업 전 첫 요청 느림(배포 직후 p99 급등); AOT/JIT 차이로 리플렉션 실패 | 핫스팟 카운터 | Dragon Book 1장 [?] | 필수 | `foundations/compiler-pipeline` (분할 — 바이트코드·PVM 절) |
| 02-lexing-and-regular-languages | 토큰화·정규식·유한 오토마타 | 01 | **ReDoS** — 백트래킹 엔진에서 `(a+)+$` 류가 지수 시간 CPU 100% | NFA/DFA, Thompson 구성 | Dragon Book 3장 [?] · Sipser 1장 [?] · Cox 2007 | 필수 | `foundations/compiler-pipeline` (분할 — 어휘 분석 절) |
| 03-parsing-grammars-ast | BNF·CFG·재귀 하강·AST | 02, data-structure/03-stack | 두 구성 요소의 파서 불일치 → HTTP request smuggling; 깊은 중첩 입력 → 파서 스택 오버플로(JSON bomb) | 재귀 하강, 푸시다운(스택), 트리 | Dragon Book 4장 [?] | 필수 | `foundations/compiler-pipeline` (분할 — BNF·파스 트리·AST 절) |
| 04-semantic-analysis-and-scopes | 심벌 테이블·스코프·바인딩 | 03 | 섀도잉 버그; JS `var` 루프 클로저가 마지막 값만 캡처 | **스코프 체인 = 해시 테이블 스택** | Dragon Book 2.7·6장 [?] | 권장 | `foundations/compiler-pipeline` (분할 — 심벌 테이블 절) · `foundations/variables-and-memory` (분할 — 스코프 절) |
| 05-ir-and-optimization | IR·SSA·인라이닝·데드 코드 제거·레지스터 할당 | 04 | 최적화가 UB 코드의 null 검사를 삭제; 마이크로벤치마크 결과가 DCE로 0ns | 제어 흐름 그래프, 데이터 흐름 분석, 그래프 컬러링 | Dragon Book 8·9장 [?] | 심화 | 신규 |

### 6.2 타입·값·추상화

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 06-type-systems | 정적/동적·강/약·명목/구조·제네릭·변성 | 04 | `ClassCastException`; 제네릭 소거로 런타임 타입 정보 없음; 공변 배열 `ArrayStoreException` | 타입 추론(단일화) | Pierce TAPL 1장 [?] | 필수 | 신규 |
| 07-values-references-passing | 값/참조, 전달 방식, 얕은/깊은 복사, 동일성 vs 동등성 | 06 | 파이썬 가변 기본 인자 공유; 얕은 복사본 수정이 원본 변경; `==` vs `equals` | 참조 그래프 | CS2023 FPL [?] | 필수 | `foundations/variables-and-memory` (분할 — 전달 방식·얕은/깊은 복사 절) |
| 08-scope-closures-first-class-functions | 1급 함수·클로저·람다 | 04, 07 | 클로저가 큰 객체를 붙잡아 누수; 캡처한 가변 변수 경쟁 | 환경 레코드 체인 | SICP 3.2 [?] | 권장 | `foundations/variables-and-memory` (분할 — 람다 절) |
| 09-error-handling-models | 예외·에러 값·Result/Option·panic | 06 | 삼킨 예외(`catch {}`) → **조용한 실패**; `finally` 안 `return` 이 예외 소멸; 체크 안 한 에러 반환값 | 합 타입(태그 유니언) | 언어 명세 각 장 [?] | 필수 | 신규 (연결: `languages/rust/syntax/22·23`, `languages/c/syntax/46`) |
| 10-functional-concepts | 불변·순수 함수·고차 함수·지연 평가 | 08 | 지연 스트림 두 번 소비 → `IllegalStateException: stream has already been operated upon`; `map` 안 부수효과 | 지연 리스트, 영속 자료구조 | SICP 1·3장 [?] | 권장 | 신규 |
| 11-dispatch-and-polymorphism-mechanics | 정적/동적 디스패치·vtable·단형화·인라인 캐시 | 06 | 오버로딩(컴파일 시점) vs 오버라이딩(실행 시점) 혼동 → 엉뚱한 메서드 호출 | vtable(함수 포인터 배열), 인라인 캐시 | Dragon Book [?] | 권장 | 신규 (연결: `languages/rust/syntax/31·33`) |

### 6.3 메모리 관리

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 12-memory-management-models | 수동·참조 카운팅·추적 GC·소유권 | 07, os/11-heap-allocation | 참조 카운팅 순환 → 누수; 수동 관리 use-after-free; 소유권 규칙 위반 → 컴파일 거부 | 참조 카운트, 소유권 그래프 | Jones 외 GC Handbook 1장 [?] | 필수 | `foundations/variables-and-memory` (분할 — 참조 카운트·GC 절) · 연결: `languages/rust/언어-특성` |
| 13-garbage-collection | mark-sweep·copying·세대·동시 GC(G1·ZGC) | 12, algorithm/11-bfs | STW pause → p99 스파이크·헬스체크 실패; `GC overhead limit exceeded`; static 컬렉션 누수로 Full GC 반복 | **도달성 = 그래프 순회**, 삼색 마킹, 카드 테이블 | Jones 외 GC Handbook [?] | 필수 | 신규 |
| 14-language-memory-model | happens-before·data race·volatile·final | 13, architecture/15-cache-coherence-and-memory-ordering | `volatile` 누락 → 종료 플래그 못 봄; DCL 부분 초기화 객체 | happens-before 부분 순서 | JSR-133 · Manson 외 POPL 2005 | 권장 | 신규 (연결: `languages/java/syntax/33-synchronized-and-volatile`) |

### 6.4 동시성 모델

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 15-concurrency-models | 스레드·액터·CSP·async/await·코루틴·가상 스레드 | os/21-event-based-concurrency | async 안 블로킹 호출 → 런타임 정지; 가상 스레드 `synchronized` pinning → 캐리어 고갈 | 상태 기계로 변환된 Future, 채널 큐 | Hoare 1978 (CSP) · JEP 444 | 필수 | 신규 (연결: `languages/java/syntax/56`, `languages/rust/syntax/54·55`) |
| 16-gil-and-runtime-constraints | GIL 같은 런타임 제약 | 15 | CPU 바운드 멀티스레드가 안 빨라짐 | — | Python 문서 (GIL) [?] · PEP 703 | 권장 | `foundations/process-thread` (분할 — GIL 절) |

### 6.5 빌드·생태계·선택

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 17-modules-and-dependency-resolution | 모듈·패키지·semver·락파일 | data-structure/34-dependency-resolver | 다이아몬드 의존 → `NoSuchMethodError`/`ClassNotFoundException`; 락파일 없는 빌드 비재현 | **위상정렬**, 버전 해결 = SAT | semver.org · Cox "Minimal Version Selection" 2018 | 필수 | 신규 (연결: `data-structure/34-dependency-resolver`) |
| 18-undefined-behavior-and-memory-safety | UB·경계 검사·메모리 안전 | 12 | 버퍼 오버런이 크래시 대신 **다른 요청의 데이터 누출**(Cloudbleed·Heartbleed) | — | C 표준 부록 J [?] · CISA 메모리 안전 로드맵 2023 [?] | 권장 | `foundations/languages/c-cpp-csharp.md` (분할) |
| 19-language-choice-tradeoffs | "틀렸을 때 어떻게 틀리는가"로 언어 고르기 | 18, 13 | 조용한 실패를 허용하는 언어·관례 선택 → 정합성 사고 | — | 기존 노트 원고 | 권장 | `foundations/languages/README.md` 축① + `c-cpp-csharp.md` + `go·java·kotlin·rust/언어-특성/` (병합) |

### 6.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 20-pl-symptom-index | 역색인: `NoSuchMethodError`·`ClassCastException`·`NullPointerException`·`StackOverflowError`·`GC overhead`·정규식 CPU 100%·async 정지 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 21-pl-incidents | 실사건: Cloudbleed(2017, 생성된 파서 버퍼 오버런) · Heartbleed(2014, 경계 검사 누락 — 보안 관점은 security/28) · left-pad(2016, 의존성 제거로 빌드 연쇄 실패) | 20 | — | — | Cloudflare 블로그 2017-02-23 · CVE-2014-0160 · npm 블로그 2016-03 [?] | 권장 | 신규 |

# Part 2 — 두 대 사이

## 7. 네트워크 (`network/`) — 신설

> **프로세스 → 소켓 → 커널 스택 → NIC → 스위치(MAC) → 라우터(IP) → … → 역방향 디캡슐화**. 지도(계층·캡슐화)를 먼저 그리고 아래 계층부터 올라온 뒤, 소켓·커널 경로로 "내 프로세스"와 잇고, DNS·TLS·HTTP로 올라가 종합한다.
> 장애의 중심은 TCP(15~22). "TCP 통신 도중 끊기면?"의 본체가 19·20·21이다.
> 뼈대: Kurose & Ross 8판(이하 K&R — 9판도 1~5장 제목 동일 확인, 6~8장 번호는 8판 기준), Stevens 『TCP/IP Illustrated Vol.1』 2판(이하 Stevens — 13·14·17장 외 장 번호 `[?]`), Grigorik 『High Performance Browser Networking』(이하 HPBN — 장 제목으로 인용), Beej's Guide, RFC.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 06 → 05 → 07 → 08 → 10 → 12 → 13 → 11 → 09 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27 → 28 → security/03~07 → 29 → 30 → 31 → 32 → 33 → 34 → 35 → 36 → 37 → 38 → 39 → 40 → 41 → 42 → 43 → 44 → 45

### 7.0 지도

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-layer-map-osi-tcpip | OSI 7 vs TCP/IP 4계층, 계층별 프로토콜·PDU(세그먼트/패킷/프레임) | — | 증상의 계층을 못 짚음 → "네트워크 문제"로 뭉뚱그려 진단 지연 | 계층 = 인터페이스 스택 | K&R 1.5 · RFC 1122 | 필수 | 신규 |
| 02-encapsulation | 헤더가 붙고 벗겨지는 과정, 계층별 헤더 필드 | 01 | 터널·VPN 헤더 오버헤드로 MTU 초과 → 큰 패킷만 실패(12로 이어짐) | 헤더 = 고정 오프셋 레코드 | K&R 1.5.2 | 필수 | 신규 |
| 03-latency-bandwidth-bdp | 지연 4요소(처리·큐잉·전송·전파), 대역폭 vs 지연, BDP | 02 | 고BDP(대륙 간) 링크에서 윈도 부족 → 대역폭 놔두고 느림; 큐잉 지연 = bufferbloat | 큐(math/15) | K&R 1.4 · HPBN "Primer on Latency and Bandwidth" | 필수 | 신규 |

### 7.1 링크 계층

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-ethernet-and-mac | 이더넷 프레임·MAC 주소·충돌 도메인 | 02 | duplex 불일치 → CRC 에러·late collision으로 간헐 느림 [?] | CRC32 프레임 검사 | K&R 6.4.2 | 필수 | 신규 |
| 05-switching-and-vlan | 허브 vs 스위치, 자가 학습·플러딩·에이징, VLAN, STP | 04 | L2 루프 + STP 부재 → **브로드캐스트 스톰**으로 망 전체 마비; MAC 테이블 가득 → 플러딩 | **MAC 테이블 = 해시(CAM)**, 스패닝 트리 | K&R 6.4.3–6.4.4 · IEEE 802.1D [?] | 권장 | 신규 |
| 06-arp | IP→MAC 해석, ARP 캐시, gratuitous ARP | 04 | VIP 페일오버 후 이웃의 stale ARP → 죽은 서버로 계속 전송; IP 충돌; ARP 스푸핑 | ARP 캐시(해시 + 타이머) | RFC 826 · K&R 6.4.1 | 필수 | 신규 |

### 7.2 네트워크 계층

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 07-ip-addressing-cidr | IPv4/IPv6 주소, 서브넷·CIDR·사설 대역 | 01 | VPC 피어링 CIDR 겹침 → 라우팅 불가; 도커 기본 브리지 172.17/16이 사내망과 충돌 → 특정 대역만 접속 불가 | 비트 마스크 | RFC 791 · 4632 · 1918 · 8200 · K&R 4.3 | 필수 | 신규 |
| 08-routing-and-longest-prefix-match | 라우팅 테이블·**최장 접두사 매칭**·기본 게이트웨이·TTL | 07, data-structure/20-radix-trie | 라우팅 루프 → `Time to live exceeded`; 블랙홀 라우트 → 조용한 드롭; 비대칭 라우팅 + 상태 방화벽 → 응답만 차단 | **radix/PATRICIA 트라이**, 포워딩 테이블 | K&R 4.2.1 · RFC 1812 | 필수 | 신규 |
| 09-routing-protocols-ospf-bgp | 링크 상태(OSPF) vs 거리 벡터 vs 경로 벡터(BGP) | 08, algorithm/14-dijkstra | BGP 경로 누출·하이재킹 → 대규모 도달 불가(Facebook 2021·Pakistan-YouTube 2008) | **OSPF = 다익스트라**, 거리 벡터 = 벨만-포드 | K&R 5.2–5.4 · RFC 2328 · 4271 | 권장 | 신규 |
| 10-icmp-ping-traceroute | ICMP 메시지·ping·traceroute 원리 | 08 | ICMP 전면 차단 → PMTUD 깨짐(12); ping 된다 ≠ 서비스 된다 | TTL 증가 탐색 | RFC 792 · K&R 5.6 | 필수 | 신규 |
| 11-dhcp | 주소 자동 할당·리스 | 07 | DHCP 풀 고갈 → 새 기기 `169.254.x.x`(링크 로컬) | 리스 테이블 | RFC 2131 · K&R 4.3.3 | 권장 | 신규 |
| 12-fragmentation-mtu-pmtud | MTU·IP 단편화·DF·PMTUD | 10, 02 | **PMTUD 블랙홀** — 작은 요청은 되는데 큰 응답·TLS 인증서 전송에서 hang(VPN·터널) | — | RFC 1191 · 8899 · Cloudflare "IP fragmentation is broken" | 필수 | 신규 |
| 13-nat-and-conntrack | SNAT/DNAT·포트 매핑·연결 추적·idle timeout | 07 | NAT idle timeout 후 재사용 → RST(AWS NAT GW 350s); `nf_conntrack: table full, dropping packet`; SNAT 포트 고갈 | **conntrack = 해시 테이블 + 타이머** | RFC 3022 · 5382 · AWS NAT GW 문서 | 필수 | 신규 |

### 7.3 전송 계층 — UDP

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 14-udp | 무연결·포트 다중화·체크섬, 사용처(DNS·QUIC·스트리밍) | 01 | 소켓 수신 버퍼 넘침 → `netstat -su` "receive buffer errors" 조용한 손실; 반사·증폭 DDoS | 포트 → 소켓 해시 | RFC 768 · K&R 3.3 · HPBN "Building Blocks of UDP" | 필수 | 신규 |

### 7.4 전송 계층 — TCP (장애의 중심)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 15-tcp-handshake-and-backlog | 3-way handshake, SYN 큐·accept 큐(listen backlog) | 14 | 포트 닫힘 → RST → `ECONNREFUSED`; 방화벽 drop → SYN 재전송 후 `ETIMEDOUT`; accept 큐 가득 → 서버 로그 없이 connect 지연(`ListenOverflows`) | SYN 큐(해시), accept 큐(FIFO), SYN cookie | RFC 9293 3.5 · Stevens 13장 · Cloudflare "SYN packet handling in the wild" | 필수 | 신규 |
| 16-tcp-reliability-retransmission | 시퀀스·누적 ACK·RTO·fast retransmit·SACK | 15 | 손실·재정렬 → 에러 없는 꼬리 지연; RTO 백오프로 수 초 멈춤 | **RTO = SRTT/RTTVAR 지수 가중 이동 평균(EWMA)**, 슬라이딩 윈도 | RFC 6298 · 2018 · Stevens 14장 · K&R 3.4–3.5 | 필수 | 신규 |
| 17-tcp-flow-control | 수신 윈도·zero window·window scaling | 16 | 느린 소비자 → zero window 무한 대기(연결은 살아 있음); 윈도 스케일 옵션 제거 장비 → 처리량 64KB/RTT 상한 | 슬라이딩 윈도, 링 버퍼 | RFC 7323 · Stevens 15장 [?] · K&R 3.5.5 | 필수 | 신규 |
| 18-tcp-congestion-control | slow start·AIMD·fast recovery·CUBIC·BBR | 17 | 유휴 후 slow start 재시작 → 첫 응답 느림; bufferbloat → 지연 수백 ms | **AIMD 제어 루프**, cwnd 상태 기계 | RFC 5681 · 9438 · K&R 3.6–3.7 · HPBN "Building Blocks of TCP" | 필수 | 신규 |
| 19-tcp-termination-fin-rst-half-open | 4-way 종료·상태 다이어그램, FIN vs RST, half-open | 15 | FIN → `read()` 0(EOF); RST → `ECONNRESET`; 닫힌 소켓에 write → `EPIPE`·SIGPIPE; half-open(상대 재부팅·케이블 단절) → 보낼 게 없으면 영원히 살아 보이고 `read` 무한 대기 | **TCP 상태 기계(11상태)** | RFC 9293 3.6 · Stevens 13장 · Cloudflare "When TCP sockets refuse to die" | 필수 | 신규 |
| 20-time-wait-and-close-wait | TIME_WAIT의 존재 이유, CLOSE_WAIT의 의미 | 19 | TIME_WAIT 누적 → 임시 포트 고갈 `EADDRNOTAVAIL`(Cannot assign requested address); CLOSE_WAIT 누적 = **앱이 close 안 함** → fd 고갈 `EMFILE` | 4-튜플 해시 | Bernat 2014 "Coping with the TCP TIME-WAIT state" · Stevens 13장 | 필수 | 신규 |
| 21-tcp-keepalive-and-user-timeout | keepalive·`TCP_USER_TIMEOUT`·앱 heartbeat | 19, 13 | 기본 keepalive 7200s가 NAT/LB idle timeout보다 길어 무용; 상대가 사라져도 write는 성공(커널 버퍼) → 한참 뒤 `ETIMEDOUT`(retries2 ≈ 15분 [?]) | 타이머(data-structure/37) | RFC 1122 4.2.3.6 · RFC 5482 · Stevens 17장 · `tcp(7)` | 필수 | 신규 |
| 22-nagle-and-delayed-ack | Nagle × delayed ACK 상호작용 | 16 | 작은 write 두 번 → 요청당 ~40ms 고정 지연; 해결 `TCP_NODELAY` | — | RFC 896 · 1122 4.2.3.2 | 권장 | 신규 |

### 7.5 소켓과 커널 경로 — "프로세스가 NIC로 나가는 길"

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 23-socket-api | socket/bind/listen/accept/connect/send/recv/close, 송수신 버퍼, fd | 15, os/22-files-and-descriptors | 부분 write/read 미처리(short write) → 메시지 잘림; 재시작 시 `Address already in use`(`SO_REUSEADDR`) | fd 테이블, 소켓 버퍼 | Beej · CS:APP 11.4 · `socket(7)` | 필수 | 신규 |
| 24-application-protocol-framing | TCP는 바이트 스트림 — 길이 접두·구분자·TLV 프레이밍 | 23 | 메시지 경계 가정 → 두 메시지가 한 read에 붙거나 쪼개져 파싱 오류(간헐, 부하 시에만) | 길이 접두 파서, 상태 기계 | Redis RESP 명세 · Beej 7.5 [?] | 필수 | `systems/resp-protocol` |
| 25-kernel-network-stack | 송신: 소켓→TCP/IP→qdisc→드라이버→NIC(DMA) / 수신: NIC→DMA→IRQ→NAPI/softirq→IP→TCP→소켓 버퍼 | 23, architecture/16-io-devices-interrupts-dma | NIC 링 오버플로 → `rx_dropped` 조용한 손실; softirq가 한 코어에 몰림 → 그 코어 100%·나머지 한가 | **DMA 링 버퍼**, `sk_buff` 연결 리스트, RSS 해시 | packagecloud "Monitoring and Tuning the Linux Networking Stack" 수신·송신편 | 권장 | 신규 |
| 26-packet-journey | 종합: 프로세스→소켓→커널→NIC→스위치→라우터→…→수신측 역방향 | 25, 08, 06 | (종합편 — 각 구간에서 무엇이 보이나를 한 장으로) | — | 『성공과 실패를 결정하는 1%의 네트워크 원리』 [?] · alex/what-happens-when | 필수 | 신규 |

### 7.6 DNS

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-dns-resolution | 재귀·반복 질의, 루트/TLD/권한, 레코드(A/AAAA/CNAME/MX/NS/TXT) | 14 | 권한 서버 장애 → `SERVFAIL`; CNAME at apex 불가; 해석기 없는 컨테이너 → `UnknownHostException` | **도메인 트리(역순 라벨 트라이)** | RFC 1034 · 1035 · K&R 2.4 | 필수 | 신규 |
| 28-dns-caching-and-ttl | TTL·캐시 계층·부정 캐시·검색 도메인 | 27 | 페일오버 후 **JVM DNS 캐시**로 죽은 IP 접속; NXDOMAIN 부정 캐시로 새 레코드가 한참 안 보임; k8s `ndots:5` 로 외부 조회 5배 | TTL 캐시(해시 + 만료) | RFC 2308 · Java `networkaddress.cache.ttl` 문서 | 필수 | 신규 |

### 7.7 TLS·인증서 (암호 기초는 security/03~07 선행)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 29-tls-handshake | TLS 1.3 1-RTT·0-RTT, 1.2와 차이, SNI·ALPN | 23, security/07-key-exchange-forward-secrecy | 버전·암호군 불일치 → `handshake_failure`; SNI 누락 → 기본 인증서 응답(호스트명 불일치); 0-RTT 재전송 공격 | 핸드셰이크 상태 기계, HKDF | RFC 8446 · 6066 · 7301 · HPBN "Transport Layer Security" | 필수 | 신규 |
| 30-x509-and-chain-validation | 인증서 구조·체인 검증(리프→중간→루트)·루트 스토어·호스트명 검증 | 29, security/06-public-key-and-signatures | 중간 인증서 누락 → "브라우저는 되는데 서버 간 호출만 실패"(`unable to get local issuer certificate`/`PKIX path building failed`); 만료 `certificate has expired`; clock skew → not yet valid | **체인 = 그래프 경로 탐색** | RFC 5280 6장 · badssl.com | 필수 | 신규 |
| 31-revocation-ocsp-ct | CRL·OCSP·stapling·Certificate Transparency, 수명 단축 흐름 | 30 | OCSP 응답기 장애 → hard-fail 클라이언트 연결 실패; Let's Encrypt OCSP 종료(2025)·수명 단축(SC-081)으로 갱신 주기 압박 | CT = **Merkle 트리**(data-structure/27) | RFC 6960 · 9162 · Let's Encrypt 2024-12-05 공지 · CA/B SC-081 | 권장 | 신규 |
| 32-mtls-and-cert-operations | 상호 TLS, ACME 자동 갱신, 인증서 인벤토리 | 30 | 갱신 누락 → 만료 전면 장애; 클라이언트 인증서 미제시 → TLS 1.3 `certificate_required`(alert 116) | 만료 타이머 | RFC 8555 · 8446 6.2 | 권장 | 신규 |

### 7.8 HTTP

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 33-http-semantics | 메서드·상태코드·헤더·안전/멱등·쿠키 | 23 | 502(상류 응답 불량) vs 503(과부하/미준비) vs 504(상류 타임아웃) 혼동 → 엉뚱한 곳 진단 | 헤더 = 다중값 맵 | RFC 9110 · 6265 | 필수 | 신규 |
| 34-http-caching | Cache-Control·ETag·조건부 요청·Vary·휴리스틱 캐시 | 33 | `Vary` 누락 → **다른 사용자의 응답을 캐시가 반환**(개인정보 노출); 헤더 없는 응답 휴리스틱 캐싱 → 배포 반영 지연 | 캐시 키 해시, LRU | RFC 9111 | 필수 | 신규 |
| 35-http-connection-management | keep-alive·커넥션 풀·idle timeout 정렬 | 33, 21 | 서버 idle close와 클라이언트 재사용 경합 → `socket hang up`·`Connection reset`·간헐 502; 풀 고갈 → 대기 타임아웃 | 커넥션 풀(큐·LRU) | RFC 9112 9장 · HPBN "HTTP/1.X" | 필수 | 신규 |
| 36-http2-multiplexing | 스트림·프레임·HPACK·흐름 제어, TCP HoL | 35 | 손실 한 번에 모든 스트림 정지(TCP HoL); `GOAWAY` 미처리 → 재시도 실패; 동시 스트림 한도 | HPACK 정적/동적 테이블, 우선순위 트리 | RFC 9113 · 7541 · HPBN "HTTP/2" | 권장 | 신규 |
| 37-http3-quic | QUIC 스트림 독립·연결 마이그레이션·0-RTT | 36, 14 | UDP 차단망 → 폴백 지연; 방화벽이 QUIC 인식 못 함 | 패킷 번호 공간, 손실 탐지 | RFC 9000 · 9114 | 권장 | 신규 |
| 38-websocket-sse-long-lived | WebSocket·SSE·롱폴링 | 35 | LB/프록시 idle timeout에 조용히 끊김; 서버 재배포 시 재연결 폭풍 | 브로드캐스트 팬아웃 | RFC 6455 · HTML 표준 SSE 절 · HPBN "WebSocket" | 권장 | 신규 (연결: `foundations/web-api/32·33`) |

### 7.9 인프라·종합

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 39-load-balancers-and-proxies | L4 vs L7, 리버스 프록시, 헬스체크, 연결 드레이닝 | 35, 13 | 깊은 헬스체크 → 의존성 장애가 전 인스턴스 제외로 번짐; `X-Forwarded-For` 스푸핑; sticky 세션 불균형 | 라운드로빈·least-conn·**일관 해싱/Maglev** | `systems/server-design` 02 · Eisenbud 외 NSDI 2016 (Maglev) | 필수 | `systems/server-design/02-request-path.md` (분할 — LB·게이트웨이·헬스체크 절) |
| 40-cdn-and-edge | CDN 캐시 계층·원점 보호·무효화 | 34 | 캐시 키에 쿠키·쿼리 누락 → 개인화 페이지 교차 노출; 퍼지 누락 | 계층 캐시 | HPBN 1장 [?] · 각 CDN 문서 | 권장 | 신규 |
| 41-firewalls-and-network-policy | 상태 방화벽·보안 그룹·iptables/nftables | 13 | drop(→ `ETIMEDOUT`) vs reject(→ `ECONNREFUSED`) 증상 차이 무시; 규칙 수천 개 → 선형 매칭 지연 | 규칙 선형 탐색 vs ipset 해시·nftables 집합 | `iptables(8)` · `nft(8)` | 권장 | 신규 |
| 42-what-happens-when-url | 종합: URL 입력 → DNS → TCP → TLS → HTTP → 렌더링 | 26, 28, 29, 33 | (구간별 실패 지도) | — | alex/what-happens-when | 필수 | 신규 |
| 43-network-diagnostics | `ss`·`tcpdump`/Wireshark·`curl -v`·`openssl s_client`·`dig`·`mtr`·`ip route` | 42 | 도구 없이 추측 진단 | BPF 필터 | 각 man page | 필수 | 신규 |

### 7.10 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 44-network-symptom-index | **에러 코드 사전**: `ECONNRESET`·`EPIPE`·`ETIMEDOUT`·`ECONNREFUSED`·`EADDRNOTAVAIL`·`EMFILE`·`EHOSTUNREACH`·`SERVFAIL`·`NXDOMAIN`·TLS alert·502/503/504 → 원인 leaf | 전체 | — | — | 이 영역 leaf · `errno(3)` | 필수 | 신규 |
| 45-network-incidents | 실사건: Facebook BGP·DNS 전면 장애(2021-10-04) · Let's Encrypt DST Root CA X3 만료로 구형 클라이언트 체인 실패(2021-09-30) · Pakistan Telecom YouTube BGP 하이재킹(2008-02) | 44 | — | — | Facebook Engineering 2021-10-05 · Let's Encrypt 2021 공지 · RIPE NCC 2008 분석 | 권장 | 신규 |

---

## 8. 보안 (`security/`)

> 원리 → 암호 기초 → 인증·인가 → 웹/앱 공격 → 공급망·운영. **TLS/PKI 본문은 network/29~32에만** 둔다(단일 출처) — 여기선 암호 부품과 신뢰 모델까지.
> 뼈대: OSTEP 53~57(Security 파트), K&R 8장, OWASP Top 10 2021, Aumasson 『Serious Cryptography』 [?], RFC.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → (network/29~32) → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27 → 28

### 8.1 원리

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-security-principles | CIA·최소 권한·심층 방어·fail-safe 기본값·완전한 중재 | — | 에러 시 허용(fail-open) → 인증 서버 장애 때 모두 통과 | — | Saltzer–Schroeder 1975 · OSTEP 53 | 필수 | 신규 |
| 02-threat-modeling | 자산·공격 표면·신뢰 경계·STRIDE | 01 | 신뢰 경계 안쪽 입력을 검증 안 함 → 내부망 SSRF·권한 상승 | 데이터 흐름 다이어그램 | Shostack 『Threat Modeling』 [?] · OWASP A04 | 권장 | 신규 |

### 8.2 암호 기초

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 03-symmetric-encryption-and-aead | 블록 암호·운용 모드·AEAD(AES-GCM·ChaCha20-Poly1305) | 01, math/13-information-theory-basics | ECB → 패턴 노출; **GCM nonce 재사용** → 평문 XOR 노출·인증 위조; 인증 없는 CBC → 패딩 오라클 | 블록·카운터 모드 | OSTEP 56 · NIST SP 800-38D · RFC 8439 | 필수 | 신규 |
| 04-hash-functions-and-digests | 암호 해시의 3성질·SHA-2·길이 확장 | 03 | MD5/SHA-1 충돌 → 위조 인증서·파일; `H(key‖msg)` 를 MAC으로 → 길이 확장 공격 | Merkle–Damgård 구조 | FIPS 180-4 | 필수 | `foundations/security/sha256-and-digest.md` |
| 05-mac-and-hmac | 무결성+출처 인증, HMAC | 04 | 비상수 시간 비교 → 타이밍 공격; 서명 원문 정규화(JSON 키 순서·공백) 불일치 → 웹훅 서명 검증 `401` | HMAC 이중 해시 | RFC 2104 · 4231 | 필수 | `foundations/security/hmac.md` |
| 06-public-key-and-signatures | RSA·ECC·전자서명(ECDSA·Ed25519) | 04, math/06-modular-arithmetic | 서명 검증 생략·알고리즘 혼동; ECDSA nonce 재사용 → 개인키 유출(PS3 2010) | 모듈러 거듭제곱, 타원곡선 군 연산 | RFC 8017 · 8032 · OSTEP 56 | 필수 | 신규 |
| 07-key-exchange-forward-secrecy | DH·ECDHE·전방 비밀성 | 06 | 정적 RSA 키 교환 → 키 유출 시 과거 트래픽 전부 복호화 | 이산 로그 | RFC 7748 · RFC 8446 부록 [?] | 권장 | 신규 |
| 08-password-storage-and-kdf | salt·느린 KDF(bcrypt·scrypt·Argon2)·pepper | 04 | 평문·단일 SHA-256 저장 → 유출 시 GPU로 대량 크래킹; bcrypt 72바이트 초과 절단 | 메모리 하드 함수 | RFC 9106 · OWASP Password Storage Cheat Sheet | 필수 | 신규 |
| 09-randomness-and-key-management | CSPRNG·키 수명·회전·KMS·시크릿 관리 | 03, math/11-randomness-and-prng | 하드코딩 시크릿 git 유출; 회전 절차 부재 → 유출 후 대응 불가 | 봉투 암호화(키 계층 트리) | NIST SP 800-57 [?] | 필수 | 신규 |

### 8.3 인증·인가

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 10-authentication-basics | 지식/소유/생체, MFA·TOTP·WebAuthn | 08 | 크리덴셜 스터핑; MFA 푸시 피로 공격; 계정 열거(로그인 에러 메시지 차이) | HOTP/TOTP(HMAC 카운터) | OSTEP 54 · RFC 6238 · W3C WebAuthn | 필수 | 신규 |
| 11-sessions-and-cookie-security | 세션 ID·고정·쿠키 속성(HttpOnly·Secure·SameSite) | 10, network/33-http-semantics | SameSite 기본값(Lax) 변경으로 크로스 사이트 SSO 콜백 깨짐; 세션 고정 | 세션 저장소(해시 + TTL) | RFC 6265 · OWASP Session Mgmt Cheat Sheet | 필수 | 신규 |
| 12-tokens-and-jwt | 자기 포함 토큰·서명·만료·폐기 | 06, 11 | `alg: none`·HS/RS 혼동 수락; `exp` 미검증; 폐기 불가 → 탈취 토큰이 만료까지 유효 | — | RFC 7519 · 8725 | 필수 | 신규 |
| 13-jwks-and-key-rotation | 공개키 배포·`kid`·캐시·회전 | 12 | 키 회전 직후 `kid` 캐시 미스 → 401 폭증; JWKS 엔드포인트 장애 → 전면 인증 실패 | `kid` → 키 맵(TTL 캐시) | RFC 7517 | 권장 | `foundations/security/jwks.md` |
| 14-oauth2-and-oidc | 위임 인가·인가 코드+PKCE·ID 토큰 | 12 | `redirect_uri` 느슨한 검증 → 코드 탈취; `state` 누락 → 로그인 CSRF; access token을 인증으로 오용 | — | RFC 6749 · 7636 · OIDC Core 1.0 | 필수 | `foundations/security/oidc.md` |
| 15-access-control-models | ACL·RBAC·ABAC·ReBAC, 객체 수준 인가 | 01 | **IDOR/BOLA** — ID만 바꾸면 남의 데이터(OWASP A01); 수평·수직 권한 상승 | 역할 그래프, 관계 그래프 탐색(Zanzibar) | OSTEP 55 · OWASP A01 · Pang 외 USENIX ATC 2019 | 필수 | 신규 (연결: `domain-modeling/advanced/28-authorization`) |
| 16-identifiers-and-enumeration | 순차 ID vs 랜덤·불투명 식별자 | 15, math/05-counting-and-birthday-bound | 순차 ID 열거로 대량 수집(Optus 2022 [?]); 짧은 랜덤 ID 충돌 | UUIDv4/v7, ULID | RFC 9562 | 권장 | `foundations/security/identity-and-ids.md` |

### 8.4 웹·애플리케이션 공격

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 17-injection | SQL·명령·LDAP 인젝션, 파라미터 바인딩 | 01, language/03-parsing-grammars-ast | 문자열 연결 쿼리 → 데이터 유출·`' OR 1=1`; 셸 경유 실행 → 원격 명령 실행 | 파서 문맥 분리 | OWASP A03 | 필수 | 신규 |
| 18-xss-and-csp | 반사·저장·DOM XSS, 문맥별 인코딩, CSP | 17 | 세션 탈취·계정 탈취; `innerHTML` 에 사용자 입력 | 문맥 인코딩 상태 기계 | OWASP A03 · W3C CSP Level 3 | 필수 | 신규 (연결: `foundations/web-api/04-textcontent-innerhtml-innertext`) |
| 19-csrf-and-samesite | 교차 사이트 요청 위조, 토큰·SameSite·Origin 검사 | 11 | 상태 변경 GET → 이미지 태그로 송금; CSRF 토큰 누락 → 403 대신 성공 | 동기화 토큰 | OWASP CSRF Cheat Sheet | 필수 | 신규 |
| 20-same-origin-and-cors | 출처 모델·SOP·CORS·preflight | 11 | 콘솔 CORS 에러인데 **서버는 200**(브라우저가 응답 차단); `credentials` + `*` 불가; preflight 405 | 출처 튜플 비교 | RFC 6454 · WHATWG Fetch "CORS protocol" | 필수 | 신규 (연결: `foundations/web-api/28-cors-simple-and-preflight`, `29-credentials-and-cookies`) |
| 21-ssrf | 서버가 대신 요청하게 만들기 | 20, network/07-ip-addressing-cidr | 클라우드 메타데이터 `169.254.169.254` 로 자격 증명 유출(Capital One 2019); DNS rebinding으로 허용 목록 우회 | IP 대역 판정(CIDR) | OWASP A10 | 필수 | 신규 |
| 22-deserialization-and-parser-attacks | 안전하지 않은 역직렬화·XXE·문자열 lookup 기능 | 17 | 역직렬화 가젯 → RCE; 로그 문자열 `${jndi:...}` → RCE(Log4Shell) | — | OWASP A08 · CVE-2021-44228 | 권장 | 신규 |
| 23-memory-safety-exploits | 버퍼 오버플로·UAF·ROP·완화책(ASLR·NX·카나리) | language/18-undefined-behavior-and-memory-safety | 경계 밖 읽기 → 개인키·세션 누출(Heartbleed) | — | CS:APP 3.10.3–3.10.4 | 권장 | 신규 |

### 8.5 공급망·운영

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 24-supply-chain-security | 의존성 위험·SBOM·서명·재현 빌드 | language/17-modules-and-dependency-resolution | 미패치 구성 요소(OWASP A06, Equifax 2017); 유지보수자 장악 백도어(xz 2024); typosquatting | 의존성 그래프, Merkle 서명 로그(Sigstore) | OWASP A06 · A08 · SLSA | 권장 | 신규 |
| 25-security-logging-and-audit | 보안 로그·감사 추적·단계적 강제(audit→enforce) | 01 | 로그에 토큰·비밀번호·PII 기록; 감사 로그 부재 → 침해 범위 산정 불가(OWASP A09) | 해시 체인(변조 탐지) | OWASP A09 | 권장 | `foundations/security/audit-enforce-rollout.md` (연결: `engineering/development-standards/security-standards`) |
| 26-dos-and-abuse | 볼륨·프로토콜·애플리케이션 계층 DoS, 봇·남용 | network/15-tcp-handshake-and-backlog | SYN flood, slowloris → 커넥션 고갈; 비싼 엔드포인트 반복 호출 → DB 과부하 | 토큰 버킷(reliability/10) | K&R 8장 [?] · Cloudflare 학습 센터 | 권장 | 신규 |

### 8.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-security-symptom-index | 역색인: 401 vs 403, CORS 에러, `invalid signature`, `kid not found`, CSRF 403, TLS alert, 로그인 폭주, 메타데이터 접근 로그 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 28-security-incidents | 실사건: Heartbleed(2014) · Equifax Struts 미패치(2017) · Capital One SSRF(2019) · Log4Shell(2021) · xz 백도어(2024) | 27 | — | — | CVE-2014-0160 · 미 GAO-18-559 [?] · CVE-2021-44228 · CVE-2024-3094 | 권장 | 신규 |

# Part 3 — 데이터

## 9. 데이터베이스 (`database/`) — 신설

> 모델·SQL → 스토리지 → 인덱스 → 쿼리 처리 → 트랜잭션·동시성 제어 → 로깅·복구 → 복제·분할 → 애플리케이션과 DB. 기존 보유(LSM·파티셔닝·clickhouse·RLS·시계열)는 대부분 스토리지·분할 쪽이므로 **트랜잭션·격리 수준·MVCC·WAL**이 신규의 중심.
> 뼈대: CMU 15-445 Fall 2024 강의 번호(이하 L#, 확인), DDIA 1판 2~7장(확인), Berenson 외 1995, PostgreSQL·MySQL 문서.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 07 → 09 → 12 → 13 → 17 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 28 → 32 → 33 → 34 → 38 → 29 → 30 → (06 · 08 · 10 · 11 · 14 · 16 · 27 · 35 · 36 · 37 권장) → (15 · 18 · 31 심화) → 39 → 40

### 9.1 모델·SQL

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-relational-model-and-algebra | 릴레이션·튜플·관계 대수(σ·π·⋈) | math/03-sets-relations-orders | 행 순서를 가정한 코드 → `ORDER BY` 없는 결과가 플랜 바뀌자 뒤섞임 | 집합 연산 | L1 · DDIA 2장 | 필수 | 신규 |
| 02-keys-and-constraints | PK·FK·UNIQUE·CHECK·NOT NULL | 01 | 제약 없이 앱 검증만 → 동시 요청에 중복·고아 행; UNIQUE 컬럼에 NULL 다중 허용 | 제약 검사 = 인덱스 조회 | L1 · PostgreSQL 문서 5.5 [?] | 필수 | 신규 (연결: `languages/sql/syntax/43·44·45`) |
| 03-normalization | 함수 종속·1NF~BCNF·반정규화 판단 | 02 | 갱신 이상 → 같은 사실이 두 곳에서 다른 값; 과정규화 → 조인 폭발 | 함수 종속 폐포 | Silberschatz 『Database System Concepts』 7장 [?] | 필수 | 신규 |
| 04-sql-joins-and-aggregation | 논리 처리 순서·조인·집계·NULL 3치 논리 | 01 | 조인 팬아웃 → `SUM` 부풀림; `NOT IN (… NULL …)` → 빈 결과; `WHERE` vs `ON` 외부 조인 차이 | — | L2 | 필수 | 신규 (연결: `languages/sql/syntax/01·04·13~25`) |
| 05-window-functions-and-cte | 윈도 함수·프레임·CTE·재귀 CTE | 04 | `RANGE` 기본 프레임 → 동률 행이 같은 누계; 재귀 CTE 종료 조건 누락 → 무한 | — | L2 | 권장 | 신규 (연결: `languages/sql/syntax/26~33`) |
| 06-data-models-document-graph | 관계 vs 문서 vs 그래프, 스키마 온 리드 | 01 | 문서 모델에 다대다 → 조인을 앱에서 → 불일치; 스키마 없는 쓰기 → 읽기 시 파싱 실패 | 트리(문서)·그래프 | DDIA 2장 | 권장 | 신규 |

### 9.2 스토리지

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 07-pages-and-tuple-layout | 힙 파일·슬롯 페이지·튜플 헤더·대형 값(TOAST) | 01, architecture/17-storage-media-workload | 넓은 행 → 페이지당 행 수 감소 → 스캔 I/O 증가; UPDATE 반복 → 페이지 부풀림(bloat) | 슬롯 배열 | L3 · L4 | 필수 | 신규 |
| 08-row-vs-column-storage | 행 저장 vs 컬럼 저장·압축 | 07 | OLAP 쿼리를 행 저장 OLTP DB에서 → 전체 스캔; 컬럼 저장에 단건 UPDATE → 느림 | 런 렝스·딕셔너리 인코딩, 비트맵 | L5 · DDIA 3장 | 권장 | 신규 (연결: `systems/clickhouse-mergetree`) |
| 09-buffer-pool | 버퍼 풀·핀·dirty·교체 정책 | 07, data-structure/10-lru-cache | 대형 순차 스캔이 버퍼 풀 오염(sequential flooding) → 이후 OLTP 적중률 급락 | **page table 해시 + LRU-K/CLOCK** | L6 | 필수 | 신규 |
| 10-lsm-storage-engine | memtable·SSTable·compaction·쓰기/읽기/공간 증폭 | 07, data-structure/24-lsm-tree | compaction 적체 → write stall; tombstone 누적 → 범위 조회 느림 | LSM, 블룸 필터, 스킵 리스트 | DDIA 3장 · O'Neil 외 1996 | 권장 | `systems/lsm-tree` |

### 9.3 인덱스

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 11-hash-indexes | 정적·확장·선형 해싱 | 09, data-structure/05-hashmap | 범위 조회에 해시 인덱스 → 미사용; 해시 버킷 분할 중 지연 | 확장 해싱, 선형 해싱 | L7 | 권장 | 신규 |
| 12-btree-indexes | B+Tree 구조·분할/병합·클러스터드 vs 보조 | 09, data-structure/15-b-tree | 랜덤 UUID PK → 페이지 분할·쓰기 증폭; 인덱스 컬럼에 함수 적용 → 인덱스 미사용 | **B+Tree** | L8 · L9 | 필수 | 신규 |
| 13-index-design | 복합·커버링·부분·표현식 인덱스, 선택도 | 12 | 복합 인덱스 선행 컬럼 누락 → 풀스캔; 인덱스 과다 → 쓰기 느려짐 | — | L8 · Winand 『SQL Performance Explained』 [?] | 필수 | 신규 (연결: `languages/sql/syntax/46·47`) |
| 14-filters-and-specialized-indexes | 블룸 필터·역색인·공간·BRIN | 12 | 전문 검색을 `LIKE '%x%'` 로 → 풀스캔 | 블룸, 역색인, R-tree | L9 | 권장 | 신규 (연결: `data-structure/11·25·32`) |
| 15-index-concurrency-control | 래치·래치 크래빙·B-link 트리 | 12, os/16-locks-and-spinlocks | 핫 인덱스 페이지 래치 경합 → 단조 증가 키 삽입 병목 | 래치 크래빙 | L10 · Lehman–Yao 1981 | 심화 | 신규 |

### 9.4 쿼리 처리

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 16-sorting-and-aggregation | 외부 정렬·해시 집계·스필 | 09, algorithm/34-external-sort-and-k-way-merge | `work_mem` 초과 → 디스크 스필로 수십 배 느림(`Sort Method: external merge`) | 외부 병합 정렬, 해시 테이블 | L11 | 권장 | 신규 |
| 17-join-algorithms | 중첩 루프·해시 조인·정렬 병합 조인 | 16 | 추정 오류로 대형 테이블에 중첩 루프 → 쿼리 수 분 | 해시 테이블, 병합 | L12 | 필수 | 신규 |
| 18-query-execution-models | 반복자(Volcano)·벡터화·병렬 실행 | 17 | — (행 단위 반복의 CPU 오버헤드) | 반복자 트리 | L13 · L14 | 심화 | 신규 |
| 19-query-optimizer-and-explain | 비용 기반 최적화·통계·카디널리티 추정·EXPLAIN 읽기 | 17, 13 | 통계 오래됨 → 플랜 급변으로 야간 배치 후 쿼리 폭주; 추정 vs 실제 행 수 괴리 | 조인 순서 DP(System R), 히스토그램 | L15 · Selinger 외 1979 | 필수 | 신규 (연결: `languages/sql/syntax/58·59·60`) |

### 9.5 트랜잭션·동시성 제어

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 20-transactions-acid | 원자성·일관성·격리·지속성의 정확한 뜻, 직렬화 가능성 | 04, os/15-race-conditions | 트랜잭션 경계 밖 외부 호출 → 롤백돼도 메일은 발송; autocommit 가정 | 충돌 그래프 | L16 · DDIA 7장 | 필수 | 신규 (연결: `languages/sql/syntax/55`) |
| 21-isolation-levels-and-anomalies | RU/RC/RR/SI/Serializable, dirty·non-repeatable·phantom·**lost update·write skew** | 20 | SI에서 write skew → 당직 0명·잔액 음수; RC에서 lost update | 이상 현상 분류 | Berenson 외 1995 · DDIA 7장 | 필수 | 신규 (연결: `languages/sql/syntax/56`) |
| 22-two-phase-locking-and-deadlock | 2PL·엄격 2PL·락 모드·DB 데드락 탐지 | 21, os/19-deadlock | `Lock wait timeout exceeded`(MySQL 1205); `deadlock detected`(PG 40P01 / MySQL 1213) | 락 테이블 해시, **wait-for 그래프** | L17 | 필수 | 신규 (연결: `languages/sql/syntax/57`) |
| 23-mvcc | 버전 체인·스냅샷·가시성·가비지 수집(vacuum) | 21 | 장기 트랜잭션 → vacuum 불가 → 테이블 bloat; PG XID wraparound 임박 → 쓰기 중단 | 버전 체인(연결 리스트), 스냅샷 | L19 · PostgreSQL 문서 "Routine Vacuuming" | 필수 | 신규 |
| 24-occ-and-timestamp-ordering | 낙관적 동시성·타임스탬프 순서·버전 컬럼 | 21 | 경합 높은 행에 OCC → `OptimisticLockException` 재시도 폭증 | 버전 번호 비교 | L18 · Kung–Robinson 1981 | 권장 | 신규 |
| 25-app-level-concurrency-patterns | `SELECT … FOR UPDATE`·조건부 UPDATE·원자적 upsert·유니크 제약 활용 | 22, 24 | check-then-insert → 중복 행; 재고 음수; 트랜잭션 안 원격 호출 → 락 장기 보유 | — | DDIA 7장 · PostgreSQL 문서 "Explicit Locking" | 필수 | 신규 (연결: `api-design/03-stock-deduct`, `reliability/04-failure-modes-catalog` F-01~08) |

### 9.6 로깅·복구·백업

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 26-wal-and-logging | WAL 규칙·group commit·no-force/steal | 23, os/25-fsync-and-durability | `fsync=off`·쓰기 캐시 → 크래시 후 커밋된 데이터 유실; WAL 디스크 풀 → DB 정지 | **append-only 로그**, LSN | L20 | 필수 | 신규 |
| 27-recovery-aries-checkpoints | ARIES(분석·재실행·취소)·체크포인트 | 26 | 체크포인트 간격 과대 → 재시작 복구 수십 분 | LSN 체인 | L21 · Mohan 외 1992 | 권장 | 신규 |
| 28-backup-and-pitr | 논리/물리 백업·PITR·복원 검증 | 26 | **복원 테스트 안 한 백업** → 사고 때 전부 무용(GitLab 2017); 백업 중 락 | WAL 아카이브 | PostgreSQL 문서 "Backup and Restore" | 필수 | 신규 |

### 9.7 복제·분할

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 29-replication-leader-follower | 동기/비동기 복제·복제 지연·읽기 보장 | 26 | 복제 지연 → **방금 쓴 글이 안 보임**(read-your-writes 위반); 비동기 페일오버 → 확인된 쓰기 유실 | 복제 로그(WAL 스트림) | DDIA 5장 | 필수 | `systems/server-design/03-data-layer.md` (분할 — 복제·복제 지연 절) |
| 30-partitioning-and-sharding | 키 범위·해시 분할·보조 인덱스·재조정 | 29 | 핫 파티션; 크로스 샤드 쿼리 폭증; 리샤딩 중 이중 쓰기 불일치 | 해시, **일관 해싱** | DDIA 6장 | 필수 | `systems/partitioning-vs-sharding` · `systems/server-design/03-data-layer.md` (분할 — 샤딩·리샤딩 절) |
| 31-distributed-databases | 분산 OLTP·OLAP 개관, NewSQL | 30, distributed/19-two-phase-commit | — (분산 트랜잭션 지연, 시계 의존) | — | L22 · L23 · L24 | 심화 | 신규 |

### 9.8 애플리케이션과 DB

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 32-connection-pooling | 풀 크기·대기·검증·max_connections | 20, math/15-queueing-and-littles-law | `Connection is not available, request timed out after 30000ms`(풀 고갈); `FATAL: sorry, too many clients already`; 풀 크기 과대 → DB 컨텍스트 스위칭 | 풀 = 블로킹 큐 | HikariCP wiki "About Pool Sizing" | 필수 | 신규 |
| 33-orm-and-n-plus-one | ORM 매핑·영속성 컨텍스트·지연 로딩·N+1 | 32 | N+1 쿼리 폭증; `LazyInitializationException`; 더티 체킹으로 의도치 않은 UPDATE | 1차 캐시(식별자 맵) | Fowler 『PoEAA』 Identity Map·Unit of Work | 필수 | `engineering/data-access` (README·jpa·spring-data-jdbc·comparison 병합) |
| 34-schema-migration | 무중단 마이그레이션·expand/contract·백필 | 12, 23 | `ALTER TABLE` 테이블 락 → 서비스 정지; 롤백 불가 마이그레이션; 백필이 복제 지연 유발 | — | `systems/server-design` 08 · Sadalage–Ambler 『Refactoring Databases』 [?] | 필수 | `systems/server-design/08-deployment-ops.md` (분할 — DB 마이그레이션 절) |
| 35-row-level-security | 행 수준 보안·테넌트 격리 | 02, security/15-access-control-models | 정책 누락 테이블로 테넌트 간 누출; 소유자 역할은 RLS 우회 | 정책 술어 | PostgreSQL 문서 "Row Security Policies" | 권장 | `systems/postgres-rls` |
| 36-timeseries-resolution-tiers | 시계열 해상도 계층·다운샘플·보존 | 08 | 롤업 경계 버그 → 집계 이중 계산; 보존 정책 누락 → 디스크 풀 | 링 버퍼·롤업 | 기존 노트 원고 | 권장 | `systems/timeseries-resolution-tiers` · `ops-patterns/17-timeseries` (병합 검토) |
| 37-clickhouse-mergetree | 컬럼 저장 + 병합 트리 엔진 | 08, 10 | 작은 INSERT 폭주 → `Too many parts` | 정렬 파트 병합(LSM 계열) | ClickHouse 문서 MergeTree | 심화 | `systems/clickhouse-mergetree` |
| 38-caching-with-databases | cache-aside·write-through·무효화·일관성 | 29, data-structure/10-lru-cache | 무효화 경합 → 오래된 값 고착; 캐시 스탬피드·관통·눈사태 | LRU, TTL, 블룸(관통 방어) | `systems/server-design` 04 · Nishtala 외 NSDI 2013 | 필수 | `systems/server-design/04-caching.md` (연결: `reliability/13-cache-stampede`) |

### 9.9 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 39-db-symptom-index | 역색인: 1205/1213/40P01/40001, 풀 고갈 메시지, `too many clients`, bloat, 복제 지연, `Too many parts`, 플랜 급변, 스필 | 전체 | — | — | 이 영역 leaf · PostgreSQL 부록 A(SQLSTATE) | 필수 | 신규 |
| 40-db-incidents | 실사건: GitLab DB 삭제 + 백업 5종 실패(2017-01-31) · Sentry PostgreSQL XID wraparound(2015) · GitHub MySQL 페일오버 불일치(2018-10-21 — 분산 관점은 distributed/32) | 39 | — | — | GitLab 포스트모템 2017-02-10 · Sentry 블로그 2015-07 · GitHub 블로그 2018-10-30 | 권장 | 신규 |

---

# Part 4 — 여러 대

## 10. 분산 시스템 (`distributed/`)

> 모델(무엇이 실패하나) → 시간 → 복제·일관성 → 합의·조정 → 분산 트랜잭션·데이터 흐름. 기존 ops-patterns의 분산 패턴(논리 시계·CRDT·리더 선출·분산 락·Snowflake·outbox·saga·event sourcing)이 **이론 단원 안으로** 들어온다.
> 뼈대: DDIA 1판 5·8·9·10·11장(확인), MIT 6.5840 Spring 2026 강의(이하 6.5840 L#, 확인), 원논문.

**권장 학습 순서**: 01 → 02 → 03 → 05 → 06 → 08 → 10 → 11 → 09 → 14 → 16 → 17 → 18 → 19 → 20 → 21 → 24 → 26 → 25 → 27 → 23 → 12 → (04 · 07 · 13 · 15 · 22 · 28 · 29 · 30 권장·심화) → 31 → 32

### 10.1 모델

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-why-distributed-and-fallacies | 분산의 이유와 8가지 오류(네트워크는 믿을 만하다 등) | network/42-what-happens-when-url | 네트워크 무결 가정 코드 → 부분 실패 시 무한 대기·데이터 불일치 | — | Deutsch "Fallacies of Distributed Computing" · 6.5840 L1 | 필수 | 신규 |
| 02-system-and-failure-models | 동기/부분동기/비동기, crash-stop·crash-recovery·비잔틴 | 01 | **느림과 죽음을 구분 못 함** → 살아 있는 노드를 죽었다고 판단해 이중 처리 | 장애 탐지기(φ accrual) | DDIA 8장 | 필수 | 신규 |
| 03-partial-failure-and-timeouts | 부분 실패·모호한 결과·타임아웃 선택 | 02 | 타임아웃 났는데 실제론 성공 → 재시도로 **중복 결제**; 너무 짧은 타임아웃 → 오탐 페일오버 | — | DDIA 8장 | 필수 | `ops-patterns/failure-at-scale` (분할 — 양상 1 부분 실패 절) |
| 04-impossibility-results | 두 장군 문제·FLP 불가능성 | 02 | "정확히 한 번 전달" 보장 주장의 허구 → 설계 오해 | — | Fischer–Lynch–Paterson 1985 · Gray 1978 [?] | 권장 | 신규 |

### 10.2 시간

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 05-physical-clocks-and-ntp | 벽시계·단조 시계·NTP·clock skew·윤초 | 02 | 벽시계로 경과 시간 계산 → **음수 duration** panic(Cloudflare 2017 윤초); 시계 어긋남 → JWT `nbf`/인증서 거절, LWW 역전 | NTP 필터 알고리즘 | RFC 5905 · DDIA 8장 | 필수 | 신규 |
| 06-logical-clocks | 램포트 시계·벡터 시계·happens-before | 05 | 벽시계 타임스탬프로 이벤트 순서 결정 → 인과 역전 | 램포트 카운터, 벡터 | Lamport 1978 | 필수 | `ops-patterns/14-logical-clock` |
| 07-hybrid-clocks-and-truetime | HLC·TrueTime·commit wait | 06 | 시계 불확실성 상한 초과 → 외부 일관성 위반 | 구간 시간 | Corbett 외 OSDI 2012 · 6.5840 L12 · Kulkarni 외 2014 | 심화 | 신규 |

### 10.3 복제·일관성

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 08-replication-strategies | 단일 리더·다중 리더·리더리스 | database/29-replication-leader-follower | 다중 리더 쓰기 충돌 → 조용한 덮어쓰기; 리더리스 읽기 복구 누락 → 오래된 값 | 복제 로그 | DDIA 5장 | 필수 | 신규 |
| 09-quorums | R+W>N·sloppy quorum·hinted handoff·anti-entropy | 08 | sloppy quorum에서 R+W>N이어도 오래된 읽기; 정족수 미달 → 쓰기 거부 | **Merkle 트리 anti-entropy**, 일관 해싱 | DeCandia 외 SOSP 2007 · DDIA 5장 | 권장 | 신규 |
| 10-consistency-models | 선형화·순차·인과·최종 일관성, 세션 보장 | 08 | 최종 일관성 저장소에서 "쓰고 바로 읽기" → 옛 값; 선형화 가정한 분산 카운터 → 과발급 | — | Herlihy–Wing 1990 · 6.5840 L8 · DDIA 9장 | 필수 | 신규 |
| 11-cap-and-pacelc | 분할 시 C vs A, 평시 L vs C | 10 | "CA 시스템" 주장 → 분할 시 동작 미정의 | — | Gilbert–Lynch 2002 · Abadi 2012 | 필수 | 신규 |
| 12-conflict-resolution-and-crdt | LWW·버전 벡터·CRDT | 06, 08 | LWW → 동시 쓰기 조용한 유실; 시계 어긋남 → 최신 쓰기가 짐 | G-Counter·OR-Set(반격자) | Shapiro 외 2011 | 권장 | `ops-patterns/15-crdt` |
| 13-chain-replication-and-striping | 체인 복제·앙상블/쓰기 정족수·스트라이핑 | 09 | 체인 중간 노드 느림 → 전체 쓰기 지연; 스트라이프 배치 편중 | 체인, 라운드로빈 배치 | van Renesse–Schneider OSDI 2004 · 6.5840 L13 · BookKeeper 문서 | 심화 | `systems/striping` |

### 10.4 합의·조정

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 14-leader-election | 리더 선출·리스·임기 | 02, 05 | 네트워크 분할 → **리더 둘**(split-brain); 리스 시계 의존 | 임기 번호(에포크) | DDIA 9장 | 필수 | `ops-patterns/12-leader-election` |
| 15-consensus-paxos | Paxos 기본형 | 14 | — (이해 난도 — Raft로 대체 학습) | 제안 번호·정족수 교집합 | Lamport 2001 "Paxos Made Simple" · 6.5840 L4 | 권장 | 신규 |
| 16-consensus-raft | 리더 선출·로그 복제·안전성·멤버십 변경 | 14 | 과반 없는 쪽 쓰기 거부(가용성 저하); 선거 타임아웃 튜닝 실패 → 선거 폭풍 | **복제 로그**, 무작위 타임아웃 | Ongaro–Ousterhout 2014 · 6.5840 L6–L7 | 필수 | 신규 |
| 17-coordination-and-fencing | ZooKeeper·etcd·분산 락·**fencing token** | 16 | GC 멈춤 중 락 만료 → **두 소유자 동시 쓰기**; Redlock 시계 가정 | 단조 증가 토큰 | Hunt 외 USENIX ATC 2010 · 6.5840 L9 · Kleppmann 2016 "How to do distributed locking" | 필수 | `ops-patterns/11-distributed-lock` |
| 18-distributed-id-generation | Snowflake·UUIDv7·시퀀스 블록 | 05 | 시계 역행 → ID 중복·역순; worker ID 중복 할당 | 비트 필드 조합 | Twitter Snowflake(2010) · RFC 9562 | 권장 | `ops-patterns/13-snowflake` |

### 10.5 분산 트랜잭션·데이터 흐름

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 19-two-phase-commit | 2PC·코디네이터·in-doubt | database/20-transactions-acid, 03 | 코디네이터 장애 → 참가자 **블로킹**(락 보유 채 대기); XA 트랜잭션 방치 | 상태 기계 | 6.5840 L11 · DDIA 9장 | 필수 | 신규 |
| 20-saga | 보상 트랜잭션·순방향/역방향 복구 | 19 | 보상 실패 → 반쯤 된 주문; 보상 불가 작업(메일 발송) 설계 누락 | 상태 기계 | Garcia-Molina–Salem 1987 | 필수 | `ops-patterns/08-saga` |
| 21-outbox-and-dual-write | 이중 쓰기 문제·transactional outbox·CDC | 20 | DB 커밋 후 메시지 발행 전 크래시 → 이벤트 유실; 순서 역전 | 로그 테이블 폴링·CDC | Richardson microservices.io "Transactional outbox" | 필수 | `ops-patterns/07-outbox` |
| 22-outbox-vs-dispatch-log | outbox와 dispatch log의 경계 | 21 | 역할 혼동 → 재발행 폭주 또는 누락 | — | 기존 노트 원고 | 심화 | `systems/outbox-vs-dispatch-log` |
| 23-orchestration-vs-choreography | 중앙 조정 vs 이벤트 연쇄 | 20 | 코레오그래피 흐름 추적 불가 → 멈춘 사가 방치; 오케스트레이터 단일 장애점 | 워크플로 상태 기계 | 기존 노트 원고 | 권장 | `systems/orchestration-choreography` |
| 24-queues-logs-and-delivery-semantics | 큐 vs 로그, at-most/at-least/effectively-once, 순서 | 21 | at-least-once → **중복 소비**(멱등성 필요); 파티션 간 순서 역전 | append-only 로그, 오프셋 | DDIA 11장 · `systems/server-design` 07 | 필수 | `systems/server-design/07-async-messaging.md` |
| 25-kafka-internals | 파티션·세그먼트·페이지 캐시·zero-copy·ISR | 24, os/30-zero-copy-and-io-uring | ISR 축소 + `acks=1` → 확인된 메시지 유실; 세그먼트 보존 설정 실수 | 세그먼트 로그 + 오프셋 인덱스(희소 인덱스·이진 탐색) | Kreps 외 NetDB 2011 · Kafka 문서 | 권장 | `systems/kafka-why-fast` |
| 26-consumer-failure-handling | 오프셋 커밋 순서·재시도·DLQ·poison pill·리밸런스 | 24 | 처리 전 커밋 → 유실 / 처리 후 커밋 실패 → 중복; poison 메시지로 파티션 정지; 리밸런스 폭풍 | 재시도 큐 | Kafka 문서 Consumer | 필수 | `systems/kafka-consumer-failure` |
| 27-event-sourcing | 이벤트를 원천으로, 스냅샷·재생·버전 | 24 | 이벤트 스키마 변경 → 재생 실패; 스냅샷 없음 → 재생 시간 폭증 | append-only 로그, 폴드 | Fowler "Event Sourcing" · DDIA 11장 | 권장 | `systems/event-sourcing` · `ops-patterns/16-event-sourcing` (병합 검토) |
| 28-batch-and-stream-processing | MapReduce·스트림·윈도·워터마크 | 24 | 늦게 온 이벤트 → 윈도 집계 누락; 스큐된 키 → 한 태스크만 느림 | 셔플 = 해시 분할 + 외부 정렬 | DDIA 10·11장 · Dean–Ghemawat 2004 · 6.5840 L1 | 권장 | 신규 |
| 29-byzantine-and-blockchain | 비잔틴 장애·PBFT·블록체인 | 16 | — (신뢰 모델 오판) | 해시 체인, Merkle 트리 | Castro–Liskov OSDI 1999 · Nakamoto 2008 · 6.5840 L20–L21 | 심화 | `ops-patterns/18-blockchain` |
| 30-distributed-cache-consistency | 대규모 캐시 일관성·lease·무효화 | database/38-caching-with-databases | 늦은 set이 삭제를 덮어써 **오래된 값 고착**; 무효화 폭풍 | lease 토큰 | Nishtala 외 NSDI 2013 · 6.5840 L16 | 심화 | 신규 |

### 10.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 31-distributed-symptom-index | 역색인: 중복 처리·유실·순서 역전·리더 둘·오래된 읽기·블로킹된 트랜잭션·음수 시간 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 32-distributed-incidents | 실사건: GitHub 43초 분할 → 24시간 복구(2018-10-21) · Cloudflare 윤초 RRDNS(2017-01-01) · AWS EBS 재미러링 폭풍(2011-04) · metastable failure | 31 | — | — | GitHub 블로그 2018-10-30 · Cloudflare 블로그 2017-01-01 · AWS 요약 2011 · Bronson 외 HotOS 2021 | 권장 | 신규 |

---

## 11. 운영·신뢰성 (`reliability/`)

> "여러 대가 돌 때 어떻게 버티고, 어떻게 보고, 어떻게 바꾸나". 기존 ops-patterns(복원력 패턴)·server-design(컬렉션)·failure 노트가 주력이다. 신규는 **성능 측정·관측성·사고 대응**.
> 뼈대: Google 『Site Reliability Engineering』(이하 SRE — 장 번호 3·4·6·21·22 외 `[?]`), Nygard 『Release It!』 [?], Gregg 『Systems Performance』 [?], Dean–Barroso 2013.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 06 → 07 → 08 → 10 → 11 → 12 → 14 → 23 → 24 → 25 → 18 → 20 → 21 → 27 → 28 → 29 → 05 → 09 → 13 → 15 → 16 → 17 → 19 → 22 → 26 → 30 → 31 → 32 → 33 → 34

### 11.1 신뢰성 개념

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-fault-error-failure-availability | fault/error/failure 구분, 가용성(9의 개수), MTBF/MTTR, 직렬·병렬 합성 | distributed/02-system-and-failure-models | 99.9% 서비스 5개 직렬 → 전체 99.5%를 모르고 SLA 약속 | 신뢰도 블록 다이어그램 | Avižienis 외 2004 · SRE 3장 | 필수 | `systems/server-design/05-ha-topology.md` (분할 — 가용성 합성 절) |
| 02-slo-sli-error-budget | SLI 선택·SLO·에러 버짓·번 레이트 | 01 | 평균 지연 SLI → 꼬리 사용자 불만 미포착; SLO 없음 → 안정성 vs 속도 논쟁 무한 | 슬라이딩 윈도 집계 | SRE 4장 · SRE Workbook 2·5장 [?] | 필수 | `systems/server-design/09-capacity-slo.md` (분할 — SLO/에러 버짓 절) |
| 03-failure-at-scale | 부분 실패 상시화·재시도 증폭·균등 가정 붕괴·상태의 확장 불가 | 01 | 재시도가 부하를 N배로 → 복구 불가 | — | 기존 노트 원고 · SRE 22장 | 필수 | `ops-patterns/failure-at-scale` |
| 04-failure-modes-catalog | 실패 카탈로그 F-01~25(동시성·DB / 분산·비동기 / 결제) | 03 | (카탈로그 자체가 ⚠ 모음) | — | 기존 노트 원고 | 필수 | `ops-patterns/failure-modes` |
| 05-failure-point-checklist | 설계 시 실패 지점 점검 절차 | 04 | 점검 없이 출시 → 알려진 실패 모드 재발 | — | 기존 노트 원고 | 권장 | `engineering/failure-point-checklist` |

### 11.2 복원력 패턴

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 06-timeouts-and-deadline-propagation | 타임아웃 계층 정렬·데드라인 전파 | distributed/03-partial-failure-and-timeouts | 하류 타임아웃 > 상류 → 이미 포기한 요청을 계속 처리(헛일); 타임아웃 없음 → 스레드 고갈 | 남은 예산 전파 | gRPC deadline 문서 · SRE 22장 | 필수 | `ops-patterns/deadline-propagation` · `systems/server-design/06-resilience.md` (분할 — 타임아웃 절) |
| 07-retry-backoff-jitter | 지수 백오프·지터·재시도 예산 | 06, math/11-randomness-and-prng | 지터 없는 재시도 → 동기화된 재시도 폭풍; 계층마다 재시도 → 곱셈 증폭 | 지수 백오프, 토큰 버킷(재시도 예산) | AWS Architecture Blog "Exponential Backoff and Jitter" 2015 | 필수 | `ops-patterns/01-retry-backoff` |
| 08-circuit-breaker | 닫힘·열림·반열림 | 07 | 임계값 과민 → 정상 서비스 차단 flapping; 폴백 없음 → 즉시 에러 전파 | 상태 기계, 슬라이딩 윈도 실패율 | Nygard 『Release It!』 5장 [?] | 필수 | `ops-patterns/02-circuit-breaker` |
| 09-bulkhead | 자원 격벽(스레드풀·커넥션 분리) | 08 | 공유 풀 하나 → 느린 의존성 하나가 전체 스레드 점유 | 세마포어(os/18) | Nygard 『Release It!』 [?] | 권장 | `ops-patterns/03-bulkhead` |
| 10-rate-limiter | 토큰 버킷·리키 버킷·고정/슬라이딩 윈도·분산 제한 | 07, algorithm/09-sliding-window | 고정 윈도 경계에서 2배 버스트; 분산 카운터 경합 → 초과 허용 | **토큰 버킷**, 슬라이딩 로그/카운터 | RFC 6585 (429) · Stripe 블로그 2017 [?] | 필수 | `ops-patterns/04-rate-limiter` |
| 11-backpressure-and-load-shedding | 역압·큐 한도·우선순위 셰딩 | 10, math/15-queueing-and-littles-law | 무한 큐 → 지연 폭증 후 OOM; 셰딩 없음 → 과부하 시 처리량 0으로 붕괴 | 유계 큐, CoDel | SRE 21장 | 필수 | `ops-patterns/05-backpressure` · `systems/server-design/06-resilience.md` (분할 — 백프레셔·로드 셰딩 절) |
| 12-idempotency | 멱등 키 저장소·중복 억제·결과 재생 | 07 | 재시도 → 중복 결제·이중 적립; 멱등 키 저장과 처리의 비원자성 | 키-결과 맵(TTL) | Stripe "Idempotent requests" | 필수 | `ops-patterns/06-idempotency-store` |
| 13-cache-stampede | 스탬피드·관통·눈사태 방어 | database/38-caching-with-databases | 인기 키 만료 순간 DB로 동시 수천 요청 → DB 다운 | 단일 비행(single-flight), 확률적 조기 만료, 블룸 | Vattani 외 VLDB 2015 | 권장 | `ops-patterns/09-stampede` |
| 14-graceful-shutdown | SIGTERM → 준비 해제 → 드레이닝 → 종료 | os/06-signals, network/39-load-balancers-and-proxies | 배포 때마다 502 순간 증가(LB 해제 전 종료); 진행 중 작업 유실 | 진행 중 요청 카운터 | k8s Pod lifecycle 문서 | 필수 | `ops-patterns/19-graceful-shutdown` · `systems/server-design/02-request-path.md` (분할 — graceful shutdown 절) |
| 15-scheduler-and-cron-ha | 스케줄러 이중화·중복 실행 방지·미실행 보정 | distributed/17-coordination-and-fencing | 두 인스턴스가 같은 배치 실행 → 이중 정산; 장애 중 놓친 실행 | 타이머 휠·리스 | 기존 노트 원고 | 권장 | `ops-patterns/10-scheduler` |
| 16-hysteresis-and-flapping | 방향별 임계값 분리로 진동 방지 | 08 | 오토스케일·알람·서킷 임계값 flapping | hysteresis band | 기존 노트 원고 | 권장 | `systems/Hysteresis` |
| 17-tail-latency-and-stragglers | 팬아웃에서 꼬리 지연 증폭, hedged request | math/09-expectation-variance-tails | 100개 팬아웃 → p99가 사실상 중앙값 경험; hedging 과다 → 부하 2배 | 백분위 추정 | Dean–Barroso CACM 2013 | 권장 | `systems/straggler` |

### 11.3 성능·용량

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 18-performance-measurement | 지연 분포·백분위·벤치마크 방법론·coordinated omission | data-analysis/06-percentiles-and-latency-distributions | 평균만 보고 판단; 부하 생성기가 느린 응답 동안 요청을 안 보냄 → p99 과소 측정 [?] | HdrHistogram, t-digest | Gregg 『Systems Performance』 2판 12장 [?] · Tene "How NOT to Measure Latency" [?] | 필수 | 신규 |
| 19-profiling | CPU·메모리·락·off-CPU 프로파일링, 플레임 그래프 | 18, os/35-os-observability-tools | 추측 최적화 → 병목 아닌 곳 수정; 세이프포인트 편향 프로파일러 | 스택 샘플 집계(트라이) | Gregg "Flame Graphs" CACM 2016 | 권장 | 신규 |
| 20-scaling-principles | 병목 이동·Little's Law·USL·무상태화 | math/15-queueing-and-littles-law | 인스턴스 늘렸는데 처리량 역전(USL 역행 — 경합·일관성 비용) | USL 곡선 | Gunther USL · `systems/server-design` 01 | 필수 | `systems/server-design/01-scaling-principles.md` |
| 21-capacity-and-load-testing | 사이징·부하 테스트 설계·헤드룸 | 20, 18 | 부하 테스트 데이터가 캐시에 다 들어가 운영보다 낙관적; 헤드룸 없이 피크 진입 | — | SRE 18장 [?] · `systems/server-design` 09 | 필수 | `systems/server-design/09-capacity-slo.md` (분할 — 사이징·부하 테스트·오토스케일링 절) |
| 22-autoscaling | 지표 기반 확장·반응 지연·쿨다운 | 21, 16 | 스케일 반응(수 분) < 트래픽 급증(수 초) → 확장 전 붕괴; 쿨다운 없음 → flapping | 제어 루프, 이동 평균 | k8s HPA 문서 | 권장 | 신규 |

### 11.4 관측성

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 23-logging | 구조화 로그·상관 ID·레벨·샘플링 | 01 | 로그 폭증 → 디스크 풀·비용; 상관 ID 없음 → 요청 추적 불가; 동기 로깅이 지연 유발 | 링 버퍼 비동기 appender | OpenTelemetry Logs 명세 · 12-factor XI | 필수 | 신규 |
| 24-metrics-and-golden-signals | 4 골든 시그널·RED·USE, 카운터/게이지/히스토그램 | 23 | 레이블 카디널리티 폭발(user_id 레이블) → TSDB OOM; 평균 지표로 꼬리 은폐; 히스토그램 버킷 부적절 | 히스토그램 버킷, 시계열 압축(Gorilla) | SRE 6장 · Gregg USE · Pelkonen 외 VLDB 2015 | 필수 | `systems/server-design/08-deployment-ops.md` (분할 — 골든 시그널 절) |
| 25-distributed-tracing | 트레이스·스팬·컨텍스트 전파·샘플링 | 24 | 비동기 경계(큐·스레드풀)에서 컨텍스트 끊김 → 트레이스 조각남; head 샘플링으로 에러 트레이스 누락 | 스팬 트리 | W3C Trace Context · Sigelman 외 2010 (Dapper) | 필수 | 신규 |
| 26-alerting-and-on-call | 증상 기반 알람·번 레이트 알람·온콜 | 02, 24 | 원인 기반 알람 남발 → 알람 피로로 진짜 장애 놓침 | 다중 윈도 번 레이트 | SRE 6장 · SRE Workbook 5장 [?] | 권장 | 신규 |

### 11.5 배포·변경·사고 대응

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-deployment-strategies | 롤링·블루그린·카나리·피처 플래그·롤백 | 14 | 신·구 버전 동시 실행 비호환(스키마·메시지) → 배포 중에만 에러; 롤백 불가 변경 | 점진 비율 제어 | `systems/server-design` 08 · SRE 8장 [?] | 필수 | `systems/server-design/08-deployment-ops.md` (분할 — 무중단 배포·롤백 절) |
| 28-high-availability-topology | 이중화 모델·페일오버·split-brain·다중 AZ/리전 | 01, distributed/14-leader-election | 페일오버 자동화가 오탐으로 멀쩡한 주 노드 강등; 같은 AZ 이중화 → 동시 장애 | 헬스 판정 상태 기계 | `systems/server-design` 05 | 필수 | `systems/server-design/05-ha-topology.md` (분할 — 이중화·failover·다중 AZ 절) |
| 29-incident-response-and-postmortem | 사고 지휘·완화 우선·비난 없는 포스트모템 | 26 | 원인 규명부터 하다 완화 지연; 개인 비난 → 은폐 문화 | 타임라인 | SRE 14·15장 [?] | 필수 | 신규 |
| 30-chaos-and-resilience-testing | 장애 주입·게임 데이 | 29 | 가정한 페일오버가 실제로는 안 됨을 사고 때 발견 | — | Basiri 외 IEEE Software 2016 (Chaos Engineering) | 권장 | 신규 |
| 31-disaster-recovery | RPO/RTO·백업 리전·복구 훈련 | 28, database/28-backup-and-pitr | DR 훈련 안 함 → 실제 전환 시 설정 누락; RPO 약속과 복제 방식 불일치 | — | AWS "Disaster Recovery of Workloads" 백서 [?] | 권장 | 신규 |
| 32-server-design-antipatterns | 흔한 안티패턴 카탈로그 | 27 | (카탈로그 자체가 ⚠ 모음) | — | 기존 노트 원고 | 권장 | `systems/server-design/11-antipatterns.md` |

### 11.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 33-reliability-symptom-index | **증상 → 진단 → 처방 플레이북**(지연 급증·에러율 급증·연쇄 장애·배포 직후 502·메모리 우상향 등) | 전체 | — | — | 기존 노트 원고 | 필수 | `systems/server-design/10-playbook-by-symptom.md` |
| 34-reliability-incidents | 실사건: AWS S3 us-east-1 오타 명령(2017-02-28) · Slack 연휴 후 복귀 트래픽(2021-01-04) · Roblox Consul 73시간(2021-10) · CrowdStrike 채널 파일(2024-07-19) | 33 | — | — | AWS 요약 2017 · Slack Engineering 2021 · Roblox 블로그 2022-01 · CrowdStrike PIR 2024 | 권장 | 신규 |

# Part 5 — 만드는 법

## 12. 소프트웨어 설계 (`software-design/`)

> 복잡도 → 모듈 → 코드 수준 → OOP → 패턴 → 아키텍처 → 품질 속성. 소프트웨어 설계에서 "깨지면"은 크래시가 아니라 **변경 비용 폭증·조용한 결합**으로 보인다 — ⚠ 칸은 스멜과 변경 시 증상으로 적는다.
> 뼈대: Ousterhout 『A Philosophy of Software Design』 2판(이하 APOSD), Fowler 『Refactoring』 2판, Martin 『Clean Architecture』, GoF, Parnas 1972, ISO/IEC 25010:2023, SWEBOK v4 Design·Architecture KA.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 20 → 21 → 22 → 19 → 23 → 24

### 12.1 복잡도와 모듈

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-complexity | 복잡도의 3증상(변경 증폭·인지 부하·unknown unknowns)과 2원인(의존·모호) | — | 한 줄 요구 변경에 파일 20개 수정(변경 증폭); 수정 후 엉뚱한 곳 장애(unknown unknowns) | 의존 그래프 | APOSD 2장 | 필수 | 신규 |
| 02-modularity-coupling-cohesion | 정보 은닉·결합도·응집도 | 01 | 내부 표현 변경이 호출자 전부를 깨뜨림(정보 누출) | 의존 그래프 분석 | Parnas 1972 · APOSD 5장 | 필수 | 신규 |
| 03-deep-modules-and-abstraction | 깊은 모듈·좋은 인터페이스·추상화 계층 | 02 | 얕은 래퍼 남발 → 호출 경로만 길어지고 복잡도 그대로; 통과 메서드 | — | APOSD 4·7장 | 권장 | 신규 |

### 12.2 코드 수준

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-clean-code | 이름·함수·주석·포매팅 | 01 | 의미 없는 이름 → 리뷰에서 버그 통과; 긴 함수 → 부분 수정 시 부작용 | — | Martin 『Clean Code』 | 필수 | `engineering/clean-code` |
| 05-code-smells | 스멜 카탈로그(Shotgun Surgery·Divergent Change·Speculative Generality·Feature Envy 등) | 04 | 스멜 방치 → 변경마다 회귀 버그 | — | Fowler 『Refactoring』 2판 3장 | 필수 | 신규 |
| 06-refactoring | 동작 보존 변환·작은 단계·테스트 안전망 | 05, testing/02-good-unit-tests | 테스트 없이 리팩터링 → 조용한 동작 변경; 큰 한 방 리팩터링 → 머지 지옥 | — | Fowler 『Refactoring』 2판 1·2·4장 | 필수 | 신규 |
| 07-error-handling-design | fail-fast·예외 경계·에러 정의로 없애기 | language/09-error-handling-models | 모든 곳에서 catch-log-rethrow → 로그 중복·원인 은폐; 삼킨 예외 → 조용한 실패 | — | APOSD 10장 | 필수 | 신규 |
| 08-immutability-and-value-objects | 불변 객체·값 의미론 | 07, language/07-values-references-passing | 공유 가변 객체 → 한 곳 수정이 다른 요청에 누출; 해시 키 변이 | 영속 자료구조 | Bloch 『Effective Java』 3판 Item 17 | 권장 | 신규 (연결: `languages/java/syntax/59-immutable-objects`) |

### 12.3 객체지향

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 09-oop-fundamentals | 캡슐화·상속·다형성·추상 클래스, IS-A/HAS-A | 02 | getter/setter 전부 공개 → 캡슐화 붕괴로 불변식 외부에서 깨짐 | vtable(language/11) | GoF 1장 · Meyer 『OOSC』 [?] | 필수 | `foundations/oop-basics` |
| 10-composition-over-inheritance | 상속의 비용·취약한 기반 클래스·위임 | 09 | 부모 변경이 자식 전부 파손(fragile base class); `HashSet` 상속 카운터 이중 집계 | — | Bloch 『Effective Java』 3판 Item 18 · GoF 1장 | 권장 | 신규 |
| 11-solid | SRP·OCP·LSP·ISP·DIP | 09 | LSP 위반 → 하위 타입에서 `UnsupportedOperationException`; DIP 부재 → 테스트 불가 | — | Martin 『Clean Architecture』 3부 | 필수 | `engineering/solid-principles` |
| 12-design-by-contract | 사전조건·사후조건·클래스 불변식 | 11 | 계약 미명시 → 호출자·피호출자가 서로 검증 미룸 → 무효 상태 진입 | 불변식 검사 | Meyer 1992 "Applying Design by Contract" | 권장 | 신규 |

### 12.4 패턴

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 13-design-patterns-gof | 생성·구조·행위 패턴 23 | 11 | 패턴을 위한 패턴 → 간접 계층만 늘어남 | 합성(Composite=트리), 옵서버 목록, 상태 기계(State) | GoF | 필수 | `engineering/design-patterns-gof` |
| 14-antipatterns | God Object·싱글턴 남용·Big Ball of Mud·과설계 | 13 | 전역 싱글턴 → 테스트 간 상태 누출·동시성 버그 | — | Foote–Yoder 1997 "Big Ball of Mud" | 권장 | 신규 |

### 12.5 아키텍처

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 15-architecture-styles | 계층·이벤트 기반·마이크로커널·공간 기반·서비스 기반 등 | 13 | 스타일-요구 불일치 → 품질 속성 미달 | — | Richards–Ford 『Fundamentals of Software Architecture』 [?] | 필수 | `systems/architecture-styles` |
| 16-layered-hexagonal-clean | 의존 방향 규칙·포트와 어댑터·클린 아키텍처 | 15, 11 | 도메인이 프레임워크·DB에 의존 → 교체·테스트 불가; 계층 건너뛰기 누적 | 의존 그래프 방향(DAG) | Cockburn 2005 "Hexagonal Architecture" · Martin 『Clean Architecture』 5부 | 필수 | 신규 |
| 17-component-principles | REP·CCP·CRP·ADP·SDP·SAP | 16 | 컴포넌트 순환 의존 → 독립 배포 불가 | **순환 탐지(SCC)** | Martin 『Clean Architecture』 4부 | 권장 | 신규 (연결: `algorithm/18-scc`) |
| 18-monolith-vs-microservices | 모듈러 모놀리스·서비스 분해·분산 모놀리스 | 17, distributed/01-why-distributed-and-fallacies | **분산 모놀리스** — 서비스 나눴는데 동시 배포 필요·공유 DB; 동기 호출 체인 → 가용성 곱셈 저하 | — | Newman 『Building Microservices』 2판 [?] | 필수 | 신규 |
| 19-multi-tenancy | 테넌트 격리 모델(사일로·풀·브리지)·noisy neighbor | 18 | 테넌트 ID 필터 누락 → 교차 테넌트 노출; 대형 테넌트가 공유 자원 독점 | 테넌트 키 파티셔닝 | 기존 노트 원고 · AWS SaaS Lens [?] | 권장 | `systems/multi-tenancy` (연결: `database/35-row-level-security`) |
| 20-quality-attributes-and-tradeoffs | 품질 속성(가용성·성능·확장성·유지보수성·동시성·UX)과 트레이드오프 | 15 | 속성 간 충돌을 명시 안 함 → 한 속성 최적화가 다른 속성 붕괴 | 유틸리티 트리(ATAM) | ISO/IEC 25010:2023 · Bass 외 『Software Architecture in Practice』 [?] | 필수 | `engineering/engineering-axes` (README + 7축 병합) |
| 21-architecture-decision-records | ADR — 결정·맥락·결과 기록 | 20 | 결정 근거 소실 → 같은 논쟁 반복, 반대 결정으로 회귀 | — | Nygard 2011 "Documenting Architecture Decisions" | 권장 | 신규 |
| 22-configuration-and-12factor | 설정·환경 분리·12-factor | 16 | 환경별 설정 드리프트 → 스테이징 통과·운영 장애; 시크릿 이미지 포함 | — | 12factor.net | 권장 | 신규 |

### 12.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 23-design-symptom-index | 역색인: "작은 변경에 파일 N개", "테스트 작성 불가", "배포를 같이 해야 함", "이 클래스는 아무도 못 건드림" → 원인 스멜·원칙 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 24-design-incidents | 실사건: Therac-25(1985–87, 재사용 코드의 하드웨어 인터록 가정 + 경쟁 조건) · Healthcare.gov 출시 장애(2013, 통합·아키텍처) | 23 | — | — | Leveson–Turner IEEE Computer 1993 · 미 GAO-14-694 [?] | 권장 | 신규 |

---

## 13. 도메인 모델링 (`domain-modeling/`)

> 기초(도메인 vs 애플리케이션) → 전술 설계 → 전략 설계 → 연습 트랙. 기존 basic 30·advanced 30 연습 문제는 **컬렉션 그대로 유지**하고 leaf 18·19가 가리킨다.
> 뼈대: Evans 『Domain-Driven Design』(2부 Building Blocks, 4부 Strategic Design), Evans 『DDD Reference』 2015, Vernon 『Implementing DDD』, Vernon "Effective Aggregate Design" 2011.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 09 → 06 → 07 → 08 → 10 → 11 → 18 → 12 → 13 → 14 → 15 → 16 → 17 → 19 → 20 → 21

### 13.1 기초

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-domain-vs-application-logic | 도메인 규칙과 애플리케이션 흐름의 경계 | software-design/02-modularity-coupling-cohesion | 규칙이 서비스·컨트롤러에 흩어짐 → 같은 규칙 N벌 중 하나만 수정 | — | Evans 4장 · Fowler 『PoEAA』 Service Layer | 필수 | `domain-modeling/domain-vs-application-logic` |
| 02-pojo-and-persistence-ignorance | 프레임워크 독립 도메인 객체 | 01 | 도메인이 ORM 어노테이션·프록시에 묶임 → 단위 테스트 불가·지연 로딩 예외 | — | Fowler "POJO" · Evans | 권장 | `domain-modeling/pojo` |
| 03-ubiquitous-language | 코드·대화·문서의 단일 언어 | 01 | 같은 단어 다른 뜻(예: "주문 완료") → 요구와 구현 불일치; 단위 누락 | 용어집 | Evans 2장 | 필수 | 신규 |

### 13.2 전술 설계

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-entities-and-value-objects | 식별성 vs 값 동등성 | 03, software-design/08-immutability-and-value-objects | 값 객체 equals 누락 → 컬렉션 중복; 원시값 집착(금액을 `long`) → 통화 혼합 | — | Evans 5장 | 필수 | 신규 |
| 05-aggregates-and-invariants | 일관성 경계·불변식·Vernon 4규칙 | 04, database/20-transactions-acid | 거대 aggregate → 락 경합·`OptimisticLockException` 폭증; 경계 밖 불변식 → 동시성에 깨짐 | 트리(루트 경유 접근) | Evans 6장 · Vernon 2011 | 필수 | 신규 |
| 06-domain-services-and-policies | 엔티티에 안 맞는 규칙·정책 객체 | 05 | 서비스 비대 → 빈약한 모델로 회귀 | 전략 패턴 | Evans 5장 | 권장 | 신규 |
| 07-domain-events | 도메인 이벤트 발행·처리 | 05, distributed/21-outbox-and-dual-write | 트랜잭션 커밋 전 이벤트 발행 → 롤백됐는데 후속 처리 진행 | — | Vernon 『IDDD』 8장 [?] | 필수 | 신규 |
| 08-repositories-and-factories | 영속성 추상·생성 캡슐화 | 05 | 리포지토리가 쿼리 메서드 폭증 → 도메인 로직 누출 | — | Evans 6장 | 권장 | 신규 |
| 09-anemic-vs-rich-model | 빈약한 도메인 모델 vs 풍부한 모델 | 05 | setter로 아무 상태나 → 불법 상태 저장 | — | Fowler "AnemicDomainModel" 2003 | 필수 | 신규 |
| 10-state-machines-in-domain | 상태·전이·가드로 수명 주기 모델링 | 09 | 불법 전이(환불된 주문 배송) → 데이터 모순; 동시 전이 경합 | **유한 상태 기계** | Harel 1987 (statecharts) | 필수 | 신규 (연결: `domain-modeling/basic/09-order-state`) |
| 11-time-money-and-units | 금액(정밀 소수·반올림)·통화·시간대·기간·단위 | 04, architecture/03-floating-point-ieee754 | 반올림 누적 → 1원 차이 정산 불일치; DST 전환일 중복/누락 시간; 단위 혼동 | 정밀 소수, 은행가 반올림 | Fowler 『PoEAA』 Money · IANA tz 데이터베이스 | 필수 | 신규 (연결: `advanced/05-multi-currency`, `languages/java/syntax/51~53`) |

### 13.3 전략 설계

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 12-bounded-contexts | 모델의 유효 경계 | 03 | 하나의 "고객" 모델을 전사 공유 → 모든 팀이 서로를 깨뜨림 | — | Evans 14장 · DDD Reference | 필수 | 신규 |
| 13-subdomains | 핵심·지원·일반 서브도메인과 투자 배분 | 12 | 일반 서브도메인(인증·결제 게이트웨이) 자체 구현에 핵심 역량 소진 | — | Evans 15장 · DDD Reference | 권장 | 신규 |
| 14-context-mapping | Partnership·Shared Kernel·Customer/Supplier·Conformist·ACL·OHS·Published Language·Separate Ways | 12 | 관계 미정의 → 상류 변경이 하류를 예고 없이 파손 | 컨텍스트 그래프 | Evans 14장 · DDD Reference | 권장 | 신규 |
| 15-anti-corruption-layer | 외부 모델 번역 계층 | 14 | ACL 부재 → 레거시·외부 API 모델이 핵심 도메인 오염 | 어댑터·번역기 | Evans 14장 | 권장 | 신규 |
| 16-event-storming | 이벤트 중심 협업 모델링 | 12 | 개발자만 모델링 → 도메인 전문가 지식 누락 | 타임라인 | Brandolini 『Introducing EventStorming』 [?] | 권장 | 신규 |
| 17-cqrs | 명령과 조회 모델 분리 | 07, database/29-replication-leader-follower | 조회 모델 지연 → "저장했는데 목록에 없음"; 불필요한 CQRS → 복잡도만 증가 | 프로젝션(폴드) | Fowler "CQRS" 2011 · `systems/server-design` 03 | 권장 | `systems/server-design/03-data-layer.md` (분할 — CQRS 절) |

### 13.4 연습 트랙

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 18-basic-modeling-exercises | 기초 모델링 연습 30편(주차 요금~배차) — 컬렉션 유지 | 11 | (각 편의 ⚠ 절) | 편별 상이(FSM·구간·트리·그래프) | 기존 원고 | 필수 | `domain-modeling/basic` (30편 유지) |
| 19-advanced-modeling-exercises | 심화 모델링 연습 30편(급여~B2B 등급) — 컬렉션 유지 | 17, 18 | (각 편의 ⚠ 절) | 편별 상이 | 기존 원고 | 권장 | `domain-modeling/advanced` (30편 유지) |

### 13.5 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 20-dm-symptom-index | 역색인: 불법 상태 데이터, 1원 정산 차이, 같은 규칙 N벌, 거대 트랜잭션 락, 팀 간 모델 충돌 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 21-dm-incidents | 실사건: Mars Climate Orbiter 단위 불일치(1999, 파운드·초 vs 뉴턴·초) · 영국 Post Office Horizon 회계 불일치(1999~) | 20 | — | — | NASA MCO 사고조사보고서 1999 · Bates v Post Office [2019] EWHC 3408 (QB) | 권장 | 신규 |

---

## 14. 테스트 (`testing/`) — 신설

> 기존 보유 0 — **갭 최대**. 왜·무엇을 → 단위 테스트의 질 → 테스트 더블·학파 → TDD → 설계 기법 → 통합·계약 → 고급 기법 → 불안정성.
> 뼈대: Google 『Software Engineering at Google』(이하 SWE@G — 11·12·13·14장), Khorikov 『Unit Testing Principles, Practices, and Patterns』, Beck 『TDD by Example』·"Canon TDD"(2023), Fowler "Mocks Aren't Stubs", Meszaros 『xUnit Test Patterns』, Feathers 『Working Effectively with Legacy Code』.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 11 → 12 → 14 → 08 → 09 → 10 → 15 → 16 → 13 → 17 → 18 → 19

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-why-test-and-pyramid | 테스트의 목적·피라미드·크기와 범위 | software-design/01-complexity | **아이스크림 콘**(E2E 과다) → 느리고 불안정한 CI, 결국 무시됨 | — | SWE@G 11장 · Fowler "TestPyramid" | 필수 | 신규 |
| 02-good-unit-tests | 좋은 테스트 4기둥(회귀 방지·리팩터링 내성·빠른 피드백·유지보수성), AAA | 01 | 구현 세부 검증 → 리팩터링마다 대량 실패(거짓 양성) | — | Khorikov 4장 · SWE@G 12장 | 필수 | 신규 |
| 03-test-doubles | Dummy·Fake·Stub·Spy·Mock | 02 | 과도한 mock → 테스트는 초록인데 실제 통합에서 실패; mock이 실제와 다른 계약 | Fake = 인메모리 자료구조 구현 | Meszaros · Fowler "Mocks Aren't Stubs" · SWE@G 13장 | 필수 | 신규 |
| 04-classical-vs-london | 고전파 vs 런던파(상태 검증 vs 상호작용 검증) | 03 | 런던파 과용 → 구현에 고착된 테스트 | — | Khorikov 2장 · Fowler "Mocks Aren't Stubs" | 권장 | 신규 |
| 05-tdd | 테스트 목록 → 하나씩 → 통과 → 리팩터링 | 02 | 기대값에 계산 결과를 붙여 넣기 → 버그를 정답으로 고정; 리팩터링 단계 생략 | — | Beck 『TDD by Example』 · Beck "Canon TDD" 2023 | 필수 | 신규 |
| 06-test-design-techniques | 동치 분할·경계값·결정 테이블·상태 전이·쌍 조합 | 02, math/02-induction-and-invariants | 경계값 누락 → off-by-one·빈 입력·최댓값에서 장애 | 상태 전이 그래프, pairwise 조합 | ISTQB Foundation Syllabus 4장 [?] | 필수 | 신규 |
| 07-integration-tests-real-dependencies | 실제 DB·브로커로 통합 테스트(Testcontainers) | 03 | H2로 테스트 → 운영 PostgreSQL 방언·락 동작 차이로 운영에서만 실패 | — | SWE@G 14장 · Testcontainers 문서 | 필수 | 신규 |
| 08-contract-testing | 소비자 주도 계약 테스트 | 07, api-design/08-versioning-and-compatibility | 제공자 필드 변경 → 소비자만 운영에서 파손 | 계약 = 예제 집합 | Pact 문서 · Fowler "ContractTest" | 권장 | 신규 |
| 09-property-based-testing | 성질·생성기·축소(shrinking) | 06 | 예제 기반만 → 드문 입력 조합 버그 누락 | 무작위 생성 + 축소(이진 탐색식) | Claessen–Hughes ICFP 2000 (QuickCheck) | 권장 | 신규 |
| 10-mutation-testing | 변이 주입으로 테스트의 판별력 측정 | 02 | 커버리지 100%인데 단언 없음 → 버그 통과 | 변이 연산자 | Jia–Harman TSE 2011 · PIT 문서 | 권장 | 신규 |
| 11-flaky-tests | 불안정 테스트의 원인(시간·순서·동시성·공유 상태·네트워크) | 07 | 재시도로 덮기 → 진짜 경쟁 조건 은폐; CI 신뢰 붕괴 | — | Luo 외 FSE 2014 | 필수 | 신규 |
| 12-testing-time-and-concurrency | 시계 주입·결정적 스케줄·동시성 테스트 | 11, os/15-race-conditions | `Thread.sleep` 기반 테스트 → 느리고 불안정; 자정·월말·DST에만 실패 | 가짜 시계, 결정적 스케줄러 | SWE@G 13장 [?] · Java `Clock` 문서 | 권장 | 신규 |
| 13-e2e-and-ui-testing | E2E·UI 테스트의 범위와 비용 | 07 | 선택자 취약 → UI 변경마다 대량 실패 | — | SWE@G 14장 | 권장 | 신규 |
| 14-test-data-and-fixtures | 픽스처·빌더·오브젝트 마더·격리 | 02 | 공유 픽스처 → 테스트 순서 의존; 거대 픽스처 → 무엇을 검증하는지 불명 | 테스트 데이터 빌더 | Meszaros 『xUnit Test Patterns』 | 권장 | 신규 |
| 15-coverage-and-its-limits | 라인·분기·조건 커버리지의 의미와 한계 | 10 | 커버리지 목표 강제 → 단언 없는 테스트 양산(굿하트) | 제어 흐름 그래프 | SWE@G 11장 [?] · Google Testing Blog "Code Coverage Best Practices" 2020 | 권장 | 신규 |
| 16-characterization-tests-legacy | 레거시에 특성 테스트로 안전망 치기·이음새 | 06, software-design/06-refactoring | 안전망 없이 레거시 수정 → 숨은 동작 파손 | 이음새(seam) | Feathers 『Working Effectively with Legacy Code』 | 권장 | 신규 |
| 17-testing-in-production | 합성 모니터링·카나리 분석·섀도 트래픽 | reliability/27-deployment-strategies | 운영 검증 없이 배포 → 테스트 환경에서 재현 안 되는 장애 | — | SRE Workbook [?] | 심화 | 신규 |
| 18-test-symptom-index | 역색인: CI 가끔 실패, 리팩터링마다 대량 실패, 초록인데 운영 장애, 테스트 느림, 커버리지 높은데 버그 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 19-test-incidents | 실사건: Apple `goto fail`(2014, 중복 goto로 서명 검증 우회 — 음성 테스트 부재) · CrowdStrike(2024, 콘텐츠 검증기 결함과 단계적 배포 부재 — 운영 관점은 reliability/34) | 18 | — | — | CVE-2014-1266 · CrowdStrike PIR 2024-08-06 | 권장 | 신규 |

---

## 15. API 설계 (`api-design/`)

> 원리(계약·자원·의미론) → 신뢰성 계약(멱등·페이지·버전·스키마) → 스타일(REST·RPC·GraphQL·비동기) → 기존 사례 6편. **HTTP 프로토콜 본문은 network/33~35**, 여기선 설계 판단만.
> 뼈대: Fielding 박사논문 5장(2000), RFC 9110·9457, Google AIP(aip.dev), Kleppmann DDIA 4장, Stripe API 문서.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 08 → 09 → 12 → 13 → 07 → 14 → 10 → 11 → 15 → 16~21(사례) → 22 → 23

### 15.1 원리

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-api-as-contract | API = 공개 계약, Hyrum의 법칙 | software-design/12-design-by-contract | 문서에 없는 동작(정렬 순서·에러 문구)에 클라이언트가 의존 → "버그 수정"이 장애 | — | SWE@G 1장 (Hyrum's Law) [?] · hyrumslaw.com | 필수 | 신규 |
| 02-rest-and-resource-modeling | 자원·표현·균일 인터페이스·성숙도 모델 | 01, network/33-http-semantics | 동사형 URL·모든 것을 POST → 캐시·재시도 의미 상실 | 자원 계층(트리) | Fielding 2000 5장 · Fowler "Richardson Maturity Model" | 필수 | 신규 |
| 03-status-codes-for-apis | 상태 코드 선택(4xx vs 5xx, 409/422/429) | 02 | 200에 에러 바디 → 모니터링·재시도 로직 무력화; 4xx를 5xx로 → 불필요 재시도 폭풍 | — | RFC 9110 15장 | 필수 | 신규 |
| 04-error-format-problem-details | 에러 응답 표준 형식 | 03 | 에러 형식 제각각 → 클라이언트 파싱 실패; 스택 트레이스 노출 | — | RFC 9457 | 권장 | 신규 |

### 15.2 신뢰성 계약

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 05-idempotency-keys | `Idempotency-Key`·멱등 메서드·재시도 안전 | 03, reliability/12-idempotency | 네트워크 타임아웃 후 재시도 → **이중 결제**; 같은 키 다른 본문 처리 규칙 부재 | 키-결과 저장소 | Stripe "Idempotent requests" · IETF draft-ietf-httpapi-idempotency-key-header [?] | 필수 | 신규 |
| 06-pagination | offset vs 커서(keyset) | 02, database/12-btree-indexes | 깊은 offset → 풀스캔으로 느려짐; 페이지 사이 삽입 → 중복·누락 | keyset = B+Tree 범위 스캔 | Google AIP-158 · Winand "Paging Through Results" [?] | 필수 | 신규 (연결: `languages/sql/syntax/09-limit-offset-keyset-pagination`) |
| 07-filtering-sorting-search | 필터·정렬 파라미터 설계 | 06 | 임의 필드 정렬 허용 → 인덱스 없는 정렬 쿼리로 DB 과부하 | — | Google AIP-160 · AIP-132 | 권장 | 신규 |
| 08-versioning-and-compatibility | 하위 호환 규칙·버저닝·폐기(Deprecation/Sunset) | 01 | 필드 삭제·의미 변경 → 구 클라이언트 파손; **enum 값 추가** → 엄격 역직렬화 클라이언트 실패 | — | Google AIP-180 · RFC 8594 · RFC 9745 [?] | 필수 | 신규 |
| 09-schema-and-serialization | JSON·Protobuf·Avro, 스키마 진화 | 08 | 64비트 ID를 JSON 숫자로 → JS에서 2^53 초과 정밀도 손실; 필드 번호 재사용(Protobuf) → 조용한 오역 | 가변 길이 정수 인코딩(varint) | DDIA 4장 · RFC 8259 | 필수 | 신규 |
| 12-async-apis-and-webhooks | 웹훅·콜백·재전송·서명 | 05, security/05-mac-and-hmac | 서명 검증 없음 → 위조 이벤트; 순서 역전·중복 전달 → 상태 역행 | 재시도 큐, 서명 | Standard Webhooks 명세 [?] | 필수 | 신규 (연결: `api-design/05-delivery-webhook` 사례) |
| 13-concurrency-control-in-apis | ETag·`If-Match`·조건부 요청 | 08, database/24-occ-and-timestamp-ordering | 동시 편집 → **lost update**; `412 Precondition Failed` 처리 누락 | 버전 비교 | RFC 9110 13장 | 권장 | 신규 |
| 14-long-running-operations | `202 Accepted` + 작업 자원·폴링 | 12 | 동기로 처리하다 LB 타임아웃 → 결과 불명 + 재시도 중복 | 작업 상태 기계 | Google AIP-151 | 권장 | 신규 |

### 15.3 스타일·문서

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 10-rpc-and-grpc | RPC 의미론·gRPC·데드라인·상태 코드 | 09, network/36-http2-multiplexing | 데드라인 미설정 → 하류 정지 시 무한 대기; L4 LB + 장수 HTTP/2 연결 → 부하 불균형 | — | gRPC 문서 (Deadlines·Status codes) | 권장 | 신규 |
| 11-graphql | 스키마·리졸버·쿼리 복잡도 | 02 | 리졸버 N+1; 깊이·복잡도 제한 없음 → 쿼리 하나로 DoS | DataLoader(배치+캐시) | GraphQL 명세 · graphql/dataloader | 권장 | 신규 |
| 15-api-documentation-openapi | 명세 우선·OpenAPI·예제 | 01 | 문서-구현 불일치 → 클라이언트 오구현 | — | OpenAPI 3.1 명세 | 권장 | 신규 |

### 15.4 사례 (기존 6편 — 번호만 이동)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 16-case-order-point | 주문·포인트 API 사례 | 05, 13 | (사례 본문 ⚠) | — | 기존 원고 | 권장 | `api-design/01-order-point` |
| 17-case-coupon-issue | 선착순 쿠폰 발급 | 05, database/25-app-level-concurrency-patterns | 초과 발급 | 원자 카운터 | 기존 원고 | 권장 | `api-design/02-coupon-issue` |
| 18-case-stock-deduct | 재고 차감 | database/25-app-level-concurrency-patterns | 재고 음수 | 조건부 UPDATE | 기존 원고 | 권장 | `api-design/03-stock-deduct` |
| 19-case-settlement-report | 정산 리포트 | 14, 06 | 대용량 동기 조회 타임아웃 | 배치·스트리밍 | 기존 원고 | 권장 | `api-design/04-settlement-report` |
| 20-case-delivery-webhook | 배송 웹훅 | 12 | 중복·순서 역전 | 재시도 큐 | 기존 원고 | 권장 | `api-design/05-delivery-webhook` |
| 21-case-refund | 환불 | 05, distributed/20-saga | 부분 환불 이중 처리 | 상태 기계 | 기존 원고 | 권장 | `api-design/06-refund` |

### 15.5 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-api-symptom-index | 역색인: 이중 처리, 목록 중복/누락, 구 앱만 크래시, ID 끝자리 변형, 412/409/429, 웹훅 역순 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 23-api-incidents | 실사건: Twitter 64비트 ID와 JS 정밀도 → `id_str` 도입(2010) · Optus 무인증 API 열거 유출(2022) [?] | 22 | — | — | Twitter 개발자 공지 2010 [?] · 호주 의회·OAIC 자료 [?] | 권장 | 신규 |

---

## 16. 웹 플랫폼 (`web-platform/`) — 신설 (개념만)

> 브라우저라는 **실행 환경의 원리**만 CS 트리에 둔다: 렌더링 파이프라인·이벤트 루프·출처 모델·저장소·캐시·성능. DOM API 118파일 레퍼런스(`foundations/web-api`)는 CS 밖(§19) — 여기서 실습 근거로 링크한다. SOP/CORS 본문은 security/20, HTTP 캐시 본문은 network/34.
> 뼈대: WHATWG HTML 표준(Event loops 절·Rendering 절), WHATWG Fetch, web.dev "Rendering performance"·Core Web Vitals, W3C Service Workers.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-browser-architecture | 멀티 프로세스·사이트 격리·렌더러 | os/04-process-and-lifecycle | 한 탭 무한 루프 → 해당 렌더러만 "응답 없음" | — | Chromium 설계 문서 "Multi-process Architecture" | 권장 | 신규 |
| 02-rendering-pipeline | 파싱 → DOM/CSSOM → 스타일 → 레이아웃 → 페인트 → 합성 | 01, language/03-parsing-grammars-ast | 읽기·쓰기 교대 → **layout thrashing** 강제 동기 레이아웃; 렌더 차단 CSS·JS | DOM 트리, 스타일 규칙 매칭(오른쪽→왼쪽) | web.dev "Rendering performance" · HTML 표준 "Rendering" | 필수 | 신규 (연결: `foundations/web-api/10-layout-thrashing`, `08·09`) |
| 03-event-loop | 태스크·마이크로태스크·렌더링 기회·rAF | 02, os/21-event-based-concurrency | 긴 태스크 → 입력 지연(INP 악화); 마이크로태스크 무한 연쇄 → 렌더 영구 정지 | 태스크 큐, 마이크로태스크 큐 | HTML 표준 "Event loops" 절 | 필수 | 신규 (연결: `foundations/web-api/38-request-animation-frame`, `39-idle-scheduling`) |
| 04-dom-and-event-model | DOM 트리·이벤트 전파(캡처/버블)·위임 | 03 | 리스너 누수 → 메모리 증가; `stopPropagation` 남용 → 위임 핸들러 무력화 | 트리 순회 | WHATWG DOM 표준 | 필수 | 신규 (연결: `foundations/web-api/01·15~18·20`) |
| 05-fetch-from-browser | fetch 수명·스트리밍·중단·자격 증명 | 04, network/33-http-semantics | **fetch는 4xx/5xx에 reject하지 않음** → 에러를 성공으로 처리; 타임아웃 기본값 없음 | — | WHATWG Fetch | 필수 | 신규 (연결: `foundations/web-api/25~30`) |
| 06-browser-storage | 쿠키·localStorage·IndexedDB·쿼터·축출 | 05, security/11-sessions-and-cookie-security | localStorage에 토큰 → XSS 한 번에 탈취; Safari ITP 7일 제한으로 저장소 삭제 [?]; 쿼터 초과 `QuotaExceededError` | 키-값 저장소, B-트리(IndexedDB 구현) | WHATWG Storage · W3C IndexedDB | 권장 | 신규 |
| 07-service-workers-and-offline | 서비스 워커 수명·캐시 전략 | 06, network/34-http-caching | SW 캐시 고착 → 배포해도 구 버전이 계속 뜸 | 캐시 저장소 | W3C Service Workers | 권장 | 신규 |
| 08-web-performance-vitals | LCP·INP·CLS와 측정(RUM vs 랩) | 02, 03 | 랩 측정만 → 실제 사용자 저사양 기기 성능 은폐; 이미지 크기 미지정 → 레이아웃 이동 | 백분위(p75) 집계 | web.dev "Web Vitals" | 필수 | 신규 |
| 09-js-modules-and-bundling | 모듈 체계·번들링·코드 분할·트리 셰이킹 | 05, language/17-modules-and-dependency-resolution | 번들 비대 → 초기 로드 지연; 청크 해시 불일치 → 배포 직후 `ChunkLoadError` | 모듈 의존 그래프, 도달성 분석(트리 셰이킹) | ECMA-262 Modules 절 · 번들러 문서 | 권장 | 신규 |
| 10-rendering-strategies | CSR·SSR·SSG·스트리밍·하이드레이션 | 02, 09 | 서버/클라이언트 렌더 결과 불일치 → hydration mismatch 경고·깜빡임; SSR에서 사용자별 데이터 캐시 → 교차 노출 | — | web.dev "Rendering on the Web" | 권장 | 신규 |
| 11-accessibility-basics | 시맨틱 마크업·접근성 트리·키보드·ARIA | 04 | div 버튼 → 키보드·스크린리더 사용 불가; 잘못된 ARIA가 없는 것보다 나쁨 | 접근성 트리 | WCAG 2.2 · WAI-ARIA 1.2 | 권장 | 신규 |
| 12-web-symptom-index | 역색인: CORS 에러, fetch 성공인데 에러, 화면 멈춤, hydration mismatch, `ChunkLoadError`, 배포가 반영 안 됨, 레이아웃 튐 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 13-web-incidents | 실사건: British Airways 결제 페이지 스크립트 변조(Magecart, 2018) · polyfill.io 도메인 인수 후 악성 코드 배포(2024) | 12 | — | — | ICO 과징금 결정 2020 · Sansec 2024-06 보고 | 권장 | 신규 |

---

## 17. 엔지니어링 실천 (`engineering-practice/`)

> SWEBOK v4의 Requirements·Configuration Management·Process·Management·Professional Practice·Economics KA를 개발자 시점으로 압축. 기존 agile-and-squad·development-standards(4축)·three-virtues가 들어온다.
> 뼈대: SWEBOK v4, SWE@G 9·16·18·23·24장(16·18 `[?]`), DORA, Google eng-practices, ISO/IEC/IEEE 29148.

**권장 학습 순서**: 01 → 02 → 04 → 05 → 06 → 08 → 07 → 09 → 10 → 11 → 03 → 12 → 13 → 14 → 15 → 16 → 17 → 18

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-lifecycle-and-agile | 개발 수명 주기·애자일·스쿼드 | — | 의식만 남은 애자일 → 회고 없음·같은 문제 반복 | — | Agile Manifesto 2001 · SWEBOK v4 Process KA | 필수 | `engineering/agile-and-squad` |
| 02-requirements-engineering | 요구 도출·명세·검증·추적 | 01 | 모호 요구("빠르게") → 구현 후 재작업; 비기능 요구 누락 | 추적 매트릭스 | ISO/IEC/IEEE 29148 · SWEBOK v4 Requirements KA | 권장 | 신규 |
| 03-estimation-and-planning | 추정·불확실성 원뿔·계획 | 02 | 단일 점 추정 → 일정 상습 초과 | 3점 추정 | McConnell 『Software Estimation』 [?] | 권장 | 신규 |
| 04-version-control-and-git-internals | 스냅샷·객체 모델·브랜치·병합 | data-structure/27-merkle-tree | force push로 남의 커밋 유실; 병합 충돌 오해결 → 조용한 코드 소실 | **Merkle DAG**, 3-way merge(LCA) | Pro Git 10장 | 필수 | 신규 |
| 05-branching-strategies | git-flow vs trunk-based·피처 플래그 | 04 | 장수 브랜치 → 머지 지옥·통합 버그 | — | SWE@G 16장 [?] · trunkbaseddevelopment.com | 필수 | 신규 |
| 06-code-review | 리뷰의 목적·기준·크기 | 05 | 거대 PR → 형식적 승인(LGTM)으로 버그 통과 | — | Google eng-practices · SWE@G 9장 | 필수 | 신규 |
| 07-build-systems-and-reproducibility | 증분 빌드·캐시·재현 가능 빌드 | 04, language/17-modules-and-dependency-resolution | 로컬에선 되는데 CI에선 실패(환경 의존); 캐시 오염 → 옛 산출물 배포 | **빌드 DAG + 위상정렬**, 콘텐츠 해시 캐시 | SWE@G 18장 [?] · reproducible-builds.org | 권장 | 신규 |
| 08-ci-cd-pipelines | 지속적 통합·전달·배포 파이프라인 | 05, testing/01-why-test-and-pyramid | 빨간 main 방치 → 모두 막힘; 배포 수동 단계 → 절차 누락(Knight Capital) | 파이프라인 DAG | SWE@G 23·24장 · Humble–Farley 『Continuous Delivery』 | 필수 | 신규 |
| 09-dora-metrics | 배포 빈도·리드 타임·변경 실패율·복구 시간·재작업률 | 08 | 지표를 목표로 → 게이밍(굿하트) | — | dora.dev "DORA's software delivery metrics" | 권장 | 신규 |
| 10-technical-debt | 기술부채 4사분면·상환 전략 | software-design/05-code-smells | 부채 가시화 안 함 → 속도 점진 저하 후 전면 재작성 유혹 | — | Fowler "TechnicalDebtQuadrant" 2009 | 권장 | 신규 |
| 11-documentation-practices | 문서 유형(튜토리얼·방법·레퍼런스·설명)·문서 신선도 | 02 | 낡은 런북 → 사고 때 잘못된 절차 실행 | — | Diátaxis · SWE@G 10장 [?] | 권장 | 신규 |
| 12-quality-standards | 품질 표준(코드 품질 기준) | 06 | 기준 부재 → 리뷰 편차 | — | 기존 원고 | 권장 | `engineering/development-standards/quality-standards` |
| 13-security-standards | 보안 표준(개발 보안 기준) | security/01-security-principles | 기준 부재 → 알려진 취약점 반복 | — | 기존 원고 | 권장 | `engineering/development-standards/security-standards` |
| 14-operational-standards | 운영 표준 | reliability/23-logging | 기준 부재 → 서비스마다 다른 로그·지표 | — | 기존 원고 | 권장 | `engineering/development-standards/operational-standards` |
| 15-legal-standards | 법률 표준(개인정보·라이선스 등) | 12 | 라이선스 위반 의존성·개인정보 보관 기한 위반 | — | 기존 원고 (`provisions.md` 포함) | 권장 | `engineering/development-standards/legal-standards` (+ `index.md`·`README.md` 흡수) |
| 16-engineering-virtues | 게으름·조급함·오만 — 개발자 태도 | 01 | — | — | Wall 외 『Programming Perl』 용어집 | 심화 | `foundations/three-virtues` |
| 17-practice-symptom-index | 역색인: 머지 지옥, CI 불신, 배포 공포, 리뷰 병목, "이건 왜 이렇게 했지?" | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 18-practice-incidents | 실사건: Knight Capital(2012-08-01, 수동 배포 누락 서버 + 재사용된 플래그로 45분 4.4억 달러 손실) · Cloudflare WAF 규칙 전역 즉시 배포(2019-07-02 — 알고리즘 관점은 algorithm/40) | 17 | — | — | 미 SEC 명령 34-70694 (2013) · Cloudflare 블로그 2019-07-12 | 권장 | 신규 |

---

# Part 6 — 판단하는 법

## 18. 데이터 분석·통계 (`data-analysis/`) — 신설

> 데이터가 어디서 왔나 → 요약 → 추론 → 관계·모델 → 실험 → 실무(SQL·정제·시각화). 확률·분포 기초는 **math/08~10이 단일 출처**(여기서 반복하지 않음).
> 뼈대: OpenIntro Statistics 4판(장·절 확인), Kohavi·Tang·Xu 『Trustworthy Online Controlled Experiments』(2020, 장 번호 `[?]`), Wilke 『Fundamentals of Data Visualization』, Downey 『Think Stats』 2판, Tukey 『Exploratory Data Analysis』.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 06 → 05 → 07 → 08 → 09 → 10 → 11 → 14 → 15 → 19 → 20 → 21 → 22 → 23 → 25 → 12 → 13 → 16 → 24 → 26 → (17 · 18 심화) → 27 → 28

### 18.1 데이터와 수집

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-data-types-and-measurement | 변수 유형(명목·순서·수치), 측정 척도 | — | 순서형을 수치로 평균(만족도 3.4점); 코드값(우편번호)을 숫자로 집계 | — | OpenIntro 1.2 | 필수 | 신규 |
| 02-sampling-and-bias | 모집단·표본·표본 추출·편향 | 01 | 표본 편향·**생존자 편향**(성공 사례만 분석); 응답 편향 | 무작위·층화 추출 | OpenIntro 1.3 | 필수 | 신규 |
| 03-observational-vs-experimental | 관찰 연구 vs 실험, 교란 변수 | 02 | 관찰 데이터로 인과 주장 → 교란 변수로 반대 결론 | — | OpenIntro 1.4 | 필수 | 신규 |

### 18.2 기술통계

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-descriptive-statistics | 중심(평균·중앙값)·산포(분산·IQR)·분위수·이상치 | 01, math/09-expectation-variance-tails | 치우친 분포(소득·지연)에 평균 보고 → 대부분의 경험과 괴리 | 선택 알고리즘(중앙값 O(n)) | OpenIntro 2.1–2.2 | 필수 | 신규 |
| 05-exploratory-data-analysis | EDA — 분포·관계 먼저 보기 | 04 | 요약 통계만 보고 모델링 → Anscombe 콰르텟 함정 | 히스토그램·박스플롯 | Tukey 1977 · OpenIntro 2.3 | 권장 | 신규 |
| 06-percentiles-and-latency-distributions | 백분위 계산·병합·히스토그램, 긴 꼬리 | 04 | **백분위를 평균 내기**(인스턴스 p99의 평균 ≠ 전체 p99); 버킷 해상도 부족 | HdrHistogram, t-digest, 분위 스케치 | Dunning–Ertl 2019 (t-digest) | 필수 | 신규 |

### 18.3 추론 (확률 기초는 math/08~10)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 07-sampling-distributions-and-clt | 표본 분포·표준오차·중심극한정리 | 04, math/10-common-distributions | 작은 표본·극단 꼬리 분포에 정규 근사 → 신뢰구간 과소 | 부트스트랩 재표집 | OpenIntro 5.1 | 필수 | 신규 |
| 08-confidence-intervals | 신뢰구간 해석과 계산 | 07 | "참값이 95% 확률로 구간 안" 오해석 | — | OpenIntro 5.2 | 필수 | 신규 |
| 09-hypothesis-testing | 귀무·대립·p-value·1종/2종 오류 | 08 | p < 0.05 = "효과가 크다" 오해; 통계적 유의 ≠ 실질적 유의 | — | OpenIntro 5.3 | 필수 | 신규 |
| 10-power-and-sample-size | 검정력·최소 탐지 효과·표본 크기 | 09 | 검정력 부족 실험 → "효과 없음" 오결론; 너무 작은 효과 추적 → 영원히 안 끝나는 실험 | — | OpenIntro 7.4 | 권장 | 신규 |
| 11-multiple-comparisons | 다중 비교·p-hacking·보정 | 09 | 지표 20개 중 1개 유의 → 우연을 발견으로 발표 | Bonferroni·BH 절차 | OpenIntro 7.5C · Ioannidis 2005 | 필수 | 신규 |
| 12-categorical-inference | 비율 추론·카이제곱 적합도·독립성 | 09 | 기대 빈도 작은 칸에 카이제곱 → 부정확 | 분할표 | OpenIntro 6장 | 권장 | 신규 |
| 13-numerical-inference-t-anova | t 분포·대응 표본·두 평균 차·ANOVA | 09 | 대응 데이터를 독립 표본으로 검정 → 검정력 낭비 | — | OpenIntro 7장 | 권장 | 신규 |

### 18.4 관계·모델

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 14-correlation-vs-causation | 상관·교란·**심슨의 역설** | 03, 09 | 부분군별 추세와 전체 추세 반대 → 잘못된 정책 결정 | — | OpenIntro 8.1 · Pearl 외 『Causal Inference in Statistics: A Primer』 [?] | 필수 | 신규 |
| 15-linear-regression | 최소제곱·잔차·결정계수·회귀 추론 | 14 | 외삽; 이상치 레버리지로 기울기 왜곡; 잔차 패턴 무시 | 최소제곱(선형대수, math/12) | OpenIntro 8장 | 필수 | 신규 |
| 16-multiple-and-logistic-regression | 다중 회귀·모델 선택·로지스틱 회귀 | 15 | 다중공선성 → 계수 부호 뒤집힘; 누설 변수(미래 정보)로 과대 성능 | 경사 하강 | OpenIntro 9장 | 권장 | 신규 |
| 17-causal-inference-basics | 인과 DAG·교란 통제·차분의 차분·도구 변수 | 14 | 매개 변수·충돌 변수를 통제 → 편향 유발 | **인과 DAG(그래프)** | Pearl 외 Primer [?] · Angrist–Pischke 『Mostly Harmless Econometrics』 [?] | 심화 | 신규 |
| 18-bayesian-thinking | 사전·사후·베이즈 갱신 | math/08-probability-and-bayes | 사전분포 무시 → 소표본 극단값(별점 5.0 리뷰 1개) 과신 | 켤레 사전분포 갱신 | Downey 『Think Bayes』 [?] | 심화 | 신규 |

### 18.5 실험

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 19-ab-testing-design | 무작위 배정·단위·지표·기간 | 09, 10 | 배정 단위 불일치(세션 vs 사용자) → 분산 과소; 신규성 효과 | 해시 기반 결정적 배정 | Kohavi 외 2020 2·3장 [?] | 필수 | 신규 (연결: `domain-modeling/advanced/27-ab-assign`) |
| 20-ab-pitfalls-srm-peeking | **SRM**(표본 비율 불일치)·엿보기·간섭 | 19, 11 | 50:50 설계인데 50.8:49.2 → 배정·로깅 버그 신호(결과 무효); 중간에 보고 멈추기 → 1종 오류 폭증 | 카이제곱 적합도(12) | Kohavi 외 2020 21장 [?] · Fabijan 외 KDD 2019 | 필수 | 신규 |
| 21-metrics-design | 목표·가드레일·대리 지표 | 19 | 대리 지표 최적화 → 본 목표 훼손(굿하트); 가드레일 없음 → 지연·오류 악화 출시 | — | Kohavi 외 2020 6·7장 [?] | 권장 | 신규 |

### 18.6 실무

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-sql-for-analysis | 코호트·퍼널·리텐션·세션화 SQL | database/05-window-functions-and-cte | 조인 팬아웃으로 전환율 부풀림; 시간대 경계 날짜 잘림 | 윈도 함수, gaps-and-islands | Mode/Winand 자료 [?] | 필수 | 신규 (연결: `languages/sql/syntax/26~33`) |
| 23-data-cleaning-and-quality | 결측·중복·이상치·타임존·스키마 드리프트 | 04 | 조용한 결측을 0으로 채움 → 평균 왜곡; UTC/KST 혼합 → 일별 집계 어긋남; **행 수 제한에서 조용한 절단** | 중복 제거(해시), 레코드 연결 | Wickham "Tidy Data" 2014 | 필수 | 신규 |
| 24-time-series-basics | 추세·계절성·이동평균·이상 탐지 | 04 | 계절성 무시 → 월요일마다 이상 알람; 이동평균 지연으로 급변 늦게 탐지 | **EWMA**, 이동 창 | Hyndman–Athanasopoulos 『Forecasting: Principles and Practice』 3판 [?] | 권장 | 신규 |
| 25-data-visualization-principles | 인코딩 선택·비례 잉크·축·색 | 04 | 잘린 y축으로 차이 과장; 3D 파이 → 비율 오독; 이중 축 조작 | — | Wilke 『Fundamentals of Data Visualization』 | 필수 | 신규 |
| 26-reproducible-analysis | 노트북 재현성·파이프라인·버전 | 23 | 셀 실행 순서 의존 → 재실행 시 다른 결과 | 파이프라인 DAG | Wilson 외 "Good Enough Practices in Scientific Computing" 2017 | 권장 | 신규 |

### 18.7 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-da-symptom-index | 역색인: 실험 비율 틀어짐(SRM), 합계가 안 맞음, 너무 좋은 결과, 부분군 반전, 날짜 경계 어긋남, 백분위 병합 오류 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 28-da-incidents | 실사건: Literary Digest 표본 편향(1936) · Google Flu Trends 과대 추정(2013) · Reinhart–Rogoff 엑셀 범위 오류(2013) · 영국 COVID 확진 약 16,000건 누락 — 구형 XLS 행 제한(2020) | 27 | — | — | Squire 1988 · Lazer 외 Science 2014 · Herndon 외 2013 · 영국 PHE 발표 2020-10 | 권장 | 신규 |

---

## 19. 기존 노트 이식 매핑표

> 판정 기호: **이동** = 한 leaf로 그대로 옮김 · **분할** = 절 단위로 여러 leaf에 나눔 · **병합** = 여러 기존 노트를 leaf 하나로 · **유지** = 컬렉션 그대로 두고 leaf가 가리킴 · **연결** = 옮기지 않고 링크만 · **CS 밖** = CS 트리에 넣지 않음(별도 최상위 권고).
> 경로는 `cs/` 기준. 이 표는 **제안**이며 실제 이동은 하지 않았다.

### 19.1 `foundations/` (14개 폴더 + 파일)

| 기존 | 판정 | 새 위치 | 이유 |
|---|---|---|---|
| `foundations/variables-and-memory` | 분할 | language/07 (전달·복사) · language/08 (람다) · language/04 (스코프) · language/12 (참조 카운트·GC) | 파이썬 원고지만 개념은 언어 중립. 파이썬 고유 인터닝 세부는 language/12 안 예시로 |
| `foundations/data-representation` | 분할 | architecture/01 · 03 · 04 · 05 | 진수·IEEE 754·엔디안·유니코드가 각각 서머리 1편 크기 |
| `foundations/oop-basics` | 이동 | software-design/09 | OOP 기초 한 편. 연산자 오버로딩 레퍼런스 절은 languages/python 쪽으로 |
| `foundations/hardware-basics` | 분할 | architecture/06 · 07 · 08 | 게이트→가산기 / 플립플롭→레지스터 / ISA 3단 |
| `foundations/memory-management` | 분할 | architecture/12 (계층·지역성) · architecture/09 (스택 프레임) · os/09 · os/10 · os/11 · 「대용량 조회 스트리밍」 절 → database/32 예시 | 하드웨어(계층)와 OS(가상 메모리) 경계가 섞여 있음 |
| `foundations/process-thread` | 분할 | os/04 · os/07 · os/08 · os/15 · language/16 (GIL) | 프로세스·스레드·스케줄링·경쟁·GIL 5덩어리 |
| `foundations/compiler-pipeline` | 분할 | language/01 · 02 · 03 · 04 | 어휘→구문→심벌→바이트코드. tokenize/ast/dis 실습은 각 leaf 실습 절로 |
| `foundations/data-structures-basics` | 분할 | data-structure/36 (ADT) · 02 · 03 · 04 · 06 (기초 절) · algorithm/32 (재귀) | 심화판(`data-structure/`)과 중복 — 기초 절만 흡수 후 폐기 검토 |
| `foundations/algorithm-basics` | 분할 | algorithm/31 · 06 · 01 · 03 (기초 절) | 심화판(`algorithm/`)과 중복 — 흡수 후 폐기 검토 |
| `foundations/python-basics` | **CS 밖** | 별도 최상위 `reference/languages/python/` 로 흡수 | list/dict/연산자·제어문 = 언어 문법 레퍼런스. 원리가 아니라 "쓰는 법" |
| `foundations/security` (README + 6편) | 분할·이동 | `sha256-and-digest` → security/04 · `hmac` → security/05 · `jwks` → security/13 · `oidc` → security/14 · `identity-and-ids` → security/16 · `audit-enforce-rollout` → security/25 · README → security 영역 index | 6편이 각각 leaf 1개 크기. 이미 3파일 전환 대상 |
| `foundations/three-virtues` | 이동 | engineering-practice/16 | CS 지식이라기보다 태도 — 실천 영역의 심화로 |
| `foundations/languages` (13개 언어 × `syntax/`, 총 2,023파일) | **CS 밖** | 별도 최상위 `reference/languages/<언어>/syntax/` | 아래 19.2 |
| `foundations/languages` 의 언어-특성 5편 + `c-cpp-csharp.md` + README 축① | 병합 | language/19 (+ language/18 에 c-cpp-csharp 일부) | "틀렸을 때 어떻게 틀리는가"로 언어를 비교 — 언어 중립 판단 축이므로 CS 안 |
| `foundations/web-api` (README + 39주제, 118파일) | **CS 밖** | 별도 최상위 `reference/web-platform-api/` | 아래 19.2 |
| `foundations/README.md` · `index.md` | 폐기(대체) | 새 루트 `cs/index.md` 의 Part 지도가 대체 | 부트캠프 챕터 기준 목차라 새 트리와 축이 다름 |

### 19.2 CS 밖 판정 상세 — 별도 최상위 `reference/` 권고

| 대상 | 규모 | 판정 | 이유 | CS 트리와의 연결 방식 |
|---|---|---|---|---|
| `foundations/languages/{c,cpp,csharp,css,go,html,java,js,kotlin,python,rust,sql,ts}/syntax/` | 13개 언어, 언어당 약 50~60주제, 2,023파일 | **CS 밖** | ① 언어 버전에 종속된 **문법·표준 API 레퍼런스**("그 언어로 어떻게 쓰나") — CS 트리는 언어 중립 원리("왜 그렇게 동작하나") ② 규모가 CS 전체 leaf(약 500)의 4배라 한 트리에 두면 사이트 탐색·통계가 레퍼런스에 잠식됨 ③ 갱신 주기가 다름(언어 릴리스 따라감) | CS leaf의 `기존` 칸에 `(연결: languages/…)` 로 실습 예시 링크. 예: os/32 ↔ `c/syntax/44·45`, language/14 ↔ `java/syntax/33`, language/12 ↔ `rust/syntax/08~12`, database/21 ↔ `sql/syntax/56` |
| `foundations/languages/sql/syntax/` (60주제) | 60 | **CS 밖(특례: database 영역 강결합)** | SQL은 DB 이론의 표면이지만 이 노트들은 방언·문법 단위("LATERAL join", "RETURNING")라 레퍼런스 성격. database 영역은 원리(격리·인덱스·옵티마이저)만 | database/02·04·05·13·19·20·21·22 가 `sql/syntax/` 해당 번호를 실습 부록으로 링크 |
| `foundations/web-api/` (39주제) | 118파일 | **CS 밖** | **호스트(브라우저) API 레퍼런스** — `querySelector`·`dataset`·`ResizeObserver` 사용법. README 스스로 "언어가 아니라 플랫폼"이라 규정. 원리(렌더링 파이프라인·이벤트 루프·출처 모델)만 web-platform 영역으로 | web-platform/02 ↔ `08·09·10`, /03 ↔ `38·39`, /04 ↔ `01·15~18·20`, /05 ↔ `25~30`, security/20 ↔ `28·29`, network/38 ↔ `32·33` |
| `foundations/python-basics` | 1편 | **CS 밖** | 파이썬 문법 노트 — `reference/languages/python/` 로 | — |

권고 최상위 구조:

```text
study-note/
├── cs/            ← 이 커리큘럼 18개 영역 (원리 · 장애 · 자료구조 연결)
└── reference/     ← 버전 종속 레퍼런스 (languages/ · web-platform-api/)
```

### 19.3 `systems/` (22개 폴더)

| 기존 | 판정 | 새 위치 |
|---|---|---|
| `systems/Hysteresis` | 이동 | reliability/16-hysteresis-and-flapping |
| `systems/architecture-styles` | 이동 | software-design/15-architecture-styles |
| `systems/call-stack` | 병합 | architecture/09-calling-convention-and-stack-frame (+ memory-management 스택 프레임 절) |
| `systems/clickhouse-mergetree` | 이동 | database/37-clickhouse-mergetree |
| `systems/event-sourcing` | 병합 | distributed/27-event-sourcing (+ ops-patterns/16) |
| `systems/kafka-consumer-failure` | 이동 | distributed/26-consumer-failure-handling |
| `systems/kafka-why-fast` | 이동 | distributed/25-kafka-internals (연결: os/14·30) |
| `systems/lsm-tree` | 이동 | database/10-lsm-storage-engine (자료구조 관점은 data-structure/24 — 중복 절 정리) |
| `systems/multi-tenancy` | 이동 | software-design/19-multi-tenancy |
| `systems/nand-flash` | 이동 | architecture/18-nand-flash-ftl |
| `systems/orchestration-choreography` | 이동 | distributed/23-orchestration-vs-choreography |
| `systems/outbox-vs-dispatch-log` | 이동 | distributed/22-outbox-vs-dispatch-log |
| `systems/partitioning-vs-sharding` | 이동 | database/30-partitioning-and-sharding |
| `systems/postgres-rls` | 이동 | database/35-row-level-security |
| `systems/resp-protocol` | 이동 | network/24-application-protocol-framing (RESP를 프레이밍 사례로) |
| `systems/semaphore` | 이동 | os/18-semaphores |
| `systems/server-design` (README + 11편 컬렉션) | **분할** | 01 → reliability/20 · math/15(Little 절) / 02 → network/39 · reliability/14 / 03 → database/29 · 30 · domain-modeling/17(CQRS) / 04 → database/38 / 05 → reliability/01 · 28 / 06 → reliability/06 · 11 (+ 07·08·09 패턴 연결) / 07 → distributed/24 / 08 → reliability/27 · 24 · database/34 / 09 → reliability/02 · 21 / 10 → reliability/33(역색인) / 11 → reliability/32 / README → reliability 영역 index |
| `systems/storage-media-workload` | 이동 | architecture/17-storage-media-workload |
| `systems/straggler` | 이동 | reliability/17-tail-latency-and-stragglers |
| `systems/striping` | 이동 | distributed/13-chain-replication-and-striping |
| `systems/thrashing` | 이동 | data-structure/41-resize-thrashing (OS 스래싱 os/12와 용어 대비 링크) |
| `systems/timeseries-resolution-tiers` | 병합 | database/36-timeseries-resolution-tiers (+ ops-patterns/17) |

→ `systems/` 는 **폴더 해체**. "시스템"은 영역 이름으로 너무 넓어 새 트리에서 architecture·os·database·distributed·reliability로 흩어진다.

### 19.4 `engineering/` (8개 폴더)

| 기존 | 판정 | 새 위치 |
|---|---|---|
| `engineering/agile-and-squad` | 이동 | engineering-practice/01-lifecycle-and-agile |
| `engineering/clean-code` | 이동 | software-design/04-clean-code |
| `engineering/data-access` (README + jpa + spring-data-jdbc + comparison) | 병합 | database/33-orm-and-n-plus-one (프레임워크 고유 API 세부는 `reference/` 후보) |
| `engineering/design-patterns-gof` | 이동 | software-design/13-design-patterns-gof |
| `engineering/development-standards` (4축 + index + README) | 분할 | engineering-practice/12 (quality) · 13 (security) · 14 (operational) · 15 (legal, provisions.md 포함) |
| `engineering/engineering-axes` (README + 7축) | 병합 | software-design/20-quality-attributes-and-tradeoffs (7축 = 가용성·동시성·유지보수성·성능·확장성·시스템 설계·UX는 서머리 절로) |
| `engineering/failure-point-checklist` | 이동 | reliability/05-failure-point-checklist |
| `engineering/solid-principles` | 이동 | software-design/11-solid |

### 19.5 `ops-patterns/` (01~19 + 3개 개념 폴더)

| 기존 | 판정 | 새 위치 |
|---|---|---|
| `01-retry-backoff` | 이동 | reliability/07 |
| `02-circuit-breaker` | 이동 | reliability/08 |
| `03-bulkhead` | 이동 | reliability/09 |
| `04-rate-limiter` | 이동 | reliability/10 |
| `05-backpressure` | 이동 | reliability/11 |
| `06-idempotency-store` | 이동 | reliability/12 |
| `07-outbox` | 이동 | distributed/21 |
| `08-saga` | 이동 | distributed/20 |
| `09-stampede` | 이동 | reliability/13 |
| `10-scheduler` | 이동 | reliability/15 |
| `11-distributed-lock` | 이동 | distributed/17 |
| `12-leader-election` | 이동 | distributed/14 |
| `13-snowflake` | 이동 | distributed/18 |
| `14-logical-clock` | 이동 | distributed/06 |
| `15-crdt` | 이동 | distributed/12 |
| `16-event-sourcing` | 병합 | distributed/27 (+ systems/event-sourcing) |
| `17-timeseries` | 병합 | database/36 (+ systems/timeseries-resolution-tiers) |
| `18-blockchain` | 이동 | distributed/29 |
| `19-graceful-shutdown` | 이동 | reliability/14 |
| `deadline-propagation` | 이동 | reliability/06 |
| `failure-at-scale` | 이동 + 분할 | reliability/03 (본문) · distributed/03 (양상 1 부분 실패 절 연결) |
| `failure-modes` | 이동 | reliability/04 (F-01~08은 database/25·os/15에서 역링크) |

→ `ops-patterns/` 는 **reliability(복원력)와 distributed(조정·데이터 흐름)로 양분**. myway 구현 챕터 번호는 원본 레포 대응을 위해 각 leaf 서머리 머리말에 `원본: ops-patterns/NN` 으로 남긴다.

### 19.6 `data-structure/` · `algorithm/` · `domain-modeling/` · `api-design/`

| 기존 | 판정 | 새 위치 |
|---|---|---|
| `data-structure/01~35` | 유지(번호·폴더명 그대로) | data-structure/01~35 |
| `data-structure/lsm-merge-model` | 이동(번호 부여) | data-structure/40-lsm-merge-model |
| `algorithm/01~30` | 유지(번호·폴더명 그대로) | algorithm/01~30 |
| `domain-modeling/domain-vs-application-logic` | 이동 | domain-modeling/01 |
| `domain-modeling/pojo` | 이동 | domain-modeling/02 |
| `domain-modeling/basic` (30편) | 유지(컬렉션) | domain-modeling/18 이 가리킴 |
| `domain-modeling/advanced` (30편) | 유지(컬렉션) | domain-modeling/19 가 가리킴 |
| `api-design/01~06` | 이동(번호만 16~21로) | api-design/16-case-order-point ~ 21-case-refund |

---

## 20. leaf 통계

> 집계 기준: 이 문서 §1~§18 표의 leaf 행(`| NN-slug |`)을 스크립트로 셌다. **기존** = `기존` 칸이 기존 노트 경로로 시작(이동·분할·병합·유지 포함), **신규** = `신규`로 시작(`(연결: …)` 만 있는 것 포함). 중복 slug 0, 등급 오기 0.

| # | 영역 | leaf | 신규 | 기존 | 필수 | 권장 | 심화 |
|---|---|---|---|---|---|---|---|
| 1 | CS 수학 | 17 | 16 | 1 | 10 | 7 | 0 |
| 2 | 자료구조 | 43 | 5 | 38 | 16 | 16 | 11 |
| 3 | 알고리즘 | 40 | 8 | 32 | 17 | 15 | 8 |
| 4 | 컴퓨터 구조 | 22 | 11 | 11 | 13 | 5 | 4 |
| 5 | 운영체제 | 37 | 29 | 8 | 28 | 8 | 1 |
| 6 | 프로그래밍 언어·컴파일러 | 21 | 11 | 10 | 11 | 9 | 1 |
| 7 | 네트워크 | 45 | 43 | 2 | 32 | 13 | 0 |
| 8 | 보안 | 28 | 22 | 6 | 18 | 10 | 0 |
| 9 | 데이터베이스 | 40 | 31 | 9 | 24 | 12 | 4 |
| 10 | 분산 시스템 | 32 | 16 | 16 | 17 | 10 | 5 |
| 11 | 운영·신뢰성 | 34 | 10 | 24 | 21 | 13 | 0 |
| 12 | 소프트웨어 설계 | 24 | 17 | 7 | 14 | 10 | 0 |
| 13 | 도메인 모델링 | 21 | 16 | 5 | 11 | 10 | 0 |
| 14 | 테스트 | 19 | 19 | 0 | 8 | 10 | 1 |
| 15 | API 설계 | 23 | 17 | 6 | 9 | 14 | 0 |
| 16 | 웹 플랫폼 | 13 | 13 | 0 | 6 | 7 | 0 |
| 17 | 엔지니어링 실천 | 18 | 12 | 6 | 6 | 11 | 1 |
| 18 | 데이터 분석·통계 | 28 | 28 | 0 | 17 | 9 | 2 |
| | **합계** | **505** | **324** | **181** | **278** | **189** | **38** |

- 영역마다 역색인 1 + 실사건 1 = **36 leaf**가 마감용이다(역색인은 전부 필수, 실사건은 전부 권장).
- **연습 컬렉션은 leaf 1개로 셌다**: domain-modeling basic 30편·advanced 30편(각 leaf 18·19), server-design 11편은 분할해 여러 leaf에 분산.
- **CS 밖(reference/)으로 뺀 규모**: languages 2,023파일 + web-api 118파일 + python-basics 1편 — leaf 수에 포함하지 않았다.
- 필수만 따라가면 278 leaf. 신규 필수는 영역별로 네트워크(30)·OS(20)·DB(19)·데이터 분석(17)·보안(15) 순으로 많다 — roadmap.md §11 착수 순서(네트워크 → OS → DB → …)와 맞는다.
- `[?]` 표기: 문서 전체 129개(범례·출처 설명 포함) 중 **leaf 행 안 113개(103행)** — 주로 장 번호 미확인 교재(P&H·Dragon Book·TAPL·Sipser·GC Handbook·Kohavi·SRE 일부 장·Stevens 15·16장)와 수치·세부 사건 기록.

---

## 21. 출처

### 이번 작업에서 목차·구성을 직접 확인한 것

- **CS2023 Knowledge Areas** (17 KA — AL·AR·AI·DM·FPL·GIT·HCI·MSF·NC·OS·PDC·SEC·SEP·SDF·SE·SPD·SF): https://csed.acm.org/knowledge-areas/
- **OSTEP** 장 목록 1~57(가상화 4~24·동시성 26~33·영속성 36~50·보안 53~57): https://pages.cs.wisc.edu/~remzi/OSTEP/
- **CMU 15-445/645 Fall 2024** 강의 L0~L25: https://15445.courses.cs.cmu.edu/fall2024/schedule.html
- **MIT 6.5840 Spring 2026** 강의 1~22와 논문: https://pdos.csail.mit.edu/6.824/schedule.html
- **DDIA 1판** 1~12장 제목: https://github.com/keyvanakbary/learning-notes/blob/master/books/designing-data-intensive-applications.md (2판 2026-03 출간 — 장 구성은 미확인 `[?]`: https://martin.kleppmann.com/2026/03/24/designing-data-intensive-applications-2e.html)
- **CS:APP 3판** 7~12장(링킹·예외적 제어흐름·가상 메모리·시스템 I/O·네트워크 프로그래밍·동시성) 및 전체 주제 순서: https://csapp.cs.cmu.edu/ · https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf
- **SWEBOK v4** 18 KA(Architecture·Operations·Security 신설): https://www.computer.org/education/bodies-of-knowledge/software-engineering
- **OpenIntro Statistics 4판** 1~9장 절 구성: https://www.openintro.org/book/os/
- **Kurose & Ross 9판** 1~5장 제목(6~8장은 8판 구성 기준): https://gaia.cs.umass.edu/kurose_ross/index.php

### 1차 리서치(roadmap.md)에서 이어받은 것

roadmap.md §출처 전체 — HPBN, Beej, packagecloud 커널 네트워크 스택, what-happens-when, Cloudflare 블로그(SYN·TCP 소켓·IP 단편화·윤초), Bernat TIME_WAIT, AWS NAT GW, Let's Encrypt OCSP 종료, CA/B SC-081, badssl, LWN fsyncgate, Mars Pathfinder, GitHub 2018, metastable failure, DDD Reference, Canon TDD, Mocks Aren't Stubs, SWE@G 13장, DORA, 면접 레포 4종, OpenIntro, Think Stats, Wilke.

### 약어

| 약어 | 원서 |
|---|---|
| CLRS | Cormen·Leiserson·Rivest·Stein 『Introduction to Algorithms』 3판 |
| CS:APP | Bryant·O'Hallaron 『Computer Systems: A Programmer's Perspective』 3판 |
| OSTEP | Arpaci-Dusseau 『Operating Systems: Three Easy Pieces』 |
| K&R | Kurose·Ross 『Computer Networking: A Top-Down Approach』 8판 |
| Stevens | Fall·Stevens 『TCP/IP Illustrated, Vol. 1』 2판 |
| HPBN | Grigorik 『High Performance Browser Networking』 (hpbn.co) |
| L# | CMU 15-445 Fall 2024 강의 번호 |
| 6.5840 L# | MIT 6.5840 Spring 2026 강의 번호 |
| DDIA | Kleppmann 『Designing Data-Intensive Applications』 1판 |
| MCS | Lehman·Leighton·Meyer 『Mathematics for Computer Science』 (MIT 6.042) |
| P&H | Patterson·Hennessy 『Computer Organization and Design』 |
| APOSD | Ousterhout 『A Philosophy of Software Design』 2판 |
| SWE@G | Winters·Manshreck·Wright 『Software Engineering at Google』 |
| SRE | Beyer 외 『Site Reliability Engineering』 (Google) |
| GoF | Gamma 외 『Design Patterns』 |

### 다음 단계에서 재확인할 것

- 모든 `[?]` — 해당 leaf 노트 작성 착수 시 원문 대조.
- DDIA 2판 장 구성 확인 후 database·distributed의 📚 칸을 2판 기준으로 갱신할지 결정.
- 등급(필수/권장/심화)은 교수 판단 초안 — 사이트 배포 후 검수 과정에서 조정.

