# 11. `serialVersionUID`와 클래스 호환성 (리뷰 finding R2)

> 리뷰어(Opus·codex 양쪽)가 지적한 것: **"`private final` -> `private transient`로 바꾸면 기본 `serialVersionUID`가 바뀐다."**
> 실측으로 확인했고, 이 문서는 그 동작 원리를 정리한다.

## 1. `serialVersionUID`가 하는 일

직렬화된 바이트에는 클래스 **이름**과 함께 `serialVersionUID`라는 숫자가 실린다. 역직렬화할 때 JVM은 이렇게 확인한다.

```
스트림에 실린 UID  ==  현재 classpath에 있는 클래스의 UID  ?
   ├─ 같다 → 진행 (필드 매칭 단계로)
   └─ 다르다 → InvalidClassException: local class incompatible
                stream classdesc serialVersionUID = -4882614078662365050,
                local class serialVersionUID = 1724818276882560505
```

즉 **"쓸 때의 클래스와 읽을 때의 클래스가 같은 버전인가"** 를 판정하는 지문(fingerprint)이다.

## 2. 선언하지 않으면 자동 계산된다

UID는 직접 선언할 수도 있고, 두지 않으면 JVM이 클래스 구조에서 계산한다.

```java
private static final long serialVersionUID = 1L;   // 이렇게 선언하면 그 값이 고정
```

선언하지 않으면 JVM이 **클래스 구조를 해싱해서** 계산한다. 문제는 이 계산의 입력이 무엇이냐다.

Java Object Serialization Specification(§4.6)에 따르면 해시 입력에는 다음이 들어간다.

- 클래스 이름, 클래스 modifier
- 구현한 인터페이스 이름들(정렬)
- **필드** — 이름·modifier·타입 (정렬)
  - 단, **`private static` 필드와 `private transient` 필드는 제외**
- 생성자·메서드 시그니처 (private 메서드 제외)

여기서 핵심은 이 한 줄이다.

> **`private transient` 필드는 UID 계산에서 빠진다.**

그래서 `private final AnnotatedElementSupplier ...`(해시에 **포함**)를 `private transient AnnotatedElementSupplier ...`(해시에서 **제외**)로 바꾸면, 필드 값이 실리느냐 마느냐 이전에 **클래스의 지문 자체가 달라진다.**

## 3. 이번 케이스 실측

`ObjectStreamClass.lookup(TypeDescriptor.class)`로 직접 확인했다.

```java
ObjectStreamClass osc = ObjectStreamClass.lookup(TypeDescriptor.class);
System.out.println("serialVersionUID = " + osc.getSerialVersionUID());
for (var f : osc.getFields()) {
    System.out.println("  serialized field: " + f.getType().getSimpleName() + " " + f.getName());
}
```

**before (upstream 원본)**
```
serialVersionUID = -4882614078662365050
  serialized field: AnnotatedElementAdapter annotatedElement
  serialized field: AnnotatedElementSupplier annotatedElementSupplier      ← 있음
  serialized field: ResolvableType resolvableType
  serialized field: Class type
```

**after (수정본)**
```
serialVersionUID = 1724818276882560505
  serialized field: AnnotatedElementAdapter annotatedElement
  serialized field: ResolvableType resolvableType
  serialized field: Class type
```

UID가 완전히 다른 값으로 바뀌었고 직렬화 대상 필드가 4개 -> 3개가 됐다.

## 4. 두 가지 실패 모드 — 어디서 터지느냐가 다르다

구버전이 쓴 스트림을 신버전이 읽을 때의 결말은 UID를 고정했는지에 따라 갈린다.

```
구버전(6.2.x/7.0)이 쓴 스트림  ─────▶  신버전(수정본)이 읽기
                                        │
                    ┌───────────────────┴────────────────────┐
                    │                                        │
          UID를 고정하지 않은 경우            UID를 예전 값으로 고정한 경우
                    │                                        │
                    ▼                                        ▼
      (1) InvalidClassException                   (2) readObject 까지 진행됨
         (readObject 진입 전에 즉시 실패)            - 스트림의 supplier 필드는 클래스에
         시끄럽게 실패 = 즉시 인지 가능               없으므로 읽고 버림
                                                   - annotatedElement 는 구버전이
                                                     강제 해석을 안 했으니 대개 null
                                                   → EMPTY 로 정규화
                                                   → **어노테이션이 조용히 사라짐**
```

**이 프로젝트의 선택은 (1)이다.** 이유:

- `TypeDescriptor`는 원래 `@SuppressWarnings("serial")`이고 `serialVersionUID`를 선언하지 않는다 = **버전 간 wire 호환을 보장 대상으로 삼은 적이 없다**
- (2)는 "읽히긴 하는데 데이터가 조용히 유실"되는 형태다. 조용한 손실보다 **즉시 예외**가 낫다
- 애초에 구버전에서 `Field`/`MethodParameter`/`Property` 기반 스트림은 **쓰이지도 못했다**(그게 이 버그다). 존재할 수 있는 구스트림은 `Annotation[]` 경로뿐

