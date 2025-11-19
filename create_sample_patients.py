import psycopg2
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

def create_sample_patients():
    """Create 30 sample patients with ear data"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        print("✅ Connected to database successfully!")
        
        # Sample data
        malay_names_male = [
            "Ahmad bin Abdullah", "Muhammad bin Ismail", "Ali bin Hassan", 
            "Salleh bin Mahmud", "Razak bin Omar", "Zulkifli bin Ahmad",
            "Hafiz bin Mohd", "Faizal bin Yusof", "Amir bin Rahman",
            "Syed bin Ibrahim", "Azman bin Sulaiman", "Kamarul bin Zaini",
            "Shahrul bin Nizam", "Firdaus bin Jamal", "Hakim bin Rosli"
        ]
        
        malay_names_female = [
            "Aishah binti Mohd", "Siti binti Hassan", "Nor binti Ahmad",
            "Fatimah binti Omar", "Zainab binti Ismail", "Mariam binti Abdullah",
            "Sarah binti Rahman", "Nurul binti Yusof", "Haslinda binti Sulaiman",
            "Rosnah binti Ibrahim", "Zuraidah binti Mahmud", "Anisah binti Jamal",
            "Farah binti Rosli", "Yusnita binti Zaini", "Suzana binti Nizam"
        ]
        
        chinese_names = [
            "Tan Wei Ming", "Lim Chen Long", "Wong Mei Ling", "Lee Kok Wai",
            "Chan Siew Lin", "Ng Poh Sim", "Teh Kim Choo", "Ooi Bee Eng"
        ]
        
        indian_names = [
            "Raj Kumar", "Priya Devi", "Suresh Menon", "Lakshmi Ammal",
            "Vikram Singh", "Anita Sharma", "Gopal Krishnan", "Shanti Bai"
        ]
        
        all_names = malay_names_male + malay_names_female + chinese_names + indian_names
        
        clinics = [
            "Klinik Kesihatan Kuala Lumpur", "Hospital Umum Selangor", 
            "Pusat Perubatan Ara Damansara", "Klinik Specialist Ear Care",
            "Hospital Pantai Bangi", "Pusat Rawatan Harapan", 
            "Klinik MediPlus", "Hospital Columbia Asia"
        ]
        
        medical_conditions = [
            "Hypertension", "Diabetes Type 2", "Asthma", "Migraine",
            "Arthritis", "High Cholesterol", "Gastric", "Allergic Rhinitis",
            "None", "Back Pain", "Insomnia", "Anxiety"
        ]
        
        medications = [
            "Metformin 500mg", "Ventolin inhaler", "Amlodipine 5mg",
            "Simvastatin 20mg", "Omeprazole 20mg", "Paracetamol 500mg",
            "Cetirizine 10mg", "None", "Vitamin D 1000IU", "Iron supplement"
        ]
        
        # Ear analysis data templates
        ear_analysis_templates = {
            "normal": {
                "detected_zones": ["earlobe", "helix_rim", "concha"],
                "color_analysis": {
                    "normal": "Healthy skin tone - 95% normal"
                },
                "texture_analysis": {
                    "smoothness": "Normal skin texture"
                },
                "structural_features": ["Well-defined ear structure"],
                "potential_concerns": [],
                "recommended_checks": ["Routine annual checkup"],
                "lifestyle_suggestions": ["Maintain current healthy lifestyle"],
                "confidence_level": "high"
            },
            "mild_inflammation": {
                "detected_zones": ["earlobe", "helix_rim", "tragus", "concha"],
                "color_analysis": {
                    "redness": "15% - Mild inflammation detected",
                    "normal": "85% - Healthy areas"
                },
                "texture_analysis": {
                    "smoothness": "Slight irritation detected"
                },
                "structural_features": ["Mild swelling in outer regions"],
                "potential_concerns": ["Possible mild infection", "Allergic reaction"],
                "recommended_checks": ["Inflammation markers", "Allergy test"],
                "lifestyle_suggestions": ["Avoid potential allergens", "Keep ear dry"],
                "confidence_level": "moderate"
            },
            "circulatory_issues": {
                "detected_zones": ["earlobe", "anti_helix", "concha", "scapha"],
                "color_analysis": {
                    "pallor": "25% - Reduced blood flow",
                    "normal": "75% - Adequate circulation"
                },
                "texture_analysis": {
                    "smoothness": "Poor circulation indicators"
                },
                "structural_features": ["Pale vascular patterns"],
                "potential_concerns": ["Circulatory issues", "Anemia possibility"],
                "recommended_checks": ["Complete blood count", "Blood pressure monitoring"],
                "lifestyle_suggestions": ["Improve cardiovascular exercise", "Iron-rich diet"],
                "confidence_level": "moderate"
            },
            "stress_indications": {
                "detected_zones": ["helix_rim", "anti_helix", "tragus"],
                "color_analysis": {
                    "redness": "20% - Stress-related inflammation",
                    "normal": "80% - Stable areas"
                },
                "texture_analysis": {
                    "roughness": "Stress pattern indicators"
                },
                "structural_features": ["Tension patterns in cartilage"],
                "potential_concerns": ["Chronic stress", "Nervous tension"],
                "recommended_checks": ["Stress hormone levels", "Blood pressure"],
                "lifestyle_suggestions": ["Stress management techniques", "Adequate sleep", "Relaxation exercises"],
                "confidence_level": "moderate"
            }
        }
        
        # Clear existing sample data (optional)
        cur.execute("DELETE FROM ear_analyses WHERE patient_id IN (SELECT id FROM patients WHERE patient_code LIKE 'SMP%')")
        cur.execute("DELETE FROM patients WHERE patient_code LIKE 'SMP%'")
        
        print("🗑️ Cleared previous sample data...")
        
        # Create 30 sample patients
        for i in range(1, 31):
            # Generate patient data
            patient_code = f"SMP{i:03d}"
            full_name = random.choice(all_names)
            age = random.randint(18, 75)
            gender = random.choice(["Male", "Female"])
            
            # Generate IC number based on age
            birth_year = 2024 - age
            ic_number = f"{birth_year % 100:02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999):04d}"
            
            phone = f"+601{random.randint(2,9)}{random.randint(1000000, 9999999):07d}"
            email = f"patient{patient_code.lower()}@example.com"
            
            blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            blood_type = random.choice(blood_types)
            
            emergency_contact = f"+601{random.randint(2,9)}{random.randint(1000000, 9999999):07d}"
            
            # Medical history
            conditions = random.sample(medical_conditions, random.randint(1, 3))
            current_meds = random.sample(medications, random.randint(1, 2))
            
            medical_history = f"Conditions: {', '.join(conditions)}. Medications: {', '.join(current_meds)}."
            
            notes = f"Registered at {random.choice(clinics)}. {random.choice(['Regular checkup', 'Follow-up visit', 'New patient assessment'])}."
            
            # Insert patient
            cur.execute("""
                INSERT INTO patients (user_id, patient_code, full_name, age, gender, contact_info, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (1, patient_code, full_name, age, gender, 
                  f"Phone: {phone}, Email: {email}, Emergency: {emergency_contact}, Blood Type: {blood_type}",
                  medical_history + " " + notes))
            
            patient_id = cur.fetchone()[0]
            
            # Create ear analyses for this patient (both ears)
            analysis_types = list(ear_analysis_templates.keys())
            left_ear_type = random.choice(analysis_types)
            right_ear_type = random.choice(analysis_types)
            
            # Ensure at least 60% of patients have normal ears
            if i <= 18:  # 60% of 30
                left_ear_type = "normal"
                right_ear_type = "normal"
            
            # Left ear analysis
            left_analysis = ear_analysis_templates[left_ear_type].copy()
            left_analysis["ear_side"] = "left"
            left_analysis["analysis_date"] = (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            left_analysis["image_filename"] = f"left_ear_{patient_code}_{datetime.now().strftime('%Y%m%d')}.jpg"
            
            cur.execute("""
                INSERT INTO ear_analyses (patient_id, analysis_data)
                VALUES (%s, %s)
            """, (patient_id, json.dumps(left_analysis)))
            
            # Right ear analysis
            right_analysis = ear_analysis_templates[right_ear_type].copy()
            right_analysis["ear_side"] = "right"
            right_analysis["analysis_date"] = (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            right_analysis["image_filename"] = f"right_ear_{patient_code}_{datetime.now().strftime('%Y%m%d')}.jpg"
            
            cur.execute("""
                INSERT INTO ear_analyses (patient_id, analysis_data)
                VALUES (%s, %s)
            """, (patient_id, json.dumps(right_analysis)))
            
            print(f"✅ Created patient {patient_code}: {full_name}")
        
        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n🎉 Successfully created 30 sample patients!")
        print("📊 Each patient has 2 ear analyses (left and right)")
        print("👥 Patient codes: SMP001 to SMP030")
        print("\nYou can now run the main app with: streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    create_sample_patients()
