from models import db, Province, District
from run import create_app

app = create_app(allow=False)

def seed_provinces_and_districts():
    with app.app_context():
        if Province.query.count() == 0:
            provinces = [
                {"name": "Northern Province", "districts": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"]},
                {"name": "Southern Province", "districts": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"]},
                {"name": "Eastern Province", "districts": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"]},
                {"name": "Western Province", "districts": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"]},
                {"name": "Kigali City", "districts": ["Gasabo", "Kicukiro", "Nyarugenge"]},
            ]

            for province_data in provinces:
                province = Province(name=province_data["name"])
                db.session.add(province)
                db.session.flush()  # Flush to get the provinceId for districts

                for district_name in province_data["districts"]:
                    district = District(name=district_name, provinceId=province.provinceId)
                    db.session.add(district)

            db.session.commit()
            print("Database seeded successfully!")
        else:
            print("Data already exists. No action taken.")

if __name__ == "__main__":
    seed_provinces_and_districts()
