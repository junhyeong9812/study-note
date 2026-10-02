# software-design/20-oop-fundamentals — 정답

## 정답

### 1. 데이터와 규칙을 묶는 이유

- 떨어져 있으면 규칙(예: 잔액 ≥ 0, 합계 = 항목 합)을 지키는 일이 데이터를 만지는 **코드마다** 각자의 몫이 된다. 한 곳만 빠뜨려도 무효 상태가 저장된다.
- 객체로 묶으면 상태를 바꾸는 길이 객체의 메서드로 좁아지고, 규칙은 그 메서드 **한 곳**에서 지킨다. 규칙이 바뀌어도 고칠 곳이 한 곳이다.

### 2. private + getter/setter 전부 = 캡슐화인가

- 아니다(대개). 바꾸는 길이 공개 필드와 같은 수만큼 열려 있고, setter에 규칙이 없으면 바깥이 불변식을 깰 수 있다.
- 판정 기준: **상태를 바꾸는 길이 몇 개이고, 그 길에 불변식 검사가 있나.** 접근 제어자는 수단일 뿐이다.
- 예외: 불변식이 없는 데이터 운반체(DTO·설정)는 setter가 있어도 지킬 규칙이 없다.

### 3. 실험 A 예측

(실험, JDK 21.0.12, `Encap.java`)

```text
[open] 리스트 직접 add  total=1000 invariant=false
[open] setTotal(-200)   total=-200 invariant=false
[encap] lines().add     -> UnsupportedOperationException, total=1000 invariant=true
```

- `getLines()`가 내부 리스트 참조를 그대로 줘서 항목만 늘고 합계는 그대로 → `false`.
- `setTotal(-200)` → 음수 합계, `false`.
- `Order.lines()`는 `List.copyOf` 사본이라 `add`가 `UnsupportedOperationException`. 내부 상태는 그대로 `true`.

### 4. 무엇이 동적으로 골라지나

(실험 B 출력)

```text
a.speak() = 멍
a.name    = animal
a.kind()  = Animal.kind
```

| 호출 | 결과 | `javap -c` 명령 | 고르는 기준 |
|---|---|---|---|
| `a.speak()` | 멍 | `invokevirtual` | 실제 타입 `Dog` |
| `a.name` | animal | `getfield` | 선언 타입 `Animal` |
| `a.kind()` | Animal.kind | `invokestatic` | 선언 타입 `Animal` |

- 바이트코드에는 셋 다 `Dispatch$Animal`이 적혀 있다. `invokevirtual`만 실행 시점에 수신 객체의 클래스에서 구현을 다시 찾는다(JVMS §6.5). 인터페이스 호출은 `invokeinterface`.
- 필드와 static 메서드는 재정의가 아니라 숨김이다.

### 5. 추상 클래스 vs 인터페이스

- 추상 클래스: 상태(필드)·생성자·일부 구현을 가질 수 있고, `extends`는 하나만. "공통 골격"을 물려준다.
- 인터페이스: 상태 없음(상수만), 추상 메서드 + 구현을 가진 `default`·`static`(자바 8+)·`private`(자바 9+) 메서드, 여러 개 구현 가능. "역할"을 약속한다.
- `new Shape()`(추상): 자바는 **컴파일 시점**에 `error: Shape is abstract; cannot be instantiated`. 파이썬 `abc`는 **인스턴스를 만들 때(실행 시점)** `TypeError`(원본 §17).

### 6. Square extends Rectangle

- `Rectangle`의 약속은 "너비와 높이를 따로 바꿀 수 있다"이다. `Square`는 이 약속을 지킬 수 없다(너비를 바꾸면 높이도 바뀜). `setWidth(5); setHeight(4)` 뒤 넓이 20을 기대한 호출자가 16을 받는다([22-solid](../22-solid/2-summary.md) 실험).
- IS-A는 **개념상 종류가 아니라 상위 타입의 행동 약속을 다 지킬 수 있는가**로 판정한다(LSP). 못 지키면 능력별 인터페이스나 HAS-A로 바꾼다.

### 7. vtable

- 클래스마다 "메서드 슬롯 번호 → 구현" 표(vtable)를 둔다. HotSpot(JDK 21) 소스 `klassVtable.hpp`가 "variable-length vtable that is embedded in InstanceKlass"라고 설명하고, 인터페이스용 `klassItable`도 있다.
- 하위 클래스는 재정의한 메서드의 슬롯만 자기 구현으로 바꾼다. 그래서 호출부는 "그 객체 클래스의 vtable[k]"로만 점프하면 되고, 새 하위 클래스가 생겨도 호출부 코드는 바뀌지 않는다.
- JIT은 인라인 캐시(`compiledIC`) 등으로 표 조회를 더 줄인다 — 세부는 language/17(미작성).

### 8. 합계 불일치, 에러 로그 없음

- 먼저 볼 곳: `Order`의 상태를 바꾸는 길 전부 — 공개 setter(`setTotal`·`setLines`), 내부 컬렉션을 그대로 내주는 getter, 그것을 쓰는 호출부(`getLines().add/remove` 검색).
- 원인 후보: 어떤 경로가 항목만 바꾸고 합계를 안 고쳤다(실험 A의 "리스트 직접 add").
- 대처: 항목·합계를 함께 바꾸는 행동 메서드(`addLine`)만 남기고, 컬렉션은 사본으로 반환. 불변식 검사를 그 메서드에 둔다. 이미 저장된 불일치 데이터는 별도 보정 작업으로 찾아 고친다.

### 9. 파이썬 네임 맹글링

(실험, Python 3.12.3, `hiding.py`)

```text
5000
{'user': 'greg', '_Account__balance': 5000, '__balance': -3000}
-3000
```

- `get_balance()`는 **5000**이다. 클래스 안의 `__balance`는 `_Account__balance`로 바뀌었고, 바깥에서 대입한 `__balance`는 별개의 새 속성이다.
- `acct._Account__balance = -3000`을 하면 `get_balance()`가 -3000이 된다. 맹글링은 이름 충돌 방지이지 강제 은닉이 아니다.
- 원본 §11은 "-3000이 나오는데"라고 썼지만 실행 결과는 5000이다. 원본도 바로 뒤의 `__dict__` 출력에서 `_Account__balance: 5000`을 보여 준다.
