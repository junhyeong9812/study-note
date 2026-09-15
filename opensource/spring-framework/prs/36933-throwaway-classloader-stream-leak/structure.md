# PR #36933 — 무대의 실구조와 워크플로우

> PR #36933의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main 526c706d1c3. 이 문서의 `파일:줄` 인용은 모두 이 커밋 기준이며, PR 시점의 base 코드와 다른 곳은 본문에서 명시한다.

이 문서가 다루는 것은 `org.springframework.aot.nativex.feature` 패키지의 두 클래스 — `ThrowawayClassLoader`와 그 유일한 소비자 `PreComputeFieldFeature` — 가 어떻게 맞물려 있고, `loadClass` 한 번이 바이트 배열을 얻어 `Class` 객체를 만들기까지 어떤 자원을 붙들었다 놓는가다.\
PR이 바꾼 것은 `try` 한 줄이지만, 그 줄이 지키는 것은 "이 메서드가 여는 스트림의 소유권이 누구에게 있는가"라는 계약이다.

---

## 1. 무대 — 실구조

**무대는 두 클래스뿐이며, 둘 다 패키지 프라이빗이고 GraalVM 네이티브 이미지 빌드 시점에만 살아 있다.**\
`PreComputeFieldFeature`가 필드 하나로 로더를 붙들고, 로더는 자기 부모와 별개로 "리소스 공급자" 한 명을 따로 들고 있다.

> **패키지 프라이빗(package-private)** — 접근 제어자를 아무것도 붙이지 않았을 때의 가시성으로, 같은 패키지 안에서만 참조할 수 있다.\
> 예: `ThrowawayClassLoader`는 이 가시성이라 다른 패키지에서는 이름조차 쓸 수 없다.

```text
  org.springframework.aot.nativex.feature   (패키지 전체가 native image 빌드 전용)

  ┌──────────────────────────────────────────────────────────────────────┐
  │ class PreComputeFieldFeature implements Feature                      │
  │                                       PreComputeFieldFeature.java:37 │
  │   static boolean   verbose                                    (:39)  │
  │   static Pattern[] patterns   (7개 필드 식별 패턴)             (:42)  │
  │   final ThrowawayClassLoader throwawayClassLoader              (:52)  │
  │       = new ThrowawayClassLoader(getClass().getClassLoader())         │
  │                                                                      │
  │   void   beforeAnalysis(BeforeAnalysisAccess)                 (:56)  │
  │   void   iterateFields(DuringAnalysisAccess, Class<?>)        (:61)  │
  │   Object provideFieldValue(Field)                             (:96)  │
  └──────────────────────────────┬───────────────────────────────────────┘
                                 │ 소유 (필드 1개, 인스턴스 1개)
                                 ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ class ThrowawayClassLoader extends ClassLoader                       │
  │                                       ThrowawayClassLoader.java:31   │
  │   static { registerAsParallelCapable(); }                     (:33)  │
  │   final ClassLoader resourceLoader                            (:37)  │
  │                                                                      │
  │   ThrowawayClassLoader(ClassLoader parent)                    (:40)  │
  │       super(parent.getParent())        ← 부모가 아니라 조부모  (:41)  │
  │       this.resourceLoader = parent     ← 부모는 리소스원으로만 (:42)  │
  │                                                                      │
  │   Class<?> loadClass(String, boolean)  [override]             (:47)  │
  │   Class<?> loadClassFromResource(String)  [private]           (:66)  │ ← PR의 무대
  │   URL      findResource(String)        [override]             (:84)  │
  └──────────────────────────────────────────────────────────────────────┘
```

생성자 두 줄(`:41~42`)이 이 클래스의 전부라 해도 과언이 아니다.\
넘겨받은 `parent`를 부모로 삼지 않고 그 부모(조부모)를 부모로 삼으며, 넘겨받은 로더 자신은 `resourceLoader` 필드에 따로 보관한다.\
결과적으로 클래스로더 그래프는 이렇게 배치된다.

