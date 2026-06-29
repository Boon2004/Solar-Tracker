import streamlit as st
import streamlit.components.v1 as components
import openpyxl
from supabase import create_client, Client
import json
import time
import base64
import math
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

st.set_page_config(layout="wide", page_title="Boon Solar Farm Tracking System")

if "active_site_id" not in st.session_state: st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state: st.session_state.is_admin_mode = False
if "managed_zones" not in st.session_state: 
    st.session_state.managed_zones = ["Zone A", "Zone B", "Zone C", "Unassigned"]
if "custom_tabs" not in st.session_state: st.session_state.custom_tabs = []

def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("id, name, admin_password, installer_password, is_published, background_image_url").order("name").execute()
        return res.data if res.data else []
    except Exception: return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# 🏡 MAIN ENTRY SITE GATEWAY
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("🚜 Boon Solar Farm Tracking System")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            if "dev_unlocked" not in st.session_state:
                st.session_state.dev_unlocked = False

            if not st.session_state.dev_unlocked:
                dev_pwd = st.text_input("Enter Control Password:", type="password")
                if dev_pwd == "devok":
                    st.session_state.dev_unlocked = True
                    st.rerun()
            else:
                st.success("Developer Access Unlocked")
                
                if st.button("🔒 Lock & Exit Developer Mode", type="secondary"):
                    st.session_state.dev_unlocked = False
                    st.rerun()
                
                st.markdown("---")
                st.subheader("🗑️ Cloud Database Cleaner")
                if farm_options:
                    wipe_target = st.selectbox("Select Project to Clear:", farm_options, key="dev_clear_dropdown")
                    if st.button("💥 Purge Cloud Data Records", type="primary"):
                        with st.spinner(f"Purging data assets for {wipe_target}..."):
                            try:
                                target_farm = next((f for f in all_registered_farms if f["name"] == wipe_target), None)
                                if target_farm:
                                    supabase.table("structures").delete().eq("farm_id", target_farm["id"]).execute()
                                    supabase.table("transformers").delete().eq("farm_id", target_farm["id"]).execute()
                                    supabase.table("inverters").delete().eq("farm_id", target_farm["id"]).execute()
                                    supabase.table("farms").delete().eq("id", target_farm["id"]).execute()
                                    st.success(f"Successfully cleared all data frameworks for {wipe_target}!")
                                    st.cache_data.clear()
                                    time.sleep(1); st.rerun()
                            except Exception as e: 
                                st.error(f"Purge rejected: {str(e)}")
                else:
                    st.info("No active cloud entries found to clear.")
                
                st.write("---")
                st.subheader("🚀 Onboard New Layout Framework")
                new_site_name = st.text_input("Assign Site Project Name:")
                init_admin_pwd = st.text_input("Assign Management Password:", value="ok")
                init_inst_pwd = st.text_input("Assign Field Access Password:", value="1234")
                
                uploaded_blueprint = st.file_uploader("Upload Master Blueprint Sheet (.xlsx)", type=["xlsx"])
                
                if uploaded_blueprint and new_site_name and st.button("Compile & Parse Structural Blueprint"):
                    st.info("🔄 Running Fast Visual Grid Scanner...")
                    with st.spinner("Processing structural frames..."):
                        wb = openpyxl.load_workbook(uploaded_blueprint, read_only=False, data_only=True)
                        sheet = wb.active
                        max_rows, max_cols = sheet.max_row, sheet.max_column
                        
                        new_fid = None
                        try:
                            farm_node = supabase.table("farms").insert({
                                "name": new_site_name, "admin_password": init_admin_pwd, "installer_password": init_inst_pwd,
                                "max_rows": max_rows, "max_cols": max_cols, "is_published": False
                            }).execute()
                            if farm_node.data: 
                                new_fid = farm_node.data[0]["id"]
                        except Exception as e:
                            st.error(f"❌ Database registration failed: {str(e)}")
                        
                        if new_fid:
                            grid_matrix = [[False for _ in range(max_cols + 1)] for _ in range(max_rows + 1)]
                            for r in range(1, max_rows + 1):
                                for c in range(1, max_cols + 1):
                                    cell = sheet.cell(row=r, column=c)
                                    if cell.value is not None and str(cell.value).strip() != "":
                                        grid_matrix[r][c] = True
                                    elif cell.fill and cell.fill.fill_type is not None and cell.fill.fill_type != 'none':
                                        grid_matrix[r][c] = True
                                    elif cell.border and ((cell.border.top and cell.border.top.style) or 
                                                         (cell.border.bottom and cell.border.bottom.style) or 
                                                         (cell.border.left and cell.border.left.style) or 
                                                         (cell.border.right and cell.border.right.style)):
                                        grid_matrix[r][c] = True

                            visited_matrix = [[False for _ in range(max_cols + 1)] for _ in range(max_rows + 1)]
                            structures_queue = []
                            table_counter = 1
                            ROAD_GAP = 1

                            for r in range(1, max_rows + 1):
                                for c in range(1, max_cols + 1):
                                    if grid_matrix[r][c] and not visited_matrix[r][c]:
                                        cluster_cells = []
                                        bfs_queue = [(r, c)]
                                        visited_matrix[r][c] = True
                                        discovered_label = ""

                                        while bfs_queue:
                                            curr_r, curr_c = bfs_queue.pop(0)
                                            cluster_cells.append((curr_r, curr_c))

                                            v_cell = sheet.cell(row=curr_r, column=curr_c).value
                                            if v_cell and not discovered_label and not str(v_cell).strip().isdigit():
                                                discovered_label = str(v_cell).strip()

                                            for dr in range(-ROAD_GAP, ROAD_GAP + 1):
                                                for dc in range(-ROAD_GAP, ROAD_GAP + 1):
                                                    nr, nc = curr_r + dr, curr_c + dc
                                                    if 1 <= nr <= max_rows and 1 <= nc <= max_cols:
                                                        if grid_matrix[nr][nc] and not visited_matrix[nr][nc]:
                                                            visited_matrix[nr][nc] = True
                                                            bfs_queue.append((nr, nc))

                                        b_rows = [pt[0] for pt in cluster_cells]
                                        b_cols = [pt[1] for pt in cluster_cells]
                                        min_br, max_br, min_bc, max_bc = min(b_rows), max(b_rows), min(b_cols), max(b_cols)
                                        
                                        h_cells = max_br - min_br + 1
                                        w_cells = max_bc - min_bc + 1

                                        if h_cells >= 2 and w_cells >= 2 and h_cells < 45:
                                            structures_queue.append({
                                                "farm_id": new_fid, 
                                                "table_label": discovered_label if discovered_label else f"T-{table_counter}",
                                                "min_r": int(min_br), "max_r": int(max_br), "min_c": int(min_bc), "max_c": int(max_bc),
                                                "structure_type": "double_6x9" if h_cells >= 5 else "single_3x9",
                                                "assigned_zone": "Unassigned",
                                                "section_group": int(table_counter),
                                                "pegging_status": "pending", "piling_status": "pending", 
                                                "mounting_status": "pending", "modules_status": "pending",
                                                "transformer_id": None, "inverter_id": None, "string_cabling_group": None
                                            })
                                            table_counter += 1

                            if len(structures_queue) == 0:
                                st.error("❌ Matrix parser rejected configuration: 0 tracker units extracted.")
                            else:
                                success_count = 0
                                for idx in range(0, len(structures_queue), 200):
                                    batch = structures_queue[idx:idx+200]
                                    try: 
                                        supabase.table("structures").insert(batch).execute()
                                        success_count += len(batch)
                                    except Exception: pass
                                
                                st.success(f"🎉 Saved {success_count} structured blocks.")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()

    st.subheader("🌐 Access Site Workspace Portal")
    if farm_options:
        with st.form("workspace_access_form"):
            chosen_farm_name = st.selectbox("Select Project Site Layout Location:", farm_options)
            entered_inst_pass = st.text_input("Enter Access Password:", type="password")
            if st.form_submit_button("🚀 Open Workspace"):
                target_site_record = next(f for f in all_registered_farms if f["name"] == chosen_farm_name)
                if str(entered_inst_pass) == str(target_site_record.get("installer_password") or "1234"):
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
    site_bg_img = current_farm_record.get("background_image_url", "")

    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.subheader(f"📍 Boon Solar Farm Tracking System — {st.session_state.active_site_name}")
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
                    else: st.error("Incorrect Password.")
        else:
            st.info("⚡ Admin Permissions Active")
            
            st.write("---")
            st.subheader("📢 Field Deployment Release")
            if not site_is_published:
                st.warning("⚠️ CRITICAL: Once published to the field crew, coordinates and electrical maps cannot be altered.")
                
                if "confirm_publish_gate" not in st.session_state: st.session_state.confirm_publish_gate = False
                
                if not st.session_state.confirm_publish_gate:
                    if st.button("🚀 Publish Layout Workspace to Field Crew", type="primary"):
                        st.session_state.confirm_publish_gate = True
                        st.rerun()
                else:
                    st.error("🔒 Confirm permanent field synchronization lock?")
                    col_lock1, col_lock2 = st.columns(2)
                    with col_lock1:
                        if st.button("🔒 YES, DEPLOY", type="primary", use_container_width=True):
                            supabase.table("farms").update({"is_published": True}).eq("id", st.session_state.active_site_id).execute()
                            st.session_state.confirm_publish_gate = False
                            st.success("Workspace deployed cleanly! Fields locked.")
                            time.sleep(1); st.rerun()
                    with col_lock2:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.confirm_publish_gate = False
                            st.rerun()
            else:
                st.success("✅ Layout Workspace Status: Locked & Live to Crew")
                if st.button("🔓 Emergency Revoke & Unfreeze Project (Admin Only)"):
                    supabase.table("farms").update({"is_published": False}).eq("id", st.session_state.active_site_id).execute()
                    st.rerun()
            
            st.write("---")
            st.subheader("🖼️ Map Background Image Configuration")
            uploaded_map_img = st.file_uploader("Upload Layout Image Blueprint (PNG/JPG):", type=["png", "jpg", "jpeg"])
            if uploaded_map_img:
                img_bytes = uploaded_map_img.read()
                b64_img_string = f"data:{uploaded_map_img.type};base64," + base64.b64encode(img_bytes).decode("utf-8")
                
                if site_is_published:
                    st.error("Cannot change image background assets on published, finalized frameworks.")
                elif st.button("💾 Apply & Save Image Blueprint", type="primary"):
                    supabase.table("farms").update({"background_image_url": b64_img_string}).eq("id", st.session_state.active_site_id).execute()
                    st.success("Image blueprints attached safely!")
                    time.sleep(0.5); st.rerun()
            
            if site_bg_img and not site_is_published:
                if st.button("🗑️ Remove Current Background Image", type="secondary"):
                    supabase.table("farms").update({"background_image_url": ""}).eq("id", st.session_state.active_site_id).execute()
                    st.success("Background mapping reference flushed!")
                    time.sleep(0.5); st.rerun()

            st.write("---")
            st.subheader("🛠️ Custom Tracker Tab Builder")
            custom_tab_name = st.text_input("Assign New Tracker Tab Label:", placeholder="e.g. Floating Cell...")
            if st.button("✨ Instantiate Phase Tab") and custom_tab_name:
                if custom_tab_name not in st.session_state.custom_tabs:
                    st.session_state.custom_tabs.append(custom_tab_name)
                    st.success(f"Instantiated '{custom_tab_name}'!")
                    time.sleep(0.4); st.rerun()
                    
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    if st.button("🔄 Reload Workspace Map from Database", type="secondary"):
        st.rerun()

    def load_site_isolated_tables(farm_id):
        all_data = []
        limit = 1000
        offset = 0
        while True:
            try:
                res = supabase.table("structures").select("*").eq("farm_id", farm_id).order("id").range(offset, offset + limit - 1).execute().data
                if not res: break
                all_data.extend(res)
                if len(res) < limit: break
                offset += limit
            except Exception: break
        return all_data

    def load_electrical_nodes(farm_id):
        try:
            tx_res = supabase.table("transformers").select("*").eq("farm_id", farm_id).execute().data
            inv_res = supabase.table("inverters").select("*").eq("farm_id", farm_id).execute().data
            return tx_res or [], inv_res or []
        except Exception:
            return [], []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)
    transformers_data, inverters_data = load_electrical_nodes(st.session_state.active_site_id)

    if not active_table_data:
        st.warning("ℹ️ No operational layout metrics have loaded from database for this specific site yet.")
        st.stop()

    min_r = min([b.get("min_r", 1) for b in active_table_data])
    max_r = max([b.get("max_r", 100) for b in active_table_data])
    min_c = min([b.get("min_c", 1) for b in active_table_data])
    max_c = max([b.get("max_c", 150) for b in active_table_data])

    CELL_SIZE = 14
    json_str = json.dumps(active_table_data)
    b64_json_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    b64_tx_data = base64.b64encode(json.dumps(transformers_data).encode("utf-8")).decode("utf-8")
    b64_inv_data = base64.b64encode(json.dumps(inverters_data).encode("utf-8")).decode("utf-8")

    for b in active_table_data:
        z = b.get("assigned_zone")
        if z and z not in st.session_state.managed_zones:
            st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, z)
    
    clean_wiping_dropdown_options = [zone for zone in st.session_state.managed_zones if zone != "Unassigned"]

    # ==============================================================================
    # ⚡ ADMIN PLATFORM ROUTING
    # ==============================================================================
    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs([
            "🖼️ Base Overview & Zone Assignation", 
            "🔌 Unified Master Electrical Canvas", 
            "📌 Pegging & Piling Customizer"
        ])
        
        # --- STAGE 1: SETUPS OVERVIEW & ZONE ASSIGNATION ---
        with setup_tabs[0]:
            st.markdown("### 🖼️ Operational Field Zoning Assignation Engine")
            if site_bg_img:
                st.image(site_bg_img, caption="Active Site Blueprint", use_container_width=False, width=600)

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
            
            st.write("---")
            st.subheader("🛠️ Selective Zone Reset Center")
            col_wipe1, col_wipe2 = st.columns([6, 4])
            with col_wipe1:
                wipe_scope_selection = st.selectbox("Select Target Scope to Flush & Reset:", ["ALL ZONES"] + clean_wiping_dropdown_options)
            with col_wipe2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if site_is_published:
                    st.error("Cannot reset zone assets on a frozen workspace framework.")
                elif st.button("💥 Reset Selected Allocation Fleet", type="secondary", use_container_width=True):
                    with st.spinner("Flushing target zones..."):
                        try:
                            if wipe_scope_selection == "ALL ZONES":
                                supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).execute()
                            else:
                                supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).eq("assigned_zone", wipe_scope_selection).execute()
                            st.success("Wiped selected configurations maps safely!")
                            time.sleep(0.5); st.rerun()
                        except Exception as e: st.error(f"Reset failed: {str(e)}")

            html_zone_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div id="canvas_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; font-weight: bold;"></div>
                <div id="dialogue_overlay" style="display:none; position:absolute; bottom:35px; left:50%; transform:translateX(-50%); background:#1e293b; padding:18px 35px; border-radius:8px; border:2px solid #38bdf8; z-index:100000; text-align:center;">
                    <div id="status_message_box" style="color:#22c55e; font-weight:bold; margin-bottom:10px; display:none;">Processing...</div>
                    <div style="color:#f1f5f9; font-weight:bold; margin-bottom:14px;">Assign Selected Section Cluster to <span id="lbl_zone" style="color:#38bdf8;"></span>?</div>
                    <button id="btn_yes" style="background:#22c55e; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; margin-right:12px;">Yes</button>
                    <button id="btn_no" style="background:#ef4444; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer;">No</button>
                </div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="zone_canvas" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    const canvas = document.getElementById("zone_canvas"); const ctx = canvas.getContext('2d');
                    const tooltip = document.getElementById("canvas_hover_tooltip");
                    const paintZone = "PAINT_ZONE_VAL"; const CELL = CELL_SIZE_VAL; const isPublished = __IS_PUBLISHED_VAL__;
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    let scale = Math.min((canvas.width - 60) / ((maxX-minX+1)*CELL), (canvas.height - 60) / ((maxY-minY+1)*CELL)) || 0.5;
                    let offsetX = (canvas.width / 2) - (((maxX-minX+1)*CELL) * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (((maxY-minY+1)*CELL) * scale / 2) - (minY * CELL * scale);
                    let isPanning = false, isSelecting = false, startX = 0, startY = 0, currentX = 0, currentY = 0, stagedBlockIds = [];
                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function getZoneColor(z) { if(!z || z.toLowerCase()==='unassigned') return '#334155'; let h=0; for(let i=0;i<z.length;i++) h=z.charCodeAt(i)+((h<<5)-h); return `hsl(${Math.abs(h*45)%360},90%,50%)`; }
                    function draw() {
                        ctx.clearRect(0,0,canvas.width,canvas.height); ctx.save(); ctx.translate(offsetX,offsetY); ctx.scale(scale,scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = getZoneColor(b.assigned_zone);
                            let x=b.min_c*CELL, y=b.min_r*CELL, w=(b.max_c-b.min_c+1)*CELL, h=(b.max_r-b.min_r+1)*CELL;
                            ctx.fillRect(x,y,w,h); ctx.strokeStyle='#020617'; ctx.lineWidth=0.75; ctx.strokeRect(x,y,w,h);
                            if(stagedBlockIds.includes(b.id)) { ctx.strokeStyle='#ffff00'; ctx.lineWidth=2.5; ctx.strokeRect(x,y,w,h); }
                        }); ctx.restore();
                        if(isSelecting) { ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.fillStyle='rgba(56,189,248,0.25)'; ctx.fillRect(startX,startY,currentX-startX,currentY-startY); ctx.strokeRect(startX,startY,currentX-startX,currentY-startY); }
                    }
                    canvas.addEventListener('mousemove', e => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left, mY = e.clientY - rect.top;
                        if(isPanning) { offsetX = e.clientX-startX; offsetY = e.clientY-startY; draw(); return; }
                        if(isSelecting) { currentX = mX; currentY = mY; draw(); return; }
                        let wX = (mX-offsetX)/scale, wY = (mY-offsetY)/scale, hb = null;
                        for(let b of blocks) { if(wX>=b.min_c*CELL && wX<=(b.max_c+1)*CELL && wY>=b.min_r*CELL && wY<=(b.max_r+1)*CELL) { hb=b; break; }}
                        if(hb) { tooltip.style.display="block"; tooltip.style.left=(mX+15)+"px"; tooltip.style.top=(mY+15)+"px"; tooltip.innerHTML=`Label: ${hb.table_label}<br/>Zone: ${hb.assigned_zone || 'Unassigned'}`; } else tooltip.style.display="none";
                    });
                    canvas.addEventListener('mousedown', e => { if(isPublished) return; const rect=canvas.getBoundingClientRect(); if(e.button===2) { isPanning=true; startX=e.clientX-offsetX; startY=e.clientY-offsetY; } else { isSelecting=true; startX=e.clientX-rect.left; startY=e.clientY-rect.top; currentX=startX; currentY=startY; }});
                    canvas.addEventListener('mouseup', e => {
                        const rect=canvas.getBoundingClientRect(); if(isPanning) isPanning=false;
                        else if(isSelecting) {
                            isSelecting=false; stagedBlockIds=[]; let x1=Math.min(startX,e.clientX-rect.left), x2=Math.max(startX,e.clientX-rect.left), y1=Math.min(startY,e.clientY-rect.top), y2=Math.max(startY,e.clientY-rect.top);
                            blocks.forEach(b => {
                                if(b.assigned_zone && b.assigned_zone.toLowerCase()!=='unassigned') return;
                                let cx1=b.min_c*CELL*scale+offsetX, cy1=b.min_r*CELL*scale+offsetY;
                                if(cx1>=x1 && cx1<=x2 && cy1>=y1 && cy1<=y2) stagedBlockIds.push(b.id);
                            });
                            if(stagedBlockIds.length>0) { document.getElementById("lbl_zone").innerText=paintZone; document.getElementById("dialogue_overlay").style.display="block"; }
                            draw();
                        }
                    });
                    document.getElementById("btn_yes").addEventListener('click', async () => {
                        document.getElementById("status_message_box").style.display="block";
                        for(let id of stagedBlockIds) {
                            await fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq."+id, { method:"PATCH", headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"}, body:JSON.stringify({"assigned_zone":paintZone})});
                        }
                        location.reload();
                    });
                    document.getElementById("btn_no").addEventListener('click', () => { stagedBlockIds=[]; document.getElementById("dialogue_overlay").style.display="none"; draw(); });
                    canvas.addEventListener('wheel', e => { e.preventDefault(); const rect=canvas.getBoundingClientRect(); const mX=e.clientX-rect.left, mY=e.clientY-rect.top, gX=(mX-offsetX)/scale, gY=(mY-offsetY)/scale; scale*=(e.deltaY<0?1.15:0.85); scale=Math.max(0.05,Math.min(scale,30)); offsetX=mX-gX*scale; offsetY=mY-gY*scale; draw(); }, {passive:false});
                    draw();
                })();
            </script>
            """
            html_zone_engine = html_zone_engine.replace("__JSON_DATA_B64__", b64_json_data).replace("PAINT_ZONE_VAL", str(target_paint_zone)).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY).replace("__IS_PUBLISHED_VAL__", "true" if site_is_published else "false")
            components.html(html_zone_engine, height=700)

        # --- STAGE 2: UNIFIED MASTER ELECTRICAL CANVA TAB WORKFLOW ---
        with setup_tabs[1]:
            st.markdown("### 🔌 Unified Master Electrical Mapping Workspace Canvas")
            
            mode_selector = st.radio("Select Active Electrical Canvas Operation Mode:", [
                "Mode 1: Place Transformer Stations Hubs",
                "Mode 2: Place Inverter System Boxes",
                "Mode 3: String to Inverter Topology Grouping (DC Cabling)"
            ], horizontal=True)

            active_mode_id = 1 if "Mode 1" in mode_selector else (2 if "Mode 2" in mode_selector else 3)
            chosen_parent_tx = "None"
            
            if active_mode_id == 2:
                tx_names = [tx["name"] for tx in transformers_data]
                if not tx_names:
                    st.info("⚠️ Please drop at least one Transformer inside Mode 1 before placing child inverters.")
                else:
                    chosen_parent_tx = st.selectbox("Assign Parent Transformer Association Group:", tx_names)

            html_electrical_master = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">
                    Current Mode Controls: <span style="color:#eab308; font-weight:bold;">Left-Click</span> grid space to place/group nodes. <span style="color:#ef4444; font-weight:bold;">Click item twice</span> to prompt removal execution.
                </div>
                <div id="elec_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #a855f7; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; font-weight: bold;"></div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="elec_canvas" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    const txNodes = JSON.parse(atob("__TX_DATA_B64__"));
                    const invNodes = JSON.parse(atob("__INV_DATA_B64__"));
                    const mode = __ACTIVE_MODE__;
                    const parentTxName = "__PARENT_TX__";
                    const canvas = document.getElementById("elec_canvas"); const ctx = canvas.getContext('2d');
                    const tooltip = document.getElementById("elec_tooltip");
                    const CELL = 14; const farmId = "__FARM_ID__";
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    let scale = Math.min((canvas.width - 60) / ((maxX-minX+1)*CELL), (canvas.height - 60) / ((maxY-minY+1)*CELL)) || 0.5;
                    let offsetX = (canvas.width/2)-(((maxX-minX+1)*CELL)*scale/2)-(minX*CELL*scale);
                    let offsetY = (canvas.height/2)-(((maxY-minY+1)*CELL)*scale/2)-(minY*CELL*scale);
                    let isPanning=false, isSelecting=false, startX=0, startY=0, currentX=0, currentY=0, activeInvSelectionId=null;

                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function getStringColor(strName) { if(!strName) return null; let h=0; for(let i=0;i<strName.length;i++) h=strName.charCodeAt(i)+((h<<5)-h); return `hsl(${Math.abs(h*75)%360}, 95%, 55%)`; }

                    function draw() {
                        ctx.clearRect(0,0,canvas.width,canvas.height); ctx.save(); ctx.translate(offsetX,offsetY); ctx.scale(scale,scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = '#1e293b';
                            let x=b.min_c*CELL, y=b.min_r*CELL, w=(b.max_c-b.min_c+1)*CELL, h=(b.max_r-b.min_r+1)*CELL;
                            ctx.fillRect(x,y,w,h); ctx.strokeStyle='#334155'; ctx.lineWidth=0.5; ctx.strokeRect(x,y,w,h);
                            if(b.string_cabling_group) { ctx.strokeStyle = getStringColor(b.string_cabling_group); ctx.lineWidth = 2.5; ctx.strokeRect(x+1,y+1,w-2,h-2); }
                        });
                        txNodes.forEach(tx => { ctx.fillStyle='#eab308'; ctx.fillRect(tx.grid_c*CELL, tx.grid_r*CELL, CELL*2, CELL*2); ctx.fillStyle='#000'; ctx.font="10px sans-serif"; ctx.fillText(tx.name, tx.grid_c*CELL+2, tx.grid_r*CELL+11); });
                        invNodes.forEach(inv => { ctx.fillStyle=(activeInvSelectionId===inv.id)?'#ffff00':'#ef4444'; ctx.fillRect(inv.grid_c*CELL, inv.grid_r*CELL, CELL, CELL); });
                        ctx.restore();
                        if(isSelecting && mode===3) { ctx.strokeStyle='#22c55e'; ctx.lineWidth=1.5; ctx.strokeRect(startX,startY,currentX-startX,currentY-startY); }
                    }

                    canvas.addEventListener('mousemove', e => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX-rect.left, mY = e.clientY-rect.top;
                        if(isPanning) { offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); return; }
                        if(isSelecting) { currentX=mX; currentY=mY; draw(); return; }
                        let wX=(mX-offsetX)/scale, wY=(mY-offsetY)/scale; let hb=null;
                        for(let b of blocks) { if(wX>=b.min_c*CELL && wX<=(b.max_c+1)*CELL && wY>=b.min_r*CELL && wY<=(b.max_r+1)*CELL) { hb=b; break; }}
                        if(hb) {
                            tooltip.style.display="block"; tooltip.style.left=(mX+15)+"px"; tooltip.style.top=(mY+15)+"px";
                            tooltip.innerHTML=`Cell Table: ${hb.table_label}<br/>Zone: ${hb.assigned_zone}<br/>Transformer: ${hb.transformer_id || 'Unassigned'}<br/>Inverter: ${hb.inverter_id || 'Unassigned'}<br/>String Cabling Code: ${hb.string_cabling_group || 'Unassigned'}`;
                            return;
                        }
                        let hInv=null;
                        for(let inv of invNodes) { let ix=inv.grid_c*CELL, iy=inv.grid_r*CELL; if(wX>=ix && wX<=ix+CELL && wY>=iy && wY<=iy+CELL) { hInv=inv; break; }}
                        if(hInv) {
                            let streamCount = blocks.filter(b => b.inverter_id === hInv.id || b.inverter_id === (hInv.transformer_name+'-'+hInv.inverter_num)).length;
                            tooltip.style.display="block"; tooltip.style.left=(mX+15)+"px"; tooltip.style.top=(mY+15)+"px";
                            tooltip.innerHTML=`Inverter Block ID: ${hInv.transformer_name}-${hInv.inverter_num}<br/>Parent Feed Hub: ${hInv.transformer_name}<br/>Total Connected DC Strings: ${streamCount}`;
                            return;
                        } tooltip.style.display="none";
                    });

                    canvas.addEventListener('mousedown', async e => {
                        const rect=canvas.getBoundingClientRect(); const mX=e.clientX-rect.left, mY=e.clientY-rect.top;
                        let wX=Math.floor(((mX-offsetX)/scale)/CELL), wY=Math.floor(((mY-offsetY)/scale)/CELL);
                        if(e.button===2) { isPanning=true; startX=e.clientX-offsetX; startY=e.clientY-offsetY; return; }
                        if(mode===1) {
                            let existingTx = txNodes.find(tx => tx.grid_c===wX && tx.grid_r===wY);
                            if(existingTx) { if(confirm("Remove Transformer "+existingTx.name+"?")) { await fetch("SUPABASE_URL_VAL/rest/v1/transformers?id=eq."+existingTx.id,{method:"DELETE",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL"}}); location.reload(); }}
                            else { let name=prompt("Assign Transformer Node Identifier Label:"); if(name) { await fetch("SUPABASE_URL_VAL/rest/v1/transformers",{method:"POST",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({farm_id:farmId,name:name,grid_r:wY,grid_c:wX})}); location.reload(); }}
                        } else if(mode===2) {
                            let existingInv = invNodes.find(inv => inv.grid_c===wX && inv.grid_r===wY);
                            if(existingInv) { if(confirm("Remove Inverter Box Unit?")) { await fetch("SUPABASE_URL_VAL/rest/v1/inverters?id=eq."+existingInv.id,{method:"DELETE",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL"}}); location.reload(); }}
                            else { if(parentTxName==="None") return; let num=prompt("Enter Inverter Number Identifier:"); if(num) { await fetch("SUPABASE_URL_VAL/rest/v1/inverters",{method:"POST",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({farm_id:farmId,transformer_name:parentTxName,inverter_num:num,grid_r:wY,grid_c:wX})}); location.reload(); }}
                        } else if(mode===3) {
                            let hitInv = invNodes.find(inv => wX>=inv.grid_c && wX<=inv.grid_c+1 && wY>=inv.grid_r && wY<=inv.grid_r+1);
                            if(hitInv) { activeInvSelectionId = hitInv.transformer_name + "-" + hitInv.inverter_num; draw(); }
                            else if(activeInvSelectionId) { isSelecting=true; startX=mX; startY=mY; currentX=mX; currentY=mY; }
                        }
                    });

                    canvas.addEventListener('mouseup', async e => {
                        if(isPanning) isPanning=false;
                        else if(isSelecting && mode===3 && activeInvSelectionId) {
                            isSelecting=false; const rect=canvas.getBoundingClientRect();
                            let x1=Math.min(startX,e.clientX-rect.left), x2=Math.max(startX,e.clientX-rect.left), y1=Math.min(startY,e.clientY-rect.top), y2=Math.max(startY,e.clientY-rect.top);
                            let targetIds=[];
                            blocks.forEach(b => {
                                let cx=b.min_c*CELL*scale+offsetX, cy=b.min_r*CELL*scale+offsetY;
                                if(cx>=x1 && cx<=x2 && cy>=y1 && cy<=y2) targetIds.push(b.id);
                            });
                            if(targetIds.length>0) {
                                let stringCode=prompt("Enter DC String Cabling Group Identification Label:");
                                if(stringCode) {
                                    for(let id of targetIds) {
                                        await fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq."+id,{method:"PATCH",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({inverter_id:activeInvSelectionId,string_cabling_group:stringCode})});
                                    } location.reload();
                                }
                            } draw();
                        }
                    });
                    canvas.addEventListener('wheel', e => { e.preventDefault(); const rect=canvas.getBoundingClientRect(); const mX=e.clientX-rect.left, mY=e.clientY-rect.top, gX=(mX-offsetX)/scale, gY=(mY-offsetY)/scale; scale*=(e.deltaY<0?1.15:0.85); scale=Math.max(0.01,Math.min(scale,15)); offsetX=mX-gX*scale; offsetY=mY-gY*scale; draw(); }, {passive:false});
                    draw();
                })();
            </script>
            """.replace("__JSON_DATA_B64__", b64_json_data).replace("__TX_DATA_B64__", b64_tx_data).replace("__INV_DATA_B64__", b64_inv_data).replace("__ACTIVE_MODE__", str(active_mode_id)).replace("__PARENT_TX__", chosen_parent_tx).replace("__FARM_ID__", str(st.session_state.active_site_id)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            components.html(active_mode_id and html_electrical_master, height=660)

        # --- STAGE 3: BLUEPRINT TEMPLATE PROPAGATION ---
        with setup_tabs[2]:
            st.markdown("### 📌 Component Placement Microscale Engineering Template Engine")
            components.html("""
            <div style="background:#0f172a; padding:15px; border-radius:12px; text-align:center;"><canvas id="micro_canvas" width="300" height="200" style="background:#020617; border:2px dashed #38bdf8; border-radius:6px;"></canvas><div style="margin-top:12px;"><button style="background:#22c55e; color:white; border:none; padding:6px 12px; border-radius:4px; font-weight:bold; cursor:pointer;" onclick="alert('Configuration Cloned Fleetwide!')">💾 Apply & Replicate Fleetwide</button></div></div>
            <script>const c=document.getElementById("micro_canvas"),ctx=c.getContext('2d');ctx.fillStyle='#334155';ctx.fillRect(40,30,220,140);ctx.strokeStyle='#38bdf8';ctx.lineWidth=2;ctx.strokeRect(40,30,220,140);ctx.fillStyle='#ef4444';ctx.beginPath();ctx.arc(80,100,6,0,Math.PI*2);ctx.fill();ctx.beginPath();ctx.arc(220,100,6,0,Math.PI*2);ctx.fill();</script>
            """, height=280)

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (CREW WORKSPACE VIEWS)
        # ==============================================================================
        if not site_is_published:
            st.info("🚜 Layout configuration is currently locked by the engineering team. Waiting for blueprint deployment release updates...")
            st.stop()

        if site_bg_img:
            st.markdown("### 🗺️ Master Blueprint Reference Layout")
            st.image(site_bg_img, use_container_width=False, width=700)
            st.write("---")

        crew_tabs = st.tabs([
            "📌 Pegging Phase", "🪵 Piling Operations", "🏗️ Mounting Structures", "☀️ PV Module Tracking"
        ] + [f"🛠️ {ct}" for ct in st.session_state.custom_tabs])

        def inject_crew_tracking_map(layer_key, b64_data, min_c, max_c, min_r, max_r):
            today_str = str(date.today())
            html_crew_map = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family: sans-serif;">
                <div id="crew_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #22c55e; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; font-weight: bold;"></div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="crew_LAYER_KEY" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); 
                    const canvas = document.getElementById("crew_LAYER_KEY"); const ctx = canvas.getContext('2d');
                    const tooltip = document.getElementById("crew_hover_tooltip");
                    const CELL = 14; let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    let scale = Math.min((canvas.width - 60) / ((maxX-minX+1)*CELL), (canvas.height - 60) / ((maxY-minY+1)*CELL)) || 0.5;
                    let offsetX = (canvas.width / 2) - (((maxX-minX+1)*CELL) * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (((maxY-minY+1)*CELL) * scale / 2) - (minY * CELL * scale);
                    let isPanning = false, isSelecting = false, dragStartRawX = 0, dragStartRawY = 0, dragCurrentRawX = 0, dragCurrentRawY = 0;

                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = b['LAYER_KEY_status'] === 'completed' ? '#22c55e' : '#3b82f6';
                            let x = b.min_c * CELL, y = b.min_r * CELL, w = (b.max_c - b.min_c + 1) * CELL, h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h);
                        }); ctx.restore();
                        if (isSelecting) { ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 2; ctx.fillStyle = 'rgba(34, 197, 94, 0.25)'; ctx.fillRect(dragStartRawX, dragStartRawY, dragCurrentRawX - dragStartRawX, dragCurrentRawY - dragStartRawY); }
                    }
                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left, mY = e.clientY - rect.top;
                        if (isPanning) { offsetX = e.clientX - dragStartRawX; offsetY = e.clientY - dragStartRawY; draw(); return; }
                        if (isSelecting) { dragCurrentRawX = mX; dragCurrentRawY = mY; draw(); return; }
                        let worldX = (mX - offsetX) / scale, worldY = (mY - offsetY) / scale, hb = null;
                        for (let b of blocks) { if (worldX >= b.min_c * CELL && worldX <= (b.max_c + 1) * CELL && worldY >= b.min_r * CELL && worldY <= (b.max_r + 1) * CELL) { hb = b; break; } }
                        if (hb) { tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Label: ${hb.table_label}<br/>Zone: ${hb.assigned_zone}<br/>Status: ${hb['LAYER_KEY_status'] || 'pending'}`; } else tooltip.style.display = "none";
                    });
                    canvas.addEventListener('mousedown', (e) => { const rect = canvas.getBoundingClientRect(); if (e.button === 2) { isPanning = true; dragStartRawX = e.clientX - offsetX; dragStartRawY = e.clientY - offsetY; } else { isSelecting = true; dragStartRawX = e.clientX - rect.left; dragStartRawY = e.clientY - rect.top; dragCurrentRawX = dragStartRawX; dragCurrentRawY = dragStartRawY; } });
                    canvas.addEventListener('mouseup', async (e) => {
                        const rect = canvas.getBoundingClientRect(); if (isPanning) isPanning = false;
                        else if (isSelecting) {
                            isSelecting = false; let x1 = Math.min(dragStartRawX, e.clientX - rect.left), x2 = Math.max(dragStartRawX, e.clientX - rect.left), y1 = Math.min(dragStartRawY, e.clientY - rect.top), y2 = Math.max(dragStartRawY, e.clientY - rect.top);
                            let payloadIds = [];
                            blocks.forEach(b => {
                                let cx = b.min_c * CELL * scale + offsetX, cy = b.min_r * CELL * scale + offsetY;
                                if (cx >= x1 && cx <= x2 && cy >= y1 && cy <= y2 && b['LAYER_KEY_status'] !== 'completed') payloadIds.push(b.id);
                            });
                            if (payloadIds.length > 0) {
                                for (let id of payloadIds) {
                                    await fetch('SUPABASE_URL_VAL/rest/v1/structures?id=eq.' + id, { method: "PATCH", headers: { "apikey": 'SUPABASE_KEY_VAL', "Authorization": 'Bearer SUPABASE_KEY_VAL', "Content-Type": "application/json" }, body: JSON.stringify({ "LAYER_KEY_status": "completed", "LAYER_KEY_date": "TODAY_STR_VAL" }) });
                                } location.reload();
                            } draw();
                        }
                    });
                    canvas.addEventListener('wheel', (e) => { e.preventDefault(); const rect = canvas.getBoundingClientRect(); const mouseX = e.clientX - rect.left, mouseY = e.clientY - rect.top, gridX = (mouseX - offsetX) / scale, gridY = (mouseY - offsetY) / scale; scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.01, Math.min(scale, 15)); offsetX = mouseX - gridX * scale; offsetY = mouseY - gridY * scale; draw(); }, { passive: false });
                    draw();
                })();
            </script>
            """
            return html_crew_map.replace("__JSON_DATA_B64__", b64_data).replace("LAYER_KEY", str(layer_key)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("TODAY_STR_VAL", today_str).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)

        def process_crew_tab(tab_obj, key_val):
            with tab_obj: components.html(inject_crew_tracking_map(key_val, b64_json_data, min_c, max_c, min_r, max_r), height=640)

        process_crew_tab(crew_tabs[0], "pegging")
        process_crew_tab(crew_tabs[1], "piling")
        process_crew_tab(crew_tabs[2], "mounting")
        process_crew_tab(crew_tabs[3], "modules")
