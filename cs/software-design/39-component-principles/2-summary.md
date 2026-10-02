# software-design/39-component-principles — 컴포넌트 원칙: REP·CCP·CRP·ADP·SDP·SAP — 정리 (힌트)

## 해결하는 문제

클래스를 잘 나눠도, 그 클래스들을 **배포 단위(jar·모듈·패키지)** 로 묶는 방법이 나쁘면 따로 빌드·배포할 수 없다.

```text
 entities.jar ──> web.jar ──> usecases.jar ──> entities.jar      (순환)
     │
     └ "entities만 고쳐서 먼저 릴리스" 불가 — web이 필요하고, web은 usecases가, usecases는 entities가 필요
       → 셋은 사실상 한 덩어리. 하나 바뀌면 함께 빌드·시험·배포해야 한다
```

- *컴포넌트(component)*: 배포 단위. Java의 jar·Maven 모듈·JPMS 모듈, JS의 npm 패키지. Martin의 1990년대 글에서는 "package", 『Clean Architecture』(2017)에서는 "component"라고 부른다.
- *컴포넌트 원칙*: 무엇을 한 컴포넌트에 묶을지(응집 3원칙: REP·CCP·CRP)와 컴포넌트 사이 의존을 어떻게 둘지(결합 3원칙: ADP·SDP·SAP).

쉬운 예: 이사할 때 상자를 싸는 기준이다. 같이 쓰는 물건을 같은 상자에(CRP), 같은 이유로 버릴 물건을 같은 상자에(CCP). 상자끼리 서로를 받치게 쌓으면(순환) 하나를 먼저 뺄 수 없다(ADP).\
똑같은 구조다.\
실무 예: 멀티 모듈 Gradle·Maven 프로젝트에서 `common` 모듈이 `api` 모듈을 참조하기 시작하면, `common`을 쓰는 모듈이 `api`의 변경에도 끌려간다.

## 동작·원리

### 1. 응집 3원칙 — 무엇을 함께 묶나

```text
            REP (재사용 단위 = 릴리스 단위)
               /\
              /  \      세 원칙은 서로 당긴다
             /    \     - REP·CCP만: 불필요한 릴리스가 잦다 (CRP 무시)
            /      \    - CCP·CRP만: 재사용하기 어렵다 (REP 무시)
           /________\   - REP·CRP만: 변경 하나에 컴포넌트 여러 개 (CCP 무시)
        CCP          CRP
  (같은 이유로 바뀌는   (같이 쓰이는 것끼리 —
   것끼리 묶는다)       안 쓰는 것에 끌려가지 않게)
```

Martin, "Granularity"(C++ Report 「Engineering Notebook」 다섯 번째 칼럼)의 원문 정의:

- *REP(Reuse/Release Equivalence Principle)*: "THE GRANULE OF REUSE IS THE GRANULE OF RELEASE." 추적 시스템(버전)으로 릴리스된 단위만 효과적으로 재사용된다.
- *CCP(Common Closure Principle)*: 한 패키지의 클래스는 같은 종류의 변경에 함께 닫혀 있어야 한다. 변경이 패키지에 영향을 주면 그 안 모든 클래스에 준다. 클래스 수준 SRP의 컴포넌트 판이다.
- *CRP(Common Reuse Principle)*: 한 패키지의 클래스는 함께 재사용된다. 하나를 쓰면 전부를 쓰는 것이다. 그래서 함께 쓰이지 않는 것은 떼어 놓는다(ISP의 컴포넌트 판).
- 세 원칙의 긴장 삼각형 그림은 『Clean Architecture』 13장 "Component Cohesion"의 내용으로 알려져 있으나, 이 노트에서는 장 제목(InformIT 목차)만 확인했다 [?]. 위 그림의 "무시하면 생기는 증상"은 각 원칙 정의에서 나온 해석이다.

### 2. 결합 3원칙 — 컴포넌트 사이 의존을 어떻게 두나

