# PR #36919 — Render parameter type names in ClassFileMethodMetadata

## 0. 정향

이 문서는 JDK 24 이상에서만 쓰이는 메타데이터 리더의 진단 문자열 한 줄을 고친 PR의 해설이다.\
고친 곳은 `ClassFileMethodMetadata.Source#toString()`의 파라미터 렌더링 한 줄이고, 고친 방법은 이미 같은 파일이 반환 타입에 쓰고 있던 헬퍼를 파라미터에도 쓰게 한 것이다.\
배경에는 Spring 7.0이 ASM 대신 JDK의 `java.lang.classfile` API로 바이트코드를 읽는 두 번째 경로를 갖게 되었다는 사실이 있다.

> **진단 문자열(diagnostic string)** — 로직이 읽고 분기하는 값이 아니라, 사람이 오류를 조사할 때만 읽는 문자열.\
> 예: 예외 메시지에 그대로 실리는 `public void com.example.Foo.sample(int)` 같은 메서드 표기.

> **`java.lang.classfile`** — JDK 24가 표준화한, 클래스 파일(바이트코드)을 읽고 쓰는 JDK 내장 API.\
> 예: 외부 라이브러리 없이 `ClassFile.of().parse(bytes)`만으로 클래스의 메서드 목록을 얻을 수 있다.

> **ASM** — 자바 생태계가 오랫동안 써 온 외부 바이트코드 조작 라이브러리.\
> 예: Spring은 JDK 24 이전까지 "클래스를 로드하지 않고 애노테이션만 읽는" 일을 전부 ASM으로 했다.

## 1. 배경 — 두 개의 메타데이터 리더

Spring은 클래스를 로드하지 않고 바이트코드만 읽어 애노테이션과 메서드 정보를 얻는다.\
컴포넌트 스캐닝이 후보 클래스 수천 개를 훑을 때 전부 `Class.forName`으로 로드하면 클래스로더가 오염되고 초기화 부작용이 생기기 때문이다.\
이 역할을 하는 것이 `MetadataReader`이고, 오랫동안 구현은 ASM 하나였다.

> **컴포넌트 스캐닝(component scanning)** — 패키지 아래 클래스를 전부 훑어 `@Component` 류가 붙은 것을 빈 후보로 골라내는 기동 단계.\
> 예: `@ComponentScan("com.example")` 한 줄이 그 패키지의 클래스 수천 개를 후보로 훑는다.

> **`MetadataReader`** — 클래스 하나의 바이트코드를 읽어 애노테이션·메서드 정보를 돌려주는 Spring의 추상.\
> 예: 스캐닝은 이 추상만 보고 일하므로, 그 뒤가 ASM인지 ClassFile인지 알 필요가 없다.

Spring 7.0부터 구현이 둘이 되었다.\
JDK 24가 `java.lang.classfile`을 표준화하면서 외부 라이브러리 없이 바이트코드를 파싱할 수 있게 되었고, Spring은 이를 위해 멀티 릴리스 소스셋을 도입했다.\
선택은 `MetadataReaderFactoryDelegate`가 하는데, 이 클래스는 같은 이름으로 두 번 존재한다.\
`src/main/java`의 것은 ASM 기반을 만들고, `src/main/java24`의 것은 ClassFile 기반을 만든다.

```java
abstract class MetadataReaderFactoryDelegate {

	static MetadataReaderFactory create(@Nullable ResourceLoader resourceLoader) {
		return new ClassFileMetadataReaderFactory(resourceLoader);
	}
```

어느 구현이 뽑히는지를 세로로 놓으면 이렇다. 왼쪽이 단계, 오른쪽이 그 단계가 정하는 것이다.

