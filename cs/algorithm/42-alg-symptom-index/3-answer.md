# algorithm/42-alg-symptom-index — 정답

## 정답

### 1. 증상과 깨진 가정

| 증상 | 깨진 가정 |
|---|---|
| 데이터 늘자 타임아웃 | "n이 작다", "입력이 평균적이다"(최악 입력이 오지 않는다) |
| 정렬 계약 예외 | "비교자가 전순서다"(반대칭·추이·일관성) |
| 재귀 스택 오버플로 | "재귀 깊이가 작다"(log n 수준) |
| 정규식 CPU 100% | "매칭 시간은 입력 길이에 선형이다" |
| 이진 탐색 무한 루프 | "구간이 매번 준다" (음수 인덱스는 "`int`가 안 넘친다") |

- 첫 질문이 입력인 이유: 알고리즘 증상의 대부분은 입력이 가정을 벗어날 때 보인다. 크기(n), 모양(정렬됨·전부 같음·긴 공백), 값의 범위(`int` 경계), 계약을 알아야 위 표의 어느 행인지 고를 수 있다.

### 2. 두 배 실험

- 4만 → 8만(두 번 실행): 이중 루프 x4.0·x4.1, `HashSet` x1.8·x1.9, 정렬 후 비교 x1.7·x2.0.
- 가를 수 있는 것: 제곱 이상(약 4배)과 그 아래(약 2배). 이중 루프의 O(n²)이 큰 n에서 분명히 보였다.
- 가를 수 없는 것: O(n)과 O(n log n). 두 배당 log 차이는 1.07배 정도라 측정 잡음(1.7~2.5배로 흔들림)에 묻힌다. 작은 n의 비율도 흔들렸다(이중 루프 1만 → 2만이 x2.7·x3.8). 큰 n, 여러 번, 최솟값으로 본다.

### 3. 타임아웃의 세 갈래

- 차수 문제
  - 관찰: 무작위 입력으로도 n 두 배에 약 4배.
  - 처방: 해시·정렬 기반으로 바꾼다 — [asymptotic-analysis 1](../02-asymptotic-analysis/2-summary.md), [algorithm-basics 1](../01-algorithm-basics/2-summary.md).
- 최악 입력
  - 관찰: 같은 n에서 무작위 입력은 빠르고 특정 입력(정렬된 파일, 같은 값만, 긴 공백)만 느리다.
  - 처방: 무작위 피벗·표준 정렬·입력 상한·패턴 재작성 — [quick-sort 1·2](../03-quick-sort/2-summary.md), [randomized-algorithms 2](../39-randomized-algorithms/2-summary.md), [43-alg-incidents](../43-alg-incidents/2-summary.md).
- 종료 조건 결함
  - 관찰: 그 요청만 끝나지 않고 덤프 여러 장이 같은 줄이다(느림은 프레임이 진행한다).
  - 처방: 불변식 수정, 반복 상한 — [binary-search 2](../06-binary-search/2-summary.md).

### 4. 테스트에서 안 보인 계약 위반

- OpenJDK의 TimSort는 `MIN_MERGE = 32`다. 길이 32 미만은 병합 없이 이진 삽입 정렬로 끝나고, 계약 위반 예외는 병합 단계(`mergeLo`·`mergeHi`)에서 발견될 때 난다.
- 실험([sorting-in-practice](../09-sorting-in-practice/2-summary.md)): 같은 위반 비교자로 n=31은 200회 중 예외 0회, n=32는 4회. 단위 테스트의 작은 리스트로는 원리적으로 안 잡힌다.
- `useLegacyMergeSort`: 옛 병합 정렬로 바뀌어 예외가 사라진다(실험: 세 비교자 모두 20회 중 예외 0회). 그러나 비교자 위반은 그대로라 정렬 결과를 믿을 수 없다. 같은 뺄셈 비교자를 기본 TimSort로 돌린 실험에서도 예외가 안 난 17회(20회 중)는 모두 틀린 순서였다 — 예외가 없다는 것이 순서가 맞다는 뜻이 아니다. 옛 병합 정렬에서 순서를 따로 검사한 실험은 leaf에 없다.

### 5. 스택 오버플로의 갈래와 `-Xss`

