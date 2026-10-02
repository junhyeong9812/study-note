# software-design/41-architecture-fitness-rules — 경계를 테스트로 강제하기 — 정리 (힌트)

## 해결하는 문제

가시성(40)으로 막을 수 없는 규칙이 남는다.

```text
 가시성으로 막히는 것                    가시성으로 안 막히는 것
 패키지 밖에서 숨긴 구현을 쓰기          domain → web import (web 타입이 public이면 가능)
                                         패키지·모듈 사이 순환
                                         "Controller로 끝나는 클래스는 web 패키지에" 같은 명명 규칙
```

이런 규칙이 위키·리뷰 코멘트에만 있으면 사람이 매번 잡아야 한다. 놓치면 조용히 쌓인다.

- *아키텍처 적합도 함수(architecture fitness function)*: 아키텍처 특성이 지켜지는지 자동으로 확인하는 검사. Ford·Parsons·Kua·Sadalage 『Building Evolutionary Architectures』 2판(2022) 2장 제목이 "Fitness Functions"다(O'Reilly 목차).
- *아키텍처 규칙 테스트*: 의존 방향·순환·명명을 단위 테스트처럼 빌드에서 돌리는 것. Java는 ArchUnit, JS/TS는 dependency-cruiser, Python은 import-linter.

쉬운 예: 맞춤법 규칙을 문서로 나눠 주는 것과 저장할 때 맞춤법 검사기가 빨간 줄을 긋는 것의 차이다.\
똑같은 구조다: 규칙 문서 → 실행되는 검사.\
실무 예: "도메인은 컨트롤러를 import하지 않는다"를 ArchUnit 규칙으로 두면, 신규 입사자의 PR이 리뷰 전에 CI에서 실패한다.

## 동작·원리

### 1. 규칙 검사기는 의존 그래프를 만들고 규칙을 대조한다

```text
 바이트코드/소스 ──(import·호출·필드 타입 수집)──> 의존 그래프 ──(규칙: 경로 패턴 매칭)──> 위반 목록
 ArchUnit: .class 파일              정점 = 클래스(→ 패키지·슬라이스로 묶음)          layeredArchitecture()
 dependency-cruiser: JS/TS 소스      간선 = 이 클래스가 저 클래스를 쓴다               slices().beFreeOfCycles()
```

- ArchUnit은 Java **바이트코드**를 분석해 클래스 구조를 가져온다(ArchUnit 사용자 가이드 1.5.1 소개). 컴파일 뒤에 돈다.
- 규칙은 "어떤 패키지 패턴의 클래스가 어떤 패키지 패턴에 의존하면 안 된다" 같은 **경로 규칙**이다. `..web..`처럼 와일드카드를 쓴다.
- *슬라이스(slice)*: 패키지 패턴으로 클래스를 묶은 단위. `com.shop.(*)..`는 `com.shop` 바로 아래 패키지 이름마다 슬라이스 하나다.

### 실험 A: 계층 규칙과 순환 규칙

일부러 위반 두 종류를 넣은 작은 앱을 ArchUnit 1.5.1로 검사했다.

```text
 com.shop.web.OrdersController ──> com.shop.service.OrdersService ──> com.shop.repository.OrdersRepository ──> com.shop.domain.Order
 com.shop.web.OrderHistoryController ──────────────────────────────> repository        (위반 1: 서비스 우회)
 com.shop.domain.Order.pageSize() ──> web.OrdersController.PAGE_SIZE                     (위반 2: 도메인 → 웹, 순환)
```

```java
static ArchRule layers() {
    return layeredArchitecture().consideringOnlyDependenciesInLayers()
        .layer("Web").definedBy("com.shop.web..")
        .layer("Service").definedBy("com.shop.service..")
        .layer("Repository").definedBy("com.shop.repository..")
        .layer("Domain").definedBy("com.shop.domain..")
        .whereLayer("Web").mayNotBeAccessedByAnyLayer()
        .whereLayer("Service").mayOnlyBeAccessedByLayers("Web")
        .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service");
}
static ArchRule noCycles() { return slices().matching("com.shop.(*)..").should().beFreeOfCycles(); }
// 실행: rule.check(new ClassFileImporter().importPath("out")) — 위반이면 AssertionError
```

(실험, ArchUnit 1.5.1, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/40/e41/run.sh`, 2026-10-02 — 일부 줄 생략)

```text
[FAIL] 계층 규칙
... was violated (3 times):
Method <com.shop.domain.Order.pageSize()> gets field <com.shop.web.OrdersController.PAGE_SIZE> in (Order.java:4)
Method <com.shop.web.OrderHistoryController.history()> calls constructor <com.shop.repository.OrdersRepository.<init>()> in (OrderHistoryController.java:4)
Method <com.shop.web.OrderHistoryController.history()> calls method <com.shop.repository.OrdersRepository.findAll()> in (OrderHistoryController.java:4)
[FAIL] 순환 없음
Architecture Violation [Priority: MEDIUM] - Rule 'slices matching 'com.shop.(*)..' should be free of cycles' was violated (3 times):
Cycle detected: Slice domain -> 
                Slice web -> 
                Slice repository -> 
                Slice domain
...
Cycle detected: Slice domain -> 
                Slice web -> 
                Slice service -> 
                Slice domain
...
Cycle detected: Slice domain -> 
                Slice web -> 
                Slice service -> 
                Slice repository -> 
                Slice domain
```

- 관찰 1 — 위반은 파일·줄 번호와 함께 **메서드·필드 수준**으로 나온다. 어디를 고칠지 바로 보인다.
- 관찰 2 — 도메인 → 웹 간선 **하나**가 순환 3개를 만들었다. 웹은 이미 서비스·리포지토리를 거쳐 도메인에 닿으므로, 거꾸로 된 간선 하나가 그 경로들을 각각 고리로 닫는다.

### 2. 기존 위반 동결(baseline)

오래된 코드에 규칙을 처음 넣으면 위반이 수백 개 나온다. 다 고칠 때까지 규칙을 못 켜면 그사이 위반이 더 쌓인다.\
ArchUnit의 `FreezingArchRule`은 첫 실행의 위반을 저장소(기본: 일반 텍스트 파일)에 기록한다. 다음 실행부터는 **새 위반만** 보고하고, 고친 위반은 저장소에서 자동으로 줄인다(ArchUnit 사용자 가이드 8.6절).

```text
 1회차: 위반 3건 → 저장, PASS        (archunit.properties: freeze.store.default.allowStoreCreation=true)
 2회차: 같은 3건 → PASS
 새 위반 추가 → 새 것만 FAIL
 기존 위반을 고침 → 저장소 줄 수 감소(되돌아가면 다시 FAIL)
```

### 실험 B: 동결의 네 단계

(실험, 같은 환경, `run.sh`·`run2.sh`, 2026-10-02)

```text
===== 2) 동결 첫 실행 (기존 위반을 기준선으로 저장)
[PASS] 계층 규칙(동결)
ef1a51cb-320e-44f5-a063-3386b37a9078
stored.rules
===== 3) 동결 두 번째 실행 (변경 없음)
[PASS] 계층 규칙(동결)
===== 4) 새 위반 추가 (NewController → repository) 후 동결 실행
[FAIL] 계층 규칙(동결)
... was violated (2 times):
Method <com.shop.web.NewController.n()> calls constructor <com.shop.repository.OrdersRepository.<init>()> in (NewController.java:3)
Method <com.shop.web.NewController.n()> calls method <com.shop.repository.OrdersRepository.findAll()> in (NewController.java:3)
===== 6) 기존 우회 고친 뒤 동결 실행 → 저장소 줄 수
3 frozen/ef1a51cb-320e-44f5-a063-3386b37a9078
[PASS] 계층 규칙(동결)
0 frozen/ef1a51cb-320e-44f5-a063-3386b37a9078
```

- 4단계: 기존 3건은 조용하고 새 2건만 실패했다.
- 6단계: 기존 위반을 고치자 저장소가 3줄 → 0줄이 됐다. 같은 위반을 다시 넣으면 이제 "새 위반"이다.
- 가이드는 CI에서 `allowStoreCreation`을 켜지 말라고 권한다(저장소가 없을 때 새로 만들어 버리면 검사가 무력해진다). 저장소 파일은 VCS에 넣어 진행을 추적한다.

### 3. 순환 제거 기법

```text
 (1) DIP 역전           A ──> B 를 A ──> «IB» <── B 로. 인터페이스를 쓰는 쪽(A)에 둔다.
 (2) 공통부 추출        A ──> B, B ──> A 의 공통 부분 C를 떼어 A ──> C <── B
 (3) 합치기             둘이 늘 함께 바뀌면 원래 한 모듈이다. 합친다.
 (4) 이벤트             B가 A를 부르는 대신 이벤트를 내고 A가 구독한다(컴파일 의존 제거, 대신 흐름 추적이 어려워짐).
 (5) 값의 위치 옮기기   상수·설정처럼 "누가 소유하나"가 틀린 경우 소유자 쪽으로 옮긴다.
