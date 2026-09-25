# MySQL - 동작 구조 분석

이 폴더는 MySQL(C++)의 동작 구조를 소스 기준으로 정리하는 자리다. 범위는 **InnoDB 저장 엔진(`storage/innobase`)을 중심**으로 하고, 서버 계층(파서, 옵티마이저, binlog)은 InnoDB와 만나는 자리만 본다. 테이블 자체가 PK B+Tree인 clustered index, 제자리 갱신과 undo로 만드는 MVCC가 [PostgreSQL](../postgres/README.md)과 정반대 선택이라 두 폴더를 짝지어 읽는다.

전체 도구 목록과 진행 순서는 [도구 동작 구조 분석 로드맵](../../docs/tool-analysis-roadmap.md)에 있다.

## 읽는 기준

공식 문서는 지도로 쓰고, 주장은 소스로 확인한다. 공식 문서의 설명을 그대로 옮기지 않고, 흐름을 고르는 출발점과 용어의 기준으로 삼는다.

- 소스: [mysql/mysql-server](https://github.com/mysql/mysql-server) 태그 `mysql-9.7.2` ([`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf)). 기본 브랜치는 `trunk`
- 로컬 클론: `~/project/mysql-server` - origin = 포크 [junhyeong9812/mysql-server](https://github.com/junhyeong9812/mysql-server), upstream = 원본. 얕은 클론(depth 1)으로 기준 태그에 체크아웃해 두었다
- 공식 문서: [The InnoDB Storage Engine](https://dev.mysql.com/doc/refman/9.7/en/innodb-storage-engine.html)
- Oracle은 소스가 없어서 따로 폴더를 두지 않고, 필요한 자리에 비교 절로만 넣는다

## 개념 교차표에서 맡는 칸

로드맵의 개념 교차표 가운데 이 도구가 채우는 축이다.

- 저장 엔진: clustered index(B+Tree) + 보조 인덱스
- 로그와 내구성: redo log(mtr), undo log, doublewrite buffer
- 복제: binlog, redo와 binlog의 2PC
- 요청 처리 모델: 연결마다 스레드

## db-engine 과 잇기

이 폴더는 [db-engine](https://github.com/junhyeong9812/db-engine)(Kotlin으로 처음부터 만든 교육용 DB 엔진, 21단계)과 짝지어 읽을 수 있다. db-engine의 단계 하나를 공부할 때, 같은 문제를 InnoDB는 어떻게 푸는지를 여기서 찾는다. 공부 노트는 [project/db-engine](../../project/db-engine/)에 impl 순서대로 있다.

어느 흐름이 어느 챕터와 맞닿는지는 [아키텍처 지도의 흐름 표](architecture/README.md#흐름-열두-편) "db-engine 대응" 칸에 적는다.
