# software-design/21-composition-over-inheritance — 정답

## 정답

### 1. 상속이 묶는 것

- 공개 API만이 아니라 부모의 **내부 구현 방식**, 특히 자기 호출(부모 메서드가 자기 다른 메서드를 부르는지)에 묶인다. 부모 안의 `this.add(e)`는 동적 디스패치로 자식 재정의에 간다.
- GoF 1장: 상속 = white-box 재사용(부모 내부가 자식에게 보임), 합성 = black-box 재사용(내부가 안 보임) — 책 본문 미열람, Wikipedia 요약으로 확인. Gamma는 2005 인터뷰에서 상속을 "brittle"하다고 했고, 합성을 "black box reuse"라고 불렀다.

### 2. 이중 집계

(실험 A, JDK 21.0.12)

```text
$ java InstrumentedHashSet     # 상속
6
$ java InstrumentedSet         # 합성
3
```

- 상속판: 자식 `addAll`이 3을 더하고 `super.addAll` → `AbstractCollection.addAll`이 원소마다 `add(e)`를 부른다 → 자식 `add`가 또 1씩 더해 6. `HashSet`은 `addAll`을 재정의하지 않는다(JDK 21 소스).
- 합성판: `ForwardingSet.addAll`이 내부 `Set`의 `addAll`을 부르고, 그 안의 `add`는 내부 `HashSet`의 것이라 래퍼의 `add`가 다시 불리지 않는다.

### 3. 기반 클래스만 리팩터링

```text
 Inventory.java | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
상속 count=7 size=4  FAIL (기대 4)
합성 count=4 size=4  PASS
```

- 1파일만 바뀌었고 자식 코드는 그대로인데 상속판이 7(기대 4)이 됐다. 예외 없이 숫자만 틀린다 — 취약한 기반 클래스 문제.

### 4. 부모의 새 메서드

- 상속판: 자식 API에 자동으로 생기고, 그 경로는 자식의 집계를 우회한다 → `count=0 size=2`.
- 합성판: 감싼 쪽이 열지 않았으므로 `error: cannot find symbol` 컴파일 오류. 쓰려면 전달 메서드를 직접 추가한다(실험에서 +3줄). 그 자리에서 셀 방법을 정한다 → `count=2 size=2`.

### 5. 합성이 손해인 경우

- 부품이 자기 자신(`this`)을 바깥(콜백 레지스트리)에 등록하는 구조. 이후 호출은 래퍼를 거치지 않는다(SELF 문제).

```text
합성(래퍼) count=0   ← 버스에 등록된 것은 inner(this), 래퍼를 거치지 않는다
상속       count=2
```

- Kotlin 문서도 `by` 위임에서 "members overridden in this way do not get called from the members of the delegate object"라고 적는다.
- 그 밖의 비용: 전달 코드(Bloch `ForwardingSet` 30줄).

### 6. 생성자에서 재정의 메서드 호출

```text
null
2026-10-02T01:54:29.780101110Z
```

- 첫 줄은 부모 생성자 안에서 불린 것 — 자식 `instant` 필드가 아직 초기화 전이라 `null`. 둘째 줄은 생성 뒤 호출. 시각은 실행마다 다르다.

### 7. 상속 허용 조건과 막는 법

- 조건: ① 상위 타입의 약속을 다 지키는 진짜 IS-A(LSP) ② 부모를 우리가 통제(같은 모듈·팀) ③ 부모가 상속용으로 설계·문서화(`@implSpec`로 자기 호출 명시). 그리고 생성자에서 재정의 가능 메서드를 부르지 않는다.
- 막기: 자바 `final` 클래스, 허용 하위 타입을 정하려면 `sealed`(JDK 17, JEP 409). Kotlin은 클래스·멤버가 기본 `final`이고 `open`을 붙여야 상속·재정의된다.

### 8. 기반 클래스 PR 뒤 지표 2배

- 가설: 기반 클래스가 내부 자기 호출 방식을 바꿨고(예: `addAll`이 `add`를 부르게), 두 메서드를 모두 재정의해 세던 하위 클래스들이 이중 집계한다(실험 B 패턴).
- 확인: PR diff에서 기반 클래스 메서드 간 호출 변화, IDE Type Hierarchy로 하위 클래스 목록과 재정의 메서드 확인, 하위 클래스 테스트 실행.
- 대처: 즉시 되돌리기. 근본은 하위 클래스를 합성으로 바꾸거나, 기반 클래스의 자기 호출을 문서화된 계약으로 고정한다. 이미 쌓인 잘못된 지표·데이터는 별도 보정.
