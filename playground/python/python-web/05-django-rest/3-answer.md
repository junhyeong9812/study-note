# python/python-web/05 — Django REST Framework (DRF) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 250자 본문은 203자, 200자 본문은 `...` 없이 그대로

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 250자 본문 → 앞 200자 + `'...'` = 203자.
- 딱 200자 본문 → `len(...) > 200` 이 거짓이라 본문 그대로 나가고 `...` 는 붙지 않는다.

**왜 그런가**

조건식은 `+` 보다 늦게 묶여 `(content[:200] + '...') if len(content) > 200 else content` 로 읽힌다.
조건은 `>=` 가 아니라 `>` 라서 200자는 「넘는」 경우가 아니다.
그래서 `summary` 는 200자가 아니라 최대 203자가 된다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 8」.

### 2. 공개글만, 한 페이지 20개, POST 는 거절

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 목록에는 `status='PB'` 인 글만 들어간다.
- 한 페이지에는 최대 20개가 담긴다.
- `POST` 는 권한 검사에서 거절된다.

**왜 그런가**

비로그인이면 `request.user.is_authenticated` 가 거짓이라 `get_queryset()` 이 `status='PB'` 로 거른다.
`PostViewSet` 에는 `pagination_class` 가 없고 `CustomPagination` 도 어디에도 붙어 있지 않으므로, 전역 설정의 `PageNumberPagination` 과 `PAGE_SIZE: 20` 이 쓰인다.
`IsAuthenticatedOrReadOnly` 는 읽기(GET)는 누구에게나, 쓰기(POST)는 로그인한 사용자에게만 허용한다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (7)」 · 「어디서 틀리나 1」.

### 3. `POST /api/posts/{pk}/publish/` 와 `GET /api/posts/popular/` — GET 으로 publish 는 안 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `publish` → `POST /api/posts/{pk}/publish/`.
- `popular` → `GET /api/posts/popular/`.
- `GET /api/posts/5/publish/` → `publish` 는 실행되지 않고 405(Method Not Allowed)로 거절된다.

**왜 그런가**

`detail=True` 는 객체 하나를 대상으로 하므로 URL 에 `{pk}` 가 들어가고, `detail=False` 는 컬렉션 대상이라 `{pk}` 가 없다.
URL 끝 조각은 메서드 이름이고, 앞은 `api/` + 등록 접두어 `posts` 다.
`methods=['post']` 이므로 GET 은 받지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (6)」.

### 4. 읽을 때와 쓸 때 편한 모양이 다르기 때문이다

응답에서는 태그의 `id` 와 `name` 을 함께 보여 주는 중첩 객체 목록이 쓸모 있다.
입력에서는 클라이언트가 태그 PK 숫자 목록만 보내면 된다.
그래서 `tags` 는 `read_only=True` 중첩 시리얼라이저, `tag_ids` 는 `write_only=True` 인 `PrimaryKeyRelatedField` 로 두고 `source='tags'` 로 같은 모델 필드에 잇는다.
`tags` 는 읽기 전용이라 입력으로 보내도 무시되므로 입력 창구가 따로 있어야 한다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 6」.

### 5. 작성자를 클라이언트에게 맡기면 남의 이름으로 글을 쓸 수 있기 때문이다

작성자는 「요청을 보낸 로그인 사용자」로 정해져야 하는 값이다.
본문에서 받으면 클라이언트가 아무 작성자 id 나 넣을 수 있다.
`perform_create` 는 저장 직전에 불리므로 `serializer.save(author=self.request.user.author_profile)` 로 서버가 아는 사용자를 끼워 넣는다.
이것이 `request.user` 를 주입하는 흔한 패턴이다.
근거: 2-summary 「동작 방식 (3)」.

### 6. 두 필드를 함께 봐야 하는 규칙이라서 — PATCH 에서는 헛걸린다

`validate_<필드>()` 는 그 필드 값 하나만 받으므로 `status` 를 검사하면서 `category` 를 볼 수 없다.
`validate(data)` 는 필드 검사가 끝난 dict 전체를 받아 교차 검증을 할 수 있다.

PATCH 로 `status` 만 보내면 통과하지 못한다.
부분 수정에서는 `data` 에 이번에 보낸 필드만 있어서 `data.get('category')` 가 `None` 이 되고, 글에 이미 카테고리가 있어도 오류가 난다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 3」.

