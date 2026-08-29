class RecordNotFoundError(Exception):
    def __init__(self, table: str):
        self.table = table
        super().__init__(f"Record not found in table: {table}")
