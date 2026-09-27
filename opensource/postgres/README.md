# PostgreSQL - 동작 구조 분석

이 폴더는 PostgreSQL(C)의 동작 구조를 소스 기준으로 정리하는 자리다. B-Tree 계열 저장 엔진과 WAL, 다중 버전(MVCC), 연결마다 프로세스를 띄우는 모델을 한 코드베이스에서 볼 수 있다. MySQL(InnoDB)과 비교하는 기준점이 된다.

전체 도구 목록과 진행 순서는 [도구 동작 구조 분석 로드맵](../../docs/tool-analysis-roadmap.md)에 있다.

## 읽는 기준

공식 문서는 지도로 쓰고, 주장은 소스로 확인한다. 공식 문서의 설명을 그대로 옮기지 않고, 흐름을 고르는 출발점과 용어의 기준으로 삼는다.

- 소스: [postgres/postgres](https://github.com/postgres/postgres) 태그 `REL_18_6` ([`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7)). GitHub 저장소는 읽기 전용 미러이고, 기여는 pgsql-hackers 메일링 리스트로 한다
- 로컬 클론: `~/project/postgres` - origin = 포크 [junhyeong9812/postgres](https://github.com/junhyeong9812/postgres), upstream = 원본. 얕은 클론(depth 1)으로 기준 태그에 체크아웃해 두었다
- 공식 문서: [PostgreSQL Internals](https://www.postgresql.org/docs/current/internals.html)

## 개념 교차표에서 맡는 칸

로드맵의 개념 교차표 가운데 이 도구가 채우는 축이다.

- 저장 엔진: heap 페이지 + B-Tree 인덱스
- 로그와 내구성: WAL, 체크포인트
- 요청 처리 모델: postmaster가 연결마다 backend 프로세스를 fork
- 복제: WAL 스트리밍 복제

## db-engine 과 잇기

이 폴더는 [db-engine](https://github.com/junhyeong9812/db-engine)(Kotlin으로 처음부터 만든 교육용 DB 엔진, 21단계)과 짝지어 읽을 수 있다. db-engine의 단계 하나를 공부할 때, 같은 문제를 PostgreSQL은 어떻게 푸는지를 여기서 찾는다. 공부 노트는 [project/db-engine](../../project/db-engine/)에 impl 순서대로 있다.

어느 흐름이 어느 챕터와 맞닿는지는 [아키텍처 지도의 흐름 표](architecture/README.md#흐름-열세-편) "db-engine 대응" 칸에 적는다.

## 확장

- [pgvector](pgvector/README.md) - 벡터 타입과 근사 최근접 검색 인덱스. 저장소가 따로라 기준 커밋도 따로 둔다.
