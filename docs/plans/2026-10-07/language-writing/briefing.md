# 집필 브리핑 — 커리큘럼 leaf 새 노트 (프로그래밍 언어·컴파일러, 2026-10-07)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/architecture/14-cache-coherence-and-memory-ordering/`, `cs/os/19-deadlock/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §6 언어 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §6 머리 문단(**언어 중립 원리만** — 문법 레퍼런스는 CS 밖)도 읽는다. 예시는 여러 언어를 비교하되(Java·JS/TS·Python·C·Go·Rust), 문법 설명이 아니라 원리를 보이는 데 쓴다.
- **이 영역의 목표**: 백엔드 개발자가 "언어·런타임의 원리가 운영에서 어떤 증상으로 보이는지"로 배운다. 각 편은 ⚠ 칸의 증상(배포 직후 p99 급등·ReDoS CPU 100%·GC 정지·OOM·데이터 레이스·의존성 충돌)에서 출발해 컴파일러·런타임 원리로 내려갔다가, 코드·진단 명령으로 돌아온다.
- **원고(보강 10편 — 읽기만, 분할 이어받기)**: 01·02·03·04 ← `cs/foundations/compiler-pipeline/README.md`(바이트코드·PVM / 어휘 분석 / BNF·파스 트리·AST / 심벌 테이블 절) · 04·06·07·09 ← `cs/foundations/variables-and-memory/README.md`(스코프 / 전달 방식·얕은/깊은 복사 / 람다 / 참조 카운트·GC 절) · 15 ← `cs/foundations/process-thread/README.md`(GIL 절) · 20 ← `languages/c-cpp-csharp.md`(분할) · 21 ← `languages/README.md` 축① + `languages/c-cpp-csharp.md` + `languages/{go,java,kotlin,rust}/언어-특성/`(병합). 원고에서 틀린 내용은 새 leaf에 바르게 쓰고 `참고: 원고 §N의 "…"는 …(근거)` 한 줄.
- **겹치는 기존 노트(먼저 읽고 링크, 되풀이하지 않는다)**: `cs/architecture/{09-isa-and-machine-code,10-calling-convention-and-stack-frame,14-cache-coherence-and-memory-ordering,18-pipelining-and-branch-prediction,21-simd-and-gpu}`(JIT·JMM·벡터화의 하드웨어 쪽), `cs/os/`(스레드·스케줄러·가상 메모리 — ls로), `cs/security/24-memory-safety-exploits`(20과 경계: 공격은 security, 언어 의미론·UB는 여기), `cs/data-structure/`(29 concurrent, 34 dependency-resolver 등 — 대응표 `cs/data-structure/curriculum.md`), `cs/algorithm/`(대응표 `cs/algorithm/curriculum.md`), `cs/distributed/`·`cs/reliability/`(동시성 패턴과 겹치는 곳), 연결 노트 `languages/{java,rust,c}/syntax/*`(커리큘럼 '기존' 칸). **architecture 11·14 등 다른 영역 노트가 language 노트를 "미작성"으로 가리키는 곳은 packet에 보고**(정합 단계에서 링크 교정).
- **근거와 열 수 있는 1차 출처(검색 한도 대비 — 주소를 알고 curl/WebFetch로 직접 연다)**:
  - 교재(Dragon Book·TAPL·GC Handbook·SICP·Sipser·JCIP·POSA2)는 본문을 열 수 없다 — **장 번호는 열 수 있는 목차(출판사·저자 페이지)로 확인될 때만**, 아니면 `[?]`. SICP는 MIT Press 공개 HTML https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/6515/sicp.zip/full-text/book/book.html (절 번호 확인 가능).
  - JLS·JVMS SE21 https://docs.oracle.com/javase/specs/ · Java API https://docs.oracle.com/en/java/javase/21/docs/api/ · `java` 도구 문서 https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html · OpenJDK 소스 raw https://raw.githubusercontent.com/openjdk/jdk21u/master/...
  - JEP: 444(가상 스레드) https://openjdk.org/jeps/444 · 483(AOT 클래스 로딩·링킹) https://openjdk.org/jeps/483 · 그 밖의 JEP는 https://openjdk.org/jeps/<번호>
  - HotSpot GC 튜닝 가이드 https://docs.oracle.com/en/java/javase/21/gctuning/ (G1 절) · JSR-133 FAQ·Cookbook https://www.cs.umd.edu/~pugh/java/memoryModel/ · Manson 외 POPL 2005(저자 사본이 열리면) · DCL 선언문
  - JOL README https://github.com/openjdk/jol · Shipilëv JVM Anatomy Quarks https://shipilev.net/jvm/anatomy-quarks/
  - GraalVM Native Image 문서 https://www.graalvm.org/latest/reference-manual/native-image/ · Spring Boot GraalVM 문서 https://docs.spring.io/spring-boot/reference/packaging/native-image/
  - Cox 2007 "Regular Expression Matching Can Be Simple And Fast" https://swtch.com/~rsc/regexp/regexp1.html · Cox 2018 "Minimal Version Selection" https://research.swtch.com/vgo-mvs · semver https://semver.org/
  - Hoare 1978 CSP(ACM — 열 수 있는 사본이 없으면 서지 `[?]`)
  - Python: GIL 용어집 https://docs.python.org/3/glossary.html#term-global-interpreter-lock · PEP 703 https://peps.python.org/pep-0703/ · 3.13 free-threading 문서
  - LLVM PGO https://llvm.org/docs/HowToBuildWithPGO.html · Clang ThinLTO https://clang.llvm.org/docs/ThinLTO.html · GCC 최적화 옵션(13.3) https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html
  - C 표준 초안 N1570 https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf (부록 J) · CISA 등 "The Case for Memory Safe Roadmaps" 2023 https://www.cisa.gov/resources-tools/resources/case-memory-safe-roadmaps
  - 사고(27): Cloudflare 2017-02-23 Cloudbleed https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/ · Heartbleed CVE-2014-0160 https://nvd.nist.gov/vuln/detail/CVE-2014-0160 · npm left-pad 2016-03 https://blog.npmjs.org/post/141577284765/kik-left-pad-and-npm (못 열면 Internet Archive) · ReDoS 사고 Cloudflare 2019-07-02 https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ (02·26·27 공유)
