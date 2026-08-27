import sqlite3
from datetime import datetime

DB_PATH = "grid.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outages (
            outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id TEXT,
            substation_id TEXT,
            reported_time TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (line_id) REFERENCES lines(line_id),
            FOREIGN KEY (substation_id) REFERENCES substations(substation_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outage_id INTEGER NOT NULL,
            assigned_to TEXT,
            created_time TEXT NOT NULL,
            status TEXT NOT NULL,
            resolved_time TEXT,
            FOREIGN KEY (outage_id) REFERENCES outages(outage_id)
        )
    """)

    conn.commit()
    conn.close()


def record_exists(table, column, value):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT 1 FROM {table} WHERE {column} = ?",
        (value,)
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None


def create_outage(line_id=None, substation_id=None, description=""):
    if not line_id and not substation_id:
        raise ValueError(
            "An outage must be linked to a line or a substation."
        )

    if line_id and not record_exists("lines", "line_id", line_id):
        raise ValueError("The selected line does not exist.")

    if substation_id and not record_exists(
        "substations",
        "substation_id",
        substation_id
    ):
        raise ValueError("The selected substation does not exist.")

    conn = get_connection()
    cursor = conn.cursor()

    reported_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO outages (
            line_id,
            substation_id,
            reported_time,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        line_id,
        substation_id,
        reported_time,
        "Reported",
        description
    ))

    outage_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return outage_id


def create_work_order(outage_id, assigned_to):
    if not record_exists("outages", "outage_id", outage_id):
        raise ValueError("The selected outage does not exist.")

    if not assigned_to.strip():
        raise ValueError("A technician must be assigned.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM outages
        WHERE outage_id = ?
    """, (outage_id,))

    outage_status = cursor.fetchone()[0]

    if outage_status == "Resolved":
        conn.close()
        raise ValueError(
            "A work order cannot be created for a resolved outage."
        )

    cursor.execute("""
        SELECT 1
        FROM work_orders
        WHERE outage_id = ?
        AND status != 'Completed'
    """, (outage_id,))

    existing_work_order = cursor.fetchone()

    if existing_work_order:
        conn.close()
        raise ValueError(
            "This outage already has an active work order."
        )

    created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO work_orders (
            outage_id,
            assigned_to,
            created_time,
            status,
            resolved_time
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        outage_id,
        assigned_to.strip(),
        created_time,
        "Assigned",
        None
    ))

    work_order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return work_order_id


def update_work_order_status(work_order_id, new_status):
    allowed_statuses = {
        "Assigned",
        "In Progress",
        "Completed"
    }

    if new_status not in allowed_statuses:
        raise ValueError(
            "Status must be Assigned, In Progress, or Completed."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT outage_id, status
        FROM work_orders
        WHERE work_order_id = ?
    """, (work_order_id,))

    result = cursor.fetchone()

    if result is None:
        conn.close()
        raise ValueError("The work order does not exist.")

    outage_id, current_status = result

    valid_transitions = {
        "Assigned": {"In Progress"},
        "In Progress": {"Completed"},
        "Completed": set()
    }

    if new_status == current_status:
        conn.close()
        return

    if new_status not in valid_transitions[current_status]:
        conn.close()
        raise ValueError(
            f"Cannot change status from {current_status} "
            f"to {new_status}."
        )

    if new_status == "In Progress":
        cursor.execute("""
            UPDATE work_orders
            SET status = ?
            WHERE work_order_id = ?
        """, (
            new_status,
            work_order_id
        ))

        cursor.execute("""
            UPDATE outages
            SET status = ?
            WHERE outage_id = ?
        """, (
            "In Progress",
            outage_id
        ))

    elif new_status == "Completed":
        resolved_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            UPDATE work_orders
            SET status = ?,
                resolved_time = ?
            WHERE work_order_id = ?
        """, (
            new_status,
            resolved_time,
            work_order_id
        ))

        cursor.execute("""
            UPDATE outages
            SET status = ?
            WHERE outage_id = ?
        """, (
            "Resolved",
            outage_id
        ))

    conn.commit()
    conn.close()


def get_outages():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            outage_id,
            line_id,
            substation_id,
            reported_time,
            status,
            description
        FROM outages
        ORDER BY outage_id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_work_orders():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            work_order_id,
            outage_id,
            assigned_to,
            created_time,
            status,
            resolved_time
        FROM work_orders
        ORDER BY work_order_id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def display_outages():
    outages = get_outages()

    if not outages:
        print("\nNo outages have been recorded.")
        return

    print("\nOUTAGES")

    for outage in outages:
        print(
            f"ID: {outage[0]} | "
            f"Line: {outage[1]} | "
            f"Substation: {outage[2]} | "
            f"Reported: {outage[3]} | "
            f"Status: {outage[4]} | "
            f"Description: {outage[5]}"
        )


def display_work_orders():
    work_orders = get_work_orders()

    if not work_orders:
        print("\nNo work orders have been created.")
        return

    print("\nWORK ORDERS")

    for order in work_orders:
        print(
            f"Work Order: {order[0]} | "
            f"Outage: {order[1]} | "
            f"Assigned To: {order[2]} | "
            f"Created: {order[3]} | "
            f"Status: {order[4]} | "
            f"Resolved: {order[5]}"
        )


def report_outage_menu():
    line_id = input(
        "Enter Line ID or press Enter to leave blank: "
    ).strip()

    substation_id = input(
        "Enter Substation ID or press Enter to leave blank: "
    ).strip()

    description = input(
        "Enter outage description: "
    ).strip()

    if line_id == "":
        line_id = None

    if substation_id == "":
        substation_id = None

    outage_id = create_outage(
        line_id,
        substation_id,
        description
    )

    print(
        f"Outage {outage_id} was recorded successfully."
    )


def create_work_order_menu():
    display_outages()

    outage_id = int(
        input("\nEnter outage ID: ")
    )

    assigned_to = input(
        "Enter technician name: "
    )

    work_order_id = create_work_order(
        outage_id,
        assigned_to
    )

    print(
        f"Work order {work_order_id} was created successfully."
    )


def update_work_order_menu():
    display_work_orders()

    work_order_id = int(
        input("\nEnter work order ID: ")
    )

    print("\n1. In Progress")
    print("2. Completed")

    choice = input(
        "Choose the new status: "
    ).strip()

    if choice == "1":
        new_status = "In Progress"
    elif choice == "2":
        new_status = "Completed"
    else:
        raise ValueError("Invalid status selection.")

    update_work_order_status(
        work_order_id,
        new_status
    )

    print(
        f"Work order {work_order_id} "
        f"was updated to {new_status}."
    )


def main():
    setup_tables()

    while True:
        print("\nGRIDCARE-LITE")
        print("1. Report Outage")
        print("2. Create Work Order")
        print("3. Update Work Order")
        print("4. View Outages")
        print("5. View Work Orders")
        print("6. Exit")

        choice = input(
            "\nSelect an option: "
        ).strip()

        try:
            if choice == "1":
                report_outage_menu()

            elif choice == "2":
                create_work_order_menu()

            elif choice == "3":
                update_work_order_menu()

            elif choice == "4":
                display_outages()

            elif choice == "5":
                display_work_orders()

            elif choice == "6":
                print("Program closed.")
                break

            else:
                print("Invalid option.")

        except ValueError as error:
            print(f"Error: {error}")

        except sqlite3.Error as error:
            print(f"Database error: {error}")


if __name__ == "__main__":
    main()