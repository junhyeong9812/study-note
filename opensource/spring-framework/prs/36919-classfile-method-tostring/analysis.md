# PR #36919 분석 — ClassFileMethodMetadata의 파라미터 타입 이름 렌더링 결함

> 기준: PR 머지베이스 `0c60266986197a191ff33eb498ebc8bac3dc933f` 대비 `refs/pr/36919`.
>
> 이 문서는 결함의 경로 추적과 계약 분석에 집중한다.\
> 배경과 교훈은 README.md, 무대의 소유 관계도와 멀티 릴리스 구조는 structure.md, 테스트 한 건의 해설은 tests.md가 각각 맡는다.

## 0. 결론

JDK 24 전용 소스셋의 `ClassFileMethodMetadata.Source#toString()`은 한 문자열 안에서 타입 이름을 두 규칙으로 만든다.\
반환 타입은 공용 헬퍼 `resolveTypeName`을 거친다(`:191`).\
파라미터만 인라인 표현식 `desc.packageName() + "." + desc.displayName()`을 쓴다(`:198`).\
`ClassDesc.packageName()`은 원시 타입·배열·디폴트 패키지 타입에서 빈 문자열을 돌려준다.\
그래서 이 셋은 선행 점이 붙은 이름(`.int`, `.String[]`)이 되고, 배열은 패키지까지 잃는다.

> **슬롯(slot)** — 한 문자열 안에서 한 종류의 값이 들어가는 자리.\
> 예: `public void Foo.bar(int)`에는 접근자·반환 타입·이름·파라미터 목록이라는 네 슬롯이 있다.

> **`ClassDesc`** — JDK의 ClassFile API가 타입 하나를 가리킬 때 쓰는 기술자 객체.\
> 예: `int`, `String[]`, `java.lang.String`이 각각 하나의 `ClassDesc`다.

수정은 그 인라인 표현식을 반환 타입 슬롯이 이미 쓰고 있는 메서드 참조 `ClassFileAnnotationMetadata::resolveTypeName`으로 바꾸는 한 줄이다.

PR은 2026-09-03 머지됐다(ad83d5ebd9e + polish 6316c06a977 — 전용 테스트 파일을 공유 스위트로 통합, README 7절 참조).\
제출 후 머지 전까지 라벨은 `status: waiting-for-triage`와 `in: core`, 리뷰 코멘트는 0건이다.\
생성일은 2026-06-14이다.

## 1. 무대

결함 클래스와 그것이 재사용해야 했던 헬퍼, 그리고 값을 맞춰야 할 대응 구현을 먼저 좌표로 고정한다.

- 모듈: `spring-core`, 소스셋 `src/main/java24`(멀티 릴리스 JAR의 JDK 24 이상 전용 층),
  패키지 `org.springframework.core.type.classreading`.
- 결함 클래스: `spring-core/src/main/java24/org/springframework/core/type/classreading/ClassFileMethodMetadata.java`
  (`final class ClassFileMethodMetadata implements MethodMetadata`, `:45`) 안의
  중첩 레코드 `Source`(`:168`).
- 공용 헬퍼: `ClassFileAnnotationMetadata.resolveTypeName(ClassDesc)`
  (`ClassFileAnnotationMetadata.java:225-235`).
- 대응 구현(ASM 변형): `src/main/java`의
  `SimpleMethodMetadataReadingVisitor.Source#toString()`(`:145-186`).

> **멀티 릴리스 JAR(multi-release JAR)** — 하나의 jar 안에 자바 버전별 구현을 따로 넣어 두고, 실행 중인 JDK 버전이 알아서 고르게 하는 포장 방식.\
> 예: JDK 24 이상이면 `src/main/java24`의 ClassFile 구현이, 그 아래면 `src/main/java`의 ASM 구현이 쓰인다.

공개 진입 API는 `org.springframework.core.type.MethodMetadata`를 통한 `toString()`이다.\
`ClassFileMethodMetadata.toString()`(`:137`)은 `Source`에 그대로 위임한다(`:138`).