```text
컴포넌트 스캐닝이 클래스 하나를 훑는다          어떤 클래스의 메타데이터가 필요한가
        |
        v
MetadataReaderFactory.create(resourceLoader)   팩터리를 만들어 달라
        |
        v
MetadataReaderFactoryDelegate.create(...)      같은 이름의 클래스가 두 벌 있다
        |
        +--> src/main/java    (JDK 24 미만)    SimpleMetadataReaderFactory  = ASM
        |
        +--> src/main/java24  (JDK 24 이상)    ClassFileMetadataReaderFactory
        |                                        = java.lang.classfile   <- 이 PR의 무대
        v
둘 다 MethodMetadata 를 돌려준다               호출자는 어느 쪽이 왔는지 모른다
```

`spring-core.gradle`의 `multiRelease { releaseVersions 21, 24 }` 선언이 이 소스셋을 등록하고, 빌드 플러그인이 `src/main/java24`를 `java24` 소스셋으로, `src/test/java24`를 `java24Test` 소스셋과 동명의 테스트 태스크로 만든다.\
런타임에는 멀티 릴리스 JAR의 규칙에 따라 JDK 24 이상에서 `java24` 쪽 클래스가 우선한다.

> **멀티 릴리스 JAR(multi-release JAR)** — 같은 JAR 안에 JDK 버전별 클래스를 따로 담아 두고, 실행 중인 JDK가 자기 버전에 맞는 것을 고르게 하는 JAR 규격.\
> 예: 이름이 같은 `MetadataReaderFactoryDelegate`가 두 벌 들어 있고, JDK 24 이상에서만 `java24` 쪽이 이긴다.

> **소스셋(source set)** — 빌드 도구가 따로 컴파일하는 소스 디렉터리 묶음.\
> 예: `src/main/java24`는 `java24` 소스셋이라 JDK 24 toolchain으로만 컴파일된다.

`toString()`은 이 중 어디에 쓰이나.\
`MethodMetadata`의 `toString()`은 내부 `Source` 레코드에 위임되고, 그 `Source`는 동시에 `MergedAnnotation`의 source로 쓰인다.\
즉 애노테이션 처리 중 오류가 나면 이 문자열이 사람이 읽는 메시지에 그대로 박힌다.\
`AnnotationTypeMapping`의 `@AliasFor` 검증이 대표적인 소비처다.

> **`MergedAnnotation`의 source** — 이 애노테이션 정보가 "어디서 왔는지"를 가리키는 꼬리표 객체.\
> 예: 오류 메시지의 `declared on ...` 뒤에 붙는 것이 이 source의 `toString()` 결과다.

> **`@AliasFor`** — 한 애노테이션의 두 속성을 서로의 별칭으로 선언하는 Spring 기능.\
> 예: `@RequestMapping`의 `value`와 `path`처럼, 어느 쪽에 써도 같은 값이 되어야 한다.

```java
String on = (source != null) ? " declared on " + source : "";
throw new AnnotationConfigurationException(String.format(
		"Different @AliasFor mirror values for annotation [%s]%s; attribute '%s' " +
		"and its alias '%s' are declared with values of [%s] and [%s].",
```

정리하면 이 문자열은 로직이 소비하는 값이 아니라 사람이 읽는 진단 값이다.\
그래서 버그의 손상 반경은 작지만, 반대로 값이 깨지면 오류 메시지를 보고 원인을 찾는 사람이 직접 손해를 본다.

## 2. 수정 전 동작 방식 — 반환 타입과 파라미터의 비대칭

수정 전 `Source#toString()`은 한 메서드 안에서 타입 이름을 두 가지 방식으로 만들고 있었다.\
반환 타입은 헬퍼를 거치고, 파라미터는 `ClassDesc`의 두 메서드를 직접 이어 붙였다.

```java
builder.append(ClassFileAnnotationMetadata.resolveTypeName(this.descriptor.returnType()));
builder.append(' ');
builder.append(this.declaringClassName);
builder.append('.');
builder.append(this.methodName);
builder.append('(');
builder.append(Stream.of(this.descriptor.parameterArray())
		.map(desc -> desc.packageName() + "." + desc.displayName())
		.collect(Collectors.joining(",")));
builder.append(')');
```

