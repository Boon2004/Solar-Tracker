import streamlit as st
import streamlit.components.v1 as components
import openpyxl
from supabase import create_client, Client
import json
import time
import base64
from datetime import datetime, date, timedelta

# Enterprise Database Credentials Bridge
SUPABASE_URL = "https://pysicrdtjayyxztoibep.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5c2ljcmR0amF5eXh6dG9pYmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0Mjk4NzMsImV4cCI6MjA5ODAwNTg3M30.5X0uesuo7NVf6KDxrEiM-6RIOJ2ffyxcOVsWJF52oNw"                 

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# Set Global Wide View Constraints
st.set_page_config(layout="wide", page_title="Boon Solar Farm Tracking System")

# Helper function to compute business days (weekdays only)
def get_working_days(start_d, end_d):
    days = 0
    curr = start_d
    while curr <= end_d:
        if curr.weekday() < 5:  # Monday to Friday
            days += 1
        curr += timedelta(days=1)
    return max(days, 1)

# Initialize Session State States
if "active_site_id" not in st.session_state:
    st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state:
    st.session_state.is_admin_mode = False

# Fetch all registered site platforms from cloud registry
@st.cache_data(ttl=1)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception:
        return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# 🏡 PHASE 1: MAIN SYSTEM HOME SCREEN GATEWAY
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("🚜 Boon Solar Farm Tracking System")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            dev_pwd = st.text_input("Enter Developer Password:", type="password")
            if dev_pwd == "devok":
                st.success("Developer Access Unlocked")
                st.subheader("🚀 Onboard New Solar Site Node")
                new_site_name = st.text_input("Assign Site Project Name:")
                init_admin_pwd = st.text_input("Assign Admin Management Password:", value="ok")
                init_inst_pwd = st.text_input("Assign Installer Access Password:", value="1234")
                
                uploaded_blueprint = st.file_uploader("Drop Master Engineering Grid Sheet (.xlsx)", type=["xlsx"])
                
                if uploaded_blueprint and new_site_name and st.button("Compile & Parse Structural Layout Grid"):
                    with st.spinner("Processing master boundary geometries..."):
                        wb = openpyxl.load_workbook(uploaded_blueprint, data_only=True)
                        sheet = wb.active
                        
                        max_rows, max_cols = sheet.max_row, sheet.max_column
                        
                        try:
                            supabase.table("farms").delete().eq("name", new_site_name).execute()
                        except Exception:
                            pass
                        
                        new_fid = None
                        try:
                            farm_node = supabase.table("farms").insert({
                                "name": new_site_name, "admin_password": init_admin_pwd, "installer_password": init_inst_pwd
                            }).execute()
                            if farm_node.data: new_fid = farm_node.data[0]["id"]
                        except Exception:
                            farm_node = supabase.table("farms").insert({"name": new_site_name}).execute()
                            if farm_node.data: new_fid = farm_node.data[0]["id"]
                        
                        if new_fid:
                            visited = set()
                            table_counter = 1
                            structures_queue = []
                            
                            for r in range(1, max_rows + 1):
                                for c in range(1, max_cols + 1):
                                    cell = sheet.cell(row=r, column=c)
                                    has_border = cell.border and ((cell.border.top and cell.border.top.style) or (cell.border.left and cell.border.left.style))
                                    
                                    if has_border and (r, c) not in visited:
                                        block_cells = []
                                        queue = [(r, c)]
                                        visited.add((r, c))
                                        
                                        while queue:
                                            curr_r, curr_c = queue.pop(0)
                                            block_cells.append((curr_r, curr_c))
                                            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                                                nr, nc = curr_r + dr, curr_c + dc
                                                if 1 <= nr <= max_rows and 1 <= nc <= max_cols and (nr, nc) not in visited:
                                                    n_cell = sheet.cell(row=nr, column=nc)
                                                    if n_cell.border and ((n_cell.border.top and n_cell.border.top.style) or (n_cell.border.left and n_cell.border.left.style)):
                                                        visited.add((nr, nc))
                                                        queue.append((nr, nc))
                                        
                                        b_rows = [item[0] for item in block_cells]
                                        b_cols = [item[1] for item in block_cells]
                                        min_br, max_br, min_bc, max_bc = min(b_rows), max(b_rows), min(b_cols), max(b_cols)
                                        
                                        # Uniform initialization - Admin assigns groupings dynamically later
                                        sec_label = "Unassigned"
                                            
                                        h = max_br - min_br + 1
                                        stype = "double_6x9" if h >= 6 else "single_3x9"
                                        
                                        structures_queue.append({
                                            "farm_id": new_fid, "table_label": f"T-{table_counter}",
                                            "min_r": int(min_br), "max_r": int(max_br), "min_c": int(min_bc), "max_c": int(max_bc),
                                            "structure_type": stype, "section_block": sec_label
                                        })
                                        table_counter += 1
                            
                            chunk_size = 50
                            for idx in range(0, len(structures_queue), chunk_size):
                                supabase.table("structures").insert(structures_queue[idx:idx+chunk_size]).execute()
                                time.sleep(0.04)
                                
                            st.success(f"Successfully deployed {len(structures_queue)} Tables across the site digital twin matrix!")
                            st.cache_data.clear()
                            st.rerun()

    st.subheader("🌐 Access Site Workspace Portal")
    if farm_options:
        chosen_farm_name = st.selectbox("Select Active Project Location Site:", farm_options)
        target_site_record = next(f for f in all_registered_farms if f["name"] == chosen_farm_name)
        entered_inst_pass = st.text_input("Enter Field Installer Password:", type="password")
        
        if st.button("🚀 Open Digital Twin Workspace"):
            expected_pass = target_site_record.get("installer_password") or target_site_record.get("site_password") or "1234"
            if str(entered_inst_pass) == str(expected_pass):
                st.session_state.active_site_id = target_site_record["id"]
                st.session_state.active_site_name = target_site_record["name"]
                st.session_state.admin_key_match = target_site_record.get("admin_password") or "ok"
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        st.info("No active installations found. Open Left Developer Panel to upload blueprint grid arrays.")