- WebSearch는 한도 소진일 수 있다 — 위 주소를 먼저 쓰고, 못 열면 Internet Archive. 그래도 못 열면 `[?]`. **기억으로 쓴 절·페이지·연도·버전 번호에는 반드시 `[?]`**.

## 2. 출력 — `cs/language/<NN-slug>/`의 4파일

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
# language/<NN-slug> — <한 줄 제목> — 정리 (힌트)

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
- **동작·원리**: 중심. ASCII 그림 먼저(소스 → 토큰 → AST → IR → 기계어 파이프라인, NFA/DFA 상태 그림, 파스 트리, 스코프 체인, 스택 vs 힙 참조 그래프, 클로저 환경 레코드, vtable, 세대별 힙·삼색 마킹, 객체 헤더 배치, 계층형 컴파일 단계, happens-before 간선, 이벤트 루프·가상 스레드, 의존성 그래프), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 🔧 칸의 구조·알고리즘을 적고 기존 노트로 링크(대응표로 실제 폴더).
- **적용 — 풀어나가는 법**: 실무 순서: 증상(지연·CPU·메모리·예외·빌드 오류) → 언어·런타임 원리 → 코드·진단 명령으로 확인. 코드는 Java 21 기본, 비교가 필요하면 JS/TS(node 22)·Python 3.12·C(gcc 13/clang 18)·Go 1.23. 진단(`-XX:+PrintCompilation`, `-Xlog:gc*`, `jcmd`, `javap -c`, `objdump -d`, `-fsanitize=address,undefined`, `python -X importtime` 등) 출력 읽기.
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(예외·로그·지표·프로파일) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 아직 없는 같은 영역 주제는 `../README.md`, 다른 영역은 실제 경로 확인), 문서 URL·명세 절, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄(근거 있는 오해만).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java 21(기본)·SQL·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건.
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M, 실험 출력과 해석.
- **언어·런타임·버전 한정**: "JDK 21 HotSpot(G1 기본)에서", "CPython 3.12에서", "V8(node 22)에서", "C11 표준상 / gcc 13 -O2 구현에서". 명세 요구(JLS·C 표준·ECMAScript) vs 구현 동작(HotSpot·V8·CPython) vs 관례를 섞지 않는다. 한 언어 결과를 "언어 일반"으로 쓰지 않는다.
- **JIT·GC 측정은 측정으로**: 워밍업·실행 횟수·힙 크기·`--cpus=2`를 적고 여러 번 돌린 범위를 쓴다. 원인(인라이닝·탈출 분석·GC 종류)은 로그(`-XX:+PrintCompilation`·`-Xlog:gc`)로 뒷받침하고, 못 하면 "해석".
- **UB 서술**: C에서 UB인 것을 "결과는 X"로 쓰지 않는다 — "이 컴파일러·옵션에서 관찰된 결과"로 한정.
- **사고 보고서의 날짜·수치는 원문 그대로**, 해석은 "해석".

## 4. 원고 이어받기 (보강 10편)

- 원고는 **수정하지 않는다.** 담당 주제를 다룬 절을 먼저 읽고, 이미 설명한 것은 "기초는 원고 §N" 링크 + 한두 줄 요약. 빈 곳(⚠ 장애, 실험, 적용, 질문·정답)을 채운다. 분할 원고(compiler-pipeline·variables-and-memory)는 담당 절만 이어받고, 다른 편이 맡는 절은 그 편으로 링크한다. 21은 여러 원고를 병합한다(원고 간 모순이 있으면 원문 근거로 판정).

