-- Cloud Resource Usage & Cost Optimization System
-- Chapter 3: Triggers

USE Cloud_Cost_Optimization;

DELIMITER $$

-- Trigger 1: low_cpu_trigger
-- Auto-creates an Optimization_Suggestion when a usage log has CPU < 5%
DROP TRIGGER IF EXISTS low_cpu_trigger$$
CREATE TRIGGER low_cpu_trigger
AFTER INSERT ON Usage_Log
FOR EACH ROW
BEGIN
    IF NEW.cpu_usage < 5.0 THEN
        INSERT INTO Optimization_Suggestion (resource_id, suggestion_type, reason, estimated_savings)
        VALUES (
            NEW.resource_id,
            'Stop',
            CONCAT('Low CPU usage detected: ', NEW.cpu_usage, '%. Resource may be idle. Consider stopping or resizing.'),
            10.00
        );
    END IF;
END$$

-- Trigger 2: calc_total_cost
-- Auto-calculates total_cost = usage_hours * cost_per_hour on Billing insert
DROP TRIGGER IF EXISTS calc_total_cost$$
CREATE TRIGGER calc_total_cost
BEFORE INSERT ON Billing
FOR EACH ROW
BEGIN
    SET NEW.total_cost = NEW.usage_hours * NEW.cost_per_hour;
END$$

-- Trigger 3: check_usage_hours
-- Rejects a Billing insert if usage_hours is negative
DROP TRIGGER IF EXISTS check_usage_hours$$
CREATE TRIGGER check_usage_hours
BEFORE INSERT ON Billing
FOR EACH ROW
BEGIN
    IF NEW.usage_hours < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'usage_hours cannot be negative. Insert rejected by check_usage_hours trigger.';
    END IF;
END$$

DELIMITER ;
