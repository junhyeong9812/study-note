# python/python-web/07 — Flask RESTful API (marshmallow, JWT) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `id` · `username` · `email` 이 들어가고 `password` 는 빠진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`user` 는 `{'id': (새 번호), 'username': 'kim', 'email': 'kim@ex.com'}` 꼴이고, 상태 코드는 201 이다.
`password` 키는 없다.

**왜 그런가**
`dump()` 는 응답을 만드는 쪽이다.
`id` 는 `dump_only` 라 응답에 나오고, 값은 저장(commit) 뒤 DB 가 정한 번호다.
`password` 는 `load_only` 라 요청에서만 받고 응답에는 실리지 않는다.
`username` · `email` 은 옵션이 없어 양쪽 다 쓰인다.
근거: 2-summary 「동작 방식 (2)」의 표, 「어디서 틀리나 1」.

### 2. 제목은 바뀌고 본문은 그대로, 상태는 200

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`title` 은 `'새 제목'`, `content` 는 `'본문'`, 상태 코드는 200 이다.

**왜 그런가**
`partial=True` 라 `required=True` 인 `content` 가 빠져도 검증 오류가 아니다.
보낸 `title` 은 1~200자 규칙을 통과한다.
`data` 에는 `title` 만 있으므로 `data.get('content', post.content)` 는 원래 값을 돌려준다.
반환이 dict 하나라 상태 코드를 적지 않았고, 그래서 200 이다.
근거: 2-summary 「동작 방식 (5)」, 「동작 방식 (1)」.

### 3. 만들어지지 않는다 — refresh 토큰은 그 문을 통과하지 못한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`@jwt_required()` 가 요청을 거절해 `post` 메서드 본문이 실행되지 않고, 글은 만들어지지 않는다.
거절 때의 상태 코드는 라이브러리 기본 처리가 정한다. (확인 필요)

**왜 그런가**
`@jwt_required()` 는 access 토큰을 요구하고, `@jwt_required(refresh=True)` 는 refresh 토큰만 받는다.
refresh 토큰은 새 access 를 받는 데만 쓰도록 문이 나뉘어 있다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 3」.

### 4. DB 가 새도 비밀번호 원문이 드러나지 않게 하려고

해시는 되돌릴 수 없는 지문이라, `password_hash` 열을 봐도 원래 비밀번호를 알 수 없다.
서버는 원문을 알 필요가 없고 「입력한 것이 저장된 해시와 맞는가」만 확인하면 되므로 `check_password_hash` 로 비교한다.
근거: 2-summary 「동작 방식 (3)」, 「언제 쓰고 언제 안 쓰나」의 비밀번호 저장 줄.

### 5. 토큰의 identity 는 문자열이고 `author_id` 는 정수라서

토큰에는 `str(user.id)` 로 문자열을 넣었으므로 `get_jwt_identity()` 도 문자열을 돌려준다.
`post.author_id` 는 정수 열이다.
그대로 비교하면 `7 != '7'` 이 참이 되어 작성자 본인도 403 을 받는다.
그래서 `int()` 로 바꿔 비교하고, 글 작성 때도 `int(get_jwt_identity())` 를 `author_id` 에 넣는다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 6. 새어도 피해가 짧고, 사용자는 자주 로그인하지 않아도 된다

매 요청에 실려 다니는 access 토큰은 1시간이면 만료되므로, 새어 나가도 쓸 수 있는 기간이 짧다.
30일짜리 refresh 토큰은 `/api/refresh` 에서만 쓰여 글 쓰기 같은 일에는 못 쓴다.
사용자는 access 가 만료되면 refresh 로 새 access 를 받으므로 다시 비밀번호를 넣지 않아도 된다.
원본 팁의 「보안과 편의성을 동시에」가 이것이다.
근거: 2-summary 「동작 방식 (3)」, 「핵심 문장 3」.

### 7. 403 — 인증은 통과했지만 그 글의 주인이 아니다

유효한 access 토큰이 있으니 `@jwt_required()` 는 통과한다(401 이 아니다).
글이 실제로 있으니 `get_or_404` 도 통과한다(404 가 아니다).
그다음 `post.author_id != int(get_jwt_identity())` 가 참이 되어 `{'message': '권한 없음'}, 403` 을 돌려준다.
401 은 「누구인지 증명 실패」, 403 은 「누구인지는 알지만 이 일은 허용 안 함」이다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 8. 스키마 검증은 통과하고, 저장(commit) 때 DB 유일 제약에서 막혀 서버 오류가 된다

