# shell — 셸 스크립트

셸 스크립트의 종료 코드와 인용·확장 규칙에서 나오는 패턴이다.\
공통 원리: **셸은 텍스트를 여러 계층에서 다시 해석하고, 종료 코드는 마지막 명령의 것만 남는다** — 단계별로 결과를 확인한다.

## 공통 원리

```
  "명령 문자열" ──▶ 인용 ──▶ 확장 ──▶ word-split ──▶ glob ──▶ 실행
                                                             │
  cmd1 | cmd2 | cmd3 ──▶ $? = cmd3의 것 ─────────────────────┘
       (pipefail 없으면 cmd1 실패가 사라짐)
```

## 패턴 카드

- [exit-status-semantics](exit-status-semantics/) — 파이프라인·그룹 리다이렉트·`&&`의 종료 코드는 마지막 명령의 것이고 errexit·명령별 비0 의미(grep 1·iconv)가 계약을 흔든다 — pipefail과 단계별 rc를 명시한다.
- [quoting-expansion-layers](quoting-expansion-layers/) — 셸은 텍스트를 인용·확장·word-split·glob·heredoc 계층마다 다시 해석한다 — 중첩 인용·dotenv source·빈 매칭 glob·heredoc 종료 태그가 의도와 다른 명령을 만든다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `parser-differential`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
