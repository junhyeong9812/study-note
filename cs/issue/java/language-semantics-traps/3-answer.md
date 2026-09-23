# cs/issue/java/language-semantics-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **Error ≠ Exception.** `Throwable` 아래에 `Exception`(복구 가능한 예외)과 `Error`(JVM 수준 심각 오류)가 형제로 있다. `OutOfMemoryError`는 `Error`라 `catch (Exception)`을 그대로 빠져나가고, 스레드는 잡히지 않은 채 종료된다 — `markDone`도 `setFailed`도 실행되지 않아 상태가 `RUNNING`에 고착되고, 스레드 덤프에서는 그 스레드가 사라져 있다.\
   부수로 OOM이 같은 JVM의 다른 클라이언트 I/O 스레드까지 죽여 "connection closed" 류 에러가 연쇄됐는데, 이 문구는 원인이 아니라 결과였다. 대조군으로 `SQLException`(Exception)으로 실패한 잡은 `setFailed`가 정상 동작해 FAILED로 보였다.\
   권고는 러너를 `catch (Throwable)`로 감싸 실패 상태로 전이 + heartbeat/오래된 잡 스윕이다. 프로세스 kill은 어떤 catch로도 막을 수 없으므로 **외부 스윕**이 필요하다.
   > **Error** — `Throwable`의 하위로, 애플리케이션이 보통 잡지 않는 JVM 수준 오류(OOM·StackOverflow 등).

2. **static 초기화 순서.** `ExceptionInInitializerError`(원인 `NullPointerException`)가 난다. 클래스 초기화 시 static 필드는 **소스에 선언된 순서대로** 초기화된다. `INSTANCE = new X()`가 먼저 실행되고, 그 생성자의 `super(RULES)` 시점에 `RULES`는 아직 초기화 전이라 null이다. 교정은 `RULES`를 `INSTANCE` 위로 옮기고 "규칙 먼저, 인스턴스 나중"을 관례로 고정하는 것.
   > **클래스 초기화** — 클래스를 처음 능동적으로 사용할 때 static 초기화식·블록을 선언 순서대로 한 번 실행하는 단계.

3. **인자 평가 순서.** 메서드 인자는 **호출 전에** 평가된다. `parseSiteId`가 `NumberFormatException`을 던지면 `onLoginFailed`는 호출조차 되지 않으므로 실패 카운트 증가·계정 잠금·감사 로그가 전부 실행되지 않고 응답은 500이다.\
   공격자가 비숫자 헤더를 붙여 무차별 대입하면 잠금이 영영 걸리지 않는다 — 신뢰할 수 없는 입력의 가드 없는 파싱이 **보안 필수 경로를 끊는다**. 권고는 파싱을 안전하게(실패 시 null) 하고, 실패 카운트를 헤더·로그와 독립된 필수 경로로 분리하는 것.

4. **불변성과 소거.** 제네릭은 **불변**이다 — `List<Sub>`가 `List<Super>`라면 `List<Super>`로 다른 하위 타입을 넣어 원래 리스트를 오염시킬 수 있으므로 금지된다. 스트림 `map`의 결과 타입을 `.<Super>map(...)` 타입 위트니스로 지정하거나, 상위 타입 필드를 가진 wrapper로 자동 확장한다.\
   제네릭 타입 인자는 **런타임에 소거**된다 — `Paged.class`는 `Paged<?>`일 뿐 원소 타입을 담을 수 없다. **타입 토큰**은 `new TypeRef<Paged<Item>>(){}`처럼 익명 서브클래스를 만들어, 그 클래스의 "상위 타입 선언"(클래스 메타데이터에 남음)에서 `Paged<Item>`을 리플렉션으로 읽어낸다.
   > **타입 소거(type erasure)** — 컴파일 후 제네릭 타입 인자를 지우고 원시 타입으로 바꾸는 Java의 구현 방식.