### 7. 지금은 막히지 않는다 — 붙여도 목록에서는 불리지 않는다

현재 권한은 `IsAuthenticatedOrReadOnly` 하나뿐이라 로그인만 했으면 PUT 이 통과한다.
`IsAuthorOrReadOnly` 는 정의만 되어 있고 뷰에 붙어 있지 않다.

붙인 뒤에도 `has_object_permission` 은 `get_object()` 안에서 불리므로, `get_object()` 를 부르지 않는 `list` 에서는 불리지 않는다.
목록에서 가릴 글은 `get_queryset()` 에서 걸러야 한다.
근거: 2-summary 「동작 방식 (8)」, 「어디서 틀리나 1」 · 「어디서 틀리나 2」.

### 8. 검색도 페이지 정보도 빠진다

`popular` 는 `get_queryset()` 만 부르고 `filter_queryset()` 을 부르지 않으므로 `?search=django` 는 무시된다.
`paginate_queryset()` 도 부르지 않으므로 응답은 `count` · `next` 없이 직렬화된 글 목록(최대 10개)뿐이다.
`get_queryset()` 은 거치므로 비로그인이면 공개글만 대상이 되는 것은 유지된다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 4」.

### 9. 글마다 관련 데이터를 따로 조회하는 N+1 문제를 막는다

`author_name` 은 `author.user` 를, `category_name` 은 `category` 를, `tags` 는 태그 목록을 읽는다.
미리 가져오지 않으면 글 하나를 직렬화할 때마다 이 관계를 읽으려고 쿼리가 더 나간다.
`select_related` 는 외래키 관계를 JOIN 으로 한 번에, `prefetch_related` 는 다대다 태그를 별도 쿼리 한 번으로 모아 가져와 쿼리 수를 줄인다.
근거: 2-summary 「동작 방식 (3)」.

### 10. 뷰의 속성이 이긴다 — 인증은 「누구인가」, 권한은 「해도 되나」

전역 `DEFAULT_PERMISSION_CLASSES` 는 기본값이고, 뷰에 `permission_classes` 가 있으면 그 뷰에서는 뷰의 값이 쓰인다.
인증은 세션 쿠키나 토큰을 보고 요청 보낸 사람(`request.user`)을 정한다.
권한은 그렇게 정해진 사람이 이 동작을 해도 되는지 판단한다.
그래서 권한 클래스(`IsAuthenticatedOrReadOnly`)는 인증 결과(로그인 여부)를 보고 결정한다.
근거: 2-summary 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 게시글 API 한 벌 만들기 — Serializer 부터 권한까지

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 태그 `id` · `name` | `TagSerializer.Meta` 의 `model = Tag` · `fields = ['id', 'name']` |
| 2. 응답 전용 중첩 태그 | `tags = TagSerializer(many=True, read_only=True)` |
| 3. 입력 전용 태그 PK 목록 | `tag_ids = serializers.PrimaryKeyRelatedField(…, write_only=True, source='tags')` |
| 4. 작성자 이름 · 카테고리 이름 | `author_name` · `category_name` 의 `source=` · `read_only=True` |
| 5. 요약 계산 | `summary = serializers.SerializerMethodField()` + `get_summary()` |
| 6. 읽기 전용 세 필드 | `Meta.read_only_fields` |
| 7. 제목 5자 검사 | `validate_title()` |
| 8. 게시 상태 카테고리 검사 | `validate()` |
| 9. CRUD + 조인 쿼리셋 | `class PostViewSet(viewsets.ModelViewSet)` · `queryset = …select_related(…).prefetch_related('tags')` · `serializer_class` |
| 10. 읽기 누구나 · 쓰기 로그인 | `permission_classes = [permissions.IsAuthenticatedOrReadOnly]` |
| 11. 필터 · 검색 · 정렬 | `filter_backends` · `filterset_fields` · `search_fields` · `ordering_fields` · `ordering` |
| 12. 작성자 주입 | `perform_create()` 의 `serializer.save(author=…)` |
| 13. 비로그인 공개글만 | `get_queryset()` 의 `qs.filter(status='PB')` |
| 14. 게시 액션 | `@action(detail=True, methods=['post'])` · `publish()` |
| 15. 인기 글 액션 | `@action(detail=False, methods=['get'])` · `popular()` |
| 16. 라우터 등록 · `api/` | `router.register('posts', PostViewSet, basename='post')` · `path('api/', include(router.urls))` |
| 17. 전역 설정 | `REST_FRAMEWORK` 의 네 묶음 키 |
| 18. 커스텀 페이지네이션 | `CustomPagination` 의 세 속성 + `get_paginated_response()` |
| 19. 작성자만 수정 | `IsAuthorOrReadOnly.has_object_permission()` |
| 20. 정리 출력 | 파일 끝 `print(...)` 일곱 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/django-rest.py`

```python
# [웹 프레임워크] Django REST Framework (DRF)
# 설명: DRF Serializer, ViewSet, Router, 인증, 페이지네이션
# 팁: ModelSerializer는 모델 필드를 자동 매핑하고 create/update를 자동 구현한다. ViewSet은 list/create/retrieve/update/destroy를 한 번에 제공한다. perform_create()에서 request.user를 주입하는 패턴이 일반적이다. @action으로 /posts/{id}/publish 같은 커스텀 엔드포인트를 추가한다.

