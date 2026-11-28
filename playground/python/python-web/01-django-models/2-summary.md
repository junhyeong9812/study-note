# python/python-web/01 — Django Models (모델 정의) — 정리 (힌트)

> 출처 — study-site 항목 `python/django-models`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/django-models.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Django 모델은 「장부 양식 설계도」다.**
사무실에서 장부를 새로 만들 때는 먼저 양식을 정한다.
양식에는 칸 머리(이름 · 날짜 · 금액)가 있다.
칸마다 「몇 글자까지」「비워도 되나」「처음에 무엇을 적어 두나」 같은 규칙도 붙는다.
양식이 바뀌면 인쇄소에 변경 공문을 보낸다.
그래야 실제 장부의 칸이 바뀐다.
Django 모델도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 장부 양식 한 장 | `models.Model` 을 상속한 클래스 하나 (`Post`) |
| 칸 머리와 칸 규칙 | 필드 (`title = models.CharField(max_length=200)`) |
| 장부의 한 줄 | 모델 객체 하나 (게시글 한 편) |
| 「이 줄은 저 장부의 몇 번 줄을 본다」 | 관계 필드 (`ForeignKey` 등) |
| 양식 맨 위의 안내문(정렬 순서, 장부 이름) | `class Meta` |
| 변경 공문 쓰기 | `makemigrations` |
| 인쇄소가 실제 장부를 고침 | `migrate` |
| 실제 장부 | 데이터베이스 테이블 |

```text
  models.py (파이썬 클래스)
        │  makemigrations  → 변경 공문(마이그레이션 파일) 작성
        ▼
  migrations/0001_….py
        │  migrate          → DB 에 적용
        ▼
  DB 테이블  blog_category, blog_post, …
```

> **모델** — DB 테이블 하나를 파이썬 클래스 하나로 적은 것.\
> 예: `class Post(models.Model): ...` 가 게시글 테이블이 된다.

> **ORM** — 테이블을 클래스로, 한 줄을 객체로 다루게 해 주는 층.\
> 예: SQL 대신 `Post.objects.create(...)` 로 한 줄을 넣는다.

## 이 주제가 답하려는 질문

1. 파이썬 클래스 하나가 어떻게 DB 테이블이 되고, 클래스를 고친 것은 언제 DB 에 반영되나?
2. 칸(필드)마다 어떤 종류의 값을, 어떤 규칙(비움 · 기본값 · 유일 · 자동 시각)으로 담나?
3. 테이블끼리는 어떻게 이어지고, 한쪽이 지워지면 다른 쪽은 어떻게 되나?
4. 정렬 · 테이블 이름 · 인덱스 · 제약 같은 「표 전체의 규칙」은 어디에 적나?

## 동작 방식

### (1) 클래스 → 테이블, 필드 → 칸

**언제 쓰나** — 저장할 대상이 생길 때마다 모델 클래스를 하나 만든다.
게시글 · 카테고리 · 태그 · 작성자가 각각 하나씩이다.

```text
class Category(models.Model):              테이블 blog_category
    name = CharField(max_length=100)  ──▶   name        varchar(100)
    order = IntegerField(default=0)   ──▶   order       integer
    is_active = BooleanField(...)     ──▶   is_active   bool
                                            id          (자동 기본 키)
```

- 클래스가 `models.Model` 을 상속하면 Django 는 그것을 테이블 하나로 본다.
- 클래스 속성으로 적은 필드 하나가 칸 하나가 된다.
- 필드 클래스의 종류(`CharField` · `IntegerField` …)가 칸에 담을 값의 종류를 정한다.
- 기본 키 칸 `id` 는 적지 않아도 Django 가 붙인다 (원본에 근거 없음 — 추론).

원본에 나온 필드 종류는 다음과 같다.

| 필드 | 담는 것 | 원본의 설명 |
|---|---|---|
| `CharField` | 짧은 문자열 | `max_length` 가 필수다 |
| `SlugField` | URL 에 쓰는 짧은 문자열 | a-z, 0-9, `-`, `_` |
| `TextField` | 긴 텍스트 | 길이 제한이 없다 |
| `BooleanField` | `True` / `False` | |
| `IntegerField` | 정수 | |
| `PositiveIntegerField` | 0 이상 정수 | 조회수처럼 음수가 없는 값 |
| `DecimalField` | 정확한 소수 | `max_digits` = 총 자릿수, `decimal_places` = 소수점 아래 자릿수 |
| `DateTimeField` | 날짜와 시각 | `auto_now_add` · `auto_now` 를 줄 수 있다 |
| `URLField` | URL | 형식 검증이 자동이다 |
| `ImageField` | 업로드한 이미지 | Pillow 가 필요하다, `upload_to` 는 `MEDIA_ROOT` 아래 경로 |