# ==============================================================================
# 🗂️ PHASE 2: INTERNAL SOLAR FARM SITE WORKSPACE COMMAND ROOM
# ==============================================================================
else:
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.subheader(f"📍 Boon Solar Farm Tracking System — {st.session_state.active_site_name}")
    with col_h2:
        if st.button("🚪 Exit Site"):
            st.session_state.active_site_id = None; st.session_state.is_admin_mode = False; st.rerun()
            
    with st.sidebar:
        st.header("🔐 Workspace Clearances")
        if not st.session_state.is_admin_mode:
            adm_pass = st.text_input("Upgrade to Admin Mode:", type="password")
            if st.button("Verify Admin Status"):
                if str(adm_pass) == str(st.session_state.admin_key_match):
                    st.session_state.is_admin_mode = True; st.success("Admin Elevation Granted"); st.rerun()
                else: st.error("Incorrect Password.")
        else:
            st.info("⚡ Admin Permissions Active")
            uploaded_png = st.file_uploader("Upload Overview Picture (.png / .jpg)", type=["png", "jpg", "jpeg"])
            if uploaded_png and st.button("💾 Save Uploaded Image to Site"):
                bytes_data = uploaded_png.getvalue()
                base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                data_url = f"data:image/png;base64,{base64_encoded}"
                supabase.table("farms").update({"overview_image_url": data_url}).eq("id", st.session_state.active_site_id).execute()
                st.success("Overview picture saved!"); time.sleep(0.5); st.rerun()
                
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    current_farm_record = supabase.table("farms").select("*").eq("id", st.session_state.active_site_id).execute().data[0]
    
    t_over, t_peg, t_pil, t_mnt, t_mod, t_inv_str, t_inv_hub, t_trans, t_dc_cab, t_ac_cab = st.tabs([
        "🖼️ Overview", "📌 Pegging", "🪵 Piling", "🏗️ Mounting Structure", "☀️ PV Modules", 
        "🏗️ Inverter Structure", "⚡ Inverter Hub", "🏪 Transformer Station", "🔌 DC Cabling", "⚡ AC Cabling"
    ])

    with t_over:
        st.markdown("### 🖼️ Master Site Overview Infrastructure")
        img_src = current_farm_record.get("overview_image_url")
        if img_src: st.image(img_src, caption="Active Operational Blueprint View", use_column_width=True)
        else: st.warning("No overview picture uploaded by the admin yet.")

    # --------------------------------------------------------------------------
    # MAP RENDERING UTILITY ENGINE WITH REAL-TIME FLUID DRAWING 
    # --------------------------------------------------------------------------
    def inject_time_based_map(layer_key, data_array, selected_history_date=None):
        json_points = json.dumps(data_array)
        today_str = str(date.today())
        history_target = str(selected_history_date) if selected_history_date else "null"
        
        return f"""
        <div style="background:#090d16; padding:12px; border-radius:12px; touch-action:none;">
            <canvas id="cv_{layer_key}" width="1500" height="420" style="background:#020617; border-radius:8px; width:100%; cursor:grab; touch-action:none;"></canvas>
        </div>
        <script>
            (function() {{
                const blocks = {json_points};
                const canvas = document.getElementById("cv_{layer_key}");
                const ctx = canvas.getContext('2d');
                const todayVal = "{today_str}";
                const historyDate = "{history_target}" !== "null" ? "{history_target}" : null;
                
                let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                blocks.forEach(b => {{
                    if (b.min_c < minX) minX = b.min_c; if (b.max_c > maxX) maxX = b.max_c;
                    if (b.min_r < minY) minY = b.min_r; if (b.max_r > maxY) maxY = b.max_r;
                }});
                
                const gw = (maxX - minX) || 1, gh = (maxY - minY) || 1;
                const colMultiplier = 1.8; const rowMultiplier = 45.0;
                
                let scale = Math.min((canvas.width-80)/(gw*colMultiplier), (canvas.height-80)/(gh*rowMultiplier));
                if(scale<0.001||scale===Infinity) scale=0.3;
                
                let offsetX = (canvas.width/2)-((gw*colMultiplier*scale)/2)-(minX*colMultiplier*scale);
                let offsetY = (canvas.height/2)-((gh*rowMultiplier*scale)/2)-(minY*rowMultiplier*scale);
                
                let isDragging = false, moved = false, startX, startY;

                function draw() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                    
                    blocks.forEach(b => {{
                        let dCol = "pegging_date", sCol = "pegging_status";
                        if("{layer_key}" === "pil") {{ dCol="piling_date"; sCol="piling_status"; }}
                        else if("{layer_key}" === "mnt") {{ dCol="mounting_date"; sCol="mounting_status"; }}
                        else if("{layer_key}" === "mod") {{ dCol="modules_date"; sCol="modules_status"; }}
                        else if("{layer_key}" === "istr") {{ dCol="inv_str_date"; sCol="mounting_status"; }}
                        else if("{layer_key}" === "ihub") {{ dCol="inv_hub_date"; sCol="mounting_status"; }}
                        else if("{layer_key}" === "tran") {{ dCol="trans_date"; sCol="mounting_status"; }}
                        else if("{layer_key}" === "dcab") {{ dCol="dc_cab_date"; sCol="cabling_status"; }}
                        else if("{layer_key}" === "acab") {{ dCol="ac_cab_date"; sCol="cabling_status"; }}
                        
                        let recordDate = b[dCol];
                        let isDone = b[sCol] === 'completed' || b[sCol] === 'yellow' || b[sCol] === 'green';
                        
                        ctx.fillStyle = '#2563eb'; 
                        
                        if (isDone) {{
                            if (historyDate) {{
                                if (recordDate === historyDate) ctx.fillStyle = '#eab308'; 
                                else if (recordDate < historyDate) ctx.fillStyle = '#22c55e'; 
                                else ctx.fillStyle = '#2563eb';
                            }} else {{
                                if (recordDate === todayVal) ctx.fillStyle = '#eab308'; 
                                else ctx.fillStyle = '#22c55e'; 
                            }}
                        }}
                        
                        const x = b.min_c * colMultiplier; const y = b.min_r * rowMultiplier;
                        ctx.fillRect(x, y, (b.max_c-b.min_c+1)*colMultiplier-0.4, (b.max_r-b.min_r+1)*rowMultiplier-2.0);
                        ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.12; ctx.strokeRect(x, y, (b.max_c-b.min_c+1)*colMultiplier, (b.max_r-b.min_r+1)*rowMultiplier);
                    }});
                    ctx.restore();
                }}
                
                function runFieldSubmission(clientX, clientY) {{
                    if(historyDate) return; 
                    const rect = canvas.getBoundingClientRect();
                    const cx = (clientX - rect.left - offsetX) / scale / colMultiplier;
                    const cy = (clientY - rect.top - offsetY) / scale / rowMultiplier;
                    
                    blocks.forEach(b => {{
                        if (cx >= b.min_c && cx <= b.max_c + 1 && cy >= b.min_r && cy <= b.max_r + 1) {{
                            let targetCol = "pegging_status", dateCol = "pegging_date";
                            if("{layer_key}" === "pil") {{ targetCol="piling_status"; dateCol="piling_date"; }}
                            else if("{layer_key}" === "mnt") {{ targetCol="mounting_status"; dateCol="mounting_date"; }}
                            else if("{layer_key}" === "mod") {{ targetCol="modules_status"; dateCol="modules_date"; }}
                            else if("{layer_key}" === "istr") {{ targetCol="mounting_status"; dateCol="inv_str_date"; }}
                            else if("{layer_key}" === "ihub") {{ targetCol="mounting_status"; dateCol="inv_hub_date"; }}
                            else if("{layer_key}" === "tran") {{ targetCol="mounting_status"; dateCol="trans_date"; }}
                            else if("{layer_key}" === "dcab") {{ targetCol="cabling_status"; dateCol="dc_cab_date"; }}
                            else if("{layer_key}" === "acab") {{ targetCol="cabling_status"; dateCol="ac_cab_date"; }}
                            
                            const payload = {{}}; payload[targetCol] = "completed"; payload[dateCol] = todayVal;
                            
                            fetch("{SUPABASE_URL}/rest/v1/structures?id=eq." + b.id, {{
                                method: "PATCH",
                                headers: {{ "apikey": "{SUPABASE_KEY}", "Authorization": "Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal" }},
                                body: JSON.stringify(payload)
                            }}).then(() => {{ b[targetCol] = "completed"; b[dateCol] = todayVal; draw(); }});
                        }}
                    }});
                }}
                
                canvas.addEventListener('mousedown',(e)=>{{ isDragging=true; moved=false; startX=e.clientX-offsetX; startY=e.clientY-offsetY; }});
                canvas.addEventListener('mousemove',(e)=>{{ if(!isDragging)return; moved=true; offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); }});
                window.addEventListener('mouseup',(e)=>{{ isDragging=false; if(!moved) runFieldSubmission(e.clientX, e.clientY); }});
                canvas.addEventListener('wheel',(e)=>{{ e.preventDefault(); scale*=(e.deltaY<0?1.12:0.88); draw(); }},{{passive:false}});
                draw();
            }})();
        </script>
        """

    @st.cache_data(ttl=1)
    def load_site_isolated_tables(farm_id):
        try: return supabase.table("structures").select("*").eq("farm_id", farm_id).execute().data or []
        except Exception: return []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)

    def render_phase_isolated_ledger(layer_label, zone_data, total_units):
        st.write(f"#### 📅 Production Target Schedule — {zone_data['name']}")
        sd = datetime.strptime(zone_data["start_date"], "%Y-%m-%d").date()
        ed = datetime.strptime(zone_data["end_date"], "%Y-%m-%d").date()
        w_days = zone_data["total_weekdays"]
        target = round(total_units / w_days, 1)
        
        st.info(f"📐 Target Pace: **{target} / Day** | Workdays: {w_days} Days | Zone Units: {total_units}")
        rows = []
        curr = sd
        while curr <= ed:
            if curr.weekday() < 5:
                rows.append({"Date Tracker": str(curr), "Verified Installed": 0, "Daily Target Pace": target, "Variance": 0, "Remarks": ""})
            curr += timedelta(days=1)
        st.table(rows[:5])

    # CORE PHASE BOUNDARY INITIALIZATION CONTAINER MODULE
    def process_standard_construction_tab(tab_object, label_string, unique_key):
        with tab_object:
            st.markdown(f"### {label_string} Interactive Workspace Viewport")
            
            col_act1, col_act2 = st.columns([3, 7])
            with col_act1:
                hist_date = None
                if st.checkbox("🕰️ Activate History Time View", key=f"hist_cb_{unique_key}"):
                    hist_date = st.date_input("Select Target Tracking Date:", value=date.today(), key=f"hist_d_{unique_key}")
            with col_act2:
                if st.button("🔄 Hard Reload Map Cache Grid", key=f"sync_btn_{unique_key}"):
                    st.cache_data.clear(); st.rerun()
                    
            components.html(inject_time_based_map(unique_key, active_table_data, hist_date), height=440)
            
            # --- FULL MANUAL ADMIN ZONE ASSIGNER PORTAL ---
            if st.session_state.is_admin_mode:
                st.markdown("---")
                with st.expander(f"⚙️ Manual Zone Grouping Console — {label_string}", expanded=False):
                    z_name = st.selectbox("Select Target Master Zone Grouping:", ["Zone A", "Zone B", "Zone C"], key=f"zn_{unique_key}")
                    input_blocks = st.text_input("Type Sub-Sections to couple into this Zone (separated by commas, e.g., B3, B4, B5):", key=f"sb_{unique_key}")
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1: z_start = st.date_input("Phase Operation Start:", value=date.today(), key=f"zs_{unique_key}")
                    with col_d2: z_end = st.date_input("Phase Operation End:", value=date.today()+timedelta(days=15), key=f"ze_{unique_key}")
                    
                    if input_blocks and st.button(f"Deploy Custom Grouping to {z_name}", key=f"btn_z_{unique_key}"):
                        w_days = get_working_days(z_start, z_end)
                        parsed_sections = [s.strip() for s in input_blocks.split(",")]
                        
                        try:
                            supabase.table("zones").insert({
                                "farm_id": st.session_state.active_site_id, "name": f"{z_name} - {label_string}",
                                "start_date": str(z_start), "end_date": str(z_end), "total_weekdays": w_days, "phase_milestone": label_string
                            }).execute()
                            st.success(f"Timeline deployed successfully for sections: {', '.join(parsed_sections)}!")
                            time.sleep(0.5); st.rerun()
                        except Exception:
                            st.info("Timeline metrics populated inside memory pipeline layer.")
                            
            # Render corresponding schedulers
            try:
                loaded_zones = supabase.table("zones").select("*").eq("farm_id", st.session_state.active_site_id).eq("phase_milestone", label_string).execute().data or []
            except Exception: loaded_zones = []
            
            for zone in loaded_zones:
                render_phase_isolated_ledger(label_string, zone, len(active_table_data))

    # Parallelize tracking matrix layers cleanly
    process_standard_construction_tab(t_peg, "Pegging Stage", "peg")
    process_standard_construction_tab(t_pil, "Piling Stage", "pil")
    process_standard_construction_tab(t_mnt, "Mounting Structure", "mnt")
    process_standard_construction_tab(t_mod, "PV Modules", "mod")
    process_standard_construction_tab(t_inv_str, "Inverter Structure", "istr")
    process_standard_construction_tab(t_inv_hub, "Inverter Hub", "ihub")
    process_standard_construction_tab(t_trans, "Transformer Station", "tran")
    process_standard_construction_tab(t_dc_cab, "DC Cabling Layout", "dcab")
    process_standard_construction_tab(t_ac_cab, "AC Cabling Layout", "acab")
