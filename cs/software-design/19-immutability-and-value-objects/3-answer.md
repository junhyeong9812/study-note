# software-design/19-immutability-and-value-objects — 정답

## 정답

### 1. 별칭 버그

- 같은 객체를 여러 참조가 가리키므로 한 곳의 변경이 다른 곳에 그대로 보인다. 값(금액·날짜)이 몰래 바뀐다.
- Fowler는 이것을 aliasing bug라고 부르고, 피하려면 값 객체를 불변으로 만들라고 적는다(bliki "ValueObject").

### 2. 공유 가변 Money

(실험 A, JDK 21.0.12, 2026-10-01)

```text
  가변: A=3500 KRW, B=3500 KRW, 캐시=3500 KRW, A==B 같은 객체? true
  불변: A=3500 KRW, B=3000 KRW, 캐시=3000 KRW
```

- 가변: 셋 다 3500. A·B·캐시가 같은 객체다.
- 불변: `add`가 새 객체를 돌려줘 A만 3500, B와 캐시는 3000.

### 3. 해시 키 변이

```text
 버킷[hash("A")] ── Key(code="B")   ← 넣을 때 위치, 지금 값은 "B"
 contains(k)          → hash("B") 버킷을 봄 → 없음
 contains(Key("A"))   → hash("A") 버킷에서 찾지만 equals 거짓 → 없음
```

```text
  size=1, contains(k)=false, contains(new Key("A"))=false, contains(new Key("B"))=false
  remove(k) 후 size=1  (지울 수도 없다)
```

- 원소는 있지만 찾지도 지우지도 못한다. JDK `Set` 문서는 이 경우 동작이 명세되지 않는다고 적는다.

### 4. record의 한계

- record는 "shallowly immutable"이다(JDK 21 `Record` 문서). 구성 요소 참조만 고정하고, 그 참조가 가리키는 리스트 내용은 바뀔 수 있다(실험 C: `OrderShallow.items=[pen, SECRET-ITEM]`).
- 방법: compact 생성자에서 `items = List.copyOf(items)`. 바깥 변경이 안 들어오고 꺼낸 리스트도 수정 불가.
- `unmodifiableList`는 뷰라서 원본이 바뀌면 보인다(`view=[a, b], copy=[a]`). 스냅샷이 아니다.

### 5. 동시 갱신

```text
  기대=200000, 가변 long[] 합=197936, 불변 Money+AtomicReference=200000
```

- 가변 `long[]`: 갱신 유실로 기대보다 작다. 8회 실행(집필 3·점검 5)에서 194596~198092, 실행마다 다르다.
- `AtomicReference`: 8회 모두 200000.
- 정확성을 만든 것은 CAS 재시도다. 불변은 읽는 쪽이 반쯤 바뀐 객체를 보지 않게 할 뿐, "현재 값 교체"의 경쟁을 없애지 않는다.

### 6. 비용과 영속 구조

- 비용: 변경마다 새 객체. 큰 컬렉션 전체를 복사하면 비싸다.
- 영속 자료구조는 새 버전이 옛 버전의 대부분을 공유한다.
- `v2.tail()==v1? true`: 앞에 원소를 붙인 새 리스트가 옛 리스트를 복사하지 않고 그대로 가리킨다(구조 공유). 옛 버전 `v1=[b,c]`도 그대로 남는다.

### 7. BigDecimal

```text
  total.add(5) 후 total=100, 대입하면=105
equals=false compareTo=0 hash=621/6202
record Money(2.0).equals(Money(2.00))=false
```

- `add`는 새 객체를 돌려준다. 결과를 버리면 `total`은 100 그대로, 에러도 없다(Error Prone `ReturnValueIgnored`가 잡는다).
- `BigDecimal.equals`는 scale까지 비교해 `2.0`≠`2.00`이다. 그래서 record `Money`도 같지 않다. 같은 금액으로 보려면 생성자에서 scale을 정규화한다.

### 8. 불변 대상과 가변 허용

- 불변: 값(금액·기간·주소·ID), 공유되는 것(캐시 값·설정·이벤트·메시지), 해시·정렬 키.
- 가변 허용: 엔티티(식별자가 있고 생애 동안 상태가 바뀌는 주문·회원).
- 가변 쪽 규칙: 상태는 의도를 드러내는 메서드로만 바꾸고(setter 남발 금지), 엔티티가 가진 값들은 불변 값 객체로 둔다. 엔티티를 해시 키로 쓰지 말고 불변 ID를 키로 쓴다.

### 9. 할증이 모두에게

- 의심: 캐시·싱글턴·static 상수가 가변 값 객체를 공유하고, 어느 호출자가 그 객체 자체를 바꿨다(별칭 버그). 재시작하면 캐시가 다시 채워져 잠시 정상이다.
- 확인: 캐시 값을 시작 직후와 지금 비교하고, 값 객체에 상태를 바꾸는 메서드(`add`가 `this` 반환, setter)가 있는지 본다. 힙 덤프에서 캐시가 가리키는 객체 값을 확인한다.
- 수정: 값 객체를 불변으로(연산은 새 객체 반환). 당장은 캐시가 복사본을 돌려주게 막는다.
