# 집필 브리핑 — 커리큘럼 leaf 새 노트 (엔지니어링 실천, 2026-10-05)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §17 엔지니어링 실천 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §17 머리 문단(SWEBOK v4를 개발자 시점으로 압축, 뼈대: SWEBOK v4·SWE@G·DORA·Google eng-practices·ISO/IEC/IEEE 29148)도 읽는다.
- **영역 표**: `cs/engineering-practice/README.md`(생성 문서). 원본(보강 6편): `cs/engineering/agile-and-squad`, `cs/engineering/development-standards/{quality,security,operational,legal}-standards`(+`legal-standards/provisions.md`, `development-standards/index.md`·`README.md`), `cs/foundations/three-virtues` — **읽기만**.
- **근거**: SWEBOK v4(computer.org PDF — KA 이름·장 번호 확인), SWE@G(abseil.io/resources/swe-book 온라인판 — 9 Code Review·10 Documentation·16 Version Control·18 Build Systems·23 CI·24 CD 등 장 번호·절 이름 확인), DORA(dora.dev 지표 정의·연도별 보고서), Google eng-practices(google.github.io/eng-practices), ISO/IEC/IEEE 29148, Agile Manifesto(agilemanifesto.org), Pro Git(git-scm.com/book 10장), git 소스·문서(git-scm.com/docs), trunkbaseddevelopment.com, Humble–Farley 『Continuous Delivery』, Fowler(martinfowler.com — TechnicalDebtQuadrant·ContinuousIntegration·FeatureToggles 등), Diátaxis(diataxis.fr), McConnell 『Software Estimation』, reproducible-builds.org, Docker 문서(멀티스테이지·빌드 캐시), Maven·Gradle 문서, SPDX·OSI, SEC 34-70694(Knight), Cloudflare 2019-07-02 사후 보고서, Wall 외 『Programming Perl』. 책 본문을 못 열면 목차·출판사 발췌로 확인한 범위만 단정, 나머지는 장 단위·`[?]`.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/engineering-practice/<NN-slug>/`의 4파일

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
# engineering-practice/<NN-slug> — <한 줄 제목> — 정리 (힌트)

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
- **동작·원리**: 중심. ASCII 그림 먼저(git 객체 DAG·브랜치 포인터, 3-way 병합, 브랜치 수명 시간축, 파이프라인 DAG, 빌드 DAG와 캐시 키, 이미지 레이어 스택, 불확실성 원뿔, 부채 4사분면, 문서 4유형), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) Merkle DAG·콘텐츠 주소(SHA-1/SHA-256), 3-way merge(LCA·merge-base), reflog, 위상정렬(빌드·파이프라인 DAG), 콘텐츠 해시 캐시 키, 레이어 해시·유니온 파일시스템, 몬테카를로·PERT 3점 추정, 추적 매트릭스(요구↔테스트), 리뷰 큐. cs 노트가 있으면 링크(`../../data-structure/27-merkle-tree` 등).
- **적용 — 풀어나가는 법**: 실무 순서. 명령(`git`·`docker build`·`mvn`·CI 설정 YAML)과 코드(Java·JS·TS 기본, 셸은 진단·실험 구동에만)·진단(로그·지표·명령 출력 읽기).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(에러·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(새 노트 `../NN-slug/2-summary.md`, 아직 없는 engineering-practice 주제는 `../README.md`, 다른 영역은 그 영역 README + "미작성", 다른 영역은 실제 경로 확인 — 특히 `../../reliability/…`(23 deployment·24 feature flag·26 incident·53 incidents), `../../testing/…`(01 pyramid·09 flaky·15 mutation·16 coverage), `../../software-design/…`(10 code smells·13 refactoring·47 ADR·53 code forensics), `../../data-structure/…`(27 merkle-tree), `../../os/…`(28 containers), `../../security/…`(있는 것만), `../../api-design/…`, 원본 `../../engineering/…`·`../../foundations/three-virtues`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄을 덧붙인다(근거 있는 오해만, 없으면 생략 — 새 절을 만들지 않는다, 2026-10-05 합의).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java(기본)·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M. 다 쓰고 스스로 대조.
- **제품·버전 한정**: "git 2.43 기준", "Docker BuildKit에서는", "Maven 3.9에서는", "DORA 2024 보고서 기준". 책의 원칙(저자 주장)과 사실(측정·문서)을 구분하고, 저자마다 다른 정의(예: trunk-based 정의(trunkbaseddevelopment.com vs DORA), CI vs CD vs 지속적 배포, 기술부채(Cunningham 원뜻 vs Fowler 사분면), DORA 지표 정의의 연도별 변화)는 출처별로 나눠 쓴다.
- **원칙은 주장으로, 측정은 측정으로**: "좋은 설계"는 단정하지 않는다 — 어떤 변경에서 비용이 줄었는지 실험(diff 크기·영향 파일 수)으로 보이고, 반대 상황(그 추상이 손해인 변경)도 함께 보인다(APOSD·YAGNI 균형).
- **도구 동작은 버전·조건과 함께**: 예) git 기본 병합 전략(ort, 2.34+), `push --force-with-lease`, reflog 만료 기본값(gc.reflogExpire 90일·unreachable 30일), BuildKit 캐시 무효화 규칙(COPY 해시·ARG), `SOURCE_DATE_EPOCH`, Maven 증분 빌드 한계, DORA 지표 정의(2024 재작업률 추가) — 문서·소스·실행으로 확인. **표준·연구(SWEBOK·DORA 데이터) vs 회사 관례(Google) vs 저자 주장**을 구분해 쓴다.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **도구 기본값·지표 정의는 문서·소스로 확인**(예: git 기본값, BuildKit 캐시 규칙, DORA 지표 정의).
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트 이어받기 (보강 6편 담당자)

- 원본은 **수정하지 않는다.** 담당 주제의 원본: 명세 §1 보강 목록.
- 원본을 먼저 **읽는다.** 이미 설명한 것은 길게 되풀이하지 않고 "기초는 원본 §N" 링크 + 한두 줄 요약.
- 빈 곳을 채운다: 커리큘럼 ⚠ 장애, 자료구조, 실험, 적용(명령·코드·진단), 질문·정답.
- 원본에 틀린 내용이 있으면 새 leaf에 올바르게 쓰고 `참고: 원본 §N의 "…"는 …(근거)` 한 줄로 짚는다(인용문 `>`가 아닌 일반 문장).
- 법률 표준(17)은 한국 법령 원문(law.go.kr — 개인정보 보호법·정보통신망법 등)과 라이선스 원문(SPDX·OSI)으로 확인하고, 법률 해석은 "해석·법률 자문 아님"으로 표시한다.

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험으로 보인다**(19·20 종합은 선택). git 실험은 scratchpad의 일회용 저장소에서만(이 저장소의 git은 조회만), author는 `Example <ex@example.invalid>`. 예:
  - 01: 회고 없는 반복 vs 있는 반복 — 시뮬레이션이면 시뮬레이션이라고 명시(실측처럼 쓰지 않는다).
  - 02: 모호 요구를 검증 가능한 문장으로 바꾼 전후 테스트 수·추적 매트릭스(요구↔테스트 누락 탐지 스크립트).
  - 03: `git cat-file -p`로 커밋·트리·블롭 보기, `git hash-object`로 해시 재계산, force push 뒤 reflog 복구 vs 다른 클론에서 유실, 3-way 병합 충돌과 잘못된 해결로 조용한 코드 소실, 같은 내용 = 같은 블롭.
  - 04: 장수 브랜치 vs 매일 통합 — 같은 변경 흐름을 두 방식으로 재생해 충돌 수·충돌 줄 비교(스크립트로 생성한 커밋, 시뮬레이션 명시).
  - 05: 리뷰 크기 — 공개 연구 수치(출처) + 작은 실험(diff 크기별 리뷰 체크리스트 적용 시간은 측정 불가 → 문서 근거로 대신하고 밝힌다).
  - 06·07: 빌드 DAG 위상정렬 직접 구현 vs 도구 결과, 증분 빌드 캐시 적중(Maven/Gradle 또는 직접 만든 해시 캐시), 캐시 키에 입력 누락 시 옛 산출물 재사용(오염) 재현, 재현 가능 빌드(타임스탬프 포함 jar 해시 차이 → `project.build.outputTimestamp`/`SOURCE_DATE_EPOCH`로 일치).
  - 08: 같은 Java 앱을 단일 스테이지 JDK vs 멀티스테이지 JRE·jlink로 빌드해 이미지 크기·레이어 수, 레이어 순서에 따른 재빌드 캐시 적중, `.dockerignore` 유무 컨텍스트 크기, alpine(musl) 차이는 문서 근거 — **기존 베이스 이미지만**(eclipse-temurin:21-jdk/jre, 21-jre-jammy, node:22-alpine 등), 태그 `sn-ep-w08-*`, 끝나면 자기 이미지만 rmi.
  - 09: 일회용 git 이력·배포 로그로 DORA 4~5지표 계산 스크립트, 지표를 목표로 할 때의 게이밍 예.
  - 10·11: 코드 이력 churn·핫스팟(software-design/53과 링크), 문서 신선도(링크 깨짐·마지막 수정일) 측정 스크립트.
  - 12·13: 3점 추정 몬테카를로(합의 분포 vs 점 추정 합), 총소유비용 계산 표(가정은 예시 명시).
  - 14~17: 원본 기준을 도구로 확인(예: 정적 분석 규칙 위반 수, 의존성 라이선스 목록·호환성 확인, 로그 형식 일관성 검사), 법률은 원문 대조.
  - 18: 태도 노트 — 실험 대신 원문(Programming Perl 용어집) 대조로 대신하고 밝힌다.
- 실험 코드는 scratchpad에 둔다(저장소 루트·노트 폴더 금지). 결과 표에는 실제 명령 출력만 싣는다.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(제품·버전), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, git 2.43 / JDK 21 temurin, 2026-10-05)`처럼 환경을 적는다. 비결정적 값은 "실행마다 다르다"고 적고 여러 번 돌린 범위를 쓴다.
- **실험으로 보일 수 없는 주장**은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.
- **재부팅 대비**: 실험 코드의 핵심은 노트에 싣는다(/tmp는 재부팅 때 사라진다).

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요한 것은 워커가 **자기 전용 일회용 컨테이너**로 띄운다: 이름 `sn-ep-w<NN>-*`, 네트워크 `sn-ep-w<NN>-net`, 포트는 열지 않거나 127.0.0.1만. **이미 있는 이미지만** 쓴다(`eclipse-temurin:21-jdk`, `maven:3.9-eclipse-temurin-21`, `postgres:17`, `redis:7-alpine`, `node:22-alpine`·`node:22-bookworm-slim`, `grafana/k6:1.2.3`, `nginx:alpine`, `apache/kafka:4.1.0`, `testcontainers/ryuk:0.12.0`·`0.14.0`) — **새 이미지 받기 금지**. 끝나면 자기 컨테이너만 `docker rm -fv <이름>` + `docker network rm <자기 네트워크>`. **`docker volume prune`·`system prune`·`image prune` 등 일괄 삭제 금지**(남의 볼륨까지 지울 수 있다), `docker ps -a --filter name=sn-ep-w<NN>`가 비었는지 확인.
- **Testcontainers(필요할 때만)**: maven 컨테이너에 `-v /var/run/docker.sock:/var/run/docker.sock`을 붙이고, 이미지 이름을 이미 있는 태그로 고정한다(`postgres:17`, `TESTCONTAINERS_RYUK_CONTAINER_IMAGE=testcontainers/ryuk:0.14.0` 또는 0.12.0). 컨테이너 안에서 호스트 접근은 `TESTCONTAINERS_HOST_OVERRIDE`·`--add-host=host.docker.internal:host-gateway` 등 문서 방식으로. 실행 전후 `docker ps -a --filter label=org.testcontainers=true`를 기록하고 끝나면 0이어야 한다(남으면 그 라벨 컨테이너 중 **자기가 만든 것만** 지운다). 새 이미지가 필요해지면 받지 말고 멈춰 packet에 보고.
- **파일 소유권**: 컨테이너는 `-u $(id -u):$(id -g) -e HOME=/tmp`로 돌린다(root로 돌리면 scratchpad에 root 소유 파일이 남는다). maven은 `-Dmaven.repo.local=/m2`에 `-v <scratchpad>/ts/m2:/m2`를 붙여 공용 로컬 저장소를 쓴다(스모크 확인: JUnit 5.13.4·surefire 3.5.3 받아 통과).
- **사용 통계 끄기(2026-10-03 w08)**: Pact는 `pact_do_not_track=true`, 의존성을 다 받은 뒤 실행은 `--network none`. Testcontainers는 매핑 포트를 0.0.0.0에 잠깐 연다(문서 동작) — 실행 시간을 짧게.
- **라이선스·사용 조항 존중(2026-10-03 w07)**: jqwik 1.10 User Guide에 AI 코딩 에이전트 사용을 원치 않는다는 "Anti-AI Usage Clause"가 있다 — jqwik은 실행하지 않는다(문서 인용·코드 모양만, 실험은 fast-check 등). 다른 도구도 비슷한 조항이 있으면 따르고 packet에 보고.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 라이브러리(JUnit 5·Mockito·AssertJ·jqwik·PIT·JaCoCo·Pact·H2 등)는 maven 이미지로 받아 쓴다 — 소규모 `pom.xml` 프로젝트 + `mvn -q test`, 로컬 저장소는 scratchpad 안(`-Dmaven.repo.local=/w/.m2`, 담당 폴더끼리 공유하려면 `scratchpad/ts/m2`). **Node**: 호스트 node 18, TS는 `tsc`.
- **부하 상한**: 실행 수십 초 이내, `--cpus=2` 이하로 제한, 호스트를 포화시키는 부하 테스트·메모리를 크게 먹는 실험(힙 1GB 초과) 금지. 측정 수치는 이 제한 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/ep/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.**
- **이미지**: 이미지를 받지 않는다(`docker pull` 금지). **빌드는 08 등 필요한 편만** — 기존 베이스로, 태그 `sn-ep-w<NN>-*`, 끝나면 **자기가 빌드한 이미지만** `docker rmi`(남의 이미지·`docker builder prune`·`image prune` 금지), `docker images | grep sn-ep`가 비었는지 확인.
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다. SEC처럼 연락처 User-Agent를 요구하는 사이트는 열지 말고 다른 출처(언론·미러)를 쓰거나 `[?]`.
- **금지**: `sn-ad-*`·`sn-ts-*`·`sn-dm-*`·`sn-sd-*`·`sn-rl-*`·`sn-dw-*`·`payment-codex-*`·`jun-bank-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·이미지는 건드리지 않는다.

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
