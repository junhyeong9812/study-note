# python/python-web/01 — Django Models (모델 정의) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `'PB'` 가 되고, `published_at` 과 `updated_at` 이 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `status` 칸에는 `'PB'` 가 들어 있다.
- `published_at` 은 `None` 에서 `publish()` 를 부른 시각으로 바뀐다.
- `updated_at` 도 그 시각 무렵으로 바뀐다.
- `created_at` 은 하루 전 생성 시각 그대로다.

**왜 그런가**
- `publish()` 는 `self.status = self.Status.PUBLISHED` 로 저장값 `'PB'` 를 넣는다.
- 이어서 `self.published_at = timezone.now()` 로 지금 시각을 넣는다.
- 마지막 `self.save()` 가 불리면 `auto_now=True` 인 `updated_at` 이 지금 시각으로 갱신된다.
- `auto_now_add=True` 인 `created_at` 은 처음 저장할 때 한 번만 채워지므로 그대로다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「동작 방식 (7)」.

### 2. `django` → `web` → `python`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
['django', 'web', 'python']
```

**왜 그런가**
- `ordering = ['order', 'name']` 은 먼저 `order` 오름차순으로 줄을 세운다.
- `order` 가 0 인 `web` · `django` 가 앞, 1 인 `python` 이 뒤다.
- `order` 가 같은 두 줄은 다음 칸 `name` 오름차순으로 비교해 `django` 가 `web` 앞이다.
- 근거: 2-summary 「동작 방식 (6)」.

### 3. 저장값은 `'DF'`, `label` 은 `'초안'`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `status` 를 주지 않았으므로 기본값 `Status.DRAFT` 가 쓰이고, DB 칸에 들어갈 글자는 `'DF'` 다.
- `b` 는 `'초안'` 이다.

**왜 그런가**
- `status` 는 `default=Status.DRAFT` 다.
- `TextChoices` 멤버 `DRAFT = 'DF', '초안'` 의 앞 값이 저장값, 뒤 값이 `label` 이다.
- 그래서 칸 길이는 `max_length=2` 로 충분하다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 4. `SET_NULL` 은 칸에 NULL 을 적는 동작이라 DB 칸이 NULL 을 받아야 한다

- 카테고리가 지워지면 `SET_NULL` 은 글의 `category` 칸을 NULL 로 바꾼다.
- `null=True` 가 없으면 그 칸은 NULL 을 받지 않으니 이 동작이 성립하지 않는다.
- 원본 메모도 「`SET_NULL`: NULL로 설정 (null=True 필요)」라 적는다.
- `blank=True` 는 폼 단계 규칙이라 이 문제를 풀어 주지 못한다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 2」.

### 5. 작성자 쪽에서 글을 찾는 이름을 `posts` 로 정해 준다

- `related_name` 은 관계 필드가 없는 쪽(작성자)에서 자기를 가리키는 줄을 찾을 때 쓰는 역참조 이름이다.
- `related_name='posts'` 덕에 `author.posts.all()` 로 그 작성자의 글 전부를 읽는다.
- 적지 않으면 `post_set` 꼴의 이름이 되어 원본 팁의 「역참조가 직관적이다」에서 멀어진다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 6. 폼에서 비우는 것은 되고, DB 의 NULL 은 허용되지 않는다

- `blank=True` 는 폼 단계 규칙이라 폼에서 빈 값을 받아 검증을 통과한다.
- `null=True` 가 없으므로 DB 칸은 NULL 을 받지 않는다.
- 두 규칙은 층이 달라 하나를 줘도 다른 하나가 따라오지 않는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 7. 생기지 않는다 — `migrate` 까지 해야 한다

- `makemigrations` 는 바뀐 점을 마이그레이션 파일로 적을 뿐 DB 는 건드리지 않는다.
- 그 파일을 DB 에 실제로 실행하는 것은 `migrate` 다.
- 순서는 언제나 `makemigrations` → `migrate` 다.
- 근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 7」.

### 8. 막지 않는다 — 제약은 날짜가 아니라 시각 전체를 비교한다

- `UniqueConstraint(fields=['slug', 'published_at'])` 는 두 칸 값의 조합이 겹치는지 본다.
- `published_at` 은 날짜와 시각을 함께 담으므로 오전 9시와 오후 3시는 다른 값이다.
- 그래서 조합이 달라 DB 는 두 글을 모두 받는다 — 제약 이름 `unique_slug_per_date` 와 실제 범위가 어긋난다 (원본에 근거 없음 — 추론).
- 날짜 단위 검사를 하는 `unique_for_date` 는 Django 검증 단계의 규칙이라 DB 가 지키는 것이 아니다 (확인 필요).
- 근거: 2-summary 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

### 9. `ForeignKey` 는 「다」 쪽 테이블의 칸에, `ManyToManyField` 는 따로 생긴 중간 테이블에

- `ForeignKey` 는 다대일이라 글 테이블의 `author` 칸 하나가 작성자 한 줄을 가리킨다 — 연결은 「다」 쪽(글)에 적힌다.
- `OneToOneField` 도 필드를 적은 쪽(`Author`)에 상대를 가리키는 칸이 생기고, 상대 하나에 하나만 붙는다.
- `ManyToManyField` 는 한 칸으로 여럿을 담을 수 없으므로 Django 가 중간 테이블을 자동으로 만들어 (글 id, 태그 id) 쌍을 줄마다 적는다.
- 근거: 2-summary 「동작 방식 (4)」 (칸 위치 설명은 원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 블로그 앱의 `models.py` 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1–2. 겹치지 않는 `name` · `slug` | `Category.name = CharField(max_length=100, unique=True)` · `slug = SlugField(..., unique=True)` |
| 3. 비울 수 있는 설명 | `description = TextField(blank=True, default='')` |
| 4. 불리언 · 정수 | `is_active = BooleanField(default=True)` · `order = IntegerField(default=0)` |
| 5. 자동 시각 | `created_at = DateTimeField(auto_now_add=True)` · `updated_at = DateTimeField(auto_now=True)` |
| 6. `Category.Meta` | `verbose_name` · `verbose_name_plural` · `ordering = ['order', 'name']` · `db_table = 'blog_category'` |
| 7. `__str__` | `return self.name` |
| 8. 표준 URL | `reverse('category-detail', kwargs={'slug': self.slug})` |
| 9. `Tag` | `name = CharField(max_length=50, unique=True)` · `__str__` |
| 10. 일대일 사용자 | `user = OneToOneField('auth.User', on_delete=models.CASCADE, related_name='author_profile')` |
| 11. 프로필 칸 | `bio = TextField(blank=True)` · `website = URLField(blank=True)` · `avatar = ImageField(upload_to='avatars/', blank=True)` |
| 12. 작성자 이름 | `return self.user.get_full_name()` |
| 13. 선택지 | `class Status(models.TextChoices)` 의 `DRAFT` · `PUBLISHED` · `ARCHIVED` |
| 14. 글 기본 칸 | `title` · `slug = SlugField(max_length=200, unique_for_date='published_at')` · `content` · `excerpt` |
| 15. 상태 칸 | `status = CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)` |
| 16. 작성자 관계 | `author = ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')` |
| 17. 카테고리 관계 | `category = ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')` |
| 18. 태그 관계 | `tags = ManyToManyField(Tag, blank=True, related_name='posts')` |
| 19. 숫자 칸 | `view_count = PositiveIntegerField(default=0)` · `rating = DecimalField(max_digits=3, decimal_places=2, default=0.00)` |
| 20. 날짜 칸 | `published_at = DateTimeField(null=True, blank=True)` · `created_at` · `updated_at` |
| 21. `Post.Meta` | `ordering = ['-published_at']` · `indexes = [...]` · `constraints = [UniqueConstraint(..., name='unique_slug_per_date')]` |
| 22. `__str__` | `return self.title` |
| 23. 게시 | `publish()` 의 `self.status = …PUBLISHED` · `timezone.now()` · `self.save()` |
| 24. 명령 · 선택지 메모 | `# === Migration 명령어 ===` · `# === on_delete 옵션 ===` 주석 묶음 |
| 25. 핵심 정리 | 파일 끝의 `print(...)` 여덟 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/django-models.py`

```python
# [웹 프레임워크] Django Models (모델 정의)
# 설명: Model 정의, 필드 타입, 관계(ForeignKey, ManyToMany), Meta 옵션, migration 개념
# 팁: auto_now_add는 생성 시 한 번만, auto_now는 save() 할 때마다 갱신된다. on_delete는 필수 인자이며 CASCADE가 가장 흔하다. related_name을 명시하면 역참조가 직관적이다. TextChoices를 사용하면 선택지가 타입 안전해진다.

