class EquipmentManager:
    def __init__(self):
        self.equipment = {
            101: {
                "name": "Dell Laptop",
                "category": "Laptop",
                "status": "AVAILABLE",
                "checked_out_by": None
            },
            102: {
                "name": "Raspberry Pi Kit",
                "category": "Electronics",
                "status": "AVAILABLE",
                "checked_out_by": None
            },
            103: {
                "name": "Arduino Uno",
                "category": "Electronics",
                "status": "AVAILABLE",
                "checked_out_by": None
            },
            104: {
                "name": "USB Microphone",
                "category": "Audio",
                "status": "AVAILABLE",
                "checked_out_by": None
            },
            105: {
                "name": "DSLR Camera",
                "category": "Camera",
                "status": "AVAILABLE",
                "checked_out_by": None
            }
        }

    def list_available(self):
        return [
            {
                "id": equipment_id,
                "name": item["name"],
                "category": item["category"],
                "status": item["status"]
            }
            for equipment_id, item in self.equipment.items()
            if item["status"] == "AVAILABLE"
        ]

    def checkout(self, equipment_id, username):
        if equipment_id not in self.equipment:
            return False, "NOT_FOUND", "Equipment does not exist.", None

        item = self.equipment[equipment_id]

        if item["status"] != "AVAILABLE":
            return False, "ITEM_UNAVAILABLE", "Equipment is already checked out.", None

        item["status"] = "CHECKED_OUT"
        item["checked_out_by"] = username

        data = {
            "equipment_id": equipment_id,
            "name": item["name"],
            "status": item["status"]
        }

        return True, None, f"{item['name']} checked out successfully.", data

    def return_item(self, equipment_id, username):
        if equipment_id not in self.equipment:
            return False, "NOT_FOUND", "Equipment does not exist.", None

        item = self.equipment[equipment_id]

        if item["checked_out_by"] != username:
            return (
                False,
                "NOT_CHECKED_OUT_BY_USER",
                "This equipment is not checked out by you.",
                None
            )

        item["status"] = "AVAILABLE"
        item["checked_out_by"] = None

        data = {
            "equipment_id": equipment_id,
            "name": item["name"],
            "status": item["status"]
        }

        return True, None, f"{item['name']} returned successfully.", data

    def get_user_items(self, username):
        return [
            {
                "id": equipment_id,
                "name": item["name"],
                "category": item["category"],
                "status": item["status"]
            }
            for equipment_id, item in self.equipment.items()
            if item["checked_out_by"] == username
        ]
