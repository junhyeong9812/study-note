# software-design/13-refactoring — 정답

## 정답

### 1. 정의

- 리팩터링(명사): 관찰 가능한 동작을 바꾸지 않으면서, 이해하기 쉽고 고치기 싸도록 소프트웨어 내부 구조를 바꾸는 것(Fowler "DefinitionOfRefactoring").
- 버그 수정은 관찰 가능한 동작을 바꾸므로 리팩터링이 아니다. 구조 변경과 동작 변경을 섞은 것이다. 나눠서 커밋한다([14-tidy-first](../14-tidy-first/2-summary.md)).

### 2. 작은 단계 루프

```text
 [작은 변환 1개] → 컴파일 → 테스트 ─ 초록 → 커밋 → 다음 변환
                              └ 빨강 → 바로 못 고치면 마지막 초록 커밋으로 되돌리고 더 작게 다시
```

- Fowler 1장: 리팩터링이 하나 성공할 때마다 로컬에 커밋하고, push 전에 의미 있는 커밋으로 squash한다. 실패하면 마지막 good 커밋으로 되돌리고 더 작은 단계로 다시 한다. "small steps are the key to moving quickly".

### 3. 두 테스트

- 자기 검증 테스트: 실행하면 기대값과 자동 비교해 초록/빨강을 낸다. 사람이 값을 눈으로 대조하지 않는다(Fowler 1장 「The First Step in Refactoring」).
- 특성 테스트(골든 마스터): 리팩터링 전 실제 출력을 기록하고 후의 출력과 비교한다. 맞는 동작인지가 아니라 바뀌었는지를 본다.
- 행복 경로 하나는 입력 공간의 한 점이다. 동작 변경이 다른 입력에서만 드러나면 못 잡는다(4번).

### 4. 반올림 위치

(실험 A, JDK 21.0.12 temurin, 2026-10-02)

```text
4 Consolidate tax rounding: HAPPY PASS / GOLDEN FAIL: 300건 중 72건 다름
```

- 행복 경로: 초록. 골든: 300건 중 72건이 다름(예: 합계 204,770 → 204,769).
- 행복 경로는 한 줄짜리 장바구니다. 줄이 하나면 "줄마다 반올림의 합"과 "합의 반올림"이 같다. Σ round(xᵢ)와 round(Σ xᵢ)의 차이는 줄이 여러 개일 때만 생길 수 있다(여러 줄이어도 같을 때가 많다 — 실험의 1~4줄 장바구니 300건 중 달라진 것은 72건).

### 5. bisect와 범인 크기

```text
f65e2dea38e51641666b6ac6481e1322443614a1 is the first bad commit
    4 Consolidate tax rounding
--- 작은 단계 4번:
 1 file changed, 2 insertions(+), 1 deletion(-)
--- 큰 한 방:
 1 file changed, 18 insertions(+), 8 deletions(-)
```

- 4단계 "Consolidate tax rounding"을 짚었다. 범인 커밋은 작은 단계에서 3줄(+2/−1), 큰 한 방에서는 26줄(+18/−8) 전체가 후보다.

### 6. 큰 리팩터링 브랜치 머지

```text
CONFLICT (content): Merge conflict in CartService.java
CONFLICT (content): Merge conflict in InvoiceService.java
CONFLICT (content): Merge conflict in OrderService.java
충돌 파일 수: 3
  BulkService.java:2: error: cannot find symbol
```

- 텍스트 충돌 3파일(기능이 고친 줄과 리팩터링이 고친 줄이 겹침).
- 충돌이 없던 `BulkService.java`는 기능 브랜치가 새로 만든 파일로, 옛 이름 `calcPrice`를 불러 컴파일 오류가 났다. 텍스트 머지는 성공해도 의미가 충돌했다.

### 7. 오래 사는 브랜치 없이

- expand(새 이름 추가, 옛 이름은 위임으로 유지) → migrate(호출처를 작은 PR 여러 개로 옮김) → contract(옛 이름 삭제).
- 실험 B 대안의 첫 커밋: `Price.java` 1파일(+3/−1)에 `priceOf`를 더하고 `calcPrice`를 `@Deprecated` 위임으로 남겼다. 이것을 먼저 합친 뒤 기능 브랜치를 머지하니 충돌 0, `javac exit=0`.
- 단, 이 충돌 0은 expand 커밋이 호출처를 건드리지 않아서다. migrate 커밋을 기능 머지 전 기준에서 만들어 두면 Order·Cart·Invoice에서 각각 충돌 1구간이 났다. 최신 main에서 파일 하나씩 옮겨 바로 합치면 7파일 모두 충돌 0, contract 뒤에도 `javac exit=0`이었다.

### 8. AST와 3-way 머지

- IDE 자동 Rename은 구문 트리(AST)와 심볼 테이블(이름 해석)로 "이 식별자가 어느 선언을 가리키나"를 안다. 같은 철자의 다른 변수·문자열·주석을 건드리지 않는다. `sed`는 글자만 본다.
- 3-way 머지는 공통 조상 대비 줄 단위로 겹침을 본다. 다른 파일의 새 줄이 옛 이름을 쓰는 것은 줄이 겹치지 않으므로 충돌로 보이지 않는다. 컴파일·테스트가 잡아야 한다.

### 9. 1원 불일치

- 원인 후보: 반올림 위치·순서를 옮긴 "같아 보이는" 변환. 동작 변경이 리팩터링으로 들어갔다.
- 찾는 법: 단계별 커밋이 있으면 넓은 입력의 골든 테스트를 `check.sh`로 만들어 `git bisect run`을 돌린다. 범인 단계의 diff만 본다.
- 예방: 리팩터링 전 골든 마스터를 만든다. 입력에 여러 줄·경계값을 섞는다. 단계마다 테스트·커밋한다. 반올림·평가 순서·부수효과 횟수를 바꾸는 변환은 리팩터링이 아니라고 의심한다.
