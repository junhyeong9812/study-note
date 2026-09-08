# PR #36938 — 무대의 실구조와 워크플로우

> PR #36938의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main 526c706d1c3. 이 문서의 `파일:줄` 인용은 모두 이 커밋 기준이며, PR 시점의 base 코드와 다른 곳은 본문에서 명시한다.

이 문서가 다루는 것은 `ThrowawayClassLoader#loadClass`의 3단 로딩 구조와, 그 3단이 전부 실패했을 때 무엇이 밖으로 나가는가다. PR이 바꾼 것은 `catch` 블록 4줄이지만, 그 4줄이 결정하는 것은 이 클래스가 `java.lang.ClassLoader`라는 상위 타입과 맺은 계약을 지키는가 여부다. 인접 PR #36933이 같은 메서드의 자원 수명을 다뤘다면, 이 PR은 같은 메서드의 **실패 표현 방식**을 다룬다.

이 PR의 base에는 이미 #36933의 수정(`ThrowawayClassLoader.java:72`의 `try (inputStream)`)이 들어가 있다. 두 변경은 같은 메서드를 무대로 삼지만 건드리는 줄이 다르다.

---

## 1. 무대 — 실구조

**무대는 로더 한 클래스와 소비자 한 클래스이며, 로더의 공개 표면은 `loadClass` 하나뿐이다.** 아래 구조도는 이 PR이 다루는 반환 계약의 관점에서 같은 두 클래스를 그린 것이다.

```
  org.springframework.aot.nativex.feature

  ┌───────────────────────────────────────────────────────────────────────┐
  │ class ThrowawayClassLoader extends ClassLoader                        │
  │                                        ThrowawayClassLoader.java:31   │
  │                                                                       │
  │  static { registerAsParallelCapable(); }                       (:33)  │
  │  final ClassLoader resourceLoader;                             (:37)  │
  │                                                                       │
  │  ThrowawayClassLoader(ClassLoader parent)                      (:40)  │
  │      super(parent.getParent());     ← 부모 = 넘겨받은 로더의 부모 (:41) │
  │      this.resourceLoader = parent;  ← 넘겨받은 로더는 리소스원   (:42) │
  │                                                                       │
  │  ┌─ 외부에 노출되는 유일한 동작 ─────────────────────────────────┐   │
  │  │ protected Class<?> loadClass(String name, boolean resolve)   │   │
  │  │         throws ClassNotFoundException              (:47)      │   │
  │  │   반환 계약: non-null Class  또는  ClassNotFoundException      │   │
  │  │   ← 수정 전에는 여기서 null 이 나갈 수 있었다  (*)              │   │
  │  └──────────────────────────────────────────────────────────────┘   │
  │        │ 내부 위임                                                    │
  │        ▼                                                              │
  │  ┌─ 내부 헬퍼 ──────────────────────────────────────────────────┐   │
  │  │ private Class<?> loadClassFromResource(String name)          │   │
  │  │         throws ClassNotFoundException, ClassFormatError (:66) │   │
  │  │   반환 계약: Class  또는  null("리소스 없음" 내부 신호)  (:70) │   │
  │  │   ← null은 이 헬퍼의 정상적 표현. 문제는 그 null의 처리였다.   │   │
  │  └──────────────────────────────────────────────────────────────┘   │
  │                                                                       │
  │  protected URL findResource(String name)                       (:84)  │
  │      → this.resourceLoader.getResource(name)                   (:85)  │
  └───────────────────────────────────────────────────────────────────────┘
                                 △
                                 │ 필드로 소유 (인스턴스 1개)
  ┌───────────────────────────────────────────────────────────────────────┐
  │ class PreComputeFieldFeature implements Feature                       │
  │                                     PreComputeFieldFeature.java:37    │
  │   final ThrowawayClassLoader throwawayClassLoader              (:52)  │
  │       = new ThrowawayClassLoader(getClass().getClassLoader())         │
  │                                                                       │
  │   Object provideFieldValue(Field field)                        (:96)  │
  │       Class<?> throwawayClass = loader.loadClass(...);         (:99)  │  (*)
  │       Field f = throwawayClass.getDeclaredField(...);          (:100) │  ← null이면 NPE
  │       f.setAccessible(true);                                   (:101) │
  │       return f.get(null);                                      (:102) │
  └───────────────────────────────────────────────────────────────────────┘
```

