-- Cloud Resource Usage & Cost Optimization System
-- Chapter 3: Views

USE Cloud_Cost_Optimization;

-- View 1: High_Cost — resources whose total billing exceeds ₹150
CREATE OR REPLACE VIEW High_Cost AS
SELECT
    cr.resource_id,
    cr.resource_type,
    cr.instance_type,
    cr.region,
    cr.status,
    u.name AS owner_name,
    SUM(b.total_cost) AS total
FROM Cloud_Resource cr
JOIN Billing b ON cr.resource_id = b.resource_id
JOIN User u ON cr.user_id = u.user_id
GROUP BY cr.resource_id, cr.resource_type, cr.instance_type, cr.region, cr.status, u.name
HAVING SUM(b.total_cost) > 150;

-- View 2: Low_CPU — resources with average CPU below 5%
CREATE OR REPLACE VIEW Low_CPU AS
SELECT
    cr.resource_id,
    cr.resource_type,
    cr.instance_type,
    cr.region,
    cr.status,
    u.name AS owner_name,
    ROUND(AVG(ul.cpu_usage), 2) AS avg_cpu
FROM Cloud_Resource cr
JOIN Usage_Log ul ON cr.resource_id = ul.resource_id
JOIN User u ON cr.user_id = u.user_id
GROUP BY cr.resource_id, cr.resource_type, cr.instance_type, cr.region, cr.status, u.name
HAVING AVG(ul.cpu_usage) < 5;

-- View 3: Resource_Owner_Summary — per-user rollup of resources, billing, and avg CPU
CREATE OR REPLACE VIEW Resource_Owner_Summary AS
SELECT
    u.user_id,
    u.name AS owner_name,
    u.organization,
    COUNT(DISTINCT cr.resource_id) AS total_resources,
    COALESCE(ROUND(SUM(b.total_cost), 2), 0.00) AS total_billing,
    COALESCE(ROUND(AVG(ul.cpu_usage), 2), 0.00) AS avg_cpu
FROM User u
LEFT JOIN Cloud_Resource cr ON u.user_id = cr.user_id
LEFT JOIN Billing b ON cr.resource_id = b.resource_id
LEFT JOIN Usage_Log ul ON cr.resource_id = ul.resource_id
GROUP BY u.user_id, u.name, u.organization;
