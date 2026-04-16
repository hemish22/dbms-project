import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import db

conn = db.get_connection()
cur = conn.cursor()
try:
    cur.execute("SET FOREIGN_KEY_CHECKS=0;")
    cur.execute("ALTER TABLE User MODIFY user_id INT AUTO_INCREMENT;")
    cur.execute("ALTER TABLE Cloud_Resource MODIFY resource_id INT AUTO_INCREMENT;")
    cur.execute("ALTER TABLE Usage_Log MODIFY log_id INT AUTO_INCREMENT;")
    cur.execute("ALTER TABLE Billing MODIFY bill_id INT AUTO_INCREMENT;")
    cur.execute("ALTER TABLE Optimization_Suggestion MODIFY suggestion_id INT AUTO_INCREMENT;")
    cur.execute("ALTER TABLE Chat_History MODIFY chat_id INT AUTO_INCREMENT;")
    cur.execute("SET FOREIGN_KEY_CHECKS=1;")
    conn.commit()
    print("SUCCESS: Auto_increment added to all relevant tables.")
except Exception as e:
    print("ERROR:", e)
finally:
    conn.close()
