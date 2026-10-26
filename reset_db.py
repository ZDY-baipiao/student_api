"""
一键重置数据库表结构（把表删掉，按当前 step4.py 的模型重新建）

什么时候用：
    改了模型（加字段、改类型、加外键），但数据库表还是旧结构，
    一跑就报 "Unknown column xxx" 或者数据存不进去。

怎么用（先 cd 到本文件所在目录）：
    python reset_db.py
    python step4.py

注意：会删掉 classes 和 students 两张表的全部数据，只适合练习库。
"""

from step4 import engine, Base
import step4  # noqa: F401  确保模型类都被加载进来

print("即将删除的表：", list(Base.metadata.tables.keys()))
Base.metadata.drop_all(engine)      # 删表
Base.metadata.create_all(engine)    # 按当前模型重建
print("重建完成，当前表结构：")
from sqlalchemy import inspect
insp = inspect(engine)
for t in Base.metadata.tables.keys():
    cols = [c["name"] for c in insp.get_columns(t)]
    print(f"  {t}: {cols}")
