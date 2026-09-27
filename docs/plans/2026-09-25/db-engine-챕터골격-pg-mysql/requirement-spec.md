# 요구사항 명세서 (requirement-spec)

> 작성일: 2026-09-25 · 작업 폴더: `docs/plans/2026-09-25/db-engine-챕터골격-pg-mysql/`

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "project 내 db엔진쪽에 impl문서 순서대로 빈 md파일 싹다 만들어놓고 각 주제만 적어놔줘 그리고 오픈소스 포스트그레와 마이에스큐엘 설명과 해당 프로젝트를 링크하려고 해. 포스트그레는 https://github.com/postgres/postgres 이거 핀하면 되고, mysql은 https://github.com/mysql/mysql-server 이거 포크하면 되는거지?"
- 해석: "project 내 db엔진쪽" = `study-note/project/db-engine/` (기존 챕터 형식 `08-01-wal-recovery/{1-question,2-summary,3-answer}.md`). impl 원본 = `~/project/db-engine/impl/` 36파일.
- Q/A: MySQL 태그 = `mysql-9.7.2`. 로컬 클론 = 사용자가 포크한 뒤 받는다(이번 범위 밖). index.md = 수정하지 않는다("지금 구조로 폴더들 쭉 만들어놓고, mysql과 postgre쪽에 해당 폴더를 링크"). 승인 · auto.
- 범위 추가(사용자, 착수 중): "둘 다 포크해놨어" → 앞서 합의한 조건("내가 포크하면 받자") 충족. `~/project/{postgres,mysql-server}` 에 포크(origin) 얕은 클론 + upstream 원격 + 기준 태그 체크아웃, README 읽는 기준에 로컬 경로 1줄.

---

## 1. 목표·대상 (필수)

A. `project/db-engine/` 에 impl 순서대로 챕터 폴더 35개(기존 08-01 제외) × 3파일(`1-question`·`2-summary`·`3-answer`) 생성. 각 파일은 제목 한 줄(`# NN-MM 주제 — 질문|정리|정답`)만. 주제 = impl 파일 첫 제목의 `—` 뒤.
B. `opensource/postgres/README.md`·`architecture/README.md` 에 기준 태그 `REL_18_6` (`724edf9bde`) 고정 + db-engine 연결 절 추가.
C. `opensource/mysql/` 골격 신설(postgres와 같은 5파일) — 기준 태그 `mysql-9.7.2` (`008e09c283`), InnoDB 범위, db-engine 연결 절. `opensource/index.md`·`README.md` 등록, 로드맵 상태 갱신.
D. 두 README의 db-engine 연결 = 소스 repo(github.com/junhyeong9812/db-engine) + 공부 노트(`project/db-engine/`) 링크 + 단계 대조 예정 표(후보 표기).

## 2. 경계·불변식 (필수)

- 기존 `08-01-wal-recovery/` 3파일 무수정. 기존 파일 덮어쓰기 금지(존재 시 중단).
- 챕터 폴더명 = impl 파일명(확장자 제외) 1:1 — 36개 전부 대응(14-01 두 개 포함).
- PG/MySQL 대조 내용은 "후보(소스 확인 전)"로 표기 — 소스를 읽지 않은 주장을 사실로 쓰지 않는다.

## 3. 기준소스 (필수)

`~/project/db-engine/impl/*.md` 첫 제목 · `git ls-remote` 로 확인한 태그 SHA(postgres `REL_18_6`=`724edf9bde9d356724ad384a2e196edc3c9f80f7`, mysql `mysql-8.4.11`=`99960bf74f`, `mysql-9.7.2`=`008e09c283`) · 기존 `project/db-engine/08-01` 형식.

## 4. 금지영역 (필수)

`~/project/db-engine` 레포(읽기만). `08-01-wal-recovery/`. `project/db-engine/index.md`·`README.md`. 다른 opensource 도구 폴더. 커밋·푸시·포크 금지(별도 지시 전).

## 5. 검증 방법 (필수)

챕터 폴더 수 = impl 파일 수(36) 대조 스크립트 · 파일당 1줄 확인 · 새/수정 md 상대 링크 실존 스크립트 · `git status` 로 금지영역 무변경. `project/db-engine/index.md` 무수정.

## 6. stakes (필수)

- 판정: 낮음 — 신규 문서 골격 + 인덱스 행 추가, 즉시 복구 가능.

---

## 7. 자율성

- [x] auto
- [ ] lazy

## 8. load-bearing 가정

- "빈 md + 주제만" = 기존 챕터 3파일 구조를 제목 한 줄로 채운 것 (1파일/챕터가 아님).

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1
- [x] 자율성 선택 → MODE=auto
