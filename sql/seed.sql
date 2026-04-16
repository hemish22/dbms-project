-- Cloud Resource Usage & Cost Optimization System
-- Chapter 2: Seed Data

USE Cloud_Cost_Optimization;

-- Clear existing data to make seed script idempotent
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Chat_History;
TRUNCATE TABLE Optimization_Suggestion;
TRUNCATE TABLE Billing;
TRUNCATE TABLE Usage_Log;
TRUNCATE TABLE Cloud_Resource;
TRUNCATE TABLE User;
SET FOREIGN_KEY_CHECKS = 1;

-- Disable triggers during seeding so low_cpu_trigger doesn't create duplicate suggestions
DROP TRIGGER IF EXISTS low_cpu_trigger;
DROP TRIGGER IF EXISTS calc_total_cost;
DROP TRIGGER IF EXISTS check_usage_hours;

-- Users
INSERT INTO User (user_id, name, email, organization) VALUES
(1, 'Rahul Sharma', 'rahul@techcorp.com', 'TechCorp'),
(2, 'Anita Patel', 'anita@startupx.in', 'StartupX'),
(3, 'Vikram Singh', 'vikram@infosys.com', 'Infosys'),
(4, 'Priya Nair', 'priya@wipro.com', 'Wipro');

-- Cloud Resources
INSERT INTO Cloud_Resource (resource_id, user_id, resource_type, instance_type, region, status) VALUES
(1, 1, 'VM',       't2.micro',       'ap-south-1', 'Running'),
(2, 1, 'Storage',  's3.standard',    'ap-south-1', 'Running'),
(3, 2, 'VM',       't2.medium',      'us-east-1',  'Idle'),
(4, 2, 'Database', 'db.t3.small',    'us-east-1',  'Running'),
(5, 3, 'VM',       't3.large',       'eu-west-1',  'Stopped'),
(6, 3, 'Network',  'lb.standard',    'eu-west-1',  'Running'),
(7, 4, 'VM',       't2.micro',       'ap-south-1', 'Idle'),
(8, 4, 'Storage',  's3.intelligent', 'us-west-2',  'Running');

-- Usage Logs
INSERT INTO Usage_Log (log_id, resource_id, cpu_usage, memory_usage, storage_used, timestamp) VALUES
(1,  1, 3.2,  45.1, 12.5,  '2026-04-10 09:00:00'),
(2,  1, 2.8,  42.3, 12.6,  '2026-04-11 09:00:00'),
(3,  1, 4.1,  44.7, 12.7,  '2026-04-12 09:00:00'),
(4,  1, 3.5,  46.2, 12.8,  '2026-04-13 09:00:00'),
(5,  1, 2.1,  41.5, 12.9,  '2026-04-14 09:00:00'),
(6,  2, 55.6, 60.3, 250.0, '2026-04-10 09:00:00'),
(7,  2, 58.2, 62.1, 255.0, '2026-04-11 09:00:00'),
(8,  2, 61.4, 65.8, 260.0, '2026-04-12 09:00:00'),
(9,  3, 1.5,  20.1, 5.2,   '2026-04-10 09:00:00'),
(10, 3, 1.8,  21.3, 5.3,   '2026-04-11 09:00:00'),
(11, 3, 2.2,  22.5, 5.4,   '2026-04-12 09:00:00'),
(12, 3, 1.3,  19.8, 5.5,   '2026-04-13 09:00:00'),
(13, 3, 1.6,  20.9, 5.6,   '2026-04-14 09:00:00'),
(14, 4, 72.3, 80.5, 500.0, '2026-04-10 09:00:00'),
(15, 4, 68.9, 77.2, 510.0, '2026-04-11 09:00:00'),
(16, 5, 0.5,  15.2, 8.0,   '2026-04-10 09:00:00'),
(17, 6, 45.2, 55.1, 100.0, '2026-04-10 09:00:00'),
(18, 7, 3.8,  35.2, 20.0,  '2026-04-10 09:00:00'),
(19, 7, 4.2,  36.1, 20.1,  '2026-04-11 09:00:00'),
(20, 7, 3.1,  34.8, 20.2,  '2026-04-12 09:00:00'),
(21, 8, 25.6, 48.3, 300.0, '2026-04-10 09:00:00');

-- Billing (total_cost set explicitly; calc_total_cost trigger only fires on new INSERTs)
INSERT INTO Billing (bill_id, resource_id, usage_hours, cost_per_hour, total_cost, billing_date) VALUES
(1, 1, 720, 0.0116, 8.35,   '2026-04-01'),
(2, 2, 720, 0.0230, 16.56,  '2026-04-01'),
(3, 3, 500, 0.0464, 23.20,  '2026-04-01'),
(4, 4, 720, 0.0340, 24.48,  '2026-04-01'),
(5, 5, 200, 0.0960, 19.20,  '2026-04-01'),
(6, 6, 720, 0.0250, 18.00,  '2026-04-01'),
(7, 7, 600, 0.0116, 6.96,   '2026-04-01'),
(8, 8, 720, 0.0200, 14.40,  '2026-04-01');

-- Optimization Suggestions (pre-seeded; triggers create more on new Usage_Log inserts)
INSERT INTO Optimization_Suggestion (suggestion_id, resource_id, suggestion_type, reason, estimated_savings) VALUES
(1, 1, 'Stop',   'VM has averaged less than 5% CPU for over 5 days. Consider stopping during off-hours.', 6.00),
(2, 3, 'Stop',   'VM is in Idle state with consistently low CPU (< 5%). Potential candidate for termination.', 18.00),
(3, 7, 'Resize', 'VM CPU usage is consistently below 5%. Downsize to a smaller instance type.', 4.00);
