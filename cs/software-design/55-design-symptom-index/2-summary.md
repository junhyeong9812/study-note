# software-design/55-design-symptom-index — 증상 사전: diff·컴파일러·기동·런타임 메시지·조용한 값 오류 → 설계 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

소프트웨어 설계 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"세율이 다섯 모듈에 복제돼 있다 → 세율 변경에 파일 5개 → 하나를 빠뜨리면 1원 차이"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 PR 하나(`12 files changed`, 예시), 메시지 한 줄(`required a single bean, but 2 were found`), 고객 문의 한 건("환불 금액이 1원 달라요")뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                              이 노트 (역방향)
  설계 결정 --> 결합·누출 --> 변경 시 증상          증상 --> 언제 드러났나 --> 흔한 설계 원인 --> 첫 진단 --> leaf
  "결제 수단 분기가 계층마다 있다"                 "수단 추가 PR이 파일 12개다. 사본인가, 통과 계층인가부터"
```

쉬운 예: 자동차 정비소의 증상표다.\
"브레이크 밟으면 끽 소리"만으로 부품을 갈지 않는다. 표가 "먼저 패드 두께를 재라"고 정해 준다.\
표는 고치지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
"작은 요구에 파일 N개"라면 먼저 바뀐 파일들을 둘로 가른다.\
같은 지식의 사본(같은 `switch`, 같은 세율)이면 **흩어진 결정**이 원인이다([10-1](../10-code-smells/2-summary.md)).\
위임만 하는 인터페이스·팩토리·매퍼라면 **쓰이지 않는 간접 계층**이 원인이다([12-1](../12-simple-design-and-yagni/2-summary.md)).\
같은 증상인데 처방은 정반대다.

실무 예:
- 설계 영역에서 "깨졌다"는 대개 크래시가 아니다. **변경 비용**(PR 크기·충돌·리뷰 시간)과 **조용한 결합**(에러 없는 값 차이)으로 보인다(커리큘럼 §12 머리말).
- 같은 결함이 설계에 따라 **다른 시점**에 보인다. 새 상태의 처리 누락은 `default` 분기가 있으면 운영의 조용한 값 오류로, `default` 없는 `switch` 식이면 컴파일 오류로 보인다.
- 메시지가 같아도 원인이 다르다. `NullPointerException`의 `because "this.repo" is null`은 null 검사 누락이 아니라 CGLIB 프록시의 final 메서드일 수 있다([33-2](../33-aop-and-proxies/2-summary.md)).

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: `NN`번 노트 「장애 시나리오와 대처」의 `k`번째 시나리오다. 예: `25-3` = 25번 노트의 시나리오 3(순환 주입).

## 동작·원리

### 0. 증상이 드러나는 시점 — 늦을수록 비싸다

```text
  변경 요청
     │
     ▼
  ① PR·diff·병합      "파일 12개", CONFLICT, 리뷰 코멘트 반복           ← 변경 비용이 직접 보이는 곳
     │
     ▼
  ② 컴파일·정적 검사   javac 오류, ArchUnit·jdeps·PMD 위반               ← 설계가 실수를 여기로 당길 수 있다
     │
     ▼
  ③ 기동             BeanCurrentlyInCreation, CGLIB 실패, 빈 2개      ← 조립(composition root) 오류
     │
     ▼
  ④ 테스트           목 도배, 순서 따라 실패, 날짜 따라 실패            ← 숨은 의존·숨은 입력
     │
     ▼
  ⑤ 운영 — 예외      NPE, UnexpectedRollback, 404, 타임아웃            ← 메시지가 있으면 아직 운이 좋다
     │
     ▼
  ⑥ 운영 — 조용함    1원 차이, "기타" 라벨, 남의 주문, 롤백 안 된 행    ← 대사·고객 문의로 며칠 뒤 발견
