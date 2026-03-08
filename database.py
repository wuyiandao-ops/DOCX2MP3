import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ReplacementRule(Base):
    __tablename__ = 'replacement_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_text = Column(String, nullable=False)
    replace_with = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

DATABASE_URL = "sqlite:///app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── 佛教專用預設詞庫 ──
BUDDHIST_DEFAULTS = {
    "楞伽經": "棱茄經", "楞伽": "棱茄", "伽": "茄", "般若": "波惹",
    "南無": "拿摩", "阿彌陀": "ㄜ彌陀", "舍利": "設利", "波羅蜜": "波羅密",
    "幢": "床", "剎": "差", "供養": "共養", "重重": "蟲重", "解脫": "解托",
    "梵": "飯", "毗盧遮那": "皮盧遮那"
}

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 如果資料表是空的，則匯入預設詞庫
        if db.query(ReplacementRule).count() == 0:
            for orig, target in BUDDHIST_DEFAULTS.items():
                rule = ReplacementRule(original_text=orig, replace_with=target)
                db.add(rule)
            db.commit()
    finally:
        db.close()

def get_all_rules():
    db = SessionLocal()
    try: return db.query(ReplacementRule).all()
    finally: db.close()

def add_rule(original, target):
    db = SessionLocal()
    try:
        new_rule = ReplacementRule(original_text=original, replace_with=target)
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        return new_rule
    finally: db.close()

def delete_rule(rule_id):
    db = SessionLocal()
    try:
        rule = db.query(ReplacementRule).filter(ReplacementRule.id == rule_id).first()
        if rule:
            db.delete(rule)
            db.commit()
            return True
        return False
    finally: db.close()
