# software-design/51-legacy-change-techniques — 레거시 변경 기법: seam·sprout/wrap·의존 끊기·parallel change — 정리 (힌트)

## 해결하는 문제

테스트가 없는 코드를 바꿔야 한다. 여기에는 닭과 달걀 문제가 있다.

```text
 안전하게 바꾸려면 ──> 테스트가 필요하다
        ^                      │
        │                      v
 코드를 바꿔야 한다 <── 테스트를 붙이려면 의존(DB·시계·전역)을 끊어야 한다
```

- *레거시 코드(Feathers의 정의)*: "테스트가 없는 코드". 『Working Effectively with Legacy Code』(2004, 이하 WELC) 머리말의 정의다("legacy code is simply code without tests"). 오래됨이나 지저분함이 기준이 아니다.
- *의존 끊기(dependency breaking)*: 테스트 하네스(테스트를 돌리는 틀)에 클래스·메서드를 올릴 수 있도록, 붙잡고 있는 의존을 바꿔 끼울 수 있게 만드는 작은 변경.

이 노트는 그 순환을 **작고 안전한 변경**으로 끊는 법이다.
- 새 코드는 테스트할 수 있는 자리에 따로 키운다(sprout·wrap).
- 바꿔 끼울 자리(seam)를 찾거나 만든다.
- 인터페이스를 바꿀 때는 한 번에 다 바꾸지 않고 넓혔다 줄인다(parallel change).

쉬운 예: 전선이 벽 속에 묻힌 오래된 집에 콘센트를 하나 더 단다. 벽을 다 뜯는 대신 기존 콘센트에서 멀티탭을 뽑아 새 기기를 거기에 꽂는다.\
똑같은 구조다.\
실무 예: 3천 줄짜리 `TransactionGate.postEntries()`에 "중복 항목은 한 번만 저장" 규칙을 넣는다. 이 메서드는 실행 중에 메서드 안에서 운영 DB에 직접 연결한다(`Database.connect()`). 50(Strangler Fig)이 시스템을 통째로 옮기는 법이라면, 이 노트는 그 안의 코드 한 줄을 바꾸는 법이다.

## 동작·원리

### 1. 레거시 코드 변경 알고리즘

```text
 ① 변경점 찾기 ─> ② 테스트 지점 찾기 ─> ③ 의존 끊기 ─> ④ 테스트 작성 ─> ⑤ 변경·리팩터링
 (어디를 바꾸나)   (어디서 효과를 볼 수 있나)  (하네스에 올리기)  (현재 동작 고정)   (새 코드는 맨 마지막)
```

- 다섯 단계 이름은 WELC 2장 「Working with Feedback」 안의 절 「The Legacy Code Change Algorithm」(목차상 18쪽)의 것이다. 본문은 열람하지 못했고, 단계 이름은 2차 출처(Agile in a Flash, 2009)와 대조했다.
- *변경점(change point)*: 동작을 바꿔야 하는 코드 위치.
- *테스트 지점(test point)*: 변경의 효과를 관찰할 수 있는 위치. 변경점과 같지 않을 수 있다. 효과가 어디로 퍼지나를 따라가 찾는다(WELC 11장 「Reasoning About Effects」·「Effect Propagation」, 목차로 확인).
- 순서의 요점: 새 코드를 쓰는 일은 맨 마지막이다.

### 2. seam과 enabling point

WELC 4장 「The Seam Model」(출판사 공개 샘플로 본문 확인)의 정의다.

- *seam*: "편집하지 않고도 그 자리의 동작을 바꿀 수 있는 곳(a place where you can alter behavior in your program without editing in that place)".
- *enabling point*: "어느 동작을 쓸지 결정하는 곳". 4장 원문: "Every seam has an enabling point".

```text
 seam 종류(4장)        바꾸는 방법                       enabling point
 preprocessing seam    매크로가 호출을 다른 코드로 치환       전처리 정의(C/C++의 #define)
 link seam             링크·클래스패스에서 다른 구현을 고름    빌드·배포 스크립트, 클래스패스
 object seam           호출 대상 객체를 바꿈(다형성)          객체를 만드는 곳·넘겨주는 곳
```

