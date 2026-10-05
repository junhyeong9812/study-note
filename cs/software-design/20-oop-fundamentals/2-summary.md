# software-design/20-oop-fundamentals — 캡슐화·상속·다형성·추상 클래스, IS-A/HAS-A — 정리 (힌트)

## 해결하는 문제

데이터와 그 데이터를 바꾸는 규칙이 떨어져 있으면, 규칙을 지키는 일이 데이터를 만지는 **곳마다** 각자의 몫이 된다.

```text
 데이터와 규칙이 따로                         객체(데이터 + 규칙)
 ┌──────────┐                                 ┌────────────────────────┐
 │ balance  │ <── 화면 코드가 직접 -=          │ Account                │
 │ (공개)   │ <── 배치 코드가 직접 =           │  balance (숨김)         │
 └──────────┘ <── 정산 코드가 직접 +=          │  withdraw(n) ── 규칙 ── │ <── 모두 이 문으로만
   "잔액 ≥ 0" 규칙을 세 곳이 각자 지켜야 한다    └────────────────────────┘
   한 곳이 빠뜨리면 잔액이 음수가 된다            규칙은 한 곳에서 지킨다
```

- *객체(object)*: 상태(필드)와 그 상태를 다루는 행동(메서드)을 한 단위로 묶은 것.
- *불변식(invariant)*: 객체가 살아 있는 동안 지켜져야 하는 조건. 예: 잔액 ≥ 0, 주문 합계 = 항목 금액의 합.

쉬운 예: 자판기다. 손님은 동전을 넣고 버튼을 누를 뿐, 금고를 열어 거스름돈을 직접 꺼내지 않는다.\
똑같은 구조다.\
실무 예: 주문(Order)의 합계·항목 목록, 계좌 잔액, 재고 수량. 이것들을 아무 코드나 바꿀 수 있으면 "합계 ≠ 항목 합"인 주문이 DB에 저장된다.

이 노트는 객체지향의 네 도구(캡슐화·상속·다형성·추상 클래스)와 두 관계(IS-A·HAS-A)를 **변경과 불변식의 관점**에서 정리한다.\
기초(파이썬으로 본 클래스·메서드의 정체, `self`, 클래스 멤버, 네임 맹글링, 프로퍼티, `abc`, Character 계층 예제)는 원본 [foundations/oop-basics](../../foundations/oop-basics/README.md) §4~§18에 있다.

## 동작·원리

### 1. 캡슐화 — 상태를 바꾸는 문을 좁힌다

```text
 캡슐화 붕괴 (getter/setter 전부 공개)          캡슐화 (행동 메서드만 공개)
 ┌──────────────────────────┐                  ┌──────────────────────────┐
 │ OpenOrder                │                  │ Order                    │
 │  - lines: List           │                  │  - lines: List           │
 │  - total: int            │                  │  - total: int            │
 │ + getLines(): List  ──────┼─ 내부 리스트 참조 │ + addLine(price)  ───────┼─ 검사 + lines·total 함께 갱신
 │ + setLines(List)         │   그대로 밖으로    │ + lines(): List (사본)   │
 │ + getTotal() / setTotal()│                  │ + total()                │
 └──────────────────────────┘                  └──────────────────────────┘
  바꾸는 길: 4개 이상, 규칙 없음                  바꾸는 길: 1개, 규칙 있음
```

- *캡슐화(encapsulation)*: 상태와 행동을 묶고, 상태를 바꾸는 길을 객체 자신의 메서드로 제한하는 것.
- *정보 은닉(information hiding)*: 바뀔 수 있는 내부 결정(표현 방식 등)을 바깥에서 못 보게 숨기는 것. Parnas 1972의 분해 기준이다. 접근 제어자(`private`)는 그 수단 중 하나다.
- private 필드에 getter/setter를 하나씩 다 붙이면 문법상 `private`이지만 바꾸는 길은 공개 필드와 같다. **접근 제어자가 아니라 "상태를 바꾸는 길이 몇 개이고 그 길에 규칙이 있나"가 캡슐화를 정한다.**

### 실험 A: getter/setter 전부 공개 vs 행동 메서드

