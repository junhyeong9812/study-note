# testing/11-test-data-and-fixtures — 정답

## 정답

### 1. 세 문제와 픽스처

- 준비가 길다: 중첩 생성자 호출이 테스트 본문을 채워, 무엇을 검증하는지 묻힌다.
- 같이 쓰면 얽힌다: 한 테스트가 재고를 예약하면, "재고 10개"를 기대하는 다른 테스트가 순서에 따라 깨진다.
- 바꾸면 번진다: 생성자에 인자 하나를 더하면 그 생성자를 부르는 테스트가 전부 컴파일 오류.
- 픽스처: 테스트 실행 전의 환경 상태(Meszaros: "the state of the test environment before the test"). 객체·DB 행·파일·설정 모두.

### 2. 2×2 표

| | 테스트마다 새로 | 여러 테스트가 공유 |
|---|---|---|
| 필요한 만큼(Minimal) | 가장 읽기 쉽고 얽히지 않는다 | 드묾 |
| 표준 세트(Standard) | 얽히지 않지만 무엇에 기대는지 흐려진다(General Fixture) | 빠르지만 얽힌다(Interacting Tests), 고치기 무섭다 |

- Fresh가 너무 느리면 Shared 전에 **Immutable Shared Fixture**(공유하되 아무도 고치지 않는 것)를 고려하라(xunitpatterns.com "Fresh Fixture").

### 3. JUnit 5 수명

- 인스턴스 필드: 기본(per-method)에서는 테스트 메서드마다 테스트 클래스 인스턴스를 새로 만들므로 공유되지 않는다.
- `@BeforeEach`: 테스트마다 실행되므로 그 안에서 만든 것도 테스트마다 새것이다.
- `static` + `@BeforeAll`: 클래스당 한 번 만들어 그 클래스의 모든 테스트가 공유한다.
- `PER_CLASS`: 클래스당 인스턴스 하나라 인스턴스 필드도 공유된다. 테스트가 그 필드의 바뀌는 상태에 기대면 `@BeforeEach`나 `@AfterEach`에서 되돌려야 할 수 있다(User Guide 2.12). 바뀌지 않는 필드나 일부러 공유하는 비싼 자원은 그대로 둔다. 대신 `@BeforeAll`을 `static`이 아닌 메서드에 둘 수 있다.

### 4. 공유 재고 실험

- 공유 판은 "아직 10개"가 맨 앞일 때만 통과한다. 4+5=9 ≤ 10이라 두 예약 순서는 상관없다.
  - 실험: 20회 중 8회 통과(`nothingReservedYet`이 첫 번째인 두 순서, 4회+4회), 12회 실패.
- 인스턴스 필드 판은 같은 순서들에서 20회 모두 통과했다. 테스트마다 재고 10개를 새로 받는다.

### 5. 기본 순서

- JUnit User Guide: "deterministic but intentionally nonobvious". 매번 같지만 어떤 순서인지 예측하기 어렵다.
- 공유 픽스처 테스트가 우연히 통과하는 순서였는데, 테스트 추가(또는 이름 변경)로 기본 순서가 바뀌어 실패하는 순서가 됐다. 실험의 기본 순서는 `reserveFive → reserveFour → nothingReservedYet`로 공유 판이 실패했다.
- 실패한 테스트는 무죄이고, 앞서 실행된 테스트가 공유 상태를 바꾼 것이 원인이다.

### 6. 세 생성 방법

- Creation Method: 객체 생성 절차를 의도를 드러내는 이름의 메서드 뒤에 숨긴다.
- Object Mother: 이름 붙은 표준 예시 객체를 돌려주는 클래스(Fowler 2006). 테스트가 마더의 정확한 데이터에 기대기 쉽다.
- Test Data Builder(Pryce 2007): 네 요소
  - 생성자 인자마다 인스턴스 변수,
  - 그 변수를 흔히 쓰거나 안전한 값으로 초기화,
  - 그 값들로 객체를 만드는 `build()`,
  - 값을 덮어쓰는 연쇄 가능한 공개 메서드(`with*`).

### 7. 생성자 변경과 마더 변경

- 컴파일 오류: 직접 호출 6곳(테스트마다), 마더 3곳(팩터리 메서드마다), 빌더 1곳(`build()`). 마더·빌더의 테스트 본문은 0곳.
- 마더의 `regular()`에 한 줄을 더하면, 그 정확한 값(합계 3000·2줄)에 기대던 `sumsLines`·`regularHasTwoLines` 2개가 깨졌다. 빌더 쪽 기존 테스트는 0개 깨졌다.

### 8. 순서 의존 확인

```bash
mvn test -Djunit.jupiter.testmethod.order.default='org.junit.jupiter.api.MethodOrderer$Random' \
         -Djunit.jupiter.execution.order.random.seed=7      # 메서드 순서 섞기
mvn test -Dsurefire.runOrder=random -Dsurefire.runOrder.random.seed=7   # 클래스 순서 섞기
```

- 시드를 바꿔 여러 번 돌리고, 실패한 시드를 기록해 재현한다. 첫 명령은 실험 클래스에서 시드 2·6 통과, 1·3 실패로 확인했다.
- 실패 위치를 믿으면 안 되는 이유: 공유 상태 장애에서는 실패한 테스트(상태를 읽은 쪽)와 원인 테스트(상태를 바꾼 쪽)가 다르다. 실패 직전에 실행된 테스트 목록을 본다.

### 9. DB 잔여 픽스처

- Meszaros의 이름
  - Unrepeatable Test: 같은 테스트의 다음 실행이 지난 실행이 남긴 데이터와 충돌한다.
  - Test Run War: 여러 사람·작업이 같은 공유 픽스처(테스트 DB)를 동시에 쓰며 서로 깬다.
- 격리 방법(셋 이상 중 아무거나)
  - 테스트를 트랜잭션으로 감싸고 끝에 롤백한다(SUT가 자기 트랜잭션을 커밋하지 않아야 한다).
  - 실행·테스트마다 고유 키(접미사)를 쓴다.
  - 작업마다 별도 DB·스키마·컨테이너를 쓴다.
  - 테스트 전·후에 테이블을 비운다(병렬이면 서로 지울 수 있다).

### 10. DAMP와 빌더, 거대 setUp

- DAMP(Descriptive And Meaningful Phrases): 테스트에서는 읽기 쉬움을 위해 약간의 중복을 허용한다. 공용 setUp으로 다 숨기기보다, 각 테스트에 중요한 값을 드러낸다.
- 빌더 사용법과 이어짐: 무관한 값은 빌더 기본값에 맡기고, 결과를 좌우하는 값은 `with*`로 테스트 본문에 적는다. 기본값에 기대어 결과를 단언하면 그 값이 안 보인다.
- 거대 `setUp()`: 여러 테스트를 섬기려고 커진 표준 픽스처라, 각 테스트가 그중 무엇에 기대는지 본문에서 안 보인다. 기대값 48,300이 어디서 왔는지 알 수 없는 Obscure Test가 된다(Mystery Guest·General Fixture, 12번).
