# cs/lsm-tree — LSM-Tree와 RUM Conjecture — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 기준 소스는 문서가 아니라 원전(원본 노트·코드)이다.
> ⚠️ **이 정답은 Claude 초안이다(2026-08-20).** 복습 전에 읽지 말 것. 본인 답과 다르면 어느 쪽이 맞는지 원본·코드로 확인하고 고친다.

## 정답

1. B-Tree는 정렬을 즉시 유지한다 — 트리를 타고 내려가 위치를 찾고(랜덤 읽기) 그 페이지를 제자리 수정(랜덤 쓰기), 꽉 차면 분할이 부모로 연쇄된다. LSM은 "정렬을 나중으로 미루자": 랜덤 쓰기를 메모리(MemTable, 정렬 유지가 저렴)에 흡수하고, 꽉 차면 정렬된 상태 그대로 불변 파일(SSTable)로 순차 flush한다. 디스크에는 순차 쓰기만 내려간다.

2. 기존 (42, A)는 어느 SSTable에 그대로 남아 있고, 수정으로 (42, B)가, 삭제로 (42, tombstone)이 MemTable(또는 이후 flush된 새 SSTable)에 추가된다. 읽을 때는 최신 것(tombstone)을 우선하므로 "없음"으로 보인다. 실제 공간 회수와 tombstone 제거는 compaction이 그 key를 가진 SSTable들을 병합할 때 일어난다. 불변 파일 + 최신 우선이라는 점에서 SSD FTL의 invalid 표시 + GC와 같은 구조다.

3. 읽기가 치른다 — 같은 key가 여러 SSTable에 흩어질 수 있어 MemTable → 최신 SSTable → ... 순으로 최악엔 전부 뒤진다(read amplification). Bloom filter는 "이 SSTable에 key가 확실히 없다"를 메모리에서 즉답해 없는 파일을 건너뛰게 한다. 있다고 답하면 실제로 있을 수도 없을 수도 있다(false positive 허용, false negative 없음). 그 외 sparse index(대략 위치), SSTable 내부 정렬(이진 탐색, 범위 스캔 순차)이 보조한다.

4. 쌓인 SSTable을 병합 정렬해 옛 버전과 tombstone을 버리고 공간을 되찾는 백그라운드 작업이라 GC다. 정렬된 파일을 순차로 읽어 순차로 쓰므로 I/O 패턴은 좋지만, 호스트(애플리케이션)가 요청하지 않은 쓰기가 발생하는 write amplification이고 대역폭과 지연을 잠식한다(SSD GC와 같은 성격). Leveled는 레벨마다 10배씩 키워 읽기 빠르고 공간 효율 좋지만 쓰기 증폭이 크고, Size-tiered는 비슷한 크기끼리 합쳐 쓰기 증폭이 적지만 읽기가 느리고 공간을 낭비한다.

5. Read / Update / Memory(공간) 중 둘을 좋게 하면 하나는 나빠진다. B-Tree: 읽기 빠름(경로 하나), 쓰기 랜덤·느림, 페이지 단편화, 배경 작업 적음. LSM: 쓰기 순차·빠름, 읽기는 여러 곳 확인, 압축 잘 됨, compaction 부담. 쓰기 많으면 LSM(RocksDB, Cassandra, HBase, LevelDB, ScyllaDB, InfluxDB), 읽기 중심이면 B-Tree.

6. LSM이 정렬·compaction·Bloom filter를 두는 이유는 key로 조회해야 하기 때문이다. Kafka는 key 조회가 없고 offset으로 위치만 알면 되므로 정렬이 필요 없고, 따라서 그 정렬을 유지하기 위한 compaction도, 여러 파일을 뒤지는 비용을 줄이는 Bloom filter도 필요 없다. "쓰기는 순차로"라는 부분만 취하고 나머지 복잡도를 요구사항 차원에서 제거한 형태다.
