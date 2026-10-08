# 레코드 포맷

상위: [MySQL 아키텍처 지도](../../README.md)

InnoDB 인덱스 페이지에 놓이는 레코드 하나의 바이트 모양이다. 핵심은 **레코드 포인터(origin)가 첫 열 데이터의 시작을 가리키고, 메타 정보는 그 앞쪽(낮은 주소)으로 거꾸로 쌓인다**는 점이다. COMPACT 와 DYNAMIC 형식에서 origin 바로 앞 5바이트가 고정 헤더(`REC_N_NEW_EXTRA_BYTES`)이고, 그 앞에 NULL 비트맵, 다시 그 앞에 가변 길이 열의 길이 목록이 놓인다. 클러스터드 인덱스 레코드에는 사용자가 정의하지 않은 숨은 열 `DB_TRX_ID`(6바이트)와 `DB_ROLL_PTR`(7바이트)가 기본 키 바로 뒤에 들어가고, 기본 키가 없으면 `DB_ROW_ID`(6바이트)가 맨 앞에 들어간다. 큰 열은 페이지 밖으로 나가고 레코드에는 20바이트 참조만 남는다. 레코드 바이트 모양에서 COMPACT 와 DYNAMIC 이 갈리는 곳은 이 마지막 부분이다. 페이지 밖으로 보낼 때 앞부분 768바이트를 레코드에 남기느냐, 그리고 최대 길이 255바이트 이하인 비 BLOB 열을 밖으로 보낼 수 있느냐(DYNAMIC 은 못 보낸다). 레코드를 페이지에 넣는 동작은 [B+Tree 삽입과 분할](../../flows/btree-insert/README.md)에, 레코드가 놓이는 페이지 모양은 [테이블스페이스와 페이지 레이아웃](../tablespace-page/README.md)에 있다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 COMPACT / DYNAMIC 레코드 하나 (낮은 주소가 왼쪽)

 ... +-------------------------+-----------+----------+-------+-------+-----+-------+
     | len(var n) .. len(var 1)| NULL bits | header 5 | col 1 | col 2 | ... | col n |
 ... +-------------------------+-----------+----------+-------+-------+-----+-------+
                                                      ^
                                                      origin (rec_t *)
     |<------------ extra (rec_offs_extra_size) ----->|<--- data (rec_offs_data_size) --->|

 len 목록   가변 길이 열의 길이. 첫 열의 길이가 origin 쪽, 1 또는 2바이트
            NULL 인 열과 고정 길이 열은 자리가 없다
 NULL bits  nullable 열만 1비트씩, 바이트 단위로 올림

 읽는 방향
   헤더      rec - 5 .. rec - 1
   NULL 비트 rec - 6 부터 낮은 주소 쪽으로    nulls = rec - (REC_N_NEW_EXTRA_BYTES + 1)
   길이 목록 NULL 비트맵 바로 아래부터 낮은 주소 쪽으로
                                              lens = nulls - UT_BITS_IN_BYTES(n_null)
   데이터    rec 부터 높은 주소 쪽으로, 열 순서대로

 origin 을 기준으로 앞뒤로 펼쳐 두는 이유를 rem0rec.cc 주석(L129-L133)이 적어 두었다
   앞쪽 열의 오프셋이 origin 가까이 있어 검색 때 캐시 적중이 좋다
```

```text
 5바이트 고정 헤더 (rec 기준 음수 오프셋, rem/rec.h L84-L125)

 rec-5       rec-4       rec-3       rec-2       rec-1       rec
 +-----------+-----------+-----------+-----------+-----------+---------
 | iiii oooo | hhhh hhhh | hhhh hsss | nnnn nnnn | nnnn nnnn | col 1 ...
 +-----------+-----------+-----------+-----------+-----------+---------

 i  info 비트 4     REC_NEW_INFO_BITS = 5   mask 0xF0
 o  n_owned 4       REC_NEW_N_OWNED   = 5   mask 0x0F
 h  heap_no 13      REC_NEW_HEAP_NO   = 4   rec-4 에서 2바이트 읽어 mask 0xFFF8, shift 3
 s  status 3        REC_NEW_STATUS    = 3   mask 0x07
 n  next 16         REC_NEXT          = 2   rec-2 에서 2바이트 읽기

 info 비트   0x10 MIN_REC   비리프 레벨 맨 왼쪽 페이지의 첫 레코드
             0x20 DELETED   delete mark (purge 가 나중에 지운다)
             0x40 VERSION   행 버전 바이트가 있다 (INSTANT ADD/DROP 이후)
             0x80 INSTANT   옛 INSTANT ADD COLUMN 이후 삽입, 필드 수 바이트가 있다
 n_owned     이 레코드를 가리키는 directory 슬롯이 소유한 레코드 수 (아니면 0)
 heap_no     페이지 heap 안 일련번호. infimum 0, supremum 1, 사용자 레코드 2 부터
             레코드 잠금 비트맵의 비트 번호로 쓰인다 (lock_rec_set_nth_bit)
 status      0 일반(리프)  1 node pointer(비리프)  2 infimum  3 supremum
 next        다음 레코드까지의 상대 거리 (자기 origin 기준, 16비트, 음수 가능)
             0 이면 끝 (supremum)
