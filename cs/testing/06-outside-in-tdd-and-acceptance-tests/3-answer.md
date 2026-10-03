# testing/06-outside-in-tdd-and-acceptance-tests — 정답

## 정답

### 1. 단위는 초록, 기능은 고장

- 단위 테스트는 시험 대상과 협력 객체를 **테스트 안에서 직접** 조립한다. 실제 조립 코드(빈 설정·Composition Root·라우팅·직렬화 설정)는 실행되지 않는다.
- 그래서 조립에서 생긴 실수(연결 누락·잘못된 인스턴스 공유)는 단위 테스트에 보이지 않는다.
- 인수 테스트는 실제 앱을 띄워 바깥에서 조작하므로, 실제 조립을 지나간다.

### 2. 이중 루프

```text
   바깥: 인수 테스트(기능 하나) — 빨강 ─────────────────────▶ 초록
            안쪽: 단위 테스트 빨강→초록→정리 (분 단위로 여러 번)
```

- 바깥 루프는 기능 단위, 안쪽 루프는 작은 동작 단위다. 바깥이 훨씬 오래 빨강이다.
- GOOS 5장 "Separate Tests That Measure Progress from Those That Catch Regressions": 구현 중인 인수 테스트(진행)와 이미 통과한 인수 테스트(회귀)를 나눠, 진행 중인 빨강이 회귀 신호를 가리지 않게 한다.

### 3. Walking Skeleton

```text
   수평: UI·API·도메인·DB를 층마다 다 만들고 마지막에 붙인다
   수직: 모든 층을 얇게 한 줄 뚫어 첫날부터 끝에서 끝까지 돈다
```

- 정의(GOOS 4장): "the thinnest possible slice of real functionality that we can automatically **build, deploy, and test** end-to-end".
- 세 동사: 빌드, 배포, 테스트 — 모두 자동으로.

### 4. 바깥에서 안으로의 mock

- 바깥 객체를 TDD하다 보면 일을 맡길 상대가 필요해진다. 그 상대의 **역할(인터페이스)**을 테스트가 요구하는 모양대로 정하고, 아직 없으니 mock으로 대신한다. mock이 설계 도구가 된다.
- 04번 런던파(mockist)와 같은 쪽이다. 과용하면 구현에 묶인 테스트가 된다.
- mock하는 대상은 내가 정의한 인터페이스여야 한다(GOOS 8장 "Only Mock Types That You Own"). 라이브러리 타입을 직접 mock하면 그 동작을 추측해 적게 된다.

### 5. 조립 실수

- 단위 테스트 4개는 모두 초록이다(`FindUserTest`·`HttpApiTest` 각 1, `RegisterUserTest` 2).
- 인수 테스트 "가입 후 조회"는 빨강이다. Raw 판 `expected: 200 but was: 404`, 첫 DSL 판 `Expecting value to be true but was false`.
- 단위 테스트는 각자 저장소 하나를 만들어 올바르게 넣는다. 실제 `App` 생성자는 실행하지 않으니, 저장소가 둘로 갈라진 사실을 볼 수 없다.

### 6. 경로 변경

- 고칠 자리: Raw 판은 테스트 본문 5곳, DSL 판은 드라이버 2곳(본문 0곳). 드라이버만 고치자 DSL 3개 통과, Raw 3개는 그대로 실패.
- 3개 중 2개만 실패한 이유: 첫 드라이버의 `register()`는 201이면 `true`, 아니면 `false`였다. 경로가 틀려 받은 404도 `false`라, "중복이라 거절됨(false)"을 기대한 테스트가 우연히 통과했다(거짓 통과).
- 개선 드라이버는 기대 상태 코드를 직접 확인하고 다르면 예외를 던진다. 같은 경로 변경에서 3개 모두 `register a@x.test: expected HTTP 201 but was 404`로 실패했다.

### 7. Given-When-Then과 추상화 수준

- 원문: "Given some initial context (the givens), When an event occurs, Then ensure some outcomes."
- "버튼 #submit 클릭"은 **어떻게 조작하는지**다. 인수 테스트 본문은 **무엇을 하는지**(가입한다)를 말해야 한다. 조작 세부를 본문에 쓰면 화면이 바뀔 때마다 모든 시나리오를 고쳐야 한다. 조작은 드라이버 한 곳으로 내린다.

### 8. 가입은 되는데 조회가 안 됨

- 의심: 조립(Composition Root·빈 설정)에서 두 유스케이스가 서로 다른 저장소·캐시·데이터소스를 받았다. 라우팅 누락도 후보다.
- 추가할 테스트: 실제 앱을 띄워 "가입 → 조회"를 바깥에서 확인하는 인수 테스트. 실패 메시지가 단계와 받은 응답을 말하게 드라이버를 쓴다.
- 고칠 것: 공유해야 할 객체를 조립 한 곳에서 하나만 만들어 주입한다.

### 9. 계층별 완성 뒤 대량 불일치

- 빠진 실천: Walking Skeleton. 끝에서 끝까지 도는 경로가 마지막에야 생겨, 연결 문제가 한꺼번에 드러났다.
- 다음 시작: 아무 기능 없는 앱이라도 빌드·배포·인수 테스트 한 개가 자동으로 도는 골격을 첫 기능보다 먼저 만든다. 이후 기능은 세로 조각으로 붙이고, 기능마다 인수 테스트로 시작한다.

### 10. 세 계층과 보편 언어

| 계층 | 바뀌는 때 |
|---|---|
| 시나리오(Given-When-Then) | 업무 규칙·요구가 바뀔 때 |
| DSL(도메인 동사) | 업무 동작의 어휘가 바뀔 때 |
| 드라이버(HTTP·UI 세부) | 경로·화면·프로토콜이 바뀔 때 |

- 시나리오와 DSL의 단어는 업무 쪽이 쓰는 말이어야 한다. 그것이 도메인 모델링의 보편 언어(ubiquitous language)다. North도 BDD가 분석 과정의 보편 언어를 정의하려는 시도였다고 쓴다("BDD provides a 'ubiquitous language' for analysis").
