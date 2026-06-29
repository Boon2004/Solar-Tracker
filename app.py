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

@st.cache_data(ttl=2)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("id, name, admin_password, installer_password, is_published").order("name").execute()
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
                    st.info("🔄 Running Grid Matrix Extraction Scanner...")
                    with st.spinner("Processing structural frames..."):
                        wb = openpyxl.load_workbook(uploaded_blueprint, data_only=True)
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
                            visited = set()
                            table_counter = 1
                            structures_queue = []
                            ROAD_GAP = 2 

                            for r in range(1, max_rows + 1):
                                for c in range(1, max_cols + 1):
                                    cell = sheet.cell(row=r, column=c)
                                    is_active_cell = False
                                    
                                    if cell.value is not None and str(cell.value).strip() != "":
                                        is_active_cell = True
                                    elif cell.fill and cell.fill.fill_type is not None and cell.fill.fill_type != 'none':
                                        is_active_cell = True
                                    elif cell.border and ((cell.border.top and cell.border.top.style) or 
                                                         (cell.border.bottom and cell.border.bottom.style) or 
                                                         (cell.border.left and cell.border.left.style) or 
                                                         (cell.border.right and cell.border.right.style)): 
                                        is_active_cell = True
                                    
                                    if is_active_cell and (r, c) not in visited:
                                        block_cells = []
                                        queue = [(r, c)]
                                        visited.add((r, c))
                                        discovered_label = ""

                                        while queue:
                                            curr_r, curr_c = queue.pop(0)
                                            block_cells.append((curr_r, curr_c))

                                            v_cell = sheet.cell(row=curr_r, column=curr_c).value
                                            if v_cell and not discovered_label and not str(v_cell).strip().isdigit():
                                                discovered_label = str(v_cell).strip()

                                            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                                                nr, nc = curr_r + dr, curr_c + dc
                                                if 1 <= nr <= max_rows and 1 <= nc <= max_cols and (nr, nc) not in visited:
                                                    n_cell = sheet.cell(row=nr, column=nc)
                                                    n_active = False
                                                    if n_cell.value is not None and str(n_cell.value).strip() != "":
                                                        n_active = True
                                                    elif n_cell.fill and n_cell.fill.fill_type is not None and n_cell.fill.fill_type != 'none':
                                                        n_active = True
                                                    elif n_cell.border and ((n_cell.border.top and n_cell.border.top.style) or 
                                                                         (n_cell.border.bottom and n_cell.border.bottom.style) or 
                                                                         (n_cell.border.left and n_cell.border.left.style) or 
                                                                         (n_cell.border.right and n_cell.border.right.style)): 
                                                        n_active = True
                                                        
                                                    if n_active:
                                                        visited.add((nr, nc))
                                                        queue.append((nr, nc))
                                                        
                                        b_rows = [pt[0] for pt in cluster_cells] if 'cluster_cells' in locals() else [item[0] for item in block_cells]
                                        b_cols = [pt[1] for pt in cluster_cells] if 'cluster_cells' in locals() else [item[1] for item in block_cells]
                                        min_br, max_br, min_bc, max_bc = min(b_rows), max(b_rows), min(b_cols), max(b_cols)
                                        
                                        h_cells = max_br - min_br + 1
                                        w_cells = max_bc - min_bc + 1

                                        if h_cells >= 2 and w_cells >= 2:
                                            structures_queue.append({
                                                "farm_id": new_fid, 
                                                "table_label": discovered_label if discovered_label else f"T-{table_counter}",
                                                "min_r": int(min_br), "max_r": int(max_br), "min_c": int(min_bc), "max_c": int(max_bc),
                                                "structure_type": "double_6x9" if h_cells >= 5 else "single_3x9",
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
            custom_tab_name = st.text_input("Assign New Tracker Tab Label:", placeholder="e.g. Floating Cell...")
            if st.button("✨ Instantiate Phase Tab") and custom_tab_name:
                if custom_tab_name not in st.session_state.custom_tabs:
                    st.session_state.custom_tabs.append(custom_tab_name)
                    st.success(f"Instantiated '{custom_tab_name}'!")
                    time.sleep(0.4); st.rerun()
                    
            if st.button("🔒 Revoke Admin Clearances"): st.session_state.is_admin_mode = False; st.rerun()

    @st.cache_data(ttl=1)
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

    if not site_is_published and not st.session_state.is_admin_mode:
        st.write("---")
        st.warning("🚧 **Configuration Incomplete:** This project site layout layout is currently hidden. Please wait for an authorized Administrator to finalize initial setup phases.")
        st.stop()

    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs([
            "🖼️ Step 1: Base Overview & Zone Assignation", 
            "🔌 Step 2: Electrical Inverter Mapping", 
            "📌 Step 3: Pegging & Piling Customizer",
            "🏪 Step 4: Transformer Drop Hubs"
        ])
        
        # --- STAGE 1: SETUPS OVERVIEW & ZONE ASSIGNATION ---
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
                        
            if st.button("🔄 Clear All Allocated Zones & Reset Assignment Fleet", type="secondary"):
                with st.spinner("Flushing master zoning allocations..."):
                    try:
                        supabase.table("structures").update({"assigned_zone": "Unassigned"}).eq("farm_id", st.session_state.active_site_id).execute()
                        st.success("Fleet master assignments wiped cleanly!")
                        time.sleep(0.5); st.rerun()
                    except Exception as e:
                        st.error(f"Reset dropped: {str(e)}")

            html_zone_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none;">
                <div style="color: #64748b; font-size: 13px; margin-bottom: 8px;">🖱️ <b>Controls:</b> Drag to <b>Scroll/Pan</b> | Mouse Wheel to <b>Zoom</b> | <kbd style="background:#1e293b; padding:2px 5px; border-radius:3px; color:#f1f5f9;">Shift</kbd> + Drag to <b>Box/Marquee Select Whole Sections Together</b>.</div>
                
                <div id="dialogue_overlay" style="display:none; position:absolute; bottom:35px; left:50%; transform:translateX(-50%); background:#1e293b; padding:18px 35px; border-radius:8px; border:2px solid #38bdf8; z-index:100000; box-shadow: 0 10px 40px rgba(0,0,0,0.85); font-family:sans-serif; text-align:center;">
                    <div style="color:#f1f5f9; font-weight:bold; margin-bottom:14px; font-size:15px;">Assign Selected Section Cluster to <span id="lbl_zone" style="color:#38bdf8; text-decoration:underline;"></span>?</div>
                    <button id="btn_yes" style="background:#22c55e; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; margin-right:12px; font-size:14px;">Yes, Stage Change</button>
                    <button id="btn_no" style="background:#ef4444; color:white; border:none; padding:8px 22px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:14px;">No</button>
                </div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="zone_canvas" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    const canvas = document.getElementById("zone_canvas");
                    const ctx = canvas.getContext('2d');
                    const paintZone = "PAINT_ZONE_VAL";
                    const CELL = CELL_SIZE_VAL;
                    
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL;
                    const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);

                    let isDragging = false, isSelecting = false;
                    let startX, startY, currentX, currentY;
                    let stagedBlockIds = [];

                    function getZoneColor(zoneName) {
                        if (!zoneName || zoneName.toLowerCase() === 'unassigned' || zoneName.trim() === '') return '#334155';
                        let hash = 0; for (let i = 0; i < zoneName.length; i++) { hash = zoneName.charCodeAt(i) + ((hash << 5) - hash); }
                        return `hsl(${Math.abs(hash % 360)}, 90%, 50%)`;
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
                            if (isStaged) { ctx.strokeStyle = '#ffff00'; ctx.lineWidth = 2.5; ctx.strokeRect(x, y, w, h); }
                        });
                        ctx.restore();

                        // Render the screen-space transparent selection marquee indicator overlay
                        if (isSelecting) {
                            ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2;
                            ctx.fillStyle = 'rgba(56, 189, 248, 0.2)';
                            ctx.fillRect(startX, startY, currentX - startX, currentY - startY);
                            ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
                        }
                    }

                    canvas.addEventListener('mousedown', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        startX = e.clientX - rect.left;
                        startY = e.clientY - rect.top;
                        
                        if (e.shiftKey) {
                            isSelecting = true;
                            isDragging = false;
                            currentX = startX;
                            currentY = startY;
                        } else {
                            isDragging = true;
                            isSelecting = false;
                            startX = e.clientX - offsetX;
                            startY = e.clientY - startY;
                        }
                    });

                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        if (isDragging) {
                            offsetX = e.clientX - startX;
                            offsetY = e.clientY - startY;
                            draw();
                        } else if (isSelecting) {
                            currentX = e.clientX - rect.left;
                            currentY = e.clientY - rect.top;
                            draw();
                        }
                    });

                    window.addEventListener('mouseup', (e) => {
                        if (isDragging) {
                            isDragging = false;
                        } else if (isSelecting) {
                            isSelecting = false;
                            
                            // Process elements mapped within the custom marquee selection box array coordinates
                            let x1 = (Math.min(startX, currentX) - offsetX) / scale;
                            let x2 = (Math.max(startX, currentX) - offsetX) / scale;
                            let y1 = (Math.min(startY, currentY) - offsetY) / scale;
                            let y2 = (Math.max(startY, currentY) - offsetY) / scale;

                            stagedBlockIds = [];
                            blocks.forEach(b => {
                                let bx = b.min_c * CELL + ((b.max_c - b.min_c + 1) * CELL / 2);
                                let by = b.min_r * CELL + ((b.max_r - b.min_r + 1) * CELL / 2);
                                if (bx >= x1 && bx <= x2 && by >= y1 && by <= y2) {
                                    stagedBlockIds.push(b.id);
                                }
                            });

                            if (stagedBlockIds.length > 0) {
                                document.getElementById("lbl_zone").innerText = paintZone;
                                document.getElementById("dialogue_overlay").style.display = "block";
                            }
                            draw();
                        }
                    });

                    // Add support for simple single clicks
                    canvas.addEventListener('click', (e) => {
                        if (e.shiftKey) return;
                        const rect = canvas.getBoundingClientRect();
                        const clX = (e.clientX - rect.left - offsetX) / scale;
                        const clY = (e.clientY - rect.top - offsetY) / scale;
                        
                        let target = null;
                        blocks.forEach(b => {
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            if (clX >= x && clX <= x + w && clY >= y && clY <= y + h) target = b;
                        });

                        if (target) {
                            stagedBlockIds = [target.id];
                            document.getElementById("lbl_zone").innerText = paintZone;
                            document.getElementById("dialogue_overlay").style.display = "block";
                            draw();
                        }
                    });

                    document.getElementById("btn_yes").addEventListener('click', () => {
                        stagedBlockIds.forEach(id => {
                            let target = blocks.find(b => b.id === id); 
                            if (target) target.assigned_zone = paintZone;
                            fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq." + id, {
                                method: "PATCH", headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json" },
                                body: JSON.stringify({ "assigned_zone": paintZone })
                            });
                        });
                        stagedBlockIds = []; document.getElementById("dialogue_overlay").style.display = "none"; draw();
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
                                                 .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            components.html(html_zone_engine, height=700)

        # --- STAGE 2: INVERTER SETUP WITH FACING SPLIT ENGINE ---
        with setup_tabs[1]:
            st.markdown("### 🔌 Electrical Inverter Infrastructure Integration Node")
            html_inverter_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none;">
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="inv_canvas" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() { 
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); const canvas = document.getElementById("inv_canvas"); const ctx = canvas.getContext('2d'); const CELL = CELL_SIZE_VAL;
                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isDragging = false, startX, startY;

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => { 
                            ctx.fillStyle = '#3b82f6'; let x = b.min_c * CELL; let y = b.min_r * CELL; 
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); 
                            ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h); 
                            if (b.structure_type === 'double_6x9') {
                                ctx.strokeStyle = '#ff007f'; ctx.lineWidth = 2.0;
                                ctx.beginPath(); ctx.moveTo(x, y + (h / 2)); ctx.lineTo(x + w, y + (h / 2)); ctx.stroke();
                            }
                        }); 
                        ctx.restore();
                    }
                    canvas.addEventListener('mousedown', (e) => { isDragging = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; });
                    canvas.addEventListener('mousemove', (e) => { if (!isDragging) return; offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); });
                    window.addEventListener('mouseup', () => { isDragging = false; });
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
            html_inverter_engine = html_inverter_engine.replace("__JSON_DATA_B64__", b64_json_data)\
                                                       .replace("CELL_SIZE_VAL", str(CELL_SIZE))\
                                                       .replace("MIN_C_VAL", str(min_c))\
                                                       .replace("MAX_C_VAL", str(max_c))\
                                                       .replace("MIN_R_VAL", str(min_r))\
                                                       .replace("MAX_R_VAL", str(max_r))
            components.html(html_inverter_engine, height=640)

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

        # --- STAGE 4: TRANSFORMER HUB PLACEMENT MAP ---
        with setup_tabs[3]:
            st.markdown("### 🏪 Transformer Station Network Grid Loop Nodes")
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

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isDragging = false, startX, startY;

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => { 
                            ctx.fillStyle = '#64748b'; let x = b.min_c * CELL; let y = b.min_r * CELL; 
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h); 
                        }); 
                        ctx.restore();
                    }
                    canvas.addEventListener('mousedown', (e) => { isDragging = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; });
                    canvas.addEventListener('mousemove', (e) => { if (!isDragging) return; offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); });
                    window.addEventListener('mouseup', () => { isDragging = false; });
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
            html_transformer_engine = html_transformer_engine.replace("__JSON_DATA_B64__", b64_json_data)\
                                                             .replace("CELL_SIZE_VAL", str(CELL_SIZE))\
                                                             .replace("MIN_C_VAL", str(min_c))\
                                                             .replace("MAX_C_VAL", str(max_c))\
                                                             .replace("MIN_R_VAL", str(min_r))\
                                                             .replace("MAX_R_VAL", str(max_r))
            components.html(html_transformer_engine, height=640)

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (CREW WORKSPACE VIEWS)
        # ==============================================================================
        crew_tabs = st.tabs([
            "📌 Pegging Phase", "🪵 Piling Operations", "🏗️ Mounting Structures", "☀️ PV Module Tracking"
        ] + [f"🛠️ {ct}" for ct in st.session_state.custom_tabs])

        def inject_crew_tracking_map(layer_key, b64_data, min_c, max_c, min_r, max_r):
            today_str = str(date.today())

            html_crew_map = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none;">
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="crew_LAYER_KEY" width="1500" height="600" style="background:#020617; display:block; cursor:grab;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const blocks = JSON.parse(atob("__JSON_DATA_B64__")); const canvas = document.getElementById("crew_LAYER_KEY"); const ctx = canvas.getContext('2d');
                    const CELL = 14; let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL; const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 60) / mapWidth, (canvas.height - 60) / mapHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;
                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);
                    let isDragging = false, moved = false, startX, startY;

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
                        blocks.forEach(b => {
                            ctx.fillStyle = b['LAYER_KEY_status'] === 'completed' ? '#22c55e' : '#3b82f6';
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            ctx.fillRect(x, y, w, h); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h);
                        });
                        ctx.restore();
                    }
                    canvas.addEventListener('click', (e) => {
                        if (moved) return;
                        const rect = canvas.getBoundingClientRect(); 
                        const cx = (e.clientX - rect.left - offsetX) / scale; const cy = (e.clientY - rect.top - offsetY) / scale;
                        blocks.forEach(b => {
                            let x = b.min_c * CELL; let y = b.min_r * CELL;
                            let w = (b.max_c - b.min_c + 1) * CELL; let h = (b.max_r - b.min_r + 1) * CELL;
                            if (cx >= x && cx <= x + w && cy >= y && cy <= y + h) {
                                b['LAYER_KEY_status'] = 'completed';
                                const p = {}; p['LAYER_KEY_status'] = 'completed'; p['LAYER_KEY_date'] = 'TODAY_STR_VAL';
                                fetch('SUPABASE_URL_VAL/rest/v1/structures?id=eq.' + b.id, {
                                    method: "PATCH", headers: { "apikey": 'SUPABASE_KEY_VAL', "Authorization": 'Bearer SUPABASE_KEY_VAL', "Content-Type": "application/json" },
                                    body: JSON.stringify(p)
                                }).then(() => draw());
                            }
                        });
                    });
                    canvas.addEventListener('mousedown', (e) => { isDragging = true; moved = false; startX = e.clientX - offsetX; startY = e.clientY - offsetY; });
                    canvas.addEventListener('mousemove', (e) => { if (!isDragging) return; moved = true; offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); });
                    window.addEventListener('mouseup', () => { isDragging = false; });
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
            html_crew_map = html_crew_map.replace("__JSON_DATA_B64__", b64_data)\
                                         .replace("LAYER_KEY", str(layer_key))\
                                         .replace("MIN_C_VAL", str(min_c))\
                                         .replace("MAX_C_VAL", str(max_c))\
                                         .replace("MIN_R_VAL", str(min_r))\
                                         .replace("MAX_R_VAL", str(max_r))\
                                         .replace("TODAY_STR_VAL", today_str)\
                                         .replace("SUPABASE_URL_VAL", SUPABASE_URL)\
                                         .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            return html_crew_map

        def process_crew_tab(tab_obj, key_val):
            with tab_obj:
                components.html(inject_crew_tracking_map(key_val, b64_json_data, min_c, max_c, min_r, max_r), height=640)

        process_crew_tab(crew_tabs[0], "pegging")
        process_crew_tab(crew_tabs[1], "piling")
        process_crew_tab(crew_tabs[2], "mounting")
        process_crew_tab(crew_tabs[3], "modules")