```

```text
 예: t(id INT PRIMARY KEY, name VARCHAR(10) NULL, memo VARCHAR(300) NULL, age INT NULL)
     1바이트 문자셋 가정, 행 (1, 'kim', NULL, 30)

 클러스터드 인덱스의 열 순서 (dict_index_build_internal_clust)
   id | DB_TRX_ID | DB_ROLL_PTR | name | memo | age

 nullable 열 = name, memo, age  -> 비트맵 1바이트, bit0=name bit1=memo bit2=age
 가변 길이 열 = name, memo       -> NULL 아닌 name 의 길이만 기록

 low                                                                       high
 +------+------+----------------+------+----------+-----------+-----+-------+
 | 0x03 | 0x02 | header 5       | id 4 | TRX_ID 6 | ROLL_PTR 7| kim | age 4 |
 +------+------+----------------+------+----------+-----------+-----+-------+
   |      |                     ^
   |      |                     origin
   |      +-- NULL 비트맵 010b  (bit1 = memo 만 NULL)
   +--------- name 의 길이 3    (memo 는 NULL 이라 길이 자리가 없다)

 memo 는 데이터도 0바이트, age 는 INT 고정 4바이트라 길이 목록에 없다

 extra = 1 + 1 + 5 = 7바이트, data = 4 + 6 + 7 + 3 + 4 = 24바이트
```

## 헤더 비트 필드

헤더 필드는 구조체가 아니라 "origin 에서 몇 바이트 앞, 마스크, 시프트" 세 값으로 정의된다. `REC_NEW_*` 가 COMPACT, `REC_OLD_*` 가 REDUNDANT 쪽이다. 두 정적 단언(static_assert)이 마스크들이 겹치지 않고 빈틈없이 3바이트(COMPACT), 4바이트(REDUNDANT)를 채운다는 것을 컴파일 때 확인한다.

`storage` / `innobase` / `rem` / `rec.h` L84-L159 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/rem/rec.h#L84-L159))

```cpp
// rec.h L84-L159
constexpr uint32_t REC_NEW_HEAP_NO = 4;
/* The shift of heap_no in a compact record.
The status is stored in the low-order bits. */
constexpr uint32_t REC_HEAP_NO_SHIFT = 3;

/* We list the byte offsets from the origin of the record, the mask,
and the shift needed to obtain each bit-field of the record. */

constexpr uint32_t REC_NEXT = 2;
constexpr uint32_t REC_NEXT_MASK = 0xFFFFUL;
constexpr uint32_t REC_NEXT_SHIFT = 0;

// ... (L96-L103 생략: REDUNDANT 전용 short, n_fields 필드)
constexpr uint32_t REC_NEW_STATUS = 3; /* This is single byte bit-field */
constexpr uint32_t REC_NEW_STATUS_MASK = 0x7UL;
constexpr uint32_t REC_NEW_STATUS_SHIFT = 0;

constexpr uint32_t REC_OLD_HEAP_NO = 5;
constexpr uint32_t REC_HEAP_NO_MASK = 0xFFF8UL;
// ... (L110-L114 생략: 비활성(#if 0) 매크로)
constexpr uint32_t REC_OLD_N_OWNED = 6; /* This is single byte bit-field */
constexpr uint32_t REC_NEW_N_OWNED = 5; /* This is single byte bit-field */
constexpr uint32_t REC_N_OWNED_MASK = 0xFUL;
constexpr uint32_t REC_N_OWNED_SHIFT = 0;

