WELCOME = "Дербес шот нөмірін жаз:"

ASK_ACCOUNT_AGAIN = "Дербес шотты қайта жаз:"

INVALID_ACCOUNT_FORMAT = "Формат қате. Тек цифр (мысалы: 123456789)."


def confirm_account_text(account: str) -> str:
    return f"Дербес шот: {account}\n\nДұрыс па?"


CHOOSE_APPLICATION_TYPE = "Өтінім түрін таңда:"

TYPE_METER_NOT_WORKING = "🔧 Счетчик жұмыс жасамайды"
TYPE_MPI_REMOVAL = "📅 МПИ-ге шешу"
TYPE_GAS_LEAK = "⚠️ Есептеу құралынан газ шығуы"

# --- METER_NOT_WORKING ---
ASK_METER_PHOTO = "📷 Есептеу құралының суретін камерамен түсір (галереядан жіберме)."
NOT_A_PHOTO = "Сурет керек."
ASK_LOCATION = "Геолокацияны жібер."
SEND_LOCATION_BUTTON = "📍 Геолокацияны жіберу"
NOT_A_LOCATION = "Төмендегі батырманы бас."


def meter_summary_text(account: str) -> str:
    return (
        f"Дербес шот: {account}\n"
        f"Өтінім түрі: Счетчик жұмыс жасамайды\n"
        f"Фото: ✅\n"
        f"Геолокация: ✅\n\n"
        f"Жіберу керек пе?"
    )


# --- MPI_REMOVAL ---
ASK_MPI_DATE = "МПИ күнін жаз (ДД.ММ.ГГГГ, мысалы 25.09.2026)."
INVALID_DATE_FORMAT = "Формат қате. Мысал: 25.09.2026"
INVALID_DATE_PAST = "Өткен күн жарамсыз."
INVALID_DATE_TOO_FAR = "Тым алыс күн."


def mpi_summary_text(account: str, date_str: str) -> str:
    return (
        f"Дербес шот: {account}\n"
        f"Өтінім түрі: МПИ-ге шешу\n"
        f"Күні: {date_str}\n\n"
        f"Дұрыс па?"
    )


# --- GAS_LEAK ---
GAS_LEAK_WARNING = "⚠️ Газ иісі қатты болса — дереу авариялық қызметке хабарлас."


def gas_leak_emergency_phone_text(phone: str) -> str:
    return f"☎️ Авариялық қызмет: {phone}"


ASK_GAS_METER_PHOTO = "📷 Есептеу құралының суретін камерамен түсір (галереядан жіберме)."
ASK_GAS_LEAK_PHOTO = "📷 Газ шығып тұрған жердің суретін камерамен түсір (галереядан жіберме)."


def gas_leak_summary_text(account: str) -> str:
    return (
        f"⚠️ Өтінім түрі:\nЕсептеу құралынан газ шығуы\n\n"
        f"Дербес шот: {account}\n"
        f"Есептеу құралының фотосы: ✅\n"
        f"Газ шығып жатқан жердің фотосы: ✅\n"
        f"Геолокация: ✅\n\n"
        f"Жіберу керек пе?"
    )


def success_text(application_number: str) -> str:
    return f"✅ Қабылданды.\n\nНөмір: {application_number}\n\nСтатусты осы нөмір арқылы тексер."


CANCELLED = "❌ Тоқтатылды. Жаңа өтінім үшін /start бас."
SOMETHING_WENT_WRONG = "Қате шықты. Қайталап көр немесе /start бас."
ACCOUNT_NOT_SET = "Алдымен дербес шотты жаз. /start бас."

MAIN_MENU_NEW_REQUEST = "📝 Өтінім қалдыру"
MAIN_MENU_MY_REQUESTS = "📋 Менің өтінімдерім"
MAIN_MENU_CONTACT = "☎️ Байланыс"

MY_REQUESTS_EMPTY = "Өтінімдер жоқ."
MY_REQUESTS_TITLE = "Соңғы өтінімдер:"

STATUS_LABELS = {
    "NEW": "🆕 Жаңа",
    "IN_PROGRESS": "🟡 Өңделуде",
    "COMPLETED": "🟢 Аяқталды",
    "REJECTED": "🔴 Қабылданбады",
}

TYPE_LABELS = {
    "METER_NOT_WORKING": "Счетчик жұмыс жасамайды",
    "MPI_REMOVAL": "МПИ-ге шешу",
    "GAS_LEAK": "Есептеу құралынан газ шығуы",
}

BACK = "⬅️ Артқа"
CANCEL = "❌ Бас тарту"
CONFIRM_CORRECT = "✅ Дұрыс"
CONFIRM_EDIT = "✏️ Өзгерту"
CONFIRM_SEND = "✅ Жіберу"
CONFIRM_SEND_URGENT = "🚨 Жіберу"
CONFIRM_EDIT_DATE = "✏️ Күнді өзгерту"


def contact_text(organization_name: str, contact_phone: str, emergency_phone: str) -> str:
    return f"{organization_name}\n\n☎️ Телефон: {contact_phone}\n🚨 Авария: {emergency_phone}"
