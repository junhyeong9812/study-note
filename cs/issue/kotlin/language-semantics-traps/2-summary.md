# cs/issue/kotlin/language-semantics-traps — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
Java 직관                           Kotlin 실제                       드러나는 시점
─────────────────────────────────────────────────────────────────────────────────
/* ... /admin/** ... */ 는 한 주석   /* 가 중첩 → 안쪽 /* 가 새 주석   컴파일 (Unclosed comment)
                                     → 닫는 */ 짝 부족 → EOF까지 주석   → 빌드 실패 → 그 서비스 미기동
`backtick 이름` 은 아무 문자나       JVM 이름 규칙 : ; . / < > 등 금지  컴파일 (illegal characters)
data class equals = 내용 비교        배열 필드는 참조 비교               런타임 (조용히 false)
sealed 케이스 추가 = 조용한 누락     else 없는 when 이 전부 컴파일 오류  컴파일 (안전망 — 의도적으로 이용)
catch (Exception) = 오류만 잡음      취소도 CancellationException 예외   런타임 (취소가 재시도로 뒤집힘)
기본값 인자 = 오버로드               JVM 오버로드는 생성 안 됨            런타임 (리플렉션 NoSuchMethod)
                                     트레일링 람다가 마지막 인자로 재바인딩 컴파일 (호출부 의미 이동)

교정
  주석에 /* 시퀀스 금지(서술로)     · 식별자는 공백·대시
  contentEquals/contentHashCode     · when 에서 else 빼고 컴파일러를 망으로
  catch (c: CancellationException) { throw c } 를 먼저 · "삼키면 실패" 테스트
  @JvmOverloads · 호출부 명시 인자
```

## 핵심 문장

- Kotlin 블록 주석은 **중첩**된다 — 주석 본문의 `/*`(예: `/admin/**`)가 새 주석을 연다. 문자열 리터럴 안은 안전.
- backtick 식별자도 **JVM 이름 규칙**을 벗어날 수 없다(`:` `;` `.` `/` `<` `>` 등 금지).
- 배열은 **참조로 비교**된다 — data class의 자동 equals/hashCode는 배열 필드에서 거짓말을 한다.
- sealed + else 없는 `when` = 케이스 추가를 컴파일 오류로 드러내는 **안전망**. else는 그 망을 끈다.
- 코루틴 취소는 **예외로 전파**된다 — 광범위 catch 앞에서 `CancellationException`을 재던진다.
- 기본값 인자는 **JVM 오버로드를 만들지 않는다** — 리플렉션·Java 호출자에겐 `@JvmOverloads`.
- 컴파일러가 잡는 함정은 빨리 드러나지만, 동등성·취소·리플렉션은 **테스트로만** 잡힌다.
