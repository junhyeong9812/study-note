# buf_page_get_gen

상위: [버퍼 풀 페이지 획득](../README.md)

**버퍼 풀에서 페이지를 얻는 공용 입구다.** 함수 자체는 인자를 `Buf_fetch` 객체에 옮겨 담고 `single_page()` 를 부르는 것이 전부인데, 그 전에 **가장 흔한 경우(NORMAL 모드, 임시 테이블스페이스 아님)를 따로 떼어** 더 짧은 `Buf_fetch_normal::get` 을 타게 한다. 볼거리는 `Page_fetch` 모드 여덟 가지가 이후 경로를 어떻게 가르는지다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L4449-L4514 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4449-L4514))

## 실제 코드

디버그 빌드의 인자 검사를 빼면 분기 하나다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4449-L4514 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4449-L4514))

```cpp
// buf0buf.cc L4449-L4514
buf_block_t *buf_page_get_gen(const page_id_t &page_id,
                              const page_size_t &page_size, ulint rw_latch,
                              buf_block_t *guess, Page_fetch mode,
                              ut::Location location, mtr_t *mtr,
                              bool dirty_with_no_latch) {
// ... (L4454-L4485 생략: UNIV_DEBUG 인자 검사)
#endif /* UNIV_DEBUG */

  if (mode == Page_fetch::NORMAL && !fsp_is_system_temporary(page_id.space())) {
    Buf_fetch_normal fetch(page_id, page_size);

    fetch.m_rw_latch = rw_latch;
    fetch.m_guess = guess;
    fetch.m_mode = mode;
    fetch.m_file = location.filename;
    fetch.m_line = location.line;
    fetch.m_mtr = mtr;
    fetch.m_dirty_with_no_latch = dirty_with_no_latch;

    return (fetch.single_page());

  } else {
    Buf_fetch_other fetch(page_id, page_size);

    fetch.m_rw_latch = rw_latch;
    fetch.m_guess = guess;
    fetch.m_mode = mode;
    fetch.m_file = location.filename;
    fetch.m_line = location.line;
    fetch.m_mtr = mtr;
    fetch.m_dirty_with_no_latch = dirty_with_no_latch;

    return (fetch.single_page());
  }
}
```

모드는 여덟 가지다. 주석이 각 모드의 뜻을 적어 두었다.

`storage` / `innobase` / `include` / `buf0buf.h` L57-L88 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L57-L88))

```cpp
// include/buf0buf.h L57-L88
enum class Page_fetch {
  /** Get always */
  NORMAL,

  /** Same as NORMAL, but hint that the fetch is part of a large scan.
  Try not to flood the buffer pool with pages that may not be accessed again
  any time soon. */
  SCAN,

  /** get if in pool */
  IF_IN_POOL,

  /** get if in pool, do not make the block young in the LRU list */
  PEEK_IF_IN_POOL,

  /** get and bufferfix, but set no latch; we have separated this case, because
  it is error-prone programming not to set a latch, and it  should be used with
  care */
  NO_LATCH,

  /** Get the page only if it's in the buffer pool, if not then set a watch on
  the page. */
  IF_IN_POOL_OR_WATCH,

  /** Like Page_fetch::NORMAL, but do not mind if the file page has been
  freed. */
  POSSIBLY_FREED,

  /** Like Page_fetch::POSSIBLY_FREED, but do not initiate read ahead. */
  POSSIBLY_FREED_NO_READ_AHEAD,
};
/** @} */
```

흔히 쓰는 두 래퍼는 모드를 고정해서 부른다.

`storage` / `innobase` / `include` / `buf0buf.h` L452-L469 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L452-L469))

```cpp
// include/buf0buf.h L452-L469
inline buf_block_t *buf_page_get(const page_id_t &id, const page_size_t &size,
                                 ulint latch, ut::Location location,
                                 mtr_t *mtr) {
  return buf_page_get_gen(id, size, latch, nullptr, Page_fetch::NORMAL,
                          location, mtr);
}
/** Use these macros to bufferfix a page with no latching. Remember not to
 read the contents of the page unless you know it is safe. Do not modify
 the contents of the page! We have separated this case, because it is
 error-prone programming not to set a latch, and it should be used
 with care. */
inline buf_block_t *buf_page_get_with_no_latch(const page_id_t &id,
                                               const page_size_t &size,
                                               ut::Location location,
                                               mtr_t *mtr) {
  return buf_page_get_gen(id, size, RW_NO_LATCH, nullptr, Page_fetch::NO_LATCH,
                          location, mtr);
}
```

