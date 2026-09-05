import json
from collections import Counter

from database import SessionLocal
from models import FavoriteService, Service


# ============================================================
# GOVNAVIGATOR — COMPLETE SERVICE LINK SEEDER
# ============================================================
# Creates/updates 22 services for all 36 States/UTs:
# 22 x 36 = 792 state-specific records.
#
# IMPORTANT:
# - Existing service content is preserved.
# - Existing records with state_id=NULL are reused for Andhra Pradesh
#   where possible, so existing IDs/favorites are not unnecessarily lost.
# - State-administered services use the official State/UT service portal.
# - National services use the official national government portal.
# - No fabricated deep links are generated.
# ============================================================



SERVICES = [

    # ========================================================
    # EXISTING SERVICES
    # These are included so the seeder can safely recognize
    # services already present in the database.
    # ========================================================

    {
        "name": "Income Certificate",
        "category": "Income / Government Certificate",
        "description": "Official proof of an individual's or family's income for eligible government services, scholarships and benefits.",
        "eligibility": "Individuals who need official proof of income for a government scheme, scholarship, fee concession, reservation-related benefit or another permitted purpose.",
        "documents": [
            "Identity proof",
            "Address / residence proof",
            "Income proof such as salary certificate, salary slips, Form 16 or other applicable records",
            "Self-declaration or affidavit, where required",
            "Additional documents specified by the state authority"
        ],
        "steps": [
            "Select your state.",
            "Open the applicable official citizen-service portal.",
            "Select Income Certificate.",
            "Enter the required personal and income details.",
            "Upload the required documents.",
            "Submit the application and save the acknowledgement/reference number."
        ],
        "fees": "Fees depend on the state, authority and application channel. Verify the current fee before payment.",
        "processing_time": "Processing time varies by state and verification requirements.",
        "official_portal_name": "State Citizen Services Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Caste / Community Certificate",
        "category": "Government Certificate",
        "description": "Official documentation of caste or community status for eligible government, education and employment purposes.",
        "eligibility": "Eligible applicants who require official caste or community documentation for permitted government, educational or employment purposes.",
        "documents": [
            "Identity proof",
            "Residence proof",
            "Existing caste/community records, where available",
            "Parent or family certificate, where applicable",
            "School records or other supporting evidence, where required",
            "Affidavit/declaration, where required"
        ],
        "steps": [
            "Select your state.",
            "Open the applicable official citizen-service portal.",
            "Select the relevant caste/community certificate service.",
            "Enter applicant and community details.",
            "Upload supporting documents.",
            "Submit the application.",
            "Save the acknowledgement/reference number."
        ],
        "fees": "Fees and service charges depend on the state and application channel.",
        "processing_time": "Processing time varies according to verification requirements and the issuing authority.",
        "official_portal_name": "State Citizen Services Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "PAN Card",
        "category": "Identity Document",
        "description": "Permanent Account Number used for taxation and many financial and identification purposes in India.",
        "eligibility": "Individuals and eligible entities requiring PAN for taxation, financial transactions, employment, business or other legally permitted purposes.",
        "documents": [
            "Proof of identity",
            "Proof of address",
            "Proof of date of birth, where applicable",
            "Photograph, where required",
            "Additional documents based on applicant type"
        ],
        "steps": [
            "Use the authorised PAN application channel.",
            "Choose a new PAN or correction service.",
            "Enter the required applicant information.",
            "Submit identity and address details.",
            "Complete verification and applicable payment.",
            "Save the acknowledgement number."
        ],
        "fees": "Application charges depend on the application type and delivery method.",
        "processing_time": "Processing time varies according to verification and application method.",
        "official_portal_name": "Income Tax Department",
        "official_portal_url": "https://www.incometax.gov.in/",
        "state_id": None
    },

    {
        "name": "Birth Certificate",
        "category": "Government Certificate",
        "description": "Official record of birth used for proof of birth details and various legal and administrative purposes.",
        "eligibility": "Parents, guardians or eligible individuals can use the applicable birth-registration system for the place where the birth occurred.",
        "documents": [
            "Hospital or birth record, where applicable",
            "Parent/guardian identity proof",
            "Address information",
            "Birth details",
            "Additional documents required by the local registration authority"
        ],
        "steps": [
            "Identify the registration authority for the place of birth.",
            "Open the applicable official registration portal.",
            "Provide birth and parent details.",
            "Upload or submit supporting documents.",
            "Review the information.",
            "Submit the registration request.",
            "Save the registration/reference number."
        ],
        "fees": "Fees may depend on the registration timing, location and applicable rules.",
        "processing_time": "Processing time varies by local registration authority.",
        "official_portal_name": "Civil Registration System",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Death Certificate",
        "category": "Government Certificate",
        "description": "Official record of a person's death issued by the applicable local registration authority.",
        "eligibility": "The death should be registered with the appropriate registration authority for the place where the death occurred.",
        "documents": [
            "Medical/hospital death record, where applicable",
            "Identity details of the deceased",
            "Applicant identity proof",
            "Death details such as date and place",
            "Additional documents required by the local authority"
        ],
        "steps": [
            "Identify the local birth/death registration authority.",
            "Open the applicable official portal.",
            "Provide details of the deceased.",
            "Upload or submit supporting records.",
            "Review the information.",
            "Submit the registration/application.",
            "Save the acknowledgement/reference number."
        ],
        "fees": "Fees may depend on location, registration timing and applicable local rules.",
        "processing_time": "Processing time varies by local registration authority.",
        "official_portal_name": "Civil Registration System",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Aadhaar Services",
        "category": "Identity Document",
        "description": "Official Aadhaar enrolment, update and related services provided through authorised UIDAI channels.",
        "eligibility": "Residents seeking Aadhaar enrolment or eligible Aadhaar update services.",
        "documents": [
            "Valid identity/address documents as applicable",
            "Supporting documents required for the requested update",
            "Existing Aadhaar details, where applicable"
        ],
        "steps": [
            "Visit the official UIDAI website.",
            "Identify the required Aadhaar service.",
            "Follow the applicable online or enrolment-centre process.",
            "Provide the required documents.",
            "Complete verification/biometric requirements where applicable.",
            "Save the acknowledgement details."
        ],
        "fees": "UIDAI service charges vary depending on the type of service.",
        "processing_time": "Processing time depends on the requested Aadhaar service.",
        "official_portal_name": "UIDAI",
        "official_portal_url": "https://uidai.gov.in/",
        "state_id": None
    },

    # ========================================================
    # NEW SERVICES
    # ========================================================

    {
        "name": "Passport Services",
        "category": "Travel Document",
        "description": "Official passport application, reissue and related services through the Passport Seva system.",
        "eligibility": "Eligible Indian citizens can use the official Passport Seva system for passport applications and related services according to applicable rules.",
        "documents": [
            "Proof of identity",
            "Proof of address",
            "Proof of date of birth, where applicable",
            "Photograph or other documents as required by the application type"
        ],
        "steps": [
            "Open the official Passport Seva portal.",
            "Register/login and choose the applicable passport service.",
            "Complete the application form.",
            "Upload/provide the required documents.",
            "Pay the applicable fee and schedule an appointment where required.",
            "Attend the designated Passport Seva Kendra or applicable centre.",
            "Track the application using the official Passport Seva system."
        ],
        "fees": "Passport fees depend on the application type and service category. Verify the current fee on the official portal.",
        "processing_time": "Processing time varies according to application type, verification and other applicable requirements.",
        "official_portal_name": "Passport Seva",
        "official_portal_url": "https://www.passportindia.gov.in/",
        "state_id": None
    },

    {
        "name": "Residence / Domicile Certificate",
        "category": "Government Certificate",
        "description": "Certificate used to establish residence or domicile for eligible government, education and other official purposes.",
        "eligibility": "Applicants who need official proof of residence or domicile and satisfy the applicable state or UT requirements.",
        "documents": [
            "Identity proof",
            "Address proof",
            "Aadhaar or other accepted identification",
            "Utility bill or residence document, where applicable",
            "Self-declaration/affidavit, where required"
        ],
        "steps": [
            "Select your state or UT.",
            "Open the official state citizen-service portal.",
            "Select Residence/Domicile Certificate.",
            "Enter the applicant and residence details.",
            "Upload the required documents.",
            "Submit the application and save the acknowledgement number."
        ],
        "fees": "Fees vary by state/UT and application channel.",
        "processing_time": "Processing time varies by state and verification requirements.",
        "official_portal_name": "State Citizen Services Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Marriage Certificate",
        "category": "Legal Certificate",
        "description": "Official registration and certificate of marriage through the competent registration authority.",
        "eligibility": "Eligible couples can apply through the marriage registration authority applicable to their place of residence or marriage.",
        "documents": [
            "Identity proof of both applicants",
            "Address proof",
            "Age/date-of-birth proof",
            "Marriage photographs",
            "Marriage invitation or other supporting proof, where applicable",
            "Witness documents, where required"
        ],
        "steps": [
            "Select your state/UT.",
            "Open the applicable official registration portal.",
            "Select Marriage Registration.",
            "Enter details of both spouses.",
            "Upload required documents.",
            "Complete appointment/verification requirements where applicable.",
            "Submit and save the acknowledgement."
        ],
        "fees": "Registration fees vary by state, marriage type and applicable rules.",
        "processing_time": "Processing time varies by registration authority.",
        "official_portal_name": "State Registration Authority",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Driving Licence",
        "category": "Transport Service",
        "description": "Application and related services for learner's and driving licences through the official transport system.",
        "eligibility": "Applicants meeting the applicable age, documentation, medical and other transport requirements.",
        "documents": [
            "Proof of identity",
            "Proof of address",
            "Age/date-of-birth proof",
            "Photograph where required",
            "Medical certificate where applicable"
        ],
        "steps": [
            "Open the official Parivahan portal.",
            "Select your state/UT.",
            "Choose the appropriate licence service.",
            "Enter applicant details.",
            "Upload required documents.",
            "Pay the applicable fee.",
            "Complete the required test/appointment process."
        ],
        "fees": "Fees depend on the licence service and applicable transport rules.",
        "processing_time": "Processing time depends on appointment, testing and RTO requirements.",
        "official_portal_name": "Parivahan",
        "official_portal_url": "https://parivahan.gov.in/",
        "state_id": None
    },

    {
        "name": "Voter ID / Electoral Registration",
        "category": "Election Services",
        "description": "Official electoral registration services including new voter registration and voter-detail updates.",
        "eligibility": "Eligible Indian citizens can use the official Election Commission voter services according to applicable electoral rules.",
        "documents": [
            "Age proof",
            "Address proof",
            "Photograph",
            "Identity details",
            "Other documents required by the electoral authority"
        ],
        "steps": [
            "Open the official Election Commission voter services portal.",
            "Select new registration or the required voter service.",
            "Enter personal and address information.",
            "Upload supporting documents.",
            "Submit the application.",
            "Track the application/reference number."
        ],
        "fees": "Official voter registration services are generally provided through the Election Commission's voter services system.",
        "processing_time": "Processing time depends on electoral-roll verification.",
        "official_portal_name": "Election Commission of India",
        "official_portal_url": "https://voters.eci.gov.in/",
        "state_id": None
    },

    {
        "name": "Ration Card / Food Security",
        "category": "Food Security",
        "description": "Food-security and ration-card services administered through the relevant state/UT food and civil-supplies authority.",
        "eligibility": "Eligibility depends on the applicable state/UT food-security and public-distribution rules.",
        "documents": [
            "Identity proof",
            "Address proof",
            "Family member details",
            "Income/category information where applicable",
            "Photographs where required"
        ],
        "steps": [
            "Select your state/UT.",
            "Open the official food/civil-supplies portal.",
            "Choose the ration-card service.",
            "Enter household details.",
            "Upload supporting documents.",
            "Submit the application and save the reference number."
        ],
        "fees": "Fees depend on the state/UT and service requested.",
        "processing_time": "Processing time varies according to local verification.",
        "official_portal_name": "State Food and Civil Supplies Authority",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "EWS Certificate",
        "category": "Government Certificate",
        "description": "Economically Weaker Section certificate for eligible applicants under applicable government rules.",
        "eligibility": "Applicants meeting the applicable EWS income, asset and other eligibility requirements.",
        "documents": [
            "Identity proof",
            "Address/residence proof",
            "Income-related documents",
            "Asset/property information where required",
            "Self-declaration/affidavit where applicable"
        ],
        "steps": [
            "Select your state/UT.",
            "Open the official citizen-service portal.",
            "Select EWS/Income and Asset Certificate where available.",
            "Enter applicant and family information.",
            "Upload supporting documents.",
            "Submit the application and retain the acknowledgement."
        ],
        "fees": "Fees vary by state/UT and application method.",
        "processing_time": "Processing time varies according to verification.",
        "official_portal_name": "State Citizen Services Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Government Scholarships",
        "category": "Education",
        "description": "Government scholarship discovery and application services for eligible students.",
        "eligibility": "Eligibility depends on the particular scholarship, course, institution, category, income and other applicable conditions.",
        "documents": [
            "Student identity proof",
            "Academic records",
            "Income certificate where required",
            "Caste/community certificate where applicable",
            "Bank account details",
            "Institution details"
        ],
        "steps": [
            "Open the official National Scholarship Portal or applicable state scholarship portal.",
            "Register/login.",
            "Find the applicable scholarship.",
            "Complete the application.",
            "Upload the required documents.",
            "Submit and track verification/status."
        ],
        "fees": "Government scholarship applications generally do not require payment to private agents. Verify the official portal before submitting.",
        "processing_time": "Processing depends on institution and government verification.",
        "official_portal_name": "National Scholarship Portal",
        "official_portal_url": "https://scholarships.gov.in/",
        "state_id": None
    },

    {
        "name": "Vehicle Registration / RC",
        "category": "Transport Service",
        "description": "Vehicle registration and Registration Certificate services through the official transport system.",
        "eligibility": "Vehicle owners requiring registration or eligible registration-related services.",
        "documents": [
            "Vehicle sale/invoice documents",
            "Identity proof",
            "Address proof",
            "Insurance documents",
            "Form and vehicle documents as applicable"
        ],
        "steps": [
            "Open the official Parivahan portal.",
            "Select your state/UT.",
            "Choose the vehicle registration service.",
            "Enter vehicle and owner details.",
            "Upload/submit required documents.",
            "Complete applicable inspection and payment requirements."
        ],
        "fees": "Fees depend on vehicle type, state and registration service.",
        "processing_time": "Processing time depends on RTO verification and vehicle inspection.",
        "official_portal_name": "Parivahan",
        "official_portal_url": "https://parivahan.gov.in/",
        "state_id": None
    },

    {
        "name": "Trade / Business Licence",
        "category": "Business Service",
        "description": "Local business and trade-licence services administered by the applicable state or local authority.",
        "eligibility": "Businesses requiring a local trade or business licence according to applicable municipal/state rules.",
        "documents": [
            "Identity proof",
            "Business address proof",
            "Property/occupancy documents where applicable",
            "Business details",
            "Other documents required by the local authority"
        ],
        "steps": [
            "Select your state/UT.",
            "Identify the applicable municipal or state portal.",
            "Select Trade/Business Licence.",
            "Enter business details.",
            "Upload supporting documents.",
            "Pay the applicable fee and submit."
        ],
        "fees": "Fees vary by local authority, business type and location.",
        "processing_time": "Processing time varies by local authority.",
        "official_portal_name": "Local Authority / Municipal Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "PM-KISAN / Farmer Services",
        "category": "Agriculture",
        "description": "Government agricultural and farmer-support services including PM-KISAN-related services.",
        "eligibility": "Eligibility depends on the specific farmer scheme and applicable government rules.",
        "documents": [
            "Aadhaar/identity details",
            "Land or farmer records where applicable",
            "Bank account details",
            "Mobile number",
            "Other documents required under the scheme"
        ],
        "steps": [
            "Open the official PM-KISAN or applicable agriculture portal.",
            "Select the required farmer service.",
            "Enter applicant details.",
            "Complete required verification.",
            "Submit the application.",
            "Track the application/payment status."
        ],
        "fees": "Verify the official scheme portal. Do not pay unofficial agents for government scheme registration.",
        "processing_time": "Processing depends on verification and applicable scheme procedures.",
        "official_portal_name": "PM-KISAN",
        "official_portal_url": "https://pmkisan.gov.in/",
        "state_id": None
    },

    {
        "name": "Disability Certificate / UDID",
        "category": "Social Welfare",
        "description": "Disability certification and UDID-related services through the official government system.",
        "eligibility": "Eligible persons with disabilities can apply according to the applicable assessment and certification requirements.",
        "documents": [
            "Identity proof",
            "Address details",
            "Medical records where applicable",
            "Existing disability records where available",
            "Photograph"
        ],
        "steps": [
            "Open the official UDID portal.",
            "Register/login.",
            "Complete the disability certificate/UDID application.",
            "Upload the required documents.",
            "Attend the required medical assessment.",
            "Track the application status."
        ],
        "fees": "Verify the official UDID portal for current requirements.",
        "processing_time": "Processing depends on medical assessment and certification.",
        "official_portal_name": "UDID",
        "official_portal_url": "https://www.swavlambancard.gov.in/",
        "state_id": None
    },

    {
        "name": "Senior Citizen Certificate",
        "category": "Social Welfare",
        "description": "Certificate or related services for senior citizens where provided by the applicable state/UT authority.",
        "eligibility": "Eligibility depends on the applicable age and state/UT rules.",
        "documents": [
            "Identity proof",
            "Age/date-of-birth proof",
            "Address proof",
            "Photograph where required"
        ],
        "steps": [
            "Select your state/UT.",
            "Open the applicable official citizen-service portal.",
            "Select the senior citizen service if available.",
            "Enter applicant details.",
            "Upload documents.",
            "Submit and save the acknowledgement."
        ],
        "fees": "Fees depend on the state/UT and service.",
        "processing_time": "Processing time varies by authority.",
        "official_portal_name": "State Citizen Services Portal",
        "official_portal_url": None,
        "state_id": None
    },

    {
        "name": "Ayushman Bharat / Health Services",
        "category": "Health Services",
        "description": "Official government health-benefit and beneficiary services under applicable national health programmes.",
        "eligibility": "Eligibility depends on the applicable government health programme and beneficiary criteria.",
        "documents": [
            "Aadhaar or accepted identity document",
            "Mobile number",
            "Beneficiary/family details",
            "Other documents as required"
        ],
        "steps": [
            "Open the official National Health Authority beneficiary portal.",
            "Check beneficiary eligibility.",
            "Complete the required verification.",
            "Follow the instructions for obtaining/using the health benefit."
        ],
        "fees": "Verify eligibility and service details only through official government channels.",
        "processing_time": "Depends on beneficiary verification and service requirements.",
        "official_portal_name": "National Health Authority",
        "official_portal_url": "https://www.nha.gov.in/",
        "state_id": None
    },

    {
        "name": "Employment / Job-Seeker Registration",
        "category": "Employment",
        "description": "Government employment and job-seeker registration services through the National Career Service.",
        "eligibility": "Job seekers can register on the government employment platform and use applicable services.",
        "documents": [
            "Identity details",
            "Educational qualification information",
            "Contact information",
            "Employment/experience details where applicable",
            "Resume where applicable"
        ],
        "steps": [
            "Open the official National Career Service portal.",
            "Register as a job seeker.",
            "Complete your profile.",
            "Add education and skills.",
            "Search applicable opportunities.",
            "Apply through the official platform where available."
        ],
        "fees": "Verify the official National Career Service portal. Be cautious of anyone asking for payment for government job registration.",
        "processing_time": "Registration is subject to successful account/profile verification.",
        "official_portal_name": "National Career Service",
        "official_portal_url": "https://www.ncs.gov.in/",
        "state_id": None
    },

    {
        "name": "Pension / Social Security Services",
        "category": "Social Security",
        "description": "Government pension and social-security services for eligible beneficiaries through applicable official portals.",
        "eligibility": "Eligibility depends on the specific pension or social-security scheme and applicable central or state/UT rules.",
        "documents": [
            "Identity proof",
            "Address/residence proof",
            "Age proof where applicable",
            "Bank account details",
            "Income/category or other scheme-specific documents where required"
        ],
        "steps": [
            "Select your state/UT if a state-administered pension service applies.",
            "Open the applicable official government pension/social-security portal.",
            "Check eligibility for the relevant scheme.",
            "Complete the application with the required details.",
            "Upload/submit supporting documents.",
            "Submit and save the acknowledgement/reference number.",
            "Track the application through the official system."
        ],
        "fees": "Verify the official scheme portal. Do not pay unofficial agents for government pension registration.",
        "processing_time": "Processing time varies according to the scheme, verification and issuing authority.",
        "official_portal_name": "Government Pension / Social Security Portal",
        "official_portal_url": None,
        "state_id": None
    },
]

