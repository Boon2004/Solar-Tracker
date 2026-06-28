# Automatically detect sheet size boundaries from existing structural data assets
            max_sheet_r = max([b.get("max_r", 0) for b in active_table_data]) + 5 if active_table_data else 100
            max_sheet_c = max([b.get("max_c", 0) for b in active_table_data]) + 5 if active_table_data else 100

            json_str = json.dumps(active_table_data)
            html_engine = """
            <div style="background:#090d16; padding:12px; border-radius:12px; user-select: none;">
                <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">✨ <b>Admin Section Tool:</b> Clicking any tracker will instantly select and assign its entire 5-row/col separated group.</div>
                <canvas id="zone_painter" width="1500" height="550" style="background:#020617; border-radius:8px; width:100%; cursor:pointer;"></canvas>
            </div>
            <script>
                (function() {
                    const blocks = """ + json_str + """;
                    const canvas = document.getElementById("zone_painter");
                    const ctx = canvas.getContext('2d');
                    const paintZone = '""" + target_paint_zone + """';
                    
                    const CELL_W = 10.0; 
                    const CELL_H = 10.0;

                    const totalRows = """ + str(max_sheet_r) + """;
                    const totalCols = """ + str(max_sheet_c) + """;

                    const totalWidth = totalCols * CELL_W;
                    const totalHeight = totalRows * CELL_H;

                    let scale = Math.min((canvas.width - 40) / totalWidth, (canvas.height - 40) / totalHeight);
                    if (scale <= 0 || scale === Infinity) scale = 0.5;

                    let offsetX = (canvas.width / 2) - (totalWidth * scale / 2);
                    let offsetY = (canvas.height / 2) - (totalHeight * scale / 2);

                    function draw() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height); 
                        ctx.save(); 
                        ctx.translate(offsetX, offsetY); 
                        ctx.scale(scale, scale);

                        blocks.forEach(b => {
                            let az = b.assigned_zone || "Unassigned";
                            if (az === 'Zone A') ctx.fillStyle = '#ff4b4b'; 
                            else if (az === 'Zone B') ctx.fillStyle = '#00f0ff'; 
                            else if (az === 'Zone C') ctx.fillStyle = '#eab308'; 
                            else ctx.fillStyle = '#334155';

                            let x = b.min_c * CELL_W;
                            let y = b.min_r * CELL_H;
                            let w = (b.max_c - b.min_c + 1) * CELL_W - 0.5;
                            let h = (b.max_r - b.min_r + 1) * CELL_H - 0.5;

                            ctx.fillRect(x, y, w, h);
                            ctx.strokeStyle = '#0f172a';
                            ctx.lineWidth = 0.5;
                            ctx.strokeRect(x, y, w, h);
                        });

                        ctx.restore();
                    }

                    canvas.addEventListener('click', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const clickX = (e.clientX - rect.left - offsetX) / scale;
                        const clickY = (e.clientY - rect.top - offsetY) / scale;

                        let targetBlock = null;

                        // 1. Find which specific string tracker was clicked
                        blocks.forEach(b => {
                            let bXStart = b.min_c * CELL_W;
                            let bXEnd = (b.max_c + 1) * CELL_W;
                            let bYStart = b.min_r * CELL_H;
                            let bYEnd = (b.max_r + 1) * CELL_H;

                            if (clickX >= bXStart && clickX <= bXEnd && clickY >= bYStart && clickY <= bYEnd) {
                                targetBlock = b;
                            }
                        });

                        // 2. If a tracker was hit, group and paint all trackers inside that same section boundary
                        if (targetBlock) {
                            blocks.forEach(b => {
                                // Since sections are separated by 5 rows/columns, we check if strings share 
                                // the same structural cluster alignment (within a 15-cell neighborhood window)
                                const rowDistance = Math.abs(b.min_r - targetBlock.min_r);
                                const colDistance = Math.abs(b.min_c - targetBlock.min_c);

                                // If they belong to the same large group chunk (not blocked by a 5-row/col blank channel)
                                if (rowDistance < 25 && colDistance < 25) {
                                    b.assigned_zone = paintZone;
                                    
                                    fetch('""" + SUPABASE_URL + """/rest/v1/structures?id=eq.' + b.id, {
                                        method: "PATCH", 
                                        headers: { 
                                            "apikey": '""" + SUPABASE_KEY + """', 
                                            "Authorization": 'Bearer """ + SUPABASE_KEY + """', 
                                            "Content-Type": "application/json" 
                                        },
                                        body: JSON.stringify({ "assigned_zone": paintZone })
                                    });
                                }
                            });
                            draw();
                        }
                    });

                    draw();
                })();
            </script>
            """
            components.html(html_engine, height=590)