누가 언제 부르는가.\
이 문자열은 **로직이 소비하는 값이 아니라 사람이 읽는 진단 값**이다.\
`Source`는 동시에 `MergedAnnotation`의 source로 쓰이므로(`:150`), 애노테이션 처리 오류 메시지에 그대로 박힌다.\
대표 소비처는 `AnnotationTypeMapping`의 `@AliasFor` 미러 검증(`" declared on " + source`)이다.\
반면 `MethodMetadata`를 실제로 쓰는 프레임워크 코드(`ConfigurationClassParser.retrieveBeanMethodMetadata`, `AutowiredAnnotationBeanPostProcessor`)는 구조화된 접근자만 쓰고 `toString()`을 파싱하지 않는다.\
즉 손상 반경은 진단 문자열 한 줄로 한정된다.

> **손상 반경(blast radius)** — 결함이 잘못되었을 때 그 여파가 미치는 범위.\
> 예: 여기서는 오류 메시지 한 줄의 가독성까지이고, 빈 생성이나 주입 판정에는 닿지 않는다.

## 2. 전체 메서드 그래프

메타데이터가 만들어지는 경로와, 그 뒤 문자열이 계산되는 경로를 나눠 둔다.

```text
[생성 경로: JDK 24 이상에서 컴포넌트 스캔 / @Configuration 파싱]
  MetadataReaderFactory.create(resourceLoader) -> MetadataReaderFactoryDelegate.create(...)
      -> ClassFileMetadataReaderFactory.getMetadataReader(className)
      -> new ClassFileMetadataReader(...)  ClassFile.of().parse(bytes)
      -> ClassFileAnnotationMetadata.of(classModel, classLoader)
           +-- MethodModel 마다 Builder.method(method)
                 -> ClassFileMethodMetadata.of(methodModel, classLoader)   ClassFileMethodMetadata.java:142
                      +-- methodName / flags / declaringClassName                 :143-147
                      +-- returnTypeName = resolveTypeName(methodTypeSymbol().returnType())  :148-149  <== 헬퍼 경유
                      +-- source = new Source(declaringClassName, flags, methodName,
                      |                       methodModel.methodTypeSymbol())     :150
                      +-- mergedAnnotations = ...                                 :151-156

[출력 경로: 누군가 toString()을 부를 때 계산된다]
  MethodMetadata.toString()
      -> ClassFileMethodMetadata.toString()                                       :137
      -> Source.toString()                                                        :184
           +-- flags.flags() 를 소문자로 나열                                      :187-190
           +-- ClassFileAnnotationMetadata.resolveTypeName(descriptor.returnType())  :191
           |        resolveTypeName(ClassDesc)          ClassFileAnnotationMetadata.java:225
           |          isPrimitive() -> displayName()                              :226-228
           |          while (isArray()) effectiveType = componentType()           :229-232
           |          packageName = effectiveType.packageName()                   :233
           |          return packageName.isEmpty() ? type.displayName()
           |                                       : packageName + "." + type.displayName()  :234
           +-- declaringClassName + '.' + methodName                              :193-195
           +-- '(' + Stream.of(descriptor.parameterArray())
           |          .map( ??? )   <== 결함 지점                                  :197-199
           |          .collect(joining(","))
           +-- ')'                                                                :200

[대조군: 같은 값을 내야 하는 ASM 변형]  SimpleMethodMetadataReadingVisitor.Source.toString() :145
      Type.getReturnType(...).getClassName() :168 과 argumentTypes[i].getClassName() :179
      -- 반환과 파라미터가 같은 함수 Type#getClassName 하나만 쓴다
```

