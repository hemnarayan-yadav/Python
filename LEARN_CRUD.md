# Python CRUD API — Zero to Hero (for Node.js developers)

> **Audience:** You know JavaScript / Node.js. You know **zero** Python.
> **Goal:** Build a full CRUD REST API in Python (FastAPI + SQLAlchemy + MySQL).
> **Language:** English + Hinglish mix for clarity. Read once → understand fully.

---

## 0. Mental map: Node.js → Python

Pehle ek quick comparison table dekho. Yeh dimaag mein rakhoge toh sab kuch easy lagega.

| Concept | Node.js | Python (this project) |
|---|---|---|
| Runtime | Node | CPython (just `python`) |
| Package manager | `npm` / `yarn` | `pip` |
| Manifest file | `package.json` | `requirements.txt` |
| Isolated env | `node_modules/` (per project, automatic) | `.venv/` (per project, **manual**) |
| Web framework | Express / Nest | **FastAPI** |
| Server | built-in `http` / Express | **Uvicorn** (ASGI server) |
| ORM | Sequelize / Prisma / Mongoose | **SQLAlchemy** |
| Validation | Joi / Zod / class-validator | **Pydantic** |
| `.env` loader | `dotenv` | `python-dotenv` |
| `async/await` | everywhere | optional (FastAPI supports both `def` and `async def`) |
| Request body parsing | `express.json()` | Automatic via Pydantic schema |

> **Mind shift #1:** Python me **indentation = code block**. Curly braces `{}` nahi hote. Galat indent → SyntaxError.
>
> **Mind shift #2:** Python me **virtual environment** banana zaroori hai. Warna packages globally install ho jayenge aur version conflicts honge. Node me `node_modules` automatic per-project hota hai — Python me tum khud banate ho.

---

## 1. Install Python (one-time setup)

### Kya karna hai
- https://www.python.org/downloads/ se Python 3.11+ install karo.
- Installer me **"Add Python to PATH"** checkbox **zaroor tick** karo.

### Kyun zaroori hai
PATH me add nahi kiya toh terminal me `python` command kaam nahi karegi. Tumhe har baar full path likhna padega.

### Yaad rakhne wali baat
Verify karo:
```powershell
python --version       # Python 3.11.x ya higher
pip --version          # pip ka version
```

### Impact
Ab tumhare paas Python interpreter aur `pip` (npm jaisa) ready hai.

### Next step
Project folder banao aur **virtual environment** setup karo.

---

## 2. Project folder + Virtual environment (`.venv`)

### Kya karna hai
```powershell
mkdir python-crud-api
cd python-crud-api
python -m venv .venv                      # virtual env banao
.\.venv\Scripts\Activate.ps1              # activate karo (Windows PowerShell)
```

Activate hone ke baad terminal prompt me `(.venv)` dikhega.

### Kyun zaroori hai
- Har project ka apna isolated package set chahiye. (Jaise Node me har project ka apna `node_modules`.)
- Globally install karoge toh ek project ka SQLAlchemy 2.0 dusre project ka SQLAlchemy 1.4 break kar dega.

### Yaad rakhne wali baat
- **Har naye terminal me dobara activate karna padta hai.**
- Agar PowerShell error de ("running scripts is disabled"), ek baar yeh chalao:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  ```
- `.venv/` folder ko `.gitignore` me daalo. Git me kabhi commit mat karo.

### Impact
Ab jo bhi `pip install` karoge, sirf is project ke andar jayega. Clean isolation.

### Next step
Dependencies install karo.

---

## 3. Install dependencies

### Kya karna hai
Project root me `requirements.txt` banao:

```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
python-dotenv
pydantic[email]
```

Install karo:
```powershell
pip install -r requirements.txt
```

### Kyun zaroori hai
| Package | Kaam |
|---|---|
| `fastapi` | Web framework (Express jaisa, but auto docs + validation built-in) |
| `uvicorn[standard]` | Server jo FastAPI app ko run karega |
| `sqlalchemy` | ORM (Sequelize/Prisma jaisa) |
| `pymysql` | MySQL driver — SQLAlchemy MySQL se baat karne ke liye iska use karta hai |
| `python-dotenv` | `.env` file load karne ke liye |
| `pydantic[email]` | Data validation + `EmailStr` type |

### Yaad rakhne wali baat
- Common galti: `pip install requirements.txt` ❌ (yeh "requirements.txt" naam ka package dhundhta hai).
  Sahi: **`pip install -r requirements.txt`** ✅
- File ka spelling **requirements** hai, **requirments** nahi.

### Impact
Sab tools ready. Ab code likh sakte ho.

### Next step
MySQL setup karo.

---

## 4. MySQL ready karo

### Kya karna hai
1. MySQL Server install karo (agar nahi hai). MySQL Workbench bhi install karo (GUI ke liye).
2. MySQL **service running** honi chahiye:
   - `Win + R` → `services.msc` → "MySQL80" find karo → **Start** → Properties → **Startup type: Automatic**.
3. Workbench me ek database banao (one time):
   ```sql
   CREATE DATABASE python_crud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