```text
 ADP: 의존 그래프에 순환이 없어야 한다 (DAG)

 SDP: 의존은 안정된 쪽으로                 SAP: 안정된 것은 추상적이어야
   불안정(I≈1)  web ──┐                     A ▲
                      ▼                    1 │ 쓸모없음 지대       ╲
   중간       usecases                      │  (추상인데 아무도   ╲ 주계열 A + I = 1
                      ▼                      │   의존 안 함)        ╲
   안정(I≈0)  entities                       │ ╲                      
   (많이 의존받고, 거의 의존하지 않음)          │   ╲  고통 지대 (구체적인데 모두가 의존 — 바꾸기 어렵다)
                                           0 └──────────────────────> I
                                             0                      1
```

- *ADP(Acyclic Dependencies Principle)*: "THE DEPENDENCY STRUCTURE BETWEEN PACKAGES MUST BE A DIRECTED ACYCLIC GRAPH (DAG)." Martin은 순환이 있으면 남이 늦게 남긴 변경 때문에 다음 날 내 코드가 깨지는 "morning after syndrome"을 막을 수 없다고 쓴다("Granularity").
- *SDP(Stable Dependencies Principle)*: 패키지 사이 의존은 안정성 방향이어야 한다. 자신보다 안정된 패키지에만 의존한다("Stability", 여섯 번째 칼럼).
- *SAP(Stable Abstractions Principle)*: 가장 안정된 패키지는 가장 추상적이어야 하고, 불안정한 패키지는 구체적이어야 한다. 추상성은 안정성에 비례한다("Stability").
- 그림의 지대 이름(고통 지대·쓸모없음 지대)은 『Clean Architecture』 14장의 것으로 알려져 있다 [?]. "Stability" 칼럼은 (0,0) 근처와 (1,1) 근처를 둘 다 "zone of exclusion"(피해야 할 지대)이라고만 부르고, 그 사이 선을 "Main Sequence"라고 부른다. (0,0)의 예로 DB 스키마를 든다.

### 3. 숫자로 재기 — Martin 1994 지표

Martin, "OO Design Quality Metrics: An Analysis of Dependencies"(1994-10-28)의 정의:

```text
 Ca (afferent, 들어오는 결합) = 이 컴포넌트 밖에서 안의 클래스에 의존하는 클래스 수
 Ce (efferent, 나가는 결합)   = 이 컴포넌트 안에서 밖의 클래스에 의존하는 클래스 수
 I  (불안정도)  = Ce / (Ca + Ce)            0 = 최대 안정, 1 = 최대 불안정
 A  (추상도)    = 추상 클래스 수 / 전체 클래스 수
 D  (주계열 거리) = |A + I − 1| / √2  범위 0~0.707
 Dn (정규화)    = |A + I − 1|         범위 0~1
```

- "안정"은 바꾸기 어렵다는 뜻이지 좋다는 뜻이 아니다. 많은 것이 의존하면(Ca 큼) 바꿀 때 영향이 커서 잘 안 바뀐다.

### 실험 A: 컴포넌트 넷의 지표와 순환 — 빌드 순서가 사라진다

`entities`·`usecases`·`db`·`web` 네 jar. acyclic판은 `Order.describe(MoneyFormat)`처럼 표시 형식을 인터페이스로 받는다. cyclic판은 엔티티가 웹 유틸을 직접 쓴다.

```java
// cyclic판 entities/Order.java
import comp.web.WebFormat;
public String describe() { return id + " " + new WebFormat().format(amount); }   // 엔티티가 웹 형식을 직접 안다
// acyclic판 — 인터페이스는 entities가 소유, 구현은 web
public interface MoneyFormat { String format(Money m); }                          // comp.entities
public String describe(MoneyFormat f) { return id + " " + f.format(amount); }
public class WebFormat implements MoneyFormat { ... }                              // comp.web
```

측정 도구(`Metrics.java`)는 `jdeps -verbose:class` 출력으로 Ca·Ce를 세고, jar를 로드해 A를 세고, 컴포넌트 그래프에서 Tarjan SCC를 구한다. 표의 `Fi` 열은 Ca(들어오는 결합), `Fo` 열은 Ce(나가는 결합)이고, `D` 열은 정규화형 Dn = |A+I−1|이다.