데이터 흐름의 요점은 두 가지다.\
첫째, `Source`가 들고 있는 것은 렌더링된 문자열이 아니라 `MethodTypeDesc descriptor` 원본이며, 문자열은 호출 시마다 새로 계산된다(ASM 변형은 `toStringValue` 캐시를 둔다).\
둘째, `returnTypeName` 필드(`:53`)와 `Source.toString()`의 반환 타입 슬롯(`:191`)은 **서로 다른 계산 경로**이지만 둘 다 헬퍼를 쓴다.\
헬퍼를 안 쓰는 자리는 파라미터 슬롯 하나뿐이다.

한 문자열이 네 슬롯으로 조립되는 모습과, 그중 어디가 헬퍼를 거치는지를 따로 그려 둔다.

```text
 Source.toString() 이 조립하는 네 칸
 +-----------+----------------+----------------------+---------------------+
 | 접근자     | 반환 타입       | 선언클래스.메서드명    | (파라미터 목록)       |
 | :187-190  | :191           | :193-195             | :196-200            |
 +-----------+----------------+----------------------+---------------------+
                     |                                        |
                     v                                        v
          resolveTypeName(...)                    desc.packageName()
          (원시/배열/빈패키지 분기 있음)             + "." + desc.displayName()
                     |                                        |
                     v                                        v
                 "void"                              ".int" , ".String[]"
                 맞는 값                                깨진 값  [!]

 같은 문자열 안에서 규칙이 둘로 갈린 자리가 오른쪽 한 칸뿐이다.
```

## 2.5 핵심 이름표 사전

이 흐름에서 "이름"은 네 층위로 존재한다.\
JVM 디스크립터 문자열, `ClassDesc`가 주는 짧은 표시 이름, 패키지, 그리고 둘을 합친 정규 이름이다.\
아래는 등장하는 식별자 전부에 대한 역할과 이 결함과의 관계다.