## 5. 실험 근거 (명세 I7 — 필수)

- 편마다 실행으로 보일 수 있는 핵심 주장 1개 이상(종합 26·27 선택). 예:
  - 01·23: `-XX:+PrintCompilation`으로 계층 단계(0·1·2·3·4) 전이, 워밍업 전후 지연, `-Xint`·`-XX:TieredStopAtLevel=1` 비교, 역최적화(`made not entrant`).
  - 02: Java `Pattern`·Python `re`의 `(a+)+$` 백트래킹 시간 증가(입력 길이별, `timeout` 필수) vs 선형 엔진 개념(Go `regexp`는 RE2 계열 — golang:1.23-alpine로 같은 패턴), NFA→DFA 작은 구현.
  - 03: 재귀 하강 파서 + 깊은 중첩 입력에서 `StackOverflowError`, 두 파서의 해석 차이(Content-Length/Transfer-Encoding은 원리 설명만 — 공격 재현 금지).
  - 04·07: JS `var` vs `let` 루프 클로저(node), Java 람다의 effectively final, 스코프 체인 모형.
  - 05: 타입 추론(단일화) 작은 구현, Java 제네릭 소거(`javap`), TS 구조적 타입.
  - 06: 값/참조 전달·얕은/깊은 복사 결과 비교(Java·JS·Python).
  - 08: 예외 vs 결과 타입 비용·흐름, 체크 예외 삼킴.
  - 09·10·11: 참조 카운트 순환 누수(Python `gc.disable()` + 순환), `-Xlog:gc*`로 G1 정지·세대, 힙 크기별 GC 로그 읽기.
  - 12: `-XX:+UnlockDiagnosticVMOptions -XX:+PrintFieldLayout`(가능하면)·`Runtime` 메모리로 박싱 비용, 탈출 분석 on/off(`-XX:-DoEscapeAnalysis`) 할당량 차이.
  - 13: volatile 없는 플래그·DCL은 architecture/14와 겹침 → 링크하고 언어 쪽(happens-before 규칙) 실험만.
  - 14·15·16: 가상 스레드 vs 플랫폼 스레드 처리량(JEP 444), CPython 3.12 GIL에서 CPU 작업 스레드 vs 프로세스, 블로킹 큐 워커 패턴.
  - 17: vtable/인라인 캐시 — 단형/다형/메가모픽 호출 지연(JMH 없음 — 직접 측정, 해석 표시).
  - 18: 지연 스트림·영속 자료구조 공유.
  - 19: 위상정렬 의존성 해석, semver 범위 충돌 모형, Go MVS(오프라인 — 모형으로).
  - 20: gcc/clang `-O2`가 UB 이후 null 검사 삭제, `-fsanitize=address,undefined` 보고(공격 코드 금지).
  - 22·25: `-O0`/`-O2` 비교(DCE·인라이닝 objdump), gcc `-flto`·`-fprofile-generate/-use`로 바이너리 크기·속도.
  - 24: Native Image는 이 호스트에 없다 — JEP 483 문서·Spring 문서로 대신하고, 리플렉션 도달성 문제는 작은 모형(호출 그래프 BFS)으로.
- 노트에 싣는 것: 실험 코드 핵심, 환경(호스트·이미지 버전·JVM 옵션), **실제 출력**, 관찰과 해석. 비결정 값은 여러 번 돌린 범위.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-lang-w<NN>-*`, `--rm`, `--cpus=2` 이하, 가능하면 `--network none`. 두 컨테이너가 통신해야 하면 `docker network create sn-lang-w<NN>-net --internal`로 만들고 끝나면 지운다. **이미 있는 이미지만**(`golang:1.23-alpine`, `eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 볼륨은 가능하면 만들지 않는다(익명 볼륨은 `--rm`으로 같이 지워진다). 끝나면 `docker ps -a --filter name=sn-lang-w<NN>`·`docker network ls --filter name=sn-lang`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만). Go는 `golang:1.23-alpine`(표준 라이브러리만, `GOFLAGS=-mod=mod` 금지·모듈 다운로드 금지 — `--network none`이라 받을 수도 없다).
- **호스트 도구**: gcc 13·clang 18·objdump·python3(표준 라이브러리)만. **sudo·패키지 설치 금지**(pip·apt·npm install 포함). 실험은 수십 초~몇 분 이내·메모리 1GB 이하.
- **데이터**: 합성 데이터만(사람 이름·이메일·전화번호 같은 실제 개인정보 금지 — `user_001` 형식).
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/lang/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다.
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지).
- **금지**: `sn-de-*`·`sn-net46-*`·`sn-arch-*`·`payment-*`·`jun-bank-*`·`text-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(문서 URL·명세 절·논문)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·네트워크를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
