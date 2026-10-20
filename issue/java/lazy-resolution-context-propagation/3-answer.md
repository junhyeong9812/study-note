# issue/java/lazy-resolution-context-propagation — 정답

태그: `silent-failure` · `identity` · `environment-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **이름은 클래스를 정하지 못한다.** 클래스 파일을 로드하지 않고 읽는 경로는 `Class` 속성값을 만들 수 없으므로(만들려면 그 클래스를 로드해야 한다) 이름 문자열로 저장한다.\
   이 문자열을 나중에 `Class`로 바꾸려면 "어느 로더로 찾을 것인가"가 필요하다 — 같은 이름도 로더마다 다른 클래스이거나 아예 없을 수 있다.\
   그래서 루트 뷰는 이름 맵과 그 메타데이터를 읽어 들인 로더를 **한 쌍**으로 들고 있다. 로더가 빠진 이름은 해석 방법이 정해지지 않은 반쪽 값이다.
   > **지연 해석(lazy resolution)** — 값을 저장 시점이 아니라 접근 시점에 최종 형태(여기서는 `Class`)로 바꾸는 것. 해석에 필요한 문맥이 접근 시점까지 살아 있어야 한다.

2. **두 갈래로 갈린다.** 파생 뷰는 접근 시점에 "로더가 `null`이면 기본 로더(스레드 컨텍스트 로더, 없으면 앱 로더)로 대체"하는 해석 유틸로 이름을 `Class`로 바꾼다.\
   (참고: JDK의 `Class.forName(name, init, null)`은 `null`을 부트스트랩 로더로 해석한다 — `null`의 뜻이 API마다 달라 더 헷갈린다.)\
   ① 클래스가 커스텀 로더에만 보이면 기본 로더가 찾지 못해 `TypeNotPresentException` — 시끄럽게 실패한다.\
   ② 기본 로더에도 같은 이름이 보이면 **다른 로더가 정의한 `Class`가 조용히 반환된다** — 이름은 맞고 타입 정체성은 틀리다.\
   ②가 더 위험하다: 실패 신호가 없고, 결과가 실행 환경(기본 로더가 무엇을 보느냐)에 따라 달라진다.
   > **스레드 컨텍스트 로더(TCCL)** — 스레드마다 지정된 "기본으로 쓸" ClassLoader. 로더를 명시하지 않은 해석이 흔히 여기로 떨어진다.

3. **루트는 복사되지 않았고, 리플렉션 값은 이미 해석돼 있다.** 루트 뷰는 파생 팩토리를 거치지 않고 그대로 반환되므로 원래 로더를 계속 들고 있었다 — 결함은 "파생" 단계에만 있었다.\
   리플렉션 경로는 속성값이 처음부터 `Class` 객체다. 이미 해석된 값에는 지연 해석이 일어나지 않으므로 로더 자리가 `null`이어도 결과가 바뀌지 않는다.\
   즉 문맥이 필요한지는 "로더 필드가 있는가"가 아니라 **"이 경로에서 지연 해석이 일어나는가"**로 판정한다 — 그래서 수정은 클래스 파일 경로에서만 로더를 넘기고 리플렉션 경로는 `null`로 둔다.

4. **정체성 = 이름 + 정의 로더.** JVM은 런타임 타입을 (이진 이름, 정의 로더) 쌍으로 구분한다. 이름이 같아도 정의 로더가 다르면 `==`는 false, `isAssignableFrom`은 false, 한쪽 인스턴스를 다른 쪽 타입으로 캐스트하면 `ClassCastException`("X cannot be cast to X")이 난다.\
   그래서 ②의 오답은 꺼내는 순간이 아니라 **멀리 떨어진 사용 지점**에서 드러난다 — 타입 비교가 조용히 false가 되어 분기가 바뀌거나, 캐스트에서 이해하기 어려운 예외가 난다.
   > **정의 로더(defining loader)** — 클래스의 바이트를 실제로 `defineClass`한 로더. 부모에게 위임만 한 로더(시작 로더)와 구분된다.

5. **같은 이름·다른 `Class`를 일부러 만든다.** 테스트 대상 클래스 하나만 부모에게 위임하지 않고 스스로 정의하는 **자식 우선 로더**를 만든다 — 그러면 같은 이름이 앱 로더에도 있지만 이 로더로 해석하면 다른 `Class`가 나온다.\
   이 로더로 메타데이터를 읽고 파생 뷰에서 그 속성을 `Class`로 꺼낸 뒤, **그 `Class`의 정의 로더가 커스텀 로더와 같은 객체(isSameAs)**인지 단언한다.\
   고치기 전에는 앱 로더가 정의한 `Class`가 나와 실패하고, 고친 뒤에는 통과한다.\
   "예외가 안 난다"를 단언하면 ②(조용한 오답)를 통과시킨다 — 앱 로더가 같은 이름을 보므로 예외가 나지 않기 때문이다. 단언 대상은 결과의 **정체성**이어야 한다.

6. **문맥 없는 값 + 기본값 대체 = 조용한 오답.** 바이트를 문자열로 바꾸는 charset, 로컬 시각을 시점으로 바꾸는 타임존, 숫자·날짜 서식의 로케일, 권한 판정의 보안 문맥은 모두 "값을 해석하는 데 필요한 문맥"이다.\
   파생·복사 단계에서 이 문맥을 빼고 `null`이면 플랫폼 기본값을 쓰게 하면, 기본값이 원래 문맥과 같은 환경에서는 통과하고 다른 환경에서만 **예외 없이 틀린 값**이 나온다.\
   점검 방법은 **형제 팩토리와의 대칭 비교**다 — 같은 원본에서 다른 뷰를 만드는 형제 팩토리들은 이미 로더를 넘기고 있었고, 한 곳만 `null`이었다. 복사 대상 필드 목록을 나란히 놓으면 빠진 문맥이 보인다.

## 문제 구조 (추상화 코드)

### 변형 A — 파생 팩토리가 해석 문맥(로더)을 떨어뜨림
① 문제 코드
```java
final class View {
    private final Source source;
    private final Map<String, Object> attributes;   // Class 속성은 이름 문자열로 저장
    private final ValueExtractor extractor;
    private final @Nullable ClassLoader loader;     // 이름을 Class로 해석할 문맥