```java
static void tarjan(String v, ...) {
    idx.put(v, counter[0]); low.put(v, counter[0]++); st.push(v); on.add(v);
    for (String w : g.getOrDefault(v, Set.of())) {
        if (!idx.containsKey(w)) { tarjan(w, ...); low.put(v, Math.min(low.get(v), low.get(w))); }
        else if (on.contains(w)) low.put(v, Math.min(low.get(v), idx.get(w)));
    }
    if (low.get(v).equals(idx.get(v))) { /* 스택에서 v까지 꺼낸 것이 SCC 하나 */ }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e39/run.sh`, 2026-10-02)

```text
######## acyclic
== 컴포넌트를 하나씩 빌드 (entities → usecases → db → web 순서, 앞 jar만 클래스패스)
  entities.jar 빌드 OK
  usecases.jar 빌드 OK
  db.jar 빌드 OK
  web.jar 빌드 OK
== 한꺼번에 컴파일해 jar로 나눈 뒤 지표
insert o-1
o-1 12,000원
컴포넌트   Fi  Fo     I     A     D   의존 대상
entities    5   0  0.00  0.50  0.50   []
usecases    2   2  0.50  0.50  0.00   [entities]
db          1   1  0.50  0.00  0.50   [entities, usecases]
web         0   2  1.00  0.00  0.00   [db, entities, usecases]
SCC: [[entities], [usecases], [db], [web]]
순환 없음 → 빌드 순서(역 위상): [[entities], [usecases], [db], [web]]
######## cyclic
== 컴포넌트를 하나씩 빌드 (entities → usecases → db → web 순서, 앞 jar만 클래스패스)
  entities 빌드 실패: cyclic/entities/comp/entities/Order.java:2: error: package comp.web does not exist
  usecases 빌드 실패: cyclic/usecases/comp/usecases/OrderGateway.java:2: error: package comp.entities does not exist
  db 빌드 실패: cyclic/db/comp/db/SqlOrderGateway.java:2: error: package comp.entities does not exist
  web 빌드 실패: cyclic/web/comp/web/WebFormat.java:3: error: cannot find symbol
== 한꺼번에 컴파일해 jar로 나눈 뒤 지표
insert o-1
o-1 12,000원
컴포넌트   Fi  Fo     I     A     D   의존 대상
entities    5   1  0.17  0.50  0.33   [web]
usecases    2   2  0.50  0.50  0.00   [entities]
db          1   1  0.50  0.00  0.50   [entities, usecases]
web         1   2  0.67  0.00  0.33   [db, entities, usecases]
SCC: [[usecases, web, entities, db]]
순환 있음 → 위상 순서(빌드 순서) 없음
```

- 관찰 1 — acyclic판은 의존 순서대로 jar를 **하나씩** 빌드할 수 있었다. 각 SCC가 컴포넌트 하나다.
- 관찰 2 — cyclic판은 import 한 줄로 네 컴포넌트가 **SCC 하나**가 됐다. `entities`가 `web`을 요구하니 첫 단계부터 빌드가 막혔고, 뒤는 연쇄로 실패했다. 둘 다 프로그램은 똑같이 돌았다(`o-1 12,000원`). 순환은 실행이 아니라 **독립 빌드·릴리스**를 깨뜨린다.
- 관찰 3(SDP) — cyclic판에서 `entities`(I=0.17)가 `web`(I=0.67)에 의존한다. 더 안정된 쪽이 덜 안정된 쪽에 기댄 SDP 위반이다. `entities`의 I가 0 → 0.17로, `web`의 Ca가 0 → 1로 바뀌었다.
- 관찰 4(SAP) — 두 판 모두 `entities`는 가장 안정(I≈0)한데 A=0.5라 Dn이 0.33~0.5다. 엔티티는 구체 값 객체(`Order`·`Money`)가 핵심이라 추상도가 낮은 것이 자연스럽다. 지표는 판정이 아니라 **질문거리**다.

(전체 출력은 `e39/run-output.txt`.)

