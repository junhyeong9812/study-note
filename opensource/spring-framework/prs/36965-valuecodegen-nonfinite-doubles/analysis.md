# PR #36965 분석 — ValueCodeGenerator가 NaN·Infinity에서 컴파일 불가 코드를 생성하는 결함

> 기준: PR 머지베이스 `a077324670693187ea98c33591e90831e5da12c9` 대비 `refs/pr/36965`.
> 이 문서는 결함의 경로 추적과 계약 분석에 집중한다. 배경과 교훈은 README.md,
> 무대의 소유 관계도와 AOT 파이프라인 지도는 structure.md, 테스트 여섯 건의 해설은
> tests.md가 각각 맡는다.

## 0. 결론

`ValueCodeGeneratorDelegates.PrimitiveDelegate`의 `Float`·`Double` 분기는 JavaPoet의
`$L`(리터럴) 플레이스홀더로 값의 `toString()`을 그대로 소스에 찍는다. 그런데 IEEE 754의
비유한 값 세 종류는 `toString()`이 `"NaN"`·`"Infinity"`·`"-Infinity"`이고, Java 언어에는
이 셋을 표현하는 리터럴 문법이 없다. 결과적으로 AOT가 `NaNF`나 `(double) Infinity` 같은
**컴파일되지 않는 소스**를 조용히 생성한다.

수정은 두 분기 안에서 세 특수값을 먼저 판별해 `$T.NaN`·`$T.POSITIVE_INFINITY`·
`$T.NEGATIVE_INFINITY`라는 JDK 상수 필드 참조로 내보내고, 유한한 값만 기존 리터럴
경로로 떨어뜨리는 것이다.

PR 상태는 2026-08-25 확인 기준 OPEN이며 라벨은 `status: waiting-for-triage`와
`in: core`, 생성일은 2026-06-24이다. 달린 코멘트 4건은 전부 이 변경과 무관한 flaky CI
실패(`SimpleAsyncTaskExecutorTests.taskTerminationTimeoutWithImmediateCancel`)에 관한
대화이며, 메인테이너 요청으로 그 flaky 테스트는 별도 PR #36967이 되었다. 이 PR 자체에
대한 리뷰는 아직 없다.

## 1. 무대

결함은 AOT 코드 생성기의 값 변환 체인 맨 앞에 있는 위임자 하나에 산다. 그 좌표를 모듈부터 위임자 목록까지 네 항목으로 고정한다.

- 모듈: `spring-core`, 패키지 `org.springframework.aot.generate`.
- 결함 클래스: `spring-core/src/main/java/org/springframework/aot/generate/ValueCodeGeneratorDelegates.java`
  의 `private static class PrimitiveDelegate implements Delegate`(`:195`), 메서드
  `generateCode(ValueCodeGenerator, Object)`(`:210`).
- 진입 클래스: `ValueCodeGenerator`(`public final`, `ValueCodeGenerator.java:35`),
  공개 진입 API는 `generateCode(@Nullable Object)`(`:107`)와 팩터리
  `withDefaults()`(`:59`)·`with(...)`(`:68`, `:77`)·`add(...)`(`:83`)·`scoped(...)`(`:98`).
- 위임자 목록: `ValueCodeGeneratorDelegates.INSTANCES`(`:68`) — `PrimitiveDelegate`가
  0번, 그 뒤로 String/Charset/Enum/Class/ResolvableType/Array/List/Set/Map이 온다.

누가 언제 부르는가. 전부 **AOT 빌드 시점**이며 런타임 요청 경로에는 없다. 확인된
소비처는 네 부류다. (1) 빈 정의 경로 — `spring-beans`의
`BeanDefinitionPropertiesCodeGenerator`가 생성자 인자·프로퍼티 값·qualifier 값마다
`generateValue(name, value)`를 거쳐 호출한다. (2) 빈 타입 경로 —
`DefaultBeanRegistrationCodeFragments`가 `withDefaults()`로 `Class`·`ResolvableType`을
옮긴다. (3) 모듈 확장 — `spring-web`의 `GroupsMetadataValueDelegate`. (4) 테스트
컨텍스트 — `TestAotProcessor` 경로.

