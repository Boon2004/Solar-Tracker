import streamlit as st
import streamlit.components.v1 as components
import openpyxl
from supabase import create_client, Client
import json
from datetime import datetime, date

# Pre-loaded live project credentials
SUPABASE_URL = "https://pysicrdtjayyxztoibep.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5c2ljcmR0amF5eXh6dG9pYmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0Mjk4NzMsImV4cCI6MjA5ODAwNTg3M30.5X0uesuo7NVf6KDxrEiM-6RIOJ2ffyxcOVsWJF52oNw"                 

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

st.set_page_config(layout="wide", page_title="Universal Solar Twin Cloud")
st.title("🚜 Universal Solar Farm EPC Digital Twin Platform")

# --- PHASE 1: SYSTEM DYNAMIC MULTI-SITE SELECTOR HUB ---
@st.cache_data(ttl=2)
def get_available_farms():
    try:
        res = supabase.table("farms").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

all_farms = get_available_farms()
farm_names = [f["name"] for f in all_farms]

# Sidebar authentication controller
with st.sidebar:
    st.header("🌐 Project Site Selector Hub")
    onboarding_mode = st.checkbox("➕ Onboard / Upload New Solar Site Layout")
    
    selected_farm_id = None
    user_authenticated = False
    is_admin = False
    
    if not onboarding_mode and farm_names:
        chosen_site_name = st.selectbox("Select Active Work Location Site:", farm_names)
        current_site_data = next(f for f in all_farms if f["name"] == chosen_site_name)
        selected_farm_id = current_site_data["id"]
        
        expected_site_pass = current_site_data.get("site_password") or "1234"
        expected_admin_pass = current_site_data.get("admin_password") or "ok"
        
        site_pwd = st.text_input("Enter Field Installer Password:", type="password", key="site_pwd")
        if str(site_pwd) == str(expected_site_pass):
            user_authenticated = True
            st.success("🔓 Site Access Granted")
            
            admin_pwd = st.text_input("Elevate to Administrator Mode (Optional):", type="password", key="admin_pwd")
            if str(admin_pwd) == str(expected_admin_pass):
                is_admin = True
                st.info("⚡ Admin Clearances Active")
        elif site_pwd:
            st.error("Incorrect Installer password credential.")
    elif not farm_names and not onboarding_mode:
        st.warning("No sites stored in cloud directory. Check the checkbox above to onboard your first layout file!")

# --- PHASE 2: AUTOMATED LAYOUT FILENAME UPLOADER ---
if onboarding_mode:
    st.header("🚀 Blueprint Template Onboarding Console")
    st.write("Upload your engineering layout spreadsheet (.xlsx file).")
    
    uploaded_file = st.file_uploader("Drop your blueprint file here", type=["xlsx"])
    if uploaded_file:
        raw_filename = uploaded_file.name.rsplit('.', 1)[0]
        st.info(f"Detected Project Asset Label: **{raw_filename}**")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1: new_s_pass = st.text_input("Set Installer Password for this site:", value="1234")
        with col_p2: new_a_pass = st.text_input("Set Admin Password for this site:", value="ok")
        
        if st.button(f"Compile & Deploy {raw_filename} To Enterprise Cloud"):
            with st.spinner("Parsing grid coordinate boundaries safely..."):
                wb = openpyxl.load_workbook(uploaded_file, data_only=True)
                sheet = wb.active
                
                # Double-tap security guard: clear old matching site rows cleanly
                try:
                    supabase.table("farms").delete().eq("name", raw_filename).execute()
                except Exception:
                    pass
                
                # Secure registration payload
                farm_res = supabase.table("farms").insert({
                    "name": raw_filename, "site_password": new_s_pass, "admin_password": new_a_pass
                }).execute()
                
                if farm_res.data:
                    new_farm_id = farm_res.data[0]["id"]
                else:
                    st.error("Cloud insertion rejected. Check table column naming models.")
                    st.stop()
                
                max_rows, max_cols = sheet.max_row, sheet.max_column
                visited = set()
                table_counter = 1
                structures_batch = []
                
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
                            
                            h, w = max_br - min_br + 1, max_bc - min_bc + 1
                            stype = "double_6x9" if h >= 6 else "single_3x9"
                            
                            structures_batch.append({
                                "farm_id": new_farm_id, 
                                "table_label": f"{raw_filename}-T{table_counter}",
                                "min_r": int(min_br), "max_r": int(max_br), 
                                "min_c": int(min_bc), "max_c": int(max_bc),
                                "structure_type": stype
                            })
                            table_counter += 1
                
                if structures_batch:
                    chunk_size = 300
                    for i in range(0, len(structures_batch), chunk_size):
                        supabase.table("structures").insert(structures_batch[i:i+chunk_size]).execute()
                    st.success(f"Success! {len(structures_batch)} layout tables cleanly registered to cloud.")
                    st.cache_data.clear()
                    st.rerun()