# Django Models - 모델 정의와 관계
# 실행: django-admin startproject mysite && cd mysite && python manage.py startapp blog

# === models.py ===
# models 모듈: Model, Field, 관계 필드 등 ORM 구성요소
from django.db import models
# timezone-aware datetime 유틸 (USE_TZ=True 권장)
from django.utils import timezone
# reverse: URL 이름으로 절대 URL 생성
from django.urls import reverse


# 카테고리 모델: 기본 필드 타입 학습용
class Category(models.Model):
    """카테고리 모델 - 기본 필드 타입 예시"""
    # CharField는 max_length 필수
    name = models.CharField(max_length=100, unique=True)       # 문자열 (필수: max_length)
    # SlugField: URL 친화적 짧은 문자열 (a-z, 0-9, -, _)
    slug = models.SlugField(max_length=100, unique=True)       # URL용 슬러그
    # TextField: 길이 제한 없는 긴 텍스트
    description = models.TextField(blank=True, default='')     # 긴 텍스트 (선택)
    # BooleanField: True/False
    is_active = models.BooleanField(default=True)              # 불리언
    # IntegerField: 정수
    order = models.IntegerField(default=0)                     # 정수
    # auto_now_add: 객체 최초 생성 시 한 번만 현재 시각 자동 입력
    created_at = models.DateTimeField(auto_now_add=True)       # 생성 시각 자동
    # auto_now: save() 호출될 때마다 현재 시각으로 갱신
    updated_at = models.DateTimeField(auto_now=True)           # 수정 시각 자동

    # Meta: 모델 메타정보 (관리자 표시명, 정렬, 인덱스 등)
    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리들'
        ordering = ['order', 'name']        # 기본 정렬
        db_table = 'blog_category'          # 테이블명 지정

    # __str__: 관리자/디버깅 시 표시될 문자열
    def __str__(self):
        return self.name

    # get_absolute_url: 객체의 표준 URL (관리자 "사이트에서 보기" 등에 사용)
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})


