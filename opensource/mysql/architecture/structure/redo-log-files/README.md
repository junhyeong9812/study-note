# redo 로그 파일과 mlog 타입

상위: [MySQL 아키텍처 지도](../../README.md)

redo 로그는 데이터 디렉터리 아래 `#innodb_redo/` 에 **`#ib_redo<번호>` 파일 여러 개**로 놓인다(8.0.30 형식). 파일 하나는 2048바이트 헤더(512바이트 블록 네 개: 파일 헤더, 체크포인트 1, 암호화, 체크포인트 2) 뒤에 512바이트 데이터 블록이 이어진 모양이다. 데이터 블록은 다시 12바이트 헤더, 496바이트 본문, 4바이트 체크섬 트레일러로 나뉜다. LSN 은 이 블록 헤더와 트레일러까지 센 바이트 위치라서, 파일 안 오프셋은 `2048 + (lsn - 파일 시작 lsn)` 한 줄로 나온다. 본문에 쌓이는 것은 mtr 이 만든 레코드들이고, 레코드 하나는 `[타입 1바이트][space_id][page_no][타입별 본문]` 모양이다. 레코드를 만들고 log buffer 로 옮기는 동작은 [mini-transaction과 redo 기록](../../flows/mtr-redo/README.md)에, 체크포인트 블록을 쓰는 동작은 [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md)에, 읽어서 다시 적용하는 동작은 [크래시 복구](../../flows/crash-recovery/README.md)에 있다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 <datadir>/#innodb_redo/                LOG_DIRECTORY_NAME
 |
 +-- #ib_redo5          사용 중, 꽉 참   [start_lsn, end_lsn)  (체크포인트가 지나가면 소비됨)
 +-- #ib_redo6          사용 중, 쓰는 중  <- log.m_current_file
 +-- #ib_redo7_tmp      예비 파일         다음에 쓸 차례가 오면 _tmp 를 떼고 이름을 바꾼다
 +-- #ib_redo8_tmp      예비 파일
 ...

 목표 파일 수 LOG_N_FILES = 32.  innodb_redo_log_capacity (8MB ~ 512GB) 를 나눠 가진다
 번호는 계속 올라간다 (Log_file_id). 소비된 파일은 _tmp 로 표시되고 다음 번호로 이름을 바꿔
 예비로 재사용된다 (log_files_governor.cc L960-L968)