호출 한 번이 문자열 한 줄이 되기까지의 경로를 세로로 놓으면, 규칙이 어디서 갈라지는지가 보인다.

```text
methodMetadata.toString()                      사람이 읽을 한 줄을 요청한다
        |
        v
ClassFileMethodMetadata.toString()             자기는 아무것도 하지 않고 Source 에 넘긴다
        |
        v
Source.toString()                              네 조각을 순서대로 이어 붙인다
        |
        +--> 접근자 나열      flags 순회                    "public "
        |
        +--> 반환 타입        resolveTypeName(returnType)   "void "        <- 헬퍼 경유
        |
        +--> 선언클래스.메서드  문자열 연결                    "...WithMethod.sample"
        |
        +--> 파라미터 목록    desc.packageName()
        |                     + "." + desc.displayName()    "(.int,.String[])"
        |                                                                  <- 인라인 표현식
        v
"public void ...WithMethod.sample(.int,.String[])"     앞 세 조각은 맞고 넷째만 틀리다
```

이 비대칭은 사고가 아니라 이력의 흔적이다.\
gh-36577이 같은 클래스의 반환 타입 버그(원시 타입과 배열 이름이 깨지던 문제)를 고치면서 `resolveTypeName` 헬퍼를 도입했고, 반환 타입 슬롯만 그 헬퍼로 옮겼다.\
파라미터 슬롯은 원래 표현식 그대로 남았다.

헬퍼는 `ClassFileAnnotationMetadata`에 있고, `ClassDesc`가 무엇을 서술하느냐에 따라 세 갈래로 갈린다.

> **`ClassDesc`** — 클래스 파일에 적힌 타입 디스크립터를 감싼 불변 값 객체(`java.lang.constant` 패키지).\
> 예: `String[]` 파라미터는 `ClassDesc`로는 디스크립터 `[Ljava/lang/String;`를 감싼 객체 하나다.

> **디스크립터(descriptor)** — 타입과 시그니처를 클래스 파일이 쓰는 축약 문법으로 적은 문자열.\
> 예: `void sample(int, String[])`의 디스크립터는 `(I[Ljava/lang/String;)V`다.

> **원시 타입(primitive type)** — `int`·`long`·`void`처럼 객체가 아닌 내장 타입. 패키지 개념이 없다.\
> 예: `int`는 어떤 패키지에도 속하지 않으므로 `java.lang.int` 같은 이름이 존재하지 않는다.

```java
static String resolveTypeName(ClassDesc type) {
	if (type.isPrimitive()) {
		return type.displayName();
	}
	ClassDesc effectiveType = type;
	while (effectiveType.isArray()) {
		effectiveType = effectiveType.componentType();
	}
	String packageName = effectiveType.packageName();
	return (packageName.isEmpty() ? type.displayName() : packageName + "." + type.displayName());
}
```

핵심은 두 가지다.\
원시 타입은 패키지 개념이 없으므로 `displayName()`만 쓴다.\
배열은 `componentType()`으로 원소 타입까지 벗겨 낸 뒤 그 패키지를 붙인다.\
그래야 `java.lang.String[]`처럼 패키지는 원소에서, 대괄호는 전체 표시 이름에서 온다.

## 3. 무엇이 문제였나 — 선행 점이 붙은 파라미터

문제는 `ClassDesc.packageName()`이 원시 타입, 배열, 디폴트 패키지 타입에 대해 빈 문자열을 반환한다는 데 있다.\
빈 문자열에 `"."`를 무조건 이어 붙이면 이름이 점으로 시작한다.\
JDK 25에서 `void sample(int, String[])`의 디스크립터를 직접 풀어 보면 그대로 재현된다.

> **디폴트 패키지(default package)** — `package` 선언 없이 만든 클래스가 속하는 이름 없는 패키지.\
> 예: 최상위에 그냥 `class Foo {}`로 둔 클래스는 패키지 이름이 빈 문자열이다.