```text
  실제 로더 그래프 (PreComputeFieldFeature.java:52 시점)

     bootstrap / platform loader
              △
              │ parent
     ┌────────┴─────────────┐
     │  조부모 로더          │◀────────────┐
     └────────△─────────────┘             │ super(parent.getParent())
              │ parent                    │      (:41)
     ┌────────┴─────────────┐    ┌─────────┴──────────────┐
     │ 애플리케이션 로더     │    │ ThrowawayClassLoader   │
     │ (= 생성자의 parent)   │◀───┤   resourceLoader 필드  │
     └──────────────────────┘    └────────────────────────┘
                    getResourceAsStream / getResource 로만 사용
                                    (:68, :85)

  ▶ 위임 체인에서 애플리케이션 로더가 통째로 빠진다.
  ▶ 그래서 애플리케이션 클래스는 위임으로 절대 풀리지 않고,
    반드시 리소스 폴백을 거쳐 이 로더가 직접 defineClass 하게 된다.
```

`resourceLoader`와의 접점은 정확히 두 군데다.\
클래스 바이트를 얻는 `getResourceAsStream`(`:68`)과 일반 리소스 URL을 넘겨주는 `findResource`(`:85`)뿐이다.\
이 PR이 다루는 자원은 전자가 돌려주는 `InputStream` 하나다.

`loadClassFromResource`(`:66~81`)의 내부 구조를 자원 관점에서 확대하면 다음과 같다.

