# PR #36965 — Generate compilable code for non-finite floating-point values

## 0. 정향

이 PR은 Spring AOT 코드 생성기가 `Float.NaN`, `Double.POSITIVE_INFINITY` 같은 비유한(non-finite) 부동소수점 값을 만났을 때 컴파일되지 않는 Java 소스를 뱉던 문제를 고친다. 고친 지점은 `spring-core`의 `ValueCodeGeneratorDelegates.PrimitiveDelegate` 한 곳이고, 변경 규모는 본문 18줄과 테스트 30줄이다. 다만 그 18줄을 이해하려면 "빈 정의를 Java 소스로 다시 써내는" AOT 파이프라인이 무엇인지부터 알아야 한다. 이 문서는 그 맥락에서 출발해 문제 재현과 수정, 검증까지 순서대로 따라간다.

이 PR의 좌표는 다음 세 가지다.

- PR: https://github.com/spring-projects/spring-framework/pull/36965
- 브랜치: `fix/valuecodegen-nan-infinity` (로컬 커밋 `a30836e112f`)
- 변경 파일: `spring-core/src/main/java/org/springframework/aot/generate/ValueCodeGeneratorDelegates.java`, `spring-core/src/test/java/org/springframework/aot/generate/ValueCodeGeneratorTests.java`

## 1. 배경 — ValueCodeGenerator란 무엇인가

`ValueCodeGenerator`는 런타임 값 하나를 "그 값을 다시 만들어내는 Java 식(expression)"으로 번역하는 변환기다. 입력은 `Object`, 출력은 JavaPoet의 `CodeBlock`이다. 예를 들어 문자열 `"test"`를 넣으면 `"test"`라는 소스 조각이, `List.of("a","b")`를 넣으면 `List.of("a", "b")`라는 소스 조각이 나온다. 즉 이 클래스는 값을 소비하는 것이 아니라 값을 다시 태어나게 하는 코드를 쓴다.

이런 번역이 필요한 이유는 Spring AOT 때문이다. GraalVM 네이티브 이미지나 AOT 최적화 빌드에서는 애플리케이션 컨텍스트를 런타임에 리플렉션으로 조립하는 대신, 빌드 시점에 빈 등록 코드를 Java 소스로 미리 생성해 함께 컴파일한다. 그러려면 `BeanDefinition`이 들고 있던 프로퍼티 값과 생성자 인자 값이 전부 소스 코드 형태로 바뀌어야 한다. 그 마지막 단계, 값에서 소스 문자열로 가는 변환을 담당하는 것이 `ValueCodeGenerator`다.

실제 호출처를 보면 성격이 분명해진다. `spring-beans`의 `BeanDefinitionPropertiesCodeGenerator`는 프로퍼티 값마다 이 생성기를 부른 뒤 그 결과를 문장에 끼워 넣는다.

```java
CodeBlock valueCode = generateValue(name, propertyValue.getValue());
code.addStatement("$L.getPropertyValues().addPropertyValue($S, $L)",
        BEAN_DEFINITION_VARIABLE, name, valueCode);
```
(`BeanDefinitionPropertiesCodeGenerator#addPropertyValues`)

같은 클래스가 생성자 인자(`addConstructorArgumentValues`)와 qualifier 값에도 같은 경로를 쓰고, `DefaultBeanRegistrationCodeFragments`와 `spring-web`의 `GroupsMetadataValueDelegate`도 이 생성기를 사용한다. 정리하면 `ValueCodeGenerator`는 "AOT 빌드가 값을 만날 때마다" 호출되는 좁고 깊은 길목이다.

구조는 단순한 책임 연쇄다. `ValueCodeGenerator`는 `Delegate` 목록을 순서대로 돌면서 처음으로 `null`이 아닌 `CodeBlock`을 돌려주는 위임자의 결과를 채택한다.

```java
public CodeBlock generateCode(@Nullable Object value) {
    if (value == null) {
        return NULL_VALUE_CODE_BLOCK;
    }
    try {
        for (Delegate delegate : this.delegates) {
            CodeBlock code = delegate.generateCode(this, value);
            if (code != null) {
                return code;
            }
        }
        throw new UnsupportedTypeValueCodeGenerationException(value);
    }
    catch (Exception ex) {
        throw new ValueCodeGenerationException(value, ex);
    }
}
```
(`ValueCodeGenerator#generateCode`)

기본 위임자 목록은 `ValueCodeGeneratorDelegates.INSTANCES`이며 `PrimitiveDelegate`가 맨 앞에 온다. 그 뒤로 `StringDelegate`, `CharsetDelegate`, `EnumDelegate`, `ClassDelegate`, `ResolvableTypeDelegate`, `ArrayDelegate`, 컬렉션·맵 위임자가 이어진다. 어느 위임자도 값을 처리하지 못하면 `UnsupportedTypeValueCodeGenerationException`이 난다. 이 "미지원이면 예외" 규칙이 뒤에서 중요해진다. 지원한다고 응답한 값이 잘못된 코드를 낳는 경우는 여기서 걸러지지 않기 때문이다.

