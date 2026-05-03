"""種子資料腳本 - 建立開發/展示用的範例資料"""
import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.database import AsyncSessionLocal, create_tables
from app.models.user import User, UserConsent
from app.models.vehicle import UserVehicle
from app.models.policy import Policy, PolicyItem, PaymentMethod, RenewalQuote
from app.models.notification import Notification
from app.models.rental import RentalCar
from app.models.inspection import InspectionStation
from app.database import generate_uuid


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as db:
        # ========== 使用者 ==========
        user = User(
            id="demo-user-001",
            phone="0912345678",
            name="陳大明",
            email="daming.chen@example.com",
            address="台北市大安區忠孝東路四段100號",
            registered_address="台北市大安區忠孝東路四段100號",
            emergency_contact_name="陳小美",
            emergency_contact_phone="0923456789",
            emergency_contact_relation="配偶",
        )
        db.add(user)

        # 個資同意
        for consent_type in ["privacy_policy", "location", "push_notification"]:
            db.add(UserConsent(
                user_id=user.id, consent_type=consent_type, is_granted=True,
                granted_at=datetime.now(timezone.utc),
            ))
        db.add(UserConsent(
            user_id=user.id, consent_type="marketing", is_granted=False,
        ))

        # ========== 車輛 ==========
        vehicle1 = UserVehicle(
            id="vehicle-001", user_id=user.id, plate_number="ABC-1234",
            brand="Toyota", model="Corolla Cross", year=2023, color="白色",
            vin="JTDKN3DU5A0000001", engine_cc=1800, is_primary=True,
        )
        vehicle2 = UserVehicle(
            id="vehicle-002", user_id=user.id, plate_number="XYZ-5678",
            brand="Honda", model="Fit", year=2021, color="藍色",
            engine_cc=1500,
        )
        db.add_all([vehicle1, vehicle2])

        # ========== 保單 - 即將到期 ==========
        today = date.today()
        policy1 = Policy(
            id="policy-001", user_id=user.id, vehicle_id=vehicle1.id,
            insurer_name="富邦產險", policy_number="FBN-2025-001234",
            status="active", start_date=today - timedelta(days=300),
            end_date=today + timedelta(days=65), total_premium=Decimal("18500"),
        )
        db.add(policy1)

        # 保單項目
        items_data = [
            ("強制汽車責任保險", Decimal("2000000"), None, Decimal("1600"), True, []),
            ("任意第三人責任險-體傷", Decimal("3000000"), None, Decimal("3200"), True, [
                {"category": "第三人責任不賠", "description": "被保險人故意行為所致", "scenario": "故意駕車撞人"},
                {"category": "第三人責任不賠", "description": "被保險人飲酒超過法定標準", "scenario": "酒後駕車發生事故，第三人責任險不理賠"},
            ]),
            ("任意第三人責任險-財損", Decimal("1000000"), None, Decimal("1800"), True, [
                {"category": "第三人責任不賠", "description": "被保險人向同居家屬求償", "scenario": "撞到自己家人的車"},
            ]),
            ("車體損失險（甲式）", Decimal("800000"), Decimal("3000"), Decimal("8500"), True, [
                {"category": "車體損失不賠", "description": "輪胎單獨破損", "scenario": "僅輪胎爆胎而車身無損"},
                {"category": "車體損失不賠", "description": "自然耗損或機械故障", "scenario": "引擎老化故障非事故造成"},
                {"category": "車體損失不賠", "description": "酒後駕車", "scenario": "酒後駕車發生事故，車體損失險不理賠"},
            ]),
            ("竊盜損失險", Decimal("600000"), Decimal("10000"), Decimal("2200"), True, [
                {"category": "竊盜不賠", "description": "車內物品遭竊", "scenario": "車窗被打破但車輛未被盜走，車內物品不賠"},
                {"category": "竊盜不賠", "description": "受託人或使用人竊盜", "scenario": "將車借給朋友後朋友據為己有"},
            ]),
            ("超額責任險", Decimal("10000000"), None, Decimal("1200"), True, []),
        ]
        for name, coverage, deductible, premium, active, exclusions in items_data:
            db.add(PolicyItem(
                policy_id=policy1.id, item_name=name, coverage_limit=coverage,
                deductible=deductible, premium=premium, is_active=active,
                exclusions=json.dumps(exclusions, ensure_ascii=False) if exclusions else None,
            ))

        # ========== 保單2 - 已到期（無超額） ==========
        policy2 = Policy(
            id="policy-002", user_id=user.id, vehicle_id=vehicle2.id,
            insurer_name="國泰產險", policy_number="CTY-2024-005678",
            status="expired", start_date=today - timedelta(days=400),
            end_date=today - timedelta(days=35), total_premium=Decimal("12800"),
        )
        db.add(policy2)
        for name, coverage, premium in [
            ("強制汽車責任保險", Decimal("2000000"), Decimal("1500")),
            ("任意第三人責任險-體傷", Decimal("2000000"), Decimal("2800")),
            ("任意第三人責任險-財損", Decimal("500000"), Decimal("1200")),
            ("車體損失險（乙式）", Decimal("500000"), Decimal("7300")),
        ]:
            db.add(PolicyItem(
                policy_id=policy2.id, item_name=name, coverage_limit=coverage,
                premium=premium, is_active=True,
            ))

        # ========== 付款方式 ==========
        db.add(PaymentMethod(
            user_id=user.id, method_type="credit_card", card_brand="visa",
            last_four="4567", bank_name="中國信託", is_default=True,
        ))
        db.add(PaymentMethod(
            user_id=user.id, method_type="credit_card", card_brand="mastercard",
            last_four="8901", bank_name="國泰世華",
        ))

        # ========== 通知 ==========
        notifications_data = [
            ("保單到期提醒", f"您的富邦產險保單（FBN-2025-001234）將於 {(today + timedelta(days=65)).strftime('%Y-%m-%d')} 到期，建議開始準備續保。", "renewal_reminder", "policy", "policy-001"),
            ("國泰保單已到期", "您的國泰產險保單已到期，目前 Honda Fit (XYZ-5678) 處於無保障狀態，請儘速投保。", "renewal_reminder", "policy", "policy-002"),
            ("系統更新通知", "車險智能服務平台已更新至 v1.0，新增車禍緊急處理功能，歡迎使用。", "system", None, None),
        ]
        for title, body, ntype, ref_type, ref_id in notifications_data:
            db.add(Notification(
                user_id=user.id, title=title, body=body,
                notification_type=ntype, reference_type=ref_type, reference_id=ref_id,
            ))

        # ========== 租車行 ==========
        rentals = [
            ("格上租車", "台北忠孝店", "台北市大安區忠孝東路四段201號", "02-27711234", 25.0415, 121.5520, 1200, 2500, True, True, True, 4.3),
            ("和運租車", "台北敦化店", "台北市松山區敦化北路100號", "02-25451234", 25.0520, 121.5490, 1000, 2200, False, True, True, 4.1),
            ("小馬租車", "台北站前店", "台北市中正區忠孝西路一段50號", "02-23711234", 25.0460, 121.5170, 800, 1800, True, False, False, 3.9),
            ("IWS 租車", "台北松山店", "台北市松山區南京東路五段88號", "02-27601234", 25.0510, 121.5560, 900, 2000, True, True, False, 4.5),
        ]
        for name, branch, addr, phone, lat, lng, rate_min, rate_max, partner, is24, delivery, rating in rentals:
            db.add(RentalCar(
                company_name=name, branch_name=branch, address=addr, phone=phone,
                latitude=lat, longitude=lng, daily_rate_min=Decimal(str(rate_min)),
                daily_rate_max=Decimal(str(rate_max)), is_partner=partner,
                is_24hr=is24, has_delivery=delivery, rating=Decimal(str(rating)),
                operating_hours="08:00-22:00",
            ))

        # ========== 驗車廠 ==========
        stations = [
            ("台北市立聯合汽車檢驗場", "台北市", "中山區", "台北市中山區濱江街200號", "02-25161234", 25.0690, 121.5320),
            ("新北市汽車檢驗所", "新北市", "板橋區", "新北市板橋區四川路一段88號", "02-29521234", 25.0150, 121.4580),
            ("桃園監理站", "桃園市", "桃園區", "桃園市桃園區中山路500號", "03-3391234", 24.9930, 121.3010),
        ]
        for name, city, district, addr, phone, lat, lng in stations:
            db.add(InspectionStation(
                station_name=name, city=city, district=district, address=addr,
                phone=phone, latitude=lat, longitude=lng,
                operating_hours="週一至週五 08:00-17:00",
                supports_motorcycle=True, supports_heavy=False,
                booking_url="https://www.mvdis.gov.tw",
            ))

        await db.commit()
        print("種子資料建立完成！")
        print(f"  使用者: {user.name} ({user.phone})")
        print(f"  車輛: {vehicle1.plate_number}, {vehicle2.plate_number}")
        print(f"  保單: {policy1.policy_number}, {policy2.policy_number}")
        print(f"  租車行: {len(rentals)} 家")
        print(f"  驗車廠: {len(stations)} 家")


if __name__ == "__main__":
    asyncio.run(seed())
