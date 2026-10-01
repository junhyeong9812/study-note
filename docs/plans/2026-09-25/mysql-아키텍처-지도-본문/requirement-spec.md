# 요구사항 명세서 (requirement-spec)

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "mysql부터 작업 진행하자 mysql 전체 마무리되면 알려줘"
- 앞선 합의: "이후 db-engine과 일치하는 주제쪽에 해당 주제는 db-engine의 어느 부분이라고 적는게 맞고, 이때 도식화랑 시각화 위주로 작업 진행할꺼야" / 오픈소스 기준은 ES 형식으로 통일.
- Q/A: 범위 = 흐름 12 + 온라인 DDL(13번째) + 구조 6. 승인 · auto. 워커 15~20 규모·흐름별 커밋·push 없음 동의.

---

## 1. 목표·대상 (필수)

`opensource/mysql/architecture/` 를 ES 지도(`opensource/elasticsearch/architecture/`)와 같은 완성도로 채운다.
- 흐름 13편(12 + 온라인 DDL `online-ddl`): `flows/<slug>/README.md`(전체 그림 트리·어디에서 쓰이는가·단계·결과가 쓰이는 곳·다루지 않는 것·하위 메서드) + 함수 폴더 `NN_<함수>/README.md`(상위·요지·위치+GitHub 고정 링크·실제 코드·동작 흐름·결과가 쓰이는 곳·다루지 않는 것). 필요한 흐름만 `spi/`.
- 구조 6편: `structure/<slug>/README.md`.
- `architecture/README.md` 흐름 표를 "목록 단계"에서 완성 상태로 갱신(문서 수·링크), `api-index.md` 흐름 링크 연결.
- db-engine 대응: 흐름 README 에 대응 챕터가 있으면 "db-engine 에서는" 박스 1개(해당 챕터 링크 + 같은 문제를 어떻게 단순화했는지). 대응 없는 흐름은 생략.
- 도식화 위주: 모든 함수 문서의 "동작 흐름"은 ASCII 그림(`text` 펜스) 중심, 산문은 그림을 읽히게 하는 만큼만.

## 2. 경계·불변식 (필수)

- 인용하는 코드·줄 번호는 전부 `~/project/mysql-server`(mysql-9.7.2, `008e09c283`)에서 실제로 연 것. 코드 블록은 소스 그대로 복사(생략은 `...` 표시). 확인 못 한 주장은 쓰지 않는다.
- 폴더명: `NN_함수` — `::`·`<T>` 는 `.`·삭제로 치환(예: `02_mtr_t.commit`, `02_Buf_fetch.single_page`).
- 문체: `reference/writing/README.md`(산문·topic sentence·이모지 금지·ASCII 다이어그램 허용). ES 문서 형식을 따른다.
- 소스 레포 읽기 전용. db-engine 레포 읽기 전용.

## 3. 기준소스 (필수)

mysql-server `mysql-9.7.2`(`008e09c2834b98143a8c067d4d225c90953050cf`) · 형식 = ES `flows/engine-write/`·`structure/durability/` · db-engine 대응 = `~/project/db-engine/impl/*.md`(5505edc 기준 구현 설명).

## 4. 금지영역 (필수)

`opensource/mysql/` 밖 파일(이 작업 폴더·측정로그 제외). 다른 워크트리·브랜치. 소스 레포 쓰기. push·PR(별도 지시 전).

## 5. 검증 방법 (필수)

- 생성≠검증: 흐름 묶음마다 작성 워커와 **다른 검증 워커**가 모든 `L줄`·코드 블록을 소스와 기계 대조(스크립트) + 서술 주장 표본 반증. 불일치 0 이 될 때까지 수정.
- 메인: 흐름당 표본 3개 직접 sed 대조 · 링크 실존 스크립트(0 broken) · 이모지·유니코드 기호 grep 0 · mysql-server `git status` clean.

## 6. stakes (필수)

- 판정: 낮음 — 학습 문서, 되돌리기 쉬움. 단 주된 실패모드가 날조(줄 번호·동작 서술)라 검증 워커 대조를 의무로 둔다.

---

## 7. 자율성

- [x] auto
- [ ] lazy

## 8. load-bearing 가정

- 흐름 목록 단계에서 확정한 함수 정의 줄(표본 29개 일치)이 본문 작성의 토대로 충분하다 — 첫 흐름 작성 직후 검증 워커 대조로 조기 실증.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | 파일럿: `connection-thread` 1흐름 작성 → 검증 → 형식 확정 | — | 검증 불일치 0, 메인 형식 확인 |
| 02 | 나머지 흐름 작성 (워커 병렬, 흐름 2개씩) | 01 | 흐름별 검증 불일치 0 |
| 03 | 구조 편 작성 | 02 일부 | 〃 |
| 04 | architecture README·api-index 갱신, 흐름별 커밋 | 02·03 | 링크 0 broken |

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1
- [x] 자율성 선택 → MODE=auto