### Kyun zaroori hai
- MySQL server **band** hua toh Python kuch nahi kar sakta. ("Can't connect to MySQL server" error.)
- SQLAlchemy **tables** banata hai (`create_all`), **database** nahi banata. Database tumhe pehle se chahiye.

### Yaad rakhne wali baat
- Default port: **3306**.
- Default host: **127.0.0.1** ya **localhost**.
- Apna `root` password yaad rakho.

### Impact
Database server ready hai connections accept karne ke liye.

### Next step
`.env` file banao secrets store karne ke liye.

---

## 5. `.env` file (secrets)

### Kya karna hai
Project root me `.env` banao:

```env
DB_USER=root
DB_PASSWORD=your_real_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=python_crud
```

**Rules:**
- No quotes around values.
- No spaces around `=`.
- `.env` ko `.gitignore` me daalo.

### Kyun zaroori hai
Password / DB credentials code me hardcode karna **security risk** hai. `.env` use karne se same code dev / staging / prod me different config ke saath chal sakta hai.

### Yaad rakhne wali baat
- Agar password me `@`, `:`, `/`, `#` jaise special characters hain → URL encode karna padega (humne `quote_plus` use kiya hai).
- `.env` file kabhi git me push mat karo.

### Impact
Credentials code se separate ho gaye.

### Next step
Project structure samjho aur files banao.

---

## 6. Project structure

```
python-crud-api/
├── .venv/                      ← virtual env (git ignore)
├── .env                        ← secrets   (git ignore)
├── .gitignore
├── requirements.txt            ← dependencies list
├── database.py                 ← DB connection + Session factory
├── models.py                   ← SQLAlchemy ORM models (table = class)
├── schemas.py                  ← Pydantic schemas (request/response shape)
├── main.py                     ← FastAPI app entry point
├── controllers/
│   └── user_controllers.py     ← business logic (CRUD functions)
└── routes/
    └── user_routes.py          ← URL → controller mapping
```

> **Node analogy:**
> - `models.py` ≈ Sequelize models
> - `schemas.py` ≈ Joi/Zod schemas
> - `controllers/` ≈ Express controllers
> - `routes/` ≈ Express router files
> - `main.py` ≈ `app.js` / `server.js`
> - `database.py` ≈ `db.js` / Sequelize instance

### Kyun aisa structure
**Separation of concerns.** Routes sirf URL jaante hain. Controllers sirf business logic. Models sirf DB. Schemas sirf data shape. Easy to test, easy to scale.

### Next step
Ek-ek karke files samjho.

---

## 7. `database.py` — DB connection

```python
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()                                    # .env → os.environ

user     = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host     = os.getenv("DB_HOST", "localhost")
port     = os.getenv("DB_PORT", "3306")
db_name  = os.getenv("DB_NAME")

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
    f"@{host}:{port}/{db_name}"
)

engine       = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()
```

### Important cheezein
- **`engine`** = connection pool. App me ek hi banta hai (singleton).
- **`SessionLocal`** = factory. Har HTTP request ke liye ek nayi session banegi.
- **`Base`** = parent class. Saare models isi se inherit karenge.
- **`echo=True`** = terminal me actual SQL print hoga. Learning ke liye gold.
- **`pool_pre_ping=True`** = connection use karne se pehle ping. "MySQL server has gone away" error se bachata hai.
- **`quote_plus`** = password me special chars (`@`, `:`, etc.) URL-safe banata hai.