대신 이 사실을 **PR 본문에 명시**한다 — "포맷이 바뀐다" 수준이 아니라 "구스트림은 `InvalidClassException`으로 거부된다"까지.

## 5. UID가 같을 때의 필드 매칭 규칙 (참고)

UID가 일치하면 필드 이름·타입으로 매칭하며, 불일치는 다음과 같이 흡수한다.

| 상황 | 동작 |
|---|---|
| 스트림에 있는데 클래스에 없는 필드 | 읽고 **버린다** |
| 클래스에 있는데 스트림에 없는 필드 | **기본값**(null/0/false) |
| 이름 같고 타입 다름 | `InvalidClassException` |

이 규칙 덕분에 "필드 추가/삭제"는 UID만 고정하면 대체로 호환된다. **그래서 UID 고정은 강력한 도구지만, 위 (2)처럼 의미 손실을 감추는 부작용도 함께 온다.**

## 6. 손으로 확인하기

한 파일로 재현하기는 어렵고(같은 클래스의 두 버전이 필요하다), 다음 절차로 확인할 수 있다.

```java
// Uid.java — UID 출력기
import java.io.ObjectStreamClass;

public class Uid {
    public static void main(String[] args) throws Exception {
        ObjectStreamClass osc = ObjectStreamClass.lookup(Class.forName(args[0]));
        System.out.println("serialVersionUID = " + osc.getSerialVersionUID());
        for (var f : osc.getFields()) {
            System.out.println("  " + f.getType().getSimpleName() + " " + f.getName());
        }
    }
}
```

```java
// Sample.java — 이 파일의 필드 수식어만 바꿔가며 비교한다
import java.io.Serializable;
import java.util.function.Supplier;

public class Sample implements Serializable {
    interface Recipe extends Supplier<String>, Serializable {}

    private final String kept = "x";
    private final Recipe recipe = () -> "hi";   // ← 여기를 private transient Recipe 로 바꿔본다
}
```

```bash
javac -d /tmp/uid Sample.java Uid.java
java -cp /tmp/uid Uid Sample        # UID 기록

# Sample.java 에서 recipe 를 private transient 로 바꾸고
javac -d /tmp/uid Sample.java
java -cp /tmp/uid Uid Sample        # UID 가 달라지는 것을 확인
```

### 실측 결과 (2026-08-04, 위 `Sample`의 필드 수식어만 바꿔가며)

| 필드 선언 | serialVersionUID | 직렬화 필드 수 |
|---|---|---|
| `private final Recipe recipe` | `-26010919696535423` | 2 |
| `private Recipe recipe` (final만 제거) | `-6613838324674247269` | 2 |
| `private transient Recipe recipe` | `-4500531582251205744` | 1 |
| `private final transient Recipe recipe` | `-4500531582251205744` | 1 |

읽어낼 수 있는 것이 세 가지다.

1. **`final`을 떼는 것만으로도 UID가 바뀐다** — 해시 입력에 필드의 **modifier**가 포함되기 때문. 즉 이번 변경은 두 요인(final 제거 + transient 추가)이 겹쳐 있고, 어느 쪽이든 결론은 같다.
2. **`private transient`가 되는 순간 필드가 해시에서 통째로 빠진다** — 그래서 3행과 4행의 UID가 **완전히 동일**하다. private transient 필드에는 `final`이 붙든 말든 UID에 영향이 없다.
3. 직렬화 필드 수가 2 -> 1로 줄어드는 것도 같은 지점에서 확인된다.

## 7. 실무 교훈

1. `Serializable`을 선언한 클래스는 **필드 수식어만 바꿔도 wire 호환이 깨질 수 있다.**
2. 호환을 원하면 처음부터 `serialVersionUID`를 명시적으로 선언해야 한다.
3. 반대로 **호환을 보장하고 싶지 않다면** 선언하지 않는 편이 낫다 — 구조가 바뀌면 시끄럽게 실패하므로 조용한 의미 손실을 피할 수 있다.
4. 라이브러리 코드에서 이런 변경을 할 때는 **실패 모드가 무엇인지**(예외냐 무음 손실이냐)를 PR에 적어야 한다. 이번 R2 finding의 실질도 코드 수정이 아니라 **이 사실을 문서화하라**는 것이었다.

## 참고

- 이 finding의 처리 결과: `log.md` 리뷰 ledger **R2**
- 관련 개념: [03 직렬화 기본](03-serialization-basics.md) · [04 transient와 volatile](04-transient-and-volatile.md) · [05 직렬화 훅](05-serialization-hooks.md)
