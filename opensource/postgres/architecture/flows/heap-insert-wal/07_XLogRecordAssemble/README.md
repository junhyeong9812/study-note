# XLogRecordAssemble

상위: [행 쓰기와 WAL 기록](../README.md)

**등록된 조각들을 실제 WAL 레코드의 바이트 순서로 엮고, 블록마다 페이지 전체 이미지(FPI)를 실을지 정한다.** 판정 규칙은 하나다. 페이지 LSN 이 마지막 체크포인트의 redo 시작점(RedoRecPtr) 이하이면, 이 페이지는 체크포인트 뒤 처음 바뀌는 것이므로 이미지를 싣는다. 이미지를 실을 때는 페이지 가운데의 빈 구멍(pd_lower ~ pd_upper)을 빼고, 대신 그 블록의 일반 데이터는 뺀다. 헤더는 `hdr_scratch` 에 차례로 쓰고, 데이터는 복사하지 않고 `XLogRecData` 체인으로 이어 붙인다. CRC 는 헤더 뒤의 모든 바이트에 대해 여기서 계산하고, 레코드 헤더 부분은 위치(`xl_prev`)가 정해진 뒤 [08] 이 마무리한다.

## 위치

`access` / `transam` / `xloginsert.c` L548-L934 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L548-L934))

## 실제 코드

블록마다 FPI 가 필요한지, 블록 데이터를 실을지 정한다.

`access` / `transam` / `xloginsert.c` L547-L647 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L547-L647))

```c
// xloginsert.c L547-L647
static XLogRecData *
XLogRecordAssemble(RmgrId rmid, uint8 info,
				   XLogRecPtr RedoRecPtr, bool doPageWrites,
				   XLogRecPtr *fpw_lsn, int *num_fpi, bool *topxid_included)
{
	XLogRecData *rdt;
	uint64		total_len = 0;
	int			block_id;
	pg_crc32c	rdata_crc;
	registered_buffer *prev_regbuf = NULL;
	XLogRecData *rdt_datas_last;
	XLogRecord *rechdr;
	char	   *scratch = hdr_scratch;

	/*
	 * Note: this function can be called multiple times for the same record.
	 * All the modifications we do to the rdata chains below must handle that.
	 */

	/* The record begins with the fixed-size header */
	rechdr = (XLogRecord *) scratch;
	scratch += SizeOfXLogRecord;

	hdr_rdt.next = NULL;
	rdt_datas_last = &hdr_rdt;
	hdr_rdt.data = hdr_scratch;

	/*
	 * Enforce consistency checks for this record if user is looking for it.
	 * Do this before at the beginning of this routine to give the possibility
	 * for callers of XLogInsert() to pass XLR_CHECK_CONSISTENCY directly for
	 * a record.
	 */
	if (wal_consistency_checking[rmid])
		info |= XLR_CHECK_CONSISTENCY;

	/*
	 * Make an rdata chain containing all the data portions of all block
	 * references. This includes the data for full-page images. Also append
	 * the headers for the block references in the scratch buffer.
	 */
	*fpw_lsn = InvalidXLogRecPtr;
	for (block_id = 0; block_id < max_registered_block_id; block_id++)
	{
		registered_buffer *regbuf = &registered_buffers[block_id];
		bool		needs_backup;
		bool		needs_data;
		XLogRecordBlockHeader bkpb;
		XLogRecordBlockImageHeader bimg;
		XLogRecordBlockCompressHeader cbimg = {0};
		bool		samerel;
		bool		is_compressed = false;
		bool		include_image;

		if (!regbuf->in_use)
			continue;

		/* Determine if this block needs to be backed up */
		if (regbuf->flags & REGBUF_FORCE_IMAGE)
			needs_backup = true;
		else if (regbuf->flags & REGBUF_NO_IMAGE)
			needs_backup = false;
		else if (!doPageWrites)
			needs_backup = false;
		else
		{
			/*
			 * We assume page LSN is first data on *every* page that can be
			 * passed to XLogInsert, whether it has the standard page layout
			 * or not.
			 */
			XLogRecPtr	page_lsn = PageGetLSN(regbuf->page);

			needs_backup = (page_lsn <= RedoRecPtr);
			if (!needs_backup)
			{
				if (*fpw_lsn == InvalidXLogRecPtr || page_lsn < *fpw_lsn)
					*fpw_lsn = page_lsn;
			}
		}

		/* Determine if the buffer data needs to included */
		if (regbuf->rdata_len == 0)
			needs_data = false;
		else if ((regbuf->flags & REGBUF_KEEP_DATA) != 0)
			needs_data = true;
		else
			needs_data = !needs_backup;

		bkpb.id = block_id;
		bkpb.fork_flags = regbuf->forkno;
		bkpb.data_length = 0;

		if ((regbuf->flags & REGBUF_WILL_INIT) == REGBUF_WILL_INIT)
			bkpb.fork_flags |= BKPBLOCK_WILL_INIT;

		/*
		 * If needs_backup is true or WAL checking is enabled for current
		 * resource manager, log a full-page write for the current block.
		 */
		include_image = needs_backup || (info & XLR_CHECK_CONSISTENCY) != 0;
```

