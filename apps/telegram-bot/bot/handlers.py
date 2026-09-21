import re
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bot.keyboards import CONTROLS, LOCATION, MAIN, date_keyboard, inline
from bot.services import Backend
from bot.states import BACK, STATUS_LABELS, TYPE_LABELS, Flow

router = Router()


def today(timezone="Asia/Qyzylorda"):
    return datetime.now(ZoneInfo(timezone)).date()


def valid_date(value, timezone="Asia/Qyzylorda"):
    try:
        parsed = datetime.strptime(value, "%d.%m.%Y").date()
        if not today(timezone) <= parsed <= date(today(timezone).year + 2, 12, 31):
            return None
        return parsed
    except ValueError:
        return None


async def prompt(message: Message, state: FSMContext, backend: Backend, timezone="Asia/Qyzylorda"):
    current, data = await state.get_state(), await state.get_data()
    account = data.get("personal_account", "")
    markup = CONTROLS
    if current == Flow.WAITING_ACCOUNT.state:
        text = "Дербес шотты қайта енгізіңіз:"
    elif current == Flow.CONFIRM_ACCOUNT.state:
        text = f"Сіз енгізген дербес шот:\n\n{account}\n\nДеректер дұрыс па?"
        markup = inline([[("✅ Дұрыс", "account:yes"), ("✏️ Өзгерту", "account:edit")]])
    elif current == Flow.SELECT_APPLICATION_TYPE.state:
        text = "Өтінім түрін таңдаңыз:"
        markup = inline(
            [
                [("🔧 Счетчик жұмыс жасамайды", "type:METER_NOT_WORKING")],
                [("📅 МПИ-ге шешу", "type:MPI_REMOVAL")],
                [("⚠️ Есептеу құралынан газ шығуы", "type:GAS_LEAK")],
            ]
        )
    elif current in {Flow.METER_WAITING_PHOTO.state, Flow.GAS_WAITING_METER_PHOTO.state}:
        text = "Есептеу құралының фотосын жіберіңіз."
    elif current == Flow.GAS_WAITING_LEAK_PHOTO.state:
        text = "Газ шығып жатқан жердің фотосын жіберіңіз."
    elif current in {Flow.METER_WAITING_LOCATION.state, Flow.GAS_WAITING_LOCATION.state}:
        text, markup = "Геолокацияңызды жіберіңіз.", LOCATION
    elif current == Flow.MPI_WAITING_DATE.state:
        text = "МПИ-ге шешу күнін енгізіңіз.\nКүнтізбеден таңдаңыз немесе ДД.ММ.ГГГГ форматында жазыңыз."
        markup = date_keyboard(today(timezone))
    else:
        kind = data["application_type"]
        text = f"{'⚠️ ' if kind == 'GAS_LEAK' else ''}Өтінім түрі: {TYPE_LABELS[kind]}\nДербес шот: {account}\n"
        if kind == "MPI_REMOVAL":
            text += f"Күні: {date.fromisoformat(data['requested_date']):%d.%m.%Y}\n\nДеректер дұрыс па?"
        else:
            text += "Есептеу құралының фотосы: ✅\n"
            if kind == "GAS_LEAK":
                text += "Газ шығып жатқан жердің фотосы: ✅\n"
            text += "Геолокация: ✅\n\nӨтінімді жібересіз бе?"
        markup = inline(
            [
                [("🚨 Жіберу" if kind == "GAS_LEAK" else "✅ Жіберу", "submit")],
                [("✏️ Күнді өзгерту" if kind == "MPI_REMOVAL" else "✏️ Өзгерту", "edit")],
            ]
        )
    sent = await message.answer(text, reply_markup=markup)
    await state.update_data(active_message_id=sent.message_id)


@router.message(CommandStart())
@router.message(Command("new"))
@router.message(F.text == "📝 Өтінім қалдыру")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Flow.WAITING_ACCOUNT)
    await state.update_data(idempotency_key=str(uuid.uuid4()))
    await message.answer(
        "Қош келдіңіз!\nӨтінім қалдыру үшін дербес шотыңызды енгізіңіз.\n\nДербес шотты енгізіңіз:",
        reply_markup=CONTROLS,
    )


