import streamlit as st
import streamlit.components.v1 as components
import openpyxl
from supabase import create_client, Client
import json
import time
import base64
from datetime import datetime, date, timedelta

# ==============================================================================
# 🔐 SECURE DATABASE CREDENTIALS BRIDGE
# ==============================================================================
SUPABASE_URL = "https://pysicrdtjayyxztoibep.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5c2ljcmR0amF5eXh6dG9pYmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0Mjk4NzMsImV4cCI6MjA5ODAwNTg3M30.5X0uesuo7NVf6KDxrEiM-6RIOJ2ffyxcOVsWJF52oNw"                  

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# Page Configurations
st.set_page_config(layout="wide", page_title="Universal Solar Digital Twin System")

if "active_site_id" not in st.session_state: st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state: st.session_state.is_admin_mode = False
if "managed_zones" not in st.session_state: 
    st.session_state.managed_zones = ["Zone A", "Zone B", "Zone C", "Unassigned"]
if "custom_tabs" not in st.session_state: st.session_state.custom_tabs = []

@st.cache_data(ttl=1)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception: return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# 🏡 MAIN ENTRY SITE GATEWAY
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("⚙️ Universal Solar Farm Engineering & Layout Tool")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            dev_pwd = st.text_input("Enter Control Password:", type="password")
            if dev_pwd == "devok":
                st.success("Access Unlocked")
                
                st.subheader("🗑️ Cloud Database Cleaner")
                if farm_options:
                    wipe_target = st.selectbox("Select Project to Clear:", farm_options, key="dev_clear_dropdown")
                    if st.button("💥 Purge Cloud Data Records", type="primary"):
                        with st.spinner(f"Purging data assets for {wipe_target}..."):
                            try:
                                supabase.table("farms").delete().eq("name", wipe_target).execute()
                                st.success(f"Purged all records for {wipe_target}!")
                                st.cache_data.clear()
                                time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Purge rejected: {str(e)}")
                
                st.write("---")
                st.subheader("🚀 Onboard New Layout Framework")
                new_site_name = st.text_input("Assign Site Project Name:")
                init_admin_pwd = st.text_input("Assign Management Password:", value="ok")
                init_inst_pwd = st.text_input("Assign Field Access Password:", value="1234")
                
                uploaded_blueprint = st.file_uploader("Upload Master Blueprint Sheet (.xlsx)", type=["xlsx"])
                
                if uploaded_blueprint and new_site_name and st.button("Compile & Parse Structural Blueprint"):
                    with st.spinner("Parsing granular array matrices..."):
                        wb = openpyxl.load_workbook(uploaded_blueprint, data_only=True)
                        sheet = wb.active
                        max_rows, max_cols = sheet.max_row, sheet.max_column
                        
                        new_fid = None
                        try:
                            farm_node = supabase.table("farms").insert({
                                "name": new_site_name, "admin_password": init_admin_pwd, "installer_password": init_inst_pwd,
                                "max_rows": max_rows, "max_cols": max_cols, "is_published": False
                            }).execute()
                            if farm_node.data: new_fid = farm_node.data[0]["id"]
                        except Exception: pass
                        
                        if new_fid:
                            structures_queue = []
                            cell_counter = 1
                            
                            for r in range(1, max_rows + 1):
                                for c in range(1, max_cols + 1):
                                    cell = sheet.cell(row=r, column=c)
                                    
                                    has_top = cell.border and cell.border.top and cell.border.top.style
                                    has_left = cell.border and cell.border.left and cell.border.left.style
                                    has_bottom = cell.border and cell.border.bottom and cell.border.bottom.style
                                    has_right = cell.border and cell.border.right and cell.border.right.style
                                    
                                    if has_top or has_left or has_bottom or has_right:
                                        structures_queue.append({
                                            "farm_id": new_fid,
                                            "table_label": f"C-{cell_counter}",
                                            "min_r": r, "max_r": r,
                                            "min_c": c, "max_c": c,
                                            "assigned_zone": "Unassigned",
                                            "border_top": bool(has_top),
                                            "border_left": bool(has_left),
                                            "border_bottom": bool(has_bottom),
                                            "border_right": bool(has_right)
                                        })
                                        cell_counter += 1
                            
                            for idx in range(0, len(structures_queue), 50):
                                try: supabase.table("structures").insert(structures_queue[idx:idx+50]).execute()
                                except Exception: pass
                                time.sleep(0.02)
                                
                            st.success("Granular grid framework built perfectly!")
                            st.cache_data.clear(); st.rerun()

    st.subheader("🌐 Entry Gateway Workspace Portal")
    if farm_options:
        with st.form("workspace_access_form"):
            chosen_farm_name = st.selectbox("Select Project Site Layout Location:", farm_options)
            entered_inst_pass = st.text_input("Enter Access Password:", type="password")
            if st.form_submit_button("🚀 Open Workspace"):
                target_site_record = next(f for f in all_registered_farms if f["name"] == chosen_farm_name)
                if str(entered_inst_pass) == str(target_site_record.get("installer_password", "1234")):
                    st.session_state.active_site_id = target_site_record["id"]
                    st.session_state.active_site_name = target_site_record["name"]
                    st.session_state.admin_key_match = target_site_record.get("admin_password") or "ok"
                    st.rerun()
                else: st.error("Incorrect password credentials.")