5. **타입 체커가 못 보는 자리.** `equals`의 파라미터는 `Object`라 무엇이든 받으므로 컴파일된다. `Optional`은 다른 `Optional`과만 같다고 판정하므로 `Optional<Node>.equals(node)`는 **항상 false**다. 교정은 id 기반 비교(`this.parent.getId().equals(opt.get().getId())`) — equals 미오버라이드 엔티티는 참조 비교라 ORM 프록시와도 틀린다.\
   위치 인자 언어에서 **타입이 같은** 인자들은 이름이 아니라 순서로만 구분된다. 순서가 바뀌어도 타입 검사는 통과한다 — 로직을 옮길 때는 옮긴 전/후를 필드 단위로 대조해야 하고, 컴파일·테스트 green은 필요조건일 뿐이다.

6. **오버로드 해석.** 가변 인자 0개 호출 `f(String.class)`는 두 varargs 오버로드 모두에 적용 가능하고, 어느 쪽도 다른 쪽보다 **더 구체적이지 않아** 컴파일러가 선택하지 못한다 → 배열 타입을 명시해 `f(String.class, new Type[0])`.\
   Mockito `any()`는 타입 정보가 없는 제네릭 반환이라, 같은 이름·같은 개수의 오버로드가 생기면 둘 다 적용 가능해 모호해진다 → `anyList()`·`any(Long.class)` 같은 **타입 매처**로 결정한다.\
   같은 계열로, catch 안의 "콜백 + throw"를 void 헬퍼로 추출하면 컴파일러는 그 헬퍼가 항상 던진다는 걸 모르므로 뒤따르는 코드의 확정 대입 분석이 깨진다 → 예외를 **반환**하는 헬퍼 + 호출부 `throw helper(...)`.

7. **사람의 의미 ≠ 언어 정의.**
   - 블록 주석은 중첩되지 않고 **첫 `*/`에서 끝난다** — 주석 본문의 글롭 표기 `*/`가 주석을 조기 종료시킨다.
   - `@Target(FIELD)` 어노테이션을 record 컴포넌트에 달면 컴파일러가 **private backing 필드로 전파**한다 → `getDeclaredField(name).getAnnotation(...)`으로 읽는다(record 컴포넌트에서 읽으려면 `@Target`에 `RECORD_COMPONENT` 포함).
   - `\W`는 `[^A-Za-z0-9_]` — 밑줄은 "특수문자"에서 빠지고 공백·한글은 들어간다. 설명 문구와 실제 허용 집합이 두 방향으로 어긋난다.\
   공통점: 모두 **언어/라이브러리가 정의한 정확한 규칙**이 직관적 읽기와 다르고, 컴파일(또는 정규식 컴파일)은 이를 알려주지 않는다. 실제 매칭 집합·실제 메타데이터 위치를 **역산해 확인**해야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 예외 계층: `catch (Exception)`이 `Error`를 못 잡음
① 문제 코드
```java
void run(Job job) {
    try {
        migrate(job);                       // 대량 적재 중 OutOfMemoryError
        job.markDone();
    } catch (Exception e) {                 // Error는 여기로 안 옴
        job.setFailed(e);
    }                                       // → 스레드 사망, 상태 RUNNING 고착
}
```
② 고친 코드
```java
    } catch (Throwable t) {                 // (권고) Error까지 잡아 상태 전이
        job.setFailed(t);
    }
// + heartbeat 갱신, 오래된 RUNNING 잡을 FAILED로 돌리는 스윕 (프로세스 kill 대비)
// + OOM 시 자동 힙덤프
```
무엇이 깨졌나: 실패 상태 전이가 잡히지 않는 예외 종류에 대해 실행되지 않았다.

### 변형 B — 평가 순서: static 초기화 · 인자 평가
① 문제 코드
```java
public final class Rules extends Base {
    public static final Rules INSTANCE = new Rules();   // ① 먼저 실행
    private Rules() { super(RULES); }                    //    RULES == null
    private static final List<Rule> RULES = build();     // ② 늦게 초기화
}
```
```java
Long parseSiteId(String header) { return Long.valueOf(header); }   // 비숫자면 throw
// ...
service.onLoginFailed(parseSiteId(req.getHeader("X-Tenant")), user); // 인자에서 throw → 본문 미실행
```
② 고친 코드
```java
    private static final List<Rule> RULES = build();     // 의존되는 필드 먼저
    public static final Rules INSTANCE = new Rules();
```
```java
Long parseSiteId(String header) {                       // (권고) 안전 파싱
    try { return Long.valueOf(header); } catch (NumberFormatException e) { return null; }
}
service.onLoginFailed(user);                            // 실패 카운트는 헤더와 독립된 필수 경로
```
무엇이 깨졌나: 코드가 "이미 준비됐다/반드시 실행된다"고 가정한 지점이 언어의 평가 순서상 그렇지 않았다.

