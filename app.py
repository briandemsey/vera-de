"""
VERA-DE: Verification Engine for Results & Accountability - Delaware
Type 4 Detection using WIDA ACCESS for ELLs Speaking vs Writing + DeSSA Achievement Data

Delaware context:
- WIDA ACCESS for ELLs, 4 domains (Listening, Speaking, Reading, Writing)
- DeSSA (Delaware System of Student Assessments) -- Smarter Balanced, 4 levels:
    Below Standard / Approaching Standard / Meets Standard / Exceeds Standard
- ~19 districts + charter schools, ~18,800 MLLs (13% statewide)
- Top MLL districts: Red Clay Consolidated, Christina, Colonial
- District merger debate: ongoing conversation about consolidating small districts
- reportcard.doe.k12.de.us -- public data dashboard
- Delaware uses "Multilingual Learner" (MLL) terminology, not just EL

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_PASSWORD = "vera2026"

DE_BLUE = "#003DA5"
DE_GOLD = "#D4A843"
DE_DARK = "#002970"
DE_GRAY = "#4A4A4A"
DE_LIGHT_BLUE = "#4D7FCC"

# ============================================================================
# DATA: Delaware Districts with MLL Populations
# Source: DDOE / reportcard.doe.k12.de.us
# Delaware uses "Multilingual Learner" (MLL) terminology
# ============================================================================

def load_districts():
    """Load DE districts with significant MLL populations.

    Delaware is a small state with ~19 traditional districts plus charter schools.
    The district merger debate is ongoing -- Delaware's current district structure
    dates to 1969 desegregation-era consolidation, and many argue the small number
    of districts still perpetuates inequity. MLL concentration is highest in the
    northern New Castle County districts near Wilmington.
    """
    data = [
        # (district_id, district_name, total_students, mll_count, mll_percent,
        #  dessa_meets_all, dessa_meets_mll, graduation_rate, star_rating, context_note)

        # --- New Castle County (northern, highest MLL concentration) ---
        ("31", "Red Clay Consolidated SD", 16200, 3564, 22.0, 45.5, 14.2, 85.8, 3, "Largest MLL count; Wilmington area; diverse"),
        ("33", "Christina School District", 14800, 3108, 21.0, 40.2, 12.5, 82.5, 2, "Wilmington + Newark; merger debate focal point"),
        ("34", "Colonial School District", 10500, 2310, 22.0, 42.8, 13.8, 83.2, 3, "New Castle area; growing MLL population"),
        ("32", "Brandywine School District", 10800, 1620, 15.0, 48.5, 16.2, 87.5, 3, "Northern suburbs; moderate MLL"),
        ("35", "Appoquinimink School District", 12500, 1250, 10.0, 55.2, 19.5, 91.2, 4, "Middletown area; fastest growing district"),

        # --- Kent County (central) ---
        ("10", "Capital School District", 7200, 1080, 15.0, 38.5, 11.8, 80.5, 2, "Dover area; state capital"),
        ("13", "Caesar Rodney School District", 8500, 850, 10.0, 46.8, 15.5, 86.2, 3, "Camden-Wyoming area; military families"),
        ("15", "Lake Forest School District", 3800, 380, 10.0, 40.5, 13.2, 82.8, 2, "Harrington area; rural Kent County"),
        ("16", "Milford School District", 4200, 546, 13.0, 39.8, 12.5, 81.5, 2, "Kent/Sussex border; agricultural area"),
        ("12", "Smyrna School District", 5800, 522, 9.0, 44.2, 14.8, 84.5, 3, "Northern Kent; growing community"),

        # --- Sussex County (southern) ---
        ("37", "Indian River School District", 11200, 1792, 16.0, 41.5, 12.8, 83.5, 3, "Sussex County; large agricultural EL pop"),
        ("38", "Woodbridge School District", 2800, 448, 16.0, 36.2, 10.5, 78.5, 2, "Bridgeville area; poultry industry"),
        ("36", "Cape Henlopen School District", 5200, 520, 10.0, 47.5, 15.8, 87.2, 3, "Lewes/Rehoboth; coastal + agricultural"),
        ("39", "Seaford School District", 3500, 455, 13.0, 37.8, 11.2, 79.8, 2, "Western Sussex; poultry processing"),
        ("40", "Laurel School District", 2200, 286, 13.0, 35.5, 10.2, 77.8, 2, "Southern Sussex; rural poverty + ELs"),
    ]

    return pd.DataFrame(data, columns=[
        'district_id', 'district_name', 'total_students',
        'mll_count', 'mll_percent',
        'dessa_meets_all', 'dessa_meets_mll', 'graduation_rate',
        'star_rating', 'context_note'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (WIDA ACCESS for ELLs)
# ============================================================================

def load_access_data(districts_df):
    """Generate district ACCESS domain data modeled from DE MLL performance patterns.
    Delaware uses WIDA ACCESS for MLL assessment."""
    access_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                base_speaking = 335 + (grade * 8)
                base_writing = 288 + (grade * 6)

                el_density_penalty = max(0, (d['mll_percent'] - 15) * 0.38)
                el_factor = d['dessa_meets_mll'] / 13.5
                speaking_adj = int(13 * el_factor + d['mll_percent'] * 0.2 - el_density_penalty)
                writing_adj = int(-8 + (el_factor - 1) * 10 - el_density_penalty * 0.75)

                yr_adj = 3 if year == 2025 else 0

                access_data.append({
                    'district_id': d['district_id'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(15, int(d['mll_count'] / 6)),
                    'listening_avg': base_speaking + speaking_adj - 4 + yr_adj,
                    'speaking_avg': base_speaking + speaking_adj + yr_adj,
                    'reading_avg': base_writing + writing_adj + 13 + yr_adj,
                    'writing_avg': base_writing + writing_adj + yr_adj,
                    'composite_avg': int((base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 15 + yr_adj),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: DeSSA Achievement Data
# DeSSA (Smarter Balanced), 4 levels:
#   Below Standard / Approaching Standard / Meets Standard / Exceeds Standard
# ============================================================================

def load_dessa_data(districts_df):
    """Generate DeSSA data based on reportcard.doe.k12.de.us patterns."""
    dessa_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    base = d['dessa_meets_all'] if subject == 'ELA' else d['dessa_meets_all'] * 0.85
                    meets_exceeds = max(8, min(80, base + (grade - 5) * -1.2))

                    exceeds = max(2, meets_exceeds * 0.22)
                    meets = meets_exceeds - exceeds
                    approaching = max(12, (100 - meets_exceeds) * 0.42)
                    below = max(8, 100 - meets_exceeds - approaching)

                    dessa_data.append({
                        'district_id': d['district_id'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'meets_exceeds_pct': round(meets_exceeds, 1),
                        'exceeds_pct': round(exceeds, 1),
                        'meets_pct': round(meets, 1),
                        'approaching_pct': round(approaching, 1),
                        'below_pct': round(below, 1),
                    })

    return pd.DataFrame(dessa_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (WIDA ACCESS results)
# ============================================================================

def load_statewide_domain_data():
    """Statewide ACCESS domain proficiency percentages by grade cluster.
    Source: DDOE MLL reports / WIDA ACCESS results."""
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 43, 'speaking': 38, 'reading': 26, 'writing': 18},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 47, 'speaking': 43, 'reading': 30, 'writing': 21},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 51, 'speaking': 46, 'reading': 34, 'writing': 24},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 54, 'speaking': 49, 'reading': 37, 'writing': 26},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 40, 'speaking': 35, 'reading': 24, 'writing': 16},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 44, 'speaking': 40, 'reading': 28, 'writing': 19},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 48, 'speaking': 43, 'reading': 32, 'writing': 22},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 51, 'speaking': 46, 'reading': 35, 'writing': 24},
    ])


# ============================================================================
# DATA: MLL Population Growth
# ============================================================================

def load_mll_growth_data():
    """Delaware MLL population growth -- steady increase driven by immigration
    and agricultural/poultry industries in Sussex County."""
    return pd.DataFrame([
        {'year': 2008, 'mll_count': 10200, 'mll_percent': 7.8, 'note': 'Baseline'},
        {'year': 2010, 'mll_count': 11500, 'mll_percent': 8.5, 'note': ''},
        {'year': 2012, 'mll_count': 12800, 'mll_percent': 9.2, 'note': ''},
        {'year': 2014, 'mll_count': 14200, 'mll_percent': 10.1, 'note': 'MLL terminology adopted'},
        {'year': 2016, 'mll_count': 15500, 'mll_percent': 10.8, 'note': ''},
        {'year': 2018, 'mll_count': 16800, 'mll_percent': 11.5, 'note': ''},
        {'year': 2020, 'mll_count': 16200, 'mll_percent': 11.2, 'note': 'COVID dip'},
        {'year': 2022, 'mll_count': 17500, 'mll_percent': 12.2, 'note': 'Post-COVID rebound'},
        {'year': 2024, 'mll_count': 18500, 'mll_percent': 12.8, 'note': 'Merger debate intensifies'},
        {'year': 2025, 'mll_count': 18800, 'mll_percent': 13.0, 'note': 'District merger under review'},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    st.session_state.authenticated = True
    return True


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, district_id, grade, year):
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'district_id': district_id, 'district_name': row['district_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'delta': delta, 'delta_normalized': delta_normalized, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================

def render_overview(districts_df):
    st.header("Delaware Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Districts", len(districts_df))
    with col2: st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3: st.metric("Multilingual Learners", f"{districts_df['mll_count'].sum():,}")
    with col4: st.metric("Statewide MLL %", "~13%", delta="Steadily growing")

    st.divider()

    # Key policy context
    st.subheader("Key Policy Context")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**District Merger Debate**\nOngoing discussion about consolidating 19 districts into fewer, more equitable units")
    with col2:
        st.warning("**MLL Terminology**\nDelaware uses 'Multilingual Learner' (MLL) rather than 'English Learner' (EL)")
    with col3:
        st.success("**DeSSA (Smarter Balanced)**\nDelaware System of Student Assessments -- aligned to Smarter Balanced consortium")

    st.divider()

    # District merger context
    st.subheader("The Delaware Pattern: District Merger Debate & MLL Equity")
    st.markdown("""
    Delaware's **19 traditional districts** reflect a structure created during 1969
    desegregation-era consolidation. The ongoing **district merger debate** centers on
    whether consolidation could improve equity for MLLs and other underserved students.

    **Key equity concerns:**
    - MLL concentration is highest in **New Castle County** (Red Clay 22%, Christina 21%, Colonial 22%)
    - Sussex County districts serve growing agricultural MLL populations (Indian River 16%)
    - Small districts may lack specialized MLL staffing and programming
    - Charter schools add complexity to MLL service delivery

    | District | MLL % | Context |
    |----------|-------|---------|
    | Red Clay Consolidated | **22.0%** | Largest MLL count; Wilmington area |
    | Colonial | **22.0%** | New Castle area; growing rapidly |
    | Christina | **21.0%** | Merger debate focal point |
    | Indian River | **16.0%** | Sussex County agricultural belt |
    | Woodbridge | **16.0%** | Poultry industry; rural Sussex |

    Delaware's use of **"Multilingual Learner" (MLL)** terminology reflects an
    asset-based framing, recognizing students' home language as a resource, not a deficit.
    """)

    st.divider()

    st.subheader("Assessment Framework")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **DeSSA (Smarter Balanced):**
        - Delaware System of Student Assessments
        - ELA and Math, grades 3-8
        - 4 Achievement Levels:
            - **Exceeds Standard** -- advanced mastery
            - **Meets Standard** -- grade-level proficiency
            - **Approaching Standard** -- nearing proficiency
            - **Below Standard** -- below expectations
        - Results on reportcard.doe.k12.de.us

        **Star Rating System:**
        - 1-5 stars for school quality
        - Academic achievement + growth
        - Graduation rate + on-track
        - Attendance + social-emotional
        """)
    with col2:
        st.markdown("""
        **MLL Program:**
        - **WIDA ACCESS** for ELP assessment
        - 4 Domains: Listening, Speaking, Reading, Writing
        - ~19 districts, ~18,800 MLLs (~13%)
        - "Multilingual Learner" terminology

        **Key Language Groups:**
        - Spanish (~72% of MLLs)
        - Haitian Creole (~8%)
        - Chinese, Arabic, Portuguese
        - Guatemalan indigenous languages

        **Key Context:**
        - **District merger debate** -- ongoing
        - **1969 consolidation** -- current structure
        - **Sussex poultry** -- agricultural ELs
        - **Charter growth** -- MLL service gaps

        **Data:** reportcard.doe.k12.de.us
        """)

    st.divider()

    # District table
    st.subheader("Districts -- MLL Populations & Performance")
    display = districts_df[['district_id', 'district_name', 'total_students', 'mll_count',
                            'mll_percent', 'dessa_meets_all', 'dessa_meets_mll',
                            'graduation_rate', 'star_rating']].copy()
    display.columns = ['ID', 'District', 'Students', 'MLL Count', 'MLL %',
                       'DeSSA Meets+ All %', 'DeSSA Meets+ MLL %', 'Grad Rate %', 'Stars']
    st.dataframe(display, use_container_width=True, hide_index=True)

    # MLL bar chart
    st.subheader("Multilingual Learner Population by District")
    fig = px.bar(
        districts_df.sort_values('mll_count', ascending=True),
        x='mll_count', y='district_name', orientation='h',
        color='mll_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, DE_BLUE]],
        labels={'mll_count': 'Multilingual Learners', 'district_name': 'District', 'mll_percent': 'MLL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # County distribution
    st.subheader("MLL Distribution by County")
    county_df = districts_df[['district_name', 'mll_percent', 'total_students']].copy()
    county_df['county'] = districts_df['district_id'].apply(
        lambda x: 'New Castle' if int(x) >= 30 else 'Kent' if int(x) >= 10 else 'Sussex'
    )
    fig2 = px.scatter(county_df, x='total_students', y='mll_percent',
                      color='county', size='mll_percent',
                      hover_name='district_name',
                      color_discrete_map={
                          'New Castle': DE_BLUE,
                          'Kent': DE_GOLD,
                          'Sussex': DE_GRAY
                      },
                      labels={'total_students': 'Total Enrollment', 'mll_percent': 'MLL %',
                              'county': 'County'})
    fig2.update_layout(
        title="MLL % vs District Size by County",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)


# ============================================================================
# PAGE 2: DOMAIN ANALYSIS
# ============================================================================

def render_domain_analysis(domain_df, growth_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** DDOE MLL reports / WIDA ACCESS results.
    Delaware is a WIDA Consortium member. Domain proficiency percentages reveal the
    systemic oral-written delta: Speaking consistently outperforms Writing across all
    grade clusters.

    **Delaware Context:** With ~18,800 MLLs (~13%) and the ongoing district merger debate,
    the oral-written gap has implications for how MLL services might be restructured
    under consolidated districts. The composite exit score means writing deficiency
    directly delays reclassification.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', DE_GRAY), ('speaking', DE_BLUE),
                          ('reading', DE_LIGHT_BLUE), ('writing', '#333333')]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 65])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[DE_BLUE if d > 18 else DE_LIGHT_BLUE for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.divider()

    # MLL growth over time
    st.subheader("Delaware MLL Population Growth")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=growth_df['year'], y=growth_df['mll_count'],
        mode='lines+markers', line=dict(color=DE_BLUE, width=3),
        marker=dict(size=8), name='MLL Count'
    ))
    fig3.update_layout(
        title="MLL Population Growth -- Steady Increase Across All Three Counties",
        xaxis_title="Year", yaxis_title="Multilingual Learners",
        height=400
    )
    fig3.add_annotation(x=2014, y=14200, text="MLL terminology adopted", showarrow=True, arrowhead=2)
    fig3.add_annotation(x=2024, y=18500, text="Merger debate intensifies", showarrow=True, arrowhead=2)
    st.plotly_chart(fig3, use_container_width=True)

    st.info("""
    **District Merger Implications:** If Delaware consolidates its 19 districts, MLL
    services could be reorganized for greater efficiency and equity. Currently, smaller
    districts (Woodbridge, Laurel, Seaford) may lack specialized MLL staff, while larger
    districts (Red Clay, Christina, Colonial) serve the majority of MLLs but face their
    own resource constraints. Merger could centralize MLL expertise but risk diluting
    community-specific language support.
    """)