# ============================================================
# OFFICIAL STATE / UT PORTALS
# ============================================================

STATE_PORTALS = {
    'Andhra Pradesh': ('AP Seva', 'https://vswsonline.ap.gov.in/'),
    'Arunachal Pradesh': ('Arunachal e-Service', 'https://eservice.arunachal.gov.in/'),
    'Assam': ('Sewa Setu', 'https://sewasetu.assam.gov.in/'),
    'Bihar': ('RTPS Bihar / ServicePlus', 'https://serviceonline.bihar.gov.in/'),
    'Chhattisgarh': ('Chhattisgarh e-District', 'https://edistrict.cgstate.gov.in/'),
    'Goa': ('Goa Online - Citizen Services', 'https://goaonline.gov.in/CitizenServices'),
    'Gujarat': ('Digital Gujarat', 'https://digitalgujarat.gov.in/'),
    'Haryana': ('Saral Haryana', 'https://saralharyana.gov.in/'),
    'Himachal Pradesh': ('HIMSeva', 'https://himseva.hp.gov.in/'),
    'Jharkhand': ('Jharsewa', 'https://jharsewa.jharkhand.gov.in/'),
    'Karnataka': ('Seva Sindhu', 'https://sevasindhu.karnataka.gov.in/Sevasindhu/English'),
    'Kerala': ('e-Sevanam', 'https://services.kerala.gov.in/'),
    'Madhya Pradesh': ('MP e-Service', 'https://services.mp.gov.in/'),
    'Maharashtra': ('Aaple Sarkar - Citizen Services', 'https://aaplesarkar.mahaonline.gov.in/en/CommonForm/ViewAllServices'),
    'Manipur': ('Manipur USP', 'https://uspmanipur.mn.gov.in/'),
    'Meghalaya': ('Meghalaya Online', 'https://meghalayaone.gov.in/'),
    'Mizoram': ('Mizoram Government Services', 'https://services.india.gov.in/service/state_services?ln=en&sd_id=2643'),
    'Nagaland': ('Nagaland e-District', 'https://edistrict.nagaland.gov.in/'),
    'Odisha': ('Odisha One', 'https://odishaone.gov.in/'),
    'Punjab': ('Connect Punjab', 'https://connect.punjab.gov.in/'),
    'Rajasthan': ('e-Mitra', 'https://emitra.rajasthan.gov.in/'),
    'Sikkim': ('Sikkim GO - Government Services', 'https://sso.sikkim.gov.in/services'),
    'Tamil Nadu': ('e-Sevai', 'https://tnesevai.tn.gov.in/'),
    'Telangana': ('MeeSeva', 'https://ts.meeseva.telangana.gov.in/'),
    'Tripura': ('Tripura e-District', 'https://edistrict.tripura.gov.in/'),
    'Uttar Pradesh': ('UP e-District', 'https://edistrict.up.gov.in/'),
    'Uttarakhand': ('Apuni Sarkar', 'https://eservices.uk.gov.in/'),
    'West Bengal': ('West Bengal e-District', 'https://edistrict.wb.gov.in/'),
    'Jammu and Kashmir': ('e-UNNAT', 'https://eunnat.jk.gov.in/'),
    'Ladakh': ('Ladakh e-Seva', 'https://eseva.ladakh.gov.in/'),
    'Chandigarh': ('Chandigarh e-District', 'https://eservices.chd.gov.in/'),
    'Delhi': ('Delhi e-District', 'https://edistrict.delhi.gov.in/'),
    'Andaman and Nicobar Islands': ('Andaman e-Seva', 'https://anieseva.andaman.gov.in/'),
    'Dadra and Nagar Haveli and Daman and Diu': ('Single Window Portal', 'https://swp.dddgov.in/'),
    'Lakshadweep': ('National Government Services Portal', 'https://services.india.gov.in/service/listing'),
    'Puducherry': ('Puducherry e-District', 'https://edistrict.py.gov.in/')
}

