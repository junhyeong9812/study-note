# issue/kotlin/spring/default-argument-evaluated-on-proxy — 정리 (힌트)

## 전체 흐름

```
컴파일 결과 (기본 인자가 있는 멤버 함수)
  public  hold(cmd, loader, before)                       ← 프록시가 가로채는 메서드
  public static hold$default(self, cmd, loader, before, mask, _)
          └─ mask에 생략된 인자 표시 → 기본값 식을 여기서 계산 (self = 호출자가 넘긴 참조)

문제 — 기본값이 필드를 읽는다
  호출자 ──▶ hold$default(self = 프록시, cmd, …)
              │ loader 생략 → self.repository::findById
              │               └─ 프록시 자신의 필드 = null (주입된 것은 대상 객체)
              ▼
            null 필드로 만든 조회 함수 → NPE
            (트랜잭션 어드바이스·대상 객체와 무관하게, 기본값을 프록시 기준으로 계산한 것이 원인)

고친 것 — 기본값은 null, 고르기는 본문에서
  호출자 ──▶ hold$default(self = 프록시, cmd, …)  loader 생략 → null (필드를 읽지 않음)
              ▼
            프록시.hold(cmd, null, …) ──▶ 어드바이스 ──▶ 대상.hold(…)
                                                        └─ load = loader ?: this.repository::findById
                                                                              └─ 대상의 필드 = 주입됨
```

## 핵심 문장

- Kotlin 기본 인자는 **호출 쪽 합성 함수**(`$default`)에서, 호출자가 넘긴 참조를 수신자로 계산된다 — 그 참조가 프록시면 프록시의 필드를 읽는다.
- Spring의 클래스 기반 프록시는 대상 클래스의 하위 클래스 인스턴스지만 **의존성은 대상 객체에만 주입**된다 — 프록시의 필드는 비어 있다.
- 상수·빈 람다처럼 **필드를 안 쓰는 기본값은 무해**하다. 위험한 것은 `this`의 상태(필드)를 읽는 기본값이다.
- 교정: 상태에 기대는 기본값은 `null`로 두고 **본문에서 해소**한다 — 본문은 프록시가 위임한 대상 객체 위에서 돈다.
- 프록시 없는 단위 테스트로는 안 보인다 — 실제 컨텍스트의 빈을 주입받아 부르는 테스트가 잡는다.
