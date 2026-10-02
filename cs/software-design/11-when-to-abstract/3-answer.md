# software-design/11-when-to-abstract — 정답

## 정답

### 1. 너무 이르면 vs 너무 늦으면

- 너무 이르면: 서로 다른 지식이 한 함수에 묶인다. 호출처마다 다른 요구가 매개변수·조건으로 쌓여 `format(won, refund, report, parenNegative)` 같은 플래그 함수가 된다. 한 호출처를 고치면 다른 호출처가 깨진다.
- 너무 늦으면(또는 끝내 안 모으면): 같은 규칙이 여러 곳에 복사돼 있다. 규칙이 바뀌면 모든 곳을 고쳐야 하고, 하나를 빠뜨리면 화면끼리 숫자가 어긋난다.

### 2. 모양이 같은 검증 함수

- DRY 위반이 아니다. 『The Pragmatic Programmer』 20주년판 「The Evils of Duplication」: 코드는 같지만 표현하는 지식이 다르다 — "That's a coincidence, not a duplication."
- 판단 기준(acid test): 어떤 한 측면을 바꿀 때 여러 곳을, 여러 형식으로 고치게 되나? 나이 규칙과 수량 규칙은 따로 바뀐다.
- DRY는 소스 줄 복사 금지가 아니라 지식·의도의 중복에 관한 원칙이다(같은 절이 1판 설명이 부족했다고 밝힌다).

### 3. Rule of Three

- Don Roberts의 지침을 Fowler 『Refactoring』 1판 2장이 소개했다. 처음은 그냥 하고, 두 번째는 찡그리며 복사하고, 세 번째에 리팩터링한다(흔한 요약: "Three strikes and you refactor").
- 기다리는 이유(해석): 사례가 셋이면 무엇이 공통이고 무엇이 변하는 축인지 두 번 비교해 확인할 수 있다.
- 예외: 같은 지식(세율·검증 규칙·상태 전이)의 중복은 둘째 사례에서도 모으는 편이 싸다. 흩어 두면 하나를 빠뜨린다(6번).
- 2판(2018)도 「When Should We Refactor?」 절의 「The Rule of Three」에 같은 지침을 싣는다("Three strikes, then you refactor." — 독자 노트로 확인한 2차 출처).

### 4. 잘못된 추상화의 수명

```text
 ① 중복을 뽑아 이름 붙임 → ② 시간 경과 → ③ "거의 맞는" 새 요구
 → ④ 매개변수 + 조건 추가 → ⑤ 또 요구·또 매개변수·또 조건 (반복)
 → ⑥ 조건투성이 절차: 이해하기 어렵고 깨지기 쉽다
```

- 신호(Metz): 공유 코드에 매개변수를 넘기고 조건 경로를 더하고 있다. (Metz는 상황 파악용으로 조건 몇 개를 잠시 쌓는 것은 가끔 말이 된다는 단서도 단다.)
- 붙잡게 되는 이유: 매몰 비용 오류. Metz의 결론: "duplication is far cheaper than the wrong abstraction".

### 5. CR1 — 한 호출처만의 요구

(실험, JDK 21.0.12 temurin, 2026-10-02)

```text
--- dup-v0 → dup-cr1
 1 file changed, 4 insertions(+), 1 deletion(-)
--- abs-v0 → abs-cr1
 4 files changed, 12 insertions(+), 6 deletions(-)
## 테스트 @abs-cr1-slip (단계 cr1)
FAIL 환불영수증  got=(12,000원) (부가세 (1,090원) 포함)  want=-12,000원 (부가세 -1,090원 포함)
```

- DUP: `SettlementReport.java` 1파일.
- ABS(매개변수 추가): 시그니처가 바뀌어 공통 함수 + 호출처 3곳 = 4파일.
- 조건을 빠뜨린 경우(가정한 실수, 1파일 수정): 정산과 무관한 **환불 영수증** 테스트가 실패했다. 공통 함수 한 줄이 fan-in 전체에 퍼졌다.

### 6. CR2 — 공유 지식

```text
--- dup-cr1 → dup-cr2
 3 files changed, 3 insertions(+), 3 deletions(-)
--- abs-cr1 → abs-cr2
 1 file changed, 1 insertion(+), 1 deletion(-)
## 테스트 @dup-cr2-miss (단계 cr2)
FAIL 환불영수증  got=-12,000원 (부가세 -1,090원 포함)  want=-12,000원 (부가세 -1,091원 포함)
```

- 환불 영수증의 부가세만 1원(−1,090 vs −1,091) 어긋났다.
- 이 요구에서는 ABS(1파일)가 DUP(3파일)보다 유리했다. 인라인 후 부가세만 `Vat.of`로 다시 뽑은 RIGHT는 CR1·CR2 모두 1파일이다.

### 7. 되돌리기

1. 추상화된 코드를 모든 호출처에 인라인한다.
2. 호출처마다 넘기던 인자 값으로 실제 실행되는 부분만 남기고 나머지 분기를 지운다.
3. 남은 중복 중 같은 지식만 다시 뽑는다(실험: `Vat.of`).

- 컴파일러의 인라이닝 → 상수 전파·접기 → 도달 불가 코드 제거와 같은 구조다. 호출처가 넘기는 상수(`refund=false`)를 대입하면 그 호출처에서 실행될 수 없는 분기가 드러난다.
- 실험에서 되돌리기 비용은 5파일, +17/−21줄 한 번이었다.

### 8. 아무도 못 고치는 공통 모듈

- 원인: 공유 이유가 같은 지식이 아니라 비슷한 모양이었다. 공유로 얻은 것은 결합뿐이고, 한 팀의 요구가 다른 두 팀을 깨뜨릴 수 있어 변경이 막혔다.
- 보이는 형태: 공통 모듈 PR이 오래 열려 있고, 팀마다 같은 기능의 우회 코드가 늘어난다.
- 대처: 팀별로 실제 쓰는 경로를 확인해 각자 코드로 가져간다(복제). 진짜 공유 규칙만 남기고 소유 팀·버전 정책을 정한다.

### 9. 플래그와 이력

- 독립 불리언 k개 → 경로 최대 2^k개. NPath 같은 경로 수 지표가 이를 센다([52-complexity-metrics](../52-complexity-metrics/2-summary.md)).
- 이력: 두 파일이 함께 나온 커밋 수를 센다.

```bash
comm -12 <(git log --format=%h -- A.java | sort) <(git log --format=%h -- B.java | sort) | wc -l
```

- 각자 바뀐 횟수에 비해 함께 바뀐 횟수가 적으면 우연한 중복일 가능성이 크다(해석). 공동 변경 분석은 53 code-forensics-hotspots에서 다룬다.
