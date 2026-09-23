# typescript — TS/JS·브라우저·React·Next

TypeScript/JavaScript와 그 위 브라우저·React·Next.js에 뿌리내린 패턴이다.\
공통 원리: **런타임(브라우저·렌더러·번들러)이 코드를 언제, 어디서, 몇 번 실행하는지가 결과를 정한다** — 평가 시점·렌더 시점·실행 위치(서버/클라이언트)를 의식한다.\
언어 레벨 카드는 이 폴더에, 환경·프레임워크별 카드는 하위 폴더에 있다.

## 공통 원리

```
  TS 소스 ──▶ 번들러·테스트 러너 (모듈 해석 기준이 도구마다 다름)
                 │
                 ├─ 서버 렌더 (Next) ──▶ HTML ──┐
                 │                               ├─ 하이드레이션: 첫 렌더 일치해야
                 └─ 브라우저 (React) ────────────┘
                        ├─ 렌더·effect 시점  → stale state
                        └─ 입력 이벤트 모델  → IME·전파·포커스
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [browser/](browser/) | 1 | 브라우저 입력 |
| [next/](next/) | 4 | BFF·라우팅·모듈 해석 |
| [react/](react/) | 13 | 렌더링·상태·CSS |

## 패턴 카드 (이 폴더 직속)

- [js-language-traps](js-language-traps/) — JS 언어 규칙(TDZ·객체 리터럴 즉시 평가·중복 키 무음 덮어쓰기·try 안 await 없는 return·구조화 에러의 String 변환)이 직관과 달라 조용히 오동작한다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(2) · `least-privilege`(1) · `race-condition`(1) · `test-reliability`(1) · `single-source-of-truth`(2) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
