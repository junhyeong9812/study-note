# software-design/32-inversion-of-control-and-framework-flow — 정답

## 정답

### 1. 반복되는 흐름과 할리우드 원칙

- 소켓·요청 읽기·스레드 배정·응답 쓰기·예외 처리·자원 닫기 같은 **흐름**을 매번 다시 쓴다. 바뀌는 것은 "이 요청에 무엇을 돌려줄까" 같은 칸 몇 개다.
- 할리우드 원칙: "Don't call us, we'll call you." 내 코드가 프레임워크를 부르는 대신 프레임워크가 정해진 때 내 코드를 부른다. Fowler(bliki, 2005)는 이 표현이 Richard Sweet의 Mesa 논문(1983)에서 나온 것으로 보인다고 적었다.

### 2. 라이브러리 vs 프레임워크

```text
 라이브러리:  내 코드 ──call──> 라이브러리 ──return──> 내 코드 (흐름의 주인: 나)
 프레임워크:  프레임워크 ──call──> 내 코드 ──return──> 프레임워크 (흐름의 주인: 프레임워크)
```

- Fowler: 라이브러리는 부르면 일을 하고 제어를 돌려주는 함수 묶음. 프레임워크는 추상 설계를 품고, 내가 끼운 코드를 프레임워크가 부른다.
- Johnson·Foote(JOOP 1988): 사용자가 정의한 메서드는 프레임워크 안에서 불리고, 프레임워크가 메인 프로그램 역할을 한다. 이 제어 역전이 프레임워크를 확장 가능한 골격으로 만든다.

### 3. 템플릿 메서드 vs 콜백

```text
 템플릿 메서드: abstract 상위의 final export() { header(); for row: row(r); }  ← 하위가 header·row 채움(상속)
 콜백:         jdbc.query(sql, (rs, i) -> ...)                                ← 함수를 넘김(합성)
```

- 템플릿 메서드 = 상속으로 맞춤 → 화이트박스(상위 내부 관례를 알아야 함, 인스턴스 상태가 프레임워크 메서드에 암묵적으로 보임).
- 콜백·인터페이스 부품 = 블랙박스(정해진 인터페이스로만, 정보는 명시적으로 넘김).

### 4. 호출 스택

(실험 C, Spring Framework 6.2.11)

```text
    Main$Notifier.init
    InitDestroyAnnotationBeanPostProcessor$LifecycleMethod.invoke
    ...
    Main.lambda$main$5
    RowMapperResultSetExtractor.extractData
    RowMapperResultSetExtractor.extractData
    JdbcTemplate$1QueryStatementCallback.doInStatement
    JdbcTemplate.execute
```

- `init()`은 `InitDestroyAnnotationBeanPostProcessor`(빈 후처리기)가 불렀다.
- `RowMapper`는 `RowMapperResultSetExtractor`가 불렀고, 그 위로 `JdbcTemplate`의 내부 콜백(`QueryStatementCallback`)과 `execute`가 있다.
- 둘 다 내 코드에는 호출 줄이 없다.

### 5. 컨테이너 빈 vs `new`

(실험 D)

```text
  컨테이너 빈: initialized=true send=sent at 2026-10-02T00:00
  new 객체:   initialized=false clock=null
  new 객체 send() -> NPE: Cannot invoke "exp32.Main$Clock.now()" because "this.clock" is null
```

- `new` 객체는 주입·초기화 콜백·프록시 단계를 하나도 거치지 않았다. 컴파일은 되고 쓰는 순간 NPE다.
- 생성자 주입이었다면 `new Notifier()`가 인자 누락으로 컴파일되지 않아 실수가 일찍 드러난다.

### 6. 골격 변경 vs 훅

(실험 E)

- 골격 한 줄: `1 file changed, 1 insertion(+)`, 골든 **3/3 실패**(CSV·TSV·Markdown 모두 끝에 total 줄).
- 훅(기본 빈 문자열, CSV만 override): `1 file changed, 3 insertions(+)`, 골든 **1/3 실패** — CSV만, 의도한 변경이다.
- 세 하위 클래스가 한 파일에 있어 두 방식 모두 diff는 1파일이다. 차이는 줄 수가 아니라 **동작이 바뀐 하위 수**다.

### 7. 골격 변경이 이득인 경우와 합성으로 갈 신호

- 이득: 세 형식 모두에 들어가야 하는 변경(예: 줄바꿈 문자 통일, 공통 헤더 인코딩 수정). 골격 한 줄이 세 곳을 한 번에 고친다.
- 합성(콜백·전략)으로 갈 신호
  - 하위마다 다른 요구가 자주 온다(훅이 계속 늘어난다).
  - 하위가 상위의 필드·내부 순서에 기대기 시작한다(화이트박스 비용).
  - 하위 조합이 필요하다(CSV + 압축 + 암호화처럼 축이 여럿).

### 8. 호출처 0건인 메서드 추적

- 추적
  - 메서드 안에 임시로 스택을 찍거나(`StackWalker`·`Thread.dumpStack()`) 브레이크포인트를 건다. 스택 아래쪽의 프레임워크 클래스가 진입점이다(실험 C처럼).
  - 새벽 실행이면 스케줄러(`@Scheduled`·cron 설정), 이벤트 리스너, 수명 주기 콜백을 의심한다. 애너테이션·설정 파일을 검색한다.
  - Spring Boot Actuator `beans` 엔드포인트로 그 클래스가 빈인지 확인한다.
- 재발 줄이기: 메서드에 "누가 언제 부르나"를 주석으로 남긴다. 스케줄·리스너 등록을 한 곳(설정 클래스)에 모은다.