## 동작 흐름

```text
 L4488  mode == NORMAL && !fsp_is_system_temporary(space)
          예   L4489  Buf_fetch_normal fetch(page_id, page_size)
                      L4491-L4497  latch, guess, mode, 호출 위치, mtr, dirty_with_no_latch 복사
               L4499  return fetch.single_page()
          아니오 L4502  Buf_fetch_other fetch(...)
                      같은 필드 복사
               L4512  return fetch.single_page()

 두 클래스는 CRTP 로 Buf_fetch<T> 를 상속한다 (L3615 struct Buf_fetch)
   single_page 는 공통이고, 그 안의 static_cast<T *>(this)->get(block) 만 다르다
```

모드마다 이후 경로에서 달라지는 곳이 다르다. 아래 표는 [02] 와 [04] 의 조건문을 모드별로 모은 것이다.

```text
 Page_fetch 모드별 차이 (줄은 buf0buf.cc)

 모드                          get   young       lin RA          미적중 시
 NORMAL                        norm  O           O (first)       읽는다
 SCAN                          oth   X (L4402)   O               읽는다, random RA 없음 (L4123)
 IF_IN_POOL                    oth   O           O               nullptr (L3815)
 PEEK_IF_IN_POOL               oth   X (L4402)   X (L4429)       nullptr (L3815)
 NO_LATCH                      oth   O           O               읽는다
 IF_IN_POOL_OR_WATCH           oth   O           O               watch 를 건다 (L3800)
 POSSIBLY_FREED                oth   O           O               읽는다
 POSSIBLY_FREED_NO_READ_AHEAD  oth   O           X (L4430)       읽는다

 young = [09] make_young 판정을 하는가, lin RA = 첫 접근 때 linear read-ahead 를 하는가
 norm = Buf_fetch_normal::get, oth = Buf_fetch_other::get
 IF_IN_POOL 과 PEEK_IF_IN_POOL 은 is_optimistic() 이다 (L4187)
   적중했더라도 IO_READ 중이면 기다리지 않고 nullptr (L4320)
 임시 테이블스페이스는 NORMAL 이어도 oth 로 간다 (래치 대신 block mutex 로 fix)
```

guess 인자는 호출자가 "아마 이 블록일 것"이라고 넘기는 힌트다. B+Tree 탐색은 루트 페이지에 `root_guess` 를 넘긴다(btr0cur.cc L958-L961). guess 가 틀려도 [03] lookup 이 검증하고 page hash 로 되돌아간다.

## 결과가 쓰이는 곳

```text
 반환한 buf_block_t *
      --> nullptr 이면 IF_IN_POOL 류의 "없음" 이거나 테이블스페이스가 사라진 경우
      --> 아니면 buf-fix 와 rw_latch 가 걸려 있고 mtr memo 에 올라가 있다
          btr_cur_search_to_nth_level 은 nullptr 을 받으면(IF_IN_POOL 류, 리프)
          연산을 change buffer 로 넘긴다 (btr0cur.cc L965, ibuf_insert L978)
```

## 다루지 않는 것

`Page_fetch` 를 고르는 쪽의 사정(`btr_cur_search_to_nth_level` 이 change buffer 연산일 때 `IF_IN_POOL` 을 고르는 이유), `ut::Location` 이 디버그 래치 기록에 쓰이는 방식, `dirty_with_no_latch` 가 필요한 호출자(공간 인덱스, 임시 테이블)는 이 함수의 곁가지라 요약만 했다. 모드별 세부는 [02 single_page](../02_Buf_fetch.single_page/README.md)와 [04 get](../04_Buf_fetch_normal.get/README.md)에 있다.