> **슬러그** — URL 에 넣기 좋게 줄인 문자열.\
> 예: 제목 「Django 첫걸음」의 슬러그 `django-first-step`.

### (2) 필드 옵션 — null · blank · default · unique · 자동 시각

**언제 쓰나** — 칸마다 「비워도 되나」「처음 값은」「겹쳐도 되나」를 정할 때 쓴다.

```text
description = TextField(blank=True, default='')
                         │            │
                         │            └─ 값을 안 주면 '' 이 들어간다
                         └─ 폼에서 비워 둬도 검증을 통과한다

category = ForeignKey(..., null=True, blank=True)
                            │           │
                            │           └─ 폼 단계: 빈 값 허용
                            └─ DB 단계: NULL 저장 허용

created_at = DateTimeField(auto_now_add=True)   처음 만들 때 한 번만 지금 시각
updated_at = DateTimeField(auto_now=True)       save() 할 때마다 지금 시각
```

- `null=True` 는 DB 칸에 NULL 을 넣어도 된다는 뜻이다(DB 단계).
- `blank=True` 는 폼에서 빈 값을 받아도 된다는 뜻이다(폼 단계).
- 둘은 서로 다른 층의 규칙이라 하나만 줘서는 다른 하나가 따라오지 않는다.
- `default` 는 값을 안 줬을 때 채울 값이다.
- `unique=True` 는 같은 값이 두 줄에 들어가지 못하게 한다.
- `auto_now_add=True` 는 객체가 처음 저장될 때 한 번만 지금 시각을 넣는다.
- `auto_now=True` 는 `save()` 가 불릴 때마다 지금 시각으로 바꾼다.

> **NULL** — DB 에서 「값이 없음」을 뜻하는 특별한 표시.\
> 예: 아직 게시하지 않은 글의 `published_at`.

### (3) 선택지 — TextChoices

**언제 쓰나** — 칸에 들어갈 값이 정해진 몇 개 중 하나일 때 쓴다(초안 · 게시됨 · 보관됨).

```text
class Status(models.TextChoices):
    DRAFT     = 'DF', '초안'        ◀ 저장값 'DF', 사람이 볼 이름 '초안'
    PUBLISHED = 'PB', '게시됨'
    ARCHIVED  = 'AR', '보관됨'

status = CharField(max_length=2,
                   choices=Status.choices,   ◀ 허용 값 목록
                   default=Status.DRAFT)     ◀ 기본은 'DF'
```

- 멤버마다 앞 값은 DB 에 저장되는 값이고, 뒤 값은 사람에게 보일 이름(`label`)이다.
- 저장값이 두 글자라 `max_length=2` 면 충분하다.
- `Status.choices` 는 (저장값, 이름) 쌍의 목록이고, `choices=` 에 넘기면 폼과 관리자 화면이 이 목록으로 선택 상자를 그린다.
- 코드에서는 `'PB'` 같은 문자열 대신 `Status.PUBLISHED` 로 쓴다 — 오타가 나면 이름 오류로 바로 드러나므로 원본은 이것을 「타입 안전」이라 부른다.
- 원본은 `TextChoices` 를 Django 3.0 이상의 기능으로 적는다.

> **열거형** — 정해진 값 몇 개에 이름을 붙여 묶은 것.\
> 예: `Status.DRAFT`, `Status.PUBLISHED`.

### (4) 관계 — ForeignKey · OneToOneField · ManyToManyField 와 역참조

**언제 쓰나** — 한 테이블의 줄이 다른 테이블의 줄을 가리켜야 할 때 쓴다.

```text
 Author ─1───N─ Post          ForeignKey      post.author  /  author.posts.all()
 Category ─1──N─ Post         ForeignKey      post.category / category.posts.all()
 User ─1───1─ Author          OneToOneField   author.user  /  user.author_profile
 Post ─N───M─ Tag             ManyToManyField post.tags.all() / tag.posts.all()
                                     │
                                     └─ Post 와 Tag 사이에 중간 테이블이 자동으로 생긴다
```