```text
displayName=int packageName=[] old=.int
displayName=String[] packageName=[] old=.String[]
```

값으로 정리하면 다음과 같다.\
왼쪽이 파라미터의 소스 타입, 가운데가 수정 전 렌더링, 오른쪽이 ASM 기반 리더가 같은 자리에서 내던 값이다.

| 파라미터 타입 | 수정 전 ClassFile 렌더링 | ASM 렌더링 |
|---|---|---|
| `int` | `.int` | `int` |
| `String[]` | `.String[]` | `java.lang.String[]` |
| `String` | `java.lang.String` | `java.lang.String` |
| `int[][]` | `.int[][]` | `int[][]` |

같은 입력을 수정 전/후로 나란히 놓으면 차이가 두 칸에서만 난다.

```text
입력: void sample(int number, String[] values)

BEFORE  --  desc.packageName() + "." + desc.displayName()
+-----------------------------------------------------+
|  int       packageName    ->  ".int"                |
|  String[]  packageName    ->  ".String[]"           |
+-----------------------------------------------------+
        public void ...WithMethod.sample(.int,.String[])

AFTER   --  ClassFileAnnotationMetadata::resolveTypeName
+-----------------------------------------------------+
|  int       isPrimitive    ->  "int"                 |
|  String[]  componentType  ->  "java.lang.String[]"  |
+-----------------------------------------------------+
        public void ...WithMethod.sample(int,java.lang.String[])
```

배열 칸은 점 하나가 더 붙는 문제가 아니라 패키지가 통째로 사라지는 문제다.

배열 사례가 특히 나쁘다.\
점이 하나 더 붙는 데 그치지 않고 패키지 자체가 사라진다.\
`java.lang.String[]`이어야 할 이름이 `.String[]`이 되므로, 오류 메시지만 보고 타입을 특정할 수 없다.

결과적으로 메서드 전체 문자열은 `public void ...WithMethod.sample(.int,.String[])`처럼 나온다.\
반환 타입 자리는 gh-36577 덕분에 이미 정상이므로, 한 줄 안에서 앞은 맞고 괄호 안만 깨져 있는 모습이 된다.

세 번째 케이스가 왜 정상인지가 이 버그가 오래 살아남은 이유를 설명한다.\
패키지가 있는 참조 타입은 `packageName()`이 비지 않으므로 문자열을 이어 붙여도 우연히 맞는 값이 나온다.\
그리고 기존 공유 테스트가 검증하던 파라미터는 전부 그런 타입이었다.

```java
assertThat(getTagged(WithMethodWithTwoArguments.class).toString())
		.isEqualTo("public java.lang.String " + WithMethodWithTwoArguments.class.getName() + ".test(java.lang.String,java.lang.Integer)");
```

같은 테스트에 원시 배열과 문자열 배열 케이스가 있긴 하지만, 그것들은 전부 반환 타입이다.\
`WithPrimitiveArrayMethod`의 `test()`는 인자가 없다.\
즉 테스트 픽스처는 "원시 타입"과 "배열"을 반환 타입 축에서만 교차시켰고, 파라미터 축에서는 참조 타입만 써서 버그가 지나갈 틈을 남겼다.

> **픽스처(fixture)** — 테스트가 입력으로 쓰려고 일부러 만들어 둔 고정된 대상.\
> 예: `sample(int number, String[] values)` 메서드 하나만 가진 중첩 클래스가 이 PR의 픽스처다.

## 4. 수정 해설 — 헬퍼 하나로 두 슬롯을 통일

수정은 파라미터 매핑을 헬퍼 참조로 바꾸는 한 줄이다.

```java
builder.append(Stream.of(this.descriptor.parameterArray())
		.map(ClassFileAnnotationMetadata::resolveTypeName)
		.collect(Collectors.joining(",")));
```

> **메서드 참조(method reference)** — 람다 대신 기존 메서드를 그대로 가리키는 자바 문법(`클래스::메서드`).\
> 예: `.map(desc -> resolveTypeName(desc))`를 `.map(ClassFileAnnotationMetadata::resolveTypeName)`으로 줄여 쓴다.

