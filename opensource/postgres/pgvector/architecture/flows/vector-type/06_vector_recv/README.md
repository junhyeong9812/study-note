# vector_recv

상위: [확장 로드와 vector 타입](../README.md)

**`vector` 의 이진 입력 함수이고, 짝인 `vector_send` 와 함께 본다.** 이진 형식은 메모리 모양에서 길이 헤더만 뺀 것이다. `int16` 차원 수, `int16` 예비 칸(항상 0), 그리고 `float4` 를 차원 수만큼 네트워크 바이트 순서로 늘어놓는다. 받는 쪽은 텍스트 입력과 같은 차원·원소 검사를 다시 한다.

## 위치

`src` / `vector.c` L375-L403 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L375-L403))

## 실제 코드

```c
// vector.c L371-L403
/*
 * Convert external binary representation to internal representation
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector_recv);
Datum
vector_recv(PG_FUNCTION_ARGS)
{
	StringInfo	buf = (StringInfo) PG_GETARG_POINTER(0);
	int32		typmod = PG_GETARG_INT32(2);
	Vector	   *result;
	int16		dim;
	int16		unused;

	dim = pq_getmsgint(buf, sizeof(int16));
	unused = pq_getmsgint(buf, sizeof(int16));

	CheckDim(dim);
	CheckExpectedDim(typmod, dim);

	if (unused != 0)
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("expected unused to be 0, not %d", unused)));

	result = InitVector(dim);
	for (int i = 0; i < dim; i++)
	{
		result->x[i] = pq_getmsgfloat4(buf);
		CheckElement(result->x[i]);
	}

	PG_RETURN_POINTER(result);
}
```

내보내는 쪽이다.

`src` / `vector.c` L409-L422 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L409-L422))

```c
// vector.c L409-L422
Datum
vector_send(PG_FUNCTION_ARGS)
{
	Vector	   *vec = PG_GETARG_VECTOR_P(0);
	StringInfoData buf;

	pq_begintypsend(&buf);
	pq_sendint16(&buf, vec->dim);
	pq_sendint16(&buf, vec->unused);
	for (int i = 0; i < vec->dim; i++)
		pq_sendfloat4(&buf, vec->x[i]);

	PG_RETURN_BYTEA_P(pq_endtypsend(&buf));
}
```

## 동작 흐름

```text
 vector_send(vec)                                   L409
   L415  pq_begintypsend
   L416  pq_sendint16(dim)
   L417  pq_sendint16(unused)
   L418  dim 번  pq_sendfloat4(x[i])
   L421  bytea 로 돌려준다

 vector_recv(buf, oid, typmod)                      L375
   L384  dim    = pq_getmsgint(buf, 2)
   L385  unused = pq_getmsgint(buf, 2)
   L387  CheckDim(dim)               1..16000
   L388  CheckExpectedDim(typmod, dim)
   L390  unused != 0 -> "expected unused to be 0"
   L395  InitVector(dim)
   L396  dim 번  x[i] = pq_getmsgfloat4, CheckElement(x[i])   NaN, inf 거절
```

```text
 [1,2,3] 의 이진 표현 (16 바이트, 빅 엔디언)

 +-------+--------+-------------+-------------+-------------+
 | 00 03 | 00 00  | 3F 80 00 00 | 40 00 00 00 | 40 40 00 00 |
 | dim   | unused | 1.0         | 2.0         | 3.0         |
 +-------+--------+-------------+-------------+-------------+
   2       2        4             4             4

 메모리 모양(20 바이트)과 비교하면 앞의 4바이트 길이 헤더만 없다
```

`unused` 칸을 받을 때 0 이 아니면 거절하는 것은 그 칸을 나중에 쓰려고 남겨 두었기 때문이다(헤더 주석 "reserved for future use, always zero", vector.h L22).

## 결과가 쓰이는 곳

```text
 vector_recv 의 Vector
      --> COPY ... (FORMAT binary) 로 읽은 값, 확장 쿼리 프로토콜의 이진 매개변수
 vector_send 의 bytea
      --> 이진 결과 형식을 요청한 클라이언트, COPY TO (FORMAT binary)
```

## 다루지 않는 것

`pq_getmsgint`, `pq_sendfloat4` 같은 PostgreSQL 메시지 버퍼 함수의 내부는 다루지 않는다. `sparsevec_recv` 는 `dim`, `nnz`, `unused` 뒤에 인덱스 배열과 값 배열을 차례로 싣는다.