> **정규 이름(fully qualified name)** — 패키지까지 포함한 타입의 온전한 이름.\
> 예: `String`은 짧은 표시 이름이고, `java.lang.String`이 정규 이름이다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `ClassFileMethodMetadata.toString()` (:137) | 공개 표면. `Source`에 위임 | -> `String` | 진단 메시지 조립, 로깅, 테스트 단언 | 결함이 밖으로 새어 나가는 유일한 출구 |
| `source` 필드 (:56) | `equals`/`hashCode`/`toString`을 대신 구현하는 위임처. 동시에 `MergedAnnotation`의 source | `Object`(실제 타입은 `Source`) | `of()`에서 주입(:150) | 이 문자열이 애노테이션 오류 메시지에 실리는 이유 |
| `record Source(...)` (:168) | 선언 클래스명 + 접근 플래그 + 메서드명 + 디스크립터를 묶은 값 객체 | -- | `of()`가 생성 | 결함이 있는 `toString()`의 소유자 |
| `Source.descriptor` (`MethodTypeDesc`) | 메서드 시그니처 원본. 반환·파라미터 타입의 출처 | -- | `toString`, `equals`, `hashCode` | 렌더링의 입력. 값 자체는 정확하다 |
| `Source.flags` (`AccessFlags`) | 접근 제어자 비트 | -> `flags()` 집합 | `toString` :187-190 | 무관. 소문자 나열로 정상 출력 |
| `Source.declaringClassName` / `methodName` | 선언 클래스와 메서드 이름 | -- | `toString` :193-195 | 무관 |
| `Source.equals` / `hashCode` (:170, :179) | 동일성 판정 | `descriptor.descriptorString()` 기준 | `MethodMetadata` 비교 시 | **`toString()`을 쓰지 않는다.** 결함이 동일성에 번지지 않는 근거 |
| `descriptor.returnType()` | 반환 타입 하나 | -> `ClassDesc` | `Source.toString` :191, `of()` :148 | 헬퍼를 거치는 정상 슬롯 |
| `descriptor.parameterArray()` | 파라미터 타입 배열 | -> `ClassDesc[]` | `Source.toString` :197 | 결함 슬롯의 입력 |
| `desc` (:198 람다 파라미터) | 파라미터 하나의 `ClassDesc` | -- | 파라미터마다 | 잘못된 표현식이 적용되는 대상 |
| `ClassDesc.packageName()` | 타입의 패키지 | -> `String` (원시·배열·디폴트 패키지는 `""`) | :198, `resolveTypeName` :233 | **빈 문자열이 결함의 직접 원인.** 배열은 원소의 패키지를 물려받지 않는다 |
| `ClassDesc.displayName()` | 사람이 읽는 짧은 이름 (`int`, `String[]`) | -> `String` | :198, `resolveTypeName` :227/:234 | 결함 시 여기에 `"."`가 앞에 붙는다 |
| `ClassDesc.isPrimitive()` | 원시 타입인가 | -> `boolean` | `resolveTypeName` :226 | 결함 슬롯에는 이 판정이 없다 |
| `ClassDesc.isArray()` / `componentType()` | 배열 여부 / 원소 타입 | -> `boolean` / `ClassDesc` | `resolveTypeName` :230-231 | 배열 패키지 소실을 막는 장치. 결함 슬롯에는 없다 |
| `resolveTypeName(ClassDesc)` (ClassFileAnnotationMetadata.java:225) | 세 갈래 분기를 담은 공용 이름 해석기 | `ClassDesc` -> 정규 이름 | `of()` :149, `Source.toString` :191, (수정 후) :198 | 수정이 재사용하는 함수. 새로 만든 규칙이 아니다 |
| `effectiveType` (:229 지역변수) | 배열을 다 벗겨낸 원소 타입 | -- | `resolveTypeName` 내부 | 패키지를 어디서 가져올지 정한다 |
| `packageName` (:233 지역변수) | `effectiveType`의 패키지 | -- | `resolveTypeName` 내부 | 비면 `displayName()`만 쓰는 방어 분기 |
| `returnTypeName` 필드 (:53) | `getReturnTypeName()`이 돌려주는 계약 값 | -- | `of()` :149에서 헬퍼로 계산 | `toString()`과 별개 경로. 결함의 영향을 받지 않는다 |
| `Type#getClassName()` (ASM 변형 :168, :179) | ASM에서 원시·배열·참조를 모두 정규 이름으로 내는 함수 | -> `String` | ASM `Source.toString` | 두 구현이 맞춰야 할 **목표값**의 정의 |
| `toStringValue` (ASM 변형 :146) | ASM 쪽 문자열 캐시 | -- | ASM `toString` | 무관. 두 구현의 사소한 구조 차이 |

## 3. 결함 경로 단계 추적

`void sample(int number, String[] values)`를 입력으로, 파라미터 슬롯의 두 칸을 단계별로 따라간다.\
비교 축은 "수정 전 인라인 표현식"과 "수정 후 헬퍼"다.

| 단계 | 파라미터 1 `int` | 파라미터 2 `String[]` | 참고: 파라미터 `java.lang.String` |
|---|---|---|---|
| 입력 `ClassDesc` | `int` | `String[]` | `String` |
| `isPrimitive()` | true | false | false |
| `isArray()` | false | true | false |
| `packageName()` | `""` | `""` | `"java.lang"` |
| `displayName()` | `"int"` | `"String[]"` | `"String"` |
| 수정 전 `:198` 결과 | `"" + "." + "int"` = `.int` | `"" + "." + "String[]"` = `.String[]` | `java.lang.String` (우연히 정답) |
| 수정 후 `resolveTypeName` 진행 | `:226` 참 -> `displayName()` | `:230` 루프로 `effectiveType = String`, `packageName = "java.lang"` | `:233` 비지 않음 |
| 수정 후 결과 | `int` | `java.lang` + `.` + `String[]` = `java.lang.String[]` | `java.lang.String` (동일) |
| ASM 변형의 값 | `int` | `java.lang.String[]` | `java.lang.String` |

같은 메서드의 반환 타입 슬롯(`:191`)은 수정 전에도 헬퍼를 거치므로 `void`가 정확히 `void`로 나온다.\
그래서 전체 문자열은 한 줄 안에서 앞은 맞고 괄호 안만 깨지는 모습이 된다.

