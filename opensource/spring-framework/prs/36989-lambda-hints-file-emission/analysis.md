# PR #36989 분석 — lambda 힌트만 있을 때 네이티브 설정 파일이 생성되지 않는 문제

> 기준 상태. **수정 전** = `d1470bbb259^`, **수정 커밋** = `d1470bbb259`, **현재** = `upstream/main`(`7daf1013aa8`). 파일:줄 인용마다 어느 상태 기준인지 밝힌다.
> 이 문서의 자리: README(서사)·structure(두 패키지의 대칭 구조도)·tests(테스트 해설)·gates(이해 게이트 기록)와 겹치지 않게, **게이트와 방출기가 각각 아는 "힌트 종류 목록"을 전수 대조**하고 이름표·단계 단위로 고정한다.

## 0. 결론

`NativeConfigurationWriter.write(RuntimeHints)`는 `hasAnyHint(hints)`가 참일 때만 `reachability-metadata.json`을 쓰는데, 그 `hasAnyHint`가 힌트 종류를 손으로 나열한 OR 사슬이면서 **`ReflectionHints.lambdaHints()`를 목록에 빠뜨렸다**. 그 결과 lambda 힌트만 담긴 `RuntimeHints`는 "힌트 없음"으로 판정되어 파일이 아예 만들어지지 않고, 직렬화 계층이 이미 지원하던 lambda 메타데이터가 조용히 사라졌다.

수정은 OR 사슬에 `hints.reflection().lambdaHints().findAny().isPresent() ||` 한 줄을 넣어 게이트의 목록을 방출기의 목록과 일치시킨 것이다.

상태: 머지됨. `upstream/main`의 커밋 `d1470bbb259`("Register native configuration file when only lambda hints are present", `Closes gh-36989`). 실패는 예외도 로그도 남기지 않고 JVM 테스트로도 드러나지 않으며, **네이티브 이미지 런타임에 가서야** 누락된 힌트에 의존하던 동작이 깨지는 형태로 나타난다.

## 1. 무대

결함은 힌트를 모으는 패키지와 그것을 JSON으로 옮기는 패키지 사이의 관문에 있다. 그 좌표를 여섯 항목으로 고정한다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 결함 클래스 | `NativeConfigurationWriter` (**public abstract**, `org.springframework.aot.nativex`, `@since 6.0`) |
| 결함 메서드 | `hasAnyHint(RuntimeHints)` (**private**) |
| 공개 진입 API | `NativeConfigurationWriter.write(RuntimeHints)` (`:39`) |
| 유일한 구현 | `FileNativeConfigurationWriter` (파일 출력) |
| 반대편 패키지 | `org.springframework.aot.hint` — 힌트를 자바 객체로 모으는 쪽 |

무대의 형태는 **두 패키지가 같은 목록을 각자 알고 있어야 하는 구조**다. `aot.hint`가 힌트 종류를 정의하고, `aot.nativex`가 그 종류를 JSON으로 옮긴다. `aot.nativex` 안에서도 책임이 둘로 갈린다 — **방출기**(`RuntimeHintsWriter` + `ReflectionHintsAttributes` + `ResourceHintsAttributes`)는 "어떻게 직렬화할지"를 알고, **게이트**(`hasAnyHint`)는 "쓸 만한 내용이 있는지"를 판정한다. 결함은 이 둘의 목록이 어긋난 데서 나왔다.

호출 시점은 #36972와 같다 — 빌드 타임 AOT 처리의 마지막 단계인 `AbstractAotProcessor.writeHints(RuntimeHints)`(`spring-context/.../AbstractAotProcessor.java:124-128`)가 writer를 만들어 `write(hints)`를 부른다. 빌드 한 번에 한 번이다.

## 2. 전체 메서드 그래프

현재(`upstream/main`) 줄번호이며, 수정 전 형태가 필요한 곳은 표시했다.

