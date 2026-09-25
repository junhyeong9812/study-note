# log

| 시각 | 사건 | 결과 |
|---|---|---|
| 20:24 | 명세 승인 · auto | MySQL 9.7.2, 클론은 포크 후, index.md 무수정 |
| 20:25 | 챕터 골격 35폴더 × 3파일 = 105파일 생성 | impl 36 = 폴더 36 (차집합 0), 새 파일 전부 1줄 |
| 20:25 | postgres 태그 고정 · db-engine 대조 절 / mysql 골격 5파일 / index·README·로드맵 갱신 | 링크 16파일 0 broken, 08-01·index.md·README.md 무변경 |
| 20:25 | 범위 추가: 포크 클론 (사용자 "둘 다 포크해놨어") | 포크에 태그 없음(기본 브랜치만 복사) 확인 → upstream에서 태그만 얕게 fetch 방식 |
| 20:26 | 클론 완료: postgres HEAD=724edf9bde (REL_18_6, 219M), mysql-server HEAD=008e09c283 (mysql-9.7.2, 1.8G) | 명세 SHA와 일치, remote origin=포크·upstream=원본, 작업트리 clean |
| 20:26 | 두 README 읽는 기준에 로컬 클론 1줄 | 완료 |

## 생략한 검증

없음 (낮음 — 셀프체크. 대조표 내용은 '후보' 표기)

## 완료 요약

- 신규: `project/db-engine/` 챕터 35폴더 × 3파일(제목 1줄), `opensource/mysql/` 5파일, 로컬 클론 2개(`~/project/postgres`, `~/project/mysql-server`)
- 수정: `opensource/postgres/README.md`(태그·대조 절·클론), `architecture/README.md`(태그), `opensource/index.md`·`README.md`, 로드맵
- 미커밋. CS 이슈 0건
