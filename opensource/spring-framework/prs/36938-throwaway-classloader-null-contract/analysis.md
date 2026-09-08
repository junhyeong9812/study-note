# PR #36938 분석 — ThrowawayClassLoader.loadClass가 null을 반환하는 계약 위반

> 기준 상태. **수정 전** = `03d80feed0f`(= 이 PR의 base. 인접 PR #36933의 `try (inputStream)`이 이미 들어간 상태), **수정 커밋** = `233e7b91f9b`, **메인테이너 폴리시** = `7b31e0c2dcd`, **현재** = `upstream/main`(`7daf1013aa8`). 파일:줄 인용마다 어느 상태 기준인지 밝힌다.
> 이 문서의 자리: README(서사)·structure(구조도)·tests(테스트 해설)와 겹치지 않게, **"null이라는 값이 어느 경계에서 의미를 바꾸는가"**를 이름표 단위로 추적하고 단계별 상태로 고정한다.

## 0. 결론

`ThrowawayClassLoader.loadClass(name, resolve)`가 폴백 결과를 그대로 반환해(`catch { return loadClassFromResource(name); }`) **null을 밖으로 내보낼 수 있었다** — `java.lang.ClassLoader.loadClass`의 계약은 non-null `Class` 반환 또는 `ClassNotFoundException`이며, "찾지 못함"을 null로 표현하는 선택지는 그 계약에 없다.

수정은 폴백이 null이면 **2단계에서 이미 손에 들고 있던 원본 `ClassNotFoundException`(`ex`)을 재전파**하는 것이다. 새 예외를 만들지 않는 이유는 원본이 클래스명과 JDK 로더가 붙인 cause를 이미 담고 있고, 폴백 실패는 "정의할 바이트도 없었다"는 확인일 뿐 새 정보를 더하지 않기 때문이다.

상태: 머지됨. `upstream/main`의 커밋 `233e7b91f9b`("Throw ClassNotFoundException for missing class resource in ThrowawayClassLoader", `Closes gh-36938`) + 메인테이너 폴리시 `7b31e0c2dcd`. 이 PR은 크래시 수정이 아니라 **계약 준수와 진단 품질** 수정이다(4장·5장 참조).

## 1. 무대

무대와 소비자는 #36933과 같다 — `spring-core`의 `org.springframework.aot.nativex.feature` 패키지, 패키지 프라이빗 `ThrowawayClassLoader`와 유일 소비자 `PreComputeFieldFeature`. 공개 진입 API는 없고, GraalVM `native-image` 빌드가 `Feature` SPI로 `PreComputeFieldFeature`를 깨울 때만 돈다.

다른 점은 **어느 표면을 보느냐**다. #36933은 `loadClassFromResource` 내부의 자원 수명이 무대였다면, 이 PR의 무대는 `loadClass`와 `loadClassFromResource` **사이의 경계**다. 두 메서드의 반환 계약이 서로 다르다는 것이 출발점이다.

| 메서드 | 가시성 | 반환 계약 | null의 의미 |
|---|---|---|---|
| `loadClass(String, boolean)` (`:47`) | protected, `ClassLoader` 재정의 | non-null `Class` 또는 CNFE | **허용되지 않음** — JDK 계약 위반 |
| `loadClassFromResource(String)` (`:62`) | private, 호출자 1개 | `Class` 또는 null 또는 CNFE/ClassFormatError | **정당한 내부 신호** — "그 이름의 .class 리소스가 없다" |

결함은 "private 헬퍼가 null을 쓴다"가 아니다. 그 내부 신호가 **번역 없이 public 계약 표면으로 흘러나갔다**는 것이고, 수정은 정확히 그 경계에 번역기를 놓는 일이다.

한 가지 배경 사실이 이 결함이 오래 남은 이유를 설명한다. 이 패키지의 `package-info.java:4`는 `@NullUnmarked`다. JSpecify 기반 null 검사가 이 패키지에는 적용되지 않으므로, `loadClassFromResource`가 null을 반환하고 그 값이 non-null 계약 자리로 흘러가는 것을 정적 도구가 잡아 주지 않는다.

## 2. 전체 메서드 그래프

수정 전(`03d80feed0f`) 기준 줄번호다. `[N]`은 값이 통과하는 지점을 표시한다.

```
 GraalVM native-image 빌드 (Feature SPI)
   |
   v
 PreComputeFieldFeature.iterateFields(access, subtype)          PreComputeFieldFeature.java:61
   |  패턴 매치 필드마다:
   |     try {                                                                    :72
   |         Object fieldValue = provideFieldValue(field);                        :73
   |         access.registerFieldValueTransformer(field, ... -> fieldValue)       :74
   |         if (verbose) println("... set to ... at build time")                 :75-78
   |     }
   |     catch (Throwable ex) {                        <=== 넓은 안전망            :80
   |         if (verbose) println("... will be evaluated at runtime due to this   :81-84
   |                               error during build time evaluation: " + ex)
   |     }                                             <=== 빌드는 실패하지 않는다
   v
 PreComputeFieldFeature.provideFieldValue(field)                                  :96
   |  [1] Class<?> throwawayClass = throwawayClassLoader.loadClass(선언클래스명)   :99
   |  [2] Field f = throwawayClass.getDeclaredField(field.getName())              :100
   |         ^^^^^^^^^^^^^^ [1]이 null이면 여기서 NullPointerException
   |      f.setAccessible(true); return f.get(null);                              :101-102
   v
 ThrowawayClassLoader.loadClass(name, resolve)              ThrowawayClassLoader.java:47
   |  synchronized (getClassLoadingLock(name))                                    :48
   |  [1단계] loaded = findLoadedClass(name); if (loaded != null) return loaded;   :49-52   -> non-null
   |  [2단계] try { return super.loadClass(name, true); }                          :53-55   -> non-null 또는 CNFE(ex)
   |  [3단계] catch (ClassNotFoundException ex) {                                  :56
   |             return loadClassFromResource(name);   [!] 결함: null이 그대로 통과   :57
   |          }                                                                    :58
   v
 ThrowawayClassLoader.loadClassFromResource(name)                                  :62
   |  resourceName = name.replace('.', '/') + ".class"                             :63
   |  inputStream = resourceLoader.getResourceAsStream(resourceName)               :64
   |  if (inputStream == null) return null;   [!] null의 발원지                      :65-67
   |  try (inputStream) { ... return defineClass(name, bytes, 0, len); }           :68-73  -> non-null
   |  catch (IOException ex) { throw new ClassNotFoundException(...); }            :74-76  -> CNFE
```

데이터 흐름을 한 줄로 요약하면 이렇다. **`:66`에서 태어난 null이 `:57`을 무번역으로 통과해 `:99`에 도착하고, `:100`에서 역참조된다.** 수정은 `:57` 자리에 번역기를 놓아 이 흐름을 `:66` -> CNFE로 끊는다.

## 2.5 핵심 이름표 사전

이 결함을 읽을 때 헷갈리는 것은 "null"과 "예외"라는 두 실패 표현이 한 호출 사슬 안에서 세 번 바뀐다는 점(`super.loadClass`의 CNFE -> 폴백의 null -> 호출자의 NPE)과, 이름이 비슷한 지역변수 `loaded`/`loadedFromResource`가 서로 다른 단계의 결과라는 점이다.

| 이름표 | 무엇인가 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `loadClass(name, resolve)` (`:47`) | 재정의된 3단 로딩 진입점이자 이 클래스의 유일한 계약 표면 | 클래스명 -> `Class` 또는 CNFE | `provideFieldValue`가 필드마다 | **계약이 깨지는 그 표면** |
| `resolve` (파라미터) | JDK 계약상 링크 여부 플래그 | boolean -> (무시됨) | 상동 | 무관. 항상 `super.loadClass(name, true)`로 상수 전달 — 기존 동작이며 이 PR 범위 밖 |
| `loaded` (지역, `:49`) | **1단계** `findLoadedClass` 결과. 이 로더가 이미 정의한 클래스 | 클래스명 -> `Class` 또는 null | 매 `loadClass` 첫 줄 | 여기의 null은 `:50`에서 즉시 검사되어 밖으로 새지 않는다 — 올바른 null 처리의 대조군 |
| `super.loadClass(name, true)` (`:54`) | **2단계** 조부모 체인 위임 | 클래스명 -> `Class` 또는 CNFE | 1단계 miss일 때 | 여기서 던져진 CNFE가 곧 수정안이 재전파할 `ex`다 |
| `ex` (catch 파라미터, `:56`) | 2단계 위임 실패 예외. JDK 로더가 만든 것이라 **클래스명과 cause를 이미 담고 있다** | - | 2단계 실패 시 | 수정의 핵심 자원. catch 블록이 폴백을 품고 있어 새 예외를 만들 필요 없이 손에 들려 있다 |
| `loadClassFromResource(name)` (`:62`) | **3단계** 리소스 바이트로 직접 정의하는 폴백 | 클래스명 -> `Class` 또는 null 또는 CNFE | `loadClass`의 catch에서만 | null 발원지를 품은 메서드. 이 PR은 이 메서드를 **바꾸지 않는다** |
| `inputStream` (지역, `:64`) | `getResourceAsStream` 결과 | 리소스 경로 -> `InputStream` 또는 null | 3단계 | 이 null이 `:66`의 반환 null로 승격된다. (스트림 닫기는 #36933의 주제) |
| `if (inputStream == null) return null;` (`:65-67`) | "그 이름의 .class 리소스가 없다"는 내부 신호 | -> null | 3단계 | **결함의 발원지이지만 결함 자체는 아니다** — private 헬퍼의 정당한 표현 |
| `loadedFromResource` (지역, 수정 후 `:57`) | 3단계 결과를 담는 새 변수 | -> `Class` 또는 null | 수정 후 catch 블록 | 수정이 도입한 이름. `loaded`(`:49`)와 이름이 겹치지 않도록 별도 명명 |
| `throw ex;` (수정 후 `:59`) | 폴백 실패 시 원본 예외 재전파 | -> CNFE | `loadedFromResource == null`일 때 | **수정의 본체.** 새 CNFE가 아니라 원본을 던지는 선택이 진단 정보를 보존한다 |
| `throwawayClassLoader` (`PreComputeFieldFeature.java:52`) | `new ThrowawayClassLoader(getClass().getClassLoader())` | -> 로더 1개 | 인스턴스 생성 시 | 계약을 신뢰하는 소비자 측 필드 |
| `provideFieldValue(field)` (`:96`) | 일회용 로더로 static final 필드값을 읽는 곳 | `Field` -> `Object` | `iterateFields`가 패턴 매치마다 | `:99`가 받은 값을 `:100`에서 **널 검사 없이 즉시 역참조** |
| `throwawayClass` (지역, `:99`) | `loadClass` 반환값 | -> `Class` (계약상 non-null) | 상동 | 이 변수에 null이 담기는 것이 계약 위반의 관측 형태 |
| `getDeclaredField(...)` (`:100`) | 복제본 클래스에서 같은 이름의 필드 조회 | 이름 -> `Field` | 상동 | **NPE 발생 지점** |
| `catch (Throwable ex)` (`:80`) | `provideFieldValue` 전체를 감싸는 넓은 안전망 | `Throwable` -> (verbose 로그) | 필드마다 | NPE를 삼켜 **빌드를 초록으로 유지**한다. 그래서 이 결함은 크래시가 아니라 조용한 진단 열화로 나타난다 |
| `verbose` (`:39-40`) | `-Dspring.native.precompute.log=verbose` 여부 | -> boolean | 클래스 초기화 시 1회 | 결함의 유일한 관측 창. 이 플래그가 꺼져 있으면 아무 흔적도 남지 않는다 |
| `package-info.java`의 `@NullUnmarked` (`:4`) | 이 패키지를 JSpecify null 검사 대상에서 제외 | - | 빌드 도구 | null이 계약 표면으로 새는 것을 정적 도구가 잡지 못한 이유 |

## 3. 결함 경로 단계 추적

트리거 조건이 좁다는 점부터 못 박아 둔다. 결함이 발동하려면 (a) 패턴에 걸리는 `static final boolean` 필드를 선언한 클래스가 (b) 조부모 체인 위임으로 풀리지 않고 (c) 그 클래스의 `.class` 리소스도 `resourceLoader`에서 얻을 수 없어야 한다. (c)를 만족하는 대표 사례는 런타임 생성 클래스다.

아래 표는 정상 케이스와 결함 케이스를 나란히 놓고, 각 단계에서 값이 무엇인지를 적은 것이다.

| 단계 | 정상 케이스 (`org.springframework.core.NativeDetector`) | 결함 케이스 (.class 리소스 없는 클래스) — 수정 전 | 결함 케이스 — 수정 후 |
|---|---|---|---|
| `:49` `findLoadedClass` | null (첫 요청) | null | null |
| `:54` `super.loadClass` | CNFE 던짐 (조부모 체인에 앱 클래스패스 없음) | CNFE 던짐 | CNFE 던짐 |
| `:56` catch 진입 | `ex` = CNFE(클래스명 포함) | `ex` = CNFE(클래스명 포함) | `ex` = CNFE(클래스명 포함) |
| `:64` `getResourceAsStream` | non-null 스트림 | **null** | **null** |
| `:66` 폴백 반환값 | (도달 안 함) | **null** | **null** |
| `:57` catch의 반환 | `defineClass` 결과(non-null `Class`) | **null을 그대로 반환** | `loadedFromResource == null` -> **`throw ex`** |
| `loadClass` 결과 | non-null `Class` | **null (계약 위반)** | CNFE (계약 준수) |
| `provideFieldValue :99` | `throwawayClass` = 복제본 클래스 | `throwawayClass` = **null** | (예외가 전파되어 `:99`에서 이미 이탈) |
| `provideFieldValue :100` | `getDeclaredField` 성공 | **NullPointerException** | (도달 안 함) |
| `iterateFields :80` | (도달 안 함 — 정상 등록) | `catch (Throwable)`가 NPE를 삼킴 | `catch (Throwable)`가 CNFE를 삼킴 |
| verbose 로그 | "Field ... set to ... at build time" | "... due to this error during build time evaluation: **java.lang.NullPointerException**" | "... : **java.lang.ClassNotFoundException: 클래스명**" |
| 최종 동작 | 빌드 타임 상수 폴딩 | 런타임 평가로 폴백 (빌드 성공) | 런타임 평가로 폴백 (빌드 성공) |

마지막 두 행이 이 PR의 성격을 규정한다. **기능 결과는 수정 전후가 동일하다** — 어느 쪽이든 `catch (Throwable)`가 잡아 런타임 평가로 폴백하고 빌드는 초록이다. 실제로 개선된 것은 두 가지뿐이다. (1) `loadClass`가 문서화된 계약을 지킨다. (2) verbose 진단이 원인을 지목하는 `ClassNotFoundException: <클래스명>`으로 바뀌어, "NullPointerException이 왜 나지"라는 오도를 없앤다. PR 본문이 이 점을 "not a crash fix"로 명시한 것도 같은 이유다.

## 4. 계약

이 무대에 걸린 약속 다섯과, 결함이 그중 무엇을 어기는지를 나란히 놓는다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| `ClassLoader.loadClass`는 non-null `Class`를 반환하거나 `ClassNotFoundException`을 던진다 | `java.lang.ClassLoader` javadoc | **어긴다** — 3단계가 null이면 그 null이 반환된다 |
| private 헬퍼는 내부 신호로 null을 써도 된다 (호출자가 하나이고 즉시 처리한다면) | `loadClassFromResource`의 시그니처와 `:65-67` | 어기지 않는다. 수정 후에도 이 메서드는 여전히 null을 반환하며, **유일 호출자가 그 null을 즉시 CNFE로 번역**해 불변식이 복원된다 |
| 로딩 성공 경로의 동작은 보존되어야 한다 | PR의 자기 제약 | 수정이 catch 블록의 null 분기에만 닿는다. 인접 PR #36933이 만든 `loadingClassFromResourceClosesInputStream` 테스트가 성공 경로의 가드 역할을 한다 |
| 실패 보고는 가장 정확한 원인을 담아야 한다 | 진단 품질 판단 | 수정이 이 계약을 **강화**한다. 새 CNFE를 만들면 2단계 위임 실패의 cause가 사라지므로 원본 `ex`를 재전파 |
| 이 패키지는 null 검사 대상이 아니다 | `package-info.java:4` (`@NullUnmarked`) | 결함과 무관하지만, 컴파일러·정적 도구가 이 계약 위반을 잡지 못한 이유 |

기존 테스트가 고정하던 것: 이 PR의 base에는 `ThrowawayClassLoaderTests`가 이미 있었다(#36933이 신설). 그러나 그 테스트는 폴백 **성공** 경로만 다루므로, 폴백 실패 시의 반환 계약은 어떤 테스트도 고정하지 않고 있었다.

## 5. 수정안

수정은 `loadClass`의 catch 블록 한 곳에만 닿으며, 한 줄이던 것이 네 줄이 된다.

before (`03d80feed0f` 기준 `ThrowawayClassLoader.java:56-58`):

```java
			catch (ClassNotFoundException ex) {
				return loadClassFromResource(name);
			}
```

after (`upstream/main` 기준 `ThrowawayClassLoader.java:56-62`):

```java
			catch (ClassNotFoundException ex) {
				Class<?> loadedFromResource = loadClassFromResource(name);
				if (loadedFromResource == null) {
					throw ex;
				}
				return loadedFromResource;
			}
```

**왜 그 위치인가.** null은 `:66`에서 태어나지만, 그 null이 "정당한 내부 신호"에서 "계약 위반"으로 성격이 바뀌는 지점은 `:57`, 즉 private 헬퍼의 반환값이 protected 계약 표면의 반환값이 되는 경계다. 번역기는 성격이 바뀌는 경계에 놓아야 한다. 덤으로 이 위치는 재전파할 `ex`가 이미 스코프 안에 있는 유일한 자리이기도 하다 — 헬퍼 안에서 고쳤다면 `ex`에 접근할 수 없어 정보가 빈약한 새 예외를 만들어야 했다.

검토된 대안과 기각 사유는 다음과 같다.

| 대안 | 형태 | 기각 사유 |
|---|---|---|
| 헬퍼 안에서 던지기 | `loadClassFromResource`의 `if (inputStream == null)` 자리에서 `throw new ClassNotFoundException(name)` | 메서드가 null-free가 되는 장점은 있으나, 2단계 위임 실패의 cause와 JDK가 붙인 상세가 사라진다. 진단 정보가 순손실 |
| `@Nullable` 표기만 추가 | `loadClassFromResource`에 `@Nullable Class<?>` | null 반환이라는 **계약 위반 자체를 고치지 않는다**. 게다가 이 패키지는 `@NullUnmarked`(`package-info.java:4`)라 표기해도 검사되지 않아 신호로도 작동하지 않는다 |
| 호출자 측 방어 | `provideFieldValue`에서 null 검사 | 계약을 지켜야 할 쪽은 로더다. 소비자마다 방어를 복제하게 되고, `PreComputeFieldFeature`의 `:99-100`은 계약을 신뢰한 **정상적인** 코드다 |
| 메서드명 변경 리팩터 | `loadClassFromResourceOrNull` 등 | 이름은 계약을 강제하지 못한다. 별건의 폴리시 |

**메인테이너 폴리시(`7b31e0c2dcd`)가 무엇을 바꿨는가.** 프로덕션 코드는 그대로 두고 테스트만 세 군데 손봤다. `@Test`에 `// gh-36938` 주석을 붙였고, 클래스명을 지역변수 `name`으로 뽑았으며, 단언에 `.withMessageContaining(name)`을 추가했다. 마지막 항목이 실질적이다 — 이 단언이 있으면 "원본 `ex`를 재전파한다"는 설계 선택이 테스트로 고정된다. 클래스명 없는 새 CNFE로 바꾸는 회귀가 들어오면 이 단언이 잡는다.

## 6. 범위 밖과 인접 영향

**같은 계열의 다른 로더는 이 계약을 지키고 있었다.** `OverridingClassLoader`(`spring-core/src/main/java/org/springframework/core/OverridingClassLoader.java`)는 구조가 거의 같지만 null 처리 방식이 다르다.

```java
	@Override
	protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
		if (isEligibleForOverriding(name)) {
			Class<?> result = loadClassForOverriding(name);
			if (result != null) {
				if (resolve) {
					resolveClass(result);
				}
				return result;
			}
		}
		return super.loadClass(name, resolve);
	}
```
(`upstream/main:86-97`)

`loadClassForOverriding`은 `@Nullable Class<?>`로 명시 표기되어 있고(`:118`), 그 null은 `:89`의 검사에 걸려 **`super.loadClass`로의 위임으로 번역된다** — 여기서도 null은 밖으로 새지 않는다. 폴백 순서가 반대(먼저 직접 정의, 실패하면 위임)라 번역 결과가 예외가 아니라 위임일 뿐, "내부 null은 경계에서 번역한다"는 원칙은 같다. `resolve` 인자도 이쪽은 `:90-92`에서 실제로 사용한다.

하위호환 영향은 없다고 본다. 클래스는 패키지 프라이빗, 패키지는 공개 API가 아니라고 선언되어 있고(`package-info.java:2`), 호출자는 저장소 안에 하나뿐이다. 반환값이 null이던 경로가 예외로 바뀌지만, 그 호출자의 `catch (Throwable)`(`PreComputeFieldFeature.java:80`)가 NPE든 CNFE든 동일하게 런타임 평가 폴백으로 처리하므로 관측 가능한 빌드 동작은 변하지 않는다.

인접 PR과의 관계: #36933이 같은 메서드 `loadClassFromResource`의 **자원 수명**(`:68`의 `try (inputStream)`)을 다뤘고, 이 PR은 같은 흐름의 **실패 표현**을 다룬다. 두 변경은 닿는 줄이 달라 충돌 없이 순차 머지되었고, PR 본문에서도 "#36933이 이미 7.1.0-M1 마일스톤으로 트리아지되었으므로 그 PR을 확장하지 않고 분리했다"고 명시했다. 현재 `ThrowawayClassLoaderTests`에는 두 PR의 테스트가 나란히 들어 있다.

이번에 손대지 않은, 확인은 되었으나 별건인 것들: `loadClass`가 `resolve` 인자를 무시하고 폴백으로 정의한 클래스에 `resolveClass`를 걸지 않는 점(기존 동작. `OverridingClassLoader`와 대비된다), `loadClassFromResource`에 `@Nullable` 표기가 없는 점(패키지가 `@NullUnmarked`라 표기의 효력이 없다).
