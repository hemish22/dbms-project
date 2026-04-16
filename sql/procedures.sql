-- Cloud Resource Usage & Cost Optimization System
-- Chapter 3: Stored Procedures

USE Cloud_Cost_Optimization;

DELIMITER $$

-- Procedure: show_billing
-- Returns a joined billing summary: resource info + owner + billing details
DROP PROCEDURE IF EXISTS show_billing$$
CREATE PROCEDURE show_billing()
BEGIN
    SELECT
        b.bill_id,
        u.name AS owner_name,
        u.organization,
        cr.resource_type,
        cr.instance_type,
        cr.region,
        b.usage_hours,
        b.cost_per_hour,
        b.total_cost,
        b.billing_date
    FROM Billing b
    JOIN Cloud_Resource cr ON b.resource_id = cr.resource_id
    JOIN User u ON cr.user_id = u.user_id
    ORDER BY b.total_cost DESC;
END$$

DELIMITER ;