constexpr uint32_t REC_OLD_INFO_BITS = 6; /* This is single byte bit-field */
constexpr uint32_t REC_NEW_INFO_BITS = 5; /* This is single byte bit-field */
constexpr uint32_t REC_TMP_INFO_BITS = 1; /* This is single byte bit-field */
constexpr uint32_t REC_INFO_BITS_MASK = 0xF0UL;
constexpr uint32_t REC_INFO_BITS_SHIFT = 0;

static_assert((REC_OLD_SHORT_MASK << (8 * (REC_OLD_SHORT - 3)) ^
               REC_OLD_N_FIELDS_MASK << (8 * (REC_OLD_N_FIELDS - 4)) ^
               REC_HEAP_NO_MASK << (8 * (REC_OLD_HEAP_NO - 4)) ^
               REC_N_OWNED_MASK << (8 * (REC_OLD_N_OWNED - 3)) ^
               REC_INFO_BITS_MASK << (8 * (REC_OLD_INFO_BITS - 3)) ^
               0xFFFFFFFFUL) == 0,
              "sum of old-style masks != 0xFFFFFFFFUL");
static_assert((REC_NEW_STATUS_MASK << (8 * (REC_NEW_STATUS - 3)) ^
               REC_HEAP_NO_MASK << (8 * (REC_NEW_HEAP_NO - 4)) ^
               REC_N_OWNED_MASK << (8 * (REC_NEW_N_OWNED - 3)) ^
               REC_INFO_BITS_MASK << (8 * (REC_NEW_INFO_BITS - 3)) ^
               0xFFFFFFUL) == 0,
              "sum of new-style masks != 0xFFFFFFUL");

/* Info bit denoting the predefined minimum record: this bit is set
if and only if the record is the first user record on a non-leaf
B-tree page that is the leftmost page on its level
(PAGE_LEVEL is nonzero and FIL_PAGE_PREV is FIL_NULL). */
constexpr uint32_t REC_INFO_MIN_REC_FLAG = 0x10UL;
/** The deleted flag in info bits; when bit is set to 1, it means the record has
 been delete marked */
constexpr uint32_t REC_INFO_DELETED_FLAG = 0x20UL;
/* Use this bit to indicate record has version */
constexpr uint32_t REC_INFO_VERSION_FLAG = 0x40UL;
/** The instant ADD COLUMN flag. When it is set to 1, it means this record
was inserted/updated after an instant ADD COLUMN. */
constexpr uint32_t REC_INFO_INSTANT_FLAG = 0x80UL;

/* Number of extra bytes in an old-style record,
in addition to the data and the offsets */
constexpr uint32_t REC_N_OLD_EXTRA_BYTES = 6;
/* Number of extra bytes in a new-style record,
in addition to the data and the offsets */
constexpr int32_t REC_N_NEW_EXTRA_BYTES = 5;
```

`storage` / `innobase` / `rem` / `rec.h` L178-L188 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/rem/rec.h#L178-L188))

```cpp
// rec.h L178-L188
/* Record status values */
constexpr uint32_t REC_STATUS_ORDINARY = 0;
constexpr uint32_t REC_STATUS_NODE_PTR = 1;
constexpr uint32_t REC_STATUS_INFIMUM = 2;
constexpr uint32_t REC_STATUS_SUPREMUM = 3;

/* The following four constants are needed in page0zip.cc in order to
efficiently compress and decompress pages. */

/* Length of a B-tree node pointer, in bytes */
constexpr uint32_t REC_NODE_PTR_SIZE = 4;
```

REDUNDANT(옛 형식)는 헤더가 6바이트이고, next 가 페이지 안 **절대** 오프셋이며, 길이 목록 대신 모든 열의 끝 오프셋 배열을 둔다(rem0rec.cc L52-L93, rem/rec.h L38-L61 주석). COMPACT 는 next 를 자기 위치 기준 상대 거리로 바꿨다.

```text
 next 포인터 해석 (rem0rec.ic L125-L155)

 field_value = mach_read_from_2(rec - REC_NEXT)
 field_value == 0              -> 끝 (nullptr)
 COMPACT    next = page 시작 + ((rec + field_value) 의 페이지 안 오프셋)
            16비트 덧셈이 페이지 크기로 감기므로 뒤쪽(낮은 주소)도 가리킬 수 있다
 REDUNDANT  next = page 시작 + field_value

 빈 페이지에서 infimum(99) 의 next = 0x000d = 13 -> 99 + 13 = 112 = supremum
