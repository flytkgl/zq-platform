"""回写表达式与事件快照的无数据库单元测试。"""

import unittest

from online_dev.form_manager.writeback_service import (
    FormWriteBackException,
    FormWriteBackService,
    RowCollection,
    SafeExpression,
)
from online_dev.form_data_manager.lifecycle import FormLifecycleContext


class WriteBackExpressionTests(unittest.TestCase):
    def context(self, new=None, old=None, new_rows=None, old_rows=None):
        return {
            "newData": new or {},
            "oldData": old or {},
            "newRows": RowCollection(new_rows or []),
            "oldRows": RowCollection(old_rows or []),
        }

    def test_delta_expression(self):
        value = SafeExpression.evaluate(
            "newData.quantity - oldData.quantity",
            self.context({"quantity": 15}, {"quantity": 10}),
        )
        self.assertEqual(value, 5)

    def test_aggregates_and_empty_values(self):
        context = self.context(
            new_rows=[{"amount": 10}, {"amount": 20}],
            old_rows=[{"amount": 8}],
        )
        self.assertEqual(SafeExpression.evaluate("sum(newRows.amount) - sum(oldRows.amount)", context), 22)
        self.assertEqual(SafeExpression.evaluate("count(newRows)", context), 2)
        self.assertEqual(SafeExpression.evaluate("avg(oldRows.amount)", context), 8)
        self.assertEqual(SafeExpression.evaluate("max(newRows.missing)", context), 0)

    def test_unsafe_expression_is_rejected(self):
        with self.assertRaises(FormWriteBackException):
            SafeExpression.validate("__import__('os').system('whoami')")

    def test_event_snapshot_update_and_delete(self):
        context = FormLifecycleContext(
            db=None,
            form_code="receipt",
            table_name="detail",
            table_type="sub",
            action="update",
            record_id="r1",
            old_data={"id": "r1", "quantity": 10},
            data={"id": "r1", "quantity": 15},
        )
        new_rows, old_rows = FormWriteBackService._apply_event_snapshot(
            [{"id": "r1", "quantity": 10}, {"id": "r2", "quantity": 3}], context, "after_update"
        )
        self.assertEqual(new_rows[0]["quantity"], 15)
        self.assertEqual(old_rows[0]["quantity"], 10)

        context.action = "delete"
        context.old_data = {"id": "r1", "quantity": 15}
        context.data = {"id": "r1", "quantity": 15}
        new_rows, old_rows = FormWriteBackService._apply_event_snapshot(
            [{"id": "r1", "quantity": 15}, {"id": "r2", "quantity": 3}], context, "before_delete"
        )
        self.assertEqual([row["id"] for row in new_rows], ["r2"])
        self.assertEqual([row["id"] for row in old_rows], ["r1", "r2"])


if __name__ == "__main__":
    unittest.main()
