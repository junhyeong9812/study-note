# 갭 리서치 — 유지보수성과 설계 판단 (클린코드의 실무 판단층) (2026-09-28, L0)

---

## 0. 한 줄 진단

현재 §12는 **"무엇이 좋은 구조인가"**(복잡도·모듈·SOLID·패턴·아키텍처)는 갖췄다. 하지만 **"언제·얼마나·어떤 순서로 바꾸나"**는 거의 없다. 이 판단층에는 추상화 시점, 변경 축, 구조 변경과 동작 변경의 분리, 레거시 진입, 측정, 삭제가 들어간다.

또 04-clean-code에는 **표와 기존 노트가 서로 다른 내용**이라는 불일치가 있다(§3).

---

## 1. 커버 점검표

| # | 조사 항목 | 판정 | 근거 / 흡수 위치 |
|---|---|---|---|
| 1 | Parnas 1972 — 바뀔 결정을 숨기는 분해 기준 | **부분** | `02-modularity-coupling-cohesion`이 Parnas 1972를 📚로 인용한다. 다만 요지는 "정보 은닉·결합·응집"의 정의에 그친다. **분해 기준**(처리 단계가 아니라 바뀔 결정으로 나눈다, KWIC 두 분해 비교)은 없다 |
| 2 | 변동성 기반 분해(Löwy 『Righting Software』) | 없음 | — |
| 3 | connascence(Page-Jones·Weirich) | 없음 | 02가 결합도를 다루지만 등급(강도·지역성·정도) 도구는 없다 |
| 4 | rule of three | 없음 | — |
| 5 | Sandi Metz "The Wrong Abstraction" | 없음 | — |
| 6 | DRY 오해(지식 중복 vs 코드 중복) | **부분** | 기존 노트 `engineering/clean-code` N절 "우연한 중복 vs 진짜 중복"에 있다. 다만 커리큘럼 표의 04 요지에는 없다 |
| 7 | YAGNI(비용 4종) | **부분** | `05-code-smells`의 Speculative Generality, `14-antipatterns`의 과설계에 증상만 있다. 판단 기준(build·delay·carry·repair)은 없다 |
| 8 | Beck 단순 설계 4규칙 | 없음 | — |
| 9 | Beck 『Tidy First?』 — 구조 변경과 동작 변경의 분리 | **부분** | `06-refactoring`의 "작은 단계"에 개념만 인접한다. 커밋·PR 분리, 정리 시점(먼저·나중·안 함)의 경제학은 없다 |
| 10 | 테스트 가능한 설계 — DI | **부분** | `11-solid` ⚠의 "DIP 부재 → 테스트 불가"에 한 줄 있다. 생성자 주입, composition root, service locator 반패턴은 없다 |
| 11 | functional core / imperative shell, 부수효과 격리 | 없음 | `language/10-functional-concepts`는 순수 함수라는 **언어 개념**만 다룬다. 설계 배치는 없다 |
| 12 | Feathers — seam, characterization test | **이미 있음** | `testing/16-characterization-tests-legacy`(특성 테스트·이음새) |
| 13 | Feathers — sprout/wrap, 의존 끊기 기법, 레거시 변경 알고리즘 | 없음 | testing/16은 안전망까지만 다룬다. **변경 기법**은 없다 |
| 14 | Strangler Fig·branch by abstraction·병행 실행 | **이미 제안됨** | gap-practical `software-design/25-legacy-migration-strangler-fig`에 있어 **중복 제안하지 않는다**. 코드 수준 parallel change(expand/contract)만 34에 넣는다(DB 버전은 `database/34-schema-migration`에 있다) |
| 15 | package by feature vs by layer(by component) | 없음 | `16-layered-hexagonal-clean`은 의존 방향만 다룬다. 폴더·패키지 배치와 가시성은 없다 |
| 16 | 순환 의존 제거 | **부분** | `17-component-principles`(ADP·SCC 탐지)가 있다. 탐지 **후 끊는 기법**(DIP 역전, 공통부 추출, 병합)은 없다 |
| 17 | ArchUnit·dependency-cruiser 경계 강제(적합도 함수) | 없음 | — |
| 18 | 순환·인지 복잡도 | 없음 | `testing/15-coverage`가 제어 흐름 그래프만 🔧로 쓴다 |
| 19 | Tornhill 핫스팟(churn × complexity)·change coupling | 없음 | `engineering-practice/10-technical-debt`는 부채 개념만 다룬다. **어디를 먼저 갚나**의 데이터 근거가 없다 |
| 20 | 이름 짓기 원칙 | **부분** | 04 요지에 "이름"이 있다. 하지만 기존 노트(CLEAN 5속성)에는 이름 절이 없다(§3) |
| 21 | 함수 설계(인자 수·CQS·플래그 인자·추상화 수준 일치) | **부분** | 04 요지 "함수"에만 있고, 기존 노트에는 없다. CQS는 `13-domain-modeling/17-cqrs`가 아키텍처 수준에서만 다룬다 |
| 22 | 주석이 필요한 자리(why)·일관성·관례 | **부분** | 04 요지 "주석·포매팅"에만 있고, 기존 노트에는 없다. 문서 일반론은 `engineering-practice/11` |
| 23 | 삭제 용이성(tef)·죽은 코드 제거 | 없음 | — |
| 24 | 기능 플래그 수명 | **이미 제안됨** | gap-practical `reliability/35-feature-flag-lifecycle`(제거 부채 포함)이 있다. 이 문서는 **코드 쪽 삭제 기법**만 42에 둔다 |
| 25 | 원시 타입 집착 제거 | **부분** | `domain-modeling/04` ⚠("금액을 `long`")와 `08-immutability-and-value-objects`에 있다. 도메인 전반의 **식별자·단위·검증된 문자열 타입화**는 없다 |
| 26 | 타입으로 불변식 표현(make illegal states unrepresentable, parse don't validate) | 없음 | `domain-modeling/10-state-machines`는 FSM 모델링만 다룬다. `language/06`은 타입 이론만 다룬다 |
| 27 | 에러 처리 설계의 유지보수성 | **이미 있음** | `07-error-handling-design`(fail-fast·예외 경계·에러 정의로 없애기). 로그·메시지 정책은 gap-practical 26 |
| 28 | null·부재 처리 설계 | **부분** | `language/09`(Option의 언어 기제)에 있다. 설계 판단(null 반환 vs 빈 컬렉션 vs Optional vs Null Object vs 예외)은 없다 |
| 29 | 조건 분기 폭발 → 다형성·테이블 기반 | **부분** | `13-design-patterns-gof`(Strategy·State)와 05의 Repeated Switches 스멜에 흩어져 있다. "if 지옥을 어느 도구로 푸나"의 판단 leaf가 없다 |

**요약**: 29개 항목 중 이미 있음 2, 이미 제안됨 2, 부분 12, 없음 13.

---

## 2. 신규 leaf 제안 (19개)

### 배치 — 새 단원 "12.7 유지보수성 판단"

§12.5 아키텍처 다음, §12.6 영역 마감 **앞**에 새 단원을 둔다. 역색인 `23-design-symptom-index`는 이 단원의 ⚠ 칸까지 흡수하도록 요지를 넓힌다.

단원은 4묶음이다. 가독성 3편(39~41)은 04를 쪼갠 결과이므로, 단원은 12.7이지만 **학습 순서상 04 직후**에 읽는다.

- **A. 변경 축**: 27·28
- **B. 추상화 시점·단순성**: 29·30·31
- **C. 테스트 가능성·레거시**: 32·33·34
- **D. 구조·측정**: 35·36·37·38
- **E. 가독성**(04 분할): 39·40·41
- **F. 수명·도메인 표현**: 42·43·44·45

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-decompose-by-change | 분해 기준 = **바뀔 결정을 숨긴다**. 처리 단계(흐름도)로 나누지 않는다. KWIC 두 분해 비교, 변동성 축 찾기(무엇이 어떤 이유로 얼마나 자주 바뀌나), 기능 분해의 함정 | 02-modularity-coupling-cohesion, 03-deep-modules-and-abstraction | 요구 1건("결제 수단 추가")에 컨트롤러·서비스·DTO·매퍼·enum 등 파일 12개 수정. 저장 포맷 변경이 모든 단계 모듈을 깨뜨림(단계별 분해가 포맷을 공유). 기능별 서비스(`OrderService`·`PaymentService`)가 같은 변동을 나눠 가짐 | 의존 그래프 위 변경 전파 범위(도달 가능 집합) | Parnas CACM 1972 · Löwy 『Righting Software』 2019 1부 [?] · APOSD 5장 | 필수 | 신규 (02를 심화) |
| 28-connascence | 결합을 **종류·강도·지역성·정도**로 재는 어휘다. 이름 → 타입 → 의미 → 위치 → 알고리즘(정적), 실행 순서 → 타이밍 → 값 → 동일성(동적). 강한 것은 약하게 바꾸고, 멀리 떨어질수록 약한 것만 허용한다 | 02 | 인자 순서 결합: `transfer(from, to, amount)`에서 from/to 뒤바뀜 → 컴파일은 통과하고 반대 송금. 매직 값 결합: 상태 `3`의 뜻이 서비스 2곳에 따로 하드코딩돼 한쪽만 수정. 호출 순서 결합: `init()` 전 `send()` 호출 시 NPE | — | Page-Jones 『What Every Programmer Should Know About OOD』 1995 [?] · Weirich "Grand Unified Theory of Software Design" 2009 [?] · connascence.io | 권장 | 신규 |
| 29-when-to-abstract | 추상화 **시점**: rule of three, "잘못된 추상화보다 중복이 훨씬 싸다", DRY = 지식의 단일 표현이지 글자 중복 제거가 아니다, 우연한 중복 판별(함께 바뀌나), 잘못된 추상화에서 되돌아가기(인라인 후 재추출) | 04-clean-code, 05-code-smells | 공통 함수에 boolean·type 인자가 5개 붙고 내부 `if` 12개. 한 호출처를 고치면 다른 호출처 회귀. "공통 모듈"을 팀 3개가 공유해 아무도 못 고침. 두 번째 사례에서 뽑은 추상화가 세 번째 사례에 안 맞아 파라미터가 늘어남 | — | Fowler 『Refactoring』 2판 2장(Rule of Three, Don Roberts) [?] · Metz "The Wrong Abstraction" 2016 · Hunt–Thomas 『The Pragmatic Programmer』 20주년판 DRY [?] | 필수 | 신규 (연결: `engineering/clean-code` N절) |
| 30-simple-design-and-yagni | Beck 단순 설계 4규칙(테스트 통과 → 의도 드러냄 → 중복 없음 → 요소 최소, 우선순위 순). YAGNI의 비용 4종(build·delay·carry·repair). **확장점은 두 번째 요구가 올 때** 만든다 | 29 | 안 쓰는 인터페이스·팩토리·플러그인 구조 → 새 기능 추가 때마다 5계층 수정(carry 비용). "나중에 필요할" 설정 키 40개 중 38개 미사용, 조합 테스트 불가. 추측한 확장점이 실제 요구 모양과 달라 결국 우회(repair 비용) | — | Fowler "BeckDesignRules" 2015 · Fowler "Yagni" 2015 · Beck 『XP Explained』 2판 [?] | 필수 | 신규 |
| 31-tidy-first | **구조 변경과 동작 변경을 섞지 않는다.** 정리(tidying) 목록(가드 절·죽은 코드 삭제·대칭 맞추기·설명 변수 등), 정리 시점(먼저·나중·나중에 따로·안 함), 커밋·PR 분리, 결합과 응집의 경제학(옵션 가치) | 06-refactoring, engineering-practice/06-code-review | 이름 변경 300줄과 로직 수정 5줄이 한 PR → 리뷰어가 버그를 못 봄. 섞인 커밋은 revert하면 정리까지 날아가 되돌리기 불가. "정리하느라" 기능 PR이 2주 지연되며 충돌 누적 | — | Beck 『Tidy First?』 2023 (1·2·3부) [?] | 권장 | 신규 |
| 32-testable-design-and-di | 테스트하기 어려움 = 설계 신호. 생성자 주입, composition root(조립은 한 곳), service locator·정적 호출·`new` 숨김의 비용, 시계·난수·UUID 같은 **숨은 입력** 주입 | 11-solid, testing/03-test-doubles | 서비스 단위 테스트에 DB·Redis·외부 API가 전부 필요. 테스트마다 static mock(`mockStatic`)을 도배. `LocalDate.now()` 직접 호출로 월말에만 실패. 컨테이너에서 꺼내 쓰는 `getBean()` → 의존이 시그니처에 안 보여 누락 발견 늦음 | 의존 그래프(생성 순서 = 위상 정렬) | Seemann–van Deursen 『Dependency Injection Principles, Practices, and Patterns』 2019 [?] · Fowler "Inversion of Control Containers and the Dependency Injection pattern" 2004 [?] | 필수 | 신규 (연결: `testing/12-testing-time-and-concurrency`) |
| 33-functional-core-imperative-shell | 결정은 순수 함수(코어)에 두고, I/O·DB·시간은 바깥 껍질에 둔다. 값이 경계를 넘는다. "읽기 → 결정 → 쓰기" 샌드위치. 부수효과를 가장자리로 밀어낸다 | 32, language/10-functional-concepts | 할인 계산 로직이 리포지토리 호출 사이에 끼어 있어 규칙 하나 테스트에 mock 7개. 같은 계산이 배치·API에서 부수효과와 엉켜 재사용 불가. mock 순서 검증 테스트 → 리팩터링마다 대량 실패 | — | Bernhardt "Boundaries" SCNA 2012 · Bernhardt "Functional Core, Imperative Shell" 스크린캐스트 [?] · Khorikov 7장(Humble Object) [?] | 권장 | 신규 |
| 34-legacy-change-techniques | 레거시 변경 알고리즘(변경점 찾기 → 테스트 지점 → 의존 끊기 → 테스트 → 변경), seam 종류와 enabling point, **sprout method/class, wrap method/class**, 의존 끊기 기법(인터페이스 추출·매개변수화), 코드 인터페이스의 parallel change(expand → migrate → contract) | testing/16-characterization-tests-legacy, 06-refactoring | 3천 줄 메서드 한가운데 새 규칙을 끼워 넣음 → 테스트 불가 상태가 더 커짐. 시그니처를 한 번에 바꿔 호출처 80곳이 동시 변경, 머지 지옥. "일단 다 고치고 테스트" → 숨은 동작(반올림·정렬) 소실 | 호출 그래프(영향 범위) | Feathers 『Working Effectively with Legacy Code』 2004 (2·4·6·25장) [?] · Fowler "ParallelChange" 2014 | 필수 | 신규 (연결: gap-practical `25-legacy-migration-strangler-fig`) |
| 35-codebase-structure | 패키지 배치: by layer vs by feature vs **by component**, 가시성(package-private)으로 경계 만들기, "소리치는 아키텍처"(최상위 폴더가 도메인을 말한다), 공통(`common`·`util`) 폴더의 함정 | 16-layered-hexagonal-clean, 17-component-principles | 기능 하나 수정에 `controller/`·`service/`·`repository/`·`dto/` 네 폴더를 오감. 모든 클래스가 `public`이라 다른 기능이 내부 리포지토리를 직접 호출. `util` 패키지가 3천 줄로 커져 모든 모듈이 의존 | 패키지 의존 그래프 | Brown "Package by component" (『Clean Architecture』 34장 "The Missing Chapter") [?] · Martin "Screaming Architecture" 2011 [?] | 필수 | 신규 |
| 36-architecture-fitness-rules | 경계를 **테스트로 강제**한다. ArchUnit(Java)·dependency-cruiser(JS/TS)·import-linter(Python)로 계층·순환·명명 규칙 검사, 기존 위반 동결(baseline). 순환 **제거** 기법(DIP 역전, 공통부 추출, 합치기, 이벤트) | 35, algorithm/18-scc | 다이어그램에는 계층이 있는데 코드는 도메인 → 컨트롤러 import. 모듈 A↔B 순환으로 A만 떼어 배포·테스트 불가. 규칙이 위키에만 있어 신규 입사자 PR마다 리뷰에서 반복 지적 | **순환 탐지(SCC)**, 경로 규칙 매칭 | ArchUnit User Guide · dependency-cruiser 문서 [?] · Ford 외 『Building Evolutionary Architectures』 2판 2장(fitness function) [?] | 권장 | 신규 |
| 37-complexity-metrics | 순환 복잡도(McCabe, 독립 경로 수 = 최소 테스트 수), 인지 복잡도(중첩 가중·선형 흐름 단절), 크기·중첩 깊이. **지표의 한계**(게이밍, 맥락 없음) | 04-clean-code, testing/06-test-design-techniques | 순환 복잡도 40인 메서드에 분기 누락 버그가 반복. 지표 게이트를 맞추려고 메서드를 잘게 쪼개 흐름이 5파일로 흩어짐(굿하트). 중첩 5단 `if` → 리뷰에서 else 누락 통과 | **제어 흐름 그래프(V = E − N + 2P)** | McCabe IEEE TSE 1976 [?] · Campbell "Cognitive Complexity" SonarSource 백서 v1.7 2023 | 권장 | 신규 (연결: `testing/15-coverage-and-its-limits`) |
| 38-code-forensics-hotspots | git 이력으로 보는 유지보수성: **핫스팟 = 변경 빈도 × 복잡도**, change coupling(함께 커밋되는 파일 = 숨은 결합), 지식 분포(bus factor), 부채 상환 우선순위 결정 | 37, engineering-practice/04-version-control-and-git-internals, engineering-practice/10-technical-debt | 전체 리팩터링 계획이 이력상 거의 안 바뀌는 파일에 인력을 소진. `Order.java`와 `OrderMapper.java`가 커밋의 90%에서 함께 바뀌는데 아무도 모름. 퇴사자 1명만 알던 모듈에서 장애 | 커밋 로그 집계(빈도), 공동 변경 행렬, 파일 쌍 지지도·신뢰도(연관 규칙) | Tornhill 『Your Code as a Crime Scene』 2판 2024 [?] · Tornhill 『Software Design X-Rays』 2018 [?] | 권장 | 신규 |
| 39-naming | 이름 = 추상화 수준의 첫 표현. 의도 드러내기, 도메인 어휘(ubiquitous language), 범위에 비례한 길이, 모호어(`data`·`info`·`manager`·`process`) 금지, 부정 boolean 피하기, 이름 붙이기 어렵다 = 책임이 불명확하다는 설계 신호 | 04-clean-code | `processData(list, flag)` → 리뷰어가 동작을 추측하다 버그 통과. `isNotDisabled` 이중 부정 → 조건 반전 버그. 같은 개념이 `user`·`member`·`customer`로 섞여 검색 누락, 한쪽만 수정 | — | Boswell–Foucher 『The Art of Readable Code』 2·3장 [?] · Hermans 『The Programmer's Brain』 8장 [?] · APOSD 14장 [?] | 필수 | 신규 (04에서 분할) |
| 40-function-design | 함수 하나 = 한 추상화 수준(SLAP). 인자 수와 인자 객체, **플래그 인자 금지**, CQS(명령은 상태를 바꾸고, 질의는 값만 돌려준다), 출력 인자 금지, 가드 절, 함수 길이보다 깊이 | 39 | `save(order, true, false, null)` → 호출처에서 의미 불명, 순서 실수. 조회처럼 보이는 `getBalance()`가 캐시 갱신·로그를 해서 두 번 부르면 결과가 다름. 한 함수에 SQL 문자열 조립과 할인 정책이 섞여 정책 변경 때 SQL 회귀 | — | Fowler "CommandQuerySeparation" 2005 · Meyer 『OOSC』 2판 [?] · Martin 『Clean Code』 3장 [?] · APOSD 9장 [?] | 필수 | 신규 (04에서 분할) |
| 41-comments-and-conventions | 주석이 필요한 자리: **왜**(결정·제약·외부 사정·버그 번호), 인터페이스 계약, 놀라운 동작. 불필요한 주석(what 반복·주석 처리된 코드·낡은 주석). 일관성: 팀 관례·포매터·린터로 논쟁 제거 | 40, 21-architecture-decision-records | 주석과 코드가 반대("재시도 3회" 주석, 코드는 5회) → 장애 때 잘못된 판단. `// 건드리지 마세요`만 있고 이유 없음 → 아무도 못 고침. 파일마다 스타일이 달라 diff의 절반이 포매팅 | — | APOSD 12·13장 [?] · Boswell–Foucher 5·6장 [?] · Google eng-practices "What to look for in a code review" | 권장 | 신규 (04에서 분할) |
| 42-designing-for-deletion | **지우기 쉬운 코드**: 결합이 적은 단위로 나누기, 확장보다 교체, 죽은 코드 찾기와 제거(미사용 탐지·호출 로그), 플래그 분기 코드 걷어내기, 주석 처리 코드 금지(git이 기억한다), 내부 deprecate 절차 | 30, 36 | 호출처가 없는 코드 30%가 남아 리팩터링 때마다 같이 고침. 끝난 실험 플래그의 `else` 분기가 몇 년 뒤 재활성(Knight Capital 유형). "혹시 몰라" 남긴 구 API를 신규 코드가 다시 호출 | 호출 그래프 도달성(루트에서 안 닿는 노드 = 죽은 코드) | tef "Write code that is easy to delete, not easy to extend" 2016 · Hodgson "Feature Toggles" (제거 절) | 권장 | 신규 (연결: gap-practical `reliability/35-feature-flag-lifecycle`) |
| 43-types-as-invariants | 원시 타입 집착 제거(ID·이메일·수량을 전용 타입으로), **parse, don't validate**(경계에서 한 번 파싱해 검증된 타입 반환), 불법 상태를 표현할 수 없게(합 타입, `sealed`, 필드 조합 대신 상태별 타입), 생성자·팩토리에서 불변식 확보 | 08-immutability-and-value-objects, language/06-type-systems, language/09-error-handling-models | `userId`와 `orderId`가 둘 다 `Long`이라 인자가 뒤바뀌어도 컴파일 통과, 남의 주문 조회. 같은 이메일 검증이 7곳에 있고 그중 1곳만 최신 규칙. `status=PAID`인데 `paidAt=null`인 행 → 정산 NPE | 합 타입(태그 유니언), 타입 상태(typestate) | King "Parse, don't validate" 2019 · Minsky "Effective ML" 2010 [?] · Fowler 『Refactoring』 2판 "Replace Primitive with Object" | 필수 | 신규 (연결: `domain-modeling/04`·`10`) |
| 44-absence-and-null-design | "없음"의 설계: null 반환 vs 빈 컬렉션 vs `Optional` vs Null Object vs 예외. Optional 남용(필드·인자), null 경계 정하기(경계에서 제거하고 안쪽은 non-null 가정), 기본값의 의미 | 07-error-handling-design, language/09-error-handling-models | 목록 조회가 `null`을 반환해 호출처 11곳 중 1곳이 체크 누락 → NPE. `Optional.get()` 무조건 호출로 NPE가 `NoSuchElementException`으로 이름만 바뀜. "없음"과 "0"을 구분 못 해 미입력 할인율을 0%로 저장 | Null Object(빈 구현) | Hoare "Null References: The Billion Dollar Mistake" QCon 2009 [?] · Bloch 『Effective Java』 3판 Item 54·55 [?] · Fowler 『Refactoring』 2판 "Introduce Special Case" | 권장 | 신규 |
| 45-taming-conditionals | if 지옥 해소의 **도구 선택**: 가드 절 → 분해 → 테이블(맵) 기반 → 다형성(Strategy·State) → 규칙 엔진, 각각을 언제 쓰나. 같은 `switch`가 여러 곳에 반복되는 것이 진짜 신호. 설정 조합 폭발 | 13-design-patterns-gof, 05-code-smells | 요금 계산 `if-else` 200줄에 고객 등급·지역·프로모션이 얽혀 새 등급 추가 시 분기 누락. `switch(type)`이 7개 파일에 복제돼 새 타입 추가 때 한 곳 누락 → 기본 분기로 조용히 처리. 반대로 단순 분기 3개를 클래스 5개로 → 흐름 추적 불가 | 결정 테이블, 룩업 맵(해시), 디스패치 테이블 | Fowler 『Refactoring』 2판 10장 "Replace Conditional with Polymorphism"·"Decompose Conditional" [?] · McConnell 『Code Complete』 2판 18장 "Table-Driven Methods" [?] | 필수 | 신규 |

### 서머리 예제 소재 — 나쁜 코드 → 개선 코드 (leaf당 1줄)

| slug | 나쁜 코드 → 개선 코드 |
|---|---|
| 27 | 주문 처리를 `parse → validate → price → save` 단계 모듈로 나눠 결제 수단 추가 때 전 단계 수정 → 결제 수단을 숨기는 `PaymentMethod` 모듈로 재분해해 수정 1곳 |
| 28 | `transfer(String from, String to, long amount)` 위치 결합 → `transfer(AccountId from, AccountId to, Money amount)` 타입 결합으로 약화. 상태 `3` → `OrderStatus.SHIPPED` |
| 29 | 알림 3종(메일·SMS·푸시)을 억지로 합친 `send(type, isUrgent, useTemplate, …)` → 인라인으로 되돌린 뒤, 진짜 공통 지식(수신 동의 확인)만 재추출 |
| 30 | 구현체 1개뿐인 `PaymentGatewayFactory` + `AbstractPaymentGateway` + 설정 키 10개 → 구체 클래스 1개. 두 번째 PG 요구가 왔을 때 인터페이스 추출 |
| 31 | 이름 변경·메서드 추출·버그 수정이 한 커밋 → 커밋 3개(tidy 2 + behavior 1)로 분리한 git 로그 전후 비교 |
| 32 | `new SmtpClient()`·`LocalDateTime.now()`를 내부에서 호출하는 `CouponService` → 생성자로 `MailSender`·`Clock` 주입, `main`/설정 한 곳에서 조립 |
| 33 | 리포지토리 조회 사이에 할인 계산이 끼어 있는 `applyDiscount()` → `load → calculate(순수) → save` 샌드위치. 계산은 mock 없이 값만으로 테스트 |
| 34 | 3천 줄 `processOrder()` 중간에 "VIP 무료 배송" 삽입 → `sprout`로 `FreeShippingPolicy.applies(order)`를 새로 만들어 TDD, 원 메서드엔 호출 1줄 |
| 35 | `controller/ service/ repository/` 최상위 구조 → `order/ payment/ member/` 최상위, 내부 클래스 package-private, 공개 진입점 1개 |
| 36 | "도메인은 인프라를 import하지 않는다"가 위키에만 → ArchUnit `noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat().resideInAPackage("..infra..")` 테스트 + 순환 1건을 인터페이스 역전으로 제거 |
| 37 | 중첩 5단 `for`/`if` 메서드(인지 복잡도 25) → 가드 절 + 추출로 8. 순환 복잡도로 필요한 최소 테스트 수 계산 |
| 38 | "전체 리팩터링" 계획 → `git log --numstat` 집계로 상위 핫스팟 5개와 함께 바뀌는 파일 쌍만 우선 처리한 계획 |
| 39 | `List<Map<String,Object>> getData(boolean f)` → `List<OverdueInvoice> findOverdueInvoices(ReminderPolicy policy)` |
| 40 | `createUser(name, email, true, false, null)` + 값을 바꾸는 `getCount()` → 인자 객체 `NewUserRequest` + `createAdmin()`/`createMember()` 분리, `count()`는 순수 질의·`increment()`는 명령 |
| 41 | `// i를 1 증가` 류 what 주석과 주석 처리된 옛 코드 → 삭제 + `// PG사 X는 3초 안에 응답 없으면 이중 승인한다(장애 #123) — 그래서 멱등 키 필수` why 주석 |
| 42 | 1년 된 실험 플래그 `if (flags.newCheckout) {…} else {…}` 양쪽 유지 → 승자 분기만 남기고 플래그·설정·테스트 동시 삭제. 도달성 분석으로 죽은 메서드 제거 |
| 43 | `Order { String status; LocalDateTime paidAt; String cancelReason; }` → `sealed interface Order permits Pending, Paid(paidAt), Cancelled(reason)`. 컨트롤러 경계에서 `Email.parse(raw)` 1회 |
| 44 | `List<Coupon> find(...)`가 `null` 반환 + `Optional<Discount>` 필드 → 빈 리스트 반환, 필드는 `Discount.NONE`(Special Case), 경계에서만 `Optional` |
| 45 | 등급·지역별 배송비 `if-else` 200줄 → 등급별 `ShippingFeePolicy` 전략 + 지역 요율 테이블(`Map<Region, Rate>`). 반례로 분기 3개짜리는 그대로 두는 것이 맞는 경우 |

### 권장 학습 순서 (§12 전체, 갱신안)

01 → 02 → 03 → **27 → 28** → 04 → **39 → 40 → 41** → 05 → **29 → 30** → 06 → **31** → 07 → **44** → 08 → **43** → 09 → 10 → 11 → **32 → 33** → 12 → 13 → **45** → 14 → 15 → 16 → **35 → 36** → 17 → 18 → 20 → 21 → 22 → 19 → **34** → (gap-practical 25·26) → **37 → 38 → 42** → 23 → 24

### 기존 leaf 조정 (신규 아님)

- `23-design-symptom-index`: 역색인 증상에 다음을 추가한다.
  - "공통 함수 인자만 계속 늘어남" → 29
  - "테스트에 DB·mock 도배" → 32·33
  - "기능 하나에 폴더 4개" → 35
  - "리팩터링 어디부터?" → 38
  - "플래그·죽은 코드 누적" → 42
  - "불법 상태 행" → 43
  - "NPE" → 44
  - "switch 복제" → 45
- `testing/16-characterization-tests-legacy`: 요지를 "안전망(특성 테스트·seam 찾기)"으로 좁히고, 변경 기법은 software-design/34로 넘긴다. 선행 관계는 16 → 34다.
- `02-modularity-coupling-cohesion`: 📚의 Parnas 1972를 유지한다. "분해 기준" 절은 27로 넘긴다는 메모를 단다.

---

## 3. 04·05·06을 쪼갤까

### 04-clean-code — **쪼갠다** (근거: 표와 기존 노트의 불일치)

- 커리큘럼 표의 04 요지는 "이름·함수·주석·포매팅"(Martin 『Clean Code』)이다.
- 그러나 기존 노트 `cs/engineering/clean-code/2-summary.md`(635줄)의 실제 내용은 **CLEAN 5속성**(Cohesive·Loosely coupled·Encapsulated·Assertive·Nonredundant)과 그 긴장 관계다. 이름·함수·주석 절은 **없다**.
- 조치:
  1. `04-clean-code`의 요지를 **"좋은 코드의 5속성(CLEAN)과 속성 간 긴장 — 품질 검사표"**로 바꾸고 기존 노트를 그대로 이식한다. 선행은 02를 권장한다. 내용이 결합·응집·캡슐화이므로 01보다 02가 맞다.
  2. 📚도 바꾼다. Martin 『Clean Code』가 아니라 기존 원고, 그리고 Shalloway–Trott 『Design Patterns Explained』의 CLEAN 두문자어 [?]다(원고 출처는 jun-bank 노트이고, 두문자어 원전은 미확인이다).
  3. 원래 요지였던 이름·함수·주석은 **39·40·41로 분리**한다. 한 leaf에 넣으면 질문이 10개를 넘는다(§0.4 크기 규칙).
- 04와 겹치는 부분(E ↔ 09 캡슐화, A ↔ domain-modeling/09 빈약한 모델, N ↔ 29 DRY)은 **연결**로만 처리한다. 04는 "검사표" 관점을 유지한다.

### 05-code-smells — **쪼개지 않는다, 조건부 분할**

- Fowler 2판 스멜은 24종이다 [?]. 한 편에 전부 넣으면 질문이 10개를 넘을 위험이 있다.
- 우선 1편으로 두고 **Mäntylä 분류**(Bloaters·OO Abusers·Change Preventers·Dispensables·Couplers) [?]로 묶는다. 이렇게 하면 질문 5~8개로 덮인다. 각 스멜은 대응 리팩터링과 해당 신규 leaf(29·43·45 등)로 링크한다.
- 서머리 작성 때 질문이 10개를 넘으면 `05a-change-preventers-and-couplers`와 `05b-bloaters-and-dispensables`로 나눈다. 앞쪽이 유지보수성과 직결되므로 먼저 쓴다.

### 06-refactoring — **쪼개지 않는다** (이미 주변으로 분산됨)

- 06은 "동작 보존 변환의 기제": 작은 단계, 테스트 안전망, 대표 리팩터링 카탈로그만 담는다.
- 판단층은 신규 leaf가 가져간다.
  - 언제·어떻게 커밋하나 → 31 Tidy First
  - 테스트 없는 코드 → 34 레거시 기법
  - 어디부터 → 38 핫스팟
  - 추상화 되돌리기 → 29
- 06의 ⚠ 칸 "큰 한 방 리팩터링 → 머지 지옥"은 31·34와 연결한다.

---

## 4. 확인하지 못한 것 (`[?]`)

- 장 번호 전부: Löwy 『Righting Software』, Page-Jones 1995, Feathers(2·4·6·25장), Beck 『Tidy First?』 부 구성, Brown "Missing Chapter"의 장 번호(34장), Boswell–Foucher, Hermans 8장, APOSD 9·12·13·14장, McConnell 18장, Bloch Item 54·55, Ford 외 2판, Tornhill 2판 출간 연도(2024 추정), Khorikov 7장, Martin 『Clean Code』 3장.
- Weirich 강연 제목·연도("Grand Unified Theory of Software Design", 2009 추정).
- CLEAN 두문자어 원전(Shalloway–Trott 추정) — 기존 원고의 출처를 먼저 확인할 것.
- Fowler 2판 스멜 개수(24)와 Mäntylä 2003 분류명.
- dependency-cruiser·import-linter 규칙 문법 세부.
- Minsky "Effective ML"(2010 Jane Street 강연)의 원문 표현.
- 등급은 교수 판단 초안이다.

---

## 5. 출처 (이번 조사에서 검색으로 확인)

- Parnas 1972 원문: http://sunnyday.mit.edu/16.355/parnas-criteria.html · https://blog.acolyer.org/2016/09/05/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/
- Löwy 『Righting Software』(변동성 기반 분해): https://rightingsoftware.org/ · https://www.infoq.com/articles/book-review-righting-software/
- Connascence: https://connascence.io/pages/about.html · https://en.wikipedia.org/wiki/Connascence
- Metz "The Wrong Abstraction" 2016: https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction
- Rule of three(Roberts, Fowler 『Refactoring』): https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)
- Fowler "Yagni": https://www.martinfowler.com/bliki/Yagni.html
- Fowler "BeckDesignRules": https://www.martinfowler.com/bliki/BeckDesignRules.html
- Beck 『Tidy First?』 2023: https://www.oreilly.com/library/view/tidy-first/9781098151232/ [?] · 서평 https://henrikwarne.com/2024/01/10/tidy-first/
- Bernhardt "Boundaries" 2012: https://www.destroyallsoftware.com/talks/boundaries
- Seemann–van Deursen DI 책: https://www.manning.com/books/dependency-injection-principles-practices-patterns
- Feathers 요약(sprout·wrap·seam): https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/
- Fowler "ParallelChange": https://martinfowler.com/bliki/ParallelChange.html
- Fowler "CommandQuerySeparation": https://martinfowler.com/bliki/CommandQuerySeparation.html
- Brown "Package by component": https://simonbrown.je/modular-monolith/
- ArchUnit User Guide: https://www.archunit.org/userguide/html/000_Index.html
- Campbell "Cognitive Complexity" 백서: https://www.sonarsource.com/docs/CognitiveComplexity.pdf
- Tornhill 『Your Code as a Crime Scene』 2판: https://pragprog.com/titles/atcrime2/your-code-as-a-crime-scene-second-edition/
- tef "Write code that is easy to delete": https://programmingisterrible.com/post/139222674273/write-code-that-is-easy-to-delete-not-easy-to
- King "Parse, don't validate": https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
- Make illegal states unrepresentable(Minsky): https://functional-architecture.org/make_illegal_states_unrepresentable/
- Fowler 리팩터링 카탈로그: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
- Boswell–Foucher, Hermans: https://www.manning.com/books/the-programmers-brain
