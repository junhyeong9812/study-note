# kotlin — Kotlin/JVM·Spring

Kotlin 언어와 그 위 Spring 계층에 뿌리내린 패턴이다.\
공통 원리: **런타임·언어의 기본값(인코딩·길이 단위·동등성·취소 예외)은 사람이 떠올리는 의미와 다르다** — 단위와 계약을 명시한다.\
언어 레벨 카드는 이 폴더에, 프레임워크 카드는 하위 폴더에 있다.

## 공통 원리

```
  값 "가나다" ──▶ 기본 charset ──▶ 바이트 ──▶ 길이 = ?
                     │                        ├─ 문자 3
                     └─ 기본값이 다르면 왜곡   ├─ UTF-16 코드유닛 3
                                              └─ UTF-8 바이트 9
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [spring/](spring/) | 4 | Spring·Jackson·아키텍처 |

## 패턴 카드 (이 폴더 직속)

- [charset-and-length-defaults](charset-and-length-defaults/) — 언어·런타임·클라이언트의 기본 인코딩과 길이 단위(바이트·UTF-16 코드유닛·코드포인트)가 값을 조용히 왜곡한다 — charset과 길이 단위를 명시한다.
- [language-semantics-traps](language-semantics-traps/) — Kotlin 언어 규칙(블록 주석 중첩·backtick 식별자 제약·배열 참조 동등성·코루틴 취소 예외)이 Java 직관과 달라 컴파일 오류·취소 파괴를 만든다.

> 이 폴더의 메타 태그: `least-privilege`(1) · `contract-drift`(1) · `encoding`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