빈 정의 경로는 확장 목록을 쓰므로 `PrimitiveDelegate`가 0번이 아니라 코어 블록의 첫
자리로 밀린다. 다만 앞선 위임자들(`ManagedList`·`BeanReference`·`TypedStringValue` 등)이
박싱 원시 타입을 매칭하지 않으므로, 실제로 `Float`·`Double`을 받는 것은 여전히
`PrimitiveDelegate`다.

## 2. 전체 메서드 그래프

빌드 태스크 진입부터 결함 지점, 그리고 잘못된 문자열이 실패로 드러나는 지점까지다.

```
[AOT 빌드 태스크]
  -> ContextAotProcessor.doProcess() -> performAotProcessing(applicationContext)
  -> ApplicationContextAotGenerator.processAheadOfTime(ctx, generationContext)
       |
       +-- 빈마다: BeanRegistrationCodeGenerator.generateCode(...)
       |     -> DefaultBeanRegistrationCodeFragments.generateSetBeanDefinitionPropertiesCode(...)
       |     -> new BeanDefinitionPropertiesCodeGenerator(...).generateCode(rootBeanDefinition)
       |          +-- addConstructorArgumentValues / addPropertyValues / addQualifiers
       |                셋 다 generateValue(name, value) 경유
       |                |
       |                v
       |          ValueCodeGenerator.generateCode(value)          ValueCodeGenerator.java:107
       |                +-- value == null -> NULL_VALUE_CODE_BLOCK                    :108-110
       |                +-- for (Delegate d : delegates) { code = d.generateCode(this, value);
       |                |       code != null -> return code }  (검증 없이 첫 성공 채택)  :112-116
       |                +-- 전원 null -> throw UnsupportedTypeValueCodeGenerationException :118
       |                      |
       |                      v
       |          PrimitiveDelegate.generateCode(codeGenerator, value)   Delegates.java:210
       |                +-- Boolean|Integer "$L" :211 / Byte "(byte) $L" :214 / Short :217
       |                +-- Long "$LL"                                               :220-222
       |                +-- Float  -> "$LF"           <== 결함 지점                    :223-225
       |                +-- Double -> "(double) $L"   <== 결함 지점                    :226-228
       |                +-- Character -> "'$L'" + escape(ch) :229 / 그 외 -> null      :232
       |                      |
       |                      v
       |                CodeBlock.of(format, args)   $L 은 인자의 toString() 을 가공 없이 인쇄
       |
       +-- generationContext.writeGeneratedContent()
             -> *__BeanDefinitions.java 를 sourceOutput 에 기록
                  |
                  v
             [javac]  <== 결함이 실제로 드러나는 지점. "cannot find symbol: NaN" 등
                          사용자가 작성하지 않은 생성 파일에서 실패한다
```

