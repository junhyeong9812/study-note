# cs/issue/kotlin/language-semantics-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **블록 주석 중첩.** Java의 `/* */`는 중첩되지 않아 첫 `*/`에서 닫히지만, Kotlin은 **중첩을 지원**한다.\
그래서 주석 본문 속 `/admin/**`의 `/*`가 **안쪽 주석을 새로 연다** — 여는 표시가 하나 더 생겼는데 닫는 `*/`는 그대로라 짝이 모자라고, 주석이 파일 끝까지 안 닫혀 `Unclosed comment`가 난다.\
빌드가 실패하니 그 서비스(여기선 관리자 엔드포인트 전체)가 기동하지 않았고, 이를 호출하는 관리자 BFF(프론트 전용 중계 서버)는 전부 502를 받았다.\
문자열 리터럴 `"/admin/**"` 안은 렉서가 문자열로 읽으므로 주석 시작으로 해석되지 않는다 — 고친 방법은 **주석에서만** 경로 리터럴을 빼고 "admin 경로"처럼 서술하는 것이다.
   > **렉서(lexer)** — 소스 문자열을 토큰(주석·문자열·식별자)으로 자르는 컴파일러 첫 단계. 주석 중첩 여부는 여기서 정해진다.

2. **backtick 식별자의 한계.** backtick은 Kotlin **문법** 수준의 제약(공백·예약어)을 풀어줄 뿐, 결과 이름은 결국 **JVM 클래스 파일의 메서드 이름**이 된다.\
JVM 명세가 메서드 이름에 `.` `;` `[` `/` `<` `>`를 금지하고, Kotlin/JVM 컴파일러는 플랫폼 호환을 위해 여기에 `]` `:` `\` 등을 더 막는다 — 그래서 `Name contains illegal characters`로 실패한다(정확한 금지 목록은 컴파일러 버전·타깃에 따라 다를 수 있다).\
한글과 공백은 허용되므로, 테스트 이름에선 `:` 대신 공백이나 대시를 쓴다.

3. **배열의 참조 동등성.** data class의 자동 `equals`는 각 프로퍼티의 `equals`를 호출하는데, `ByteArray.equals`는 JVM 배열의 기본 동작인 **참조 비교**다.\
내용이 같아도 서로 다른 배열 객체면 false — 그래서 data class 전체의 `equals`·`hashCode`가 "값 객체"처럼 보이면서 거짓말을 한다(해시 컬렉션 조회도 어긋난다).\
고치는 법: ① `equals`/`hashCode`를 직접 써서 `contentEquals`/`contentHashCode`로 비교 ② 배열 필드를 가진 타입에 data class를 쓰지 않는다.
   > **참조 동등성(reference equality)** — 두 참조가 같은 객체를 가리키는지. **구조 동등성**은 내용이 같은지.

4. **안전망이다.** sealed 계층은 하위 타입 집합이 닫혀 있어서, `else` 없는 `when` 식은 컴파일러가 "모든 케이스를 다뤘나"를 검사한다(Kotlin 1.7+는 값을 쓰지 않는 `when` 문도 sealed·enum·Boolean 대상이면 검사 — 그 이전 버전의 문은 경고였다).\
새 케이스(예: 로그 레코드에 체크포인트 타입)를 추가하면 그것을 처리하지 않은 **모든 `when`이 컴파일 오류로 드러난다** — 수정해야 할 곳의 목록을 컴파일러가 만들어 주는 셈이다.\
`else ->`를 넣으면 새 케이스가 else로 조용히 흘러가 이 검사가 꺼진다. 그래서 sealed 분기에는 else를 두지 않고, 새 케이스를 의도적으로 무시할 곳은 `is NewCase -> { /* 무시 이유 */ }`로 명시한다.

5. **취소는 예외로 전파된다.** 코루틴의 협조적 취소는 중단 지점에서 `CancellationException`을 던지는 방식으로 스택을 거슬러 올라간다.\
이것도 `Exception`의 하위 타입이라 `catch (e: Exception)`에 걸리고, 그 catch가 RETRY를 반환하면 "작업을 멈춰라"는 신호가 "다시 시도하라"로 뒤집힌다 — 부모가 취소를 요청했는데 자식이 계속 일하는 **구조적 동시성 위반**이다.\
고치는 법: `catch (c: CancellationException) { throw c }`를 광범위 catch **앞에** 둔다. 그리고 "취소 예외를 던지는 가짜 의존성 → 실행이 예외 없이 반환되면 fail"인 **삼키면 실패하는 테스트**로 순서를 고정한다.
   > **구조적 동시성(structured concurrency)** — 코루틴의 생명주기를 부모 스코프에 묶어, 부모의 취소가 자식에게 반드시 전파되게 하는 규칙.

6. **기본값 인자 ≠ JVM 오버로드.** Kotlin 컴파일러는 기본값 인자를 가진 생성자에 대해 **모든 인자를 받는 시그니처 하나**(+ 내부용 합성 생성자)만 만든다.\
Kotlin 호출부는 컴파일러가 기본값을 채워 주니 문제가 없지만, **리플렉션으로 특정 인자 수의 생성자를 찾는** Java 쪽 프레임워크는 그 시그니처를 못 찾아 런타임에 `NoSuchMethodException`을 낸다 — 컴파일러가 보지 못하는 호출이라 컴파일은 통과한다. `@JvmOverloads`가 인자 수별 오버로드를 생성해 해결한다.\
트레일링 람다: 마지막 파라미터로 함수 타입 기본값 인자를 추가하면, 기존의 `Foo(a, b) { ... }` 호출에서 괄호 밖 람다가 **새 마지막 파라미터**에 바인딩된다(트레일링 람다는 항상 마지막 파라미터로 간다). 원래 받던 파라미터에 기본값이 없으면 "인자 누락" 컴파일 오류로 드러나지만, 기본값이 있으면 컴파일이 통과한 채 람다가 엉뚱한 파라미터로 가 **의미만 바뀐다**(`() -> Unit` 자리는 반환값이 있는 람다도 받는다). 호출부를 `Foo(a, b, { ... })`처럼 명시 인자(또는 이름 붙인 인자)로 바꿔 의도한 파라미터에 묶었다.

7. **컴파일러가 잡는 것**: 블록 주석 중첩(`Unclosed comment`), backtick 금지 문자, sealed `when` 누락, 트레일링 람다 재바인딩(원래 파라미터에 기본값이 없어 인자 누락이 될 때 — 기본값이 있으면 조용한 의미 변경이라 후자에 속한다).\
**런타임·의미로만 드러나는 것**: 배열 필드의 동등성(조용히 false), 취소 예외 흡수(정상 반환처럼 보임), 리플렉션 생성자(실행 시점에만 실패).\
후자는 컴파일 성공이 아무것도 증명하지 않으므로 ① 같은 내용·다른 인스턴스의 동등성 테스트 ② 취소를 주입해 "삼키면 실패"하는 테스트 ③ 실제 프레임워크 경로(리플렉션 생성)를 한 번 태우는 테스트를 둔다.

## 문제 구조 (추상화 코드)

### 변형 A — 주석 본문의 `/*`가 중첩 주석을 연다
① 문제 코드
```kotlin
/** 공개 경로는 오픈, /admin/** 경로는 인증 필요. */     // "/admin/*" 의 "/*" 가 안쪽 주석을 연다
@Configuration
class SecurityRules { /* ... */ }                       // 이후 파일 전체가 주석 → Unclosed comment
```
② 고친 코드
```kotlin
/** 공개 경로는 오픈, admin 경로는 인증 필요. */          // 주석에는 서술만
@Configuration
class SecurityRules {
    // ...
    http.authorizeHttpRequests { it.requestMatchers("/admin/**").authenticated() }   // 문자열 안은 안전
}
```
무엇이 깨졌나: Java 기준으로 쓴 주석이 Kotlin 렉서에서 짝이 맞지 않았고, 빌드 실패로 서비스가 통째 미기동했다.

### 변형 B — backtick 식별자도 JVM 이름 규칙을 따른다
① 문제 코드
```kotlin
@Test fun `Filter: age > 28`() { /* ... */ }             // ':' '>' → illegal characters
```
② 고친 코드
```kotlin
@Test fun `Filter age greater than 28`() { /* ... */ }  // 공백·한글은 허용, 기호는 풀어 쓴다
```
무엇이 깨졌나: 문법 수준의 탈출(backtick)이 바이트코드 수준의 이름 제약을 풀어 주지 않았다.

### 변형 C — sealed 케이스 추가를 컴파일러가 드러냄 (안전망으로 이용)
① 문제 코드
```kotlin
sealed class Record {
    data class Begin(/* ... */) : Record()
    data class Checkpoint(/* ... */) : Record()           // 신규
}
when (rec) {
    is Record.Begin -> apply(rec)
    // 'when' expression must be exhaustive
}
```
② 고친 코드
```kotlin
when (rec) {
    is Record.Begin -> apply(rec)
    is Record.Checkpoint -> { /* 구 복구 경로는 무시 — 이유 명시 */ }
}                                                         // else 를 두지 않아 다음 케이스 추가도 다시 드러난다
```
무엇이 깨졌나: 깨진 것이 아니라 드러난 것 — else가 있었다면 새 케이스가 조용히 흘러갔을 것이다.

### 변형 D — 배열 필드를 가진 data class의 동등성
① 문제 코드
```kotlin
data class Record(val data: ByteArray)
Record(byteArrayOf(1, 2)) == Record(byteArrayOf(1, 2))   // false — ByteArray.equals 는 참조 비교
```
② 고친 코드
```kotlin
class Record(val data: ByteArray) {
    override fun equals(other: Any?) = other is Record && data.contentEquals(other.data)
    override fun hashCode() = data.contentHashCode()
}
```
무엇이 깨졌나: 자동 생성 equals가 필드의 equals를 그대로 믿었고, 배열의 equals는 값 비교가 아니었다.\
같은 구조(의도 표현만 남는 규칙): 단일 빌드 모듈에서는 `internal`이 사실상 public이라 접근 제한이 걸리지 않는다 — 의도 표시로만 두고 규칙(테스트에서 internal 직접 접근 금지)으로 보완.

### 변형 E — 광범위 catch가 코루틴 취소를 삼킴
① 문제 코드
```kotlin
suspend fun run(repo: Repo): Result =
    try { repo.flush(); repo.pull(); SUCCESS }
    catch (e: Exception) { RETRY }                        // CancellationException 도 여기로 → 취소가 재시도로
