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
                                    has_value = cell.value is not None and str(cell.value).strip() != ""
                                    
                                    has_fill = False
                                    if cell.fill and cell.fill.fill_type is not None and cell.fill.fill_type != 'none':
                                        if hasattr(cell.fill, 'start_color') and cell.fill.start_color:
                                            color_hex = str(cell.fill.start_color.rgb)
                                            if color_hex and "00000000" not in color_hex and "FFFFFFFF" not in color_hex:
                                                has_fill = True
                                        else:
                                            has_fill = True
                                            
                                    if has_value or has_fill:
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
                                                "structure_type": f"Layout_{w_cells}x{h_cells}",
                                                "assigned_zone": "Unassigned",
                                                "section_group": int(table_counter),
                                                "pegging_status": "pending", "piling_status": "pending", 
                                                "mounting_status": "pending", "modules_status": "pending"
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
            # Fixed form-lifecycle state assignment bypass sequence
            adm_pass = st.text_input("Upgrade to Admin Mode:", type="password", key="sidebar_admin_pass_input")
            if st.button("Verify Clearance", type="primary"):
                if str(adm_pass) == str(st.session_state.admin_key_match):
                    st.session_state.is_admin_mode = True
                    st.success("Clearance Granted!")
                    time.sleep(0.5)
                    st.rerun()
                else: 
                    st.error("Incorrect Password.")
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
                    if not site_bg_img.startswith("{"):
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

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)

    if not active_table_data:
        st.warning("ℹ️ No operational layout metrics have loaded from database for this specific site yet. Use the control configuration page above to import structural data files.")
        st.stop()

    min_r = min([b.get("min_r", 1) for b in active_table_data])
    max_r = max([b.get("max_r", 100) for b in active_table_data])
    min_c = min([b.get("min_c", 1) for b in active_table_data])
    max_c = max([b.get("max_c", 150) for b in active_table_data])

    CELL_SIZE = 14
    
    json_str = json.dumps(active_table_data)
    b64_json_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    for b in active_table_data:
        z = b.get("assigned_zone")
        if z and z not in st.session_state.managed_zones:
            st.session_state.managed_zones.insert(len(st.session_state.managed_zones)-1, z)
    
    clean_wiping_dropdown_options = [zone for zone in st.session_state.managed_zones if zone != "Unassigned"]

    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs([
            "🖼️ Base Overview & Zone Assignation", 
            "📌 Pegging & Piling Customizer",
            "🛰️ Unified Layout Planner & Topology Workspace"
        ])
        
        # --- STAGE 1: SETUPS OVERVIEW & ZONE ASSIGNATION ---
        with setup_tabs[0]:
            st.markdown("### 🖼️ Operational Field Zoning Assignation Engine")
            
            if site_bg_img and not site_bg_img.startswith("{"):
                st.image(site_bg_img, caption="Active Site Blueprint Layout Background Reference", use_container_width=False, width=600)

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
                wipe_scope_selection = st.selectbox("Select Target Scope to Flush & Reset to Unassigned:", ["ALL ZONES"] + clean_wiping_dropdown_options)
            with col_wipe2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                
                if site_is_published:
                    st.error("Cannot reset zone assets on a frozen, deployed workspace framework.")
                elif st.button("💥 Reset Selected Allocation Fleet", type="secondary", use_container_width=True):
                    with st.spinner("Flushing target zones..."):
                        try:
                            if wipe_scope_selection == "ALL ZONES":
                                supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).execute()
                                st.success("Entire farm structural matrix zones set back to Unassigned!")
                            else:
                                supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).eq("assigned_zone", wipe_scope_selection).execute()
                                st.success(f"Successfully cleared allocation indexes for {wipe_scope_selection}!")
                            time.sleep(0.5); st.rerun()
                        except Exception as e:
                            st.error(f"Reset failed: {str(e)}")

            html_zone_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">
                    Mouse Controls: <span style="color:#22c55e; font-weight:bold;">Left-Click + Drag</span> to select multiple cells &nbsp;|&nbsp; <span style="color:#38bdf8; font-weight:bold;">Right-Click + Drag</span> to pan map &nbsp;|&nbsp; <span style="color:#eab308; font-weight:bold;">Single Left-Click</span> to select a single block &nbsp;|&nbsp; <span style="color:#a78bfa; font-weight:bold;">Scroll</span> to zoom.
                </div>
                
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
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    const canvas = document.getElementById("zone_canvas");
                    const ctx = canvas.getContext('2d');
                    const tooltip = document.getElementById("canvas_hover_tooltip");
                    const paintZone = "PAINT_ZONE_VAL";
                    const CELL = CELL_SIZE_VAL;
                    const isPublished = __IS_PUBLISHED_VAL__;
                    
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL;
                    const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);

                    let isPanning = false;
                    let isSelecting = false;
                    let startX = 0, startY = 0, currentX = 0, currentY = 0;
                    let stagedBlockIds = [];

                    canvas.addEventListener('contextmenu', e => e.preventDefault());

                    function getZoneColor(zoneName) {
                        if (!zoneName || zoneName.toLowerCase() === 'unassigned' || zoneName.trim() === '') return '#334155';
                        let hash = 0; 
                        let cleaned = zoneName.toUpperCase().trim();
                        for (let i = 0; i < cleaned.length; i++) { 
                            hash = cleaned.charCodeAt(i) + ((hash << 5) - hash); 
                        }
                        let hue = Math.abs(hash * 45) % 360; 
                        return `hsl(${hue}, 90%, 50%)`;
                    }

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);

                        blocks.forEach(b => {
                            let isStaged = stagedBlockIds.includes(b.id);
                            ctx.fillStyle = getZoneColor(b.assigned_zone);
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h);
                            ctx.strokeStyle = '#020617'; ctx.lineWidth = 0.75; ctx.strokeRect(x, y, w, h);
                            
                            if (isStaged) { 
                                ctx.strokeStyle = '#ffff00'; 
                                ctx.lineWidth = 2.5; 
                                ctx.strokeRect(x, y, w, h); 
                            }
                        });
                        ctx.restore();

                        if (isSelecting) {
                            ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2;
                            ctx.fillStyle = 'rgba(56, 189, 248, 0.25)';
                            ctx.fillRect(startX, startY, currentX - startX, currentY - startY);
                            ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
                        }
                    }

                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const mX = e.clientX - rect.left;
                        const mY = e.clientY - rect.top;
                        
                        if (isPanning) {
                            offsetX = e.clientX - startX;
                            offsetY = e.clientY - startY;
                            draw();
                            tooltip.style.display = "none";
                            return;
                        } else if (isSelecting) {
                            currentX = mX;
                            currentY = mY;
                            draw();
                            tooltip.style.display = "none";
                            return;
                        }

                        let worldX = (mX - offsetX) / scale;
                        let worldY = (mY - offsetY) / scale;
                        
                        let hoveredBlock = null;
                        for (let b of blocks) {
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            if (worldX >= x && worldX <= x + w && worldY >= y && worldY <= y + h) {
                                hoveredBlock = b;
                                break;
                            }
                        }

                        if (hoveredBlock) {
                            tooltip.style.display = "block";
                            tooltip.style.left = (mX + 15) + "px";
                            tooltip.style.top = (mY + 15) + "px";
                            tooltip.innerHTML = `Label: ${hoveredBlock.table_label}<br/>Zone: ${hoveredBlock.assigned_zone || 'Unassigned'}`;
                        } else {
                            tooltip.style.display = "none";
                        }
                    });

                    canvas.addEventListener('mousedown', (e) => {
                        if (isPublished) return; 
                        const rect = canvas.getBoundingClientRect();
                        const mX = e.clientX - rect.left;
                        const mY = e.clientY - rect.top;
                        
                        if (e.button === 2) { 
                            isPanning = true;
                            isSelecting = false;
                            startX = e.clientX - offsetX;
                            startY = e.clientY - offsetY;
                            canvas.style.cursor = 'move';
                        } else if (e.button === 0) { 
                            isSelecting = true;
                            isPanning = false;
                            startX = mX;
                            startY = mY;
                            currentX = mX;
                            currentY = mY;
                            canvas.style.cursor = 'crosshair';
                        }
                        tooltip.style.display = "none";
                    });

                    canvas.addEventListener('mouseup', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const endX = e.clientX - rect.left;
                        const endY = e.clientY - rect.top;

                        if (isPanning) {
                            isPanning = false;
                            canvas.style.cursor = 'grab';
                        } else if (isSelecting) {
                            isSelecting = false;
                            canvas.style.cursor = 'default';
                            
                            stagedBlockIds = [];

                            let boxX1 = Math.min(startX, endX);
                            let boxX2 = Math.max(startX, endX);
                            let boxY1 = Math.min(startY, endY);
                            let boxY2 = Math.max(startY, endY);

                            if (Math.abs(endX - startX) > 4 || Math.abs(endY - startY) > 4) {
                                blocks.forEach(b => {
                                    if (b.assigned_zone && b.assigned_zone.toLowerCase() !== 'unassigned') return;

                                    let cellScreenX1 = b.min_c * CELL * scale + offsetX;
                                    let cellScreenX2 = (b.max_c * CELL + CELL) * scale + offsetX;
                                    let cellScreenY1 = b.min_r * CELL * scale + offsetY;
                                    let cellScreenY2 = (b.max_r * CELL + CELL) * scale + offsetY;

                                    if (cellScreenX2 >= boxX1 && cellScreenX1 <= boxX2 &&
                                        cellScreenY2 >= boxY1 && cellScreenY1 <= boxY2) {
                                        stagedBlockIds.push(b.id);
                                    }
                                });
                            } else {
                                blocks.forEach(b => {
                                    if (b.assigned_zone && b.assigned_zone.toLowerCase() !== 'unassigned') return;

                                    let cellScreenX1 = b.min_c * CELL * scale + offsetX;
                                    let cellScreenX2 = (b.max_c * CELL + CELL) * scale + offsetX;
                                    let cellScreenY1 = b.min_r * CELL * scale + offsetY;
                                    let cellScreenY2 = (b.max_r * CELL + CELL) * scale + offsetY;

                                    if (boxX1 >= cellScreenX1 && boxX1 <= cellScreenX2 &&
                                        boxY1 >= cellScreenY1 && boxY1 <= cellScreenY2) {
                                        stagedBlockIds.push(b.id);
                                    }
                                });
                            }

                            if (stagedBlockIds.length > 0) {
                                document.getElementById("lbl_zone").innerText = paintZone;
                                document.getElementById("dialogue_overlay").style.display = "block";
                            }
                            draw();
                        }
                    });

                    document.getElementById("btn_yes").addEventListener('click', async () => {
                        const msgBox = document.getElementById("status_message_box");
                        msgBox.style.display = "block";
                        msgBox.innerText = `Updating ${stagedBlockIds.length} components...`;
                        
                        try {
                            for (let id of stagedBlockIds) {
                                let target = blocks.find(b => b.id === id); 
                                if (target) target.assigned_zone = paintZone;
                                
                                await fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq." + id, {
                                    method: "PATCH", 
                                    headers: { 
                                        "apikey": "SUPABASE_KEY_VAL", 
                                        "Authorization": "Bearer SUPABASE_KEY_VAL", 
                                        "Content-Type": "application/json",
                                        "Prefer": "return=minimal"
                                    },
                                    body: JSON.stringify({ "assigned_zone": paintZone })
                                });
                            }
                            msgBox.innerText = "Done! Hit the reload button to refresh overview.";
                            setTimeout(() => { msgBox.style.display = "none"; }, 4000);
                        } catch(e) {
                            msgBox.innerText = "Network transmission exception dropped.";
                        }
                        
                        stagedBlockIds = []; 
                        document.getElementById("dialogue_overlay").style.display = "none"; 
                        draw();
                    });

                    document.getElementById("btn_no").addEventListener('click', () => {
                        stagedBlockIds = []; document.getElementById("dialogue_overlay").style.display = "none"; draw();
                    });

                    canvas.addEventListener('wheel', (e) => {
                        e.preventDefault(); const rect = canvas.getBoundingClientRect(); const mouseX = e.clientX - rect.left; const mouseY = e.clientY - rect.top;
                        const gridX = (mouseX - offsetX) / scale; const gridY = (mouseY - offsetY) / scale;
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.005, Math.min(scale, 30));
                        offsetX = mouseX - gridX * scale; offsetY = mouseY - gridY * scale; draw();
                    }, { passive: false });
                    draw();
                })();
            </script>
            """
            html_zone_engine = html_zone_engine.replace("__JSON_DATA_B64__", b64_json_data)\
                                             .replace("PAINT_ZONE_VAL", str(target_paint_zone))\
                                             .replace("CELL_SIZE_VAL", str(CELL_SIZE))\
                                             .replace("MIN_C_VAL", str(min_c))\
                                             .replace("MAX_C_VAL", str(max_c))\
                                             .replace("MIN_R_VAL", str(min_r))\
                                             .replace("MAX_R_VAL", str(max_r))\
                                             .replace("SUPABASE_URL_VAL", SUPABASE_URL)\
                                             .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)\
                                             .replace("__IS_PUBLISHED_VAL__", "true" if site_is_published else "false")
            components.html(html_zone_engine, height=700)

        # --- STAGE 2: PEGGING & PILING CUSTOMIZER ---
        with setup_tabs[1]:
            st.markdown("### 📌 Component Placement Microscale Engineering Template Engine")
            
            layout_types = {}
            for block in active_table_data:
                h_cells = block.get("max_r", 1) - block.get("min_r", 1) + 1
                w_cells = block.get("max_c", 1) - block.get("min_c", 1) + 1
                layout_key = f"Tracker Configuration Matrix Profile ({w_cells}x{h_cells} Columns/Rows)"
                
                if layout_key not in layout_types:
                    layout_types[layout_key] = {
                        "type_string": block.get("structure_type"),
                        "h_cells": h_cells,
                        "w_cells": w_cells
                    }

            layout_options = list(layout_types.keys())
            
            if not layout_options:
                st.info("No active matrix layout definitions tracked in database.")
            else:
                selected_layout_label = st.selectbox(
                    "Select Layout Architecture Template Matrix to Customize:", 
                    layout_options
                )
                
                target_layout = layout_types[selected_layout_label]
                state_prefix = f"layout_cfg_{target_layout['type_string']}"
                undo_stack_key = f"undo_{state_prefix}"
                
                if undo_stack_key not in st.session_state:
                    st.session_state[undo_stack_key] = []
                
                if f"{state_prefix}_rows" not in st.session_state:
                    st.session_state[f"{state_prefix}_rows"] = 4
                if f"{state_prefix}_cols" not in st.session_state:
                    st.session_state[f"{state_prefix}_cols"] = 3

                col_inputs, col_actions = st.columns([4, 6])
                
                with col_inputs:
                    st.markdown("#### 📏 Target Coordination Point Formations")
                    row_pts = st.number_input(
                        "Array Pin Points per Row Dimension Layout:", 
                        min_value=1, max_value=20, 
                        key=f"{state_prefix}_rows"
                    )
                    col_pts = st.number_input(
                        "Array Pin Points per Column Dimension Layout:", 
                        min_value=1, max_value=20, 
                        key=f"{state_prefix}_cols"
                    )
                    
                    total_calculated_points = row_pts * col_pts
                    st.metric(label="Calculated Component Volume Distribution Density Matrix", value=f"{total_calculated_points} Points / Block")
                    
                    if st.button("💾 Apply & Replicate Structural Configuration Fleetwide", type="primary", use_container_width=True):
                        st.session_state[undo_stack_key].append({
                            "rows": row_pts,
                            "cols": col_pts,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        with st.spinner("Broadcasting visual component patterns to cloud layout..."):
                            try:
                                supabase.table("structures").update({
                                    "section_group": int(total_calculated_points)
                                }).eq("farm_id", st.session_state.active_site_id)\
                                  .eq("structure_type", target_layout["type_string"]).execute()
                                
                                st.success("Replication batch mutations applied securely workspace fleetwide!")
                                time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error(f"Transmission mutation dropped: {str(e)}")

                    if st.session_state[undo_stack_key]:
                        last_action = st.session_state[undo_stack_key][-1]
                        if st.button(f"↩️ Revert Layout Assignment Block (Snapshot: {last_action['timestamp']})", type="secondary", use_container_width=True):
                            st.session_state[undo_stack_key].pop()
                            st.rerun()

                with col_actions:
                    st.markdown("#### 🛰️ Structural Pin Grid Dynamic Canvas Previewer")
                    
                    h_px = int(target_layout["h_cells"] * 25)
                    w_px = int(target_layout["w_cells"] * 35)
                    
                    html_micro_template = f"""
                    <div style="background:#0f172a; padding:15px; border-radius:12px; text-align:center; font-family:sans-serif;">
                        <canvas id="micro_canvas" width="450" height="280" style="background:#020617; border:2px dashed #38bdf8; border-radius:8px;"></canvas>
                    </div>
                    <script>
                        (function() {{
                            const canvas = document.getElementById("micro_canvas");
                            const ctx = canvas.getContext('2d');
                            
                            const rows = {row_pts};
                            const cols = {col_pts};
                            const boxW = {w_px};
                            const boxH = {h_px};
                            
                            const bx = (canvas.width / 2) - (boxW / 2);
                            const by = (canvas.height / 2) - (boxH / 2);
                            
                            ctx.fillStyle = '#1e293b';
                            ctx.fillRect(bx, by, boxW, boxH);
                            ctx.strokeStyle = '#38bdf8';
                            ctx.lineWidth = 2;
                            ctx.strokeRect(bx, by, boxW, boxH);
                            
                            if(rows > 0 && cols > 0) {{
                                const rowGap = (rows === 1) ? boxH / 2 : boxH / (rows - 1);
                                const colGap = (cols === 1) ? boxW / 2 : boxW / (cols - 1);
                                
                                for(let r = 0; r < rows; r++) {{
                                    for(let c = 0; c < cols; c++) {{
                                        let px = (cols === 1) ? bx + (boxW / 2) : bx + (c * colGap);
                                        let py = (rows === 1) ? by + (boxH / 2) : by + (r * rowGap);
                                        
                                        ctx.fillStyle = '#f43f5e';
                                        ctx.beginPath();
                                        ctx.arc(px, py, 5, 0, Math.PI * 2);
                                        ctx.fill();
                                        
                                        ctx.strokeStyle = '#ffffff';
                                        ctx.lineWidth = 1;
                                        ctx.stroke();
                                    }}
                                }}
                            }}
                        }})();
                    </script>
                    """
                    components.html(html_micro_template, height=340)

        # --- STAGE 3: UNIFIED LAYOUT PLANNER & DC TOPOLOGY WORKSPACE ---
        with setup_tabs[2]:
            st.markdown("### 🔌 Microscale Grid Infrastructure Topologies, Stringing & Drop Station Routing")
            
            stored_metadata_string = current_farm_record.get("background_image_url") if (current_farm_record.get("background_image_url") and current_farm_record.get("background_image_url").startswith("{")) else "{}"
            
            html_topology_workspace = """
            <div style="background:#090d16; padding:15px; border-radius:12px; font-family:sans-serif; color:#f8fafc;">
                <div style="display:grid; grid-template-columns: 260px 1fr; gap:15px;">
                    <div style="background:#0f172a; padding:14px; border-radius:8px; border:1px solid #1e293b; font-size:13px;">
                        <h4 style="margin-top:0; margin-bottom:12px; color:#38bdf8; font-size:14px; border-bottom:1px solid #1e293b; padding-bottom:6px;">🛠️ DESIGN DECK</h4>
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="pan" checked> ✋ Pan / Navigate Map</label>
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="string"> 🔌 Click / Lasso Strings</label>
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="inverter"> ⚡ Click Place Inverter</label>
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="transformer"> 🏪 Click Place Transformer</label>
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="route"> 🔗 Route Inverter ➔ Xfrmr</label>
                        
                        <hr style="border-color:#1e293b; margin:14px 0;">
                        <h5 style="margin-top:0; margin-bottom:8px; color:#a78bfa; font-size:12px;">ACTIVE IDENTIFICATION</h5>
                        <label style="font-size:11px; color:#94a3b8;">Target Inverter ID #:</label>
                        <input type="number" id="topo_inv_token" value="20" min="1" style="width:100%; background:#1e293b; color:white; border:1px solid #334155; border-radius:4px; padding:5px; margin-bottom:12px; box-sizing:border-box;">
                        
                        <hr style="border-color:#1e293b; margin:14px 0;">
                        <h5 style="margin-top:0; margin-bottom:8px; color:#f43f5e; font-size:11px;">⚠️ GRANULAR FAULT FLUSH</h5>
                        <button id="btn_flush_routes" style="width:100%; background:#334155; border:none; padding:6px; color:#cbd5e1; font-weight:bold; border-radius:4px; cursor:pointer; margin-bottom:6px; font-size:11px;">❌ Clear Lines Only</button>
                        <button id="btn_flush_inverters" style="width:100%; background:#334155; border:none; padding:6px; color:#cbd5e1; font-weight:bold; border-radius:4px; cursor:pointer; margin-bottom:6px; font-size:11px;">❌ Clear Inverters Only</button>
                        <button id="btn_flush_transformers" style="width:100%; background:#334155; border:none; padding:6px; color:#cbd5e1; font-weight:bold; border-radius:4px; cursor:pointer; margin-bottom:12px; font-size:11px;">❌ Clear Xfrmrs Only</button>
                        
                        <button id="btn_topo_save" style="width:100%; background:#22c55e; border:none; padding:9px; color:white; font-weight:bold; border-radius:4px; cursor:pointer;">💾 Save Topologies</button>
                    </div>

                    <div style="position:relative;">
                        <div id="topo_tooltip" style="position:absolute; display:none; background:rgba(15,23,42,0.95); border:1px solid #38bdf8; padding:8px; border-radius:4px; font-size:12px; pointer-events:none; z-index:99999; color:#f8fafc; box-shadow:0 4px 12px rgba(0,0,0,0.5);"></div>
                        <canvas id="topo_canvas" width="1120" height="600" style="background:#020617; border-radius:8px; border:1px solid #1e293b; display:block;"></canvas>
                    </div>
                </div>
            </div>

            <script>
                (function() {
                    const databaseStructures = JSON.parse(atob("__JSON_DATA_B64__"));
                    let gridTopo = JSON.parse(atob("__TOPOLOGY_METADATA_B64__"));
                    
                    if (!gridTopo.inverters) gridTopo.inverters = [];
                    if (!gridTopo.transformers) gridTopo.transformers = [];
                    if (!gridTopo.stringGroups) gridTopo.stringGroups = {};

                    const canvas = document.getElementById("topo_canvas");
                    const ctx = canvas.getContext("2d");
                    const tooltip = document.getElementById("topo_tooltip");
                    const CELL = 14;

                    let independentStrings = [];
                    databaseStructures.forEach(b => {
                        if (b.structure_type === "double_6x9") {
                            let mid = b.min_r + Math.floor((b.max_r - b.min_r) / 2);
                            independentStrings.push({
                                id: b.id + "_N", parentId: b.id, label: b.table_label + " (North Facing)",
                                min_c: b.min_c, max_c: b.max_c, min_r: b.min_r, max_r: mid,
                                zone: b.assigned_zone || "Unassigned"
                            });
                            independentStrings.push({
                                id: b.id + "_S", parentId: b.id, label: b.table_label + " (South Facing)",
                                min_c: b.min_c, max_c: b.max_c, min_r: mid + 1, max_r: b.max_r,
                                zone: b.assigned_zone || "Unassigned"
                            });
                        } else {
                            independentStrings.push({
                                id: b.id + "_A", parentId: b.id, label: b.table_label,
                                min_c: b.min_c, max_c: b.max_c, min_r: b.min_r, max_r: b.max_r,
                                zone: b.assigned_zone || "Unassigned"
                            });
                        }
                    });

                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapW = (maxX - minX + 1) * CELL;
                    const mapH = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 80) / mapW, (canvas.height - 80) / mapH);
                    if (scale <= 0 || !isFinite(scale)) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (mapW * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapH * scale / 2) - (minY * CELL * scale);

                    let isPanning = false, isSelecting = false;
                    let startX = 0, startY = 0, currX = 0, currY = 0;
                    let selectedInverterIndexForRouting = null;

                    canvas.addEventListener("contextmenu", e => e.preventDefault());

                    function getActiveTool() {
                        return document.querySelector('input[name="topo_tool"]:checked').value;
                    }

                    function getCapacityColor(stringCount) {
                        if (stringCount <= 0) return "#1e293b";
                        const palette = [
                            "#10b981", "#06b6d4", "#8b5cf6", "#f43f5e", "#ec4899", 
                            "#3b82f6", "#14b8a6", "#f59e0b", "#6366f1", "#a855f7"
                        ];
                        return palette[(stringCount - 1) % palette.length];
                    }

                    function isInverterPlaced(invId) {
                        return gridTopo.inverters.some(i => i.id === parseInt(invId));
                    }

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.save();
                        ctx.translate(offsetX, offsetY);
                        ctx.scale(scale, scale);

                        gridTopo.inverters.forEach(inv => {
                            if (inv.transformerId !== null && gridTopo.transformers[inv.transformerId]) {
                                let xf = gridTopo.transformers[inv.transformerId];
                                ctx.strokeStyle = "rgba(255,255,255,0.4)";
                                ctx.lineWidth = 1.5;
                                ctx.beginPath();
                                ctx.moveTo(inv.x, inv.y);
                                ctx.lineTo(xf.x, xf.y);
                                ctx.stroke();
                            }
                        });

                        let counts = {};
                        Object.values(gridTopo.stringGroups).forEach(id => { counts[id] = (counts[id] || 0) + 1; });

                        independentStrings.forEach(s => {
                            let x = s.min_c * CELL; let y = s.min_r * CELL;
                            let w = (s.max_c - s.min_c + 1) * CELL; let h = (s.max_r - s.min_r + 1) * CELL;
                            let linkedInv = gridTopo.stringGroups[s.id];
                            
                            if (linkedInv) {
                                if (isInverterPlaced(linkedInv)) {
                                    ctx.fillStyle = getCapacityColor(counts[linkedInv]); 
                                    ctx.strokeStyle = getCapacityColor(counts[linkedInv]);
                                    ctx.lineWidth = 1.5;
                                } else {
                                    ctx.fillStyle = "#d97706";
                                    ctx.strokeStyle = "#fbbf24";
                                    ctx.lineWidth = 2;
                                }
                            } else {
                                ctx.fillStyle = "#1e293b"; 
                                ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                                ctx.lineWidth = 0.5;
                            }
                            
                            ctx.fillRect(x, y, w, h);
                            ctx.strokeRect(x, y, w, h);

                            if (linkedInv) {
                                ctx.fillStyle = "rgba(0,0,0,0.85)";
                                ctx.fillRect(x + 2, y + 2, 35, 11);
                                ctx.fillStyle = "#ffffff";
                                ctx.font = "bold 7px sans-serif";
                                ctx.fillText("I-" + linkedInv, x + 4, y + 10);
                            }
                        });

                        gridTopo.inverters.forEach(inv => {
                            let strCount = counts[inv.id] || 0;
                            let tsPrefix = "";
                            if (inv.transformerId !== null) {
                                tsPrefix = "TS" + (inv.transformerId + 1) + "-";
                            }
                            let titleText = tsPrefix + "IN" + String(inv.id).padStart(3, '0');
                            let countText = strCount + " STRINGS";

                            ctx.font = "bold 9px sans-serif";
                            let titleW = ctx.measureText(titleText).width + 12;
                            let countW = ctx.measureText(countText).width + 12;
                            let badgeW = Math.max(titleW, countW, 65);
                            let badgeH = 26;

                            let bx = inv.x - (badgeW / 2);
                            let by = inv.y - (badgeH / 2);

                            ctx.fillStyle = "#ff0000";
                            ctx.fillRect(bx, by, badgeW, badgeH / 2);
                            
                            ctx.fillStyle = getCapacityColor(strCount);
                            ctx.fillRect(bx, by + (badgeH / 2), badgeW, badgeH / 2);

                            ctx.fillStyle = "#ffffff";
                            ctx.textAlign = "center";
                            ctx.fillText(titleText, inv.x, by + 9);
                            ctx.fillText(countText, inv.x, by + 21);

                            ctx.strokeStyle = "#ffffff";
                            ctx.lineWidth = 1;
                            ctx.strokeRect(bx, by, badgeW, badgeH);
                        });

                        gridTopo.transformers.forEach((t, i) => {
                            ctx.fillStyle = "#ff1744";
                            ctx.fillRect(t.x - 18, t.y - 18, 36, 36);
                            ctx.strokeStyle = "#ffffff";
                            ctx.lineWidth = 2;
                            ctx.strokeRect(t.x - 18, t.y - 18, 36, 36);
                            
                            ctx.fillStyle = "#ffffff";
                            ctx.font = "bold 10px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("TS " + (i + 1), t.x, t.y + 4);
                        });

                        ctx.restore();

                        if (isSelecting && getActiveTool() === "string") {
                            ctx.strokeStyle = "#a78bfa"; ctx.lineWidth = 1.5;
                            ctx.fillStyle = 'rgba(167, 139, 250, 0.2)';
                            ctx.fillRect(startX, startY, currX - startX, currY - startY);
                            ctx.strokeRect(startX, startY, currX - startX, currY - startY);
                        }
                    }

                    function getMouseLocation(e) {
                        const rect = canvas.getBoundingClientRect();
                        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
                    }

                    function transformToWorldSpace(p) {
                        return { x: (p.x - offsetX) / scale, y: (p.y - offsetY) / scale };
                    }

                    canvas.addEventListener("mousedown", e => {
                        const m = getMouseLocation(e);
                        const world = transformToWorldSpace(m);
                        const tool = getActiveTool();

                        if (e.button === 2) {
                            if (tool === "inverter") {
                                gridTopo.inverters = gridTopo.inverters.filter(inv => {
                                    let isHit = Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 20;
                                    if (isHit) {
                                        Object.keys(gridTopo.stringGroups).forEach(key => {
                                            if (gridTopo.stringGroups[key] === inv.id) delete gridTopo.stringGroups[key];
                                        });
                                    }
                                    return !isHit;
                                });
                                draw(); return;
                            }
                            if (tool === "transformer") {
                                gridTopo.transformers = gridTopo.transformers.filter((t, idx) => {
                                    let match = Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 25;
                                    if (match) {
                                        gridTopo.inverters.forEach(i => { if (i.transformerId === idx) i.transformerId = null; });
                                    }
                                    return !match;
                                });
                                draw(); return;
                            }
                            
                            isPanning = true;
                            startX = e.clientX - offsetX;
                            startY = e.clientY - offsetY;
                            canvas.style.cursor = "move";
                            return;
                        }

                        if (tool === "pan") {
                            isPanning = true;
                            startX = e.clientX - offsetX;
                            startY = e.clientY - offsetY;
                            canvas.style.cursor = "move";
                        } else if (tool === "string") {
                            isSelecting = true;
                            startX = m.x; startY = m.y;
                            currX = m.x; currY = m.y;
                        } else if (tool === "inverter") {
                            let hitStruct = databaseStructures.find(b => {
                                let sx = b.min_c * CELL, sy = b.min_r * CELL;
                                let sw = (b.max_c - b.min_c + 1) * CELL, sh = (b.max_r - b.min_r + 1) * CELL;
                                return world.x >= sx && world.x <= sx + sw && world.y >= sy && world.y <= sy + sh;
                            });

                            if (hitStruct) {
                                let invId = parseInt(document.getElementById("topo_inv_token").value) || 20;
                                gridTopo.inverters = gridTopo.inverters.filter(i => i.id !== invId);
                                
                                let structW = (hitStruct.max_c - hitStruct.min_c + 1) * CELL;
                                let structH = (hitStruct.max_r - hitStruct.min_r + 1) * CELL;
                                
                                gridTopo.inverters.push({
                                    id: invId,
                                    x: (hitStruct.min_c * CELL) + (structW / 2),
                                    y: (hitStruct.min_r * CELL) + (structH / 2),
                                    transformerId: null
                                });
                                draw();
                            }
                        } else if (tool === "transformer") {
                            let hitString = independentStrings.find(s => {
                                let sx = s.min_c * CELL, sy = s.min_r * CELL;
                                return world.x >= sx && world.x <= sx + ((s.max_c - s.min_c + 1) * CELL) &&
                                       world.y >= sy && world.y <= sy + ((s.max_r - s.min_r + 1) * CELL);
                            });
                            if (!hitString) {
                                gridTopo.transformers.push({ x: world.x, y: world.y });
                                draw();
                            }
                        } else if (tool === "route") {
                            let invIdx = gridTopo.inverters.findIndex(i => Math.sqrt(Math.pow(world.x - i.x, 2) + Math.pow(world.y - i.y, 2)) <= 25);
                            if (invIdx !== -1) {
                                selectedInverterIndexForRouting = invIdx;
                                tooltip.style.display = "block";
                                tooltip.innerHTML = "🎯 <b>Inverter Targeted</b>: Choose target Transformer box station destination node.";
                            } else if (selectedInverterIndexForRouting !== null) {
                                let xfmrIdx = gridTopo.transformers.findIndex(t => Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 25);
                                if (xfmrIdx !== -1) {
                                    gridTopo.inverters[selectedInverterIndexForRouting].transformerId = xfmrIdx;
                                    selectedInverterIndexForRouting = null;
                                    draw();
                                }
                            }
                        }
                    });

                    canvas.addEventListener("mousemove", e => {
                        const m = getMouseLocation(e);
                        const world = transformToWorldSpace(m);

                        if (isPanning) {
                            offsetX = e.clientX - startX;
                            offsetY = e.clientY - startY;
                            draw(); return;
                        } else if (isSelecting) {
                            currX = m.x; currY = m.y;
                            draw(); return;
                        }

                        let matchFound = false;

                        gridTopo.transformers.forEach((t, index) => {
                            if (Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 25) {
                                let connectedInvs = gridTopo.inverters.filter(i => i.transformerId === index).map(i => "INV " + i.id).join(", ");
                                tooltip.style.display = "block";
                                tooltip.style.left = (m.x + 15) + "px";
                                tooltip.style.top = (m.y + 15) + "px";
                                tooltip.innerHTML = `<b>🏪 Transformer Hub</b><br>Station: TS ${index + 1}<br>Fed by Inverters: [ ${connectedInvs || 'None'} ]`;
                                matchFound = true;
                            }
                        });

                        if (!matchFound) {
                            gridTopo.inverters.forEach(inv => {
                                if (Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 25) {
                                    tooltip.style.display = "block";
                                    tooltip.style.left = (m.x + 15) + "px";
                                    tooltip.style.top = (m.y + 15) + "px";
                                    tooltip.innerHTML = `<b>⚡ Inverter Badge</b><br>Inverter ID: INV #${inv.id}<br>Routed Station: ${inv.transformerId !== null ? 'TS ' + (inv.transformerId + 1) : 'Unassigned Route'}`;
                                    matchFound = true;
                                }
                            });
                        }

                        if (!matchFound) {
                            let s = independentStrings.find(s => {
                                let sx = s.min_c * CELL, sy = s.min_r * CELL;
                                return world.x >= sx && world.x <= sx + ((s.max_c - s.min_c + 1) * CELL) &&
                                       world.y >= sy && world.y <= sy + ((s.max_r - s.min_r + 1) * CELL);
                            });

                            if (s) {
                                tooltip.style.display = "block";
                                tooltip.style.left = (m.x + 15) + "px";
                                tooltip.style.top = (m.y + 15) + "px";
                                
                                let invRef = gridTopo.stringGroups[s.id] || "None Assigned";
                                let xfmrRef = "None Assigned";
                                if (invRef !== "None Assigned") {
                                    let invObj = gridTopo.inverters.find(i => i.id === parseInt(invRef));
                                    if (invObj && invObj.transformerId !== null) xfmrRef = "TS " + (invObj.transformerId + 1);
                                }

                                tooltip.innerHTML = `<b>☀️ Tracker Table String</b><br>Table Label: ${s.label}<br>Zone ID: ${s.zone}<br>Connected Inverter: ${invRef}<br>Connected Transformer: ${xfmrRef}`;
                                matchFound = true;
                            }
                        }

                        if (!matchFound && selectedInverterIndexForRouting === null) tooltip.style.display = "none";
                    });

                    canvas.addEventListener("mouseup", e => {
                        if (e.button === 2) { isPanning = false; canvas.style.cursor = "default"; return; }
                        if (isPanning) { isPanning = false; canvas.style.cursor = "default"; return; }
                        if (isSelecting) {
                            isSelecting = false;
                            const mUp = getMouseLocation(e);
                            const p1 = transformToWorldSpace(getMouseLocation({ clientX: startX + canvas.getBoundingClientRect().left, clientY: startY + canvas.getBoundingClientRect().top }));
                            const p2 = transformToWorldSpace(mUp);

                            let boxX1 = Math.min(p1.x, p2.x), boxX2 = Math.max(p1.x, p2.x);
                            let boxY1 = Math.min(p1.y, p2.y), boxY2 = Math.max(p1.y, p2.y);
                            
                            let totalDragDistance = Math.sqrt(Math.pow(mUp.x - startX, 2) + Math.pow(mUp.y - startY, 2));
                            let activeInv = parseInt(document.getElementById("topo_inv_token").value) || 20;
                            let isLassoSelection = totalDragDistance > 5;
                            
                            let boxSelected = independentStrings.filter(s => {
                                let cx = s.min_c * CELL; let cy = s.min_r * CELL;
                                let cw = (s.max_c - s.min_c + 1) * CELL; let ch = (s.max_r - s.min_r + 1) * CELL;
                                
                                if (!isLassoSelection) {
                                    return (boxX1 >= cx && boxX1 <= cx + cw && boxY1 >= cy && boxY1 <= cy + ch);
                                } else {
                                    return (cx >= boxX1 && cx <= boxX2 && cy >= boxY1 && cy <= boxY2);
                                }
                            });

                            if (boxSelected.length > 0) {
                                boxSelected.forEach(el => {
                                    let currentAssign = gridTopo.stringGroups[el.id];
                                    
                                    if (currentAssign && currentAssign !== activeInv) {
                                        return; 
                                    }

                                    if (isLassoSelection) {
                                        gridTopo.stringGroups[el.id] = activeInv;
                                    } else {
                                        if (currentAssign === activeInv) {
                                            delete gridTopo.stringGroups[el.id]; 
                                        } else {
                                            gridTopo.stringGroups[el.id] = activeInv;
                                        }
                                    }
                                });
                                draw();
                            }
                        }
                    });

                    canvas.addEventListener("wheel", e => {
                        e.preventDefault();
                        const m = getMouseLocation(e); const world = transformToWorldSpace(m);
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.01, Math.min(scale, 20));
                        offsetX = m.x - world.x * scale; offsetY = m.y - world.y * scale; draw();
                    }, { passive: false });

                    document.getElementById("btn_flush_routes").addEventListener("click", () => {
                        if (confirm("Disconnect layout line strings routes safely?")) {
                            gridTopo.inverters.forEach(i => i.transformerId = null); draw();
                        }
                    });
                    document.getElementById("btn_flush_inverters").addEventListener("click", () => {
                        if (confirm("Flush custom configured inverter nodes?")) {
                            gridTopo.inverters = []; gridTopo.stringGroups = {}; draw();
                        }
                    });
                    document.getElementById("btn_flush_transformers").addEventListener("click", () => {
                        if (confirm("Flush transformer stations?")) {
                            gridTopo.transformers = []; gridTopo.inverters.forEach(i => i.transformerId = null); draw();
                        }
                    });

                    document.getElementById("btn_topo_save").addEventListener("click", async () => {
                        const saveBtn = document.getElementById("btn_topo_save");
                        saveBtn.innerText = "⏳ Saving Topology...";
                        try {
                            await fetch("SUPABASE_URL_VAL/rest/v1/farms?id=eq.ACTIVE_SITE_ID_VAL", {
                                method: "PATCH",
                                headers: {
                                    "apikey": "SUPABASE_KEY_VAL",
                                    "Authorization": "Bearer SUPABASE_KEY_VAL",
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({ background_image_url: JSON.stringify(gridTopo) })
                            });
                            saveBtn.innerText = "🎉 Saved to Cloud Database!";
                            setTimeout(() => { saveBtn.innerText = "💾 Save Workspace Topologies"; }, 2500);
                        } catch (err) {
                            saveBtn.innerText = "❌ Sync Failure";
                        }
                    });

                    draw();
                })();
            </script>
            """
            html_topology_workspace = html_topology_workspace.replace("__JSON_DATA_B64__", b64_json_data)\
                                                             .replace("__TOPOLOGY_METADATA_B64__", base64.b64encode(stored_metadata_string.encode("utf-8")).decode("utf-8"))\
                                                             .replace("MIN_C_VAL", str(min_c))\
                                                             .replace("MAX_C_VAL", str(max_c))\
                                                             .replace("MIN_R_VAL", str(min_r))\
                                                             .replace("MAX_R_VAL", str(max_r))\
                                                             .replace("SUPABASE_URL_VAL", SUPABASE_URL)\
                                                             .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)\
                                                             .replace("ACTIVE_SITE_ID_VAL", str(st.session_state.active_site_id))
            
            components.html(html_topology_workspace, height=660)

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (CREW WORKSPACE VIEWS)
        # ==============================================================================
        if site_bg_img and not site_bg_img.startswith("{"):
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
                    ⚙️ <b>Crew Controls:</b> 
                    <span style="color:#22c55e; font-weight:bold;">Left-Click + Drag</span> to multi-select cell blocks &nbsp;|&nbsp; 
                    <span style="color:#38bdf8; font-weight:bold;">Right-Click + Drag</span> to pan map &nbsp;|&nbsp; 
                    <span style="color:#eab308; font-weight:bold;">Single Left-Click</span> to complete a single section &nbsp;|&nbsp;
                    <span style="color:#a78bfa; font-weight:bold;">Scroll</span> to zoom.
                    <div id="crew_sync_status_msg" style="color:#22c55e; font-weight:bold; display:none; margin-top:4px;">Transmitting field records...</div>
                </div>
                
                <div id="crew_hover_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #22c55e; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-weight: bold;"></div>

                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="crew_LAYER_KEY" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); 
                    const canvas = document.getElementById("crew_LAYER_KEY"); 
                    const ctx = canvas.getContext('2d');
                    const tooltip = document.getElementById("crew_hover_tooltip");
                    const CELL = 14; 
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL; 
                    const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    
                    let isPanning = false;
                    let isSelecting = false;
                    let dragStartRawX = 0, dragStartRawY = 0;
                    let dragCurrentRawX = 0, dragCurrentRawY = 0;

                    canvas.addEventListener('contextmenu', e => e.preventDefault());

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); 
                        ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        
                        blocks.forEach(b => {
                            ctx.fillStyle = b['LAYER_KEY_status'] === 'completed' ? '#22c55e' : '#3b82f6';
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); 
                            ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h);
                        });
                        ctx.restore();

                        if (isSelecting) {
                            ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 2;
                            ctx.fillStyle = 'rgba(34, 197, 94, 0.25)';
                            ctx.fillRect(dragStartRawX, dragStartRawY, dragCurrentRawX - dragStartRawX, dragCurrentRawY - dragStartRawY);
                            ctx.strokeRect(dragStartRawX, dragStartRawY, dragCurrentRawX - dragStartRawX, dragCurrentRawY - dragStartRawY);
                        }
                    }

                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const mX = e.clientX - rect.left;
                        const mY = e.clientY - rect.top;
                        
                        if (isPanning) {
                            offsetX = e.clientX - dragStartRawX;
                            offsetY = e.clientY - dragStartRawY;
                            draw();
                            tooltip.style.display = "none";
                            return;
                        } else if (isSelecting) {
                            dragCurrentRawX = mX;
                            dragCurrentRawY = mY;
                            draw();
                            tooltip.style.display = "none";
                            return;
                        }

                        let worldX = (mX - offsetX) / scale;
                        let worldY = (mY - offsetY) / scale;
                        
                        let hoveredBlock = null;
                        for (let b of blocks) {
                            if (worldX >= b.min_c * CELL && worldX <= (b.max_c + 1) * CELL && worldY >= b.min_r * CELL && worldY <= (b.max_r + 1) * CELL) { hoveredBlock = b; break; }
                        }

                        if (hoveredBlock) {
                            tooltip.style.display = "block";
                            tooltip.style.left = (mX + 15) + "px";
                            tooltip.style.top = (mY + 15) + "px";
                            tooltip.innerHTML = `Label: ${hoveredBlock.table_label}<br/>Zone: ${hoveredBlock.assigned_zone}<br/>Status: ${hoveredBlock['LAYER_KEY_status'] || 'pending'}`;
                        } else {
                            tooltip.style.display = "none";
                        }
                    });

                    canvas.addEventListener('mousedown', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const clickX = e.clientX - rect.left;
                        const clickY = e.clientY - rect.top;

                        if (e.button === 2) { 
                            isPanning = true;
                            isSelecting = false;
                            dragStartRawX = e.clientX - offsetX;
                            dragStartRawY = e.clientY - offsetY;
                            canvas.style.cursor = 'move';
                        } else if (e.button === 0) { 
                            isSelecting = true;
                            isPanning = false;
                            dragStartRawX = clickX;
                            dragStartRawY = clickY;
                            dragCurrentRawX = clickX;
                            dragCurrentRawY = clickY;
                            canvas.style.cursor = 'crosshair';
                        }
                        tooltip.style.display = "none";
                    });

                    canvas.addEventListener('mouseup', async (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const mouseUpX = e.clientX - rect.left;
                        const mouseUpY = e.clientY - rect.top;

                        if (isPanning) {
                            isPanning = false;
                            canvas.style.cursor = 'grab';
                        } else if (isSelecting) {
                            isSelecting = false;
                            canvas.style.cursor = 'default';

                            let boxX1 = Math.min(dragStartRawX, mouseUpX);
                            let boxX2 = Math.max(dragStartRawX, mouseUpX);
                            let boxY1 = Math.min(dragStartRawY, mouseUpY);
                            let boxY2 = Math.max(dragStartRawY, mouseUpY);

                            let totalDragDistance = Math.sqrt(Math.pow(mouseUpX - dragStartRawX, 2) + Math.pow(mouseUpY - dragStartRawY, 2));
                            let payloadIds = [];

                            blocks.forEach(b => {
                                let cx = b.min_c * CELL * scale + offsetX; let cy = b.min_r * CELL * scale + offsetY;
                                let isMatched = (totalDragDistance > 4) ? (cx >= boxX1 && cx <= boxX2 && cy >= boxY1 && cy <= boxY2) : (boxX1 >= cx && boxX1 <= (b.max_c * CELL * scale + offsetX) && boxY1 >= cy && boxY1 <= (b.max_r * CELL * scale + offsetY));
                                if (isMatched && b['LAYER_KEY_status'] !== 'completed') {
                                    payloadIds.push(b.id);
                                }
                            });
                            
                            if (payloadIds.length > 0) {
                                const statMsg = document.getElementById("crew_sync_status_msg");
                                statMsg.style.display = "block";
                                statMsg.innerText = `Synchronizing ${payloadIds.length} blocks to database...`;
                                
                                try {
                                    for (let id of payloadIds) {
                                        let target = blocks.find(b => b.id === id);
                                        if (target) target['LAYER_KEY_status'] = 'completed';
                                        
                                        await fetch('SUPABASE_URL_VAL/rest/v1/structures?id=eq.' + id, {
                                            method: "PATCH", 
                                            headers: { 
                                                "apikey": 'SUPABASE_KEY_VAL', 
                                                "Authorization": 'Bearer SUPABASE_KEY_VAL', 
                                                "Content-Type": "application/json",
                                                "Prefer": "return=minimal"
                                            },
                                            body: JSON.stringify({ "LAYER_KEY_status": "completed", "LAYER_KEY_date": "TODAY_STR_VAL" })
                                        });
                                    }
                                    statMsg.innerText = "Sync Complete! Click the top reload button to update map view colors.";
                                    setTimeout(() => { statMsg.style.display = "none"; }, 5000);
                                } catch (e) {
                                    statMsg.innerText = "Database updates timed out.";
                                }
                            }
                            setTimeout(draw, 50);
                        }
                    });

                    canvas.addEventListener('wheel', (e) => {
                        e.preventDefault(); 
                        const rect = canvas.getBoundingClientRect(); 
                        const mouseX = e.clientX - rect.left; 
                        const mouseY = e.clientY - rect.top;
                        const gridX = (mouseX - offsetX) / scale; 
                        const gridY = (mouseY - offsetY) / scale;
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85); 
                        scale = Math.max(0.01, Math.min(scale, 15));
                        offsetX = mouseX - gridX * scale; 
                        offsetY = mouseY - gridY * scale; 
                        draw();
                    }, { passive: false });

                    draw();
                })();
            </script>
            """
            html_crew_map = html_crew_map.replace("__JSON_DATA_B64__", b64_data)\
                                         .replace("LAYER_KEY", str(layer_key)) \
                                         .replace("MIN_C_VAL", str(min_c)) \
                                         .replace("MAX_C_VAL", str(max_c)) \
                                         .replace("MIN_R_VAL", str(min_r)) \
                                         .replace("MAX_R_VAL", str(max_r)) \
                                         .replace("TODAY_STR_VAL", today_str) \
                                         .replace("SUPABASE_URL_VAL", SUPABASE_URL) \
                                         .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            return html_crew_map

        def process_crew_tab(tab_obj, key_val):
            with tab_obj:
                components.html(inject_crew_tracking_map(key_val, b64_json_data, min_c, max_c, min_r, max_r), height=640)

        process_crew_tab(crew_tabs[0], "pegging")
        process_crew_tab(crew_tabs[1], "piling")
        process_crew_tab(crew_tabs[2], "mounting")
        process_crew_tab(crew_tabs[3], "modules")
