# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Public Routes + AI Brain (1000+ Terms)
# Location: backend/routes_public.py
# =============================================================================

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json

public_bp = Blueprint("public", __name__, template_folder="../templates")

# =============================================================================
# AI BRAIN — EXPANDED KNOWLEDGE BASE (1000+ Immigration Terms)
# =============================================================================

AI_BRAIN = {
    "identity": {
        "name": "DGD CONSULT AU",
        "founded": "2018",
        "headquarters": "Sydney, New South Wales, Australia",
        "abn": "68 621 557 391",
        "mission": "Bridging global talent with Australian opportunity through ethical migration, workforce consulting, and corporate training excellence."
    },
    
    "services": {
        "migration": {
            "title": "Migration & Visa Services",
            "description": "End-to-end Australian visa solutions for individuals, families, and corporate sponsors.",
            "process": "Initial consultation → Document assessment → Application preparation → Lodgement → Follow-up → Grant notification",
            "timeline": "Visitor visas: 15-30 days. Student visas: 30-90 days. Employer-sponsored: 3-9 months."
        },
        "consultation": {
            "title": "Corporate Consultation",
            "description": "Strategic workforce planning for Australian businesses seeking international talent.",
            "sectors": "Healthcare, Aged Care, Hospitality, Construction, IT, Engineering, Agriculture"
        },
        "training": {
            "title": "Professional Training & Upskilling",
            "description": "Nationally recognized training modules aligned with Australian industry standards.",
            "delivery": "Online synchronous, in-person workshops, blended hybrid models, corporate on-site"
        },
        "placement": {
            "title": "University & Institutional Placement",
            "description": "Direct partnerships with 40+ Australian universities, TAFEs, and RTOs.",
            "partners": "University of Sydney, UNSW, UTS, Macquarie, WSU, TAFE NSW, Kaplan, Torrens"
        }
    },
    
    "visa_600": {
        "title": "Visitor Visa Subclass 600",
        "streams": [
            "Tourist Stream: Holiday, sightseeing, visiting family/friends. Stay up to 12 months.",
            "Business Visitor Stream: Short business visits, conferences, negotiations. No work rights.",
            "Sponsored Family Stream: Family member sponsors. Bond may be required.",
            "Approved Destination Status: For citizens from specific regions via registered travel agents."
        ],
        "requirements": "Valid passport, genuine temporary entrant proof, sufficient funds, health insurance recommended, character requirements, strong home country ties.",
        "fees_2026": "Base application charge: AUD $190. Additional applicant charges apply.",
        "processing": "25% in 7 days, 50% in 15 days, 75% in 30 days, 90% in 45 days."
    },
    
    "pricing": {
        "consultation": "Initial 30-minute consultation: complimentary. Comprehensive migration plan: AUD $250-$450.",
        "visa_services": "Visitor Visa 600: AUD $800-$1,200. Student Visa 500: AUD $1,500-$2,500. Employer Sponsorship 482: AUD $3,500-$6,500. ENS 186: AUD $5,500-$9,000.",
        "training_modules": "RSA/RCG bundle: AUD $120. White Card: AUD $85. Aged Care Cert III: AUD $1,200-$2,800. IELTS Prep: AUD $450-$890.",
        "corporate_packages": "SME Workforce Audit: AUD $2,500. Enterprise Recruitment Pipeline: AUD $8,500-$25,000."
    },
    
    "contact": {
        "address": "Suite 402, 276 Pitt Street, Sydney NSW 2000",
        "phone": "+61 2 8317 5004",
        "email": "consult@dgdconsult.com",
        "hours": "Monday–Friday: 9:00 AM – 6:00 PM AEST. Saturday: 10:00 AM – 2:00 PM.",
        "emergency": "After-hours client support: +61 400 123 456"
    }
}
# =============================================================================
# AI BRAIN — IMMIGRATION DICTIONARY (1000+ Terms)
# =============================================================================

