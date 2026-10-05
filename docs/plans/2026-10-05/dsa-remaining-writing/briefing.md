# 집필 브리핑 — 커리큘럼 leaf 새 노트 (자료구조·알고리즘 잔여, 2026-10-05)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §2 자료구조·§3 알고리즘 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧 쓰이는 곳·📚 칸은 **모두 다뤄야 할 요구사항**이다. §2·§3 머리 문단(번호 = 권장 학습 순서, 근거 CLRS 3판·Sedgewick 4판·원논문)도 읽는다.
- **번호 주의**: 커리큘럼 번호 ≠ 기존 myway 폴더 번호. 생성 문서 `cs/data-structure/curriculum.md`·`cs/algorithm/curriculum.md`의 "노트" 칸이 대응표다(예: 커리큘럼 alg 04 binary-search = 폴더 `algorithm/06-binary-search`, ds 10 heap = `data-structure/07-heap`). 선행·관련 링크는 **실제 폴더 경로**로(`ls`로 확인). 새 leaf(이번 21편)는 커리큘럼 번호 폴더 `cs/<area>/NN-slug/`.
- **원본(보강 3편)**: ds 01 ← `cs/foundations/data-structures-basics` · alg 01 ← `cs/foundations/algorithm-basics` · ds 19 ← `cs/data-structure/lsm-merge-model` — **읽기만**. 기존 myway 노트(`data-structure/01~35`·`algorithm/01~30`)도 읽기만(옛 형식이라 check_new FAIL — 정상, 고치지 않는다).
- **근거**: CLRS 3판(장·절 번호), Sedgewick 『Algorithms』 4판(algs4.cs.princeton.edu), Knuth TAOCP 3권, Sipser 『Introduction to the Theory of Computation』, 원논문(Varghese–Lauck 1987 "Hashed and Hierarchical Timing Wheels", Michael–Scott 1996 PODC, Huffman 1952, Ziv–Lempel 1977, Aumasson–Bernstein 2012 SipHash, Carter–Wegman 1979, Duda 2013 ANS, O'Neil 외 1996 LSM-tree, Turing 1936, Cook 1971·Karp 1972), RFC 1951·1952·8878·7932, LZ4 frame/block 포맷 문서(github.com/lz4/lz4/doc), OpenJDK 소스(github.com/openjdk/jdk — `TimSort.java`·`ComparableTimSort`·`HashMap.java`·`ConcurrentHashMap.java`·`ArrayBlockingQueue`·`ConcurrentLinkedQueue`·`DelayQueue`·`ScheduledThreadPoolExecutor`·`Arrays.binarySearch`), Netty `HashedWheelTimer`, Linux `kernel/time/timer.c` 주석·LWN, Kafka purgatory 타이밍 휠 글, 28C3 "Efficient Denial of Service Attacks on Web Application Platforms"(Klink–Wälde 2011)·oCERT-2011-003, JEP 180(HashMap 트리화), Python PEP 456, Bloch 2006 "Nearly All Binary Searches and Mergesorts are Broken", Stack Overflow 2016-07-20 사후 보고(stackstatus), Cloudflare 2019-07-02 사후 보고, de Gouw 외 2015 TimSort 버그(CAV). 책 본문을 못 열면 목차·출판사 발췌로 확인한 범위만 단정, 나머지는 장 단위·`[?]`.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/<area>/<NN-slug>/`의 4파일 (area = data-structure 또는 algorithm)

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-05 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# <area>/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(메모리 배치·포인터, 링 버퍼 head/tail, 타이머 휠 슬롯·계층, CAS 경합 시간축, LSM 레벨/티어, 재귀 호출 스택, 병합 트리, 허프만 트리, LZ77 슬라이딩 윈도, 환원 화살표, 대각선 논법 표), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 이 영역에서는 "이 주제가 쓰는 하위 구조 + 이 주제를 쓰는 곳(🔧)"을 적는다. 기존 노트 링크는 실제 폴더로(`../07-heap/2-summary.md` 등 — 같은 영역, 다른 영역은 `../../database/…`).
- **적용 — 풀어나가는 법**: 실무·코테 순서. 코드는 Java 21 기본(JS·TS 가능), Java로 어려운 저수준(메모리 배치·원자 연산 세부)은 C. 진단(스택 트레이스·`jcmd`·`jstack`·프로파일 출력 읽기).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(예외·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 기존 myway 노트는 실제 폴더, 아직 없는 같은 영역 주제는 `../curriculum.md`, 다른 영역은 실제 경로 확인 — 특히 `../../database/…`(LSM·B-tree·정렬·해시 조인), `../../network/…`(압축 39·43·44), `../../os/…`(스레드·메모리), `../../reliability/…`, `../../security/…`(있는 것만), `../../engineering-practice/20-practice-incidents`(Cloudflare·Knight), 원본 `../../foundations/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄을 덧붙인다(근거 있는 오해만, 없으면 생략 — 새 절을 만들지 않는다, 2026-10-05 합의).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java 21(기본)·JS·TS, Java로 어려운 저수준은 C. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M. 다 쓰고 스스로 대조.
- **제품·버전 한정**: "OpenJDK 21 기준", "CPython 3.12에서는", "zstd 1.5.x 기본 레벨 3". 이론(점근 복잡도·정리) vs 구현 상수(캐시·분기 예측) vs 측정을 구분하고, 정의가 갈리는 것(빅오를 상한 vs 꽉 낀 한계로 쓰는 관행, "평균" = 입력 분포 평균 vs 무작위 알고리즘 기대값, 분할 상환 vs 평균, lock-free vs wait-free, 레벨/티어 정의(RocksDB vs 논문))은 출처별로 나눠 쓴다.
- **측정은 측정으로**: 마이크로벤치는 JIT 워밍업·GC·`--cpus` 제한 영향을 적고 여러 번 돌린 범위를 쓴다. "N배 빠르다"는 그 환경·크기 한정. 점근 차이를 보일 때는 크기를 키우며 비율(두 배 크기 → 시간 몇 배)로 보인다.
- **구현 동작은 소스로**: 예) Java `HashMap` 트리화 임계(TREEIFY_THRESHOLD 8·MIN_TREEIFY_CAPACITY 64), `Collections.sort`/`List.sort`의 TimSort와 `Arrays.sort(int[])`의 Dual-Pivot Quicksort, `String.hashCode`, Python 해시 랜덤화(PYTHONHASHSEED, 3.4부터 SipHash — PEP 456), 기본 스레드 스택 크기(`-Xss`) — 문서·소스·실행으로 확인.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트 이어받기 (보강 3편 담당자)

- 원본은 **수정하지 않는다.** 담당 주제의 원본: §1 원본 목록.
- 원본을 먼저 **읽는다.** 이미 설명한 것은 길게 되풀이하지 않고 "기초는 원본 §N" 링크 + 한두 줄 요약.
- 빈 곳을 채운다: 커리큘럼 ⚠ 장애, 자료구조, 실험, 적용(코드·진단), 질문·정답.
- 원본에 틀린 내용이 있으면 새 leaf에 올바르게 쓰고 `참고: 원본 §N의 "…"는 …(근거)` 한 줄로 짚는다(인용문 `>`가 아닌 일반 문장).
- ds 19 lsm-merge-model은 기존 `data-structure/24-lsm-tree`·`database/` LSM 노트와 겹치지 않게 "병합 정책(레벨·티어) 트레이드오프"에 집중하고 그쪽을 링크한다.

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험으로 보인다**(종합 4편은 선택). 예:
  - ds 01·02: 같은 `List` 인터페이스 — ArrayList vs LinkedList 중간 삽입·임의 접근·순회 시간(크기를 키우며 비율), `Deque` 구현별 비용. 비용 계약을 문서(Javadoc "constant time" 문구)와 측정으로.
  - ds 25: 링 버퍼 구현(가득 참 판정: 한 칸 비우기 vs 카운트), 덮어쓰기 vs 거부 정책, 2의 거듭제곱 마스크, 생산자/소비자 `ArrayBlockingQueue`.
  - ds 26: 타이머 힙(PriorityQueue) vs 해시 타이머 휠 — 타이머 N개 삽입·취소·틱 비용 측정, 휠 해상도 오차.
  - ds 29: 비동기화 `HashMap` 동시 put 유실, ABA 재현(C11 atomics 또는 Java `AtomicReference` vs `AtomicStampedReference`), 락 vs `ConcurrentLinkedQueue` 처리량(제한 환경 명시).
  - ds 19: 레벨 vs 티어 병합의 쓰기 증폭·읽기 비용 시뮬레이션(시뮬레이션 명시).
  - alg 01·02: 크기 두 배 → 시간 비율로 O(n)·O(n log n)·O(n²) 구분, 분할 상환(ArrayList 증가 시 복사 횟수 합).
  - alg 03: 재귀 깊이 → `StackOverflowError` 깊이(`-Xss` 별), 꼬리 재귀가 Java에서 최적화되지 않음, 반복으로 변환.
  - alg 09: 비교자 계약 위반 → "Comparison method violates its general contract!", 안정 정렬로 다중 키, `Arrays.sort` 원시형 vs 객체.
  - alg 11: 메모리 제한(`-Xmx`)보다 큰 파일 외부 정렬 + k-way 병합(힙) — run 수·병합 패스 수.
  - alg 12: 충돌 유도 키(`"Aa"`/`"BB"` 조합)로 HashMap 성능 — Comparable 키(트리화) vs 비Comparable 키, Python 해시 랜덤화 확인.
  - alg 33·34: 직접 구현한 허프만 부호 길이 vs 엔트로피, gzip/zstd/xz 레벨별 비율·시간(호스트 CLI), 이미 압축된 데이터 재압축, zstd 딕셔너리(`--train`) 소형 레코드. lz4·brotli는 CLI 없음 → 문서·RFC 근거라고 밝힌다(설치 금지).
  - alg 39: 퀵정렬 고정 피벗 vs 무작위 피벗 — 정렬된 입력, 몬테카를로 소수 판정(`BigInteger.isProbablePrime`) 오류 확률.
  - alg 40·41: 실험 대신 작은 환원 코드(3-SAT → 독립 집합 등)나 정지 문제 대각선 논법 코드 스케치 — 실행 가능한 부분만 실행, 나머지는 교재 근거.
  - 종합: 증상 재현 몇 개(CME·이진 탐색 `(lo+hi)/2` 오버플로·정규식 백트래킹 시간 폭증(Java `Pattern`))는 선택.
- 실험 코드는 scratchpad에 둔다(저장소 루트·노트 폴더 금지). 결과 표에는 실제 명령 출력만 싣는다.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(제품·버전), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, OpenJDK 21 temurin --cpus=2, 2026-10-05)`처럼 환경을 적는다. 비결정적 값은 "실행마다 다르다"고 적고 여러 번 돌린 범위를 쓴다.
- **실험으로 보일 수 없는 주장**은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.
- **재부팅 대비**: 실험 코드의 핵심은 노트에 싣는다(/tmp는 재부팅 때 사라진다).

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-dsa-w<NN>-*`, `--rm`, 가능하면 `--network none`, `--cpus=2` 이하. **이미 있는 이미지만**(`eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 끝나면 `docker ps -a --filter name=sn-dsa-w<NN>`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만).
- **호스트 도구**: gcc(C11 atomics 등)·python3·gzip·zstd·xz 사용 가능. **새 패키지 설치 금지**(pip·apt·npm install 포함). 호스트에서 돌리는 실험도 수십 초 이내·메모리 1GB 이하.
- **부하 상한**: 실행 수십 초 이내, 호스트를 포화시키는 실험·무한 루프 재현(JDK7 HashMap 동시 resize 등)은 시간 제한(`timeout 10`)을 걸고, 재현 불가하면 원 보고·소스 근거로 대신하고 밝힌다. 측정 수치는 이 제한 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/dsa/<담당 첫 폴더명>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다.
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다. 연락처 User-Agent를 요구하는 사이트는 열지 말고 다른 출처나 `[?]`.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지 — 다른 워커 실험을 죽인 사고, 10-04).
- **금지**: `sn-ep-*`·`sn-ad-*`·`payment-*`·`jun-bank-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·이미지는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(원고·다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(논문·문서 URL·소스 경로·교재 장)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·토픽·키를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
