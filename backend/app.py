"""
Cloud Resource Usage & Cost Optimization System
Flask REST API — 32 endpoints
"""
import json
from datetime import datetime, date
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

import db
import ai
import ml

app = Flask(__name__)
CORS(app)  # Allow frontend to call API from file:// or different port


# ---------------------------------------------------------------------------
# JSON serialization helper for MySQL decimal/date types
# ---------------------------------------------------------------------------
class MySQLEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

app.json_encoder = MySQLEncoder


def ok(data):
    return jsonify(data), 200


def err(msg, code=400):
    return jsonify({"error": str(msg)}), code


# ===========================================================================
# DASHBOARD
# ===========================================================================

@app.route("/api/dashboard/stats")
def dashboard_stats():
    try:
        stats = {}
        stats["total_users"]     = db.query("SELECT COUNT(*) AS c FROM User")[0]["c"]
        stats["total_resources"] = db.query("SELECT COUNT(*) AS c FROM Cloud_Resource")[0]["c"]
        stats["total_cost"]      = db.query("SELECT COALESCE(SUM(total_cost),0) AS c FROM Billing")[0]["c"]
        stats["total_suggestions"] = db.query("SELECT COUNT(*) AS c FROM Optimization_Suggestion")[0]["c"]
        stats["active_resources"] = db.query("SELECT COUNT(*) AS c FROM Cloud_Resource WHERE status='Running'")[0]["c"]

        stats["cost_per_resource"] = db.query(
            "SELECT cr.resource_id, cr.instance_type, COALESCE(SUM(b.total_cost),0) AS total_cost "
            "FROM Cloud_Resource cr LEFT JOIN Billing b ON cr.resource_id=b.resource_id "
            "GROUP BY cr.resource_id, cr.instance_type ORDER BY cr.resource_id"
        )
        stats["avg_cpu_per_resource"] = db.query(
            "SELECT cr.resource_id, cr.instance_type, ROUND(AVG(ul.cpu_usage),2) AS avg_cpu "
            "FROM Cloud_Resource cr LEFT JOIN Usage_Log ul ON cr.resource_id=ul.resource_id "
            "GROUP BY cr.resource_id, cr.instance_type ORDER BY cr.resource_id"
        )
        stats["recent_logs"] = db.query(
            "SELECT ul.log_id, cr.instance_type, cr.resource_type, ul.cpu_usage, ul.memory_usage, ul.timestamp "
            "FROM Usage_Log ul JOIN Cloud_Resource cr ON ul.resource_id=cr.resource_id "
            "ORDER BY ul.timestamp DESC LIMIT 5"
        )
        return ok(stats)
    except Exception as e:
        return err(e)


# ===========================================================================
# USERS CRUD
# ===========================================================================

@app.route("/api/users", methods=["GET"])
def get_users():
    try:
        return ok(db.query("SELECT * FROM User ORDER BY user_id"))
    except Exception as e:
        return err(e)


@app.route("/api/users", methods=["POST"])
def create_user():
    try:
        d = request.json
        lid, _ = db.execute(
            "INSERT INTO User (name, email, organization) VALUES (%s, %s, %s)",
            (d["name"], d["email"], d.get("organization", ""))
        )
        row = db.query("SELECT * FROM User WHERE user_id=%s", (lid,))
        return ok(row[0])
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/users/<int:uid>", methods=["PUT"])
def update_user(uid):
    try:
        d = request.json
        db.execute(
            "UPDATE User SET name=%s, email=%s, organization=%s WHERE user_id=%s",
            (d["name"], d["email"], d.get("organization", ""), uid)
        )
        row = db.query("SELECT * FROM User WHERE user_id=%s", (uid,))
        return ok(row[0] if row else {})
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/users/<int:uid>", methods=["DELETE"])
def delete_user(uid):
    try:
        _, rowcount = db.execute("DELETE FROM User WHERE user_id=%s", (uid,))
        return ok({"deleted": rowcount})
    except Exception as e:
        return err(e)


# ===========================================================================
# CLOUD RESOURCES CRUD
# ===========================================================================