```

### 실험 C: 순환 끊기 두 가지

Java — 도메인이 웹의 `PAGE_SIZE`를 읽던 것을 도메인 상수로 옮기고 웹이 그것을 읽게 했다(값의 소유자를 바로잡아 간선 방향을 뒤집음).

(실험, 같은 환경, `run2.sh` 5단계)

```text
[FAIL] 계층 규칙
where layer 'Repository' may only be accessed by layers ['Service']' was violated (2 times):
Method <com.shop.web.OrderHistoryController.history()> calls constructor <com.shop.repository.OrdersRepository.<init>()> in (OrderHistoryController.java:4)
Method <com.shop.web.OrderHistoryController.history()> calls method <com.shop.repository.OrdersRepository.findAll()> in (OrderHistoryController.java:4)
[PASS] 순환 없음
```

JS — `orders ↔ billing` 순환을 dependency-cruiser 18.5.0으로 잡고, 가격 합계 함수를 `pricing`으로 추출(공통부 추출)했다.

```js
// .dependency-cruiser.cjs
module.exports = { forbidden: [
  { name: 'no-circular', severity: 'error', from: {}, to: { circular: true } },
  { name: 'domain-not-to-web', severity: 'error', from: { path: '^src/(orders|billing)' }, to: { path: '^src/web' } },
]};
```

(실험, node v22.23.2 `node:22-alpine`, dependency-cruiser 18.5.0, `scratchpad/sd/40/e41/js`, 2026-10-02)

```text
  error no-circular: src/billing/invoice.js → 
      src/orders/order.js →
      src/billing/invoice.js

