# PR #36933 분석 — ThrowawayClassLoader의 클래스 리소스 스트림 미해제

> 기준 상태 세 가지를 구분해 쓴다. **수정 전** = `03d80feed0f^`, **수정 커밋** = `03d80feed0f`, **현재** = `upstream/main`(`7daf1013aa8`, #36938까지 반영된 상태). 파일:줄 인용마다 어느 상태 기준인지 밝힌다.
> 이 문서의 자리: README(왜 이런 물건인가의 서사)·structure(클래스 구조도)·tests(테스트 해설)와 겹치지 않도록, 호출 그래프 위에 놓인 **이름표 하나하나의 역할**과 **결함 경로의 단계별 상태**를 고정하는 데 집중한다.

## 0. 결론

`ThrowawayClassLoader.loadClassFromResource`가 `getResourceAsStream(...)`으로 연 `InputStream`을 성공 출구(`defineClass` 반환)와 예외 출구(`IOException` -> `ClassNotFoundException`) 어디에서도 닫지 않아, native-image 빌드 한 번 동안 이 경로가 도는 횟수만큼 OS 자원(파일 디스크립터 또는 jar zip 엔트리와 네이티브 inflater 버퍼)이 GC 시점까지 붙들린다.

수정은 이미 실질적 final인 지역변수 `inputStream`을 try-with-resources의 **자원으로 채택**(`try (inputStream)`)해, 로딩 로직을 한 글자도 건드리지 않고 모든 출구에 닫기를 붙인 것이다.

상태: 머지됨. `upstream/main`의 커밋 `03d80feed0f`("Close class resource InputStream in ThrowawayClassLoader", `Closes gh-36933`). GitHub PR 상태값은 `CLOSED`이고 `mergeCommit`은 비어 있는데, 이는 스프링이 기여 커밋을 직접 적용한 뒤 PR을 닫는 운영 방식 때문이다.

## 1. 무대

결함이 사는 클래스와 그것을 부르는 유일한 소비자를 먼저 좌표로 고정한다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 패키지 | `org.springframework.aot.nativex.feature` |
| 패키지 성격 | `package-info.java:1-5` — "GraalVM native image features, **not part of Spring Framework public API**" + `@NullUnmarked` |
| 결함 클래스 | `ThrowawayClassLoader` (패키지 프라이빗, `@since 6.0`) |
| 결함 메서드 | `loadClassFromResource(String)` (private) |
| 유일한 소비자 | `PreComputeFieldFeature` (같은 패키지, GraalVM `Feature` 구현) |

공개 진입 API는 없다. 이 클래스는 사용자가 직접 부르는 물건이 아니라, GraalVM `native-image` 컴파일러가 빌드 도중 `Feature` SPI로 `PreComputeFieldFeature`를 깨우면 그 안에서 간접적으로 도는 내부 부품이다. 따라서 "누가 부르나"의 답은 사람이 아니라 **네이티브 이미지 빌드 파이프라인**이며, 실행 횟수는 "도달 가능한 모든 타입 x 패턴에 걸리는 static final boolean 필드 수"에 비례한다.

## 2. 전체 메서드 그래프

수정 전(`03d80feed0f^`) 기준 줄번호다. 화살표는 호출 방향, 괄호 안은 그 지점을 통과하는 값이다.

```
 GraalVM native-image 빌드 (Feature SPI)
   |
   v
 PreComputeFieldFeature.beforeAnalysis(access)                       PreComputeFieldFeature.java:56
   |  access.registerSubtypeReachabilityHandler(this::iterateFields, Object.class)   :57
   |     -> 도달 가능한 "모든" 타입마다 콜백
   v
 PreComputeFieldFeature.iterateFields(access, subtype)                              :61
   |  for (Field field : subtype.getDeclaredFields())                               :63
   |    static && final && (boolean|Boolean) && !enumConstant 만 통과                :64-68
   |    fieldIdentifier = 선언클래스명 + "#" + 필드명                                :69
   |    for (Pattern p : patterns)  p.matcher(fieldIdentifier).matches()             :70-71
   |       (patterns = NativeDetector#inNativeImage 등 7개                           :42-50)
   |    try { provideFieldValue(field) } catch (Throwable ex) { 런타임 평가로 폴백 }  :72-85
   v
 PreComputeFieldFeature.provideFieldValue(field)                                    :96
   |  Class<?> throwawayClass = this.throwawayClassLoader.loadClass(선언클래스명)     :99
   |  throwawayClass.getDeclaredField(...) -> setAccessible -> get(null)             :100-102
   v
 ThrowawayClassLoader.loadClass(name, resolve)          ThrowawayClassLoader.java:47  (수정 전)
   |  synchronized (getClassLoadingLock(name))                                       :48
   |  [1] findLoadedClass(name) != null -> 반환                                       :49-52
   |  [2] try { return super.loadClass(name, true) }   (부모 = 조부모 체인)           :53-55
   |  [3] catch (ClassNotFoundException ex) { return loadClassFromResource(name) }    :56-58
   v
 ThrowawayClassLoader.loadClassFromResource(name)                                    :62   [!] 결함 위치
   |  resourceName = name.replace('.', '/') + ".class"                               :63
   |  inputStream = this.resourceLoader.getResourceAsStream(resourceName)  <-- 자원 획득 :64
   |  if (inputStream == null) return null;                                          :65-67
   |  try {                                        <-- 자원 등록이 없다               :68
   |     outputStream = new ByteArrayOutputStream()                                  :69
   |     inputStream.transferTo(outputStream)       <-- 여기서만 읽고                 :70
   |     bytes = outputStream.toByteArray()                                          :71
   |     return defineClass(name, bytes, 0, bytes.length)   ===> 출구 A (닫지 않음)   :72
   |  }
   |  catch (IOException ex) {
   |     throw new ClassNotFoundException(...)             ===> 출구 B (닫지 않음)    :75-77
   |  }
   |  (defineClass가 ClassFormatError를 던지면)             ===> 출구 C (닫지 않음)
   v
 this.resourceLoader (= PreComputeFieldFeature를 로드한 앱 클래스로더)
   |  jar 클래스패스면: 열린 zip 엔트리 + 네이티브 inflater 버퍼
   |  디렉터리 클래스패스면: 파일 디스크립터
```

데이터 흐름의 요점은 `inputStream`이 `:64`에서 태어나 `:70`에서 소비되고, 그 뒤 **어느 출구에서도 참조되지 않는다**는 것이다. 참조가 끊기므로 자바 객체로서는 GC 대상이 되지만, 그 아래에 매달린 OS 핸들은 GC가 언제 수거하느냐에 운명이 달린다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 지점은 "클래스로더가 세 개(조부모, resourceLoader, ThrowawayClassLoader 자신)"라는 것과, "스트림이 두 겹(원본과 그것을 감싼 테스트용 추적기)"이라는 것이다. 아래는 결함 경로에 등장하는 모든 이름을 그 관점에서 정리한 것이다.

| 이름표 | 무엇인가 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `PreComputeFieldFeature.patterns` | 값을 미리 계산할 필드를 고르는 정규식 7개 (`:42-50`) | (없음) -> `Pattern[]` | 클래스 로딩 시 1회 초기화 | 이 패턴에 걸리는 필드 수가 곧 결함 경로 실행 횟수 |
| `PreComputeFieldFeature.throwawayClassLoader` | `new ThrowawayClassLoader(getClass().getClassLoader())` (`:52`) | (없음) -> 로더 1개 | 인스턴스 생성 시 1회 | **인스턴스가 하나뿐**이라 누수가 한 로더에 누적된다 |
| `iterateFields(access, subtype)` | 도달 가능한 타입 하나의 필드를 훑는 콜백 (`:61`) | 타입 -> 없음(부작용: 필드값 등록) | GraalVM이 타입마다 | 결함 경로를 반복 구동하는 루프 |
| `provideFieldValue(field)` | 일회용 로더로 필드값을 실제로 읽는 곳 (`:96`) | `Field` -> `Object` | `iterateFields`가 패턴 매치마다 | `loadClass` 진입점 |
| `loadClass(name, resolve)` | 재정의된 3단 로딩 진입점 (`:47`) | 클래스명 -> `Class` 또는 CNFE | `provideFieldValue`가 필드마다 | 결함 메서드의 유일한 호출자 |
| `resolve` (파라미터) | JDK 계약상 "정의 후 링크할지" 플래그 | boolean -> (무시됨) | 상동 | 이 결함과 무관. `super.loadClass(name, **true**)`로 상수 전달되고 폴백 경로에서는 `resolveClass`가 아예 없다 — 기존 동작이며 이 PR의 범위 밖 |
| `getClassLoadingLock(name)` | 이름별 로딩 락 (`:48`) | 클래스명 -> 락 객체 | 매 `loadClass` | `registerAsParallelCapable()`(`:33-35`)과 짝. 병렬 빌드에서 같은 이름이 동시에 이 경로를 타지 않게 하지만, **다른** 이름들은 동시에 탈 수 있어 누수는 병렬로 누적된다 |
| `findLoadedClass(name)` -> `loaded` | 이 로더가 이미 정의한 클래스 조회 (`:49`) | 클래스명 -> `Class` 또는 null | 매 `loadClass` 첫 단계 | 두 번째 요청부터는 결함 경로에 **안 들어간다**. 즉 누수는 "서로 다른 클래스 수"만큼 |
| `super.loadClass(name, true)` | 조부모 체인 위임 (`:54`) | 클래스명 -> `Class` 또는 CNFE | 1단계가 miss일 때 | 앱 클래스패스가 빠진 체인이라 대상 클래스는 대개 실패 -> 이 실패가 결함 경로의 문 |
| `resourceLoader` (필드) | 생성자에 넘어온 로더 자체. 부모로 삼지 않고 **바이트 공급원**으로만 쓴다 (`:37`, `:42`) | (없음) -> `ClassLoader` | `loadClassFromResource`·`findResource` | 여기서 나온 스트림이 닫히지 않는 그 스트림 |
| 생성자 `ThrowawayClassLoader(parent)` | `super(parent.getParent())` — 부모 체인을 **한 칸 건너뛴다** (`:40-43`) | 로더 -> 인스턴스 | `PreComputeFieldFeature` 필드 초기화 | 이 배치 때문에 2단계가 실패하고 3단계(결함 경로)가 상시 실행된다 |
| `loadClassFromResource(name)` | 리소스에서 바이트를 읽어 직접 정의하는 폴백 (`:62`) | 클래스명 -> `Class` 또는 **null** | `loadClass`의 catch에서만 | 결함이 사는 메서드 |
| `resourceName` (지역) | `name.replace('.', '/') + ".class"` (`:63`) | 클래스명 -> 리소스 경로 | 상동 | 자원 획득의 키. 결함과 직접 관계 없음 |
| `inputStream` (지역) | `getResourceAsStream`이 돌려준 열린 스트림 (`:64`) | 리소스 경로 -> `InputStream` 또는 null | 상동 | **결함의 주인공**. 한 번 대입되고 재대입되지 않아 "실질적 final" — 그래서 `try (inputStream)`이 문법적으로 성립한다 |
| `if (inputStream == null)` | "그런 리소스가 없다"는 내부 신호로 null 반환 (`:65-67`) | -> null | 상동 | 이 조기 반환 때문에 자원 선언형 try-with-resources로 감싸려면 구조를 손봐야 한다(5장 대안 비교) |
| `outputStream` (지역) | 바이트를 모으는 메모리 버퍼 (`:69`) | -> `ByteArrayOutputStream` | 상동 | `ByteArrayOutputStream.close()`는 무의미(no-op)하므로 닫을 필요가 없는 쪽. 대비되는 존재 |
| `transferTo(outputStream)` | 스트림 전체를 버퍼로 옮김 (`:70`) | 스트림 -> 바이트 | 상동 | **읽기를 끝내도 스트림을 닫지 않는** JDK 메서드. 여기서 "다 읽었으니 끝"이라는 착시가 생긴다 |
| `bytes` (지역) | 클래스 파일 바이트 (`:71`) | -> `byte[]` | 상동 | `defineClass` 입력 |
| `defineClass(name, bytes, 0, len)` | 이 로더 소유의 새 `Class` 생성 (`:72`) | 바이트 -> `Class` | 상동 | 출구 A. 반환식 안에 있어 "반환 직전 정리"를 넣을 자리가 눈에 안 띈다 |
| `catch (IOException ex)` | 읽기 실패를 CNFE로 번역 (`:75-77`) | `IOException` -> CNFE | `transferTo` 실패 시 | 출구 B. **자원이 부족할 때 자원 반환이 가장 확실히 누락되는** 경로 |
| `ClassFormatError` (throws 선언) | `defineClass`가 던질 수 있는 Error (`:62`) | - | JVM | 출구 C. catch 대상이 아니라 그대로 전파되며, 수정 전에는 이 경로도 스트림을 남긴다 |
| `findResource(name)` | `resourceLoader.getResource(name)` 위임 (`:80-83`) | 리소스명 -> `URL` | JDK 리소스 조회 경로 | 스트림을 열지 않으므로 이 결함과 무관 |
| `TrackingInputStream` (테스트) | `close()` 호출을 `AtomicBoolean`에 기록하는 `FilterInputStream` | 스트림 -> 관측 가능한 스트림 | 회귀 테스트가 `getResourceAsStream` 재정의로 주입 | 보이지 않는 누수를 단언 가능한 신호로 바꾸는 장치 |

## 3. 결함 경로 단계 추적

누수는 "값이 틀린다"가 아니라 "정리가 빠진다"이므로, 관찰 대상은 반환값이 아니라 `inputStream`의 열림 상태다. 아래 표는 정상 클래스 하나(`org.springframework.core.NativeDetector`)가 지나갈 때 수정 전후가 각 단계에서 무엇이 다른지를 나란히 놓은 것이다.

| 단계 | 수행 내용 | 수정 전 `inputStream` 상태 | 수정 후 `inputStream` 상태 |
|---|---|---|---|
| 1. `loadClass` 진입 | `findLoadedClass` miss | (아직 없음) | (아직 없음) |
| 2. 위임 | `super.loadClass` -> CNFE(`ex`) | (아직 없음) | (아직 없음) |
| 3. 폴백 진입 | `loadClassFromResource(name)` | (아직 없음) | (아직 없음) |
| 4. 자원 획득 | `getResourceAsStream` | **열림** (jar 엔트리 + inflater 점유) | **열림** |
| 5. try 진입 | 수정 전 `try {` / 수정 후 `try (inputStream) {` | 열림, 자원 등록 **없음** | 열림, **자원으로 등록됨** |
| 6. 읽기 | `transferTo(outputStream)` | 열림(EOF 도달, 그러나 닫히지 않음) | 열림 |
| 7-A. 성공 출구 | `defineClass` 반환 | **열린 채 메서드 이탈** | try 블록 이탈 시 `close()` -> **닫힘** |
| 7-B. IOException 출구 | `throw new ClassNotFoundException(...)` | **열린 채 예외 전파** | `close()`가 catch보다 **먼저** 실행 -> 닫힘. 닫기 자체가 `IOException`이면 같은 catch에 잡혀 CNFE로 번역되고, 본문과 close가 동시에 실패하면 후자는 suppressed로 첨부 |
| 7-C. ClassFormatError 출구 | Error 전파 | **열린 채 이탈** | `close()` 후 Error 전파 |
| 8. 반복 | 다음 필드/다음 클래스 | 4번으로 돌아가 **누적** | 누적 없음 |

행 8이 이 결함의 성격을 규정한다. 한 번의 누수는 무해하지만, `registerSubtypeReachabilityHandler(..., Object.class)`(`PreComputeFieldFeature.java:57`)가 도달 가능한 전 타입을 훑기 때문에 4-7 사이클이 빌드 한 번에 반복해서 돈다. 그래서 증상은 "항상 터지는 버그"가 아니라 "빌드 규모가 커질수록 확률이 오르는 비결정적 고갈"의 형태를 띤다. 디스크립터 한도가 낮은 CI 컨테이너의 `Too many open files`, 윈도우에서 jar 파일이 잠겨 후속 단계의 삭제/교체가 막히는 현상, inflater 버퍼 누적에 의한 빌드 프로세스 메모리 증가가 그 세 방향이다. 다만 실제 빌드에서 이 세 증상 중 어느 것이 관측되었다는 보고는 이번 조사에서 확인하지 못했다(미확인) — PR은 "재현된 장애"가 아니라 "정적으로 확정된 자원 위생 결함"으로 제출되었다.

## 4. 계약

이 코드가 지켜야 하는 것들과, 결함이 어긴 것을 구분해 둔다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| 열린 `Closeable`은 성공·예외 모든 출구에서 닫는다 | 자바 자원 관리 관례. 같은 저장소의 `FileCopyUtils.copyToByteArray`가 `try (in)`으로 이를 구현(`FileCopyUtils.java:140-148`) | **어긴다** — 출구 A·B·C 전부 |
| `loadClassFromResource`는 성공 시 `Class`, 리소스 부재 시 null, 읽기 실패 시 CNFE | 메서드 시그니처 `throws ClassNotFoundException, ClassFormatError`(`:62`) + `:65-67`의 조기 반환 | 어기지 않는다 — 이 PR은 반환 계약을 건드리지 않는다(그쪽은 #36938의 무대) |
| 로딩 동작은 보존되어야 한다 | PR의 자기 제약("leaving the loading logic unchanged") | 수정이 `try` 한 줄에만 닿아 보존됨. 회귀 테스트의 `loaded.getName()` 단언이 이를 고정 |
| try-with-resources의 `close()`는 같은 `try` 문의 `catch`보다 먼저 실행된다 | JLS 14.20.3 | 수정이 이 규칙에 **의존**한다 — 닫기 중 발생한 `IOException`도 기존 `catch (IOException)`이 CNFE로 번역 |
| 이 패키지의 코드는 공개 API가 아니며 null 검사 대상도 아니다 | `package-info.java:1-5` (`@NullUnmarked`) | 결함과 무관하나, **정적 도구가 이 패키지를 검사하지 않는다**는 사실이 결함이 오래 남은 배경 |

기존 테스트가 고정하던 것은 아무것도 없었다. 이 클래스에는 테스트 파일 자체가 없었고, PR이 `ThrowawayClassLoaderTests`를 신규로 만들었다.

## 5. 수정안

수정 커밋 `03d80feed0f`의 프로덕션 diff는 정확히 두 줄이다(한 줄은 빈 줄 제거).

before (`03d80feed0f^` 기준 `ThrowawayClassLoader.java:68-74`):

```java
		try {
			ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
			inputStream.transferTo(outputStream);
			byte[] bytes = outputStream.toByteArray();
			return defineClass(name, bytes, 0, bytes.length);

		}
```

after (`upstream/main` 기준 `ThrowawayClassLoader.java:72-77`):

```java
		try (inputStream) {
			ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
			inputStream.transferTo(outputStream);
			byte[] bytes = outputStream.toByteArray();
			return defineClass(name, bytes, 0, bytes.length);
		}
```

**왜 그 위치인가.** 자원의 수명은 획득 지점(`:64`)에서 시작하지만, 정리를 붙일 수 있는 최소 침습 지점은 이미 존재하는 `try` 블록이다. 자바 9부터 실질적 final인 기존 변수를 이름만 적어 자원으로 채택할 수 있으므로(`try (inputStream)`), `:65-67`의 null 검사와 조기 반환을 그대로 둔 채 닫기만 추가된다. 즉 "구조 변경 0, 불변식 +1"이다.

검토된 대안과 기각 사유는 다음과 같다.

| 대안 | 형태 | 기각 사유 |
|---|---|---|
| 자원 선언형으로 감싸기 | `try (InputStream inputStream = this.resourceLoader.getResourceAsStream(resourceName)) { if (inputStream == null) return null; ... }` | 사전 조사 문서(`docs/plans/2026-06-13/spring-core-bug-hunt/B6-.../task.md`)의 최초 수정안이 이 형태였으나, null 검사와 조기 반환을 try 블록 **안으로** 옮겨야 해 diff가 넓어진다. 제출본은 채택형으로 좁혔다 |
| `finally { inputStream.close(); }` | 명시적 정리 블록 | 동작은 같으나 `close()`의 `IOException`을 또 처리해야 하고, suppressed 예외 첨부를 수동으로 못 한다 |
| `FileCopyUtils.copyToByteArray(inputStream)`로 교체 | 유틸이 닫아 준다(`FileCopyUtils.java:145`) | 로딩 로직 자체를 바꾸는 변경이라 PR의 자기 제약("loading logic unchanged")에 어긋난다. 더해 이 패키지는 `java.*`와 `org.graalvm.*` 외 import가 하나도 없어(`git grep '^import'`로 확인) 스프링 유틸 의존을 새로 들이는 셈이 된다 — 그 무의존이 의도된 설계인지는 미확인 |
| 수정하지 않음(빌드 타임 1회성이므로) | - | 사전 조사에서 한 번 "보류"로 판정되었다가, 추적 스트림으로 결정론적 red/green 테스트가 가능하다는 점이 확인되면서 진행으로 번복되었다 |

## 6. 범위 밖과 인접 영향

**같은 패턴을 저장소 전체에서 확인한 결과, 이 클래스가 예외적인 쪽이었다.** `getResourceAsStream`으로 클래스 바이트를 읽는 다른 지점들은 모두 닫고 있었다.

- `OverridingClassLoader.loadBytesForClass`(`upstream/main:139-153`)는 구조가 거의 동일하다 — `openStreamForClass`(`:162-165`)가 `getParent().getResourceAsStream(...)`을 돌려주고, null이면 조기 반환하고, 아니면 읽어서 바이트를 만든다. 차이는 읽기를 `FileCopyUtils.copyToByteArray(is)`(`:146`)에 맡긴다는 것뿐이고, 그 유틸이 `try (in)`으로 닫는다(`FileCopyUtils.java:145`). 즉 **직접 `transferTo`를 손으로 쓰면서 닫기를 잃어버린 것**이 이 결함의 형태다.
- 재패키징된 cglib 사본도 닫는다. `DuplicatesPredicate`(`:91-99`)는 `try { ... } finally { is.close(); }`를 쓴다.

하위호환 영향은 없다고 본다. 클래스는 패키지 프라이빗이고 패키지 자체가 공개 API가 아니라고 선언되어 있으며(`package-info.java:2`), 관측 가능한 동작(반환 클래스, 던지는 예외의 종류)은 그대로다. 유일하게 새로 가능해진 것은 닫기 실패가 `IOException`으로 나타나 CNFE로 번역되는 경로인데, 이는 이전에는 "조용히 누수"였던 상황이 "정상적으로 보고"로 바뀐 것이다.

인접 결함 하나가 이 조사에서 함께 드러났고 별도 PR로 갈라졌다. 같은 메서드의 `:65-67`(`if (inputStream == null) return null;`)이 만드는 null이 `loadClass`를 통해 밖으로 새는 문제 — `ClassLoader.loadClass` 반환 계약 위반이다. 두 변경은 같은 메서드를 무대로 삼지만 닿는 줄이 다르고, 실제로 텍스트 충돌 없이 순차 머지되었다(#36938, `233e7b91f9b`). 테스트 파일만 양쪽이 각각 신규 생성해 결합이 필요했고, 현재 `ThrowawayClassLoaderTests`에는 두 테스트가 나란히 들어 있다.

이 PR에서 손대지 않은, 확인은 되었으나 별건인 것들: `loadClass(name, resolve)`가 `resolve` 인자를 무시하고 항상 `super.loadClass(name, true)`를 부르며 폴백으로 정의한 클래스에는 `resolveClass`를 걸지 않는 점(기존 동작), `loadClassFromResource`에 `@Nullable` 표기가 없는 점(패키지가 `@NullUnmarked`라 표기해도 검사되지 않는다).