# 태그 모델 - ManyToMany 대상
class Tag(models.Model):
    """태그 모델 - ManyToMany 관계용"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# 작성자 모델 - 인증 User와 1:1
class Author(models.Model):
    """작성자 모델 - OneToOne 관계 예시"""
    # OneToOneField: 1:1 관계, 사용자별 단 하나의 프로필
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,     # 유저 삭제 시 함께 삭제
        # related_name: 역참조 시 사용할 이름 (user.author_profile)
        related_name='author_profile'
    )
    bio = models.TextField(blank=True)
    # URLField: URL 형식 검증 자동
    website = models.URLField(blank=True)                      # URL 필드
    # ImageField: 이미지 업로드 (Pillow 필요), upload_to: MEDIA_ROOT 하위 경로
    avatar = models.ImageField(upload_to='avatars/', blank=True)  # 이미지 필드

    def __str__(self):
        return self.user.get_full_name()


# 게시글 모델 - 다양한 관계와 Meta 옵션 종합
class Post(models.Model):
    """게시글 모델 - 다양한 관계와 필드"""
    # TextChoices: enum과 같은 타입 안전한 선택지 (Django 3.0+)
    class Status(models.TextChoices):    # 선택지 열거형 (Django 3.0+)
        DRAFT = 'DF', '초안'
        PUBLISHED = 'PB', '게시됨'
        ARCHIVED = 'AR', '보관됨'

    title = models.CharField(max_length=200)
    # unique_for_date: published_at 날짜 기준 slug 유일성 보장
    slug = models.SlugField(max_length=200, unique_for_date='published_at')
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    # choices 인자에 TextChoices.choices 사용
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    # 관계 필드
    # ForeignKey: 다대일 관계 (post.author -> Author)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,      # 작성자 삭제 시 글도 삭제
        related_name='posts'           # author.posts.all()
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,     # 카테고리 삭제 시 NULL
        # null=True: DB 레벨 NULL 허용, blank=True: 폼 레벨 빈값 허용
        null=True,
        blank=True,
        related_name='posts'
    )
    # ManyToManyField: 중간 테이블 자동 생성
    tags = models.ManyToManyField(      # 다대다 관계
        Tag,
        blank=True,
        related_name='posts'
    )
    # 숫자 필드
    # PositiveIntegerField: 0 이상 정수
    view_count = models.PositiveIntegerField(default=0)
    # DecimalField: 정확한 소수 (max_digits=총자릿수, decimal_places=소수점)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    # 날짜 필드
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 기본 정렬: 최신 게시 글 먼저 ('-' 접두사 = 내림차순)
        ordering = ['-published_at']
        # indexes: DB 인덱스 명시적 생성 (조회 성능 향상)
        indexes = [
            models.Index(fields=['-published_at']),   # 인덱스
            models.Index(fields=['slug']),
        ]
        # constraints: DB 레벨 제약조건
        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'published_at'],
                name='unique_slug_per_date'
            )
        ]

    def __str__(self):
        return self.title

    # 모델 메서드: 비즈니스 로직 캡슐화
    def publish(self):
        # status 변경 + 발행 시각 기록
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save()


# === Migration 명령어 (터미널) ===
# python manage.py makemigrations blog    # 마이그레이션 파일 생성
# python manage.py migrate                # 데이터베이스에 적용
# python manage.py showmigrations         # 마이그레이션 상태 확인
# python manage.py sqlmigrate blog 0001   # SQL 확인

# === on_delete 옵션 ===
# CASCADE:     참조 객체 삭제 시 함께 삭제
# SET_NULL:    NULL로 설정 (null=True 필요)
# SET_DEFAULT: 기본값으로 설정 (default 필요)
# PROTECT:     참조 객체 삭제 방지 (ProtectedError)
# RESTRICT:    Django 3.1+, PROTECT와 유사하지만 CASCADE와 함께 가능
# DO_NOTHING:  아무 것도 안 함 (DB 레벨 에러 가능)

print("Django Model 핵심 정리")
print("="*50)
print("필드 타입: CharField, TextField, IntegerField, BooleanField, ...")
print("관계 필드: ForeignKey(1:N), OneToOneField(1:1), ManyToManyField(N:M)")
print("Meta 옵션: ordering, db_table, indexes, constraints, verbose_name")
print("auto_now_add: 생성 시 자동 / auto_now: 수정 시 자동")
print("TextChoices: 열거형 선택지 정의 (Django 3.0+)")
print("makemigrations -> migrate 순서로 DB 반영")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 모델 넷은 각자 테이블 하나가 되고, `Post` 와 `Tag` 사이에는 다대다 연결용 중간 테이블이 하나 더 생긴다.
- `on_delete` 는 관계마다 뜻에 맞춰 고른다 — 작성자 · 사용자는 `CASCADE`, 카테고리는 글을 남기려고 `SET_NULL`(+ `null=True`).
- `Post` 의 세 관계가 모두 `related_name='posts'` 여도 상대 모델이 달라 역참조 이름이 겹치지 않는다.
- `publish()` 의 `save()` 는 `updated_at` 까지 갱신한다는 점을 놓치지 않는다.
- `unique_for_date` 와 `unique_slug_per_date` 는 이름과 달리 지키는 범위가 다르다 — 2-summary 「어디서 틀리나 6」을 다시 본다.
- 모델을 다 쓴 뒤에는 `makemigrations` → `migrate` 를 거쳐야 DB 에 테이블이 생긴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