```java
static class OpenOrder {                       // 불변식: total == sum(lines) && total >= 0
    private List<Integer> lines = new ArrayList<>();
    private int total;
    public List<Integer> getLines() { return lines; }
    public void setTotal(int t) { this.total = t; }
    // ...
}
static final class Order {
    private final List<Integer> lines = new ArrayList<>();
    private int total;
    public void addLine(int price) {
        if (price <= 0) throw new IllegalArgumentException("price must be > 0: " + price);
        lines.add(price);
        total += price;
    }
    public List<Integer> lines() { return List.copyOf(lines); }   // 읽기 전용 사본
    public int total() { return total; }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/20/e20/Encap.java`, 2026-10-02)

```text
[open] 정상 사용        total=1000 invariant=true
[open] 리스트 직접 add  total=1000 invariant=false
[open] setTotal(-200)   total=-200 invariant=false
[encap] addLine(1000)   total=1000 invariant=true
[encap] lines().add     -> UnsupportedOperationException, total=1000 invariant=true
[encap] addLine(-200)   -> price must be > 0: -200, total=1000 invariant=true
```

- 관찰: 공개 getter가 내부 리스트 참조를 그대로 내주자, 바깥 코드가 항목만 추가해 합계가 어긋났다. setter로 음수 합계도 들어갔다. 둘 다 컴파일·실행 모두 조용히 통과했다.
- 관찰: 캡슐화한 쪽은 바깥에서 리스트를 고치려 하면 `UnsupportedOperationException`, 잘못된 금액은 `IllegalArgumentException`으로 거절했고 불변식이 유지됐다.
- 해석: 불변식을 깨뜨릴 수 있는 길의 수가 곧 "규칙을 기억해야 하는 곳의 수"다.

### 2. 상속과 다형성 — 같은 호출, 다른 구현

```text
           ┌───────────────┐
           │ Animal        │  speak()  ← 인스턴스 메서드: 실행 시점의 실제 타입으로 고른다
           │ name="animal" │  kind()   ← static: 컴파일 시점의 선언 타입으로 고른다
           └───────▲───────┘
                   │ extends (IS-A)
           ┌───────┴───────┐
           │ Dog           │  speak() 재정의(override)
           │ name="dog"    │  kind()  같은 이름 static → 재정의가 아니라 숨김(hiding)
           └───────────────┘
   Animal a = new Dog();   선언 타입 = Animal, 실제 타입 = Dog
```

- *상속(inheritance)*: 기존 클래스의 필드·메서드를 물려받아 새 클래스를 만드는 것. 자바에서는 `extends`(구현 상속)와 `implements`(인터페이스 상속)가 있다.
- *다형성(polymorphism)*: 같은 메서드 호출이 실제 객체의 타입에 따라 다른 구현으로 실행되는 성질.
- *동적 디스패치(dynamic dispatch)*: 호출할 구현을 실행 시점에 실제 타입으로 고르는 것.
- *재정의(override)*: 하위 클래스가 상위의 인스턴스 메서드를 같은 시그니처로 다시 구현하는 것.

### 실험 B: 무엇이 동적으로 골라지나

(실험, JDK 21.0.12 temurin, `scratchpad/sd/20/e20/Dispatch.java`, `javap -c` 일부, 2026-10-02)

```text
a.speak() = 멍
a.name    = animal
a.kind()  = Animal.kind
g.greet() = 안녕
      12: invokevirtual #16                 // Method Dispatch$Animal.speak:()Ljava/lang/String;
      27: getfield      #32                 // Field Dispatch$Animal.name:Ljava/lang/String;
      43: invokestatic  #37                 // Method Dispatch$Animal.kind:()Ljava/lang/String;
      66: invokeinterface #44,  1           // InterfaceMethod Dispatch$Greeter.greet:()Ljava/lang/String;
```

- 관찰: 바이트코드에는 세 곳 모두 **선언 타입 `Animal`** 이 적혀 있다. 그런데 `speak()`만 `Dog` 구현이 실행됐다.
- `invokevirtual`·`invokeinterface`: 실행 시점에 수신 객체의 실제 클래스에서 구현을 찾는다(JVMS §6.5). 그래서 `멍`.
- `getfield`(필드)와 `invokestatic`(static 메서드): 컴파일 때 정한 대상으로 고정된다. 그래서 `animal`, `Animal.kind`. **필드와 static 메서드는 다형적이지 않다.**

