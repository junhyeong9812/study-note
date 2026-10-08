# vector_out

상위: [확장 로드와 vector 타입](../README.md)

**`vector` 를 `'[1,2,3]'` 문자열로 바꾸는 출력 함수다.** 출력 버퍼를 원소 수로 한 번에 넉넉히 잡고, 원소마다 `float_to_shortest_decimal_bufn` 으로 "다시 읽었을 때 같은 float 가 되는 가장 짧은 십진 표기"를 써 넣는다.

## 위치

`src` / `vector.c` L290-L326 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L290-L326))

## 실제 코드

```c
// vector.c L283-L326
#define AppendChar(ptr, c) (*(ptr)++ = (c))
#define AppendFloat(ptr, f) ((ptr) += float_to_shortest_decimal_bufn((f), (ptr)))

/*
 * Convert internal representation to textual representation
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector_out);
Datum
vector_out(PG_FUNCTION_ARGS)
{
	Vector	   *vector = PG_GETARG_VECTOR_P(0);
	int			dim = vector->dim;
	char	   *buf;
	char	   *ptr;

	/*
	 * Need:
	 *
	 * dim * (FLOAT_SHORTEST_DECIMAL_LEN - 1) bytes for
	 * float_to_shortest_decimal_bufn
	 *
	 * max(dim - 1, 0) bytes for separator
	 *
	 * 3 bytes for [, ], and \0
	 */
	buf = (char *) palloc(add_size(mul_size(FLOAT_SHORTEST_DECIMAL_LEN, dim), 3));
	ptr = buf;

	AppendChar(ptr, '[');

	for (int i = 0; i < dim; i++)
	{
		if (i > 0)
			AppendChar(ptr, ',');

		AppendFloat(ptr, vector->x[i]);
	}

	AppendChar(ptr, ']');
	*ptr = '\0';

	PG_FREE_IF_COPY(vector, 0);
	PG_RETURN_CSTRING(buf);
}
```

## 동작 흐름

```text
 vector_out(vector)                                 L290
   L293  PG_GETARG_VECTOR_P(0)       TOAST 됐으면 여기서 펼친다
   L308  buf = palloc(FLOAT_SHORTEST_DECIMAL_LEN * dim + 3)
           원소당 최대 길이 * dim  +  '['  ']'  '\0'
   L311  '['
   L313  for i in 0..dim-1
           L315  i > 0 이면 ','
           L318  AppendFloat  -> ptr 가 쓴 길이만큼 전진     L284
   L321  ']'
   L322  '\0'
   L324  PG_FREE_IF_COPY             펼친 복사본이면 해제
   L325  return buf
```

```text
 버퍼 크기 계산 (주석 L298-L307)

 필요한 것
   원소마다  FLOAT_SHORTEST_DECIMAL_LEN - 1 바이트  (bufn 은 '\0' 을 쓰지 않는다)
   구분자    dim - 1 개의 ','
   괄호와 끝 '[' ']' '\0' 3 바이트
 잡는 것
   FLOAT_SHORTEST_DECIMAL_LEN * dim + 3
   원소마다 1바이트 여유가 생기고, 그 여유가 dim - 1 개의 ',' 를 덮는다
```

```text
 출력 예

 저장 값 x = {1.0, 2.5, 0.1f}
   1.0   -> "1"
   2.5   -> "2.5"
   0.1f  -> "0.1"    float 로 0.1 에 가장 가까운 값을 다시 만드는 가장 짧은 표기
 결과 "[1,2.5,0.1]"   공백 없음
```

## 결과가 쓰이는 곳

```text
 cstring
      --> 클라이언트에 텍스트 결과로 나간다
      --> PrintVector (L332) 가 디버깅 로그에 쓴다
      --> 다시 vector_in 에 넣으면 같은 값이 된다 (최단 왕복 표기)
```

## 다루지 않는 것

`float_to_shortest_decimal_bufn`(PostgreSQL `common/shortest_dec.h`)의 내부는 다루지 않는다. `halfvec_out` 과 `sparsevec_out`(sparsevec.c L426, `{1:1,3:2}/5` 꼴)은 같은 틀에 표기만 다르다.
