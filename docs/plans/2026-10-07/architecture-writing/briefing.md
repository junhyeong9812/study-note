# 집필 브리핑 — 커리큘럼 leaf 새 노트 (컴퓨터 구조, 2026-10-07)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §4 컴퓨터 구조 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §4 머리 문단(비트 → 게이트 → CPU → 메모리 계층 → 저장장치, 백엔드가 만나는 장애)도 읽는다.
- **이 영역의 목표**: 백엔드 개발자가 "하드웨어·표현이 어긋나면 운영에서 무엇이 보이는지"로 배운다. 각 편은 ⚠ 칸의 운영 증상에서 출발해 비트·회로·캐시 수준의 원인으로 내려갔다가, 코드로 돌아온다.
- **원고(보강 10편 — 읽기만)**: 01·03·04·06 ← `cs/foundations/data-representation` · 07·08·09 ← `cs/foundations/hardware-basics` · 10 ← `cs/systems/call-stack`(+`cs/foundations/memory-management`) · 11 ← `cs/foundations/memory-management` · 16 ← `cs/systems/storage-media-workload`. 17 nand-flash-ftl은 범위 밖(`cs/systems/nand-flash`로 링크).
- **겹치는 기존 노트(먼저 읽고 링크, 되풀이하지 않는다)**: `cs/math/{11-modular-arithmetic,15-numerical-stability,02-induction-and-invariants,13-linear-algebra-essentials,10-queueing-and-littles-law}`, `cs/os/`(스케줄러·가상 메모리·인터럽트·I/O·NUMA — `ls`로 찾기), `cs/security/24-memory-safety-exploits`, `cs/network/`(바이트 순서·NIC·인터럽트), `cs/database/`(저장·버퍼·I/O), `cs/data-structure/25-ring-buffer`·`29-concurrent-data-structures`, `cs/algorithm/{01-algorithm-basics,42-alg-symptom-index,43-alg-incidents}`(이진 탐색 오버플로), `cs/systems/nand-flash`. 자료구조·알고리즘은 커리큘럼 번호 ≠ 폴더 번호(대응표 `cs/data-structure/curriculum.md`·`cs/algorithm/curriculum.md`).
- **근거와 열 수 있는 1차 출처(검색 한도 대비 — 주소를 알고 curl/WebFetch로 직접 연다)**:
  - CS:APP 3판 목차·저자 자료: https://csapp.cs.cmu.edu/3e/ (장·절 번호는 목차에서 확인)
  - OSTEP 장 PDF: https://pages.cs.wisc.edu/~remzi/OSTEP/ (36 I/O devices `file-devices.pdf`, 37 HDD `file-disks.pdf`, 44 SSD `file-ssd.pdf`)
  - Goldberg 1991 floating-point: https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html
  - Unicode: UAX #15 https://www.unicode.org/reports/tr15/ · UAX #29 https://www.unicode.org/reports/tr29/ · RFC 3629 https://www.rfc-editor.org/rfc/rfc3629.txt · MySQL utf8mb4 문서 https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html
  - JLS SE21 https://docs.oracle.com/javase/specs/jls/se21/html/ (§4.2 정수·부동소수, §5.1.3 좁히기, §15.17·§15.18, §17 메모리 모델), Java API https://docs.oracle.com/en/java/javase/21/docs/api/ (`Math.addExact`, `BigDecimal`, `Double.compare`, `String`·`Character`·`BreakIterator`·`Normalizer`, `VarHandle`), OpenJDK 소스 raw https://raw.githubusercontent.com/openjdk/jdk21u/master/...
  - JSR-133 Cookbook·FAQ: https://gee.cs.oswego.edu/dl/jmm/cookbook.html · https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html · DCL 선언문 https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
  - Drepper 2007: https://people.freebsd.org/~lstewart/articles/cpumemory.pdf
  - 지연 숫자: https://gist.github.com/jboner/2841832 (Dean 원 슬라이드는 2차 정리 — 출처 성격을 밝힌다)
  - Linux 문서: https://docs.kernel.org/ (예: `admin-guide/hw-vuln/`, `core-api/`, `/proc/interrupts` 설명은 `filesystems/proc.html`), y2038 https://docs.kernel.org/ 검색 대신 `include/linux/time64.h`·LWN 글 주소를 아는 범위에서
  - Spectre/Meltdown: https://spectreattack.com/spectre.pdf · https://meltdownattack.com/meltdown.pdf · 커널 hw-vuln 문서
  - 사고: GAO/IMTEC-92-26 https://www.gao.gov/products/imtec-92-26 (PDF, 접근 거부 시 Internet Archive 사본) · Ariane 501 보고서 https://esamultimedia.esa.int/docs/esa-x-1819eng.pdf (또는 보관본) · Intel FDIV 백서(Intel 사이트·보관본)
  - P&H는 열 수 있는 목차가 없으면 장 번호 `[?]`.