x 1 dependency violations (1 errors, 0 warnings). 3 modules, 3 dependencies cruised.

exit=1
{ items: [ 1000, 2000 ], invoice: 'INV-3000' }
```

`pricing/total.js`로 합계 함수를 추출한 뒤 같은 명령:

```text
✔ no dependency violations found (4 modules, 4 dependencies cruised)

exit=0
{ items: [ 1000, 2000 ], invoice: 'INV-3000' }
```

- 관찰 — 순환이 있을 때도 프로그램은 **정상 실행**됐다(마지막 줄). ES 모듈은 함수가 나중에 호출되면 순환을 견딘다. 그래서 순환은 실행으로는 드러나지 않고 조용히 쌓인다. 검사가 필요한 이유다.

### 4. 바이트코드 검사의 사각: 컴파일 타임 상수

(실험, 같은 환경, `run3.sh`, 2026-10-02) — 도메인이 웹의 `public static final int PAGE_SIZE_CONST = 20`을 읽게 바꿨다. 소스에는 `import com.shop.web.OrdersController`가 있다.

```text
===== 7) 도메인 → 컨트롤러의 컴파일 타임 상수(static final int) 참조
[PASS] 계층 규칙
[PASS] 순환 없음
-- javap: Order.pageSize() 바이트코드
  public static int pageSize();
    Code:
       0: bipush        20
       2: ireturn