# ============================================================
# OFFICIAL NATIONAL PORTALS
# ============================================================

NATIONAL_PORTALS = {
    'PAN Card': ('Income Tax Department - PAN', 'https://www.incometax.gov.in/'),
    'Aadhaar Services': ('UIDAI', 'https://uidai.gov.in/'),
    'Passport Services': ('Passport Seva', 'https://www.passportindia.gov.in/'),
    'Driving Licence': ('Parivahan Sewa', 'https://parivahan.gov.in/'),
    'Voter ID / Electoral Registration': ("Election Commission of India - Voters' Services", 'https://voters.eci.gov.in/'),
    'Government Scholarships': ('National Scholarship Portal - Student Services', 'https://scholarships.gov.in/Students'),
    'Vehicle Registration / RC': ('Parivahan Sewa', 'https://parivahan.gov.in/'),
    'PM-KISAN / Farmer Services': ('PM-KISAN', 'https://pmkisan.gov.in/'),
    'Disability Certificate / UDID': ('UDID / Swavlamban', 'https://www.swavlambancard.gov.in/'),
    'Ayushman Bharat / Health Services': ('National Health Authority', 'https://beneficiary.nha.gov.in/'),
    'Employment / Job-Seeker Registration': ('National Career Service', 'https://www.ncs.gov.in/')
}