```
 빌드 타임 (Gradle/Maven AOT 플러그인)
   |
   v
 AbstractAotProcessor.writeHints(hints)                    AbstractAotProcessor.java:124-128
   v
 NativeConfigurationWriter.write(hints)              NativeConfigurationWriter.java:39
   |
   +-- if (hasAnyHint(hints))                                                  :40
   |      |
   |      v
   |    hasAnyHint(hints)   [!] 결함 위치                                        :46
   |      hints.proxies().jdkProxyHints()          .findAny().isPresent()      :47
   |      hints.reflection().typeHints()           .findAny().isPresent()      :48
   |      hints.reflection().lambdaHints()         .findAny().isPresent()      :49  <-- 수정으로 추가
   |         (수정 전에는 이 줄이 통째로 없었다)
   |      hints.resources().resourcePatternHints() .findAny().isPresent()      :50
   |      hints.resources().resourceBundleHints()  .findAny().isPresent()      :51
   |      hints.jni().typeHints()                  .findAny().isPresent()      :52
   |      hasAnyDeprecatedHint(hints)                                          :53
   |         hints.serialization().javaSerializationHints().findAny()...       :58
   |      -> 단락 평가(||): 첫 true에서 종료, 전부 false면 false
   |
   +-- true  --> writeTo("reachability-metadata.json", 콜백)                    :41-42
   |               |
   |               v
   |             FileNativeConfigurationWriter.writeTo(...)  FileNativeConfigurationWriter.java:60
   |               file 생성 -> FileWriter(UTF_8) -> BasicJsonWriter            :62-64
   |               |
   |               v
   |             RuntimeHintsWriter.write(jsonWriter, hints)   RuntimeHintsWriter.java:37
   |               document["comment"]    <- SpringVersion.getVersion()         :39-41
   |               document["reflection"] <- ReflectionHintsAttributes.reflection(hints)  :43-46
   |                   |  reflectionHints(hints)              ReflectionHintsAttributes.java:82
   |                   |    typeHints().map(toAttributes)                       :83-85
   |                   |    + javaSerializationHints() 병합                      :86-92
   |                   |    + Stream.concat(정렬 타입힌트,
   |                   |         lambdaHints().sorted(LAMBDA_HINT_COMPARATOR)
   |                   |                      .map(this::toAttributes))         :93-95  <-- lambda는 여기서 "이미" 처리됨
   |                   |         toAttributes(LambdaHint) -> {"type":{"lambda":{...}}}  :118-133
   |                   +  jdkProxyHints().sorted(...).map(toAttributes)          :75-77
   |               document["jni"]        <- ReflectionHintsAttributes.jni(hints)  :47-50
   |                   |  hints.jni().typeHints()만 사용                          :98-104
   |               document["resources"]  <- ResourceHintsAttributes.resources(...)  :51-54
   |                   |  resourcePatternHints + resourceBundleHints            ResourceHintsAttributes.java:54-60
   |               writer.writeObject(document)                                 :56
   |               v
   |             디스크: META-INF/native-image/reachability-metadata.json
   |
   +-- false --> 아무것도 하지 않음. 예외 없음 / 로그 없음 / 파일 없음            :40
                 [!] lambda 전용 hints가 수정 전에 떨어지던 자리
```

이 그래프의 핵심은 **`writeTo` 아래의 모든 코드가 lambda를 이미 알고 있었다**는 것이다(`:93-95`, `:118-133`). 결함은 직렬화 능력의 부재가 아니라 그 능력에 도달하지 못하게 막는 문 하나였고, 그래서 수정이 한 줄로 끝난다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 지점은 셋이다. (1) `RuntimeHints.reflection()`과 `RuntimeHints.jni()`가 **같은 타입의 다른 인스턴스**라는 것, (2) `lambdaHints`가 `ReflectionHints` 안에 `types`와 나란히 사는 **두 번째 컬렉션**이라는 것, (3) 게이트와 방출기가 각자 목록을 들고 있다는 것.

