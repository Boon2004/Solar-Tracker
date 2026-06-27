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

def get_working_days(start_d, end_d):
    days = 0
    curr = start_d
    while curr <= end_d:
        if curr.weekday() < 5: days += 1
        curr += timedelta(days=1)
    return max(days, 1)

if "active_site_id" not in st.session_state: st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state: st.session_state.is_admin_mode = False

# Fresh Cloud Fetching Engine
@st.cache_data(ttl=1)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception: return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# 🏡 MAIN PORTAL SCREEN
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("🚜 Boon Solar Farm Tracking System")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            dev_pwd = st.text_input("Enter Developer Password:", type="password")
            if dev_pwd == "devok":
                st.success("Developer Access Unlocked")
                
                # --- AUTOMATIC DYNAMIC DROPDOWN WIPEOUT TOOL ---
                st.subheader("🗑️ Cloud Database Cleaner")
                if farm_options:
                    wipe_target = st.selectbox("Select Cloud Project to Clear:", farm_options, key="dev_clear_dropdown")
                    if st.button("💥 Force Clear Cloud Database Records", type="primary"):
                        with st.spinner(f"Purging data assets for {wipe_target}..."):
                            try:
                                supabase.table("farms").delete().eq("name", wipe_target).execute()
                                st.success(f"Successfully purged all cloud data for {wipe_target}!")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Purge request rejected: {str(e)}")
                else:
                    st.info("No active cloud entries found to clear.")
                
                st.write("---")
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
                        
                        new_fid = None
                        try:
                            farm_node = supabase.table("farms").insert({
                                "name": new_site_name, "admin_password": init_admin_pwd, "installer_password": init_inst_pwd
                            }).execute()
                            if farm_node.data: new_fid = farm_node.data[0]["id"]
                        except Exception:
                            try:
                                farm_node = supabase.table("farms").insert({"name": new_site_name}).execute()
                                if farm_node.data: new_fid = farm_node.data[0]["id"]
                            except Exception:
                                pass
                        
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
                                        
                                        structures_queue.append({
                                            "farm_id": new_fid, "table_label": f"T-{table_counter}",
                                            "min_r": int(min_br), "max_r": int(max_br), "min_c": int(min_bc), "max_c": int(max_bc),
                                            "structure_type": "double_6x9" if (max_br - min_br + 1) >= 6 else "single_3x9",
                                            "assigned_zone": "Unassigned"
                                        })
                                        table_counter += 1
                            
                            for idx in range(0, len(structures_queue), 50):
                                try: supabase.table("structures").insert(structures_queue[idx:idx+50]).execute()
                                except Exception: pass
                                time.sleep(0.04)
                                
                            st.success("Layout arrays updated perfectly!")
                            st.cache_data.clear(); st.rerun()
                        else:
                            st.error("Submission failed. Select this project name in the dropdown cleaner list above, clear it first, then re-upload.")

    # NATIVE FORM LOGIN GATEWAY
    st.subheader("🌐 Access Site Workspace Portal")
    if farm_options:
        with st.form("workspace_access_form", clear_on_submit=False):
            chosen_farm_name = st.selectbox("Select Active Project Location Site:", farm_options)
            entered_inst_pass = st.text_input("Enter Field Installer Password:", type="password")
            submit_login = st.form_submit_button("🚀 Open Digital Twin Workspace")
            
            if submit_login:
                target_site_record = next(f for f in all_registered_farms if f["name"] == chosen_farm_name)
                expected_pass = target_site_record.get("installer_password") or target_site_record.get("site_password") or "1234"
                if str(entered_inst_pass) == str(expected_pass):
                    st.session_state.active_site_id = target_site_record["id"]
                    st.session_state.active_site_name = target_site_record["name"]
                    st.session_state.admin_key_match = target_site_record.get("admin_password") or "ok"
                    st.rerun()
                else: st.error("Invalid credentials entered.")
    else: st.info("No active installations found. Open Left Developer Panel to upload blueprint grid arrays.")

