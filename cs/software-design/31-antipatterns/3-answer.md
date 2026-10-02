# software-design/31-antipatterns — 정답

## 정답

### 1. 안티패턴의 정의

- 패턴: 반복되는 문제에 대한 검증된 해법. 안티패턴: 흔히 쓰이지만 결과가 나쁜 해법.
- Andrew Koenig가 1995년 JOOP 칼럼 "Patterns and Antipatterns"에서 처음 썼고, 1998년 『AntiPatterns』(Brown 외)가 널리 알렸다(Wikipedia 경유).
- 인용되는 정의: 안티패턴은 패턴과 같지만, 해법 대신 "겉보기엔 해법 같지만 아닌 것"을 준다.

### 2. Big Ball of Mud의 힘

- Foote·Yoder(PLoP '97): Time, Cost, Experience, Skill, Visibility, Complexity, Change, Scale.
- 흐름: 버릴 코드가 남고(THROWAWAY CODE) → 조금씩 덧붙고(PIECEMEAL GROWTH) → 돌아가게만 유지된다(KEEP IT WORKING). 대응으로 SHEARING LAYERS·SWEEPING IT UNDER THE RUG·RECONSTRUCTION을 든다.
- 시사점: 진흙은 게으름만의 결과가 아니라 마감·비용·보이지 않음에 대한 반응이다. 코드만 고치고 그 힘을 그대로 두면 같은 모양이 다시 생긴다.

### 3. God Object의 그래프와 지표

```text
 여러 호출자 ──> [OrderManager] ──> 여러 의존 대상
               fan-in 큼          fan-out 큼
```

- 지표: 들어오는 의존 수(그 클래스를 쓰는 파일 수), 나가는 의존 수(import·필드 수), 줄 수, 그리고 `git log` 변경 빈도. 크고 자주 바뀌는 파일이 우선 후보다.

### 4. 병합 결과

(실험 A, git 2.43.0)

```text
### god
  coupon:  1 file changed, 2 insertions(+)
  settlement:  1 file changed, 2 insertions(+)
CONFLICT (content): Merge conflict in OrderManager.java
### split
  coupon:  1 file changed, 4 insertions(+)
  settlement:  1 file changed, 5 insertions(+)
Merge made by the 'ort' strategy.
```

- God 판은 충돌, 분리 판은 자동 병합.
- 줄 수는 God 판이 적었다(2줄씩 vs 4·5줄). 비용은 줄 수가 아니라 같은 자리를 함께 건드린다는 데서 나왔다.

### 5. 테스트 순서 의존

(실험 B, JUnit 1.12.2)

- 이름순(`normalDay` → `promotionDay`): 4개 모두 통과.
- 이름 역순(`promotionDay` → `normalDay`): `normalDay() ✘ expected: <10000> but was: <8000>` — 1건 실패. 앞 테스트의 할인율 0.2가 남았다.
- 주입판(`new PricingService(...)`)은 두 순서 모두 통과.

### 6. 동시성 결과

(실험 C, `--cpus=2`, 실행마다 다름)

- 카운트: 400,000이어야 하는데 집필 20회 219,162~303,651, 점검 재실행 20회 215,829~327,778(실행마다 다르다). `long++`가 읽기-수정-쓰기라 겹치면 증가분이 사라진다.
- `HashMap.size()`: 4,000이어야 하는데 3,464~6,468(40회 범위) — 작게도 크게도 나온다.
- 예외: 0건. 조용히 틀렸다.
- 드문 일: 감시 없는 첫 실행은 끝나지 않았다. 스레드 덤프에서 한 스레드가 `HashMap$TreeNode.balanceInsertion`에서 RUNNABLE로 2분 넘게 돌고 있었다(이 환경에서 집필·점검 합쳐 41회 중 1회).
- 주입판(`AtomicLong`·`ConcurrentHashMap`)은 출력한 5회 모두 400,000·4,000.

### 7. 싱글턴의 진짜 문제와 경계

- 문제는 "하나"가 아니라 **전역에서 꺼내 쓰는 가변 상태**다. 누가 언제 바꿨는지 호출 관계에 드러나지 않고, 테스트·스레드 사이로 샌다.
- Spring 빈 싱글턴 스코프는 인스턴스가 하나지만 주입으로 받고(테스트에서 다른 인스턴스로 바꿀 수 있다) 대개 상태를 두지 않는다. 상태를 두면 같은 문제가 생긴다.
- God Object 분리가 손해인 경우: 기능이 하나뿐이거나 함께 바뀌는 책임을 억지로 쪼갤 때. 파일만 늘고 한 변경이 여러 파일에 퍼진다. 분리 기준은 "따로 바뀌나"다.

### 8. CPU 100% + 집계 누락

- 뜰 것: 스레드 덤프를 몇 초 간격으로 2~3번. 같은 스택에 계속 머무는 RUNNABLE 스레드를 찾는다. 실험 C에서는 `HashMap.put → resize → TreeNode.split → treeify → balanceInsertion`이었다.
- 좁히기: 그 스택의 맨 위 애플리케이션 프레임(`Pricing.quote`)이 공유하는 자료구조를 본다. 전역·`static`·싱글턴 필드인지, 동기화가 없는지.
- 집계 누락도 같은 원인(비원자적 갱신)으로 설명된다.
- 고치기: 전역 가변 상태를 없애고 주입으로 바꾼다. 공유가 꼭 필요하면 `ConcurrentHashMap`·`AtomicLong`(또는 `LongAdder`). 멈춘 인스턴스는 재시작이 당장의 대처다.