| 이름표 | 무엇인가 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `write(RuntimeHints)` (`NativeConfigurationWriter.java:39`) | 공개 진입 API. 게이트 판정 후 방출 | `RuntimeHints` -> 없음(부작용: 파일) | `AbstractAotProcessor.writeHints` | 결함이 관측되는 표면 — "파일이 없다"가 곧 증상 |
| `hasAnyHint(hints)` (`:46`) | **쓰기 게이트.** 종류별 존재 검사를 `\|\|`로 이은 사슬 | `RuntimeHints` -> boolean | `write`가 매번 | **결함이 사는 메서드.** 목록이 방출기보다 좁았다 |
| `hasAnyDeprecatedHint(hints)` (`:57-59`) | 폐기 예정 `serialization` 종류만 분리한 보조 판정 | `RuntimeHints` -> boolean | `hasAnyHint` 마지막 항 | `@SuppressWarnings("removal")`을 한 곳에 가두려고 분리된 것. 결함과 무관 |
| `findAny().isPresent()` | "적어도 하나 있나"의 순수 존재 검사 | `Stream` -> boolean | 각 항 | 부작용 없고 비용도 사실상 상수. 항을 추가해도 성능 문제가 없다는 근거 |
| `\|\|` 단락 평가 | 첫 true에서 나머지를 평가하지 않음 | - | - | **무회귀 논증의 핵심.** OR에 항을 더하면 true가 되는 입력만 늘고 기존 true가 false로 뒤집히지 않는다 |
| `RuntimeHints` (`RuntimeHints.java:34`) | 다섯 하위 묶음의 소유자 | - | AOT 처리 전반 | **`isEmpty()` 같은 메서드가 없다.** 그래서 게이트가 종류 목록을 손으로 복제할 수밖에 없었다 |
| `RuntimeHints.reflection` (`:36`) | `ReflectionHints` 인스턴스 하나 | -> `ReflectionHints` | `reflection()` (`:52`) | `types`와 `lambdaHints` 둘을 품는다 |
| `RuntimeHints.jni` (`:45`) | **또 하나의 `ReflectionHints` 인스턴스** | -> `ReflectionHints` | `jni()` (`:87`) | 타입이 같아 `jni().lambdaHints()`도 문법적으로 가능하다. 6장에서 다룬다 |
| `ReflectionHints.types` (`ReflectionHints.java:48`) | `Map<TypeReference, TypeHint.Builder>` | - | `registerType` 계열 4개 오버로드 | 게이트가 원래부터 검사하던 컬렉션 |
| `ReflectionHints.lambdaHints` (`:50`) | `Set<LambdaHint>` — `types`와 **나란히 놓인 두 번째 상태** | - | `registerLambda` | **게이트가 몰랐던 컬렉션.** 같은 클래스 안에 있어 "reflection을 검사했으니 됐다"는 착시가 생긴다 |
| `typeHints()` (`:56`) | `types.values().stream().map(Builder::build)` | -> `Stream<TypeHint>` | 게이트 `:48`, 방출기 `:83` | 게이트와 방출기 양쪽이 부르는 정상 짝 |
| `lambdaHints()` (`:66`, `@since 7.0.6`) | `lambdaHints.stream()` | -> `Stream<LambdaHint>` | 수정 전: 방출기(`:95`)만. 수정 후: 게이트(`:49`)도 | **비대칭의 증거.** 접근자는 있었고 방출기는 쓰고 있었는데 게이트만 안 썼다 |
| `registerLambda(TypeReference, Consumer<Builder>)` (`:265-271`) | 빌더를 만들어 소비자에게 넘기고 결과를 `lambdaHints`에 add | 선언 클래스 + 빌더 콜백 -> `this` | 프레임워크·사용자 AOT 코드 | 결함 상태를 만드는 유일한 통로 |
| `registerLambda(Class, Consumer<Builder>)` (`:279-281`) | 위 오버로드로 위임 | - | 상동 | 테스트가 쓰는 형태 |
| `LambdaHint` (`LambdaHint.java:31`) | `declaringClass`(`:33`) / `reachableType`(`:35`) / `declaringMethod`(`:37`) / `interfaces`(`:39`)를 담은 final 클래스 | - | - | 저장되는 값. 게이트는 내용이 아니라 **존재 여부만** 본다 |
| `LambdaHint.DeclaringMethod` (`:183`) | `record (String name, List<TypeReference> parameterTypes)` | - | `toAttributes`(`:122-127`) | JSON의 `declaringMethod` 하위 객체가 되는 값 |
| `LAMBDA_HINT_COMPARATOR` (`ReflectionHintsAttributes.java:67-70`) | declaringClass -> declaringMethod.name 순 정렬자 | - | `:95` | 방출기가 lambda를 **1급으로 다루고 있었다는 증거** |
| `toAttributes(LambdaHint)` (`:118-133`) | `{"type": {"lambda": {...}}}` 맵 생성 | `LambdaHint` -> `Map` | `:95` | 게이트만 열리면 곧바로 동작하는 준비된 코드 |
| `reflectionHints(RuntimeHints)` (`:82-96`) | 타입 힌트 + 자바 직렬화 힌트 병합 + lambda 힌트 concat | `RuntimeHints` -> `List<Map>` | `reflection(hints)` (`:73`) | **방출기의 목록**이 여기 다 있다. 게이트와 대조할 기준표 |
| `jni(RuntimeHints)` (`:98-104`) | `hints.jni().typeHints()`만 직렬화 | `RuntimeHints` -> `List<Map>` | `RuntimeHintsWriter.write` `:47` | jni 쪽 lambda는 **방출도 하지 않는다** — 6장의 판정 근거 |
| `document["comment"]` (`RuntimeHintsWriter.java:39-41`) | 항상 들어가는 스프링 버전 주석 | -> `String` | 방출기 첫 줄 | **게이트가 왜 필요한가**의 답. 방출기만으로는 빈 힌트에도 `{"comment": ...}`짜리 파일이 생긴다 |
| `emptyConfig` 테스트 (`FileNativeConfigurationWriterTests.java:58-62`) | 빈 `RuntimeHints`로 write 시 파일이 없어야 함 | - | 테스트 | 게이트의 **반대편 계약**을 고정. 수정이 이 테스트를 깨지 않아야 한다 |

