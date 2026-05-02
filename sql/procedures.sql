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

DELIMITER $$

-- Function: get_cost_grade
-- Returns a cost tier label based on total billing amount
DROP FUNCTION IF EXISTS get_cost_grade$$
CREATE FUNCTION get_cost_grade(total DECIMAL(10,2))
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
    DECLARE grade VARCHAR(10);
    IF total >= 500 THEN
        SET grade = 'Critical';
    ELSEIF total >= 200 THEN
        SET grade = 'High';
    ELSEIF total >= 100 THEN
        SET grade = 'Medium';
    ELSE
        SET grade = 'Low';
    END IF;
    RETURN grade;
END$$

-- Procedure: flag_idle_resources
-- Uses a cursor to iterate running resources with avg CPU < 10%
-- and inserts an Optimization_Suggestion for each idle candidate
DROP PROCEDURE IF EXISTS flag_idle_resources$$
CREATE PROCEDURE flag_idle_resources()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE r_id INT;
    DECLARE r_type VARCHAR(50);
    DECLARE avg_c DECIMAL(5,2);
    DECLARE flagged INT DEFAULT 0;

    DECLARE cur CURSOR FOR
        SELECT cr.resource_id, cr.resource_type,
               ROUND(AVG(ul.cpu_usage), 2) AS avg_cpu
        FROM Cloud_Resource cr
        JOIN Usage_Log ul ON cr.resource_id = ul.resource_id
        WHERE cr.status = 'Running'
        GROUP BY cr.resource_id, cr.resource_type
        HAVING AVG(ul.cpu_usage) < 10.0;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO r_id, r_type, avg_c;
        IF done THEN
            LEAVE read_loop;
        END IF;
        INSERT INTO Optimization_Suggestion (resource_id, suggestion_type, reason, estimated_savings)
        VALUES (
            r_id,
            'Stop',
            CONCAT('Cursor scan: ', r_type, ' running at avg ', avg_c, '% CPU — candidate for shutdown.'),
            15.00
        );
        SET flagged = flagged + 1;
    END LOOP;
    CLOSE cur;

    SELECT flagged AS suggestions_created;
END$$

DELIMITER ;
