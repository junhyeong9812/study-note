# 요구사항 명세서 (requirement-spec)

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "우선 리스트업을 해보면 postgres(pgvector),redis,nginx 3개부터 작업하고, 위 리스트는 별도 docs쪽에 위에 추출한 목록을 전체 쭉 정리해놔줘 처음 대화에 나온 기술 리스트업부터 쭉 정리한번하고 우선 3개 폴더 구조화하자"
- 전체 목록은 L0로 `docs/tool-analysis-roadmap.md`에 작성 완료(이 명세 범위 밖).
- Q/A: pgvector 위치 · 명세 승인 · 모드 — AskUserQuestion으로 확인.
- 범위 추가(사용자 지시, 착수 중): "키클록은 이미 오픈소스 내 project에 있으니 그걸 기준으로 오픈소스에 정리해보자" / "키클록까지 하면 될 꺼 같아" → `opensource/keycloak/` 같은 골격 추가. 기준 = 로컬 `~/project/keycloak`(태그 26.6.2, `0a402f777f`) + 한국어 완역 `~/project/keycloak-analyze`.

---

## 1. 목표·대상 (필수)

`opensource/postgres/`, `opensource/redis/`, `opensource/nginx/` 세 폴더와 `opensource/keycloak/`(범위 추가)을 ES 아키텍처 지도 모양의 **골격**으로 만들고 `opensource/index.md`·`README.md`에 한 줄씩 등록하면 끝.
폴더당 파일: `README.md`(왜 보는가·기준 커밋 자리·읽는 순서) · `index.md` · `architecture/README.md`(지도 골격, 흐름 표 비어 있음) · `architecture/api-index.md`(빈 표) · `concepts/index.md`. pgvector는 `opensource/postgres/pgvector/` 하위(같은 골격 축소판)에 둔다.

## 2. 경계·불변식 (필수)

신규 파일 생성 + `opensource/index.md`·`opensource/README.md`에 행 추가만. 본문 분석 내용(흐름 문서·기준 커밋 SHA)은 채우지 않는다 — 소스를 읽지 않은 주장 금지. `structure/`·`flows/`는 첫 문서가 생길 때 만든다(빈 폴더·.gitkeep 만들지 않음).

## 3. 기준소스 (필수)

`opensource/elasticsearch/architecture/` · `opensource/react/architecture/` 의 폴더·README 형식 + `reference/writing/README.md` 문체 + 이 대화의 합의.

## 4. 금지영역 (필수)

기존 `opensource/*` 도구 폴더(elasticsearch·react·nextjs·spring-*) 내용, 현재 브랜치의 미커밋 변경(nextjs·cpp). 커밋·푸시는 별도 지시 전 금지.

## 5. 검증 방법 (필수)

`find opensource/{postgres,redis,nginx}` 로 파일 목록 확인 + 상대 링크 전부 실존 확인(스크립트) + `git status`로 금지영역 무변경 확인.

## 6. stakes (필수)

- 판정: 낮음 — 근거 1줄: 신규 문서 골격, blast radius 없음, 삭제로 즉시 복구.

---

## 7. 자율성

- [x] auto (사용자 확인 대기)
- [ ] lazy

## 8. load-bearing 가정

- 소스 분석이 아닌 도구 지도도 `opensource/<tool>/` 아래 둔다(react·nextjs 선례 — 기여 없이 architecture만 있음).

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1 (2026-09-24, pgvector=postgres 하위)
- [x] 자율성 선택 → MODE=auto
