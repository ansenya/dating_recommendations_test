db = db.getSiblingDB("dating");

db.createUser(
    {
        user: "senya",
        pwd: "insecure",
        roles: [
            {
                role: "dbOwner",
                db: "dating"
            }
        ]
    }
);