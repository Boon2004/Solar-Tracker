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

@st.cache_data(ttl=1)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception: return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# HOME NAVIGATION PORTAL
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("🚜 Boon Solar Farm Tracking System")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            dev_pwd = st.text_input("Enter Developer Password:", type="password")
            if dev_pwd == "devok":
                st.success("Developer Access Unlocked")
                new_site_name = st.text_input("Assign Site Project Name:")
                init_admin_pwd = st.text_input("Assign Admin Password:", value="ok")
                init_inst_pwd = st.text_input("Assign Installer Password:", value="1234")
                uploaded_blueprint = st.file_uploader("Upload Grid Sheet (.xlsx)", type=["xlsx"])
                
                if uploaded_blueprint and new_site_name and st.button("Compile Structural Layout Grid"):
                    with st.spinner("Parsing grid boundary layouts..."):
                        wb = openpyxl.load_workbook(uploaded_blueprint, data_only=True)
                        sheet = wb.active
                        max_rows, max_cols = sheet.max_row, sheet.max_column
                        
                        try: supabase.table("farms").delete().eq("name", new_site_name).execute()
                        except Exception: pass
                        
                        new_fid = None
                        try:
                            farm_node = supabase.table("farms").insert({"name": new_site_name, "admin_password": init_admin_pwd, "installer_password": init_inst_pwd}).execute()
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
                                        
                                        structures_queue.append({
                                            "farm_id": new_fid, "table_label": f"T-{table_counter}",
                                            "min_r": int(min_br), "max_r": int(max_br), "min_c": int(min_bc), "max_c": int(max_bc),
                                            "structure_type": "double_6x9" if (max_br - min_br + 1) >= 6 else "single_3x9",
                                            "assigned_zone": "Unassigned"
                                        })
                                        table_counter += 1
                            
                            for idx in range(0, len(structures_queue), 50):
                                supabase.table("structures").insert(structures_queue[idx:idx+50]).execute()
                                time.sleep(0.04)
                            st.success("Worskpace deployed successfully!")
                            st.cache_data.clear(); st.rerun()

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
            else: st.error("Invalid credentials.")
