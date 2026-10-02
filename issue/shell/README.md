# shell — 셸 스크립트

셸 스크립트의 종료 코드와 인용·확장 규칙, 스크립트 파일을 읽는 방식에서 나오는 패턴이다.\
공통 원리: **셸은 텍스트를 여러 계층에서 다시 해석하고, 종료 코드는 마지막 명령의 것만 남는다** — 단계별로 결과를 확인한다. 그리고 셸은 스크립트를 **실행하면서 읽는다** — 실행 중인 파일은 고치지 않는다.

## 공통 원리

```
  "명령 문자열" ──▶ 인용 ──▶ 확장 ──▶ word-split ──▶ glob ──▶ 실행
                                                             │
  cmd1 | cmd2 | cmd3 ──▶ $? = cmd3의 것 ─────────────────────┘
       (pipefail 없으면 cmd1 실패가 사라짐)

  runner.sh ──▶ 명령 읽기 → 실행 → 다음 명령은 파일의 현재 바이트 위치부터
                (실행 중 제자리 편집 → 어긋난 위치 → 문법 오류·엉뚱한 명령)
```

## 패턴 카드

- [exit-status-semantics](exit-status-semantics/) — 파이프라인·그룹 리다이렉트·`&&`의 종료 코드는 마지막 명령의 것이고 errexit·명령별 비0 의미(grep 1·iconv)가 계약을 흔든다 — pipefail과 단계별 rc를 명시한다.
- [quoting-expansion-layers](quoting-expansion-layers/) — 셸은 텍스트를 인용·확장·word-split·glob·heredoc 계층마다 다시 해석한다 — 중첩 인용·dotenv source·빈 매칭 glob·heredoc 종료 태그가 의도와 다른 명령을 만든다.
- [script-modified-while-running](script-modified-while-running/) — bash는 스크립트를 실행하면서 읽는다 — 실행 중 제자리 편집은 어긋난 바이트 위치에서 다음 명령을 읽게 해 문법 오류·정리 누락을 만든다, 진입점·입력 전체를 동결 사본으로 실행하고 실행 코드 = 기록 커밋을 시작 시 한 번 확인한다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `race-condition`(1) · `parser-differential`(1) — 태그별 전체 목록은 [issue 태그 역인덱스](../README.md#태그-역인덱스).
