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
                        # FIXED: Changed from use_iterators=False to read_only=False
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
                st.warning("⚠️ CRITICAL: Review zoning allocations, electrical maps, structural placement settings, and cabling routes carefully. Once published to the field crew, coordinates cannot be altered.")
                
                if "confirm_publish_gate" not in st.session_state: st.session_state.confirm_publish_gate = False
                
                if not st.session_state.confirm_publish_gate:
                    if st.button("🚀 Publish Layout Workspace to Field Crew", type="primary"):
                        st.session_state.confirm_publish_gate = True
                        st.rerun()
                else:
                    st.error("❗ ARE YOU ABSOLUTELY SURE? This lock is permanent.")
                    col_lock1, col_lock2 = st.columns(2)
                    with col_lock1:
                        if st.button("🔒 YES, FREEZE & DEPLOY", type="primary", use_container_width=True):
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

    def load_electrical_nodes(table_name, farm_id):
        try:
            res = supabase.table(table_name).select("*").eq("farm_id", farm_id).execute()
            return res.data if res.data else []
        except Exception: return []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)
    transformers_data = load_electrical_nodes("transformers", st.session_state.active_site_id)
    inverters_data = load_electrical_nodes("inverters", st.session_state.active_site_id)

    min_r = min([b.get("min_r", 1) for b in active_table_data]) if active_table_data else 1
    max_r = max([b.get("max_r", 100) for b in active_table_data]) if active_table_data else 100
    min_c = min([b.get("min_c", 1) for b in active_table_data]) if active_table_data else 1
    max_c = max([b.get("max_c", 150) for b in active_table_data]) if active_table_data else 150

    CELL_SIZE = 14
    json_str = json.dumps(active_table_data)
    b64_json_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    
    b64_transformers = base64.b64encode(json.dumps(transformers_data).encode("utf-8")).decode("utf-8")
    b64_inverters = base64.b64encode(json.dumps(inverters_data).encode("utf-8")).decode("utf-8")

    for b in active_table_data:
        z = b.get("assigned_zone")
        if z and z not in st.session_state.managed_zones:
            st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, z)
            
    zone_list_for_wiping = sorted(list(set([b["assigned_zone"] for b in active_table_data if b.get("assigned_zone")])))
    if "Unassigned" in zone_list_for_wiping: zone_list_for_wiping.remove("Unassigned")
    inverter_list_for_wiping = sorted(list(set([b["inverter_id"] for b in active_table_data if b.get("inverter_id")])))

    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs([
            "🖼️ Base Overview & Zone Assignation", 
            "🔌 Electrical Infrastructure Workspace", 
            "📌 Pegging & Piling Customizer",
            "🏪 Master Blueprint Configuration Overview Nodes"
        ])
        
        # --- STAGE 1: SETUPS OVERVIEW & ZONE ASSIGNATION ---
        with setup_tabs[0]:
            st.markdown("### 🖼️ Operational Field Zoning Assignation Engine")
            if site_bg_img: st.image(site_bg_img, width=600)

            col_z1, col_z2 = st.columns([6, 4])
            with col_z1:
                target_paint_zone = st.selectbox("Active Target Zone Selector:", st.session_state.managed_zones, index=0)
            with col_z2:
                new_zone_opt = st.text_input("➕ Register New managed Zone String:", placeholder="e.g. Zone D...")
                if st.button("Register Variant Entry") and new_zone_opt:
                    clean_opt = new_zone_opt.strip()
                    if clean_opt not in st.session_state.managed_zones:
                        st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, clean_opt)
                        st.rerun()
            
            st.write("---")
            st.subheader("🛠️ Selective Zone Reset Center")
            col_wipe1, col_wipe2 = st.columns([6, 4])
            with col_wipe1:
                wipe_scope_selection = st.selectbox("Select Target Scope to Flush:", ["ALL ZONES"] + zone_list_for_wiping)
            with col_wipe2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if site_is_published: st.error("Framework locked.")
                elif st.button("💥 Reset Selected Allocation Fleet", type="secondary", use_container_width=True):
                    if wipe_scope_selection == "ALL ZONES":
                        supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).execute()
                    else:
                        supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).eq("assigned_zone", wipe_scope_selection).execute()
                    st.rerun()

            html_zone_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div id="canvas_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-weight: bold;"></div>
                <div id="dialogue_overlay" style="display:none; position:absolute; bottom:35px; left:50%; transform:translateX(-50%); background:#1e293b; padding:18px 35px; border-radius:8px; border:2px solid #38bdf8; z-index:100000; box-shadow: 0 10px 40px rgba(0,0,0,0.85); text-align:center;">
                    <div id="status_message_box" style="color:#22c55e; font-weight:bold; margin-bottom:10px; display:none;">Processing updates...</div>
                    <div style="color:#f1f5f9; font-weight:bold; margin-bottom:14px; font-size:15px;">Assign Selected Section Cluster to <span id="lbl_zone" style="color:#38bdf8; text-decoration:underline;"></span>?</div>
                    <button id="btn_yes" style="background:#22c55e; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; margin-right:12px; font-size:14px;">Yes, Stage Change</button>
                    <button id="btn_no" style="background:#ef4444; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:14px;">No</button>
                </div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="zone_canvas" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); const canvas = document.getElementById("zone_canvas"); const ctx = canvas.getContext('2d'); const tooltip = document.getElementById("canvas_hover_tooltip"); const paintZone = "PAINT_ZONE_VAL"; const CELL = CELL_SIZE_VAL; const isPublished = __IS_PUBLISHED_VAL__;
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL; const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;
                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight); if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale); let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isPanning = false, isSelecting = false, startX = 0, startY = 0, currentX = 0, currentY = 0, stagedBlockIds = [];
                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function getZoneColor(zoneName) {
                        if (!zoneName || zoneName.toLowerCase() === 'unassigned' || zoneName.trim() === '') return '#334155';
                        let hash = 0; let cleaned = zoneName.toUpperCase().trim(); for (let i = 0; i < cleaned.length; i++) { hash = cleaned.charCodeAt(i) + ((hash << 5) - hash); }
                        return `hsl(${Math.abs(hash * 45) % 360}, 90%, 50%)`;
                    }
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            let isStaged = stagedBlockIds.includes(b.id); ctx.fillStyle = getZoneColor(b.assigned_zone);
                            let x = b.min_c * CELL; let y = b.min_r * CELL; let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#020617'; ctx.lineWidth = 0.75; ctx.strokeRect(x, y, w, h);
                            if (isStaged) { ctx.strokeStyle = '#ffff00'; ctx.lineWidth = 2.5; ctx.strokeRect(x, y, w, h); }
                        }); ctx.restore();
                        if (isSelecting) { ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2; ctx.fillStyle = 'rgba(56, 189, 248, 0.25)'; ctx.fillRect(startX, startY, currentX - startX, currentY - startY); }
                    }
                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left; const mY = e.clientY - rect.top;
                        if (isPanning) { offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); tooltip.style.display = "none"; return; }
                        else if (isSelecting) { currentX = mX; currentY = mY; draw(); tooltip.style.display = "none"; return; }
                        let worldX = (mX - offsetX) / scale; let worldY = (mY - offsetY) / scale; let hoveredBlock = null;
                        for (let b of blocks) {
                            let x = b.min_c * CELL; let y = b.min_r * CELL; let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            if (worldX >= x && worldX <= x + w && worldY >= y && worldY <= y + h) { hoveredBlock = b; break; }
                        }
                        if (hoveredBlock) { tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Label: ${hoveredBlock.table_label}<br/>Zone: ${hoveredBlock.assigned_zone || 'Unassigned'}`; }
                        else { tooltip.style.display = "none"; }
                    });
                    canvas.addEventListener('mousedown', (e) => {
                        if (isPublished) return; const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left; const mY = e.clientY - rect.top;
                        if (e.button === 2) { isPanning = true; isSelecting = false; startX = e.clientX - offsetX; startY = e.clientY - offsetY; }
                        else if (e.button === 0) { isSelecting = true; isPanning = false; startX = mX; startY = mY; currentX = mX; currentY = mY; canvas.style.cursor = 'crosshair'; }
                        tooltip.style.display = "none";
                    });
                    canvas.addEventListener('mouseup', (e) => {
                        const rect = canvas.getBoundingClientRect(); const endX = e.clientX - rect.left; const endY = e.clientY - rect.top;
                        if (isPanning) { isPanning = false; canvas.style.cursor = 'grab'; }
                        else if (isSelecting) {
                            isSelecting = false; canvas.style.cursor = 'default'; stagedBlockIds = [];
                            let boxX1 = Math.min(startX, currentX), boxX2 = Math.max(startX, currentX); let boxY1 = Math.min(startY, currentY), boxY2 = Math.max(startY, currentY);
                            blocks.forEach(b => {
                                if (b.assigned_zone && b.assigned_zone.toLowerCase() !== 'unassigned') return;
                                let cellX = b.min_c * CELL * scale + offsetX; let cellY = b.min_r * CELL * scale + offsetY;
                                if (cellX >= boxX1 && cellX <= boxX2 && cellY >= boxY1 && cellY <= boxY2) stagedBlockIds.push(b.id);
                            });
                            if (stagedBlockIds.length > 0) { document.getElementById("lbl_zone").innerText = paintZone; document.getElementById("dialogue_overlay").style.display = "block"; }
                            draw();
                        }
                    });
                    document.getElementById("btn_yes").addEventListener('click', async () => {
                        const msgBox = document.getElementById("status_message_box"); msgBox.style.display = "block";
                        for (let id of stagedBlockIds) {
                            let target = blocks.find(b => b.id === id); if (target) target.assigned_zone = paintZone;
                            await fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq." + id, {
                                method: "PATCH", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json", "Prefer": "return=minimal" },
                                body: JSON.stringify({ "assigned_zone": paintZone })
                            });
                        }
                        msgBox.innerText = "Saved!"; setTimeout(() => { msgBox.style.display = "none"; }, 1000);
                        stagedBlockIds = []; document.getElementById("dialogue_overlay").style.display = "none"; draw();
                    });
                    document.getElementById("btn_no").addEventListener('click', () => { stagedBlockIds = []; document.getElementById("dialogue_overlay").style.display = "none"; draw(); });
                })();
            </script>
            """
            html_zone_engine = html_zone_engine.replace("__JSON_DATA_B64__", b64_json_data).replace("PAINT_ZONE_VAL", str(target_paint_zone)).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY).replace("__IS_PUBLISHED_VAL__", "true" if site_is_published else "false")
            components.html(html_zone_engine, height=700)

        # --- STAGE 2: UNIFIED ELECTRICAL INFRASTRUCTURE WORKSPACE ---
        with setup_tabs[1]:
            st.markdown("### 🔌 Unified Electrical Infrastructure Setup Module")
            
            col_mode, col_inputs = st.columns([3, 7])
            with col_mode:
                active_elec_mode = st.radio("Select Operational Mapping State:", [
                    "1. Drop Transformer Stations",
                    "2. Place Inverter Boxes",
                    "3. Cable DC String Grouping"
                ])
            with col_inputs:
                if "1." in active_elec_mode:
                    ts_prefix = st.text_input("New Transformer Tag Label Name:", value="TS1", placeholder="e.g. TS1, TS2...")
                elif "2." in active_elec_mode:
                    inv_parent_ts = st.selectbox("Assign Downstream to Parent Transformer:", ["Select Master Hub"] + [t["name"] for t in transformers_data])
                    inv_num_val = st.text_input("Assign Inverter Block Number:", value="INV01", placeholder="e.g. INV01...")
                else:
                    active_string_lbl = st.text_input("Enter String Wiring Code Identifier:", value="STR-A1", placeholder="e.g. STR-A1...")

            st.subheader("🗑️ Selective Electrical Node Reset Center")
            col_el_w1, col_el_w2 = st.columns([6, 4])
            with col_el_w1:
                elec_reset_scope = st.selectbox("Select Target Active Inverter Fleet to Wipe out:", ["ALL CABLING GROUPS"] + inverter_list_for_wiping)
            with col_el_w2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if site_is_published: st.error("Canceled: Locked framework.")
                elif st.button("💥 Reset Selected Infrastructure Layout Data", type="secondary", use_container_width=True):
                    with st.spinner("Wiping rows..."):
                        if elec_reset_scope == "ALL CABLING GROUPS":
                            supabase.table("structures").update({"transformer_id": None, "inverter_id": None, "string_cabling_group": None}).eq("farm_id", st.session_state.active_site_id).execute()
                        else:
                            supabase.table("structures").update({"transformer_id": None, "inverter_id": None, "string_cabling_group": None}).eq("farm_id", st.session_state.active_site_id).eq("inverter_id", elec_reset_scope).execute()
                        time.sleep(0.4); st.rerun()

            html_elec_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div id="elec_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #ff007f; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-weight: bold;"></div>
                <div id="elec_dialogue_modal" style="display:none; position:absolute; bottom:35px; left:50%; transform:translateX(-50%); background:#1e293b; padding:18px 35px; border-radius:8px; border:2px solid #ff007f; z-index:100000; box-shadow: 0 10px 40px rgba(0,0,0,0.85); text-align:center;">
                    <div id="elec_modal_status_msg" style="color:#22c55e; font-weight:bold; margin-bottom:10px; display:none;">Processing database updates...</div>
                    <div style="color:#f1f5f9; font-weight:bold; margin-bottom:14px; font-size:15px;" id="popup_query_label_txt">Execute Action?</div>
                    <button id="btn_elec_confirm" style="background:#22c55e; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; margin-right:12px; font-size:14px;">Confirm, Save Change</button>
                    <button id="btn_elec_cancel" style="background:#ef4444; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:14px;">Cancel</button>
                </div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="elec_canvas" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); let txs = JSON.parse(atob("__TX_DATA_B64__")); let invs = JSON.parse(atob("__INV_DATA_B64__"));
                    const canvas = document.getElementById("elec_canvas"); const ctx = canvas.getContext('2d'); const tooltip = document.getElementById("elec_hover_tooltip"); const modal = document.getElementById("elec_dialogue_modal");
                    const CELL = CELL_SIZE_VAL; const currentMode = "CURRENT_MODE_VAL"; const tsTag = "TS_TAG_VAL"; const parentTs = "INV_PARENT_TS_VAL"; const invNum = "INV_NUM_VAL"; const stringCode = "STR_CODE_VAL";
                    const isPublished = __IS_PUBLISHED_VAL__; const activeFarmId = "__FARM_ID_VAL__";
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL; const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;
                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight); if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale); let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isPanning = false, isSelecting = false, startX = 0, startY = 0, currentX = 0, currentY = 0, activeSelectedInverterNode = null, actionPayloadQueue = null;
                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function getStringColor(stringName) {
                        if (!stringName) return 'transparent';
                        let hash = 0; for (let i = 0; i < stringName.length; i++) { hash = stringName.charCodeAt(i) + ((hash << 5) - hash); }
                        return `hsl(${Math.abs(hash * 45) % 360}, 95%, 50%)`;
                    }
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = '#1e293b'; let x = b.min_c * CELL; let y = b.min_r * CELL; let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#020617'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h);
                            if (b.structure_type === 'double_6x9') { ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'; ctx.lineWidth = 0.75; ctx.beginPath(); ctx.moveTo(x, y + (h / 2)); ctx.lineTo(x + w, y + (h / 2)); ctx.stroke(); }
                            if (b.string_cabling_group) { ctx.strokeStyle = getStringColor(b.string_cabling_group); ctx.lineWidth = 1.75; ctx.strokeRect(x + 1, y + 1, w - 2, h - 2); }
                        });
                        txs.forEach(t => {
                            ctx.fillStyle = '#a78bfa'; ctx.fillRect(t.grid_c * CELL - 4, t.grid_r * CELL - 4, CELL + 8, CELL + 8);
                            ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.strokeRect(t.grid_c * CELL - 4, t.grid_r * CELL - 4, CELL + 8, CELL + 8);
                            ctx.fillStyle = '#020617'; ctx.font = "bold 9px sans-serif"; ctx.fillText(t.name, t.grid_c * CELL - 2, t.grid_r * CELL + 6);
                        });
                        invs.forEach(i => {
                            ctx.fillStyle = (activeSelectedInverterNode && activeSelectedInverterNode.id === i.id) ? '#facc15' : '#ef4444';
                            ctx.fillRect(i.grid_c * CELL + 2, i.grid_r * CELL + 4, CELL - 4, CELL - 8); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.75; ctx.strokeRect(i.grid_c * CELL + 2, i.grid_r * CELL + 4, CELL - 4, CELL - 8);
                        });
                        ctx.restore();
                        if (isSelecting && currentMode.includes("3.")) { ctx.strokeStyle = '#ff007f'; ctx.lineWidth = 2; ctx.fillStyle = 'rgba(255, 0, 127, 0.2)'; ctx.fillRect(startX, startY, currentX - startX, currentY - startY); }
                    }
                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left; const mY = e.clientY - rect.top;
                        if (isPanning) { offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); tooltip.style.display = "none"; return; }
                        else if (isSelecting) { currentX = mX; currentY = mY; draw(); tooltip.style.display = "none"; return; }
                        let worldX = (mX - offsetX) / scale; let worldY = (mY - offsetY) / scale; let gridC = Math.floor(worldX / CELL); let gridR = Math.floor(worldY / CELL);
                        let matchTx = txs.find(t => t.grid_c === gridC && t.grid_r === gridR);
                        if (matchTx) { tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Transformer Station Node<br/>ID Label: ${matchTx.name}`; return; }
                        let matchInv = invs.find(i => i.grid_c === gridC && i.grid_r === gridR);
                        if (matchInv) {
                            let targetedIdCode = `${matchInv.transformer_name}-${matchInv.inverter_num}`; let matchedCablesCount = blocks.filter(b => b.inverter_id === targetedIdCode).length;
                            tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Inverter Box Node<br/>ID Code: ${targetedIdCode}<br/>Linked Wire Strings: ${matchedCablesCount}`; return;
                        }
                        let hoveredBlock = null; for (let b of blocks) { if (worldX >= b.min_c * CELL && worldX <= (b.max_c + 1) * CELL && worldY >= b.min_r * CELL && worldY <= (b.max_r + 1) * CELL) { hoveredBlock = b; break; } }
                        if (hoveredBlock) { tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Tracker Cell: ${hoveredBlock.table_label}<br/>Zone: ${hoveredBlock.assigned_zone}<br/>Transformer Feed: ${hoveredBlock.transformer_id || 'None'}<br/>Inverter Array: ${hoveredBlock.inverter_id || 'None'}<br/>DC Cabling String: ${hoveredBlock.string_cabling_group || 'None'}`; }
                        else { tooltip.style.display = "none"; }
                    });
                    canvas.addEventListener('mousedown', async (e) => {
                        if (isPublished) return; const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left; const mY = e.clientY - rect.top;
                        let worldX = (mX - offsetX) / scale; let worldY = (mY - offsetY) / scale; let gridC = Math.floor(worldX / CELL); let gridR = Math.floor(worldY / CELL);
                        if (e.button === 2) { isPanning = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; return; }
                        if (currentMode.includes("1.")) {
                            let existingTx = txs.find(t => t.grid_c === gridC && t.grid_r === gridR);
                            if (existingTx) { actionPayloadQueue = { type: "DELETE_TX", id: existingTx.id }; document.getElementById("popup_query_label_txt").innerText = `🗑️ Remove Transformer Station ${existingTx.name}?`; modal.style.display = "block"; }
                            else { if (!tsTag) return; actionPayloadQueue = { type: "CREATE_TX", body: { farm_id: activeFarmId, name: tsTag, grid_r: gridR, grid_c: gridC } }; document.getElementById("popup_query_label_txt").innerText = `➕ Place Transformer Node labeled '${tsTag}' here?`; modal.style.display = "block"; }
                        } else if (currentMode.includes("2.")) {
                            let existingInv = invs.find(i => i.grid_c === gridC && i.grid_r === gridR);
                            if (existingInv) { actionPayloadQueue = { type: "DELETE_INV", id: existingInv.id }; document.getElementById("popup_query_label_txt").innerText = `🗑️ Delete Inverter Node ${existingInv.transformer_name}-${existingInv.inverter_num}?`; modal.style.display = "block"; }
                            else { if (parentTs.includes("Select") || !invNum) return; actionPayloadQueue = { type: "CREATE_INV", body: { farm_id: activeFarmId, transformer_name: parentTs, inverter_num: invNum, grid_r: gridR, grid_c: gridC } }; document.getElementById("popup_query_label_txt").innerText = `➕ Place Inverter Box linked to ${parentTs} here?`; modal.style.display = "block"; }
                        } else if (currentMode.includes("3.")) {
                            let existingInv = invs.find(i => i.grid_c === gridC && i.grid_r === gridR);
                            if (existingInv) { activeSelectedInverterNode = existingInv; draw(); }
                            else { isSelecting = true; startX = mX; startY = mY; currentX = mX; currentY = mY; }
                        }
                    });
                    canvas.addEventListener('mouseup', async (e) => {
                        if (isPanning) { isPanning = false; }
                        else if (isSelecting && currentMode.includes("3.")) {
                            isSelecting = false; if (!activeSelectedInverterNode) { alert("Please click an Inverter dot first."); return; }
                            let boxX1 = Math.min(startX, currentX), boxX2 = Math.max(startX, currentX); let boxY1 = Math.min(startY, currentY), boxY2 = Math.max(startY, currentY);
                            let stagedIds = []; blocks.forEach(b => { let cx = b.min_c * CELL * scale + offsetX; let cy = b.min_r * CELL * scale + offsetY; if (cx >= boxX1 && cx <= boxX2 && cy >= boxY1 && cy <= boxY2) stagedIds.push(b.id); });
                            if (stagedIds.length > 0) { actionPayloadQueue = { type: "LINK_STRINGS", ids: stagedIds, inv: activeSelectedInverterNode }; document.getElementById("popup_query_label_txt").innerText = `🔌 Route ${stagedIds.length} trackers into Inverter ${actionPayloadQueue.inv.transformer_name}-${actionPayloadQueue.inv.inverter_num}?`; modal.style.display = "block"; }
                        }
                    });
                    document.getElementById("btn_elec_confirm").addEventListener('click', async () => {
                        if (!actionPayloadQueue) return; document.getElementById("elec_modal_status_msg").style.display = "block";
                        if (actionPayloadQueue.type === "CREATE_TX") { await fetch("SUPABASE_URL_VAL/rest/v1/transformers", { method: "POST", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json" }, body: JSON.stringify(actionPayloadQueue.body) }); }
                        else if (actionPayloadQueue.type === "DELETE_TX") { await fetch(`SUPABASE_URL_VAL/rest/v1/transformers?id=eq.${actionPayloadQueue.id}`, { method: "DELETE", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL" } }); }
                        else if (actionPayloadQueue.type === "CREATE_INV") { await fetch("SUPABASE_URL_VAL/rest/v1/inverters", { method: "POST", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json" }, body: JSON.stringify(actionPayloadQueue.body) }); }
                        else if (actionPayloadQueue.type === "DELETE_INV") { await fetch(`SUPABASE_URL_VAL/rest/v1/inverters?id=eq.${actionPayloadQueue.id}`, { method: "DELETE", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL" } }); }
                        else if (actionPayloadQueue.type === "LINK_STRINGS") {
                            let code = `${actionPayloadQueue.inv.transformer_name}-${actionPayloadQueue.inv.inverter_num}`;
                            for (let id of actionPayloadQueue.ids) { await fetch(`SUPABASE_URL_VAL/rest/v1/structures?id=eq.${id}`, { method: "PATCH", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json" }, body: JSON.stringify({ transformer_id: actionPayloadQueue.inv.transformer_name, inverter_id: code, string_cabling_group: stringCode }) }); }
                        }
                        location.reload();
                    });
                    document.getElementById("btn_elec_cancel").addEventListener('click', () => { actionPayloadQueue = null; modal.style.display = "none"; draw(); });
                    canvas.addEventListener('wheel', (e) => { e.preventDefault(); const rect = canvas.getBoundingClientRect(); const mouseX = e.clientX - rect.left; const mouseY = e.clientY - rect.top; const gridX = (mouseX - offsetX) / scale; const gridY = (mouseY - offsetY) / scale; scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.005, Math.min(scale, 30)); offsetX = mouseX - gridX * scale; offsetY = mouseY - gridY * scale; draw(); }, { passive: false });
                    draw();
                })();
            </script>
            """
            html_elec_engine = html_elec_engine.replace("__JSON_DATA_B64__", b64_json_data).replace("__TX_DATA_B64__", b64_transformers).replace("__INV_DATA_B64__", b64_inverters).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("CURRENT_MODE_VAL", str(active_elec_mode)).replace("TS_TAG_VAL", str(ts_prefix if "1." in active_elec_mode else "")).replace("INV_PARENT_TS_VAL", str(inv_parent_ts if "2." in active_elec_mode else "")).replace("INV_NUM_VAL", str(inv_num_val if "2." in active_elec_mode else "")).replace("STR_CODE_VAL", str(active_string_lbl if "3." in active_elec_mode else "")).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY).replace("__IS_PUBLISHED_VAL__", "true" if site_is_published else "false").replace("__FARM_ID_VAL__", str(st.session_state.active_site_id))
            components.html(html_elec_engine, height=660)

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

        # --- STAGE 4: MASTER BLUEPRINT OVERVIEW NODES ---
        with setup_tabs[3]:
            st.markdown("### 🏪 Master Blueprint Configuration Overview Nodes")
            html_transformer_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none;">
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="trans_canvas" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() { 
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); const canvas = document.getElementById("trans_canvas"); const ctx = canvas.getContext('2d'); const CELL = CELL_SIZE_VAL;
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;
                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight); if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale); let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isDragging = false, startX, startY;
                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => { 
                            ctx.fillStyle = '#64748b'; let x = b.min_c * CELL; let y = b.min_r * CELL; let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h); 
                        }); ctx.restore();
                    }
                    canvas.addEventListener('mousedown', (e) => { if(e.button===2 || e.button===0) { isDragging = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; } });
                    canvas.addEventListener('mousemove', (e) => { if (!isDragging) return; offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); });
                    canvas.addEventListener('mouseup', () => { isDragging = false; });
                    canvas.addEventListener('wheel', (e) => {
                        e.preventDefault(); const rect = canvas.getBoundingClientRect(); const mouseX = e.clientX - rect.left; const mouseY = e.clientY - rect.top;
                        const gridX = (mouseX - offsetX) / scale; const gridY = (mouseY - offsetY) / scale;
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.01, Math.min(scale, 15));
                        offsetX = mouseX - gridX * scale; offsetY = mouseY - gridY * scale; draw();
                    }, { passive: false });
                    draw();
                })();
            </script>
            """
            html_transformer_engine = html_transformer_engine.replace("__JSON_DATA_B64__", b64_json_data).replace("CELL_SIZE_VAL", str(CELL_SIZE)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r))
            components.html(html_transformer_engine, height=640)

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (CREW WORKSPACE VIEWS)
        # ==============================================================================
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
                <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">
                    ⚙️ <b>Crew Controls:</b> <span style="color:#22c55e; font-weight:bold;">Left-Click + Drag</span> to multi-select cell blocks &nbsp;|&nbsp; <span style="color:#38bdf8; font-weight:bold;">Right-Click + Drag</span> to pan map &nbsp;|&nbsp; <span style="color:#eab308; font-weight:bold;">Single Left-Click</span> to complete &nbsp;|&nbsp; <span style="color:#a78bfa; font-weight:bold;">Scroll</span> to zoom.
                    <div id="crew_sync_status_msg" style="color:#22c55e; font-weight:bold; display:none; margin-top:4px;">Transmitting field records...</div>
                </div>
                <div id="crew_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #22c55e; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-weight: bold;"></div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="crew_LAYER_KEY" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); const canvas = document.getElementById("crew_LAYER_KEY"); const ctx = canvas.getContext('2d'); const tooltip = document.getElementById("crew_hover_tooltip"); const CELL = 14; 
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL; const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;
                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight); if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale); let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isPanning = false, isSelecting = false, dragStartRawX = 0, dragStartRawY = 0, dragCurrentRawX = 0, dragCurrentRawY = 0;
                    canvas.addEventListener('contextmenu', e => e.preventDefault());
                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = b['LAYER_KEY_status'] === 'completed' ? '#22c55e' : '#3b82f6';
                            let x = b.min_c * CELL; let y = b.min_r * CELL; let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h);
                        }); ctx.restore();
                        if (isSelecting) { ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 2; ctx.fillStyle = 'rgba(34, 197, 94, 0.25)'; ctx.fillRect(dragStartRawX, dragStartRawY, dragCurrentRawX - dragStartRawX, dragCurrentRawY - dragStartRawY); }
                    }
                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX - rect.left; const mY = e.clientY - rect.top;
                        if (isPanning) { offsetX = e.clientX - dragStartRawX; offsetY = e.clientY - dragStartRawY; draw(); tooltip.style.display = "none"; return; }
                        else if (isSelecting) { dragCurrentRawX = mX; dragCurrentRawY = mY; draw(); tooltip.style.display = "none"; return; }
                        let worldX = (mX - offsetX) / scale; let worldY = (mY - offsetY) / scale; let hoveredBlock = null;
                        for (let b of blocks) {
                            if (worldX >= b.min_c * CELL && worldX <= (b.max_c + 1) * CELL && worldY >= b.min_r * CELL && worldY <= (b.max_r + 1) * CELL) { hoveredBlock = b; break; }
                        }
                        if (hoveredBlock) { tooltip.style.display = "block"; tooltip.style.left = (mX + 15) + "px"; tooltip.style.top = (mY + 15) + "px"; tooltip.innerHTML = `Label: ${hoveredBlock.table_label}<br/>Zone: ${hoveredBlock.assigned_zone}<br/>Status: ${hoveredBlock['LAYER_KEY_status'] || 'pending'}`; }
                        else { tooltip.style.display = "none"; }
                    });
                    canvas.addEventListener('mousedown', (e) => {
                        const rect = canvas.getBoundingClientRect(); const clickX = e.clientX - rect.left; const clickY = e.clientY - rect.top;
                        if (e.button === 2) { isPanning = true; isSelecting = false; dragStartRawX = e.clientX - offsetX; dragStartRawY = e.clientY - offsetY; }
                        else if (e.button === 0) { isSelecting = true; isPanning = false; dragStartRawX = clickX; dragStartRawY = clickY; dragCurrentRawX = clickX; dragCurrentRawY = clickY; canvas.style.cursor = 'crosshair'; }
                        tooltip.style.display = "none";
                    });
                    canvas.addEventListener('mouseup', async (e) => {
                        const rect = canvas.getBoundingClientRect(); const mouseUpX = e.clientX - rect.left; const mouseUpY = e.clientY - rect.top;
                        if (isPanning) { isPanning = false; canvas.style.cursor = 'grab'; }
                        else if (isSelecting) {
                            isSelecting = false; canvas.style.cursor = 'default';
                            let boxX1 = Math.min(dragStartRawX, mouseUpX), boxX2 = Math.max(dragStartRawX, mouseUpX); let boxY1 = Math.min(dragStartRawY, mouseUpY), boxY2 = Math.max(dragStartRawY, mouseUpY);
                            let totalDragDistance = Math.sqrt(Math.pow(mouseUpX - dragStartRawX, 2) + Math.pow(mouseUpY - dragStartRawY, 2)); let payloadIds = [];
                            blocks.forEach(b => {
                                let cx = b.min_c * CELL * scale + offsetX; let cy = b.min_r * CELL * scale + offsetY;
                                let isMatched = (totalDragDistance > 4) ? (cx >= boxX1 && cx <= boxX2 && cy >= boxY1 && cy <= boxY2) : (boxX1 >= cx && boxX1 <= (b.max_c * CELL * scale + offsetX) && boxY1 >= cy && boxY1 <= (b.max_r * CELL * scale + offsetY));
                                if (isMatched && b['LAYER_KEY_status'] !== 'completed') payloadIds.push(b.id);
                            });
                            if (payloadIds.length > 0) {
                                const statMsg = document.getElementById("crew_sync_status_msg"); statMsg.style.display = "block"; statMsg.innerText = `Synchronizing ${payloadIds.length} blocks to database...`;
                                try {
                                    for (let id of payloadIds) {
                                        let target = blocks.find(b => b.id === id); if (target) target['LAYER_KEY_status'] = 'completed';
                                        await fetch('SUPABASE_URL_VAL/rest/v1/structures?id=eq.' + id, {
                                            method: "PATCH", headers: { "apikey": 'SUPABASE_KEY_VAL', "Authorization": 'Bearer SUPABASE_KEY_VAL', "Content-Type": "application/json", "Prefer": "return=minimal" },
                                            body: JSON.stringify({ "LAYER_KEY_status": "completed", "LAYER_KEY_date": "TODAY_STR_VAL" })
                                        });
                                    }
                                    statMsg.innerText = "Sync Complete!"; setTimeout(() => { statMsg.style.display = "none"; }, 5000);
                                } catch (e) { statMsg.innerText = "Database updates timed out."; }
                            }
                            setTimeout(draw, 50);
                        }
                    });
                })();
            </script>
            """
            html_crew_map = html_crew_map.replace("__JSON_DATA_B64__", b64_data).replace("LAYER_KEY", str(layer_key)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("TODAY_STR_VAL", today_str).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            return html_crew_map

        def process_crew_tab(tab_obj, key_val):
            with tab_obj:
                components.html(inject_crew_tracking_map(key_val, b64_json_data, min_c, max_c, min_r, max_r), height=640)

        process_crew_tab(crew_tabs[0], "pegging")
        process_crew_tab(crew_tabs[1], "piling")
        process_crew_tab(crew_tabs[2], "mounting")
        process_crew_tab(crew_tabs[3], "modules")
