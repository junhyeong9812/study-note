# log — errata-fixes-2

| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-10-08 | 요구 "다른 영역 오류들 수정하자" — 범위 4묶음 전부(노트 오류·커리큘럼 본문·원고 3건·옛 형식), 검증 가볍게·합의 auto | 인터뷰 |
| 2026-10-08 | 옛 형식 2편 확인: `domain-modeling/advanced` 0 PASS/30 FAIL, `data-structure/[0-9]*` 8 PASS/35 FAIL — 컬렉션 형식 → 사용자 "컬렉션 전체 전환" 선택 | 전환은 별도 작업(이 작업은 사실 오류만) |
| 2026-10-08 | 브랜치 `docs/errata-fixes-2`(main 1f78bfd7) | 생성 |
| 2026-10-08 | 수정 워커 4(Opus) 병렬: A 통계·알고리즘 9파일 · B 나머지 8파일 · C 원고 3파일 · D 커리큘럼 + 재생성(README 4) | 전 항목 수정, 미확인 0 |
| 2026-10-08 | 메인 점검: C의 EWMA '함정' 셋째 항목("에러 즉시 반환 인스턴스로 몰림")은 출처 없는 추론 → 제거(I4) · 생성기 재실행 안정 | 25파일 |
| 2026-10-08 | 검증: 상대 링크 446개 깨짐 0(A) · 새 형식 leaf check_new PASS(옛 형식 13-backtracking·27-ab-assign·nand-flash FAIL은 HEAD부터) · diff -U0 셀프 리뷰 | 통과 |

## 리뷰 ledger

| 대상 | 리뷰어 | 지적 | 반영 |
|---|---|---|---|
| T1~T3 | Opus 워커 1차 출처 재대조(curl: Cox MVS·JLS 17.5·PG17·Confluent·RFC 1952·RFC 10017·OWASP 2025·Finagle) | 범위 밖 동일 오류 추가 수정(38·42 3-answer, 커리큘럼 [?] 3곳) | 채택(근거 leaf 확인) |

## 생략한 검증

- codex 2차 리뷰 생략 — 사용자 선택 "가볍게"(stakes 낮음~중간, 1차 출처 재대조로 대체)

## 완료 요약

- 노트 오류 17파일·원고 3파일·커리큘럼 15곳 정정, 생성 README 4. 남은 것: 원고 02 표 Consistent Hashing '함정' 칸도 장점(범위 밖 — NEXT), algorithm/33:176 RFC 1951 최악 팽창 수치와 측정 +310B의 관계 미판정(NEXT).

