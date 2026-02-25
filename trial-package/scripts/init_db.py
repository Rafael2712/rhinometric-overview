import sys
sys.path.insert(0, "/app")
from database import engine, Base, SessionLocal
from models.user import User
from models.role import Role, Permission, UserRole, RolePermission
from models.password_reset import PasswordResetToken
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

from sqlalchemy import inspect
inspector = inspect(engine)
for t in sorted(inspector.get_table_names()):
    print("  -", t)

db = SessionLocal()
try:
    roles_data = [
        {"id": 1, "name": "OWNER", "description": "Full platform access", "level": 1},
        {"id": 2, "name": "ADMIN", "description": "Administrative access", "level": 2},
        {"id": 3, "name": "OPERATOR", "description": "Operational access", "level": 3},
        {"id": 4, "name": "VIEWER", "description": "Read-only access", "level": 4},
    ]
    for rd in roles_data:
        existing = db.query(Role).filter(Role.name == rd["name"]).first()
        if not existing:
            r = Role(**rd)
            db.add(r)
            print("  Created role:", rd["name"])
        else:
            print("  Role exists:", rd["name"])
    db.commit()

    resources = ["dashboards", "alerts", "users", "settings", "logs", "traces", "anomalies", "kpis", "license"]
    actions = ["create", "read", "update", "delete"]
    perm_count = 0
    for res in resources:
        for act in actions:
            existing = db.query(Permission).filter(Permission.resource == res, Permission.action == act).first()
            if not existing:
                p = Permission(resource=res, action=act, description=act.title() + " " + res)
                db.add(p)
                perm_count += 1
    db.commit()
    print("  Created", perm_count, "permissions")

    owner_role = db.query(Role).filter(Role.name == "OWNER").first()
    all_perms = db.query(Permission).all()
    rp_count = 0
    for perm in all_perms:
        existing = db.query(RolePermission).filter(RolePermission.role_id == owner_role.id, RolePermission.permission_id == perm.id).first()
        if not existing:
            rp = RolePermission(role_id=owner_role.id, permission_id=perm.id)
            db.add(rp)
            rp_count += 1
    db.commit()
    print("  Assigned", rp_count, "permissions to OWNER")

    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@rhinometric.local",
            password_hash=pwd_context.hash("admin123"),
            full_name="System Administrator",
            is_active=True,
            must_change_password=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        ur = UserRole(user_id=admin.id, role_id=owner_role.id)
        db.add(ur)
        db.commit()
        print("  Admin user created id=", admin.id)
    else:
        admin.password_hash = pwd_context.hash("admin123")
        admin.is_active = True
        db.commit()
        print("  Admin password reset to admin123")

    print("DONE! Login: admin / admin123")

except Exception as e:
    db.rollback()
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
finally:
    db.close()
