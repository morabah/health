from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Doctor, User
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def search_doctors(
    db: AsyncSession,
    specialty: Optional[str] = None,
    location: Optional[str] = None,
    languages: Optional[str] = None,
    name: Optional[str] = None,
    max_fee: Optional[float] = None
) -> List[Dict[str, Any]]:
    try:
        query = select(Doctor).join(User)
        if specialty:
            query = query.filter(Doctor.specialty == specialty)
        if location:
            query = query.filter(Doctor.location.like(f"%{location}%"))
        if languages:
            query = query.filter(Doctor.languages.like(f"%{languages}%"))
        if name:
            query = query.filter(
                (User.first_name.like(f"%{name}%")) | 
                (User.last_name.like(f"%{name}%"))
            )
        if max_fee is not None:
            query = query.filter(Doctor.consultation_fee <= max_fee)
        result = await db.execute(query)
        doctors = result.scalars().all()
        doctor_list = []
        for doctor in doctors:
            doctor_list.append({
                "id": doctor.id,
                "first_name": doctor.user.first_name,
                "last_name": doctor.user.last_name,
                "specialty": doctor.specialty,
                "location": doctor.location,
                "languages": doctor.languages,
                "consultation_fee": doctor.consultation_fee,
                "email": doctor.user.email
            })
        return doctor_list
    except Exception as e:
        logger.error(f"Error in async doctor search: {str(e)}")
        raise