이미지를 실을 때는 구멍을 계산하고, 구멍 앞뒤 두 조각으로 체인에 붙인다. 압축 갈래는 줄였다.

`access` / `transam` / `xloginsert.c` L649-L786 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L649-L786))

```c
// xloginsert.c L649-L786
		if (include_image)
		{
			const PageData *page = regbuf->page;
			uint16		compressed_len = 0;

			/*
			 * The page needs to be backed up, so calculate its hole length
			 * and offset.
			 */
			if (regbuf->flags & REGBUF_STANDARD)
			{
				/* Assume we can omit data between pd_lower and pd_upper */
				uint16		lower = ((PageHeader) page)->pd_lower;
				uint16		upper = ((PageHeader) page)->pd_upper;

				if (lower >= SizeOfPageHeaderData &&
					upper > lower &&
					upper <= BLCKSZ)
				{
					bimg.hole_offset = lower;
					cbimg.hole_length = upper - lower;
				}
				else
				{
					/* No "hole" to remove */
					bimg.hole_offset = 0;
					cbimg.hole_length = 0;
				}
			}
			else
			{
				/* Not a standard page header, don't try to eliminate "hole" */
				bimg.hole_offset = 0;
				cbimg.hole_length = 0;
			}

			// ... (L685-L695 생략: wal_compression 이면 XLogCompressBackupBlock)

			/*
			 * Fill in the remaining fields in the XLogRecordBlockHeader
			 * struct
			 */
			bkpb.fork_flags |= BKPBLOCK_HAS_IMAGE;

			/* Report a full page image constructed for the WAL record */
			*num_fpi += 1;

			/*
			 * Construct XLogRecData entries for the page content.
			 */
			rdt_datas_last->next = &regbuf->bkp_rdatas[0];
			rdt_datas_last = rdt_datas_last->next;

			bimg.bimg_info = (cbimg.hole_length == 0) ? 0 : BKPIMAGE_HAS_HOLE;

			/*
			 * If WAL consistency checking is enabled for the resource manager
			 * of this WAL record, a full-page image is included in the record
			 * for the block modified. During redo, the full-page is replayed
			 * only if BKPIMAGE_APPLY is set.
			 */
			if (needs_backup)
				bimg.bimg_info |= BKPIMAGE_APPLY;

			// ... (L723-L759 생략: 압축됐으면 압축 방식 비트와 압축본을 체인에)
			else
			{
				bimg.length = BLCKSZ - cbimg.hole_length;

				if (cbimg.hole_length == 0)
				{
					rdt_datas_last->data = page;
					rdt_datas_last->len = BLCKSZ;
				}
				else
				{
					/* must skip the hole */
					rdt_datas_last->data = page;
					rdt_datas_last->len = bimg.hole_offset;

					rdt_datas_last->next = &regbuf->bkp_rdatas[1];
					rdt_datas_last = rdt_datas_last->next;

					rdt_datas_last->data =
						page + (bimg.hole_offset + cbimg.hole_length);
					rdt_datas_last->len =
						BLCKSZ - (bimg.hole_offset + cbimg.hole_length);
				}
			}

			total_len += bimg.length;
		}
```