(*) 두 곳을 나란히 놓고 보면 결함의 형태가 드러난다. `:99`가 받은 값을 `:100`에서 **곧바로 역참조**한다. 널 검사도, `Optional`도, 방어 코드도 없다. 이것은 소비자의 부주의가 아니라 `ClassLoader.loadClass`의 문서화된 계약을 그대로 신뢰한 정상적인 코드다. `java.lang.ClassLoader`의 `loadClass`는 요청한 클래스의 non-null `Class`를 반환하거나 `ClassNotFoundException`을 던진다고 규정하며, "찾지 못함"을 `null`로 표현하는 선택지는 계약에 없다.

두 메서드의 반환 계약이 서로 다르다는 점도 구조적으로 중요하다. `loadClassFromResource`(`:66`)에서 `null`은 "리소스가 없다"는 **정당한 내부 신호**다. 이 헬퍼는 private이고 호출자가 하나뿐이므로 그런 표현을 써도 무방하다. 문제는 그 내부 신호가 번역 없이 `loadClass`의 반환값으로 그대로 흘러나갔다는 것이고, 이 PR의 수정은 정확히 그 경계에 번역기를 놓는 일이다.

`loadClass` 안의 3단 구조를 반환값 관점에서 확대하면 다음과 같다.

```
  loadClass(name, resolve)                                       (:47)
  ┌──────────────────────────────────────────────────────────────────────┐
  │ synchronized (getClassLoadingLock(name)) {                    (:48)  │
  │                                                                      │
  │   [1] Class<?> loaded = findLoadedClass(name);                (:49)  │
  │       if (loaded != null) return loaded;                    (:50~52) │ → Class
  │                                                                      │
  │   try {                                                       (:53)  │
  │   [2]   return super.loadClass(name, true);                   (:54)  │ → Class
  │   }                                                                  │
  │   catch (ClassNotFoundException ex) {                         (:56)  │
  │   [3]   Class<?> loadedFromResource = loadClassFromResource(name);   │
  │                                                               (:57)  │
  │         if (loadedFromResource == null) {                     (:58)  │ ← PR이 추가
  │             throw ex;                                         (:59)  │ ← PR이 추가
  │         }                                                            │
  │         return loadedFromResource;                            (:61)  │ → Class
  │   }                                                                  │
  │ }                                                                    │
  └──────────────────────────────────────────────────────────────────────┘

  수정 전 :56~58 은 다음 한 줄이었다.
      catch (ClassNotFoundException ex) {
          return loadClassFromResource(name);      ← null 이 그대로 통과
      }
```

`catch` 블록이 폴백 로직을 품고 있다는 배치가 이 수정의 핵심 자원이다. 3단계가 실패했을 때 되던질 예외 `ex`가 이미 손에 들려 있으므로, 새 예외를 만들 필요 없이 2단계의 원본 예외를 그대로 재전파할 수 있다. 원본 예외는 클래스명과 JDK 로더가 붙인 cause를 이미 담고 있고, 3단계 실패는 "정의할 바이트도 없었다"는 확인일 뿐 새 정보를 더하지 않는다.

---

## 2. 수정 전 동작 워크플로우

**정상 시나리오는 2단계가 실패하고 3단계가 성공하는 흐름이며, 그것이 이 로더의 존재 이유다.** 아래는 `org.springframework.core.NativeDetector` 같은 실제 대상 클래스가 지나가는 길이다. 이 경로는 수정 전후로 완전히 동일하다.