# National services that are the same regardless of state/UT.
NATIONAL_SERVICES = set(NATIONAL_PORTALS.keys())

EXPECTED_STATES = list(STATE_PORTALS.keys())
EXPECTED_SERVICE_COUNT = len(SERVICES)
EXPECTED_RECORD_COUNT = len(EXPECTED_STATES) * EXPECTED_SERVICE_COUNT


def normalize_state_name(value):
    """Normalize common state/UT naming differences returned by the DB."""
    if not value:
        return ""

    value = " ".join(str(value).strip().split())
    key = value.casefold()

    aliases = {
        "andaman and nicobar islands": "Andaman and Nicobar Islands",
        "andaman & nicobar islands": "Andaman and Nicobar Islands",
        "andaman and nicobar island": "Andaman and Nicobar Islands",
        "the andaman and nicobar islands": "Andaman and Nicobar Islands",
        "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
        "the dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
        "dadra & nagar haveli and daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
        "jammu & kashmir": "Jammu and Kashmir",
        "jammu and kashmir": "Jammu and Kashmir",
        "puducherry (ut)": "Puducherry",
        "chandigarh (ut)": "Chandigarh",
        "delhi (nct)": "Delhi",
        "lakshadweep (ut)": "Lakshadweep",
        "ladakh (ut)": "Ladakh",
    }

    return aliases.get(key, value)