- `ForeignKey` 는 다대일이다 — 글 여러 편이 작성자 한 명을 가리킨다.
- `OneToOneField` 는 일대일이다 — 사용자 하나에 프로필 하나.
- `ManyToManyField` 는 다대다다 — 글 하나에 태그 여럿, 태그 하나에 글 여럿. 이 연결은 Django 가 자동으로 만든 중간 테이블에 저장된다.
- 관계 필드를 적은 쪽에서는 속성으로 상대를 바로 읽는다(`post.author`).
- 반대쪽에서 거꾸로 찾는 것을 역참조라 한다. `related_name` 이 그 이름이다.
- `related_name` 을 적지 않으면 역참조 이름은 `post_set` 꼴(소문자 모델 이름 + `_set`)이 된다 (원본에 근거 없음 — 추론). 적어 두면 `author.posts.all()` 처럼 읽기 쉽다 — 원본 팁의 「역참조가 직관적이다」가 이 뜻이다.
- `'auth.User'` 처럼 상대 모델을 「앱 이름.모델 이름」 문자열로 적을 수도 있다. 다른 앱의 모델을 import 하지 않고 가리킬 때 쓴다.

> **역참조** — 관계 필드가 없는 쪽에서 자기를 가리키는 줄들을 찾는 것.\
> 예: `author.posts.all()` 은 이 작성자를 가리키는 글 전부.

> **중간 테이블** — 다대다 연결을 (글 id, 태그 id) 쌍으로 적어 두는 테이블.\
> 예: 글 3번에 태그 1·2번이면 두 줄이 생긴다.

### (5) on_delete — 가리키던 대상이 지워질 때

**언제 쓰나** — `ForeignKey` · `OneToOneField` 를 쓸 때 언제나 쓴다. 필수 인자다.

```text
 작성자 A 삭제 ──▶ Post.author (CASCADE)     ──▶ A 의 글도 함께 삭제
 카테고리 C 삭제 ─▶ Post.category (SET_NULL) ──▶ 글은 남고 category 칸이 NULL
 User U 삭제 ────▶ Author.user (CASCADE)     ──▶ U 의 프로필도 삭제
                                               (프로필이 지워지니 그 글도 CASCADE 로 삭제)
```

원본이 정리한 선택지는 여섯이다.

| 값 | 원본의 설명 |
|---|---|
| `CASCADE` | 참조 객체가 지워지면 함께 지운다 — 가장 흔하다 |
| `SET_NULL` | NULL 로 바꾼다 — `null=True` 가 필요하다 |
| `SET_DEFAULT` | 기본값으로 바꾼다 — `default` 가 필요하다 |
| `PROTECT` | 참조 객체의 삭제를 막는다 — `ProtectedError` |
| `RESTRICT` | Django 3.1+, `PROTECT` 와 비슷하지만 `CASCADE` 와 함께 가능 |
| `DO_NOTHING` | 아무것도 안 한다 — DB 단계 에러가 날 수 있다 |

- 삭제가 연쇄로 번질 수 있다 — `User` → `Author` → `Post` 처럼 `CASCADE` 가 이어지면 맨 위 하나를 지울 때 아래가 다 지워진다.
- `SET_NULL` 은 칸에 NULL 을 적는 동작이라 그 칸이 `null=True` 여야 한다.

### (6) Meta — 표 전체의 규칙

**언제 쓰나** — 칸 하나가 아니라 테이블 전체에 걸린 설정을 적을 때 쓴다.

```text
class Meta:
    ordering = ['order', 'name']      ◀ 따로 정하지 않으면 order 오름차순, 같으면 name 오름차순
    db_table = 'blog_category'        ◀ 테이블 이름을 직접 정함
    verbose_name = '카테고리'          ◀ 관리자 화면 등에 보일 이름

class Meta:                          (Post)
    ordering = ['-published_at']      ◀ '-' = 내림차순 → 최신 글 먼저
    indexes = [Index(fields=['-published_at']), Index(fields=['slug'])]
    constraints = [UniqueConstraint(fields=['slug', 'published_at'], name=...)]
```

- `ordering` 은 조회할 때 따로 정렬을 주지 않으면 쓰이는 기본 정렬이다. 앞 칸부터 비교하고, 같으면 다음 칸으로 넘어간다.
- 칸 이름 앞의 `-` 는 내림차순이다.
- `db_table` 은 테이블 이름을 정한다.
- `verbose_name` · `verbose_name_plural` 은 사람에게 보일 단수 · 복수 이름이다.
- `indexes` 는 DB 인덱스를 명시해 만든다 — 원본은 「조회 성능 향상」이라 적는다.
- `constraints` 는 DB 단계 제약이다. `UniqueConstraint` 는 적힌 칸들의 값 조합이 겹치지 못하게 한다.