## 2. 수정 전 동작 방식 — 값이 소스 문자열이 되기까지

수정 전 `PrimitiveDelegate`는 박싱된 원시 타입을 타입별로 분기해 포맷 문자열 하나씩을 골랐다.

```java
if (value instanceof Boolean || value instanceof Integer) {
    return CodeBlock.of("$L", value);
}
if (value instanceof Byte) {
    return CodeBlock.of("(byte) $L", value);
}
if (value instanceof Short) {
    return CodeBlock.of("(short) $L", value);
}
if (value instanceof Long) {
    return CodeBlock.of("$LL", value);
}
if (value instanceof Float) {
    return CodeBlock.of("$LF", value);
}
if (value instanceof Double) {
    return CodeBlock.of("(double) $L", value);
}
```
(수정 전 `PrimitiveDelegate#generateCode`)

여기서 핵심은 JavaPoet의 `$L` 플레이스홀더다. `$L`은 인자를 아무 가공 없이 리터럴로 찍는다. 즉 값의 `toString()` 결과가 그대로 소스 텍스트가 된다. `5L`이라는 `Long` 값은 `"$LL"`을 만나 `5L`이 되고, `0.1F`는 `"$LF"`를 거쳐 `0.1F`가 된다. `Double`은 접미사 대신 `(double)` 캐스트를 앞에 붙여 `(double) 0.2`가 된다. 각 분기는 "이 타입의 `toString()`은 유효한 Java 숫자 리터럴이다"라는 가정 위에 서 있다.

대비되는 것이 `$T` 플레이스홀더다. `$T`는 인자를 타입으로 다루어 이름을 찍고, 동시에 생성 중인 파일의 import 목록을 관리한다. 같은 파일 안 다른 위임자들이 이미 이 방식을 쓴다. `EnumDelegate`는 `CodeBlock.of("$T.$L", enumValue.getDeclaringClass(), enumValue.name())`으로 열거 상수를 참조하고, `ClassDelegate`는 `CodeBlock.of("$T.class", ClassUtils.getUserClass(clazz))`를 낸다. 다시 말해 "값을 이름 있는 상수로 가리키는" 표현 수단은 이미 이 코드베이스에 있었고, 원시 타입 분기만 그것을 쓰지 않았다.

## 3. 무엇이 문제였나 — NaN과 Infinity가 만드는 컴파일 불가 코드

문제는 IEEE 754의 비유한 값 세 종류에서 터진다. `Float.toString`과 `Double.toString`은 이 값들에 대해 숫자가 아닌 단어를 돌려준다. `NaN`은 `"NaN"`, 양의 무한대는 `"Infinity"`, 음의 무한대는 `"-Infinity"`다. 그런데 Java 언어에는 이 셋을 표현하는 리터럴 문법이 없다. `NaN`은 그냥 식별자로 파싱되고, `Infinity`도 마찬가지다. `$L`이 `toString()`을 그대로 옮기는 순간 소스는 깨진다.

수정 전 코드가 각 값에 대해 실제로 만들어내던 출력은 다음과 같다.

| 값 | 생성된 코드 | 컴파일 |
|---|---|---|
| `Float.NaN` | `NaNF` | 불가 |
| `Float.POSITIVE_INFINITY` | `InfinityF` | 불가 |
| `Float.NEGATIVE_INFINITY` | `-InfinityF` | 불가 |
| `Double.NaN` | `(double) NaN` | 불가 |
| `Double.POSITIVE_INFINITY` | `(double) Infinity` | 불가 |
| `Double.NEGATIVE_INFINITY` | `(double) -Infinity` | 불가 |

이 실패가 특히 다루기 나쁜 이유는 실패 시점이 늦고 위치가 엉뚱하기 때문이다. 코드 생성 자체는 조용히 성공한다. `PrimitiveDelegate`는 `Float`를 지원한다고 응답했으므로 `UnsupportedTypeValueCodeGenerationException`도 나지 않는다. 문제는 그 뒤 javac 단계에서, 생성된 `*__BeanDefinitions.java` 파일의 알 수 없는 심벌 오류로 드러난다. 사용자가 보는 것은 자기가 쓰지 않은 파일의 `cannot find symbol: NaN`이고, 원인인 "어떤 빈의 어떤 프로퍼티가 무한대였다"는 사실은 그 메시지 어디에도 없다.