같은 입력 하나가 수정 전후에 어떤 최종 문자열이 되는지를 같은 칸 폭으로 놓으면 이렇다.

```text
 입력: void sample(int number, String[] values)

 수정 전                                        수정 후
 +----------------------------------+          +----------------------------------+
 | public void ...WithMethod.sample |          | public void ...WithMethod.sample |
 |   ( .int , .String[] )           |          |   ( int , java.lang.String[] )   |
 +----------------------------------+          +----------------------------------+
   int      -> .int      점이 붙음               int      -> int       그대로
   String[] -> .String[] 패키지 소실  [!]        String[] -> java.lang.String[]

 참고: 패키지 있는 참조 타입은 양쪽이 같다
 +----------------------------------+          +----------------------------------+
 | ...test( java.lang.String )      |          | ...test( java.lang.String )      |
 +----------------------------------+          +----------------------------------+
   -> 기존 테스트가 이 칸만 재고 있었기 때문에 결함이 통과했다.
```

배열 칸이 특히 나쁘다.\
점이 하나 더 붙는 데 그치지 않고 **패키지가 통째로 사라진다.**\
동명의 클래스가 여러 패키지에 있을 때 메시지만으로는 어느 것인지 특정할 수 없다.\
같은 이유로 디폴트 패키지 클래스도 `.Foo`가 되지만, 이 경우는 원래 패키지가 없으므로 잃는 정보는 없고 선행 점만 남는다.

> **디폴트 패키지(default package)** — `package` 선언 없이 만든 클래스가 들어가는 이름 없는 패키지.\
> 예: `class Foo {}`만 있는 파일의 `Foo`는 패키지가 `""`라서 `packageName()`이 빈 문자열이다.

## 4. 계약

**구현 간 동치.**\
이 소스셋 구조가 요구하는 첫 번째 계약은 ASM 변형과 ClassFile 변형이 같은 값을 내야 한다는 것이다.\
두 클래스는 이름과 패키지가 같고, 멀티 릴리스 JAR 규칙에 따라 런타임 JDK 버전이 구현을 고르므로 호출자는 어느 쪽인지 모른다.\
값이 갈리면 같은 애플리케이션이 JDK 버전에 따라 다른 문자열을 낸다.\
§3 표의 마지막 행이 목표값이다.

**기존 공유 테스트가 고정하는 것.**\
`spring-core/src/test/java/org/springframework/core/type/AbstractMethodMetadataTests.java`의 `verifyToString()`(`:78-104`)이 여덟 개의 문자열을 등호로 고정한다.\
이 파일은 ASM과 ClassFile 두 리더가 함께 상속하는 공유 테스트이므로, 한 벌의 단언이 두 구현을 동시에 잰다.\
그중 파라미터가 있는 단언은 둘이다.

```java
		assertThat(getTagged(WithMethodWithOneArgument.class).toString())
				.isEqualTo("public java.lang.String " + WithMethodWithOneArgument.class.getName() + ".test(java.lang.String)");

		assertThat(getTagged(WithMethodWithTwoArguments.class).toString())
				.isEqualTo("public java.lang.String " + WithMethodWithTwoArguments.class.getName() + ".test(java.lang.String,java.lang.Integer)");
```

두 단언의 파라미터는 전부 패키지가 있는 참조 타입이라 수정 전에도 통과했다.\
원시 배열·문자열 배열·2차원 배열을 검증하는 나머지 여섯 단언(`:93-103`)은 모두 **반환 타입** 축이고, 그 픽스처들의 `test()`는 인자가 없다.\
즉 "원시/배열"과 "반환/파라미터"라는 두 축의 곱집합에서 파라미터 쪽 두 칸이 비어 있었고, 결함이 정확히 그 칸에 있었다.

그 곱집합을 격자로 그리면 빈칸이 어디였는지가 한눈에 보인다.

