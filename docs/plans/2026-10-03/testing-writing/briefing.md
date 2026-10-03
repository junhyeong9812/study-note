# 집필 브리핑 — 커리큘럼 leaf 새 노트 (테스트, 2026-10-03)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §14 테스트 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §14 머리 문단(뼈대: SWE@G 11~14장, Khorikov, Beck TDD·Canon TDD, Fowler "Mocks Aren't Stubs", Meszaros, Feathers)도 읽는다.
- **영역 표**: `cs/testing/README.md` — 번호·선행·다른 영역 노트 링크 대상. 기존 노트는 없다(전부 신규).
- **근거**: SWE@G(abseil.io/resources/swe-book 온라인판 — 장 번호·절 이름 확인), Khorikov 『Unit Testing PPP』(Manning 목차·livebook 발췌), Beck 『TDD by Example』·"Canon TDD"(tidyfirst.substack.com 2023), Fowler martinfowler.com(MocksArentStubs·TestPyramid·PracticalTestPyramid·ContractTest·NonDeterminism·TestCoverage·IntegrationTest 등), Meszaros xunitpatterns.com, Feathers 『WELC』, Freeman–Pryce 『GOOS』, ISTQB CTFL 4.0 syllabus PDF, Claessen–Hughes ICFP 2000, Jia–Harman TSE 2011, Luo 외 FSE 2014, Google Testing Blog, 제품 문서·소스(JUnit 5 User Guide·Mockito javadoc·AssertJ·Testcontainers·Pact·jqwik·PIT(pitest.org)·JaCoCo·Playwright/Testing Library 문서·k6). 책 본문을 못 열면 목차·출판사 발췌·저자 사이트로 확인한 범위만 단정하고 나머지는 장 단위·`[?]`.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/testing/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-03 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# testing/<NN-slug> — <한 줄 제목> — 정리 (힌트)

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
- **동작·원리**: 중심. ASCII 그림 먼저(피라미드·테스트 크기, 테스트 더블 분류, 고전파 vs 런던파 호출 그림, TDD 사이클, 경계값 수직선, 상태 전이 그래프, 계약 흐름(소비자→계약→제공자), 축소 과정, 변이 연산자, 불안정 테스트 시간축), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) Fake = 인메모리 자료구조, 동치 분할·경계값, 결정 테이블, 상태 전이 그래프·전이 커버리지, pairwise 조합(직교 배열), 무작위 생성 + 축소(이진 탐색식), 변이 연산자, 제어 흐름 그래프(라인·분기·조건 커버리지), 가짜 시계·결정적 스케줄러. cs 노트가 있으면 링크.
- **적용 — 풀어나가는 법**: 실무 순서. 코드(Java 기본 — JUnit 5·AssertJ·Mockito, 필요 시 TS/JS Jest·Vitest)와 진단(CI 실패 재현, 반복 실행으로 불안정 비율 측정, 변이 점수·커버리지 보고서 읽기 등).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(에러·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(새 노트 `../NN-slug/2-summary.md`, 아직 없는 주제는 `../README.md` 또는 해당 영역 README + "미작성", 다른 영역은 실제 경로 확인 — 특히 `../../software-design/…`(01 complexity·13 refactoring·51 legacy 등), `../../reliability/…`(23 deployment·53 incidents 등), `../../domain-modeling/…`, `../../os/…`(15 race conditions), `../../math/…`, `../../api-design/…`, `../../../languages/java/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`.
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java(기본)·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M. 다 쓰고 스스로 대조.
- **제품·버전 한정**: "JUnit 5.x에서는", "Mockito 5.x에서는", "PIT 1.x 기본 변이 연산자 집합", "Testcontainers 1.x/2.x에서는". 책의 원칙(저자 주장)과 사실(측정·문서)을 구분하고, 저자마다 다른 정의(예: Fowler vs Khorikov의 mock 정의, Meszaros 더블 분류, SWE@G의 test size vs scope, ISTQB 기법 정의)는 출처별로 나눠 쓴다.
- **원칙은 주장으로, 측정은 측정으로**: "좋은 설계"는 단정하지 않는다 — 어떤 변경에서 비용이 줄었는지 실험(diff 크기·영향 파일 수)으로 보이고, 반대 상황(그 추상이 손해인 변경)도 함께 보인다(APOSD·YAGNI 균형).
- **라이브러리 동작은 버전·조건과 함께**: 예) Mockito strict stubs(`UnnecessaryStubbingException`)·기본 응답(RETURNS_DEFAULTS), JUnit 5 테스트 순서 기본(결정적이지만 명시 안 됨 — `MethodOrderer` 문서 확인), `@RepeatedTest`, PIT 기본 변이 연산자(DEFAULTS 그룹), JaCoCo 카운터 정의(라인·분기·명령), jqwik 기본 시도 수·축소 — 문서·소스·실행으로 확인.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **도구 기본값·지표 정의는 문서·소스로 확인**(예: PIT 변이 점수 분모(커버되지 않은 변이 포함 여부), JaCoCo 분기 카운트, k6 지표).
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트

- 이 영역은 기존 노트가 없다(전부 신규). 인접 영역 노트(software-design 13·51·52, reliability 19·23·53, domain-modeling 11·13·14, os 15)와 겹치는 내용은 링크하고 테스트 관점만 쓴다.

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험으로 보인다**(20·21 종합은 선택). 예:
  - 01: 테스트 크기별 실행 시간(작은 단위 테스트 N개 vs 컨테이너 통합 테스트 1개), 같은 결함을 잡는 테스트 위치.
  - 02·04: 같은 동작을 구현 세부(private 호출·mock verify)로 검증한 테스트와 관찰 가능한 결과로 검증한 테스트 — 동작을 보존하는 리팩터링 뒤 깨지는 테스트 수(거짓 양성), 버그 주입 뒤 잡는 테스트 수(거짓 음성).
  - 03: mock이 실제 의존과 다른 계약(예: null 대신 예외, 정렬 순서)을 흉내 내 단위 테스트는 초록인데 Fake·실제 구현과 붙이면 실패.
  - 05·06: TDD 사이클 기록(테스트 목록 → 빨강 → 초록 → 리팩터링을 git 커밋으로), 기대값에 계산 결과를 붙여 넣어 버그를 고정하는 반례, 인수 테스트 빨강이 조립 누락을 잡는 예.
  - 07: 경계값·동치 분할 테스트가 off-by-one을 잡고 무작위 예제는 못 잡는 비율, pairwise 조합 수 vs 전수 조합 수.
  - 08: H2(호환 모드) vs PostgreSQL 17(Testcontainers)에서 다르게 동작하는 SQL·락(예: `SELECT … FOR UPDATE SKIP LOCKED`, 정렬·NULL 순서, 타입 캐스팅, upsert 문법) 실제 출력.
  - 09·10: 순서 의존(공유 정적 상태)·시간 의존(`LocalDate.now()`)·경쟁 조건 테스트를 반복 실행해 실패 비율, 가짜 `Clock`·결정적 실행기로 고친 뒤 0.
  - 11·12: 공유 픽스처 순서 의존 재현, Assertion Roulette 실패 메시지 vs 커스텀 단언 메시지.
  - 13: Pact(JVM 또는 JS)로 소비자 계약 생성 → 제공자 필드 변경 시 검증 실패 출력.
  - 14: jqwik(또는 fast-check) 속성 테스트가 찾은 반례와 축소 출력.
  - 15·16: PIT 변이 점수 vs JaCoCo 라인·분기 커버리지 — 단언 없는 테스트로 커버리지 100%·변이 점수 낮음.
  - 17: 특성 테스트(골든 마스터)로 레거시 출력 고정 → 리팩터링 중 의도치 않은 변화 검출.
  - 18: 취약한 선택자(구조·CSS 경로) vs 역할·레이블 선택자 — 마크업 변경 뒤 깨지는 테스트 수(jsdom + Testing Library 등, 브라우저 다운로드 없이).
  - 19: 합성 모니터링·카나리 분석을 작은 시뮬레이션으로(기준 vs 카나리 오류율 비교 판정), k6 체크.
  - 21: goto fail 구조를 C로 재현해 음성 테스트(잘못된 서명) 유무에 따른 검출.
- 실험 코드는 scratchpad에 둔다(저장소 루트·노트 폴더 금지). 결과 표에는 실제 명령 출력만 싣는다.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(제품·버전), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, JDK 21 temurin · JUnit 5.x, 2026-10-03)`처럼 환경을 적는다. 비결정적 값은 "실행마다 다르다"고 적고 여러 번 돌린 범위를 쓴다.
- **실험으로 보일 수 없는 주장**은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.
- **재부팅 대비**: 실험 코드의 핵심은 노트에 싣는다(/tmp는 재부팅 때 사라진다).

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요한 것은 워커가 **자기 전용 일회용 컨테이너**로 띄운다: 이름 `sn-ts-w<NN>-*`, 네트워크 `sn-ts-w<NN>-net`, 포트는 열지 않거나 127.0.0.1만. **이미 있는 이미지만** 쓴다(`eclipse-temurin:21-jdk`, `maven:3.9-eclipse-temurin-21`, `postgres:17`, `redis:7-alpine`, `node:22-alpine`·`node:22-bookworm-slim`, `grafana/k6:1.2.3`, `testcontainers/ryuk:0.12.0`·`0.14.0`) — **새 이미지 받기 금지**. 끝나면 자기 컨테이너만 `docker rm -fv <이름>` + `docker network rm <자기 네트워크>`. **`docker volume prune`·`system prune`·`image prune` 등 일괄 삭제 금지**(남의 볼륨까지 지울 수 있다), `docker ps -a --filter name=sn-ts-w<NN>`가 비었는지 확인.
- **Testcontainers(08 등만)**: maven 컨테이너에 `-v /var/run/docker.sock:/var/run/docker.sock`을 붙이고, 이미지 이름을 이미 있는 태그로 고정한다(`postgres:17`, `TESTCONTAINERS_RYUK_CONTAINER_IMAGE=testcontainers/ryuk:0.14.0` 또는 0.12.0). 컨테이너 안에서 호스트 접근은 `TESTCONTAINERS_HOST_OVERRIDE`·`--add-host=host.docker.internal:host-gateway` 등 문서 방식으로. 실행 전후 `docker ps -a --filter label=org.testcontainers=true`를 기록하고 끝나면 0이어야 한다(남으면 그 라벨 컨테이너 중 **자기가 만든 것만** 지운다). 새 이미지가 필요해지면 받지 말고 멈춰 packet에 보고.
- **파일 소유권**: 컨테이너는 `-u $(id -u):$(id -g) -e HOME=/tmp`로 돌린다(root로 돌리면 scratchpad에 root 소유 파일이 남는다). maven은 `-Dmaven.repo.local=/m2`에 `-v <scratchpad>/ts/m2:/m2`를 붙여 공용 로컬 저장소를 쓴다(스모크 확인: JUnit 5.13.4·surefire 3.5.3 받아 통과).
- **사용 통계 끄기(2026-10-03 w08)**: Pact는 `pact_do_not_track=true`, 의존성을 다 받은 뒤 실행은 `--network none`. Testcontainers는 매핑 포트를 0.0.0.0에 잠깐 연다(문서 동작) — 실행 시간을 짧게.
- **라이선스·사용 조항 존중(2026-10-03 w07)**: jqwik 1.10 User Guide에 AI 코딩 에이전트 사용을 원치 않는다는 "Anti-AI Usage Clause"가 있다 — jqwik은 실행하지 않는다(문서 인용·코드 모양만, 실험은 fast-check 등). 다른 도구도 비슷한 조항이 있으면 따르고 packet에 보고.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 라이브러리(JUnit 5·Mockito·AssertJ·jqwik·PIT·JaCoCo·Pact·H2 등)는 maven 이미지로 받아 쓴다 — 소규모 `pom.xml` 프로젝트 + `mvn -q test`, 로컬 저장소는 scratchpad 안(`-Dmaven.repo.local=/w/.m2`, 담당 폴더끼리 공유하려면 `scratchpad/ts/m2`). **Node**: 호스트 node 18, TS는 `tsc`.
- **부하 상한**: 실행 수십 초 이내, `--cpus=2` 이하로 제한, 호스트를 포화시키는 부하 테스트·메모리를 크게 먹는 실험(힙 1GB 초과) 금지. 측정 수치는 이 제한 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/ts/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.**
- **이미지(2026-10-01 사고)**: 이 작업은 이미지를 받지도 지우지도 않는다(`docker pull`·`docker rmi` 금지).
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다. SEC처럼 연락처 User-Agent를 요구하는 사이트는 열지 말고 다른 출처(언론·미러)를 쓰거나 `[?]`.
- **금지**: `sn-dm-*`·`sn-sd-*`·`sn-rl-*`·`sn-dw-*`·`payment-codex-*`·`jun-bank-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·이미지는 건드리지 않는다.

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