- 4장의 Java 예: `cell.Recalculate()`는 `cell`이 어느 객체냐에 따라 다른 메서드가 불린다. 둘레 코드를 안 고치고 바꿀 수 있으면 seam이다.
- 반대로 메서드 안에서 `new FormulaCell(...)`로 만들고 바로 부르면 seam이 아니다. 셀의 클래스가 생성 시점에 정해져 메서드를 고치지 않고는 못 바꾼다 — enabling point가 없다(4장 "There is no enabling point"). 같은 메서드가 `Cell`을 인자로 받으면 seam이 되고, enabling point는 그 인자 목록이다.
- 4장의 주의: link seam을 쓰면 테스트와 운영 환경의 차이가 눈에 띄게 하라.
- Java에서 가장 흔한 것은 object seam이다. 생성을 생성자 인자·팩토리 메서드로 빼면 enabling point가 생긴다.

### 3. 새 코드를 키우는 네 방법 — sprout와 wrap

WELC 6장 「I Don't Have Much Time and I Have to Change It」(목차: Sprout Method 59쪽, Sprout Class 63쪽, Wrap Method 67쪽, Wrap Class 71쪽). 본문은 열람하지 못해 정의는 2차 출처(Mark Needham book club, 2009)와 대조한 요약이다.

```text
 Sprout Method                              Wrap Method
 legacy() {                                 pay() {            ← 원래 이름의 새 메서드
   ...기존 300줄...                            logPayment();   ← 새 동작(앞 또는 뒤)
   out = uniqueEntries(out);  ← 한 줄 추가      dispatchPayment(); ← 원래 본문(이름만 바꿈)
   ...                                       }
 }
 uniqueEntries(in) { 새 로직 }  ← 테스트로 키움

 Sprout Class                               Wrap Class (데코레이터)
 legacy() { new EntryDeduper().dedupe(x); }  class LoggingPayer implements Payer {
 class EntryDeduper { 새 로직 }              ← 원 클래스를  Payer inner; pay(){ log(); inner.pay(); } }
 (원 클래스를 하네스에 못 올릴 때)              감싸 새 동작을 더한다
```

- *sprout method*: 새 로직을 새 메서드로 쓰고 테스트한 뒤, 기존 메서드에서 그 메서드를 부르는 한 줄만 넣는다. 기존 메서드는 테스트되지 않은 채 남는다(한계).
- *sprout class*: 원 클래스를 하네스에 올릴 수 없을 때 새 로직을 새 클래스로 만든다.
- *wrap method*: 기존 메서드 이름을 바꾸고, 원래 이름의 새 메서드가 [새 동작 + 원 메서드]를 부른다. 새 동작이 기존 동작 앞뒤에 매번 붙어야 할 때 쓴다.
- *wrap class*: 원 클래스를 생성자로 받아 대부분 위임하고 새 동작을 더한다(GoF Decorator와 같은 모양).

### 4. 의존 끊기 기법 — 인터페이스 추출·매개변수화

WELC 25장은 기법 24개를 카탈로그로 둔다(목차로 확인 — Adapt Parameter, Break Out Method Object, Extract and Override Call/Factory Method/Getter, Extract Implementer, Extract Interface, Parameterize Constructor, Parameterize Method, Subclass and Override Method 등).

```text
 Before: 숨은 의존                          After: Parameterize Constructor + Extract Interface
 class TransactionGate {                    interface EntryStore { void save(List<String> rows); }
   void postEntries(...) {                  class TransactionGate {
     Database db = Database.connect(); ←✗     private final EntryStore store;
     ...                                      TransactionGate(EntryStore store) { this.store = store; } ← enabling point
   }                                          void postEntries(...) { ... store.save(out); }
 }                                          }
```