```

`storage` / `innobase` / `include` / `rem0rec.ic` L125-L155 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/rem0rec.ic#L125-L155))

```cpp
// rem0rec.ic L125-L155
static inline const rec_t *rec_get_next_ptr_const(const rec_t *rec,
                                                  ulint comp) {
  static_assert(REC_NEXT_MASK == 0xFFFFUL);
  static_assert(REC_NEXT_SHIFT == 0);

  const auto field_value = mach_read_from_2(rec - REC_NEXT);

  if (field_value == 0) {
    return (nullptr);
  }

  if (comp) {
    /** Check if the result offset is still on the same page. We allow
    `field_value` to be interpreted as negative 16bit integer. This check does
    nothing for 64KB pages. */
    ut_ad(static_cast<uint16_t>(field_value +
                                ut_align_offset(rec, UNIV_PAGE_SIZE)));

    /* There must be at least REC_N_NEW_EXTRA_BYTES + 1
    between each record. */
    ut_ad((field_value > REC_N_NEW_EXTRA_BYTES && field_value < 32768) ||
          field_value < (uint16_t)-REC_N_NEW_EXTRA_BYTES);

    return ((byte *)ut_align_down(rec, UNIV_PAGE_SIZE) +
            ut_align_offset(rec + field_value, UNIV_PAGE_SIZE));
  } else {
    ut_ad(field_value < UNIV_PAGE_SIZE);

    return ((byte *)ut_align_down(rec, UNIV_PAGE_SIZE) + field_value);
  }
}
```

전체 형식은 `rem0rec.cc` 머리 주석에 그림처럼 적혀 있다. 아래가 COMPACT(새 형식) 부분이다.

`storage` / `innobase` / `rem` / `rem0rec.cc` L95-L134 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/rem/rem0rec.cc#L95-L134))

```cpp
// rem0rec.cc L95-L134
/*                      PHYSICAL RECORD (NEW STYLE)
                        ===========================

The physical record, which is the data type of all the records
found in index pages of the database, has the following format
(lower addresses and more significant bits inside a byte are below
represented on a higher text line):

| length of the last non-null variable-length field of data:
  if the maximum length is 255, one byte; otherwise,
  0xxxxxxx (one byte, length=0..127), or 1exxxxxxxxxxxxxx (two bytes,
  length=128..16383, extern storage flag) |
...
| length of first variable-length field of data |
| SQL-null flags (1 bit per nullable field), padded to full bytes |
| 1 or 2 bytes to indicate number of fields in the record if the table
  where the record resides has undergone an instant ADD COLUMN
  before this record gets inserted; If no instant ADD COLUMN ever
  happened, here should be no byte; So parsing this optional number
  requires the index or table information |
| 4 bits used to delete mark a record, and mark a predefined
  minimum record in alphabetical order |
| 4 bits giving the number of records owned by this record
  (this term is explained in page0page.h) |
| 13 bits giving the order number of this record in the
  heap of the index page |
| 3 bits record type: 000=conventional, 001=node pointer (inside B-tree),
  010=infimum, 011=supremum, 1xx=reserved |
| two bytes giving a relative pointer to the next record in the page |
ORIGIN of the record
| first field of data |
...
| last field of data |

The origin of the record is the start address of the first field
of data. The offsets are given relative to the origin.
The offsets of the data fields are stored in an inverted
order because then the offset of the first fields are near the
origin, giving maybe a better processor cache hit rate in searches.

```

## NULL 비트맵과 가변 길이 목록

이 두 영역은 **열 정의를 알아야만 해석된다.** 비트맵에는 nullable 열만 자리가 있고, 길이 목록에는 NULL 이 아닌 가변 길이 열만 자리가 있다. 그래서 레코드 혼자서는 경계를 알 수 없고, `rec_get_offsets` 가 인덱스 정의(`dict_index_t`)와 함께 읽어 열마다 끝 오프셋 배열(`offsets`)을 만든다.

```text
 길이 바이트 해석 (rec_init_offsets_comp_ordinary, rem/rec.h L1230-L1290)

 열이 NOT NULL 이 아니면     nulls 의 다음 비트를 본다. 1 이면 NULL, 길이도 데이터도 없다
 열이 고정 길이면            길이 목록을 건드리지 않고 fixed_len 만큼 전진
 열이 가변 길이면            lens 에서 한 바이트 읽고 lens--
   최대 길이 <= 255 이고 BLOB 류가 아니면 (DATA_BIG_COL 거짓)
                             그 1바이트가 길이 (0..255)
   아니면 첫 바이트를 보고
     0xxxxxxx                1바이트, 길이 0..127
     1exxxxxx xxxxxxxx       2바이트, 길이 = & 0x3fff (최대 16383)
                             e (0x4000) = 페이지 밖 저장 -> REC_OFFS_EXTERNAL

 offsets[i+1] = 열 i 의 끝 오프셋 | 플래그 (SQL_NULL, EXTERNAL, DEFAULT, DROP)
```

`storage` / `innobase` / `rem` / `rec.h` L1031-L1095 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/rem/rec.h#L1031-L1095))

```cpp
// rec.h L1031-L1095
  /* Position nulls */
  *nulls = rec - (REC_N_NEW_EXTRA_BYTES + 1);