> **인덱스** — 특정 칸으로 빨리 찾도록 DB 가 따로 만들어 두는 찾아보기.\
> 예: `slug` 인덱스가 있으면 슬러그로 글을 찾을 때 표 전체를 훑지 않는다.

> **제약** — DB 가 스스로 지키는 규칙.\
> 예: (slug, published_at) 조합이 겹치는 줄은 넣을 수 없다.

### (7) 모델 메서드 — `__str__` · `get_absolute_url` · `publish`

**언제 쓰나** — 객체를 글자로 보이거나, 객체의 URL 을 만들거나, 여러 칸을 한 번에 바꾸는 일을 객체 스스로 하게 할 때 쓴다.

```text
post.publish()
  ├─ self.status = Status.PUBLISHED      → 'PB'
  ├─ self.published_at = timezone.now()  → 지금 시각
  └─ self.save()
        ├─ DB 에 바뀐 칸들을 씀
        └─ updated_at(auto_now) 도 지금 시각으로 갱신, created_at 은 그대로
```

- `__str__` 은 관리자 화면 · 디버깅에서 객체를 보일 문자열이다.
- `get_absolute_url` 은 객체의 표준 URL 이다. `reverse('category-detail', kwargs={'slug': ...})` 가 URL 이름과 인자로 실제 경로를 만든다. 관리자의 「사이트에서 보기」 등에 쓰인다.
- `publish` 처럼 「상태 바꾸기 + 시각 기록 + 저장」을 메서드 하나에 묶는 것을 원본은 「비즈니스 로직 캡슐화」라 부른다.
- `timezone.now()` 는 시간대 정보가 붙은 지금 시각을 준다. 원본은 `USE_TZ=True` 를 권한다.

### (8) 마이그레이션 — 클래스 변경을 DB 로

**언제 쓰나** — 모델을 처음 만들었을 때, 그리고 필드를 더하거나 바꿀 때마다 쓴다.

```text
 models.py 수정
   │  python manage.py makemigrations blog   → blog/migrations/0001_….py 생성 (아직 DB 는 그대로)
   │  python manage.py sqlmigrate blog 0001  → 그 파일이 낼 SQL 을 보기만 함
   │  python manage.py showmigrations        → 적용된 것 / 안 된 것 표시
   ▼
   python manage.py migrate                  → DB 에 실제로 적용
```

- `makemigrations` 는 모델과 지난 마이그레이션을 비교해 바뀐 점을 파일로 적는다.
- `migrate` 가 그 파일을 DB 에 실행한다. 이 단계 전에는 테이블이 바뀌지 않는다.
- 순서는 언제나 `makemigrations` → `migrate` 다.

> **마이그레이션** — 모델의 변경을 DB 구조 변경으로 옮기는 기록 파일과 그 적용.\
> 예: `Post` 에 `excerpt` 를 더하면 「칸 추가」 마이그레이션이 생긴다.

## 문법 — 형태와 규칙

```python
from django.db import models

class Note(models.Model):
    class Kind(models.TextChoices):
        MEMO = 'MM', '메모'
        TODO = 'TD', '할 일'

    title = models.CharField(max_length=100)
    kind = models.CharField(max_length=2, choices=Kind.choices, default=Kind.MEMO)
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
```

- 모델은 `models.Model` 을 상속한 클래스다.
- 필드는 `이름 = models.필드종류(옵션...)` 꼴의 클래스 속성이다.
- `CharField` · `SlugField` 에는 `max_length` 를 준다.
- `DecimalField` 에는 `max_digits` 와 `decimal_places` 를 준다.
- `ForeignKey` · `OneToOneField` 의 첫 인자는 상대 모델(클래스 또는 `'앱.모델'` 문자열), `on_delete` 는 필수다.
- `ManyToManyField` 에는 `on_delete` 가 없다.
- 선택지는 모델 안에 `TextChoices` 를 상속한 클래스로 적고, 필드에 `choices=…choices` 로 넘긴다.
- 표 전체의 설정은 모델 안의 `class Meta:` 에 적는다.
- 클래스를 고친 뒤에는 `makemigrations` → `migrate`.