### 실험 B: ArchUnit의 순환 검사 — SCC 하나 안의 여러 순환

```java
slices().matching("comp.(*)..").should().beFreeOfCycles()
```

(실험, ArchUnit 1.4.1, 같은 환경, `scratchpad/sd/35/e39/Cycles.java`, 2026-10-02 — 발췌, 전체는 `cycles-output.txt`)

```text
cyclic/all: 순환 위반
Architecture Violation [Priority: MEDIUM] - Rule 'slices matching 'comp.(*)..' should be free of cycles' was violated (4 times):
Cycle detected: Slice db -> 
                Slice entities -> 
                Slice web -> 
                Slice db
...
Cycle detected: Slice entities -> 
                Slice web -> 
                Slice entities
  1. Dependencies of Slice entities
    - Method <comp.entities.Order.describe()> calls constructor <comp.web.WebFormat.<init>()> in (Order.java:8)
    - Method <comp.entities.Order.describe()> calls method <comp.web.WebFormat.format(comp.entities.Money)> in (Order.java:8)
```

- acyclic판은 `순환 없음`이었다.
- 관찰 — SCC는 하나(실험 A)인데 ArchUnit은 순환을 **4개** 보고했다. SCC는 "서로 닿는 정점 묶음", ArchUnit 보고는 그 안의 개별 순환 경로다. 4개 경로 모두 `entities → web` 간선(`Order.java:8`)을 지난다(출력 전체에서 확인). 끊을 간선은 하나다.

### 4. 순환 끊기

```text
 순환:  entities ──> web ──> usecases ──> entities
 (1) DIP: entities가 인터페이스 MoneyFormat을 소유, web이 구현     entities <── web  (방향 역전)
 (2) 새 컴포넌트: 둘이 함께 쓰는 것을 format 같은 새 컴포넌트로 뺀다  entities ──> format <── web
```

- Martin "Granularity" 「Breaking the Cycle」: 두 방법 — DIP로 의존을 뒤집기, 둘이 함께 의존할 새 패키지 만들기. 실험의 acyclic판이 (1)이다.
- 같은 글: 요구가 자라면 패키지 구조가 "jitters and grows" 하므로 순환을 계속 감시해야 한다.

## 쓰이는 자료구조·알고리즘

- **방향 그래프 + 강한 연결 요소(SCC)**: 컴포넌트 = 정점, 의존 = 간선. Tarjan SCC는 DFS 한 번(O(V+E))으로 SCC를 찾는다. 크기 2 이상 SCC = 한 덩어리로 릴리스해야 하는 순환 묶음. [algorithm/18-scc](../../algorithm/18-scc/2-summary.md).
- **위상 정렬**: 순환이 없을 때 빌드 순서. Tarjan이 SCC를 내는 순서가 역 위상 순서다(실험 A: entities → usecases → db → web).
- **응축 그래프(condensation)**: SCC를 정점 하나로 접은 그래프는 정의상 DAG다. 순환이 많은 레거시는 응축 그래프로 큰 덩어리부터 본다.
- **차수 세기**: Ca·Ce는 클래스 단위 들어오는·나가는 간선의 출발 클래스 수다(`jdeps -verbose:class`).

## 적용 — 풀어나가는 법

