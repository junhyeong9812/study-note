# algorithm/09-sorting-in-practice — 정답

## 정답

### 1. 안정성

- 비교 결과가 0인 원소들의 입력 순서를 결과에서도 유지하는 정렬이다.
- `int` 두 개가 같으면 구별할 수 없어 순서가 바뀌어도 결과가 같다. 실무에서 의미가 있는 것은 키 외의 필드가 있는 객체다(드문 예외: 비트 패턴이 다른 `double` NaN).
- 다중 키는 **2차 키(날짜)로 먼저**, 1차 키(도시)로 나중에 안정 정렬한다. 실험에서 `s.sort(byDay); s.sort(byCity);`가 `comparing(city).thenComparing(day)`와 같은 순서였다(`true`). 불안정한 힙 정렬 두 번은 `false`.

### 2. 계약 세 조건과 위반

- ① `sgn(compare(x, y)) == -sgn(compare(y, x))` ② `compare(x, y) > 0 && compare(y, z) > 0 ⇒ compare(x, z) > 0` ③ `compare(x, y) == 0 ⇒ sgn(compare(x, z)) == sgn(compare(y, z))`.
- `x - y`: `int` 오버플로로 "아주 작은 수 − 양수"가 양수가 된다. 큰 수·작은 수 사이 판정이 뒤집혀 ②(추이)가 깨진다.
- `x < y ? -1 : 1`: `compare(x, x) = 1`이고 같은 값 x, y에서 `compare(x, y) = compare(y, x) = 1`이라 ①이 깨진다.

### 3. OpenJDK 21의 정렬 배치

| 호출 | 알고리즘 | 안정 |
|---|---|---|
| `Arrays.sort(int[])` | DualPivotQuicksort | 원시값이라 해당 없음 |
| `Arrays.sort(Object[])` | ComparableTimSort | 예 |
| `list.sort(cmp)` | `Arrays.sort(배열, cmp)` → TimSort (ArrayList는 내부 배열 직접) | 예 |

- 근거: `Arrays.java`·`ArrayList.java`·`List.java` 소스.

### 4. TimSort 그림

```text
  [오름 run][내림 run → 뒤집기][짧은 run → 이진 삽입으로 minRun까지]
  run 스택: 새 run을 push → 위쪽 길이가 불변식을 깨면 이웃끼리 병합
  병합 중 한쪽이 minGallop번(처음 MIN_GALLOP = 7, 병합 중 조정) 연속 이기면 지수 탐색으로 덩어리 이동
```

- 32개 미만 배열은 병합 없이 이진 삽입 정렬로 끝낸다(`MIN_MERGE = 32`).
- 이웃끼리만 병합해야 같은 키가 다른 run을 건너뛰지 않아 안정성이 유지된다.

### 5. 비교 횟수 (실험, n=1,000,000)

- 정렬된 입력 999,999, 엄격한 역순 999,999(run 하나로 보고 뒤집음), 두 덩어리 1,999,998, 무작위 18,640,462(n log₂ n = 19,931,568보다 약간 적음).
- 거의 정렬(무작위 교환 100번)도 1,013,397이었다.

### 6. 크기에 따른 예외

- 실험(각 200회): n=31 → 예외 0회, n=32 → 4회, n=64 → 81회, n=2000 → 200회.
- 31개 이하는 병합 단계가 없어서 TimSort가 위반을 만날 기회가 없다. 크기가 클수록 병합에서 불가능한 상태를 만날 확률이 오른다.
- `useLegacyMergeSort`를 주면 예외가 0회가 된다(옛 병합 정렬은 검사하지 않음). 그러나 비교자가 틀린 것은 그대로다. 기본 TimSort에서 뺄셈 비교자 실험(n=2000, 20회)을 하면 3회는 예외가 났고, 예외가 나지 않은 17회는 모두 순서가 틀렸다(legacy 결과의 순서는 따로 검사하지 않았다).

### 7. 페이지 겹침

- `created_at` 동점이 많은데 동점 해소 키가 없다. DB는 동점 행의 순서를 보장하지 않고, PostgreSQL 문서도 `LIMIT`/`OFFSET` 값마다 다른 계획·다른 행 순서가 나올 수 있다고 적는다(7.6).
- 시뮬레이션(질의마다 셔플 + 불안정 정렬)에서 10페이지 동안 중복 55건·누락 55건, `ORDER BY day, id`는 0건.
- 대처: `ORDER BY created_at, id`, 가능하면 키셋 페이지네이션(오름차순이면 `WHERE (created_at, id) > (?, ?)`, 내림차순 `ORDER BY created_at DESC, id DESC`이면 `<`).

### 8. `TreeSet` 소실

- `TreeSet`은 `compare == 0`이면 같은 원소로 보고 추가하지 않는다. 이름만 비교하면 같은 이름의 다른 사용자가 버려진다.
- 실험: 이름만 → 2명, 이름 + id → 3명.

### 9. 비교자

```java
Comparator<Order> cmp = Comparator
        .comparing(Order::city, Comparator.nullsLast(Comparator.naturalOrder()))
        .thenComparing(Order::day, Comparator.reverseOrder())
        .thenComparingLong(Order::id);
```

- 유일 키 id를 마지막에 붙이면 어떤 두 원소도 0이 아니게 되어 순서가 결정적이다. 동점 순서가 흔들려 생기는 페이지네이션 중복과 `TreeSet` 소실을 함께 막는다. 단 `OFFSET` 질의 사이에 앞쪽에 행이 삽입되면 순서가 유일해도 이전 페이지 행이 다시 나올 수 있다(키셋 페이지네이션이나 같은 스냅숏으로 피한다).

### 10. TimSort 정형 검증 버그

- `mergeCollapse`가 run 스택 불변식을 위 3개만 검사해 깊은 곳의 불변식이 깨질 수 있었다. 길이 67,108,864 배열에서 스택 배열이 모자라 `ArrayIndexOutOfBoundsException`이 나는 입력이 만들어졌다(de Gouw 외 CAV 2015).
- OpenJDK는 처음에 run 스택 배열 길이만 늘렸고(JDK-8072909, JDK 9), JDK-8203864(JDK 11)에서 `mergeCollapse`를 고쳤다. OpenJDK 21 소스는 위 4개까지 검사한다.
- 차이: 이 버그는 **비교자가 올바른데도** 라이브러리가 죽는 문제였다. `Comparison method violates…`는 **비교자가 틀렸다**는 신호다.
