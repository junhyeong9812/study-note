# page_cur_tuple_insert

상위: [B+Tree 삽입과 분할](../README.md)

**논리 튜플(`dtuple_t`)을 물리 레코드 바이트로 바꾸는 자리다.** 페이지 밖의 임시 힙에 레코드를 한 번 만들고, 그 레코드의 필드 경계(`offsets`)를 계산한 뒤, 페이지가 압축이면 `page_cur_insert_rec_zip`, 아니면 [06] `page_cur_insert_rec_low` 에 넘긴다. [03], [08], [09] 가 모두 이 함수로 레코드를 넣는다.

## 위치

`storage` / `innobase` / `include` / `page0cur.ic` L187-L230 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/page0cur.ic#L187-L230))

## 실제 코드

`storage` / `innobase` / `include` / `page0cur.ic` L187-L230 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/page0cur.ic#L187-L230))

```cpp
// page0cur.ic L187-L230
static inline rec_t *page_cur_tuple_insert(page_cur_t *cursor,
                                           const dtuple_t *tuple,
                                           dict_index_t *index, ulint **offsets,
                                           mem_heap_t **heap, mtr_t *mtr) {
  rec_t *rec;
  rec_t *insert_rec;

  ulint size = rec_get_converted_size(index, tuple);

  if (!*heap) {
    *heap = mem_heap_create(
        size + (4 + REC_OFFS_HEADER_SIZE + dtuple_get_n_fields(tuple)) *
                   sizeof **offsets,
        UT_LOCATION_HERE);
  }

  rec = rec_convert_dtuple_to_rec((byte *)mem_heap_alloc(*heap, size), index,
                                  tuple);

  *offsets = rec_get_offsets(rec, index, *offsets, ULINT_UNDEFINED,
                             UT_LOCATION_HERE, heap);

  ut_ad(cmp_dtuple_rec(tuple, rec, index, *offsets) == 0);

  if (buf_block_get_page_zip(cursor->block)) {
    insert_rec = page_cur_insert_rec_zip(cursor, index, rec, *offsets, mtr);
  } else {
    insert_rec =
        page_cur_insert_rec_low(cursor->rec, index, rec, *offsets, mtr);
  }

// ... (L218-L227 생략: 디버그 빌드의 튜플과 레코드 비교)

  return (insert_rec);
}
```

## 동작 흐름

```text
 L194  size = rec_get_converted_size(index, tuple)      헤더 + 필드 데이터 크기
 L196  heap 이 없으면 size 와 offsets 배열이 들어갈 만큼 만든다
 L203  rec = rec_convert_dtuple_to_rec(heap 버퍼, index, tuple)
         튜플의 필드를 테이블의 레코드 형식으로 굽는다
 L206  offsets = rec_get_offsets(rec, index)             필드마다 끝 위치, 헤더 크기
 L209  assert: 튜플과 레코드가 같은 값
 L211  압축 페이지면 page_cur_insert_rec_zip
 L214  아니면 [06] page_cur_insert_rec_low(cursor->rec, index, rec, offsets, mtr)
         cursor->rec 바로 뒤에 넣는다
 L229  return 페이지 안의 새 레코드 (자리가 없으면 nullptr)
```

여기서 만든 레코드는 아직 페이지 밖에 있다. [06] 이 페이지 안에 자리를 얻어 이 바이트를 통째로 복사한다(`rec_copy`). 새 형식 레코드의 모양은 아래와 같다.

```text
 새 형식(COMPACT 계열) 레코드 하나 (rem/rec.h)

  <------- extra (rec_offs_extra_size) -------><-------- data -------->
 +-----------------+---------+----------------+----------------------+
 | 가변 길이 목록  | NULL    | 5 바이트 헤더  | 필드0 | 필드1 | ...  |
 |                 | 비트맵  |                |       |       |      |
 +-----------------+---------+----------------+----------------------+
                                              ^
                                              rec (origin). 포인터는 여기를 가리킨다

 5 바이트 헤더 (origin 에서 뒤로 센 자리)
   rec - 5          info bits 상위 4 bit + n_owned 하위 4 bit   REC_INFO_BITS_MASK 0xF0, REC_N_OWNED_MASK 0xF
   rec - 4 .. - 3   heap_no 상위 13 bit + status 하위 3 bit   REC_HEAP_NO_MASK 0xFFF8, REC_NEW_STATUS_MASK 0x7
   rec - 2 .. - 1   next  다음 레코드를 가리키는 값           REC_NEXT = 2
   REC_N_NEW_EXTRA_BYTES = 5 (L159), 마스크는 L105-L123

 이 함수가 만든 레코드의 n_owned, heap_no, next 는 아직 의미가 없다
 [06] 이 페이지에 넣으면서 채운다 (5. n_owned = 0, heap_no 설정, 4. next 연결)
```

## 결과가 쓰이는 곳

```text
 rec, offsets (페이지 밖의 임시 레코드)
      --> [06] 이 rec_copy 로 페이지 안에 복사하고 offsets 를 새 위치에 맞춘다
 반환값 (페이지 안의 레코드 또는 nullptr)
      --> [03] 은 nullptr 이면 재구성 후 재시도, [08] 은 재구성 후 또 실패하면 다시 분할
 *heap
      --> 호출자가 이어서 쓰고 비운다 (offsets_heap)
```

## 다루지 않는 것

레코드 형식 변환의 세부(`rec_convert_dtuple_to_rec` 의 REDUNDANT / COMPACT / 인스턴트 ADD COLUMN 버전 처리), 압축 페이지 삽입(`page_cur_insert_rec_zip`), 튜플에서 바로 페이지에 쓰는 내부 임시 테이블 경로(`page_cur_tuple_direct_insert`)는 곁가지다. 레코드 형식은 [레코드 포맷](../../../structure/record-format/README.md)에서 다룬다.