이 선택의 근거는 세 가지다.\
첫째, 새 규칙을 만들지 않는다.\
`resolveTypeName`은 이미 같은 파일의 반환 타입 슬롯이 쓰는 함수이므로, 한 문자열 안의 두 타입 슬롯이 같은 규칙을 공유하게 될 뿐이다.

둘째, ASM 변형과 값이 정렬된다.\
ASM 쪽 `SimpleMethodMetadataReadingVisitor.Source#toString()`은 파라미터마다 `argumentTypes[i].getClassName()`을 쓰는데, 이것이 내는 정규 이름이 곧 `resolveTypeName`의 목표값이다.

> **정규 이름(canonical name)** — 패키지까지 붙인, 사람이 소스에 쓰는 그대로의 타입 이름.\
> 예: `String[]`의 정규 이름은 `java.lang.String[]`이고, `int[][]`의 정규 이름은 `int[][]`다.

셋째, 파급이 없다.\
이 문자열을 읽어 분기하는 메타데이터 로직은 없고 소비처는 진단 메시지뿐이므로, 계약 표면은 그대로다.

> **계약 표면(contract surface)** — 바꾸면 남의 코드가 깨지는, 밖으로 약속된 부분.\
> 예: `getReturnTypeName()`이 돌려주는 값은 계약이지만, 진단용 `toString()` 문자열은 아니다.

`ClassDesc`를 직접 다루는 대안 — 예컨대 파라미터마다 배열 여부를 판정해 분기하는 코드를 `Source` 안에 다시 쓰는 방식 — 은 규칙을 두 곳에 두게 된다.\
gh-36577이 이미 그 규칙을 한 곳으로 모아 두었으므로, 그 결정을 따르는 편이 일관된다.

## 5. 검증 — 테스트가 무엇을 고정하나

PR은 `src/test/java24`에 회귀 테스트를 새로 추가했다.\
이 경로는 앞서 본 멀티 릴리스 빌드 설정 덕분에 `java24Test` 태스크에서만 컴파일·실행되므로, JDK 24 미만에서는 아예 존재하지 않는 테스트가 된다.

> **회귀 테스트(regression test)** — 한 번 고친 결함이 다시 살아나는지 감시하려고 남기는 테스트.\
> 예: 수정 전 코드에서 반드시 실패하고, 수정 후에는 통과해야 한다.

```java
	@Test
	void toStringRendersParameterTypeNames() throws Exception {
		ClassFileMetadataReaderFactory factory = new ClassFileMetadataReaderFactory(new DefaultResourceLoader());
		MetadataReader reader = factory.getMetadataReader(WithMethod.class.getName());
		MethodMetadata method = reader.getAnnotationMetadata().getDeclaredMethods().stream()
				.filter(candidate -> candidate.getMethodName().equals("sample"))
				.findFirst()
				.orElseThrow();
		// primitive and array parameter types must keep their canonical names,
		// not be prefixed with "." (".int", ".String[]")
		assertThat(method.toString()).endsWith(".sample(int,java.lang.String[])");
	}
```

이 테스트가 고정하는 불변식은 하나다.\
원시 타입 파라미터와 참조 배열 파라미터가 정규 이름으로 렌더링된다는 것.\
픽스처 `sample(int number, String[] values)`는 앞 절의 표에서 깨지던 두 칸을 정확히 겨냥한다.\
단언은 `endsWith`를 써서 선언 클래스 이름과 접근 제어자 접두사를 검증 대상에서 뺐다.\
그 부분은 이 PR의 관심사가 아니고, 이미 공유 테스트가 검증한다.

> **불변식(invariant)** — 코드가 어떻게 바뀌든 항상 참이어야 하는 성질.\
> 예: "파라미터 타입은 언제나 정규 이름으로 렌더링된다"가 이 테스트가 박아 두는 불변식이다.

