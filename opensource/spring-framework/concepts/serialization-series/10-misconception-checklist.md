# 10. 오해 체크리스트 — 자가 점검용

> 2026-08-04 작업 대화에서 **실제로 걸렸던 지점들**을 문답으로 정리했다.
> 답을 가리고 스스로 답해본 뒤 펼쳐 보는 용도. 각 항목 끝에 해당 개념 문서를 달아뒀다.

---

### Q1. `Serializable`이 아닌 값을 필드에 담으면 컴파일 오류가 나나?

<details><summary>답</summary>

**아니다. 컴파일은 100% 성공한다.** 직렬화 가능 여부는 javac의 검사 대상이 아니다. `ObjectOutputStream.writeObject()`를 실제로 호출하는 **런타임**에만 드러난다.

실제로 이번 작업의 RED 테스트에서 `compileTestJava`는 성공했고 테스트 **실행** 단계에서 실패했다. -> [01](01-compile-vs-runtime.md)
</details>

---

### Q2. 객체를 힙에 올릴 때 직렬화가 함께 일어나나?

<details><summary>답</summary>

**아니다. 완전히 별개다.** `new`는 힙에 객체를 만들 뿐이고, 직렬화는 **누군가 `writeObject()`를 호출해야만** 시작된다. 실무에서 그 "누군가"는 보통 프레임워크(세션 복제·분산 캐시·원격 호출)다. -> [02](02-heap-and-object-graph.md), [03](03-serialization-basics.md)
</details>

---

### Q3. "직렬화는 객체 상태를 메모리에 올리는 것"이 맞나?

<details><summary>답</summary>

**방향이 반대다.**
- 직렬화: 힙의 객체 -> 바이트 (**밖으로 꺼내 납작하게**)
- 역직렬화: 바이트 -> 힙의 새 객체 (**다시 메모리에 세움**)

-> [03](03-serialization-basics.md)
</details>

---

### Q4. 직렬화하면 바이트코드(클래스 코드)가 실리나?

<details><summary>답</summary>

**아니다. 상태만 실린다.** 스트림에 들어가는 것은 클래스 **이름**, `serialVersionUID`, non-transient·non-static **필드 값**뿐이다. 그래서 받는 쪽 JVM에도 같은 클래스가 classpath에 있어야 한다. -> [03](03-serialization-basics.md)
</details>

---

### Q5. `transient`를 붙이면 그 필드는 항상 `null`이 되나?

<details><summary>답</summary>

**아니다.** 살아 있는 객체에서는 값이 멀쩡히 들어 있고 정상 동작한다. `transient`는 **직렬화기에게만** 하는 말이다. 값이 비는 것은 **역직렬화로 새로 만들어진 객체**뿐이다. -> [04](04-transient-and-volatile.md)
</details>

---

### Q6. 직렬화가 실패한 원인이 `final` 때문인가?

<details><summary>답</summary>

**아니다.** 원인은 **람다가 캡처한 값의 타입**(`Field`/`MethodParameter`/`Property`)이다. `final`을 뗀 것은 `transient`를 붙인 **결과** `readObject`에서 다시 대입해야 해서다. 인과 순서를 뒤집지 말 것. -> [04](04-transient-and-volatile.md), [06](06-lambda-internals.md)
</details>

---

### Q7. `interface X extends Supplier<Adapter>, Serializable`은 `Adapter`의 부모를 상속하는 건가?

<details><summary>답</summary>

**아니다.** `Supplier`와 `Serializable` 두 인터페이스를 상속하는 것이고, `<Adapter>`는 **`get()`의 반환 타입**을 지정하는 제네릭 인자일 뿐이다. 게다가 제네릭은 컴파일 시점 개념이라 런타임에는 소거된다. -> [01](01-compile-vs-runtime.md)
</details>

---

### Q8. `getAnnotatedElement()`는 어느 필드를 읽고 어느 필드를 쓰나?

<details><summary>답</summary>

**supplier(76번 줄)를 읽어서 실행하고, 그 결과를 캐시(78번 줄)에 쓴다.** 실행 후 값이 달라지는 쪽은 **78번**이다. supplier는 생성자에서 이미 채워져 있고 이 메서드가 건드리지 않는다.

반대로 이해하면 `writeObject`가 왜 그 메서드를 부르는지가 설명되지 않는다. -> [02](02-heap-and-object-graph.md), [05](05-serialization-hooks.md)
</details>

---

### Q9. `writeObject`에서 `getAnnotatedElement()`를 호출하고 반환값을 버리는데, 그래도 되나?

<details><summary>답</summary>

**된다. 목적이 반환값이 아니라 부작용이기 때문이다.** 그 메서드가 내부에서 `this.annotatedElement = ...` 대입을 수행하므로, 호출만으로 캐시가 채워진다. 그 상태에서 `defaultWriteObject()`를 부르면 채워진 어댑터가 스트림에 실린다. -> [05](05-serialization-hooks.md)
</details>