1. **현재 그래프를 뽑는다.** `jdeps -summary *.jar`(jar 간), `jdeps -verbose:class`(클래스 간 — 같은 패키지 간선까지 보려면 `-filter:none`, [54](../54-designing-for-deletion/2-summary.md)). Maven이면 `mvn dependency:tree`, Gradle이면 모듈 의존을 본다.
2. **순환을 막는다.** Maven은 모듈 사이 순환을 리액터 단계에서 거부한다(실험, Maven 3.9.16, 모듈 a·b가 서로 의존: `The projects in the reactor contain a cyclic reference: ... x:a:1 --> x:b:1 --> x:a:1`). Gradle의 동작과 문구는 이 노트에서 확인하지 않았다 [?]. 같은 모듈 안 패키지 순환은 도구가 막지 않으니 ArchUnit `slices().matching("..(*)..").should().beFreeOfCycles()`로 막는다(실험 B).
3. **순환을 끊는다.** 보고된 경로가 공통으로 지나는 줄(실험 B `Order.java:8`)을 찾아, DIP로 뒤집거나 공통 부분을 새 컴포넌트로 뺀다.
4. **지표로 질문한다.** 안정된 컴포넌트(I 낮음)가 불안정한 것에 의존하면 SDP 위반 후보. 안정된데 구체적이면(Dn 큼) "이걸 바꿀 일이 생기면?"을 묻는다.
5. **묶음을 다시 본다(CCP·CRP).** `git log`로 함께 바뀌는 파일이 여러 모듈에 흩어지면 CCP 위반, 한 모듈의 일부만 쓰는 소비자가 많으면 CRP 위반 후보.
   ```bash
   # 커밋마다 몇 개 모듈(최상위 디렉터리, p[1])을 건드렸나의 분포
   git log --since=3.months --pretty=format:'@%h' --name-only \
     | awk '/^@/{if(c)print n; split("",seen); n=0; c=1; next} NF{split($0,p,"/"); if(!(p[1] in seen)){seen[p[1]]=1;n++}} END{print n}' \
     | sort -n | uniq -c
   ```
   (출력 "건수 모듈수". 38의 실험 저장소 `e38/g/v1`에 `p[3]`(패키지 단계)로 돌리면 `2 3` — 커밋 2개가 각각 패키지 3개를 건드렸다. 모듈 수가 큰 커밋이 많으면 CCP를 의심한다.)

## 장애 시나리오와 대처

### 1. 컴포넌트 순환 의존 → 독립 배포 불가 (⚠ 커리큘럼)

- 현상: `entities` 버그 하나 고쳐 릴리스하려는데 `web`·`usecases`·`db`까지 함께 빌드·시험·배포해야 한다.
- 보이는 형태: 모듈을 따로 빌드하면 `package comp.web does not exist`(실험 A cyclic). ArchUnit `Cycle detected`(실험 B). 빌드 그래프 도구의 순환 경고.
- 원인: 안쪽 컴포넌트가 바깥 컴포넌트의 클래스를 직접 쓴다(실험: import는 `Order.java:2`, 사용은 `Order.java:8` — ArchUnit은 바이트코드의 사용 지점을 짚는다). import만 지우면 컴파일이 깨지므로 끊을 것은 8행의 사용(의존)이다.
- 대처: DIP(인터페이스를 안쪽이 소유) 또는 공통부 추출로 끊고, `beFreeOfCycles` 규칙을 빌드에 넣는다. 기존 순환이 많으면 위반을 동결하고 신규만 막는다([41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)).

### 2. 안정된 공통 모듈이 불안정한 모듈에 의존한다 (SDP 위반)

- 현상: 거의 안 바뀌던 `common`이 자꾸 바뀌고, 바뀔 때마다 그것을 쓰는 모듈이 줄줄이 재빌드된다.
- 보이는 형태: `common`의 I가 0 근처에서 올라간다(실험 A `entities` 0 → 0.17). `common` 변경 PR의 영향 모듈 수가 크다.
- 원인: 공통 모듈이 기능 모듈(웹·DB)의 타입을 참조하기 시작했다.
- 대처: 참조 방향을 뒤집거나 그 기능을 공통 모듈 밖으로 뺀다. CI에서 모듈별 I를 기록해 추세를 본다.

### 3. 쓰지 않는 것 때문에 끌려 릴리스된다 (CRP 위반)

- 현상: 날짜 유틸 하나 쓰려고 넣은 `common` 모듈이 바뀔 때마다 우리 서비스도 재배포·재시험한다.
- 보이는 형태: 의존 업그레이드 PR이 우리와 무관한 변경 때문에 잦다.
- 원인: 함께 쓰이지 않는 클래스를 한 컴포넌트에 묶었다.
- 대처: 함께 쓰이는 것끼리 컴포넌트를 쪼갠다(`common-time`·`common-web`). 단, 너무 잘게 쪼개면 하나의 변경이 여러 컴포넌트에 걸친다(CCP와의 긴장).