한편 이 테스트 배치는 프로젝트가 같은 문제를 다루던 방식과는 다르다.\
gh-36577의 최종 커밋은 오히려 반대 방향으로 움직였다.\
ClassFile 전용 테스트 파일을 지우고, 검증을 ASM과 ClassFile이 함께 상속하는 `AbstractMethodMetadataTests`로 옮겼다.

`src/test/java` 아래의 공유 테스트는 `java24Test` 태스크에서도 java24 클래스와 함께 다시 실행되므로, 한 벌의 단언이 두 구현을 동시에 잰다.\
이 PR의 픽스처를 `AbstractMethodMetadataTests.verifyToString()`에 파라미터 케이스로 추가했다면 두 리더의 정렬까지 함께 고정됐을 것이다.

## 6. 상태와 교훈

PR은 2026-09-03 머지됐다(`ad83d5ebd9e`, main).\
본문은 `## Overview` / `## Problem` / `## Fix` 형식을 따르고, gh-36577과의 관계를 별도 절로 명시했다.\
같은 함수의 미완 수정을 잇는 PR이므로, 선행 이슈 번호를 밝히는 것이 리뷰어의 판단 비용을 줄인다.\
머지 직후 메인테이너가 테스트 배치를 손댔는데, 그 내용은 §7에서 따로 다룬다.

교훈은 둘이다.\
첫째, 헬퍼를 도입하는 수정은 도입만으로 끝나지 않는다.\
gh-36577은 문제의 규칙을 함수로 뽑아 놓고도 호출부 하나를 남겼다.\
같은 파일 안에서 옛 표현식이 문자열 검색으로 바로 잡히는 형태였는데도 그렇다.\
규칙을 추출했다면 그 규칙의 옛 인라인 표현을 전부 훑는 것이 추출 작업의 일부다.

둘째, 테스트 픽스처의 교차가 부족하면 버그가 통과한다.\
기존 테스트는 "원시/배열"과 "반환/파라미터"라는 두 축을 갖고 있었지만 실제로는 대각선만 채웠다.\
파라미터 축에는 참조 타입만 있었고, 그 타입들은 깨진 코드에서도 우연히 맞는 값을 냈다.\
타입 렌더링처럼 케이스가 분류로 갈리는 로직은, 분류마다 값을 확인하는 것이 아니라 분류의 곱집합에서 빈 칸을 찾는 편이 안전하다.

> **곱집합(cartesian product)** — 두 축의 모든 조합을 빠짐없이 만든 표.\
> 예: 축이 {원시, 배열} × {반환, 파라미터}면 칸이 넷이고, 이 버그는 채워지지 않은 칸에 있었다.

## 7. 머지와 후속 polish — 전용 테스트가 공유 스위트로 옮겨졌다

머지 커밋 `ad83d5ebd9e`는 제출한 내용 그대로다.\
프로덕션 한 줄과 `src/test/java24`의 전용 테스트 파일 55줄이 함께 들어갔다.\
그리고 같은 날 Brian Clozel이 `6316c06a977`("Polishing contribution", See gh-36919)로 **테스트만** 재배치했다.\
전용 파일을 통째로 지우고, 같은 검증을 `AbstractMethodMetadataTests`에 15줄로 다시 썼다.

```java
	@Test
	void toStringMethodShowsPrimitives() {
		assertThat(getTagged(WithMethodParameters.class).toString())
				.isEqualTo("public java.lang.String org.springframework.core.type.AbstractMethodMetadataTests$WithMethodParameters.test(java.lang.String[],int)");
	}
```

```java
	public static class WithMethodParameters {

		@Tag
		public String test(String[] names, int age) {
			return "";
		}

	}
```

폴리시가 바꾼 것은 셋이다.\
위치가 `src/test/java24`의 ClassFile 전용 파일에서 `src/test/java`의 공유 추상 스위트로 옮겨졌고, 픽스처가 `void sample(int, String[])`에서 `String test(String[] names, int age)`로 바뀌었으며, 단언이 `endsWith`에서 전체 문자열 `isEqualTo`로 강해졌다.