| `Meta` 옵션 | 하는 일 |
|---|---|
| `ordering` | 기본 정렬 (`-` 는 내림차순) |
| `db_table` | 테이블 이름 |
| `verbose_name` / `verbose_name_plural` | 사람에게 보일 이름 |
| `indexes` | DB 인덱스 |
| `constraints` | DB 제약 (`UniqueConstraint` 등) |

## 어디서 틀리나

### 1. `auto_now_add` 와 `auto_now` 를 바꿔 쓴다

`auto_now_add` 는 생성할 때 한 번만, `auto_now` 는 `save()` 할 때마다 갱신된다.
생성 시각 칸에 `auto_now` 를 주면 수정할 때마다 「생성 시각」이 바뀌어 버린다.
`publish()` 처럼 안에서 `save()` 를 부르는 메서드도 `updated_at` 을 바꾼다는 점을 놓치기 쉽다.

### 2. `on_delete` 를 빼먹거나, `SET_NULL` 에 `null=True` 를 안 준다

`on_delete` 는 필수 인자이고 `CASCADE` 가 가장 흔하다.
`SET_NULL` 은 칸에 NULL 을 적는 동작이라 `null=True` 없이는 쓸 수 없다.
`SET_DEFAULT` 도 같은 까닭으로 `default` 가 있어야 한다.
`CASCADE` 는 연쇄로 번진다 — 사용자 하나를 지우면 프로필과 그 글까지 사라진다.

### 3. `null` 과 `blank` 를 같은 것으로 본다

`null=True` 는 DB 단계, `blank=True` 는 폼 단계 규칙이다.
`excerpt = CharField(..., blank=True)` 는 폼에서 비워도 되지만 DB 칸은 NULL 을 받지 않는다 — 빈 값은 빈 문자열로 들어간다 (원본에 근거 없음 — 추론).
`category` 처럼 「폼에서도 비우고 DB 에도 NULL 을 넣는」 칸은 둘 다 준다.

### 4. `related_name` 을 안 적고 역참조 이름을 헤맨다

`related_name` 을 명시하면 역참조가 직관적이다.
`Post` 는 `author` · `category` · `tags` 셋 다 `related_name='posts'` 를 쓰지만 상대 모델이 서로 달라(`Author` · `Category` · `Tag`) 겹치지 않는다.
한 모델이 같은 상대를 두 번 가리키면 역참조 이름이 겹치므로 그때는 서로 다른 `related_name` 이 꼭 필요하다 (원본에 근거 없음 — 추론).

### 5. `TextChoices` 의 저장값과 이름을 헷갈린다

DB 에 들어가는 것은 앞 값(`'DF'`)이고, `'초안'` 은 보일 이름(`label`)이다.
그래서 `max_length=2` 로 충분하다.
코드에서 `'PB'` 를 직접 쓰지 말고 `Status.PUBLISHED` 를 쓴다 — 원본 팁의 「타입 안전」이 이것이다.

### 6. `unique_for_date` 와 `unique_slug_per_date` 의 이름을 그대로 믿는다

**원본의 주장** — 「`unique_for_date`: `published_at` 날짜 기준 slug 유일성 보장」, 그리고 이름이 `unique_slug_per_date` 인 `UniqueConstraint(fields=['slug', 'published_at'])`.
**왜 의심스러운가**
- `unique_for_date` 는 모델 검증(폼 · `full_clean()`) 단계에서 검사하는 규칙이라 그냥 `save()` 하면 검사되지 않는 것으로 안다 (확인 필요).
- `UniqueConstraint` 는 `published_at` 칸의 값, 곧 **날짜와 시각 전체**를 비교한다. 같은 날 다른 시각이면 (slug, published_at) 조합이 달라 DB 는 막지 않는다. 이름은 「날짜마다 하나」지만 실제로는 「시각마다 하나」다 (원본에 근거 없음 — 추론).
- `published_at` 은 `null=True` 라 초안끼리는 둘 다 NULL 이다. 여러 DB 가 NULL 끼리는 같다고 보지 않아 같은 슬러그의 초안 여럿이 통과할 수 있다 (확인 필요).

### 7. 클래스만 고치고 DB 에 반영하지 않는다

필드를 더해도 `makemigrations` → `migrate` 를 거치기 전에는 테이블에 칸이 없다.
`makemigrations` 만 하면 파일만 생기고 DB 는 그대로다.

