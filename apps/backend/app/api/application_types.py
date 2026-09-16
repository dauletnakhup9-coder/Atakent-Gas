from fastapi import APIRouter

router = APIRouter(prefix="/application-types", tags=["application-types"])

APPLICATION_TYPE_LABELS = [
    {"value": "METER_NOT_WORKING", "label_kk": "Счетчик жұмыс жасамайды", "icon": "🔧"},
    {"value": "MPI_REMOVAL", "label_kk": "МПИ-ге шешу", "icon": "📅"},
    {"value": "GAS_LEAK", "label_kk": "Есептеу құралынан газ шығуы", "icon": "⚠️"},
]


@router.get("")
async def get_application_types():
    return APPLICATION_TYPE_LABELS