### 3. 추상 클래스와 인터페이스

```text
 추상 클래스 Shape                      인터페이스 Greeter
 ┌──────────────────────┐              ┌──────────────────────┐
 │ 상태(필드)·생성자 가능 │              │ 상태 없음(상수만)      │
 │ 일부 구현 + abstract  │              │ 추상 + default 등      │
 │ 단일 상속(extends 1개) │              │ 여러 개 구현 가능      │
 └──────────────────────┘              └──────────────────────┘
   "공통 골격을 물려준다"                   "할 수 있는 일(역할)을 약속한다"
```

- *추상 클래스(abstract class)*: 인스턴스를 만들 수 없고, 하위 클래스가 채울 추상 메서드를 가질 수 있는 클래스.
- *인터페이스(interface)*: 메서드 약속을 정의한 타입. 인스턴스 필드(상태)는 없다. 구현을 가진 메서드는 `default`·`static`(자바 8부터), `private`(자바 9부터, JEP 213)만 둘 수 있다.

(실험, JDK 21.0.12, `scratchpad/sd/20/e20/AbstractNew.java`)

```text
AbstractNew.java:3: error: Shape is abstract; cannot be instantiated
    public static void main(String[] args) { Shape s = new Shape(); }
                                                       ^
1 error
```

- 파이썬 `abc`는 이 검사를 **인스턴스를 만들 때(실행 시점)** 한다(원본 §17). 자바는 컴파일 시점에 막는다.
  - (실험, Python 3.12.3) `A()` → `TypeError Can't instantiate abstract class A without an implementation for abstract method 'eat'`
- Bloch는 『Effective Java』 3판 4장에서 상속용 설계를 따로 다룬다(Item 19 "Design and document for inheritance or else prohibit it"). 추상 클래스 대신 인터페이스를 권하는 항목은 Item 20이다(요약 저장소로 번호만 확인 [?]).

### 4. IS-A와 HAS-A

```text
 IS-A (상속)                      HAS-A (합성·통합)
 Laptop ──extends──> Computer     Computer ◆──> CPU    합성: 함께 생기고 함께 사라진다
                                  Police   ◇──> Gun    통합: 따로 생기고, 나중에 쥐었다 놓는다
 "Laptop은 Computer의 한 종류"      "Computer는 CPU를 가진다"
```

- *IS-A*: "A는 B의 한 종류다". 상속으로 표현한다.
- *HAS-A*: "A는 B를 가진다". 필드로 다른 객체를 참조해 표현한다.
- *합성(composition)*: 부품의 수명이 전체에 묶인 강한 HAS-A.
- *통합(aggregation)*: 부품이 따로 존재하는 약한 HAS-A. 원본 §15의 `Police`와 `Gun`.
- 판정 기준: "개념상 종류인가"만으로는 부족하다. **상위 타입의 약속(계약)을 하위 타입이 다 지킬 수 있나**가 기준이다. 정사각형-직사각형·펭귄-새가 개념상 IS-A인데 상속하면 깨지는 예다 → [22-solid](../22-solid/2-summary.md)의 LSP.
- 상속이 비싼 이유(취약한 기반 클래스)와 위임으로 바꾸는 법은 [21-composition-over-inheritance](../21-composition-over-inheritance/2-summary.md).

### 원칙 출처 (주장으로 읽는다)

- GoF 『Design Patterns』(1994) 1장의 두 원칙: "Program to an interface, not an implementation", "Favor object composition over class inheritance". Gamma가 2005년 인터뷰에서 두 원칙을 다시 설명했다(Artima, 아래 근거). 책 본문은 열지 못해 쪽 번호는 [?].
- Martin 『Clean Architecture』 5장 "Object-Oriented Programming"은 절 제목이 "Encapsulation?", "Inheritance?", "Polymorphism?"이다(출판사 목차로 확인). 각 절의 결론은 본문을 열지 못해 [?].

## 쓰이는 자료구조·알고리즘

- **가상 메서드 테이블(vtable)·인터페이스 테이블(itable)**: 동적 디스패치를 빠르게 하는 표. 클래스마다 "메서드 슬롯 번호 → 구현 주소" 배열을 두고, 하위 클래스는 재정의한 슬롯만 바꿔 끼운다.

