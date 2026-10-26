# 学生管理接口（FastAPI + MySQL）

基于 FastAPI + SQLAlchemy 2.x 的班级 / 学生 CRUD 接口，用于练习 ORM 建模与 REST 接口设计。
从零手写，包含踩坑与修复过程。

## 功能

- 班级：新建、列表（带学生人数）、详情（带学生名单）
- 学生：新建、列表（可按班级筛选）、修改年龄、删除
- 请求体使用 Pydantic 校验，字段缺失或类型错误自动返回 422
- 依赖注入管理数据库会话：每请求一个 Session，异常自动回滚

## 技术栈

Python 3.13 · FastAPI 0.143 · SQLAlchemy 2.1 · MySQL 8 · PyMySQL · uvicorn

## 目录结构

```
student-api/
├── app.py            # 主程序：模型定义 + 依赖注入 + 全部接口
├── reset_db.py       # 重建表结构（模型改动后用它同步，会清空数据）
├── requirements.txt
└── .gitignore
```

## 运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 准备数据库（MySQL 中先建库）

```sql
CREATE DATABASE IF NOT EXISTS demo_db DEFAULT CHARSET utf8mb4;
```

3. 修改 `app.py` 顶部的数据库连接信息（`DB_USER` / `DB_PASSWORD` 等）

4. 建表并启动

```bash
python reset_db.py      # 首次运行或模型变更后执行
python app.py
```

5. 打开交互式文档

```
http://127.0.0.1:8003/docs
```

## 接口一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /classes | 新建班级 |
| GET | /classes | 班级列表（含学生人数） |
| GET | /classes/{clazz_id} | 班级详情（含学生名单） |
| POST | /students | 新建学生 |
| GET | /students | 学生列表（可按 clazz_id 筛选） |
| PUT | /students/{student_id} | 修改学生年龄 |
| DELETE | /students/{student_id} | 删除学生 |

示例：新建学生

```bash
curl -X POST http://127.0.0.1:8003/students \
  -H "Content-Type: application/json" \
  -d '{"name":"小明","age":18,"clazz_id":1,"email":"xm@example.com","phone_num":"13800138000"}'
```

## 踩过的坑

- **手机号用 Integer 存储溢出**：11 位手机号超过 INT 上限 21 亿，报 `(1264) Out of range value`。
  改为 `VARCHAR(20)`，Python 侧类型也同步改成 `str`。
- **改了模型但表没变**：`create_all()` 只建表不改表。用 `SHOW CREATE TABLE students` 核对，
  或执行 `reset_db.py` 重建（会丢数据），生产环境应使用 Alembic 迁移。
- **接口返回 200 但字段是 NULL**：`Student(...)` 构造时漏传 `email`，请求体里有值但没落库。
  排查方法：查询接口也要返回该字段，否则看不出来。
- **系统学习到的一个区分**：`Column(Integer)` 只影响建表，Python 类型注解只影响请求校验，
  两者是两套系统，改一个不代表改另一个。

## 后续计划

- [ ] 数据库连接信息改为从环境变量读取
- [ ] 增加分页与模糊搜索
- [ ] 补充 pytest 接口测试
