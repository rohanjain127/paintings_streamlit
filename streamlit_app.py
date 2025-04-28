# streamlit_app.py — launch with: streamlit run streamlit_app.py

import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# ── DB credentials from secrets ──
DB = dict(
    host     = st.secrets["DB_HOST"],
    dbname   = st.secrets["DB_NAME"],
    user     = st.secrets["DB_USER"],
    password = st.secrets["DB_PASSWORD"],
    port     = st.secrets.get("DB_PORT", 5432),
)

# ── Query Helper ──
@st.cache_data(show_spinner=False)
def run_query(sql_text, params=None):
    with psycopg2.connect(**DB) as conn:
        return pd.read_sql_query(sql_text, conn, params=params)

# ── Add background image (Starry Night) ──
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://upload.wikimedia.org/wikipedia/commons/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    .block-container {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 2rem;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ── UI Header ──
st.title("🎨 Paintings Database Explorer")

# ── Sidebar navigation ──
page_options = ["SQL Playground"]

# Add table names dynamically
tables = run_query("""
    SELECT relname AS table_name, n_live_tup AS row_count
    FROM pg_stat_user_tables
    ORDER BY table_name
""")
for _, row in tables.iterrows():
    page_options.append(f"{row['table_name']} ({row['row_count']} rows)")

# Add custom dashboards
page_options += [
    "Top Nationalities",
    "Price Distribution",
    "Top Museums by Artworks"
]

page = st.sidebar.selectbox("Select a page", page_options)

# ── Logic per page ──

# 1 ── SQL Playground
if page == "SQL Playground":
    st.subheader("🛠 Ad-hoc SQL Playground (SELECT-only)")
    default = "SELECT * FROM artist LIMIT 10;"
    user_sql = st.text_area("Enter a SELECT statement:", default, height=160)

    if st.button("Run query"):
        sql_lower = user_sql.strip().lower()
        if not sql_lower.startswith("select"):
            st.warning("Only SELECT statements are allowed.")
        else:
            try:
                df = run_query(user_sql)
                if df.empty:
                    st.info("Query ran, but returned zero rows.")
                else:
                    st.success(f"Returned {len(df)} rows.")
                    st.dataframe(df)
                    
                    nums = df.select_dtypes("number")
                    if nums.shape[1] >= 2:
                        x, y = nums.columns[:2]
                        st.plotly_chart(
                            px.scatter(df, x=x, y=y, title=f"{x} vs {y}"),
                            use_container_width=True,
                        )
            except Exception as e:
                st.error(f"Query failed: {e}")

# 2 ── Table Viewer
elif "(" in page and ")" in page:
    table_name = page.split(" (")[0]
    st.subheader(f"📄 Table: `{table_name}`")
    df = run_query(f"SELECT * FROM {table_name}")
    st.dataframe(df)
    st.success(f"Total rows: {len(df)}")

# 3 ── Top Nationalities
elif page == "Top Nationalities":
    st.subheader("🌍 Top 10 Nationalities by Artworks")
    df = run_query("""
        SELECT nationality, COUNT(*) AS count
        FROM artist
        WHERE nationality IS NOT NULL
        GROUP BY nationality
        ORDER BY count DESC
        LIMIT 10
    """)
    fig = px.bar(df, x="nationality", y="count", title="Top 10 Nationalities")
    st.plotly_chart(fig, use_container_width=True)

# 4 ── Price Distribution
elif page == "Price Distribution":
    st.subheader("💵 Sale Price Distribution")
    df = run_query("""
        SELECT sale_price
        FROM product_size
        WHERE sale_price IS NOT NULL
    """)
    fig = px.histogram(df, x="sale_price", nbins=30, title="Sale Price Distribution")
    st.plotly_chart(fig, use_container_width=True)

# 5 ── Top Museums by Artworks
elif page == "Top Museums by Artworks":
    st.subheader("🏛 Top Museums by Artwork Count")
    df = run_query("""
        SELECT m.name, COUNT(*) AS count
        FROM museum m
        JOIN work w ON m.museum_id = w.museum_id
        GROUP BY m.name
        ORDER BY count DESC
        LIMIT 10
    """)
    fig = px.bar(df, x="count", y="name", orientation="h", title="Top Museums")
    st.plotly_chart(fig, use_container_width=True)