```
② 고친 코드
```kotlin
suspend fun run(repo: Repo): Result =
    try { repo.flush(); repo.pull(); SUCCESS }
    catch (c: CancellationException) { throw c }          // 반드시 먼저 — 취소는 재전파
    catch (e: Exception) { RETRY }

@Test fun `취소 예외는 흡수하지 않고 재전파한다`() = runTest {
    val repo = ThrowingRepo(onFlush = CancellationException("취소"))
    try { run(repo); fail("삼키면 실패") } catch (c: CancellationException) { /* 기대 경로 */ }
    assertEquals(listOf("flush"), repo.calls)             // pull 에 도달하지 않음
}
```
무엇이 깨졌나: 제어 신호(취소)가 오류와 같은 예외 채널로 흘러, 오류 처리 정책에 흡수됐다.

### 변형 F — 기본값 인자와 JVM 상호운용·트레일링 람다
① 문제 코드
```kotlin
class Worker(ctx: Context, params: Params, deps: Deps = Deps.default()) : BaseWorker(ctx, params)
// 프레임워크가 리플렉션으로 (Context, Params) 생성자를 찾음 → NoSuchMethodException (컴파일은 통과)

class ViewModel(repo: Repo, id: String, idGen: () -> String, scheduler: () -> Unit = {})   // 마지막에 함수 타입 기본값 추가
ViewModel(repo, id) { "gen" }                            // 트레일링 람다가 idGen 이 아니라 scheduler 로 바인딩 → idGen 누락 컴파일 오류
                                                         // (idGen 에도 기본값이 있었다면 오류 없이 의미만 바뀐다)
```
② 고친 코드
```kotlin
class Worker @JvmOverloads constructor(ctx: Context, params: Params, deps: Deps = Deps.default()) : BaseWorker(ctx, params)

ViewModel(repo, id, { "gen" })                           // 명시 인자로 의도한 파라미터에 묶음
```
무엇이 깨졌나: Kotlin 컴파일러만 아는 편의(기본값·트레일링 람다)가 JVM 시그니처나 기존 호출부의 의미와 어긋났다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