### 4. 한 기능 변경이 여러 모듈 PR로 쪼개진다 (CCP 위반)

- 현상: "환불 정책 변경" 하나에 모듈 4개 릴리스가 순서대로 필요하다.
- 보이는 형태: 같은 티켓 번호의 커밋이 여러 모듈에 걸침(적용 5의 `git log` 집계).
- 원인: 같은 이유로 바뀌는 클래스들이 기술 계층별로 흩어졌다.
- 대처: 변경 이유(업무 능력)로 다시 묶는다. 37 아키텍처 스타일의 도메인 분할, [04-decompose-by-change](../04-decompose-by-change/2-summary.md)와 같은 판단이다.

## 핵심 문장

- 응집 3원칙(REP·CCP·CRP)은 무엇을 한 배포 단위로 묶을지, 결합 3원칙(ADP·SDP·SAP)은 배포 단위 사이 의존을 어떻게 둘지를 정한다.
- 의존 그래프에 순환이 생기면 그 SCC 전체가 한 덩어리가 된다. 실험에서 import 한 줄로 네 컴포넌트가 SCC 하나가 됐고, 의존 순서대로 하나씩 빌드할 수 없게 됐다.
- 순환은 실행을 깨지 않는다. 독립 빌드·릴리스를 깬다. 실험의 두 판은 같은 결과를 출력했다.
- I = Ce/(Ca+Ce), A = 추상 클래스 비율, Dn = |A+I−1|. 지표는 판정이 아니라 "이것을 바꾸면 무엇이 끌려오나"를 묻는 출발점이다.
- 순환은 DIP(인터페이스를 안정된 쪽이 소유)나 공통 컴포넌트 추출로 끊고, 빌드 테스트로 다시 생기지 않게 막는다.

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 의존 방향 규칙(DIP의 아키텍처 판)
  - [22-solid](../22-solid/2-summary.md), 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)
- 연결
  - [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) — Tarjan·Kosaraju SCC
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 플러그인 → 안정된 계약 방향
  - [40-codebase-structure](../40-codebase-structure/2-summary.md), [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)
- 글·책
  - Robert C. Martin, "Granularity", C++ Report 「Engineering Notebook」 다섯 번째 칼럼 — REP·CRP·CCP·ADP 원문 정의, morning after syndrome, Breaking the Cycle 두 방법 <https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/granularity.pdf> (C++ Report 1996년 11/12월호 — 다음 칼럼 "Stability"의 이전 칼럼 목록 기준)
  - Robert C. Martin, "Stability", 같은 칼럼 여섯 번째 — SDP·SAP 원문 정의 <https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/stability.pdf>
  - Robert C. Martin, "OO Design Quality Metrics: An Analysis of Dependencies", 1994-10-28 — Ca·Ce·I·A·D·Dn 정의 <https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/oodmetrc.pdf>
  - Robert C. Martin, 『Clean Architecture』(Pearson, 2017) 4부 Component Principles: 12장 Components, 13장 Component Cohesion, 14장 Component Coupling — InformIT 목차로 장 제목만 확인 <https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166>
  - ArchUnit User Guide — Slices, `beFreeOfCycles` <https://www.archunit.org/userguide/html/000_Index.html>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02, 코드 scratchpad `sd/35/e39/`)
  - A `acyclic/`·`cyclic/` 네 컴포넌트, `run.sh`(컴포넌트별 순차 빌드 + 지표), `Metrics.java`(jdeps 파싱·Ca·Ce·I·A·Dn·Tarjan SCC). 출력 `run-output.txt`
  - B `Cycles.java`(ArchUnit 1.4.1 `slices().beFreeOfCycles()`). 출력 `cycles-output.txt`
  - C(사실 점검 때 추가) Maven 3.9.16(`maven:3.9-eclipse-temurin-21`, 네트워크 없음, `mvn -o validate`) — 서로 의존하는 두 모듈의 리액터 순환 오류. 코드 scratchpad `sd/fc-35/mvncyc/`
