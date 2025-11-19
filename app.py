import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# ==================== SUPABASE DATABASE SETUP ====================
def init_supabase_database():
    """Initialize Supabase database tables"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'practitioner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create admin user if not exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            hashed_pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            cur.execute("""
                INSERT INTO users (username, email, name, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', 'admin@pinnalogy.com', 'Admin User', hashed_pw, 'admin'))
            st.success("✅ Admin user created!")
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Database setup failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        st.success("🎉 SUPABASE CONNECTION SUCCESSFUL!")
        
        # Initialize database
        if init_supabase_database():
            st.success("✅ Database tables initialized!")
        
        # Show database info
        cur = conn.cursor()
        cur.execute("SELECT version();")
        st.write(f"**Database:** {cur.fetchone()[0]}")
        
        # Show tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        if tables:
            st.write("**Tables Created:**")
            for table in tables:
                st.write(f"✅ {table[0]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        return False

# ===== AUTHENTICATION =====
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(username, password):
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute(
            "SELECT username, name, password_hash, role FROM users WHERE username = %s",
            (username.lower(),)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and verify_password(password, result[2]):
            return result[1], True, result[0]
        else:
            return None, False, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None, False, None

# ===== APP CONFIG =====
st.set_page_config(
    page_title="Pinnalogy AI - Supabase",
    page_icon="👂",
    layout="wide"
)

# ===== MAIN APP =====
def main():
    st.title("👂 Pinnalogy AI Professional")
    st.markdown("## Supabase Database System")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Tools")
        if st.button("Test Supabase Connection"):
            test_supabase_connection()
        
        if st.session_state.authenticated:
            if st.button("🚪 Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Main content
    if not st.session_state.authenticated:
        show_login()
    else:
        show_dashboard()

def show_login():
    st.header("🔐 Login to Pinnalogy AI")
    
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")
        
        if st.form_submit_button("Login"):
            name, auth_status, username = authenticate_user(username, password)
            if auth_status:
                st.session_state.authenticated = True
                st.session_state.name = name
                st.session_state.username = username
                st.success(f"Welcome {name}!")
                st.rerun()
            else:
                st.error("Login failed!")
    
    st.info("**Demo:** admin / admin123")

def show_dashboard():
    st.success(f"🎉 Welcome, {st.session_state.name}!")
    st.balloons()
    
    st.header("🚀 Supabase Migration Complete!")
    st.write("Your database is now running on Supabase Cloud!")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Database", "Supabase")
    with col2:
        st.metric("Status", "Active")
    with col3:
        st.metric("Storage", "500MB Free")
    
    st.markdown("---")
    st.subheader("Next Steps:")
    st.write("1. ✅ Add patient management system")
    st.write("2. ✅ Build ear analysis with image upload")
    st.write("3. ✅ Implement AI training features")
    st.write("4. 🚀 Deploy production app")

if __name__ == "__main__":
    main()