---

### Q10. `writeObject`에서 그 호출을 생략하면 어떻게 되나?

<details><summary>답</summary>

캐시가 `null`인 채로 실리고, 받는 쪽은 supplier(transient -> null)도 캐시(null)도 없어 **어노테이션이 영구 소실**된다. 이후 접근 시 NPE 위험도 생긴다. -> [05](05-serialization-hooks.md), [09](09-case-study-typedescriptor.md)
</details>

---

### Q11. 역직렬화하면 생성자가 실행되나?

<details><summary>답</summary>

**아니다.** JVM이 인스턴스 공간만 확보하고 스트림 값을 필드에 직접 밀어 넣는다(`Serializable`이 아닌 첫 부모의 no-arg 생성자만 실행). **따라서 생성자·정적 팩토리에 넣어둔 규칙은 전부 우회된다.** -> [05](05-serialization-hooks.md)
</details>

---

### Q12. 어노테이션이 0개인 어댑터를 역직렬화하면 `isEmpty()`가 true인가?

<details><summary>답</summary>

**false다.** `isEmpty()`는 `this == EMPTY` **동일성 비교**인데, 역직렬화는 `from()` 팩토리를 거치지 않고 새 인스턴스를 만든다. 그 클래스에 `readResolve()`도 없다. 그래서 배열 길이가 0이어도 EMPTY와 다른 객체다.

결과값은 여전히 맞지만 `hasAnnotation()`의 빠른 경로가 죽는다 — **예외가 아니라 조용한 성능 저하**. -> [08](08-identity-and-singleton.md)
</details>

---

### Q13. `readObject`의 `AnnotatedElementAdapter.from(...)`은 null 가드인가?

<details><summary>답</summary>

**아니다. 싱글턴 정규화(canonicalization)다.** 배열 길이가 0이면 `from()`이 `EMPTY`를 돌려주므로, 역직렬화로 깨진 동일성이 복구되고 shortcut이 되살아난다. -> [08](08-identity-and-singleton.md)
</details>

---

### Q14. 역직렬화 후 설치하는 `() -> annotatedElement` 람다는 원래 람다를 복원한 것인가?

<details><summary>답</summary>

**아니다. 다른 람다다.** 원래 람다가 붙들던 `Field`는 스트림에 실리지 않아 영원히 사라졌고, 새 람다는 **이미 완성된 결과만 반환**한다. 재료는 없지만 겉보기 동작은 동일하다. -> [06](06-lambda-internals.md)
</details>

---

### Q15. 필드 수식어만 바꾸면 직렬화 호환성에는 영향이 없나?

<details><summary>답</summary>

**있다.** `private final` -> `private transient`로 바꾸면 기본 `serialVersionUID`가 달라져 **구버전 스트림이 `InvalidClassException`으로 거부**된다. 실측: `-4882614078662365050` -> `1724818276882560505`.

추가로 `final`만 떼도 UID가 바뀌고, `private transient`가 되는 순간 필드가 해시에서 통째로 빠져 `private final transient`와 UID가 같아진다. -> [11](11-serialversionuid.md)
</details>

---

### Q16. 테스트에서 직렬화 전에 `getAnnotations()`를 미리 불러도 상관없나?

<details><summary>답</summary>

**상관있다.** 미리 부르면 캐시가 채워져서, `writeObject`의 강제 해석을 빠뜨린 **반쪽 fix도 초록으로 통과**한다(가짜 green). 그래서 헬퍼는 일부러 미리 해석하지 않고, 기대값도 원본 descriptor가 아니라 `field`/`methodParameter`에서 직접 뽑는다. -> [09](09-case-study-typedescriptor.md)
</details>

---

## 한 장 요약 — 이 케이스의 개념 지도

각 문서가 다음 문서로 넘겨주는 결론을 한 줄씩 이으면 이 케이스의 개념 지도가 된다.

```
컴파일 vs 런타임 (01) ──▶ "직렬화 불가"는 런타임 예외다
        │
힙·객체 그래프 (02) ──▶ 직렬화는 그래프 순회다
        │
직렬화 기본 (03) ──────▶ 상태만 실리고, 자동으로 일어나지 않는다
        │
transient/volatile (04) ▶ 스트림에서 뺄 필드를 고른다
        │
직렬화 훅 (05) ────────▶ 뺀 자리를 write/read 시점에 메운다 (생성자 우회!)
        │
람다 내부 (06) ────────▶ 문제의 뿌리: 캡처값이 함께 직렬화된다
        │
리플렉션 객체 (07) ────▶ 캡처값이 하필 직렬화 불가능한 것들이었다
        │
동일성·싱글턴 (08) ────▶ 되살릴 때 싱글턴이 깨진다 → 정규화 필요
        │
serialVersionUID (11) ─▶ 필드 수식어를 바꾸면 wire 호환이 깨진다
```