// ... (L1033-L1093 생략: 행 버전, INSTANT 상태에 따라 nulls 를 1~2바이트 더 내리는 처리)
  /* Position lens */
  *lens = *nulls - UT_BITS_IN_BYTES(*n_null);
```

`storage` / `innobase` / `rem` / `rec.h` L1230-L1290 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/rem/rec.h#L1230-L1290))

```cpp
// rec.h L1230-L1290
    if (!(col->prtype & DATA_NOT_NULL)) {
      /* nullable field => read the null flag */
      ut_ad(n_null--);

      if (UNIV_UNLIKELY(!(byte)null_mask)) {
        nulls--;
        null_mask = 1;
      }

      if (*nulls & null_mask) {
        null_mask <<= 1;
        /* No length is stored for NULL fields.
        We do not advance offs, and we set
        the length to zero and enable the
        SQL NULL flag in offsets[]. */
        len = offs | REC_OFFS_SQL_NULL;
        goto resolved;
      }
      null_mask <<= 1;
    }

    if (!field->fixed_len || (temp && !col->get_fixed_size(temp))) {
      ut_ad(col->mtype != DATA_POINT);
      /* Variable-length field: read the length */
      len = *lens--;
      /* If the maximum length of the field is up
      to 255 bytes, the actual length is always
      stored in one byte. If the maximum length is
      more than 255 bytes, the actual length is
      stored in one byte for 0..127.  The length
      will be encoded in two bytes when it is 128 or
      more, or when the field is stored externally. */
      if (DATA_BIG_COL(col)) {
        if (len & 0x80) {
          /* 1exxxxxxx xxxxxxxx */
          len <<= 8;
          len |= *lens--;

          offs += len & 0x3fff;
          if (UNIV_UNLIKELY(len & 0x4000)) {
            ut_ad(index->is_clustered());
            any_ext = REC_OFFS_EXTERNAL;
            len = offs | REC_OFFS_EXTERNAL;
          } else {
            len = offs;
          }

          goto resolved;
        }
      }

      len = offs += len;
    } else {
      len = offs += field->fixed_len;
    }
  resolved:
    rec_offs_base(offsets)[i + 1] = len;
  } while (++i < rec_offs_n_fields(offsets));

  *rec_offs_base(offsets) = (rec - (lens + 1)) | REC_OFFS_COMPACT | any_ext;
}
```

## 숨은 열

테이블을 만들면 사용자 열 뒤에 시스템 열 셋이 덧붙는다. 이 순서는 `DATA_ROW_ID`(0), `DATA_TRX_ID`(1), `DATA_ROLL_PTR`(2) 값으로 바로 찾을 수 있도록 고정이다.

`storage` / `innobase` / `include` / `data0type.h` L173-L194 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/data0type.h#L173-L194))

```cpp
// data0type.h L173-L194
/* Precise data types for system columns and the length of those columns;
NOTE: the values must run from 0 up in the order given! All codes must
be less than 256 */
/** row id: a 48-bit integer */
constexpr uint32_t DATA_ROW_ID = 0;
/** stored length for row id */
constexpr uint32_t DATA_ROW_ID_LEN = 6;

/** Transaction id: 6 bytes */
constexpr size_t DATA_TRX_ID = 1;

/** Transaction ID type size in bytes. */
constexpr size_t DATA_TRX_ID_LEN = 6;

/** Rollback data pointer: 7 bytes */
constexpr size_t DATA_ROLL_PTR = 2;