`UserSchema` 의 `@validates` 는 `username` 만 DB 에서 중복을 조회한다.
`email` 은 꼴만 검사하므로 중복이어도 `load()` 를 통과한다.
`User` 모델의 `email` 열은 `unique=True` 라 `db.session.commit()` 에서 DB 가 거절하며 예외가 난다.
`RegisterResource` 는 그 예외를 잡지 않으므로 400 같은 친절한 응답이 아니라 서버 오류(500)가 된다. (원본에 근거 없음 — 추론)
근거: 2-summary 「어디서 틀리나 6」.

### 9. 서버는 뜨지 않고, `print` 줄들은 import 하는 순간 찍힌다

`db.create_all()` 과 `app.run(debug=True)` 는 `if __name__ == '__main__':` 안에 있어, import 될 때는 `__name__` 이 모듈 이름이라 실행되지 않는다.
끝의 `print` 들은 그 블록 밖 모듈 맨 끝에 있으므로 import 할 때 모듈 본문이 실행되며 바로 찍힌다.
직접 실행할 때는 반대로 `app.run` 이 서버를 띄운 채 돌아오지 않아, 서버가 끝나야 `print` 에 닿는다.
근거: 2-summary 「어디서 틀리나 9」.

### 10. HTTP 메서드 이름 = 메서드 이름, URL 조각은 변수 컨버터로 인자가 된다

`api.add_resource(PostResource, '/api/posts/<int:post_id>')` 가 두 요청을 모두 `PostResource` 로 보낸다.
그 안에서 Flask-RESTful 이 요청의 HTTP 메서드 이름에 맞는 메서드를 부른다 — GET 은 `get`, PUT 은 `put`.
`<int:post_id>` 컨버터가 `'3'` 을 정수 `3` 으로 바꿔 `get(self, post_id)` · `put(self, post_id)` 의 `post_id` 로 넘긴다.
근거: 2-summary 「동작 방식 (1)」.

## 실습 정답

### 실습 1. 회원 · 토큰 · 게시글 CRUD 를 갖춘 Flask REST API 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. DB URI · 서명 키 | `app.config['SQLALCHEMY_DATABASE_URI']` · `app.config['JWT_SECRET_KEY']` |
| 2. 토큰 만료 | `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)` · `JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)` |
| 3. 확장 초기화 | `db = SQLAlchemy(app)` · `api = Api(app)` · `jwt = JWTManager(app)` |
| 4. `User` 열 | `class User(db.Model)` 의 `id` · `username` · `email` · `password_hash` |
| 5. 비밀번호 해시 · 확인 | `set_password` (`generate_password_hash`) · `check_password` (`check_password_hash`) |
| 6. `Post` 열 · 관계 | `class Post` 의 `author_id = …ForeignKey('user.id')` · `created_at … default=db.func.now()` · `author = db.relationship('User', backref='posts')` |
| 7. 응답 전용 / 요청 전용 | `UserSchema.id` 의 `dump_only=True` · `password` 의 `load_only=True` |
| 8. 사용자 필드 규칙 | `validate.Length(min=3, max=80)` · `fields.Email(required=True)` · `validate.Length(min=6)` |
| 9. 사용자명 중복 | `@validates('username')` `validate_username` |
| 10. 글 필드 규칙 | `PostSchema` 의 `dump_only=True` 세 필드 · `validate.Length(min=1, max=200)` · `content = fields.Str(required=True)` |
| 11. 작성자 이름 계산 | `author_name = fields.Method('get_author_name')` · `get_author_name` |
| 12. 스키마 인스턴스 | `user_schema` · `post_schema` · `posts_schema = PostSchema(many=True)` |
| 13. 가입 | `RegisterResource.post` — `user_schema.load` · `except ValidationError` → 400 · `…, 201` |
| 14. 로그인 | `LoginResource.post` — `check_password` 실패 → 401 · `create_access_token(identity=str(user.id))` · `create_refresh_token(…)` |
| 15. 갱신 | `TokenRefreshResource` 의 `@jwt_required(refresh=True)` · `get_jwt_identity()` · `create_access_token` |
| 16. 목록 쿼리 · 검색 | `PostListResource.get` 의 `request.args.get(…, type=int)` · `Post.title.ilike(f'%{search}%')` |
| 17. 정렬 · 페이지 | `order_by(Post.created_at.desc()).paginate(…)` · 반환 dict 의 네 키 |
| 18. 작성 | `PostListResource.post` 의 `@jwt_required()` · `author_id=int(get_jwt_identity())` · `…, 201` |
| 19. 단건 조회 | `PostResource.get` 의 `Post.query.get_or_404(post_id)` |
| 20. 수정 | `PostResource.put` — `get_or_404` · `!= int(get_jwt_identity())` → 403 · `load(…, partial=True)` · `data.get('title', post.title)` |
| 21. 삭제 | `PostResource.delete` — `get_or_404` · 403 · `db.session.delete(post)` · `{'message': '삭제 완료'}, 200` |
| 22. 라우트 | `api.add_resource(…)` 다섯 줄 |
| 23. 직접 실행 | `if __name__ == '__main__':` 안의 `with app.app_context(): db.create_all()` · `app.run(debug=True)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/flask-api.py`

