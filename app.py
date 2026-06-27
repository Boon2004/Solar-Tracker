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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5c2ljcmR0amF5eXh6dG9pYmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI4Mjk4NzMsImV4cCI6MjA5ODAwNTg3M30.5X0uesuo7NVf6KDxrEiM-6RIOJ2ffyxcOVsWJF52oNw"                 

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# Set Global Wide View Constraints
st.set_page_config(layout="wide", page_title="Boon Solar Farm Tracking System")

# Helper function to compute business days (weekdays only)
def get_working_days(start_d, end_d):
    days = 0
    curr = start_d
    while curr <= end_d:
        if curr.weekday() < 5:  # Monday to Friday
            days += 1
        curr += timedelta(days=1)
    return max(days, 1)

# Initialize Session State States
if "active_site_id" not in st.session_state:
    st.session_state.active_site_id = None
if "is_admin_mode" not in st.session_state:
    st.session_state.is_admin_mode = False

# Fetch all registered site platforms from cloud registry
@st.cache_data(ttl=1)
def fetch_farms_directory():
    try:
        res = supabase.table("farms").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception:
        return []

all_registered_farms = fetch_farms_directory()
farm_options = [f["name"] for f in all_registered_farms]

# ==============================================================================
# 🏡 PHASE 1: MAIN SYSTEM HOME SCREEN GATEWAY
# ==============================================================================
if st.session_state.active_site_id is None:
    st.title("🚜 Boon Solar Farm Tracking System")
    st.write("---")
    
    with st.sidebar:
        with st.expander("⚙️ Developer Master Control Panel", expanded=False):
            dev_pwd = st.text_input("Enter Developer Password:", type="password")
            if dev_pwd == "devok":
                st.success("Developer Access Unlocked")
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
                        
                        # BULLETPROOF RE-ENGINEERED CRASH-PROOF OVERWRITE GATEWAY
                        new_fid = None
                        try:
                            existing_farm = supabase.table("farms").select("id").eq("name", new_site_name).execute()
                            if existing_farm.data and len(existing_farm.data) > 0:
                                new_fid = existing_farm.data[0]["id"]
                                supabase.table("structures").delete().eq("farm_id", new_fid).execute()
                        except Exception:
                            pass
                        
                        if not new_fid:
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
                            
                            chunk_size = 50
                            for idx in range(0, len(structures_queue), chunk_size):
                                try:
                                    supabase.table("structures").insert(structures_queue[idx:idx+chunk_size]).execute()
                                except Exception:
                                    pass
                                time.sleep(0.04)
                                
                            st.success(f"Successfully deployed {len(structures_queue)} layout tables!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Database connection refused. Ensure you completed Step 1 in your Supabase SQL Tab first.")

    st.subheader("🌐 Access Site Workspace Portal")
    if farm_options:
        chosen_farm_name = st.selectbox("Select Active Project Location Site:", farm_options)
        target_site_record = next(f for f in all_registered_farms if f["name"] == chosen_farm_name)
        entered_inst_pass = st.text_input("Enter Field Installer Password:", type="password")
        
        if