```

- 같은 결함이 설계에 따라 ①~⑥ 중 다른 칸에 나타난다. 좋은 설계 결정 상당수는 결함을 **위 칸으로 끌어올리는** 일이다.

| 결함 | 아래 칸에서 보일 때 | 위 칸으로 당긴 설계 | 당긴 뒤 보이는 형태 | leaf |
|---|---|---|---|---|
| 새 상태·타입 처리 누락 | ⑥ `default`가 받아 `label=기타` | `sealed` + `default` 없는 `switch` 식 | ② `the switch expression does not cover all possible input values` | [28-2](../28-taming-conditionals/2-summary.md) · [24-5](../24-types-as-invariants/2-summary.md) |
| 같은 타입 인자 뒤바뀜 | ⑥ 반대 송금·남의 주문 | `UserId`·`OrderId` 전용 타입 | ② `incompatible types` | [05-1](../05-connascence/2-summary.md) · [24-1](../24-types-as-invariants/2-summary.md) |
| 빈 설정 누락 | ⑤ 첫 호출 때 `NoSuchBeanDefinitionException` | Service Locator → 생성자 주입 | ③ 기동 실패 | [25-2](../25-dependency-injection-and-composition-root/2-summary.md) |
| 계층 우회 import | ⑥ 권한 검사 빠진 화면 | ArchUnit 계층 규칙 | ② 규칙 테스트 실패 | [40-1](../40-codebase-structure/2-summary.md) · [41-3](../41-architecture-fitness-rules/2-summary.md) |
| 필수 설정 없음 | ⑥ 기본값(개발 DB)으로 떠서 엉뚱한 곳에 저장 | 배포별 값에 기본값을 두지 않음 | ③ 기동 실패(종료 코드 1) | [48-4](../48-configuration-and-12factor/2-summary.md) |
| 불법 상태 조합 | ⑤ 새벽 배치 NPE / ⑥ 이상한 행 | 상태별 타입 + DB `CHECK` | ② 컴파일 오류 / 저장 시 `violates check constraint` | [24-3](../24-types-as-invariants/2-summary.md) |

- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: 메시지 전체(`Caused by`까지), 도구·프레임워크 버전, PR의 `--stat`.
  - **시점과 모양**: ①~⑥ 중 어디서 처음 보였나. 에러가 있나 없나. 특정 변경·배포·날짜와 겹치나.

### 1. 변경할 때 보이는 증상 — diff·이력·리뷰

| 증상 | 보이는 것 | 흔한 설계 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **작은 변경에 파일 N개** | `git show --stat`의 `N files changed`가 요구 크기보다 크다. 같은 묶음이 같은 유형의 커밋마다 반복된다 | (가) 같은 결정의 사본이 N곳(Shotgun Surgery, 단계별 분해에 퍼진 `switch`) (나) 위임만 하는 인터페이스·팩토리·매퍼 계층(과설계) | 바뀐 파일을 "사본"과 "통과 계층"으로 가른다. 같은 유형의 과거 커밋 `--stat`과 비교 | (가) [01-1](../01-complexity/2-summary.md) · [04-1](../04-decompose-by-change/2-summary.md) · [10-1](../10-code-smells/2-summary.md) (나) [03-1](../03-deep-modules-and-abstraction/2-summary.md) · [10-5](../10-code-smells/2-summary.md) · [12-1](../12-simple-design-and-yagni/2-summary.md) · [22-5](../22-solid/2-summary.md) · [27-1](../27-design-patterns-gof/2-summary.md) · [38-4](../38-layered-hexagonal-clean/2-summary.md) · [44-3](../44-architecture-in-code/2-summary.md) |
| **값 하나 내려보내는데 시그니처 수십 개** | 로케일·테넌트 ID·요청 ID를 추가하는 PR이, 맨 아래에서만 쓰는 값 때문에 중간 메서드 시그니처를 전부 바꿈 | 통과 변수(pass-through variable) | 그 인자를 실제로 읽는 메서드 수 vs 받아서 넘기기만 하는 메서드 수 | [03-2](../03-deep-modules-and-abstraction/2-summary.md) |
| **화면 기능 하나에 하위 모듈 담당자까지 리뷰** | 하위 모듈의 공개 메서드 수가 화면 기능 수와 함께 늘어남 | 하위 모듈이 상위 개념으로 만든 특수 목적 인터페이스 | 하위 모듈 공개 메서드 이름이 화면 용어인가 | [03-4](../03-deep-modules-and-abstraction/2-summary.md) |
| **호출처 검색이 0건인데 실행됨** | IDE의 Find Usages 0건, 스택 맨 아래가 프레임워크 클래스뿐 | 제어 역전 — 리플렉션·콜백 목록·후처리기가 부름, 어노테이션이 동작을 만듦 | 스택 트레이스의 프레임워크 진입점, 그 확장 지점 문서 | [32-1](../32-inversion-of-control-and-framework-flow/2-summary.md) · [35-1](../35-annotation-and-metadata-programming/2-summary.md) |
| **기능 하나에 폴더 4개** | `git diff --dirstat`이 `controller/`·`service/`·`repository/`·`dto/`로 갈린다. 리뷰어가 여러 팀 | 기술 역할로 묶은 패키지(by layer). 함께 바뀌는 것이 흩어짐 | `git diff --dirstat=files,0 HEAD~1` | [40-2](../40-codebase-structure/2-summary.md) · [39-4](../39-component-principles/2-summary.md) |
| **한 클래스에서 병합 충돌 반복** | `CONFLICT (content): Merge conflict in OrderManager.java`. 변경 빈도 1위 파일이 무관한 기능 PR마다 등장 | God Object·Divergent Change(변경 이유 여럿), 잡동사니 `CommonUtils`·`util` | 변경 빈도 상위 파일의 커밋 메시지를 이유별로 분류 | [10-2](../10-code-smells/2-summary.md) · [31-3](../31-antipatterns/2-summary.md) · [22-4](../22-solid/2-summary.md) · [02-3](../02-modularity-coupling-cohesion/2-summary.md) · [40-3](../40-codebase-structure/2-summary.md) |
| **두 파일 중 하나를 늘 깜빡** | "OrderMapper 수정 누락" 핫픽스가 이력에 반복. import 그래프에는 간선이 없다 | 같은 지식(필드 목록)이 두 곳 — 숨은 결합 | 공동 변경(change coupling) 집계 | [53-2](../53-code-forensics-hotspots/2-summary.md) · [43-5](../43-data-across-boundaries/2-summary.md) |
| **이 클래스는 아무도 못 건드림** | 공통 모듈 PR이 몇 주씩 열림, `XxxUtil2` 증가. `// 건드리지 마세요`만 있음. 작성자 1명 | 우연한 모양 공유로 묶인 공통 모듈, 이유 없는 경고 주석, 지식 섬, Big Ball of Mud | 작성자 분포(`git log --format=%aN -- <파일> \| sort \| uniq -c`), 승인자 수, `git blame`으로 경고의 원래 이유 | [11-2](../11-when-to-abstract/2-summary.md) · [09-2](../09-comments-and-conventions/2-summary.md) · [53-3](../53-code-forensics-hotspots/2-summary.md) · [31-4](../31-antipatterns/2-summary.md) · [29-3](../29-refactoring-to-patterns/2-summary.md) |
| **공통 함수 인자만 계속 늘어남** | boolean·type 인자 5개, 내부 `if` 12개. `process(order, true, false, 2)`. 한 호출처 수정이 다른 호출처 회귀 | 잘못된 추상화(다른 지식을 한 함수에), 제어 결합, 플래그 인자 | 호출처별 인자 조합을 grep으로 모아 본다 → 인라인 후 재추출 | [11-1](../11-when-to-abstract/2-summary.md) · [02-4](../02-modularity-coupling-cohesion/2-summary.md) · [08-1](../08-function-design/2-summary.md) · [07-1](../07-naming/2-summary.md) |
| **배포를 같이 해야 함** | 릴리스 노트에 "A·B·C 동시 배포". 공통 라이브러리 버전 올림 PR이 서비스 수만큼. 모듈 하나 고치는데 넷 다 빌드 | 분산 모놀리스(공유 도메인 라이브러리·공유 DB·버전 없는 계약), 컴포넌트 순환, 단계별 분해가 형식을 공유 | 서비스·모듈 간 공동 변경 집계, 빌드 그래프 순환 | [45-1](../45-monolith-vs-microservices/2-summary.md) · [45-2](../45-monolith-vs-microservices/2-summary.md) · [06-5](../06-clean-code/2-summary.md) · [39-1](../39-component-principles/2-summary.md) · [39-3](../39-component-principles/2-summary.md) · [04-2](../04-decompose-by-change/2-summary.md) |
| **충돌 없이 병합했는데 빌드가 깨짐** | `git merge` 충돌 0 뒤에 `cannot find symbol`·`incompatible types` | 큰 한 방 리팩터링, 원자적 시그니처 변경(중간 상태 없음) | 깨진 호출처가 옛 이름·옛 시그니처를 쓰나 | [13-2](../13-refactoring/2-summary.md) · [51-2](../51-legacy-change-techniques/2-summary.md) |
| **revert했더니 빌드가 깨짐** | `git revert`는 충돌 없이 끝났는데 `cannot find symbol` | 구조 변경과 동작 변경이 한 커밋 | 되돌린 커밋에 rename이 섞였나 | [14-2](../14-tidy-first/2-summary.md) · [13-4](../13-refactoring/2-summary.md) |
| **1줄 수정 PR이 56줄 diff** | `31 insertions(+), 25 deletions(-)` | 팀 포매터 없음 | 공백 무시 diff(`git diff -w`)와 비교 | [09-3](../09-comments-and-conventions/2-summary.md) |
| **리팩터링 어디부터?** | 6개월 리팩터링 뒤에도 속도·버그 수가 그대로 | 크기·나이로 고름. 안 바뀌는 큰 파일에 인력 소진 | 핫스팟 = 변경 빈도 × 복잡도 | [53-1](../53-code-forensics-hotspots/2-summary.md) · [31-4](../31-antipatterns/2-summary.md) · [01-4](../01-complexity/2-summary.md) |
| **플래그·죽은 코드 누적** | 시그니처 변경 때 안 쓰는 클래스까지 고침. 끝난 플래그의 `else`가 남음. 주석 처리 코드. 전환 1년 뒤에도 구 경로 호출 | 기능 종료 때 코드를 안 지움, 플래그 수명 관리 없음 | 호출 그래프 도달성 + 실행 시 관측(호출 카운터·`-Xlog:class+load`) | [54-1](../54-designing-for-deletion/2-summary.md) · [54-2](../54-designing-for-deletion/2-summary.md) · [54-5](../54-designing-for-deletion/2-summary.md) · [09-4](../09-comments-and-conventions/2-summary.md) · [28-4](../28-taming-conditionals/2-summary.md) · [50-4](../50-legacy-migration-strangler-fig/2-summary.md) |
| **확장점 시그니처 변경이 구현 전부를 건드림** | 계약 파일 PR에 플러그인·전략 N개가 묶임 | 추측한 확장점이 실제 축과 다름, 계약의 변동 | 최근 계약 변경 횟수 vs 구현 추가 횟수 | [12-3](../12-simple-design-and-yagni/2-summary.md) · [37-3](../37-architecture-styles/2-summary.md) · [36-5](../36-extension-points-and-plugins/2-summary.md) |
| **같은 논쟁·같은 설정 값이 왕복** | `git log -S`로 같은 값의 추가·삭제가 반복 | 결정 근거 소실 | 그 값의 커밋 이력, ADR 유무 | [47-1](../47-architecture-decision-records/2-summary.md) · [47-2](../47-architecture-decision-records/2-summary.md) |
| **PR이 2주째 열림** | 리베이스마다 충돌, "고치는 김에" 커밋이 계속 붙음 | 정리 범위에 상한 없음 | 정리 커밋과 기능 커밋 비율 | [14-3](../14-tidy-first/2-summary.md) |

- "파일 N개"는 숫자 자체보다 **같은 유형의 요구가 매번 같은 N개를 건드리는가**가 신호다. 한 번 넓게 바뀐 것은 경계를 옮기는 정리일 수도 있다.

### 2. 테스트에서 보이는 증상

| 증상 | 보이는 것 | 흔한 설계 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **테스트를 쓸 수 없다** | `ConnectException: Connection refused`(CI에서만), 테스트에 실제 DB·SMTP 기동 스크립트. 하네스에서 객체 생성조차 안 됨. 컨트롤러 테스트에 HTTP·세션·DB | 정책 클래스가 세부 구현을 `new`로 만듦(DIP 부재), 숨은 의존(DB 연결)이 메서드 안에, 컨트롤러에 규칙 집중 | 생성자·메서드 안의 `new`·정적 호출 grep | [22-2](../22-solid/2-summary.md) · [38-1](../38-layered-hexagonal-clean/2-summary.md) · [51-1](../51-legacy-change-techniques/2-summary.md) · [42-1](../42-ui-architecture-patterns/2-summary.md) |
| **테스트에 DB·mock 도배** | `@SpringBootTest`·`@MockBean`·`mockStatic` 다수, Testcontainers로 규칙 하나 시험 | 변동 의존을 `new`·정적 호출로 숨김(Control Freak·Ambient Context), 계산이 I/O 사이에 낌 | 규칙 하나 시험에 필요한 목 개수 | [25-4](../25-dependency-injection-and-composition-root/2-summary.md) · [26-1](../26-functional-core-imperative-shell/2-summary.md) |
| **리팩터링마다 테스트 대량 실패, 동작은 그대로** | Mockito 5.20.0: `VerificationInOrderFailure … Wanted but not invoked`, `TooManyActualInvocations` | 테스트가 결과 대신 호출 순서를 검증(깨지기 쉬운 테스트) | 실패한 단언이 값인가 상호작용인가 | [26-1](../26-functional-core-imperative-shell/2-summary.md) |
| **날짜에 따라 실패** | 말일·윤년에만 "처리 0건", 평소 CI 초록. "밤 11시 59분 주문만" 재현 불가 | `LocalDate.now()`·난수 직접 호출(숨은 입력) | 코드에서 `now()`·`random` 호출 위치 | [25-5](../25-dependency-injection-and-composition-root/2-summary.md) · [26-3](../26-functional-core-imperative-shell/2-summary.md) |
| **실행 순서에 따라 실패** | 단독 실행은 초록. `expected: <10000> but was: <8000>` | 가변 전역 싱글턴 | 실패 테스트 앞에 돈 테스트가 무엇을 바꿨나 | [31-1](../31-antipatterns/2-summary.md) · [29-4](../29-refactoring-to-patterns/2-summary.md) |
| **테스트 초록인데 운영 값이 다름** | 행복 경로 테스트 초록. 새 타입을 모르는 테스트 `tests: 6 pass, 0 fail`인데 `label=?`. 새 코드 동작을 기대값으로 적은 테스트 | 동작 보존을 고정하지 않은 리팩터링, `default`가 있는 분기 | 리팩터링 전 출력과의 지문 비교(골든 마스터·특성 테스트) | [13-1](../13-refactoring/2-summary.md) · [29-2](../29-refactoring-to-patterns/2-summary.md) · [51-3](../51-legacy-change-techniques/2-summary.md) · [14-4](../14-tidy-first/2-summary.md) · [50-3](../50-legacy-migration-strangler-fig/2-summary.md) |
| **부모 1파일 수정에 하위 테스트 N개 실패** | 골든·스냅샷 테스트가 하위 개수만큼 깨짐(32 실험 E: 3/3) | 템플릿 메서드 골격·기반 클래스 공유(취약한 기반 클래스) | 깨진 테스트가 모두 같은 부모를 상속하나 | [32-2](../32-inversion-of-control-and-framework-flow/2-summary.md) · [21-1](../21-composition-over-inheritance/2-summary.md) |
| **CI와 운영의 검사 결과가 다름** | 테스트에서는 `AssertionError`, 운영에서는 통과해 `qty=-3` | 사전조건을 `assert`로만(JVM 기본은 꺼짐) | 실행 옵션의 `-ea` 유무 | [23-2](../23-design-by-contract/2-summary.md) |
| **테스트는 통과, 운영에서만 실패** | 테스트 클래스패스에 가짜 구현 JAR가 먼저 잡혀 있었다 | link seam(enabling point가 코드 밖) | 테스트·운영 클래스패스 비교 | [51-5](../51-legacy-change-techniques/2-summary.md) |

