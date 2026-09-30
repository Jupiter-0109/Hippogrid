"""Generate SQL inserts for Supabase database."""
import pandas as pd
from pathlib import Path

raw_dir = Path("e:/HippoGrid/data/raw")
phcs_df = pd.read_csv(raw_dir / "phcs.csv")

values = []
for _, r in phcs_df.iterrows():
    val = (
        f"('{r['district_code']}', '{r['code']}', '{r['name']}', 'PHC', {r['latitude']}, {r['longitude']}, "
        f"{r['catchment_population']}, {r['remote_flag']}, {r['vulnerability_score']}, {r['total_beds']}, "
        f"{r['staff_mo']}, {r['staff_nurse']}, {r['staff_anm']}, '{r['backup_power_type']}', "
        f"{r['backup_power_capacity_kva']}, {r['backup_power_hours']}, {r['solar_capacity_kw']})"
    )
    values.append(val)

joined_values = ',\n'.join(values)
sql = f"""INSERT INTO phcs (
    district_id, code, name, facility_type, latitude, longitude,
    catchment_population, remote_flag, vulnerability_score, total_beds,
    staff_mo, staff_nurse, staff_anm, backup_power_type,
    backup_power_capacity_kva, backup_power_hours, solar_capacity_kw
)
SELECT d.id, p.code, p.name, p.facility_type, p.latitude, p.longitude,
       p.catchment_population, p.remote_flag, p.vulnerability_score, p.total_beds,
       p.staff_mo, p.staff_nurse, p.staff_anm, p.backup_power_type,
       p.backup_power_capacity_kva, p.backup_power_hours, p.solar_capacity_kw
FROM (VALUES
{joined_values}
) AS p(
    district_code, code, name, facility_type, latitude, longitude,
    catchment_population, remote_flag, vulnerability_score, total_beds,
    staff_mo, staff_nurse, staff_anm, backup_power_type,
    backup_power_capacity_kva, backup_power_hours, solar_capacity_kw
)
JOIN districts d ON d.code = p.district_code
ON CONFLICT (code) DO NOTHING;
"""

with open("e:/HippoGrid/scripts/insert_phcs.sql", "w", encoding="utf-8") as f:
    f.write(sql)
print("Saved insert_phcs.sql successfully, rows:", len(phcs_df))