@app.route("/api/resources", methods=["GET"])
def get_resources():
    try:
        user_id = request.args.get("user_id")
        status  = request.args.get("status")
        region  = request.args.get("region")

        sql = ("SELECT cr.*, u.name AS owner_name FROM Cloud_Resource cr "
               "JOIN User u ON cr.user_id=u.user_id WHERE 1=1")
        params = []
        if user_id:
            sql += " AND cr.user_id=%s"; params.append(user_id)
        if status:
            sql += " AND cr.status=%s"; params.append(status)
        if region:
            sql += " AND cr.region=%s"; params.append(region)
        sql += " ORDER BY cr.resource_id"
        return ok(db.query(sql, params))
    except Exception as e:
        return err(e)


@app.route("/api/resources", methods=["POST"])
def create_resource():
    try:
        d = request.json
        lid, _ = db.execute(
            "INSERT INTO Cloud_Resource (user_id, resource_type, instance_type, region, status) "
            "VALUES (%s, %s, %s, %s, %s)",
            (d["user_id"], d["resource_type"], d["instance_type"], d["region"], d.get("status", "Running"))
        )
        row = db.query(
            "SELECT cr.*, u.name AS owner_name FROM Cloud_Resource cr "
            "JOIN User u ON cr.user_id=u.user_id WHERE cr.resource_id=%s", (lid,)
        )
        return ok(row[0])
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/resources/<int:rid>", methods=["PUT"])
def update_resource(rid):
    try:
        d = request.json
        db.execute(
            "UPDATE Cloud_Resource SET user_id=%s, resource_type=%s, instance_type=%s, region=%s, status=%s "
            "WHERE resource_id=%s",
            (d["user_id"], d["resource_type"], d["instance_type"], d["region"], d["status"], rid)
        )
        row = db.query(
            "SELECT cr.*, u.name AS owner_name FROM Cloud_Resource cr "
            "JOIN User u ON cr.user_id=u.user_id WHERE cr.resource_id=%s", (rid,)
        )
        return ok(row[0] if row else {})
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/resources/<int:rid>", methods=["DELETE"])
def delete_resource(rid):
    try:
        _, rowcount = db.execute("DELETE FROM Cloud_Resource WHERE resource_id=%s", (rid,))
        return ok({"deleted": rowcount})
    except Exception as e:
        return err(e)


# ===========================================================================
# USAGE LOGS CRUD
# ===========================================================================

@app.route("/api/usage-logs", methods=["GET"])
def get_usage_logs():
    try:
        resource_id = request.args.get("resource_id")
        sql = ("SELECT ul.*, cr.instance_type, cr.resource_type FROM Usage_Log ul "
               "JOIN Cloud_Resource cr ON ul.resource_id=cr.resource_id WHERE 1=1")
        params = []
        if resource_id:
            sql += " AND ul.resource_id=%s"; params.append(resource_id)
        sql += " ORDER BY ul.timestamp DESC"
        return ok(db.query(sql, params))
    except Exception as e:
        return err(e)


@app.route("/api/usage-logs", methods=["POST"])
def create_usage_log():
    try:
        d = request.json
        # Count suggestions before insert to see how many the trigger adds
        before_count = db.query("SELECT COUNT(*) AS c FROM Optimization_Suggestion")[0]["c"]

        lid, _ = db.execute(
            "INSERT INTO Usage_Log (resource_id, cpu_usage, memory_usage, storage_used) VALUES (%s,%s,%s,%s)",
            (d["resource_id"], d["cpu_usage"], d["memory_usage"], d["storage_used"])
        )
        after_count = db.query("SELECT COUNT(*) AS c FROM Optimization_Suggestion")[0]["c"]
        new_suggestions = after_count - before_count

        row = db.query(
            "SELECT ul.*, cr.instance_type, cr.resource_type FROM Usage_Log ul "
            "JOIN Cloud_Resource cr ON ul.resource_id=cr.resource_id WHERE ul.log_id=%s", (lid,)
        )
        return ok({"log": row[0], "new_suggestions_created": new_suggestions})
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/usage-logs/<int:lid>", methods=["DELETE"])
def delete_usage_log(lid):
    try:
        _, rowcount = db.execute("DELETE FROM Usage_Log WHERE log_id=%s", (lid,))
        return ok({"deleted": rowcount})
    except Exception as e:
        return err(e)