### 3. 컴파일·정적 검사에서 보이는 메시지 — 좋은 신호와 나쁜 신호

| 메시지 (도구·버전) | 뜻 | 신호 | leaf |
|---|---|---|---|
| `error: the switch expression does not cover all possible input values` (javac, JDK 21.0.12 — 아래 실행 확인) | `sealed`·enum의 새 경우를 `switch` 식이 다루지 않음 | **좋은 신호** — 누락이 ⑥에서 ②로 올라왔다 | [24-5](../24-types-as-invariants/2-summary.md) · [28-2](../28-taming-conditionals/2-summary.md) · [16-5](../16-error-strategy-exceptions-vs-results/2-summary.md) |
| `… is not abstract and does not override abstract method …` (javac) | 다형성으로 모은 뒤 새 타입이 메서드를 구현하지 않음 / SPI 계약에 메서드 추가 | 앞은 좋은 신호, 뒤는 계약 변경이 구현자 전부를 깸 | [29-2](../29-refactoring-to-patterns/2-summary.md) · [36-5](../36-extension-points-and-plugins/2-summary.md) |
| `incompatible types` (javac) | 전용 타입·enum이 인자 뒤바뀜을 막음 / 병합 뒤 남은 옛 호출 | 앞은 좋은 신호, 뒤는 원자적 시그니처 변경 | [05-1](../05-connascence/2-summary.md) · [08-1](../08-function-design/2-summary.md) · [24-1](../24-types-as-invariants/2-summary.md) · [51-2](../51-legacy-change-techniques/2-summary.md) |
| javac 오류가 **바꾼 파일이 아닌 호출자 파일들**에 줄줄이 | 내부 표현이 공개 시그니처에 실려 있었다 | 나쁜 신호(정보 누출) | [02-1](../02-modularity-coupling-cohesion/2-summary.md) |
| `error: cyclic dependence involving a` (javac, JPMS) / 모듈을 따로 빌드하면 `package comp.web does not exist` | 패키지 수준에 숨어 있던 순환이 모듈 경계에서 드러남 | 나쁜 신호(분리 불가) | [40-4](../40-codebase-structure/2-summary.md) · [39-1](../39-component-principles/2-summary.md) |
| `Cycle detected: Slice domain -> …`, `Method <…domain…> gets field <…web…>` (ArchUnit 1.5.1) | 도메인이 웹을 참조, 슬라이스 순환 | 규칙이 제 역할을 함. 위반의 소유자를 찾을 차례 | [41-1](../41-architecture-fitness-rules/2-summary.md) · [38-2](../38-layered-hexagonal-clean/2-summary.md) · [39-1](../39-component-principles/2-summary.md) |
| `error no-circular: src/billing/invoice.js → …` (dependency-cruiser 18.5.0) | JS 모듈 순환. 프로그램은 정상 실행된다 | 나쁜 신호(따로 테스트·배포 불가) | [41-2](../41-architecture-fitness-rules/2-summary.md) |
| jdeps에 `com.shop.web -> com.shop.repository` | 컨트롤러가 리포지토리를 직접 참조(서비스 계층 우회) | 나쁜 신호. 컴파일·테스트는 통과한다 | [40-1](../40-codebase-structure/2-summary.md) |
| `[removal]` 경고인데 빌드 `exit=0` | 제거 예정 API를 신규 코드가 호출 | 경고에 그친 deprecate | [54-3](../54-designing-for-deletion/2-summary.md) |
| `Unmapped target properties` 경고 한 줄 (MapStruct 1.6.3) | 처리기 순서 때문에 Lombok 게터를 못 봄 → 필드 null | 경고를 오류로 다루지 않으면 ⑥로 내려감 | [35-5](../35-annotation-and-metadata-programming/2-summary.md) |
| PMD `CyclomaticComplexity`·`AvoidDeeplyNestedIfStmts` 보고 (PMD 7.28.0) | 결정이 많거나 중첩이 깊음 | 후보일 뿐. 게이트로 강제하면 잘게 쪼개 흐름이 흩어짐 | [52-1](../52-complexity-metrics/2-summary.md) · [52-3](../52-complexity-metrics/2-summary.md) · [52-2](../52-complexity-metrics/2-summary.md) |
| 정적 분석 **0건** | 도구가 보는 스멜이 없다는 뜻일 뿐 | Shotgun·Divergent는 소스 한 시점에 없고(이력에 있다), Feature Envy·Repeated Switches는 10 실험에서 돌린 PMD 규칙이 보지 않았다(10 실험 B: 심은 8개 중 4개만 보고, 타입 정보를 주면 5개) | [10-4](../10-code-smells/2-summary.md) · [07-2](../07-naming/2-summary.md) |
| ArchUnit 동결 위반 0건인데 새 위반이 들어감 | CI가 동결 저장소를 매번 새로 만듦(`allowStoreCreation=true`) | 규칙이 무력화됨 | [41-4](../41-architecture-fitness-rules/2-summary.md) |

### 4. 기동에서 보이는 증상 — "빈 하나 추가했더니 안 뜬다"

| 메시지 (실험 버전) | 흔한 설계 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `BeanCurrentlyInCreationException: … Requested bean is currently in creation: Is there an unresolvable circular reference or an asynchronous initialization dependency?` (Spring Framework 6.2.11) | A→B→A 순환 주입. 한 클래스가 두 책임을 가져 서로의 일부가 필요함 | 메시지의 빈 이름으로 순환 고리를 그린다 | [25-3](../25-dependency-injection-and-composition-root/2-summary.md) |
| `APPLICATION FAILED TO START` … `required a single bean, but 2 were found` (Spring Boot 3.5.6) | 자동 설정의 `@ConditionalOnMissingBean` 대상이 구현 클래스라 사용자의 다른 구현을 못 봄 | `--debug` 조건 평가 보고서 | [36-2](../36-extension-points-and-plugins/2-summary.md) |
| `BeanCreationException … Could not generate CGLIB subclass of class …`, 근본 원인 `IllegalArgumentException: Cannot subclass final class` (Spring Framework 6.2.11) | 애스펙트가 걸리는 빈이 final 클래스 | 그 클래스에 걸린 어드바이스(`@Transactional` 등) | [33-3](../33-aop-and-proxies/2-summary.md) |
| `NoSuchBeanDefinitionException`(구현 타입으로 조회) / `BeanNotOfRequiredTypeException`(이름 + 구현 타입) | JDK 동적 프록시는 인터페이스만 구현한다 | 주입 지점의 타입이 구현 클래스인가 | [33-5](../33-aop-and-proxies/2-summary.md) |
| 필수 설정 누락으로 기동 실패(종료 코드 1) | 설계가 의도한 실패. 배포 매니페스트 누락 | 빠진 키 | [48-4](../48-configuration-and-12factor/2-summary.md) |

- 기동은 되는데 **첫 호출**에서 `NoSuchBeanDefinitionException: No qualifying bean of type '…' available`이 난다면 Service Locator·`getBean()`이다. 생성자 주입으로 바꾸면 위 표(기동 실패)로 올라온다([25-2](../25-dependency-injection-and-composition-root/2-summary.md)).
- 기동 시간이 서비스가 커질수록 늘어나는 것은 메시지가 없는 기동 증상이다. 기동 시 스캔·리플렉션이 원인 후보다([35-3](../35-annotation-and-metadata-programming/2-summary.md)).

### 5. 런타임 예외 — 메시지에서 원인 자리 찾기

**NullPointerException — `because` 뒤를 읽는다** (helpful NPE, JEP 358. JEP 문서: 지역 변수는 지역 변수 표가 있으면 변수 이름, 없으면 `<local i>`. JDK 21.0.12에서 `javac`로 컴파일하면 `<local0>`, `javac -g`면 변수 이름이 나왔다 — 아래 실행 확인)