- *Extract Interface*: 의존 클래스에서 쓰는 메서드만 인터페이스로 뽑아, 테스트에서 가짜 구현을 넣는다.
- *Parameterize Constructor / Method*: 안에서 `new` 하던 것을 인자로 받는다. 기존 호출자를 위해 옛 생성자를 남겨 새 생성자에 위임하면 호출처를 안 고쳐도 된다.
- *Extract and Override Factory Method*: 생성 코드를 보호된 메서드로 뽑고, 테스트 서브클래스에서 오버라이드한다. 아래 실험의 `openDatabase()`가 이것이다.
- *sensing과 separation*(WELC 3장 제목, 본문 미열람 — 아래 풀이는 이 노트의 요약 [?]): 의존을 끊는 두 이유. 코드가 계산한 값을 볼 수 없어서(감지), 또는 코드를 하네스에서 아예 돌릴 수 없어서(분리). 4장 본문도 "seam에서 동작을 바꾸면 테스트에서 의존을 골라 뺄 수 있고, 그 자리에서 조건을 감지(sense)할 수 있다"고 적는다.

### 실험 B: 숨은 의존·sprout·wrap·object seam (Java)

```java
static class TransactionGate {
    void postEntries(List<String> entries) {
        Database db = Database.connect();               // 숨은 의존(테스트 환경에서는 예외)
        List<String> out = new ArrayList<>();
        for (String e : entries) out.add(e.trim().toUpperCase());
        out = uniqueEntries(out);                        // ← sprout method 호출 한 줄
        db.save(out);
    }
    static List<String> uniqueEntries(List<String> in) { return new ArrayList<>(new LinkedHashSet<>(in)); }
    void pay(long amount) { logPayment(amount); dispatchPayment(amount); }   // wrap method
}
static class TransactionGate2 {
    Database openDatabase() { return Database.connect(); }   // seam (Extract and Override Factory Method)
    void postEntries(List<String> entries) { openDatabase().save(TransactionGate.uniqueEntries(entries)); }
}
// 테스트: new TransactionGate2() { @Override Database openDatabase() { return 가짜(save 내용을 기록); } }
```

(실험, JDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-02)

```text
== 레거시 메서드를 그대로 테스트
  FAIL postEntries 중복 제거 — IllegalStateException: 운영 DB에 연결할 수 없음(테스트 환경)
== sprout method만 테스트
  PASS uniqueEntries 중복 제거·순서 유지
== wrap method
  PASS pay가 로그를 남긴다
== 객체 seam(서브클래스로 DB 교체)
  PASS postEntries 저장 내용 감지(sensing)
```

- 관찰 1 — 레거시 메서드는 하네스에서 실행조차 안 된다(분리 문제).
- 관찰 2 — sprout한 `uniqueEntries`는 순수 함수라 바로 테스트된다. 다만 `postEntries` 본체는 여전히 테스트 밖이다.
- 관찰 3 — 생성을 오버라이드 가능한 메서드로 빼자(seam), 테스트 서브클래스가 가짜 DB를 넣고 저장 내용 `[X, Y]`를 감지했다. enabling point는 "어떤 객체를 만드느냐(테스트용 익명 서브클래스)"다.

### 5. 인터페이스를 바꿀 때 — parallel change (expand → migrate → contract)

Danilo Sato, "ParallelChange"(martinfowler.com bliki, 2014-05-13). "expand and contract"라고도 한다.

```text
 expand                          migrate                         contract
 charge(long, long) ─┐ 위임        호출처를 묶음 단위로 새 쪽으로        charge(long, long) 삭제
 charge(long, Money) <┘           (커밋마다 빌드 통과)               charge(long, Money)만 남음
```

- *expand*: 옛 버전과 새 버전을 둘 다 지원하게 넓힌다. 옛 메서드를 새 메서드에 위임하면 구현이 하나로 유지된다(같은 글의 변형).
- *migrate*: 호출처를 조금씩 새 버전으로 옮긴다. 외부 호출자면 이 단계가 길다.
- *contract*: 옛 버전을 지운다.
- 같은 글의 단점: migrate 동안 공급자가 두 버전을 지원하고, 어느 쪽이 새것인지 헷갈릴 수 있다. contract를 하지 않으면 시작보다 나쁜 상태가 된다. deprecation 표시·문서로 알린다.