- WebSearch는 한도 소진일 수 있다 — 위 주소를 먼저 쓰고, 못 열면 Internet Archive(`https://web.archive.org/web/2024/<URL>`)를 시도한다. 그래도 못 열면 `[?]`. **기억으로 쓴 절·정리·페이지 번호에는 반드시 `[?]`**를 붙인다.

## 2. 출력 — `cs/architecture/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-07 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# architecture/<NN-slug> — <한 줄 제목> — 정리 (힌트)

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
- **동작·원리**: 중심. ASCII 그림 먼저(비트 배치, 2의 보수 원, IEEE 754 필드, UTF-8 바이트 틀, 메모리 덤프·패딩, 게이트·가산기, 클록 타이밍, 스택 프레임, 파이프라인 단계, 캐시 주소 분해(태그·인덱스·오프셋), MESI 상태, 지연 자릿수 막대, DMA 링, 디스크 헤드, NUMA 노드), 글은 그 해설, 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 이 주제가 쓰는·쓰이는 구조·알고리즘(🔧 칸)을 적고 기존 노트로 링크(실제 폴더 — `../../algorithm/12-hash-functions/2-summary.md` 등).
- **적용 — 풀어나가는 법**: 실무 순서: 증상 → 표현·하드웨어 원인 → 코드·명령으로 확인. 코드는 Java 21 기본, 비트·메모리 배치·어셈블리 수준은 C(gcc)·`objdump`. 진단 명령(`file`, `objdump -d`, `xxd`, `iconv`, `lscpu`, `numactl -H`, `/proc/interrupts`, `jcmd`) 출력 읽기.
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(예외·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 기존 myway 노트는 실제 폴더, 아직 없는 같은 영역 주제는 `../curriculum.md`, 다른 영역은 실제 경로 확인 — 특히 `../../math/…`·`../../os/…`·`../../security/…`·`../../network/…`·`../../database/…`·`../../data-structure/…`(대응표), 원고 `../../foundations/…`·`../../systems/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

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
- **하드웨어·런타임 한정**: "x86-64(i7-13700HX)에서", "ARM64에서는", "IEEE 754 binary64 기본 반올림", "JMM(JLS §17)상", "Linux 커널 문서 기준". 같은 현상이 아키텍처·컴파일러·JIT마다 다를 수 있으면 조건을 붙인다(예: 비정렬 접근은 x86에서 허용, 일부 ARM에서 SIGBUS).
- **측정은 측정으로**: 캐시·분기 예측·false sharing 효과는 크기를 바꿔 가며 비율로 보이고, 하이브리드 CPU(P/E 코어)·`--cpus=2`·JIT 영향을 적고 여러 번 돌린 범위를 쓴다. 하드웨어 카운터는 못 쓴다(perf 불가) — "캐시 미스 때문"은 실험 설계와 문헌으로 뒷받침하고 해석이라고 표시.
- **표준 요구 vs 구현 동작 구분**: IEEE 754 요구 vs Java/C 동작, Unicode 표준 vs 라이브러리 기본값, JMM 보장 vs x86 TSO 실제 동작.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트 이어받기 (보강 10편)

- 원고는 **수정하지 않는다.** 담당 주제를 다룬 절을 먼저 읽고, 이미 설명한 것은 "기초는 원고 §N" 링크 + 한두 줄 요약. 빈 곳(⚠ 장애, 실험, 적용, 질문·정답)을 채운다. 원고에 틀린 내용이 있으면 새 leaf에 바르게 쓰고 `참고: 원고 §N의 "…"는 …(근거)` 한 줄. 알려진 원고 오류: `foundations/data-representation` 98행 epsilon 정의("1.0+ε != 1.0인 가장 작은 값" — 반 ulp 근처 값도 성립, math/15 정합 패스 보고) → 03 담당이 바르게 쓰고 참고 줄.

## 5. 실험 근거 (명세 I7 — 필수)

- 편마다 실행으로 보일 수 있는 핵심 주장 1개 이상(종합 22·23 선택). 예:
  - 01·02: C `-1 > 0u`(경고 포함), 부호 확장, Java `int` 오버플로·`Math.addExact` 예외·`(short)` 좁히기, `size_t` 언더플로로 거대 크기(할당은 실제로 하지 않고 값만 출력).
  - 03: `0.1+0.2`, `NaN != NaN`·`Double.compare`·`TreeSet`에 NaN, `-0.0`, `double` 금액 합 vs `BigDecimal`, ulp(`Math.ulp`).
  - 04·05: 같은 문자열의 UTF-8/UTF-16 바이트(`xxd`), 모지바케 재현(`iconv`·Java 디코딩), 서로게이트 중간 절단, NFC/NFD 파일명 비교(`Normalizer`), 4바이트 문자 길이, 그래핌 vs 코드포인트 vs UTF-16 길이(`BreakIterator`), 터키어 로캘 `toUpperCase`.
  - 06: 엔디안 덤프(`ByteBuffer.order`·C `memcpy`), 구조체 패딩(`offsetof`·`sizeof`), `htons` 누락으로 뒤집힌 포트.
  - 07·08: 리플 캐리 가산기·룩어헤드 시뮬레이션(게이트 지연 단계 수), 유한 상태 기계 코드.
  - 09·10: `file`로 ELF 아키텍처 확인, `objdump -d`로 명령어 인코딩·함수 프롤로그, 재귀 깊이와 프레임 크기, `-fno-omit-frame-pointer`.
  - 11·12·13: 행/열 순회·연결 리스트 추적, stride별 시간(충돌), false sharing 카운터(패딩 유무, 스레드 2개), 지연 자릿수(L1 접근 vs 메모리 vs syscall vs 로컬 루프백 왕복).
  - 14: volatile 없는 플래그 대기(JIT가 끝나지 않는 루프 — 시간 제한), `AtomicInteger` vs 일반 증가 유실, DCL 문서 근거.
  - 15·16: `/proc/interrupts` 읽기, 순차 vs 랜덤 읽기(작은 임시 파일, 페이지 캐시 영향 명시).
  - 18·19: 정렬 vs 비정렬 배열의 조건 합(분기 예측), 브랜치리스 판 비교 / 19는 **`/sys/devices/system/cpu/vulnerabilities/*` 읽기와 문서까지**(공격 재현 금지).
  - 20·21: `lscpu`·`numactl -H` 출력 해석, 스레드 수별 처리량, `-O3`(자동 벡터화) vs `-O0`·`-fopt-info-vec`.
- 노트에 싣는 것: 실험 코드 핵심, 환경(i7-13700HX·커널·gcc·JDK 버전), **실제 출력**, 관찰과 해석. 비결정 값은 여러 번 돌린 범위.
- 실험으로 보일 수 없는 주장은 1차 출처로 대신하고 그 사실을 적는다. packet에 실험 목록.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-arch-w<NN>-*`, `--rm`, 가능하면 `--network none`, `--cpus=2` 이하. **이미 있는 이미지만**(`eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 끝나면 `docker ps -a --filter name=sn-arch-w<NN>`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만).
- **호스트 도구**: gcc·objdump·file·iconv·xxd·lscpu·numactl·python3(표준 라이브러리만) 사용 가능. **sudo·커널 설정 변경 금지**(perf는 `perf_event_paranoid=4`라 쓰지 않는다). **새 패키지 설치 금지**(pip·apt·npm install 포함). 호스트에서 돌리는 실험도 수십 초 이내·메모리 1GB 이하.
- **부하 상한**: 실행 수십 초 이내, 호스트를 포화시키는 실험·무한 루프 재현(JDK7 HashMap 동시 resize 등)은 시간 제한(`timeout 10`)을 걸고, 재현 불가하면 원 보고·소스 근거로 대신하고 밝힌다. 측정 수치는 이 제한 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/arch/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다.
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다. 연락처 User-Agent를 요구하는 사이트는 열지 말고 다른 출처나 `[?]`.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지 — 다른 워커 실험을 죽인 사고, 10-04).
- **금지**: `sn-math-*`·`sn-sec-*`·`payment-*`·`jun-bank-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·이미지는 건드리지 않는다.

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
