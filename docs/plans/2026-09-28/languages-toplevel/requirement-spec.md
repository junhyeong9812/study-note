# 요구사항 명세서 (requirement-spec)

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "그리고 언어는 외부로 빼는 작업까지도 진행하자." / 추가: "위 작업 후 스터디 노트의 브랜치들 전부 main에 머지해서 정리좀 해놓자. auto로 진행해줘"
- Q/A
  - 이동 위치: **최상위 `languages/`**. 최상위 `reference/`는 이미 작성법 문서 폴더라 쓰지 않는다.
  - 이동 범위: **`cs/foundations/languages/` 폴더 통째로**(syntax, 언어-특성, README, c-cpp-csharp.md).
    - 언어-특성을 cs language/19로 병합하는 일은 cs 재편 때 새로 작성한다.
  - 함께 옮길 것: **web-api(DOM API 118파일)**, **python-basics**.
- 앞선 결정: cs는 지식 본문만 둔다. 채팅 기록 경로 마이그레이션은 작업 C에서 한다(path-map 산출).

---

## 1. 목표·대상 (필수)

study-note에서 세 가지를 옮기고, 링크·경로 표기·색인을 교정한 뒤 커밋하면 끝이다.

| 옮기는 것 | 새 위치 | 비고 |
|---|---|---|
| `cs/foundations/languages/**` (2,023파일) | `languages/**` | 구조 그대로 |
| `cs/foundations/web-api/**` (118파일) | `languages/web-api/**` | 브라우저 호스트 API라 JS 곁에 둔다. 최상위 수를 늘리지 않는다. |
| `cs/foundations/python-basics/**` | `languages/python/basics/**` | — |

## 2. 경계·불변식 (필수)

- **I1 파일 보존**: 이동 대상 파일 집합과 새 위치 파일 집합이 1:1로 대응한다. 본문 변경은 링크와 경로 표기 교정뿐이다.
- **I2 링크 무손상**: 저장소 전체에서 새로 깨지는 상대 링크가 0이다. 비교 기준은 이동 전 기준선이다.
- **I3 잔존 0**: 제외 범위 밖에서 옛 경로 문자열이 0건이어야 한다.
  - 대상 문자열: `foundations/languages`, `foundations/web-api`, `foundations/python-basics`
  - 제외 범위: `docs/plans/**`, `history/**`
- **I4 배포 트리 규칙**: 리프 폴더에는 md만 둔다. `languages/python/`이 `syntax/`와 `basics/`를 갖는 형태가 규칙을 지켜야 한다.
- **I5 커밋 범위**: 이 작업 경로만 커밋한다. 기존 미커밋분(measurement-log, NEXT.md, 09-26 폴더, roadmap 폴더)은 섞지 않는다.

## 3. 기준소스 (필수)

- study-note 현 HEAD `ebe32576`의 세 폴더 트리.
- 이동 전 링크 기준선. linkcheck.py로 측정한다.

## 4. 금지영역 (필수)

- 언어 노트 본문 재작성과 언어-특성의 cs 병합. 이 둘은 cs 재편 작업에서 한다.
- `cs/foundations`의 나머지 폴더와 그 밖의 cs 재편.
- 하네스와 deploy-study-note. 이번 작업에는 옛 경로 참조가 없다(grep 0건).
- push. study-note push는 별도로 확인받는다.
- `docs/plans/**`·`history/**` 기록의 옛 경로 표기.

## 5. 검증 방법 (필수)

- **V1**: 스테이징 후 `git diff --cached -M --name-status`에서 R이 이동 대상 파일 수와 같고, 추가·삭제는 작업 폴더 문서뿐이다.
- **V2**: linkcheck 전후 비교로 새로 깨진 링크가 0이다.
- **V3**: 옛 경로 grep 결과가 제외 범위 밖에서 0건이다.
- **V4**: `languages/` 아래 리프 폴더에 비-md 파일이 0이다. 리프가 아닌 폴더에 md와 하위 폴더가 섞인 곳을 목록으로 뽑아 이동 전 구조와 같은지 확인한다.
- **V5**: `path-map.tsv`(옛 경로 → 새 경로)의 행 수가 R 건수와 같다. 작업 C의 입력이다.
- **V6 리뷰**: 듀얼 1패스(Opus 워커 ∥ codex). 중간 stakes이므로 채택 finding을 고친 뒤 post-fix 타깃 재점검을 1회 한다.

