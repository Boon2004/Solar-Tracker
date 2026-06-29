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
                                time.sleep(1); st.rerun()

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
    with col_h1: st.subheader(f"📍 Boon Solar Tracking — {st.session_state.active_site_name}")
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
                if "confirm_publish_gate" not in st.session_state: st.session_state.confirm_publish_gate = False
                if not st.session_state.confirm_publish_gate:
                    if st.button("🚀 Publish Layout to Crew", type="primary"):
                        st.session_state.confirm_publish_gate = True; st.rerun()
                else:
                    st.error("🔒 Confirm permanent lock?")
                    col_lock1, col_lock2 = st.columns(2)
                    with col_lock1:
                        if st.button("🔒 DEPLOY", type="primary", use_container_width=True):
                            supabase.table("farms").update({"is_published": True}).eq("id", st.session_state.active_site_id).execute()
                            st.session_state.confirm_publish_gate = False; st.rerun()
                    with col_lock2:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.confirm_publish_gate = False; st.rerun()
            else:
                st.success("✅ Workspace Live")
                if st.button("🔓 Emergency Revoke & Unfreeze"):
                    supabase.table("farms").update({"is_published": False}).eq("id", st.session_state.active_site_id).execute()
                    st.rerun()

    def load_site_isolated_tables(farm_id):
        all_data = []
        limit = 1000; offset = 0
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
        st.warning("ℹ️ No metrics found. Upload a blueprint.")
        st.stop()

    min_r = min([b.get("min_r", 1) for b in active_table_data])
    max_r = max([b.get("max_r", 100) for b in active_table_data])
    min_c = min([b.get("min_c", 1) for b in active_table_data])
    max_c = max([b.get("max_c", 150) for b in active_table_data])
    
    json_str = json.dumps(active_table_data)
    b64_json_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs(["⚡ Advanced Infrastructure Stringing & Layout Core", "📌 Legacy Phase Customizer"])
        
        with setup_tabs[0]:
            st.markdown("### 🔌 Advanced Electrical Infrastructure Stringing Matrix Node")
            
            # Form setup inside Streamlit to hold complex topology strings
            current_meta_str = current_farm_record.get("background_image_url") if (current_farm_record.get("background_image_url") and current_farm_record.get("background_image_url").startswith("{")) else "{}"
            
            col_save1, col_save2 = st.columns([8, 2])
            with col_save1:
                st.info("💡 Select a command operation tool on the workspace dashboard, then execute actions directly on the canvas map node.")
            
            # ADVANCED CAD GRAPHICS SYSTEM ENGINE ENGINE WITH INDEPENDENT NORTH/SOUTH STRING SPLITTING
            html_advanced_cad_system = """
            <div style="background:#090d16; padding:15px; border-radius:12px; font-family:sans-serif; color:#f8fafc;">
                <div style="display:grid; grid-template-columns: 240px 1fr; gap:15px;">
                    <div style="background:#0f172a; padding:12px; border-radius:8px; border:1px solid #1e293b;">
                        <h4 style="margin-top:0; color:#38bdf8;">🛠️ Command Tool</h4>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="pan" checked> ✋ Pan / Navigate Map</label>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="zone"> 🎨 Paint Zone Allocation</label>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="string"> 🔌 Lasso Group Strings</label>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="inverter"> ⚡ Place Inverter Block</label>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="transformer"> 🏪 Click Place Xfrmr</label>
                        <label style="display:block; margin-bottom:8px; cursor:pointer;"><input type="radio" name="tool" value="route"> 🔗 Route Inv ➔ Xfrmr</label>
                        
                        <hr style="border-color:#1e293b;">
                        <h5 style="margin-bottom:6px; color:#a78bfa;">Parameters</h5>
                        <div id="zone_selector_panel">
                            <label style="font-size:12px;">Active Target Zone:</label>
                            <input type="text" id="target_zone_val" value="Zone A" style="width:100%; background:#1e293b; color:white; border:1px solid #334155; border-radius:4px; padding:4px; margin-bottom:8px;">
                        </div>
                        <div id="inv_selector_panel">
                            <label style="font-size:12px;">Target Inverter ID:</label>
                            <input type="number" id="target_inv_id" value="1" min="1" style="width:100%; background:#1e293b; color:white; border:1px solid #334155; border-radius:4px; padding:4px; margin-bottom:8px;">
                        </div>
                        
                        <button id="btn_clear_topology" style="width:100%; background:#ef4444; border:none; padding:8px; color:white; font-weight:bold; border-radius:4px; cursor:pointer; margin-top:10px;">💥 Reset Topology Layout</button>
                        <button id="btn_push_cloud" style="width:100%; background:#22c55e; border:none; padding:8px; color:white; font-weight:bold; border-radius:4px; cursor:pointer; margin-top:8px;">💾 Push Mapping to Cloud</button>
                    </div>

                    <div style="position:relative;">
                        <div id="cad_tooltip" style="position:absolute; display:none; background:rgba(15,23,42,0.95); border:1px solid #38bdf8; padding:8px; border-radius:6px; font-size:12px; pointer-events:none; z-index:9999; color:white;"></div>
                        <canvas id="advanced_cad_canvas" width="1100" height="600" style="background:#020617; border-radius:8px; border:2px solid #1e293b; display:block;"></canvas>
                    </div>
                </div>
            </div>

            <script>
                (function() {
                    const rawBlocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    let topology = JSON.parse(atob("__TOPOLOGY_METADATA_B64__"));
                    
                    // Default configuration variables initialization
                    if (!topology.inverters) topology.inverters = [];
                    if (!topology.transformers) topology.transformers = [];
                    if (!topology.stringGroups) topology.stringGroups = {}; 

                    const canvas = document.getElementById("advanced_cad_canvas");
                    const ctx = canvas.getContext("2d");
                    const tooltip = document.getElementById("cad_tooltip");
                    const CELL = 14;

                    // Compute structures & expand multi-facing strings independently
                    let strings = [];
                    rawBlocks.forEach(b => {
                        if (b.structure_type === "double_6x9") {
                            let midpointRow = b.min_r + Math.floor((b.max_r - b.min_r) / 2);
                            // North Facing String Segment
                            strings.append({
                                id: b.id + "_N", parentId: b.id, label: b.table_label + " (N)",
                                min_c: b.min_c, max_c: b.max_c, min_r: b.min_r, max_r: midpointRow,
                                zone: b.assigned_zone || "Unassigned"
                            });
                            // South Facing String Segment
                            strings.append({
                                id: b.id + "_S", parentId: b.id, label: b.table_label + " (S)",
                                min_c: b.min_c, max_c: b.max_c, min_r: midpointRow + 1, max_r: b.max_r,
                                zone: b.assigned_zone || "Unassigned"
                            });
                        } else {
                            // Standard Single Facing Structure Row Block
                            strings.append({
                                id: b.id + "_A", parentId: b.id, label: b.table_label,
                                min_c: b.min_c, max_c: b.max_c, min_r: b.min_r, max_r: b.max_r,
                                zone: b.assigned_zone || "Unassigned"
                            });
                        }
                    });

                    let minX = MIN_C_VAL, maxX = MAX_C_VAL, minY = MIN_R_VAL, maxY = MAX_R_VAL;
                    const mapWidth = (maxX - minX + 1) * CELL;
                    const mapHeight = (maxY - minY + 1) * CELL;

                    let scale = Math.min((canvas.width - 100) / mapWidth, (canvas.height - 100) / mapHeight);
                    if (scale <= 0 || !isFinite(scale)) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (mapWidth * scale / 2) - (minX * CELL * scale);
                    let offsetY = (canvas.height / 2) - (mapHeight * scale / 2) - (minY * CELL * scale);

                    let isPanning = false, isSelecting = false;
                    let startX = 0, startY = 0, currX = 0, currY = 0;
                    let selectedInverterIndexForRouting = null;

                    canvas.addEventListener("contextmenu", e => e.preventDefault());

                    function getTool() {
                        return document.querySelector('input[name="tool"]:checked').value;
                    }

                    function getBorderColorForCount(count) {
                        if (!count || count === 0) return "transparent";
                        if (count <= 4) return "#38bdf8"; // Cyan blue loop 
                        if (count <= 8) return "#eab308"; // Amber grouping loop
                        if (count <= 12) return "#a78bfa"; // Amethyst loop
                        return "#f43f5e"; // Rose maximum configuration boundary 
                    }

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.save();
                        ctx.translate(offsetX, offsetY);
                        ctx.scale(scale, scale);

                        // Draw Transformer Stations
                        topology.transformers.forEach((t, index) => {
                            ctx.fillStyle = "#ef4444";
                            ctx.fillRect(t.x - 15, t.y - 15, 30, 30);
                            ctx.strokeStyle = "#ffffff";
                            ctx.lineWidth = 2;
                            ctx.strokeRect(t.x - 15, t.y - 15, 30, 30);
                            
                            ctx.fillStyle = "#ffffff";
                            ctx.font = "bold 10px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("XFMR " + (index + 1), t.x, t.y + 4);
                        });

                        // Draw Routing Lines (Inverter to Transformers)
                        topology.inverters.forEach(inv => {
                            if (inv.transformerId !== null && topology.transformers[inv.transformerId]) {
                                let xfmr = topology.transformers[inv.transformerId];
                                ctx.strokeStyle = "rgba(234, 179, 8, 0.65)";
                                ctx.lineWidth = 3;
                                ctx.setLineDash([4, 4]);
                                ctx.beginPath();
                                ctx.moveTo(inv.x, inv.y);
                                ctx.lineTo(xfmr.x, xfmr.y);
                                ctx.stroke();
                                ctx.setLineDash([]);
                            }
                        });

                        // Draw Inverters
                        topology.inverters.forEach((inv, index) => {
                            ctx.fillStyle = "#22c55e";
                            ctx.fillRect(inv.x - 10, inv.y - 10, 20, 20);
                            ctx.strokeStyle = "#ffffff";
                            ctx.lineWidth = 1.5;
                            ctx.strokeRect(inv.x - 10, inv.y - 10, 20, 20);
                            
                            ctx.fillStyle = "#ffffff";
                            ctx.font = "bold 9px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("INV " + inv.id, inv.x, inv.y + 3);
                        });

                        // Count active inverter assignments to calculate grouping loop border variations
                        let invCounts = {};
                        Object.values(topology.stringGroups).forEach(invId => {
                            invCounts[invId] = (invCounts[invId] || 0) + 1;
                        });

                        // Draw Independent Solar String Blocks
                        strings.forEach(s => {
                            let x = s.min_c * CELL;
                            let y = s.min_r * CELL;
                            let w = (s.max_c - s.min_c + 1) * CELL;
                            let h = (s.max_r - s.min_r + 1) * CELL;

                            // Dynamic Zone Color Mapping Calculation Logic
                            let hash = 0;
                            for (let i = 0; i < s.zone.length; i++) hash = s.zone.charCodeAt(i) + ((hash << 5) - hash);
                            let hue = s.zone === "Unassigned" ? 215 : Math.abs(hash * 35) % 360;
                            ctx.fillStyle = s.zone === "Unassigned" ? "#1e293b" : `hsl(${hue}, 70%, 40%)`;
                            ctx.fillRect(x, y, w, h);

                            // Render base framework grid line separator paths
                            ctx.strokeStyle = "rgba(255,255,255,0.08)";
                            ctx.lineWidth = 0.5;
                            ctx.strokeRect(x, y, w, h);

                            // Draw grouping border loop if linked to active inverter
                            let linkedInvId = topology.stringGroups[s.id];
                            if (linkedInvId) {
                                ctx.strokeStyle = getBorderColorForCount(invCounts[linkedInvId]);
                                ctx.lineWidth = 2.5;
                                ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);

                                // Tiny label showing connected inverter
                                ctx.fillStyle = "#ffffff";
                                ctx.font = "7px sans-serif";
                                ctx.fillText("I-" + linkedInvId, x + 4, y + 10);
                            }
                        });

                        ctx.restore();

                        // Render Lasso Selection Rectangle Overlay Feedback Boundary
                        if (isSelecting && (getTool() === "zone" || getTool() === "string")) {
                            ctx.strokeStyle = getTool() === "zone" ? "#38bdf8" : "#a78bfa";
                            ctx.lineWidth = 1.5;
                            ctx.fillStyle = getTool() === "zone" ? "rgba(56, 189, 248, 0.15)" : "rgba(167, 139, 250, 0.15)";
                            ctx.fillRect(startX, startY, currX - startX, currY - startY);
                            ctx.strokeRect(startX, startY, currX - startX, currY - startY);
                        }
                    }

                    // Global workspace canvas mouse tracking coordinates interpreter
                    function getMousePos(e) {
                        const rect = canvas.getBoundingClientRect();
                        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
                    }

                    function toWorldCoords(p) {
                        return { x: (p.x - offsetX) / scale, y: (p.y - offsetY) / scale };
                    }

                    canvas.addEventListener("mousedown", e => {
                        const m = getMousePos(e);
                        const world = toWorldCoords(m);
                        const tool = getTool();

                        if (e.button === 2 || tool === "pan") {
                            isPanning = true;
                            startX = e.clientX - offsetX;
                            startY = e.clientY - offsetY;
                            canvas.style.cursor = "move";
                        } else if (tool === "zone" || tool === "string") {
                            isSelecting = true;
                            startX = m.x; startY = m.y;
                            currX = m.x; currY = m.y;
                        } else if (tool === "inverter") {
                            // Find target hover solar block tracking position to snap structural layout inverter box anchor
                            let targetBlock = strings.find(s => {
                                let sx = s.min_c * CELL, sy = s.min_r * CELL;
                                let sw = (s.max_c - s.min_c + 1) * CELL, sh = (s.max_r - s.min_r + 1) * CELL;
                                return world.x >= sx && world.x <= sx + sw && world.y >= sy && world.y <= sy + sh;
                            });

                            if (targetBlock) {
                                let invId = parseInt(document.getElementById("target_inv_id").value) || 1;
                                // Clean redundant matching ids if existing to re-allocate coordinates safely
                                topology.inverters = topology.inverters.filter(i => i.id !== invId);
                                topology.inverters.push({
                                    id: invId,
                                    x: (targetBlock.min_c * CELL) + (((targetBlock.max_c - targetBlock.min_c + 1) * CELL) / 2),
                                    y: (targetBlock.max_r * CELL) + 20, // Snapped offset alignment position configuration
                                    transformerId: null
                                });
                                draw();
                            }
                        } else if (tool === "transformer") {
                            // Check collision boundaries to confirm instantiation lands on black spacing coordinates
                            let hitBlock = strings.find(s => {
                                let sx = s.min_c * CELL, sy = s.min_r * CELL;
                                let sw = (s.max_c - s.min_c + 1) * CELL, sh = (s.max_r - s.min_r + 1) * CELL;
                                return world.x >= sx && world.x <= sx + sw && world.y >= sy && world.y <= sy + sh;
                            });

                            if (!hitBlock) {
                                topology.transformers.push({ x: world.x, y: world.y });
                                draw();
                            }
                        } else if (tool === "route") {
                            // Check click collision coordinate accuracy targeted directly on an inverter node block asset
                            let matchedInvIdx = topology.inverters.findIndex(inv => {
                                return Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 15;
                            });

                            if (matchedInvIdx !== -1) {
                                selectedInverterIndexForRouting = matchedInvIdx;
                                tooltip.style.display = "block";
                                tooltip.innerHTML = "🎯 Routing Active: Now select destination Transformer Station Box Node.";
                            } else if (selectedInverterIndexForRouting !== null) {
                                // Check collision selection context on transformer node asset destination target
                                let matchedXfmrIdx = topology.transformers.findIndex(t => {
                                    return Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 20;
                                });

                                if (matchedXfmrIdx !== -1) {
                                    topology.inverters[selectedInverterIndexForRouting].transformerId = matchedXfmrIdx;
                                    selectedInverterIndexForRouting = null;
                                    draw();
                                }
                            }
                        }
                    });

                    canvas.addEventListener("mousemove", e => {
                        const m = getMousePos(e);
                        const world = toWorldCoords(m);

                        if (isPanning) {
                            offsetX = e.clientX - startX;
                            offsetY = e.clientY - startY;
                            draw();
                            return;
                        } else if (isSelecting) {
                            currX = m.x; currY = m.y;
                            draw();
                            return;
                        }

                        // Spatial Unified Hover Interaction System Logic Coordinates Analyzer Matrix Parser
                        let foundHover = false;

                        // 1. Inspect Transformer Hover Context Elements
                        topology.transformers.forEach((t, idx) => {
                            if (Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 20) {
                                let mappedInverters = topology.inverters.filter(i => i.transformerId === idx).map(i => i.id).join(", ");
                                tooltip.style.display = "block";
                                tooltip.style.left = (m.x + 20) + "px";
                                tooltip.style.top = (m.y + 20) + "px";
                                tooltip.innerHTML = `<b>🏪 Transformer Hub Asset Station</b><br>Station Allocation Key: #${idx + 1}<br>Routed Feeding Inverters: [${mappedInverters || 'None'}]`;
                                foundHover = true;
                            }
                        });

                        // 2. Inspect Inverter Hover Context Elements
                        if (!foundHover) {
                            topology.inverters.forEach((inv) => {
                                if (Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 15) {
                                    tooltip.style.display = "block";
                                    tooltip.style.left = (m.x + 20) + "px";
                                    tooltip.style.top = (m.y + 20) + "px";
                                    tooltip.innerHTML = `<b>⚡ Inverter Control Node Block</b><br>Inverter ID Token: ${inv.id}<br>Routed Station Line: ${inv.transformerId !== null ? 'XFMR ' + (inv.transformerId + 1) : 'Unrouted Loop'}`;
                                    foundHover = true;
                                }
                            });
                        }

                        // 3. Inspect String Layout Component Hover Context Elements 
                        if (!foundHover) {
                            let s = strings.find(s => {
                                let sx = s.min_c * CELL, sy = s.min_r * CELL;
                                let sw = (s.max_c - s.min_c + 1) * CELL, sh = (s.max_r - s.min_r + 1) * CELL;
                                return world.x >= sx && world.x <= sx + sw && world.y >= sy && world.y <= sy + sh;
                            });

                            if (s) {
                                tooltip.style.display = "block";
                                tooltip.style.left = (m.x + 20) + "px";
                                tooltip.style.top = (m.y + 20) + "px";
                                
                                let parentInv = topology.stringGroups[s.id] || "None Linked";
                                let parentXfmr = "None Linked";
                                if (parentInv !== "None Linked") {
                                    let invObj = topology.inverters.find(i => i.id === parseInt(parentInv));
                                    if (invObj && invObj.transformerId !== null) parentXfmr = "XFMR " + (invObj.transformerId + 1);
                                }

                                tooltip.innerHTML = `<b>☀️ Solar String Element Block</b><br>Identifier: ${s.label}<br>Zoning Assignment: ${s.zone}<br>Linked Inverter: ${parentInv}<br>Linked Network Hub: ${parentXfmr}`;
                                foundHover = true;
                            }
                        }

                        if (!foundHover && selectedInverterIndexForRouting === null) tooltip.style.display = "none";
                    });

                    canvas.addEventListener("mouseup", async e => {
                        if (isPanning) {
                            isPanning = false;
                            canvas.style.cursor = "default";
                            return;
                        }

                        if (isSelecting) {
                            isSelecting = false;
                            const tool = getTool();
                            const p1 = toWorldCoords(getMousePos({ clientX: startX + canvas.getBoundingClientRect().left, clientY: startY + canvas.getBoundingClientRect().top }));
                            const p2 = toWorldCoords(getMousePos(e));

                            let bx1 = Math.min(p1.x, p2.x), bx2 = Math.max(p1.x, p2.x);
                            let by1 = Math.min(p1.y, p2.y), by2 = Math.max(p1.y, p2.y);

                            let selectedElements = strings.filter(s => {
                                let cx = s.min_c * CELL, cy = s.min_r * CELL;
                                return cx >= bx1 && cx <= bx2 && cy >= by1 && cy <= by2;
                            });

                            if (selectedElements.length > 0) {
                                if (tool === "zone") {
                                    let zoneVal = document.getElementById("target_zone_val").value || "Unassigned";
                                    // Local updates loop propagation 
                                    selectedElements.forEach(async el => {
                                        el.zone = zoneVal;
                                        // Execute structural parent updates patch payload synchronization down to Supabase Rest API
                                        await fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq." + el.parentId, {
                                            method: "PATCH",
                                            headers: {
                                                "apikey": "SUPABASE_KEY_VAL",
                                                "Authorization": "Bearer SUPABASE_KEY_VAL",
                                                "Content-Type": "application/json"
                                            },
                                            body: JSON.stringify({ assigned_zone: zoneVal })
                                        });
                                    });
                                } else if (tool === "string") {
                                    let invId = parseInt(document.getElementById("target_inv_id").value) || 1;
                                    selectedElements.forEach(el => {
                                        topology.stringGroups[el.id] = invId;
                                    });
                                }
                                draw();
                            }
                        }
                    });

                    canvas.addEventListener("wheel", e => {
                        e.preventDefault();
                        const m = getMousePos(e);
                        const grid = toWorldCoords(m);
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85);
                        scale = Math.max(0.01, Math.min(scale, 25));
                        offsetX = m.x - grid.x * scale;
                        offsetY = m.y - grid.y * scale;
                        draw();
                    }, { passive: false });

                    document.getElementById("btn_clear_topology").addEventListener("click", () => {
                        if (confirm("Reset structural loop paths, stringing patterns, and transformer drop coordinates?")) {
                            topology = { inverters: [], transformers: [], stringGroups: {} };
                            draw();
                        }
                    });

                    document.getElementById("btn_push_cloud").addEventListener("click", async () => {
                        const targetButton = document.getElementById("btn_push_cloud");
                        targetButton.innerText = "⏳ Synchronizing Topology Matrix...";
                        try {
                            const payloadString = JSON.stringify(topology);
                            await fetch("SUPABASE_URL_VAL/rest/v1/farms?id=eq.ACTIVE_SITE_ID_VAL", {
                                method: "PATCH",
                                headers: {
                                    "apikey": "SUPABASE_KEY_VAL",
                                    "Authorization": "Bearer SUPABASE_KEY_VAL",
                                    "Content-Type": "application/json",
                                    "Prefer": "return=minimal"
                                },
                                body: JSON.stringify({ background_image_url: payloadString })
                            });
                            targetButton.innerText = "✅ Topology Saved Sync Complete!";
                            setTimeout(() => { targetButton.innerText = "💾 Push Mapping to Cloud"; }, 2500);
                        } catch (err) {
                            targetButton.innerText = "❌ Synchronization Refused";
                        }
                    });

                    draw();
                })();
            </script>
            """
            # Inject tokens and pass the structural models directly into the visual interface module
            html_advanced_cad_system = html_advanced_cad_system.replace("__JSON_DATA_B64__", b64_json_data)\
                                                               .replace("__TOPOLOGY_METADATA_B64__", base64.b64encode(current_meta_str.encode("utf-8")).decode("utf-8"))\
                                                               .replace("MIN_C_VAL", str(min_c))\
                                                               .replace("MAX_C_VAL", str(max_c))\
                                                               .replace("MIN_R_VAL", str(min_r))\
                                                               .replace("MAX_R_VAL", str(max_r))\
                                                               .replace("SUPABASE_URL_VAL", SUPABASE_URL)\
                                                               .replace("SUPABASE_KEY_VAL", SUPABASE_KEY)\
                                                               .replace("ACTIVE_SITE_ID_VAL", str(st.session_state.active_site_id))
            
            components.html(html_advanced_cad_system, height=660)

        with setup_tabs[1]:
            st.info("Legacy phase mapping controls hosted below.")
            # --- PREVIOUS STAGE 3 INHERITED BLUEPRINT PLACEMENT MICROSCALE ENGINE ---
            html_micro_template = """
            <div style="background:#0f172a; padding:15px; border-radius:12px; text-align:center;"><canvas id="micro_canvas" width="300" height="200" style="background:#020617; border:2px dashed #38bdf8; border-radius:6px; cursor:crosshair Pap;"></canvas></div>
            <script>const c = document.getElementById("micro_canvas"); const ctx = c.getContext('2d'); ctx.fillStyle='#334155'; ctx.fillRect(40,30,220,140); ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.strokeRect(40,30,220,140);</script>
            """
            components.html(html_micro_template, height=240)

    else:
        # ==============================================================================
        # 👷 THE OPERATION INTERFACES (CREW WORKSPACE VIEWS)
        # ==============================================================================
        if not site_is_published:
            st.warning("⏳ **Workspace Under Construction**")
            st.info("The layout map is currently being prepared by engineering. Modules will become accessible once published live.")
        else:
            st.success("🛰️ Deployed Operational Framework Grid Reference Active")
            crew_tabs = st.tabs(["📌 Structural String Tracking Monitor", "🪵 Physical Piling Matrix"])
            
            with crew_tabs[0]:
                # Implement high fidelity overview tracker component node matrix for deployment tracking 
                st.info("Visual Field Inspection layer active.")
