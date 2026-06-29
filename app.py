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
                            except Exception as e: st.error(f"Purge rejected: {str(e)}")
                
                st.write("---")
                st.subheader("🚀 Onboard New Layout Framework")
                new_site_name = st.text_input("Assign Site Project Name:")
                init_admin_pwd = st.text_input("Assign Management Password:", value="ok")
                init_inst_pwd = st.text_input("Assign Field Access Password:", value="1234")
                
                uploaded_blueprint = st.file_uploader("Upload Master Blueprint Sheet (.xlsx)", type=["xlsx"])
                
                if uploaded_blueprint and new_site_name and st.button("Compile & Parse Structural Blueprint"):
                    st.info("🔄 Running Strict Isolated Row Matrix Scanner...")
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
                            if farm_node.data: new_fid = farm_node.data[0]["id"]
                        except Exception as e: st.error(f"❌ Database registration failed: {str(e)}")
                        
                        if new_fid:
                            structures_queue = []
                            table_counter = 1
                            
                            # Strict row-by-row scanning to preserve 3x9 independent structures
                            for r in range(1, max_rows + 1):
                                start_c = None
                                for c in range(1, max_cols + 1):
                                    cell = sheet.cell(row=r, column=c)
                                    has_val = cell.value is not None and str(cell.value).strip() != ""
                                    has_fill = cell.fill and cell.fill.fill_type is not None and cell.fill.fill_type != 'none'
                                    
                                    if has_val or has_fill:
                                        if start_c is None:
                                            start_c = c
                                    else:
                                        if start_c is not None:
                                            # Found isolated contiguous block horizontal span within this specific row
                                            structures_queue.append({
                                                "farm_id": new_fid,
                                                "table_label": f"T-{table_counter}",
                                                "min_r": int(r), "max_r": int(r),
                                                "min_c": int(start_c), "max_c": int(c - 1),
                                                "structure_type": "single_3x9",
                                                "assigned_zone": "Unassigned",
                                                "section_group": int(table_counter),
                                                "pegging_status": "pending", "piling_status": "pending", 
                                                "mounting_status": "pending", "modules_status": "pending"
                                            })
                                            table_counter += 1
                                            start_c = None
                                if start_c is not None:
                                    structures_queue.append({
                                        "farm_id": new_fid, "table_label": f"T-{table_counter}",
                                        "min_r": int(r), "max_r": int(r), "min_c": int(start_c), "max_c": int(max_cols),
                                        "structure_type": "single_3x9", "assigned_zone": "Unassigned", "section_group": int(table_counter),
                                        "pegging_status": "pending", "piling_status": "pending", "mounting_status": "pending", "modules_status": "pending"
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
                                
                                st.success(f"🎉 Processed {success_count} Strict Independent Cell Records.")
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
                    st.success("Workspace deployed cleanly! Fields locked.")
                    time.sleep(1); st.rerun()
            else:
                st.success("✅ Layout Workspace Status: Locked & Live")
                if st.button("🔓 Emergency Revoke & Unfreeze Project"):
                    supabase.table("farms").update({"is_published": False}).eq("id", st.session_state.active_site_id).execute()
                    st.rerun()

    def load_site_isolated_tables(farm_id):
        all_data = []
        limit = 1000, offset = 0
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
        except Exception: return [], []

    active_table_data = load_site_isolated_tables(st.session_state.active_site_id)
    transformers_data, inverters_data = load_electrical_nodes(st.session_state.active_site_id)

    if not active_table_data:
        st.warning("ℹ️ No tracker operational layout vectors loaded yet.")
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

    # ==============================================================================
    # ⚡ ADMIN MODE ROUTING
    # ==============================================================================
    if st.session_state.is_admin_mode:
        setup_tabs = st.tabs(["🖼️ Base Overview & Zones", "🔌 Unified Master Electrical Canvas"])
        
        with setup_tabs[0]:
            st.markdown("### 🖼️ Zone Management Overview")
            # Baseline Zone Assignation HTML engine maps can be injected here.
            
        with setup_tabs[1]:
            st.markdown("### 🔌 Bottom-Up Master Electrical Infrastructure Layout Setup")
            
            mode_selector = st.radio("Select Electrical Step Mode Sequence:", [
                "Step 1: DC Cabling (String Grouping Assignment)",
                "Step 2: Place Electrical Inverter System Boxes",
                "Step 3: Transformer Network Drop Hub Stations"
            ], horizontal=True)

            active_mode_id = 1 if "Step 1" in mode_selector else (2 if "Step 2" in mode_selector else 3)
            chosen_parent_tx = "None"
            
            if active_mode_id == 2:
                tx_names = [tx["name"] for tx in transformers_data]
                chosen_parent_tx = st.selectbox("Assign Active Parent Transformer Target:", ["None"] + tx_names)

            html_electrical_master = """
            <div style="background:#090d16; padding:12px; border-radius:12px; position:relative; touch-action:none; user-select: none; font-family:sans-serif;">
                <div id="elec_tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); color: #f8fafc; border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 99999; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.5);"></div>
                <div style="width:100%; max-height:600px; border:2px solid #1e293b; border-radius:8px; overflow:hidden;">
                    <canvas id="elec_canvas" width="1500" height="600" style="background:#020617; display:block;"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    let blocks = JSON.parse(atob("__JSON_DATA_B64__"));
                    let txNodes = JSON.parse(atob("__TX_DATA_B64__"));
                    let invNodes = JSON.parse(atob("__INV_DATA_B64__"));
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
                    function getStringColor(s) { if(!s) return null; let h=0; for(let i=0;i<s.length;i++) h=s.charCodeAt(i)+((h<<5)-h); return `hsl(${Math.abs(h*75)%360}, 95%, 55%)`; }

                    function draw() {
                        ctx.clearRect(0,0,canvas.width,canvas.height); ctx.save(); ctx.translate(offsetX,offsetY); ctx.scale(scale,scale);
                        
                        // Render completely independent rows
                        blocks.forEach(b => {
                            ctx.fillStyle = '#1e293b';
                            let x=b.min_c*CELL, y=b.min_r*CELL, w=(b.max_c-b.min_c+1)*CELL, h=(b.max_r-b.min_r+1)*CELL;
                            ctx.fillRect(x,y,w,h); ctx.strokeStyle='#334155'; ctx.lineWidth=0.5; ctx.strokeRect(x,y,w,h);
                            if(b.string_cabling_group) { ctx.strokeStyle = getStringColor(b.string_cabling_group); ctx.lineWidth = 2.5; ctx.strokeRect(x+1,y+1,w-2,h-2); }
                        });
                        
                        // Render Electrical Node Assets
                        txNodes.forEach(tx => { ctx.fillStyle='#eab308'; ctx.fillRect(tx.grid_c*CELL, tx.grid_r*CELL, CELL*2, CELL*2); });
                        invNodes.forEach(inv => { ctx.fillStyle=(activeInvSelectionId===inv.id)?'#ffff00':'#ef4444'; ctx.fillRect(inv.grid_c*CELL, inv.grid_r*CELL, CELL, CELL); });
                        ctx.restore();
                        if(isSelecting && mode===1) { ctx.strokeStyle='#22c55e'; ctx.lineWidth=1.5; ctx.strokeRect(startX,startY,currentX-startX,currentY-startY); }
                    }

                    canvas.addEventListener('mousemove', e => {
                        const rect = canvas.getBoundingClientRect(); const mX = e.clientX-rect.left, mY = e.clientY-rect.top;
                        if(isPanning) { offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); return; }
                        if(isSelecting) { currentX=mX; currentY=mY; draw(); return; }
                        
                        let wX=(mX-offsetX)/scale, wY=(mY-offsetY)/scale;
                        
                        // 1. Instant Inverter (Red Box) Hover Diagnostics
                        let hInv=null;
                        for(let inv of invNodes) { 
                            let ix=inv.grid_c*CELL, iy=inv.grid_r*CELL; 
                            if(wX>=ix && wX<=ix+CELL && wY>=iy && wY<=iy+CELL) { hInv=inv; break; }
                        }
                        if(hInv) {
                            let streamCount = blocks.filter(b => b.inverter_id === (hInv.transformer_name+'-'+hInv.inverter_num)).length;
                            tooltip.style.display="block"; tooltip.style.left=(mX+15)+"px"; tooltip.style.top=(mY+15)+"px";
                            tooltip.innerHTML=`Inverter Block ID: ${hInv.transformer_name}-${hInv.inverter_num}<br/>Parent Feed Hub: ${hInv.transformer_name}<br/>Total Connected DC Strings: ${streamCount}`;
                            return;
                        }
                        
                        // 2. Tracker Row Cell Hover Info
                        let hb=null;
                        for(let b of blocks) { if(wX>=b.min_c*CELL && wX<=(b.max_c+1)*CELL && wY>=b.min_r*CELL && wY<=(b.max_r+1)*CELL) { hb=b; break; }}
                        if(hb) {
                            tooltip.style.display="block"; tooltip.style.left=(mX+15)+"px"; tooltip.style.top=(mY+15)+"px";
                            tooltip.innerHTML=`Cell Label: ${hb.table_label}<br/>Zone: ${hb.assigned_zone}<br/>Inverter Link: ${hb.inverter_id || 'Unassigned'}<br/>String Cabling Code: ${hb.string_cabling_group || 'Unassigned'}`;
                            return;
                        } tooltip.style.display="none";
                    });

                    canvas.addEventListener('mousedown', async e => {
                        const rect=canvas.getBoundingClientRect(); const mX=e.clientX-rect.left, mY=e.clientY-rect.top;
                        let wX=Math.floor(((mX-offsetX)/scale)/CELL), wY=Math.floor(((mY-offsetY)/scale)/CELL);
                        if(e.button===2) { isPanning=true; startX=e.clientX-offsetX; startY=e.clientY-offsetY; return; }
                        
                        if(mode===1) {
                            let hitInv = invNodes.find(inv => wX===inv.grid_c && wY===inv.grid_r);
                            if(hitInv) { activeInvSelectionId = hitInv.transformer_name + "-" + hitInv.inverter_num; draw(); }
                            else if(activeInvSelectionId) { isSelecting=true; startX=mX; startY=mY; currentX=mX; currentY=mY; }
                        } else if(mode===2) {
                            let existingInv = invNodes.find(inv => inv.grid_c===wX && inv.grid_r===wY);
                            if(existingInv) {
                                if(confirm("Delete Inverter Unit Component?")) {
                                    invNodes = invNodes.filter(i => i.id !== existingInv.id); draw();
                                    fetch("SUPABASE_URL_VAL/rest/v1/inverters?id=eq."+existingInv.id,{method:"DELETE",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL"}});
                                }
                            } else {
                                if(parentTxName==="None") return;
                                let num=prompt("Enter Inverter Identifier Label Number:");
                                if(num) {
                                    let newInv = {id:Math.random().toString(), farm_id:farmId, transformer_name:parentTxName, inverter_num:num, grid_r:wY, grid_c:wX};
                                    invNodes.push(newInv); draw(); // Dynamic Instant UI Render
                                    fetch("SUPABASE_URL_VAL/rest/v1/inverters",{method:"POST",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({farm_id:farmId,transformer_name:parentTxName,inverter_num:num,grid_r:wY,grid_c:wX})});
                                }
                            }
                        } else if(mode===3) {
                            let existingTx = txNodes.find(tx => tx.grid_c===wX && tx.grid_r===wY);
                            if(existingTx) {
                                if(confirm("Delete Transformer Node Hub?")) {
                                    txNodes = txNodes.filter(t => t.id !== existingTx.id); draw();
                                    fetch("SUPABASE_URL_VAL/rest/v1/transformers?id=eq."+existingTx.id,{method:"DELETE",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL"}});
                                }
                            } else {
                                let name=prompt("Assign New Transformer Station ID Hub Label:");
                                if(name) {
                                    let newTx = {id:Math.random().toString(), farm_id:farmId, name:name, grid_r:wY, grid_c:wX};
                                    txNodes.push(newTx); draw(); // Dynamic Instant UI Render
                                    fetch("SUPABASE_URL_VAL/rest/v1/transformers",{method:"POST",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({farm_id:farmId,name:name,grid_r:wY,grid_c:wX})});
                                }
                            }
                        }
                    });

                    canvas.addEventListener('mouseup', async e => {
                        if(isPanning) isPanning=false;
                        else if(isSelecting && mode===1 && activeInvSelectionId) {
                            isSelecting=false; const rect=canvas.getBoundingClientRect();
                            let x1=Math.min(startX,e.clientX-rect.left), x2=Math.max(startX,e.clientX-rect.left), y1=Math.min(startY,e.clientY-rect.top), y2=Math.max(startY,e.clientY-rect.top);
                            let targetIds=[];
                            blocks.forEach(b => {
                                let cx=b.min_c*CELL*scale+offsetX, cy=b.min_r*CELL*scale+offsetY;
                                if(cx>=x1 && cx<=x2 && cy>=y1 && cy<=y2) { targetIds.push(b.id); b.string_cabling_group="Staging"; b.inverter_id=activeInvSelectionId; }
                            });
                            if(targetIds.length>0) {
                                let stringCode=prompt("Assign DC String Code Tracking Vector Group:");
                                if(stringCode) {
                                    blocks.forEach(b => { if(b.string_cabling_group==="Staging") b.string_cabling_group=stringCode; }); draw(); // Update UI on the fly
                                    for(let id of targetIds) {
                                        fetch("SUPABASE_URL_VAL/rest/v1/structures?id=eq."+id,{method:"PATCH",headers:{"apikey":"SUPABASE_KEY_VAL","Authorization":"Bearer SUPABASE_KEY_VAL","Content-Type":"application/json"},body:JSON.stringify({inverter_id:activeInvSelectionId,string_cabling_group:stringCode})});
                                    }
                                } else { blocks.forEach(b => { if(b.string_cabling_group==="Staging") { b.string_cabling_group=null; b.inverter_id=null; } }); draw(); }
                            } else draw();
                        }
                    });
                    canvas.addEventListener('wheel', e => { e.preventDefault(); const rect=canvas.getBoundingClientRect(); const mX=e.clientX-rect.left, mY=e.clientY-rect.top, gX=(mX-offsetX)/scale, gY=(mY-offsetY)/scale; scale*=(e.deltaY<0?1.15:0.85); scale=Math.max(0.01,Math.min(scale,15)); offsetX=mX-gX*scale; offsetY=mY-gY*scale; draw(); }, {passive:false});
                    draw();
                })();
            </script>
            """.replace("__JSON_DATA_B64__", b64_json_data).replace("__TX_DATA_B64__", b64_tx_data).replace("__INV_DATA_B64__", b64_inv_data).replace("__ACTIVE_MODE__", str(active_mode_id)).replace("__PARENT_TX__", chosen_parent_tx).replace("__FARM_ID__", str(st.session_state.active_site_id)).replace("MIN_C_VAL", str(min_c)).replace("MAX_C_VAL", str(max_c)).replace("MIN_R_VAL", str(min_r)).replace("MAX_R_VAL", str(max_r)).replace("SUPABASE_URL_VAL", SUPABASE_URL).replace("SUPABASE_KEY_VAL", SUPABASE_KEY)
            components.html(html_electrical_master, height=660)