### 8. `DecimalField` 의 자릿수를 잘못 읽는다

`max_digits=3, decimal_places=2` 는 총 세 자리 중 두 자리가 소수점 아래라는 뜻이다 — 정수부는 한 자리뿐이라 담을 수 있는 가장 큰 값은 9.99 다.
**원본의 주장** — `default=0.00`.
**왜 의심스러운가** — `0.00` 은 파이썬 `float` 다. `DecimalField` 에는 `Decimal('0.00')` 을 주는 편이 정확한 소수라는 필드의 뜻과 맞는다 (확인 필요).

### 9. `ImageField` 의 준비물을 잊는다

원본 주석대로 `ImageField` 는 Pillow 가 있어야 한다.
`upload_to='avatars/'` 는 `MEDIA_ROOT` 아래 경로다.

### 10. `__str__` 이 빈 글자를 낼 수 있다

`Author.__str__` 은 `self.user.get_full_name()` 을 돌려준다.
사용자의 이름 칸이 비어 있으면 빈 문자열이 되어 관리자 화면에서 무엇인지 알아보기 어렵다 (원본에 근거 없음 — 추론).

### 11. `RESTRICT` 와 `PROTECT`

원본은 `RESTRICT` 를 「Django 3.1+, `PROTECT` 와 유사하지만 `CASCADE` 와 함께 가능」이라 적는다.
「함께 가능」이 정확히 어떤 경우인지는 원본에 설명이 없다 (확인 필요).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `blank=True` 면 폼에서 빈 값을 받는다 | Django 의 폼 · 모델 검증 |
| `null=True` 면 칸에 NULL 을 넣을 수 있다 | Django 가 만든 DB 칸 정의 → DB 가 지킨다 |
| `unique=True` · `UniqueConstraint` 가 겹침을 막는다 | 마이그레이션이 만든 DB 제약 → DB 가 지킨다 |
| `unique_for_date` 가 날짜별 유일성을 지킨다 | Django 모델 검증뿐 (확인 필요) — DB 는 모른다 |
| `auto_now_add` · `auto_now` 가 시각을 채운다 | Django 의 `save()` — DB 기능이 아니다 |
| `on_delete=CASCADE` 가 함께 지운다 | Django 가 지울 대상을 모아 지운다 (확인 필요) |
| `DO_NOTHING` 이면 DB 에러가 날 수 있다 | DB 의 외래 키 제약 |
| `ordering` 의 NULL 위치(초안 글이 앞이냐 뒤냐) | DB 마다 다르다 (확인 필요) |
| `TextChoices` · `RESTRICT` 가 쓰이는 버전 | 원본의 주장(3.0+ · 3.1+) — Django 버전이 정한다 |
| `ImageField` 의 이미지 처리 | Pillow 라이브러리 |
| `TextChoices` 멤버가 `'DF'` 와 같은 문자열로 쓰인다 | Django 가 파이썬 `enum` 위에 만든 클래스 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 짧은 이름 · 제목 | `CharField(max_length=…)` | 길이 없는 `CharField` |
| 길이를 모르는 본문 | `TextField` | 아주 큰 `max_length` 의 `CharField` |
| 돈 · 평점처럼 정확한 소수 | `DecimalField` | 오차가 나는 실수 칸 |
| 생성 시각 | `auto_now_add=True` | `auto_now=True` |
| 수정 시각 | `auto_now=True` | `auto_now_add=True` |
| 값이 몇 개 중 하나 | `TextChoices` + `choices=` | 코드 곳곳의 `'PB'` 같은 맨 문자열 |
| 글 N : 작성자 1 | `ForeignKey` | `ManyToManyField` |
| 사용자 1 : 프로필 1 | `OneToOneField` | `ForeignKey` (프로필이 여럿 생길 수 있음) |
| 글 N : 태그 M | `ManyToManyField` | 글 테이블에 태그 칸 여러 개 |
| 부모가 사라지면 자식도 의미 없음 | `CASCADE` | `SET_NULL` |
| 부모가 사라져도 자식은 남아야 함 | `SET_NULL` (+ `null=True`) | `CASCADE` |
| 참조 중이면 삭제를 막아야 함 | `PROTECT` | `CASCADE` |
| 모델을 고쳤다 | `makemigrations` → `migrate` | DB 를 손으로 고치기 |

## 핵심 문장