```text
 Animal vtable            Dog vtable
 [0] toString → Object    [0] toString → Object
 [1] speak    → Animal    [1] speak    → Dog        ← 같은 슬롯 번호, 다른 구현
 호출부: a.speak() = "a의 클래스 vtable[1]로 점프"
```

  - HotSpot(JDK 21) 소스에 `src/hotspot/share/oops/klassVtable.hpp`가 있고, 주석이 "variable-length vtable that is embedded in InstanceKlass"라고 설명한다. 같은 파일에 `klassItable`도 있다. 실제 JIT은 인라인 캐시(`src/hotspot/share/code/compiledIC.*`) 등으로 표 조회를 더 줄인다 — 세부 동작은 이 노트 범위 밖이다.
  - 디스패치 메커니즘 심화는 language/17 `dispatch-and-polymorphism-mechanics` — 미작성([language/README](../../language/README.md)).
- **객체 그래프**: HAS-A 관계가 이루는 방향 그래프. 합성은 대개 트리(부품이 한 주인에게만)다. 통합은 한 부품을 여러 주인이 공유할 수 있고 서로를 참조하는 순환도 생길 수 있어 일반 방향 그래프가 된다. 직렬화·복사·삭제 범위가 이 그래프를 따라간다.
- **클래스 계층 = 트리(자바 클래스) / DAG(인터페이스 다중 구현)**: 자바는 클래스 단일 상속이라 클래스 계층이 트리, 인터페이스까지 넣으면 DAG다.

## 적용 — 풀어나가는 법