else:
    # ==============================================================================
    # INTERNAL FARM WORKSPACE INTERFACE
    # ==============================================================================
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.subheader(f"📍 Boon Solar Farm Tracking System — {st.session_state.active_site_name}")
    with col_h2: 
        if st.button("🚪 Exit Site"): st.session_state.active_site_id = None; st.session_state.is_admin_mode = False; st.rerun()
            
    with st.sidebar:
        st.header("🔐 Workspace Clearances")
        if not st.session_state.is_admin_mode:
            adm_pass = st.text_input("Upgrade to Admin Mode:", type="password")
            if st.button("Verify Admin Status"):
                if str(adm_pass) == str(st.session_state.admin_key_match):
                    st.session_state.is_admin_mode = True; st.success("Admin Access Granted"); st.rerun()
                else: st.error("Incorrect Password.")
        else:
            st.info("⚡ Admin Permissions Active")
            uploaded_png = st.file_uploader("Upload Overview Layout Image (.png / .jpg)", type=["png", "jpg", "jpeg"])
            if uploaded_png and st.button("💾 Save Background Image to Dashboard"):
                bytes_data = uploaded_png.getvalue()
                base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                supabase.table("farms").update({"overview_image_url": f"data:image/png;base64,{base64_encoded}"}).eq("id", st.session_state.active_site_id).execute()
                st.success("Background image configured successfully!"); time.sleep(0.5); st.rerun()
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    current_farm_record = supabase.table("farms").select("*").eq("id", st.session_state.active_site_id).execute().data[0]
    
    @st.cache_data(ttl=1)
    def load_site_isolated_tables(farm_id):
        try: return supabase.table("structures").select("*").eq("farm_id", farm_id).execute().data or []
        except Exception: return []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)

    t_over, t_peg, t_pil, t_mnt, t_mod, t_inv_str, t_inv_hub, t_trans, t_dc_cab, t_ac_cab = st.tabs([
        "🖼️ Overview", "📌 Pegging", "🪵 Piling", "🏗️ Mounting Structure", "☀️ PV Modules", 
        "🏗️ Inverter Structure", "⚡ Inverter Hub", "🏪 Transformer Station", "🔌 DC Cabling", "⚡ AC Cabling"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: OVERVIEW & MANUAL VISUAL ZONE COUPLING ASSIGNER
    # --------------------------------------------------------------------------
    with t_over:
        st.markdown("### 🖼️ Master Layout Boundary & Zone Planner Engine")
        
        if st.session_state.is_admin_mode:
            st.info("🎨 **Admin Visual Painter Mode Active:** Select a destination target zone from the dropdown menu below, then click cleanly onto individual blueprint blocks on the interactive layout map grid to assign them directly!")
            target_paint_zone = st.selectbox("Active Painter Palette Target Zone:", ["Zone A", "Zone B", "Zone C", "Unassigned"])
            
            # Master Interactive Zone Selection Matrix JavaScript Canvas Code
            json_str = json.dumps(active_table_data)
            html_engine = f"""
            <div style="background:#090d16; padding:12px; border-radius:12px;">
                <canvas id="zone_painter" width="1500" height="420" style="background:#020617; border-radius:8px; width:100%; cursor:crosshair;"></canvas>
            </div>
            <script>
                (function() {{
                    const blocks = {json_str};
                    const canvas = document.getElementById("zone_painter");
                    const ctx = canvas.getContext('2d');
                    const paintZone = "{target_paint_zone}";
                    
                    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                    blocks.forEach(b => {{
                        if (b.min_c < minX) minX = b.min_c; if (b.max_c > maxX) maxX = b.max_c;
                        if (b.min_r < minY) minY = b.min_r; if (b.max_r > maxY) maxY = b.max_r;
                    }});
                    const gw = (maxX - minX) || 1, gh = (maxY - minY) || 1;
                    const colMultiplier = 1.8; const rowMultiplier = 45.0;
                    let scale = Math.min((canvas.width-80)/(gw*colMultiplier), (canvas.height-80)/(gh*rowMultiplier));
                    let offsetX = (canvas.width/2)-((gw*colMultiplier*scale)/2)-(minX*colMultiplier*scale);
                    let offsetY = (canvas.height/2)-((gh*rowMultiplier*scale)/2)-(minY*rowMultiplier*scale);
                    
                    function draw() {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {{
                            if (b.assigned_zone === 'Zone A') ctx.fillStyle = '#ff4b4b';      // Red for Zone A
                            else if (b.assigned_zone === 'Zone B') ctx.fillStyle = '#00f0ff'; // Cyan for Zone B
                            else if (b.assigned_zone === 'Zone C') ctx.fillStyle = '#eab308'; // Yellow for Zone C
                            else ctx.fillStyle = '#334155';                                   // Muted slate gray for unassigned
                            
                            const x = b.min_c * colMultiplier; const y = b.min_r * rowMultiplier;
                            ctx.fillRect(x, y, (b.max_c-b.min_c+1)*colMultiplier-0.4, (b.max_r-b.min_r+1)*rowMultiplier-2.0);
                            ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.1; ctx.strokeRect(x, y, (b.max_c-b.min_c+1)*colMultiplier, (b.max_r-b.min_r+1)*rowMultiplier);
                        }});
                        ctx.restore();
                    }}
                    
                    canvas.addEventListener('click', (e) => {{
                        const rect = canvas.getBoundingClientRect();
                        const cx = (e.clientX - rect.left - offsetX) / scale / colMultiplier;
                        const cy = (e.clientY - rect.top - offsetY) / scale / rowMultiplier;
                        
                        blocks.forEach(b => {{
                            if (cx >= b.min_c && cx <= b.max_c + 1 && cy >= b.min_r && cy <= b.max_r + 1) {{
                                b.assigned_zone = paintZone; draw();
                                fetch("{SUPABASE_URL}/rest/v1/structures?id=eq." + b.id, {{
                                    method: "PATCH",
                                    headers: {{ "apikey": "{SUPABASE_KEY}", "Authorization": "Bearer {SUPABASE_KEY}", "Content-Type": "application/json" }},
                                    body: JSON.stringify({{ "assigned_zone": paintZone }})
                                }});
                            }}
                        }});
                    }});
                    draw();
                }})();
            </script>
            """
            components.html(html_engine, height=450)
        else:
            img_src = current_farm_record.get("overview_image_url")
            if img_src: st.image(img_src, caption="Active Farm Blueprint", use_column_width=True)
            else: st.warning("No overview picture uploaded by the administrator yet.")

    # --------------------------------------------------------------------------
    # SEQUENTIAL MILESTONE TAB RENDERING PIPELINE WITH ZONE FILTERING
    # --------------------------------------------------------------------------
    def inject_construction_map(layer_key, data_array, selected_history_date=None):
        json_points = json.dumps(data_array)
        today_str = str(date.today())
        history_target = str(selected_history_date) if selected_history_date else "null"
        
        return f"""
        <div style="background:#090d16; padding:12px; border-radius:12px;">
            <canvas id="cv_{layer_key}" width="1500" height="420" style="background:#020617; border-radius:8px; width:100%;"></canvas>
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
                let offsetX = (canvas.width/2)-((gw*colMultiplier*scale)/2)-(minX*colMultiplier*scale);
                let offsetY = (canvas.height/2)-((gh*rowMultiplier*scale)/2)-(minY*rowMultiplier*scale);
                
                function draw() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                    blocks.forEach(b => {{
                        let dCol = "pegging_date", sCol = "pegging_status";
                        if("{layer_key}" === "pil") {{ dCol="piling_date"; sCol="piling_status"; }}
                        else if("{layer_key}" === "mnt") {{ dCol="mounting_date"; sCol="mounting_status"; }}
                        else if("{layer_key}" === "mod") {{ dCol="modules_date"; sCol="modules_status"; }}
                        
                        let recordDate = b[dCol];
                        let isDone = b[sCol] === 'completed';
                        
                        ctx.fillStyle = '#2563eb'; // Blue - Pending
                        if (isDone) {{
                            if (historyDate) {{
                                if (recordDate === historyDate) ctx.fillStyle = '#eab308'; // Yellow built that specific day
                                else if (recordDate < historyDate) ctx.fillStyle = '#22c55e'; // Green built previously
                                else ctx.fillStyle = '#2563eb';
                            }} else {{
                                if (recordDate === todayVal) ctx.fillStyle = '#eab308'; // Yellow today
                                else ctx.fillStyle = '#22c55e'; // Green past
                            }}
                        }}
                        const x = b.min_c * colMultiplier; const y = b.min_r * rowMultiplier;
                        ctx.fillRect(x, y, (b.max_c-b.min_c+1)*colMultiplier-0.4, (b.max_r-b.min_r+1)*rowMultiplier-2.0);
                        ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.12; ctx.strokeRect(x, y, (b.max_c-b.min_c+1)*colMultiplier, (b.max_r-b.min_r+1)*rowMultiplier);
                    }});
                    ctx.restore();
                }}
                
                canvas.addEventListener('click', (e) => {{
                    if(historyDate) return;
                    const rect = canvas.getBoundingClientRect();
                    const cx = (e.clientX - rect.left - offsetX) / scale / colMultiplier;
                    const cy = (e.clientY - rect.top - offsetY) / scale / rowMultiplier;
                    blocks.forEach(b => {{
                        if (cx >= b.min_c && cx <= b.max_c + 1 && cy >= b.min_r && cy <= b.max_r + 1) {{
                            let targetCol = "pegging_status", dateCol = "pegging_date";
                            if("{layer_key}" === "pil") {{ targetCol="piling_status"; dateCol="piling_date"; }}
                            else if("{layer_key}" === "mnt") {{ targetCol="mounting_status"; dateCol="mounting_date"; }}
                            else if("{layer_key}" === "mod") {{ targetCol="modules_status"; dateCol="modules_date"; }}
                            
                            const payload = {{}}; payload[targetCol] = "completed"; payload[dateCol] = todayVal;
                            fetch("{SUPABASE_URL}/rest/v1/structures?id=eq." + b.id, {{
                                method: "PATCH",
                                headers: {{ "apikey": "{SUPABASE_KEY}", "Authorization": "Bearer {SUPABASE_KEY}", "Content-Type": "application/json" }},
                                body: JSON.stringify(payload)
                            }}).then(() => {{ b[targetCol] = "completed"; b[dateCol] = todayVal; draw(); }});
                        }}
                    }});
                }});
                draw();
            }})();
        </script>
        """

    def render_milestone_tab_layout(tab_obj, label_str, unique_key):
        with tab_obj:
            st.markdown(f"### {label_str} Viewport")
            
            # History Query Mode Engine Integration
            hist_date = None
            if st.checkbox("🕰️ Review History Records", key=f"cb_h_{unique_key}"):
                hist_date = st.date_input("Target Date:", value=date.today(), key=f"d_h_{unique_key}")
                
            components.html(inject_construction_map(unique_key, active_table_data, hist_date), height=440)
            
            # Tab-localized timeline scheduler configurator
            if st.session_state.is_admin_mode:
                st.markdown("---")
                with st.expander(f"⚙️ Target Scheduling Parameters — {label_str}", expanded=False):
                    z_target = st.selectbox("Link Timeline To:", ["Zone A", "Zone B", "Zone C"], key=f"zsel_{unique_key}")
                    col_s1, col_s2 = st.columns(2)
                    with col_s1: s_d = st.date_input("Start Date:", value=date.today(), key=f"sd_{unique_key}")
                    with col_s2: e_d = st.date_input("End Date:", value=date.today()+timedelta(days=14), key=f"ed_{unique_key}")
                    
                    if st.button("Deploy Schedule", key=f"btn_{unique_key}"):
                        w_days = get_working_days(s_d, e_d)
                        supabase.table("zones").insert({"farm_id": st.session_state.active_site_id, "name": f"{z_target} - {label_str}", "start_date": str(s_d), "end_date": str(e_d), "total_weekdays": w_days, "phase_milestone": label_str}).execute()
                        st.success("Target timeline logged!"); time.sleep(0.5); st.rerun()

            # Render calculations for active grouped tables
            try: loaded_zones = supabase.table("zones").select("*").eq("farm_id", st.session_state.active_site_id).eq("phase_milestone", label_str).execute().data or []
            except Exception: loaded_zones = []
            
            for zone in loaded_zones:
                zone_tag = zone['name'].split(" - ")[0] # Extracts 'Zone A', etc.
                tables_in_zone = len([b for b in active_table_data if b.get('assigned_zone') == zone_tag])
                
                st.write(f"#### 📅 Production Target Schedule — {zone_tag}")
                st.info(f"📐 Available Workdays: {zone['total_weekdays']} Weekdays | Total Zone Units: {tables_in_zone} Tables | Target: **{round(tables_in_zone/zone['total_weekdays'], 1)} / Day**")

    # Generate the sequential layouts cleanly
    render_milestone_tab_layout(t_peg, "Pegging Stage", "peg")
    render_milestone_tab_layout(t_pil, "Piling Stage", "pil")
    render_milestone_tab_layout(t_mnt, "Mounting Structure", "mnt")
    render_milestone_tab_layout(t_mod, "PV Modules", "mod")