# ===========================================================================
# BILLING CRUD
# ===========================================================================

@app.route("/api/billing", methods=["GET"])
def get_billing():
    try:
        return ok(db.query(
            "SELECT b.*, cr.instance_type, cr.resource_type, u.name AS owner_name "
            "FROM Billing b JOIN Cloud_Resource cr ON b.resource_id=cr.resource_id "
            "JOIN User u ON cr.user_id=u.user_id ORDER BY b.bill_id"
        ))
    except Exception as e:
        return err(e)


@app.route("/api/billing", methods=["POST"])
def create_billing():
    try:
        d = request.json
        # Note: total_cost is computed by the calc_total_cost trigger
        lid, _ = db.execute(
            "INSERT INTO Billing (resource_id, usage_hours, cost_per_hour, billing_date) VALUES (%s,%s,%s,%s)",
            (d["resource_id"], d["usage_hours"], d["cost_per_hour"],
             d.get("billing_date", date.today().isoformat()))
        )
        row = db.query(
            "SELECT b.*, cr.instance_type, cr.resource_type, u.name AS owner_name "
            "FROM Billing b JOIN Cloud_Resource cr ON b.resource_id=cr.resource_id "
            "JOIN User u ON cr.user_id=u.user_id WHERE b.bill_id=%s", (lid,)
        )
        return ok(row[0])
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


@app.route("/api/billing/<int:bid>", methods=["DELETE"])
def delete_billing(bid):
    try:
        _, rowcount = db.execute("DELETE FROM Billing WHERE bill_id=%s", (bid,))
        return ok({"deleted": rowcount})
    except Exception as e:
        return err(e)


# ===========================================================================
# SUGGESTIONS
# ===========================================================================

@app.route("/api/suggestions", methods=["GET"])
def get_suggestions():
    try:
        return ok(db.query(
            "SELECT s.*, cr.instance_type, cr.resource_type, cr.region, u.name AS owner_name "
            "FROM Optimization_Suggestion s "
            "JOIN Cloud_Resource cr ON s.resource_id=cr.resource_id "
            "JOIN User u ON cr.user_id=u.user_id "
            "ORDER BY s.suggestion_id DESC"
        ))
    except Exception as e:
        return err(e)


# ===========================================================================
# VIEWS
# ===========================================================================

@app.route("/api/views/high-cost")
def view_high_cost():
    try:
        return ok(db.query("SELECT * FROM High_Cost ORDER BY total DESC"))
    except Exception as e:
        return err(e)


@app.route("/api/views/low-cpu")
def view_low_cpu():
    try:
        return ok(db.query("SELECT * FROM Low_CPU ORDER BY avg_cpu ASC"))
    except Exception as e:
        return err(e)


@app.route("/api/views/resource-summary")
def view_resource_summary():
    try:
        return ok(db.query("SELECT * FROM Resource_Owner_Summary ORDER BY total_billing DESC"))
    except Exception as e:
        return err(e)


# ===========================================================================
# STORED PROCEDURE
# ===========================================================================

@app.route("/api/procedures/flag-idle", methods=["POST"])
def proc_flag_idle():
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("flag_idle_resources")
        rows = []
        for result in cur.stored_results():
            rows.extend(result.fetchall())
        conn.commit()
        conn.close()
        return ok({"result": rows[0] if rows else {"suggestions_created": 0}})
    except Exception as e:
        return err(e)


@app.route("/api/procedures/show-billing", methods=["POST"])
def proc_show_billing():
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("show_billing")
        rows = []
        for result in cur.stored_results():
            rows.extend(result.fetchall())
        conn.close()
        return ok(rows)
    except Exception as e:
        return err(e)


# ===========================================================================
# CUSTOM SQL (Reports page — SELECT only)
# ===========================================================================

@app.route("/api/custom-sql", methods=["POST"])
def custom_sql():
    try:
        sql = (request.json or {}).get("sql", "").strip()
        if not sql:
            return err("No SQL provided")
        sql_lower = sql.lower()
        for kw in ai.BLOCKED_KEYWORDS:
            # word boundary check
            import re
            if re.search(r'\b' + kw + r'\b', sql_lower):
                return err(f"Keyword '{kw}' is not allowed. Only SELECT queries permitted.")
        if not sql_lower.startswith("select"):
            return err("Only SELECT queries are allowed.")
        rows = db.query(sql)
        columns = list(rows[0].keys()) if rows else []
        return ok({"columns": columns, "rows": rows})
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