## 3. 결함 경로 단계 추적

lambda 힌트를 **하나만** 등록한 경우와, lambda + 타입 힌트를 함께 등록한 경우를 나란히 보면 결함이 왜 오래 숨어 있었는지가 드러난다. 후자는 수정 전에도 정상 동작한다.

| 단계 | 케이스 A: lambda 힌트만 (수정 전) | 케이스 B: lambda + 타입 힌트 (수정 전) | 케이스 A (수정 후) |
|---|---|---|---|
| 등록 | `registerLambda(Integer.class, ...)` | 같은 lambda + `registerType(String.class, ...)` | `registerLambda(Integer.class, ...)` |
| 상태 | `types = {}`, `lambdaHints = {LambdaHint(Integer,...)}` | `types = {String}`, `lambdaHints = {LambdaHint(...)}` | 케이스 A와 동일 |
| 게이트 `:47` jdkProxy | false | false | false |
| 게이트 `:48` typeHints | false | **true -> 단락 평가로 즉시 종료** | false |
| 게이트 `:49` lambdaHints | (항 자체가 없음) | (평가되지 않음) | **true -> 종료** |
| 게이트 `:50-53` 나머지 | 전부 false | (평가되지 않음) | (평가되지 않음) |
| `hasAnyHint` 결과 | **false** | true | **true** |
| `writeTo` 호출 | **안 됨** | 됨 | 됨 |
| 방출기 도달 | 안 됨 | 도달 — `:95`가 lambda를 정상 직렬화 | 도달 |
| 디스크 | **파일 없음** | 파일 있음, lambda JSON 포함 | 파일 있음, lambda JSON 포함 |
| 관측되는 신호 | **없음**(예외·로그·경고 전무, 빌드 초록) | - | - |
| 최종 결과 | 네이티브 이미지 런타임에서 해당 lambda 관련 동작 실패 | 정상 | 정상 |

케이스 B의 행 "게이트 `:48`"이 은폐의 메커니즘이다. 실제 애플리케이션의 `RuntimeHints`에는 거의 항상 타입 힌트가 섞여 있으므로 게이트는 다른 항에서 참이 되고, lambda는 그 뒤에 얹혀 정상적으로 직렬화된다. 결함이 드러나려면 **lambda 힌트만 단독으로** 존재해야 하고, 그래서 회귀 테스트도 lambda 하나만 등록하는 형태여야 한다 — 다른 힌트를 섞으면 게이트가 다른 항으로 열려 버그가 가려진다.

수정 전 상태에서 그 테스트를 돌리면 실패 신호는 단언 실패가 아니라 `NoSuchFileException`이다. `assertEquals` 헬퍼(`FileNativeConfigurationWriterTests.java:234-238`)가 `Files.readString(jsonFile)`로 파일을 먼저 읽기 때문이다. 즉 "내용이 다르다"가 아니라 "파일이 없다"로 떨어진다.

## 4. 계약

이 결함을 둘러싼 계약은 다섯 개이고, 그중 명시된 문서가 없는 첫 번째 암묵 불변식만 깨진다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| **방출기가 JSON으로 내보낼 수 있는 모든 힌트 종류는 게이트 판정에 포함되어야 한다** | 명시된 문서는 없다. `write`(`:39-44`)의 구조 자체가 만드는 암묵 불변식 | **어긴다** — 게이트가 방출기의 진부분집합이었다 |
| 힌트가 전혀 없으면 파일도 만들지 않는다 | `emptyConfig` 테스트(`FileNativeConfigurationWriterTests.java:58-62`)가 고정 | 어기지 않는다. 수정 후에도 빈 `RuntimeHints`는 모든 항이 false라 파일이 생기지 않는다 |
| lambda 힌트는 `{"type": {"lambda": {...}}}` 형태로 직렬화된다 | `ReflectionHintsAttributes.toAttributes(LambdaHint)`(`:118-133`) + `RuntimeHintsWriterTests.oneLambda`(`RuntimeHintsWriterTests.java:314`)가 고정 | 어기지 않는다 — **이미 지켜지고 있었다.** 이 계약이 이미 있었다는 사실이 "게이트만 고치면 된다"의 근거 |
| 문서에는 항상 `"comment"`가 들어간다 | `RuntimeHintsWriter.java:39-41` | 결함이 아니라 **게이트의 존재 이유**. 방출기에게 "비었으면 아무것도 쓰지 마라"를 맡길 수 없다 |
| OR 사슬에 항을 추가해도 기존 판정은 뒤집히지 않는다 | 논리합의 성질 | 수정이 이 성질에 **의존**한다 — 다른 다섯 종류와 `emptyConfig`의 무회귀 근거 |