async def cancel(message, state):
    await state.clear()
    await message.answer("Өтінімнен бас тартылды.", reply_markup=MAIN)


@router.message(Command("cancel"))
@router.message(F.text == "❌ Бас тарту")
async def cancel_message(message: Message, state: FSMContext):
    await cancel(message, state)


async def go_back(message, state, backend, timezone):
    current = await state.get_state()
    if current not in BACK:
        await cancel(message, state)
        return
    await state.set_state(BACK[current])
    await prompt(message, state, backend, timezone)


@router.message(F.text == "⬅️ Артқа")
async def back_message(message: Message, state: FSMContext, backend: Backend, timezone: str):
    await go_back(message, state, backend, timezone)


@router.message(Command("menu"))
async def menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Басты мәзір", reply_markup=MAIN)


@router.message(F.text == "☎️ Байланыс")
@router.message(Command("contact"))
async def contact(message: Message, backend: Backend):
    config = await backend.settings()
    text = config["organization_name"] + "\nБайланыс: " + (config["contact_phone"] or "Нөмір әлі көрсетілмеген")
    if config["emergency_phone"]:
        text += "\nАвариялық қызмет: " + config["emergency_phone"]
    await message.answer(text)


async def show_applications(message, backend, user_id, page=1):
    result = await backend.applications(user_id, page)
    if not result["items"]:
        await message.answer("Өтінімдеріңіз жоқ.", reply_markup=MAIN)
        return
    blocks = [
        f"{a['application_number']}\n{TYPE_LABELS[a['application_type']]}\n{a['created_at'][:10]} · {STATUS_LABELS[a['status']]}"
        for a in result["items"]
    ]
    rows = [[(a["application_number"], f"view:{a['id']}")] for a in result["items"]]
    navigation = []
    if page > 1:
        navigation.append(("‹ Алдыңғы", f"list:{page - 1}"))
    if result["has_more"]:
        navigation.append(("Келесі ›", f"list:{page + 1}"))
    if navigation:
        rows.append(navigation)
    await message.answer("📋 Менің өтінімдерім\n\n" + "\n\n".join(blocks), reply_markup=inline(rows, controls=False))


@router.message(F.text == "📋 Менің өтінімдерім")
@router.message(Command("applications"))
async def my_applications(message: Message, state: FSMContext, backend: Backend):
    await state.clear()
    await show_applications(message, backend, message.from_user.id)


@router.callback_query(F.data.startswith("view:"))
async def view_application(callback: CallbackQuery, backend: Backend):
    await callback.answer()
    id = callback.data.split(":")[1]
    if not id.isdigit():
        return
    a = await backend.application(callback.from_user.id, int(id))
    await callback.message.answer(
        f"{a['application_number']}\nДербес шот: {a['personal_account']}\n{TYPE_LABELS[a['application_type']]}\n{STATUS_LABELS[a['status']]}"
    )


@router.callback_query(F.data.startswith("list:"))
async def list_page(callback: CallbackQuery, backend: Backend):
    await callback.answer()
    page = callback.data.split(":")[1]
    if page.isdigit() and 1 <= int(page) <= 10000:
        await show_applications(callback.message, backend, callback.from_user.id, int(page))


@router.message(Flow.WAITING_ACCOUNT, F.text)
async def account(message: Message, state: FSMContext, backend: Backend, timezone: str):
    value = message.text.strip()
    if not re.fullmatch(r"[0-9]{6,20}", value):
        await message.answer("Дербес шот 6–20 цифрдан тұруы керек. Қайта енгізіңіз:", reply_markup=CONTROLS)
        return
    await state.update_data(personal_account=value)
    await state.set_state(Flow.CONFIRM_ACCOUNT)
    await prompt(message, state, backend, timezone)