블록 데이터를 붙이고, 블록 헤더를 scratch 에 쓴다.

`access` / `transam` / `xloginsert.c` L788-L838 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L788-L838))

```c
// xloginsert.c L788-L838
		if (needs_data)
		{
			/*
			 * When copying to XLogRecordBlockHeader, the length is narrowed
			 * to an uint16.  Double-check that it is still correct.
			 */
			Assert(regbuf->rdata_len <= UINT16_MAX);

			/*
			 * Link the caller-supplied rdata chain for this buffer to the
			 * overall list.
			 */
			bkpb.fork_flags |= BKPBLOCK_HAS_DATA;
			bkpb.data_length = (uint16) regbuf->rdata_len;
			total_len += regbuf->rdata_len;

			rdt_datas_last->next = regbuf->rdata_head;
			rdt_datas_last = regbuf->rdata_tail;
		}

		if (prev_regbuf && RelFileLocatorEquals(regbuf->rlocator, prev_regbuf->rlocator))
		{
			samerel = true;
			bkpb.fork_flags |= BKPBLOCK_SAME_REL;
		}
		else
			samerel = false;
		prev_regbuf = regbuf;

		/* Ok, copy the header to the scratch buffer */
		memcpy(scratch, &bkpb, SizeOfXLogRecordBlockHeader);
		scratch += SizeOfXLogRecordBlockHeader;
		if (include_image)
		{
			memcpy(scratch, &bimg, SizeOfXLogRecordBlockImageHeader);
			scratch += SizeOfXLogRecordBlockImageHeader;
			if (cbimg.hole_length != 0 && is_compressed)
			{
				memcpy(scratch, &cbimg,
					   SizeOfXLogRecordBlockCompressHeader);
				scratch += SizeOfXLogRecordBlockCompressHeader;
			}
		}
		if (!samerel)
		{
			memcpy(scratch, &regbuf->rlocator, sizeof(RelFileLocator));
			scratch += sizeof(RelFileLocator);
		}
		memcpy(scratch, &regbuf->block, sizeof(BlockNumber));
		scratch += sizeof(BlockNumber);
	}
```

origin, 상위 XID, 주 데이터 헤더를 쓰고 CRC 와 레코드 헤더를 채운다.

`access` / `transam` / `xloginsert.c` L840-L934 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L840-L934))

```c
// xloginsert.c L840-L934
	/* followed by the record's origin, if any */
	if ((curinsert_flags & XLOG_INCLUDE_ORIGIN) &&
		replorigin_session_origin != InvalidRepOriginId)
	{
		*(scratch++) = (char) XLR_BLOCK_ID_ORIGIN;
		memcpy(scratch, &replorigin_session_origin, sizeof(replorigin_session_origin));
		scratch += sizeof(replorigin_session_origin);
	}

	/* followed by toplevel XID, if not already included in previous record */
	if (IsSubxactTopXidLogPending())
	{
		TransactionId xid = GetTopTransactionIdIfAny();

		/* Set the flag that the top xid is included in the WAL */
		*topxid_included = true;

		*(scratch++) = (char) XLR_BLOCK_ID_TOPLEVEL_XID;
		memcpy(scratch, &xid, sizeof(TransactionId));
		scratch += sizeof(TransactionId);
	}

	/* followed by main data, if any */
	if (mainrdata_len > 0)
	{
		// ... (L865-L880 생략: 주 데이터가 255 바이트를 넘으면 4바이트 길이 헤더)
		else
		{
			*(scratch++) = (char) XLR_BLOCK_ID_DATA_SHORT;
			*(scratch++) = (uint8) mainrdata_len;
		}
		rdt_datas_last->next = mainrdata_head;
		rdt_datas_last = mainrdata_last;
		total_len += mainrdata_len;
	}
	rdt_datas_last->next = NULL;

	hdr_rdt.len = (scratch - hdr_scratch);
	total_len += hdr_rdt.len;

	/*
	 * Calculate CRC of the data
	 *
	 * Note that the record header isn't added into the CRC initially since we
	 * don't know the prev-link yet.  Thus, the CRC will represent the CRC of
	 * the whole record in the order: rdata, then backup blocks, then record
	 * header.
	 */
	INIT_CRC32C(rdata_crc);
	COMP_CRC32C(rdata_crc, hdr_scratch + SizeOfXLogRecord, hdr_rdt.len - SizeOfXLogRecord);
	for (rdt = hdr_rdt.next; rdt != NULL; rdt = rdt->next)
		COMP_CRC32C(rdata_crc, rdt->data, rdt->len);

	// ... (L908-L919 생략: 레코드 최대 크기 검사)

	/*
	 * Fill in the fields in the record header. Prev-link is filled in later,
	 * once we know where in the WAL the record will be inserted. The CRC does
	 * not include the record header yet.
	 */
	rechdr->xl_xid = GetCurrentTransactionIdIfAny();
	rechdr->xl_tot_len = (uint32) total_len;
	rechdr->xl_info = info;
	rechdr->xl_rmid = rmid;
	rechdr->xl_prev = InvalidXLogRecPtr;
	rechdr->xl_crc = rdata_crc;

	return &hdr_rdt;
}
```