기존 테스트가 고정하지 **않던** 것: "특정 종류의 힌트만 있을 때 파일이 생기는가". `FileNativeConfigurationWriterTests`의 기존 테스트들(`serializationConfig`·`proxyConfig`·`reflectionConfig`·`jniConfig`·`resourceConfig`)은 각자 한 종류만 등록해 사실상 이 성질을 종류별로 검증하고 있었는데, **lambda만 그 목록에 없었다.** 결함과 테스트 공백이 정확히 같은 모양이다.

## 5. 수정안

프로덕션 diff는 OR 사슬에 항 하나를 더하는 한 줄이다.

before (`d1470bbb259^` 기준 `NativeConfigurationWriter.java:46-53`):

```java
	private boolean hasAnyHint(RuntimeHints hints) {
		return (hints.proxies().jdkProxyHints().findAny().isPresent() ||
				hints.reflection().typeHints().findAny().isPresent() ||
				hints.resources().resourcePatternHints().findAny().isPresent() ||
				hints.resources().resourceBundleHints().findAny().isPresent() ||
				hints.jni().typeHints().findAny().isPresent() ||
				hasAnyDeprecatedHint(hints));
	}
```

after (`upstream/main` 기준 `NativeConfigurationWriter.java:46-54`):

```java
	private boolean hasAnyHint(RuntimeHints hints) {
		return (hints.proxies().jdkProxyHints().findAny().isPresent() ||
				hints.reflection().typeHints().findAny().isPresent() ||
				hints.reflection().lambdaHints().findAny().isPresent() ||
				hints.resources().resourcePatternHints().findAny().isPresent() ||
				hints.resources().resourceBundleHints().findAny().isPresent() ||
				hints.jni().typeHints().findAny().isPresent() ||
				hasAnyDeprecatedHint(hints));
	}
```

**왜 그 위치인가.** 두 층위의 "위치"가 있다. 메서드 층위에서는, 결함이 "직렬화가 안 된다"가 아니라 "직렬화에 도달하지 못한다"이므로 고칠 곳은 방출기가 아니라 게이트다 — 방출기 쪽 `:95`·`:118-133`은 이미 옳다. 줄 층위에서는, 새 항을 같은 `reflection()` 소속인 `typeHints` 바로 뒤(`:49`)에 넣었다. 사슬이 "소유자별로 묶여 읽히는" 배치(proxies / reflection / resources / jni / deprecated)를 유지하기 위해서다.

검토된 대안과 기각 사유는 다음과 같다.

| 대안 | 형태 | 기각 사유 |
|---|---|---|
| `RuntimeHints`에 `isEmpty()` 추가 | 힌트 모델이 스스로 "비었는가"를 답하게 하고 게이트는 그것만 호출 | 구조적으로는 더 옳지만 **public API 추가**이고 blast radius가 크다. 이 PR이 고쳐야 할 결함은 한 종류의 누락이며, API 확장은 별개 판단 |
| `reflection()` 하위 종류를 묶는 헬퍼 메서드로 리팩터 | `hasAnyReflectionHint(hints)` 같은 중간 메서드 | 구조 정리 효과는 있으나 계약이 달라지지 않고 diff만 넓어진다 |
| 방출기 쪽에서 빈 문서를 감지해 파일을 지우기 | 게이트를 없애고 사후 판정 | `"comment"`가 항상 들어가므로(`RuntimeHintsWriter.java:39-41`) "빈 문서" 판정 자체가 별도 규칙을 요구한다. 파일을 만들었다 지우는 것도 부작용이 크다 |
| 파일 존재만 단언하는 가벼운 테스트 | `namespace` 테스트 스타일 | 파일 생성은 잡지만 lambda JSON이 실제로 흘러가는지를 검증하지 못한다. 기존 `assertEquals` 헬퍼로 전체 JSON을 대조하는 편이 계약을 더 넓게 고정 |