- 갈래
  - 기저 누락·축소 실패: 특정 입력이면 크기와 무관하게(음수 인자, `mid == hi`) — [recursion 1](../03-recursion/2-summary.md).
  - 깊이 ∝ n: 긴 리스트·직선 그래프·치우친 트리, 재귀 DFS — [recursion 2](../03-recursion/2-summary.md), [dfs 1](../12-dfs/2-summary.md).
  - 고정 피벗 + 정렬된 입력의 재귀 퀵 정렬 — [quick-sort 1](../03-quick-sort/2-summary.md).
  - 외부 입력의 중첩 깊이(재귀 하강 파서) — [recursion 3](../03-recursion/2-summary.md).
  - 꼬리 재귀를 믿음(HotSpot·V8은 제거하지 않음) — [recursion 5](../03-recursion/2-summary.md).
- `-Xss`가 처방이 아닌 이유
  - 같은 `-Xss1m`에서도 깊이 한계가 실행마다 19,415~41,224로 달랐다(JIT 영향). 숫자를 믿고 설계할 수 없다.
  - 깊이가 n에 비례하면 스택을 키워도 n이 따라 큰다. 1,000,000 깊이에 `-Xss64m`도 부족했다.
  - 처방은 깊이를 입력에서 떼어 놓는 것(명시적 스택, 작은 쪽만 재귀, 타뷸레이션, 파서 깊이 상한)이다.

### 6. 정규식 세 모양

- `(a+)+$` + 끝이 안 맞는 입력: 백트래킹 엔진에서 한 글자 늘 때마다 시간이 약 두 배 — 지수([backtracking 1](../13-backtracking/2-summary.md)). JDK 21은 이 모양만 내부 메모이제이션으로 막아 평평했고, `(a+)+$|(b)\2`처럼 역참조를 섞으면 지수였다([language/02](../../language/02-lexing-and-regular-languages/2-summary.md) 실험).
- `\s+$` + 공백 n개 뒤 다른 문자: 두 배에 약 4배 — O(n²). 실험: 2만 개 약 4초 → 4만 개 약 15초([43-alg-incidents](../43-alg-incidents/2-summary.md) 실험 E).
- `.*.*=.*` + `=` 없는 입력: 두 배에 약 7~8배 — O(n³) 쪽(해석). 실험: 1,000자 약 2.5초 → 2,000자 약 19초([engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 B, `--cpus=1`).
- 테스트가 통과시키는 이유: 위 입력은 모두 매칭 실패(`false`)로 결과가 정상이다. 정상·공격 요청 모음으로 "맞게 막고 맞게 통과시키나"만 보면 시간 결함은 보이지 않는다. 적대적 입력에서 **시간 예산**을 재야 한다.

### 7. 같은 줄에 멈춘 이진 탐색

- 원인
  - 닫힌 판(`while (lo <= hi)`)에 반열린 판의 `hi = mid`를 섞음: `lo == hi == mid`일 때 `hi = mid`가 아무것도 안 바꿔 제자리다.
  - `lo = mid`: 구간이 2칸일 때 `mid = lo`라 `lo`가 안 움직인다.
  - 처방: 판 하나로 고정하고, "mid가 아직 답 후보인가"로 `hi = mid`(남김)와 `mid - 1`(버림)을 정한다([binary-search 2](../06-binary-search/2-summary.md)).
- 같은 모양의 다른 사례
  - 펜윅 트리 `add`에 0 인덱스: `0 & -0 == 0`이라 `x`가 안 움직이고 `0 <= n`이 계속 참([data-structure/17-fenwick-tree](../../data-structure/17-fenwick-tree/2-summary.md) 장애 1).
  - 부분집합 순회: `(0 - 1) & mask == mask`로 처음으로 돌아감([bit-manipulation 2](../29-bit-manipulation/2-summary.md)).

### 8. 공통점과 테스트 짝

- 공통점: 왼쪽 열(타임아웃 상향, `useLegacyMergeSort`, `-Xss`, 서버 증설, 재시작)은 모두 **가정 위반을 그대로 두고 증상만 끄거나 미룬다**.
- 적용 3의 테스트
  - `assertSubQuadratic`(두 배 비율): 데이터 늘자 타임아웃(1절), 정규식처럼 입력 길이에 다항으로 느는 경로(4절)에도 쓸 수 있다.
  - `lowerBound`의 반복 상한 + `>>> 1`: 이진 탐색 무한 루프와 중간값 오버플로(5절).
  - `assertSorted`: 예외 없이 틀린 정렬 순서(2절).