## 6. stakes (필수)

- 판정: **중간**
- 근거
  - 파일 2,142개를 옮긴다. 배포 사이트 URL이 바뀌고 채팅 기록 키도 바뀐다(작업 C로 분리).
  - git으로 되돌릴 수 있다. 정책 파일은 바뀌지 않는다.
  - 방식은 직전 issue 이동과 같다. 같은 도구로 기계적으로 치환한다.
- 적용: 외부 검색은 불필요하다(내부 경로). 리뷰는 듀얼 1패스와 post-fix 재점검 1회다.

---

## 7. 자율성 (모드)

- [ ] auto (기본 권장)
- [ ] lazy

## 8. load-bearing 가정

- **A1**: 직전 작업의 relink 방식이 폴더 3개를 동시에 옮길 때도 맞는다. 방식은 "옛 소스 위치 기준으로 해소한 대상을 다시 매핑하는 것"이다. 두 방향을 모두 교정해야 한다.
  - 이동하는 파일에서 밖으로 나가는 링크: 깊이가 바뀐다. `languages/`는 −2, `web-api`는 −1, `python-basics`는 0.
  - 밖에서 이동하는 파일로 들어오는 링크: `cs/index.md`, `foundations/index.md` 등.
  - 착수 직후 기준선과 dry-run으로 검증한다.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | 링크 기준선, relink 일반화(여러 매핑·저장소 전체 대상), dry-run | — | 변경 예정 링크 수 기록 |
| 02 | `git mv` 3건과 relink, 경로 표기 치환 | 01 | V1·V2·V3·V4 |
| 03 | 색인 갱신: 루트 index·README에 `languages/` 입구, `cs/index.md`·`cs/foundations/index.md`의 해당 행을 새 위치로, `languages/README.md` 상단 1행 위치 안내 | 02 | V2 |
| 04 | 듀얼 리뷰, 수정, 재점검 | 03 | 채택 전부 fixed, 재점검 clean |
| 05 | 커밋(경로 지정) + log 마감, path-map | 04 | V5 · `git show --stat` |
| 06 | (사용자 추가 2026-09-28) study-note 로컬 브랜치 전부 main에 병합·정리 — 병합 전 브랜치 목록·main 대비 상태 확인, 충돌 시 멈추고 보고, push는 별도 확인 | 05 | 모든 브랜치가 main에 포함(`git branch --no-merged main` 빈 결과) |

---

## 재합의 (2026-09-28)

- 순서 변경 합의: **통합 먼저 → 언어 이동**. main이 현 브랜치보다 402커밋 앞서 있고 언어 문서 482개가 추가돼 있어, 이동을 먼저 하면 병합분의 링크가 깨지기 때문이다.
  - 흐름: main 기준 통합 브랜치 `docs/integrate-2026-09-28` → 모든 미병합 브랜치 병합 → 그 위에서 task 01~05 → main ff.
- 진행 중 브랜치(`archive/2026-09-28`, `docs/mysql-architecture`)는 **커밋된 것만** 병합한다. 워크트리·미커밋 파일·브랜치는 삭제하지 않는다.
- push: **검증 통과 시 origin main push까지** 진행한다(사용자 지시). 네이티브 승인이 필요하다.
- 기존 미커밋 기록(measurement-log, NEXT.md, 09-26 폴더, roadmap)은 통합 전에 별도 docs 커밋으로 확정한다. 이동 커밋과는 분리한다.

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1 (2026-09-28)
- [x] 자율성 선택 → auto
