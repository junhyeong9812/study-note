# math/17-math-incidents — 정답

## 정답

### 1. 키 길이와 키 공간

- 결정적 생성기가 만드는 키의 개수는 시드 개수를 넘지 못한다. Debian 패치 뒤 OpenSSL은 PID만으로 시드됐으므로(Debian 위키 "seeded only by process ID"), 키가 2048비트여도 공간은 (아키텍처·키 종류·길이, 그리고 `~/.rnd` 파일 유무 같은 입력 상태를 고정하면) PID 개수 이하였다. 같은 PID라도 `~/.rnd` 유무에 따라 다른 키가 나왔다는 당시 보고가 있다(debian-security 2008-05).
- 32,767: 아키텍처 하나에서 가능한 난수 흐름 수. PID 0(커널)을 빼고 PID_MAX 32768에는 닿지 않으므로 2^15 − 1.
- 98,301: 출력이 다른 아키텍처 세 종류(리틀 엔디언 32비트·64비트, 빅 엔디언 32비트)를 합친 (2^15 − 1) × 3.

### 2. 서버 간 키 충돌

- 실험 B(200회 평균): 1,000대 15.5쌍(이론 15.2), 10,000대 1525.9쌍(이론 1525.8).
- 이론 식: 같은 키 쌍의 기대 수 = C(k, 2) / N, N = 32,767. 전제는 PID가 1~32,767에서 **균등·독립**으로 뽑힌다는 것이다.
- 실제 PID는 부팅 직후 작은 값에 몰리는 등 균등하지 않을 수 있다. 그러면 충돌은 이 식보다 잦아진다고 볼 수 있다(노트의 해석).

### 3. 15비트의 생일 한계

- 50% 지점 ≈ √(2 ln 2 · N) = √(2 ln 2 · 32,767) ≈ 213개.
- 32비트 공간은 약 77,163개에서 50%다([05](../05-counting-and-birthday-bound/2-summary.md)). 15비트로 줄자 서버 수백 대 규모에서 이미 충돌이 흔하다.

### 4. Java 7의 정렬 예외

- 호환성 노트: "The new sort implementation may throw an IllegalArgumentException if it detects a Comparable that violates the Comparable contract. The previous implementation silently ignored such a situation." 비교자는 원래 틀렸고, 바뀐 것은 위반을 드러내는 구현(TimSort, RFE 6804124)이다.
- JDK 자신의 코드: Swing의 `SortingFocusTraversalPolicy`(JDK-7075600의 스택, 2011-08-05 등록).
- 원인(JDK-8048887): "uses ROW_TOLERANCE conception ... This however breaks the transitivity rule" — 행 허용 오차가 추이성을 깼다.

### 5. 세 점의 순환

- a·b: |16 − 8| = 8 ≤ 10 → x 비교 → a < b(−1). b·c: 8 ≤ 10 → x 비교 → b < c(−1). a·c: 16 > 10 → y 비교 → a > c(1). 출력 `a<b? -1  b<c? -1  a<c? 1`.
- a < b < c인데 a > c이므로 **추이성** 위반이다(순환).
- 기본 TimSort: n = 31·32·100·1000 각 200회에서 예외 0·1·1·0회(800회 중 2회), 나머지 실행 결과는 모두 비교자 기준으로 뒤집힌 쌍이 있었다.
- `useLegacyMergeSort=true`: 예외 0회, 뒤집힌 쌍은 그대로(각 200회).

### 6. run 스택 불변식

- 불변식: 스택의 모든 i에 대해 `runLen[i] > runLen[i+1] + runLen[i+2]`이고 `runLen[i] > runLen[i+1]`.
- `[120, 80, 25, 20, 30]` → 25·20 병합 → `[120, 80, 45, 30]`에서 위 3개(80 > 45 + 30, 45 > 30)만 보고 종료. 그러나 120 ≤ 80 + 45로 아래쪽이 깨졌다(실험 C 출력 `깨진 불변식: 120 <= 80 + 45`).
- 틀린 단계: **유지**. "위 3개만 다시 세우면 전체가 유지된다"는 귀납 단계에 빈틈이 있었다. 병합으로 생긴 run이 그 아래와의 관계를 바꾸는데 다시 확인하지 않았다.

### 7. 왜 배열 범위 예외인가

- 불변식이 전부 성립하면 run 길이가 r_k > r_{k−1} + r_{k−2}로 피보나치보다 빨리 커진다. 그래서 run 개수는 배열 길이의 로그 수준이고, 고정 크기 스택(입력 길이 119,151 이상에서 40)으로 충분하다고 계산했다(노트의 어림: int 길이 배열에 run 약 38개).
- 불변식이 깨지면 run 길이가 그만큼 빨리 커지지 않아 run이 더 많이 쌓인다. 스택 칸(40)을 넘는 순간 `pushRun`에서 `ArrayIndexOutOfBoundsException: 40`이 났다(JDK-8072909·블로그 재현, 길이 67,108,864).

### 8. 2015년과 2018년

- 2015년(JDK-8072909, JDK 9 b51 등): 스택 길이를 늘렸다(40 → 49). 블로그는 "they opted to increase the allocated runLen "sufficiently""라고 적었다. 증상 완화다 — 불변식 위반은 남는다.
- 2018년(JDK-8203864, JDK 11): Pivoteau의 분석이 "changing Timsort stack size ... is wrong and that it is still possible to make it break"라고 전했고, 알고리즘 수정을 권했다. OpenJDK 21 소스의 `mergeCollapse`는 위 4개를 검사한다 — 불변식을 복구하는 근본 수정이다.

### 9. 막았을 장치와 공통점

- Debian: 엔트로피 입력 경로의 회귀 테스트, 대량 생성 표본의 중복 검사, 암호 코드 상류 수정의 상류 확인.
- Java 7 정렬: 비교자 계약 속성 테스트(무작위 세 원소의 부호 반대칭·추이성·0의 일관성), 허용 오차 대신 양자화한 키.
- TimSort 불변식: 불변식 전체 검사 assert(테스트·디버그), 형식 검증, 적대적 입력 생성기.
- 공통점: 결과가 그럴듯해 보이는 동안 수학 전제 위반이 숨어 있었고, 그것을 드러낸 것은 출력 검사가 아니라 전제를 직접 따지는 방법(세기·공리 검사·증명)이었다.