중첩 값도 같은 지점을 지난다. `List.of(1.0F, Float.NaN)` 같은 값이 오면
`ListDelegate`가 원소마다 `codeGenerator.generateCode(...)`를 재귀 호출하고, 재귀는
위임자 목록을 처음부터 다시 훑으므로 원소 하나하나가 `PrimitiveDelegate`를 통과한다.
즉 컬렉션·배열·맵 어디에 묻혀 있든 원시 값은 결국 이 분기로 수렴한다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 지점은 "값"이 세 형태로 오간다는 것이다: 실행 중인 JVM의 박싱된
객체, JavaPoet의 포맷 인자, 그리고 최종 소스 텍스트. 아래는 등장하는 식별자 전부에
대한 역할과 이 결함과의 관계다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `ValueCodeGenerator.generateCode(Object)` (ValueCodeGenerator.java:107) | 공개 진입점. 위임자 체인을 돌린다 | `Object` -> `CodeBlock` | AOT 코드 생성기가 값마다 | 결함 있는 `CodeBlock`을 그대로 반환한다 |
| `delegates` 필드 (:43) | 순서 있는 위임자 목록. 앞에서부터 시도 | `List<Delegate>` | 생성자에서 고정 | `PrimitiveDelegate`가 원시 값을 선점하는 근거 |
| `INSTANCE` / `withDefaults()` (:37, :59) | 기본 목록으로 구성된 공유 인스턴스 | -> `ValueCodeGenerator` | `DefaultBeanRegistrationCodeFragments`, 테스트 | 테스트가 쓰는 진입 형태 |
| `NULL_VALUE_CODE_BLOCK` (:40) | `null` 값 전용 상수 `CodeBlock.of("null")` | -- | `generateCode` :108-110 | 무관 |
| `Delegate.generateCode(...)` (:151) | 전략 인터페이스. **미지원이면 예외가 아니라 `null`** | `(gen, value)` -> `@Nullable CodeBlock` | 체인 순회 중 | 이 계약 때문에 "지원한다고 응답했는데 틀린" 경우를 걸러낼 자리가 없다 |
| `UnsupportedTypeValueCodeGenerationException` (:118) | 아무 위임자도 처리하지 못했을 때 | -- | 체인 끝 | 유일한 방어선인데, 이 결함은 여기 걸리지 않고 통과한다 |
| `ValueCodeGenerationException` (:121) | 위임자 내부 예외를 감싸 값 문맥을 붙임 | -- | catch 블록 | 무관. 결함 경로는 예외를 던지지 않는다 |
| `generatedMethods` / `scoped(...)` (:45, :98) | 생성 메서드 스코프 | -- | 빈 정의 경로가 사용 | 무관. `PrimitiveDelegate`는 스코프를 요구하지 않는다 |
| `add(List<Delegate>)` (:83) | 목록 뒤에 규칙을 덧붙임 | -- | 모듈 확장 | 무관 |
| `ValueCodeGeneratorDelegates.INSTANCES` (Delegates.java:68) | 기본 위임자 10종 | -- | `withDefaults`, 빈 정의용 목록 조립 | `PrimitiveDelegate`가 0번임을 정하는 자리 |
| `PrimitiveDelegate` (:195) | 박싱 원시 타입 전담 위임자 | -- | 체인 0번 | 결함이 있는 클래스 |
| `PrimitiveDelegate.generateCode` (:210) | 타입별 포맷 선택 | `Object` -> `@Nullable CodeBlock` | 값마다 | 결함이 있는 메서드 본체 |
| `value` (:210 파라미터) | 번역 대상 값. 정적 타입은 `Object` | -- | -- | `Object`라 부동소수점 연산을 직접 못 쓴다. 패턴 변수가 필요한 이유 |
| `floatValue` / `doubleValue` (수정 후 :223, :235 패턴 변수) | `instanceof` 패턴이 바인딩한 언박싱 대상 | -- | 특수값 판별 3회 | 수정이 도입한 이름. Java 16+ 패턴 매칭 |
| `CHAR_ESCAPES` / `escape(char)` (:197, :253) | 문자 리터럴 이스케이프 표와 함수 | `char` -> `String` | `Character` 분기 :230 | 같은 클래스의 다른 관심사. **"toString이 곧 리터럴은 아니다"를 이미 인정한 선례** |
| `CodeBlock.of(format, args...)` | 소스 조각 + 참조 타입 목록을 담은 값 객체 생성 | -- | 모든 분기 | 출력 형태 |
| `$L` (리터럴 플레이스홀더) | 인자를 **가공 없이** 그대로 인쇄 | `Object` -> 그 `toString()` | `"$L"`, `"$LL"`, `"$LF"`, `"(double) $L"` | 결함의 통로. `$L` 자체는 정상 동작이고, 오용된 것이다 |
| `$T` (타입 플레이스홀더) | 인자를 타입으로 다뤄 이름을 인쇄하고 import를 관리 | `Class`/`TypeName` -> 안전한 이름 | `EnumDelegate` `"$T.$L"`, `ClassDelegate` `"$T.class"`, (수정 후) `"$T.NaN"` | 수정이 재사용하는 표현 수단. 새 개념이 아니다 |
| `$S` (문자열 플레이스홀더) | 인자를 따옴표로 감싸고 이스케이프 | -- | `StringDelegate` | 무관. 대조용 |
| `Float.isNaN(f)` / `Double.isNaN(d)` | NaN 판별 | `float`/`double` -> `boolean` | 수정 후 :224, :236 | `NaN == NaN`이 항상 false이므로 `==`로는 불가능. 명세가 강제한 선택 |
| `Float.POSITIVE_INFINITY` / `NEGATIVE_INFINITY` (및 `Double` 대응) | 무한대 상수 필드 | -- | 수정 후 판별(:227, :230 등)과 출력 문자열 양쪽 | 판별 대상이자 생성될 참조 이름 |