| `because …` 부분 | 흔한 설계 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `Cannot invoke "java.util.List.size()" because "<local5>" is null` | 목록 조회가 "없음"을 null로 반환, 새 호출처가 검사 누락 | 반환 지점이 null을 낼 수 있나 | [18-1](../18-absence-and-null-design/2-summary.md) |
| `… because "this.conn" is null` | 호출 순서 결합 — `init()` 전 `send()` | 생성 후 초기화를 따로 요구하나 | [05-3](../05-connascence/2-summary.md) |
| `… because "this.clock" is null`, `@PostConstruct` 로그 없음 | 컨테이너 밖에서 `new`로 만든 객체 — 주입·훅 미적용 | 그 객체를 누가 `new`했나 | [32-3](../32-inversion-of-control-and-framework-flow/2-summary.md) |
| `… because "this.repo" is null`, 생성자 주입을 했는데도 | CGLIB 프록시가 final 메서드를 가로채지 못해 본문이 프록시 인스턴스에서 실행 | 그 메서드가 final인가, DEBUG 로그의 `cannot get proxied via CGLIB` | [33-2](../33-aop-and-proxies/2-summary.md) |
| 하위 클래스 `final` 필드가 초기화 중 null | 부모 생성자가 재정의 가능 메서드를 호출 | 스택이 부모 생성자 → 자식 메서드인가 | [21-4](../21-composition-over-inheritance/2-summary.md) |
| `NullPointerException: instant … at java.time.LocalDate.ofInstant` (새벽 배치) | `status=PAID`인데 `paidAt=null` — 불법 상태가 표현 가능 | 불법 조합 행을 SQL로 센다 | [24-3](../24-types-as-invariants/2-summary.md) |
| `… return value of "Subcontract$Gateway.approve(long)" is null` | 하위 타입이 사후조건을 약화 | 부모 계약 테스트를 새 구현에 돌린다 | [23-4](../23-design-by-contract/2-summary.md) |
| 스택 맨 위가 증상 자리(출고 라벨)이고 원인 자리(주문 생성)는 없음 | 생성 시점 검사 없음(늦은 실패) | 그 값이 처음 만들어진 곳 | [15-4](../15-error-handling-design/2-summary.md) |

**그 밖의 예외**

| 메시지 | 흔한 설계 원인 | leaf |
|---|---|---|
| `java.util.NoSuchElementException: No value present` | `Optional.get()` 무조건 호출 — NPE가 이름만 바뀜 | [18-2](../18-absence-and-null-design/2-summary.md) |
| `IllegalStateException: get() on Err: …` | 결과 타입을 검사 없이 꺼냄 | [16-2](../16-error-strategy-exceptions-vs-results/2-summary.md) |
| `UnsupportedOperationException` (`ImmutableCollections.uoe`) | LSP 위반·수정 불가 컬렉션을 받은 공통 함수 / 두 사례로 뽑은 인터페이스의 셋째 구현 / 개념상 IS-A로 만든 상속 | [22-1](../22-solid/2-summary.md) · [11-3](../11-when-to-abstract/2-summary.md) · [20-4](../20-oop-fundamentals/2-summary.md) |
| `UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only` | 안쪽 `@Transactional`의 도메인 예외를 바깥이 잡음(예외로 흐름 제어) / 재시도 프록시가 트랜잭션 안쪽 | [16-1](../16-error-strategy-exceptions-vs-results/2-summary.md) · [33-4](../33-aop-and-proxies/2-summary.md) |
| `JsonMappingException: Cannot lazily initialize collection of role '…' … (no session)` ← `LazyInitializationException` | 엔티티를 그대로 직렬화 | [43-1](../43-data-across-boundaries/2-summary.md) |
| `ClassCastException` (프록시를 구현 클래스로 캐스팅) | JDK 프록시 | [33-5](../33-aop-and-proxies/2-summary.md) |
| `AbstractMethodError: Receiver class … does not define or inherit an implementation …` | 옛 계약으로 컴파일된 플러그인 + 메서드가 추가된 SPI | [36-5](../36-extension-points-and-plugins/2-summary.md) |
| `NoSuchMethodError` / `NoSuchFieldError` (다른 JAR·서비스) | contract를 너무 일찍 함 / 공유 라이브러리 모델 변경을 일부만 배포 | [51-4](../51-legacy-change-techniques/2-summary.md) · [45-1](../45-monolith-vs-microservices/2-summary.md) |
| `ClassNotFoundException: shop.LegacyCsvExporter` | 정적 도달성만 믿고 지움(리플렉션·설정 문자열은 간선이 없다) | [54-4](../54-designing-for-deletion/2-summary.md) |
| `StackOverflowError` / `Document nesting depth (1001) exceeds the maximum allowed (1000 …)` (Jackson 2.22.3) / JS `RangeError: Maximum call stack size exceeded` | Composite 트리에 순환 / 양방향 연관 직렬화 / 양방향 바인딩 고리 | [27-4](../27-design-patterns-gof/2-summary.md) · [43-3](../43-data-across-boundaries/2-summary.md) · [42-2](../42-ui-architecture-patterns/2-summary.md) |
| `java.util.ConcurrentModificationException` (`publish` 루프) | 알림 중 구독 해지 | [27-3](../27-design-patterns-gof/2-summary.md) |
| `Invariant Violation: Dispatch.dispatch(...): Cannot dispatch in the middle of a dispatch.` | 스토어 콜백에서 연쇄 dispatch | [42-4](../42-ui-architecture-patterns/2-summary.md) |
| `java.io.NotSerializableException: java.util.Optional` | Optional 필드 | [18-4](../18-absence-and-null-design/2-summary.md) |
| `IllegalArgumentException: amount >= 100` (구현 교체 직후) | 하위 타입이 사전조건을 강화 | [23-4](../23-design-by-contract/2-summary.md) |
| 배포한 적 없는 서비스 로그에 SQL 오류(예: PostgreSQL `column "…" does not exist`) | 공유 DB 테이블이 사실상 공개 API | [45-2](../45-monolith-vs-microservices/2-summary.md) |
| 스레드 덤프에 `HashMap$TreeNode.balanceInsertion`에서 RUNNABLE인 스레드, CPU 100% | 동기화 없는 전역 가변 맵 | [31-2](../31-antipatterns/2-summary.md) |

### 6. 요청 단에서 보이는 증상 — HTTP·미들웨어

| 증상 | 흔한 설계 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 새 커스텀 어노테이션을 붙인 경로가 **404**, 오류·경고 없음(35 실험 A의 직접 만든 스캐너) | `@Retention` 생략 → 기본 `CLASS` → 리플렉션에서 안 보임 | `javap -v`에 `RuntimeVisibleAnnotations`가 있나 | [35-2](../35-annotation-and-metadata-programming/2-summary.md) |
| 특정 경로만 응답이 없고 클라이언트 `TimeoutError`(Express 5.2.1, 1505ms) / 같은 실수가 Koa 2.16.4에서는 404, Servlet Filter에서는 빈 200 | 미들웨어가 응답도 `next()`도 안 함 | 그 경로의 분기마다 응답 또는 `next()`가 있나 | [34-2](../34-middleware-filter-interceptor-chains/2-summary.md) |
| 401 요청의 본문이 로그에 쌓임, 인증 전에 대용량 바디 파싱 | 미들웨어·필터 **순서 역전** | 등록 순서(필터 order 값)를 출력 | [34-1](../34-middleware-filter-interceptor-chains/2-summary.md) |
| 요청 하나에 같은 필터 로그 2줄, 레이트 리밋 2배 | 필터를 `@Component`로도, Security 체인에도 등록 | 등록 지점 수 | [34-3](../34-middleware-filter-interceptor-chains/2-summary.md) |
| 인터셉터가 막았다는 요청이 컨트롤러에 도달 | 인터셉터를 보안 계층으로 씀 | 경로 매칭 차이 | [34-4](../34-middleware-filter-interceptor-chains/2-summary.md) |
| 잔액 부족 같은 도메인 실패가 500, 같은 멱등 키 재시도 폭증 | 도메인 실패를 5xx로 번역 / 새 예외가 기본 처리기로 샘 | 응답 코드별 재시도 수 | [16-3](../16-error-strategy-exceptions-vs-results/2-summary.md) · [16-5](../16-error-strategy-exceptions-vs-results/2-summary.md) |
| 응답에 SQL 원문 / "오류가 발생했습니다"만 | `e.getMessage()`를 그대로 응답 / 연결 고리(incidentId)까지 지움 | 스테이징에서 일부러 실패시킨 응답 본문 | [17-3](../17-error-messages-and-log-level-policy/2-summary.md) · [17-4](../17-error-messages-and-log-level-policy/2-summary.md) |
| 응답에 `passwordHash` / 새 필드가 늘 `null` | 엔티티 직렬화(차단 목록) / 손 매퍼 한 계층 누락 | 응답 모델이 따로 있나 | [43-2](../43-data-across-boundaries/2-summary.md) · [43-5](../43-data-across-boundaries/2-summary.md) |
| 상세 화면 하나에 같은 서비스 호출 수십~수백 번(50건에 103회) | 게터 수준 원격 인터페이스(Chatty I/O) | 트레이스의 호출 수 | [43-4](../43-data-across-boundaries/2-summary.md) |
| 앞단 502가 뒷단 하나의 장애와 함께 오름 | 동기 호출 체인 | 트레이스의 홉 수 | [45-3](../45-monolith-vs-microservices/2-summary.md) |
| 다른 고객사의 청구서가 보임(간헐적) | 캐시 키에 테넌트 누락 | 캐시 키 구성 | [49-1](../49-multi-tenancy/2-summary.md) |

### 7. 조용한 실패 — 에러도 경보도 없이 값만 틀림

가장 비싼 칸(⑥)이다. 발견은 대사(reconciliation)·고객 문의·월말 숫자로 늦게 온다.