```
 PreComputeFieldFeature#provideFieldValue                              (:96)
   │
   │ loadClass("org.springframework.core.NativeDetector")               (:99)
   ▼
 [1] findLoadedClass                                    ThrowawayClassLoader.java:49
       이 로더가 아직 정의한 적 없음 → null → 통과
   │
 [2] super.loadClass(name, true)                                       (:54)
       조부모 체인 = 부트스트랩/플랫폼. 애플리케이션 클래스패스 없음.
       → ClassNotFoundException  ◀ 정상 흐름의 신호이지 오류가 아니다
   │
 [3] catch → loadClassFromResource(name)                          (:57 → :66)
       resourceName = "org/springframework/core/NativeDetector.class"   (:67)
       resourceLoader.getResourceAsStream(resourceName)                 (:68)
         → 애플리케이션 클래스패스에 .class 파일이 실재하므로 스트림 획득
       try (inputStream) { transferTo → toByteArray }              (:72~75)
       defineClass(name, bytes, 0, len)                                 (:76)
         → 원본과 이름은 같지만 정의 로더가 다른 사본 Class 탄생
   │
   ▼ return 사본 Class
 PreComputeFieldFeature
   getDeclaredField / setAccessible / get(null)                  (:100~102)
     → 사본의 static 초기화가 이때 실행되고 그 부작용은 사본에만 남는다
```

**결함 시나리오는 "1·2·3단계가 모두 실패"할 때이며, 수정 전에는 그때 `null`이 조용히 밖으로 나갔다.** 아래가 수정 전 기준의 흐름이다.

```
 대상: .class 리소스가 존재하지 않는 클래스
       (CGLIB 프록시, JDK 동적 프록시, defineClass로만 존재하는 클래스 등이
        declaring class인 경우)
   │
   │ loadClass(name)                                                    (:99)
   ▼
 [1] findLoadedClass → null                                            (:49)
   │
 [2] super.loadClass → ClassNotFoundException ex                       (:54)
   │
 [3] loadClassFromResource(name)                                       (:66)
       getResourceAsStream → null                                      (:68)
       return null                                                     (:70)
   │
   │ 수정 전 catch 블록:  return loadClassFromResource(name);
   ▼
 loadClass 가 null 을 반환   ◀ ClassLoader 계약 위반. 예외도 로그도 없다.
   │
   ▼
 PreComputeFieldFeature#provideFieldValue
   throwawayClass == null
   throwawayClass.getDeclaredField(field.getName())                   (:100)
     ──▶ NullPointerException
   │
   ▼
 PreComputeFieldFeature#iterateFields 의 광범위 catch                 (:80)
   catch (Throwable ex) {
       if (verbose) {                                                  (:81)
           System.out.println("Field " + fieldIdentifier +
               " will be evaluated at runtime due to this error " +
               "during build time evaluation: " + ex);              (:82~83)
       }
   }
   ▶ 빌드는 깨지지 않는다. 그 필드는 빌드 시점 상수화를 포기하고
     런타임 평가로 폴백한다.
   ▶ 그러나 로그에는 "NullPointerException 때문에" 라는 문장만 남는다.
     어떤 클래스가 왜 안 잡혔는지 알 수 없다.
```

수정 후에는 마지막 두 단계만 달라진다. `:58~59`가 `null`을 붙잡아 원본 `ex`를 재전파하므로, `provideFieldValue`는 NPE 대신 `ClassNotFoundException`을 받는다. 그 예외는 이미 `provideFieldValue`의 시그니처(`PreComputeFieldFeature.java:97`)에 `throws ClassNotFoundException`으로 선언돼 있고, `:80`의 `catch (Throwable)`이 NPE든 CNFE든 똑같이 잡는다. 즉 **빌드 동작은 한 글자도 바뀌지 않고 로그 문장만 진단 가능한 것으로 바뀐다.**

---

## 3. 분기 처리 워크플로우