/** Rollback data pointer type size in bytes. */
constexpr size_t DATA_ROLL_PTR_LEN = 7;

/** number of system columns defined above */
constexpr uint32_t DATA_N_SYS_COLS = 3;
```

테이블 객체에 붙는 순서와 **레코드 안의 자리**는 다르다. 클러스터드 인덱스를 만들 때 자리를 정한다. 기본 키 열들 바로 뒤에 TRX_ID 와 ROLL_PTR 가 오고, 나머지 열이 그 뒤를 따른다. 기본 키가 없으면(유일 인덱스가 아니면) ROW_ID 가 키 역할로 먼저 들어간다.

```text
 클러스터드 인덱스 레코드의 열 순서

 PRIMARY KEY 가 있을 때
   [pk1][pk2]..[DB_TRX_ID 6][DB_ROLL_PTR 7][나머지 열 ...]
 없을 때 (GEN_CLUST_INDEX)
   [DB_ROW_ID 6][DB_TRX_ID 6][DB_ROLL_PTR 7][모든 열 ...]

 보조 인덱스 레코드에는 숨은 열이 없다
   [인덱스 열 ...][PK 열 ...]  <- PK 로 클러스터드 레코드를 다시 찾는다
                                 (dict0dict.cc L3209 주석)

 DB_ROLL_PTR 7바이트 = 56비트 (trx_undo_build_roll_ptr)
   bit 55     is_insert   insert undo 인가
   bit 48-54  undo 번호   undo 테이블스페이스 번호 (시스템 공간이면 0, 7비트)
   bit 16-47  page_no     undo 레코드가 있는 페이지
   bit 0-15   offset      그 페이지 안 위치
```

`storage` / `innobase` / `dict` / `dict0dict.cc` L3027-L3113 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/dict/dict0dict.cc#L3027-L3113))

```cpp
// dict0dict.cc L3027-L3113
  /* Add system columns */

  size_t trx_id_pos = new_index->n_def;

  /* Add ROW ID */
  if (!dict_index_is_unique(index)) {
    dict_index_add_col(new_index, table, table->get_sys_col(DATA_ROW_ID), 0,
                       true);
    set_phy_pos(table->get_sys_col(DATA_ROW_ID));
    trx_id_pos++;
  }

  /* Add TRX ID */
  dict_index_add_col(new_index, table, table->get_sys_col(DATA_TRX_ID), 0,
                     true);
  set_phy_pos(table->get_sys_col(DATA_TRX_ID));
// ... (L3043-L3076 생략: TRX_ID 의 고정 오프셋(trx_id_offset) 계산)
  /* Add ROLL PTR. UNDO logging is turned-off for intrinsic table and so
  DATA_ROLL_PTR system columns are not added as default system columns to such
  tables. */
  if (!table->is_intrinsic()) {
    dict_index_add_col(new_index, table, table->get_sys_col(DATA_ROLL_PTR), 0,
                       true);
    set_phy_pos(table->get_sys_col(DATA_ROLL_PTR));
  }

  // ... (L3086-L3101 생략: 이미 들어간 열 표시)
  /* Add to new_index non-system columns of table not yet included there */
  for (size_t i = 0; i < table->get_n_user_cols(); i++) {
    dict_col_t *col = table->get_col(i);
    ut_ad(col->mtype != DATA_SYS);

    if (indexed[col->ind]) {
      continue;
    }

    dict_index_add_col(new_index, table, col, 0, true);
    set_phy_pos(new_index->get_col(n_fields_processed));
  }
