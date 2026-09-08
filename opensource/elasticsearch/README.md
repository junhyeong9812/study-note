# elasticsearch — 업스트림 기여 학습 아카이브

이 폴더는 Elasticsearch 업스트림 기여(2026-06~) 과정에서 작성한 학습 문서의 아카이브다.
원본은 작업 repo(elasticsearch fork)의 `docs/plans/`에 작업 기록 형태로 남아 있고,
2026-09-08에 PR 4건(머지 3) 시점의 상태로 이곳에 학습 문서로 다시 썼다. **이후의 새
기여 문서는 이 폴더에 직접 작성한다.**

네 건은 우연히 모인 것이 아니라 **하나의 렌즈로 찾은 같은 계열의 결함**이다. 렌즈는
"집계 빌더가 직렬화하는 필드 목록과 `equals`/`hashCode`가 비교하는 필드 목록이 일치하는가"
이고, 그 렌즈로 세 건(정방향 - 직렬화되는데 비교에서 빠짐)과 한 건(역방향 - 비교에는
있는데 직렬화가 안 됨)을 찾았다. 그래서 이 아카이브를 읽는 순서는 PR 번호순보다
**개념 문서를 먼저 읽고 PR로 내려가는** 쪽이 낫다.

구성은 두 갈래다. `prs/`는 PR 하나당 주제 폴더 하나로, 각 폴더의 문서 구성은 자료가
받쳐 주는 만큼만 둔다(각 README의 0절에 그 폴더의 구성이 적혀 있다). `concepts/`는
기여 중 배운 개념을 단일 문서 주제(폴더명 = md 파일명)로 담는다.

## 작성 규칙 (이 폴더의 계약)

- 배포 트리 규칙: 주제(리프) = 하위 폴더 없이 md만 있는 폴더. PR 주제 폴더 안에 하위
  폴더를 만들지 않는다. 단일 문서 개념은 `<슬러그>/<슬러그>.md`.
- 폴더명은 영문 슬러그: PR은 `<번호>-<내용-kebab>`, 개념은 내용 kebab.
- 문체는 study-note 작성 방법론(`reference/writing/README.md`)을 따른다: 산문, 절마다
  topic sentence, 결론 앞, 표는 고정 차원 비교 + lead-in, 이모지·유니코드 특수기호 금지
  (ASCII 다이어그램 허용).
- 인용하는 file:line은 별도 표시가 없으면 **수정이 반영된 뒤**의 좌표다. 수정 전 코드를
  인용할 때는 "수정 전"이라고 표시한다.
- 새 PR마다 문서를 채우고 아래 대장과 [prs/index.md](prs/index.md)에 한 줄을 더한다.

## PR 대장

| 폴더 | 상태 | 한 줄 주제 |
|---|---|---|
| [prs/151152-timeseries-size-equality](prs/151152-timeseries-size-equality/) | 머지 2026-06-19 (`3ba1d47ecf1`, main, v9.5.0) | time_series 빌더가 직렬화되는 size를 동등성에서 빼놓았다 |
| [prs/151154-matrixstats-missingmap-multivaluemode](prs/151154-matrixstats-missingmap-multivaluemode/) | 머지 2026-06-19 (`6e5be615e88`, main, v9.5.0) | matrix_stats가 죽은 필드를 비교하고 자식 필드를 상속으로 놓쳤다 |
| [prs/151156-roundinginfo-serialized-fields](prs/151156-roundinginfo-serialized-fields/) | 머지 2026-06-19 (`5130e384dd8`, main, v9.5.0) | RoundingInfo가 다섯을 싣고 셋만 비교했다 |
| [prs/151796-variable-width-histogram-shard-size](prs/151796-variable-width-histogram-shard-size/) | 리뷰 대기 (2026-06-20 제출, v9.6.0 라벨) | variable_width_histogram의 shard_size·initial_buffer가 데이터 노드에 안 갔다 |

머지 3건은 모두 이슈를 먼저 열고(#151151·#151153·#151155) 그것을 닫는 PR로 올렸으며,
메인테이너 swallez가 리뷰했다. 리뷰 대기 중인 #151796은 이슈 #151795를 닫는다. 상태는
2026-09-08 기준이고, 이후 변동은 각 폴더 README와 이 표를 함께 갱신한다.

## 이 프로젝트에서 배운 기여 절차

Spring과 다른 점만 적는다. 자세한 맥락은 각 PR README의 상태 절에 있다.

- **이슈를 먼저 연다.** `CONTRIBUTING.md`가 기능·버그픽스 모두 이슈 선행을 권장한다.
  CI가 강제하지는 않지만 네 건 모두 이 경로를 따랐다.
- **community PR은 changelog YAML을 직접 넣어야 한다.** `CONTRIBUTING.md`에는 자동
  생성이라고 적혀 있지만 실제 CI의 `Check changelog`는 `docs/changelog/<PR번호>.yaml`을
  요구한다. PR 번호는 PR을 만들어야 나오므로 순서가 **PR 생성 -> changelog 커밋 추가**다.
- **빨간 체크가 다 내 책임은 아니다.** `Check labels`·`Check assignee`는 Elastic triage
  팀 전용이라 외부 기여자는 손댈 수 없고, CI 워크플로우 실행도 메인테이너의 수동 승인이
  필요하다.
- **PR 오픈 후에는 amend·force-push를 하지 않는다.** 리뷰 대응은 새 커밋으로 쌓는다.
- **전송 버전(TransportVersion)을 건드리는 PR은 최신 main에서 브랜치를 딴다.**
  `upper_bounds/<minor>.csv`가 거의 반드시 충돌하고, 해소는 손이 아니라
  `./gradlew resolveTransportVersionConflict`로 한다.
