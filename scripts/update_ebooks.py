import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db_schemas.schemas import DBEBook
from database import SessionLocal


 # return {
#     "ebooks": [
#         {
#             "id": "a2004360-fed7-478a-aa5b-5f8a65b0503e",
#             "title": "计算机网络（第8版）",
#             "author": "谢希仁",
#             "collection": "computer_network"
#         },
#         {
#             "id": "9dacf3f0-4e14-4ffe-b38b-4ce4a8e4a5ec",
#             "title": "动手学深度学习",
#             "author": "阿斯顿·张,李沐...",
#             "collection": "d2l"
#         },
#         {
#             "id": "51be21c2-6525-462c-ae50-de031932e7ec",
#             "title": "操作系统原理（第四版）",
#             "author": "庞丽萍",
#             "collection": "operation_system"
#         },
#         {
#             "id": "f0ac4a02-f4fe-4452-bb7a-08d581bb303d",
#             "title": "现代控制系统（第12版）",
#             "author": "Richard C. Dorf",
#             "collection": "modern_control_system_zh"
#         },
#         {
#             "id": "b4c14756-9ef5-460b-bded-61ebc67d9dbc",
#             "title": "Modern Control System",
#             "author": "Richard C. Dorf",
#             "collection": "modern_control_system_en"
#         },
#         # {
#         #     "id": "661863c2-8870-4db3-8898-5d3670edf070",
#         #     "title": "算法设计与分析（第12版）",
#         #     "author": "李春葆",
#         #     "collection": "algorithm_design"
#         # },
#     ],
#     "total": 6
# }
ebooks = [
    {
        "title": "计算机网络（第8版）",
        "author": "谢希仁",
        "collection": "computer_network"
    },
    {
        "title": "动手学深度学习",
        "author": "阿斯顿·张,李沐...",
        "collection": "d2l"
    },
    {
        "title": "操作系统原理（第四版）",
        "author": "庞丽萍",
        "collection": "operation_system"
    },
    {
        "title": "现代控制系统（第12版）",
        "author": "Richard C. Dorf",
        "collection": "modern_control_system_zh"
    },
    {
        "title": "Modern Control System",
        "author": "Richard C. Dorf",
        "collection": "modern_control_system_en"
    }
]

def upsert_ebooks(db: Session):
    """
    Insert these ebooks into the DB. Do not provide id here so the DB or ORM default is used.
    Expects `db` to be a configured SQLAlchemy Session instance.
    """
    for item in ebooks:
        obj = DBEBook(**item)
        db.merge(obj)  # merge will insert or update based on primary key; without id it will insert
    db.commit()

if __name__ == "__main__":
    with SessionLocal() as session:
        upsert_ebooks(session)
