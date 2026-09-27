# recv_find_max_checkpoint

상위: [크래시 복구](../README.md)

**복구의 시작점, 곧 가장 최근 체크포인트를 고르는 함수다.** 이름이 같은 두 함수가 겹쳐 있다. 바깥 함수는 모든 redo 파일을 돌고, 안쪽 함수는 파일 하나의 체크포인트 헤더 두 개(HEADER_1, HEADER_2)를 읽어 LSN 이 큰 쪽을 고른다. 체크포인트는 두 헤더에 번갈아 쓰이고(log0constants.h L164-L166 주석), 읽기가 `DB_CORRUPTION` 이면 그 헤더만 건너뛰므로 한쪽이 깨져도 다른 쪽으로 시작할 수 있다. 체크포인트 LSN 이 그 파일의 LSN 범위 밖이면 그 파일을 버린다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L973-L1005 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L973-L1005))

## 실제 코드

파일 하나 안에서 헤더 두 개를 비교한다.

`storage` / `innobase` / `log` / `log0recv.cc` L917-L967 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L917-L967))

```cpp
// log0recv.cc L917-L967
/** Describes location of a single checkpoint. */
struct Log_checkpoint_location {
  /** File containing checkpoint header and checkpoint lsn. */
  Log_file_id m_checkpoint_file_id{0};

  /** Checkpoint header number. */
  Log_checkpoint_header_no m_checkpoint_header_no{};

  /** Checkpoint LSN. */
  lsn_t m_checkpoint_lsn{0};
};

/** Find the latest checkpoint in the given log file.
@param[in]      file_handle     handle for the opened redo log file
@param[out]     checkpoint      the latest checkpoint found (if any)
@return true iff any checkpoint has been found */
[[nodiscard]] static bool recv_find_max_checkpoint(
    log_t &, Log_file_handle &file_handle,
    Log_checkpoint_location &checkpoint) {
  bool found = false;
  checkpoint = {};

  for (auto checkpoint_header_no : {Log_checkpoint_header_no::HEADER_1,
                                    Log_checkpoint_header_no::HEADER_2}) {
    Log_checkpoint_header checkpoint_header;
    const dberr_t err = log_checkpoint_header_read(
        file_handle, checkpoint_header_no, checkpoint_header);
    if (err != DB_SUCCESS) {
      /* Crash if IO error on read */
      ut_a(err == DB_CORRUPTION);
      continue;
    }

    const lsn_t checkpoint_lsn = checkpoint_header.m_checkpoint_lsn;
    if (checkpoint_lsn == 0) {
      continue;
    }

    DBUG_PRINT("ib_log", ("checkpoint at " LSN_PF, checkpoint_lsn));

    if (!found || checkpoint_lsn > checkpoint.m_checkpoint_lsn) {
      ut_a(checkpoint_lsn >= LOG_START_LSN);
      found = true;
      checkpoint.m_checkpoint_file_id = file_handle.file_id();
      checkpoint.m_checkpoint_header_no = checkpoint_header_no;
      checkpoint.m_checkpoint_lsn = checkpoint_lsn;
    }
  }

  return found;
}
```

모든 redo 파일에서 가장 큰 것을 고른다.

`storage` / `innobase` / `log` / `log0recv.cc` L969-L1005 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L969-L1005))

```cpp
// log0recv.cc L969-L1005
/** Find the latest checkpoint (check all existing redo log files).
@param[in,out]  log             redo log
@param[out]     checkpoint      the latest checkpoint found (if any)
@return true iff any checkpoint has been found */
static bool recv_find_max_checkpoint(log_t &log,
                                     Log_checkpoint_location &checkpoint) {
  bool found = false;
  checkpoint = {};

  log_files_for_each(log.m_files, [&](const Log_file &file) {
    auto file_handle = file.open(Log_file_access_mode::READ_ONLY);
    ut_a(file_handle.is_open());

    Log_checkpoint_location checkpoint_in_file;

    if (!recv_find_max_checkpoint(log, file_handle, checkpoint_in_file)) {
      return;
    }

    if (!file.contains(checkpoint_in_file.m_checkpoint_lsn)) {
      const auto file_path = file_handle.file_path();
      ib::error(ER_IB_MSG_RECOVERY_CHECKPOINT_OUTSIDE_LOG_FILE,
                ulonglong{checkpoint_in_file.m_checkpoint_lsn},
                file_path.c_str(), ulonglong{file.m_start_lsn},
                ulonglong{file.m_end_lsn});
      return;
    }

    if (!found ||
        checkpoint_in_file.m_checkpoint_lsn > checkpoint.m_checkpoint_lsn) {
      found = true;
      checkpoint = checkpoint_in_file;
    }
  });

  return found;
}
```