### Impact
DB se baat karne ka raasta ready hai.

### Next step
Table define karo.

---

## 8. `models.py` — table = Python class

```python
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    age        = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
```

### Important cheezein
- **`__tablename__`** = MySQL me actual table name.
- **`primary_key=True`** = unique row id, auto-increment.
- **`unique=True`** on `email` = duplicate emails MySQL khud reject karega.
- **`index=True`** = fast lookup (jaise Sequelize `indexes: [...]`).
- **`nullable=False`** = column required (NOT NULL).
- **`server_default=func.now()`** = MySQL khud current time daalega INSERT pe.

### Impact
Python class aur MySQL table ek dusre se mapped hain.

### Next step
Request/response shape define karo (Pydantic).

---

## 9. `schemas.py` — input/output validation (Pydantic)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):                     # ← input for POST
    name:  str      = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age:   int      = Field(..., gt=0, lt=150)

class UserUpdate(BaseModel):                     # ← input for PATCH (partial)
    name:  Optional[str]      = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    age:   Optional[int]      = Field(None, gt=0, lt=150)

class UserResponse(BaseModel):                   # ← output (what API returns)
    id:         int
    name:       str
    email:      EmailStr
    age:        int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)   # SQLAlchemy → JSON
```

### Why **two** classes (model vs schema)?
- **Model** = DB ki shape (with `password_hash`, internal fields, etc.).
- **Schema** = API ki shape (sirf wo fields jo client ko dikhane hain).
- Yeh separation **security** ke liye hai. Tumhara DB model accidentally `password_hash` API se nahi leak karega.

### `from_attributes=True` kya hai?
Bina iske, FastAPI SQLAlchemy `User` object ko JSON me convert nahi kar payega. Ye Pydantic v2 ka tareeka hai bolne ka "iss class ke fields ORM object ke attributes se padho".

### Impact
Galat data andar nahi aayega, internal data bahar nahi jayega.

### Next step
Business logic (CRUD functions) likho.

---

## 10. `controllers/user_controllers.py` — CRUD functions

### `get_db()` — Dependency
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- `yield` = "is point pe value de do, jab caller khatam ho jaye toh `finally` chalao."
- **Har request ke liye fresh session** milti hai, aur request khatam hote hi automatically close ho jati hai. Memory leak / dangling connection nahi hota.

### CRUD functions (sab Express controller jaise hi hain)

| Function | Express equivalent | DB call |
|---|---|---|
| `create_user` | `app.post('/users', handler)` | `db.add(); db.commit(); db.refresh()` |
| `list_users` | `app.get('/users', handler)` | `db.query(User).offset().limit().all()` |
| `get_user` | `app.get('/users/:id', handler)` | `db.query(User).filter(User.id==id).first()` |
| `update_user` | `app.patch('/users/:id', handler)` | `setattr(); db.commit()` |
| `delete_user` | `app.delete('/users/:id', handler)` | `db.delete(); db.commit()` |

### Important rules
- **`db.commit()` lagana mat bhoolo** — warna data save nahi hoga.
- Error aaye toh **`db.rollback()`** karo, warna session corrupted ho jati hai.
- Not found = **`HTTPException(404)`** raise karo, `None` return mat karo.
- Duplicate key (unique violation) = **`409 Conflict`**.

### Impact
Saari business logic ek jagah, routes file clean rahegi.

### Next step
Routes register karo.

---

## 11. `routes/user_routes.py` — URL → controller

```python
from typing import List
from fastapi import APIRouter, status
from controllers import user_controllers
from schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

router.add_api_route("/",            user_controllers.create_user, methods=["POST"],   response_model=UserResponse, status_code=status.HTTP_201_CREATED)
router.add_api_route("/",            user_controllers.list_users,  methods=["GET"],    response_model=List[UserResponse])
router.add_api_route("/{user_id}",   user_controllers.get_user,    methods=["GET"],    response_model=UserResponse)
router.add_api_route("/{user_id}",   user_controllers.update_user, methods=["PATCH"],  response_model=UserResponse)
router.add_api_route("/{user_id}",   user_controllers.delete_user, methods=["DELETE"])
```

### Important
- **`prefix="/users"`** = saari routes auto `/users/...` ho jati hain. (Jaise Express `app.use('/users', router)`.)
- **`response_model=UserResponse`** = response automatically `UserResponse` shape me filter ho jata hai. Extra fields silently drop ho jate hain. Big security win.
- **`status_code=201`** = REST convention: POST = 201 Created, not 200.

### Impact
Ab `http://127.0.0.1:8000/users/` callable hai.

