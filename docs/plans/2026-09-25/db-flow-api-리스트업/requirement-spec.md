# 요구사항 명세서 (requirement-spec)

> 작성일: 2026-09-25 · 작업 폴더: `docs/plans/2026-09-25/db-flow-api-리스트업/`

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "우선 둘다 다른 오픈소스들처럼 플로우랑 각 api 리스트업 하는게 맞지않아? 오픈소스 기준은 통일 시키는게 낫지않아? 우선 그렇게 리스트업해보고 db-engine도 리스트업해서 확인해볼래?"
- 해석: 기준 = `opensource/elasticsearch/architecture/` 형식(README 흐름 표: 흐름 | 진입점 `함수` L줄 | 문서 수 + 흐름 연결 그림 + 읽는 순서 / api-index: API | 핸들러 | 지나는 흐름 + "안 덮는 API" 명시). "리스트업" = 흐름 문서 본문을 쓰는 게 아니라 **목록(흐름·진입점·흐름별 메서드 목록·API 역인덱스)을 소스로 확인해 채우는 것**.
- 사실 확인: db-engine 작업트리 `src/main`은 사용자가 다시 치는 중(08단계까지, 1423줄). 21단계 전체 구현은 커밋 `5505edc`("complete: 21 stages + 12 보강, 120/120 tests").
- Q/A: "포스트그레 마이에스큐엘 각각 오픈소스로 정리하라고 db-engine과 상관없이" → db-engine 리스트업은 범위 제외(C 삭제). 흐름 선정도 db-engine 단계에 맞추지 않고 각 DB 소스 구조 기준. 기존 README의 'db-engine 과 잇기' 링크 절(직전 작업에서 요청)은 유지·무수정. 승인 · auto.
- 범위 추가(사용자, 착수 중): "그렇게 작업하고 이후 db-engine과 일치하는 주제쪽에 해당 주제는 db-engine의 어느 부분이라고 적는게 맞고, 이때 도식화랑 시각화 위주로 작업 진행할꺼야" → 흐름 선정은 여전히 각 DB 소스 기준. 선정이 끝난 뒤 **일치하는 흐름에만** 'db-engine 대응' 칸(챕터 폴더 링크)을 단다. 기존 'db-engine 과 잇기' 후보 표는 이 대응으로 교체(단일 출처). 도식화·시각화 위주는 이후 흐름 문서 작성 방식 — 이번 목록 단계에서는 흐름 연결 그림(ASCII)까지.

---

## 1. 목표·대상 (필수)

A. `opensource/postgres/architecture/{README,api-index}.md`: 소스(`~/project/postgres` REL_18_6)로 진입점 확인한 흐름 목록(흐름당 진입 함수 file:line + 거칠 메서드 목록 NN_) + 흐름 연결 그림 + api-index(SQL 문·GUC → 진입 함수 → 흐름, 안 덮는 것 명시).
B. `opensource/mysql/architecture/{README,api-index}.md`: 같은 형식, `~/project/mysql-server` mysql-9.7.2, InnoDB 중심.
C. 두 README 흐름 표에 'db-engine 대응' 칸 — 일치하는 흐름만 `project/db-engine/<챕터>/` 링크, 나머지 '-'. 대응 판정 근거 = impl 파일 제목·해당 impl이 다루는 객체.

## 2. 경계·불변식 (필수)

- 모든 file:line은 **실제로 연 파일**에서 온다(고정 태그/커밋 기준). 확인 못 한 것은 "미확인"으로 두고 지어내지 않는다.
- 흐름 문서 본문(`flows/<흐름>/NN_*.md`)은 만들지 않는다 — 목록까지만.
- 소스 레포 2개(`~/project/{postgres,mysql-server}`)는 읽기만.

## 3. 기준소스 (필수)

postgres `REL_18_6`(`724edf9bde`) · mysql `mysql-9.7.2`(`008e09c283`) · 형식 = ES architecture README·api-index.

## 4. 금지영역 (필수)

소스 레포 쓰기. `~/project/db-engine`. `project/db-engine/` 챕터 파일·index·README. 다른 opensource 도구 폴더. 커밋·푸시 금지(별도 지시 전).

## 5. 검증 방법 (필수)

워커가 뽑은 진입점 file:line 중 도구당 3개 이상을 메인이 직접 `sed -n` 으로 열어 대조 · 링크 실존 스크립트 · 소스 레포 2개 `git status` 무변경 · `git status`로 금지영역 무변경.

## 6. stakes (필수)

- 판정: 낮음 — 문서 목록, 복구 쉬움. 단 날조 위험(줄 번호)이 주된 실패모드라 표본 대조를 의무로 둔다.

---

## 7. 자율성

- [x] auto
- [ ] lazy

## 8. load-bearing 가정

- 흐름당 진입 함수 1개 + 메서드 5~10개 규모로 도구당 흐름 8~12개가 ES 형식과 맞는 크기다.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | PG 흐름·API 목록 (워커) | — | 진입점 file:line 표본 대조 통과 |
| 02 | MySQL 흐름·API 목록 (워커) | — | 〃 |
| 03 | 문서 반영 + db-engine 대응 칸 (메인) | 01~02 | 링크 0 broken |

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1
- [x] 자율성 선택 → MODE=auto