def get_state_lookup(db):
    """Return canonical state name -> State object without importing State."""
    # We intentionally discover states through the existing Service rows only
    # if the State model is unavailable. Normally main.py/seed_states already
    # created the states table and Service.state_id points to it.
    from models import State

    rows = db.query(State).all()

    lookup = {}
    for row in rows:
        canonical = normalize_state_name(getattr(row, "name", ""))
        if canonical:
            lookup[canonical] = row

    return lookup


def find_existing_service(db, name, state_id):
    return (
        db.query(Service)
        .filter(
            Service.name == name,
            Service.state_id == state_id,
        )
        .first()
    )


def find_legacy_service(db, name):
    """Find an old pre-state-specific record, if one exists."""
    return (
        db.query(Service)
        .filter(
            Service.name == name,
            Service.state_id.is_(None),
        )
        .order_by(Service.id.asc())
        .first()
    )


def serialize_list(value):
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        return json.dumps([value], ensure_ascii=False)

    return json.dumps(value or [], ensure_ascii=False)


def apply_service_data(row, base, portal_name, portal_url, state_id):
    """Update a Service row while preserving the original service content."""
    row.name = base["name"]
    row.category = base.get("category")
    row.description = base.get("description")
    row.eligibility = base.get("eligibility")
    row.documents = serialize_list(base.get("documents", []))
    row.steps = serialize_list(base.get("steps", []))
    row.fees = base.get("fees")
    row.processing_time = base.get("processing_time")
    row.official_portal_name = portal_name
    row.official_portal_url = portal_url
    row.state_id = state_id


