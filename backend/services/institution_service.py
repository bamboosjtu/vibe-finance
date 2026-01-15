from typing import List

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from models.institution import Institution


def create_institution(session: Session, name: str) -> Institution:
    institution = Institution(name=name)
    session.add(institution)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("institution name already exists")
    session.refresh(institution)
    return institution


def list_institutions(session: Session) -> List[Institution]:
    statement = select(Institution).order_by(Institution.id)
    return list(session.exec(statement).all())