```text
                 |  반환 타입 슬롯      |  파라미터 슬롯
 ----------------+---------------------+--------------------------
  참조 타입       |  단언 있음 (green)   |  단언 있음 (green)
  (java.lang.String) |                 |  -> 우연히 값이 맞아 통과
 ----------------+---------------------+--------------------------
  원시 타입       |  단언 있음 (green)   |  단언 없음  [빈칸]
  (int)          |  gh-36577 이 채움    |  -> 결함이 여기 숨었다
 ----------------+---------------------+--------------------------
  배열           |  단언 있음 (green)   |  단언 없음  [빈칸]
  (String[])     |  gh-36577 이 채움    |  -> 패키지 소실이 여기 숨었다
 ----------------+---------------------+--------------------------

 이 PR 의 새 테스트가 아래 두 빈칸을 채운다.
```

**헬퍼 도입 커밋이 세운 규칙.**\
`resolveTypeName`은 커밋 `b01fdb01408`("Fix ClassFileMethodMetadata return type names for primitives and arrays", gh-36577)이 반환 타입의 같은 결함을 고치면서 도입한 함수다.\
그 커밋이 확립한 규칙은 "`ClassDesc`를 사람이 읽는 타입 이름으로 바꾸는 일은 이 함수 하나가 한다"이다.\
파라미터 슬롯은 그 규칙 밖에 남아 있었다.

**결함이 어기지 않는 것.**\
`Source.equals`/`hashCode`(`:170`, `:179`)는 `descriptor.descriptorString()`을 쓴다.\
`getReturnTypeName()`(`:83`)이 돌려주는 값은 `of()`(`:149`)에서 따로 계산된다.\
두 계약은 결함의 영향을 받지 않는다.\
이것이 이 PR의 stakes를 낮게 유지하는 근거다.

## 5. 수정안

변경 지점은 `ClassFileMethodMetadata.java:198` 한 줄이다.

before (머지베이스 기준 `:196-200`):

```java
			builder.append('(');
			builder.append(Stream.of(this.descriptor.parameterArray())
					.map(desc -> desc.packageName() + "." + desc.displayName())
					.collect(Collectors.joining(",")));
			builder.append(')');
```

after (`refs/pr/36919`의 같은 자리):

```java
			builder.append(Stream.of(this.descriptor.parameterArray())
					.map(ClassFileAnnotationMetadata::resolveTypeName)
					.collect(Collectors.joining(",")));
```

왜 이 위치인가.\
결함은 `ClassDesc`가 주는 값에도, `resolveTypeName`의 규칙에도 없다.\
`packageName()`이 배열과 원시 타입에서 빈 문자열을 돌려주는 것은 JVM의 관점을 그대로 반영한 정상 동작이고, 헬퍼는 그 성질을 이미 정확히 다룬다.\
어긋난 것은 **같은 문자열 안의 두 슬롯이 서로 다른 규칙을 쓴다**는 사실뿐이다.\
그러므로 규칙이 없는 쪽을 있는 쪽에 맞추는 것이 최소이자 유일하게 일관된 수정이다.

검토된 대안과 기각 이유는 셋이다.

첫째, `Source` 안에 파라미터용 분기를 직접 다시 쓰는 방향.\
`isPrimitive`/`isArray` 판정을 람다 안에 펼치면 같은 규칙이 두 곳에 존재하게 된다.\
gh-36577이 규칙을 한 곳으로 모아 둔 결정을 되돌리는 셈이다.

둘째, `descriptor.descriptorString()`을 파싱해 이름을 만드는 방향.\
이미 구조화된 `ClassDesc` 배열이 있는데 문자열로 되돌아가는 것이라, 규칙 통일이라는 목표에서 더 멀어진다.

셋째, ASM 쪽처럼 `Type#getClassName`을 쓰는 방향.\
java24 소스셋은 ASM에 의존하지 않는 것이 존재 이유이므로 성립하지 않는다.

