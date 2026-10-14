"""Explicit, idempotent demo initialization. Never runs during application startup."""

from datetime import date, timedelta

from app.common import utcnow
from app.config import Settings
from app.db import session_factory
from app.models import Activity, Club, Member, Notice, Recruitment, StudentIdentity, User
from app.security import passwords

DEMO_PASSWORD = "123456"
CLUBS = [
    ("c-1", "摄影社", "文化艺术", "📷", ["摄影", "校园纪实", "户外活动"]),
    ("c-2", "街舞社", "文化艺术", "🕺", ["街舞", "舞台"]),
    ("c-3", "辩论社", "学术科技", "🎤", ["辩论", "表达"]),
    ("c-4", "篮球社", "体育竞技", "🏀", ["篮球", "运动"]),
    ("c-5", "志愿者协会", "志愿服务", "🤝", ["公益", "志愿"]),
    ("c-6", "机器人社", "学术科技", "🤖", ["编程", "机器人"]),
    ("c-7", "文学社", "文化艺术", "📚", ["阅读", "写作"]),
    ("c-8", "羽毛球社", "体育竞技", "🏸", ["运动", "羽毛球"]),
]


def seed(sessions) -> None:
    with sessions.begin() as db:
        for club_id, name, category, logo, tags in CLUBS:
            if not db.get(Club, club_id):
                db.add(
                    Club(
                        id=club_id,
                        name=name,
                        category=category,
                        logo=logo,
                        description=f"欢迎加入{name}，一起发现校园生活的精彩。",
                        introduction=f"<p>{name}定期组织交流与实践活动。</p>",
                        founded_at=date(2015, 9, 1),
                        tags=tags,
                    )
                )
        db.flush()
        people = [
            ("u-student", "林晓", "2024001", "linxiao@campus.edu.cn", "student", None),
            ("u-club", "陈光影", "2021002", "chensy@campus.edu.cn", "clubAdmin", "c-1"),
            ("u-admin", "系统管理员", "admin", "admin@campus.edu.cn", "admin", None),
        ]
        for user_id, name, number, email, role, club_id in people:
            if not db.get(User, user_id):
                db.add(
                    User(
                        id=user_id,
                        name=name,
                        student_no=number,
                        email=email,
                        role=role,
                        club_id=club_id,
                        password_hash=passwords.hash(DEMO_PASSWORD),
                    )
                )
        identities = [
            ("2024001", "林晓", "linxiao@campus.edu.cn"),
            ("2021002", "陈光影", "chensy@campus.edu.cn"),
            ("2024099", "张三", "zhangsan@campus.edu.cn"),
            ("2024100", "李四", "lisi@campus.edu.cn"),
        ]
        for number, name, email in identities:
            if not db.get(StudentIdentity, number):
                db.add(StudentIdentity(student_no=number, name=name, email=email))
        db.flush()
        if not db.get(Member, "m-owner"):
            db.add(Member(id="m-owner", club_id="c-1", user_id="u-club", role="owner"))
        if not db.get(Notice, "notice-1"):
            db.add(
                Notice(
                    id="notice-1",
                    club_id="c-1",
                    title="欢迎参加秋季招新",
                    content="欢迎热爱摄影的同学提交入社申请。",
                )
            )
        if not db.get(Recruitment, "rc-1"):
            db.add(
                Recruitment(
                    id="rc-1",
                    club_id="c-1",
                    title="摄影社秋季招新",
                    content="不限器材基础，提供入门培训。",
                    deadline=date.today() + timedelta(days=14),
                )
            )
        now = utcnow()
        for index in range(1, 9):
            activity_id = f"a-{index}"
            if not db.get(Activity, activity_id):
                db.add(
                    Activity(
                        id=activity_id,
                        club_id=f"c-{index}",
                        title=f"{CLUBS[index - 1][1]}交流会",
                        description="面向全校学生的兴趣交流与实践活动。",
                        cover=CLUBS[index - 1][3],
                        location="大学生活动中心",
                        start_time=now + timedelta(days=index),
                        end_time=now + timedelta(days=index, hours=2),
                        capacity=50,
                        type="实践",
                        status="published",
                    )
                )


if __name__ == "__main__":
    factory = session_factory(Settings())
    try:
        seed(factory)
        print("演示数据初始化完成；已有数据未重置。演示密码为 123456，仅用于课堂演示。")
    finally:
        factory.kw["bind"].dispose()
