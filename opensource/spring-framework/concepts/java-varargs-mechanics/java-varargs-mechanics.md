# 개념: 컴파일러는 `String...`을 어떻게 처리하나 — varargs의 실체와 in-place 정렬

> J6(`SQLErrorCodes.setDuplicateKeyCodes` 정렬 누락, 작업 폴더
> `docs/plans/2026-08-29/j6-sqlerrorcodes-duplicate-key-sort/`)의 배경 문서.
> 아래 바이트코드와 실행 출력은 JDK 25.0.1(`javac 25.0.1`)로 실제 뽑은 것이다.

## 결론

varargs는 **호출 지점에서 배열을 만들어 주는 문법 설탕**이고, 메서드 쪽에서 보면
그냥 `String[]` 파라미터다(바이트코드 시그니처 `([Ljava/lang/String;)V` +
`ACC_VARARGS` 플래그). 값을 나열해 부르면 컴파일러가 그 자리에서 `anewarray`로 새
배열을 만들지만, 배열 변수를 그대로 넘기면 그 참조가 그대로 간다. 그래서
`Arrays.sort(array); return array;` 같은 in-place 유틸리티를 쓰는 setter는 값 나열
호출에서는 안전하고(갓 만든 배열), 배열 전달 호출에서는 호출자의 배열을 정렬해
버린다. `SQLErrorCodes`의 코드 setter 10개가 전부 이 동작을 공유하는 관례다.

## 실증 1 — 메서드 쪽에는 varargs가 없다

프로브(`Probe.java`)를 컴파일해 `javap -v`로 본 `setCodes`의 머리 부분이다.

```
  static void setCodes(java.lang.String...);
    descriptor: ([Ljava/lang/String;)V
    flags: (0x0088) ACC_STATIC, ACC_VARARGS
```

`descriptor`는 `String[]`을 받는 메서드와 글자 하나 다르지 않다. 차이는
`ACC_VARARGS`(0x0080)뿐이고, 이 플래그는 "값 나열 호출도 받아 줄 수 있다"를
**컴파일러에게** 알릴 뿐 JVM의 호출 동작에는 관여하지 않는다(리플렉션의
`Method.isVarArgs()`가 읽는 것도 이 플래그다).

## 실증 2 — 배열은 호출 지점에서 만들어진다

같은 프로브의 두 호출 지점을 `javap -c`로 나란히 본다. 위가
`setCodes("90002", "1586", "1062")`, 아래가 `setCodes(callerArray)`다.

```
  static void callWithValues();
    Code:
         0: iconst_3
         1: anewarray     #22                 // class java/lang/String
         4: dup
         5: iconst_0
         6: ldc           #24                 // String 90002
         8: aastore
                                              // 1586, 1062 도 같은 dup/ldc/aastore 3연
        19: invokestatic  #30                 // Method setCodes:([Ljava/lang/String;)V
        22: return

  static void callWithArray(java.lang.String[]);
    Code:
         0: aload_0
         1: invokestatic  #30                 // Method setCodes:([Ljava/lang/String;)V
         4: return
```

두 호출이 도달하는 `invokestatic` 대상은 같은 `#30`이다 — 오버로드가 둘인 것이
아니라, 컴파일러가 한쪽에만 배열 생성 코드를 끼워 넣었을 뿐이다. 두 호출 형태의 차이를
정리하면 다음과 같다.

| | 값 나열 `f("a","b")` | 배열 전달 `f(arr)` |
|---|---|---|
| 호출 지점 바이트코드 | `anewarray` + `aastore` | `aload` 한 개 |
| 넘어가는 배열의 주인 | 호출 지점이 방금 만든 것 | 호출자 |
| 콜리가 in-place 수정하면 | 아무도 안 보는 배열이라 무해 | 호출자 배열이 변이됨 |

## 실증 3 — in-place 정렬과 결합했을 때

`StringUtils.sortStringArray`(spring-core `StringUtils.java` L1066-1073)는 새
배열을 만들지 않는다.

```java
public static String[] sortStringArray(String[] array) {
	if (ObjectUtils.isEmpty(array)) {
		return array;
	}

	Arrays.sort(array);
	return array;
}
```

프로브에서 같은 모양의 헬퍼를 varargs setter에 붙이고 실행한 출력이다.

```
caller array after call = [1062, 1586, 90002]
same reference as stored = true
stored (values call)    = [1062, 1586, 90002]
```

첫 줄이 요점이다. 호출자가 `{"90002", "1586", "1062"}` 배열 변수를 넘겼는데 호출이
끝난 뒤 **호출자 쪽 변수의 내용이 정렬돼 있고**, 저장된 필드와 그 배열은 같은
객체다. 값 나열 호출(셋째 줄)은 결과가 같아 보이지만 정렬 대상이 호출 지점에서 갓
만든 임시 배열이라 밖에서 관측되지 않는다.

## Spring 실코드 — SQLErrorCodes와 J6

`SQLErrorCodes.java` L105-183의 코드 배열 setter는 J6 수정 이후 열 개가 전부 같은
형태다(L105/113/125/129/137/145/153/161/169/177).

```java
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = StringUtils.sortStringArray(duplicateKeyCodes);
}
```