## 동작 흐름

```text
 L567  rechdr = hdr_scratch 앞 24바이트               XLogRecord 자리
 L580  wal_consistency_checking 대상 rmgr 면 XLR_CHECK_CONSISTENCY

 L589  for 등록된 블록마다
 L605    REGBUF_FORCE_IMAGE      -> 무조건 이미지
 L607    REGBUF_NO_IMAGE         -> 이미지 없음
 L609    full_page_writes 꺼짐   -> 이미지 없음
 L618    아니면 page_lsn = PageGetLSN(page)
 L620      needs_backup = page_lsn <= RedoRecPtr
 L623      아니면 fpw_lsn = 그런 페이지들 중 가장 작은 LSN    [08] 이 다시 확인할 값
 L629    needs_data = 데이터가 있고, (KEEP_DATA 이거나 이미지가 없을 때)
 L640    REGBUF_WILL_INIT 면 BKPBLOCK_WILL_INIT
 L647    include_image = needs_backup 또는 일관성 검사
 L658      표준 페이지면 hole = [pd_lower, pd_upper)
 L701      BKPBLOCK_HAS_IMAGE, L704 num_fpi++
 L712      구멍이 있으면 BKPIMAGE_HAS_HOLE, L721 needs_backup 이면 BKPIMAGE_APPLY
 L762      length = BLCKSZ - hole_length
 L772      체인 += page[0, hole_offset), page[hole_offset + hole_length, BLCKSZ)
 L788    needs_data 면 BKPBLOCK_HAS_DATA, data_length, 체인 += 블록 데이터
 L808    앞 블록과 같은 릴레이션이면 BKPBLOCK_SAME_REL (RelFileLocator 생략)
 L818    scratch += 블록 헤더 4, (이미지면) 이미지 헤더 5, (SAME_REL 아니면) RelFileLocator 12, BlockNumber 4

 L841  origin 이 설정된 세션이면 XLR_BLOCK_ID_ORIGIN + 2바이트
 L850  하위 트랜잭션의 상위 XID 를 아직 안 남겼으면 XLR_BLOCK_ID_TOPLEVEL_XID + 4바이트
 L863  주 데이터가 있으면 XLR_BLOCK_ID_DATA_SHORT(255) + 길이 1바이트, 체인 += 주 데이터
 L892  hdr_rdt.len = scratch 에 쓴 길이
 L903  CRC = scratch[24..] + 체인 전체 (레코드 헤더 24바이트는 아직 제외)
 L926  xl_xid, xl_tot_len, xl_info, xl_rmid, xl_prev = 0, xl_crc = 중간 CRC
 L933  return &hdr_rdt                               체인의 머리
```

FPI 판정은 체크포인트와 페이지 LSN 의 대소 비교 하나다. 이유는 소스 README 에 있다. 페이지 쓰기가 원자적이지 않아 찢어진 페이지가 디스크에 남을 수 있으므로, 체크포인트 뒤 첫 변경 때 페이지 전체를 남겨 redo 가 그것부터 복원하게 한다(access/transam/README L424-L435).

