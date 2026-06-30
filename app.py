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

# --- HIDE ONLY GITHUB & EDIT PENCIL ICONS ---
st.markdown("""
    <style>
    div[data-testid="stAppToolbar"] > div:has(a),
    div[data-testid="stAppToolbar"] div[class*="stActionButton"]:not(:has(button[data-testid="stActionButtonDropdown"])) {
        display: none !important;
    }
    div[data-testid="stAppToolbar"] a {
        display: none !important;
    }
    div[data-testid="stAppToolbar"] div:has(button[data-testid="stActionButtonDropdown"]),
    button[data-testid="stActionButtonDropdown"] {
        display: inline-flex !important;
        visibility: visible !important;
    }
    </style>
""", unsafe_allow_html=True)

if "active_site_id" not in st.session_state: st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state: st.session_state.is_admin_mode = False
if "managed_zones" not in st.session_state: 
    st.session_state.managed_zones = ["Zone A", "Zone B", "Zone C", "Unassigned"]
if "custom_tabs" not in st.session_state: st.session_state.custom_tabs = []
if "time_travel_date" not in st.session_state: st.session_state.time_travel_date = None

def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("id, name, admin_password, installer_password, is_published, background_image_url").order("name").execute()
        return res.data if res.data else []
    except Exception: return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# Helper to identify current target operational window context date
def get_operational_date():
    if st.session_state.is_admin_mode and st.session_state.time_travel_date:
        return st.session_state.time_travel_date
    return date.today()

# Helper to calculate working business days (Mon-Fri) within active dates bounds
def calculate_working_days(start: date, end: date) -> int:
    if start > end: return 0
    days = 0
    curr = start
    while curr <= end:
        if curr.weekday() < 5: days += 1
        curr += timedelta(days=1)
    return max(days, 1)

# Mapping indices metadata constants
aspects_dictionary = {
    "pegging": "📌 Pegging Phase",
    "piling": "🪵 Piling Operations",
    "mounting": "🏗️ Mounting Structures",
    "module": "☀️ PV Module Tracking",
    "inverter_struct": "🔧 Inverter Structure",
    "inverter": "⚡ Inverter Node",
    "transformer_station": "🏪 Transformer Station",
    "dc_cabling": "🔌 DC Cabling Interconnect",
    "ac_cabling": "🔗 AC Cabling Tie"
}

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
                    
                    if "confirm_purge_gate" not in st.session_state:
                        st.session_state.confirm_purge_gate = False
                    if "purge_target_selected" not in st.session_state:
                        st.session_state.purge_target_selected = ""

                    if st.session_state.purge_target_selected != wipe_target:
                        st.session_state.confirm_purge_gate = False
                        st.session_state.purge_target_selected = wipe_target

                    if not st.session_state.confirm_purge_gate:
                        if st.button("💥 Purge Cloud Data Records", type="primary"):
                            st.session_state.confirm_purge_gate = True
                            st.rerun()
                    else:
                        st.error(f"🚨 **CRITICAL WARNING:** Are you sure you want to delete layout parameters for **{wipe_target}**? This cannot be undone.")
                        
                        col_purge1, col_purge2 = st.columns(2)
                        with col_purge1:
                            if st.button("🔥 YES, PERMANENTLY PURGE", type="primary", use_container_width=True):
                                with st.spinner(f"Purging data assets for {wipe_target}..."):
                                    try:
                                        target_farm = next((f for f in all_registered_farms if f["name"] == wipe_target), None)
                                        if target_farm:
                                            supabase.table("structures").delete().eq("farm_id", target_farm["id"]).execute()
                                            supabase.table("aspect_schedules").delete().eq("farm_id", target_farm["id"]).execute()
                                            supabase.table("daily_progress_log").delete().eq("farm_id", target_farm["id"]).execute()
                                            supabase.table("farms").delete().eq("id", target_farm["id"]).execute()
                                            st.success(f"Successfully cleared all data frameworks for {wipe_target}!")
                                            
                                            st.session_state.confirm_purge_gate = False
                                            st.cache_resource.clear()
                                            time.sleep(1)
                                            st.rerun()
                                    except Exception as e: 
                                        st.error(f"Purge rejected: {str(e)}")
                        with col_purge2:
                            if st.button("❌ Cancel / Abort", use_container_width=True):
                                st.session_state.confirm_purge_gate = False
                                st.rerun()
                else:
                    st.info("No active cloud entries found to clear.")
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
                                                "section_group": 403, 
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
                                st.cache_resource.clear()
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
                    st.session_state.dev_unlocked = False 
                    st.rerun()