```text
  loadClassFromResource(name)                                     (:66)
  ┌─────────────────────────────────────────────────────────────────┐
  │ String resourceName = name.replace('.','/') + ".class"    (:67) │
  │                                                                 │
  │ InputStream inputStream =                                       │
  │     this.resourceLoader.getResourceAsStream(resourceName) (:68) │  ◀ 자원 획득
  │                                                                 │
  │ if (inputStream == null) return null;                   (:69~71)│  ◀ 자원 없음
  │                                                                 │
  │ try (inputStream) {                                       (:72) │  ◀ PR이 추가한 줄
  │     ByteArrayOutputStream outputStream = new ...          (:73) │
  │     inputStream.transferTo(outputStream);                 (:74) │  ◀ 유일한 읽기
  │     byte[] bytes = outputStream.toByteArray();            (:75) │
  │     return defineClass(name, bytes, 0, bytes.length);     (:76) │  ◀ 출구 1 (반환)
  │ }                                                               │
  │ catch (IOException ex) {                                  (:78) │
  │     throw new ClassNotFoundException(...);                (:79) │  ◀ 출구 2 (예외)
  │ }                                                               │
  └─────────────────────────────────────────────────────────────────┘

  자원 수명: :68에서 열리고, :72의 try-with-resources가 두 출구 모두에서 닫는다.
  수정 전에는 :72가 그냥 `try {`였고, 두 출구 어디에도 close()가 없었다.
```

`defineClass`(`:76`)는 `java.lang.ClassLoader`가 제공하는 `protected` 메서드로, 바이트 배열을 JVM에 넘겨 **이 로더가 소유하는 새 `Class` 객체**를 만든다.\
이 호출이 성공하는 순간 원본 클래스와 이름은 같지만 런타임 신원(정의 로더)이 다른 별도의 클래스가 태어난다.\
이 사본 만들기가 로더 전체의 존재 이유이며, 그 재료를 나르는 것이 이 PR이 닫는 스트림이다.

> **정의 로더(defining class loader)와 런타임 신원** — JVM은 클래스를 "이름"이 아니라 "이름 + 그 클래스를 `defineClass` 한 로더"의 쌍으로 구별한다.\
> 예: 같은 `NativeDetector.class` 바이트라도 앱 로더가 정의한 것과 `ThrowawayClassLoader`가 정의한 것은 서로 다른 클래스다.

---

## 2. 수정 전 동작 워크플로우

**대표 시나리오는 `PreComputeFieldFeature`가 `NativeDetector#inNativeImage` 같은 필드 하나의 값을 알아내는 흐름이고, 그 안에서 스트림이 한 번 열린다.**\
아래는 네이티브 이미지 빌드 중 실제로 일어나는 호출 사슬이다.\
수정 전 기준이며, `:72`가 `try {`였다는 점만 현재와 다르다.

```text
 GraalVM native-image 빌드 시작
   │
   │ native-image.properties 가 feature를 등록
   │   spring-core/src/main/resources/META-INF/native-image/
   │     org.springframework/spring-core/native-image.properties
   │     --features=org.springframework.aot.nativex.feature.PreComputeFieldFeature
   ▼
 PreComputeFieldFeature 인스턴스 생성
   └─ 필드 초기화자가 로더를 만든다                PreComputeFieldFeature.java:52
        new ThrowawayClassLoader(getClass().getClassLoader())
        → 생성자가 조부모를 부모로 삼고 애플리케이션 로더를 resourceLoader에 보관
                                                   ThrowawayClassLoader.java:41~42
   │
   ▼
 beforeAnalysis(access)                            PreComputeFieldFeature.java:56
   └─ access.registerSubtypeReachabilityHandler(this::iterateFields, Object.class)  (:57)
        ▶ Object의 모든 하위 타입 = 도달 가능한 모든 타입마다 콜백
   │
   ▼
 iterateFields(access, subtype)   ← 타입 하나마다 1회   (:61)
   │
   ├─ subtype.getDeclaredFields() 순회                  (:63)
   ├─ static && final && boolean 인 필드만 통과          (:65~68)
   ├─ fieldIdentifier = "선언클래스#필드명"              (:69)
   └─ patterns 7개 중 하나라도 매칭되면                  (:70~71)
        │
        ▼
      provideFieldValue(field)                          (:73 → :96)
        │
        ├─ throwawayClassLoader.loadClass(선언클래스명)   (:99)  (*) 로더 진입
        │     │
        │     ▼
        │   ThrowawayClassLoader#loadClass(name, resolve)   ThrowawayClassLoader.java:47
        │     │
        │     ├─ synchronized (getClassLoadingLock(name))          (:48)
        │     ├─ findLoadedClass(name) → 캐시 히트면 즉시 반환       (:49~52)
        │     ├─ super.loadClass(name, true)                        (:54)
        │     │     조부모 체인에는 애플리케이션 클래스패스가 없다
        │     │     → org.springframework.core.NativeDetector 는 여기서 실패
        │     │     → ClassNotFoundException
        │     │
        │     └─ catch (ClassNotFoundException ex)                  (:56)
        │           loadClassFromResource(name)                     (:57 → :66)
        │             │
        │             ├─ "org/springframework/core/NativeDetector.class"   (:67)
        │             ├─ resourceLoader.getResourceAsStream(...)     (:68)  ◀ 스트림 OPEN
        │             │     jar 이면 zip 엔트리 + 네이티브 inflater 버퍼
        │             │     디렉터리면 파일 디스크립터
        │             ├─ transferTo(ByteArrayOutputStream)           (:74)
        │             ├─ toByteArray()                              (:75)
        │             └─ defineClass(name, bytes, 0, len)            (:76)  ◀ 사본 생성
        │                   │
        │                   └─ 수정 전: 여기서 곧장 return.
        │                      스트림은 열린 채 스택을 벗어난다.  ◀ 결함
        │
        ├─ throwawayClass.getDeclaredField(field.getName())          (:100)
        ├─ throwawayField.setAccessible(true)                        (:101)
        └─ return throwawayField.get(null)                           (:102)
              ▶ 이 순간 사본 클래스의 static 초기화가 실행되고,
                그 부작용은 사본에만 남아 본체 이미지에 새겨지지 않는다.
        │
        ▼
      access.registerFieldValueTransformer(field, (r, o) -> fieldValue)   (:74)
        ▶ 원본 필드의 값을 빌드 시점 상수로 고정
```

(*) 표시한 `:99`가 로더의 유일한 진입점이다.\
그리고 이 진입점이 몇 번 불리는지가 결함의 규모를 결정한다.\
`:57`의 `registerSubtypeReachabilityHandler(..., Object.class)`는 **도달 가능한 모든 타입**에 대해 콜백을 걸고, 그중 패턴에 걸리는 `static final boolean` 필드마다 `provideFieldValue`가 한 번씩 불린다.\
패턴에 `org.springframework.*#*Present`(`:46`)와 `*#*PRESENT`(`:47`), `reactor.core.*#*Available`(`:48`)이 포함되어 있으므로, 실제 애플리케이션 빌드에서는 수십에서 수백 번 이 경로가 반복된다.\
한 번에 스트림 하나씩이다.

수정 후 흐름은 위와 동일하되 `:76`의 `return` 직전에 `close()`가 한 번 끼어든다.\
try-with-resources의 자원 해제는 `return` 표현식이 평가된 다음, 값이 실제로 반환되기 전에 일어난다.

---

## 3. 분기 처리 워크플로우

**`loadClass` 한 번에는 관문이 세 개 있고, 스트림이 열리는 것은 세 번째 관문 안쪽뿐이다.**\
아래 분기도에서 `[LEAK]`로 표시한 두 출구가 수정 전에 스트림을 놓치던 자리다.

```text
 loadClass(name, resolve)                        ThrowawayClassLoader.java:47
 │
 │ synchronized (getClassLoadingLock(name))                          (:48)
 │
 ├── 관문 1: findLoadedClass(name)                                   (:49)
 │   │
 │   ├─ != null ──────────────────────────▶ return loaded            (:51)
 │   │                                      (같은 이름 2회 defineClass = LinkageError.
 │   │                                       이 캐시 조회가 그것을 막는다)
 │   └─ == null ↓
 │
 ├── 관문 2: super.loadClass(name, true)                             (:54)
 │   │        = 표준 부모 위임. 단 부모는 "조부모"로 치환돼 있다.
 │   │
 │   ├─ 성공 ─────────────────────────────▶ return (JDK/부트스트랩 클래스)
 │   │        스트림은 열리지 않는다.
 │   │
 │   └─ ClassNotFoundException ex                                    (:56)
 │        = 애플리케이션 클래스의 정상 경로. 이 실패가 3단계 신호다.
 │        ↓
 │
 └── 관문 3: loadClassFromResource(name)                       (:57 → :66)
     │
     ├── 분기 3-a: getResourceAsStream 결과                          (:68)
     │   │
     │   ├─ null ────────────────────────▶ return null               (:70)
     │   │        스트림이 아예 없으므로 누수도 없다.
     │   │        (이 null이 loadClass 밖으로 새는 문제는 후속 PR #36938이 다룬다)
     │   │
     │   └─ non-null ↓   ◀ 여기서부터 자원을 붙든 상태
     │
     └── 분기 3-b: try 블록의 두 출구                            (:72~80)
         │
         ├─ 정상: transferTo → toByteArray → defineClass            (:74~76)
         │     │
         │     ├─ defineClass 성공 ────▶ return Class   [LEAK] 수정 전
         │     └─ defineClass 실패 ────▶ ClassFormatError 전파  [LEAK] 수정 전
         │            (ClassFormatError는 Error라 catch(IOException)에 걸리지 않는다.
         │             메서드 시그니처 :66이 이 에러를 throws로 선언하고 있다)
         │
         └─ transferTo 중 IOException                                (:78)
               throw new ClassNotFoundException(...)  [LEAK] 수정 전  (:79)
               ▶ 하필 I/O가 이미 이상한 상황에서 자원 반환이 확실하게 누락된다.

  수정 후: :72가 try (inputStream) 이 되어 위 세 출구가 모두 close()를 통과한다.
           close() 자체가 IOException을 던지면 :78의 catch가 그것도 잡아
           ClassNotFoundException으로 번역하고, 본문과 close()가 동시에 실패하면
           후자는 suppressed 예외로 첨부된다.
```

> **`LinkageError`** — 클래스를 연결(link)하는 단계에서 JVM이 던지는 `Error` 계열. 같은 로더가 같은 이름을 두 번 정의하려 하면 여기에 걸린다.\
> 예: `findLoadedClass`가 캐시 히트를 먼저 돌려주는 덕분에 두 번째 `defineClass`가 일어나지 않는다.

여기서 읽어 둘 구조적 사실은 **분기 3-b의 출구가 세 개인데 정리 코드는 0개였다**는 점이다.\
`finally`도 없고 try-with-resources도 아니었으므로, 어느 출구로 나가든 스트림 객체는 지역 변수 스코프를 벗어나며 GC 대상이 될 뿐이다.\
`InputStream`이 붙든 OS 자원은 GC가 그 객체를 수거하고 정리 로직이 동작할 때까지 반환되지 않으며, 그 시점은 보장되지 않는다.\
그래서 이 결함은 "항상 터지는 버그"가 아니라 "빌드 규모에 비례해 확률이 오르는 비결정적 고갈"의 형태를 띤다.

`try (inputStream)`이라는 문법 형태 자체도 분기 구조와 관련이 있다.\
자바 9부터 이미 선언된 실질적 final 변수를 괄호 안에 이름만 적어 자원으로 채택할 수 있고, 여기서 `inputStream`은 `:68`에서 한 번 대입된 뒤 재대입되지 않으므로 조건을 만족한다.\
스트림 획득 자체를 `try (InputStream in = ...)`로 감싸면 분기 3-a의 조기 반환(`:70`) 구조를 함께 바꿔야 하지만, 기존 변수를 채택하면 분기 3-a는 손대지 않고 분기 3-b에만 정리를 더할 수 있다.

> **실질적 final(effectively final)** — `final` 키워드는 없지만 한 번 대입된 뒤 재대입되지 않는 지역 변수. 자바 9의 try-with-resources는 이런 변수를 이름만으로 자원으로 받아들인다.\
> 예: `inputStream`은 `:68`의 대입 이후 값이 바뀌지 않아 `try (inputStream)`이 컴파일된다.

---

## 4. 스프링 전역에서의 자리

**이 로더는 애플리케이션 런타임에는 존재하지 않는다.**\
**GraalVM 네이티브 이미지 빌드라는 별도 수명주기에서만 살아 있고, 진입점은 `native-image.properties` 파일 한 줄이다.**

```text
 [진입 경로 — grep으로 실확인한 전부]

 spring-core/src/main/resources/META-INF/native-image/
     org.springframework/spring-core/native-image.properties
   ┌────────────────────────────────────────────────────────────────────┐
   │ Args = --initialize-at-build-time=                                 │
   │            org.springframework.aot.nativex.feature.ThrowawayClassLoader │
   │        --features=                                                 │
   │            org.springframework.aot.nativex.feature.PreComputeFieldFeature │
   └────────────────────────────────────────────────────────────────────┘
        │
        │ GraalVM native-image 도구가 이 파일을 읽어 Feature를 등록
        ▼
   PreComputeFieldFeature#beforeAnalysis          PreComputeFieldFeature.java:56
        │
        ▼
   PreComputeFieldFeature#iterateFields           PreComputeFieldFeature.java:61
        │
        ▼
   PreComputeFieldFeature#provideFieldValue:99 → ThrowawayClassLoader#loadClass:47
        │
        ▼
   ThrowawayClassLoader#loadClassFromResource:66  ← 이 PR의 무대
```

> **`native-image.properties`** — jar 안의 `META-INF/native-image/` 아래에 두면 GraalVM 빌드 도구가 자동으로 읽어 가는 설정 파일.\
> 예: 여기에 적힌 `--features=...PreComputeFieldFeature` 한 줄이 이 PR 무대의 유일한 진입 경로다.

`ThrowawayClassLoader`를 참조하는 프로덕션 코드는 grep 기준 `PreComputeFieldFeature.java:52` 한 자리뿐이다.\
클래스가 패키지 프라이빗(`ThrowawayClassLoader.java:31`)이므로 외부에서 참조할 방법 자체가 없다.\
이름이 비슷한 `spring-context`의 `SimpleThrowawayClassLoader`(`spring-context/src/main/java/org/springframework/instrument/classloading/SimpleThrowawayClassLoader.java:31`)와 `LoadTimeWeaver#getThrowawayClassLoader`(`spring-context/src/main/java/org/springframework/instrument/classloading/LoadTimeWeaver.java:61`)는 JPA 로드타임 위빙용으로 `OverridingClassLoader`를 상속한 **완전히 다른 계열**이며, 이 PR과 무관하다.

> **로드타임 위빙(LTW, load-time weaving)** — 클래스가 JVM에 로드되는 순간 그 바이트코드를 고쳐 넣는 기법.\
> 예: JPA 구현체가 엔티티 클래스에 지연 로딩용 코드를 심을 때 이 시점을 쓴다.

`native-image.properties`의 첫 인자 `--initialize-at-build-time=...ThrowawayClassLoader`도 이 로더의 성격을 말해 준다.\
로더 자신은 빌드 시점에 초기화되어야 하고(빌드 도구의 일부이므로), 로더가 읽어보는 대상 클래스는 반대로 빌드 시점 초기화를 피해야 한다.\
이 역할 분담이 로더 이름의 "throwaway"가 뜻하는 바다.

### 클래스로더 위임 모델 — 이 로더가 무엇을 비껴가는가

자바 클래스로더의 기본 규칙은 **부모 위임(parent delegation)**이다.\
`ClassLoader#loadClass`의 표준 구현은 (1) 이미 로드했는지 확인하고, (2) 부모에게 먼저 위임하고, (3) 부모가 실패했을 때만 자신이 `findClass`로 직접 찾는다.\
이 순서가 중요한 이유는 같은 이름의 클래스가 여러 로더에서 중복 정의되는 것을 막고, `java.lang.Object` 같은 코어 클래스가 항상 부트스트랩 로더 하나에서만 나오게 보장하기 때문이다.

```text
  표준 위임 (일반적인 ClassLoader)

    loadClass("com.app.Foo")
      │
      ├─ findLoadedClass  ─── 히트 ──▶ 반환
      │
      ├─ parent.loadClass ─── 성공 ──▶ 반환  ◀ 부모가 이미 로드했다면 그 클래스
      │
      └─ findClass(name)  ─── 하위 클래스의 확장 지점
```

`ThrowawayClassLoader`는 이 모델을 두 곳에서 비튼다.

첫째, **부모를 한 칸 건너뛴다**(`:41`).\
넘겨받은 애플리케이션 로더를 부모로 삼으면 `com.app.Foo`는 위임 단계에서 곧바로 해결되고, 그 결과는 애플리케이션 로더가 이미 정의한 원본 클래스다.\
그러면 사본을 만들 기회가 없고, 그 클래스의 static 초기화 결과는 원본 그대로다.\
조부모를 부모로 삼으면 위임은 JDK 코어 클래스에서만 성공하고 애플리케이션 클래스는 반드시 실패하므로, 실패가 곧 "이제 내가 직접 정의할 차례"라는 신호가 된다.

둘째, **`findClass` 대신 `loadClass(String, boolean)` 자체를 재정의한다**(`:47`).\
표준 확장 지점은 `findClass`인데 이 클래스는 그 위층을 통째로 덮어썼다.\
그 결과 위임 실패를 `try/catch`로 직접 붙잡을 수 있게 되고(`:53~62`), 폴백 로직이 `catch` 블록 안에 들어간다.\
이 배치가 후속 PR #36938이 다루는 `null` 반환 문제의 구조적 배경이기도 하다.

`getClassLoadingLock(name)`(`:48`)과 `registerAsParallelCapable()`(`:34`)은 병렬 로딩을 위한 짝이다.\
후자를 클래스 초기화 시점에 호출해 두면 JDK가 이름별 락 객체를 나눠 주고, 그래야 서로 다른 클래스를 동시에 로드할 때 로더 전체가 직렬화되지 않는다.\
`defineClass`는 같은 이름을 두 번 부르면 `LinkageError`를 던지므로, `findLoadedClass`(`:49`)와 이름별 락은 그 중복을 막는 한 세트로 읽어야 한다.

> **`registerAsParallelCapable()`과 이름별 락** — 로더가 "병렬 로딩 가능"이라고 등록해 두면 JDK가 클래스 이름마다 별도의 락 객체를 내준다.\
> 예: 등록하지 않으면 로더 인스턴스 하나에 락이 걸려, 서로 다른 클래스를 동시에 로드하려 해도 한 줄로 늘어선다.

---

## 5. 관련 개념

`../../concepts/`에는 이 문서가 참조할 만한 기존 개념 문서가 없으므로, 필요한 개념을 여기에 직접 서술한다.

### 5.1 build-time initialization과 클래스 사본

GraalVM 네이티브 이미지는 빌드 시점에 도달 가능한 코드를 정적 분석하고, 일부 클래스는 그때 초기화해 결과를 이미지 힙에 그대로 굳혀 넣는다.\
이것을 build-time initialization이라 부른다.\
문제는 부작용이다.\
어떤 클래스의 `static final boolean` 값 하나를 알고 싶어서 그 클래스를 초기화하면, 그 클래스의 static 블록 전체가 실행되고 그 결과가 이미지에 새겨진다.\
원래 런타임에 결정되어야 할 값까지 빌드 시점 값으로 고정될 수 있다.

> **이미지 힙(image heap)** — 네이티브 이미지 빌드가 끝난 실행 파일 안에 미리 채워 넣어 두는 객체 영역.\
> 예: 빌드 시점에 초기화된 클래스의 `static` 필드 값이 여기에 그대로 실려 나간다.

`ThrowawayClassLoader`의 해법은 **신원이 다른 사본을 만들어 그 사본만 초기화하는 것**이다.\
JVM에서 클래스의 런타임 신원은 "이름 + 정의 로더"의 쌍이므로, 같은 바이트로 다른 로더가 `defineClass`(`:76`)하면 JVM은 완전히 별개의 클래스로 취급한다.\
`PreComputeFieldFeature.java:102`의 `throwawayField.get(null)`이 초기화를 유발하지만, 그 초기화는 사본에만 일어나고 사본은 곧 버려진다.

### 5.2 try-with-resources와 이미 선언된 변수

자바 7의 try-with-resources는 괄호 안에서 자원을 **선언**해야 했다.\
자바 9부터는 이미 선언된 변수가 final이거나 실질적 final(effectively final, 한 번 대입 후 재대입 없음)이면 이름만 적어 자원으로 채택할 수 있다.\
`:72`의 `try (inputStream)`이 그 형태다.

해제 순서에 대해 알아 둘 것이 두 가지 있다.\
하나는 **`close()`가 같은 `try` 문의 `catch` 절보다 먼저 실행된다**는 점이다.\
그래서 `close()`가 던진 `IOException`도 `:78`의 `catch (IOException ex)`에 잡혀 `ClassNotFoundException`으로 번역된다.\
다른 하나는 **본문과 `close()`가 동시에 실패하면 본문 예외가 주(primary)가 되고 `close()` 예외는 suppressed로 첨부된다**는 점이다.\
원인 정보가 사라지지 않는다.

> **suppressed 예외** — 주 예외에 매달아 두는 부차 예외. `Throwable#getSuppressed()`로 꺼낼 수 있고 스택트레이스에도 함께 출력된다.\
> 예: `transferTo`의 `IOException`이 주 예외가 되고, 뒤이은 `close()` 실패가 거기에 첨부된다.

### 5.3 자원 누수의 관측 불가능성

이 결함이 오래 살아남은 이유는 **기능이 깨지지 않기 때문**이다.\
`defineClass`는 성공하고, 필드 값은 정상적으로 읽히고, 빌드는 통과한다.\
누수되는 것은 자바 객체가 아니라 그 아래의 OS 자원 — jar이면 열린 zip 엔트리와 네이티브 inflater 버퍼, 디렉터리면 파일 디스크립터 — 이고, 이것들은 GC 타이밍에 의존해 비결정적으로 반환된다.

> **파일 디스크립터(file descriptor)** — OS가 열린 파일 하나마다 프로세스에 내주는 번호표. 프로세스마다 동시에 가질 수 있는 개수에 한도가 있다.\
> 예: 한도를 넘기면 그 다음 파일 열기가 `Too many open files`로 실패한다.

증상은 세 방향으로 갈린다.\
디스크립터 한도가 낮은 CI 컨테이너에서는 빌드 후반부에 `Too many open files`가 나온다.\
윈도우에서는 열린 핸들이 jar 파일을 잠가 후속 단계의 삭제나 교체를 막는다.\
inflater 버퍼가 쌓이면 빌드 프로세스의 메모리 사용이 필요 이상으로 늘어난다.\
셋 다 "실패 지점이 결함 지점에서 멀리 떨어진" 형태이며, 그래서 테스트는 자원 반환 자체를 관측 가능한 신호로 번역해야 한다(테스트 설계는 tests.md 참조).

### 5.4 인접 결함과의 관계

같은 메서드 `loadClassFromResource`의 다른 줄에 별개의 결함이 하나 더 있었다.\
분기 3-a의 `return null`(`:70`)이 `loadClass`의 반환값으로 그대로 흘러나가 `ClassLoader.loadClass` 계약을 위반하던 문제이며, 후속 PR #36938이 `:57~61`의 catch 블록을 고쳐 해결했다.\
두 결함은 같은 메서드를 무대로 삼지만 건드리는 줄이 달라 서로 충돌하지 않는다.\
그쪽의 구조 설명은 `../36938/structure.md`에 있다.
