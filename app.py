import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

# ==================== PASSWORD FUNCTIONS ====================
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

# ==================== DATABASE FUNCTIONS ====================
def init_database():
    """Initialize database tables"""
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
        
        # Check if admin exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cur.fetchone()[0]
        
        # Create admin user if not exists
        if admin_exists == 0:
            hashed_password = hash_password('admin123')
            cur.execute("""
                INSERT INTO users (username, email, name, password_hash, role) 
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', 'admin@pinnalogy.com', 'Admin User', hashed_password, 'admin'))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        st.success("✅ PostgreSQL Connection SUCCESSFUL!")
        
        # Initialize database
        if init_database():
            st.success("✅ Database tables initialized!")
        
        # Get database info
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        st.write(f"**Database Version:** {db_version[0]}")
        
        # Show existing users
        cur.execute("SELECT username, email, role FROM users")
        users = cur.fetchall()
        if users:
            st.write("**Existing Users:**")
            for user in users:
                st.write(f"- {user[0]} ({user[1]}) - {user[2]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Database Connection FAILED: {e}")
        return False

# ===== CONFIGURATION =====
st.set_page_config(
    page_title="Pinnalogy AI - Professional Ear Analysis",
    page_icon="👂", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== MAIN APP =====
def main():
    st.title("👂 Pinnalogy AI Professional")
    st.markdown("## Ear Reflexology Analysis System")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    
    # Sidebar
    with st.sidebar:
        st.header("Tools")
        if st.button("🔗 Test Database Connection"):
            test_database_connection()
        
        if st.session_state.authenticated:
            st.success(f"Logged in as: {st.session_state.name}")
            if st.button("🚪 Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Authentication
    if not st.session_state.authenticated:
        show_login_interface()
    else:
        show_main_interface()

def show_login_interface():
    """Show login form"""
    st.header("🔐 Practitioner Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if username and password:
                name, auth_status, username = authenticate_user(username, password)
                if auth_status:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.name = name
                    st.success(f"Welcome {name}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter username and password")
    
    st.info("**Demo Account:** admin / admin123")

def show_main_interface():
    """Show main interface after login"""
    st.success(f"🎉 Welcome back, {st.session_state.name}!")
    st.header("🚀 Ready for Supabase Migration")
    st.write("Database connection is working! Next step: Migrate to Supabase.")
    
    # Simple dashboard
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("System Status", "Active")
    with col2:
        st.metric("Database", "Connected")
    with col3:
        st.metric("Next Step", "Supabase Setup")

if __name__ == "__main__":
    main()