# ==============================================================================
# 🗂️ PHASE 2: INTERNAL OPERATIONS TRACKING PLATFORM COMMAND CENTER
# ==============================================================================
else:
    def load_site_isolated_tables(farm_id):
        all_data = []
        limit = 1000
        offset = 0
        while True:
            try:
                res = supabase.table("structures").select("*, pegging_pins_state, piling_pins_state, modules_state, inverter_struct_status, inverter_status, transformer_status, dc_cabling_status, ac_cabling_status").eq("farm_id", farm_id).order("min_r").order("min_c").range(offset, offset + limit - 1).execute().data
                if not res: break
                all_data.extend(res)
                if len(res) < limit: break
                offset += limit
            except Exception: break
        return all_data

    current_farm_record = supabase.table("farms").select("*").eq("id", st.session_state.active_site_id).execute().data[0]
    site_is_published = current_farm_record.get("is_published", False)
    site_bg_img = current_farm_record.get("background_image_url", "")

    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: 
        st.subheader(f"📍 Boon Solar Farm Tracking System — {st.session_state.active_site_name}")
    with col_h2:
        if st.button("🚪 Exit Site", use_container_width=True): 
            st.session_state.active_site_id = None
            st.session_state.is_admin_mode = False
            st.session_state.time_travel_date = None
            st.rerun()
            
    with st.sidebar:
        st.header("🔐 Workspace Clearances")
        
        if not st.session_state.is_admin_mode:
            with st.form("admin_upgrade_form", clear_on_submit=True):
                adm_pass = st.text_input("Enter Management Credentials Panel Pass:", type="password")
                if st.form_submit_button("Verify Clearance", use_container_width=True):
                    if str(adm_pass) == str(st.session_state.admin_key_match):
                        st.session_state.is_admin_mode = True
                        st.rerun()
                    else: 
                        st.error("Incorrect Password.")
        else:
            st.success("⚡ Admin Permissions Active")
            
            # --- TIME TRAVEL OVERRIDE WIDGET PANEL ---
            st.markdown("---")
            st.subheader("🕒 Historic Late Entry Adjuster")
            tt_flag = st.checkbox("Unlock Temporal State Backfills", value=(st.session_state.time_travel_date is not None))
            if tt_flag:
                st.session_state.time_travel_date = st.date_input("Target History Entry Window:", value=st.session_state.time_travel_date if st.session_state.time_travel_date else date.today())
            else:
                st.session_state.time_travel_date = None
            
            st.write("---")
            with st.expander("🧪 Dynamic Workspace Duplicator", expanded=False):
                st.markdown("#### Create an Isolated Testing Sandbox")
                st.caption("Clones your active operational layout matrix completely, including custom stringing and topologies.")
                
                sandbox_suffix = st.text_input("Assign Sandbox Name Extension:", value="EXPERIMENTAL COPY")
                
                if st.button("🚀 Clone Target Setup to New Sandbox Slot", type="primary", use_container_width=True):
                    with st.spinner("Executing 100% Master Duplication Loop..."):
                        try:
                            parent_farm_id = st.session_state.active_site_id
                            raw_topo_string = current_farm_record.get("background_image_url") or "{}"
                            
                            parent_structures = []
                            limit = 1000
                            offset = 0
                            while True:
                                res_page = supabase.table("structures").select("*").eq("farm_id", parent_farm_id).order("min_r").order("min_c").range(offset, offset + limit - 1).execute().data
                                if not res_page: break
                                parent_structures.extend(res_page)
                                if len(res_page) < limit: break
                                offset += limit

                            sandbox_payload = {
                                "name": f"{st.session_state.active_site_name} - {sandbox_suffix.upper()}",
                                "admin_password": current_farm_record.get("admin_password", "ok"),
                                "installer_password": current_farm_record.get("installer_password", "1234"),
                                "max_rows": int(current_farm_record.get("max_rows", 100)),
                                "max_cols": int(current_farm_record.get("max_cols", 150)),
                                "is_published": False,
                                "background_image_url": "{}"
                            }
                            
                            new_farm_response = supabase.table("farms").insert(sandbox_payload).execute()
                            
                            if new_farm_response.data and parent_structures:
                                sandbox_farm_id = new_farm_response.data[0]["id"]
                                
                                sandbox_structures = []
                                for struct in parent_structures:
                                    sandbox_structures.append({
                                        "farm_id": sandbox_farm_id,
                                        "table_label": str(struct.get("table_label", "")),
                                        "min_r": int(struct.get("min_r")), "max_r": int(struct.get("max_r")),
                                        "min_c": int(struct.get("min_c")), "max_c": int(struct.get("max_c")),
                                        "structure_type": str(struct.get("structure_type", "single_3x9")),
                                        "assigned_zone": str(struct.get("assigned_zone", "Unassigned")),
                                        "section_group": int(struct.get("section_group")) if struct.get("section_group") is not None else None,
                                        "pegging_status": str(struct.get("pegging_status", "pending")),
                                        "piling_status": str(struct.get("piling_status", "pending")),
                                        "mounting_status": str(struct.get("mounting_status", "pending")),
                                        "modules_status": str(struct.get("modules_status", "pending"))
                                    })
                                
                                inserted_structures_fleet = []
                                for idx in range(0, len(sandbox_structures), 200):
                                    batch = sandbox_structures[idx:idx+200]
                                    res_batch = supabase.table("structures").insert(batch).execute()
                                    if res_batch.data:
                                        inserted_structures_fleet.extend(res_batch.data)
                                
                                id_mapping_dictionary = {}
                                for old_s in parent_structures:
                                    match = next((new_s for new_s in inserted_structures_fleet 
                                                  if new_s["table_label"] == str(old_s["table_label"]) 
                                                  and int(new_s["min_r"]) == int(old_s["min_r"]) 
                                                  and int(new_s["min_c"]) == int(old_s["min_c"])), None)
                                    if match:
                                        id_mapping_dictionary[str(old_s["id"])] = str(match["id"])
                                
                                try:
                                    if raw_topo_string.startswith("{"):
                                        topo_data = json.loads(raw_topo_string)
                                        
                                        if "stringGroups" in topo_data:
                                            new_string_groups = {}
                                            for old_key, inv_value in topo_data["stringGroups"].items():
                                                parts = old_key.split("_")
                                                old_base_id = parts[0]
                                                suffix = f"_{parts[1]}" if len(parts) > 1 else ""
                                                
                                                if old_base_id in id_mapping_dictionary:
                                                    new_base_id = id_mapping_dictionary[old_base_id]
                                                    new_string_groups[f"{new_base_id}{suffix}"] = inv_value
                                            topo_data["stringGroups"] = new_string_groups
                                        
                                        if "inverters" in topo_data:
                                            CELL = 14
                                            for inv in topo_data["inverters"]:
                                                if "transformerId" in inv and inv["transformerId"] is not None:
                                                    if "transformers" in topo_data and (inv["transformerId"] >= len(topo_data["transformers"]) or inv["transformerId"] < 0):
                                                        inv["transformerId"] = None
                                                
                                                matching_parent_block = None
                                                for p_struct in parent_structures:
                                                    if (p_struct["min_c"] * CELL) <= inv["x"] <= ((p_struct["max_c"] + 1) * CELL) and \
                                                       (p_struct["min_r"] * CELL) <= inv["y"] <= ((p_struct["max_r"] + 1) * CELL):
                                                        matching_parent_block = p_struct
                                                        break
                                                
                                                if matching_parent_block and str(matching_parent_block["id"]) in id_mapping_dictionary:
                                                    new_id_val = int(id_mapping_dictionary[str(matching_parent_block["id"])])
                                                    new_block = next((nb for nb in inserted_structures_fleet if nb["id"] == new_id_val), None)
                                                    if new_block:
                                                        inv["x"] = (new_block["min_c"] * CELL) + (((new_block["max_c"] - new_block["min_c"] + 1) * CELL) / 2)
                                                        inv["y"] = (new_block["min_r"] * CELL) + (((new_block["max_r"] - new_block["min_r"] + 1) * CELL) / 2)
                                                        
                                        raw_topo_string = json.dumps(topo_data)
                                except Exception: pass
                                
                                supabase.table("farms").update({"background_image_url": raw_topo_string}).eq("id", sandbox_farm_id).execute()
                                st.cache_resource.clear()
                                st.success("🎉 100% Perfect Clone Created! Panels, Inverters, Strings, and TS Hubs are identical.")
                                time.sleep(1.5)
                                st.rerun()
                        except Exception as err:
                            st.error(f"Duplication sequence failed: {str(err)}")
            
            st.write("---")
            st.subheader("📢 Field Deployment Release")
            if not site_is_published:
                st.warning("⚠️ CRITICAL: Review settings carefully. Once published to the field crew, coordinates cannot be altered.")
                
                if "confirm_publish_gate" not in st.session_state: st.session_state.confirm_publish_gate = False
                
                if not st.session_state.confirm_publish_gate:
                    if st.button("🚀 Publish Layout Workspace to Field Crew", type="primary", use_container_width=True):
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
                if st.button("🔓 Emergency Revoke & Unfreeze Project (Admin Only)", use_container_width=True):
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
                elif st.button("💾 Apply & Save Image Blueprint", type="primary", use_container_width=True):
                    supabase.table("farms").update({"background_image_url": b64_img_string}).eq("id", st.session_state.active_site_id).execute()
                    st.success("Image blueprints attached safely!")
                    time.sleep(0.5); st.rerun()
            
            if site_bg_img and not site_is_published:
                if st.button("🗑️ Remove Current Background Image", type="secondary", use_container_width=True):
                    if not site_bg_img.startswith("{"):
                        supabase.table("farms").update({"background_image_url": ""}).eq("id", st.session_state.active_site_id).execute()
                        st.success("Background mapping reference flushed!")
                        time.sleep(0.5); st.rerun()

            st.write("---")
            st.subheader("🛠️ Custom Tracker Tab Builder")
            custom_tab_name = st.text_input("Assign New Tracker Tab Label:", placeholder="e.g. Floating Cell...")
            if st.button("✨ Instantiate Phase Tab", use_container_width=True) and custom_tab_name:
                if custom_tab_name not in st.session_state.custom_tabs:
                    st.session_state.custom_tabs.append(custom_tab_name)
                    st.success(f"Instantiated '{custom_tab_name}'!")
                    time.sleep(0.4); st.rerun()
                    
            if st.button("🔒 Revoke Admin Clearances", use_container_width=True): 
                st.session_state.is_admin_mode = False
                st.session_state.time_travel_date = None
                st.rerun()

    if st.button("🔄 Reload Workspace Map from Database", type="secondary"):
        st.rerun()

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

    # ==============================================================================
    # 👑 REGION A: ADMIN WORKSPACE LAYOUT & MANAGEMENT tabs
    # ==============================================================================
    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs([
            "🖼️ Base Overview & Zone Assignation", 
            "📌 Pegging & Piling Customizer",
            "🛰️ Unified Layout Planner & Topology Workspace",
            "📊 Executive Analytical Summary",
            "🗓️ Aspect Timeline Master Scheduler",
            "📈 Progress History & Log Viewer"
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
                        ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale,scale);

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
                l_type = block.get("structure_type", "single_3x9")
                layout_key = f"{l_type} ({h_cells}x{w_cells} grid layout)"
                
                if layout_key not in layout_types:
                    layout_types[layout_key] = {
                        "type_string": l_type,
                        "h_cells": h_cells,
                        "w_cells": w_cells,
                        "sample_block_id": block.get("id"),
                        "encoded_value": block.get("section_group") if block.get("section_group") is not None else 403
                    }

            layout_count = len(layout_types)
            if layout_count == 0:
                st.info("No structure architecture frameworks detected.")
            else:
                st.markdown("#### 🗺️ Current Active Database Layout Formations")
                top_cols = st.columns(max(layout_count, 2))
                
                for idx, (label, data) in enumerate(layout_types.items()):
                    with top_cols[idx]:
                        st.markdown(f"📦 **Current saved pattern for {data['type_string'].upper()}**")
                        
                        enc_val = data["encoded_value"]
                        if enc_val > 100:
                            saved_rows = int(enc_val // 100)
                            saved_cols = int(enc_val % 100)
                        else:
                            if enc_val == 12: saved_rows, saved_cols = 3, 4
                            elif enc_val == 6: saved_rows, saved_cols = 2, 3
                            else: saved_rows, saved_cols = 4, 3
                        
                        h_px = int(data["h_cells"] * 18)
                        w_px = int(data["w_cells"] * 26)
                        total_pts = int(saved_rows * saved_cols)

                        html_current_view = f"""
                        <div style="background:#0f172a; padding:10px; border-radius:8px; text-align:center; font-family:sans-serif;">
                            <canvas id="saved_canvas_{idx}" width="320" height="200" style="background:#020617; border:2px solid #22c55e; border-radius:6px;"></canvas>
                            <div style="color:#64748b; font-size:11px; margin-top:4px;">Database Value: {total_pts} Pins ({saved_rows} Rows × {saved_cols} Columns)</div>
                        </div>
                        <script>
                            (function() {{
                                const canvas = document.getElementById("saved_canvas_{idx}");
                                const ctx = canvas.getContext('2d');
                                const rows = {saved_rows};
                                const cols = {saved_cols};
                                const boxW = {w_px}; const boxH = {h_px};
                                
                                const bx = (canvas.width / 2) - (boxW / 2); 
                                const by = (canvas.height / 2) - (boxH / 2);
                                
                                ctx.fillStyle = '#1e293b'; ctx.fillRect(bx, by, boxW, boxH);
                                ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 2; ctx.strokeRect(bx, by, boxW, boxH);
                                
                                if(rows > 0 && cols > 0) {{
                                    const rowGap = (rows === 1) ? boxH / 2 : boxH / (rows - 1);
                                    const colGap = (cols === 1) ? boxW / 2 : boxW / (cols - 1);
                                    
                                    for(let r = 0; r < rows; r++) {{
                                        for(let c = 0; c < cols; c++) {{
                                            let px = (cols === 1) ? bx + (boxW / 2) : bx + (c * colGap);
                                            let py = (rows === 1) ? by + (boxH / 2) : by + (r * rowGap);
                                            
                                            ctx.fillStyle = '#22c55e';
                                            ctx.beginPath();
                                            ctx.arc(px, py, 4.5, 0, Math.PI * 2);
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
                        components.html(html_current_view, height=220)

                st.write("---")
                st.markdown("#### ⚙️ Layout Architecture Blueprint Adjustments Deck")
                selected_layout_label = st.selectbox("Select Model Template Variant to Configure Layout Pins Amount:", list(layout_types.keys()))
                
                target_layout = layout_types[selected_layout_label]
                state_prefix = f"layout_cfg_{selected_layout_label}"
                
                if f"{state_prefix}_rows" not in st.session_state: st.session_state[f"{state_prefix}_rows"] = 3
                if f"{state_prefix}_cols" not in st.session_state: st.session_state[f"{state_prefix}_cols"] = 4

                col_inputs, col_actions = st.columns([4, 6])
                with col_inputs:
                    row_pts = st.number_input("Array Points per Row Count (Rows stacked vertically):", min_value=1, max_value=20, key=f"{state_prefix}_rows")
                    col_pts = st.number_input("Array Points per Column Count (Columns lined horizontally):", min_value=1, max_value=20, key=f"{state_prefix}_cols")
                    
                    total_calculated_points = row_pts * col_pts
                    st.metric(label="Calculated Configuration Pins", value=f"{total_calculated_points} Pts / Unit")
                    
                    if st.button("💾 Apply & Replicate Fleetwide Structure Patterns", type="primary", use_container_width=True):
                        with st.spinner("Broadcasting layout modifications to cloud ecosystem records..."):
                            try:
                                encoded_group_signature = int((row_pts * 100) + col_pts)
                                supabase.table("structures").update({
                                    "section_group": encoded_group_signature
                                }).eq("farm_id", st.session_state.active_site_id).eq("structure_type", target_layout["type_string"]).execute()
                                
                                st.cache_resource.clear()
                                st.success("Updated fleet configuration profiles cleanly!")
                                time.sleep(0.5); st.rerun()
                            except Exception as e:
                                st.error(f"Transmission mutation failure occurred: {str(e)}")

                with col_actions:
                    h_px_prev = int(target_layout["h_cells"] * 18)
                    w_px_prev = int(target_layout["w_cells"] * 26)
                    
                    html_micro_template = f"""
                    <div style="background:#0f172a; padding:15px; border-radius:12px; text-align:center; font-family:sans-serif;">
                        <div style="margin-bottom: 8px; font-size:12px; color:#94a3b8;">Auto-Updating Local Matrix Preview (Before Saving)</div>
                        <canvas id="micro_canvas" width="400" height="220" style="background:#020617; border:1px dashed #38bdf8; border-radius:8px;"></canvas>
                    </div>
                    <script>
                        (function() {{
                            const canvas = document.getElementById("micro_canvas");
                            const ctx = canvas.getContext('2d');
                            const rows = {row_pts}; const cols = {col_pts};
                            const boxW = {w_px_prev}; const boxH = {h_px_prev};
                            const bx = (canvas.width / 2) - (boxW / 2); const by = (canvas.height / 2) - (boxH / 2);
                            
                            ctx.fillStyle = '#1e293b'; ctx.fillRect(bx, by, boxW, boxH);
                            ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2; ctx.strokeRect(bx, by, boxW, boxH);
                            
                            if(rows > 0 && cols > 0) {{
                                const rowGap = (rows === 1) ? boxH / 2 : boxH / (rows - 1);
                                const colGap = (cols === 1) ? boxW / 2 : boxW / (cols - 1);
                                for(let r = 0; r < rows; r++) {{
                                    for(let c = 0; c < cols; c++) {{
                                        let px = (cols === 1) ? bx + (boxW / 2) : bx + (c * colGap);
                                        let py = (rows === 1) ? by + (boxH / 2) : by + (r * rowGap);
                                        ctx.fillStyle = '#f43f5e'; ctx.beginPath(); ctx.arc(px, py, 4.5, 0, Math.PI * 2); ctx.fill();
                                        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.stroke();
                                    }}
                                }}
                            }}
                        }})();
                    </script>
                    """
                    components.html(html_micro_template, height=270)

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
                        <label style="display:block; margin-bottom:10px; cursor:pointer;"><input type="radio" name="topo_tool" value="route"> 🔗 Route Inverters to MVS (Click / Drag Lasso)</label>
                        <hr style="border-color:#1e293b; margin:14px 0;">
                        <h5 style="margin-top:0; margin-bottom:8px; color:#a78bfa; font-size:12px;">ACTIVE IDENTIFICATION</h5>
                        <label style="font-size:11px; color:#94a3b8;">Target Inverter ID #:</label>
                        <input type="number" id="topo_inv_token" value="20" min="1" style="width:100%; background:#1e293b; color:white; border:1px solid #334155; border-radius:4px; padding:5px; margin-bottom:12px; box-sizing:border-box;">
                        <hr style="border-color:#1e293b; margin:14px 0;">
                        <button id="btn_topo_save" style="width:100%; background:#22c55e; border:none; padding:10px 0px; color:white; font-weight:bold; border-radius:4px; cursor:pointer; font-size:13px; line-height:normal; height:auto;">💾 Save Topologies</button>
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
                    let lassoSelectedInvertersList = [];

                    canvas.addEventListener("contextmenu", e => e.preventDefault());
                    function getActiveTool() { return document.querySelector('input[name="topo_tool"]:checked').value; }

                    function getCapacityColor(stringCount) {
                        if (stringCount <= 0) return "#1e293b";
                        const palette = ["#10b981", "#06b6d4", "#8b5cf6", "#f43f5e", "#ec4899", "#3b82f6", "#14b8a6", "#f59e0b", "#6366f1", "#a855f7"];
                        return palette[(stringCount - 1) % palette.length];
                    }
                    function isInverterPlaced(invId) { return gridTopo.inverters.some(i => i.id === parseInt(invId)); }

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.save(); ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);

                        gridTopo.inverters.forEach(inv => {
                            if (inv.transformerId !== null && gridTopo.transformers[inv.transformerId]) {
                                let xf = gridTopo.transformers[inv.transformerId];
                                ctx.strokeStyle = "rgba(56, 189, 248, 0.85)"; ctx.lineWidth = 2.0; ctx.beginPath();
                                ctx.moveTo(inv.x, inv.y); ctx.lineTo(xf.x, xf.y); ctx.stroke();
                            }
                        });

                        let counts = {};
                        Object.values(gridTopo.stringGroups).forEach(id => { counts[id] = (counts[id] || 0) + 1; });

                        independentStrings.forEach(s => {
                            let x = s.min_c * CELL; let y = s.min_r * CELL;
                            let w = (s.max_c - s.min_c + 1) * CELL; let h = (s.max_r - s.min_r + 1) * CELL;
                            let linkedInv = gridTopo.stringGroups[s.id];
                            ctx.fillStyle = linkedInv ? (isInverterPlaced(linkedInv) ? getCapacityColor(counts[linkedInv]) : "#d97706") : "#1e293b";
                            ctx.fillRect(x, y, w, h);
                            if (!linkedInv) { ctx.strokeStyle = "rgba(255, 255, 255, 0.12)"; ctx.lineWidth = 0.5; ctx.strokeRect(x, y, w, h); }
                        });

                        gridTopo.inverters.forEach(inv => {
                            let strCount = counts[inv.id] || 0;
                            let tsPrefix = inv.transformerId !== null && gridTopo.transformers[inv.transformerId] ? "TS" + (inv.transformerId + 1) + "-" : "";
                            let titleText = tsPrefix + "IN" + String(inv.id).padStart(3, '0');
                            let countText = strCount + " STRINGS";
                            ctx.font = "bold 9px sans-serif";
                            let badgeW = Math.max(ctx.measureText(titleText).width + 12, ctx.measureText(countText).width + 12, 65);
                            let badgeH = 26; let bx = inv.x - (badgeW / 2); let by = inv.y - (badgeH / 2);
                            ctx.fillStyle = "#ff0000"; ctx.fillRect(bx, by, badgeW, badgeH / 2);
                            ctx.fillStyle = getCapacityColor(strCount); ctx.fillRect(bx, by + (badgeH / 2), badgeW, badgeH / 2);
                            ctx.fillStyle = "#ffffff"; ctx.textAlign = "center";
                            ctx.fillText(titleText, inv.x, by + 9); ctx.fillText(countText, inv.x, by + 21);
                            ctx.strokeStyle = lassoSelectedInvertersList.includes(inv.id) ? "#facc15" : "#ffffff";
                            ctx.lineWidth = lassoSelectedInvertersList.includes(inv.id) ? 3.5 : 1; ctx.strokeRect(bx, by, badgeW, badgeH);
                        });

                        gridTopo.transformers.forEach((t, i) => {
                            ctx.fillStyle = "#ff1744"; ctx.fillRect(t.x - 18, t.y - 18, 36, 36);
                            ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.strokeRect(t.x - 18, t.y - 18, 36, 36);
                            ctx.fillStyle = "#ffffff"; ctx.font = "bold 10px sans-serif"; ctx.textAlign = "center";
                            ctx.fillText("TS " + (i + 1), t.x, t.y + 4);
                        });
                        ctx.restore();

                        if (isSelecting && (getActiveTool() === "string" || getActiveTool() === "route")) {
                            ctx.strokeStyle = getActiveTool() === "string" ? "#a78bfa" : "#38bdf8"; ctx.lineWidth = 1.5;
                            ctx.fillStyle = getActiveTool() === "string" ? "rgba(167, 139, 250, 0.2)" : "rgba(56, 189, 248, 0.2)";
                            ctx.fillRect(startX, startY, currX - startX, currY - startY); ctx.strokeRect(startX, startY, currX - startX, currY - startY);
                        }
                    }

                    function getMouseLocation(e) { const rect = canvas.getBoundingClientRect(); return { x: e.clientX - rect.left, y: e.clientY - rect.top }; }
                    function transformToWorldSpace(p) { return { x: (p.x - offsetX) / scale, y: (p.y - offsetY) / scale }; }

                    canvas.addEventListener("mousedown", e => {
                        const m = getMouseLocation(e); const world = transformToWorldSpace(m); const tool = getActiveTool();
                        if (e.button === 2) {
                            if (tool === "transformer") {
                                let tIdx = gridTopo.transformers.findIndex(t => Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 25);
                                if (tIdx !== -1) {
                                    gridTopo.transformers.splice(tIdx, 1);
                                    gridTopo.inverters.forEach(i => { if (i.transformerId === tIdx) i.transformerId = null; else if (i.transformerId > tIdx) i.transformerId -= 1; });
                                }
                                draw(); return;
                            }
                            if (tool === "inverter") {
                                gridTopo.inverters = gridTopo.inverters.filter(inv => {
                                    let isHit = Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 20;
                                    if (isHit) { Object.keys(gridTopo.stringGroups).forEach(key => { if (gridTopo.stringGroups[key] === inv.id) delete gridTopo.stringGroups[key]; }); }
                                    return !isHit;
                                });
                                draw(); return;
                            }
                            isPanning = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; canvas.style.cursor = "move"; return;
                        }

                        if (tool === "pan") { isPanning = true; startX = e.clientX - offsetX; startY = e.clientY - offsetY; canvas.style.cursor = "move"; }
                        else if (tool === "string" || tool === "route") {
                            if (tool === "route") {
                                let clickedInv = gridTopo.inverters.find(inv => Math.sqrt(Math.pow(world.x - inv.x, 2) + Math.pow(world.y - inv.y, 2)) <= 25);
                                if (clickedInv) {
                                    if (lassoSelectedInvertersList.includes(clickedInv.id)) { lassoSelectedInvertersList = lassoSelectedInvertersList.filter(id => id !== clickedInv.id); }
                                    else { lassoSelectedInvertersList.push(clickedInv.id); }
                                    draw(); return;
                                }
                                let clickedXfmrIdx = gridTopo.transformers.findIndex(t => Math.sqrt(Math.pow(world.x - t.x, 2) + Math.pow(world.y - t.y, 2)) <= 25);
                                if (clickedXfmrIdx !== -1 && lassoSelectedInvertersList.length > 0) {
                                    gridTopo.inverters.forEach(inv => { if (lassoSelectedInvertersList.includes(inv.id)) inv.transformerId = clickedXfmrIdx; });
                                    lassoSelectedInvertersList = []; draw(); return;
                                }
                            }
                            isSelecting = true; startX = m.x; startY = m.y; currX = m.x; currY = m.y;
                        } else if (tool === "inverter") {
                            let hitStruct = databaseStructures.find(b => world.x >= b.min_c*CELL && world.x <= (b.max_c+1)*CELL && world.y >= b.min_r*CELL && world.y <= (b.max_r+1)*CELL);
                            if (hitStruct) {
                                let invId = parseInt(document.getElementById("topo_inv_token").value) || 20;
                                gridTopo.inverters = gridTopo.inverters.filter(i => i.id !== invId);
                                gridTopo.inverters.push({ id: invId, x: (hitStruct.min_c * CELL) + (((hitStruct.max_c - hitStruct.min_c + 1) * CELL) / 2), y: (hitStruct.min_r * CELL) + (((hitStruct.max_r - hitStruct.min_r + 1) * CELL) / 2), transformerId: null });
                                draw();
                            }
                        } else if (tool === "transformer") {
                            let hitStr = independentStrings.find(s => world.x >= s.min_c*CELL && world.x <= (s.max_c+1)*CELL && world.y >= s.min_r*CELL && world.y <= (s.max_r+1)*CELL);
                            if (!hitStr) { gridTopo.transformers.push({ x: world.x, y: world.y }); draw(); }
                        }
                    });

                    canvas.addEventListener("mousemove", e => {
                        const m = getMouseLocation(e); const world = transformToWorldSpace(m);
                        if (isPanning) { offsetX = e.clientX - startX; offsetY = e.clientY - startY; draw(); return; }
                        else if (isSelecting) { currX = m.x; currY = m.y; draw(); return; }
                        let match = false;
                        if (!match) tooltip.style.display = "none";
                    });

                    canvas.addEventListener("mouseup", e => {
                        if (e.button === 2 || isPanning) { isPanning = false; canvas.style.cursor = "default"; return; }
                        if (isSelecting) {
                            isSelecting = false; const mUp = getMouseLocation(e);
                            const p1 = transformToWorldSpace(getMouseLocation({ clientX: startX + canvas.getBoundingClientRect().left, clientY: startY + canvas.getBoundingClientRect().top }));
                            const p2 = transformToWorldSpace(mUp);
                            let x1 = Math.min(p1.x, p2.x), x2 = Math.max(p1.x, p2.x), y1 = Math.min(p1.y, p2.y), y2 = Math.max(p1.y, p2.y);
                            let dist = Math.sqrt(Math.pow(mUp.x - startX, 2) + Math.pow(mUp.y - startY, 2));

                            if (getActiveTool() === "route") {
                                if (dist > 5) { gridTopo.inverters.forEach(inv => { if (inv.x >= x1 && inv.x <= x2 && inv.y >= y1 && inv.y <= y2) { if (!lassoSelectedInvertersList.includes(inv.id)) lassoSelectedInvertersList.push(inv.id); } }); }
                                draw(); return;
                            }
                            let activeInv = parseInt(document.getElementById("topo_inv_token").value) || 20;
                            let isLassoSelection = dist > 5;
                            let boxSelected = independentStrings.filter(s => {
                                let cx = s.min_c * CELL; let cy = s.min_r * CELL;
                                let cw = (s.max_c - s.min_c + 1) * CELL; let ch = (s.max_r - s.min_r + 1) * CELL;
                                return isLassoSelection ? (cx >= x1 && cx <= x2 && cy >= y1 && cy <= y2) : (x1 >= cx && x1 <= cx + cw && y1 >= cy && y1 <= cy + ch);
                            });
                            boxSelected.forEach(s => { if (!gridTopo.stringGroups[s.id] || gridTopo.stringGroups[s.id] === activeInv) { if (!isLassoSelection && gridTopo.stringGroups[s.id] === activeInv) delete gridTopo.stringGroups[s.id]; else gridTopo.stringGroups[s.id] = activeInv; } });
                            draw();
                        }
                    });

                    document.getElementById("btn_topo_save").addEventListener("click", async () => {
                        await fetch("SUPABASE_URL_VAL/rest/v1/farms?id=eq.ACTIVE_SITE_ID_VAL", {
                            method: "PATCH",
                            headers: { "apikey": "SUPABASE_KEY_VAL", "Authorization": "Bearer SUPABASE_KEY_VAL", "Content-Type": "application/json" },
                            body: JSON.stringify({ "background_image_url": json.dumps(gridTopo) })
                        });
                        alert("Topologies committed safely!");
                    });

                    canvas.addEventListener("wheel", e => {
                        e.preventDefault(); const m = getMouseLocation(e); const world = transformToWorldSpace(m);
                        scale *= (e.deltaY < 0 ? 1.15 : 0.85); scale = Math.max(0.01, Math.min(scale, 20));
                        offsetX = m.x - world.x * scale; offsetY = m.y - world.y * scale; draw();
                    }, { passive: false });
                    draw();
                })();
            </script>
            """
            html_topology_workspace = html_topology_workspace.replace("__JSON_DATA_B64__", b64_json_data)\
                                                             .replace("__TOPOLOGY_METADATA_B64__", base64.b64encode(stored_metadata_string.encode("utf-8")).decode("utf-8"))\
                                                             .replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c))\
                                                             .replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r))\
                                                             .replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)\
                                                             .replace("ACTIVE_SITE_ID_VAL", str(st.session_state.active_site_id))
            components.html(html_topology_workspace, height=660)

        # --- STAGE 4: EXECUTIVE SUMMARY TAB ---
        with setup_tabs[3]:
            st.markdown("## 📊 Executive Analytical Summary Dashboard Panel")
            try: topo_meta = json.loads(current_farm_record.get("background_image_url") or "{}")
            except Exception: topo_meta = {}
            inverters_list = topo_meta.get("inverters", [])
            transformers_list = topo_meta.get("transformers", [])
            string_groups = topo_meta.get("stringGroups", {})
            
            global_inv_string_distribution = {}
            for str_id, inv_id in string_groups.items():
                global_inv_string_distribution[inv_id] = global_inv_string_distribution.get(inv_id, 0) + 1
            
            st.subheader("Whole Plant Operational Fleet Totals")
            layout_analysis = {}
            grand_total_trackers = 0
            grand_total_pegging_points = 0
            
            for block in active_table_data:
                l_type = block.get("structure_type", "single_3x9")
                enc_val = block.get("section_group") if block.get("section_group") is not None else 403
                pins_per_unit = (int(enc_val // 100) * int(enc_val % 100)) if enc_val > 100 else 12
                
                if l_type not in layout_analysis:
                    layout_analysis[l_type] = {"tracker_count": 0, "total_pins": 0}
                layout_analysis[l_type]["tracker_count"] += 1
                layout_analysis[l_type]["total_pins"] += pins_per_unit
                grand_total_trackers += 1
                grand_total_pegging_points += pins_per_unit

            st.metric("Total Tracker Structures", f"{grand_total_trackers} Units")

        # --- STAGE 5: ASPECT TIMELINE MASTER SCHEDULER ---
        with setup_tabs[4]:
            st.markdown("### 🗓️ Project Scheduling Timeline Assignation Deck")
            sched_res = supabase.table("aspect_schedules").select("*").eq("farm_id", st.session_state.active_site_id).execute().data
            schedules_index = {(item["zone_label"], item["aspect_key"]): item for item in sched_res}
            
            with st.form("scheduling_batch_form"):
                col_sch1, col_sch2 = st.columns(2)
                with col_sch1: select_sz = st.selectbox("Target Operations Zone Registry:", st.session_state.managed_zones)
                with col_sch2: select_sa = st.selectbox("Target Construction Aspect Phase:", list(aspects_dictionary.keys()), format_func=lambda x: aspects_dictionary[x])
                
                match_existing = schedules_index.get((select_sz, select_sa), {})
                default_start = datetime.strptime(match_existing["start_date"], "%Y-%m-%d").date() if match_existing else date.today()
                default_end = datetime.strptime(match_existing["end_date"], "%Y-%m-%d").date() if match_existing else date.today() + timedelta(days=14)
                
                col_dp1, col_dp2 = st.columns(2)
                with col_dp1: val_start = st.date_input("Scheduled Commencement Date:", value=default_start, key="sch_start")
                with col_dp2: val_end = st.date_input("Scheduled Target Finalization Date:", value=default_end, key="sch_end")
                
                if st.form_submit_button("💾 Synchronize Operational Schedule Bounds"):
                    payload = {
                        "farm_id": st.session_state.active_site_id, "zone_label": select_sz,
                        "aspect_key": select_sa, "start_date": str(val_start), "end_date": str(val_end)
                    }
                    if match_existing: supabase.table("aspect_schedules").update(payload).eq("id", match_existing["id"]).execute()
                    else: supabase.table("aspect_schedules").insert(payload).execute()
                    st.success("Timeline schedule metrics written down cleanly!")
                    time.sleep(0.5); st.rerun()

            if sched_res:
                st.markdown("#### Active Production Pipeline Matrix Targets Summary")
                sched_table_summary = []
                for s in sched_res:
                    w_days = calculate_working_days(datetime.strptime(s["start_date"], "%Y-%m-%d").date(), datetime.strptime(s["end_date"], "%Y-%m-%d").date())
                    sched_table_summary.append({
                        "Zone Allocation Target": s["zone_label"],
                        "Aspect Pipeline Stage": s["aspect_key"].upper(),
                        "Commencement Bounds Date": s["start_date"],
                        "Target Delivery Boundary": s["end_date"],
                        "Calculated Productive Working Days": f"{w_days} Days"
                    })
                st.table(sched_table_summary)

        # --- STAGE 6: PROGRESS HISTORY & LOG VIEWER ---
        with setup_tabs[5]:
            st.markdown("### 📈 Engineering Analytics Execution Log & Dynamic Timeline Rollup")
            history_aspect = st.selectbox("Select Filter Category View Aspect:", list(aspects_dictionary.keys()), format_func=lambda x: aspects_dictionary[x])
            history_date = st.date_input("Select Historical State Target Snapshot Date:", value=date.today())
            
            logs_res = supabase.table("daily_progress_log").select("*").eq("farm_id", st.session_state.active_site_id).order("log_date", desc=True).execute().data
            if logs_res:
                formatted_logs = [{
                    "Logged Date Index": l["log_date"],
                    "Zone Region Label": l["zone_label"],
                    "Construction Aspect Stage": l["aspect_key"].upper(),
                    "Calculated Daily Incremental Output": f"+{l['installed_count']} Units Added",
                    "Crew Remarks Journal": l["remark"] if l["remark"] else "-"
                } for l in logs_res]
                st.table(formatted_logs)
            else: st.info("No field completion journal events verified across this database record scope.")

    # ==============================================================================
    # 🇲🇾 REGION B: FIELD INSTALLER CREW OPERATION TRACKING ENGINE WORKSPACE
    # ==============================================================================
    else:
        if not site_is_published:
            st.error("🛑 **Access Restricted:** The operational blueprint for this site layout has not been deployed or finalized by the administrator yet.")
            st.stop()
            
        if site_bg_img and not site_bg_img.startswith("{"):
            st.markdown("### 🗺️ Master Blueprint Reference Layout")
            st.image(site_bg_img, use_container_width=False, width=700)
            st.write("---")

        crew_aspect_keys = ["pegging", "piling", "mounting", "module", "inverter_struct", "inverter", "transformer_station", "dc_cabling", "ac_cabling"]
        crew_tabs = st.tabs([aspects_dictionary.get(k, k) for k in crew_aspect_keys])
        
        op_date = get_operational_date()
        sched_res = supabase.table("aspect_schedules").select("*").eq("farm_id", st.session_state.active_site_id).execute().data
        schedules_index = {(item["zone_label"], item["aspect_key"]): item for item in sched_res}
        progress_res = supabase.table("daily_progress_log").select("*").eq("farm_id", st.session_state.active_site_id).eq("log_date", str(op_date)).execute().data

        for a_idx, a_key in enumerate(crew_aspect_keys):
            with crew_tabs[a_idx]:
                
                # --- EMBED GRAPHICS INTERACTIVE MULTI-SELECT CANVAS tracker MODULES ---
                html_crew_engine = f"""
                <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select:none; font-family:sans-serif;">
                    <canvas id="crew_canvas_{a_key}" width="1400" height="450" style="background:#020617; display:block; border-radius:6px; cursor:crosshair;"></canvas>
                    <div id="crew_bar" style="position:absolute; bottom:20px; left:20px; background:rgba(30,41,59,0.95); border:2px solid #22c55e; padding:12px; border-radius:8px; display:none; color:white; font-size:13px; box-shadow:0 10px 25px rgba(0,0,0,0.5);">
                        Selected Cluster Index Components Mapped: <span id="crw_sel_count" style="font-weight:bold; color:#22c55e;">0</span> &nbsp;|&nbsp; 
                        <button id="crw_cmt_btn" style="background:#22c55e; border:none; padding:6px 12px; color:white; font-weight:bold; border-radius:4px; cursor:pointer;">Stage Changes Locally</button>
                    </div>
                </div>
                <script>
                    (function() {{
                        const blocks = JSON.parse(atob("{b64_json_data}"));
                        const topo = JSON.parse(atob("{b64_topo_data}"));
                        const canvas = document.getElementById("crew_canvas_{a_key}");
                        const ctx = canvas.getContext('2d');
                        const aspect = "{a_key}";
                        const CELL = 14;
                        let scale = 0.6, offsetX = 40, offsetY = 40;
                        let isSelecting = false, isPanning = false, startX=0, startY=0, curX=0, curY=0;
                        let localSelectionMap = {{}};

                        function isBlockHostToInverter(b) {{
                            if(!topo.inverters) return false;
                            return topo.inverters.some(inv => (inv.x >= b.min_c*CELL && inv.x <= (b.max_c+1)*CELL) && (inv.y >= b.min_r*CELL && inv.y <= (b.max_r+1)*CELL));
                        }}

                        function draw() {{
                            ctx.clearRect(0,0,canvas.width,canvas.height);
                            ctx.save(); ctx.translate(offsetX,offsetY); ctx.scale(scale,scale);
                            
                            blocks.forEach(b => {{
                                let isLocked = false;
                                if((aspect==='inverter_struct' || aspect==='inverter' || aspect==='ac_cabling') && !isBlockHostToInverter(b)) isLocked = true;
                                if(aspect==='transformer_station') isLocked = true; 
                                
                                let totalElements = 1, completedElements = 0;
                                let enc = b.section_group || 403;
                                let r_f = Math.floor(enc/100), c_f = enc%100;
                                
                                if(aspect==='pegging' || aspect==='piling' || aspect==='module') {{
                                    totalElements = r_f * c_f;
                                    let stateArr = b[aspect+'_pins_state'] || [];
                                    completedElements = stateArr.filter(p => p.status==='completed').length;
                                }} else {{
                                    if(b[aspect+'_status']==='completed') completedElements = 1;
                                }}
                                
                                if(isLocked) ctx.fillStyle = '#1e293b';
                                else if(completedElements === totalElements) ctx.fillStyle = '#22c55e';
                                else if(completedElements > 0) ctx.fillStyle = '#eab308';
                                else ctx.fillStyle = '#3b82f6';
                                
                                if(localSelectionMap[b.id]) ctx.fillStyle = '#facd15';
                                
                                let bx = b.min_c*CELL, by = b.min_r*CELL;
                                let bw = (b.max_c-b.min_c+1)*CELL, bh = (b.max_r-b.min_r+1)*CELL;
                                ctx.fillRect(bx, by, bw, bh);
                                
                                if(!isLocked && (aspect==='pegging' || aspect==='piling' || aspect==='module')) {{
                                    ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth=0.5;
                                    let rg = bh/r_f, cg = bw/c_f;
                                    for(let i=1; i<r_f; i++) {{ ctx.beginPath(); ctx.moveTo(bx, by+i*rg); ctx.lineTo(bx+bw, by+i*rg); ctx.stroke(); }}
                                    for(let j=1; j<c_f; j++) {{ ctx.beginPath(); ctx.moveTo(bx+j*cg, by); ctx.lineTo(bx+j*cg, by+bh); ctx.stroke(); }}
                                }}
                                ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth = 0.5; ctx.strokeRect(bx, by, bw, bh);
                            }});
                            
                            if(topo.transformers) {{
                                topo.transformers.forEach((t, i) => {{
                                    ctx.fillStyle = '#ef4444'; ctx.fillRect(t.x-14, t.y-14, 28, 28);
                                    ctx.strokeStyle = '#ffffff'; ctx.lineWidth=1.5; ctx.strokeRect(t.x-14, t.y-14, 28, 28);
                                }});
                            }}
                            ctx.restore();
                            if(isSelecting) {{
                                ctx.strokeStyle='#22c55e'; ctx.fillStyle='rgba(34,197,94,0.15)';
                                ctx.fillRect(startX,startY,curX-startX,curY-startY); ctx.strokeRect(startX,startY,curX-startX,curY-startY);
                            }}
                        }}

                        canvas.addEventListener('mousedown', e => {{
                            let r = canvas.getBoundingClientRect(); let x = e.clientX-r.left, y = e.clientY-r.top;
                            if(e.button===2) {{ isPanning=true; startX=e.clientX-offsetX; startY=e.clientY-offsetY; }}
                            else {{ isSelecting=true; startX=x; startY=y; curX=x; curY=y; }}
                        }});
                        canvas.addEventListener('mousemove', e => {{
                            let r = canvas.getBoundingClientRect(); let x = e.clientX-r.left, y = e.clientY-r.top;
                            if(isPanning) {{ offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); }}
                            else if(isSelecting) {{ curX=x; curY=y; draw(); }}
                        }});
                        canvas.addEventListener('mouseup', e => {{
                            if(isPanning) isPanning=false;
                            if(isSelecting) {{
                                isSelecting = false;
                                let x1 = Math.min(startX,curX), x2 = Math.max(startX,curX);
                                let y1 = Math.min(startY,curY), y2 = Math.max(startY,curY);
                                
                                blocks.forEach(b => {{
                                    let cx = b.min_c*CELL*scale+offsetX, cy = b.min_r*CELL*scale+offsetY;
                                    if(cx>=x1 && cx<=x2 && cy>=y1 && cy<=y2) {{ localSelectionMap[b.id] = !localSelectionMap[b.id]; }}
                                }});
                                let activeSelSize = Object.values(localSelectionMap).filter(Boolean).length;
                                document.getElementById("crew_bar").style.display = activeSelSize ? "block" : "none";
                                document.getElementById("crw_sel_count").innerText = activeSelSize;
                                draw();
                            }}
                        }});
                        canvas.addEventListener('wheel', e => {{
                            e.preventDefault(); let r = canvas.getBoundingClientRect(); let mx = e.clientX-r.left, my = e.clientY-r.top;
                            let wx = (mx-offsetX)/scale, wy = (my-offsetY)/scale;
                            scale *= (e.deltaY<0?1.15:0.85); scale=Math.max(0.1,Math.min(scale,10));
                            offsetX = mx-wx*scale; offsetY = my-wy*scale; draw();
                        }}, {{passive:false}});
                        
                        document.getElementById("crw_cmt_btn").addEventListener('click', async () => {{
                            let targetIds = Object.keys(localSelectionMap).filter(k => localSelectionMap[k]);
                            for(let id of targetIds) {{
                                let b = blocks.find(x => x.id == id);
                                let updateBody = {{}};
                                if(aspect==='pegging' || aspect==='piling' || aspect==='module') {{
                                    let enc = b.section_group || 403; let total = Math.floor(enc/100)*(enc%100);
                                    let fullState = []; for(let i=0; i<total; i++) fullState.push({{index:i, status:'completed'}});
                                    updateBody[aspect+'_pins_state'] = fullState;
                                }} else {{
                                    updateBody[aspect+'_status'] = 'completed';
                                }}
                                await fetch('{SUPABASE_URL}/rest/v1/structures?id=eq.'+id, {{
                                    method: 'PATCH', headers: {{ 'apikey':'{SUPABASE_KEY}', 'Authorization':'Bearer {SUPABASE_KEY}', 'Content-Type':'application/json' }},
                                    body: JSON.stringify(updateBody)
                                }});
                            }}
                            alert("Staging completed successfully! Click 'Save and Update Table' below to confirm ledger outputs.");
                            window.location.reload();
                        }});
                        draw();
                    }})();
                </script>
                """
                components.html(html_crew_engine, height=480)

                # --- 📊 DYNAMIC TIMELINE OPERATIONAL LEDGER METRICS TABLES ---
                st.markdown("##### 📊 Dynamic Timeline Operations Progress Verification Ledger")
                zone_submissions_index = {}
                progress_index = {item["zone_label"]: item for item in progress_res if item["aspect_key"] == a_key}

                for zone in all_zones_list:
                    zone_blocks = [b for b in active_table_data if b.get("assigned_zone", "Unassigned") == zone]
                    if not zone_blocks and zone != "Unassigned": continue
                    
                    total_scope_units = 0
                    for b in zone_blocks:
                        enc = b.get("section_group", 403)
                        sub_pins = int(enc // 100) * int(enc % 100)
                        if a_key in ["pegging", "piling", "module"]: total_scope_units += sub_pins
                        else: total_scope_units += 1

                    sched = schedules_index.get((zone, a_key), None)
                    if sched:
                        w_days = calculate_working_days(datetime.strptime(sched["start_date"], "%Y-%m-%d").date(), datetime.strptime(sched["end_date"], "%Y-%m-%d").date())
                        daily_target = math.ceil(total_scope_units / w_days) if w_days > 0 else total_scope_units
                    else:
                        daily_target = 0
                    
                    saved_log = progress_index.get(zone, {})
                    
                    st.markdown(f"###### 📍 Production Row Metrics: `{zone.upper()}`")
                    col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns([2, 2, 2, 2, 4])
                    
                    with col_l1: st.text_input("Log Date:", value=str(op_date), disabled=True, key=f"dt_{a_key}_{zone}")
                    with col_l2: st.number_input("Target Per Day:", value=int(daily_target), disabled=True, key=f"tgt_{a_key}_{zone}")
                    
                    # TIMELINE BOUNDARY ENFORCEMENT ENGINE
                    is_row_locked = False if (st.session_state.is_admin_mode and st.session_state.time_travel_date) or (op_date == date.today()) else True
                    
                    with col_l3: crew_installed_num = st.number_input("Installed Today Amount:", min_value=0, max_value=max(total_scope_units, 1), value=int(saved_log.get("installed_count", 0)), disabled=is_row_locked, key=f"ins_{a_key}_{zone}")
                    with col_l4: st.text_input("Calculated Deviation Variance:", value=f"{crew_installed_num - daily_target} Pts", disabled=True, key=f"dev_{a_key}_{zone}")
                    with col_l5: crew_remark_txt = st.text_input("Field Crew Remark Notes Line:", value=saved_log.get("remark", ""), disabled=is_row_locked, key=f"rem_{a_key}_{zone}")
                    
                    zone_submissions_index[zone] = {
                        "installed_count": crew_installed_num, "remark": crew_remark_txt, "existing_id": saved_log.get("id", None)
                    }
                
                if st.button("💾 Save and Update Table Records Matrix", key=f"save_ledger_{a_key}", type="primary", use_container_width=True):
                    with st.spinner("Writing production progress snapshots..."):
                        for z_name, pl in zone_submissions_index.items():
                            db_payload = {
                                "farm_id": st.session_state.active_site_id, "log_date": str(op_date),
                                "zone_label": z_name, "aspect_key": a_key,
                                "installed_count": int(pl["installed_count"]), "remark": str(pl["remark"])
                            }
                            if pl["existing_id"]: supabase.table("daily_progress_log").update(db_payload).eq("id", pl["existing_id"]).execute()
                            else: supabase.table("daily_progress_log").insert(db_payload).execute()
                        st.success("🎉 Workspace ledger tables updated completely!"); time.sleep(0.5); st.rerun()
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transmission protocol transaction failed: {str(e)}")

        # --- AFTER MIDNIGHT AUTOLOCK COLOR & TIME-TRAVEL STATE PARSER ---
        # This section checks and updates the color-rendering rules based on midnight shifts
        # Yellow items roll over to permanent locked green fields
        today_str = str(date.today())
        for block in active_table_data:
            needs_update = False
            update_payload = {}
            
            for state_key in ["pegging", "piling", "modules"]:
                state_field = f"{state_key if state_key != 'modules' else 'modules'}_state"
                arr = block.get(state_field) or []
                item_changed = False
                for item in arr:
                    # If status is logged as temporary yellow staging but date has passed midnight
                    if item.get("status") == "completed_staged" and item.get("date") != today_str:
                        item["status"] = "completed"
                        item_changed = True
                        needs_update = True
                if item_changed:
                    update_payload[state_field] = arr

            for status_key in ["mounting", "inverter_struct", "inverter", "transformer_station", "dc_cabling", "ac_cabling"]:
                db_status_field = f"{status_key}_status" if status_key == "mounting" else f"{status_key if 'struct' in status_key or 'cabling' in status_key else status_key + '_status'}"
                db_date_field = f"{status_key}_date" # Assume matching layout tracking dates fields exist
                
                if block.get(db_status_field) == "completed_staged" and block.get(db_date_field) != today_str:
                    update_payload[db_status_field] = "completed"
                    needs_update = True
            
            if needs_update:
                try:
                    supabase.table("structures").update(update_payload).eq("id", block["id"]).execute()
                except Exception:
                    pass
                    # --- DYNAMIC CUSTOM TABS RENDERER ---
        # Appends all user-instantiated tabs built dynamically via the Admin Panel Deck
        for c_idx, ct_name in enumerate(st.session_state.custom_tabs):
            # Calculate tab index offset matching standard array properties keys rules
            tab_offset = len(crew_aspect_keys) + c_idx
            with crew_tabs[tab_offset]:
                st.markdown(f"#### Live Crew Field View Grid Framework: 🛠️ **{ct_name.upper()}**")
                
                # Render standard baseline grid tracking map for custom built layers
                components.html(inject_crew_tracking_map(f"custom_{ct_name}", b64_json_data, min_c, max_c, min_r, max_r), height=640)
                
                # Build ledger target lines matrices rows for custom aspect tracking columns
                custom_submissions_index = {}
                for zone in all_zones_list:
                    zone_blocks = [b for b in active_table_data if b.get("assigned_zone", "Unassigned") == zone]
                    if not zone_blocks and zone != "Unassigned": continue
                    
                    st.markdown(f"###### 📍 Production Row Metrics: `{zone.upper()}`")
                    col_c1, col_l2, col_l3, col_l4, col_l5 = st.columns([2, 2, 2, 2, 4])
                    
                    with col_c1: st.text_input("Log Date:", value=str(op_date), disabled=True, key=f"dt_custom_{ct_name}_{zone}")
                    with col_l2: st.number_input("Target Per Day:", value=0, disabled=True, key=f"tgt_custom_{ct_name}_{zone}")
                    
                    is_row_locked = False if (st.session_state.is_admin_mode and st.session_state.time_travel_date) or (op_date == date.today()) else True
                    
                    with col_l3: crew_installed_num = st.number_input("Installed Today Amount:", min_value=0, value=0, disabled=is_row_locked, key=f"ins_custom_{ct_name}_{zone}")
                    with col_l4: st.text_input("Calculated Deviation Variance:", value="0 Pts", disabled=True, key=f"dev_custom_{ct_name}_{zone}")
                    with col_l5: crew_remark_txt = st.text_input("Field Crew Remark Notes Line:", value="", disabled=is_row_locked, key=f"rem_custom_{ct_name}_{zone}")
                    
                st.button("💾 Save and Update Custom Table Records Matrix Snapshot", key=f"save_custom_ledger_{ct_name}", type="primary", use_container_width=True)