```

```text
 파일 하나 (#ib_redoN)

 offset
      0  +--------------------------------------+  블록 0  파일 헤더
         | format 4 | log_uuid 4 | start_lsn 8  |
         | creator 32 ("MySQL " + 버전)         |
         | flags 4                              |
         | ...                       | crc32 4  |
    512  +--------------------------------------+  블록 1  LOG_CHECKPOINT_1
         | (8) checkpoint_lsn 8 ...  | crc32 4  |
   1024  +--------------------------------------+  블록 2  LOG_ENCRYPTION (암호화 키 정보)
   1536  +--------------------------------------+  블록 3  LOG_CHECKPOINT_2
         | (8) checkpoint_lsn 8 ...  | crc32 4  |
   2048  +--------------------------------------+  LOG_FILE_HDR_SIZE, 여기부터 데이터
         | 데이터 블록  lsn = start_lsn         |
   2560  +--------------------------------------+
         | 데이터 블록  lsn = start_lsn + 512   |
         | ...                                  |
         +--------------------------------------+  파일 끝 = end_lsn 의 자리

 lsn -> 파일 오프셋    LOG_FILE_HDR_SIZE + (lsn - m_start_lsn)     (log0types.h L532-L534)
 start_lsn, end_lsn 은 늘 512 의 배수                             (log0types.h L506-L507)
```

```text
 데이터 블록 하나 (OS_FILE_LOG_BLOCK_SIZE = 512)

 offset  size  field                       뜻
 ------  ----  --------------------------  ---------------------------------------
      0     4  LOG_BLOCK_HDR_NO            블록 번호 = 1 + (lsn / 512) % 2^30
      4     2  LOG_BLOCK_HDR_DATA_LEN      이 블록에 찬 바이트 수 (헤더 포함), 최상위 비트 = 암호화
      6     2  LOG_BLOCK_FIRST_REC_GROUP   이 블록에서 처음 시작하는 mtr 묶음의 오프셋 (없으면 0)
      8     4  LOG_BLOCK_EPOCH_NO          블록 번호가 몇 바퀴 돌았나
     12   496  본문                        mtr 레코드 바이트가 블록 경계를 무시하고 흘러간다
    508     4  LOG_BLOCK_CHECKSUM          앞 508바이트의 crc32

 mtr 하나의 레코드 묶음은 여러 블록에 걸칠 수 있다
 복구는 FIRST_REC_GROUP 덕분에 블록 중간에서도 묶음의 시작을 찾는다
```

## sn 과 lsn

mtr 이 log buffer 에 자리를 예약할 때 쓰는 카운터는 sn 이고, 파일과 페이지에 적히는 값은 lsn 이다. sn 은 **본문 바이트만** 센다. lsn 은 블록 헤더와 트레일러까지 센다. 둘 사이는 산술로만 바뀐다.

```text
 sn -> lsn (log_translate_sn_to_lsn, log0log.h L85-L88)

 lsn = sn / 496 * 512  +  sn % 496  +  12

 예  sn = 1000
     1000 / 496 = 2 블록 -> 1024
     1000 % 496 = 8      -> 블록 안 본문 8번째 바이트
     + 헤더 12           -> lsn 1044  (블록 안 오프셋 20)

 lsn 은 늘 어떤 블록의 본문을 가리킨다 (블록 안 오프셋 12 ~ 507)
 첫 lsn 은 LOG_START_LSN = 16 * 512 = 8192
```

`storage` / `innobase` / `include` / `log0log.h` L73-L88 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0log.h#L73-L88))

```cpp
// log0log.h L73-L88
/** Calculates lsn value for given sn value. Sequence of sn values
enumerate all data bytes in the redo log. Sequence of lsn values
enumerate all data bytes and bytes used for headers and footers
of all log blocks in the redo log. For every LOG_BLOCK_DATA_SIZE
bytes of data we have OS_FILE_LOG_BLOCK_SIZE bytes in the redo log.
NOTE that LOG_BLOCK_DATA_SIZE + LOG_BLOCK_HDR_SIZE + LOG_BLOCK_TRL_SIZE
== OS_FILE_LOG_BLOCK_SIZE. The calculated lsn value will always point
to some data byte (will be % OS_FILE_LOG_BLOCK_SIZE >= LOG_BLOCK_HDR_SIZE,
and < OS_FILE_LOG_BLOCK_SIZE - LOG_BLOCK_TRL_SIZE).

@param[in]      sn      sn value
@return lsn value for the provided sn value */
constexpr inline lsn_t log_translate_sn_to_lsn(sn_t sn) {
  return sn / LOG_BLOCK_DATA_SIZE * OS_FILE_LOG_BLOCK_SIZE +
         sn % LOG_BLOCK_DATA_SIZE + LOG_BLOCK_HDR_SIZE;
}
```

`mtr-redo` 의 `log_buffer_reserve` 가 `sn.fetch_add(len)` 로 범위를 받고 이 함수로 lsn 을 만든다([log_buffer_reserve](../../flows/mtr-redo/05_log_buffer_reserve/README.md)). log buffer 자체가 이미 블록 모양이어서, `log_buffer_write` 는 복사하면서 블록 헤더 12바이트와 트레일러 4바이트 자리를 건너뛴다([log_buffer_write](../../flows/mtr-redo/06_log_buffer_write/README.md)).

## 파일 이름과 헤더

파일 이름은 접두사와 번호를 붙여 만들고, 예비 파일은 뒤에 `_tmp` 를 붙인다.

`storage` / `innobase` / `include` / `log0constants.h` L72-L107 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0constants.h#L72-L107))

```cpp
// log0constants.h L72-L107
/** Name of subdirectory which contains redo log files. */
constexpr const char *const LOG_DIRECTORY_NAME = "#innodb_redo";

/** Prefix of log file name in the current redo format. */
constexpr const char *const LOG_FILE_BASE_NAME = "#ib_redo";

/** Maximum length of log file name, computed as: base name length(8)
+ length for decimal digits(22). */
constexpr uint32_t LOG_FILE_NAME_MAX_LENGTH = 8 + 22;

/** Targeted number of log files. */
constexpr size_t LOG_N_FILES = 32;

/** Determines maximum downsize for maximum redo file size during resize.
If maximum file size is 8G, then 1.0/8 means, that InnoDB needs to first
achieve maximum file size equal to 1G before targeting even lower values. */
constexpr double LOG_N_FILES_MAX_DOWNSIZE_RATIO = 1.0 / 8;

/** Minimum size of single log file, expressed in bytes. */
constexpr os_offset_t LOG_FILE_MIN_SIZE = 64 * 1024;

/** Minimum allowed value for innodb_redo_log_capacity. */
constexpr os_offset_t LOG_CAPACITY_MIN = 8 * 1024 * 1024; /* 8M */

/** Maximum allowed value for innodb_redo_log_capacity. */
constexpr os_offset_t LOG_CAPACITY_MAX = 512ull * 1024 * 1024 * 1024; /* 512G */

static_assert(LOG_CAPACITY_MAX % LOG_N_FILES == 0,
              "A valid log size can be created with LOG_N_FILES");

/** Maximum size of a log file, expressed in bytes. */
constexpr os_offset_t LOG_FILE_MAX_SIZE = LOG_CAPACITY_MAX / LOG_N_FILES;

/** Id of the first redo log file (assigned to the first log file
when new data directory is being initialized). */
constexpr Log_file_id LOG_FIRST_FILE_ID = 0;
```

`storage` / `innobase` / `log` / `log0files_io.cc` L716-L737 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0files_io.cc#L716-L737))

```cpp
// log0files_io.cc L716-L737
std::string log_file_name(const Log_files_context &ctx, Log_file_id file_id) {
  switch (ctx.m_files_ruleset) {
    case Log_files_ruleset::CURRENT:
      break;
    case Log_files_ruleset::PRE_8_0_30:
      return log_pre_8_0_30::file_name(file_id);
    default:
      ut_error;
  }
  std::ostringstream str;
  str << LOG_FILE_BASE_NAME << file_id;
  return str.str();
}

std::string log_file_path(const Log_files_context &ctx, Log_file_id file_id) {
  return log_directory_path(ctx) + log_file_name(ctx, file_id);
}

std::string log_file_path_for_unused_file(const Log_files_context &ctx,
                                          Log_file_id file_id) {
  return log_file_path(ctx, file_id) + "_tmp";
}
```

파일 헤더 블록과 체크포인트 블록, 데이터 블록의 오프셋이 한곳에 모여 있다. 체크포인트 블록에는 8.0.30 형식부터 `checkpoint_lsn` 하나만 남았다.

`storage` / `innobase` / `include` / `log0constants.h` L147-L312 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0constants.h#L147-L312))

```cpp
// log0constants.h L147-L312
/* General constants describing the log file format. */

/** Magic value to use instead of log checksums when they are disabled. */
constexpr uint32_t LOG_NO_CHECKSUM_MAGIC = 0xDEADBEEFUL;

/** The counting of lsn's starts from this value: this must be non-zero. */
constexpr lsn_t LOG_START_LSN = 16 * OS_FILE_LOG_BLOCK_SIZE;

/** Maximum possible lsn value is slightly higher than the maximum sn value,
because lsn sequence enumerates also bytes used for headers and footers of
all log blocks. However, still 64-bits are enough to represent the maximum
lsn value, because only 63 bits are used to represent sn value. */
constexpr lsn_t LSN_MAX = (1ULL << 63) - 1;

/** The sn bit to express locked state. */
constexpr sn_t SN_LOCKED = 1ULL << 63;

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

// ... (L178-L238 생략: 파일 헤더 필드 (format 0, log_uuid 4, start_lsn 8, creator 16..47, flags 48. 위 그림 참고))
constexpr os_offset_t LOG_HEADER_SIZE = LOG_HEADER_FLAGS + 4;

/* Offsets inside the checkpoint pages since 8.0.30 redo format. */

/** Checkpoint lsn. Recovery starts from this lsn and searches for the first
log record group that starts since then. */
constexpr os_offset_t LOG_CHECKPOINT_LSN = 8;

/* Offsets used in a log block header. */

/** Offset to hdr_no, which is a log block number and must be > 0.
It is allowed to wrap around at LOG_BLOCK_MAX_NO.
In older versions of MySQL the highest bit (LOG_BLOCK_FLUSH_BIT_MASK) of hdr_no
is set to 1, if this is the first block in a call to write. */
constexpr uint32_t LOG_BLOCK_HDR_NO = 0;

/** Mask used to get the highest bit in the hdr_no field.
In the older MySQL versions this bit was used to mark first block in a write.*/
constexpr uint32_t LOG_BLOCK_FLUSH_BIT_MASK = 0x80000000UL;

/** Maximum allowed block's number (stored in hdr_no) increased by 1. */
constexpr uint32_t LOG_BLOCK_MAX_NO = 0x3FFFFFFFUL + 1;

/** Offset to number of bytes written to this block (also header bytes). */
constexpr uint32_t LOG_BLOCK_HDR_DATA_LEN = 4;

/** Mask used to get the highest bit in the data len field,
this bit is to indicate if this block is encrypted or not. */
constexpr uint32_t LOG_BLOCK_ENCRYPT_BIT_MASK = 0x8000UL;

/** Offset to "first_rec_group offset" stored in the log block header.

The first_rec_group offset is an offset of the first start of mtr log
record group in this log block (0 if no mtr starts in that log block).

If the value is the same as LOG_BLOCK_HDR_DATA_LEN, it means that the
first rec group has not yet been concatenated to this log block, but if
it was supposed to be appended, it would start at this offset.

An archive recovery can start parsing the log records starting from this
offset in this log block, if value is not 0. */
constexpr uint32_t LOG_BLOCK_FIRST_REC_GROUP = 6;

/** Offset to epoch_no stored in this log block. The epoch_no is computed
as the number of epochs passed by the value of start_lsn of the log block.
Single epoch is defined as range of lsn values containing LOG_BLOCK_MAX_NO
log blocks, each of OS_FILE_LOG_BLOCK_SIZE bytes. Note, that hdr_no stored
in header of log block at offset=LOG_BLOCK_HDR_NO, can address the block
within a given epoch, whereas epoch_no stored at offset=LOG_BLOCK_EPOCH_NO
is the number of full epochs that were before. The pair <epoch_no, hdr_no>
would be the absolute block number, so the epoch_no helps in discovery of
unexpected end of the log during recovery in similar way as hdr_no does.
@remarks The epoch_no for block that starts at start_lsn is computed as
the start_lsn divided by OS_FILE_LOG_BLOCK_SIZE, and then divided by the
LOG_BLOCK_MAX_NO. */
constexpr uint32_t LOG_BLOCK_EPOCH_NO = 8;

/** Size of the log block's header in bytes. */
constexpr uint32_t LOG_BLOCK_HDR_SIZE = 12;

/* Offsets used in a log block's footer (refer to the end of the block). */

/** 4 byte checksum of the log block contents. In InnoDB versions < 3.23.52
this did not contain the checksum, but the same value as .._HDR_NO. */
constexpr uint32_t LOG_BLOCK_CHECKSUM = 4;

/** Size of the log block footer (trailer) in bytes. */
constexpr uint32_t LOG_BLOCK_TRL_SIZE = 4;

static_assert(LOG_BLOCK_HDR_SIZE + LOG_BLOCK_TRL_SIZE < OS_FILE_LOG_BLOCK_SIZE,
              "Header + footer cannot be larger than the whole log block.");

/** Size of log block's data fragment (where actual data is stored). */
constexpr uint32_t LOG_BLOCK_DATA_SIZE =
```

헤더 블록을 실제로 쓰는 코드다. 모든 512바이트 헤더 블록은 0 으로 지운 뒤 필드를 쓰고, 마지막 4바이트에 앞 508바이트의 crc32 를 넣는다.

`storage` / `innobase` / `log` / `log0files_io.cc` L453-L470 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0files_io.cc#L453-L470))

```cpp
// log0files_io.cc L453-L470
void log_file_header_serialize(const Log_file_header &header, byte *buf) {
  log_file_header_validate(header);

  std::memset(buf, 0x00, OS_FILE_LOG_BLOCK_SIZE);

  mach_write_to_4(buf + LOG_HEADER_FORMAT, header.m_format);

  mach_write_to_8(buf + LOG_HEADER_START_LSN, header.m_start_lsn);

  strncpy(reinterpret_cast<char *>(buf) + LOG_HEADER_CREATOR,
          header.m_creator_name.c_str(), LOG_HEADER_CREATOR_MAX_LENGTH);

  mach_write_to_4(buf + LOG_HEADER_FLAGS, header.m_log_flags);

  mach_write_to_4(buf + LOG_HEADER_LOG_UUID, header.m_log_uuid);

  log_block_set_checksum(buf, log_block_calc_checksum_crc32(buf));
}
```

`storage` / `innobase` / `log` / `log0files_io.cc` L576-L611 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0files_io.cc#L576-L611))

```cpp
// log0files_io.cc L576-L611
void log_checkpoint_header_serialize(const Log_checkpoint_header &header,
                                     byte *buf) {
  memset(buf, 0x00, OS_FILE_LOG_BLOCK_SIZE);

  mach_write_to_8(buf + LOG_CHECKPOINT_LSN, header.m_checkpoint_lsn);

  log_block_set_checksum(buf, log_block_calc_checksum_crc32(buf));
}

bool log_checkpoint_header_deserialize(const byte *buf,
                                       Log_checkpoint_header &header) {
  header.m_checkpoint_lsn = mach_read_from_8(buf + LOG_CHECKPOINT_LSN);

  return log_header_checksum_is_ok(buf);
}

// ... (L592-L600 생략: 헤더 구조체를 받는 쓰기 래퍼)
static os_offset_t log_checkpoint_header_offset(
    Log_checkpoint_header_no checkpoint_header_no) {
  switch (checkpoint_header_no) {
    case Log_checkpoint_header_no::HEADER_1:
      return LOG_CHECKPOINT_1;
    case Log_checkpoint_header_no::HEADER_2:
      return LOG_CHECKPOINT_2;
    default:
      ut_error;
  }
}
```

LSN 을 파일 오프셋으로 바꾸는 것은 `Log_file` 의 정적 함수 한 줄이다.

`storage` / `innobase` / `include` / `log0types.h` L518-L534 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0types.h#L518-L534))

```cpp
// log0types.h L518-L534
  /** Provides offset for the given LSN (from the beginning of the log file).
  @param[in]  lsn   lsn to locate (must exist in the file)
  @return offset from the beginning of the file for the given lsn */
  os_offset_t offset(lsn_t lsn) const {
    lsn_validate();
    ut_a(contains(lsn) || lsn == m_end_lsn);
    return offset(lsn, m_start_lsn);
  }

  /** Provides offset for the given LSN and log file with the given start_lsn
  (offset from the beginning of the log file).
  @param[in]  lsn              lsn to locate (must be >= file_start_lsn)
  @param[in]  file_start_lsn   start lsn of the log file
  @return offset from the beginning of the file for the given lsn */
  static os_offset_t offset(lsn_t lsn, lsn_t file_start_lsn) {
    return LOG_FILE_HDR_SIZE + (lsn - file_start_lsn);
  }
```

## 체크포인트 블록 두 개

체크포인트를 쓸 때마다 블록 1 과 블록 3 을 번갈아 쓴다. 쓰다가 끊겨 한쪽이 깨져도 다른 쪽에 직전 체크포인트가 남는다. 체크포인트 블록은 체크포인트 LSN 이 들어 있는 파일에 쓰인다(`log.m_files.find(next_checkpoint_lsn)`, log0chkp.cc L344).

```text
 체크포인트 갱신 (log_files_next_checkpoint -> log_files_write_checkpoint_low)

  1회째   HEADER_1 (offset 512)  <- checkpoint_lsn = A
  2회째   HEADER_2 (offset 1536) <- checkpoint_lsn = B
  3회째   HEADER_1 (offset 512)  <- checkpoint_lsn = C     (log_next_checkpoint_header)
  ...
  쓴 뒤 fsync, 그 다음에 log.last_checkpoint_lsn 을 올린다 (log0chkp.cc L375-L394)

 복구 때 (recv_find_max_checkpoint, log0recv.cc L973-L1005)
   파일마다 두 블록을 읽고 crc32 가 맞는 것 중 checkpoint_lsn 이 가장 큰 것을 고른다
   그 lsn 이 그 파일의 [start_lsn, end_lsn) 안에 있어야 한다
```

`storage` / `innobase` / `log` / `log0chkp.cc` L415-L425 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L415-L425))

```cpp
// log0chkp.cc L415-L425
Log_checkpoint_header_no log_next_checkpoint_header(
    Log_checkpoint_header_no checkpoint_header_no) {
  switch (checkpoint_header_no) {
    case Log_checkpoint_header_no::HEADER_1:
      return Log_checkpoint_header_no::HEADER_2;
    case Log_checkpoint_header_no::HEADER_2:
      return Log_checkpoint_header_no::HEADER_1;
    default:
      ut_error;
  }
}
```

체크포인트를 언제 어디까지 올리는지는 [log_checkpoint](../../flows/flush-checkpoint/09_log_checkpoint/README.md)와 [log_files_next_checkpoint](../../flows/flush-checkpoint/10_log_files_next_checkpoint/README.md), 복구가 고르는 과정은 [recv_find_max_checkpoint](../../flows/crash-recovery/03_recv_find_max_checkpoint/README.md)에 있다.

## 데이터 블록 헤더

블록 번호와 epoch 는 lsn 만으로 계산된다. 그래서 복구는 읽은 블록의 번호가 그 lsn 에서 기대한 값과 다르거나 체크섬이 틀리면 "쓰레기이거나 덜 쓰인 블록", 곧 로그의 끝으로 본다(log0recv.cc L1342-L1350).

`storage` / `innobase` / `include` / `log0files_io.h` L530-L548 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0files_io.h#L530-L548))

```cpp
// log0files_io.h L530-L548
/** Converts a lsn to a log block epoch number.
For details @see LOG_BLOCK_EPOCH_NO.
@param[in]	lsn	lsn of a byte within the block
@return log block epoch number, it is > 0 */
inline uint32_t log_block_convert_lsn_to_epoch_no(lsn_t lsn) {
  return 1 +
         static_cast<uint32_t>(lsn / OS_FILE_LOG_BLOCK_SIZE / LOG_BLOCK_MAX_NO);
}

/** Converts a lsn to a log block number. Consecutive log blocks have
consecutive numbers (unless the sequence wraps). It is guaranteed that
the calculated number is greater than zero.

@param[in]	lsn	lsn of a byte within the block
@return log block number, it is > 0 and <= 1G */
inline uint32_t log_block_convert_lsn_to_hdr_no(lsn_t lsn) {
  return 1 +
         static_cast<uint32_t>(lsn / OS_FILE_LOG_BLOCK_SIZE % LOG_BLOCK_MAX_NO);
}
```

`storage` / `innobase` / `include` / `log0files_io.h` L623-L634 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0files_io.h#L623-L634))

```cpp
// log0files_io.h L623-L634
/** Serializes the log data block header to the redo log block buffer which
already contains redo log data (must have the redo data before this call).
@param[in]   header    the header to serialize
@param[out]  buf       the buffer containing the redo log block with the data */
inline void log_data_block_header_serialize(const Log_data_block_header &header,
                                            byte *buf) {
  log_block_set_epoch_no(buf, header.m_epoch_no);
  log_block_set_hdr_no(buf, header.m_hdr_no);
  log_block_set_data_len(buf, header.m_data_len);
  log_block_set_first_rec_group(buf, header.m_first_rec_group);
  log_block_store_checksum(buf);
}
```

## mlog 레코드 한 개의 모양

redo 레코드는 "어느 페이지의 어느 바이트를 어떻게 바꿨나"다. 맨 앞 1바이트가 타입(`mlog_id_t`), 이어서 space_id 와 page_no 가 가변 길이 정수로 붙고, 그 뒤 본문 모양은 타입마다 다르다.

```text
 레코드 공통 머리 (mlog_write_initial_log_record_low, mtr0log.ic L169-L184)

 +--------+--------------------+--------------------+----------------------+
 | type 1 | space_id  1~5      | page_no  1~5       | 타입별 본문          |
 +--------+--------------------+--------------------+----------------------+
   최상위 비트 0x80 = MLOG_SINGLE_REC_FLAG           최대 11바이트 = REDO_LOG_INITIAL_INFO_SIZE
   (mtr 에 레코드가 하나뿐일 때 첫 레코드에 OR)

 가변 길이 정수 (mach_write_compressed, mach0data.ic L155-L192)
   0nnnnnnn                               < 0x80         1바이트
   10nnnnnn nnnnnnnn                      < 0x4000       2바이트
   110nnnnn nnnnnnnn nnnnnnnn             < 0x200000     3바이트
   1110nnnn  + 3바이트                    < 0x10000000   4바이트
   11110000  + 4바이트                    그 밖           5바이트
   (0xFF... 근처의 큰 값은 111110nn 등 확장 형식으로 짧게 쓴다)
```

```text
 예: 페이지의 4바이트 필드 하나를 바꾸는 MLOG_4BYTES (mlog_write_ulint, mtr0log.cc L258-L296)

 space_id = 5, page_no = 300, 페이지 안 offset = 38 + 16 (PAGE_N_RECS), 새 값 = 7

 +------+------+-----------+-----------+------+
 | 0x04 | 0x05 | 0x81 0x2c | 0x00 0x36 | 0x07 |
 +------+------+-----------+-----------+------+
   type   space  page_no     offset 2    값 (가변 길이 정수)
   =4     =5     =300        =54         =7
          1바이트 2바이트 (10 + 14비트)

 mtr 안 레코드가 여럿이면 마지막에 MLOG_MULTI_REC_END (31) 1바이트가 붙는다
 하나뿐이면 끝 표시 대신 첫 바이트에 0x80 을 OR 한다 (mtr0mtr.cc L797, L804)
```

```text
 mlog_id_t 의 큰 갈래 (mtr0types.h L63-L283)

 값        이름                           본문
 --------  -----------------------------  ------------------------------------------
 1 2 4 8   MLOG_1BYTE .. MLOG_8BYTES      offset 2 + 값. 타입 값이 곧 바이트 수
 30        MLOG_WRITE_STRING              offset 2 + 길이 2 + 바이트열
 31        MLOG_MULTI_REC_END             없음. mtr 묶음의 끝
 32        MLOG_DUMMY_RECORD              블록을 채우는 패딩
 19 37     MLOG_PAGE_CREATE / COMP_        빈 인덱스 페이지 생성
 20        MLOG_UNDO_INSERT               undo 레코드 한 개 추가 (trx0rec.cc L85)
 33 34 35  MLOG_FILE_CREATE/RENAME/DELETE 페이지가 아니라 파일 연산
 59        MLOG_INIT_FILE_PAGE2           페이지를 새로 쓰기 시작, 이전 내용 무시
 65        MLOG_FILE_EXTEND               공간 확장
 67 .. 76  MLOG_REC_INSERT ..             인덱스 페이지의 레코드 연산 (insert, clust delete mark,
           MLOG_LIST_START_DELETE         delete, update in place, 리스트 끝 복사, 재구성,
                                          압축 페이지 재구성과 압축, 리스트 앞뒤 삭제)
                                          본문에 인덱스 열 정의가 먼저 들어간다
                                          (mlog_open_and_write_index, page0cur.cc L976)
 OBSOLETE_*_8027                          8.0.27 이전 형식의 이름. 새 형식은 67 이후 값을 쓴다
```

`storage` / `innobase` / `include` / `mtr0types.h` L59-L82 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/mtr0types.h#L59-L82))

```cpp
// include/mtr0types.h L59-L82
/** @name Log item types
The log items are declared 'byte' so that the compiler can warn if val
and type parameters are switched in a call to mlog_write_ulint. NOTE!
For 1 - 8 bytes, the flag value must give the length also! @{ */
enum mlog_id_t {
  /** if the mtr contains only one log record for one page,
  i.e., write_initial_log_record has been called only once,
  this flag is ORed to the type of that first log record */
  MLOG_SINGLE_REC_FLAG = 128,

  /** one byte is written */
  MLOG_1BYTE = 1,

  /** 2 bytes ... */
  MLOG_2BYTES = 2,

  /** 4 bytes ... */
  MLOG_4BYTES = 4,

  /** 8 bytes ... */
  MLOG_8BYTES = 8,

  /** Record insert */
  OBSOLETE_MLOG_REC_INSERT_8027 = 9,
```

`storage` / `innobase` / `include` / `mtr0types.h` L145-L157 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/mtr0types.h#L145-L157))

```cpp
// include/mtr0types.h L145-L157
  /** write a string to a page */
  MLOG_WRITE_STRING = 30,

  /** If a single mtr writes several log records, this log
  record ends the sequence of these records */
  MLOG_MULTI_REC_END = 31,

  /** dummy log record used to pad a log block full */
  MLOG_DUMMY_RECORD = 32,

  /** log record about creating an .ibd file, with format */
  MLOG_FILE_CREATE = 33,

```

`storage` / `innobase` / `include` / `mtr0log.ic` L162-L184 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/mtr0log.ic#L162-L184))

```cpp
// mtr0log.ic L162-L184
/** Writes a log record about an operation.
@param[in]      type            Redo log record type
@param[in]      space_id        Tablespace identifier
@param[in]      page_no         Page number
@param[in,out]  log_ptr         Current end of mini-transaction log
@param[in,out]  mtr             Mini-transaction
@return end of mini-transaction log */
static inline byte *mlog_write_initial_log_record_low(mlog_id_t type,
                                                      space_id_t space_id,
                                                      page_no_t page_no,
                                                      byte *log_ptr,
                                                      mtr_t *mtr) {
  ut_ad(type <= MLOG_BIGGEST_TYPE);

  mach_write_to_1(log_ptr, type);
  log_ptr++;

  log_ptr += mach_write_compressed(log_ptr, space_id);
  log_ptr += mach_write_compressed(log_ptr, page_no);

  mtr->added_rec();
  return (log_ptr);
}
```

`storage` / `innobase` / `include` / `mach0data.ic` L155-L192 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/mach0data.ic#L155-L192))

```cpp
// mach0data.ic L155-L192
static inline ulint mach_write_compressed(byte *b, ulint n) {
  ut_ad(b);

  if (n < 0x80) {
    /* 0nnnnnnn (7 bits) */
    mach_write_to_1(b, n);
    return (1);
  } else if (n < 0x4000) {
    /* 10nnnnnn nnnnnnnn (14 bits) */
    mach_write_to_2(b, n | 0x8000);
    return (2);
  } else if (n < 0x200000) {
    /* 110nnnnn nnnnnnnn nnnnnnnn (21 bits) */
    mach_write_to_3(b, n | 0xC00000);
    return (3);
  } else if (n < 0x10000000) {
    /* 1110nnnn nnnnnnnn nnnnnnnn nnnnnnnn (28 bits) */
    mach_write_to_4(b, n | 0xE0000000);
    return (4);
  } else if (n >= 0xFFFFFC00) {
    /* 111110nn nnnnnnnn (10 bits) (extended) */
    mach_write_to_2(b, (n & 0x3FF) | 0xF800);
    return (2);
  } else if (n >= 0xFFFE0000) {
    /* 1111110n nnnnnnnn nnnnnnnn (17 bits) (extended) */
    mach_write_to_3(b, (n & 0x1FFFF) | 0xFC0000);
    return (3);
  } else if (n >= 0xFF000000) {
    /* 11111110 nnnnnnnn nnnnnnnn nnnnnnnn (24 bits) (extended) */
    mach_write_to_4(b, (n & 0xFFFFFF) | 0xFE000000);
    return (4);
  } else {
    /* 11110000 nnnnnnnn nnnnnnnn nnnnnnnn nnnnnnnn (32 bits) */
    mach_write_to_1(b, 0xF0);
    mach_write_to_4(b + 1, n);
    return (5);
  }
}
```

`storage` / `innobase` / `mtr` / `mtr0log.cc` L256-L296 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0log.cc#L256-L296))

```cpp
// mtr/mtr0log.cc L256-L296
/** Writes 1, 2 or 4 bytes to a file page. Writes the corresponding log
 record to the mini-transaction log if mtr is not NULL. */
void mlog_write_ulint(
    byte *ptr,      /*!< in: pointer where to write */
    ulint val,      /*!< in: value to write */
    mlog_id_t type, /*!< in: MLOG_1BYTE, MLOG_2BYTES, MLOG_4BYTES */
    mtr_t *mtr)     /*!< in: mini-transaction handle */
{
  switch (type) {
    case MLOG_1BYTE:
      mach_write_to_1(ptr, val);
      break;
    case MLOG_2BYTES:
      mach_write_to_2(ptr, val);
      break;
    case MLOG_4BYTES:
      mach_write_to_4(ptr, val);
      break;
    default:
      ut_error;
  }

  if (mtr == nullptr) {
    return;
  }

  /* If no logging is requested, we may return now */
  byte *log_ptr = nullptr;
  if (!mlog_open(mtr, REDO_LOG_INITIAL_INFO_SIZE + 2 + 5, log_ptr)) {
    return;
  }

  log_ptr = mlog_write_initial_log_record_fast(ptr, type, log_ptr, mtr);

  mach_write_to_2(log_ptr, page_offset(ptr));
  log_ptr += 2;

  log_ptr += mach_write_compressed(log_ptr, val);

  mlog_close(mtr, log_ptr);
}
```

## log_t 의 파일 관련 필드

메모리 쪽에서 파일 집합을 들고 있는 것은 전역 `log_sys`(`log_t`)다. 파일 목록과 현재 파일, 체크포인트 상태가 여기에 있다.

```text
 log_t (log0sys.h L77) 중 파일과 체크포인트 쪽

 m_current_file              L287  log_writer 가 쓰는 파일. offset 계산에 쓴다
 m_files_ctx                 L415  #innodb_redo 경로와 규칙 (CURRENT / PRE_8_0_30)
 m_files                     L419  Log_files_dict. id -> Log_file{start_lsn, end_lsn, consumed, full}
 m_unused_files_count        L423  _tmp 예비 파일 수
 m_capacity                  L431  innodb_redo_log_capacity 와 리사이즈
 last_checkpoint_lsn         L701  마지막으로 블록에 쓴 체크포인트
 next_checkpoint_header_no   L706  다음에 쓸 블록 (HEADER_1 / HEADER_2)
```

## 어디에서 쓰이는가

```text
 [mini-transaction과 redo 기록]  mlog_write_* 가 레코드를 m_log 에 쌓고
                                 commit 이 sn 범위를 받아 블록 모양 log buffer 에 복사한다
                                 log_writer 가 lsn -> 파일 오프셋으로 바꿔 write 한다
 [페이지 플러시...]              log_checkpointer 가 체크포인트 블록 1/3 을 번갈아 쓰고
                                 다 쓴 파일을 소비해 _tmp 예비로 돌린다
 [크래시 복구]                   두 체크포인트 블록 중 큰 것에서 시작해
                                 블록 번호, data_len, 체크섬으로 로그 끝을 찾고
                                 타입별로 레코드를 파싱해 page LSN 보다 새 것만 적용한다
```

흐름 문서: [mini-transaction과 redo 기록](../../flows/mtr-redo/README.md)(레코드 묶음의 끝 표시는 [prepare_write](../../flows/mtr-redo/03_mtr_t.Command.prepare_write/README.md)), [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md), [크래시 복구](../../flows/crash-recovery/README.md)(레코드 파싱은 [recv_parse_log_recs](../../flows/crash-recovery/06_recv_parse_log_recs/README.md)). redo 가 가리키는 페이지 안 오프셋의 의미는 [테이블스페이스와 페이지 레이아웃](../tablespace-page/README.md)에 있다.

## db-engine 에서는

db-engine 의 WAL 은 파일 하나에 `[길이 4][tag 1][txId 8][본문]` 을 이어 붙인다. MySQL 이 물리 페이지 변경을 적는 것과 달리 db-engine 은 "어느 테이블에 어떤 튜플을 넣었다"는 논리 연산을 적는다.

```text
 같은 문제(로그 파일 모양과 체크포인트), 두 구현 (위 MySQL / 아래 db-engine)

 파일
   MySQL      #innodb_redo/#ib_redoN 여러 개, 순환 재사용, 파일마다 2048바이트 헤더
   db-engine  wal 파일 하나, 계속 append

 단위
   MySQL      512바이트 블록. 레코드는 블록 경계를 넘어 흐르고 블록마다 crc32
   db-engine  레코드마다 [len Int][payload]. 체크섬 없음, 블록 없음

 레코드 머리
   MySQL      [type 1][space_id 가변][page_no 가변] + 페이지 안 offset 과 바이트
   db-engine  [tag 1 (BEGIN/INSERT/COMMIT/ABORT/CHECKPOINT)][txId 8]

 LSN
   MySQL      바이트 위치 (블록 헤더 포함). 파일 오프셋 = 2048 + (lsn - start_lsn)
   db-engine  레코드 순번 (1, 2, 3 ...). reopen 때 레코드 수를 세어 복원

 체크포인트가 놓이는 곳
   MySQL      파일 헤더의 고정 블록 2개 (offset 512, 1536) 에 번갈아 덮어쓴다
   db-engine  로그 본문에 Checkpoint 레코드로 append (checkpointLsn + 활성 txId 목록)
              마지막 적용 LSN 은 별도 recovery.meta 파일
```

MySQL 은 체크포인트를 로그 흐름 밖의 고정 자리에 두므로, 복구가 로그를 처음부터 훑지 않고 블록 두 개만 읽어 시작점을 안다. db-engine 은 체크포인트 레코드도 로그 안에 있어 찾으려면 로그를 읽어야 한다. 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/).

## 다루지 않는 것

8.0.30 이전 형식(`ib_logfile0/1`, `log_pre_8_0_30`), redo 암호화 블록의 내용, 파일 크기 조정과 governor 의 예비 파일 관리(`log_files_governor.cc`), redo 비활성화 플래그(`LOG_HEADER_FLAG_NO_LOGGING`), 각 mlog 타입 본문의 세부 형식(`recv_parse_or_apply_log_rec_body`), 압축 페이지용 `MLOG_ZIP_*`, 레코드 단위 연산 앞에 붙는 인덱스 정의의 바이트 모양, 로그 아카이브와 clone 이 파일을 읽는 방식은 곁가지라 다루지 않았다.
