INSERT INTO phcs (
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
('DST-A1', 'PHC-DST-A1-01', 'PHC North Sector-1', 'PHC', 24.67979, 73.912265, 36702, False, 2.24, 6, 1, 3, 4, 'DIESEL_GENERATOR', 25.0, 24.0, 5.0),
('DST-A1', 'PHC-DST-A1-02', 'PHC North Sector-2', 'PHC', 24.495859, 73.917376, 35888, False, 1.89, 8, 1, 3, 4, 'DIESEL_GENERATOR', 20.0, 24.0, 0.0),
('DST-A1', 'PHC-DST-A1-03', 'PHC North Sector-3', 'PHC', 24.45074, 73.710295, 31750, False, 2.47, 4, 2, 4, 3, 'DIESEL_GENERATOR', 20.0, 24.0, 5.0),
('DST-A1', 'PHC-DST-A1-04', 'PHC North Sector-4', 'PHC', 24.515207, 73.563433, 33827, False, 2.22, 6, 1, 4, 4, 'DIESEL_GENERATOR', 20.0, 24.0, 5.0),
('DST-A1', 'PHC-DST-A1-05', 'PHC North Sector-5', 'PHC', 24.678581, 73.52967, 26155, True, 2.44, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 5.0),
('DST-A1', 'PHC-DST-A1-06', 'PHC North Sector-6', 'PHC', 24.858538, 73.690072, 26601, True, 3.07, 4, 1, 2, 4, 'HYBRID_SOLAR_DIESEL', 15.0, 36.0, 3.0),
('DST-A2', 'PHC-DST-A2-01', 'PHC South Sector-1', 'PHC', 24.245497, 74.22809, 33093, False, 1.62, 6, 2, 3, 2, 'DIESEL_GENERATOR', 25.0, 24.0, 0.0),
('DST-A2', 'PHC-DST-A2-02', 'PHC South Sector-2', 'PHC', 23.963728, 74.173745, 30401, False, 1.55, 6, 1, 3, 3, 'DIESEL_GENERATOR', 15.0, 24.0, 0.0),
('DST-A2', 'PHC-DST-A2-03', 'PHC South Sector-3', 'PHC', 23.891939, 73.938468, 30325, False, 2.02, 6, 1, 3, 3, 'DIESEL_GENERATOR', 25.0, 24.0, 0.0),
('DST-A2', 'PHC-DST-A2-04', 'PHC South Sector-4', 'PHC', 23.984085, 73.77644, 23330, True, 2.56, 6, 1, 2, 4, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 3.0),
('DST-A2', 'PHC-DST-A2-05', 'PHC South Sector-5', 'PHC', 24.202918, 73.781801, 26416, True, 3.16, 4, 1, 2, 3, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 5.0),
('DST-A2', 'PHC-DST-A2-06', 'PHC South Sector-6', 'PHC', 24.427104, 73.941373, 21683, True, 2.4, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 8.0),
('DST-B1', 'PHC-DST-B1-01', 'PHC East Sector-1', 'PHC', 23.914097, 74.447139, 34403, False, 1.82, 6, 2, 3, 3, 'DIESEL_GENERATOR', 15.0, 24.0, 0.0),
('DST-B1', 'PHC-DST-B1-02', 'PHC East Sector-2', 'PHC', 23.725592, 74.483886, 19370, True, 3.3, 6, 1, 2, 4, 'HYBRID_SOLAR_DIESEL', 20.0, 36.0, 8.0),
('DST-B1', 'PHC-DST-B1-03', 'PHC East Sector-3', 'PHC', 23.491935, 74.336066, 35687, False, 1.51, 8, 1, 4, 2, 'DIESEL_GENERATOR', 20.0, 24.0, 5.0),
('DST-B1', 'PHC-DST-B1-04', 'PHC East Sector-4', 'PHC', 23.748822, 74.168886, 33188, False, 2.23, 6, 1, 3, 4, 'DIESEL_GENERATOR', 20.0, 24.0, 5.0),
('DST-B1', 'PHC-DST-B1-05', 'PHC East Sector-5', 'PHC', 23.961451, 74.080482, 29606, True, 2.39, 4, 1, 2, 3, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 5.0),
('DST-B1', 'PHC-DST-B1-06', 'PHC East Sector-6', 'PHC', 24.065412, 74.279975, 26922, True, 2.41, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 15.0, 36.0, 5.0),
('DST-B2', 'PHC-DST-B2-01', 'PHC West Sector-1', 'PHC', 23.644011, 74.870372, 25116, False, 2.45, 6, 1, 2, 2, 'DIESEL_GENERATOR', 20.0, 24.0, 2.5),
('DST-B2', 'PHC-DST-B2-02', 'PHC West Sector-2', 'PHC', 23.370536, 74.71408, 46569, False, 1.92, 6, 2, 2, 3, 'DIESEL_GENERATOR', 25.0, 24.0, 0.0),
('DST-B2', 'PHC-DST-B2-03', 'PHC West Sector-3', 'PHC', 23.210551, 74.612109, 31296, False, 1.55, 6, 2, 2, 4, 'DIESEL_GENERATOR', 15.0, 24.0, 2.5),
('DST-B2', 'PHC-DST-B2-04', 'PHC West Sector-4', 'PHC', 23.285775, 74.379901, 33403, False, 1.52, 8, 2, 4, 4, 'DIESEL_GENERATOR', 20.0, 24.0, 5.0),
('DST-B2', 'PHC-DST-B2-05', 'PHC West Sector-5', 'PHC', 23.505088, 74.483791, 21461, True, 3.21, 6, 1, 2, 3, 'HYBRID_SOLAR_DIESEL', 20.0, 36.0, 8.0),
('DST-B2', 'PHC-DST-B2-06', 'PHC West Sector-6', 'PHC', 23.788657, 74.581403, 25347, True, 2.58, 6, 1, 2, 3, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 8.0),
('DST-C1', 'PHC-DST-C1-01', 'PHC Chinar Sector-1', 'PHC', 25.286173, 75.225752, 25610, False, 1.88, 4, 2, 2, 4, 'DIESEL_GENERATOR', 15.0, 24.0, 5.0),
('DST-C1', 'PHC-DST-C1-02', 'PHC Chinar Sector-2', 'PHC', 25.112726, 75.286304, 29945, False, 1.72, 6, 1, 4, 2, 'DIESEL_GENERATOR', 20.0, 24.0, 0.0),
('DST-C1', 'PHC-DST-C1-03', 'PHC Chinar Sector-3', 'PHC', 25.036081, 75.097078, 30032, True, 2.0, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 20.0, 36.0, 5.0),
('DST-C1', 'PHC-DST-C1-04', 'PHC Chinar Sector-4', 'PHC', 25.143971, 74.968591, 35216, False, 1.06, 6, 2, 3, 3, 'DIESEL_GENERATOR', 25.0, 24.0, 0.0),
('DST-C1', 'PHC-DST-C1-05', 'PHC Chinar Sector-5', 'PHC', 25.274366, 74.984159, 26253, True, 2.36, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 8.0),
('DST-C1', 'PHC-DST-C1-06', 'PHC Chinar Sector-6', 'PHC', 25.375899, 75.124038, 22830, True, 2.61, 4, 1, 2, 4, 'HYBRID_SOLAR_DIESEL', 25.0, 36.0, 3.0),
('DST-C2', 'PHC-DST-C2-01', 'PHC Dharani Sector-1', 'PHC', 25.848124, 75.808071, 30361, False, 1.95, 4, 1, 3, 3, 'DIESEL_GENERATOR', 20.0, 24.0, 0.0),
('DST-C2', 'PHC-DST-C2-02', 'PHC Dharani Sector-2', 'PHC', 25.573813, 75.640003, 32882, False, 1.36, 10, 1, 4, 2, 'DIESEL_GENERATOR', 15.0, 24.0, 5.0),
('DST-C2', 'PHC-DST-C2-03', 'PHC Dharani Sector-3', 'PHC', 25.315544, 75.530361, 24682, False, 1.02, 6, 2, 4, 2, 'DIESEL_GENERATOR', 15.0, 24.0, 5.0),
('DST-C2', 'PHC-DST-C2-04', 'PHC Dharani Sector-4', 'PHC', 25.576952, 75.382619, 26687, False, 1.35, 10, 2, 4, 3, 'DIESEL_GENERATOR', 15.0, 24.0, 2.5),
('DST-C2', 'PHC-DST-C2-05', 'PHC Dharani Sector-5', 'PHC', 25.779741, 75.303278, 18000, True, 2.07, 6, 1, 2, 3, 'HYBRID_SOLAR_DIESEL', 15.0, 36.0, 3.0),
('DST-C2', 'PHC-DST-C2-06', 'PHC Dharani Sector-6', 'PHC', 25.956973, 75.562697, 34167, True, 2.45, 6, 1, 2, 2, 'HYBRID_SOLAR_DIESEL', 20.0, 36.0, 3.0)
) AS p(
    district_code, code, name, facility_type, latitude, longitude,
    catchment_population, remote_flag, vulnerability_score, total_beds,
    staff_mo, staff_nurse, staff_anm, backup_power_type,
    backup_power_capacity_kva, backup_power_hours, solar_capacity_kw
)
JOIN districts d ON d.code = p.district_code
ON CONFLICT (code) DO NOTHING;