### Next step
App entry point banao.

---

## 12. `main.py` — entry point

```python
from fastapi import FastAPI
import models
from database import engine
from routes.user_routes import router as user_router

app = FastAPI(title="Users CRUD API", version="1.0.0")

models.Base.metadata.create_all(bind=engine)     # tables banao agar nahi hain
app.include_router(user_router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}
```

### Important
- **`create_all`** sirf missing tables banata hai. **Existing tables alter nahi karta.** Schema badle toh **Alembic** (migrations tool) use karna padega — Sequelize migrations jaisa.
- **`include_router`** = Express ka `app.use(router)`.

### Impact
App fully wired hai.

### Next step
Server chalao aur test karo.

---

## 13. Run karo

```powershell
.\.venv\Scripts\Activate.ps1     # agar already activate nahi hai
uvicorn main:app --reload
```

- `main:app` = `main.py` file me `app` variable.
- `--reload` = nodemon jaisa, code change pe auto-restart.

Browser kholo:
- **http://127.0.0.1:8000/docs** ← Swagger UI (testing ke liye best)
- **http://127.0.0.1:8000/redoc** ← Pretty docs

### Test sequence
1. **POST /users/** → body:
   ```json
   { "name": "Ali", "email": "ali@test.com", "age": 25 }
   ```
   Expect: `201` + JSON with `id` and `created_at`.
2. **GET /users/** → list me Ali dikhega.
3. **PATCH /users/1** → body `{ "age": 30 }` → updated user.
4. **DELETE /users/1** → success message.
5. Workbench me confirm:
   ```sql
   USE python_crud;
   SELECT * FROM users;
   ```

### Validation testing (try these to fail intentionally)
- `"email": "not-email"` → **422** (Pydantic ne reject kiya).
- `"age": -1` → **422** (gt=0 fail).
- Same email twice POST → **409 Conflict**.
- `GET /users/9999` → **404 Not Found**.

---

## 14. Common errors aur unke fix

| Error | Reason | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | venv activate nahi hai ya install nahi hua | activate karo, `pip install -r requirements.txt` |
| `Can't connect to MySQL server on '...'` | MySQL service stopped | `services.msc` → MySQL80 → Start |
| `Can't connect to MySQL server on '123@127.0.0.1'` | password me `@` aur URL break ho gaya | `quote_plus()` use karo (already done) |
| `Unknown database 'python_crud'` | DB pehle nahi banayi | Workbench me `CREATE DATABASE python_crud;` |
| `Access denied for user 'root'@...` | galat password in `.env` | `.env` fix karo |
| `IntegrityError: Duplicate entry` | unique constraint violate | controller me already 409 return ho raha hai |
| Route returns 422 unexpectedly | request body schema match nahi karti | Swagger me example dekho, fields fix karo |
| `RuntimeError: Working outside of application context` | FastAPI me nahi aata, Flask error hai | ignore |

---

## 15. Quick cheat sheet

| Karna hai | Command |
|---|---|
| venv banao | `python -m venv .venv` |
| venv activate | `.\.venv\Scripts\Activate.ps1` |
| install deps | `pip install -r requirements.txt` |
| naya package add | `pip install <name>` then `pip freeze > requirements.txt` |
| server run | `uvicorn main:app --reload` |
| docs | `http://127.0.0.1:8000/docs` |

---

# Practice Tasks

> Niche 3 tasks hain. Apne is project me hi try karo. Dimaag use karo, AI se mat puchho first try me. Stuck ho toh hint dekho.

---

## ✅ Task 1 — Add a `Product` resource (warm-up)

**Goal:** `users` ki tarah ek naya resource `products` banao with full CRUD.

**Requirements:**
- Table `products`: `id`, `name` (string), `price` (float, > 0), `stock` (int, ≥ 0), `created_at`.
- Routes: `POST /products/`, `GET /products/`, `GET /products/{id}`, `PATCH /products/{id}`, `DELETE /products/{id}`.
- `name` length 1–200.
- `price` 2 decimal places, must be positive.
- Duplicate name allowed (no unique constraint).

**Hint:**
- `models.py` me `Product` class add karo (`Float` import karo `sqlalchemy` se).
- `schemas.py` me `ProductCreate`, `ProductUpdate`, `ProductResponse` banao.
- `controllers/product_controllers.py` banao — `user_controllers.py` ko reference ke liye copy kar sakte ho.
- `routes/product_routes.py` banao.
- `main.py` me naya router include karo.
- Server restart hone pe `products` table apne aap ban jayegi.

**Done jab:** Swagger me `/products/...` endpoints kaam karein aur Workbench me `SELECT * FROM products;` me row dikhe.

---

## ✅ Task 2 — Search + pagination (intermediate)

**Goal:** `GET /users/` me search aur better pagination add karo.

**Requirements:**
- Query params support karo: `?skip=0&limit=10&search=ali`.
- `search` agar diya gaya hai toh `name` ya `email` me **partial match** (case-insensitive) karo.
- Response me sirf list nahi, **total count** bhi do:
  ```json
  {
    "total": 42,
    "skip": 0,
    "limit": 10,
    "items": [ ...users... ]
  }
  ```

**Hint:**
- SQLAlchemy me `User.name.ilike(f"%{search}%")` use karo (case-insensitive LIKE).
- Multiple OR conditions: `from sqlalchemy import or_` → `query.filter(or_(User.name.ilike(...), User.email.ilike(...)))`.
- `total = db.query(User).filter(...).count()` filter ke baad count nikal sakte ho.
- New schema banao: `UserListResponse` with fields `total`, `skip`, `limit`, `items: List[UserResponse]`.
- Route ka `response_model` is naye schema pe set karo.

**Done jab:** `GET /users/?search=al&limit=5` Ali ke matching users return kare with correct total.

---

## ✅ Task 3 — One-to-many relationship: User → Posts (advanced)

**Goal:** Ek `User` ke multiple `Post` ho sakte hain (blog post jaisa).

**Requirements:**
- Naya table `posts`: `id`, `title`, `body`, `user_id` (FK to users.id), `created_at`.
- Routes:
  - `POST /users/{user_id}/posts/` → us user ka naya post create karo.
  - `GET /users/{user_id}/posts/` → us user ke saare posts.
  - `DELETE /posts/{post_id}` → ek post delete.
- Agar `user_id` exist nahi karta → 404.
- `GET /users/{user_id}` me response me user ke posts bhi include karo (nested).

**Hint:**
- `models.py`:
  ```python
  from sqlalchemy import ForeignKey
  from sqlalchemy.orm import relationship

  class Post(Base):
      __tablename__ = "posts"
      id      = Column(Integer, primary_key=True, index=True)
      title   = Column(String(200), nullable=False)
      body    = Column(String(2000), nullable=False)
      user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
      created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
      user = relationship("User", back_populates="posts")

  # User class me add karo:
  posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
  ```
- `cascade="all, delete-orphan"` → user delete hone pe uske posts bhi delete.
- `schemas.py` me `PostResponse` aur ek naya `UserWithPostsResponse` (jisme `posts: List[PostResponse]` ho).
- Controller me `db.query(User).filter(User.id==user_id).first()` se relationship lazy-load ho jayega.

**Done jab:**
- 1 user banao, uske 3 posts banao.
- `GET /users/1` me 3 posts nested dikhne chahiye.
- User delete karo → uske posts bhi automatically gayab.

---

## Final advice

1. **Errors padho.** Python ke errors bahut clear hote hain. Last line first padho.
2. **Swagger best dost hai.** Postman ki zaroorat nahi.
3. **`echo=True` rakho** jab tak seekh rahe ho — actual SQL dekhna gold hai.
4. **Indentation pe dhyan do.** 4 spaces standard hai. Tabs aur spaces mix mat karo.
5. **Type hints lagao** har function pe. FastAPI sab unhi se kaam karta hai.
6. **Commit + rollback** hamesha pair me socho. Like `try/catch` in Node.

Happy coding! 🐍
