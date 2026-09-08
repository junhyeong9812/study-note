# PR #36938 — 테스트 해설 (테스트 하나하나)

> PR #36938 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 기존 `ThrowawayClassLoaderTests`에 테스트 메서드 하나를 덧붙였다. 성격은 red다.
파일 자체는 인접 기여 #36933이 만든 것이므로, 이 PR의 가드 역할은 새로 만든 것이 아니라
그 파일에 이미 있던 테스트가 맡는다. 이 문서는 추가된 한 건을 해설하고, 두 테스트가
폴백의 실패와 성공을 각각 어떻게 나눠 붙잡는지 정리한다.

## 1. 리소스가 없을 때의 예외 계약 — red

이 한 건은 3단 로딩의 세 관문을 모두 닫아 놓고, 그때 무엇이 밖으로 나오는지를 단언한다.

```java
@Test
void loadClassThrowsClassNotFoundExceptionWhenClassResourceIsMissing() {
	// The grandparent resolves bootstrap classes only, so super.loadClass(...) fails,
	// and the resource loader provides no class bytes. The fallback must then honor the
	// ClassLoader.loadClass contract by reporting the failure instead of returning null.
	ClassLoader resourceLoader = new ClassLoader(new ClassLoader(null) {}) {
		@Override
		public InputStream getResourceAsStream(String name) {
			return null;
		}
	};
	ThrowawayClassLoader classLoader = new ThrowawayClassLoader(resourceLoader);

	assertThatExceptionOfType(ClassNotFoundException.class)
			.isThrownBy(() -> classLoader.loadClass("com.example.MissingClass"));
}
```

- **주장**: 위임도 실패하고 리소스 폴백도 빈손일 때, `loadClass`는 `null`을 반환하는 대신
  `ClassNotFoundException`을 던진다. 즉 `java.lang.ClassLoader`가 문서화한 계약 —
  non-null `Class`를 반환하거나 `ClassNotFoundException`을 던진다 — 을 지킨다.
- **fix 전 결과와 이유**: red다. 판별은 diff의 프로덕션 쪽으로 확정된다. 수정 전
  catch 블록은 `return loadClassFromResource(name);` 한 줄이었고,
  `loadClassFromResource`는 `getResourceAsStream`이 `null`이면 그대로 `null`을 반환한다.
  그러면 그 `null`이 `loadClass`의 반환값으로 조용히 흘러 나가고, 예외는 발생하지 않는다.
  `assertThatExceptionOfType(...).isThrownBy(...)`는 "던져지지 않았다"로 실패한다.
- **fix 후**: catch 블록이 결과를 변수로 받아 `null`이면 원래 `ex`를 재전파한다.

  ```java
  catch (ClassNotFoundException ex) {
      Class<?> loadedFromResource = loadClassFromResource(name);
      if (loadedFromResource == null) {
          throw ex;
      }
      return loadedFromResource;
  }
  ```

  단언이 요구하는 예외 타입이 그대로 나오므로 green이 된다.
- **결함의 형태가 조용한 실패라는 점이 중요하다**. 예외가 나던 것이 안 나게 된 것이
  아니라, 처음부터 아무 신호도 없이 `null`이 반환되던 결함이다. 이런 종류는 호출자
  쪽에서 `NullPointerException`으로 뒤늦게 드러나므로, 테스트를 결함 지점에 붙여
  "여기서 예외가 나야 한다"를 못 박는 것이 유일한 재현 방법이다.
- **호출자 쪽 NPE를 재현하지 않은 이유**: 실제 증상은 `PreComputeFieldFeature`의
  `provideFieldValue`에서 `throwawayClass.getDeclaredField(...)`가 NPE를 내는 것이다.
  그러나 그 NPE는 상위 `catch (Throwable)`에 삼켜져 빌드를 깨지 않으므로 관측 대상으로
  삼기 어렵고, 무엇보다 이 PR이 고치는 것은 소비자가 아니라 로더의 계약이다. 테스트는
  결함이 있는 층에 붙었다.

## 2. 목이 흉내 내는 실제 상황

이 테스트의 목은 익명 클래스로더 두 겹이며, 각각 흉내 내는 것이 다르다.

바깥 익명 로더의 `getResourceAsStream`이 항상 `null`을 반환하는 것은 **`.class` 리소스가
존재하지 않는 클래스**를 흉내 낸다. 현실에서 이런 클래스는 런타임에 생성된 것들이다.
CGLIB 프록시, JDK 동적 프록시, 또는 `defineClass`로만 존재하고 파일 실체가 없는 클래스가
declaring class인 경우가 여기에 해당한다. 그런 클래스는 클래스패스를 뒤져도 바이트를
얻을 수 없으므로 3단계가 빈손이 된다. 이 상황을 진짜로 만들려면 프록시를 생성해 그
declaring class를 조회하게 만들어야 하는데, 재정의 한 줄이 같은 조건을 훨씬 단순하게
만든다.

안쪽 `new ClassLoader(null) {}`은 **위임 체인에 애플리케이션 클래스패스가 없는 상태**를
흉내 낸다. 이것은 흉내라기보다 프로덕션 구조 그대로다. `ThrowawayClassLoader`의 생성자가
`super(parent.getParent())`로 조부모를 자기 부모로 삼기 때문에, 넘겨받은 로더는 위임
체인에서 빠지고 리소스 공급자로만 남는다. 테스트는 그 구조에 맞춰 로더를 두 겹 쌓았고,
부모가 `null`인 로더는 부트스트랩 위임만 하므로 2단계가 반드시 실패한다.