## 3. 결함 경로 단계 추적

먼저 값 하나가 소스 텍스트가 되기까지를 정상·결함 두 축으로 비교한다.

| 단계 | 정상 케이스 `0.1F` | 결함 케이스 `Float.NaN` | 결함 케이스 `Double.NEGATIVE_INFINITY` |
|---|---|---|---|
| 체인 진입 (:107) | `Float` 객체 | `Float` 객체 | `Double` 객체 |
| 위임자 0번 (:210) | `instanceof Float` 참 | `instanceof Float` 참 | `instanceof Double` 참 |
| 분기 선택 | `:224` `"$LF"` | `:224` `"$LF"` (같은 분기) | `:227` `"(double) $L"` |
| `$L`이 인쇄하는 값 | `Float.toString(0.1f)` = `"0.1"` | `Float.toString(NaN)` = `"NaN"` | `Double.toString(-inf)` = `"-Infinity"` |
| 생성된 소스 조각 | `0.1F` | `NaNF` | `(double) -Infinity` |
| 코드 생성 단계 결과 | 성공 | **성공(예외 없음)** | **성공(예외 없음)** |
| 파일 기록 후 javac | 통과 | `cannot find symbol` 류 실패 | `Infinity`가 식별자로 파싱되어 실패 |
| 수정 후 조각 | `0.1F` (무변경) | `java.lang.Float.NaN` | `java.lang.Double.NEGATIVE_INFINITY` |

여섯 개 특수값 전체를 한 표로 모으면 수정 전후가 이렇다.

| 값 | 수정 전 생성 코드 | 컴파일 | 수정 후 생성 코드 |
|---|---|---|---|
| `Float.NaN` | `NaNF` | 불가 | `java.lang.Float.NaN` |
| `Float.POSITIVE_INFINITY` | `InfinityF` | 불가 | `java.lang.Float.POSITIVE_INFINITY` |
| `Float.NEGATIVE_INFINITY` | `-InfinityF` | 불가 | `java.lang.Float.NEGATIVE_INFINITY` |
| `Double.NaN` | `(double) NaN` | 불가 | `java.lang.Double.NaN` |
| `Double.POSITIVE_INFINITY` | `(double) Infinity` | 불가 | `java.lang.Double.POSITIVE_INFINITY` |
| `Double.NEGATIVE_INFINITY` | `(double) -Infinity` | 불가 | `java.lang.Double.NEGATIVE_INFINITY` |

이 실패가 다루기 나쁜 이유는 **실패 시점이 늦고 위치가 엉뚱하기 때문**이다. 코드 생성은
끝까지 조용히 성공한다. `PrimitiveDelegate`가 "이 타입을 지원한다"고 응답했으므로
`UnsupportedTypeValueCodeGenerationException`도 나지 않는다. 사용자가 보는 것은 자기가
쓰지 않은 `*__BeanDefinitions.java`의 심벌 오류이고, 원인인 "어떤 빈의 어떤 프로퍼티가
무한대였다"는 사실은 그 메시지 어디에도 없다. 게다가 실패 범위는 그 빈 하나가 아니라
생성 소스 집합 전체의 컴파일이다.

재현 조건 자체는 평범하다. 임계값을 "제한 없음" 의미로 `Double.POSITIVE_INFINITY`로
두거나, 초기화되지 않은 통계 필드를 `Double.NaN`으로 두는 빈 설정이면 충분하다.

## 4. 계약

**Delegate의 명시 계약.** `ValueCodeGenerator.Delegate#generateCode`의 javadoc은
지원하지 않는 값에 대해 예외가 아니라 `null`을 돌려주라고 규정한다. 덕분에 진입점은
"첫 성공을 채택하고 나머지는 무시"라는 루프 하나로 임의 개수의 위임자를 조합할 수 있다.
`PrimitiveDelegate`는 이 계약을 어기지 않는다 — `Float`를 지원한다고 응답한 것 자체는
맞다.