| 증상 | 흔한 설계 원인 | 첫 확인 | leaf |
|---|---|---|---|
| 고친 곳이 아닌 **다른 화면·정산의 숫자**가 틀림(1원 차이 등) | 같은 지식이 다른 모양으로 여러 곳(grep·jdeps에 안 걸림) | 같은 입력으로 두 경로의 값을 대조하는 교차 테스트 | [01-2](../01-complexity/2-summary.md) · [06-1](../06-clean-code/2-summary.md) · [11-4](../11-when-to-abstract/2-summary.md) · [26-2](../26-functional-core-imperative-shell/2-summary.md) · [42-3](../42-ui-architecture-patterns/2-summary.md) |
| 공유 모듈 문구를 고쳤더니 **무관한 화면**이 바뀜 / 수수료를 올렸더니 정산이 바뀜 | 함께 바뀌지 않는 지식을 합침(우연한 중복의 통합) | "함께 바뀌나?" | [01-3](../01-complexity/2-summary.md) · [06-2](../06-clean-code/2-summary.md) |
| 새 등급·타입·상태가 **기본 분기**로(`label=기타`, BASIC 요율, 환불이 "대기") | 마지막 `else`·`default`가 누락을 삼킴, 같은 `switch`가 여러 파일 | `switch`/`if` 사슬의 기본 분기 grep | [28-1](../28-taming-conditionals/2-summary.md) · [28-2](../28-taming-conditionals/2-summary.md) · [22-3](../22-solid/2-summary.md) · [24-5](../24-types-as-invariants/2-summary.md) · [29-2](../29-refactoring-to-patterns/2-summary.md) · [04-3](../04-decompose-by-change/2-summary.md) |
| 반대 방향 송금, **남의 주문** 조회, 감사 로그 대신 고객 알림 | 같은 타입 인자 둘의 위치 결합, 원시 타입 집착, 플래그 인자 | 같은 타입 인자가 둘 이상인 시그니처 | [05-1](../05-connascence/2-summary.md) · [24-1](../24-types-as-invariants/2-summary.md) · [08-1](../08-function-design/2-summary.md) |
| 상태 `3`의 뜻이 서비스마다 다름 | 의미 결합(매직 값)이 경계를 넘음 | 숫자 상태값 grep | [05-2](../05-connascence/2-summary.md) |
| **불법 상태 행**: 음수 재고, 빈 이메일, `PAID` + `paidAt=null`, 미입력 할인율이 0% | 검증한 사실이 타입에 안 남음, 계약 미명시, 상태·필드 독립 컬럼, 원시 `int`의 기본값 0 | `WHERE qty < 0`류 정합성 쿼리 | [24-2](../24-types-as-invariants/2-summary.md) · [24-3](../24-types-as-invariants/2-summary.md) · [23-1](../23-design-by-contract/2-summary.md) · [18-3](../18-absence-and-null-design/2-summary.md) · [20-1](../20-oop-fundamentals/2-summary.md) · [23-5](../23-design-by-contract/2-summary.md) |
| 한 요청의 수정이 **다른 요청·사용자에게 누출** | 공유 가변 값 객체, 싱글턴에 요청 범위 객체(captive dependency), 얕은 불변 record, 내부 컬렉션 노출 | 로그의 요청 ID와 컨텍스트 ID 대조 | [19-1](../19-immutability-and-value-objects/2-summary.md) · [25-1](../25-dependency-injection-and-composition-root/2-summary.md) · [19-3](../19-immutability-and-value-objects/2-summary.md) · [06-4](../06-clean-code/2-summary.md) · [20-2](../20-oop-fundamentals/2-summary.md) · [02-2](../02-modularity-coupling-cohesion/2-summary.md) |
| 맵에 넣은 것을 못 찾고 크기만 증가 | 해시 키 변이 | 키의 `equals`·`hashCode` 필드가 가변인가 | [19-2](../19-immutability-and-value-objects/2-summary.md) |
| 누적·집계 수치가 모자람(실행마다 다름) | 불변 값의 "교체"를 경쟁 상태로, 전역 싱글턴 카운터 | 공유 참조 갱신 지점 | [19-4](../19-immutability-and-value-objects/2-summary.md) · [31-2](../31-antipatterns/2-summary.md) |
| 예외가 났는데 **앞서 쓴 행이 남음** | `@Transactional` 자기 호출·final 메서드, checked 예외(기본 롤백 규칙), 실패 결과를 정상 반환, 어댑터마다 트랜잭션 | 트랜잭션 DEBUG 로그에 `Creating new transaction` 줄이 있나 | [33-1](../33-aop-and-proxies/2-summary.md) · [33-2](../33-aop-and-proxies/2-summary.md) · [16-1](../16-error-strategy-exceptions-vs-results/2-summary.md) · [16-4](../16-error-strategy-exceptions-vs-results/2-summary.md) · [44-4](../44-architecture-in-code/2-summary.md) |
| 재시도는 성공했는데 실패한 시도의 쓰기도 커밋 | 프록시 순서 — 재시도가 트랜잭션 안쪽 | 애스펙트 우선순위(`@Order`) 출력 | [33-4](../33-aop-and-proxies/2-summary.md) |
| 집계가 부풀어 최대 2배까지(`addAll` 경로 비중만큼) | 상속한 자식이 부모의 자기 호출에 의존(`HashSet` 카운터), 부모의 새 메서드가 자식 검증 우회 | 경로별(`add` vs `addAll`) 수치 | [21-1](../21-composition-over-inheritance/2-summary.md) · [21-2](../21-composition-over-inheritance/2-summary.md) · [21-3](../21-composition-over-inheritance/2-summary.md) |
| 리팩터링·전환 뒤 **1원·정렬** 차이 | 문서화 안 된 동작(반올림 위치·동점 정렬)을 고정하지 않음 | 병행 실행 비교, 지문 비교 | [13-1](../13-refactoring/2-summary.md) · [50-3](../50-legacy-migration-strangler-fig/2-summary.md) · [51-3](../51-legacy-change-techniques/2-summary.md) · [14-4](../14-tidy-first/2-summary.md) |
| 직접 정의한 빈 대신 기본 구현이 동작 / 환경마다 다른 플러그인 / 기능이 조용히 꺼짐 | 빈 덮어쓰기 허용, `ServiceLoader` 발견 순서, `META-INF/services` 누락 | 주입된 구현 클래스 이름을 기동 로그에 | [36-1](../36-extension-points-and-plugins/2-summary.md) · [36-3](../36-extension-points-and-plugins/2-summary.md) · [36-4](../36-extension-points-and-plugins/2-summary.md) |
| 설정을 바꿨는데 효과 없음 / 같은 이미지가 환경마다 다르게 동작 | 오타 변수명은 다른 키, 손으로 고친 값의 드리프트 | 실효 설정(비밀은 가림), 환경 간 설정 diff | [48-3](../48-configuration-and-12factor/2-summary.md) · [48-1](../48-configuration-and-12factor/2-summary.md) |
| 에러율 0인데 저장 건수가 모자람 | 삼킨 예외 | 들어온 수 = 처리 수 + 실패 수 대조 | [15-2](../15-error-handling-design/2-summary.md) |
| 주문은 됐는데 정산 기록이 가끔 빠짐 | 동기 Observer에서 앞 리스너 예외가 루프를 끊음 | 리스너별 로그 유무 | [27-2](../27-design-patterns-gof/2-summary.md) |
| 할인 줄이 있는데 합계 그대로 | 불변 객체 연산 결과를 버림 | 반환값 무시 정적 검사 | [19-5](../19-immutability-and-value-objects/2-summary.md) |
| 화면마다 할인액이 다름 / 활성 사용자만 건너뜀 / 타임아웃이 즉시 | 같은 개념의 이름 셋, 이중 부정 boolean, 단위 없는 이름 | 용어 grep, 조건식 | [07-3](../07-naming/2-summary.md) · [07-2](../07-naming/2-summary.md) · [07-4](../07-naming/2-summary.md) |
| 디버그 로그를 켜면 결과가 달라짐 | 질의 이름의 함수가 상태를 바꿈(CQS 위반) | 게터 안의 쓰기 | [08-2](../08-function-design/2-summary.md) |
| 온콜이 주석을 믿고 다른 곳을 찾음 | 주석이 코드 숫자를 복사, 값만 바뀜 | 바뀐 줄 근처 주석 | [09-1](../09-comments-and-conventions/2-summary.md) |
| 플래그 설정을 지우자 다섯 곳이 옛 경로 | 끝난 플래그 분기 잔존, 없는 플래그의 기본값 = 옛 경로 | 플래그 키 사용처 | [54-2](../54-designing-for-deletion/2-summary.md) |
| 같은 주문의 값이 화면마다 1원 다름(이전 중) | 신·구 경로가 같은 행에 이중 쓰기 | 기준(system of record) 지정 여부 | [50-2](../50-legacy-migration-strangler-fig/2-summary.md) |

### 8. 지표·로그 패턴 — 에러 대신 숫자가 이상하다