테스트는 `src/test/java24`에 `ClassFileMethodMetadataToStringTests` 한 건이 추가되었다.\
픽스처 `WithMethod.sample(int number, String[] values)`는 §3 표에서 깨지던 두 칸을 정확히 겨냥한다.\
단언은 `endsWith(".sample(int,java.lang.String[])")`로 검증 표면을 괄호 안으로 좁혔다.\
배치에 대해서는 한 가지 물음이 남는다.\
gh-36577의 최종 커밋은 오히려 ClassFile 전용 테스트를 지우고 검증을 공유 테스트로 옮기는 방향이었다.\
그러므로 이 픽스처를 `AbstractMethodMetadataTests.verifyToString()`에 파라미터 케이스로 추가했다면, 두 구현의 정렬까지 한 벌의 단언으로 고정됐을 것이다.

> **픽스처(fixture)** — 테스트가 재려는 상황을 만들기 위해 미리 준비해 두는 대상 클래스나 데이터.\
> 예: 여기서는 `sample(int number, String[] values)` 메서드 하나를 가진 `WithMethod` 클래스가 픽스처다.

## 6. 범위 밖과 인접 영향

**같은 패턴의 다른 위치.**\
`packageName() +` 형태의 인라인 결합을 트리 전체에서 찾으면 두 곳이 나온다.\
하나는 이 결함 자리(`ClassFileMethodMetadata.java:198`)다.\
다른 하나는 `spring-core/src/main/java/org/springframework/aot/generate/GeneratedFiles.java:52`의 `javaFile.packageName() + "." + javaFile.typeSpec().name()`이다.\
후자는 표면상 같은 형태지만, 바로 앞 줄(`:51`)의 `validatePackage(...)`가 빈 패키지를 먼저 `IllegalArgumentException`으로 거부한다(`:194-200`).\
빈 문자열이 결합에 도달하지 않으므로 같은 결함이 아니다.

**하위 호환.**\
바뀌는 것은 원시 타입·배열·디폴트 패키지 파라미터의 렌더링뿐이고, 패키지가 있는 참조 타입은 수정 전후 값이 같다(§3 표의 셋째 열).\
공유 테스트 `verifyToString()`의 여덟 단언은 전부 그대로 통과해야 하며, 그것이 이 변경의 양성 가드다.\
이 문자열을 읽어 분기하는 프레임워크 로직이 없으므로 계약 표면 변화도 없다.

> **양성 가드(positive guard)** — 수정 전후 모두 통과해야 하는 단언. 고치는 김에 다른 것이 깨지지 않았음을 지킨다.\
> 예: `test(java.lang.String)` 단언은 결함과 무관하지만, 수정이 참조 타입 렌더링을 망가뜨리지 않았는지를 잰다.

**실행 조건.**\
새 테스트는 `src/test/java24`에 있어 `java24Test` 태스크에서만 컴파일·실행된다.\
`spring-core.gradle`의 `multiRelease { releaseVersions 21, 24 }` 선언이 그 소스셋을 등록한다.\
JDK 24 미만 환경에서는 이 테스트가 아예 존재하지 않으므로, 로컬 검증에는 JDK 24 이상 toolchain이 필요하다.

**인접하지만 이번에 건드리지 않은 것.**

- (1) 접근 제어자 출력 순서.\
  ASM은 `public/protected/private/abstract/static/final` 순서를 코드로 고정한다(`:149-166`).\
  ClassFile은 `flags.flags()` 집합의 순회 순서를 그대로 따른다(`:187-190`).\
  두 순서가 항상 일치하는지는 미확인이며 범위 밖이다.
- (2) ASM 쪽 `toStringValue` 캐시가 ClassFile 쪽에는 없다는 구조 차이.\
  값에는 영향이 없다.
- (3) 테스트를 공유 테스트로 옮기는 배치 변경.\
  리뷰에서 제안될 수 있는 항목으로 남겨 둔다.