# --- PHASE 3: ISOLATED WORKSPACE VIEWPORT RENDERING ---
elif user_authenticated and selected_farm_id:
    @st.cache_data(ttl=2)
    def load_site_isolated_tables(farm_id):
        res = supabase.table("structures").select("min_r, max_r, min_c, max_c, table_label, structure_type, pegging_status, piling_status, mounting_status, dc_cabling_status").eq("farm_id", farm_id).execute()
        return res.data if res.data else []

    active_table_data = load_site_isolated_tables(selected_farm_id)
    
    def render_map_script(layer_id, data_points):
        json_str = json.dumps(data_points)
        return f"""
        <div style="background:#090d16; padding:12px; border-radius:12px; color:#fff; font-family:sans-serif; touch-action:none;">
            <canvas id="canvas_{layer_id}" width="1500" height="480" style="background:#020617; border-radius:8px; width:100%; cursor:grab; touch-action:none;"></canvas>
        </div>
        <script>
            (function() {{
                const blocks = {json_str};
                const canvas = document.getElementById("canvas_{layer_id}");
                const ctx = canvas.getContext('2d');
                
                let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                blocks.forEach(b => {{
                    if (b.min_c < minX) minX = b.min_c; if (b.max_c > maxX) maxX = b.max_c;
                    if (b.min_r < minY) minY = b.min_r; if (b.max_r > maxY) maxY = b.max_r;
                }});
                
                const gw = (maxX - minX) || 1, gh = (maxY - minY) || 1;
                
                let scale = Math.min((canvas.width - 100) / gw, (canvas.height - 100) / (gh * 4));
                if(scale < 0.005 || scale === Infinity) scale = 0.4;
                
                let offsetX = (canvas.width / 2) - ((gw * scale) / 2) - (minX * scale);
                let offsetY = (canvas.height / 2) - ((gh * 4 * scale) / 2) - (minY * 4 * scale);
                
                let isDragging = false, startX, startY, initialDist = null;

                function draw() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height); 
                    ctx.save(); 
                    ctx.translate(offsetX, offsetY); 
                    ctx.scale(scale, scale);
                    
                    blocks.forEach(b => {{
                        let status = 'pending';
                        if("{layer_id}" === "peg") status = b.pegging_status;
                        else if("{layer_id}" === "pil") status = b.piling_status;
                        else if("{layer_id}" === "mnt") status = b.mounting_status;
                        else if("{layer_id}" === "cab") status = b.dc_cabling_status;
                        
                        ctx.fillStyle = status === 'completed' ? '#22c55e' : '#2563eb';
                        
                        const w = b.max_c - b.min_c + 1;
                        const h = (b.max_r - b.min_r + 1) * 4;
                        
                        ctx.fillRect(b.min_c, b.min_r * 4, w, h);
                        ctx.strokeStyle = '#ffffff'; 
                        ctx.lineWidth = 0.2; 
                        ctx.strokeRect(b.min_c, b.min_r * 4, w, h);
                    }});
                    ctx.restore();
                }}
                
                canvas.addEventListener('mousedown',(e)=>{{ isDragging=true; startX=e.clientX-offsetX; startY=e.clientY-offsetY; }});
                canvas.addEventListener('mousemove',(e)=>{{ if(!isDragging)return; offsetX=e.clientX-startX; offsetY=e.clientY-startY; draw(); }});
                window.addEventListener('mouseup',()=>isDragging=false);
                canvas.addEventListener('wheel',(e)=>{{ e.preventDefault(); scale*=(e.deltaY<0?1.1:0.9); draw(); }},{{passive:false}});
                
                canvas.addEventListener('touchstart',(e)=>{{
                    if(e.touches.length===1){{ isDragging=true; startX=e.touches[0].clientX-offsetX; startY=e.touches[0].clientY-offsetY; }}
                    else if(e.touches.length===2){{ isDragging=false; initialDist=Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY); }}
                }});
                canvas.addEventListener('touchmove',(e)=>{{
                    if(isDragging && e.touches.length===1){{ offsetX=e.touches[0].clientX-startX; offsetY=e.touches[0].clientY-startY; draw(); }}
                    else if(e.touches.length===2 && initialDist){{
                        const d = Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
                        scale*=(d>initialDist?1.04:0.96); initialDist=d; draw();
                    }}
                }});
                canvas.addEventListener('touchend',()=>{{ isDragging=false; initialDist=null; }});
                
                draw();
            }})();
        </script>
        """

    def render_ledger_dashboard(label, total_count, done_count):
        st.subheader(f"📊 {label} Phase Tracker Ledger Spreadsheet")
        st.table([{
            "Operational Step": f"{label} Progress", "Total Site Volume": f"{total_count:,}",
            "Verified Complete": f"{done_count:,}", "Remaining Units": f"{total_count - done_count:,}",
            "Daily Run-Rate Target": f"{round(total_count/44,1)} / Day", "Status Notes": "Active database link live"
        }])

    t_peg, t_pil, t_mnt, t_mod, t_cab = st.tabs(["📌 Pegging Stage", "🪵 Piling Stage", "🏗️ Mounting Structure", "☀️ PV Module Large Grid", "🔌 DC Cabling Matrix"])
    total_t = len(active_table_data)
    
    with t_peg:
        st.header("📌 Pegging Tracking Viewport")
        if active_table_data: components.html(render_map_script("peg", active_table_data), height=510)
        done = sum(1 for b in active_table_data if b.get("pegging_status") == "completed")
        render_ledger_dashboard("Pegging", total_t * 12, done * 12)
        
    with t_pil:
        st.header("🪵 Piling Foundation Viewport")
        if active_table_data: components.html(render_map_script("pil", active_table_data), height=510)
        done = sum(1 for b in active_table_data if b.get("piling_status") == "completed")
        render_ledger_dashboard("Piling", total_t * 12, done * 12)
        
    with t_mnt:
        st.header("🏗️ Mounting Frame Tracker")
        if active_table_data: components.html(render_map_script("mnt", active_table_data), height=510)
        done = sum(1 for b in active_table_data if b.get("mounting_status") == "completed")
        render_ledger_dashboard("Mounting Structures", total_t, done)
        
    with t_mod:
        st.header("☀️ PV Module Scale Mapping")
        if active_table_data: components.html(render_map_script("mod", active_table_data), height=510)
        render_ledger_dashboard("PV Modules Mounted", total_t * 54, 0)
        
    with t_cab:
        st.header("🔌 DC Cabling Layout Interconnection")
        if active_table_data: components.html(render_map_script("cab", active_table_data), height=510)
        done = sum(1 for b in active_table_data if b.get("dc_cabling_status") == "completed")
        render_ledger_dashboard("DC Cabling Matrix Blocks", total_t, done)
        
else:
    st.info("🔒 Please select a work location site and insert the valid security credentials to populate the interactive digital twin layout blueprint mapping screens.")