### 실험 C: 빅뱅 vs parallel change — 커밋 크기와 커밋마다 빌드

호출처 40곳이 `Billing.charge(long customerId, long amountWon)`를 부른다. 시그니처를 `charge(long, Money)`로 바꾼다. 스크립트가 git 커밋을 만들고 각 지점에서 `javac`로 전체를 컴파일한다.

```bash
OLD='public static void charge(long customerId, long amountWon) { total += amountWon; }'
NEW='public static void charge(long customerId, Money m) { total += m.amount(); }'
# B1 expand: 옛 메서드를 남기고 새 메서드에 위임
sed -i "s/$OLD/public static void charge(long customerId, long amountWon) { charge(customerId, new Money(amountWon, \"KRW\")); }\n    $NEW/" src/billing/Billing.java
# B2 migrate: 10곳씩 4번
sed -i -E 's/Billing.charge\(([0-9]+L), 1000L\)/Billing.charge(\1, new Money(1000L, "KRW"))/' $files
# B3 contract: 옛 메서드 삭제
sed -i '/charge(long customerId, long amountWon)/d' src/billing/Billing.java
```

(실험, git 2.43.0 + JDK 21.0.12 temurin `javac`, Docker `--cpus=2`, 2026-10-02, `scratchpad/sd/50/e51/run.sh`)

```text
== A. 빅뱅
  [A1: 시그니처 변경만]
 1 file changed, 1 insertion(+), 1 deletion(-)
  컴파일 실패: 오류 40건 (파일 40개)
  [A2: 호출처 40곳 동시 수정]
 40 files changed, 40 insertions(+), 40 deletions(-)
  컴파일 OK
  A1+A2 합계:  41 files changed, 41 insertions(+), 41 deletions(-)
== B. parallel change
  [B1 expand: 새 메서드 추가, 옛 메서드는 위임]
 1 file changed, 2 insertions(+), 1 deletion(-)
  컴파일 OK
  … (이 노트에서 줄임: B2-0~B2-3 각 "10 files changed", B2-1·B2-3 뒤 "컴파일 OK")
  [B3 contract: 옛 메서드 삭제]
 1 file changed, 1 deletion(-)
  컴파일 OK
  B 커밋별 변경 파일 수: 1 10 10 10 10 1 
== C. contract를 너무 일찍 하면 (migrate 2묶음만 끝난 상태에서 옛 메서드 삭제)
  컴파일 실패: 오류 20건 (파일 20개)
```

