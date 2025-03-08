from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from async_database import get_async_db
from models import Doctor, Patient, Appointment, User
from typing import List, Optional
from pydantic import BaseModel
import datetime

app = FastAPI(title="Health Appointment API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DoctorBase(BaseModel):
    specialty: str
    location: str
    languages: str
    consultation_fee: float

class DoctorResponse(DoctorBase):
    id: int
    first_name: str
    last_name: str
    
    class Config:
        orm_mode = True

class AppointmentBase(BaseModel):
    doctor_id: int
    appointment_date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    reason: str

class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    patient_name: str
    
    class Config:
        orm_mode = True

@app.get("/api/doctors/", response_model=List[DoctorResponse])
async def get_doctors(
    db: AsyncSession = Depends(get_async_db),
    specialty: Optional[str] = None,
    location: Optional[str] = None
):
    query = select(Doctor).join(User)
    
    if specialty:
        query = query.filter(Doctor.specialty == specialty)
    if location:
        query = query.filter(Doctor.location.like(f"%{location}%"))
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    response = []
    for doctor in doctors:
        response.append({
            "id": doctor.id,
            "first_name": doctor.user.first_name,
            "last_name": doctor.user.last_name,
            "specialty": doctor.specialty,
            "location": doctor.location,
            "languages": doctor.languages,
            "consultation_fee": doctor.consultation_fee
        })
    
    return response

@app.get("/api/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_async_db)):
    query = select(Doctor).filter(Doctor.id == doctor_id).join(User)
    result = await db.execute(query)
    doctor = result.scalars().first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return {
        "id": doctor.id,
        "first_name": doctor.user.first_name,
        "last_name": doctor.user.last_name,
        "specialty": doctor.specialty,
        "location": doctor.location,
        "languages": doctor.languages,
        "consultation_fee": doctor.consultation_fee
    }

@app.get("/api/appointments/{patient_id}", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    patient_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    query = select(Appointment).filter(
        Appointment.patient_id == patient_id
    ).join(Doctor).join(Patient).join(User, Doctor.user_id == User.id)
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    response = []
    for appointment in appointments:
        response.append({
            "id": appointment.id,
            "doctor_id": appointment.doctor_id,
            "appointment_date": appointment.appointment_date,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "reason": appointment.reason,
            "status": appointment.status,
            "patient_name": f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}"
        })
    
    return response