1. **모델 클래스 하나 = 테이블 하나, 필드 하나 = 칸 하나**이고, 클래스의 변경은 `makemigrations` → `migrate` 를 거쳐야 DB 에 닿는다.
2. **`null` 은 DB 단계, `blank` 는 폼 단계** 규칙이고, `auto_now_add` 는 생성 때 한 번, `auto_now` 는 `save()` 마다다.
3. **관계는 세 가지** — `ForeignKey`(N:1) · `OneToOneField`(1:1) · `ManyToManyField`(N:M, 중간 테이블) — 이고, `related_name` 이 반대쪽에서 찾는 이름이다.
4. **`on_delete` 는 필수**이며, 가리키던 대상이 지워질 때 함께 지울지(`CASCADE`) · 비울지(`SET_NULL`) · 막을지(`PROTECT`)를 정한다.
5. **표 전체의 규칙은 `Meta`** 에 — 기본 정렬 · 테이블 이름 · 인덱스 · 제약 — 적는다.

## 관련 자료

- [django-views](../02-django-views/2-summary.md)
- `django-orm` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [django-forms](../04-django-forms/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `django-models`

## 용어 풀이

- **모델** — DB 테이블 하나를 적은 파이썬 클래스.
- **ORM** — 테이블을 클래스로, 한 줄을 객체로 다루게 해 주는 층.
- **필드** — 모델의 칸 하나, 칸에 담을 값의 종류와 규칙을 정한다.
- **슬러그** — URL 에 넣기 좋게 줄인 문자열.
- **NULL** — DB 에서 「값이 없음」을 뜻하는 표시.
- **`null` / `blank`** — DB 단계 NULL 허용 / 폼 단계 빈 값 허용.
- **`auto_now_add` / `auto_now`** — 처음 저장 때 한 번 / `save()` 마다 지금 시각을 넣는 옵션.
- **`TextChoices`** — 저장값과 보일 이름을 묶은 선택지 열거형.
- **`label`** — 선택지 멤버의 사람에게 보일 이름.
- **열거형** — 정해진 값 몇 개에 이름을 붙여 묶은 것.
- **`ForeignKey`** — 다대일 관계 필드.
- **`OneToOneField`** — 일대일 관계 필드.
- **`ManyToManyField`** — 다대다 관계 필드, 중간 테이블을 자동으로 만든다.
- **중간 테이블** — 다대다 연결을 id 쌍으로 적는 테이블.
- **역참조** — 관계 필드가 없는 쪽에서 자기를 가리키는 줄을 찾는 것.
- **`related_name`** — 역참조에 쓸 이름.
- **`on_delete`** — 가리키던 대상이 지워질 때의 처리 방식.
- **`Meta`** — 모델 안에서 표 전체의 설정을 적는 클래스.
- **인덱스** — 특정 칸으로 빨리 찾도록 DB 가 만드는 찾아보기.
- **제약** — DB 가 스스로 지키는 규칙.
- **`reverse`** — URL 이름과 인자로 실제 경로를 만드는 함수.
- **마이그레이션** — 모델 변경을 DB 구조 변경으로 옮기는 기록 파일과 그 적용.

## 더 들어가면

- `QuerySet.update()` 는 `save()` 를 거치지 않아 `auto_now` 칸이 갱신되지 않는다고 알려져 있다 (확인 필요).
- 조회수를 늘릴 때는 `F('view_count') + 1` 로 DB 안에서 더하면 동시에 여러 요청이 와도 값이 덜 꼬인다 (확인 필요).
- `'auth.User'` 를 직접 적기보다 `settings.AUTH_USER_MODEL` 을 쓰면 사용자 모델을 바꿔 끼운 프로젝트에서도 동작한다 (확인 필요).
- 다대다 연결에 「태그 단 시각」 같은 칸을 더하려면 `ManyToManyField(through=…)` 로 중간 테이블을 직접 모델로 적는다 (확인 필요).
- 여러 모델이 `created_at` · `updated_at` 을 똑같이 가지면 `Meta: abstract = True` 인 부모 모델에 모아 상속할 수 있다 (확인 필요).
- 글 목록에서 `post.author` 를 매번 읽으면 질의가 여러 번 나가므로 `select_related` · `prefetch_related` 로 한꺼번에 가져온다 (확인 필요).
- 새 Django 버전에는 `on_delete` 를 DB 의 외래 키 동작으로 맡기는 선택지가 생겼다는 이야기가 있다 (확인 필요).
