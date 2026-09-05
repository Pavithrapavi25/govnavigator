from database import SessionLocal
from models import State, Service


db = SessionLocal()

try:
    telangana = db.query(State).filter(State.name == "Telangana").first()

    if not telangana:
        print("Telangana was not found.")
        raise SystemExit

    print("Telangana ID:", telangana.id)

    services = [
        "Income Certificate",
        "Caste Certificate",
        "Birth Certificate",
        "Death Certificate",
    ]

    for name in services:
        service = db.query(Service).filter(Service.name == name).first()

        if service:
            print(f"Updating: {service.name}")
            service.state_id = telangana.id
        else:
            print(f"NOT FOUND: {name}")

    db.commit()

    print("\nUpdate committed successfully.")

    # Verify immediately
    for name in services:
        service = db.query(Service).filter(Service.name == name).first()

        if service:
            print(
                f"{service.name} -> state_id={service.state_id}"
            )

finally:
    db.close()