```

`storage` / `innobase` / `include` / `trx0undo.ic` L45-L54 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.ic#L45-L54))

```cpp
// trx0undo.ic L45-L54
inline roll_ptr_t trx_undo_build_roll_ptr(bool is_insert, space_id_t space_id,
                                          page_no_t page_no, ulint offset) {
  ut_ad(offset < 65536);

  ulint id = (fsp_is_undo_tablespace(space_id) ? undo::id2num(space_id) : 0);

  roll_ptr_t roll_ptr = (roll_ptr_t)is_insert << 55 | (roll_ptr_t)id << 48 |
                        (roll_ptr_t)page_no << 16 | offset;
  return (roll_ptr);
}
```

`DB_TRX_ID` 는 이 행을 마지막으로 바꾼 트랜잭션이고, `DB_ROLL_PTR` 는 바뀌기 전 모습을 담은 undo 레코드의 주소다. MVCC 읽기는 이 두 값으로 보이는지 판단하고 이전 버전을 거슬러 올라간다([일관 읽기(MVCC)와 undo 체인](../../flows/mvcc-read/README.md)).

## 페이지 밖(off-page) 저장

레코드가 페이지에 들어가기에 너무 크면(`page_zip_rec_needs_ext`), 가장 긴 가변 길이 열부터 하나씩 페이지 밖 LOB 페이지로 보낸다. 레코드에 남는 것은 20바이트 참조(`BTR_EXTERN_FIELD_REF_SIZE`)이고, 길이 목록의 그 열 자리에는 2바이트 형식에 e 비트가 켜진다.

```text
 열 하나가 페이지 밖으로 갈 때 레코드에 남는 것

 DYNAMIC, COMPRESSED (atomic blobs)
   [ref 20바이트]
 COMPACT, REDUNDANT
   [앞부분 768바이트 (DICT_ANTELOPE_MAX_INDEX_COL_LEN)][ref 20바이트]

 20바이트 참조 (lob0lob.h L101-L136)
   +0   4  BTR_EXTERN_SPACE_ID   LOB 가 있는 space
   +4   4  BTR_EXTERN_PAGE_NO    첫 LOB 페이지
   +8   4  BTR_EXTERN_OFFSET     옛 BLOB 은 페이지 안 오프셋, 새 LOB 은 버전 (BTR_EXTERN_VERSION)
   +12  8  BTR_EXTERN_LEN        페이지 밖 부분의 길이
           첫 바이트 상위 비트가 플래그
             0x80 OWNER_FLAG           이 레코드가 소유자가 아니다 (purge 가 지우면 안 된다)
             0x40 INHERITED_FLAG       이전 버전에서 물려받았다 (롤백이 지우면 안 된다)
             0x20 BEING_MODIFIED_FLAG  수정 중 (READ UNCOMMITTED 가 피한다)

 보낼 후보에서 빠지는 열 (dtuple_convert_big_rec)
   고정 길이, NULL, 이미 외부, local_len 이하, 키 열 (n_unique_in_tree 앞)
   DYNAMIC 에서는 최대 길이 255 이하인 비 BLOB 열도 빠진다
     길이가 1바이트로만 기록되어 e 비트 자리가 없기 때문이다
```

`storage` / `innobase` / `data` / `data0data.cc` L440-L446 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/data/data0data.cc#L440-L446))

```cpp
// data0data.cc L440-L446
  if (!dict_table_has_atomic_blobs(index->table)) {
    /* up to MySQL 5.1: store a 768-byte prefix locally */
    local_len = BTR_EXTERN_FIELD_REF_SIZE + DICT_ANTELOPE_MAX_INDEX_COL_LEN;
  } else {
    /* new-format table: do not store any BLOB prefix locally */
    local_len = BTR_EXTERN_FIELD_REF_SIZE;
  }
```

`storage` / `innobase` / `include` / `lob0lob.h` L101-L136 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lob0lob.h#L101-L136))

```cpp
// lob0lob.h L101-L136
/** Space identifier where stored. */
const ulint BTR_EXTERN_SPACE_ID = 0;

/** page number where stored */
const ulint BTR_EXTERN_PAGE_NO = 4;

/** offset of BLOB header on that page */
const ulint BTR_EXTERN_OFFSET = 8;

/** Version number of LOB (LOB in new format)*/
const ulint BTR_EXTERN_VERSION = BTR_EXTERN_OFFSET;

/** 8 bytes containing the length of the externally stored part of the LOB.
The 2 highest bits are reserved to the flags below. */
const ulint BTR_EXTERN_LEN = 12;

/*-------------------------------------- @} */

/** The most significant bit of BTR_EXTERN_LEN (i.e., the most
significant bit of the byte at smallest address) is set to 1 if this
field does not 'own' the externally stored field; only the owner field
is allowed to free the field in purge! */
const ulint BTR_EXTERN_OWNER_FLAG = 128UL;

/** If the second most significant bit of BTR_EXTERN_LEN (i.e., the
second most significant bit of the byte at smallest address) is 1 then
it means that the externally stored field was inherited from an
earlier version of the row.  In rollback we are not allowed to free an
inherited external field. */
const ulint BTR_EXTERN_INHERITED_FLAG = 64UL;