- 관찰 1 — 빅뱅은 시그니처 한 줄이 컴파일 오류 40건을 만들고, 41개 파일을 한 덩어리로 고쳐야 빌드가 돌아온다.
- 관찰 2 — parallel change는 같은 총량을 1 → 10 → 10 → 10 → 10 → 1 파일 커밋으로 나눴다. 점검한 지점마다 빌드가 통과했다(B2-0·B2-2 직후는 컴파일하지 않았다).
- 관찰 3 — contract를 이르게 하면 남은 호출처 수만큼(20건) 오류가 난다. 컴파일러가 "남은 호출처 목록"이 된다(WELC 23장 「How Do I Know That I'm Not Breaking Anything?」 안의 절 「Lean on the Compiler」, 목차로 확인). Sato의 글은 migrate 단계가 "컴파일러에 기대어 사용처를 전부 찾는 것"의 대안이라고 적는다.

### 실험 D: 동시 작업 브랜치와의 병합

시그니처를 바꾸는 동안 다른 브랜치가 옛 시그니처로 호출처 `Caller41`을 새로 추가했다.

(실험, 같은 환경, `scratchpad/sd/50/e51/merge.sh`)

```text
== D-bigbang: feature 병합
  git merge: 충돌 없음
  컴파일 실패: 오류 1건 (파일 1개)
== D-expand: feature 병합
  git merge: 충돌 없음
  컴파일 OK
```

```text
src/callers/Caller41.java:4: error: incompatible types: long cannot be converted to Money
    public static void run() { Billing.charge(41L, 1000L); }
```

- 관찰 — 빅뱅 쪽은 텍스트 충돌 없이 병합됐는데 빌드가 깨졌다. git은 줄 단위로만 충돌을 본다. "새 파일이 옛 시그니처를 부른다"는 의미 충돌은 못 본다.
- expand 상태에서는 옛 메서드가 살아 있어 같은 병합이 빌드됐다. 늦게 들어온 호출처도 migrate 목록에 더하면 된다.

## 쓰이는 자료구조·알고리즘

- **호출 그래프(영향 범위)** — 변경점에서 호출자 쪽으로 거꾸로 따라가면 영향받는 코드, 앞으로 따라가면 효과가 보이는 테스트 지점이 나온다. WELC 11장의 effect sketch(효과 스케치)가 손으로 그리는 이 그래프다(목차로 확인). 도달 가능 집합 계산은 그래프 BFS다.
- **pinch point** — 많은 효과가 모이는 좁은 지점. 거기 테스트를 걸면 적은 테스트로 넓게 덮는다(WELC 12장 「Interception Points」·「Judging Design with Pinch Points」, 목차로 확인).
- **동적 디스패치(가상 메서드 테이블)** — object seam이 동작하는 이유. 호출 지점은 그대로이고 객체의 클래스가 실제 메서드를 정한다.
- **데코레이터** — wrap class의 모양. 같은 인터페이스를 구현하고 안쪽 객체에 위임한다.
- **오버로딩 + 위임** — expand 단계에서 옛 시그니처가 새 시그니처를 부르게 해 구현을 하나로 둔다.

## 적용 — 풀어나가는 법

### 1. 순서 (변경 하나에 대해)

1. **변경점과 호출처를 센다.**

```bash
grep -rn "Billing.charge(" src/ | wc -l          # 직접 호출처 수
grep -rln "Billing.charge(" src/ | wc -l         # 파일 수
```

2. **테스트 지점을 고른다.** 효과가 관찰되는 가장 가까운 공개 메서드. 없으면 pinch point를 찾는다.
3. **하네스에 올려 본다.** 생성자를 테스트에서 불러 보고, 실패하면 무엇이 막는지(DB·전역·시계·파일) 적는다.
4. **가장 작은 의존 끊기를 고른다.** 대개 Parameterize Constructor(옛 생성자 유지) 또는 Extract and Override Factory Method. 이 단계는 테스트 없이 하는 변경이므로 기계적·작게 한다(WELC 머리말: Part III의 의존 끊기 리팩터링은 "테스트를 붙이기 위해, 테스트 없이 하도록 만든 것").
5. **현재 동작을 특성 테스트로 고정한다.** 기대값을 추측하지 않고 지금 나오는 값을 적는다([testing](../../testing/README.md) 17 characterization-tests-legacy — 미작성).
6. **새 코드는 sprout/wrap으로 키운다.** 거대한 메서드 한가운데에 직접 쓰지 않는다.
7. **시그니처를 바꿔야 하면 parallel change.** expand 커밋 → 묶음별 migrate 커밋 → contract 커밋.

### 2. migrate 단계의 표시 (Java)

```java
/** @deprecated {@link #charge(long, Money)}로 옮기는 중. 호출처 0이 되면 삭제. */
@Deprecated(since = "3.4", forRemoval = true)
public static void charge(long customerId, long amountWon) { charge(customerId, new Money(amountWon, "KRW")); }
public static void charge(long customerId, Money m) { total += m.amount(); }
```

- `forRemoval = true`면 `javac`가 호출처마다 `[removal]` 경고를 낸다(54의 실험에서 확인). 남은 호출처 목록과 CI 게이트로 쓸 수 있다.

### 3. 진단 도구

- 호출처 수의 변화: migrate 커밋마다 `grep -rn "charge(.*L, [0-9]*L)" src/ | wc -l`이 줄어야 한다.
- 커밋 크기: `git show --stat`으로 커밋당 파일 수를 확인한다(실험 C의 1 10 10 10 10 1).
- 클래스 간 의존: `jdeps -verbose:class -filter:none <classes>`로 누가 `Billing`을 참조하는지 본다(기본 `-filter:package`는 같은 패키지 간선을 숨긴다 — 54 실험).

## 장애 시나리오와 대처

### 1. 3천 줄 메서드 한가운데 새 규칙을 끼워 넣음 → 테스트 불가 영역이 커짐 (⚠ 커리큘럼)

- 현상: 새 규칙 버그를 고치려 해도 테스트를 못 쓴다. 메서드가 3,040줄이 됐다.
- 보이는 형태: 커버리지 리포트에서 그 메서드가 0%. 실험 B처럼 하네스에서 실행조차 안 된다(메서드 안의 DB 연결에서 예외).
- 원인: 새 로직이 숨은 의존(DB 연결)과 같은 메서드에 섞였다.
- 대처: sprout method/class로 새 로직을 떼어 그것만 테스트로 키운다. 원 메서드에는 호출 한 줄만 둔다. 다음 변경 때 seam을 만들어 원 메서드도 하네스에 올린다.

### 2. 시그니처를 한 번에 바꿔 호출처 80곳 동시 변경 → 머지 지옥 (⚠ 커리큘럼)

- 현상: PR 하나가 81개 파일을 건드리고, 리뷰 중에 다른 브랜치들과 계속 충돌한다. 병합하고 나니 빌드가 깨진다.
- 보이는 형태: `81 files changed`. 실험 D처럼 "git merge: 충돌 없음" 뒤에 `incompatible types` 컴파일 오류.
- 원인: 시그니처 변경이 원자적이라 중간 상태가 없다. 그동안 다른 브랜치가 옛 시그니처를 계속 쓴다.
- 대처: parallel change. expand를 먼저 병합하면 다른 브랜치는 옛 시그니처를 써도 빌드된다. migrate는 소유 팀·모듈별로 작게 병합한다. 마지막에 contract.

### 3. "일단 다 고치고 테스트" → 숨은 동작(반올림·정렬) 소실 (⚠ 커리큘럼)

- 현상: 리팩터링 후 금액이 1원씩 다르거나 목록 순서가 바뀐다. 아무도 그것이 "기능"이었는지 몰랐다.
- 보이는 형태: 새로 쓴 테스트는 통과한다(새 코드의 동작을 기대값으로 적었기 때문). 운영에서 고객 문의·정산 차이.
- 원인: 변경 전에 현재 동작을 고정하지 않았다. 테스트 기대값을 사양 문서나 추측으로 썼다.
- 대처: 알고리즘 순서를 지킨다 — 테스트 지점에서 현재 출력을 특성 테스트로 먼저 고정하고, 그다음 바꾼다. 시스템 단위라면 병행 실행으로 비교한다(50 실험 A).

### 4. contract를 너무 일찍 함

- 현상: 옛 메서드를 지운 커밋에서 빌드가 깨지거나, 외부 클라이언트가 런타임에 `NoSuchMethodError`를 낸다.
- 보이는 형태: 실험 C처럼 남은 호출처 수만큼 컴파일 오류(20건). 별도 배포 단위(다른 JAR·서비스)의 호출처는 컴파일 오류 없이 런타임에 터진다.
- 원인: migrate 완료를 확인하지 않았다. 컴파일러는 같은 빌드 안의 호출처만 본다.
- 대처: contract 전에 같은 빌드는 `grep`·`javac -Werror`로, 다른 배포 단위는 호출 로그로 0을 확인한다. JDK 21 `javac`에서 `forRemoval = true`의 `[removal]` 경고는 기본으로 켜져 있어 `-Werror`만으로 빌드가 실패한다. 일반 `@Deprecated`는 기본으로 "Note:" 한 줄만 내므로 `-Xlint:deprecation -Werror`를 함께 줘야 실패한다(사실 점검 재실행으로 확인).

### 5. link seam의 환경 차이를 잊음

- 현상: 테스트는 통과하는데 운영에서만 실패한다.
- 보이는 형태: 테스트 클래스패스에 가짜 구현 JAR가 먼저 잡혀 있었다.
- 원인: enabling point(클래스패스·빌드 스크립트)가 코드 밖에 있어 눈에 안 띈다.
- 대처: WELC 4장의 권고대로 테스트와 운영의 차이를 드러낸다. Java에서는 object seam(생성자 주입)을 우선 쓴다.

## 핵심 문장

- Feathers는 레거시 코드를 "테스트가 없는 코드"로 정의한다. 바꾸려면 테스트가 필요하고, 테스트를 붙이려면 의존을 끊어야 하는 순환이 문제다.
- 레거시 변경 알고리즘은 변경점 → 테스트 지점 → 의존 끊기 → 테스트 → 변경 순이고, 새 코드를 쓰는 일은 맨 마지막이다.
- seam은 그 자리를 고치지 않고 동작을 바꿀 수 있는 곳이고, 무엇을 쓸지 정하는 enabling point가 함께 있다. Java에서는 생성을 인자·팩토리 메서드로 빼서 만든다.
- sprout는 새 로직을 테스트 가능한 새 메서드·클래스로 키우고, wrap은 기존 동작 앞뒤에 새 동작을 감싼다.
- 시그니처 변경은 expand → migrate → contract로 나눈다. 실험에서 41파일 한 덩어리가 1·10·10·10·10·1 파일 커밋으로 나뉘었고, 점검한 지점마다 빌드가 통과했다.

## 관련 주제·근거

- 선행
  - [testing](../../testing/README.md) 17 characterization-tests-legacy — 미작성
  - [13-refactoring](../13-refactoring/2-summary.md)
- 후속·연결
  - [50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md) — 시스템 단위의 같은 생각(추상 뒤 공존 → 전환 → 삭제)
  - [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md) — contract 단계와 내부 deprecate
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 생성자 주입 = object seam
  - [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) — 스키마의 expand/contract
- 글·문서
  - Michael Feathers, 『Working Effectively with Legacy Code』, Prentice Hall, 2004 — 출판사 공개 샘플(목차·추천사·머리말·1장·4장·색인 — 2·3장 본문은 샘플에 없다)로 확인: 레거시 정의·Part III 소개(머리말), seam·enabling point 정의와 preprocessing·link·object seam(4장), 6장 sprout/wrap·11장 효과 추론·12장 pinch point·23장 Lean on the Compiler·25장 기법 24개(목차). 2장 알고리즘·6장·25장 본문은 미열람 <https://ptgmedia.pearsoncmg.com/images/9780131177055/samplepages/0131177052.pdf>
  - Agile in a Flash, "Legacy Code Change Algorithm", 2009 (알고리즘 다섯 단계 이름 대조) <http://agileinaflash.blogspot.com/2009/03/legacy-code-change-algorithm.html>
  - Mark Needham, "Book Club: Working Effectively With Legacy Code - Chapters 6 & 7", 2009 (sprout/wrap 요약 대조) <https://www.markhneedham.com/blog/2009/10/26/book-club-working-effectively-with-legacy-code-chapters-6-7-michael-feathers/>
  - Danilo Sato, "ParallelChange", 2014-05-13 <https://martinfowler.com/bliki/ParallelChange.html>
- 실험 목록
  - 실험 B — 숨은 의존·sprout·wrap·object seam. `scratchpad/sd/50/e51/Seams.java`, `docker run --rm --cpus=2 eclipse-temurin:21-jdk java Seams.java`(JDK 21.0.12).
  - 실험 C — 빅뱅 vs parallel change 커밋 크기·커밋별 컴파일, 이른 contract. `scratchpad/sd/50/e51/run.sh`(+ `gen.sh`·`compile.sh`). git 2.43.0(호스트), 컴파일은 JDK 21.0.12 컨테이너.
  - 실험 D — 동시 브랜치 병합의 의미 충돌. `scratchpad/sd/50/e51/merge.sh`.