@router.message(Flow.MPI_WAITING_DATE, F.text)
async def mpi_date(message: Message, state: FSMContext, backend: Backend, timezone: str):
    value = valid_date(message.text, timezone)
    if value is None:
        await message.answer("Күн дұрыс емес. Бүгіннен бастап екі жыл шегінде ДД.ММ.ГГГГ форматымен енгізіңіз.")
        return
    await state.update_data(requested_date=value.isoformat())
    await state.set_state(Flow.MPI_CONFIRM)
    await prompt(message, state, backend, timezone)


@router.message(Flow.METER_WAITING_PHOTO, F.photo)
@router.message(Flow.GAS_WAITING_METER_PHOTO, F.photo)
@router.message(Flow.GAS_WAITING_LEAK_PHOTO, F.photo)
async def photo(message: Message, state: FSMContext, backend: Backend, timezone: str):
    current = await state.get_state()
    leak = current == Flow.GAS_WAITING_LEAK_PHOTO.state
    data = await state.get_data()
    image = message.photo[-1]
    if leak and image.file_unique_id == data.get("meter_unique_id"):
        await message.answer("Газ шығып жатқан жердің бөлек фотосын жіберіңіз.")
        return
    file = await backend.upload(message.bot, message.from_user.id, image, "GAS_LEAK_PHOTO" if leak else "METER_PHOTO")
    await state.update_data(
        **(
            {"leak_photo_id": file["id"]}
            if leak
            else {"meter_photo_id": file["id"], "meter_unique_id": image.file_unique_id}
        )
    )
    next_state = {
        Flow.METER_WAITING_PHOTO.state: Flow.METER_WAITING_LOCATION,
        Flow.GAS_WAITING_METER_PHOTO.state: Flow.GAS_WAITING_LEAK_PHOTO,
        Flow.GAS_WAITING_LEAK_PHOTO.state: Flow.GAS_WAITING_LOCATION,
    }[current]
    await state.set_state(next_state)
    await prompt(message, state, backend, timezone)


@router.message(Flow.METER_WAITING_LOCATION, F.location)
@router.message(Flow.GAS_WAITING_LOCATION, F.location)
async def location(message: Message, state: FSMContext, backend: Backend, timezone: str):
    latitude, longitude = message.location.latitude, message.location.longitude
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        await message.answer("Геолокация дұрыс емес. Қайта жіберіңіз.")
        return
    current = await state.get_state()
    await state.update_data(latitude=latitude, longitude=longitude)
    await state.set_state(Flow.METER_CONFIRM if current == Flow.METER_WAITING_LOCATION.state else Flow.GAS_CONFIRM)
    await message.answer("Геолокация қабылданды.", reply_markup=CONTROLS)
    await prompt(message, state, backend, timezone)