### 변형 C — 타입 시스템: 불변성 · 소거 · `equals(Object)`
① 문제 코드
```java
List<Base> list = stream.map(this::toSub).toList();            // List<Sub> → 대입 불가
Paged<Item> page = client.get().retrieve().body(Paged.class);  // 원소 타입 소실
boolean same = parentOpt.equals(this.parent);                  // Optional vs Node → 항상 false
```
② 고친 코드
```java
List<Base> list = stream.<Base>map(this::toSub).toList();      // 타입 위트니스
static final TypeRef<Paged<Item>> PAGED = new TypeRef<>() {};  // 익명 서브클래스 = 타입 토큰
Paged<Item> page = client.get().retrieve().body(PAGED);
boolean same = this.parent.getId().equals(parentOpt.get().getId());   // id 비교
```
무엇이 깨졌나: 타입 인자·비교 대상의 타입이 코드의 가정과 달랐고, 두 경우는 컴파일러가 알려주지 않았다.\
같은 구조: 서비스 간 포트를 `Object call(Object)`로 약타입 선언 → 어댑터의 경로 3건이 실제 매핑과 다른 것을 아무 정적 검증도 못 잡음 → 강타입 record 시그니처로 바꾸며 상대 매핑과 1:1 대조.

### 변형 D — 오버로드 해석 · 위치 인자 · 도달성
① 문제 코드
```java
f(String.class);                                   // f(Class<?>, Class<?>...) vs f(Class<?>, Type...) → 모호
verify(repo).find(any(), any());                   // find 오버로드 추가 후 → 모호
Command asCommand() { return new Command(b, a); }  // (a, b) 같은 타입 — 순서 뒤바뀜, 컴파일 통과
catch (AuthFailure e) { reject(req, id); }       // void 헬퍼 — 컴파일러는 항상 던진다는 걸 모름
```
② 고친 코드
```java
f(String.class, new Type[0]);                      // 배열 타입 명시
verify(repo).find(anyList(), any(Long.class));     // 타입 매처
// 로직 이동은 전/후를 필드 단위로 대조 (green은 필요조건)
catch (AuthFailure e) { throw rejected(req, id); }   // 예외를 반환하는 헬퍼
```
무엇이 깨졌나: 호출 해석이 타입 정보만으로 결정되는데, 넘긴 정보가 해석을 결정하기에 부족하거나(모호) 순서를 검사할 수 없었다.

### 변형 E — 렉싱·메타데이터·문자 클래스
① 문제 코드
```java
/** created_*/modified_* 컬럼을 채운다 */           // 첫 */ 에서 주석 종료 → 컴파일 에러
record Doc(@Field("name") String name) {}           // @Target(FIELD)
rc.getAnnotation(Field.class);                      // RecordComponent → null
@Pattern(regexp = "(?=.*\\W).{8,20}")               // 설명: "특수문자 1자 이상"
```
② 고친 코드
```java
/** (예) created_* 와 modified_* 컬럼을 채운다 */  // 본문에 */ 연속 표기를 두지 않는다
type.getDeclaredField(rc.getName()).getAnnotation(Field.class);   // backing 필드에서 읽음
// 클래스별 메타는 ConcurrentHashMap.computeIfAbsent로 1회 캐시
// 설명을 실제 집합으로 정정: "영문·숫자·밑줄 이외의 문자 1자 이상"
```
무엇이 깨졌나: 사람이 읽은 의미(주석·"필드에 달았다"·"특수문자")와 언어가 정의한 의미가 달랐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
