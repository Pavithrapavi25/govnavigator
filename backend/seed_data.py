from database import SessionLocal, engine, Base
from models import State, Service


print("Starting GovNavigator database seed...")


# =========================================================
# CREATE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)

print("Database tables ready.")


# =========================================================
# DATABASE SESSION
# =========================================================

db = SessionLocal()


try:

    # =====================================================
    # STATES
    # =====================================================

    states_data = [
        ("Andhra Pradesh", "State"),
        ("Arunachal Pradesh", "State"),
        ("Assam", "State"),
        ("Bihar", "State"),
        ("Chhattisgarh", "State"),
        ("Goa", "State"),
        ("Gujarat", "State"),
        ("Haryana", "State"),
        ("Himachal Pradesh", "State"),
        ("Jharkhand", "State"),
        ("Karnataka", "State"),
        ("Kerala", "State"),
        ("Madhya Pradesh", "State"),
        ("Maharashtra", "State"),
        ("Manipur", "State"),
        ("Meghalaya", "State"),
        ("Mizoram", "State"),
        ("Nagaland", "State"),
        ("Odisha", "State"),
        ("Punjab", "State"),
        ("Rajasthan", "State"),
        ("Sikkim", "State"),
        ("Tamil Nadu", "State"),
        ("Telangana", "State"),
        ("Tripura", "State"),
        ("Uttar Pradesh", "State"),
        ("Uttarakhand", "State"),
        ("West Bengal", "State"),

        ("Andaman and Nicobar Islands", "Union Territory"),
        ("Chandigarh", "Union Territory"),
        ("Dadra and Nagar Haveli and Daman and Diu", "Union Territory"),
        ("Delhi", "Union Territory"),
        ("Jammu and Kashmir", "Union Territory"),
        ("Ladakh", "Union Territory"),
        ("Lakshadweep", "Union Territory"),
        ("Puducherry", "Union Territory"),
    ]


    for name, state_type in states_data:

        existing_state = (
            db.query(State)
            .filter(State.name == name)
            .first()
        )

        if not existing_state:

            state = State(
                name=name,
                state_type=state_type
            )

            db.add(state)


    db.commit()

    print("States inserted successfully.")


    # =====================================================
    # SERVICES
    # =====================================================

    services_data = [

        {
            "name": "PAN Card",
            "category": "Identity Document",
            "description": "PAN card application and related services.",
            "eligibility": "Eligible Indian citizens and entities.",
            "documents": "Identity proof, address proof and applicable documents.",
            "steps": "Visit the official Income Tax Department portal and complete the applicable PAN application.",
            "fees": "Applicable service charges may apply.",
            "processing_time": "Varies depending on verification.",
            "official_portal_name": "Income Tax Department",
            "official_portal_url": "https://www.incometax.gov.in/",
        },

        {
            "name": "Aadhaar Services",
            "category": "Identity Document",
            "description": "Aadhaar enrolment, update and related services.",
            "eligibility": "Eligible residents of India.",
            "documents": "Valid identity and address documents as applicable.",
            "steps": "Use the official UIDAI website or an authorised Aadhaar centre.",
            "fees": "Some services may have applicable charges.",
            "processing_time": "Varies by service.",
            "official_portal_name": "UIDAI",
            "official_portal_url": "https://uidai.gov.in/",
        },

        {
            "name": "Passport Services",
            "category": "Travel Document",
            "description": "Passport application, renewal and related services.",
            "eligibility": "Eligible Indian citizens.",
            "documents": "Documents depend on the passport service.",
            "steps": "Register on Passport Seva, complete the application, pay applicable fees and attend the required appointment.",
            "fees": "Depends on passport type and service.",
            "processing_time": "Varies by service and verification.",
            "official_portal_name": "Passport Seva",
            "official_portal_url": "https://www.passportindia.gov.in/",
        },

        {
            "name": "Voter Services",
            "category": "Election Services",
            "description": "Voter registration and related electoral services.",
            "eligibility": "Eligible Indian citizens according to applicable electoral rules.",
            "documents": "Applicable identity, age and residence documents.",
            "steps": "Use the official Election Commission voter services portal.",
            "fees": "Basic voter registration services are generally free.",
            "processing_time": "Depends on verification.",
            "official_portal_name": "Election Commission of India",
            "official_portal_url": "https://voters.eci.gov.in/",
        },

        {
            "name": "Driving Licence",
            "category": "Transport",
            "description": "Learner and driving licence related services.",
            "eligibility": "Applicants meeting applicable age and legal requirements.",
            "documents": "Identity, address and other required documents.",
            "steps": "Apply through the official Parivahan service and complete the applicable tests and verification.",
            "fees": "Depends on the service.",
            "processing_time": "Varies by transport authority.",
            "official_portal_name": "Parivahan",
            "official_portal_url": "https://parivahan.gov.in/",
        },

        {
            "name": "Vehicle Registration",
            "category": "Transport",
            "description": "Vehicle registration and related transport services.",
            "eligibility": "Vehicle owners subject to applicable registration requirements.",
            "documents": "Vehicle and ownership documents as required.",
            "steps": "Use the official transport service and follow the applicable registration process.",
            "fees": "Depends on vehicle and applicable registration requirements.",
            "processing_time": "Varies by transport authority.",
            "official_portal_name": "Parivahan",
            "official_portal_url": "https://parivahan.gov.in/",
        },

        {
            "name": "Income Certificate",
            "category": "Certificate",
            "description": "Certificate used to establish income for applicable government purposes.",
            "eligibility": "Eligible residents according to applicable state rules.",
            "documents": "Identity proof, address proof and income-related documents as applicable.",
            "steps": "Apply through the relevant state government service portal or designated authority.",
            "fees": "Depends on the state and service.",
            "processing_time": "Depends on the concerned authority.",
            "official_portal_name": "National Government Services Portal",
            "official_portal_url": "https://services.india.gov.in/",
        },

        {
            "name": "Caste Certificate",
            "category": "Certificate",
            "description": "Certificate used to establish caste or category status for applicable government purposes.",
            "eligibility": "Eligible applicants according to applicable state rules.",
            "documents": "Identity, address and supporting documents as applicable.",
            "steps": "Apply through the relevant state government portal or designated authority.",
            "fees": "Depends on the state and service.",
            "processing_time": "Depends on the concerned authority.",
            "official_portal_name": "National Government Services Portal",
            "official_portal_url": "https://services.india.gov.in/",
        },

        {
            "name": "Birth Certificate",
            "category": "Civil Registration",
            "description": "Birth registration and certificate services.",
            "eligibility": "Births occurring within the applicable jurisdiction.",
            "documents": "Documents vary according to the registration circumstances.",
            "steps": "Submit the birth registration/application to the appropriate local authority.",
            "fees": "Depends on the authority and circumstances.",
            "processing_time": "Depends on the local registration authority.",
            "official_portal_name": "National Government Services Portal",
            "official_portal_url": "https://services.india.gov.in/",
        },

        {
            "name": "Death Certificate",
            "category": "Civil Registration",
            "description": "Death registration and certificate services.",
            "eligibility": "Deaths occurring within the applicable jurisdiction.",
            "documents": "Documents vary according to circumstances and local authority.",
            "steps": "Register the death with the appropriate local authority and submit required information.",
            "fees": "Depends on the authority and circumstances.",
            "processing_time": "Depends on the local registration authority.",
            "official_portal_name": "National Government Services Portal",
            "official_portal_url": "https://services.india.gov.in/",
        },

        {
            "name": "Government Schemes",
            "category": "Welfare Scheme",
            "description": "Information about government welfare schemes and citizen benefits.",
            "eligibility": "Depends on the individual government scheme.",
            "documents": "Depends on the selected scheme.",
            "steps": "Identify the scheme, verify eligibility and apply through the relevant official channel.",
            "fees": "Depends on the scheme.",
            "processing_time": "Depends on the scheme and implementing authority.",
            "official_portal_name": "MyScheme",
            "official_portal_url": "https://www.myscheme.gov.in/",
        },

        {
            "name": "National Government Services",
            "category": "Citizen Services",
            "description": "Search for government services provided by central and state governments.",
            "eligibility": "Depends on the individual service.",
            "documents": "Depends on the selected service.",
            "steps": "Search for the required service and follow the instructions provided by the relevant government authority.",
            "fees": "Depends on the selected service.",
            "processing_time": "Depends on the selected service.",
            "official_portal_name": "National Government Services Portal",
            "official_portal_url": "https://services.india.gov.in/",
        },
    ]


    for data in services_data:

        existing_service = (
            db.query(Service)
            .filter(Service.name == data["name"])
            .first()
        )

        if not existing_service:

            service = Service(
                name=data["name"],
                category=data["category"],
                description=data["description"],
                eligibility=data["eligibility"],
                documents=data["documents"],
                steps=data["steps"],
                fees=data["fees"],
                processing_time=data["processing_time"],
                official_portal_name=data["official_portal_name"],
                official_portal_url=data["official_portal_url"],
            )

            db.add(service)


    db.commit()

    print("Services inserted successfully.")


    # =====================================================
    # FINAL DATABASE COUNT
    # =====================================================

    state_count = db.query(State).count()
    service_count = db.query(Service).count()


    print()
    print("==============================================")
    print("GovNavigator Database Seed Completed")
    print("==============================================")
    print(f"States / UTs : {state_count}")
    print(f"Services     : {service_count}")
    print("==============================================")


except Exception as error:

    db.rollback()

    print()
    print("DATABASE ERROR:")
    print(error)


finally:

    db.close()