1. **불변식을 먼저 문장으로 적는다.** "합계 = 항목 합", "잔액 ≥ 0". 적을 수 없으면 캡슐화할 대상도 아직 모르는 것이다.
2. **setter 대신 의도를 드러내는 행동 메서드를 둔다.** `setStatus(PAID)` 대신 `pay(at)`. 바깥이 상태를 꺼내 판단하지 말고 객체에게 시킨다(Tell, Don't Ask — Fowler 2013 bliki. Fowler는 이 원칙이 Andy Hunt·Dave Thomas와 "most often associated"된다고 적는다).
3. **컬렉션·가변 객체를 돌려줄 때는 사본이나 읽기 전용 뷰로.** 실험 A의 `List.copyOf`. 불변 값 객체는 [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md).
4. **상속은 "약속까지 같은 종류"일 때만.** 재사용만이 목적이면 HAS-A(위임)를 먼저 검토한다([21](../21-composition-over-inheritance/2-summary.md)).
5. **필드·static 메서드로 다형성을 기대하지 않는다.** 실험 B처럼 선언 타입으로 고정된다.

```java
// Tell, Don't Ask — 상태를 꺼내 판단하지 말고 객체에게 시킨다
// Ask (판단이 바깥에 흩어진다)
if (account.getBalance() >= amount) account.setBalance(account.getBalance() - amount);
// Tell (판단이 객체 안 한 곳에)
account.withdraw(amount);   // 안에서 잔액 검사 후 차감, 부족하면 예외
```

진단 — 캡슐화가 새는 곳 찾기:

```bash
# 공개 setter가 많은 클래스 (불변식이 바깥에 맡겨진 후보)
grep -rhoE 'public void set[A-Z]\w*\(' src/main/java | wc -l
grep -rlE 'public void set[A-Z]\w*\(' src/main/java | xargs -I{} sh -c 'echo "$(grep -cE "public void set[A-Z]" {}) {}"' | sort -rn | head
# 내부 컬렉션을 그대로 내주는 getter 후보
grep -rnE 'public (List|Set|Map)<.*> get\w*\(\) *\{ *return \w+; *\}' src/main/java
```

- 숫자는 판정이 아니라 **볼 곳의 목록**이다. DTO·설정 클래스처럼 불변식이 없는 데이터 운반체에는 setter가 문제가 아닐 수 있다.

## 장애 시나리오와 대처

### 1. getter/setter 전부 공개 → 불변식이 바깥에서 깨진다

- 현상: 합계와 항목 합이 다른 주문, 음수 잔액 행이 DB에 있다. 에러 로그는 없다.
- 보이는 형태: 정산 대사(reconciliation) 불일치 리포트, "합계 검증 실패" 배치 알림. 실험 A의 `invariant=false`가 운영에서는 데이터 불일치로 나온다.
- 원인: 상태를 바꾸는 길이 setter·컬렉션 getter로 여러 개 열려 있고, 그중 한 경로가 규칙을 빠뜨렸다.
- 대처: 불변식을 묶는 필드들을 하나의 행동 메서드로만 바꾸게 한다. 컬렉션은 사본으로 내준다. 이미 들어간 불일치 데이터는 별도로 찾아 고친다(코드 수정이 과거 데이터를 고치지 않는다).

### 2. 내부 가변 컬렉션 노출 → 엉뚱한 곳에서 상태가 바뀐다

- 현상: 어떤 서비스도 `setLines`를 부르지 않았는데 주문 항목이 늘었다.
- 보이는 형태: 디버거로 보면 다른 모듈이 `order.getLines().add(...)`나 `removeIf(...)`를 했다. 실험 A의 "리스트 직접 add".
- 원인: getter가 내부 리스트 참조를 그대로 반환했다. `private`은 참조를 숨기지 않는다.
- 대처: `List.copyOf`/`Collections.unmodifiableList`로 반환. 변경은 `addLine`·`removeLine` 같은 메서드로만.

### 3. 필드·static을 재정의했다고 착각 → 하위 클래스 값이 안 쓰인다

- 현상: `Dog`에 `name="dog"`을 선언했는데 로그에 `animal`이 찍힌다. static 팩토리를 하위 클래스에 같은 이름으로 만들었는데 상위 것이 불린다.
- 보이는 형태: 실험 B의 `a.name = animal`, `a.kind() = Animal.kind`.
- 원인: 필드 접근(`getfield`)과 static 호출(`invokestatic`)은 선언 타입으로 컴파일 때 정해진다. 재정의가 아니라 숨김이다.
- 대처: 다형적으로 달라져야 하는 값은 인스턴스 메서드로 노출한다(`String name()`). 같은 이름의 필드·static을 하위 클래스에 다시 선언하지 않는다(IDE·정적 분석 경고 활용).

### 4. 개념상 IS-A라서 상속 → 하위 타입이 상위 약속을 못 지킨다

- 현상: `Penguin extends Bird`의 `fly()`가 `UnsupportedOperationException`을 던진다. `Square extends Rectangle`에서 넓이 계산이 틀린다.
- 보이는 형태: 상위 타입을 받는 코드에서 런타임 예외, 또는 호출부에 `instanceof` 분기가 늘어난다.
- 원인: IS-A를 "개념상 종류"로만 판정했다. 상위 타입의 행동 약속은 검토하지 않았다.
- 대처: 능력별 인터페이스로 나누거나 HAS-A로 바꾼다. 판정·실험은 [22-solid](../22-solid/2-summary.md) LSP, 비용은 [21](../21-composition-over-inheritance/2-summary.md).

### 5. "파이썬 `__`면 숨겨진다"는 오해 → 바깥 대입이 조용히 무시되거나 우회된다

- 현상: `acct.__balance = -3000`을 했는데 `get_balance()`는 여전히 5000이다. 반대로 `acct._Account__balance = -3000`은 그대로 먹힌다.
- 보이는 형태 (실험, Python 3.12.3, `scratchpad/sd/20/e20/hiding.py`):

```text
5000
{'user': 'greg', '_Account__balance': 5000, '__balance': -3000}
-3000
```

- 원인: 클래스 안의 `__balance`는 `_Account__balance`로 이름이 바뀐다(네임 맹글링). 바깥에서 쓴 `__balance`는 **별개의 새 속성**이 된다. 맹글링된 이름으로는 바깥에서도 바꿀 수 있다.
- 대처: 파이썬에서 은닉은 관례(`_`)와 프로퍼티 검사에 기대는 것이고, 강제는 아니다. 불변식은 setter/프로퍼티 검사와 테스트로 지킨다.
- 참고: 원본 §11의 "-3000이 나오는데"는 위 실행 결과와 다르다 — `get_balance()`는 5000을 돌려준다. 원본도 바로 뒤의 `__dict__` 출력에서 `_Account__balance: 5000`을 보이고 있다.

## 핵심 문장

- 캡슐화는 `private` 키워드가 아니라 **상태를 바꾸는 길을 좁히고 그 길에 규칙을 두는 것**이다. getter/setter를 전부 열면 `private`이어도 캡슐화가 없다.
- 다형성은 인스턴스 메서드 호출이 실행 시점의 실제 타입으로 구현을 고르는 것이다(`invokevirtual`·`invokeinterface`). 필드와 static은 선언 타입으로 고정된다.
- 추상 클래스는 공통 골격(상태·일부 구현)을 물려주고, 인터페이스는 역할을 약속한다.
- IS-A의 기준은 개념이 아니라 **상위 타입의 약속을 다 지킬 수 있는가**다. 재사용만 원하면 HAS-A부터 검토한다.

## 관련 주제·근거

- 선행
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 정보 은닉·결합도
- 원본
  - [foundations/oop-basics](../../foundations/oop-basics/README.md) — 파이썬으로 본 클래스·메서드·네임 맹글링(§11)·프로퍼티(§12)·IS-A(§14)·HAS-A(§15)·다형성(§16)·`abc`(§17)·Character 계층(§18)
- 후속·연결
  - [21-composition-over-inheritance](../21-composition-over-inheritance/2-summary.md) — 상속의 비용, 취약한 기반 클래스
  - [22-solid](../22-solid/2-summary.md) — LSP(IS-A의 행동 기준), DIP(다형성으로 의존 방향 뒤집기)
  - [23-design-by-contract](../23-design-by-contract/2-summary.md) — 불변식을 계약으로 명시
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) — 불변 객체로 공유 문제 없애기
  - language/17 `dispatch-and-polymorphism-mechanics`(vtable·인라인 캐시) — 미작성([language/README](../../language/README.md))
  - [domain-modeling/04-entities-and-value-objects](../../domain-modeling/04-entities-and-value-objects/2-summary.md)·[domain-modeling/05-aggregates-and-invariants](../../domain-modeling/05-aggregates-and-invariants/2-summary.md)
