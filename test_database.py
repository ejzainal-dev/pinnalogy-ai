import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="Database Test - Pinnalogy AI",
    page_icon="🔧",
    layout="wide"
)

# Load environment variables
load_dotenv()

st.title("🔧 Database Connection Test")
st.markdown("### Test PostgreSQL Database Connection")

# Function to test database connection
def test_database_connection():
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            st.error("❌ DATABASE_URL not found in environment variables")
            return False
        
        # Display safe connection info (hide password)
        safe_url = database_url
        if '@' in database_url:
            parts = database_url.split('@')
            user_part = parts[0]
            if ':' in user_part:
                user_parts = user_part.split(':')
                if len(user_parts) >= 3:
                    # Hide password
                    user_parts[2] = '***'
                    safe_user_part = ':'.join(user_parts)
                    safe_url = safe_user_part + '@' + parts[1]
        
        st.write(f"**Connecting to:** `{safe_url}`")
        
        # Test connection
        conn = psycopg2.connect(database_url)
        st.success("✅ PostgreSQL Connection SUCCESSFUL!")
        
        # Get database info
        cur = conn.cursor()
        
        # Database version
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        st.write(f"**Database Version:** {db_version[0]}")
        
        # Current database name
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()
        st.write(f"**Database Name:** {db_name[0]}")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        if tables:
            st.write("**📊 Tables in database:**")
            for table in tables:
                st.write(f"✅ {table[0]}")
                
            # Show row counts for each table
            st.write("**📈 Table Row Counts:**")
            for table in tables:
                table_name = table[0]
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cur.fetchone()[0]
                    st.write(f"- {table_name}: {count} rows")
                except:
                    st.write(f"- {table_name}: Unable to count")
        else:
            st.warning("📭 No tables found in database")
        
        # Check if users table exists and show users
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'users'
        """)
        users_table_exists = cur.fetchone()
        
        if users_table_exists:
            try:
                cur.execute("SELECT username, email, role, created_at FROM users ORDER BY created_at")
                users = cur.fetchall()
                if users:
                    st.write("**👥 Users in database:**")
                    for user in users:
                        st.write(f"- **{user[0]}** ({user[1]}) - *{user[2]}* - {user[3]}")
                else:
                    st.info("👤 No users found in users table")
            except Exception as e:
                st.warning(f"Could not read users table: {e}")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        st.error(f"❌ Connection Failed: {e}")
        st.info("""
        **Common Solutions:**
        1. Check if database exists in cPanel
        2. Verify username and password
        3. Check hostname and port
        4. Ensure database service is running
        """)
        return False
    except Exception as e:
        st.error(f"❌ Unexpected Error: {e}")
        return False

# Function to initialize database (create tables)
def initialize_database():
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
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
        
        # Create other tables
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                patient_code VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                age INTEGER,
                gender VARCHAR(10),
                contact_info TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                patient_id INTEGER REFERENCES patients(id),
                session_code VARCHAR(50) UNIQUE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for sql in tables_sql:
            cur.execute(sql)
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to initialize database: {e}")
        return False

# Main interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("Connection Test")
    if st.button("🔗 Test Database Connection", type="primary"):
        test_database_connection()

with col2:
    st.subheader("Database Setup")
    if st.button("🔄 Initialize Database Tables"):
        if initialize_database():
            st.info("Please run connection test again to verify")

st.markdown("---")
st.subheader("Troubleshooting")

with st.expander("🔧 Advanced Tools"):
    st.write("**Environment Variables Check:**")
    st.write(f"DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")
    
    if st.button("Show Raw Connection String (Hidden Password)"):
        db_url = os.getenv('DATABASE_URL')
        if db_url and '@' in db_url:
            parts = db_url.split('@')
            user_part = parts[0]
            # Hide password but show other parts
            if ':' in user_part:
                user_parts = user_part.split(':')
                if len(user_parts) >= 3:
                    user_parts[2] = '***'  # Hide password
                    safe_user_part = ':'.join(user_parts)
                    st.code(safe_user_part + '@' + parts[1])
        else:
            st.code(db_url)

st.markdown("---")
st.info("""
**Note:** This is a testing page. After confirming database connection is working, 
you can remove this page or keep it for future debugging.
""")
