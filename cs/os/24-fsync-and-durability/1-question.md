# os/24-fsync-and-durability — 질문

## 질문

1. (그림) 앱이 쓴 바이트가 비휘발성 매체에 닿기까지 거치는 층을 그려라. `flush()`, `write()`, `fsync()`는 각각 어느 층까지 보장하나?
2. (비교) `fsync`와 `fdatasync`는 무엇이 다른가? 파일 크기가 늘어나는 append에서 `fdatasync`가 메타데이터를 건너뛸 수 있나?
3. (경계) `O_DIRECT`로 열었거나 `sync_file_range`를 불렀다면 내구성이 보장되나? 무엇을 대신 써야 하나?
4. (왜) 새 파일을 만들고 그 파일에 `fsync`까지 했는데 크래시 뒤 파일이 없을 수 있다. 왜인가? 무엇을 더 해야 하나?
5. (그림) "설정 파일 원자적 교체" 네 단계를 적고, 각 단계 사이에 크래시가 나면 `cfg`에 무엇이 남는지 표로 그려라.
6. (예측) 5번에서 (a) 임시 파일 `fsync`를 빼면, (b) 디렉터리 `fsync`를 빼면 각각 어떤 증상이 나나?
7. (장애 진단) fsync가 `EIO`를 냈고 재시도하니 성공했다. 데이터는 안전한가? 커널은 실패한 페이지를 어떻게 처리하나? PostgreSQL은 왜 PANIC을 택했나?
8. (연결) 리눅스 4.13과 4.17의 writeback 오류 보고 변화는 무엇인가? PostgreSQL checkpointer에게 왜 중요했나?
9. (계산·설계) 로컬에서 write+fdatasync 한 번이 약 5 ms였다. 초당 2000건 쓰기 API가 요청마다 fdatasync하면 무슨 일이 생기나? fsync를 끄지 않고 푸는 방법은?
10. (연결) Java `FileChannel.force(false)`와 `force(true)`는 각각 어떤 시스템 콜이 되나? Node의 `fs.writeFileSync`는 내구성을 보장하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