클래스 이름 `"com.example.MissingClass"`는 어떤 클래스로더로도 절대 해석되지 않는 이름을
고른 것이다. 실재하는 이름을 썼다면 부트스트랩이나 플랫폼 로더가 해결해 버려 폴백에
도달하지 못할 위험이 있다.

정리하면 이 테스트는 3단 로딩의 세 관문을 모두 닫아 실패 경로만 남기는 배치다. 1단계
`findLoadedClass`는 이 로더가 아직 아무것도 정의하지 않았으므로 통과, 2단계 위임은
부모가 부트스트랩뿐이라 실패, 3단계 리소스는 `null`이라 실패다.

## 3. 가드는 인접 PR이 만든 기존 테스트가 맡는다

이 PR은 새 가드를 만들지 않았다. 같은 파일의 `loadingClassFromResourceClosesInputStream`
(PR #36933이 추가)이 그 역할을 한다. 그 테스트는 `Probe`의 실제 클래스 바이트를 공급해
폴백이 `defineClass`까지 도달함을 확인하므로, 이번 변경이 정상 로딩 경로를 망가뜨리지
않았다는 보증이 된다. 수정 전에도 green이고 수정 후에도 green이어야 하는 양성 가드다.

두 테스트가 나눠 붙잡는 경로를 정리하면 다음과 같다. 공통 전제는 둘 다 리소스 폴백
경로를 강제로 태운다는 점이고, 갈리는 축은 그 폴백이 바이트를 얻느냐 못 얻느냐다.

| 테스트 | `getResourceAsStream` | 기대 결과 | 성격 |
|---|---|---|---|
| `loadingClassFromResourceClosesInputStream` | 진짜 클래스 바이트 | `Class` 반환 + 스트림 닫힘 | 이 PR 기준 양성 가드 |
| `loadClassThrowsClassNotFoundExceptionWhenClassResourceIsMissing` | `null` | `ClassNotFoundException` | red |

이 배치가 중요한 이유는 이 PR의 수정이 **`null` 반환을 예외로 바꾸는 것**이기 때문이다.
과잉 수정의 형태는 명확히 상상 가능하다. 폴백이 성공했는데도 예외를 던지게 만드는
실수다. 위 표의 첫 행이 정확히 그 실수를 잡는다.

바꿔 말하면 이 PR은 인접 PR이 깔아 둔 테스트 위에 올라탔다. 두 변경은
`loadClassFromResource`라는 같은 메서드를 건드리지만 서로 다른 줄이라 충돌하지 않았고,
실제 리베이스 시 충돌은 테스트 파일에서만 났으며 양쪽 테스트를 모두 남기는 것으로
해결됐다.

## 4. 머지 후 폴리시

위 스니펫은 PR diff의 최종 상태다. 머지 후 sbrannen이 커밋
`7b31e0c2dcd9f6d0b142d58f111b6f960409555e`("Polish contribution")에서 두 가지를 보탰다.
하나는 `@Test  // gh-36938`이라는 이슈 번호 표기이고, 다른 하나는 단언 한 줄이다.

```java
String name = "com.example.MissingClass";
assertThatExceptionOfType(ClassNotFoundException.class)
		.isThrownBy(() -> classLoader.loadClass(name))
		.withMessageContaining(name);
```

`withMessageContaining(name)`이 추가로 고정하는 것은 재전파된 예외의 **정보량**이다.
이 PR의 설계 선택 중 하나가 "새 예외를 만들지 않고 2단계에서 발생한 원래 `ex`를 다시
던진다"였고, 그 이유는 원래 예외가 클래스명과 JDK 로더가 붙인 cause를 이미 담고 있기
때문이었다. 폴리시가 붙인 단언은 그 근거를 검증 대상으로 승격시킨다. 예외 타입만 맞고
메시지가 빈 껍데기라면 진단 품질 개선이라는 이 PR의 실제 이득이 사라지는데, 이 한 줄이
그것을 막는다. 원래 단언이 계약을 고정했다면 이 단언은 계약을 지킨 방식을 고정한다.

## 실측과 역할 요약

이 PR의 테스트 한 건에 대해 확인된 사실과 그 성격을 모아 둔다.

- 실측 기록: PR 본문에 "`./gradlew :spring-core:test`와 `checkstyleMain`/`checkstyleTest`가
  통과한다"는 서술이 있다. 개별 테스트 수나 수정 전 실패 건수는 본문과 diff에 남아 있지
  않으므로 판별 근거 부족으로 남긴다.
- red 1건, 이 PR이 추가한 가드 0건. 가드는 인접 PR #36933이 만든
  `loadingClassFromResourceClosesInputStream`이 겸한다.
- 이 테스트가 고정하는 명제는 값이 아니라 실패의 **표현 방식**이다. 같은 실패를
  `null`로 알리느냐 예외로 알리느냐의 차이이며, 그 차이가 소비자 쪽에서 정보 없는
  `NullPointerException`이 될지 클래스명이 담긴 `ClassNotFoundException`이 될지를 가른다.
- 테스트를 어렵게 만드는 부분은 단언이 아니라 조건 조성이다. 3단 로딩의 세 관문을 모두
  닫아야 검증하려는 줄에 도달하며, 그 조성이 익명 클래스로더 두 겹과 재정의 한 줄로
  이루어진다.