| 패턴 | 먼저 의심 | leaf |
|---|---|---|
| ERROR 대부분이 `status=400·404`, 알람을 습관적으로 닫음 | "실패 = ERROR" 느낌 기반 레벨 | [17-1](../17-error-messages-and-log-level-policy/2-summary.md) |
| 같은 요청 ID로 ERROR 4건, 같은 근본 원인 문장 4번 | 계층마다 catch-log-rethrow | [15-1](../15-error-handling-design/2-summary.md) · [17-2](../17-error-messages-and-log-level-policy/2-summary.md) |
| 기동 시작~`Started` 간격이 서비스 크기와 함께 증가 | 기동 시 스캔·리플렉션 | [35-3](../35-annotation-and-metadata-programming/2-summary.md) |
| 평균은 내려갔는데 p99 그대로 | 캐시 만료 순간의 원본 대기 — 평균과 꼬리는 다른 측정치 | [46-2](../46-quality-attributes-and-tradeoffs/2-summary.md) |
| 응답 시간은 좋아졌는데 "예전 가격으로 결제" 문의 증가 | 정합성 요구를 측정치로 적지 않은 최적화 | [46-1](../46-quality-attributes-and-tradeoffs/2-summary.md) |
| 이벤트로 바꾼 뒤 consumer lag, "됐는데 안 됐다" 문의 | 즉시성이 필요한 경로를 비동기로 | [37-2](../37-architecture-styles/2-summary.md) |
| 작은 테넌트 지연이 큰 테넌트 배치 시각에만 급등 | 공용 FIFO 자원에 테넌트별 상한 없음 | [49-2](../49-multi-tenancy/2-summary.md) |
| 같은 배치가 다른 환경보다 수십 배 느림, 결과는 맞음, 프로파일러에서 `read` 시스템 호출이 대부분 | 깊어야 할 결정(버퍼링)을 호출자에게 맡긴 얕은 인터페이스 | [03-3](../03-deep-modules-and-abstraction/2-summary.md) |
| 정적 분석 0건인데 기능마다 파일 5~6개 | 도구 밖의 변경 축 스멜 | [10-4](../10-code-smells/2-summary.md) |
| 복잡도·핫스팟 점수는 내려갔는데 변경당 수정 파일 수 증가 | 지표 게이밍(굿하트) | [52-2](../52-complexity-metrics/2-summary.md) · [53-5](../53-code-forensics-hotspots/2-summary.md) |
| 서비스마다 99.9%인데 체감 성공률은 더 낮음 | 직렬 의존은 가용성을 곱한다 | [45-3](../45-monolith-vs-microservices/2-summary.md) |

### 9. 흔한 오독 — 증상을 보고 잘못 내리는 결론

| 오독 | 왜 틀리나 (조건) | 근거 leaf |
|---|---|---|
| "추상화하면 좋아진다" | 추상화는 **예측한 축**의 변경만 싸게 한다. 축이 틀리면 패턴 판 6파일(진입점 Main 포함)·19줄 추가 대 plain 1파일·10줄 추가(27 실험 A). 1:1 매핑만 하는 계층은 필드 하나에 4파일(44 실험 B). 잘못된 추상화는 중복보다 비쌀 수 있다(Metz, 11) | [27-1](../27-design-patterns-gof/2-summary.md) · [44-3](../44-architecture-in-code/2-summary.md) · [11-1](../11-when-to-abstract/2-summary.md) · [12-1](../12-simple-design-and-yagni/2-summary.md) |
| "패턴을 썼으니 설계가 좋다" | 패턴은 특정 힘(forces)에 대한 해법이다. 힘이 없는 곳의 패턴은 간접 계층이다. 구현 하나짜리 Strategy·Factory는 화석이 된다 | [30-1](../30-pattern-languages-and-catalogs/2-summary.md) · [29-1](../29-refactoring-to-patterns/2-summary.md) · [29-3](../29-refactoring-to-patterns/2-summary.md) · [31-5](../31-antipatterns/2-summary.md) |
| "복잡도 지표만 낮추면 된다" | 게이트를 맞추려 쪼개면 메서드별 숫자는 내려가도 클래스 합계가 오른다(52 실험 c: 순환 14 → 합 19). 큰 `switch`는 순환 복잡도가 크고 인지 복잡도는 작다. 지표는 "어디를 볼지"용이다 | [52-2](../52-complexity-metrics/2-summary.md) · [52-4](../52-complexity-metrics/2-summary.md) · [53-5](../53-code-forensics-hotspots/2-summary.md) |
| "테스트가 통과하니 리팩터링은 안전하다" | 테스트가 보는 입력만 안전하다. 반올림 위치 이동은 행복 경로 테스트를 통과했고(13 실험 A), 새 타입을 모르는 테스트는 `6 pass, 0 fail`이었다(29 실험 A). 리팩터링 전에 현재 동작을 고정해야 한다 | [13-1](../13-refactoring/2-summary.md) · [29-2](../29-refactoring-to-patterns/2-summary.md) · [51-3](../51-legacy-change-techniques/2-summary.md) |
| "중복은 다 없애야 한다" | DRY는 **지식**의 단일 표현이다. 값이 같을 뿐인 다른 지식을 합치면 한쪽 변경이 다른 쪽을 바꾼다(06 실험 B) | [06-2](../06-clean-code/2-summary.md) · [11-1](../11-when-to-abstract/2-summary.md) · [22-4](../22-solid/2-summary.md) |
| "도구 경고 0건이면 깨끗하다" | PMD는 심은 스멜 8개 중 4개만 보고했다(타입 정보를 주면 5개, 10 실험 B). 부정 boolean 이름도 이름 규칙을 통과한다(07) | [10-4](../10-code-smells/2-summary.md) · [07-2](../07-naming/2-summary.md) |
| "서비스로 나누면 독립 배포된다" | 함께 바뀌는 결정을 가르지 못하면 분산 모놀리스다. 공유 DB 컬럼 하나가 서비스 3개로 번졌다(45 실험 B) | [45-1](../45-monolith-vs-microservices/2-summary.md) · [45-2](../45-monolith-vs-microservices/2-summary.md) |
| "헥사고날 폴더가 있으니 헥사고날이다" | 폴더명은 배치일 뿐이다. 전부 `public`이면 컨트롤러가 JPA 리포지토리를 바로 쓴다. 의존 방향은 가시성·모듈·규칙 테스트로 강제한다 | [40-5](../40-codebase-structure/2-summary.md) · [44-1](../44-architecture-in-code/2-summary.md) |
| "Optional을 쓰면 NPE가 없어진다" | `get()`을 무조건 부르면 `NoSuchElementException: No value present`로 이름만 바뀐다 | [18-2](../18-absence-and-null-design/2-summary.md) |
| "record·불변이면 안전하다" | record는 참조만 고정한다(얕은 불변). 불변 값의 교체는 여전히 경쟁이다 | [19-3](../19-immutability-and-value-objects/2-summary.md) · [19-4](../19-immutability-and-value-objects/2-summary.md) |
| "`@Transactional`을 붙였으니 원자적이다" | 프록시를 거쳐야 적용된다(자기 호출·final 메서드 제외). 기본 롤백 규칙은 unchecked·`Error`만이다(Spring 6.2) | [33-1](../33-aop-and-proxies/2-summary.md) · [33-2](../33-aop-and-proxies/2-summary.md) · [16-1](../16-error-strategy-exceptions-vs-results/2-summary.md) |
| "규칙 테스트가 있으니 경계가 지켜진다" | CI가 동결 저장소를 새로 만들면 현재 위반 전부가 기준선이 된다. 컴파일 타임 상수 참조는 바이트코드에서 사라져 규칙이 못 본다 | [41-4](../41-architecture-fitness-rules/2-summary.md) · [41-1](../41-architecture-fitness-rules/2-summary.md) |
| "이벤트로 바꾸면 결합이 사라진다" | 직접 결합 대신 흐름 가시성을 잃는다. 동기 리스너 하나의 실패가 나머지를 막을 수 있고, 즉시성을 내준다 | [06-3](../06-clean-code/2-summary.md) · [27-2](../27-design-patterns-gof/2-summary.md) · [37-2](../37-architecture-styles/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인** — 이 노트 자체다. 정방향 "leaf → 시나리오 목록"을 뒤집어 "증상 → leaf 목록"으로 만들었다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **결정 트리** — 한 증상에 원인이 여럿이면 질문 몇 개로 가른다. 아래 "파일 N개" 그림이 그렇다.
- **공동 변경 행렬(연관 규칙)** — 커밋을 "함께 바뀐 파일 집합"으로 보고 파일 쌍의 공동 등장 수(지지도)를 센다. import 그래프에 없는 결합이 보인다([53](../53-code-forensics-hotspots/2-summary.md)).
- **의존 그래프와 SCC** — jdeps·ArchUnit이 만든 간선에서 강한 연결 요소를 찾으면 순환 묶음이 나온다([39](../39-component-principles/2-summary.md) · [41](../41-architecture-fitness-rules/2-summary.md), [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)).
- **호출 그래프 도달성** — 진입점에서 닿지 않는 노드가 죽은 코드 후보다. 리플렉션·설정 문자열은 간선을 남기지 않아 실행 관측으로 보완한다([54](../54-designing-for-deletion/2-summary.md)).

```text
  "작은 요구에 파일 N개"를 보면 먼저 묻는다: "바뀐 파일들은 무엇인가?"

    같은 지식의 사본(같은 switch·세율·필드 목록) ── 흩어진 결정 ── 한 곳으로 모은다         (10-1, 04-1, 53-2)
    위임만 하는 인터페이스·팩토리·매퍼 ─────────── 간접 계층 과잉 ── 인라인한다             (12-1, 27-1, 44-3)
    controller/service/repository/dto 폴더 ──────── 기술 역할 배치 ── 기능 단위로 묶는다     (40-2, 39-4)
    여러 서비스·모듈 ───────────────────────────── 경계가 결정을 못 가름 ── 합치거나 계약화 (45-1, 39-4)
```

```text
  NPE를 보면 먼저 묻는다: "because 뒤가 무엇인가?"

    지역 변수(<localN>·변수 이름) ── 반환값이 null ─────────── 반환 설계(빈 컬렉션·Optional)   (18-1)
    this.<주입 필드>, 생성자 주입함 ── 프록시 인스턴스에서 실행 ── final 메서드?              (33-2)
    this.<주입 필드>, 필드 주입 ───── 컨테이너 밖 new ──────────── 누가 new 했나              (32-3)
    this.<초기화 필드> ────────────── 호출 순서 결합 ──────────── init 전 호출               (05-3)
    JDK 메서드 인자(instant 등) ───── 불법 상태 데이터 ─────────── 상태별 타입·DB 제약         (24-3)
```

## 적용 — 풀어나가는 법

### 1. 시점과 모양으로 1차 분류한다

```text
  처음 보인 곳                  대개 뜻하는 것                                    먼저 볼 표
  ---------------------------   ----------------------------------------------   ----------
  PR·리뷰·병합                  흩어진 결정, 간접 계층, 기술 역할 배치, 공유 경계     §1
  컴파일·규칙 테스트             설계가 실수를 당겨 온 것(좋은 신호) 또는 누출·순환    §3
  기동                          조립(composition root)·프록시·자동 설정 조건         §4
  테스트                        숨은 의존·숨은 입력·가변 전역·동작 미고정            §2
  운영 예외                     "없음"의 설계, 수명 주기, 프록시, 계약 변경          §5·§6
  에러 없이 값·건수만 틀림        지식 사본, 기본 분기, 불법 상태, 공유 가변, 트랜잭션 §7
  지표만 이상                    로그 레벨, 꼬리 지연, 지표 게이밍                   §8
```

### 2. 첫 진단 세트

```sh
# 변경 비용 — 요구 1건의 크기와 반복되는 묶음
git show --stat <커밋>
git log --grep='결제 수단' --stat --format='%h %s'        # 같은 유형 요구의 과거 커밋과 비교
git diff --dirstat=files,0 HEAD~1                         # 폴더별 분포 (40)

# 변경 빈도(핫스팟 후보)와 공동 변경(숨은 결합)
git log --since=12.months --format= --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head
git log --since=12.months --format='@%h' --name-only | awk '
  /^@/{n=0; next} NF{f[++n]=$0; for(i=1;i<n;i++){a=f[i];b=$0; if(a>b){t=a;a=b;b=t}; p[a" + "b]++}}
  END{for(k in p) if(p[k]>=3) print p[k], k}' | sort -rn | head

# 지식 분포 — 이 파일을 누가 아는가
git log --format=%aN -- src/main/java/shop/TokenStore.java | sort | uniq -c | sort -rn

# 결정 이력 — 같은 값이 왕복했나
git log -S'maxAttempts = 5' --oneline

# 의존 방향·순환 (컴파일된 클래스 기준)
jdeps -verbose:package -filter:none build/classes        # web -> repository 같은 우회 간선 (40)
javap -v build/classes/shop/RefundController.class | grep -A2 RuntimeVisibleAnnotations   # 보존 정책 (35)
```

- 공동 변경 awk는 커밋마다 파일 쌍을 센다. 커밋 하나에 파일이 많으면 쌍이 제곱으로 늘어나므로, 대량 커밋(포매팅·일괄 rename)은 빼고 센다([53-4](../53-code-forensics-hotspots/2-summary.md)). 실무에서는 code-maat 같은 도구가 기간·최소 공동 커밋 수·대량 변경 크기를 거른다([53](../53-code-forensics-hotspots/2-summary.md)).
- jdeps 기본 필터(`-filter:package`)는 같은 패키지 안의 간선을 숨긴다([54-4](../54-designing-for-deletion/2-summary.md)). 그래서 위에서는 `-filter:none`을 썼다.

```java
// 경계를 실행 가능한 규칙으로 — ArchUnit (41·38). 색인에서 "계층 우회"를 찾았다면 다음 PR부터 이 규칙이 막는다.
@ArchTest
static final ArchRule domainIsPure = noClasses().that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAnyPackage("..web..", "..persistence..");

@ArchTest
static final ArchRule noCycles = slices().matching("com.shop.(*)..").should().beFreeOfCycles();
```

### 실행 확인: 색인에 쓴 메시지와 첫 진단 명령

이 노트는 실험 의무 대상이 아니다(명세 I7 — 종합 55·56 제외). 다만 색인에 인용한 메시지 몇 개와 위의 git 명령을 직접 실행해 확인했다.

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `scratchpad/sd/55/e55/Msgs.java`·`sw/Status.java`, 2026-10-02)