**세 관문이 순차적으로 닫히는 구조이며, 수정은 마지막 관문이 닫혔을 때의 출구 하나만 바꾼다.** 아래 분기도에서 `[BUG]`가 결함이 살던 출구다.

```
 loadClass(name, resolve)                        ThrowawayClassLoader.java:47
 │
 │ synchronized (getClassLoadingLock(name))                          (:48)
 │   ▶ registerAsParallelCapable() (:34) 가 이름별 락을 가능하게 한다.
 │     같은 이름을 두 번 defineClass 하면 LinkageError 이므로,
 │     이름별 락 + findLoadedClass 가 그 중복을 막는 한 세트다.
 │
 ├── 관문 1: findLoadedClass(name)                                   (:49)
 │   │
 │   ├─ != null ────────────────────────▶ return loaded              (:51)
 │   │                                    "이미 이 로더가 정의함"
 │   └─ == null ↓
 │
 ├── 관문 2: super.loadClass(name, true)                             (:54)
 │   │        표준 부모 위임. 단 부모는 조부모로 치환됨 (:41).
 │   │
 │   ├─ 성공 ───────────────────────────▶ return Class
 │   │         JDK/부트스트랩 클래스가 여기서 풀린다.
 │   │
 │   └─ ClassNotFoundException ex ↓                                  (:56)
 │         애플리케이션 클래스의 정상 경로. ex 를 손에 쥔 채 3단계로.
 │
 └── 관문 3: loadClassFromResource(name)                       (:57 → :66)
     │
     ├── 3-a: getResourceAsStream(resourceName)                      (:68)
     │   │
     │   ├─ null ─────────────────────▶ return null                  (:70)
     │   │     "리소스 없음" 내부 신호
     │   │        │
     │   │        ├─ [BUG] 수정 전:  catch 가 이 null 을 그대로 return
     │   │        │        ──▶ loadClass 가 null 반환 → 호출자에서 NPE
     │   │        │
     │   │        └─ 수정 후:  if (loadedFromResource == null)  (:58)
     │   │                        throw ex;                     (:59)
     │   │                 ──▶ 2단계의 원본 CNFE 재전파
     │   │
     │   └─ non-null ↓
     │
     ├── 3-b: try (inputStream) { ... }                          (:72~76)
     │   │
     │   ├─ defineClass 성공 ────────▶ return Class                  (:76)
     │   │        → catch 블록의 :61 이 그대로 반환. 수정 전후 동일.
     │   │
     │   └─ defineClass 실패 ────────▶ ClassFormatError 전파
     │            Error 이므로 :78 의 catch(IOException) 에 걸리지 않고
     │            시그니처 :66 의 throws 를 타고 그대로 올라간다.
     │
     └── 3-c: transferTo 중 IOException                              (:78)
               throw new ClassNotFoundException(
                   "Cannot load resource for class [" + name + "]", ex)  (:79)
               → 수정 전후 동일. 이미 예외로 표현되던 유일한 실패 경로였다.


 반환값 관점의 수정 전/후 비교
 ┌──────────────────────────────┬───────────────────┬─────────────────────────┐
 │ 상황                         │ 수정 전           │ 수정 후                 │
 ├──────────────────────────────┼───────────────────┼─────────────────────────┤
 │ 관문 1 히트                  │ Class             │ Class                   │
 │ 관문 2 위임 성공             │ Class             │ Class                   │
 │ 관문 3 폴백 성공             │ Class             │ Class                   │
 │ 관문 3 중 IOException        │ CNFE              │ CNFE                    │
 │ 관문 2 실패 + 리소스 없음    │ null       [BUG]  │ CNFE (원본 재전파)      │
 └──────────────────────────────┴───────────────────┴─────────────────────────┘
   값이 달라지는 행은 마지막 하나뿐이며, 그것이 이 PR의 전부다.
```

