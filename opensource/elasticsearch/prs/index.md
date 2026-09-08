# prs 인덱스

PR별 주제 폴더 목록이다. 네 건 모두 "직렬화되는 필드와 equals/hashCode가 일치하는가"라는
한 렌즈에서 나왔고, 방향(정방향·역방향)과 문서 구성이 폴더마다 다르다. 상태는 2026-09-08
기준이며 갱신은 각 폴더 README와 상위 README 대장에서 한다.

| 주제 | 상태 | 방향 | 구성 | 한 줄 주제 |
|------|------|------|------|------|
| [151152-timeseries-size-equality](151152-timeseries-size-equality/) | 머지 2026-06-19 (`3ba1d47ecf1`) | 정방향 | README·tests | time_series의 size가 동등성에서 누락 |
| [151154-matrixstats-missingmap-multivaluemode](151154-matrixstats-missingmap-multivaluemode/) | 머지 2026-06-19 (`6e5be615e88`) | 정방향 | README·tests·structure·analysis | 죽은 missing을 비교, multiValueMode는 상속으로 누락 |
| [151156-roundinginfo-serialized-fields](151156-roundinginfo-serialized-fields/) | 머지 2026-06-19 (`5130e384dd8`) | 정방향 | README·tests·analysis | RoundingInfo가 다섯 중 셋만 비교 |
| [151796-variable-width-histogram-shard-size](151796-variable-width-histogram-shard-size/) | 리뷰 대기 (2026-06-20 제출) | 역방향 | README·tests·structure·analysis | shard_size·initial_buffer가 wire·clone·XContent에서 누락 |

구성 열이 폴더마다 다른 것은 자료가 받쳐 주는 만큼만 문서를 두었기 때문이다. 착수 분석은 151154·151156·151796의 경우 별도 analysis.md로 두었고, 151152는 분량상 README가 겸한다. 상세는 각 README의 0절에
적혀 있다. 리뷰 대응 기록이 있는 두 건(#151152·#151154)은 README에 리뷰 절이 있다.