```java
@interface AuditedDefault {}                                  // @Retention 생략 -> 기본 CLASS
@Retention(RetentionPolicy.RUNTIME) @interface AuditedRuntime {}
@AuditedDefault @AuditedRuntime static class RefundController {}

static List<String> coupons(String user) { return null; }     // "없음"을 null로
// main: getAnnotation 두 번, coupons(..).size(), Optional.empty().get(), List.of("x").add("y")

sealed interface Status permits Status.Paid, Status.Pending, Status.Refunded { ...
    static String label(Status s) {
        return switch (s) {                       // default 없음 -> 누락이 컴파일 오류
            case Paid p -> "결제됨";
            case Pending p -> "대기";             // Refunded를 빠뜨렸다
        };
    }
}
```

```text
CLASS(기본) 보존 어노테이션 보임? false
RUNTIME 보존 어노테이션 보임?   true
null 목록의 size() -> java.lang.NullPointerException: Cannot invoke "java.util.List.size()" because "<local0>" is null
Optional.empty().get() -> java.util.NoSuchElementException: No value present
List.of("x").add("y") -> java.lang.UnsupportedOperationException
== javac sealed switch
sw/Status.java:6: error: the switch expression does not cover all possible input values
        return switch (s) {                       // default 없음 -> 누락이 컴파일 오류
               ^
1 error
exit=1
```

같은 `Msgs.java`를 `javac`로 컴파일해 실행하면 `"<local0>"`, `javac -g`로 컴파일하면 `"c"`(변수 이름)가 나왔다.

```text
null 목록의 size() -> java.lang.NullPointerException: Cannot invoke "java.util.List.size()" because "<local0>" is null
null 목록의 size() -> java.lang.NullPointerException: Cannot invoke "java.util.List.size()" because "c" is null
```

(실험, git 2.43.0, `maven:3.9-eclipse-temurin-21` 컨테이너 `--cpus=2`, `scratchpad/sd/55/e55/diag.sh` — 커밋 6개짜리 장난감 저장소, 2026-10-02)

```text
== 1) 요구 1건의 크기: git show --stat (마지막 '결제 수단 추가' 커밋)
 5 files changed, 5 insertions(+)
== 2) 변경 빈도: git log --format= --name-only | sort | uniq -c | sort -rn
      4 OrderMapper.java
      4 Order.java
      2 util/Dates.java
      2 PaymentService.java
      2 PaymentMethod.java
== 3) 함께 바뀌는 쌍(공동 커밋 수)
4 Order.java + OrderMapper.java
```

관찰:
- `@Retention`을 생략한 어노테이션은 컴파일·실행 오류 없이 리플렉션에서 사라졌다. 35-2의 "404, 오류 없음"과 같은 모양이다.
- `default` 없는 `switch` 식은 새 상태 누락을 컴파일 오류로 바꿨다. 28-2·24-5의 "조용한 기본 분기"가 ⑥에서 ②로 올라온 것이다.
- helpful NPE의 지역 변수 표기는 컴파일 옵션(`-g`)에 따라 다르다. 그래서 18-1의 `<local5>`와 이 실행의 `<local0>`은 같은 종류의 메시지다. `this.필드`처럼 필드 이름은 `-g`와 상관없이 나온다(05-3·32-3·33-2의 메시지).
- 장난감 저장소에서 "결제 수단 추가" 커밋은 매번 같은 5파일을 건드렸고, `Order.java`·`OrderMapper.java`는 4번 모두 함께 바뀌었다. 같은 명령을 실제 저장소에 돌리면 §1의 "파일 N개"·"두 파일 중 하나를 깜빡" 후보가 나온다. 이 저장소의 숫자는 예시일 뿐 어떤 설계의 비용을 잰 것이 아니다.

### 3. leaf로 간다

- §1~§8에서 후보 leaf를 고른다. 후보가 여럿이면 각 leaf 시나리오의 "보이는 형태"와 내 관찰을 대조해 지운다.
- 원인이 설계 밖이면 다른 색인으로 간다.
  - 타임아웃·재시도·배포·플래그 운영: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)
  - 분산 트랜잭션·메시지·시계: [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md)
  - SQLSTATE·풀·ORM 메시지: [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)
- 실제 사건에서 설계 결함이 어떻게 이어졌는지는 [56-design-incidents](../56-design-incidents/2-summary.md)에 있다.

## 장애 시나리오와 대처

이 절은 **색인을 읽는 실수**를 다룬다. 증상 자체는 위 표와 leaf에 있다.

### 1. "파일 N개"를 보고 추상화를 하나 더 얹는다

- **현상**: 할인 하나 추가에 파일 7개를 고쳤다. 팀은 "확장성이 부족하다"며 플러그인 레지스트리를 하나 더 넣는다. 다음 할인 추가는 파일 9개다.
- **보이는 형태**: `git show --stat`의 파일 수가 늘어남. 늘어난 파일이 인터페이스·팩토리·레지스트리·설정이다. 리뷰 질문 "이 계층은 뭐 하는 거냐"(12 실험 SPEC v2: 7파일 +20/−8).
- **원인**: "파일 N개"에는 반대 방향의 원인이 둘 있다. 흩어진 사본(모아야 함)과 간접 계층 과잉(걷어내야 함)이다. 바뀐 파일의 종류를 보지 않고 처방했다.
- **대처**: 바뀐 파일을 사본과 통과 계층으로 분류한다(§동작·원리 결정 트리). 통과 계층이 대부분이면 구현 하나짜리 인터페이스·팩토리를 인라인한다([12-1](../12-simple-design-and-yagni/2-summary.md) · [27-1](../27-design-patterns-gof/2-summary.md)). 사본이 대부분이면 결정을 한 곳에 모으는 정리 커밋을 먼저 낸다([10-1](../10-code-smells/2-summary.md)).

### 2. NPE를 null 검사 추가로 닫는다