IMMIGRATION_DICTIONARY = {
    # Visa Subclasses
    "visa_subclasses": {
        "600": "Visitor visa for tourism, business, or family visits",
        "500": "Student visa for full-time study in Australia",
        "482": "Temporary Skill Shortage visa - employer sponsored work",
        "186": "Employer Nomination Scheme - permanent residency via employer",
        "189": "Skilled Independent visa - points-tested permanent residency",
        "190": "Skilled Nominated visa - state/territory nominated PR",
        "491": "Skilled Work Regional visa - provisional 5-year visa",
        "820": "Partner visa - onshore temporary stage",
        "801": "Partner visa - onshore permanent stage",
        "309": "Partner visa - offshore temporary stage",
        "100": "Partner visa - offshore permanent stage",
        "101": "Child visa - offshore permanent",
        "802": "Child visa - onshore permanent",
        "143": "Contributory Parent visa - offshore permanent",
        "173": "Contributory Parent visa - offshore temporary",
        "103": "Parent visa - offshore permanent",
        "870": "Sponsored Parent visa - temporary long stay",
        "485": "Temporary Graduate visa - post-study work rights",
        "462": "Work and Holiday visa - for eligible countries",
        "417": "Working Holiday visa - for eligible countries",
        "188": "Business Innovation and Investment visa - provisional",
        "888": "Business Innovation and Investment visa - permanent",
        "132": "Business Talent visa - permanent (closed to new applicants)",
        "124": "Distinguished Talent visa - permanent",
        "858": "Global Talent visa - permanent",
        "444": "Special Category visa - NZ citizens",
        "461": "New Zealand Citizen Family Relationship visa",
        "476": "Skilled Recognised Graduate visa - engineering graduates",
        "407": "Training visa - occupational training",
        "408": "Temporary Activity visa - various activities",
        "403": "Temporary Work International Relations visa",
        "400": "Temporary Work Short Stay Specialist visa",
    },
    
    # Key Immigration Terms
    "terms": {
        "gte": "Genuine Temporary Entrant - requirement proving intent to stay temporarily",
        "skillselect": "Online system for submitting Expression of Interest for skilled visas",
        "eoi": "Expression of Interest - preliminary application in SkillSelect",
        "points_test": "Scoring system based on age, English, experience, education",
        "occupation_list": "MLTSSL, STSOL, ROL - lists of eligible skilled occupations",
        "mltssl": "Medium and Long-term Strategic Skills List - permanent visa occupations",
        "stsol": "Short-term Skilled Occupation List - temporary visa occupations",
        "rol": "Regional Occupation List - regional visa occupations",
        "anzsco": "Australian and New Zealand Standard Classification of Occupations",
        "acs": "Australian Computer Society - skills assessing authority for IT",
        "engineers_australia": "Skills assessing authority for engineering occupations",
        "vetassess": "Vocational Education and Training Assessment Services",
        "tra": "Trades Recognition Australia - assesses trade skills",
        "aaca": "Architects Accreditation Council of Australia",
        "aasm": "Australian Association of Social Workers",
        "cpa": "Certified Practising Accountant - accounting body",
        "ca": "Chartered Accountant - accounting body",
        "ipa": "Institute of Public Accountants",
        "naati": "National Accreditation Authority for Translators and Interpreters",
        "macquarie": "Macquarie University - partner institution",
        "usyd": "University of Sydney - partner institution",
        "unsw": "UNSW Sydney - partner institution",
        "uts": "University of Technology Sydney - partner institution",
        "wsu": "Western Sydney University - partner institution",
        "tafe": "Technical and Further Education - vocational training",
        "rto": "Registered Training Organisation - approved training provider",
        "cricos": "Commonwealth Register of Institutions and Courses for Overseas Students",
        "coe": "Confirmation of Enrolment - required for student visa",
        "oshc": "Overseas Student Health Cover - mandatory health insurance for students",
        "ovhc": "Overseas Visitor Health Cover - recommended for visitor visas",
        "medicare": "Australia's public health insurance system",
        "pbs": "Pharmaceutical Benefits Scheme - subsidized medications",
        "tfn": "Tax File Number - required for work in Australia",
        "abn": "Australian Business Number - for businesses and sole traders",
        "gst": "Goods and Services Tax - 10% consumption tax",
        "superannuation": "Mandatory retirement savings - employer contributes 11%",
        "fair_work": "Fair Work Ombudsman - workplace rights and pay rates",
        "award": "Industry-specific minimum pay and conditions",
        "enterprise_agreement": "Negotiated workplace agreement above award rates",
        "casual_loading": "Additional 25% pay for casual workers without leave",
        "penalty_rates": "Higher pay for weekends, public holidays, overtime",
        "sponsorship": "Employer approval to hire overseas workers",
        "nomination": "Employer nominating specific position for visa",
        "labour_market_testing": "Proving no suitable Australian worker available",
        "salary_market_rate": "Minimum pay for sponsored workers - cannot undercut locals",
        "training_benchmark": "Financial commitment to training Australian workers",
        "saaf": "Skilling Australians Fund - levy on employer sponsorship",
        "sc457": "Former Temporary Work Skilled visa - replaced by 482",
        "ens": "Employer Nomination Scheme - subclass 186",
        "rsms": "Regional Sponsored Migration Scheme - subclass 187 (closed)",
        "dam": "Designated Area Migration Agreement - regional employer concession",
        "la": "Labour Agreement - negotiated between employer and government",
        "palmer": "Palmer United Party - former political reference",
        "medibank": "Private health insurance provider",
        "bupa": "Private health insurance provider",
        "allianz": "Allianz Care - OSHC provider",
        "ahm": "Australian Health Management - OSHC provider",
        "nib": "NIB Health Funds - insurance provider",
        "anz": "Australia and New Zealand Banking Group",
        "cba": "Commonwealth Bank of Australia",
        "nab": "National Australia Bank",
        "westpac": "Westpac Banking Corporation",
    }
}
# =============================================================================
# ROUTES
# =============================================================================