# Django REST Framework (DRF) - API 구축
# pip install djangorestframework

# === 1. Serializer 정의 ===
# serializers: 모델 <-> JSON 변환과 유효성 검사 담당
from rest_framework import serializers

# ModelSerializer: 모델 기반 자동 직렬화 클래스
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        # fields: 직렬화에 포함할 필드 목록
        fields = ['id', 'name']


class PostSerializer(serializers.ModelSerializer):
    # 중첩 시리얼라이저
    # many=True: 리스트 직렬화, read_only: 응답에만 포함 (입력 X)
    tags = TagSerializer(many=True, read_only=True)
    # PrimaryKeyRelatedField: PK 리스트로 입력 받기, source로 모델 필드와 연결
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
        write_only=True, source='tags'
    )
    # 추가 필드
    # source: 모델의 다른 속성/메서드를 매핑 (점 표기법으로 깊은 접근)
    author_name = serializers.CharField(
        source='author.user.get_full_name', read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    # SerializerMethodField - get_<field> 메서드로 동적 값 생성
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'status', 'author', 'author_name',
            'category', 'category_name',
            'tags', 'tag_ids',
            'view_count', 'summary',
            'published_at', 'created_at', 'updated_at'
        ]
        # read_only_fields: 응답에만 포함되고 입력 시 무시
        read_only_fields = ['view_count', 'created_at', 'updated_at']

    # SerializerMethodField의 동적 값을 계산하는 메서드
    def get_summary(self, obj):
        return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content

    # validate_<필드>: 단일 필드 추가 검증
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError('제목은 5자 이상이어야 합니다.')
        return value

    # validate(): 다중 필드 교차 검증
    def validate(self, data):
        if data.get('status') == 'PB' and not data.get('category'):
            raise serializers.ValidationError(
                '게시 상태의 글은 카테고리가 필요합니다.'
            )
        return data


# === 2. ViewSet ===
# viewsets: CRUD 액션을 클래스 하나로 처리하는 뷰 추상화
from rest_framework import viewsets, status, permissions, filters
# action: ViewSet에 커스텀 엔드포인트 추가하는 데코레이터
from rest_framework.decorators import action
# Response: DRF 응답 객체 (콘텐츠 협상 자동 처리)
from rest_framework.response import Response
# DjangoFilterBackend: ?field=value 형태 필터링 지원
from django_filters.rest_framework import DjangoFilterBackend