```python
# [웹 프레임워크] Flask RESTful API (marshmallow, JWT)
# 설명: Flask-RESTful, marshmallow 스키마, JWT 인증, API 구축 패턴
# 팁: marshmallow의 dump_only는 응답에만, load_only는 요청에만 포함된다. partial=True로 부분 업데이트를 허용한다. JWT refresh 토큰으로 access 토큰을 갱신하면 보안과 편의성을 동시에 확보한다. get_or_404는 Flask-SQLAlchemy가 제공하는 편의 메서드다.

# Flask RESTful API - marshmallow + JWT
# pip install flask flask-restful marshmallow flask-jwt-extended flask-sqlalchemy

# Flask는 WSGI 기반 - request/response 동기 처리
from flask import Flask, request, jsonify
# flask_restful: Resource 클래스 기반 라우팅 추상화
from flask_restful import Api, Resource, reqparse
# Flask-SQLAlchemy: SQLAlchemy ORM 통합
from flask_sqlalchemy import SQLAlchemy
# JWT 토큰 발급/검증/데코레이터 모음
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
# marshmallow: 직렬화 + 유효성 검사 라이브러리
from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import timedelta
# werkzeug: Flask의 WSGI 유틸 (비밀번호 해싱)
from werkzeug.security import generate_password_hash, check_password_hash

# Flask 앱 + 설정
app = Flask(__name__)
# DB URI (개발용 SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api.db'
# JWT 서명 키 (절대 노출 금지)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
# 액세스 토큰 만료 1시간
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
# 리프레시 토큰 만료 30일
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# 확장 모듈 초기화
db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)


# === 1. 모델 ===
# SQLAlchemy 선언적 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # 비밀번호는 해시만 저장 (평문 저장 금지)
    password_hash = db.Column(db.String(256), nullable=False)

    # 비밀번호 해싱 후 저장
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 입력 비밀번호 검증
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # ForeignKey로 User 참조
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # default=db.func.now(): DB의 NOW() 함수 사용
    created_at = db.Column(db.DateTime, default=db.func.now())
    # relationship: ORM 레벨 양방향 연결, backref로 역참조 자동 생성
    author = db.relationship('User', backref='posts')


# === 2. Marshmallow 스키마 ===
# Schema: 직렬화 형식 + 입력 유효성 검사 정의
class UserSchema(Schema):
    # dump_only: 응답에만 포함 (서버 생성 ID 등)
    id = fields.Int(dump_only=True)                    # 응답에만 포함
    # validate: 검증 규칙
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80)
    )
    # Email: 이메일 형식 자동 검증
    email = fields.Email(required=True)
    # load_only: 요청에만 포함 (응답에 비밀번호 노출 방지)
    password = fields.Str(
        load_only=True,                                 # 요청에만 포함
        required=True,
        validate=validate.Length(min=6)
    )

    # @validates: 특정 필드 추가 검증 (DB 조회 등)
    @validates('username')
    def validate_username(self, value):
        if User.query.filter_by(username=value).first():
            raise ValidationError('이미 사용 중인 사용자명입니다.')


class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200)
    )
    content = fields.Str(required=True)
    author_id = fields.Int(dump_only=True)
    # Method 필드: 메서드명을 받아 동적 값 계산
    author_name = fields.Method('get_author_name')
    created_at = fields.DateTime(dump_only=True)

    # Method 필드의 계산 함수
    def get_author_name(self, obj):
        return obj.author.username if obj.author else None


# 스키마 인스턴스 (단일 / 다중 직렬화용)
user_schema = UserSchema()
post_schema = PostSchema()
# many=True: 리스트 직렬화용
posts_schema = PostSchema(many=True)


# === 3. 인증 API ===
# Resource 클래스: HTTP 메서드명을 메서드로 정의
class RegisterResource(Resource):
    def post(self):
        try:
            # load(): 입력 검증 + 정제된 dict 반환
            data = user_schema.load(request.get_json())
        except ValidationError as err:
            # 검증 실패 시 에러 메시지 + 400
            return {'errors': err.messages}, 400

        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        # dump(): 객체 -> dict 직렬화
        return {'message': '회원가입 성공', 'user': user_schema.dump(user)}, 201


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()

        # 인증 실패 시 401
        if not user or not user.check_password(data.get('password', '')):
            return {'message': '잘못된 인증 정보'}, 401

        # 액세스/리프레시 토큰 발급 (identity는 사용자 식별자)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_schema.dump(user)
        }


class TokenRefreshResource(Resource):
    # refresh=True: 리프레시 토큰만 허용
    @jwt_required(refresh=True)
    def post(self):
        # 현재 토큰의 identity 추출
        identity = get_jwt_identity()
        # 새 액세스 토큰 발급
        new_token = create_access_token(identity=identity)
        return {'access_token': new_token}


# === 4. CRUD API ===
class PostListResource(Resource):
    def get(self):
        """게시글 목록 (페이지네이션)"""
        # query string에서 페이지 정보
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('q', '')

        query = Post.query
        if search:
            # ilike: 대소문자 무시 LIKE
            query = query.filter(Post.title.ilike(f'%{search}%'))

        # paginate: SQLAlchemy 페이지네이션
        pagination = query.order_by(
            Post.created_at.desc()
        ).paginate(page=page, per_page=per_page)

        return {
            'posts': posts_schema.dump(pagination.items),
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }

    # @jwt_required: 유효한 액세스 토큰 필수
    @jwt_required()
    def post(self):
        """게시글 작성"""
        try:
            data = post_schema.load(request.get_json())
        except ValidationError as err:
            return {'errors': err.messages}, 400

        post = Post(
            title=data['title'],
            content=data['content'],
            # 토큰에서 사용자 ID 가져와 자동 주입
            author_id=int(get_jwt_identity())
        )
        db.session.add(post)
        db.session.commit()
        return {'post': post_schema.dump(post)}, 201


class PostResource(Resource):
    def get(self, post_id):
        # get_or_404: 없으면 자동 404 (Flask-SQLAlchemy 헬퍼)
        post = Post.query.get_or_404(post_id)
        return {'post': post_schema.dump(post)}

    @jwt_required()
    def put(self, post_id):
        post = Post.query.get_or_404(post_id)
        # 작성자 본인 확인 (객체 수준 권한)
        if post.author_id != int(get_jwt_identity()):
            return {'message': '권한 없음'}, 403

        try:
            # partial=True: 일부 필드만 보내도 허용 (PATCH 의미)
            data = post_schema.load(request.get_json(), partial=True)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        # 부분 업데이트
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        db.session.commit()
        return {'post': post_schema.dump(post)}

    @jwt_required()
    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        if post.author_id != int(get_jwt_identity()):
            return {'message': '권한 없음'}, 403
        db.session.delete(post)
        db.session.commit()
        return {'message': '삭제 완료'}, 200


# === 5. 라우트 등록 ===
# add_resource(클래스, URL): Resource를 URL에 매핑 (메서드 자동 디스패치)
api.add_resource(RegisterResource, '/api/register')
api.add_resource(LoginResource, '/api/login')
api.add_resource(TokenRefreshResource, '/api/refresh')
api.add_resource(PostListResource, '/api/posts')
# <int:post_id>: 변수 컨버터 - 메서드 인자로 전달
api.add_resource(PostResource, '/api/posts/<int:post_id>')


# 모듈 직접 실행 시 개발 서버 시작
if __name__ == '__main__':
    # 앱 컨텍스트에서 테이블 생성
    with app.app_context():
        db.create_all()
    # debug=True: 자동 리로드 + 디버거
    app.run(debug=True)

print("Flask RESTful API 핵심 정리")
print("="*50)
print("Flask-RESTful: Resource 클래스로 REST API 구축")
print("marshmallow: 스키마 기반 직렬화/유효성 검사")
print("Flask-JWT-Extended: JWT 인증 (access + refresh 토큰)")
print("@jwt_required(): 인증 필수 엔드포인트")
print("get_jwt_identity(): 현재 사용자 ID 조회")
print("partial=True: 부분 업데이트 허용 (PUT/PATCH)")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 들어오는 쪽은 언제나 `schema.load` → `except ValidationError` → 400 의 같은 틀로 막는다.
- 응답에 무엇이 실리나는 `dump_only` · `load_only` 가 정한다 — 비밀번호가 응답에 없는 것도, 요청으로 `author_id` 를 못 정하는 것도 이 덕분이다.
- 토큰 identity 는 문자열로 넣고, DB 의 정수와 비교 · 저장할 때마다 `int()` 로 바꾼다.
- 쓰기 엔드포인트는 「`@jwt_required()` (인증) → `get_or_404` (존재) → 작성자 비교 (인가)」 순서로 문을 지난다.
- 부분 수정은 `partial=True` 와 `data.get(키, 원래값)` 이 함께 있어야 완성된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