**수정이 기존 동작을 깨지 않는 이유**는 논리합의 성질 하나로 끝난다. OR 사슬에 항(disjunct)을 추가하면 결과가 false에서 true로 바뀌는 입력만 늘고, true였던 입력이 false가 되는 경우는 없다. 따라서 다른 다섯 종류의 판정과 `emptyConfig`(전 항 false -> 여전히 false)는 그대로다.

## 6. 범위 밖과 인접 영향

**게이트와 방출기의 목록을 전수 대조했다.** 수정 후 기준으로 두 목록은 다음과 같이 일치한다.

| 힌트 종류 | 방출기가 직렬화하는가 | 게이트가 검사하는가 (수정 후) |
|---|---|---|
| `proxies().jdkProxyHints()` | 예 — `ReflectionHintsAttributes.java:75-77` | 예 — `:47` |
| `reflection().typeHints()` | 예 — `:83-85` | 예 — `:48` |
| `reflection().lambdaHints()` | 예 — `:93-95` | 예 — `:49` (**이 PR이 추가**) |
| `serialization().javaSerializationHints()` (폐기 예정) | 예 — `:86-92` | 예 — `:53` -> `:58` |
| `resources().resourcePatternHints()` | 예 — `ResourceHintsAttributes.java:54-57` | 예 — `:50` |
| `resources().resourceBundleHints()` | 예 — `:58-60` | 예 — `:51` |
| `jni().typeHints()` | 예 — `ReflectionHintsAttributes.java:98-104` | 예 — `:52` |
| `jni().lambdaHints()` | **아니오** — `jni(RuntimeHints)`(`:98-104`)는 `typeHints()`만 읽는다 | 아니오 |

마지막 행이 이번 조사에서 확인한 중요한 판정이다. `RuntimeHints.jni`는 `reflection`과 **같은 `ReflectionHints` 타입**(`RuntimeHints.java:45`)이므로 `jni().lambdaHints()`도 문법적으로는 호출할 수 있고, 게이트에 그 항이 없는 것이 얼핏 두 번째 누락처럼 보인다. 그러나 방출기가 jni 쪽 lambda를 직렬화하지 않으므로 게이트가 그것을 참으로 판정하면 오히려 **내용 없는 파일**이 생긴다. 즉 여기서는 게이트가 방출기와 일치하는 것이 맞고, 이 PR의 범위 밖일 뿐 아니라 고치면 안 되는 자리다. (jni lambda 힌트를 등록할 수 있는데 직렬화되지 않는 것이 그 자체로 결함인지는 별개 문제이며 이번에 판정하지 않았다 — 미확인.)

하위호환 영향은 없다고 본다. `hasAnyHint`는 private이고, 변경은 판정이 참이 되는 입력 집합을 넓히기만 한다. 이전에 파일이 만들어지던 모든 입력에서 여전히 만들어지고 내용도 같다.

구조적 교훈이 하나 남는다. 이 게이트는 "힌트가 있는가"를 힌트 모델에게 묻지 않고 **자기가 아는 종류를 손으로 나열해** 묻는다. `RuntimeHints`에 `isEmpty()`가 없으므로(`RuntimeHints.java:34-91`) 이 열거는 모델의 종류 목록을 복제한 코드이고, 새 종류가 추가될 때 함께 갱신되지 않으면 조용히 틀린다. 컴파일러는 이 커플링을 강제하지 못한다 — 양쪽 다 정상적으로 컴파일된다. 실제로 lambda 힌트는 `@since 7.0.6`으로 나중에 들어왔고(`ReflectionHints.java:66`, `:265`), 방출기에는 반영되었으나 게이트에는 반영되지 않았다. 회귀 방지는 "그 종류만 가진 hints가 파일로 써지는가" 형태의 테스트로만 담보되며, 기존 테스트들이 종류별로 정확히 그 형태였다는 점(4장)이 이 방식의 유효성을 보여 준다.

인접 PR과의 관계: 같은 파일 계층의 한 층 아래, `FileNativeConfigurationWriter.writeTo`의 출력 인코딩 결함이 #36972로 먼저 처리되었다. 이 PR이 "쓸 것인가 말 것인가"라면 #36972는 "쓸 때 어떻게 쓰는가"이며, 두 결함은 같은 `write` 호출 사슬 위의 서로 다른 관문에 있었다.