재현 조건은 평범하다. 빈 프로퍼티나 생성자 인자에 무한대·NaN이 들어 있으면 된다. 임계값을 "제한 없음" 의미로 `Double.POSITIVE_INFINITY`로 두거나, 초기화되지 않은 통계 필드를 `Double.NaN`으로 두는 설정은 흔하다. 그런 빈 하나면 AOT 빌드 전체가 컴파일에 실패한다. 실패 범위가 빈 하나가 아니라 생성 소스 집합 전체라는 점에서 blast radius가 작지 않다.

## 4. 수정 해설 — 무엇을 왜 바꿨나

수정의 핵심 아이디어는 한 줄이다. 리터럴로 찍을 수 없는 값은 리터럴 대신 상수 필드 참조로 가리킨다. `Float.NaN`과 `Double.POSITIVE_INFINITY` 같은 필드는 JDK가 제공하는 `public static final` 상수이므로, 이름으로 참조하면 언제나 유효한 Java 식이 된다.

```java
if (value instanceof Float floatValue) {
    if (Float.isNaN(floatValue)) {
        return CodeBlock.of("$T.NaN", Float.class);
    }
    if (floatValue == Float.POSITIVE_INFINITY) {
        return CodeBlock.of("$T.POSITIVE_INFINITY", Float.class);
    }
    if (floatValue == Float.NEGATIVE_INFINITY) {
        return CodeBlock.of("$T.NEGATIVE_INFINITY", Float.class);
    }
    return CodeBlock.of("$LF", value);
}
if (value instanceof Double doubleValue) {
    if (Double.isNaN(doubleValue)) {
        return CodeBlock.of("$T.NaN", Double.class);
    }
    if (doubleValue == Double.POSITIVE_INFINITY) {
        return CodeBlock.of("$T.POSITIVE_INFINITY", Double.class);
    }
    if (doubleValue == Double.NEGATIVE_INFINITY) {
        return CodeBlock.of("$T.NEGATIVE_INFINITY", Double.class);
    }
    return CodeBlock.of("(double) $L", value);
}
```
(수정 후 `PrimitiveDelegate#generateCode`)

세부 선택지 네 가지를 짚어둘 만하다.

첫째, NaN 판별에 `==`가 아니라 `isNaN()`을 쓴다. IEEE 754에서 NaN은 자기 자신과도 같지 않아 `Float.NaN == Float.NaN`은 항상 `false`다. 무한대는 그 규칙의 예외가 아니라 정상적인 비교 대상이므로 `==`로 충분하다. 두 판별 방식이 섞인 것은 실수가 아니라 명세를 따른 결과다.

둘째, `instanceof Float`가 `instanceof Float floatValue` 패턴으로 바뀌었다. 값을 두 번 이상 검사해야 하므로 바인딩 변수가 필요했고, 이때 언박싱은 패턴 변수 사용 지점에서 일어난다. 같은 파일의 `instanceof Character character` 분기가 이미 쓰던 관용구라 스타일도 일관된다.

셋째, `$T`를 쓴 이유는 import 처리 때문이다. `$L`로 `"Float.NaN"` 문자열을 직접 찍어도 대부분 동작하겠지만, 그러면 생성 파일에 같은 단순 이름의 다른 타입이 있을 때 충돌한다. `$T`에 `Float.class`를 넘기면 JavaPoet이 파일 문맥을 보고 단순 이름과 정규화 이름 중 안전한 쪽을 고른다. 이는 `EnumDelegate`, `ClassDelegate`가 쓰던 방식과 동일하다.

넷째, 유한한 값의 처리는 손대지 않았다. 세 검사 중 어느 것도 걸리지 않으면 기존의 `"$LF"`와 `"(double) $L"`로 그대로 떨어진다. 따라서 정상 숫자의 출력 형태는 문자 하나도 달라지지 않으며, 이는 하위 호환과 회귀 위험을 동시에 낮추는 선택이다. `-0.0` 같은 특이값도 `toString()`이 `"-0.0"`이라 기존 경로에서 이미 유효하다.

## 5. 검증 — 각 테스트가 무엇을 고정하는가

테스트는 `ValueCodeGeneratorTests`의 `PrimitiveTests` 중첩 클래스에 여섯 개가 추가됐다. `Float`와 `Double` 각각에 대해 NaN, 양의 무한대, 음의 무한대를 덮는 곱집합이다.

```java
@Test
void generateWhenFloatNaN() {
    assertThat(generateCode(Float.NaN)).hasToString("java.lang.Float.NaN");
}

@Test
void generateWhenDoubleNegativeInfinity() {
    assertThat(generateCode(Double.NEGATIVE_INFINITY)).hasToString("java.lang.Double.NEGATIVE_INFINITY");
}
```
(추가된 테스트 중 두 개)