- **현상**: 결제 서비스의 한 메서드에서만 NPE가 난다. `if (repo == null) return;`을 넣었다. 이제 예외는 없고 결제가 조용히 저장되지 않는다.
- **보이는 형태**: `NullPointerException: … because "this.repo" is null`. 생성자 주입을 했고 다른 메서드에서는 `repo`가 정상이다(33 실험 C3, Spring Framework 6.2.11).
- **원인**: 그 메서드가 final이라 CGLIB 프록시가 가로채지 못했다. 본문이 필드가 비어 있는 프록시 인스턴스에서 실행됐다. null 검사는 ⑤의 증상을 ⑥의 조용한 실패로 내렸다.
- **대처**: `because` 뒤가 **주입 필드**면 null 검사보다 생성·주입 경로를 먼저 본다. final 메서드인가(33-2), 컨테이너 밖 `new`인가(32-3), 초기화 순서인가(05-3·21-4). 지역 변수·반환값이면 "없음"의 설계를 본다(18-1).

### 3. 기동 실패를 설정 스위치로 덮는다

- **현상**: 빈 하나를 추가하자 기동이 실패했다. `spring.main.allow-bean-definition-overriding=true`를 켰더니 뜬다. 몇 주 뒤 결제가 기본 구현으로 처리된 것이 발견된다.
- **보이는 형태**: 처음에는 같은 이름 빈 충돌로 `The bean 'paymentClient' … could not be registered. … overriding is disabled.`(36 실험 B의 C). 스위치를 켠 뒤에는 오류 없이 `주입된 구현=Default(자동 설정)`(36 실험 B의 C + 덮어쓰기 허용).
  - 이 스위치는 이름이 같은 경우만 바꾼다. 이름이 다른 같은 타입 빈 둘(`required a single bean, but 2 were found`, 36 실험 B의 B)은 켜도 그대로다(변형 B에 덮어쓰기 허용을 켜고 다시 돌려 같은 메시지로 기동 실패 확인, 2026-10-02).
  - 순환(`BeanCurrentlyInCreationException`)에 `spring.main.allow-circular-references=true`를 켜는 것도 같은 덮기다. 단 이 스위치는 세터·필드 주입 순환만 띄운다. 25 실험 A 같은 생성자 순환은 켜도 실패한다(25 실험 E).
- **원인**: 기동 실패는 ③에서 조립 오류를 잡아 준 좋은 신호였다. 스위치가 그것을 ⑥의 조용한 오동작으로 내렸다. Seemann–van Deursen은 프로퍼티(세터) 주입으로 순환을 끊는 것을 최후 수단이라 부른다(6.3.5절 제목). `allow-circular-references`로 순환을 허용하는 것도 같은 부류로 보는 것은 25번의 해석이다(25-3).
- **대처**: 순환이면 공통 부분을 세 번째 클래스로 추출하거나 한 방향을 이벤트로 바꾼다(25-3). 빈 충돌이면 급한 대로 `@Primary`·`@Qualifier`, 근본은 자동 설정의 `@ConditionalOnMissingBean(인터페이스.class)`다(36-2). 덮어쓰기 허용은 Boot 기본값(false)으로 둔다(36-1).

### 4. "테스트 초록 + 정적 분석 0건"으로 리팩터링을 끝냈다고 선언한다

- **현상**: 구조만 바꿨다는 배포 뒤 정산 대사에서 1원씩 어긋나는 건이 나온다.
- **보이는 형태**: CI 초록, PMD 0건. 영수증 줄 금액 합과 합계 줄이 다르다(13 실험 A 관찰 1·2). 새 타입이 들어왔다면 `tests: 6 pass, 0 fail`인데 `label=?`(29 실험 A).
- **원인**: 테스트는 테스트가 고른 입력만 지킨다. 도구는 도구가 아는 스멜만 본다. 둘 다 "동작이 같다"를 증명하지 않는다.
- **대처**: 리팩터링 **전에** 넓은 입력으로 현재 출력을 고정한다(골든 마스터·특성 테스트, 13·51). 리팩터링 커밋마다 지문을 비교한다(14-4). 이미 배포됐으면 단계별 커밋에서 `git bisect run`으로 범인 단계를 찾는다(13-1).

### 5. 조용한 값 오류를 데이터 핫픽스로만 닫는다

- **현상**: 음수 재고·`PAID`인데 `paidAt=null` 행을 SQL로 고쳤다. 다음 달 같은 행이 또 생긴다.
- **보이는 형태**: 정합성 쿼리 결과가 매달 0이 아니다. 새로 생긴 경로(CSV 가져오기·관리자 API)에서만 발생한다(24 실험 C validate 판).
- **원인**: 원인은 설계(검증한 사실이 타입에 안 남음, 상태·필드가 독립)인데 결과(데이터)만 고쳤다. 반대로 코드만 고치면 이미 저장된 불법 행은 그대로다(20-1·23-1).
- **대처**: 둘 다 한다. 코드는 값 타입 생성자·상태별 타입으로 불법 상태를 표현할 수 없게 하고(24-2·24-3), DB에는 `CHECK` 제약을 둔다. 기존 불법 행이 있으면 `NOT VALID`로 새 행부터 막고 보정 뒤 검증한다(24 실험 E).

## 핵심 문장

- 이 노트는 **증상 → 드러난 시점 → 흔한 설계 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 설계 결함은 PR·컴파일·기동·테스트·운영 예외·조용한 값 오류 중 어디서든 보일 수 있다. 좋은 설계 결정의 상당수는 같은 결함을 더 이른 칸(컴파일·기동)으로 끌어올린다.
- "작은 변경에 파일 N개"에는 반대 방향 원인이 둘 있다. 흩어진 사본이면 모으고, 위임만 하는 간접 계층이면 걷어낸다. 바뀐 파일의 종류를 먼저 본다.
- helpful NPE는 `because` 뒤를 읽는다. 주입 필드면 프록시·수명 주기·초기화 순서를, 지역 변수·반환값이면 "없음"의 설계를 본다.
- 기동 실패·컴파일 오류는 대개 좋은 신호다. 설정 스위치나 `default` 분기로 덮으면 조용한 실패로 내려간다.
- 테스트 초록과 도구 0건은 "동작이 같다"의 증거가 아니다. 현재 동작을 먼저 고정하고, 지표는 어디를 볼지 정하는 데만 쓴다.

## 관련 주제·근거

- 선행: 소프트웨어 설계 영역 전체([../README.md](../README.md)). 이 노트의 `NN-k` 링크는 각 leaf의 「장애 시나리오와 대처」 시나리오를 가리킨다(2026-10-02 판을 읽고 대조).
- 특히 자주 가리키는 leaf
  - [01-complexity](../01-complexity/2-summary.md) · [10-code-smells](../10-code-smells/2-summary.md) · [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 변경 증폭, 스멜, 이력으로 보는 결합
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md) · [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md) · [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — 불법 상태, NPE, 기본 분기
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) · [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md) · [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 기동 실패, 프록시, 자동 설정
  - [40-codebase-structure](../40-codebase-structure/2-summary.md) · [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md) · [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md) — 폴더 4개, 규칙 테스트, 같이 배포
- 후속: [56-design-incidents](../56-design-incidents/2-summary.md) — 실사건(Therac-25, Healthcare.gov)에서 설계 결함이 어떻게 이어졌나
- 다른 영역 색인: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md) · [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)
- 근거 문서
  - 커리큘럼 §12 머리말("깨지면"은 변경 비용 폭증·조용한 결합) — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`
  - JEP 358 "Helpful NullPointerExceptions"(Release 14) <https://openjdk.org/jeps/358> — 지역 변수 표가 없으면 `<local i>`로 쓴다는 규칙. JDK 21.0.12의 실제 문구는 이 노트의 실행으로 확인
  - JEP 441 "Pattern Matching for switch"(JDK 21) <https://openjdk.org/jeps/441> — `switch` 식의 망라성 검사는 이 노트의 실행(javac 21.0.12)으로 확인
  - `java.lang.annotation.Retention` API 문서(JDK 21) — 보존 정책을 생략하면 `CLASS` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/annotation/Retention.html>
  - 프레임워크·도구 메시지는 각 leaf의 실험 출력을 따른다: Spring Framework 6.2.11(25·33), Spring Boot 3.5.6(36), Spring Framework 6.2.19(16), ArchUnit 1.5.1(41)·1.4.1(39), dependency-cruiser 18.5.0(41), PMD 7.28.0(10·52), Mockito 5.20.0(26), Jackson 2.22.3·Hibernate ORM 7.4.11(43), Express 5.2.1·Koa 2.16.4(34), MapStruct 1.6.3(35)
- 실험 목록
  - 메시지 확인: `scratchpad/sd/55/e55/Msgs.java`(보존 정책 CLASS·RUNTIME, helpful NPE, `Optional.get`, `List.of().add`), `sw/Status.java`(sealed `switch` 망라성) — JDK 21.0.12 temurin 컨테이너 `--cpus=2`. `javac` / `javac -g` 비교로 NPE 지역 변수 표기 확인.
  - 기동 스위치 범위: `scratchpad/sd/adj-55/Cyc.java`(25 실험 E — 순환 허용 켬/끔 × 생성자·필드 순환, `@Lazy`), `scratchpad/sd/adj-55/boot36/runB.sh`(36 실험 B의 변형 B + 덮어쓰기 허용, Spring Boot 3.5.6) — JDK 21.0.12 temurin 컨테이너 `--cpus=2`.
  - 첫 진단 명령: `scratchpad/sd/55/e55/diag.sh` — git 2.43.0, 커밋 6개 장난감 저장소에서 `git show --stat`, 변경 빈도, 공동 변경 쌍 집계. 출력 `diag-output.txt`.