def cleanup_non_target_records(db, state_lookup):
    """
    Reconcile the Service table to exactly the intended 22 x 36
    state-specific records.

    - Removes legacy/extra service rows outside SERVICES.
    - Removes duplicate rows for the same (service, state).
    - Repoints favorites from duplicate rows to the retained row.
    - Removes favorites attached to obsolete service rows.
    - Preserves one legacy state_id=NULL row per service only when it
      is migrated to Andhra Pradesh by the normal seeding logic.
    """
    expected_names = {item["name"] for item in SERVICES}
    expected_state_ids = {
        row.id for row in state_lookup.values()
        if row is not None
    }

    # We only reconcile rows that are state-scoped or obsolete legacy rows.
    # This avoids touching unrelated non-Service tables.
    all_rows = db.query(Service).all()

    # 1) Remove service rows whose names are not part of the canonical 22.
    obsolete_rows = [
        row
        for row in all_rows
        if row.name not in expected_names
    ]

    removed_obsolete = 0
    removed_duplicates = 0
    removed_obsolete_favorites = 0

    for row in obsolete_rows:
        favorites = (
            db.query(FavoriteService)
            .filter(FavoriteService.service_id == row.id)
            .all()
        )

        for favorite in favorites:
            db.delete(favorite)
            removed_obsolete_favorites += 1

        db.delete(row)
        removed_obsolete += 1

    db.flush()

    # 2) Deduplicate canonical state-specific records.
    grouped = {}

    canonical_rows = (
        db.query(Service)
        .filter(Service.state_id.in_(expected_state_ids))
        .order_by(Service.id.asc())
        .all()
        if expected_state_ids
        else []
    )

    for row in canonical_rows:
        key = (row.name.strip().casefold(), int(row.state_id))
        grouped.setdefault(key, []).append(row)

    for rows in grouped.values():
        if len(rows) <= 1:
            continue

        keep = rows[0]

        for duplicate in rows[1:]:
            favorites = (
                db.query(FavoriteService)
                .filter(FavoriteService.service_id == duplicate.id)
                .all()
            )

            for favorite in favorites:
                # The unique constraint is (user_id, service_id).
                # If the user already favorited the retained service,
                # simply remove the duplicate favorite.
                existing = (
                    db.query(FavoriteService)
                    .filter(
                        FavoriteService.user_id == favorite.user_id,
                        FavoriteService.service_id == keep.id,
                    )
                    .first()
                )

                if existing is None:
                    favorite.service_id = keep.id
                else:
                    db.delete(favorite)
                    removed_obsolete_favorites += 1

            db.delete(duplicate)
            removed_duplicates += 1

    db.flush()

    return {
        "removed_obsolete": removed_obsolete,
        "removed_duplicates": removed_duplicates,
        "removed_obsolete_favorites": removed_obsolete_favorites,
    }


