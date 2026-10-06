# issue/kotlin/spring/default-argument-evaluated-on-proxy — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **호출 쪽 합성 함수에서, 호출자가 넘긴 참조를 수신자로.** Kotlin은 기본 인자가 있는 멤버 함수마다 정적 합성 함수 `이름$default(self, 인자…, mask, marker)`를 만든다.\
   인자를 생략한 호출은 원래 메서드가 아니라 이 합성 함수로 컴파일되고, 생략된 인자의 기본값 식은 **그 안에서** `self`를 수신자로 계산된 뒤 원래 메서드에 넘겨진다.\
   그래서 `= repository::findById`는 "이 메서드가 실행될 객체의 필드"가 아니라 **"호출자가 들고 있던 참조의 필드"**를 읽는다. 호출자가 들고 있던 것이 프록시라 프록시의 필드(null)를 읽었고, 그 null로 만든 조회 함수가 NPE를 냈다(기존 테스트 38개 중 14개 실패).
   > **`$default` 합성 함수** — 기본 인자를 구현하려고 컴파일러가 만드는 정적 함수. 비트마스크로 생략된 인자를 알고 그 자리의 기본값 식을 계산한다.

2. **주입은 대상 객체에, 참조는 프록시로.** `@Transactional` 같은 어드바이스가 붙은 빈은 프록시로 감싸 등록되고, 다른 빈이 주입받는 것은 그 프록시다.\
   클래스 기반(CGLIB) 프록시는 대상 클래스를 상속한 하위 클래스의 인스턴스라 같은 필드 선언을 갖지만, Spring은 이 인스턴스를 생성자 호출 없이 만들고 의존성은 **대상 객체에만** 주입한다 — 프록시의 필드는 JVM 기본값(null)으로 남는다.\
   평소에는 문제가 없다 — 프록시의 공개 메서드는 가로채져 대상 객체로 위임되고, 필드는 대상 객체의 본문에서만 읽히기 때문이다. 기본 인자는 이 위임 **앞**에서 필드를 읽는 드문 통로다.
   > **CGLIB 프록시** — 인터페이스 없이 대상 클래스를 상속해 메서드를 가로채는 프록시. Kotlin 클래스는 기본이 final이라 Spring용 컴파일러 플러그인이 열어 준다.

3. **필드를 읽느냐.** `= {}`(아무것도 하지 않는 람다)는 `self`의 상태를 쓰지 않으므로 어느 인스턴스를 수신자로 계산해도 결과가 같다 — 실제로 이 기본 인자는 고친 뒤에도 그대로 두었고 문제가 없었다.\
   `= repository::findById`는 `self.repository`를 읽는다. 위험한 것은 기본 인자 자체가 아니라 **수신자의 상태에 기대는 기본값 식**이다.

4. **드러나지 않는다.** 대상 객체를 직접 생성해 부르면 `self`가 진짜 객체이고 필드가 채워져 있어 기본값이 정상 계산된다.\
   이 결함은 **실제 컨텍스트에서 주입받은 빈(=프록시)으로 기본 인자를 생략해 부르는** 경로에서만 난다 — 이 사례에서는 컨텍스트를 띄우는 기존 통합 테스트가 잡았다.

5. **본문은 대상 객체 위에서 돈다.** 기본값을 `null`로 두면 합성 함수는 필드를 읽지 않고 `null`만 넘긴다. 프록시는 이 호출을 가로채 어드바이스를 적용한 뒤 대상 객체의 메서드로 위임하고, 본문의 `loader ?: this.repository::findById`는 주입이 끝난 **대상 객체의 필드**를 읽는다.\
   비용은 시그니처에 nullable 타입이 하나 생기는 것뿐이다. 이 사례에서는 수정 후 기존 테스트 38/38이 통과했고, 이어서 추가한 테스트까지 63/63이 통과했다. 같은 이유를 코드 주석에 남겨 다시 기본 인자로 되돌리지 않게 했다.

6. **결함의 위치가 흐려진다.** 이 변경은 "새 인자를 생략한 기본 경로 = 기존 동작"을 전제로 그 위에 여러 경합 제어 전략을 얹는 작업이었다.\
   전제를 착수 직후 기존 테스트로 실증해서 실패 14건이 **방금 바꾼 한 시그니처**로 좁혀졌다. 전략 구현까지 쌓은 뒤였다면 같은 NPE가 전략 코드·트랜잭션 설정·테스트 픽스처 중 어디의 결함인지부터 가려야 했다.

## 문제 구조 (추상화 코드)

### 변형 A — 수신자의 필드를 읽는 기본 인자 × 클래스 기반 프록시

① 문제 코드
```kotlin
@Component
class ItemProcess(private val repository: ItemRepository) {
    @Transactional(propagation = Propagation.MANDATORY)
    fun process(
        cmd: Command,
        loader: (Long) -> Item? = repository::findById,   // 호출 쪽 $default에서 self.repository로 계산
        before: (Item) -> Unit = {},                      // 상태를 안 읽음 → 무해
    ): Result {
        val item = loader(cmd.id) ?: throw NotFound()
        // ...
    }
}

@Service
class LockingStrategy(private val process: ItemProcess) {    // 주입된 것은 프록시
    @Transactional
    fun run(cmd: Command) = process.process(cmd)              // loader 생략 → 프록시의 null 필드 → NPE
}
```
② 고친 코드
```kotlin
@Transactional(propagation = Propagation.MANDATORY)
fun process(
    cmd: Command,
    loader: ((Long) -> Item?)? = null,                        // 기본값은 상태와 무관한 상수
    before: (Item) -> Unit = {},
): Result {
    val load = loader ?: repository::findById                 // 본문 = 대상 객체 위 → 주입된 필드
    val item = load(cmd.id) ?: throw NotFound()
    // ...
}
```
무엇이 깨졌나: 기본값 식이 "메서드가 실행될 객체"가 아니라 "호출자가 가진 참조(프록시)"를 수신자로 계산돼, 주입되지 않은 프록시의 필드를 읽었다.

```text
# 컴파일 결과의 형태 (javap -p, 이름 일반화)
public Result process(Command, Function1, Function1);
public static Result process$default(ItemProcess, Command, Function1, Function1, int, Object);   ← self를 인자로 받는 정적 함수
```

## 검증 기록
- 2026-10-06: 사건 기록 대조·추상화(Claude 초안) — 컴파일된 클래스의 `$default` 정적 합성 함수는 javap로 확인
