# python — Python 언어·FastAPI

Python 언어·표준 라이브러리와 그 위 FastAPI에 뿌리내린 패턴이다.\
공통 원리: **실행 경로와 언어 규칙(import 시점 바인딩·truthiness·모듈 해석)이 결과를 좌우한다** — 같은 코드가 실행 방식에 따라 다르게 동작할 수 있다.\
언어 레벨 카드는 이 폴더에, 프레임워크 카드는 하위 폴더에 있다.

## 공통 원리

```
  같은 코드 ──▶ 실행 방식 (pytest · python -m · 서버 기동)
                  │
                  ├─ sys.path·import 순서 다름 → 다른 모듈 로드
                  ├─ import 시점 바인딩        → 이후 변경 미반영
                  └─ truthiness·bool⊂int       → 조용한 분기 오류
                               ▼
                 초록불이 우연히 켜지거나 꺼짐
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [fastapi/](fastapi/) | 4 | 실행 모델·응답 경계 |

## 패턴 카드 (이 폴더 직속)

- [language-and-stdlib-traps](language-and-stdlib-traps/) — Python 언어·표준 라이브러리 규칙(bool⊂int·`"" in s`·except 중 traceback 프레임 보유·import 시점 바인딩·truthiness·csv 필드 상한·버퍼링)이 직관과 달라 드문 경로에서만 터진다.
- [module-resolution-and-accidental-pass](module-resolution-and-accidental-pass/) — 실행 경로(pytest vs python -m, 클래스패스 순서, import 시점 부작용)에 따라 모듈 해석이 갈려 초록불이 우연히 켜지거나 꺼진다.

> 이 폴더의 메타 태그: `resource-bounding`(1) · `contract-drift`(2) · `test-reliability`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