분기 3-a의 `null`(`:70`)을 그대로 두고 호출자 쪽에서 번역한 선택에는 이유가 있다. `loadClassFromResource`가 직접 예외를 던지게 바꾸면 원본 `ex`에 접근할 수 없어 정보가 빈약한 새 예외를 만들어야 한다. 지금 형태에서 `null`은 private 헬퍼의 내부 신호로 남고, 유일한 호출자가 그 신호를 즉시 계약에 맞는 예외로 번역하므로 밖으로 새지 않는다. **계약은 공개 표면에서 지키고, 내부 신호는 내부에 가둔다**는 배치다.

---

## 4. 스프링 전역에서의 자리

**이 로더는 GraalVM 네이티브 이미지 빌드라는 별도 수명주기에서만 존재하며, 진입점은 `native-image.properties` 한 줄이다. 애플리케이션 런타임에는 등장하지 않는다.**

```
 [진입 경로 — grep으로 실확인한 전부]

 spring-core/src/main/resources/META-INF/native-image/
     org.springframework/spring-core/native-image.properties
   ┌─────────────────────────────────────────────────────────────────────┐
   │ Args = --initialize-at-build-time=                                  │
   │           org.springframework.aot.nativex.feature.ThrowawayClassLoader  │
   │        --features=                                                  │
   │           org.springframework.aot.nativex.feature.PreComputeFieldFeature │
   └─────────────────────────────────────────────────────────────────────┘
        │ GraalVM native-image 도구가 Feature 를 등록
        ▼
   beforeAnalysis(access)                      PreComputeFieldFeature.java:56
        access.registerSubtypeReachabilityHandler(this::iterateFields, Object.class)
                                               PreComputeFieldFeature.java:57
        ▶ Object 의 모든 하위 타입 = 도달 가능한 모든 타입마다 콜백
        ▼
   iterateFields(access, subtype)               PreComputeFieldFeature.java:61
        static && final && (boolean|Boolean) 인 필드만 통과      (:65~68)
        fieldIdentifier = "선언클래스#필드명"                     (:69)
        patterns 7개 중 매칭되면                                  (:70~71)
        ▼
   provideFieldValue(field)                     PreComputeFieldFeature.java:96
        loader.loadClass(field.getDeclaringClass().getName())     (:99)  (*) 유일한 진입점
        ▼
   ThrowawayClassLoader#loadClass               ThrowawayClassLoader.java:47  ← 이 PR의 무대
```

패턴 7개(`PreComputeFieldFeature.java:42~50`)가 이 로더의 작업 부하를 결정한다.

```
  org.springframework.core.NativeDetector#inNativeImage                    (:43)
  org.springframework.cglib.core.AbstractClassGenerator#inNativeImage      (:44)
  org.springframework.aot.AotDetector#inNativeImage                        (:45)
  org.springframework.*#*Present                                           (:46)
  org.springframework.*#*PRESENT                                           (:47)
  reactor.core.*#*Available                                                (:48)
  org.apache.commons.logging.LogAdapter#*Present                           (:49)
```

앞의 셋은 특정 필드 하나를 콕 집지만 뒤의 넷은 와일드카드다. `org.springframework.*#*Present` 같은 패턴은 프레임워크 전역에 흩어진 "라이브러리 존재 여부" 상수를 전부 훑으므로, 실제 애플리케이션 빌드에서 이 경로는 수십에서 수백 번 반복된다. 그중 declaring class가 런타임 생성 클래스인 경우가 결함의 트리거 조건이 된다.

`ThrowawayClassLoader`를 참조하는 프로덕션 코드는 grep 기준 `PreComputeFieldFeature.java:52` 한 자리뿐이다. 클래스가 패키지 프라이빗(`ThrowawayClassLoader.java:31`)이라 외부 참조 경로가 구조적으로 존재하지 않는다. 이름이 비슷한 `spring-context`의 `SimpleThrowawayClassLoader`(`spring-context/src/main/java/org/springframework/instrument/classloading/SimpleThrowawayClassLoader.java:31`)와 `LoadTimeWeaver#getThrowawayClassLoader`(`.../LoadTimeWeaver.java:61`)는 JPA 로드타임 위빙용 `OverridingClassLoader` 계열로 이 PR과 무관하다.