# ==============================================================================
# 🗂️ PHASE 2: INTERNAL OPERATIONS TRACKING COMMAND CENTER
# ==============================================================================
else:
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.subheader(f"📍 Boon Solar Farm Tracking System — {st.session_state.active_site_name}")
    with col_h2:
        if st.button("🚪 Exit Site"): st.session_state.active_site_id = None; st.session_state.is_admin_mode = False; st.rerun()
            
    with st.sidebar:
        st.header("🔐 Workspace Clearances")
        if not st.session_state.is_admin_mode:
            with st.form("admin_upgrade_form", clear_on_submit=True):
                st.write("Elevate Workspace Rights")
                adm_pass = st.text_input("Upgrade to Admin Mode:", type="password")
                submit_admin = st.form_submit_button("Verify Admin Status")
                
                if submit_admin:
                    if str(adm_pass) == str(st.session_state.admin_key_match):
                        st.session_state.is_admin_mode = True; st.success("Admin Elevation Granted"); st.rerun()
                    else: st.error("Incorrect Password.")
        else:
            st.info("⚡ Admin Permissions Active")
            uploaded_png = st.file_uploader("Upload Overview Picture (.png / .jpg)", type=["png", "jpg", "jpeg"])
            if uploaded_png and st.button("💾 Save Uploaded Image to Site"):
                bytes_data = uploaded_png.getvalue()
                base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                supabase.table("farms").update({"overview_image_url": f"data:image/png;base64,{base64_encoded}"}).eq("id", st.session_state.active_site_id).execute()
                st.success("Overview picture saved!"); time.sleep(0.5); st.rerun()
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    current_farm_record = supabase.table("farms").select("*").eq("id", st.session_state.active_site_id).execute().data[0]
    
    t_over, t_peg, t_pil, t_mnt, t_mod, t_inv_str, t_inv_hub, t_trans, t_dc_cab, t_ac_cab = st.tabs([
        "🖼️ Overview", "📌 Pegging", "🪵 Piling", "🏗️ Mounting Structure", "☀️ PV Modules", 
        "🏗️ Inverter Structure", "⚡ Inverter Hub", "🏪 Transformer Station", "🔌 DC Cabling", "⚡ AC Cabling"
    ])

    @st.cache_data(ttl=1)
    def load_site_isolated_tables(farm_id):
        try: return supabase.table("structures").select("*").eq("farm_id", farm_id).execute().data or []
        except Exception: return []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)

    with t_over:
        st.markdown("### 🖼️ Master Site Overview Infrastructure")
        img_src = current_farm_record.get("overview_image_url")
        if img_src: st.image(img_src, caption="Active Farm Layout", use_column_width=True)
        else: st.warning("No custom overview picture uploaded yet.")

        if st.session_state.is_admin_mode:
            st.markdown("---")
            target_paint_zone = st.selectbox("Active Painter Palette Target Zone:", ["Zone A", "Zone B", "Zone C", "Unassigned"])
            
            json_str = json.dumps(active_table_data)
            html_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px;">
                <canvas id="zone_painter" width="1500" height="420" style="background:#020617; border-radius:8px; width:100%; cursor:crosshair;"></canvas>
            </div>
            <script>
                (function() {
                    const blocks = """ + json_str + """;
                    const canvas = document.getElementById("zone_painter");
                    const ctx = canvas.getContext('2d');
                    const paintZone = '""" + target_paint_zone + """';
                    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                    blocks.forEach(b => {
                        if (b.min_c < minX) minX = b.min_c; if (b.max_c > maxX) maxX = b.max_c;
                        if (b.min_r < minY) minY = b.min_r; if (b.max_r > maxY) maxY = b.max_r;
                    });
                    const gw = (maxX - minX) || 1, gh = (maxY - minY) || 1;
                    const colMultiplier = 1.8; const rowMultiplier = 45.0;
                    let scale = Math.min((canvas.width-80)/(gw*colMultiplier), (canvas.height-80)/(gh*rowMultiplier));
                    let offsetX = (canvas.width/2)-((gw*colMultiplier*scale)/2)-(minX*colMultiplier*scale);
                    let offsetY = (canvas.height/2)-((gh*rowMultiplier*scale)/2)-(minY*rowMultiplier*scale);
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            let az = b.assigned_zone || "Unassigned";
                            if (az === 'Zone A') ctx.fillStyle = '#ff4b4b'; else if (az === 'Zone B') ctx.fillStyle = '#00f0ff'; else if (az === 'Zone C') ctx.fillStyle = '#eab308'; else ctx.fillStyle = '#334155';
                            ctx.fillRect(b.min_c * colMultiplier, b.min_r * rowMultiplier, (b.max_c-b.min_c+1)*colMultiplier-0.4, (b.max_r-b.min_r+1)*rowMultiplier-2.0);
                        });
                        ctx.restore();
                    }
                    canvas.addEventListener('click', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const cx = (e.clientX - rect.left - offsetX) / scale / colMultiplier;
                        const cy = (e.clientY - rect.top - offsetY) / scale / rowMultiplier;
                        blocks.forEach(b => {
                            if (cx >= b.min_c && cx <= b.max_c + 1 && cy >= b.min_r && cy <= b.max_r + 1) {
                                b.assigned_zone = paintZone; draw();
                                fetch('""" + SUPABASE_URL + """/rest/v1/structures?id=eq.' + b.id, {
                                    method: "PATCH", headers: { "apikey": '""" + SUPABASE_KEY + """', "Authorization": 'Bearer """ + SUPABASE_KEY + """', "Content-Type": "application/json" },
                                    body: JSON.stringify({ "assigned_zone": paintZone })
                                });
                            }
                        });
                    });
                    draw();
                })();
            </script>
            """
            components.html(html_engine, height=450)

    def inject_time_based_map(layer_key, data_array, selected_history_date=None):
        json_points = json.dumps(data_array)
        today_str = str(date.today())
        history_target = str(selected_history_date) if selected_history_date else "null"
        return """
        <div style="background:#090d16; padding:12px; border-radius:12px; touch-action:none;">
            <canvas id="cv_""" + layer_key + """" width="1500" height="420" style="background:#020617; border-radius:8px; width:100%; cursor:grab; touch-action:none;"></canvas>
        </div>
        <script>
            (function() {
                const blocks = """ + json_points + """;
                const canvas = document.getElementById("cv_""" + layer_key + """");
                const ctx = canvas.getContext('2d');
                const todayVal = '""" + today_str + """';
                const historyDate = '""" + history_target + """' !== "null" ? '""" + history_target + """' : null;
                const layerKey = '""" + layer_key + """';
                let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                blocks.forEach(b => {
                    if (b.min_c < minX) minX = b.min_c; if (b.max_c > maxX) maxX = b.max_c;
                    if (b.min_r < minY) minY = b.min_r; if (b.max_r > maxY) maxY = b.max_r;
                });
                const gw = (maxX - minX) || 1, gh = (maxY - minY) || 1;
                const colMultiplier = 1.8; const rowMultiplier = 45.0;
                let scale = Math.min((canvas.width-80)/(gw*colMultiplier), (canvas.height-80)/(gh*rowMultiplier));
                if(scale<0.001||scale===Infinity) scale=0.3;
                let offsetX = (canvas.width/2)-((gw*colMultiplier*scale)/2)-(minX*colMultiplier*scale);
                let offsetY = (canvas.height/2)-((gh*rowMultiplier*scale)/2)-(minY*rowMultiplier*scale);
                let isDragging = false, moved = false, startX, startY;
                function draw() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                    blocks.forEach(b => {
                        let dCol = "pegging_date", sCol = "pegging_status";
                        if(layerKey === "pil") { dCol="piling_date"; sCol="piling_status"; }
                        else if(layerKey === "mnt") { dCol="mounting_date"; sCol="mounting_status"; }
                        else if(layerKey === "mod") { dCol="modules_date"; sCol="modules_status"; }
                        else if(layerKey === "istr") { dCol="inv_str_date"; sCol="mounting_status"; }
                        else if(layerKey === "ihub") { dCol="inv_hub_date"; sCol="mounting_status"; }
                        else if(layerKey === "tran") { dCol="trans_date"; sCol="mounting_status"; }
                        else if(layerKey === "dcab") { dCol="dc_cab_date"; sCol="cabling_status"; }
                        else if(layerKey === "acab") { dCol="ac_cab_date"; sCol="cabling_status"; }
                        let isDone = b[sCol] === 'completed';
                        ctx.fillStyle = '#2563eb'; 
                        if (isDone) {
                            if (historyDate) {
                                if (b[dCol] === historyDate) ctx.fillStyle = '#eab308'; 
                                else if (b[dCol] < historyDate) ctx.fillStyle = '#22c55e'; 
                            } else {
                                if (b[dCol] === todayVal) ctx.fillStyle = '#eab308'; else ctx.fillStyle = '#22c55e'; 
                            }
                        }
                        ctx.fillRect(b.min_c * colMultiplier, b.min_r * rowMultiplier, (b.max_c-b.min_c+1)*colMultiplier-0.4, (b.max_r-b.min_r+1)*rowMultiplier-2.0);
                    });
                    ctx.restore();
                }
                function runFieldSubmission(clientX, clientY) {
                    if(historyDate) return; 
                    const rect = canvas.getBoundingClientRect();
                    const cx = (clientX - rect.left - offsetX) / scale / colMultiplier;
                    const cy = (clientY - rect.top - offsetY) / scale / rowMultiplier;
                    blocks.forEach(b => {
                        if (cx >= b.min_c && cx <= b.max_c + 1 && cy >= b.min_r && cy <= b.max_r + 1) {
                            let targetCol = "pegging_status", dateCol = "pegging_date";
                            if(layerKey === "pil") { targetCol="piling_status"; dateCol="piling_date"; }
                            else if(layerKey === "mnt") { targetCol="mounting_status"; dateCol="mounting_date"; }
                            else if(layerKey === "mod") { targetCol="modules_status"; dateCol="modules_date"; }
                            else if(layerKey === "istr") { targetCol="mounting_status"; dateCol="inv_str_date"; }
                            else if(layerKey === "ihub") { targetCol="mounting_status"; dateCol="inv_hub_date"; }
                            else if(layerKey === "tran") { targetCol="mounting_status"; dateCol="trans_date"; }
                            else if(layerKey === "dcab") { targetCol="cabling_status"; dateCol="dc_cab_date"; }
                            else if(layerKey === "acab") { targetCol="cabling_status"; dateCol="ac_cab_date"; }
                            const payload = {}; payload[targetCol] = "completed"; payload[dateCol] = todayVal;
                            fetch('""" + SUPABASE_URL + """/rest/v1/structures?id=eq.' + b.id, {
                                method: "PATCH", headers: { "apikey": '""" + SUPABASE_KEY + """', "Authorization": 'Bearer """ + SUPABASE_KEY + """', "Content-Type": "application/json", "Prefer": "return=minimal" },
                                body: JSON.stringify(payload)
                            }).then(() => { b[targetCol] = "completed"; b[dateCol] = todayVal; draw(); });
                        }
                    });
                }
                canvas.addEventListener('mousedown',(e)=>{ isDragging=true; moved=false; startX=e.clientX-offsetX; startY=e.clientY-offsetY; });
                canvas.addEventListener('mousemove',(e)=>{ if(!isDragging)return; moved=true; offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); });
                window.addEventListener('mouseup',(e)=>{ isDragging=false; if(!moved) runFieldSubmission(e.clientX, e.clientY); });
                canvas.addEventListener('wheel',(e)=>{ e.preventDefault(); scale*=(e.deltaY<0?1.12:0.88); draw(); },{passive:false});
                draw();
            })();
        </script>
        """

    def process_standard_construction_tab(tab_object, label_string, unique_key):
        with tab_object:
            st.markdown(f"### {label_string} Workspace Viewport")
            col_act1, col_act2 = st.columns([3, 7])
            with col_act1:
                hist_date = None
                if st.checkbox("🕰️ Activate History Time View", key=f"hist_cb_{unique_key}"):
                    hist_date = st.date_input("Select Target Tracking Date:", value=date.today(), key=f"hist_d_{unique_key}")
            with col_act2:
                if st.button("🔄 Hard Reset Map Layout Caches", key=f"sync_btn_{unique_key}"): st.cache_data.clear(); st.rerun()
            components.html(inject_time_based_map(unique_key, active_table_data, hist_date), height=440)

    process_standard_construction_tab(t_peg, "Pegging Stage", "peg")
    process_standard_construction_tab(t_pil, "Piling Stage", "pil")
    process_standard_construction_tab(t_mnt, "Mounting Structure", "mnt")
    process_standard_construction_tab(t_mod, "PV Modules", "mod")
    process_standard_construction_tab(t_inv_str, "Inverter Structure", "istr")
    process_standard_construction_tab(t_inv_hub, "Inverter Hub", "ihub")
    process_standard_construction_tab(t_trans, "Transformer Station", "tran")
    process_standard_construction_tab(t_dc_cab, "DC Cabling Layout", "dcab")
    process_standard_construction_tab(t_ac_cab, "AC Cabling Layout", "acab")