**암묵 계약 — 반환한 조각은 유효한 Java 식이어야 한다.** 이것이 결함이 어기는 계약이다.
`ValueCodeGenerator`에는 채택된 `CodeBlock`이 문법적으로 유효한지 확인하는 단계가 없고
(`:112-116`), 유일한 검사인 `:118`은 "아무도 이 타입을 모른다"만 잡는다. 즉 이 계약은
코드로 강제되지 않고 각 `Delegate`가 스스로 지켜야 하는 것이며, 각 분기는 "이 타입의
`toString()`은 유효한 Java 숫자 리터럴이다"라는 가정 위에 서 있다. `Boolean`·`Integer`·
`Byte`·`Short`·`Long`에서는 그 가정이 참이고, `Float`·`Double`에서만 비유한 값 세
종류에서 깨진다.

**같은 클래스가 이미 인정한 선례.** `Character` 분기(`:229-231`)는 `toString()`을
그대로 쓰지 않고 `escape(char)`(`:253-260`)를 거친다. 이스케이프가 필요한 문자와 ISO
제어 문자는 `toString()`이 유효한 문자 리터럴 본문이 아니기 때문이다. 즉 "toString이 곧
리터럴은 아니다"라는 인식은 이 클래스 안에 이미 있었고, 부동소수점 분기만 그 검사를
갖지 않았다.

**`$T`를 쓰는 관례.** 값을 이름 있는 상수로 가리키는 표현 수단은 같은 파일에 이미
있다. `EnumDelegate`가 `"$T.$L"`로 열거 상수를, `ClassDelegate`가 `"$T.class"`를,
`CharsetDelegate`가 `"$T.forName($S)"`를 만든다. 수정이 새 개념을 도입하지 않는다는
근거다.

**기존 테스트가 고정하는 유한 경로.** `ValueCodeGeneratorTests.PrimitiveTests`의
`generateWhenFloat`가 `0.1F`를, `generateWhenDouble`이 `(double) 0.2`를 고정한다.
수정이 유한 값 경로를 건드리지 않았다는 주장은 이 두 건으로 실증된다.

## 5. 수정안

변경 지점은 `ValueCodeGeneratorDelegates.java`의 `Float`·`Double` 두 분기다.

before (머지베이스 기준 `:223-228`):

```java
			if (value instanceof Float) {
				return CodeBlock.of("$LF", value);
			}
			if (value instanceof Double) {
				return CodeBlock.of("(double) $L", value);
			}
```