# ===========================================================================
# TRANSACTIONS (Chapter 5)
# ===========================================================================

@app.route("/api/transactions/1", methods=["POST"])
def transaction_1():
    """
    Transaction 1: Update resource status with SAVEPOINT + ROLLBACK to savepoint.
    Demonstrates partial rollback — status change rolls back, but the read stays.
    """
    conn = db.get_connection()
    result = {}
    try:
        cur = conn.cursor(dictionary=True)

        # Before state
        cur.execute("SELECT resource_id, instance_type, status FROM Cloud_Resource WHERE resource_id=1")
        result["before_state"] = cur.fetchall()

        cur.execute("START TRANSACTION")
        cur.execute("SAVEPOINT before_update")

        cur.execute("UPDATE Cloud_Resource SET status='Stopped' WHERE resource_id=1")
        cur.execute("SELECT resource_id, instance_type, status FROM Cloud_Resource WHERE resource_id=1")
        result["after_update"] = cur.fetchall()

        # Rollback to savepoint (undo the update)
        cur.execute("ROLLBACK TO SAVEPOINT before_update")
        conn.commit()

        cur.execute("SELECT resource_id, instance_type, status FROM Cloud_Resource WHERE resource_id=1")
        result["after_state"] = cur.fetchall()
        result["message"] = "Status updated then rolled back to SAVEPOINT. Original status restored."
        result["status"] = "success"
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "message": str(e)}
    finally:
        conn.close()
    return ok(result)


@app.route("/api/transactions/2", methods=["POST"])
def transaction_2():
    """
    Transaction 2: Insert usage log + COMMIT.
    Demonstrates a basic committed transaction.
    """
    conn = db.get_connection()
    result = {}
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS c FROM Usage_Log")
        before_count = cur.fetchone()["c"]

        cur.execute("START TRANSACTION")
        cur.execute(
            "INSERT INTO Usage_Log (resource_id, cpu_usage, memory_usage, storage_used) "
            "VALUES (2, 55.0, 60.0, 200.0)"
        )
        cur.execute("SELECT COUNT(*) AS c FROM Usage_Log")
        during_count = cur.fetchone()["c"]
        conn.commit()

        cur.execute("SELECT COUNT(*) AS c FROM Usage_Log")
        after_count = cur.fetchone()["c"]

        result["before_state"] = [{"usage_log_count": before_count}]
        result["after_state"]  = [{"usage_log_count": after_count}]
        result["message"] = f"Inserted 1 usage log (resource_id=2). Count: {before_count} → {after_count}. COMMIT successful."
        result["status"] = "success"
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "message": str(e)}
    finally:
        conn.close()
    return ok(result)


@app.route("/api/transactions/3", methods=["POST"])
def transaction_3():
    """
    Transaction 3: Billing insert with SAVEPOINT, verify trigger computed total_cost, then COMMIT.
    """
    conn = db.get_connection()
    result = {}
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS c FROM Billing")
        before_count = cur.fetchone()["c"]

        cur.execute("START TRANSACTION")
        cur.execute("SAVEPOINT pre_insert")
        cur.execute(
            "INSERT INTO Billing (resource_id, usage_hours, cost_per_hour, billing_date) "
            "VALUES (3, 100, 0.05, CURDATE())"
        )
        cur.execute("SELECT bill_id, resource_id, usage_hours, cost_per_hour, total_cost FROM Billing ORDER BY bill_id DESC LIMIT 1")
        new_bill = cur.fetchone()
        conn.commit()

        cur.execute("SELECT COUNT(*) AS c FROM Billing")
        after_count = cur.fetchone()["c"]

        result["before_state"] = [{"billing_count": before_count}]
        result["after_state"]  = [{"billing_count": after_count, "new_bill": new_bill}]
        result["message"] = (f"Billing inserted. Trigger calc_total_cost computed: "
                             f"total_cost = {new_bill['usage_hours']} × {new_bill['cost_per_hour']} "
                             f"= ₹{new_bill['total_cost']}. COMMIT successful.")
        result["status"] = "success"
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "message": str(e)}
    finally:
        conn.close()
    return ok(result)