def seed_services():
    db = SessionLocal()

    added = 0
    updated = 0
    migrated = 0
    missing_states = []
    missing_urls = []
    state_counts = Counter()
    service_counts = Counter()

    try:
        print("\n" + "=" * 68)
        print(" GOVNAVIGATOR — 792 OFFICIAL SERVICE LINK SEEDER")
        print("=" * 68)
        print(f"Expected states/UTs : {len(EXPECTED_STATES)}")
        print(f"Base services       : {EXPECTED_SERVICE_COUNT}")
        print(f"Expected records    : {EXPECTED_RECORD_COUNT}")
        print("=" * 68 + "\n")

        state_lookup = get_state_lookup(db)

        cleanup_stats = cleanup_non_target_records(db, state_lookup)
        print("CLEANUP")
        print(f"  Removed obsolete service rows : {cleanup_stats['removed_obsolete']}")
        print(f"  Removed duplicate service rows: {cleanup_stats['removed_duplicates']}")
        print(f"  Removed/repointed favorites   : {cleanup_stats['removed_obsolete_favorites']}")
        print()

        # Report any DB state names that could not be matched.
        for canonical_state in EXPECTED_STATES:
            if canonical_state not in state_lookup:
                missing_states.append(canonical_state)

        if missing_states:
            print("WARNING — these states/UTs are missing from the states table:")
            for state in missing_states:
                print(f"  - {state}")
            print()

        for canonical_state in EXPECTED_STATES:
            state_row = state_lookup.get(canonical_state)

            if not state_row:
                continue

            state_id = state_row.id
            portal_name, portal_url = STATE_PORTALS[canonical_state]

            for base in SERVICES:
                service_name = base["name"]

                if service_name in NATIONAL_SERVICES:
                    final_portal_name, final_portal_url = NATIONAL_PORTALS[
                        service_name
                    ]
                else:
                    final_portal_name, final_portal_url = (
                        portal_name,
                        portal_url,
                    )

                if not final_portal_url:
                    missing_urls.append(
                        (canonical_state, service_name)
                    )
                    continue

                row = find_existing_service(
                    db,
                    service_name,
                    state_id,
                )

                # Reuse an old state_id=NULL row for Andhra Pradesh.
                if row is None and canonical_state == "Andhra Pradesh":
                    row = find_legacy_service(
                        db,
                        service_name,
                    )

                    if row is not None:
                        migrated += 1

                if row is None:
                    row = Service(
                        name=service_name,
                        category=base.get("category"),
                        description=base.get("description"),
                        eligibility=base.get("eligibility"),
                        documents=serialize_list(
                            base.get("documents", [])
                        ),
                        steps=serialize_list(
                            base.get("steps", [])
                        ),
                        fees=base.get("fees"),
                        processing_time=base.get(
                            "processing_time"
                        ),
                        official_portal_name=final_portal_name,
                        official_portal_url=final_portal_url,
                        state_id=state_id,
                    )

                    db.add(row)
                    added += 1
                else:
                    apply_service_data(
                        row,
                        base,
                        final_portal_name,
                        final_portal_url,
                        state_id,
                    )
                    updated += 1

                state_counts[canonical_state] += 1
                service_counts[service_name] += 1

        db.commit()

        # ========================================================
        # FINAL AUDIT
        # ========================================================

        print("\n" + "=" * 68)
        print(" FINAL GOVNAVIGATOR SERVICE LINK AUDIT")
        print("=" * 68)

        target_state_ids = [
            state_lookup[state].id
            for state in EXPECTED_STATES
            if state in state_lookup
        ]

        target_rows = (
            db.query(Service)
            .filter(Service.state_id.in_(target_state_ids))
            .all()
            if target_state_ids
            else []
        )

        actual_target_count = len(target_rows)
        records_with_url = sum(
            1
            for row in target_rows
            if row.official_portal_url
        )
        records_without_url = actual_target_count - records_with_url

        unique_urls = len(
            {
                row.official_portal_url
                for row in target_rows
                if row.official_portal_url
            }
        )

        national_count = sum(
            1
            for row in target_rows
            if row.name in NATIONAL_SERVICES
        )

        state_portal_count = actual_target_count - national_count

        print(f"Expected target records : {EXPECTED_RECORD_COUNT}")
        print(f"Actual target records   : {actual_target_count}")
        print(f"Added                   : {added}")
        print(f"Updated                 : {updated}")
        print(f"Legacy records migrated : {migrated}")
        print(f"Records with URL        : {records_with_url}")
        print(f"Records without URL     : {records_without_url}")
        print(f"Unique official URLs    : {unique_urls}")
        print(f"National portal records : {national_count}")
        print(f"State portal records    : {state_portal_count}")

        total_service_rows = db.query(Service).count()
        expected_service_rows = EXPECTED_RECORD_COUNT
        extra_service_rows = max(0, total_service_rows - expected_service_rows)

        print(f"Total Service rows       : {total_service_rows}")
        print(f"Expected Service rows    : {expected_service_rows}")
        print(f"Extra Service rows       : {extra_service_rows}")

        print("\nSTATE / UT RECORD COUNTS")
        print("-" * 68)

        bad_state_counts = []

        for state in EXPECTED_STATES:
            row = state_lookup.get(state)
            count = (
                db.query(Service)
                .filter(Service.state_id == row.id)
                .count()
                if row
                else 0
            )

            status = "PASS" if count == EXPECTED_SERVICE_COUNT else "FAIL"

            print(
                f"{state:<48} {count:>3}  {status}"
            )

            if count != EXPECTED_SERVICE_COUNT:
                bad_state_counts.append(
                    (state, count)
                )

        print("\nSERVICE COUNTS")
        print("-" * 68)

        bad_service_counts = []

        for service_name in [
            item["name"] for item in SERVICES
        ]:
            count = (
                db.query(Service)
                .filter(
                    Service.name == service_name,
                    Service.state_id.in_(target_state_ids),
                )
                .count()
                if target_state_ids
                else 0
            )

            status = "PASS" if count == len(target_state_ids) else "FAIL"

            print(
                f"{service_name:<48} {count:>3}  {status}"
            )

            if count != len(target_state_ids):
                bad_service_counts.append(
                    (service_name, count)
                )

        print("\n" + "=" * 68)

        if missing_states:
            print("❌ FAIL — missing states/UTs in database.")

        if missing_urls:
            print("❌ FAIL — records without official URLs:")
            for state, service in missing_urls:
                print(f"   {state} -> {service}")

        if bad_state_counts:
            print("❌ FAIL — one or more states/UTs do not have 22 records.")

        if bad_service_counts:
            print("❌ FAIL — one or more services do not exist for every state/UT.")

        if (
            not missing_states
            and not missing_urls
            and not bad_state_counts
            and not bad_service_counts
            and actual_target_count == EXPECTED_RECORD_COUNT
            and total_service_rows == EXPECTED_RECORD_COUNT
            and records_without_url == 0
        ):
            print("✅ PASS — all 792 state/service records are actionable.")
        else:
            print("⚠️ AUDIT INCOMPLETE — see failures above.")

        print("=" * 68 + "\n")

    except Exception as error:
        db.rollback()
        print("\n❌ ERROR WHILE SEEDING SERVICES")
        print(type(error).__name__, ":", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_services()