after (`refs/pr/36965` `:223-246`, `Float` 쪽만 인용):

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
```

`Double` 분기(`:235-246`)도 같은 형태이며 폴백만 `"(double) $L"`이다.

왜 이 위치인가. 세 가지 이유다. 첫째, 결함은 타입 판별이 아니라 **같은 타입 안의 값
분류**에서 오므로 판별은 그 타입 분기 안에 있어야 한다. 둘째, 특수값 검사는 반드시
폴백 `return`보다 **위**에 와야 한다 — `if` 분기는 첫 매치에서 반환하므로, 폴백이 위에
있으면 NaN도 거기 먼저 걸려 특수값 분기에 도달조차 못 한다. 셋째, 위임자 바깥(진입점)에
검증을 두는 방식은 "생성된 코드가 유효한가"를 문자열로 판정해야 해서 실현 수단이 없다.

세부 선택 넷. (1) NaN만 `isNaN()`이고 무한대는 `==`인 것은 IEEE 754 명세의 직접적
귀결이다 — NaN은 자기 자신과도 같지 않아 `==`로 절대 걸리지 않고, 무한대는 자기 자신과
같아 `==`로 부호까지 분기할 수 있다. (2) `instanceof Float floatValue` 패턴 변수는 값을
세 번 검사해야 해서 필요하다(`value`의 정적 타입이 `Object`). 같은 메서드의
`instanceof Character character`(`:229`)가 이미 쓰던 관용구다. (3) `$L`로 `"Float.NaN"`
문자열을 직접 찍는 대신 `$T`를 쓴 것은 import 안전 때문이다. (4) 유한 값 폴백은 손대지
않았다.

검토된 대안과 기각 이유는 셋이다. **(A) `$L`로 `"Float.NaN"` 리터럴 문자열 방출** —
테스트 기대값이 짧아지고 기존 `$L` 관례와 일관되지만, 생성 파일에 같은 단순 이름의 다른
타입이 있을 때 충돌한다. import 관리는 `$T`의 존재 이유이므로 기각. **(B)
`floatLiteral`/`doubleLiteral` private 헬퍼 추출** — `Float`와 `Double` 두 블록의 구조가
같아 중복이 보이지만, 타입별 상수와 판별 함수가 달라 제네릭으로 합쳐지지 않고 분기
수도 줄지 않는다. diff만 커져 기각. **(C) 특수값에서 예외를 던져 조기 실패시키기** —
값 자체는 정당한 `float`이고 소스로 표현할 수단(상수 필드 참조)이 실제로 존재하므로,
표현 가능한 값을 거부하는 것은 후퇴다. 기각.

테스트는 `ValueCodeGeneratorTests.PrimitiveTests`에 여섯 건이 추가되었다. `Float`와
`Double` 각각의 NaN·양의 무한대·음의 무한대를 덮는 곱집합이며, 부호가 다른 두 무한대를
따로 두는 이유는 한쪽 분기만 넣거나 부호를 뒤바꾸는 회귀가 실제로 가능하기 때문이다.
기대값이 단순 이름이 아니라 `java.lang.Float.NaN`인 것은, `CodeBlock`을 `JavaFile`에
배치하지 않고 직접 문자열화하면 `$T`가 정규화 이름으로 나오기 때문이다. 즉 이 여섯
테스트가 고정하는 것은 "어떤 타입의 어떤 상수를 참조하는가"이지 "짧은 이름으로 찍히는가"가
아니다.

## 6. 범위 밖과 인접 영향

**같은 패턴의 다른 위치.** `$L`로 숫자를 찍는 자리를 트리 전체에서 찾으면
`ValueCodeGeneratorDelegates.java`의 `:212`(`"$L"`, Boolean/Integer), `:215`(byte),
`:218`(short), `:221`(`"$LL"`, Long), 그리고 이번에 고친 두 곳뿐이다. 앞의 네 개는
정수 타입이라 `toString()`이 언제나 유효한 리터럴이며 특수값이 없다. `Boolean`도
`"true"`/`"false"`로 안전하다. 즉 같은 결함 클래스는 부동소수점 두 분기에만 존재한다.

**하위 호환.** 유한한 값의 출력은 문자 하나 달라지지 않는다. `-0.0`처럼 특이해 보이는
값도 `toString()`이 `"-0.0"`이라 기존 경로에서 이미 유효하고, 지수 표기(`1.4E-45`)도
마찬가지다. 비유한 값 경로는 수정 전에 **컴파일 가능한 출력을 낸 적이 없으므로**
바뀌는 것은 실패에서 성공으로의 이동뿐이다. 계약 표면(공개 API 시그니처, `Delegate`
인터페이스)에는 변화가 없다.

**검증의 한계.** 추가된 여섯 테스트는 생성된 문자열을 비교할 뿐 javac를 돌려 컴파일
가능성을 확인하지는 않는다. `java.lang.Float.NaN`이 유효한 상수 참조라는 것은 언어 명세
수준에서 자명하고 기존 `PrimitiveTests`도 전부 문자열 비교 방식이지만, "생성물이
컴파일된다"는 최종 주장 자체를 테스트가 직접 재현하지는 않는다.

**인접하지만 이번에 건드리지 않은 것.** (1) `BigDecimal`·`BigInteger` 등은 어느
위임자도 지원하지 않아 `UnsupportedTypeValueCodeGenerationException`으로 떨어진다 —
시끄러운 실패이므로 이 결함과 성격이 다르다. (2) 채택된 `CodeBlock`이 유효한 Java 식인지
진입점이 확인하지 않는다는 구조적 공백 — 이 PR은 한 위임자의 출력을 고칠 뿐 그 공백은
남긴다. 다른 위임자에도 같은 질문을 던져 볼 수 있으나 범위 밖이다.