@app.route("/api/transactions/4", methods=["POST"])
def transaction_4():
    """
    Transaction 4: Delete a resource then ROLLBACK — demonstrates full rollback.
    """
    conn = db.get_connection()
    result = {}
    try:
        cur = conn.cursor(dictionary=True)

        # Use resource 8 (safe — least critical in seed data)
        cur.execute("SELECT resource_id, instance_type, status FROM Cloud_Resource WHERE resource_id=8")
        before = cur.fetchall()
        result["before_state"] = before

        cur.execute("START TRANSACTION")
        cur.execute("DELETE FROM Cloud_Resource WHERE resource_id=8")
        cur.execute("SELECT COUNT(*) AS c FROM Cloud_Resource WHERE resource_id=8")
        during = cur.fetchone()
        conn.rollback()  # Full rollback

        cur.execute("SELECT resource_id, instance_type, status FROM Cloud_Resource WHERE resource_id=8")
        after = cur.fetchall()
        result["after_state"] = after
        result["message"] = "DELETE executed inside transaction then ROLLBACK issued. Resource 8 is restored."
        result["status"] = "success"
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "message": str(e)}
    finally:
        conn.close()
    return ok(result)


@app.route("/api/transactions/5", methods=["POST"])
def transaction_5():
    """
    Transaction 5: Insert optimization suggestion + COMMIT.
    Demonstrates manual (non-trigger) suggestion insertion in a transaction.
    """
    conn = db.get_connection()
    result = {}
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS c FROM Optimization_Suggestion")
        before_count = cur.fetchone()["c"]

        cur.execute("START TRANSACTION")
        cur.execute(
            "INSERT INTO Optimization_Suggestion (resource_id, suggestion_type, reason, estimated_savings) "
            "VALUES (4, 'Migrate', 'Resource in us-east-1 can be migrated to ap-south-1 for 30%% cost reduction.', 20.00)"
        )
        cur.execute("SELECT suggestion_id, resource_id, suggestion_type, estimated_savings FROM Optimization_Suggestion ORDER BY suggestion_id DESC LIMIT 1")
        new_row = cur.fetchone()
        conn.commit()

        cur.execute("SELECT COUNT(*) AS c FROM Optimization_Suggestion")
        after_count = cur.fetchone()["c"]

        result["before_state"] = [{"suggestion_count": before_count}]
        result["after_state"]  = [{"suggestion_count": after_count, "new_suggestion": new_row}]
        result["message"] = f"Suggestion inserted manually in a transaction. Count: {before_count} → {after_count}. COMMIT successful."
        result["status"] = "success"
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "message": str(e)}
    finally:
        conn.close()
    return ok(result)


# ===========================================================================
# AI — Natural Language to SQL
# ===========================================================================

@app.route("/api/ai/nl-to-sql", methods=["POST"])
def nl_to_sql():
    try:
        question = (request.json or {}).get("question", "").strip()
        if not question:
            return err("No question provided")
        result = ai.natural_language_to_sql(question)
        if "error" in result:
            return err(result["error"])
        # Execute the generated SQL
        rows = db.query(result["sql"])
        columns = list(rows[0].keys()) if rows else []
        result["columns"] = columns
        result["rows"] = rows
        return ok(result)
    except mysql.connector.Error as e:
        return err(e.msg)
    except Exception as e:
        return err(e)


# ===========================================================================
# AI — Resource Recommendations
# ===========================================================================