```text
 RedoRecPtr = 0/6000028 (마지막 체크포인트의 redo 시작점. 세그먼트 6 의 긴 페이지 헤더 40바이트 바로 뒤)

 페이지   page_lsn (바꾸기 전)  page_lsn <= RedoRecPtr   이미지
 A        0/5FFF000             O                        싣는다. 체크포인트 뒤 처음 바뀐다
 B        0/6000400             X                        안 싣는다. fpw_lsn = 0/6000400
 C        0/0 (new page)        O                        싣는다. 단 INIT_PAGE 면 안 싣는다
                                                         REGBUF_WILL_INIT = 0x04 | NO_IMAGE (xloginsert.h L34) 라 L607 에서 걸린다

 같은 페이지의 두 번째 변경부터는 page_lsn 이 체크포인트 뒤라 이미지가 없다
```

조립된 레코드의 바이트 배치는 아래와 같다. [02] 의 예(int4 두 열 행, 블록 7, FPI 없음)는 63바이트다.

```text
 XLOG_HEAP_INSERT, FPI 없음                                    크기   누계

 XLogRecord                                                     24     24
   xl_tot_len = 63, xl_xid, xl_prev(아직 0), xl_info, xl_rmid = RM_HEAP_ID, 패딩 2, xl_crc
 XLogRecordBlockHeader  id = 0, fork_flags = 0x20 (HAS_DATA),    4      28
                        data_length = 14
 RelFileLocator         spcOid, dbOid, relNumber                12      40
 BlockNumber            7                                        4      44
 XLogRecordDataHeaderShort  id = 255, data_length = 3            2      46
 block 0 data           xl_heap_header 5 + tuple data 9         14      60
 main data              xl_heap_insert (offnum, flags)           3      63

 헤더 부분(hdr_rdt) = 24 + 4 + 12 + 4 + 2 = 46   나머지는 체인
 [09] 가 예약할 때 MAXALIGN(63) = 64
```

같은 레코드에 FPI 가 실리면 블록 데이터 14바이트가 빠지고 이미지가 들어간다. [05] 의 블록 3 (행 95개, pd_lower 404, pd_upper 5152)이면 이렇다.

```text
 XLOG_HEAP_INSERT, FPI 있음 (wal_compression 꺼짐)              크기   누계

 XLogRecord                                                     24     24
 XLogRecordBlockHeader  fork_flags = 0x10 (HAS_IMAGE)            4      28
                        data_length = 0  (needs_data = !needs_backup = false)
 XLogRecordBlockImageHeader                                      5      33
   length = 8192 - 4748 = 3444, hole_offset = 404,
   bimg_info = HAS_HOLE | APPLY
 RelFileLocator                                                 12      45
 BlockNumber            3                                        4      49
 XLogRecordDataHeaderShort                                       2      51
 image part 1           page[0, 404)                           404     455
 image part 2           page[5152, 8192)                      3040    3495
 main data              xl_heap_insert                           3    3498

 hole_length = pd_upper - pd_lower = 5152 - 404 = 4748
 xl_tot_len = 3498, 예약은 MAXALIGN(3498) = 3504
```

## 결과가 쓰이는 곳

```text
 &hdr_rdt (XLogRecData 체인)
      --> [08] XLogInsertRecord 가 체인을 따라 WAL 버퍼에 복사한다
 *fpw_lsn
      --> [08] 이 삽입 잠금 아래에서 RedoRecPtr 와 다시 비교한다 (xlog.c L848-L850)
 *num_fpi
      --> pgWalUsage.wal_fpi (pg_stat_wal, EXPLAIN (WAL))
 rechdr->xl_crc (중간값)
      --> [08] 이 xl_prev 를 넣은 뒤 헤더를 더해 마무리한다
```

## 다루지 않는 것

FPI 압축(`XLogCompressBackupBlock`, `BKPIMAGE_COMPRESS_*`, `XLogRecordBlockCompressHeader`), 일관성 검사(`wal_consistency_checking`), 255 바이트를 넘는 주 데이터의 긴 헤더, 복제 origin 과 상위 XID 블록, 레코드 최대 크기(`XLogRecordMaxSize`)는 조립의 곁가지라 요약만 했다. 레코드 형식의 정의 자체는 구조 편 "WAL 레코드 형식"의 주제다.