헤더 두 개의 자리와 이름이다.

`storage` / `innobase` / `include` / `log0constants.h` L164-L176 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0constants.h#L164-L176))

```cpp
// log0constants.h L164-L176
/** First checkpoint field in the log header. We write alternately to
the checkpoint fields when we make new checkpoints. This field is only
defined in the first log file. */
constexpr os_offset_t LOG_CHECKPOINT_1 = OS_FILE_LOG_BLOCK_SIZE;

/** Log Encryption information in redo log header. */
constexpr os_offset_t LOG_ENCRYPTION = 2 * OS_FILE_LOG_BLOCK_SIZE;

/** Second checkpoint field in the header of the first log file. */
constexpr os_offset_t LOG_CHECKPOINT_2 = 3 * OS_FILE_LOG_BLOCK_SIZE;

/** Size of log file's header. */
constexpr os_offset_t LOG_FILE_HDR_SIZE = 4 * OS_FILE_LOG_BLOCK_SIZE;
```

`storage` / `innobase` / `include` / `log0types.h` L94-L101 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0types.h#L94-L101))

```cpp
// log0types.h L94-L101
/** Enumerates checkpoint headers in the redo log file. */
enum class Log_checkpoint_header_no : uint32_t {
  /** The first checkpoint header. */
  HEADER_1,

  /** The second checkpoint header. */
  HEADER_2
};
```

## 동작 흐름

```text
 바깥 (L973)
 L978   log_files_for_each(log.m_files, ...)     redo 파일마다
 L979     file.open(READ_ONLY)
 L984     안쪽 recv_find_max_checkpoint           이 파일에서 최댓값
 L988     file.contains(checkpoint_lsn) 이 아니면 에러 로그, 이 파일은 무시
 L998     지금까지의 최댓값보다 크면 교체
 L1004  return found

 안쪽 (L933)
 L939   for HEADER_1, HEADER_2
 L942     log_checkpoint_header_read
 L946     실패는 DB_CORRUPTION 만 허용 (그 밖의 I/O 에러면 ut_a 로 죽는다), continue
 L951     checkpoint_lsn == 0 이면 continue      쓰인 적 없는 헤더
 L957     더 크면 file_id, header_no, lsn 을 기록
```

```text
 redo 파일 하나의 머리 (log0constants.h, 블록 = OS_FILE_LOG_BLOCK_SIZE 512 바이트, os0file.h L192)

 오프셋         내용
 0              파일 헤더 (형식 식별자부터, L178 이하)
 512            LOG_CHECKPOINT_1   (HEADER_1)
 1024           LOG_ENCRYPTION
 1536           LOG_CHECKPOINT_2   (HEADER_2)
 2048           LOG_FILE_HDR_SIZE, 여기서부터 로그 블록

 체크포인트는 다음 헤더 번호를 번갈아 고른다 (log_next_checkpoint_header, log0chkp.cc L415)
 한쪽 헤더가 DB_CORRUPTION 이면 L946-L948 에서 건너뛰고 다른 쪽을 쓴다
```

## 결과가 쓰이는 곳

```text
 Log_checkpoint_location (file_id, header_no, checkpoint_lsn)
      --> [02] 가 같은 헤더를 다시 읽어 확인하고 last_checkpoint_lsn 에 넣는다
      --> [04] 스캔의 시작점. 블록 경계로 내림한 자리부터 읽는다
      --> recv_find_checkpoint_header_no 가 같은 함수를 재사용한다 (L1007)
```

## 다루지 않는 것

체크포인트 헤더의 필드 배치와 체크섬(`log_checkpoint_header_read` 의 역직렬화), redo 파일 이름 규칙과 `log.m_files` 를 만드는 과정, 체크포인트를 쓰는 쪽([페이지 플러시, doublewrite, 체크포인트](../../flush-checkpoint/README.md))은 이 함수의 곁가지라 요약만 했다.