기대값이 단순 이름이 아니라 `java.lang.Float.NaN`인 데는 이유가 있다. `generateCode`는 `ValueCodeGenerator.withDefaults().generateCode(value)`를 부르고 그 `CodeBlock`을 바로 문자열화한다. import 축약은 `CodeBlock`이 `JavaFile` 안에 배치될 때 일어나므로, 파일 문맥 없이 찍으면 `$T`는 정규화된 이름으로 나온다. 같은 파일에서 클래스나 컬렉션을 검사하는 테스트들이 `resolve(...)` 헬퍼로 `JavaFile`을 만들어 import를 확인하는 것과 대비된다. 즉 이 여섯 테스트가 고정하는 것은 "어떤 타입의 어떤 상수를 참조하는가"이지 "짧은 이름으로 찍히는가"가 아니다.

기존 테스트 두 개도 회귀 방어선으로 계속 작동한다. `generateWhenFloat`는 `0.1F`가, `generateWhenDouble`은 `(double) 0.2`가 유지되는지를 본다. 수정이 유한 경로를 건드리지 않았다는 4절의 주장은 이 두 테스트로 실증된다.

한 가지 남는 한계는 짚어둘 만하다. 이 테스트들은 생성된 문자열을 비교할 뿐 실제로 javac를 돌려 컴파일 가능성을 확인하지는 않는다. 다만 `java.lang.Float.NaN`이 유효한 상수 참조라는 것은 언어 명세 수준에서 자명하고, 기존 `PrimitiveTests`도 모두 문자열 비교 방식이라 관례를 따른 셈이다.

## 6. 상태와 교훈

PR은 2026-06-24에 열렸고 이 문서 작성 시점까지 `OPEN` 상태이며 리뷰는 아직 달리지 않았다. 진행 중 있었던 대화는 본 수정과 무관한 CI 실패에 관한 것이었다. `Build Pull Request` 워크플로가 `SimpleAsyncTaskExecutorTests.taskTerminationTimeoutWithImmediateCancel()`에서 실패했고, 기여자가 그 실패의 경합 조건을 분석해 이 PR과 무관함을 설명했다. 메인테이너 `bclozel`이 워크플로를 재실행하면서 그 flaky 테스트를 별도 기여로 고쳐달라고 요청했고, 그 결과가 별도 PR #36967이다. 하나의 PR을 하나의 관심사로 유지한 덕에 무관한 실패를 분리해낼 수 있었던 사례다.

교훈 두 가지를 남긴다. 첫째, `toString()` 결과를 소스 코드로 재사용하는 코드는 그 타입의 값 집합 전체를 훑어야 한다. 숫자 타입이라고 해서 `toString()`이 항상 리터럴 문법을 만족하지는 않으며, 부동소수점의 비유한 값이 정확히 그 반례다. 같은 종류의 질문을 다른 위임자에게도 던져볼 수 있다. 둘째, "예외가 나지 않는다"는 성공의 증거가 아니다. 이 결함에서 코드 생성 단계는 끝까지 조용히 성공했고, 실패는 한 단계 뒤 컴파일에서 원인과 동떨어진 메시지로 나타났다. 파이프라인의 중간 단계를 고칠 때는 출력이 다음 단계의 문법을 만족하는지를 직접 물어야 한다.

## 7. 머지 — 72일의 트리아지 대기 끝에

2026-09-04에 Brian Clozel이 `4a803961bc5`로 머지했다. 코멘트는 없었고, 커밋은 제출한
그대로다. author와 authored date(2026-06-24)가 유지됐으며 `ValueCodeGeneratorDelegates`
프로덕션 변경과 `ValueCodeGeneratorTests`의 여섯 테스트 diff가 제출본과 바이트 단위로
같다. 후속 polish 커밋도 없다. 7.0.x와 main 양쪽에 들어갔고 마일스톤은 7.0.10,
라벨은 `type: bug`와 `in: core`다.

기록해 둘 것은 시간이다. 6월 24일 제출에서 9월 4일 머지까지 72일 동안 리뷰 코멘트도
라벨 변경도 없었다. 큐에서 조용한 것이 거절의 신호는 아니라는 사례다. 넛지는 한 번도
하지 않았고, 트리아지가 이 영역에 도달했을 때 그대로 처리됐다. 반응이 없는 기간에
할 일은 재촉이 아니라, PR을 리뷰어가 한 번에 판정할 수 있는 상태로 유지해 두는 것이다.

한편 6절에서 언급한 CI flaky 대화는 별도 결과를 냈다. 무관한 실패로 분석해 낸
`SimpleAsyncTaskExecutorTests.taskTerminationTimeoutWithImmediateCancel`은 메인테이너
요청으로 PR #36967이 되어 2026-07-12에 먼저 머지됐고(7.0.9), 정작 본 PR은 그보다
두 달 가까이 뒤에 처리됐다. 하나의 PR을 하나의 관심사로 유지한 덕에 파생 기여가
본 PR의 대기와 무관하게 독립적으로 흘러갈 수 있었다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