@app.route("/api/ai/suggest/<int:resource_id>", methods=["POST"])
def ai_suggest_resource(resource_id):
    try:
        resource = db.query(
            "SELECT cr.*, u.name AS owner_name, u.organization FROM Cloud_Resource cr "
            "JOIN User u ON cr.user_id=u.user_id WHERE cr.resource_id=%s", (resource_id,)
        )
        if not resource:
            return err("Resource not found", 404)

        logs = db.query(
            "SELECT cpu_usage, memory_usage, storage_used, timestamp FROM Usage_Log "
            "WHERE resource_id=%s ORDER BY timestamp DESC LIMIT 7", (resource_id,)
        )
        bills = db.query(
            "SELECT usage_hours, cost_per_hour, total_cost, billing_date FROM Billing "
            "WHERE resource_id=%s ORDER BY billing_date DESC LIMIT 3", (resource_id,)
        )

        context = {
            "resource": resource[0],
            "last_7_usage_logs": logs,
            "last_3_bills": bills,
        }
        # Convert to string for prompt
        import json as _json
        context_str = _json.dumps(context, indent=2, default=str)

        recommendation = ai.generate_resource_recommendation(context_str)

        # Save to DB
        db.execute(
            "UPDATE Optimization_Suggestion SET ai_recommendation=%s, ai_generated_at=NOW() "
            "WHERE resource_id=%s ORDER BY suggestion_id DESC LIMIT 1",
            (recommendation, resource_id)
        )

        return ok({"resource_id": resource_id, "recommendation": recommendation})
    except Exception as e:
        return err(e)


@app.route("/api/ai/suggest-all", methods=["POST"])
def ai_suggest_all():
    try:
        resources = db.query("SELECT resource_id FROM Cloud_Resource")
        results = []
        for r in resources:
            rid = r["resource_id"]
            resource = db.query(
                "SELECT cr.*, u.name AS owner_name FROM Cloud_Resource cr "
                "JOIN User u ON cr.user_id=u.user_id WHERE cr.resource_id=%s", (rid,)
            )
            logs = db.query(
                "SELECT cpu_usage, memory_usage, storage_used FROM Usage_Log "
                "WHERE resource_id=%s ORDER BY timestamp DESC LIMIT 5", (rid,)
            )
            bills = db.query(
                "SELECT usage_hours, cost_per_hour, total_cost FROM Billing "
                "WHERE resource_id=%s ORDER BY billing_date DESC LIMIT 2", (rid,)
            )
            import json as _json
            context_str = _json.dumps({"resource": resource[0], "logs": logs, "bills": bills}, default=str)
            rec = ai.generate_resource_recommendation(context_str)
            db.execute(
                "UPDATE Optimization_Suggestion SET ai_recommendation=%s, ai_generated_at=NOW() "
                "WHERE resource_id=%s ORDER BY suggestion_id DESC LIMIT 1",
                (rec, rid)
            )
            results.append({"resource_id": rid, "recommendation": rec})
        return ok({"generated": len(results), "results": results})
    except Exception as e:
        return err(e)


# ===========================================================================
# ML — Anomaly Detection
# ===========================================================================

@app.route("/api/ml/detect-anomalies", methods=["POST"])
def detect_anomalies():
    try:
        results = ml.detect_anomalies()
        anomaly_count = sum(1 for r in results if r["is_anomaly"])
        return ok({"total_logs": len(results), "anomalies_found": anomaly_count, "results": results})
    except Exception as e:
        return err(e)


# ===========================================================================
# AI — Chatbot
# ===========================================================================

@app.route("/api/ai/chat", methods=["POST"])
def chat():
    try:
        d = request.json or {}
        user_message = d.get("message", "").strip()
        if not user_message:
            return err("No message provided")

        # Fetch last 5 turns for context
        history_rows = db.query(
            "SELECT user_question, ai_response FROM Chat_History ORDER BY created_at DESC LIMIT 5"
        )
        history = []
        for row in reversed(history_rows):
            history.append({"role": "user", "content": row["user_question"]})
            history.append({"role": "assistant", "content": row["ai_response"]})

        response = ai.chat(user_message, history)

        # Save to Chat_History
        db.execute(
            "INSERT INTO Chat_History (user_question, ai_response) VALUES (%s, %s)",
            (user_message, response)
        )

        return ok({"response": response})
    except Exception as e:
        return err(e)


@app.route("/api/ai/chat/history", methods=["GET"])
def chat_history():
    try:
        rows = db.query("SELECT * FROM Chat_History ORDER BY created_at ASC")
        return ok(rows)
    except Exception as e:
        return err(e)


@app.route("/api/ai/chat/history", methods=["DELETE"])
def clear_chat_history():
    try:
        db.execute("DELETE FROM Chat_History")
        return ok({"message": "Chat history cleared"})
    except Exception as e:
        return err(e)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5500)