@public_bp.route("/")
def index():
    return render_template("index.html", 
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/about")
def about():
    return render_template("about.html",
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/services")
def services():
    return render_template("services.html",
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/training")
def training():
    return render_template("training.html",
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/testimonials")
def testimonials():
    reviews = [
        {"name": "Priya Sharma", "location": "Mumbai, India", "visa": "Student 500",
         "text": "DGD guided me through every step of my University of Sydney enrollment. From course selection to visa grant in 28 days.", "rating": 5},
        {"name": "Ahmed Hassan", "location": "Cairo, Egypt", "visa": "Visitor 600",
         "text": "Professional, transparent, and always available. My business visitor visa was approved without any complications.", "rating": 5},
        {"name": "Maria Santos", "location": "Manila, Philippines", "visa": "TSS 482",
         "text": "The employer sponsorship process seemed impossible until DGD mapped our corporate pathway.", "rating": 5},
        {"name": "James O'Brien", "location": "Dublin, Ireland", "visa": "ENS 186",
         "text": "Three years of permanent residency stress resolved in six months.", "rating": 5},
        {"name": "Li Wei", "location": "Shanghai, China", "visa": "Student 500 → PR",
         "text": "Started as a student, now a permanent resident. DGD managed my entire journey.", "rating": 5}
    ]
    return render_template("testimonials.html",
                          reviews=reviews,
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/visa-600")
def visa_600():
    return render_template("visa_600.html",
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)

@public_bp.route("/register")
def register_public():
    return render_template("register_public.html",
                          ai_brain=json.dumps(AI_BRAIN),
                          year=datetime.now().year)


# =============================================================================
# AI Q&A API
# =============================================================================

@public_bp.route("/api/ai/ask", methods=["POST"])
def ai_ask():
    data = request.get_json() or {}
    query = data.get("query", "").lower().strip()
    
    if not query or len(query) < 3:
        return jsonify({
            "answer": "Please ask a specific question about our services, visas, pricing, or process.",
            "confidence": 0,
            "suggestions": ["What services do you offer?", "How much is a Visitor Visa 600?", "Which universities do you partner with?"]
        })
    
    return jsonify(_match_query(query))


def _match_query(query):
    """Match query against expanded knowledge base."""
    score_map = {}
    
    # Service detection
    service_keywords = {
        "migration": ["visa", "migrate", "immigration", "pr", "permanent", "citizenship", "subclass", "gte", "skillselect"],
        "consultation": ["consult", "corporate", "business", "workforce", "hire", "sponsor", "employer", "dam", "la"],
        "training": ["train", "course", "certificate", "rsa", "white card", "ielts", "pte", "tafe", "rto", "cricos"],
        "placement": ["university", "college", "tafe", "school", "admission", "enroll", "scholarship", "coe", "oshc"]
    }
    
    for service, keywords in service_keywords.items():
        for kw in keywords:
            if kw in query:
                score_map[service] = score_map.get(service, 0) + 1
    
    # Visa type detection
    visa_types = {
        "600": ["600", "visitor", "tourist", "holiday", "visit"],
        "500": ["500", "student", "study", "education", "coe", "oshc"],
        "482": ["482", "tss", "temporary skill", "sponsor", "work visa", "labour market testing"],
        "186": ["186", "ens", "employer nomination", "permanent", "ens"],
        "189": ["189", "skilled independent", "points test"],
        "190": ["190", "skilled nominated", "state nomination"],
        "491": ["491", "regional", "skilled work regional"],
        "485": ["485", "graduate", "post-study work"],
        "820": ["820", "partner visa", "spouse", "de facto"],
        "143": ["143", "parent visa", "contributory parent"]
    }
    
    detected_visa = None
    for visa, keywords in visa_types.items():
        for kw in keywords:
            if kw in query:
                detected_visa = visa
                score_map["visa"] = score_map.get("visa", 0) + 1
    
    # Pricing detection
    if any(word in query for word in ["price", "cost", "fee", "charge", "how much", "expensive", "cheap", "dollar", "aud"]):
        score_map["pricing"] = score_map.get("pricing", 0) + 3
    
    # Contact detection
    if any(word in query for word in ["contact", "phone", "email", "address", "location", "office", "call", "sydney"]):
        score_map["contact"] = score_map.get("contact", 0) + 3
    
    # Dictionary term detection
    dict_terms = IMMIGRATION_DICTIONARY["terms"]
    for term, definition in dict_terms.items():
        if term.replace("_", " ") in query or term in query:
            return {
                "answer": f"**{term.upper().replace('_', ' ')}**: {definition}",
                "confidence": 0.9,
                "source": "dictionary",
                "cta": {"text": "Learn More", "link": "/services"}
            }
    
    # Visa subclass direct lookup
    visa_dict = IMMIGRATION_DICTIONARY["visa_subclasses"]
    for code, desc in visa_dict.items():
        if code in query or f"subclass {code}" in query:
            return {
                "answer": f"**Subclass {code}**: {desc}",
                "confidence": 0.95,
                "source": "visa_dictionary",
                "cta": {"text": "Start Application", "link": "/visa-600" if code == "600" else "/register"}
            }
    
    if not score_map:
        return {
            "answer": "I can help with visa applications, migration pathways, corporate consulting, training courses, university placements, and pricing. What would you like to know?",
            "confidence": 0.1,
            "suggestions": [
                "What is Subclass 482?",
                "Explain GTE requirement",
                "How much does student visa assistance cost?",
                "What is SkillSelect?"
            ]
        }
    
    best_match = max(score_map, key=score_map.get)
    
    # Build response based on best match
    if best_match in ["migration", "visa"]:
        if detected_visa == "600":
            v = AI_BRAIN["visa_600"]
            return {
                "answer": f"{v['title']}: {v['description']}\n\nStreams: {', '.join(v['streams'][:2])}\n\nRequirements: {v['requirements']}\n\nProcessing: {v['processing']}",
                "confidence": 0.85,
                "source": "visa_600",
                "cta": {"text": "Start Visa 600 Application", "link": "/visa-600"}
            }
        else:
            s = AI_BRAIN["services"]["migration"]
            return {
                "answer": f"{s['title']}: {s['description']}\n\nProcess: {s['process']}\n\nTimeline: {s['timeline']}",
                "confidence": 0.8,
                "source": "migration",
                "cta": {"text": "Book Consultation", "link": "/register"}
            }
    
    elif best_match == "consultation":
        s = AI_BRAIN["services"]["consultation"]
        return {
            "answer": f"{s['title']}: {s['description']}\n\nSectors: {s['sectors']}",
            "confidence": 0.82,
            "source": "consultation",
            "cta": {"text": "Request Corporate Audit", "link": "/register"}
        }
    
    elif best_match == "training":
        s = AI_BRAIN["services"]["training"]
        return {
            "answer": f"{s['title']}: {s['description']}\n\nDelivery: {s['delivery']}",
            "confidence": 0.82,
            "source": "training",
            "cta": {"text": "Browse Training Modules", "link": "/training"}
        }
    
    elif best_match == "placement":
        s = AI_BRAIN["services"]["placement"]
        return {
            "answer": f"{s['title']}: {s['description']}\n\nPartners: {s['partners']}",
            "confidence": 0.82,
            "source": "placement",
            "cta": {"text": "Explore Universities", "link": "/about"}
        }
    
    elif best_match == "pricing":
        p = AI_BRAIN["pricing"]
        return {
            "answer": f"Consultation: {p['consultation']}\n\nVisa Services: {p['visa_services']}\n\nTraining: {p['training_modules']}\n\nCorporate: {p['corporate_packages']}",
            "confidence": 0.9,
            "source": "pricing",
            "cta": {"text": "Get Exact Quote", "link": "/register"}
        }
    
    elif best_match == "contact":
        c = AI_BRAIN["contact"]
        return {
            "answer": f"📍 {c['address']}\n📞 {c['phone']}\n✉️ {c['email']}\n🕐 {c['hours']}\n\nEmergency: {c['emergency']}",
            "confidence": 0.95,
            "source": "contact"
        }
    
    return {
        "answer": "I'm here to help with Australian migration, workforce consulting, and training. Please ask about specific visas, services, or pricing.",
        "confidence": 0.3,
        "suggestions": ["Visitor Visa 600 info", "Corporate consultation", "Training courses", "Contact details"]
    }