@router.callback_query()
async def callback(callback: CallbackQuery, state: FSMContext, backend: Backend, timezone: str):
    current, data = await state.get_state(), await state.get_data()
    if not current or callback.message.message_id != data.get("active_message_id"):
        await callback.answer("Бұл батырма ескірген. Соңғы хабарламаны пайдаланыңыз.")
        return
    await callback.answer()
    action = callback.data
    if action == "noop":
        return
    if action == "cancel":
        await cancel(callback.message, state)
        return
    if action == "back":
        await go_back(callback.message, state, backend, timezone)
        return
    if current == Flow.CONFIRM_ACCOUNT.state and action in {"account:yes", "account:edit"}:
        await state.set_state(Flow.SELECT_APPLICATION_TYPE if action == "account:yes" else Flow.WAITING_ACCOUNT)
    elif current == Flow.SELECT_APPLICATION_TYPE.state and action.startswith("type:"):
        kind = action.split(":")[1]
        if kind not in TYPE_LABELS:
            return
        # Switching type clears incompatible fields but preserves the confirmed account and idempotency key.
        await state.set_data({k: data[k] for k in ["personal_account", "idempotency_key"]})
        await state.update_data(application_type=kind)
        if kind == "GAS_LEAK":
            warning = "⚠️ Газ иісі қатты сезілсе немесе қауіп төніп тұрса, авариялық газ қызметіне дереу хабарласыңыз."
            # Show the warning immediately, even if the settings API is temporarily unavailable.
            await callback.message.answer(warning, reply_markup=CONTROLS)
            from bot.services import APIError

            try:
                config = await backend.settings()
                if config["emergency_phone"]:
                    await callback.message.answer("☎️ Авариялық қызмет: " + config["emergency_phone"])
            except APIError:
                pass
        await state.set_state(
            {
                "METER_NOT_WORKING": Flow.METER_WAITING_PHOTO,
                "MPI_REMOVAL": Flow.MPI_WAITING_DATE,
                "GAS_LEAK": Flow.GAS_WAITING_METER_PHOTO,
            }[kind]
        )
    elif current == Flow.MPI_WAITING_DATE.state and action.startswith("month:"):
        try:
            month = date.fromisoformat(action.split(":")[1] + "-01")
        except ValueError:
            return
        if not today(timezone).replace(day=1) <= month <= date(today(timezone).year + 2, 12, 1):
            return
        await callback.message.edit_reply_markup(reply_markup=date_keyboard(today(timezone), month.year, month.month))
        return
    elif current == Flow.MPI_WAITING_DATE.state and action.startswith("date:"):
        try:
            date_value = date.fromisoformat(action.split(":")[1])
        except ValueError:
            return
        if valid_date(date_value.strftime("%d.%m.%Y"), timezone) is None:
            return
        await state.update_data(requested_date=date_value.isoformat())
        await state.set_state(Flow.MPI_CONFIRM)
    elif current in {Flow.METER_CONFIRM.state, Flow.MPI_CONFIRM.state, Flow.GAS_CONFIRM.state}:
        if action == "edit":
            await state.set_state(
                {
                    Flow.METER_CONFIRM.state: Flow.METER_WAITING_PHOTO,
                    Flow.MPI_CONFIRM.state: Flow.MPI_WAITING_DATE,
                    Flow.GAS_CONFIRM.state: Flow.GAS_WAITING_METER_PHOTO,
                }[current]
            )
        elif action == "submit":
            payload = {
                k: data[k]
                for k in [
                    "idempotency_key",
                    "personal_account",
                    "application_type",
                    "requested_date",
                    "latitude",
                    "longitude",
                    "meter_photo_id",
                    "leak_photo_id",
                ]
                if k in data
            }
            user = callback.from_user
            payload["user"] = {
                "telegram_user_id": user.id,
                "telegram_username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            result = await backend.create(payload)
            await state.clear()
            await callback.message.answer(
                f"✅ Өтініміңіз қабылданды.\n\nӨтінім нөмірі:\n{result['application_number']}\n\nӨтініміңіздің жағдайын осы нөмір арқылы бақылай аласыз.",
                reply_markup=MAIN,
            )
            return
        else:
            return
    else:
        return
    await prompt(callback.message, state, backend, timezone)


@router.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in {
        Flow.METER_WAITING_PHOTO.state,
        Flow.GAS_WAITING_METER_PHOTO.state,
        Flow.GAS_WAITING_LEAK_PHOTO.state,
    }:
        await message.answer(
            "Фотосуретті «Фото» ретінде жіберіңіз. Құжат немесе мәтін қабылданбайды.", reply_markup=CONTROLS
        )
    elif current in {Flow.METER_WAITING_LOCATION.state, Flow.GAS_WAITING_LOCATION.state}:
        await message.answer("📍 Геолокацияны жіберу батырмасын басыңыз.", reply_markup=LOCATION)
    elif current:
        await message.answer("Соңғы хабарламадағы батырманы пайдаланыңыз. ⬅️ Артқа немесе ❌ Бас тарту қолжетімді.")
    else:
        await message.answer("Басты мәзір", reply_markup=MAIN)