J6 전에는 `setDuplicateKeyCodes`만 정렬 없이 대입했고, 소비자
`SQLErrorCodeSQLExceptionTranslator`가 `Arrays.binarySearch`를 쓰기 때문에 미정렬
선언이 조용한 미번역으로 이어졌다. 수정은 예외를 하나 지운 것이며, 그 결과 "코드
배열 setter는 입력 순서와 무관하게 정렬 배열을 저장한다"는 불변식이 열 개 전부에
성립한다. 부수 효과인 "배열을 넘기면 호출자 배열도 정렬된다"는 이 클래스의 오래된
관례이지 J6이 들여온 것이 아니다.

`SQLErrorCodeSQLExceptionTranslatorTests` L113의
`errorCodes.setDuplicateKeyCodes("90002", "1586", "1062")`는 컴파일 후 실증 2의
`callWithValues`와 같은 모양이 된다 — 길이 3짜리 `String[]`을 그 자리에서 만들어
`aastore` 세 번으로 채운 뒤 `setDuplicateKeyCodes([Ljava/lang/String;)V`를
호출한다. 이 테스트는 그 임시 배열을 붙잡고 있지 않으므로, 정렬을 관측하는 통로는
getter가 아니라 번역 결과다.

## varargs는 제네릭이 아니다

varargs와 제네릭은 무관한 기능이다. `String...`에는 타입 파라미터가 없고 지워지는
것도 없다. 다만 둘이 겹칠 때만 별도 규칙이 붙는다. 파라미터화된 타입의
varargs(`List<T>...`)는 컴파일러가 `List[]`를 만드는데, 배열은 공변이고 제네릭은
소거되므로 그 배열에 엉뚱한 원소가 들어갈 여지(heap pollution)가 생긴다.

```
Generic.java:5: warning: [unchecked] Possible heap pollution from parameterized vararg type List<T>
	static <T> List<T> first(List<T>... lists) {
```

메서드가 그 배열을 읽기만 하고 밖으로 새게 하지 않는다면 `@SafeVarargs`로 경고를
없앨 수 있다(정적 메서드, final/private 인스턴스 메서드, 생성자에만 붙는다).
`String...`에는 해당 사항이 없다.

## 함정 1 — `f(null)`은 "인자 없음"이 아니다

`setCodes(null)`은 빈 배열 호출이 아니라 배열 자리에 null을 넣는다(바이트코드는
`0: aconst_null` 뒤 곧장 `invokestatic`). 컴파일러도 이를 모호하게 보아 경고한다:
`non-varargs call of varargs method with inexact argument type for last parameter`.
프로브에서는 헬퍼가 곧장 `Arrays.sort`를 불러 `NullPointerException: Cannot read
the array length because "a" is null`이 났다. Spring의 `sortStringArray`는 앞단의
`ObjectUtils.isEmpty`(null이면 true, `ObjectUtils.java` L118-120)가 걸러 null을
그대로 되돌려 주므로 여기서 터지지는 않는다 — 대신 필드가 null이 되고 문제는 그
필드를 읽는 쪽으로 미뤄진다. `f((String[]) null)` 또는 `f(new String[0])`으로
캐스팅해 의도를 못 박아야 한다.

## 함정 2 — 오버로드 모호로 컴파일 자체가 안 되는 경우

varargs는 오버로드 해석의 마지막 단계에서만 고려되지만, 같은 이름의 varargs
메서드가 둘 이상이면 값 나열 호출이 어느 쪽으로도 갈 수 있어 컴파일이 막힌다.
PR #37186의 blind 테스트 설계에서 실제로 밟은 사례가 그것이다
(`../../prs/37186-resolvabletype-generics-serialization/tests.md` T6):

> (`forClassWithGenerics(String.class)`는 오버로드 모호로 컴파일 불가 — 배열
> 명시가 필요하다는 것도 blind 설계의 실측 발견.)

`ResolvableType`에는 `forClassWithGenerics(Class<?>, Class<?>...)`와
`forClassWithGenerics(Class<?>, ResolvableType...)`이 둘 다 있어서, 가변 인자를
0개로 준 호출은 두 후보 중 하나를 고를 근거가 없다. 그래서 그 테스트는
`new ResolvableType[0]`을 명시해 varargs 확장을 아예 거치지 않게 만들었다. 런타임
실패가 아니라 **컴파일 실패**라는 점이 요점이다 — varargs 해석은 전부 컴파일
타임에 끝난다.

## 남는 규칙

이 문서에서 실증한 것을 설계 규칙으로 옮기면 세 가지가 남는다.

- varargs 파라미터는 메서드 안에서는 그냥 배열이다. 그 배열을 필드에 저장하거나
  in-place로 수정한다면 호출자가 배열을 넘겼을 때 무슨 일이 일어나는지를 계약으로
  정해 둬야 한다(방어 복사할지, 관례로 남길지).
- "값 나열 호출은 매번 새 배열"은 공짜 방어 복사처럼 보이지만 호출 형태에 의존하는
  안전이므로 불변식으로 기대면 안 된다.
- 컴파일 경고(`f(null)`)와 오버로드 모호는 둘 다 "이 호출이 varargs로 읽힐지 배열로
  읽힐지 모르겠다"는 같은 사정의 다른 얼굴이다.
