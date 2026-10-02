# software-design/51-legacy-change-techniques — 정답

## 정답

### 1. 정의와 순환

- WELC 머리말: "legacy code is simply code without tests" — 테스트가 없는 코드.
- 순환: 안전하게 바꾸려면 테스트가 필요하다 → 테스트를 붙이려면 DB·전역·시계 같은 의존을 끊어야 한다 → 의존을 끊는 것도 코드 변경이다.
- 그래서 처음의 의존 끊기는 테스트 없이 하는, 작고 기계적인 변경으로 한다(WELC 머리말: Part III 기법은 "테스트를 붙이기 위해 테스트 없이" 하도록 만든 것).

### 2. 알고리즘

```text
 ① 변경점 찾기 → ② 테스트 지점 찾기 → ③ 의존 끊기 → ④ 테스트 작성 → ⑤ 변경·리팩터링
```

- 변경점은 코드가 바뀌는 곳이고, 테스트 지점은 그 효과를 관찰할 수 있는 곳이다. 변경점이 깊은 private 메서드 안에 있으면 효과는 그것을 부르는 공개 메서드의 반환값·부수 효과로 보인다. 그래서 효과가 퍼지는 길(호출 그래프)을 따라가 테스트 지점을 고른다(WELC 11장).
- 새 코드를 쓰는 것은 마지막이다.

### 3. seam·enabling point

- seam: 그 자리를 편집하지 않고 동작을 바꿀 수 있는 곳.
- enabling point: 어느 동작을 쓸지 결정하는 곳.
- 메서드 안에서 `new FormulaCell(...)` 후 `cell.Recalculate()`: seam이 아니다. 클래스가 생성 시점에 메서드 안에서 정해져, 메서드를 고치지 않고는 바꿀 수 없다(enabling point 없음 — WELC 4장).
- `buildMartSheet(Cell cell)`처럼 인자로 받으면 seam이 된다. enabling point는 인자 목록이다. 테스트가 원하는 `Cell`을 넘긴다.

### 4. sprout vs wrap

- sprout method: 새 로직을 한 지점에 넣으면 될 때. 새 메서드로 쓰고 테스트한 뒤 기존 메서드에서 한 줄로 부른다.
- wrap method: 새 동작이 기존 동작 앞이나 뒤에 매번 붙어야 할 때(예: 결제마다 로그). 기존 메서드 이름을 바꾸고 원래 이름의 새 메서드가 [새 동작 + 원 메서드]를 부른다.
- sprout method의 한계: 원 메서드는 여전히 테스트 밖이다. 새 로직만 보호한다. 원 클래스를 하네스에 못 올리면 sprout class로 간다.

### 5. 숨은 의존과 object seam

(실험 B, JDK 21.0.12, 2026-10-02)

```text
== 레거시 메서드를 그대로 테스트
  FAIL postEntries 중복 제거 — IllegalStateException: 운영 DB에 연결할 수 없음(테스트 환경)
== 객체 seam(서브클래스로 DB 교체)
  PASS postEntries 저장 내용 감지(sensing)
```

- 그대로: 실행 자체가 실패한다(DB 연결 예외).
- `openDatabase()` 오버라이드: 테스트 서브클래스가 가짜 DB를 돌려주고, 저장된 내용 `[X, Y]`를 기록해 확인했다. 이것이 Extract and Override Factory Method이고, enabling point는 "테스트가 만드는 서브클래스 객체"다.

### 6. 빅뱅 vs parallel change

(실험 C, 같은 환경)

```text
  [A1: 시그니처 변경만]
  컴파일 실패: 오류 40건 (파일 40개)
  A1+A2 합계:  41 files changed, 41 insertions(+), 41 deletions(-)
  B 커밋별 변경 파일 수: 1 10 10 10 10 1 
```

- 시그니처만 바꾸면 호출처 수만큼 40건.
- parallel change: expand 1 → migrate 10·10·10·10 → contract 1. 점검한 지점(B1, B2-1, B2-3, B3 직후)마다 컴파일 OK.
- 총 변경량은 비슷하다. 다른 것은 "중간 상태가 빌드되는가"다.

### 7. 충돌 없는 병합, 깨진 빌드

(실험 D)

```text
== D-bigbang: feature 병합
  git merge: 충돌 없음
  컴파일 실패: 오류 1건 (파일 1개)
== D-expand: feature 병합
  git merge: 충돌 없음
  컴파일 OK
```

- 다른 브랜치가 옛 시그니처로 새 호출처(`Caller41`)를 추가했다. 줄 단위로는 겹치지 않아 git은 충돌을 못 봤지만, 의미상 존재하지 않는 메서드를 부른다(`long cannot be converted to Money`).
- expand 상태에서는 옛 메서드가 살아 있어(새 메서드에 위임) 병합 후에도 빌드된다. 늦게 온 호출처는 migrate 목록에 추가하면 된다.

### 8. 새 테스트는 통과, 운영 값은 다름

- 건너뛴 단계: ④ 현재 동작을 고정하는 테스트(특성 테스트). 새 테스트의 기대값을 새 코드의 출력이나 사양서로 적었다.
- 숨은 동작(반올림·정렬·공백 처리)은 현재 출력을 그대로 기대값으로 적을 때만 잡힌다. 시스템 단위라면 병행 실행으로 구·신을 비교한다(50 실험 A에서 반올림 차이 1.29%).

### 9. contract 시점

- migrate가 끝나 옛 버전 호출이 0일 때.
- 같은 빌드: 컴파일러가 확인해 준다. 옛 메서드를 지워 보면 남은 호출처가 오류로 나온다(실험 C의 C: 20건). `@Deprecated(forRemoval = true)` + `javac -Werror`로 미리 막을 수도 있다(`[removal]` 경고는 JDK 21에서 기본으로 켜져 있다. 일반 `@Deprecated`는 `-Xlint:deprecation`도 함께 줘야 한다).
- 다른 배포 단위(다른 서비스·JAR·외부 클라이언트): 컴파일러가 못 본다. 지우면 런타임 `NoSuchMethodError`·404가 된다. 호출 로그·지표로 0을 확인한 뒤 지운다.

### 10. 의존 끊기와 DI·branch by abstraction

- Parameterize Constructor: 안에서 `new` 하던 의존을 생성자 인자로 받는다. 이것이 생성자 주입이고, 조립을 바깥(Composition Root)으로 미는 25의 첫걸음이다. 옛 생성자를 남겨 위임하면 그 자체가 작은 expand다.
- Extract Interface: 의존 클래스 앞에 인터페이스를 둔다. 테스트에서는 가짜를, 운영에서는 실물을 넣는다. 같은 인터페이스 뒤에 새 구현을 넣어 호출자를 하나씩 옮기면 그것이 branch by abstraction(50)이다.