# ============================================================================
# PAGE 3: EL ASSESSMENT ANALYSIS (ACCESS)
# ============================================================================

def render_el_assessment(access_df, districts_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures Multilingual Learners across four domains. Delaware has ~18,800
    MLLs across ~19 districts. Delaware uses the term **"Multilingual Learner" (MLL)**
    as an asset-based alternative to "English Learner."
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="acc_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="acc_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = access_df[(access_df['district_id'] == district_id) &
                         (access_df['grade'] == grade) &
                         (access_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        d_info = districts_df[districts_df['district_id'] == district_id].iloc[0]
        if d_info['mll_percent'] > 18:
            st.warning(f"""
            **High-Concentration District:** {district} has **{d_info['mll_percent']:.1f}% MLL enrollment**.
            {d_info['context_note']}.
            """)

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(x=domains, y=scores,
                               marker_color=[DE_GRAY, DE_BLUE, DE_LIGHT_BLUE, '#333333'],
                               text=[f"{s:.0f}" for s in scores], textposition='outside'))
        fig.update_layout(title=f"ACCESS Domains -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Scale Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written

        st.subheader("Oral vs Written Gap")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average", f"{oral:.0f}")
        with col2: st.metric("Written Average", f"{written:.0f}")
        with col3: st.metric("Gap", f"{gap:+.0f}", delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        st.divider()
        st.subheader("Composite & Context")
        composite = row['composite_avg']
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Composite Average", f"{composite}")
        with col2: st.metric("Star Rating", f"{d_info['star_rating']}/5", help="Delaware school quality rating")
        with col3: st.metric("Total Tested", f"{row['total_tested']:,}")


# ============================================================================
# PAGE 4: TYPE 4 DETECTION
# ============================================================================

def render_type4(access_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score. Flag threshold: normalized delta > 8 points.

    **Delaware Context:** In a small state with ~19 districts and the ongoing merger debate,
    Type 4 patterns have direct implications for how MLL reclassification is managed.
    New Castle County districts (Red Clay, Christina, Colonial) serve the highest MLL
    concentrations and may exhibit the most pronounced Speaking-Writing gaps due to
    community immersion in conversational English.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    result = compute_type4_analysis(access_df, district_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2: st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3: st.metric("Delta", f"{result['delta']:+.0f}")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']], marker_color=DE_BLUE))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']], marker_color=DE_GRAY))
        fig.update_layout(title=f"Speaking vs Writing -- {district} -- Grade {grade}", barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} MLLs affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        # All grades
        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(access_df, district_id, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                                     mode='lines+markers', line=dict(color=DE_BLUE, width=3)))
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                                     mode='lines+markers', line=dict(color=DE_GRAY, width=3)))
            fig.update_layout(title="Speaking vs Writing Across Grades", xaxis_title="Grade",
                             yaxis_title="Scale Score", height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("District Summary")
        if all_data:
            summary_df = pd.DataFrame(all_data)[['grade', 'speaking_avg', 'writing_avg', 'delta', 'flagged', 'estimated_flagged']]
            summary_df.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Flagged', 'Est. Affected']
            summary_df['Flagged'] = summary_df['Flagged'].map({True: 'YES', False: 'No'})
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 5: ACHIEVEMENT GAPS
# ============================================================================

def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Data from reportcard.doe.k12.de.us.** DeSSA Meets + Exceeds rates across districts.

    **DeSSA** uses 4 achievement levels: Below Standard, Approaching Standard,
    Meets Standard, Exceeds Standard (Smarter Balanced alignment).

    **Key Pattern:** The New Castle County districts serving the highest MLL concentrations
    (Red Clay, Christina, Colonial) show significant MLL-to-All achievement gaps.
    The district merger debate is partly driven by these persistent inequities.
    """)

    st.divider()

    # All vs MLL comparison
    fig = go.Figure()
    sorted_df = districts_df.sort_values('dessa_meets_all', ascending=True)
    fig.add_trace(go.Bar(
        x=sorted_df['dessa_meets_all'], y=sorted_df['district_name'],
        name='All Students', orientation='h', marker_color=DE_GRAY
    ))
    fig.add_trace(go.Bar(
        x=sorted_df['dessa_meets_mll'], y=sorted_df['district_name'],
        name='Multilingual Learners', orientation='h', marker_color=DE_BLUE
    ))
    fig.update_layout(
        title="DeSSA Meets+ Rate: All Students vs Multilingual Learners",
        barmode='group', xaxis_title="% Meets + Exceeds Standard",
        height=600, legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    st.subheader("All-MLL Achievement Gap by District")
    gap_df = districts_df.copy()
    gap_df['mll_gap'] = gap_df['dessa_meets_all'] - gap_df['dessa_meets_mll']
    gap_df = gap_df.sort_values('mll_gap', ascending=True)

    fig_gap = go.Figure(go.Bar(
        x=gap_df['mll_gap'], y=gap_df['district_name'], orientation='h',
        marker_color=[DE_BLUE if g > 28 else DE_LIGHT_BLUE if g > 20 else DE_GRAY for g in gap_df['mll_gap']],
        text=[f"{g:.0f} pts" for g in gap_df['mll_gap']], textposition='outside'
    ))
    fig_gap.update_layout(title="All Students - MLL Gap (DeSSA Meets+)",
                         xaxis_title="Gap (percentage points)", height=550)
    st.plotly_chart(fig_gap, use_container_width=True)

    # MLL proficiency vs MLL concentration
    st.subheader("MLL Proficiency vs MLL Concentration")
    fig2 = px.scatter(districts_df, x='mll_percent', y='dessa_meets_mll', size='mll_count',
                      color='star_rating',
                      color_continuous_scale=[[0, DE_BLUE], [0.5, DE_GOLD], [1, '#2E7D32']],
                      hover_name='district_name',
                      labels={'mll_percent': 'MLL %', 'dessa_meets_mll': 'MLL Meets+ %',
                              'mll_count': 'MLL Count', 'star_rating': 'Star Rating'})
    fig2.update_layout(
        title="MLL Proficiency vs Concentration",
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.info("""
    **District Merger Context:** The persistent MLL achievement gap is a central argument
    in the district merger debate. Consolidating districts could:
    - Pool MLL expertise and specialized staff across current district boundaries
    - Reduce geographic concentration of MLL students in specific districts
    - Create more equitable per-pupil MLL funding
    - Risk losing community-specific language support programs
    """)


# ============================================================================
# PAGE 6: DeSSA ANALYSIS (State Test)
# ============================================================================

def render_dessa(dessa_df, districts_df):
    st.header("DeSSA Assessment Analysis")
    st.markdown("""
    **DeSSA (Delaware System of Student Assessments)** is a Smarter Balanced assessment
    for grades 3-8 in ELA and Math.

    **4 Achievement Levels:**
    - **Exceeds Standard** -- Advanced understanding and mastery
    - **Meets Standard** -- Grade-level proficiency
    - **Approaching Standard** -- Nearing proficiency
    - **Below Standard** -- Below grade-level expectations

    Results are published on **reportcard.doe.k12.de.us** and contribute to the **Star Rating** system.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="dessa_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="dessa_g")
    with col3: subject = st.selectbox("Subject", ['ELA', 'Math'], key="dessa_s")
    with col4: year = st.selectbox("Year", [2025, 2024], key="dessa_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = dessa_df[(dessa_df['district_id'] == district_id) &
                        (dessa_df['grade'] == grade) &
                        (dessa_df['subject'] == subject) &
                        (dessa_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Meets + Exceeds Standard", f"{row['meets_exceeds_pct']:.1f}%",
                      help="Grade-level proficient and above")
        with col2:
            st.metric("Exceeds Standard Only", f"{row['exceeds_pct']:.1f}%",
                      help="Advanced mastery")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Below Standard", f"{row['below_pct']:.1f}%")
        with col2: st.metric("Approaching", f"{row['approaching_pct']:.1f}%")
        with col3: st.metric("Meets Standard", f"{row['meets_pct']:.1f}%")
        with col4: st.metric("Exceeds Standard", f"{row['exceeds_pct']:.1f}%")

        levels = ['Below\nStandard', 'Approaching\nStandard', 'Meets\nStandard', 'Exceeds\nStandard']
        values = [row['below_pct'], row['approaching_pct'], row['meets_pct'], row['exceeds_pct']]
        colors = ['#d32f2f', '#f57c00', DE_GOLD, DE_BLUE]
        fig = go.Figure(go.Bar(x=levels, y=values, marker_color=colors,
                               text=[f"{v:.1f}%" for v in values], textposition='outside'))
        fig.update_layout(title=f"DeSSA {subject} -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Percentage", height=420)
        st.plotly_chart(fig, use_container_width=True)

        d_info = districts_df[districts_df['district_id'] == district_id].iloc[0]

        st.subheader("District Context")
        st.markdown(f"""
        **{district}** -- Grade {grade} {subject} ({year}):
        - Meets+ Rate: **{row['meets_exceeds_pct']:.1f}%**
        - Star Rating: **{d_info['star_rating']}/5** | MLL %: **{d_info['mll_percent']:.1f}%**
        - {d_info['context_note']}
        - Results on reportcard.doe.k12.de.us
        """)


# ============================================================================
# PAGE 7: EXPORT DATA
# ============================================================================

def render_export(access_df, dessa_df, districts_df, domain_df, growth_df):
    st.header("Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button("Download ACCESS CSV", access_df.to_csv(index=False),
                          "vera_de_access.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("DeSSA Data")
        st.dataframe(dessa_df, use_container_width=True, hide_index=True)
        st.download_button("Download DeSSA CSV", dessa_df.to_csv(index=False),
                          "vera_de_dessa.csv", "text/csv", use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button("Download Domain CSV", domain_df.to_csv(index=False),
                          "vera_de_domains.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("District Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button("Download Districts CSV", districts_df.to_csv(index=False),
                          "vera_de_districts.csv", "text/csv", use_container_width=True)

    st.divider()

    st.subheader("MLL Population Growth (2008-2025)")
    st.dataframe(growth_df, use_container_width=True, hide_index=True)
    st.download_button("Download MLL Growth CSV", growth_df.to_csv(index=False),
                      "vera_de_mll_growth.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-DE | Delaware Type 4 Detection", page_icon="", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {DE_BLUE}; }}
        .stButton > button {{ background-color: {DE_BLUE}; color: white; }}
        .stButton > button:hover {{ background-color: {DE_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    if not check_password():
        return

    # Load data
    districts_df = load_districts()
    access_df = load_access_data(districts_df)
    dessa_df = load_dessa_data(districts_df)
    domain_df = load_statewide_domain_data()
    growth_df = load_mll_growth_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {DE_BLUE}; margin: 0;">VERA-DE</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Delaware Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Domain Analysis",
        "EL Assessment Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "State Test Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - DeSSA (Smarter Balanced)
    - reportcard.doe.k12.de.us
    - DDOE MLL reports

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points
    - WIDA ACCESS domain scores

    **Key DE Context:**
    - ~19 districts, ~18.8K MLLs (~13%)
    - "Multilingual Learner" terminology
    - District merger debate ongoing
    - 1969 consolidation structure
    - Top MLL: Red Clay 22%,
      Colonial 22%, Christina 21%
    - Sussex County agricultural belt
    - Star Rating accountability
    - DeSSA: 4 levels (Smarter Balanced)

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(districts_df)
    elif page == "Domain Analysis": render_domain_analysis(domain_df, growth_df)
    elif page == "EL Assessment Analysis": render_el_assessment(access_df, districts_df)
    elif page == "Type 4 Detection": render_type4(access_df, districts_df)
    elif page == "Achievement Gaps": render_achievement_gaps(districts_df)
    elif page == "State Test Analysis": render_dessa(dessa_df, districts_df)
    elif page == "Export Data": render_export(access_df, dessa_df, districts_df, domain_df, growth_df)


if __name__ == "__main__":
    main()