### 클래스로더 위임 모델과 loadClass 계약

자바 클래스로더의 기본 규칙은 **부모 위임(parent delegation)**이다. 표준 `ClassLoader#loadClass` 구현은 (1) `findLoadedClass`로 이미 로드했는지 보고, (2) 부모에게 위임하고, (3) 부모가 실패하면 `findClass`로 자신이 직접 찾는다. 이 순서가 `java.lang.Object` 같은 코어 클래스가 항상 부트스트랩 로더 하나에서만 나오도록 보장한다.

```
  표준 위임                          ThrowawayClassLoader 의 변형

  loadClass(name)                    loadClass(name, resolve)     (:47)
    │                                  │
    ├─ findLoadedClass ──▶ 반환         ├─ findLoadedClass ──▶ 반환  (:49)
    │                                  │
    ├─ parent.loadClass ─▶ 반환         ├─ super.loadClass ──▶ 반환  (:54)
    │    (직계 부모)                    │    (부모가 "조부모"로 치환됨)
    │                                  │
    └─ findClass(name)                 └─ catch CNFE
         하위 클래스의 확장 지점             └─ loadClassFromResource  (:57)
                                                resourceLoader 에서 바이트를 얻어
                                                직접 defineClass                (:76)
```

이 클래스가 표준에서 벗어나는 지점은 두 곳이다.

첫째, **부모를 한 칸 건너뛴다**(`:41`). 넘겨받은 애플리케이션 로더를 부모로 삼으면 애플리케이션 클래스는 2단계에서 곧바로 풀리고, 그 결과는 애플리케이션 로더가 이미 정의한 원본 클래스다. 그러면 사본을 만들 기회가 없어 build-time initialization 회피라는 목적 자체가 무너진다. 조부모를 부모로 삼으면 위임은 JDK 코어 클래스에서만 성공하고 애플리케이션 클래스는 반드시 실패하므로, 그 실패가 3단계 진입 신호가 된다.

둘째, **`findClass` 대신 `loadClass(String, boolean)` 자체를 재정의한다**(`:47`). 표준 확장 지점은 `findClass`인데 이 클래스는 그 위층을 통째로 덮어썼고, 그 덕에 위임 실패를 `try/catch`로 직접 붙잡아 폴백을 `catch` 블록 안에 넣을 수 있게 되었다(`:53~62`). 바로 이 배치가 이 PR의 결함과 수정을 동시에 만들어 낸다. `findClass`를 재정의하는 표준 형태였다면 `null` 반환은 상위 `loadClass`가 알아서 `ClassNotFoundException`으로 번역했을 것이다. 상위 층을 덮어쓰면서 **그 층이 하던 번역 책임까지 함께 인수했다는 사실이 코드에 반영되지 않은 것**이 결함의 구조적 원인이다.

---

## 5. 관련 개념

`../../concepts/`에는 이 문서가 참조할 만한 기존 개념 문서가 없으므로, 필요한 개념을 여기에 직접 서술한다.

### 5.1 `ClassLoader.loadClass`의 반환 계약

`java.lang.ClassLoader#loadClass`는 요청한 이름의 클래스에 대해 **non-null `Class` 객체를 반환하거나 `ClassNotFoundException`을 던진다.** "찾지 못함"을 `null`로 표현하는 세 번째 선택지는 계약에 없다. 그래서 모든 호출자는 반환값을 널 검사 없이 역참조하는 것이 정상이고, `PreComputeFieldFeature.java:99~100`이 정확히 그렇게 쓰여 있다.

이 구분이 형식 논쟁이 아닌 이유는 **정보량**에 있다. `ClassNotFoundException`은 "무엇을 못 찾았는지"를 클래스명과 cause로 실어 나르는 도메인 예외다. 반면 `NullPointerException`은 "누군가 계약을 어겼다"는 사후 증상일 뿐, 어떤 클래스가 문제였는지 알려주지 않는다. 계약 위반의 실질 비용은 대부분 이 진단 정보의 소실로 나타난다.