# ==============================================================================
# 🗂️ PHASE 2: INTERNAL OPERATIONS TRACKING PLATFORM COMMAND CENTER
# ==============================================================================
else:
    current_farm_record = supabase.table("farms").select("*").eq("id", st.session_state.active_site_id).execute().data[0]
    site_is_published = current_farm_record.get("is_published", False)

    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.subheader(f"📍 Operational Twin Workspace — {st.session_state.active_site_name}")
    with col_h2:
        if st.button("🚪 Exit Site"): st.session_state.active_site_id = None; st.session_state.is_admin_mode = False; st.rerun()
            
    with st.sidebar:
        st.header("🔐 Workspace Clearances")
        if not st.session_state.is_admin_mode:
            with st.form("admin_upgrade_form", clear_on_submit=True):
                adm_pass = st.text_input("Upgrade to Admin Mode:", type="password")
                if st.form_submit_button("Verify Clearance"):
                    if str(adm_pass) == str(st.session_state.admin_key_match):
                        st.session_state.is_admin_mode = True; st.rerun()
        else:
            st.info("⚡ Admin Permissions Active")
            
            # --- GLOBAL PUBLISH ACTIVATION TOGGLE ---
            st.write("---")
            st.subheader("📢 Field Deployment Release")
            if not site_is_published:
                if st.button("🚀 Publish Layout Workspace to Field Crew", type="primary"):
                    supabase.table("farms").update({"is_published": True}).eq("id", st.session_state.active_site_id).execute()
                    st.success("Workspace deployed out live successfully!")
                    time.sleep(0.5); st.rerun()
            else:
                st.success("✅ Layout Workspace Status: Live to Crew")
                if st.button("🔒 Revoke Live Deployment and Hide Workspaces"):
                    supabase.table("farms").update({"is_published": False}).eq("id", st.session_state.active_site_id).execute()
                    st.rerun()
            
            st.write("---")
            st.subheader("🛠️ Custom Tracker Tab Builder")
            custom_tab_name = st.text_input("Assign New Tracker Tab Label:", placeholder="e.g. Floating Cell, Cabling Phase...")
            if st.button("✨ Instantiate Phase Tab") and custom_tab_name:
                if custom_tab_name not in st.session_state.custom_tabs:
                    st.session_state.custom_tabs.append(custom_tab_name)
                    st.success(f"Instantiated '{custom_tab_name}'!")
                    time.sleep(0.4); st.rerun()
                    
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    # Database Pull
    @st.cache_data(ttl=1)
    def load_site_isolated_tables(farm_id):
        try: return supabase.table("structures").select("*").eq("farm_id", farm_id).order("id").execute().data or []
        except Exception: return []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)

    min_r = min([b.get("min_r", 1) for b in active_table_data]) if active_table_data else 1
    max_r = max([b.get("max_r", 100) for b in active_table_data]) if active_table_data else 100
    min_c = min([b.get("min_c", 1) for b in active_table_data]) if active_table_data else 1
    max_c = max([b.get("max_c", 150) for b in active_table_data]) if active_table_data else 150

    CELL_SIZE = 14
    canvas_w = (max_c - min_c + 5) * CELL_SIZE
    canvas_h = (max_r - min_r + 5) * CELL_SIZE
    json_str = json.dumps(active_table_data)

    # Automatically handle fallback zone structures
    for b in active_table_data:
        z = b.get("assigned_zone")
        if z and z not in st.session_state.managed_zones:
            st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, z)

    # ==============================================================================
    # 🚨 INTERFACE ROUTING ENGINE RULES (LOCKED SETUP CHECK SYSTEM)
    # ==============================================================================
    if not site_is_published and not st.session_state.is_admin_mode:
        # If site layout initialization config setup isn't finalized, lock out out all tabs from crew views
        st.write("---")
        st.warning("🚧 **Configuration Incomplete:** This project site layout layout is currently hidden. Please wait for an authorized Administrator to finalize initial setup phases.")
        st.info("🔒 If you are the site manager, please log in as Admin in the left clearance panel to configure zoning boundaries.")
        st.stop()

    # Dynamic Tab Compilation Array routing logic
    if st.session_state.is_admin_mode:
        # Admin gets full access configuration views to organize elements
        setup_tabs = st.tabs([
            "🖼️ Step 1: Base Overview & Zone Assignation", 
            "🔌 Step 2: Electrical Inverter Mapping", 
            "📌 Step 3: Pegging & Piling Customizer",
            "🏪 Step 4: Transformer Drop Hubs"
        ])
        
        # --- STAGE 1: SETUPS OVERVIEW TAB ---
        with setup_tabs[0]:
            st.markdown("### 🖼️ Operational Field Zoning Assignation Engine")
            col_z1, col_z2 = st.columns([6, 4])
            with col_z1:
                target_paint_zone = st.selectbox("Active Selector Target Zone Label Options:", st.session_state.managed_zones, index=0)
            with col_z2:
                new_zone_opt = st.text_input("➕ Extend Managed Zone List Registry:", placeholder="e.g. Zone D...")
                if st.button("Register Variant Entry") and new_zone_opt:
                    clean_opt = new_zone_opt.strip()
                    if clean_opt not in st.session_state.managed_zones:
                        st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, clean_opt)
                        st.rerun()

            html_zone_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; font-family:sans-serif; user-select:none;">
                <div id="dialogue_overlay" style="display:none; position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:#1e293b; padding:18px 35px; border-radius:8px; border:2px solid #38bdf8; z-index:100000; box-shadow: 0 10px 40px rgba(0,0,0,0.85); text-align:center;">
                    <div style="color:#f1f5f9; font-weight:bold; margin-bottom:14px; font-size:15px;">Assign Selected Section Cluster to <span id="lbl_zone" style="color:#38bdf8; text-decoration:underline;"></span>?</div>
                    <button id="btn_yes" style="background:#22c55e; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; margin-right:12px; font-size:14px;">Yes, Stage Change</button>
                    <button id="btn_no" style="background:#ef4444; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:14px;">No</button>
                </div>
                <div style="width:100%; max-height:600px; overflow:auto; border:2px solid #1e293b; border-radius:8px;">
                    <canvas id="zone_canvas" width="CANVAS_W" height="CANVAS_H" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = __JSON_DATA__;
                    const canvas = document.getElementById("zone_canvas");
                    const ctx = canvas.getContext('2d');
                    const paintZone = 'PAINT_ZONE_VAL';
                    const CELL = CELL_SIZE_VAL;
                    const offsetCol = MIN_C_VAL - 2; const offsetRow = MIN_R_VAL - 2;
                    let hoverGroupBlockIds = []; let stagedBlockIds = [];

                    function getZoneColor(zoneName) {
                        if (!zoneName || zoneName === 'Unassigned') return '#27272a';
                        let hash = 0; for (let i = 0; i < zoneName.length; i++) { hash = zoneName.charCodeAt(i) + ((hash << 5) - hash); }
                        return `hsl(${Math.abs(hash % 360)}, 80%, 50%)`;
                    }
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        blocks.forEach(b => {
                            let isHovered = hoverGroupBlockIds.includes(b.id); let isStaged = stagedBlockIds.includes(b.id);
                            ctx.fillStyle = getZoneColor(b.assigned_zone);
                            if (isHovered) ctx.fillStyle = 'rgba(56, 189, 248, 0.4)';
                            let x = (b.min_c - offsetCol) * CELL; let y = (b.min_r - offsetRow) * CELL;
                            ctx.fillRect(x, y, CELL, CELL);
                            ctx.strokeStyle = '#18181b'; ctx.lineWidth = 0.5;
                            if (b.border_top) { ctx.strokeStyle='#f4f4f5'; ctx.lineWidth=1.5; }
                            ctx.strokeRect(x, y, CELL, CELL);
                            if (isStaged) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.strokeRect(x, y, CELL, CELL); }
                        });
                    }
                    function getGroupCluster(targetBlock) {
                        let cluster = [];
                        blocks.forEach(b => {
                            if (Math.abs(b.min_c - targetBlock.min_c) < 15 && Math.abs(b.min_r - targetBlock.min_r) < 30) { cluster.push(b.id); }
                        });
                        return cluster;
                    }
                    canvas.addEventListener('mousemove', (e) => {
                        if (stagedBlockIds.length > 0) return;
                        const rect = canvas.getBoundingClientRect();
                        const mx = e.clientX - rect.left; const my = e.clientY - rect.top;
                        let found = null;
                        blocks.forEach(b => {
                            let x = (b.min_c - offsetCol) * CELL; let y = (b.min_r - offsetRow) * CELL;
                            if (mx >= x && mx <= x + CELL && my >= y && my <= y + CELL) found = b;
                        });
                        if (found) { hoverGroupBlockIds = getGroupCluster(found); } else { hoverGroupBlockIds = []; }
                        draw();
                    });
                    canvas.addEventListener('click', (e) => {
                        if (stagedBlockIds.length > 0) return;
                        if (hoverGroupBlockIds.length > 0) {
                            stagedBlockIds = [...hoverGroupBlockIds];
                            document.getElementById("lbl_zone").innerText = paintZone;
                            document.getElementById("dialogue_overlay").style.display = "block";
                            draw();
                        }
                    });
                    document.getElementById("btn_yes").addEventListener('click', () => {
                        stagedBlockIds.forEach(id => {
                            let target = blocks.find(b => b.id === id); if (target) target.assigned_zone = paintZone;
                            fetch('SUPABASE_URL_VAL/rest/v1/structures?id=eq.' + id, {
                                method: "PATCH", headers: { "apikey": 'SUPABASE_KEY_VAL', "Authorization": 'Bearer SUPABASE_KEY_VAL', "Content-Type": "application/json" },
                                body: JSON.stringify({ "assigned_zone": paintZone })
                            });
                        });
                        stagedBlockIds = []; document.getElementById("dialogue_overlay").style.display = "none"; draw();
                    });
                    document.getElementById("btn_no").addEventListener('click', () => {
                        stagedBlockIds = []; document.getElementById("dialogue_overlay").style.none"; draw();
                    });
                    draw();
                })();
            </script>
            """
            html_zone_engine = html_zone_engine.replace("CANVAS_W", str(canvas_w)).replace("CANVAS_H", str(canvas_h)).replace("__JSON_DATA__", json_str).replace("PAINT_ZONE_VAL", str(target_paint_zone)).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MIN_R_VAL", str(min_r)).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            components.html(html_zone_engine, height=660)

        # --- STAGE 2: INVERTER SETUP VIEWS ---
        with setup_tabs[1]:
            st.markdown("### 🔌 Electrical Inverter Infrastructure Integration Node")
            html_inverter_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px;"><div style="width:100%; max-height:580px; overflow:auto; border:2px solid #1e293b; border-radius:8px;"><canvas id="inv_canvas" width="CANVAS_W" height="CANVAS_H" style="background:#020617; display:block;"></canvas></div></div>
            <script>(function() { const blocks = __JSON_DATA__; const canvas = document.getElementById("inv_canvas"); const ctx = canvas.getContext('2d'); const CELL = CELL_SIZE_VAL; const offsetCol = MIN_C_VAL - 2; const offsetRow = MIN_R_VAL - 2; blocks.forEach(b => { ctx.fillStyle = '#1e293b'; let x = (b.min_c - offsetCol) * CELL; let y = (b.min_r - offsetRow) * CELL; ctx.fillRect(x, y, CELL, CELL); ctx.strokeStyle = '#020617'; ctx.lineWidth = 0.5; if (b.border_top) { ctx.strokeStyle='#ff007f'; ctx.lineWidth=2.0; } ctx.strokeRect(x, y, CELL, CELL); }); })();</script>
            """
            html_inverter_engine = html_inverter_engine.replace("CANVAS_W", str(canvas_w)).replace("CANVAS_H", str(canvas_h)).replace("__JSON_DATA__", json_str).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MIN_R_VAL", str(min_r))
            components.html(html_inverter_engine, height=620)

        # --- STAGE 3: BLUEPRINT TEMPLATE PROPAGATION ---
        with setup_tabs[2]:
            st.markdown("### 📌 Component Placement Microscale Engineering Template Engine")
            col_t1, col_t2 = st.columns([4, 6])
            with col_t1:
                html_micro_template = """
                <div style="background:#0f172a; padding:15px; border-radius:12px; text-align:center;"><canvas id="micro_canvas" width="300" height="200" style="background:#020617; border:2px dashed #38bdf8; border-radius:6px; cursor:crosshair;"></canvas><div style="margin-top:12px;"><button style="background:#22c55e; color:white; border:none; padding:6px 12px; border-radius:4px; font-weight:bold; cursor:pointer;" onclick="alert('Component Pattern Cloned Fleetwide!')">💾 Apply & Replicate Fleetwide</button></div></div>
                <script>const c = document.getElementById("micro_canvas"); const ctx = c.getContext('2d'); ctx.fillStyle='#334155'; ctx.fillRect(40,30,220,140); ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.strokeRect(40,30,220,140); ctx.fillStyle='#ef4444'; ctx.beginPath(); ctx.arc(80,100,6,0,Math.PI*2); ctx.fill(); ctx.fillStyle='#ef4444'; ctx.beginPath(); ctx.arc(220,100,6,0,Math.PI*2); ctx.fill();</script>
                """
                components.html(html_micro_template, height=280)

        with setup_tabs[3]:
            st.markdown("### 🏪 Transformer Station Network Grid Loop Nodes")

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (ONLY VISIBLE ONCE DEPLOYED LIVE BY ADMIN)
        # ==============================================================================
        crew_tabs = st.tabs([
            "📌 Pegging Phase", "🪵 Piling Operations", "🏗️ Mounting Structures", "☀️ PV Module Tracking"
        ] + [f"🛠️ {ct}" for ct in st.session_state.custom_tabs])

        def inject_crew_tracking_map(layer_key, data_array, min_c, max_c, min_r, max_r):
            json_points = json.dumps(data_array)
            today_str = str(date.today())
            canvas_w = (max_c - min_c + 5) * 14
            canvas_h = (max_r - min_r + 5) * 14

            return f"""
            <div style="background:#090d16; padding:12px; border-radius:12px;"><div style="width:100%; max-height:600px; overflow:auto; border:2px solid #1e293b; border-radius:8px;"><canvas id="crew_{layer_key}" width="{canvas_w}" height="{canvas_h}" style="background:#020617; display:block; cursor:pointer;"></canvas></div></div>
            <script>
                (function() {{
                    const blocks = {json_points}; const canvas = document.getElementById("crew_{layer_key}"); const ctx = canvas.getContext('2d');
                    const CELL = 14; const offsetCol = {min_c} - 2; const offsetRow = {min_r} - 2;
                    function draw() {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        blocks.forEach(b => {{
                            ctx.fillStyle = b['{layer_key}_status'] === 'completed' ? '#22c55e' : '#2563eb';
                            let x = (b.min_c - offsetCol) * CELL; let y = (b.min_r - offsetRow) * CELL;
                            ctx.fillRect(x, y, CELL, CELL); ctx.strokeStyle = '#0f172a'; ctx.strokeRect(x, y, CELL, CELL);
                        }});
                    }}
                    canvas.addEventListener('click', (e) => {{
                        const rect = canvas.getBoundingClientRect(); const cx = e.clientX - rect.left; const cy = e.clientY - rect.top;
                        blocks.forEach(b => {{
                            let x = (b.min_c - offsetCol) * CELL; let y = (b.min_r - offsetRow) * CELL;
                            if (cx >= x && cx <= x + CELL && cy >= y && cy <= y + CELL) {{
                                b['{layer_key}_status'] = 'completed';
                                const p = {{}}; p['{layer_key}_status'] = 'completed'; p['{layer_key}_date'] = '{today_str}';
                                fetch('{SUPABASE_URL}/rest/v1/structures?id=eq.' + b.id, {{
                                    method: "PATCH", headers: {{ "apikey": '{SUPABASE_KEY}', "Authorization": 'Bearer {SUPABASE_KEY}', "Content-Type": "application/json" }},
                                    body: JSON.stringify(p)
                                }}).then(() => draw());
                            }}
                        }});
                    }});
                    draw();
                })();
            </script>
            """

        def process_crew_tab(tab_obj, key_val):
            with tab_obj:
                components.html(inject_crew_tracking_map(key_val, active_table_data, min_c, max_c, min_r, max_r), height=640)

        process_crew_tab(crew_tabs[0], "pegging")
        process_crew_tab(crew_tabs[1], "piling")
        process_crew_tab(crew_tabs[2], "mounting")
        process_crew_tab(crew_tabs[3], "modules")