    static View root(Source source, Map<String, Object> attrs, ClassLoader loader) {
        return new View(source, attrs, DEFAULT_EXTRACTOR, loader);      // 루트: 로더 보유
    }

    View derive(Level level) {                                          // 파생 뷰
        return new View(level.source(), this.attributes, this.extractor, null);   // 로더 누락
    }

    Class<?> getClass(String name) {
        Object value = this.extractor.extract(this.attributes, name);
        if (value instanceof String className) {                        // 지연 해석
            return resolve(className, this.loader);                     // null → 기본 로더
        }
        return (Class<?>) value;                                        // 리플렉션 경로: 이미 Class
    }
}
```
② 고친 코드
```java
    View derive(Level level) {
        return derive(level, this.loader);                              // 루트의 로더를 그대로 운반
    }

    private View derive(Level level, @Nullable ClassLoader loader) {    // private 오버로드로 문맥 전달
        return new View(level.source(), this.attributes, this.extractor, loader);
    }
// 리플렉션으로 만든 뷰는 loader = null 유지: 값이 이미 Class라 resolve가 호출되지 않는다
// 형제 팩토리(같은 원본에서 다른 뷰를 만드는 메서드)는 이미 loader를 넘기고 있었다 — 대칭 회복
```
무엇이 깨졌나: 값(이름)은 복사됐지만 그 값을 해석할 문맥(로더)이 복사되지 않아, 접근 시점에 기본 로더로 해석되었다.

### 테스트 기법 — 같은 이름·다른 정체성으로 조용한 오답을 드러냄
```java
class ChildFirstLoader extends ClassLoader {          // 대상 하나만 스스로 정의
    @Override
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        if (name.equals(TARGET)) {
            synchronized (getClassLoadingLock(name)) {
                Class<?> found = findLoadedClass(name);
                if (found == null) {
                    byte[] bytes = readClassBytes(name);
                    found = defineClass(name, bytes, 0, bytes.length);   // 앱 로더와 다른 Class
                }
                return found;
            }
        }
        return super.loadClass(name, resolve);
    }
}

ClassLoader custom = new ChildFirstLoader(appLoader);
View view = readFromClassFile(annotatedType, custom).derive(level);
Class<?> type = view.getClass("value");
assertThat(definingLoaderOf(type)).isSameAs(custom);  // 고치기 전: 앱 로더 → 실패
// assertThatNoException()... 은 부족: 앱 로더도 같은 이름을 보므로 고치기 전에도 통과한다
```
무엇이 드러나나: 결함의 두 갈래 중 조용한 쪽(기본 로더도 이름을 아는 경우)을 정체성 단언으로 재현한다.

## 검증 기록
- 2026-10-20: 사건 기록 대조·추상화(Claude 초안)

## 관련 카드
- [capture-context-at-request-time](../../cross-cutting/concurrency/capture-context-at-request-time/) — 문맥을 실행 시점의 전역 "현재"에서 다시 읽지 말고 값과 함께 운반한다(이 카드는 경합이 아니라 파생 단계의 문맥 누락).
- [execution-context-inheritance](../../cross-cutting/os/execution-context-inheritance/) — 자식 프로세스가 상속받지 못한 실행 문맥이 개발 셸에서만 우연히 맞던 사례.
