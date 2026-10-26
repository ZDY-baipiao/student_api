"""
第四章 · 第 4 讲（最后一讲）：把数据库接到接口上

运行（先 cd 到这个文件夹）：
    python app.py

然后浏览器打开 http://127.0.0.1:8003/docs ，所有接口都能在页面上点着测。

注意：这一讲不删表，你 step3.py 建好的班级和学生数据会直接用上。
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
import uvicorn

# ============================================================
# 一、数据库（和前面几讲一样）
# ============================================================
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "demo_db"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
class Base(DeclarativeBase):
    pass



class Clazz(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)

    students = relationship("Student", back_populates="clazz", lazy="selectin")


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    age = Column(Integer)
    email = Column(String(50))
    phone_num = Column(String(20))
    clazz_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    clazz = relationship("Clazz", back_populates="students")


Base.metadata.create_all(engine)      # 表已在就跳过，不会删你的数据


# ============================================================
# 二、请求体模型：客户端传什么，由它说了算
# ============================================================
class ClazzIn(BaseModel):
    name: str


class StudentIn(BaseModel):
    name: str
    age: int
    clazz_id: int
    email: str
    phone_num: str

class StudentUpdate(BaseModel):
    age: int

# ============================================================
# 三、依赖注入：每个请求一个会话，用完自动关闭（这一讲的核心）
# ============================================================
def get_db():
    db = SessionLocal()
    try:
        yield db              # 把会话交给接口函数用
    except Exception:
        db.rollback()         # 出异常回滚
        raise
    finally:
        db.close()            # 无论成功失败都关闭，连接还给池子


app = FastAPI(title="班级学生接口")


# ============================================================
# 四、接口
# ============================================================
@app.post("/classes", summary="新建班级")
def create_class(data: ClazzIn, db: Session = Depends(get_db)):
    c = Clazz(name=data.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@app.get("/classes", summary="班级列表（带学生人数）")
def list_classes(db: Session = Depends(get_db)):
    cs = db.execute(select(Clazz)).scalars().all()
    return [{"id": c.id, "name": c.name, "student_count": len(c.students)} for c in cs]


@app.get("/classes/{clazz_id}", summary="班级详情（带学生名单）")
def get_class(clazz_id: int, db: Session = Depends(get_db)):
    c = db.get(Clazz, clazz_id)
    if c is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return {
        "id": c.id,
        "name": c.name,
        # 关联关系在这里发挥价值：不用写 JOIN，直接遍历
        "students": [{"id": s.id, "name": s.name, "age": s.age,"email": s.email,"phone_num":s.phone_num} for s in c.students],
    }


@app.post("/students", summary="新建学生")
def create_student(data: StudentIn, db: Session = Depends(get_db)):
    if db.get(Clazz, data.clazz_id) is None:
        raise HTTPException(status_code=400, detail=f"班级 {data.clazz_id} 不存在")
    s = Student(name=data.name, age=data.age, clazz_id=data.clazz_id,email =data.email,phone_num=data.phone_num)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "name": s.name, "age": s.age, "clazz_id": s.clazz_id,"email":s.email,"phone_num":s.phone_num}


@app.get("/students", summary="学生列表（可按班级筛选）")
def list_students(clazz_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Student)
    if clazz_id is not None:
        stmt = stmt.where(Student.clazz_id == clazz_id)
    rows = db.execute(stmt).scalars().all()
    return [{"id": s.id, "name": s.name, "age": s.age,"phone_num":s.phone_num ,"email":s.email ,"clazz_id": s.clazz_id} for s in rows]

@app.get("/students/stats", summary="学生统计（总人数与平均年龄）")
def student_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.execute(select(func.count()).select_from(Student)).scalar_one()
    avg_age = db.execute(select(func.avg(Student.age))).scalar_one()
    return {"total": total, "avg_age": round(float(avg_age), 1) if avg_age is not None else None}


@app.put("/students/{student_id}",summary="修改学生")
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)                # 空3
    if s is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    s.age = data.age                               # 空4
    db.commit()                                    # 空5
    return {"id": s.id, "name": s.name, "age": s.age,"phone_num":s.phone_num,"email":s.email ,"clazz_id": s.clazz_id}

@app.delete("/students/{student_id}", summary="删除学生")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(s)              # ← PUT 这里是 s.age = data.age
    db.commit()
    return {"deleted": student_id}



if __name__ == "__main__":
    uvicorn.run(app="app:app", host="127.0.0.1", port=8003, reload=True)
