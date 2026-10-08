# GetScanValue

상위: [HNSW 검색](../README.md)

**ORDER BY 의 오른쪽 값(검색 벡터)을 스캔 키에서 꺼내는 함수다.** 값이 NULL 이면 NULL 포인터를 그대로 쓰고, 연산자 클래스에 정규화 함수가 있으면(코사인 계열) 인덱스에 저장된 값과 같은 방식으로 단위 벡터로 바꾼다. 저장 쪽 [HnswFormIndexValue](../../operators-index-am/06_HnswFormIndexValue/README.md)의 짝이다.

## 위치

`src` / `hnswscan.c` L97-L119 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L97-L119))

## 실제 코드

```c
// hnswscan.c L94-L119
/*
 * Get scan value
 */
static Datum
GetScanValue(IndexScanDesc scan)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;
	Datum		value;

	if (scan->orderByData->sk_flags & SK_ISNULL)
		value = PointerGetDatum(NULL);
	else
	{
		value = scan->orderByData->sk_argument;

		/* Value should not be compressed or toasted */
		Assert(!VARATT_IS_COMPRESSED(DatumGetPointer(value)));
		Assert(!VARATT_IS_EXTENDED(DatumGetPointer(value)));

		/* Normalize if needed */
		if (so->support.normprocinfo != NULL)
			value = HnswNormValue(so->typeInfo, so->support.collation, value);
	}

	return value;
}
```

## 동작 흐름

```text
 GetScanValue(scan)                                  L97
   L103  sk_flags 에 SK_ISNULL 이면 value = NULL
           -> 모든 거리가 0 이 된다 (HnswLoadElementImpl L560-L561)
   L107  아니면 value = sk_argument
           L110  압축·TOAST 되지 않았다고 가정 (Assert)
           L114  normprocinfo 가 있으면 HnswNormValue -> l2_normalize
   L118  return value
```

```text
 ORDER BY embedding <=> '[3,4]'  (vector_cosine_ops)

 sk_argument   [3, 4]
 정규화        [0.6, 0.8]      저장된 원소들도 같은 방식으로 정규화돼 있다
 비교          -(원소 . [0.6, 0.8])   FUNCTION 1 = vector_negative_inner_product
```

크기가 0 인 검색 벡터(`'[0,0]'`)는 여기서 따로 막지 않는다. `l2_normalize` 는 노름이 0 이면 0 벡터를 돌려주므로(vector.c L804-L805) 모든 원소와의 음의 내적이 0 이 된다.

## 결과가 쓰이는 곳

```text
 value
      --> [05] GetScanItems 가 HnswCheckDim 으로 차원을 확인하고 so->q.value 에 둔다
      --> 이후 모든 거리 계산의 한쪽 인자
```

## 다루지 않는 것

정규화 결과는 `tmpCtx` 에 할당되어 rescan 때 함께 사라진다(`hnswgettuple` 이 L198 에서 컨텍스트를 바꾼 뒤 이 함수를 부른다). 그 밖의 메모리 수명은 다루지 않았다.