단언 한 줄이 몇 개의 구현을 재는지가 이 이동의 전부다.

```text
제출 시점 -- src/test/java24 의 ClassFile 전용 파일
  ClassFileMethodMetadataToStringTests.toStringRendersParameterTypeNames()
        |
        +--> ClassFile 구현 하나만 잰다

폴리시 후 -- src/test/java 의 공유 추상 스위트
  AbstractMethodMetadataTests.toStringMethodShowsPrimitives()
        |
        +--> StandardMethodMetadataTests    리플렉션
        |
        +--> DefaultMethodMetadataTests     JDK 24 미만 -> ASM
        |
        +--> DefaultMethodMetadataTests     JDK 24 이상 -> ClassFile
```

이 배치가 나은 이유는 이 추상 클래스를 상속하는 구현이 하나가 아니라는 데 있다.\
`StandardMethodMetadataTests`는 리플렉션 기반이고, `DefaultMethodMetadataTests`는 `MetadataReaderFactory.create(...)`에 위임하므로 JDK 24 미만에서는 ASM 구현을, JDK 24 이상에서는 ClassFile 구현을 잰다.

> **리플렉션(reflection)** — 클래스를 실제로 로드한 뒤 그 객체에게 자기 구조를 물어보는 방식.\
> 예: `Method#toString()`은 이미 로드된 메서드가 스스로 내놓는 문자열이다.

그리고 `java24Test` 태스크는 java24 소스셋만 도는 것이 아니라 공유 테스트 소스셋을 멀티 릴리스 JAR와 함께 다시 돌린다 — `MultiReleaseExtension.createTestTask`가 `sharedTestSourceSet.getOutput()`을 `testClassesDirs`에 넣고 `jar` 태스크 산출물을 클래스패스 맨 앞에 둔다.\
그래서 단언 한 줄이 리플렉션·ASM·ClassFile 세 경로를 동시에 고정한다.

기대 문자열이 임의로 정한 형식이 아니라는 점이 핵심이다.\
`StandardMethodMetadata.toString()`은 `this.introspectedMethod.toString()`을 그대로 위임하므로, 저 문자열은 JDK `java.lang.reflect.Method#toString()`의 출력이다.\
즉 같은 단언을 세 구현이 공유하는 순간 "바이트코드만 읽는 두 리더가 JDK 리플렉션과 **같은 문자열**을 내야 한다"는 계약이 테스트로 박힌다.\
전용 파일에 `endsWith`로 두었을 때 ClassFile 구현은 자기 자신과만 일치하면 됐고, ASM 구현과 어긋나도 아무도 알려주지 않았다.\
부수 효과로 `src/test/java24` 디렉터리는 파일이 하나도 남지 않아 사라졌다.

배울 점은 명확하다.\
이 배치는 [tests.md](tests.md) §3과 위 §5 끝 단락이 제출 시점에 이미 지적해 둔 것이다 — "이 픽스처를 `AbstractMethodMetadataTests`에 파라미터 케이스로 추가했다면 두 리더의 정렬까지 함께 고정됐을 것이다".\
게다가 선행 gh-36577의 최종 커밋이 정확히 같은 이동, 곧 전용 파일을 지우고 공유 스위트로 편입하는 이동을 했다는 사실까지 파악한 상태였다.

문제 인식은 맞았는데 제출물에는 반영하지 않았고, 그 한 걸음을 메인테이너가 대신 걸었다.\
프로젝트에 이미 선례가 있는 배치 관례는 "더 나은 대안"으로 문서에 적어 둘 것이 아니라 제출의 기본값으로 삼아야 한다.\
관례를 알면서 따르지 않으면, 그 판단 비용이 리뷰어에게 넘어간다.

---

연관 ko-docs (모듈 지도): `spring-core/05-어노테이션-메타데이터와-asm.md`