```

- 소스에는 도메인 → 웹 의존이 있는데 두 규칙 모두 통과했다.
- 원인: Java 언어 명세(JLS 21, 13.1절)상 상수 변수 참조는 컴파일 때 값으로 바뀐다. 바이트코드에는 `bipush 20`만 남고 `OrdersController` 참조가 없다. `import` 문도 바이트코드에 남지 않는다.
- 결과: 바이트코드 기반 도구(ArchUnit·jdeps)는 이 의존을 보지 못한다. 상수 값이 바뀌면 도메인을 다시 컴파일하지 않는 한 옛 값이 남는다는 위험도 같은 원인이다(JLS 13.4.9 절이 이 이진 호환성 문제를 다룬다).
- 대처: 상수의 소유자를 바로잡는다(도메인 상수는 도메인에). 소스 수준 import 규칙이 필요하면 소스 기반 검사(Checkstyle `ImportControl` 등)를 함께 쓴다 — 이 노트에서 실행하지 않았다 [?].

## 쓰이는 자료구조·알고리즘

- **의존 그래프** — 정점 = 클래스(또는 모듈 파일), 간선 = 사용 관계. ArchUnit은 바이트코드의 호출·필드 접근·타입 참조·애너테이션에서 간선을 만든다(실험 A 전체 출력에 `calls method`, `gets field`, `has generic return type` 같은 종류가 찍힌다).
- **순환 탐지** — 슬라이스 그래프에서 순환을 찾는다. ArchUnit은 `CycleDetector` 핵심 API를 따로 공개한다(가이드 8.2.2절). 탐지할 순환 수 상한 `cycles.maxNumberToDetect`는 기본 100, 간선마다 보고할 의존 수 `cycles.maxNumberOfDependenciesPerEdge`는 기본 20이다(가이드 8.2.1절 설정 예시의 주석). 실험 A 출력의 `...`는 노트에 옮기며 생략한 부분이다. 그래프에서 "서로 닿는 정점 묶음"을 찾는 표준 알고리즘은 강연결요소(SCC, Tarjan·Kosaraju) — [algorithm/18-scc](../../algorithm/18-scc/2-summary.md). 순환이 하나라도 있으면 그 정점들은 크기 2 이상인 SCC에 함께 들어간다.
- **경로 패턴 매칭** — `..web..`, `com.shop.(*)..` 같은 패키지 패턴(ArchUnit), 정규식 경로(dependency-cruiser `path: '^src/web'`).
- **동결 저장소** — 규칙별 위반 문자열 목록(텍스트 파일). 기본은 줄 번호를 무시하고 비교해서, 코드가 다른 줄로 밀려도 같은 위반으로 본다(가이드 8.6.1).

## 적용 — 풀어나가는 법

### 1. 순서

1. **규칙을 문장으로 먼저**: "웹은 리포지토리를 직접 쓰지 않는다", "도메인은 프레임워크·웹을 모른다", "컴포넌트 사이 순환 없음".
2. **가시성으로 막을 수 있으면 그게 먼저**다(40). 테스트는 컴파일보다 늦게 실패한다. Brown도 가능하면 컴파일러를 쓰라고 권한다.
3. **나머지를 규칙 테스트로**: Java는 ArchUnit(가이드 1.5.1 기준 JUnit 4, JUnit 5·6 통합 제공), JS/TS는 dependency-cruiser, Python은 import-linter(계약 종류: Forbidden, Layers, Independence, Protected, Acyclic siblings — import-linter 문서 `docs/contract_types/`).
4. **오래된 코드는 동결부터**: `FreezingArchRule`로 기준선을 커밋하고 CI에서는 저장소 생성을 막는다. 새 위반 0을 유지하며 기존 위반을 줄인다.
5. **순환은 기법을 골라 끊는다**: 값 소유자 바로잡기 → DIP → 공통부 추출 → 합치기 → 이벤트 순으로 비용이 커진다(해석).
6. **사각을 안다**: 바이트코드 도구는 상수 인라인·리플렉션·문자열 기반 호출을 못 본다(4절 실험은 상수 인라인 사례).

### 2. 코드 (JUnit 5 + ArchUnit)

```java
@AnalyzeClasses(packages = "com.shop")
class ArchitectureTest {
    @ArchTest
    static final ArchRule layers = FreezingArchRule.freeze(
        layeredArchitecture().consideringOnlyDependenciesInLayers()
            .layer("Web").definedBy("..web..")
            .layer("Service").definedBy("..service..")
            .layer("Repository").definedBy("..repository..")
            .whereLayer("Web").mayNotBeAccessedByAnyLayer()
            .whereLayer("Service").mayOnlyBeAccessedByLayers("Web")
            .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service"));

    @ArchTest
    static final ArchRule noCycles = slices().matching("com.shop.(*)..").should().beFreeOfCycles();

    @ArchTest
    static final ArchRule domainIsPure = noClasses().that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAnyPackage("..web..", "jakarta.persistence..", "org.springframework..");
}
```

- 실험은 JUnit 없이 `rule.check(classes)`를 `main`에서 돌렸다. 위 `@AnalyzeClasses`·`@ArchTest`는 가이드의 JUnit 통합 방식이며 이 노트에서 JUnit으로 실행하지는 않았다.

### 3. 진단 명령

```bash
npx depcruise src --validate .dependency-cruiser.cjs     # JS/TS
lint-imports                                              # Python import-linter (설정: setup.cfg·.importlinter·pyproject.toml — 문서 get_started/configure) 이 노트에서 실행 안 함
jdeps -verbose:package -filter:none build/classes/java/main | grep -v java.base   # 빠른 그래프 확인
```

## 장애 시나리오와 대처

### 1. 다이어그램에는 계층이 있는데 코드는 도메인 → 컨트롤러 import (⚠ 커리큘럼)

- 현상: 도메인 클래스를 다른 서비스에 재사용하려니 웹 모듈까지 따라온다.
- 보이는 형태: ArchUnit 계층 규칙 `Method <...domain...> gets field <...web...>`, 순환 규칙 `Cycle detected: Slice domain -> Slice web -> ...`(실험 A).
- 원인: 값(설정·상수)의 소유자가 틀렸다. 규칙이 실행되지 않아 아무도 몰랐다.
- 대처: 값을 도메인으로 옮기고 웹이 읽게 한다(실험 C: 순환 PASS). 도메인 순수성 규칙을 추가한다. 컴파일 타임 상수는 바이트코드에서 사라지므로(4절) 규칙만 믿지 않는다.

### 2. 모듈 A↔B 순환으로 A만 떼어 배포·테스트 불가 (⚠ 커리큘럼)

- 현상: `orders`만 테스트하려 해도 `billing`이 필요하고, 반대도 그렇다. 둘을 따로 배포할 수 없다.
- 보이는 형태: dependency-cruiser `error no-circular: src/billing/invoice.js → src/orders/order.js → src/billing/invoice.js`. 프로그램은 정상 실행된다(실험 C).
- 원인: 둘이 서로의 일부(합계 계산)를 소유하고 있다.
- 대처: 공통부(`pricing/total.js`)를 추출하자 위반 0. 둘이 늘 함께 바뀐다면 추출 대신 합친다.

### 3. 규칙이 위키에만 있어 PR마다 같은 지적 반복 (⚠ 커리큘럼)

- 현상: 신규 입사자 PR마다 "컨트롤러에서 리포지토리 쓰지 마세요" 코멘트가 붙는다. 리뷰어가 바쁠 때는 빠진다.
- 보이는 형태: 리뷰 코멘트 이력에 같은 문장이 반복. `jdeps`로 보면 우회 간선이 몇 개 이미 들어와 있다.
- 원인: 규칙이 실행되지 않는다.
- 대처: 규칙 테스트로 옮기고 기존 위반은 동결한다(실험 B). 리뷰는 규칙이 다루지 못하는 판단에 쓴다.

### 4. 동결 저장소가 CI에서 새로 만들어져 검사가 무력해진다

- 현상: 새 위반을 넣었는데 CI가 통과한다.
- 보이는 형태: CI 로그에 저장소 생성 흔적. 저장소 파일이 VCS에 없다.
- 원인: CI에서 `freeze.store.default.allowStoreCreation=true`. 매 빌드가 "첫 실행"이 되어 현재 위반을 전부 기준선으로 삼는다.
- 대처: 저장소를 VCS에 커밋하고 CI에서는 생성을 막는다(가이드 8.6.2가 권하는 설정). 기준선 갱신(`freeze.refreeze=true`)은 의도한 결정일 때만.

### 5. 규칙이 너무 거칠거나 틀려서 무시된다

- 현상: 정당한 의존까지 막아 개발자가 규칙을 끄거나 예외를 남발한다.
- 원인: 규칙이 실제 설계 의도가 아니라 폴더 이름을 기준으로 쓰였다.
- 대처: 규칙마다 이유(어떤 변경을 지키려는가)를 주석으로 둔다. CQRS 읽기 경로처럼 의도된 우회는 Brown도 예외로 든다 — 규칙에 명시적 예외로 표현한다.

## 핵심 문장

- 가시성으로 막을 수 없는 규칙(의존 방향·순환·명명)은 실행되는 테스트로 강제한다. 위키 규칙은 리뷰어가 바쁠 때 사라진다.
- 실험에서 도메인 → 웹 간선 하나가 슬라이스 순환 3개를 만들었고, 값의 소유자를 도메인으로 옮기자 순환 규칙이 통과했다.
- `FreezingArchRule`은 기존 위반을 기준선으로 저장해 새 위반만 실패시키고, 고친 위반은 저장소에서 줄인다(실험: 새 2건만 FAIL, 고친 뒤 저장소 3줄 → 0줄).
- 순환이 있어도 프로그램은 돌아간다(dependency-cruiser 실험의 정상 출력). 그래서 순환은 검사 없이는 조용히 쌓인다.
- 바이트코드 기반 검사는 컴파일 타임 상수 참조를 보지 못한다. 실험에서 도메인 → 웹 `static final int` 참조가 두 규칙을 모두 통과했다.

## 관련 주제·근거

- 선행
  - [40-codebase-structure](../40-codebase-structure/2-summary.md) — 가시성으로 먼저 막고, 남는 규칙만 테스트로
  - [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) — 순환 탐지(SCC)
- 후속·연결
  - [44-architecture-in-code](../44-architecture-in-code/2-summary.md) — 도메인 순수성 규칙을 세 스타일에 적용
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 계층 규칙의 원리
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 기존 위반을 어디부터 줄일지
  - [39 component-principles](../39-component-principles/2-summary.md)(ADP 비순환 의존 원칙)
- 글·문서
  - ArchUnit User Guide 1.5.1 — 바이트코드 분석, 4.7 Cycle Checks, 8.2.2 CycleDetector, 8.6 Freezing Arch Rules <https://www.archunit.org/userguide/html/000_Index.html>
  - dependency-cruiser README·규칙 참조 <https://github.com/sverweij/dependency-cruiser>
  - import-linter 계약 종류(Forbidden·Protected·Layers 등) <https://github.com/seddonym/import-linter/tree/master/docs/contract_types>
  - Ford·Parsons·Kua·Sadalage, 『Building Evolutionary Architectures』 2판(O'Reilly, 2022) 2장 "Fitness Functions" — O'Reilly 장 페이지 제목으로 확인, 본문 미열람 [?] <https://www.oreilly.com/library/view/building-evolutionary-architectures/9781492097532/ch02.html>
  - Simon Brown, "Package by component" — 정적 분석으로 아키텍처 위반을 잡는 방식의 한계(피드백이 늦다)와 컴파일러 선호 <https://simonbrown.je/modular-monolith>
  - JLS (Java SE 21) 13.1절 상수 변수 참조의 컴파일 시 해석, 13.4.9절 <https://docs.oracle.com/javase/specs/jls/se21/html/jls-13.html>
- 실험 목록 (코드: scratchpad `sd/40/e41/`, ArchUnit 1.5.1 jar는 Maven Central에서 `sd/40/libs/`로 받음, JDK 21.0.12 temurin `--cpus=2`)
  - A 계층·순환 규칙 — `run.sh` 1단계
  - B 동결 — `run.sh` 2·3단계, `run2.sh` 4·6단계(저장소 `frozen/`)
  - C 순환 끊기 — Java: `run2.sh` 5단계 / JS: `js/`에서 `npx depcruise src --validate .dependency-cruiser.cjs` 전후(node:22-alpine, dependency-cruiser 18.5.0)
  - 상수 인라인 사각 — `run3.sh`(ArchUnit 두 규칙 PASS + `javap -c`)
