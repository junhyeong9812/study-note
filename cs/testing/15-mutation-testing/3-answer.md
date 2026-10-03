# testing/15-mutation-testing — 정답

## 정답

### 1. 같은 커버리지, 다른 품질

- 커버리지는 "실행됐나"만 잰다. 실행 결과를 단언하는지는 재지 않는다.
- 변이 테스트는 코드에 작은 결함을 심고 테스트가 실패하는지 본다. 단언이 없거나 무디면 변이체가 살아남는다.
- 실험: NoAssertTest와 StrongTest는 JaCoCo 라인 4/4·분기 8/8로 같았지만, 변이는 1/14(7%) vs 14/14(100%).

### 2. 두 가설

- 유능한 프로그래머 가설(CPH): 프로그래머는 정답에 가까운 프로그램을 쓰므로 결함은 대개 작은 문법 변경 몇 개로 고칠 수 있다(DeMillo 외 1978).
- 결합 효과: 단순한 결함을 전부 구별하는 테스트 데이터는 복잡한 결함도 상당 부분 구별한다. Offutt가 "복잡한 변이체는 단순한 변이체에 결합돼 있다"로 정식화했다.
- 둘 다 **가설**이다(Jia–Harman 2011 II.A). 변이 검출과 실제 결함 검출의 상관을 보인 실증 연구(Just 외 FSE 2014)가 근거로 인용된다.

### 3. NoAssertTest

(실험, PIT 1.20.4 · JUnit 5.13.4 · JaCoCo 0.8.14, 2026-10-03)

```text
Pricing,0,30,0,8,0,4
>> Generated 14 mutations Killed 1 (7%)
>> Mutations with no coverage 0. Test strength 7%
```

- 1개가 죽는다. 6번 줄 `amount < 0`의 조건 반전(`NegateConditionalsMutator`)이다.
- 이유: 반전되면 정상 금액에서 `IllegalArgumentException`이 나고, 그 예외가 테스트 밖으로 나가 테스트가 실패한다. 단언이 없어도 예외는 잡힌다.

### 4. WeakTest 생존자

```text
ConditionalsBoundaryMutator,discountedPrice,6,SURVIVED
ConditionalsBoundaryMutator,discountedPrice,7,SURVIVED
ConditionalsBoundaryMutator,discountedPrice,8,SURVIVED
```

- 셋 다 경계 변이(`<`↔`<=`, `>=`↔`>`)다.
- 죽이는 입력: 6번 줄은 `0`(0에서 예외가 나면 실패), 7번 줄은 VIP `100000`/`99999`, 8번 줄은 `50000`/`49999`. 이것을 넣은 StrongTest는 14/14였다.

### 5. PartialTest 점수

- Killed % = 6 / 14 = 43%. 분모에 실행 안 된 변이(NO_COVERAGE 6개)를 포함한다.
- Test strength = 6 / (14 − 6) = 75%. killed / (killed + survived), NO_COVERAGE 제외(PIT maven 문서 `testStrengthThreshold` 정의).
- 다른 이유: Test strength는 "실행된 곳에서 단언이 얼마나 날카로운가"만 본다. 실행 범위가 좁으면 둘이 갈린다.
- Jia–Harman의 MS = 죽인 수 / (전체 − 등가 변이체 수). PIT는 생성한 변이체가 등가인지 판정해 분모에서 빼지 않으므로 분모가 다르다(로깅 줄처럼 일부는 처음부터 변이하지 않는다).

### 6. abs의 경계 변이

- `x <= 0`으로 바꾸면 x = 0일 때 `-0 = 0`을 반환한다. 원본도 0을 반환한다. 어떤 입력에서도 결과가 같아 **어떤 테스트로도 못 죽인다.**
- 이름: 등가 변이체.
- 자동으로 전부 걸러낼 수 없다. 프로그램 동치는 결정 불가능하다(Jia–Harman 2011 II.B). 실험에서 0을 포함한 테스트로도 4/5(80%)에서 멈췄다.

### 7. 비용과 줄이는 법

- 비용: 변이체 수 × (변이체마다 돌리는 테스트 시간).
- PIT: 먼저 줄별 커버리지를 재고, 변이된 줄을 덮는 테스트만 돌린다(실험 "Ran 14 tests (1 tests per mutation)"). `targetClasses`·`targetTests`·`threads`·`withHistory`로 더 줄인다.
- Google(ICSE-SEIP 2018): 리뷰 중인 diff에서 변경되고, 커버되고, arid가 아닌 줄에만 줄당 변이체 하나(연산자 무작위).
- arid 노드: 로그 출력·메모리 예약 호출·stdout 쓰기처럼 단위 테스트가 보통 검증하지 않는 코드. 언어별 전문가 규칙과 개발자 "Not useful" 피드백으로 정한다. 복합 노드는 자식이 전부 arid일 때 arid다.

### 8. green suite 오류와 불안정 테스트

- 원인: 변이 전 원본에서 실패하는 테스트가 있다. 실험에서 기대값을 잘못 적은 행(99999 VIP → 94999)이 있었다.
- 대처: 실패 테스트를 고쳐 초록으로 만든 뒤 돌린다.
- 불안정 테스트: 변이와 무관하게 실패하면 그 변이체가 "KILLED"로 세어진다. 점수가 부풀고 실행마다 달라진다. 먼저 결정적으로 고치거나 대상 테스트에서 뺀다.

### 9. 100% 게이트

- 문제: 등가 변이체는 못 죽인다(실험 `abs` 80%). 게이트를 영원히 못 넘거나, 통과용 억지 테스트·코드 비틀기가 생긴다. 큰 코드베이스에서는 실행 시간도 문제다.
- 대안: 생존자를 사람이 검토해 등가로 표시하고, 임계값은 팀이 정한 수준으로 둔다. 변경된 줄의 새 생존자를 리뷰에서 보여 주는 방식(Google)도 있다.

### 10. 생존자 → 테스트 설계

- 경계 변이(CONDITIONALS_BOUNDARY) 생존 → 그 비교의 경계값과 ±1을 추가(경계값 분석).
- 조건 반전·`&&` 관련 생존 → 조건 조합 열이 빠졌는지 결정 테이블로 확인.
- 반환값 변이(`replaced int return with 0`) 생존 → 그 반환값을 아무도 단언하지 않는다는 뜻 → 결과 단언 추가.