/** If the 3rd most significant bit of BTR_EXTERN_LEN is 1, then it
means that the externally stored field is currently being modified.
This is mainly used by the READ UNCOMMITTED transaction to avoid returning
inconsistent blob data. */
const ulint BTR_EXTERN_BEING_MODIFIED_FLAG = 32UL;
```

## 어디에서 쓰이는가

```text
 [행 쓰기]              row_ins 가 dtuple 을 만들고 숨은 열 TRX_ID, ROLL_PTR 를 채운다
 [B+Tree 삽입과 분할]   rec_convert_dtuple_to_rec 가 이 바이트 모양을 만든다
                        너무 크면 dtuple_convert_big_rec 로 열을 밖으로 뺀다
                        page_cur_insert_rec_low 가 heap_no, n_owned, next 를 채운다
 [일관 읽기(MVCC)]      DB_TRX_ID 로 가시성을 보고 DB_ROLL_PTR 로 undo 를 따라간다
 [레코드 잠금]          잠금 비트맵의 비트 번호가 heap_no 다
 [purge]                delete mark(0x20) 레코드를 실제로 지우고 LOB 소유 플래그를 본다
```

흐름 문서: [행 쓰기](../../flows/row-insert/README.md), [B+Tree 삽입과 분할](../../flows/btree-insert/README.md)(특히 [page_cur_tuple_insert](../../flows/btree-insert/05_page_cur_tuple_insert/README.md)), [일관 읽기(MVCC)와 undo 체인](../../flows/mvcc-read/README.md), [레코드 잠금과 교착](../../flows/record-lock/README.md), [purge](../../flows/purge/README.md).

## db-engine 에서는

db-engine 의 `Tuple.encode` 도 NULL 비트맵을 앞에 두고 NULL 이 아닌 값만 이어 쓴다. 뼈대는 같고, 길이를 어디에 두느냐와 레코드 밖의 정보가 있느냐가 다르다.

```text
 같은 문제(행 하나를 바이트로), 두 구현 (위 MySQL COMPACT / 아래 db-engine)

 배치
   MySQL      [길이 목록 거꾸로][NULL 비트맵][헤더 5][데이터 ...]   origin 은 데이터 시작
   db-engine  [NULL 비트맵][데이터 ...]                          바이트 0 부터

 NULL 비트맵
   MySQL      nullable 열만 1비트, 열 정의가 NOT NULL 이면 자리 없음
   db-engine  모든 열에 1비트, ceil(N/8) 바이트

 가변 길이 열의 길이
   MySQL      데이터 앞쪽 별도 목록에 1~2바이트. 데이터는 값만 이어 붙는다
   db-engine  값 바로 앞에 4바이트 Int (Type.STRING.encode)

 행 밖의 정보
   MySQL      헤더(delete mark, heap_no, next, n_owned) + 숨은 열 TRX_ID, ROLL_PTR
   db-engine  없음. 삭제 표시, 버전, 다음 행 포인터 모두 행 바깥이 맡는다

 큰 값
   MySQL      페이지에 안 맞으면 LOB 페이지로 보내고 20바이트 참조
   db-engine  없음. encode 결과가 그대로 한 덩어리
```

db-engine 의 `decode` 는 앞에서부터 순서대로 읽어야 다음 열의 시작을 안다(4바이트 길이를 읽고 건너뛴다). MySQL 은 `rec_get_offsets` 가 길이 목록만 한 번 훑어 모든 열의 끝 오프셋을 미리 만들어 두므로, 이후 n 번째 열 접근이 바로 된다. 챕터: [04-01-catalog](../../../../../project/db-engine/04-01-catalog/).

## 다루지 않는 것

REDUNDANT 형식의 세부(1바이트/2바이트 오프셋 배열, `REC_OLD_SHORT`), COMPRESSED 페이지의 레코드 압축, INSTANT ADD/DROP COLUMN 이 남기는 행 버전 바이트와 필드 수 바이트(`rec_init_null_and_len_comp`), 임시 파일용 레코드(`REC_N_TMP_EXTRA_BYTES`), node pointer 레코드(자식 page_no 4바이트, `REC_NODE_PTR_SIZE`), 열 값 자체의 인코딩(정수 부호 비트 뒤집기, 문자셋, DECIMAL), 새 LOB 형식의 페이지 구조(`lob::first_page_t`)는 곁가지라 다루지 않았다.