- 글·문서
  - GoF 1장 두 원칙 — Erich Gamma 인터뷰, Bill Venners, "Design Principles from Design Patterns", Artima, 2005-06-06 <https://www.artima.com/articles/design-principles-from-design-patterns>
  - Robert C. Martin, 『Clean Architecture』(2017) 5장 "Object-Oriented Programming" — 절 제목만 출판사 목차로 확인 <https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166>
  - D. L. Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules", CACM 15(12):1053–1058, 1972. doi:10.1145/361598.361623
  - Martin Fowler, "TellDontAsk", 2013-09-05 <https://martinfowler.com/bliki/TellDontAsk.html>
  - JVMS SE 21 §6.5 `invokevirtual`·`invokeinterface`·`invokestatic`·`getfield` <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html>
  - HotSpot 소스 `src/hotspot/share/oops/klassVtable.hpp`(openjdk/jdk21u) <https://github.com/openjdk/jdk21u/blob/master/src/hotspot/share/oops/klassVtable.hpp>
  - Joshua Bloch, 『Effective Java』 3판(2018) 4장 Item 19 — 저자 예제 저장소 `chapter4/item19` <https://github.com/jbloch/effective-java-3e-source-code>
  - Bertrand Meyer, 『Object-Oriented Software Construction』 — 커리큘럼 지정 교재, 본문 미열람 [?]
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`, Python 3.12.3 호스트, 2026-10-02)
  - A `scratchpad/sd/20/e20/Encap.java` — getter/setter 공개 vs 행동 메서드, 불변식 유지 여부
  - B `scratchpad/sd/20/e20/Dispatch.java` + `javap -c` — 메서드·필드·static의 디스패치 차이
  - C `scratchpad/sd/20/e20/AbstractNew.java` — 추상 클래스 인스턴스화 컴파일 오류
  - D `scratchpad/sd/20/e20/hiding.py` — 원본 §11 네임 맹글링 재현
  - E `python3 -c` 한 줄 — `abc` 추상 클래스 인스턴스화 시 `TypeError`