`findClass`와의 관계도 알아 둘 만하다. `findClass`는 위임이 실패한 뒤 하위 클래스가 직접 클래스를 찾도록 마련된 확장 지점이며, 표준 `loadClass`가 그 결과를 받아 `null`이면 `ClassNotFoundException`으로 번역해 준다. `ThrowawayClassLoader`는 `loadClass`를 통째로 재정의했으므로 그 번역기를 잃었고, 이 PR이 `:58~59`로 같은 번역기를 손으로 다시 놓았다.

### 5.2 조용한 실패(silent failure)로서의 null 반환

이 결함의 성격은 "예외가 나던 것이 안 나게 됨"이 아니라 **처음부터 아무 신호도 없이 `null`이 반환되던 것**이다. 이런 종류는 세 가지 이유로 발견이 늦다.

첫째, 증상이 결함 지점에서 떨어져 나타난다. 실제 예외는 `PreComputeFieldFeature.java:100`에서 터지지만 원인은 `ThrowawayClassLoader.java:57`에 있다. 둘째, 상위에 광범위한 `catch (Throwable)`(`PreComputeFieldFeature.java:80`)이 있어 빌드가 깨지지 않는다. 셋째, 그 catch의 로그가 verbose 모드(`PreComputeFieldFeature.java:39~40`, `-Dspring.native.precompute.log=verbose`)에서만 출력되므로 평소에는 아무 흔적도 남지 않는다.

이런 형태의 결함은 증상 지점이 아니라 **결함이 있는 층에 테스트를 붙여** "여기서 예외가 나야 한다"를 못 박는 것이 유일한 재현 방법이다.

### 5.3 트리거 조건 — .class 리소스가 없는 클래스

3단계가 빈손이 되려면 `resourceLoader.getResourceAsStream("경로/이름.class")`가 `null`을 돌려줘야 한다. 현실에서 이 조건을 만족하는 것은 **파일 실체 없이 런타임에 생성된 클래스**다. CGLIB 프록시, JDK 동적 프록시, 또는 `defineClass`로만 존재하는 클래스가 여기 해당한다.

`PreComputeFieldFeature`의 패턴 중 `org.springframework.cglib.core.AbstractClassGenerator#inNativeImage`(`:44`)가 CGLIB 영역을 명시적으로 겨냥하고 있고, 와일드카드 패턴 `org.springframework.*#*Present`(`:46`)는 declaring class를 가리지 않는다. 즉 트리거 조건은 좁지만 이론적이지는 않다. 다만 앞서 본 대로 결과가 빌드 실패가 아니라 로그 품질 저하이므로, 이 PR은 크래시 수정이 아니라 계약 정합성과 진단 가능성 수정으로 위치가 정해진다.

### 5.4 인접 PR #36933과의 관계

같은 메서드 `loadClassFromResource`의 다른 결함 — `getResourceAsStream`이 연 스트림이 어느 출구에서도 닫히지 않던 자원 누수 — 을 인접 PR #36933이 `:72`의 `try (inputStream)`로 고쳤다. 두 변경은 무대가 같지만 건드리는 줄이 다르다. #36933은 분기 3-b의 자원 수명을, #36938은 분기 3-a의 반환 표현을 다룬다.

테스트 파일 `spring-core/src/test/java/org/springframework/aot/nativex/feature/ThrowawayClassLoaderTests.java`도 #36933이 새로 만든 것이고, 이 PR은 거기에 메서드 하나(`:60~77`)를 덧붙였다. 결과적으로 두 테스트가 폴백의 성공(`:37~58`)과 실패(`:60~77`)를 각각 하나씩 붙잡는 구조가 되었다. 그쪽 구조 설명은 `../36933/structure.md`에 있다.