# ModelViewSet: list/create/retrieve/update/partial_update/destroy 자동 제공
class PostViewSet(viewsets.ModelViewSet):
    """게시글 CRUD API ViewSet"""
    # queryset: 기본 데이터셋, 성능 최적화 위해 select/prefetch 적용
    queryset = Post.objects.select_related(
        'author__user', 'category'
    ).prefetch_related('tags')
    serializer_class = PostSerializer
    # IsAuthenticatedOrReadOnly: 읽기는 누구나, 쓰기는 인증 필요
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # 필터링, 검색, 정렬
    # filter_backends: 활성화할 필터 백엔드 리스트
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # filterset_fields: 정확한 매칭 필터 (?status=PB)
    filterset_fields = ['status', 'category', 'author']
    # search_fields: 부분 매칭 검색 대상 필드
    search_fields = ['title', 'content']          # ?search=django
    # ordering_fields: 정렬 가능한 필드 (?ordering=-view_count)
    ordering_fields = ['created_at', 'view_count'] # ?ordering=-view_count
    ordering = ['-created_at']                     # 기본 정렬

    # perform_create: 생성 직전 추가 처리 (request.user 주입 패턴)
    def perform_create(self, serializer):
        serializer.save(author=self.request.user.author_profile)

    # get_queryset: 동적 쿼리셋 (요청 컨텍스트 기반 필터)
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            qs = qs.filter(status='PB')  # 비로그인: 공개글만
        return qs

    # 커스텀 액션
    # detail=True: 단일 객체 대상 (/posts/{pk}/publish/)
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        # get_object(): 현재 pk의 객체 (권한 검사 포함)
        post = self.get_object()
        post.publish()
        return Response({'status': '게시됨'})

    # detail=False: 컬렉션 대상 (/posts/popular/)
    @action(detail=False, methods=['get'])
    def popular(self, request):
        popular = self.get_queryset().order_by('-view_count')[:10]
        # get_serializer로 컨텍스트 포함된 시리얼라이저 가져오기
        serializer = self.get_serializer(popular, many=True)
        return Response(serializer.data)


# === 3. Router ===
# DefaultRouter: ViewSet의 URL 패턴 자동 생성 + API 루트 뷰 제공
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# register: ViewSet을 URL prefix와 매핑
router.register('posts', PostViewSet, basename='post')
# /api/posts/          (list, create)
# /api/posts/{id}/     (retrieve, update, destroy)
# /api/posts/{id}/publish/  (custom action)
# /api/posts/popular/       (custom action)

# urls.py
from django.urls import path, include
urlpatterns = [
    # router.urls를 include로 포함
    path('api/', include(router.urls)),
]


# === 4. 인증 설정 (settings.py) ===
# REST_FRAMEWORK: DRF 전역 설정 dict
REST_FRAMEWORK = {
    # DEFAULT_AUTHENTICATION_CLASSES: 요청 인증 방식 (여러 개 동시 가능)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # 기본 권한 정책
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # 페이지네이션 클래스 + 페이지 크기
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Throttling: 요청 빈도 제한
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}


# === 5. 커스텀 Pagination ===
# PageNumberPagination 상속하여 응답 구조/페이지 크기 커스터마이즈
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10
    # 클라이언트가 ?page_size= 로 동적 조절 가능
    page_size_query_param = 'page_size'
    max_page_size = 100

    # 페이지네이션 응답 형식 오버라이드
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


# === 6. 커스텀 Permission ===
# BasePermission 상속, has_permission/has_object_permission 구현
from rest_framework.permissions import BasePermission

class IsAuthorOrReadOnly(BasePermission):
    # 객체 수준 권한: 특정 인스턴스에 대한 접근 제어
    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        if request.method in permissions.SAFE_METHODS:
            return True
        # 본인 글만 수정/삭제
        return obj.author.user == request.user


print("Django REST Framework 핵심 정리")
print("="*50)
print("Serializer: 직렬화/역직렬화 + 유효성 검사")
print("ModelSerializer: 모델 기반 자동 시리얼라이저")
print("ViewSet: CRUD 자동 생성, @action으로 커스텀 엔드포인트")
print("Router: ViewSet URL 자동 매핑")
print("인증: Session, Token, JWT")
print("페이지네이션: PageNumber, LimitOffset, Cursor")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `rest_framework` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- `ModelSerializer` 는 `Meta` 만 적어도 필드 매핑과 `create` · `update` 를 해 주고, 나머지는 `read_only` · `write_only` · `source` 로 모양을 다듬는다.
- 하나의 필드 검사는 `validate_<필드>()`, 둘 이상을 엮는 검사는 `validate()` 에 둔다.
- 요청마다 달라지는 일(작성자 주입, 보이는 범위)은 `perform_create` · `get_queryset` 훅에 둔다.
- `@action` 의 `detail` 이 URL 의 `{pk}` 유무를, `methods` 가 받을 HTTP 메서드를 정한다.
- `CustomPagination` · `IsAuthorOrReadOnly` 는 이 정답에서 정의만 되어 있다 — 실제로 쓰려면 뷰의 `pagination_class` · `permission_classes` 나 전역 설정에 넣어야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `rest_framework` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
